"""Unit tests for the thesis-grade statistical evaluation primitives."""

from __future__ import annotations

import math
import unittest

from parallel_truth_fingerprint.lstm_service.offline_training.academic_metrics import (
    aggregate_repeated_estimates,
    binary_operating_metrics,
    bootstrap_confidence_intervals,
    calibrate_threshold,
    curve_points,
    derive_repetition_count,
    event_metrics,
    holm_adjust,
    paired_comparison,
    per_class_detection_metrics,
    ranking_metrics,
    score_distribution,
)


class ThresholdCalibrationTests(unittest.TestCase):
    def test_sensitivity_grid_is_configurable_and_bound_to_identity(self) -> None:
        first = calibrate_threshold(
            [0.1, 0.2, 0.3, 0.4],
            [0, 0, 0, 0],
            method="target-fpr",
            target_fpr=0.25,
            sensitivity_quantiles=(0.8, 0.9),
        )
        changed = calibrate_threshold(
            [0.1, 0.2, 0.3, 0.4],
            [0, 0, 0, 0],
            method="target-fpr",
            target_fpr=0.25,
            sensitivity_quantiles=(0.8, 0.95),
        )

        self.assertEqual(
            [row["normal_quantile"] for row in first.sensitivity], [0.8, 0.9]
        )
        self.assertNotEqual(first.identity, changed.identity)

    def test_sensitivity_grid_rejects_duplicates_and_boundaries(self) -> None:
        for values in ((0.9, 0.9), (0.0, 0.9), (0.9, 1.0), ()):
            with self.subTest(values=values):
                with self.assertRaisesRegex(ValueError, "sensitivity_quantiles"):
                    calibrate_threshold(
                        [0.1, 0.2],
                        [0, 0],
                        method="target-fpr",
                        sensitivity_quantiles=values,
                    )

    def test_target_fpr_selects_most_sensitive_attainable_threshold(self) -> None:
        calibration = calibrate_threshold(
            [0.0, 1.0, 2.0, 3.0],
            [0, 0, 0, 0],
            method="target-fpr",
            target_fpr=0.25,
        )

        self.assertEqual(calibration.value, 2.5)
        self.assertEqual(calibration.objective_name, "attained_validation_normal_fpr")
        self.assertEqual(calibration.objective_value, 0.25)
        self.assertEqual(calibration.validation_support, {"total": 4, "normal": 4, "attack": 0})
        self.assertEqual(calibration.direction, "higher-is-more-anomalous")

    def test_calibration_identity_is_deterministic_and_data_bound(self) -> None:
        first = calibrate_threshold([0.1, 0.2, 0.3], [0, 0, 0], method="normal-quantile")
        repeated = calibrate_threshold([0.1, 0.2, 0.3], [0, 0, 0], method="normal-quantile")
        changed = calibrate_threshold([0.1, 0.2, 0.4], [0, 0, 0], method="normal-quantile")

        self.assertEqual(first.identity, repeated.identity)
        self.assertNotEqual(first.identity, changed.identity)
        self.assertTrue(first.identity.startswith("sha256:"))
        self.assertEqual(len(first.sensitivity), 5)

    def test_max_f1_requires_validation_attacks(self) -> None:
        with self.assertRaisesRegex(ValueError, "requires validation attacks"):
            calibrate_threshold([0.1, 0.2], [0, 0], method="max-f1")

    def test_calibration_rejects_invalid_support_and_parameters(self) -> None:
        cases = (
            (([0.1], [1]), {"method": "target-fpr"}, "normal units"),
            (([0.1], [0]), {"method": "target-fpr", "target_fpr": 0.0}, "target_fpr"),
            (([0.1], [0]), {"method": "normal-quantile", "quantile": 1.0}, "quantile"),
            (([0.1], [0]), {"method": "unknown"}, "Unsupported"),
        )
        for arguments, keywords, message in cases:
            with self.subTest(keywords=keywords):
                with self.assertRaisesRegex(ValueError, message):
                    calibrate_threshold(*arguments, **keywords)


