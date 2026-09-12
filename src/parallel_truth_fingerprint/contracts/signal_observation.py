"""Strict, offline ``SignalObservation.v2`` wire contract.

This module deliberately owns only record-level syntax, canonical bytes and
content identity.  It neither reads a device nor performs a conversion.
"""
from __future__ import annotations

import hashlib
import json
import re
from dataclasses import dataclass
from decimal import Decimal, InvalidOperation
from types import MappingProxyType
from typing import Any, Mapping

from parallel_truth_fingerprint.contracts.scientific_governance import is_immutable_id

CONTRACT_ID = "SignalObservation"
SCHEMA_VERSION = 2
RECORD_ROLE = "primary_per_edge"
_DIGEST = re.compile(r"sha256:[0-9a-f]{64}\Z")
_DECIMAL = re.compile(r"-?(?:0|[1-9][0-9]*)(?:\.[0-9]+)?\Z")
_CANONICAL_UTC = re.compile(r"\d{4}-\d{2}-\d{2}T\d{2}:\d{2}:\d{2}\.\d{6}Z\Z")
_IDENTITY_FIELDS = ("experiment_id", "run_id", "round_id", "edge_id", "sensor_id", "source_stream_id", "source_boot_id", "source_session_id", "event_id")
_FIELDS = {"contract_id", "schema_version", "schema_ref", "record_role", "audience_access_class", "semantic_identity", *_IDENTITY_FIELDS, "source_sequence", "correlation", "source_timestamp", "observed_timestamp", "clock", "profile_binding", "raw_current", "diagnostics", "quality_trace", "normalized_span", "engineering_value", "observation_content_id"}


@dataclass(frozen=True)
class SignalObservationViolation:
    family: str
    field: str
    token: str

    def to_dict(self) -> dict[str, str]:
        return {"family": self.family, "field": self.field, "token": self.token}


class SignalObservationError(ValueError):
    """Raised for a fail-closed parse/validation error.

    ``violation`` is stable machine-readable diagnostic data; callers must not
    branch on this exception's prose.
    """
    def __init__(self, family: str, field: str, token: str) -> None:
        self.violation = SignalObservationViolation(family, field, token)
        super().__init__(f"{family}:{field}:{token}")


def _freeze(value: Any) -> Any:
    if isinstance(value, Mapping):
        return MappingProxyType({str(k): _freeze(v) for k, v in value.items()})
    if isinstance(value, list):
        return tuple(_freeze(v) for v in value)
    return value


def _thaw(value: Any) -> Any:
    if isinstance(value, Mapping):
        return {str(k): _thaw(v) for k, v in value.items()}
    if isinstance(value, tuple):
        return [_thaw(v) for v in value]
    return value


def canonical_decimal(value: object) -> str:
    """Accept one non-exponent, finite, non-negative-zero decimal spelling."""
    if not isinstance(value, str) or not _DECIMAL.fullmatch(value):
        raise SignalObservationError("SOV2_RAW_CURRENT_PRIMARY", "value", "canonical_decimal_required")
    try:
        decimal = Decimal(value)
    except InvalidOperation as exc:  # pragma: no cover - regex already excludes it
        raise SignalObservationError("SOV2_RAW_CURRENT_PRIMARY", "value", "canonical_decimal_required") from exc
    if not decimal.is_finite() or (decimal.is_zero() and value.startswith("-")):
        raise SignalObservationError("SOV2_RAW_CURRENT_PRIMARY", "value", "noncanonical_decimal")
    return value


def _object(value: object, fields: set[str], field: str, family: str) -> Mapping[str, Any]:
    if not isinstance(value, Mapping) or set(value) != fields:
        raise SignalObservationError(family, field, "closed_fields_required")
    return value


def _opaque_id(value: object, field: str, family: str = "SOV2_IDENTITY") -> str:
    if not isinstance(value, str) or not value or not is_immutable_id(value):
        raise SignalObservationError(family, field, "resolved_immutable_id_required")
    return value


