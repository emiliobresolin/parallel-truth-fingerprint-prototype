"""Persist valid structured consensus artifacts only for successful rounds."""

from __future__ import annotations

from dataclasses import replace
from datetime import datetime, timezone

from parallel_truth_fingerprint.consensus.quorum import required_quorum
from parallel_truth_fingerprint.contracts.consensus_audit_package import (
    ConsensusAuditPackage,
)
from parallel_truth_fingerprint.contracts.consensus_status import ConsensusStatus
from parallel_truth_fingerprint.contracts.edge_local_replicated_state import (
    EdgeLocalReplicatedStateContract,
)
from parallel_truth_fingerprint.contracts.persistence_record import (
    ValidConsensusArtifactRecord,
)
from parallel_truth_fingerprint.contracts.raw_hart_payload import RawHartPayload
from parallel_truth_fingerprint.contracts.scada_comparison_output import (
    ScadaComparisonOutput,
)
from parallel_truth_fingerprint.contracts.scada_state import ScadaState
from parallel_truth_fingerprint.contracts.scada_alert import ScadaAlert


class PersistenceBlockedError(RuntimeError):
    """Raised when invalid or pre-consensus data attempts to enter persistence."""


def persist_valid_consensus_artifact(
    *,
    audit_package: ConsensusAuditPackage,
    scada_state: ScadaState,
    scada_comparison_output: ScadaComparisonOutput,
    scada_alert: ScadaAlert | None = None,
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
    round_identity = _serialize_round_identity(valid_state.round_identity)
    payload_snapshot = _build_validated_payload_snapshot(audit_package)

    record = ValidConsensusArtifactRecord(
        artifact_key=artifact_key,
        persisted_at=persisted_at.isoformat(),
        artifact_identity={
            "artifact_type": "valid_consensus_artifact",
            "artifact_version": "2.0",
            "record_id": f"valid-consensus-artifact::{artifact_key}",
        },
        round_identity=round_identity,
        consensus_context={
            "final_consensus_status": audit_package.final_status.value,
            "participating_edges": list(audit_package.round_input.participating_edges),
            "quorum_required": required_quorum(
                len(audit_package.round_input.participating_edges)
            ),
            "source_edges": list(valid_state.source_edges),
            "trust_ranking": [
                {
                    "edge_id": entry.edge_id,
                    "score": entry.score,
                }
                for entry in audit_package.trust_ranking.entries
            ],
            "exclusions": [
                {
                    "edge_id": exclusion.edge_id,
                    "reason": exclusion.reason.value,
                    "detail": exclusion.detail,
                }
                for exclusion in audit_package.exclusions
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
                            "peer_edge_id": distance.peer_edge_id,
                            "sensor_name": distance.sensor_name,
                            "distance_value": distance.distance_value,
                            "unit": distance.unit,
                        }
                        for distance in evidence.pairwise_distances
                    ],
                }
                for evidence in audit_package.trust_evidence
            ],
        },
        validated_state={
            "state_type": "consensused_valid_state",
            "source_edges": list(valid_state.source_edges),
            "sensor_values": dict(valid_state.sensor_values),
            "structured_payload_snapshot": payload_snapshot,
        },
        scada_context={
            "scada_state": scada_state.to_dict(),
            "comparison_output": scada_comparison_output.to_dict(),
            "divergence_alert": None if scada_alert is None else scada_alert.to_dict(),
        },
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


def _serialize_round_identity(round_identity) -> dict[str, object]:
    return {
        "round_id": round_identity.round_id,
        "window_started_at": round_identity.window_started_at.isoformat(),
        "window_ended_at": round_identity.window_ended_at.isoformat(),
    }


def _build_validated_payload_snapshot(
    audit_package: ConsensusAuditPackage,
) -> dict[str, object]:
    valid_state = audit_package.consensused_valid_state
    if valid_state is None:
        raise PersistenceBlockedError(
            "Validated payload snapshot requires a consensused valid state."
        )

    source_state = _select_validated_source_state(audit_package, valid_state.source_edges)
    payloads_by_sensor = {}
    for sensor_name, payload in sorted(source_state.observations_by_sensor.items()):
        payloads_by_sensor[sensor_name] = _build_validated_payload(
            payload=payload,
            consensused_value=valid_state.sensor_values[sensor_name],
        ).to_dict()

    return {
        "snapshot_type": "validated_source_view",
        "selected_source_edge_id": source_state.owner_edge_id,
        "payloads_by_sensor": payloads_by_sensor,
    }


def _select_validated_source_state(
    audit_package: ConsensusAuditPackage,
    source_edges: tuple[str, ...],
) -> EdgeLocalReplicatedStateContract:
    for state in audit_package.round_input.replicated_states:
        if state.owner_edge_id in source_edges:
            return state
    raise PersistenceBlockedError(
        "Validated payload snapshot could not find a source edge view inside the round input."
    )


def _build_validated_payload(
    *,
    payload: RawHartPayload,
    consensused_value: float,
) -> RawHartPayload:
    return replace(
        payload,
        process_data=replace(
            payload.process_data,
            pv=replace(payload.process_data.pv, value=round(float(consensused_value), 3)),
        ),
    )
