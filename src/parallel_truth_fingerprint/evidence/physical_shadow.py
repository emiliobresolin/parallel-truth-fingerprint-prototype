"""Pure fail-closed admission and replay checks for the physical shadow path.

All model/feature work is injected.  This module has no I/O, training,
calibration, update, control, truth, promotion, or alias-resolution path.
"""
from __future__ import annotations

from dataclasses import dataclass, replace
from typing import Callable

from parallel_truth_fingerprint.contracts.detector_bundle import DetectorBundle
from parallel_truth_fingerprint.contracts.physical_blind_scores import (
    DETECTOR_SCORE_SCHEMA, DetectorScore, ScoreDecision, detector_score_identity,
    finalize_detector_score,
)
from parallel_truth_fingerprint.contracts.physical_shadow import (
    G5_QUALIFICATION_SCHEMA, G5Disposition, G5QualificationResult,
    PHYSICAL_SHADOW_SELECTION_SCHEMA, PhysicalShadowSelection,
    ShadowRouteDisposition, finalize_g5_qualification, finalize_physical_shadow_selection,
    g5_qualification_identity, physical_shadow_selection_identity,
)
from parallel_truth_fingerprint.contracts.scientific_governance import is_immutable_id
from parallel_truth_fingerprint.contracts.signal_observation import SignalObservation, parse_signal_observation
from parallel_truth_fingerprint.evidence.detector_bundle import ComponentResolver, DeclaredBundleEnvironment, load_detector_bundle


ImmutableResolver = Callable[[str], bool]
AuthorizationValidator = Callable[[str, str, str], bool]


@dataclass(frozen=True)
class ShadowValidation:
    accepted: bool
    diagnostic_codes: tuple[str, ...]
    authorization_effect: str = "none"


@dataclass(frozen=True)
class ShadowInferenceInput:
    window_id: str
    observations: tuple[SignalObservation, ...]
    input_hash: str
    missingness_id: str
    input_quality_id: str
    run_correlation_id: str
    failure_evidence_id: str | None = None


@dataclass(frozen=True)
class ShadowInferenceOutput:
    raw_score: str | None
    calibrated_score: str | None
    decision: ScoreDecision | str
    latency_evidence_id: str | None
    unavailability_reason_id: str | None = None


@dataclass(frozen=True)
class ShadowServingResult:
    score: DetectorScore | None
    disposition: ShadowRouteDisposition | str
    diagnostic_codes: tuple[str, ...]
    authorization_effect: str = "none"


@dataclass(frozen=True)
class G5RouteDecision:
    disposition: ShadowRouteDisposition | str
    selected_identity: str | None
    reason_ids: tuple[str, ...]
    authorization_effect: str = "none"


Predictor = Callable[[ShadowInferenceInput], ShadowInferenceOutput]


def _ids_are_resolved(values: tuple[str | None, ...], resolver: ImmutableResolver) -> bool:
    return all(is_immutable_id(value) and resolver(value) for value in values)


def _validation(codes: list[str]) -> ShadowValidation:
    codes = sorted(set(codes))
    return ShadowValidation(not codes, tuple(codes))


def validate_physical_shadow_selection(selection: PhysicalShadowSelection, bundle: DetectorBundle, *,
                                       environment: DeclaredBundleEnvironment,
                                       component_resolver: ComponentResolver,
                                       immutable_resolver: ImmutableResolver,
                                       authorization_validator: AuthorizationValidator) -> ShadowValidation:
    """Validate one exact selection.  A missing prerequisite is never replaced."""
    codes: list[str] = []
    if selection.schema_version != PHYSICAL_SHADOW_SELECTION_SCHEMA:
        codes.append("PS13_SCHEMA_UNSUPPORTED")
    if selection.authorization_effect != "none":
        codes.append("PS13_AUTHORIZATION_EFFECT_FORBIDDEN")
    if selection.selection_id != physical_shadow_selection_identity(selection):
        codes.append("PS13_SELECTION_ID_MISMATCH")
    load = load_detector_bundle(bundle, environment=environment, component_resolver=component_resolver)
    codes.extend(load.diagnostic_codes)
    if selection.bundle_id != bundle.bundle_id:
        codes.append("PS13_BUNDLE_MISMATCH")
    expected = (bundle.feature_schema_id, bundle.preprocessing_state_id, bundle.threshold_id,
                bundle.code_identity, bundle.dependency_lock_sha256, bundle.runtime_identity)
    actual = (selection.feature_schema_id, selection.preprocessing_id, selection.threshold_id,
              selection.code_identity, selection.dependency_lock_sha256, selection.runtime_identity)
    if actual != expected:
        codes.append("PS13_DECLARED_ENVIRONMENT_MISMATCH")
    identities = (selection.selection_id, selection.bundle_id, selection.profile_id,
                  selection.parameter_set_id, selection.feature_schema_id, selection.preprocessing_id,
                  selection.threshold_id, selection.code_identity, selection.dependency_lock_sha256,
                  selection.runtime_identity, selection.authorization_id)
    if not _ids_are_resolved(identities, immutable_resolver):
        codes.append("PS13_IDENTITY_UNRESOLVED")
    if not authorization_validator("shadow_serving", selection.authorization_id, selection.bundle_id):
        codes.append("PS13_AUTHORIZATION_DENIED")
    return _validation(codes)


