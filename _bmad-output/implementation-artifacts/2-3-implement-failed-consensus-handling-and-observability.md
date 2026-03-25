# Story 2.3: Implement Failed-Consensus Handling and Consensus Observability

Status: review

<!-- Note: Validation is optional. Run validate-create-story for quality check before dev-story. -->

## Story

As a researcher,
I want consensus outcomes to be clearly visible and failed consensus to be surfaced as an explicit architectural result,
so that I can demonstrate and audit successful and failed rounds without treating failures as generic errors.

## Acceptance Criteria

1. Given any consensus round, when the engine completes, then the system emits a compact round summary including `round_id`, total participants, quorum required, valid participants after exclusions, excluded edges, exclusion reasons, and final consensus status.
2. Given a round where insufficient valid edges remain, when quorum is not satisfied, then the system surfaces `failed_consensus` explicitly in logs/output as an expected architectural outcome and it does not emit a `ConsensusedValidState` for downstream use.
3. Given successful and failed rounds during runtime/demo execution, when consensus visibility is shown, then the output makes it easy to distinguish successful consensus from failed consensus and it identifies which edges were excluded and why.
4. Given the current prototype scope, when this observability layer is implemented, then it builds on the existing `ConsensusEngine` and `ConsensusAuditPackage` only and it does not add SCADA, persistence, alert-routing, or ML logic.

## Tasks / Subtasks

- [x] Define a compact round-observability model for consensus outcomes. (AC: 1, 2, 3, 4)
  - [x] Add a simple typed summary contract or formatter output shape for round visibility.
  - [x] Include `round_id`, participant counts, quorum required, excluded edges, exclusion reasons, and final status.
  - [x] Keep the model minimal, serializable, and derived directly from `ConsensusAuditPackage`.
- [x] Implement explicit failed-consensus visibility on top of the existing engine output. (AC: 2, 4)
  - [x] Surface `failed_consensus` as an expected result, not an exception path.
  - [x] Ensure the observability output makes it explicit that no `ConsensusedValidState` exists on failed rounds.
  - [x] Preserve the existing result invariants from Story 2.2.
- [x] Add demo-friendly summary rendering for successful and failed rounds. (AC: 1, 3, 4)
  - [x] Render a compact per-round summary suitable for terminal/demo output.
  - [x] Keep excluded edge identity and typed exclusion reason visible.
  - [x] Make successful and failed rounds visually distinguishable without introducing UI complexity.
- [x] Integrate consensus summary emission into the local runtime/demo path. (AC: 1, 2, 3, 4)
  - [x] Reuse the current local runtime/demo structure and keep the integration inside the consensus/observability boundary.
  - [x] Do not introduce downstream consumers such as SCADA comparison, persistence, or LSTM.
- [x] Add focused tests for round summaries and failed-consensus visibility. (AC: 1, 2, 3, 4)
  - [x] Verify compact summaries include the required round fields.
  - [x] Verify failed-consensus summaries show the failed status and absence of valid state.
  - [x] Verify exclusion identity and reasons are preserved in the observable output.
  - [x] Verify successful rounds remain distinguishable from failed rounds.

## Dev Notes

- This story builds directly on Story 2.2. Do not modify the core consensus algorithm unless required to expose already-produced results cleanly. [Source: [2-2-implement-byzantine-style-consensus-evaluation.md](/c:/Users/emili/Desktop/Projets/parallel-truth-fingerprint-prototype/_bmad-output/implementation-artifacts/2-2-implement-byzantine-style-consensus-evaluation.md)]
- Story 2.2 already produces:
  - explicit quorum enforcement
  - explicit `failed_consensus`
  - `ConsensusResult`
  - `ConsensusAuditPackage`
  Story 2.3 should expose these outcomes clearly, not redesign them.
- Failed consensus must remain an expected architectural outcome, not an exception. The observability layer should make that visible in logs/output and keep it suitable for demonstration and audit.
- The compact round summary must include:
  - `round_id`
  - total participants
  - quorum required
  - valid participants after exclusions
  - excluded edges
  - exclusion reasons
  - final consensus status
- Demo/runtime visibility must make it easy to see:
  - successful rounds
  - failed rounds
  - which edges were excluded
  - why they were excluded
- Do not add SCADA, comparison, persistence, alert-routing, or ML logic in this story. Alerts remain Story 2.5. Structured logging depth can expand further in Story 2.4 if needed, but this story must provide a usable compact observability layer now.

### Project Structure Notes

- Primary implementation areas:
  - `src/parallel_truth_fingerprint/consensus/`
  - `src/parallel_truth_fingerprint/contracts/`
  - `scripts/`
  - `tests/consensus/`
- Supporting areas if directly needed:
  - current demo/runtime helpers
  - existing consensus audit package and result contracts
- Do not touch:
  - `scada/`
  - `comparison/`
  - `persistence/`
  - `lstm_service/`
