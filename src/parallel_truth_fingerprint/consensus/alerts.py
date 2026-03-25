"""Consensus-specific alert generation derived from existing outputs."""

from __future__ import annotations

from parallel_truth_fingerprint.contracts.consensus_alert import (
    ConsensusAlert,
    ConsensusAlertType,
)
from parallel_truth_fingerprint.contracts.consensus_audit_package import (
    ConsensusAuditPackage,
)
from parallel_truth_fingerprint.contracts.consensus_round_log import ConsensusRoundLog
from parallel_truth_fingerprint.contracts.consensus_status import ConsensusStatus


def build_consensus_alert(
    audit_package: ConsensusAuditPackage,
    round_log: ConsensusRoundLog,
) -> ConsensusAlert | None:
    """Build a consensus alert strictly from existing audit/log outputs."""

    if audit_package.round_input.round_identity != round_log.round_identity:
        raise ValueError("Alert inputs must refer to the same round.")
    if audit_package.final_status != round_log.final_status:
        raise ValueError("Alert inputs must share the same final status.")
    if audit_package.exclusions != round_log.exclusions:
        raise ValueError("Alert inputs must share the same exclusions.")
    if audit_package.trust_evidence != round_log.trust_evidence:
        raise ValueError("Alert inputs must share the same trust evidence.")

    if audit_package.final_status != ConsensusStatus.FAILED_CONSENSUS:
        return None

    return ConsensusAlert(
        alert_type=ConsensusAlertType.CONSENSUS_FAILED,
        round_identity=audit_package.round_input.round_identity,
        final_status=audit_package.final_status,
        exclusions=audit_package.exclusions,
        trust_evidence=audit_package.trust_evidence,
    )


def format_consensus_alert_compact(alert: ConsensusAlert | None) -> str:
    """Render a compact deterministic alert line for demo output."""

    if alert is None:
        return "none"

    exclusions_text = ", ".join(
        f"{exclusion.edge_id}:{exclusion.reason.value}" for exclusion in alert.exclusions
    )
    return (
        f"{alert.round_identity.round_id}: "
        f"alert={alert.alert_type.value} "
        f"status={alert.final_status.value} "
        f"exclusions[{exclusions_text}]"
    )


def format_consensus_alert_detailed(alert: ConsensusAlert | None) -> str:
    """Render a readable detailed alert view from the structured alert object."""

    if alert is None:
        return "consensus_alert=none"

    lines = [
        f"alert_type={alert.alert_type.value}",
        f"round={alert.round_identity.round_id}",
        f"status={alert.final_status.value}",
    ]
    for exclusion in alert.exclusions:
        lines.append(
            f"excluded={exclusion.edge_id} reason={exclusion.reason.value} detail={exclusion.detail}"
        )
    for evidence in alert.trust_evidence:
        deviation_text = ", ".join(
            f"{deviation.sensor_name}={deviation.deviation_value:.3f} {deviation.unit}"
            for deviation in evidence.sensor_deviations
        )
        lines.append(
            f"evidence={evidence.edge_id} score={evidence.score:.3f} deviations[{deviation_text}]"
        )
    return "\n".join(lines)
