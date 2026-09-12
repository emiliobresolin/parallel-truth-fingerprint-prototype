"""Strict, offline contracts for the non-executing consensus-v2 boundary.

This module deliberately describes evidence closure only.  It contains no
numeric comparison, ranking algorithm, transport, persistence, or authority
to activate a consensus result.
"""
from __future__ import annotations

import hashlib
import json
import re
from dataclasses import dataclass
from enum import StrEnum
from types import MappingProxyType
from typing import Any, Mapping

from parallel_truth_fingerprint.contracts.scientific_governance import is_immutable_id

CONSENSUS_V2_SCHEMA = "Consensus.v2"
_DIGEST = re.compile(r"sha256:[0-9a-f]{64}\Z")
_BASIS_KINDS = {"same_profile_raw_current", "dimensionless_profile_residual"}
_INPUT_FIELDS = {"schema_version", "experiment_id", "run_id", "round_id", "qualification_result_id", "comparison_basis", "quality_policy_ids", "parameter_ids", "observations", "input_content_id", "authorization_effect"}
_DECISION_FIELDS = {"schema_version", "round_input_id", "round_input_hash", "comparison_basis", "outcome", "participant_ids", "included_ids", "excluded", "ranking", "diagnostics", "decision_content_id", "authorization_effect"}


class ConsensusOutcomeV2(StrEnum):
    SUCCESS = "success"
    FAILURE = "failure"


class ConsensusV2Error(ValueError):
    """Fail-closed bounded diagnostic.  The code is suitable for assertions."""
    def __init__(self, code: str) -> None:
        self.code = code
        super().__init__(code)


def _opaque(value: object, code: str) -> str:
    if not isinstance(value, str) or not is_immutable_id(value):
        raise ConsensusV2Error(code)
    return value


def _closed(value: object, expected: set[str], code: str) -> Mapping[str, Any]:
    if not isinstance(value, Mapping) or set(value) != expected:
        raise ConsensusV2Error(code)
    return value


def _thaw(value: Any) -> Any:
    if isinstance(value, Mapping): return {str(k): _thaw(v) for k, v in value.items()}
    if isinstance(value, tuple): return [_thaw(v) for v in value]
    if isinstance(value, StrEnum): return value.value
    return value


def _freeze(value: Any) -> Any:
    if isinstance(value, Mapping): return MappingProxyType({str(k): _freeze(v) for k, v in value.items()})
    if isinstance(value, list): return tuple(_freeze(v) for v in value)
    return value


def _ordered_ids(value: object, code: str, *, nonempty: bool = False) -> tuple[str, ...]:
    if not isinstance(value, (list, tuple)) or (nonempty and not value): raise ConsensusV2Error(code)
    ids = tuple(_opaque(item, code) for item in value)
    if ids != tuple(sorted(ids)) or len(ids) != len(set(ids)): raise ConsensusV2Error(code)
    return ids


def _basis(value: object) -> Mapping[str, Any]:
    basis = _closed(value, {"basis_id", "schema_version", "canonical_bytes", "canonical_bytes_hash", "kind", "unit", "profile_ids", "uncertainty_parameter_ids"}, "CV2_BASIS_FIELDS")
    _opaque(basis["basis_id"], "CV2_BASIS_ID")
    if not isinstance(basis["schema_version"], str) or not basis["schema_version"] or not isinstance(basis["canonical_bytes"], str): raise ConsensusV2Error("CV2_BASIS_VERSION")
    try:
        canonical_bytes = basis["canonical_bytes"].encode("ascii")
    except UnicodeEncodeError as exc:
        raise ConsensusV2Error("CV2_BASIS_CANONICAL_BYTES") from exc
    expected = "sha256:" + hashlib.sha256(canonical_bytes).hexdigest()
    if basis["canonical_bytes_hash"] != expected: raise ConsensusV2Error("CV2_BASIS_HASH")
    kind, profiles, uncertainty = basis["kind"], _ordered_ids(basis["profile_ids"], "CV2_BASIS_PROFILE", nonempty=True), _ordered_ids(basis["uncertainty_parameter_ids"], "CV2_BASIS_UNCERTAINTY")
    if kind not in _BASIS_KINDS: raise ConsensusV2Error("CV2_BASIS_KIND")
    if kind == "same_profile_raw_current" and (basis["unit"] != "mA" or len(profiles) != 1 or uncertainty): raise ConsensusV2Error("CV2_RAW_CURRENT_CLOSURE")
    if kind == "dimensionless_profile_residual" and (basis["unit"] != "one" or len(profiles) < 2 or not uncertainty): raise ConsensusV2Error("CV2_RESIDUAL_CLOSURE")
    return basis


