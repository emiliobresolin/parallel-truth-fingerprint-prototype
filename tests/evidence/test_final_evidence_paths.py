from __future__ import annotations
import unittest
from parallel_truth_fingerprint.evidence.benchmark_evaluation import *
from parallel_truth_fingerprint.evidence.frozen_fusion import *
from parallel_truth_fingerprint.evidence.evidence_package import *
class FinalPaths(unittest.TestCase):
 def test_truth_and_fusion_boundaries(self):
  d=lambda c:"sha256:"+c*64
  b=BenchmarkEvaluation("adfa_ld",d("a"),d("b"),d("c"),d("d"),d("e"),None,d("f"),"complete")
  self.assertFalse(validate_benchmark_publication(b).allowed)
  self.assertFalse(validate_fusion_plan(FrozenFusionPlan(d("a"),d("b"),d("c"),d("d"),d("e"),True))[0])
  self.assertFalse(reconstruct_evidence_package(claims=(),required_claim_ids=("claim",),final_receipt_id=d("f")).accepted)
if __name__=="__main__":unittest.main()
