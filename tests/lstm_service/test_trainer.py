"""Focused tests for Epic 4 Story 4.2 training and model save."""

from __future__ import annotations

import json
import os
from pathlib import Path
from unittest import mock
import unittest

from parallel_truth_fingerprint.contracts.training_dataset import (
    TrainingDatasetManifest,
    TrainingWindow,
)
from parallel_truth_fingerprint.lstm_service import train_and_save_lstm_fingerprint
from parallel_truth_fingerprint.persistence import MinioArtifactStore, MinioStoreConfig
from tests.persistence.test_service import FakeMinioClient


def build_training_windows() -> tuple[TrainingWindow, ...]:
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
                (70.0, 5.0, 3100.0),
                (70.5, 5.1, 3110.0),
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
                (70.5, 5.1, 3110.0),
                (71.0, 5.2, 3120.0),
            ),
        ),
    )


def build_manifest() -> TrainingDatasetManifest:
    return TrainingDatasetManifest(
        dataset_id="training-dataset::round-1::round-3::seq-2",
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


class _FakeLayer:
    def __init__(self, *args, **kwargs) -> None:
        self.args = args
        self.kwargs = kwargs

    def __call__(self, value):
        return {
            "layer": self.__class__.__name__,
            "input": value,
            "args": self.args,
            "kwargs": self.kwargs,
        }


class _FakeDense(_FakeLayer):
    pass


class _FakeLSTM(_FakeLayer):
    pass


class _FakeRepeatVector(_FakeLayer):
    pass


class _FakeTimeDistributed(_FakeLayer):
    pass


class _FakeHistory:
    history = {"loss": [0.21, 0.12]}


class _FakeModel:
    def __init__(self, inputs, outputs, name: str) -> None:
        self.inputs = inputs
        self.outputs = outputs
        self.name = name
        self.compiled = None
        self.fit_args = None

    def compile(self, optimizer: str, loss: str) -> None:
        self.compiled = {"optimizer": optimizer, "loss": loss}

    def fit(self, features, targets, *, epochs: int, batch_size: int, verbose: int):
        self.fit_args = {
            "features": features,
            "targets": targets,
            "epochs": epochs,
            "batch_size": batch_size,
            "verbose": verbose,
        }
        return _FakeHistory()

    def save(self, path) -> None:
        Path(path).write_bytes(b"fake-keras-model")


class _FakeKeras:
    class layers:
        LSTM = _FakeLSTM
        RepeatVector = _FakeRepeatVector
        TimeDistributed = _FakeTimeDistributed
        Dense = _FakeDense

    @staticmethod
    def Input(*, shape, name: str):
        return {"shape": shape, "name": name}

    @staticmethod
    def Model(inputs, outputs, name: str):
        return _FakeModel(inputs, outputs, name)


class TrainerTests(unittest.TestCase):
    def build_store(self) -> tuple[MinioArtifactStore, FakeMinioClient]:
        fake_client = FakeMinioClient()
        store = MinioArtifactStore(
            MinioStoreConfig(
                endpoint="localhost:9000",
                access_key="minioadmin",
                secret_key="minioadmin",
                bucket="valid-consensus-artifacts",
            ),
            client=fake_client,
        )
        return store, fake_client

    def test_train_and_save_lstm_fingerprint_persists_model_and_metadata(self) -> None:
        store, fake_client = self.build_store()
        training_windows = build_training_windows()
        manifest = build_manifest()

        with mock.patch(
            "parallel_truth_fingerprint.lstm_service.trainer._load_keras_module",
            return_value=_FakeKeras(),
        ):
            with mock.patch(
                "parallel_truth_fingerprint.lstm_service.trainer._export_model_bytes",
                return_value=b"fake-keras-model",
            ):
                metadata = train_and_save_lstm_fingerprint(
                    training_windows=training_windows,
                    dataset_manifest=manifest,
                    artifact_store=store,
                    epochs=4,
                    batch_size=2,
                    latent_units=8,
                )

        self.assertEqual(metadata.backend, "torch")
        self.assertEqual(metadata.model_format, "keras")
        self.assertEqual(metadata.model_type, "lstm_autoencoder")
        self.assertEqual(metadata.source_dataset_id, manifest.dataset_id)
        self.assertEqual(metadata.sequence_length, 2)
        self.assertEqual(metadata.training_window_count, 2)
        self.assertEqual(metadata.epochs, 4)
        self.assertEqual(metadata.batch_size, 2)
        self.assertEqual(metadata.loss_name, "mse")
        self.assertTrue(metadata.model_object_key.startswith("fingerprint-models/"))
        self.assertTrue(metadata.model_object_key.endswith(".keras"))
        self.assertTrue(metadata.metadata_object_key.startswith("fingerprint-models/"))
        self.assertTrue(metadata.metadata_object_key.endswith(".json"))
        self.assertTrue(metadata.artifact_uri.startswith("minio://valid-consensus-artifacts/"))
        self.assertEqual(metadata.final_training_loss, 0.12)
        self.assertIn(
            ("valid-consensus-artifacts", metadata.model_object_key),
            fake_client.objects,
        )
        self.assertIn(
            ("valid-consensus-artifacts", metadata.metadata_object_key),
            fake_client.objects,
        )
        saved_metadata = json.loads(
            fake_client.objects[
                ("valid-consensus-artifacts", metadata.metadata_object_key)
            ].decode("utf-8")
        )
        self.assertEqual(saved_metadata["backend"], "torch")
        self.assertEqual(saved_metadata["model_format"], "keras")

    def test_train_and_save_lstm_fingerprint_rejects_empty_windows(self) -> None:
        store, _ = self.build_store()

        with self.assertRaises(ValueError):
            train_and_save_lstm_fingerprint(
                training_windows=(),
                dataset_manifest=build_manifest(),
                artifact_store=store,
            )

    def test_train_and_save_lstm_fingerprint_rejects_schema_mismatch(self) -> None:
        store, _ = self.build_store()
        training_windows = list(build_training_windows())
        training_windows[1] = TrainingWindow(
            window_id=training_windows[1].window_id,
            artifact_keys=training_windows[1].artifact_keys,
            round_ids=training_windows[1].round_ids,
            timestamps=training_windows[1].timestamps,
            feature_schema=("temperature.pv", "pressure.pv"),
            feature_matrix=training_windows[1].feature_matrix,
        )

        with self.assertRaises(ValueError):
            train_and_save_lstm_fingerprint(
                training_windows=tuple(training_windows),
                dataset_manifest=build_manifest(),
                artifact_store=store,
            )

    def test_load_keras_module_rejects_non_torch_backend_override(self) -> None:
        from parallel_truth_fingerprint.lstm_service.trainer import _load_keras_module

        previous_backend = os.environ.get("KERAS_BACKEND")
        try:
            os.environ["KERAS_BACKEND"] = "tensorflow"
            with self.assertRaises(RuntimeError):
                _load_keras_module()
        finally:
            if previous_backend is None:
                os.environ.pop("KERAS_BACKEND", None)
            else:
                os.environ["KERAS_BACKEND"] = previous_backend


if __name__ == "__main__":
    unittest.main()
