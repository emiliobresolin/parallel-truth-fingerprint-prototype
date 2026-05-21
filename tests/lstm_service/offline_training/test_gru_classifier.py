"""Story 7.8: GRU classifier baseline tests."""

from __future__ import annotations

import os
import unittest
from pathlib import Path

os.environ.setdefault("KERAS_BACKEND", "torch")

from parallel_truth_fingerprint.lstm_service.offline_training.models import (  # noqa: E402
    load_model,
)
from parallel_truth_fingerprint.lstm_service.offline_training.models.gru_classifier import (  # noqa: E402
    GruClassifier,
)
from parallel_truth_fingerprint.lstm_service.offline_training.models.base import (  # noqa: E402
    FitResult,
)


FIXTURE_PATH = (
    Path(__file__).resolve().parent / "fixtures" / "adfa_ld_fixture"
)


def _toy_batch(
    n_samples: int, sequence_length: int, feature_count: int, fill: float
) -> tuple[tuple[tuple[float, ...], ...], ...]:
    return tuple(
        tuple(tuple(fill for _ in range(feature_count)) for _ in range(sequence_length))
        for _ in range(n_samples)
    )


class GruClassifierAdapterTests(unittest.TestCase):
    def test_adapter_registered_under_gru_classifier(self) -> None:
        adapter = load_model("gru-classifier")
        self.assertEqual(adapter.name, "gru-classifier")

    def test_build_returns_keras_model_with_expected_topology(self) -> None:
        adapter = GruClassifier()
        handle = adapter.build(
            sequence_length=4,
            feature_count=3,
            class_count=2,
            learning_rate=1e-3,
            seed=7,
            extra_hyperparameters={"hidden_units": 8, "num_layers": 2},
        )
        self.assertTrue(hasattr(handle, "count_params"))
        self.assertGreater(handle.count_params(), 0)
        self.assertEqual(handle.output_shape, (None, 2))

    def test_fit_predict_round_trip_does_not_raise(self) -> None:
        adapter = GruClassifier()
        handle = adapter.build(
            sequence_length=3,
            feature_count=2,
            class_count=2,
            learning_rate=1e-2,
            seed=0,
            extra_hyperparameters={"hidden_units": 4, "num_layers": 1},
        )
        x_train = _toy_batch(8, 3, 2, 0.0) + _toy_batch(8, 3, 2, 1.0)
        y_train = tuple([0] * 8 + [1] * 8)
        x_test = _toy_batch(2, 3, 2, 0.0) + _toy_batch(2, 3, 2, 1.0)
        fit_result = adapter.fit(
            model_handle=handle,
            x_train=x_train,
            y_train=y_train,
            epochs=1,
            batch_size=4,
        )
        self.assertIsInstance(fit_result, FitResult)
        self.assertEqual(fit_result.epochs_executed, 1)
        self.assertGreater(fit_result.parameter_count, 0)
        predictions = adapter.predict(
            model_handle=fit_result.model_handle, x_test=x_test
        )
        self.assertEqual(len(predictions), len(x_test))
        for label in predictions:
            self.assertIn(label, (0, 1))


class EndToEndThroughExecuteTrainingRunTests(unittest.TestCase):
    def test_dummy_benchmark_with_gru_classifier_runs_end_to_end(self) -> None:
        from parallel_truth_fingerprint.lstm_service.offline_training.training.run import (
            execute_training_run,
        )

        record = execute_training_run(
            benchmark="dummy",
            model="gru-classifier",
            epochs=1,
            batch_size=4,
            learning_rate=1e-2,
            sequence_length=3,
            seed=42,
            extra_hyperparameters={"hidden_units": 4, "num_layers": 1},
        )
        self.assertEqual(record.model_name, "gru-classifier")
        self.assertGreater(record.parameter_count, 0)

    def test_adfa_ld_with_gru_classifier_runs_end_to_end(self) -> None:
        previous = os.environ.get("ADFA_LD_PATH")
        os.environ["ADFA_LD_PATH"] = str(FIXTURE_PATH)
        try:
            from parallel_truth_fingerprint.lstm_service.offline_training.training.run import (
                execute_training_run,
            )

            record = execute_training_run(
                benchmark="adfa-ld",
                model="gru-classifier",
                epochs=1,
                batch_size=2,
                learning_rate=1e-2,
                sequence_length=4,
                seed=42,
                extra_hyperparameters={"hidden_units": 4, "num_layers": 1},
            )
            self.assertEqual(record.dataset_name, "adfa-ld")
            self.assertEqual(record.model_name, "gru-classifier")
            self.assertGreater(record.parameter_count, 0)
            self.assertIsNotNone(record.confusion_matrix)
        finally:
            if previous is None:
                os.environ.pop("ADFA_LD_PATH", None)
            else:
                os.environ["ADFA_LD_PATH"] = previous


if __name__ == "__main__":
    unittest.main()
