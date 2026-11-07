import unittest
from datetime import datetime, timedelta, timezone

from parallel_truth_fingerprint.contracts.consensus_status import ConsensusStatus
from parallel_truth_fingerprint.contracts.edge_local_replicated_state import (
    EdgeLocalReplicatedStateContract,
)
from parallel_truth_fingerprint.contracts.raw_hart_payload import (
    DeviceInfo,
    Diagnostics,
    PhysicsMetrics,
    ProcessData,
    ProcessVariable,
    RawHartPayload,
)
from parallel_truth_fingerprint.contracts.round_identity import RoundIdentity
from parallel_truth_fingerprint.contracts.consensus_round_input import ConsensusRoundInput
from parallel_truth_fingerprint.contracts.exclusion_reason import ExclusionReason
from parallel_truth_fingerprint.consensus.engine import ConsensusEngine
from parallel_truth_fingerprint.consensus.quorum import required_quorum


def make_payload(tag: str, value: float, unit: str, current_ma: float = 12.0) -> RawHartPayload:
    return RawHartPayload(
        protocol="HART",
        gateway_id="GW",
        timestamp="2026-03-25T12:00:00Z",
        device_info=DeviceInfo(
            tag=tag,
            long_tag=tag,
            manufacturer_id=1,
            device_type=1,
        ),
        process_data=ProcessData(
            pv=ProcessVariable(value=value, unit=unit),
            sv=ProcessVariable(value=65.0, unit="percent", description="Compressor_Power"),
            loop_current_ma=current_ma,
            pv_percent_range=50.0,
            physics_metrics=PhysicsMetrics(
                noise_floor=0.1,
                rate_of_change_dtdt=0.0,
                local_stability_score=1.0,
            ),
        ),
        diagnostics=Diagnostics(
            device_status_hex="0x00",
            field_device_malfunction=False,
            loop_current_saturated=False,
            cold_start=False,
        ),
    )


def make_replicated_state(
    round_identity: RoundIdentity,
    owner_edge_id: str,
    temperature: float,
    pressure: float,
    rpm: float,
    currents: tuple[float, float, float] = (12.0, 12.0, 12.0),
) -> EdgeLocalReplicatedStateContract:
    participants = ("edge-1", "edge-2", "edge-3")
    return EdgeLocalReplicatedStateContract(
        round_identity=round_identity,
        owner_edge_id=owner_edge_id,
        participating_edges=participants,
        observations_by_sensor={
            "temperature": make_payload("TIT-101", temperature, "degC", currents[0]),
            "pressure": make_payload("PIT-101", pressure, "bar", currents[1]),
            "rpm": make_payload("RIT-101", rpm, "rpm", currents[2]),
        },
        is_validated=False,
    )


