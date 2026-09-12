"""Pure, fail-closed validation for :mod:`linux_edge_workload` contracts."""

from __future__ import annotations

import re
from dataclasses import dataclass
from typing import Callable

from parallel_truth_fingerprint.contracts.linux_edge_workload import (
    ExecutionPath, LinuxEdgeWorkload, WorkloadActivity, WorkloadEvidenceRole,
    WorkloadExecutionRequest, WorkloadRuntimeIdentity, linux_edge_workload_content_id,
)


_DIGEST = re.compile(r"sha256:[0-9a-f]{64}\Z")
_REQUIRED_EXCLUSIONS = frozenset({"mosquitto", "minio", "cometbft", "abci", "collector", "unrelated_container"})
_SAFE_ACTIVITIES = frozenset(item.value for item in WorkloadActivity)


@dataclass(frozen=True)
class LinuxWorkloadViolation:
    rule_id: str
    field: str
    detail: str


@dataclass(frozen=True)
class LinuxWorkloadValidation:
    allowed: bool
    violations: tuple[LinuxWorkloadViolation, ...]
    authorization_effect: str = "none"


def _digest(value: object) -> bool:
    return isinstance(value, str) and _DIGEST.fullmatch(value) is not None


def _add(items: list[LinuxWorkloadViolation], rule: str, field: str, detail: str) -> None:
    items.append(LinuxWorkloadViolation(rule, field, detail))


def validate_linux_edge_workload(workload: LinuxEdgeWorkload) -> LinuxWorkloadValidation:
    """Check an immutable workload declaration without resolving external state."""
    violations: list[LinuxWorkloadViolation] = []
    if workload.schema_version != "LinuxEdgeWorkload.v1":
        _add(violations, "LWE1_SCHEMA_VERSION_INVALID", "schema_version", "exact_v1_schema_required")
    if workload.authorization_effect != "none":
        _add(violations, "LWE1_AUTHORIZATION_EFFECT_INVALID", "authorization_effect", "declaration_must_not_authorize")
    if not _digest(workload.workload_id) or workload.workload_id != linux_edge_workload_content_id(workload):
        _add(violations, "LWE1_CONTENT_ID_INVALID", "workload_id", "canonical_content_identity_required")
    if workload.workload_content_id != workload.workload_id:
        _add(violations, "LWE1_CONTENT_ID_MISMATCH", "workload_content_id", "matching_workload_identity_required")
    for field, value in {
        "image_or_executable_identity": workload.image_or_executable_identity,
        "entrypoint_identity": workload.entrypoint_identity,
        "configuration_identity": workload.configuration_identity,
        "code_identity": workload.code_identity,
        "dependency_identity": workload.dependency_identity,
    }.items():
        if not _digest(value):
            _add(violations, "LWE1_IDENTITY_UNRESOLVED", field, "exact_immutable_identity_required")
    if not workload.expected_process_tree:
        _add(violations, "LWE1_PROCESS_TREE_EMPTY", "expected_process_tree", "declared_process_tree_required")
    roles = [item.process_role for item in workload.expected_process_tree]
    if any(not isinstance(role, str) or not role.strip() for role in roles) or len(roles) != len(set(roles)):
        _add(violations, "LWE1_PROCESS_TREE_INVALID", "expected_process_tree", "unique_nonempty_roles_required")
    for item in workload.expected_process_tree:
        if not _digest(item.executable_identity) or (item.parent_process_role is not None and item.parent_process_role not in roles):
            _add(violations, "LWE1_PROCESS_DECLARATION_INVALID", "expected_process_tree", "resolved_executable_and_declared_parent_required")
    if not isinstance(workload.edge_role, str) or not workload.edge_role.strip() or not isinstance(workload.experiment_role, str) or not workload.experiment_role.strip():
        _add(violations, "LWE1_ROLE_INVALID", "edge_role", "explicit_edge_and_experiment_roles_required")
    if not workload.permission_identities or any(not _digest(item) for item in workload.permission_identities):
        _add(violations, "LWE1_PERMISSION_IDENTITY_INVALID", "permission_identities", "nonempty_immutable_permissions_required")
    for field, interactions in (("network_interactions", workload.network_interactions), ("storage_interactions", workload.storage_interactions)):
        names = [item.interaction_role for item in interactions]
        if len(names) != len(set(names)) or any(not isinstance(name, str) or not name.strip() for name in names):
            _add(violations, "LWE1_INTERACTION_ROLE_INVALID", field, "unique_nonempty_interaction_roles_required")
        for item in interactions:
            ids = (item.endpoint_identity, item.protocol_identity) if field == "network_interactions" else (item.store_identity, item.schema_identity)
            if any(not _digest(value) for value in ids):
                _add(violations, "LWE1_INTERACTION_IDENTITY_INVALID", field, "exact_immutable_interaction_identities_required")
    activities = {str(item) for item in workload.allowed_activities}
    if not activities or not activities.issubset(_SAFE_ACTIVITIES):
        _add(violations, "LWE1_ACTIVITY_ALLOWLIST_INVALID", "allowed_activities", "only_closed_safe_activity_allowlist_permitted")
    role = str(workload.evidence_role)
    if role not in {item.value for item in WorkloadEvidenceRole}:
        _add(violations, "LWE1_EVIDENCE_ROLE_INVALID", "evidence_role", "closed_evidence_role_required")
    elif role == WorkloadEvidenceRole.FIXTURE_REPLAY.value and not workload.test_only:
        _add(violations, "LWE1_FIXTURE_REPLAY_NOT_TEST_ONLY", "test_only", "fixture_replay_must_be_test_only")
    elif role == WorkloadEvidenceRole.HOST_CAPTURE.value and workload.test_only:
        _add(violations, "LWE1_HOST_CAPTURE_TEST_ONLY", "test_only", "host_capture_cannot_be_fixture_replay")
    if not _REQUIRED_EXCLUSIONS.issubset(set(workload.excluded_process_roles)):
        _add(violations, "LWE1_INFRASTRUCTURE_EXCLUSION_MISSING", "excluded_process_roles", "all_required_infrastructure_exclusions_required")
    if workload.mock_admission_identity is not None and not _digest(workload.mock_admission_identity):
        _add(violations, "LWE1_MOCK_ADMISSION_ID_INVALID", "mock_admission_identity", "exact_immutable_identity_required")
    return LinuxWorkloadValidation(not violations, tuple(violations))


