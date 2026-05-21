"""Story 8.1: promotion of a TrainingRunRecord to live-runtime status."""

from __future__ import annotations

import os
import unittest
from pathlib import Path

os.environ.setdefault("KERAS_BACKEND", "torch")

from parallel_truth_fingerprint.lstm_service.offline_training.registry.promotion import (  # noqa: E402
    PromotedRun,
    promote_training_run,
    read_promoted_run,
)
from parallel_truth_fingerprint.lstm_service.offline_training.training.runner_adfa_ld import (  # noqa: E402
    run_first_adfa_ld_training,
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


def _seed_one_run(
    store: MinioArtifactStore, *, seed: int = 42
):
    record, written = run_first_adfa_ld_training(
        adfa_ld_root=ADFA_FIXTURE,
        artifact_store=store,
        epochs=1,
        batch_size=2,
        learning_rate=1e-2,
        sequence_length=4,
        seed=seed,
        extra_hyperparameters={"hidden_units": 4, "num_layers": 1},
    )
    return record


class PromotionTests(unittest.TestCase):
    def test_read_returns_none_when_nothing_promoted(self) -> None:
        store = _fresh_store()
        self.assertIsNone(read_promoted_run(artifact_store=store))

    def test_promote_records_run_id_and_metadata(self) -> None:
        store = _fresh_store()
        record = _seed_one_run(store)
        promoted = promote_training_run(
            record.run_id, artifact_store=store
        )
        self.assertIsInstance(promoted, PromotedRun)
        self.assertEqual(promoted.run_id, record.run_id)
        self.assertEqual(promoted.dataset_name, "adfa-ld")
        self.assertEqual(promoted.model_name, "lstm-classifier")
        self.assertIsNone(promoted.previous_run_id)
        # Round-trip via read_promoted_run.
        round_trip = read_promoted_run(artifact_store=store)
        self.assertEqual(round_trip, promoted)

    def test_re_promote_same_id_is_no_op_keeps_previous_null(self) -> None:
        store = _fresh_store()
        record = _seed_one_run(store)
        first = promote_training_run(record.run_id, artifact_store=store)
        second = promote_training_run(record.run_id, artifact_store=store)
        self.assertEqual(first, second)
        self.assertIsNone(second.previous_run_id)

    def test_promote_replaces_pointer_and_records_previous(self) -> None:
        store = _fresh_store()
        first_record = _seed_one_run(store, seed=42)
        second_record = _seed_one_run(store, seed=7)
        promote_training_run(first_record.run_id, artifact_store=store)
        promoted = promote_training_run(
            second_record.run_id, artifact_store=store
        )
        self.assertEqual(promoted.run_id, second_record.run_id)
        self.assertEqual(promoted.previous_run_id, first_record.run_id)

    def test_promote_unknown_run_id_raises(self) -> None:
        store = _fresh_store()
        with self.assertRaises(ValueError) as ctx:
            promote_training_run("run-does-not-exist", artifact_store=store)
        self.assertIn("fingerprint-training-history", str(ctx.exception))


if __name__ == "__main__":
    unittest.main()
