"""One fixed offline investigation: contemporaneous physical + supervisory inputs."""
from datetime import datetime, timezone
from pathlib import Path
import argparse
import csv
import hashlib
import json
import sys

ROOT = Path(__file__).resolve().parents[1]
sys.path.insert(0,str(ROOT/'src'))
sys.path.insert(0,str(ROOT/'scripts'))
from evaluate_replay_training_offline import prepare, source_hashes, save
from parallel_truth_fingerprint.evidence.contextual_replay import test_windows, metrics


def weight_hash(model):
    return hashlib.sha256(b''.join(v.tobytes() for v in model.get_weights())).hexdigest()


def run_profile(session, name, output, keras, torch, np, technical=False):
    from parallel_truth_fingerprint.evidence.replay_evaluation import fixed_threshold
    from parallel_truth_fingerprint.lstm_service.trainer import build_lstm_autoencoder
    source, baseline_root = session/'collection'/name, session/'training'/name
    rows = [json.loads(line) for line in (source/'observations.jsonl').read_text(encoding='utf-8').splitlines()]
    indices, physical, partitions = prepare(rows,technical=technical)
    if len(indices)!=4:
        raise ValueError('This investigation requires the completed four-instrument dataset.')
    # Check the logged normal supervisory projection, rather than assuming alignment.
    for row in rows:
        for i in indices:
            sensor = row['feature_schema'][i].split('.')[0]
            if row['physical_vector'][i] != row['physical_scada']['behavioral_sensor_values'][sensor]['loop_current_ma']:
                raise ValueError('Normal supervisory projection differs from declared physical reference.')
    contextual = {phase:np.concatenate([x,x],axis=2) for phase,x in physical.items()}
    output.mkdir()
    save(output/'partitions.json',partitions)
    for phase,x in contextual.items():
        np.save(output/f'{phase}.npy',x)
    keras.utils.set_random_seed(101)
    model = build_lstm_autoencoder(keras=keras,sequence_length=2,feature_count=8,latent_units=16)
    stop = keras.callbacks.EarlyStopping(monitor='val_loss',patience=25,min_delta=1e-6,restore_best_weights=True)
    class Progress(keras.callbacks.Callback):
        def on_epoch_end(self,epoch,logs=None):
            if epoch==0 or (epoch+1)%50==0:
                print(f'{name}: epoch={epoch+1} loss={logs["loss"]:.8f} val={logs["val_loss"]:.8f}',flush=True)
    history = model.fit(contextual['fit'],contextual['fit'],
        validation_data=(contextual['validation'],contextual['validation']),
        epochs=1 if technical else 300,batch_size=8,shuffle=False,verbose=0,callbacks=[stop,Progress()])
    frozen = weight_hash(model)
    def score(detector,x):
        x=np.asarray(x,dtype='float32')
        with torch.inference_mode():
            predicted=keras.ops.convert_to_numpy(detector(x,training=False))
        errors=np.mean(np.square(predicted-x),axis=(1,2))
        if not np.isfinite(errors).all():
            raise ValueError('Non-finite score.')
        return errors
    calibration_scores=score(model,contextual['calibration']).tolist()
    calibration=fixed_threshold(calibration_scores)
    # Model and threshold fixed before assembling and scoring the test branches.
    samples=test_windows(rows,indices)
    if len(samples)!=(16 if technical else 600):
        raise ValueError('Unexpected paired test support.')
    x=np.asarray([s['input_window'] for s in samples],dtype='float32')
    new_scores=score(model,x)
    control=keras.models.model_from_json((baseline_root/'architecture.json').read_text())
    control.load_weights(str(baseline_root/'model.weights.h5'))
    control_hash=weight_hash(control)
    control_calibration=json.loads((baseline_root/'calibration.json').read_text())
    recalculated=score(control,physical['calibration'])
    if not np.allclose(recalculated,control_calibration['scores'],rtol=1e-5,atol=1e-8):
        raise ValueError('Frozen control weights failed to reproduce calibration.')
    control_scores=score(control,x[:,:,4:])
    old=json.loads((baseline_root/'scores.json').read_text())
    old_lookup={(r['round_id'],r['condition']):r for r in old}
    records=[]
    for sample,new_score,control_score in zip(samples,new_scores,control_scores):
        before=old_lookup[(sample['round_id'],sample['condition'])]
        records.append(dict(sample,contextual_score=float(new_score),
            contextual_anomalous=bool(new_score>calibration['threshold']),
            supervisory_control_score=float(control_score),
            supervisory_control_anomalous=bool(control_score>control_calibration['threshold']),
            original_score=before['score'],original_anomalous=before['anomalous']))
    if frozen!=weight_hash(model) or control_hash!=weight_hash(control):
        raise ValueError('Weights changed during test scoring.')
    models={'contextual_lstm':'contextual_anomalous','supervisory_history_control':'supervisory_control_anomalous',
            'original_hybrid_lstm':'original_anomalous','physical_scada_comparator':'comparator_anomalous'}
    summary={'profile':name,'epochs_completed':len(history.history['loss']),
        'selected_epoch':int(stop.best_epoch)+1,'threshold':calibration['threshold'],
        'control_threshold':control_calibration['threshold'],'weights_sha256':frozen,
        'control_weights_sha256':control_hash,'weights_unchanged':True,
        'features':[f'{domain}.{rows[0]["feature_schema"][i]}' for domain in ('physical','supervisory') for i in indices],
        'normal_pairing':'normal supervisory values are the same logged physical projection',
        'metrics':{method:metrics(records,field) for method,field in models.items()},
        'metrics_without_boundary':{method:metrics(records,field,True) for method,field in models.items()},
        'validation_mse':float(score(model,contextual['validation']).mean())}
    save(output/'history.json',history.history)
    save(output/'calibration.json',dict(calibration,scores=calibration_scores))
    save(output/'scores.json',records)
    save(output/'architecture.json',json.loads(model.to_json()))
    model.save_weights(str(output/'model.weights.h5'))
    save(output/'summary.json',summary)
    return summary


