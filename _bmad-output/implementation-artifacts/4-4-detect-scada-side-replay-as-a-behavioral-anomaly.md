# Story 4.4: Detect SCADA-Side Replay as a Behavioral Anomaly

Status: review

## Story

As a researcher,
I want SCADA-side replay, freeze, or reused-value behavior to surface as a behavioral anomaly through the existing fingerprint path,
so that the prototype can demonstrate replay-oriented temporal inconsistency without confusing it with SCADA divergence or consensus failure.

## Scope Notes

- This story is limited to replay-oriented anomaly behavior.
- It must build on:
  - Story 4.3 fingerprint inference
  - Story 4.3A continuous autonomous runtime loop and deferred fingerprint lifecycle
- It must preserve the existing:
  - MinIO persistence boundary
  - dataset -> training -> model -> inference flow
  - runtime loop and deferred-training lifecycle
- It must keep replay detection distinct from:
  - SCADA divergence outputs
  - consensus-failure outputs
  - generic LSTM inference outputs as a raw capability
- It must not add:
  - UI implementation
  - architecture redesign
  - a new service boundary
  - a new storage boundary
  - production-grade replay-detection infrastructure

## Limitation Carried Forward

Story 4.4 must proceed on a runtime-valid but not yet meaningful-fingerprint-valid fingerprint base, because the current normal-history dataset still falls below the approved adequacy floor of 30 eligible artifacts and 20 generated windows.

## Acceptance Criteria

1. Given the existing continuous runtime and fingerprint path, when a SCADA-side replay, freeze, or reused-value condition is introduced, then the prototype can route that scenario through the current operational pipeline without bypassing the approved architecture.
2. Given replay-oriented temporal inconsistency, when the fingerprint path evaluates later cycles, then the resulting anomaly behavior is surfaced through the existing LSTM inference channel.
3. Given the requirement to keep output channels distinct, when Story 4.4 emits replay-oriented anomaly behavior, then it remains separate from:
   - SCADA divergence outputs
   - consensus-failure outputs
   - generic inference plumbing details
4. Given the corrected Epic 4 sequencing, when Story 4.4 is implemented, then it builds on the already established persisted dataset, saved-model, inference, and autonomous runtime lifecycle paths rather than inventing a parallel path.
5. Given the current adequacy-limited fingerprint base, when Story 4.4 outputs are demonstrated, then the runtime-valid-only limitation is carried forward explicitly and the story does not overclaim academically strong replay detection.
6. Given focused validation, when Story 4.4 tests are run, then they prove:
   - replay or freeze scenario injection through the approved prototype path
   - anomaly behavior emitted through the fingerprint output channel
   - continued distinction between replay anomaly, SCADA divergence, and consensus failure
   - no retraining every cycle during replay-oriented runtime behavior
   - real runtime validation of replay-oriented anomaly behavior through the approved local stack
7. Given the project testing rule, when Story 4.4 is closed, then the story record explicitly includes:
   - what was tested
   - exact commands executed
   - test results
   - real runtime behavior validated
   - remaining limitations

## Testing Requirements

- Testing is mandatory for this story.
- The story is incomplete unless it includes:
  - focused tests for replay or freeze scenario handling through the existing runtime path
  - focused tests that validate anomaly behavior appears through the fingerprint channel
  - focused tests that prove replay results stay distinct from SCADA divergence and consensus-failure results
  - a real runtime validation pass proving replay-oriented behavior can be demonstrated end-to-end through the approved local stack
  - a limitations note stating the current fingerprint base remains runtime-valid only if the adequacy floor is still unmet

## Dependencies

- Story 4.2A persisted dataset artifacts
- Story 4.2 revalidated training path
- Story 4.3 fingerprint inference
- Story 4.3A continuous autonomous runtime loop and deferred fingerprint lifecycle
- Existing MinIO-backed persistence boundary

## Non-Goals

- no UI implementation
- no final dashboard or industrial demo screen
- no scenario-control UX expansion beyond what is necessary to exercise replay behavior
- no new storage service
- no new service boundary
- no architecture redesign

## Tasks / Subtasks

- [x] Define the replay-oriented anomaly contract and output separation rules. (AC: 2, 3, 5, 6)
- [x] Implement SCADA-side replay/freeze/reuse scenario handling through the approved runtime path. (AC: 1, 2, 4, 6)
- [x] Surface replay-oriented anomaly behavior through the existing fingerprint output channel without collapsing it into SCADA divergence or consensus failure. (AC: 2, 3, 6)
- [x] Preserve deferred-training behavior and saved-model reuse while replay scenarios are exercised. (AC: 4, 6)
- [x] Add focused Story 4.4 tests and one real runtime validation pass. (AC: 6, 7)

