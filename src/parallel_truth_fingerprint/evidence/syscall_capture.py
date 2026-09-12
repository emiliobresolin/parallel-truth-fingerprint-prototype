"""Pure, fail-closed validation for raw syscall capture contracts.

Resolvers are supplied by callers.  This module does not read raw bytes, write
storage, transport a batch, or upgrade fixture provenance into formal evidence.
"""
from __future__ import annotations

import re
from dataclasses import dataclass
from typing import Callable

from parallel_truth_fingerprint.contracts.scientific_governance import is_immutable_id
from parallel_truth_fingerprint.contracts.syscall_capture import (
    CaptureOrigin, RawCaptureSegment, SegmentOutcome, SyscallEventBatch,
    SYSCALL_EVENT_BATCH_VERSION, SYSCALL_TRANSPORT_PATH,
    RAW_CAPTURE_SEGMENT_VERSION, raw_capture_segment_content_id,
    syscall_event_batch_content_id,
)


_UTC = re.compile(r"\d{4}-\d{2}-\d{2}T\d{2}:\d{2}:\d{2}(?:\.\d+)?Z\Z")
_DIRECTIONS = frozenset({"enter", "exit"})
RawSegmentResolver = Callable[[str], RawCaptureSegment | None]
RawContentResolver = Callable[[RawCaptureSegment], bool]


@dataclass(frozen=True)
class SyscallCaptureViolation:
    rule_id: str
    field: str
    detail: str


@dataclass(frozen=True)
class SyscallCaptureValidation:
    allowed: bool
    formal_eligible: bool
    violations: tuple[SyscallCaptureViolation, ...]
    authorization_effect: str = "none"


def _add(items: list[SyscallCaptureViolation], rule: str, field: str, detail: str) -> None:
    items.append(SyscallCaptureViolation(rule, field, detail))


def _timestamp(value: object) -> bool:
    return isinstance(value, str) and _UTC.fullmatch(value) is not None


def _identity_fields(record: object, names: tuple[str, ...], violations: list[SyscallCaptureViolation], rule: str) -> None:
    for name in names:
        if not is_immutable_id(getattr(record, name)):
            _add(violations, rule, name, "exact_immutable_identity_required")


def _queue(queue: object, violations: list[SyscallCaptureViolation]) -> None:
    values = (queue.dropped_count, queue.duplicate_count, queue.gap_count, queue.storage_lag_count)
    if not is_immutable_id(queue.queue_identity) or any(not isinstance(item, int) or item < 0 for item in values) or not isinstance(queue.outcome, str) or not queue.outcome:
        _add(violations, "SEC1_QUEUE_EVIDENCE_INVALID", "queue_evidence", "resolved_queue_identity_nonnegative_counts_and_outcome_required")


def validate_raw_capture_segment(segment: RawCaptureSegment) -> SyscallCaptureValidation:
    violations: list[SyscallCaptureViolation] = []
    if segment.schema_version != RAW_CAPTURE_SEGMENT_VERSION:
        _add(violations, "SEC1_SEGMENT_SCHEMA_INVALID", "schema_version", "exact_v1_schema_required")
    origin = str(segment.capture_origin)
    if origin not in {item.value for item in CaptureOrigin}:
        _add(violations, "SEC1_CAPTURE_ORIGIN_INVALID", "capture_origin", "closed_capture_origin_required")
    if segment.authorization_effect != "none":
        _add(violations, "SEC1_AUTHORIZATION_EFFECT_INVALID", "authorization_effect", "contract_must_not_authorize")
    if not isinstance(segment.raw_segment_uri, str) or not segment.raw_segment_uri.strip():
        _add(violations, "SEC1_RAW_URI_INVALID", "raw_segment_uri", "explicit_raw_object_uri_required")
    _identity_fields(segment, ("raw_segment_content_id", "collector_identity", "filter_identity", "host_or_vm_identity", "boot_identity", "kernel_identity", "architecture_identity", "workload_identity", "container_or_cgroup_identity", "process_scope_identity", "experiment_identity", "run_identity", "edge_identity", "session_identity", "correlation_identity"), violations, "SEC1_SEGMENT_IDENTITY_INVALID")
    if segment.segment_id != raw_capture_segment_content_id(segment) or segment.segment_content_id != segment.segment_id:
        _add(violations, "SEC1_SEGMENT_CONTENT_ID_INVALID", "segment_id", "canonical_self_identity_required")
    if not all(isinstance(value, int) and value >= 0 for value in (segment.byte_count, segment.event_count, segment.source_sequence_start, segment.source_sequence_end)) or segment.source_sequence_end < segment.source_sequence_start:
        _add(violations, "SEC1_SEGMENT_COUNTS_INVALID", "byte_count", "nonnegative_counts_and_ordered_source_sequence_required")
    if not _timestamp(segment.capture_started_at) or not _timestamp(segment.capture_ended_at) or segment.capture_ended_at < segment.capture_started_at:
        _add(violations, "SEC1_SEGMENT_TIME_INVALID", "capture_started_at", "ordered_canonical_capture_times_required")
    _queue(segment.queue_evidence, violations)
    if str(segment.outcome) not in {item.value for item in SegmentOutcome}:
        _add(violations, "SEC1_SEGMENT_OUTCOME_INVALID", "outcome", "closed_finalization_outcome_required")
    if str(segment.outcome) == SegmentOutcome.COMPLETE.value and segment.exclusion_or_abort_reason is not None:
        _add(violations, "SEC1_SEGMENT_OUTCOME_REASON_INVALID", "exclusion_or_abort_reason", "complete_segment_must_not_declare_abort_reason")
    if str(segment.outcome) != SegmentOutcome.COMPLETE.value and not segment.exclusion_or_abort_reason:
        _add(violations, "SEC1_SEGMENT_OUTCOME_REASON_MISSING", "exclusion_or_abort_reason", "partial_failed_or_aborted_segment_requires_explicit_reason")
    if origin == CaptureOrigin.HOST_CAPTURE.value and segment.test_only:
        _add(violations, "SEC1_HOST_CAPTURE_TEST_ONLY", "test_only", "host_capture_cannot_be_test_fixture")
    if origin == CaptureOrigin.FIXTURE_REPLAY.value and not segment.test_only:
        _add(violations, "SEC1_FIXTURE_NOT_TEST_ONLY", "test_only", "fixture_replay_must_be_test_only")
    return SyscallCaptureValidation(not violations, not violations and origin == CaptureOrigin.HOST_CAPTURE.value, tuple(violations))