def _reference(value: object, field: str) -> Mapping[str, Any]:
    ref = _object(value, {"revision_id", "serialized_sha256", "subject_sha256", "contract_id", "contract_version", "locator", "evidence_role"}, field, "SOV2_PROFILE_REFERENCE")
    for name in ("revision_id", "serialized_sha256"):
        _opaque_id(ref[name], f"{field}.{name}", "SOV2_PROFILE_REFERENCE")
    if ref["subject_sha256"] is not None:
        _opaque_id(ref["subject_sha256"], f"{field}.subject_sha256", "SOV2_PROFILE_REFERENCE")
    if any(not isinstance(ref[name], str) or not ref[name] for name in ("contract_id", "contract_version", "locator", "evidence_role")):
        raise SignalObservationError("SOV2_PROFILE_REFERENCE", field, "immutable_reference_required")
    return ref


def _parameter_uses(value: object, field: str) -> tuple[Mapping[str, Any], ...]:
    if not isinstance(value, (list, tuple)) or not value:
        raise SignalObservationError("SOV2_PARAMETER_CLOSURE", field, "nonempty_array_required")
    parsed = []
    for item in value:
        use = _object(item, {"role", "target_revision_ref", "target_bytes_hash"}, field, "SOV2_PARAMETER_CLOSURE")
        if not isinstance(use["role"], str) or not use["role"]:
            raise SignalObservationError("SOV2_PARAMETER_CLOSURE", field, "role_required")
        _reference(use["target_revision_ref"], f"{field}.target_revision_ref")
        _opaque_id(use["target_bytes_hash"], f"{field}.target_bytes_hash", "SOV2_PARAMETER_CLOSURE")
        parsed.append(use)
    keys = [(x["role"], x["target_revision_ref"]["revision_id"], x["target_bytes_hash"]) for x in parsed]
    if keys != sorted(keys) or len(set(keys)) != len(keys):
        raise SignalObservationError("SOV2_PARAMETER_CLOSURE", field, "canonical_unique_order_required")
    return tuple(parsed)


def _raw(value: object) -> None:
    if not isinstance(value, Mapping) or value.get("state") not in {"present", "missing"}:
        raise SignalObservationError("SOV2_RAW_CURRENT_PRIMARY", "raw_current", "closed_variant_required")
    expected = {"state", "unit", "value"} if value["state"] == "present" else {"state", "unit", "reason"}
    _object(value, expected, "raw_current", "SOV2_RAW_CURRENT_PRIMARY")
    if value["unit"] != "mA":
        raise SignalObservationError("SOV2_UNIT_QUANTITY", "raw_current.unit", "ma_required")
    if value["state"] == "present": canonical_decimal(value["value"])
    elif not isinstance(value["reason"], str) or not value["reason"]:
        raise SignalObservationError("SOV2_RAW_CURRENT_PRIMARY", "raw_current.reason", "closed_reason_required")


def _representation(value: object, field: str, quantity: str, unit: str | None) -> None:
    if not isinstance(value, Mapping) or value.get("state") not in {"derived", "not_derived"}:
        raise SignalObservationError("SOV2_REPRESENTATION_RECOMPUTE", field, "closed_variant_required")
    expected = {"state", "value", "quantity_kind", "unit", "derivation"} if value["state"] == "derived" else {"state", "quantity_kind", "unit", "reason"}
    _object(value, expected, field, "SOV2_REPRESENTATION_RECOMPUTE")
    if value["quantity_kind"] != quantity or (unit is not None and value["unit"] != unit):
        raise SignalObservationError("SOV2_UNIT_QUANTITY", field, "profile_quantity_unit_required")
    if value["state"] == "derived":
        canonical_decimal(value["value"])
        derivation = _object(value["derivation"], {"direction", "transform_revision_ref", "profile_revision_ref", "input_representation", "output_representation", "parameter_uses"}, f"{field}.derivation", "SOV2_REPRESENTATION_RECOMPUTE")
        _reference(derivation["transform_revision_ref"], f"{field}.derivation.transform_revision_ref")
        _reference(derivation["profile_revision_ref"], f"{field}.derivation.profile_revision_ref")
        _parameter_uses(derivation["parameter_uses"], f"{field}.derivation.parameter_uses")
    elif not isinstance(value["reason"], str) or not value["reason"]:
        raise SignalObservationError("SOV2_REPRESENTATION_RECOMPUTE", field, "closed_reason_required")


