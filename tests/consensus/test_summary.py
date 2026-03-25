import unittest
from datetime import datetime, timedelta, timezone

from parallel_truth_fingerprint.consensus.engine import ConsensusEngine
from parallel_truth_fingerprint.consensus.summary import (
    build_round_summary,
    format_round_summary,
)
from parallel_truth_fingerprint.contracts.consensus_round_input import ConsensusRoundInput
from parallel_truth_fingerprint.contracts.raw_hart_payload import (
    DeviceInfo,
    Diagnostics,
    PhysicsMetrics,
    ProcessData,
    ProcessVariable,
    RawHartPayload,
)
from parallel_truth_fingerprint.contracts.round_identity import RoundIdentity
from parallel_truth_fingerprint.edge_nodes.common.acquisition import (
    EdgeAcquisitionService,
    EDGE_DEVICE_CONFIGS,
)
from parallel_truth_fingerprint.contracts.edge_local_replicated_state import (
    EdgeLocalReplicatedStateContract,
)


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


class ConsensusSummaryTest(unittest.TestCase):
    def setUp(self) -> None:
        start = datetime(2026, 3, 25, 12, 0, tzinfo=timezone.utc)
        self.round_identity = RoundIdentity(
            round_id="round-visibility",
            window_started_at=start,
            window_ended_at=start + timedelta(minutes=1),
        )

    def test_summary_contains_required_fields_for_success(self) -> None:
        round_input = ConsensusRoundInput(
            round_identity=self.round_identity,
            participating_edges=("edge-1", "edge-2", "edge-3"),
            replicated_states=(
                make_replicated_state(self.round_identity, "edge-1", 80.0, 6.0, 3200.0),
                make_replicated_state(self.round_identity, "edge-2", 82.0, 6.2, 3220.0),
                make_replicated_state(self.round_identity, "edge-3", 81.0, 6.1, 3210.0),
            ),
        )

        summary = build_round_summary(ConsensusEngine().evaluate(round_input))

        self.assertEqual(summary.round_id, "round-visibility")
        self.assertEqual(summary.total_participants, 3)
        self.assertEqual(summary.quorum_required, 2)
        self.assertEqual(summary.valid_participants_after_exclusions, 3)
        self.assertEqual(summary.excluded_edge_ids, ())
        self.assertEqual(summary.exclusion_reasons, ())
        self.assertTrue(summary.has_consensused_valid_state)

    def test_failed_consensus_summary_is_explicit_and_deterministic(self) -> None:
        round_input = ConsensusRoundInput(
            round_identity=self.round_identity,
            participating_edges=("edge-1", "edge-2", "edge-3"),
            replicated_states=(
                make_replicated_state(self.round_identity, "edge-1", 80.0, 6.0, 3200.0),
                make_replicated_state(self.round_identity, "edge-2", 150.0, 11.5, 5000.0),
                make_replicated_state(self.round_identity, "edge-3", 20.0, 1.0, 900.0),
            ),
        )

        summary = build_round_summary(ConsensusEngine().evaluate(round_input))
        formatted = format_round_summary(summary)

        self.assertEqual(summary.valid_participants_after_exclusions, 1)
        self.assertFalse(summary.has_consensused_valid_state)
        self.assertEqual(summary.excluded_edge_ids, ("edge-2", "edge-3"))
        self.assertEqual(
            summary.exclusion_reasons,
            ("suspected_byzantine_behavior", "suspected_byzantine_behavior"),
        )
        self.assertIn("status=failed_consensus", formatted)
        self.assertIn("valid_state=absent", formatted)
        self.assertIn("edge-2:suspected_byzantine_behavior", formatted)

    def test_summary_serialization_is_stable(self) -> None:
        round_input = ConsensusRoundInput(
            round_identity=self.round_identity,
            participating_edges=("edge-1", "edge-2", "edge-3"),
            replicated_states=(
                make_replicated_state(self.round_identity, "edge-1", 80.0, 6.0, 3200.0),
                make_replicated_state(self.round_identity, "edge-2", 82.0, 6.2, 3220.0),
                make_replicated_state(self.round_identity, "edge-3", 81.0, 6.1, 3210.0),
            ),
        )

        summary = build_round_summary(ConsensusEngine().evaluate(round_input))

        self.assertEqual(summary.to_dict(), summary.to_dict())


class ReplicatedStateExportTest(unittest.TestCase):
    def test_edge_service_exports_replicated_state_contract(self) -> None:
        service = EdgeAcquisitionService(EDGE_DEVICE_CONFIGS["edge-1"])
        payload = make_payload("TIT-101", 80.0, "degC")
        service._replicated_state.update_from_payload(payload)

        round_identity = RoundIdentity(
            round_id="round-export",
            window_started_at=datetime(2026, 3, 25, 12, 0, tzinfo=timezone.utc),
            window_ended_at=datetime(2026, 3, 25, 12, 1, tzinfo=timezone.utc),
        )
        contract = service.replicated_state_contract(
            round_identity=round_identity,
            participating_edges=("edge-1", "edge-2", "edge-3"),
        )

        self.assertEqual(contract.owner_edge_id, "edge-1")
        self.assertFalse(contract.is_validated)
        self.assertIn("temperature", contract.observations_by_sensor)


if __name__ == "__main__":
    unittest.main()
