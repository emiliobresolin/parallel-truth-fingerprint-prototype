"""Run the local edge observation demo against the selected MQTT transport."""

from __future__ import annotations

import json
import sys
import time
from dataclasses import replace
from pathlib import Path

PROJECT_ROOT = Path(__file__).resolve().parents[1]
SRC_PATH = PROJECT_ROOT / "src"
if str(SRC_PATH) not in sys.path:
    sys.path.insert(0, str(SRC_PATH))

from parallel_truth_fingerprint.config.runtime import load_runtime_demo_config
from parallel_truth_fingerprint.consensus import (
    build_consensus_alert,
    build_round_log,
    build_round_summary,
    committed_round_to_audit_package,
    format_consensus_alert_compact,
    format_consensus_alert_detailed,
    format_round_log_compact,
    format_round_log_detailed,
    format_round_summary,
)
from parallel_truth_fingerprint.consensus.cometbft_client import CometBftRpcClient
from parallel_truth_fingerprint.contracts.consensus_round_input import ConsensusRoundInput
from parallel_truth_fingerprint.edge_nodes.common.mqtt_io import create_transport
from parallel_truth_fingerprint.edge_nodes.edge_1.service import TemperatureEdgeService
from parallel_truth_fingerprint.edge_nodes.edge_2.service import PressureEdgeService
from parallel_truth_fingerprint.edge_nodes.edge_3.service import RpmEdgeService
from parallel_truth_fingerprint.sensor_simulation.simulator import CompressorSimulator


def default_demo_log_path(log_path: str) -> Path:
    """Resolve the configured demo log path relative to the project root."""

    candidate = Path(log_path)
    if candidate.is_absolute():
        return candidate
    return PROJECT_ROOT / candidate


def format_edge_summary(edge) -> str:
    """Return a compact live-demo summary for one edge."""

    runtime_state = edge.runtime_state()
    replicated_state = edge.local_replicated_state()
    sensor_values = replicated_state["sensor_values"]
    sensors_text = ", ".join(
        f"{name}={value}" for name, value in sorted(sensor_values.items())
    )
    return (
        f"{runtime_state['edge_id']}: "
        f"published={runtime_state['published_observation_count']} "
        f"consumed={runtime_state['peer_observation_count']} "
        f"complete={replicated_state['is_complete']} "
        f"validated={replicated_state['is_validated']} "
        f"view[{sensors_text}]"
    )


def build_consensus_round_input(edges) -> ConsensusRoundInput:
    """Build one deterministic consensus round input from the current edge views."""

    participating_edges = tuple(edge.runtime_state()["edge_id"] for edge in edges)
    round_identity = edges[0].consensus_round_identity()
    replicated_states = tuple(
        edge.replicated_state_contract(
            round_identity=round_identity,
            participating_edges=participating_edges,
        )
        for edge in edges
    )
    return ConsensusRoundInput(
        round_identity=round_identity,
        participating_edges=participating_edges,
        replicated_states=replicated_states,
    )


def default_faulty_edges(fault_mode: str) -> tuple[str, ...]:
    """Return the default edge targets for each demo fault mode."""

    if fault_mode == "single_edge_exclusion":
        return ("edge-3",)
    if fault_mode == "quorum_loss":
        return ("edge-2", "edge-3")
    return ()


def resolve_faulty_edges(config, participating_edges: tuple[str, ...]) -> tuple[str, ...]:
    """Resolve configured or default faulty edges deterministically."""

    raw_edges = config.demo_faulty_edges or default_faulty_edges(config.demo_fault_mode)
    return tuple(edge_id for edge_id in raw_edges if edge_id in participating_edges)


def inject_faults(round_input: ConsensusRoundInput, config) -> ConsensusRoundInput:
    """Inject deterministic inconsistent-edge views for live demo scenarios only."""

    if config.demo_fault_mode == "none":
        return round_input

    faulty_edges = resolve_faulty_edges(config, round_input.participating_edges)
    if not faulty_edges:
        return round_input

    offsets_by_edge = {
        edge_id: {
            "temperature": 40.0 if index % 2 == 0 else -60.0,
            "pressure": 3.4 if index % 2 == 0 else -5.0,
            "rpm": 1490.0 if index % 2 == 0 else -2300.0,
        }
        for index, edge_id in enumerate(faulty_edges)
    }

    injected_states = []
    for state in round_input.replicated_states:
        if state.owner_edge_id not in offsets_by_edge:
            injected_states.append(state)
            continue

        offsets = offsets_by_edge[state.owner_edge_id]
        mutated_observations = {}
        for sensor_name, payload in state.observations_by_sensor.items():
            mutated_pv = replace(
                payload.process_data.pv,
                value=round(payload.process_data.pv.value + offsets[sensor_name], 3),
            )
            mutated_process_data = replace(payload.process_data, pv=mutated_pv)
            mutated_observations[sensor_name] = replace(
                payload,
                process_data=mutated_process_data,
            )

        injected_states.append(
            replace(state, observations_by_sensor=mutated_observations)
        )

    return replace(round_input, replicated_states=tuple(injected_states))


