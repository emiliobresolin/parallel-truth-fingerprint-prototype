# Story 7.8: GRU Classifier Baseline (Assis 4.2.4 Effect-of-Model)

Status: review

## Story

As a researcher mirroring the "effect of deep learning model" experiment
in Assis Section 4.2.4, I want a GRU classifier adapter that exposes the
same hyperparameter surface as `LstmClassifier`, so that Story 7.9's
hyperparameter sweep and Story 7.13's cross-benchmark report can compare
LSTM vs GRU on identical inputs.

## Scope Notes

- Implements `offline_training/models/gru_classifier.py` declared in
  `architecture-update-2026-05-21.md` §B.1.
- Same KERAS_BACKEND=torch discipline as Story 7.5.
- Same `extra_hyperparameters` surface (`hidden_units`, `num_layers`).

## Acceptance Criteria

1. A new module `offline_training/models/gru_classifier.py` exposes `GruClassifier` registered under the name `"gru-classifier"`.
2. `build()` constructs a compiled Keras model on the torch backend with: input shape `(sequence_length, feature_count)`, `num_layers` stacked `GRU` layers with `hidden_units` units each (defaults 2 / 64), softmax head over `class_count`, Adam optimizer, sparse categorical crossentropy loss.
3. `fit()` returns a `FitResult` with the per-epoch loss series and the parameter count.
4. `predict()` returns one integer class id per test sequence (argmax of softmax).
5. End-to-end run through `execute_training_run(benchmark="dummy", model="gru-classifier", ...)` and through `execute_training_run(benchmark="adfa-ld", model="gru-classifier", ...)` produces a record with `model_name="gru-classifier"` and a non-zero parameter count.
6. Full regression remains green.

## Tasks / Subtasks

- [x] Implement `GruClassifier` adapter. (AC: 1, 2, 3, 4)
- [x] Register via side-effect import in `models/__init__.py`. (AC: 1)
- [x] Add unit tests (5): adapter registered, build topology, fit/predict round trip, end-to-end through `execute_training_run` on `dummy` and `adfa-ld`. (AC: 5)
- [x] Run full suite; 184 tests pass. (AC: 6)
- [x] Update File List + Completion Notes.

### Debug Log References

- GREEN on first attempt. The GRU adapter is a structural twin of the LSTM
  adapter with only `LSTM` -> `GRU` and naming swapped, so the same
  `_load_keras_module` guard, deterministic seed setup, and `fit`/`predict`
  paths are reused.

### Completion Notes List

- `GruClassifier` mirrors `LstmClassifier` API exactly so Story 7.9's sweep
  and Story 7.13's report can substitute `--model gru-classifier` for
  `--model lstm-classifier` without other changes.
- Both end-to-end tests (dummy and adfa-ld) confirm the adapter integrates
  with `execute_training_run` and produces a non-zero parameter count and a
  valid confusion matrix.
- Full regression: 184 tests, OK (skipped=7).

### File List

- `_bmad-output/implementation-artifacts/7-8-gru-classifier-baseline.md`
- `src/parallel_truth_fingerprint/lstm_service/offline_training/models/gru_classifier.py`
- `src/parallel_truth_fingerprint/lstm_service/offline_training/models/__init__.py`
- `tests/lstm_service/offline_training/test_gru_classifier.py`

## Dev Notes

- GRU has roughly 3/4 of the parameter count of LSTM for the same hidden
  size, mirroring Assis Section 4.2.4. The unit test asserts on structure
  (registration + class) and on non-zero parameter count, not on a fixed
  number.

## Dev Agent Record

### Agent Model Used

Claude Opus 4.7 via BMAD dev-story workflow.

<!-- Dev Agent Record populated above. -->

