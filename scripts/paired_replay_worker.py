"""Two operating profiles, with paired current/replayed supervision per physical round."""
from dataclasses import asdict, replace
from datetime import datetime, timezone
import argparse
import hashlib
import json
import os
from pathlib import Path
import sys
import time

ROOT = Path(__file__).resolve().parents[1]
sys.path.insert(0, str(ROOT / 'src'))
sys.path.insert(0, str(ROOT / 'scripts'))
from replay_evaluation_worker import acquire, save
import run_local_demo as demo
from parallel_truth_fingerprint.evidence.replay_evaluation import (
    PhaseStore, SequenceReplayScada, build_scoring_window, fixed_threshold,
)
from parallel_truth_fingerprint.evidence.paired_replay import PairedReplayProtocol, replay_view, paired_metrics
from parallel_truth_fingerprint.sensor_simulation.operational_profiles import OperationalCompressorSimulator, OperationalAssumptions
from parallel_truth_fingerprint.sensor_simulation.current_noise import noise_configuration, validate_noise_configuration
from parallel_truth_fingerprint.lstm_service.replay_behavior import extract_scada_behavioral_feature_vector


def run_profile(profile, protocol, output, root_output, root_summary, *, hart_totalizer=False, generic_settings=None):
    import numpy as np
    import torch
    torch.set_num_threads(1)
    from parallel_truth_fingerprint.lstm_service.trainer import _load_keras_module, build_lstm_autoencoder, _export_model_bytes
    keras = _load_keras_module()
    keras.utils.set_random_seed(protocol.seed)
    output.mkdir(exist_ok=False)
    config = replace(demo.load_runtime_demo_config(), demo_scenario_name='normal', demo_scada_mode='match',
                     demo_disable_runtime_autoencoder=True,
                     minio_bucket=demo.load_runtime_demo_config().minio_bucket + '-' + profile)
    if generic_settings is not None:
        config=replace(config,demo_steps=1)
    components = demo.build_demo_runtime_components(config, edge_count=protocol.edge_count)
    simulator_class = OperationalCompressorSimulator
    if protocol.edge_count == 4:
        from parallel_truth_fingerprint.sensor_simulation.mass_flow import MassFlowCompressorSimulator
        simulator_class = MassFlowCompressorSimulator
    if generic_settings is not None:
        from parallel_truth_fingerprint.sensor_simulation.generic_plant import GenericReceiverCompressorSimulator, generic_device_configurations
        simulator=GenericReceiverCompressorSimulator(modulated=profile=='modulated',sample_seconds=5,
            seed=808,internal_substeps=generic_settings['generic_numerical_resolution']['selected_substeps_per_round'])
        devices=generic_device_configurations()
        for edge in components['edges']:
            edge.device_config=devices[edge.device_config.edge_id]
    else:
        simulator = simulator_class(**({'enable_hart_totalizer': True} if hart_totalizer else {}), modulated=profile == 'modulated',
                        sample_seconds=protocol.interval_seconds / config.demo_steps,
                        seed=protocol.simulation_seed if protocol.simulation_seed is not None else protocol.seed)
    components['simulator'] = simulator
    store = PhaseStore(components['artifact_store'])
    sensors = ('temperature','pressure','rpm','mass_flow') if protocol.edge_count == 4 else ('temperature','pressure','rpm')
    display_ranges = {d.sensor_name: d.sensor_range for d in devices.values()} if generic_settings is not None else None
    scada = SequenceReplayScada(sensor_names=sensors, sensor_ranges=display_ranges)
    previous = None
    rows, train, calibration_windows = [], [], []
    model, model_hash, frozen_hash, threshold = None, None, None, None
    summary = {'status': 'running', 'profile': profile, 'completed_rounds': 0,
               'current_noise_configuration': noise_configuration(),
               'parameters': asdict(protocol), 'operational_assumptions': None if generic_settings is not None else asdict(simulator.assumptions),
               'started_at': datetime.now(timezone.utc).isoformat()}

    def weights_hash():
        return hashlib.sha256(b''.join(w.tobytes() for w in model.get_weights())).hexdigest()

    def score(windows):
        if weights_hash() != frozen_hash:
            raise ValueError('Frozen model changed.')
        tensor = np.asarray(windows, dtype='float32')
        with torch.inference_mode():
            reconstructed = keras.ops.convert_to_numpy(model(tensor, training=False))
        scores = np.mean(np.square(reconstructed - tensor), axis=(1, 2))
        if not np.isfinite(scores).all():
            raise ValueError('Invalid MSE.')
        return [float(s) for s in scores]

    sources = []
    try:
        with (output / 'observations.jsonl').open('x', encoding='utf-8') as stream:
            for index, (phase, block, offset) in enumerate(protocol.profile_schedule(), 1):
                started = time.monotonic()
                if offset == 0 and (phase in {'train', 'calibration'} or (phase == 'settle' and block == 1)):
                    previous = None
                if phase == 'source' and offset == 0:
                    sources = []
                simulator.set_demand_target(protocol.demand_target(phase, offset))
                conditioning=None
                if generic_settings is not None and offset==0 and phase in {'train','source'}:
                    print(f'{profile}: conditioning {phase} block={block} (unobserved model time)',flush=True)
                    conditioning=simulator.condition_to_regime()
                if generic_settings is not None:
                    # Unobserved conditioning CPU time must not consume the
                    # cadence budget of the following acquired observation.
                    started = time.monotonic()
                store.phase = phase
                scada.select_phase(phase, offset)  # Always live; attacks exist only in paired audit views.
                acquisition_wall_start = time.perf_counter_ns()
                acquisition_cpu_start = time.process_time_ns()
                acquisition_start = time.time()
                current, comparison, persistence, physical = acquire(index, config, components, store, scada)
                acquisition_end = time.time()
                acquisition_timing = {
                    'wall_seconds': (time.perf_counter_ns()-acquisition_wall_start)/1e9,
                    'cpu_seconds': (time.process_time_ns()-acquisition_cpu_start)/1e9,
                    'wall_clock': 'perf_counter_ns', 'cpu_clock': 'process_time_ns',
                    'scope': 'acquire(): acquisition, pacing waits, MQTT/consensus, comparison, persistence and HART source readback; excludes conditioning and later offline inference',
                }
                if persistence['status'] != 'persisted' or comparison.divergent_sensors:
                    raise RuntimeError('Unmodified current supervisory baseline was not valid.')
                schema, vector = extract_scada_behavioral_feature_vector(current)
                window = build_scoring_window(previous, vector)
                row = {'index': index, 'profile': profile, 'phase': phase, 'block': block, 'offset': offset,
                       'measurement_domain': physical.measurement_domain,
                       'consensus_schema': 'current-consensus-v2',
                       'edge_membership': [edge.runtime_state()['edge_id'] for edge in components['edges']],
                       'consensus_source_edges': list(physical.source_edges),
                       'acquisition_window': {'start_epoch': acquisition_start, 'end_epoch': acquisition_end},
                       'acquisition_timing': acquisition_timing,
                       'round_id': current.source_round_id, 'timestamp': current.timestamp,
                       'physical_scada': current.to_dict(), 'physical_vector': list(vector),
                       'reference_window': window, 'feature_schema': list(schema),
                       'consensused_values': dict(physical.sensor_values),
                       'baseline_persistence': persistence['status'], 'baseline_comparison': comparison.to_dict(),
                       'generation': {'current_noise_configuration': noise_configuration(),
                           'current_noise_multiplier': simulator._control.current_noise_multiplier,
                           'acquisition_snapshot': components['acquisition_snapshot'],
                           'simulation_seconds': simulator.simulation_seconds,
                           'demand_target_pct': simulator.target_demand, 'base_demand_pct': simulator.base_demand,
                           'actual_demand_pct': simulator.current_demand,
                           'latent_engineering_state': dict(simulator.engineering_state)}, 'views': []}
                if hart_totalizer:
                    row['hart_source_evidence'] = components['hart_source_evidence']
                    row['baseline_persisted_artifact_key'] = persistence['artifact_key']
                if generic_settings is not None:
                    row['generation']['generic_conditioning']=conditioning
                if phase == 'source':
                    sources.append(current)
                if phase == 'train' and window is not None:
                    train.append(window)
                if phase == 'calibration' and window is not None:
                    calibration_windows.append(window)
                if phase in {'stable', 'transition'}:
                    if previous is None or len(sources) != protocol.block_rounds:
                        raise ValueError('Missing common physical history or reserved replay source.')
                    historical = sources[offset]
                    replayed = replay_view(current, historical)
                    attack_schema, attack_vector = extract_scada_behavioral_feature_vector(replayed)
                    if attack_schema != schema:
                        raise ValueError('Replay schema mismatch.')
                    windows = [window, build_scoring_window(previous, attack_vector)]
                    scores = score(windows)
                    conditions = ('normal_stable', 'replay_same_regime') if phase == 'stable' else ('legitimate_transition', 'replay_hiding_change')
                    for condition, state, values, input_window, mse in zip(conditions, [current, replayed], [vector, attack_vector], windows, scores):
                        compared = demo.build_scada_comparison_output(demo.compare_consensused_to_scada(valid_state=physical, scada_state=state))
                        attack = state is replayed
                        row['views'].append({'condition': condition, 'is_replay': attack,
                            'scada_state': state.to_dict(), 'historical_state': historical.to_dict() if attack else None,
                            'supervisory_vector': list(values), 'input_window': input_window,
                            'score': mse, 'threshold': threshold, 'anomalous': mse > threshold,
                            'score_to_threshold': mse / threshold, 'model_sha256': model_hash,
                            'comparison': compared.to_dict(),
                            'counterfactual_persistence_blocked': bool(compared.divergent_sensors),
                            'transition_window': offset == 0,
                            'supervisory_write_performed': False})
                stream.write(json.dumps(row, allow_nan=False) + '\n')
                stream.flush()
                os.fsync(stream.fileno())
                rows.append(row)
                previous = vector
                summary['completed_rounds'] = index
                summary['current_phase'] = phase
                save(output / 'summary.json', summary)
                root_summary['completed_rounds'] += 1
                root_summary.update(current_profile=profile, current_phase=phase)
                save(root_output / 'summary.json', root_summary)
                print(f'{profile} {index}/{len(protocol.profile_schedule())} {phase} bloco={block} demanda={simulator.current_demand:.2f}%', flush=True)
                if phase == 'train' and offset == protocol.train_rounds - 1:
                    tensor = np.asarray(train, dtype='float32')
                    np.save(output / 'train-windows.npy', tensor)
                    model = build_lstm_autoencoder(keras=keras, sequence_length=2, feature_count=len(schema), latent_units=protocol.latent_units)
                    history = model.fit(tensor, tensor, epochs=protocol.epochs, batch_size=protocol.batch_size, verbose=0)
                    payload = _export_model_bytes(model, f'paired-{profile}')
                    (output / 'model.keras').write_bytes(payload)
                    model_hash = hashlib.sha256(payload).hexdigest()
                    frozen_hash = weights_hash()
                    save(output / 'model.json', {'sha256': model_hash, 'weights_sha256': frozen_hash,
                        'parameters': asdict(protocol), 'feature_schema': list(schema),
                        'training_windows': len(train), 'training_round_ids': [r['round_id'] for r in rows if r['phase'] == 'train'],
                        'history': history.history, 'architecture': json.loads(model.to_json()),
                        'optimizer': keras.optimizers.serialize(model.optimizer)})
                if phase == 'calibration' and offset == protocol.calibration_rounds - 1:
                    np.save(output / 'calibration-windows.npy', np.asarray(calibration_windows, dtype='float32'))
                    scores = score(calibration_windows)
                    calibrated = fixed_threshold(scores)
                    threshold = calibrated['threshold']
                    save(output / 'calibration.json', dict(calibrated, scores=scores, model_sha256=model_hash,
                         round_ids=[r['round_id'] for r in rows if r['phase'] == 'calibration']))
                if index < len(protocol.profile_schedule()):
                    time.sleep(max(0, protocol.interval_seconds - (time.monotonic() - started)))
        summary['status'] = 'completed'
    except BaseException as error:
        summary.update(status='failed', error=str(error))
        raise
    finally:
        summary['finished_at'] = datetime.now(timezone.utc).isoformat()
        summary['weights_unchanged'] = frozen_hash is not None and frozen_hash == weights_hash()
        summary['final_weights_sha256'] = weights_hash() if frozen_hash is not None else None
        summary['metrics'] = paired_metrics(rows)
        summary['metrics_without_boundary_windows'] = paired_metrics([
            dict(r, views=[v for v in r['views'] if not v['transition_window']]) for r in rows])
        save(output / 'summary.json', summary)
        names = ['observations.jsonl', 'summary.json', 'model.json', 'model.keras', 'calibration.json',
                 'train-windows.npy', 'calibration-windows.npy']
        save(output / 'manifest.json', {n: hashlib.sha256((output / n).read_bytes()).hexdigest()
                                      for n in names if (output / n).exists()})
    return summary


