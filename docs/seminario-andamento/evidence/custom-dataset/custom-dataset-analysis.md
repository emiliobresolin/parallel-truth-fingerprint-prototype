# Análise do dataset custom / físico-operacional

> Verificado ao vivo em 2026-06-23 regenerando o dataset pelo pipeline real a partir do
> bucket MinIO `sem-normal` (14 artefatos válidos do cenário `normal`).
> Artefatos: `live-custom-dataset.manifest.pretty.json`, `live-custom-dataset.windows.npz`, `_npz-inspection.json`.

As perguntas da tarefa, respondidas **apenas com base em artefatos reais**:

### 1. O dataset custom existe?
Sim — como *produto do pipeline*, não como arquivo fixo no repositório. Ele é gerado em
runtime a partir dos artefatos de consenso válidos. Nesta sessão foi **regenerado ao vivo**
(`persist_training_dataset_artifacts`) e salvo no MinIO sob `fingerprint-datasets/`.

### 2. Onde está?
- Live (esta sessão): MinIO bucket `sem-normal`, prefixo `fingerprint-datasets/`
  (`training-dataset::round-…::round-…::seq-2.manifest.json` + `.windows.npz`).
- Cópia legível nesta entrega: `evidence/custom-dataset/live-custom-dataset.manifest.pretty.json`
  e `live-custom-dataset.windows.npz`.
- **O `fingerprint-datasets.zip` citado no Relatório de Evidências Parciais NÃO está presente
  no working tree** (busca no repositório: apenas `datasets/ADFA-LD.zip` existe). Os números
  daquele zip (11 manifests / 11 `.windows.npz`, 9–19 janelas) vêm do relatório e não foram
  reproduzíveis a partir do repositório atual — por isso o dataset foi **regenerado** aqui.

### 3. Quantos arquivos existem?
No live: 1 manifest `.manifest.json` + 1 arquivo `.windows.npz` (um dataset). O relatório
descreve 22 arquivos (11+11) no zip ausente.

### 4. Quantas janelas temporais foram geradas?
**13 janelas** (de **14 artefatos elegíveis**), `tensor_shape = [13, 2, 27]`. Fonte:
`_npz-inspection.json` / manifest.

### 5. Quais features existem?
**27 features** = 9 por sensor × 3 sensores (temperature, pressure, rpm):
`pv`, `loop_current_ma`, `pv_percent_range`, `noise_floor`, `rate_of_change_dtdt`,
`local_stability_score`, `field_device_malfunction`, `loop_current_saturated`, `cold_start`.
(Schema idêntico ao documentado em `docs/runtime-artifacts-and-evidence-report.md` §Feature Schema.)

### 6. Existem labels?
Sim, mas **apenas um valor**: `training_label = normal`. As janelas observadas têm rótulo
único `{normal}` (verificado: `DISTINCT_WINDOW_LABELS = ['normal']`).

### 7. Existem dados normais e anômalos?
**Não.** Por construção, o builder só considera elegível o que é `final_consensus_status=success`
+ `training_label=normal` + `training_eligible=true` + `has_scada_divergence=false`. Cenários de
ataque (quorum_loss, scada_divergence, replay) são **deliberadamente excluídos** do dataset de
treino normal. Logo, não há classe de ataque.

### 8. Existe volume suficiente para treino supervisionado?
**Não.** A avaliação de adequação do próprio pipeline retorna
`adequacy_met = false`, `status_reason = below_default_adequacy_floor`,
`validation_level = runtime_valid_only` (pisos padrão: 30 artefatos elegíveis / 20 janelas;
obtido: 14 / 13).

### 9–11. Qual foi o problema ao tentar usar esse dataset? Causa? Pode ser evidência de integração?
A causa é **estrutural, não um erro de pipeline**:
1. **Ausência de rótulo de ataque** (single-class `normal`) — impossível calcular F1/accuracy
   supervisionados, que exigem ao menos duas classes.
2. **Volume abaixo do piso de adequação** — poucas janelas para treino/validação robustos.
3. **Natureza do artefato**: marcado `runtime_valid_only`, isto é, foi projetado como
   **demonstração de integração** do caminho (consenso → SCADA → persistência → janelas →
   tensor pronto para modelo), e não como dataset acadêmico de avaliação.

Portanto, **sim, ele serve como evidência de integração do pipeline** (o caminho produz, de
forma rastreável, tensores rotulados a partir de estado validado), mas **não** como base para
a métrica acadêmica do fingerprint. Por isso a métrica supervisionada foi obtida no **ADFA-LD**
(rotulado), tratado como validação preliminar do pipeline de fingerprint/anomaly detection
(ver `../adfa-ld/adfa-ld-analysis.md`).

### 12. O que falta para virar um dataset físico-operacional robusto?
- Incluir **cenários de ataque rotulados** (ex.: divergência SCADA / replay marcados como anômalos),
  para ter as classes Normal × Anômalo.
- **Acumular volume** acima do piso de adequação (≥ 30 artefatos / ≥ 20 janelas; idealmente muito mais).
- **Diversidade operacional** (variação de regime do processo, ruído, transientes) e, idealmente,
  **dados de instrumentação real** (HART/Profibus), hoje simulados.
- Definir um **protocolo de rotulagem** alinhado ao modelo de ameaça (injeção, replay, drift gradual).

> **Conclusão honesta:** o dataset custom comprova a integração ponta-a-ponta do pipeline de
> fingerprint (real, regenerado nesta sessão), mas é normal-only, pequeno e `runtime_valid_only`;
> não substitui o dataset físico-operacional rotulado que ainda precisa ser construído.
