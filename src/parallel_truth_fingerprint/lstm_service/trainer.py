"""Training helpers for Epic 4 Story 4.2."""

from __future__ import annotations

from datetime import datetime, timezone
import io
import importlib
import importlib.util
import os
from pathlib import Path
import zipfile

from parallel_truth_fingerprint.contracts.fingerprint_model import (
    FingerprintModelArtifact,
)
from parallel_truth_fingerprint.lstm_service.dataset_artifacts import (
    load_persisted_training_dataset_artifacts,
)


DEFAULT_MODEL_PREFIX = "fingerprint-models/"
EXPORT_SCRATCH_ROOT = Path(__file__).resolve().parents[3] / ".tmp" / "lstm_service_export"


def train_and_save_lstm_fingerprint(
    *,
    training_windows,
    dataset_manifest,
    artifact_store,
    epochs: int = 12,
    batch_size: int = 8,
    latent_units: int = 16,
    model_prefix: str = DEFAULT_MODEL_PREFIX,
) -> FingerprintModelArtifact:
    """Train a local LSTM autoencoder and persist the model plus metadata."""

    if not training_windows:
        raise ValueError("At least one training window is required for LSTM training.")

    feature_schema = training_windows[0].feature_schema
    sequence_length = len(training_windows[0].feature_matrix)
    feature_count = len(feature_schema)
    for window in training_windows:
        if window.feature_schema != feature_schema:
            raise ValueError("All training windows must share the same feature schema.")
        if len(window.feature_matrix) != sequence_length:
            raise ValueError("All training windows must share the same sequence length.")
        for row in window.feature_matrix:
            if len(row) != feature_count:
                raise ValueError("All feature rows must match the declared feature schema.")

    keras = _load_keras_module()
    numpy = importlib.import_module("numpy")
    training_tensor = numpy.asarray(
        [
            [list(row) for row in window.feature_matrix]
            for window in training_windows
        ],
        dtype="float32",
    )
    model = build_lstm_autoencoder(
        keras=keras,
        sequence_length=sequence_length,
        feature_count=feature_count,
        latent_units=latent_units,
    )
    history = model.fit(
        training_tensor,
        training_tensor,
        epochs=epochs,
        batch_size=batch_size,
        verbose=0,
    )

    created_at = datetime.now(timezone.utc).isoformat()
    model_id = _build_model_id(dataset_manifest.dataset_id, created_at)
    model_object_key = f"{model_prefix}{model_id}.keras"
    metadata_object_key = f"{model_prefix}{model_id}.json"

    artifact_store.save_bytes(
        model_object_key,
        _export_model_bytes(model, model_id),
        content_type="application/vnd.keras",
    )

    metadata = FingerprintModelArtifact(
        model_id=model_id,
        created_at=created_at,
        backend="torch",
        model_format="keras",
        model_type="lstm_autoencoder",
        source_dataset_id=dataset_manifest.dataset_id,
        feature_schema=feature_schema,
        sequence_length=sequence_length,
        training_window_count=len(training_windows),
        epochs=epochs,
        batch_size=batch_size,
        loss_name="mse",
        bucket=artifact_store.config.bucket,
        model_object_key=model_object_key,
        metadata_object_key=metadata_object_key,
        artifact_uri=f"minio://{artifact_store.config.bucket}/{model_object_key}",
        metadata_uri=f"minio://{artifact_store.config.bucket}/{metadata_object_key}",
        final_training_loss=_extract_final_loss(history),
    )
    artifact_store.save_json(metadata_object_key, metadata.to_dict())
    return metadata


def train_and_save_lstm_fingerprint_from_persisted_dataset(
    *,
    manifest_object_key: str,
    artifact_store,
    windows_object_key: str | None = None,
    epochs: int = 12,
    batch_size: int = 8,
    latent_units: int = 16,
    model_prefix: str = DEFAULT_MODEL_PREFIX,
) -> FingerprintModelArtifact:
    """Train Story 4.2 against the persisted Story 4.2A dataset artifact path."""

    training_windows, dataset_manifest = load_persisted_training_dataset_artifacts(
        manifest_object_key=manifest_object_key,
        windows_object_key=windows_object_key,
        artifact_store=artifact_store,
    )
    return train_and_save_lstm_fingerprint(
        training_windows=training_windows,
        dataset_manifest=dataset_manifest,
        artifact_store=artifact_store,
        epochs=epochs,
        batch_size=batch_size,
        latent_units=latent_units,
        model_prefix=model_prefix,
    )


def build_lstm_autoencoder(
    *,
    keras,
    sequence_length: int,
    feature_count: int,
    latent_units: int,
):
    """Build a simple LSTM autoencoder for normal-sequence reconstruction."""

    inputs = keras.Input(shape=(sequence_length, feature_count), name="input_window")
    encoded = keras.layers.LSTM(latent_units, name="encoder_lstm")(inputs)
    repeated = keras.layers.RepeatVector(sequence_length, name="repeat_latent")(encoded)
    decoded = keras.layers.LSTM(
        latent_units,
        return_sequences=True,
        name="decoder_lstm",
    )(repeated)
    outputs = keras.layers.TimeDistributed(
        keras.layers.Dense(feature_count),
        name="reconstructed_window",
    )(decoded)
    model = keras.Model(inputs, outputs, name="compressor_fingerprint_lstm_autoencoder")
    model.compile(optimizer="adam", loss="mse")
    return model


def _load_keras_module():
    backend = os.getenv("KERAS_BACKEND")
    if backend and backend != "torch":
        raise RuntimeError(
            "Story 4.2 requires KERAS_BACKEND=torch. Clear the variable or set it to 'torch'."
        )
    os.environ["KERAS_BACKEND"] = "torch"

    if importlib.util.find_spec("keras") is None:
        raise RuntimeError(
            "Story 4.2 training requires the 'keras' package. "
            "Install project ML dependencies before training."
        )
    if importlib.util.find_spec("torch") is None:
        raise RuntimeError(
            "Story 4.2 training requires the 'torch' package for the approved Keras backend."
        )

    return importlib.import_module("keras")


def _export_model_bytes(model, model_id: str) -> bytes:
    keras = importlib.import_module("keras")
    # Compose a native .keras archive from Keras' own config/metadata plus
    # a real weights export. This avoids the save path that hangs on the
    # current torch-backend Windows runtime while keeping the artifact loadable.
    config_json, metadata_json = keras.src.saving.saving_lib._serialize_model_as_json(
        model
    )
    EXPORT_SCRATCH_ROOT.mkdir(parents=True, exist_ok=True)
    weights_path = EXPORT_SCRATCH_ROOT / f"{model_id}.weights.h5"
    weights_path.unlink(missing_ok=True)
    try:
        model.save_weights(str(weights_path))
        payload = io.BytesIO()
        with zipfile.ZipFile(payload, "w") as archive:
            archive.writestr("metadata.json", metadata_json)
            archive.writestr("config.json", config_json)
            archive.write(weights_path, arcname="model.weights.h5")
        return payload.getvalue()
    finally:
        weights_path.unlink(missing_ok=True)


def _build_model_id(dataset_id: str, created_at: str) -> str:
    timestamp = (
        created_at.replace("-", "")
        .replace(":", "")
        .replace(".", "")
        .replace("+00:00", "Z")
    )
    normalized_dataset_id = dataset_id.replace("::", "-")
    return f"lstm-fingerprint-{normalized_dataset_id}-{timestamp}"


def _extract_final_loss(history) -> float | None:
    loss_values = getattr(history, "history", {}).get("loss")
    if not loss_values:
        return None
    return float(loss_values[-1])
