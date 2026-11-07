# Parallel Truth Fingerprint

Industrial acquisition and supervisory-consistency testbed. Python runtime,
Go ABCI, CometBFT, MQTT, OPC UA, MinIO, Keras/PyTorch.

- Four instrument channels: temperature, pressure, rotational speed and mass flow.
- Current-domain comparison and HART totalizer support.
- Generic-plant evaluation: four logical edges, four equal-power validators,
  paired replay conditions and Linux syscall capture.
- Offline LSTM reconstruction: instrumental inputs `2×10`; paired current-only
  control `2×8`. Public benchmark adapters and deterministic baselines.

## Environment

Python 3.14+, Docker Desktop with Linux containers, PowerShell. The ABCI image
builds Go dependencies in Docker.

```powershell
powershell -NoProfile -ExecutionPolicy Bypass -File .\scripts\setup_windows.ps1
```

Benchmark data under `datasets/` and archived reference binaries under
`docs/reference-archive/documents/` are supplied separately. Runtime reference
catalogs and broker configuration remain versioned.

## Local runtime

```powershell
docker compose -f compose.local.yml up -d
powershell -NoProfile -ExecutionPolicy Bypass -File .\scripts\init_cometbft_testnet.ps1
powershell -NoProfile -ExecutionPolicy Bypass -File .\scripts\start_consensus_stack.ps1
$env:PYTHONPATH='src'
.\.venv\Scripts\python.exe scripts\run_local_demo.py
```

The demo uses `compose.consensus.yml`; its three-validator topology is separate
from the isolated four-validator evaluation. Runtime settings: `.env.example`.
Dashboard: `scripts/run_local_dashboard.py`.

## Isolated evaluation

```powershell
.\.venv\Scripts\python.exe scripts\run_replay_evaluation.py --paired-profiles --four-edges --hart-totalizer --generic-plant --simulation-seed 808
```

Add `--smoke` for the short protocol. The launcher creates isolated services and
writes data, models, traces and provenance under `output/`. Offline reevaluation:
`scripts/evaluate_hart_totalizer.py` and `scripts/evaluate_hart_multiseed.py`
(`--source`, `--output`). Public benchmark runner:
`scripts/run_academic_experiments.py --help`.

## Tests

```powershell
$env:PYTHONPATH='src'
.\.venv\Scripts\python.exe -m unittest discover -s tests
```

Go: run `go test ./...` in `abci/consensus_app` with the toolchain from `go.mod`.

Execution is manual. Local datasets, generated outputs and writing materials
are excluded from version control.
