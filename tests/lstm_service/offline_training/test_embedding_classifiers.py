"""Tests for the embedding LSTM/GRU classifiers (Embedding over syscalls)."""

from __future__ import annotations

import os
import unittest

# Force the torch backend before any keras import, like the sibling tests.
os.environ.setdefault("KERAS_BACKEND", "torch")

from parallel_truth_fingerprint.lstm_service.offline_training.models import (  # noqa: E402
    load_model,
)
from parallel_truth_fingerprint.lstm_service.offline_training.models.base import (  # noqa: E402
    FitResult,
)
from parallel_truth_fingerprint.lstm_service.offline_training.models.embedding_classifiers import (  # noqa: E402
    GruEmbeddingClassifier,
    LstmEmbeddingClassifier,
)


def _token_batch(
    n_samples: int, sequence_length: int, token: int
) -> tuple[tuple[tuple[float, ...], ...], ...]:
    """Build n_samples windows of one repeated integer token (as float)."""
    return tuple(
        tuple((float(token),) for _ in range(sequence_length))
        for _ in range(n_samples)
    )


class EmbeddingClassifierRegistrationTests(unittest.TestCase):
    def test_both_embedding_models_registered(self) -> None:
        self.assertEqual(
            load_model("lstm-embedding-classifier").name,
            "lstm-embedding-classifier",
        )
        self.assertEqual(
            load_model("gru-embedding-classifier").name,
            "gru-embedding-classifier",
        )


class EmbeddingClassifierBuildTests(unittest.TestCase):
    def test_build_topology_outputs_class_count(self) -> None:
        adapter = LstmEmbeddingClassifier()
        handle = adapter.build(
            sequence_length=6,
            feature_count=1,
            class_count=3,
            learning_rate=1e-3,
            seed=42,
            extra_hyperparameters={
                "vocab_size": 64,
                "embed_dim": 8,
                "hidden_units": 8,
                "num_layers": 1,
                "dropout": 0.1,
            },
        )
        self.assertTrue(hasattr(handle, "count_params"))
        self.assertGreater(handle.count_params(), 0)
        self.assertEqual(handle.output_shape, (None, 3))

    def test_feature_count_other_than_one_raises(self) -> None:
        adapter = LstmEmbeddingClassifier()
        with self.assertRaises(ValueError):
            adapter.build(
                sequence_length=4,
                feature_count=2,
                class_count=2,
                learning_rate=1e-3,
                seed=0,
                extra_hyperparameters={},
            )

    def test_defaults_used_when_extra_empty(self) -> None:
        # No extra hyperparameters -> module defaults (vocab 512, embed 64...).
        adapter = GruEmbeddingClassifier()
        handle = adapter.build(
            sequence_length=4,
            feature_count=1,
            class_count=2,
            learning_rate=1e-3,
            seed=0,
            extra_hyperparameters={},
        )
        self.assertEqual(handle.output_shape, (None, 2))


class EmbeddingClassifierFitPredictTests(unittest.TestCase):
    def test_fit_predict_round_trip(self) -> None:
        adapter = LstmEmbeddingClassifier()
        handle = adapter.build(
            sequence_length=5,
            feature_count=1,
            class_count=2,
            learning_rate=1e-2,
            seed=0,
            extra_hyperparameters={
                "vocab_size": 32,
                "embed_dim": 8,
                "hidden_units": 8,
                "num_layers": 1,
                "dropout": 0.0,
            },
        )
        # Class 0 = token 2 everywhere; class 1 = token 20 everywhere.
        x_train = _token_batch(8, 5, 2) + _token_batch(8, 5, 20)
        y_train = tuple([0] * 8 + [1] * 8)
        x_test = _token_batch(2, 5, 2) + _token_batch(2, 5, 20)
        fit_result = adapter.fit(
            model_handle=handle,
            x_train=x_train,
            y_train=y_train,
            epochs=2,
            batch_size=4,
        )
        self.assertIsInstance(fit_result, FitResult)
        self.assertEqual(fit_result.epochs_executed, 2)
        self.assertGreater(fit_result.parameter_count, 0)
        predictions = adapter.predict(
            model_handle=fit_result.model_handle, x_test=x_test
        )
        self.assertEqual(len(predictions), 4)
        for label in predictions:
            self.assertIn(label, (0, 1))


class EmbeddingEndToEndTests(unittest.TestCase):
    def test_embedding_benchmark_with_embedding_model_runs(self) -> None:
        # End-to-end through execute_training_run on the fixture-backed
        # embedding benchmark (feature_count == 1, as the embedding model
        # requires). ADFA_LD_PATH points the registered adapter at the
        # embedded fixture so no real dataset is needed.
        from pathlib import Path

        from parallel_truth_fingerprint.lstm_service.offline_training.training.run import (
            execute_training_run,
        )

        fixture = (
            Path(__file__).resolve().parent / "fixtures" / "adfa_ld_fixture"
        )
        previous = os.environ.get("ADFA_LD_PATH")
        os.environ["ADFA_LD_PATH"] = str(fixture)
        try:
            record = execute_training_run(
                benchmark="adfa-ld-embed-binary",
                model="gru-embedding-classifier",
                epochs=1,
                batch_size=4,
                learning_rate=1e-2,
                sequence_length=4,
                seed=42,
                extra_hyperparameters={
                    "vocab_size": 512,
                    "embed_dim": 4,
                    "hidden_units": 4,
                    "num_layers": 1,
                },
            )
        finally:
            if previous is None:
                os.environ.pop("ADFA_LD_PATH", None)
            else:
                os.environ["ADFA_LD_PATH"] = previous
        self.assertEqual(record.model_name, "gru-embedding-classifier")
        self.assertEqual(record.dataset_name, "adfa-ld-embed-binary")
        self.assertEqual(record.epochs_executed, 1)
        self.assertIn("macro_f1", record.metrics)


if __name__ == "__main__":
    unittest.main()
