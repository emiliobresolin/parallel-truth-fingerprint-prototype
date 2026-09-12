"""Fail-closed v2 physical feature schemas and canonical projections.

This module deliberately does not convert transmitter values, fit preprocessing,
read evidence, resolve aliases, or turn a feature row into a model tensor.  A
schema declares which already-canonical ``SignalObservation.v2`` field may be
used; callers must supply all authority resolution and frozen preprocessing.
"""
from __future__ import annotations

import hashlib
import json
import re
from dataclasses import dataclass, fields
from typing import Any, Callable, Mapping

from parallel_truth_fingerprint.contracts.scientific_governance import is_immutable_id
from parallel_truth_fingerprint.contracts.signal_observation import SignalObservation


PHYSICAL_FEATURE_SCHEMA_VERSION = "PhysicalFeatureSchema.v2"
LEGACY_BASELINE_STATUS = "LEGACY_BASELINE"
_TOKEN = re.compile(r"[a-z][a-z0-9_]*\Z")
_VERSION = re.compile(r"v[1-9][0-9]*\Z")
_PROHIBITED = ("truth", "label", "outcome", "intervention", "scenario", "decision", "fusion", "future")
_SOURCES = {
    "raw_current": {"raw_current.value"},
    "normalized_span": {"normalized_span.value"},
    "engineering_value": {"engineering_value.value"},
    "quality": {"quality_trace.outcome", "quality_trace.conversion_disposition", "diagnostics"},
    "temporal": {"source_timestamp", "observed_timestamp", "source_sequence"},
    "operating_context": set(),
}
_MISSINGNESS = {"forbid", "explicit_unavailable"}
_DATA_TYPES = {"canonical_decimal", "canonical_utc", "positive_integer", "closed_token", "diagnostic_set"}


class FeatureSchemaError(ValueError):
    """Stable machine-readable failure for a schema or projection."""
    def __init__(self, code: str, field: str, token: str) -> None:
        self.code, self.field, self.token = code, field, token
        super().__init__(f"{code}:{field}:{token}")


@dataclass(frozen=True)
class LegacyBaselineCatalogue:
    """Comparison metadata only; deliberately not a v2 feature schema."""
    contract_id: str
    contract_version: str
    artifact_id: str
    status: str = LEGACY_BASELINE_STATUS

    def __post_init__(self) -> None:
        if not isinstance(self.contract_id, str) or not self.contract_id or not isinstance(self.contract_version, str) or not self.contract_version:
            raise FeatureSchemaError("PFS2_LEGACY", "legacy_contract", "contract_identity_required")
        _immutable(self.artifact_id, "legacy.artifact_id")
        if self.status != LEGACY_BASELINE_STATUS:
            raise FeatureSchemaError("PFS2_LEGACY", "status", "legacy_baseline_required")


def _token(value: object, field: str) -> str:
    if not isinstance(value, str) or not _TOKEN.fullmatch(value):
        raise FeatureSchemaError("PFS2_SCHEMA", field, "closed_token_required")
    return value


def _immutable(value: object, field: str) -> str:
    if not isinstance(value, str) or not is_immutable_id(value):
        raise FeatureSchemaError("PFS2_AUTHORITY", field, "immutable_reference_required")
    return value


def _safe(value: str, field: str) -> None:
    if any(word in value.lower() for word in _PROHIBITED):
        raise FeatureSchemaError("PFS2_TRUTH_ISOLATION", field, "prohibited_detector_content")


