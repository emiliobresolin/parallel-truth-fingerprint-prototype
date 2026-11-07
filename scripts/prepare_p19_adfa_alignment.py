"""Materialize the owner-approved ADFA alignment, preserving the old protocol.

prepare freezes the decision; verify records focused tests, locks the raw-source
surface and finalizes the runnable config. Neither action trains on ADFA.
"""
from __future__ import annotations
import argparse
import ast
from dataclasses import replace
from datetime import datetime, timezone
import hashlib
import json
import os
from pathlib import Path
import subprocess
import sys

ROOT = Path(__file__).resolve().parents[1]
sys.path.insert(0, str(ROOT / 'src'))
sys.path.insert(0, str(ROOT))
os.environ.setdefault('KERAS_BACKEND', 'torch')
from parallel_truth_fingerprint.evidence.parameter_evidence import (
    load_parameter_catalog, canonical_parameter_catalog_bytes,
    decision_record_identity, parameter_revision_identity, parameter_catalog_identity,
)
from parallel_truth_fingerprint.lstm_service.offline_training.academic_runner import (
    _numeric_authority_gate, academic_paths, config_identity, load_academic_config,
)
from scripts.authorize_academic_matrix_v2 import (
    _artifact_identity, _publish_immutable, lock_truth, finalize,
)

BASE = ROOT / 'output/dissertacao/professor_inputs/p19_alinhamento/v3'
PREFIX = 'configs/experiments/p19-adfa-aligned-v3'
CONFIG = ROOT / (PREFIX + '.json')
AUTHORIZED = ROOT / (PREFIX + '.authorized.json')

def now():
    return datetime.now(timezone.utc).isoformat(timespec='microseconds').replace('+00:00', 'Z')

def sha(payload):
    return 'sha256:' + hashlib.sha256(payload).hexdigest()

def encoded(value):
    return (json.dumps(value, ensure_ascii=False, sort_keys=True, indent=2, allow_nan=False)+'\n').encode('utf-8')

def publish(path, value):
    payload = encoded(value)
    _publish_immutable(path, payload)
    return sha(payload)

