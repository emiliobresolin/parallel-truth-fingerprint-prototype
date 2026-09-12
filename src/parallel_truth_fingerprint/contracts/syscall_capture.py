"""Immutable, transport-neutral contracts for captured Linux syscall evidence.

The contracts describe capture provenance only.  They never invoke a collector,
open a raw object, publish a message, or authorize formal evidence use.
"""
from __future__ import annotations

import hashlib
import json
from dataclasses import dataclass, fields
from enum import StrEnum
from typing import Any


RAW_CAPTURE_SEGMENT_VERSION = "RawCaptureSegment.v1"
SYSCALL_EVENT_BATCH_VERSION = "SyscallEventBatch.v1"
SYSCALL_TRANSPORT_PATH = "host/syscalls/v1"


class CaptureOrigin(StrEnum):
    HOST_CAPTURE = "host_capture"
    FIXTURE_REPLAY = "fixture_replay"


class SegmentOutcome(StrEnum):
    COMPLETE = "complete"
    PARTIAL = "partial"
    FAILED = "failed"
    ABORTED = "aborted"


@dataclass(frozen=True)
class QueueEvidence:
    queue_identity: str
    dropped_count: int
    duplicate_count: int
    gap_count: int
    storage_lag_count: int
    outcome: str


@dataclass(frozen=True)
class RawCaptureSegment:
    schema_version: str
    segment_id: str
    capture_origin: CaptureOrigin | str
    raw_segment_uri: str
    raw_segment_content_id: str
    byte_count: int
    event_count: int
    capture_started_at: str
    capture_ended_at: str
    collector_identity: str
    filter_identity: str
    host_or_vm_identity: str
    boot_identity: str
    kernel_identity: str
    architecture_identity: str
    workload_identity: str
    container_or_cgroup_identity: str
    process_scope_identity: str
    experiment_identity: str
    run_identity: str
    edge_identity: str
    session_identity: str
    correlation_identity: str
    source_sequence_start: int
    source_sequence_end: int
    queue_evidence: QueueEvidence
    outcome: SegmentOutcome | str
    exclusion_or_abort_reason: str | None
    test_only: bool
    segment_content_id: str
    authorization_effect: str = "none"

    def to_dict(self) -> dict[str, Any]:
        return {field.name: _plain(getattr(self, field.name)) for field in fields(self)}


@dataclass(frozen=True)
class RawEventRange:
    start_offset: int
    end_offset: int
    collector_record_offset: int | None = None


@dataclass(frozen=True)
class SyscallEvent:
    event_identity: str
    source_sequence: int
    source_timestamp: str | None
    observed_timestamp: str | None
    monotonic_timestamp: str | None
    process_identity: str
    thread_identity: str | None
    syscall_name: str
    direction: str
    abi_identity: str
    syscall_number: int | None
    canonical_name_mapping_identity: str | None
    return_value: str | None
    sanitized_arguments: tuple[tuple[str, str], ...]
    raw_event_range: RawEventRange

    def __post_init__(self) -> None:
        object.__setattr__(self, "sanitized_arguments", tuple(sorted(self.sanitized_arguments)))


@dataclass(frozen=True)
class SyscallEventBatch:
    schema_version: str
    batch_id: str
    transport_path: str
    capture_origin: CaptureOrigin | str
    raw_segment_id: str
    raw_segment_content_id: str
    run_identity: str
    edge_identity: str
    boot_identity: str
    session_identity: str
    container_or_cgroup_identity: str
    kernel_identity: str
    architecture_identity: str
    collector_identity: str
    filter_identity: str
    queue_evidence: QueueEvidence
    events: tuple[SyscallEvent, ...]
    test_only: bool
    batch_content_id: str
    authorization_effect: str = "none"

    def __post_init__(self) -> None:
        object.__setattr__(self, "events", tuple(sorted(self.events, key=lambda event: event.source_sequence)))

    def to_dict(self) -> dict[str, Any]:
        return {field.name: _plain(getattr(self, field.name)) for field in fields(self)}


def _plain(value: Any) -> Any:
    if isinstance(value, StrEnum):
        return value.value
    if isinstance(value, tuple):
        return [_plain(item) for item in value]
    if hasattr(value, "__dataclass_fields__"):
        return {field.name: _plain(getattr(value, field.name)) for field in fields(value)}
    return value


def _canonical(record: RawCaptureSegment | SyscallEventBatch, identity_field: str) -> bytes:
    payload = record.to_dict()
    payload[identity_field] = ""
    if identity_field == "segment_content_id":
        payload["segment_id"] = ""
    else:
        payload["batch_id"] = ""
    return json.dumps(payload, ensure_ascii=True, sort_keys=True, separators=(",", ":"), allow_nan=False).encode("ascii")


def raw_capture_segment_content_id(segment: RawCaptureSegment) -> str:
    return "sha256:" + hashlib.sha256(_canonical(segment, "segment_content_id")).hexdigest()


def syscall_event_batch_content_id(batch: SyscallEventBatch) -> str:
    return "sha256:" + hashlib.sha256(_canonical(batch, "batch_content_id")).hexdigest()
