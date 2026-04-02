"""Dataset artifact persistence helpers for Epic 4 Story 4.2A."""

from __future__ import annotations

from datetime import datetime, timezone
import importlib.util
import io

from parallel_truth_fingerprint.contracts.dataset_artifact import (
    DatasetAdequacyAssessment,
    PersistedTrainingDatasetArtifact,
)
from parallel_truth_fingerprint.contracts.training_dataset import (
    TrainingDatasetManifest,
    TrainingWindow,
)


DATASET_PREFIX = "fingerprint-datasets/"
DEFAULT_WINDOW_STRIDE = 1
DEFAULT_ORDERING_RULE = "round_identity.window_ended_at_then_artifact_key"
DEFAULT_MIN_ELIGIBLE_ARTIFACT_COUNT = 30
DEFAULT_MIN_WINDOW_COUNT = 20


def evaluate_training_dataset_adequacy(
    *,
    eligible_artifact_count: int,
    window_count: int,
    minimum_eligible_artifact_count: int = DEFAULT_MIN_ELIGIBLE_ARTIFACT_COUNT,
    minimum_window_count: int = DEFAULT_MIN_WINDOW_COUNT,
) -> DatasetAdequacyAssessment:
    """Classify whether one dataset is runtime-valid only or meaningfully adequate."""

    eligible_artifact_floor_met = (
        eligible_artifact_count >= minimum_eligible_artifact_count
    )
    window_floor_met = window_count >= minimum_window_count
    adequacy_met = eligible_artifact_floor_met and window_floor_met

    if adequacy_met:
        validation_level = "meaningful_fingerprint_valid"
        status_reason = "adequacy_floor_met"
    else:
        validation_level = "runtime_valid_only"
        status_reason = "below_default_adequacy_floor"

    return DatasetAdequacyAssessment(
        validation_level=validation_level,
        adequacy_met=adequacy_met,
        status_reason=status_reason,
        minimum_eligible_artifact_count=minimum_eligible_artifact_count,
        minimum_window_count=minimum_window_count,
        eligible_artifact_count=eligible_artifact_count,
        window_count=window_count,
        eligible_artifact_floor_met=eligible_artifact_floor_met,
        window_floor_met=window_floor_met,
    )


def persist_training_dataset_artifacts(
    *,
    training_windows,
    dataset_manifest,
    artifact_store,
    created_at: datetime | None = None,
    dataset_prefix: str = DATASET_PREFIX,
    minimum_eligible_artifact_count: int = DEFAULT_MIN_ELIGIBLE_ARTIFACT_COUNT,
    minimum_window_count: int = DEFAULT_MIN_WINDOW_COUNT,
) -> PersistedTrainingDatasetArtifact:
    """Persist one inspectable dataset manifest and windows archive to MinIO."""

    if created_at is None:
        created_at = datetime.now(timezone.utc)

    manifest_object_key = (
        f"{dataset_prefix}{dataset_manifest.dataset_id}.manifest.json"
    )
    windows_object_key = f"{dataset_prefix}{dataset_manifest.dataset_id}.windows.npz"
    adequacy = evaluate_training_dataset_adequacy(
        eligible_artifact_count=dataset_manifest.eligible_record_count,
        window_count=dataset_manifest.window_count,
        minimum_eligible_artifact_count=minimum_eligible_artifact_count,
        minimum_window_count=minimum_window_count,
    )
    tensor_shape = (
        len(training_windows),
        dataset_manifest.sequence_length,
        len(dataset_manifest.feature_schema),
    )
    overlap_behavior = (
        "sliding_stride_1"
        if dataset_manifest.sequence_length > DEFAULT_WINDOW_STRIDE
        else "non_overlapping"
    )

    persisted_artifact = PersistedTrainingDatasetArtifact(
        dataset_id=dataset_manifest.dataset_id,
        created_at=created_at.isoformat(),
        source_bucket=dataset_manifest.source_bucket,
        source_prefix=dataset_manifest.source_prefix,
        manifest_object_key=manifest_object_key,
        windows_object_key=windows_object_key,
        chronological_ordering_rule=DEFAULT_ORDERING_RULE,
        sequence_length=dataset_manifest.sequence_length,
        stride=DEFAULT_WINDOW_STRIDE,
        overlap_behavior=overlap_behavior,
        feature_schema=dataset_manifest.feature_schema,
        selected_artifact_keys=dataset_manifest.selected_artifact_keys,
        skipped_artifacts=dataset_manifest.skipped_artifacts,
        eligible_artifact_count=dataset_manifest.eligible_record_count,
        window_count=dataset_manifest.window_count,
        tensor_shape=tensor_shape,
        training_label=dataset_manifest.training_label,
        adequacy_assessment=adequacy,
    )

    artifact_store.save_json(manifest_object_key, persisted_artifact.to_dict())
    artifact_store.save_bytes(
        windows_object_key,
        _serialize_training_windows_npz(
            training_windows,
            sequence_length=dataset_manifest.sequence_length,
            feature_count=len(dataset_manifest.feature_schema),
        ),
        content_type="application/octet-stream",
    )
    return persisted_artifact


