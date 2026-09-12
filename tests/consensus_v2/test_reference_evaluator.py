"""Focused tests for the isolated, fail-closed reference boundary."""
from __future__ import annotations

import unittest
import hashlib
from types import SimpleNamespace

from parallel_truth_fingerprint.consensus_v2.reference_evaluator import (
    ConsensusReferenceStatus,
    evaluate_consensus_v2_reference,
)
from parallel_truth_fingerprint.consensus_v2_parameters import (
    ConsensusParameterValidationResult,
)
from parallel_truth_fingerprint.evidence.consensus_contract_validation import (
    ConsensusContractValidation,
)
from parallel_truth_fingerprint.consensus_v2.reference_inputs import (
    ConsensusEvaluationObservationV2, ConsensusOperationClosureV2, MEAN_CURRENT_RESIDUAL_V1,
)
from parallel_truth_fingerprint.contracts.consensus_v2 import (
    ConsensusRoundInputV2, consensus_round_input_content_id,
)


def _id(name: str) -> str:
    return "sha256:" + hashlib.sha256(name.encode("ascii")).hexdigest()


class ReferenceEvaluatorTests(unittest.TestCase):
    def setUp(self) -> None:
        self.round_input = SimpleNamespace(to_dict=lambda: {"input_content_id": "sha256:" + "1" * 64})
        self.parameter_set = SimpleNamespace(parameter_set_id="sha256:" + "2" * 64)

    def _operation(self, *, budget: int = 3) -> ConsensusOperationClosureV2:
        content = MEAN_CURRENT_RESIDUAL_V1
        vector = (_id("conformance"),)
        operation_id = _id(content)
        return ConsensusOperationClosureV2(
            operation_id, content, _id(content), vector,
            "sha256:" + hashlib.sha256("\n".join(vector).encode("ascii")).hexdigest(),
            2, "1.0", budget, {"no_ranking": _id("no-ranking"), "residual": _id("residual")},
        )

    def _real_round(self) -> ConsensusRoundInputV2:
        basis_bytes = "basis-v2"
        rows = []
        for edge in (_id("edge-a"), _id("edge-b")):
            rows.append({"edge_id": edge, "observation_id": _id("obs-" + edge),
                "observation_canonical_hash": _id("bytes-" + edge), "profile_id": _id("profile"),
                "source_sequence": 1, "correlation_id": _id("correlation-" + edge), "raw_current_unit": "mA"})
        rows.sort(key=lambda row: (row["edge_id"], row["source_sequence"], row["observation_id"]))
        payload = {"schema_version": "Consensus.v2", "experiment_id": _id("experiment"), "run_id": _id("run"),
            "round_id": _id("round"), "qualification_result_id": _id("qualification"),
            "comparison_basis": {"basis_id": _id("basis"), "schema_version": "Basis.v2", "canonical_bytes": basis_bytes,
                "canonical_bytes_hash": _id(basis_bytes), "kind": "same_profile_raw_current", "unit": "mA",
                "profile_ids": [_id("profile")], "uncertainty_parameter_ids": []},
            "quality_policy_ids": [_id("quality")], "parameter_ids": [], "observations": rows,
            "input_content_id": "", "authorization_effect": "none"}
        payload["input_content_id"] = consensus_round_input_content_id(payload)
        return ConsensusRoundInputV2(payload)

    def _bind_parameters(self, round_input: ConsensusRoundInputV2, operation: ConsensusOperationClosureV2) -> None:
        data = round_input.to_dict()
        self.parameter_set.comparison_basis_id = data["comparison_basis"]["basis_id"]
        self.parameter_set.profile_id = data["comparison_basis"]["profile_ids"][0]
        self.parameter_set.quality_policy_id = data["quality_policy_ids"][0]
        self.parameter_set.residual_policy_id = operation.operation_id
        self.parameter_set.residual_policy_canonical_bytes_sha256 = operation.canonical_bytes_hash
        self.parameter_set.residual_policy_conformance_id = operation.conformance_vector_hash

    def test_validated_declarations_do_not_invent_an_operation_or_decision(self) -> None:
        result = evaluate_consensus_v2_reference(
            self.round_input, self.parameter_set, ConsensusContractValidation(True, ()),
            ConsensusParameterValidationResult("valid", self.parameter_set.parameter_set_id, ()),
        )
        self.assertEqual(ConsensusReferenceStatus.BLOCKED, result.status)
        self.assertIsNone(result.decision)
        self.assertEqual((), result.trace.events)
        self.assertEqual(("CV2_REFERENCE_OPERATION_INPUT_UNAVAILABLE",), result.diagnostics)

    def test_validation_blockers_are_retained_in_canonical_order(self) -> None:
        result = evaluate_consensus_v2_reference(
            self.round_input, self.parameter_set,
            ConsensusContractValidation(False, ("Z_CONTRACT", "A_CONTRACT")),
            ConsensusParameterValidationResult("blocked", self.parameter_set.parameter_set_id, ()),
        )
        self.assertEqual(tuple(sorted(result.diagnostics)), result.diagnostics)
        self.assertIn("CV2_REFERENCE_CONTRACT_BLOCKED", result.diagnostics)
        self.assertIn("CV2_REFERENCE_PARAMETER_BLOCKED", result.diagnostics)
        self.assertIn("CV2_REFERENCE_OPERATION_INPUT_UNAVAILABLE", result.diagnostics)

    def test_closed_exact_projection_produces_canonical_success_and_trace(self) -> None:
        round_input = self._real_round()
        operation = self._operation()
        self._bind_parameters(round_input, operation)
        projections = tuple(ConsensusEvaluationObservationV2(
            row["edge_id"], row["observation_id"], row["observation_canonical_hash"], value, None, _id("eligible-" + row["edge_id"])
        ) for row, value in zip(round_input.to_dict()["observations"], ("10.0", "10.5")))
        result = evaluate_consensus_v2_reference(round_input, self.parameter_set, ConsensusContractValidation(True, ()),
            ConsensusParameterValidationResult("valid", self.parameter_set.parameter_set_id, ()), operation, projections)
        self.assertEqual(ConsensusReferenceStatus.EVALUATED, result.status)
        self.assertEqual("success", result.decision.to_dict()["outcome"])
        self.assertEqual(3, len(result.trace.events))

    def test_trace_budget_blocks_before_a_decision(self) -> None:
        round_input = self._real_round()
        operation = self._operation(budget=2)
        self._bind_parameters(round_input, operation)
        projections = tuple(ConsensusEvaluationObservationV2(
            row["edge_id"], row["observation_id"], row["observation_canonical_hash"], "10.0", None, _id("eligible-" + row["edge_id"])
        ) for row in round_input.to_dict()["observations"])
        result = evaluate_consensus_v2_reference(round_input, self.parameter_set, ConsensusContractValidation(True, ()),
            ConsensusParameterValidationResult("valid", self.parameter_set.parameter_set_id, ()), operation, projections)
        self.assertEqual(ConsensusReferenceStatus.BLOCKED, result.status)
        self.assertIsNone(result.decision)
        self.assertIn("CV2_REFERENCE_TRACE_BUDGET_EXCEEDED", result.diagnostics)

    def test_ineligible_or_insufficient_projection_is_explicit_no_ranking_failure(self) -> None:
        round_input = self._real_round()
        operation = self._operation()
        self._bind_parameters(round_input, operation)
        rows = round_input.to_dict()["observations"]
        projections = tuple(ConsensusEvaluationObservationV2(
            row["edge_id"], row["observation_id"], row["observation_canonical_hash"], "10.0",
            _id("quality-invalid") if index == 0 else None, _id("evidence-" + row["edge_id"])
        ) for index, row in enumerate(rows))
        result = evaluate_consensus_v2_reference(round_input, self.parameter_set, ConsensusContractValidation(True, ()),
            ConsensusParameterValidationResult("valid", self.parameter_set.parameter_set_id, ()), operation, projections)
        self.assertEqual("failure", result.decision.to_dict()["outcome"])
        self.assertEqual([], result.decision.to_dict()["ranking"])
        self.assertEqual([], result.decision.to_dict()["included_ids"])


if __name__ == "__main__":
    unittest.main()