class ConsensusEngineTest(unittest.TestCase):
    def setUp(self):
        start = datetime(2026, 3, 25, 12, 0, tzinfo=timezone.utc)
        self.round_identity = RoundIdentity("round-current", start, start + timedelta(minutes=1))

    def evaluate(self, currents=(12.0, 12.0, 12.0), *, pv_values=None, stale=False):
        from dataclasses import replace
        ids = tuple(f"edge-{i+1}" for i in range(len(currents)))
        states = []
        for index, (edge, current) in enumerate(zip(ids, currents)):
            pv = (pv_values or [80.0] * len(ids))[index]
            state = make_replicated_state(self.round_identity, edge, pv, 6.0, 3200.0, currents=(current,) * 3)
            state = replace(state, participating_edges=ids)
            if stale and index == len(ids)-1:
                obs = dict(state.observations_by_sensor)
                obs["temperature"] = replace(obs["temperature"], timestamp="2026-03-25T11:59:00Z")
                state = replace(state, observations_by_sensor=obs)
            states.append(state)
        return ConsensusEngine().evaluate(ConsensusRoundInput(self.round_identity, ids, tuple(states)))

    def test_required_quorum_is_strictly_above_two_thirds(self):
        self.assertEqual([required_quorum(n) for n in (1, 2, 3, 4, 6)], [1, 2, 3, 3, 5])

    def test_success_retains_exact_acquired_current_without_averaging(self):
        audit = self.evaluate((12.123456789,) * 3)
        self.assertEqual(audit.final_status, ConsensusStatus.SUCCESS)
        self.assertEqual(audit.consensused_valid_state.sensor_values, dict.fromkeys(("temperature", "pressure", "rpm"), 12.123456789))
        self.assertEqual(audit.consensused_valid_state.measurement_domain, "loop_current_ma")

    def test_engineering_pv_changes_do_not_change_decision_or_scores(self):
        normal = self.evaluate()
        changed = self.evaluate(pv_values=[-1000.0, 3000.0, 999999.0])
        self.assertEqual(normal.consensus_result, changed.consensus_result)
        self.assertEqual(normal.trust_evidence, changed.trust_evidence)

    def test_current_only_disagreement_fails_three_edge_quorum(self):
        audit = self.evaluate((12.0, 12.0, 16.0))
        self.assertEqual(audit.final_status, ConsensusStatus.FAILED_CONSENSUS)
        self.assertIsNone(audit.consensused_valid_state)
        self.assertEqual(len(audit.exclusions), 3)

    def test_failed_round_retains_advisory_ranking_and_evidence(self):
        audit = self.evaluate((4.0, 12.0, 20.0))
        self.assertEqual(len(audit.trust_ranking.entries), 3)
        self.assertEqual(len(audit.trust_evidence), 3)
        self.assertTrue(all(ex.reason == ExclusionReason.INCONSISTENT_VIEW for ex in audit.exclusions))
        self.assertTrue(all(d.unit == "mA" for e in audit.trust_evidence for d in e.sensor_deviations))

    def test_advisory_ranking_uses_sixteen_ma_span(self):
        audit = self.evaluate((12.0, 12.0, 20.0))
        evidence = {e.edge_id: e for e in audit.trust_evidence}
        self.assertEqual(evidence["edge-1"].overall_normalized_deviation, 0.25)
        self.assertEqual(evidence["edge-3"].overall_normalized_deviation, 0.5)
        self.assertEqual(evidence["edge-1"].score, 0.8)
        self.assertEqual(evidence["edge-3"].score, 0.667)

    def test_same_value_different_source_event_is_incompatible(self):
        audit = self.evaluate(stale=True)
        self.assertEqual(audit.final_status, ConsensusStatus.FAILED_CONSENSUS)
        self.assertEqual(audit.trust_evidence[-1].compatible_peer_count, 0)
        self.assertEqual(audit.trust_evidence[-1].overall_normalized_deviation, 0.0)

    def test_tiny_current_drift_is_detected_even_when_score_rounds_to_one(self):
        audit = self.evaluate((12.0, 12.0, 12.0000001))
        self.assertEqual(audit.final_status, ConsensusStatus.FAILED_CONSENSUS)
        self.assertTrue(all(entry.score == 1.0 for entry in audit.trust_ranking.entries))

    def test_three_of_four_agreeing_copies_succeed(self):
        audit = self.evaluate((12.0, 12.0, 12.0, 18.0))
        self.assertEqual(audit.final_status, ConsensusStatus.SUCCESS)
        self.assertEqual(audit.consensused_valid_state.source_edges, ("edge-1", "edge-2", "edge-3"))
        self.assertEqual(tuple(ex.edge_id for ex in audit.exclusions), ("edge-4",))

    def test_two_against_two_fails(self):
        audit = self.evaluate((12.0, 12.0, 18.0, 18.0))
        self.assertEqual(audit.final_status, ConsensusStatus.FAILED_CONSENSUS)
        self.assertIsNone(audit.consensused_valid_state)

    def test_nonfinite_current_is_blocked(self):
        for current in (float("nan"), float("inf"), float("-inf")):
            with self.subTest(current=current), self.assertRaises(ValueError):
                self.evaluate((current,) * 3)

    def test_unknown_current_is_blocked(self):
        from dataclasses import replace
        state = make_replicated_state(self.round_identity, "edge-1", 80, 6, 3200)
        payload = state.observations_by_sensor["temperature"]
        payload = replace(payload, process_data=replace(payload.process_data, loop_current_ma=None))
        state = replace(state, participating_edges=("edge-1",), observations_by_sensor={"temperature": payload})
        with self.assertRaises((ValueError, TypeError)):
            ConsensusEngine().evaluate(ConsensusRoundInput(self.round_identity, ("edge-1",), (state,)))

    def test_audit_package_contains_inputs_status_and_selected_state(self):
        audit = self.evaluate()
        self.assertEqual(audit.round_input.round_identity, self.round_identity)
        self.assertEqual(audit.final_status, ConsensusStatus.SUCCESS)
        self.assertEqual(audit.consensus_result.consensused_valid_state, audit.consensused_valid_state)


if __name__ == "__main__":
    unittest.main()
