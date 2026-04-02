"""Deferred fingerprint lifecycle helpers for Epic 4 Story 4.3A."""

from __future__ import annotations

from dataclasses import dataclass

from parallel_truth_fingerprint.lstm_service.dataset_artifacts import (
    DATASET_PREFIX,
    persist_training_dataset_artifacts,
)
from parallel_truth_fingerprint.lstm_service.dataset_builder import (
    build_normal_training_windows,
)
from parallel_truth_fingerprint.lstm_service.inference import (
    run_lstm_fingerprint_inference_from_persisted_dataset,
)
from parallel_truth_fingerprint.lstm_service.inference import RUNTIME_VALID_LIMITATION_NOTE
from parallel_truth_fingerprint.lstm_service.trainer import (
    train_and_save_lstm_fingerprint_from_persisted_dataset,
)


VALID_ARTIFACT_PREFIX = "valid-consensus-artifacts/"
MODEL_METADATA_PREFIX = "fingerprint-models/"
DEFAULT_RUNTIME_SEQUENCE_LENGTH = 2
DEFAULT_TRAIN_AFTER_ELIGIBLE_CYCLES = 10


@dataclass(frozen=True)
class FingerprintLifecycleStage:
    """Inspectable per-cycle fingerprint lifecycle state."""

    cycle_index: int
    valid_artifact_count: int
    eligible_history_count: int
    eligible_history_threshold: int
    window_count: int
    latest_valid_artifact_key: str | None
    model_status: str
    training_events: tuple[str, ...]
    inference_status: str
    inference_result_count: int
    dataset_manifest_object_key: str | None = None
    model_metadata_object_key: str | None = None
    source_dataset_validation_level: str | None = None
    limitation_note: str | None = None

    def to_dict(self) -> dict[str, object]:
        return {
            "cycle_index": self.cycle_index,
            "valid_artifact_count": self.valid_artifact_count,
            "eligible_history_count": self.eligible_history_count,
            "eligible_history_threshold": self.eligible_history_threshold,
            "window_count": self.window_count,
            "latest_valid_artifact_key": self.latest_valid_artifact_key,
            "model_status": self.model_status,
            "training_events": list(self.training_events),
            "inference_status": self.inference_status,
            "inference_result_count": self.inference_result_count,
            "dataset_manifest_object_key": self.dataset_manifest_object_key,
            "model_metadata_object_key": self.model_metadata_object_key,
            "source_dataset_validation_level": self.source_dataset_validation_level,
            "limitation_note": self.limitation_note,
        }


