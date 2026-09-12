"""Focused offline tests for Story 13.3's fair physical candidate protocol."""
from __future__ import annotations

import unittest
from dataclasses import replace

from parallel_truth_fingerprint.contracts.physical_candidate_comparison import (
    PHYSICAL_CANDIDATE_COMPARISON_SCHEMA, CandidateRunStatus, ComparisonDisposition,
    FrozenPhysicalComparisonPlan, PhysicalCandidate, PhysicalCandidateComparisonRecord,
    PhysicalCandidateRun, physical_comparison_plan_content_id,
)
from parallel_truth_fingerprint.evidence.physical_candidate_comparison import (
    finalize_physical_candidate_comparison, validate_frozen_physical_comparison_plan,
    validate_physical_candidate_comparison,
)


def digest(number: int) -> str:
    return "sha256:" + f"{number:064x}"


class PhysicalCandidateComparisonTests(unittest.TestCase):
    def resolve(self, value: str) -> bool:
        return value.startswith("sha256:")

    def plan(self) -> FrozenPhysicalComparisonPlan:
        candidates = (
            PhysicalCandidate(digest(1), "lstm_ae", digest(2), digest(3), digest(4)),
            PhysicalCandidate(digest(5), "gru_ae", digest(6), digest(7), digest(8), (digest(9),)),
            PhysicalCandidate(digest(10), "transparent_baseline", digest(11), digest(12), digest(13)),
        )
        provisional = FrozenPhysicalComparisonPlan(
            PHYSICAL_CANDIDATE_COMPARISON_SCHEMA, digest(14), digest(15), digest(16), digest(17),
            digest(18), digest(19), digest(20), digest(21), digest(22), (digest(23),), (digest(24), digest(25)),
            candidates, "",
        )
        return replace(provisional, plan_content_id=physical_comparison_plan_content_id(provisional))

    def record(self, plan: FrozenPhysicalComparisonPlan, **changes: object) -> PhysicalCandidateComparisonRecord:
        runs = tuple(PhysicalCandidateRun(
            candidate.candidate_id, repetition, plan.feature_schema_id, plan.partition_id,
            plan.preprocessing_state_id, plan.normal_training_evidence_id, plan.validation_evidence_id,
            plan.tuning_access_id, plan.resource_budget_id, candidate.configuration_id, CandidateRunStatus.COMPLETE,
            (digest(30 + index),), (digest(40 + index),), (digest(50 + index),), (digest(60 + index),),
            candidate.preregistered_exception_ids,
        ) for index, (candidate, repetition) in enumerate(
            (candidate, repetition) for candidate in plan.candidates for repetition in plan.repetition_ids
        ))
        values: dict[str, object] = dict(schema_version=PHYSICAL_CANDIDATE_COMPARISON_SCHEMA,
            plan_content_id=plan.plan_content_id, run_records=runs,
            selected_candidate_id=plan.candidates[0].candidate_id, selection_record_id=digest(70),
            non_selected_candidate_ids=tuple(candidate.candidate_id for candidate in plan.candidates[1:]),
            disposition=ComparisonDisposition.COMPLETE, diagnostic_codes=(), record_content_id="")
        values.update(changes)
        return PhysicalCandidateComparisonRecord(**values)

    def test_frozen_plan_requires_three_families_and_hashed_content(self) -> None:
        plan = self.plan()
        self.assertTrue(validate_frozen_physical_comparison_plan(plan, immutable_resolver=self.resolve).valid)
        invalid = replace(plan, candidates=plan.candidates[:2])
        result = validate_frozen_physical_comparison_plan(invalid, immutable_resolver=self.resolve)
        self.assertIn("PCC13_REQUIRED_CANDIDATES_MISSING", result.diagnostic_codes)

    def test_complete_comparison_retains_every_candidate_repetition(self) -> None:
        plan = self.plan()
        result = finalize_physical_candidate_comparison(self.record(plan), plan=plan, immutable_resolver=self.resolve)
        validation = validate_physical_candidate_comparison(result, plan=plan, immutable_resolver=self.resolve)
        self.assertTrue(validation.valid)
        self.assertEqual(ComparisonDisposition.COMPLETE, result.disposition)

    def test_missing_run_and_changed_shared_input_fail_closed(self) -> None:
        plan = self.plan(); record = self.record(plan)
        short = replace(record, run_records=record.run_records[:-1])
        result = validate_physical_candidate_comparison(short, plan=plan, immutable_resolver=self.resolve)
        self.assertIn("PCC13_PLANNED_RUN_CLOSURE_INCOMPLETE", result.diagnostic_codes)
        wrong = replace(record.run_records[0], partition_id=digest(900))
        changed = replace(record, run_records=(wrong, *record.run_records[1:]))
        result = validate_physical_candidate_comparison(changed, plan=plan, immutable_resolver=self.resolve)
        self.assertIn("PCC13_FAIR_INPUT_MISMATCH", result.diagnostic_codes)

    def test_failure_is_retained_not_cherry_picked_and_selection_closure_is_required(self) -> None:
        plan = self.plan(); record = self.record(plan)
        failed = replace(record.run_records[0], status=CandidateRunStatus.FAILED)
        retained = replace(record, run_records=(failed, *record.run_records[1:]))
        result = finalize_physical_candidate_comparison(retained, plan=plan, immutable_resolver=self.resolve)
        self.assertTrue(validate_physical_candidate_comparison(result, plan=plan, immutable_resolver=self.resolve).valid)
        bad = replace(record, non_selected_candidate_ids=(plan.candidates[1].candidate_id,))
        result = validate_physical_candidate_comparison(bad, plan=plan, immutable_resolver=self.resolve)
        self.assertIn("PCC13_NONSELECTED_OUTCOMES_INCOMPLETE", result.diagnostic_codes)

    def test_unresolved_evidence_and_noncompleted_selection_are_rejected(self) -> None:
        plan = self.plan(); record = self.record(plan)
        unresolved = replace(record.run_records[0], output_ids=("not-an-id",))
        result = validate_physical_candidate_comparison(replace(record, run_records=(unresolved, *record.run_records[1:])), plan=plan, immutable_resolver=self.resolve)
        self.assertIn("PCC13_RUN_EVIDENCE_UNRESOLVED", result.diagnostic_codes)
        blocked = tuple(replace(run, status=CandidateRunStatus.BLOCKED) if run.candidate_id == plan.candidates[0].candidate_id else run for run in record.run_records)
        result = validate_physical_candidate_comparison(replace(record, run_records=blocked), plan=plan, immutable_resolver=self.resolve)
        self.assertIn("PCC13_SELECTION_CANDIDATE_INVALID", result.diagnostic_codes)


if __name__ == "__main__":
    unittest.main()
