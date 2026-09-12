"""Closed, data-only contracts for Story 9.6 evidence manifests."""

from __future__ import annotations

from dataclasses import dataclass, field, fields
from enum import StrEnum
from typing import Mapping


class AccessClass(StrEnum):
    DETECTOR_FACING = "detector_facing"
    EVALUATOR_RESTRICTED = "evaluator_restricted"
    PUBLIC_REFERENCE = "public_reference"


class ProvenanceRelation(StrEnum):
    USED = "used"
    WAS_GENERATED_BY = "was_generated_by"
    WAS_DERIVED_FROM = "was_derived_from"
    EVALUATED_WITH = "evaluated_with"
    REFERENCES = "references"


class BindingDisposition(StrEnum):
    BOUND = "bound"
    NOT_APPLICABLE = "not_applicable"
    UNAVAILABLE_BLOCKING = "unavailable_blocking"


class ExecutionOutcome(StrEnum):
    COMPLETE = "complete"
    ABORTED = "aborted"
    FAILED = "failed"
    INVALIDATED = "invalidated"


class FindingDisposition(StrEnum):
    FAVORABLE = "favorable"
    UNFAVORABLE = "unfavorable"
    INCONCLUSIVE = "inconclusive"
    NOT_APPLICABLE = "not_applicable"


def _value(value: object) -> object:
    if isinstance(value, StrEnum):
        return value.value
    if hasattr(value, "to_dict"):
        return value.to_dict()  # type: ignore[no-any-return,attr-defined]
    if isinstance(value, Mapping):
        return {str(key): _value(item) for key, item in value.items()}
    if isinstance(value, tuple):
        return [_value(item) for item in value]
    return value


class _Record:
    def to_dict(self) -> dict[str, object]:
        return {item.name: _value(getattr(self, item.name)) for item in fields(self)}


@dataclass(frozen=True)
class ImmutableReference(_Record):
    revision_id: str
    serialized_sha256: str
    subject_sha256: str | None
    contract_id: str
    contract_version: str
    locator: str
    evidence_role: str


@dataclass(frozen=True)
class ProvenanceEdge(_Record):
    relation: ProvenanceRelation | str
    target: ImmutableReference
    expected_contract_id: str
    expected_contract_version: str
    expected_subject_sha256: str | None
    expected_evidence_role: str


@dataclass(frozen=True)
class BindingSlot(_Record):
    name: str
    disposition: BindingDisposition | str
    reference: ImmutableReference | None
    reason: str | None


@dataclass(frozen=True)
class RequirementProfile(_Record):
    profile_id: str
    profile_revision_id: str
    required_slots: tuple[str, ...]
    not_applicable_slots: tuple[str, ...]
    metric_definition_ids: tuple[str, ...]
    limitations: tuple[str, ...]
    authorization_effect: str = field(default="none", init=False)

    def __post_init__(self) -> None:
        for name in ("required_slots", "not_applicable_slots", "metric_definition_ids", "limitations"):
            object.__setattr__(self, name, tuple(sorted(getattr(self, name))))


@dataclass(frozen=True)
class ManifestViolation(_Record):
    rule_id: str
    record_id: str
    field_path: str
    expected_value: str
    observed_value: str
    explanation: str


@dataclass(frozen=True)
class ArtifactManifest(_Record):
    logical_artifact_id: str
    manifest_revision_id: str
    content_sha256: str
    byte_size: int
    evidence_identity: Mapping[str, object]
    access_class: AccessClass | str
    contract_id: str
    contract_version: str
    schema_id: str
    schema_sha256: str
    media_type: str
    locator: str
    created_at: str
    producer_activity_id: str
    producer_agent_id: str
    tool_identity: str
    code_identity: str
    dependency_lock_sha256: str
    runtime_identity: str
    source_use_ids: tuple[str, ...]
    provenance_edges: tuple[ProvenanceEdge, ...]
    limitations: tuple[str, ...]
    authorization_effect: str = field(default="none", init=False)

    def __post_init__(self) -> None:
        object.__setattr__(self, "evidence_identity", dict(self.evidence_identity))
        object.__setattr__(self, "source_use_ids", tuple(sorted(self.source_use_ids)))
        object.__setattr__(self, "provenance_edges", tuple(sorted(
            self.provenance_edges, key=lambda item: (str(item.relation), item.target.revision_id),
        )))
        object.__setattr__(self, "limitations", tuple(sorted(self.limitations)))


@dataclass(frozen=True)
class RunManifest(_Record):
    logical_run_id: str
    manifest_revision_id: str
    run_kind: str
    requirement_profile: ImmutableReference
    bindings: tuple[BindingSlot, ...]
    access_class: AccessClass | str
    created_at: str
    limitations: tuple[str, ...]
    authorization_effect: str = field(default="none", init=False)

    def __post_init__(self) -> None:
        object.__setattr__(self, "bindings", tuple(sorted(self.bindings, key=lambda item: item.name)))
        object.__setattr__(self, "limitations", tuple(sorted(self.limitations)))


@dataclass(frozen=True)
class BundleManifest(_Record):
    logical_bundle_id: str
    manifest_revision_id: str
    requirement_profile: ImmutableReference
    modality: str
    component_artifacts: tuple[BindingSlot, ...]
    access_class: AccessClass | str
    created_at: str
    limitations: tuple[str, ...]
    package_content_sha256: str | None
    authorization_effect: str = field(default="none", init=False)

    def __post_init__(self) -> None:
        object.__setattr__(self, "component_artifacts", tuple(sorted(
            self.component_artifacts, key=lambda item: item.name,
        )))
        object.__setattr__(self, "limitations", tuple(sorted(self.limitations)))


@dataclass(frozen=True)
class MetricRecord(_Record):
    metric_definition: ImmutableReference
    protocol_level: str
    direction: str
    unit: str
    value: str | None
    support_reference: ImmutableReference | None
    uncertainty_reference: ImmutableReference | None
    availability_reason: str | None


@dataclass(frozen=True)
class EvaluationResult(_Record):
    logical_evaluation_id: str
    manifest_revision_id: str
    dataset_family: str
    dataset_version: str
    native_scope: str
    track: str
    modality_or_result_kind: str
    requirement_profile: ImmutableReference
    support_set: ImmutableReference
    run_references: tuple[ImmutableReference, ...]
    bindings: tuple[BindingSlot, ...]
    metrics: tuple[MetricRecord, ...]
    execution_outcome: ExecutionOutcome | str
    finding_disposition: FindingDisposition | str
    access_class: AccessClass | str
    created_at: str
    limitations: tuple[str, ...]
    final_output: ImmutableReference | None
    authorization_effect: str = field(default="none", init=False)

    def __post_init__(self) -> None:
        object.__setattr__(self, "run_references", tuple(sorted(
            self.run_references, key=lambda item: item.revision_id,
        )))
        object.__setattr__(self, "bindings", tuple(sorted(self.bindings, key=lambda item: item.name)))
        object.__setattr__(self, "metrics", tuple(sorted(
            self.metrics, key=lambda item: item.metric_definition.revision_id,
        )))
        object.__setattr__(self, "limitations", tuple(sorted(self.limitations)))


@dataclass(frozen=True)
class AliasResolution(_Record):
    resolution_id: str
    requested_alias: str
    resolver_snapshot_id: str
    resolved_target: ImmutableReference
    observed_at: str
    authorization_effect: str = field(default="none", init=False)


@dataclass(frozen=True)
class PublicationReceipt(_Record):
    receipt_id: str
    manifest_revision_id: str
    manifest_serialized_sha256: str
    repository_snapshot_id: str
    authorization_effect: str = field(default="none", init=False)
