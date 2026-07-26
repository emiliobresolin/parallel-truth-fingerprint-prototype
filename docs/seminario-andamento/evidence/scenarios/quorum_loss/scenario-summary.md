# Cenario `quorum_loss` - resumo da execucao (LIVE 2026-06-23)

**Objetivo:** Validar que sem quorum confiavel o downstream e bloqueado (comparacao SCADA, persistencia e fingerprint).

## Execucao
- Inicio (UTC): 2026-06-23T19:20:05Z  |  Fim (UTC): 2026-06-23T19:20:11Z
- Ciclos executados: 2 (DEMO_MAX_CYCLES=2)
- Caminho oficial do runtime (`scripts/run_local_demo.py`), sem bypass; cenario via `DEMO_SCENARIO`.
- Bucket MinIO alvo: `sem-quorum-loss`

## Consenso (CometBFT real)
- round_id (ultimo ciclo): `round-20260623192009763877`
- node_version: 0.39.0  |  committed_height: 55  |  tx_hash: `34E79CC7CDB29EFEDD0793E6F3413F4806A32CCC88230DC28F7D20A6E03E4446`
- participantes: 3  |  quorum requerido: 2  |  validos apos exclusoes: 0
- status final do consenso: **failed_consensus**
- exclusoes: edge-1:suspected_byzantine_behavior, edge-2:suspected_byzantine_behavior, edge-3:suspected_byzantine_behavior

## Comparacao SCADA
- status: **blocked**
- motivo: `no_quorum_reached`
- downstream permitido: False

## Persistencia (MinIO)
- status: **blocked**  |  bucket: `sem-quorum-loss`  |  endpoint: localhost:9000
- motivo do bloqueio: `no_quorum_reached` (stage `consensus`)

## Fingerprint (estagio downstream)
- model_status: `no_model_yet`  |  inference_status: `blocked:no_quorum_reached`
- valid_artifacts: 0  |  windows: 0

## Arquivos gerados nesta pasta
- `command.txt`, `terminal-output.txt`
- `consensus-payload.pretty.json`, `consensus-payload.txt`
- `scada-comparison.pretty.json` / `scada-comparison.txt` (ou `missing-artifact.txt`)
- `minio-artifact.pretty.json` / `minio-artifact.txt` (ou `missing-artifact.txt`)

> Proveniencia: execucao ao vivo do runtime em 2026-06-23 contra a stack real (3 validadores CometBFT v0.39.0 + 3 ABCI Go + MQTT + MinIO em containers locais). Log JSON completo: `logs/sem-quorum-loss.log`.
