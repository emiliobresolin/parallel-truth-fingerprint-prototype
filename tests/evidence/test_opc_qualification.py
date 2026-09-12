from __future__ import annotations
import unittest
from parallel_truth_fingerprint.evidence.opc_qualification import qualify_opc_evidence
class GateTests(unittest.TestCase):
    def test_missing_closure_blocks_without_authorizing(self):
        result=qualify_opc_evidence(comparison_results=(), causal_paths_demonstrated=False, publication_receipt_id=None)
        self.assertFalse(result.qualified); self.assertEqual("none", result.authorization_effect)
if __name__ == "__main__": unittest.main()
