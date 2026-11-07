"""Collect fresh paired observations, then apply the fixed corrected training recipe."""
from datetime import datetime, timezone
from pathlib import Path
import argparse
import ctypes
import hashlib
import json
import os
import subprocess
import sys

ROOT = Path(__file__).resolve().parents[1]
sys.path.insert(0, str(ROOT/'src'))
from parallel_truth_fingerprint.sensor_simulation.current_noise import noise_configuration


def save(path, value):
    path.write_text(json.dumps(value, indent=2, allow_nan=False), encoding='utf-8')


def verify_training(root):
    """Verify frozen outputs and compare their source hashes after collection stopped."""
    import math
    import statistics
    from parallel_truth_fingerprint.evidence.paired_syscalls import digest as file_digest
    frozen = json.loads((root/'protocol.json').read_text(encoding='utf-8'))
    if frozen.get('version', '').startswith('documented-noise-'):
        from parallel_truth_fingerprint.sensor_simulation.current_noise import validate_noise_configuration
        collected = json.loads((root/'collection/protocol.json').read_text(encoding='utf-8'))
        validate_noise_configuration(frozen.get('current_noise_configuration'))
        if (collected.get('current_noise_configuration') != frozen['current_noise_configuration']
                or frozen.get('current_noise_multiplier') != 1.0
                or collected.get('current_noise_multiplier') != frozen['current_noise_multiplier']):
            raise ValueError('Confirmation and collection noise protocols differ.')
    training = root/'training'
    for name, digest in json.loads((training/'manifest.json').read_text()).items():
        if file_digest(training/name) != digest:
            raise ValueError(f'Training artifact changed: {name}')
    for name, digest in json.loads((training/'source-hashes.json').read_text()).items():
        if file_digest(root/'collection'/name) != digest:
            raise ValueError(f'Collection artifact changed: {name}')
    result = json.loads((training/'summary.json').read_text())
    if result['status'] != 'completed' or not result['source_unchanged']:
        raise ValueError('Corrected training incomplete.')
    for name, summary in result['profiles'].items():
        profile = training/name
        calibration = json.loads((profile/'calibration.json').read_text())
        scores = json.loads((profile/'scores.json').read_text())
        threshold = max(statistics.mean(calibration['scores']) + 3*statistics.pstdev(calibration['scores']), 1e-6)
        if not math.isclose(threshold, calibration['threshold'], rel_tol=1e-6):
            raise ValueError('Calibration threshold mismatch.')
        for condition, metric in summary['metrics'].items():
            selected = [s for s in scores if s['condition'] == condition]
            if len(selected) != metric['count'] or sum(s['anomalous'] for s in selected) != metric['alerts']:
                raise ValueError('Recomputed metric mismatch.')
            if any(not math.isfinite(s['score']) or s['anomalous'] != (s['score'] > calibration['threshold']) for s in selected):
                raise ValueError('Invalid anomaly score.')
    return result


