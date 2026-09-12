"""Deterministic validation and serialization for ParameterEvidence.v1."""

from __future__ import annotations

import hashlib
import json
import re
from dataclasses import fields
from datetime import datetime
from decimal import (
    Context,
    Decimal,
    DivisionByZero,
    FloatOperation,
    Inexact,
    InvalidOperation,
    Overflow,
    ROUND_HALF_EVEN,
    Rounded,
    Underflow,
    localcontext,
)
from pathlib import Path
from typing import Callable, Mapping

from parallel_truth_fingerprint.contracts.parameter_evidence import *
from parallel_truth_fingerprint.contracts.semantic_vocabulary import (
    SEMANTIC_VOCABULARY_VERSION,
    SyntheticStatus,
)
from parallel_truth_fingerprint.contracts.source_catalog import (
    AuthorityRole,
    ClaimUse,
    RetrievalStatus,
    SourceCatalog,
    SourceType,
    SourceUseStatus,
    VerificationStatus,
)
from parallel_truth_fingerprint.evidence.source_catalog import (
    canonical_catalog_bytes,
    validate_source_catalog,
)


DECIMAL_PATTERN = re.compile(r"^-?(0|[1-9][0-9]*)(\.[0-9]*[1-9])?$")
DIGEST_PATTERN = re.compile(r"^sha256:[0-9a-f]{64}$")
AFFINE_OPERATION = "affine_map.v1"
VALIDATOR_IDENTITY = "sha256:" + hashlib.sha256(
    b"ParameterEvidence.v1/accountability-gate/affine_map.v1/decimal50-half-even"
).hexdigest()
UNIT_BY_QUANTITY = {
    QuantityKind.LOOP_CURRENT.value: {Unit.MILLIAMPERE.value},
    QuantityKind.NORMALIZED_SPAN.value: {Unit.ONE.value},
    QuantityKind.TEMPERATURE.value: {Unit.DEG_C.value},
    QuantityKind.PRESSURE_GAUGE.value: {Unit.BAR.value},
    QuantityKind.PRESSURE_ABSOLUTE.value: {Unit.BAR.value},
    QuantityKind.ROTATIONAL_SPEED.value: {Unit.RPM.value},
    QuantityKind.SPEED_REFERENCE.value: {Unit.PERCENT.value},
    QuantityKind.CAPACITY_REFERENCE.value: {Unit.PERCENT.value},
    QuantityKind.POWER_REFERENCE.value: {Unit.PERCENT.value},
    QuantityKind.WINDOW_LENGTH.value: {Unit.COUNT.value},
    QuantityKind.QUEUE_CAPACITY.value: {Unit.COUNT.value, Unit.BYTE.value},
    QuantityKind.CAPTURE_LOSS_FRACTION.value: {Unit.ONE.value},
    QuantityKind.DURATION.value: {Unit.SECOND.value, Unit.MILLISECOND.value},
    QuantityKind.RAMP_DURATION.value: {Unit.SECOND.value, Unit.MILLISECOND.value},
    QuantityKind.DWELL_DURATION.value: {Unit.SECOND.value, Unit.MILLISECOND.value},
    QuantityKind.REPETITION_COUNT.value: {Unit.COUNT.value},
    QuantityKind.RANDOM_SEED.value: {Unit.COUNT.value},
    QuantityKind.SPLIT_FRACTION.value: {Unit.ONE.value},
}
QUANTITY_LOCATOR_TERMS = {
    QuantityKind.LOOP_CURRENT.value: ("current", "ma"),
    QuantityKind.TEMPERATURE.value: ("temperature", "pt100", "degc"),
    QuantityKind.PRESSURE_GAUGE.value: ("gauge",),
    QuantityKind.PRESSURE_ABSOLUTE.value: ("absolute",),
    QuantityKind.ROTATIONAL_SPEED.value: ("rpm", "speed"),
}


def _token(value: object) -> str:
    return str(value.value if hasattr(value, "value") else value)


def _nonblank(value: object) -> bool:
    return isinstance(value, str) and bool(value.strip()) and value == value.strip()


def _enum(value: object, enum_type: type) -> bool:
    return _token(value) in {item.value for item in enum_type}


def _decimal(value: object) -> Decimal | None:
    if not isinstance(value, str) or DECIMAL_PATTERN.fullmatch(value) is None:
        return None
    parsed = Decimal(value)
    if parsed == 0 and value.startswith("-"):
        return None
    return parsed


def _instant(value: object) -> datetime | None:
    if not _nonblank(value):
        return None
    try:
        instant = datetime.fromisoformat(str(value))
        return instant if instant.tzinfo is not None and instant.utcoffset() is not None else None
    except ValueError:
        return None


def _reject_floats(value: object) -> None:
    if isinstance(value, float):
        raise ValueError("binary floats are forbidden in ParameterEvidence.v1")
    if isinstance(value, Mapping):
        for child in value.values():
            _reject_floats(child)
    elif isinstance(value, (list, tuple)):
        for child in value:
            _reject_floats(child)


def canonical_parameter_catalog_bytes(catalog: ParameterEvidenceCatalog) -> bytes:
    payload = catalog.to_dict()
    _reject_floats(payload)
    return (json.dumps(payload, sort_keys=True, ensure_ascii=False, separators=(",", ":"),
                       allow_nan=False) + "\n").encode("utf-8")


def parameter_catalog_identity(catalog: ParameterEvidenceCatalog) -> str:
    payload = catalog.to_dict()
    for required_set in payload["required_sets"]:
        required_set["catalog_identity"] = ""
    encoded = (json.dumps(payload, sort_keys=True, ensure_ascii=False, separators=(",", ":"),
                          allow_nan=False) + "\n").encode("utf-8")
    return "sha256:" + hashlib.sha256(encoded).hexdigest()


def source_catalog_identity(catalog: SourceCatalog) -> str:
    return "sha256:" + hashlib.sha256(canonical_catalog_bytes(catalog)).hexdigest()


def _record_identity(record: object, self_field: str) -> str:
    payload = record.to_dict()  # type: ignore[attr-defined]
    payload[self_field] = ""
    encoded = (json.dumps(payload, sort_keys=True, ensure_ascii=False, separators=(",", ":"),
                          allow_nan=False) + "\n").encode("utf-8")
    return "sha256:" + hashlib.sha256(encoded).hexdigest()


def parameter_revision_identity(record: ParameterRevision) -> str:
    return _record_identity(record, "revision_sha256")


def decision_record_identity(record: DecisionRecord) -> str:
    return _record_identity(record, "record_sha256")


def mock_admission_identity(record: MockAdmission) -> str:
    return _record_identity(record, "record_sha256")


def _violation(rule: str, record: object, field: str, offending: object, explanation: str) -> ParameterViolation:
    return ParameterViolation(rule, _token(record), field, _token(offending), explanation)


def _safe_path(root: Path, locator: object, resolver: Callable[[Path], Path] | None) -> Path | None:
    if not _nonblank(locator):
        return None
    relative = Path(str(locator))
    if relative.is_absolute() or any(part in {"", ".", ".."} for part in relative.parts):
        return None
    resolve = resolver or (lambda path: path.resolve(strict=False))
    resolved_root = resolve(root)
    resolved = resolve(resolved_root / relative)
    try:
        resolved.relative_to(resolved_root)
    except ValueError:
        return None
    return resolved


