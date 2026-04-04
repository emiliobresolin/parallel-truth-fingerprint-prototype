"""Real runtime smoke validation for Epic 4 Story 4.5."""

from __future__ import annotations

from dataclasses import replace
from datetime import datetime, timedelta, timezone
import importlib.util
import json
import os
from pathlib import Path
import socket
import unittest
from unittest import mock

from parallel_truth_fingerprint.config.runtime import RuntimeDemoConfig
from parallel_truth_fingerprint.consensus import (
    build_consensus_alert,
    build_round_log,
    build_round_summary,
)
from parallel_truth_fingerprint.lstm_service import (
    configure_scada_replay_runtime_stage,
)
from parallel_truth_fingerprint.persistence import MinioArtifactStore, MinioStoreConfig
from parallel_truth_fingerprint.scada import FakeOpcUaScadaService
from parallel_truth_fingerprint.scenario_control import (
    apply_runtime_scenario_control,
    resolve_runtime_scenario_control_stage,
)
from scripts import run_local_demo
from tests.persistence.test_service import build_valid_audit_package


def _real_scenario_control_smoke_enabled() -> bool:
    return os.getenv("RUN_REAL_SCENARIO_CONTROL_SMOKE") == "1"


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
            if sensor_name == "temperature":
                loop_current_ma = round(10.0 + (value / 10.0), 3)
                pv_percent_range = round(35.0 + value, 3)
                noise_floor = round(0.15 + (value / 200.0), 6)
                rate_of_change = round(value / 25.0, 6)
                local_stability = round(max(0.55, 0.98 - (value / 120.0)), 6)
            elif sensor_name == "pressure":
                loop_current_ma = round(11.0 + (value * 1.5), 3)
                pv_percent_range = round(40.0 + (value * 8.0), 3)
                noise_floor = round(0.05 + (value / 20.0), 6)
                rate_of_change = round(value / 3.0, 6)
                local_stability = round(max(0.55, 0.99 - (value / 15.0)), 6)
            else:
                loop_current_ma = round(8.0 + (value / 400.0), 3)
                pv_percent_range = round(20.0 + (value / 50.0), 3)
                noise_floor = round(0.5 + (value / 6000.0), 6)
                rate_of_change = round(value / 120.0, 6)
                local_stability = round(max(0.55, 0.97 - (value / 10000.0)), 6)
            state.observations_by_sensor[sensor_name] = replace(
                payload,
                process_data=replace(
                    payload.process_data,
                    pv=replace(payload.process_data.pv, value=float(value)),
                    loop_current_ma=loop_current_ma,
                    pv_percent_range=pv_percent_range,
                    physics_metrics=replace(
                        payload.process_data.physics_metrics,
                        noise_floor=noise_floor,
                        rate_of_change_dtdt=rate_of_change,
                        local_stability_score=local_stability,
                    ),
                ),
            )

    return audit_package


