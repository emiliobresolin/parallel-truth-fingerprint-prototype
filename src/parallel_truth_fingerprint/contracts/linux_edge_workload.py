"""Immutable, non-executing contract for a declared Linux edge workload.

This module deliberately describes a workload only.  It has no process,
container, network, capture, persistence, or authorization side effect.
"""

from __future__ import annotations

import hashlib
import json
from dataclasses import dataclass, fields
from enum import StrEnum
from typing import Any


LINUX_EDGE_WORKLOAD_VERSION = "LinuxEdgeWorkload.v1"


class WorkloadActivity(StrEnum):
    SAFE_ACQUISITION = "safe_acquisition"
    SERIALIZATION = "serialization"
    MQTT = "mqtt"
    CONSENSUS_INTERACTION = "consensus_interaction"
    EVIDENCE_WRITE = "evidence_write"
    APPROVED_DEVIATION = "approved_deviation"


class WorkloadEvidenceRole(StrEnum):
    HOST_CAPTURE = "host_capture"
    FIXTURE_REPLAY = "fixture-replay"


class ExecutionPath(StrEnum):
    AUTHENTIC = "authentic"
    MOCK = "mock"


@dataclass(frozen=True)
class ProcessDeclaration:
    process_role: str
    executable_identity: str
    parent_process_role: str | None


@dataclass(frozen=True)
class NetworkInteraction:
    interaction_role: str
    endpoint_identity: str
    protocol_identity: str


@dataclass(frozen=True)
class StorageInteraction:
    interaction_role: str
    store_identity: str
    schema_identity: str


@dataclass(frozen=True)
class LinuxEdgeWorkload:
    """A content-addressed allowlist declaration, never an execution command."""

    schema_version: str
    workload_id: str
    image_or_executable_identity: str
    entrypoint_identity: str
    expected_process_tree: tuple[ProcessDeclaration, ...]
    edge_role: str
    experiment_role: str
    permission_identities: tuple[str, ...]
    network_interactions: tuple[NetworkInteraction, ...]
    storage_interactions: tuple[StorageInteraction, ...]
    configuration_identity: str
    code_identity: str
    dependency_identity: str
    mock_admission_identity: str | None
    allowed_activities: tuple[WorkloadActivity | str, ...]
    evidence_role: WorkloadEvidenceRole | str
    test_only: bool
    excluded_process_roles: tuple[str, ...]
    workload_content_id: str
    authorization_effect: str = "none"

    def __post_init__(self) -> None:
        object.__setattr__(self, "expected_process_tree", tuple(sorted(self.expected_process_tree, key=lambda item: item.process_role)))
        for name in ("permission_identities", "allowed_activities", "excluded_process_roles"):
            object.__setattr__(self, name, tuple(sorted(set(getattr(self, name)), key=str)))
        object.__setattr__(self, "network_interactions", tuple(sorted(self.network_interactions, key=lambda item: item.interaction_role)))
        object.__setattr__(self, "storage_interactions", tuple(sorted(self.storage_interactions, key=lambda item: item.interaction_role)))

    def to_dict(self) -> dict[str, Any]:
        return {field.name: _plain(getattr(self, field.name)) for field in fields(self)}


@dataclass(frozen=True)
class WorkloadRuntimeIdentity:
    host_or_vm_identity: str
    boot_identity: str
    container_identity: str
    cgroup_identity: str
    process_identity: str
    thread_identities: tuple[str, ...]
    kernel_identity: str
    architecture_identity: str
    edge_identity: str
    experiment_identity: str
    run_identity: str
    correlation_identity: str
    authorization_effect: str = "none"

    def __post_init__(self) -> None:
        object.__setattr__(self, "thread_identities", tuple(sorted(set(self.thread_identities))) )


@dataclass(frozen=True)
class WorkloadExecutionRequest:
    workload: LinuxEdgeWorkload
    path: ExecutionPath | str
    runtime_identity: WorkloadRuntimeIdentity
    requested_activities: tuple[WorkloadActivity | str, ...]
    authorization_effect: str = "none"

    def __post_init__(self) -> None:
        object.__setattr__(self, "requested_activities", tuple(sorted(set(self.requested_activities), key=str)))


def _plain(value: Any) -> Any:
    if isinstance(value, StrEnum):
        return value.value
    if isinstance(value, tuple):
        return [_plain(item) for item in value]
    if hasattr(value, "__dataclass_fields__"):
        return {field.name: _plain(getattr(value, field.name)) for field in fields(value)}
    return value


def canonical_linux_edge_workload_bytes(record: LinuxEdgeWorkload) -> bytes:
    """Return canonical bytes excluding its self-referential content identity."""
    payload = record.to_dict()
    payload["workload_id"] = ""
    payload["workload_content_id"] = ""
    return json.dumps(payload, ensure_ascii=True, sort_keys=True, separators=(",", ":"), allow_nan=False).encode("ascii")


def linux_edge_workload_content_id(record: LinuxEdgeWorkload) -> str:
    return "sha256:" + hashlib.sha256(canonical_linux_edge_workload_bytes(record)).hexdigest()
