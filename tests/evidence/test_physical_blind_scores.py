"""Focused offline guardrails for frozen physical blind scoring (Story 13.6)."""
from __future__ import annotations

import unittest
from dataclasses import replace

from parallel_truth_fingerprint.contracts.detector_bundle import (
    DETECTOR_BUNDLE_SCHEMA, PHYSICAL_FEATURE_SCHEMA_VERSION, PHYSICAL_MODEL_CONTRACT_VERSION,
    BundleComponentHash, DetectorBundle,
)
from parallel_truth_fingerprint.contracts.physical_blind_scores import (
    PHYSICAL_SCORE_MANIFEST_SCHEMA, PhysicalScoreManifest, ScoreDecision,
    finalize_physical_score_manifest,
)
from parallel_truth_fingerprint.contracts.physical_threshold import PhysicalThreshold
from parallel_truth_fingerprint.evidence.detector_bundle import DeclaredBundleEnvironment, assemble_detector_bundle
from parallel_truth_fingerprint.evidence.physical_blind_scores import (
    BlindPhysicalScoringContext, InferenceResult, PhysicalInferenceInput,
    score_blind_physical_window, validate_physical_score_manifest,
)
from parallel_truth_fingerprint.evidence.physical_partitions import (
    PhysicalPartition, PhysicalPartitionMember, PhysicalWindow, PreprocessingFit,
)


def digest(number: int) -> str:
    return "sha256:" + f"{number:064x}"


