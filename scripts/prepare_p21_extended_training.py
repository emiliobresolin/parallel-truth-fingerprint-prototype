"""Freeze the approved 48-epoch public pilot, with current F1 implementation."""
import argparse
import ast
from dataclasses import replace
import json
import os
from pathlib import Path
import sys
import subprocess

ROOT=Path(__file__).resolve().parents[1]
sys.path.insert(0,str(ROOT))
sys.path.insert(0,str(ROOT/'src'))
os.environ.setdefault('KERAS_BACKEND','torch')
from scripts import prepare_p19_adfa_alignment as common
from parallel_truth_fingerprint.evidence.parameter_evidence import (
    load_parameter_catalog,canonical_parameter_catalog_bytes,parameter_catalog_identity,
    decision_record_identity,parameter_revision_identity,
)
from parallel_truth_fingerprint.lstm_service.offline_training.academic_runner import (
    academic_paths,config_identity,load_academic_config,_numeric_authority_gate,
)

BASE=ROOT/'output/dissertacao/professor_inputs/p21_treino_ampliado/v1'
PREFIX='configs/experiments/p21-public-48epochs-v1'
CONFIG=ROOT/(PREFIX+'.json')
AUTHORIZED=ROOT/(PREFIX+'.authorized.json')

def prepare():
    if AUTHORIZED.exists():
        print('Preparação existente:',AUTHORIZED)
        return
    original_path=ROOT/'configs/experiments/p19-adfa-aligned-v3.json'
    original=load_academic_config(original_path)
    config=json.loads(json.dumps(original))
    config['output_root']='evidence/academic-p21-extended'
    config['protocol_version']='2026-11-03-p21-48epochs-v1'
    changes={f'/datasets/{name}/models/recurrent-autoencoder/epochs':48 for name in config['datasets']}
    for name in config['datasets']:
        config['datasets'][name]['models']['recurrent-autoencoder']['epochs']=48
        assert config['datasets'][name]['window']['stride']==128
        assert config['datasets'][name]['window']['aggregation']=='max'
    approval=dict(registered_at=common.now(),owner='Emilio',
        statement='vamos reparar o q tiver q reparar e rodar novamente',
        scope='Prepare manual re-evaluation of public bases using the planned maximum of 48 epochs, existing five seeds, early stopping and corrected F1. Deterministic controls are cheap and will be recalculated under the same new core.',
        rationale='Fourteen of fifteen previous fits reached best normal validation at the old twelve-epoch limit; investigate convergence rather than promise improved attack detection.',
        changes=changes,source_config=original_path.relative_to(ROOT).as_posix(),source_config_sha256=common.sha(original_path.read_bytes()),
        constraints=['Manual long execution by owner','No custom compressor training in this invocation','Preserve twelve-epoch artifacts','Exploratory pilot, previously examined test data','No change to feature sets, source selections, partitions, seeds, optimizer, batch size, early stopping or normal calibration rule'])
    approval_hash=common.publish(BASE/'aprovacao.json',approval)
    catalog=load_parameter_catalog((ROOT/original['numeric_authority']['catalog_path']).read_bytes())
    changed_revisions={}; changed_values={}
    for old in catalog.parameter_revisions:
        if old.consumer_locator not in changes: continue
        revision=replace(old,parameter_revision_id=old.parameter_id+':revision-p21-v1',revision_sha256='',
            value=replace(old.value,scalar='48'),owner='Emilio')
        revision=replace(revision,revision_sha256=parameter_revision_identity(revision))
        changed_revisions[old.parameter_revision_id]=revision
        changed_values[old.parameter_id]='48'
    assert len(changed_revisions)==3
    previous=catalog.decisions[0]
    decision=replace(previous,record_sha256='',content_sha256=approval_hash,owner='Emilio',approved_by='Emilio',
        approved_at=approval['registered_at'],freeze_time=common.now(),
        parameter_values=tuple(replace(v,value=replace(v.value,scalar=changed_values[v.parameter_id])) if v.parameter_id in changed_values else v for v in previous.parameter_values),
        rationale='Owner approved increasing the recurrent epoch cap from twelve to forty-eight in all three public datasets, preserving other settings and recalculating controls under the corrected metric core.',
        limitations=('Existing public test data were previously examined; this is exploratory re-evaluation.',
            'Only pilot evaluation is authorized by this preparation; confirmation and compressor evaluation remain separate.',
            'A higher epoch cap is an approved investigation budget, not an optimum guaranteed by external documentation.'))
    decision=replace(decision,record_sha256=decision_record_identity(decision))
    required_sets=tuple(replace(item,bindings=tuple(
        replace(binding,parameter_revision_id=changed_revisions[binding.parameter_revision_id].parameter_revision_id,
                parameter_revision_sha256=changed_revisions[binding.parameter_revision_id].revision_sha256,
                rationale='Owner-approved P21 epoch budget 48.')
        if binding.parameter_revision_id in changed_revisions else binding for binding in item.bindings)) for item in catalog.required_sets)
    updated=replace(catalog,decisions=(decision,),required_sets=required_sets,
        parameter_revisions=tuple(changed_revisions.get(r.parameter_revision_id,r) for r in catalog.parameter_revisions))
    updated=replace(updated,required_sets=tuple(replace(r,catalog_identity=parameter_catalog_identity(updated)) for r in updated.required_sets))
    catalog_path=ROOT/(PREFIX+'.parameter-evidence.json')
    catalog_bytes=canonical_parameter_catalog_bytes(updated)
    common._publish_immutable(catalog_path,catalog_bytes)
    requirements=json.loads((ROOT/original['numeric_authority']['requirements_path']).read_text(encoding='utf-8'))
    for slot in requirements['slots']:
        revision=changed_revisions.get(slot['parameter_revision_id'])
        if revision:
            slot.update(value='48',parameter_revision_id=revision.parameter_revision_id,parameter_revision_sha256=revision.revision_sha256)
    requirements_path=ROOT/(PREFIX+'.requirements.json')
    req_hash=common.publish(requirements_path,requirements)
    config['numeric_authority'].update(requirements_path=requirements_path.relative_to(ROOT).as_posix(),requirements_sha256=req_hash,
        catalog_path=catalog_path.relative_to(ROOT).as_posix(),catalog_sha256=common.sha(catalog_bytes),
        temporal_context_path=PREFIX+'.temporal-context.json',temporal_context_sha256='UNRESOLVED')
    common.publish(AUTHORIZED,config)
    print('Configuração autorizada:',AUTHORIZED)

