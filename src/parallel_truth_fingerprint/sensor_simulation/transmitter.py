"""The sole pure v2 engineering-to-transmitter-to-observation composition.

The conversion implementation is injected from an admitted profile boundary.
This module deliberately has neither a local affine formula nor a process or
transport dependency.
"""
from __future__ import annotations

from dataclasses import dataclass
from decimal import Decimal, InvalidOperation
from typing import Callable, Mapping, Any

from parallel_truth_fingerprint.contracts.signal_observation import SignalObservation
from parallel_truth_fingerprint.evidence.signal_observations import (
    SignalObservationResolver,
    build_signal_observation,
)
from parallel_truth_fingerprint.sensor_simulation.process_physics import EngineeringChannel


@dataclass(frozen=True)
class TransmitterAssignment:
    channel_id: str
    edge_id: str
    sensor_id: str
    quantity_kind: str
    unit: str
    profile_id: str
    authorization_effect: str = "none"

    def __post_init__(self) -> None:
        if (not all(isinstance(v, str) and v for v in (self.channel_id, self.edge_id, self.sensor_id,
                                                        self.quantity_kind, self.unit, self.profile_id))
                or self.authorization_effect != "none"):
            raise ValueError("PTEV2_TRANSMITTER_ASSIGNMENT")


def _canonical(value: object) -> str:
    if not isinstance(value, str) or not value or "e" in value.lower() or value in {"-0", "+0"}:
        raise ValueError("PTEV2_TRANSMITTER_CURRENT")
    try:
        parsed = Decimal(value)
    except (InvalidOperation, ValueError) as exc:
        raise ValueError("PTEV2_TRANSMITTER_CURRENT") from exc
    if not parsed.is_finite():
        raise ValueError("PTEV2_TRANSMITTER_CURRENT")
    return value


def compose_signal_observation(
    channel: EngineeringChannel, *, assignment: TransmitterAssignment,
    raw_facts: Mapping[str, Any], engineering_or_reference_to_current: Callable[[Decimal], str],
    resolver: SignalObservationResolver,
) -> SignalObservation:
    """Perform exactly one injected forward transform and delegate all reverse work.

    ``raw_facts`` holds fully injected identity/time/diagnostic facts, but cannot
    contain any representation derived by a caller or a precomputed raw current.
    """
    if (channel.channel_id, channel.quantity_kind, channel.unit) != (
        assignment.channel_id, assignment.quantity_kind, assignment.unit,
    ):
        raise ValueError("PTEV2_TRANSMITTER_ASSIGNMENT")
    value = channel.decimal_value()
    if value is None:
        raise ValueError("PTEV2_TRANSMITTER_UNAVAILABLE")
    forbidden = {"raw_current", "quality_trace", "normalized_span", "engineering_value", "observation_content_id"}
    if forbidden.intersection(raw_facts):
        raise ValueError("PTEV2_TRANSMITTER_DERIVED_INPUT")
    if raw_facts.get("edge_id") != assignment.edge_id or raw_facts.get("sensor_id") != assignment.sensor_id:
        raise ValueError("PTEV2_TRANSMITTER_ASSIGNMENT")
    profile = raw_facts.get("profile_binding")
    if not isinstance(profile, Mapping) or profile.get("profile_id") != assignment.profile_id:
        raise ValueError("PTEV2_TRANSMITTER_ASSIGNMENT")
    raw_current = _canonical(engineering_or_reference_to_current(value))
    facts = dict(raw_facts)
    facts["raw_current"] = {"state": "present", "value": raw_current, "unit": "mA"}
    return build_signal_observation(facts, resolver=resolver)
