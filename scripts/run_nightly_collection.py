"""Collect isolated five-round custom-dataset campaigns, sequentially."""
from __future__ import annotations

import argparse
import ctypes
from datetime import datetime, timedelta, timezone
import hashlib
import json
import math
import os
from pathlib import Path
import socket
import shutil
import subprocess
import sys
import time
import urllib.request

ROOT = Path(__file__).resolve().parents[1]
COMET = 'cometbft/cometbft@sha256:d086a1318d05a41389460f2160aaaf7ca135aa961987e6d7689e4448599c5a76'


def next_local_stop(value, now=None):
    """Resolve the next local HH:MM occurrence before preparation starts."""
    clock = datetime.strptime(value, '%H:%M').time()
    now = now or datetime.now()
    target = now.replace(hour=clock.hour, minute=clock.minute, second=0, microsecond=0)
    return target + timedelta(days=1) if target <= now else target


def save_json(path, value):
    temporary = path.with_suffix('.tmp')
    temporary.write_text(json.dumps(value, indent=2, ensure_ascii=False) + '\n', encoding='utf-8')
    temporary.replace(path)


def cached_base_available(name):
    """Use only an explicitly staged local dependency environment, never old code."""
    try:
        result = subprocess.run(['docker', 'image', 'inspect', name], capture_output=True, timeout=10)
        return result.returncode == 0
    except (OSError, subprocess.TimeoutExpired):
        return False


def infrastructure(directory, validator_count=4):
    """Fresh paths and project-scoped volumes; never reset old consensus state."""
    if validator_count not in (3, 4):
        raise ValueError('Supported validator counts are three and four.')
    app_dockerfile = 'Dockerfile.cached' if cached_base_available('ptfp-current-go-base:20261028') else 'Dockerfile'
    services = {
        'mqtt': {'image': 'eclipse-mosquitto:2', 'volumes': [
            f'{(ROOT / "docs/infrastructure/mosquitto.conf").as_posix()}:/mosquitto/config/mosquitto.conf:ro']},
        'minio': {'image': 'minio/minio:latest', 'command': ['server', '/data'],
                  'environment': {'MINIO_ROOT_USER': 'minioadmin', 'MINIO_ROOT_PASSWORD': 'minioadmin'},
                  'ports': ['127.0.0.1:19010:9000'],
                  'volumes': [f'{directory.as_posix()}/minio-data:/data']},
    }
    for index in range(validator_count):
        name = f'node{index}'
        services[f'abci-{name}'] = {
            'build': {'context': str(ROOT / 'abci/consensus_app'), 'dockerfile': app_dockerfile},
            'entrypoint': ['/usr/local/bin/consensus_abci'],
            'command': ['--home', f'/state/{name}', '--socket-addr', 'tcp://0.0.0.0:26658'],
            'volumes': [f'{directory.as_posix()}/abci/{name}:/state/{name}'],
        }
        services[name] = {
            'image': COMET, 'depends_on': [f'abci-{name}'],
            'entrypoint': ['/bin/sh', '-c'],
            'command': ['mkdir -p /cometbft/config /cometbft/data && cp -R /bootstrap/config/. /cometbft/config/ && cp -n /bootstrap/data/priv_validator_state.json /cometbft/data/priv_validator_state.json && exec cometbft node --home /cometbft'],
            'volumes': [f'{name}-home:/cometbft',
                        f'{directory.as_posix()}/testnet/{name}:/bootstrap:ro'],
        }
        if index == 0:
            services[name]['ports'] = ['127.0.0.1:28657:26657']
    return {'services': services, 'volumes': {f'node{i}-home': {} for i in range(validator_count)}}


def wait_services(timeout=120):
    deadline = time.monotonic() + timeout
    while time.monotonic() < deadline:
        try:
            with urllib.request.urlopen('http://127.0.0.1:19010/minio/health/live', timeout=3) as response:
                if response.status != 200:
                    raise ValueError('MinIO not ready')
            with urllib.request.urlopen('http://127.0.0.1:28657/status', timeout=3) as response:
                status = json.load(response)['result']['sync_info']
                if int(status['latest_block_height']) < 1 or status['catching_up']:
                    raise ValueError('Consensus not ready')
            return
        except (OSError, ValueError, KeyError):
            time.sleep(2)
    raise RuntimeError('Services did not become ready within 120 seconds; see infrastructure.log.')


