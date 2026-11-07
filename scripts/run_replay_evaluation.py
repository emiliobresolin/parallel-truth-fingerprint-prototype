"""Launch one isolated, prospective SCADA sequence-replay evaluation."""
from __future__ import annotations

import argparse
import ctypes
from dataclasses import asdict
from datetime import datetime, timezone
import hashlib
import json
import math
import os
from pathlib import Path
import socket
import subprocess
import sys
import time
import urllib.request

ROOT = Path(__file__).resolve().parents[1]
sys.path.insert(0, str(ROOT / 'src'))
from run_nightly_collection import COMET, infrastructure, save_json, wait_services, cached_base_available
from parallel_truth_fingerprint.evidence.replay_evaluation import ReplayProtocol, build_scoring_window
from parallel_truth_fingerprint.evidence.paired_replay import PairedReplayProtocol, verify_paired_results
from parallel_truth_fingerprint.sensor_simulation.operational_profiles import OperationalAssumptions
from parallel_truth_fingerprint.sensor_simulation.mass_flow import MassFlowConfiguration, totalizer_configuration
from parallel_truth_fingerprint.sensor_simulation.current_noise import noise_configuration


def verify_results(directory, protocol):
    if isinstance(protocol, PairedReplayProtocol):
        if protocol.edge_count == 4:
            from parallel_truth_fingerprint.evidence.paired_syscalls import verify_dataset
            verify_dataset(directory)
            proof = json.loads((directory/'validator_qualification.json').read_text())
            if (proof['status'] != 'passed' or len(proof['validators']) != 4
                    or len({v['voting_power'] for v in proof['validators']}) != 1
                    or proof['height_with_one_stopped'] <= proof['height_before_stop']):
                raise ValueError('Four-validator availability qualification missing.')
        return verify_paired_results(directory, protocol)
    summary = json.loads((directory / 'summary.json').read_text())
    protocol_path = directory / 'protocol.json'
    frozen_protocol = json.loads(protocol_path.read_text(encoding='utf-8')) if protocol_path.exists() else {}
    documented_noise = frozen_protocol.get('version', '').startswith('documented-noise-')
    if documented_noise:
        from parallel_truth_fingerprint.sensor_simulation.current_noise import validate_noise_configuration
        validate_noise_configuration(frozen_protocol.get('current_noise_configuration'))
        if (frozen_protocol.get('current_noise_multiplier') != 1.0
                or summary.get('protocol_sha256') != hashlib.sha256((directory/'protocol.json').read_bytes()).hexdigest()):
            raise ValueError('Frozen noise protocol differs from the completed experiment.')
    if summary['status'] != 'completed' or summary['completed_rounds'] != len(protocol.schedule()):
        raise ValueError('Experiment incomplete; retained data must not be counted as a complete run.')
    manifest = json.loads((directory / 'manifest.json').read_text())
    for name, digest in manifest.items():
        if hashlib.sha256((directory / name).read_bytes()).hexdigest() != digest:
            raise ValueError(f'Result hash mismatch: {name}')
    rows = [json.loads(s) for s in (directory / 'observations.jsonl').read_text().splitlines()]
    if len(rows) != len(protocol.schedule()) or len({r['round_id'] for r in rows}) != len(rows):
        raise ValueError('Missing/duplicate acquired rounds.')
    calibration = json.loads((directory / 'calibration.json').read_text())
    model = json.loads((directory / 'model.json').read_text())
    if hashlib.sha256((directory / 'model.keras').read_bytes()).hexdigest() != model['sha256']:
        raise ValueError('Model archive mismatch.')
    if not summary['weights_unchanged']:
        raise ValueError('Model was not kept fixed.')
    normal_sources = {}
    previous_physical = None
    previous_phase = None
    for index, (r, expected) in enumerate(zip(rows, protocol.schedule()), 1):
        if documented_noise:
            from parallel_truth_fingerprint.evidence.paired_replay import verify_recorded_noise
            verify_recorded_noise({
                'current_noise_configuration': frozen_protocol['current_noise_configuration'],
                'current_noise_multiplier': frozen_protocol['current_noise_multiplier'],
                'acquisition_snapshot': r.get('acquisition_snapshot', {}),
            }, frozen_protocol['current_noise_configuration'], r['consensused_physical_values'])
        phase, block, offset = expected
        if (r['index'], r['phase'], r['block'], r['offset']) != (index, phase, block, offset):
            raise ValueError('Observation schedule differs from the fixed protocol.')
        warmup = offset == 0 and (phase in {'train', 'calibration'} or (phase == 'normal' and block == 1))
        if r['warmup'] != warmup:
            raise ValueError('Incorrect partition warmup handling.')
        if r['transition'] != (phase != previous_phase):
            raise ValueError('Incorrect transition marking.')
        previous_phase = phase
        if warmup:
            previous_physical = None
        if r['input_window'] != build_scoring_window(previous_physical, r['current_supervisory_vector']):
            raise ValueError('Scoring input does not follow the common window rule.')
        previous_physical = r['current_physical_vector']
        evaluation = phase in {'normal', 'replay', 'recovery'}
        expected_scored = evaluation and not warmup
        if (r['score'] is not None) != expected_scored:
            raise ValueError('Missing or unexpected scored observation.')
        if expected_scored and (not math.isfinite(r['score']) or r['score'] < 0
                or r['anomalous'] != (r['score'] > calibration['threshold'])):
            raise ValueError('Invalid score or anomaly decision.')
        if expected_scored and (r['threshold'] != calibration['threshold'] or r['model_sha256'] != model['sha256']):
            raise ValueError('Model or threshold differed between conditions.')
        if phase == 'normal':
            normal_sources[block, offset] = r
        if phase == 'replay':
            source = normal_sources[block, offset]['scada_state']
            if r['replay_original_state'] != source:
                raise ValueError('Replay source is not the corresponding preceding normal observation.')
            if r['scada_state']['behavioral_source_round_id'] != source['source_round_id']:
                raise ValueError('Replay historical identity was lost.')
            for group in ('sensor_values', 'behavioral_sensor_values'):
                expected_payload = {k: dict(v, mode='replay') for k, v in source[group].items()}
                if r['scada_state'][group] != expected_payload:
                    raise ValueError('Replay failed to re-present complete historical payload.')
        blocked = bool(r['comparison']['divergent_sensors'])
        if (r['persistence_status'] == 'blocked') != blocked:
            raise ValueError('Persistence no longer matches the supervisory divergence gate.')
    if model['training_windows'] != protocol.train_rounds - 1 or calibration['count'] != protocol.calibration_rounds - 1:
        raise ValueError('Training or calibration support differs from the fixed protocol.')
    return summary


