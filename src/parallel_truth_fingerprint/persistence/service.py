"""Persist valid structured consensus artifacts only for successful rounds."""

from __future__ import annotations

from datetime import datetime, timezone

from parallel_truth_fingerprint.contracts.consensus_audit_package import (
    ConsensusAuditPackage,
)
from parallel_truth_fingerprint.contracts.consensus_status import ConsensusStatus
from parallel_truth_fingerprint.contracts.persistence_record import (
    ValidConsensusArtifactRecord,
)
from parallel_truth_fingerprint.contracts.scada_comparison_output import (
    ScadaComparisonOutput,
)


class PersistenceBlockedError(RuntimeError):
    """Raised when invalid or pre-consensus data attempts to enter persistence."""


def persist_valid_consensus_artifact(
    *,
    audit_package: ConsensusAuditPackage,
    scada_comparison_output: ScadaComparisonOutput,
    artifact_store,
    persisted_at: datetime | None = None,
) -> ValidConsensusArtifactRecord:
    """Persist one structured valid artifact into the configured object store."""

    if audit_package.final_status != ConsensusStatus.SUCCESS:
        raise PersistenceBlockedError(
            "Valid artifact persistence is blocked because consensus did not succeed."
        )
    if audit_package.consensused_valid_state is None:
        raise PersistenceBlockedError(
            "Valid artifact persistence is blocked because no consensused valid state exists."
        )
    if audit_package.round_input.round_identity != scada_comparison_output.round_identity:
        raise ValueError("Persistence inputs must share the same round identity.")

    valid_state = audit_package.consensused_valid_state
    persisted_at = persisted_at or datetime.now(timezone.utc)
    artifact_key = f"valid-consensus-artifacts/{valid_state.round_identity.round_id}.json"

    record = ValidConsensusArtifactRecord(
        artifact_key=artifact_key,
        persisted_at=persisted_at.isoformat(),
        consensus_state={
            "round_id": valid_state.round_identity.round_id,
            "source_edges": list(valid_state.source_edges),
            "sensor_values": dict(valid_state.sensor_values),
        },
        trust_scores=tuple(
            {
                "edge_id": entry.edge_id,
                "score": entry.score,
            }
            for entry in audit_package.trust_ranking.entries
        ),
        excluded_edges=tuple(
            {
                "edge_id": exclusion.edge_id,
                "reason": exclusion.reason.value,
                "detail": exclusion.detail,
            }
            for exclusion in audit_package.exclusions
        ),
        scada_comparison_results=scada_comparison_output.to_dict(),
        diagnostics={
            "final_consensus_status": audit_package.final_status.value,
            "has_scada_divergence": bool(scada_comparison_output.divergent_sensors),
            "divergent_sensors": list(scada_comparison_output.divergent_sensors),
            "participating_edges": list(audit_package.round_input.participating_edges),
            "persisted_record_type": "valid_consensus_artifact",
        },
    )
    artifact_store.save_json(artifact_key, record.to_dict())
    return record
