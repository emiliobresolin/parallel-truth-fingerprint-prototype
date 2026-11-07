"""Fit documented HART increment inputs and matched current-only ablation."""
from datetime import datetime, timezone
from pathlib import Path
import argparse
import hashlib
import json
import sys
import time

ROOT = Path(__file__).resolve().parents[1]
sys.path[:0] = [str(ROOT/'src'), str(ROOT/'scripts')]
from parallel_truth_fingerprint.evidence.hart_totalizer import FEATURES, prepare, matched_currents
from parallel_truth_fingerprint.evidence.contextual_replay import metrics
from parallel_truth_fingerprint.evidence.replay_calibration import COMMON, calibrate, anomalous
from parallel_truth_fingerprint.sensor_simulation.mass_flow import totalizer_configuration
from evaluate_replay_training_offline import source_hashes, save


def digest(path):
    return hashlib.sha256(Path(path).read_bytes()).hexdigest()


def weight_hash(model):
    return hashlib.sha256(b''.join(w.tobytes() for w in model.get_weights())).hexdigest()


def evaluate_components(model, tensor, keras, torch, np):
    x = np.asarray(tensor, dtype='float32')
    if x.ndim != 3 or x.shape[1] != 2 or x.shape[2] not in (8, 10) or not np.isfinite(x).all():
        raise ValueError('Expected finite two-step HART or matched-current windows.')
    with torch.inference_mode():
        predicted = keras.ops.convert_to_numpy(model(x, training=False))
    error = predicted.astype('float64')-x.astype('float64')
    half = x.shape[2]//2
    ep, es = error[:, :, :half], error[:, :, half:]
    direct = (x[:, :, :half].astype('float64')-x[:, :, half:].astype('float64'))/2
    values = {'global_mse': np.mean(error**2, axis=(1, 2)),
              'common_error': np.mean(((ep+es)/2)**2, axis=(1, 2)),
              'relational_error': np.mean(((ep-es)/2)**2, axis=(1, 2)),
              'direct_gap': np.mean(direct**2, axis=(1, 2))}
    if any(not np.isfinite(v).all() for v in values.values()):
        raise ValueError('Nonfinite HART reconstruction score.')
    return values


def variants(tensors, examples, np, variant):
    transform = (lambda w: w) if variant == 'hart_totalizer' else matched_currents
    data = {phase: np.asarray([transform(w) for w in windows], dtype='float32')
            for phase, windows in tensors.items()}
    test = np.asarray([transform(e['input_window']) for e in examples], dtype='float32')
    return data, test


def timed_components(model, tensor, keras, torch, np):
    wall, cpu = time.perf_counter_ns(), time.process_time_ns()
    values = evaluate_components(model, tensor, keras, torch, np)
    wall_seconds = (time.perf_counter_ns()-wall)/1e9
    return values, {'windows': len(tensor), 'wall_seconds': wall_seconds,
        'cpu_seconds': (time.process_time_ns()-cpu)/1e9,
        'amortized_milliseconds_per_window': 1000*wall_seconds/len(tensor),
        'scope': 'batch tensor conversion, model reconstruction and four scores; excludes acquisition, threshold decisions and persistence',
        'wall_clock': 'perf_counter_ns', 'cpu_clock': 'process_time_ns'}


