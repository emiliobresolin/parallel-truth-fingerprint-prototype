"""Consensus round input contract."""

from __future__ import annotations

from dataclasses import dataclass

from parallel_truth_fingerprint.contracts.edge_local_replicated_state import (
    EdgeLocalReplicatedStateContract,
)
from parallel_truth_fingerprint.contracts.round_identity import RoundIdentity


@dataclass(frozen=True)
class ConsensusRoundInput:
    """Input to one edge-local consensus round based only on replicated state."""

    round_identity: RoundIdentity
    participating_edges: tuple[str, ...]
    replicated_states: tuple[EdgeLocalReplicatedStateContract, ...]

    def __post_init__(self) -> None:
        for replicated_state in self.replicated_states:
            if replicated_state.round_identity != self.round_identity:
                raise ValueError("All replicated states must share the same round identity.")
            if replicated_state.owner_edge_id not in self.participating_edges:
                raise ValueError("Replicated state owner must be a participating edge.")
