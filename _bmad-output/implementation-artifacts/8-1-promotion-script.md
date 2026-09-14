# Story 8.1: Promotion Script for the Endorsed Run

Status: done

## Story

As a researcher controlling which classifier the live runtime should
actually use, I want a CLI that endorses one specific TrainingRunRecord
as the "promoted" run by writing its id into
`fingerprint-training-history/index/latest.json`, so that the Epic 8
online inference helper (Story 8.2) loads exactly that model from MinIO
and the dashboard (Story 8.4) shows which run is in production.

## Scope Notes

- Owns `scripts/promote_lstm_run.py` declared in
  `architecture-update-2026-05-21.md` §B.3.
- Reuses Story 7.3's `MinioArtifactStore` boundary (no new transport).
- Persistence layout:
  ```
  fingerprint-training-history/
    index/latest.json   {"run_id": "...", "promoted_at": "...",
                         "previous_run_id": "..." | null}
  ```
- The script also exposes a programmatic helper
  `offline_training/registry/promotion.py::promote_training_run` so unit
  tests (and later the dashboard) can drive promotion without forking a
  subprocess.

## Acceptance Criteria

1. A new module `offline_training/registry/promotion.py` exposes:
   - `promote_training_run(run_id, *, artifact_store, prefix=HISTORY_PREFIX) -> PromotedRun`.
   - `read_promoted_run(*, artifact_store, prefix=HISTORY_PREFIX) -> PromotedRun | None`.
2. `promote_training_run` rejects unknown run ids with a `ValueError` referencing the expected MinIO path. It refuses to overwrite the latest pointer when the previous and new run ids are identical, returning the existing `PromotedRun` unchanged.
3. The `latest.json` payload carries: `run_id`, `dataset_name`, `model_name`, `promoted_at` (UTC ISO 8601), `previous_run_id` (or `null`).
4. A new CLI `scripts/promote_lstm_run.py` accepts `--run-id`, the four MinIO flags from Story 7.7's CLI, and prints the JSON payload that was written.
5. Unit tests cover: promote a brand-new id, re-promote the same id is a no-op, promote replaces the latest pointer and records `previous_run_id`, attempting to promote an unknown id raises, `read_promoted_run` returns `None` when nothing is promoted yet.
6. Full regression remains green.

## Tasks / Subtasks

- [x] Implement `PromotedRun` dataclass + `promote_training_run` + `read_promoted_run` in `offline_training/registry/promotion.py`. (AC: 1, 2, 3)
- [x] Implement `scripts/promote_lstm_run.py` CLI (supports `--persist` for MinIO and `--persist-local` for filesystem). (AC: 4)
- [x] Add unit tests (5) using `FakeMinioClient`. (AC: 5)
- [x] Run full suite; net 206 tests pass.
- [x] Update File List + Completion Notes.

## Dev Notes

- The promoted pointer is intentionally separate from the per-benchmark
  index files. Multiple benchmarks have independent histories; only one
  run is ever "promoted to live runtime" at a time.

## Dev Agent Record

### Agent Model Used

Claude Opus 4.7 via BMAD dev-story workflow.

### Debug Log References

(populated by Dev)

### Completion Notes List

(populated by Dev)

### File List

(populated by Dev)
