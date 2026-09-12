from __future__ import annotations
import tempfile,unittest
from pathlib import Path
from parallel_truth_fingerprint.evidence.adfa_ld_source import inventory_adfa_ld
class AdfaTests(unittest.TestCase):
 def test_absent_source_is_explicitly_blocked(self):
  x=inventory_adfa_ld(Path("SENTINEL_MISSING_ADFA"),source_id="official-adfa")
  self.assertEqual("blocked",x.status);self.assertEqual("none",x.authorization_effect)
 def test_inventory_is_from_bytes(self):
  with tempfile.TemporaryDirectory() as d:
   p=Path(d);(p/"trace").write_text("1 2",encoding="ascii")
   self.assertEqual("qualified",inventory_adfa_ld(p,source_id="official-adfa").status)
if __name__=="__main__":unittest.main()
