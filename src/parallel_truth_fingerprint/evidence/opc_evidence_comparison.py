"""Offline, fail-closed eligibility and comparison of independent OPC evidence.

This is deliberately a validator, not an OPC client or a persistence service.
It accepts only caller-supplied, immutable identities and never substitutes a
cached reading, a legacy SCADA tolerance, or a current/default policy.
"""
from __future__ import annotations

from dataclasses import dataclass
from decimal import Decimal, InvalidOperation
from typing import Callable, Mapping

from parallel_truth_fingerprint.contracts.scientific_governance import is_immutable_id


ImmutableResolver = Callable[[str], bool]
SCHEMA_VERSION = "OPC-Evidence-Comparison.v1"
_REQUIRED_POLICY_PARAMETERS = frozenset({"freshness_limit", "source_server_skew_limit", "comparison_tolerance"})


@dataclass(frozen=True)
class OpcComparisonResult:
    """A reconstructible, non-authorizing outcome; ``difference`` is absent unless eligible."""

    eligible: bool
    outcome: str
    diagnostics: tuple[str, ...]
    source_references: tuple[str, ...]
    difference: str | None = None
    classification: str | None = None


def _decimal(value: object) -> Decimal | None:
    if not isinstance(value, str):
        return None
    try:
        parsed = Decimal(value)
    except InvalidOperation:
        return None
    return parsed if parsed.is_finite() else None


def _id(value: object, resolver: ImmutableResolver) -> bool:
    return isinstance(value, str) and is_immutable_id(value) and resolver(value)


def _closed(mapping: object, fields: frozenset[str]) -> bool:
    return isinstance(mapping, Mapping) and set(mapping) == fields


