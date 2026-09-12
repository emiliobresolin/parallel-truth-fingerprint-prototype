"""Inactive v2 engineering-frame boundary.

This module intentionally has no relation to the legacy compressor simulator.
It accepts a caller-supplied trace; it neither generates physics nor controls a
device.
"""

from __future__ import annotations

from dataclasses import dataclass
from decimal import Decimal, InvalidOperation


@dataclass(frozen=True)
class EngineeringChannel:
    channel_id: str
    quantity_kind: str
    unit: str
    value: str | None
    trace_reference: str
    parameter_gate_id: str
    mock_admission_id: str
    availability: str
    authorization_effect: str = "none"

    def decimal_value(self) -> Decimal | None:
        if self.availability == "unavailable":
            if self.value is not None:
                raise ValueError("PTEV2_PROCESS_PROFILE")
            return None
        if self.availability != "present" or not isinstance(self.value, str) or not self.value:
            raise ValueError("PTEV2_PROCESS_PROFILE")
        try:
            parsed = Decimal(self.value)
        except (InvalidOperation, ValueError) as exc:
            raise ValueError("PTEV2_PROCESS_PROFILE") from exc
        if not parsed.is_finite() or "e" in self.value.lower() or self.value in {"-0", "+0"}:
            raise ValueError("PTEV2_PROCESS_PROFILE")
        return parsed


@dataclass(frozen=True)
class EngineeringFrame:
    temperature: EngineeringChannel
    pressure: EngineeringChannel
    rotational_speed: EngineeringChannel
    frame_trace_reference: str
    authorization_effect: str = "none"

    def validate(self) -> None:
        expected = ((self.temperature, "temperature"), (self.pressure, "pressure"),
                    (self.rotational_speed, "rotational_speed"))
        for channel, quantity in expected:
            if channel.quantity_kind != quantity or channel.authorization_effect != "none":
                raise ValueError("PTEV2_PROCESS_PROFILE")
            channel.decimal_value()
            if not all((channel.trace_reference, channel.parameter_gate_id, channel.mock_admission_id)):
                raise ValueError("PTEV2_PREREQUISITE_ADMISSION")
