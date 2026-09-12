"""Pure, fail-closed post-truth evaluator for frozen physical scores.

No truth store, scoring runtime, threshold calculation, persistence, or
authorization issuer is present here.  Callers inject both immutable identity
resolution and the narrow evaluator authorization check.
"""
from __future__ import annotations

from dataclasses import dataclass
from typing import Callable, Iterable

from parallel_truth_fingerprint.contracts.physical_blind_scores import PhysicalScoreManifest, ScoreDecision
from parallel_truth_fingerprint.contracts.physical_evaluation import (
    EvaluationDisposition, EvaluationMetric, FrozenEvaluationWindow, MetricApplicability,
    MetricDeclaration, PhysicalEvaluationPlan, PhysicalPostTruthEvaluation, RestrictedTruthJoin,
    SensitivityOutcome, TruthState, finalize_physical_post_truth_evaluation,
    physical_evaluation_plan_identity,
)
from parallel_truth_fingerprint.contracts.scientific_governance import is_immutable_id
from parallel_truth_fingerprint.evidence.physical_blind_scores import validate_physical_score_manifest


ImmutableResolver = Callable[[str], bool]
AuthorizationValidator = Callable[[str, str, str], bool]
_KINDS = frozenset({"precision", "recall", "f1", "false_positive_count", "false_events", "confusion_tp", "confusion_fp", "confusion_tn", "confusion_fn", "classified_count", "unavailable_count", "event_recall", "event_support"})


@dataclass(frozen=True)
class PhysicalEvaluationValidation:
    accepted: bool
    diagnostic_codes: tuple[str, ...]
    authorization_effect: str = "none"


def _result(codes: Iterable[str]) -> PhysicalEvaluationValidation:
    ordered = tuple(sorted(set(codes)))
    return PhysicalEvaluationValidation(not ordered, ordered)


def _resolved(value: str | None, resolver: ImmutableResolver) -> bool:
    return isinstance(value, str) and is_immutable_id(value) and resolver(value)


def validate_physical_evaluation_plan(plan: PhysicalEvaluationPlan, *, immutable_resolver: ImmutableResolver,
                                      authorization_validator: AuthorizationValidator) -> PhysicalEvaluationValidation:
    codes: list[str] = []
    if plan.schema_version != "PhysicalPostTruthEvaluation.v1": codes.append("PPE13_PLAN_SCHEMA_UNSUPPORTED")
    if plan.authorization_effect != "none": codes.append("PPE13_PLAN_AUTHORIZATION_EFFECT_FORBIDDEN")
    ids = (plan.score_manifest_id, plan.bundle_id, plan.threshold_id, plan.partition_id, plan.metric_policy_id,
           plan.experiment_id, plan.truth_unlock_id, plan.evaluator_authorization_id, *plan.planned_stratum_ids,
           *plan.planned_sensitivity_threshold_ids)
    if not all(_resolved(value, immutable_resolver) for value in ids): codes.append("PPE13_PLAN_REFERENCE_UNRESOLVED")
    if not plan.windows or len({item.window_id for item in plan.windows}) != len(plan.windows): codes.append("PPE13_WINDOW_INVENTORY_INVALID")
    for item in plan.windows:
        if item.experiment_id != plan.experiment_id or not all(_resolved(value, immutable_resolver) for value in (item.window_id, item.experiment_id, item.run_id, item.event_id, item.correlation_id)):
            codes.append("PPE13_WINDOW_PROVENANCE_INVALID")
    if plan.plan_id != physical_evaluation_plan_identity(plan): codes.append("PPE13_PLAN_IMMUTABILITY_INVALID")
    if not authorization_validator("post_truth_physical_evaluation", plan.evaluator_authorization_id, plan.truth_unlock_id): codes.append("PPE13_AUTHORIZATION_DENIED")
    return _result(codes)


def _ratio(numerator: int, denominator: int) -> str | None:
    return None if denominator == 0 else str(numerator / denominator)


