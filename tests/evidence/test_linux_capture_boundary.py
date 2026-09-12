"""Offline conformance tests for Story 14.2's injected Linux-boundary gate."""
from __future__ import annotations

import unittest

from parallel_truth_fingerprint.contracts.linux_capture_boundary import (
    CaptureBoundaryDecision, CaptureBoundaryKind, CaptureEnvironment,
    CaptureMeasurement, CaptureOrigin, RawCaptureSegmentQualification,
    linux_capture_boundary_qualification_content_id,
)
from parallel_truth_fingerprint.evidence.linux_capture_boundary import (
    LinuxCaptureQualificationInput, qualify_linux_capture_boundary,
)


def digest(number: int) -> str:
    return "sha256:" + f"{number:064x}"


class LinuxCaptureBoundaryTests(unittest.TestCase):
    def environment(self) -> CaptureEnvironment:
        return CaptureEnvironment(
            CaptureBoundaryKind.LINUX_VM, *(digest(number) for number in range(10, 25))
        )

    def candidate(self, **changes: object) -> LinuxCaptureQualificationInput:
        env = self.environment()
        measurements = tuple(CaptureMeasurement(name, (digest(100 + index),), (digest(200 + index),), True)
                             for index, name in enumerate((
                                 "workload_attribution", "event_ordering", "duplicates", "gaps", "drops",
                                 "queue_behavior", "storage_lag", "capture_overhead", "raw_to_canonical_replay",
                             )))
        segment = RawCaptureSegmentQualification(
            digest(300), digest(301), CaptureOrigin.HOST_CAPTURE, env.collector_identity,
            env.filter_identity, env.host_or_vm_identity, env.boot_identity, env.kernel_identity,
            digest(30), digest(31), digest(32), digest(33), digest(34), digest(35),
        )
        values: dict[str, object] = dict(
            candidate_boundary_id=digest(1), environment=env, workload_identity=digest(30), run_identity=digest(33),
            measurements=measurements, raw_segments=(segment,), decision=CaptureBoundaryDecision.SELECTED,
            selected_boundary_id=digest(1), fallback_boundary_id=None, limitations=("Offline test fixture.",),
        )
        values.update(changes)
        return LinuxCaptureQualificationInput(**values)

    @staticmethod
    def resolve(_: str) -> bool: return True

    def qualify(self, candidate: LinuxCaptureQualificationInput):
        return qualify_linux_capture_boundary(candidate, immutable_resolver=self.resolve,
                                              parameter_evidence_resolver=self.resolve)

    def test_complete_linux_vm_capture_closure_is_qualified_and_stable(self) -> None:
        result = self.qualify(self.candidate())
        self.assertEqual("qualified", result.disposition)
        self.assertEqual(result.qualification_content_id, linux_capture_boundary_qualification_content_id(result))
        self.assertEqual("none", result.authorization_effect)

    def test_windows_host_is_never_a_linux_capture_boundary(self) -> None:
        env = self.environment()
        env = CaptureEnvironment(CaptureBoundaryKind.WINDOWS_HOST, *(getattr(env, field) for field in vars(env) if field != "boundary_kind"))
        result = self.qualify(self.candidate(environment=env))
        self.assertEqual("not_qualified", result.disposition)
        self.assertIn("LCB1_NON_LINUX_OR_UNKNOWN_BOUNDARY", {code for check in result.checks for code in check.diagnostic_codes})

    def test_missing_measurement_and_unresolved_parameter_fail_closed(self) -> None:
        result = self.qualify(self.candidate(measurements=()))
        self.assertEqual("incomplete", result.disposition)
        item = self.candidate().measurements[0]
        changed = (CaptureMeasurement(item.measurement_kind, item.evidence_ids, ("not-an-id",), True), *self.candidate().measurements[1:])
        result = self.qualify(self.candidate(measurements=changed))
        self.assertEqual("blocked", result.disposition)
        self.assertIn("LCB1_PARAMETER_EVIDENCE_UNRESOLVED", {code for check in result.checks for code in check.diagnostic_codes})

    def test_prohibited_origins_and_environment_mismatch_are_ineligible(self) -> None:
        segment = self.candidate().raw_segments[0]
        injected = RawCaptureSegmentQualification(
            segment.segment_content_id, segment.raw_bytes_hash, CaptureOrigin.INJECTED, segment.collector_identity,
            segment.filter_identity, segment.host_or_vm_identity, segment.boot_identity, segment.kernel_identity,
            segment.workload_identity, segment.cgroup_identity, segment.process_identity, segment.run_identity,
            segment.ordering_evidence_id, segment.replay_evidence_id,
        )
        result = self.qualify(self.candidate(raw_segments=(injected,)))
        self.assertEqual("not_qualified", result.disposition)
        bad_kernel = RawCaptureSegmentQualification(
            segment.segment_content_id, segment.raw_bytes_hash, segment.capture_origin, segment.collector_identity,
            segment.filter_identity, segment.host_or_vm_identity, segment.boot_identity, digest(999),
            segment.workload_identity, segment.cgroup_identity, segment.process_identity, segment.run_identity,
            segment.ordering_evidence_id, segment.replay_evidence_id,
        )
        result = self.qualify(self.candidate(raw_segments=(bad_kernel,)))
        self.assertEqual("incomplete", result.disposition)

    def test_rejected_boundary_requires_pinned_fallback_and_blocked_stays_blocked(self) -> None:
        self.assertEqual("blocked", self.qualify(self.candidate(decision=CaptureBoundaryDecision.REJECTED, selected_boundary_id=None)).disposition)
        result = self.qualify(self.candidate(decision=CaptureBoundaryDecision.BLOCKED, selected_boundary_id=None))
        self.assertEqual("blocked", result.disposition)
        self.assertIn("LCB1_CAPTURE_ACTIVITY_BLOCKED", {code for check in result.checks for code in check.diagnostic_codes})


if __name__ == "__main__":
    unittest.main()
