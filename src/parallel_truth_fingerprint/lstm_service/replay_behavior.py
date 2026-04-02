"""Replay-oriented anomaly helpers for Epic 4 Story 4.4."""

from __future__ import annotations

from dataclasses import dataclass

from parallel_truth_fingerprint.contracts.replay_behavior import ReplayBehaviorResult
from parallel_truth_fingerprint.contracts.training_dataset import (
    TrainingDatasetManifest,
    TrainingWindow,
)
from parallel_truth_fingerprint.lstm_service.dataset_artifacts import (
    persist_training_dataset_artifacts,
)
from parallel_truth_fingerprint.lstm_service.dataset_builder import extract_feature_vector
from parallel_truth_fingerprint.lstm_service.inference import (
    run_lstm_fingerprint_inference_from_persisted_dataset,
)
from parallel_truth_fingerprint.lstm_service.lifecycle import latest_model_metadata_key
from parallel_truth_fingerprint.scada import SUPPORTED_SCADA_SENSORS


REPLAY_OUTPUT_CHANNEL = "scada_replay_behavior"
VALID_ARTIFACT_PREFIX = "valid-consensus-artifacts/"
DEFAULT_REPLAY_THRESHOLD_STDDEV_MULTIPLIER = 0.0


@dataclass(frozen=True)
class ScadaReplayRuntimeStage:
    """Structured SCADA logical-side runtime state for one cycle."""

    active: bool
    mode: str
    start_cycle: int
    replay_source_round_id: str | None = None

    def to_dict(self) -> dict[str, object]:
        return {
            "active": self.active,
            "mode": self.mode,
            "start_cycle": self.start_cycle,
            "replay_source_round_id": self.replay_source_round_id,
        }


def configure_scada_replay_runtime_stage(
    *,
    scada_service,
    config,
    cycle_index: int,
) -> ScadaReplayRuntimeStage:
    """Configure the stateful fake SCADA service for one runtime cycle."""

    scada_service.clear_overrides()
    mode = getattr(config, "demo_scada_mode", "match")
    start_cycle = getattr(config, "demo_scada_start_cycle", 0)
    if mode in {"none", "match"} or start_cycle <= 0 or cycle_index < start_cycle:
        return ScadaReplayRuntimeStage(active=False, mode="match", start_cycle=start_cycle)

    replay_source_round_id = None
    if mode == "replay" and scada_service.history():
        replay_source_round_id = scada_service.history()[0].source_round_id

    for sensor_name in SUPPORTED_SCADA_SENSORS:
        if mode == "freeze":
            scada_service.set_sensor_override(sensor_name, mode="freeze")
        elif mode == "replay":
            scada_service.set_sensor_override(
                sensor_name,
                mode="replay",
                replay_round_id=replay_source_round_id,
            )
        elif mode == "offset":
            scada_service.set_sensor_override(
                sensor_name,
                mode="offset",
                offset=_resolve_scada_offset(sensor_name, config),
            )

    return ScadaReplayRuntimeStage(
        active=True,
        mode=mode,
        start_cycle=start_cycle,
        replay_source_round_id=replay_source_round_id,
    )


def run_scada_replay_behavior_detection(
    *,
    current_round_id: str,
    consensus_final_status: str,
    scada_state,
    comparison_output,
    replay_stage: ScadaReplayRuntimeStage,
    artifact_store,
    sequence_length: int,
    threshold_stddev_multiplier: float = DEFAULT_REPLAY_THRESHOLD_STDDEV_MULTIPLIER,
) -> tuple[ReplayBehaviorResult | None, tuple]:
    """Run replay/freeze detection through the existing fingerprint path."""

    if not replay_stage.active or replay_stage.mode not in {"replay", "freeze"}:
        return None, ()

    model_metadata_object_key = latest_model_metadata_key(artifact_store)
    if model_metadata_object_key is None:
        return None, ()

    persisted_dataset = persist_scada_replay_inference_dataset(
        artifact_store=artifact_store,
        current_round_id=current_round_id,
        replay_stage=replay_stage,
        sequence_length=sequence_length,
    )
    inference_results = run_lstm_fingerprint_inference_from_persisted_dataset(
        model_metadata_object_key=model_metadata_object_key,
        inference_manifest_object_key=persisted_dataset.manifest_object_key,
        artifact_store=artifact_store,
        threshold_stddev_multiplier=threshold_stddev_multiplier,
    )
    if not inference_results:
        return None, ()

    first_result = inference_results[0]
    replay_result = ReplayBehaviorResult(
        output_channel=REPLAY_OUTPUT_CHANNEL,
        scenario_mode=replay_stage.mode,
        current_round_id=current_round_id,
        scada_source_round_id=scada_state.source_round_id,
        replay_source_round_id=replay_stage.replay_source_round_id,
        model_id=first_result.model_id,
        source_dataset_id=first_result.source_dataset_id,
        inference_dataset_id=first_result.inference_dataset_id,
        source_dataset_validation_level=first_result.source_dataset_validation_level,
        limitation_note=first_result.limitation_note,
        window_id=first_result.window_id,
        artifact_keys=first_result.artifact_keys,
        anomaly_score=first_result.anomaly_score,
        classification_threshold=first_result.classification_threshold,
        classification=first_result.classification,
        scada_divergent_sensors=tuple(comparison_output.divergent_sensors),
        consensus_final_status=consensus_final_status,
    )
    return replay_result, inference_results


