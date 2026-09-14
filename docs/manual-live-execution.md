# Guia de execução manual e inspeção de resultados

Este guia executa somente caminhos qualificados. Não use fixtures de teste,
resultados históricos ou arquivos Git LFS como se fossem dados medidos.

## 1. Pré-requisitos

No PowerShell, na raiz do repositório:

```powershell
.\scripts\setup_windows.ps1
$env:PYTHONPATH = 'src'
$env:KERAS_BACKEND = 'torch'
$env:DEMO_DISABLE_RUNTIME_AUTOENCODER = 'false'
docker compose -f compose.local.yml up -d mqtt-broker minio
.\scripts\init_cometbft_testnet.ps1
.\scripts\start_consensus_stack.ps1
```

Espere `docker ps` listar MQTT, MinIO, três validadores CometBFT e três
processos ABCI. MinIO fica em `http://127.0.0.1:9001` (credenciais locais
definidas em `.env.example`).

## 2. Bloqueio obrigatório antes de medir

```powershell
.\.venv\Scripts\python.exe scripts\qualify_live_run.py
```

O comando precisa terminar com código `0`. Código `2` significa que bytes
oficiais HAI 23.05 ou LID-DS 2021 estão ausentes/inválidos; pare nesse ponto e
não gere números de comparação. O diagnóstico detalha o arquivo ou papel de
dados faltante.

Para configurar os dados reais, sem os incluir no Git:

```powershell
$env:LID_DS_2021_PATH = (Resolve-Path 'datasets\LID-DS-2021-real').Path
# HAI deve estar em datasets\HAI-23.05-kaggle\hai-23.05 com hai-train1..4,
# hai-test1..2 e label-test1..2 reais e verificáveis.
```

Para o HAI, instale/autorize o cliente Kaggle uma única vez e execute:

```powershell
.\.venv\Scripts\kaggle.exe auth login
.\scripts\download_hai_official.ps1
```

O login abre o fluxo oficial do Kaggle no navegador e guarda o token fora do
repositório. Sem essa autenticação, o download oficial não pode ser automatizado.

## 3. Gerar evidência do pipeline físico

Depois do preflight aprovado, use um bucket e log novos:

```powershell
$env:MINIO_BUCKET = 'ptfp-live-YYYYMMDD'
$env:DEMO_LOG_PATH = 'logs\ptfp-live-YYYYMMDD.json'
$env:DEMO_MAX_CYCLES = '30'
$env:DEMO_CYCLE_INTERVAL_SECONDS = '5'
$env:DEMO_SCENARIO = 'normal'
.\.venv\Scripts\python.exe scripts\run_local_demo.py
```

Espere, em cada ciclo: três edges publicando observações, commit do CometBFT,
comparação SCADA `match`, persistência em MinIO e crescimento do dataset
normal-only. O valor de `DEMO_POWER` controla a potência do compressor; por
exemplo, defina `DEMO_POWER='80'` antes de iniciar uma execução nova.

## 4. Cenários controlados da matriz local

Rode cada cenário em bucket/log separado. Eles testam o pipeline local, não
produzem métricas de benchmark externo por si só.

```powershell
$env:DEMO_SCENARIO = 'normal'
$env:MINIO_BUCKET = 'ptfp-normal'; $env:DEMO_LOG_PATH = 'logs\normal.json'
$env:DEMO_MAX_CYCLES = '30'; .\.venv\Scripts\python.exe scripts\run_local_demo.py
$env:DEMO_SCENARIO = 'single_edge_exclusion'
$env:MINIO_BUCKET = 'ptfp-single-edge'; $env:DEMO_LOG_PATH = 'logs\single-edge.json'
$env:DEMO_MAX_CYCLES = '30'; .\.venv\Scripts\python.exe scripts\run_local_demo.py
$env:DEMO_SCENARIO = 'quorum_loss'
$env:MINIO_BUCKET = 'ptfp-quorum-loss'; $env:DEMO_LOG_PATH = 'logs\quorum-loss.json'
$env:DEMO_MAX_CYCLES = '30'; .\.venv\Scripts\python.exe scripts\run_local_demo.py
$env:DEMO_SCENARIO = 'scada_divergence'
$env:MINIO_BUCKET = 'ptfp-scada-divergence'; $env:DEMO_LOG_PATH = 'logs\scada-divergence.json'
$env:DEMO_MAX_CYCLES = '30'; .\.venv\Scripts\python.exe scripts\run_local_demo.py
$env:DEMO_SCENARIO = 'scada_replay'
$env:MINIO_BUCKET = 'ptfp-scada-replay'; $env:DEMO_LOG_PATH = 'logs\scada-replay.json'
$env:DEMO_MAX_CYCLES = '30'; .\.venv\Scripts\python.exe scripts\run_local_demo.py
```

Resultados esperados: `normal` pode persistir; `quorum_loss` bloqueia etapas
posteriores; `scada_divergence` bloqueia persistência; replay permanece uma
evidência comportamental distinta da divergência SCADA.

## 5. Dashboard e artefatos

Em outro terminal:

```powershell
$env:PYTHONPATH = 'src'
.\.venv\Scripts\python.exe scripts\run_local_dashboard.py
```

Abra `http://127.0.0.1:8088`. Verifique os blocos Edge, consenso, SCADA,
persistência e fingerprint; após a quantidade configurada de janelas elegíveis,
o dashboard deve mostrar o treinamento e a reutilização do autoencoder de
runtime. Use o controle de potência para aplicar a mudança no próximo ciclo e
confirme o novo `power_pct` no snapshot.

