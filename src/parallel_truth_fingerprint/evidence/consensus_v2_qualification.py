"""Pure G3 qualification of supplied Consensus.v2 evidence closures.

No resolver is implicit: callers provide an immutable-id resolver.  Missing
evidence is visible as incomplete and any bad result leaves v2 in shadow.
"""
from __future__ import annotations

from dataclasses import dataclass, replace
from typing import Callable

from parallel_truth_fingerprint.contracts.consensus_v2_qualification import (
    CONSENSUS_V2_QUALIFICATION_SCHEMA, ConsensusV2CheckDisposition,
    ConsensusV2QualificationCheck, ConsensusV2QualificationDisposition,
    ConsensusV2QualificationResult, consensus_v2_qualification_content_id,
)
from parallel_truth_fingerprint.contracts.scientific_governance import is_immutable_id


ImmutableResolver = Callable[[str], bool]
_REQUIRED_CASES = frozenset({"valid", "invalid", "missing", "stale", "mixed_profile", "mixed_unit", "boundary", "exclusion", "tie", "failure"})
_REQUIRED_CHECKS = ("python_go_parity", "abci_integration", "versioned_state", "sensitivity", "provenance")


@dataclass(frozen=True)
class ParityFixtureEvidence:
    fixture_id: str
    case_kind: str
    python_result_id: str | None
    go_result_id: str | None
    matched: bool | None
    mismatch_diagnostic_id: str | None = None


@dataclass(frozen=True)
class ConsensusV2QualificationInput:
    primary_configuration_id: str
    closure_ids: tuple[str, ...]
    parity_fixtures: tuple[ParityFixtureEvidence, ...]
    integration_evidence_id: str | None
    integration_used_real_boundary: bool | None
    state_evidence_id: str | None
    state_preserved: bool | None
    sensitivity_plan_id: str | None
    sensitivity_result_ids: tuple[str, ...]
    sensitivity_complete: bool | None
    provenance_ids: tuple[str, ...]
    provenance_complete: bool | None
    limitations: tuple[str, ...]


def _check(check_id: str, disposition: ConsensusV2CheckDisposition, *codes: str, evidence: tuple[str, ...] = ()) -> ConsensusV2QualificationCheck:
    return ConsensusV2QualificationCheck(check_id, disposition, evidence, codes)


def _resolved(value: str | None, resolver: ImmutableResolver) -> bool:
    return bool(value and is_immutable_id(value) and resolver(value))


def _parity_check(fixtures: tuple[ParityFixtureEvidence, ...], resolver: ImmutableResolver) -> ConsensusV2QualificationCheck:
    kinds = {item.case_kind for item in fixtures}
    evidence = tuple(item.fixture_id for item in fixtures)
    if not _REQUIRED_CASES.issubset(kinds):
        return _check("python_go_parity", ConsensusV2CheckDisposition.INCOMPLETE, "G3_PARITY_CASE_COVERAGE_MISSING", evidence=evidence)
    if len(fixtures) != len({item.fixture_id for item in fixtures}):
        return _check("python_go_parity", ConsensusV2CheckDisposition.FAIL, "G3_PARITY_FIXTURE_DUPLICATE", evidence=evidence)
    if any(not _resolved(item.fixture_id, resolver) for item in fixtures):
        return _check("python_go_parity", ConsensusV2CheckDisposition.BLOCKED, "G3_PARITY_FIXTURE_UNRESOLVED", evidence=evidence)
    for item in fixtures:
        if item.matched is None or item.python_result_id is None or item.go_result_id is None:
            return _check("python_go_parity", ConsensusV2CheckDisposition.INCOMPLETE, "G3_PARITY_RESULT_MISSING", evidence=evidence)
        if not _resolved(item.python_result_id, resolver) or not _resolved(item.go_result_id, resolver):
            return _check("python_go_parity", ConsensusV2CheckDisposition.BLOCKED, "G3_PARITY_RESULT_UNRESOLVED", evidence=evidence)
        if not item.matched and not _resolved(item.mismatch_diagnostic_id, resolver):
            return _check("python_go_parity", ConsensusV2CheckDisposition.BLOCKED, "G3_PARITY_MISMATCH_UNRETAINED", evidence=evidence)
        if not item.matched:
            return _check("python_go_parity", ConsensusV2CheckDisposition.FAIL, "G3_PARITY_MISMATCH", evidence=evidence)
    return _check("python_go_parity", ConsensusV2CheckDisposition.PASS, evidence=evidence)


def _evidence_boolean(check_id: str, evidence_id: str | None, outcome: bool | None, resolver: ImmutableResolver, missing: str, unresolved: str, failed: str) -> ConsensusV2QualificationCheck:
    if evidence_id is None or outcome is None:
        return _check(check_id, ConsensusV2CheckDisposition.INCOMPLETE, missing)
    if not _resolved(evidence_id, resolver):
        return _check(check_id, ConsensusV2CheckDisposition.BLOCKED, unresolved, evidence=(evidence_id,))
    return _check(check_id, ConsensusV2CheckDisposition.PASS if outcome else ConsensusV2CheckDisposition.FAIL, *(() if outcome else (failed,)), evidence=(evidence_id,))


