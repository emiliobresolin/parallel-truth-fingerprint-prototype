"""Isolated, exploratory reconstruction diagnostic; never promotes a runtime model."""
from datetime import datetime, timezone
from pathlib import Path
import argparse
import hashlib
import json
import sys

ROOT = Path(__file__).resolve().parents[1]
sys.path.insert(0, str(ROOT / 'src'))


def save(path, value):
    path.write_text(json.dumps(value, indent=2, allow_nan=False), encoding='utf-8')


def source_hashes(root):
    result = {}
    for p in sorted(root.rglob('*')):
        if p.is_file():
            h = hashlib.sha256()
            with p.open('rb') as handle:
                for block in iter(lambda: handle.read(1024*1024), b''):
                    h.update(block)
            result[str(p.relative_to(root))] = h.hexdigest()
    return result


def current_indices(schema):
    indices = [i for i, name in enumerate(schema) if name.endswith('.loop_current_ma')]
    if len(indices) not in (3,4) or len({schema[i] for i in indices}) != len(indices):
        raise ValueError('Expected three or four distinct current channels.')
    if len(indices) == 4 and {schema[i].split('.')[0] for i in indices} != {'temperature','pressure','rpm','mass_flow'}:
        raise ValueError('Four-channel input must include temperature, pressure, rpm and mass_flow.')
    return indices


def prepare(rows, technical=False):
    """Split physical records BEFORE windowing; no shared boundary observation."""
    import numpy as np
    schema = rows[0]['feature_schema']
    indices = current_indices(schema)
    if any(row['feature_schema'] != schema for row in rows):
        raise ValueError('Feature schema changed.')
    reference = [r for r in rows if r['phase'] == 'train']
    calibration_records = [r for r in rows if r['phase'] == 'calibration']
    expected = (16, 12) if technical else (120, 60)
    if (len(reference), len(calibration_records)) != expected:
        raise ValueError('This fixed diagnostic requires 120 training and 60 calibration records.')
    split = int(len(reference) * .6)
    partitions = {'fit': reference[:split], 'validation': reference[split:],
                  'calibration': calibration_records}
    tensors, ids = {}, {}
    for name, records in partitions.items():
        if len(records) < (3 if technical else 8):
            raise ValueError('Insufficient temporal support.')
        vectors = [[(r['physical_vector'][i] - 4.) / 16. for i in indices] for r in records]
        tensors[name] = np.asarray([vectors[i:i+2] for i in range(len(vectors)-1)], dtype='float32')
        ids[name] = [r['round_id'] for r in records]
        if not np.isfinite(tensors[name]).all():
            raise ValueError('Non-finite reference input.')
    if any(set(ids[a]) & set(ids[b]) for a, b in [('fit', 'validation'), ('fit', 'calibration'), ('validation', 'calibration')]):
        raise ValueError('Temporal partition overlap.')
    return indices, tensors, ids


def run_profile(source, output, keras, torch, np, technical=False, prospective=False):
    from parallel_truth_fingerprint.lstm_service.trainer import build_lstm_autoencoder
    from parallel_truth_fingerprint.evidence.replay_evaluation import fixed_threshold
    rows = [json.loads(line) for line in (source/'observations.jsonl').read_text(encoding='utf-8').splitlines()]
    indices, tensors, ids = prepare(rows, technical=technical)
    output.mkdir()
    keras.utils.set_random_seed(101)
    model = build_lstm_autoencoder(keras=keras, sequence_length=2, feature_count=len(indices), latent_units=16)
    stop = keras.callbacks.EarlyStopping(monitor='val_loss', patience=25, min_delta=1e-6, restore_best_weights=True)
    class Progress(keras.callbacks.Callback):
        def on_epoch_end(self, epoch, logs=None):
            if epoch == 0 or (epoch+1) % 25 == 0:
                print(f'{source.name}: epoch={epoch+1} loss={logs["loss"]:.8f} val={logs["val_loss"]:.8f}', flush=True)
    history = model.fit(tensors['fit'], tensors['fit'], validation_data=(tensors['validation'], tensors['validation']),
                        epochs=1 if technical else 300, batch_size=8, shuffle=False, verbose=0, callbacks=[stop, Progress()])
    def score(tensor):
        tensor = np.asarray(tensor, dtype='float32')
        with torch.inference_mode():
            prediction = keras.ops.convert_to_numpy(model(tensor, training=False))
        result = np.mean(np.square(prediction-tensor), axis=(1, 2))
        if not np.isfinite(result).all():
            raise ValueError('Non-finite scores.')
        return result
    mean = tensors['fit'].mean(axis=(0, 1))
    diagnostics = {name: {'windows': len(x), 'model_mse': float(score(x).mean()),
                         'constant_fit_mean_mse': float(np.square(x-mean).mean())} for name, x in tensors.items()}
    calibration_scores = score(tensors['calibration']).tolist()
    calibration = fixed_threshold(calibration_scores)
    # Only now touch attack/test windows. No model or threshold selection follows.
    views = [v for r in rows for v in r['views']]
    test = np.asarray([[[(sample[i]-4.)/16. for i in indices] for sample in v['input_window']] for v in views], dtype='float32')
    scores = score(test)
    records = [{'round_id': r['round_id'], 'block': r['block'], 'condition': v['condition'],
                'score': float(s), 'anomalous': bool(s > calibration['threshold']),
                'original_score': v['score'], 'original_anomalous': v['anomalous']}
               for (r, v), s in zip([(r, v) for r in rows for v in r['views']], scores)]
    metrics = {}
    for condition in sorted({v['condition'] for v in records}):
        selected = [v for v in records if v['condition'] == condition]
        metrics[condition] = {'count': len(selected), 'alerts': sum(v['anomalous'] for v in selected),
                              'alert_rate': sum(v['anomalous'] for v in selected)/len(selected),
                              'score_mean': float(np.mean([v['score'] for v in selected]))}
    save(output/'history.json', history.history)
    save(output/'partitions.json', ids)
    save(output/'calibration.json', dict(calibration, scores=calibration_scores))
    save(output/'scores.json', records)
    save(output/'architecture.json', json.loads(model.to_json()))
    model.save_weights(str(output/'model.weights.h5'))
    for name, tensor in tensors.items():
        np.save(output/f'{name}.npy', tensor)
    summary = {'profile': source.name, 'epochs_completed': len(history.history['loss']),
               'selected_epoch': int(stop.best_epoch)+1, 'diagnostics': diagnostics,
               'threshold': calibration['threshold'], 'metrics': metrics,
               'features': [rows[0]['feature_schema'][i] for i in indices],
               'qualification': ('Technical verification only.' if technical else
                   'Prospective exploratory repetition with fixed recipe; paired two-step windows unchanged.' if prospective else
                   'Exploratory reuse of an already inspected test; paired two-step windows unchanged; not independent confirmation.')}
    save(output/'summary.json', summary)
    return summary


