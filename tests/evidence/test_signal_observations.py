import hashlib
import json
import unittest

from parallel_truth_fingerprint.contracts.signal_observation import SignalObservationError, observation_content_id, parse_signal_observation, parse_signal_observation_json


def digest(n: int) -> str:
    return "sha256:" + f"{n:064x}"


def ref(n: int) -> dict:
    return {"revision_id": digest(n), "serialized_sha256": digest(n + 1), "subject_sha256": None, "contract_id": "Fixture", "contract_version": "v1", "locator": "fixture", "evidence_role": "fixture_test"}


def sample() -> dict:
    uses = [{"role": "quality", "target_revision_ref": ref(30), "target_bytes_hash": digest(32)}]
    derivation = {"direction": "current_to_normalized", "transform_revision_ref": ref(40), "profile_revision_ref": ref(42), "input_representation": "raw_current_ma", "output_representation": "normalized_span", "parameter_uses": uses}
    unavailable = {"state": "unavailable", "reason": "fixture_unknown"}
    base = {"contract_id": "SignalObservation", "schema_version": 2, "schema_ref": ref(1), "record_role": "primary_per_edge", "audience_access_class": "detector_facing", "semantic_identity": {"modality": "physical_instrumentation"}, "source_sequence": 1, "correlation": {"correlation_id": digest(51), "evidence_state": "unknown", "method": unavailable, "measured_uncertainty": unavailable}, "source_timestamp": "2026-01-01T00:00:00.000000Z", "observed_timestamp": "2026-01-01T00:00:01.000000Z", "clock": {"source_clock_id": digest(52), "observed_clock_id": digest(53), "evidence_status": "unknown", "method": unavailable, "measured_offset": unavailable, "measured_uncertainty": unavailable, "qualification_policy": unavailable}, "profile_binding": {"profile_id": digest(50), "profile_revision_ref": ref(54), "profile_canonical_bytes_hash": digest(56), "catalog_snapshot_ref": ref(57), "catalog_snapshot_hash": digest(59), "parameter_gate_result_ref": ref(60), "consumed_parameters": uses}, "raw_current": {"state": "present", "value": "3.5", "unit": "mA"}, "diagnostics": [], "quality_trace": {"outcome": "under_range", "conversion_disposition": "convert", "applied_rule_ids": ["rule"], "diagnostic_ids_used": [], "parameter_uses": uses}, "normalized_span": {"state": "derived", "value": "-0.1", "quantity_kind": "normalized_span", "unit": "one", "derivation": derivation}, "engineering_value": {"state": "derived", "value": "1", "quantity_kind": "fixture_quantity", "unit": "fixture_unit", "derivation": {**derivation, "direction": "current_to_engineering_or_reference", "output_representation": "engineering_value"}}}
    for index, name in enumerate(("experiment_id", "run_id", "round_id", "edge_id", "sensor_id", "source_stream_id", "source_boot_id", "source_session_id", "event_id"), 60): base[name] = digest(index)
    base["observation_content_id"] = observation_content_id(base)
    return base


class SignalObservationTests(unittest.TestCase):
    def test_parses_and_hashes_canonical_preimage(self):
        payload = sample()
        observation = parse_signal_observation(payload)
        expected = "sha256:" + hashlib.sha256(json.dumps({k:v for k,v in payload.items() if k != "observation_content_id"}, ensure_ascii=True, sort_keys=True, separators=(",", ":")).encode("ascii")).hexdigest()
        self.assertEqual(observation.to_dict()["observation_content_id"], expected)
        self.assertEqual(observation.sequence_key[-1], 1)

    def test_rejects_numeric_raw_and_hash_tampering(self):
        payload = sample(); payload["raw_current"] = {"state": "present", "value": 3, "unit": "mA"}
        with self.assertRaises(SignalObservationError) as caught: parse_signal_observation(payload)
        self.assertEqual(caught.exception.violation.family, "SOV2_RAW_CURRENT_PRIMARY")
        payload = sample(); payload["observation_content_id"] = digest(99)
        with self.assertRaises(SignalObservationError) as caught: parse_signal_observation(payload)
        self.assertEqual(caught.exception.violation.family, "SOV2_CONTENT_ID")

    def test_rejects_duplicate_unknown_and_wrong_representation_state(self):
        with self.assertRaises(SignalObservationError) as caught: parse_signal_observation_json('{"contract_id":"SignalObservation","contract_id":"SignalObservation"}')
        self.assertEqual(caught.exception.violation.token, "duplicate_field")
        payload = sample(); payload["aggregate"] = []
        with self.assertRaises(SignalObservationError) as caught: parse_signal_observation(payload)
        self.assertEqual(caught.exception.violation.family, "SOV2_SCHEMA_VERSION_TOKEN")
        payload = sample(); payload["quality_trace"]["conversion_disposition"] = "no_numeric_value"; payload["observation_content_id"] = observation_content_id(payload)
        with self.assertRaises(SignalObservationError) as caught: parse_signal_observation(payload)
        self.assertEqual(caught.exception.violation.family, "SOV2_REPRESENTATION_RECOMPUTE")
