# Story 1.4: Implement MQTT Exchange and Shared State Reconstruction

Status: review

<!-- Note: Validation is optional. Run validate-create-story for quality check before dev-story. -->

## Story

As a researcher,
I want each edge to publish its local observation and consume the others through MQTT,
so that every edge reconstructs its own local replicated compressor-state view needed for later validation.

## Acceptance Criteria

1. Given active edge services and a local MQTT broker, when an edge collects a local observation, then it publishes that observation through MQTT and the other edges consume it through the brokered publish/subscribe flow while the broker remains a passive message relay only.
2. Given cross-edge observation exchange, when all current sensor observations are received, then each edge reconstructs its own local replicated view containing temperature, pressure, and RPM from its own sensor data plus peer data received through MQTT and that edge-local replicated state is explicitly marked or handled as non-validated and not yet valid for downstream processing.

## Tasks / Subtasks

- [x] Define MQTT message contracts for local edge observation exchange. (AC: 1)
  - [x] Reuse the raw HART-style payload produced in Story 1.3 as the publish/consume message body.
  - [x] Keep MQTT message handling limited to relay-based exchange and avoid adding trust or consensus metadata.
- [x] Implement MQTT publish/consume helpers for logically independent edges. (AC: 1)
  - [x] Add minimal MQTT I/O support under `edge_nodes/common/`.
  - [x] Ensure each edge publishes only its own local observation.
  - [x] Ensure each edge consumes peer observations through the broker without treating the broker as part of the trust model.
- [x] Implement per-edge local replicated state reconstruction. (AC: 2)
  - [x] Build each edge-local replicated view from self-observation plus peer observations received through MQTT.
  - [x] Keep the replicated view explicitly intermediate and non-validated.
  - [x] Avoid any central shared-state manager.
- [x] Add simple observability for MQTT exchange and edge-local replicated state. (AC: 1, 2)
  - [x] Make publication, consumption, and local replicated-state contents easy to inspect.
  - [x] Keep observability limited to upstream communication and intermediate state only.
- [x] Add focused tests for MQTT exchange and edge-local replicated state reconstruction. (AC: 1, 2)
  - [x] Verify an edge publishes its own local payload.
  - [x] Verify peer observations are consumed through brokered publish/subscribe behavior.
  - [x] Verify each edge builds its own local replicated view from self plus peers.
  - [x] Verify the resulting edge-local replicated state is treated as non-validated intermediate state.

## Dev Notes

