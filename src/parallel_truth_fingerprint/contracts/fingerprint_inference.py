"""Typed inference-result contracts for Epic 4 Story 4.3."""

from __future__ import annotations

from dataclasses import dataclass
from enum import Enum


class FingerprintInferenceClassification(str, Enum):
    """Bounded LSTM fingerprint classification."""

    NORMAL = "normal"
    ANOMALOUS = "anomalous"


@dataclass(frozen=True)
class FingerprintInferenceResult:
    """One LSTM fingerprint inference result for one valid temporal window."""

    output_channel: str
    model_id: str
    source_dataset_id: str
    inference_dataset_id: str
    source_dataset_validation_level: str
    limitation_note: str | None
    window_id: str
    artifact_keys: tuple[str, ...]
    round_ids: tuple[str, ...]
    timestamps: tuple[str, ...]
    anomaly_score: float
    classification_threshold: float
    threshold_origin: str
    classification: FingerprintInferenceClassification

    def to_dict(self) -> dict[str, object]:
        return {
            "output_channel": self.output_channel,
            "model_id": self.model_id,
            "source_dataset_id": self.source_dataset_id,
            "inference_dataset_id": self.inference_dataset_id,
            "source_dataset_validation_level": self.source_dataset_validation_level,
            "limitation_note": self.limitation_note,
            "window_id": self.window_id,
            "artifact_keys": list(self.artifact_keys),
            "round_ids": list(self.round_ids),
            "timestamps": list(self.timestamps),
            "anomaly_score": self.anomaly_score,
            "classification_threshold": self.classification_threshold,
            "threshold_origin": self.threshold_origin,
            "classification": self.classification.value,
        }
