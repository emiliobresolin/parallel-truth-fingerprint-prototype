"""Prospective replay protocol, ordered injection and leakage boundary checks."""
from dataclasses import replace
import hashlib
import json
import math
from pathlib import Path
import sys
import tempfile
import unittest

sys.path.insert(0, str(Path(__file__).resolve().parents[2] / 'src'))
sys.path.insert(0, str(Path(__file__).resolve().parents[2] / 'scripts'))
from run_replay_evaluation import verify_results
from parallel_truth_fingerprint.contracts.scada_state import ScadaState, ScadaSensorState, ScadaBehavioralSensorState
from parallel_truth_fingerprint.evidence.replay_evaluation import (
    ReplayProtocol, SequenceReplayScada, PhaseStore, build_scoring_window, fixed_threshold, summarize_scores,
)


def state(number):
    return ScadaState('compressor-1', f'round-{number}', f'2026-10-27T12:{number:02d}:00+00:00',
        {n: ScadaSensorState(float(number), 'test') for n in ('temperature', 'pressure', 'rpm')},
        f'round-{number}', {n: ScadaBehavioralSensorState(loop_current_ma=float(number), source_round_id=f'round-{number}')
                             for n in ('temperature', 'pressure', 'rpm')})


class ReplayEvaluationTests(unittest.TestCase):
    def result_fixture(self, root, *, missing_scores=False, wrong_schedule=False):
        protocol = ReplayProtocol(train_rounds=3, calibration_rounds=3, block_rounds=3, repetitions=1)
        model_hash = hashlib.sha256(b'model').hexdigest()
        rows, sources = [], {}
        previous, previous_phase = None, None
        for index, (phase, block, offset) in enumerate(protocol.schedule(), 1):
            physical = state(index)
            original = sources.get(offset) if phase == 'replay' else None
            logical = replace(original, source_round_id=physical.source_round_id, timestamp=physical.timestamp,
                              behavioral_source_round_id=original.source_round_id,
                              sensor_values={k: replace(v, mode='replay') for k, v in original.sensor_values.items()},
                              behavioral_sensor_values={k: replace(v, mode='replay') for k, v in original.behavioral_sensor_values.items()}) if original else physical
            if phase == 'normal':
                sources[offset] = logical
            warmup = offset == 0 and (phase in {'train', 'calibration'} or (phase == 'normal' and block == 1))
            if warmup:
                previous = None
            vector = [logical.sensor_values['rpm'].value]
            scored = phase in {'normal', 'replay', 'recovery'} and not warmup and not missing_scores
            rows.append({'index': index, 'round_id': physical.source_round_id, 'phase': phase,
                'block': block, 'offset': offset, 'warmup': warmup, 'transition': phase != previous_phase,
                'score': 1.0 if scored else None, 'anomalous': False if scored else None,
                'threshold': 2.0, 'model_sha256': model_hash,
                'current_supervisory_vector': vector, 'current_physical_vector': [float(index)],
                'input_window': build_scoring_window(previous, vector),
                'scada_state': logical.to_dict(), 'replay_original_state': original.to_dict() if original else None,
                'comparison': {'divergent_sensors': []}, 'persistence_status': 'persisted'})
            previous, previous_phase = [float(index)], phase
        if wrong_schedule:
            rows[-1]['offset'] = 0
        payloads = {'summary.json': {'status': 'completed', 'completed_rounds': len(rows), 'weights_unchanged': True},
                    'calibration.json': {'threshold': 2.0, 'count': 2},
                    'model.json': {'sha256': model_hash, 'training_windows': 2}}
        for name, payload in payloads.items():
            (root / name).write_text(json.dumps(payload))
        (root / 'model.keras').write_bytes(b'model')
        (root / 'observations.jsonl').write_text(''.join(json.dumps(r) + '\n' for r in rows))
        manifest = {p.name: hashlib.sha256(p.read_bytes()).hexdigest() for p in root.iterdir()}
        (root / 'manifest.json').write_text(json.dumps(manifest))
        return protocol

    def test_verifier_requires_scored_windows_not_just_round_counts(self):
        with tempfile.TemporaryDirectory() as directory:
            root = Path(directory)
            protocol = self.result_fixture(root, missing_scores=True)
            with self.assertRaisesRegex(ValueError, 'Missing or unexpected scored'):
                verify_results(root, protocol)

    def test_verifier_checks_schedule_and_accepts_consistent_replay(self):
        with tempfile.TemporaryDirectory() as directory:
            root = Path(directory)
            protocol = self.result_fixture(root)
            self.assertEqual(verify_results(root, protocol)['status'], 'completed')
        with tempfile.TemporaryDirectory() as directory:
            root = Path(directory)
            protocol = self.result_fixture(root, wrong_schedule=True)
            with self.assertRaisesRegex(ValueError, 'schedule'):
                verify_results(root, protocol)

    def test_approved_schedule_counts_and_order(self):
        schedule = ReplayProtocol().schedule()
        self.assertEqual(len(schedule), 630)
        self.assertEqual(sum(p == 'replay' for p, _, _ in schedule), 150)
        self.assertEqual(schedule[180], ('normal', 1, 0))
        self.assertEqual(schedule[210], ('replay', 1, 0))
        self.assertEqual(schedule[-1], ('recovery', 5, 29))

    def test_documented_noise_nonpaired_verifier_checks_acquisition_after_rehash(self):
        from parallel_truth_fingerprint.sensor_simulation.current_noise import noise_configuration
        from parallel_truth_fingerprint.sensor_simulation.simulator import CompressorSimulator
        with tempfile.TemporaryDirectory() as directory:
            root = Path(directory)
            protocol = self.result_fixture(root)
            frozen = {'version': 'documented-noise-scada-replay-v2',
                      'current_noise_configuration': noise_configuration(), 'current_noise_multiplier': 1.0}
            (root/'protocol.json').write_text(json.dumps(frozen), encoding='utf-8')
            summary = json.loads((root/'summary.json').read_text())
            summary['protocol_sha256'] = hashlib.sha256((root/'protocol.json').read_bytes()).hexdigest()
            (root/'summary.json').write_text(json.dumps(summary))
            rows = [json.loads(line) for line in (root/'observations.jsonl').read_text().splitlines()]
            for row in rows:
                frame = CompressorSimulator(seed=row['index']).step(operating_state_pct=50).to_dict()
                row['acquisition_snapshot'] = frame
                row['consensused_physical_values'] = {
                    channel: observation['loop_current_ma']
                    for channel, observation in frame['transmitter_observations'].items()}

            def persist():
                (root/'observations.jsonl').write_text(''.join(json.dumps(row)+'\n' for row in rows))
                manifest = {p.name: hashlib.sha256(p.read_bytes()).hexdigest()
                            for p in root.iterdir() if p.name != 'manifest.json'}
                (root/'manifest.json').write_text(json.dumps(manifest))

            persist()
            self.assertEqual(verify_results(root, protocol)['status'], 'completed')
            snapshot = rows[0]['acquisition_snapshot']
            del snapshot['metadata']['current_noise_configuration']
            persist()
            with self.assertRaisesRegex(ValueError, 'acquisition noise'):
                verify_results(root, protocol)
            snapshot['metadata']['current_noise_configuration'] = noise_configuration()
            snapshot['transmitter_observations']['rpm']['loop_current_ma'] += 0.001
            persist()
            with self.assertRaisesRegex(ValueError, 'snapshot differs'):
                verify_results(root, protocol)

    def test_sequence_replays_all_values_in_order_and_recovers(self):
        scada = SequenceReplayScada()
        physical = [state(i) for i in range(1, 10)]
        for offset in range(3):
            scada.select_phase('normal', offset)
            scada.project_state = lambda *a, value=physical[offset], **k: value
            scada.update_from_consensused_state(None)
        for offset in range(3):
            scada.select_phase('replay', offset)
            scada.project_state = lambda *a, value=physical[3 + offset], **k: value
            result = scada.update_from_consensused_state(None)
            self.assertEqual(result.sensor_values['rpm'].value, physical[offset].sensor_values['rpm'].value)
            self.assertEqual(result.behavioral_sensor_values['rpm'].loop_current_ma, float(offset + 1))
            self.assertEqual(result.timestamp, physical[3 + offset].timestamp)
            self.assertEqual(result.behavioral_source_round_id, physical[offset].source_round_id)
            self.assertEqual(scada.physical_state, physical[3 + offset])
        scada.select_phase('recovery', 0)
        scada.project_state = lambda *a, **k: physical[6]
        self.assertEqual(scada.update_from_consensused_state(None), physical[6])

    def test_empty_replay_source_fails_instead_of_using_current(self):
        scada = SequenceReplayScada()
        scada.select_phase('replay', 0)
        scada.project_state = lambda *a, **k: state(1)
        with self.assertRaisesRegex(ValueError, 'Missing preceding'):
            scada.update_from_consensused_state(None)

    def test_identical_window_rule_and_calibration(self):
        self.assertIsNone(build_scoring_window(None, (1, 2)))
        self.assertEqual(build_scoring_window((1, 2), (3, 4)), [[1, 2], [3, 4]])
        with self.assertRaises(ValueError):
            build_scoring_window((1,), (2, 3))
        self.assertAlmostEqual(fixed_threshold([1, 2, 3])['threshold'], 2 + 3 * math.sqrt(2 / 3))
        with self.assertRaises(ValueError):
            fixed_threshold([float('nan')])

    def test_replay_never_marked_training_eligible(self):
        class Store:
            def save_json(self, key, payload):
                self.payload = payload
        delegate = Store()
        wrapped = PhaseStore(delegate)
        for phase in ('train', 'calibration', 'normal', 'replay', 'recovery'):
            wrapped.phase = phase
            wrapped.save_json('valid-consensus-artifacts/round.json', {})
            self.assertEqual(delegate.payload['dataset_context']['training_eligible'], phase == 'train')

    def test_metric_truth_is_phase_not_score_or_persistence(self):
        rows = [{'phase': 'normal', 'score': 4, 'anomalous': True, 'transition': False},
                {'phase': 'replay', 'score': 1, 'anomalous': False, 'transition': True},
                {'phase': 'recovery', 'score': 1, 'anomalous': False, 'transition': False}]
        all_rows = summarize_scores(rows)
        self.assertEqual((all_rows['FP'], all_rows['FN'], all_rows['TN']), (1, 1, 1))
        self.assertEqual(summarize_scores(rows, exclude_transitions=True)['FN'], 0)


if __name__ == '__main__':
    unittest.main()