def _metrics(declarations: tuple[MetricDeclaration, ...], joins: tuple[RestrictedTruthJoin, ...], decisions: dict[str, str], planned_strata: tuple[str, ...]) -> tuple[EvaluationMetric, ...]:
    """Return an overall result plus a visible result for every declared stratum."""
    output: list[EvaluationMetric] = []
    for stratum_id, scoped_joins in ((None, joins), *((item, tuple(join for join in joins if item in join.stratum_ids)) for item in planned_strata)):
        output.extend(_scoped_metrics(declarations, scoped_joins, decisions, stratum_id))
    return tuple(output)


def _scoped_metrics(declarations: tuple[MetricDeclaration, ...], joins: tuple[RestrictedTruthJoin, ...], decisions: dict[str, str], stratum_id: str | None) -> tuple[EvaluationMetric, ...]:
    counts = {"tp": 0, "fp": 0, "tn": 0, "fn": 0, "unavailable": 0}
    detected_events: set[str] = set(); anomalous_events: set[str] = set(); false_events: set[str] = set()
    for join in joins:
        decision = decisions[join.score_id]; truth = str(join.truth_state)
        if truth == TruthState.UNAVAILABLE.value or decision not in {ScoreDecision.NORMAL.value, ScoreDecision.ANOMALOUS.value}:
            counts["unavailable"] += 1; continue
        anomaly = decision == ScoreDecision.ANOMALOUS.value; expected = truth == TruthState.ANOMALOUS.value
        if expected: anomalous_events.add(join.event_id)
        if anomaly and expected: counts["tp"] += 1; detected_events.add(join.event_id)
        elif anomaly: counts["fp"] += 1; false_events.add(join.event_id)
        elif expected: counts["fn"] += 1
        else: counts["tn"] += 1
    classified = counts["tp"] + counts["fp"] + counts["tn"] + counts["fn"]
    values: dict[str, str | None] = {
        "precision": _ratio(counts["tp"], counts["tp"] + counts["fp"]), "recall": _ratio(counts["tp"], counts["tp"] + counts["fn"]),
        "f1": _ratio(2 * counts["tp"], 2 * counts["tp"] + counts["fp"] + counts["fn"]),
        "false_positive_count": str(counts["fp"]), "false_events": str(len(false_events)), "confusion_tp": str(counts["tp"]), "confusion_fp": str(counts["fp"]),
        "confusion_tn": str(counts["tn"]), "confusion_fn": str(counts["fn"]), "classified_count": str(classified), "unavailable_count": str(counts["unavailable"]),
        "event_recall": _ratio(len(detected_events), len(anomalous_events)), "event_support": str(len(anomalous_events)),
    }
    output: list[EvaluationMetric] = []
    for declaration in declarations:
        if str(declaration.applicability) == MetricApplicability.INAPPLICABLE.value:
            output.append(EvaluationMetric(declaration.metric_id, declaration.metric_kind, declaration.applicability, None, 0, declaration.inapplicable_reason_id, stratum_id)); continue
        value = values.get(declaration.metric_kind)
        reason = declaration.inapplicable_reason_id if value is None else None
        applicability = MetricApplicability.APPLICABLE if value is not None else MetricApplicability.INAPPLICABLE
        output.append(EvaluationMetric(declaration.metric_id, declaration.metric_kind, applicability, value, classified if declaration.metric_kind not in {"event_recall", "event_support"} else len(anomalous_events), reason, stratum_id))
    return tuple(output)