- This story starts where Story 1.3 stops. Reuse the local acquisition payloads already produced by the edge services instead of redefining the edge acquisition boundary. [Source: [1-3-implement-logically-independent-edge-acquisition-services.md](/c:/Users/emili/Desktop/Projets/parallel-truth-fingerprint-prototype/_bmad-output/implementation-artifacts/1-3-implement-logically-independent-edge-acquisition-services.md)]
- The MQTT broker is infrastructure only. It is a passive publish/subscribe relay and is not part of the trust model, validation logic, or consensus decisions. [Source: [architecture.md](/c:/Users/emili/Desktop/Projets/parallel-truth-fingerprint-prototype/_bmad-output/planning-artifacts/architecture.md#L236)]
- Decentralization must remain at the edge layer. Each edge independently publishes its own local observation, consumes peer observations, and builds its own local replicated state. [Source: [architecture.md](/c:/Users/emili/Desktop/Projets/parallel-truth-fingerprint-prototype/_bmad-output/planning-artifacts/architecture.md#L288)]
- Each edge-local replicated state is an intermediate state only. This story must not introduce consensused valid state or any downstream-trusted output. [Source: [architecture.md](/c:/Users/emili/Desktop/Projets/parallel-truth-fingerprint-prototype/_bmad-output/planning-artifacts/architecture.md#L492)]
- Keep the message and state naming aligned with the corrected terminology:
  - raw edge-local observation
  - edge-local replicated state
  - consensused valid state only later in Epic 2
- Story 1.5 will add broader presentation-focused visibility. This story should include only enough observability to verify publish, consume, and intermediate-state reconstruction behavior.

### Project Structure Notes

- Primary implementation areas:
  - `src/parallel_truth_fingerprint/edge_nodes/common/`
  - `src/parallel_truth_fingerprint/edge_nodes/edge_1/`
  - `src/parallel_truth_fingerprint/edge_nodes/edge_2/`
  - `src/parallel_truth_fingerprint/edge_nodes/edge_3/`
- Supporting areas if directly needed:
  - `src/parallel_truth_fingerprint/contracts/`
  - `tests/edge_nodes/`
  - `compose.local.yml` only if a non-breaking local MQTT detail must be referenced, not redesigned
- Do not touch:
  - `consensus/`
  - `scada/`
  - `comparison/`
  - `persistence/`
  - `lstm_service/`
- Avoid introducing a centralized state module outside the edge boundary.

### Technical Requirements

- MQTT is used only for inter-edge communication.
- The broker must be treated as a passive relay.
- Each edge must publish only its own raw local payload.
- Each edge must consume peer payloads and reconstruct its own local replicated view.
- The local replicated view should contain temperature, pressure, and RPM once all observations are available.
- The replicated view must remain clearly non-validated.
- Keep the implementation simple and local. No production-style messaging complexity.

### Architecture Compliance

- MQTT must not be treated as part of the trust model.
- No consensus logic is allowed in this story.
- No SCADA, persistence, or LSTM logic is allowed in this story.
- No central replicated-state authority is allowed in this story.
- Each edge must own its own replicated-state assembly.

### Library / Framework Requirements

- Stay within the current local Python project structure.
- Prefer the simplest MQTT client approach consistent with the approved architecture.
- If MQTT client dependency work is needed, keep it minimal and aligned with the selected architecture stack.

### File Structure Requirements

- Prefer adding:
  - `src/parallel_truth_fingerprint/edge_nodes/common/mqtt_io.py`
  - `src/parallel_truth_fingerprint/edge_nodes/common/local_state.py`
- Extend existing edge service modules only as needed to support publish/consume behavior and local replicated-state assembly.
- Keep the story boundary clear: no consensus contracts or unified payload files should appear here.

### Testing Requirements

- Add focused tests for MQTT exchange and edge-local replicated state only.
- Validate:
  - publish of local observation
  - consume of peer observations
  - construction of one local replicated state per edge
  - explicit non-validated handling of the replicated state
- Do not write tests for consensus, SCADA comparison, persistence, or LSTM in this story.

### Previous Story Intelligence

- Story 1.3 added the raw HART-style local payload and per-edge acquisition services in:
  - [raw_hart_payload.py](/c:/Users/emili/Desktop/Projets/parallel-truth-fingerprint-prototype/src/parallel_truth_fingerprint/contracts/raw_hart_payload.py)
  - [acquisition.py](/c:/Users/emili/Desktop/Projets/parallel-truth-fingerprint-prototype/src/parallel_truth_fingerprint/edge_nodes/common/acquisition.py)
  - [edge_1/service.py](/c:/Users/emili/Desktop/Projets/parallel-truth-fingerprint-prototype/src/parallel_truth_fingerprint/edge_nodes/edge_1/service.py)
  - [edge_2/service.py](/c:/Users/emili/Desktop/Projets/parallel-truth-fingerprint-prototype/src/parallel_truth_fingerprint/edge_nodes/edge_2/service.py)
  - [edge_3/service.py](/c:/Users/emili/Desktop/Projets/parallel-truth-fingerprint-prototype/src/parallel_truth_fingerprint/edge_nodes/edge_3/service.py)
- Reuse those local payloads as MQTT message bodies.
- Keep the Story 1.3 acquisition semantics intact:
  - simulator output -> edge reads -> edge interprets -> payload
- The next step in Story 1.4 is transport plus edge-local replicated-state assembly only.

### Git Intelligence Summary

- Most recent commit title available: `story 1.1`
- Current implemented stories already establish the upstream simulation and local acquisition boundaries; Story 1.4 should build on those rather than redesign them.

### References

- Story definition and acceptance criteria: [epics.md](/c:/Users/emili/Desktop/Projets/parallel-truth-fingerprint-prototype/_bmad-output/planning-artifacts/epics.md#L217)
- MQTT passive relay clarification: [architecture.md](/c:/Users/emili/Desktop/Projets/parallel-truth-fingerprint-prototype/_bmad-output/planning-artifacts/architecture.md#L236)
- Edge-local decentralized behavior: [architecture.md](/c:/Users/emili/Desktop/Projets/parallel-truth-fingerprint-prototype/_bmad-output/planning-artifacts/architecture.md#L288)
- Intermediate-state trust boundary: [architecture.md](/c:/Users/emili/Desktop/Projets/parallel-truth-fingerprint-prototype/_bmad-output/planning-artifacts/architecture.md#L492)
- Previous story implementation: [1-3-implement-logically-independent-edge-acquisition-services.md](/c:/Users/emili/Desktop/Projets/parallel-truth-fingerprint-prototype/_bmad-output/implementation-artifacts/1-3-implement-logically-independent-edge-acquisition-services.md)

## Dev Agent Record

### Agent Model Used

GPT-5 Codex

### Debug Log References

- Story created from Epic 1, Story 1.4 and current architecture refinements.
- No sprint-status file exists yet.
- Previous story context and MQTT architecture constraints loaded for implementation guardrails.
- `venv\\Scripts\\python -m unittest tests.edge_nodes.test_mqtt_replication`
- `venv\\Scripts\\python -m unittest discover -s tests`

### Completion Notes List

- Ultimate context engine analysis completed - comprehensive developer guide created.
- Reused the raw HART-style payload from Story 1.3 as the MQTT publish/consume message body without adding trust metadata.
- Added a minimal passive MQTT relay abstraction that models brokered publish/subscribe behavior while keeping the broker outside the trust model.
- Added per-edge local replicated-state assembly so each edge reconstructs its own intermediate shared view from self-observation plus peer observations.
- Extended the edge acquisition service with publish, consume, and replicated-state helpers without introducing consensus or downstream trust semantics.
- Added focused tests covering local publish behavior, peer consumption through the passive relay, and explicit non-validated replicated-state handling.

### File List

- `_bmad-output/implementation-artifacts/1-4-implement-mqtt-exchange-and-shared-state-reconstruction.md`
- `src/parallel_truth_fingerprint/edge_nodes/common/__init__.py`
- `src/parallel_truth_fingerprint/edge_nodes/common/acquisition.py`
- `src/parallel_truth_fingerprint/edge_nodes/common/local_state.py`
- `src/parallel_truth_fingerprint/edge_nodes/common/mqtt_io.py`
- `tests/edge_nodes/test_mqtt_replication.py`

### Change Log

- 2026-03-24: Implemented Story 1.4 passive MQTT relay behavior, per-edge local replicated-state reconstruction, and focused unit tests.