@dataclass(frozen=True)
class FeatureDefinition:
    """One ordered, source-addressed feature; no numeric encoding is implied."""
    name: str
    source_field: str
    representation: str
    unit: str
    data_type: str
    compatible_profile_ids: tuple[str, ...]
    missingness_policy: str
    parameter_evidence_references: tuple[str, ...]
    preprocessing_id: str
    availability: str = "available"

    def __post_init__(self) -> None:
        _token(self.name, "feature.name"); _safe(self.name, "feature.name")
        if self.representation not in _SOURCES:
            raise FeatureSchemaError("PFS2_REPRESENTATION", "feature.representation", "undeclared_representation")
        if not isinstance(self.source_field, str) or not self.source_field:
            raise FeatureSchemaError("PFS2_SOURCE", "feature.source_field", "source_required")
        _safe(self.source_field, "feature.source_field")
        if self.representation == "operating_context":
            if not self.source_field.startswith("operating_context.") or self.source_field.count(".") != 1:
                raise FeatureSchemaError("PFS2_SOURCE", "feature.source_field", "operating_context_path_required")
        elif self.source_field not in _SOURCES[self.representation]:
            raise FeatureSchemaError("PFS2_SOURCE", "feature.source_field", "representation_path_mismatch")
        if not isinstance(self.unit, str) or not self.unit:
            raise FeatureSchemaError("PFS2_UNIT", "feature.unit", "unit_required")
        if self.data_type not in _DATA_TYPES:
            raise FeatureSchemaError("PFS2_TYPE", "feature.data_type", "undeclared_data_type")
        if self.missingness_policy not in _MISSINGNESS:
            raise FeatureSchemaError("PFS2_MISSINGNESS", "feature.missingness_policy", "undeclared_policy")
        if self.availability not in {"available", "excluded", "unavailable"}:
            raise FeatureSchemaError("PFS2_AVAILABILITY", "feature.availability", "closed_state_required")
        profile_ids = tuple(self.compatible_profile_ids)
        refs = tuple(self.parameter_evidence_references)
        if self.representation != "operating_context" and not profile_ids:
            raise FeatureSchemaError("PFS2_PROFILE", "feature.compatible_profile_ids", "nonempty_required")
        if not refs:
            raise FeatureSchemaError("PFS2_AUTHORITY", "feature.parameter_evidence_references", "nonempty_required")
        for value in profile_ids: _immutable(value, "feature.compatible_profile_ids")
        for value in refs: _immutable(value, "feature.parameter_evidence_references")
        _immutable(self.preprocessing_id, "feature.preprocessing_id")
        if profile_ids != tuple(sorted(set(profile_ids))) or refs != tuple(sorted(set(refs))):
            raise FeatureSchemaError("PFS2_CANONICAL", "feature.references", "ordered_unique_required")
        object.__setattr__(self, "compatible_profile_ids", profile_ids)
        object.__setattr__(self, "parameter_evidence_references", refs)


@dataclass(frozen=True)
class FeatureSchema:
    schema_id: str
    version: str
    features: tuple[FeatureDefinition, ...]
    schema_content_id: str
    schema_version: str = PHYSICAL_FEATURE_SCHEMA_VERSION
    legacy_status: str | None = None

    def __post_init__(self) -> None:
        _token(self.schema_id, "schema_id")
        if not isinstance(self.version, str) or not _VERSION.fullmatch(self.version):
            raise FeatureSchemaError("PFS2_SCHEMA", "version", "version_token_required")
        if self.schema_version != PHYSICAL_FEATURE_SCHEMA_VERSION:
            raise FeatureSchemaError("PFS2_SCHEMA", "schema_version", "physical_feature_schema_v2_required")
        items = tuple(self.features)
        if not items:
            raise FeatureSchemaError("PFS2_SCHEMA", "features", "nonempty_required")
        if any(not isinstance(item, FeatureDefinition) for item in items):
            raise FeatureSchemaError("PFS2_SCHEMA", "features", "definitions_required")
        names = tuple(item.name for item in items)
        if len(names) != len(set(names)):
            raise FeatureSchemaError("PFS2_SCHEMA", "features", "unique_names_required")
        if self.legacy_status is not None:
            raise FeatureSchemaError("PFS2_LEGACY", "legacy_status", "v2_schema_cannot_be_legacy")
        if not isinstance(self.schema_content_id, str) or not re.fullmatch(r"sha256:[0-9a-f]{64}", self.schema_content_id):
            raise FeatureSchemaError("PFS2_SCHEMA", "schema_content_id", "sha256_required")
        if self.schema_content_id != physical_feature_schema_content_id(self):
            raise FeatureSchemaError("PFS2_SCHEMA", "schema_content_id", "digest_mismatch")
        object.__setattr__(self, "features", items)

    def to_dict(self, *, include_content_id: bool = True) -> dict[str, Any]:
        result = {"schema_id": self.schema_id, "version": self.version, "schema_version": self.schema_version,
                  "features": [{field.name: getattr(feature, field.name) for field in fields(FeatureDefinition)} for feature in self.features]}
        if include_content_id: result["schema_content_id"] = self.schema_content_id
        return result


