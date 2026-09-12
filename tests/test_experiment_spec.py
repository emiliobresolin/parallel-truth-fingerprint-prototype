import copy
import json
import unittest

from parallel_truth_fingerprint.contracts.experiment_spec import (
    BindingDisposition, ExperimentSpecError, ExperimentSpecValidator,
    experiment_spec_content_id, parse_experiment_spec, parse_experiment_spec_json,
    project_experiment_matrix,
)


def digest(n: int) -> str: return "sha256:" + f"{n:064x}"


def payload():
    value = {
        "schema_version": "experiment-spec.v1", "experiment_id": digest(1),
        "run_bindings": [{"run_binding_id": "fixture-run-a", "phase_id": "phase-a", "scenario_ref": digest(2), "intervention_ref": digest(3), "recovery_ref": digest(4), "planned_disposition": "planned", "allowed_outcome_policy_ref": digest(5)}],
        "stimulus_identity": {"kind": "input_trace", "input_trace_ref": digest(6), "seed_ref": None, "rng_ref": None, "code_ref": None, "runtime_ref": None},
        "phases": [{"slot_id": "phase-a", "disposition": "bound", "reference": digest(7), "rationale": "fixture"}],
        "schedule_descriptors": [{"descriptor_id": "fixture-schedule", "numeric_loci": [{"slot_id": "dwell", "disposition": "unavailable_blocking", "reference": None, "rationale": "not a domain value"}], "opaque_descriptor_ref": digest(8)}],
        "expected_streams": [{"stream_id": "fixture-stream", "schema_ref": digest(9), "audience_ref": digest(10), "profile_ref": digest(11)}],
        "policy_references": [{"slot_id": "truth-policy", "disposition": "bound", "reference": digest(12), "rationale": "opaque"}],
        "reference_factor_binding": {"factor_name": "speed_reference_pct", "decision_ref": digest(13), "low_factor_parameter_ref": digest(14), "high_factor_parameter_ref": digest(15), "command_profile_ref": digest(16), "low_profile_parameter_ref": digest(17), "high_profile_parameter_ref": digest(18), "low_current_parameter_ref": digest(19), "high_current_parameter_ref": digest(20), "prohibited_meanings": ["electrical_power", "manufacturer_recommendation", "universal_compressor_range", "safety_limit", "efficiency_limit"]},
        "applicability": {"evidence_role": "fixture_test", "scope": "test_only", "synchronization": "not_synchronized", "disposition": "bound"}, "limitations": ["fixture only"], "authorization_effect": "none",
    }
    value["content_sha256"] = experiment_spec_content_id(value)
    return value


class ExperimentSpecTests(unittest.TestCase):
    def test_canonical_parse_matrix_and_blocked_eligibility(self):
        spec = parse_experiment_spec(payload())
        self.assertEqual(spec.to_dict()["content_sha256"], experiment_spec_content_id(spec.to_dict()))
        self.assertFalse(ExperimentSpecValidator(lambda _: True).validate(spec).execution_eligible)
        row = project_experiment_matrix(spec)[0]
        self.assertEqual(row.planned_disposition, "planned")
        self.assertFalse(hasattr(row, "outcome"))

    def test_strict_duplicate_unknown_and_seed_rejected(self):
        with self.assertRaises(ExperimentSpecError): parse_experiment_spec_json(json.dumps(payload())[:-1] + ',"x":1}')
        with self.assertRaises(ExperimentSpecError): parse_experiment_spec_json('{"schema_version":"experiment-spec.v1","schema_version":"x"}')
        bad = copy.deepcopy(payload()); bad["stimulus_identity"]["seed_ref"] = digest(99); bad["content_sha256"] = experiment_spec_content_id(bad)
        with self.assertRaises(ExperimentSpecError): parse_experiment_spec(bad)

    def test_identity_changes_and_unresolved_reference_blocks(self):
        first = payload(); second = copy.deepcopy(first); second["limitations"] = ["changed fixture"]; second["content_sha256"] = experiment_spec_content_id(second)
        self.assertNotEqual(first["content_sha256"], second["content_sha256"])
        result = ExperimentSpecValidator(lambda ref: ref != digest(10)).validate(parse_experiment_spec(first))
        self.assertFalse(result.execution_eligible)
        self.assertEqual(result.authorization_effect, "none")


if __name__ == "__main__": unittest.main()
