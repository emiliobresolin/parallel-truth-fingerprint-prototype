"""Prospective opt-in collector and matched HART/current LSTM evaluation."""
from datetime import datetime, timezone
from pathlib import Path
import ctypes
import json
import os
import subprocess
import sys

ROOT = Path(__file__).resolve().parents[1]
sys.path[:0] = [str(ROOT/'src'), str(ROOT/'scripts')]
from parallel_truth_fingerprint.sensor_simulation.mass_flow import totalizer_configuration
from parallel_truth_fingerprint.sensor_simulation.current_noise import noise_configuration
from parallel_truth_fingerprint.evidence.hart_totalizer import FEATURES


def save(path, value):
    path.write_text(json.dumps(value, indent=2, allow_nan=False), encoding='utf-8')


def run(*, technical=False, generic_plant=False):
    if generic_plant:
        from parallel_truth_fingerprint.sensor_simulation.generic_plant import generic_totalizer_configuration, generic_plant_configuration
    session = datetime.now(timezone.utc).strftime('%Y%m%dT%H%M%S%fZ')
    root = ROOT/('output/replay-generic-plant' if generic_plant else 'output/replay-hart-totalizer')/session
    root.mkdir(parents=True, exist_ok=False)
    protocol = {'version': 'generic-receiver-hart-confirmation-v1' if generic_plant else 'hart-totalizer-contextual-replay-v1',
        **({'generic_plant_configuration':generic_plant_configuration()} if generic_plant else {}),
        'hart_totalizer_configuration': generic_totalizer_configuration() if generic_plant else totalizer_configuration(),
        'current_noise_configuration': noise_configuration(), 'current_noise_multiplier': 1.0,
        'consensus_schema': 'current-consensus-v2', 'measurement_domain': 'loop_current_ma',
        'auxiliary_measurement_domain': 'hart_totalizer_mass_kg',
        'feature_unit': 'dimensionless after per-field documented normalization',
        'source_binding': 'Documented Totalizer1 identity/unit/value bound into source_event_id; same-event current agreement unchanged.',
        'simulation_seed': 808 if generic_plant else 707, 'training_seed': 101, 'edge_count': 4, 'validator_count': 4,
        'profiles': ['unmodulated', 'modulated'], 'features': list(FEATURES),
        'feature_count': 10, 'matched_current_feature_count': 8, 'sequence_length': 2,
        'train_records': 16 if technical else 120, 'calibration_records': 12 if technical else 60,
        'fit_fraction': .6, 'fit_windows': 7 if technical else 70,
        'validation_windows': 5 if technical else 46, 'calibration_windows': 10 if technical else 58,
        'eligible_windows_per_condition_profile': 2 if technical else 140,
        'warmup': 'First two observations of each partition and evaluated episode omitted uniformly; increments within branch only.',
        'max_epochs': 1 if technical else 300, 'patience': 25, 'min_delta': 1e-6,
        'batch_size': 8, 'latent_units': 16, 'shuffle': False,
        'calibration_rule': 'target-fpr', 'target_fpr': .01, 'decision': 'score >= threshold; no floor',
        'primary_detector': 'hart_totalizer.relational_error',
        'controls': ['matched current-only contextual LSTM', 'direct-gap', 'current comparator'],
        'mode': 'technical-smoke' if technical else 'prospective-fixed-exploratory',
        'selection': 'Normal validation only; fixed inputs and recipe; preserve every outcome.',
        'output': 'collection/ contains acquired SV/current/syscalls; hart-evaluation/ contains the primary model and matched ablation.'}
    protocol['intermediate_collection_scores'] = 'Legacy collector diagnostic only; primary10-feature model and matched8-feature control are fit after collection.'
    save(root/'protocol.json', protocol)
    status = {'status': 'preparing', 'smoke': technical, 'started_at': datetime.now(timezone.utc).isoformat()}
    save(root/'summary.json', status)
    awake = False
    print(f'Resultados HART e controle pareado: {root}', flush=True)
    try:
        if os.name == 'nt':
            awake = bool(ctypes.windll.kernel32.SetThreadExecutionState(0x80000001))
            if not awake:
                raise RuntimeError('Unable to prevent automatic sleep.')
        command = [sys.executable, '-B', '-u', str(ROOT/'scripts/run_replay_evaluation.py'),
            '--paired-profiles', '--four-edges', '--hart-totalizer', '--simulation-seed', str(protocol['simulation_seed']),
            '--output-directory', str(root/'collection')]
        if technical:
            command += ['--smoke']
        if generic_plant:
            command += ['--generic-plant']
        status['status'] = 'collecting'
        save(root/'summary.json', status)
        subprocess.run(command, cwd=ROOT, check=True)
        acquired = json.loads((root/'collection/protocol.json').read_text())
        if (acquired.get('hart_totalizer_configuration') != protocol['hart_totalizer_configuration']
                or acquired.get('current_noise_configuration') != protocol['current_noise_configuration']
                or acquired['parameters']['simulation_seed'] != protocol['simulation_seed']):
            raise ValueError('Confirmation and acquisition HART protocols differ.')
        if generic_plant and acquired.get('generic_plant_configuration')!=protocol['generic_plant_configuration']:
            raise ValueError('Confirmation and acquisition generic plant configurations differ.')
        status['status'] = 'hart_training'
        save(root/'summary.json', status)
        print('Coleta verificada. Treinando correntes + SV HART e controle somente com correntes...', flush=True)
        command = [sys.executable, '-B', '-u', str(ROOT/'scripts/evaluate_hart_totalizer.py'),
            '--source', str(root/'collection'), '--output', str(root/'hart-evaluation')]
        if technical:
            command += ['--smoke']
        with (root/'hart-training.log').open('x', encoding='utf-8') as log:
            subprocess.run(command, cwd=ROOT, check=True, timeout=7200, stdout=log, stderr=subprocess.STDOUT)
        from evaluate_hart_totalizer import verify_output
        evaluated = verify_output(root/'hart-evaluation')
        status.update(status='completed', profiles=evaluated['profiles'], verified=True,
                      primary_detector='hart_totalizer.relational_error')
    except KeyboardInterrupt:
        status.update(status='interrupted', verified=False)
    except Exception as error:
        status.update(status='failed', verified=False, error=str(error))
        print(f'Falha: {error}. Consulte {root}', flush=True)
    finally:
        if awake:
            ctypes.windll.kernel32.SetThreadExecutionState(0x80000000)
        status['finished_at'] = datetime.now(timezone.utc).isoformat()
        save(root/'summary.json', status)
    print(f'Final: {status["status"]}. Resultado principal: {root/"summary.json"}', flush=True)
    return 0 if status['status'] == 'completed' else 1
