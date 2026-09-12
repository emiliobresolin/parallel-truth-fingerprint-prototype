"""Pure, injected qualification for a real Linux kernel capture boundary.

No capture implementation exists here.  Resolvers are deliberately injected so
unit tests and callers cannot accidentally use a local host, Docker, storage,
or a legacy/default qualification result.
"""
from __future__ import annotations

from dataclasses import dataclass, replace
from typing import Callable

from parallel_truth_fingerprint.contracts.linux_capture_boundary import (
    LINUX_CAPTURE_BOUNDARY_QUALIFICATION_VERSION, CaptureBoundaryDecision,
    CaptureBoundaryKind, CaptureCheckDisposition, CaptureEnvironment,
    CaptureMeasurement, CaptureOrigin, CaptureQualificationCheck,
    CaptureQualificationDisposition, LinuxCaptureBoundaryQualification,
    RawCaptureSegmentQualification, linux_capture_boundary_qualification_content_id,
)
from parallel_truth_fingerprint.contracts.scientific_governance import is_immutable_id


ImmutableResolver = Callable[[str], bool]
ParameterEvidenceResolver = Callable[[str], bool]
_REQUIRED_MEASUREMENTS = frozenset({
    "workload_attribution", "event_ordering", "duplicates", "gaps", "drops",
    "queue_behavior", "storage_lag", "capture_overhead", "raw_to_canonical_replay",
})


@dataclass(frozen=True)
class LinuxCaptureQualificationInput:
    candidate_boundary_id: str
    environment: CaptureEnvironment
    workload_identity: str
    run_identity: str
    measurements: tuple[CaptureMeasurement, ...]
    raw_segments: tuple[RawCaptureSegmentQualification, ...]
    decision: CaptureBoundaryDecision | str
    selected_boundary_id: str | None = None
    fallback_boundary_id: str | None = None
    limitations: tuple[str, ...] = ()


def _check(check_id: str, disposition: CaptureCheckDisposition, *codes: str,
           affected: tuple[str, ...] = ()) -> CaptureQualificationCheck:
    return CaptureQualificationCheck(check_id, disposition, affected, codes)


def _resolved(value: str | None, resolver: ImmutableResolver) -> bool:
    return bool(value and is_immutable_id(value) and resolver(value))


def _environment_ids(environment: CaptureEnvironment) -> tuple[str, ...]:
    return tuple(value for name, value in vars(environment).items() if name != "boundary_kind")


