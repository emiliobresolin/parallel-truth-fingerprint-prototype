"""Evaluator-restricted, immutable records for post-freeze physical outcomes.

These records are intentionally separate from detector-facing scores.  They
model an authorized evaluator's *reported* join of frozen score identities to
restricted truth; they neither unlock truth nor run a detector.
"""
from __future__ import annotations

import hashlib
import json
from dataclasses import dataclass, fields, replace
from enum import StrEnum
from typing import Any


PHYSICAL_EVALUATION_SCHEMA = "PhysicalPostTruthEvaluation.v1"


class TruthState(StrEnum):
    NORMAL = "normal"
    ANOMALOUS = "anomalous"
    UNAVAILABLE = "unavailable"


class MetricApplicability(StrEnum):
    APPLICABLE = "applicable"
    INAPPLICABLE = "inapplicable"


class EvaluationDisposition(StrEnum):
    COMPLETE = "complete"
    INCOMPLETE = "incomplete"
    BLOCKED = "blocked"
    INVALID = "invalid"


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
class FrozenEvaluationWindow:
    window_id: str
    experiment_id: str
    run_id: str
    event_id: str
    correlation_id: str


@dataclass(frozen=True)
class PhysicalEvaluationPlan(_Record):
    schema_version: str
    score_manifest_id: str
    bundle_id: str
    threshold_id: str
    partition_id: str
    metric_policy_id: str
    experiment_id: str
    truth_unlock_id: str
    evaluator_authorization_id: str
    windows: tuple[FrozenEvaluationWindow, ...]
    planned_stratum_ids: tuple[str, ...]
    planned_sensitivity_threshold_ids: tuple[str, ...]
    plan_id: str = ""
    authorization_effect: str = "none"

    def __post_init__(self) -> None:
        object.__setattr__(self, "windows", tuple(sorted(self.windows, key=lambda item: item.window_id)))
        object.__setattr__(self, "planned_stratum_ids", tuple(sorted(set(self.planned_stratum_ids))))
        object.__setattr__(self, "planned_sensitivity_threshold_ids", tuple(sorted(set(self.planned_sensitivity_threshold_ids))))


@dataclass(frozen=True)
class RestrictedTruthJoin(_Record):
    score_id: str
    window_id: str
    experiment_id: str
    run_id: str
    event_id: str
    correlation_id: str
    truth_record_id: str
    truth_state: TruthState | str
    regime_id: str
    transition_id: str
    scenario_id: str
    severity_id: str
    sensor_id: str
    repetition_id: str
    recovery_id: str
    quality_state_id: str
    stratum_ids: tuple[str, ...]

    def __post_init__(self) -> None:
        object.__setattr__(self, "stratum_ids", tuple(sorted(set(self.stratum_ids))))


@dataclass(frozen=True)
class MetricDeclaration(_Record):
    metric_id: str
    metric_kind: str
    applicability: MetricApplicability | str
    inapplicable_reason_id: str | None = None


@dataclass(frozen=True)
class EvaluationMetric(_Record):
    metric_id: str
    metric_kind: str
    applicability: MetricApplicability | str
    value: str | None
    support: int
    inapplicable_reason_id: str | None = None
    stratum_id: str | None = None


@dataclass(frozen=True)
class SensitivityOutcome(_Record):
    threshold_id: str
    score_id: str
    decision: str


@dataclass(frozen=True)
class PhysicalPostTruthEvaluation(_Record):
    schema_version: str
    plan_id: str
    score_manifest_id: str
    primary_threshold_id: str
    joins: tuple[RestrictedTruthJoin, ...]
    metrics: tuple[EvaluationMetric, ...]
    sensitivity_outcomes: tuple[SensitivityOutcome, ...]
    resource_evidence_ids: tuple[str, ...]
    quality_evidence_ids: tuple[str, ...]
    limitation_ids: tuple[str, ...]
    disposition: EvaluationDisposition | str
    diagnostic_codes: tuple[str, ...]
    evaluation_id: str = ""
    authorization_effect: str = "none"

    def __post_init__(self) -> None:
        object.__setattr__(self, "joins", tuple(sorted(self.joins, key=lambda item: item.score_id)))
        object.__setattr__(self, "metrics", tuple(sorted(self.metrics, key=lambda item: (item.metric_id, item.stratum_id or ""))))
        object.__setattr__(self, "sensitivity_outcomes", tuple(sorted(self.sensitivity_outcomes, key=lambda item: (item.threshold_id, item.score_id))))
        for name in ("resource_evidence_ids", "quality_evidence_ids", "limitation_ids", "diagnostic_codes"):
            object.__setattr__(self, name, tuple(sorted(set(getattr(self, name)))))


def _canonical(record: _Record, identity_field: str) -> bytes:
    payload = record.to_dict()
    payload[identity_field] = ""
    return (json.dumps(payload, ensure_ascii=True, sort_keys=True, separators=(",", ":"), allow_nan=False) + "\n").encode("ascii")


def physical_evaluation_plan_identity(record: PhysicalEvaluationPlan) -> str:
    return "sha256:" + hashlib.sha256(_canonical(record, "plan_id")).hexdigest()


def physical_post_truth_evaluation_identity(record: PhysicalPostTruthEvaluation) -> str:
    return "sha256:" + hashlib.sha256(_canonical(record, "evaluation_id")).hexdigest()


def finalize_physical_evaluation_plan(record: PhysicalEvaluationPlan) -> PhysicalEvaluationPlan:
    return replace(record, plan_id=physical_evaluation_plan_identity(replace(record, plan_id="")))


def finalize_physical_post_truth_evaluation(record: PhysicalPostTruthEvaluation) -> PhysicalPostTruthEvaluation:
    return replace(record, evaluation_id=physical_post_truth_evaluation_identity(replace(record, evaluation_id="")))
