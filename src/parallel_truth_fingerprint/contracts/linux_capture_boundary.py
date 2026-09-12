"""Immutable, non-executing qualification record for a Linux capture boundary.

This contract records facts supplied by a collector qualification spike.  It
does not invoke Sysdig/eBPF, start a workload, read raw bytes, publish an
object, or authorize host capture.
"""
from __future__ import annotations

import hashlib
import json
from dataclasses import dataclass, fields
from enum import StrEnum
from typing import Any


LINUX_CAPTURE_BOUNDARY_QUALIFICATION_VERSION = "LinuxCaptureBoundaryQualification.v1"


class CaptureOrigin(StrEnum):
    HOST_CAPTURE = "host_capture"
    FIXTURE_REPLAY = "fixture_replay"
    INJECTED = "injected"
    GENERATED = "generated"
    REPLAYED = "replayed"
    EXTERNAL_DATASET = "external_dataset"
    UNKNOWN = "unknown"


class CaptureBoundaryKind(StrEnum):
    LINUX_HOST = "linux_host"
    LINUX_VM = "linux_vm"
    WINDOWS_HOST = "windows_host"
    UNKNOWN = "unknown"


class CaptureBoundaryDecision(StrEnum):
    SELECTED = "selected"
    REJECTED = "rejected"
    BLOCKED = "blocked"


class CaptureCheckDisposition(StrEnum):
    PASS = "pass"
    FAIL = "fail"
    BLOCKED = "blocked"
    INCOMPLETE = "incomplete"


class CaptureQualificationDisposition(StrEnum):
    QUALIFIED = "qualified"
    NOT_QUALIFIED = "not_qualified"
    BLOCKED = "blocked"
    INCOMPLETE = "incomplete"


@dataclass(frozen=True)
class CaptureEnvironment:
    """Opaque identities of the actual observed Linux boundary."""
    boundary_kind: CaptureBoundaryKind | str
    host_or_vm_identity: str
    boot_identity: str
    kernel_identity: str
    architecture_identity: str
    container_runtime_identity: str
    collector_identity: str
    collector_version_identity: str
    capture_mode_identity: str
    filter_identity: str
    buffer_identity: str
    queue_identity: str
    compression_identity: str
    storage_identity: str
    resource_identity: str
    code_runtime_identity: str


@dataclass(frozen=True)
class CaptureMeasurement:
    """A measured/replay fact and its immutable evidence closure."""
    measurement_kind: str
    evidence_ids: tuple[str, ...]
    parameter_evidence_ids: tuple[str, ...] = ()
    passed: bool | None = None

    def __post_init__(self) -> None:
        object.__setattr__(self, "evidence_ids", tuple(sorted(set(self.evidence_ids))))
        object.__setattr__(self, "parameter_evidence_ids", tuple(sorted(set(self.parameter_evidence_ids))))


@dataclass(frozen=True)
class RawCaptureSegmentQualification:
    """Identity-only provenance for one immutable segment from a spike."""
    segment_content_id: str
    raw_bytes_hash: str
    capture_origin: CaptureOrigin | str
    collector_identity: str
    filter_identity: str
    host_or_vm_identity: str
    boot_identity: str
    kernel_identity: str
    workload_identity: str
    cgroup_identity: str
    process_identity: str
    run_identity: str
    ordering_evidence_id: str
    replay_evidence_id: str


@dataclass(frozen=True)
class CaptureQualificationCheck:
    check_id: str
    disposition: CaptureCheckDisposition | str
    affected_ids: tuple[str, ...] = ()
    diagnostic_codes: tuple[str, ...] = ()

    def __post_init__(self) -> None:
        object.__setattr__(self, "affected_ids", tuple(sorted(set(self.affected_ids))))
        object.__setattr__(self, "diagnostic_codes", tuple(sorted(set(self.diagnostic_codes))))


@dataclass(frozen=True)
class LinuxCaptureBoundaryQualification:
    """Public, immutable result of an injected qualification assessment."""
    schema_version: str
    candidate_boundary_id: str
    environment: CaptureEnvironment
    workload_identity: str
    run_identity: str
    measurements: tuple[CaptureMeasurement, ...]
    raw_segments: tuple[RawCaptureSegmentQualification, ...]
    decision: CaptureBoundaryDecision | str
    selected_boundary_id: str | None
    fallback_boundary_id: str | None
    checks: tuple[CaptureQualificationCheck, ...]
    disposition: CaptureQualificationDisposition | str
    limitations: tuple[str, ...]
    qualification_content_id: str
    authorization_effect: str = "none"

    def __post_init__(self) -> None:
        object.__setattr__(self, "measurements", tuple(sorted(self.measurements, key=lambda item: item.measurement_kind)))
        object.__setattr__(self, "raw_segments", tuple(sorted(self.raw_segments, key=lambda item: item.segment_content_id)))
        object.__setattr__(self, "checks", tuple(sorted(self.checks, key=lambda item: item.check_id)))
        object.__setattr__(self, "limitations", tuple(sorted(set(self.limitations))))

    def to_dict(self) -> dict[str, Any]:
        def plain(value: Any) -> Any:
            if isinstance(value, StrEnum): return value.value
            if isinstance(value, tuple): return [plain(item) for item in value]
            if hasattr(value, "__dataclass_fields__"):
                return {field.name: plain(getattr(value, field.name)) for field in fields(value)}
            return value
        return {field.name: plain(getattr(self, field.name)) for field in fields(self)}


def canonical_linux_capture_boundary_qualification_bytes(record: LinuxCaptureBoundaryQualification) -> bytes:
    payload = record.to_dict()
    payload.pop("qualification_content_id", None)
    return json.dumps(payload, ensure_ascii=True, sort_keys=True, separators=(",", ":"), allow_nan=False).encode("ascii")


def linux_capture_boundary_qualification_content_id(record: LinuxCaptureBoundaryQualification) -> str:
    return "sha256:" + hashlib.sha256(canonical_linux_capture_boundary_qualification_bytes(record)).hexdigest()