def _observation(value: object) -> Mapping[str, Any]:
    item = _closed(value, {"edge_id", "observation_id", "observation_canonical_hash", "profile_id", "source_sequence", "correlation_id", "raw_current_unit"}, "CV2_OBSERVATION_FIELDS")
    for name in ("edge_id", "observation_id", "profile_id", "correlation_id"): _opaque(item[name], "CV2_OBSERVATION_ID")
    if not isinstance(item["observation_canonical_hash"], str) or not _DIGEST.fullmatch(item["observation_canonical_hash"]): raise ConsensusV2Error("CV2_OBSERVATION_HASH")
    if type(item["source_sequence"]) is not int or item["source_sequence"] <= 0: raise ConsensusV2Error("CV2_SOURCE_SEQUENCE")
    if item["raw_current_unit"] != "mA": raise ConsensusV2Error("CV2_RAW_CURRENT_UNIT")
    return item


def _input(payload: Mapping[str, Any], verify_id: bool) -> None:
    _closed(payload, _INPUT_FIELDS, "CV2_INPUT_FIELDS")
    if payload["schema_version"] != CONSENSUS_V2_SCHEMA or payload["authorization_effect"] != "none": raise ConsensusV2Error("CV2_INPUT_VERSION")
    for name in ("experiment_id", "run_id", "round_id", "qualification_result_id"): _opaque(payload[name], "CV2_INPUT_ID")
    basis = _basis(payload["comparison_basis"]); _ordered_ids(payload["quality_policy_ids"], "CV2_QUALITY_POLICY_CLOSURE", nonempty=True); parameters = _ordered_ids(payload["parameter_ids"], "CV2_PARAMETER_CLOSURE")
    observations = tuple(_observation(item) for item in payload["observations"]) if isinstance(payload["observations"], (list, tuple)) else ()
    if not observations: raise ConsensusV2Error("CV2_OBSERVATION_CLOSURE")
    keys = tuple((item["edge_id"], item["source_sequence"], item["observation_id"]) for item in observations)
    if keys != tuple(sorted(keys)) or len({item["edge_id"] for item in observations}) != len(observations): raise ConsensusV2Error("CV2_OBSERVATION_ORDER")
    profile_ids = {item["profile_id"] for item in observations}
    if basis["kind"] == "same_profile_raw_current" and profile_ids != {basis["profile_ids"][0]}: raise ConsensusV2Error("CV2_RAW_CURRENT_PROFILE")
    if basis["kind"] == "dimensionless_profile_residual" and not profile_ids.issubset(set(basis["profile_ids"])): raise ConsensusV2Error("CV2_RESIDUAL_PROFILE")
    if not set(basis["uncertainty_parameter_ids"]).issubset(parameters): raise ConsensusV2Error("CV2_PARAMETER_CLOSURE")
    _opaque(payload["input_content_id"], "CV2_INPUT_CONTENT_ID")
    if verify_id and payload["input_content_id"] != consensus_round_input_content_id(payload): raise ConsensusV2Error("CV2_INPUT_CONTENT_HASH")


def canonical_consensus_round_input_bytes(payload: Mapping[str, Any]) -> bytes:
    value = _thaw(payload); value.pop("input_content_id", None)
    return json.dumps(value, ensure_ascii=True, sort_keys=True, separators=(",", ":"), allow_nan=False).encode("ascii")


def consensus_round_input_content_id(payload: Mapping[str, Any]) -> str:
    return "sha256:" + hashlib.sha256(canonical_consensus_round_input_bytes(payload)).hexdigest()


@dataclass(frozen=True)
class ConsensusRoundInputV2:
    payload: Mapping[str, Any]
    def __post_init__(self) -> None:
        _input(self.payload, True); object.__setattr__(self, "payload", _freeze(_thaw(self.payload)))
    def to_dict(self) -> dict[str, Any]: return _thaw(self.payload)
    def canonical_bytes(self) -> bytes: return canonical_consensus_round_input_bytes(self.payload)


def parse_consensus_round_input_v2(payload: object) -> ConsensusRoundInputV2:
    if not isinstance(payload, Mapping): raise ConsensusV2Error("CV2_INPUT_OBJECT")
    return ConsensusRoundInputV2(dict(payload))


def parse_consensus_round_input_v2_json(raw: str | bytes) -> ConsensusRoundInputV2:
    """Parse strict JSON, rejecting duplicate keys before record construction."""
    def no_duplicates(pairs: list[tuple[str, Any]]) -> dict[str, Any]:
        value: dict[str, Any] = {}
        for key, item in pairs:
            if key in value: raise ConsensusV2Error("CV2_DUPLICATE_FIELD")
            value[key] = item
        return value
    try:
        return parse_consensus_round_input_v2(json.loads(raw, object_pairs_hook=no_duplicates, parse_constant=lambda _: (_ for _ in ()).throw(ValueError())))
    except ConsensusV2Error: raise
    except (TypeError, ValueError, json.JSONDecodeError) as exc: raise ConsensusV2Error("CV2_STRICT_JSON") from exc


