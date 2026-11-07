"""Read-only source audit of the new digital-current comparator on saved views.

This is a posthoc calculation, not a re-execution of the current-domain runtime.
"""
from datetime import datetime, timezone
from pathlib import Path
import csv
import hashlib
import json

ROOT = Path(__file__).resolve().parents[1]
SOURCE = ROOT/'output/replay-common-calibration/20261028T174856943376Z/collection'


def main():
    output = ROOT/'output/current-domain-impact'/datetime.now(timezone.utc).strftime('%Y%m%dT%H%M%S%fZ')
    evidence, sources = [], {}
    for profile in ('unmodulated', 'modulated'):
        path = SOURCE/profile/'observations.jsonl'
        sources[str(path.relative_to(ROOT))] = hashlib.sha256(path.read_bytes()).hexdigest()
        rows = [json.loads(line) for line in path.read_text(encoding='utf-8').splitlines()]
        for condition in ('normal_stable','legitimate_transition','replay_same_regime','replay_hiding_change'):
            pairs = [(r, v) for r in rows for v in r['views'] if v['condition'] == condition]
            old_alerts = sum(bool(v['comparison']['divergent_sensors']) for _,v in pairs)
            alerts = 0
            for r, v in pairs:
                current = {name: s['loop_current_ma'] for name,s in r['physical_scada']['behavioral_sensor_values'].items()}
                supervisory = {name: s['loop_current_ma'] for name,s in v['scada_state']['behavioral_sensor_values'].items()}
                if set(current) != set(supervisory):
                    raise ValueError('Current channel schemas differ.')
                alerts += any(current[s] != supervisory[s] for s in current)
            evidence.append(dict(perfil=profile, condicao=condition, avaliacoes=len(pairs),
                                 alertas_comparador_engenharia_original=old_alerts,
                                 alertas_corrente_recalculados=alerts))
    output.mkdir(parents=True, exist_ok=False)
    with (output/'comparacao.csv').open('w',encoding='utf-8-sig',newline='') as handle:
        writer = csv.DictWriter(handle, fieldnames=list(evidence[0]))
        writer.writeheader()
        writer.writerows(evidence)
    (output/'fontes.json').write_text(json.dumps(sources,indent=2),encoding='utf-8')
    for name, expected in sources.items():
        if hashlib.sha256((ROOT/name).read_bytes()).hexdigest() != expected:
            raise ValueError('Saved source changed during audit.')
    note = ['# Impacto da migração — diagnóstico dos dados existentes', '',
            'Cálculo posterior sobre as visões da semente 404; preserva o comparador original e as correntes adquiridas. A tabela compara decisões originais em engenharia com igualdade de corrente por canal.', '',
            '| Perfil | Condição | Avaliações | Alertas originais | Alertas recalculados em corrente |',
            '|---|---|---:|---:|---:|']
    note += [f"| {r['perfil']} | {r['condicao']} | {r['avaliacoes']} | {r['alertas_comparador_engenharia_original']} | {r['alertas_corrente_recalculados']} |" for r in evidence]
    note += ['', 'A nova implementação requer nova execução integrada para qualificar consenso, persistência, syscalls e treinamento sob o contrato atual. Este diagnóstico verifica somente o efeito da mudança do comparador sobre os valores já registrados; as saídas históricas conservam sua proveniência original. As bases públicas mantêm suas tarefas e métodos originais e não dependem desse caminho de aquisição.']
    (output/'relatorio.md').write_text('\n'.join(note)+'\n',encoding='utf-8')
    (output/'manifest.json').write_text(json.dumps({p.name:hashlib.sha256(p.read_bytes()).hexdigest() for p in output.iterdir() if p.is_file()},indent=2),encoding='utf-8')
    print(output)
    print(json.dumps(evidence,indent=2))


if __name__ == '__main__':
    main()
