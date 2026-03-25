# Story 1.5: Add Observation-Flow Logging and Runtime MQTT Demo Support

Status: ready-for-dev

<!-- Note: Validation is optional. Run validate-create-story for quality check before dev-story. -->

## Story

As a researcher,
I want clear logs and observable state for the acquisition and MQTT replication flow, plus real MQTT runtime support,
so that the decentralized observation stage is demonstrable and traceable before consensus is introduced.

## Acceptance Criteria

1. Given the sensor simulation and edge communication flow, when the prototype runs, then logs show sensor generation, local edge acquisition, MQTT publication, MQTT consumption, and shared-state reconstruction and the outputs are presentation-friendly and reproducible.
2. Given the trust-boundary rules, when an edge-local replicated state is displayed or logged, then it is distinguishable from future consensused valid state and the system does not present it as validated output.
3. Given optional minimal visualization support, when an edge-local replicated intermediate state is shown to support demonstration, then it may be displayed through logs, simple charts, or simple metrics and it remains clearly identified as non-validated intermediate state.
4. Given local demo/runtime execution, when MQTT transport is used outside tests, then edges connect as real MQTT clients to a real local broker and the system can switch between the passive in-memory relay for tests and real MQTT transport for runtime/demo without changing the architectural boundaries.

## Tasks / Subtasks

- [ ] Add structured observation-flow logging for the upstream pipeline. (AC: 1, 2)
  - [ ] Log sensor generation, local edge acquisition, MQTT publication, MQTT consumption, and edge-local replicated-state reconstruction.
  - [ ] Keep logs presentation-friendly and explicit about intermediate non-validated state.
- [ ] Add simple observation-state display helpers. (AC: 2, 3)
  - [ ] Provide a lightweight way to inspect edge-local replicated state through logs or simple local metrics/state output.
  - [ ] Ensure any displayed state is clearly marked as non-validated intermediate state.
- [ ] Introduce a transport abstraction that supports passive relay for tests and real MQTT for runtime/demo. (AC: 4)
  - [ ] Keep the passive in-memory relay available for deterministic tests.
  - [ ] Add a real MQTT transport path for runtime/demo use.
  - [ ] Ensure both transport paths preserve the same edge-owned publish/consume responsibilities.
- [ ] Add real MQTT broker/client demo support. (AC: 4)
  - [ ] Use the local Mosquitto broker from `compose.local.yml` as the real runtime broker.
  - [ ] Make edges connect as real MQTT clients in the runtime/demo path.
  - [ ] Keep the broker as passive infrastructure only, outside the trust model.
- [ ] Add focused tests for observability and transport switching. (AC: 1, 2, 4)
  - [ ] Verify observation-flow logs or outputs include the required upstream stages.
  - [ ] Verify transport selection can use passive relay in tests.
  - [ ] Verify the real MQTT transport path is isolated behind the same transport boundary, even if exercised with integration-style checks only.

## Dev Notes

