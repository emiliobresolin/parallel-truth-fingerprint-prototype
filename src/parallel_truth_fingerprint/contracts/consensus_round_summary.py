"""Structured compact summary for one consensus round."""

from __future__ import annotations

from dataclasses import dataclass

from parallel_truth_fingerprint.contracts.consensus_status import ConsensusStatus


@dataclass(frozen=True)
class ExcludedEdgeSummary:
    """Deterministic structured exclusion visibility for one edge."""

    edge_id: str
    reason: str
    detail: str | None = None


@dataclass(frozen=True)
class ConsensusRoundSummary:
    """Compact structured observability view derived from one audit package."""

    round_id: str
    total_participants: int
    quorum_required: int
    valid_participants_after_exclusions: int
    excluded_edge_ids: tuple[str, ...]
    exclusion_reasons: tuple[str, ...]
    excluded_edges: tuple[ExcludedEdgeSummary, ...]
    final_consensus_status: ConsensusStatus
    has_consensused_valid_state: bool

    def to_dict(self) -> dict[str, object]:
        """Return a deterministic serialized view for logs or later reuse."""

        return {
            "round_id": self.round_id,
            "total_participants": self.total_participants,
            "quorum_required": self.quorum_required,
            "valid_participants_after_exclusions": self.valid_participants_after_exclusions,
            "excluded_edge_ids": list(self.excluded_edge_ids),
            "exclusion_reasons": list(self.exclusion_reasons),
            "excluded_edges": [
                {
                    "edge_id": excluded.edge_id,
                    "reason": excluded.reason,
                    "detail": excluded.detail,
                }
                for excluded in self.excluded_edges
            ],
            "final_consensus_status": self.final_consensus_status.value,
            "has_consensused_valid_state": self.has_consensused_valid_state,
        }
