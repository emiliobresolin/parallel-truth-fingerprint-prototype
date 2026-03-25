"""Consensus result contract with explicit success/failure invariants."""

from __future__ import annotations

from dataclasses import dataclass

from parallel_truth_fingerprint.contracts.consensus_status import ConsensusStatus
from parallel_truth_fingerprint.contracts.consensused_valid_state import (
    ConsensusedValidState,
)
from parallel_truth_fingerprint.contracts.exclusion_decision import ExclusionDecision
from parallel_truth_fingerprint.contracts.round_identity import RoundIdentity
from parallel_truth_fingerprint.contracts.trust_ranking import TrustRanking


@dataclass(frozen=True)
class ConsensusResult:
    """Auditable round result with explicit success/failure behavior."""

    round_identity: RoundIdentity
    status: ConsensusStatus
    participating_edges: tuple[str, ...]
    trust_ranking: TrustRanking
    exclusions: tuple[ExclusionDecision, ...]
    consensused_valid_state: ConsensusedValidState | None

    def __post_init__(self) -> None:
        if self.trust_ranking.round_identity != self.round_identity:
            raise ValueError("Trust ranking must share the same round identity as the result.")

        for exclusion in self.exclusions:
            if exclusion.round_identity != self.round_identity:
                raise ValueError("Exclusion decisions must be round-scoped.")

        participating = set(self.participating_edges)
        ranking_edges = {entry.edge_id for entry in self.trust_ranking.entries}
        if ranking_edges != participating:
            raise ValueError("Trust ranking must reference only participating edges for that round.")

        if self.status == ConsensusStatus.SUCCESS and self.consensused_valid_state is None:
            raise ValueError("Successful consensus must include a consensused valid state.")
        if (
            self.status == ConsensusStatus.FAILED_CONSENSUS
            and self.consensused_valid_state is not None
        ):
            raise ValueError("Failed consensus must not include a consensused valid state.")
        if (
            self.consensused_valid_state is not None
            and self.consensused_valid_state.round_identity != self.round_identity
        ):
            raise ValueError("Consensused valid state must share the same round identity.")
