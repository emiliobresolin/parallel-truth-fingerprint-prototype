"""Focused, offline tests for the authorized physical shadow/G5 closure."""
from __future__ import annotations

import unittest
from dataclasses import replace

from parallel_truth_fingerprint.contracts.physical_blind_scores import ScoreDecision
from parallel_truth_fingerprint.contracts.physical_shadow import (
    G5Disposition, PHYSICAL_SHADOW_SELECTION_SCHEMA, PhysicalShadowSelection,
    finalize_physical_shadow_selection,
)
from parallel_truth_fingerprint.evidence.physical_shadow import (
    ShadowInferenceInput, ShadowInferenceOutput, decide_g5_shadow_route,
    qualify_g5_replay, serve_physical_shadow, validate_physical_shadow_selection,
)
from tests.evidence.test_detector_bundle import DetectorBundleTests, digest
from tests.evidence.test_physical_evidence_qualification import observation


class PhysicalShadowTests(unittest.TestCase):
    def bundle(self): return DetectorBundleTests().bundle()
    def environment(self, bundle): return DetectorBundleTests().environment(bundle)
    def components(self, bundle): return DetectorBundleTests().resolver(bundle)
    def resolve(self, _: str) -> bool: return True

    def selection(self, bundle, **changes: object) -> PhysicalShadowSelection:
        values: dict[str, object] = dict(schema_version=PHYSICAL_SHADOW_SELECTION_SCHEMA,
            bundle_id=bundle.bundle_id, profile_id=digest(50), parameter_set_id=digest(400),
            feature_schema_id=bundle.feature_schema_id, preprocessing_id=bundle.preprocessing_state_id,
            threshold_id=bundle.threshold_id, code_identity=bundle.code_identity,
            dependency_lock_sha256=bundle.dependency_lock_sha256, runtime_identity=bundle.runtime_identity,
            authorization_id=digest(401))
        values.update(changes)
        return finalize_physical_shadow_selection(PhysicalShadowSelection(**values))

    def item(self, **changes: object) -> ShadowInferenceInput:
        values: dict[str, object] = dict(window_id=digest(410), observations=(observation(),),
            input_hash=digest(411), missingness_id=digest(412), input_quality_id=digest(413),
            run_correlation_id=digest(414), failure_evidence_id=digest(415))
        values.update(changes)
        return ShadowInferenceInput(**values)

    def serve(self, selection, bundle, item, predictor):
        return serve_physical_shadow(selection, bundle, item, environment=self.environment(bundle),
            component_resolver=self.components(bundle), immutable_resolver=self.resolve,
            authorization_validator=lambda action, auth, scope: (action, auth, scope) == ("shadow_serving", selection.authorization_id, bundle.bundle_id), predictor=predictor)

    def test_exact_authorized_selection_runs_inference_only_on_signal_v2(self) -> None:
        bundle = self.bundle(); selection = self.selection(bundle); called = []
        valid = validate_physical_shadow_selection(selection, bundle, environment=self.environment(bundle),
            component_resolver=self.components(bundle), immutable_resolver=self.resolve,
            authorization_validator=lambda *_: True)
        self.assertTrue(valid.accepted)
        result = self.serve(selection, bundle, self.item(), lambda item: (called.append(item) or ShadowInferenceOutput("raw", "calibrated", ScoreDecision.ANOMALOUS, digest(416))))
        self.assertEqual("eligible", result.disposition)
        self.assertEqual(1, len(called))
        self.assertEqual(ScoreDecision.ANOMALOUS, result.score.decision)

    def test_missing_or_incompatible_input_is_blocked_without_predictor_or_fallback(self) -> None:
        bundle = self.bundle(); selection = self.selection(bundle); called = []
        blocked = self.serve(selection, bundle, self.item(observations=()), lambda _: called.append(True))
        self.assertEqual("blocked", blocked.disposition)
        self.assertIn("PS13_INPUT_STREAM_ABSENT", blocked.diagnostic_codes)
        self.assertEqual([], called)
        stale = self.selection(bundle, feature_schema_id=digest(999))
        invalid = validate_physical_shadow_selection(stale, bundle, environment=self.environment(bundle),
            component_resolver=self.components(bundle), immutable_resolver=self.resolve,
            authorization_validator=lambda *_: True)
        self.assertIn("PS13_DECLARED_ENVIRONMENT_MISMATCH", invalid.diagnostic_codes)

    def test_unauthorized_selection_and_nonimmutable_alias_fail_closed(self) -> None:
        bundle = self.bundle(); selection = self.selection(bundle, parameter_set_id="latest")
        validation = validate_physical_shadow_selection(selection, bundle, environment=self.environment(bundle),
            component_resolver=self.components(bundle), immutable_resolver=self.resolve,
            authorization_validator=lambda *_: False)
        self.assertIn("PS13_IDENTITY_UNRESOLVED", validation.diagnostic_codes)
        self.assertIn("PS13_AUTHORIZATION_DENIED", validation.diagnostic_codes)

    def test_g5_replay_retains_mismatch_and_explicitly_rolls_back(self) -> None:
        bundle = self.bundle(); selection = self.selection(bundle)
        served = self.serve(selection, bundle, self.item(), lambda _: ShadowInferenceOutput("raw", "calibrated", "normal", digest(416)))
        mismatch = replace(served.score, calibrated_score="different")
        qualification = qualify_g5_replay(selection, (served.score,), (mismatch,), tolerance_id=digest(417), immutable_resolver=self.resolve)
        self.assertEqual(G5Disposition.NOT_QUALIFIED, qualification.disposition)
        self.assertIn("G5_REPLAY_MISMATCH", qualification.diagnostic_codes)
        prior = self.selection(bundle, parameter_set_id=digest(499))
        route = decide_g5_shadow_route(selection, qualification, last_verified_selection=prior, immutable_resolver=self.resolve)
        self.assertEqual("rolled_back", route.disposition)
        self.assertEqual(prior.selection_id, route.selected_identity)

    def test_g5_only_selects_an_exact_qualified_identity(self) -> None:
        bundle = self.bundle(); selection = self.selection(bundle)
        served = self.serve(selection, bundle, self.item(), lambda _: ShadowInferenceOutput("raw", "calibrated", "normal", digest(416)))
        qualification = qualify_g5_replay(selection, (served.score,), (served.score,), tolerance_id=digest(417), immutable_resolver=self.resolve)
        route = decide_g5_shadow_route(selection, qualification, last_verified_selection=None, immutable_resolver=self.resolve)
        self.assertEqual("eligible", route.disposition)
        self.assertEqual(selection.selection_id, route.selected_identity)


if __name__ == "__main__":
    unittest.main()
