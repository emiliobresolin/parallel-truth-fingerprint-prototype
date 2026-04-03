"""Focused tests for Story 5.1 interpreted dashboard events."""

from __future__ import annotations

import unittest

from parallel_truth_fingerprint.dashboard.event_timeline import (
    COMPONENT_IDS,
    build_dashboard_event_views,
)


def _sample_runtime_payload() -> dict[str, object]:
    return {
        "runtime": {
            "status": "active",
            "current_cycle": 3,
            "completed_cycles": 3,
            "cycle_interval_seconds": 60.0,
        },
        "cycle_history": [
            {
                "cycle_index": 1,
                "round_id": "round-001",
                "final_consensus_status": "success",
                "scenario_control": {
                    "active_scenario": "normal",
                },
                "fingerprint_lifecycle": {
                    "model_status": "no_model_yet",
                    "training_events": ["deferred"],
                    "inference_status": "skipped_no_model",
                },
                "replay_behavior": None,
            },
            {
                "cycle_index": 2,
                "round_id": "round-002",
                "final_consensus_status": "success",
                "scenario_control": {
                    "active_scenario": "normal",
                },
                "fingerprint_lifecycle": {
                    "model_status": "model_available",
                    "training_events": ["started", "completed"],
                    "inference_status": "skipped_until_next_cycle",
                },
                "replay_behavior": None,
            },
        ],
        "latest_cycle": {
            "runtime_cycle": {"current_cycle": 3},
            "simulator_snapshot": {
                "compressor_id": "compressor-1",
                "operating_state_pct": 80.0,
                "sensors": {
                    "temperature": 82.0,
                    "pressure": 5.4,
                    "rpm": 3510.0,
                },
            },
            "edges": [
                {
                    "summary": "edge-1: published=3 consumed=6 complete=True validated=False view[pressure=5.4, rpm=3510.0, temperature=82.0]",
                    "runtime_state": {
                        "edge_id": "edge-1",
                        "published_observation_count": 3,
                    },
                    "replicated_state": {"is_complete": True},
                    "observation_flow": [],
                },
                {
                    "summary": "edge-2: published=3 consumed=6 complete=True validated=False view[pressure=5.4, rpm=3510.0, temperature=82.0]",
                    "runtime_state": {
                        "edge_id": "edge-2",
                        "published_observation_count": 3,
                    },
                    "replicated_state": {"is_complete": True},
                    "observation_flow": [],
                },
                {
                    "summary": "edge-3: published=3 consumed=6 complete=True validated=False view[pressure=5.4, rpm=3510.0, temperature=82.0]",
                    "runtime_state": {
                        "edge_id": "edge-3",
                        "published_observation_count": 3,
                    },
                    "replicated_state": {"is_complete": True},
                    "observation_flow": [],
                },
            ],
            "consensus_summary": {
                "round_id": "round-003",
                "final_consensus_status": "success",
            },
            "consensus_log": {
                "structured": {
                    "status": "committed",
                }
            },
            "consensus_alert": None,
            "committed_round_state": {
                "round_id": "round-003",
            },
            "scada_state": {
                "source_round_id": "round-003",
                "sensor_values": {
                    "temperature": {"value": 82.0, "mode": "match"},
                    "pressure": {"value": 5.4, "mode": "match"},
                    "rpm": {"value": 3510.0, "mode": "match"},
                },
            },
            "comparison_output": {
                "divergent_sensors": ["temperature"],
                "sensor_outputs": [
                    {
                        "sensor_name": "temperature",
                        "physical_value": 82.0,
                        "scada_value": 88.0,
                        "divergence_classification": "divergent",
                    },
                    {
                        "sensor_name": "pressure",
                        "physical_value": 5.4,
                        "scada_value": 5.4,
                        "divergence_classification": "match",
                    },
                    {
                        "sensor_name": "rpm",
                        "physical_value": 3510.0,
                        "scada_value": 3510.0,
                        "divergence_classification": "match",
                    },
                ],
            },
            "scada_divergence_alert": {
                "structured": {
                    "divergent_sensors": ["temperature"],
                }
            },
            "scada_runtime_scenario": {
                "active": False,
                "mode": "match",
            },
            "fingerprint_lifecycle": {
                "cycle_index": 3,
                "model_status": "model_available",
                "training_events": ["reused"],
                "inference_status": "completed",
                "source_dataset_validation_level": "runtime_valid_only",
                "valid_artifact_count": 3,
            },
            "fingerprint_inference_results": [
                {
                    "classification": "normal",
                    "output_channel": "lstm_fingerprint",
                }
            ],
            "replay_behavior": {
                "output_channel": "scada_replay_behavior",
                "classification": "anomalous",
                "scenario_mode": "replay",
            },
            "replay_inference_results": [],
        },
    }


