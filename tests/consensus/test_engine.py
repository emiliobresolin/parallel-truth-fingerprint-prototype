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


def make_payload(tag: str, value: float, unit: str) -> RawHartPayload:
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
            loop_current_ma=12.0,
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
) -> EdgeLocalReplicatedStateContract:
    participants = ("edge-1", "edge-2", "edge-3")
    return EdgeLocalReplicatedStateContract(
        round_identity=round_identity,
        owner_edge_id=owner_edge_id,
        participating_edges=participants,
        observations_by_sensor={
            "temperature": make_payload("TIT-101", temperature, "degC"),
            "pressure": make_payload("PIT-101", pressure, "bar"),
            "rpm": make_payload("RIT-101", rpm, "rpm"),
        },
        is_validated=False,
    )


class ConsensusEngineTest(unittest.TestCase):
    def setUp(self) -> None:
        start = datetime(2026, 3, 25, 12, 0, tzinfo=timezone.utc)
        self.round_identity = RoundIdentity(
            round_id="round-002",
            window_started_at=start,
            window_ended_at=start + timedelta(minutes=1),
        )

    def test_required_quorum_for_three_edges_is_two(self) -> None:
        self.assertEqual(required_quorum(3), 2)

    def test_successful_consensus_uses_simple_average_of_non_excluded_edges(self) -> None:
        round_input = ConsensusRoundInput(
            round_identity=self.round_identity,
            participating_edges=("edge-1", "edge-2", "edge-3"),
            replicated_states=(
                make_replicated_state(self.round_identity, "edge-1", 80.0, 6.0, 3200.0),
                make_replicated_state(self.round_identity, "edge-2", 82.0, 6.2, 3220.0),
                make_replicated_state(self.round_identity, "edge-3", 81.0, 6.1, 3210.0),
            ),
        )

        audit_package = ConsensusEngine().evaluate(round_input)

        self.assertEqual(audit_package.consensus_result.status, ConsensusStatus.SUCCESS)
        valid_state = audit_package.consensus_result.consensused_valid_state
        assert valid_state is not None
        self.assertEqual(valid_state.sensor_values["temperature"], 81.0)
        self.assertEqual(valid_state.sensor_values["pressure"], 6.1)
        self.assertEqual(valid_state.sensor_values["rpm"], 3210.0)

    def test_exclusions_below_quorum_produce_failed_consensus(self) -> None:
        round_input = ConsensusRoundInput(
            round_identity=self.round_identity,
            participating_edges=("edge-1", "edge-2", "edge-3"),
            replicated_states=(
                make_replicated_state(self.round_identity, "edge-1", 80.0, 6.0, 3200.0),
                make_replicated_state(self.round_identity, "edge-2", 150.0, 11.5, 5000.0),
                make_replicated_state(self.round_identity, "edge-3", 20.0, 1.0, 900.0),
            ),
        )

        audit_package = ConsensusEngine().evaluate(round_input)

        self.assertEqual(
            audit_package.consensus_result.status,
            ConsensusStatus.FAILED_CONSENSUS,
        )
        self.assertIsNone(audit_package.consensus_result.consensused_valid_state)
        self.assertGreaterEqual(len(audit_package.consensus_result.exclusions), 2)

    def test_failed_consensus_still_contains_ranking_and_exclusions(self) -> None:
        round_input = ConsensusRoundInput(
            round_identity=self.round_identity,
            participating_edges=("edge-1", "edge-2", "edge-3"),
            replicated_states=(
                make_replicated_state(self.round_identity, "edge-1", 80.0, 6.0, 3200.0),
                make_replicated_state(self.round_identity, "edge-2", 80.5, 6.1, 3210.0),
                make_replicated_state(self.round_identity, "edge-3", 120.0, 9.5, 4700.0),
            ),
        )

        audit_package = ConsensusEngine().evaluate(round_input)

        self.assertGreater(len(audit_package.consensus_result.trust_ranking.entries), 0)
        self.assertGreater(len(audit_package.consensus_result.exclusions), 0)
        self.assertIn(
            audit_package.consensus_result.exclusions[0].reason,
            (
                ExclusionReason.INCONSISTENT_VIEW,
                ExclusionReason.SUSPECTED_BYZANTINE_BEHAVIOR,
            ),
        )

    def test_trust_ranking_is_derived_from_pairwise_deviation(self) -> None:
        round_input = ConsensusRoundInput(
            round_identity=self.round_identity,
            participating_edges=("edge-1", "edge-2", "edge-3"),
            replicated_states=(
                make_replicated_state(self.round_identity, "edge-1", 80.0, 6.0, 3200.0),
                make_replicated_state(self.round_identity, "edge-2", 81.0, 6.1, 3210.0),
                make_replicated_state(self.round_identity, "edge-3", 120.0, 9.5, 4700.0),
            ),
        )

        audit_package = ConsensusEngine().evaluate(round_input)
        ranking_by_edge = {
            entry.edge_id: entry.score
            for entry in audit_package.consensus_result.trust_ranking.entries
        }

        self.assertGreater(ranking_by_edge["edge-1"], ranking_by_edge["edge-3"])
        self.assertGreater(ranking_by_edge["edge-2"], ranking_by_edge["edge-3"])

    def test_replay_style_stale_view_produces_detectable_inconsistency(self) -> None:
        round_input = ConsensusRoundInput(
            round_identity=self.round_identity,
            participating_edges=("edge-1", "edge-2", "edge-3"),
            replicated_states=(
                make_replicated_state(self.round_identity, "edge-1", 85.0, 6.8, 3400.0),
                make_replicated_state(self.round_identity, "edge-2", 84.5, 6.7, 3390.0),
                make_replicated_state(self.round_identity, "edge-3", 74.0, 5.7, 3080.0),
            ),
        )

        audit_package = ConsensusEngine().evaluate(round_input)
        excluded_edges = {decision.edge_id for decision in audit_package.consensus_result.exclusions}

        self.assertIn("edge-3", excluded_edges)

    def test_small_drift_reduces_trust_without_breaking_quorum(self) -> None:
        round_input = ConsensusRoundInput(
            round_identity=self.round_identity,
            participating_edges=("edge-1", "edge-2", "edge-3"),
            replicated_states=(
                make_replicated_state(self.round_identity, "edge-1", 80.0, 6.0, 3200.0),
                make_replicated_state(self.round_identity, "edge-2", 80.8, 6.08, 3208.0),
                make_replicated_state(self.round_identity, "edge-3", 83.5, 6.4, 3280.0),
            ),
        )

        audit_package = ConsensusEngine().evaluate(round_input)
        ranking_by_edge = {
            entry.edge_id: entry.score
            for entry in audit_package.consensus_result.trust_ranking.entries
        }

        self.assertEqual(audit_package.final_status, ConsensusStatus.SUCCESS)
        self.assertLess(ranking_by_edge["edge-3"], ranking_by_edge["edge-1"])

    def test_audit_package_contains_inputs_status_and_valid_state_only_on_success(self) -> None:
        round_input = ConsensusRoundInput(
            round_identity=self.round_identity,
            participating_edges=("edge-1", "edge-2", "edge-3"),
            replicated_states=(
                make_replicated_state(self.round_identity, "edge-1", 80.0, 6.0, 3200.0),
                make_replicated_state(self.round_identity, "edge-2", 82.0, 6.2, 3220.0),
                make_replicated_state(self.round_identity, "edge-3", 81.0, 6.1, 3210.0),
            ),
        )

        audit_package = ConsensusEngine().evaluate(round_input)

        self.assertEqual(audit_package.round_input, round_input)
        self.assertEqual(audit_package.final_status, ConsensusStatus.SUCCESS)
        self.assertIsNotNone(audit_package.consensus_result.consensused_valid_state)
        self.assertIsNotNone(audit_package.consensused_valid_state)


if __name__ == "__main__":
    unittest.main()
