"""Dataset-building helpers for Epic 4 Story 4.1."""

from __future__ import annotations

from dataclasses import dataclass
from datetime import datetime

from parallel_truth_fingerprint.contracts.training_dataset import (
    TrainingDatasetManifest,
    TrainingWindow,
)


@dataclass(frozen=True)
class _EligibleArtifact:
    artifact_key: str
    round_id: str
    timestamp: str
    feature_vector: tuple[float, ...]


def build_normal_training_windows(
    *,
    artifact_store,
    sequence_length: int,
    prefix: str = "valid-consensus-artifacts/",
) -> tuple[tuple[TrainingWindow, ...], TrainingDatasetManifest]:
    """Build deterministic fixed-length normal windows from MinIO artifacts."""

    if sequence_length <= 0:
        raise ValueError("sequence_length must be a positive integer.")

    object_keys = artifact_store.list_json_objects(prefix=prefix)
    eligible_records: list[_EligibleArtifact] = []
    skipped_artifacts: dict[str, str] = {}
    feature_schema: tuple[str, ...] = ()

    for object_key in object_keys:
        artifact = artifact_store.load_json(object_key)
        eligible, reason = evaluate_training_eligibility(artifact)
        if not eligible:
            skipped_artifacts[object_key] = reason
            continue

        current_schema, feature_vector = extract_feature_vector(artifact)
        if not feature_schema:
            feature_schema = current_schema
        elif current_schema != feature_schema:
            skipped_artifacts[object_key] = "feature_schema_mismatch"
            continue

        round_identity = artifact["round_identity"]
        eligible_records.append(
            _EligibleArtifact(
                artifact_key=object_key,
                round_id=round_identity["round_id"],
                timestamp=round_identity["window_ended_at"],
                feature_vector=feature_vector,
            )
        )

    eligible_records.sort(key=lambda record: (record.timestamp, record.artifact_key))
    windows = _build_windows(
        eligible_records=eligible_records,
        feature_schema=feature_schema,
        sequence_length=sequence_length,
    )
    manifest = TrainingDatasetManifest(
        dataset_id=_build_dataset_id(eligible_records, sequence_length),
        source_bucket=artifact_store.config.bucket,
        source_prefix=prefix,
        sequence_length=sequence_length,
        feature_schema=feature_schema,
        selected_artifact_keys=tuple(record.artifact_key for record in eligible_records),
        skipped_artifacts=skipped_artifacts,
        eligible_record_count=len(eligible_records),
        window_count=len(windows),
    )
    return windows, manifest


def evaluate_training_eligibility(artifact: dict[str, object]) -> tuple[bool, str]:
    """Return whether one persisted artifact is eligible for normal training."""

    consensus_context = artifact.get("consensus_context", {})
    if consensus_context.get("final_consensus_status") != "success":
        return False, "consensus_not_success"

    dataset_context = artifact.get("dataset_context")
    if not isinstance(dataset_context, dict):
        return False, "missing_dataset_context"
    if dataset_context.get("training_label") != "normal":
        return False, "training_label_not_normal"
    if not dataset_context.get("training_eligible", False):
        reason = dataset_context.get("training_eligibility_reason", "training_ineligible")
        return False, str(reason)

    diagnostics = artifact.get("diagnostics", {})
    if diagnostics.get("has_scada_divergence", False):
        return False, "scada_divergence"

    return True, "normal_eligible"


def extract_feature_vector(
    artifact: dict[str, object],
) -> tuple[tuple[str, ...], tuple[float, ...]]:
    """Extract one deterministic physical-operational feature vector."""

    payload_snapshot = artifact["validated_state"]["structured_payload_snapshot"]
    payloads_by_sensor = payload_snapshot["payloads_by_sensor"]

    feature_schema: list[str] = []
    feature_values: list[float] = []
    for sensor_name in sorted(payloads_by_sensor):
        payload = payloads_by_sensor[sensor_name]
        process_data = payload["process_data"]
        physics_metrics = process_data["physics_metrics"]
        diagnostics = payload["diagnostics"]

        feature_schema.extend(
            [
                f"{sensor_name}.pv",
                f"{sensor_name}.loop_current_ma",
                f"{sensor_name}.pv_percent_range",
                f"{sensor_name}.noise_floor",
                f"{sensor_name}.rate_of_change_dtdt",
                f"{sensor_name}.local_stability_score",
                f"{sensor_name}.field_device_malfunction",
                f"{sensor_name}.loop_current_saturated",
                f"{sensor_name}.cold_start",
            ]
        )
        feature_values.extend(
            [
                float(process_data["pv"]["value"]),
                float(process_data["loop_current_ma"]),
                float(process_data["pv_percent_range"]),
                float(physics_metrics["noise_floor"]),
                float(physics_metrics["rate_of_change_dtdt"]),
                float(physics_metrics["local_stability_score"]),
                _bool_to_float(diagnostics["field_device_malfunction"]),
                _bool_to_float(diagnostics["loop_current_saturated"]),
                _bool_to_float(diagnostics["cold_start"]),
            ]
        )

    return tuple(feature_schema), tuple(feature_values)


def _build_windows(
    *,
    eligible_records: list[_EligibleArtifact],
    feature_schema: tuple[str, ...],
    sequence_length: int,
) -> tuple[TrainingWindow, ...]:
    windows: list[TrainingWindow] = []
    if len(eligible_records) < sequence_length:
        return ()

    for start_index in range(len(eligible_records) - sequence_length + 1):
        chunk = eligible_records[start_index : start_index + sequence_length]
        windows.append(
            TrainingWindow(
                window_id=(
                    f"window::{chunk[0].round_id}::{chunk[-1].round_id}"
                ),
                artifact_keys=tuple(record.artifact_key for record in chunk),
                round_ids=tuple(record.round_id for record in chunk),
                timestamps=tuple(record.timestamp for record in chunk),
                feature_schema=feature_schema,
                feature_matrix=tuple(record.feature_vector for record in chunk),
            )
        )
    return tuple(windows)


def _build_dataset_id(
    eligible_records: list[_EligibleArtifact],
    sequence_length: int,
) -> str:
    if not eligible_records:
        return f"training-dataset::empty::seq-{sequence_length}"
    return (
        "training-dataset::"
        f"{eligible_records[0].round_id}::"
        f"{eligible_records[-1].round_id}::"
        f"seq-{sequence_length}"
    )


def _bool_to_float(value: bool) -> float:
    return 1.0 if value else 0.0
