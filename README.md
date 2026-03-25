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

Consensus, SCADA comparison, persistence, and LSTM stages are still intentionally out of scope in the current code.

## Local Execution Model

The prototype remains fully local.

- Edge nodes and core orchestration run as local Python processes.
- MQTT infrastructure runs as a local containerized service.
- MinIO and the LSTM service may also run as local containerized services later if that improves reproducibility.

This mixed process/container model is a local setup decision only. It is not a production deployment model.

## Runtime/Demo Setup

### 1. Install the optional runtime MQTT client dependency

```powershell
.\venv\Scripts\python -m pip install "paho-mqtt>=2.1,<3"
```

Or, if you prefer to use the optional dependency group from `pyproject.toml`:

```powershell
uv sync --extra runtime-demo
```

### 2. Start the local Mosquitto broker

```powershell
docker compose -f compose.local.yml up -d mqtt-broker
```

### 3. Set the demo environment

The defaults are already present in [.env.example](./.env.example):

- `MQTT_TRANSPORT=real`
- `MQTT_BROKER_HOST=localhost`
- `MQTT_BROKER_PORT=1883`
- `MQTT_TOPIC=edges/observations`
- `DEMO_STEPS=3`
- `DEMO_POWER=65.0`

### 4. Run the local demo

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
- print runtime state, replicated state, and observation-flow events

## Transport Modes

Two MQTT transport modes are supported behind the same edge communication boundary:

- `passive`: in-memory relay for tests and deterministic local checks
- `real`: real MQTT clients against the local broker for runtime/demo

Switch mode through `MQTT_TRANSPORT`.

## Architectural Notes

- MQTT is transport only. The broker is a passive relay and is not part of the trust model.
- Each edge independently acquires, publishes, consumes, and reconstructs its own local replicated shared view.
- The replicated shared view is intermediate, non-validated, and not trusted.
- Only later consensus stages will turn that intermediate view into validated state.

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
