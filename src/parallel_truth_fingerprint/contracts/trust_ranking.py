"""Trust ranking contracts for one consensus round."""

from __future__ import annotations

from dataclasses import dataclass

from parallel_truth_fingerprint.contracts.round_identity import RoundIdentity


@dataclass(frozen=True)
class TrustRankEntry:
    edge_id: str
    score: float


@dataclass(frozen=True)
class TrustRanking:
    """Auditable trust ranking for participating edges in one round."""

    round_identity: RoundIdentity
    participating_edges: tuple[str, ...]
    entries: tuple[TrustRankEntry, ...]

    def __post_init__(self) -> None:
        participating = set(self.participating_edges)
        entry_edges = {entry.edge_id for entry in self.entries}
        if entry_edges != participating:
            raise ValueError("Trust ranking must reference only participating edges for the round.")
