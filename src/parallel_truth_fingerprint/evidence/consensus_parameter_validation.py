"""Pure fail-closed resolution of ``ConsensusParameterSet.v2``.

It only compares immutable declarations supplied by injected resolvers.  It
does not calculate a residual, select trust, load legacy values, or invoke an
evaluator or any external system.
"""

from __future__ import annotations

import hashlib
import json
import re
from dataclasses import asdict, is_dataclass
from typing import Any

from parallel_truth_fingerprint.consensus_v2_parameters import (
    CONSENSUS_PARAMETER_SET_SCHEMA, ConsensusParameterResolvers,
    ConsensusParameterSet, ConsensusParameterValidationResult,
    ConsensusParameterViolation,
)


_DIGEST = re.compile(r"sha256:[0-9a-f]{64}\Z")
_MUTABLE = {"", "latest", "current", "default", "legacy", "v1"}
_DIRECT = "direct"
_PREREGISTERED = "preregistered_factor"
_CROSS_PROFILE = "cross_profile_residual"
_SAME_PROFILE = "same_profile_raw_current"


def _value(record: object | None, name: str, default: object = None) -> object:
    if record is None:
        return default
    if isinstance(record, dict):
        return record.get(name, default)
    return getattr(record, name, default)


def _digest(value: object) -> bool:
    return isinstance(value, str) and bool(_DIGEST.fullmatch(value))


def _opaque(value: object) -> bool:
    return isinstance(value, str) and value.strip() == value and value.casefold() not in _MUTABLE


def _record_hash(record: object | None, *, self_fields: tuple[str, ...] = ()) -> str | None:
    """Hash only a canonical record representation, without accepting an alias."""
    if record is None:
        return None
    if hasattr(record, "to_dict"):
        payload = record.to_dict()  # type: ignore[union-attr]
    elif is_dataclass(record):
        payload = asdict(record)
    elif isinstance(record, dict):
        payload = dict(record)
    else:
        return None
    for name in self_fields:
        payload[name] = ""
    try:
        encoded = json.dumps(payload, sort_keys=True, ensure_ascii=True, separators=(",", ":"), allow_nan=False).encode("ascii")
    except (TypeError, ValueError):
        return None
    return "sha256:" + hashlib.sha256(encoded).hexdigest()


def _matches_hash(record: object | None, expected: str, *declared_names: str) -> bool:
    if not _digest(expected):
        return False
    declared = [str(_value(record, name, "")) for name in declared_names]
    if expected in declared:
        return True
    # Some upstream records are self-identifying while other immutable
    # governance records derive their identity from their complete payload.
    return expected in {
        _record_hash(record),
        _record_hash(record, self_fields=declared_names),
    }


