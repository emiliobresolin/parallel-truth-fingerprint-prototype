# Story 2.4: Add Consensus Round Logging and Exclusion Visibility

Status: review

<!-- Note: Validation is optional. Run validate-create-story for quality check before dev-story. -->

## Story

As a researcher,
I want each consensus round to be fully traceable in logs and outputs,
so that I can explain which edges participated, which were excluded, why the trust decision was made, and what score or deviation triggered that decision.

## Acceptance Criteria

1. Given any consensus round, when the round is executed, then structured logs capture the round identifier, participating edges, trust ranking, excluded edges, exclusion reasons, and round success or failure status and the logs remain clear enough for academic demonstration and evaluation.
2. Given a suspicious-edge or inconsistent-view exclusion, when the exclusion is logged or displayed, then the output identifies exactly which edge was excluded, records the typed exclusion reason, and includes the scoring or deviation metric used to justify that exclusion.
3. Given the existing deterministic trust evaluation, when round observability is emitted, then the audit trail includes the score and per-sensor deviation information used by the trust model for each participating edge in that round.
4. Given the current prototype scope, when consensus logging is implemented, then it builds only on the existing consensus engine, trust model, summary model, and audit package and it does not add SCADA, persistence, alert-routing, or ML logic.
5. Given demo/runtime execution, when consensus logs are shown, then the output remains readable and demo-friendly while preserving the underlying structured data for traceability.

## Tasks / Subtasks

- [x] Define structured consensus log models for traceability. (AC: 1, 2, 3, 4, 5)
  - [x] Add a structured round-log contract derived from `ConsensusAuditPackage`.
  - [x] Add a per-edge trust-evaluation structure that includes trust score and per-sensor deviation metrics.
  - [x] Keep the contracts serializable, deterministic, and separate from human-readable formatting.
- [x] Extend the trust evaluation output so exclusion evidence is traceable per edge. (AC: 2, 3, 4)
  - [x] Expose the score and deviation metrics used by the current deterministic trust model.
  - [x] Keep exclusion reasons explicit and bounded.
  - [x] Preserve current deterministic behavior and do not redesign the exclusion algorithm.
- [x] Implement structured consensus-round logging on top of the current engine output. (AC: 1, 2, 3, 4)
  - [x] Emit one structured round log package per executed round.
  - [x] Include round identity, participants, trust ranking, exclusion decisions, score/deviation evidence, final status, and consensused valid state when present.
  - [x] Keep failed-consensus and successful rounds equally traceable.
- [x] Add demo-friendly rendering for structured consensus logs. (AC: 1, 2, 5)
  - [x] Render a readable round log view suitable for terminal/demo output.
  - [x] Keep excluded edge identity, typed reason, and the relevant score/deviation evidence visible.
  - [x] Preserve the structured log object as the source of truth behind the rendering.
- [x] Integrate round log emission into the local demo/runtime path. (AC: 1, 4, 5)
  - [x] Reuse the existing demo path without introducing downstream consumers.
  - [x] Keep the output compact enough for presentation while allowing inspection of the full structured log.
- [x] Add focused tests for round-log structure and exclusion evidence visibility. (AC: 1, 2, 3, 4, 5)
  - [x] Verify structured logs include all required round fields.
  - [x] Verify per-edge score and deviation data are present and deterministic.
  - [x] Verify excluded edges always include typed reason plus supporting evidence.
  - [x] Verify demo formatting remains readable while preserving underlying structure.

## Dev Notes

- This story builds directly on Story 2.3. Do not redesign the consensus engine or trust semantics. [Source: [2-3-implement-failed-consensus-handling-and-observability.md](/c:/Users/emili/Desktop/Projets/parallel-truth-fingerprint-prototype/_bmad-output/implementation-artifacts/2-3-implement-failed-consensus-handling-and-observability.md)]
- Story 2.2 already provides deterministic trust evaluation and exclusions. Story 2.4 must make those decisions more traceable by exposing the score and deviation evidence that already drives the outcome.
- Exclusion reasons must remain explicit and traceable per edge.
- Any score or deviation metric used for exclusion must be included in the audit/log trail.
- Output must remain demo-friendly and readable, but the structured object must remain the source of truth.
- Do not add SCADA, comparison, persistence, alert-routing, or ML logic in this story. Alerts remain Story 2.5.

### Project Structure Notes

- Primary implementation areas:
  - `src/parallel_truth_fingerprint/consensus/`
  - `src/parallel_truth_fingerprint/contracts/`
  - `scripts/`
  - `tests/consensus/`
- Supporting areas if directly needed:
  - existing trust model
  - existing audit package
  - current demo/runtime helpers
- Do not touch:
  - `scada/`
  - `comparison/`
  - `persistence/`
  - `lstm_service/`
- Keep the work confined to consensus observability and traceability.

### Technical Requirements

- Emit structured round logs that include:
  - round identity
  - participating edges
  - trust ranking
  - excluded edges
  - exclusion reasons
  - final status
  - consensused valid state when present
- Include per-edge trust evidence in the log trail:
  - trust score
  - per-sensor deviation metrics used by the deterministic trust model