def build_detailed_log_payload(
    *,
    config,
    node_status,
    commit_receipt,
    committed_round,
    consensus_summary,
    consensus_log,
    consensus_alert,
    edges,
    fault_edges: tuple[str, ...],
) -> dict:
    """Build the full deterministic development log payload."""

    return {
        "demo": {
            "mqtt_transport": config.mqtt_transport,
            "mqtt_topic": config.mqtt_topic,
            "fault_mode": config.demo_fault_mode,
            "faulty_edges": list(fault_edges),
            "log_path": config.demo_log_path,
        },
        "cometbft": {
            "node_version": node_status["node_info"]["version"],
            "latest_block_height": node_status["sync_info"]["latest_block_height"],
            "committed_height": commit_receipt.height,
            "tx_hash": commit_receipt.tx_hash,
            "check_tx_code": commit_receipt.check_tx_code,
            "deliver_tx_code": commit_receipt.deliver_tx_code,
        },
        "consensus_summary": consensus_summary.to_dict(),
        "committed_round_state": committed_round,
        "consensus_log": {
            "compact": format_round_log_compact(consensus_log),
            "detailed": format_round_log_detailed(consensus_log),
            "structured": consensus_log.to_dict(),
        },
        "consensus_alert": {
            "compact": format_consensus_alert_compact(consensus_alert),
            "detailed": format_consensus_alert_detailed(consensus_alert),
            "structured": None if consensus_alert is None else consensus_alert.to_dict(),
        },
        "edges": [
            {
                "edge_id": edge.runtime_state()["edge_id"],
                "summary": format_edge_summary(edge),
                "runtime_state": edge.runtime_state(),
                "replicated_state": edge.local_replicated_state(),
                "observation_flow": edge.observation_flow_log(),
            }
            for edge in edges
        ],
    }


def write_detailed_log(log_path: Path, payload: dict) -> Path:
    """Persist the full development trace for one demo run."""

    log_path.parent.mkdir(parents=True, exist_ok=True)
    log_path.write_text(json.dumps(payload, indent=2), encoding="utf-8")
    return log_path


def main() -> None:
    config = load_runtime_demo_config()
    simulator = CompressorSimulator(seed=101)
    edges = [
        TemperatureEdgeService(),
        PressureEdgeService(),
        RpmEdgeService(),
    ]
    transports = []
    if config.mqtt_transport == "passive":
        shared_transport = create_transport(
            config.mqtt_transport,
            host=config.mqtt_broker_host,
            port=config.mqtt_broker_port,
        )
        transports = [shared_transport, shared_transport, shared_transport]
    else:
        transports = [
            create_transport(
                config.mqtt_transport,
                host=config.mqtt_broker_host,
                port=config.mqtt_broker_port,
            )
            for _ in edges
        ]

    for edge, transport in zip(edges, transports, strict=True):
        edge.attach_transport(transport, topic=config.mqtt_topic)
    time.sleep(0.5)

    for step in range(config.demo_steps):
        snapshot = simulator.step(compressor_power=config.demo_power + step)
        for edge in edges:
            payload = edge.acquire(snapshot=snapshot)
            edge.publish_local_observation(payload, topic=config.mqtt_topic)
        time.sleep(0.2)

    time.sleep(1.0)

    print("=== Local Demo Summary ===")
    print("Compact view:")
    for edge in edges:
        print(f"- {format_edge_summary(edge)}")

    consensus_round_input = build_consensus_round_input(edges)
    consensus_round_input = inject_faults(consensus_round_input, config)
    cometbft_client = CometBftRpcClient(config.cometbft_rpc_url)
    node_status = cometbft_client.status()
    commit_receipt = cometbft_client.broadcast_round(consensus_round_input)
    committed_round = cometbft_client.query_committed_round(commit_receipt.round_id)
    consensus_audit = committed_round_to_audit_package(
        consensus_round_input,
        committed_round,
    )
    consensus_summary = build_round_summary(consensus_audit)
    consensus_log = build_round_log(consensus_audit)
    consensus_alert = build_consensus_alert(consensus_audit, consensus_log)
    fault_edges = resolve_faulty_edges(config, consensus_round_input.participating_edges)
    detailed_log_payload = build_detailed_log_payload(
        config=config,
        node_status=node_status,
        commit_receipt=commit_receipt,
        committed_round=committed_round,
        consensus_summary=consensus_summary,
        consensus_log=consensus_log,
        consensus_alert=consensus_alert,
        edges=edges,
        fault_edges=fault_edges,
    )
    detailed_log_path = write_detailed_log(
        default_demo_log_path(config.demo_log_path),
        detailed_log_payload,
    )

    print("\nConsensus summary:")
    print(
        f"- source=cometbft "
        f"node_version={node_status['node_info']['version']} "
        f"latest_block_height={node_status['sync_info']['latest_block_height']}"
    )
    print(
        f"- committed_height={commit_receipt.height} "
        f"tx_hash={commit_receipt.tx_hash} "
        f"check_tx_code={commit_receipt.check_tx_code} "
        f"deliver_tx_code={commit_receipt.deliver_tx_code}"
    )
    print(
        f"- fault_mode={config.demo_fault_mode} "
        f"faulty_edges={list(fault_edges)}"
    )
    print(f"- {format_round_summary(consensus_summary)}")
    print(f"- {format_round_log_compact(consensus_log)}")
    print(f"- {format_consensus_alert_compact(consensus_alert)}")
    print(f"- detailed_log={detailed_log_path}")


if __name__ == "__main__":
    main()
