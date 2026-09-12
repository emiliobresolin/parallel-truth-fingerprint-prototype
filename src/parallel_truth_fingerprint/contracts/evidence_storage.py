"""Closed, immutable data contracts for minimal evidence-storage qualification."""

from __future__ import annotations

from dataclasses import dataclass, field, fields
from enum import StrEnum


class BackendKind(StrEnum):
    MINIO_S3 = "minio_s3"


class StoragePhase(StrEnum):
    PREFLIGHT = "preflight"
    CONDITIONAL_CREATE = "conditional_create"
    PUBLICATION = "publication"
    SERVICE_RESTART = "service_restart"
    CONTAINER_RECREATION = "container_recreation"
    SNAPSHOT = "snapshot"
    RESTORATION = "restoration"


class QualificationResult(StrEnum):
    QUALIFIED = "qualified"
    BLOCKED = "blocked"
    ABORTED = "aborted"


class VolumeKind(StrEnum):
    NAMED = "named"
    EXPLICIT_BIND = "explicit_bind"
    UNKNOWN_BLOCKING = "unknown_blocking"


class VersioningState(StrEnum):
    ENABLED = "enabled"
    DISABLED = "disabled"
    UNKNOWN_BLOCKING = "unknown_blocking"


class ObjectLockState(StrEnum):
    ENABLED = "enabled"
    DISABLED = "disabled"
    UNKNOWN_BLOCKING = "unknown_blocking"


class CapabilityState(StrEnum):
    PROVEN = "proven"
    UNAVAILABLE_BLOCKING = "unavailable_blocking"
    UNKNOWN_BLOCKING = "unknown_blocking"


class RolePrefixPolicy(StrEnum):
    DETECTOR_FACING = "detector_facing"
    EVALUATOR_RESTRICTED = "evaluator_restricted"
    PUBLIC_REFERENCE = "public_reference"


def _value(value: object) -> object:
    if isinstance(value, StrEnum):
        return value.value
    if hasattr(value, "to_dict"):
        return value.to_dict()  # type: ignore[no-any-return,attr-defined]
    if isinstance(value, tuple):
        return [_value(item) for item in value]
    return value


class _Record:
    def to_dict(self) -> dict[str, object]:
        return {item.name: _value(getattr(self, item.name)) for item in fields(self)}


@dataclass(frozen=True)
class StorageViolation(_Record):
    rule_id: str
    phase: str
    field_path: str
    expected_value: str
    observed_value: str
    explanation: str


@dataclass(frozen=True)
class StorageQualificationPlan(_Record):
    plan_revision_id: str
    backend_kind: BackendKind | str
    endpoint_identity: str
    bucket_name: str
    namespace_policy_revision: str
    server_image_digest: str
    server_release: str
    compose_sha256: str
    volume_kind: VolumeKind | str
    volume_identity: str
    versioning_state: VersioningState | str
    object_lock_state: ObjectLockState | str
    client_identity: str
    dependency_lock_sha256: str
    runtime_identity: str
    fixture_reference: str
    source_use_ids: tuple[str, ...]
    observed_at: str
    authorization_effect: str = field(default="none", init=False)

    def __post_init__(self) -> None:
        object.__setattr__(self, "source_use_ids", tuple(sorted(set(self.source_use_ids))))


@dataclass(frozen=True)
class StorageObjectObservation(_Record):
    immutable_key: str
    role_prefix_policy: RolePrefixPolicy | str
    byte_size: int
    content_sha256: str
    backend_version_id: str | None
    backend_etag: str | None
    capability_state: CapabilityState | str


@dataclass(frozen=True)
class StoragePhaseObservation(_Record):
    phase: StoragePhase | str
    result: QualificationResult | str
    environment_identity: str
    object_observations: tuple[StorageObjectObservation, ...]
    violation_rule_ids: tuple[str, ...]
    limitations: tuple[str, ...]

    def __post_init__(self) -> None:
        object.__setattr__(self, "object_observations", tuple(sorted(
            self.object_observations, key=lambda item: item.immutable_key,
        )))
        object.__setattr__(self, "violation_rule_ids", tuple(sorted(set(self.violation_rule_ids))))
        object.__setattr__(self, "limitations", tuple(sorted(set(self.limitations))))


@dataclass(frozen=True)
class StorageSnapshotManifest(_Record):
    snapshot_revision_id: str
    source_plan_revision_id: str
    object_observations: tuple[StorageObjectObservation, ...]
    authorization_effect: str = field(default="none", init=False)

    def __post_init__(self) -> None:
        object.__setattr__(self, "object_observations", tuple(sorted(
            self.object_observations, key=lambda item: item.immutable_key,
        )))


@dataclass(frozen=True)
class StorageQualificationReport(_Record):
    report_revision_id: str
    plan_revision_id: str
    qualification_result: QualificationResult | str
    phase_observations: tuple[StoragePhaseObservation, ...]
    limitations: tuple[str, ...]
    authorization_effect: str = field(default="none", init=False)

    def __post_init__(self) -> None:
        object.__setattr__(self, "phase_observations", tuple(self.phase_observations))
        object.__setattr__(self, "limitations", tuple(sorted(set(self.limitations))))