## Technical Notes

- Replay in this story should be treated as temporal reuse, freeze, or delayed reuse behavior on the SCADA side.
- Story 4.4 should use the current fingerprint path rather than inventing a second anomaly engine.
- The story should keep the behavioral interpretation explicit:
  - replay anomaly is not the same thing as SCADA divergence
  - replay anomaly is not the same thing as consensus failure
- Runtime output should remain inspectable and should clearly identify the replay-oriented anomaly path without overstating fingerprint strength.

## Real vs Simulated Boundary

- Real in this story:
  - local runtime loop
  - persisted valid-artifact accumulation
  - persisted dataset path
  - saved-model reuse
  - LSTM inference output channel
  - replay-oriented anomaly surfacing through the current runtime
- Simulated or mock around this story:
  - compressor/process behavior
  - SCADA-side replay, freeze, or reused-value scenario generation
- Conceptual only for later stories:
  - final UI layer
  - broader demo scenario-control polish

## Academic Mapping

- This story connects the fingerprint path to the dissertation claim that replay-oriented temporal inconsistency can be surfaced as behavioral anomaly rather than as simple value mismatch alone.
- It preserves the distinction between:
  - data-plane disagreement with SCADA
  - trust/consensus failure
  - temporal behavioral anomaly through the fingerprint path
- It keeps the prototype academically honest by carrying forward the runtime-valid-only limitation until the adequacy floor is met.

## Dev Agent Record

### Agent Model Used

GPT-5 Codex

### Debug Log References

- Story 4.4 was implemented after Story 4.3A, using the existing autonomous runtime lifecycle rather than introducing a second replay-detection path.
- The real runtime validation used the local MinIO boundary plus the approved `keras + torch` local ML stack.

### Completion Notes List

- Added a typed `ReplayBehaviorResult` contract with a distinct `scada_replay_behavior` output channel.
- Added replay/freeze runtime helpers that:
  - configure the stateful fake SCADA service for replay/freeze cycles
  - persist replay-oriented inference datasets under `fingerprint-datasets/`
  - reuse the existing saved-model inference path
- Routed SCADA replay/freeze through the approved runtime path without bypassing:
  - valid-artifact persistence
  - persisted dataset artifacts
  - saved-model reuse
- Marked replay-active cycles as non-normal in `dataset_context` so replay/freeze runs do not contaminate training history.
- Preserved deferred-training behavior and model reuse from Story 4.3A.
- Added a replay-specific sensitivity setting on top of the existing fingerprint path so the replay channel stays distinct from generic Story 4.3 inference behavior while still reusing the same model and persisted dataset flow.
- Added focused tests for:
  - replay-stage activation
  - replay dataset construction
  - freeze dataset construction
  - distinct replay-result wrapping over generic inference
- Added a gated real runtime smoke test that proves:
  - normal history accumulation
  - one-time model training
  - later replay-cycle model reuse
  - replay-specific anomaly classification through the distinct replay output channel
- Implemented only Story 4.4.

### What Was Tested

- Focused Story 4.4 replay-behavior tests
- Existing Story 4.3A runtime-demo tests
- Existing Story 4.3 inference tests
- Existing Story 4.2A dataset-artifact tests
- Existing Story 4.2 lifecycle tests
- Existing persistence tests
- Full regression suite
- Real MinIO-backed and real `keras + torch` replay-behavior smoke validation

### Exact Commands Executed

```powershell
$env:PYTHONPATH='src'
.\.venv\Scripts\python -m unittest tests.test_runtime_demo tests.lstm_service.test_replay_behavior
.\.venv\Scripts\python -m unittest tests.lstm_service.test_lifecycle tests.lstm_service.test_inference tests.lstm_service.test_dataset_artifacts tests.persistence.test_service
.\.venv\Scripts\python -m unittest discover -s tests

venv\Scripts\uv.exe sync --extra ml-training
docker compose -f compose.local.yml up -d minio
Test-NetConnection 127.0.0.1 -Port 9000

$env:PYTHONPATH='src'
$env:RUN_REAL_REPLAY_BEHAVIOR_SMOKE='1'
.\.venv\Scripts\python -m unittest tests.lstm_service.test_replay_behavior_runtime_smoke

$env:PYTHONPATH='src'
@'
from minio import Minio
client = Minio('localhost:9000', access_key='minioadmin', secret_key='minioadmin', secure=False)
buckets = sorted(bucket.name for bucket in client.list_buckets() if bucket.name.startswith('replay-behavior-smoke-'))
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
client = Minio('localhost:9000', access_key='minioadmin', secret_key='minioadmin', secure=False)
latest = sorted(bucket.name for bucket in client.list_buckets() if bucket.name.startswith('replay-behavior-smoke-'))[-1]
metadata_key = sorted(obj.object_name for obj in client.list_objects(latest, recursive=True) if obj.object_name.startswith('fingerprint-models/') and obj.object_name.endswith('.json'))[-1]
replay_manifest_key = sorted(obj.object_name for obj in client.list_objects(latest, recursive=True) if obj.object_name.endswith('.manifest.json') and 'replay-dataset::' in obj.object_name)[-1]
store = MinioArtifactStore(MinioStoreConfig(endpoint='localhost:9000', access_key='minioadmin', secret_key='minioadmin', bucket=latest, secure=False))
results = run_lstm_fingerprint_inference_from_persisted_dataset(model_metadata_object_key=metadata_key, inference_manifest_object_key=replay_manifest_key, artifact_store=store, threshold_stddev_multiplier=0.0)
first = results[0]
print('LATEST_BUCKET', latest)
print('MODEL_METADATA_KEY', metadata_key)
print('REPLAY_MANIFEST_KEY', replay_manifest_key)
print('CLASSIFICATION', first.classification.value)
print('ANOMALY_SCORE', first.anomaly_score)
print('THRESHOLD', first.classification_threshold)
print('VALIDATION_LEVEL', first.source_dataset_validation_level)
print('LIMITATION_NOTE', first.limitation_note)
'@ | .\.venv\Scripts\python -
```

