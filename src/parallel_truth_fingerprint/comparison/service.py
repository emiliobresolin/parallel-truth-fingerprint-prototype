"""Sensor-by-sensor comparison service between consensused and SCADA state."""

from __future__ import annotations

from dataclasses import dataclass

from parallel_truth_fingerprint.contracts.consensused_valid_state import (
    ConsensusedValidState,
)
from parallel_truth_fingerprint.contracts.scada_comparison import (
    ScadaComparisonResult,
    SensorScadaComparison,
)
from parallel_truth_fingerprint.contracts.scada_state import ScadaState

COMPARISON_SENSOR_ORDER = ("temperature", "pressure", "rpm")


class ComparisonBlockedError(RuntimeError):
    """Raised when comparison cannot run because no valid state exists."""


@dataclass(frozen=True)
class ScadaToleranceProfile:
    """Prototype-scaled configurable tolerance values by sensor."""

    temperature: float = 2.0
    pressure: float = 0.35
    rpm: float = 120.0

    def value_for(self, sensor_name: str) -> float:
        """Return the configured tolerance for one supported sensor."""

        if sensor_name not in COMPARISON_SENSOR_ORDER:
            raise ValueError(
                f"Unsupported comparison sensor '{sensor_name}'. "
                f"Expected one of {list(COMPARISON_SENSOR_ORDER)}."
            )
        return float(getattr(self, sensor_name))


def compare_consensused_to_scada(
    *,
    valid_state: ConsensusedValidState | None,
    scada_state: ScadaState,
    tolerance_profile: ScadaToleranceProfile | None = None,
    contextual_evidence: dict[str, dict[str, object]] | None = None,
) -> ScadaComparisonResult:
    """Compare physical-side valid state to the current logical SCADA state.

    Configurable tolerance is the only decision rule in Story 3.2.
    Optional contextual evidence may be attached for later explanation, but it
    does not alter the decision outcome.
    """

    if valid_state is None:
        raise ComparisonBlockedError(
            "SCADA comparison requires a consensused valid state and remains blocked "
            "when consensus did not produce one."
        )

    tolerance_profile = tolerance_profile or ScadaToleranceProfile()
    contextual_evidence = contextual_evidence or {}

    _validate_supported_sensors(valid_state.sensor_values.keys(), "ConsensusedValidState")
    _validate_supported_sensors(scada_state.sensor_values.keys(), "ScadaState")

    sensor_comparisons = []
    for sensor_name in COMPARISON_SENSOR_ORDER:
        physical_value = round(float(valid_state.sensor_values[sensor_name]), 3)
        scada_value = round(float(scada_state.sensor_values[sensor_name].value), 3)
        tolerance = round(tolerance_profile.value_for(sensor_name), 3)
        absolute_difference = round(abs(physical_value - scada_value), 3)
        sensor_comparisons.append(
            SensorScadaComparison(
                sensor_name=sensor_name,
                physical_value=physical_value,
                scada_value=scada_value,
                absolute_difference=absolute_difference,
                tolerance=tolerance,
                within_tolerance=absolute_difference <= tolerance,
                contextual_evidence=contextual_evidence.get(sensor_name),
            )
        )

    return ScadaComparisonResult(
        round_identity=valid_state.round_identity,
        scada_source_round_id=scada_state.source_round_id,
        sensor_comparisons=tuple(sensor_comparisons),
    )


def _validate_supported_sensors(sensor_names, source_name: str) -> None:
    missing = set(COMPARISON_SENSOR_ORDER).difference(sensor_names)
    if missing:
        raise ValueError(
            f"{source_name} is missing supported comparison sensors: {sorted(missing)}"
        )
