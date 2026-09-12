"""Fail-closed, side-effect-free reference boundary for Consensus.v2.

The v2 input contract carries immutable observation references, not values or
eligibility evidence.  Its parameter counterpart carries evidence identities,
not numeric values or an executable operation.  This module never fabricates a
residual, ranking, exclusion, or decision from defaults, floats, or v1 state.
"""
from __future__ import annotations

from dataclasses import dataclass
from decimal import Decimal
from enum import StrEnum

from parallel_truth_fingerprint.consensus_v2_parameters import ConsensusParameterSet, ConsensusParameterValidationResult
from parallel_truth_fingerprint.contracts.consensus_v2 import (
    ConsensusDecisionV2, ConsensusRoundInputV2, consensus_decision_content_id,
)
from parallel_truth_fingerprint.evidence.consensus_contract_validation import ConsensusContractValidation
from parallel_truth_fingerprint.consensus_v2.reference_inputs import (
    ConsensusEvaluationObservationV2, ConsensusOperationClosureV2, exact_decimal,
)


class ConsensusReferenceStatus(StrEnum):
    BLOCKED = "blocked"
    EVALUATED = "evaluated"


@dataclass(frozen=True)
class ConsensusReferenceTrace:
    """Bounded public trace: blocked pre-evaluation has no operation events."""
    round_input_id: str
    parameter_set_id: str
    events: tuple[tuple[str, str], ...]
    authorization_effect: str = "none"


@dataclass(frozen=True)
class ConsensusReferenceEvaluation:
    """Result that cannot be confused with a consensus decision."""
    status: ConsensusReferenceStatus
    decision: ConsensusDecisionV2 | None
    diagnostics: tuple[str, ...]
    trace: ConsensusReferenceTrace
    authorization_effect: str = "none"


def evaluate_consensus_v2_reference(
    round_input: ConsensusRoundInputV2,
    parameter_set: ConsensusParameterSet,
    contract_validation: ConsensusContractValidation,
    parameter_validation: ConsensusParameterValidationResult,
    operation: ConsensusOperationClosureV2 | None = None,
    observations: tuple[ConsensusEvaluationObservationV2, ...] = (),
) -> ConsensusReferenceEvaluation:
    """Deterministically refuse evaluation without a closed public operation.

    Explicit validation results keep this isolated module from resolving
    evidence, accepting injected execution, or performing I/O.  Current v2
    declarations provide neither an immutable numeric observation projection,
    per-observation eligibility evidence, canonical operation body/conformance
    vector, nor a trace budget.  Evaluating would require invention.
    """
    input_id = round_input.to_dict()["input_content_id"]
    diagnostics = list(contract_validation.diagnostics)
    diagnostics.extend(item.rule_id for item in parameter_validation.violations)
    if not contract_validation.valid:
        diagnostics.append("CV2_REFERENCE_CONTRACT_BLOCKED")
    if parameter_validation.status != "valid":
        diagnostics.append("CV2_REFERENCE_PARAMETER_BLOCKED")
    if operation is None or not observations:
        diagnostics.append("CV2_REFERENCE_OPERATION_INPUT_UNAVAILABLE")
    if diagnostics:
        return ConsensusReferenceEvaluation(
            status=ConsensusReferenceStatus.BLOCKED, decision=None,
            diagnostics=tuple(sorted(set(diagnostics))),
            trace=ConsensusReferenceTrace(input_id, parameter_set.parameter_set_id, ()),
        )
    data = round_input.to_dict()
    if (getattr(parameter_set, "comparison_basis_id", None) != data["comparison_basis"]["basis_id"] or
            getattr(parameter_set, "profile_id", None) not in data["comparison_basis"]["profile_ids"] or
            getattr(parameter_set, "quality_policy_id", None) not in data["quality_policy_ids"] or
            getattr(parameter_set, "residual_policy_id", None) != operation.operation_id or
            getattr(parameter_set, "residual_policy_canonical_bytes_sha256", None) != operation.canonical_bytes_hash or
            getattr(parameter_set, "residual_policy_conformance_id", None) != operation.conformance_vector_hash):
        diagnostics.append("CV2_REFERENCE_OPERATION_PARAMETER_CLOSURE")
    input_rows = {item["edge_id"]: item for item in data["observations"]}
    provided = {item.edge_id: item for item in observations}
    if len(provided) != len(observations) or set(provided) != set(input_rows):
        diagnostics.append("CV2_REFERENCE_PROJECTION_CLOSURE")
    for edge_id, projection in provided.items():
        source = input_rows.get(edge_id)
        if source is None or any(source[name] != getattr(projection, name) for name in ("observation_id", "observation_canonical_hash")):
            diagnostics.append("CV2_REFERENCE_PROJECTION_BINDING")
    event_count = len(observations) + 1
    if event_count > operation.trace_max_events:
        diagnostics.append("CV2_REFERENCE_TRACE_BUDGET_EXCEEDED")
    if diagnostics:
        return ConsensusReferenceEvaluation(ConsensusReferenceStatus.BLOCKED, None, tuple(sorted(set(diagnostics))), ConsensusReferenceTrace(input_id, parameter_set.parameter_set_id, ()))
    excluded = {item.edge_id: (item.eligibility_reason_id, item.eligibility_evidence_id) for item in observations if item.eligibility_reason_id is not None}
    eligible = [item for item in observations if item.eligibility_reason_id is None]
    values = {item.edge_id: exact_decimal(item.current_value) for item in eligible}
    if eligible:
        mean = sum(values.values(), Decimal("0")) / Decimal(len(values))
        for edge_id, value in values.items():
            if abs(value - mean) > exact_decimal(operation.max_abs_residual):
                source = provided[edge_id]
                excluded[edge_id] = (operation.exclusion_reason_ids["residual"], source.eligibility_evidence_id)
    included = tuple(sorted(set(values) - set(excluded)))
    trace_events = tuple(("observation", edge_id) for edge_id in sorted(provided)) + (("operation", operation.operation_id),)
    participant_ids = tuple(sorted(provided))
    if len(included) < operation.minimum_participants:
        excluded = {edge_id: (operation.exclusion_reason_ids["no_ranking"], provided[edge_id].eligibility_evidence_id) for edge_id in participant_ids}
        included, ranking, outcome, decision_diagnostics = (), (), "failure", ("no_ranking", "CV2_OPERATION:" + operation.operation_id)
    else:
        ranking = tuple(sorted(included, key=lambda edge_id: (abs(values[edge_id] - mean), edge_id)))
        outcome, decision_diagnostics = "success", ("CV2_OPERATION:" + operation.operation_id,)
    decision_payload = {"schema_version": "Consensus.v2", "round_input_id": input_id, "round_input_hash": input_id,
        "comparison_basis": data["comparison_basis"], "outcome": outcome, "participant_ids": list(participant_ids),
        "included_ids": list(included), "excluded": [{"edge_id": edge_id, "reason_id": excluded[edge_id][0], "evidence_ids": [excluded[edge_id][1]]} for edge_id in sorted(excluded)],
        "ranking": list(ranking), "diagnostics": list(decision_diagnostics), "decision_content_id": "", "authorization_effect": "none"}
    decision_payload["decision_content_id"] = consensus_decision_content_id(decision_payload)
    return ConsensusReferenceEvaluation(
        status=ConsensusReferenceStatus.EVALUATED,
        decision=ConsensusDecisionV2(decision_payload), diagnostics=(),
        trace=ConsensusReferenceTrace(input_id, parameter_set.parameter_set_id, trace_events),
    )
