from __future__ import annotations

import hashlib
import unittest

from parallel_truth_fingerprint.contracts.consensus_v2 import (
    CONSENSUS_V2_SCHEMA, ConsensusDecisionV2, ConsensusRoundInputV2, ConsensusV2Error,
    consensus_decision_content_id, consensus_round_input_content_id, parse_consensus_round_input_v2_json,
)
from parallel_truth_fingerprint.evidence.consensus_contract_validation import (
    ConsensusContractResolver, validate_consensus_decision_v2, validate_consensus_round_input_v2,
)


def ident(seed: int) -> str: return "sha256:" + f"{seed:064x}"


def basis(kind="same_profile_raw_current"):
    text = '{"version":"basis.v1"}'
    return {"basis_id": ident(1), "schema_version": "basis.v1", "canonical_bytes": text,
            "canonical_bytes_hash": "sha256:" + hashlib.sha256(text.encode("ascii")).hexdigest(), "kind": kind,
            "unit": "mA" if kind == "same_profile_raw_current" else "one",
            "profile_ids": [ident(2)] if kind == "same_profile_raw_current" else [ident(2), ident(3)],
            "uncertainty_parameter_ids": [] if kind == "same_profile_raw_current" else [ident(4)]}


def input_payload(kind="same_profile_raw_current"):
    data = {"schema_version": CONSENSUS_V2_SCHEMA, "experiment_id": ident(10), "run_id": ident(11), "round_id": ident(12),
            "qualification_result_id": ident(13), "comparison_basis": basis(kind), "quality_policy_ids": [ident(5)], "parameter_ids": [ident(4)] if kind != "same_profile_raw_current" else [],
            "observations": [{"edge_id": ident(20), "observation_id": ident(21), "observation_canonical_hash": ident(22), "profile_id": ident(2), "source_sequence": 1, "correlation_id": ident(23), "raw_current_unit": "mA"}],
            "input_content_id": ident(0), "authorization_effect": "none"}
    data["input_content_id"] = consensus_round_input_content_id(data)
    return data


class ConsensusV2ContractTests(unittest.TestCase):
    def resolver(self):
        dependency = lambda _: {"immutable": True, "audience": "public", "semantic_tokens": (), "provenance_tokens": ()}
        return ConsensusContractResolver(lambda _: True, lambda oid: {"observation_content_id": oid, "canonical_hash": ident(22), "profile_id": ident(2), "source_sequence": 1}, lambda _: {"disposition": "qualified", "g2": "pass", "observation_ids": [ident(21)], "closure_ids": [ident(1), ident(2), ident(5)]}, dependency)

    def test_input_is_canonical_and_resolver_closed(self):
        record = ConsensusRoundInputV2(input_payload())
        self.assertEqual(record.canonical_bytes(), ConsensusRoundInputV2(dict(reversed(list(input_payload().items())))).canonical_bytes())
        self.assertTrue(validate_consensus_round_input_v2(record, self.resolver()).valid)

    def test_cross_profile_requires_dimensionless_uncertainty_closure(self):
        data = input_payload("dimensionless_profile_residual")
        data["observations"][0]["profile_id"] = ident(3)
        data["input_content_id"] = consensus_round_input_content_id(data)
        self.assertTrue(ConsensusRoundInputV2(data))
        data = input_payload(); data["comparison_basis"]["unit"] = "one"; data["input_content_id"] = consensus_round_input_content_id(data)
        with self.assertRaisesRegex(ConsensusV2Error, "CV2_RAW_CURRENT_CLOSURE"): ConsensusRoundInputV2(data)

    def test_rejects_malformed_and_unsafe_dependencies(self):
        data = input_payload(); data["extra"] = "no"
        with self.assertRaisesRegex(ConsensusV2Error, "CV2_INPUT_FIELDS"): ConsensusRoundInputV2(data)
        record = ConsensusRoundInputV2(input_payload())
        unsafe = ConsensusContractResolver(lambda _: True, lambda oid: {"observation_content_id": oid, "canonical_hash": ident(22), "profile_id": ident(2), "source_sequence": 1}, lambda _: {"disposition": "qualified", "g2": "pass", "observation_ids": [ident(21)], "closure_ids": [ident(1), ident(2), ident(5)]}, lambda _: {"immutable": True, "audience": "public", "semantic_tokens": ["truth"], "provenance_tokens": ()})
        self.assertFalse(validate_consensus_round_input_v2(record, unsafe).valid)

    def test_json_duplicate_keys_fail_closed(self):
        with self.assertRaisesRegex(ConsensusV2Error, "CV2_DUPLICATE_FIELD"):
            parse_consensus_round_input_v2_json('{"schema_version":"Consensus.v2","schema_version":"Consensus.v2"}')

    def test_failure_is_not_reduced_success(self):
        inp = ConsensusRoundInputV2(input_payload())
        data = {"schema_version": CONSENSUS_V2_SCHEMA, "round_input_id": inp.to_dict()["input_content_id"], "round_input_hash": inp.to_dict()["input_content_id"], "comparison_basis": inp.to_dict()["comparison_basis"], "outcome": "failure", "participant_ids": [ident(20)], "included_ids": [], "excluded": [{"edge_id": ident(20), "reason_id": ident(30), "evidence_ids": [ident(31)]}], "ranking": [], "diagnostics": ["no_quorum"], "decision_content_id": ident(0), "authorization_effect": "none"}
        data["decision_content_id"] = consensus_decision_content_id(data)
        decision = ConsensusDecisionV2(data)
        self.assertTrue(validate_consensus_decision_v2(decision, inp, self.resolver()).valid)
        data["ranking"] = [ident(20)]; data["decision_content_id"] = consensus_decision_content_id(data)
        with self.assertRaisesRegex(ConsensusV2Error, "CV2_FAILURE_NO_RANKING"): ConsensusDecisionV2(data)