def write_report(output,summary):
    mode=json.loads((output/'protocol.json').read_text())['mode']
    scope=('Os resultados correspondem à nova coleta com configuração fixada previamente.' if mode=='prospective-fixed' else
           'Esta execução reduzida verifica o caminho técnico.' if mode=='technical-smoke' else
           'Os resultados reutilizam uma coleta já examinada e são exploratórios.')
    lines=['# Investigação offline — referência física e supervisória na LSTM','',
        'Entrada: duas amostras, cada uma com quatro correntes físicas e quatro supervisórias, '
        'normalizadas por (mA−4)/16. Cada visão de replay conserva seu próprio histórico após '
        'o início do episódio. O modelo é selecionado pela validação normal, com limiar de '
        'calibração normal. '+scope,'',
        'O pareamento normal reproduz o mesmo valor nos dois caminhos, conforme os registros '
        'de origem. Essa característica da emulação acompanha a interpretação dos resultados.','',
        '| Perfil | Método | Condição | Alertas / avaliações | Taxa |',
        '|---|---|---|---:|---:|']
    table=[]
    for profile,s in summary['profiles'].items():
        for method,conditions in s['metrics'].items():
            for condition,m in conditions.items():
                lines.append(f'| {profile} | {method} | {condition} | {m["alerts"]}/{m["count"]} | {100*m["rate"]:.1f}% |')
                table.append(dict(profile=profile,method=method,condition=condition,**m))
    lines+=['','O controle supervisório reutiliza os pesos e o limiar da LSTM de quatro correntes '
        'do ensaio anterior, alterando apenas o histórico de teste para uma sequência supervisória '
        'contínua. A coluna original mantém os scores já publicados da janela física-anterior/'
        'supervisória-atual. O comparador conserva suas decisões registradas na coleta.','',
        'As taxas das condições normais são falsos positivos; as taxas das condições de replay '
        'são detecções. Scores individuais, pesos, arquitetura, partições, calibração e hashes '
        'acompanham este relatório. As quantidades por condição constam da tabela.','']
    (output/'relatorio.md').write_text('\n'.join(lines),encoding='utf-8')
    with (output/'metricas.csv').open('w',newline='',encoding='utf-8-sig') as handle:
        writer=csv.DictWriter(handle,fieldnames=list(table[0]))
        writer.writeheader()
        writer.writerows(table)