def validate_syscall_event_batch(
    batch: SyscallEventBatch, *, raw_segment_resolver: RawSegmentResolver,
    raw_content_resolver: RawContentResolver | None = None,
) -> SyscallCaptureValidation:
    violations = list(validate_raw_capture_segment_result(batch, raw_segment_resolver, raw_content_resolver))
    origin = str(batch.capture_origin)
    if batch.schema_version != SYSCALL_EVENT_BATCH_VERSION:
        _add(violations, "SEC1_BATCH_SCHEMA_INVALID", "schema_version", "exact_v1_schema_required")
    if batch.transport_path != SYSCALL_TRANSPORT_PATH:
        _add(violations, "SEC1_TRANSPORT_PATH_INVALID", "transport_path", "separate_host_syscalls_v1_path_required")
    if batch.authorization_effect != "none":
        _add(violations, "SEC1_BATCH_AUTHORIZATION_EFFECT_INVALID", "authorization_effect", "contract_must_not_authorize")
    _identity_fields(batch, ("raw_segment_id", "raw_segment_content_id", "run_identity", "edge_identity", "boot_identity", "session_identity", "container_or_cgroup_identity", "kernel_identity", "architecture_identity", "collector_identity", "filter_identity"), violations, "SEC1_BATCH_IDENTITY_INVALID")
    if batch.batch_id != syscall_event_batch_content_id(batch) or batch.batch_content_id != batch.batch_id:
        _add(violations, "SEC1_BATCH_CONTENT_ID_INVALID", "batch_id", "canonical_self_identity_required")
    _queue(batch.queue_evidence, violations)
    if not batch.events:
        _add(violations, "SEC1_BATCH_EVENTS_EMPTY", "events", "at_least_one_captured_event_required")
    seen_events: set[str] = set(); previous_sequence: int | None = None; previous_end = -1
    for event in batch.events:
        if not is_immutable_id(event.event_identity) or event.event_identity in seen_events:
            _add(violations, "SEC1_EVENT_IDENTITY_INVALID", "events", "unique_immutable_event_identity_required")
        seen_events.add(event.event_identity)
        if not isinstance(event.source_sequence, int) or (previous_sequence is not None and event.source_sequence <= previous_sequence):
            _add(violations, "SEC1_EVENT_SEQUENCE_INVALID", "events", "strictly_ordered_source_sequence_required")
        previous_sequence = event.source_sequence
        if any(value is not None and not _timestamp(value) for value in (event.source_timestamp, event.observed_timestamp, event.monotonic_timestamp)):
            _add(violations, "SEC1_EVENT_TIME_INVALID", "events", "timestamps_must_be_canonical_when_available")
        if not is_immutable_id(event.process_identity) or (event.thread_identity is not None and not is_immutable_id(event.thread_identity)):
            _add(violations, "SEC1_EVENT_PROCESS_IDENTITY_INVALID", "events", "immutable_process_and_thread_identity_required")
        if not isinstance(event.syscall_name, str) or not event.syscall_name or str(event.direction) not in _DIRECTIONS or not is_immutable_id(event.abi_identity):
            _add(violations, "SEC1_EVENT_CATEGORICAL_CONTEXT_INVALID", "events", "categorical_name_direction_and_abi_required")
        if event.syscall_number is not None and (not isinstance(event.syscall_number, int) or not is_immutable_id(event.canonical_name_mapping_identity)):
            _add(violations, "SEC1_SYSCALL_NUMBER_CONTEXT_INVALID", "events", "numeric_identifier_requires_exact_abi_name_mapping")
        rng = event.raw_event_range
        if not isinstance(rng.start_offset, int) or not isinstance(rng.end_offset, int) or rng.start_offset < 0 or rng.end_offset <= rng.start_offset or rng.start_offset < previous_end:
            _add(violations, "SEC1_RAW_EVENT_RANGE_INVALID", "events", "ordered_nonoverlapping_raw_ranges_required")
        previous_end = max(previous_end, rng.end_offset if isinstance(rng.end_offset, int) else previous_end)
        if rng.collector_record_offset is not None and (not isinstance(rng.collector_record_offset, int) or rng.collector_record_offset < 0):
            _add(violations, "SEC1_COLLECTOR_OFFSET_INVALID", "events", "nonnegative_collector_offset_required")
    formal = not violations and origin == CaptureOrigin.HOST_CAPTURE.value and not batch.test_only
    return SyscallCaptureValidation(not violations, formal, tuple(violations))