def verify_export(path, campaign_id):
    """Recompute counts and trace hashes instead of trusting the process exit code."""
    manifest = json.loads((path / 'dataset/manifest.json').read_text(encoding='utf-8'))
    rows = [json.loads(line) for line in (path / 'dataset/current-syscall-windows.jsonl').read_text(encoding='utf-8').splitlines() if line.strip()]
    if not rows or manifest['row_count'] != len(rows):
        raise ValueError('Export is empty or its count does not match the manifest.')
    if any(row['campaign_id'] != campaign_id or not row['syscall_tokens'] for row in rows):
        raise ValueError('Missing syscall association or inconsistent campaign ID.')
    if len({row['round_id'] for row in rows}) != len(rows):
        raise ValueError('Duplicate round IDs in campaign.')
    runtime_hash = manifest.get('runtime_log_sha256')
    if runtime_hash is not None and runtime_hash != 'sha256:' + hashlib.sha256((path / 'runtime.json').read_bytes()).hexdigest():
        raise ValueError('Runtime log hash mismatch.')
    for name, expected in manifest['syscall_trace_sha256'].items():
        digest = hashlib.sha256()
        with (path / name).open('rb') as handle:
            for chunk in iter(lambda: handle.read(1024 * 1024), b''):
                digest.update(chunk)
        if expected != 'sha256:' + digest.hexdigest():
            raise ValueError(f'Trace hash mismatch: {name}')
    return rows