def _verify_bytes(path: Path, expected_size: int, expected_hash: str) -> bool:
    try:
        before = path.stat(follow_symlinks=False)
        if not path.is_file() or path.is_symlink():
            return False
        digest = hashlib.sha256()
        size = 0
        with path.open("rb") as stream:
            for chunk in iter(lambda: stream.read(1024 * 1024), b""):
                size += len(chunk)
                digest.update(chunk)
        after = path.stat(follow_symlinks=False)
    except OSError:
        return False
    stable = (before.st_dev, before.st_ino, before.st_size, before.st_mtime_ns) == (
        after.st_dev, after.st_ino, after.st_size, after.st_mtime_ns
    )
    return stable and size == expected_size and "sha256:" + digest.hexdigest() == expected_hash


def _documented_fact_is_located(authority: DirectAuthority, use: object) -> bool:
    haystack = str(getattr(use, "exact_locator", "")).casefold()
    unit = re.escape(_token(authority.documented_unit).casefold())
    value = authority.documented_value
    if _token(value.kind) == NumericValueKind.SCALAR.value and _decimal(value.scalar) is not None:
        numeric = re.escape(str(value.scalar))
        located = re.search(rf"(?<![0-9.]){numeric}\s*{unit}(?![a-z0-9])", haystack) is not None
    elif (_token(value.kind) == NumericValueKind.INTERVAL.value
          and _decimal(value.lower) is not None and _decimal(value.upper) is not None):
        low, high = re.escape(str(value.lower)), re.escape(str(value.upper))
        located = re.search(
            rf"(?<![0-9.]){low}\s*[-–—]\s*{high}\s*{unit}(?![a-z0-9])", haystack
        ) is not None
    else:
        return False
    terms = QUANTITY_LOCATOR_TERMS.get(_token(authority.documented_quantity_kind), ())
    return located and (not terms or any(term in haystack for term in terms))


def _valid_uncertainty(value: UncertaintyRecord) -> bool:
    if not _enum(value.kind, UncertaintyKind):
        return False
    if _token(value.kind) == UncertaintyKind.NOT_APPLICABLE.value:
        return (
            _nonblank(value.rationale) and value.estimate is None and value.unit is None
            and value.method is None and not value.component_ids and value.coverage is None
            and value.evidence_reference is None
        )
    return (
        _decimal(value.estimate) is not None and _enum(value.unit, Unit)
        and _nonblank(value.method) and bool(value.component_ids)
        and _nonblank(value.evidence_reference) and value.rationale is None
    )


def _validate_numeric_value(record: ParameterRevision, violations: list[ParameterViolation]) -> None:
    value = record.value
    if not _enum(value.kind, NumericValueKind):
        violations.append(_violation("PAR-TOKEN-INVALID", record.parameter_revision_id,
                                     "value.kind", value.kind, "Unknown numeric-value kind."))
        return
    kind = _token(value.kind)
    if kind == NumericValueKind.SCALAR.value:
        valid = _decimal(value.scalar) is not None and all(item is None for item in (
            value.lower, value.upper, value.lower_inclusive, value.upper_inclusive, value.unresolved_reason
        ))
    elif kind == NumericValueKind.INTERVAL.value:
        lower, upper = _decimal(value.lower), _decimal(value.upper)
        valid = (
            lower is not None and upper is not None and lower < upper
            and type(value.lower_inclusive) is bool and type(value.upper_inclusive) is bool
            and value.scalar is None and value.unresolved_reason is None
        )
    elif kind == NumericValueKind.OBSERVATION_TRANSFORM.value:
        valid = (
            _token(record.parameter_class) == ParameterClass.DERIVED.value
            and all(item is None for item in (
                value.scalar, value.lower, value.upper, value.lower_inclusive,
                value.upper_inclusive, value.unresolved_reason,
            ))
        )
    else:
        valid = (
            record.record_state in {RecordState.BLOCKED, RecordState.UNRESOLVED, "blocked", "unresolved"}
            and _nonblank(value.unresolved_reason)
            and all(item is None for item in (
                value.scalar, value.lower, value.upper, value.lower_inclusive, value.upper_inclusive
            ))
        )
    if not valid:
        violations.append(_violation("PAR-DECIMAL-INVALID", record.parameter_revision_id,
                                     "value", value.to_dict(),
                                     "Use canonical decimal strings or an explicitly blocked unresolved value."))


def _scalar(record: ParameterRevision | None) -> Decimal | None:
    if record is None or _token(record.value.kind) != NumericValueKind.SCALAR.value:
        return None
    return _decimal(record.value.scalar)


def _validate_uncertainty(record: ParameterRevision, violations: list[ParameterViolation]) -> None:
    uncertainty = record.uncertainty
    if not _enum(uncertainty.kind, UncertaintyKind):
        violations.append(_violation("PAR-TOKEN-INVALID", record.parameter_revision_id,
                                     "uncertainty.kind", uncertainty.kind, "Unknown uncertainty kind."))
        return
    valid = _valid_uncertainty(uncertainty)
    if valid and _token(uncertainty.kind) != UncertaintyKind.NOT_APPLICABLE.value:
        valid = _token(uncertainty.unit) == _token(record.unit)
    if not valid:
        violations.append(_violation("PAR-UNCERTAINTY-INVALID", record.parameter_revision_id,
                                     "uncertainty", uncertainty.kind,
                                     "Uncertainty/dispersion requires typed evidence or a scoped not-applicable rationale."))


