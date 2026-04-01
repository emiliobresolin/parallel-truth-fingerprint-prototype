"""Focused tests for Story 3.2 SCADA comparison behavior."""

from __future__ import annotations

from datetime import datetime, timedelta, timezone
import unittest

from parallel_truth_fingerprint.comparison import (
    ComparisonBlockedError,
    ScadaToleranceProfile,
    compare_consensused_to_scada,
)
from parallel_truth_fingerprint.contracts.consensused_valid_state import (
    ConsensusedValidState,
)
from parallel_truth_fingerprint.contracts.round_identity import RoundIdentity
from parallel_truth_fingerprint.scada import FakeOpcUaScadaService


def build_valid_state(
    *,
    round_id: str = "round-200",
    temperature: float = 72.5,
    pressure: float = 5.3,
    rpm: float = 3120.0,
) -> ConsensusedValidState:
    ended_at = datetime(2026, 4, 1, 13, 0, 0, tzinfo=timezone.utc)
    return ConsensusedValidState(
        round_identity=RoundIdentity(
            round_id=round_id,
            window_started_at=ended_at - timedelta(minutes=1),
            window_ended_at=ended_at,
        ),
        source_edges=("edge-1", "edge-2"),
        sensor_values={
            "temperature": temperature,
            "pressure": pressure,
            "rpm": rpm,
        },
    )


class ScadaComparisonServiceTests(unittest.TestCase):
    def test_matching_values_inside_tolerance_pass(self) -> None:
        valid_state = build_valid_state()
        scada_state = FakeOpcUaScadaService().project_state(valid_state)

        result = compare_consensused_to_scada(
            valid_state=valid_state,
            scada_state=scada_state,
            tolerance_profile=ScadaToleranceProfile(
                temperature=1.0,
                pressure=0.2,
                rpm=50.0,
            ),
        )

        self.assertTrue(result.all_within_tolerance)
        self.assertTrue(all(item.within_tolerance for item in result.sensor_comparisons))

    def test_out_of_tolerance_difference_is_detected_by_sensor(self) -> None:
        valid_state = build_valid_state()
        scada_service = FakeOpcUaScadaService()
        scada_service.set_sensor_override("pressure", mode="offset", offset=0.9)
        scada_state = scada_service.project_state(valid_state)

        result = compare_consensused_to_scada(
            valid_state=valid_state,
            scada_state=scada_state,
            tolerance_profile=ScadaToleranceProfile(
                temperature=1.0,
                pressure=0.3,
                rpm=50.0,
            ),
        )

        by_sensor = {item.sensor_name: item for item in result.sensor_comparisons}
        self.assertFalse(result.all_within_tolerance)
        self.assertTrue(by_sensor["temperature"].within_tolerance)
        self.assertFalse(by_sensor["pressure"].within_tolerance)
        self.assertEqual(by_sensor["pressure"].absolute_difference, 0.9)
        self.assertEqual(by_sensor["pressure"].tolerance, 0.3)

    def test_contextual_evidence_is_attached_but_not_decision_driving(self) -> None:
        valid_state = build_valid_state()
        scada_service = FakeOpcUaScadaService()
        scada_service.set_sensor_override("rpm", mode="offset", offset=40.0)
        scada_state = scada_service.project_state(valid_state)

        result = compare_consensused_to_scada(
            valid_state=valid_state,
            scada_state=scada_state,
            tolerance_profile=ScadaToleranceProfile(
                temperature=1.0,
                pressure=0.3,
                rpm=100.0,
            ),
            contextual_evidence={
                "rpm": {
                    "scada_mode": "offset",
                    "note": "simulated supervisory offset for demo preparation",
                }
            },
        )

        rpm_result = next(
            item for item in result.sensor_comparisons if item.sensor_name == "rpm"
        )
        self.assertTrue(rpm_result.within_tolerance)
        self.assertEqual(rpm_result.absolute_difference, 40.0)
        self.assertEqual(
            rpm_result.contextual_evidence,
            {
                "scada_mode": "offset",
                "note": "simulated supervisory offset for demo preparation",
            },
        )

    def test_comparison_is_blocked_without_valid_state(self) -> None:
        scada_state = FakeOpcUaScadaService().project_state(build_valid_state())

        with self.assertRaises(ComparisonBlockedError):
            compare_consensused_to_scada(
                valid_state=None,
                scada_state=scada_state,
            )
