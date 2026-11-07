"""Collect once, then fit and verify five HART/current-only seed pairs."""
from datetime import datetime,timezone
import argparse
import json
from pathlib import Path
import subprocess
import sys

ROOT=Path(__file__).resolve().parents[1]
sys.path[:0]=[str(ROOT/'src'),str(ROOT/'scripts')]
from evaluate_replay_training_offline import save
from evaluate_hart_multiseed import SEEDS,verify_multi
from parallel_truth_fingerprint.evidence.paired_replay import PairedReplayProtocol

def run(*,technical=False,resume=None):
    if resume:
        root=Path(resume).resolve()
        if not root.is_relative_to((ROOT/'output/replay-p23-multiseed').resolve()):
            raise ValueError('Resume must select a P23 session in this workspace.')
        protocol=json.loads((root/'protocol.json').read_text(encoding='utf-8'))
        if protocol['version']!='p23-generic-hart-five-seeds-v1' or protocol['technical_smoke']!=technical:
            raise ValueError('Resume recipe/mode mismatch.')
    else:
        root=ROOT/'output/replay-p23-multiseed'/datetime.now(timezone.utc).strftime('%Y%m%dT%H%M%S%fZ')
        root.mkdir(parents=True,exist_ok=False)
        from parallel_truth_fingerprint.sensor_simulation.generic_plant import generic_plant_configuration,generic_totalizer_configuration
        collection_protocol=PairedReplayProtocol(train_rounds=16,calibration_rounds=12,block_rounds=4,settle_rounds=3,
            repetitions=1,epochs=1,interval_seconds=5,edge_count=4,simulation_seed=808) if technical else PairedReplayProtocol(edge_count=4,simulation_seed=808)
        protocol={'version':'p23-generic-hart-five-seeds-v1','technical_smoke':technical,
            'training_seeds':list(SEEDS),'expected_model_fits':20,'simulation_seed':808,
            'collection_parameters':vars(collection_protocol),'expected_acquisitions':len(collection_protocol.schedule()),
            'generic_plant_configuration':generic_plant_configuration(),'hart_totalizer_configuration':generic_totalizer_configuration(),
            'max_epochs':1 if technical else 300,'patience':25,'min_delta':1e-6,'batch_size':8,'latent_units':16,
            'selection':'Normal validation and separate normal calibration, target FPR 1%; preserve every seed.',
            'approval':'Emilio approved preparing and manually running five training seeds on one collection and documented timing (P23).',
            'scope':'Two process profiles; four paired conditions; HART 2x10 and matched currents 2x8. Seeds replicate training, not acquisition.',
            'collector_diagnostic':'Intermediate collector model is diagnostic; primary HART/current models are fit after collection.'}
        save(root/'protocol.json',protocol)
    print('Resultados P23: '+str(root),flush=True)
    log_path=root/'console.log'
    state={'status':'preparing','started_at':datetime.now(timezone.utc).isoformat(),'root':str(root)}
    def execute(command):
        with log_path.open('a',encoding='utf-8',buffering=1) as log:
            with subprocess.Popen(command,cwd=ROOT,stdout=subprocess.PIPE,stderr=subprocess.STDOUT,
                text=True,encoding='utf-8',errors='replace',bufsize=1) as child:
                for line in child.stdout:
                    print(line.rstrip('\n'),flush=True);log.write(line)
                code=child.wait()
        if code:raise RuntimeError(f'Subprocess failed ({code}); preserve console.log and session artifacts.')
    try:
        source=root/'collection'
        if not source.exists():
            state['status']='collecting';save(root/'summary.json',state)
            command=[sys.executable,'-B','-u',str(ROOT/'scripts/run_replay_evaluation.py'),
                '--paired-profiles','--four-edges','--hart-totalizer','--generic-plant','--simulation-seed','808',
                '--output-directory',str(source),'--timeout-hours','4']
            if technical:command+=['--smoke']
            execute(command)
        from run_replay_evaluation import verify_results
        frozen=json.loads((source/'protocol.json').read_text(encoding='utf-8'))
        if frozen['parameters']!=protocol['collection_parameters'] or frozen['generic_plant_configuration']!=protocol['generic_plant_configuration']:
            raise ValueError('Collection differs from frozen parent recipe.')
        verify_results(source,PairedReplayProtocol(**frozen['parameters']))
        for profile in ('unmodulated','modulated'):
            rows=[json.loads(line) for line in (source/profile/'observations.jsonl').read_text(encoding='utf-8').splitlines()]
            if any('acquisition_timing' not in row for row in rows):raise ValueError('P23 acquisition timing is missing.')
        state['status']='training_five_seeds';save(root/'summary.json',state)
        command=[sys.executable,'-B','-u',str(ROOT/'scripts/evaluate_hart_multiseed.py'),
            '--source',str(source),'--output',str(root/'hart-multiseed')]
        if technical:command+=['--smoke']
        execute(command)
        evaluated=verify_multi(root/'hart-multiseed')
        state.update(status='completed',verified=True,model_fits=evaluated['model_fits'],
            aggregate=evaluated['aggregate'],source_collection=str(source),evaluation=str(root/'hart-multiseed'))
    except KeyboardInterrupt:
        state.update(status='interrupted',verified=False)
        print('Interrompido; artefatos preservados.',flush=True)
    except Exception as error:
        state.update(status='failed',verified=False,error=str(error))
        print('Falha: '+str(error),flush=True)
    finally:
        state['finished_at']=datetime.now(timezone.utc).isoformat();save(root/'summary.json',state)
    print('Final: '+state['status']+'. Resumo: '+str(root/'summary.json'),flush=True)
    return 0 if state['status']=='completed' else 1

if __name__=='__main__':
    parser=argparse.ArgumentParser(description=__doc__)
    parser.add_argument('--smoke',action='store_true');parser.add_argument('--resume',type=Path)
    args=parser.parse_args();raise SystemExit(run(technical=args.smoke,resume=args.resume))
