"""Protocol and audit for paired normal/replayed supervision on a shared trajectory."""
from dataclasses import dataclass, replace
import hashlib
import json
import math
from pathlib import Path

from parallel_truth_fingerprint.evidence.replay_evaluation import build_scoring_window
from parallel_truth_fingerprint.sensor_simulation.operational_profiles import OperationalAssumptions


@dataclass(frozen=True)
class PairedReplayProtocol:
    train_rounds: int = 120
    calibration_rounds: int = 60
    block_rounds: int = 30
    settle_rounds: int = 12
    repetitions: int = 5
    interval_seconds: float = 5.0
    epochs: int = 12
    batch_size: int = 8
    latent_units: int = 16
    seed: int = 101
    simulation_seed: int | None = None
    edge_count: int = 3
    sequence_length: int = 2
    threshold_stddev_multiplier: float = 3.0

    def validate(self):
        if self.edge_count not in (3, 4):
            raise ValueError('Expected three or four acquisition edges.')
        if self.simulation_seed is not None and (not isinstance(self.simulation_seed, int) or not 0 <= self.simulation_seed < 2**32):
            raise ValueError('Invalid simulation seed.')
        if min(self.train_rounds, self.calibration_rounds) < 8 or min(self.block_rounds, self.settle_rounds) < 3 or self.repetitions < 1:
            raise ValueError('Insufficient partition/block support.')
        if not math.isfinite(self.interval_seconds) or self.interval_seconds <= 0:
            raise ValueError('Invalid cadence.')
        if min(self.epochs, self.batch_size, self.latent_units) < 1 or self.sequence_length != 2 or self.threshold_stddev_multiplier != 3:
            raise ValueError('Invalid fixed model protocol.')

    def profile_schedule(self):
        self.validate()
        phases = [('train', 0, self.train_rounds), ('calibration', 0, self.calibration_rounds)]
        phases += [(phase, block, self.settle_rounds if phase == 'settle' else self.block_rounds)
                   for block in range(1, self.repetitions + 1)
                   for phase in ('settle', 'source', 'stable', 'transition')]
        return [(phase, block, i) for phase, block, count in phases for i in range(count)]

    def schedule(self):
        return [(profile, *step) for profile in ('unmodulated', 'modulated') for step in self.profile_schedule()]

    def demand_target(self, phase, offset):
        a = OperationalAssumptions()
        if phase in {'train', 'calibration'}:
            count = self.train_rounds if phase == 'train' else self.calibration_rounds
            # A/B/A/B during train and calibration, including both transition directions.
            segment = min(3, offset * 4 // count)
            return a.low_demand_pct if segment % 2 == 0 else a.high_demand_pct
        return a.high_demand_pct if phase == 'transition' else a.low_demand_pct


def replay_view(current, historical):
    return replace(historical, source_round_id=current.source_round_id, timestamp=current.timestamp,
                   behavioral_source_round_id=historical.source_round_id,
                   sensor_values={k: replace(v, mode='replay') for k, v in historical.sensor_values.items()},
                   behavioral_sensor_values={k: replace(v, mode='replay') for k, v in historical.behavioral_sensor_values.items()})


def paired_metrics(rows):
    result = {}
    for condition in ('normal_stable', 'legitimate_transition', 'replay_same_regime', 'replay_hiding_change'):
        selected = [view for row in rows for view in row.get('views', []) if view['condition'] == condition]
        scores = [view['score'] for view in selected]
        result[condition] = {
            'count': len(selected), 'lstm_alerts': sum(view['anomalous'] for view in selected),
            'comparator_alerts': sum(bool(view['comparison']['divergent_sensors']) for view in selected),
            'rate_role': 'replay_recall' if condition.startswith('replay_') else 'false_positive_rate',
            'lstm_alert_rate': sum(view['anomalous'] for view in selected) / len(selected) if selected else None,
            'comparator_alert_rate': sum(bool(view['comparison']['divergent_sensors']) for view in selected) / len(selected) if selected else None,
            'score_min': min(scores) if scores else None, 'score_max': max(scores) if scores else None,
            'score_mean': sum(scores) / len(scores) if scores else None,
            'transition_windows': sum(view['transition_window'] for view in selected),
        }
    return result


def verify_recorded_noise(generation, declared_noise, expected_currents=None):
    """Check persisted acquisition provenance against its frozen noise contract."""
    from parallel_truth_fingerprint.sensor_simulation.current_noise import noise_rms_ma
    snapshot = generation.get('acquisition_snapshot', {})
    metadata = snapshot.get('metadata', {})
    multiplier = generation.get('current_noise_multiplier')
    if (multiplier != 1.0
            or generation.get('current_noise_configuration') != declared_noise
            or metadata.get('current_noise_configuration') != declared_noise
            or metadata.get('current_noise_ma') != noise_rms_ma(multiplier)
            or metadata.get('control_adjustments', {}).get('current_noise_multiplier') != multiplier):
        raise ValueError('Recorded acquisition noise differs from frozen profile.')
    if expected_currents is not None:
        acquired_currents = {sensor: item['loop_current_ma']
            for sensor, item in snapshot.get('transmitter_observations', {}).items()}
        if acquired_currents != expected_currents:
            raise ValueError('Acquisition snapshot differs from agreed current observations.')
    return snapshot


def verify_paired_results(directory, protocol):
    import numpy as np
    from parallel_truth_fingerprint.evidence.replay_evaluation import fixed_threshold
    directory = Path(directory)
    root_summary = json.loads((directory / 'summary.json').read_text(encoding='utf-8'))
    if root_summary['status'] != 'completed':
        raise ValueError('Paired experiment incomplete.')
    if root_summary['protocol_sha256'] != hashlib.sha256((directory / 'protocol.json').read_bytes()).hexdigest():
        raise ValueError('Frozen protocol hash mismatch.')
    total = 0
    frozen_protocol = json.loads((directory/'protocol.json').read_text())
    from parallel_truth_fingerprint.evidence.hart_totalizer import validate_collection_contract
    validate_collection_contract(frozen_protocol)
    declared_domain = frozen_protocol.get('measurement_domain')
    declared_noise = frozen_protocol.get('current_noise_configuration')
    if frozen_protocol.get('version', '').startswith('documented-noise-'):
        from parallel_truth_fingerprint.sensor_simulation.current_noise import validate_noise_configuration
        validate_noise_configuration(declared_noise)
        if declared_domain != 'loop_current_ma' or frozen_protocol.get('current_noise_multiplier') != 1.0:
            raise ValueError('Documented-noise protocol requires currents and the unscaled reference profile.')
        if root_summary.get('current_noise_configuration') != declared_noise:
            raise ValueError('Root summary differs from frozen noise profile.')
    for profile in ('unmodulated', 'modulated'):
        root = directory / profile
        manifest = json.loads((root / 'manifest.json').read_text())
        for name, digest in manifest.items():
            if hashlib.sha256((root / name).read_bytes()).hexdigest() != digest:
                raise ValueError(f'Hash mismatch: {profile}/{name}')
        rows = [json.loads(s) for s in (root / 'observations.jsonl').read_text().splitlines()]
        if 'hart_totalizer_configuration' in frozen_protocol:
            from parallel_truth_fingerprint.evidence.hart_totalizer import validate_rows
            validate_rows(rows, frozen_protocol)
        if len(rows) != len(protocol.profile_schedule()) or len({r['round_id'] for r in rows}) != len(rows):
            raise ValueError('Missing/duplicate physical rounds.')
        model = json.loads((root / 'model.json').read_text())
        calibration = json.loads((root / 'calibration.json').read_text())
        summary = json.loads((root / 'summary.json').read_text())
        if declared_noise is not None and summary.get('current_noise_configuration') != declared_noise:
            raise ValueError('Profile summary differs from frozen noise profile.')
        if hashlib.sha256((root / 'model.keras').read_bytes()).hexdigest() != model['sha256'] or not summary['weights_unchanged']:
            raise ValueError('Frozen model mismatch.')
        if summary['final_weights_sha256'] != model['weights_sha256']:
            raise ValueError('Final model weights differ from training.')
        previous = None
        sources = {}
        for index, (row, expected) in enumerate(zip(rows, protocol.profile_schedule()), 1):
            if declared_domain == 'loop_current_ma':
                expected_currents = {name.split('.')[0]: row['physical_vector'][i]
                    for i, name in enumerate(row['feature_schema']) if name.endswith('.loop_current_ma')}
                if (row.get('measurement_domain') != declared_domain or row.get('consensus_schema') != 'current-consensus-v2'
                        or row['consensused_values'] != expected_currents):
                    raise ValueError('Acquired/consensused/supervisory currents must agree in the declared domain.')
                baseline_currents = {sensor: item['loop_current_ma'] for sensor, item in row['physical_scada']['behavioral_sensor_values'].items()}
                if baseline_currents != expected_currents:
                    raise ValueError('Physical reference differs from its recorded current observation.')
                if declared_noise is not None:
                    verify_recorded_noise(row['generation'], declared_noise, expected_currents)
                for view in row['views']:
                    state = view['scada_state']
                    expected_vector = []
                    for sensor in sorted(state['sensor_values']):
                        b = state['behavioral_sensor_values'][sensor]
                        current = float(b['loop_current_ma'])
                        if not math.isfinite(current):
                            raise ValueError('Nonfinite supervisory current.')
                        expected_vector.extend([current, (current-4)/16,
                            float(bool(b['field_device_malfunction'])), float(bool(b['loop_current_saturated'])), float(bool(b['cold_start']))])
                    if view['supervisory_vector'] != expected_vector:
                        raise ValueError('Supervisory features differ from recorded current observations.')
                    divergent = []
                    outputs = view['comparison']['sensor_outputs']
                    if len(outputs) != len(expected_currents) or {item['sensor_name'] for item in outputs} != set(expected_currents):
                        raise ValueError('Comparator must account for every current channel exactly once.')
                    for item in view['comparison']['sensor_outputs']:
                        if item.get('unit') != 'mA' or item['tolerance'] != 0:
                            raise ValueError('Comparator must use the declared digital-current rule.')
                        sensor = item['sensor_name']
                        physical = expected_currents[sensor]
                        supervisory = state['behavioral_sensor_values'][sensor]['loop_current_ma']
                        difference = abs(physical-supervisory)
                        within = difference == 0
                        if (item['physical_value'] != physical or item['scada_value'] != supervisory
                                or item['absolute_difference'] != difference
                                or item['tolerance_evaluation'] != ('within_tolerance' if within else 'outside_tolerance')
                                or item['divergence_classification'] != ('match' if within else 'divergent')):
                            raise ValueError('Comparator decision differs from acquired currents.')
                        if not within:
                            divergent.append(sensor)
                    if set(divergent) != set(view['comparison']['divergent_sensors']):
                        raise ValueError('Comparator divergent channel summary mismatch.')
            if protocol.edge_count == 4:
                expected_edges = [f'edge-{i}' for i in range(1, 5)]
                if row.get('edge_membership') != expected_edges or sorted(row.get('consensus_source_edges', [])) != expected_edges:
                    raise ValueError('Four-edge membership missing from acquisition/consensus.')
                interval = row.get('acquisition_window', {})
                if not interval.get('start_epoch', 0) < interval.get('end_epoch', 0):
                    raise ValueError('Missing acquisition timing for syscall association.')
            phase, block, offset = expected
            if (row['index'], row['profile'], row['phase'], row['block'], row['offset']) != (index, profile, phase, block, offset):
                raise ValueError('Schedule mismatch.')
            if offset == 0 and (phase in {'train', 'calibration'} or (phase == 'settle' and block == 1)):
                previous = None
            if row['reference_window'] != build_scoring_window(previous, row['physical_vector']):
                raise ValueError('Physical reference window crossed a partition or changed its rule.')
            if row['generation']['demand_target_pct'] != protocol.demand_target(phase, offset):
                raise ValueError('Demand target differs from the protocol.')
            if row['baseline_persistence'] != 'persisted' or row['baseline_comparison']['divergent_sensors']:
                raise ValueError('Current supervisory baseline was not valid.')
            if phase == 'source':
                sources[block, offset] = row
            if phase in {'stable', 'transition'}:
                conditions = ('normal_stable', 'replay_same_regime') if phase == 'stable' else ('legitimate_transition', 'replay_hiding_change')
                if [v['condition'] for v in row['views']] != list(conditions):
                    raise ValueError('Missing paired conditions.')
                for view in row['views']:
                    if (not math.isfinite(view['score']) or view['score'] < 0 or view['threshold'] != calibration['threshold']
                            or view['model_sha256'] != model['sha256'] or view['anomalous'] != (view['score'] > view['threshold'])):
                        raise ValueError('Score/model/threshold mismatch.')
                    if view['input_window'] != build_scoring_window(previous, view['supervisory_vector']):
                        raise ValueError('Window rule mismatch.')
                    if view['counterfactual_persistence_blocked'] != bool(view['comparison']['divergent_sensors']):
                        raise ValueError('Comparator gate mismatch.')
                    if view['supervisory_write_performed'] or view['transition_window'] != (offset == 0):
                        raise ValueError('Unexpected supervisory write or boundary flag.')
                source = sources[block, offset]['physical_scada']
                attack = row['views'][1]
                if attack['historical_state'] != source or attack['scada_state']['behavioral_source_round_id'] != source['source_round_id']:
                    raise ValueError('Historical source/order mismatch.')
                for group in ('sensor_values', 'behavioral_sensor_values'):
                    expected_values = {k: dict(v, mode='replay') for k, v in source[group].items()}
                    if attack['scada_state'][group] != expected_values:
                        raise ValueError('Historical payload mismatch.')
                if row['views'][0]['scada_state'] != row['physical_scada']:
                    raise ValueError('Paired normal view is not the current observation.')
            elif row['views']:
                raise ValueError('Unexpected test scoring in reference/source partitions.')
            previous = row['physical_vector']
        if paired_metrics(rows) != summary['metrics']:
            raise ValueError('Recomputed paired metrics differ.')
        if model['training_windows'] != protocol.train_rounds - 1 or calibration['count'] != protocol.calibration_rounds - 1:
            raise ValueError('Reference support mismatch.')
        for phase, filename in [('train', 'train-windows.npy'), ('calibration', 'calibration-windows.npy')]:
            expected_windows = [r['reference_window'] for r in rows if r['phase'] == phase and r['reference_window'] is not None]
            if not np.array_equal(np.load(root / filename), np.asarray(expected_windows, dtype='float32')):
                raise ValueError('Saved reference tensor differs from its declared partition.')
        if calibration['threshold'] != fixed_threshold(calibration['scores'])['threshold']:
            raise ValueError('Calibration threshold rule mismatch.')
        if model['training_round_ids'] != [r['round_id'] for r in rows if r['phase'] == 'train']:
            raise ValueError('Model training provenance mismatch.')
        total += len(rows)
    if total != len(protocol.schedule()) or root_summary['completed_rounds'] != total:
        raise ValueError('Root count mismatch.')
    return root_summary
