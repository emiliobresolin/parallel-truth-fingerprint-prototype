"""Story 7.11: orchestrate the first real training run on LID-DS 2021."""

from __future__ import annotations

import os
import unittest
from pathlib import Path

os.environ.setdefault("KERAS_BACKEND", "torch")

from parallel_truth_fingerprint.lstm_service.offline_training.training.runner_lid_ds_2021 import (  # noqa: E402
    run_first_lid_ds_2021_training,
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
    Path(__file__).resolve().parent / "fixtures" / "lid_ds_2021_fixture"
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


class RunnerLidDs2021Tests(unittest.TestCase):
    def test_end_to_end_run_persists_and_is_listable(self) -> None:
        store = _fresh_store()
        record, written = run_first_lid_ds_2021_training(
            lid_ds_root=FIXTURE_PATH,
            artifact_store=store,
            epochs=1,
            batch_size=2,
            learning_rate=1e-2,
            sequence_length=4,
            seed=42,
            extra_hyperparameters={"hidden_units": 4, "num_layers": 1},
        )
        self.assertEqual(record.dataset_name, "lid-ds-2021")
        self.assertEqual(record.model_name, "lstm-classifier")
        self.assertEqual(record.seed, 42)
        # 1 Normal + 2 scenario-attack classes = 3 columns in the matrix.
        self.assertIsNotNone(record.confusion_matrix)
        self.assertEqual(len(record.confusion_matrix), 3)
        self.assertTrue(all(len(row) == 3 for row in record.confusion_matrix))

        self.assertTrue(written.run_object_key.endswith(f"{record.run_id}.json"))
        listed = list_training_runs(
            artifact_store=store, benchmark="lid-ds-2021"
        )
        self.assertIn(record.run_id, listed)
        restored = read_training_run(record.run_id, artifact_store=store)
        self.assertEqual(restored.dataset_name, "lid-ds-2021")
        self.assertEqual(restored.metrics, record.metrics)


if __name__ == "__main__":
    unittest.main()
