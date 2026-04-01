# Story 3.3: Produce Structured Per-Sensor SCADA Comparison Outputs and Alerts

Status: review

<!-- Note: Validation is optional. Run validate-create-story for quality check before dev-story. -->

## Story

As a researcher,
I want structured comparison outputs for each sensor,
so that SCADA divergence can be explained clearly and remain separate from other alert paths.

## Scope Notes

- This story is limited to structured output and alert generation on top of the Story 3.2 comparison result.
- It must build on the existing `ScadaComparisonResult` rather than replacing Story 3.2 comparison logic.
- The output must remain per-sensor and explainable.
- SCADA divergence alerts must remain distinct from:
  - consensus failure alerts
  - future LSTM anomaly alerts
- This story must not add:
  - persistence logic
  - fingerprint logic
  - demo UI behavior
  - new comparison rules beyond Story 3.2 tolerance evaluation

## Acceptance Criteria

1. Given a comparison between consensused valid payloads and SCADA values, when the comparison completes, then the output for each sensor includes the consensused physical value, the SCADA value, the tolerance-based evaluation, optional contextual evidence when present, and a divergence classification.
2. Given the approved architecture constraints, when the output format is produced, then it remains consistent with the unified payload-driven design and does not introduce a second comparison model.
3. Given divergence is detected, when an alert is emitted, then the system generates a SCADA divergence alert as a separate alert path and it remains distinct from consensus failure alerts and LSTM anomaly alerts.
4. Given no divergence is detected, when the alert builder is executed, then no SCADA divergence alert is emitted.
5. Given focused validation, when Story 3.3 tests are run, then they prove:
   - per-sensor structured output content
   - divergence classification
   - distinct SCADA alert generation only when needed
   - deterministic readable formatting

## Tasks / Subtasks

- [x] Add structured SCADA comparison output contracts. (AC: 1, 2, 5)
  - [x] Define per-sensor output with divergence classification.
  - [x] Define a round-scoped structured comparison output.
  - [x] Keep it additive on top of Story 3.2 contracts.
- [x] Add SCADA divergence alert contracts and builders. (AC: 3, 4, 5)
  - [x] Define a distinct SCADA divergence alert type.
  - [x] Build the alert from structured comparison outputs only.
  - [x] Emit no alert when all sensors remain within tolerance.
- [x] Add deterministic formatting helpers. (AC: 1, 3, 5)
  - [x] Render a compact comparison summary.
  - [x] Render a readable SCADA divergence alert view.
- [x] Add focused Story 3.3 tests. (AC: 1, 2, 3, 4, 5)
  - [x] Verify structured output content.
  - [x] Verify divergence classification.
  - [x] Verify alert/no-alert behavior.
  - [x] Verify deterministic formatting.

## Dev Notes

- Story 3.3 builds directly on Story 3.2 and must not modify the tolerance decision rule. [Source: [3-2-implement-sensor-by-sensor-scada-comparison-on-consensused-valid-payloads.md](/c:/Users/emili/Desktop/Projets/parallel-truth-fingerprint-prototype/_bmad-output/implementation-artifacts/3-2-implement-sensor-by-sensor-scada-comparison-on-consensused-valid-payloads.md)]
- The split proposal files in `docs/input/` remain the research source of truth.
- This story should remain small and reviewable:
  - comparison result from Story 3.2
  - structured output layer for Story 3.3
  - distinct SCADA divergence alert path for Story 3.3
- Do not add persistence or fingerprint logic.

### Project Structure Notes

- Primary implementation areas:
  - `src/parallel_truth_fingerprint/comparison/`
  - `src/parallel_truth_fingerprint/contracts/`
  - `tests/comparison/`
- Do not redesign:
  - `src/parallel_truth_fingerprint/scada/`
  - `src/parallel_truth_fingerprint/persistence/`
  - `src/parallel_truth_fingerprint/lstm_service/`

## Dev Agent Record

### Agent Model Used

GPT-5 Codex

### Debug Log References

- Story created from approved Epic 3 Story 3.3 wording.
- Story intentionally excludes persistence and LSTM behavior.

### Completion Notes List

- Story artifact created before Story 3.3 implementation begins.
- Added a structured per-sensor output layer on top of the Story 3.2 comparison result.
- Added a distinct SCADA divergence alert contract and builder that emits only when one or more sensors diverge.
- Added compact and detailed formatting helpers for structured SCADA outputs and alerts.
- Kept persistence, LSTM, and later demo/UI behavior out of Story 3.3.
- Added focused tests and preserved full regression stability.

### File List

- `_bmad-output/implementation-artifacts/3-3-produce-structured-per-sensor-scada-comparison-outputs-and-alerts.md`
- `src/parallel_truth_fingerprint/contracts/scada_comparison_output.py`
- `src/parallel_truth_fingerprint/contracts/scada_alert.py`
- `src/parallel_truth_fingerprint/contracts/__init__.py`
- `src/parallel_truth_fingerprint/comparison/__init__.py`
- `src/parallel_truth_fingerprint/comparison/outputs.py`
- `tests/comparison/test_outputs_and_alerts.py`
