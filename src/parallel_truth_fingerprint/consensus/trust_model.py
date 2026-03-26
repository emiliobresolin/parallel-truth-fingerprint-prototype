"""Deterministic pairwise-consistency trust evaluation for prototype consensus."""

from __future__ import annotations

from dataclasses import dataclass

from parallel_truth_fingerprint.contracts.edge_local_replicated_state import (
    EdgeLocalReplicatedStateContract,
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


@dataclass(frozen=True)
class SensorTolerance:
    normalization_scale: float


SENSOR_SCALES = {
    "temperature": SensorTolerance(20.0),
    "pressure": SensorTolerance(3.0),
    "rpm": SensorTolerance(600.0),
}
PAIRWISE_CONSISTENCY_THRESHOLD = 0.35
SUSPECTED_BYZANTINE_THRESHOLD = 0.75


def _sensor_value(state: EdgeLocalReplicatedStateContract, sensor_name: str) -> float:
    return state.observations_by_sensor[sensor_name].process_data.pv.value


def _normalized_pair_distance(
    left_state: EdgeLocalReplicatedStateContract,
    right_state: EdgeLocalReplicatedStateContract,
) -> float:
    normalized_distances = []
    for sensor_name, sensor_scale in SENSOR_SCALES.items():
        normalized_distances.append(
            abs(_sensor_value(left_state, sensor_name) - _sensor_value(right_state, sensor_name))
            / sensor_scale.normalization_scale
        )
    return sum(normalized_distances) / len(normalized_distances)


def evaluate_trust(
    *,
    round_identity: RoundIdentity,
    participating_edges: tuple[str, ...],
    replicated_states: tuple[EdgeLocalReplicatedStateContract, ...],
) -> tuple[
    TrustRanking,
    tuple[ExclusionDecision, ...],
    tuple[PerEdgeTrustEvidence, ...],
]:
    """Compute deterministic trust ranking from pairwise consistency."""

    by_edge = {state.owner_edge_id: state for state in replicated_states}
    pairwise_distances = {
        (left_edge, right_edge): _normalized_pair_distance(by_edge[left_edge], by_edge[right_edge])
        for left_edge in participating_edges
        for right_edge in participating_edges
        if left_edge != right_edge
    }
    quorum = (len(participating_edges) // 2) + 1

    ranking_entries: list[TrustRankEntry] = []
    exclusions: list[ExclusionDecision] = []
    trust_evidence: list[PerEdgeTrustEvidence] = []

    for edge_id in participating_edges:
        state = by_edge[edge_id]
        peer_edges = tuple(peer for peer in participating_edges if peer != edge_id)
        detail_parts: list[str] = []
        sensor_deviations: list[SensorDeviationEvidence] = []
        per_pair_distances: list[PairwiseDistanceEvidence] = []

        for sensor_name, sensor_scale in SENSOR_SCALES.items():
            payload = state.observations_by_sensor[sensor_name]
            peer_distances = []
            for peer_edge_id in peer_edges:
                peer_payload = by_edge[peer_edge_id].observations_by_sensor[sensor_name]
                distance = abs(payload.process_data.pv.value - peer_payload.process_data.pv.value)
                peer_distances.append(distance)
                per_pair_distances.append(
                    PairwiseDistanceEvidence(
                        peer_edge_id=peer_edge_id,
                        sensor_name=sensor_name,
                        distance_value=round(distance, 3),
                        unit=payload.process_data.pv.unit,
                    )
                )

            mean_distance = sum(peer_distances) / len(peer_distances)
            sensor_deviations.append(
                SensorDeviationEvidence(
                    sensor_name=sensor_name,
                    deviation_value=round(mean_distance, 3),
                    unit=payload.process_data.pv.unit,
                )
            )

        compatible_peer_count = sum(
            1
            for peer_edge_id in peer_edges
            if pairwise_distances[(edge_id, peer_edge_id)] <= PAIRWISE_CONSISTENCY_THRESHOLD
        )
        overall_normalized_deviation = round(
            sum(pairwise_distances[(edge_id, peer_edge_id)] for peer_edge_id in peer_edges)
            / len(peer_edges),
            3,
        )
        score = round(1.0 / (1.0 + overall_normalized_deviation), 3)
        ranking_entries.append(TrustRankEntry(edge_id=edge_id, score=score))
        trust_evidence.append(
            PerEdgeTrustEvidence(
                round_identity=round_identity,
                edge_id=edge_id,
                score=score,
                compatible_peer_count=compatible_peer_count,
                overall_normalized_deviation=overall_normalized_deviation,
                sensor_deviations=tuple(sensor_deviations),
                pairwise_distances=tuple(per_pair_distances),
            )
        )

        if compatible_peer_count + 1 < quorum:
            primary_reason = (
                ExclusionReason.SUSPECTED_BYZANTINE_BEHAVIOR
                if overall_normalized_deviation >= SUSPECTED_BYZANTINE_THRESHOLD
                else ExclusionReason.INCONSISTENT_VIEW
            )
            for deviation in sensor_deviations:
                normalized = deviation.deviation_value / SENSOR_SCALES[deviation.sensor_name].normalization_scale
                detail_parts.append(
                    f"{deviation.sensor_name}:{deviation.deviation_value:.3f}{deviation.unit}"
                    f"(norm={normalized:.3f})"
                )
            exclusions.append(
                ExclusionDecision(
                    round_identity=round_identity,
                    edge_id=edge_id,
                    reason=primary_reason,
                    detail=(
                        f"compatible_peers={compatible_peer_count}, "
                        f"overall_normalized_deviation={overall_normalized_deviation:.3f}, "
                        + ", ".join(detail_parts)
                    ),
                )
            )

    ranking = TrustRanking(
        round_identity=round_identity,
        participating_edges=participating_edges,
        entries=tuple(ranking_entries),
    )
    return ranking, tuple(exclusions), tuple(trust_evidence)
