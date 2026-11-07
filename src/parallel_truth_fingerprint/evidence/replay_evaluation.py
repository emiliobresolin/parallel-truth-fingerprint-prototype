"""Fixed, prospective replay experiment; separate from the legacy runtime detector."""
from __future__ import annotations

from dataclasses import dataclass, replace
import math

from parallel_truth_fingerprint.scada import FakeOpcUaScadaService


@dataclass(frozen=True)
class ReplayProtocol:
    train_rounds: int = 120
    calibration_rounds: int = 60
    block_rounds: int = 30
    repetitions: int = 5
    interval_seconds: float = 5.0
    epochs: int = 12
    batch_size: int = 8
    latent_units: int = 16
    seed: int = 101
    sequence_length: int = 2
    threshold_stddev_multiplier: float = 3.0

    def validate(self):
        if self.train_rounds < 3 or self.calibration_rounds < 3 or self.block_rounds < 3:
            raise ValueError('Each partition/block requires at least three rounds.')
        if self.repetitions < 1 or min(self.epochs, self.batch_size, self.latent_units) < 1:
            raise ValueError('Invalid training or repetition count.')
        if not math.isfinite(self.interval_seconds) or self.interval_seconds <= 0:
            raise ValueError('Invalid cadence.')
        if self.sequence_length != 2 or self.threshold_stddev_multiplier != 3.0:
            raise ValueError('This protocol fixes L=2 and calibration mean + 3 population standard deviations.')

    def schedule(self):
        self.validate()
        phases = [('train', 0, self.train_rounds), ('calibration', 0, self.calibration_rounds)]
        phases += [(phase, block, self.block_rounds)
                   for block in range(1, self.repetitions + 1)
                   for phase in ('normal', 'replay', 'recovery')]
        return [(phase, block, offset) for phase, block, count in phases for offset in range(count)]


class SequenceReplayScada(FakeOpcUaScadaService):
    """Re-present a whole preceding normal sequence while physical input stays live.

    This is a logical fake-SCADA injection, not a network packet replay. Current
    acquisition time and original source identity are both preserved in audit data.
    """

    def __init__(self, *, sensor_names=('temperature','pressure','rpm'), sensor_ranges=None):
        super().__init__(sensor_names=sensor_names, sensor_ranges=sensor_ranges)
        self.phase = 'train'
        self.offset = 0
        self.source_sequence = []
        self.normal_sequence = []
        self.physical_state = None
        self.original_state = None

    def select_phase(self, phase, offset):
        if phase == 'normal' and offset == 0:
            self.normal_sequence = []
        if phase == 'replay' and offset == 0:
            self.source_sequence = tuple(self.normal_sequence)
        self.phase, self.offset = phase, offset

    def update_from_consensused_state(self, valid_state, *, source_replicated_state=None):
        physical = self.project_state(valid_state, source_replicated_state=source_replicated_state)
        self.physical_state = physical
        self.original_state = None
        if self.phase == 'replay':
            if self.offset >= len(self.source_sequence):
                raise ValueError('Missing preceding normal source for sequence replay.')
            source = self.source_sequence[self.offset]
            self.original_state = source
            logical = replace(
                source, timestamp=physical.timestamp, source_round_id=physical.source_round_id,
                behavioral_source_round_id=source.source_round_id,
                sensor_values={k: replace(v, mode='replay') for k, v in source.sensor_values.items()},
                behavioral_sensor_values={k: replace(v, mode='replay')
                                          for k, v in (source.behavioral_sensor_values or {}).items()},
            )
        else:
            logical = physical
            if self.phase == 'normal':
                self.normal_sequence.append(physical)
        self._current_state = logical
        # No use of the inherited growing legacy history is needed for this experiment.
        return logical


class PhaseStore:
    """Keep any persisted test/replay observations out of normal training history."""

    def __init__(self, delegate):
        self.delegate = delegate
        self.phase = 'train'

    def __getattr__(self, name):
        return getattr(self.delegate, name)

    def save_json(self, key, payload):
        if key.startswith('valid-consensus-artifacts/'):
            payload = dict(payload)
            payload['dataset_context'] = dict(payload.get('dataset_context', {}),
                scenario_label=self.phase, training_label='normal' if self.phase == 'train' else 'reserved',
                training_eligible=self.phase == 'train', training_eligibility_reason='fixed_replay_protocol')
        return self.delegate.save_json(key, payload)


def build_scoring_window(previous_physical, current_supervisory):
    """Identical hybrid L=2 input in train/calibration/normal/replay/recovery."""
    if previous_physical is None:
        return None
    if len(previous_physical) != len(current_supervisory):
        raise ValueError('Physical/supervisory schema mismatch.')
    return [list(previous_physical), list(current_supervisory)]


def fixed_threshold(scores):
    if not scores or any(not math.isfinite(s) or s < 0 for s in scores):
        raise ValueError('Invalid calibration scores.')
    mean = sum(scores) / len(scores)
    std = math.sqrt(sum((s - mean) ** 2 for s in scores) / len(scores))
    return {'rule': 'max(mean(calibration MSE) + 3*population_std(calibration MSE), 1e-6)',
            'count': len(scores), 'mean': mean, 'population_std': std,
            'threshold': max(mean + 3 * std, 1e-6)}


def summarize_scores(rows, *, exclude_transitions=False):
    scored = [r for r in rows if r['phase'] in {'normal', 'replay', 'recovery'}
              and r['score'] is not None and (not exclude_transitions or not r['transition'])]
    tp = sum(r['phase'] == 'replay' and r['anomalous'] for r in scored)
    fn = sum(r['phase'] == 'replay' and not r['anomalous'] for r in scored)
    fp = sum(r['phase'] != 'replay' and r['anomalous'] for r in scored)
    tn = sum(r['phase'] != 'replay' and not r['anomalous'] for r in scored)
    groups = {}
    for phase in ('normal', 'replay', 'recovery'):
        values = sorted(r['score'] for r in scored if r['phase'] == phase)
        groups[phase] = {'count': len(values), 'min': min(values) if values else None,
                         'max': max(values) if values else None,
                         'mean': sum(values) / len(values) if values else None}
    return {'scored_rounds': len(scored), 'TP': tp, 'FN': fn, 'FP': fp, 'TN': tn,
            'FPR': fp / (fp + tn) if fp + tn else None,
            'replay_recall': tp / (tp + fn) if tp + fn else None,
            'distributions': groups,
            'qualification': 'Descriptive dependent windows from one model fit; not independent repetitions.'}
