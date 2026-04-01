# Story 3.1: Implement Fake OPC UA Logical SCADA Service

Status: review

<!-- Note: Validation is optional. Run validate-create-story for quality check before dev-story. -->

## Story

As a researcher,
I want the logical supervisory state to be exposed through a realistic local SCADA interface,
so that the prototype prioritizes industrial alignment without adding production complexity.

## Scope Notes

- This story is limited to the fake SCADA boundary for one compressor and three sensors: temperature, pressure, and RPM.
- The SCADA environment remains simulated, but the implementation must use real OPC UA technology.
- The service must consume the current consensused valid payload reality established by Epic 2.
- The service must expose logical supervisory values only. It is not a physical truth source and it must not duplicate consensus logic.
- Keep future divergence support local and lightweight:
  - normal matching values
  - offset values
  - frozen values
  - replayed supervisory values
- Do not implement Story 3.2 comparison logic here beyond the minimal interface needed for future consumption.
- Do not introduce FastAPI fallback as default scope.
- This story should be additive and must not redesign MQTT, CometBFT, MinIO, LSTM, or the Story 1.6 acquisition semantics.

## Acceptance Criteria

1. Given the approved local prototype scope, when the SCADA component is implemented, then the preferred implementation is a simple local Python OPC UA server and it represents the logical supervisory state rather than the physical truth source.
2. Given the current upstream architecture, when the fake SCADA service is updated from a consensused valid payload, then it consumes the current committed valid-state model rather than reintroducing generic float-only assumptions or mandatory `compressor_power` downstream fields.
3. Given the prototype scope of one compressor and three sensors, when the OPC UA server is started, then it exposes logical SCADA-side values for temperature, pressure, and RPM using a stable address space suitable for later consumption.
4. Given normal operation, when no divergence override is active, then the logical SCADA-side values match the current consensused valid payload sensor values.
5. Given controlled demonstration scenarios, when SCADA-side divergence behavior is configured, then the SCADA layer can intentionally produce replayed, frozen, or offset supervisory values without bypassing the normal service boundary.
6. Given the Story 3.1 scope guardrails, when this story is implemented, then it does not implement the Story 3.2 comparison decision logic and it does not redesign MQTT, CometBFT, fake OPC UA scope, storage, or LSTM.
7. Given review and testing needs, when focused tests are run, then they prove the OPC UA service can expose the three logical values, update them from consensused valid state, and support future divergence scenarios in a deterministic way.

## Tasks / Subtasks

- [x] Add the standalone fake SCADA logical-state contracts. (AC: 2, 3, 4, 5, 7)
  - [x] Define a typed logical SCADA state contract for one compressor and the three supervisory sensor values.
  - [x] Keep the contract additive and small.
  - [x] Preserve downstream consumption clarity for Story 3.2.
- [x] Implement the local OPC UA server service. (AC: 1, 3, 4, 5, 6, 7)
  - [x] Use a real Python OPC UA library.
  - [x] Expose a stable address space for one compressor and the three sensors.
  - [x] Keep the implementation local, lightweight, and easy to start and stop in tests.
- [x] Implement deterministic logical-state projection from consensused valid payloads. (AC: 2, 4, 5, 7)
  - [x] Accept the current `ConsensusedValidState` contract as input.
  - [x] Publish matching logical values by default.
  - [x] Support additive offset/freeze/replay scenario controls without adding comparison logic.
- [x] Add focused Story 3.1 tests. (AC: 3, 4, 5, 7)
  - [x] Verify normal matching values.
  - [x] Verify offset/freeze/replay supervisory overrides.
  - [x] Verify real OPC UA exposure of the three sensor values.
  - [x] Keep tests local and deterministic.

## Dev Notes

- Story 3.1 starts Epic 3 and must stay narrowly scoped to the fake OPC UA SCADA service. [Source: [epics.md](/c:/Users/emili/Desktop/Projets/parallel-truth-fingerprint-prototype/_bmad-output/planning-artifacts/epics.md)]
- The split proposal files in `docs/input/` remain the research source of truth.
- The SCADA environment is simulated, but the OPC UA technology must be real in the prototype.
- This story must sit on top of the current implementation truth:
  - Story 1.6 refined the acquisition payload into structured transmitter-inspired sensor data.
  - Epic 2 established the real committed consensus path through CometBFT plus Go ABCI.
- The fake OPC UA service must consume the downstream `ConsensusedValidState` model and expose logical supervisory values only.
- No Story 3.2 comparison logic belongs here beyond the minimal interfaces needed for later consumption.
- No FastAPI fallback belongs in default Story 3.1 scope.

### Project Structure Notes

