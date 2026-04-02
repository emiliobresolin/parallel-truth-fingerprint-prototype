"""Real runtime smoke validation for Epic 4 Story 4.3."""

from __future__ import annotations

from datetime import datetime, timedelta, timezone
import importlib.util
import os
import socket
import unittest

from parallel_truth_fingerprint.comparison import (
    ScadaToleranceProfile,
    build_scada_comparison_output,
    compare_consensused_to_scada,
)
from parallel_truth_fingerprint.lstm_service import (
    build_normal_training_windows,
    persist_training_dataset_artifacts,
    run_lstm_fingerprint_inference_from_persisted_dataset,
    train_and_save_lstm_fingerprint_from_persisted_dataset,
)
from parallel_truth_fingerprint.persistence import (
    MinioArtifactStore,
    MinioStoreConfig,
    persist_valid_consensus_artifact,
)
from parallel_truth_fingerprint.scada import FakeOpcUaScadaService
from tests.persistence.test_service import build_valid_audit_package


def _real_ml_inference_smoke_enabled() -> bool:
    return os.getenv("RUN_REAL_ML_INFERENCE_SMOKE") == "1"


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


@unittest.skipUnless(
    _real_ml_inference_smoke_enabled(),
    "Set RUN_REAL_ML_INFERENCE_SMOKE=1 to run the real inference smoke test.",
)
@unittest.skipUnless(
    _dependencies_available(),
    "Required runtime dependencies for Story 4.3 are not installed.",
)
@unittest.skipUnless(
    _minio_available(),
    "Local MinIO is not reachable on 127.0.0.1:9000.",
)
class RuntimeInferenceSmokeTests(unittest.TestCase):
    def test_real_inference_smoke_runs_from_persisted_dataset_artifact_path(self) -> None:
        run_suffix = datetime.now(timezone.utc).strftime("%Y%m%d%H%M%S%f")
        bucket_name = f"valid-consensus-artifacts-inference-smoke-{run_suffix}"
        store = MinioArtifactStore(
            MinioStoreConfig(
                endpoint="localhost:9000",
                access_key="minioadmin",
                secret_key="minioadmin",
                bucket=bucket_name,
                secure=False,
            )
        )
        os.environ.pop("KERAS_BACKEND", None)

        for index in range(3):
            audit_package = build_valid_audit_package(
                round_id=f"round-inference-smoke-{run_suffix}-{index + 1:03d}"
            )
            scada_state = FakeOpcUaScadaService().project_state(
                audit_package.consensused_valid_state
            )
            comparison_output = build_scada_comparison_output(
                compare_consensused_to_scada(
                    valid_state=audit_package.consensused_valid_state,
                    scada_state=scada_state,
                    tolerance_profile=ScadaToleranceProfile(
                        temperature=1.0,
                        pressure=0.3,
                        rpm=100.0,
                    ),
                )
            )
            persist_valid_consensus_artifact(
                audit_package=audit_package,
                scada_state=scada_state,
                scada_comparison_output=comparison_output,
                dataset_context={
                    "scenario_label": "normal",
                    "training_label": "normal",
                    "training_eligible": True,
                    "training_eligibility_reason": "story_4_3_runtime_smoke",
                },
                artifact_store=store,
                persisted_at=datetime(2026, 4, 2, 19, 0, 0, tzinfo=timezone.utc)
                + timedelta(minutes=index),
            )

        training_windows, dataset_manifest = build_normal_training_windows(
            artifact_store=store,
            sequence_length=2,
            prefix="valid-consensus-artifacts/",
        )
        persisted_dataset = persist_training_dataset_artifacts(
            training_windows=training_windows,
            dataset_manifest=dataset_manifest,
            artifact_store=store,
            created_at=datetime(2026, 4, 2, 19, 5, 0, tzinfo=timezone.utc),
        )
        model_metadata = train_and_save_lstm_fingerprint_from_persisted_dataset(
            manifest_object_key=persisted_dataset.manifest_object_key,
            artifact_store=store,
            epochs=1,
            batch_size=1,
            latent_units=4,
        )

        results = run_lstm_fingerprint_inference_from_persisted_dataset(
            model_metadata_object_key=model_metadata.metadata_object_key,
            inference_manifest_object_key=persisted_dataset.manifest_object_key,
            artifact_store=store,
        )

        self.assertEqual(len(results), 2)
        self.assertTrue(
            all(result.output_channel == "lstm_fingerprint" for result in results)
        )
        self.assertTrue(
            all(
                result.source_dataset_validation_level == "runtime_valid_only"
                for result in results
            )
        )
        self.assertTrue(
            all(
                "runtime-valid but not yet meaningful-fingerprint-valid"
                in result.limitation_note
                for result in results
            )
        )
        self.assertTrue(all(result.classification.value == "normal" for result in results))
        self.assertTrue(all(result.anomaly_score >= 0.0 for result in results))
        self.assertTrue(all(result.classification_threshold > 0.0 for result in results))
        self.assertEqual(
            results[0].source_dataset_id,
            dataset_manifest.dataset_id,
        )
        self.assertEqual(
            results[0].inference_dataset_id,
            dataset_manifest.dataset_id,
        )


if __name__ == "__main__":
    unittest.main()
