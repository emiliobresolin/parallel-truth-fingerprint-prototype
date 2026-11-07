from pathlib import Path
import sys
import unittest
import numpy as np

sys.path.insert(0,str(Path(__file__).resolve().parents[2]/'src'))
from parallel_truth_fingerprint.evidence.contextual_error import components


class ContextualErrorTests(unittest.TestCase):
    def test_common_reconstruction_error_is_removed_from_relational_term(self):
        x=np.zeros((1,2,8),dtype='float32')
        c=components(x,np.ones_like(x))
        self.assertEqual(c['global_mse'][0],1.)
        self.assertEqual(c['common_error'][0],1.)
        self.assertEqual(c['relational_error'][0],0.)

    def test_opposed_error_and_direct_control_use_same_scale(self):
        x=np.zeros((1,2,8),dtype='float32')
        x[:,:,4:]=2
        y=np.ones_like(x)
        c=components(x,y)
        self.assertEqual(c['global_mse'][0],1.)
        self.assertEqual(c['relational_error'][0],1.)
        self.assertEqual(c['direct_gap'][0],1.)
        self.assertEqual(c['common_error'][0],0.)

    def test_global_identity_and_invalid_inputs(self):
        rng=np.random.default_rng(101)
        x=rng.normal(size=(7,2,8))
        y=rng.normal(size=(7,2,8))
        c=components(x,y)
        np.testing.assert_allclose(c['global_mse'],c['common_error']+c['relational_error'],rtol=1e-5)
        with self.assertRaises(ValueError):
            components(x[:,:,:4],y[:,:,:4])
        x[0,0,0]=np.nan
        with self.assertRaises(ValueError):
            components(x,y)
