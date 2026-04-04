# parallel-truth-fingerprint-prototype

Local academic prototype for a decentralized industrial-validation and fingerprinting architecture.

## Prototype Status

The current codebase preserves the five real pillars of the prototype:

1. acquisition of sensor values
2. decentralization across edges
3. Byzantine consensus across edges
4. comparison between consensused data and SCADA data
5. LSTM-based fingerprint generation

Implemented in the current prototype:

- one local compressor process simulation with temperature, pressure, and RPM
- one logically independent acquisition path per edge
- raw HART-style payload construction at the edge boundary
- switchable MQTT transport:
  - passive in-memory relay for deterministic tests
  - real MQTT path for runtime and demo use
- edge-local replicated shared-view reconstruction as an explicit intermediate state
- real CometBFT-backed consensus for the live local demo
- deterministic trust and exclusion logic through the Go ABCI application
- fake OPC UA SCADA projection using real OPC UA tooling
- narrow SCADA comparison based only on:
  - temperature
  - pressure
  - rpm
- explicit no-quorum behavior that blocks downstream progression
- explicit SCADA-divergence behavior that blocks downstream progression
- persistence of valid artifacts only to local MinIO object storage
- persisted fingerprint datasets under `fingerprint-datasets/`:
  - manifest JSON
  - reusable `.npz` windows archive
- adequacy evaluation that distinguishes:
  - `runtime_valid_only`
  - `meaningful_fingerprint_valid`
- local LSTM training and inference against the persisted dataset artifact path
- deferred first training after an eligible-history threshold
- saved-model reuse for later-cycle inference
- replay-oriented fingerprint evaluation through a richer SCADA-side behavioral payload
- local operator dashboard with:
  - runtime start and stop
  - scenario activation
  - compressor power control
  - interpreted events
  - raw-log access
  - explainability and evidence views
  - architecture-aligned pipeline blocks

## Current Limitations

- The main remaining limitation is still dataset adequacy, not missing local runtime plumbing.
- A dataset becomes stronger only after reaching the approved adequacy floor:
  - `30` eligible artifacts
  - `20` generated windows
- By default, the runtime can train the first model earlier than that threshold. That proves the pipeline works, but it does not yet justify a stronger academic fingerprint claim.
- Once the first model exists, the current lifecycle reuses it. It does not automatically retrain a second model later in the same run.
- The replay path is implemented and separated correctly from SCADA divergence and no-quorum behavior, but the strongest live replay demonstration still depends on:
  - a fresh bucket
  - a stronger normal-history baseline
  - replay being triggered only after the first model exists
- SCADA comparison is intentionally narrow. Richer behavioral fields belong to the fingerprint path, not to the SCADA supervisory comparison rule.

## Local Execution Model

The prototype remains fully local.

- Edge nodes and orchestration run as local Python processes.
- MQTT and MinIO run as local containerized services.
- The live consensus demo runs against a local 3-validator CometBFT network with a Go ABCI application.
- The fingerprint lifecycle runs inside the same local Python runtime and reuses the existing MinIO boundary.

This mixed process/container model is a local setup decision only. It is not a production deployment model.

## Local Demo Setup

### 1. Install the local runtime dependencies

```powershell
venv\Scripts\uv.exe sync --extra ml-training --extra runtime-demo
```

### 2. Start MQTT and MinIO

```powershell
docker compose -f compose.local.yml up -d mqtt-broker minio
```

### 3. Start the local consensus stack

Initialize the 3-validator local network once:

```powershell
.\scripts\init_cometbft_testnet.ps1
```

Then start the validators and the 3 ABCI instances:

```powershell
.\scripts\start_consensus_stack.ps1
```

This stack is the source of truth for the committed consensus result in the live demo:

- CometBFT is the real BFT consensus layer
- the Go ABCI application computes the deterministic trust and exclusion result
- the Python layer submits the round and reads back the committed state

### 4. Set the demo environment

The defaults are already present in [.env.example](./.env.example):

- `MQTT_TRANSPORT=real`
- `MQTT_BROKER_HOST=localhost`
- `MQTT_BROKER_PORT=1883`
- `MQTT_TOPIC=edges/observations`
- `COMETBFT_RPC_URL=http://127.0.0.1:26657`
- `MINIO_ENDPOINT=localhost:9000`
- `MINIO_ACCESS_KEY=minioadmin`
- `MINIO_SECRET_KEY=minioadmin`
- `MINIO_BUCKET=valid-consensus-artifacts`
- `MINIO_SECURE=false`
- `DEMO_STEPS=3`
- `DEMO_CYCLE_INTERVAL_SECONDS=60`
- `DEMO_MAX_CYCLES=0`
- `DEMO_TRAIN_AFTER_ELIGIBLE_CYCLES=10`
- `DEMO_FINGERPRINT_SEQUENCE_LENGTH=2`
- `DEMO_POWER=65.0`
- `DEMO_DASHBOARD_HOST=127.0.0.1`
- `DEMO_DASHBOARD_PORT=8088`
- `DEMO_SCENARIO=`
- `DEMO_SCENARIO_START_CYCLE=1`
- `DEMO_FAULT_MODE=none`
- `DEMO_FAULTY_EDGES=`
- `DEMO_SCADA_MODE=match`
- `DEMO_SCADA_START_CYCLE=0`
- `DEMO_SCADA_OFFSET_VALUE=6.0`

