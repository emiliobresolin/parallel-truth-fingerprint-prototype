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
    ConsensusEngine,
    build_consensus_alert,
    build_round_log,
    build_round_summary,
    format_consensus_alert_compact,
    format_consensus_alert_detailed,
    format_round_log_compact,
    format_round_log_detailed,
    format_round_summary,
)
from parallel_truth_fingerprint.contracts.consensus_round_input import ConsensusRoundInput
from parallel_truth_fingerprint.edge_nodes.common.mqtt_io import create_transport
from parallel_truth_fingerprint.edge_nodes.edge_1.service import TemperatureEdgeService
from parallel_truth_fingerprint.edge_nodes.edge_2.service import PressureEdgeService
from parallel_truth_fingerprint.edge_nodes.edge_3.service import RpmEdgeService
from parallel_truth_fingerprint.sensor_simulation.simulator import CompressorSimulator


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
    consensus_engine = ConsensusEngine()
    consensus_audit = consensus_engine.evaluate(consensus_round_input)
    consensus_summary = build_round_summary(consensus_audit)
    consensus_log = build_round_log(consensus_audit)
    consensus_alert = build_consensus_alert(consensus_audit, consensus_log)

    print("\nConsensus summary:")
    print(
        f"- fault_mode={config.demo_fault_mode} "
        f"faulty_edges={list(resolve_faulty_edges(config, consensus_round_input.participating_edges))}"
    )
    print(f"- {format_round_summary(consensus_summary)}")
    print(json.dumps(consensus_summary.to_dict(), indent=2))
    print("\nConsensus log compact:")
    print(f"- {format_round_log_compact(consensus_log)}")
    print("\nConsensus log detailed:")
    print(format_round_log_detailed(consensus_log))
    print("\nConsensus log structured:")
    print(json.dumps(consensus_log.to_dict(), indent=2))
    print("\nConsensus alert compact:")
    print(f"- {format_consensus_alert_compact(consensus_alert)}")
    print("\nConsensus alert detailed:")
    print(format_consensus_alert_detailed(consensus_alert))
    print("\nConsensus alert structured:")
    print(json.dumps(None if consensus_alert is None else consensus_alert.to_dict(), indent=2))

    print("\nDetailed view:")
    for edge in edges:
        print(f"\n[{edge.runtime_state()['edge_id']}]")
        print("Runtime state:")
        print(json.dumps(edge.runtime_state(), indent=2))
        print("Replicated state:")
        print(json.dumps(edge.local_replicated_state(), indent=2))
        #print("Observation flow:")
        #print(json.dumps(edge.observation_flow_log(), indent=2))


if __name__ == "__main__":
    main()
