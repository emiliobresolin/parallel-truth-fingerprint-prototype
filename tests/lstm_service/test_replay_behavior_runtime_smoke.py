"""Real runtime smoke validation for Epic 4 Story 4.4."""

from __future__ import annotations

from dataclasses import replace
from datetime import datetime, timedelta, timezone
import importlib.util
import os
import socket
import unittest

from parallel_truth_fingerprint.config.runtime import RuntimeDemoConfig
from parallel_truth_fingerprint.lstm_service import (
    configure_scada_replay_runtime_stage,
)
from parallel_truth_fingerprint.persistence import MinioArtifactStore, MinioStoreConfig
from parallel_truth_fingerprint.scada import FakeOpcUaScadaService
from scripts import run_local_demo
from tests.persistence.test_service import build_valid_audit_package


def _real_replay_behavior_smoke_enabled() -> bool:
    return os.getenv("RUN_REAL_REPLAY_BEHAVIOR_SMOKE") == "1"


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


def build_variable_audit_package(
    *,
    round_id: str,
    temperature: float,
    pressure: float,
    rpm: float,
):
    """Create one valid audit package with deterministic supervisory and behavioral drift."""

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
    _real_replay_behavior_smoke_enabled(),
    "Set RUN_REAL_REPLAY_BEHAVIOR_SMOKE=1 to run the Story 4.4 smoke test.",
)
@unittest.skipUnless(
    _dependencies_available(),
    "Required runtime dependencies for Story 4.4 are not installed.",
)
@unittest.skipUnless(
    _minio_available(),
    "Local MinIO is not reachable on 127.0.0.1:9000.",
)
class RuntimeReplayBehaviorSmokeTests(unittest.TestCase):
    def test_real_runtime_replay_behavior_surfaces_through_fingerprint_path_without_mandatory_scada_divergence(
        self,
    ) -> None:
        run_suffix = datetime.now(timezone.utc).strftime("%Y%m%d%H%M%S%f")
        bucket_name = f"replay-behavior-smoke-{run_suffix}"
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
            demo_train_after_eligible_cycles=3,
            demo_fingerprint_sequence_length=2,
            demo_scada_mode="replay",
            demo_scada_start_cycle=4,
        )
        scada_service = FakeOpcUaScadaService(compressor_id="compressor-1")
        os.environ.pop("KERAS_BACKEND", None)

        normal_cycles = (
            ("round-replay-smoke-%s-001" % run_suffix, 10.0, 1.0, 1000.0),
            ("round-replay-smoke-%s-002" % run_suffix, 20.0, 2.0, 2000.0),
            ("round-replay-smoke-%s-003" % run_suffix, 30.0, 3.0, 3000.0),
        )

        for cycle_index, (round_id, temperature, pressure, rpm) in enumerate(
            normal_cycles,
            start=1,
        ):
            replay_stage = configure_scada_replay_runtime_stage(
                scada_service=scada_service,
                config=config,
                cycle_index=cycle_index,
            )
            audit_package = build_variable_audit_package(
                round_id=round_id,
                temperature=temperature,
                pressure=pressure,
                rpm=rpm,
            )
            (
                scada_state,
                comparison_stage,
                comparison_output,
                _scada_alert,
                persistence_stage,
            ) = run_local_demo.run_scada_comparison_and_persistence(
                consensus_audit=audit_package,
                artifact_store=store,
                scada_service=scada_service,
                fault_mode="none",
                scada_replay_stage=replay_stage,
            )
            run_local_demo.execute_fingerprint_pipeline_for_cycle(
                cycle_index=cycle_index,
                config=config,
                artifact_store=store,
                scada_state=scada_state,
                comparison_output=comparison_output,
                comparison_stage=comparison_stage,
                persistence_stage=persistence_stage,
                scada_replay_stage=replay_stage,
                consensus_summary=run_local_demo.build_round_summary(audit_package),
            )

        replay_stage = configure_scada_replay_runtime_stage(
            scada_service=scada_service,
            config=config,
            cycle_index=4,
        )
        replay_audit_package = build_variable_audit_package(
            round_id=f"round-replay-smoke-{run_suffix}-004",
            temperature=40.0,
            pressure=4.0,
            rpm=4000.0,
        )
        (
            replay_scada_state,
            comparison_stage,
            comparison_output,
            _scada_alert,
            persistence_stage,
        ) = run_local_demo.run_scada_comparison_and_persistence(
            consensus_audit=replay_audit_package,
            artifact_store=store,
            scada_service=scada_service,
            fault_mode="none",
            scada_replay_stage=replay_stage,
        )
        (
            lifecycle_stage,
            generic_inference_results,
            replay_result,
            replay_inference_results,
        ) = run_local_demo.execute_fingerprint_pipeline_for_cycle(
            cycle_index=4,
            config=config,
            artifact_store=store,
            scada_state=replay_scada_state,
            comparison_output=comparison_output,
            comparison_stage=comparison_stage,
            persistence_stage=persistence_stage,
            scada_replay_stage=replay_stage,
            consensus_summary=run_local_demo.build_round_summary(replay_audit_package),
        )

        self.assertEqual(comparison_stage["status"], "completed")
        self.assertTrue(comparison_stage["downstream_permitted"])
        self.assertEqual(persistence_stage["status"], "persisted")
        self.assertEqual(lifecycle_stage.training_events, ("reused",))
        self.assertEqual(lifecycle_stage.inference_status, "completed")
        self.assertEqual(lifecycle_stage.model_status, "model_available")
        self.assertTrue(generic_inference_results)
        self.assertIsNotNone(replay_result)
        self.assertTrue(replay_inference_results)
        self.assertEqual(replay_result.output_channel, "scada_replay_behavior")
        self.assertEqual(replay_result.scenario_mode, "replay")
        self.assertEqual(replay_result.scada_divergent_sensors, ())

        valid_artifact_keys = store.list_json_objects(prefix="valid-consensus-artifacts/")
        dataset_manifest_keys = store.list_json_objects(prefix="fingerprint-datasets/")
        model_metadata_keys = store.list_json_objects(prefix="fingerprint-models/")
        self.assertEqual(len(valid_artifact_keys), 4)
        self.assertEqual(len(model_metadata_keys), 1)
        self.assertEqual(len(dataset_manifest_keys), 2)
        self.assertTrue(
            any("training-dataset::" in object_key for object_key in dataset_manifest_keys)
        )
        self.assertTrue(
            any("replay-dataset::" in object_key for object_key in dataset_manifest_keys)
        )


if __name__ == "__main__":
    unittest.main()
