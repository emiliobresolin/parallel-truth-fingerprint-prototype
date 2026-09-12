"""Pure fail-closed admission, scoring, and closure checks for Story 13.6.

This module performs no fitting, tuning, threshold change, I/O, publication,
truth access, alias resolution, or ambient runtime discovery.  A caller owns
any actual inference and supplies it as a narrow injected function.
"""
from __future__ import annotations

from dataclasses import dataclass, replace
from typing import Callable, Iterable

from parallel_truth_fingerprint.contracts.detector_bundle import DetectorBundle
from parallel_truth_fingerprint.contracts.physical_blind_scores import (
    DETECTOR_SCORE_SCHEMA, PHYSICAL_SCORE_MANIFEST_SCHEMA, DetectorScore,
    PhysicalScoreManifest, ScoreDecision, detector_score_identity,
    finalize_detector_score, physical_score_manifest_identity,
)
from parallel_truth_fingerprint.contracts.physical_threshold import PhysicalThreshold
from parallel_truth_fingerprint.contracts.scientific_governance import is_immutable_id
from parallel_truth_fingerprint.evidence.detector_bundle import (
    ComponentResolver, DeclaredBundleEnvironment, load_detector_bundle,
)
from parallel_truth_fingerprint.evidence.physical_partitions import (
    PhysicalPartition, PhysicalPartitionRole, PhysicalWindow, PreprocessingFit,
    validate_frozen_preprocessing_application, validate_physical_partition,
)
from parallel_truth_fingerprint.evidence.physical_threshold import load_frozen_threshold


@dataclass(frozen=True)
class BlindPhysicalScoringContext:
    bundle: DetectorBundle
    environment: DeclaredBundleEnvironment
    partition: PhysicalPartition
    preprocessing: PreprocessingFit
    threshold: PhysicalThreshold
    profile_id: str
    code_identity: str
    runtime_identity: str
    authorization_id: str
    authorization_effect: str = "none"


@dataclass(frozen=True)
class PhysicalInferenceInput:
    window: PhysicalWindow
    input_hash: str
    missingness_id: str
    input_quality_id: str
    run_correlation_id: str


@dataclass(frozen=True)
class InferenceResult:
    raw_score: str | None
    calibrated_score: str | None
    decision: ScoreDecision | str
    latency_evidence_id: str | None
    unavailability_reason_id: str | None = None


@dataclass(frozen=True)
class BlindScoreValidation:
    accepted: bool
    diagnostic_codes: tuple[str, ...]
    authorization_effect: str = "none"


ImmutableResolver = Callable[[str], bool]
AuthorizationValidator = Callable[[str, str, str], bool]
Predictor = Callable[[PhysicalInferenceInput], InferenceResult]


def _result(codes: Iterable[str]) -> BlindScoreValidation:
    ordered = tuple(sorted(set(codes)))
    return BlindScoreValidation(not ordered, ordered)


def _resolves(value: str | None, resolver: ImmutableResolver) -> bool:
    return is_immutable_id(value) and resolver(value)


