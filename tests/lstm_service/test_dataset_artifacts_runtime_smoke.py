"""Real runtime smoke validation for Epic 4 Story 4.2A."""

from __future__ import annotations

from datetime import datetime, timedelta, timezone
import importlib.util
import io
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
)
from parallel_truth_fingerprint.persistence import (
    MinioArtifactStore,
    MinioStoreConfig,
    persist_valid_consensus_artifact,
)
from parallel_truth_fingerprint.scada import FakeOpcUaScadaService
from tests.persistence.test_service import build_valid_audit_package


def _real_dataset_smoke_enabled() -> bool:
    return os.getenv("RUN_REAL_DATASET_ARTIFACT_SMOKE") == "1"


def _dependencies_available() -> bool:
    return (
        importlib.util.find_spec("numpy") is not None
        and importlib.util.find_spec("minio") is not None
    )


def _minio_available(host: str = "127.0.0.1", port: int = 9000) -> bool:
    try:
        with socket.create_connection((host, port), timeout=2):
            return True
    except OSError:
        return False


@unittest.skipUnless(
    _real_dataset_smoke_enabled(),
    "Set RUN_REAL_DATASET_ARTIFACT_SMOKE=1 to run the real MinIO dataset smoke test.",
)
@unittest.skipUnless(
    _dependencies_available(),
    "Required runtime dependencies for Story 4.2A are not installed.",
)
@unittest.skipUnless(
    _minio_available(),
    "Local MinIO is not reachable on 127.0.0.1:9000.",
)
class RuntimeDatasetArtifactSmokeTests(unittest.TestCase):
    def test_real_dataset_artifact_smoke_persists_manifest_and_windows_to_minio(self) -> None:
        run_suffix = datetime.now(timezone.utc).strftime("%Y%m%d%H%M%S%f")
        bucket_name = f"fingerprint-datasets-smoke-{run_suffix}"
        store = MinioArtifactStore(
            MinioStoreConfig(
                endpoint="localhost:9000",
                access_key="minioadmin",
                secret_key="minioadmin",
                bucket=bucket_name,
                secure=False,
            )
        )
        numpy = __import__("numpy")

        for index in range(3):
            audit_package = build_valid_audit_package(
                round_id=f"round-dataset-smoke-{run_suffix}-{index + 1:03d}"
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
                    "training_eligibility_reason": "story_4_2a_runtime_smoke",
                },
                artifact_store=store,
                persisted_at=datetime(2026, 4, 2, 18, 0, 0, tzinfo=timezone.utc)
                + timedelta(minutes=index),
            )

        replay_package = build_valid_audit_package(round_id=f"round-dataset-smoke-{run_suffix}-replay")
        replay_scada_state = FakeOpcUaScadaService().project_state(
            replay_package.consensused_valid_state
        )
        replay_output = build_scada_comparison_output(
            compare_consensused_to_scada(
                valid_state=replay_package.consensused_valid_state,
                scada_state=replay_scada_state,
                tolerance_profile=ScadaToleranceProfile(
                    temperature=1.0,
                    pressure=0.3,
                    rpm=100.0,
                ),
            )
        )
        persist_valid_consensus_artifact(
            audit_package=replay_package,
            scada_state=replay_scada_state,
            scada_comparison_output=replay_output,
            dataset_context={
                "scenario_label": "replay",
                "training_label": "non_normal",
                "training_eligible": False,
                "training_eligibility_reason": "scenario:replay",
            },
            artifact_store=store,
            persisted_at=datetime(2026, 4, 2, 18, 3, 0, tzinfo=timezone.utc),
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
            created_at=datetime(2026, 4, 2, 18, 5, 0, tzinfo=timezone.utc),
        )

        manifest_payload = store.load_json(persisted_dataset.manifest_object_key)
        windows_payload = store.load_bytes(persisted_dataset.windows_object_key)
        windows_archive = numpy.load(io.BytesIO(windows_payload))

        self.assertEqual(dataset_manifest.eligible_record_count, 3)
        self.assertEqual(dataset_manifest.window_count, 2)
        self.assertEqual(
            manifest_payload["adequacy_assessment"]["validation_level"],
            "runtime_valid_only",
        )
        self.assertFalse(manifest_payload["adequacy_assessment"]["adequacy_met"])
        self.assertEqual(
            manifest_payload["skipped_artifacts"][
                f"valid-consensus-artifacts/round-dataset-smoke-{run_suffix}-replay.json"
            ],
            "training_label_not_normal",
        )
        self.assertEqual(tuple(windows_archive["feature_tensor"].shape), (2, 2, 27))
        self.assertEqual(
            tuple(windows_archive["artifact_keys"][0]),
            (
                f"valid-consensus-artifacts/round-dataset-smoke-{run_suffix}-001.json",
                f"valid-consensus-artifacts/round-dataset-smoke-{run_suffix}-002.json",
            ),
        )
        self.assertEqual(manifest_payload["source_bucket"], bucket_name)
        self.assertTrue(
            persisted_dataset.manifest_object_key.startswith("fingerprint-datasets/")
        )
        self.assertTrue(
            persisted_dataset.windows_object_key.startswith("fingerprint-datasets/")
        )


if __name__ == "__main__":
    unittest.main()
