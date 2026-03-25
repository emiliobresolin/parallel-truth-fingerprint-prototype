import unittest
from datetime import datetime, timedelta, timezone

from parallel_truth_fingerprint.contracts.raw_hart_payload import (
    DeviceInfo,
    Diagnostics,
    PhysicsMetrics,
    ProcessData,
    ProcessVariable,
    RawHartPayload,
)
from parallel_truth_fingerprint.contracts.consensus_status import ConsensusStatus
from parallel_truth_fingerprint.contracts.exclusion_reason import ExclusionReason
from parallel_truth_fingerprint.contracts.round_identity import RoundIdentity
from parallel_truth_fingerprint.contracts.edge_local_replicated_state import (
    EdgeLocalReplicatedStateContract,
)
from parallel_truth_fingerprint.contracts.consensused_valid_state import (
    ConsensusedValidState,
)
from parallel_truth_fingerprint.contracts.consensus_round_input import (
    ConsensusRoundInput,
)
from parallel_truth_fingerprint.contracts.exclusion_decision import ExclusionDecision
from parallel_truth_fingerprint.contracts.trust_ranking import TrustRankEntry, TrustRanking
from parallel_truth_fingerprint.contracts.consensus_result import ConsensusResult


class ConsensusContractsTest(unittest.TestCase):
    def setUp(self) -> None:
        start = datetime(2026, 3, 25, 10, 0, tzinfo=timezone.utc)
        self.round_identity = RoundIdentity(
            round_id="round-001",
            window_started_at=start,
            window_ended_at=start + timedelta(minutes=1),
        )
        self.raw_observation = RawHartPayload(
            protocol="HART",
            gateway_id="GW-EDGE-01",
            timestamp="2026-03-25T10:00:00Z",
            device_info=DeviceInfo(
                tag="TIT-101",
                long_tag="Temperature_Compressor_Casing",
                manufacturer_id=26,
                device_type=33,
            ),
            process_data=ProcessData(
                pv=ProcessVariable(value=78.254, unit="degC", unit_code=32),
                sv=ProcessVariable(
                    value=67.0,
                    unit="percent",
                    description="Compressor_Power",
                ),
                loop_current_ma=14.3,
                pv_percent_range=64.2,
                physics_metrics=PhysicsMetrics(
                    noise_floor=0.42,
                    rate_of_change_dtdt=0.5,
                    local_stability_score=0.91,
                ),
            ),
            diagnostics=Diagnostics(
                device_status_hex="0x00",
                field_device_malfunction=False,
                loop_current_saturated=False,
                cold_start=False,
            ),
        )
        self.replicated_state = EdgeLocalReplicatedStateContract(
            round_identity=self.round_identity,
            owner_edge_id="edge-1",
            participating_edges=("edge-1", "edge-2", "edge-3"),
            observations_by_sensor={
                "temperature": self.raw_observation,
            },
            is_validated=False,
        )

    def test_state_types_are_explicit_and_distinct(self) -> None:
        consensused = ConsensusedValidState(
            round_identity=self.round_identity,
            source_edges=("edge-1", "edge-2"),
            sensor_values={
                "temperature": 78.254,
                "pressure": 6.253,
                "rpm": 3234.344,
            },
        )

        self.assertIsInstance(self.raw_observation, RawHartPayload)
        self.assertIsInstance(self.replicated_state, EdgeLocalReplicatedStateContract)
        self.assertIsInstance(consensused, ConsensusedValidState)
        self.assertNotEqual(type(self.raw_observation), type(self.replicated_state))
        self.assertNotEqual(type(self.replicated_state), type(consensused))

    def test_consensus_round_input_accepts_only_replicated_state(self) -> None:
        round_input = ConsensusRoundInput(
            round_identity=self.round_identity,
            participating_edges=("edge-1", "edge-2", "edge-3"),
            replicated_states=(self.replicated_state,),
        )

        self.assertEqual(round_input.round_identity.round_id, "round-001")
        self.assertEqual(round_input.replicated_states[0].owner_edge_id, "edge-1")

    def test_exclusion_decision_is_round_scoped_and_uses_bounded_reason(self) -> None:
        decision = ExclusionDecision(
            round_identity=self.round_identity,
            edge_id="edge-3",
            reason=ExclusionReason.SUSPECTED_BYZANTINE_BEHAVIOR,
            detail="inconsistent payload timestamp window",
        )

        self.assertEqual(decision.round_identity.round_id, "round-001")
        self.assertEqual(decision.reason, ExclusionReason.SUSPECTED_BYZANTINE_BEHAVIOR)
        self.assertEqual(decision.edge_id, "edge-3")

    def test_failed_consensus_has_no_valid_state(self) -> None:
        ranking = TrustRanking(
            round_identity=self.round_identity,
            participating_edges=("edge-1", "edge-2"),
            entries=(
                TrustRankEntry(edge_id="edge-1", score=0.89),
                TrustRankEntry(edge_id="edge-2", score=0.42),
            ),
        )
        exclusion = ExclusionDecision(
            round_identity=self.round_identity,
            edge_id="edge-2",
            reason=ExclusionReason.TRUST_BELOW_THRESHOLD,
        )

        result = ConsensusResult(
            round_identity=self.round_identity,
            status=ConsensusStatus.FAILED_CONSENSUS,
            participating_edges=("edge-1", "edge-2"),
            trust_ranking=ranking,
            exclusions=(exclusion,),
            consensused_valid_state=None,
        )

        self.assertEqual(result.status, ConsensusStatus.FAILED_CONSENSUS)
        self.assertIsNone(result.consensused_valid_state)

    def test_success_consensus_requires_valid_state(self) -> None:
        ranking = TrustRanking(
            round_identity=self.round_identity,
            participating_edges=("edge-1", "edge-2"),
            entries=(
                TrustRankEntry(edge_id="edge-1", score=0.95),
                TrustRankEntry(edge_id="edge-2", score=0.91),
            ),
        )
        valid_state = ConsensusedValidState(
            round_identity=self.round_identity,
            source_edges=("edge-1", "edge-2"),
            sensor_values={
                "temperature": 78.254,
                "pressure": 6.253,
                "rpm": 3234.344,
            },
        )

        result = ConsensusResult(
            round_identity=self.round_identity,
            status=ConsensusStatus.SUCCESS,
            participating_edges=("edge-1", "edge-2"),
            trust_ranking=ranking,
            exclusions=(),
            consensused_valid_state=valid_state,
        )

        self.assertEqual(result.status, ConsensusStatus.SUCCESS)
        self.assertIsNotNone(result.consensused_valid_state)

    def test_trust_ranking_references_only_participating_edges(self) -> None:
        ranking = TrustRanking(
            round_identity=self.round_identity,
            participating_edges=("edge-1", "edge-2"),
            entries=(
                TrustRankEntry(edge_id="edge-1", score=0.8),
                TrustRankEntry(edge_id="edge-2", score=0.7),
            ),
        )

        self.assertEqual(tuple(entry.edge_id for entry in ranking.entries), ("edge-1", "edge-2"))


if __name__ == "__main__":
    unittest.main()