Verifique também:

- `logs\*.json`: ciclos, recibos de consenso, alertas e decisão de persistência;
- MinIO: `valid-consensus-artifacts/`, `fingerprint-datasets/` e
  `fingerprint-training-history/` no bucket escolhido;
- `_bmad-output\local-store\fingerprint-training-history\`: runs offline e
  ponteiro de promoção, quando houver;
- `docs\live-qualification-2026-09-13.md`: condição científica de execução.

## 6. Treino e resultados externos

Execute treino apenas após os datasets oficiais passarem pelo preflight e com
resultado por dataset, sem fundir domínios:

```powershell
.\.venv\Scripts\python.exe scripts\train_lstm_offline.py `
    --benchmark lid-ds-2021 --model lstm-classifier `
    --epochs 30 --batch-size 64 --learning-rate 0.001 `
    --sequence-length 50 --seed 42 `
    --persist-local _bmad-output\local-store
```

HAI é executado pelo adaptador nativo qualificado da seção 7. Nunca use o
dataset normal-only do compressor para reportar F1, accuracy ou resultado de
HAI/LID.

## 7. Execução completa confirmada: HAI × LID × ADFA × custom

O adaptador HAI 23.05 e o caminho de captura customizada estão implementados.
Use a raiz efetiva baixada do Kaggle (não a pasta vazia legada):

```powershell
$env:HAI_2305_PATH = (Resolve-Path 'datasets\HAI-23.05-kaggle\hai-23.05').Path
$env:LID_DS_2021_PATH = (Resolve-Path 'datasets\LID-DS-2021-real').Path
$env:ADFA_LD_PATH = (Resolve-Path 'datasets\ADFA-LD').Path
$env:HAI_MAX_WINDOWS_PER_CLASS = '50' # amostra estratificada registrada
$env:LID_DS_2021_MAX_ARCHIVES_PER_SCENARIO_PARTITION = '2' # dois ZIPs por cenário/papel; 0 lê todos
```

Rode cada fonte separadamente. Os valores abaixo são uma execução curta de
integração; aumente épocas e a cota LID para experimentos estatísticos.

```powershell
.\.venv\Scripts\python.exe scripts\train_lstm_offline.py --benchmark hai-23.05 --model lstm-classifier --epochs 1 --batch-size 8 --learning-rate 0.001 --sequence-length 5 --seed 42 --persist
.\.venv\Scripts\python.exe scripts\train_lstm_offline.py --benchmark lid-ds-2021 --model lstm-classifier --epochs 1 --batch-size 16 --learning-rate 0.001 --sequence-length 20 --seed 42 --persist
.\.venv\Scripts\python.exe scripts\train_lstm_offline.py --benchmark adfa-ld --model lstm-classifier --epochs 1 --batch-size 32 --learning-rate 0.001 --sequence-length 20 --seed 42 --persist
```

Para o dataset customizado, capture uma campanha normal e outra com exclusão
de edge. O script registra syscalls Linux reais via `strace`, artefato MinIO,
atributos de fingerprint exclusivamente em corrente 4–20 mA e score/limiar/
classificação do autoencoder no mesmo `round_id`:

```powershell
.\scripts\run_live_edge_capture.ps1 -Bucket ptfp-custom-current-syscall -Cycles 1 -IntervalSeconds 1 -Scenario normal -FaultMode none -PowerPct 65 -RunId custom-normal-YYYYMMDD
.\scripts\run_live_edge_capture.ps1 -Bucket ptfp-custom-current-syscall -Cycles 1 -IntervalSeconds 1 -FaultMode single_edge_exclusion -PowerPct 25 -RunId custom-edgefault-YYYYMMDD
$env:PYTHONPATH = 'src'
.\.venv\Scripts\python.exe scripts\build_custom_campaign_dataset.py --run-id custom-normal-YYYYMMDD --capture-dir logs\syscall-captures\custom-normal-YYYYMMDD --minio-bucket ptfp-custom-current-syscall
.\.venv\Scripts\python.exe scripts\build_custom_campaign_dataset.py --run-id custom-edgefault-YYYYMMDD --capture-dir logs\syscall-captures\custom-edgefault-YYYYMMDD --minio-bucket ptfp-custom-current-syscall
.\.venv\Scripts\python.exe scripts\evaluate_custom_campaign.py --dataset-file evidence\custom-dataset\custom-normal-YYYYMMDD\current-syscall-windows.jsonl --dataset-file evidence\custom-dataset\custom-edgefault-YYYYMMDD\current-syscall-windows.jsonl
```

Finalmente, gere a matriz. Ela escolhe o melhor `macro_f1` persistido dentro
de cada fonte e nunca interpreta as quatro métricas como uma única acurácia
comparável:

```powershell
.\.venv\Scripts\python.exe scripts\build_cross_benchmark_report.py --output evidence\reports\cross-benchmark-comparison.md
```

Confira `evidence\reports\cross-benchmark-comparison.md`, os manifestos em
`evidence\custom-dataset\<run-id>\manifest.json`, os logs em
`logs\syscall-captures\<run-id>\runtime.json` e MinIO em
`fingerprint-training-history/runs/`. O dashboard em `http://127.0.0.1:8088`
mostra o estado ao vivo do consenso, corrente/SCADA e fingerprint da campanha
em execução; a matriz offline é o arquivo Markdown persistido acima.
