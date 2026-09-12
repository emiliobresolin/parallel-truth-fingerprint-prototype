import unittest

from parallel_truth_fingerprint.evidence.opc_evidence_comparison import validate_and_compare_opc_evidence


def iid(char: str) -> str:
    return "sha256:" + char * 64


class OpcEvidenceComparisonTests(unittest.TestCase):
    def setUp(self):
        self.resolver = lambda value: value.startswith("sha256:")
        self.observation = {"schema_version":"ScadaObservation.v2", "observation_id":iid("1"), "experiment_id":iid("2"), "run_id":iid("3"), "cycle_id":iid("4"), "correlation_id":iid("5"), "endpoint_id":iid("6"), "namespace_id":iid("7"), "node_id":"ns=2;s=current", "profile_revision_id":iid("8"), "snapshot_revision_id":iid("9"), "source_branch_id":"independent_opc", "status_code":"Good", "source_timestamp":"2026-01-01T00:00:00Z", "server_timestamp":"2026-01-01T00:00:00Z", "fresh":True, "attempt_count":1, "value":"4.0", "unit":"mA", "source_reference":iid("a")}
        self.consensus = {"schema_version":"ConsensusDecision.v2", "decision_id":iid("b"), "experiment_id":iid("2"), "run_id":iid("3"), "cycle_id":iid("4"), "correlation_id":iid("5"), "profile_revision_id":iid("8"), "preconsensus_branch_id":"physical_branch", "value":"4.25", "unit":"mA", "source_reference":iid("c")}
        self.policy = {"schema_version":"OPC-Evidence-Comparison.v1", "policy_id":iid("d"), "basis_id":iid("e"), "basis_kind":"same_profile_raw_current", "unit":"mA", "parameter_ids":{"freshness_limit":iid("f"), "source_server_skew_limit":iid("0"), "comparison_tolerance":iid("1")}}

    def test_eligible_same_profile_current_returns_difference_without_classification(self):
        result = validate_and_compare_opc_evidence(self.observation, self.consensus, self.policy, immutable_resolver=self.resolver)
        self.assertTrue(result.eligible); self.assertEqual(result.difference, "0.25"); self.assertEqual(result.outcome, "eligible_unclassified")

    def test_bad_status_blocks_without_difference(self):
        self.observation["status_code"] = "Uncertain"
        result = validate_and_compare_opc_evidence(self.observation, self.consensus, self.policy, immutable_resolver=self.resolver)
        self.assertFalse(result.eligible); self.assertIn("OPC-CMP-STATUS-NOT-GOOD", result.diagnostics); self.assertIsNone(result.difference)

    def test_stale_mixed_profile_and_shared_branch_are_explicitly_rejected(self):
        self.observation["fresh"] = False; self.consensus["profile_revision_id"] = iid("f"); self.consensus["preconsensus_branch_id"] = "independent_opc"
        result = validate_and_compare_opc_evidence(self.observation, self.consensus, self.policy, immutable_resolver=self.resolver)
        self.assertFalse(result.eligible); self.assertTrue({"OPC-CMP-STALE-OR-UNVERIFIED", "OPC-CMP-PROFILE-MISMATCH", "OPC-CMP-BRANCH-NOT-INDEPENDENT"}.issubset(result.diagnostics))

    def test_missing_parameter_authority_and_cross_profile_basis_fail_closed(self):
        self.policy["parameter_ids"].pop("comparison_tolerance"); self.policy["basis_kind"] = "dimensionless_profile_residual"
        result = validate_and_compare_opc_evidence(self.observation, self.consensus, self.policy, immutable_resolver=self.resolver)
        self.assertFalse(result.eligible); self.assertIn("OPC-CMP-PARAMETER-CLOSURE", result.diagnostics); self.assertIn("OPC-CMP-BASIS-INELIGIBLE", result.diagnostics)

    def test_unknown_schema_or_unresolved_identity_is_invalid(self):
        self.observation["schema_version"] = "ScadaObservation.v9"
        result = validate_and_compare_opc_evidence(self.observation, self.consensus, self.policy, immutable_resolver=lambda _: False)
        self.assertFalse(result.eligible); self.assertIn("OPC-CMP-OBSERVATION-VERSION", result.diagnostics); self.assertIn("OPC-CMP-OBSERVATION-IDENTITY", result.diagnostics)
