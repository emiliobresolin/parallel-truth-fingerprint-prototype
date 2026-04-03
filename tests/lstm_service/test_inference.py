"""Focused tests for Epic 4 Story 4.3 fingerprint inference."""

from __future__ import annotations

from unittest import mock
import unittest

from parallel_truth_fingerprint.contracts.fingerprint_model import (
    FingerprintModelArtifact,
)
from parallel_truth_fingerprint.contracts.training_dataset import (
    TrainingDatasetManifest,
    TrainingWindow,
)
from parallel_truth_fingerprint.lstm_service import (
    persist_training_dataset_artifacts,
    run_lstm_fingerprint_inference_from_persisted_dataset,
)
from parallel_truth_fingerprint.persistence import MinioArtifactStore, MinioStoreConfig
from tests.persistence.test_service import FakeMinioClient


def build_training_windows(
    *,
    first_temperature: float = 70.0,
) -> tuple[TrainingWindow, ...]:
    feature_schema = (
        "temperature.pv",
        "pressure.pv",
        "rpm.pv",
    )
    return (
        TrainingWindow(
            window_id="window::round-1::round-2",
            artifact_keys=(
                "valid-consensus-artifacts/round-1.json",
                "valid-consensus-artifacts/round-2.json",
            ),
            round_ids=("round-1", "round-2"),
            timestamps=(
                "2026-04-01T18:01:00+00:00",
                "2026-04-01T18:02:00+00:00",
            ),
            feature_schema=feature_schema,
            feature_matrix=(
                (first_temperature, 5.0, 3100.0),
                (first_temperature + 0.5, 5.1, 3110.0),
            ),
        ),
        TrainingWindow(
            window_id="window::round-2::round-3",
            artifact_keys=(
                "valid-consensus-artifacts/round-2.json",
                "valid-consensus-artifacts/round-3.json",
            ),
            round_ids=("round-2", "round-3"),
            timestamps=(
                "2026-04-01T18:02:00+00:00",
                "2026-04-01T18:03:00+00:00",
            ),
            feature_schema=feature_schema,
            feature_matrix=(
                (first_temperature + 0.5, 5.1, 3110.0),
                (first_temperature + 1.0, 5.2, 3120.0),
            ),
        ),
    )


def build_manifest(dataset_id: str) -> TrainingDatasetManifest:
    return TrainingDatasetManifest(
        dataset_id=dataset_id,
        source_bucket="valid-consensus-artifacts",
        source_prefix="valid-consensus-artifacts/",
        sequence_length=2,
        feature_schema=("temperature.pv", "pressure.pv", "rpm.pv"),
        selected_artifact_keys=(
            "valid-consensus-artifacts/round-1.json",
            "valid-consensus-artifacts/round-2.json",
            "valid-consensus-artifacts/round-3.json",
        ),
        skipped_artifacts={},
        eligible_record_count=3,
        window_count=2,
    )


class _ThresholdAwareFakeModel:
    def predict(self, tensor, verbose: int = 0):
        numpy = __import__("numpy")
        if float(tensor[0, 0, 0]) >= 500.0:
            return numpy.zeros_like(tensor)
        return tensor