def canonical_physical_feature_schema_bytes(schema: FeatureSchema) -> bytes:
    return _canonical_schema_bytes(schema.schema_id, schema.version, schema.features)


def _canonical_schema_bytes(schema_id: str, version: str, features: tuple[FeatureDefinition, ...]) -> bytes:
    payload = {"schema_id": schema_id, "version": version, "schema_version": PHYSICAL_FEATURE_SCHEMA_VERSION,
               "features": [{field.name: getattr(feature, field.name) for field in fields(FeatureDefinition)} for feature in features]}
    return json.dumps(payload, ensure_ascii=True, sort_keys=True,
                      separators=(",", ":"), allow_nan=False).encode("ascii")


def physical_feature_schema_content_id(schema: FeatureSchema) -> str:
    return "sha256:" + hashlib.sha256(canonical_physical_feature_schema_bytes(schema)).hexdigest()


def register_physical_feature_schema(*, schema_id: str, version: str,
                                     features: tuple[FeatureDefinition, ...]) -> FeatureSchema:
    """Create the immutable v2 schema identity from its complete declaration."""
    content_id = "sha256:" + hashlib.sha256(_canonical_schema_bytes(schema_id, version, tuple(features))).hexdigest()
    return FeatureSchema(schema_id, version, tuple(features), content_id)


def validate_physical_feature_schema(schema: object, *, immutable_resolver: Callable[[str], bool]) -> FeatureSchema:
    if not isinstance(schema, FeatureSchema):
        raise FeatureSchemaError("PFS2_SCHEMA", "schema", "feature_schema_required")
    for feature in schema.features:
        for reference in (*feature.compatible_profile_ids, *feature.parameter_evidence_references, feature.preprocessing_id):
            if not immutable_resolver(reference):
                raise FeatureSchemaError("PFS2_AUTHORITY", "feature.references", "unresolved_immutable_reference")
    return schema


@dataclass(frozen=True)
class OperatingContextValue:
    name: str
    value: str | None
    data_type: str
    unit: str
    experiment_specification_id: str
    parameter_evidence_references: tuple[str, ...]
    availability: str = "available"

    def __post_init__(self) -> None:
        _token(self.name, "operating_context.name"); _safe(self.name, "operating_context.name")
        if self.data_type not in _DATA_TYPES or not isinstance(self.unit, str) or not self.unit:
            raise FeatureSchemaError("PFS2_CONTEXT", "operating_context", "declared_type_and_unit_required")
        _immutable(self.experiment_specification_id, "operating_context.experiment_specification_id")
        refs = tuple(self.parameter_evidence_references)
        if not refs: raise FeatureSchemaError("PFS2_AUTHORITY", "operating_context.parameter_evidence_references", "nonempty_required")
        for reference in refs: _immutable(reference, "operating_context.parameter_evidence_references")
        if refs != tuple(sorted(set(refs))): raise FeatureSchemaError("PFS2_CANONICAL", "operating_context.references", "ordered_unique_required")
        if self.availability not in {"available", "unavailable"} or (self.availability == "available") != (self.value is not None):
            raise FeatureSchemaError("PFS2_CONTEXT", "operating_context.availability", "value_state_mismatch")
        object.__setattr__(self, "parameter_evidence_references", refs)


@dataclass(frozen=True)
class FeatureValue:
    name: str
    value: Any | None
    availability: str
    source_field: str
    representation: str
    unit: str
    data_type: str


@dataclass(frozen=True)
class PhysicalFeatureRow:
    schema_content_id: str
    observation_content_id: str
    values: tuple[FeatureValue, ...]
    preprocessing_ids: tuple[str, ...]

    def tensor(self, *, frozen_preprocessor_id: str, transform: Callable[[FeatureValue], float]) -> tuple[float, ...]:
        """Apply only an injected exact frozen preprocessor; no default encoding."""
        _immutable(frozen_preprocessor_id, "frozen_preprocessor_id")
        if set(self.preprocessing_ids) != {frozen_preprocessor_id}:
            raise FeatureSchemaError("PFS2_PREPROCESSING", "frozen_preprocessor_id", "schema_preprocessing_mismatch")
        if not callable(transform): raise FeatureSchemaError("PFS2_PREPROCESSING", "transform", "callable_required")
        output = []
        for value in self.values:
            if value.availability != "available":
                raise FeatureSchemaError("PFS2_MISSINGNESS", value.name, "tensor_has_unavailable_feature")
            result = transform(value)
            if type(result) not in {int, float} or isinstance(result, bool):
                raise FeatureSchemaError("PFS2_PREPROCESSING", value.name, "numeric_output_required")
            output.append(float(result))
        return tuple(output)