def qualify_consensus_v2(candidate: ConsensusV2QualificationInput, *, immutable_resolver: ImmutableResolver) -> ConsensusV2QualificationResult:
    """Return a non-authorizing G3 result from already-retained evidence only."""
    checks: list[ConsensusV2QualificationCheck] = []
    closure = (candidate.primary_configuration_id, *candidate.closure_ids)
    if any(not is_immutable_id(item) for item in closure):
        checks.append(_check("immutable_closure", ConsensusV2CheckDisposition.INCOMPLETE, "G3_CLOSURE_ID_MISSING", evidence=closure))
    elif any(not immutable_resolver(item) for item in closure):
        checks.append(_check("immutable_closure", ConsensusV2CheckDisposition.BLOCKED, "G3_CLOSURE_UNRESOLVED", evidence=closure))
    else:
        checks.append(_check("immutable_closure", ConsensusV2CheckDisposition.PASS, evidence=closure))
    checks.append(_parity_check(candidate.parity_fixtures, immutable_resolver))
    checks.append(_evidence_boolean("abci_integration", candidate.integration_evidence_id, candidate.integration_used_real_boundary, immutable_resolver, "G3_INTEGRATION_EVIDENCE_MISSING", "G3_INTEGRATION_EVIDENCE_UNRESOLVED", "G3_INTEGRATION_BOUNDARY_NOT_REAL"))
    checks.append(_evidence_boolean("versioned_state", candidate.state_evidence_id, candidate.state_preserved, immutable_resolver, "G3_STATE_EVIDENCE_MISSING", "G3_STATE_EVIDENCE_UNRESOLVED", "G3_STATE_COMPATIBILITY_FAILED"))
    sensitivity_ids = (candidate.sensitivity_plan_id, *candidate.sensitivity_result_ids)
    if candidate.sensitivity_plan_id is None or candidate.sensitivity_complete is None or not candidate.sensitivity_result_ids:
        checks.append(_check("sensitivity", ConsensusV2CheckDisposition.INCOMPLETE, "G3_SENSITIVITY_EVIDENCE_MISSING"))
    elif any(not _resolved(item, immutable_resolver) for item in sensitivity_ids):
        checks.append(_check("sensitivity", ConsensusV2CheckDisposition.BLOCKED, "G3_SENSITIVITY_EVIDENCE_UNRESOLVED", evidence=tuple(item for item in sensitivity_ids if item)))
    else:
        checks.append(_check("sensitivity", ConsensusV2CheckDisposition.PASS if candidate.sensitivity_complete else ConsensusV2CheckDisposition.FAIL, *(() if candidate.sensitivity_complete else ("G3_SENSITIVITY_PLAN_INCOMPLETE",)), evidence=tuple(item for item in sensitivity_ids if item)))
    if not candidate.provenance_ids or candidate.provenance_complete is None:
        checks.append(_check("provenance", ConsensusV2CheckDisposition.INCOMPLETE, "G3_PROVENANCE_EVIDENCE_MISSING"))
    elif any(not _resolved(item, immutable_resolver) for item in candidate.provenance_ids):
        checks.append(_check("provenance", ConsensusV2CheckDisposition.BLOCKED, "G3_PROVENANCE_EVIDENCE_UNRESOLVED", evidence=candidate.provenance_ids))
    else:
        checks.append(_check("provenance", ConsensusV2CheckDisposition.PASS if candidate.provenance_complete else ConsensusV2CheckDisposition.FAIL, *(() if candidate.provenance_complete else ("G3_PROVENANCE_CLOSURE_INCOMPLETE",)), evidence=candidate.provenance_ids))
    dispositions = {str(item.disposition) for item in checks}
    if ConsensusV2CheckDisposition.INCOMPLETE.value in dispositions:
        result = ConsensusV2QualificationDisposition.INCOMPLETE
    elif ConsensusV2CheckDisposition.BLOCKED.value in dispositions:
        result = ConsensusV2QualificationDisposition.BLOCKED
    elif ConsensusV2CheckDisposition.FAIL.value in dispositions:
        result = ConsensusV2QualificationDisposition.SHADOW
    else:
        result = ConsensusV2QualificationDisposition.QUALIFIED
    provisional = ConsensusV2QualificationResult(CONSENSUS_V2_QUALIFICATION_SCHEMA, candidate.primary_configuration_id, candidate.closure_ids, tuple(checks), result, candidate.limitations, "")
    return replace(provisional, result_content_id=consensus_v2_qualification_content_id(provisional))
