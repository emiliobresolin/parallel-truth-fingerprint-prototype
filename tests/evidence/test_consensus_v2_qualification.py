"""Offline tests for pure, fail-closed Story 11.6 G3 qualification."""
from __future__ import annotations

import unittest

from parallel_truth_fingerprint.contracts.consensus_v2_qualification import (
    ConsensusV2QualificationDisposition, consensus_v2_qualification_content_id,
)
from parallel_truth_fingerprint.evidence.consensus_v2_qualification import (
    ConsensusV2QualificationInput, ParityFixtureEvidence, qualify_consensus_v2,
)


def digest(number: int) -> str: return "sha256:" + f"{number:064x}"


class ConsensusV2QualificationTests(unittest.TestCase):
    def candidate(self, **changes: object) -> ConsensusV2QualificationInput:
        cases = ("valid", "invalid", "missing", "stale", "mixed_profile", "mixed_unit", "boundary", "exclusion", "tie", "failure")
        fixtures = tuple(ParityFixtureEvidence(digest(100 + index), case, digest(200 + index), digest(300 + index), True) for index, case in enumerate(cases))
        values: dict[str, object] = {"primary_configuration_id": digest(1), "closure_ids": (digest(2),), "parity_fixtures": fixtures, "integration_evidence_id": digest(3), "integration_used_real_boundary": True, "state_evidence_id": digest(4), "state_preserved": True, "sensitivity_plan_id": digest(5), "sensitivity_result_ids": (digest(6),), "sensitivity_complete": True, "provenance_ids": (digest(7), digest(8)), "provenance_complete": True, "limitations": ("Non-domain offline fixture evidence only.",)}
        values.update(changes)
        return ConsensusV2QualificationInput(**values)

    def test_complete_resolved_evidence_is_qualified_and_non_authorizing(self) -> None:
        result = qualify_consensus_v2(self.candidate(), immutable_resolver=lambda _: True)
        self.assertEqual(ConsensusV2QualificationDisposition.QUALIFIED, result.disposition)
        self.assertEqual("none", result.authorization_effect)
        self.assertEqual(consensus_v2_qualification_content_id(result), result.result_content_id)

    def test_missing_planned_fixture_is_incomplete(self) -> None:
        result = qualify_consensus_v2(self.candidate(parity_fixtures=()), immutable_resolver=lambda _: True)
        self.assertEqual(ConsensusV2QualificationDisposition.INCOMPLETE, result.disposition)
        self.assertIn("G3_PARITY_CASE_COVERAGE_MISSING", {code for check in result.checks for code in check.diagnostic_codes})

    def test_mismatch_without_retained_diagnostic_blocks(self) -> None:
        fixture = list(self.candidate().parity_fixtures)
        fixture[0] = ParityFixtureEvidence(fixture[0].fixture_id, fixture[0].case_kind, fixture[0].python_result_id, fixture[0].go_result_id, False)
        result = qualify_consensus_v2(self.candidate(parity_fixtures=tuple(fixture)), immutable_resolver=lambda _: True)
        self.assertEqual(ConsensusV2QualificationDisposition.BLOCKED, result.disposition)
        self.assertIn("G3_PARITY_MISMATCH_UNRETAINED", {code for check in result.checks for code in check.diagnostic_codes})

    def test_real_boundary_substitution_leaves_v2_in_shadow(self) -> None:
        result = qualify_consensus_v2(self.candidate(integration_used_real_boundary=False), immutable_resolver=lambda _: True)
        self.assertEqual(ConsensusV2QualificationDisposition.SHADOW, result.disposition)
        self.assertIn("G3_INTEGRATION_BOUNDARY_NOT_REAL", {code for check in result.checks for code in check.diagnostic_codes})

    def test_unresolved_primary_configuration_blocks(self) -> None:
        result = qualify_consensus_v2(self.candidate(), immutable_resolver=lambda value: value != digest(1))
        self.assertEqual(ConsensusV2QualificationDisposition.BLOCKED, result.disposition)


if __name__ == "__main__": unittest.main()
