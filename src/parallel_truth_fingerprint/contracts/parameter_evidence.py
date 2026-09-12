"""Immutable contracts for ParameterEvidence.v1 numerical accountability."""

from __future__ import annotations

from dataclasses import dataclass, field, fields, is_dataclass
from enum import StrEnum
from typing import Mapping


PARAMETER_EVIDENCE_SCHEMA_VERSION = "parameter-evidence.v1"


class ParameterClass(StrEnum):
    DIRECT = "direct"
    DERIVED = "derived"
    MEASURED = "measured"
    PREREGISTERED_FACTOR = "preregistered_factor"
    MOCK = "mock"


class ValueRole(StrEnum):
    SINGLE = "single"
    LOWER_ENDPOINT = "lower_endpoint"
    UPPER_ENDPOINT = "upper_endpoint"


class RecordState(StrEnum):
    VALID = "valid"
    BLOCKED = "blocked"
    UNRESOLVED = "unresolved"
    LEGACY_ONLY = "legacy_only"


class ApprovalState(StrEnum):
    APPROVED = "approved"
    PLANNING_FROZEN = "planning_frozen"
    CONDITIONAL = "conditional"
    CANDIDATE = "candidate"
    PENDING_SOURCE = "pending_source"
    PENDING_DECISION = "pending_decision"


class AccountabilityOutcome(StrEnum):
    ACCOUNTABLE = "accountable"
    BLOCKED = "blocked"


class NumericValueKind(StrEnum):
    SCALAR = "scalar"
    INTERVAL = "interval"
    OBSERVATION_TRANSFORM = "observation_transform"
    UNRESOLVED = "unresolved"


class Unit(StrEnum):
    MILLIAMPERE = "mA"
    PERCENT = "percent"
    ONE = "one"
    DEG_C = "degC"
    BAR = "bar"
    RPM = "rpm"
    SECOND = "second"
    MILLISECOND = "millisecond"
    COUNT = "count"
    BYTE = "byte"


class QuantityKind(StrEnum):
    LOOP_CURRENT = "loop_current"
    NORMALIZED_SPAN = "normalized_span"
    TEMPERATURE = "temperature"
    PRESSURE_GAUGE = "pressure_gauge"
    PRESSURE_ABSOLUTE = "pressure_absolute"
    ROTATIONAL_SPEED = "rotational_speed"
    SPEED_REFERENCE = "speed_reference"
    CAPACITY_REFERENCE = "capacity_reference"
    POWER_REFERENCE = "power_reference"
    NOISE_AMPLITUDE = "noise_amplitude"
    DYNAMIC_FACTOR = "dynamic_factor"
    COMPARISON_TOLERANCE = "comparison_tolerance"
    DECISION_THRESHOLD = "decision_threshold"
    WINDOW_LENGTH = "window_length"
    QUEUE_CAPACITY = "queue_capacity"
    CAPTURE_LOSS_FRACTION = "capture_loss_fraction"
    DURATION = "duration"
    RAMP_DURATION = "ramp_duration"
    DWELL_DURATION = "dwell_duration"
    REPETITION_COUNT = "repetition_count"
    RANDOM_SEED = "random_seed"
    MODEL_HYPERPARAMETER = "model_hyperparameter"
    TRAINING_STOPPING = "training_stopping"
    SPLIT_FRACTION = "split_fraction"
    CALIBRATION_PARAMETER = "calibration_parameter"
    METRIC_PARAMETER = "metric_parameter"
    FUSION_PARAMETER = "fusion_parameter"


class UncertaintyKind(StrEnum):
    UNCERTAINTY = "uncertainty"
    DISPERSION = "dispersion"
    NOT_APPLICABLE = "not_applicable"


class AuthenticFeasibility(StrEnum):
    AVAILABLE = "available"
    UNAVAILABLE_WITH_EVIDENCE = "unavailable_with_evidence"
    UNRESOLVED = "unresolved"


