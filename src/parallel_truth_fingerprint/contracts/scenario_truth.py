"""Restricted, immutable ``ScenarioTruth.v1`` contract.

This module is deliberately data-only.  It defines a declared restricted-truth
record; it does not produce truth, resolve references, unlock it, or write it.
"""
from __future__ import annotations

import hashlib
import json
import re
from dataclasses import dataclass, fields, replace
from typing import Any, Mapping


CONTRACT_ID = "ScenarioTruth"
SCHEMA_VERSION = 1
AUDIENCE = "evaluator_restricted"
NAMESPACE = "restricted_truth"
SEMANTIC_IDENTITY = "declared_restricted_scenario_truth"
DECLARATION_ROLE = "declared_restricted_truth"
AUTHORIZATION_EFFECT = "none"

_DIGEST = re.compile(r"sha256:[0-9a-f]{64}\Z")
_UTC = re.compile(r"\d{4}-\d{2}-\d{2}T\d{2}:\d{2}:\d{2}\.\d{6}Z\Z")
_FIELDS = {
    "contract_id", "schema_version", "scenario_truth_content_id", "experiment_id", "matrix_id",
    "predeclared_run_id", "trace_id", "event_id", "correlation_id", "condition_interval_ref",
    "intervention_interval_ref", "declared_truth_provenance_ref", "restricted_writer_id",
    "semantic_identity", "audience_access_class", "namespace", "declaration_role", "declared_at",
    "interval_facts_at", "authorization_effect",
}


@dataclass(frozen=True)
class ScenarioTruthViolation:
    rule_id: str
    field: str
    token: str

    def to_dict(self) -> dict[str, str]:
        return {"rule_id": self.rule_id, "field": self.field, "token": self.token}


class ScenarioTruthError(ValueError):
    def __init__(self, rule_id: str, field: str, token: str) -> None:
        self.violation = ScenarioTruthViolation(rule_id, field, token)
        super().__init__(f"{rule_id}:{field}:{token}")


@dataclass(frozen=True)
class ScenarioTruth:
    contract_id: str
    schema_version: int
    scenario_truth_content_id: str
    experiment_id: str
    matrix_id: str
    predeclared_run_id: str
    trace_id: str
    event_id: str
    correlation_id: str
    condition_interval_ref: str
    intervention_interval_ref: str
    declared_truth_provenance_ref: str
    restricted_writer_id: str
    semantic_identity: str
    audience_access_class: str
    namespace: str
    declaration_role: str
    declared_at: str
    interval_facts_at: str
    authorization_effect: str = AUTHORIZATION_EFFECT

    @property
    def immutable_parent_ids(self) -> tuple[str, ...]:
        return (
            self.experiment_id, self.matrix_id, self.predeclared_run_id, self.trace_id,
            self.condition_interval_ref, self.intervention_interval_ref,
            self.declared_truth_provenance_ref, self.restricted_writer_id,
        )

    def to_dict(self) -> dict[str, object]:
        return {item.name: getattr(self, item.name) for item in fields(self)}

    @classmethod
    def build(cls, *, experiment_id: str, matrix_id: str, predeclared_run_id: str, trace_id: str,
              event_id: str, correlation_id: str, condition_interval_ref: str,
              intervention_interval_ref: str, declared_truth_provenance_ref: str,
              restricted_writer_id: str, declared_at: str, interval_facts_at: str) -> "ScenarioTruth":
        provisional = cls(
            CONTRACT_ID, SCHEMA_VERSION, "", experiment_id, matrix_id, predeclared_run_id, trace_id,
            event_id, correlation_id, condition_interval_ref, intervention_interval_ref,
            declared_truth_provenance_ref, restricted_writer_id, SEMANTIC_IDENTITY, AUDIENCE,
            NAMESPACE, DECLARATION_ROLE, declared_at, interval_facts_at,
        )
        return replace(provisional, scenario_truth_content_id=scenario_truth_content_id(provisional))


def canonical_scenario_truth_bytes(record: ScenarioTruth) -> bytes:
    """Return canonical UTF-8 bytes.  No ambient values are consulted."""
    return (json.dumps(record.to_dict(), sort_keys=True, ensure_ascii=True, separators=(",", ":"),
                       allow_nan=False) + "\n").encode("ascii")


def scenario_truth_content_id(record: ScenarioTruth) -> str:
    """Hash the complete record with its self identity excluded."""
    payload = record.to_dict()
    payload["scenario_truth_content_id"] = ""
    encoded = (json.dumps(payload, sort_keys=True, ensure_ascii=True, separators=(",", ":"),
                          allow_nan=False) + "\n").encode("ascii")
    return "sha256:" + hashlib.sha256(encoded).hexdigest()


def _require_digest(value: object, field: str) -> str:
    if not isinstance(value, str) or not _DIGEST.fullmatch(value):
        raise ScenarioTruthError("STV1-IDENTITY-INVALID", field, "immutable_digest_required")
    return value


def _require_utc(value: object, field: str) -> str:
    if not isinstance(value, str) or not _UTC.fullmatch(value):
        raise ScenarioTruthError("STV1-TIME-INVALID", field, "canonical_utc_required")
    return value


def parse_scenario_truth(payload: object) -> ScenarioTruth:
    """Strictly parse a JSON-shaped v1 payload without IDs or time defaults."""
    if not isinstance(payload, Mapping) or set(payload) != _FIELDS:
        raise ScenarioTruthError("STV1-PARSE-FIELDS", "record", "closed_fields_required")
    if payload["contract_id"] != CONTRACT_ID or payload["schema_version"] != SCHEMA_VERSION:
        raise ScenarioTruthError("STV1-VERSION", "contract_id", "v1_required")
    for field in _FIELDS - {"contract_id", "schema_version", "semantic_identity", "audience_access_class",
                            "namespace", "declaration_role", "declared_at", "interval_facts_at",
                            "authorization_effect"}:
        _require_digest(payload[field], field)
    for field, expected in (("semantic_identity", SEMANTIC_IDENTITY), ("audience_access_class", AUDIENCE),
                            ("namespace", NAMESPACE), ("declaration_role", DECLARATION_ROLE),
                            ("authorization_effect", AUTHORIZATION_EFFECT)):
        if payload[field] != expected:
            raise ScenarioTruthError("STV1-RESTRICTED-BINDING", field, "exact_restricted_token_required")
    _require_utc(payload["declared_at"], "declared_at")
    _require_utc(payload["interval_facts_at"], "interval_facts_at")
    record = ScenarioTruth(**dict(payload))  # type: ignore[arg-type]
    if record.scenario_truth_content_id != scenario_truth_content_id(record):
        raise ScenarioTruthError("STV1-CONTENT-ID", "scenario_truth_content_id", "recomputed_identity_required")
    return record


def parse_scenario_truth_json(payload: str | bytes) -> ScenarioTruth:
    """Decode JSON while rejecting duplicate keys before strict parsing."""
    def no_duplicates(pairs: list[tuple[str, object]]) -> dict[str, object]:
        result: dict[str, object] = {}
        for key, value in pairs:
            if key in result:
                raise ScenarioTruthError("STV1-PARSE-FIELDS", key, "duplicate_key")
            result[key] = value
        return result
    try:
        raw = json.loads(payload, object_pairs_hook=no_duplicates)
    except ScenarioTruthError:
        raise
    except (TypeError, ValueError, UnicodeDecodeError) as exc:
        raise ScenarioTruthError("STV1-PARSE-JSON", "record", "valid_json_required") from exc
    return parse_scenario_truth(raw)
