"""SCADA-specific divergence alert contracts."""

from __future__ import annotations

from dataclasses import dataclass
from enum import StrEnum

from parallel_truth_fingerprint.contracts.round_identity import RoundIdentity
from parallel_truth_fingerprint.contracts.scada_comparison_output import (
    SensorScadaComparisonOutput,
)


class ScadaAlertType(StrEnum):
    """Bounded SCADA alert categories for the prototype."""

    SCADA_DIVERGENCE = "scada_divergence"


@dataclass(frozen=True)
class ScadaAlert:
    """Structured SCADA divergence alert."""

    alert_type: ScadaAlertType
    round_identity: RoundIdentity
    scada_source_round_id: str
    divergent_sensor_outputs: tuple[SensorScadaComparisonOutput, ...]

    def __post_init__(self) -> None:
        if self.alert_type == ScadaAlertType.SCADA_DIVERGENCE and not self.divergent_sensor_outputs:
            raise ValueError(
                "SCADA_DIVERGENCE alerts require at least one divergent sensor output."
            )

    def to_dict(self) -> dict[str, object]:
        return {
            "alert_type": self.alert_type.value,
            "round_identity": {
                "round_id": self.round_identity.round_id,
                "window_started_at": self.round_identity.window_started_at.isoformat(),
                "window_ended_at": self.round_identity.window_ended_at.isoformat(),
            },
            "scada_source_round_id": self.scada_source_round_id,
            "divergent_sensor_outputs": [
                output.to_dict() for output in self.divergent_sensor_outputs
            ],
        }
