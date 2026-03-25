"""Run the local edge observation demo against the selected MQTT transport."""

from __future__ import annotations

import json
import sys
import time
from pathlib import Path

PROJECT_ROOT = Path(__file__).resolve().parents[1]
SRC_PATH = PROJECT_ROOT / "src"
if str(SRC_PATH) not in sys.path:
    sys.path.insert(0, str(SRC_PATH))

from parallel_truth_fingerprint.config.runtime import load_runtime_demo_config
from parallel_truth_fingerprint.consensus import (
    ConsensusEngine,
    build_round_summary,
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
    consensus_engine = ConsensusEngine()
    consensus_audit = consensus_engine.evaluate(consensus_round_input)
    consensus_summary = build_round_summary(consensus_audit)

    print("\nConsensus summary:")
    print(f"- {format_round_summary(consensus_summary)}")
    print(json.dumps(consensus_summary.to_dict(), indent=2))

    print("\nDetailed view:")
    for edge in edges:
        print(f"\n[{edge.runtime_state()['edge_id']}]")
        print("Runtime state:")
        print(json.dumps(edge.runtime_state(), indent=2))
        print("Replicated state:")
        print(json.dumps(edge.local_replicated_state(), indent=2))
        print("Observation flow:")
        print(json.dumps(edge.observation_flow_log(), indent=2))


if __name__ == "__main__":
    main()
