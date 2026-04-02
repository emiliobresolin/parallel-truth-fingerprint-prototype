"""Real runtime smoke validation for Story 4.6."""

from __future__ import annotations

from dataclasses import replace
from datetime import datetime, timezone
import importlib.util
import json
import os
from pathlib import Path
import socket
import time
import unittest
from unittest import mock
from urllib import request

from parallel_truth_fingerprint.config.runtime import RuntimeDemoConfig
from parallel_truth_fingerprint.consensus import (
    build_consensus_alert,
    build_round_log,
    build_round_summary,
)
from parallel_truth_fingerprint.dashboard import (
    LocalOperatorDashboardController,
    LocalOperatorDashboardServer,
)
from parallel_truth_fingerprint.lstm_service import (
    configure_scada_replay_runtime_stage,
    execute_deferred_fingerprint_lifecycle,
    run_scada_replay_behavior_detection,
)
from parallel_truth_fingerprint.persistence import MinioArtifactStore, MinioStoreConfig
from parallel_truth_fingerprint.scada import FakeOpcUaScadaService
from parallel_truth_fingerprint.scenario_control import (
    apply_runtime_scenario_control,
    resolve_runtime_scenario_control_stage,
)
from scripts import run_local_demo
from tests.persistence.test_service import build_valid_audit_package


def _real_dashboard_smoke_enabled() -> bool:
    return os.getenv("RUN_REAL_DASHBOARD_SMOKE") == "1"


def _dependencies_available() -> bool:
    return (
        importlib.util.find_spec("keras") is not None
        and importlib.util.find_spec("torch") is not None
        and importlib.util.find_spec("minio") is not None
        and importlib.util.find_spec("numpy") is not None
    )


def _minio_available(host: str = "127.0.0.1", port: int = 9000) -> bool:
    try:
        with socket.create_connection((host, port), timeout=2):
            return True
    except OSError:
        return False


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


def _wait_for(predicate, *, timeout_seconds: float = 10.0) -> dict[str, object]:
    deadline = time.time() + timeout_seconds
    while time.time() < deadline:
        state = predicate()
        if state is not None:
            return state
        time.sleep(0.05)
    raise AssertionError("Timed out waiting for dashboard runtime condition.")


class _FakeReceipt:
    def __init__(self, cycle_index: int, round_id: str) -> None:
        self.height = cycle_index
        self.tx_hash = f"TX-{cycle_index:03d}"
        self.check_tx_code = 0
        self.deliver_tx_code = 0
        self.round_id = round_id


def build_variable_audit_package(
    *,
    round_id: str,
    temperature: float,
    pressure: float,
    rpm: float,
):
    audit_package = build_valid_audit_package(round_id=round_id)
    updated_values = {
        "temperature": float(temperature),
        "pressure": float(pressure),
        "rpm": float(rpm),
    }
    audit_package.consensused_valid_state.sensor_values.update(updated_values)
    audit_package.consensus_result.consensused_valid_state.sensor_values.update(
        updated_values
    )

    for state in audit_package.round_input.replicated_states:
        for sensor_name, value in updated_values.items():
            payload = state.observations_by_sensor[sensor_name]
            state.observations_by_sensor[sensor_name] = replace(
                payload,
                process_data=replace(
                    payload.process_data,
                    pv=replace(payload.process_data.pv, value=float(value)),
                ),
            )

    return audit_package


