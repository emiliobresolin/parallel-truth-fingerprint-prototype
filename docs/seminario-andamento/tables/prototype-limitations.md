<!-- Limitacoes consolidadas a partir do relatorio tecnico (secao 8) e das verificacoes ao vivo desta sessao (2026-06-23). -->
| limitacao | impacto | evidencia | como_sera_tratado | prioridade |
| --- | --- | --- | --- | --- |
| Dataset custom e normal-only e sem rotulo de ataque | Nao suporta metrica supervisionada (F1/accuracy) do fingerprint | custom-dataset/live-custom-dataset.manifest (training_label=normal; labels={normal}) | Usar ADFA-LD para D6; coletar/rotular dados fisico-operacionais de ataque | Alta |
| Volume do dataset custom abaixo do piso de adequacao | 13 janelas/14 elegiveis vs piso 20/30; validation_level=runtime_valid_only | _npz-inspection.json (adequacy_met=false) | Acumular mais ciclos validos; cenarios de ataque rotulados | Media |
| 6-classe ADFA-LD nao atinge D6 | Distinguir familia de ataque continua dificil (melhor F1=0.561) | tables/adfa-ld-multiclass-results.md | Reportar como complementar; D6 fica no binario (gap G2) | Media |
| Modelo promovido local != campeao binario do relatorio | Inferencia online local roda GRU multiclasse 2026-05-21, nao o LSTM binario 2026-06-02 | online-inference/online-inference-summary.md; index/latest.json | Promover o campeao binario para o store usado pelo runtime | Media/Alta |
| Inferencia online re-treina na carga | Nao carrega pesos persistidos; custo de fit na carga | online-inference-summary.md (gap G3) | Persistir pesos reais (.keras) em MinIO e pular o re-fit | Media |
| Stack de consenso (testnet fresca) estagna quando ocioso | Re-execucoes podem precisar de restart para janela saudavel | logs: timeouts 'tx included in block'; restart resolve | Configurar create_empty_blocks/timeouts; documentar restart | Baixa/Media |
| replay/freeze nao executado como resultado principal | Cenario previsto sem evidencia bruta estavel nesta sessao | ausente nas evidencias desta entrega | Capturar log bruto + payload quando estabilizado | Media |
| SCADA/sensores/planta sao simulados | Nao e validacao em planta industrial real | tables/infrastructure-components.md | Trabalho futuro: piloto com instrumentacao HART/Profibus real | Alta (escopo de mestrado) |
| Test suite nao anexada nesta entrega | Estabilidade de codigo nao comprovada por testes nesta sessao | -  | Rodar unittest/pytest e anexar saida | Media |
| fingerprint-datasets.zip do relatorio ausente no working tree | Datasets temporais citados no relatorio nao reproduziveis localmente | find no repo: ausente (so ADFA-LD.zip presente) | Regerar via pipeline (feito ao vivo) ou reanexar o zip | Baixa |

> Limitacoes consolidadas a partir do relatorio tecnico (secao 8) e das verificacoes ao vivo desta sessao (2026-06-23).