def qualify_linux_capture_boundary(
    candidate: LinuxCaptureQualificationInput, *, immutable_resolver: ImmutableResolver,
    parameter_evidence_resolver: ParameterEvidenceResolver,
) -> LinuxCaptureBoundaryQualification:
    """Validate only supplied evidence and return a non-authorizing record."""
    checks: list[CaptureQualificationCheck] = []
    environment_ids = _environment_ids(candidate.environment)
    closure = (candidate.candidate_boundary_id, candidate.workload_identity, candidate.run_identity, *environment_ids)
    invalid = tuple(value for value in closure if not is_immutable_id(value))
    unresolved = tuple(value for value in closure if is_immutable_id(value) and not immutable_resolver(value))
    if invalid:
        checks.append(_check("immutable_environment", CaptureCheckDisposition.INCOMPLETE, "LCB1_IDENTITY_MISSING", affected=invalid))
    elif unresolved:
        checks.append(_check("immutable_environment", CaptureCheckDisposition.BLOCKED, "LCB1_IDENTITY_UNRESOLVED", affected=unresolved))
    else:
        checks.append(_check("immutable_environment", CaptureCheckDisposition.PASS))

    kind = str(candidate.environment.boundary_kind)
    if kind not in {CaptureBoundaryKind.LINUX_HOST.value, CaptureBoundaryKind.LINUX_VM.value}:
        checks.append(_check("linux_kernel_boundary", CaptureCheckDisposition.FAIL, "LCB1_NON_LINUX_OR_UNKNOWN_BOUNDARY"))
    else:
        checks.append(_check("linux_kernel_boundary", CaptureCheckDisposition.PASS))

    measures = {item.measurement_kind: item for item in candidate.measurements}
    missing_measures = tuple(sorted(_REQUIRED_MEASUREMENTS - set(measures)))
    duplicate_kinds = len(measures) != len(candidate.measurements)
    bad_measurements: list[str] = []
    unresolved_parameters: list[str] = []
    failed_measurements: list[str] = []
    for item in candidate.measurements:
        if not item.evidence_ids or not all(_resolved(value, immutable_resolver) for value in item.evidence_ids):
            bad_measurements.append(item.measurement_kind)
        if not all(_resolved(value, parameter_evidence_resolver) for value in item.parameter_evidence_ids):
            unresolved_parameters.append(item.measurement_kind)
        if item.passed is not True:
            failed_measurements.append(item.measurement_kind)
    if missing_measures or duplicate_kinds or bad_measurements:
        checks.append(_check("capture_measurements", CaptureCheckDisposition.INCOMPLETE, "LCB1_MEASUREMENT_CLOSURE_INCOMPLETE", affected=tuple(sorted(set((*missing_measures, *bad_measurements))))))
    elif unresolved_parameters:
        checks.append(_check("capture_measurements", CaptureCheckDisposition.BLOCKED, "LCB1_PARAMETER_EVIDENCE_UNRESOLVED", affected=tuple(sorted(set(unresolved_parameters)))))
    elif failed_measurements:
        checks.append(_check("capture_measurements", CaptureCheckDisposition.FAIL, "LCB1_MEASUREMENT_POLICY_FAILED", affected=tuple(sorted(set(failed_measurements)))))
    else:
        checks.append(_check("capture_measurements", CaptureCheckDisposition.PASS))

    segments = candidate.raw_segments
    segment_ids = [item.segment_content_id for item in segments]
    bad_segments: list[str] = []
    origins: list[str] = []
    for item in segments:
        ids = (item.segment_content_id, item.raw_bytes_hash, item.collector_identity, item.filter_identity,
               item.host_or_vm_identity, item.boot_identity, item.kernel_identity, item.workload_identity,
               item.cgroup_identity, item.process_identity, item.run_identity, item.ordering_evidence_id,
               item.replay_evidence_id)
        if not all(_resolved(value, immutable_resolver) for value in ids): bad_segments.append(item.segment_content_id)
        if str(item.capture_origin) != CaptureOrigin.HOST_CAPTURE.value: origins.append(item.segment_content_id)
        if (item.collector_identity != candidate.environment.collector_identity or item.filter_identity != candidate.environment.filter_identity
                or item.host_or_vm_identity != candidate.environment.host_or_vm_identity or item.boot_identity != candidate.environment.boot_identity
                or item.kernel_identity != candidate.environment.kernel_identity or item.workload_identity != candidate.workload_identity
                or item.run_identity != candidate.run_identity): bad_segments.append(item.segment_content_id)
    if not segments or len(segment_ids) != len(set(segment_ids)) or bad_segments:
        checks.append(_check("raw_capture_replay_closure", CaptureCheckDisposition.INCOMPLETE, "LCB1_RAW_SEGMENT_PROVENANCE_INCOMPLETE", affected=tuple(sorted(set(bad_segments)))))
    elif origins:
        checks.append(_check("raw_capture_replay_closure", CaptureCheckDisposition.FAIL, "LCB1_CAPTURE_ORIGIN_INELIGIBLE", affected=tuple(sorted(origins))))
    else:
        checks.append(_check("raw_capture_replay_closure", CaptureCheckDisposition.PASS, affected=tuple(sorted(segment_ids))))

    decision = str(candidate.decision)
    selection_ids = tuple(value for value in (candidate.selected_boundary_id, candidate.fallback_boundary_id) if value is not None)
    if decision not in {item.value for item in CaptureBoundaryDecision}:
        checks.append(_check("boundary_decision", CaptureCheckDisposition.INCOMPLETE, "LCB1_DECISION_INVALID"))
    elif any(not _resolved(value, immutable_resolver) for value in selection_ids):
        checks.append(_check("boundary_decision", CaptureCheckDisposition.BLOCKED, "LCB1_DECISION_BOUNDARY_UNRESOLVED", affected=selection_ids))
    elif decision == CaptureBoundaryDecision.SELECTED.value and candidate.selected_boundary_id != candidate.candidate_boundary_id:
        checks.append(_check("boundary_decision", CaptureCheckDisposition.FAIL, "LCB1_SELECTED_BOUNDARY_MISMATCH"))
    elif decision == CaptureBoundaryDecision.REJECTED.value and candidate.fallback_boundary_id is None:
        checks.append(_check("boundary_decision", CaptureCheckDisposition.BLOCKED, "LCB1_PINNED_FALLBACK_MISSING"))
    elif decision == CaptureBoundaryDecision.BLOCKED.value:
        checks.append(_check("boundary_decision", CaptureCheckDisposition.BLOCKED, "LCB1_CAPTURE_ACTIVITY_BLOCKED"))
    else:
        checks.append(_check("boundary_decision", CaptureCheckDisposition.PASS))

    states = {str(item.disposition) for item in checks}
    disposition = (CaptureQualificationDisposition.INCOMPLETE if CaptureCheckDisposition.INCOMPLETE.value in states else
                   CaptureQualificationDisposition.BLOCKED if CaptureCheckDisposition.BLOCKED.value in states else
                   CaptureQualificationDisposition.NOT_QUALIFIED if CaptureCheckDisposition.FAIL.value in states else
                   CaptureQualificationDisposition.QUALIFIED)
    provisional = LinuxCaptureBoundaryQualification(
        LINUX_CAPTURE_BOUNDARY_QUALIFICATION_VERSION, candidate.candidate_boundary_id, candidate.environment,
        candidate.workload_identity, candidate.run_identity, candidate.measurements, candidate.raw_segments,
        candidate.decision, candidate.selected_boundary_id, candidate.fallback_boundary_id, tuple(checks),
        disposition, candidate.limitations, "",
    )
    return replace(provisional, qualification_content_id=linux_capture_boundary_qualification_content_id(provisional))
