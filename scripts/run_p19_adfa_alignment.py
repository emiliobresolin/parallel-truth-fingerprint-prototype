"""Manual ADFA-only invocation with console progress and a persistent log."""
import json
from pathlib import Path
import subprocess
import sys
import threading
from datetime import datetime

ROOT = Path(__file__).resolve().parents[1]
CONFIG = ROOT/'configs/experiments/p19-adfa-aligned-v3.json'
RECORDS = ROOT/'output/dissertacao/professor_inputs/p19_alinhamento/v3'

def main():
    preparation=json.loads((RECORDS/'preparacao.json').read_text(encoding='utf-8'))
    cell_dir=ROOT/preparation['resultado']/'pilot/cells'
    log_path=RECORDS/('execucao-'+datetime.now().strftime('%Y%m%d-%H%M%S')+'.log')
    mutex=threading.Lock()
    done=threading.Event()
    with log_path.open('a',encoding='utf-8',buffering=1) as log:
        def emit(line):
            with mutex:
                print(line,flush=True); log.write(line+'\n')
        def monitor():
            previous=None
            while not done.is_set():
                names=[]
                for path in cell_dir.glob('adfa-ld__*.json'):
                    try:
                        row=json.loads(path.read_text(encoding='utf-8'))
                        if row.get('status')=='complete': names.append((row['model'],row['seed']))
                    except (OSError,json.JSONDecodeError):
                        continue
                current=tuple(sorted(names))
                if current!=previous:
                    emit(f'Progresso: {len(current)}/8 ajustes completos. '+', '.join(f'{model} seed {seed}' for model,seed in current))
                    previous=current
                done.wait(5)
        emit('Log: '+str(log_path))
        emit('Resultados: '+str(cell_dir.parent))
        watcher=threading.Thread(target=monitor,daemon=True)
        watcher.start()
        command=[sys.executable,'-B','-u',str(ROOT/'scripts/run_academic_experiments.py'),
            'run','--phase','pilot','--config',str(CONFIG),'--dataset','adfa-ld']
        try:
            with subprocess.Popen(command,cwd=ROOT,stdout=subprocess.PIPE,stderr=subprocess.STDOUT,text=True,encoding='utf-8',errors='replace',bufsize=1) as child:
                for line in child.stdout:
                    emit(line.rstrip('\n'))
                code=child.wait()
        finally:
            done.set(); watcher.join(timeout=6)
        if code:
            emit(f'Execucao interrompida ou falhou (codigo {code}). O mesmo comando retoma as celulas completas.')
            return code
        result=subprocess.run([sys.executable,'-B','-u',str(ROOT/'scripts/prepare_p19_adfa_alignment.py'),'summary'],cwd=ROOT,stdout=subprocess.PIPE,stderr=subprocess.STDOUT,text=True,encoding='utf-8',errors='replace')
        emit(result.stdout.rstrip())
        return result.returncode

if __name__=='__main__':
    raise SystemExit(main())
