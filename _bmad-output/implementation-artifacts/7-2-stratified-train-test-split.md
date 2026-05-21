# Story 7.2: Stratified 80/20 Train/Test Split with Recorded Seed

Status: review

## Story

As a researcher mirroring the methodological discipline of Assis Section 3.3.1,
I want a deterministic stratified train/test split utility that respects the
80/20 ratio mandated by the advisor (meeting M1) and records the seed plus
per-class counts, so that every offline training run can be reproduced
exactly from its split record alone.

## Scope Notes

- Implements `offline_training/splits.py` declared in
  `architecture-update-2026-05-21.md` §B.1.
- Replaces the naive 80/20 cut placeholder used in Story 7.1's
  `execute_training_run`.
- Does **not** persist the split record to MinIO; that lands in Story 7.3.
- Does **not** depend on `sklearn` (project has no sklearn dependency).

## Acceptance Criteria

1. A new function `stratified_train_test_split(sequences, labels, *, train_ratio=0.8, seed)` lives at `parallel_truth_fingerprint.lstm_service.offline_training.splits`.
2. The split is **stratified**: each class label is split independently according to the same `train_ratio`, so the train and test sets preserve class proportions.
3. The split is **deterministic** for a given `seed`: two calls with identical inputs return identical outputs.
4. The function returns a tuple `(x_train, y_train, x_test, y_test, split_record)` where `split_record` is a dataclass exposing `seed`, `train_ratio`, `total_samples`, `train_samples`, `test_samples`, `per_class_counts_train`, `per_class_counts_test`.
5. The function rejects empty inputs and rejects any class that has fewer than 2 samples (cannot be stratified).
6. `execute_training_run` (Story 7.1) is updated to use the new split. The CLI smoke tests from Story 7.1 continue to pass.
7. Five new unit tests cover: 80/20 stratification on balanced data, 80/20 stratification on imbalanced data, determinism for fixed seed, different seeds produce different splits, and the rejection rules.

## Dependencies

- Story 7.1 must be at status review or done.

## Tasks / Subtasks

- [x] Define `SplitRecord` dataclass in `offline_training/splits.py`. (AC: 4)
- [x] Implement `stratified_train_test_split` using `random.Random(seed)` and per-class shuffle. (AC: 1, 2, 3, 4, 5)
- [x] Wire `execute_training_run` to call `stratified_train_test_split` instead of the naive slice. Add a `split_record` attribute to `TrainingRunRecord`. (AC: 6)
- [x] Add unit tests under `tests/lstm_service/offline_training/test_splits.py`. (AC: 7)
- [x] Add a CLI smoke test that asserts `split_record` is present on the run record returned by `cli_main`. (AC: 6) — covered by `TrainingRunUsesStratifiedSplitTests.test_execute_training_run_records_split`.
- [x] Run full suite; 153 tests pass (145 baseline + 8 new).
- [x] Update File List + Completion Notes.

## Technical Notes

- Use `random.Random(seed)` only (no global `random`). Same seed must shuffle
  each class deterministically.
- Round per-class train count with `int(round(per_class * train_ratio))`,
  clamp to leave at least 1 sample in both train and test for every class.
- The function must accept `sequences` as any indexable sequence (list, tuple,
  arbitrary nested structures). Return the same container types.

## Dev Notes

- Assis Section 3.3.1 quotes a 75/25 split; the advisor explicitly named
  80/20 (meeting M1). The `train_ratio` parameter defaults to 0.8 to match
  the advisor; passing `0.75` lets us reproduce the original Assis figure
  for direct comparison.

## Dev Agent Record

### Agent Model Used

Claude Opus 4.7 via BMAD dev-story workflow.

### Debug Log References

- All seven split-specific unit tests passed on the first GREEN attempt
  after the placeholder slice in `execute_training_run` was replaced.
- The dummy benchmark produces 32 samples (16 per class). 80/20 stratified
  split gives 26 train / 6 test (13/3 per class with the clamp rule);
  validated by `test_execute_training_run_records_split`.

### Completion Notes List

- `SplitRecord` dataclass introduced (seed, train_ratio, totals, per-class
  counts).
- `stratified_train_test_split` uses an isolated `random.Random(seed)` per
  call; no global RNG mutation.
- Class clamp rule: at least 1 sample in train AND 1 in test per class.
- `train_ratio=0.8` default matches advisor M1; passing 0.75 reproduces
  Assis Section 3.3.1 explicitly.
- `TrainingRunRecord` now carries `split_record`; downstream Story 7.3 will
  persist it to MinIO alongside the rest of the run.
- Full regression: 153 tests, OK (skipped=7).

### File List

- `_bmad-output/implementation-artifacts/7-2-stratified-train-test-split.md`
- `src/parallel_truth_fingerprint/lstm_service/offline_training/splits.py`
- `src/parallel_truth_fingerprint/lstm_service/offline_training/training/run.py`
- `tests/lstm_service/offline_training/test_splits.py`
