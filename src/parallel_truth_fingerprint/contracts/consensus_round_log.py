"""Structured consensus round log derived from audit output."""

from __future__ import annotations

from dataclasses import dataclass

from parallel_truth_fingerprint.contracts.consensus_status import ConsensusStatus
from parallel_truth_fingerprint.contracts.consensused_valid_state import (
    ConsensusedValidState,
)
from parallel_truth_fingerprint.contracts.exclusion_decision import ExclusionDecision
from parallel_truth_fingerprint.contracts.round_identity import RoundIdentity
from parallel_truth_fingerprint.contracts.trust_evidence import PerEdgeTrustEvidence
from parallel_truth_fingerprint.contracts.trust_ranking import TrustRanking


@dataclass(frozen=True)
class ConsensusRoundLog:
    """Fully traceable structured round log for demo and audit use."""

    round_identity: RoundIdentity
    participating_edges: tuple[str, ...]
    trust_ranking: TrustRanking
    exclusions: tuple[ExclusionDecision, ...]
    trust_evidence: tuple[PerEdgeTrustEvidence, ...]
    final_status: ConsensusStatus
    consensused_valid_state: ConsensusedValidState | None

    def to_dict(self) -> dict[str, object]:
        """Return a deterministic serialized view of the round log."""

        return {
            "round_id": self.round_identity.round_id,
            "window_started_at": self.round_identity.window_started_at.isoformat(),
            "window_ended_at": self.round_identity.window_ended_at.isoformat(),
            "participating_edges": list(self.participating_edges),
            "trust_ranking": [
                {
                    "edge_id": entry.edge_id,
                    "score": entry.score,
                }
                for entry in self.trust_ranking.entries
            ],
            "exclusions": [
                {
                    "edge_id": exclusion.edge_id,
                    "reason": exclusion.reason.value,
                    "detail": exclusion.detail,
                }
                for exclusion in self.exclusions
            ],
            "trust_evidence": [
                {
                    "edge_id": evidence.edge_id,
                    "score": evidence.score,
                    "sensor_deviations": [
                        {
                            "sensor_name": deviation.sensor_name,
                            "deviation_value": deviation.deviation_value,
                            "unit": deviation.unit,
                        }
                        for deviation in evidence.sensor_deviations
                    ],
                }
                for evidence in self.trust_evidence
            ],
            "final_status": self.final_status.value,
            "consensused_valid_state": (
                None
                if self.consensused_valid_state is None
                else {
                    "source_edges": list(self.consensused_valid_state.source_edges),
                    "sensor_values": dict(self.consensused_valid_state.sensor_values),
                }
            ),
        }