### Test Results

- `tests.test_runtime_demo tests.lstm_service.test_replay_behavior` -> `Ran 25 tests` -> `OK`
- `tests.lstm_service.test_lifecycle tests.lstm_service.test_inference tests.lstm_service.test_dataset_artifacts tests.persistence.test_service` -> `Ran 12 tests` -> `OK`
- `python -m unittest discover -s tests` -> `Ran 109 tests` -> `OK (skipped=5)`
- `tests.lstm_service.test_replay_behavior_runtime_smoke` -> `Ran 1 test` -> `OK`

### Real Runtime Behavior Validated

- Replay/freeze handling now uses the approved runtime path and does not bypass:
  - valid-artifact persistence
  - persisted dataset artifact generation
  - saved-model inference
- Replay-active cycles are persisted as valid artifacts but explicitly marked non-normal in `dataset_context`.
- The real Story 4.4 smoke run trained a model once from three normal cycles, then reused that saved model on the replay cycle without retraining.
- The latest replay smoke bucket was `replay-behavior-smoke-20260402203104848048`.
- That bucket contained:
  - 4 valid round artifacts under `valid-consensus-artifacts/`
  - 2 dataset manifests under `fingerprint-datasets/`
  - 2 dataset archives under `fingerprint-datasets/`
  - 2 model artifacts under `fingerprint-models/`
- Live replay-manifest inspection confirmed:
  - `validation_level = runtime_valid_only`
  - `eligible_artifact_count = 2`
  - `window_count = 1`
- Live replay inference inspection confirmed:
  - `CLASSIFICATION = anomalous`
  - `ANOMALY_SCORE = 185638.71875`
  - `THRESHOLD = 167122.4921875`
  - `VALIDATION_LEVEL = runtime_valid_only`
- The replay output remained distinct from:
  - SCADA divergence, which still surfaced through `comparison_output` / `scada_alert`
  - consensus status, which remained `success`
  - generic inference plumbing, which still used `output_channel = lstm_fingerprint`
- Story 4.4 preserved deferred training and saved-model reuse; it did not retrain every replay cycle.

### Remaining Limitations

- Story 4.4 remains runtime-valid only, not yet meaningful-fingerprint-valid.
- The approved adequacy floor is still unmet:
  - required 30 eligible normal artifacts
  - required 20 generated windows
- The real replay smoke corpus remained intentionally small:
  - 3 eligible normal training artifacts
  - 2 training windows
  - 1 replay evaluation window
- Replay behavior is demonstrated through the approved local stack, but it should not yet be presented as academically strong replay detection evidence.
- Story 4.4 does not add UI work, scenario-control polish, or production-grade replay infrastructure.

### File List

- `_bmad-output/implementation-artifacts/4-4-detect-scada-side-replay-as-a-behavioral-anomaly.md`
- `scripts/run_local_demo.py`
- `src/parallel_truth_fingerprint/config/runtime.py`
- `src/parallel_truth_fingerprint/contracts/__init__.py`
- `src/parallel_truth_fingerprint/contracts/replay_behavior.py`
- `src/parallel_truth_fingerprint/lstm_service/__init__.py`
- `src/parallel_truth_fingerprint/lstm_service/replay_behavior.py`
- `tests/lstm_service/test_replay_behavior.py`
- `tests/lstm_service/test_replay_behavior_runtime_smoke.py`
- `tests/test_runtime_demo.py`
