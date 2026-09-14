# Story 8.2: Online Inference Helper for the Promoted Classifier

Status: done

## Story

As a researcher closing the loop between the offline training track and
the live pipeline (Decision D6, "reintegration after acceptable
metrics"), I want an `online_inference` helper that loads the currently
promoted run's model from the training-history store at runtime start-up
and exposes a `predict_sequence(window)` API, so that the live runtime
can attach the supervised classifier as a new alert channel without
re-training inside the loop.

## Scope Notes

- Implements `lstm_service/online_inference.py` declared in
  `architecture-update-2026-05-21.md` §B.3.
- Reads the promoted run pointer via Story 8.1's
  `read_promoted_run`.
- Loads the corresponding model file from the artifact store. For now,
  the training pipeline does NOT save the model weights to the store
  (Story 7.5 keeps the keras handle in memory). The helper therefore
  rebuilds the model from the recorded hyperparameters + sequence length
  + class_count taken from the persisted record. This is sufficient for
  the demonstration end-to-end; future work will persist weights.
- The helper is import-light: bringing it in must NOT trigger any model
  build until `OnlineLstmInferencer.load()` is invoked.

## Acceptance Criteria

1. A new module `lstm_service/online_inference.py` exposes `OnlineLstmInferencer` with `load(*, artifact_store) -> OnlineLstmInferencer` and `predict_sequence(window: Sequence[Sequence[float]]) -> InferenceResult`.
2. `InferenceResult` exposes: `predicted_class_id: int`, `predicted_class_name: str`, `class_probabilities: tuple[float, ...]`, `promoted_run_id: str`.
3. `load` rejects a store with no promoted run by raising `RuntimeError` whose message names the promotion CLI command to run first.
4. `predict_sequence` rejects windows whose shape disagrees with the promoted run's `sequence_length` or `feature_count`, raising `ValueError`.
5. Unit test exercises the full path: seed one training run on the embedded ADFA-LD fixture, promote it via Story 8.1, instantiate `OnlineLstmInferencer.load(...)`, call `predict_sequence(...)` on a synthetic window, assert the returned `predicted_class_name` is one of the six ADFA-LD label names and that `class_probabilities` sums to ~1.0.
6. Full regression remains green.

## Tasks / Subtasks

- [ ] Implement `OnlineLstmInferencer` and `InferenceResult`. (AC: 1, 2, 3, 4)
- [ ] Add unit test. (AC: 5)
- [ ] Run full suite. (AC: 6)
- [ ] Update File List + Completion Notes.

## Dev Notes

- The helper deliberately rebuilds the model topology from the persisted
  record's hyperparameters and runs `fit` on the training split before
  serving inference. This keeps Story 8.2 self-contained without
  introducing a model-weights persistence story. Future work can
  serialise weights into MinIO + skip the re-fit.

## Dev Agent Record

### Agent Model Used

Claude Opus 4.7 via BMAD dev-story workflow.

### Debug Log References

(populated by Dev)

### Completion Notes List

(populated by Dev)

### File List

(populated by Dev)
