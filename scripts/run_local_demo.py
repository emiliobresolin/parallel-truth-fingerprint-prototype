"""Run the local edge observation demo against the selected MQTT transport."""

from __future__ import annotations

import json
import sys
import time
from dataclasses import replace
from pathlib import Path
from urllib.parse import urlsplit

PROJECT_ROOT = Path(__file__).resolve().parents[1]
SRC_PATH = PROJECT_ROOT / "src"
if str(SRC_PATH) not in sys.path:
    sys.path.insert(0, str(SRC_PATH))

from parallel_truth_fingerprint.config.runtime import load_runtime_demo_config
from parallel_truth_fingerprint.comparison import (
    build_scada_comparison_output,
    build_scada_divergence_alert,
    compare_consensused_to_scada,
    format_scada_alert_compact,
    format_scada_alert_detailed,
    format_scada_comparison_output_compact,
)
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
from parallel_truth_fingerprint.lstm_service import (
    FingerprintLifecycleStage,
    ScadaReplayRuntimeStage,
    configure_scada_replay_runtime_stage,
    execute_deferred_fingerprint_lifecycle,
    run_scada_replay_behavior_detection,
)
from parallel_truth_fingerprint.persistence import (
    MinioArtifactStore,
    MinioStoreConfig,
    PersistenceBlockedError,
    persist_valid_consensus_artifact,
)
from parallel_truth_fingerprint.scada import FakeOpcUaScadaService
from parallel_truth_fingerprint.scenario_control import (
    RuntimeScenarioControlStage,
    apply_runtime_scenario_control,
    resolve_runtime_scenario_control_stage,
)
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
    cycle_index: int,
    config,
    simulator_snapshot: dict[str, object] | None,
    node_status,
    commit_receipt,
    committed_round,
    consensus_summary,
    consensus_log,
    consensus_alert,
    scada_state,
    comparison_stage,
    comparison_output,
    scada_alert,
    persistence_stage,
    cadence_stage: dict[str, object],
    scenario_control_stage: RuntimeScenarioControlStage,
    fingerprint_stage: FingerprintLifecycleStage,
    fingerprint_inference_results,
    scada_replay_stage: ScadaReplayRuntimeStage,
    replay_behavior_result,
    replay_inference_results,
    edges,
    fault_edges: tuple[str, ...],
) -> dict:
    """Build the full deterministic development log payload for one cycle."""

    return {
        "demo": {
            "cycle_index": cycle_index,
            "mqtt_transport": config.mqtt_transport,
            "mqtt_topic": config.mqtt_topic,
            "fault_mode": config.demo_fault_mode,
            "faulty_edges": list(fault_edges),
            "log_path": config.demo_log_path,
            "cycle_interval_seconds": config.demo_cycle_interval_seconds,
            "train_after_eligible_cycles": config.demo_train_after_eligible_cycles,
            "fingerprint_sequence_length": config.demo_fingerprint_sequence_length,
            "scenario_name": config.demo_scenario_name,
            "scenario_start_cycle": config.demo_scenario_start_cycle,
            "scada_mode": config.demo_scada_mode,
            "scada_start_cycle": config.demo_scada_start_cycle,
        },
        "runtime_cycle": {
            "current_cycle": cycle_index,
            "cadence_stage": cadence_stage,
        },
        "simulator_snapshot": simulator_snapshot,
        "scenario_control": scenario_control_stage.to_dict(),
        "scada_runtime_scenario": scada_replay_stage.to_dict(),
        "fingerprint_lifecycle": fingerprint_stage.to_dict(),
        "fingerprint_inference_results": [
            result.to_dict() for result in fingerprint_inference_results
        ],
        "replay_behavior": None
        if replay_behavior_result is None
        else replay_behavior_result.to_dict(),
        "replay_inference_results": [
            result.to_dict() for result in replay_inference_results
        ],
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
        "scada_state": None if scada_state is None else scada_state.to_dict(),
        "comparison_stage": comparison_stage,
        "comparison_output": {
            "compact": None
            if comparison_output is None
            else format_scada_comparison_output_compact(comparison_output),
            "structured": None if comparison_output is None else comparison_output.to_dict(),
        },
        "scada_divergence_alert": {
            "compact": format_scada_alert_compact(scada_alert),
            "detailed": format_scada_alert_detailed(scada_alert),
            "structured": None if scada_alert is None else scada_alert.to_dict(),
        },
        "persistence_stage": persistence_stage,
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


def build_runtime_log_payload(
    *,
    config,
    runtime_status: str,
    cycle_history: list[dict[str, object]],
    latest_cycle_payload: dict[str, object] | None,
) -> dict[str, object]:
    """Build the continuous-runtime log envelope for the live demo."""

    latest_fingerprint_stage = (
        {}
        if latest_cycle_payload is None
        else latest_cycle_payload.get("fingerprint_lifecycle", {})
    )
    return {
        "runtime": {
            "status": runtime_status,
            "completed_cycles": len(cycle_history),
            "current_cycle": 0 if not cycle_history else cycle_history[-1]["cycle_index"],
            "cycle_interval_seconds": config.demo_cycle_interval_seconds,
            "max_cycles": config.demo_max_cycles,
            "configured_power_pct": config.demo_power,
            "train_after_eligible_cycles": config.demo_train_after_eligible_cycles,
            "fingerprint_sequence_length": config.demo_fingerprint_sequence_length,
            "model_status": latest_fingerprint_stage.get("model_status"),
            "training_events": latest_fingerprint_stage.get("training_events", []),
            "latest_valid_artifact_count": latest_fingerprint_stage.get(
                "valid_artifact_count"
            ),
            "latest_eligible_history_count": latest_fingerprint_stage.get(
                "eligible_history_count"
            ),
            "latest_window_count": latest_fingerprint_stage.get("window_count"),
        },
        "scenario_control": {
            "configured_scenario": config.demo_scenario_name or None,
            "scenario_start_cycle": config.demo_scenario_start_cycle,
        },
        "cycle_history": cycle_history,
        "latest_cycle": latest_cycle_payload,
    }


def format_comparison_stage_compact(stage: dict[str, object]) -> str:
    """Render one compact comparison-stage line for demo output."""

    if stage["status"] == "blocked":
        return f"comparison=blocked reason={stage['reason']}"
    return stage["compact"]


def format_persistence_stage_compact(stage: dict[str, object]) -> str:
    """Render one compact persistence-stage line for demo output."""

    if stage["status"] == "blocked":
        return (
            f"persistence=blocked "
            f"backend={stage['backend']} "
            f"endpoint={stage['endpoint']} "
            f"secure={str(stage['secure']).lower()} "
            f"bucket={stage['bucket']} "
            f"reason={stage['reason']}"
        )
    if stage["status"] == "error":
        return (
            f"persistence=error "
            f"backend={stage['backend']} "
            f"endpoint={stage['endpoint']} "
            f"secure={str(stage['secure']).lower()} "
            f"bucket={stage['bucket']} "
            f"reason={stage['reason']}"
        )
    return (
        f"persistence={stage['status']} "
        f"backend={stage['backend']} "
        f"endpoint={stage['endpoint']} "
        f"secure={str(stage['secure']).lower()} "
        f"bucket={stage['bucket']} "
        f"artifact_key={stage['artifact_key']} "
        f"artifact_uri={stage['artifact_uri']}"
    )


def build_cadence_stage(
    *,
    cycle_index: int,
    configured_interval_seconds: float,
    elapsed_seconds: float,
    next_sleep_seconds: float,
    will_continue: bool,
) -> dict[str, object]:
    """Return structured cadence metadata for one runtime cycle."""

    status = "sleeping_until_next_cycle" if will_continue else "cycle_complete"
    if will_continue and next_sleep_seconds == 0.0:
        status = "continuing_without_sleep"
    return {
        "cycle_index": cycle_index,
        "status": status,
        "configured_interval_seconds": round(configured_interval_seconds, 3),
        "elapsed_seconds": round(elapsed_seconds, 3),
        "next_sleep_seconds": round(next_sleep_seconds, 3),
        "will_continue": will_continue,
    }


def format_cadence_stage_compact(stage: dict[str, object]) -> str:
    """Render one compact cadence line for demo output."""

    return (
        f"cycle={stage['cycle_index']} "
        f"cadence={stage['status']} "
        f"interval_seconds={stage['configured_interval_seconds']} "
        f"elapsed_seconds={stage['elapsed_seconds']} "
        f"next_sleep_seconds={stage['next_sleep_seconds']}"
    )


def sleep_until_next_cycle(
    *,
    total_seconds: float,
    sleep_fn=time.sleep,
    stop_requested_fn=None,
    poll_interval_seconds: float = 0.1,
) -> bool:
    """Sleep in small slices so the runtime can stop promptly from the UI."""

    remaining_seconds = max(total_seconds, 0.0)
    if stop_requested_fn is None:
        if remaining_seconds > 0.0:
            sleep_fn(remaining_seconds)
        return False
    while remaining_seconds > 0.0:
        if stop_requested_fn is not None and stop_requested_fn():
            return True
        next_slice = min(remaining_seconds, poll_interval_seconds)
        sleep_fn(next_slice)
        remaining_seconds = max(remaining_seconds - next_slice, 0.0)
    return stop_requested_fn is not None and stop_requested_fn()


def format_scenario_control_compact(stage: RuntimeScenarioControlStage) -> str:
    """Render one compact scenario-control line for demo output."""

    expected_outputs = ",".join(stage.expected_output_channels)
    return (
        f"scenario=active={str(stage.active).lower()} "
        f"configured={stage.configured_scenario} "
        f"current={stage.active_scenario} "
        f"start_cycle={stage.start_cycle} "
        f"training_eligible={str(stage.training_eligible).lower()} "
        f"expected_outputs={expected_outputs}"
    )


def format_fingerprint_lifecycle_compact(stage: FingerprintLifecycleStage) -> str:
    """Render one compact fingerprint-lifecycle line for demo output."""

    training_state = "+".join(stage.training_events)
    latest_artifact = stage.latest_valid_artifact_key or "none"
    parts = [
        f"fingerprint=model_status={stage.model_status}",
        f"training={training_state}",
        f"inference={stage.inference_status}",
        f"valid_artifacts={stage.valid_artifact_count}",
        (
            f"eligible_history={stage.eligible_history_count}/"
            f"{stage.eligible_history_threshold}"
        ),
        f"windows={stage.window_count}",
        f"latest_artifact={latest_artifact}",
    ]
    if stage.dataset_manifest_object_key is not None:
        parts.append(f"dataset_manifest={stage.dataset_manifest_object_key}")
    if stage.model_metadata_object_key is not None:
        parts.append(f"model_metadata={stage.model_metadata_object_key}")
    if stage.source_dataset_validation_level is not None:
        parts.append(
            f"validation_level={stage.source_dataset_validation_level}"
        )
    return " ".join(parts)


def format_inference_results_compact(fingerprint_inference_results) -> str:
    """Render one compact inference line for demo output."""

    if not fingerprint_inference_results:
        return "fingerprint_inference=none"
    first_result = fingerprint_inference_results[0]
    return (
        f"fingerprint_inference=completed "
        f"results={len(fingerprint_inference_results)} "
        f"classification={first_result.classification.value} "
        f"score={round(first_result.anomaly_score, 6)} "
        f"threshold={round(first_result.classification_threshold, 6)} "
        f"validation_level={first_result.source_dataset_validation_level}"
    )


def format_scada_runtime_scenario_compact(stage: ScadaReplayRuntimeStage) -> str:
    """Render one compact SCADA replay/freeze scenario line for demo output."""

    return (
        f"scada_runtime=active={str(stage.active).lower()} "
        f"mode={stage.mode} "
        f"start_cycle={stage.start_cycle} "
        f"replay_source_round_id={stage.replay_source_round_id or 'none'}"
    )


def format_replay_behavior_compact(replay_behavior_result) -> str:
    """Render one compact replay-behavior line for demo output."""

    if replay_behavior_result is None:
        return "replay_behavior=none"
    return (
        f"replay_behavior=completed "
        f"mode={replay_behavior_result.scenario_mode} "
        f"classification={replay_behavior_result.classification.value} "
        f"score={round(replay_behavior_result.anomaly_score, 6)} "
        f"threshold={round(replay_behavior_result.classification_threshold, 6)} "
        f"replay_source_round_id={replay_behavior_result.replay_source_round_id or 'none'}"
    )


def build_minio_runtime_metadata(artifact_store) -> dict[str, object]:
    """Return normalized MinIO metadata for terminal and JSON log visibility."""

    config = artifact_store.config
    endpoint = config.endpoint
    parsed = urlsplit(f"http://{endpoint}")
    return {
        "backend": "minio",
        "endpoint": endpoint,
        "host": parsed.hostname or endpoint,
        "port": parsed.port,
        "secure": getattr(config, "secure", False),
        "bucket": config.bucket,
    }


def build_dataset_context(
    *,
    fault_mode: str,
    comparison_output,
    scenario_control_stage: RuntimeScenarioControlStage | None = None,
    scada_replay_stage: ScadaReplayRuntimeStage | None = None,
) -> dict[str, object]:
    """Return explicit dataset eligibility metadata for persisted artifacts."""

    if scenario_control_stage is not None and not scenario_control_stage.training_eligible:
        return {
            "scenario_label": scenario_control_stage.scenario_label,
            "training_label": scenario_control_stage.training_label,
            "training_eligible": scenario_control_stage.training_eligible,
            "training_eligibility_reason": (
                scenario_control_stage.training_eligibility_reason
            ),
        }
    if scada_replay_stage is not None and scada_replay_stage.active:
        return {
            "scenario_label": f"scada_{scada_replay_stage.mode}",
            "training_label": "non_normal",
            "training_eligible": False,
            "training_eligibility_reason": f"scada_{scada_replay_stage.mode}",
        }
    if comparison_output.divergent_sensors:
        return {
            "scenario_label": "scada_divergence",
            "training_label": "non_normal",
            "training_eligible": False,
            "training_eligibility_reason": "scada_divergence",
        }
    if fault_mode == "none":
        if scenario_control_stage is not None:
            return {
                "scenario_label": scenario_control_stage.scenario_label,
                "training_label": scenario_control_stage.training_label,
                "training_eligible": scenario_control_stage.training_eligible,
                "training_eligibility_reason": (
                    scenario_control_stage.training_eligibility_reason
                ),
            }
        return {
            "scenario_label": "normal",
            "training_label": "normal",
            "training_eligible": True,
            "training_eligibility_reason": "normal_validated_run",
        }
    if fault_mode == "single_edge_exclusion":
        return {
            "scenario_label": "faulty_edge_exclusion",
            "training_label": "non_normal",
            "training_eligible": False,
            "training_eligibility_reason": "faulty_edge_exclusion",
        }
    return {
        "scenario_label": fault_mode,
        "training_label": "non_normal",
        "training_eligible": False,
        "training_eligibility_reason": f"scenario:{fault_mode}",
    }


def run_scada_comparison_and_persistence(
    *,
    consensus_audit,
    artifact_store,
    scada_service=None,
    fault_mode: str = "none",
    scenario_control_stage: RuntimeScenarioControlStage | None = None,
    scada_replay_stage: ScadaReplayRuntimeStage | None = None,
) -> tuple[object | None, dict[str, object], object | None, object | None, dict[str, object]]:
    """Run the Story 3 comparison/persistence path for demo observability."""

    storage_metadata = build_minio_runtime_metadata(artifact_store)
    valid_state = consensus_audit.consensused_valid_state
    if valid_state is None:
        blocked_reason = "no_consensused_valid_state"
        return (
            None,
            {"status": "blocked", "reason": blocked_reason, "compact": None},
            None,
            None,
            {
                "status": "blocked",
                **storage_metadata,
                "reason": blocked_reason,
                "write_confirmed": False,
            },
        )

    resolved_scada_service = (
        scada_service if scada_service is not None else FakeOpcUaScadaService(compressor_id="compressor-1")
    )
    scada_state = resolved_scada_service.update_from_consensused_state(valid_state)
    comparison_result = compare_consensused_to_scada(
        valid_state=valid_state,
        scada_state=scada_state,
    )
    comparison_output = build_scada_comparison_output(comparison_result)
    scada_alert = build_scada_divergence_alert(comparison_output)

    comparison_stage = {
        "status": "completed",
        "compact": format_scada_comparison_output_compact(comparison_output),
    }

    try:
        dataset_context = build_dataset_context(
            fault_mode=fault_mode,
            comparison_output=comparison_output,
            scenario_control_stage=scenario_control_stage,
            scada_replay_stage=scada_replay_stage,
        )
        persistence_record = persist_valid_consensus_artifact(
            audit_package=consensus_audit,
            scada_state=scada_state,
            scada_comparison_output=comparison_output,
            scada_alert=scada_alert,
            dataset_context=dataset_context,
            artifact_store=artifact_store,
        )
        persistence_stage = {
            "status": "persisted",
            **storage_metadata,
            "artifact_key": persistence_record.artifact_key,
            "object_name": persistence_record.artifact_key,
            "artifact_uri": (
                f"minio://{artifact_store.config.bucket}/{persistence_record.artifact_key}"
            ),
            "storage_action": "put_object",
            "content_type": "application/json",
            "write_confirmed": True,
            "record": persistence_record.to_dict(),
        }
    except PersistenceBlockedError as exc:
        persistence_stage = {
            "status": "blocked",
            **storage_metadata,
            "reason": str(exc),
            "write_confirmed": False,
        }
    except Exception as exc:
        persistence_stage = {
            "status": "error",
            **storage_metadata,
            "reason": str(exc),
            "write_confirmed": False,
        }

    return (
        scada_state,
        comparison_stage,
        comparison_output,
        scada_alert,
        persistence_stage,
    )


def build_demo_artifact_store(config) -> MinioArtifactStore:
    """Build the real runtime artifact store for the local demo path."""

    return MinioArtifactStore(
        MinioStoreConfig(
            endpoint=config.minio_endpoint,
            access_key=config.minio_access_key,
            secret_key=config.minio_secret_key,
            bucket=config.minio_bucket,
            secure=config.minio_secure,
        )
    )


def build_demo_runtime_components(config) -> dict[str, object]:
    """Build the local runtime components for CLI or dashboard control."""

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

    return {
        "simulator": simulator,
        "edges": edges,
        "cometbft_client": CometBftRpcClient(config.cometbft_rpc_url),
        "artifact_store": build_demo_artifact_store(config),
        "scada_service": FakeOpcUaScadaService(compressor_id="compressor-1"),
    }


def build_lifecycle_error_stage(
    *,
    cycle_index: int,
    config,
    artifact_key: str | None,
    error: Exception,
) -> FingerprintLifecycleStage:
    """Return a conservative lifecycle stage when lifecycle orchestration fails."""

    return FingerprintLifecycleStage(
        cycle_index=cycle_index,
        valid_artifact_count=0,
        eligible_history_count=0,
        eligible_history_threshold=config.demo_train_after_eligible_cycles,
        window_count=0,
        latest_valid_artifact_key=artifact_key,
        model_status="error",
        training_events=("deferred",),
        inference_status=f"error:{error}",
        inference_result_count=0,
        limitation_note=str(error),
    )


def execute_demo_cycle(
    *,
    cycle_index: int,
    config,
    simulator,
    edges,
    cometbft_client,
    artifact_store,
    scada_service,
    sleep_fn=time.sleep,
) -> dict[str, object]:
    """Execute one full prototype cycle for the live demo runtime."""

    scenario_control_stage = resolve_runtime_scenario_control_stage(
        config=config,
        cycle_index=cycle_index,
    )
    cycle_config = apply_runtime_scenario_control(
        config=config,
        scenario_stage=scenario_control_stage,
    )

    latest_snapshot = None
    for _ in range(config.demo_steps):
        snapshot = simulator.step(compressor_power=config.demo_power)
        latest_snapshot = snapshot
        for edge in edges:
            payload = edge.acquire(snapshot=snapshot)
            edge.publish_local_observation(payload, topic=config.mqtt_topic)
        sleep_fn(0.2)

    sleep_fn(1.0)

    consensus_round_input = build_consensus_round_input(edges)
    consensus_round_input = inject_faults(consensus_round_input, cycle_config)
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
    scada_replay_stage = configure_scada_replay_runtime_stage(
        scada_service=scada_service,
        config=cycle_config,
        cycle_index=cycle_index,
    )
    scada_state, comparison_stage, comparison_output, scada_alert, persistence_stage = (
        run_scada_comparison_and_persistence(
            consensus_audit=consensus_audit,
            artifact_store=artifact_store,
            scada_service=scada_service,
            fault_mode=cycle_config.demo_fault_mode,
            scenario_control_stage=scenario_control_stage,
            scada_replay_stage=scada_replay_stage,
        )
    )
    fault_edges = resolve_faulty_edges(
        cycle_config,
        consensus_round_input.participating_edges,
    )
    try:
        fingerprint_stage, fingerprint_inference_results = (
            execute_deferred_fingerprint_lifecycle(
                cycle_index=cycle_index,
                artifact_store=artifact_store,
                sequence_length=config.demo_fingerprint_sequence_length,
                train_after_eligible_cycles=config.demo_train_after_eligible_cycles,
            )
        )
    except Exception as exc:
        fingerprint_stage = build_lifecycle_error_stage(
            cycle_index=cycle_index,
            config=config,
            artifact_key=persistence_stage.get("artifact_key"),
            error=exc,
        )
        fingerprint_inference_results = ()

    try:
        replay_behavior_result, replay_inference_results = (
            run_scada_replay_behavior_detection(
                current_round_id=consensus_summary.round_id,
                consensus_final_status=consensus_summary.final_consensus_status.value,
                scada_state=scada_state,
                comparison_output=comparison_output,
                replay_stage=scada_replay_stage,
                artifact_store=artifact_store,
                sequence_length=config.demo_fingerprint_sequence_length,
            )
            if scada_state is not None and comparison_output is not None
            else (None, ())
        )
    except Exception as exc:
        replay_behavior_result = None
        replay_inference_results = ()
        comparison_stage = {
            **comparison_stage,
            "replay_behavior_error": str(exc),
        }

    return {
        "cycle_index": cycle_index,
        "simulator_snapshot": None
        if latest_snapshot is None
        else latest_snapshot.to_dict(),
        "node_status": node_status,
        "commit_receipt": commit_receipt,
        "committed_round": committed_round,
        "consensus_summary": consensus_summary,
        "consensus_log": consensus_log,
        "consensus_alert": consensus_alert,
        "scada_state": scada_state,
        "comparison_stage": comparison_stage,
        "comparison_output": comparison_output,
        "scada_alert": scada_alert,
        "persistence_stage": persistence_stage,
        "fault_edges": fault_edges,
        "scenario_control_stage": scenario_control_stage,
        "scada_replay_stage": scada_replay_stage,
        "fingerprint_stage": fingerprint_stage,
        "fingerprint_inference_results": fingerprint_inference_results,
        "replay_behavior_result": replay_behavior_result,
        "replay_inference_results": replay_inference_results,
        "edges": edges,
    }


def build_cycle_history_entry(
    *,
    cycle_result: dict[str, object],
    cadence_stage: dict[str, object],
) -> dict[str, object]:
    """Return one compact cycle-history entry for the runtime log."""

    consensus_summary = cycle_result["consensus_summary"]
    persistence_stage = cycle_result["persistence_stage"]
    fingerprint_stage = cycle_result["fingerprint_stage"]
    return {
        "cycle_index": cycle_result["cycle_index"],
        "round_id": consensus_summary.round_id,
        "final_consensus_status": consensus_summary.final_consensus_status.value,
        "persistence_status": persistence_stage["status"],
        "artifact_key": persistence_stage.get("artifact_key"),
        "cadence_stage": cadence_stage,
        "scenario_control": cycle_result["scenario_control_stage"].to_dict(),
        "scada_runtime_scenario": cycle_result["scada_replay_stage"].to_dict(),
        "fingerprint_lifecycle": fingerprint_stage.to_dict(),
        "replay_behavior": None
        if cycle_result["replay_behavior_result"] is None
        else cycle_result["replay_behavior_result"].to_dict(),
    }


def print_cycle_report(
    *,
    cycle_result: dict[str, object],
    cadence_stage: dict[str, object],
    config,
    detailed_log_path: Path,
) -> None:
    """Print one compact cycle report for the live terminal output."""

    print(f"=== Local Demo Cycle {cycle_result['cycle_index']} ===")
    print("Compact view:")
    for edge in cycle_result["edges"]:
        print(f"- {format_edge_summary(edge)}")
    if cycle_result["simulator_snapshot"] is not None:
        compressor_state = cycle_result["simulator_snapshot"]
        print(
            "- "
            f"compressor={compressor_state['compressor_id']} "
            f"power_pct={compressor_state['operating_state_pct']} "
            f"sensors={compressor_state['sensors']}"
        )

    node_status = cycle_result["node_status"]
    commit_receipt = cycle_result["commit_receipt"]
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
        f"- fault_mode={cycle_result['scenario_control_stage'].fault_mode} "
        f"faulty_edges={list(cycle_result['fault_edges'])}"
    )
    print(f"- {format_round_summary(cycle_result['consensus_summary'])}")
    print(f"- {format_round_log_compact(cycle_result['consensus_log'])}")
    print(f"- {format_consensus_alert_compact(cycle_result['consensus_alert'])}")
    print(f"- {format_cadence_stage_compact(cadence_stage)}")
    print(f"- {format_scenario_control_compact(cycle_result['scenario_control_stage'])}")
    print(f"- {format_scada_runtime_scenario_compact(cycle_result['scada_replay_stage'])}")
    print(f"- {format_comparison_stage_compact(cycle_result['comparison_stage'])}")
    print(f"- {format_scada_alert_compact(cycle_result['scada_alert'])}")
    print(f"- {format_persistence_stage_compact(cycle_result['persistence_stage'])}")
    print(
        f"- {format_fingerprint_lifecycle_compact(cycle_result['fingerprint_stage'])}"
    )
    print(
        f"- {format_inference_results_compact(cycle_result['fingerprint_inference_results'])}"
    )
    print(f"- {format_replay_behavior_compact(cycle_result['replay_behavior_result'])}")
    print(f"- detailed_log={detailed_log_path}")