def load_persisted_training_dataset_artifacts(
    *,
    manifest_object_key: str,
    artifact_store,
    windows_object_key: str | None = None,
) -> tuple[tuple[TrainingWindow, ...], TrainingDatasetManifest]:
    """Load one persisted Story 4.2A dataset artifact back into training objects."""

    numpy = _load_numpy()
    manifest_payload = artifact_store.load_json(manifest_object_key)
    resolved_windows_object_key = (
        windows_object_key or manifest_payload["windows_object_key"]
    )
    windows_payload = artifact_store.load_bytes(resolved_windows_object_key)
    windows_archive = numpy.load(io.BytesIO(windows_payload))

    feature_schema = tuple(manifest_payload["feature_schema"])
    feature_tensor = windows_archive["feature_tensor"]
    if feature_tensor.ndim != 3:
        raise ValueError("Persisted training dataset tensor must be rank-3.")
    if feature_tensor.shape[2] != len(feature_schema):
        raise ValueError(
            "Persisted training dataset tensor does not match the declared feature schema."
        )

    window_ids = windows_archive["window_ids"].tolist()
    artifact_key_rows = windows_archive["artifact_keys"].tolist()
    round_id_rows = windows_archive["round_ids"].tolist()
    timestamp_rows = windows_archive["timestamps"].tolist()
    labels = windows_archive["labels"].tolist()

    training_windows = tuple(
        TrainingWindow(
            window_id=str(window_ids[index]),
            artifact_keys=tuple(str(value) for value in artifact_key_rows[index]),
            round_ids=tuple(str(value) for value in round_id_rows[index]),
            timestamps=tuple(str(value) for value in timestamp_rows[index]),
            feature_schema=feature_schema,
            feature_matrix=tuple(
                tuple(float(value) for value in row)
                for row in feature_tensor[index].tolist()
            ),
            label=str(labels[index]),
        )
        for index in range(len(window_ids))
    )

    dataset_manifest = TrainingDatasetManifest(
        dataset_id=str(manifest_payload["dataset_id"]),
        source_bucket=str(manifest_payload["source_bucket"]),
        source_prefix=str(manifest_payload["source_prefix"]),
        sequence_length=int(manifest_payload["sequence_length"]),
        feature_schema=feature_schema,
        selected_artifact_keys=tuple(manifest_payload["selected_artifact_keys"]),
        skipped_artifacts=dict(manifest_payload["skipped_artifacts"]),
        eligible_record_count=int(manifest_payload["eligible_artifact_count"]),
        window_count=int(manifest_payload["window_count"]),
        training_label=str(manifest_payload["training_label"]),
    )
    return training_windows, dataset_manifest


def _serialize_training_windows_npz(
    training_windows,
    *,
    sequence_length: int,
    feature_count: int,
) -> bytes:
    numpy = _load_numpy()
    if training_windows:
        sequence_length = len(training_windows[0].artifact_keys)
        feature_count = len(training_windows[0].feature_schema)

    if training_windows:
        feature_tensor = numpy.asarray(
            [window.feature_matrix for window in training_windows],
            dtype="float32",
        )
    else:
        feature_tensor = numpy.zeros((0, sequence_length, feature_count), dtype="float32")
    window_ids = numpy.asarray([window.window_id for window in training_windows], dtype=str)
    labels = numpy.asarray([window.label for window in training_windows], dtype=str)

    artifact_keys = numpy.asarray(
        [window.artifact_keys for window in training_windows],
        dtype=str,
    ).reshape(len(training_windows), sequence_length)
    round_ids = numpy.asarray(
        [window.round_ids for window in training_windows],
        dtype=str,
    ).reshape(len(training_windows), sequence_length)
    timestamps = numpy.asarray(
        [window.timestamps for window in training_windows],
        dtype=str,
    ).reshape(len(training_windows), sequence_length)

    payload = io.BytesIO()
    numpy.savez_compressed(
        payload,
        feature_tensor=feature_tensor,
        window_ids=window_ids,
        artifact_keys=artifact_keys,
        round_ids=round_ids,
        timestamps=timestamps,
        labels=labels,
    )
    return payload.getvalue()


def _load_numpy():
    if importlib.util.find_spec("numpy") is None:
        raise RuntimeError(
            "Story 4.2A dataset artifact persistence requires the 'numpy' package."
        )
    return __import__("numpy")
