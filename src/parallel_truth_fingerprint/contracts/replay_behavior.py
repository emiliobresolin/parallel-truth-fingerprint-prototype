"""Typed replay-behavior contracts for Epic 4 Story 4.4."""

from __future__ import annotations

from dataclasses import dataclass

from parallel_truth_fingerprint.contracts.fingerprint_inference import (
    FingerprintInferenceClassification,
)


@dataclass(frozen=True)
class ReplayBehaviorResult:
    """Replay-oriented anomaly result derived from the existing fingerprint path."""

    output_channel: str
    scenario_mode: str
    current_round_id: str
    scada_source_round_id: str
    replay_source_round_id: str | None
    model_id: str
    source_dataset_id: str
    inference_dataset_id: str
    source_dataset_validation_level: str
    limitation_note: str | None
    window_id: str
    artifact_keys: tuple[str, ...]
    anomaly_score: float
    classification_threshold: float
    classification: FingerprintInferenceClassification
    scada_divergent_sensors: tuple[str, ...]
    consensus_final_status: str

    def to_dict(self) -> dict[str, object]:
        return {
            "output_channel": self.output_channel,
            "scenario_mode": self.scenario_mode,
            "current_round_id": self.current_round_id,
            "scada_source_round_id": self.scada_source_round_id,
            "replay_source_round_id": self.replay_source_round_id,
            "model_id": self.model_id,
            "source_dataset_id": self.source_dataset_id,
            "inference_dataset_id": self.inference_dataset_id,
            "source_dataset_validation_level": self.source_dataset_validation_level,
            "limitation_note": self.limitation_note,
            "window_id": self.window_id,
            "artifact_keys": list(self.artifact_keys),
            "anomaly_score": self.anomaly_score,
            "classification_threshold": self.classification_threshold,
            "classification": self.classification.value,
            "scada_divergent_sensors": list(self.scada_divergent_sensors),
            "consensus_final_status": self.consensus_final_status,
        }
