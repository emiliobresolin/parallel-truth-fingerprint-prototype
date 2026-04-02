"""Typed trained-fingerprint metadata contracts for Epic 4 Story 4.2."""

from __future__ import annotations

from dataclasses import dataclass


@dataclass(frozen=True)
class FingerprintModelArtifact:
    """Structured metadata for one saved LSTM fingerprint model artifact."""

    model_id: str
    created_at: str
    backend: str
    model_format: str
    model_type: str
    source_dataset_id: str
    feature_schema: tuple[str, ...]
    sequence_length: int
    training_window_count: int
    epochs: int
    batch_size: int
    loss_name: str
    bucket: str
    model_object_key: str
    metadata_object_key: str
    artifact_uri: str
    metadata_uri: str
    final_training_loss: float | None = None

    def to_dict(self) -> dict[str, object]:
        return {
            "model_id": self.model_id,
            "created_at": self.created_at,
            "backend": self.backend,
            "model_format": self.model_format,
            "model_type": self.model_type,
            "source_dataset_id": self.source_dataset_id,
            "feature_schema": list(self.feature_schema),
            "sequence_length": self.sequence_length,
            "training_window_count": self.training_window_count,
            "epochs": self.epochs,
            "batch_size": self.batch_size,
            "loss_name": self.loss_name,
            "bucket": self.bucket,
            "model_object_key": self.model_object_key,
            "metadata_object_key": self.metadata_object_key,
            "artifact_uri": self.artifact_uri,
            "metadata_uri": self.metadata_uri,
            "final_training_loss": self.final_training_loss,
        }
