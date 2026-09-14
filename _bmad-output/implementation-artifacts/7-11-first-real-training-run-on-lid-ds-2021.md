# Story 7.11: First Real Training Run on LID-DS 2021

Status: done

## Story

Mirror of Story 7.7 against LID-DS 2021: produce one fully-recorded
end-to-end training run with the supervised LSTM classifier, persist it
via Story 7.3, so that Story 7.12's sweep and Story 7.13's cross-benchmark
report can extend it.

## Acceptance Criteria

1. A new helper `offline_training/training/runner_lid_ds_2021.py::run_first_lid_ds_2021_training` orchestrates: configure `LID_DS_2021_PATH` → `execute_training_run(benchmark="lid-ds-2021", model="lstm-classifier", ...)` → persist via Story 7.3 → return `(record, written)`.
2. Unit test exercises the helper end-to-end against the embedded LID-DS fixture + FakeMinioClient with tiny hyperparameters (epochs=1, batch=2, sequence_length=4). Test asserts: `dataset_name="lid-ds-2021"`, `model_name="lstm-classifier"`, confusion matrix axis count equals the label-space size (Normal + 2 scenarios = 3), persistence + list + read round-trip works.
3. Full regression remains green.

## Tasks / Subtasks

- [x] Implement `run_first_lid_ds_2021_training`. (AC: 1)
- [x] Add unit test (1) end-to-end on the fixture + FakeMinioClient. (AC: 2)
- [x] Run full suite; 197 tests pass.
- [x] Update File List + Completion Notes.

### Debug Log References

- GREEN on first attempt; helper is a structural twin of
  `run_first_adfa_ld_training` with the env var name and benchmark id
  swapped.

### Completion Notes List

- Helper preserves the prior `LID_DS_2021_PATH` env var across the call;
  concurrent tests that set the env var do not see drift.
- Confusion matrix is 3x3 against the fixture (Normal + 2 scenarios).

### File List

- `_bmad-output/implementation-artifacts/7-11-first-real-training-run-on-lid-ds-2021.md`
- `src/parallel_truth_fingerprint/lstm_service/offline_training/training/runner_lid_ds_2021.py`
- `tests/lstm_service/offline_training/test_runner_lid_ds_2021.py`

## Dev Notes

- Production run command for the user (on a machine with the real
  LID-DS 2021 archive):
  ```powershell
  $env:KERAS_BACKEND='torch'
  $env:PYTHONPATH='src'
  $env:LID_DS_2021_PATH='<absolute path to LID-DS 2021 root>'
  docker compose -f compose.local.yml up -d minio
  .venv\Scripts\python.exe scripts\train_lstm_offline.py `
      --benchmark lid-ds-2021 --model lstm-classifier `
      --epochs 30 --batch-size 64 --learning-rate 1e-3 `
      --sequence-length 50 --seed 42 --persist
  ```

## Dev Agent Record

### Agent Model Used

Claude Opus 4.7 via BMAD dev-story workflow.

<!-- Dev Agent Record populated above. -->

