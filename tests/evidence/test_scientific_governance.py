"""Offline conformance checks for the Story 9.8 governance boundary."""

from __future__ import annotations

import unittest
from dataclasses import replace

from parallel_truth_fingerprint.contracts.scientific_governance import (
    ActivityAuthorization,
    PartitionMembership,
    PartitionRecord,
    ScientificFreeze,
    TruthJoinRecord,
    TruthUnlockRecord,
    canonical_governance_bytes,
    parse_partition_record,
)
from parallel_truth_fingerprint.evidence.scientific_governance import (
    GovernanceProfile,
    SupportDisposition,
    validate_activity_authorization,
    validate_partition_record,
    validate_scientific_freeze,
    validate_truth_join,
    validate_truth_unlock,
)


class ScientificGovernanceTests(unittest.TestCase):
    @staticmethod
    def digest(letter: str) -> str:
        return "sha256:" + letter * 64
    def test_partition_is_canonical_and_requires_complete_opaque_inventory(self) -> None:
        record = PartitionRecord(
            audience="detector_facing", source_universe_id="sha256:" + "a" * 64,
            track_id="sentinel-track", eligibility_policy_id="sha256:" + "b" * 64,
            profile_revision_id="profile-sentinel", grouping_scheme_id="sha256:" + "c" * 64,
            method_identity="sha256:" + "d" * 64, created_at="2026-01-01T00:00:00Z",
            source_use_revision_ids=("sha256:" + "e" * 64,),
            memberships=(PartitionMembership("SENTINEL_GROUP_ALPHA", "train"),),
        )
        result = validate_partition_record(record, inventory_groups=("SENTINEL_GROUP_ALPHA", "SENTINEL_GROUP_BETA"),
                                           profile=GovernanceProfile.sentinel_partition())
        self.assertFalse(result.allowed)
        self.assertEqual("none", result.authorization_effect)
        self.assertIn("GOV-PARTITION-INVENTORY-INCOMPLETE", {item.rule_id for item in result.violations})
        self.assertEqual(canonical_governance_bytes(record), canonical_governance_bytes(record))

    def test_authorization_digest_ignores_its_decision_but_requires_exact_scope(self) -> None:
        auth = ActivityAuthorization(
            audience="detector_facing", action="model_training", profile_revision_id="profile-action",
            scope_slots=(("track", "sha256:" + "a" * 64),), input_ids=("sha256:" + "b" * 64,),
            prerequisite_ids=("sha256:" + "c" * 64,), expected_output_roles=("detector_bundle",),
            owner_id="sentinel-owner", decision="approved", created_at="2026-01-01T00:00:00Z",
            limitations=("prototype",), planned_activity_id="",
        ).with_computed_id()
        result = validate_activity_authorization(auth, profile=GovernanceProfile.sentinel_action())
        self.assertTrue(result.allowed)
        self.assertEqual("permission", result.authorization_effect)
        self.assertFalse(validate_activity_authorization(
            replace(auth, planned_activity_id="sha256:" + "0" * 64),
            profile=GovernanceProfile.sentinel_action(),
        ).allowed)

    def test_parser_rejects_extra_fields_and_truth_action_requires_evaluator(self) -> None:
        with self.assertRaisesRegex(ValueError, "GOV-PARSE-FIELDS-INVALID"):
            parse_partition_record({"unexpected": "value"})
        auth = ActivityAuthorization(
            audience="detector_facing", action="truth_unlock", profile_revision_id="profile-action",
            scope_slots=(("track", "sha256:" + "a" * 64),), input_ids=(), prerequisite_ids=(),
            expected_output_roles=("detector_bundle",), owner_id="owner", decision="approved",
            created_at="2026-01-01T00:00:00Z", limitations=(), planned_activity_id="",
        ).with_computed_id()
        self.assertFalse(validate_activity_authorization(auth, profile=GovernanceProfile(
            "profile-action", "detector_facing", required_scope_slots=("track",), action="truth_unlock",
            expected_output_roles=("detector_bundle",),
        )).allowed)

    def test_pretruth_freeze_requires_blind_predecessor_and_rejects_truth_taint(self) -> None:
        slots = GovernanceProfile.sentinel_pretruth_freeze().required_binding_slots
        bindings = tuple((slot, self.digest(chr(97 + index))) for index, slot in enumerate(slots))
        predecessor = self.digest("f")
        freeze = ScientificFreeze(
            audience="evaluator_restricted", stage="pretruth_evaluation", profile_revision_id="profile-pretruth",
            created_at="2026-01-01T00:00:00Z", bindings=bindings, predecessor_freeze_id=predecessor,
        )
        self.assertTrue(validate_scientific_freeze(
            freeze, profile=GovernanceProfile.sentinel_pretruth_freeze(), predecessor_stages={predecessor: "blind_scoring"},
        ).allowed)
        denied = validate_scientific_freeze(
            freeze, profile=GovernanceProfile.sentinel_pretruth_freeze(), predecessor_stages={predecessor: "calibration"},
            truth_tainted_ids=(bindings[0][1],),
        )
        self.assertFalse(denied.allowed)
        self.assertEqual({"GOV-FREEZE-PREDECESSOR", "GOV-FREEZE-TRUTH-TAINT"}, {item.rule_id for item in denied.violations})

    def test_truth_unlock_closes_each_support_unit_and_join_blocks_detector_taint(self) -> None:
        support = (self.digest("a"), self.digest("b"))
        score = tuple(SupportDisposition(item, self.digest("c"), self.digest("d")) for item in support)
        decisions = tuple(SupportDisposition(item, self.digest("e"), self.digest("f")) for item in support)
        authorization, pretruth, blind = self.digest("1"), self.digest("2"), self.digest("3")
        unlock = TruthUnlockRecord(
            audience="evaluator_restricted", partition_id=self.digest("4"), support_id=self.digest("5"),
            pretruth_freeze_id=pretruth, blind_scoring_freeze_id=blind, score_closure_id=self.digest("6"),
            detector_decision_closure_id=self.digest("7"), completion_receipt_ids=tuple(sorted({item.completion_receipt_id for item in (*score, *decisions)})),
            restricted_truth_id=self.digest("8"), authorization_id=authorization, owner_id="evaluator", decision="granted",
            created_at="2026-01-01T00:00:00Z",
        )
        profile = GovernanceProfile("truth-profile", "evaluator_restricted")
        self.assertTrue(validate_truth_unlock(
            unlock, expected_support_ids=support, score_dispositions=score, decision_dispositions=decisions,
            granted_authorization_id=authorization, pretruth_freeze_id=pretruth, blind_scoring_freeze_id=blind, profile=profile,
        ).allowed)
        self.assertFalse(validate_truth_unlock(
            unlock, expected_support_ids=support, score_dispositions=score[:-1], decision_dispositions=decisions,
            granted_authorization_id=authorization, pretruth_freeze_id=pretruth, blind_scoring_freeze_id=blind, profile=profile,
        ).allowed)
        join = TruthJoinRecord(
            audience="evaluator_restricted", unlock_id=self.digest("9"), authorization_id=self.digest("a"),
            partition_id=self.digest("4"), support_id=self.digest("5"), freeze_id=pretruth, score_id=self.digest("6"),
            detector_decision_id=self.digest("7"), restricted_truth_id=unlock.restricted_truth_id,
            evaluator_identity="evaluator", join_outcome="joined", created_at="2026-01-01T00:00:00Z",
        )
        self.assertFalse(validate_truth_join(
            join, unlock_id=join.unlock_id, authorization_id=join.authorization_id, profile=profile,
            detector_references=(unlock.restricted_truth_id,),
        ).allowed)


if __name__ == "__main__":
    unittest.main()
