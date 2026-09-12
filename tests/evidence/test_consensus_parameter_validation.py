from __future__ import annotations

import hashlib
import json
import unittest
from dataclasses import replace

from parallel_truth_fingerprint.consensus_v2_parameters import (
    CONSENSUS_PARAMETER_SET_SCHEMA, ConsensusParameterResolvers,
    ConsensusParameterSet, ConsensusParameterSlot,
)
from parallel_truth_fingerprint.evidence.consensus_parameter_validation import (
    validate_consensus_parameter_set,
)


def digest(value: object) -> str:
    return "sha256:" + hashlib.sha256(json.dumps(value, sort_keys=True, separators=(",", ":")).encode("ascii")).hexdigest()


class ConsensusParameterValidationTests(unittest.TestCase):
    def resolved(self, value: dict[str, object], identity_field: str | None = None) -> dict[str, object]:
        if identity_field:
            copy = dict(value)
            copy[identity_field] = ""
            value[identity_field] = digest(copy)
        return value

    def fixture(self, *, cross_profile: bool = False) -> tuple[ConsensusParameterSet, ConsensusParameterResolvers]:
        scope, profile = "experiment:sentinel", "profile:sentinel"
        revision = self.resolved({"parameter_revision_id": "revision:uncertainty", "revision_sha256": "", "parameter_class": "measured", "quantity_kind": "comparison_tolerance", "unit": "one", "profile_id": profile, "experiment_scope": scope}, "revision_sha256")
        inventory = {"inventory_id": "inventory:sentinel", "component_identity": "consensus-v2", "scope": scope, "profile_id": profile}
        required = {"required_set_id": "required:sentinel", "inventory_id": "inventory:sentinel", "scope": scope, "profile_id": profile, "component_identity": "consensus-v2", "bindings": [{"slot_id": "uncertainty", "not_applicable": False}]}
        gate = {"gate_result_id": "sha256:" + "1" * 64, "inventory_id": "inventory:sentinel", "required_set_id": "required:sentinel", "accountability_outcome": "accountable", "authorization_effect": "none"}
        decision = self.resolved({"decision_id": "decision:primary", "record_sha256": "", "profile_id": profile, "experiment_scope": scope}, "record_sha256")
        plan = {"plan_id": "plan:sentinel", "content_sha256": ""}
        plan["content_sha256"] = digest({"plan_id": "plan:sentinel", "content_sha256": ""})
        policy = {"policy_id": "policy:residual", "content_sha256": ""}
        policy["content_sha256"] = digest({"policy_id": "policy:residual", "content_sha256": ""})
        freeze = {"freeze": "frozen"}
        lock = {"lock": "partition"}
        slot = ConsensusParameterSlot("uncertainty", "revision:uncertainty", str(revision["revision_sha256"]), "measured", "comparison_tolerance", "one", "one", profile, scope)
        parameter_set = ConsensusParameterSet(
            CONSENSUS_PARAMETER_SET_SCHEMA, "set:sentinel", "consensus-v2", scope, profile,
            "basis:current", "ComparisonBasis.v2", "sha256:" + "2" * 64, "sha256:" + "3" * 64,
            "quality:sentinel", "inventory:sentinel", digest(inventory), "required:sentinel", digest(required),
            str(gate["gate_result_id"]), str(gate["gate_result_id"]),
            "cross_profile_residual" if cross_profile else "same_profile_raw_current",
            "policy:residual", "ResidualPolicy.v2", str(policy["content_sha256"]), "sha256:" + "4" * 64,
            ("uncertainty",) if cross_profile else (), ("one",) if cross_profile else (), ("one",) if cross_profile else (), "conformance:sentinel",
            "plan:sentinel", str(plan["content_sha256"]), "sensitivity:sentinel", "sha256:" + "5" * 64, ("sensitivity:a",), "primary",
            "decision:primary", str(decision["record_sha256"]), "freeze:sentinel", digest(freeze), "lock:sentinel", digest(lock), (slot,),
        )
        tables = {
            "inventory:sentinel": inventory, "required:sentinel": required, str(gate["gate_result_id"]): gate,
            "revision:uncertainty": revision, "decision:primary": decision, "freeze:sentinel": freeze,
            "lock:sentinel": lock, "plan:sentinel": plan, "policy:residual": policy,
        }
        resolver = lambda name: lambda key: tables.get(key) if key == name else None
        return parameter_set, ConsensusParameterResolvers(
            resolver("inventory:sentinel"), resolver("required:sentinel"), resolver(str(gate["gate_result_id"])),
            resolver("revision:uncertainty"), resolver("decision:primary"), resolver("freeze:sentinel"),
            resolver("lock:sentinel"), resolver("plan:sentinel"), resolver("policy:residual"),
        )

    def test_complete_same_profile_closure_is_valid_and_non_authorizing(self) -> None:
        parameter_set, resolvers = self.fixture()
        result = validate_consensus_parameter_set(parameter_set, resolvers)
        self.assertEqual(("valid", "none", ()), (result.status, result.authorization_effect, result.violations))

    def test_missing_duplicate_and_conflicting_slot_closure_blocks(self) -> None:
        parameter_set, resolvers = self.fixture()
        duplicate = replace(parameter_set.slots[0], parameter_revision_id="revision:other")
        result = validate_consensus_parameter_set(replace(parameter_set, slots=(parameter_set.slots[0], duplicate)), resolvers)
        self.assertIn("CPS-SLOT-CLOSURE", {item.rule_id for item in result.violations})
        self.assertIn("CPS-REVISION", {item.rule_id for item in result.violations})

    def test_scope_stale_gate_and_unknown_sensitivity_fail_closed(self) -> None:
        parameter_set, resolvers = self.fixture()
        result = validate_consensus_parameter_set(replace(parameter_set, parameter_gate_result_sha256="sha256:" + "f" * 64, selected_alternative_id="sensitivity:unknown"), resolvers)
        rules = {item.rule_id for item in result.violations}
        self.assertIn("CPS-GATE", rules)
        self.assertIn("CPS-UNKNOWN-SENSITIVITY", rules)

    def test_cross_profile_requires_dimensionless_uncertainty_and_policy_closure(self) -> None:
        parameter_set, resolvers = self.fixture(cross_profile=True)
        bad_slot = replace(parameter_set.slots[0], parameter_class="direct", dimension="mA")
        result = validate_consensus_parameter_set(replace(parameter_set, slots=(bad_slot,)), resolvers)
        self.assertIn("CPS-CROSS-PROFILE-UNCERTAINTY", {item.rule_id for item in result.violations})

    def test_preregistered_factor_requires_decision_record(self) -> None:
        parameter_set, resolvers = self.fixture()
        slot = replace(parameter_set.slots[0], parameter_class="preregistered_factor")
        result = validate_consensus_parameter_set(replace(parameter_set, slots=(slot,)), resolvers)
        self.assertIn("CPS-DECISION-REQUIRED", {item.rule_id for item in result.violations})

    def test_legacy_default_and_authorizing_values_never_migrate(self) -> None:
        parameter_set, resolvers = self.fixture()
        result = validate_consensus_parameter_set(replace(parameter_set, parameter_set_id="legacy", authorization_effect="permission"), resolvers)
        self.assertEqual("blocked", result.status)
        self.assertTrue({"CPS-MUTABLE-OR-MISSING", "CPS-AUTHORIZATION-EFFECT"}.issubset({item.rule_id for item in result.violations}))

    def test_resolvers_are_the_only_boundary_and_are_called_without_side_effect_helpers(self) -> None:
        parameter_set, _ = self.fixture()
        calls: list[str] = []
        def absent(name: str):
            def resolve(_: str):
                calls.append(name)
                return None
            return resolve
        result = validate_consensus_parameter_set(parameter_set, ConsensusParameterResolvers(*[absent(str(index)) for index in range(9)]))
        self.assertEqual("blocked", result.status)
        self.assertEqual({str(index) for index in range(9)}, set(calls))


if __name__ == "__main__":
    unittest.main()
