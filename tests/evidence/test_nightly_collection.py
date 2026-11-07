"""Checks for unattended export validation and infrastructure isolation."""
import hashlib
import importlib.util
import json
from pathlib import Path
import tempfile
import unittest
from datetime import datetime

SCRIPT = Path(__file__).resolve().parents[2] / 'scripts/run_nightly_collection.py'
SPEC = importlib.util.spec_from_file_location('nightly_collection', SCRIPT)
nightly = importlib.util.module_from_spec(SPEC)
SPEC.loader.exec_module(nightly)


class NightlyCollectionTests(unittest.TestCase):
    def test_stop_at_next_morning_and_same_day(self):
        self.assertEqual(nightly.next_local_stop('06:00', datetime(2026, 10, 26, 19)), datetime(2026, 10, 27, 6))
        self.assertEqual(nightly.next_local_stop('06:00', datetime(2026, 10, 27, 2)), datetime(2026, 10, 27, 6))
        with self.assertRaises(ValueError):
            nightly.next_local_stop('25:00')

    def fixture(self, root):
        (root / 'dataset').mkdir()
        (root / 'edge-syscalls.1').write_bytes(b'1.0 read(0)\n')
        row = {'campaign_id': 'test-run', 'round_id': 'round-1', 'syscall_tokens': ['read']}
        (root / 'dataset/current-syscall-windows.jsonl').write_text(json.dumps(row) + '\n')
        manifest = {'row_count': 1, 'syscall_trace_sha256': {
            'edge-syscalls.1': 'sha256:' + hashlib.sha256(b'1.0 read(0)\n').hexdigest()}}
        (root / 'dataset/manifest.json').write_text(json.dumps(manifest))
        return row

    def test_valid_export_and_tampered_trace(self):
        with tempfile.TemporaryDirectory() as temporary:
            root = Path(temporary)
            row = self.fixture(root)
            self.assertEqual(nightly.verify_export(root, 'test-run'), [row])
            (root / 'edge-syscalls.1').write_bytes(b'changed')
            with self.assertRaisesRegex(ValueError, 'hash mismatch'):
                nightly.verify_export(root, 'test-run')

    def test_count_and_campaign_mismatch_are_rejected(self):
        with tempfile.TemporaryDirectory() as temporary:
            root = Path(temporary)
            self.fixture(root)
            with self.assertRaisesRegex(ValueError, 'campaign ID'):
                nightly.verify_export(root, 'another-run')
            (root / 'dataset/current-syscall-windows.jsonl').write_text('')
            with self.assertRaisesRegex(ValueError, 'empty'):
                nightly.verify_export(root, 'test-run')

    def test_topology_preserves_existing_consensus_paths(self):
        topology = nightly.infrastructure(Path('D:/isolated-session'))
        encoded = json.dumps(topology)
        self.assertNotIn('unsafe-reset', encoded)
        self.assertNotIn('.cometbft/', encoded)
        self.assertNotIn('container_name', encoded)
        self.assertEqual(topology['services']['minio']['ports'], ['127.0.0.1:19010:9000'])
        self.assertIn('cp -n', topology['services']['node0']['command'][0])


if __name__ == '__main__':
    unittest.main()