def evaluate_frozen_physical_scores(plan: PhysicalEvaluationPlan, manifest: PhysicalScoreManifest, *,
                                    joins: tuple[RestrictedTruthJoin, ...], metric_declarations: tuple[MetricDeclaration, ...],
                                    sensitivity_outcomes: tuple[SensitivityOutcome, ...], resource_evidence_ids: tuple[str, ...],
                                    quality_evidence_ids: tuple[str, ...], limitation_ids: tuple[str, ...],
                                    immutable_resolver: ImmutableResolver, authorization_validator: AuthorizationValidator) -> PhysicalPostTruthEvaluation:
    """Evaluate only a complete frozen score closure with an authorized truth join."""
    codes = list(validate_physical_evaluation_plan(plan, immutable_resolver=immutable_resolver, authorization_validator=authorization_validator).diagnostic_codes)
    score_check = validate_physical_score_manifest(manifest, immutable_resolver=immutable_resolver)
    codes.extend("PPE13_" + code for code in score_check.diagnostic_codes)
    if (manifest.manifest_id, manifest.bundle_id, manifest.partition_id) != (plan.score_manifest_id, plan.bundle_id, plan.partition_id): codes.append("PPE13_MANIFEST_PLAN_BINDING_MISMATCH")
    scores = {item.score_id: item for item in manifest.scores}; windows = {item.window_id: item for item in plan.windows}
    if len(joins) != len(scores) or {item.score_id for item in joins} != set(scores): codes.append("PPE13_TRUTH_JOIN_CLOSURE_INCOMPLETE")
    for join in joins:
        score = scores.get(join.score_id); window = windows.get(join.window_id)
        required = (join.score_id, join.window_id, join.experiment_id, join.run_id, join.event_id, join.correlation_id, join.truth_record_id, join.regime_id, join.transition_id, join.scenario_id, join.severity_id, join.sensor_id, join.repetition_id, join.recovery_id, join.quality_state_id, *join.stratum_ids)
        if not all(_resolved(value, immutable_resolver) for value in required): codes.append("PPE13_TRUTH_JOIN_REFERENCE_UNRESOLVED")
        if score is None or window is None or (score.window_id, score.run_correlation_id) != (join.window_id, join.correlation_id) or (window.experiment_id, window.run_id, window.event_id, window.correlation_id) != (join.experiment_id, join.run_id, join.event_id, join.correlation_id): codes.append("PPE13_TRUTH_JOIN_IDENTITY_MISMATCH")
        if str(join.truth_state) not in {item.value for item in TruthState}: codes.append("PPE13_TRUTH_STATE_INVALID")
        if not set(join.stratum_ids).issubset(plan.planned_stratum_ids): codes.append("PPE13_UNDECLARED_STRATUM")
    declarations = {item.metric_id: item for item in metric_declarations}
    if len(declarations) != len(metric_declarations) or not declarations: codes.append("PPE13_METRIC_POLICY_INVALID")
    for item in metric_declarations:
        if not _resolved(item.metric_id, immutable_resolver) or item.metric_kind not in _KINDS or str(item.applicability) not in {value.value for value in MetricApplicability} or (str(item.applicability) == MetricApplicability.INAPPLICABLE.value and not _resolved(item.inapplicable_reason_id, immutable_resolver)):
            codes.append("PPE13_METRIC_DECLARATION_INVALID")
    if not all(_resolved(value, immutable_resolver) for value in (*resource_evidence_ids, *quality_evidence_ids, *limitation_ids)): codes.append("PPE13_EVIDENCE_REFERENCE_UNRESOLVED")
    expected_sensitivity = {(threshold_id, score_id) for threshold_id in plan.planned_sensitivity_threshold_ids for score_id in scores}
    actual_sensitivity = {(item.threshold_id, item.score_id) for item in sensitivity_outcomes}
    if actual_sensitivity != expected_sensitivity or any(item.threshold_id not in plan.planned_sensitivity_threshold_ids or item.score_id not in scores or item.decision not in {ScoreDecision.NORMAL.value, ScoreDecision.ANOMALOUS.value, ScoreDecision.UNAVAILABLE.value, ScoreDecision.INVALID.value} for item in sensitivity_outcomes): codes.append("PPE13_SENSITIVITY_INVALID")
    if codes:
        return finalize_physical_post_truth_evaluation(PhysicalPostTruthEvaluation("PhysicalPostTruthEvaluation.v1", plan.plan_id, plan.score_manifest_id, plan.threshold_id, joins, (), sensitivity_outcomes, resource_evidence_ids, quality_evidence_ids, limitation_ids, EvaluationDisposition.INVALID, tuple(codes)))
    decisions = {join.score_id: str(scores[join.score_id].decision) for join in joins}
    metrics = _metrics(metric_declarations, joins, decisions, plan.planned_stratum_ids)
    return finalize_physical_post_truth_evaluation(PhysicalPostTruthEvaluation("PhysicalPostTruthEvaluation.v1", plan.plan_id, plan.score_manifest_id, plan.threshold_id, joins, metrics, sensitivity_outcomes, resource_evidence_ids, quality_evidence_ids, limitation_ids, EvaluationDisposition.COMPLETE, ()))
