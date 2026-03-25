"""Trusted state contract produced only by successful consensus."""

from __future__ import annotations

from dataclasses import dataclass

from parallel_truth_fingerprint.contracts.round_identity import RoundIdentity


@dataclass(frozen=True)
class ConsensusedValidState:
    """Validated state for downstream consumers."""

    round_identity: RoundIdentity
    source_edges: tuple[str, ...]
    sensor_values: dict[str, float]