class OperatingAndRankingMetricTests(unittest.TestCase):
    def test_binary_operating_metrics_are_reconstructible(self) -> None:
        result = binary_operating_metrics(
            [0.9, 0.8, 0.7, 0.1, 0.2, 0.6],
            [1, 0, 1, 0, 1, 0],
            threshold=0.5,
        )

        self.assertEqual(result["confusion_matrix"], {"tn": 1, "fp": 2, "fn": 1, "tp": 2})
        self.assertAlmostEqual(result["accuracy"], 0.5)
        self.assertAlmostEqual(result["precision"], 0.5)
        self.assertAlmostEqual(result["recall"], 2 / 3)
        self.assertAlmostEqual(result["specificity"], 1 / 3)
        self.assertAlmostEqual(result["f1"], 4 / 7)
        self.assertAlmostEqual(result["balanced_accuracy"], 0.5)
        self.assertAlmostEqual(result["mcc"], 0.0)
        self.assertEqual(result["undefined"], {})

    def test_undefined_precision_and_f1_are_none_not_synthetic_zeroes(self) -> None:
        result = binary_operating_metrics([0.1, 0.2, 0.3], [0, 1, 1], threshold=1.0)

        self.assertIsNone(result["precision"])
        self.assertIsNone(result["f1"])
        self.assertIn("precision", result["undefined"])
        self.assertIn("f1", result["undefined"])
        self.assertEqual(result["recall"], 0.0)

    def test_ranking_metrics_cover_perfect_reversed_and_one_class_cases(self) -> None:
        perfect = ranking_metrics([0.1, 0.2, 0.8, 0.9], [0, 0, 1, 1])
        reversed_result = ranking_metrics([0.9, 0.8, 0.2, 0.1], [0, 0, 1, 1])
        normal_only = ranking_metrics([0.1, 0.2], [0, 0])

        self.assertEqual(perfect["auroc"], 1.0)
        self.assertEqual(perfect["auprc"], 1.0)
        self.assertEqual(reversed_result["auroc"], 0.0)
        self.assertAlmostEqual(reversed_result["auprc"], (1 / 3 + 1 / 2) / 2)
        self.assertIsNone(normal_only["auroc"])
        self.assertIsNone(normal_only["auprc"])
        self.assertEqual(set(normal_only["undefined"]), {"auroc", "auprc"})

    def test_tied_score_results_are_invariant_to_row_order(self) -> None:
        first = ranking_metrics([0.8, 0.8, 0.2, 0.2], [1, 0, 1, 0])
        reordered = ranking_metrics([0.8, 0.8, 0.2, 0.2], [0, 1, 0, 1])

        self.assertEqual(first, reordered)
        self.assertEqual(first["auroc"], 0.5)
        self.assertEqual(first["auprc"], 0.5)

    def test_input_validation_rejects_empty_misaligned_nonfinite_and_nonbinary(self) -> None:
        cases = (
            ([], [], "must not be empty"),
            ([0.1], [0, 1], "must align"),
            ([math.nan], [0], "finite"),
            ([0.1], [2], "binary labels"),
        )
        for scores, truths, message in cases:
            with self.subTest(scores=scores, truths=truths):
                with self.assertRaisesRegex(ValueError, message):
                    ranking_metrics(scores, truths)

    def test_curve_points_are_bounded_and_score_distributions_keep_support(self) -> None:
        scores = [0.1, 0.2, 0.3, 0.8, 0.9]
        truths = [0, 0, 0, 1, 1]
        curves = curve_points(scores, truths, max_points=3)
        distribution = score_distribution(scores, truths)

        self.assertLessEqual(len(curves["roc"]), 3)
        self.assertEqual(len(curves["roc"]), len(curves["precision_recall"]))
        self.assertEqual(distribution["normal"]["n"], 3)
        self.assertEqual(distribution["attack"]["n"], 2)
        self.assertEqual(distribution["normal"]["max"], 0.3)
        self.assertEqual(distribution["attack"]["min"], 0.8)