def validate_and_compare_opc_evidence(
    observation: Mapping[str, object] | None,
    consensus: Mapping[str, object] | None,
    policy: Mapping[str, object] | None,
    *,
    immutable_resolver: ImmutableResolver,
) -> OpcComparisonResult:
    """Validate supplied branches then compare current-domain values.

    The input format is intentionally compact and closed.  Callers must provide
    an already-correlated consensus projection because ``ConsensusDecision.v2``
    stores decision closure rather than a numeric reading.  Any malformed,
    unresolved, unavailable, stale, non-Good, shared-branch, or incompatible
    input returns a blocked result and performs no numeric calculation.
    """
    errors: list[str] = []
    refs: list[str] = []
    observation_fields = frozenset({
        "schema_version", "observation_id", "experiment_id", "run_id", "cycle_id", "correlation_id",
        "endpoint_id", "namespace_id", "node_id", "profile_revision_id", "snapshot_revision_id",
        "source_branch_id", "status_code", "source_timestamp", "server_timestamp", "fresh", "attempt_count",
        "value", "unit", "source_reference",
    })
    consensus_fields = frozenset({
        "schema_version", "decision_id", "experiment_id", "run_id", "cycle_id", "correlation_id",
        "profile_revision_id", "preconsensus_branch_id", "value", "unit", "source_reference",
    })
    policy_fields = frozenset({"schema_version", "policy_id", "basis_id", "basis_kind", "unit", "parameter_ids"})
    if not _closed(observation, observation_fields):
        errors.append("OPC-CMP-OBSERVATION-SCHEMA")
    if not _closed(consensus, consensus_fields):
        errors.append("OPC-CMP-CONSENSUS-SCHEMA")
    if not _closed(policy, policy_fields):
        errors.append("OPC-CMP-POLICY-SCHEMA")
    if errors:
        return OpcComparisonResult(False, "invalid", tuple(errors), ())
    assert observation is not None and consensus is not None and policy is not None
    if observation["schema_version"] != "ScadaObservation.v2": errors.append("OPC-CMP-OBSERVATION-VERSION")
    if consensus["schema_version"] != "ConsensusDecision.v2": errors.append("OPC-CMP-CONSENSUS-VERSION")
    if policy["schema_version"] != SCHEMA_VERSION: errors.append("OPC-CMP-POLICY-VERSION")
    identity_names = ("observation_id", "experiment_id", "run_id", "cycle_id", "correlation_id", "endpoint_id", "namespace_id", "profile_revision_id", "snapshot_revision_id", "source_reference")
    for name in identity_names:
        if not _id(observation[name], immutable_resolver): errors.append("OPC-CMP-OBSERVATION-IDENTITY")
    for name in ("decision_id", "experiment_id", "run_id", "cycle_id", "correlation_id", "profile_revision_id", "source_reference"):
        if not _id(consensus[name], immutable_resolver): errors.append("OPC-CMP-CONSENSUS-IDENTITY")
    for name in ("policy_id", "basis_id"):
        if not _id(policy[name], immutable_resolver): errors.append("OPC-CMP-POLICY-IDENTITY")
    parameters = policy["parameter_ids"]
    if not isinstance(parameters, Mapping) or set(parameters) != _REQUIRED_POLICY_PARAMETERS:
        errors.append("OPC-CMP-PARAMETER-CLOSURE")
    else:
        for parameter_id in parameters.values():
            if not _id(parameter_id, immutable_resolver): errors.append("OPC-CMP-PARAMETER-UNRESOLVED")
    refs.extend(str(item) for item in (observation["observation_id"], observation["source_reference"], consensus["decision_id"], consensus["source_reference"], policy["policy_id"], policy["basis_id"]) if isinstance(item, str))
    if isinstance(parameters, Mapping): refs.extend(item for item in parameters.values() if isinstance(item, str))
    if not isinstance(observation["node_id"], str) or not observation["node_id"]: errors.append("OPC-CMP-NODE-ID")
    if observation["status_code"] != "Good": errors.append("OPC-CMP-STATUS-NOT-GOOD")
    if observation["fresh"] is not True: errors.append("OPC-CMP-STALE-OR-UNVERIFIED")
    if type(observation["attempt_count"]) is not int or observation["attempt_count"] <= 0: errors.append("OPC-CMP-ATTEMPTS")
    if not all(isinstance(observation[name], str) and observation[name].endswith("Z") for name in ("source_timestamp", "server_timestamp")):
        errors.append("OPC-CMP-TIMESTAMP")
    if observation["source_branch_id"] != "independent_opc": errors.append("OPC-CMP-OPC-BRANCH-NOT-INDEPENDENT")
    if consensus["preconsensus_branch_id"] == observation["source_branch_id"]: errors.append("OPC-CMP-BRANCH-NOT-INDEPENDENT")
    if any(observation[name] != consensus[name] for name in ("experiment_id", "run_id", "cycle_id", "correlation_id")):
        errors.append("OPC-CMP-CORRELATION-MISMATCH")
    if observation["profile_revision_id"] != consensus["profile_revision_id"]: errors.append("OPC-CMP-PROFILE-MISMATCH")
    if policy["basis_kind"] != "same_profile_raw_current" or policy["unit"] != "mA": errors.append("OPC-CMP-BASIS-INELIGIBLE")
    if observation["unit"] != policy["unit"] or consensus["unit"] != policy["unit"]: errors.append("OPC-CMP-UNIT-MISMATCH")
    opc_value, consensus_value = _decimal(observation["value"]), _decimal(consensus["value"])
    if opc_value is None or consensus_value is None: errors.append("OPC-CMP-VALUE-INCONSISTENT")
    if errors:
        return OpcComparisonResult(False, "invalid", tuple(sorted(set(errors))), tuple(sorted(set(refs))))
    difference = abs(opc_value - consensus_value)
    # The policy's tolerance is an immutable referenced parameter, not a numeric
    # value carried here. Classification remains deliberately uncomputed.
    return OpcComparisonResult(True, "eligible_unclassified", (), tuple(sorted(set(refs))), format(difference, "f"), None)
