"""Structured and formatted observability helpers for consensus rounds."""

from __future__ import annotations

from parallel_truth_fingerprint.consensus.quorum import required_quorum
from parallel_truth_fingerprint.contracts.consensus_audit_package import (
    ConsensusAuditPackage,
)
from parallel_truth_fingerprint.contracts.consensus_round_summary import (
    ConsensusRoundSummary,
    ExcludedEdgeSummary,
)


def build_round_summary(audit_package: ConsensusAuditPackage) -> ConsensusRoundSummary:
    """Derive a deterministic structured summary from one audit package."""

    exclusions = tuple(
        ExcludedEdgeSummary(
            edge_id=decision.edge_id,
            reason=decision.reason.value,
            detail=decision.detail,
        )
        for decision in audit_package.exclusions
    )
    total_participants = len(audit_package.round_input.participating_edges)
    excluded_edge_ids = tuple(exclusion.edge_id for exclusion in exclusions)
    exclusion_reasons = tuple(exclusion.reason for exclusion in exclusions)

    return ConsensusRoundSummary(
        round_id=audit_package.round_input.round_identity.round_id,
        total_participants=total_participants,
        quorum_required=required_quorum(total_participants),
        valid_participants_after_exclusions=total_participants - len(exclusions),
        excluded_edge_ids=excluded_edge_ids,
        exclusion_reasons=exclusion_reasons,
        excluded_edges=exclusions,
        final_consensus_status=audit_package.final_status,
        has_consensused_valid_state=audit_package.consensused_valid_state is not None,
    )


def format_round_summary(summary: ConsensusRoundSummary) -> str:
    """Render one compact deterministic summary line for demo output."""

    if summary.excluded_edges:
        exclusions_text = ", ".join(
            f"{excluded.edge_id}:{excluded.reason}" for excluded in summary.excluded_edges
        )
    else:
        exclusions_text = "none"

    valid_state_text = "present" if summary.has_consensused_valid_state else "absent"
    return (
        f"{summary.round_id}: "
        f"participants={summary.total_participants} "
        f"quorum={summary.quorum_required} "
        f"valid={summary.valid_participants_after_exclusions} "
        f"status={summary.final_consensus_status.value} "
        f"valid_state={valid_state_text} "
        f"exclusions[{exclusions_text}]"
    )
