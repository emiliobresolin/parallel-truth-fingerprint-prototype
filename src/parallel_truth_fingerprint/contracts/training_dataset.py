"""Typed dataset-building contracts for Epic 4 Story 4.1."""

from __future__ import annotations

from dataclasses import dataclass


@dataclass(frozen=True)
class TrainingWindow:
    """One fixed-length normal training window derived from valid artifacts."""

    window_id: str
    artifact_keys: tuple[str, ...]
    round_ids: tuple[str, ...]
    timestamps: tuple[str, ...]
    feature_schema: tuple[str, ...]
    feature_matrix: tuple[tuple[float, ...], ...]
    label: str = "normal"

    def to_dict(self) -> dict[str, object]:
        return {
            "window_id": self.window_id,
            "artifact_keys": list(self.artifact_keys),
            "round_ids": list(self.round_ids),
            "timestamps": list(self.timestamps),
            "feature_schema": list(self.feature_schema),
            "feature_matrix": [list(row) for row in self.feature_matrix],
            "label": self.label,
        }


@dataclass(frozen=True)
class TrainingDatasetManifest:
    """Traceability manifest for one deterministic dataset-building run."""

    dataset_id: str
    source_bucket: str
    source_prefix: str
    sequence_length: int
    feature_schema: tuple[str, ...]
    selected_artifact_keys: tuple[str, ...]
    skipped_artifacts: dict[str, str]
    eligible_record_count: int
    window_count: int
    training_label: str = "normal"

    def to_dict(self) -> dict[str, object]:
        return {
            "dataset_id": self.dataset_id,
            "source_bucket": self.source_bucket,
            "source_prefix": self.source_prefix,
            "sequence_length": self.sequence_length,
            "feature_schema": list(self.feature_schema),
            "selected_artifact_keys": list(self.selected_artifact_keys),
            "skipped_artifacts": dict(sorted(self.skipped_artifacts.items())),
            "eligible_record_count": self.eligible_record_count,
            "window_count": self.window_count,
            "training_label": self.training_label,
        }
