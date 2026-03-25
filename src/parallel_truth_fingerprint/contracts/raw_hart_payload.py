"""Typed raw HART-style payload contracts for edge-local acquisition.

These contracts represent the digital output of the edge after it reads and
interprets the physical measurement coming from the simulator/process model.
"""

from __future__ import annotations

from dataclasses import asdict, dataclass


@dataclass(frozen=True)
class DeviceInfo:
    tag: str
    long_tag: str
    manufacturer_id: int
    device_type: int


@dataclass(frozen=True)
class ProcessVariable:
    value: float
    unit: str
    unit_code: int | None = None
    description: str | None = None


@dataclass(frozen=True)
class PhysicsMetrics:
    noise_floor: float
    rate_of_change_dtdt: float
    local_stability_score: float


@dataclass(frozen=True)
class ProcessData:
    pv: ProcessVariable
    sv: ProcessVariable
    loop_current_ma: float
    pv_percent_range: float
    physics_metrics: PhysicsMetrics


@dataclass(frozen=True)
class Diagnostics:
    device_status_hex: str
    field_device_malfunction: bool
    loop_current_saturated: bool
    cold_start: bool


@dataclass(frozen=True)
class RawHartPayload:
    protocol: str
    gateway_id: str
    timestamp: str
    device_info: DeviceInfo
    process_data: ProcessData
    diagnostics: Diagnostics

    def to_dict(self) -> dict[str, object]:
        """Return a serializable raw HART-style payload."""

        return asdict(self)
