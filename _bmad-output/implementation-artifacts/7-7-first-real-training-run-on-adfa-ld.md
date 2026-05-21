# Story 7.7: First Real Training Run on ADFA-LD

Status: review

## Story

As a researcher producing the first piece of academic evidence for the
offline track, I want one fully-recorded end-to-end training run on
ADFA-LD with the supervised LSTM classifier, including persistence of
the run record to the MinIO-backed training history, so that subsequent
stories (7.8 GRU baseline, 7.9 sweep, 7.13 comparative report) have a
real run to extend and compare against.

## Scope Notes

- Drives `execute_training_run(benchmark="adfa-ld", model="lstm-classifier", ...)`
  with the hyperparameters declared in `epics-update-2026-05-21.md`
  Story 7.7 (epochs=30, batch=64, lr=1e-3, sequence_length=50, seed=42).
- Story 7.7 is exercised in CI against the embedded fixture (no network
  download). The real-data execution path is documented in this story for
  the user to run locally once they obtain `ADFA_LD_PATH`.
- Persistence uses Story 7.3's `record_training_run_to_artifact_store`
  against the FakeMinioClient in tests; against the real local MinIO when
  the user runs it manually.

## Acceptance Criteria

1. A new helper `offline_training/training/runner_adfa_ld.py::run_first_adfa_ld_training` orchestrates: configure ADFA-LD root → execute_training_run with the Story 7.7 hyperparameters → persist via Story 7.3 → return the (record, written) tuple.
2. A new CLI flag `--persist` on `scripts/train_lstm_offline.py` triggers persistence to a local MinIO when set, defaulting to false so existing smoke runs do not produce side effects.
3. Unit test exercises the helper end-to-end against the embedded fixture: returns a `TrainingRunRecord` with `dataset_name="adfa-ld"`, `model_name="lstm-classifier"`, all 6 classes present in the confusion matrix axis (even if some are absent in the test split), and `split_record.seed == 42`. Run record is written and listable via `list_training_runs(benchmark="adfa-ld")`.
4. Test uses tiny hyperparameters (epochs=1, batch=2, sequence_length=4) so wall-clock stays under 5 seconds on the project's reference machine.
5. Full regression remains green.

## Tasks / Subtasks

- [x] Implement `run_first_adfa_ld_training` helper. (AC: 1)
- [x] Extend the CLI with `--persist`, `--minio-bucket`, `--minio-endpoint`, `--minio-access-key`, `--minio-secret-key`, `--minio-secure`; default off. (AC: 2)
- [x] Add unit test that exercises the helper end-to-end against the fixture + FakeMinioClient. (AC: 3, 4)
- [x] Run full suite; 179 tests pass. (AC: 5)
- [x] Document the real local-MinIO run command in the story file's Dev Notes.
- [x] Update File List + Completion Notes.

## Dev Notes

- The Story 7.7 hyperparameters declared in `epics-update` are the *production*
  defaults. The unit test uses smaller values so it stays fast under
  unittest. Both share the same code path.
- For the real local run the user should:
  ```powershell
  $env:KERAS_BACKEND='torch'
  $env:PYTHONPATH='src'
  $env:ADFA_LD_PATH='<absolute path to unzipped ADFA-LD root>'
  docker compose -f compose.local.yml up -d minio   # ensures MinIO is reachable
  .venv\Scripts\python.exe scripts\train_lstm_offline.py `
      --benchmark adfa-ld --model lstm-classifier `
      --epochs 30 --batch-size 64 --learning-rate 1e-3 `
      --sequence-length 50 --seed 42 --persist
  ```
- The CLI prints the run_id; the user later inspects it under
  `fingerprint-training-history/runs/<run_id>.json` in MinIO.

## Dev Agent Record

### Agent Model Used

Claude Opus 4.7 via BMAD dev-story workflow.

### Debug Log References

- GREEN on first attempt. No debugging cycles required.
- Wall clock for the unit test (epochs=1, batch=2, seq_len=4): ~2.8 s on
  the project reference machine. Within the 5 s budget set in AC4.

### Completion Notes List

- `run_first_adfa_ld_training` is the single chokepoint for ADFA-LD runs.
  It temporarily sets `ADFA_LD_PATH` (restored on exit) so concurrent
  tests do not see drift.
- The CLI gains `--persist` plus four MinIO-connection flags. Without
  `--persist` the CLI behaviour is byte-identical to Story 7.1; with
  `--persist` it uses Story 7.3's writer.
- The unit test uses tiny hyperparameters (epochs=1, batch=2,
  sequence_length=4) and the embedded fixture. The "production"
  hyperparameters declared in `epics-update` Story 7.7 are executed by
  the user on a machine with the real ADFA-LD dataset; the CLI command is
  documented in this story's Dev Notes block.
- Full regression: 179 tests, OK (skipped=7).

### File List

- `_bmad-output/implementation-artifacts/7-7-first-real-training-run-on-adfa-ld.md`
- `src/parallel_truth_fingerprint/lstm_service/offline_training/training/runner_adfa_ld.py`
- `src/parallel_truth_fingerprint/lstm_service/offline_training/cli.py`
- `tests/lstm_service/offline_training/test_runner_adfa_ld.py`