def _validate_derivation(
    record: ParameterRevision,
    spec: DerivationSpec | None,
    records: Mapping[str, ParameterRevision],
    violations: list[ParameterViolation],
) -> None:
    if spec is None:
        violations.append(_violation("PAR-REFERENCE-UNRESOLVED", record.parameter_revision_id,
                                     "derived_authority.derivation_id", "missing",
                                     "Derived authority must resolve an immutable derivation."))
        return
    if spec.operation != AFFINE_OPERATION or spec.decimal_precision != 50 or spec.rounding != "ROUND_HALF_EVEN":
        violations.append(_violation("PAR-DERIVATION-INVALID", spec.derivation_id, "operation",
                                     spec.operation, "Only affine_map.v1 with the pinned decimal policy is allowed."))
        return
    refs = [spec.input_low_revision_id, spec.input_high_revision_id,
            spec.output_low_revision_id, spec.output_high_revision_id]
    if spec.selected_input_revision_id is not None:
        refs.append(spec.selected_input_revision_id)
    if len(set(refs)) != len(refs) or any(item not in records for item in refs):
        violations.append(_violation("PAR-DERIVATION-INVALID", spec.derivation_id, "inputs", refs,
                                     "Every affine operand must be a distinct exact parameter revision."))
        return
    x0, x1, y0, y1 = (_scalar(records[item]) for item in refs[:4])
    if None in (x0, x1, y0, y1) or x0 == x1:
        violations.append(_violation("PAR-DERIVATION-INVALID", spec.derivation_id, "inputs", refs,
                                     "Affine endpoints must be scalar and the input span nonzero."))
        return
    if records[refs[0]].unit != records[refs[1]].unit or records[refs[2]].unit != records[refs[3]].unit:
        violations.append(_violation("PAR-UNIT-INVALID", spec.derivation_id, "inputs.unit", refs,
                                     "Affine endpoint units must agree on each axis."))
        return
    if (
        _token(records[refs[0]].quantity_kind) != _token(records[refs[1]].quantity_kind)
        or _token(records[refs[2]].quantity_kind) != _token(records[refs[3]].quantity_kind)
        or (
            spec.selected_input_revision_id is not None
            and _token(records[spec.selected_input_revision_id].quantity_kind)
            != _token(records[refs[0]].quantity_kind)
        )
    ):
        violations.append(_violation("PAR-UNIT-INVALID", spec.derivation_id, "inputs.quantity_kind", refs,
                                     "Affine endpoint and selected-input quantity kinds must agree by axis."))
        return
    if (
        spec.selected_input_revision_id is not None
        and _token(records[spec.selected_input_revision_id].unit) != _token(records[refs[0]].unit)
    ) or (
        _token(spec.derivation_kind) == DerivationKind.OBSERVATION_TRANSFORM.value
        and _token(spec.observation_unit) != _token(records[refs[0]].unit)
    ):
        violations.append(_violation("PAR-UNIT-INVALID", spec.derivation_id, "observation_unit",
                                     spec.observation_unit,
                                     "Selected or observed input unit must match the affine input axis."))
        return
    if _token(records[refs[2]].unit) != _token(spec.output_unit) or _token(record.unit) != _token(spec.output_unit):
        violations.append(_violation("PAR-UNIT-INVALID", spec.derivation_id, "output_unit", spec.output_unit,
                                     "Derivation, endpoint, and parameter output units must agree."))
        return
    if (
        _token(records[refs[2]].quantity_kind) != _token(records[refs[3]].quantity_kind)
        or _token(record.quantity_kind) != _token(records[refs[2]].quantity_kind)
    ):
        violations.append(_violation(
            "PAR-UNIT-INVALID", spec.derivation_id, "output_quantity_kind",
            record.quantity_kind, "Derivation and output endpoints must retain one quantity kind.",
        ))
        return
    context = Context(prec=50, rounding=ROUND_HALF_EVEN)
    for signal in (FloatOperation, InvalidOperation, DivisionByZero, Overflow, Underflow, Inexact, Rounded):
        context.traps[signal] = True

    def apply(value: Decimal) -> Decimal:
        with localcontext(context):
            return y0 + (y1 - y0) * (value - x0) / (x1 - x0)  # type: ignore[operator]

    try:
        if _token(spec.derivation_kind) == DerivationKind.CONSTANT_RESULT.value:
            selected = _scalar(records.get(spec.selected_input_revision_id or ""))
            expected = _decimal(spec.declared_output)
            valid = selected is not None and expected is not None and apply(selected) == expected == _scalar(record)
        elif _token(spec.derivation_kind) == DerivationKind.OBSERVATION_TRANSFORM.value:
            with localcontext(context):
                midpoint = (x0 + x1) / Decimal("2")  # type: ignore[operator]
            vector_inputs = tuple(_decimal(item.input_value) for item in spec.conformance_vectors)
            valid = (
                spec.selected_input_revision_id is None and _nonblank(spec.observation_variable)
                and _enum(spec.observation_unit, Unit) and len(spec.conformance_vectors) == 3
                and None not in vector_inputs and len(set(vector_inputs)) == 3
                and set(vector_inputs) == {x0, midpoint, x1}
                and all(_decimal(item.input_value) is not None and _decimal(item.expected_output) is not None
                        and apply(_decimal(item.input_value)) == _decimal(item.expected_output)  # type: ignore[arg-type]
                        for item in spec.conformance_vectors)
            )
        else:
            valid = False
    except (ArithmeticError, TypeError):
        valid = False
    if not valid:
        violations.append(_violation("PAR-DERIVATION-INVALID", spec.derivation_id, "reproduced_output",
                                     spec.declared_output, "Affine reproduction/conformance must match exactly without rounding."))


def _gate_result(
    catalog: ParameterEvidenceCatalog,
    source_catalog: SourceCatalog,
    inventory: NumericConsumerInventory,
    required_set: RequiredParameterSet,
    violations: list[ParameterViolation],
    temporal_context: TemporalGateContext | None,
) -> ParameterGateResult:
    ordered = tuple(sorted(violations, key=lambda item: (
        item.rule_id, item.record_id, item.field_path, item.offending_reference
    )))
    outcome = AccountabilityOutcome.BLOCKED if ordered else AccountabilityOutcome.ACCOUNTABLE
    limitations = ("Numerical accountability only; no scientific activity is authorized.",)
    identity_payload = {
        "catalog_identity": parameter_catalog_identity(catalog),
        "source_catalog_identity": source_catalog_identity(source_catalog),
        "vocabulary_version": catalog.semantic_vocabulary_version,
        "inventory_id": inventory.inventory_id,
        "required_set_id": required_set.required_set_id,
        "temporal_context_id": temporal_context.context_id if temporal_context else None,
        "decision_ids": sorted(item.decision_id for item in catalog.decisions),
        "measurement_evidence_ids": sorted(
            item.measurement_evidence_id for item in catalog.measurements
        ),
        "mock_admission_ids": sorted(item.mock_admission_id for item in catalog.mock_admissions),
        "validator_identity": VALIDATOR_IDENTITY,
        "accountability_outcome": outcome.value,
        "violations": [{
            "rule_id": item.rule_id, "record_id": item.record_id,
            "field_path": item.field_path, "offending_reference": item.offending_reference,
        } for item in ordered],
        "limitations": list(limitations),
        "authorization_effect": "none",
    }
    encoded = json.dumps(identity_payload, sort_keys=True, ensure_ascii=False,
                         separators=(",", ":"), allow_nan=False).encode("utf-8")
    return ParameterGateResult(
        gate_result_id="sha256:" + hashlib.sha256(encoded).hexdigest(),
        catalog_identity=identity_payload["catalog_identity"],
        source_catalog_identity=identity_payload["source_catalog_identity"],
        vocabulary_version=catalog.semantic_vocabulary_version,
        inventory_id=inventory.inventory_id,
        required_set_id=required_set.required_set_id,
        temporal_context_id=identity_payload["temporal_context_id"],
        decision_ids=tuple(identity_payload["decision_ids"]),
        measurement_evidence_ids=tuple(identity_payload["measurement_evidence_ids"]),
        mock_admission_ids=tuple(identity_payload["mock_admission_ids"]),
        validator_identity=VALIDATOR_IDENTITY,
        accountability_outcome=outcome,
        violations=ordered,
        limitations=limitations,
    )


