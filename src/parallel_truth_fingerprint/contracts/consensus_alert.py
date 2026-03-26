"""Consensus-specific alert contracts."""

from __future__ import annotations

from dataclasses import dataclass
from enum import StrEnum

from parallel_truth_fingerprint.contracts.consensus_status import ConsensusStatus
from parallel_truth_fingerprint.contracts.exclusion_decision import ExclusionDecision
from parallel_truth_fingerprint.contracts.round_identity import RoundIdentity
from parallel_truth_fingerprint.contracts.trust_evidence import PerEdgeTrustEvidence


class ConsensusAlertType(StrEnum):
    CONSENSUS_FAILED = "consensus_failed"


@dataclass(frozen=True)
class ConsensusAlert:
    """Structured consensus alert derived from existing consensus outputs only."""

    alert_type: ConsensusAlertType
    round_identity: RoundIdentity
    final_status: ConsensusStatus
    exclusions: tuple[ExclusionDecision, ...]
    trust_evidence: tuple[PerEdgeTrustEvidence, ...]

    def __post_init__(self) -> None:
        if self.alert_type == ConsensusAlertType.CONSENSUS_FAILED:
            if self.final_status != ConsensusStatus.FAILED_CONSENSUS:
                raise ValueError("CONSENSUS_FAILED alerts require failed_consensus status.")

        for exclusion in self.exclusions:
            if exclusion.round_identity != self.round_identity:
                raise ValueError("Alert exclusions must share the alert round identity.")

        for evidence in self.trust_evidence:
            if evidence.round_identity != self.round_identity:
                raise ValueError("Alert trust evidence must share the alert round identity.")

    def to_dict(self) -> dict[str, object]:
        """Return a deterministic serialized alert view."""

        return {
            "alert_type": self.alert_type.value,
            "round_id": self.round_identity.round_id,
            "final_status": self.final_status.value,
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
                    "compatible_peer_count": evidence.compatible_peer_count,
                    "overall_normalized_deviation": evidence.overall_normalized_deviation,
                    "sensor_deviations": [
                        {
                            "sensor_name": deviation.sensor_name,
                            "deviation_value": deviation.deviation_value,
                            "unit": deviation.unit,
                        }
                        for deviation in evidence.sensor_deviations
                    ],
                    "pairwise_distances": [
                        {
                            "peer_edge_id": pairwise.peer_edge_id,
                            "sensor_name": pairwise.sensor_name,
                            "distance_value": pairwise.distance_value,
                            "unit": pairwise.unit,
                        }
                        for pairwise in evidence.pairwise_distances
                    ],
                }
                for evidence in self.trust_evidence
            ],
        }