def serve_physical_shadow(selection: PhysicalShadowSelection, bundle: DetectorBundle, item: ShadowInferenceInput, *,
                          environment: DeclaredBundleEnvironment, component_resolver: ComponentResolver,
                          immutable_resolver: ImmutableResolver, authorization_validator: AuthorizationValidator,
                          predictor: Predictor) -> ShadowServingResult:
    """Emit a score only after exact admission; otherwise retain explicit unavailability."""
    codes = list(validate_physical_shadow_selection(selection, bundle, environment=environment,
        component_resolver=component_resolver, immutable_resolver=immutable_resolver,
        authorization_validator=authorization_validator).diagnostic_codes)
    if not item.observations:
        codes.append("PS13_INPUT_STREAM_ABSENT")
    for observation in item.observations:
        try:
            parsed = parse_signal_observation(observation.to_dict())
            if parsed.to_dict()["profile_binding"]["profile_id"] != selection.profile_id:
                codes.append("PS13_INPUT_PROFILE_MISMATCH")
        except Exception:
            codes.append("PS13_INPUT_SIGNALOBSERVATION_INVALID")
    if not _ids_are_resolved((item.window_id, item.input_hash, item.missingness_id, item.input_quality_id,
                              item.run_correlation_id), immutable_resolver):
        codes.append("PS13_INPUT_IDENTITY_UNRESOLVED")
    if codes:
        reason = item.failure_evidence_id if is_immutable_id(item.failure_evidence_id) and immutable_resolver(item.failure_evidence_id) else None
        score = None if not is_immutable_id(bundle.bundle_id) else finalize_detector_score(DetectorScore(
            DETECTOR_SCORE_SCHEMA, bundle.bundle_id, item.window_id, item.input_hash, None, None,
            str(bundle.score_direction), bundle.threshold_id, ScoreDecision.UNAVAILABLE, None,
            item.missingness_id, item.input_quality_id, selection.profile_id, item.run_correlation_id,
            selection.code_identity, selection.runtime_identity, reason))
        return ShadowServingResult(score, ShadowRouteDisposition.BLOCKED, tuple(sorted(set(codes))))
    output = predictor(item)
    unavailable = str(output.decision) in {ScoreDecision.UNAVAILABLE.value, ScoreDecision.INVALID.value}
    valid = ((unavailable and output.raw_score is None and output.calibrated_score is None
              and _ids_are_resolved((output.unavailability_reason_id,), immutable_resolver)) or
             (not unavailable and str(output.decision) in {ScoreDecision.NORMAL.value, ScoreDecision.ANOMALOUS.value}
              and output.raw_score is not None and output.calibrated_score is not None
              and _ids_are_resolved((output.latency_evidence_id,), immutable_resolver)))
    if not valid:
        return ShadowServingResult(None, ShadowRouteDisposition.BLOCKED, ("PS13_PREDICTOR_OUTPUT_INVALID",))
    score = finalize_detector_score(DetectorScore(DETECTOR_SCORE_SCHEMA, bundle.bundle_id, item.window_id,
        item.input_hash, output.raw_score, output.calibrated_score, str(bundle.score_direction), bundle.threshold_id,
        output.decision, output.latency_evidence_id, item.missingness_id, item.input_quality_id,
        selection.profile_id, item.run_correlation_id, selection.code_identity, selection.runtime_identity,
        output.unavailability_reason_id))
    return ShadowServingResult(score, ShadowRouteDisposition.ELIGIBLE, ())


