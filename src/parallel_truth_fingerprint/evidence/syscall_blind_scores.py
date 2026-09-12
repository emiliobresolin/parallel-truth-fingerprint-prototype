"""Pure fail-closed admission and scoring boundary for Story 14.7.

All inference is injected.  This module does not capture, read raw evidence,
fit or extend a vocabulary, tune/calibrate, access truth, publish, or do I/O.
"""
from __future__ import annotations

from dataclasses import dataclass, replace
from typing import Callable, Iterable

from parallel_truth_fingerprint.contracts.scientific_governance import is_immutable_id
from parallel_truth_fingerprint.contracts.syscall_blind_scores import (
    SYSCALL_DETECTOR_SCORE_SCHEMA, SYSCALL_SCORE_MANIFEST_SCHEMA,
    SyscallDetectorScore, SyscallScoreDecision, SyscallScoreManifest,
    finalize_syscall_detector_score, syscall_detector_score_identity,
    syscall_score_manifest_identity,
)
from parallel_truth_fingerprint.contracts.syscall_detector_bundle import SyscallDetectorBundle
from parallel_truth_fingerprint.evidence.syscall_partitions import (
    CategoricalSyscallWindow, SyscallPartition, SyscallPartitionRole,
    SyscallPreprocessingFit, validate_syscall_partition,
    validate_syscall_preprocessing_fit,
)


@dataclass(frozen=True)
class BlindSyscallScoringContext:
    bundle: SyscallDetectorBundle
    partition: SyscallPartition
    preprocessing: SyscallPreprocessingFit
    metric_policy_id: str
    capture_context_id: str
    code_identity: str
    runtime_identity: str
    authorization_id: str
    authorization_effect: str = "none"


@dataclass(frozen=True)
class SyscallInferenceInput:
    window: CategoricalSyscallWindow
    input_hash: str
    missingness_id: str
    capture_quality_id: str
    run_correlation_id: str
    workload_correlation_id: str
    failure_reason_id: str | None = None


@dataclass(frozen=True)
class SyscallInferenceResult:
    raw_score: str | None
    calibrated_score: str | None
    decision: SyscallScoreDecision | str
    latency_evidence_id: str | None
    unavailability_reason_id: str | None = None


@dataclass(frozen=True)
class BlindSyscallScoreValidation:
    accepted: bool
    diagnostic_codes: tuple[str, ...]
    authorization_effect: str = "none"


ImmutableResolver = Callable[[str], bool]
AuthorizationValidator = Callable[[str, str, str], bool]
Predictor = Callable[[SyscallInferenceInput], SyscallInferenceResult]


def _result(codes: Iterable[str]) -> BlindSyscallScoreValidation:
    ordered = tuple(sorted(set(codes)))
    return BlindSyscallScoreValidation(not ordered, ordered)


def _resolves(value: str | None, resolver: ImmutableResolver) -> bool:
    return is_immutable_id(value) and resolver(value)


def validate_blind_syscall_scoring_context(context: BlindSyscallScoringContext, *,
                                           immutable_resolver: ImmutableResolver,
                                           authorization_validator: AuthorizationValidator) -> BlindSyscallScoreValidation:
    """Check every pinned pre-truth prerequisite before an injected prediction."""
    codes: list[str] = []
    if context.authorization_effect != "none":
        codes.append("SBS14_CONTEXT_AUTHORIZATION_EFFECT_FORBIDDEN")
    try:
        context.bundle.validate()
    except ValueError:
        codes.append("SBS14_BUNDLE_INVALID")
    if not context.bundle.content_id or context.bundle.content_id != context.bundle.computed_id():
        codes.append("SBS14_BUNDLE_NOT_FROZEN")
    partition = validate_syscall_partition(context.partition, immutable_resolver=immutable_resolver)
    codes.extend(item.code for item in partition.diagnostics)
    fit = validate_syscall_preprocessing_fit(context.preprocessing, partition=context.partition,
                                             immutable_resolver=immutable_resolver)
    codes.extend(item.code for item in fit.diagnostics)
    test_members = [member for member in context.partition.members if str(member.role) == SyscallPartitionRole.TEST.value]
    if not test_members:
        codes.append("SBS14_TEST_PARTITION_MISSING")
    if (context.bundle.vocabulary_id, context.bundle.preprocessing_id) != (
            context.preprocessing.vocabulary_id, context.preprocessing.preprocessing_id):
        codes.append("SBS14_BUNDLE_PREPROCESSING_MISMATCH")
    if context.bundle.capture_policy_id != context.capture_context_id:
        codes.append("SBS14_CAPTURE_CONTEXT_MISMATCH")
    if (context.bundle.code_id, context.bundle.runtime_id) != (context.code_identity, context.runtime_identity):
        codes.append("SBS14_CODE_OR_RUNTIME_MISMATCH")
    identities = (context.bundle.content_id, context.metric_policy_id, context.capture_context_id,
                  context.code_identity, context.runtime_identity, context.authorization_id)
    if not all(_resolves(value, immutable_resolver) for value in identities):
        codes.append("SBS14_CONTEXT_IDENTITY_UNRESOLVED")
    if not authorization_validator("blind_syscall_scoring", context.authorization_id, context.partition.partition_id):
        codes.append("SBS14_AUTHORIZATION_DENIED")
    return _result(codes)