def main():
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument('--hours', type=float, default=10)
    parser.add_argument('--stop-at', help='Next local HH:MM; overrides --hours and includes preparation time.')
    parser.add_argument('--cycles', type=int, default=5)
    parser.add_argument('--interval-seconds', type=int, default=5)
    parser.add_argument('--max-campaigns', type=int, default=0)
    parser.add_argument('--campaign-timeout-seconds', type=int, default=600)
    parser.add_argument('--scenario-cycle', default=','.join(['normal'] * 9 + ['single_edge_exclusion']))
    args = parser.parse_args()
    try:
        stop_at = next_local_stop(args.stop_at) if args.stop_at else None
    except ValueError:
        parser.error('--stop-at must be a valid local time, for example 06:00.')
    scenarios = args.scenario_cycle.split(',')
    if (not math.isfinite(args.hours) or args.hours <= 0 or args.cycles < 1 or args.interval_seconds < 1
            or args.max_campaigns < 0 or args.campaign_timeout_seconds < 1
            or any(s not in {'normal', 'single_edge_exclusion'} for s in scenarios)):
        parser.error('Invalid duration, limits or scenario cycle.')
    # Refuse a port conflict before creating or starting any service.
    for port in (19010, 28657):
        with socket.socket() as probe:
            probe.bind(('127.0.0.1', port))
    stamp = datetime.now(timezone.utc).strftime('%Y%m%dT%H%M%SZ')
    session_id = f'nightly-{stamp.lower()}-{os.getpid()}'
    directory = ROOT / 'output/nightly-collection' / session_id
    directory.mkdir(parents=True, exist_ok=False)
    project = 'ptfp-' + session_id
    compose_path = directory / 'compose.json'
    save_json(compose_path, infrastructure(directory))
    compose = ['docker', 'compose', '-p', project, '-f', str(compose_path)]
    image = 'ptfp-capture-' + session_id
    container_name = project + '-capture'
    summary = {'session_id': session_id, 'status': 'preparing',
               'started_at': datetime.now(timezone.utc).isoformat(), 'settings': vars(args),
               'completed_campaigns': 0, 'complete_campaigns': 0,
               'valid_records': 0, 'failed_campaigns': 0, 'campaigns': [],
               'note': 'Current + strace dataset collection; no claim of joint-model training or independent samples.'}
    summary_path = directory / 'summary.json'
    save_json(summary_path, summary)
    if stop_at:
        summary['stop_at_local'] = stop_at.isoformat()
        save_json(summary_path, summary)
    print(f'Resultados e progresso: {directory}', flush=True)

    def run(command, log, timeout=600):
        with log.open('a', encoding='utf-8') as handle:
            subprocess.run(command, cwd=ROOT, stdout=handle, stderr=subprocess.STDOUT,
                           check=True, timeout=timeout)

    infrastructure_log = directory / 'infrastructure.log'
    stay_awake = False
    try:
        if os.name == 'nt':
            stay_awake = bool(ctypes.windll.kernel32.SetThreadExecutionState(0x80000001))
            if not stay_awake:
                raise RuntimeError('Unable to prevent automatic Windows sleep.')
        print('Preparando: verificando requisitos e Docker...', flush=True)
        run([sys.executable, '-B', 'scripts/qualify_live_run.py'], infrastructure_log)
        run(['docker', 'info', '--format', '{{.OSType}}'], infrastructure_log, 30)
        print('Preparando: criando consenso e armazenamento isolados...', flush=True)
        run(['docker', 'run', '--rm', '--mount', f'type=bind,source={directory},target=/work',
             COMET, 'testnet', '--v', '4', '--o', '/work/testnet'], infrastructure_log)
        for index in range(4):
            config = directory / f'testnet/node{index}/config/config.toml'
            text = config.read_text(encoding='utf-8')
            text = text.replace('proxy_app = "tcp://127.0.0.1:26658"', f'proxy_app = "tcp://abci-node{index}:26658"')
            text = text.replace('laddr = "tcp://127.0.0.1:26657"', 'laddr = "tcp://0.0.0.0:26657"')
            config.write_text(text, encoding='utf-8')
        run(compose + ['up', '-d', '--build'], infrastructure_log, 1800)
        wait_services()
        print('Preparando: construindo imagem de captura (primeira vez pode demorar)...', flush=True)
        run(['docker', 'build', '-t', image, '-f', 'Dockerfile.live-edge-capture', '.'], infrastructure_log, 1800)
        image = subprocess.check_output(['docker', 'image', 'inspect', '--format', '{{.Id}}', image], text=True, timeout=30).strip()
        revision = subprocess.run(['git', 'rev-parse', 'HEAD'], cwd=ROOT, capture_output=True, text=True, timeout=30)
        source_files = sorted(list((ROOT / 'src').rglob('*.py')) + list((ROOT / 'abci/consensus_app').rglob('*.go')))
        source_files += [ROOT / 'scripts/run_local_demo.py', ROOT / 'scripts/run_nightly_collection.py', ROOT / 'Dockerfile.live-edge-capture']
        save_json(directory / 'provenance.json', {
            'git_revision': revision.stdout.strip() if revision.returncode == 0 else None,
            'capture_image_id': image,
            'source_sha256': {str(p.relative_to(ROOT)): hashlib.sha256(p.read_bytes()).hexdigest() for p in source_files},
            'python_executable': sys.executable,
            'settings': vars(args),
            'isolation': 'fresh consensus, bucket per campaign, sequential execution',
        })
        summary['collection_started_at'] = datetime.now(timezone.utc).isoformat()
        summary['status'] = 'running'
        save_json(summary_path, summary)
        remaining = (stop_at - datetime.now()).total_seconds() if stop_at else args.hours * 3600
        deadline = time.monotonic() + max(remaining, 0)
        period = f'ate {stop_at:%d/%m/%Y %H:%M} (horario local)' if stop_at else f'{args.hours:g} horas'
        print(f'Coleta iniciada: {period}; {args.cycles} rodadas por campanha.', flush=True)
        failures = 0
        index = 0
        while time.monotonic() < deadline and (not args.max_campaigns or index < args.max_campaigns):
            if shutil.disk_usage(directory).free < 5 * 1024 ** 3:
                raise RuntimeError('Less than 5 GiB free; stopping collection to preserve existing results.')
            index += 1
            campaign_id = f'{session_id}-{index:05d}'
            capture = directory / campaign_id
            capture.mkdir()
            scenario = scenarios[(index - 1) % len(scenarios)]
            started = time.monotonic()
            record = {'campaign_id': campaign_id, 'scenario': scenario, 'status': 'running', 'rows': 0}
            summary['campaigns'].append(record)
            save_json(summary_path, summary)
            print(f'Campanha {index}: {scenario}', flush=True)
            bucket = campaign_id
            command = ['docker', 'run', '--rm', '--name', container_name,
                       '--network', project + '_default',
                       '--mount', f'type=bind,source={capture},target=/captures']
            environment = {
                'MQTT_TRANSPORT': 'real', 'MQTT_BROKER_HOST': 'mqtt',
                'MQTT_TOPIC': f'ptfp/{campaign_id}',
                'COMETBFT_RPC_URL': 'http://node0:26657', 'MINIO_ENDPOINT': 'minio:9000',
                'MINIO_ACCESS_KEY': 'minioadmin', 'MINIO_SECRET_KEY': 'minioadmin',
                'MINIO_BUCKET': bucket, 'MINIO_SECURE': 'false',
                'DEMO_DISABLE_RUNTIME_AUTOENCODER': 'false', 'DEMO_CAMPAIGN_ID': campaign_id,
                'DEMO_SCENARIO': scenario, 'DEMO_FAULT_MODE': 'none' if scenario == 'normal' else scenario,
                'DEMO_POWER': '65', 'DEMO_MAX_CYCLES': str(args.cycles),
                'DEMO_CYCLE_INTERVAL_SECONDS': str(args.interval_seconds),
                'DEMO_LOG_PATH': '/captures/runtime.json',
            }
            for key, value in environment.items():
                command += ['--env', f'{key}={value}']
            try:
                run(command + [image], capture / 'console.log', args.campaign_timeout_seconds)
                run([sys.executable, '-B', 'scripts/build_custom_campaign_dataset.py',
                     '--run-id', campaign_id, '--capture-dir', str(capture),
                     '--output-dir', str(capture / 'dataset'),
                     '--minio-endpoint', 'localhost:19010', '--minio-bucket', bucket],
                    capture / 'export.log', args.campaign_timeout_seconds)
                rows = verify_export(capture, campaign_id)
                runtime = json.loads((capture / 'runtime.json').read_text(encoding='utf-8'))
                record['model_status'] = runtime.get('runtime', {}).get('model_status')
                record['dataset_sha256'] = hashlib.sha256((capture / 'dataset/current-syscall-windows.jsonl').read_bytes()).hexdigest()
                expected_label = 'normal' if scenario == 'normal' else 'faulty_edge_exclusion'
                if any(row['scenario_label'] != expected_label for row in rows):
                    raise ValueError('Exported labels differ from the requested scenario.')
                record.update(status='completed' if len(rows) == args.cycles else 'partial', rows=len(rows))
                summary['completed_campaigns'] += 1
                summary['complete_campaigns'] += int(len(rows) == args.cycles)
                summary['valid_records'] += len(rows)
                failures = 0
            except (subprocess.SubprocessError, OSError, ValueError, KeyError) as error:
                record.update(status='failed', error=str(error))
                summary['failed_campaigns'] += 1
                failures += 1
            finally:
                subprocess.run(['docker', 'rm', '-f', container_name], stdout=subprocess.DEVNULL,
                               stderr=subprocess.DEVNULL, timeout=30)
                record['elapsed_seconds'] = round(time.monotonic() - started, 2)
                save_json(summary_path, summary)
            print(f"  {record['status']}: {record['rows']} registros; total {summary['valid_records']}", flush=True)
            if failures >= 3:
                raise RuntimeError('Three consecutive campaigns failed; collection stopped. Consult campaign logs.')
        summary['status'] = 'completed'
    except KeyboardInterrupt:
        summary['status'] = 'stopped_by_operator'
    except Exception as error:
        summary.update(status='failed', error=str(error))
        print(f'FALHA: {error}', flush=True)
    finally:
        cleanup_errors = []
        for command, log, timeout in [
            (['docker', 'rm', '-f', container_name], infrastructure_log, 30),
            (compose + ['logs', '--no-color'], directory / 'services.log', 60),
            (compose + ['stop', '-t', '10'], infrastructure_log, 90),
        ]:
            try:
                # A --rm capture normally no longer exists.
                if command[:3] == ['docker', 'rm', '-f']:
                    subprocess.run(command, stdout=subprocess.DEVNULL, stderr=subprocess.DEVNULL, timeout=timeout)
                else:
                    run(command, log, timeout)
            except Exception as error:
                cleanup_errors.append(str(error))
        if cleanup_errors:
            summary['cleanup_errors'] = cleanup_errors
            if summary['status'] == 'completed':
                summary['status'] = 'completed_with_cleanup_errors'
        if stay_awake:
            ctypes.windll.kernel32.SetThreadExecutionState(0x80000000)
        summary['finished_at'] = datetime.now(timezone.utc).isoformat()
        save_json(summary_path, summary)
        print(f"Final: {summary['status']}; {summary['complete_campaigns']} campanhas completas; "
              f"{summary['valid_records']} registros.\nResumo: {summary_path}", flush=True)
    return 0 if summary['status'] == 'completed' else 1


if __name__ == '__main__':
    raise SystemExit(main())
