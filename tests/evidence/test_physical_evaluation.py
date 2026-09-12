"""Focused unit coverage for evaluator-only post-truth physical outcomes."""
from __future__ import annotations

import unittest

from parallel_truth_fingerprint.contracts.physical_blind_scores import (
    DETECTOR_SCORE_SCHEMA, PHYSICAL_SCORE_MANIFEST_SCHEMA, DetectorScore,
    PhysicalScoreManifest, ScoreDecision, finalize_detector_score, finalize_physical_score_manifest,
)
from parallel_truth_fingerprint.contracts.physical_evaluation import (
    MetricApplicability, MetricDeclaration, PhysicalEvaluationPlan, RestrictedTruthJoin,
    SensitivityOutcome, TruthState, finalize_physical_evaluation_plan,
)
from parallel_truth_fingerprint.evidence.physical_evaluation import (
    evaluate_frozen_physical_scores, validate_physical_evaluation_plan,
)
from parallel_truth_fingerprint.contracts.physical_evaluation import FrozenEvaluationWindow


def digest(number: int) -> str:
    return "sha256:" + f"{number:064x}"


class PhysicalPostTruthEvaluationTests(unittest.TestCase):
    def resolver(self, value: str) -> bool:
        return value.startswith("sha256:") and value != digest(999)

    def manifest(self) -> PhysicalScoreManifest:
        score = finalize_detector_score(DetectorScore(
            DETECTOR_SCORE_SCHEMA, digest(1), digest(2), digest(3), "0.8", "0.8", "higher_anomalous", digest(4),
            ScoreDecision.ANOMALOUS, digest(5), digest(6), digest(7), digest(8), digest(9), digest(10), digest(11), None,
        ))
        return finalize_physical_score_manifest(PhysicalScoreManifest(
            PHYSICAL_SCORE_MANIFEST_SCHEMA, digest(1), digest(12), (digest(2),), (score,), (digest(13),), (), digest(10), digest(11),
        ))

    def plan(self, manifest: PhysicalScoreManifest, **changes: object) -> PhysicalEvaluationPlan:
        data: dict[str, object] = dict(
            schema_version="PhysicalPostTruthEvaluation.v1", score_manifest_id=manifest.manifest_id, bundle_id=digest(1),
            threshold_id=digest(4), partition_id=digest(12), metric_policy_id=digest(14), experiment_id=digest(15),
            truth_unlock_id=digest(16), evaluator_authorization_id=digest(17),
            windows=(FrozenEvaluationWindow(digest(2), digest(15), digest(18), digest(19), digest(9)),),
            planned_stratum_ids=(digest(20),), planned_sensitivity_threshold_ids=(digest(21),),
        )
        data.update(changes)
        return finalize_physical_evaluation_plan(PhysicalEvaluationPlan(**data))

    def join(self, manifest: PhysicalScoreManifest, **changes: object) -> RestrictedTruthJoin:
        score = manifest.scores[0]
        data: dict[str, object] = dict(score_id=score.score_id, window_id=digest(2), experiment_id=digest(15), run_id=digest(18), event_id=digest(19), correlation_id=digest(9), truth_record_id=digest(22), truth_state=TruthState.ANOMALOUS, regime_id=digest(23), transition_id=digest(24), scenario_id=digest(25), severity_id=digest(26), sensor_id=digest(27), repetition_id=digest(28), recovery_id=digest(29), quality_state_id=digest(30), stratum_ids=(digest(20),))
        data.update(changes)
        return RestrictedTruthJoin(**data)

    def declarations(self) -> tuple[MetricDeclaration, ...]:
        return (
            MetricDeclaration(digest(31), "precision", MetricApplicability.APPLICABLE),
            MetricDeclaration(digest(32), "recall", MetricApplicability.APPLICABLE),
            MetricDeclaration(digest(33), "f1", MetricApplicability.APPLICABLE),
            MetricDeclaration(digest(34), "confusion_tp", MetricApplicability.APPLICABLE),
            MetricDeclaration(digest(35), "event_recall", MetricApplicability.APPLICABLE),
            MetricDeclaration(digest(36), "false_events", MetricApplicability.APPLICABLE),
            MetricDeclaration(digest(37), "classified_count", MetricApplicability.APPLICABLE),
            MetricDeclaration(digest(38), "unavailable_count", MetricApplicability.APPLICABLE),
            MetricDeclaration(digest(39), "precision", MetricApplicability.INAPPLICABLE, digest(40)),
        )

    def evaluate(self, *, manifest: PhysicalScoreManifest | None = None, plan: PhysicalEvaluationPlan | None = None, joins: tuple[RestrictedTruthJoin, ...] | None = None, declarations: tuple[MetricDeclaration, ...] | None = None, sensitivity: tuple[SensitivityOutcome, ...] | None = None):
        manifest = manifest or self.manifest(); plan = plan or self.plan(manifest); joins = joins or (self.join(manifest),)
        sensitivity = sensitivity if sensitivity is not None else (SensitivityOutcome(digest(21), manifest.scores[0].score_id, "anomalous"),)
        return evaluate_frozen_physical_scores(plan, manifest, joins=joins, metric_declarations=declarations or self.declarations(), sensitivity_outcomes=sensitivity, resource_evidence_ids=(digest(41),), quality_evidence_ids=(digest(42),), limitation_ids=(digest(43),), immutable_resolver=self.resolver, authorization_validator=lambda action, authorization, unlock: (action, authorization, unlock) == ("post_truth_physical_evaluation", digest(17), digest(16)))

    def test_authorized_join_preserves_regime_transition_and_reports_declared_outcomes(self) -> None:
        result = self.evaluate()
        self.assertEqual("complete", result.disposition)
        self.assertEqual(digest(23), result.joins[0].regime_id)
        self.assertEqual(digest(24), result.joins[0].transition_id)
        metrics = {item.metric_id: item for item in result.metrics}
        self.assertEqual("1.0", metrics[digest(31)].value)
        self.assertEqual("1", metrics[digest(34)].value)
        self.assertIsNone(metrics[digest(39)].value)
        self.assertEqual(digest(40), metrics[digest(39)].inapplicable_reason_id)
        self.assertTrue(any(item.stratum_id == digest(20) and item.support == 1 for item in result.metrics))

    def test_plan_requires_exact_truth_authorization_and_immutable_window_closure(self) -> None:
        manifest = self.manifest(); plan = self.plan(manifest)
        denied = validate_physical_evaluation_plan(plan, immutable_resolver=self.resolver, authorization_validator=lambda *_: False)
        self.assertIn("PPE13_AUTHORIZATION_DENIED", denied.diagnostic_codes)
        broken = self.plan(manifest, windows=(FrozenEvaluationWindow(digest(2), digest(999), digest(18), digest(19), digest(9)),))
        result = self.evaluate(manifest=manifest, plan=broken)
        self.assertEqual("invalid", result.disposition)
        self.assertIn("PPE13_WINDOW_PROVENANCE_INVALID", result.diagnostic_codes)

    def test_truth_join_cannot_swap_correlation_or_hide_a_declared_stratum(self) -> None:
        manifest = self.manifest()
        result = self.evaluate(manifest=manifest, joins=(self.join(manifest, correlation_id=digest(44), stratum_ids=(digest(45),)),))
        self.assertEqual("invalid", result.disposition)
        self.assertIn("PPE13_TRUTH_JOIN_IDENTITY_MISMATCH", result.diagnostic_codes)
        self.assertIn("PPE13_UNDECLARED_STRATUM", result.diagnostic_codes)

    def test_sensitivity_is_restricted_to_preregistered_thresholds_and_frozen_scores(self) -> None:
        manifest = self.manifest()
        invalid = self.evaluate(manifest=manifest, sensitivity=(SensitivityOutcome(digest(44), manifest.scores[0].score_id, "anomalous"),))
        self.assertEqual("invalid", invalid.disposition)
        self.assertIn("PPE13_SENSITIVITY_INVALID", invalid.diagnostic_codes)
        valid = self.evaluate(manifest=manifest, sensitivity=(SensitivityOutcome(digest(21), manifest.scores[0].score_id, "normal"),))
        self.assertEqual("complete", valid.disposition)

    def test_unavailable_truth_is_not_silently_counted_as_normal(self) -> None:
        manifest = self.manifest(); result = self.evaluate(manifest=manifest, joins=(self.join(manifest, truth_state=TruthState.UNAVAILABLE),))
        metrics = {item.metric_kind: item for item in result.metrics}
        self.assertEqual("0", metrics["classified_count"].value)
        self.assertEqual("1", metrics["unavailable_count"].value)


if __name__ == "__main__":
    unittest.main()