- Keep the implementation localized to consensus observability and demo visibility.

### Technical Requirements

- Reuse `ConsensusAuditPackage` as the source of truth for round observability.
- Emit a compact summary for every round containing:
  - `round_id`
  - participant count
  - quorum required
  - valid participant count after exclusions
  - excluded edge ids
  - exclusion reasons
  - final status
- Failed-consensus visibility must:
  - show `failed_consensus` explicitly
  - show exclusions and reasons when present
  - make absence of `ConsensusedValidState` explicit
- Successful consensus visibility must remain compact and clearly distinct from failed consensus.
- Keep output deterministic and reproducible for the same input.

### Architecture Compliance

- No central authority may be introduced.
- No SCADA or comparison logic may appear in this story.
- No persistence or ML logic may appear in this story.
- No new trust semantics may be added beyond what Story 2.2 already defines.
- Observability must remain derived from edge-local consensus execution outputs.

### Library / Framework Requirements

- Stay within the current local Python project structure.
- Use standard-library Python only unless an existing project dependency is clearly required.
- Do not add any new logging, UI, or visualization framework in this story.

### File Structure Requirements

- Prefer adding files such as:
  - `src/parallel_truth_fingerprint/contracts/consensus_round_summary.py`
  - `src/parallel_truth_fingerprint/consensus/summary.py`
  - focused updates to `scripts/run_local_demo.py` only if needed for consensus demo output
- Keep names aligned with the approved architecture and current consensus terminology.

### Testing Requirements

- Add focused observability tests only.
- Validate:
  - compact round summary contents
  - explicit failed-consensus visibility
  - exclusion identity and reason visibility
  - success/failure distinction in output
- Do not write tests for SCADA, persistence, or LSTM in this story.

### Previous Story Intelligence

- Story 2.1 defined the consensus contracts and trust-state boundaries.
- Story 2.2 implemented:
  - deterministic trust evaluation
  - quorum enforcement
  - failed-consensus handling
  - `ConsensusAuditPackage`
- Story 2.3 should expose those outputs cleanly for demo and audit without changing their architectural meaning.

### Git Intelligence Summary

- Most recent commit titles:
  - `Story 1.5 MQTT`
  - `Stroy 1.3 and 1.4`
  - `Stroy 1.2`
- The repo now has working consensus execution. The next increment is visibility and explicit failed-consensus surfacing, not new decision logic.

### References

- Story definition and acceptance criteria: [epics.md](/c:/Users/emili/Desktop/Projets/parallel-truth-fingerprint-prototype/_bmad-output/planning-artifacts/epics.md#L301)
- Consensus engine and audit package: [2-2-implement-byzantine-style-consensus-evaluation.md](/c:/Users/emili/Desktop/Projets/parallel-truth-fingerprint-prototype/_bmad-output/implementation-artifacts/2-2-implement-byzantine-style-consensus-evaluation.md)
- Auditability requirements: [architecture.md](/c:/Users/emili/Desktop/Projets/parallel-truth-fingerprint-prototype/_bmad-output/planning-artifacts/architecture.md#L37)

## Dev Agent Record

### Agent Model Used

GPT-5 Codex

### Debug Log References

- Story created from Epic 2, Story 2.3 with explicit failed-consensus visibility and demo-summary constraints from the user.
- No sprint-status file exists yet.
- Story 2.2 implementation was used as the direct architectural baseline.
- `venv\\Scripts\\python -m unittest tests.consensus.test_summary`
- `venv\\Scripts\\python -m unittest discover -s tests`

### Completion Notes List

- Ultimate context engine analysis completed - comprehensive developer guide created.
- Added a structured `ConsensusRoundSummary` contract and deterministic serialization path derived directly from `ConsensusAuditPackage`.
- Added deterministic consensus summary formatting that keeps failed consensus explicit and preserves excluded edge identity and typed exclusion reasons.
- Added typed export of edge-local replicated state for consensus/demo wiring without changing the consensus engine semantics.
- Integrated compact consensus summary output into the local demo path on top of the existing engine.
- Added focused tests for structured summary contents, failed-consensus visibility, serialization stability, and demo formatting.

### File List

- `_bmad-output/implementation-artifacts/2-3-implement-failed-consensus-handling-and-observability.md`
- `src/parallel_truth_fingerprint/contracts/consensus_round_summary.py`
- `src/parallel_truth_fingerprint/contracts/__init__.py`
- `src/parallel_truth_fingerprint/consensus/summary.py`
- `src/parallel_truth_fingerprint/consensus/__init__.py`
- `src/parallel_truth_fingerprint/edge_nodes/common/acquisition.py`
- `scripts/run_local_demo.py`
- `tests/consensus/test_summary.py`
- `tests/test_runtime_demo.py`

### Change Log

- 2026-03-25: Implemented Story 2.3 structured round summaries, deterministic failed-consensus visibility, and demo integration.
