from __future__ import annotations
import unittest
from parallel_truth_fingerprint.evidence.benchmark_lineage import admit_benchmark_track
class BenchTests(unittest.TestCase):
 def test_fixture_cannot_substitute_official_track(self):
  d=lambda c:"sha256:"+c*64
  self.assertEqual("blocked",admit_benchmark_track(dataset_family="adfa_ld",source_manifest_id=d("a"),inventory_id=d("b"),official_source=True,fixture_only=True).status)
if __name__=="__main__":unittest.main()
