"""Focused tests for the Story 4.6 local operator dashboard."""

from __future__ import annotations

import json
import unittest
from urllib import request

from parallel_truth_fingerprint.dashboard import (
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
                "cycle_history": [{"cycle_index": 1}],
            },
            "channels": {
                "scada_divergence": {"structured": {"divergent_sensors": ["temperature"]}},
                "consensus": {"summary": {"final_consensus_status": "success"}, "alert": None},
                "fingerprint_inference": [{"output_channel": "lstm_fingerprint"}],
                "replay_behavior": {"output_channel": "scada_replay_behavior"},
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
        self._state["operator_feedback"]["actions"].insert(
            0,
            {
                "action": "start_runtime",
                "applied_at": "2026-04-02T00:00:00+00:00",
                "applies_on_cycle": 1,
                "runtime_command": "start_runtime()",
                "configuration_change": {"runtime_state": "running"},
                "expected_output_channels": ["runtime_state"],
                "note": "Runtime started.",
            },
        )
        return self.build_dashboard_state()

    def stop_runtime(self) -> dict[str, object]:
        self._state["runtime"]["ui_status"] = "stopped"
        self._state["runtime"]["is_running"] = False
        self._state["operator_feedback"]["actions"].insert(
            0,
            {
                "action": "stop_runtime",
                "applied_at": "2026-04-02T00:01:00+00:00",
                "applies_on_cycle": 2,
                "runtime_command": "stop_runtime()",
                "configuration_change": {"runtime_state": "stopped"},
                "expected_output_channels": ["runtime_state"],
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
                "expected_output_channels": ["scada_divergence_alert", "replay_behavior"],
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
        self.assertIn("Transparent Operator Feedback", html)
        self.assertIn("Fingerprint Inference", html)

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

    def test_state_endpoint_preserves_channel_separation(self) -> None:
        state = _json_request(method="GET", url=f"{self.server.base_url}/api/state")

        self.assertIn("scada_divergence", state["channels"])
        self.assertIn("consensus", state["channels"])
        self.assertIn("fingerprint_inference", state["channels"])
        self.assertIn("replay_behavior", state["channels"])
        self.assertEqual(
            state["channels"]["replay_behavior"]["output_channel"],
            "scada_replay_behavior",
        )


if __name__ == "__main__":
    unittest.main()
