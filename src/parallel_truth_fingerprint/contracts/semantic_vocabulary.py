"""Versioned semantic vocabulary shared by scientific evidence contracts."""

from __future__ import annotations

from dataclasses import dataclass, field
from enum import StrEnum
from types import MappingProxyType
from typing import Mapping


SEMANTIC_VOCABULARY_VERSION = "semantic-vocabulary.v1"


class DetectionModality(StrEnum):
    PHYSICAL_INSTRUMENTATION = "physical_instrumentation"
    LINUX_HOST_SYSCALL = "linux_host_syscall"


class RepresentationKind(StrEnum):
    RAW_CURRENT_MA = "raw_current_ma"
    NORMALIZED_SPAN = "normalized_span"
    ENGINEERING_VALUE = "engineering_value"
    CATEGORICAL_SYSCALL_EVENT = "categorical_syscall_event"


class ModelFamily(StrEnum):
    LSTM = "lstm"
    GRU = "gru"
    AUTOENCODER = "autoencoder"
    BASELINE = "baseline"


class EvidenceRole(StrEnum):
    CUSTOM_GENERATED = "custom_generated"
    OFFICIAL_REAL = "official_real"
    FIXTURE_TEST = "fixture_test"
    PUBLISHED_REFERENCE = "published_reference"
    RUNTIME_EVIDENCE = "runtime_evidence"
    LEGACY_V1 = "legacy_v1"


class ResultRole(StrEnum):
    NONE = "none"
    LOCALLY_MEASURED = "locally_measured"
    PUBLISHED_REFERENCE = "published_reference"
    FIXTURE_EXPECTED = "fixture_expected"
    LEGACY_RECORDED = "legacy_recorded"


class ScientificStatus(StrEnum):
    QUALIFIED = "qualified"
    UNQUALIFIED = "unqualified"
    BLOCKED = "blocked"
    UNSUPPORTED = "unsupported"
    TEST_ONLY = "test_only"
    REFERENCE_ONLY = "reference_only"
    LEGACY = "legacy"


class SyntheticStatus(StrEnum):
    AUTHENTIC = "authentic"
    MOCK = "mock"
    MOCK_DERIVED = "mock_derived"
    NOT_APPLICABLE = "not_applicable"


class EntityKind(StrEnum):
    SOURCE = "source"
    DATASET = "dataset"
    RUN = "run"
    ARTIFACT = "artifact"
    REPRESENTATION = "representation"
    MODEL = "model"
    DETECTOR_BUNDLE = "detector_bundle"
    SCORE = "score"
    EVALUATION_RESULT = "evaluation_result"
    FIXTURE = "fixture"
    LEGACY_MAPPING = "legacy_mapping"


class DatasetFamily(StrEnum):
    ADFA_LD = "adfa_ld"
    LID_DS_2021 = "lid_ds_2021"
    HAI_23_05 = "hai_23_05"
    PTFP_CUSTOM_V1 = "ptfp_custom_v1"


class DomainScope(StrEnum):
    COMPRESSOR_PROTOTYPE = "compressor_prototype"
    NATIVE_ADFA_LD = "native_adfa_ld"
    NATIVE_LID_DS_2021 = "native_lid_ds_2021"
    NATIVE_HAI_23_05 = "native_hai_23_05"
    PTFP_CUSTOM_CONTROLLED = "ptfp_custom_controlled"
    REAL_PLANT = "real_plant"
    NOT_APPLICABLE = "not_applicable"


class EvidenceOrigin(StrEnum):
    OFFICIAL_NATIVE = "official_native"
    AUTHENTIC_CAPTURE = "authentic_capture"
    PROTOTYPE_GENERATED = "prototype_generated"
    MOCK_PARAMETERIZED = "mock_parameterized"
    MEASURED = "measured"
    TEST_FIXTURE = "test_fixture"


VOCABULARY_AXES: tuple[type[StrEnum], ...] = (
    DetectionModality,
    RepresentationKind,
    ModelFamily,
    EvidenceRole,
    ResultRole,
    ScientificStatus,
    SyntheticStatus,
    EntityKind,
    DatasetFamily,
    DomainScope,
    EvidenceOrigin,
)


def _token(value: object) -> object:
    return value.value if isinstance(value, StrEnum) else value