def fit_variant(output, tensors, examples, lineage, reference_mass, *, variant, technical, keras, torch, np, seed=101):
    from parallel_truth_fingerprint.lstm_service.trainer import build_lstm_autoencoder
    output.mkdir(parents=True, exist_ok=False)
    data, test = variants(tensors, examples, np, variant)
    keras.utils.set_random_seed(seed)
    training_wall, training_cpu = time.perf_counter_ns(), time.process_time_ns()
    model = build_lstm_autoencoder(keras=keras, sequence_length=2, feature_count=data['fit'].shape[2], latent_units=16)
    stop = keras.callbacks.EarlyStopping(monitor='val_loss', patience=25, min_delta=1e-6, restore_best_weights=True)
    history = model.fit(data['fit'], data['fit'], validation_data=(data['validation'], data['validation']),
                        epochs=1 if technical else 300, batch_size=8, shuffle=False, verbose=0, callbacks=[stop])
    training_timing = {'wall_seconds': (time.perf_counter_ns()-training_wall)/1e9,
        'cpu_seconds': (time.process_time_ns()-training_cpu)/1e9,
        'scope': 'model construction, normal-only fit, validation selection and best-weight restoration',
        'wall_clock': 'perf_counter_ns', 'cpu_clock': 'process_time_ns'}
    frozen = weight_hash(model)
    cal, calibration_timing = timed_components(model, data['calibration'], keras, torch, np)
    thresholds = {name: dict(calibrate(value.tolist(), COMMON), scores=value.tolist()) for name, value in cal.items()}
    # No attack/test tensor is used for choosing weights or calibration thresholds.
    values, test_timing = timed_components(model, test, keras, torch, np)
    records = []
    for i, example in enumerate(examples):
        row = {k: v for k, v in example.items() if k != 'input_window'}
        row['input_window'] = test[i].tolist()
        for method, scores in values.items():
            row[method+'_score'] = float(scores[i])
            row[method+'_anomalous'] = anomalous(scores[i], thresholds[method]['threshold'], COMMON)
        records.append(row)
    if frozen != weight_hash(model):
        raise ValueError('HART model weights changed during evaluation.')
    methods = {name: name+'_anomalous' for name in values}
    methods['comparator'] = 'comparator_anomalous'
    selected_features = list(FEATURES) if variant == 'hart_totalizer' else [FEATURES[i] for i in (*range(4), *range(5, 9))]
    summary = {'variant': variant, 'features': selected_features,
               'training_seed': seed,
               'timing': {'training': training_timing, 'calibration_batch': calibration_timing, 'test_batch': test_timing},
               'epochs_completed': len(history.history['loss']), 'selected_epoch': int(stop.best_epoch)+1,
               'weights_sha256': frozen, 'weights_unchanged': True,
               'reference_mass_kg': reference_mass,
               'partition_windows': {name: len(value) for name, value in data.items()},
               'metrics': {method: metrics(records, key) for method, key in methods.items()},
               'thresholds': {method: entry['threshold'] for method, entry in thresholds.items()},
               'warmup': 'First two records of every partition/episode omitted uniformly; within-episode increments only.'}
    save(output/'architecture.json', json.loads(model.to_json()))
    model.save_weights(str(output/'model.weights.h5'))
    save(output/'partitions.json', lineage)
    save(output/'history.json', history.history)
    save(output/'calibration.json', thresholds)
    save(output/'scores.json', records)
    save(output/'summary.json', summary)
    for phase, tensor in data.items():
        np.save(output/f'{phase}.npy', tensor)
    return summary