class UncertaintyAndComparisonTests(unittest.TestCase):
    def test_stratified_bootstrap_is_seeded_and_preserves_perfect_separation(self) -> None:
        keywords = {
            "threshold": 0.5,
            "replicates": 40,
            "confidence_level": 0.95,
            "seed": 913,
        }
        first = bootstrap_confidence_intervals(
            [0.1, 0.2, 0.8, 0.9], [0, 0, 1, 1], **keywords
        )
        repeated = bootstrap_confidence_intervals(
            [0.1, 0.2, 0.8, 0.9], [0, 0, 1, 1], **keywords
        )

        self.assertEqual(first, repeated)
        for name in ("accuracy", "f1", "auroc", "auprc"):
            self.assertEqual(first[name]["estimate"], 1.0)
            self.assertEqual(first[name]["low"], 1.0)
            self.assertEqual(first[name]["high"], 1.0)
            self.assertEqual(first[name]["valid_replicates"], 40)

    def test_bootstrap_rejects_invalid_design_parameters(self) -> None:
        with self.assertRaisesRegex(ValueError, "replicates"):
            bootstrap_confidence_intervals(
                [0.1], [0], threshold=0.5, replicates=0, confidence_level=0.95, seed=1
            )
        with self.assertRaisesRegex(ValueError, "confidence_level"):
            bootstrap_confidence_intervals(
                [0.1], [0], threshold=0.5, replicates=1, confidence_level=1.0, seed=1
            )
        with self.assertRaisesRegex(ValueError, "minimum_clusters"):
            bootstrap_confidence_intervals(
                [0.1],
                [0],
                threshold=0.5,
                replicates=1,
                confidence_level=0.95,
                seed=1,
                minimum_clusters=1,
            )

    def test_cluster_bootstrap_resamples_whole_independent_clusters(self) -> None:
        result = bootstrap_confidence_intervals(
            [0.1, 0.2, 0.8, 0.9],
            [0, 0, 1, 1],
            threshold=0.5,
            replicates=40,
            confidence_level=0.95,
            seed=913,
            cluster_ids=["normal-recording-a", "normal-recording-b", "event-a", "event-b"],
            minimum_class_carrying_clusters=2,
            minimum_valid_replicates=40,
            minimum_valid_fraction=1.0,
        )

        self.assertEqual(result["design"]["resampling_unit"], "declared independent cluster")
        self.assertEqual(result["design"]["independent_cluster_count"], 4)
        self.assertTrue(result["design"]["inferentially_valid"])
        self.assertEqual(result["auroc"]["valid_replicates"], 40)

    def test_cluster_bootstrap_marks_insufficient_class_clusters_undefined(self) -> None:
        result = bootstrap_confidence_intervals(
            [0.1, 0.8, 0.9],
            [0, 1, 1],
            threshold=0.5,
            replicates=20,
            confidence_level=0.95,
            seed=1,
            cluster_ids=["only-normal-recording", "event-a", "event-b"],
            minimum_class_carrying_clusters=2,
            minimum_valid_replicates=20,
            minimum_valid_fraction=1.0,
        )

        self.assertFalse(result["design"]["inferentially_valid"])
        self.assertIn("at least 2", result["design"]["undefined_reason"])
        self.assertIsNone(result["auroc"]["low"])
        self.assertEqual(result["auroc"]["valid_replicates"], 0)

    def test_cluster_bootstrap_enforces_configured_minimum_cluster_count(self) -> None:
        result = bootstrap_confidence_intervals(
            [0.1, 0.2, 0.8, 0.9],
            [0, 0, 1, 1],
            threshold=0.5,
            replicates=20,
            confidence_level=0.95,
            seed=1,
            cluster_ids=["normal-a", "normal-b", "attack-a", "attack-b"],
            minimum_clusters=5,
            minimum_class_carrying_clusters=2,
            minimum_valid_replicates=20,
            minimum_valid_fraction=1.0,
        )

        self.assertFalse(result["design"]["inferentially_valid"])
        self.assertEqual(result["design"]["minimum_clusters_required"], 5)
        self.assertIn("observed 4", result["design"]["undefined_reason"])
        self.assertIsNone(result["auroc"]["low"])
        self.assertEqual(result["auroc"]["valid_replicates"], 0)

    def test_cluster_bootstrap_requires_preregistered_validity_criteria(self) -> None:
        result = bootstrap_confidence_intervals(
            [0.1, 0.2, 0.8, 0.9],
            [0, 0, 1, 1],
            threshold=0.5,
            replicates=20,
            confidence_level=0.95,
            seed=1,
            cluster_ids=["normal-a", "normal-b", "attack-a", "attack-b"],
        )

        self.assertFalse(result["design"]["inferentially_valid"])
        self.assertEqual(
            result["design"]["undefined_reason_code"],
            "bootstrap_criteria_not_preregistered",
        )
        self.assertIsNone(result["auroc"]["low"])

    def test_mixed_cluster_bootstrap_enforces_valid_replicate_count_and_fraction(self) -> None:
        result = bootstrap_confidence_intervals(
            [0.1, 0.8, 0.2, 0.9, 0.3, 0.7],
            [0, 1, 0, 1, 0, 1],
            threshold=0.5,
            replicates=20,
            confidence_level=0.95,
            seed=7,
            cluster_ids=["mixed-a", "mixed-a", "mixed-b", "mixed-b", "mixed-c", "mixed-c"],
            minimum_clusters=3,
            minimum_class_carrying_clusters=3,
            minimum_valid_replicates=20,
            minimum_valid_fraction=1.0,
        )

        self.assertTrue(result["design"]["inferentially_valid"])
        self.assertEqual(result["design"]["attempted_replicates"], 20)
        self.assertEqual(result["design"]["valid_mixed_label_replicates"], 20)
        self.assertEqual(result["design"]["valid_mixed_label_fraction"], 1.0)

    def test_repeated_estimates_retain_dispersion_and_ignore_nonfinite_values(self) -> None:
        result = aggregate_repeated_estimates([0.6, 0.7, 0.8, math.nan])

        self.assertEqual(result["n"], 3)
        self.assertAlmostEqual(result["mean"], 0.7)
        self.assertAlmostEqual(result["sd"], 0.1)
        self.assertAlmostEqual(result["median"], 0.7)
        self.assertAlmostEqual(result["iqr"], 0.1)
        self.assertLess(result["ci_low"], result["mean"])
        self.assertGreater(result["ci_high"], result["mean"])
        self.assertEqual(result["ci_method"], "two-sided Student-t interval, df=2")
        # t(0.975, 2) is about 4.303; the small-n interval must be much wider
        # than the former normal approximation.
        self.assertGreater(result["ci_high"] - result["mean"], 0.20)

    def test_repetition_planning_uses_variance_with_floor_cap_and_missing_pilot(self) -> None:
        zero_variance = derive_repetition_count(
            [0.8, 0.8, 0.8],
            target_half_width=0.02,
            confidence_level=0.95,
            minimum=5,
            maximum=30,
        )
        high_variance = derive_repetition_count(
            [0.1, 0.9],
            target_half_width=0.01,
            confidence_level=0.95,
            minimum=5,
            maximum=30,
        )
        missing = derive_repetition_count(
            [0.8],
            target_half_width=0.02,
            confidence_level=0.95,
            minimum=5,
            maximum=30,
        )

        self.assertEqual(zero_variance["recommended_total_trials"], 5)
        self.assertIn("zero", zero_variance["reason"])
        self.assertEqual(high_variance["recommended_total_trials"], 30)
        self.assertEqual(missing["recommended_total_trials"], 30)
        self.assertIsNone(missing["observed_sd"])

    def test_fixed_fifty_plan_is_nonadaptive_and_blocks_incomplete_pilot(self) -> None:
        complete = derive_repetition_count(
            [0.55, 0.65, 0.75, 0.85, 0.95],
            target_half_width=0.025,
            confidence_level=0.95,
            minimum=10,
            maximum=50,
            required_pilot_trials=5,
            fixed_execution_trials=50,
        )
        incomplete = derive_repetition_count(
            [0.55, 0.65, 0.75, math.nan, 0.95],
            target_half_width=0.025,
            confidence_level=0.95,
            minimum=10,
            maximum=50,
            required_pilot_trials=5,
            fixed_execution_trials=50,
        )

        self.assertTrue(complete["planning_determinate"])
        self.assertEqual(complete["fixed_execution_trials"], 50)
        self.assertEqual(complete["scheduled_execution_trials"], 50)
        self.assertTrue(complete["scheduled_cap_reached"])
        self.assertIsNone(complete["operational_cap_reached"])
        self.assertIn(
            "not observable from pilot",
            str(complete["operational_cap_reached_reason"]),
        )
        self.assertGreater(complete["uncapped_required_trials"], 50)
        self.assertTrue(complete["maximum_cap_binding"])
        self.assertFalse(complete["precision_target_projected_met_at_cap"])
        self.assertEqual(
            complete["precision_claim_status"],
            "projection-only-not-a-sufficiency-guarantee",
        )
        self.assertFalse(incomplete["planning_determinate"])
        self.assertEqual(incomplete["finite_pilot_trials"], 4)
        self.assertIsNone(incomplete["uncapped_required_trials"])
        self.assertIsNone(incomplete["recommended_total_trials"])
        self.assertIsNone(incomplete["projected_ci_half_width_at_cap"])
        self.assertIsNone(incomplete["maximum_cap_binding"])

    def test_projection_uses_prospective_not_pilot_degrees_of_freedom(self) -> None:
        plan = derive_repetition_count(
            [0.70, 0.72, 0.74, 0.76, 0.78],
            target_half_width=0.025,
            confidence_level=0.95,
            minimum=10,
            maximum=50,
            required_pilot_trials=5,
            fixed_execution_trials=50,
        )

        # With future df=49 this is about 0.009; reusing pilot df=4 would
        # produce about 0.012 and would describe the wrong future interval.
        self.assertLess(plan["projected_ci_half_width_at_cap"], 0.010)

    def test_exact_paired_comparison_and_holm_correction(self) -> None:
        comparison = paired_comparison(
            {1: 0.9, 2: 0.8, 3: 0.7, 99: 0.1},
            {1: 0.7, 2: 0.7, 3: 0.6, 100: 0.9},
        )
        adjusted = holm_adjust({"a": 0.01, "b": 0.04, "c": 0.03, "missing": None})

        self.assertEqual(comparison["paired_trials"], 3)
        self.assertAlmostEqual(comparison["mean_difference"], 2 / 15)
        self.assertEqual(comparison["method"], "exact paired sign-flip permutation")
        self.assertGreaterEqual(comparison["p_value"], 0.0)
        self.assertLessEqual(comparison["p_value"], 1.0)
        self.assertEqual(adjusted, {"a": 0.03, "b": 0.06, "c": 0.06, "missing": None})

    def test_deterministic_estimate_is_never_fabricated_across_seed_pairs(self) -> None:
        comparison = paired_comparison(
            {0: 0.72},
            {101: 0.70, 211: 0.75, 307: 0.73},
            left_randomness="deterministic",
            right_randomness="seeded",
        )

        self.assertEqual(comparison["paired_trials"], 0)
        self.assertEqual(comparison["method"], "descriptive difference only")
        self.assertIsNone(comparison["cohen_dz"])
        self.assertIsNone(comparison["p_value"])
        self.assertIn("never replicated", comparison["undefined"])


class StratifiedAndEventMetricTests(unittest.TestCase):
    def test_per_class_detection_compares_each_attack_family_to_normals(self) -> None:
        results = per_class_detection_metrics(
            [0.1, 0.2, 0.9, 0.8],
            [0, 0, 1, 1],
            ["Normal", "Normal", "Attack-A", "Attack-B"],
            threshold=0.5,
        )

        self.assertEqual(set(results), {"Attack-A", "Attack-B"})
        for result in results.values():
            self.assertEqual(result["support"], {"total": 3, "normal": 2, "attack": 1})
            self.assertEqual(result["recall"], 1.0)
            self.assertEqual(result["auroc"], 1.0)

    def test_event_metrics_deduplicate_events_and_count_false_alert_units(self) -> None:
        result = event_metrics(
            [1, 0, 1, 1],
            [1, 1, 0, 1],
            [("event-a",), ("event-a", "event-b"), (), ("event-c",)],
        )

        self.assertEqual(result["event_count"], 3)
        self.assertEqual(result["detected_event_count"], 2)
        self.assertAlmostEqual(result["event_recall"], 2 / 3)
        self.assertEqual(result["false_alert_unit_count"], 1)


if __name__ == "__main__":
    unittest.main()