class RandomnessMode(StrEnum):
    DETERMINISTIC = "deterministic"
    SEEDED = "seeded"


class ReproductionDisposition(StrEnum):
    STILL_UNAVAILABLE_WITH_EVIDENCE = "still_unavailable_with_evidence"
    AUTHENTIC_PATH_AVAILABLE = "authentic_path_available"
    UNRESOLVED = "unresolved"


class DerivationKind(StrEnum):
    CONSTANT_RESULT = "constant_result"
    OBSERVATION_TRANSFORM = "observation_transform"


class InventoryCategory(StrEnum):
    RANGES_ENDPOINTS = "ranges_endpoints"
    SCHEDULE_SETPOINTS = "schedule_setpoints"
    NOISE = "noise"
    DYNAMICS = "dynamics"
    TOLERANCES = "tolerances"
    THRESHOLDS = "thresholds"
    PREPROCESSING_WINDOWS = "preprocessing_windows"
    QUEUES_BACKPRESSURE = "queues_backpressure"
    CAPTURE_LOSS_QUALITY = "capture_loss_quality"
    DURATION_RAMP_DWELL_TIMING = "duration_ramp_dwell_timing"
    REPETITIONS_SEEDS = "repetitions_seeds"
    MODEL_TRAINING_HYPERPARAMETERS_STOPPING = "model_training_hyperparameters_stopping"
    SPLIT_CALIBRATION = "split_calibration"
    METRICS_EVALUATION = "metrics_evaluation"
    FUSION = "fusion"


class CategoryState(StrEnum):
    REQUIRED = "required"
    NOT_APPLICABLE = "not_applicable"


class LocusDisposition(StrEnum):
    FORMAL_V2_REQUIRED = "formal_v2_required"
    LEGACY_V1_ONLY = "legacy_v1_only"
    INFRASTRUCTURE_EXEMPT = "infrastructure_exempt"
    UNRESOLVED_FUTURE_V2 = "unresolved_future_v2"


def _ordered(values: object, key: str | None = None) -> tuple[object, ...]:
    if not isinstance(values, (list, tuple)):
        raise TypeError("array-valued fields require a list or tuple")
    items = tuple(values)
    if key is None:
        return tuple(sorted(items, key=lambda item: str(item.value if isinstance(item, StrEnum) else item)))
    return tuple(sorted(items, key=lambda item: str(getattr(item, key))))


def _primitive(value: object) -> object:
    if isinstance(value, StrEnum):
        return value.value
    if is_dataclass(value):
        return {item.name: _primitive(getattr(value, item.name)) for item in fields(value)}
    if isinstance(value, Mapping):
        return {str(key): _primitive(item) for key, item in sorted(value.items())}
    if isinstance(value, tuple):
        return [_primitive(item) for item in value]
    return value


class _Record:
    def to_dict(self) -> dict[str, object]:
        return {item.name: _primitive(getattr(self, item.name)) for item in fields(self)}


@dataclass(frozen=True)
class NumericValue(_Record):
    kind: NumericValueKind | str
    scalar: str | None = None
    lower: str | None = None
    upper: str | None = None
    lower_inclusive: bool | None = None
    upper_inclusive: bool | None = None
    unresolved_reason: str | None = None


@dataclass(frozen=True)
class UncertaintyRecord(_Record):
    kind: UncertaintyKind | str
    estimate: str | None
    unit: Unit | str | None
    method: str | None
    component_ids: tuple[str, ...]
    coverage: str | None
    evidence_reference: str | None
    rationale: str | None

    def __post_init__(self) -> None:
        object.__setattr__(self, "component_ids", _ordered(self.component_ids))


@dataclass(frozen=True)
class DirectAuthority(_Record):
    source_revision_id: str
    source_use_id: str
    documented_value: NumericValue
    documented_unit: Unit | str
    documented_quantity_kind: QuantityKind | str


@dataclass(frozen=True)
class DerivedAuthority(_Record):
    derivation_id: str


