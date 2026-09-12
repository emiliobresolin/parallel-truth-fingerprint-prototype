"""Pure injected-resolver validation for consensus-v2 contract evidence closure."""
from __future__ import annotations

from dataclasses import dataclass
from typing import Callable, Mapping, Any

from parallel_truth_fingerprint.contracts.consensus_v2 import ConsensusRoundInputV2, ConsensusDecisionV2


@dataclass(frozen=True)
class ConsensusContractResolver:
    """All authority comes from immutable, caller-owned snapshots; no I/O occurs."""
    immutable: Callable[[str], bool]
    observation: Callable[[str], Mapping[str, Any] | None]
    qualification: Callable[[str], Mapping[str, Any] | None]
    dependency: Callable[[str], Mapping[str, Any] | None]


@dataclass(frozen=True)
class ConsensusContractValidation:
    valid: bool
    diagnostics: tuple[str, ...]
    authorization_effect: str = "none"


_FORBIDDEN = frozenset({"syscall", "truth", "label", "scenario", "detector_score", "fusion", "opc", "actuator", "command"})


def _safe_dependency(identity: str, resolver: ConsensusContractResolver) -> bool:
    entry = resolver.dependency(identity)
    if not resolver.immutable(identity) or entry is None or entry.get("immutable") is not True or entry.get("audience") != "public": return False
    tokens = {str(value).lower() for value in entry.get("semantic_tokens", ())} | {str(value).lower() for value in entry.get("provenance_tokens", ())}
    return not bool(tokens & _FORBIDDEN)


def validate_consensus_round_input_v2(record: ConsensusRoundInputV2, resolver: ConsensusContractResolver) -> ConsensusContractValidation:
    data, errors = record.to_dict(), []
    qualification = resolver.qualification(data["qualification_result_id"])
    if not _safe_dependency(data["qualification_result_id"], resolver) or qualification is None or qualification.get("disposition") != "qualified" or qualification.get("g2") != "pass": errors.append("CV2_QUALIFICATION_UNRESOLVED")
    qualification_observations = set(qualification.get("observation_ids", ())) if qualification else set()
    qualification_closure = set(qualification.get("closure_ids", ())) if qualification else set()
    basis = data["comparison_basis"]
    ids = [basis["basis_id"]] + list(data["quality_policy_ids"]) + list(data["parameter_ids"]) + list(basis["profile_ids"]) + list(basis["uncertainty_parameter_ids"])
    for identity in ids:
        if not _safe_dependency(identity, resolver) or identity not in qualification_closure: errors.append("CV2_DEPENDENCY_UNSAFE")
    for item in data["observations"]:
        observed = resolver.observation(item["observation_id"])
        if (not _safe_dependency(item["observation_id"], resolver) or observed is None or
                observed.get("observation_content_id") != item["observation_id"] or
                observed.get("canonical_hash") != item["observation_canonical_hash"] or
                observed.get("profile_id") != item["profile_id"] or observed.get("source_sequence") != item["source_sequence"] or
                item["observation_id"] not in qualification_observations): errors.append("CV2_OBSERVATION_UNRESOLVED")
    return ConsensusContractValidation(not errors, tuple(sorted(set(errors))))


def validate_consensus_decision_v2(record: ConsensusDecisionV2, round_input: ConsensusRoundInputV2, resolver: ConsensusContractResolver) -> ConsensusContractValidation:
    errors = list(validate_consensus_round_input_v2(round_input, resolver).diagnostics)
    data = record.to_dict()
    if data["round_input_id"] != round_input.to_dict()["input_content_id"] or data["round_input_hash"] != round_input.to_dict()["input_content_id"]: errors.append("CV2_DECISION_INPUT_MISMATCH")
    if data["comparison_basis"] != round_input.to_dict()["comparison_basis"]: errors.append("CV2_DECISION_BASIS_MISMATCH")
    return ConsensusContractValidation(not errors, tuple(sorted(set(errors))))