class PhysicalBlindScoreTests(unittest.TestCase):
    def resolver(self, value: str) -> bool:
        return value.startswith("sha256:") and value != digest(999)

    def bundle(self) -> DetectorBundle:
        names = ("architecture", "weights", "feature_schema", "preprocessing", "training_dataset", "training_split",
                 "calibration_dataset", "calibration_split", "calibration_artifact", "threshold", "threshold_derivation",
                 "profile_compatibility", "code", "dependency_lock", "runtime")
        ids = {name: digest(index) for index, name in enumerate(names, 1)}
        return assemble_detector_bundle(DetectorBundle(
            DETECTOR_BUNDLE_SCHEMA, "lstm_ae", PHYSICAL_MODEL_CONTRACT_VERSION, ids["architecture"], ids["weights"],
            ids["feature_schema"], PHYSICAL_FEATURE_SCHEMA_VERSION, ("current", "pressure"), ids["preprocessing"],
            ids["training_dataset"], ids["training_split"], ids["calibration_dataset"], ids["calibration_split"],
            ids["calibration_artifact"], ids["threshold"], ids["threshold_derivation"], "higher_anomalous",
            ids["profile_compatibility"], ids["code"], ids["dependency_lock"], ids["runtime"],
            tuple(BundleComponentHash(name, ids[name], digest(100 + index)) for index, name in enumerate(sorted(ids))),
        ))

    def context(self) -> BlindPhysicalScoringContext:
        bundle = self.bundle()
        partition = PhysicalPartition(digest(201), bundle.feature_schema_id, (digest(202),), (
            PhysicalPartitionMember(digest(203), "train", True, digest(204)),
            PhysicalPartitionMember(digest(205), "test", False, digest(206)),
        ))
        fit = PreprocessingFit(bundle.preprocessing_state_id, partition.partition_id, (digest(203),), bundle.feature_schema_id,
                               digest(207), bundle.ordered_feature_names, digest(208), digest(209), (digest(210),), digest(211))
        threshold0 = PhysicalThreshold(bundle.weights_id, bundle.preprocessing_state_id, bundle.feature_schema_id,
            digest(212), (digest(213),), digest(214), "higher_anomalous", "frozen", "opaque", digest(215),
            bundle.code_identity, bundle.runtime_identity, "2026-01-01T00:00:00Z")
        threshold = replace(threshold0, content_id=threshold0.computed_id())
        environment = DeclaredBundleEnvironment(bundle.model_contract_version, bundle.feature_schema_id,
            bundle.feature_schema_version, bundle.ordered_feature_names, bundle.profile_compatibility_id,
            bundle.code_identity, bundle.dependency_lock_sha256, bundle.runtime_identity)
        return BlindPhysicalScoringContext(bundle, environment, partition, fit, threshold, digest(207),
                                           bundle.code_identity, bundle.runtime_identity, digest(216))

    def item(self, context: BlindPhysicalScoringContext, **changes: object) -> PhysicalInferenceInput:
        window = PhysicalWindow("physical-window-1", digest(205), (digest(220), digest(221)), 1, 2,
                                context.partition.partition_id, context.bundle.feature_schema_id,
                                context.bundle.preprocessing_state_id, (digest(222),), ())
        values: dict[str, object] = dict(window=window, input_hash=digest(223), missingness_id=digest(224),
                                         input_quality_id=digest(225), run_correlation_id=digest(226))
        values.update(changes)
        return PhysicalInferenceInput(**values)

    def score(self, context: BlindPhysicalScoringContext, item: PhysicalInferenceInput):
        hashes = {part.artifact_id: part.serialized_sha256 for part in context.bundle.component_hashes}
        return score_blind_physical_window(context, item, component_resolver=hashes.get,
            immutable_resolver=self.resolver, authorization_validator=lambda action, identity, scope: action == "blind_scoring" and identity == context.authorization_id,
            predictor=lambda _: InferenceResult("raw", "calibrated", ScoreDecision.ANOMALOUS, digest(227)))

    def manifest(self, context: BlindPhysicalScoringContext, score, **changes: object) -> PhysicalScoreManifest:
        values: dict[str, object] = dict(schema_version=PHYSICAL_SCORE_MANIFEST_SCHEMA, bundle_id=context.bundle.bundle_id,
            partition_id=context.partition.partition_id, planned_window_ids=(score.window_id,), scores=(score,),
            resource_evidence_ids=(digest(228),), failure_evidence_ids=(), code_identity=context.code_identity,
            runtime_identity=context.runtime_identity)
        values.update(changes)
        return finalize_physical_score_manifest(PhysicalScoreManifest(**values))

    def test_frozen_context_scores_only_test_window_with_exact_pinned_dependencies(self) -> None:
        context = self.context(); score = self.score(context, self.item(context))
        self.assertEqual(ScoreDecision.ANOMALOUS, score.decision)
        self.assertEqual(context.bundle.bundle_id, score.bundle_id)
        self.assertTrue(validate_physical_score_manifest(self.manifest(context, score), immutable_resolver=self.resolver).accepted)

    def test_incompatible_or_unauthorized_context_becomes_retained_invalid_outcome(self) -> None:
        context = replace(self.context(), code_identity=digest(999)); score = self.score(context, self.item(context))
        self.assertEqual(ScoreDecision.INVALID, score.decision)
        self.assertIsNone(score.raw_score)
        self.assertNotEqual(ScoreDecision.NORMAL, score.decision)

    def test_unavailable_result_preserves_reason_and_never_looks_normal(self) -> None:
        context = self.context(); item = self.item(context); hashes = {part.artifact_id: part.serialized_sha256 for part in context.bundle.component_hashes}
        score = score_blind_physical_window(context, item, component_resolver=hashes.get, immutable_resolver=self.resolver,
            authorization_validator=lambda *_: True,
            predictor=lambda _: InferenceResult("would-be-raw", "would-be-calibrated", "unavailable", digest(227), digest(229)))
        self.assertEqual(ScoreDecision.UNAVAILABLE, score.decision)
        self.assertIsNone(score.raw_score); self.assertEqual(digest(229), score.unavailability_reason_id)

    def test_manifest_rejects_dropped_window_tampered_score_and_unavailable_without_reason(self) -> None:
        context = self.context(); score = self.score(context, self.item(context)); manifest = self.manifest(context, score)
        dropped = replace(manifest, planned_window_ids=(score.window_id, "unaccounted-window"))
        self.assertIn("PBS13_MANIFEST_WINDOW_CLOSURE_INCOMPLETE", validate_physical_score_manifest(dropped, immutable_resolver=self.resolver).diagnostic_codes)
        tampered = replace(score, raw_score="changed")
        invalid = finalize_physical_score_manifest(replace(manifest, scores=(tampered,)))
        self.assertIn("PBS13_SCORE_IMMUTABILITY_INVALID", validate_physical_score_manifest(invalid, immutable_resolver=self.resolver).diagnostic_codes)
        unavailable = replace(score, decision="unavailable", raw_score=None, calibrated_score=None, unavailability_reason_id=None)
        malformed = finalize_physical_score_manifest(replace(manifest, scores=(unavailable,)))
        self.assertIn("PBS13_UNAVAILABLE_OUTCOME_INVALID", validate_physical_score_manifest(malformed, immutable_resolver=self.resolver).diagnostic_codes)


if __name__ == "__main__":
    unittest.main()