@dataclass(frozen=True)
class MeasuredAuthority(_Record):
    measurement_evidence_id: str


@dataclass(frozen=True)
class DecisionAuthority(_Record):
    decision_id: str


@dataclass(frozen=True)
class MockAuthority(_Record):
    mock_admission_id: str
    mock_claim_id: str


@dataclass(frozen=True)
class ParameterRevision(_Record):
    parameter_id: str
    parameter_revision_id: str
    revision_sha256: str
    parameter_class: ParameterClass | str
    value_role: ValueRole | str
    value: NumericValue
    unit: Unit | str
    quantity_kind: QuantityKind | str
    record_state: RecordState | str
    approval_state: ApprovalState | str
    migration_status: str
    profile_id: str
    experiment_scope: str
    authentic_reproduction_feasibility: AuthenticFeasibility | str
    prototype_component: str
    consumer_locator: str
    research_question: str
    evidence_track: str
    final_package_element: str
    transferability_rationale: str
    limitations: tuple[str, ...]
    uncertainty: UncertaintyRecord
    owner: str
    synthetic_status: str
    direct_authority: DirectAuthority | None = None
    derived_authority: DerivedAuthority | None = None
    measured_authority: MeasuredAuthority | None = None
    decision_authority: DecisionAuthority | None = None
    mock_authority: MockAuthority | None = None

    def __post_init__(self) -> None:
        object.__setattr__(self, "limitations", _ordered(self.limitations))


@dataclass(frozen=True)
class ConformanceVector(_Record):
    input_value: str
    expected_output: str


@dataclass(frozen=True)
class DerivationSpec(_Record):
    derivation_id: str
    derivation_kind: DerivationKind | str
    operation: str
    input_low_revision_id: str
    input_high_revision_id: str
    output_low_revision_id: str
    output_high_revision_id: str
    selected_input_revision_id: str | None
    observation_variable: str | None
    observation_unit: Unit | str | None
    declared_output: str | None
    output_unit: Unit | str
    conformance_vectors: tuple[ConformanceVector, ...]
    decimal_precision: int
    rounding: str

    def __post_init__(self) -> None:
        object.__setattr__(self, "conformance_vectors", _ordered(self.conformance_vectors, "input_value"))


@dataclass(frozen=True)
class DecisionValue(_Record):
    parameter_id: str
    value: NumericValue
    unit: Unit | str
    quantity_kind: QuantityKind | str
    value_role: ValueRole | str


@dataclass(frozen=True)
class DecisionRecord(_Record):
    decision_id: str
    record_sha256: str
    content_sha256: str
    owner: str
    approved_by: str
    approved_at: str
    freeze_time: str
    mutable: bool
    test_locked: bool
    truth_locked: bool
    parameter_ids: tuple[str, ...]
    parameter_values: tuple[DecisionValue, ...]
    profile_id: str
    experiment_scope: str
    component: str
    question: str
    evidence_track: str
    final_output: str
    rationale: str
    source_use_ids: tuple[str, ...]
    prohibited_interpretations: tuple[str, ...]
    limitations: tuple[str, ...]

    def __post_init__(self) -> None:
        object.__setattr__(self, "parameter_values", _ordered(self.parameter_values, "parameter_id"))
        for name in ("parameter_ids", "source_use_ids", "prohibited_interpretations", "limitations"):
            object.__setattr__(self, name, _ordered(getattr(self, name)))


@dataclass(frozen=True)
class MockSupportClaim(_Record):
    mock_claim_id: str
    behavior: str
    expected_value: str | None
    unit: Unit | str | None
    quantity_kind: QuantityKind | str | None
    scope: str
    source_use_ids: tuple[str, ...]

    def __post_init__(self) -> None:
        object.__setattr__(self, "source_use_ids", _ordered(self.source_use_ids))


@dataclass(frozen=True)
class MockParameterRevisionBinding(_Record):
    parameter_revision_id: str
    revision_sha256: str