@unittest.skipUnless(
    _real_scenario_control_smoke_enabled(),
    "Set RUN_REAL_SCENARIO_CONTROL_SMOKE=1 to run the Story 4.5 smoke test.",
)
@unittest.skipUnless(
    _dependencies_available(),
    "Required runtime dependencies for Story 4.5 are not installed.",
)
@unittest.skipUnless(
    _minio_available(),
    "Local MinIO is not reachable on 127.0.0.1:9000.",
)
class RuntimeScenarioControlSmokeTests(unittest.TestCase):
    def test_real_runtime_scenario_control_activates_replay_without_pipeline_bypass(
        self,
    ) -> None:
        run_suffix = datetime.now(timezone.utc).strftime("%Y%m%d%H%M%S%f")
        bucket_name = f"scenario-control-smoke-{run_suffix}"
        log_relative_path = f"logs/scenario-control-smoke-{run_suffix}.json"
        log_path = run_local_demo.PROJECT_ROOT / log_relative_path
        store = MinioArtifactStore(
            MinioStoreConfig(
                endpoint="localhost:9000",
                access_key="minioadmin",
                secret_key="minioadmin",
                bucket=bucket_name,
                secure=False,
            )
        )
        config = RuntimeDemoConfig(
            mqtt_transport="passive",
            minio_endpoint="localhost:9000",
            minio_access_key="minioadmin",
            minio_secret_key="minioadmin",
            minio_bucket=bucket_name,
            demo_cycle_interval_seconds=0.05,
            demo_max_cycles=4,
            demo_train_after_eligible_cycles=3,
            demo_fingerprint_sequence_length=2,
            demo_scenario_name="scada_replay",
            demo_scenario_start_cycle=4,
            demo_log_path=log_relative_path,
        )
        scada_service = FakeOpcUaScadaService(compressor_id="compressor-1")
        os.environ.pop("KERAS_BACKEND", None)
        cycle_values = (
            (10.0, 1.0, 1000.0),
            (20.0, 2.0, 2000.0),
            (30.0, 3.0, 3000.0),
            (40.0, 4.0, 4000.0),
        )

        def cycle_executor(*, cycle_index: int, **kwargs) -> dict[str, object]:
            round_id = f"round-scenario-control-{run_suffix}-{cycle_index:03d}"
            scenario_control_stage = resolve_runtime_scenario_control_stage(
                config=config,
                cycle_index=cycle_index,
            )
            cycle_config = apply_runtime_scenario_control(
                config=config,
                scenario_stage=scenario_control_stage,
            )
            temperature, pressure, rpm = cycle_values[cycle_index - 1]
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
                artifact_store=store,
                scada_service=scada_service,
                fault_mode=cycle_config.demo_fault_mode,
                scenario_control_stage=scenario_control_stage,
                scada_replay_stage=scada_replay_stage,
            )
            (
                fingerprint_stage,
                fingerprint_inference_results,
                replay_behavior_result,
                replay_inference_results,
            ) = run_local_demo.execute_fingerprint_pipeline_for_cycle(
                cycle_index=cycle_index,
                config=config,
                artifact_store=store,
                scada_state=scada_state,
                comparison_output=comparison_output,
                comparison_stage=comparison_stage,
                persistence_stage=persistence_stage,
                scada_replay_stage=scada_replay_stage,
                consensus_summary=build_round_summary(audit_package),
            )
            return {
                "cycle_index": cycle_index,
                "simulator_snapshot": {
                    "compressor_id": "compressor-1",
                    "operating_state_pct": float(cycle_config.demo_power),
                    "sensors": {
                        "temperature": float(temperature),
                        "pressure": float(pressure),
                        "rpm": float(rpm),
                    },
                },
                "node_status": {
                    "node_info": {"version": "scenario-control-smoke"},
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

        try:
            with mock.patch.object(
                run_local_demo,
                "execute_demo_cycle",
                side_effect=cycle_executor,
            ):
                with mock.patch.object(run_local_demo, "print_cycle_report"):
                    payload = run_local_demo.run_autonomous_demo_loop(
                        config=config,
                        simulator=object(),
                        edges=(),
                        cometbft_client=object(),
                        artifact_store=store,
                        scada_service=scada_service,
                        sleep_fn=lambda _: None,
                        monotonic_fn=mock.Mock(
                            side_effect=(0.0, 0.01, 1.0, 1.01, 2.0, 2.01, 3.0, 3.01)
                        ),
                    )

            self.assertEqual(payload["runtime"]["status"], "completed")
            self.assertEqual(payload["runtime"]["completed_cycles"], 4)
            self.assertEqual(
                payload["cycle_history"][0]["scenario_control"]["configured_scenario"],
                "scada_replay",
            )
            self.assertEqual(
                payload["cycle_history"][0]["scenario_control"]["active_scenario"],
                "normal",
            )
            self.assertTrue(
                payload["cycle_history"][0]["scenario_control"]["training_eligible"]
            )
            self.assertEqual(
                payload["cycle_history"][3]["scenario_control"]["active_scenario"],
                "scada_replay",
            )
            self.assertFalse(
                payload["cycle_history"][3]["scenario_control"]["training_eligible"]
            )
            self.assertEqual(
                payload["latest_cycle"]["scenario_control"]["expected_output_channels"],
                [
                    "consensus_alert",
                    "persistence_stage",
                    "replay_behavior",
                    "fingerprint_inference",
                ],
            )
            self.assertEqual(
                payload["latest_cycle"]["fingerprint_lifecycle"]["training_events"],
                ["reused"],
            )
            self.assertEqual(
                payload["latest_cycle"]["fingerprint_lifecycle"]["inference_status"],
                "completed",
            )
            self.assertEqual(
                payload["latest_cycle"]["replay_behavior"]["output_channel"],
                "scada_replay_behavior",
            )
            self.assertEqual(
                payload["latest_cycle"]["comparison_stage"]["status"],
                "completed",
            )

            valid_artifact_keys = store.list_json_objects(prefix="valid-consensus-artifacts/")
            dataset_manifest_keys = store.list_json_objects(prefix="fingerprint-datasets/")
            model_metadata_keys = store.list_json_objects(prefix="fingerprint-models/")
            self.assertEqual(len(valid_artifact_keys), 4)
            self.assertEqual(len(model_metadata_keys), 1)
            self.assertEqual(len(dataset_manifest_keys), 2)

            saved_log = json.loads(log_path.read_text(encoding="utf-8"))
            self.assertEqual(saved_log["runtime"]["status"], "completed")
            self.assertEqual(
                saved_log["latest_cycle"]["scenario_control"]["active_scenario"],
                "scada_replay",
            )
            self.assertEqual(
                saved_log["latest_cycle"]["scenario_control"]["training_eligible"],
                False,
            )
            self.assertEqual(
                saved_log["latest_cycle"]["replay_behavior"]["output_channel"],
                "scada_replay_behavior",
            )
            self.assertEqual(
                saved_log["latest_cycle"]["comparison_stage"]["status"],
                "completed",
            )
        finally:
            log_path.unlink(missing_ok=True)


if __name__ == "__main__":
    unittest.main()