def _as_items(values: object) -> tuple[object, ...]:
    if isinstance(values, (list, tuple)):
        return tuple(values)
    return (values,)


def _normalized_tokens(values: object) -> tuple[object, ...]:
    by_token = {str(_token(value)): value for value in _as_items(values)}
    return tuple(by_token[key] for key in sorted(by_token))


def _normalized_collection(values: object) -> tuple[object, ...]:
    unique: list[object] = []
    for value in _as_items(values):
        if not any(value == existing for existing in unique):
            unique.append(value)
    return tuple(sorted(unique, key=lambda item: (type(item).__name__, repr(item))))


def _freeze(value: object) -> object:
    if isinstance(value, Mapping):
        return MappingProxyType({str(key): _freeze(item) for key, item in value.items()})
    if isinstance(value, (list, tuple)):
        return tuple(_freeze(item) for item in value)
    return value


def _thaw(value: object) -> object:
    if isinstance(value, Mapping):
        return {str(key): _thaw(item) for key, item in value.items()}
    if isinstance(value, tuple):
        return [_thaw(item) for item in value]
    return _token(value)


@dataclass(frozen=True)
class SemanticVocabularyDefinition:
    version: str
    axes: tuple[tuple[str, tuple[str, ...]], ...]

    @classmethod
    def current(cls) -> SemanticVocabularyDefinition:
        return cls(
            version=SEMANTIC_VOCABULARY_VERSION,
            axes=tuple(
                (axis.__name__, tuple(member.value for member in axis))
                for axis in VOCABULARY_AXES
            ),
        )

    def to_dict(self) -> dict[str, object]:
        return {
            "version": self.version,
            "axes": {name: list(tokens) for name, tokens in self.axes},
        }


@dataclass(frozen=True)
class MockInfluence:
    field_path: str
    parameter_evidence_reference: str
    mock_admission_reference: str
    derivation: str | None = None

    def to_dict(self) -> dict[str, object]:
        return {
            "field_path": self.field_path,
            "parameter_evidence_reference": self.parameter_evidence_reference,
            "mock_admission_reference": self.mock_admission_reference,
            "derivation": self.derivation,
        }


@dataclass(frozen=True)
class SemanticIdentity:
    vocabulary_version: str | None
    identity_id: str
    entity_kind: EntityKind | str
    modalities: tuple[DetectionModality | str, ...]
    representations: tuple[RepresentationKind | str, ...]
    model_families: tuple[ModelFamily | str, ...]
    evidence_role: EvidenceRole | str
    result_role: ResultRole | str
    scientific_status: ScientificStatus | str
    synthetic_status: SyntheticStatus | str
    evidence_origin: EvidenceOrigin | str | None
    domain_scope: DomainScope | str
    numeric_authority_references: tuple[str, ...]
    formal_evidence: bool
    generation_origin: EvidenceOrigin | str | None = None
    mock_influences: tuple[MockInfluence, ...] = ()
    dataset_family: DatasetFamily | str | None = None
    dataset_version: str | None = None
    dataset_native_scope: str | None = None
    dataset_native_role: str | None = None
    dataset_subset: str | None = None
    provenance_references: tuple[str, ...] = ()
    qualification_references: tuple[str, ...] = ()
    source_qualification_reference: str | None = None
    owning_gate_reference: str | None = None
    mock_admission_reference: str | None = None
    authentic_capture_reference: str | None = None
    detector_bundle_reference: str | None = None
    limitations: tuple[str, ...] = ()

    def __post_init__(self) -> None:
        for name in ("modalities", "representations", "model_families"):
            object.__setattr__(self, name, _normalized_tokens(getattr(self, name)))
        for name in (
            "numeric_authority_references",
            "provenance_references",
            "qualification_references",
            "limitations",
        ):
            object.__setattr__(self, name, _normalized_collection(getattr(self, name)))
        if any(not isinstance(item, MockInfluence) for item in self.mock_influences):
            raise TypeError("mock_influences must contain only MockInfluence records")
        object.__setattr__(
            self,
            "mock_influences",
            tuple(sorted(self.mock_influences, key=lambda item: (item.field_path, item.parameter_evidence_reference))),
        )

    def to_dict(self) -> dict[str, object]:
        return {
            "vocabulary_version": self.vocabulary_version,
            "identity_id": self.identity_id,
            "entity_kind": _token(self.entity_kind),
            "modalities": [_token(item) for item in self.modalities],
            "representations": [_token(item) for item in self.representations],
            "model_families": [_token(item) for item in self.model_families],
            "evidence_role": _token(self.evidence_role),
            "result_role": _token(self.result_role),
            "scientific_status": _token(self.scientific_status),
            "synthetic_status": _token(self.synthetic_status),
            "evidence_origin": _token(self.evidence_origin),
            "generation_origin": _token(self.generation_origin),
            "mock_influences": [item.to_dict() for item in self.mock_influences],
            "dataset_family": _token(self.dataset_family),
            "dataset_version": self.dataset_version,
            "dataset_native_scope": self.dataset_native_scope,
            "dataset_native_role": self.dataset_native_role,
            "dataset_subset": self.dataset_subset,
            "domain_scope": _token(self.domain_scope),
            "numeric_authority_references": list(self.numeric_authority_references),
            "provenance_references": list(self.provenance_references),
            "qualification_references": list(self.qualification_references),
            "source_qualification_reference": self.source_qualification_reference,
            "owning_gate_reference": self.owning_gate_reference,
            "mock_admission_reference": self.mock_admission_reference,
            "authentic_capture_reference": self.authentic_capture_reference,
            "detector_bundle_reference": self.detector_bundle_reference,
            "limitations": list(self.limitations),
            "formal_evidence": self.formal_evidence,
        }


