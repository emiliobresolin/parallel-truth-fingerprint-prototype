# Story 4.3A: Add Continuous Autonomous Runtime Loop and Deferred Fingerprint Lifecycle

Status: review

## Story

As a researcher,
I want the prototype to run continuously on a recurring cadence, accumulate valid history over time, and manage fingerprint training/inference through an explicit deferred lifecycle,
so that the live demo can operate mostly autonomously while remaining technically coherent and academically honest.

## Rationale

- The current prototype can execute one full pipeline cycle successfully.
- The current runtime is still a bounded one-shot run and exits after that cycle.
- The live demo requires continuous operation, recurring artifact accumulation, delayed training after enough valid history exists, and later inference reuse without retraining every cycle.
- This is a runtime orchestration correction, not a new analytics story and not an architecture redesign.

## Scope Notes

- This story is limited to runtime orchestration and lifecycle timing.
- It must preserve the current architecture and data flow:
  - sensor simulation
  - edge acquisition
  - MQTT exchange
  - consensus
  - SCADA comparison
  - valid-artifact persistence to MinIO
  - persisted dataset artifact path
  - saved-model path
  - inference path
- It must preserve the existing MinIO persistence boundary.
- It must not add:
  - replay-specific anomaly logic
  - UI implementation
  - architecture redesign
  - a new storage path
  - a new service boundary

## Acceptance Criteria

1. Given the live demo runtime, when the prototype is started, then it keeps running continuously until manually stopped.
2. Given the recurring runtime requirement, when the prototype is active, then it executes the full pipeline on a configurable cadence.
3. Given the preferred demo rhythm, when cadence is configured, then the default cadence is approximately 1 minute, with a small configurable extension allowed for prototype practicality.
4. Given valid successful cycles, when the runtime continues over time, then valid artifacts keep accumulating in MinIO under the existing valid-artifact storage path and remain available as temporal history for later dataset-building and training.
5. Given the fingerprint lifecycle requirement, when the runtime is active, then fingerprint training does not run every cycle.
6. Given insufficient accumulated valid history, when the runtime evaluates whether training should occur, then training is explicitly deferred and the runtime records that state in logs.
7. Given an explicit minimum-history rule, when enough valid history has accumulated, then the runtime triggers fingerprint training once using the approved persisted dataset path.
8. Given a saved trained model already exists, when later runtime cycles complete, then inference may run using the saved model without retraining every cycle.
9. Given the live demo observability requirement, when the runtime is active, then logs explicitly show:
   - current cycle
   - cadence status
   - valid-artifact accumulation status
   - model status
   - whether training is deferred, started, completed, or reused
10. Given the current Epic 4 limitation, when Story 4.3A is implemented, then the runtime still carries forward the explicit statement that the current fingerprint base may remain runtime-valid only if the adequacy floor has not yet been met.
11. Given the approved sequencing, when Story 4.3A is implemented, then it preserves Story 4.4 as the replay/anomaly story and Story 4.6 as the UI story.
12. Given the project testing rule, when Story 4.3A is closed, then the story record explicitly includes:
   - what was tested
   - exact commands executed
   - test results
   - real runtime behavior validated
   - remaining limitations

## Testing Requirements

- Testing is mandatory for this story.
- The story is incomplete unless it includes:
  - focused tests for continuous-cycle orchestration logic
  - focused tests for deferred-training trigger logic
  - focused tests for saved-model reuse without per-cycle retraining
  - a runtime validation pass proving:
    - the loop keeps running until manually stopped
    - valid artifacts accumulate across cycles in MinIO
    - training is deferred before the threshold
    - training triggers once after the threshold
    - inference reuses the saved model later without retraining each cycle
  - a limitations note stating whether the fingerprint base is still runtime-valid only or has reached meaningful adequacy

## Dependencies

- Story 4.2A persisted dataset artifacts
- Story 4.2 revalidated training path
- Story 4.3 persisted-dataset-based inference path
- Existing MinIO-backed persistence boundary
- Existing local demo runtime path

## Non-Goals

- no replay-specific anomaly implementation
- no UI implementation
- no scenario-control implementation beyond what is required for the continuous runtime loop itself
- no new storage service
- no architecture redesign
- no production-grade job scheduler

## Tasks / Subtasks

- [x] Define the continuous autonomous runtime-loop behavior and lifecycle states. (AC: 1, 2, 5, 6, 7, 8, 9)
- [x] Add configurable recurring cadence settings with a demo-safe default. (AC: 2, 3, 9)
- [x] Implement continuous valid-artifact accumulation under the existing MinIO path. (AC: 4, 9)
- [x] Implement deferred fingerprint-training trigger after an explicit history threshold. (AC: 5, 6, 7, 9)
- [x] Implement saved-model reuse for inference on later cycles without retraining every cycle. (AC: 8, 9, 10)
- [x] Add focused Story 4.3A tests and one real runtime validation pass. (AC: 12)

