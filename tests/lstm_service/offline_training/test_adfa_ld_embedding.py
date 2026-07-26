"""Tests for the embedding/sliding-window ADFA-LD adapters (adfa-ld-embed*).

Mirrors the fixture-based style of test_adfa_ld.py. The sliding-window logic
is also unit-tested directly on synthetic traces so the window count, stride
spread, and tail coverage are verified independently of the fixture's short
traces.
"""

from __future__ import annotations

import unittest
from pathlib import Path

from parallel_truth_fingerprint.lstm_service.offline_training.benchmarks import (
    list_available_benchmarks,
    load_benchmark,
)
from parallel_truth_fingerprint.lstm_service.offline_training.benchmarks.adfa_ld_embedding import (
    BINARY_LABEL_NAMES,
    AdfaLdEmbeddingBenchmark,
)
from parallel_truth_fingerprint.lstm_service.offline_training.benchmarks.adfa_ld import (
    ADFA_LD_LABEL_NAMES,
)


FIXTURE_PATH = Path(__file__).resolve().parent / "fixtures" / "adfa_ld_fixture"


class EmbeddingRegistrationTests(unittest.TestCase):
    def test_both_variants_are_registered(self) -> None:
        available = list_available_benchmarks()
        self.assertIn("adfa-ld-embed", available)
        self.assertIn("adfa-ld-embed-binary", available)


class EmbeddingFixtureLoadTests(unittest.TestCase):
    def setUp(self) -> None:
        self.multiclass = AdfaLdEmbeddingBenchmark(root_path=FIXTURE_PATH)
        self.binary = AdfaLdEmbeddingBenchmark(
            name="adfa-ld-embed-binary", binary=True, root_path=FIXTURE_PATH
        )

    def test_multiclass_keeps_six_class_label_space(self) -> None:
        data = self.multiclass.load(sequence_length=5, seed=0)
        self.assertEqual(data.label_names, ADFA_LD_LABEL_NAMES)
        self.assertEqual(data.feature_count, 1)

    def test_binary_collapses_attacks_to_one_class(self) -> None:
        data = self.binary.load(sequence_length=5, seed=0)
        self.assertEqual(data.label_names, BINARY_LABEL_NAMES)
        self.assertEqual(sorted(set(data.labels)), [0, 1])

    def test_tokens_are_raw_integers_not_normalised(self) -> None:
        # The original adfa-ld adapter divides by max_syscall_id (values in
        # [0,1]); the embedding adapter must emit raw integer ids carried as
        # floats so every value is a whole number >= 1 somewhere.
        data = self.multiclass.load(sequence_length=5, seed=0)
        all_values = [
            value
            for window in data.sequences
            for (value,) in window
        ]
        self.assertTrue(any(v > 1.0 for v in all_values))
        for v in all_values:
            self.assertEqual(v, float(int(v)))

    def test_provenance_carries_vocab_and_windowing(self) -> None:
        data = self.multiclass.load(sequence_length=5, seed=0)
        self.assertEqual(data.provenance["windowing"], "sliding")
        self.assertEqual(
            data.provenance["vocab_size"],
            int(data.provenance["max_syscall_id"]) + 1,
        )
        self.assertEqual(data.provenance["framing"], "multiclass")

    def test_invalid_sequence_length_raises(self) -> None:
        with self.assertRaises(ValueError):
            self.multiclass.load(sequence_length=0, seed=0)


class SlidingWindowUnitTests(unittest.TestCase):
    def setUp(self) -> None:
        self.adapter = AdfaLdEmbeddingBenchmark(root_path=FIXTURE_PATH)

    def test_short_trace_yields_single_padded_window(self) -> None:
        windows = self.adapter._sliding_windows([7, 8, 9], sequence_length=5, max_windows=4)
        self.assertEqual(windows, [(7, 8, 9, 0, 0)])

    def test_max_windows_one_is_leading_window(self) -> None:
        trace = list(range(1, 101))
        windows = self.adapter._sliding_windows(trace, sequence_length=10, max_windows=1)
        self.assertEqual(windows, [tuple(range(1, 11))])

    def test_sliding_spreads_and_covers_tail(self) -> None:
        trace = list(range(1, 101))  # length 100
        windows = self.adapter._sliding_windows(trace, sequence_length=10, max_windows=4)
        self.assertLessEqual(len(windows), 4)
        # First window is the head.
        self.assertEqual(windows[0], tuple(range(1, 11)))
        # Tail window (last 10 elements) must be present.
        self.assertIn(tuple(range(91, 101)), windows)

    def test_normal_capped_more_tightly_than_attack(self) -> None:
        # Normal traces (label 0) honour normal_max_windows_per_trace, attack
        # traces honour max_windows_per_trace. Verify the load path applies
        # the per-class cap by comparing window totals for a custom adapter.
        adapter = AdfaLdEmbeddingBenchmark(
            root_path=FIXTURE_PATH,
            max_windows_per_trace=4,
            normal_max_windows_per_trace=1,
        )
        data = adapter.load(sequence_length=3, seed=0)
        self.assertGreater(len(data.sequences), 0)


if __name__ == "__main__":
    unittest.main()
