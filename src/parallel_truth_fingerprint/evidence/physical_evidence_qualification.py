"""Pure, read-only G2 physical-evidence qualification gates.

All facts and resolvers are injected.  This module does not repair evidence,
run an experiment, access storage, resolve restricted bytes, or publish.
"""
from __future__ import annotations

from dataclasses import dataclass, replace
from typing import Callable, Mapping

from parallel_truth_fingerprint.contracts.physical_evidence_qualification import (
    PHYSICAL_EVIDENCE_QUALIFICATION_VERSION, PhysicalEvidenceQualificationResult,
    QualificationCheck, QualificationCheckDisposition, QualificationDisposition,
    physical_evidence_qualification_content_id,
)
from parallel_truth_fingerprint.contracts.scientific_governance import is_immutable_id
from parallel_truth_fingerprint.contracts.signal_observation import SignalObservation, parse_signal_observation
from parallel_truth_fingerprint.evidence.scenario_truth_validation import ReferenceDescriptor, validate_public_boundary


ImmutableResolver = Callable[[str], bool]
BoundaryResolver = Callable[[str], ReferenceDescriptor | None]


@dataclass(frozen=True)
class FeatureProjection:
    projection_id: str
    input_closure_id: str
    feature_ids: tuple[str, ...]
    canonical_output: bytes


@dataclass(frozen=True)
class ProjectionComparison:
    batch: FeatureProjection | None
    live: FeatureProjection | None
    tolerance_id: str | None
    tolerance_applicable: bool


@dataclass(frozen=True)
class PhysicalQualificationInput:
    run_manifest_id: str
    run_receipt_id: str | None
    actual_run_status: str
    execution_modality: str
    closure_ids: tuple[str, ...]
    observations: tuple[SignalObservation, ...]
    expected_observation_ids: tuple[str, ...]
    experiment_id: str
    run_id: str
    expected_stream_ids: tuple[str, ...]
    public_boundary: Mapping[str, object]
    limitations: tuple[str, ...]
    projection_comparison: ProjectionComparison | None = None


def _check(name: str, disposition: QualificationCheckDisposition, *codes: str, affected: tuple[str, ...] = ()) -> QualificationCheck:
    return QualificationCheck(name, disposition, affected, codes)


def _check_projection(comparison: ProjectionComparison | None, resolver: ImmutableResolver) -> QualificationCheck:
    if comparison is None:
        return _check("feature_projection_parity", QualificationCheckDisposition.BLOCKED, "PEQ2_PROJECTION_UNAVAILABLE")
    if comparison.batch is None or comparison.live is None:
        return _check("feature_projection_parity", QualificationCheckDisposition.INCOMPLETE, "PEQ2_PROJECTION_PATH_MISSING")
    values = (comparison.batch.projection_id, comparison.live.projection_id, comparison.batch.input_closure_id,
              comparison.live.input_closure_id, comparison.tolerance_id)
    if any(not is_immutable_id(value) or not resolver(value) for value in values if value is not None):
        return _check("feature_projection_parity", QualificationCheckDisposition.BLOCKED, "PEQ2_PROJECTION_REFERENCE_UNRESOLVED")
    if comparison.tolerance_id is None or not comparison.tolerance_applicable:
        return _check("feature_projection_parity", QualificationCheckDisposition.BLOCKED, "PEQ2_TOLERANCE_UNAVAILABLE")
    if (comparison.batch.input_closure_id != comparison.live.input_closure_id
            or tuple(comparison.batch.feature_ids) != tuple(comparison.live.feature_ids)
            or comparison.batch.canonical_output != comparison.live.canonical_output):
        return _check("feature_projection_parity", QualificationCheckDisposition.FAIL, "PEQ2_PROJECTION_MISMATCH",
                      affected=(comparison.batch.projection_id, comparison.live.projection_id))
    return _check("feature_projection_parity", QualificationCheckDisposition.PASS)


