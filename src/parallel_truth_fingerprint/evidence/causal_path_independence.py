"""Pure, injected causal-path independence assessment for Story 12.5.

The assessor evaluates retained identity-only traces.  It does not exercise an
OPC client, contact a server, run consensus, read a cache, or publish evidence.
"""
from __future__ import annotations

from dataclasses import replace
from typing import Callable

from parallel_truth_fingerprint.contracts.causal_path_independence import (
    CAUSAL_PATH_INDEPENDENCE_SCHEMA, CausalCheckDisposition,
    CausalIndependenceDisposition, CausalPathCase, CausalPathCheck,
    CausalPathIndependenceResult, CausalPathTrace, CausalVariation,
    OpcEvidenceState, causal_path_independence_content_id,
)
from parallel_truth_fingerprint.contracts.scientific_governance import is_immutable_id


ImmutableResolver = Callable[[str], bool]
_REQUIRED_VARIATIONS = frozenset(item.value for item in CausalVariation)
_NO_FALLBACK = "none"


def _check(case_id: str, disposition: CausalCheckDisposition, *codes: str, evidence: tuple[str, ...] = ()) -> CausalPathCheck:
    return CausalPathCheck(case_id, disposition, codes, evidence)


def _trace_ids(trace: CausalPathTrace) -> tuple[str | None, ...]:
    return (
        trace.trace_id, trace.snapshot_id, trace.writer_id, trace.server_id,
        trace.client_id, trace.opc_condition_id, trace.opc_observation_id,
        trace.consensus_configuration_id, trace.consensus_input_id,
        trace.consensus_decision_id, trace.comparison_id,
        trace.opc_lineage_snapshot_id, trace.consensus_lineage_snapshot_id,
    )


def _trace_errors(trace: CausalPathTrace, resolver: ImmutableResolver) -> tuple[CausalCheckDisposition | None, tuple[str, ...]]:
    values = tuple(value for value in _trace_ids(trace) if value is not None)
    if any(not is_immutable_id(value) for value in values):
        return CausalCheckDisposition.INCOMPLETE, ("CPI_TRACE_ID_MISSING",)
    if any(not resolver(value) for value in values):
        return CausalCheckDisposition.BLOCKED, ("CPI_TRACE_ID_UNRESOLVED",)
    if str(trace.opc_evidence_state) not in {item.value for item in OpcEvidenceState}:
        return CausalCheckDisposition.INCOMPLETE, ("CPI_OPC_STATE_UNKNOWN",)
    if trace.opc_fallback_kind != _NO_FALLBACK:
        return CausalCheckDisposition.FAIL, ("CPI_OPC_FALLBACK_USED",)
    state = str(trace.opc_evidence_state)
    evidence_present = trace.opc_observation_id is not None
    if state in {OpcEvidenceState.AVAILABLE.value, OpcEvidenceState.NEWLY_READ.value}:
        if not trace.opc_evidence_valid or not evidence_present:
            return CausalCheckDisposition.FAIL, ("CPI_OPC_VALID_EVIDENCE_INCOHERENT",)
    elif trace.opc_evidence_valid or evidence_present:
        return CausalCheckDisposition.FAIL, ("CPI_OPC_UNAVAILABLE_EVIDENCE_FABRICATED",)
    if trace.opc_lineage_snapshot_id != trace.snapshot_id or trace.consensus_lineage_snapshot_id != trace.snapshot_id:
        return CausalCheckDisposition.FAIL, ("CPI_COMMON_SOURCE_LINEAGE_BROKEN",)
    return None, ()


