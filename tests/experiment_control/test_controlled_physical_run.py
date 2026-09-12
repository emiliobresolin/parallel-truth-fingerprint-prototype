"""Offline conformance tests for the Story 10.6 admission boundary."""

from __future__ import annotations

import hashlib
import unittest
from dataclasses import replace

from parallel_truth_fingerprint.contracts.experiment_spec import ExperimentSpecValidator, parse_experiment_spec, project_experiment_matrix
from parallel_truth_fingerprint.contracts.physical_run import (
    ExecutionModality, PhysicalRunRequest, RunScopeProjection,
    StreamRecord, StreamRequirement, StreamStatus,
)
from parallel_truth_fingerprint.evidence.physical_run import (
    authorize_physical_run_request, validate_stream_completeness,
)


def digest(n: int) -> str:
    return "sha256:" + f"{n:064x}"


def spec_payload() -> dict[str, object]:
    payload: dict[str, object] = {
        "schema_version": "experiment-spec.v1", "experiment_id": digest(1),
        "run_bindings": [{"run_binding_id": "fixture-run", "phase_id": "fixture-phase", "scenario_ref": digest(2), "intervention_ref": digest(3), "recovery_ref": digest(4), "planned_disposition": "planned", "allowed_outcome_policy_ref": digest(5)}],
        "stimulus_identity": {"kind": "input_trace", "input_trace_ref": digest(6), "seed_ref": None, "rng_ref": None, "code_ref": None, "runtime_ref": None},
        "phases": [{"slot_id": "phase", "disposition": "bound", "reference": digest(7), "rationale": "fixture"}],
        "schedule_descriptors": [], "expected_streams": [{"stream_id": "stream-alpha", "schema_ref": digest(8), "audience_ref": digest(9), "profile_ref": digest(10)}],
        "policy_references": [{"slot_id": "policy", "disposition": "bound", "reference": digest(11), "rationale": "fixture"}],
        "reference_factor_binding": {"factor_name": "speed_reference_pct", "decision_ref": digest(12), "low_factor_parameter_ref": digest(13), "high_factor_parameter_ref": digest(14), "command_profile_ref": digest(15), "low_profile_parameter_ref": digest(16), "high_profile_parameter_ref": digest(17), "low_current_parameter_ref": digest(18), "high_current_parameter_ref": digest(19), "prohibited_meanings": ["electrical_power", "manufacturer_recommendation", "universal_compressor_range", "safety_limit", "efficiency_limit"]},
        "applicability": {"evidence_role": "fixture", "scope": "fixture", "synchronization": "none", "disposition": "bound"}, "limitations": ["Non-domain fixture."], "content_sha256": "", "authorization_effect": "none",
    }
    from parallel_truth_fingerprint.contracts.experiment_spec import experiment_spec_content_id
    payload["content_sha256"] = experiment_spec_content_id(payload)
    return payload


class ControlledPhysicalRunTests(unittest.TestCase):
    def request(self) -> tuple[PhysicalRunRequest, object]:
        spec = parse_experiment_spec(spec_payload())
        row = project_experiment_matrix(spec)[0]
        projection = RunScopeProjection(digest(20), spec.payload["content_sha256"], row.row_content_sha256, "fixture-run", digest(21))
        request = PhysicalRunRequest(digest(22), projection, ExecutionModality.ADMITTED_EMULATOR, digest(23), digest(24), digest(25), (digest(26), digest(27)), (StreamRequirement("stream-alpha", "edge-alpha", "sensor-alpha", 1, 2),))
        return request, spec

    def test_request_requires_exact_eligibility_authorizations_and_qualified_repository(self) -> None:
        request, spec = self.request()
        calls: list[str] = []
        result = authorize_physical_run_request(
            request, spec=spec, matrix_rows=project_experiment_matrix(spec),
            spec_validator=ExperimentSpecValidator(lambda _: True),
            immutable_resolver=lambda _: True, repository_qualified=lambda identity: identity == digest(25),
            authorization_validator=lambda action, identity, scope: calls.append(action) or (identity in {digest(26), digest(27)} and scope == digest(20)),
        )
        self.assertTrue(result.allowed)
        self.assertEqual(["feature_activation", "experiment_execution"], calls)
        denied = authorize_physical_run_request(
            replace(request, repository_qualification_id=digest(99)), spec=spec, matrix_rows=project_experiment_matrix(spec),
            spec_validator=ExperimentSpecValidator(lambda _: True), immutable_resolver=lambda _: True, repository_qualified=lambda _: False,
            authorization_validator=lambda *_: True,
        )
        self.assertFalse(denied.allowed)
        self.assertIn("PRV1_REPOSITORY_UNQUALIFIED", {item.rule_id for item in denied.violations})

    def test_real_hardware_requires_a_third_distinct_authorization(self) -> None:
        request, spec = self.request()
        physical = replace(request, modality=ExecutionModality.PHYSICAL_HARDWARE, physical_acquisition_authorization_id=None)
        result = authorize_physical_run_request(
            physical, spec=spec, matrix_rows=project_experiment_matrix(spec), spec_validator=ExperimentSpecValidator(lambda _: True),
            immutable_resolver=lambda _: True, repository_qualified=lambda _: True, authorization_validator=lambda *_: True,
        )
        self.assertIn("PRV1_PHYSICAL_ACQUISITION_REQUIRED", {item.rule_id for item in result.violations})

    def test_stream_completeness_keeps_edge_scope_and_reports_all_defects(self) -> None:
        requirements = (StreamRequirement("stream-alpha", "edge-alpha", "sensor-alpha", 1, 3),)
        first = b'{"fixture":"one"}'
        records = (
            StreamRecord("stream-alpha", "edge-alpha", "sensor-alpha", 2, first, "sha256:" + hashlib.sha256(first).hexdigest()),
            StreamRecord("stream-alpha", "edge-alpha", "sensor-alpha", 1, b"bad", digest(90)),
            StreamRecord("stream-alpha", "edge-alpha", "sensor-alpha", 2, b'{"fixture":"different"}', "sha256:" + hashlib.sha256(b'{"fixture":"different"}').hexdigest()),
            StreamRecord("stream-alpha", "edge-other", "sensor-alpha", 4, b"ok", "sha256:" + hashlib.sha256(b"ok").hexdigest()),
        )
        result = validate_stream_completeness(requirements, records)
        rules = {item.rule_id for item in result.defects}
        self.assertEqual(StreamStatus.INCOMPLETE, result.status)
        self.assertTrue({"PRV1_STREAM_MISSING", "PRV1_STREAM_OUT_OF_ORDER", "PRV1_STREAM_DIVERGENT_DUPLICATE", "PRV1_STREAM_HASH_MISMATCH", "PRV1_STREAM_SCOPE_MISMATCH"}.issubset(rules))
        self.assertEqual(records, result.retained_records)


if __name__ == "__main__":
    unittest.main()
