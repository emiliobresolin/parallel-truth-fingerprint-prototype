# Cenario `normal` - resumo da execucao (LIVE 2026-06-23)

**Objetivo:** Validar o caminho feliz do pipeline: consenso bem-sucedido, comparacao SCADA sem divergencia, persistencia.

## Execucao
- Inicio (UTC): 2026-06-23T19:19:38Z  |  Fim (UTC): 2026-06-23T19:19:50Z
- Ciclos executados: 2 (DEMO_MAX_CYCLES=2)
- Caminho oficial do runtime (`scripts/run_local_demo.py`), sem bypass; cenario via `DEMO_SCENARIO`.
- Bucket MinIO alvo: `sem-normal`

## Consenso (CometBFT real)
- round_id (ultimo ciclo): `round-20260623191948013076`
- node_version: 0.39.0  |  committed_height: 39  |  tx_hash: `C45D71C56E85A0924784B29ACFBF8B8299E2651337314B2BF24AF7C901939ADB`
- participantes: 3  |  quorum requerido: 2  |  validos apos exclusoes: 3
- status final do consenso: **success**
- exclusoes: nenhuma

## Comparacao SCADA
- status: **completed**
- downstream permitido: True

## Persistencia (MinIO)
- status: **persisted**  |  bucket: `sem-normal`  |  endpoint: localhost:9000
- artifact_key: `valid-consensus-artifacts/round-20260623191948013076.json`
- artifact_uri: `minio://sem-normal/valid-consensus-artifacts/round-20260623191948013076.json`  |  write_confirmed: True

## Fingerprint (estagio downstream)
- model_status: `runtime_autoencoder_disabled`  |  inference_status: `skipped_runtime_autoencoder_disabled`
- valid_artifacts: 2  |  windows: 1

## Arquivos gerados nesta pasta
- `command.txt`, `terminal-output.txt`
- `consensus-payload.pretty.json`, `consensus-payload.txt`
- `scada-comparison.pretty.json` / `scada-comparison.txt` (ou `missing-artifact.txt`)
- `minio-artifact.pretty.json` / `minio-artifact.txt` (ou `missing-artifact.txt`)

> Proveniencia: execucao ao vivo do runtime em 2026-06-23 contra a stack real (3 validadores CometBFT v0.39.0 + 3 ABCI Go + MQTT + MinIO em containers locais). Log JSON completo: `logs/sem-normal.log`.