def main():
    parser = argparse.ArgumentParser()
    parser.add_argument('--protocol', type=Path, required=True)
    parser.add_argument('--output', type=Path, default=Path('/results'))
    args = parser.parse_args()
    frozen_protocol = json.loads(args.protocol.read_text(encoding='utf-8'))
    generic=(frozen_protocol.get('version')=='documented-noise-generic-receiver-hart-v1'
             or 'generic_plant_configuration' in frozen_protocol)
    if generic:
        from parallel_truth_fingerprint.evidence.generic_plant import validate_generic_contract
        validate_generic_contract(frozen_protocol,verify_numerics=True)
    from parallel_truth_fingerprint.evidence.hart_totalizer import validate_collection_contract
    hart_totalizer = validate_collection_contract(frozen_protocol)
    if hart_totalizer:
        from parallel_truth_fingerprint.sensor_simulation.mass_flow import validate_totalizer_configuration
        if not generic:
            validate_totalizer_configuration(frozen_protocol['hart_totalizer_configuration'])
        if frozen_protocol['parameters']['edge_count'] != 4:
            raise ValueError('HART totalizer acquisition requires four edges.')
    validate_noise_configuration(frozen_protocol.get('current_noise_configuration'))
    if frozen_protocol.get('current_noise_multiplier') != 1.0:
        raise ValueError('Frozen experiment requires the unscaled reference noise profile.')
    protocol = PairedReplayProtocol(**frozen_protocol['parameters'])
    if protocol.edge_count == 4:
        from parallel_truth_fingerprint.sensor_simulation.mass_flow import MassFlowConfiguration
        if not generic and frozen_protocol.get('mass_flow_configuration') != asdict(MassFlowConfiguration()):
            raise ValueError('Mass-flow configuration differs from frozen protocol.')
    if not generic and frozen_protocol['operational_assumptions'] != asdict(OperationalAssumptions()):
        raise ValueError('Frozen operational assumptions differ from the implementation.')
    root_summary = {'status': 'running', 'completed_rounds': 0, 'expected_rounds': len(protocol.schedule()),
                    'current_noise_configuration': noise_configuration(),
                    'protocol_sha256': hashlib.sha256(args.protocol.read_bytes()).hexdigest(),
                    'started_at': datetime.now(timezone.utc).isoformat(), 'profile_summaries': {},
                    'qualification': 'Two separate model fits with identical hyperparameters; paired dependent observations; approved idealized generic receiver plant.' if generic else 'Two separate model fits with identical hyperparameters; paired dependent observations; uncalibrated process emulation.'}
    try:
        for profile in ('unmodulated', 'modulated'):
            summary = run_profile(profile, protocol, args.output / profile, args.output, root_summary, hart_totalizer=hart_totalizer,
                                  generic_settings=frozen_protocol if generic else None)
            root_summary['profile_summaries'][profile] = summary
        root_summary['status'] = 'completed'
    except BaseException as error:
        root_summary.update(status='failed', error=str(error))
        raise
    finally:
        root_summary['finished_at'] = datetime.now(timezone.utc).isoformat()
        save(args.output / 'summary.json', root_summary)


if __name__ == '__main__':
    main()