def _trace(value: object) -> str:
    trace = _object(value, {"outcome", "conversion_disposition", "applied_rule_ids", "diagnostic_ids_used", "parameter_uses"}, "quality_trace", "SOV2_QUALITY_RECOMPUTE")
    if trace["outcome"] not in {"in_range", "under_range", "over_range", "missing", "uncertain", "fault"} or trace["conversion_disposition"] not in {"convert", "no_numeric_value"}:
        raise SignalObservationError("SOV2_QUALITY_RECOMPUTE", "quality_trace", "unknown_quality_token")
    for name in ("applied_rule_ids", "diagnostic_ids_used"):
        if not isinstance(trace[name], (list, tuple)) or any(not isinstance(x, str) or not x for x in trace[name]) or len(set(trace[name])) != len(trace[name]):
            raise SignalObservationError("SOV2_QUALITY_RECOMPUTE", f"quality_trace.{name}", "ordered_unique_ids_required")
    _parameter_uses(trace["parameter_uses"], "quality_trace.parameter_uses")
    return str(trace["conversion_disposition"])


def _diagnostics(value: object) -> None:
    if not isinstance(value, (list, tuple)):
        raise SignalObservationError("SOV2_QUALITY_RECOMPUTE", "diagnostics", "array_required")
    ids: list[str] = []
    for item in value:
        if not isinstance(item, Mapping) or item.get("value_state") not in {"present", "missing"}:
            raise SignalObservationError("SOV2_QUALITY_RECOMPUTE", "diagnostics", "closed_variant_required")
        expected = {"diagnostic_id", "value_state", "value_type", "unit_binding", "value"} if item["value_state"] == "present" else {"diagnostic_id", "value_state", "value_type", "unit_binding", "reason"}
        _object(item, expected, "diagnostics", "SOV2_QUALITY_RECOMPUTE")
        if item["value_type"] not in {"boolean", "canonical_decimal", "canonical_integer", "closed_token"} or not isinstance(item["diagnostic_id"], str):
            raise SignalObservationError("SOV2_QUALITY_RECOMPUTE", "diagnostics", "diagnostic_token_required")
        ids.append(item["diagnostic_id"])
        if item["value_state"] == "present":
            v = item["value"]
            if item["value_type"] == "canonical_decimal": canonical_decimal(v)
            elif item["value_type"] == "canonical_integer" and (type(v) is not int or v < 0): raise SignalObservationError("SOV2_QUALITY_RECOMPUTE", "diagnostics.value", "canonical_integer_required")
            elif item["value_type"] == "boolean" and type(v) is not bool: raise SignalObservationError("SOV2_QUALITY_RECOMPUTE", "diagnostics.value", "boolean_required")
            elif item["value_type"] == "closed_token" and (not isinstance(v, str) or not v): raise SignalObservationError("SOV2_QUALITY_RECOMPUTE", "diagnostics.value", "closed_token_required")
    if ids != sorted(ids) or len(set(ids)) != len(ids):
        raise SignalObservationError("SOV2_QUALITY_RECOMPUTE", "diagnostics", "canonical_unique_order_required")


def _reference_slot(value: object, field: str, family: str) -> bool:
    if not isinstance(value, Mapping) or value.get("state") not in {"present", "unavailable"}:
        raise SignalObservationError(family, field, "closed_slot_required")
    if value["state"] == "present":
        _object(value, {"state", "reference"}, field, family); _reference(value["reference"], f"{field}.reference")
        return True
    _object(value, {"state", "reason"}, field, family)
    if not isinstance(value["reason"], str) or not value["reason"]: raise SignalObservationError(family, field, "closed_reason_required")
    return False


