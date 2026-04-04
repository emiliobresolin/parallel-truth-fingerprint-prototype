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
class ScadaBehavioralSensorState:
    """Richer SCADA-side behavioral fields carried for fingerprint evaluation."""

    loop_current_ma: float | None = None
    pv_percent_range: float | None = None
    noise_floor: float | None = None
    rate_of_change_dtdt: float | None = None
    local_stability_score: float | None = None
    field_device_malfunction: bool | None = None
    loop_current_saturated: bool | None = None
    cold_start: bool | None = None
    mode: str = "match"
    source_round_id: str | None = None

    def to_dict(self) -> dict[str, object]:
        return {
            "loop_current_ma": self.loop_current_ma,
            "pv_percent_range": self.pv_percent_range,
            "noise_floor": self.noise_floor,
            "rate_of_change_dtdt": self.rate_of_change_dtdt,
            "local_stability_score": self.local_stability_score,
            "field_device_malfunction": self.field_device_malfunction,
            "loop_current_saturated": self.loop_current_saturated,
            "cold_start": self.cold_start,
            "mode": self.mode,
            "source_round_id": self.source_round_id,
        }


@dataclass(frozen=True)
class ScadaState:
    """Logical SCADA-side state derived from the consensused valid payload."""

    compressor_id: str
    source_round_id: str
    timestamp: str
    sensor_values: dict[str, ScadaSensorState]
    behavioral_source_round_id: str | None = None
    behavioral_sensor_values: dict[str, ScadaBehavioralSensorState] | None = None

    def to_dict(self) -> dict[str, object]:
        """Return a serializable logical SCADA-state representation."""

        return {
            "compressor_id": self.compressor_id,
            "source_round_id": self.source_round_id,
            "timestamp": self.timestamp,
            "behavioral_source_round_id": self.behavioral_source_round_id,
            "sensor_values": {
                sensor_name: {
                    "value": sensor_state.value,
                    "unit": sensor_state.unit,
                    "mode": sensor_state.mode,
                }
                for sensor_name, sensor_state in sorted(self.sensor_values.items())
            },
            "behavioral_sensor_values": {
                sensor_name: sensor_state.to_dict()
                for sensor_name, sensor_state in sorted(
                    (self.behavioral_sensor_values or {}).items()
                )
            },
        }
