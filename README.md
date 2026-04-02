# parallel-truth-fingerprint-prototype

Local academic prototype scaffold for a decentralized industrial-validation architecture.

## Current State

The repository now includes the upstream observation path for Epic 1:

- sensor simulation for one compressor with temperature, pressure, and RPM
- logically independent edge-local acquisition services
- raw HART-style payload construction at the edge boundary
- switchable MQTT transport:
  - passive in-memory relay for deterministic tests
  - real MQTT client path for runtime/demo
- edge-local replicated shared view reconstruction as explicit non-validated intermediate state
- upstream observation-flow logging for demo visibility

The consensus pillar now uses a real CometBFT-backed path for the live demo. Epic 3 is also implemented in the current code through:

- fake OPC UA SCADA-state projection using real OPC UA tooling
- sensor-by-sensor SCADA comparison with configurable tolerance
- distinct SCADA divergence output and alerting
- valid-artifact persistence to local MinIO object storage only

Epic 4 has now started in the current code through:

- MinIO-backed loading of validated persisted artifacts
- normal-only temporal window generation for future fingerprint training
- persisted dataset artifacts under `fingerprint-datasets/`:
  - inspectable manifest JSON
  - reusable `.npz` windows archive
- explicit dataset adequacy evaluation that distinguishes:
  - `runtime-valid only`
  - `meaningful fingerprint-valid`
- local LSTM fingerprint training revalidated against the persisted dataset artifact path
- MinIO-backed model save linked back to the persisted dataset id
- LSTM inference outputs with:
  - anomaly score
  - normal/anomalous classification
  - an explicit runtime-valid-only limitation note when the adequacy floor is not met

The current Epic 4 state is intentionally asymmetric:

- Story 4.2A is implemented and runtime-validated for persisted dataset artifacts
- Story 4.2 has now been revalidated against the persisted dataset artifact path introduced by Story 4.2A
- the default adequacy floor is still not met by the small smoke dataset used for runtime proof
- Story 4.2 and Story 4.3 therefore remain runtime-valid only, not meaningful-fingerprint-valid

The planning artifacts now treat the split PEP files in `docs/input/` as the research source of truth. They also distinguish explicitly between:

- real prototype components such as MQTT, CometBFT plus Go ABCI, fake OPC UA, and MinIO, with the local LSTM added later
- simulated environment components such as sensors, compressor behavior, the SCADA environment itself, and the cloud environment
- conceptual-only dissertation references such as BBD/FABA, Orion/Kafka-style cloud infrastructure, and production-grade SCADA/HMI scope

## Local Execution Model

The prototype remains fully local.

- Edge nodes and core orchestration run as local Python processes.
- MQTT and MinIO infrastructure run as local containerized services.
- The live consensus demo runs against a local 3-validator CometBFT network with a Go ABCI application.
- The LSTM service may also run as a local containerized service later if that improves reproducibility.

This mixed process/container model is a local setup decision only. It is not a production deployment model.

## Planned Next Layers

These layers are approved in planning but are not yet implemented in the current code:

- replay-oriented anomaly validation on top of the new inference layer
- final lightweight SCADA-inspired demo UI, implemented only after the backend/runtime/services are stable

## Runtime/Demo Setup

### 1. Install the optional runtime MQTT client dependency

```powershell
.\venv\Scripts\python -m pip install "paho-mqtt>=2.1,<3"
```

Or, if you prefer to use the optional dependency group from `pyproject.toml`:

```powershell
uv sync --extra runtime-demo
```

### 2. Start the local Mosquitto broker and MinIO

```powershell
docker compose -f compose.local.yml up -d mqtt-broker minio
```

### 3. Start the local CometBFT consensus stack

Initialize the 3-validator local network once:

```powershell
.\scripts\init_cometbft_testnet.ps1
```

Then start the validators plus the 3 ABCI app instances:

```powershell
.\scripts\start_consensus_stack.ps1
```

This stack is the source of truth for the final consensus result in the live demo:

- CometBFT is the real BFT consensus layer
- the Go ABCI application computes the deterministic trust/exclusion result
- the Python layer submits the round and reads back the committed state
- Python no longer finalizes consensus independently on the live demo path

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
- `DEMO_POWER=65.0`
- `DEMO_FAULT_MODE=none`
- `DEMO_FAULTY_EDGES=`

### 5. Run the local demo

```powershell
$env:PYTHONPATH='src'
.\venv\Scripts\python scripts\run_local_demo.py
```

This will:

- create the three logical edge services
- connect them through the selected MQTT transport
- publish local edge observations
- consume peer observations
- reconstruct one edge-local replicated shared view per edge
- submit the consensus round to CometBFT
- query the committed round result back from CometBFT
- build summary/log/alert output from that committed state only
- project the logical SCADA-side state and run the SCADA comparison path
- persist only valid structured artifacts to local MinIO
- print runtime state, replicated state, commit metadata, comparison visibility, persistence visibility, and observation-flow events

### 6. Stop the consensus stack

```powershell
.\scripts\stop_consensus_stack.ps1
```

## Transport Modes

Two MQTT transport modes are supported behind the same edge communication boundary:

- `passive`: in-memory relay for tests and deterministic local checks
- `real`: real MQTT clients against the local broker for runtime/demo

Switch mode through `MQTT_TRANSPORT`.

## Demo Fault Injection

The local demo can inject deterministic inconsistent-edge scenarios without changing the CometBFT-backed live path.

- `DEMO_FAULT_MODE=none`
  normal behavior
- `DEMO_FAULT_MODE=single_edge_exclusion`
  inject one faulty edge so quorum is preserved and the committed result still succeeds
- `DEMO_FAULT_MODE=quorum_loss`
  inject two faulty edges so quorum is lost and the committed result returns `failed_consensus`

Optional target edges can be supplied with `DEMO_FAULTY_EDGES`.

Examples:

```powershell
$env:DEMO_FAULT_MODE='single_edge_exclusion'
$env:DEMO_FAULTY_EDGES='edge-3'
.\venv\Scripts\python scripts\run_local_demo.py
```

```powershell
$env:DEMO_FAULT_MODE='quorum_loss'
$env:DEMO_FAULTY_EDGES='edge-2,edge-3'
.\venv\Scripts\python scripts\run_local_demo.py
```

## Architectural Notes

- MQTT is transport only. The broker is a passive relay and is not part of the trust model.
- Each edge independently acquires, publishes, consumes, and reconstructs its own local replicated shared view.
- The replicated shared view is intermediate, non-validated, and not trusted.
- CometBFT is the source of truth for the final consensus result in the live demo.
- The committed state returned from CometBFT defines the valid system state.
- The Python layer no longer finalizes consensus independently on the live demo path.

## Tests

Run the current test suite with:

```powershell
$env:PYTHONPATH='src'
.\venv\Scripts\python -m unittest discover -s tests
```

## Payload Samples

Reference payload artifacts for later stories are available in:

- `src/parallel_truth_fingerprint/contracts/samples/hart_payload_sample.txt`
- `src/parallel_truth_fingerprint/contracts/samples/unified_hart_payload_sample.txt`
