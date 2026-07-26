# Cenario `scada_divergence` - resumo da execucao (LIVE 2026-06-23)

**Objetivo:** Validar a comparacao fisico-logica: com SCADA divergente do estado consensado, o downstream e bloqueado.

## Execucao
- Inicio (UTC): 2026-06-23T19:20:23Z  |  Fim (UTC): 2026-06-23T19:20:30Z
- Ciclos executados: 2 (DEMO_MAX_CYCLES=2)
- Caminho oficial do runtime (`scripts/run_local_demo.py`), sem bypass; cenario via `DEMO_SCENARIO`.
- Bucket MinIO alvo: `sem-scada-divergence`

## Consenso (CometBFT real)
- round_id (ultimo ciclo): `round-20260623192028230653`
- node_version: 0.39.0  |  committed_height: 69  |  tx_hash: `2EA949FD561E71388CBA8A8BA8CF6D2FBF7CAE8D8185B019ABDD1CC0ADBCC345`
- participantes: 3  |  quorum requerido: 2  |  validos apos exclusoes: 3
- status final do consenso: **success**
- exclusoes: nenhuma

## Comparacao SCADA
- status: **blocked_downstream**
- motivo: `scada_divergence_detected`
- sensores divergentes: temperature, pressure, rpm
- downstream permitido: False

## Persistencia (MinIO)
- status: **blocked**  |  bucket: `sem-scada-divergence`  |  endpoint: localhost:9000
- motivo do bloqueio: `scada_divergence_detected` (stage `scada_comparison`)

## Fingerprint (estagio downstream)
- model_status: `no_model_yet`  |  inference_status: `blocked:scada_divergence_detected`
- valid_artifacts: 0  |  windows: 0

## Arquivos gerados nesta pasta
- `command.txt`, `terminal-output.txt`
- `consensus-payload.pretty.json`, `consensus-payload.txt`
- `scada-comparison.pretty.json` / `scada-comparison.txt` (ou `missing-artifact.txt`)
- `minio-artifact.pretty.json` / `minio-artifact.txt` (ou `missing-artifact.txt`)

> Proveniencia: execucao ao vivo do runtime em 2026-06-23 contra a stack real (3 validadores CometBFT v0.39.0 + 3 ABCI Go + MQTT + MinIO em containers locais). Log JSON completo: `logs/sem-scada-divergence.log`.
