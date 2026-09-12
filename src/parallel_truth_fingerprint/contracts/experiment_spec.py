"""Offline, immutable ``ExperimentSpec.v1`` planning contract.

The contract deliberately describes a frozen proposal only.  It has no clock,
I/O, runner, command emitter, or authorization side effect.
"""
from __future__ import annotations

import hashlib
import json
import re
from dataclasses import dataclass
from enum import StrEnum
from types import MappingProxyType
from typing import Any, Callable, Mapping


EXPERIMENT_SPEC_SCHEMA_VERSION = "experiment-spec.v1"
_DIGEST = re.compile(r"sha256:[0-9a-f]{64}\Z")
_FIELDS = frozenset({
    "schema_version", "experiment_id", "run_bindings", "stimulus_identity",
    "phases", "schedule_descriptors", "expected_streams", "policy_references",
    "reference_factor_binding", "applicability", "limitations", "content_sha256",
    "authorization_effect",
})


class BindingDisposition(StrEnum):
    BOUND = "bound"
    NOT_APPLICABLE = "not_applicable"
    UNAVAILABLE_BLOCKING = "unavailable_blocking"


class FreezeState(StrEnum):
    STRUCTURALLY_FROZEN = "structurally_frozen"
    EXECUTION_ELIGIBLE = "execution_eligible"
    BLOCKED = "blocked"


@dataclass(frozen=True)
class ExperimentSpecViolation:
    rule_id: str
    field: str
    token: str

    def to_dict(self) -> dict[str, str]:
        return {"rule_id": self.rule_id, "field": self.field, "token": self.token}


class ExperimentSpecError(ValueError):
    def __init__(self, rule_id: str, field: str, token: str) -> None:
        self.violation = ExperimentSpecViolation(rule_id, field, token)
        super().__init__(f"{rule_id}:{field}:{token}")


def _freeze(value: Any) -> Any:
    if isinstance(value, Mapping): return MappingProxyType({str(k): _freeze(v) for k, v in value.items()})
    if isinstance(value, list): return tuple(_freeze(v) for v in value)
    if isinstance(value, tuple): return tuple(_freeze(v) for v in value)
    return value


def _thaw(value: Any) -> Any:
    if isinstance(value, Mapping): return {k: _thaw(v) for k, v in value.items()}
    if isinstance(value, tuple): return [_thaw(v) for v in value]
    return value


def canonical_experiment_spec_bytes(payload: Mapping[str, Any]) -> bytes:
    """Canonical ASCII preimage; the self-referential content hash is omitted."""
    preimage = _thaw(payload)
    preimage.pop("content_sha256", None)
    return json.dumps(preimage, sort_keys=True, ensure_ascii=True, separators=(",", ":"), allow_nan=False).encode("ascii")


def experiment_spec_content_id(payload: Mapping[str, Any]) -> str:
    return "sha256:" + hashlib.sha256(canonical_experiment_spec_bytes(payload)).hexdigest()


def _id(value: Any, field: str) -> None:
    if not isinstance(value, str) or not _DIGEST.fullmatch(value):
        raise ExperimentSpecError("ESV1_IMMUTABLE_REFERENCE", field, "sha256_identity_required")


def _closed_object(value: Any, fields: set[str], field: str) -> Mapping[str, Any]:
    if not isinstance(value, Mapping) or set(value) != fields:
        raise ExperimentSpecError("ESV1_CLOSED_SCHEMA", field, "exact_fields_required")
    return value


def _slot(value: Any, field: str) -> Mapping[str, Any]:
    item = _closed_object(value, {"slot_id", "disposition", "reference", "rationale"}, field)
    if not isinstance(item["slot_id"], str) or not item["slot_id"] or item["disposition"] not in set(BindingDisposition):
        raise ExperimentSpecError("ESV1_SLOT", field, "closed_disposition_required")
    if not isinstance(item["rationale"], str) or not item["rationale"]: raise ExperimentSpecError("ESV1_SLOT", field, "rationale_required")
    if item["disposition"] == BindingDisposition.BOUND:
        _id(item["reference"], f"{field}.reference")
    elif item["reference"] is not None:
        raise ExperimentSpecError("ESV1_SLOT", field, "unbound_reference_forbidden")
    return item