def qualify_g5_replay(selection: PhysicalShadowSelection, batch_scores: tuple[DetectorScore, ...],
                      shadow_scores: tuple[DetectorScore, ...], *, tolerance_id: str | None,
                      immutable_resolver: ImmutableResolver) -> G5QualificationResult:
    """Compare supplied immutable fixtures exactly; discrepancies remain visible."""
    diagnostics: list[str] = []
    discrepancies: list[str] = []
    if (selection.selection_id != physical_shadow_selection_identity(selection)
            or not _ids_are_resolved((selection.selection_id, selection.bundle_id, tolerance_id), immutable_resolver)):
        diagnostics.append("G5_TOLERANCE_OR_SELECTION_UNRESOLVED")
    batch = {score.window_id: score for score in batch_scores}
    shadow = {score.window_id: score for score in shadow_scores}
    if not batch or set(batch) != set(shadow) or len(batch) != len(batch_scores) or len(shadow) != len(shadow_scores):
        diagnostics.append("G5_SCORE_INVENTORY_MISMATCH")
    for window in sorted(set(batch).intersection(shadow)):
        left, right = batch[window], shadow[window]
        for score in (left, right):
            if score.schema_version != DETECTOR_SCORE_SCHEMA or score.score_id != detector_score_identity(score):
                diagnostics.append("G5_SCORE_ID_INVALID")
            if (score.bundle_id, score.profile_id, score.code_identity, score.runtime_identity) != (
                    selection.bundle_id, selection.profile_id, selection.code_identity, selection.runtime_identity):
                diagnostics.append("G5_SCORE_SELECTION_MISMATCH")
        if (left.bundle_id, left.input_hash, left.raw_score, left.calibrated_score, left.decision,
            left.threshold_id, left.score_direction) != (right.bundle_id, right.input_hash, right.raw_score,
            right.calibrated_score, right.decision, right.threshold_id, right.score_direction):
            diagnostics.append("G5_REPLAY_MISMATCH")
            discrepancies.extend(value for value in (left.score_id, right.score_id) if is_immutable_id(value))
    disposition = G5Disposition.QUALIFIED if not diagnostics else G5Disposition.NOT_QUALIFIED
    result = G5QualificationResult(G5_QUALIFICATION_SCHEMA, selection.selection_id, selection.bundle_id,
        tuple(score.score_id for score in batch_scores), tuple(score.score_id for score in shadow_scores), tolerance_id,
        tuple(discrepancies), disposition, tuple(diagnostics))
    return finalize_g5_qualification(result)


def decide_g5_shadow_route(candidate: PhysicalShadowSelection, qualification: G5QualificationResult, *,
                           last_verified_selection: PhysicalShadowSelection | None,
                           immutable_resolver: ImmutableResolver) -> G5RouteDecision:
    """Pick only an explicit qualified identity, otherwise explicit rollback/block."""
    qualified = (qualification.schema_version == G5_QUALIFICATION_SCHEMA and
                 qualification.result_id == g5_qualification_identity(qualification) and
                 str(qualification.disposition) == G5Disposition.QUALIFIED.value and
                 qualification.selection_id == candidate.selection_id and
                 qualification.bundle_id == candidate.bundle_id and not qualification.discrepancy_ids and
                 _ids_are_resolved((candidate.selection_id, qualification.result_id), immutable_resolver))
    if qualified:
        return G5RouteDecision(ShadowRouteDisposition.ELIGIBLE, candidate.selection_id, ())
    if last_verified_selection is not None and _ids_are_resolved((last_verified_selection.selection_id,), immutable_resolver):
        return G5RouteDecision(ShadowRouteDisposition.ROLLED_BACK, last_verified_selection.selection_id,
                               (qualification.result_id,) if is_immutable_id(qualification.result_id) else ())
    return G5RouteDecision(ShadowRouteDisposition.BLOCKED, None,
                           (qualification.result_id,) if is_immutable_id(qualification.result_id) else ())