def validate_parameter_gate(
    catalog: ParameterEvidenceCatalog,
    source_catalog: SourceCatalog,
    inventory: NumericConsumerInventory,
    required_set: RequiredParameterSet,
    *,
    evidence_root: Path | None = None,
    path_resolver: Callable[[Path], Path] | None = None,
    temporal_context: TemporalGateContext | None = None,
) -> ParameterGateResult:
    """Validate numerical accountability without selecting values or authorizing activity."""

    violations: list[ParameterViolation] = []
    if catalog.schema_version != PARAMETER_EVIDENCE_SCHEMA_VERSION or (
        catalog.semantic_vocabulary_version != SEMANTIC_VOCABULARY_VERSION
    ):
        violations.append(_violation("PAR-SCHEMA-UNSUPPORTED", "catalog", "schema_version",
                                     catalog.schema_version, "Unsupported parameter/vocabulary schema."))

    expected_source = source_catalog_identity(source_catalog)
    if catalog.source_catalog_identity != expected_source:
        violations.append(_violation(
            "PAR-BINDING-INVALID", "catalog", "source_catalog_identity",
            catalog.source_catalog_identity, "Catalog must bind the exact source-catalog identity.",
        ))
    source_validation = validate_source_catalog(source_catalog)
    for source_violation in source_validation.violations:
        violations.append(_violation(
            "PAR-SOURCE-CATALOG-INVALID", source_violation.record_id,
            ",".join(source_violation.fields), ",".join(source_violation.offending_tokens),
            "The bound Story 9.3 source catalog must be structurally qualified.",
        ))

    groups = (
        (catalog.parameter_revisions, "parameter_revision_id"),
        (catalog.derivations, "derivation_id"), (catalog.decisions, "decision_id"),
        (catalog.mock_admissions, "mock_admission_id"),
        (catalog.measurements, "measurement_evidence_id"),
        (catalog.inventories, "inventory_id"), (catalog.required_sets, "required_set_id"),
        (catalog.locus_audits, "audit_id"), (catalog.legacy_quarantine, "quarantine_id"),
    )
    for records_group, id_field in groups:
        seen: set[str] = set()
        for item in records_group:
            identifier = str(getattr(item, id_field))
            if identifier in seen:
                violations.append(_violation("PAR-ID-DUPLICATE", identifier, id_field, identifier,
                                             "Immutable IDs must be unique."))
            seen.add(identifier)
            if not _nonblank(identifier) or identifier.casefold() in {"latest", "current"} or (
                identifier.casefold().endswith(":latest")
                or identifier.casefold().endswith(":current")
            ):
                violations.append(_violation(
                    "PAR-ID-MUTABLE", identifier, id_field, identifier,
                    "Mutable aliases cannot identify numerical evidence.",
                ))

    records = {item.parameter_revision_id: item for item in catalog.parameter_revisions}
    derivations = {item.derivation_id: item for item in catalog.derivations}
    decisions = {item.decision_id: item for item in catalog.decisions}
    measurements = {item.measurement_evidence_id: item for item in catalog.measurements}
    mocks = {item.mock_admission_id: item for item in catalog.mock_admissions}
    source_uses = {item.use_id: item for item in source_catalog.uses}
    source_revisions = {item.source_revision_id: item for item in source_catalog.revisions}
    sources = {item.source_id: item for item in source_catalog.sources}

    for record in catalog.parameter_revisions:
        if record.revision_sha256 != parameter_revision_identity(record):
            violations.append(_violation(
                "PAR-REVISION-HASH-MISMATCH", record.parameter_revision_id,
                "revision_sha256", record.revision_sha256,
                "Parameter revision content must match its immutable digest.",
            ))
        for name, value, enum_type in (
            ("parameter_class", record.parameter_class, ParameterClass),
            ("value_role", record.value_role, ValueRole), ("unit", record.unit, Unit),
            ("quantity_kind", record.quantity_kind, QuantityKind),
            ("record_state", record.record_state, RecordState),
            ("approval_state", record.approval_state, ApprovalState),
            ("authentic_reproduction_feasibility", record.authentic_reproduction_feasibility,
             AuthenticFeasibility),
            ("synthetic_status", record.synthetic_status, SyntheticStatus),
        ):
            if not _enum(value, enum_type):
                violations.append(_violation("PAR-TOKEN-INVALID", record.parameter_revision_id,
                                             name, value, "Closed ParameterEvidence.v1 token required."))
        required_text = (
            "parameter_id", "parameter_revision_id", "profile_id", "experiment_scope",
            "prototype_component", "consumer_locator", "research_question", "evidence_track",
            "final_package_element", "transferability_rationale", "owner",
        )
        for name in required_text:
            if not _nonblank(getattr(record, name)):
                violations.append(_violation("PAR-METADATA-INCOMPLETE", record.parameter_revision_id,
                                             name, getattr(record, name), "Required bounded metadata is missing."))
        if not record.limitations:
            violations.append(_violation("PAR-METADATA-INCOMPLETE", record.parameter_revision_id,
                                         "limitations", "", "Mandatory limitations cannot be empty."))
        _validate_numeric_value(record, violations)
        _validate_uncertainty(record, violations)
        allowed_units = UNIT_BY_QUANTITY.get(_token(record.quantity_kind))
        if allowed_units is not None and _token(record.unit) not in allowed_units:
            violations.append(_violation("PAR-UNIT-INVALID", record.parameter_revision_id,
                                         "unit", record.unit,
                                         "Unit is incompatible with the declared semantic quantity kind."))
        authorities = [
            record.direct_authority, record.derived_authority, record.measured_authority,
            record.decision_authority, record.mock_authority,
        ]
        branch_by_class = {
            ParameterClass.DIRECT.value: record.direct_authority,
            ParameterClass.DERIVED.value: record.derived_authority,
            ParameterClass.MEASURED.value: record.measured_authority,
            ParameterClass.PREREGISTERED_FACTOR.value: record.decision_authority,
            ParameterClass.MOCK.value: record.mock_authority,
        }
        if sum(item is not None for item in authorities) != 1 or branch_by_class.get(
            _token(record.parameter_class)
        ) is None:
            violations.append(_violation("PAR-AUTHORITY-MISMATCH", record.parameter_revision_id,
                                         "authority", record.parameter_class,
                                         "Exactly one authority branch must match the parameter class."))
            continue

        if record.direct_authority:
            authority = record.direct_authority
            use = source_uses.get(authority.source_use_id)
            revision = source_revisions.get(authority.source_revision_id)
            source = sources.get(revision.source_id) if revision else None
            eligible = (
                use is not None and revision is not None and source is not None
                and use.source_revision_id == authority.source_revision_id
                and use.source_id == revision.source_id
                and not revision.mutable_location and _nonblank(revision.immutable_locator)
                and _token(use.status) == SourceUseStatus.LOCATED.value
                and _token(use.claim_use) == ClaimUse.DIRECT_VALUE.value
                and _nonblank(use.exact_locator) and _nonblank(use.applicable_variant)
                and use.responsible_authority
                and _token(source.source_type) in {
                    SourceType.VENDOR_MANUAL.value, SourceType.STANDARD.value,
                    SourceType.OFFICIAL_SPECIFICATION.value, SourceType.DATASET_RELEASE.value,
                    SourceType.DATASET_MANUAL.value,
                }
                and _token(source.authority_role) in {
                    AuthorityRole.RESPONSIBLE_OFFICIAL.value,
                    AuthorityRole.AUTHORITATIVE_FOR_SCOPE.value,
                }
                and use.prototype_component == record.prototype_component
                and use.research_question == record.research_question
                and use.evidence_track == record.evidence_track
                and use.final_package_element == record.final_package_element
                and use.transferability_rationale == record.transferability_rationale
                and authority.documented_value.to_dict() == record.value.to_dict()
                and _token(authority.documented_unit) == _token(record.unit)
                and _token(authority.documented_quantity_kind) == _token(record.quantity_kind)
                and _documented_fact_is_located(authority, use)
            )
            if not eligible:
                violations.append(_violation("PAR-SOURCE-INELIGIBLE", record.parameter_revision_id,
                                             "direct_authority", authority.source_use_id,
                                             "Direct authority must resolve the exact responsible bounded source use."))

        elif record.derived_authority:
            derivation = derivations.get(record.derived_authority.derivation_id)
            _validate_derivation(record, derivation, records, violations)
            if derivation is not None:
                lineage_inputs = tuple(records.get(item) for item in (
                    derivation.input_low_revision_id, derivation.input_high_revision_id,
                    derivation.output_low_revision_id, derivation.output_high_revision_id,
                    derivation.selected_input_revision_id,
                ) if item is not None)
                if any(item is not None and _token(item.synthetic_status) in {
                    SyntheticStatus.MOCK.value, SyntheticStatus.MOCK_DERIVED.value,
                } for item in lineage_inputs) and (
                    _token(record.synthetic_status) != SyntheticStatus.MOCK_DERIVED.value
                ):
                    violations.append(_violation(
                        "PAR-LINEAGE-PROMOTION", record.parameter_revision_id,
                        "synthetic_status", record.synthetic_status,
                        "A derivation depending on mock lineage must remain mock_derived.",
                    ))

        elif record.measured_authority:
            measurement = measurements.get(record.measured_authority.measurement_evidence_id)
            valid = (
                measurement is not None and _scalar(record) == _decimal(measurement.result)
                and _token(record.unit) == _token(measurement.unit)
                and record.profile_id == measurement.profile_id
                and record.experiment_scope == measurement.experiment_scope
                and _nonblank(measurement.method_identity) and _nonblank(measurement.environment_identity)
                and bool(measurement.sample_ids) and bool(measurement.run_ids)
                and _instant(measurement.measured_at) is not None
                and DIGEST_PATTERN.fullmatch(measurement.sha256) is not None
                and measurement.byte_size >= 0 and _valid_uncertainty(measurement.uncertainty)
                and measurement.uncertainty.to_dict() == record.uncertainty.to_dict()
                and (
                    _token(measurement.uncertainty.kind) == UncertaintyKind.NOT_APPLICABLE.value
                    or _token(measurement.uncertainty.unit) == _token(measurement.unit)
                )
                and _token(measurement.approval_state) in {
                    ApprovalState.APPROVED.value, ApprovalState.PLANNING_FROZEN.value,
                }
                and bool(measurement.limitations) and measurement.owner == record.owner
            )
            if valid and evidence_root is not None:
                path = _safe_path(evidence_root, measurement.locator, path_resolver)
                valid = path is not None and _verify_bytes(path, measurement.byte_size, measurement.sha256)
            elif valid:
                valid = False
            if not valid:
                violations.append(_violation("PAR-MEASUREMENT-INVALID", record.parameter_revision_id,
                                             "measured_authority", record.measured_authority.measurement_evidence_id,
                                             "Measured authority requires matching preserved opaque evidence in scope."))

        elif record.decision_authority:
            decision = decisions.get(record.decision_authority.decision_id)
            selected_decision = next((item for item in decision.parameter_values
                                      if item.parameter_id == record.parameter_id), None) if decision else None
            ordered = False
            if decision and temporal_context:
                freeze = _instant(decision.freeze_time)
                test = _instant(temporal_context.test_time)
                truth = _instant(temporal_context.truth_time)
                ordered = bool(
                    freeze and test and truth and freeze < test < truth
                    and temporal_context.freeze_time == decision.freeze_time
                    and _nonblank(temporal_context.context_id)
                    and temporal_context.freeze_identity == decision.record_sha256
                    and DIGEST_PATTERN.fullmatch(temporal_context.test_identity) is not None
                    and DIGEST_PATTERN.fullmatch(temporal_context.truth_identity) is not None
                )
            valid = (
                decision is not None and DIGEST_PATTERN.fullmatch(decision.content_sha256) is not None
                and decision.record_sha256 == decision_record_identity(decision)
                and not decision.mutable and _nonblank(decision.owner) and _nonblank(decision.approved_by)
                and _instant(decision.approved_at) is not None
                and _instant(decision.freeze_time) is not None
                and _instant(decision.approved_at) <= _instant(decision.freeze_time)
                and _nonblank(decision.rationale) and bool(decision.limitations)
                and bool(decision.prohibited_interpretations) and bool(decision.source_use_ids)
                and decision.test_locked and decision.truth_locked
                and record.parameter_id in decision.parameter_ids
                and len(decision.parameter_ids) == len(set(decision.parameter_ids))
                and len(decision.parameter_values) == len(decision.parameter_ids)
                and {item.parameter_id for item in decision.parameter_values} == set(decision.parameter_ids)
                and selected_decision is not None
                and selected_decision.value.to_dict() == record.value.to_dict()
                and _token(selected_decision.unit) == _token(record.unit)
                and _token(selected_decision.quantity_kind) == _token(record.quantity_kind)
                and _token(selected_decision.value_role) == _token(record.value_role)
                and record.profile_id == decision.profile_id
                and record.experiment_scope == decision.experiment_scope
                and record.prototype_component == decision.component
                and record.research_question == decision.question
                and record.evidence_track == decision.evidence_track
                and record.final_package_element == decision.final_output
                and ordered
            )
            if valid:
                cited = [source_uses.get(item) for item in decision.source_use_ids]
                valid = all(
                    item is not None and item.source_revision_id in source_revisions
                    and _token(item.status) in {
                        SourceUseStatus.LOCATED.value, SourceUseStatus.CONTEXTUAL_ONLY.value,
                    }
                    and _nonblank(item.exact_locator)
                    and _token(item.claim_use) in {
                        ClaimUse.CAPABILITY.value, ClaimUse.CONSTRAINT.value,
                        ClaimUse.CONTEXTUAL_ONLY.value, ClaimUse.DERIVATION_METHOD.value,
                    } for item in cited
                )
            if _scalar(record) in {Decimal("25"), Decimal("75")} and _token(record.quantity_kind) not in {
                QuantityKind.SPEED_REFERENCE.value, QuantityKind.CAPACITY_REFERENCE.value,
            }:
                valid = False
            if not valid:
                violations.append(_violation("PAR-DECISION-INVALID", record.parameter_revision_id,
                                             "decision_authority", record.decision_authority.decision_id,
                                             "Research factors require an immutable pre-test/pre-truth decision proof."))

        elif record.mock_authority:
            authority = record.mock_authority
            admission = mocks.get(authority.mock_admission_id)
            claim = next((item for item in admission.support_claims
                          if item.mock_claim_id == authority.mock_claim_id), None) if admission else None
            parameter_bindings = {
                item.parameter_revision_id: item for item in admission.parameter_revision_bindings
            } if admission else {}
            all_claims_valid = bool(admission and admission.support_claims)
            claim_ids: set[str] = set()
            if admission:
                for support_claim in admission.support_claims:
                    resolved_uses = [source_uses.get(item) for item in support_claim.source_use_ids]
                    claim_valid = (
                        support_claim.mock_claim_id not in claim_ids
                        and _nonblank(support_claim.behavior) and _nonblank(support_claim.scope)
                        and bool(support_claim.source_use_ids)
                        and all(
                            item is not None and item.source_revision_id in source_revisions
                            and _token(item.status) == SourceUseStatus.LOCATED.value
                            and _nonblank(item.exact_locator)
                            and _token(item.claim_use) in {
                                ClaimUse.DIRECT_VALUE.value, ClaimUse.CAPABILITY.value,
                                ClaimUse.CONSTRAINT.value, ClaimUse.DERIVATION_METHOD.value,
                                ClaimUse.PROTOCOL_RULE.value,
                            }
                            for item in resolved_uses
                        )
                    )
                    if support_claim.expected_value is not None:
                        claim_valid = claim_valid and _decimal(support_claim.expected_value) is not None
                        claim_valid = claim_valid and support_claim.unit is not None
                        claim_valid = claim_valid and support_claim.quantity_kind is not None
                    claim_ids.add(support_claim.mock_claim_id)
                    all_claims_valid = all_claims_valid and claim_valid
            bound_revisions_valid = bool(parameter_bindings) and admission is not None
            if admission:
                bound_revisions_valid = bound_revisions_valid and (
                    len(parameter_bindings) == len(admission.parameter_revision_bindings)
                    and all(
                        item.parameter_revision_id in records
                        and item.revision_sha256 == records[item.parameter_revision_id].revision_sha256
                        and DIGEST_PATTERN.fullmatch(item.revision_sha256) is not None
                        for item in admission.parameter_revision_bindings
                    )
                )
            randomness_valid = False
            if admission and _token(admission.randomness_mode) == RandomnessMode.DETERMINISTIC.value:
                randomness_valid = (
                    admission.seed_closure_id == "not_applicable"
                    and admission.seed_parameter_revision_id is None
                    and admission.seed_parameter_revision_sha256 is None
                )
            elif admission and _token(admission.randomness_mode) == RandomnessMode.SEEDED.value:
                seed = records.get(admission.seed_parameter_revision_id or "")
                randomness_valid = (
                    DIGEST_PATTERN.fullmatch(admission.seed_closure_id) is not None
                    and seed is not None
                    and admission.seed_parameter_revision_sha256 == seed.revision_sha256
                    and DIGEST_PATTERN.fullmatch(admission.seed_parameter_revision_sha256 or "") is not None
                )
            valid = (
                admission is not None and claim is not None and not admission.mutable
                and DIGEST_PATTERN.fullmatch(admission.content_sha256) is not None
                and admission.record_sha256 == mock_admission_identity(admission)
                and admission.owner == admission.approved_by
                and _instant(admission.approved_at) is not None
                and _token(admission.authentic_feasibility) == AuthenticFeasibility.UNAVAILABLE_WITH_EVIDENCE.value
                and _token(admission.reproduction_disposition)
                == ReproductionDisposition.STILL_UNAVAILABLE_WITH_EVIDENCE.value
                and DIGEST_PATTERN.fullmatch(admission.reproduction_assessment_identity) is not None
                and _token(record.authentic_reproduction_feasibility)
                == AuthenticFeasibility.UNAVAILABLE_WITH_EVIDENCE.value
                and _token(record.synthetic_status) == SyntheticStatus.MOCK.value
                and all(_nonblank(item) for item in (
                    admission.authentic_path_assessment, admission.exact_entrypoint,
                    admission.prototype_component_id, admission.interface_schema_version,
                    admission.permitted_output_role, admission.permitted_output_record_family,
                    admission.semantic_provenance, admission.simulator_profile,
                    admission.purpose, admission.replacement_condition,
                ))
                and all(DIGEST_PATTERN.fullmatch(item) is not None for item in (
                    admission.code_identity, admission.runtime_identity,
                    admission.configuration_identity, admission.parameter_closure_id,
                    admission.emission_trace_identity,
                ))
                and admission.prototype_component_id == record.prototype_component
                and admission.component == record.prototype_component
                and admission.question == record.research_question
                and admission.evidence_track == record.evidence_track
                and admission.final_output == record.final_package_element
                and admission.semantic_provenance == "mock_parameterized"
                and {"measured", "authentic_capture", "official_native", "official_real"}.issubset(
                    set(admission.prohibited_output_roles)
                )
                and bool(admission.prohibited_claims) and bool(admission.limitations)
                and all_claims_valid and bound_revisions_valid and randomness_valid
                and claim.scope == record.experiment_scope
                and (claim.expected_value is None or _decimal(claim.expected_value) == _scalar(record))
                and (claim.unit is None or _token(claim.unit) == _token(record.unit))
                and (claim.quantity_kind is None
                     or _token(claim.quantity_kind) == _token(record.quantity_kind))
            )
            if not valid:
                violations.append(_violation("PAR-MOCK-INELIGIBLE", record.parameter_revision_id,
                                             "mock_authority", authority.mock_admission_id,
                                             "Mock authority requires proven unavailability and complete immutable support closure."))

    # Detect derived cycles independently of evaluation order.
    dependency_graph: dict[str, set[str]] = {}
    for record in catalog.parameter_revisions:
        if record.derived_authority and record.derived_authority.derivation_id in derivations:
            spec = derivations[record.derived_authority.derivation_id]
            dependency_graph[record.parameter_revision_id] = {
                item for item in (
                    spec.input_low_revision_id, spec.input_high_revision_id,
                    spec.output_low_revision_id, spec.output_high_revision_id,
                    spec.selected_input_revision_id,
                ) if item is not None and records.get(item) and records[item].derived_authority
            }
    visiting: set[str] = set()
    visited: set[str] = set()

    def visit(node: str) -> bool:
        if node in visiting:
            return True
        if node in visited:
            return False
        visiting.add(node)
        cyclic = any(visit(child) for child in sorted(dependency_graph.get(node, ())))
        visiting.remove(node)
        visited.add(node)
        return cyclic

    for node in sorted(dependency_graph):
        if visit(node):
            violations.append(_violation("PAR-DERIVATION-INVALID", node, "inputs", node,
                                         "Derived parameter dependencies must be acyclic."))

    active_slots: dict[tuple[str, str, str, str, str], list[ParameterRevision]] = {}
    for record in catalog.parameter_revisions:
        if _token(record.record_state) == RecordState.VALID.value and _token(record.approval_state) in {
            ApprovalState.APPROVED.value, ApprovalState.PLANNING_FROZEN.value,
        }:
            key = (record.parameter_id, record.experiment_scope, record.profile_id,
                   record.consumer_locator, _token(record.value_role))
            active_slots.setdefault(key, []).append(record)
    for slot, active in sorted(active_slots.items()):
        if len(active) > 1 and len({json.dumps(item.to_dict(), sort_keys=True) for item in active}) > 1:
            for record in active:
                violations.append(_violation(
                    "PAR-ACTIVE-CONFLICT", record.parameter_revision_id, "selection_slot", slot,
                    "Conflicting active revisions cannot share one logical consumer slot.",
                ))

    catalog_inventory = next((item for item in catalog.inventories
                              if item.inventory_id == inventory.inventory_id), None)
    if catalog_inventory is None:
        violations.append(_violation("PAR-REFERENCE-UNRESOLVED", inventory.inventory_id,
                                     "inventory_id", inventory.inventory_id,
                                     "Gate inventory must be part of the catalog authority."))
    elif catalog_inventory.to_dict() != inventory.to_dict():
        violations.append(_violation(
            "PAR-SELECTION-MISMATCH", inventory.inventory_id, "inventory",
            inventory.inventory_id, "Gate inventory must exactly match the catalog record.",
        ))
    catalog_required = next((item for item in catalog.required_sets
                             if item.required_set_id == required_set.required_set_id), None)
    if catalog_required is None:
        violations.append(_violation("PAR-REFERENCE-UNRESOLVED", required_set.required_set_id,
                                     "required_set_id", required_set.required_set_id,
                                     "Required set must be part of the catalog authority."))
    elif catalog_required.to_dict() != required_set.to_dict():
        violations.append(_violation(
            "PAR-SELECTION-MISMATCH", required_set.required_set_id, "required_set",
            required_set.required_set_id, "Gate required set must exactly match the catalog record.",
        ))
    expected_catalog = parameter_catalog_identity(catalog)
    if required_set.catalog_identity != expected_catalog or required_set.source_catalog_identity != expected_source:
        violations.append(_violation("PAR-BINDING-INVALID", required_set.required_set_id,
                                     "catalog_identity", required_set.catalog_identity,
                                     "Required set must bind the exact parameter and source catalogs."))
    if (
        required_set.inventory_id != inventory.inventory_id
        or required_set.vocabulary_version != catalog.semantic_vocabulary_version
        or required_set.scope != inventory.scope or required_set.profile_id != inventory.profile_id
        or required_set.component_identity != inventory.component_identity
    ):
        violations.append(_violation("PAR-SCOPE-MISMATCH", required_set.required_set_id,
                                     "inventory_scope", inventory.inventory_id,
                                     "Required set and independent inventory identities/scope must agree."))

    requirements = {item.slot_id: item for item in inventory.requirements}
    bindings = {item.slot_id: item for item in required_set.bindings}
    if len(bindings) != len(required_set.bindings) or set(bindings) != set(requirements):
        violations.append(_violation("PAR-INVENTORY-INCOMPLETE", required_set.required_set_id,
                                     "bindings", sorted(set(requirements) - set(bindings)),
                                     "Every independent inventory slot requires exactly one binding and no extras."))
    dispositions = {str(item.category): item for item in inventory.category_dispositions}
    if (len(dispositions) != len(inventory.category_dispositions)
            or set(dispositions) != {item.value for item in InventoryCategory}):
        violations.append(_violation("PAR-INVENTORY-INCOMPLETE", inventory.inventory_id,
                                     "category_dispositions", "missing",
                                     "Every v1 completeness category requires a disposition."))
    for disposition in inventory.category_dispositions:
        if (
            not _enum(disposition.category, InventoryCategory)
            or not _enum(disposition.state, CategoryState)
            or not _nonblank(disposition.rationale)
            or not disposition.owner_approved
        ):
            violations.append(_violation(
                "PAR-INVENTORY-INCOMPLETE", inventory.inventory_id,
                f"category_dispositions.{_token(disposition.category)}",
                disposition.state, "Every category disposition must be closed, reasoned, and owner-approved.",
            ))
    for requirement in inventory.requirements:
        disposition = dispositions.get(_token(requirement.category))
        if disposition is None or _token(disposition.state) != CategoryState.REQUIRED.value:
            violations.append(_violation("PAR-INVENTORY-INCOMPLETE", requirement.slot_id,
                                         "category", requirement.category,
                                         "A category containing slots cannot be not-applicable."))
        binding = bindings.get(requirement.slot_id)
        if binding is None:
            continue
        if binding.not_applicable:
            if (not requirement.not_applicable_allowed or binding.parameter_revision_id is not None
                    or not _nonblank(binding.rationale)):
                violations.append(_violation("PAR-BINDING-INVALID", requirement.slot_id,
                                             "not_applicable", binding.not_applicable,
                                             "This required slot cannot be declared not applicable."))
            continue
        selected = records.get(binding.parameter_revision_id or "")
        if selected is None:
            violations.append(_violation("PAR-REFERENCE-UNRESOLVED", requirement.slot_id,
                                         "parameter_revision_id", binding.parameter_revision_id,
                                         "Binding must select one exact immutable parameter revision."))
            continue
        if (
            binding.parameter_revision_sha256 != selected.revision_sha256
            or DIGEST_PATTERN.fullmatch(binding.parameter_revision_sha256 or "") is None
        ):
            violations.append(_violation(
                "PAR-BINDING-INVALID", requirement.slot_id, "parameter_revision_sha256",
                binding.parameter_revision_sha256,
                "Binding must name the exact immutable parameter-revision digest.",
            ))
        if selected.record_state != RecordState.VALID or selected.approval_state not in {
            ApprovalState.APPROVED, ApprovalState.PLANNING_FROZEN
        }:
            violations.append(_violation("PAR-BINDING-INVALID", requirement.slot_id,
                                         "parameter_revision_id", selected.parameter_revision_id,
                                         "Blocked, unresolved, conditional, candidate, or legacy records cannot satisfy formal slots."))
        if (
            _token(selected.unit) != _token(requirement.unit)
            or _token(selected.quantity_kind) != _token(requirement.quantity_kind)
            or _token(selected.value_role) != _token(requirement.value_role)
            or selected.profile_id != requirement.profile_id
            or selected.experiment_scope != requirement.scope
            or selected.consumer_locator != requirement.consumer_locator
        ):
            violations.append(_violation("PAR-SCOPE-MISMATCH", requirement.slot_id,
                                         "selected_parameter", selected.parameter_revision_id,
                                         "Selected parameter must match the exact slot unit, kind, role, scope, profile, and consumer."))

    selected_ids = {
        item.parameter_revision_id for item in required_set.bindings
        if not item.not_applicable and item.parameter_revision_id is not None
    }
    legacy_ids = {item.quarantine_id for item in catalog.legacy_quarantine}
    for selected_id in sorted(selected_ids):
        if selected_id in legacy_ids or records.get(selected_id) and (
            _token(records[selected_id].record_state) == RecordState.LEGACY_ONLY.value
        ):
            violations.append(_violation(
                "PAR-LEGACY-INFLUENCE", selected_id, "parameter_revision_id", selected_id,
                "Legacy reproduction evidence cannot satisfy a formal v2 requirement.",
            ))

    for audit in catalog.locus_audits:
        locus_ids: set[str] = set()
        collision_keys: set[tuple[str, str, str, str, str]] = set()
        for locus in audit.entries:
            if locus.locus_id in locus_ids or not _enum(locus.category, InventoryCategory) or not _enum(
                locus.value_role, ValueRole
            ) or not _enum(locus.disposition, LocusDisposition) or not all(_nonblank(item) for item in (
                locus.component, locus.consumer_locator, locus.scope, locus.profile_id,
                locus.lineage, locus.rationale, locus.related_identity,
            )):
                violations.append(_violation(
                    "PAR-LOCUS-AUDIT-INVALID", audit.audit_id, "entries", locus.locus_id,
                    "Known numeric loci require unique IDs and closed, fully reasoned dispositions.",
                ))
            locus_ids.add(locus.locus_id)
            key = (locus.component, locus.consumer_locator, locus.profile_id,
                   _token(locus.value_role), locus.lineage)
            if key in collision_keys:
                violations.append(_violation(
                    "PAR-LOCUS-CONFLICT", audit.audit_id, "entries", locus.locus_id,
                    "Numeric-locus collisions are evaluated by consumer/profile/role/lineage.",
                ))
            collision_keys.add(key)

    return _gate_result(catalog, source_catalog, inventory, required_set, violations, temporal_context)


