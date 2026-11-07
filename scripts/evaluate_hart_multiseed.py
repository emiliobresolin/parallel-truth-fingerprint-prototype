"""Five fixed training seeds on one immutable HART collection."""
from datetime import datetime, timezone
import argparse
import json
from pathlib import Path
import statistics
import sys

ROOT=Path(__file__).resolve().parents[1]
sys.path[:0]=[str(ROOT/'src'),str(ROOT/'scripts')]
from evaluate_hart_totalizer import evaluate_collection,verify_output,digest
from evaluate_replay_training_offline import source_hashes,save

SEEDS=(101,211,307,419,523)
PROFILES=('unmodulated','modulated')
VARIANTS=('hart_totalizer','currents_only')

def implementation_hashes():
    paths=['scripts/evaluate_hart_totalizer.py','scripts/evaluate_hart_multiseed.py',
        'src/parallel_truth_fingerprint/evidence/hart_totalizer.py',
        'src/parallel_truth_fingerprint/evidence/replay_calibration.py',
        'src/parallel_truth_fingerprint/lstm_service/trainer.py']
    return {p:digest(ROOT/p) for p in paths}

def aggregate(summaries):
    if set(summaries)!=set(SEEDS): raise ValueError('Expected all five fixed seeds.')
    result={}
    for profile in PROFILES:
        result[profile]={}
        for variant in VARIANTS:
            records=[summaries[seed]['profiles'][profile][variant] for seed in SEEDS]
            first=records[0]['metrics']; combined={}
            for record in records:
                if record['metrics'].keys()!=first.keys(): raise ValueError('Method mismatch across seeds.')
            for method,conditions in first.items():
                if any(record['metrics'][method].keys()!=conditions.keys() for record in records):
                    raise ValueError('Condition mismatch across seeds.')
                combined[method]={}
                for condition in conditions:
                    values=[r['metrics'][method][condition] for r in records]
                    counts={r['count'] for r in values}
                    if len(counts)!=1 or {r['rate_role'] for r in values}!={values[0]['rate_role']}:
                        raise ValueError('Different evaluation support across seeds.')
                    rates=[r['rate'] for r in values]
                    if method in ('direct_gap','comparator') and len(set(rates))!=1:
                        raise ValueError('Deterministic control changed across training seeds.')
                    combined[method][condition]={
                        'training_fits':len(SEEDS),'evaluations_per_fit':values[0]['count'],
                        'rate_role':values[0]['rate_role'],'rates_by_seed':dict(zip(map(str,SEEDS),rates)),
                        'mean_rate':statistics.mean(rates),'min_rate':min(rates),'max_rate':max(rates),
                        'sample_sd_rate':statistics.stdev(rates),
                        'interpretation':'Five training fits on the same physical observations; counts are not multiplied into independent observations.'}
            result[profile][variant]=combined
    return result

def verify_multi(output):
    output=Path(output)
    manifest=json.loads((output/'manifest.json').read_text(encoding='utf-8'))
    for name,expected in manifest.items():
        path=(output/name).resolve()
        if not path.is_relative_to(output.resolve()) or digest(path)!=expected: raise ValueError('Multi-seed artifact hash mismatch.')
    protocol=json.loads((output/'protocol.json').read_text(encoding='utf-8'))
    if protocol['version']!='hart-five-seeds-v1' or protocol['training_seeds']!=list(SEEDS): raise ValueError('Invalid multi-seed protocol.')
    if protocol['implementation_hashes']!=implementation_hashes(): raise ValueError('Evaluation implementation changed.')
    source=Path(protocol['source_collection'])
    if source_hashes(source)!=json.loads((output/'source-hashes.json').read_text(encoding='utf-8')):
        raise ValueError('Shared acquisition changed.')
    root=json.loads((output/'summary.json').read_text(encoding='utf-8'))
    if root['status']!='completed' or root['model_fits']!=20 or set(root['seed_folders'])!=set(map(str,SEEDS)):
        raise ValueError('Incomplete five-seed evaluation.')
    summaries={}; common_lineage={}
    for seed in SEEDS:
        relative=root['seed_folders'][str(seed)]
        folder=(output/relative).resolve()
        if not folder.is_relative_to(output.resolve()): raise ValueError('Invalid seed folder.')
        child=json.loads((folder/'protocol.json').read_text(encoding='utf-8'))
        if child['seed']!=seed or Path(child['source_collection'])!=source or child['technical_smoke']!=protocol['technical_smoke']:
            raise ValueError('Seed or source mismatch.')
        summaries[seed]=verify_output(folder)
        for profile in PROFILES:
            for variant in VARIANTS:
                lineage=json.loads((folder/profile/variant/'partitions.json').read_text(encoding='utf-8'))
                key=(profile,variant)
                if common_lineage.setdefault(key,lineage)!=lineage: raise ValueError('Partition mismatch across seeds.')
    if aggregate(summaries)!=root['aggregate']: raise ValueError('Aggregated seed metrics differ.')
    return root