- Primary implementation areas:
  - `src/parallel_truth_fingerprint/scada/`
  - `src/parallel_truth_fingerprint/contracts/`
  - `tests/scada/`
- Supporting areas if directly needed:
  - `src/parallel_truth_fingerprint/contracts/consensused_valid_state.py`
  - `scripts/run_local_demo.py`
- Do not redesign:
  - `src/parallel_truth_fingerprint/edge_nodes/`
  - `src/parallel_truth_fingerprint/consensus/`
  - `src/parallel_truth_fingerprint/persistence/`
  - `src/parallel_truth_fingerprint/lstm_service/`

### Technical Requirements

- Use a real Python OPC UA implementation.
- Keep the server local and lightweight.
- Expose one compressor and exactly three logical sensor values:
  - temperature
  - pressure
  - rpm
- Provide a deterministic update path from `ConsensusedValidState`.
- Provide simple scenario controls for future divergence support:
  - match
  - offset
  - freeze
  - replay
- Do not compute divergences or alerts in this story.

### Architecture Compliance

- Preserve the current MQTT/Mosquitto decentralization path unchanged.
- Preserve the current CometBFT plus Go ABCI consensus path unchanged.
- Preserve Story 1.6 payload semantics unchanged.
- Keep SCADA simulated as an environment, but real in OPC UA implementation technology.
- Keep the service local, testable, and easy to consume in Story 3.2.

### Library / Framework Requirements

- Use a real Python OPC UA library for the server.
- Do not add FastAPI or any second SCADA stack as default scope.
- Keep any added dependency narrow and directly justified by Story 3.1.

### Testing Requirements

- Add focused deterministic tests for:
  - logical-state projection from consensused valid payload
  - offset/freeze/replay support
  - real OPC UA node exposure for temperature, pressure, and RPM
- Do not add Story 3.2 comparison tests here.

### References

- Planning artifact:
  - [epics.md](/c:/Users/emili/Desktop/Projets/parallel-truth-fingerprint-prototype/_bmad-output/planning-artifacts/epics.md)
- Split proposal source of truth:
  - [ARQUITETURA_PROPOSTA.txt](/c:/Users/emili/Desktop/Projets/parallel-truth-fingerprint-prototype/docs/input/Arquitetura%20Baseada%20em%20Fonte%20de%20Verdade%20Paralela%20para%20Gera%C3%A7%C3%A3o%20de%20Fingerprint%20F%C3%ADsico-Operacional%20em%20Sistemas%20Industriais%20Legados_ARQUITETURA_PROPOSTA.txt)
  - [METODOLOGIA_DE_PESQUISA.txt](/c:/Users/emili/Desktop/Projets/parallel-truth-fingerprint-prototype/docs/input/Arquitetura%20Baseada%20em%20Fonte%20de%20Verdade%20Paralela%20para%20Gera%C3%A7%C3%A3o%20de%20Fingerprint%20F%C3%ADsico-Operacional%20em%20Sistemas%20Industriais%20Legados_METODOLOGIA_DE_PESQUISA.txt)
  - [FUNDAMENTACAO_TEORICA.txt](/c:/Users/emili/Desktop/Projets/parallel-truth-fingerprint-prototype/docs/input/Arquitetura%20Baseada%20em%20Fonte%20de%20Verdade%20Paralela%20para%20Gera%C3%A7%C3%A3o%20de%20Fingerprint%20F%C3%ADsico-Operacional%20em%20Sistemas%20Industriais%20Legados_FUNDAMENTACAO_TEORICA.txt)

## Dev Agent Record

### Agent Model Used

GPT-5 Codex

### Debug Log References

- Story created as the first standalone Epic 3 implementation artifact.
- Story 3.1 is intentionally isolated from Story 3.2 comparison logic.

### Completion Notes List

- Story artifact created to anchor Epic 3 development in a reviewable standalone file before code changes start.
- Added a small `ScadaState` contract and a real local OPC UA service for one compressor and three sensors.
- Kept Story 3.1 scoped to logical-state projection and OPC UA exposure only.
- Added deterministic offset/freeze/replay supervisory controls without pulling Story 3.2 comparison logic forward.
- Added focused SCADA tests, including a live OPC UA server test.

### File List

- `_bmad-output/implementation-artifacts/3-1-implement-fake-opc-ua-logical-scada-service.md`
- `src/parallel_truth_fingerprint/contracts/scada_state.py`
- `src/parallel_truth_fingerprint/contracts/__init__.py`
- `src/parallel_truth_fingerprint/scada/__init__.py`
- `src/parallel_truth_fingerprint/scada/opcua_service.py`
- `tests/scada/__init__.py`
- `tests/scada/test_opcua_service.py`
- `pyproject.toml`
