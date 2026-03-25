"""Structured consensus round logging derived from audit output."""

from __future__ import annotations

from parallel_truth_fingerprint.contracts.consensus_audit_package import (
    ConsensusAuditPackage,
)
from parallel_truth_fingerprint.contracts.consensus_round_log import ConsensusRoundLog


def build_round_log(audit_package: ConsensusAuditPackage) -> ConsensusRoundLog:
    """Build a structured round log without recomputing trust decisions."""

    return ConsensusRoundLog(
        round_identity=audit_package.round_input.round_identity,
        participating_edges=audit_package.round_input.participating_edges,
        trust_ranking=audit_package.trust_ranking,
        exclusions=audit_package.exclusions,
        trust_evidence=audit_package.trust_evidence,
        final_status=audit_package.final_status,
        consensused_valid_state=audit_package.consensused_valid_state,
    )


def format_round_log_compact(round_log: ConsensusRoundLog) -> str:
    """Render a compact deterministic log line for one round."""

    if round_log.exclusions:
        exclusions_text = ", ".join(
            f"{exclusion.edge_id}:{exclusion.reason.value}" for exclusion in round_log.exclusions
        )
    else:
        exclusions_text = "none"

    return (
        f"{round_log.round_identity.round_id}: "
        f"status={round_log.final_status.value} "
        f"participants={len(round_log.participating_edges)} "
        f"excluded={len(round_log.exclusions)} "
        f"exclusions[{exclusions_text}]"
    )


def format_round_log_detailed(round_log: ConsensusRoundLog) -> str:
    """Render a readable detailed round log from the structured log object."""

    lines = [
        f"round={round_log.round_identity.round_id}",
        f"status={round_log.final_status.value}",
        f"participants={', '.join(round_log.participating_edges)}",
    ]

    for evidence in round_log.trust_evidence:
        deviation_text = ", ".join(
            f"{deviation.sensor_name}={deviation.deviation_value:.3f} {deviation.unit}"
            for deviation in evidence.sensor_deviations
        )
        lines.append(
            f"edge={evidence.edge_id} score={evidence.score:.3f} deviations[{deviation_text}]"
        )

    for exclusion in round_log.exclusions:
        lines.append(
            f"excluded={exclusion.edge_id} reason={exclusion.reason.value} detail={exclusion.detail}"
        )

    if round_log.consensused_valid_state is None:
        lines.append("consensused_valid_state=absent")
    else:
        sensor_text = ", ".join(
            f"{sensor}={value}"
            for sensor, value in sorted(round_log.consensused_valid_state.sensor_values.items())
        )
        lines.append(f"consensused_valid_state=present [{sensor_text}]")

    return "\n".join(lines)
