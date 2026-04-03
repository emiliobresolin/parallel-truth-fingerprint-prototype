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
    execute_deferred_fingerprint_lifecycle,
    run_scada_replay_behavior_detection,
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
    """Create one valid audit package with deterministic but varying PV values."""

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
    def test_real_runtime_replay_behavior_surfaces_through_distinct_fingerprint_channel(
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
            run_local_demo.run_scada_comparison_and_persistence(
                consensus_audit=audit_package,
                artifact_store=store,
                scada_service=scada_service,
                fault_mode="none",
                scada_replay_stage=replay_stage,
            )
            execute_deferred_fingerprint_lifecycle(
                cycle_index=cycle_index,
                artifact_store=store,
                sequence_length=config.demo_fingerprint_sequence_length,
                train_after_eligible_cycles=config.demo_train_after_eligible_cycles,
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
        lifecycle_stage, _generic_inference_results = execute_deferred_fingerprint_lifecycle(
            cycle_index=4,
            artifact_store=store,
            sequence_length=config.demo_fingerprint_sequence_length,
            train_after_eligible_cycles=config.demo_train_after_eligible_cycles,
        )
        replay_result, replay_inference_results = run_scada_replay_behavior_detection(
            current_round_id=replay_audit_package.consensused_valid_state.round_identity.round_id,
            consensus_final_status="success",
            scada_state=replay_scada_state,
            comparison_output=comparison_output,
            replay_stage=replay_stage,
            artifact_store=store,
            sequence_length=config.demo_fingerprint_sequence_length,
        )

        self.assertEqual(comparison_stage["status"], "completed")
        self.assertEqual(persistence_stage["status"], "persisted")
        self.assertEqual(
            persistence_stage["record"]["dataset_context"]["training_eligible"],
            False,
        )
        self.assertEqual(
            persistence_stage["record"]["dataset_context"]["scenario_label"],
            "scada_replay",
        )
        self.assertEqual(lifecycle_stage.training_events, ("reused",))
        self.assertEqual(lifecycle_stage.model_status, "model_available")
        self.assertIsNotNone(replay_result)
        self.assertEqual(replay_result.output_channel, "scada_replay_behavior")
        self.assertEqual(replay_result.scenario_mode, "replay")
        self.assertEqual(replay_result.consensus_final_status, "success")
        self.assertTrue(replay_result.scada_divergent_sensors)
        self.assertEqual(replay_result.source_dataset_validation_level, "runtime_valid_only")
        self.assertIn(
            "runtime-valid but not yet meaningfully fingerprint-valid",
            replay_result.limitation_note,
        )
        self.assertNotIn("Story ", replay_result.limitation_note)
        self.assertTrue(replay_inference_results)
        self.assertEqual(replay_inference_results[0].output_channel, "lstm_fingerprint")
        self.assertEqual(replay_result.classification.value, "anomalous")

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