def validate_blind_physical_scoring_context(context: BlindPhysicalScoringContext, *,
                                            component_resolver: ComponentResolver,
                                            immutable_resolver: ImmutableResolver,
                                            authorization_validator: AuthorizationValidator) -> BlindScoreValidation:
    """Verify every frozen prerequisite before any injected prediction runs."""
    codes: list[str] = []
    if context.authorization_effect != "none":
        codes.append("PBS13_CONTEXT_AUTHORIZATION_EFFECT_FORBIDDEN")
    bundle_load = load_detector_bundle(context.bundle, environment=context.environment,
                                       component_resolver=component_resolver)
    codes.extend(bundle_load.diagnostic_codes)
    partition = validate_physical_partition(context.partition, immutable_resolver=immutable_resolver)
    codes.extend(item.code for item in partition.diagnostics)
    preprocessing = validate_frozen_preprocessing_application(
        fit=context.preprocessing, partition=context.partition, role=PhysicalPartitionRole.TEST,
        schema_id=context.bundle.feature_schema_id, profile_id=context.profile_id,
        feature_order=context.bundle.ordered_feature_names,
        missingness_policy_id=context.preprocessing.missingness_policy_id,
        output_hash=context.preprocessing.output_hash, immutable_resolver=immutable_resolver,
    )
    codes.extend(item.code for item in preprocessing.diagnostics)
    threshold = load_frozen_threshold(context.threshold, candidate_id=context.bundle.weights_id,
                                      preprocessing_id=context.bundle.preprocessing_state_id,
                                      feature_schema_id=context.bundle.feature_schema_id)
    if not threshold.loaded:
        codes.append(threshold.reason or "PBS13_THRESHOLD_UNAVAILABLE")
    identities = (context.profile_id, context.code_identity, context.runtime_identity, context.authorization_id,
                  context.bundle.bundle_id)
    if not all(_resolves(value, immutable_resolver) for value in identities):
        codes.append("PBS13_CONTEXT_IDENTITY_UNRESOLVED")
    if (context.code_identity, context.runtime_identity) != (context.bundle.code_identity, context.bundle.runtime_identity):
        codes.append("PBS13_CODE_OR_RUNTIME_MISMATCH")
    if not authorization_validator("blind_scoring", context.authorization_id, context.partition.partition_id):
        codes.append("PBS13_AUTHORIZATION_DENIED")
    return _result(codes)


def _window_codes(context: BlindPhysicalScoringContext, item: PhysicalInferenceInput,
                  immutable_resolver: ImmutableResolver) -> list[str]:
    window = item.window
    codes: list[str] = []
    test_runs = {member.run_id for member in context.partition.members if str(member.role) == "test"}
    if window.source_run_id not in test_runs or window.partition_id != context.partition.partition_id:
        codes.append("PBS13_WINDOW_NOT_ELIGIBLE_TEST")
    if (window.feature_schema_id, window.preprocessing_id) != (context.bundle.feature_schema_id, context.bundle.preprocessing_state_id):
        codes.append("PBS13_WINDOW_COMPATIBILITY_MISMATCH")
    if window.authorization_effect != "none" or not window.window_id:
        codes.append("PBS13_WINDOW_SHAPE_INVALID")
    required = (item.input_hash, item.missingness_id, item.input_quality_id, item.run_correlation_id,
                window.source_run_id, *window.observation_ids, *window.quality_ids)
    if not all(_resolves(value, immutable_resolver) for value in required):
        codes.append("PBS13_INPUT_OR_PROVENANCE_UNRESOLVED")
    return codes


def score_blind_physical_window(context: BlindPhysicalScoringContext, item: PhysicalInferenceInput, *,
                                component_resolver: ComponentResolver, immutable_resolver: ImmutableResolver,
                                authorization_validator: AuthorizationValidator, predictor: Predictor) -> DetectorScore:
    """Create a scored or unavailable immutable record; failures are never dropped."""
    codes = list(validate_blind_physical_scoring_context(
        context, component_resolver=component_resolver, immutable_resolver=immutable_resolver,
        authorization_validator=authorization_validator).diagnostic_codes)
    codes.extend(_window_codes(context, item, immutable_resolver))
    if codes:
        return finalize_detector_score(DetectorScore(
            DETECTOR_SCORE_SCHEMA, context.bundle.bundle_id, item.window.window_id, item.input_hash,
            None, None, str(context.bundle.score_direction), context.bundle.threshold_id,
            ScoreDecision.INVALID, None, item.missingness_id, item.input_quality_id, context.profile_id,
            item.run_correlation_id, context.code_identity, context.runtime_identity,
            next((value for value in (item.input_quality_id, item.missingness_id) if _resolves(value, immutable_resolver)), None),
        ))
    outcome = predictor(item)
    unavailable = str(outcome.decision) in {ScoreDecision.UNAVAILABLE.value, ScoreDecision.INVALID.value}
    if unavailable:
        outcome = replace(outcome, raw_score=None, calibrated_score=None)
    if (not unavailable and (outcome.raw_score is None or outcome.calibrated_score is None)) or (
            unavailable and not _resolves(outcome.unavailability_reason_id, immutable_resolver)) or (
            not unavailable and str(outcome.decision) not in {ScoreDecision.NORMAL.value, ScoreDecision.ANOMALOUS.value}):
        outcome = InferenceResult(None, None, ScoreDecision.INVALID, outcome.latency_evidence_id, item.input_quality_id)
    return finalize_detector_score(DetectorScore(
        DETECTOR_SCORE_SCHEMA, context.bundle.bundle_id, item.window.window_id, item.input_hash,
        outcome.raw_score, outcome.calibrated_score, str(context.bundle.score_direction), context.bundle.threshold_id,
        outcome.decision, outcome.latency_evidence_id, item.missingness_id, item.input_quality_id,
        context.profile_id, item.run_correlation_id, context.code_identity, context.runtime_identity,
        outcome.unavailability_reason_id,
    ))