def verify_output(output):
    """Rebuild from recorded SVs and reproduce frozen predictions and decisions."""
    import numpy as np
    import torch
    torch.set_num_threads(1)
    from parallel_truth_fingerprint.lstm_service.trainer import _load_keras_module
    from parallel_truth_fingerprint.evidence.paired_replay import PairedReplayProtocol
    from run_replay_evaluation import verify_results
    keras = _load_keras_module()
    output = Path(output)
    for name, expected in json.loads((output/'manifest.json').read_text()).items():
        if digest(output/name) != expected:
            raise ValueError('HART output hash mismatch.')
    protocol = json.loads((output/'protocol.json').read_text())
    if protocol['version'] not in ('hart-totalizer-matched-evaluation-v1', 'hart-totalizer-matched-evaluation-v2'):
        raise ValueError('Unrecognized HART evaluation contract.')
    allowed_seeds = (101,) if protocol['version'].endswith('-v1') else (101,211,307,419,523)
    if (protocol.get('features') != list(FEATURES) or protocol.get('seed') not in allowed_seeds
            or protocol.get('sequence_length') != 2 or protocol.get('fit_fraction') != .6
            or protocol.get('calibration_rule') != COMMON or protocol.get('target_normal_fpr') != .01
            or protocol.get('latent_units') != 16 or protocol.get('batch_size') != 8
            or protocol.get('patience') != 25 or protocol.get('min_delta') != 1e-6
            or protocol.get('shuffle') is not False
            or protocol.get('max_epochs') != (1 if protocol.get('technical_smoke') else 300)):
        raise ValueError('HART feature/training/calibration recipe differs from the fixed contract.')
    source = Path(protocol['source_collection'])
    if source_hashes(source) != json.loads((output/'source-hashes.json').read_text()):
        raise ValueError('HART source collection changed.')
    frozen = json.loads((source/'protocol.json').read_text())
    from parallel_truth_fingerprint.evidence.hart_totalizer import validate_collection_contract
    validate_collection_contract(frozen)
    if protocol['hart_totalizer_configuration']!=frozen.get('hart_totalizer_configuration'):
        raise ValueError('Evaluation counter recipe differs from its verified acquired source.')
    verify_results(source, PairedReplayProtocol(**frozen['parameters']))
    summary = json.loads((output/'summary.json').read_text())
    if summary['status'] != 'completed' or not summary['source_unchanged']:
        raise ValueError('HART evaluation incomplete.')
    for profile in ('unmodulated', 'modulated'):
        rows = [json.loads(line) for line in (source/profile/'observations.jsonl').read_text().splitlines()]
        tensors, lineage, examples, reference = prepare(rows, frozen, technical=protocol['technical_smoke'])
        matched_ids = None
        for variant in ('hart_totalizer', 'currents_only'):
            folder = output/profile/variant
            data, test = variants(tensors, examples, np, variant)
            if json.loads((folder/'partitions.json').read_text()) != lineage:
                raise ValueError('HART partition lineage changed.')
            for phase, tensor in data.items():
                if not np.array_equal(tensor, np.load(folder/f'{phase}.npy')):
                    raise ValueError('HART tensor differs from acquired raw SV/current lineage.')
            records = json.loads((folder/'scores.json').read_text())
            if len(records) != len(examples) or not np.array_equal(test, np.asarray([r['input_window'] for r in records], dtype='float32')):
                raise ValueError('HART test tensor differs from episode-local construction.')
            for record, example in zip(records, examples):
                if any(record.get(k) != v for k, v in example.items() if k != 'input_window'):
                    raise ValueError('HART test lineage or comparator changed.')
            ids = [(r['round_id'], r['condition'], r['offset']) for r in records]
            if matched_ids is not None and ids != matched_ids:
                raise ValueError('HART and current-only evaluations use different observations.')
            matched_ids = ids
            model = keras.models.model_from_json((folder/'architecture.json').read_text())
            model.load_weights(str(folder/'model.weights.h5'))
            actual = json.loads((folder/'summary.json').read_text())
            if protocol['version'].endswith('-v2'):
                if actual.get('training_seed') != protocol['seed']:
                    raise ValueError('HART summary seed differs from frozen protocol.')
                timing = actual['timing']
                for entry in timing.values():
                    if any(not np.isfinite(entry[key]) or entry[key]<0 for key in ('wall_seconds','cpu_seconds')):
                        raise ValueError('Invalid HART timing duration.')
                if timing['test_batch']['windows'] != len(examples) or timing['calibration_batch']['windows'] != len(data['calibration']):
                    raise ValueError('HART timing window support differs.')
            expected_features = list(FEATURES) if variant == 'hart_totalizer' else [FEATURES[i] for i in (*range(4), *range(5, 9))]
            if (actual.get('features') != expected_features or actual.get('variant') != variant
                    or actual.get('partition_windows') != {key: len(value) for key, value in data.items()}):
                raise ValueError('HART summary input schema or support differs from rebuilt tensors.')
            if weight_hash(model) != actual['weights_sha256'] or not actual['weights_unchanged'] or actual['reference_mass_kg'] != reference:
                raise ValueError('Frozen HART model or scaling changed.')
            cal = json.loads((folder/'calibration.json').read_text())
            cal_values = evaluate_components(model, data['calibration'], keras, torch, np)
            test_values = evaluate_components(model, test, keras, torch, np)
            for method, values in cal_values.items():
                expected = calibrate(values.tolist(), COMMON)
                if not np.allclose(values, cal[method]['scores'], rtol=1e-8, atol=1e-12) or expected['threshold'] != cal[method]['threshold']:
                    raise ValueError('HART calibration does not reproduce normal-only threshold.')
                if actual['thresholds'][method] != expected['threshold']:
                    raise ValueError('HART summary threshold mismatch.')
                for i, record in enumerate(records):
                    if not np.isclose(record[method+'_score'], test_values[method][i], rtol=1e-8, atol=1e-12) or record[method+'_anomalous'] != anomalous(test_values[method][i], expected['threshold'], COMMON):
                        raise ValueError('HART prediction or decision does not reproduce.')
                if actual['metrics'][method] != metrics(records, method+'_anomalous'):
                    raise ValueError('HART metrics do not reproduce individual decisions.')
            if actual['metrics']['comparator'] != metrics(records, 'comparator_anomalous') or summary['profiles'][profile][variant] != actual:
                raise ValueError('HART comparator or root summary mismatch.')
    return summary


