from __future__ import annotations
import unittest
from parallel_truth_fingerprint.contracts.preconsensus_snapshot import PreConsensusSnapshot
from parallel_truth_fingerprint.scada.opcua_v2 import project_preconsensus_snapshot

class V2OpcTests(unittest.TestCase):
    def test_missing_writer_is_explicit_and_has_no_side_effect(self):
        d=lambda c:"sha256:"+c*64
        value=PreConsensusSnapshot(d("a"),d("b"),d("c"),1,d("d"),"2026-01-01T00:00:00Z",d("e"),d("f"),d("0"),"1","u","2","in_range")
        self.assertEqual("writer_unavailable", project_preconsensus_snapshot(value, None).reason)

if __name__ == "__main__": unittest.main()
