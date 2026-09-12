"""Offline tests for restricted ScenarioTruth v1 contracts."""
from __future__ import annotations

import unittest
from dataclasses import replace

from parallel_truth_fingerprint.contracts.scenario_truth import (
    ScenarioTruth, ScenarioTruthError, canonical_scenario_truth_bytes, parse_scenario_truth,
    parse_scenario_truth_json,
)
from parallel_truth_fingerprint.evidence.scenario_truth_validation import (
    ReferenceDescriptor, assess_truth_compatibility, validate_public_boundary, validate_scenario_truth,
)


def digest(letter: str) -> str: return "sha256:" + letter * 64


class ScenarioTruthTests(unittest.TestCase):
    def setUp(self) -> None:
        self.record = ScenarioTruth.build(
            experiment_id=digest("a"), matrix_id=digest("b"), predeclared_run_id=digest("c"), trace_id=digest("d"),
            event_id=digest("e"), correlation_id=digest("f"), condition_interval_ref=digest("1"),
            intervention_interval_ref=digest("2"), declared_truth_provenance_ref=digest("3"),
            restricted_writer_id=digest("4"), declared_at="2026-01-01T00:00:00.000000Z",
            interval_facts_at="2026-01-01T00:00:01.000000Z",
        )
        self.registry = {identity: ReferenceDescriptor(identity, "evaluator_restricted" if identity in self.record.immutable_parent_ids[-4:] else "detector_facing", "declared_parent", True) for identity in self.record.immutable_parent_ids}

    def test_canonical_identity_is_repeatable_and_replacement_is_new_record(self) -> None:
        self.assertEqual(self.record, parse_scenario_truth(self.record.to_dict()))
        self.assertEqual(canonical_scenario_truth_bytes(self.record), canonical_scenario_truth_bytes(self.record))
        inputs = {key: value for key, value in self.record.to_dict().items() if key in {
            "experiment_id", "matrix_id", "predeclared_run_id", "trace_id", "event_id", "correlation_id", "condition_interval_ref", "intervention_interval_ref", "declared_truth_provenance_ref", "restricted_writer_id", "declared_at", "interval_facts_at"}}
        inputs["event_id"] = digest("9")
        changed = ScenarioTruth.build(**inputs)
        self.assertNotEqual(self.record.scenario_truth_content_id, changed.scenario_truth_content_id)

    def test_strict_parser_rejects_unknown_duplicate_and_forged_identity(self) -> None:
        with self.assertRaises(ScenarioTruthError): parse_scenario_truth({**self.record.to_dict(), "unexpected": "x"})
        with self.assertRaises(ScenarioTruthError): parse_scenario_truth(replace(self.record, scenario_truth_content_id=digest("0")).to_dict())
        payload = '{"contract_id":"ScenarioTruth","contract_id":"ScenarioTruth"}'
        with self.assertRaises(ScenarioTruthError): parse_scenario_truth_json(payload)

    def test_restricted_validation_and_public_leakage_are_fail_closed(self) -> None:
        self.assertTrue(validate_scenario_truth(self.record, resolver=self.registry.get).valid)
        bad = dict(self.registry); bad[self.record.trace_id] = ReferenceDescriptor(self.record.trace_id, "detector_facing", "mutable", False)
        self.assertFalse(validate_scenario_truth(self.record, resolver=bad.get).valid)
        public_id = digest("7")
        public = {public_id: ReferenceDescriptor(public_id, "detector_facing", "public_observation", True, (self.record.scenario_truth_content_id,)), self.record.scenario_truth_content_id: ReferenceDescriptor(self.record.scenario_truth_content_id, "evaluator_restricted", "restricted_truth", True)}
        result = validate_public_boundary({"correlation_id": public_id}, resolver=public.get)
        self.assertFalse(result.valid)
        self.assertFalse(validate_public_boundary({"scenario_name": "forbidden"}, resolver=public.get).valid)

    def test_compatibility_is_redacted_nonpublished_and_detects_lineage_change(self) -> None:
        result = assess_truth_compatibility(self.record, upstream_validated=True, upstream_restricted_truth_id=self.record.scenario_truth_content_id, upstream_parent_ids=self.record.immutable_parent_ids, observed_at="2026-01-01T00:00:02.000000Z", audience="evaluator_restricted")
        self.assertTrue(result.compatible); self.assertFalse(result.published); self.assertEqual("none", result.authorization_effect)
        denied = assess_truth_compatibility(self.record, upstream_validated=False, upstream_restricted_truth_id=digest("0"), upstream_parent_ids=(), observed_at="invalid", audience="detector_facing")
        self.assertFalse(denied.compatible)
        self.assertTrue(all(item.token not in {self.record.scenario_truth_content_id, "forbidden"} for item in denied.violations))


if __name__ == "__main__": unittest.main()
