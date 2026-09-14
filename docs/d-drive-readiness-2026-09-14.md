# Readiness on drive D — 2026-09-14

## Verified state

- Workspace: `D:\Projetos\parallel-truth-fingerprint-prototype\parallel-truth-fingerprint-prototype`.
- Python environment: `.venv\Scripts\python.exe` resolves within that workspace.
- Docker Desktop 29.5.2 and WSL2 `docker-desktop` are running.
- MQTT, MinIO, the three CometBFT nodes, and the three ABCI services are up.
- `scripts\qualify_live_run.py` passes with no blockers.
- HAI 23.05 is present at `datasets\HAI-23.05-kaggle\hai-23.05` with all six observation and two label files.
- LID-DS 2021 is present at `datasets\LID-DS-2021-real`. Its 15 official scenarios use ZIP recording bundles; the loader reads them in place rather than expanding 87+ GiB.

## Execution evidence

The controlled Linux/WSL2 run `d-drive-live-20260914` completed with 30/30
successful consensus rounds and 30 persisted MinIO artifacts. It created 29
eligible normal-history windows and raw syscall traces under
`logs\syscall-captures\d-drive-live-20260914` (3,214,162 bytes across four
strace files). The deprecated runtime autoencoder was explicitly disabled.

This is runtime/capture evidence only. It is not a benchmark score or a
physical/syscall fusion result.

## Remaining scientific gate

`validate_parameter_evidence.py` correctly reports the planning parameter
ledger as blocked: RPM endpoints, several profile bindings, and their decision
identities remain unresolved. Therefore no physical metric, paired custom
matrix, or fusion claim may be generated from the runtime data yet. The HAI
and LID native data tracks remain separate and must not be treated as
compressor data or combined into a common metric.