## Technical Notes

- Acceptable prototype trigger examples include:
  - train once after 10 valid completed cycles
  - or train once after 10 minutes of valid accumulated history
- The trigger rule must be explicit, simple, and inspectable in logs.
- The lifecycle should remain easy to demonstrate and may use explicit states such as:
  - `no_model_yet`
  - `training_deferred`
  - `training_started`
  - `model_available`
  - `inference_reused_model`
- This story must not make replay behavior part of the runtime lifecycle logic itself; replay remains Story 4.4 scope.
- This story must not make UI behavior part of the runtime lifecycle logic itself; UI remains Story 4.6 scope.

## Real vs Simulated Boundary

- Real in this story:
  - continuous local runtime loop
  - recurring cadence execution
  - continuous valid-artifact persistence to MinIO
  - deferred model-training trigger
  - saved-model reuse for inference
  - runtime logs describing cycle and model state
- Simulated or mock around this story:
  - compressor/process behavior
  - sensor values
  - SCADA environment
- Conceptual only for later stories:
  - replay-specific anomaly demonstration
  - final UI layer

## Academic Mapping

- This story makes the prototype temporally alive during presentation rather than behaving as a one-shot script.
- It preserves a coherent distinction between:
  - continuous physical-operational data collection
  - continuous valid-artifact accumulation
  - deferred fingerprint training
  - later inference reuse
- It keeps the demo behavior honest by avoiding meaningless retraining on every cycle and by carrying forward the adequacy limitation explicitly.

## Dev Agent Record

### Agent Model Used

GPT-5 Codex

### Debug Log References

- Story implemented after the approved Epic 4 corrective planning pass that inserted Story 4.3A between Story 4.3 and Story 4.4.
- The real runtime validation used the existing local MinIO path plus the already approved `keras + torch` local ML stack.

### Completion Notes List

- Converted the bounded one-shot runtime into a continuous autonomous loop with configurable cadence and optional max-cycle bounds for tests.
- Added explicit runtime lifecycle orchestration that:
  - accumulates valid artifacts continuously in MinIO
  - defers fingerprint training until the eligible-history threshold is reached
  - trains once after the threshold
  - reuses the saved model for later-cycle inference without retraining every cycle
- Added compact and structured runtime logging for:
  - current cycle
  - cadence status
  - valid-artifact accumulation status
  - model status
  - training deferred, started, completed, or reused
- Preserved the corrected Story 4 dataset -> training -> model -> inference path and did not add replay logic, UI work, new services, or a new storage boundary.
- Added focused tests for:
  - deferred-training logic
  - one-time training trigger logic
  - saved-model reuse without retraining
  - recurring cadence loop behavior
  - manual-stop loop behavior
- Added a gated real runtime smoke test proving the Story 4.3A lifecycle against real MinIO and the real local ML stack.
- Implemented only Story 4.3A.

### What Was Tested

- Focused Story 4.3A lifecycle tests
- Focused runtime-demo tests for cadence and continuous loop behavior
- Focused runtime-demo test for manual-stop handling
- Existing Story 4.1 dataset-builder tests
- Existing Story 4.2A dataset-artifact tests
- Existing Story 4.2 trainer tests
- Existing Story 4.3 inference tests
- Existing persistence tests
- Full regression suite
- Real MinIO-backed and real `keras + torch` runtime lifecycle smoke validation

### Exact Commands Executed