def validate_physical_score_manifest(manifest: PhysicalScoreManifest, *, immutable_resolver: ImmutableResolver) -> BlindScoreValidation:
    """Require one immutable, accounted outcome per planned physical test window."""
    codes: list[str] = []
    if manifest.schema_version != PHYSICAL_SCORE_MANIFEST_SCHEMA:
        codes.append("PBS13_MANIFEST_SCHEMA_UNSUPPORTED")
    if manifest.authorization_effect != "none":
        codes.append("PBS13_MANIFEST_AUTHORIZATION_EFFECT_FORBIDDEN")
    if not manifest.planned_window_ids:
        codes.append("PBS13_MANIFEST_WINDOW_INVENTORY_EMPTY")
    windows = [score.window_id for score in manifest.scores]
    if len(windows) != len(set(windows)) or set(windows) != set(manifest.planned_window_ids):
        codes.append("PBS13_MANIFEST_WINDOW_CLOSURE_INCOMPLETE")
    all_ids = (manifest.bundle_id, manifest.partition_id, manifest.code_identity, manifest.runtime_identity,
               *manifest.resource_evidence_ids, *manifest.failure_evidence_ids)
    if not all(_resolves(value, immutable_resolver) for value in all_ids):
        codes.append("PBS13_MANIFEST_REFERENCE_UNRESOLVED")
    for score in manifest.scores:
        if score.schema_version != DETECTOR_SCORE_SCHEMA or score.score_id != detector_score_identity(score):
            codes.append("PBS13_SCORE_IMMUTABILITY_INVALID")
        if (score.bundle_id, score.code_identity, score.runtime_identity) != (manifest.bundle_id, manifest.code_identity, manifest.runtime_identity):
            codes.append("PBS13_SCORE_MANIFEST_BINDING_MISMATCH")
        unavailable = str(score.decision) in {ScoreDecision.UNAVAILABLE.value, ScoreDecision.INVALID.value}
        identities = (score.bundle_id, score.input_hash, score.threshold_id, score.missingness_id,
                      score.input_quality_id, score.profile_id, score.run_correlation_id,
                      score.code_identity, score.runtime_identity)
        if not all(_resolves(value, immutable_resolver) for value in identities):
            codes.append("PBS13_SCORE_REFERENCE_UNRESOLVED")
        if unavailable != (score.raw_score is None and score.calibrated_score is None) or (unavailable and not _resolves(score.unavailability_reason_id, immutable_resolver)):
            codes.append("PBS13_UNAVAILABLE_OUTCOME_INVALID")
        if not unavailable and (not score.raw_score or not score.calibrated_score or not _resolves(score.latency_evidence_id, immutable_resolver)):
            codes.append("PBS13_COMPLETE_SCORE_INVALID")
    if manifest.manifest_id != physical_score_manifest_identity(manifest):
        codes.append("PBS13_MANIFEST_IMMUTABILITY_INVALID")
    return _result(codes)