def main():
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument('--smoke', action='store_true')
    parser.add_argument('--four-edges', action='store_true')
    parser.add_argument('--contextual-inputs', action='store_true', help='Paired physical/supervisory LSTM with fixed relational score and controls.')
    parser.add_argument('--common-calibration', action='store_true', help='Documented-noise current-domain target-FPR .01 repetition, simulation seed 606.')
    parser.add_argument('--hart-totalizer', action='store_true', help='Documented HART SV increments with a matched current-only ablation.')
    parser.add_argument('--generic-plant', action='store_true', help='Approved receiver model and updated HART instruments; seed808.')
    args = parser.parse_args()
    if args.generic_plant and not args.hart_totalizer:
        parser.error('generic-plant requires hart-totalizer and its four-edge/contextual/common-calibration flags.')
    if args.hart_totalizer:
        if not (args.four_edges and args.contextual_inputs and args.common_calibration):
            parser.error('hart-totalizer requires four-edges, contextual-inputs and common-calibration.')
        from run_hart_confirmation import run
        return run(technical=args.smoke,generic_plant=args.generic_plant)
    if args.contextual_inputs and not args.four_edges:
        parser.error('contextual-inputs requires four-edges.')
    if args.common_calibration and not args.contextual_inputs:
        parser.error('common-calibration requires contextual-inputs and four-edges.')
    simulation_seed=606 if args.common_calibration else 303 if args.contextual_inputs else 202
    session = datetime.now(timezone.utc).strftime('%Y%m%dT%H%M%S%fZ')
    root = ROOT/'output'/('replay-documented-noise' if args.common_calibration else 'replay-documented-noise-controls')/session
    root.mkdir(parents=True, exist_ok=False)
    save(root/'protocol.json', {'version': 'documented-noise-contextual-replay-v3' if args.contextual_inputs else 'documented-noise-replay-v3',
        'current_noise_configuration': noise_configuration(),
        'current_noise_multiplier': 1.0,
        'consensus_schema': 'current-consensus-v2', 'measurement_domain': 'loop_current_ma',
        'consistency_rule': 'exact current and source-event agreement; strictly more than 2/3 equal-power views',
        'supervisory_comparator': 'same-event digital current comparison, zero mA tolerance; engineering display excluded',
        'mode': 'technical-smoke' if args.smoke else 'prospective-exploratory-repetition',
        'simulation_seed': simulation_seed, 'training_seed': 101, 'profiles': ['unmodulated', 'modulated'],
        'edge_count': 4 if args.four_edges else 3, 'validator_count': 4 if args.four_edges else 3,
        'syscalls': 'real Linux shared-runtime capture with per-acquisition association' if args.four_edges else 'unchanged',
        'train_records': 16 if args.smoke else 120, 'calibration_records': 12 if args.smoke else 60,
        'fit_fraction': .6, 'sequence_length': 2,
        'features': 'Physical and supervisory current pairs, two timesteps by eight attributes' if args.contextual_inputs else 'Four currents including mass_flow, scaled (mA-4)/16' if args.four_edges else 'Three currents scaled (mA-4)/16',
        'primary_detector':'relational_lstm' if args.contextual_inputs else 'original_hybrid_lstm',
        'relational_formula':'mean((((predicted_physical-observed_physical)-(predicted_supervisory-observed_supervisory))/2)^2)' if args.contextual_inputs else None,
        'direct_control':'mean(((observed_physical-observed_supervisory)/2)^2); calibrated on same normal partition' if args.contextual_inputs else None,
        'max_epochs': 1 if args.smoke else 300, 'patience': 25, 'min_delta': 1e-6,
        'batch_size': 8, 'latent_units': 16, 'shuffle': False,
        'threshold': 'target normal calibration FPR <= 0.01; academic candidate rule; score >= threshold; no floor' if args.common_calibration else 'normal calibration mean + 3 population std',
        'calibration_rule': 'target-fpr' if args.common_calibration else 'mean-plus-3std',
        'intermediate_thresholds': 'collection/, training/ and contextual-training/ preserve historical mean+3std diagnostics; relational-evaluation/ is the final declared evaluation',
        'selection': 'normal validation only; retain every outcome',
        'output': 'collection/ preserves original collector scores; training/ contains corrected-model results'})
    status = {'status': 'preparing', 'started_at': datetime.now(timezone.utc).isoformat(), 'smoke': args.smoke}
    save(root/'summary.json', status)
    awake = False
    print(f'Resultados da nova coleta e treinamento: {root}', flush=True)
    try:
        if os.name == 'nt':
            awake = bool(ctypes.windll.kernel32.SetThreadExecutionState(0x80000001))
            if not awake:
                raise RuntimeError('Unable to prevent automatic sleep.')
        command = [sys.executable, '-B', '-u', str(ROOT/'scripts/run_replay_evaluation.py'),
                   '--paired-profiles', '--simulation-seed', str(simulation_seed), '--output-directory', str(root/'collection')]
        if args.smoke:
            command += ['--smoke']
        if args.four_edges:
            command += ['--four-edges']
        status['status'] = 'collecting'
        save(root/'summary.json', status)
        subprocess.run(command, cwd=ROOT, check=True)
        status['status'] = 'training'
        save(root/'summary.json', status)
        print('Coleta verificada. Aplicando automaticamente o treinamento corrigido...', flush=True)
        command = [sys.executable, '-B', '-u', str(ROOT/'scripts/evaluate_replay_training_offline.py'),
                   '--source', str(root/'collection'), '--output', str(root/'training'), '--prospective']
        if args.smoke:
            command += ['--smoke']
        with (root/'training.log').open('x', encoding='utf-8') as log:
            subprocess.run(command, cwd=ROOT, check=True, timeout=3600, stdout=log, stderr=subprocess.STDOUT)
        result = verify_training(root)
        status.update(status='completed', profiles=result['profiles'], verified=True)
        if args.contextual_inputs:
            status.update(status='contextual_training',baseline_profiles=result['profiles'],primary_detector='relational_lstm',verified=False)
            save(root/'summary.json',status)
            print('Treinando a LSTM com referencia fisica e supervisoria simultaneas...',flush=True)
            command=[sys.executable,'-B','-u',str(ROOT/'scripts/evaluate_contextual_replay.py'),
                '--session',str(root),'--output',str(root/'contextual-training'),'--prospective']
            if args.smoke:
                command+=['--smoke']
            with (root/'contextual-training.log').open('x',encoding='utf-8') as log:
                subprocess.run(command,cwd=ROOT,check=True,timeout=3600,stdout=log,stderr=subprocess.STDOUT)
            print('Verificando escore relacional e controles...',flush=True)
            command=[sys.executable,'-B','-u',str(ROOT/'scripts/evaluate_contextual_error.py'),
                '--contextual',str(root/'contextual-training'),'--output',str(root/'relational-evaluation'),'--prospective']
            if args.common_calibration:
                command+=['--calibration-rule','target-fpr']
            with (root/'relational-evaluation.log').open('x',encoding='utf-8') as log:
                subprocess.run(command,cwd=ROOT,check=True,timeout=1800,stdout=log,stderr=subprocess.STDOUT)
            from evaluate_contextual_error import verify_output
            relational=verify_output(root/'relational-evaluation')
            status.update(status='completed',profiles=relational['profiles'],verified=True)
    except KeyboardInterrupt:
        status['status'] = 'interrupted'
    except Exception as error:
        status.update(status='failed', error=str(error))
        print(f'Falha: {error}. Consulte {root}', flush=True)
    finally:
        if awake:
            ctypes.windll.kernel32.SetThreadExecutionState(0x80000000)
        status['finished_at'] = datetime.now(timezone.utc).isoformat()
        save(root/'summary.json', status)
    print(f'Final: {status["status"]}. Resultado principal: {root / "summary.json"}', flush=True)
    return 0 if status['status'] == 'completed' else 1


if __name__ == '__main__':
    raise SystemExit(main())