def _window_codes(context: BlindSyscallScoringContext, item: SyscallInferenceInput,
                  immutable_resolver: ImmutableResolver) -> list[str]:
    window = item.window
    codes: list[str] = []
    test_runs = {member.run_id for member in context.partition.members if str(member.role) == SyscallPartitionRole.TEST.value}
    if window.source_run_id not in test_runs or window.partition_id != context.partition.partition_id:
        codes.append("SBS14_WINDOW_NOT_ELIGIBLE_TEST")
    if (window.feature_schema_id, window.preprocessing_id) != (
            context.partition.feature_schema_id, context.bundle.preprocessing_id):
        codes.append("SBS14_WINDOW_COMPATIBILITY_MISMATCH")
    if window.authorization_effect != "none" or not window.window_id or not window.event_ids:
        codes.append("SBS14_WINDOW_SHAPE_INVALID")
    identities = (item.input_hash, item.missingness_id, item.capture_quality_id,
                  item.run_correlation_id, item.workload_correlation_id, window.source_run_id,
                  *window.event_ids, *window.batch_ids, *window.raw_segment_ids,
                  *window.quality_ids, *window.exclusion_ids)
    if not all(_resolves(value, immutable_resolver) for value in identities):
        codes.append("SBS14_INPUT_OR_CAPTURE_PROVENANCE_UNRESOLVED")
    return codes


def score_blind_syscall_window(context: BlindSyscallScoringContext, item: SyscallInferenceInput, *,
                               immutable_resolver: ImmutableResolver,
                               authorization_validator: AuthorizationValidator,
                               predictor: Predictor) -> SyscallDetectorScore:
    """Retain an immutable invalid/unavailable outcome instead of silently dropping it."""
    codes = list(validate_blind_syscall_scoring_context(
        context, immutable_resolver=immutable_resolver,
        authorization_validator=authorization_validator).diagnostic_codes)
    codes.extend(_window_codes(context, item, immutable_resolver))
    if codes:
        reason = next((candidate for candidate in (item.failure_reason_id, item.capture_quality_id,
                                                    item.missingness_id) if _resolves(candidate, immutable_resolver)), None)
        return finalize_syscall_detector_score(SyscallDetectorScore(
            SYSCALL_DETECTOR_SCORE_SCHEMA, context.bundle.content_id, item.window.window_id, item.input_hash,
            None, None, "higher_anomalous", context.bundle.threshold_id, SyscallScoreDecision.INVALID,
            None, item.missingness_id, item.capture_quality_id, context.capture_context_id,
            item.run_correlation_id, item.workload_correlation_id, context.code_identity,
            context.runtime_identity, reason,
        ))
    outcome = predictor(item)
    unavailable = str(outcome.decision) in {SyscallScoreDecision.UNAVAILABLE.value, SyscallScoreDecision.INVALID.value}
    if unavailable:
        outcome = replace(outcome, raw_score=None, calibrated_score=None)
    if ((not unavailable and (outcome.raw_score is None or outcome.calibrated_score is None)) or
            (unavailable and not _resolves(outcome.unavailability_reason_id, immutable_resolver)) or
            (not unavailable and str(outcome.decision) not in {SyscallScoreDecision.NORMAL.value, SyscallScoreDecision.ANOMALOUS.value})):
        outcome = SyscallInferenceResult(None, None, SyscallScoreDecision.INVALID,
                                         outcome.latency_evidence_id, item.failure_reason_id or item.capture_quality_id)
    return finalize_syscall_detector_score(SyscallDetectorScore(
        SYSCALL_DETECTOR_SCORE_SCHEMA, context.bundle.content_id, item.window.window_id, item.input_hash,
        outcome.raw_score, outcome.calibrated_score, "higher_anomalous", context.bundle.threshold_id,
        outcome.decision, outcome.latency_evidence_id, item.missingness_id, item.capture_quality_id,
        context.capture_context_id, item.run_correlation_id, item.workload_correlation_id,
        context.code_identity, context.runtime_identity, outcome.unavailability_reason_id,
    ))


