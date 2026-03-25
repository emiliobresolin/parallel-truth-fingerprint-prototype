# Story 2.5: Generate Consensus Failure Alerts

Status: review

<!-- Note: Validation is optional. Run validate-create-story for quality check before dev-story. -->

## Story

As a researcher,
I want explicit alerts when consensus fails,
so that critical trust-breakdown conditions are visible during demonstration and evaluation.

## Acceptance Criteria

1. Given a consensus failure caused by loss of quorum, when the round completes, then the system generates a consensus-related alert and that alert remains distinct from future SCADA divergence and LSTM anomaly alerts.
2. Given a consensus-related alert, when it is emitted, then it references the associated round outcome, excluded edges, typed exclusion reasons, and supporting trust evidence and it does not bypass the normal consensus execution path.
3. Given the existing consensus observability layer, when alerts are generated, then they are derived directly from the current `ConsensusAuditPackage` and `ConsensusRoundLog` outputs without recomputing trust or exclusion decisions.
4. Given demo/runtime execution, when consensus-related alerts are shown, then the output remains readable and clearly distinguishes:
   - failed consensus
   - ordinary successful rounds with no consensus alert
5. Given the current prototype scope, when this alert layer is implemented, then it adds only consensus-specific alerting and it does not add SCADA, persistence, or ML logic.

## Tasks / Subtasks

- [x] Define structured consensus alert contracts. (AC: 1, 2, 3, 4, 5)
  - [x] Add a typed consensus alert model with a bounded alert category specific to consensus.
  - [x] Include round identity, final status, excluded edges, typed reasons, and supporting trust evidence references.
  - [x] Keep the model deterministic, serializable, and separate from human-readable rendering.
- [x] Implement alert generation from existing consensus outputs only. (AC: 1, 2, 3, 5)
  - [x] Derive alerts from `ConsensusAuditPackage` and `ConsensusRoundLog`.
  - [x] Do not recompute trust ranking, exclusions, or status during alert generation.
  - [x] Generate alerts only for `failed_consensus`.
- [x] Keep alert categories distinct from future downstream paths. (AC: 1, 5)
  - [x] Ensure the alert contract and formatter are clearly consensus-specific.
  - [x] Avoid any coupling to SCADA divergence or LSTM anomaly terminology.
- [x] Add demo-friendly rendering for consensus alerts. (AC: 2, 4, 5)
  - [x] Render readable alert output for terminal/demo use.
  - [x] Keep the alert output clearly tied to the associated round and exclusion context.
  - [x] Make no-alert successful rounds distinguishable from alerting rounds.
- [x] Integrate consensus alert emission into the local demo/runtime path. (AC: 1, 4, 5)
  - [x] Reuse the existing consensus engine, summary, and round-log path.
  - [x] Keep integration local and lightweight without introducing downstream consumers.
- [x] Add focused tests for consensus alert conditions and formatting. (AC: 1, 2, 3, 4, 5)
  - [x] Verify `failed_consensus` produces a consensus alert.
  - [x] Verify ordinary successful rounds do not emit a consensus alert.
  - [x] Verify emitted alerts include round outcome, exclusion context, and supporting evidence.
  - [x] Verify formatting remains readable and deterministic.

## Dev Notes

- This story builds directly on Stories 2.2, 2.3, and 2.4. Do not redesign the consensus engine, trust semantics, or round-log structure. [Source: [2-4-add-consensus-round-logging-and-exclusion-visibility.md](/c:/Users/emili/Desktop/Projets/parallel-truth-fingerprint-prototype/_bmad-output/implementation-artifacts/2-4-add-consensus-round-logging-and-exclusion-visibility.md)]
- Alerts in this story are consensus-specific only.
- Alert generation must be strictly derived from existing consensus outputs:
  - `ConsensusAuditPackage`
  - `ConsensusRoundLog`
- Do not recompute trust decisions or exclusions in the alert layer.
- The alert output must stay distinct from future:
  - SCADA divergence alerts
  - LSTM anomaly alerts
- The only alert condition in this prototype is `failed_consensus`, meaning quorum was lost.
- The story must remain local, deterministic, and demo-friendly.
- Do not add SCADA, comparison, persistence, or ML logic here.

### Project Structure Notes

- Primary implementation areas:
  - `src/parallel_truth_fingerprint/consensus/`
  - `src/parallel_truth_fingerprint/contracts/`
  - `scripts/`
  - `tests/consensus/`
- Supporting areas if directly needed:
  - existing audit package
  - existing round log
  - current demo/runtime helpers
- Do not touch:
  - `scada/`
  - `comparison/`
  - `persistence/`
  - `lstm_service/`
- Keep the work confined to consensus alert generation and presentation.

### Technical Requirements

- Add structured consensus alerting only for:
  - `failed_consensus`
- Alert data must include:
  - round identity
  - final consensus status
  - excluded edges
  - typed exclusion reasons
  - supporting trust evidence references or embedded evidence needed for demonstration
