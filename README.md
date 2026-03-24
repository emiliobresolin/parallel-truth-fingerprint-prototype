# parallel-truth-fingerprint-prototype

Local academic prototype scaffold for a decentralized industrial-validation architecture.

## Scope of This Bootstrap

This repository currently contains only:

- minimal `uv` bootstrap metadata
- architecture-driven directory structure
- local orchestration scaffolding for infrastructure services
- configuration and documentation stubs
- payload sample references for later contract work

No business logic is implemented yet.

## Local Execution Model

The prototype remains fully local.

- Edge nodes and core orchestration are intended to run as local Python processes.
- MQTT infrastructure is intended to run as a local containerized service.
- MinIO and the LSTM service may also run as local containerized services later if that improves reproducibility.

This mixed process/container model is a local setup decision only. It is not a production deployment model.

## Next Implementation Focus

Later stories will add:

- sensor simulation
- edge acquisition
- MQTT exchange
- consensus
- SCADA comparison
- persistence
- LSTM processing
- observability

## Payload Samples

Reference payload artifacts for later stories are available in:

- `src/parallel_truth_fingerprint/contracts/samples/hart_payload_sample.txt`
- `src/parallel_truth_fingerprint/contracts/samples/unified_hart_payload_sample.txt`
