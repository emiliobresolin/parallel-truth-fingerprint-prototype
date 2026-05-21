# Story 7.3: Training History Schema, Writer, and Reader

Status: review

## Story

As a researcher producing reproducible academic evidence, I want every
offline training run persisted under a dedicated MinIO prefix with a
strict JSON schema, plus a reader API that lists runs by benchmark, so
that the cross-benchmark report (Story 7.13) and the post-validation
reintegration (Epic 8) can both consume the same canonical run records
without re-running training.

## Scope Notes

- Implements the `fingerprint-training-history/` MinIO layout declared
  in `architecture-update-2026-05-21.md` §B.2.
- Reuses the existing `MinioArtifactStore` + `FakeMinioClient` from the
  Story 4.x persistence stack — no new external dependency.
- Story 7.3 persists the record, the confusion matrix, and the model
  artifact placeholder. Real model bytes land in Story 7.5 when the
  keras LSTM classifier is introduced.

## Acceptance Criteria

1. A new module `offline_training/registry/training_history.py` provides:
   - `serialize_training_run(record) -> dict` (Story 7.4-aligned schema).
   - `deserialize_training_run(payload) -> TrainingRunRecord`.
   - `write_training_run(record, *, artifact_store, prefix='fingerprint-training-history/') -> WrittenRun`.
   - `list_training_runs(*, artifact_store, benchmark=None, prefix='fingerprint-training-history/') -> tuple[str, ...]`.
   - `read_training_run(run_id, *, artifact_store, prefix='fingerprint-training-history/') -> TrainingRunRecord`.
2. The persisted JSON object key matches `fingerprint-training-history/runs/<run_id>.json`. The confusion matrix is written to `fingerprint-training-history/runs/<run_id>.confusion.json`.
3. After writing, a per-benchmark index file at `fingerprint-training-history/index/by-benchmark/<dataset>.json` lists the run_ids for that dataset in chronological insertion order. `list_training_runs` reads from this index.
4. The serialized payload is round-trip stable: `deserialize(serialize(record)) == record`.
5. Writer/reader work against the existing `MinioArtifactStore` and the existing `FakeMinioClient` test double; no real network is required.
6. Wiring: a new helper `record_training_run_to_artifact_store(record, artifact_store)` is exposed so future stories (and Story 7.7) can persist a real run with one call.
7. Unit tests cover: schema round-trip, write+list+read across two distinct benchmarks, index update is idempotent (writing the same run_id twice does not duplicate).
8. Full regression remains green.

## Tasks / Subtasks

- [x] Define the JSON schema (Python dict shape) for one TrainingRunRecord. (AC: 1, 4)
- [x] Implement `serialize_training_run` / `deserialize_training_run`. (AC: 1, 4)
- [x] Implement `write_training_run` writing both the main record and the confusion-matrix sidecar. (AC: 2)
- [x] Implement the by-benchmark index: read-modify-write of `fingerprint-training-history/index/by-benchmark/<dataset>.json` with deduplicated insertion. (AC: 3, 7)
- [x] Implement `list_training_runs` and `read_training_run`. (AC: 1)
- [x] Add unit tests using the existing `FakeMinioClient`. (AC: 4, 5, 6, 7)
- [x] Run full suite; 164 tests pass.
- [x] Update File List + Completion Notes.

## Dev Notes

- Use the existing `MinioArtifactStore.save_json` / `load_json` / `list_json_objects` API. No new transport.
- `SplitRecord.per_class_counts_train` is a dict with int keys; JSON requires string keys. Coerce on serialize, parse back on deserialize.
- Index file payload shape: `{"dataset": "<name>", "run_ids": ["...", "..."]}`.

## Dev Agent Record

### Agent Model Used

Claude Opus 4.7 via BMAD dev-story workflow.

### Debug Log References

- First RED run failed only because `training_history.py` did not exist;
  GREEN passed on first attempt after the module was added.

### Completion Notes List

- `training_history` module exposes serialize/deserialize, write, list,
  read, and a one-shot helper. All five reuse the project's existing
  `MinioArtifactStore` + `FakeMinioClient` boundary (no new transport).
- Index file shape: `{"dataset": str, "run_ids": [str, ...]}`. The writer
  is idempotent (writing the same run_id twice does not duplicate).
- Confusion matrix is written to a sidecar JSON to keep the main record
  small and easy to diff.
- `SplitRecord` int-keyed dicts are coerced to string keys on serialize
  and parsed back on deserialize so the JSON round-trip is exact.
- Full regression: 164 tests, OK (skipped=7).

### File List

- `_bmad-output/implementation-artifacts/7-3-training-history-schema-and-writer.md`
- `src/parallel_truth_fingerprint/lstm_service/offline_training/registry/training_history.py`
- `tests/lstm_service/offline_training/test_training_history.py`
