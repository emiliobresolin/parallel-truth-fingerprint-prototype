import unittest
from datetime import datetime, timedelta, timezone

from parallel_truth_fingerprint.consensus import (
    ConsensusEngine,
    build_consensus_alert,
    build_round_log,
    format_consensus_alert_compact,
    format_consensus_alert_detailed,
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


class ConsensusAlertTest(unittest.TestCase):
    def setUp(self) -> None:
        start = datetime(2026, 3, 25, 12, 0, tzinfo=timezone.utc)
        self.round_identity = RoundIdentity(
            round_id="round-alert",
            window_started_at=start,
            window_ended_at=start + timedelta(minutes=1),
        )

    def _build_alert(self, states):
        round_input = ConsensusRoundInput(
            round_identity=self.round_identity,
            participating_edges=("edge-1", "edge-2", "edge-3"),
            replicated_states=tuple(
                make_replicated_state(self.round_identity, edge_id, temp, pressure, rpm)
                for edge_id, temp, pressure, rpm in states
            ),
        )
        audit = ConsensusEngine().evaluate(round_input)
        round_log = build_round_log(audit)
        return build_consensus_alert(audit, round_log)

    def test_failed_consensus_produces_alert(self) -> None:
        alert = self._build_alert(
            [
                ("edge-1", 80.0, 6.0, 3200.0),
                ("edge-2", 150.0, 11.5, 5000.0),
                ("edge-3", 20.0, 1.0, 900.0),
            ]
        )

        self.assertIsNotNone(alert)
        assert alert is not None
        self.assertEqual(alert.alert_type.value, "consensus_failed")
        self.assertEqual(alert.final_status.value, "failed_consensus")
        self.assertEqual(tuple(ex.edge_id for ex in alert.exclusions), ("edge-2", "edge-3"))

    def test_successful_round_does_not_produce_alert(self) -> None:
        alert = self._build_alert(
            [
                ("edge-1", 80.0, 6.0, 3200.0),
                ("edge-2", 82.0, 6.2, 3220.0),
                ("edge-3", 81.0, 6.1, 3210.0),
            ]
        )

        self.assertIsNone(alert)

    def test_alert_includes_traceable_supporting_evidence(self) -> None:
        alert = self._build_alert(
            [
                ("edge-1", 80.0, 6.0, 3200.0),
                ("edge-2", 150.0, 11.5, 5000.0),
                ("edge-3", 20.0, 1.0, 900.0),
            ]
        )

        assert alert is not None
        self.assertGreaterEqual(len(alert.trust_evidence), 3)
        self.assertEqual(alert.trust_evidence[1].sensor_deviations[0].unit, "degC")
        self.assertEqual(alert.trust_evidence[1].sensor_deviations[0].deviation_value, 70.0)

    def test_alert_formatting_is_readable_and_deterministic(self) -> None:
        alert = self._build_alert(
            [
                ("edge-1", 80.0, 6.0, 3200.0),
                ("edge-2", 150.0, 11.5, 5000.0),
                ("edge-3", 20.0, 1.0, 900.0),
            ]
        )

        compact = format_consensus_alert_compact(alert)
        detailed = format_consensus_alert_detailed(alert)

        self.assertIn("alert=consensus_failed", compact)
        self.assertIn("status=failed_consensus", compact)
        self.assertIn("alert_type=consensus_failed", detailed)
        self.assertIn("excluded=edge-2 reason=suspected_byzantine_behavior", detailed)
        self.assertEqual(compact, format_consensus_alert_compact(alert))


if __name__ == "__main__":
    unittest.main()
