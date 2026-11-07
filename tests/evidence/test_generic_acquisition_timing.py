"""Exercise actual worker scheduling across unobserved conditioning gaps."""
from contextlib import ExitStack
from dataclasses import make_dataclass
import importlib.util
import json
from pathlib import Path
import sys
import tempfile
from types import SimpleNamespace
import unittest
from unittest.mock import patch

from parallel_truth_fingerprint.evidence.paired_replay import PairedReplayProtocol
from parallel_truth_fingerprint.sensor_simulation.operational_profiles import OperationalAssumptions


ROOT = Path(__file__).resolve().parents[2]
spec = importlib.util.spec_from_file_location('generic_timing_worker', ROOT/'scripts/paired_replay_worker.py')
worker = importlib.util.module_from_spec(spec)
spec.loader.exec_module(worker)


class TimingProtocol(PairedReplayProtocol):
    def profile_schedule(self):
        # Stop before model fitting: this test exercises the acquisition loop.
        return [('train',0,i) for i in range(3)]+[('source',1,i) for i in range(3)]


class FakeClock:
    def __init__(self):
        self.now = 1000.0

    def advance(self, seconds):
        self.now += seconds


class AcquisitionTimingTests(unittest.TestCase):
    def run_worker(self, *, generic):
        clock = FakeClock()
        starts, conditioning = [], []

        class Simulator:
            def __init__(self, **kwargs):
                self.assumptions = OperationalAssumptions()
                self._control = SimpleNamespace(current_noise_multiplier=1.0)
                self.simulation_seconds = 0.0
                self.target_demand = self.base_demand = self.current_demand = 50.0
                self.engineering_state = {}

            def set_demand_target(self, target):
                self.target_demand = target

            def condition_to_regime(self):
                conditioning.append(clock.now)
                clock.advance(8.0)
                return {'wall_duration_seconds':8.0}

        def acquire(index, config, components, store, scada):
            starts.append((scada.phase, scada.offset, clock.now))
            clock.advance(2.0)
            components['simulator'].simulation_seconds += 5.0
            current = SimpleNamespace(source_round_id=f'r{index}', timestamp='test', to_dict=lambda:{})
            physical = SimpleNamespace(measurement_domain='loop_current_ma', source_edges=('edge-1',),
                sensor_values={'temperature':8.8})
            comparison = SimpleNamespace(divergent_sensors=(), to_dict=lambda:{})
            return current, comparison, {'status':'persisted','artifact_key':f'a{index}'}, physical

        Config = make_dataclass('TimingConfig', ['minio_bucket','demo_steps',
            'demo_scenario_name','demo_scada_mode','demo_disable_runtime_autoencoder'])
        config = Config('timing',1,'normal','match',True)
        components = {'edges':[], 'artifact_store':object(), 'acquisition_snapshot':{},
            'hart_source_evidence':{}}
        keras = SimpleNamespace(utils=SimpleNamespace(set_random_seed=lambda seed:None))
        protocol = TimingProtocol(edge_count=4, interval_seconds=5.0)
        settings = {'generic_numerical_resolution':{'selected_substeps_per_round':384}} if generic else None
        # Load the native extension before patch.dict restores sys.modules;
        # NumPy cannot be unloaded and imported twice in one process.
        import numpy
        with tempfile.TemporaryDirectory() as temporary, ExitStack() as stack:
            stack.enter_context(patch.dict(sys.modules, torch=SimpleNamespace(set_num_threads=lambda count:None)))
            stack.enter_context(patch('parallel_truth_fingerprint.lstm_service.trainer._load_keras_module',return_value=keras))
            stack.enter_context(patch.object(worker.demo,'load_runtime_demo_config',return_value=config))
            stack.enter_context(patch.object(worker.demo,'build_demo_runtime_components',return_value=components))
            stack.enter_context(patch('parallel_truth_fingerprint.sensor_simulation.generic_plant.GenericReceiverCompressorSimulator',Simulator))
            stack.enter_context(patch('parallel_truth_fingerprint.sensor_simulation.mass_flow.MassFlowCompressorSimulator',Simulator))
            stack.enter_context(patch.object(worker,'acquire',side_effect=acquire))
            stack.enter_context(patch.object(worker,'extract_scada_behavioral_feature_vector',return_value=(('temperature',),(8.8,))))
            stack.enter_context(patch.object(worker,'time',SimpleNamespace(
                monotonic=lambda:clock.now,time=lambda:clock.now,sleep=clock.advance,
                perf_counter_ns=lambda:int(clock.now*1e9),process_time_ns=lambda:0)))
            root = Path(temporary)
            summary = worker.run_profile('unmodulated',protocol,root/'profile',root,
                {'completed_rounds':0},hart_totalizer=generic,generic_settings=settings)
            self.assertEqual(summary['status'],'completed')
            rows=[json.loads(line) for line in (root/'profile/observations.jsonl').read_text().splitlines()]
            self.assertEqual([row['acquisition_timing']['wall_seconds'] for row in rows],[2.0]*6)
            self.assertEqual([row['acquisition_timing']['cpu_seconds'] for row in rows],[0.0]*6)
        return starts, conditioning

    def test_generic_acquisitions_keep_cadence_after_train_and_source_conditioning(self):
        starts, conditioning = self.run_worker(generic=True)
        self.assertEqual(len(conditioning),2)
        self.assertEqual([(phase,offset) for phase,offset,_ in starts],
            [('train',0),('train',1),('train',2),('source',0),('source',1),('source',2)])
        # Train/source conditioned acquisitions and ordinary acquisitions all
        # retain five seconds before their successor; the intervening source
        # conditioning contributes eight additional unobserved seconds.
        self.assertEqual([b[2]-a[2] for a,b in zip(starts,starts[1:])],
            [5.0,5.0,13.0,5.0,5.0])

    def test_legacy_acquisitions_keep_existing_cadence_without_conditioning(self):
        starts, conditioning = self.run_worker(generic=False)
        self.assertEqual(conditioning,[])
        self.assertEqual([b[2]-a[2] for a,b in zip(starts,starts[1:])],[5.0]*5)


if __name__ == '__main__':
    unittest.main()
