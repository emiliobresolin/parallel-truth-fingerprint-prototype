from __future__ import annotations

import unittest

from parallel_truth_fingerprint.contracts.signal_observation import observation_content_id, parse_signal_observation
from parallel_truth_fingerprint.edge_nodes.common.signal_acquisition import EdgeSignalObservationView, SignalEdgeBinding
from parallel_truth_fingerprint.edge_nodes.common.signal_mqtt import (InMemorySignalMqtt, SignalMqttTransportPolicy, bind_signal_observation_v2_receiver, publish_signal_observation_v2)
from parallel_truth_fingerprint.evidence.signal_observations import SignalObservationResolver
from parallel_truth_fingerprint.sensor_simulation.process_physics import EngineeringChannel
from parallel_truth_fingerprint.sensor_simulation.transmitter import TransmitterAssignment, compose_signal_observation


def digest(n: int) -> str: return "sha256:" + f"{n:064x}"
def ref(n: int) -> dict: return {"revision_id": digest(n), "serialized_sha256": digest(n+1), "subject_sha256": None, "contract_id": "Fixture", "contract_version": "v1", "locator": "fixture", "evidence_role": "fixture_test"}


def payload() -> dict:
    uses = [{"role": "quality", "target_revision_ref": ref(30), "target_bytes_hash": digest(32)}]
    derivation = {"direction": "current_to_normalized", "transform_revision_ref": ref(40), "profile_revision_ref": ref(42), "input_representation": "raw_current_ma", "output_representation": "normalized_span", "parameter_uses": uses}
    unavailable = {"state": "unavailable", "reason": "fixture_unknown"}
    value = {"contract_id": "SignalObservation", "schema_version": 2, "schema_ref": ref(1), "record_role": "primary_per_edge", "audience_access_class": "detector_facing", "semantic_identity": {"modality": "physical_instrumentation"}, "source_sequence": 1, "correlation": {"correlation_id": digest(51), "evidence_state": "unknown", "method": unavailable, "measured_uncertainty": unavailable}, "source_timestamp": "2026-01-01T00:00:00.000000Z", "observed_timestamp": "2026-01-01T00:00:01.000000Z", "clock": {"source_clock_id": digest(52), "observed_clock_id": digest(53), "evidence_status": "unknown", "method": unavailable, "measured_offset": unavailable, "measured_uncertainty": unavailable, "qualification_policy": unavailable}, "profile_binding": {"profile_id": digest(50), "profile_revision_ref": ref(54), "profile_canonical_bytes_hash": digest(56), "catalog_snapshot_ref": ref(57), "catalog_snapshot_hash": digest(59), "parameter_gate_result_ref": ref(60), "consumed_parameters": uses}, "raw_current": {"state": "present", "value": "3.5", "unit": "mA"}, "diagnostics": [], "quality_trace": {"outcome": "under_range", "conversion_disposition": "convert", "applied_rule_ids": ["rule"], "diagnostic_ids_used": [], "parameter_uses": uses}, "normalized_span": {"state": "derived", "value": "-0.1", "quantity_kind": "normalized_span", "unit": "one", "derivation": derivation}, "engineering_value": {"state": "derived", "value": "1", "quantity_kind": "fixture_quantity", "unit": "fixture_unit", "derivation": {**derivation, "direction": "current_to_engineering_or_reference", "output_representation": "engineering_value"}}}
    for n, name in enumerate(("experiment_id", "run_id", "round_id", "edge_id", "sensor_id", "source_stream_id", "source_boot_id", "source_session_id", "event_id"), 60): value[name] = digest(n)
    value["observation_content_id"] = observation_content_id(value)
    return value


def resolver() -> SignalObservationResolver:
    return SignalObservationResolver("fixture", lambda _: True, lambda _: True, lambda _: True, lambda *_: True, lambda data: {key: data[key] for key in ("quality_trace", "normalized_span", "engineering_value")})


class SignalV2RouteTests(unittest.TestCase):
    def test_transmitter_uses_one_injected_forward_conversion(self) -> None:
        facts = payload(); facts.pop("observation_content_id"); facts.pop("raw_current")
        for key in ("quality_trace", "normalized_span", "engineering_value"):
            facts.pop(key)
        calls = []
        expected = payload()
        transmitter_resolver = SignalObservationResolver(
            "fixture", lambda _: True, lambda _: True, lambda _: True, lambda *_: True,
            lambda _: {key: expected[key] for key in ("quality_trace", "normalized_span", "engineering_value")},
        )
        channel = EngineeringChannel("fixture-channel", "fixture_quantity", "fixture_unit", "1", "trace", "gate", "mock", "present")
        observation = compose_signal_observation(
            channel,
            assignment=TransmitterAssignment("fixture-channel", facts["edge_id"], facts["sensor_id"], "fixture_quantity", "fixture_unit", facts["profile_binding"]["profile_id"]),
            raw_facts=facts,
            engineering_or_reference_to_current=lambda value: (calls.append(value) or "3.5"),
            resolver=transmitter_resolver,
        )
        self.assertEqual(calls, [1]); self.assertEqual(observation.to_dict()["raw_current"]["value"], "3.5")

    def test_canonical_bytes_cross_transport_and_mutate_only_after_validation(self) -> None:
        observation = parse_signal_observation(payload()); data = observation.to_dict()
        view = EdgeSignalObservationView(SignalEdgeBinding(data["edge_id"], data["sensor_id"], data["profile_binding"]["profile_id"]))
        relay = InMemorySignalMqtt(); results = []
        bind_signal_observation_v2_receiver(subscriber=relay, view=view, policy=SignalMqttTransportPolicy("fixture"), resolver=resolver(), on_result=results.append)
        sent = publish_signal_observation_v2(observation, publisher=relay, policy=SignalMqttTransportPolicy("fixture"), resolver=resolver())
        self.assertTrue(sent.accepted); self.assertTrue(results[-1].accepted); self.assertEqual(len(view.observations()), 1)
        relay.publish(topic="physical/observations/v2", publisher_id="forged", payload=b'{"contract_id":"SignalObservation"}')
        self.assertFalse(results[-1].accepted); self.assertEqual(len(view.observations()), 1)

    def test_noncanonical_bytes_are_rejected_without_delivery(self) -> None:
        observation = parse_signal_observation(payload()); data = observation.to_dict()
        view = EdgeSignalObservationView(SignalEdgeBinding(data["edge_id"], data["sensor_id"], data["profile_binding"]["profile_id"]))
        relay = InMemorySignalMqtt(); results = []
        bind_signal_observation_v2_receiver(subscriber=relay, view=view, policy=SignalMqttTransportPolicy("fixture"), resolver=resolver(), on_result=results.append)
        relay.publish(topic="physical/observations/v2", publisher_id="forged", payload=str(observation.to_dict()).encode())
        self.assertFalse(results[-1].accepted); self.assertEqual(len(view.observations()), 0)