### 5. Recommended clean run for a stronger fingerprint baseline

Use a fresh bucket when you want a clean demonstration run:

```powershell
$env:PYTHONPATH='src'
$env:MINIO_BUCKET='fresh-demo-20260404'
$env:DEMO_LOG_PATH='logs/fresh-demo-20260404.log'
```

For a stronger first fingerprint baseline, delay first training until the adequacy target:

```powershell
$env:DEMO_TRAIN_AFTER_ELIGIBLE_CYCLES='30'
```

### 6. Run the local demo runtime directly

```powershell
$env:PYTHONPATH='src'
.\venv\Scripts\python scripts\run_local_demo.py
```

This will:

- create the three logical edge services
- connect them through the selected MQTT transport
- execute the full cycle on a recurring cadence
- publish local edge observations
- consume peer observations
- reconstruct one edge-local replicated view per edge
- submit the round to CometBFT
- query the committed result back from CometBFT
- project the logical SCADA-side state
- compare the consensused state against the SCADA supervisory values
- persist only valid artifacts to local MinIO
- accumulate valid history over time for later training
- defer first fingerprint training until the configured threshold is reached
- reuse the saved model for later-cycle inference
- apply the selected scenario through the approved runtime path without bypassing persistence, dataset, training, or inference boundaries

Stop the runtime with `Ctrl+C`.

### 7. Run the local operator dashboard

```powershell
$env:PYTHONPATH='src'
.\venv\Scripts\python scripts\run_local_dashboard.py
```

Open:

- Dashboard: `http://127.0.0.1:8088`
- MinIO console: `http://127.0.0.1:9001`

MinIO login:

- user: `minioadmin`
- password: `minioadmin`

From the dashboard you can:

- start and stop the autonomous runtime
- activate supported scenarios through the approved runtime path
- change compressor power through the real simulator/runtime flow
- monitor cycle cadence, artifacts, lifecycle state, replay behavior, and channel separation

### 8. Stop the local stack

```powershell
Ctrl+C
.\scripts\stop_consensus_stack.ps1
docker compose -f compose.local.yml down
```

## Transport Modes

Two MQTT transport modes are supported behind the same edge communication boundary:

- `passive`: in-memory relay for tests and deterministic local checks
- `real`: real MQTT clients against the local broker for runtime/demo

Switch mode through `MQTT_TRANSPORT`.

## Demo Scenario Control

The local demo can activate deterministic scenarios without changing the CometBFT-backed path or bypassing the approved runtime boundaries.

The simplest explicit control is:

- `DEMO_SCENARIO=normal`
- `DEMO_SCENARIO=scada_replay`
- `DEMO_SCENARIO=scada_freeze`
- `DEMO_SCENARIO=scada_divergence`
- `DEMO_SCENARIO=single_edge_exclusion`
- `DEMO_SCENARIO=quorum_loss`
- `DEMO_SCENARIO_START_CYCLE=<cycle index>`

Examples:

```powershell
$env:DEMO_SCENARIO='scada_replay'
$env:DEMO_SCENARIO_START_CYCLE='35'
.\venv\Scripts\python scripts\run_local_demo.py
```

```powershell
$env:DEMO_SCENARIO='single_edge_exclusion'
$env:DEMO_SCENARIO_START_CYCLE='2'
.\venv\Scripts\python scripts\run_local_demo.py
```

Lower-level controls are still supported and map into the same runtime path:

- `DEMO_FAULT_MODE=none`
- `DEMO_FAULT_MODE=single_edge_exclusion`
- `DEMO_FAULT_MODE=quorum_loss`
- `DEMO_SCADA_MODE=match`
- `DEMO_SCADA_MODE=offset`
- `DEMO_SCADA_MODE=replay`
- `DEMO_SCADA_MODE=freeze`
- `DEMO_SCADA_START_CYCLE=<cycle index>`
- `DEMO_SCADA_OFFSET_VALUE=<base offset>`

## Recommended Replay Demonstration

For the strongest replay-oriented fingerprint demonstration in the current prototype:

1. start with a fresh MinIO bucket
2. train the first model after `30` eligible artifacts
3. keep the baseline normal until that first model exists
4. apply a clear compressor power change
5. let the process evolve for a few cycles
6. trigger `scada_replay`

This keeps:

- SCADA comparison narrow to `temperature`, `pressure`, and `rpm`
- replay distinct from SCADA divergence
- fingerprint behavior tied to richer SCADA-side payload rather than only a simple supervisory mismatch

## Architectural Notes

- MQTT is transport only. The broker is not part of the trust model.
- Each edge independently acquires, publishes, consumes, and reconstructs its own local replicated shared view.
- The replicated shared view is intermediate and not trusted.
- CometBFT is the source of truth for the committed consensus result in the live demo.
- The committed state returned from CometBFT defines the valid system state.
- SCADA comparison remains a later supervisory check, not the origin of truth.
- The fingerprint path is a behavioral interpretation stage built on persisted valid history.

## Tests

Run the current test suite with:

```powershell
$env:PYTHONPATH='src'
.\venv\Scripts\python -m unittest discover -s tests
```

## Payload Samples

Reference payload artifacts are available in:

- `src/parallel_truth_fingerprint/contracts/samples/hart_payload_sample.txt`
- `src/parallel_truth_fingerprint/contracts/samples/unified_hart_payload_sample.txt`
