"""Offline guardrail tests for Story 13.2 physical partitioning."""
from __future__ import annotations

import unittest

from parallel_truth_fingerprint.evidence.physical_partitions import (
    PhysicalObservation, PhysicalPartition, PhysicalPartitionMember,
    PhysicalPartitionRole, PreprocessingFit, WindowParameters,
    build_physical_windows, validate_frozen_preprocessing_application,
    validate_physical_partition, validate_preprocessing_fit,
)


def digest(number: int) -> str:
    return "sha256:" + f"{number:064x}"


class PhysicalPartitionTests(unittest.TestCase):
    def resolve(self, identity: str) -> bool:
        return identity != digest(999)

    def partition(self, **changes: object) -> PhysicalPartition:
        values: dict[str, object] = {
            "partition_id": digest(1), "feature_schema_id": digest(2),
            "parameter_evidence_ids": (digest(3),),
            "members": (
                PhysicalPartitionMember(digest(10), PhysicalPartitionRole.TRAIN, True, digest(11)),
                PhysicalPartitionMember(digest(12), PhysicalPartitionRole.VALIDATION, False, digest(13)),
                PhysicalPartitionMember(digest(14), PhysicalPartitionRole.CALIBRATION, False, digest(15)),
                PhysicalPartitionMember(digest(16), PhysicalPartitionRole.TEST, False, digest(17)),
            ),
        }
        values.update(changes)
        return PhysicalPartition(**values)

    def observations(self, **changes: object) -> tuple[PhysicalObservation, ...]:
        values = {"run_id": digest(10), "experiment_id": digest(20), "phase_id": digest(21),
                  "scenario_id": digest(22), "profile_id": digest(23), "schema_id": digest(2),
                  "partition_id": digest(1), "valid": True, "gap_before": False, "quality_id": digest(24)}
        values.update(changes)
        return tuple(PhysicalObservation(observation_id=digest(100 + index), sequence=index, **values) for index in range(1, 5))

    def parameters(self) -> WindowParameters:
        return WindowParameters(digest(30), 2, 1, "none", digest(31))

    def fit(self) -> PreprocessingFit:
        return PreprocessingFit(digest(40), digest(1), (digest(10),), digest(2), digest(23),
                                ("feature.a", "feature.b"), digest(41), digest(42), (digest(43),), digest(44))

    def test_independent_runs_are_assigned_exactly_once(self) -> None:
        self.assertTrue(validate_physical_partition(self.partition(), immutable_resolver=self.resolve).accepted)
        overlapping = self.partition(members=(
            PhysicalPartitionMember(digest(10), "train", True, digest(11)),
            PhysicalPartitionMember(digest(10), "test", False, digest(11)),
        ))
        result = validate_physical_partition(overlapping, immutable_resolver=self.resolve)
        self.assertFalse(result.accepted)
        self.assertIn("PPV1_RUN_ROLE_OVERLAP", {item.code for item in result.diagnostics})

    def test_windows_preserve_lineage_but_exclude_scenario_and_labels(self) -> None:
        output = build_physical_windows(partition=self.partition(), observations=self.observations(),
                                        parameters=self.parameters(), preprocessing_id=digest(40), immutable_resolver=self.resolve)
        self.assertIsInstance(output, tuple)
        assert isinstance(output, tuple)
        self.assertEqual(3, len(output))
        self.assertEqual((digest(101), digest(102)), output[0].observation_ids)
        self.assertFalse(hasattr(output[0], "scenario_id"))
        self.assertFalse(hasattr(output[0], "label"))

    def test_gap_boundary_invalid_interval_and_partition_mismatch_reject(self) -> None:
        gapped = list(self.observations())
        gapped[1] = PhysicalObservation(**{**gapped[1].__dict__, "gap_before": True})
        result = build_physical_windows(partition=self.partition(), observations=gapped, parameters=self.parameters(), preprocessing_id=digest(40), immutable_resolver=self.resolve)
        self.assertFalse(isinstance(result, tuple))
        self.assertIn("PPV1_WINDOW_BOUNDARY_CROSSING", {item.code for item in result.diagnostics})
        invalid = self.observations(valid=False)
        result = build_physical_windows(partition=self.partition(), observations=invalid, parameters=self.parameters(), preprocessing_id=digest(40), immutable_resolver=self.resolve)
        self.assertIn("PPV1_INVALID_OBSERVATION", {item.code for item in result.diagnostics})

    def test_unevidenced_padding_and_reference_fail_closed(self) -> None:
        bad = WindowParameters(digest(30), 2, 1, "zero", digest(31))
        result = build_physical_windows(partition=self.partition(), observations=self.observations(), parameters=bad, preprocessing_id=digest(999), immutable_resolver=self.resolve)
        self.assertFalse(isinstance(result, tuple))
        self.assertEqual({"PPV1_WINDOW_PARAMETERS_INVALID", "PPV1_WINDOW_REFERENCE_UNRESOLVED"}, {item.code for item in result.diagnostics})

    def test_fit_uses_exactly_all_normal_training_runs(self) -> None:
        self.assertTrue(validate_preprocessing_fit(self.fit(), partition=self.partition(), immutable_resolver=self.resolve).accepted)
        improper = PreprocessingFit(**{**self.fit().__dict__, "training_run_ids": (digest(10), digest(12))})
        result = validate_preprocessing_fit(improper, partition=self.partition(), immutable_resolver=self.resolve)
        self.assertFalse(result.accepted)
        self.assertIn("PPV1_FIT_TRAINING_CLOSURE_INVALID", {item.code for item in result.diagnostics})

    def test_frozen_application_never_refits_or_accepts_identity_mismatch(self) -> None:
        valid = validate_frozen_preprocessing_application(fit=self.fit(), partition=self.partition(), role="test",
            schema_id=digest(2), profile_id=digest(23), feature_order=("feature.a", "feature.b"), missingness_policy_id=digest(41), output_hash=digest(44), immutable_resolver=self.resolve)
        self.assertTrue(valid.accepted)
        mismatch = validate_frozen_preprocessing_application(fit=self.fit(), partition=self.partition(), role="train",
            schema_id=digest(2), profile_id=digest(23), feature_order=("feature.b", "feature.a"), missingness_policy_id=digest(41), output_hash=digest(44), immutable_resolver=self.resolve)
        self.assertFalse(mismatch.accepted)
        self.assertEqual({"PPV1_APPLY_ROLE_INVALID", "PPV1_FROZEN_PREPROCESSING_MISMATCH"}, {item.code for item in mismatch.diagnostics})


if __name__ == "__main__":
    unittest.main()