def run(source,output,*,technical=False):
    source,output=Path(source).resolve(),Path(output).resolve()
    if source==output or source in output.parents or output in source.parents: raise ValueError('Separate source and output required.')
    if (output/'manifest.json').exists():
        result=verify_multi(output);print('Five-seed evaluation already complete and verified.',flush=True);return result
    before=source_hashes(source)
    if not before: raise ValueError('Missing acquisition source.')
    output.mkdir(parents=True,exist_ok=True)
    protocol={'version':'hart-five-seeds-v1','source_collection':str(source),'training_seeds':list(SEEDS),
        'technical_smoke':technical,'simulation_seed':json.loads((source/'protocol.json').read_text(encoding='utf-8'))['parameters']['simulation_seed'],
        'model_fits':20,'profiles':list(PROFILES),'variants':list(VARIANTS),
        'max_epochs':1 if technical else 300,'patience':25,'min_delta':1e-6,
        'model_selection':'normal validation; best weights restored','threshold_selection':'separate normal calibration, target FPR 1%',
        'acquisition_repetitions':'One shared acquisition session with paired views; seeds replicate training only.',
        'implementation_hashes':implementation_hashes()}
    protocol_path=output/'protocol.json'
    if protocol_path.exists():
        if json.loads(protocol_path.read_text(encoding='utf-8'))!=protocol or json.loads((output/'source-hashes.json').read_text(encoding='utf-8'))!=before:
            raise ValueError('Cannot resume after source, recipe or implementation changed.')
    else:
        save(protocol_path,protocol);save(output/'source-hashes.json',before)
    status={'status':'running','started_at':datetime.now(timezone.utc).isoformat(),'seed_folders':{},'completed_seeds':[],'model_fits':0}
    summaries={}
    for seed in SEEDS:
        candidates=sorted(output.glob(f'seed-{seed}-attempt-*'))
        folder=None
        for candidate in candidates:
            if (candidate/'manifest.json').exists():
                child=json.loads((candidate/'protocol.json').read_text(encoding='utf-8'))
                if child['seed']!=seed or Path(child['source_collection'])!=source: raise ValueError('Resume identity mismatch.')
                summaries[seed]=verify_output(candidate);folder=candidate;break
        if folder is None:
            number=1
            while (output/f'seed-{seed}-attempt-{number:02d}').exists(): number+=1
            folder=output/f'seed-{seed}-attempt-{number:02d}'
            print(f'Seed {seed}: treinamento pareado ({len(summaries)+1}/5).',flush=True)
            summaries[seed]=evaluate_collection(source,folder,technical=technical,seed=seed,versioned_seed=True)
        status['seed_folders'][str(seed)]=folder.relative_to(output).as_posix()
        status['completed_seeds']=list(summaries);status['model_fits']=len(summaries)*4
        save(output/'summary.json',status)
        print(f'Concluidos {len(summaries)}/5 seeds e {len(summaries)*4}/20 modelos.',flush=True)
    if source_hashes(source)!=before: raise ValueError('Acquisition source changed during training.')
    status.update(status='completed',aggregate=aggregate(summaries),source_unchanged=True,finished_at=datetime.now(timezone.utc).isoformat())
    save(output/'summary.json',status)
    save(output/'manifest.json',{str(p.relative_to(output)):digest(p) for p in output.rglob('*') if p.is_file() and p!=output/'manifest.json'})
    result=verify_multi(output)
    print('Cinco seeds e vinte modelos verificados; coleta compartilhada preservada.',flush=True)
    return result

if __name__=='__main__':
    parser=argparse.ArgumentParser(description=__doc__)
    parser.add_argument('--source',type=Path,required=True);parser.add_argument('--output',type=Path,required=True)
    parser.add_argument('--smoke',action='store_true')
    args=parser.parse_args();run(args.source,args.output,technical=args.smoke)