def main():
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument('--source', type=Path, required=True)
    parser.add_argument('--output', type=Path, help='Fresh directory, outside the source session.')
    parser.add_argument('--smoke', action='store_true', help='Technical path verification only: reduced support and one epoch.')
    parser.add_argument('--prospective', action='store_true', help='Declare fresh collection under the fixed confirmation workflow.')
    args = parser.parse_args()
    source = args.source.resolve()
    from parallel_truth_fingerprint.evidence.paired_replay import PairedReplayProtocol, verify_paired_results
    protocol = json.loads((source/'protocol.json').read_text(encoding='utf-8'))
    verify_paired_results(source, PairedReplayProtocol(**protocol['parameters']))
    hashes = source_hashes(source)
    output = ROOT/'output'/'offline-replay-training'/datetime.now(timezone.utc).strftime('%Y%m%dT%H%M%S%fZ')
    if args.output is not None:
        output = args.output.resolve()
    if output == source or source in output.parents or output in source.parents:
        raise ValueError('Source and output directories must be separate, without containment.')
    output.mkdir(parents=True, exist_ok=False)
    save(output/'protocol.json', {'source': str(source), 'seed': 101, 'fit_fraction': .6, 'sequence_length': 2,
         'features': 'Acquired current channels only, scaled by fixed (mA-4)/16, no clipping',
         'mode': 'technical-smoke' if args.smoke else 'prospective-exploratory-repetition' if args.prospective else 'exploratory',
         'max_epochs': 1 if args.smoke else 300, 'patience': 25, 'min_delta': 1e-6, 'shuffle': False,
         'batch_size': 8, 'latent_units': 16,
         'threshold': 'Calibration mean + 3 population std; unchanged rule',
         'test_policy': 'Fixed recipe; no tuning against test metrics. Fresh collection.' if args.prospective else
                        'Already inspected test is exploratory only; no tuning against its metrics'})
    save(output/'source-hashes.json', hashes)
    print(f'Results: {output}', flush=True)
    summary = {'status': 'running', 'profiles': {}, 'started_at': datetime.now(timezone.utc).isoformat()}
    try:
        import numpy as np
        import torch
        torch.set_num_threads(1)
        from parallel_truth_fingerprint.lstm_service.trainer import _load_keras_module
        keras = _load_keras_module()
        save(output/'environment.json', {'python': sys.version, 'numpy': np.__version__, 'torch': torch.__version__, 'keras': keras.__version__})
        for name in ('unmodulated', 'modulated'):
            summary['profiles'][name] = run_profile(source/name, output/name, keras, torch, np,
                                                    technical=args.smoke, prospective=args.prospective)
        if source_hashes(source) != hashes:
            raise ValueError('Source artifacts changed during offline evaluation.')
        summary.update(status='completed', source_unchanged=True)
    except BaseException as error:
        summary.update(status='failed', error=str(error))
        raise
    finally:
        summary['finished_at'] = datetime.now(timezone.utc).isoformat()
        save(output/'summary.json', summary)
        save(output/'manifest.json', source_hashes(output))
    print(json.dumps(summary, indent=2), flush=True)


if __name__ == '__main__':
    main()
