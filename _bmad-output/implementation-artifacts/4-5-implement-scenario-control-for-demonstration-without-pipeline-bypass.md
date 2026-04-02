# Story 4.5: Implement Scenario-Control for Demonstration Without Pipeline Bypass

Status: review

## Story

As a researcher,
I want simple, explicit scenario controls for the live demo runtime,
so that I can trigger normal, SCADA replay/freeze, and edge-fault demonstration scenarios through the approved prototype pipeline without bypassing the architecture.

## Scope Notes

- This story is limited to scenario-control for demonstration.
- It must build on:
  - Story 4.3 continuous fingerprint inference
  - Story 4.3A continuous autonomous runtime loop and deferred fingerprint lifecycle
  - Story 4.4 replay-oriented anomaly behavior
- It must preserve the existing:
  - MinIO persistence boundary
  - dataset -> training -> model -> inference flow
  - continuous runtime lifecycle
- It must preserve explicit separation between:
  - SCADA divergence outputs
  - consensus status or failure outputs
  - LSTM fingerprint anomaly and replay behavior
- It must not add:
  - UI implementation
  - architecture redesign
  - a new service boundary
  - a new storage boundary
  - production-grade orchestration infrastructure

## Limitation Carried Forward

Story 4.5 must proceed on a runtime-valid but not yet meaningful-fingerprint-valid fingerprint base, because the current normal-history dataset still falls below the approved adequacy floor of 30 eligible artifacts and 20 generated windows.

## Acceptance Criteria

1. Given the autonomous runtime loop, when the prototype is started for demonstration, then scenario-control can select and activate approved demo scenarios without bypassing the normal runtime path.
2. Given the approved prototype boundary, when a scenario is activated, then it still flows through:
   - acquisition or simulation
   - MQTT exchange
   - consensus
   - SCADA comparison
   - valid-artifact persistence
   - persisted dataset handling
   - fingerprint training or inference lifecycle as already defined
3. Given demonstration needs, when scenario-control is used, then it supports a minimal explicit set of prototype scenarios such as:
   - normal runtime
   - SCADA replay or freeze runtime
   - existing edge-fault runtime modes already supported by the prototype
4. Given the need for transparency, when a scenario is active, then logs explicitly record:
   - active scenario
   - scenario start state or cycle
   - whether the scenario is training-eligible or excluded from training
   - which output channels are expected to react
5. Given the need to preserve output separation, when Story 4.5 is exercised, then scenario-control does not collapse:
   - SCADA divergence output
   - consensus-failure output
   - fingerprint anomaly or replay output
   into a single undifferentiated result.
6. Given the deferred fingerprint lifecycle from Story 4.3A, when scenarios are exercised over time, then the runtime still preserves:
   - no retraining every cycle
   - delayed training until the explicit history threshold
   - saved-model reuse on later cycles after a model exists
7. Given the current adequacy-limited fingerprint base, when Story 4.5 scenarios are demonstrated, then the runtime-valid-only limitation is carried forward explicitly and no academically strong fingerprint claim is made.
8. Given focused validation, when Story 4.5 tests are run, then they prove:
   - scenario selection works through the approved runtime path
   - scenarios do not bypass persistence, dataset, training, or inference boundaries
   - scenario labels and training eligibility metadata remain explicit
   - output-channel separation is preserved during scenario execution
   - real runtime validation of scenario-controlled demo behavior through the approved local stack
9. Given the project testing rule, when Story 4.5 is closed, then the story record explicitly includes:
   - what was tested
   - exact commands executed
   - test results
   - real runtime behavior validated
   - remaining limitations

## Testing Requirements

- Testing is mandatory for this story.
- The story is incomplete unless it includes:
  - focused tests for scenario selection and activation through the existing runtime path
  - focused tests that prove scenario labels and training eligibility remain explicit
  - focused tests that prove scenario-controlled runs preserve output separation
  - a real runtime validation pass proving scenario-controlled demo behavior can be exercised end-to-end through the approved local stack
  - a limitations note stating that the current fingerprint base remains runtime-valid only if the adequacy floor is still unmet

## Dependencies

- Story 4.2A persisted dataset artifacts
- Story 4.2 revalidated training path
- Story 4.3 fingerprint inference
- Story 4.3A continuous autonomous runtime loop and deferred fingerprint lifecycle
- Story 4.4 replay-oriented anomaly behavior
- Existing MinIO-backed persistence boundary

## Non-Goals

- no UI implementation
- no final dashboard or industrial demo screen
- no architecture redesign
- no new storage service
- no new service boundary
- no production-grade orchestration layer
- no new anomaly engine outside the current fingerprint path

## Tasks / Subtasks

