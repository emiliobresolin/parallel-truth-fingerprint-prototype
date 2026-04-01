# Story 3.4: Persist Structured Consensus Artifacts Only for Valid States

Status: review

<!-- Note: Validation is optional. Run validate-create-story for quality check before dev-story. -->

## Story

As a researcher,
I want valid structured consensus artifacts persisted in local storage,
so that downstream training and audit evidence use only validated data.

## Scope Notes

- This story is limited to valid-artifact persistence only.
- It must persist the validated structured artifact produced after:
  - successful consensus
  - SCADA comparison output
- It must block persistence for:
  - failed consensus
  - missing `ConsensusedValidState`
  - any pre-consensus or non-validated intermediate state
- The persistence target must follow the approved local object-storage direction and remain ready for local MinIO usage.
- This story must not add:
  - new comparison logic
  - new alert logic
  - LSTM training/inference
  - demo UI behavior
  - Story 3.5 observability wiring

## Acceptance Criteria

1. Given a successful consensus outcome, when persistence executes, then the stored artifact includes at least timestamp, consensus_state based on the unified payload, trust_scores, excluded_edges, SCADA comparison results, and diagnostics.
2. Given a successful valid state, when it is persisted, then the artifact is written only for valid consensused states.
3. Given a failed consensus outcome, any edge-local replicated intermediate state, or other non-validated data, when persistence would otherwise execute, then the system blocks persistence of that data as valid artifact and invalid or pre-consensus data does not enter the training-ready storage path.
4. Given the approved architecture direction, when Story 3.4 is implemented, then the persistence boundary remains compatible with local object storage and does not redesign upstream comparison or downstream LSTM scope.
5. Given focused validation, when Story 3.4 tests are run, then they prove:
   - valid artifact persistence content
   - blocked persistence on invalid rounds
   - deterministic object naming and serialization
   - object-store compatibility for later local MinIO runtime use

## Tasks / Subtasks

- [x] Add a typed persisted-artifact contract. (AC: 1, 2, 5)
  - [x] Define the valid persisted artifact structure.
  - [x] Keep the artifact deterministic and serializable.
- [x] Add an object-store adapter aligned to local MinIO usage. (AC: 4, 5)
  - [x] Implement a small store adapter for JSON artifact writes.
  - [x] Keep the runtime dependency narrow and local-object-store oriented.
- [x] Implement the valid-state persistence service. (AC: 1, 2, 3, 4, 5)
  - [x] Accept the current consensus and SCADA comparison outputs.
  - [x] Persist only successful valid artifacts.
  - [x] Block invalid or pre-consensus inputs.
- [x] Add focused Story 3.4 tests. (AC: 1, 2, 3, 4, 5)
  - [x] Verify persisted content.
  - [x] Verify blocked invalid persistence.
  - [x] Verify deterministic object naming.
  - [x] Verify object-store compatibility behavior.

## Dev Notes

- Story 3.4 builds on the current implementation truth:
  - real CometBFT plus Go ABCI consensus
  - fake OPC UA SCADA state
  - Story 3.2 comparison
  - Story 3.3 structured outputs and divergence alert path
- This story persists valid artifacts only. It does not redesign the pipeline.
- Keep the persistence boundary object-store oriented and ready for local MinIO use.
- Do not pull LSTM logic into this story.

## Dev Agent Record

### Agent Model Used

GPT-5 Codex

### Debug Log References

- Story created from approved Epic 3 Story 3.4 wording.
- Story intentionally excludes Story 3.5 observability wiring and Epic 4 behavior.

### Completion Notes List

- Story artifact created before Story 3.4 implementation begins.
- Added a typed persisted-artifact contract for valid downstream records only.
- Added a small MinIO-oriented JSON artifact store adapter with lazy runtime dependency loading.
- Implemented valid-state persistence with a hard block on failed or missing-valid-state rounds.
- Added focused persistence tests and preserved full-suite stability.

### File List

- `_bmad-output/implementation-artifacts/3-4-persist-structured-consensus-artifacts-only-for-valid-states.md`
- `src/parallel_truth_fingerprint/contracts/persistence_record.py`
- `src/parallel_truth_fingerprint/contracts/__init__.py`
- `src/parallel_truth_fingerprint/persistence/__init__.py`
- `src/parallel_truth_fingerprint/persistence/artifact_store.py`
- `src/parallel_truth_fingerprint/persistence/service.py`
- `tests/persistence/__init__.py`
- `tests/persistence/test_service.py`
- `pyproject.toml`
