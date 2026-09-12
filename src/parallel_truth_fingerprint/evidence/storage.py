"""Pure identities and fail-closed validation for Story 9.7 storage records."""

from __future__ import annotations

import hashlib
import re

from parallel_truth_fingerprint.contracts.evidence_storage import (
    BackendKind, CapabilityState, ObjectLockState, QualificationResult,
    RolePrefixPolicy, StoragePhase, StorageQualificationPlan,
    StorageQualificationReport, StorageSnapshotManifest, StorageViolation,
    VersioningState, VolumeKind,
)
from parallel_truth_fingerprint.evidence.manifests import canonical_manifest_bytes


_DIGEST = re.compile(r"sha256:[0-9a-f]{64}\Z")
_UTC = re.compile(r"[0-9]{4}-[0-9]{2}-[0-9]{2}T[0-9]{2}:[0-9]{2}:[0-9]{2}\.[0-9]{6}Z\Z")


def _identity(record: object, field: str) -> str:
    payload = record.to_dict()
    payload[field] = ""
    return "sha256:" + hashlib.sha256(canonical_manifest_bytes(_DictRecord(payload))).hexdigest()


class _DictRecord:
    def __init__(self, payload: dict[str, object]) -> None:
        self._payload = payload

    def to_dict(self) -> dict[str, object]:
        return self._payload


def storage_qualification_plan_identity(record: StorageQualificationPlan) -> str:
    return _identity(record, "plan_revision_id")


def storage_qualification_report_identity(record: StorageQualificationReport) -> str:
    return _identity(record, "report_revision_id")


def storage_snapshot_manifest_identity(record: StorageSnapshotManifest) -> str:
    return _identity(record, "snapshot_revision_id")


def validate_storage_snapshot(
    snapshot: StorageSnapshotManifest, *, observed: dict[str, bytes],
) -> tuple[StorageViolation, ...]:
    """Verify a closed exported set before a distinct restore operation."""
    violations: list[StorageViolation] = []
    if snapshot.snapshot_revision_id != storage_snapshot_manifest_identity(snapshot):
        violations.append(_violation("STORAGE-SNAPSHOT-REVISION-MISMATCH", "snapshot", "snapshot_revision_id", storage_snapshot_manifest_identity(snapshot), snapshot.snapshot_revision_id, "Snapshot identity must bind its closed object set."))
    declared = {item.immutable_key: item for item in snapshot.object_observations}
    for key in sorted(set(observed) - set(declared)):
        violations.append(_violation("STORAGE-SNAPSHOT-EXTRA", "snapshot", "objects", "declared closed set", key, "Restoration cannot include undeclared objects."))
    for key, item in declared.items():
        payload = observed.get(key)
        if payload is None:
            violations.append(_violation("STORAGE-SNAPSHOT-MISSING", "snapshot", "objects", key, "missing", "Every declared object must be present before restore."))
            continue
        actual = "sha256:" + hashlib.sha256(payload).hexdigest()
        if len(payload) != item.byte_size or actual != item.content_sha256:
            violations.append(_violation("STORAGE-SNAPSHOT-HASH-MISMATCH", "snapshot", "objects", f"{item.byte_size}|{item.content_sha256}", f"{len(payload)}|{actual}", "Snapshot bytes must exactly match the declared scientific identity."))
        expected_prefix = {
            RolePrefixPolicy.DETECTOR_FACING.value: "detector-facing",
            RolePrefixPolicy.EVALUATOR_RESTRICTED.value: "evaluator-restricted",
            RolePrefixPolicy.PUBLIC_REFERENCE.value: "public-reference",
        }.get(_token(item.role_prefix_policy))
        if expected_prefix is None or not key.startswith(f"formal/v1/{expected_prefix}/"):
            violations.append(_violation("STORAGE-SNAPSHOT-ROLE-MISMATCH", "snapshot", "role_prefix_policy", "key role prefix", key, "Stored keys cannot cross role namespaces."))
    return tuple(sorted(violations, key=lambda item: (item.rule_id, item.field_path, item.observed_value)))


def _token(value: object) -> str:
    return str(value.value if hasattr(value, "value") else value)