def prepare():
    if AUTHORIZED.exists():
        print('Preparação já registrada; use verify ou o comando de execução.')
        return
    original_path = ROOT / 'evidence/academic/thesis-evaluation-v2/73c6eadb15c3c35a/frozen-config.json'
    original = json.loads(original_path.read_text(encoding='utf-8'))
    config = json.loads(json.dumps(original))
    config['output_root'] = 'evidence/academic-p19-aligned'
    config['protocol_version'] = '2026-11-03-p19-alignment-v1'
    config['datasets']['adfa-ld']['window']['stride'] = 128
    config['datasets']['adfa-ld']['window']['aggregation'] = 'max'
    approval = {
        'data_registro': now(), 'autor': 'Emilio',
        'mensagem_aprovacao': 'aprovo, e sim!',
        'escopo': 'Preparar configuração separada, verificação curta e comando manual para ADFA-LD: avanço 128, agregação max, janela 128; preservar demais receitas, partições, seeds e regras de calibração.',
        'origem': 'Aprovação explícita na conversa após proposta de alinhamento P19.',
        'limite_execucao': 'A execução completa é manual pelo autor, somente piloto ADFA-LD; não autoriza iniciar a matriz confirmatória nem treinar outras bases.',
        'interpretacao': 'Reavaliação exploratória de dados já examinados sob regras agora fixadas; não constitui confirmação independente em dados inéditos.',
        'config_original': original_path.relative_to(ROOT).as_posix(),
        'sha256_config_original': sha(original_path.read_bytes()),
        'janela_anterior': original['datasets']['adfa-ld']['window'],
        'janela_aprovada': config['datasets']['adfa-ld']['window'],
    }
    approval_hash = publish(BASE / 'aprovacao.json', approval)
    catalog = load_parameter_catalog((ROOT / original['numeric_authority']['catalog_path']).read_bytes())
    previous = catalog.decisions[0]
    old_revision = next(r for r in catalog.parameter_revisions if r.consumer_locator == '/datasets/adfa-ld/window/stride')
    values = tuple(replace(v, value=replace(v.value, scalar='128')) if v.parameter_id == old_revision.parameter_id else v for v in previous.parameter_values)
    freeze = now()
    decision = replace(previous, record_sha256='', content_sha256=approval_hash,
        approved_at=approval['data_registro'], freeze_time=freeze, parameter_values=values,
        owner='Emilio', approved_by='Emilio',
        rationale='Owner approved the P19 ADFA stride/aggregation alignment and preservation of the remaining historical numeric settings. This is not a fresh independent review of seven parameter groups.',
        limitations=previous.limitations + ('Exploratory re-evaluation of previously examined pilot data; only ADFA pilot execution is authorized here.',))
    decision = replace(decision, record_sha256=decision_record_identity(decision))
    revision = replace(old_revision, parameter_revision_id=old_revision.parameter_id+':revision-p19-v1',
        revision_sha256='', value=replace(old_revision.value, scalar='128'), owner='Emilio')
    revision = replace(revision, revision_sha256=parameter_revision_identity(revision))
    revisions = tuple(revision if r.parameter_revision_id == old_revision.parameter_revision_id else r for r in catalog.parameter_revisions)
    required_sets = tuple(replace(item, bindings=tuple(
        replace(binding, parameter_revision_id=revision.parameter_revision_id, parameter_revision_sha256=revision.revision_sha256,
                rationale='P19 owner-approved stride 128; same window length and no overlap.')
        if binding.parameter_revision_id == old_revision.parameter_revision_id else binding for binding in item.bindings)) for item in catalog.required_sets)
    updated_catalog = replace(catalog, decisions=(decision,), parameter_revisions=revisions, required_sets=required_sets)
    updated_catalog = replace(updated_catalog, required_sets=tuple(
        replace(item, catalog_identity=parameter_catalog_identity(updated_catalog))
        for item in updated_catalog.required_sets))
    catalog_path = ROOT / (PREFIX+'.parameter-evidence.json')
    catalog_bytes = canonical_parameter_catalog_bytes(updated_catalog)
    _publish_immutable(catalog_path, catalog_bytes)
    requirements = json.loads((ROOT / original['numeric_authority']['requirements_path']).read_text(encoding='utf-8'))
    slot = next(s for s in requirements['slots'] if s['consumer_locator'] == old_revision.consumer_locator)
    slot.update(value='128', parameter_revision_id=revision.parameter_revision_id, parameter_revision_sha256=revision.revision_sha256)
    requirements_path = ROOT / (PREFIX+'.requirements.json')
    requirements_hash = publish(requirements_path, requirements)
    config['numeric_authority'].update(
        catalog_path=catalog_path.relative_to(ROOT).as_posix(), catalog_sha256=sha(catalog_bytes),
        requirements_path=requirements_path.relative_to(ROOT).as_posix(), requirements_sha256=requirements_hash,
        temporal_context_path=PREFIX+'.temporal-context.json', temporal_context_sha256='UNRESOLVED')
    publish(AUTHORIZED, config)
    print(json.dumps({'authorized':str(AUTHORIZED),'freeze_time':freeze,'decision_sha256':decision.record_sha256},ensure_ascii=False))

