"""Flat immutable contracts for Story 9.5 v1 golden fixture replay."""

from __future__ import annotations

from dataclasses import dataclass, field, fields
from enum import StrEnum
from types import MappingProxyType
from typing import Mapping

from parallel_truth_fingerprint.contracts.semantic_vocabulary import SemanticIdentity


GOLDEN_CATALOG_SCHEMA_VERSION = "v1-golden-fixture-catalog.v1"
GOLDEN_REQUIREMENT_SCHEMA_VERSION = "v1-golden-fixture-requirements.v1"


class FixtureGroup(StrEnum):
    CORE = "core"
    OPTIONAL_DASHBOARD = "optional_dashboard"


class FixtureOrigin(StrEnum):
    FROZEN_HISTORICAL_BYTES = "frozen_historical_bytes"
    RECONSTRUCTED_LEGACY_FIXTURE = "reconstructed_legacy_fixture"
    NON_DOMAIN_SENTINEL = "non_domain_sentinel"
    ADMITTED_DOMAIN_MOCK_FIXTURE = "admitted_domain_mock_fixture"


class NativeVersionStatus(StrEnum):
    EXPLICIT = "explicit"
    VERSIONLESS = "versionless"


class StorageEncoding(StrEnum):
    RAW = "raw"
    BASE64 = "base64"


class NativeReaderOutcome(StrEnum):
    ACCEPTED = "accepted"
    REJECTED = "rejected"
    NOT_INVOKED = "not_invoked"
    UNVERIFIABLE = "unverifiable"


class FixtureGateOutcome(StrEnum):
    ACCEPTED = "accepted"
    REJECTED = "rejected"
    NOT_INVOKED = "not_invoked"
    UNVERIFIABLE = "unverifiable"


class ComparisonMode(StrEnum):
    BYTE_EXACT = "byte_exact"
    SEMANTIC_EXACT = "semantic_exact"


class ReplayRoute(StrEnum):
    REGISTERED_FIXTURE = "registered_fixture"
    EXPLICIT_ENVELOPE = "explicit_envelope"


def _token(value: object) -> object:
    return value.value if isinstance(value, StrEnum) else value


def _thaw(value: object) -> object:
    if hasattr(value, "to_dict"):
        return value.to_dict()  # type: ignore[no-any-return,attr-defined]
    if isinstance(value, Mapping):
        return {str(key): _thaw(item) for key, item in value.items()}
    if isinstance(value, tuple):
        return [_thaw(item) for item in value]
    return _token(value)


class _Record:
    def to_dict(self) -> dict[str, object]:
        return {item.name: _thaw(getattr(self, item.name)) for item in fields(self)}


@dataclass(frozen=True)
class V1GoldenFixtureRequirement(_Record):
    requirement_id: str
    group: FixtureGroup | str
    native_reader_id: str
    allowed_origins: tuple[FixtureOrigin | str, ...]
    expected_legacy_reader_outcome: NativeReaderOutcome | str
    expected_fixture_gate_outcome: FixtureGateOutcome | str
    comparison_mode: ComparisonMode | str
    cardinality: int = 1

    def __post_init__(self) -> None:
        object.__setattr__(self, "allowed_origins", tuple(sorted(
            self.allowed_origins, key=lambda item: str(_token(item))
        )))


@dataclass(frozen=True)
class V1GoldenFixtureRequirementSet(_Record):
    schema_version: str
    requirement_set_id: str
    requirements: tuple[V1GoldenFixtureRequirement, ...]
    limitations: tuple[str, ...]
    authorization_effect: str = field(default="none", init=False)

    def __post_init__(self) -> None:
        object.__setattr__(self, "requirements", tuple(sorted(
            self.requirements, key=lambda item: item.requirement_id
        )))
        object.__setattr__(self, "limitations", tuple(sorted(self.limitations)))


@dataclass(frozen=True)
class FixtureParameterRevisionBinding(_Record):
    parameter_revision_id: str
    revision_sha256: str


