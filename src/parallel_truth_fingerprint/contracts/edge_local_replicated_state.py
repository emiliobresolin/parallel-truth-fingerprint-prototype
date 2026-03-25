"""Typed intermediate edge-local replicated state contract."""

from __future__ import annotations

from dataclasses import dataclass

from parallel_truth_fingerprint.contracts.raw_hart_payload import RawHartPayload
from parallel_truth_fingerprint.contracts.round_identity import RoundIdentity


@dataclass(frozen=True)
class EdgeLocalReplicatedStateContract:
    """Intermediate non-validated shared view reconstructed by one edge."""

    round_identity: RoundIdentity
    owner_edge_id: str
    participating_edges: tuple[str, ...]
    observations_by_sensor: dict[str, RawHartPayload]
    is_validated: bool = False

    def __post_init__(self) -> None:
        if self.is_validated:
            raise ValueError("Edge-local replicated state must remain non-validated.")
