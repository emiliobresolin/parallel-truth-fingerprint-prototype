# Story 4.3: Implement Fingerprint Inference With Anomaly Score and Classification

Status: review

## Story

As a researcher,
I want inference outputs with anomaly score and normal/anomalous classification,
so that temporal behavior can be evaluated during execution.

## Scope Notes

- This story is limited to LSTM fingerprint inference outputs.
- It must preserve the corrected dataset -> training -> model flow established by Stories 4.2A and 4.2.
- It must preserve the existing MinIO persistence boundary.
- It must keep fingerprint inference distinct from:
  - SCADA divergence outputs
  - consensus-failure outputs
- It must not add:
  - replay-detection logic beyond generic inference outputs
  - UI work
  - scenario-control wiring
  - a second storage path
  - architecture redesign

## Limitation Carried Forward

Story 4.3 must proceed on a runtime-valid but not yet meaningful-fingerprint-valid fingerprint base, because the current normal-history dataset still falls below the approved adequacy floor of 30 eligible artifacts and 20 generated windows.

## Acceptance Criteria

1. Given a saved fingerprint model and valid runtime input, when inference executes, then the system produces an anomaly score and a normal/anomalous classification.
2. Given runtime inference input, when the inference path runs, then it consumes only valid downstream inputs derived from the approved persisted payload pipeline and it does not accept non-validated state as inference input.
3. Given the need to keep detection channels separate, when Story 4.3 produces inference output, then the result remains distinct from SCADA divergence and consensus-failure outputs.
4. Given the corrected Epic 4 sequencing, when Story 4.3 is implemented, then it builds on the persisted dataset artifact path introduced by Story 4.2A and the revalidated training path from Story 4.2.
5. Given the current adequacy-limited fingerprint base, when Story 4.3 outputs are produced, then the result explicitly carries the runtime-valid-only limitation and does not overclaim academically strong inference readiness.
6. Given focused validation, when Story 4.3 tests are run, then they prove:
   - score and classification output generation
   - persisted dataset artifact input use
   - distinction from SCADA outputs
   - rejection of schema-incompatible input
   - real runtime inference through the approved local ML and MinIO path
7. Given the project testing rule, when Story 4.3 is closed, then the story record explicitly includes:
   - what was tested
   - exact commands executed
   - test results
   - real runtime behavior validated
   - remaining limitations

## Dependencies

- Story 4.2A persisted dataset artifacts
- Story 4.2 revalidated trainer path
- Existing MinIO-backed object-store boundary

## Non-Goals

- no replay-specific detection logic yet
- no UI changes
- no scenario-control wiring
- no new storage service
- no architecture redesign

## Tasks / Subtasks

- [x] Define the Story 4.3 inference-output contract. (AC: 1, 3, 5, 6)
- [x] Implement model loading plus inference from the persisted dataset artifact path. (AC: 1, 2, 4, 6)
- [x] Implement explicit thresholding and normal/anomalous classification. (AC: 1, 5, 6)
- [x] Preserve explicit distinction between LSTM inference output and SCADA divergence output. (AC: 3, 6)
- [x] Add focused Story 4.3 tests and one real runtime inference validation pass. (AC: 6, 7)

## Technical Notes

- Story 4.3 must consume the persisted dataset artifact path rather than bypassing it with raw in-memory inputs.
- The current fingerprint limitation must be carried into the output surface so the prototype remains academically honest.
- The inference result should remain inspectable and machine-readable.

## Dev Agent Record

### Agent Model Used

GPT-5 Codex

### Debug Log References

- Story opened immediately after approved Story 4.2 revalidation.
- Runtime validation used the local MinIO path and the real `keras + torch` stack already installed for Epic 4.

### Completion Notes List

- Created the standalone Story 4.3 implementation artifact.
- Added a typed inference-result contract with explicit `lstm_fingerprint` output-channel separation.
- Implemented model loading plus inference from the persisted Story 4.2A dataset artifact path.
- Implemented deterministic anomaly scoring through reconstruction error.
- Implemented deterministic normal/anomalous classification through a source-dataset threshold derived from mean plus `3 * std`.
- Carried the runtime-valid-only adequacy limitation directly into the inference output surface.
- Added focused Story 4.3 tests for:
  - normal inference output
  - anomalous inference output
  - schema-mismatch rejection
- Added a gated real runtime smoke test that runs:
  - persisted dataset artifact generation
  - persisted-dataset-based training
  - persisted-dataset-based inference
  through MinIO and the real local ML stack.
- Implemented only Story 4.3.

### What Was Tested

- Focused Story 4.3 inference tests
- Existing Story 4.2 trainer tests
- Existing Story 4.2A dataset-artifact tests
- Combined affected regression surface for inference, trainer, and dataset artifacts
- Full regression suite
- Real MinIO-backed inference smoke validation through the persisted dataset artifact path

### Exact Commands Executed