@unittest.skipUnless(
    _real_dashboard_smoke_enabled(),
    "Set RUN_REAL_DASHBOARD_SMOKE=1 to run the Story 4.6 smoke test.",
)
@unittest.skipUnless(
    _dependencies_available(),
    "Required runtime dependencies for Story 4.6 are not installed.",
)
@unittest.skipUnless(
    _minio_available(),
    "Local MinIO is not reachable on 127.0.0.1:9000.",
)
class DashboardControlSurfaceRuntimeSmokeTests(unittest.TestCase):
    def test_dashboard_controls_real_runtime_lifecycle_end_to_end(self) -> None:
        run_suffix = datetime.now(timezone.utc).strftime("%Y%m%d%H%M%S%f")
        bucket_name = f"dashboard-smoke-{run_suffix}"
        log_relative_path = f"logs/dashboard-smoke-{run_suffix}.json"
        log_path = run_local_demo.PROJECT_ROOT / log_relative_path
        config = RuntimeDemoConfig(
            mqtt_transport="passive",
            minio_endpoint="localhost:9000",
            minio_access_key="minioadmin",
            minio_secret_key="minioadmin",
            minio_bucket=bucket_name,
            demo_cycle_interval_seconds=0.05,
            demo_max_cycles=0,
            demo_train_after_eligible_cycles=3,
            demo_fingerprint_sequence_length=2,
            demo_dashboard_host="127.0.0.1",
            demo_dashboard_port=0,
            demo_log_path=log_relative_path,
        )
        controller = LocalOperatorDashboardController(config)
        server = LocalOperatorDashboardServer(controller, host="127.0.0.1", port=0)
        store = MinioArtifactStore(
            MinioStoreConfig(
                endpoint="localhost:9000",
                access_key="minioadmin",
                secret_key="minioadmin",
                bucket=bucket_name,
                secure=False,
            )
        )

        def cycle_executor(*, cycle_index: int, config, artifact_store, scada_service, **kwargs):
            scenario_control_stage = resolve_runtime_scenario_control_stage(
                config=config,
                cycle_index=cycle_index,
            )
            cycle_config = apply_runtime_scenario_control(
                config=config,
                scenario_stage=scenario_control_stage,
            )
            power = float(cycle_config.demo_power)
            temperature = round(38.0 + (power * 0.52) + cycle_index, 3)
            pressure = round(1.4 + (power * 0.055) + (cycle_index * 0.05), 3)
            rpm = round(850.0 + (power * 28.0) + (cycle_index * 12.0), 3)
            round_id = f"round-dashboard-{run_suffix}-{cycle_index:03d}"
            audit_package = build_variable_audit_package(
                round_id=round_id,
                temperature=temperature,
                pressure=pressure,
                rpm=rpm,
            )
            scada_replay_stage = configure_scada_replay_runtime_stage(
                scada_service=scada_service,
                config=cycle_config,
                cycle_index=cycle_index,
            )
            (
                scada_state,
                comparison_stage,
                comparison_output,
                scada_alert,
                persistence_stage,
            ) = run_local_demo.run_scada_comparison_and_persistence(
                consensus_audit=audit_package,
                artifact_store=artifact_store,
                scada_service=scada_service,
                fault_mode=cycle_config.demo_fault_mode,
                scenario_control_stage=scenario_control_stage,
                scada_replay_stage=scada_replay_stage,
            )
            fingerprint_stage, fingerprint_inference_results = (
                execute_deferred_fingerprint_lifecycle(
                    cycle_index=cycle_index,
                    artifact_store=artifact_store,
                    sequence_length=config.demo_fingerprint_sequence_length,
                    train_after_eligible_cycles=config.demo_train_after_eligible_cycles,
                )
            )
            replay_behavior_result, replay_inference_results = (
                run_scada_replay_behavior_detection(
                    current_round_id=round_id,
                    consensus_final_status="success",
                    scada_state=scada_state,
                    comparison_output=comparison_output,
                    replay_stage=scada_replay_stage,
                    artifact_store=artifact_store,
                    sequence_length=config.demo_fingerprint_sequence_length,
                )
                if scada_state is not None and comparison_output is not None
                else (None, ())
            )
            return {
                "cycle_index": cycle_index,
                "simulator_snapshot": {
                    "compressor_id": "compressor-1",
                    "operating_state_pct": power,
                    "sensors": {
                        "temperature": temperature,
                        "pressure": pressure,
                        "rpm": rpm,
                    },
                },
                "node_status": {
                    "node_info": {"version": "dashboard-smoke"},
                    "sync_info": {"latest_block_height": str(cycle_index)},
                },
                "commit_receipt": _FakeReceipt(cycle_index, round_id),
                "committed_round": {"round_id": round_id, "commit_height": cycle_index},
                "consensus_summary": build_round_summary(audit_package),
                "consensus_log": build_round_log(audit_package),
                "consensus_alert": build_consensus_alert(
                    audit_package,
                    build_round_log(audit_package),
                ),
                "scada_state": scada_state,
                "comparison_stage": comparison_stage,
                "comparison_output": comparison_output,
                "scada_alert": scada_alert,
                "persistence_stage": persistence_stage,
                "fault_edges": (),
                "scenario_control_stage": scenario_control_stage,
                "scada_replay_stage": scada_replay_stage,
                "fingerprint_stage": fingerprint_stage,
                "fingerprint_inference_results": fingerprint_inference_results,
                "replay_behavior_result": replay_behavior_result,
                "replay_inference_results": replay_inference_results,
                "edges": (),
            }

        def read_state() -> dict[str, object]:
            return _json_request(method="GET", url=f"{server.base_url}/api/state")

        def wait_for_high_power_state() -> dict[str, object] | None:
            state = read_state()
            if state["runtime"]["current_cycle"] < 2:
                return None
            operating_state_pct = float(
                state["monitoring"]
                .get("compressor_state", {})
                .get("operating_state_pct", 0.0)
            )
            return state if operating_state_pct >= 80.0 else None

        def wait_for_low_power_state() -> dict[str, object] | None:
            state = read_state()
            if state["runtime"]["current_cycle"] < 3:
                return None
            operating_state_pct = float(
                state["monitoring"]
                .get("compressor_state", {})
                .get("operating_state_pct", 100.0)
            )
            return state if operating_state_pct <= 20.0 else None

        def wait_for_replay_state() -> dict[str, object] | None:
            state = read_state()
            if state["runtime"]["current_cycle"] < 4:
                return None
            if state["monitoring"]["active_scenario"] != "scada_replay":
                return None
            return state if state["channels"]["replay_behavior"] is not None else None

        def wait_for_stopped_state() -> dict[str, object] | None:
            state = read_state()
            return state if state["runtime"]["ui_status"] == "stopped" else None

        try:
            server.start_in_background()
            with mock.patch.object(
                run_local_demo,
                "execute_demo_cycle",
                side_effect=cycle_executor,
            ):
                with mock.patch.object(run_local_demo, "print_cycle_report"):
                    power_state = _json_request(
                        method="POST",
                        url=f"{server.base_url}/api/control/power",
                        payload={"power": 80.0},
                    )
                    self.assertEqual(
                        power_state["controls"]["configured_power_pct"],
                        80.0,
                    )

                    started = _json_request(
                        method="POST",
                        url=f"{server.base_url}/api/runtime/start",
                        payload={},
                    )
                    self.assertIn(started["runtime"]["ui_status"], {"starting", "running"})

                    high_power_state = _wait_for(wait_for_high_power_state)
                    self.assertEqual(
                        high_power_state["controls"]["configured_power_pct"],
                        80.0,
                    )

                    reduced_power = _json_request(
                        method="POST",
                        url=f"{server.base_url}/api/control/power",
                        payload={"power": 20.0},
                    )
                    self.assertEqual(
                        reduced_power["operator_feedback"]["actions"][0]["action"],
                        "set_power",
                    )

                    low_power_state = _wait_for(wait_for_low_power_state)
                    self.assertEqual(
                        low_power_state["controls"]["configured_power_pct"],
                        20.0,
                    )

                    scenario_state = _json_request(
                        method="POST",
                        url=f"{server.base_url}/api/control/scenario",
                        payload={"scenario": "scada_replay"},
                    )
                    self.assertEqual(
                        scenario_state["controls"]["configured_scenario"],
                        "scada_replay",
                    )

                    replay_state = _wait_for(wait_for_replay_state)
                    self.assertEqual(
                        replay_state["channels"]["replay_behavior"]["output_channel"],
                        "scada_replay_behavior",
                    )
                    self.assertEqual(
                        replay_state["monitoring"]["lifecycle"]["training_events"],
                        ["reused"],
                    )

                    stopped = _json_request(
                        method="POST",
                        url=f"{server.base_url}/api/runtime/stop",
                        payload={},
                    )
                    self.assertIn(stopped["runtime"]["ui_status"], {"stopping", "stopped"})
                    final_state = _wait_for(wait_for_stopped_state)

            self.assertEqual(final_state["runtime"]["ui_status"], "stopped")
            self.assertEqual(
                final_state["limitations"]["source_dataset_validation_level"],
                "runtime_valid_only",
            )

            valid_artifact_keys = store.list_json_objects(prefix="valid-consensus-artifacts/")
            dataset_manifest_keys = store.list_json_objects(prefix="fingerprint-datasets/")
            model_metadata_keys = store.list_json_objects(prefix="fingerprint-models/")
            self.assertGreaterEqual(len(valid_artifact_keys), 4)
            self.assertGreaterEqual(len(dataset_manifest_keys), 2)
            self.assertEqual(len(model_metadata_keys), 1)

            saved_log = json.loads(log_path.read_text(encoding="utf-8"))
            self.assertEqual(saved_log["runtime"]["status"], "stopped_operator")
            self.assertEqual(
                saved_log["latest_cycle"]["scenario_control"]["active_scenario"],
                "scada_replay",
            )
            self.assertEqual(
                saved_log["latest_cycle"]["fingerprint_lifecycle"]["training_events"],
                ["reused"],
            )
            self.assertEqual(
                saved_log["latest_cycle"]["simulator_snapshot"]["operating_state_pct"],
                20.0,
            )
        finally:
            server.stop()
            log_path.unlink(missing_ok=True)


if __name__ == "__main__":
    unittest.main()
