"""Typed contracts for sensor-by-sensor SCADA comparison decisions."""

from __future__ import annotations

from dataclasses import dataclass

from parallel_truth_fingerprint.contracts.round_identity import RoundIdentity


@dataclass(frozen=True)
class SensorScadaComparison:
    """One tolerance-based comparison between physical and logical values."""

    sensor_name: str
    physical_value: float
    scada_value: float
    absolute_difference: float
    tolerance: float
    within_tolerance: bool
    contextual_evidence: dict[str, object] | None = None

    def to_dict(self) -> dict[str, object]:
        """Return a serializable per-sensor comparison view."""

        payload = {
            "sensor_name": self.sensor_name,
            "physical_value": self.physical_value,
            "scada_value": self.scada_value,
            "absolute_difference": self.absolute_difference,
            "tolerance": self.tolerance,
            "within_tolerance": self.within_tolerance,
        }
        if self.contextual_evidence is not None:
            payload["contextual_evidence"] = self.contextual_evidence
        return payload


@dataclass(frozen=True)
class ScadaComparisonResult:
    """Round-scoped comparison result ready for later output and alert layers."""

    round_identity: RoundIdentity
    scada_source_round_id: str
    sensor_comparisons: tuple[SensorScadaComparison, ...]

    @property
    def all_within_tolerance(self) -> bool:
        """Return True when every sensor remains within the configured tolerance."""

        return all(item.within_tolerance for item in self.sensor_comparisons)

    def to_dict(self) -> dict[str, object]:
        """Return a serializable comparison result."""

        return {
            "round_identity": {
                "round_id": self.round_identity.round_id,
                "window_started_at": self.round_identity.window_started_at.isoformat(),
                "window_ended_at": self.round_identity.window_ended_at.isoformat(),
            },
            "scada_source_round_id": self.scada_source_round_id,
            "all_within_tolerance": self.all_within_tolerance,
            "sensor_comparisons": [
                item.to_dict() for item in self.sensor_comparisons
            ],
        }
