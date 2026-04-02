"""Typed dataset-artifact contracts for Epic 4 Story 4.2A."""

from __future__ import annotations

from dataclasses import dataclass


@dataclass(frozen=True)
class DatasetAdequacyAssessment:
    """Explicit adequacy result for one persisted training dataset."""

    validation_level: str
    adequacy_met: bool
    status_reason: str
    minimum_eligible_artifact_count: int
    minimum_window_count: int
    eligible_artifact_count: int
    window_count: int
    eligible_artifact_floor_met: bool
    window_floor_met: bool

    def to_dict(self) -> dict[str, object]:
        return {
            "validation_level": self.validation_level,
            "adequacy_met": self.adequacy_met,
            "status_reason": self.status_reason,
            "minimum_eligible_artifact_count": self.minimum_eligible_artifact_count,
            "minimum_window_count": self.minimum_window_count,
            "eligible_artifact_count": self.eligible_artifact_count,
            "window_count": self.window_count,
            "eligible_artifact_floor_met": self.eligible_artifact_floor_met,
            "window_floor_met": self.window_floor_met,
        }


@dataclass(frozen=True)
class PersistedTrainingDatasetArtifact:
    """Inspectable persisted dataset manifest for Story 4.2A."""

    dataset_id: str
    created_at: str
    source_bucket: str
    source_prefix: str
    manifest_object_key: str
    windows_object_key: str
    chronological_ordering_rule: str
    sequence_length: int
    stride: int
    overlap_behavior: str
    feature_schema: tuple[str, ...]
    selected_artifact_keys: tuple[str, ...]
    skipped_artifacts: dict[str, str]
    eligible_artifact_count: int
    window_count: int
    tensor_shape: tuple[int, int, int]
    training_label: str
    adequacy_assessment: DatasetAdequacyAssessment

    def to_dict(self) -> dict[str, object]:
        return {
            "dataset_id": self.dataset_id,
            "created_at": self.created_at,
            "source_bucket": self.source_bucket,
            "source_prefix": self.source_prefix,
            "manifest_object_key": self.manifest_object_key,
            "windows_object_key": self.windows_object_key,
            "chronological_ordering_rule": self.chronological_ordering_rule,
            "sequence_length": self.sequence_length,
            "stride": self.stride,
            "overlap_behavior": self.overlap_behavior,
            "feature_schema": list(self.feature_schema),
            "selected_artifact_keys": list(self.selected_artifact_keys),
            "skipped_artifacts": dict(sorted(self.skipped_artifacts.items())),
            "eligible_artifact_count": self.eligible_artifact_count,
            "window_count": self.window_count,
            "tensor_shape": list(self.tensor_shape),
            "training_label": self.training_label,
            "adequacy_assessment": self.adequacy_assessment.to_dict(),
        }
