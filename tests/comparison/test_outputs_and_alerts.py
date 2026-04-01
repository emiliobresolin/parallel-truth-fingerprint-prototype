"""Focused tests for Story 3.3 structured outputs and SCADA alerts."""

from __future__ import annotations

from datetime import datetime, timedelta, timezone
import unittest

from parallel_truth_fingerprint.comparison import (
    ScadaToleranceProfile,
    build_scada_comparison_output,
    build_scada_divergence_alert,
    compare_consensused_to_scada,
    format_scada_alert_compact,
    format_scada_alert_detailed,
    format_scada_comparison_output_compact,
)
from parallel_truth_fingerprint.contracts.consensused_valid_state import (
    ConsensusedValidState,
)
from parallel_truth_fingerprint.contracts.round_identity import RoundIdentity
from parallel_truth_fingerprint.scada import FakeOpcUaScadaService


def build_valid_state(
    *,
    round_id: str = "round-300",
    temperature: float = 72.5,
    pressure: float = 5.3,
    rpm: float = 3120.0,
) -> ConsensusedValidState:
    ended_at = datetime(2026, 4, 1, 14, 0, 0, tzinfo=timezone.utc)
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


class ScadaComparisonOutputsAndAlertsTests(unittest.TestCase):
    def test_structured_output_contains_per_sensor_values_and_classification(self) -> None:
        valid_state = build_valid_state()
        scada_state = FakeOpcUaScadaService().project_state(valid_state)

        comparison_result = compare_consensused_to_scada(
            valid_state=valid_state,
            scada_state=scada_state,
            tolerance_profile=ScadaToleranceProfile(
                temperature=1.0,
                pressure=0.2,
                rpm=50.0,
            ),
            contextual_evidence={
                "temperature": {
                    "scada_mode": "match",
                    "evidence_note": "normal supervisory alignment",
                }
            },
        )
        output = build_scada_comparison_output(comparison_result)

        temperature_output = next(
            item for item in output.sensor_outputs if item.sensor_name == "temperature"
        )
        self.assertEqual(temperature_output.physical_value, 72.5)
        self.assertEqual(temperature_output.scada_value, 72.5)
        self.assertEqual(temperature_output.tolerance_evaluation, "within_tolerance")
        self.assertEqual(temperature_output.divergence_classification.value, "match")
        self.assertEqual(
            temperature_output.contextual_evidence,
            {
                "scada_mode": "match",
                "evidence_note": "normal supervisory alignment",
            },
        )
        self.assertEqual(output.divergent_sensors, ())

    def test_divergence_alert_is_emitted_only_for_divergent_sensors(self) -> None:
        valid_state = build_valid_state()
        scada_service = FakeOpcUaScadaService()
        scada_service.set_sensor_override("pressure", mode="offset", offset=0.8)
        scada_service.set_sensor_override("rpm", mode="offset", offset=190.0)
        scada_state = scada_service.project_state(valid_state)

        comparison_result = compare_consensused_to_scada(
            valid_state=valid_state,
            scada_state=scada_state,
            tolerance_profile=ScadaToleranceProfile(
                temperature=1.0,
                pressure=0.3,
                rpm=100.0,
            ),
        )
        output = build_scada_comparison_output(comparison_result)
        alert = build_scada_divergence_alert(output)

        self.assertEqual(output.divergent_sensors, ("pressure", "rpm"))
        self.assertIsNotNone(alert)
        assert alert is not None
        self.assertEqual(alert.alert_type.value, "scada_divergence")
        self.assertEqual(
            tuple(item.sensor_name for item in alert.divergent_sensor_outputs),
            ("pressure", "rpm"),
        )

    def test_no_alert_is_emitted_when_all_sensors_match(self) -> None:
        valid_state = build_valid_state()
        scada_state = FakeOpcUaScadaService().project_state(valid_state)

        comparison_result = compare_consensused_to_scada(
            valid_state=valid_state,
            scada_state=scada_state,
        )
        output = build_scada_comparison_output(comparison_result)

        self.assertIsNone(build_scada_divergence_alert(output))

    def test_formatting_is_deterministic_and_readable(self) -> None:
        valid_state = build_valid_state(round_id="round-321")
        scada_service = FakeOpcUaScadaService()
        scada_service.set_sensor_override("pressure", mode="offset", offset=0.8)
        scada_state = scada_service.project_state(valid_state)

        comparison_result = compare_consensused_to_scada(
            valid_state=valid_state,
            scada_state=scada_state,
            tolerance_profile=ScadaToleranceProfile(
                temperature=1.0,
                pressure=0.3,
                rpm=100.0,
            ),
        )
        output = build_scada_comparison_output(comparison_result)
        alert = build_scada_divergence_alert(output)

        compact_output = format_scada_comparison_output_compact(output)
        compact_alert = format_scada_alert_compact(alert)
        detailed_alert = format_scada_alert_detailed(alert)

        self.assertIn("round-321", compact_output)
        self.assertIn("pressure=divergent", compact_output)
        self.assertIn("alert=scada_divergence", compact_alert)
        self.assertIn("sensor=pressure", detailed_alert)
        self.assertEqual(compact_output, format_scada_comparison_output_compact(output))
        self.assertEqual(compact_alert, format_scada_alert_compact(alert))