def run_autonomous_demo_loop(
    *,
    config,
    simulator,
    edges,
    cometbft_client,
    artifact_store,
    scada_service,
    sleep_fn=time.sleep,
    monotonic_fn=time.monotonic,
    config_provider=None,
    stop_requested_fn=None,
    cycle_observer=None,
) -> dict[str, object]:
    """Run the Story 4.3A autonomous runtime loop until manual stop or max cycles."""

    cycle_history: list[dict[str, object]] = []
    latest_cycle_payload: dict[str, object] | None = None
    log_path = default_demo_log_path(config.demo_log_path)
    cycle_index = 0

    try:
        while True:
            current_config = config_provider() if config_provider is not None else config
            if stop_requested_fn is not None and stop_requested_fn():
                runtime_payload = build_runtime_log_payload(
                    config=current_config,
                    runtime_status="stopped_operator",
                    cycle_history=cycle_history,
                    latest_cycle_payload=latest_cycle_payload,
                )
                write_detailed_log(log_path, runtime_payload)
                if cycle_observer is not None:
                    cycle_observer(runtime_payload)
                return runtime_payload
            if current_config.demo_max_cycles > 0 and cycle_index >= current_config.demo_max_cycles:
                runtime_payload = build_runtime_log_payload(
                    config=current_config,
                    runtime_status="completed",
                    cycle_history=cycle_history,
                    latest_cycle_payload=latest_cycle_payload,
                )
                if cycle_observer is not None:
                    cycle_observer(runtime_payload)
                return runtime_payload

            cycle_index += 1
            cycle_started_at = monotonic_fn()
            cycle_result = execute_demo_cycle(
                cycle_index=cycle_index,
                config=current_config,
                simulator=simulator,
                edges=edges,
                cometbft_client=cometbft_client,
                artifact_store=artifact_store,
                scada_service=scada_service,
                sleep_fn=sleep_fn,
            )
            elapsed_seconds = max(monotonic_fn() - cycle_started_at, 0.0)
            will_continue = (
                current_config.demo_max_cycles <= 0
                or cycle_index < current_config.demo_max_cycles
            )
            next_sleep_seconds = (
                max(current_config.demo_cycle_interval_seconds - elapsed_seconds, 0.0)
                if will_continue
                else 0.0
            )
            cadence_stage = build_cadence_stage(
                cycle_index=cycle_index,
                configured_interval_seconds=current_config.demo_cycle_interval_seconds,
                elapsed_seconds=elapsed_seconds,
                next_sleep_seconds=next_sleep_seconds,
                will_continue=will_continue,
            )
            latest_cycle_payload = build_detailed_log_payload(
                cycle_index=cycle_index,
                config=current_config,
                simulator_snapshot=cycle_result["simulator_snapshot"],
                node_status=cycle_result["node_status"],
                commit_receipt=cycle_result["commit_receipt"],
                committed_round=cycle_result["committed_round"],
                consensus_summary=cycle_result["consensus_summary"],
                consensus_log=cycle_result["consensus_log"],
                consensus_alert=cycle_result["consensus_alert"],
                scada_state=cycle_result["scada_state"],
                comparison_stage=cycle_result["comparison_stage"],
                comparison_output=cycle_result["comparison_output"],
                scada_alert=cycle_result["scada_alert"],
                persistence_stage=cycle_result["persistence_stage"],
                cadence_stage=cadence_stage,
                scenario_control_stage=cycle_result["scenario_control_stage"],
                fingerprint_stage=cycle_result["fingerprint_stage"],
                fingerprint_inference_results=cycle_result[
                    "fingerprint_inference_results"
                ],
                scada_replay_stage=cycle_result["scada_replay_stage"],
                replay_behavior_result=cycle_result["replay_behavior_result"],
                replay_inference_results=cycle_result["replay_inference_results"],
                edges=cycle_result["edges"],
                fault_edges=cycle_result["fault_edges"],
            )
            cycle_history.append(
                build_cycle_history_entry(
                    cycle_result=cycle_result,
                    cadence_stage=cadence_stage,
                )
            )
            runtime_payload = build_runtime_log_payload(
                config=current_config,
                runtime_status="active" if will_continue else "completed",
                cycle_history=cycle_history,
                latest_cycle_payload=latest_cycle_payload,
            )
            detailed_log_path = write_detailed_log(log_path, runtime_payload)
            if cycle_observer is not None:
                cycle_observer(runtime_payload)
            print_cycle_report(
                cycle_result=cycle_result,
                cadence_stage=cadence_stage,
                config=current_config,
                detailed_log_path=detailed_log_path,
            )
            if not will_continue:
                return runtime_payload
            if sleep_until_next_cycle(
                total_seconds=next_sleep_seconds,
                sleep_fn=sleep_fn,
                stop_requested_fn=stop_requested_fn,
            ):
                runtime_payload = build_runtime_log_payload(
                    config=current_config,
                    runtime_status="stopped_operator",
                    cycle_history=cycle_history,
                    latest_cycle_payload=latest_cycle_payload,
                )
                write_detailed_log(log_path, runtime_payload)
                if cycle_observer is not None:
                    cycle_observer(runtime_payload)
                return runtime_payload
    except KeyboardInterrupt:
        runtime_payload = build_runtime_log_payload(
            config=config,
            runtime_status="stopped_manually",
            cycle_history=cycle_history,
            latest_cycle_payload=latest_cycle_payload,
        )
        write_detailed_log(log_path, runtime_payload)
        if cycle_observer is not None:
            cycle_observer(runtime_payload)
        print("\nRuntime stopped manually.")
        return runtime_payload


def main() -> None:
    config = load_runtime_demo_config()
    components = build_demo_runtime_components(config)
    run_autonomous_demo_loop(
        config=config,
        simulator=components["simulator"],
        edges=components["edges"],
        cometbft_client=components["cometbft_client"],
        artifact_store=components["artifact_store"],
        scada_service=components["scada_service"],
    )


if __name__ == "__main__":
    main()