def persist_scada_replay_inference_dataset(
    *,
    artifact_store,
    current_round_id: str,
    replay_stage: ScadaReplayRuntimeStage,
    sequence_length: int,
):
    """Persist one replay-oriented inference dataset derived from valid artifacts."""

    if sequence_length <= 0:
        raise ValueError("sequence_length must be positive for replay detection.")

    object_keys = artifact_store.list_json_objects(prefix=VALID_ARTIFACT_PREFIX)
    artifacts = [artifact_store.load_json(object_key) for object_key in object_keys]
    artifact_by_round_id = {
        artifact["round_identity"]["round_id"]: artifact for artifact in artifacts
    }
    if current_round_id not in artifact_by_round_id:
        raise ValueError("Current round artifact is not available for replay detection.")

    current_index = next(
        index
        for index, artifact in enumerate(artifacts)
        if artifact["round_identity"]["round_id"] == current_round_id
    )
    if current_index < sequence_length - 1:
        raise ValueError("Not enough valid history to build replay inference dataset.")

    chronological_history = artifacts[: current_index + 1]
    recent_real_artifacts = chronological_history[-sequence_length:-1]
    replay_artifact = _resolve_replay_source_artifact(
        chronological_history=chronological_history,
        replay_stage=replay_stage,
    )
    selected_artifacts = recent_real_artifacts + [replay_artifact]

    feature_schema = ()
    feature_matrix = []
    artifact_keys = []
    round_ids = []
    timestamps = []
    for artifact in selected_artifacts:
        current_schema, feature_vector = extract_feature_vector(artifact)
        if not feature_schema:
            feature_schema = current_schema
        elif current_schema != feature_schema:
            raise ValueError("Replay inference dataset feature schema mismatch.")
        feature_matrix.append(feature_vector)
        artifact_keys.append(artifact["artifact_key"])
        round_ids.append(artifact["round_identity"]["round_id"])
        timestamps.append(artifact["round_identity"]["window_ended_at"])

    replay_round_id = replay_stage.replay_source_round_id or replay_artifact["round_identity"][
        "round_id"
    ]
    dataset_id = (
        f"replay-dataset::{current_round_id}::{replay_stage.mode}::{replay_round_id}"
        f"::seq-{sequence_length}"
    )
    replay_window = TrainingWindow(
        window_id=f"replay-window::{current_round_id}::{replay_round_id}",
        artifact_keys=tuple(artifact_keys),
        round_ids=tuple(round_ids),
        timestamps=tuple(timestamps),
        feature_schema=feature_schema,
        feature_matrix=tuple(feature_matrix),
        label=replay_stage.mode,
    )
    manifest = TrainingDatasetManifest(
        dataset_id=dataset_id,
        source_bucket=artifact_store.config.bucket,
        source_prefix=VALID_ARTIFACT_PREFIX,
        sequence_length=sequence_length,
        feature_schema=feature_schema,
        selected_artifact_keys=tuple(artifact_keys),
        skipped_artifacts={},
        eligible_record_count=len(artifact_keys),
        window_count=1,
        training_label=f"{replay_stage.mode}_evaluation",
    )
    return persist_training_dataset_artifacts(
        training_windows=(replay_window,),
        dataset_manifest=manifest,
        artifact_store=artifact_store,
    )


def _resolve_replay_source_artifact(
    *,
    chronological_history: list[dict[str, object]],
    replay_stage: ScadaReplayRuntimeStage,
) -> dict[str, object]:
    if replay_stage.mode == "freeze":
        if len(chronological_history) < 2:
            raise ValueError("Freeze detection requires at least one previous round.")
        return chronological_history[-2]

    if replay_stage.replay_source_round_id is not None:
        for artifact in chronological_history:
            if artifact["round_identity"]["round_id"] == replay_stage.replay_source_round_id:
                return artifact

    return chronological_history[0]


def _resolve_scada_offset(sensor_name: str, config) -> float:
    """Return a simple demo-safe SCADA offset for divergence scenarios."""

    base_offset = float(getattr(config, "demo_scada_offset_value", 6.0))
    if sensor_name == "temperature":
        return round(base_offset, 3)
    if sensor_name == "pressure":
        return round(base_offset / 10.0, 3)
    return round(base_offset * 50.0, 3)
