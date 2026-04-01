"""Typed logical SCADA-state contracts for the fake OPC UA service."""

from __future__ import annotations

from dataclasses import dataclass


@dataclass(frozen=True)
class ScadaSensorState:
    """One logical supervisory value exposed by the fake SCADA layer."""

    value: float
    unit: str
    mode: str = "match"


@dataclass(frozen=True)
class ScadaState:
    """Logical SCADA-side state derived from the consensused valid payload."""

    compressor_id: str
    source_round_id: str
    timestamp: str
    sensor_values: dict[str, ScadaSensorState]

    def to_dict(self) -> dict[str, object]:
        """Return a serializable logical SCADA-state representation."""

        return {
            "compressor_id": self.compressor_id,
            "source_round_id": self.source_round_id,
            "timestamp": self.timestamp,
            "sensor_values": {
                sensor_name: {
                    "value": sensor_state.value,
                    "unit": sensor_state.unit,
                    "mode": sensor_state.mode,
                }
                for sensor_name, sensor_state in sorted(self.sensor_values.items())
            },
        }
