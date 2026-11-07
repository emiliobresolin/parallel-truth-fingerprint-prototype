"""Manual complete public pilot with 48-epoch cap, progress and persistent logs."""
from datetime import datetime
import json
from pathlib import Path
import subprocess
import sys
import threading

ROOT=Path(__file__).resolve().parents[1]
CONFIG=ROOT/'configs/experiments/p21-public-48epochs-v1.json'
RECORDS=ROOT/'output/dissertacao/professor_inputs/p21_treino_ampliado/v1'

def main():
    prep=json.loads((RECORDS/'preparacao_completa.json').read_text(encoding='utf-8'))
    cell_dir=ROOT/prep['resultado']/'pilot/cells'
    log_path=RECORDS/('execucao-'+datetime.now().strftime('%Y%m%d-%H%M%S')+'.log')
    done=threading.Event(); mutex=threading.Lock()
    with log_path.open('a',encoding='utf-8',buffering=1) as log:
        def emit(line):
            with mutex:
                print(line,flush=True); log.write(line+'\n')
        def monitor():
            previous=None
            while not done.is_set():
                items=[]
                for path in cell_dir.glob('*.json'):
                    try:
                        row=json.loads(path.read_text(encoding='utf-8'))
                        if row.get('status')=='complete' and row.get('config_identity')==prep['config_identity']:
                            items.append((row['dataset'],row['model'],row['seed'],row['model_fit']['epochs_executed']))
                    except (OSError,json.JSONDecodeError):
                        continue
                current=tuple(sorted(items))
                if current!=previous:
                    emit(f'Progresso por ajustes completos: {len(items)}/23. O tempo por ajuste varia.')
                    for item in sorted(set(current)-set(previous or ())):
                        emit(f'  Concluido: {item[0]} / {item[1]} / seed {item[2]} / epocas executadas {item[3]}')
                    previous=current
                done.wait(5)
        emit('Log: '+str(log_path))
        emit('Resultados: '+str(cell_dir.parent))
        emit('Tres bases; 15 ajustes LSTM, teto 48 com parada antecipada, e oito controles determinísticos.')
        emit('Preparacao, autenticacao e ajuste podem ocorrer sem incremento imediato da contagem.')
        thread=threading.Thread(target=monitor,daemon=True); thread.start()
        command=[sys.executable,'-B','-u',str(ROOT/'scripts/run_academic_experiments.py'),
            'run','--phase','pilot','--config',str(CONFIG)]
        try:
            with subprocess.Popen(command,cwd=ROOT,stdout=subprocess.PIPE,stderr=subprocess.STDOUT,
                text=True,encoding='utf-8',errors='replace',bufsize=1) as child:
                for line in child.stdout: emit(line.rstrip('\n'))
                code=child.wait()
        finally:
            done.set(); thread.join(timeout=6)
        if code:
            emit(f'Execucao terminou com codigo {code}. Preserve o log. O mesmo comando retoma celulas completas validas.')
            return code
        result=subprocess.run([sys.executable,'-B','-u',str(ROOT/'scripts/prepare_p21_extended_training.py'),'summary'],
            cwd=ROOT,stdout=subprocess.PIPE,stderr=subprocess.STDOUT,text=True,encoding='utf-8',errors='replace')
        emit(result.stdout.rstrip())
        return result.returncode

if __name__=='__main__':
    raise SystemExit(main())