def qualify_physical_evidence(candidate: PhysicalQualificationInput, *, immutable_resolver: ImmutableResolver,
                              boundary_resolver: BoundaryResolver) -> PhysicalEvidenceQualificationResult:
    """Assess a supplied public closure without mutating it or assigning authority."""
    checks: list[QualificationCheck] = []
    closure = (candidate.run_manifest_id, *candidate.closure_ids)
    missing = tuple(value for value in closure if not is_immutable_id(value))
    unresolved = tuple(value for value in closure if is_immutable_id(value) and not immutable_resolver(value))
    if missing:
        checks.append(_check("immutable_closure", QualificationCheckDisposition.INCOMPLETE, "PEQ2_CLOSURE_ID_MISSING", affected=missing))
    elif unresolved:
        checks.append(_check("immutable_closure", QualificationCheckDisposition.BLOCKED, "PEQ2_CLOSURE_UNRESOLVED", affected=unresolved))
    else:
        checks.append(_check("immutable_closure", QualificationCheckDisposition.PASS))
    if candidate.run_receipt_id is None:
        checks.append(_check("final_run_closure", QualificationCheckDisposition.INCOMPLETE, "PEQ2_FINAL_RECEIPT_MISSING"))
    elif not is_immutable_id(candidate.run_receipt_id) or not immutable_resolver(candidate.run_receipt_id):
        checks.append(_check("final_run_closure", QualificationCheckDisposition.BLOCKED, "PEQ2_FINAL_RECEIPT_UNVERIFIED", affected=(candidate.run_receipt_id,)))
    else:
        checks.append(_check("final_run_closure", QualificationCheckDisposition.PASS))
    if candidate.actual_run_status != "complete":
        checks.append(_check("actual_run_status", QualificationCheckDisposition.FAIL, "PEQ2_RUN_NOT_COMPLETE"))
    else:
        checks.append(_check("actual_run_status", QualificationCheckDisposition.PASS))
    if candidate.execution_modality not in {"controlled_custom_physical", "admitted_emulator"}:
        checks.append(_check("claim_safe_modality", QualificationCheckDisposition.BLOCKED, "PEQ2_MODALITY_UNDECLARED"))
    else:
        checks.append(_check("claim_safe_modality", QualificationCheckDisposition.PASS))

    observed_ids: list[str] = []
    signal_errors: list[str] = []
    for observation in candidate.observations:
        try:
            parsed = parse_signal_observation(observation.to_dict())
            payload = parsed.to_dict()
            observed_ids.append(payload["observation_content_id"])
            if payload["experiment_id"] != candidate.experiment_id or payload["run_id"] != candidate.run_id:
                signal_errors.append("PEQ2_OBSERVATION_RUN_MISMATCH")
            if payload["source_stream_id"] not in candidate.expected_stream_ids:
                signal_errors.append("PEQ2_OBSERVATION_STREAM_MISMATCH")
        except Exception:
            signal_errors.append("PEQ2_OBSERVATION_INVALID")
    expected = tuple(sorted(set(candidate.expected_observation_ids)))
    if tuple(sorted(set(observed_ids))) != expected or len(observed_ids) != len(set(observed_ids)):
        signal_errors.append("PEQ2_OBSERVATION_CLOSURE_MISMATCH")
    checks.append(_check("g2_signal_invariants", QualificationCheckDisposition.FAIL if signal_errors else QualificationCheckDisposition.PASS,
                         *signal_errors, affected=tuple(observed_ids)))

    boundary = validate_public_boundary(candidate.public_boundary, resolver=boundary_resolver)
    checks.append(_check("public_truth_isolation", QualificationCheckDisposition.PASS if boundary.valid else QualificationCheckDisposition.FAIL,
                         *[item.rule_id for item in boundary.violations]))
    checks.append(_check_projection(candidate.projection_comparison, immutable_resolver))
    dispositions = {str(item.disposition) for item in checks}
    if QualificationCheckDisposition.INCOMPLETE.value in dispositions:
        result_disposition = QualificationDisposition.INCOMPLETE
    elif QualificationCheckDisposition.BLOCKED.value in dispositions:
        result_disposition = QualificationDisposition.BLOCKED
    elif QualificationCheckDisposition.FAIL.value in dispositions:
        result_disposition = QualificationDisposition.NOT_QUALIFIED
    else:
        result_disposition = QualificationDisposition.QUALIFIED
    provisional = PhysicalEvidenceQualificationResult(
        PHYSICAL_EVIDENCE_QUALIFICATION_VERSION, candidate.run_manifest_id, candidate.run_receipt_id,
        candidate.actual_run_status, candidate.execution_modality, candidate.closure_ids, tuple(observed_ids),
        tuple(checks), result_disposition, candidate.limitations, "",
    )
    return replace(provisional, result_content_id=physical_evidence_qualification_content_id(provisional))
