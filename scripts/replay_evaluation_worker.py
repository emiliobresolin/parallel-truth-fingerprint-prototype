"""Live acquisition and fixed-model evaluation inside the isolated Linux container."""
from __future__ import annotations

import argparse
from dataclasses import asdict, replace
from datetime import datetime, timezone
import hashlib
import json
import os
from pathlib import Path
import sys
import time

ROOT = Path(__file__).resolve().parents[1]
sys.path.insert(0, str(ROOT / 'src'))
sys.path.insert(0, str(ROOT / 'scripts'))
import run_local_demo as demo
from parallel_truth_fingerprint.evidence.replay_evaluation import (
    ReplayProtocol, SequenceReplayScada, PhaseStore, build_scoring_window, fixed_threshold, summarize_scores,
)
from parallel_truth_fingerprint.lstm_service.replay_behavior import extract_scada_behavioral_feature_vector


def save(path, payload):
    temporary = path.with_suffix('.tmp')
    temporary.write_text(json.dumps(payload, indent=2, allow_nan=False) + '\n', encoding='utf-8')
    temporary.replace(path)


def acquire(index, config, components, store, scada):
    """Reuse acquisition, real MQTT/CometBFT and unchanged persistence gate, without legacy lifecycle."""
    simulator, edges, client = (components[k] for k in ('simulator', 'edges', 'cometbft_client'))
    for _ in range(config.demo_steps):
        snapshot = simulator.step(compressor_power=config.demo_power)
        for edge in edges:
            payload = edge.acquire(snapshot=snapshot)
            edge.publish_local_observation(payload, topic=config.mqtt_topic)
        time.sleep(0.2)
    components['acquisition_snapshot'] = snapshot.to_dict()
    time.sleep(1.0)
    round_input = demo.build_consensus_round_input(edges)
    receipt = client.broadcast_round(round_input)
    committed = client.query_committed_round(receipt.round_id)
    audit = demo.committed_round_to_audit_package(round_input, committed)
    if audit.consensused_valid_state is None:
        raise RuntimeError('No trusted physical state; abort instead of silently omitting a round.')
    scada.clear_overrides()
    state, comparison_stage, comparison, alert, persistence = demo.run_scada_comparison_and_persistence(
        consensus_audit=audit, artifact_store=store, scada_service=scada,
        campaign_id=config.demo_campaign_id,
    )
    if state is None or comparison is None:
        raise RuntimeError('Missing supervisory comparison.')
    if persistence['status'] not in {'persisted', 'blocked'}:
        raise RuntimeError(f'Persistence error: {persistence}')
    if persistence['status'] == 'blocked' and not comparison.divergent_sensors:
        raise RuntimeError('Unexpected persistence block.')
    if snapshot.metadata.get('hart_totalizer_configuration') is not None:
        if persistence['status'] != 'persisted':
            raise RuntimeError('HART reference requires a persisted selected source.')
        from parallel_truth_fingerprint.evidence.hart_totalizer import build_source_evidence
        persisted = store.load_json(persistence['artifact_key'])
        components['hart_source_evidence'] = build_source_evidence(
            audit.round_input, audit.consensused_valid_state, persisted,
            include_all_sensors='generic_plant_configuration' in snapshot.metadata)
    return state, comparison, persistence, audit.consensused_valid_state


