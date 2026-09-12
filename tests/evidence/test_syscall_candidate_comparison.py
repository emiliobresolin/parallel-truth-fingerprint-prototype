from __future__ import annotations
import unittest
from parallel_truth_fingerprint.evidence.syscall_candidate_comparison import SyscallCandidatePlan,validate_syscall_candidate_plan
class CandidateTests(unittest.TestCase):
 def test_test_derived_candidate_is_blocked(self):
  d=lambda c:"sha256:"+c*64
  x=SyscallCandidatePlan(d("a"),d("b"),d("c"),d("d"),("normal_model","test_leak"),d("e"))
  self.assertFalse(validate_syscall_candidate_plan(x).allowed)
if __name__=="__main__": unittest.main()
