# Story 1.3: Implement Logically Independent Edge Acquisition Services

Status: review

<!-- Note: Validation is optional. Run validate-create-story for quality check before dev-story. -->

## Story

As a researcher,
I want each edge to acquire only its own local sensor through pre-PLC acquisition semantics,
so that the prototype preserves decentralized physical-side observation even on one machine.

## Acceptance Criteria

1. Given three logical edge nodes, when the local edge services run, then Edge 1 acquires only temperature, Edge 2 only pressure, and Edge 3 only RPM and each edge uses pre-PLC physical acquisition semantics (conceptual HART / 4-20 mA reference) at the local acquisition boundary.
2. Given the payload-driven data model, when an edge emits a local acquisition payload, then it follows the raw HART-style payload structure used by the project and it includes process variables, loop current, diagnostics, and available local physics metrics needed for downstream enrichment.
3. Given local co-location on one machine, when edge services execute, then each edge maintains its own acquisition flow and local runtime context and no shared mutable state collapses the decentralized edge model.

## Tasks / Subtasks

- [x] Define the edge acquisition contract for raw HART-style payloads. (AC: 1, 2)
  - [x] Add a lightweight typed payload model aligned with the raw HART-style sample structure.
  - [x] Keep the contract local to edge acquisition and avoid introducing consensus or unified payload semantics.
- [x] Implement shared acquisition helpers for edge-local sensor mapping. (AC: 1, 2)
  - [x] Map each edge to exactly one local sensor.
  - [x] Convert simulator output into a raw HART-style acquisition payload with process data, loop current, diagnostics, and local physics metrics.
  - [x] Keep acquisition semantics pre-PLC and upstream-only.
- [x] Implement three logically independent edge services. (AC: 1, 3)
  - [x] Add one service per edge under `edge_nodes/edge_1`, `edge_nodes/edge_2`, and `edge_nodes/edge_3`.
  - [x] Ensure each service owns its own runtime context and acquisition path.
  - [x] Do not introduce shared mutable state across edge services.
- [x] Add simple observability for local acquisition outputs. (AC: 1, 2, 3)
  - [x] Make each edge payload easy to inspect through a simple serialization or state output.
  - [x] Keep observability limited to local acquisition only.
- [x] Add focused tests for payload shape and strict edge independence. (AC: 1, 2, 3)
  - [x] Verify each edge acquires only its assigned sensor.
  - [x] Verify each emitted payload follows the expected raw HART-style shape.
  - [x] Verify separate edge services keep distinct local runtime context.

## Dev Notes

