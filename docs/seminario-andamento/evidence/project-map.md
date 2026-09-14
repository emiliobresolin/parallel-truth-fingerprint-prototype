# Mapa do Projeto — Protótipo (Seminário de Andamento)

> Gerado em 2026-06-23 a partir da inspeção do repositório e de execuções ao vivo da stack.
> Projeto: *Arquitetura baseada em Fonte de Verdade Paralela para Geração de Fingerprint Físico-Operacional em Sistemas Industriais Legados*.

## 1. Raiz do projeto

O repositório versionado está em `parallel-truth-fingerprint-prototype/` (pasta aninhada).
Todos os caminhos abaixo são relativos a essa raiz.

```
src/parallel_truth_fingerprint/   # código-fonte (pacote Python)
scripts/                          # orquestração e CLIs
abci/consensus_app/               # aplicação ABCI em Go (lógica de confiança/exclusão)
compose.local.yml                 # MQTT + MinIO
compose.consensus.yml             # 3 validadores CometBFT + 3 ABCI
datasets/ADFA-LD/                 # dataset público (git-ignored)
_bmad-output/                     # artefatos de implementação, store local, evidências
docs/                             # relatórios técnicos + esta pasta (seminario-andamento)
logs/                             # logs de execução (JSON detalhado + terminal)
tests/                            # suíte de testes
```

## 2. Scripts principais (`scripts/`)

| Script | Função |
| --- | --- |
| `run_local_demo.py` | **Caminho oficial do runtime.** Executa o ciclo completo (edges → MQTT → CometBFT/ABCI → SCADA → MinIO → fingerprint). Cenários via `DEMO_SCENARIO`. |
| `run_local_dashboard.py` | Dashboard local do operador (porta 8088). |
| `init_cometbft_testnet.ps1` | Inicializa a rede de 3 validadores (uma vez). |
| `start_consensus_stack.ps1` / `stop_consensus_stack.ps1` | Sobe/desce a stack de consenso (`compose.consensus.yml`). |
| `train_lstm_offline.py` / `train_lstm_sweep.py` | Treino supervisionado offline (ADFA-LD/LID-DS) e sweep de hiperparâmetros. |
| `promote_lstm_run.py` | Promove um run treinado como modelo do runtime (escreve `index/latest.json`). |
| `build_cross_benchmark_report.py` | Relatório comparativo entre benchmarks. |
| `sweeps/*.json` | Configurações de sweep (binário/multiclasse ADFA-LD; LID-DS). |

## 3. Como subir o projeto

```powershell
# 1) deps
.\scripts\setup_windows.ps1
# 2) MQTT + MinIO
docker compose -f compose.local.yml up -d mqtt-broker minio
# 3) consenso (init uma vez, depois start)
.\scripts\init_cometbft_testnet.ps1
.\scripts\start_consensus_stack.ps1     # ou: docker compose -f compose.consensus.yml up -d --build
```
Verificação rápida da camada de consenso: `curl http://127.0.0.1:26657/status` (node_version 0.39.0).

> **Observação de liveness (verificada nesta sessão):** a testnet fresca produz blocos por
> uma janela e pode estagnar quando ociosa, fazendo `broadcast_tx_commit` expirar
> ("timed out waiting for tx to be included in a block"). Um `docker compose -f
> compose.consensus.yml restart` restabelece a produção de blocos; rode os cenários logo
> em seguida. As 3 execuções obrigatórias desta entrega foram feitas nessa janela saudável.

## 4. Como executar a demo / cenários

```powershell
$env:PYTHONPATH='src'; $env:KERAS_BACKEND='torch'
# normal (caminho feliz)
.\.venv\Scripts\python.exe scripts\run_local_demo.py
# cenários (caminho oficial, sem bypass)
$env:DEMO_SCENARIO='quorum_loss';      .\.venv\Scripts\python.exe scripts\run_local_demo.py
$env:DEMO_SCENARIO='scada_divergence'; .\.venv\Scripts\python.exe scripts\run_local_demo.py
```
Variáveis úteis: `DEMO_MAX_CYCLES` (0 = infinito), `DEMO_CYCLE_INTERVAL_SECONDS`,
`MINIO_BUCKET` (bucket alvo), `DEMO_LOG_PATH` (log JSON), `DEMO_DISABLE_RUNTIME_AUTOENCODER=true`
(desliga o autoencoder de runtime, depreciado — Story 8.3). Config lida 100% de variáveis de
ambiente em `src/parallel_truth_fingerprint/config/runtime.py` (o `.env` **não** é auto-carregado).

> Comandos exatos usados nesta entrega: ver `evidence/scenarios/<cenario>/command.txt`.

## 5. Onde ficam os artefatos

| Tipo | Local |
| --- | --- |
| **Datasets (público)** | `datasets/ADFA-LD/` (+ `ADFA-LD.zip`). `ADFA_LD_PATH` aponta para cá. |
| **Dataset custom (fingerprint)** | gerado em runtime no MinIO sob `fingerprint-datasets/` (manifest `.manifest.json` + `.windows.npz`). Regenerado ao vivo em `evidence/custom-dataset/`. |
| **Resultados de treino (offline)** | `_bmad-output/local-store/fingerprint-training-history/.../runs/*.json` (+ `.confusion.json`) e sweeps em `_bmad-output/implementation-artifacts/embedding-adfa-ld-*-sweep.md`. |
| **Modelo promovido (ponteiro)** | `_bmad-output/local-store/.../index/latest.json` (store local) ou MinIO `fingerprint-training-history/index/latest.json`. |
| **Artefatos de consenso válidos** | MinIO bucket `valid-consensus-artifacts` (ou bucket por cenário, ex. `sem-normal`). |
| **Logs** | `logs/` — JSON detalhado por run (`*.log`) + captura de terminal (`*.terminal.txt`). |
| **Relatórios técnicos** | `docs/results-of-the-prototype.md`, `docs/runtime-artifacts-and-evidence-report.md`. |

## 6. Onde ficam logs / MinIO

- **Logs desta entrega (ao vivo 2026-06-23):** `logs/sem-normal.log`, `logs/sem-quorum-loss.log`,
  `logs/sem-scada-divergence.log` (+ `*.terminal.txt`); inferência online em `logs/sem-online-inference.terminal.txt`.
- **MinIO:** container `ptfp-minio`, endpoint `localhost:9000`, console `localhost:9001`,
  credenciais `minioadmin/minioadmin`. Listagem ao vivo: `evidence/minio/minio-listing.txt`.

## 7. Comandos "oficiais" para execução (resumo)

1. `docker compose -f compose.local.yml up -d mqtt-broker minio`
2. `docker compose -f compose.consensus.yml up -d --build` (após `init_cometbft_testnet.ps1`)
3. `python scripts/run_local_demo.py` (com `DEMO_SCENARIO` para cada cenário)
4. `python scripts/train_lstm_sweep.py --config scripts/sweeps/adfa_ld_embedding_binary_sweep.json --persist`
5. `python scripts/promote_lstm_run.py --run-id <champion> --persist-local _bmad-output/local-store`
6. Inferência online: `OnlineLstmInferencer.load(artifact_store=...)` (ver `evidence/online-inference/online-inference-command.txt`)