def load_parameter_catalog(payload: bytes | str) -> ParameterEvidenceCatalog:
    """Strictly parse the versioned machine authority."""

    def reject_constant(token: str) -> None:
        raise ValueError(f"non-finite number is forbidden: {token}")

    raw = json.loads(payload, parse_constant=reject_constant)
    _reject_floats(raw)
    if not isinstance(raw, dict) or raw.get("authorization_effect") != "none":
        raise ValueError("invalid ParameterEvidence.v1 envelope")

    def exact(data: object, cls: type) -> dict[str, object]:
        if not isinstance(data, dict):
            raise ValueError(f"{cls.__name__} must be an object")
        expected = {item.name for item in fields(cls) if item.init}
        if set(data) != expected:
            raise ValueError(f"{cls.__name__} has unknown or missing fields")
        return data

    def seq(name: str, builder: Callable[[dict[str, object]], object]) -> tuple[object, ...]:
        values = raw.get(name)
        if not isinstance(values, list):
            raise ValueError(f"{name} must be an array")
        return tuple(builder(item) for item in values)  # type: ignore[arg-type]

    def uncertainty(data: object) -> UncertaintyRecord:
        return UncertaintyRecord(**exact(data, UncertaintyRecord))

    def exact_bool(value: object, field_name: str) -> bool:
        if type(value) is not bool:
            raise ValueError(f"{field_name} must be a boolean")
        return value

    def exact_int(value: object, field_name: str) -> int:
        if type(value) is not int:
            raise ValueError(f"{field_name} must be an integer")
        return value

    def parameter(data: dict[str, object]) -> ParameterRevision:
        item = exact(data, ParameterRevision).copy()
        item["value"] = NumericValue(**exact(item["value"], NumericValue))
        item["uncertainty"] = uncertainty(item["uncertainty"])
        for name, cls in (
            ("direct_authority", DirectAuthority), ("derived_authority", DerivedAuthority),
            ("measured_authority", MeasuredAuthority), ("decision_authority", DecisionAuthority),
            ("mock_authority", MockAuthority),
        ):
            if item[name] is not None:
                authority = exact(item[name], cls).copy()
                if cls is DirectAuthority:
                    authority["documented_value"] = NumericValue(**exact(
                        authority["documented_value"], NumericValue
                    ))
                item[name] = cls(**authority)
        return ParameterRevision(**item)

    def derivation(data: dict[str, object]) -> DerivationSpec:
        item = exact(data, DerivationSpec).copy()
        item["decimal_precision"] = exact_int(item["decimal_precision"], "decimal_precision")
        vectors = item["conformance_vectors"]
        if not isinstance(vectors, list):
            raise ValueError("conformance_vectors must be an array")
        item["conformance_vectors"] = tuple(ConformanceVector(**exact(value, ConformanceVector))
                                             for value in vectors)
        return DerivationSpec(**item)

    def decision(data: dict[str, object]) -> DecisionRecord:
        item = exact(data, DecisionRecord).copy()
        for name in ("mutable", "test_locked", "truth_locked"):
            item[name] = exact_bool(item[name], name)
        values = item["parameter_values"]
        if not isinstance(values, list):
            raise ValueError("parameter_values must be an array")
        parsed: list[DecisionValue] = []
        for value in values:
            decision_value = exact(value, DecisionValue).copy()
            decision_value["value"] = NumericValue(**exact(decision_value["value"], NumericValue))
            parsed.append(DecisionValue(**decision_value))
        item["parameter_values"] = tuple(parsed)
        return DecisionRecord(**item)

    def admission(data: dict[str, object]) -> MockAdmission:
        item = exact(data, MockAdmission).copy()
        item["mutable"] = exact_bool(item["mutable"], "mutable")
        claims = item["support_claims"]
        if not isinstance(claims, list):
            raise ValueError("support_claims must be an array")
        item["support_claims"] = tuple(MockSupportClaim(**exact(value, MockSupportClaim))
                                       for value in claims)
        bindings = item["parameter_revision_bindings"]
        if not isinstance(bindings, list):
            raise ValueError("parameter_revision_bindings must be an array")
        item["parameter_revision_bindings"] = tuple(
            MockParameterRevisionBinding(**exact(value, MockParameterRevisionBinding))
            for value in bindings
        )
        return MockAdmission(**item)

    def measurement(data: dict[str, object]) -> MeasurementEvidenceRef:
        item = exact(data, MeasurementEvidenceRef).copy()
        item["byte_size"] = exact_int(item["byte_size"], "byte_size")
        item["uncertainty"] = uncertainty(item["uncertainty"])
        return MeasurementEvidenceRef(**item)

    def inventory(data: dict[str, object]) -> NumericConsumerInventory:
        item = exact(data, NumericConsumerInventory).copy()
        requirements = []
        for value in item["requirements"]:  # type: ignore[union-attr]
            parsed = exact(value, ParameterRequirement).copy()
            parsed["not_applicable_allowed"] = exact_bool(
                parsed["not_applicable_allowed"], "not_applicable_allowed"
            )
            requirements.append(ParameterRequirement(**parsed))
        item["requirements"] = tuple(requirements)
        dispositions = []
        for value in item["category_dispositions"]:  # type: ignore[union-attr]
            parsed = exact(value, CategoryDisposition).copy()
            parsed["owner_approved"] = exact_bool(parsed["owner_approved"], "owner_approved")
            dispositions.append(CategoryDisposition(**parsed))
        item["category_dispositions"] = tuple(dispositions)
        return NumericConsumerInventory(**item)

    def required(data: dict[str, object]) -> RequiredParameterSet:
        item = exact(data, RequiredParameterSet).copy()
        bindings = []
        for value in item["bindings"]:  # type: ignore[union-attr]
            parsed = exact(value, ParameterBinding).copy()
            parsed["not_applicable"] = exact_bool(parsed["not_applicable"], "not_applicable")
            bindings.append(ParameterBinding(**parsed))
        item["bindings"] = tuple(bindings)
        return RequiredParameterSet(**item)

    def audit(data: dict[str, object]) -> NumericLocusAudit:
        item = exact(data, NumericLocusAudit).copy()
        item["entries"] = tuple(NumericLocus(**exact(value, NumericLocus))
                                for value in item["entries"])  # type: ignore[union-attr]
        return NumericLocusAudit(**item)

    expected_top = {item.name for item in fields(ParameterEvidenceCatalog)}
    if set(raw) != expected_top:
        raise ValueError("ParameterEvidence.v1 has unknown or missing top-level fields")
    return ParameterEvidenceCatalog(
        schema_version=raw["schema_version"],
        semantic_vocabulary_version=raw["semantic_vocabulary_version"],
        source_catalog_identity=raw["source_catalog_identity"],
        parameter_revisions=seq("parameter_revisions", parameter),
        derivations=seq("derivations", derivation),
        decisions=seq("decisions", decision),
        mock_admissions=seq("mock_admissions", admission),
        measurements=seq("measurements", measurement),
        inventories=seq("inventories", inventory),
        required_sets=seq("required_sets", required),
        locus_audits=seq("locus_audits", audit),
        legacy_quarantine=seq(
            "legacy_quarantine", lambda data: LegacyQuarantineEntry(**exact(data, LegacyQuarantineEntry))
        ),
    )