def _decision(payload: Mapping[str, Any], verify_id: bool) -> None:
    _closed(payload, _DECISION_FIELDS, "CV2_DECISION_FIELDS")
    if payload["schema_version"] != CONSENSUS_V2_SCHEMA or payload["authorization_effect"] != "none": raise ConsensusV2Error("CV2_DECISION_VERSION")
    for field in ("round_input_id", "round_input_hash"): _opaque(payload[field], "CV2_DECISION_INPUT")
    _basis(payload["comparison_basis"])
    participants, included = _ordered_ids(payload["participant_ids"], "CV2_PARTICIPANT_CLOSURE", nonempty=True), _ordered_ids(payload["included_ids"], "CV2_INCLUDED_CLOSURE")
    if not set(included).issubset(participants): raise ConsensusV2Error("CV2_INCLUDED_CLOSURE")
    if not isinstance(payload["excluded"], (list, tuple)): raise ConsensusV2Error("CV2_EXCLUSION_CLOSURE")
    excluded: list[str] = []
    for entry in payload["excluded"]:
        row = _closed(entry, {"edge_id", "reason_id", "evidence_ids"}, "CV2_EXCLUSION_FIELDS")
        edge = _opaque(row["edge_id"], "CV2_EXCLUSION_ID"); _opaque(row["reason_id"], "CV2_EXCLUSION_REASON"); _ordered_ids(row["evidence_ids"], "CV2_EXCLUSION_EVIDENCE", nonempty=True); excluded.append(edge)
    if tuple(excluded) != tuple(sorted(excluded)) or len(set(excluded)) != len(excluded) or set(excluded).union(included) != set(participants) or set(excluded).intersection(included): raise ConsensusV2Error("CV2_EXCLUSION_CLOSURE")
    if not isinstance(payload["diagnostics"], (list, tuple)) or any(not isinstance(x, str) or not x for x in payload["diagnostics"]): raise ConsensusV2Error("CV2_DIAGNOSTICS")
    outcome = payload["outcome"]
    if outcome not in {item.value for item in ConsensusOutcomeV2}: raise ConsensusV2Error("CV2_OUTCOME")
    ranking = _ordered_ids(payload["ranking"], "CV2_RANKING")
    if outcome == "success" and (set(ranking) != set(included) or not ranking): raise ConsensusV2Error("CV2_SUCCESS_RANKING")
    if outcome == "failure" and (ranking or payload["included_ids"]): raise ConsensusV2Error("CV2_FAILURE_NO_RANKING")
    _opaque(payload["decision_content_id"], "CV2_DECISION_CONTENT_ID")
    if verify_id and payload["decision_content_id"] != consensus_decision_content_id(payload): raise ConsensusV2Error("CV2_DECISION_CONTENT_HASH")


def canonical_consensus_decision_bytes(payload: Mapping[str, Any]) -> bytes:
    value = _thaw(payload); value.pop("decision_content_id", None)
    return json.dumps(value, ensure_ascii=True, sort_keys=True, separators=(",", ":"), allow_nan=False).encode("ascii")


def consensus_decision_content_id(payload: Mapping[str, Any]) -> str:
    return "sha256:" + hashlib.sha256(canonical_consensus_decision_bytes(payload)).hexdigest()


@dataclass(frozen=True)
class ConsensusDecisionV2:
    payload: Mapping[str, Any]
    def __post_init__(self) -> None:
        _decision(self.payload, True); object.__setattr__(self, "payload", _freeze(_thaw(self.payload)))
    def to_dict(self) -> dict[str, Any]: return _thaw(self.payload)
    def canonical_bytes(self) -> bytes: return canonical_consensus_decision_bytes(self.payload)


def parse_consensus_decision_v2(payload: object) -> ConsensusDecisionV2:
    if not isinstance(payload, Mapping): raise ConsensusV2Error("CV2_DECISION_OBJECT")
    return ConsensusDecisionV2(dict(payload))


def parse_consensus_decision_v2_json(raw: str | bytes) -> ConsensusDecisionV2:
    def no_duplicates(pairs: list[tuple[str, Any]]) -> dict[str, Any]:
        value: dict[str, Any] = {}
        for key, item in pairs:
            if key in value: raise ConsensusV2Error("CV2_DUPLICATE_FIELD")
            value[key] = item
        return value
    try:
        return parse_consensus_decision_v2(json.loads(raw, object_pairs_hook=no_duplicates, parse_constant=lambda _: (_ for _ in ()).throw(ValueError())))
    except ConsensusV2Error: raise
    except (TypeError, ValueError, json.JSONDecodeError) as exc: raise ConsensusV2Error("CV2_STRICT_JSON") from exc
