"""Strict, non-trusted edge-local retention for ``SignalObservation.v2``.

This is deliberately independent of the legacy edge acquisition state.  It
accepts already-constructed observations only; it cannot see process frames or
perform a conversion.
"""
from __future__ import annotations

from dataclasses import dataclass, field
from types import MappingProxyType
from typing import Mapping

from parallel_truth_fingerprint.contracts.signal_observation import SignalObservation
from parallel_truth_fingerprint.evidence.signal_observations import (
    SignalObservationResolver,
    validate_signal_observation,
)


@dataclass(frozen=True)
class SignalEdgeBinding:
    """Explicit immutable receiver binding; identities are never inferred."""
    edge_id: str
    sensor_id: str
    profile_id: str
    authorization_effect: str = "none"

    def __post_init__(self) -> None:
        if (not all(isinstance(v, str) and v for v in (self.edge_id, self.sensor_id, self.profile_id))
                or self.authorization_effect != "none"):
            raise ValueError("PTEV2_EDGE_BINDING")


@dataclass(frozen=True)
class SignalReceiveResult:
    accepted: bool
    content_id: str | None
    diagnostics: tuple[Mapping[str, str], ...]
    authorization_effect: str = "none"


@dataclass
class EdgeSignalObservationView:
    """An edge-owned, content-addressed, non-trusted immutable observation view."""
    binding: SignalEdgeBinding
    _observations: dict[str, SignalObservation] = field(default_factory=dict, init=False, repr=False)

    def receive(self, observation: SignalObservation, *, resolver: SignalObservationResolver) -> SignalReceiveResult:
        """Validate first, then retain by content ID without replacing prior data."""
        checked = validate_signal_observation(observation.to_dict(), resolver)
        if not checked.valid or checked.observation is None:
            return SignalReceiveResult(False, None, checked.violations)
        data = checked.observation.to_dict()
        if (data["edge_id"], data["sensor_id"], data["profile_binding"]["profile_id"]) != (
            self.binding.edge_id, self.binding.sensor_id, self.binding.profile_id,
        ):
            return SignalReceiveResult(False, None, ({"family": "PTEV2_EDGE_BINDING", "field": "observation", "token": "receiver_binding_mismatch"},))
        content_id = data["observation_content_id"]
        # A duplicate byte-identical input is idempotent.  No event/sequence
        # classification belongs in this module.
        self._observations.setdefault(content_id, checked.observation)
        return SignalReceiveResult(True, content_id, ())

    def observations(self) -> Mapping[str, SignalObservation]:
        """Expose a fresh read-only mapping, never the mutable backing store."""
        return MappingProxyType(dict(self._observations))

    def retained(self) -> tuple[SignalObservation, ...]:
        return tuple(self._observations[key] for key in sorted(self._observations))