def main():
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument('--smoke', action='store_true', help='Technical verification only; not the approved 630-round run.')
    parser.add_argument('--paired-profiles', action='store_true', help='Opt-in two demand profiles and four paired conditions.')
    parser.add_argument('--timeout-hours', type=float, default=4)
    parser.add_argument('--simulation-seed', type=int, help='Separate process-noise seed; paired profiles only.')
    parser.add_argument('--output-directory', type=Path, help='Fresh result directory for a sequential workflow.')
    parser.add_argument('--four-edges', action='store_true', help='Four acquisition edges, four equal-power validators and real syscall capture.')
    parser.add_argument('--hart-totalizer', action='store_true', help='Opt-in documented FIT-101 HART Totalizer1 acquisition.')
    parser.add_argument('--generic-plant', action='store_true', help='Approved generic receiver and documented HART instruments; explicit version.')
    args = parser.parse_args()
    if args.hart_totalizer and not (args.paired_profiles and args.four_edges):
        parser.error('hart-totalizer requires paired-profiles and four-edges.')
    if args.generic_plant and not (args.hart_totalizer and args.paired_profiles and args.four_edges):
        parser.error('generic-plant requires hart-totalizer, paired-profiles and four-edges.')
    if args.generic_plant and args.simulation_seed not in (None,808):
        parser.error('generic-plant freezes simulation-seed 808.')
    if args.generic_plant:
        args.simulation_seed=808
    if not 0 < args.timeout_hours <= 24:
        parser.error('timeout-hours must be greater than zero and at most 24.')
    protocol = ReplayProtocol(train_rounds=8, calibration_rounds=6, block_rounds=4, repetitions=2,
                              epochs=1, interval_seconds=2) if args.smoke else ReplayProtocol()
    if args.paired_profiles:
        protocol = PairedReplayProtocol(train_rounds=16, calibration_rounds=12, block_rounds=4, settle_rounds=3,
                      repetitions=1, epochs=1, interval_seconds=2) if args.smoke else PairedReplayProtocol()
        if args.simulation_seed is not None or args.four_edges:
            from dataclasses import replace
            protocol = replace(protocol, simulation_seed=args.simulation_seed, edge_count=4 if args.four_edges else 3)
    elif args.simulation_seed is not None:
        parser.error('simulation-seed requires paired-profiles.')
    if args.four_edges and not args.paired_profiles:
        parser.error('four-edges requires paired-profiles.')
    validator_count = 4 if args.four_edges else 3
    if args.generic_plant:
        from dataclasses import replace
        from parallel_truth_fingerprint.sensor_simulation.generic_plant import (
            COLLECTION_VERSION, generic_plant_configuration, generic_totalizer_configuration,
            generic_mass_flow_configuration, select_numerical_resolution)
        protocol=replace(protocol,interval_seconds=5.0)
        generic_resolution=select_numerical_resolution()
    protocol.validate()
    for port in (19010, 28657):
        with socket.socket() as probe:
            probe.bind(('127.0.0.1', port))
    session = 'replay-' + datetime.now(timezone.utc).strftime('%Y%m%dT%H%M%SZ').lower() + f'-{os.getpid()}'
    directory = ROOT / ('output/replay-generic-plant' if args.generic_plant else 'output/paired-replay-evaluation' if args.paired_profiles else 'output/replay-evaluation') / session
    if args.output_directory is not None:
        directory = args.output_directory.resolve()
    directory.mkdir(parents=True, exist_ok=False)
    project, container = 'ptfp-' + session, session + '-worker'
    save_json(directory / 'compose.json', infrastructure(directory, validator_count=validator_count))
    compose = ['docker', 'compose', '-p', project, '-f', str(directory / 'compose.json')]
    save_json(directory / 'protocol.json', {
        **({'hart_totalizer_configuration': generic_totalizer_configuration() if args.generic_plant else totalizer_configuration(),
            'auxiliary_measurement_domain': 'hart_totalizer_mass_kg'} if args.hart_totalizer else {}),
        **({'generic_plant_configuration':generic_plant_configuration(),
            'generic_numerical_resolution':generic_resolution} if args.generic_plant else {}),
        'current_noise_configuration': noise_configuration(),
        'current_noise_multiplier': 1.0,
        'consensus_schema': 'current-consensus-v2', 'measurement_domain': 'loop_current_ma',
        'consistency_rule': 'exact replicated current/source-event agreement',
        'comparison_domain': 'loop_current_ma', 'comparison_tolerance_ma': 0.0,
        'version': COLLECTION_VERSION if args.generic_plant else 'documented-noise-hart-totalizer-v1' if args.hart_totalizer else 'documented-noise-four-edge-v2' if args.four_edges else 'documented-noise-paired-profiles-v2' if args.paired_profiles else 'documented-noise-scada-replay-v2', 'mode': 'technical-smoke' if args.smoke else 'approved-exploratory',
        'parameters': asdict(protocol), 'expected_rounds': len(protocol.schedule()),
        'validator_count': validator_count, 'equal_voting_power': True,
        'syscall_capture': 'real Linux strace of shared four-edge runtime, associated by acquisition timestamps' if args.four_edges else None,
        'fourth_edge_role': 'FIT-101 Endress+Hauser t-mass F 300 HART mass-flow acquisition; kg/h, configured 0..1000' if args.four_edges else None,
        'mass_flow_configuration': generic_mass_flow_configuration() if args.generic_plant else asdict(MassFlowConfiguration()) if args.four_edges else None,
        'operational_assumptions': None if args.generic_plant else asdict(OperationalAssumptions()) if args.paired_profiles else None,
        'assumption_status': 'Approved idealized generic plant; published balances and explicit physical/instrument selections.' if args.generic_plant else 'Numerical dynamics are prototype assumptions, not measured compressor parameters.' if args.paired_profiles else None,
        'attack': 'paired current/replayed views of one physical trajectory; source is the preceding reserved normal block' if args.paired_profiles else 're-present the preceding normal block in order, including supervisory and behavioral values',
        'input': 'previous physical vector + current SCADA vector; identical path in all conditions',
        'calibration': 'separate normal windows; mean + 3 population standard deviations, floor 1e-6',
        'partitions': 'chronological; no timestep crosses train/calibration/evaluation',
        'scope': 'logical simulated-SCADA injection; process emulated; no syscall model, no packet replay',
        'frozen_at': datetime.now(timezone.utc).isoformat(),
    })
    launcher = {'status': 'preparing', 'session': session, 'smoke': args.smoke}
    save_json(directory / 'launcher.json', launcher)
    print(f'Resultados: {directory}', flush=True)

    def run(command, log='infrastructure.log', timeout=600):
        with (directory / log).open('a', encoding='utf-8') as handle:
            subprocess.run(command, cwd=ROOT, check=True, timeout=timeout,
                           stdout=handle, stderr=subprocess.STDOUT)

    awake = False
    try:
        if os.name == 'nt':
            awake = bool(ctypes.windll.kernel32.SetThreadExecutionState(0x80000001))
            if not awake:
                raise RuntimeError('Unable to prevent automatic sleep.')
        print('Verificando ambiente e preparando servicos isolados...', flush=True)
        run(['docker', 'info', '--format', '{{.OSType}}'], timeout=30)
        run([sys.executable, '-B', 'scripts/qualify_live_run.py'])
        run(['docker', 'run', '--rm', '--mount', f'type=bind,source={directory},target=/work',
             COMET, 'testnet', '--v', str(validator_count), '--o', '/work/testnet'])
        for i in range(validator_count):
            path = directory / f'testnet/node{i}/config/config.toml'
            content = path.read_text(encoding='utf-8').replace('proxy_app = "tcp://127.0.0.1:26658"', f'proxy_app = "tcp://abci-node{i}:26658"')
            path.write_text(content.replace('laddr = "tcp://127.0.0.1:26657"', 'laddr = "tcp://0.0.0.0:26657"'), encoding='utf-8')
        run(compose + ['up', '-d', '--build'], timeout=1800)
        wait_services()
        if args.four_edges:
            def rpc(method):
                with urllib.request.urlopen('http://127.0.0.1:28657/'+method, timeout=5) as response:
                    return json.load(response)['result']
            validators = rpc('validators?per_page=100')['validators']
            if len(validators) != 4 or len({v['voting_power'] for v in validators}) != 1:
                raise ValueError('Expected four validators with equal voting power.')
            before = int(rpc('status')['sync_info']['latest_block_height'])
            print('Verificando progresso do consenso com um dos quatro validadores parado...', flush=True)
            try:
                run(compose+['stop', '-t', '2', 'node3'], timeout=45)
                before = int(rpc('status')['sync_info']['latest_block_height'])
                deadline = time.monotonic()+60
                after = before
                while time.monotonic() < deadline:
                    after = int(rpc('status')['sync_info']['latest_block_height'])
                    if after >= before+3:
                        break
                    time.sleep(1)
                if after < before+3:
                    raise ValueError('Consensus did not advance with one stopped validator.')
            finally:
                run(compose+['start', 'node3'], timeout=45)
            save_json(directory/'validator_qualification.json', {
                'status':'passed', 'fault':'one validator stopped; then restarted before collection',
                'validators':validators, 'height_before_stop':before, 'height_with_one_stopped':after,
                'quorum':'strictly greater than 2/3 voting power; three of four equal-power validators'})
        print('Preparando imagem de avaliacao...', flush=True)
        image = 'ptfp-' + session
        capture_dockerfile = 'Dockerfile.live-edge-capture.cached' if cached_base_available('ptfp-current-capture-base:20261028') else 'Dockerfile.live-edge-capture'
        run(['docker', 'build', '-t', image, '-f', capture_dockerfile, '.'], timeout=1800)
        image = subprocess.check_output(['docker', 'image', 'inspect', '--format', '{{.Id}}', image], text=True, timeout=30).strip()
        files = list((ROOT / 'src').rglob('*.py')) + list((ROOT / 'abci/consensus_app').rglob('*.go'))
        if args.generic_plant:
            generic_manifest=ROOT/'docs/reference-archive/catalog/p14-generic-plant-sources.v1.json'
            files += [ROOT/'src/parallel_truth_fingerprint/sensor_simulation/generic_plant_config.json',generic_manifest]
            for source in json.loads(generic_manifest.read_text(encoding='utf-8'))['archived']:
                path=ROOT/source['path']
                if hashlib.sha256(path.read_bytes()).hexdigest()!=source['sha256']:
                    raise ValueError('Generic plant reference source hash mismatch.')
                files.append(path)
        if args.hart_totalizer:
            hart_manifest = ROOT/'docs/reference-archive/catalog/hart-totalizer-sources.v1.json'
            hart_sources = json.loads(hart_manifest.read_text(encoding='utf-8'))['sources']
            files += [hart_manifest, ROOT/'docs/hart-totalizer-lstm.md', ROOT/'scripts/evaluate_hart_totalizer.py', ROOT/'scripts/run_hart_confirmation.py']
            for source in hart_sources:
                source_path = ROOT/source['path']
                if hashlib.sha256(source_path.read_bytes()).hexdigest() != source['sha256']:
                    raise ValueError('HART totalizer reference hash mismatch.')
                files.append(source_path)
        files += [ROOT / 'scripts/run_replay_evaluation.py', ROOT / 'scripts/replay_evaluation_worker.py',
                  ROOT / 'scripts/paired_replay_worker.py',
                  ROOT / 'scripts/trace_paired_worker.py',
                  ROOT / 'scripts/evaluate_contextual_replay.py', ROOT / 'scripts/evaluate_contextual_error.py',
                  ROOT / 'scripts/evaluate_replay_training_offline.py', ROOT / 'scripts/run_replay_confirmation.py',
                  ROOT / 'scripts/run_local_demo.py', ROOT / 'scripts/run_nightly_collection.py', ROOT / capture_dockerfile,
                  ROOT / 'abci/consensus_app/Dockerfile', ROOT / 'abci/consensus_app/Dockerfile.cached',
                  ROOT / 'docs/reference-archive/catalog/current-domain-runtime-contract.v2.json']
        noise_manifest_path = ROOT / 'docs/reference-archive/catalog/documented-loop-noise-sources.v1.json'
        noise_sources = json.loads(noise_manifest_path.read_text(encoding='utf-8'))['sources']
        files += [noise_manifest_path, ROOT / 'docs/documented-loop-current-noise.md']
        for source in noise_sources:
            path = ROOT / source['path']
            if hashlib.sha256(path.read_bytes()).hexdigest() != source['sha256']:
                raise ValueError(f'Noise reference source hash mismatch: {source["path"]}')
            files.append(path)
        if args.four_edges:
            files.append(ROOT/'docs/reference-archive/documents/EndressHauser_t-mass_F300_HART_BA01992DEN_0323-00.pdf')
        save_json(directory / 'provenance.json', {
            'dependency_base_image_ids': {name: subprocess.check_output(['docker','image','inspect','--format','{{.Id}}',name],text=True,timeout=15).strip()
                for name in ('ptfp-current-go-base:20261028','ptfp-current-capture-base:20261028') if cached_base_available(name)},
            'capture_dockerfile': capture_dockerfile,
            'image_id': image, 'source_sha256': {str(p.relative_to(ROOT)): hashlib.sha256(p.read_bytes()).hexdigest() for p in files},
            'host_python': sys.executable,
        })
        command = ['docker', 'run', '--rm', '--name', container, '--network', project + '_default',
                   '--mount', f'type=bind,source={directory},target=/results',
                   '--mount', f'type=bind,source={ROOT / "scripts"},target=/workspace/scripts,readonly',
                   '--entrypoint', 'python']
        environment = {'MQTT_TRANSPORT': 'real', 'MQTT_BROKER_HOST': 'mqtt', 'MQTT_TOPIC': session,
                       'COMETBFT_RPC_URL': 'http://node0:26657', 'MINIO_ENDPOINT': 'minio:9000',
                       'MINIO_ACCESS_KEY': 'minioadmin', 'MINIO_SECRET_KEY': 'minioadmin',
                       'MINIO_BUCKET': session, 'MINIO_SECURE': 'false', 'DEMO_CAMPAIGN_ID': session,
                       'KERAS_BACKEND': 'torch', 'PYTHONDONTWRITEBYTECODE': '1',
                       'DEMO_DISABLE_RUNTIME_AUTOENCODER': 'true'}
        for key, value in environment.items():
            command += ['--env', f'{key}={value}']
        worker = 'scripts/paired_replay_worker.py' if args.paired_profiles else 'scripts/replay_evaluation_worker.py'
        command += [image]
        if args.four_edges:
            (directory/'syscalls').mkdir()
            command += ['-u', '-B', 'scripts/trace_paired_worker.py']
        else:
            command += ['-u', '-B', worker, '--protocol', '/results/protocol.json']
        launcher['status'] = 'running'
        save_json(directory / 'launcher.json', launcher)
        print(f'Ensaio iniciado: {len(protocol.schedule())} rodadas. Progresso em summary.json e console.log.', flush=True)
        run(command, 'console.log', args.timeout_hours * 3600)
        if args.four_edges:
            from parallel_truth_fingerprint.evidence.paired_syscalls import export_dataset
            dataset = export_dataset(directory)
            print(f'Dataset de correntes e syscalls: {dataset["row_count"]} registros associados.', flush=True)
        summary = verify_results(directory, protocol)
        launcher.update(status='completed', verified_rounds=summary['completed_rounds'])
    except KeyboardInterrupt:
        launcher['status'] = 'interrupted'
    except Exception as error:
        launcher.update(status='failed', error=str(error))
        print(f'FALHA: {error}', flush=True)
    finally:
        errors = []
        for command, log, timeout in [(['docker', 'rm', '-f', container], 'infrastructure.log', 30),
                                      (compose + ['stop', '-t', '10'], 'infrastructure.log', 90),
                                      (compose + ['logs', '--no-color', '--tail', '1000'], 'services.log', 60)]:
            try:
                if command[:3] == ['docker', 'rm', '-f']:
                    subprocess.run(command, stdout=subprocess.DEVNULL, stderr=subprocess.DEVNULL, timeout=timeout)
                else:
                    run(command, log, timeout)
            except Exception as error:
                errors.append(str(error))
        if errors:
            launcher['cleanup_errors'] = errors
            if launcher['status'] == 'completed':
                launcher['status'] = 'completed_with_cleanup_errors'
        if awake:
            ctypes.windll.kernel32.SetThreadExecutionState(0x80000000)
        launcher['finished_at'] = datetime.now(timezone.utc).isoformat()
        save_json(directory / 'launcher.json', launcher)
        print(f'Final: {launcher["status"]}. Resultados: {directory}', flush=True)
    return 0 if launcher['status'] == 'completed' else 1


if __name__ == '__main__':
    raise SystemExit(main())