def evaluate_collection(source, output, *, technical=False, seed=101, versioned_seed=False):
    if seed not in (101,211,307,419,523):
        raise ValueError('Unsupported fixed training seed.')
    if not versioned_seed and seed != 101:
        raise ValueError('Alternative seeds require the versioned seed contract.')
    import numpy as np
    import torch
    torch.set_num_threads(1)
    from parallel_truth_fingerprint.lstm_service.trainer import _load_keras_module
    from parallel_truth_fingerprint.evidence.paired_replay import PairedReplayProtocol
    from run_replay_evaluation import verify_results
    keras = _load_keras_module()
    source, output = Path(source).resolve(), Path(output).resolve()
    if output == source or source in output.parents or output in source.parents:
        raise ValueError('HART evaluation and source must have separate directories.')
    frozen = json.loads((source/'protocol.json').read_text())
    verify_results(source, PairedReplayProtocol(**frozen['parameters']))
    before = source_hashes(source)
    output.mkdir(parents=True, exist_ok=False)
    protocol = {'version': 'hart-totalizer-matched-evaluation-v2' if versioned_seed else 'hart-totalizer-matched-evaluation-v1', 'source_collection': str(source),
        'hart_totalizer_configuration': frozen['hart_totalizer_configuration'], 'technical_smoke': technical,
        'measurement_domain': 'loop_current_ma', 'auxiliary_measurement_domain': 'hart_totalizer_mass_kg',
        'feature_unit': 'dimensionless after per-field documented normalization',
        'seed': seed, 'sequence_length': 2, 'features': list(FEATURES),
        'fit_fraction': .6, 'max_epochs': 1 if technical else 300, 'patience': 25,
        'min_delta': 1e-6, 'batch_size': 8, 'latent_units': 16, 'shuffle': False,
        'calibration_rule': COMMON, 'target_normal_fpr': .01,
        'normalization': 'currents=(mA-4)/16; delta mass/(configured upper kg/h * nominal interval/3600)',
        'warmup': 'Drop first two observations of every partition and condition/block before scoring.',
        'selection': 'Normal validation only; fixed inputs/recipe; preserve every test outcome.'}
    save(output/'protocol.json', protocol)
    save(output/'source-hashes.json', before)
    summary = {'status': 'running', 'profiles': {}, 'started_at': datetime.now(timezone.utc).isoformat()}
    save(output/'summary.json', summary)
    for profile in ('unmodulated', 'modulated'):
        rows = [json.loads(line) for line in (source/profile/'observations.jsonl').read_text().splitlines()]
        tensors, lineage, examples, reference = prepare(rows, frozen, technical=technical)
        summary['profiles'][profile] = {}
        for variant in ('hart_totalizer', 'currents_only'):
            print(f'{profile}: training {variant}, features={10 if variant=="hart_totalizer" else 8}', flush=True)
            summary['profiles'][profile][variant] = fit_variant(output/profile/variant, tensors, examples, lineage, reference,
                variant=variant, technical=technical, keras=keras, torch=torch, np=np, seed=seed)
    summary.update(status='completed', source_unchanged=source_hashes(source)==before,
                   finished_at=datetime.now(timezone.utc).isoformat())
    if not summary['source_unchanged']:
        raise ValueError('HART collection changed during training.')
    save(output/'summary.json', summary)
    save(output/'manifest.json', {str(p.relative_to(output)): digest(p) for p in output.rglob('*') if p.is_file()})
    verify_output(output)
    print('HART totalizer and matched ablation independently verified.', flush=True)
    return summary


def main():
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument('--source', type=Path, required=True)
    parser.add_argument('--output', type=Path, required=True)
    parser.add_argument('--smoke', action='store_true')
    parser.add_argument('--seed', type=int, choices=(101,211,307,419,523))
    args = parser.parse_args()
    evaluate_collection(args.source,args.output,technical=args.smoke,
        seed=101 if args.seed is None else args.seed,versioned_seed=args.seed is not None)


if __name__ == '__main__':
    main()