def validate_workload_execution(
    request: WorkloadExecutionRequest,
    *,
    authentic_reproduction_available: Callable[[LinuxEdgeWorkload], bool],
    mock_admission_valid: Callable[[str, LinuxEdgeWorkload], bool],
) -> LinuxWorkloadValidation:
    """Admit a selected path only; callers retain all execution responsibility."""
    base = list(validate_linux_edge_workload(request.workload).violations)
    if request.authorization_effect != "none" or request.runtime_identity.authorization_effect != "none":
        _add(base, "LWE1_EXECUTION_AUTHORIZATION_EFFECT_INVALID", "authorization_effect", "validation_cannot_authorize_execution")
    path = str(request.path)
    if path not in {item.value for item in ExecutionPath}:
        _add(base, "LWE1_EXECUTION_PATH_INVALID", "path", "closed_execution_path_required")
    requested = {str(item) for item in request.requested_activities}
    if not requested or not requested.issubset({str(item) for item in request.workload.allowed_activities}):
        _add(base, "LWE1_ACTIVITY_NOT_ALLOWLISTED", "requested_activities", "requested_activity_must_be_declared")
    _validate_runtime_identity(request.runtime_identity, base)
    available = authentic_reproduction_available(request.workload)
    if path == ExecutionPath.AUTHENTIC.value and not available:
        _add(base, "LWE1_AUTHENTIC_PATH_UNAVAILABLE", "path", "authentic_path_not_reproducible")
    if path == ExecutionPath.MOCK.value:
        admission = request.workload.mock_admission_identity
        if available:
            _add(base, "LWE1_MOCK_REJECTED_AUTHENTIC_AVAILABLE", "path", "authentic_path_remains_authoritative")
        elif admission is None or not mock_admission_valid(admission, request.workload):
            _add(base, "LWE1_MOCK_ADMISSION_REJECTED", "mock_admission_identity", "exact_approved_mock_admission_required")
    return LinuxWorkloadValidation(not base, tuple(base))


def _validate_runtime_identity(identity: WorkloadRuntimeIdentity, violations: list[LinuxWorkloadViolation]) -> None:
    values = {
        "host_or_vm_identity": identity.host_or_vm_identity, "boot_identity": identity.boot_identity,
        "container_identity": identity.container_identity, "cgroup_identity": identity.cgroup_identity,
        "process_identity": identity.process_identity, "kernel_identity": identity.kernel_identity,
        "architecture_identity": identity.architecture_identity, "edge_identity": identity.edge_identity,
        "experiment_identity": identity.experiment_identity, "run_identity": identity.run_identity,
        "correlation_identity": identity.correlation_identity,
    }
    if any(not _digest(value) for value in values.values()) or any(not _digest(value) for value in identity.thread_identities):
        _add(violations, "LWE1_RUNTIME_IDENTITY_UNRESOLVED", "runtime_identity", "complete_exact_runtime_identity_required")