def execute_deferred_fingerprint_lifecycle(
    *,
    cycle_index: int,
    artifact_store,
    sequence_length: int = DEFAULT_RUNTIME_SEQUENCE_LENGTH,
    train_after_eligible_cycles: int = DEFAULT_TRAIN_AFTER_ELIGIBLE_CYCLES,
) -> tuple[FingerprintLifecycleStage, tuple]:
    """Run the Story 4.3A deferred lifecycle for one completed valid-artifact cycle."""

    valid_artifact_keys = artifact_store.list_json_objects(prefix=VALID_ARTIFACT_PREFIX)
    latest_valid_artifact_key = valid_artifact_keys[-1] if valid_artifact_keys else None
    training_windows, dataset_manifest = build_normal_training_windows(
        artifact_store=artifact_store,
        sequence_length=sequence_length,
        prefix=VALID_ARTIFACT_PREFIX,
    )
    eligible_history_count = dataset_manifest.eligible_record_count
    latest_model_metadata_object_key = latest_model_metadata_key(artifact_store)
    window_count = dataset_manifest.window_count

    if latest_model_metadata_object_key is None:
        if eligible_history_count < train_after_eligible_cycles or window_count == 0:
            return (
                FingerprintLifecycleStage(
                    cycle_index=cycle_index,
                    valid_artifact_count=len(valid_artifact_keys),
                    eligible_history_count=eligible_history_count,
                    eligible_history_threshold=train_after_eligible_cycles,
                    window_count=window_count,
                    latest_valid_artifact_key=latest_valid_artifact_key,
                    model_status="no_model_yet",
                    training_events=("deferred",),
                    inference_status="skipped_no_model",
                    inference_result_count=0,
                    limitation_note=RUNTIME_VALID_LIMITATION_NOTE,
                ),
                (),
            )

        persisted_dataset = persist_training_dataset_artifacts(
            training_windows=training_windows,
            dataset_manifest=dataset_manifest,
            artifact_store=artifact_store,
        )
        model_metadata = train_and_save_lstm_fingerprint_from_persisted_dataset(
            manifest_object_key=persisted_dataset.manifest_object_key,
            artifact_store=artifact_store,
            epochs=1,
            batch_size=1,
            latent_units=4,
        )
        limitation_note = (
            None
            if persisted_dataset.adequacy_assessment.validation_level
            == "meaningful_fingerprint_valid"
            else RUNTIME_VALID_LIMITATION_NOTE
        )
        return (
            FingerprintLifecycleStage(
                cycle_index=cycle_index,
                valid_artifact_count=len(valid_artifact_keys),
                eligible_history_count=eligible_history_count,
                eligible_history_threshold=train_after_eligible_cycles,
                window_count=window_count,
                latest_valid_artifact_key=latest_valid_artifact_key,
                model_status="model_available",
                training_events=("started", "completed"),
                inference_status="skipped_until_next_cycle",
                inference_result_count=0,
                dataset_manifest_object_key=persisted_dataset.manifest_object_key,
                model_metadata_object_key=model_metadata.metadata_object_key,
                source_dataset_validation_level=(
                    persisted_dataset.adequacy_assessment.validation_level
                ),
                limitation_note=limitation_note,
            ),
            (),
        )

    persisted_dataset = persist_training_dataset_artifacts(
        training_windows=training_windows,
        dataset_manifest=dataset_manifest,
        artifact_store=artifact_store,
    )
    if window_count == 0:
        return (
            FingerprintLifecycleStage(
                cycle_index=cycle_index,
                valid_artifact_count=len(valid_artifact_keys),
                eligible_history_count=eligible_history_count,
                eligible_history_threshold=train_after_eligible_cycles,
                window_count=window_count,
                latest_valid_artifact_key=latest_valid_artifact_key,
                model_status="model_available",
                training_events=("reused",),
                inference_status="skipped_no_windows",
                inference_result_count=0,
                dataset_manifest_object_key=persisted_dataset.manifest_object_key,
                model_metadata_object_key=latest_model_metadata_object_key,
                source_dataset_validation_level=(
                    persisted_dataset.adequacy_assessment.validation_level
                ),
                limitation_note=(
                    None
                    if persisted_dataset.adequacy_assessment.validation_level
                    == "meaningful_fingerprint_valid"
                    else RUNTIME_VALID_LIMITATION_NOTE
                ),
            ),
            (),
        )

    inference_results = run_lstm_fingerprint_inference_from_persisted_dataset(
        model_metadata_object_key=latest_model_metadata_object_key,
        inference_manifest_object_key=persisted_dataset.manifest_object_key,
        artifact_store=artifact_store,
    )
    first_result = inference_results[0] if inference_results else None
    return (
        FingerprintLifecycleStage(
            cycle_index=cycle_index,
            valid_artifact_count=len(valid_artifact_keys),
            eligible_history_count=eligible_history_count,
            eligible_history_threshold=train_after_eligible_cycles,
            window_count=window_count,
            latest_valid_artifact_key=latest_valid_artifact_key,
            model_status="model_available",
            training_events=("reused",),
            inference_status="completed",
            inference_result_count=len(inference_results),
            dataset_manifest_object_key=persisted_dataset.manifest_object_key,
            model_metadata_object_key=latest_model_metadata_object_key,
            source_dataset_validation_level=None
            if first_result is None
            else first_result.source_dataset_validation_level,
            limitation_note=None if first_result is None else first_result.limitation_note,
        ),
        inference_results,
    )


def latest_model_metadata_key(artifact_store) -> str | None:
    """Return the latest saved fingerprint-model metadata key, if any."""

    model_keys = artifact_store.list_json_objects(prefix=MODEL_METADATA_PREFIX)
    if not model_keys:
        return None
    return model_keys[-1]
