"""Pure fail-closed validation for Story 13.3 candidate comparisons."""
from __future__ import annotations

from dataclasses import dataclass, replace
from typing import Callable

from parallel_truth_fingerprint.contracts.physical_candidate_comparison import (
    PHYSICAL_CANDIDATE_COMPARISON_SCHEMA, CandidateRunStatus, ComparisonDisposition,
    FrozenPhysicalComparisonPlan, PhysicalCandidateComparisonRecord,
    physical_comparison_plan_content_id, physical_comparison_record_content_id,
)
from parallel_truth_fingerprint.contracts.scientific_governance import is_immutable_id


ImmutableResolver = Callable[[str], bool]


@dataclass(frozen=True)
class PhysicalComparisonValidation:
    valid: bool
    disposition: ComparisonDisposition
    diagnostic_codes: tuple[str, ...]
    authorization_effect: str = "none"


def _ids_resolve(values: tuple[str, ...], resolver: ImmutableResolver) -> bool:
    return bool(values) and all(is_immutable_id(value) and resolver(value) for value in values)


def validate_frozen_physical_comparison_plan(plan: FrozenPhysicalComparisonPlan, *, immutable_resolver: ImmutableResolver) -> PhysicalComparisonValidation:
    """Validate a preregistered plan without fitting, resolving data, or publishing."""
    codes: list[str] = []
    if plan.schema_version != PHYSICAL_CANDIDATE_COMPARISON_SCHEMA:
        codes.append("PCC13_SCHEMA_UNSUPPORTED")
    common = (plan.protocol_id, plan.feature_schema_id, plan.partition_id, plan.preprocessing_state_id,
              plan.normal_training_evidence_id, plan.validation_evidence_id, plan.resource_budget_id,
              plan.tuning_access_id, plan.selection_rule_id, *plan.primary_metric_ids, *plan.repetition_ids)
    if not _ids_resolve(common, immutable_resolver):
        codes.append("PCC13_COMMON_INPUT_UNRESOLVED")
    candidate_ids = [candidate.candidate_id for candidate in plan.candidates]
    families = {str(candidate.family) for candidate in plan.candidates}
    required = {"lstm_ae", "gru_ae", "transparent_baseline"}
    if len(candidate_ids) != len(set(candidate_ids)) or not required.issubset(families):
        codes.append("PCC13_REQUIRED_CANDIDATES_MISSING")
    for candidate in plan.candidates:
        if str(candidate.family) not in required:
            codes.append("PCC13_CANDIDATE_FAMILY_UNDECLARED")
        if not _ids_resolve((candidate.candidate_id, candidate.architecture_identity, candidate.parameter_set_id,
                             candidate.configuration_id, *candidate.preregistered_exception_ids), immutable_resolver):
            codes.append("PCC13_CANDIDATE_IDENTITY_UNRESOLVED")
    if plan.authorization_effect != "none" or plan.plan_content_id != physical_comparison_plan_content_id(plan):
        codes.append("PCC13_PLAN_IMMUTABILITY_INVALID")
    codes = sorted(set(codes))
    return PhysicalComparisonValidation(not codes, ComparisonDisposition.COMPLETE if not codes else ComparisonDisposition.INVALID, tuple(codes))