def main():
    parser = argparse.ArgumentParser()
    parser.add_argument('--protocol', type=Path, required=True)
    parser.add_argument('--output', type=Path, default=Path('/results'))
    args = parser.parse_args()
    protocol_payload = json.loads(args.protocol.read_text(encoding='utf-8'))
    from parallel_truth_fingerprint.sensor_simulation.current_noise import validate_noise_configuration
    validate_noise_configuration(protocol_payload.get('current_noise_configuration'))
    if protocol_payload.get('current_noise_multiplier') != 1.0:
        raise ValueError('Frozen experiment requires the unscaled reference noise profile.')
    protocol = ReplayProtocol(**protocol_payload['parameters'])
    schedule = protocol.schedule()
    output = args.output
    output.mkdir(parents=True, exist_ok=True)
    import numpy as np
    import torch
    torch.set_num_threads(1)
    from parallel_truth_fingerprint.lstm_service.trainer import (
        _load_keras_module, build_lstm_autoencoder, _export_model_bytes,
    )
    keras = _load_keras_module()
    keras.utils.set_random_seed(protocol.seed)
    config = replace(demo.load_runtime_demo_config(), demo_scenario_name='normal',
                     demo_scada_mode='match', demo_disable_runtime_autoencoder=True)
    components = demo.build_demo_runtime_components(config)
    store = PhaseStore(components['artifact_store'])
    scada = SequenceReplayScada()
    train_windows, calibration_windows, rows = [], [], []
    phase_counts = {}
    previous_physical = None
    previous_phase = None
    model = None
    threshold = None
    model_hash = None
    frozen_weights_hash = None
    score_schema = None
    summary = {'status': 'running', 'completed_rounds': 0, 'expected_rounds': len(schedule),
               'protocol_sha256': hashlib.sha256(args.protocol.read_bytes()).hexdigest(),
               'started_at': datetime.now(timezone.utc).isoformat(), 'parameters': asdict(protocol),
               'evaluation_branch': 'score recorded independently of unchanged persistence block',
               'independent_training_runs': 1}

    def weights_hash():
        return hashlib.sha256(b''.join(w.tobytes() for w in model.get_weights())).hexdigest()

    def score(windows):
        if weights_hash() != frozen_weights_hash:
            raise ValueError('Frozen model weights changed during evaluation.')
        tensor = np.asarray(windows, dtype='float32')
        with torch.inference_mode():
            reconstruction = keras.ops.convert_to_numpy(model(tensor, training=False))
        values = np.mean(np.square(reconstruction - tensor), axis=(1, 2))
        if not np.isfinite(values).all():
            raise ValueError('Non-finite reconstruction scores.')
        return [float(s) for s in values]

    try:
        with (output / 'observations.jsonl').open('x', encoding='utf-8') as stream:
            for index, (phase, block, offset) in enumerate(schedule, 1):
                started = time.monotonic()
                # Partition boundaries have no shared physical timestep.
                if phase != previous_phase and phase in {'calibration', 'normal'} and block <= 1:
                    previous_physical = None
                scada.select_phase(phase, offset)
                store.phase = phase
                state, comparison, persistence, physical = acquire(index, config, components, store, scada)
                physical_schema, physical_vector = extract_scada_behavioral_feature_vector(scada.physical_state)
                schema, supervisory_vector = extract_scada_behavioral_feature_vector(state)
                if schema != physical_schema or (score_schema is not None and schema != score_schema):
                    raise ValueError('Feature schema changed.')
                score_schema = schema
                window = build_scoring_window(previous_physical, supervisory_vector)
                transition = phase != previous_phase
                row = {
                    'acquisition_snapshot': components['acquisition_snapshot'],
                    'index': index, 'round_id': state.source_round_id, 'timestamp': state.timestamp,
                    'phase': phase, 'block': block, 'offset': offset, 'transition': transition,
                    'warmup': window is None, 'feature_schema': list(schema),
                    'current_physical_vector': list(physical_vector),
                    'current_supervisory_vector': list(supervisory_vector), 'input_window': window,
                    'physical_state': scada.physical_state.to_dict(), 'scada_state': state.to_dict(),
                    'replay_original_state': scada.original_state.to_dict() if scada.original_state else None,
                    'comparison': comparison.to_dict(), 'persistence_status': persistence['status'],
                    'persisted_artifact_key': persistence.get('artifact_key'),
                    'consensused_physical_values': dict(physical.sensor_values),
                    'score': None, 'threshold': threshold, 'anomalous': None, 'model_sha256': model_hash,
                }
                if phase == 'train' and window is not None:
                    train_windows.append(window)
                elif phase == 'calibration' and window is not None:
                    calibration_windows.append(window)
                elif phase in {'normal', 'replay', 'recovery'} and window is not None:
                    row['score'] = score([window])[0]
                    row['anomalous'] = row['score'] > threshold
                    row['score_to_threshold'] = row['score'] / threshold
                stream.write(json.dumps(row, allow_nan=False) + '\n')
                stream.flush()
                os.fsync(stream.fileno())
                rows.append(row)
                phase_counts[phase] = phase_counts.get(phase, 0) + 1
                summary.update(completed_rounds=index, phase_counts=phase_counts, current_phase=phase)
                save(output / 'summary.json', summary)
                print(f'{index}/{len(schedule)} {phase} bloco={block} score={row["score"]} limiar={threshold}', flush=True)
                previous_physical, previous_phase = physical_vector, phase
                if phase == 'train' and offset == protocol.train_rounds - 1:
                    tensor = np.asarray(train_windows, dtype='float32')
                    np.save(output / 'train-windows.npy', tensor)
                    model = build_lstm_autoencoder(keras=keras, sequence_length=2,
                            feature_count=len(schema), latent_units=protocol.latent_units)
                    fit_start = time.monotonic()
                    history = model.fit(tensor, tensor, epochs=protocol.epochs,
                                        batch_size=protocol.batch_size, verbose=0)
                    model_bytes = _export_model_bytes(model, 'fixed-replay-model')
                    (output / 'model.keras').write_bytes(model_bytes)
                    model_hash = hashlib.sha256(model_bytes).hexdigest()
                    frozen_weights_hash = weights_hash()
                    save(output / 'model.json', {'sha256': model_hash, 'parameters': asdict(protocol),
                        'weights_sha256': frozen_weights_hash,
                        'feature_schema': list(schema), 'training_windows': len(train_windows),
                        'training_round_ids': [r['round_id'] for r in rows if r['phase'] == 'train'],
                        'history': history.history, 'optimizer': keras.optimizers.serialize(model.optimizer),
                        'architecture': json.loads(model.to_json()),
                        'fit_seconds': time.monotonic() - fit_start,
                        'preprocessing': 'mA, (mA-4)/16 and three boolean diagnostics per sensor; no extra scaling'})
                if phase == 'calibration' and offset == protocol.calibration_rounds - 1:
                    np.save(output / 'calibration-windows.npy', np.asarray(calibration_windows, dtype='float32'))
                    calibration_scores = score(calibration_windows)
                    calibrated = fixed_threshold(calibration_scores)
                    threshold = calibrated['threshold']
                    save(output / 'calibration.json', dict(calibrated, scores=calibration_scores,
                         scoring_round_ids=[r['round_id'] for r in rows if r['phase'] == 'calibration' and not r['warmup']],
                         model_sha256=model_hash, independent_of_training_timesteps=True))
                if index < len(schedule):
                    time.sleep(max(0, protocol.interval_seconds - (time.monotonic() - started)))
        summary['status'] = 'completed'
    except BaseException as error:
        summary.update(status='interrupted' if isinstance(error, KeyboardInterrupt) else 'failed', error=str(error))
        raise
    finally:
        if frozen_weights_hash:
            summary['final_weights_sha256'] = weights_hash()
            summary['weights_unchanged'] = weights_hash() == frozen_weights_hash
        summary['finished_at'] = datetime.now(timezone.utc).isoformat()
        summary['metrics_all_scored'] = summarize_scores(rows)
        summary['metrics_without_transitions'] = summarize_scores(rows, exclude_transitions=True)
        delays = []
        for block in range(1, protocol.repetitions + 1):
            attack = [r for r in rows if r['phase'] == 'replay' and r['block'] == block]
            detected = next((r for r in attack if r['anomalous']), None)
            delays.append({'block': block, 'observed_replay_rounds': len(attack),
                'first_detection_offset_rounds': detected['offset'] if detected else None,
                'first_detection_delay_seconds': (datetime.fromisoformat(detected['timestamp']) - datetime.fromisoformat(attack[0]['timestamp'])).total_seconds() if detected else None})
        summary['replay_blocks'] = delays
        save(output / 'summary.json', summary)
        files = [output / name for name in ('observations.jsonl', 'summary.json', 'model.json',
                 'model.keras', 'calibration.json', 'train-windows.npy', 'calibration-windows.npy', 'protocol.json')
                 if (output / name).is_file()]
        save(output / 'manifest.json', {p.name: hashlib.sha256(p.read_bytes()).hexdigest() for p in files})


if __name__ == '__main__':
    main()
