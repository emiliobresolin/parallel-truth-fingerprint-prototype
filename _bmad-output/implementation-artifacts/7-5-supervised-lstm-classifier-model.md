# Story 7.5: Supervised LSTM Classifier Model

Status: review

## Story

As a researcher implementing the migration from the deprecated autoencoder
to a supervised classifier (course-correction decision D1), I want a small
Keras LSTM classifier on the torch backend, sized in the spirit of Assis
Section 4.1.1 (two LSTM layers, configurable hidden units, softmax head),
so that Story 7.7's first real run on ADFA-LD can use a real LSTM
classifier and produce defensible F1 / accuracy numbers.

## Scope Notes

- Implements `offline_training/models/lstm_classifier.py` declared in
  `architecture-update-2026-05-21.md` §B.1.
- Uses the project's approved ML stack: `KERAS_BACKEND=torch`. Sets the
  env var defensively at import time, mirroring `lstm_service/trainer.py`.
- Story 7.5 introduces ONE real classifier (`lstm-classifier`). Story 7.8
  adds the GRU baseline; Story 7.6 adds the ADFA-LD adapter; Story 7.7
  drives the first real training run.

## Acceptance Criteria

1. A new module `offline_training/models/lstm_classifier.py` exposes a `LstmClassifier` adapter that satisfies the `ClassifierAdapter` protocol and is registered under the name `"lstm-classifier"`.
2. `build()` returns a compiled Keras model on the torch backend with: input shape `(sequence_length, feature_count)`, two stacked `LSTM` layers with configurable `hidden_units` (default 64), a `Dense(class_count, softmax)` head, optimizer Adam, loss `sparse_categorical_crossentropy`.
3. `fit()` trains the model for `epochs` epochs at `batch_size`, returns a `FitResult` carrying the per-epoch loss series and the model parameter count.
4. `predict()` returns one integer class id per test sequence (argmax of softmax).
5. The classifier is deterministic enough to enable Story 7.9's hyperparameter sweep: same seed + same hyperparameters + same data => the same parameter count and the same number of epochs executed. Loss values may differ slightly due to backend non-determinism; tests assert on the parameter count and shape only.
6. The dummy benchmark exercises a real end-to-end training cycle through `execute_training_run(benchmark='dummy', model='lstm-classifier', ...)` without raising, and the resulting record has a non-empty `per_epoch_loss` series and a non-zero `parameter_count`.
7. Full regression remains green. New tests bring the suite to 164 + new.

## Tasks / Subtasks

- [x] Add `LstmClassifier` adapter with build / fit / predict. (AC: 1, 2, 3, 4)
- [x] Register the adapter under the name `"lstm-classifier"` via side-effect import in `models/__init__.py`. (AC: 1)
- [x] Add unit tests (4): adapter registered, model topology, fit/predict round trip, end-to-end run through `execute_training_run`. (AC: 2, 3, 4, 5, 6)
- [x] Run full suite; 168 tests pass.
- [x] Update File List + Completion Notes.

## Dev Notes

- The legacy autoencoder trainer sets `os.environ["KERAS_BACKEND"] = "torch"`
  before `import keras`. The new classifier module must do the same to
  avoid loading the deprecated `tensorflow` import path that crashes the
  Windows runtime.
- Use small defaults to keep test wall-clock time low: 2 stacked LSTMs of
  16 units, 1 epoch, batch size 2 in the unit tests.
- `random.Random(seed)` is not sufficient for Keras model determinism on
  the torch backend; we set `keras.utils.set_random_seed(seed)` before
  build. This is "best effort"; tests only assert structural determinism
  (parameter count, output shape), not numerical equality of weights.

## Dev Agent Record

### Agent Model Used

Claude Opus 4.7 via BMAD dev-story workflow.

### Debug Log References

- Keras emits a `DeprecationWarning` from
  `keras/src/backend/torch/core.py:253` about `np.array(copy=False)` under
  NumPy 2.x. The warning does not affect correctness (tests pass) and is
  upstream; no project-level action needed for Story 7.5. Worth a follow-up
  ticket once Keras releases a fix on the torch backend.

### Completion Notes List

- `LstmClassifier` is a small stacked LSTM (configurable `hidden_units`,
  `num_layers`) with a `Dense(class_count, softmax)` head, Adam optimiser,
  sparse categorical crossentropy loss.
- The classifier is the first model in the offline track that consumes
  real benchmark sequences. Its hyperparameter surface lines up with the
  Story 7.9 sweep config.
- `_load_keras_module` mirrors the existing legacy trainer guard: forces
  `KERAS_BACKEND=torch`, hard-fails clearly if `keras` or `torch` are not
  installed.
- `keras.utils.set_random_seed(seed)` is invoked before building the
  model, giving best-effort determinism on the torch backend; tests only
  assert structural determinism (parameter count, output shape).
- Side-effect registration via `models/__init__.py` keeps `load_model`
  working without touching every caller.
- Full regression: 168 tests, OK (skipped=7).

### File List

- `_bmad-output/implementation-artifacts/7-5-supervised-lstm-classifier-model.md`
- `src/parallel_truth_fingerprint/lstm_service/offline_training/models/lstm_classifier.py`
- `src/parallel_truth_fingerprint/lstm_service/offline_training/models/__init__.py`
- `tests/lstm_service/offline_training/test_lstm_classifier.py`
