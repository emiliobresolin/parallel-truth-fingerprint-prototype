"""Offline contract tests for Story 14.4 categorical syscall preparation."""
from __future__ import annotations

import unittest
from dataclasses import replace

from parallel_truth_fingerprint.evidence.syscall_partitions import (
    CategoricalSyscallEvent, SyscallPartition, SyscallPartitionMember,
    SyscallPartitionRole, SyscallPreprocessingFit, SyscallWindowParameters,
    build_syscall_windows, canonicalize_categorical_syscalls,
    validate_syscall_partition, validate_syscall_preprocessing_fit,
)


def digest(number: int) -> str:
    return "sha256:" + f"{number:064x}"


class SyscallPartitionTests(unittest.TestCase):
    def resolve(self, identity: str) -> bool:
        return identity != digest(999)

    def partition(self, **changes: object) -> SyscallPartition:
        values: dict[str, object] = {
            "partition_id": digest(1), "feature_schema_id": digest(2), "parameter_evidence_ids": (digest(3),),
            "members": (
                SyscallPartitionMember(digest(10), SyscallPartitionRole.TRAIN, True, digest(11), digest(12), digest(13), digest(14), digest(15), digest(16), (digest(17),)),
                SyscallPartitionMember(digest(20), SyscallPartitionRole.VALIDATION, False, digest(21), digest(22), digest(23), digest(24), digest(25), digest(26), (digest(27),)),
            ),
        }
        values.update(changes)
        return SyscallPartition(**values)

    def events(self, **changes: object) -> tuple[CategoricalSyscallEvent, ...]:
        values: dict[str, object] = {
            "batch_id": digest(17), "raw_segment_id": digest(30), "run_id": digest(10), "boot_id": digest(12),
            "session_id": digest(13), "container_id": digest(14), "process_scope_id": digest(15), "capture_group_id": digest(16),
            "collector_id": digest(31), "filter_id": digest(32), "kernel_id": digest(33), "abi_id": digest(34),
            "schema_id": digest(2), "partition_id": digest(1), "source_identity": digest(35), "categorical_name": "openat",
            "direction": "enter", "timestamp": "2026-01-01T00:00:00Z", "gap_before": False, "loss_boundary_before": False,
            "duplicate": False, "queue_pressure": False, "quality_id": digest(36), "exclusion_policy_id": digest(37),
        }
        values.update(changes)
        return tuple(CategoricalSyscallEvent(event_id=digest(100 + sequence), sequence=sequence, **values) for sequence in range(1, 5))

    def parameters(self) -> SyscallWindowParameters:
        return SyscallWindowParameters(digest(40), 2, 1, "none", digest(37), digest(41))

    def fit(self) -> SyscallPreprocessingFit:
        return SyscallPreprocessingFit(digest(50), digest(1), (digest(10),), (digest(101), digest(102)), digest(2), digest(51), digest(52), digest(53), digest(54), digest(55), (digest(56),), digest(57), digest(58))

    def test_partition_requires_one_role_per_capture_group(self) -> None:
        self.assertTrue(validate_syscall_partition(self.partition(), immutable_resolver=self.resolve).accepted)
        overlap = replace(self.partition().members[1], capture_group_id=digest(16))
        result = validate_syscall_partition(self.partition(members=(self.partition().members[0], overlap)), immutable_resolver=self.resolve)
        self.assertIn("SPV1_CAPTURE_GROUP_ROLE_OVERLAP", {item.code for item in result.diagnostics})

    def test_canonicalization_keeps_unknown_names_explicit_and_rejects_ambiguity(self) -> None:
        rows = self.events(categorical_name="unknown:collector-value")
        output = canonicalize_categorical_syscalls(rows, immutable_resolver=self.resolve)
        self.assertIsInstance(output, tuple)
        assert isinstance(output, tuple)
        self.assertEqual("unknown:collector-value", output[0].categorical_name)
        ambiguous = canonicalize_categorical_syscalls((rows[0], replace(rows[1], sequence=1)), immutable_resolver=self.resolve)
        self.assertIn("SPV1_EVENT_DUPLICATE_OR_AMBIGUOUS", {item.code for item in ambiguous.diagnostics})

    def test_windows_preserve_lineage_and_reject_any_boundary_crossing(self) -> None:
        output = build_syscall_windows(partition=self.partition(), events=self.events(), parameters=self.parameters(), preprocessing_id=digest(50), immutable_resolver=self.resolve)
        self.assertIsInstance(output, tuple)
        assert isinstance(output, tuple)
        self.assertEqual(3, len(output))
        self.assertEqual((digest(101), digest(102)), output[0].event_ids)
        self.assertFalse(hasattr(output[0], "scenario_id"))
        blocked = build_syscall_windows(partition=self.partition(), events=self.events(loss_boundary_before=True), parameters=self.parameters(), preprocessing_id=digest(50), immutable_resolver=self.resolve)
        self.assertIn("SPV1_WINDOW_BOUNDARY_CROSSING", {item.code for item in blocked.diagnostics})

    def test_window_parameters_and_scope_mismatch_fail_closed(self) -> None:
        bad = SyscallWindowParameters(digest(40), 2, 1, "zero", digest(37), digest(41))
        result = build_syscall_windows(partition=self.partition(), events=self.events(container_id=digest(999)), parameters=bad, preprocessing_id=digest(999), immutable_resolver=self.resolve)
        codes = {item.code for item in result.diagnostics}
        self.assertTrue({"SPV1_WINDOW_PARAMETERS_INVALID", "SPV1_WINDOW_REFERENCE_UNRESOLVED", "SPV1_EVENT_REFERENCE_UNRESOLVED"} <= codes)

    def test_fit_is_exactly_normal_training_only_and_immutable(self) -> None:
        self.assertTrue(validate_syscall_preprocessing_fit(self.fit(), partition=self.partition(), immutable_resolver=self.resolve).accepted)
        improper = replace(self.fit(), training_run_ids=(digest(10), digest(20)))
        result = validate_syscall_preprocessing_fit(improper, partition=self.partition(), immutable_resolver=self.resolve)
        self.assertIn("SPV1_FIT_TRAINING_CLOSURE_INVALID", {item.code for item in result.diagnostics})


if __name__ == "__main__":
    unittest.main()
