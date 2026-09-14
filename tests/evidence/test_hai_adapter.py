from __future__ import annotations

import tempfile
import unittest
from pathlib import Path

from parallel_truth_fingerprint.evidence.hai_adapter import (
    Hai2305LayoutError,
    inspect_hai_23_05,
    iter_native_observations,
)


class Hai2305AdapterTests(unittest.TestCase):
    def _write_layout(self, root: Path) -> None:
        for index in range(1, 5):
            (root / f"hai-train{index}.csv").write_text("timestamp,Tag_A,Tag_B\n2022-01-01 00:00:01,1.0,2\n2022-01-01 00:00:02,1.5,2.5\n", encoding="utf-8")
        for index in range(1, 3):
            (root / f"hai-test{index}.csv").write_text("timestamp,Tag_A,Tag_B\n2022-01-02 00:00:01,3.0,4\n2022-01-02 00:00:02,3.5,4.5\n", encoding="utf-8")
            (root / f"label-test{index}.csv").write_text("timestamp,label\n2022-01-02 00:00:01,0\n2022-01-02 00:00:02,1\n", encoding="utf-8")

    def test_streaming_native_layout_preserves_tags_and_separates_labels(self) -> None:
        with tempfile.TemporaryDirectory() as directory:
            root = Path(directory)
            self._write_layout(root)
            manifest = inspect_hai_23_05(root)
            rows = list(iter_native_observations(root / "hai-train1.csv"))
        self.assertEqual(manifest.version_id, "HAI-23.05")
        self.assertEqual(manifest.observations[0].columns, ("timestamp", "Tag_A", "Tag_B"))
        self.assertEqual(manifest.labels[0].role, "restricted-evaluation-truth")
        self.assertEqual(rows[0], ("2022-01-01 00:00:01", {"Tag_A": 1.0, "Tag_B": 2.0}))

    def test_misaligned_truth_fails_closed(self) -> None:
        with tempfile.TemporaryDirectory() as directory:
            root = Path(directory)
            self._write_layout(root)
            (root / "label-test2.csv").write_text("timestamp,label\n2022-01-02 00:00:03,0\n", encoding="utf-8")
            with self.assertRaises(Hai2305LayoutError):
                inspect_hai_23_05(root)