def _violation(rule_id: str, phase: object, field: str, expected: object, observed: object, explanation: str) -> StorageViolation:
    def safe(value: object) -> str:
        text = str(value)
        if any(token in text.casefold() for token in ("secret", "password", "access_key", "token=")):
            return "[REDACTED]"
        return "sha256:" + hashlib.sha256(text.encode()).hexdigest()
    return StorageViolation(rule_id, _token(phase), field, safe(expected), safe(observed), explanation)


def validate_storage_qualification_report(
    report: StorageQualificationReport, *, plan: StorageQualificationPlan,
    registered_source_uses: frozenset[str] | None = None,
) -> tuple[StorageViolation, ...]:
    violations: list[StorageViolation] = []
    if plan.plan_revision_id != storage_qualification_plan_identity(plan):
        violations.append(_violation("STORAGE-PLAN-REVISION-MISMATCH", "preflight", "plan_revision_id", storage_qualification_plan_identity(plan), plan.plan_revision_id, "Plan identity must bind every safe configuration observation."))
    if _token(plan.backend_kind) not in {item.value for item in BackendKind}:
        violations.append(_violation("STORAGE-BACKEND-INVALID", "preflight", "backend_kind", "closed backend", plan.backend_kind, "Unknown backends block qualification."))
    for value, enum, field in ((plan.volume_kind, VolumeKind, "volume_kind"), (plan.versioning_state, VersioningState, "versioning_state"), (plan.object_lock_state, ObjectLockState, "object_lock_state")):
        if _token(value) not in {item.value for item in enum}:
            violations.append(_violation("STORAGE-OBSERVATION-INVALID", "preflight", field, "closed observation", value, "Required storage observations use closed tokens."))
    if not _UTC.fullmatch(plan.observed_at) or not all(_DIGEST.fullmatch(value) for value in (plan.server_image_digest, plan.compose_sha256, plan.dependency_lock_sha256, plan.fixture_reference)):
        violations.append(_violation("STORAGE-PLAN-IDENTITY-INVALID", "preflight", "identity", "UTC and lowercase digests", "invalid", "Qualification identities are exact and immutable."))
    if report.plan_revision_id != plan.plan_revision_id or report.report_revision_id != storage_qualification_report_identity(report):
        violations.append(_violation("STORAGE-REPORT-REVISION-MISMATCH", "report", "report_revision_id", "report bound to plan", report.report_revision_id, "Report identity binds its exact plan and phases."))
    if _token(report.qualification_result) not in {item.value for item in QualificationResult}:
        violations.append(_violation("STORAGE-RESULT-INVALID", "report", "qualification_result", "closed result", report.qualification_result, "Qualification results are closed."))
    if registered_source_uses is not None and _token(report.qualification_result) == QualificationResult.QUALIFIED.value:
        missing = sorted(set(plan.source_use_ids) - registered_source_uses)
        if missing:
            violations.append(_violation("STORAGE-SOURCE-USE-UNRESOLVED", "preflight", "source_use_ids", "registered immutable source uses", missing, "A qualified storage report requires every declared technical authority to be registered."))
    for phase in report.phase_observations:
        if _token(phase.phase) not in {item.value for item in StoragePhase}:
            violations.append(_violation("STORAGE-PHASE-INVALID", phase.phase, "phase", "closed phase", phase.phase, "Unknown phases block a report."))
        if _token(phase.result) not in {item.value for item in QualificationResult} or not _DIGEST.fullmatch(phase.environment_identity):
            violations.append(_violation("STORAGE-PHASE-INVALID", phase.phase, "result_or_environment", "closed result and digest", "invalid", "Phase outcomes must be reproducible observations."))
        for observed in phase.object_observations:
            if (_token(observed.role_prefix_policy) not in {item.value for item in RolePrefixPolicy}
                    or _token(observed.capability_state) not in {item.value for item in CapabilityState}
                    or observed.byte_size < 0 or not _DIGEST.fullmatch(observed.content_sha256)):
                violations.append(_violation("STORAGE-OBJECT-INVALID", phase.phase, "object_observation", "closed role/capability and digest", "invalid", "ETag is only backend metadata, never content authority."))
    if report.authorization_effect != "none" or plan.authorization_effect != "none":
        violations.append(_violation("STORAGE-AUTHORIZATION-PROHIBITED", "report", "authorization_effect", "none", report.authorization_effect, "Storage qualification cannot authorize activity."))
    return tuple(sorted(violations, key=lambda item: (item.rule_id, item.phase, item.field_path)))
