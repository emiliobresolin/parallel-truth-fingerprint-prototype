"""Story 7.9: hyperparameter sweep harness tests."""

from __future__ import annotations

import os
import unittest
from pathlib import Path

os.environ.setdefault("KERAS_BACKEND", "torch")

from parallel_truth_fingerprint.lstm_service.offline_training.training.sweep import (  # noqa: E402
    run_sweep,
    summarize_sweep,
)
from parallel_truth_fingerprint.lstm_service.offline_training.registry.training_history import (  # noqa: E402
    list_training_runs,
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


def _tiny_sweep_config() -> dict:
    return {
        "benchmark": "adfa-ld",
        "models": ["lstm-classifier"],
        "epochs": 1,
        "seed": 42,
        "extra_hyperparameters": {"hidden_units": 4, "num_layers": 1},
        "grid": {
            "learning_rate": [1e-2, 1e-3],
            "batch_size": [2],
            "sequence_length": [4, 6],
        },
    }


class SweepEndToEndTests(unittest.TestCase):
    def test_sweep_runs_every_cell_and_persists(self) -> None:
        previous = os.environ.get("ADFA_LD_PATH")
        os.environ["ADFA_LD_PATH"] = str(FIXTURE_PATH)
        try:
            store = _fresh_store()
            results = run_sweep(_tiny_sweep_config(), artifact_store=store)
        finally:
            if previous is None:
                os.environ.pop("ADFA_LD_PATH", None)
            else:
                os.environ["ADFA_LD_PATH"] = previous

        # AC1: 1 model x 2 lr x 1 batch x 2 seq_len = 4 cells.
        self.assertEqual(len(results), 4)
        for record, written in results:
            self.assertEqual(record.dataset_name, "adfa-ld")
            self.assertEqual(record.model_name, "lstm-classifier")
            self.assertEqual(written.run_id, record.run_id)
        listed = list_training_runs(artifact_store=store, benchmark="adfa-ld")
        for record, _ in results:
            self.assertIn(record.run_id, listed)

    def test_summarize_sweep_returns_markdown_table(self) -> None:
        previous = os.environ.get("ADFA_LD_PATH")
        os.environ["ADFA_LD_PATH"] = str(FIXTURE_PATH)
        try:
            store = _fresh_store()
            results = run_sweep(_tiny_sweep_config(), artifact_store=store)
        finally:
            if previous is None:
                os.environ.pop("ADFA_LD_PATH", None)
            else:
                os.environ["ADFA_LD_PATH"] = previous

        report = summarize_sweep([record for record, _ in results])
        self.assertIn("| run_id", report)
        self.assertIn("| macro_f1", report)
        for record, _ in results:
            self.assertIn(record.run_id, report)


class SweepValidationTests(unittest.TestCase):
    def test_missing_grid_axis_raises(self) -> None:
        store = _fresh_store()
        bad_config = {
            "benchmark": "adfa-ld",
            "models": ["lstm-classifier"],
            "epochs": 1,
            "seed": 42,
            "extra_hyperparameters": {},
            "grid": {
                "learning_rate": [1e-3],
                # missing batch_size and sequence_length
            },
        }
        with self.assertRaises(ValueError):
            run_sweep(bad_config, artifact_store=store)

    def test_empty_models_raises(self) -> None:
        store = _fresh_store()
        bad_config = {
            "benchmark": "adfa-ld",
            "models": [],
            "epochs": 1,
            "seed": 42,
            "extra_hyperparameters": {},
            "grid": {
                "learning_rate": [1e-3],
                "batch_size": [2],
                "sequence_length": [4],
            },
        }
        with self.assertRaises(ValueError):
            run_sweep(bad_config, artifact_store=store)


if __name__ == "__main__":
    unittest.main()
