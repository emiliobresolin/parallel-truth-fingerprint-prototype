"""Story 8.2: live-runtime classifier inference helper."""

from __future__ import annotations

import os
import unittest
from pathlib import Path

os.environ.setdefault("KERAS_BACKEND", "torch")

from parallel_truth_fingerprint.lstm_service.offline_training.registry.promotion import (  # noqa: E402
    promote_training_run,
)
from parallel_truth_fingerprint.lstm_service.offline_training.training.runner_adfa_ld import (  # noqa: E402
    run_first_adfa_ld_training,
)
from parallel_truth_fingerprint.lstm_service.online_inference import (  # noqa: E402
    InferenceResult,
    OnlineLstmInferencer,
)
from parallel_truth_fingerprint.persistence import (  # noqa: E402
    MinioArtifactStore,
    MinioStoreConfig,
)
from tests.persistence.test_service import FakeMinioClient  # noqa: E402


ADFA_FIXTURE = (
    Path(__file__).resolve().parent / "fixtures" / "adfa_ld_fixture"
)


def _fresh_store() -> MinioArtifactStore:
    return MinioArtifactStore(
        MinioStoreConfig(
            endpoint="localhost:0",
            access_key="x",
            secret_key="y",
            bucket="fingerprint-training-history",
            secure=False,
        ),
        client=FakeMinioClient(),
    )


class OnlineInferencerTests(unittest.TestCase):
    def test_load_raises_when_nothing_promoted(self) -> None:
        store = _fresh_store()
        with self.assertRaises(RuntimeError) as ctx:
            OnlineLstmInferencer.load(artifact_store=store)
        self.assertIn("promote_lstm_run", str(ctx.exception))

    def _seed_train_promote(self, store):
        record, _ = run_first_adfa_ld_training(
            adfa_ld_root=ADFA_FIXTURE,
            artifact_store=store,
            epochs=1,
            batch_size=2,
            learning_rate=1e-2,
            sequence_length=4,
            seed=42,
            extra_hyperparameters={"hidden_units": 4, "num_layers": 1},
        )
        promote_training_run(record.run_id, artifact_store=store)
        return record

    def _load_with_fixture_env(self, store):
        # Mirror production: the live runtime has the benchmark env var
        # configured at start-up. The runner helper restored the env var
        # on exit, so we set it again here just for the .load() call.
        previous = os.environ.get("ADFA_LD_PATH")
        os.environ["ADFA_LD_PATH"] = str(ADFA_FIXTURE)
        try:
            return OnlineLstmInferencer.load(artifact_store=store)
        finally:
            if previous is None:
                os.environ.pop("ADFA_LD_PATH", None)
            else:
                os.environ["ADFA_LD_PATH"] = previous

    def test_predict_after_promotion_returns_valid_class(self) -> None:
        store = _fresh_store()
        record = self._seed_train_promote(store)
        inferencer = self._load_with_fixture_env(store)
        window = ((0.1,), (0.2,), (0.15,), (0.18,))  # 4 timesteps x 1 feature
        result = inferencer.predict_sequence(window)
        self.assertIsInstance(result, InferenceResult)
        self.assertEqual(result.promoted_run_id, record.run_id)
        self.assertIn(result.predicted_class_name, record.label_names)
        self.assertEqual(len(result.class_probabilities), len(record.label_names))
        self.assertAlmostEqual(sum(result.class_probabilities), 1.0, places=4)

    def test_predict_rejects_wrong_window_shape(self) -> None:
        store = _fresh_store()
        self._seed_train_promote(store)
        inferencer = self._load_with_fixture_env(store)
        with self.assertRaises(ValueError):
            # Wrong sequence_length (3 instead of 4).
            inferencer.predict_sequence(((0.1,), (0.2,), (0.3,)))
        with self.assertRaises(ValueError):
            # Wrong feature_count (2 instead of 1).
            inferencer.predict_sequence(
                ((0.1, 0.2), (0.2, 0.3), (0.3, 0.4), (0.4, 0.5))
            )


if __name__ == "__main__":
    unittest.main()