- This story is limited to local edge acquisition only. Do not implement MQTT publishing/consumption, edge-local replicated state assembly, consensus, SCADA comparison, persistence, or LSTM logic here. [Source: [epics.md](/c:/Users/emili/Desktop/Projets/parallel-truth-fingerprint-prototype/_bmad-output/planning-artifacts/epics.md#L192)]
- The MQTT broker is passive relay infrastructure only and is not part of the trust model. Nothing in this story should add MQTT behavior or rely on it for correctness. [Source: [architecture.md](/c:/Users/emili/Desktop/Projets/parallel-truth-fingerprint-prototype/_bmad-output/planning-artifacts/architecture.md#L236)]
- Each edge must remain logically independent even on one machine. That means separate local acquisition flow, separate runtime context, and no shared mutable state across edge services. [Source: [architecture.md](/c:/Users/emili/Desktop/Projets/parallel-truth-fingerprint-prototype/_bmad-output/planning-artifacts/architecture.md#L350)]
- Edge-local replicated state is a later-stage artifact built from self-observation plus peer observations. This story must stop at local raw acquisition payload generation. [Source: [architecture.md](/c:/Users/emili/Desktop/Projets/parallel-truth-fingerprint-prototype/_bmad-output/planning-artifacts/architecture.md#L492)]
- Use the raw HART-style payload sample as the shape reference for acquisition output. Do not reinterpret this story as the post-consensus unified payload story. [Source: [hart_payload_sample.txt](/c:/Users/emili/Desktop/Projets/parallel-truth-fingerprint-prototype/src/parallel_truth_fingerprint/contracts/samples/hart_payload_sample.txt)]
- Reuse Story 1.2 simulation output as the upstream input source. Do not duplicate the simulation logic or create a second behavior model.

### Project Structure Notes

- Primary implementation areas:
  - `src/parallel_truth_fingerprint/edge_nodes/common/`
  - `src/parallel_truth_fingerprint/edge_nodes/edge_1/`
  - `src/parallel_truth_fingerprint/edge_nodes/edge_2/`
  - `src/parallel_truth_fingerprint/edge_nodes/edge_3/`
- Supporting areas if directly needed:
  - `src/parallel_truth_fingerprint/contracts/`
  - `src/parallel_truth_fingerprint/sensor_simulation/`
  - `tests/edge_nodes/`
- Do not touch:
  - `consensus/`
  - `scada/`
  - `comparison/`
  - `persistence/`
  - `lstm_service/`
- Keep naming aligned with the approved architecture and the current edge-local replicated state terminology.

### Technical Requirements

- Edge 1 acquires only temperature.
- Edge 2 acquires only pressure.
- Edge 3 acquires only RPM.
- Local acquisition payloads must be raw HART-style and must include:
  - device information
  - process data with `pv`, `sv`, `loop_current_ma`, and `pv_percent_range`
  - diagnostics
  - available local physics metrics
- The implementation should stay simple and observable, not production-grade.
- Reproducibility matters. If acquisition calculations depend on deterministic simulation state, preserve deterministic inputs in tests.

### Architecture Compliance

- The story must stop at local acquisition.
- No MQTT behavior is allowed in this story.
- No edge-local replicated state is produced here.
- No consensused or validated state semantics are allowed here.
- No central acquisition coordinator or fake global edge manager should be introduced.

### Library / Framework Requirements

- Stay within the current local Python project structure.
- Do not add new frameworks or external infrastructure dependencies for this story.
- Use standard-library Python only unless an existing project dependency is clearly required.

### File Structure Requirements

- Prefer adding:
  - `src/parallel_truth_fingerprint/edge_nodes/common/acquisition.py`
  - `src/parallel_truth_fingerprint/edge_nodes/edge_1/service.py`
  - `src/parallel_truth_fingerprint/edge_nodes/edge_2/service.py`
  - `src/parallel_truth_fingerprint/edge_nodes/edge_3/service.py`
- Add a small typed payload contract only if it simplifies testability and keeps the story boundary clear.

### Testing Requirements

- Add focused edge acquisition tests only.
- Validate:
  - one-sensor-per-edge enforcement
  - raw HART-style payload shape
  - local runtime context isolation across edges
- Do not write tests for MQTT, replicated-state reconstruction, consensus, SCADA, persistence, or LSTM in this story.

### Previous Story Intelligence

- Story 1.2 introduced the deterministic `CompressorSimulator`, default simulation ranges, temperature-driven noise, and upstream-only control hooks in:
  - [simulator.py](/c:/Users/emili/Desktop/Projets/parallel-truth-fingerprint-prototype/src/parallel_truth_fingerprint/sensor_simulation/simulator.py)
  - [behavior_model.py](/c:/Users/emili/Desktop/Projets/parallel-truth-fingerprint-prototype/src/parallel_truth_fingerprint/sensor_simulation/behavior_model.py)
  - [ranges.py](/c:/Users/emili/Desktop/Projets/parallel-truth-fingerprint-prototype/src/parallel_truth_fingerprint/config/ranges.py)
- Reuse those outputs as acquisition inputs instead of reimplementing sensor generation.
- Keep the Story 1.2 trust boundary intact: simulation output is upstream-only and must not be labeled as replicated or validated.

### Git Intelligence Summary

- Most recent commit title available: `story 1.1`
- No recent git history yet constrains Story 1.3 beyond the current architecture and story artifacts.

### References

- Story definition and acceptance criteria: [epics.md](/c:/Users/emili/Desktop/Projets/parallel-truth-fingerprint-prototype/_bmad-output/planning-artifacts/epics.md#L192)
- Edge-local replicated state and trust boundary: [architecture.md](/c:/Users/emili/Desktop/Projets/parallel-truth-fingerprint-prototype/_bmad-output/planning-artifacts/architecture.md#L492)
- MQTT passive relay clarification: [architecture.md](/c:/Users/emili/Desktop/Projets/parallel-truth-fingerprint-prototype/_bmad-output/planning-artifacts/architecture.md#L236)
- Raw payload reference: [hart_payload_sample.txt](/c:/Users/emili/Desktop/Projets/parallel-truth-fingerprint-prototype/src/parallel_truth_fingerprint/contracts/samples/hart_payload_sample.txt)
- Previous story implementation: [1-2-implement-sensor-simulation-with-controlled-normal-behavior.md](/c:/Users/emili/Desktop/Projets/parallel-truth-fingerprint-prototype/_bmad-output/implementation-artifacts/1-2-implement-sensor-simulation-with-controlled-normal-behavior.md)

## Dev Agent Record

### Agent Model Used

GPT-5 Codex

### Debug Log References

- Story created from Epic 1, Story 1.3 and current architecture refinements.
- No sprint-status file exists yet.
- Previous story context and raw payload sample loaded for implementation guardrails.
- `venv\\Scripts\\python -m unittest tests.edge_nodes.test_acquisition_services`
- `venv\\Scripts\\python -m unittest discover -s tests`

### Completion Notes List

- Ultimate context engine analysis completed - comprehensive developer guide created.
- Added a typed raw HART-style acquisition payload contract with device info, process data, diagnostics, and local physics metrics.
- Added shared acquisition helpers that map each edge to exactly one local sensor and derive loop current, percent range, and local stability metrics from simulator input.
- Added three logically independent edge services for temperature, pressure, and RPM acquisition without introducing MQTT, replicated state, or downstream trust semantics.
- Added simple inspectable runtime state per edge service to keep local acquisition observable.
- Added focused edge acquisition tests covering one-sensor-per-edge enforcement, payload shape, and runtime context isolation.

### File List

- `_bmad-output/implementation-artifacts/1-3-implement-logically-independent-edge-acquisition-services.md`
- `src/parallel_truth_fingerprint/contracts/__init__.py`
- `src/parallel_truth_fingerprint/contracts/raw_hart_payload.py`
- `src/parallel_truth_fingerprint/edge_nodes/__init__.py`
- `src/parallel_truth_fingerprint/edge_nodes/common/__init__.py`
- `src/parallel_truth_fingerprint/edge_nodes/common/acquisition.py`
- `src/parallel_truth_fingerprint/edge_nodes/edge_1/service.py`
- `src/parallel_truth_fingerprint/edge_nodes/edge_2/service.py`
- `src/parallel_truth_fingerprint/edge_nodes/edge_3/service.py`
- `tests/edge_nodes/__init__.py`
- `tests/edge_nodes/test_acquisition_services.py`

### Change Log

- 2026-03-24: Implemented Story 1.3 edge-local acquisition contracts, per-edge acquisition services, and focused unit tests.
