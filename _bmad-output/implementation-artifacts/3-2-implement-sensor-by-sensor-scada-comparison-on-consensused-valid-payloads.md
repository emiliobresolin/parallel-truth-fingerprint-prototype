# Story 3.2: Implement Sensor-by-Sensor SCADA Comparison on Consensused Valid Payloads

Status: review

<!-- Note: Validation is optional. Run validate-create-story for quality check before dev-story. -->

## Story

As a researcher,
I want SCADA comparison to use simple sensor-by-sensor configurable tolerance as the core behavior,
so that divergence is evaluated in a defensible, explainable, and prototype-scaled way.

## Scope Notes

- This story is limited to sensor-by-sensor comparison between the consensused physical-side state and the logical SCADA-side state.
- The current implementation truth is:
  - physical-side input comes from `ConsensusedValidState`
  - logical-side input comes from the fake OPC UA SCADA projection represented by `ScadaState`
- Configurable tolerance is the core decision rule.
- Optional contextual evidence may be attached when helpful, but it must not replace the tolerance rule.
- This story must not add:
  - SCADA divergence alerts
  - persistence logic
  - fingerprint or anomaly logic
  - demo UI behavior
- This story should remain additive and must not redesign MQTT, CometBFT, Story 1.6 acquisition semantics, or Story 3.1 fake OPC UA service.

## Acceptance Criteria

1. Given a consensused valid payload and current SCADA state, when the comparison service executes, then it compares temperature, pressure, and RPM sensor by sensor using configurable tolerance against the current SCADA values.
2. Given the approved scope guardrails, when comparison logic is implemented, then configurable tolerance remains the core decision rule and optional contextual evidence does not replace that core rule.
3. Given no consensused valid state exists, when comparison would otherwise run, then the comparison service remains blocked and it does not execute against edge-local replicated intermediate state or invalid consensus output.
4. Given a comparison result, when it is returned for later stories, then it remains typed, deterministic, and suitable for downstream Story 3.3 alert/output work without forcing that later scope into Story 3.2.
5. Given focused tests, when Story 3.2 is validated, then the tests prove:
   - within-tolerance matching behavior
   - out-of-tolerance divergence behavior
   - optional contextual evidence attachment
   - blocked behavior when no valid state exists

## Tasks / Subtasks

- [x] Add minimal typed comparison contracts. (AC: 1, 2, 4, 5)
  - [x] Define a per-sensor comparison decision model.
  - [x] Define a round-scoped comparison result model.
  - [x] Keep the model small and Story 3.3-ready.
- [x] Implement the comparison service. (AC: 1, 2, 3, 4, 5)
  - [x] Accept `ConsensusedValidState` and `ScadaState`.
  - [x] Apply configurable tolerance by sensor.
  - [x] Block execution if no valid state is provided.
  - [x] Keep optional contextual evidence additive only.
- [x] Add focused Story 3.2 tests. (AC: 1, 2, 3, 4, 5)
  - [x] Verify matching values inside tolerance.
  - [x] Verify divergence outside tolerance.
  - [x] Verify contextual evidence is attached but not decision-driving.
  - [x] Verify blocked behavior without `ConsensusedValidState`.

## Dev Notes

- Story 3.2 builds directly on Story 3.1 and must consume the current `ScadaState` boundary rather than inventing a second logical-state model. [Source: [3-1-implement-fake-opc-ua-logical-scada-service.md](/c:/Users/emili/Desktop/Projets/parallel-truth-fingerprint-prototype/_bmad-output/implementation-artifacts/3-1-implement-fake-opc-ua-logical-scada-service.md)]
- The split proposal files in `docs/input/` remain the research source of truth.
- This story must stay academically honest:
  - real comparison logic in Python
  - simulated SCADA environment through the Story 3.1 fake OPC UA service
- Do not introduce alerts here. Alerts belong to Story 3.3.
- Do not introduce persistence here. Persistence belongs to Story 3.4.

### Project Structure Notes

- Primary implementation areas:
  - `src/parallel_truth_fingerprint/comparison/`
  - `src/parallel_truth_fingerprint/contracts/`
  - `tests/comparison/`
- Supporting areas if directly needed:
  - `src/parallel_truth_fingerprint/contracts/consensused_valid_state.py`
  - `src/parallel_truth_fingerprint/contracts/scada_state.py`
- Do not redesign:
  - `src/parallel_truth_fingerprint/scada/`
  - `src/parallel_truth_fingerprint/consensus/`
  - `src/parallel_truth_fingerprint/persistence/`
  - `src/parallel_truth_fingerprint/lstm_service/`

### Technical Requirements

- Compare only:
  - temperature
  - pressure
  - rpm
- Use configurable tolerance by sensor as the only decision rule.
- Allow optional contextual evidence to be attached without affecting the rule.
- Block comparison if there is no valid consensus output.
- Keep the result deterministic and round-scoped.

### Testing Requirements

- Add focused deterministic tests for:
  - within-tolerance results
  - divergence results
  - evidence attachment
  - blocked execution without a valid state
- Do not add alert or persistence tests here.

## Dev Agent Record

### Agent Model Used

GPT-5 Codex

### Debug Log References

- Story created from the approved Epic 3 Story 3.2 planning wording.
- Story intentionally excludes Story 3.3 alert generation.

### Completion Notes List

- Story artifact created before Story 3.2 implementation begins.
- Added a small typed comparison result model with per-sensor tolerance outcomes.
- Implemented configurable sensor-by-sensor comparison over `ConsensusedValidState` and `ScadaState`.
- Kept optional contextual evidence additive only and out of the decision rule.
- Kept alert generation, persistence, and later fingerprint logic out of Story 3.2.
- Added focused comparison tests and preserved full-suite stability.

### File List

- `_bmad-output/implementation-artifacts/3-2-implement-sensor-by-sensor-scada-comparison-on-consensused-valid-payloads.md`
- `src/parallel_truth_fingerprint/contracts/scada_comparison.py`
- `src/parallel_truth_fingerprint/contracts/__init__.py`
- `src/parallel_truth_fingerprint/comparison/__init__.py`
- `src/parallel_truth_fingerprint/comparison/service.py`
- `tests/comparison/__init__.py`
- `tests/comparison/test_service.py`