def _measurement_slot(value: object, field: str, family: str) -> bool:
    if not isinstance(value, Mapping) or value.get("state") not in {"present", "unavailable"}:
        raise SignalObservationError(family, field, "closed_slot_required")
    if value["state"] == "present":
        _object(value, {"state", "value", "unit", "evidence_ref"}, field, family)
        canonical_decimal(value["value"]); _reference(value["evidence_ref"], f"{field}.evidence_ref")
        if not isinstance(value["unit"], str) or not value["unit"]: raise SignalObservationError(family, field, "unit_required")
        return True
    _object(value, {"state", "reason"}, field, family)
    if not isinstance(value["reason"], str) or not value["reason"]: raise SignalObservationError(family, field, "closed_reason_required")
    return False


def _correlation(value: object) -> None:
    item = _object(value, {"correlation_id", "evidence_state", "method", "measured_uncertainty"}, "correlation", "SOV2_CORRELATION_EVIDENCE")
    _opaque_id(item["correlation_id"], "correlation.correlation_id", "SOV2_CORRELATION_EVIDENCE")
    method_present = _reference_slot(item["method"], "correlation.method", "SOV2_CORRELATION_EVIDENCE")
    uncertainty = item["measured_uncertainty"]
    if not isinstance(uncertainty, Mapping) or uncertainty.get("state") not in {"present", "not_applicable", "unavailable"}: raise SignalObservationError("SOV2_CORRELATION_EVIDENCE", "correlation.measured_uncertainty", "closed_slot_required")
    if uncertainty["state"] == "present":
        _object(uncertainty, {"state", "value", "unit", "evidence_ref"}, "correlation.measured_uncertainty", "SOV2_CORRELATION_EVIDENCE"); canonical_decimal(uncertainty["value"]); _reference(uncertainty["evidence_ref"], "correlation.measured_uncertainty.evidence_ref")
    elif uncertainty["state"] == "not_applicable": _object(uncertainty, {"state", "policy_ref", "reason"}, "correlation.measured_uncertainty", "SOV2_CORRELATION_EVIDENCE"); _reference(uncertainty["policy_ref"], "correlation.measured_uncertainty.policy_ref")
    else: _object(uncertainty, {"state", "reason"}, "correlation.measured_uncertainty", "SOV2_CORRELATION_EVIDENCE")
    state = item["evidence_state"]
    if state not in {"evidence_present", "unresolved", "unknown"} or (state == "evidence_present" and (not method_present or uncertainty["state"] == "unavailable")) or (state == "unresolved" and (not method_present or uncertainty["state"] != "unavailable")) or (state == "unknown" and (method_present or uncertainty["state"] != "unavailable")):
        raise SignalObservationError("SOV2_CORRELATION_EVIDENCE", "correlation", "incompatible_evidence_state")


def _clock(value: object) -> None:
    item = _object(value, {"source_clock_id", "observed_clock_id", "evidence_status", "method", "measured_offset", "measured_uncertainty", "qualification_policy"}, "clock", "SOV2_TIMESTAMP_CLOCK")
    _opaque_id(item["source_clock_id"], "clock.source_clock_id", "SOV2_TIMESTAMP_CLOCK"); _opaque_id(item["observed_clock_id"], "clock.observed_clock_id", "SOV2_TIMESTAMP_CLOCK")
    method = _reference_slot(item["method"], "clock.method", "SOV2_TIMESTAMP_CLOCK")
    offset = _measurement_slot(item["measured_offset"], "clock.measured_offset", "SOV2_TIMESTAMP_CLOCK")
    uncertainty = _measurement_slot(item["measured_uncertainty"], "clock.measured_uncertainty", "SOV2_TIMESTAMP_CLOCK")
    policy = _reference_slot(item["qualification_policy"], "clock.qualification_policy", "SOV2_TIMESTAMP_CLOCK")
    status = item["evidence_status"]
    if status not in {"qualified", "unqualified", "unresolved", "unknown"} or (status in {"qualified", "unqualified"} and not (method and policy)) or (status == "unknown" and any((method, offset, uncertainty, policy))) or (status == "unresolved" and not method):
        raise SignalObservationError("SOV2_TIMESTAMP_CLOCK", "clock.evidence_status", "incompatible_clock_state")


