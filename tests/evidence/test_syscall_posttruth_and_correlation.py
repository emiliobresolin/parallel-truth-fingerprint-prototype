from __future__ import annotations
import unittest
from parallel_truth_fingerprint.evidence.syscall_posttruth_evaluation import *
from parallel_truth_fingerprint.evidence.syscall_correlation import *
class Tests(unittest.TestCase):
 def test_evaluator_boundary_and_correlation(self):
  d=lambda c:"sha256:"+c*64
  self.assertFalse(validate_syscall_evaluation(SyscallEvaluationRequest(d("a"),d("b"),d("c"),d("d"),"detector_facing")).allowed)
  self.assertFalse(validate_custom_correlation(physical_run_id=d("a"),syscall_run_id=d("b"),campaign_id=d("c"),correlation_id=d("d"),same_campaign=False).correlated)
if __name__=="__main__":unittest.main()
