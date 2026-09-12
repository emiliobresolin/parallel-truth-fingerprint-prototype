"""Frozen, non-executing parameter bindings for ConsensusParameterSet.v2.

This module deliberately contains neither numeric values nor executable
operations.  It is a portable declaration of the evidence a later evaluator
must resolve again before it can do any computation.
"""

from __future__ import annotations

from dataclasses import dataclass
from typing import Callable, Protocol


CONSENSUS_PARAMETER_SET_SCHEMA = "ConsensusParameterSet.v2"


class ImmutableRecord(Protocol):
    """Minimal read-only view accepted from an injected evidence resolver."""

    def to_dict(self) -> dict[str, object]: ...


@dataclass(frozen=True)
class ConsensusParameterSlot:
    """One exact evidence revision required by a closed numeric consumer slot."""

    slot_id: str
    parameter_revision_id: str
    parameter_revision_sha256: str
    parameter_class: str
    quantity_kind: str
    unit: str
    dimension: str
    profile_id: str
    experiment_scope: str
    decision_id: str | None = None
    decision_record_sha256: str | None = None


@dataclass(frozen=True)
class ConsensusParameterSet:
    """Flat immutable v2 parameter declaration; it grants no execution right."""

    schema_version: str
    parameter_set_id: str
    component_identity: str
    experiment_scope: str
    profile_id: str
    comparison_basis_id: str
    comparison_basis_schema: str
    comparison_basis_sha256: str
    comparison_basis_canonical_bytes_sha256: str
    quality_policy_id: str
    numeric_inventory_id: str
    numeric_inventory_sha256: str
    required_parameter_set_id: str
    required_parameter_set_sha256: str
    parameter_gate_result_id: str
    parameter_gate_result_sha256: str
    comparison_mode: str
    residual_policy_id: str
    residual_policy_schema: str
    residual_policy_sha256: str
    residual_policy_canonical_bytes_sha256: str
    residual_policy_slot_ids: tuple[str, ...]
    residual_policy_units: tuple[str, ...]
    residual_policy_dimensions: tuple[str, ...]
    residual_policy_conformance_id: str
    analysis_plan_id: str
    analysis_plan_sha256: str
    sensitivity_plan_id: str
    sensitivity_plan_sha256: str
    sensitivity_alternative_ids: tuple[str, ...]
    selected_alternative_id: str
    primary_decision_id: str
    primary_decision_record_sha256: str
    scientific_freeze_id: str
    scientific_freeze_sha256: str
    partition_lock_id: str
    partition_lock_sha256: str
    slots: tuple[ConsensusParameterSlot, ...]
    authorization_effect: str = "none"

    def __post_init__(self) -> None:
        # Preserve duplicates so the validator can report their attempted use.
        object.__setattr__(self, "slots", tuple(sorted(self.slots, key=lambda item: item.slot_id)))
        for name in ("residual_policy_slot_ids", "residual_policy_units", "residual_policy_dimensions",
                     "sensitivity_alternative_ids"):
            object.__setattr__(self, name, tuple(sorted(getattr(self, name))))


@dataclass(frozen=True)
class ConsensusParameterResolvers:
    """Pure caller-provided resolvers; no registry, alias lookup, or I/O exists here."""

    inventory: Callable[[str], object | None]
    required_set: Callable[[str], object | None]
    gate_result: Callable[[str], object | None]
    parameter_revision: Callable[[str], object | None]
    decision_record: Callable[[str], object | None]
    scientific_freeze: Callable[[str], object | None]
    partition_lock: Callable[[str], object | None]
    analysis_plan: Callable[[str], object | None]
    residual_policy: Callable[[str], object | None]


@dataclass(frozen=True)
class ConsensusParameterViolation:
    rule_id: str
    field: str
    reference: str
    explanation: str


@dataclass(frozen=True)
class ConsensusParameterValidationResult:
    status: str
    parameter_set_id: str
    violations: tuple[ConsensusParameterViolation, ...]
    authorization_effect: str = "none"

