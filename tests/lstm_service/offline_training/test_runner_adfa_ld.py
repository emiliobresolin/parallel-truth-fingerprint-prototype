"""Story 7.7: orchestrate the first real training run on ADFA-LD."""

from __future__ import annotations

import os
import unittest
from pathlib import Path

# Force the torch backend before any keras import.
os.environ.setdefault("KERAS_BACKEND", "torch")

from parallel_truth_fingerprint.lstm_service.offline_training.training.runner_adfa_ld import (  # noqa: E402
    run_first_adfa_ld_training,
)
from parallel_truth_fingerprint.lstm_service.offline_training.registry.training_history import (  # noqa: E402
    list_training_runs,
    read_training_run,
)
from parallel_truth_fingerprint.persistence import (  # noqa: E402
    MinioArtifactStore,
    MinioStoreConfig,
)
from tests.persistence.test_service import FakeMinioClient  # noqa: E402


FIXTURE_PATH = (
    Path(__file__).resolve().parent / "fixtures" / "adfa_ld_fixture"
)


def _fresh_store(bucket: str = "fingerprint-training-history") -> MinioArtifactStore:
    return MinioArtifactStore(
        MinioStoreConfig(
            endpoint="localhost:0",
            access_key="x",
            secret_key="y",
            bucket=bucket,
            secure=False,
        ),
        client=FakeMinioClient(),
    )


class RunnerAdfaLdTests(unittest.TestCase):
    def test_end_to_end_run_persists_and_is_listable(self) -> None:
        store = _fresh_store()
        record, written = run_first_adfa_ld_training(
            adfa_ld_root=FIXTURE_PATH,
            artifact_store=store,
            epochs=1,
            batch_size=2,
            learning_rate=1e-2,
            sequence_length=4,
            seed=42,
            extra_hyperparameters={"hidden_units": 4, "num_layers": 1},
        )
        self.assertEqual(record.dataset_name, "adfa-ld")
        self.assertEqual(record.model_name, "lstm-classifier")
        self.assertEqual(record.seed, 42)
        self.assertIsNotNone(record.split_record)
        self.assertEqual(record.split_record.seed, 42)
        # Confusion matrix is 6x6 (the full ADFA-LD label space), even if
        # some classes happen to be absent from the test split.
        self.assertIsNotNone(record.confusion_matrix)
        self.assertEqual(len(record.confusion_matrix), 6)
        self.assertTrue(all(len(row) == 6 for row in record.confusion_matrix))

        # Persistence side: written under fingerprint-training-history/.
        self.assertTrue(written.run_object_key.endswith(f"{record.run_id}.json"))
        listed = list_training_runs(artifact_store=store, benchmark="adfa-ld")
        self.assertIn(record.run_id, listed)
        restored = read_training_run(record.run_id, artifact_store=store)
        self.assertEqual(restored.dataset_name, "adfa-ld")
        self.assertEqual(restored.metrics, record.metrics)


if __name__ == "__main__":
    unittest.main()
