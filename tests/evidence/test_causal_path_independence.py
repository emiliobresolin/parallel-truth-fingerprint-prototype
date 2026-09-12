"""Offline tests for Story 12.5 causal-path independence contracts."""
from __future__ import annotations

import unittest
from dataclasses import replace

from parallel_truth_fingerprint.contracts.causal_path_independence import (
    CausalIndependenceDisposition, CausalPathCase, CausalPathTrace,
    CausalVariation, causal_path_independence_content_id,
)
from parallel_truth_fingerprint.evidence.causal_path_independence import assess_causal_path_independence


def digest(number: int) -> str:
    return "sha256:" + f"{number:064x}"


class CausalPathIndependenceTests(unittest.TestCase):
    def trace(self, offset: int, **changes: object) -> CausalPathTrace:
        values: dict[str, object] = {
            "trace_id": digest(offset), "snapshot_id": digest(1), "writer_id": digest(2), "server_id": digest(3),
            "client_id": digest(4), "opc_condition_id": digest(5), "opc_evidence_state": "available",
            "opc_observation_id": digest(6), "opc_evidence_valid": True, "opc_fallback_kind": "none",
            "consensus_configuration_id": digest(7), "consensus_input_id": digest(8), "consensus_decision_id": digest(9),
            "comparison_id": digest(10), "opc_lineage_snapshot_id": digest(1), "consensus_lineage_snapshot_id": digest(1),
        }
        values.update(changes)
        return CausalPathTrace(**values)

    def case(self, variation: CausalVariation, baseline: CausalPathTrace, varied: CausalPathTrace, number: int) -> CausalPathCase:
        return CausalPathCase(digest(number), variation, baseline, varied, (digest(number + 100),))

    def complete_matrix(self) -> tuple[CausalPathCase, ...]:
        baseline = self.trace(20)
        consensus_changed = self.trace(21, consensus_configuration_id=digest(70))
        opc_changed = self.trace(22, opc_condition_id=digest(71), client_id=digest(72), opc_observation_id=digest(73))
        source_changed = self.trace(23, snapshot_id=digest(74), opc_observation_id=digest(75), consensus_input_id=digest(76), consensus_decision_id=digest(77), opc_lineage_snapshot_id=digest(74), consensus_lineage_snapshot_id=digest(74))
        unavailable = self.trace(24, opc_condition_id=digest(78), opc_evidence_state="unavailable", opc_observation_id=None, opc_evidence_valid=False)
        return (
            self.case(CausalVariation.CONSENSUS_ONLY, baseline, consensus_changed, 30),
            self.case(CausalVariation.OPC_ONLY, baseline, opc_changed, 31),
            self.case(CausalVariation.COMMON_SOURCE, baseline, source_changed, 32),
            self.case(CausalVariation.OPC_UNAVAILABLE, baseline, unavailable, 33),
        )

    def test_complete_controlled_matrix_is_demonstrated_but_never_authorizing(self) -> None:
        result = assess_causal_path_independence(self.complete_matrix(), immutable_resolver=lambda _: True)
        self.assertEqual(CausalIndependenceDisposition.DEMONSTRATED, result.disposition)
        self.assertEqual("none", result.authorization_effect)
        self.assertEqual(causal_path_independence_content_id(result), result.result_content_id)
        self.assertIn("logical and transport-path independence only", result.limitations[0])

    def test_consensus_change_that_changes_opc_is_a_violation(self) -> None:
        cases = list(self.complete_matrix())
        case = cases[0]
        cases[0] = replace(case, varied=replace(case.varied, opc_observation_id=digest(999)))
        result = assess_causal_path_independence(tuple(cases), immutable_resolver=lambda _: True)
        self.assertEqual(CausalIndependenceDisposition.VIOLATED, result.disposition)
        self.assertIn("CPI_CONSENSUS_CHANGE_LEAKED_TO_OPC", {code for check in result.checks for code in check.diagnostic_codes})

    def test_opc_change_that_changes_consensus_is_a_violation(self) -> None:
        cases = list(self.complete_matrix())
        case = cases[1]
        cases[1] = replace(case, varied=replace(case.varied, consensus_decision_id=digest(999)))
        result = assess_causal_path_independence(tuple(cases), immutable_resolver=lambda _: True)
        self.assertEqual(CausalIndependenceDisposition.VIOLATED, result.disposition)
        self.assertIn("CPI_OPC_CHANGE_LEAKED_TO_CONSENSUS", {code for check in result.checks for code in check.diagnostic_codes})

    def test_opc_outage_cannot_be_replaced_by_cached_or_consensus_evidence(self) -> None:
        cases = list(self.complete_matrix())
        case = cases[-1]
        cases[-1] = replace(case, varied=replace(case.varied, opc_fallback_kind="consensus_projected", opc_evidence_valid=True, opc_observation_id=digest(900)))
        result = assess_causal_path_independence(tuple(cases), immutable_resolver=lambda _: True)
        self.assertEqual(CausalIndependenceDisposition.VIOLATED, result.disposition)
        self.assertIn("CPI_OPC_FALLBACK_USED", {code for check in result.checks for code in check.diagnostic_codes})

    def test_missing_or_unresolved_trace_evidence_fails_closed(self) -> None:
        incomplete = assess_causal_path_independence(self.complete_matrix()[:-1], immutable_resolver=lambda _: True)
        self.assertEqual(CausalIndependenceDisposition.INCOMPLETE, incomplete.disposition)
        blocked = assess_causal_path_independence(self.complete_matrix(), immutable_resolver=lambda value: value != digest(1))
        self.assertEqual(CausalIndependenceDisposition.BLOCKED, blocked.disposition)


if __name__ == "__main__":
    unittest.main()
