"""Real runtime smoke validation for Epic 4 Story 4.2."""

from __future__ import annotations

from datetime import datetime, timedelta, timezone
import importlib.util
import json
import os
from pathlib import Path
import socket
import unittest

from parallel_truth_fingerprint.comparison import (
    ScadaToleranceProfile,
    build_scada_comparison_output,
    compare_consensused_to_scada,
)
from parallel_truth_fingerprint.lstm_service import (
    build_normal_training_windows,
    train_and_save_lstm_fingerprint,
)
from parallel_truth_fingerprint.persistence import (
    MinioArtifactStore,
    MinioStoreConfig,
    persist_valid_consensus_artifact,
)
from parallel_truth_fingerprint.scada import FakeOpcUaScadaService
from tests.persistence.test_service import build_valid_audit_package


def _real_ml_smoke_enabled() -> bool:
    return os.getenv("RUN_REAL_ML_SMOKE") == "1"


def _dependencies_available() -> bool:
    return (
        importlib.util.find_spec("keras") is not None
        and importlib.util.find_spec("torch") is not None
        and importlib.util.find_spec("minio") is not None
    )


def _minio_available(host: str = "127.0.0.1", port: int = 9000) -> bool:
    try:
        with socket.create_connection((host, port), timeout=2):
            return True
    except OSError:
        return False


@unittest.skipUnless(
    _real_ml_smoke_enabled(),
    "Set RUN_REAL_ML_SMOKE=1 to run the real keras+torch+MinIO smoke test.",
)
@unittest.skipUnless(
    _dependencies_available(),
    "Real ML dependencies are not installed in this environment.",
)
@unittest.skipUnless(
    _minio_available(),
    "Local MinIO is not reachable on 127.0.0.1:9000.",
)
class RuntimeTrainerSmokeTests(unittest.TestCase):
    def test_real_training_smoke_persists_model_and_metadata_to_minio(self) -> None:
        run_suffix = datetime.now(timezone.utc).strftime("%Y%m%d%H%M%S%f")
        bucket_name = f"valid-consensus-artifacts-smoke-{run_suffix}"
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
                round_id=f"round-smoke-{run_suffix}-{index + 1:03d}"
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
                    "training_eligibility_reason": "story_4_2_runtime_smoke",
                },
                artifact_store=store,
                persisted_at=datetime(2026, 4, 2, 12, 0, 0, tzinfo=timezone.utc)
                + timedelta(minutes=index),
            )

        training_windows, dataset_manifest = build_normal_training_windows(
            artifact_store=store,
            sequence_length=2,
            prefix="valid-consensus-artifacts/",
        )
        metadata = train_and_save_lstm_fingerprint(
            training_windows=training_windows,
            dataset_manifest=dataset_manifest,
            artifact_store=store,
            epochs=1,
            batch_size=1,
            latent_units=4,
        )

        saved_model = store.load_bytes(metadata.model_object_key)
        saved_metadata = store.load_json(metadata.metadata_object_key)
        keras = __import__("keras")
        numpy = __import__("numpy")
        scratch_root = Path(".tmp") / "lstm_service_runtime_smoke"
        scratch_root.mkdir(parents=True, exist_ok=True)
        archive_path = scratch_root / f"{metadata.model_id}.keras"
        archive_path.write_bytes(saved_model)
        try:
            loaded_model = keras.saving.load_model(str(archive_path), compile=False)
            prediction = loaded_model.predict(
                numpy.asarray([training_windows[0].feature_matrix], dtype="float32"),
                verbose=0,
            )
        finally:
            archive_path.unlink(missing_ok=True)

        self.assertEqual(os.environ.get("KERAS_BACKEND"), "torch")
        self.assertEqual(len(training_windows), 2)
        self.assertTrue(metadata.model_object_key.endswith(".keras"))
        self.assertTrue(metadata.metadata_object_key.endswith(".json"))
        self.assertGreater(len(saved_model), 0)
        self.assertEqual(
            tuple(prediction.shape),
            (1, 2, len(training_windows[0].feature_schema)),
        )
        self.assertEqual(saved_metadata["backend"], "torch")
        self.assertEqual(saved_metadata["model_format"], "keras")
        self.assertEqual(saved_metadata["source_dataset_id"], dataset_manifest.dataset_id)
        self.assertEqual(saved_metadata["bucket"], bucket_name)
        self.assertEqual(saved_metadata["training_window_count"], 2)
        self.assertEqual(saved_metadata["epochs"], 1)
        self.assertEqual(saved_metadata["batch_size"], 1)
        self.assertIn("artifact_uri", saved_metadata)
        self.assertIsInstance(saved_metadata["final_training_loss"], float)


if __name__ == "__main__":
    unittest.main()
