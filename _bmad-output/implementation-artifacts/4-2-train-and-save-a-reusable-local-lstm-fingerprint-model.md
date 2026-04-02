# Story 4.2: Train and Save a Reusable Local LSTM Fingerprint Model

Status: review

<!-- Note: Validation is optional. Run validate-create-story for quality check before dev-story. -->

## Story

As a researcher,
I want the system to train and save an LSTM fingerprint model from validated normal data,
so that the prototype can reuse the model for later inference during demonstrations.

## Scope Notes

- This story is limited to local LSTM model training and model-artifact persistence.
- It must consume only the Story 4.1 training windows and dataset manifest.
- It must use the approved Epic 4 ML stack decision:
  - `keras`
  - `torch` backend
- The trained model must be saved in the real local MinIO-backed object-store path under a dedicated model prefix.
- This story must not add:
  - runtime inference
  - anomaly score generation
  - replay detection
  - UI behavior

## Acceptance Criteria

1. Given a prepared normal training dataset, when model training executes, then the system trains a real LSTM model for the compressor physical-operational fingerprint using `keras` with the `torch` backend.
2. Given the approved local execution scope, when the training flow runs, then it remains a simple local component and does not require distributed ML infrastructure or a separate deployed ML platform.
3. Given a successful training run, when the model is saved, then the system persists the `.keras` model artifact plus structured training metadata for reuse.
4. Given the current prototype storage boundary, when the model is saved, then it is written to the MinIO-backed object-store path under a dedicated model prefix rather than a second unrelated storage solution.
5. Given focused validation, when Story 4.2 tests are run, then they prove:
   - real LSTM model construction through the approved Keras API surface
   - torch-backend enforcement
   - deterministic model/metadata object naming
   - MinIO-backed model persistence
   - rejection of empty or schema-inconsistent training input

## Dependencies

- Story 4.1 training windows and dataset manifest
- Existing MinIO-backed artifact store

## Tasks / Subtasks

- [x] Define the Story 4.2 trained-model metadata contract. (AC: 3, 4, 5)
  - [x] Capture model identity, dataset lineage, backend, and storage keys.
- [x] Add MinIO object-store support for model bytes. (AC: 3, 4, 5)
  - [x] Add binary save/load helpers to the object-store adapter.
- [x] Implement local LSTM model training. (AC: 1, 2, 5)
  - [x] Enforce `KERAS_BACKEND=torch`.
  - [x] Build a simple LSTM autoencoder suitable for later anomaly scoring.
- [x] Implement model save plus metadata save for reuse. (AC: 3, 4, 5)
  - [x] Save the `.keras` model artifact under a dedicated MinIO prefix.
  - [x] Save structured training metadata alongside it.
- [x] Add focused Story 4.2 tests and preserve regression stability. (AC: 5)

## Technical Notes

- Explicit Epic 4 ML stack decision:
  - `keras` with `torch` backend
- This story makes that decision executable in code.
- The implementation uses an LSTM autoencoder so Story 4.3 can later derive anomaly score from reconstruction error without redesigning the model.
- Model artifacts are stored in the existing MinIO bucket under `fingerprint-models/`.
- The model metadata must capture:
  - model id
  - backend
  - model format
  - source dataset id
  - feature schema
  - sequence length
  - training window count
  - training parameters
  - model object key
  - metadata object key

## Real vs Simulated Boundary

- Real in this story:
  - Keras LSTM model construction
  - local training flow
  - MinIO-backed model artifact storage
  - training metadata persistence
- Simulated or mock around this story:
  - the upstream compressor/process behavior represented in the dataset
- Conceptual only for later stories:
  - runtime inference
  - replay detection output
  - UI integration

## Academic Mapping

- This story turns validated normal physical-operational sequences into a learned reusable fingerprint.
- It preserves the methodological rule that only trusted validated data may enter model training.
- It keeps the model local, inspectable, and demonstrable.

## Dev Notes

- Do not train on raw values outside the Story 4.1 dataset builder.
- Do not introduce a second model-storage path.
- Do not start inference in this story.

## Dev Agent Record

### Agent Model Used

GPT-5 Codex

### Debug Log References

- Story created and implemented immediately after approved Story 4.1.

### Completion Notes List

- Standalone Story 4.2 artifact created and implemented.
- Added typed trained-model metadata contract.
- Added MinIO byte-save/load support for model artifacts.
- Implemented local Keras LSTM autoencoder training with torch-backend enforcement.
- Added MinIO-backed model save plus metadata save.
- Added focused Story 4.2 tests and preserved full regression stability.

### File List

- `_bmad-output/implementation-artifacts/4-2-train-and-save-a-reusable-local-lstm-fingerprint-model.md`
- `pyproject.toml`
- `README.md`
- `src/parallel_truth_fingerprint/contracts/fingerprint_model.py`
- `src/parallel_truth_fingerprint/contracts/__init__.py`
- `src/parallel_truth_fingerprint/lstm_service/__init__.py`
- `src/parallel_truth_fingerprint/lstm_service/trainer.py`
- `src/parallel_truth_fingerprint/persistence/artifact_store.py`
- `tests/lstm_service/test_trainer.py`
