"""Typed transmitter-side observation contracts for the simulator.

These contracts model what the edge would read from a local transmitter-like
observation before it builds the gateway payload.
"""

from __future__ import annotations

from dataclasses import asdict, dataclass


@dataclass(frozen=True)
class TransmitterVariableObservation:
    value: float
    unit: str
    unit_code: int | None = None
    description: str | None = None


@dataclass(frozen=True)
class TransmitterDiagnosticsObservation:
    device_status_hex: str
    field_device_malfunction: bool
    loop_current_saturated: bool


@dataclass(frozen=True)
class SimulatedTransmitterObservation:
    sensor_name: str
    operating_state_pct: float
    pv: TransmitterVariableObservation
    sv: TransmitterVariableObservation | None
    loop_current_ma: float
    pv_percent_range: float
    diagnostics: TransmitterDiagnosticsObservation

    def to_dict(self) -> dict[str, object]:
        """Return a serializable representation for logs and tests."""

        data = asdict(self)
        if data.get("sv") is None:
            data.pop("sv", None)
        return data
