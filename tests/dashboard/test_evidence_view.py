"""Focused tests for Story 5.3 dashboard explainability views."""

from __future__ import annotations

import unittest

from parallel_truth_fingerprint.dashboard.evidence_view import (
    build_dashboard_explainability_view,
)


def _sample_runtime_payload() -> dict[str, object]:
    return {
        "runtime": {
            "status": "active",
            "current_cycle": 4,
            "completed_cycles": 4,
            "latest_valid_artifact_count": 4,
        },
        "cycle_history": [
            {
                "cycle_index": 1,
                "fingerprint_lifecycle": {
                    "valid_artifact_count": 1,
                    "training_events": ["deferred"],
                    "model_status": "no_model_yet",
                },
            },
            {
                "cycle_index": 2,
                "fingerprint_lifecycle": {
                    "valid_artifact_count": 2,
                    "training_events": ["deferred"],
                    "model_status": "no_model_yet",
                },
            },
            {
                "cycle_index": 3,
                "fingerprint_lifecycle": {
                    "valid_artifact_count": 3,
                    "training_events": ["started", "completed"],
                    "model_status": "model_available",
                    "model_metadata_object_key": "fingerprint-models/model-003.json",
                },
            },
            {
                "cycle_index": 4,
                "fingerprint_lifecycle": {
                    "valid_artifact_count": 4,
                    "training_events": ["reused"],
                    "model_status": "model_available",
                    "model_metadata_object_key": "fingerprint-models/model-003.json",
                },
                "replay_behavior": {
                    "classification": "anomalous",
                    "scenario_mode": "replay",
                },
            },
        ],
        "latest_cycle": {
            "consensus_summary": {"final_consensus_status": "success"},
            "fingerprint_lifecycle": {
                "cycle_index": 4,
                "valid_artifact_count": 4,
                "eligible_history_count": 4,
                "eligible_history_threshold": 10,
                "model_status": "model_available",
                "training_events": ["reused"],
                "inference_status": "completed",
                "model_metadata_object_key": "fingerprint-models/model-003.json",
                "source_dataset_validation_level": "runtime_valid_only",
            },
            "fingerprint_inference_results": [
                {
                    "anomaly_score": 0.125,
                    "classification": "normal",
                }
            ],
            "replay_behavior": {
                "anomaly_score": 0.875,
                "classification": "anomalous",
                "scenario_mode": "replay",
            },
        },
    }


class DashboardEvidenceViewTests(unittest.TestCase):
    def test_explainability_view_translates_required_status_labels(self) -> None:
        explainability = build_dashboard_explainability_view(
            generated_at="2026-04-02T00:05:00+00:00",
            latest_runtime_payload=_sample_runtime_payload(),
            operator_actions=[
                {
                    "action": "start_runtime",
                    "applied_at": "2026-04-02T00:00:00+00:00",
                    "effect_scope": "runtime_command_started",
                }
            ],
            limitation_note="Runtime-valid only.",
        )

        translated = explainability["translated_statuses"]
        self.assertEqual(
            translated["model_status"]["raw_value"],
            "model_available",
        )
        self.assertEqual(
            translated["validation_level"]["raw_value"],
            "runtime_valid_only",
        )
        self.assertEqual(
            translated["consensus_status"]["raw_value"],
            "success",
        )
        self.assertEqual(
            translated["replay_behavior"]["raw_value"],
            "anomalous",
        )
        self.assertEqual(
            translated["training_adequacy"]["label"],
            "Training adequacy still below target",
        )
        self.assertEqual(
            translated["anomaly_score"]["label"],
            "Fingerprint anomaly score available",
        )

    def test_explainability_view_builds_what_changed_since_startup_evidence(self) -> None:
        explainability = build_dashboard_explainability_view(
            generated_at="2026-04-02T00:05:00+00:00",
            latest_runtime_payload=_sample_runtime_payload(),
            operator_actions=[
                {
                    "action": "start_runtime",
                    "applied_at": "2026-04-02T00:00:00+00:00",
                    "effect_scope": "runtime_command_started",
                },
                {
                    "action": "runtime_error",
                    "applied_at": "2026-04-02T00:01:00+00:00",
                    "effect_scope": "runtime_error",
                },
                {
                    "action": "start_runtime",
                    "applied_at": "2026-04-02T00:03:00+00:00",
                    "effect_scope": "runtime_command_started",
                },
                {
                    "action": "start_runtime",
                    "applied_at": "2026-04-02T00:04:00+00:00",
                    "effect_scope": "no_change_already_running",
                }
            ],
            limitation_note="Runtime-valid only.",
        )

        evidence = explainability["what_changed_since_startup"]
        self.assertEqual(evidence["runtime_start_time"], "2026-04-02T00:03:00+00:00")
        self.assertEqual(evidence["elapsed_runtime"], "00:02:00")
        self.assertEqual(evidence["current_cycle_count"], 4)
        self.assertEqual(
            evidence["valid_artifact_count_growth"]["growth"],
            3,
        )
        self.assertTrue(evidence["training"]["has_training_happened"])
        self.assertEqual(evidence["training"]["first_training_reference"], "cycle 3")
        self.assertEqual(
            evidence["training"]["current_model_usage"],
            "reused_existing_model",
        )
        self.assertEqual(
            evidence["training"]["current_model_identity"],
            "fingerprint-models/model-003.json",
        )
        self.assertTrue(evidence["happened_already"])
        self.assertTrue(evidence["not_happened_yet"])
        self.assertIn("summary", evidence["expected_next"])


if __name__ == "__main__":
    unittest.main()
