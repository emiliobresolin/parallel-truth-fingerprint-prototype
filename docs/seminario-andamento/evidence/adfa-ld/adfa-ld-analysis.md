# Análise do ADFA-LD no contexto do projeto

> Fontes: `datasets/ADFA-LD/` (presente), `_bmad-output/implementation-artifacts/embedding-adfa-ld-binary-sweep.md`
> e `…multiclass-sweep.md` (sweeps reais persistidos), `docs/results-of-the-prototype.md` §5–6.
> Tabelas derivadas: `tables/adfa-ld-*.md/.csv`, `tables/champion-*.md/.csv`, `tables/confusion-matrix.*`.

### 1. O que é o ADFA-LD no contexto do projeto
ADFA-LD (UNSW Canberra, 2013) é um **dataset público de detecção de intrusão baseado em
sequências de syscalls** de host Linux. No projeto ele é usado como **benchmark público para
validação preliminar do pipeline de fingerprint/anomaly detection** — i.e., para obter métricas
supervisionadas (F1/accuracy) que o dataset custom (normal-only) não permite.

> **Ressalva de domínio (importante):** ADFA-LD é syscalls de host, **não** telemetria
> físico-operacional industrial. Ele **não representa diretamente** o domínio físico-operacional
> alvo da dissertação; serve como prova de que o pipeline supervisionado de fingerprint funciona
> e atinge o critério de qualidade definido, enquanto o dataset físico-operacional rotulado é
> construído (ver `../custom-dataset/custom-dataset-analysis.md`).

### 2. Onde o dataset está
`datasets/ADFA-LD/` (descompactado) + `datasets/ADFA-LD.zip`. O adaptador encontra-o via
`ADFA_LD_PATH=datasets/ADFA-LD`. Subpastas: `Training_Data_Master`, `Validation_Data_Master`,
`Attack_Data_Master`.

### 3. Por que foi usado
Porque é **rotulado** (normal + 5 famílias de ataque), permitindo as métricas supervisionadas
(F1, accuracy, precision, recall, matriz de confusão) exigidas pelo critério **D6** — algo
inviável no dataset custom normal-only.

### 4. Quais labels fornece
- **Binário:** `Normal` × `Attack` (as 5 famílias colapsadas em uma classe). É o enquadramento
  que corresponde à pergunta operacional do protótipo ("é normal ou anômalo?").
- **6-classe:** `Normal` + `Adduser`, `Hydra-FTP`, `Hydra-SSH`, `Java-Meterpreter`, `Web-Shell`.
- Volume: **5.951 traces** (5.205 normais / 746 de ataque), maior syscall id = 340.

### 5. Por que permite métricas supervisionadas
Há ≥ 2 classes rotuladas e volume suficiente → split estratificado 80/20 (seed 42) e cálculo de
F1/accuracy/precision/recall + matriz de confusão.

### 6. Quais modelos foram testados
`lstm-embedding-classifier` e `gru-embedding-classifier` (Embedding de syscalls → LSTM/GRU →
dropout → softmax), em sweep `sequence_length ∈ {50,80,120}` × {LSTM,GRU}, 18 épocas, seed 42,
`embed_dim=64`, `hidden_units=64`, batch 256, lr 0.001 (6 runs por enquadramento).

### 7. Quais métricas foram geradas
Tabela completa em `tables/adfa-ld-binary-results.md` (binário) e
`tables/adfa-ld-multiclass-results.md` (6-classe).
- **Binário:** 4 dos 6 runs passam **ambos** os limiares D6 (macro F1 ≥ 0.85 **e** accuracy ≥ 0.90).
- **6-classe:** nenhum run passa D6 (melhor macro F1 = 0.561, LSTM seq=80) — reportado como
  análise complementar honesta, não como base do D6.

### 8. Qual foi o melhor run (campeão)
`run-adfa-ld-embed-binary-lstm-embedding-classifier-20260602T175338-3acfb039`
(LSTM-embedding, seq=80, 18 épocas, 65.922 parâmetros): **macro F1 = 0.9187**, **accuracy = 0.9229**.
Por classe: Normal F1=0.9372 / Attack F1=0.9002; **recall de ataque = 0.958**, FPR normal = 4.2%.
Matriz de confusão (1.634 janelas de teste): `tables/confusion-matrix.md` / `assets/confusion-matrix.md`.

### 9. Por que esse resultado é útil para o Seminário de Andamento
- Demonstra que o **pipeline supervisionado de fingerprint** atinge qualidade alta e **estável**
  (não depende de um único run: 4/6 passam D6, em duas arquiteturas e dois comprimentos de sequência).
- Fecha o laço de **reintegração** (offline treinado → promovido → inferência online), comprovado
  ao vivo nesta sessão (`../online-inference/online-inference-summary.md`).
- Fornece números quantitativos defensáveis para a seção de resultados preliminares do Seminário.

### 10. Limitações de domínio
- ADFA-LD **não** é dado físico-operacional industrial — é syscalls de host. A transferência para
  o domínio físico ainda precisa ser demonstrada com o dataset custom rotulado.
- 6-classe permanece difícil (propriedade conhecida do ADFA-LD com 1 feature de syscall + modelo
  pequeno), tratado como trabalho futuro (gap G2).
- A inferência online local desta sessão usou o **run multiclasse GRU de 2026-05-21** promovido no
  store local — **não** o campeão binário de 2026-06-02 (esse foi promovido contra o MinIO e seu
  ponteiro não está no store local). Ver `../online-inference/online-inference-summary.md`.