```powershell
$env:PYTHONPATH='src'
.\.venv\Scripts\python -m unittest tests.lstm_service.test_lifecycle
.\.venv\Scripts\python -m unittest tests.test_runtime_demo
.\.venv\Scripts\python -m unittest tests.lstm_service.test_lifecycle tests.lstm_service.test_dataset_builder tests.lstm_service.test_dataset_artifacts tests.lstm_service.test_trainer tests.lstm_service.test_inference tests.persistence.test_service
.\.venv\Scripts\python -m unittest discover -s tests

venv\Scripts\uv.exe sync --extra ml-training
docker compose -f compose.local.yml up -d minio
Test-NetConnection 127.0.0.1 -Port 9000

$env:PYTHONPATH='src'
$env:RUN_REAL_RUNTIME_LIFECYCLE_SMOKE='1'
.\.venv\Scripts\python -m unittest tests.lstm_service.test_lifecycle_runtime_smoke

@'
from minio import Minio
client = Minio('localhost:9000', access_key='minioadmin', secret_key='minioadmin', secure=False)
latest = sorted(bucket.name for bucket in client.list_buckets() if bucket.name.startswith('runtime-lifecycle-smoke-'))[-1]
objects = sorted(obj.object_name for obj in client.list_objects(latest, recursive=True))
print('LATEST_BUCKET', latest)
print('OBJECT_COUNT', len(objects))
for name in objects:
    print(name)
'@ | .\.venv\Scripts\python -

@'
import json
from minio import Minio
client = Minio('localhost:9000', access_key='minioadmin', secret_key='minioadmin', secure=False)
latest = sorted(bucket.name for bucket in client.list_buckets() if bucket.name.startswith('runtime-lifecycle-smoke-'))[-1]
manifest_name = sorted(obj.object_name for obj in client.list_objects(latest, recursive=True) if obj.object_name.endswith('.manifest.json'))[-1]
metadata_name = sorted(obj.object_name for obj in client.list_objects(latest, recursive=True) if obj.object_name.startswith('fingerprint-models/') and obj.object_name.endswith('.json'))[-1]
manifest = json.loads(client.get_object(latest, manifest_name).read().decode('utf-8'))
metadata = json.loads(client.get_object(latest, metadata_name).read().decode('utf-8'))
print('MANIFEST_NAME', manifest_name)
print('VALIDATION_LEVEL', manifest['adequacy_assessment']['validation_level'])
print('ADEQUACY_MET', manifest['adequacy_assessment']['adequacy_met'])
print('ELIGIBLE_ARTIFACT_COUNT', manifest['eligible_artifact_count'])
print('WINDOW_COUNT', manifest['window_count'])
print('MODEL_METADATA_NAME', metadata_name)
print('SOURCE_DATASET_ID', metadata['source_dataset_id'])
print('TRAINING_WINDOW_COUNT', metadata['training_window_count'])
'@ | .\.venv\Scripts\python -
```

### Test Results

- `tests.lstm_service.test_lifecycle` -> `Ran 3 tests` -> `OK`
- `tests.test_runtime_demo` -> `Ran 21 tests` -> `OK`
- combined affected Story 4.3A surface -> `Ran 21 tests` -> `OK`
- `python -m unittest discover -s tests` -> `Ran 104 tests` -> `OK (skipped=4)`
- `tests.lstm_service.test_lifecycle_runtime_smoke` -> `Ran 1 test` -> `OK`

### Real Runtime Behavior Validated

- The Story 4.3A runtime loop completed four real cycles in the smoke validation and wrote continuous runtime state to the live JSON log.
- Valid artifacts accumulated continuously in MinIO under `valid-consensus-artifacts/` across those cycles.
- Training was deferred on the first two cycles because the eligible-history threshold had not yet been reached.
- Training started and completed exactly once on the third cycle when the threshold was reached.
- The fourth cycle reused the saved model and completed inference without retraining.
- The latest real smoke bucket was `runtime-lifecycle-smoke-20260402194457229458`.
- That bucket contained 10 objects:
  - 4 valid round artifacts under `valid-consensus-artifacts/`
  - 4 dataset artifacts under `fingerprint-datasets/`
  - 2 model artifacts under `fingerprint-models/`
- Live manifest inspection confirmed:
  - `validation_level = runtime_valid_only`
  - `adequacy_met = False`
  - `eligible_artifact_count = 4`
  - `window_count = 3`
- Live model-metadata inspection confirmed:
  - the model was trained from the first threshold-reaching dataset snapshot
  - `training_window_count = 2`

### Remaining Limitations

- Story 4.3A is runtime-valid but still not meaningful-fingerprint-valid because the adequacy floor remains unmet.
- The real smoke history remained intentionally small:
  - 4 eligible normal persisted artifacts
  - 3 generated windows
- The approved adequacy floor still requires:
  - 30 eligible artifacts
  - 20 generated windows
- Story 4.3A does not add replay-specific anomaly behavior, scenario-control orchestration, or UI work.
- The live demo loop now supports continuous cadence and deferred training, but Story 4.4 is still the place where replay/anomaly behavior must be implemented.

### File List

- `_bmad-output/implementation-artifacts/4-3a-add-continuous-autonomous-runtime-loop-and-deferred-fingerprint-lifecycle.md`
- `README.md`
- `scripts/run_local_demo.py`
- `src/parallel_truth_fingerprint/config/runtime.py`
- `src/parallel_truth_fingerprint/lstm_service/__init__.py`
- `src/parallel_truth_fingerprint/lstm_service/lifecycle.py`
- `tests/lstm_service/test_lifecycle.py`
- `tests/lstm_service/test_lifecycle_runtime_smoke.py`
- `tests/test_runtime_demo.py`
