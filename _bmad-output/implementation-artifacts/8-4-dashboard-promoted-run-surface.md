# Story 8.4: Dashboard Surface for the Promoted Run

Status: done

## Story

As an operator watching the live demo, I want a small JSON helper that
the dashboard (or any inspection tool) can hit to learn which training
run is currently promoted to live runtime, so that the demonstration
shows the supervised classifier identity alongside the existing
consensus / SCADA cards without forcing a large dashboard rewrite.

## Scope Notes

- Implements `lstm_service/promoted_run_view.py`: a thin read-only view
  layer over Story 8.1's `read_promoted_run`.
- Output shape is JSON-safe and ready to be embedded into the dashboard
  state. The dashboard wiring itself stays out of scope for this story
  to keep the change reviewable; the function is invokable from any
  surface that has access to a `MinioArtifactStore`-compatible store.

## Acceptance Criteria

1. A new function `build_promoted_run_dashboard_view(artifact_store) -> dict` returns: `{"status": "promoted" | "none", "run_id": ... | None, "dataset_name": ... | None, "model_name": ... | None, "promoted_at": ... | None, "previous_run_id": ... | None, "macro_f1": ... | None, "accuracy": ... | None, "parameter_count": ... | None}`.
2. When nothing is promoted, the function returns `{"status": "none", "run_id": null, ...}` without raising.
3. When a run is promoted, the function reads the underlying `TrainingRunRecord` and surfaces its champion metrics.
4. Unit tests cover both branches (nothing promoted; one run promoted with metrics).
5. Full regression remains green.

## Tasks / Subtasks

- [x] Implement `build_promoted_run_dashboard_view`. (AC: 1, 2, 3)
- [x] Add unit tests (2) using `FakeMinioClient`. (AC: 4)
- [x] Run full suite; 215 tests pass.
- [x] Update File List + Completion Notes.

### Completion Notes List

- `build_promoted_run_dashboard_view` returns a JSON-safe dict
  consumable by the dashboard or any other inspection surface.
- Tolerates the case where the promoted run pointer references a
  record that has gone missing from the store: returns the pointer
  metadata with metric fields set to None instead of raising.

### File List

- `_bmad-output/implementation-artifacts/8-4-dashboard-promoted-run-surface.md`
- `src/parallel_truth_fingerprint/lstm_service/promoted_run_view.py`
- `tests/lstm_service/offline_training/test_promoted_run_view.py`

## Dev Agent Record

### Agent Model Used

Claude Opus 4.7 via BMAD dev-story workflow.