class DashboardEventTimelineTests(unittest.TestCase):
    def test_build_dashboard_event_views_supports_all_required_components(self) -> None:
        event_views = build_dashboard_event_views(
            generated_at="2026-04-02T00:00:00+00:00",
            latest_runtime_payload=_sample_runtime_payload(),
            operator_actions=[
                {
                    "action": "set_power",
                    "applied_at": "2026-04-02T00:00:00+00:00",
                    "applies_on_cycle": 3,
                    "configuration_change": {"demo_power": 80.0},
                    "note": "Power updated.",
                }
            ],
        )

        self.assertTrue(event_views["global_timeline"])
        self.assertEqual(
            tuple(component["id"] for component in event_views["components"]),
            COMPONENT_IDS,
        )
        for component_id in COMPONENT_IDS:
            self.assertIn(component_id, event_views["component_timelines"])
            self.assertIn(component_id, event_views["component_raw_logs"])
            self.assertTrue(event_views["component_timelines"][component_id])

    def test_component_raw_logs_preserve_component_ground_truth_payloads(self) -> None:
        event_views = build_dashboard_event_views(
            generated_at="2026-04-02T00:00:00+00:00",
            latest_runtime_payload=_sample_runtime_payload(),
            operator_actions=[],
        )

        self.assertEqual(
            event_views["component_raw_logs"]["compressor"]["simulator_snapshot"][
                "operating_state_pct"
            ],
            80.0,
        )
        self.assertEqual(
            event_views["component_raw_logs"]["temperature_sensor"][
                "comparison_sensor_output"
            ]["divergence_classification"],
            "divergent",
        )
        self.assertEqual(
            event_views["component_raw_logs"]["consensus"]["summary"][
                "final_consensus_status"
            ],
            "success",
        )
        self.assertEqual(
            event_views["component_raw_logs"]["fingerprint_lifecycle"]["lifecycle"][
                "model_status"
            ],
            "model_available",
        )

    def test_operator_actions_are_reflected_in_interpreted_events(self) -> None:
        event_views = build_dashboard_event_views(
            generated_at="2026-04-02T00:00:00+00:00",
            latest_runtime_payload=_sample_runtime_payload(),
            operator_actions=[
                {
                    "action": "set_power",
                    "applied_at": "2026-04-02T00:00:00+00:00",
                    "applies_on_cycle": 3,
                    "configuration_change": {"demo_power": 80.0},
                    "note": "Power updated.",
                },
                {
                    "action": "set_scenario",
                    "applied_at": "2026-04-02T00:01:00+00:00",
                    "applies_on_cycle": 4,
                    "configuration_change": {"demo_scenario_name": "scada_replay"},
                    "note": "Scenario updated.",
                },
            ],
        )

        compressor_messages = [
            event["message"]
            for event in event_views["component_timelines"]["compressor"]
        ]
        scada_messages = [
            event["message"]
            for event in event_views["component_timelines"]["scada_comparison"]
        ]
        self.assertTrue(
            any("Operator set compressor power" in message for message in compressor_messages)
        )
        self.assertTrue(
            any("Operator activated scenario scada_replay" in message for message in scada_messages)
        )


if __name__ == "__main__":
    unittest.main()