def validate_physical_candidate_comparison(record: PhysicalCandidateComparisonRecord, *, plan: FrozenPhysicalComparisonPlan,
                                            immutable_resolver: ImmutableResolver) -> PhysicalComparisonValidation:
    """Validate complete planned-run retention and pre-calibration selection.

    The caller supplies only immutable identities.  Any test, calibration, or
    truth reference is structurally absent from these contracts and cannot be
    accepted as a substitute for the frozen validation-only protocol.
    """
    plan_result = validate_frozen_physical_comparison_plan(plan, immutable_resolver=immutable_resolver)
    codes = list(plan_result.diagnostic_codes)
    if record.schema_version != PHYSICAL_CANDIDATE_COMPARISON_SCHEMA or record.plan_content_id != plan.plan_content_id:
        codes.append("PCC13_PLAN_BINDING_INVALID")
    expected = {(candidate.candidate_id, repetition) for candidate in plan.candidates for repetition in plan.repetition_ids}
    actual = {(run.candidate_id, run.repetition_id) for run in record.run_records}
    if len(actual) != len(record.run_records) or actual != expected:
        codes.append("PCC13_PLANNED_RUN_CLOSURE_INCOMPLETE")
    candidate_config = {candidate.candidate_id: candidate.configuration_id for candidate in plan.candidates}
    candidate_exceptions = {candidate.candidate_id: candidate.preregistered_exception_ids for candidate in plan.candidates}
    shared = (plan.feature_schema_id, plan.partition_id, plan.preprocessing_state_id,
              plan.normal_training_evidence_id, plan.validation_evidence_id, plan.tuning_access_id, plan.resource_budget_id)
    valid_status = {item.value for item in CandidateRunStatus}
    for run in record.run_records:
        if (run.feature_schema_id, run.partition_id, run.preprocessing_state_id, run.normal_training_evidence_id,
                run.validation_evidence_id, run.tuning_access_id, run.resource_budget_id) != shared:
            codes.append("PCC13_FAIR_INPUT_MISMATCH")
        if candidate_config.get(run.candidate_id) != run.configuration_id:
            codes.append("PCC13_CONFIGURATION_MISMATCH")
        if tuple(run.applied_exception_ids) != tuple(candidate_exceptions.get(run.candidate_id, ())):
            codes.append("PCC13_EXCEPTION_REGISTRATION_MISMATCH")
        if str(run.status) not in valid_status:
            codes.append("PCC13_RUN_STATUS_UNDECLARED")
        evidence = (*run.output_ids, *run.resource_evidence_ids, *run.diagnostic_ids, *run.limitation_ids, *run.applied_exception_ids)
        if not _ids_resolve(evidence, immutable_resolver):
            codes.append("PCC13_RUN_EVIDENCE_UNRESOLVED")
    planned_candidates = set(candidate_config)
    completed = {run.candidate_id for run in record.run_records if str(run.status) == CandidateRunStatus.COMPLETE.value}
    if record.selected_candidate_id is not None:
        if record.selected_candidate_id not in planned_candidates or record.selected_candidate_id not in completed:
            codes.append("PCC13_SELECTION_CANDIDATE_INVALID")
        if not _ids_resolve((record.selection_record_id or "",), immutable_resolver):
            codes.append("PCC13_SELECTION_EVIDENCE_UNRESOLVED")
        if set(record.non_selected_candidate_ids) != planned_candidates - {record.selected_candidate_id}:
            codes.append("PCC13_NONSELECTED_OUTCOMES_INCOMPLETE")
    elif record.selection_record_id is not None or record.non_selected_candidate_ids:
        codes.append("PCC13_SELECTION_STATE_INCONSISTENT")
    if record.authorization_effect != "none" or record.record_content_id != physical_comparison_record_content_id(record):
        codes.append("PCC13_RECORD_IMMUTABILITY_INVALID")
    codes = sorted(set(codes))
    if codes:
        disposition = ComparisonDisposition.INVALID
    elif record.selected_candidate_id is None:
        disposition = ComparisonDisposition.INCOMPLETE
    else:
        disposition = ComparisonDisposition.COMPLETE
    if str(record.disposition) != disposition.value:
        codes = sorted(set((*codes, "PCC13_DISPOSITION_MISMATCH")))
        disposition = ComparisonDisposition.INVALID
    return PhysicalComparisonValidation(not codes, disposition, tuple(codes))


def finalize_physical_candidate_comparison(record: PhysicalCandidateComparisonRecord, *, plan: FrozenPhysicalComparisonPlan,
                                            immutable_resolver: ImmutableResolver) -> PhysicalCandidateComparisonRecord:
    """Return an immutable, diagnostic-complete record; never performs model work."""
    provisional = replace(record, record_content_id="")
    provisional = replace(provisional, record_content_id=physical_comparison_record_content_id(provisional))
    validation = validate_physical_candidate_comparison(provisional, plan=plan, immutable_resolver=immutable_resolver)
    disposition = validation.disposition
    provisional = replace(provisional, disposition=disposition, diagnostic_codes=validation.diagnostic_codes)
    return replace(provisional, record_content_id=physical_comparison_record_content_id(provisional))