- Excluded-edge visibility must include:
  - edge id
  - typed exclusion reason
  - supporting score or deviation evidence
- Keep the structured data deterministic for the same input.
- Keep human-readable formatting separate from the structured log model.

### Architecture Compliance

- No central authority may be introduced.
- No SCADA or comparison logic may appear in this story.
- No persistence, alert-routing, or ML logic may appear in this story.
- Observability must remain derived from edge-local consensus execution outputs and existing audit objects.
- No new trust semantics may be introduced beyond the current deterministic trust model.

### Library / Framework Requirements

- Stay within the current local Python project structure.
- Use standard-library Python only unless an existing project dependency is clearly required.
- Do not add any new logging, UI, or visualization framework in this story.

### File Structure Requirements

- Prefer adding files such as:
  - `src/parallel_truth_fingerprint/contracts/consensus_round_log.py`
  - `src/parallel_truth_fingerprint/consensus/logging.py`
  - focused updates to `src/parallel_truth_fingerprint/consensus/trust_model.py`
  - focused updates to `scripts/run_local_demo.py`
- Keep names aligned with the approved architecture and current consensus terminology.

### Testing Requirements

- Add focused consensus observability tests only.
- Validate:
  - structured round-log contents
  - per-edge trust score and deviation visibility
  - explicit exclusion evidence
  - readable demo formatting backed by structured data
- Do not write tests for SCADA, persistence, alerts, or LSTM in this story.

### Previous Story Intelligence

- Story 2.1 defined the consensus contracts and trust-state boundaries.
- Story 2.2 implemented deterministic consensus execution and the audit package.
- Story 2.3 added structured compact summaries and demo-facing failed-consensus visibility.
- Story 2.4 should deepen traceability by logging the trust evidence behind exclusions, not alter the consensus decision path.

### Git Intelligence Summary

- Most recent commit titles:
  - `Story 1.5 MQTT`
  - `Stroy 1.3 and 1.4`
  - `Stroy 1.2`
- The repo already has working consensus execution and compact summaries. The next increment is full traceability of trust evidence and exclusion rationale.

### References

- Story definition and acceptance criteria: [epics.md](/c:/Users/emili/Desktop/Projets/parallel-truth-fingerprint-prototype/_bmad-output/planning-artifacts/epics.md#L314)
- Consensus execution baseline: [2-2-implement-byzantine-style-consensus-evaluation.md](/c:/Users/emili/Desktop/Projets/parallel-truth-fingerprint-prototype/_bmad-output/implementation-artifacts/2-2-implement-byzantine-style-consensus-evaluation.md)
- Consensus observability baseline: [2-3-implement-failed-consensus-handling-and-observability.md](/c:/Users/emili/Desktop/Projets/parallel-truth-fingerprint-prototype/_bmad-output/implementation-artifacts/2-3-implement-failed-consensus-handling-and-observability.md)
- Auditability requirements: [architecture.md](/c:/Users/emili/Desktop/Projets/parallel-truth-fingerprint-prototype/_bmad-output/planning-artifacts/architecture.md#L37)

## Dev Agent Record

### Agent Model Used

GPT-5 Codex

### Debug Log References

- Story created from Epic 2, Story 2.4 with explicit traceability requirements for exclusion reasons, scores, and deviation metrics.
- No sprint-status file exists yet.
- Stories 2.2 and 2.3 were used as the direct implementation baseline.
- `venv\\Scripts\\python -m unittest tests.consensus.test_logging`
- `venv\\Scripts\\python -m unittest discover -s tests`

### Completion Notes List

- Ultimate context engine analysis completed - comprehensive developer guide created.
- Added structured per-edge trust evidence with explicit numeric deviation values and units, derived directly from the existing deterministic trust model.
- Extended `ConsensusAuditPackage` to carry trust evidence so round logging can be built without recomputing any values.
- Added a structured `ConsensusRoundLog` plus compact and detailed deterministic renderers, with the structured log kept as the single source of truth.
- Integrated the structured round log into the local demo path while preserving compact and detailed demo readability.
- Added focused tests for round-log contents, exclusion evidence visibility, deterministic serialization, and demo formatting.

### File List

- `_bmad-output/implementation-artifacts/2-4-add-consensus-round-logging-and-exclusion-visibility.md`
- `src/parallel_truth_fingerprint/contracts/trust_evidence.py`
- `src/parallel_truth_fingerprint/contracts/consensus_round_log.py`
- `src/parallel_truth_fingerprint/contracts/consensus_audit_package.py`
- `src/parallel_truth_fingerprint/contracts/__init__.py`
- `src/parallel_truth_fingerprint/consensus/trust_model.py`
- `src/parallel_truth_fingerprint/consensus/engine.py`
- `src/parallel_truth_fingerprint/consensus/logging.py`
- `src/parallel_truth_fingerprint/consensus/__init__.py`
- `scripts/run_local_demo.py`
- `tests/consensus/test_logging.py`
- `tests/test_runtime_demo.py`

### Change Log

- 2026-03-25: Implemented Story 2.4 structured round logging, explicit per-edge trust evidence, and demo-friendly compact/detailed round-log output.
