from __future__ import annotations
import unittest
from parallel_truth_fingerprint.evidence.lid_ds_scope import resolve_lid_ds_scope
from parallel_truth_fingerprint.evidence.hai_adapter import admit_hai_adapter
from parallel_truth_fingerprint.evidence.custom_campaign import verify_campaign
class CrossTrackTests(unittest.TestCase):
 def test_all_tracks_fail_closed_without_immutable_closure(self):
  self.assertEqual("blocked",resolve_lid_ds_scope(authorization_id=None,official_source_id=None,environment_id=None).status)
  self.assertFalse(admit_hai_adapter(source_manifest_id="x",adapter_code_id="x",layout_hash="x",requested_version_id="x").admitted)
  self.assertFalse(verify_campaign(campaign_id="x",physical_authorization_id="x",syscall_authorization_id="x",correlation_policy_id="x").ready)
if __name__=="__main__":unittest.main()
