"""Offline contract tests for Story 14.3 syscall capture provenance."""
from __future__ import annotations

from dataclasses import replace
import unittest

from parallel_truth_fingerprint.contracts.syscall_capture import (
    CaptureOrigin, QueueEvidence, RawCaptureSegment, RawEventRange,
    SegmentOutcome, SyscallEvent, SyscallEventBatch, raw_capture_segment_content_id,
    syscall_event_batch_content_id,
)
from parallel_truth_fingerprint.evidence.syscall_capture import (
    validate_raw_capture_segment, validate_syscall_event_batch,
)


def digest(number: int) -> str:
    return "sha256:" + f"{number:064x}"


def queue() -> QueueEvidence:
    return QueueEvidence(digest(1), 0, 0, 0, 0, "drained")


def segment(**changes: object) -> RawCaptureSegment:
    values: dict[str, object] = dict(
        schema_version="RawCaptureSegment.v1", segment_id="", capture_origin=CaptureOrigin.HOST_CAPTURE,
        raw_segment_uri="object://captures/segment-a", raw_segment_content_id=digest(2), byte_count=100,
        event_count=2, capture_started_at="2026-08-01T00:00:00Z", capture_ended_at="2026-08-01T00:00:01Z",
        collector_identity=digest(3), filter_identity=digest(4), host_or_vm_identity=digest(5), boot_identity=digest(6),
        kernel_identity=digest(7), architecture_identity=digest(8), workload_identity=digest(9),
        container_or_cgroup_identity=digest(10), process_scope_identity=digest(11), experiment_identity=digest(12),
        run_identity=digest(13), edge_identity=digest(14), session_identity=digest(15), correlation_identity=digest(16),
        source_sequence_start=10, source_sequence_end=11, queue_evidence=queue(), outcome=SegmentOutcome.COMPLETE,
        exclusion_or_abort_reason=None, test_only=False, segment_content_id="",
    )
    values.update(changes)
    item = RawCaptureSegment(**values)
    content_id = raw_capture_segment_content_id(item)
    return replace(item, segment_id=content_id, segment_content_id=content_id)


def event(number: int, sequence: int, start: int, end: int) -> SyscallEvent:
    return SyscallEvent(digest(number), sequence, "2026-08-01T00:00:00Z", None, None, digest(number + 30), digest(number + 40),
                        "read", "enter", digest(number + 50), 0, digest(number + 60), "0", (("fd", "redacted"),), RawEventRange(start, end, start))


def batch(raw: RawCaptureSegment, **changes: object) -> SyscallEventBatch:
    values: dict[str, object] = dict(
        schema_version="SyscallEventBatch.v1", batch_id="", transport_path="host/syscalls/v1", capture_origin=CaptureOrigin.HOST_CAPTURE,
        raw_segment_id=raw.segment_id, raw_segment_content_id=raw.raw_segment_content_id, run_identity=raw.run_identity,
        edge_identity=raw.edge_identity, boot_identity=raw.boot_identity, session_identity=raw.session_identity,
        container_or_cgroup_identity=raw.container_or_cgroup_identity, kernel_identity=raw.kernel_identity,
        architecture_identity=raw.architecture_identity, collector_identity=raw.collector_identity, filter_identity=raw.filter_identity,
        queue_evidence=queue(), events=(event(100, 10, 0, 10), event(101, 11, 10, 20)), test_only=False, batch_content_id="",
    )
    values.update(changes)
    item = SyscallEventBatch(**values)
    content_id = syscall_event_batch_content_id(item)
    return replace(item, batch_id=content_id, batch_content_id=content_id)


class SyscallCaptureTests(unittest.TestCase):
    @staticmethod
    def raw_bytes_verified(_: RawCaptureSegment) -> bool:
        return True

    def test_host_capture_segment_and_batch_are_formally_eligible(self) -> None:
        raw = segment(); result = validate_syscall_event_batch(batch(raw), raw_segment_resolver=lambda _: raw, raw_content_resolver=self.raw_bytes_verified)
        self.assertTrue(validate_raw_capture_segment(raw).allowed)
        self.assertTrue(result.allowed); self.assertTrue(result.formal_eligible)

    def test_partial_segment_remains_explicit(self) -> None:
        raw = segment(outcome=SegmentOutcome.PARTIAL, exclusion_or_abort_reason="collector_closed")
        self.assertTrue(validate_raw_capture_segment(raw).allowed)

    def test_fixture_replay_can_never_be_formal_or_host_capture(self) -> None:
        raw = segment(capture_origin=CaptureOrigin.FIXTURE_REPLAY, test_only=True)
        item = batch(raw, capture_origin=CaptureOrigin.FIXTURE_REPLAY, test_only=True)
        result = validate_syscall_event_batch(item, raw_segment_resolver=lambda _: raw)
        self.assertTrue(result.allowed); self.assertFalse(result.formal_eligible)
        forged = batch(raw, capture_origin=CaptureOrigin.HOST_CAPTURE, test_only=False)
        self.assertIn("SEC1_RAW_SEGMENT_BINDING_MISMATCH", {v.rule_id for v in validate_syscall_event_batch(forged, raw_segment_resolver=lambda _: raw, raw_content_resolver=self.raw_bytes_verified).violations})

    def test_forbidden_route_and_unmapped_or_overlapping_events_fail_closed(self) -> None:
        raw = segment()
        overlap = (event(100, 10, 0, 20), event(101, 11, 10, 120))
        item = batch(raw, transport_path="physical/consensus/v1", events=overlap)
        codes = {v.rule_id for v in validate_syscall_event_batch(item, raw_segment_resolver=lambda _: raw, raw_content_resolver=self.raw_bytes_verified).violations}
        self.assertTrue({"SEC1_TRANSPORT_PATH_INVALID", "SEC1_RAW_EVENT_RANGE_INVALID", "SEC1_RAW_EVENT_RANGE_UNMAPPED"}.issubset(codes))

    def test_missing_segment_numeric_mapping_and_provenance_break_are_rejected(self) -> None:
        raw = segment(); broken_event = replace(event(100, 10, 0, 10), canonical_name_mapping_identity=None)
        item = batch(raw, events=(broken_event,), run_identity=digest(999))
        codes = {v.rule_id for v in validate_syscall_event_batch(item, raw_segment_resolver=lambda _: raw, raw_content_resolver=self.raw_bytes_verified).violations}
        self.assertTrue({"SEC1_SYSCALL_NUMBER_CONTEXT_INVALID", "SEC1_SEGMENT_PROVENANCE_MISMATCH"}.issubset(codes))
        missing = validate_syscall_event_batch(batch(raw), raw_segment_resolver=lambda _: None)
        self.assertIn("SEC1_RAW_SEGMENT_UNRESOLVED", {v.rule_id for v in missing.violations})

    def test_host_capture_without_verified_raw_bytes_is_not_formal_evidence(self) -> None:
        raw = segment()
        result = validate_syscall_event_batch(batch(raw), raw_segment_resolver=lambda _: raw)
        self.assertFalse(result.allowed); self.assertFalse(result.formal_eligible)
        self.assertIn("SEC1_RAW_CONTENT_UNVERIFIED", {v.rule_id for v in result.violations})


if __name__ == "__main__":
    unittest.main()
