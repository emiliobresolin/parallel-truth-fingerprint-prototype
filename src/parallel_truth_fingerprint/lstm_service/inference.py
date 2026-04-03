"""Inference helpers for Epic 4 Story 4.3."""

from __future__ import annotations

from pathlib import Path

from parallel_truth_fingerprint.contracts.fingerprint_inference import (
    FingerprintInferenceClassification,
    FingerprintInferenceResult,
)
from parallel_truth_fingerprint.lstm_service.dataset_artifacts import (
    DATASET_PREFIX,
    load_persisted_training_dataset_artifacts,
)
from parallel_truth_fingerprint.lstm_service.trainer import _load_keras_module


INFERENCE_OUTPUT_CHANNEL = "lstm_fingerprint"
DEFAULT_THRESHOLD_STDDEV_MULTIPLIER = 3.0
DEFAULT_MINIMUM_ANOMALY_THRESHOLD = 1e-6
RUNTIME_VALID_LIMITATION_NOTE = (
    "The fingerprint pipeline is running correctly on a runtime-valid but not yet "
    "meaningfully fingerprint-valid dataset because the current normal-history data "
    "still falls below the approved adequacy floor of 30 eligible artifacts and "
    "20 generated windows."
)
INFERENCE_SCRATCH_ROOT = (
    Path(__file__).resolve().parents[3] / ".tmp" / "lstm_service_inference"
)


def run_lstm_fingerprint_inference_from_persisted_dataset(
    *,
    model_metadata_object_key: str,
    inference_manifest_object_key: str,
    artifact_store,
    inference_windows_object_key: str | None = None,
    threshold_stddev_multiplier: float = DEFAULT_THRESHOLD_STDDEV_MULTIPLIER,
    minimum_threshold: float = DEFAULT_MINIMUM_ANOMALY_THRESHOLD,
) -> tuple[FingerprintInferenceResult, ...]:
    """Run Story 4.3 inference only from persisted dataset artifacts."""

    model_metadata = artifact_store.load_json(model_metadata_object_key)
    source_manifest_object_key = (
        f"{DATASET_PREFIX}{model_metadata['source_dataset_id']}.manifest.json"
    )
    source_manifest_payload = artifact_store.load_json(source_manifest_object_key)
    source_windows, source_manifest = load_persisted_training_dataset_artifacts(
        manifest_object_key=source_manifest_object_key,
        artifact_store=artifact_store,
    )
    inference_windows, inference_manifest = load_persisted_training_dataset_artifacts(
        manifest_object_key=inference_manifest_object_key,
        windows_object_key=inference_windows_object_key,
        artifact_store=artifact_store,
    )
    _validate_model_compatibility(
        model_metadata=model_metadata,
        source_manifest_payload=source_manifest_payload,
        inference_manifest=inference_manifest,
    )
    model = _load_saved_keras_model(
        model_object_key=model_metadata["model_object_key"],
        artifact_store=artifact_store,
        model_id=model_metadata["model_id"],
    )
    baseline_errors = _compute_window_reconstruction_errors(model, source_windows)
    threshold_value = _derive_anomaly_threshold(
        baseline_errors=baseline_errors,
        minimum_threshold=minimum_threshold,
        threshold_stddev_multiplier=threshold_stddev_multiplier,
    )
    source_validation_level = source_manifest_payload["adequacy_assessment"][
        "validation_level"
    ]
    limitation_note = (
        None
        if source_validation_level == "meaningful_fingerprint_valid"
        else RUNTIME_VALID_LIMITATION_NOTE
    )
    inference_errors = _compute_window_reconstruction_errors(model, inference_windows)
    threshold_origin = (
        f"source_dataset_mean_plus_{threshold_stddev_multiplier:g}std"
    )
    return tuple(
        FingerprintInferenceResult(
            output_channel=INFERENCE_OUTPUT_CHANNEL,
            model_id=str(model_metadata["model_id"]),
            source_dataset_id=str(model_metadata["source_dataset_id"]),
            inference_dataset_id=inference_manifest.dataset_id,
            source_dataset_validation_level=source_validation_level,
            limitation_note=limitation_note,
            window_id=window.window_id,
            artifact_keys=window.artifact_keys,
            round_ids=window.round_ids,
            timestamps=window.timestamps,
            anomaly_score=float(inference_errors[index]),
            classification_threshold=threshold_value,
            threshold_origin=threshold_origin,
            classification=(
                FingerprintInferenceClassification.NORMAL
                if float(inference_errors[index]) <= threshold_value
                else FingerprintInferenceClassification.ANOMALOUS
            ),
        )
        for index, window in enumerate(inference_windows)
    )


def _validate_model_compatibility(
    *,
    model_metadata: dict[str, object],
    source_manifest_payload: dict[str, object],
    inference_manifest,
) -> None:
    expected_feature_schema = tuple(model_metadata["feature_schema"])
    expected_sequence_length = int(model_metadata["sequence_length"])

    if tuple(source_manifest_payload["feature_schema"]) != expected_feature_schema:
        raise ValueError(
            "The saved model feature schema does not match its source dataset artifact."
        )
    if int(source_manifest_payload["sequence_length"]) != expected_sequence_length:
        raise ValueError(
            "The saved model sequence length does not match its source dataset artifact."
        )
    if inference_manifest.feature_schema != expected_feature_schema:
        raise ValueError(
            "The persisted inference dataset feature schema does not match the saved model."
        )
    if inference_manifest.sequence_length != expected_sequence_length:
        raise ValueError(
            "The persisted inference dataset sequence length does not match the saved model."
        )


def _load_saved_keras_model(*, model_object_key: str, artifact_store, model_id: str):
    keras = _load_keras_module()
    model_bytes = artifact_store.load_bytes(model_object_key)
    INFERENCE_SCRATCH_ROOT.mkdir(parents=True, exist_ok=True)
    archive_path = INFERENCE_SCRATCH_ROOT / f"{model_id}.keras"
    archive_path.write_bytes(model_bytes)
    try:
        return keras.saving.load_model(str(archive_path), compile=False)
    finally:
        archive_path.unlink(missing_ok=True)


def _compute_window_reconstruction_errors(model, training_windows) -> tuple[float, ...]:
    numpy = __import__("numpy")
    if not training_windows:
        raise ValueError("At least one valid temporal window is required for inference.")

    feature_tensor = numpy.asarray(
        [window.feature_matrix for window in training_windows],
        dtype="float32",
    )
    reconstructed_tensor = model.predict(feature_tensor, verbose=0)
    squared_error = numpy.square(reconstructed_tensor - feature_tensor)
    window_errors = numpy.mean(squared_error, axis=(1, 2))
    return tuple(float(value) for value in window_errors.tolist())


def _derive_anomaly_threshold(
    *,
    baseline_errors: tuple[float, ...],
    minimum_threshold: float,
    threshold_stddev_multiplier: float,
) -> float:
    numpy = __import__("numpy")
    mean_error = float(numpy.mean(baseline_errors))
    std_error = float(numpy.std(baseline_errors))
    return max(
        mean_error + (threshold_stddev_multiplier * std_error),
        minimum_threshold,
    )