@dataclass(frozen=True)
class V1GoldenFixtureEntry(_Record):
    fixture_id: str
    fixture_revision_id: str
    fixture_revision_sha256: str
    requirement_id: str
    baseline_generation: str
    native_contract_id: str
    native_version_status: NativeVersionStatus | str
    native_version_token: str | None
    baseline_id: str
    baseline_entry_id: str
    baseline_entry_sha256: str | None
    origin: FixtureOrigin | str
    filesystem_locator: str | None
    object_key: str | None
    storage_encoding: StorageEncoding | str
    media_type: str
    character_encoding: str | None
    newline_form: str | None
    decoded_byte_length: int
    decoded_sha256: str
    carrier_sha256: str | None
    semantic_identity: SemanticIdentity
    expected_legacy_reader_outcome: NativeReaderOutcome | str
    expected_fixture_gate_outcome: FixtureGateOutcome | str
    expected_reason: str | None
    expected_output_sha256: str | None
    reader_id: str
    comparison_mode: ComparisonMode | str
    comparator_id: str
    comparator_version: str
    compared_fields: tuple[str, ...]
    order_rules: str
    reconstruction_identity: str | None
    mock_admission_id: str | None
    parameter_revision_bindings: tuple[FixtureParameterRevisionBinding, ...]
    limitations: tuple[str, ...]
    prohibited_uses: tuple[str, ...]

    def __post_init__(self) -> None:
        for name in ("compared_fields", "limitations", "prohibited_uses"):
            object.__setattr__(self, name, tuple(sorted(getattr(self, name))))
        object.__setattr__(self, "parameter_revision_bindings", tuple(sorted(
            self.parameter_revision_bindings, key=lambda item: item.parameter_revision_id
        )))


@dataclass(frozen=True)
class V1GoldenAdapterDeclaration(_Record):
    adapter_id: str
    adapter_revision_id: str
    input_fixture_revision_id: str
    output_fixture_revision_id: str
    input_contract_id: str
    output_contract_id: str
    field_mappings: tuple[str, ...]
    code_identity: str
    limitations: tuple[str, ...]

    def __post_init__(self) -> None:
        object.__setattr__(self, "field_mappings", tuple(self.field_mappings))
        object.__setattr__(self, "limitations", tuple(sorted(self.limitations)))


@dataclass(frozen=True)
class V1GoldenFixtureCatalog(_Record):
    schema_version: str
    catalog_id: str
    requirement_set_id: str
    entries: tuple[V1GoldenFixtureEntry, ...]
    adapters: tuple[V1GoldenAdapterDeclaration, ...]
    limitations: tuple[str, ...]
    authorization_effect: str = field(default="none", init=False)

    def __post_init__(self) -> None:
        object.__setattr__(self, "entries", tuple(sorted(
            self.entries, key=lambda item: (item.requirement_id, item.fixture_revision_id)
        )))
        object.__setattr__(self, "adapters", tuple(sorted(
            self.adapters, key=lambda item: item.adapter_revision_id
        )))
        object.__setattr__(self, "limitations", tuple(sorted(self.limitations)))


@dataclass(frozen=True)
class V1GoldenReplayRequest(_Record):
    request_id: str
    route: ReplayRoute | str
    catalog_id: str
    fixture_revision_id: str | None
    supplied_decoded_sha256: str | None
    envelope_id: str | None
    native_version: str | None
    payload_sha256: str
    adapter_revision_id: str | None = None
    authorization_effect: str = field(default="none", init=False)


@dataclass(frozen=True)
class V1GoldenViolation(_Record):
    rule_id: str
    fixture_or_requirement_id: str
    contract_id: str
    field_path: str
    offending_reference: str
    expected_value: str
    observed_value: str
    explanation: str


@dataclass(frozen=True)
class V1GoldenCatalogValidationResult(_Record):
    validation_id: str
    catalog_id: str
    requirement_set_id: str
    fixture_gate_outcome: FixtureGateOutcome | str
    violations: tuple[V1GoldenViolation, ...]
    limitations: tuple[str, ...]
    authorization_effect: str = field(default="none", init=False)

    def __post_init__(self) -> None:
        object.__setattr__(self, "violations", tuple(sorted(
            self.violations,
            key=lambda item: (item.rule_id, item.fixture_or_requirement_id, item.field_path,
                              item.expected_value, item.observed_value),
        )))
        object.__setattr__(self, "limitations", tuple(sorted(self.limitations)))


@dataclass(frozen=True)
class V1GoldenReplayResult(_Record):
    replay_result_id: str
    request_id: str
    catalog_id: str
    fixture_revision_id: str | None
    legacy_reader_outcome: NativeReaderOutcome | str
    fixture_gate_outcome: FixtureGateOutcome | str
    observed_output_sha256: str | None
    violations: tuple[V1GoldenViolation, ...]
    limitations: tuple[str, ...]
    authorization_effect: str = field(default="none", init=False)

    def __post_init__(self) -> None:
        object.__setattr__(self, "violations", tuple(sorted(
            self.violations,
            key=lambda item: (item.rule_id, item.fixture_or_requirement_id, item.field_path,
                              item.expected_value, item.observed_value),
        )))
        object.__setattr__(self, "limitations", tuple(sorted(self.limitations)))