def validate_syscall_score_manifest(manifest: SyscallScoreManifest, *,
                                    immutable_resolver: ImmutableResolver) -> BlindSyscallScoreValidation:
    """Require exact retained closure before a later evaluator may consume it."""
    codes: list[str] = []
    if manifest.schema_version != SYSCALL_SCORE_MANIFEST_SCHEMA:
        codes.append("SBS14_MANIFEST_SCHEMA_UNSUPPORTED")
    if manifest.authorization_effect != "none":
        codes.append("SBS14_MANIFEST_AUTHORIZATION_EFFECT_FORBIDDEN")
    if not manifest.planned_window_ids:
        codes.append("SBS14_MANIFEST_WINDOW_INVENTORY_EMPTY")
    windows = [score.window_id for score in manifest.scores]
    if len(windows) != len(set(windows)) or set(windows) != set(manifest.planned_window_ids):
        codes.append("SBS14_MANIFEST_WINDOW_CLOSURE_INCOMPLETE")
    identities = (manifest.bundle_id, manifest.partition_id, manifest.code_identity, manifest.runtime_identity,
                  *manifest.resource_evidence_ids, *manifest.failure_evidence_ids)
    if not all(_resolves(value, immutable_resolver) for value in identities):
        codes.append("SBS14_MANIFEST_REFERENCE_UNRESOLVED")
    for score in manifest.scores:
        if score.schema_version != SYSCALL_DETECTOR_SCORE_SCHEMA or score.score_id != syscall_detector_score_identity(score):
            codes.append("SBS14_SCORE_IMMUTABILITY_INVALID")
        if (score.bundle_id, score.code_identity, score.runtime_identity) != (
                manifest.bundle_id, manifest.code_identity, manifest.runtime_identity):
            codes.append("SBS14_SCORE_MANIFEST_BINDING_MISMATCH")
        unavailable = str(score.decision) in {SyscallScoreDecision.UNAVAILABLE.value, SyscallScoreDecision.INVALID.value}
        required = (score.bundle_id, score.input_hash, score.threshold_id, score.missingness_id,
                    score.capture_quality_id, score.capture_context_id, score.run_correlation_id,
                    score.workload_correlation_id, score.code_identity, score.runtime_identity)
        if not all(_resolves(value, immutable_resolver) for value in required):
            codes.append("SBS14_SCORE_REFERENCE_UNRESOLVED")
        if unavailable != (score.raw_score is None and score.calibrated_score is None) or (
                unavailable and not _resolves(score.unavailability_reason_id, immutable_resolver)):
            codes.append("SBS14_UNAVAILABLE_OUTCOME_INVALID")
        if not unavailable and (not score.raw_score or not score.calibrated_score or
                                not _resolves(score.latency_evidence_id, immutable_resolver)):
            codes.append("SBS14_COMPLETE_SCORE_INVALID")
    if manifest.manifest_id != syscall_score_manifest_identity(manifest):
        codes.append("SBS14_MANIFEST_IMMUTABILITY_INVALID")
    return _result(codes)
