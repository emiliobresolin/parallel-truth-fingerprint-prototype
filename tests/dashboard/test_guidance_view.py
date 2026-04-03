"""Focused tests for Story 5.4 dashboard guidance views."""

from __future__ import annotations

import unittest

from parallel_truth_fingerprint.dashboard.guidance_view import (
    build_dashboard_guidance_view,
)


def _sample_runtime_payload() -> dict[str, object]:
    return {
        "runtime": {
            "status": "active",
            "current_cycle": 4,
        },
        "latest_cycle": {
            "scenario_control": {
                "active_scenario": "scada_replay",
            },
            "consensus_summary": {
                "final_consensus_status": "success",
            },
            "fingerprint_lifecycle": {
                "model_status": "model_available",
                "inference_status": "completed",
            },
            "replay_behavior": {
                "classification": "anomalous",
                "scenario_mode": "replay",
            },
            "scada_divergence_alert": {
                "structured": {
                    "divergent_sensors": ["temperature"],
                }
            },
        },
    }


def _sample_explainability() -> dict[str, object]:
    return {
        "what_changed_since_startup": {
            "questions_answered": {
                "what_changed_since_startup": "The run accumulated artifacts and created a reusable model.",
                "what_evidence_exists_in_this_run": "Artifacts, model metadata, and replay output exist.",
            },
            "happened_already": [
                "The runtime has completed 4 cycles in this run.",
                "The run has already persisted 4 valid artifacts.",
            ],
            "not_happened_yet": [
                "The dataset adequacy target has not been reached yet.",
            ],
            "expected_next": {
                "summary": "Reuse the saved model on later cycles.",
            },
        }
    }


class DashboardGuidanceViewTests(unittest.TestCase):
    def test_guidance_view_produces_required_panels(self) -> None:
        guidance = build_dashboard_guidance_view(
            latest_runtime_payload=_sample_runtime_payload(),
            explainability=_sample_explainability(),
            limitation_note="Runtime-valid only.",
        )

        self.assertEqual(
            [panel["title"] for panel in guidance["panels"]],
            [
                "What Is Happening",
                "What Should Happen",
                "What Changed",
                "Evidence Signals",
            ],
        )
        self.assertIn("raw logs", guidance["raw_evidence_note"])

    def test_guidance_view_keeps_ml_limitation_and_channel_distinction_explicit(self) -> None:
        guidance = build_dashboard_guidance_view(
            latest_runtime_payload=_sample_runtime_payload(),
            explainability=_sample_explainability(),
            limitation_note="Runtime-valid only.",
        )

        what_should_happen = guidance["panels"][1]["bullets"]
        evidence_signals = guidance["panels"][3]["bullets"]
        self.assertTrue(
            any("Replay or freeze should show up through the fingerprint/replay behavior path" in bullet for bullet in what_should_happen)
        )
        self.assertTrue(
            any("Runtime-valid only." in bullet for bullet in evidence_signals)
        )


if __name__ == "__main__":
    unittest.main()