def validate_raw_capture_segment_result(
    batch: SyscallEventBatch, resolver: RawSegmentResolver,
    raw_content_resolver: RawContentResolver | None = None,
) -> tuple[SyscallCaptureViolation, ...]:
    """Resolve and compare the declared segment; unavailable evidence stays explicit."""
    violations: list[SyscallCaptureViolation] = []
    segment = resolver(batch.raw_segment_id) if is_immutable_id(batch.raw_segment_id) else None
    if segment is None:
        _add(violations, "SEC1_RAW_SEGMENT_UNRESOLVED", "raw_segment_id", "declared_immutable_raw_segment_required")
        return tuple(violations)
    violations.extend(validate_raw_capture_segment(segment).violations)
    if batch.raw_segment_content_id != segment.raw_segment_content_id or str(batch.capture_origin) != str(segment.capture_origin):
        _add(violations, "SEC1_RAW_SEGMENT_BINDING_MISMATCH", "raw_segment_content_id", "batch_must_bind_declared_segment_and_origin")
    for field in ("run_identity", "edge_identity", "boot_identity", "session_identity", "container_or_cgroup_identity", "kernel_identity", "architecture_identity", "collector_identity", "filter_identity"):
        source = "container_or_cgroup_identity" if field == "container_or_cgroup_identity" else field
        if getattr(batch, field) != getattr(segment, source):
            _add(violations, "SEC1_SEGMENT_PROVENANCE_MISMATCH", field, "batch_provenance_must_match_raw_segment")
    for event in batch.events:
        event_range = event.raw_event_range
        if not isinstance(event_range.end_offset, int) or event_range.end_offset > segment.byte_count:
            _add(violations, "SEC1_RAW_EVENT_RANGE_UNMAPPED", "events", "event_range_must_resolve_inside_declared_raw_segment")
        if (not isinstance(event.source_sequence, int)
                or event.source_sequence < segment.source_sequence_start
                or event.source_sequence > segment.source_sequence_end):
            _add(violations, "SEC1_EVENT_SEQUENCE_OUTSIDE_SEGMENT", "events", "event_sequence_must_resolve_to_declared_segment")
    if str(batch.capture_origin) == CaptureOrigin.HOST_CAPTURE.value:
        if raw_content_resolver is None or not raw_content_resolver(segment):
            _add(violations, "SEC1_RAW_CONTENT_UNVERIFIED", "raw_segment_content_id", "formal_host_capture_requires_verified_immutable_raw_bytes")
    if str(batch.capture_origin) == CaptureOrigin.FIXTURE_REPLAY.value and not batch.test_only:
        _add(violations, "SEC1_BATCH_FIXTURE_NOT_TEST_ONLY", "test_only", "fixture_batch_must_remain_test_only")
    if str(batch.capture_origin) == CaptureOrigin.HOST_CAPTURE.value and batch.test_only:
        _add(violations, "SEC1_BATCH_HOST_CAPTURE_TEST_ONLY", "test_only", "host_capture_batch_cannot_be_fixture")
    return tuple(violations)
