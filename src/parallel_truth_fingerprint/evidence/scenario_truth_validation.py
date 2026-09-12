"""Pure audience-bound checks for ``ScenarioTruth.v1``.

These checks deliberately do not authenticate a caller, grant access, resolve
storage, or inspect restricted truth bytes.  Story 9.8 owns unlock/join
validation; this module only compares opaque immutable identities.
"""
from __future__ import annotations

from dataclasses import dataclass
from typing import Callable, Mapping

from parallel_truth_fingerprint.contracts.scenario_truth import (
    AUDIENCE, AUTHORIZATION_EFFECT, ScenarioTruth, ScenarioTruthViolation,
    _DIGEST, _UTC, parse_scenario_truth,
)


FORBIDDEN_TRUTH_FIELDS = frozenset({
    "truth", "scenario_truth", "scenario_name", "scenario_label", "label", "attack_label",
    "intervention", "condition", "interval", "expected_outcome", "truth_locator", "training_label",
})


@dataclass(frozen=True)
class ReferenceDescriptor:
    """An injected, immutable semantic/provenance/audience-map entry."""
    identity: str
    audience: str
    semantic_role: str
    immutable: bool
    dependencies: tuple[str, ...] = ()


@dataclass(frozen=True)
class ScenarioTruthValidationResult:
    valid: bool
    violations: tuple[ScenarioTruthViolation, ...]
    authorization_effect: str = AUTHORIZATION_EFFECT


@dataclass(frozen=True)
class TruthCompatibilityResult:
    compatible: bool
    observed_at: str
    violations: tuple[ScenarioTruthViolation, ...]
    published: bool = False
    authorization_effect: str = AUTHORIZATION_EFFECT


Resolver = Callable[[str], ReferenceDescriptor | None]


def _result(violations: list[ScenarioTruthViolation]) -> ScenarioTruthValidationResult:
    ordered = tuple(sorted(violations, key=lambda item: (item.rule_id, item.field, item.token)))
    return ScenarioTruthValidationResult(not ordered, ordered)


def _violation(rule_id: str, field: str, token: str) -> ScenarioTruthViolation:
    # Tokens are fixed rule-level descriptors, never truth values or references.
    return ScenarioTruthViolation(rule_id, field, token)


def validate_scenario_truth(record: ScenarioTruth, *, resolver: Resolver) -> ScenarioTruthValidationResult:
    """Validate one restricted record against only injected immutable metadata."""
    violations: list[ScenarioTruthViolation] = []
    try:
        parse_scenario_truth(record.to_dict())
    except Exception as exc:
        violation = getattr(exc, "violation", None)
        violations.append(violation or _violation("STV1-RECORD-INVALID", "record", "invalid"))
        return _result(violations)
    for identity in record.immutable_parent_ids:
        descriptor = resolver(identity)
        if descriptor is None:
            violations.append(_violation("STV1-PROVENANCE-UNRESOLVED", "parent", "unresolved"))
        elif descriptor.identity != identity or not descriptor.immutable:
            violations.append(_violation("STV1-PROVENANCE-IMMUTABLE", "parent", "immutable_mapping_required"))
        elif descriptor.audience not in {"detector_facing", AUDIENCE}:
            violations.append(_violation("STV1-PROVENANCE-AUDIENCE", "parent", "evaluator_compatible_required"))
        elif descriptor.semantic_role in {"restricted_truth", "truth_label", "legacy_v1", "mutable"}:
            violations.append(_violation("STV1-PROVENANCE-ROLE", "parent", "declared_nontruth_parent_required"))
    return _result(violations)


def validate_public_boundary(payload: Mapping[str, object], *, resolver: Resolver) -> ScenarioTruthValidationResult:
    """Reject declared direct or transitive restricted truth in a public v2 map.

    This validates declared map closure only; it does not claim to detect an
    undeclared covert channel.
    """
    violations: list[ScenarioTruthViolation] = []
    visited: set[str] = set()

    def inspect(value: object, path: str) -> None:
        if isinstance(value, Mapping):
            for key, child in value.items():
                key_text = str(key).casefold()
                if key_text in FORBIDDEN_TRUTH_FIELDS or any(part in key_text for part in ("truth", "scenario", "label", "intervention", "expected")):
                    violations.append(_violation("STV1-PUBLIC-FORBIDDEN-FIELD", path + "." + str(key), "forbidden"))
                inspect(child, path + "." + str(key))
        elif isinstance(value, (tuple, list)):
            for index, child in enumerate(value): inspect(child, f"{path}[{index}]")
        elif isinstance(value, str) and _DIGEST.fullmatch(value):
            inspect_reference(value, path)

    def inspect_reference(identity: str, path: str) -> None:
        if identity in visited: return
        visited.add(identity)
        descriptor = resolver(identity)
        if descriptor is None:
            violations.append(_violation("STV1-PUBLIC-PROVENANCE-UNRESOLVED", path, "mapped_identity_required")); return
        if descriptor.identity != identity or not descriptor.immutable:
            violations.append(_violation("STV1-PUBLIC-PROVENANCE-MUTABLE", path, "immutable_mapping_required")); return
        if descriptor.audience != "detector_facing" or descriptor.semantic_role in {"restricted_truth", "truth_label", "scenario_truth", "legacy_v1"}:
            violations.append(_violation("STV1-PUBLIC-RESTRICTED-TAINT", path, "public_compatible_required")); return
        for dependency in descriptor.dependencies:
            inspect_reference(dependency, path + ".dependency")

    inspect(payload, "$")
    return _result(violations)


def assess_truth_compatibility(record: ScenarioTruth, *, upstream_validated: bool,
                               upstream_restricted_truth_id: str | None,
                               upstream_parent_ids: tuple[str, ...], observed_at: str,
                               audience: str) -> TruthCompatibilityResult:
    """Compare opaque IDs after Story 9.8 validation without granting unlock."""
    violations: list[ScenarioTruthViolation] = []
    if not _UTC.fullmatch(observed_at):
        violations.append(_violation("STV1-COMPATIBILITY-TIME", "observed_at", "canonical_utc_required"))
    if audience != AUDIENCE:
        violations.append(_violation("STV1-COMPATIBILITY-AUDIENCE", "audience", "evaluator_restricted_required"))
    if not upstream_validated:
        violations.append(_violation("STV1-COMPATIBILITY-UPSTREAM", "upstream", "validated_98_result_required"))
    if not isinstance(upstream_restricted_truth_id, str) or record.scenario_truth_content_id != upstream_restricted_truth_id:
        violations.append(_violation("STV1-COMPATIBILITY-TRUTH", "restricted_truth", "unchanged_reference_required"))
    if tuple(upstream_parent_ids) != record.immutable_parent_ids:
        violations.append(_violation("STV1-COMPATIBILITY-PARENTS", "parents", "unchanged_closure_required"))
    ordered = tuple(sorted(violations, key=lambda item: (item.rule_id, item.field, item.token)))
    return TruthCompatibilityResult(not ordered, observed_at, ordered)