- This story expands the upstream observation stage for demonstration and runtime completeness. It must still stop before consensus. [Source: [epics.md](/c:/Users/emili/Desktop/Projets/parallel-truth-fingerprint-prototype/_bmad-output/planning-artifacts/epics.md#L234)]
- Story 1.4 already proved the decentralized behavior using a passive in-memory relay. Preserve that path for tests because it keeps edge behavior deterministic and simple. [Source: [1-4-implement-mqtt-exchange-and-shared-state-reconstruction.md](/c:/Users/emili/Desktop/Projets/parallel-truth-fingerprint-prototype/_bmad-output/implementation-artifacts/1-4-implement-mqtt-exchange-and-shared-state-reconstruction.md)]
- For runtime/demo completeness, add a real MQTT client path that connects to the real local broker configured through Docker Compose. This is a local reproducibility/runtime concern, not a change to the trust model. [Source: [architecture.md](/c:/Users/emili/Desktop/Projets/parallel-truth-fingerprint-prototype/_bmad-output/planning-artifacts/architecture.md#L756)]
- MQTT remains transport only. Whether using passive in-memory relay or the real broker/client path, the broker must remain outside the trust model and outside any validation decision. [Source: [architecture.md](/c:/Users/emili/Desktop/Projets/parallel-truth-fingerprint-prototype/_bmad-output/planning-artifacts/architecture.md#L236)]
- Each edge still owns its own publish, consume, and replicated-state assembly responsibilities. Do not introduce a central state coordinator while adding runtime/demo transport support. [Source: [architecture.md](/c:/Users/emili/Desktop/Projets/parallel-truth-fingerprint-prototype/_bmad-output/planning-artifacts/architecture.md#L288)]
- Keep Story 1.5 focused on observation-flow visibility and runtime transport completeness only. Do not add consensus, SCADA, persistence, or LSTM behavior here.

### Project Structure Notes

- Primary implementation areas:
  - `src/parallel_truth_fingerprint/edge_nodes/common/`
  - `src/parallel_truth_fingerprint/edge_nodes/`
  - optionally `src/parallel_truth_fingerprint/observability/` for lightweight upstream logging helpers if truly needed
- Supporting areas if directly needed:
  - `compose.local.yml`
  - `.env.example`
  - `tests/edge_nodes/`
- Do not touch:
  - `consensus/`
  - `scada/`
  - `comparison/`
  - `persistence/`
  - `lstm_service/`
- Keep the transport switch behind a boundary in the edge communication layer, not spread through business logic.

### Technical Requirements

- Keep the passive in-memory relay available for tests.
- Add a real MQTT client path for runtime/demo.
- Use the Mosquitto broker defined in `compose.local.yml`.
- Transport selection must not change edge responsibilities:
  - edge acquires local payload
  - edge publishes local payload
  - edge consumes peer payloads
  - edge reconstructs its own local replicated state
- Observation-flow output must cover:
  - simulation output
  - local acquisition payload creation
  - MQTT publication
  - MQTT consumption
  - edge-local replicated-state contents
- Any displayed replicated state must remain explicitly non-validated.

### Architecture Compliance

- The broker remains passive infrastructure only.
- No consensus or trusted-state semantics may be introduced here.
- No SCADA, persistence, or LSTM work belongs in this story.
- Real MQTT support is for local runtime/demo completeness only and must not turn into deployment/platform expansion.
- The passive relay and real MQTT paths must both preserve the same decentralized edge model.

### Library / Framework Requirements

- Stay within the current local Python project structure.
- If a real MQTT client dependency is introduced, keep it minimal and consistent with the approved architecture.
- Do not add unnecessary UI or infrastructure frameworks.

### File Structure Requirements

- Likely implementation areas:
  - `src/parallel_truth_fingerprint/edge_nodes/common/mqtt_io.py`
  - `src/parallel_truth_fingerprint/edge_nodes/common/local_state.py`
  - optional lightweight upstream observability helper(s)
- Keep real transport support behind a narrow interface so tests can continue using the passive relay.

### Testing Requirements

- Add focused tests for:
  - observation-flow logging/output shape
  - transport selection behavior
  - preservation of non-validated replicated-state labeling
- Keep deterministic unit tests on the passive relay path.
- Real MQTT verification may use focused integration-style checks, but it must stay local and simple.

### Previous Story Intelligence

- Story 1.4 added:
  - passive in-memory relay behavior in [mqtt_io.py](/c:/Users/emili/Desktop/Projets/parallel-truth-fingerprint-prototype/src/parallel_truth_fingerprint/edge_nodes/common/mqtt_io.py)
  - edge-local replicated state in [local_state.py](/c:/Users/emili/Desktop/Projets/parallel-truth-fingerprint-prototype/src/parallel_truth_fingerprint/edge_nodes/common/local_state.py)
  - publish/consume hooks in [acquisition.py](/c:/Users/emili/Desktop/Projets/parallel-truth-fingerprint-prototype/src/parallel_truth_fingerprint/edge_nodes/common/acquisition.py)
- Preserve those boundaries. Story 1.5 should extend transport/runtime completeness and observability, not redesign the publish/consume or replicated-state model.

### Git Intelligence Summary

- Most recent commit title available: `story 1.1`
- Current code already supports the passive relay path; Story 1.5 should layer real runtime MQTT support and upstream observability on top of it.

### References

- Story definition and acceptance criteria: [epics.md](/c:/Users/emili/Desktop/Projets/parallel-truth-fingerprint-prototype/_bmad-output/planning-artifacts/epics.md#L234)
- MQTT passive relay clarification: [architecture.md](/c:/Users/emili/Desktop/Projets/parallel-truth-fingerprint-prototype/_bmad-output/planning-artifacts/architecture.md#L236)
- Mixed local process/container execution model: [architecture.md](/c:/Users/emili/Desktop/Projets/parallel-truth-fingerprint-prototype/_bmad-output/planning-artifacts/architecture.md#L756)
- Local broker scaffold: [compose.local.yml](/c:/Users/emili/Desktop/Projets/parallel-truth-fingerprint-prototype/compose.local.yml)
- Previous story implementation: [1-4-implement-mqtt-exchange-and-shared-state-reconstruction.md](/c:/Users/emili/Desktop/Projets/parallel-truth-fingerprint-prototype/_bmad-output/implementation-artifacts/1-4-implement-mqtt-exchange-and-shared-state-reconstruction.md)

## Dev Agent Record

### Agent Model Used

GPT-5 Codex

### Debug Log References

- Story created from Epic 1, Story 1.5 plus the new runtime/demo MQTT requirement.
- No sprint-status file exists yet.
- Previous passive-relay implementation and local broker scaffold reviewed for guardrails.

### Completion Notes List

- Ultimate context engine analysis completed - comprehensive developer guide created.

### File List

- `_bmad-output/implementation-artifacts/1-5-add-observation-flow-logging-and-runtime-mqtt-demo-support.md`