def _validate(payload: Mapping[str, Any], *, verify_hash: bool) -> None:
    if set(payload) != _FIELDS: raise ExperimentSpecError("ESV1_CLOSED_SCHEMA", "record", "exact_top_level_fields_required")
    if payload["schema_version"] != EXPERIMENT_SPEC_SCHEMA_VERSION: raise ExperimentSpecError("ESV1_SCHEMA_VERSION", "schema_version", "experiment_spec_v1_required")
    _id(payload["experiment_id"], "experiment_id")
    if payload["authorization_effect"] != "none": raise ExperimentSpecError("ESV1_AUTHORIZATION", "authorization_effect", "none_required")
    if not isinstance(payload["limitations"], list) or not payload["limitations"] or not all(isinstance(x, str) and x for x in payload["limitations"]): raise ExperimentSpecError("ESV1_LIMITATIONS", "limitations", "nonempty_required")
    if not isinstance(payload["applicability"], Mapping): raise ExperimentSpecError("ESV1_APPLICABILITY", "applicability", "object_required")
    app = _closed_object(payload["applicability"], {"evidence_role", "scope", "synchronization", "disposition"}, "applicability")
    if app["disposition"] not in set(BindingDisposition) or not all(isinstance(app[k], str) and app[k] for k in ("evidence_role", "scope", "synchronization")): raise ExperimentSpecError("ESV1_APPLICABILITY", "applicability", "explicit_disposition_required")
    if not isinstance(payload["run_bindings"], list) or not payload["run_bindings"]: raise ExperimentSpecError("ESV1_RUN_BINDING", "run_bindings", "predeclared_bindings_required")
    seen = set()
    for i, binding in enumerate(payload["run_bindings"]):
        b = _closed_object(binding, {"run_binding_id", "phase_id", "scenario_ref", "intervention_ref", "recovery_ref", "planned_disposition", "allowed_outcome_policy_ref"}, f"run_bindings[{i}]")
        if not isinstance(b["run_binding_id"], str) or not b["run_binding_id"] or b["run_binding_id"] in seen or b["planned_disposition"] != "planned": raise ExperimentSpecError("ESV1_RUN_BINDING", f"run_bindings[{i}]", "stable_planned_binding_required")
        seen.add(b["run_binding_id"])
        for name in ("scenario_ref", "intervention_ref", "recovery_ref", "allowed_outcome_policy_ref"): _id(b[name], f"run_bindings[{i}].{name}")
    stimulus = _closed_object(payload["stimulus_identity"], {"kind", "input_trace_ref", "seed_ref", "rng_ref", "code_ref", "runtime_ref"}, "stimulus_identity")
    if stimulus["kind"] != "input_trace" or not all(stimulus[k] is None for k in ("seed_ref", "rng_ref", "code_ref", "runtime_ref")): raise ExperimentSpecError("ESV1_STIMULUS", "stimulus_identity", "input_trace_only_required")
    _id(stimulus["input_trace_ref"], "stimulus_identity.input_trace_ref")
    for name in ("phases", "policy_references"):
        if not isinstance(payload[name], list) or not payload[name]: raise ExperimentSpecError("ESV1_REQUIRED_REFERENCE", name, "nonempty_required")
        for i, item in enumerate(payload[name]): _slot(item, f"{name}[{i}]")
    if not isinstance(payload["schedule_descriptors"], list): raise ExperimentSpecError("ESV1_SCHEDULE", "schedule_descriptors", "list_required")
    for i, item in enumerate(payload["schedule_descriptors"]):
        d = _closed_object(item, {"descriptor_id", "numeric_loci", "opaque_descriptor_ref"}, f"schedule_descriptors[{i}]")
        if not isinstance(d["descriptor_id"], str) or not d["descriptor_id"] or not isinstance(d["numeric_loci"], list): raise ExperimentSpecError("ESV1_SCHEDULE", f"schedule_descriptors[{i}]", "closed_descriptor_required")
        _id(d["opaque_descriptor_ref"], f"schedule_descriptors[{i}].opaque_descriptor_ref")
        for j, locus in enumerate(d["numeric_loci"]): _slot(locus, f"schedule_descriptors[{i}].numeric_loci[{j}]")
    if not isinstance(payload["expected_streams"], list) or not payload["expected_streams"]: raise ExperimentSpecError("ESV1_STREAM", "expected_streams", "nonempty_required")
    for i, item in enumerate(payload["expected_streams"]):
        stream = _closed_object(item, {"stream_id", "schema_ref", "audience_ref", "profile_ref"}, f"expected_streams[{i}]")
        if not isinstance(stream["stream_id"], str) or not stream["stream_id"]: raise ExperimentSpecError("ESV1_STREAM", f"expected_streams[{i}]", "identity_required")
        for name in ("schema_ref", "audience_ref", "profile_ref"): _id(stream[name], f"expected_streams[{i}].{name}")
    factor = _closed_object(payload["reference_factor_binding"], {"factor_name", "decision_ref", "low_factor_parameter_ref", "high_factor_parameter_ref", "command_profile_ref", "low_profile_parameter_ref", "high_profile_parameter_ref", "low_current_parameter_ref", "high_current_parameter_ref", "prohibited_meanings"}, "reference_factor_binding")
    if factor["factor_name"] != "speed_reference_pct": raise ExperimentSpecError("ESV1_REFERENCE_FACTOR", "reference_factor_binding.factor_name", "speed_reference_pct_required")
    if not isinstance(factor["prohibited_meanings"], list) or not {"electrical_power", "manufacturer_recommendation", "universal_compressor_range", "safety_limit", "efficiency_limit"}.issubset(factor["prohibited_meanings"]): raise ExperimentSpecError("ESV1_REFERENCE_FACTOR", "reference_factor_binding.prohibited_meanings", "required_prohibitions_missing")
    for name in set(factor) - {"factor_name", "prohibited_meanings"}: _id(factor[name], f"reference_factor_binding.{name}")
    if not isinstance(payload["content_sha256"], str) or not _DIGEST.fullmatch(payload["content_sha256"]): raise ExperimentSpecError("ESV1_CONTENT_ID", "content_sha256", "sha256_required")
    if verify_hash and payload["content_sha256"] != experiment_spec_content_id(payload): raise ExperimentSpecError("ESV1_CONTENT_ID", "content_sha256", "digest_mismatch")


