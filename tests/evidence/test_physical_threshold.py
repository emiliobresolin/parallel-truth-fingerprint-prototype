from __future__ import annotations
import unittest
from parallel_truth_fingerprint.contracts.physical_threshold import PhysicalThreshold
from parallel_truth_fingerprint.evidence.physical_threshold import load_frozen_threshold
class ThresholdTests(unittest.TestCase):
 def test_forged_threshold_cannot_load(self):
  d=lambda c:"sha256:"+c*64
  x=PhysicalThreshold(d("a"),d("b"),d("c"),d("d"),(d("e"),),d("f"),"higher_anomalous","SENTINEL","one",d("0"),d("1"),d("2"),"2026-01-01T00:00:00Z","sha256:"+"3"*64)
  self.assertFalse(load_frozen_threshold(x,candidate_id=d("a"),preprocessing_id=d("b"),feature_schema_id=d("c")).loaded)
if __name__ == "__main__": unittest.main()
