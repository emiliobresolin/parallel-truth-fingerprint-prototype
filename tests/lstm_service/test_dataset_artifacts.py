"""Focused tests for Epic 4 Story 4.2A dataset artifact persistence."""

from __future__ import annotations

from datetime import datetime, timezone
import io
import unittest

from parallel_truth_fingerprint.lstm_service import (
    build_normal_training_windows,
    evaluate_training_dataset_adequacy,
    load_persisted_training_dataset_artifacts,
    persist_training_dataset_artifacts,
)
from parallel_truth_fingerprint.persistence import MinioArtifactStore, MinioStoreConfig
from tests.lstm_service.test_dataset_builder import build_persisted_artifact
from tests.persistence.test_service import FakeMinioClient


class DatasetArtifactTests(unittest.TestCase):
    def build_store(self) -> MinioArtifactStore:
        return MinioArtifactStore(
            MinioStoreConfig(
                endpoint="localhost:9000",
                access_key="minioadmin",
                secret_key="minioadmin",
                bucket="valid-consensus-artifacts",
            ),
            client=FakeMinioClient(),
        )

    def test_evaluate_training_dataset_adequacy_distinguishes_runtime_from_meaningful(self) -> None:
        runtime_only = evaluate_training_dataset_adequacy(
            eligible_artifact_count=3,
            window_count=2,
        )
        meaningful = evaluate_training_dataset_adequacy(
            eligible_artifact_count=30,
            window_count=20,
        )

        self.assertEqual(runtime_only.validation_level, "runtime_valid_only")
        self.assertFalse(runtime_only.adequacy_met)
        self.assertEqual(runtime_only.status_reason, "below_default_adequacy_floor")
        self.assertEqual(meaningful.validation_level, "meaningful_fingerprint_valid")
        self.assertTrue(meaningful.adequacy_met)
        self.assertEqual(meaningful.status_reason, "adequacy_floor_met")

    def test_persist_training_dataset_artifacts_writes_manifest_and_windows_npz(self) -> None:
        store = self.build_store()
        for index in range(1, 5):
            artifact = build_persisted_artifact(index=index)
            store.save_json(artifact["artifact_key"], artifact)

        training_windows, dataset_manifest = build_normal_training_windows(
            artifact_store=store,
            sequence_length=3,
        )
        persisted_artifact = persist_training_dataset_artifacts(
            training_windows=training_windows,
            dataset_manifest=dataset_manifest,
            artifact_store=store,
            created_at=datetime(2026, 4, 2, 15, 0, 0, tzinfo=timezone.utc),
        )

        manifest_payload = store.load_json(persisted_artifact.manifest_object_key)
        windows_payload = store.load_bytes(persisted_artifact.windows_object_key)
        numpy = __import__("numpy")
        windows_archive = numpy.load(io.BytesIO(windows_payload))

        self.assertEqual(
            persisted_artifact.manifest_object_key,
            "fingerprint-datasets/training-dataset::round-501::round-504::seq-3.manifest.json",
        )
        self.assertEqual(
            persisted_artifact.windows_object_key,
            "fingerprint-datasets/training-dataset::round-501::round-504::seq-3.windows.npz",
        )
        self.assertEqual(manifest_payload["chronological_ordering_rule"], "round_identity.window_ended_at_then_artifact_key")
        self.assertEqual(manifest_payload["stride"], 1)
        self.assertEqual(manifest_payload["overlap_behavior"], "sliding_stride_1")
        self.assertEqual(manifest_payload["eligible_artifact_count"], 4)
        self.assertEqual(manifest_payload["window_count"], 2)
        self.assertEqual(manifest_payload["tensor_shape"], [2, 3, 27])
        self.assertEqual(
            manifest_payload["adequacy_assessment"]["validation_level"],
            "runtime_valid_only",
        )
        self.assertEqual(tuple(windows_archive["feature_tensor"].shape), (2, 3, 27))
        self.assertEqual(
            tuple(windows_archive["artifact_keys"][0]),
            (
                "valid-consensus-artifacts/round-501.json",
                "valid-consensus-artifacts/round-502.json",
                "valid-consensus-artifacts/round-503.json",
            ),
        )
        self.assertEqual(
            tuple(windows_archive["round_ids"][1]),
            ("round-502", "round-503", "round-504"),
        )
        self.assertEqual(
            tuple(windows_archive["labels"]),
            ("normal", "normal"),
        )

        loaded_windows, loaded_manifest = load_persisted_training_dataset_artifacts(
            manifest_object_key=persisted_artifact.manifest_object_key,
            artifact_store=store,
        )
        self.assertEqual(loaded_manifest.dataset_id, dataset_manifest.dataset_id)
        self.assertEqual(len(loaded_windows), 2)
        self.assertEqual(
            loaded_windows[0].artifact_keys,
            (
                "valid-consensus-artifacts/round-501.json",
                "valid-consensus-artifacts/round-502.json",
                "valid-consensus-artifacts/round-503.json",
            ),
        )
        self.assertEqual(len(loaded_windows[0].feature_matrix[0]), 27)

    def test_persisted_manifest_records_excluded_records_and_reasons(self) -> None:
        store = self.build_store()
        normal = build_persisted_artifact(index=1)
        replay = build_persisted_artifact(
            index=2,
            scenario_label="replay",
            training_eligible=False,
        )
        faulty_edge = build_persisted_artifact(
            index=3,
            scenario_label="faulty_edge_exclusion",
            training_eligible=False,
        )
        scada_divergent = build_persisted_artifact(
            index=4,
            scenario_label="normal",
            training_eligible=True,
            has_scada_divergence=True,
        )
        failed_consensus = build_persisted_artifact(index=5)
        failed_consensus["consensus_context"]["final_consensus_status"] = "failed_consensus"
        missing_context = build_persisted_artifact(index=6)
        missing_context.pop("dataset_context")

        for artifact in (
            normal,
            replay,
            faulty_edge,
            scada_divergent,
            failed_consensus,
            missing_context,
        ):
            store.save_json(artifact["artifact_key"], artifact)

        training_windows, dataset_manifest = build_normal_training_windows(
            artifact_store=store,
            sequence_length=2,
        )
        persisted_artifact = persist_training_dataset_artifacts(
            training_windows=training_windows,
            dataset_manifest=dataset_manifest,
            artifact_store=store,
            created_at=datetime(2026, 4, 2, 16, 0, 0, tzinfo=timezone.utc),
        )
        manifest_payload = store.load_json(persisted_artifact.manifest_object_key)
        windows_archive = __import__("numpy").load(
            io.BytesIO(store.load_bytes(persisted_artifact.windows_object_key))
        )

        self.assertEqual(dataset_manifest.eligible_record_count, 1)
        self.assertEqual(dataset_manifest.window_count, 0)
        self.assertEqual(tuple(windows_archive["feature_tensor"].shape), (0, 2, 27))
        self.assertEqual(
            manifest_payload["skipped_artifacts"]["valid-consensus-artifacts/round-502.json"],
            "training_label_not_normal",
        )
        self.assertEqual(
            manifest_payload["skipped_artifacts"]["valid-consensus-artifacts/round-503.json"],
            "training_label_not_normal",
        )
        self.assertEqual(
            manifest_payload["skipped_artifacts"]["valid-consensus-artifacts/round-504.json"],
            "scada_divergence",
        )
        self.assertEqual(
            manifest_payload["skipped_artifacts"]["valid-consensus-artifacts/round-505.json"],
            "consensus_not_success",
        )
        self.assertEqual(
            manifest_payload["skipped_artifacts"]["valid-consensus-artifacts/round-506.json"],
            "missing_dataset_context",
        )
        self.assertEqual(
            manifest_payload["adequacy_assessment"]["validation_level"],
            "runtime_valid_only",
        )


if __name__ == "__main__":
    unittest.main()