- [x] Define the approved Story 4.5 scenario-control set and activation rules. (AC: 1, 3, 4, 8)
- [x] Implement simple scenario-control wiring through the existing autonomous runtime path. (AC: 1, 2, 6, 8)
- [x] Preserve explicit training-eligibility and scenario-label metadata during controlled runs. (AC: 2, 4, 8)
- [x] Preserve output-channel separation during scenario-controlled execution. (AC: 5, 6, 8)
- [x] Add focused Story 4.5 tests and one real runtime validation pass. (AC: 8, 9)

## Technical Notes

- Scenario-control should remain simple and prototype-oriented.
- It should prefer explicit configuration and runtime flags over new orchestration layers.
- Scenario-control in this story should orchestrate existing capabilities rather than inventing new analytics.
- The implementation should remain inspectable in logs and should make it easy to explain:
  - which scenario is active
  - which records are excluded from training
  - which output channel is reacting
- Story 4.5 should prepare the prototype for the final demonstration flow without absorbing UI scope.

## Real vs Simulated Boundary

- Real in this story:
  - continuous runtime loop
  - valid-artifact accumulation
  - persisted dataset path
  - model lifecycle reuse
  - scenario-control wiring through the approved runtime
  - output-channel separation
- Simulated or mock around this story:
  - compressor/process behavior
  - SCADA-side replay or freeze scenario generation
  - edge-fault scenario generation
- Conceptual only for later stories:
  - final UI layer
  - presentation polish beyond runtime scenario orchestration

## Academic Mapping

- This story ensures the prototype can demonstrate controlled scenarios honestly without bypassing the trusted pipeline.
- It preserves the conceptual distinction between:
  - process-side or logical-side scenario injection
  - consensus and SCADA validation behavior
  - fingerprint anomaly behavior
- It supports a defensible live demo by making scenario activation explicit, auditable, and reproducible while carrying forward the runtime-valid-only limitation.

## Dev Agent Record

### Agent Model Used

GPT-5 Codex

### Debug Log References

- Story 4.5 was implemented after the approved Story 4.4 review pass and keeps scenario-control as runtime orchestration, not analytics.
- The real runtime validation reused the existing MinIO boundary and the approved `keras + torch` local ML stack.

### Completion Notes List

- Added explicit runtime scenario-control in the existing `scenario_control` package.
- Added high-level scenario configuration support for:
  - `normal`
  - `scada_replay`
  - `scada_freeze`
  - `single_edge_exclusion`
  - `quorum_loss`
- Preserved the existing pipeline by applying scenario-control as per-cycle runtime overrides rather than creating a second execution path.
- Preserved explicit training eligibility metadata by routing scenario-control into persisted `dataset_context`.
- Preserved output separation by logging:
  - scenario-control state
  - SCADA runtime replay state
  - consensus output
  - SCADA divergence output
  - fingerprint inference output
  - replay behavior output
- Preserved deferred training and saved-model reuse from Story 4.3A and Story 4.4.
- Added focused tests for:
  - explicit scenario activation rules
  - legacy scenario fallback behavior
  - conflict rejection for ambiguous legacy scenario configuration
  - runtime-demo formatting and dataset-context precedence
- Added a gated real runtime smoke test proving:
  - scenario activation through the autonomous runtime shape
  - normal cycles before activation
  - replay activation at the configured cycle
  - replay output emitted through the existing fingerprint path
  - no pipeline bypass
- Updated the README so the demo scenario env vars and current Epic 4 state are honest.
- Implemented only Story 4.5.

### What Was Tested

- Focused Story 4.5 scenario-control tests
- Existing runtime-demo tests
- Existing Story 4.4 replay-behavior tests
- Existing Story 4.3A lifecycle tests
- Existing Story 4.3 inference tests
- Existing Story 4.2A dataset-artifact tests
- Existing persistence tests
- Full regression suite
- Real MinIO-backed and real `keras + torch` scenario-control smoke validation

### Exact Commands Executed

