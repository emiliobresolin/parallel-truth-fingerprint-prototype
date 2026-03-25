"""Deterministic trust evaluation for prototype consensus."""

from __future__ import annotations

from dataclasses import dataclass
from statistics import median

from parallel_truth_fingerprint.contracts.edge_local_replicated_state import (
    EdgeLocalReplicatedStateContract,
)
from parallel_truth_fingerprint.contracts.exclusion_decision import ExclusionDecision
from parallel_truth_fingerprint.contracts.exclusion_reason import ExclusionReason
from parallel_truth_fingerprint.contracts.round_identity import RoundIdentity
from parallel_truth_fingerprint.contracts.trust_ranking import TrustRankEntry, TrustRanking


@dataclass(frozen=True)
class SensorTolerance:
    inconsistent_threshold: float
    suspicious_threshold: float


SENSOR_TOLERANCES = {
    "temperature": SensorTolerance(5.0, 20.0),
    "pressure": SensorTolerance(0.8, 3.0),
    "rpm": SensorTolerance(120.0, 600.0),
}


def _sensor_value(state: EdgeLocalReplicatedStateContract, sensor_name: str) -> float:
    return state.observations_by_sensor[sensor_name].process_data.pv.value


def evaluate_trust(
    *,
    round_identity: RoundIdentity,
    participating_edges: tuple[str, ...],
    replicated_states: tuple[EdgeLocalReplicatedStateContract, ...],
) -> tuple[TrustRanking, tuple[ExclusionDecision, ...]]:
    """Compute deterministic trust ranking and bounded exclusions."""

    by_edge = {state.owner_edge_id: state for state in replicated_states}
    medians = {
        sensor_name: median(
            _sensor_value(state, sensor_name) for state in replicated_states
        )
        for sensor_name in ("temperature", "pressure", "rpm")
    }

    ranking_entries: list[TrustRankEntry] = []
    exclusions: list[ExclusionDecision] = []

    for edge_id in participating_edges:
        state = by_edge[edge_id]
        max_ratio = 0.0
        primary_reason: ExclusionReason | None = None
        detail_parts: list[str] = []

        for sensor_name, tolerance in SENSOR_TOLERANCES.items():
            deviation = abs(_sensor_value(state, sensor_name) - medians[sensor_name])
            ratio = deviation / tolerance.suspicious_threshold
            max_ratio = max(max_ratio, ratio)

            if deviation > tolerance.suspicious_threshold:
                primary_reason = ExclusionReason.SUSPECTED_BYZANTINE_BEHAVIOR
                detail_parts.append(f"{sensor_name}:{deviation:.3f}")
            elif deviation > tolerance.inconsistent_threshold and primary_reason is None:
                primary_reason = ExclusionReason.INCONSISTENT_VIEW
                detail_parts.append(f"{sensor_name}:{deviation:.3f}")

        score = round(max(0.0, 1.0 - max_ratio), 3)
        ranking_entries.append(TrustRankEntry(edge_id=edge_id, score=score))

        if primary_reason is not None:
            exclusions.append(
                ExclusionDecision(
                    round_identity=round_identity,
                    edge_id=edge_id,
                    reason=primary_reason,
                    detail=", ".join(detail_parts) if detail_parts else None,
                )
            )

    ranking = TrustRanking(
        round_identity=round_identity,
        participating_edges=participating_edges,
        entries=tuple(ranking_entries),
    )
    return ranking, tuple(exclusions)
