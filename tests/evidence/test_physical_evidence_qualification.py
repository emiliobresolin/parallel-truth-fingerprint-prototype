"""Offline tests for the narrow Story 10.7 G2 qualification gate."""
from __future__ import annotations

import unittest

from parallel_truth_fingerprint.contracts.physical_evidence_qualification import QualificationDisposition
from parallel_truth_fingerprint.contracts.signal_observation import observation_content_id, parse_signal_observation
from parallel_truth_fingerprint.evidence.physical_evidence_qualification import (
    FeatureProjection, PhysicalQualificationInput, ProjectionComparison, qualify_physical_evidence,
)
from parallel_truth_fingerprint.evidence.scenario_truth_validation import ReferenceDescriptor


def digest(number: int) -> str: return "sha256:" + f"{number:064x}"
def ref(number: int) -> dict[str, object]: return {"revision_id": digest(number), "serialized_sha256": digest(number + 100), "subject_sha256": None, "contract_id": "Fixture", "contract_version": "v1", "locator": "fixture", "evidence_role": "fixture"}

def observation() -> object:
    use = [{"role": "fixture", "target_revision_ref": ref(30), "target_bytes_hash": digest(32)}]
    derivation = {"direction": "current_to_normalized", "transform_revision_ref": ref(40), "profile_revision_ref": ref(42), "input_representation": "raw_current_ma", "output_representation": "normalized_span", "parameter_uses": use}
    unavailable = {"state": "unavailable", "reason": "fixture"}
    payload: dict[str, object] = {"contract_id": "SignalObservation", "schema_version": 2, "schema_ref": ref(1), "record_role": "primary_per_edge", "audience_access_class": "detector_facing", "semantic_identity": {"modality": "fixture"}, "source_sequence": 1, "correlation": {"correlation_id": digest(51), "evidence_state": "unknown", "method": unavailable, "measured_uncertainty": unavailable}, "source_timestamp": "2026-01-01T00:00:00.000000Z", "observed_timestamp": "2026-01-01T00:00:01.000000Z", "clock": {"source_clock_id": digest(52), "observed_clock_id": digest(53), "evidence_status": "unknown", "method": unavailable, "measured_offset": unavailable, "measured_uncertainty": unavailable, "qualification_policy": unavailable}, "profile_binding": {"profile_id": digest(50), "profile_revision_ref": ref(54), "profile_canonical_bytes_hash": digest(56), "catalog_snapshot_ref": ref(57), "catalog_snapshot_hash": digest(59), "parameter_gate_result_ref": ref(60), "consumed_parameters": use}, "raw_current": {"state": "present", "value": "3.5", "unit": "mA"}, "diagnostics": [], "quality_trace": {"outcome": "under_range", "conversion_disposition": "convert", "applied_rule_ids": ["fixture"], "diagnostic_ids_used": [], "parameter_uses": use}, "normalized_span": {"state": "derived", "value": "-0.1", "quantity_kind": "normalized_span", "unit": "one", "derivation": derivation}, "engineering_value": {"state": "derived", "value": "1", "quantity_kind": "fixture_quantity", "unit": "fixture_unit", "derivation": {**derivation, "direction": "current_to_engineering_or_reference", "output_representation": "engineering_value"}}}
    for number, field in enumerate(("experiment_id", "run_id", "round_id", "edge_id", "sensor_id", "source_stream_id", "source_boot_id", "source_session_id", "event_id"), 60): payload[field] = digest(number)
    payload["observation_content_id"] = observation_content_id(payload)
    return parse_signal_observation(payload)

class PhysicalEvidenceQualificationTests(unittest.TestCase):
    def candidate(self, **changes: object) -> PhysicalQualificationInput:
        item = observation(); body = item.to_dict()
        projection = ProjectionComparison(FeatureProjection(digest(200), digest(201), ("fixture-feature",), b"fixture"), FeatureProjection(digest(202), digest(201), ("fixture-feature",), b"fixture"), digest(203), True)
        values: dict[str, object] = dict(run_manifest_id=digest(210), run_receipt_id=digest(211), actual_run_status="complete", execution_modality="admitted_emulator", closure_ids=(digest(212),), observations=(item,), expected_observation_ids=(body["observation_content_id"],), experiment_id=body["experiment_id"], run_id=body["run_id"], expected_stream_ids=(body["source_stream_id"],), public_boundary={"closure": digest(212)}, limitations=("Non-domain fixture.",), projection_comparison=projection)
        values.update(changes); return PhysicalQualificationInput(**values)
    def resolve(self, _: str) -> bool: return True
    def boundary(self, identity: str) -> ReferenceDescriptor: return ReferenceDescriptor(identity, "detector_facing", "public", True)
    def test_complete_exact_public_closure_is_qualified(self) -> None:
        result = qualify_physical_evidence(self.candidate(), immutable_resolver=self.resolve, boundary_resolver=self.boundary)
        self.assertEqual(QualificationDisposition.QUALIFIED, result.disposition)
        self.assertEqual(result.result_content_id, __import__("parallel_truth_fingerprint.contracts.physical_evidence_qualification", fromlist=["physical_evidence_qualification_content_id"]).physical_evidence_qualification_content_id(result))
    def test_missing_final_receipt_is_visible_incomplete(self) -> None:
        result = qualify_physical_evidence(self.candidate(run_receipt_id=None), immutable_resolver=self.resolve, boundary_resolver=self.boundary)
        self.assertEqual(QualificationDisposition.INCOMPLETE, result.disposition)
    def test_bad_run_identity_and_missing_tolerance_fail_closed(self) -> None:
        projection = ProjectionComparison(None, None, None, False)
        result = qualify_physical_evidence(self.candidate(run_id=digest(999), projection_comparison=projection), immutable_resolver=self.resolve, boundary_resolver=self.boundary)
        self.assertEqual(QualificationDisposition.INCOMPLETE, result.disposition)
        self.assertIn("PEQ2_OBSERVATION_RUN_MISMATCH", {code for check in result.checks for code in check.diagnostic_codes})
    def test_declared_truth_taint_is_not_qualified(self) -> None:
        def tainted(identity: str) -> ReferenceDescriptor: return ReferenceDescriptor(identity, "evaluator_restricted", "restricted_truth", True)
        result = qualify_physical_evidence(self.candidate(), immutable_resolver=self.resolve, boundary_resolver=tainted)
        self.assertEqual(QualificationDisposition.NOT_QUALIFIED, result.disposition)
        self.assertIn("STV1-PUBLIC-RESTRICTED-TAINT", {code for check in result.checks for code in check.diagnostic_codes})

if __name__ == "__main__": unittest.main()
