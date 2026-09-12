"""Pure fail-closed admission and stream-closure checks for Story 10.6.

The module deliberately owns no side effects.  A caller must separately own
control, collection, persistence, restricted truth, and publication.
"""

from __future__ import annotations

import hashlib
import re
from dataclasses import dataclass
from typing import Callable, Iterable

from parallel_truth_fingerprint.contracts.experiment_spec import ExperimentMatrixRow, ExperimentSpec, ExperimentSpecValidator
from parallel_truth_fingerprint.contracts.physical_run import (
    ExecutionModality, PhysicalRunRequest, StreamRecord, StreamRequirement, StreamStatus,
)


_DIGEST = re.compile(r"sha256:[0-9a-f]{64}\Z")


@dataclass(frozen=True)
class PhysicalRunViolation:
    rule_id: str
    field: str
    detail: str


@dataclass(frozen=True)
class PhysicalRunAdmission:
    allowed: bool
    violations: tuple[PhysicalRunViolation, ...]
    authorization_effect: str = "none"


@dataclass(frozen=True)
class StreamDefect:
    rule_id: str
    stream_id: str
    edge_id: str
    sensor_id: str
    source_sequence: int | None


@dataclass(frozen=True)
class StreamCompleteness:
    status: StreamStatus
    defects: tuple[StreamDefect, ...]
    retained_records: tuple[StreamRecord, ...]
    authorization_effect: str = "none"


def _valid_id(value: object) -> bool:
    return isinstance(value, str) and _DIGEST.fullmatch(value) is not None


def _violation(rule_id: str, field: str, detail: str) -> PhysicalRunViolation:
    return PhysicalRunViolation(rule_id, field, detail)


def authorize_physical_run_request(
    request: PhysicalRunRequest,
    *,
    spec: ExperimentSpec,
    matrix_rows: Iterable[ExperimentMatrixRow],
    spec_validator: ExperimentSpecValidator,
    immutable_resolver: Callable[[str], bool],
    repository_qualified: Callable[[str], bool],
    authorization_validator: Callable[[str, str, str], bool],
) -> PhysicalRunAdmission:
    """Validate only immutable prerequisites before a separate run side effect.

    ``authorization_validator`` is the sole authorization delegation point.
    It receives exactly action, authorization identity, and projection scope.
    """
    violations: list[PhysicalRunViolation] = []
    spec_result = spec_validator.validate(spec)
    if not spec_result.execution_eligible:
        violations.append(_violation("PRV1_SPEC_NOT_ELIGIBLE", "experiment_spec", "frozen_spec_required"))
    rows = tuple(matrix_rows)
    matched = [row for row in rows if row.run_binding_id == request.projection.run_binding_id]
    if len(matched) != 1 or request.projection.matrix_row_id != (matched[0].row_content_sha256 if matched else None):
        violations.append(_violation("PRV1_MATRIX_BINDING_MISMATCH", "projection.matrix_row_id", "exact_declared_row_required"))
    if request.projection.experiment_spec_id != spec.payload["content_sha256"]:
        violations.append(_violation("PRV1_SPEC_BINDING_MISMATCH", "projection.experiment_spec_id", "exact_frozen_spec_required"))
    if not _valid_id(request.request_id) or request.projection.authorization_effect != "none" or request.authorization_effect != "none":
        violations.append(_violation("PRV1_REQUEST_SHAPE_INVALID", "request", "immutable_non_authorizing_request_required"))
    reference_fields = {
        "projection.projection_id": request.projection.projection_id,
        "projection.input_trace_id": request.projection.input_trace_id,
        "profile_revision_id": request.profile_revision_id,
        "parameter_gate_result_id": request.parameter_gate_result_id,
        "repository_qualification_id": request.repository_qualification_id,
    }
    for field, identity in reference_fields.items():
        if not _valid_id(identity) or not immutable_resolver(identity):
            violations.append(_violation("PRV1_PREREQUISITE_UNRESOLVED", field, "exact_immutable_resolution_required"))
    if not repository_qualified(request.repository_qualification_id):
        violations.append(_violation("PRV1_REPOSITORY_UNQUALIFIED", "repository_qualification_id", "qualified_exact_report_required"))
    if len(request.authorization_ids) != 2 or len(set(request.authorization_ids)) != 2:
        violations.append(_violation("PRV1_AUTHORIZATION_SET_INVALID", "authorization_ids", "two_distinct_authorizations_required"))
    else:
        for action, identity in zip(("feature_activation", "experiment_execution"), request.authorization_ids):
            if not _valid_id(identity) or not authorization_validator(action, identity, request.projection.projection_id):
                violations.append(_violation("PRV1_AUTHORIZATION_DENIED", action, "approved_exact_scope_required"))
    if str(request.modality) not in {item.value for item in ExecutionModality}:
        violations.append(_violation("PRV1_MODALITY_INVALID", "modality", "closed_declared_modality_required"))
    if str(request.modality) == ExecutionModality.PHYSICAL_HARDWARE.value:
        identity = request.physical_acquisition_authorization_id
        if not _valid_id(identity):
            violations.append(_violation("PRV1_PHYSICAL_ACQUISITION_REQUIRED", "physical_acquisition_authorization_id", "exact_authorization_required"))
        elif not authorization_validator("physical_acquisition", identity, request.projection.projection_id):
            violations.append(_violation("PRV1_AUTHORIZATION_DENIED", "physical_acquisition", "approved_exact_scope_required"))
    requirements = request.stream_requirements
    keys = [(item.stream_id, item.edge_id, item.sensor_id) for item in requirements]
    if not requirements or len(keys) != len(set(keys)) or any(item.first_sequence < 1 or item.last_sequence < item.first_sequence for item in requirements):
        violations.append(_violation("PRV1_STREAM_REQUIREMENTS_INVALID", "stream_requirements", "unique_positive_closed_intervals_required"))
    return PhysicalRunAdmission(not violations, tuple(violations))


