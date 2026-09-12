from __future__ import annotations
import unittest
from parallel_truth_fingerprint.contracts.syscall_detector_bundle import SyscallDetectorBundle
class BundleTests(unittest.TestCase):
 def test_mutable_component_blocks(self):
  d=lambda c:"sha256:"+c*64
  with self.assertRaises(ValueError):SyscallDetectorBundle("latest",d("a"),d("b"),d("c"),d("d"),d("e"),d("f"),d("0"),d("1"),d("2")).validate()
if __name__=="__main__":unittest.main()