def _profile_binding(value: object) -> None:
    item = _object(value, {"profile_id", "profile_revision_ref", "profile_canonical_bytes_hash", "catalog_snapshot_ref", "catalog_snapshot_hash", "parameter_gate_result_ref", "consumed_parameters"}, "profile_binding", "SOV2_PROFILE_REFERENCE")
    _opaque_id(item["profile_id"], "profile_binding.profile_id", "SOV2_PROFILE_REFERENCE")
    for field in ("profile_revision_ref", "catalog_snapshot_ref", "parameter_gate_result_ref"): _reference(item[field], f"profile_binding.{field}")
    for field in ("profile_canonical_bytes_hash", "catalog_snapshot_hash"): _opaque_id(item[field], f"profile_binding.{field}", "SOV2_PROFILE_REFERENCE")
    _parameter_uses(item["consumed_parameters"], "profile_binding.consumed_parameters")


def _validate(payload: Mapping[str, Any], *, content_id: bool) -> None:
    if set(payload) != _FIELDS:
        unknown = next(iter(set(payload).difference(_FIELDS)), "missing_field")
        raise SignalObservationError("SOV2_SCHEMA_VERSION_TOKEN", str(unknown), "closed_top_level_fields_required")
    if payload["contract_id"] != CONTRACT_ID or type(payload["schema_version"]) is not int or payload["schema_version"] != SCHEMA_VERSION:
        raise SignalObservationError("SOV2_SCHEMA_VERSION_TOKEN", "contract_id", "signal_observation_v2_required")
    _reference(payload["schema_ref"], "schema_ref")
    if payload["record_role"] != RECORD_ROLE: raise SignalObservationError("SOV2_RECORD_ROLE", "record_role", "primary_per_edge_required")
    if payload["audience_access_class"] != "detector_facing": raise SignalObservationError("SOV2_AUDIENCE_IDENTITY", "audience_access_class", "detector_facing_required")
    if not isinstance(payload["semantic_identity"], Mapping): raise SignalObservationError("SOV2_SEMANTIC_ROLE", "semantic_identity", "structured_identity_required")
    for key in _IDENTITY_FIELDS: _opaque_id(payload[key], key)
    if type(payload["source_sequence"]) is not int or payload["source_sequence"] <= 0: raise SignalObservationError("SOV2_SEQUENCE", "source_sequence", "positive_integer_required")
    for key in ("source_timestamp", "observed_timestamp"):
        if not isinstance(payload[key], str) or not _CANONICAL_UTC.fullmatch(payload[key]): raise SignalObservationError("SOV2_TIMESTAMP_CLOCK", key, "canonical_utc_required")
    _raw(payload["raw_current"]); _diagnostics(payload["diagnostics"])
    disposition = _trace(payload["quality_trace"])
    _representation(payload["normalized_span"], "normalized_span", "normalized_span", "one")
    if not isinstance(payload["engineering_value"], Mapping) or not isinstance(payload["engineering_value"].get("quantity_kind"), str) or not isinstance(payload["engineering_value"].get("unit"), str): raise SignalObservationError("SOV2_UNIT_QUANTITY", "engineering_value", "profile_quantity_unit_required")
    _representation(payload["engineering_value"], "engineering_value", payload["engineering_value"]["quantity_kind"], payload["engineering_value"]["unit"])
    if disposition == "convert" and (payload["normalized_span"]["state"] != "derived" or payload["engineering_value"]["state"] != "derived"): raise SignalObservationError("SOV2_REPRESENTATION_RECOMPUTE", "representation", "convert_requires_derived")
    if disposition == "no_numeric_value" and (payload["normalized_span"]["state"] != "not_derived" or payload["engineering_value"]["state"] != "not_derived"): raise SignalObservationError("SOV2_REPRESENTATION_RECOMPUTE", "representation", "no_numeric_value_requires_not_derived")
    _correlation(payload["correlation"]); _clock(payload["clock"]); _profile_binding(payload["profile_binding"])
    if not isinstance(payload["observation_content_id"], str) or not _DIGEST.fullmatch(payload["observation_content_id"]): raise SignalObservationError("SOV2_CONTENT_ID", "observation_content_id", "lowercase_sha256_required")
    if content_id and payload["observation_content_id"] != observation_content_id(payload): raise SignalObservationError("SOV2_CONTENT_ID", "observation_content_id", "digest_mismatch")


