import unittest
from datetime import datetime, timedelta, timezone

from parallel_truth_fingerprint.consensus import (
    ConsensusEngine,
    build_round_log,
    format_round_log_compact,
    format_round_log_detailed,
)
from parallel_truth_fingerprint.contracts.consensus_round_input import ConsensusRoundInput
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


class ConsensusLoggingTest(unittest.TestCase):
    def setUp(self) -> None:
        start = datetime(2026, 3, 25, 12, 0, tzinfo=timezone.utc)
        self.round_identity = RoundIdentity(
            round_id="round-log",
            window_started_at=start,
            window_ended_at=start + timedelta(minutes=1),
        )

    def test_round_log_contains_structured_trust_evidence(self) -> None:
        round_input = ConsensusRoundInput(
            round_identity=self.round_identity,
            participating_edges=("edge-1", "edge-2", "edge-3"),
            replicated_states=(
                make_replicated_state(self.round_identity, "edge-1", 80.0, 6.0, 3200.0),
                make_replicated_state(self.round_identity, "edge-2", 82.0, 6.2, 3220.0),
                make_replicated_state(self.round_identity, "edge-3", 81.0, 6.1, 3210.0),
            ),
        )

        round_log = build_round_log(ConsensusEngine().evaluate(round_input))

        self.assertEqual(round_log.round_identity.round_id, "round-log")
        self.assertEqual(round_log.participating_edges, ("edge-1", "edge-2", "edge-3"))
        self.assertEqual(len(round_log.trust_evidence), 3)
        self.assertGreaterEqual(len(round_log.trust_evidence[0].pairwise_distances), 6)
        self.assertEqual(round_log.trust_evidence[0].compatible_peer_count, 2)
        self.assertEqual(
            tuple(deviation.sensor_name for deviation in round_log.trust_evidence[0].sensor_deviations),
            ("temperature", "pressure", "rpm"),
        )
        self.assertEqual(
            tuple(deviation.unit for deviation in round_log.trust_evidence[0].sensor_deviations),
            ("degC", "bar", "rpm"),
        )

    def test_excluded_edge_log_includes_reason_and_numeric_evidence(self) -> None:
        round_input = ConsensusRoundInput(
            round_identity=self.round_identity,
            participating_edges=("edge-1", "edge-2", "edge-3"),
            replicated_states=(
                make_replicated_state(self.round_identity, "edge-1", 80.0, 6.0, 3200.0),
                make_replicated_state(self.round_identity, "edge-2", 80.5, 6.1, 3210.0),
                make_replicated_state(self.round_identity, "edge-3", 120.0, 9.5, 4700.0),
            ),
        )

        round_log = build_round_log(ConsensusEngine().evaluate(round_input))
        detailed = format_round_log_detailed(round_log)

        self.assertEqual(round_log.exclusions[0].edge_id, "edge-3")
        self.assertEqual(round_log.exclusions[0].reason.value, "suspected_byzantine_behavior")
        excluded_evidence = next(
            evidence for evidence in round_log.trust_evidence if evidence.edge_id == "edge-3"
        )
        self.assertEqual(excluded_evidence.sensor_deviations[0].deviation_value, 39.75)
        self.assertIn("excluded=edge-3 reason=suspected_byzantine_behavior", detailed)
        self.assertIn("temperature=39.750 degC", detailed)
        self.assertIn("edge-1:temperature=40.000 degC", detailed)

    def test_round_log_serialization_is_deterministic(self) -> None:
        round_input = ConsensusRoundInput(
            round_identity=self.round_identity,
            participating_edges=("edge-1", "edge-2", "edge-3"),
            replicated_states=(
                make_replicated_state(self.round_identity, "edge-1", 80.0, 6.0, 3200.0),
                make_replicated_state(self.round_identity, "edge-2", 82.0, 6.2, 3220.0),
                make_replicated_state(self.round_identity, "edge-3", 81.0, 6.1, 3210.0),
            ),
        )

        round_log = build_round_log(ConsensusEngine().evaluate(round_input))

        self.assertEqual(round_log.to_dict(), round_log.to_dict())
        self.assertEqual(format_round_log_compact(round_log), format_round_log_compact(round_log))


if __name__ == "__main__":
    unittest.main()