@dataclass(frozen=True)
class MockAdmission(_Record):
    mock_admission_id: str
    record_sha256: str
    content_sha256: str
    owner: str
    approved_by: str
    approved_at: str
    mutable: bool
    authentic_path_assessment: str
    authentic_feasibility: AuthenticFeasibility | str
    reproduction_assessment_identity: str
    reproduction_disposition: ReproductionDisposition | str
    prototype_component_id: str
    exact_entrypoint: str
    interface_schema_version: str
    code_identity: str
    runtime_identity: str
    configuration_identity: str
    parameter_closure_id: str
    parameter_revision_bindings: tuple[MockParameterRevisionBinding, ...]
    randomness_mode: RandomnessMode | str
    seed_closure_id: str
    seed_parameter_revision_id: str | None
    seed_parameter_revision_sha256: str | None
    permitted_output_role: str
    permitted_output_record_family: str
    semantic_provenance: str
    emission_trace_identity: str
    simulator_profile: str
    purpose: str
    component: str
    question: str
    evidence_track: str
    final_output: str
    replacement_condition: str
    support_claims: tuple[MockSupportClaim, ...]
    prohibited_claims: tuple[str, ...]
    prohibited_output_roles: tuple[str, ...]
    limitations: tuple[str, ...]

    def __post_init__(self) -> None:
        object.__setattr__(self, "support_claims", _ordered(self.support_claims, "mock_claim_id"))
        object.__setattr__(self, "parameter_revision_bindings", _ordered(
            self.parameter_revision_bindings, "parameter_revision_id"
        ))
        object.__setattr__(self, "prohibited_claims", _ordered(self.prohibited_claims))
        object.__setattr__(self, "prohibited_output_roles", _ordered(self.prohibited_output_roles))
        object.__setattr__(self, "limitations", _ordered(self.limitations))


@dataclass(frozen=True)
class MeasurementEvidenceRef(_Record):
    measurement_evidence_id: str
    version: str
    locator: str
    sha256: str
    byte_size: int
    method_identity: str
    environment_identity: str
    profile_id: str
    experiment_scope: str
    sample_ids: tuple[str, ...]
    run_ids: tuple[str, ...]
    measured_at: str
    result: str
    unit: Unit | str
    uncertainty: UncertaintyRecord
    owner: str
    approval_state: ApprovalState | str
    limitations: tuple[str, ...]

    def __post_init__(self) -> None:
        for name in ("sample_ids", "run_ids", "limitations"):
            object.__setattr__(self, name, _ordered(getattr(self, name)))


@dataclass(frozen=True)
class TemporalGateContext(_Record):
    context_id: str
    freeze_identity: str
    freeze_time: str
    test_identity: str
    test_time: str
    truth_identity: str
    truth_time: str


@dataclass(frozen=True)
class ParameterRequirement(_Record):
    slot_id: str
    category: InventoryCategory | str
    consumer_locator: str
    quantity_kind: QuantityKind | str
    unit: Unit | str
    value_role: ValueRole | str
    scope: str
    profile_id: str
    not_applicable_allowed: bool


@dataclass(frozen=True)
class CategoryDisposition(_Record):
    category: InventoryCategory | str
    state: CategoryState | str
    rationale: str
    owner_approved: bool


@dataclass(frozen=True)
class NumericConsumerInventory(_Record):
    inventory_id: str
    component_identity: str
    contract_identity: str
    code_identity: str
    scope: str
    profile_id: str
    requirements: tuple[ParameterRequirement, ...]
    category_dispositions: tuple[CategoryDisposition, ...]

    def __post_init__(self) -> None:
        object.__setattr__(self, "requirements", _ordered(self.requirements, "slot_id"))
        object.__setattr__(self, "category_dispositions", _ordered(self.category_dispositions, "category"))


@dataclass(frozen=True)
class ParameterBinding(_Record):
    slot_id: str
    parameter_revision_id: str | None
    parameter_revision_sha256: str | None
    not_applicable: bool
    rationale: str