def canonical_signal_observation_bytes(payload: Mapping[str, Any]) -> bytes:
    """Canonical ASCII JSON of the acyclic preimage (content ID excluded)."""
    preimage = dict(_thaw(payload)); preimage.pop("observation_content_id", None)
    return json.dumps(preimage, ensure_ascii=True, sort_keys=True, separators=(",", ":"), allow_nan=False).encode("ascii")


def observation_content_id(payload: Mapping[str, Any]) -> str:
    return "sha256:" + hashlib.sha256(canonical_signal_observation_bytes(payload)).hexdigest()


@dataclass(frozen=True)
class SignalObservation:
    """Frozen v2 record; use :func:`parse_signal_observation` for untrusted input."""
    payload: Mapping[str, Any]
    authorization_effect: str = "none"

    def __post_init__(self) -> None:
        _validate(self.payload, content_id=True)
        if self.authorization_effect != "none": raise SignalObservationError("SOV2_AUTHORIZATION_EFFECT", "authorization_effect", "none_required")
        object.__setattr__(self, "payload", _freeze(_thaw(self.payload)))

    def to_dict(self) -> dict[str, Any]: return _thaw(self.payload)
    def canonical_bytes(self) -> bytes: return canonical_signal_observation_bytes(self.payload)
    @property
    def event_key(self) -> tuple[Any, ...]: return tuple(self.payload[x] for x in _IDENTITY_FIELDS[:-1]) + (self.payload["event_id"],)
    @property
    def sequence_key(self) -> tuple[Any, ...]: return tuple(self.payload[x] for x in _IDENTITY_FIELDS if x != "event_id") + (self.payload["source_sequence"],)


def parse_signal_observation(payload: object) -> SignalObservation:
    if not isinstance(payload, Mapping): raise SignalObservationError("SOV2_SCHEMA_VERSION_TOKEN", "record", "object_required")
    return SignalObservation(dict(payload))


def parse_signal_observation_json(raw: str | bytes) -> SignalObservation:
    def no_duplicates(pairs: list[tuple[str, Any]]) -> dict[str, Any]:
        result: dict[str, Any] = {}
        for key, value in pairs:
            if key in result: raise SignalObservationError("SOV2_SCHEMA_VERSION_TOKEN", key, "duplicate_field")
            result[key] = value
        return result
    try: payload = json.loads(raw, object_pairs_hook=no_duplicates, parse_constant=lambda _: (_ for _ in ()).throw(ValueError()))
    except SignalObservationError: raise
    except (TypeError, ValueError, json.JSONDecodeError) as exc: raise SignalObservationError("SOV2_SCHEMA_VERSION_TOKEN", "record", "strict_json_required") from exc
    return parse_signal_observation(payload)


def signal_observation_schema_projection(schema_ref: Mapping[str, Any]) -> Mapping[str, Any]:
    """Identity-addressed, non-alias schema projection for inspection."""
    _reference(schema_ref, "schema_ref")
    return MappingProxyType({"contract_id": CONTRACT_ID, "schema_version": SCHEMA_VERSION, "schema_ref": _freeze(_thaw(schema_ref)), "top_level_fields": tuple(sorted(_FIELDS)), "content_id_preimage_excludes": "observation_content_id"})