```powershell
$env:PYTHONPATH='src'
.\.venv\Scripts\python -m unittest tests.scenario_control.test_runtime tests.test_runtime_demo
.\.venv\Scripts\python -m unittest tests.lstm_service.test_replay_behavior tests.lstm_service.test_lifecycle tests.lstm_service.test_inference tests.persistence.test_service
.\.venv\Scripts\python -m unittest discover -s tests

venv\Scripts\uv.exe sync --extra ml-training
docker compose -f compose.local.yml up -d minio
Test-NetConnection 127.0.0.1 -Port 9000

$env:PYTHONPATH='src'
$env:RUN_REAL_SCENARIO_CONTROL_SMOKE='1'
.\.venv\Scripts\python -m unittest tests.scenario_control.test_runtime_smoke

$env:PYTHONPATH='src'
@'
from minio import Minio
client = Minio('localhost:9000', access_key='minioadmin', secret_key='minioadmin', secure=False)
latest = sorted(bucket.name for bucket in client.list_buckets() if bucket.name.startswith('scenario-control-smoke-'))[-1]
objects = sorted(obj.object_name for obj in client.list_objects(latest, recursive=True))
print('LATEST_BUCKET', latest)
print('OBJECT_COUNT', len(objects))
for name in objects:
    print(name)
'@ | .\.venv\Scripts\python -

$env:PYTHONPATH='src'
@'
import json
from minio import Minio
client = Minio('localhost:9000', access_key='minioadmin', secret_key='minioadmin', secure=False)
latest = sorted(bucket.name for bucket in client.list_buckets() if bucket.name.startswith('scenario-control-smoke-'))[-1]
manifest_name = sorted(obj.object_name for obj in client.list_objects(latest, recursive=True) if obj.object_name.endswith('.manifest.json') and 'replay-dataset::' in obj.object_name)[-1]
response = client.get_object(latest, manifest_name)
manifest = json.loads(response.read().decode('utf-8'))
print('LATEST_BUCKET', latest)
print('REPLAY_MANIFEST', manifest_name)
print('VALIDATION_LEVEL', manifest['adequacy_assessment']['validation_level'])
print('ELIGIBLE_ARTIFACT_COUNT', manifest['eligible_artifact_count'])
print('WINDOW_COUNT', manifest['window_count'])
'@ | .\.venv\Scripts\python -
```

### Test Results

- `tests.scenario_control.test_runtime tests.test_runtime_demo` -> `Ran 26 tests` -> `OK`
- `tests.lstm_service.test_replay_behavior tests.lstm_service.test_lifecycle tests.lstm_service.test_inference tests.persistence.test_service` -> `Ran 13 tests` -> `OK`
- `python -m unittest discover -s tests` -> `Ran 115 tests` -> `OK (skipped=6)`
- `tests.scenario_control.test_runtime_smoke` -> `Ran 1 test` -> `OK`

### Real Runtime Behavior Validated

- Story 4.5 scenario-control now selects and activates demo scenarios through the existing runtime path rather than bypassing persistence, dataset, training, or inference boundaries.
- The real Story 4.5 smoke run used:
  - three normal cycles before activation
  - one replay-controlled cycle at the configured start cycle
- The latest scenario-control smoke bucket was `scenario-control-smoke-20260402205515864632`.
- That bucket contained 10 objects:
  - 4 valid artifacts under `valid-consensus-artifacts/`
  - 2 dataset manifests under `fingerprint-datasets/`
  - 2 dataset archives under `fingerprint-datasets/`
  - 2 model artifacts under `fingerprint-models/`
- Live replay-manifest inspection confirmed:
  - `validation_level = runtime_valid_only`
  - `eligible_artifact_count = 2`
  - `window_count = 1`
- The real runtime smoke verified:
  - cycle 1 scenario-control state remained `normal` while `scada_replay` was configured for later activation
  - cycle 4 activated `scada_replay`
  - cycle 4 marked training as ineligible
  - cycle 4 preserved `training_events = ["reused"]`
  - cycle 4 emitted `replay_behavior.output_channel = scada_replay_behavior`
  - cycle 4 preserved expected reactive outputs:
    - `scada_divergence_alert`
    - `replay_behavior`
    - `fingerprint_inference`
- The runtime log payload recorded:
  - configured scenario
  - active scenario
  - start cycle
  - training eligibility
  - expected output channels

### Remaining Limitations

- Story 4.5 remains runtime-valid only, not yet meaningful-fingerprint-valid.
- The adequacy floor is still unmet:
  - required 30 eligible normal artifacts
  - required 20 generated windows
- The real scenario-control smoke corpus remained intentionally small:
  - 3 eligible normal training artifacts
  - 2 training windows
  - 1 replay evaluation window
- Story 4.5 does not add UI work or presentation polish; that remains Story 4.6.
- Story 4.5 does not add production-grade orchestration or a new control plane; it stays prototype-simple by design.

### File List

- `_bmad-output/implementation-artifacts/4-5-implement-scenario-control-for-demonstration-without-pipeline-bypass.md`
- `README.md`
- `scripts/run_local_demo.py`
- `src/parallel_truth_fingerprint/config/runtime.py`
- `src/parallel_truth_fingerprint/scenario_control/__init__.py`
- `src/parallel_truth_fingerprint/scenario_control/runtime.py`
- `tests/scenario_control/__init__.py`
- `tests/scenario_control/test_runtime.py`
- `tests/scenario_control/test_runtime_smoke.py`
- `tests/test_runtime_demo.py`
