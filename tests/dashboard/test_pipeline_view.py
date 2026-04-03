"""Focused tests for Story 5.2 dashboard pipeline views."""

from __future__ import annotations

import unittest

from parallel_truth_fingerprint.dashboard.pipeline_view import (
    build_dashboard_pipeline_view,
)


def _sample_event_views() -> dict[str, object]:
    return {
        "component_timelines": {
            "compressor": [{"message": "Compressor operating at 80.0% with live sensor values."}],
            "temperature_sensor": [{"message": "Temperature Sensor reported 82.0; SCADA comparison classified it as divergent."}],
            "pressure_sensor": [{"message": "Pressure Sensor reported 5.4; SCADA comparison classified it as match."}],
            "rpm_sensor": [{"message": "RPM Sensor reported 3510.0; SCADA comparison classified it as match."}],
            "edge_1": [{"message": "Edge 1 reconstructed a complete shared view."}],
            "edge_2": [{"message": "Edge 2 reconstructed a complete shared view."}],
            "edge_3": [{"message": "Edge 3 reconstructed a complete shared view."}],
            "consensus": [{"message": "Consensus success for round round-003."}],
            "scada_comparison": [{"message": "SCADA comparison currently shows divergence on temperature."}],
            "fingerprint_lifecycle": [{"message": "Fingerprint lifecycle reused the saved model on cycle 3."}],
        }
    }


def _sample_runtime_payload() -> dict[str, object]:
    return {
        "latest_cycle": {
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
                    "runtime_state": {
                        "edge_id": "edge-1",
                        "published_observation_count": 3,
                        "consumed_observation_count": 6,
                    },
                    "replicated_state": {"is_complete": True},
                },
                {
                    "runtime_state": {
                        "edge_id": "edge-2",
                        "published_observation_count": 3,
                        "consumed_observation_count": 6,
                    },
                    "replicated_state": {"is_complete": True},
                },
                {
                    "runtime_state": {
                        "edge_id": "edge-3",
                        "published_observation_count": 3,
                        "consumed_observation_count": 6,
                    },
                    "replicated_state": {"is_complete": True},
                },
            ],
            "consensus_summary": {
                "round_id": "round-003",
                "final_consensus_status": "success",
            },
            "scada_state": {
                "source_round_id": "round-003",
                "sensor_values": {
                    "temperature": {"value": 88.0, "mode": "offset"},
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
            "scada_divergence_alert": {"structured": {"divergent_sensors": ["temperature"]}},
            "fingerprint_lifecycle": {
                "model_status": "model_available",
                "inference_status": "completed",
            },
            "fingerprint_inference_results": [
                {"classification": "normal", "output_channel": "lstm_fingerprint"}
            ],
            "replay_behavior": {
                "classification": "anomalous",
                "output_channel": "scada_replay_behavior",
                "scenario_mode": "replay",
            },
        }
    }


class DashboardPipelineViewTests(unittest.TestCase):
    def test_pipeline_view_includes_required_visual_nodes(self) -> None:
        pipeline = build_dashboard_pipeline_view(
            latest_runtime_payload=_sample_runtime_payload(),
            event_views=_sample_event_views(),
        )

        self.assertEqual(
            [row["id"] for row in pipeline["rows"]],
            ["process", "edges", "decision"],
        )
        titles = [
            node["title"]
            for row in pipeline["rows"]
            for node in row["nodes"]
        ]
        self.assertIn("Compressor", titles)
        self.assertIn("Temperature Sensor", titles)
        self.assertIn("Pressure Sensor", titles)
        self.assertIn("RPM Sensor", titles)
        self.assertIn("Edge 1", titles)
        self.assertIn("Edge 2", titles)
        self.assertIn("Edge 3", titles)
        self.assertIn("Consensus", titles)
        self.assertIn("SCADA Workstation", titles)
        self.assertIn("SCADA Comparison", titles)
        self.assertIn("Fingerprint / LSTM", titles)

    def test_pipeline_view_keeps_scada_source_distinct_and_links_to_component_logs(self) -> None:
        pipeline = build_dashboard_pipeline_view(
            latest_runtime_payload=_sample_runtime_payload(),
            event_views=_sample_event_views(),
        )

        decision_nodes = {
            node["component_id"]: node for node in pipeline["rows"][2]["nodes"]
        }
        self.assertEqual(
            decision_nodes["scada_source"]["log_component_id"],
            "scada_comparison",
        )
        self.assertEqual(
            decision_nodes["scada_source"]["metrics"][0]["value"],
            "88.0",
        )
        self.assertEqual(
            decision_nodes["scada_comparison"]["metrics"][0]["value"],
            "temperature",
        )
        self.assertEqual(
            pipeline["channel_separation"][0]["status"],
            "active",
        )


if __name__ == "__main__":
    unittest.main()
