from __future__ import annotations
import unittest
from parallel_truth_fingerprint.dashboard.frozen_evidence_projection import project_frozen_evidence
class ProjectionTests(unittest.TestCase):
 def test_projection_refuses_control_content(self):
  with self.assertRaises(ValueError):project_frozen_evidence(package_receipt_id="sha256:"+"a"*64,claims=({"control":"x"},),limitations=())
if __name__=="__main__":unittest.main()