def _case_check(case: CausalPathCase, resolver: ImmutableResolver) -> CausalPathCheck:
    if not is_immutable_id(case.case_id) or not case.transition_evidence_ids:
        return _check(case.case_id, CausalCheckDisposition.INCOMPLETE, "CPI_CASE_EVIDENCE_MISSING")
    all_ids = (*case.transition_evidence_ids, *tuple(value for trace in (case.baseline, case.varied) for value in _trace_ids(trace) if value is not None))
    if any(not is_immutable_id(value) for value in all_ids):
        return _check(case.case_id, CausalCheckDisposition.INCOMPLETE, "CPI_CASE_ID_MISSING", evidence=tuple(value for value in all_ids if value))
    if any(not resolver(value) for value in all_ids):
        return _check(case.case_id, CausalCheckDisposition.BLOCKED, "CPI_CASE_ID_UNRESOLVED", evidence=all_ids)
    for trace in (case.baseline, case.varied):
        disposition, codes = _trace_errors(trace, resolver)
        if disposition is not None:
            return _check(case.case_id, disposition, *codes, evidence=all_ids)
    variation = str(case.variation)
    base, varied = case.baseline, case.varied
    if variation == CausalVariation.CONSENSUS_ONLY.value:
        if base.snapshot_id != varied.snapshot_id or base.opc_observation_id != varied.opc_observation_id:
            return _check(case.case_id, CausalCheckDisposition.FAIL, "CPI_CONSENSUS_CHANGE_LEAKED_TO_OPC", evidence=all_ids)
        if base.consensus_configuration_id == varied.consensus_configuration_id and base.consensus_input_id == varied.consensus_input_id:
            return _check(case.case_id, CausalCheckDisposition.INCOMPLETE, "CPI_CONSENSUS_VARIATION_NOT_OBSERVED", evidence=all_ids)
    elif variation == CausalVariation.OPC_ONLY.value:
        if (base.snapshot_id != varied.snapshot_id or base.consensus_configuration_id != varied.consensus_configuration_id
                or base.consensus_input_id != varied.consensus_input_id or base.consensus_decision_id != varied.consensus_decision_id):
            return _check(case.case_id, CausalCheckDisposition.FAIL, "CPI_OPC_CHANGE_LEAKED_TO_CONSENSUS", evidence=all_ids)
        if base.opc_condition_id == varied.opc_condition_id:
            return _check(case.case_id, CausalCheckDisposition.INCOMPLETE, "CPI_OPC_VARIATION_NOT_OBSERVED", evidence=all_ids)
    elif variation == CausalVariation.COMMON_SOURCE.value:
        if base.snapshot_id == varied.snapshot_id:
            return _check(case.case_id, CausalCheckDisposition.INCOMPLETE, "CPI_COMMON_SOURCE_VARIATION_NOT_OBSERVED", evidence=all_ids)
    elif variation == CausalVariation.OPC_UNAVAILABLE.value:
        if str(varied.opc_evidence_state) not in {OpcEvidenceState.UNAVAILABLE.value, OpcEvidenceState.DELAYED.value, OpcEvidenceState.NEWLY_READ.value}:
            return _check(case.case_id, CausalCheckDisposition.FAIL, "CPI_OPC_OUTAGE_STATE_UNDECLARED", evidence=all_ids)
        if (base.snapshot_id != varied.snapshot_id or base.consensus_configuration_id != varied.consensus_configuration_id
                or base.consensus_input_id != varied.consensus_input_id or base.consensus_decision_id != varied.consensus_decision_id):
            return _check(case.case_id, CausalCheckDisposition.FAIL, "CPI_OPC_OUTAGE_LEAKED_TO_CONSENSUS", evidence=all_ids)
    else:
        return _check(case.case_id, CausalCheckDisposition.INCOMPLETE, "CPI_VARIATION_UNKNOWN", evidence=all_ids)
    return _check(case.case_id, CausalCheckDisposition.PASS, evidence=all_ids)


def assess_causal_path_independence(cases: tuple[CausalPathCase, ...], *, immutable_resolver: ImmutableResolver,
                                    limitations: tuple[str, ...] = ()) -> CausalPathIndependenceResult:
    """Assess a complete controlled matrix without issuing qualification authority."""
    checks = [_case_check(case, immutable_resolver) for case in cases]
    kinds = [str(case.variation) for case in cases]
    if len(kinds) != len(set(kinds)):
        checks.append(_check("matrix_coverage", CausalCheckDisposition.INCOMPLETE, "CPI_VARIATION_DUPLICATE"))
    missing = _REQUIRED_VARIATIONS.difference(kinds)
    if missing:
        checks.append(_check("matrix_coverage", CausalCheckDisposition.INCOMPLETE, "CPI_VARIATION_COVERAGE_MISSING"))
    dispositions = {str(item.disposition) for item in checks}
    if CausalCheckDisposition.INCOMPLETE.value in dispositions:
        result_disposition = CausalIndependenceDisposition.INCOMPLETE
    elif CausalCheckDisposition.BLOCKED.value in dispositions:
        result_disposition = CausalIndependenceDisposition.BLOCKED
    elif CausalCheckDisposition.FAIL.value in dispositions:
        result_disposition = CausalIndependenceDisposition.VIOLATED
    else:
        result_disposition = CausalIndependenceDisposition.DEMONSTRATED
    canonical_limitations = (
        "Demonstrates controlled logical and transport-path independence only; it does not demonstrate independent physical instrumentation, plant redundancy, or real-world SCADA validation.",
        *limitations,
    )
    provisional = CausalPathIndependenceResult(CAUSAL_PATH_INDEPENDENCE_SCHEMA, cases, tuple(checks), result_disposition, canonical_limitations, "")
    return replace(provisional, result_content_id=causal_path_independence_content_id(provisional))
