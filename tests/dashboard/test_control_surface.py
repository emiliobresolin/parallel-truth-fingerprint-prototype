"""Focused tests for the Story 4.6 local operator dashboard."""

from __future__ import annotations

import json
import unittest
from urllib import request

from parallel_truth_fingerprint.config.runtime import RuntimeDemoConfig
from parallel_truth_fingerprint.dashboard import (
    LocalOperatorDashboardController,
    LocalOperatorDashboardServer,
    build_dashboard_html,
)


def _json_request(
    *,
    method: str,
    url: str,
    payload: dict[str, object] | None = None,
) -> dict[str, object]:
    data = None if payload is None else json.dumps(payload).encode("utf-8")
    headers = {"Content-Type": "application/json"} if payload is not None else {}
    req = request.Request(url, data=data, headers=headers, method=method)
    with request.urlopen(req, timeout=5) as response:
        return json.loads(response.read().decode("utf-8"))


class FakeDashboardController:
    def __init__(self) -> None:
        self._state = {
            "runtime": {
                "ui_status": "stopped",
                "is_running": False,
                "last_runtime_status": "not_started",
                "status_note": "Runtime is stopped.",
                "current_cycle": 0,
                "cycle_interval_seconds": 60.0,
            },
            "controls": {
                "supported_scenarios": [
                    "normal",
                    "scada_replay",
                    "scada_freeze",
                    "scada_divergence",
                    "single_edge_exclusion",
                    "quorum_loss",
                ],
                "configured_scenario": "normal",
                "configured_power_pct": 65.0,
                "apply_mode": "next_start",
                "runtime_effect_note": "Runtime is stopped. Control changes update configured state only.",
            },
            "operator_feedback": {"actions": []},
            "monitoring": {
                "active_scenario": "normal",
                "compressor_state": {"operating_state_pct": 65.0},
                "sensor_values": {"temperature": 72.0, "pressure": 5.1, "rpm": 3100.0},
                "edge_status": [{"edge_id": "edge-1"}],
                "quorum_consensus": {"summary": {"final_consensus_status": "success"}},
                "valid_artifact_accumulation": {"count": 2},
                "lifecycle": {"model_status": "model_available"},
                "comparison_stage": {
                    "status": "blocked_downstream",
                    "reason": "scada_divergence_detected",
                    "operator_message": "SCADA divergence blocked the cycle.",
                },
                "persistence_stage": {
                    "status": "blocked",
                    "reason": "scada_divergence_detected",
                    "operator_message": "SCADA divergence blocked downstream persistence.",
                },
                "cycle_history": [{"cycle_index": 1}],
            },
            "channels": {
                "scada_divergence": {"structured": {"divergent_sensors": ["temperature"]}},
                "consensus": {"summary": {"final_consensus_status": "success"}, "alert": None},
                "fingerprint_inference": [{"output_channel": "lstm_fingerprint"}],
                "replay_behavior": {"output_channel": "scada_replay_behavior"},
            },
            "events": {
                "components": [
                    {"id": "compressor", "label": "Compressor"},
                    {"id": "temperature_sensor", "label": "Temperature Sensor"},
                ],
                "global_timeline": [
                    {
                        "event_id": "compressor:latest_cycle:1",
                        "component": "compressor",
                        "component_label": "Compressor",
                        "recorded_at": "2026-04-02T00:00:00+00:00",
                        "runtime_reference": "cycle 1",
                        "message": "Compressor operating at 65.0% with live sensor values.",
                    }
                ],
                "component_timelines": {
                    "compressor": [
                        {
                            "event_id": "compressor:latest_cycle:1",
                            "component": "compressor",
                            "component_label": "Compressor",
                            "recorded_at": "2026-04-02T00:00:00+00:00",
                            "runtime_reference": "cycle 1",
                            "message": "Compressor operating at 65.0% with live sensor values.",
                        }
                    ],
                    "temperature_sensor": [
                        {
                            "event_id": "temperature_sensor:latest_cycle:1",
                            "component": "temperature_sensor",
                            "component_label": "Temperature Sensor",
                            "recorded_at": "2026-04-02T00:00:00+00:00",
                            "runtime_reference": "cycle 1",
                            "message": "Temperature Sensor reported 72.0 degC on cycle 1.",
                        }
                    ],
                },
                "component_raw_logs": {
                    "compressor": {"simulator_snapshot": {"operating_state_pct": 65.0}},
                    "temperature_sensor": {"simulator_value": 72.0},
                },
                "raw_log_ground_truth_note": "Raw logs stay available.",
            },
            "pipeline": {
                "flow_summary": "Power -> sensors -> edges -> consensus -> SCADA comparison -> fingerprint",
                "rows": [
                    {
                        "id": "physical_origin",
                        "label": "Physical origin and sensors",
                        "summary": "The compressor and its sensors are the physical origin of the process values.",
                        "nodes": [
                            {
                                "component_id": "compressor",
                                "log_component_id": "compressor",
                                "title": "Compressor",
                                "kind": "process",
                                "status": "Compressor operating at 65.0% with live sensor values.",
                                "metrics": [
                                    {"label": "Power", "value": "65.0%"},
                                ],
                            }
                        ],
                    }
                ],
                "channel_separation": [
                    {
                        "label": "SCADA divergence",
                        "status": "blocked",
                        "tone": "blocked",
                        "explanation": "Direct mismatch is visible here.",
                    }
                ],
            },
            "explainability": {
                "translated_statuses": {
                    "model_status": {
                        "raw_value": "model_available",
                        "label": "Fingerprint model is available",
                        "explanation": "A fingerprint model has already been trained.",
                    },
                    "validation_level": {
                        "raw_value": "runtime_valid_only",
                        "label": "Runtime-valid only",
                        "explanation": "Training pipeline works but adequacy remains below target.",
                    },
                },
                "fingerprint_readiness": {
                    "summary": "A saved fingerprint model exists, but the source dataset is still below the stronger adequacy floor.",
                    "readiness_state": {
                        "raw_value": "runtime_valid_only",
                        "label": "Fingerprint pipeline works, but readiness is still below target",
                    },
                    "adequacy_gate": {
                        "validation_level": "runtime_valid_only",
                        "summary": "Source dataset evidence: 4/30 eligible artifacts and 2/20 temporal windows.",
                    },
                    "provenance": {
                        "model_identity": "fingerprint-models/model-001.json",
                        "model_id": "model-001",
                        "source_dataset_id": "training-dataset::round-1::round-3::seq-2",
                        "training_window_count": "2",
                        "threshold_origin": "source_dataset_mean_plus_3std",
                    },
                    "training_details": {
                        "first_training_reference": "cycle 1",
                        "current_model_usage": "reused_existing_model",
                        "trained_at": "2026-04-02T00:00:00+00:00",
                        "epochs": "1",
                        "batch_size": "1",
                        "loss_name": "mse",
                        "final_training_loss": "0.01",
                        "sequence_length": "2",
                        "feature_schema": "temperature.pv, pressure.pv, rpm.pv",
                    },
                    "working_now": [
                        "A saved fingerprint model is available for reuse in the current run."
                    ],
                    "evidence_available": [
                        "Threshold origin: source_dataset_mean_plus_3std."
                    ],
                    "not_proven_yet": [
                        "The fingerprint base is still runtime-valid only."
                    ],
                    "evidence_matrix": [
                        {
                            "label": "Normal operation",
                            "status": "Observed",
                            "summary": "The generic fingerprint path is evaluating normal-history windows from the current run.",
                            "evidence": ["classification=normal"],
                        }
                    ],
                },
                "what_changed_since_startup": {
                    "runtime_start_time": "2026-04-02T00:00:00+00:00",
                    "elapsed_runtime": "00:05:00",
                    "current_cycle_count": 1,
                    "valid_artifact_count_growth": {
                        "summary": "Valid persisted artifacts grew from 0 to 2 in this run."
                    },
                    "training": {
                        "has_training_happened": True,
                        "first_training_reference": "cycle 1",
                        "current_model_usage": "reused_existing_model",
                        "current_model_identity": "fingerprint-models/model-001.json",
                    },
                    "questions_answered": {
                        "has_fingerprint_been_created": "Yes.",
                        "what_changed_since_startup": "Cycle advanced and artifacts grew.",
                        "what_evidence_exists_in_this_run": "Artifacts and model metadata exist.",
                        "what_is_expected_next": "Reuse the saved model.",
                    },
                    "happened_already": ["Runtime started.", "Fingerprint created."],
                    "not_happened_yet": ["No replay is active right now."],
                    "expected_next": {"summary": "Reuse the saved model."},
                    "limitation": "Runtime-valid only.",
                },
            },
            "guidance": {
                "panels": [
                    {
                        "title": "What Is Happening",
                        "summary": "The runtime is running in normal mode.",
                        "bullets": ["Active scenario: normal."],
                    },
                    {
                        "title": "What Should Happen",
                        "summary": "Normal operation should keep artifacts growing.",
                        "bullets": ["Replay should stay separate from consensus failure."],
                    },
                ],
                "raw_evidence_note": "Use component logs and raw logs as ground truth.",
            },
            "limitations": {
                "source_dataset_validation_level": "runtime_valid_only",
                "note": "Runtime-valid only.",
            },
        }

    def build_dashboard_state(self) -> dict[str, object]:
        return json.loads(json.dumps(self._state))

    def start_runtime(self) -> dict[str, object]:
        self._state["runtime"]["ui_status"] = "running"
        self._state["runtime"]["is_running"] = True
        self._state["controls"]["apply_mode"] = "next_cycle"
        self._state["controls"]["runtime_effect_note"] = "Changes apply on the next live cycle."
        self._state["operator_feedback"]["actions"].insert(
            0,
            {
                "action": "start_runtime",
                "applied_at": "2026-04-02T00:00:00+00:00",
                "applies_on_cycle": 1,
                "runtime_command": "start_runtime()",
                "configuration_change": {"runtime_state": "running"},
                "expected_output_channels": ["runtime_state"],
                "effect_scope": "runtime_command_started",
                "note": "Runtime started.",
            },
        )
        return self.build_dashboard_state()

    def stop_runtime(self) -> dict[str, object]:
        self._state["runtime"]["ui_status"] = "stopped"
        self._state["runtime"]["is_running"] = False
        self._state["controls"]["apply_mode"] = "next_start"
        self._state["controls"]["runtime_effect_note"] = "Runtime is stopped. Control changes update configured state only."
        self._state["operator_feedback"]["actions"].insert(
            0,
            {
                "action": "stop_runtime",
                "applied_at": "2026-04-02T00:01:00+00:00",
                "applies_on_cycle": 2,
                "runtime_command": "stop_runtime()",
                "configuration_change": {"runtime_state": "stopped"},
                "expected_output_channels": ["runtime_state"],
                "effect_scope": "runtime_command_requested_stop",
                "note": "Runtime stopped.",
            },
        )
        return self.build_dashboard_state()

    def set_scenario(self, scenario_name: str) -> dict[str, object]:
        self._state["controls"]["configured_scenario"] = scenario_name
        self._state["monitoring"]["active_scenario"] = scenario_name
        self._state["operator_feedback"]["actions"].insert(
            0,
            {
                "action": "set_scenario",
                "applied_at": "2026-04-02T00:02:00+00:00",
                "applies_on_cycle": 3,
                "runtime_command": f"set_scenario('{scenario_name}')",
                "configuration_change": {
                    "demo_scenario_name": scenario_name,
                    "demo_scenario_start_cycle": 3,
                },
                "expected_output_channels": [
                    "consensus_alert",
                    "persistence_stage",
                    "replay_behavior",
                    "fingerprint_inference",
                ],
                "effect_scope": "applies_next_cycle",
                "note": "Scenario updated.",
            },
        )
        return self.build_dashboard_state()

    def set_power(self, power: float) -> dict[str, object]:
        self._state["controls"]["configured_power_pct"] = power
        self._state["monitoring"]["compressor_state"]["operating_state_pct"] = power
        self._state["operator_feedback"]["actions"].insert(
            0,
            {
                "action": "set_power",
                "applied_at": "2026-04-02T00:03:00+00:00",
                "applies_on_cycle": 4,
                "runtime_command": f"set_power({power})",
                "configuration_change": {"demo_power": power},
                "expected_output_channels": ["sensor_values", "fingerprint_inference"],
                "effect_scope": "applies_next_cycle",
                "note": "Power updated.",
            },
        )
        return self.build_dashboard_state()