def validate_stream_completeness(
    requirements: Iterable[StreamRequirement], records: Iterable[StreamRecord],
) -> StreamCompleteness:
    """Report defects while returning original immutable record facts unchanged."""
    required = tuple(requirements)
    retained = tuple(records)
    defects: list[StreamDefect] = []
    scopes = {(item.stream_id, item.edge_id, item.sensor_id): item for item in required}
    per_scope: dict[tuple[str, str, str], dict[int, StreamRecord]] = {key: {} for key in scopes}
    last_seen: dict[tuple[str, str, str], int] = {}
    for record in retained:
        key = (record.stream_id, record.edge_id, record.sensor_id)
        requirement = scopes.get(key)
        if requirement is None:
            defects.append(StreamDefect("PRV1_STREAM_SCOPE_MISMATCH", *key, record.source_sequence))
            continue
        if record.source_sequence < requirement.first_sequence or record.source_sequence > requirement.last_sequence:
            defects.append(StreamDefect("PRV1_STREAM_SEQUENCE_OUTSIDE_DECLARATION", *key, record.source_sequence))
        prior_sequence = last_seen.get(key)
        if prior_sequence is not None and record.source_sequence < prior_sequence:
            defects.append(StreamDefect("PRV1_STREAM_OUT_OF_ORDER", *key, record.source_sequence))
        last_seen[key] = record.source_sequence
        expected_hash = "sha256:" + hashlib.sha256(record.canonical_bytes).hexdigest()
        if record.content_sha256 != expected_hash:
            defects.append(StreamDefect("PRV1_STREAM_HASH_MISMATCH", *key, record.source_sequence))
        prior = per_scope[key].get(record.source_sequence)
        if prior is not None:
            rule = "PRV1_STREAM_DUPLICATE" if prior == record else "PRV1_STREAM_DIVERGENT_DUPLICATE"
            defects.append(StreamDefect(rule, *key, record.source_sequence))
        else:
            per_scope[key][record.source_sequence] = record
    for key, requirement in scopes.items():
        observed = per_scope[key]
        for sequence in range(requirement.first_sequence, requirement.last_sequence + 1):
            if sequence not in observed:
                defects.append(StreamDefect("PRV1_STREAM_MISSING", *key, sequence))
    return StreamCompleteness(StreamStatus.COMPLETE if not defects else StreamStatus.INCOMPLETE, tuple(defects), retained)
