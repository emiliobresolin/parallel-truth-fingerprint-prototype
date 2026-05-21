"""Story 7.2 tests for the stratified 80/20 train/test split."""

from __future__ import annotations

import unittest
from collections import Counter

from parallel_truth_fingerprint.lstm_service.offline_training.splits import (
    SplitRecord,
    stratified_train_test_split,
)


def _toy_sequences(count: int, value: float = 0.0) -> tuple[tuple[tuple[float, ...], ...], ...]:
    """Build `count` toy 2-step 1-feature sequences, all carrying `value`."""
    return tuple(((value,), (value,)) for _ in range(count))


class StratifiedSplitTests(unittest.TestCase):
    def test_balanced_two_class_80_20(self) -> None:
        # 10 samples per class -> 80% train (8) + 20% test (2) per class.
        seq_a = _toy_sequences(10, 0.0)
        seq_b = _toy_sequences(10, 1.0)
        sequences = seq_a + seq_b
        labels = tuple([0] * 10 + [1] * 10)

        x_train, y_train, x_test, y_test, record = stratified_train_test_split(
            sequences, labels, train_ratio=0.8, seed=42
        )

        self.assertEqual(len(y_train), 16)
        self.assertEqual(len(y_test), 4)
        self.assertEqual(Counter(y_train), Counter({0: 8, 1: 8}))
        self.assertEqual(Counter(y_test), Counter({0: 2, 1: 2}))
        self.assertEqual(len(x_train), len(y_train))
        self.assertEqual(len(x_test), len(y_test))
        self.assertIsInstance(record, SplitRecord)
        self.assertEqual(record.seed, 42)
        self.assertEqual(record.train_ratio, 0.8)
        self.assertEqual(record.total_samples, 20)
        self.assertEqual(record.train_samples, 16)
        self.assertEqual(record.test_samples, 4)
        self.assertEqual(record.per_class_counts_train[0], 8)
        self.assertEqual(record.per_class_counts_train[1], 8)
        self.assertEqual(record.per_class_counts_test[0], 2)
        self.assertEqual(record.per_class_counts_test[1], 2)

    def test_imbalanced_three_class_preserves_proportions(self) -> None:
        # 20 / 10 / 5 -> 80% train: 16 / 8 / 4 ; 20% test: 4 / 2 / 1.
        sequences = (
            _toy_sequences(20, 0.0)
            + _toy_sequences(10, 1.0)
            + _toy_sequences(5, 2.0)
        )
        labels = tuple([0] * 20 + [1] * 10 + [2] * 5)

        _, y_train, _, y_test, record = stratified_train_test_split(
            sequences, labels, train_ratio=0.8, seed=7
        )

        self.assertEqual(Counter(y_train), Counter({0: 16, 1: 8, 2: 4}))
        self.assertEqual(Counter(y_test), Counter({0: 4, 1: 2, 2: 1}))
        self.assertEqual(record.total_samples, 35)
        self.assertEqual(record.train_samples, 28)
        self.assertEqual(record.test_samples, 7)

    def test_same_seed_is_deterministic(self) -> None:
        sequences = _toy_sequences(20, 0.0) + _toy_sequences(20, 1.0)
        labels = tuple([0] * 20 + [1] * 20)

        x_train_1, y_train_1, x_test_1, y_test_1, record_1 = (
            stratified_train_test_split(sequences, labels, seed=99)
        )
        x_train_2, y_train_2, x_test_2, y_test_2, record_2 = (
            stratified_train_test_split(sequences, labels, seed=99)
        )

        self.assertEqual(y_train_1, y_train_2)
        self.assertEqual(y_test_1, y_test_2)
        self.assertEqual(x_train_1, x_train_2)
        self.assertEqual(x_test_1, x_test_2)
        self.assertEqual(record_1, record_2)

    def test_different_seeds_produce_different_orderings(self) -> None:
        sequences = _toy_sequences(20, 0.0) + _toy_sequences(20, 1.0)
        labels = tuple([0] * 20 + [1] * 20)

        _, y_train_a, _, y_test_a, _ = stratified_train_test_split(
            sequences, labels, seed=1
        )
        _, y_train_b, _, y_test_b, _ = stratified_train_test_split(
            sequences, labels, seed=2
        )

        # Class proportions are identical, but the orderings differ.
        self.assertEqual(Counter(y_train_a), Counter(y_train_b))
        self.assertEqual(Counter(y_test_a), Counter(y_test_b))
        # Probability of identical ordering across 16-element shuffles is
        # vanishing; if this ever fires we want to know.
        self.assertTrue(
            y_train_a != y_train_b or y_test_a != y_test_b,
            "Two different seeds produced identical orderings.",
        )

    def test_rejects_empty_inputs(self) -> None:
        with self.assertRaises(ValueError):
            stratified_train_test_split((), (), seed=0)

    def test_rejects_class_with_fewer_than_two_samples(self) -> None:
        sequences = _toy_sequences(5, 0.0) + _toy_sequences(1, 1.0)
        labels = tuple([0] * 5 + [1])
        with self.assertRaises(ValueError):
            stratified_train_test_split(sequences, labels, seed=0)

    def test_rejects_invalid_train_ratio(self) -> None:
        sequences = _toy_sequences(10, 0.0) + _toy_sequences(10, 1.0)
        labels = tuple([0] * 10 + [1] * 10)
        with self.assertRaises(ValueError):
            stratified_train_test_split(sequences, labels, train_ratio=0.0, seed=0)
        with self.assertRaises(ValueError):
            stratified_train_test_split(sequences, labels, train_ratio=1.0, seed=0)


class TrainingRunUsesStratifiedSplitTests(unittest.TestCase):
    def test_execute_training_run_records_split(self) -> None:
        from parallel_truth_fingerprint.lstm_service.offline_training.training.run import (
            execute_training_run,
        )

        record = execute_training_run(
            benchmark="dummy",
            model="dummy",
            epochs=1,
            batch_size=2,
            learning_rate=0.01,
            sequence_length=3,
            seed=11,
        )
        # AC6: run record must expose the split_record from Story 7.2.
        self.assertIsNotNone(record.split_record)
        self.assertEqual(record.split_record.seed, 11)
        # Dummy benchmark has 16 + 16 samples per class; 80/20 -> 26/6.
        self.assertEqual(record.split_record.total_samples, 32)
        self.assertEqual(record.split_record.train_samples, 26)
        self.assertEqual(record.split_record.test_samples, 6)


if __name__ == "__main__":
    unittest.main()
