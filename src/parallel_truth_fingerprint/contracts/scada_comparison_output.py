"""Structured per-sensor output contracts for SCADA comparison results."""

from __future__ import annotations

from dataclasses import dataclass
from enum import StrEnum

from parallel_truth_fingerprint.contracts.round_identity import RoundIdentity


class ScadaDivergenceClassification(StrEnum):
    """Bounded divergence classification for one sensor."""

    MATCH = "match"
    DIVERGENT = "divergent"


@dataclass(frozen=True)
class SensorScadaComparisonOutput:
    """Structured per-sensor SCADA comparison output for Story 3.3."""

    sensor_name: str
    physical_value: float
    scada_value: float
    absolute_difference: float
    tolerance: float
    tolerance_evaluation: str
    divergence_classification: ScadaDivergenceClassification
    contextual_evidence: dict[str, object] | None = None

    def to_dict(self) -> dict[str, object]:
        payload = {
            "sensor_name": self.sensor_name,
            "physical_value": self.physical_value,
            "scada_value": self.scada_value,
            "absolute_difference": self.absolute_difference,
            "tolerance": self.tolerance,
            "tolerance_evaluation": self.tolerance_evaluation,
            "divergence_classification": self.divergence_classification.value,
        }
        if self.contextual_evidence is not None:
            payload["contextual_evidence"] = self.contextual_evidence
        return payload


@dataclass(frozen=True)
class ScadaComparisonOutput:
    """Round-scoped structured output derived from Story 3.2 comparison results."""

    round_identity: RoundIdentity
    scada_source_round_id: str
    sensor_outputs: tuple[SensorScadaComparisonOutput, ...]

    @property
    def divergent_sensors(self) -> tuple[str, ...]:
        return tuple(
            output.sensor_name
            for output in self.sensor_outputs
            if output.divergence_classification == ScadaDivergenceClassification.DIVERGENT
        )

    def to_dict(self) -> dict[str, object]:
        return {
            "round_identity": {
                "round_id": self.round_identity.round_id,
                "window_started_at": self.round_identity.window_started_at.isoformat(),
                "window_ended_at": self.round_identity.window_ended_at.isoformat(),
            },
            "scada_source_round_id": self.scada_source_round_id,
            "divergent_sensors": list(self.divergent_sensors),
            "sensor_outputs": [output.to_dict() for output in self.sensor_outputs],
        }
