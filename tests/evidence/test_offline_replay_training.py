"""Guard temporal split and feature selection against leakage."""
import sys
from pathlib import Path
import unittest

sys.path.insert(0, str(Path(__file__).resolve().parents[2]/'scripts'))
from evaluate_replay_training_offline import current_indices, prepare


class OfflineTrainingTests(unittest.TestCase):
    def test_split_before_windowing_and_fixed_scaling(self):
        schema = ['a.loop_current_ma', 'a.flag', 'b.loop_current_ma', 'c.loop_current_ma']
        rows = [dict(round_id=str(i), phase='train' if i < 120 else 'calibration',
                     feature_schema=schema, physical_vector=[4, 999, 12, 20]) for i in range(180)]
        indices, tensors, ids = prepare(rows)
        self.assertEqual(indices, [0, 2, 3])
        self.assertEqual([len(tensors[k]) for k in ('fit', 'validation', 'calibration')], [71, 47, 59])
        self.assertFalse(set(ids['fit']) & set(ids['validation']))
        self.assertEqual(tensors['fit'][0].tolist(), [[0, .5, 1], [0, .5, 1]])

    def test_overlap_is_rejected(self):
        schema = ['a.loop_current_ma', 'b.loop_current_ma', 'c.loop_current_ma']
        rows = [dict(round_id='duplicate', phase='train' if i < 120 else 'calibration',
                     feature_schema=schema, physical_vector=[4, 12, 20]) for i in range(180)]
        with self.assertRaisesRegex(ValueError, 'overlap'):
            prepare(rows)

    def test_missing_channel_is_rejected(self):
        with self.assertRaises(ValueError):
            current_indices(['a.loop_current_ma'])

    def test_different_reference_support_is_rejected(self):
        schema = ['a.loop_current_ma', 'b.loop_current_ma', 'c.loop_current_ma']
        rows = [dict(round_id=str(i), phase='train' if i < 100 else 'calibration',
                     feature_schema=schema, physical_vector=[4, 12, 20]) for i in range(180)]
        with self.assertRaisesRegex(ValueError, '120 training and 60 calibration'):
            prepare(rows)

    def test_smoke_support_requires_explicit_technical_mode(self):
        schema = ['a.loop_current_ma', 'b.loop_current_ma', 'c.loop_current_ma']
        rows = [dict(round_id=str(i), phase='train' if i < 16 else 'calibration',
                     feature_schema=schema, physical_vector=[4, 12, 20]) for i in range(28)]
        with self.assertRaises(ValueError):
            prepare(rows)
        _, tensors, ids = prepare(rows, technical=True)
        self.assertEqual([len(tensors[k]) for k in ('fit', 'validation', 'calibration')], [8, 6, 11])
        self.assertFalse(set(ids['fit']) & set(ids['validation']))