class InferenceTests(unittest.TestCase):
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

    def persist_dataset(
        self,
        *,
        store: MinioArtifactStore,
        dataset_id: str,
        first_temperature: float,
    ) -> str:
        persisted = persist_training_dataset_artifacts(
            training_windows=build_training_windows(first_temperature=first_temperature),
            dataset_manifest=build_manifest(dataset_id),
            artifact_store=store,
        )
        return persisted.manifest_object_key

    def persist_model_metadata(
        self,
        *,
        store: MinioArtifactStore,
        source_dataset_id: str,
    ) -> str:
        metadata = FingerprintModelArtifact(
            model_id="model-001",
            created_at="2026-04-02T18:00:00+00:00",
            backend="torch",
            model_format="keras",
            model_type="lstm_autoencoder",
            source_dataset_id=source_dataset_id,
            feature_schema=("temperature.pv", "pressure.pv", "rpm.pv"),
            sequence_length=2,
            training_window_count=2,
            epochs=1,
            batch_size=1,
            loss_name="mse",
            bucket="valid-consensus-artifacts",
            model_object_key="fingerprint-models/model-001.keras",
            metadata_object_key="fingerprint-models/model-001.json",
            artifact_uri="minio://valid-consensus-artifacts/fingerprint-models/model-001.keras",
            metadata_uri="minio://valid-consensus-artifacts/fingerprint-models/model-001.json",
            final_training_loss=0.01,
        )
        store.save_json(metadata.metadata_object_key, metadata.to_dict())
        return metadata.metadata_object_key

    def test_inference_from_source_like_dataset_returns_normal_results(self) -> None:
        store = self.build_store()
        manifest_key = self.persist_dataset(
            store=store,
            dataset_id="training-dataset::round-1::round-3::seq-2",
            first_temperature=70.0,
        )
        metadata_key = self.persist_model_metadata(
            store=store,
            source_dataset_id="training-dataset::round-1::round-3::seq-2",
        )

        with mock.patch(
            "parallel_truth_fingerprint.lstm_service.inference._load_saved_keras_model",
            return_value=_ThresholdAwareFakeModel(),
        ):
            results = run_lstm_fingerprint_inference_from_persisted_dataset(
                model_metadata_object_key=metadata_key,
                inference_manifest_object_key=manifest_key,
                artifact_store=store,
            )

        self.assertEqual(len(results), 2)
        self.assertTrue(all(result.output_channel == "lstm_fingerprint" for result in results))
        self.assertTrue(all(result.classification.value == "normal" for result in results))
        self.assertTrue(all(result.source_dataset_validation_level == "runtime_valid_only" for result in results))
        self.assertTrue(all(result.anomaly_score >= 0.0 for result in results))
        self.assertTrue(all(result.classification_threshold > 0.0 for result in results))
        self.assertIn("runtime-valid but not yet meaningfully fingerprint-valid", results[0].limitation_note)
        self.assertNotIn("Story ", results[0].limitation_note)

    def test_inference_flags_anomalous_results_for_out_of_profile_dataset(self) -> None:
        store = self.build_store()
        self.persist_dataset(
            store=store,
            dataset_id="training-dataset::round-1::round-3::seq-2",
            first_temperature=70.0,
        )
        anomalous_manifest_key = self.persist_dataset(
            store=store,
            dataset_id="inference-dataset::round-101::round-103::seq-2",
            first_temperature=800.0,
        )
        metadata_key = self.persist_model_metadata(
            store=store,
            source_dataset_id="training-dataset::round-1::round-3::seq-2",
        )

        with mock.patch(
            "parallel_truth_fingerprint.lstm_service.inference._load_saved_keras_model",
            return_value=_ThresholdAwareFakeModel(),
        ):
            results = run_lstm_fingerprint_inference_from_persisted_dataset(
                model_metadata_object_key=metadata_key,
                inference_manifest_object_key=anomalous_manifest_key,
                artifact_store=store,
            )

        self.assertEqual(len(results), 2)
        self.assertTrue(
            all(result.classification.value == "anomalous" for result in results)
        )
        self.assertTrue(
            all(result.anomaly_score > result.classification_threshold for result in results)
        )

    def test_inference_rejects_persisted_schema_mismatch(self) -> None:
        store = self.build_store()
        manifest_key = self.persist_dataset(
            store=store,
            dataset_id="training-dataset::round-1::round-3::seq-2",
            first_temperature=70.0,
        )
        metadata_key = self.persist_model_metadata(
            store=store,
            source_dataset_id="training-dataset::round-1::round-3::seq-2",
        )
        manifest_payload = store.load_json(manifest_key)
        manifest_payload["feature_schema"] = ["temperature.pv", "pressure.pv"]
        store.save_json(manifest_key, manifest_payload)

        with self.assertRaises(ValueError):
            run_lstm_fingerprint_inference_from_persisted_dataset(
                model_metadata_object_key=metadata_key,
                inference_manifest_object_key=manifest_key,
                artifact_store=store,
            )


if __name__ == "__main__":
    unittest.main()