```powershell
$env:PYTHONPATH='src'
.\.venv\Scripts\python -m unittest tests.lstm_service.test_inference
.\.venv\Scripts\python -m unittest tests.lstm_service.test_trainer
.\.venv\Scripts\python -m unittest tests.lstm_service.test_dataset_artifacts
.\.venv\Scripts\python -m unittest tests.lstm_service.test_inference tests.lstm_service.test_trainer tests.lstm_service.test_dataset_artifacts tests.lstm_service.test_dataset_builder

$env:RUN_REAL_ML_INFERENCE_SMOKE='1'
.\.venv\Scripts\python -m unittest tests.lstm_service.test_inference_runtime_smoke

@'
from minio import Minio
client = Minio('localhost:9000', access_key='minioadmin', secret_key='minioadmin', secure=False)
buckets = sorted([bucket.name for bucket in client.list_buckets() if bucket.name.startswith('valid-consensus-artifacts-inference-smoke-')])
latest = buckets[-1]
objects = sorted(obj.object_name for obj in client.list_objects(latest, recursive=True))
print('LATEST_BUCKET', latest)
print('OBJECT_COUNT', len(objects))
for name in objects:
    print(name)
'@ | .\.venv\Scripts\python -

$env:PYTHONPATH='src'
@'
from minio import Minio
from parallel_truth_fingerprint.lstm_service import run_lstm_fingerprint_inference_from_persisted_dataset
from parallel_truth_fingerprint.persistence import MinioArtifactStore, MinioStoreConfig
store_client = Minio('localhost:9000', access_key='minioadmin', secret_key='minioadmin', secure=False)
buckets = sorted([bucket.name for bucket in store_client.list_buckets() if bucket.name.startswith('valid-consensus-artifacts-inference-smoke-')])
latest = buckets[-1]
store = MinioArtifactStore(MinioStoreConfig(endpoint='localhost:9000', access_key='minioadmin', secret_key='minioadmin', bucket=latest, secure=False))
metadata_key = sorted(obj.object_name for obj in store_client.list_objects(latest, recursive=True) if obj.object_name.startswith('fingerprint-models/') and obj.object_name.endswith('.json'))[-1]
manifest_key = sorted(obj.object_name for obj in store_client.list_objects(latest, recursive=True) if obj.object_name.startswith('fingerprint-datasets/') and obj.object_name.endswith('.manifest.json'))[-1]
results = run_lstm_fingerprint_inference_from_persisted_dataset(model_metadata_object_key=metadata_key, inference_manifest_object_key=manifest_key, artifact_store=store)
first = results[0]
print('MODEL_METADATA_KEY', metadata_key)
print('MANIFEST_KEY', manifest_key)
print('WINDOW_ID', first.window_id)
print('ANOMALY_SCORE', first.anomaly_score)
print('THRESHOLD', first.classification_threshold)
print('CLASSIFICATION', first.classification.value)
print('VALIDATION_LEVEL', first.source_dataset_validation_level)
print('LIMITATION_NOTE', first.limitation_note)
'@ | .\.venv\Scripts\python -

.\.venv\Scripts\python -m unittest discover -s tests
```

### Test Results

- `tests.lstm_service.test_inference` -> `Ran 3 tests` -> `OK`
- `tests.lstm_service.test_trainer` -> `Ran 5 tests` -> `OK`
- `tests.lstm_service.test_dataset_artifacts` -> `Ran 3 tests` -> `OK`
- combined affected surface -> `Ran 15 tests` -> `OK`
- `tests.lstm_service.test_inference_runtime_smoke` -> `Ran 1 test` -> `OK`
- `python -m unittest discover -s tests` -> `Ran 97 tests` -> `OK (skipped=3)`

### Real Runtime Behavior Validated

- The real inference path loaded:
  - the persisted Story 4.2A dataset manifest
  - the persisted Story 4.2A `.npz` windows archive
  - the saved `.keras` fingerprint model artifact
- The real inference path consumed only persisted downstream dataset artifacts, not non-validated state.
- The latest inference smoke bucket contained:
  - 3 valid round artifacts
  - 2 persisted dataset artifacts under `fingerprint-datasets/`
  - 2 model artifacts under `fingerprint-models/`
- The live inference output produced:
  - `ANOMALY_SCORE`
  - `THRESHOLD`
  - `CLASSIFICATION`
  - `VALIDATION_LEVEL = runtime_valid_only`
  - the carried limitation note
- The inference output remained explicitly separate from SCADA outputs through `output_channel = lstm_fingerprint`.

### Remaining Limitations

- Story 4.3 runs on a runtime-valid but not yet meaningful-fingerprint-valid base.
- The current normal-history dataset still falls below the approved adequacy floor:
  - required 30 eligible artifacts
  - required 20 generated windows
- The runtime smoke corpus remained intentionally small and should not be overclaimed as academically strong inference evidence.
- Replay-specific anomaly validation is still pending for Story 4.4.

### File List

- `_bmad-output/implementation-artifacts/4-3-implement-fingerprint-inference-with-anomaly-score-and-classification.md`
- `README.md`
- `src/parallel_truth_fingerprint/contracts/__init__.py`
- `src/parallel_truth_fingerprint/contracts/fingerprint_inference.py`
- `src/parallel_truth_fingerprint/lstm_service/__init__.py`
- `src/parallel_truth_fingerprint/lstm_service/inference.py`
- `tests/lstm_service/test_inference.py`
- `tests/lstm_service/test_inference_runtime_smoke.py`
