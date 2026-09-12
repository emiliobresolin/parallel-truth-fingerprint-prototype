"""Immutable public contracts for a fair physical-candidate comparison.

These records deliberately carry only opaque evidence identities.  They do not
contain windows, values, labels, truth, fitted weights, or an implicit model
default.  Fitting and publication are separate, explicitly authorized work.
"""
from __future__ import annotations

import hashlib
import json
from dataclasses import dataclass, fields
from enum import StrEnum
from typing import Any


PHYSICAL_CANDIDATE_COMPARISON_SCHEMA = "PhysicalCandidateComparison.v1"


class PhysicalCandidateFamily(StrEnum):
    LSTM_AE = "lstm_ae"
    GRU_AE = "gru_ae"
    TRANSPARENT_BASELINE = "transparent_baseline"


class CandidateRunStatus(StrEnum):
    COMPLETE = "complete"
    FAILED = "failed"
    STOPPED_EARLY = "stopped_early"
    BUDGET_EXCEEDED = "budget_exceeded"
    BLOCKED = "blocked"


class ComparisonDisposition(StrEnum):
    COMPLETE = "complete"
    INCOMPLETE = "incomplete"
    BLOCKED = "blocked"
    INVALID = "invalid"


def _ordered(items: tuple[Any, ...], attribute: str) -> tuple[Any, ...]:
    return tuple(sorted(items, key=lambda item: str(getattr(item, attribute))))


def _plain(value: Any) -> Any:
    if isinstance(value, StrEnum):
        return value.value
    if isinstance(value, tuple):
        return [_plain(item) for item in value]
    if hasattr(value, "__dataclass_fields__"):
        return {field.name: _plain(getattr(value, field.name)) for field in fields(value)}
    return value


class _Record:
    def to_dict(self) -> dict[str, Any]:
        return {field.name: _plain(getattr(self, field.name)) for field in fields(self)}


@dataclass(frozen=True)
class PhysicalCandidate:
    candidate_id: str
    family: PhysicalCandidateFamily | str
    architecture_identity: str
    parameter_set_id: str
    configuration_id: str
    preregistered_exception_ids: tuple[str, ...] = ()

    def __post_init__(self) -> None:
        object.__setattr__(self, "preregistered_exception_ids", tuple(sorted(set(self.preregistered_exception_ids))))


@dataclass(frozen=True)
class FrozenPhysicalComparisonPlan(_Record):
    schema_version: str
    protocol_id: str
    feature_schema_id: str
    partition_id: str
    preprocessing_state_id: str
    normal_training_evidence_id: str
    validation_evidence_id: str
    tuning_access_id: str
    resource_budget_id: str
    selection_rule_id: str
    primary_metric_ids: tuple[str, ...]
    repetition_ids: tuple[str, ...]
    candidates: tuple[PhysicalCandidate, ...]
    plan_content_id: str
    authorization_effect: str = "none"

    def __post_init__(self) -> None:
        object.__setattr__(self, "primary_metric_ids", tuple(sorted(set(self.primary_metric_ids))))
        object.__setattr__(self, "repetition_ids", tuple(sorted(set(self.repetition_ids))))
        object.__setattr__(self, "candidates", _ordered(self.candidates, "candidate_id"))


@dataclass(frozen=True)
class PhysicalCandidateRun(_Record):
    candidate_id: str
    repetition_id: str
    feature_schema_id: str
    partition_id: str
    preprocessing_state_id: str
    normal_training_evidence_id: str
    validation_evidence_id: str
    tuning_access_id: str
    resource_budget_id: str
    configuration_id: str
    status: CandidateRunStatus | str
    output_ids: tuple[str, ...]
    resource_evidence_ids: tuple[str, ...]
    diagnostic_ids: tuple[str, ...]
    limitation_ids: tuple[str, ...]
    applied_exception_ids: tuple[str, ...] = ()

    def __post_init__(self) -> None:
        for name in ("output_ids", "resource_evidence_ids", "diagnostic_ids", "limitation_ids", "applied_exception_ids"):
            object.__setattr__(self, name, tuple(sorted(set(getattr(self, name)))))


@dataclass(frozen=True)
class PhysicalCandidateComparisonRecord(_Record):
    schema_version: str
    plan_content_id: str
    run_records: tuple[PhysicalCandidateRun, ...]
    selected_candidate_id: str | None
    selection_record_id: str | None
    non_selected_candidate_ids: tuple[str, ...]
    disposition: ComparisonDisposition | str
    diagnostic_codes: tuple[str, ...]
    record_content_id: str
    authorization_effect: str = "none"

    def __post_init__(self) -> None:
        object.__setattr__(self, "run_records", tuple(sorted(
            self.run_records, key=lambda item: (item.candidate_id, item.repetition_id)
        )))
        object.__setattr__(self, "non_selected_candidate_ids", tuple(sorted(set(self.non_selected_candidate_ids))))
        object.__setattr__(self, "diagnostic_codes", tuple(sorted(set(self.diagnostic_codes))))


def canonical_physical_comparison_plan_bytes(record: FrozenPhysicalComparisonPlan) -> bytes:
    payload = record.to_dict(); payload.pop("plan_content_id", None)
    return json.dumps(payload, ensure_ascii=True, sort_keys=True, separators=(",", ":"), allow_nan=False).encode("ascii")


def physical_comparison_plan_content_id(record: FrozenPhysicalComparisonPlan) -> str:
    return "sha256:" + hashlib.sha256(canonical_physical_comparison_plan_bytes(record)).hexdigest()


def canonical_physical_comparison_record_bytes(record: PhysicalCandidateComparisonRecord) -> bytes:
    payload = record.to_dict(); payload.pop("record_content_id", None)
    return json.dumps(payload, ensure_ascii=True, sort_keys=True, separators=(",", ":"), allow_nan=False).encode("ascii")


def physical_comparison_record_content_id(record: PhysicalCandidateComparisonRecord) -> str:
    return "sha256:" + hashlib.sha256(canonical_physical_comparison_record_bytes(record)).hexdigest()