def verify(test_paths=None, preparation_scope='pilot ADFA-LD only', expected_cells=8):
    if CONFIG.exists():
        config = load_academic_config(CONFIG)
        gate = _numeric_authority_gate(config, project_root=ROOT)
        assert gate['accountability_outcome'] == 'accountable', gate
        print('Configuração final já verificada:', CONFIG)
        return
    config = load_academic_config(AUTHORIZED)
    catalog = load_parameter_catalog((ROOT/config['numeric_authority']['catalog_path']).read_bytes())
    decision = catalog.decisions[0]
    command = [sys.executable,'-B','-m','pytest','-q',*(test_paths or [
        'tests/lstm_service/offline_training/test_academic_protocol.py',
        'tests/lstm_service/offline_training/test_academic_runner.py',
        'tests/lstm_service/offline_training/test_academic_numeric_schema.py',
        'tests/lstm_service/offline_training/test_academic_report_cli.py'])]
    started = now()
    result = subprocess.run(command,cwd=ROOT,capture_output=True,text=True,encoding='utf-8',errors='replace')
    completed = now()
    stdout_path, stderr_path = BASE/'tests.stdout.txt', BASE/'tests.stderr.txt'
    _publish_immutable(stdout_path,result.stdout.encode('utf-8'))
    _publish_immutable(stderr_path,result.stderr.encode('utf-8'))
    print(result.stdout[-3500:])
    if result.returncode:
        raise RuntimeError('Verificação falhou; veja tests.stdout.txt e tests.stderr.txt. Configuração final não publicada.')
    lock = dict(schema_version='academic-matrix-v2-test-lock-v1',experiment_id=config['experiment_id'],
        config_identity=config_identity(config),freeze_identity=decision.record_sha256,started_at=started,
        completed_at=completed,command=command,exit_code=0,passed=True,
        stdout_artifact=dict(path=stdout_path.relative_to(ROOT).as_posix(),sha256=sha(stdout_path.read_bytes()),byte_size=stdout_path.stat().st_size),
        stderr_artifact=dict(path=stderr_path.relative_to(ROOT).as_posix(),sha256=sha(stderr_path.read_bytes()),byte_size=stderr_path.stat().st_size),identity='')
    lock['identity'] = _artifact_identity(lock)
    test_path = BASE/'test-lock.json'
    publish(test_path,lock)
    # Preserve the existing metadata-only source inventory without parsing data.
    truth_path = BASE/'truth-lock.json'
    lock_truth(authorized_config_path=AUTHORIZED,test_lock_path=test_path,truth_lock_path=truth_path)
    finalize(authorized_config_path=AUTHORIZED,test_lock_path=test_path,truth_lock_path=truth_path,
        temporal_context_path=ROOT/(PREFIX+'.temporal-context.json'),frozen_config_path=CONFIG)
    final_config=load_academic_config(CONFIG)
    gate=_numeric_authority_gate(final_config,project_root=ROOT)
    assert gate['accountability_outcome']=='accountable', gate
    paths=academic_paths(final_config,project_root=ROOT,phase='pilot')
    publish(BASE/'preparacao.json',dict(config=CONFIG.relative_to(ROOT).as_posix(),config_identity=config_identity(final_config),
        numeric_authority=gate['accountability_outcome'],resultado=paths.root.relative_to(ROOT).as_posix(),
        scope=preparation_scope,expected_cells=expected_cells,tests_passed=True))
    print('Configuração pronta:',CONFIG)
    print('Resultados:',paths.root)

def summary():
    config=load_academic_config(CONFIG)
    paths=academic_paths(config,project_root=ROOT,phase='pilot')
    cells=[]
    for path in sorted(paths.cells.glob('adfa-ld__*.json')):
        cell=json.loads(path.read_text(encoding='utf-8'))
        if cell.get('status') != 'complete':
            continue
        data=cell['data']
        assert data['windowing']['stride']==128 and data['windowing']['aggregation']=='max'
        assert cell['config_identity']==config_identity(config)
        cells.append(dict(model=cell['model'],seed=cell['seed'],cell=path.relative_to(ROOT).as_posix(),
            units=data['support'],windows=data['windowing']['window_count'],
            auroc=cell['test']['ranking']['auroc'],operating=cell['test']['operating']))
    assert len(cells)==8, f'Esperadas oito celulas completas; encontradas {len(cells)}.'
    expected={(name,seed) for name,settings in config['datasets']['adfa-ld']['models'].items()
              for seed in (config['pilot_seeds'][:1] if settings['deterministic'] else config['pilot_seeds'])}
    assert {(c['model'],c['seed']) for c in cells}==expected
    record=dict(status='complete',config_identity=config_identity(config),dataset='adfa-ld',
        interpretation='Exploratory aligned pilot, not an independent confirmatory study',cells=cells)
    (BASE/'resultado_resumo.json').write_bytes(encoded(record))
    print('Oito celulas completas. Resumo:',BASE/'resultado_resumo.json')

def check_launchers():
    for filename in ['prepare_p19_adfa_alignment.py','run_p19_adfa_alignment.py']:
        ast.parse((ROOT/'scripts'/filename).read_text(encoding='utf-8'))
    ps_command = "$parseTokens = $null; $parseProblems = $null; [System.Management.Automation.Language.Parser]::ParseFile('scripts/run_p19_adfa_alignment.ps1', [ref]$parseTokens, [ref]$parseProblems) | Out-Null; if ($parseProblems.Count) { $parseProblems | Out-String | Write-Output; exit 1 }"
    result=subprocess.run(['powershell','-NoProfile','-Command',ps_command],cwd=ROOT,capture_output=True,text=True)
    assert result.returncode==0, result.stdout+result.stderr
    print('Sintaxe dos dois scripts Python e do launcher PowerShell conferida.')

if __name__ == '__main__':
    parser=argparse.ArgumentParser(description=__doc__)
    parser.add_argument('action',choices=['prepare','verify','summary','check'])
    action=parser.parse_args().action
    {'prepare':prepare,'verify':verify,'summary':summary,'check':check_launchers}[action]()