- Alert generation must be deterministic for the same input.
- Human-readable rendering must be separate from the structured alert object.
- Successful no-alert rounds must remain observable but should not produce consensus alerts.

### Architecture Compliance

- No central authority may be introduced.
- No SCADA or comparison logic may appear in this story.
- No persistence or ML logic may appear in this story.
- No alert routing beyond local consensus-specific alert generation may be introduced.
- Alert generation must remain downstream of, and derived from, existing consensus execution outputs.

### Library / Framework Requirements

- Stay within the current local Python project structure.
- Use standard-library Python only unless an existing project dependency is clearly required.
- Do not add any new alerting, logging, UI, or visualization framework in this story.

### File Structure Requirements

- Prefer adding files such as:
  - `src/parallel_truth_fingerprint/contracts/consensus_alert.py`
  - `src/parallel_truth_fingerprint/consensus/alerts.py`
  - focused updates to `scripts/run_local_demo.py`
- Keep names aligned with the approved architecture and current consensus terminology.

### Testing Requirements

- Add focused consensus alert tests only.
- Validate:
  - failed-consensus alert emission
  - no alert for ordinary successful rounds
  - alert payload traceability
  - readable deterministic formatting
- Do not write tests for SCADA, persistence, or LSTM in this story.

### Previous Story Intelligence

- Story 2.2 implemented deterministic consensus execution and the audit package.
- Story 2.3 added structured compact summaries and failed-consensus visibility.
- Story 2.4 added structured round logs and per-edge trust evidence.
- Story 2.5 should add failed-consensus alerting on top of those outputs, not alter the decision path.

### Git Intelligence Summary

- Most recent commit titles:
  - `Story 1.5 MQTT`
  - `Stroy 1.3 and 1.4`
  - `Stroy 1.2`
- The repo already has deterministic consensus execution plus traceable observability. The next increment is an explicit failed-consensus alert for quorum-loss conditions.

### References

- Story definition and acceptance criteria: [epics.md](/c:/Users/emili/Desktop/Projets/parallel-truth-fingerprint-prototype/_bmad-output/planning-artifacts/epics.md#L329)
- Consensus execution baseline: [2-2-implement-byzantine-style-consensus-evaluation.md](/c:/Users/emili/Desktop/Projets/parallel-truth-fingerprint-prototype/_bmad-output/implementation-artifacts/2-2-implement-byzantine-style-consensus-evaluation.md)
- Consensus observability baseline: [2-3-implement-failed-consensus-handling-and-observability.md](/c:/Users/emili/Desktop/Projets/parallel-truth-fingerprint-prototype/_bmad-output/implementation-artifacts/2-3-implement-failed-consensus-handling-and-observability.md)
- Consensus logging baseline: [2-4-add-consensus-round-logging-and-exclusion-visibility.md](/c:/Users/emili/Desktop/Projets/parallel-truth-fingerprint-prototype/_bmad-output/implementation-artifacts/2-4-add-consensus-round-logging-and-exclusion-visibility.md)
- Auditability requirements: [architecture.md](/c:/Users/emili/Desktop/Projets/parallel-truth-fingerprint-prototype/_bmad-output/planning-artifacts/architecture.md#L37)

## Dev Agent Record

### Agent Model Used

GPT-5 Codex

### Debug Log References

- Story created from Epic 2, Story 2.5 with explicit consensus-alert scope and traceability constraints.
- No sprint-status file exists yet.
- Stories 2.2, 2.3, and 2.4 were used as the direct implementation baseline.

### Completion Notes List

- Ultimate context engine analysis completed - comprehensive developer guide created.
- Added a bounded consensus-specific alert contract with a single alert type: `CONSENSUS_FAILED`.
- Implemented alert generation strictly from `ConsensusAuditPackage` and `ConsensusRoundLog` with no recomputation of trust, exclusions, or status.
- Kept the alert trigger strictly aligned to architecture: alert only when final status is `failed_consensus`.
- Integrated compact and detailed alert rendering into the local demo path while preserving `no alert` visibility for successful rounds.
- Added focused tests for failed-consensus alert emission, no-alert successful rounds, traceable evidence payloads, and deterministic formatting.

### File List

- `_bmad-output/implementation-artifacts/2-5-generate-consensus-failure-and-multi-invalid-edge-alerts.md`
- `src/parallel_truth_fingerprint/contracts/consensus_alert.py`
- `src/parallel_truth_fingerprint/contracts/__init__.py`
- `src/parallel_truth_fingerprint/consensus/alerts.py`
- `src/parallel_truth_fingerprint/consensus/__init__.py`
- `scripts/run_local_demo.py`
- `tests/consensus/test_alerts.py`
- `tests/test_runtime_demo.py`

### Change Log

- 2026-03-25: Implemented Story 2.5 failed-consensus alert generation and demo-friendly alert visibility.
