# Story 4.2: Train and Save a Reusable Local LSTM Fingerprint Model

Status: review

<!-- Note: Validation is optional. Run validate-create-story for quality check before dev-story. -->

## Story

As a researcher,
I want the system to train and save an LSTM fingerprint model from the approved normal-only dataset path,
so that the prototype can validate the real local training path now and later support a more meaningful temporal fingerprint claim once dataset adequacy is satisfied.

## Scope Notes

- This story is limited to local LSTM model training and model-artifact persistence.
- The original implementation reached runtime-valid training against the Story 4.1 in-memory dataset outputs.
- This story has now been revalidated against the persisted dataset artifact path introduced by Story 4.2A.
- Meaningful fingerprint-valid closure still depends on dataset adequacy, which remains below the approved floor in the current smoke corpus.
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
5. Given the corrected Epic 4 dataset boundary, when Story 4.2 is fully validated, then the trainer consumes the persisted dataset artifact path introduced by Story 4.2A rather than relying only on in-memory dataset objects.
6. Given the distinction between runtime validation and fingerprint meaningfulness, when Story 4.2 validation is recorded, then the story explicitly distinguishes:
   - runtime-valid training
   - meaningful fingerprint-valid training
   and it does not claim academically strong fingerprint readiness if the dataset adequacy gate has not yet been satisfied.
7. Given focused validation, when Story 4.2 tests are run, then they prove:
   - real LSTM model construction through the approved Keras API surface
   - torch-backend enforcement
   - deterministic model/metadata object naming
   - MinIO-backed model persistence
   - rejection of empty or schema-inconsistent training input
8. Given the project testing rule, when Story 4.2 is closed, then the story record explicitly includes:
   - what was tested
   - exact commands executed
   - test results
   - real runtime behavior validated
   - remaining limitations

## Dependencies

- Story 4.1 training windows and dataset manifest for current runtime-valid implementation
- Story 4.2A persisted dataset artifact path for final revalidation and closure
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
- Story 4.2 may be considered closed as runtime-valid once the real local training and MinIO-backed model persistence path is proven.
- Story 4.2 may not be treated as meaningfully fingerprint-valid until:
  - Story 4.2A has persisted the dataset artifact
  - the trainer has been revalidated against that persisted dataset path
  - the normal-history adequacy gate has been evaluated explicitly
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
- Revalidated Story 4.2 against the persisted Story 4.2A dataset artifact path.
- Added one trainer entrypoint that loads the persisted dataset manifest plus `.npz` windows artifact before training.
- Updated the real runtime smoke test so the model is trained from the persisted dataset artifact path, not directly from in-memory windows.

### What Was Tested

- Focused Story 4.2 trainer tests
- Persisted-dataset reload coverage through Story 4.2A dataset-artifact tests
- Combined affected regression surface for trainer plus persistence boundary
- Full regression suite
- Real Keras plus torch plus MinIO smoke validation using the persisted dataset artifact path

### Exact Commands Executed

```powershell
$env:PYTHONPATH='src'
.\.venv\Scripts\python -m unittest tests.lstm_service.test_dataset_artifacts
.\.venv\Scripts\python -m unittest tests.lstm_service.test_trainer
.\.venv\Scripts\python -m unittest tests.lstm_service.test_dataset_builder
.\.venv\Scripts\python -m unittest tests.persistence.test_service tests.lstm_service.test_dataset_artifacts tests.lstm_service.test_trainer
.\.venv\Scripts\python -m unittest discover -s tests

$env:RUN_REAL_ML_SMOKE='1'
.\.venv\Scripts\python -m unittest tests.lstm_service.test_trainer_runtime_smoke

@'
from minio import Minio
client = Minio('localhost:9000', access_key='minioadmin', secret_key='minioadmin', secure=False)
buckets = sorted([bucket.name for bucket in client.list_buckets() if bucket.name.startswith('valid-consensus-artifacts-smoke-')])
latest = buckets[-1]
print('LATEST_BUCKET', latest)
print('OBJECTS', sorted(obj.object_name for obj in client.list_objects(latest, recursive=True)))
'@ | .\.venv\Scripts\python -
```

### Test Results

- `tests.lstm_service.test_dataset_artifacts` -> `Ran 3 tests` -> `OK`
- `tests.lstm_service.test_trainer` -> `Ran 5 tests` -> `OK`
- `tests.lstm_service.test_dataset_builder` -> `Ran 4 tests` -> `OK`
- `tests.persistence.test_service tests.lstm_service.test_dataset_artifacts tests.lstm_service.test_trainer` -> `Ran 11 tests` -> `OK`
- `python -m unittest discover -s tests` -> `Ran 93 tests` -> `OK (skipped=2)`
- `tests.lstm_service.test_trainer_runtime_smoke` -> `Ran 1 test` -> `OK`

### Real Runtime Behavior Validated

- The real Keras plus torch training path consumed the persisted Story 4.2A dataset artifact path.
- The smoke bucket contained:
  - 3 upstream valid round artifacts
  - 2 persisted dataset artifacts under `fingerprint-datasets/`
  - 2 model artifacts under `fingerprint-models/`
- The saved model metadata pointed back to the persisted dataset id, not only to an in-memory dataset object.
- The saved `.keras` model artifact loaded back successfully for prediction after training from the persisted dataset artifact path.
- The real smoke run produced:
  - `SOURCE_DATASET_ID = training-dataset::round-smoke-...::seq-2`
  - `TRAINING_WINDOW_COUNT = 2`
  - a valid MinIO `artifact_uri` for the model object

### Remaining Limitations

- Story 4.2 is now revalidated against the persisted dataset artifact path, but it remains only `runtime-valid`.
- The current smoke corpus is still intentionally small:
  - 3 eligible normal persisted artifacts
  - 2 generated windows
- The Story 4.2A adequacy floor is still not met:
  - required 30 eligible normal persisted artifacts
  - required 20 generated windows
- Story 4.3 remains blocked until the sequencing rule is satisfied and the fingerprint path is moved beyond runtime-only validation.

### File List

- `_bmad-output/implementation-artifacts/4-2-train-and-save-a-reusable-local-lstm-fingerprint-model.md`
- `pyproject.toml`
- `README.md`
- `src/parallel_truth_fingerprint/contracts/fingerprint_model.py`
- `src/parallel_truth_fingerprint/contracts/__init__.py`
- `src/parallel_truth_fingerprint/lstm_service/__init__.py`
- `src/parallel_truth_fingerprint/lstm_service/dataset_artifacts.py`
- `src/parallel_truth_fingerprint/lstm_service/trainer.py`
- `src/parallel_truth_fingerprint/persistence/artifact_store.py`
- `tests/lstm_service/test_dataset_artifacts.py`
- `tests/lstm_service/test_trainer.py`
- `tests/lstm_service/test_trainer_runtime_smoke.py`
