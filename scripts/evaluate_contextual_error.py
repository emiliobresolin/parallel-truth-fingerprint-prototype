"""Evaluate a declared relational score on frozen contextual LSTM weights."""
from datetime import datetime, timezone
from pathlib import Path
import argparse
import json
import sys

ROOT=Path(__file__).resolve().parents[1]
sys.path.insert(0,str(ROOT/'src'))
sys.path.insert(0,str(ROOT/'scripts'))
from evaluate_replay_training_offline import source_hashes,save
from parallel_truth_fingerprint.evidence.contextual_replay import metrics
from parallel_truth_fingerprint.evidence.contextual_error import components
from parallel_truth_fingerprint.evidence.replay_calibration import calibrate, anomalous, LEGACY, COMMON


def run_profile(source,output,keras,torch,np,rule=LEGACY):
    model=keras.models.model_from_json((source/'architecture.json').read_text())
    model.load_weights(str(source/'model.weights.h5'))
    records=json.loads((source/'scores.json').read_text())
    calibration=np.load(source/'calibration.npy')
    test=np.asarray([r['input_window'] for r in records],dtype='float32')
    def evaluate(x):
        with torch.inference_mode():
            y=keras.ops.convert_to_numpy(model(x,training=False))
        return components(x,y)
    cal,test_components=evaluate(calibration),evaluate(test)
    if not np.allclose(test_components['global_mse'],[r['contextual_score'] for r in records],rtol=1e-5,atol=1e-8):
        raise ValueError('Frozen contextual model did not reproduce scores.')
    old_cal=json.loads((source/'calibration.json').read_text())
    if not np.allclose(cal['global_mse'],old_cal['scores'],rtol=1e-5,atol=1e-8):
        raise ValueError('Frozen model calibration mismatch.')
    thresholds={name:calibrate(values.tolist(),rule) for name,values in cal.items()}
    scored=[]
    for i,r in enumerate(records):
        selected={key:r[key] for key in ('round_id','block','offset','condition','boundary')}
        for method,values in test_components.items():
            selected[method+'_score']=float(values[i])
            selected[method+'_anomalous']=anomalous(values[i],thresholds[method]['threshold'],rule)
        selected['comparator_anomalous']=r['comparator_anomalous']
        scored.append(selected)
    methods={name:name+'_anomalous' for name in test_components}
    methods['comparator']='comparator_anomalous'
    summary={'profile':source.name,'metrics':{name:metrics(scored,field) for name,field in methods.items()},
        'metrics_without_boundary':{name:metrics(scored,field,True) for name,field in methods.items()},
        'thresholds':{name:value['threshold'] for name,value in thresholds.items()},
        'normal_calibration_common_fraction':float(cal['common_error'].mean()/cal['global_mse'].mean()),
        'frozen_model_source':str(source),'global_scores_reproduced':True}
    output.mkdir()
    save(output/'calibration.json',{name:dict(value,scores=cal[name].tolist()) for name,value in thresholds.items()})
    save(output/'scores.json',scored)
    save(output/'summary.json',summary)
    return summary


def verify_output(output):
    from parallel_truth_fingerprint.evidence.paired_syscalls import digest
    output=Path(output)
    for name,h in json.loads((output/'manifest.json').read_text()).items():
        if digest(output/name)!=h:
            raise ValueError('Relational output hash mismatch.')
    protocol=json.loads((output/'protocol.json').read_text())
    rule=protocol.get('calibration_rule',LEGACY)
    source=Path(protocol['contextual_source'])
    if source_hashes(source)!=json.loads((output/'source-hashes.json').read_text()):
        raise ValueError('Contextual source changed.')
    summary=json.loads((output/'summary.json').read_text())
    if summary['status']!='completed':
        raise ValueError('Relational evaluation incomplete.')
    for name,p in summary['profiles'].items():
        profile=output/name
        cal=json.loads((profile/'calibration.json').read_text())
        records=json.loads((profile/'scores.json').read_text())
        original=json.loads((source/name/'scores.json').read_text())
        if len(records)!=len(original):
            raise ValueError('Relational evaluation row count mismatch.')
        for r,old in zip(records,original):
            if any(r[key]!=old[key] for key in ('round_id','block','offset','condition','boundary','comparator_anomalous')):
                raise ValueError('Relational evaluation changed source identity or comparator.')
        for method,entry in cal.items():
            expected=calibrate(entry['scores'],rule)
            if any(entry.get(key)!=value for key,value in expected.items()):
                raise ValueError('Relational calibration mismatch.')
            if p['thresholds'][method]!=entry['threshold']:
                raise ValueError('Relational summary threshold mismatch.')
            if any(r[method+'_anomalous']!=anomalous(r[method+'_score'],entry['threshold'],rule) for r in records):
                raise ValueError('Relational decision mismatch.')
        for method in (*cal,'comparator'):
            if metrics(records,method+'_anomalous')!=p['metrics'][method]:
                raise ValueError('Relational metrics mismatch.')
            if metrics(records,method+'_anomalous',True)!=p['metrics_without_boundary'][method]:
                raise ValueError('Relational non-boundary metrics mismatch.')
    return summary


