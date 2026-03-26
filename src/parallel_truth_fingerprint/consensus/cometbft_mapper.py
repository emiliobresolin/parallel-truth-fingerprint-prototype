"""Map committed CometBFT state back into the project's consensus contracts."""

from __future__ import annotations

from dataclasses import replace
from datetime import datetime

from parallel_truth_fingerprint.contracts.consensus_audit_package import (
    ConsensusAuditPackage,
)
from parallel_truth_fingerprint.contracts.consensus_result import ConsensusResult
from parallel_truth_fingerprint.contracts.consensus_round_input import ConsensusRoundInput
from parallel_truth_fingerprint.contracts.consensus_status import ConsensusStatus
from parallel_truth_fingerprint.contracts.consensused_valid_state import (
    ConsensusedValidState,
)
from parallel_truth_fingerprint.contracts.exclusion_decision import ExclusionDecision
from parallel_truth_fingerprint.contracts.exclusion_reason import ExclusionReason
from parallel_truth_fingerprint.contracts.round_identity import RoundIdentity
from parallel_truth_fingerprint.contracts.trust_evidence import (
    PairwiseDistanceEvidence,
    PerEdgeTrustEvidence,
    SensorDeviationEvidence,
)
from parallel_truth_fingerprint.contracts.trust_ranking import TrustRankEntry, TrustRanking


def committed_round_to_audit_package(
    round_input: ConsensusRoundInput,
    committed_round: dict[str, object],
) -> ConsensusAuditPackage:
    """Convert a CometBFT-committed round result into the local audit contracts."""

    round_identity = RoundIdentity(
        round_id=str(committed_round["round_id"]),
        window_started_at=datetime.fromisoformat(str(committed_round["window_started_at"])),
        window_ended_at=datetime.fromisoformat(str(committed_round["window_ended_at"])),
    )
    if round_identity.round_id != round_input.round_identity.round_id:
        raise ValueError("Committed round id must match the submitted round input.")
    committed_round_input = ConsensusRoundInput(
        round_identity=round_identity,
        participating_edges=round_input.participating_edges,
        replicated_states=tuple(
            replace(replicated_state, round_identity=round_identity)
            for replicated_state in round_input.replicated_states
        ),
    )

    participating_edges = tuple(committed_round["participating_edges"])
    trust_ranking = TrustRanking(
        round_identity=round_identity,
        participating_edges=participating_edges,
        entries=tuple(
            TrustRankEntry(edge_id=entry["edge_id"], score=float(entry["score"]))
            for entry in committed_round["trust_ranking"]
        ),
    )
    exclusions = tuple(
        ExclusionDecision(
            round_identity=round_identity,
            edge_id=entry["edge_id"],
            reason=ExclusionReason(entry["reason"]),
            detail=entry.get("detail"),
        )
        for entry in committed_round["exclusions"]
    )
    trust_evidence = tuple(
        PerEdgeTrustEvidence(
            round_identity=round_identity,
            edge_id=entry["edge_id"],
            score=float(entry["score"]),
            compatible_peer_count=int(entry["compatible_peer_count"]),
            overall_normalized_deviation=float(entry["overall_normalized_deviation"]),
            sensor_deviations=tuple(
                SensorDeviationEvidence(
                    sensor_name=deviation["sensor_name"],
                    deviation_value=float(deviation["deviation_value"]),
                    unit=deviation["unit"],
                )
                for deviation in entry["sensor_deviations"]
            ),
            pairwise_distances=tuple(
                PairwiseDistanceEvidence(
                    peer_edge_id=distance["peer_edge_id"],
                    sensor_name=distance["sensor_name"],
                    distance_value=float(distance["distance_value"]),
                    unit=distance["unit"],
                )
                for distance in entry["pairwise_distances"]
            ),
        )
        for entry in committed_round["trust_evidence"]
    )
    valid_state_payload = committed_round.get("consensused_valid_state")
    valid_state = None
    if valid_state_payload is not None:
        valid_state = ConsensusedValidState(
            round_identity=round_identity,
            source_edges=tuple(valid_state_payload["source_edges"]),
            sensor_values={
                sensor_name: float(value)
                for sensor_name, value in valid_state_payload["sensor_values"].items()
            },
        )

    final_status = ConsensusStatus(committed_round["final_status"])
    consensus_result = ConsensusResult(
        round_identity=round_identity,
        status=final_status,
        participating_edges=participating_edges,
        trust_ranking=trust_ranking,
        exclusions=exclusions,
        consensused_valid_state=valid_state,
    )
    return ConsensusAuditPackage(
        round_input=committed_round_input,
        trust_ranking=trust_ranking,
        exclusions=exclusions,
        trust_evidence=trust_evidence,
        final_status=final_status,
        consensus_result=consensus_result,
        consensused_valid_state=valid_state,
    )
