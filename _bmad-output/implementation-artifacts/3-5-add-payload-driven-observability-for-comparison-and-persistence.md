# Story 3.5: Add Payload-Driven Observability for Comparison and Persistence

Status: review

<!-- Note: Validation is optional. Run validate-create-story for quality check before dev-story. -->

## Story

As a researcher,
I want logs and outputs to reflect the full payload-driven pipeline through comparison and persistence,
so that the system remains explainable and auditable during demonstration.

## Scope Notes

- This story is limited to observability and runtime output for:
  - SCADA comparison
  - SCADA divergence visibility
  - valid-artifact persistence actions
- It must build on the already implemented Story 3.1 through Story 3.4 services.
- The output must stay compact in the terminal and detailed in the JSON log file.
- Comparison or persistence blocks caused by the trust boundary must be logged explicitly.
- This story must not add:
  - new comparison rules
  - new persistence rules
  - LSTM logic
  - UI behavior

## Acceptance Criteria

1. Given edge contributions, consensus results, SCADA comparison, and persistence actions, when the prototype runs, then logs reflect those stages using the agreed payload structure and they show excluded edges, comparison outcomes, and persistence actions in a presentation-ready format.
2. Given comparison or persistence is blocked because no consensused valid state exists, when the block occurs, then the blocked flow is logged explicitly and the output makes clear that the pipeline stopped for trust-boundary reasons rather than silent failure.
3. Given the existing compact-output policy, when Story 3.5 is implemented, then the terminal output remains concise while the detailed log file captures the full structured comparison and persistence view.
4. Given focused validation, when Story 3.5 tests are run, then they prove:
   - comparison-stage logging
   - persistence-stage logging
   - blocked-stage visibility
   - deterministic MinIO bucket, artifact key, and artifact URI visibility in the demo/log flow

## Tasks / Subtasks

- [x] Extend the demo/log payload with SCADA comparison and persistence sections. (AC: 1, 2, 3, 4)
- [x] Add compact formatting for comparison and persistence stages. (AC: 1, 2, 3, 4)
- [x] Add explicit blocked-stage visibility for no-valid-state flows. (AC: 2, 4)
- [x] Add focused Story 3.5 tests and preserve full regression stability. (AC: 4)

## Dev Notes

- Story 3.5 must stay additive and observability-focused.
- It should reuse the existing Story 3.1 to Story 3.4 services rather than introducing a second runtime path.
- It must keep MinIO as the real runtime persistence path.
- Any file-backed helper must remain test-only or explicitly isolated as debug-only and must not become the effective prototype storage implementation.
- It must not alter the comparison rule, persistence gate, or downstream LSTM scope.

## Dev Agent Record

### Agent Model Used

GPT-5 Codex

### Debug Log References

- Story created from approved Epic 3 Story 3.5 wording.
- Story intentionally excludes Epic 4.

### Completion Notes List

- Story artifact created before Story 3.5 implementation begins.
- Added explicit comparison-stage and persistence-stage sections to the runtime demo log payload.
- Added compact terminal formatting for comparison and persistence stages.
- Added explicit blocked-stage visibility when no consensused valid state exists.
- Restored MinIO as the real runtime persistence target in the demo path and exposed MinIO artifact visibility in the compact and detailed outputs.
- Added focused runtime-demo tests and preserved full-suite stability.

### File List

- `_bmad-output/implementation-artifacts/3-5-add-payload-driven-observability-for-comparison-and-persistence.md`
- `src/parallel_truth_fingerprint/persistence/artifact_store.py`
- `src/parallel_truth_fingerprint/persistence/__init__.py`
- `src/parallel_truth_fingerprint/config/runtime.py`
- `scripts/run_local_demo.py`
- `tests/test_runtime_demo.py`