def main():
    parser=argparse.ArgumentParser(description=__doc__)
    parser.add_argument('--contextual',type=Path,required=True)
    parser.add_argument('--output',type=Path)
    parser.add_argument('--prospective',action='store_true')
    parser.add_argument('--calibration-rule',choices=(LEGACY,COMMON),default=LEGACY)
    args=parser.parse_args()
    source=args.contextual.resolve()
    if json.loads((source/'summary.json').read_text())['status']!='completed':
        raise ValueError('A completed contextual fit is required.')
    from parallel_truth_fingerprint.evidence.paired_syscalls import digest
    for name,h in json.loads((source/'manifest.json').read_text()).items():
        if digest(source/name)!=h:
            raise ValueError('Contextual input hash mismatch.')
    output=args.output.resolve() if args.output else ROOT/'output/contextual-error-diagnostic'/datetime.now(timezone.utc).strftime('%Y%m%dT%H%M%S%fZ')
    if source==output or source in output.parents or output in source.parents:
        raise ValueError('Source and output must be separate.')
    output.mkdir(parents=True,exist_ok=False)
    hashes=source_hashes(source)
    save(output/'source-hashes.json',hashes)
    save(output/'protocol.json',{'version':'contextual-relational-error-v1','contextual_source':str(source),
        'mode':'technical-smoke' if json.loads((source/'protocol.json').read_text())['mode']=='technical-smoke' else
               'prospective-fixed' if args.prospective else 'posthoc-exploratory-diagnostic',
        'definition':'ep=predicted_physical-observed_physical; es=predicted_supervisory-observed_supervisory; relational=mean(((ep-es)/2)^2)',
        'identity':'global_MSE = mean(((ep+es)/2)^2) + mean(((ep-es)/2)^2)',
        'control':'direct_gap=mean(((observed_physical-observed_supervisory)/2)^2), same scale and calibration rule',
        'calibration_rule':args.calibration_rule,
        'threshold':'target normal calibration FPR <= 0.01; academic candidate rule; score >= threshold; no floor' if args.calibration_rule==COMMON else 'normal calibration mean+3 population std; floor 1e-6',
        'selection':'no weight changes; retain global, common, relational, direct and comparator outcomes'})
    summary={'status':'running','started_at':datetime.now(timezone.utc).isoformat(),'profiles':{}}
    save(output/'summary.json',summary)
    print(f'Diagnostico: {output}',flush=True)
    try:
        import numpy as np
        import torch
        torch.set_num_threads(1)
        from parallel_truth_fingerprint.lstm_service.trainer import _load_keras_module
        keras=_load_keras_module()
        for name in ('unmodulated','modulated'):
            summary['profiles'][name]=run_profile(source/name,output/name,keras,torch,np,args.calibration_rule)
        if source_hashes(source)!=hashes:
            raise ValueError('Contextual fit changed.')
        summary.update(status='completed',source_unchanged=True)
    except BaseException as error:
        summary.update(status='failed',error=str(error))
        raise
    finally:
        summary['finished_at']=datetime.now(timezone.utc).isoformat()
        save(output/'summary.json',summary)
        save(output/'manifest.json',source_hashes(output))
    verify_output(output)
    print('Relational score and controls verified.',flush=True)


if __name__=='__main__':
    main()
