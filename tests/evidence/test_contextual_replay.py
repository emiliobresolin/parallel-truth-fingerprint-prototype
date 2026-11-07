"""History isolation and onset behavior for physical/supervisory LSTM inputs."""
from pathlib import Path
import sys
import unittest

sys.path.insert(0,str(Path(__file__).resolve().parents[2]/'src'))
from parallel_truth_fingerprint.evidence.contextual_replay import test_windows as build_test_windows, metrics


def row(index,phase,offset,value,attack=None):
    views=[]
    if attack is not None:
        normal='normal_stable' if phase=='stable' else 'legitimate_transition'
        replay='replay_same_regime' if phase=='stable' else 'replay_hiding_change'
        for condition,current in [(normal,value),(replay,attack)]:
            views.append({'condition':condition,'supervisory_vector':[current]*4,
                'historical_state':{'source_round_id':f'historical-{offset}'} if condition==replay else None,
                'comparison':{'divergent_sensors':[]}})
    return {'index':index,'round_id':f'round-{index}','phase':phase,'block':1,
            'offset':offset,'physical_vector':[value]*4,'views':views}


class ContextualReplayTests(unittest.TestCase):
    def fixture(self):
        return [row(1,'source',0,12),row(2,'stable',0,13,8),row(3,'stable',1,14,9),
                row(4,'transition',0,15,8)]

    def test_replay_keeps_its_own_history_and_normal_branch_stays_clean(self):
        samples=build_test_windows(self.fixture(),[0,1,2,3])
        replay=[s for s in samples if s['condition']=='replay_same_regime']
        self.assertEqual(replay[0]['input_window'][0],[.5]*8)
        self.assertEqual(replay[1]['input_window'][0],[.5625]*4+[.25]*4)
        self.assertEqual(replay[1]['input_window'][1],[.625]*4+[.3125]*4)
        self.assertEqual(replay[1]['supervisory_source_ids'],['historical-0','historical-1'])
        for sample in samples:
            if sample['condition'] in ('normal_stable','legitimate_transition'):
                for instant in sample['input_window']:
                    self.assertEqual(instant[:4],instant[4:])

    def test_new_phase_resets_supervisory_history_to_prior_live_observation(self):
        samples=build_test_windows(self.fixture(),[0,1,2,3])
        last=samples[-1]
        self.assertEqual(last['condition'],'replay_hiding_change')
        self.assertEqual(last['input_window'][0],[.625]*8)
        self.assertTrue(last['boundary'])

    def test_missing_physical_history_and_noncontiguous_sequence_fail(self):
        with self.assertRaises(ValueError):
            build_test_windows(self.fixture()[1:],[0,1,2,3])
        rows=self.fixture()
        rows[2]['index']=4
        with self.assertRaises(ValueError):
            build_test_windows(rows,[0,1,2,3])

    def test_skipped_supervisory_offset_fails(self):
        rows=self.fixture()
        rows[2]['offset']=2
        with self.assertRaisesRegex(ValueError,'Supervisory history'):
            build_test_windows(rows,[0,1,2,3])

    def test_boundary_metrics_and_numeric_finiteness(self):
        samples=build_test_windows(self.fixture(),[0,1,2,3])
        for sample in samples:
            sample['alert']=True
        m=metrics(samples,'alert',True)
        self.assertEqual(m['replay_same_regime']['count'],1)
        self.assertEqual(m['replay_hiding_change']['count'],0)
        rows=self.fixture()
        rows[2]['physical_vector'][0]=float('nan')
        with self.assertRaises(ValueError):
            build_test_windows(rows,[0,1,2,3])
