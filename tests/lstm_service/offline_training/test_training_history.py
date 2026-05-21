"""Story 7.3: training history persistence via MinIO artifact store."""

from __future__ import annotations

import unittest

from parallel_truth_fingerprint.lstm_service.offline_training.registry.training_history import (
    HISTORY_PREFIX,
    deserialize_training_run,
    list_training_runs,
    read_training_run,
    record_training_run_to_artifact_store,
    serialize_training_run,
    write_training_run,
)
from parallel_truth_fingerprint.lstm_service.offline_training.training.run import (
    execute_training_run,
)
from parallel_truth_fingerprint.persistence import (
    MinioArtifactStore,
    MinioStoreConfig,
)
from tests.persistence.test_service import FakeMinioClient


def _make_store(bucket: str = "fingerprint-training-history") -> MinioArtifactStore:
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


class SerializationRoundTripTests(unittest.TestCase):
    def test_round_trip_preserves_record_fields(self) -> None:
        original = execute_training_run(
            benchmark="dummy",
            model="dummy",
            epochs=2,
            batch_size=4,
            learning_rate=0.01,
            sequence_length=3,
            seed=21,
        )
        payload = serialize_training_run(original)
        self.assertIsInstance(payload, dict)
        for key in (
            "run_id",
            "created_at",
            "dataset_name",
            "model_name",
            "seed",
            "sequence_length",
            "epochs_planned",
            "epochs_executed",
            "hyperparameters",
            "metrics",
            "per_class_metrics",
            "split_record",
            "parameter_count",
            "per_epoch_loss",
        ):
            self.assertIn(key, payload)

        restored = deserialize_training_run(payload)
        self.assertEqual(restored.run_id, original.run_id)
        self.assertEqual(restored.dataset_name, original.dataset_name)
        self.assertEqual(restored.model_name, original.model_name)
        self.assertEqual(restored.seed, original.seed)
        self.assertEqual(restored.epochs_planned, original.epochs_planned)
        self.assertEqual(restored.epochs_executed, original.epochs_executed)
        self.assertEqual(restored.hyperparameters, original.hyperparameters)
        self.assertEqual(restored.metrics, original.metrics)
        self.assertEqual(restored.per_class_metrics, original.per_class_metrics)
        self.assertEqual(restored.parameter_count, original.parameter_count)
        self.assertEqual(restored.per_epoch_loss, original.per_epoch_loss)
        self.assertEqual(restored.split_record, original.split_record)
        self.assertEqual(restored.confusion_matrix, original.confusion_matrix)


class WriteListReadTests(unittest.TestCase):
    def test_write_then_list_then_read_round_trip(self) -> None:
        store = _make_store()
        record = execute_training_run(
            benchmark="dummy",
            model="dummy",
            epochs=1,
            batch_size=2,
            learning_rate=0.01,
            sequence_length=3,
            seed=33,
        )
        written = write_training_run(record, artifact_store=store)

        self.assertTrue(
            written.run_object_key.startswith(f"{HISTORY_PREFIX}runs/")
        )
        self.assertTrue(written.run_object_key.endswith(f"/{record.run_id}.json"))
        self.assertTrue(
            written.confusion_object_key.endswith(
                f"/{record.run_id}.confusion.json"
            )
        )
        self.assertTrue(
            written.index_object_key.startswith(
                f"{HISTORY_PREFIX}index/by-benchmark/"
            )
        )

        # AC3: index returns the run_id for the dataset.
        listed = list_training_runs(artifact_store=store, benchmark="dummy")
        self.assertIn(record.run_id, listed)

        # AC1: read_training_run reconstitutes the record.
        restored = read_training_run(record.run_id, artifact_store=store)
        self.assertEqual(restored, deserialize_training_run(serialize_training_run(record)))

    def test_index_is_idempotent_on_repeated_writes(self) -> None:
        store = _make_store()
        record = execute_training_run(
            benchmark="dummy",
            model="dummy",
            epochs=1,
            batch_size=2,
            learning_rate=0.01,
            sequence_length=3,
            seed=33,
        )
        write_training_run(record, artifact_store=store)
        write_training_run(record, artifact_store=store)
        listed = list_training_runs(artifact_store=store, benchmark="dummy")
        self.assertEqual(listed.count(record.run_id), 1)

    def test_list_across_two_benchmarks(self) -> None:
        store = _make_store()
        record_a = execute_training_run(
            benchmark="dummy",
            model="dummy",
            epochs=1,
            batch_size=2,
            learning_rate=0.01,
            sequence_length=3,
            seed=10,
        )
        # Pretend the same record came from a different benchmark by
        # rewriting the in-memory field. Story 7.6/7.10 will exercise this
        # for real with ADFA-LD / LID-DS-2021.
        from dataclasses import replace
        record_b = replace(
            record_a,
            run_id=record_a.run_id + "-alt",
            dataset_name="other-benchmark",
        )
        write_training_run(record_a, artifact_store=store)
        write_training_run(record_b, artifact_store=store)

        dummy_runs = list_training_runs(artifact_store=store, benchmark="dummy")
        other_runs = list_training_runs(
            artifact_store=store, benchmark="other-benchmark"
        )
        self.assertEqual(dummy_runs, (record_a.run_id,))
        self.assertEqual(other_runs, (record_b.run_id,))

    def test_one_shot_helper_records_training_run(self) -> None:
        store = _make_store()
        record = execute_training_run(
            benchmark="dummy",
            model="dummy",
            epochs=1,
            batch_size=2,
            learning_rate=0.01,
            sequence_length=3,
            seed=55,
        )
        written = record_training_run_to_artifact_store(record, store)
        self.assertEqual(written.run_id, record.run_id)
        listed = list_training_runs(artifact_store=store, benchmark="dummy")
        self.assertIn(record.run_id, listed)


if __name__ == "__main__":
    unittest.main()