def main():
    parser=argparse.ArgumentParser(description=__doc__)
    parser.add_argument('--session',type=Path,required=True)
    parser.add_argument('--output',type=Path)
    parser.add_argument('--smoke',action='store_true')
    parser.add_argument('--prospective',action='store_true')
    args=parser.parse_args()
    session=args.session.resolve()
    from run_replay_confirmation import verify_training
    from run_replay_evaluation import verify_results
    from parallel_truth_fingerprint.evidence.paired_replay import PairedReplayProtocol
    p=json.loads((session/'collection/protocol.json').read_text())
    verify_results(session/'collection',PairedReplayProtocol(**p['parameters']))
    verify_training(session)
    output=ROOT/'output/offline-contextual-replay'/datetime.now(timezone.utc).strftime('%Y%m%dT%H%M%S%fZ')
    if args.output:
        output=args.output.resolve()
    for protected in (session/'collection',session/'training'):
        if output==protected or protected in output.parents or output in protected.parents:
            raise ValueError('Contextual output must be separate from collection and baseline training.')
    output.mkdir(parents=True,exist_ok=False)
    hashes={'collection':source_hashes(session/'collection'),'training':source_hashes(session/'training')}
    save(output/'source-hashes.json',hashes)
    save(output/'protocol.json',{'version':'physical-supervisory-context-v1','source_session':str(session),
        'mode':'technical-smoke' if args.smoke else 'prospective-fixed' if args.prospective else 'retrospective-exploratory',
        'seed':101,'sequence_length':2,'feature_count':8,
        'latent_units':16,'batch_size':8,'max_epochs':1 if args.smoke else 300,'patience':25,'min_delta':1e-6,'shuffle':False,
        'fit_records':9 if args.smoke else 72,'validation_records':7 if args.smoke else 48,'calibration_records':12 if args.smoke else 60,
        'input':'[physical(t-1), supervisory_branch(t-1)], [physical(t), supervisory_branch(t)]',
        'episode_rule':'reset supervisory branch to previous live physical observation at each phase/block onset; then retain that branch history',
        'threshold':'calibration normal MSE mean + 3 population std; floor 1e-6',
        'selection':'one configuration, normal validation only; fresh collection' if args.prospective else
                    'one configuration, no attack-based selection; test scores already inspected previously',
        'controls':['frozen continuous supervisory LSTM','original hybrid LSTM','physical-supervisory comparator'],
        'normal_pairing':'same logged physical projection in physical and normal supervisory channels',
        'source_code_sha256':{str(path.relative_to(ROOT)):hashlib.sha256(path.read_bytes()).hexdigest()
            for path in [Path(__file__),ROOT/'src/parallel_truth_fingerprint/evidence/contextual_replay.py',
                         ROOT/'scripts/evaluate_replay_training_offline.py',ROOT/'src/parallel_truth_fingerprint/lstm_service/trainer.py']}})
    summary={'status':'running','started_at':datetime.now(timezone.utc).isoformat(),'profiles':{}}
    save(output/'summary.json',summary)
    print(f'Resultados: {output}',flush=True)
    try:
        import numpy as np
        import torch
        torch.set_num_threads(1)
        from parallel_truth_fingerprint.lstm_service.trainer import _load_keras_module
        keras=_load_keras_module()
        save(output/'environment.json',{'python':sys.version,'numpy':np.__version__,'torch':torch.__version__,'keras':keras.__version__})
        for profile in ('unmodulated','modulated'):
            summary['profiles'][profile]=run_profile(session,profile,output/profile,keras,torch,np,technical=args.smoke)
            save(output/'summary.json',summary)
        if hashes!={'collection':source_hashes(session/'collection'),'training':source_hashes(session/'training')}:
            raise ValueError('Source artifacts changed.')
        summary.update(status='completed',source_unchanged=True)
        write_report(output,summary)
    except BaseException as error:
        summary.update(status='failed',error=str(error))
        raise
    finally:
        summary['finished_at']=datetime.now(timezone.utc).isoformat()
        save(output/'summary.json',summary)
        save(output/'manifest.json',source_hashes(output))
    print(json.dumps(summary,indent=2),flush=True)


if __name__=='__main__':
    main()
