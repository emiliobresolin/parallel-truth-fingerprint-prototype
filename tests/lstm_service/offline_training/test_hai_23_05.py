from __future__ import annotations

from pathlib import Path
import tempfile
import unittest

from parallel_truth_fingerprint.lstm_service.offline_training.benchmarks.hai_23_05 import (
    Hai2305Benchmark,
)


class Hai2305BenchmarkTests(unittest.TestCase):
    def test_adapter_preserves_native_features_and_uses_only_published_test_labels(self) -> None:
        with tempfile.TemporaryDirectory() as temporary:
            root = Path(temporary)
            for index in range(1, 5):
                (root / f"hai-train{index}.csv").write_text(
                    "timestamp,TAG_A,TAG_B\n"
                    f"2026-01-0{index} 00:00:01,1,2\n"
                    f"2026-01-0{index} 00:00:02,3,4\n",
                    encoding="utf-8",
                )
            for index in range(1, 3):
                (root / f"hai-test{index}.csv").write_text(
                    "timestamp,TAG_A,TAG_B\n"
                    f"2026-02-0{index} 00:00:01,5,6\n"
                    f"2026-02-0{index} 00:00:02,7,8\n",
                    encoding="utf-8",
                )
                (root / f"label-test{index}.csv").write_text(
                    "timestamp,label\n"
                    f"2026-02-0{index} 00:00:01,0\n"
                    f"2026-02-0{index} 00:00:02,1\n",
                    encoding="utf-8",
                )
            data = Hai2305Benchmark(root_path=root, max_windows_per_class=10).load(
                sequence_length=1, seed=7
            )

        self.assertEqual(data.name, "hai-23.05")
        self.assertEqual(data.label_names, ("Normal", "Attack"))
        self.assertEqual(data.feature_count, 2)
        self.assertEqual(data.provenance["feature_names"], ("TAG_A", "TAG_B"))
        self.assertIn("no compressor or mA conversion", data.provenance["feature_semantics"])
        self.assertGreaterEqual(data.provenance["per_class_counts"]["Attack"], 2)


if __name__ == "__main__":
    unittest.main()