def verify():
    # Reuse the same immutable test/source lock and parameter-gate procedure.
    common.BASE=BASE; common.PREFIX=PREFIX; common.CONFIG=CONFIG; common.AUTHORIZED=AUTHORIZED
    common.verify(preparation_scope='Three public pilot bases; all methods; LSTM up to 48 epochs',expected_cells=23,test_paths=[
        'tests/lstm_service/offline_training/test_academic_metrics.py',
        'tests/lstm_service/offline_training/test_academic_protocol.py',
        'tests/lstm_service/offline_training/test_academic_runner.py',
        'tests/lstm_service/offline_training/test_academic_numeric_schema.py',
        'tests/lstm_service/offline_training/test_academic_report_cli.py'])
    config=load_academic_config(CONFIG)
    gate=_numeric_authority_gate(config,project_root=ROOT)
    assert gate['accountability_outcome']=='accountable'
    paths=academic_paths(config,project_root=ROOT,phase='pilot')
    common.publish(BASE/'preparacao_completa.json',dict(config=CONFIG.relative_to(ROOT).as_posix(),
        config_identity=config_identity(config),resultado=paths.root.relative_to(ROOT).as_posix(),
        expected_cells=23,lstm_cells=15,deterministic_cells=8,scope='Three public pilot bases; all methods; LSTM up to 48 epochs',
        seeds=config['pilot_seeds'],numeric_authority='accountable',long_execution_started=False))
    print('Preparação completa: 23 células, cinco seeds LSTM por base.')

def summary():
    config=load_academic_config(CONFIG)
    paths=academic_paths(config,project_root=ROOT,phase='pilot')
    expected={(name,model,seed) for name,dataset in config['datasets'].items() for model,settings in dataset['models'].items()
        for seed in (config['pilot_seeds'][:1] if settings['deterministic'] else config['pilot_seeds'])}
    cells=[]
    for path in sorted(paths.cells.glob('*.json')):
        row=json.loads(path.read_text(encoding='utf-8'))
        if row.get('status')!='complete': continue
        assert row['config_identity']==config_identity(config)
        if row['model']=='recurrent-autoencoder':
            assert row['model_fit']['epochs_planned']==48
            assert 1<=row['model_fit']['epochs_executed']<=48
        cells.append(dict(dataset=row['dataset_key'],model=row['model'],seed=row['seed'],
            epochs=row['model_fit']['epochs_executed'],cell=path.relative_to(ROOT).as_posix(),
            operating=row['test']['operating'],ranking=row['test']['ranking']))
    assert {(r['dataset'],r['model'],r['seed']) for r in cells}==expected
    assert len(cells)==23
    report=json.loads((paths.phase/'run-summary.json').read_text(encoding='utf-8'))
    assert not report['failed']
    gate=report['eligibility_gate']
    assert gate['exact_matrix_match'] and gate['prediction_artifacts_verified'] and gate['raw_evidence_reconstructed'],gate['reasons']
    (BASE/'resultado_resumo.json').write_bytes(common.encoded(dict(status='complete',cells=cells,
        interpretation='Exploratory 48-epoch-budget public pilot; not a confirmatory matrix.')))
    print('23 células completas e autenticadas. Resumo:',BASE/'resultado_resumo.json')

def check():
    for filename in ['prepare_p19_adfa_alignment.py','prepare_p21_extended_training.py','run_p21_extended_training.py']:
        ast.parse((ROOT/'scripts'/filename).read_text(encoding='utf-8'))
    command="$parseTokens=$null; $parseProblems=$null; [System.Management.Automation.Language.Parser]::ParseFile('scripts/run_p21_extended_training.ps1',[ref]$parseTokens,[ref]$parseProblems) | Out-Null; if ($parseProblems.Count) { $parseProblems | Out-String | Write-Output; exit 1 }"
    result=subprocess.run(['powershell','-NoProfile','-Command',command],cwd=ROOT,capture_output=True,text=True)
    assert result.returncode==0,result.stdout+result.stderr
    original=load_academic_config(ROOT/'configs/experiments/p19-adfa-aligned-v3.json')
    config=load_academic_config(CONFIG)
    for name in config['datasets']:
        expected=json.loads(json.dumps(original['datasets'][name]))
        expected['models']['recurrent-autoencoder']['epochs']=48
        assert config['datasets'][name]==expected
    assert config['pilot_seeds']==original['pilot_seeds']==[101,211,307,419,523]
    assert config['statistical_protocol']==original['statistical_protocol']
    assert config['validation_protocol']==original['validation_protocol']
    print('Sintaxe e configuração verificadas: somente os três tetos de épocas mudaram nas receitas.')

if __name__=='__main__':
    parser=argparse.ArgumentParser(description=__doc__)
    parser.add_argument('action',choices=['prepare','verify','summary','check'])
    action=parser.parse_args().action
    {'prepare':prepare,'verify':verify,'summary':summary,'check':check}[action]()