def validate_consensus_parameter_set(
    parameter_set: ConsensusParameterSet, resolvers: ConsensusParameterResolvers,
) -> ConsensusParameterValidationResult:
    """Resolve all declared immutable references and return a bounded blocker.

    ``valid`` says the supplied closure is structurally accountable, never
    that consensus is authorized, evaluated, persisted, or scientifically
    qualified.
    """
    violations: list[ConsensusParameterViolation] = []

    def fail(rule: str, field: str, reference: object, explanation: str) -> None:
        violations.append(ConsensusParameterViolation(rule, field, str(reference), explanation))

    if parameter_set.schema_version != CONSENSUS_PARAMETER_SET_SCHEMA:
        fail("CPS-SCHEMA", "schema_version", parameter_set.schema_version, "Only ConsensusParameterSet.v2 is accepted.")
    if parameter_set.authorization_effect != "none":
        fail("CPS-AUTHORIZATION-EFFECT", "authorization_effect", parameter_set.authorization_effect, "This resolver can never authorize activity.")
    for field in ("parameter_set_id", "component_identity", "experiment_scope", "profile_id", "comparison_basis_id", "comparison_basis_schema", "quality_policy_id", "comparison_mode", "residual_policy_id", "residual_policy_schema", "residual_policy_conformance_id", "analysis_plan_id", "sensitivity_plan_id", "selected_alternative_id", "primary_decision_id", "scientific_freeze_id", "partition_lock_id"):
        value = getattr(parameter_set, field)
        if not _opaque(value):
            fail("CPS-MUTABLE-OR-MISSING", field, value, "Aliases, defaults, legacy tokens, and blank identifiers are forbidden.")
    for field in ("comparison_basis_sha256", "comparison_basis_canonical_bytes_sha256", "numeric_inventory_sha256", "required_parameter_set_sha256", "parameter_gate_result_sha256", "residual_policy_sha256", "residual_policy_canonical_bytes_sha256", "analysis_plan_sha256", "sensitivity_plan_sha256", "primary_decision_record_sha256", "scientific_freeze_sha256", "partition_lock_sha256"):
        if not _digest(getattr(parameter_set, field)):
            fail("CPS-IMMUTABLE-HASH", field, getattr(parameter_set, field), "An exact SHA-256 content identity is required.")

    inventory = resolvers.inventory(parameter_set.numeric_inventory_id)
    required = resolvers.required_set(parameter_set.required_parameter_set_id)
    gate = resolvers.gate_result(parameter_set.parameter_gate_result_id)
    if inventory is None or not _matches_hash(inventory, parameter_set.numeric_inventory_sha256):
        fail("CPS-INVENTORY", "numeric_inventory_id", parameter_set.numeric_inventory_id, "The exact numeric inventory was not resolved.")
    if required is None or not _matches_hash(required, parameter_set.required_parameter_set_sha256):
        fail("CPS-REQUIRED-SET", "required_parameter_set_id", parameter_set.required_parameter_set_id, "The exact closed required set was not resolved.")
    if gate is None or not _matches_hash(gate, parameter_set.parameter_gate_result_sha256, "gate_result_id"):
        fail("CPS-GATE", "parameter_gate_result_id", parameter_set.parameter_gate_result_id, "The exact accountable parameter gate result was not resolved.")
    elif str(_value(gate, "accountability_outcome")) != "accountable" or _value(gate, "authorization_effect") != "none":
        fail("CPS-GATE-BLOCKED", "parameter_gate_result_id", parameter_set.parameter_gate_result_id, "A blocked or authorizing parameter gate cannot satisfy v2.")

    for record, field, expected in ((inventory, "inventory", parameter_set), (required, "required_set", parameter_set), (gate, "gate", parameter_set)):
        if record is None:
            continue
        for name in ("component_identity", "scope", "profile_id"):
            actual = _value(record, name)
            wanted = expected.component_identity if name == "component_identity" else (expected.experiment_scope if name == "scope" else expected.profile_id)
            if actual is not None and str(actual) != wanted:
                fail("CPS-SCOPE-CLOSURE", field + "." + name, actual, "Inventory, required set, and gate must use the exact component/scope/profile closure.")
    if required is not None:
        if str(_value(required, "inventory_id")) != parameter_set.numeric_inventory_id:
            fail("CPS-INVENTORY-REQUIRED-LINK", "required_parameter_set_id", parameter_set.required_parameter_set_id, "Required set does not bind this inventory.")
    if gate is not None:
        if str(_value(gate, "inventory_id")) != parameter_set.numeric_inventory_id or str(_value(gate, "required_set_id")) != parameter_set.required_parameter_set_id:
            fail("CPS-GATE-CLOSURE", "parameter_gate_result_id", parameter_set.parameter_gate_result_id, "Gate must bind the same inventory and required set.")

    required_bindings = tuple(_value(required, "bindings", ()) or ())
    required_slots = {str(_value(item, "slot_id")) for item in required_bindings if not bool(_value(item, "not_applicable", False))}
    slots = parameter_set.slots
    slot_ids = [item.slot_id for item in slots]
    if not slots or len(slot_ids) != len(set(slot_ids)) or set(slot_ids) != required_slots:
        fail("CPS-SLOT-CLOSURE", "slots", ",".join(slot_ids), "Slots must match the required non-N/A inventory exactly once; no relaxation is allowed.")
    for slot in slots:
        if not _opaque(slot.slot_id) or not _opaque(slot.parameter_revision_id) or not _digest(slot.parameter_revision_sha256):
            fail("CPS-SLOT-IDENTITY", "slots", slot.slot_id, "A slot requires exact non-alias revision identity and hash.")
        revision = resolvers.parameter_revision(slot.parameter_revision_id)
        if revision is None or not _matches_hash(revision, slot.parameter_revision_sha256, "revision_sha256"):
            fail("CPS-REVISION", "slots." + slot.slot_id, slot.parameter_revision_id, "Revision is absent, stale, or hash-conflicting.")
            continue
        for name, wanted in (("parameter_class", slot.parameter_class), ("quantity_kind", slot.quantity_kind), ("unit", slot.unit), ("profile_id", slot.profile_id), ("experiment_scope", slot.experiment_scope)):
            if str(_value(revision, name)) != wanted:
                fail("CPS-REVISION-CLOSURE", "slots." + slot.slot_id + "." + name, str(_value(revision, name)), "Revision fields must exactly match the declared slot.")
        if slot.profile_id != parameter_set.profile_id or slot.experiment_scope != parameter_set.experiment_scope:
            fail("CPS-SLOT-SCOPE", "slots." + slot.slot_id, slot.slot_id, "Slots cannot cross profiles or experiment scopes.")
        if slot.parameter_class == _PREREGISTERED and (not slot.decision_id or not slot.decision_record_sha256):
            fail("CPS-DECISION-REQUIRED", "slots." + slot.slot_id, slot.slot_id, "Preregistered factors require a frozen DecisionRecord.")
        if slot.decision_id or slot.decision_record_sha256:
            decision = resolvers.decision_record(slot.decision_id or "")
            if not slot.decision_id or not _matches_hash(decision, slot.decision_record_sha256 or "", "record_sha256"):
                fail("CPS-DECISION", "slots." + slot.slot_id, slot.decision_id, "Decision identity is absent or stale.")

    if parameter_set.comparison_mode not in {_SAME_PROFILE, _CROSS_PROFILE}:
        fail("CPS-COMPARISON-MODE", "comparison_mode", parameter_set.comparison_mode, "Comparison mode is closed.")
    policy = resolvers.residual_policy(parameter_set.residual_policy_id)
    if policy is None or not _matches_hash(policy, parameter_set.residual_policy_sha256, "content_sha256", "policy_sha256"):
        fail("CPS-RESIDUAL-POLICY", "residual_policy_id", parameter_set.residual_policy_id, "Residual policy requires its exact immutable content.")
    if parameter_set.comparison_mode == _CROSS_PROFILE:
        if not parameter_set.residual_policy_slot_ids or not parameter_set.residual_policy_units or not parameter_set.residual_policy_dimensions or not _digest(parameter_set.residual_policy_canonical_bytes_sha256):
            fail("CPS-CROSS-PROFILE-RESIDUAL", "residual_policy_id", parameter_set.residual_policy_id, "Cross-profile residuals require slots, units, dimensions and canonical operation closure.")
        if any(slot_id not in set(slot_ids) for slot_id in parameter_set.residual_policy_slot_ids):
            fail("CPS-RESIDUAL-SLOT", "residual_policy_slot_ids", ",".join(parameter_set.residual_policy_slot_ids), "Residual policy names an undeclared slot.")
        if not any(item.parameter_class in {"measured", "derived"} and item.dimension == "one" for item in slots):
            fail("CPS-CROSS-PROFILE-UNCERTAINTY", "slots", "", "Cross-profile residuals require explicit dimensionless measured or derived uncertainty support.")
    elif parameter_set.residual_policy_slot_ids or parameter_set.residual_policy_units or parameter_set.residual_policy_dimensions:
        fail("CPS-SAME-PROFILE-RESIDUAL", "residual_policy_slot_ids", "", "Raw same-profile comparison cannot smuggle cross-profile residual inputs.")

    plan = resolvers.analysis_plan(parameter_set.analysis_plan_id)
    freeze = resolvers.scientific_freeze(parameter_set.scientific_freeze_id)
    lock = resolvers.partition_lock(parameter_set.partition_lock_id)
    if plan is None or not _matches_hash(plan, parameter_set.analysis_plan_sha256, "content_sha256", "plan_sha256"):
        fail("CPS-ANALYSIS-PLAN", "analysis_plan_id", parameter_set.analysis_plan_id, "Frozen analysis plan did not resolve exactly.")
    if freeze is None or not _matches_hash(freeze, parameter_set.scientific_freeze_sha256):
        fail("CPS-SCIENTIFIC-FREEZE", "scientific_freeze_id", parameter_set.scientific_freeze_id, "ScientificFreeze identity is missing or stale.")
    if lock is None or not _matches_hash(lock, parameter_set.partition_lock_sha256, "content_sha256", "record_sha256"):
        fail("CPS-PARTITION-LOCK", "partition_lock_id", parameter_set.partition_lock_id, "Partition-lock identity is missing or stale.")
    primary = resolvers.decision_record(parameter_set.primary_decision_id)
    if primary is None or not _matches_hash(primary, parameter_set.primary_decision_record_sha256, "record_sha256"):
        fail("CPS-PRIMARY-DECISION", "primary_decision_id", parameter_set.primary_decision_id, "Primary selection requires exact pre-test DecisionRecord.")
    if parameter_set.selected_alternative_id not in {"primary", *parameter_set.sensitivity_alternative_ids}:
        fail("CPS-UNKNOWN-SENSITIVITY", "selected_alternative_id", parameter_set.selected_alternative_id, "Selected configuration is not in the frozen sensitivity plan.")
    if len(parameter_set.sensitivity_alternative_ids) != len(set(parameter_set.sensitivity_alternative_ids)):
        fail("CPS-SENSITIVITY-DUPLICATE", "sensitivity_alternative_ids", ",".join(parameter_set.sensitivity_alternative_ids), "Sensitivity alternatives must be unique.")

    ordered = tuple(sorted(violations, key=lambda item: (item.rule_id, item.field, item.reference)))
    return ConsensusParameterValidationResult("blocked" if ordered else "valid", parameter_set.parameter_set_id, ordered)