@dataclass(frozen=True)
class SemanticViolation:
    rule_id: str
    fields: tuple[str, ...]
    offending_tokens: tuple[str, ...]
    explanation: str

    def to_dict(self) -> dict[str, object]:
        return {
            "rule_id": self.rule_id,
            "fields": list(self.fields),
            "offending_tokens": list(self.offending_tokens),
            "explanation": self.explanation,
        }


@dataclass(frozen=True)
class SemanticValidationResult:
    supported: bool
    valid: bool
    violations: tuple[SemanticViolation, ...]
    authorization_effect: str = "none"

    def to_dict(self) -> dict[str, object]:
        return {
            "supported": self.supported,
            "valid": self.valid,
            "violations": [violation.to_dict() for violation in self.violations],
            "authorization_effect": self.authorization_effect,
        }


@dataclass(frozen=True)
class UnsupportedSemanticIdentity:
    raw_version: object
    raw_payload: Mapping[str, object]
    violations: tuple[SemanticViolation, ...]
    scientific_status: ScientificStatus = field(default=ScientificStatus.UNSUPPORTED, init=False)

    def __post_init__(self) -> None:
        object.__setattr__(self, "raw_payload", _freeze(self.raw_payload))

    def to_dict(self) -> dict[str, object]:
        return {
            "raw_version": _thaw(self.raw_version),
            "raw_payload": _thaw(self.raw_payload),
            "violations": [violation.to_dict() for violation in self.violations],
            "scientific_status": self.scientific_status.value,
        }


@dataclass(frozen=True)
class LegacySemanticMapping:
    mapping_id: str
    vocabulary_version: str
    baseline_id: str
    entry_id: str
    original_field: str
    original_value: str
    current_semantic_assignment: tuple[tuple[str, str], ...]
    provenance_references: tuple[str, ...]
    limitations: tuple[str, ...]
    scientific_status: ScientificStatus = field(default=ScientificStatus.LEGACY, init=False)

    def __post_init__(self) -> None:
        object.__setattr__(self, "current_semantic_assignment", tuple(sorted(set(self.current_semantic_assignment))))
        object.__setattr__(self, "provenance_references", tuple(sorted(set(self.provenance_references))))
        object.__setattr__(self, "limitations", tuple(sorted(set(self.limitations))))

    def to_dict(self) -> dict[str, object]:
        return {
            "mapping_id": self.mapping_id,
            "vocabulary_version": self.vocabulary_version,
            "baseline_id": self.baseline_id,
            "entry_id": self.entry_id,
            "original_field": self.original_field,
            "original_value": self.original_value,
            "current_semantic_assignment": [
                {"field": field_name, "value": token}
                for field_name, token in self.current_semantic_assignment
            ],
            "provenance_references": list(self.provenance_references),
            "limitations": list(self.limitations),
            "scientific_status": self.scientific_status.value,
        }
