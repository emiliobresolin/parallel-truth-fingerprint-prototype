from __future__ import annotations
import unittest
from parallel_truth_fingerprint.contracts.preconsensus_snapshot import PreConsensusSnapshot
from parallel_truth_fingerprint.evidence.preconsensus_snapshot import guard_snapshot

class SnapshotTests(unittest.TestCase):
    def test_snapshot_is_content_addressed_and_guard_never_replaces_conflict(self):
        d = lambda c: "sha256:" + c * 64
        item = PreConsensusSnapshot(d("a"), d("b"), d("c"), 1, d("d"), "2026-01-01T00:00:00Z", d("e"), d("f"), d("0"), "1", "sentinel", "2", "in_range")
        item = PreConsensusSnapshot(**{**item.__dict__, "snapshot_content_id": item.content_id()})
        self.assertTrue(guard_snapshot(item, known={}).accepted)
        self.assertEqual("idempotent_duplicate", guard_snapshot(item, known={(item.run_id,item.cycle_id,1): item.content_id()}).classification)

if __name__ == "__main__": unittest.main()