class DashboardControlSurfaceTests(unittest.TestCase):
    def setUp(self) -> None:
        self.controller = FakeDashboardController()
        self.server = LocalOperatorDashboardServer(self.controller, host="127.0.0.1", port=0)
        self.server.start_in_background()

    def tearDown(self) -> None:
        self.server.stop()

    def test_dashboard_html_includes_runtime_control_and_monitoring_sections(self) -> None:
        html = build_dashboard_html(self.controller.build_dashboard_state())

        self.assertIn("Start Runtime", html)
        self.assertIn("Scenario Control", html)
        self.assertIn("Compressor Control", html)
        self.assertIn("Fingerprint Inference", html)
        self.assertIn("Operational Event Timeline", html)
        self.assertIn("Component Evidence", html)
        self.assertIn("Current Evidence Summary", html)
        self.assertIn("Fingerprint Readiness", html)
        self.assertIn("Prototype Pipeline", html)
        self.assertIn("Distinct output channels", html)
        self.assertIn("Transparent Operator Feedback", html)
        self.assertIn("Physical origin and sensors", html)
        self.assertIn("Demo Guidance", html)
        self.assertIn("guidance-panels", html)
        self.assertIn("component-log-details", html)
        self.assertIn("Raw Channel Details", html)
        self.assertNotIn("Story 4.", html)
        self.assertNotIn("Story 5.", html)
        self.assertNotIn("Story 6.", html)

    def test_runtime_start_and_stop_flow_works_through_http_control_path(self) -> None:
        state = _json_request(method="GET", url=f"{self.server.base_url}/api/state")
        self.assertEqual(state["runtime"]["ui_status"], "stopped")

        started = _json_request(
            method="POST",
            url=f"{self.server.base_url}/api/runtime/start",
            payload={},
        )
        self.assertEqual(started["runtime"]["ui_status"], "running")

        stopped = _json_request(
            method="POST",
            url=f"{self.server.base_url}/api/runtime/stop",
            payload={},
        )
        self.assertEqual(stopped["runtime"]["ui_status"], "stopped")

    def test_scenario_and_power_controls_record_transparent_feedback(self) -> None:
        scenario_state = _json_request(
            method="POST",
            url=f"{self.server.base_url}/api/control/scenario",
            payload={"scenario": "scada_replay"},
        )
        power_state = _json_request(
            method="POST",
            url=f"{self.server.base_url}/api/control/power",
            payload={"power": 80.0},
        )

        self.assertEqual(
            scenario_state["controls"]["configured_scenario"],
            "scada_replay",
        )
        self.assertEqual(
            power_state["controls"]["configured_power_pct"],
            80.0,
        )
        latest_action = power_state["operator_feedback"]["actions"][0]
        self.assertEqual(latest_action["action"], "set_power")
        self.assertIn("demo_power", latest_action["configuration_change"])
        self.assertIn("sensor_values", latest_action["expected_output_channels"])
        self.assertEqual(latest_action["effect_scope"], "applies_next_cycle")

    def test_state_endpoint_preserves_channel_separation(self) -> None:
        state = _json_request(method="GET", url=f"{self.server.base_url}/api/state")

        self.assertIn("scada_divergence", state["channels"])
        self.assertIn("consensus", state["channels"])
        self.assertIn("fingerprint_inference", state["channels"])
        self.assertIn("replay_behavior", state["channels"])
        self.assertIn("events", state)
        self.assertIn("global_timeline", state["events"])
        self.assertIn("component_raw_logs", state["events"])
        self.assertIn("pipeline", state)
        self.assertIn("flow_summary", state["pipeline"])
        self.assertIn("explainability", state)
        self.assertIn("translated_statuses", state["explainability"])
        self.assertIn("fingerprint_readiness", state["explainability"])
        self.assertIn("what_changed_since_startup", state["explainability"])
        self.assertIn("guidance", state)
        self.assertTrue(state["guidance"]["panels"])
        self.assertEqual(
            state["channels"]["replay_behavior"]["output_channel"],
            "scada_replay_behavior",
        )