def _value_at(payload: Mapping[str, Any], path: str) -> Any:
    value: Any = payload
    for part in path.split("."):
        if not isinstance(value, Mapping) or part not in value:
            raise FeatureSchemaError("PFS2_SOURCE", path, "canonical_source_missing")
        value = value[part]
    return value


def _profile_closure_ids(profile_binding: Mapping[str, Any]) -> tuple[str, ...]:
    """Return only identities already declared by the canonical observation."""
    values = [profile_binding["profile_id"], profile_binding["profile_canonical_bytes_hash"],
              profile_binding["catalog_snapshot_hash"]]
    for name in ("profile_revision_ref", "catalog_snapshot_ref", "parameter_gate_result_ref"):
        reference = profile_binding[name]
        values.extend((reference["revision_id"], reference["serialized_sha256"]))
        if reference["subject_sha256"] is not None: values.append(reference["subject_sha256"])
    for use in profile_binding["consumed_parameters"]:
        values.append(use["target_bytes_hash"])
        values.extend((use["target_revision_ref"]["revision_id"], use["target_revision_ref"]["serialized_sha256"]))
    return tuple(values)


def build_physical_features(observation: SignalObservation, schema: FeatureSchema, *,
                            immutable_resolver: Callable[[str], bool],
                            operating_context: Mapping[str, OperatingContextValue] | None = None) -> PhysicalFeatureRow:
    """Project canonical observation fields only; it never recalculates conversions."""
    if not isinstance(observation, SignalObservation):
        raise FeatureSchemaError("PFS2_OBSERVATION", "observation", "signal_observation_v2_required")
    validate_physical_feature_schema(schema, immutable_resolver=immutable_resolver)
    payload = observation.to_dict(); profile_id = payload["profile_binding"]["profile_id"]
    if any(not immutable_resolver(value) for value in _profile_closure_ids(payload["profile_binding"])):
        raise FeatureSchemaError("PFS2_AUTHORITY", "observation.profile_binding", "profile_closure_unresolved")
    context = dict(operating_context or {})
    values: list[FeatureValue] = []
    for feature in schema.features:
        if feature.availability != "available":
            values.append(FeatureValue(feature.name, None, feature.availability, feature.source_field, feature.representation, feature.unit, feature.data_type)); continue
        if feature.representation != "operating_context" and profile_id not in feature.compatible_profile_ids:
            raise FeatureSchemaError("PFS2_PROFILE", feature.name, "profile_incompatible")
        if feature.representation == "operating_context":
            key = feature.source_field.split(".", 1)[1]; supplied = context.get(key)
            if supplied is None or supplied.name != key:
                raise FeatureSchemaError("PFS2_CONTEXT", feature.name, "declared_context_missing")
            if not immutable_resolver(supplied.experiment_specification_id) or any(not immutable_resolver(ref) for ref in supplied.parameter_evidence_references):
                raise FeatureSchemaError("PFS2_AUTHORITY", feature.name, "context_authority_unresolved")
            if supplied.data_type != feature.data_type or supplied.unit != feature.unit:
                raise FeatureSchemaError("PFS2_CONTEXT", feature.name, "context_type_or_unit_mismatch")
            raw, availability = supplied.value, supplied.availability
        else:
            raw = _value_at(payload, feature.source_field)
            state = payload[feature.representation].get("state") if feature.representation in {"raw_current", "normalized_span", "engineering_value"} else None
            availability = "available" if state in {None, "present", "derived"} else "unavailable"
            if feature.source_field == "diagnostics": raw = tuple(raw)
        if availability != "available" and feature.missingness_policy == "forbid":
            raise FeatureSchemaError("PFS2_MISSINGNESS", feature.name, "required_feature_unavailable")
        values.append(FeatureValue(feature.name, raw if availability == "available" else None, availability, feature.source_field, feature.representation, feature.unit, feature.data_type))
    return PhysicalFeatureRow(schema.schema_content_id, payload["observation_content_id"], tuple(values),
                              tuple(feature.preprocessing_id for feature in schema.features))
