"""Unified auditable package emitted after each consensus round."""

from __future__ import annotations

from dataclasses import dataclass

from parallel_truth_fingerprint.contracts.consensus_result import ConsensusResult
from parallel_truth_fingerprint.contracts.consensus_round_input import ConsensusRoundInput
from parallel_truth_fingerprint.contracts.consensus_status import ConsensusStatus
from parallel_truth_fingerprint.contracts.consensused_valid_state import (
    ConsensusedValidState,
)
from parallel_truth_fingerprint.contracts.exclusion_decision import ExclusionDecision
from parallel_truth_fingerprint.contracts.trust_evidence import PerEdgeTrustEvidence
from parallel_truth_fingerprint.contracts.trust_ranking import TrustRanking


@dataclass(frozen=True)
class ConsensusAuditPackage:
    """Auditable package for traceability and later downstream stages."""

    round_input: ConsensusRoundInput
    trust_ranking: TrustRanking
    exclusions: tuple[ExclusionDecision, ...]
    trust_evidence: tuple[PerEdgeTrustEvidence, ...]
    final_status: ConsensusStatus
    consensus_result: ConsensusResult
    consensused_valid_state: ConsensusedValidState | None

    def __post_init__(self) -> None:
        if self.trust_ranking.round_identity != self.round_input.round_identity:
            raise ValueError("Trust ranking must share the round identity of the input.")

        for exclusion in self.exclusions:
            if exclusion.round_identity != self.round_input.round_identity:
                raise ValueError("Exclusions must be scoped to the audit round.")

        for evidence in self.trust_evidence:
            if evidence.round_identity != self.round_input.round_identity:
                raise ValueError("Trust evidence must be scoped to the audit round.")

        if self.consensus_result.round_identity != self.round_input.round_identity:
            raise ValueError("Consensus result must share the round identity of the input.")

        if self.consensus_result.trust_ranking != self.trust_ranking:
            raise ValueError("Audit package trust ranking must match the consensus result.")

        if self.consensus_result.exclusions != self.exclusions:
            raise ValueError("Audit package exclusions must match the consensus result.")

        if self.consensus_result.status != self.final_status:
            raise ValueError("Audit package final status must match the consensus result.")

        if self.consensus_result.consensused_valid_state != self.consensused_valid_state:
            raise ValueError("Audit package valid state must match the consensus result.")