@dataclass(frozen=True)
class ExperimentSpec:
    payload: Mapping[str, Any]
    def __post_init__(self) -> None:
        _validate(self.payload, verify_hash=True)
        object.__setattr__(self, "payload", _freeze(_thaw(self.payload)))
    def to_dict(self) -> dict[str, Any]: return _thaw(self.payload)
    def canonical_bytes(self) -> bytes: return canonical_experiment_spec_bytes(self.payload)


def parse_experiment_spec(payload: object) -> ExperimentSpec:
    if not isinstance(payload, Mapping): raise ExperimentSpecError("ESV1_CLOSED_SCHEMA", "record", "object_required")
    return ExperimentSpec(dict(payload))


def parse_experiment_spec_json(raw: str | bytes) -> ExperimentSpec:
    def no_duplicates(pairs: list[tuple[str, Any]]) -> dict[str, Any]:
        result: dict[str, Any] = {}
        for key, value in pairs:
            if key in result: raise ExperimentSpecError("ESV1_CLOSED_SCHEMA", key, "duplicate_field")
            result[key] = value
        return result
    try: return parse_experiment_spec(json.loads(raw, object_pairs_hook=no_duplicates, parse_constant=lambda _: (_ for _ in ()).throw(ValueError())))
    except ExperimentSpecError: raise
    except (TypeError, ValueError, json.JSONDecodeError) as exc: raise ExperimentSpecError("ESV1_CLOSED_SCHEMA", "record", "strict_json_required") from exc


@dataclass(frozen=True)
class ExperimentValidationResult:
    content_sha256: str
    freeze_state: FreezeState
    execution_eligible: bool
    violations: tuple[ExperimentSpecViolation, ...]
    authorization_effect: str = "none"


class ExperimentSpecValidator:
    """Pure resolver boundary; resolvers answer immutable-reference admission only."""
    def __init__(self, resolver: Callable[[str], bool]) -> None: self._resolver = resolver
    def validate(self, spec: ExperimentSpec) -> ExperimentValidationResult:
        refs: list[str] = []
        blocking_slots: list[Mapping[str, Any]] = []
        def walk(value: Any) -> None:
            if isinstance(value, Mapping):
                if value.get("disposition") == BindingDisposition.UNAVAILABLE_BLOCKING:
                    blocking_slots.append(value)
                for key, item in value.items():
                    if key.endswith("_ref") and isinstance(item, str): refs.append(item)
                    walk(item)
            elif isinstance(value, tuple) or isinstance(value, list):
                for item in value: walk(item)
        walk(spec.payload)
        violations = tuple(ExperimentSpecViolation("ESV1_RESOLUTION", "reference", ref) for ref in sorted(set(refs)) if not self._resolver(ref))
        blocked = bool(blocking_slots)
        eligible = not violations and not blocked and spec.payload["applicability"]["disposition"] == BindingDisposition.BOUND
        return ExperimentValidationResult(spec.payload["content_sha256"], FreezeState.EXECUTION_ELIGIBLE if eligible else (FreezeState.STRUCTURALLY_FROZEN if not violations else FreezeState.BLOCKED), eligible, violations)


@dataclass(frozen=True)
class ExperimentMatrixRow:
    run_binding_id: str
    row_content_sha256: str
    phase_id: str
    scenario_ref: str
    intervention_ref: str
    recovery_ref: str
    planned_disposition: str
    allowed_outcome_policy_ref: str
    authorization_effect: str = "none"


def project_experiment_matrix(spec: ExperimentSpec) -> tuple[ExperimentMatrixRow, ...]:
    """Return ordered declaration rows; never outcomes, execution IDs, or commands."""
    rows = []
    for binding in spec.payload["run_bindings"]:
        raw = json.dumps(_thaw(binding), sort_keys=True, ensure_ascii=True, separators=(",", ":")).encode("ascii")
        rows.append(ExperimentMatrixRow(binding["run_binding_id"], "sha256:" + hashlib.sha256(raw).hexdigest(), binding["phase_id"], binding["scenario_ref"], binding["intervention_ref"], binding["recovery_ref"], binding["planned_disposition"], binding["allowed_outcome_policy_ref"]))
    return tuple(rows)