@dataclass(frozen=True)
class RequiredParameterSet(_Record):
    required_set_id: str
    catalog_identity: str
    source_catalog_identity: str
    vocabulary_version: str
    inventory_id: str
    scope: str
    profile_id: str
    experiment_id: str
    component_identity: str
    bindings: tuple[ParameterBinding, ...]

    def __post_init__(self) -> None:
        object.__setattr__(self, "bindings", _ordered(self.bindings, "slot_id"))


@dataclass(frozen=True)
class NumericLocus(_Record):
    locus_id: str
    component: str
    consumer_locator: str
    category: InventoryCategory | str
    scope: str
    profile_id: str
    value_role: ValueRole | str
    lineage: str
    disposition: LocusDisposition | str
    rationale: str
    related_identity: str


@dataclass(frozen=True)
class NumericLocusAudit(_Record):
    audit_id: str
    entries: tuple[NumericLocus, ...]

    def __post_init__(self) -> None:
        object.__setattr__(self, "entries", _ordered(self.entries, "locus_id"))


@dataclass(frozen=True)
class LegacyQuarantineEntry(_Record):
    quarantine_id: str
    group: str
    current_value_or_pattern: str
    unit: str
    repository_locator: str
    formal_v2_status: str
    legacy_mode_status: str
    reason: str
    resolution_requirement: str
    allowed_effect: str


@dataclass(frozen=True)
class ParameterEvidenceCatalog(_Record):
    schema_version: str
    semantic_vocabulary_version: str
    source_catalog_identity: str
    parameter_revisions: tuple[ParameterRevision, ...]
    derivations: tuple[DerivationSpec, ...]
    decisions: tuple[DecisionRecord, ...]
    mock_admissions: tuple[MockAdmission, ...]
    measurements: tuple[MeasurementEvidenceRef, ...]
    inventories: tuple[NumericConsumerInventory, ...]
    required_sets: tuple[RequiredParameterSet, ...]
    locus_audits: tuple[NumericLocusAudit, ...]
    legacy_quarantine: tuple[LegacyQuarantineEntry, ...]
    authorization_effect: str = field(default="none", init=False)

    def __post_init__(self) -> None:
        order = {
            "parameter_revisions": "parameter_revision_id", "derivations": "derivation_id",
            "decisions": "decision_id", "mock_admissions": "mock_admission_id",
            "measurements": "measurement_evidence_id", "inventories": "inventory_id",
            "required_sets": "required_set_id", "locus_audits": "audit_id",
            "legacy_quarantine": "quarantine_id",
        }
        for name, key in order.items():
            object.__setattr__(self, name, _ordered(getattr(self, name), key))


@dataclass(frozen=True)
class ParameterViolation(_Record):
    rule_id: str
    record_id: str
    field_path: str
    offending_reference: str
    explanation: str


@dataclass(frozen=True)
class ParameterGateResult(_Record):
    gate_result_id: str
    catalog_identity: str
    source_catalog_identity: str
    vocabulary_version: str
    inventory_id: str
    required_set_id: str
    temporal_context_id: str | None
    decision_ids: tuple[str, ...]
    measurement_evidence_ids: tuple[str, ...]
    mock_admission_ids: tuple[str, ...]
    validator_identity: str
    accountability_outcome: AccountabilityOutcome | str
    violations: tuple[ParameterViolation, ...]
    limitations: tuple[str, ...]
    authorization_effect: str = field(default="none", init=False)

    def __post_init__(self) -> None:
        for name in ("decision_ids", "measurement_evidence_ids", "mock_admission_ids"):
            object.__setattr__(self, name, _ordered(getattr(self, name)))
        object.__setattr__(self, "violations", tuple(sorted(
            self.violations, key=lambda item: (item.rule_id, item.record_id, item.field_path,
                                                item.offending_reference)
        )))
        object.__setattr__(self, "limitations", _ordered(self.limitations))