class DashboardControllerHonestyTests(unittest.TestCase):
    def test_stopped_runtime_controls_are_marked_as_configuration_only(self) -> None:
        controller = LocalOperatorDashboardController(
            RuntimeDemoConfig(mqtt_transport="passive")
        )

        state = controller.set_power(80.0)

        self.assertEqual(state["controls"]["apply_mode"], "next_start")
        self.assertIn(
            "update configured state only",
            state["controls"]["runtime_effect_note"],
        )
        self.assertEqual(
            state["operator_feedback"]["actions"][0]["effect_scope"],
            "configuration_only_until_next_start",
        )

    def test_running_runtime_controls_are_marked_for_next_cycle(self) -> None:
        controller = LocalOperatorDashboardController(
            RuntimeDemoConfig(mqtt_transport="passive")
        )
        with controller._lock:
            controller._runtime_status = "running"
            controller._latest_runtime_payload = {
                "runtime": {"current_cycle": 2},
            }

        state = controller.set_scenario("scada_replay")

        self.assertEqual(state["controls"]["apply_mode"], "next_cycle")
        self.assertIn(
            "next eligible live cycle",
            state["controls"]["runtime_effect_note"],
        )
        self.assertEqual(
            state["operator_feedback"]["actions"][0]["effect_scope"],
            "applies_next_cycle",
        )


if __name__ == "__main__":
    unittest.main()
