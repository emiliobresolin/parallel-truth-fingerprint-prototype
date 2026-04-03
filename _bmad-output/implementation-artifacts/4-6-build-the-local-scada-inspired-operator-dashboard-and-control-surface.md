# Story 4.6: Build the Local SCADA-Inspired Operator Dashboard and Control Surface

Status: review

## Story

As a researcher and demo operator,
I want a local SCADA-inspired dashboard and control surface for the prototype,
so that I can start and stop the real runtime, trigger supported demo scenarios, control compressor operating level, and observe the full prototype behavior transparently through one operator-facing interface.

## Scope Notes

- This story is not only a presentation layer.
- It is the local operator dashboard and control surface for the real prototype flow.
- It must build on:
  - Story 4.3 fingerprint inference
  - Story 4.3A continuous autonomous runtime loop and deferred fingerprint lifecycle
  - Story 4.4 replay-oriented anomaly behavior
  - Story 4.5 scenario-control without pipeline bypass
- It must preserve the existing:
  - MinIO persistence boundary
  - dataset -> training -> model -> inference flow
  - continuous runtime lifecycle
  - scenario-control behavior
  - replay/anomaly behavior
- It must preserve explicit separation between:
  - SCADA divergence outputs
  - consensus status or failure outputs
  - LSTM fingerprint anomaly and replay behavior
- It may add minimal backend hooks only if needed to expose existing runtime, scenario-control, or compressor-control behavior honestly through the UI.
- It must not add:
  - architecture redesign
  - a new service boundary
  - a new storage boundary
  - production-grade HMI or industrial control infrastructure

## Limitation Carried Forward

Story 4.6 must proceed on a runtime-valid but not yet meaningful-fingerprint-valid fingerprint base, because the current normal-history dataset still falls below the approved adequacy floor of 30 eligible artifacts and 20 generated windows.

## Acceptance Criteria

1. Given the operator-control requirement, when the local dashboard is opened, then it can start the prototype runtime and stop the prototype runtime through the approved local runtime path.
2. Given runtime control, when the operator uses the dashboard, then the UI clearly shows whether the system is running or stopped.
3. Given the scenario-control requirement, when the operator uses the dashboard, then the UI can trigger the supported prototype demo scenarios through the existing runtime/scenario-control path without bypassing the architecture, including at minimum:
   - normal runtime
   - SCADA replay
   - SCADA freeze
   - existing edge-fault or reduced-edge or quorum-loss scenarios already supported by the prototype
   - SCADA divergence or other already supported demo scenarios where applicable
4. Given the transparency requirement, when the operator triggers a scenario or control action, then the UI explicitly shows:
   - which scenario or control was activated
   - when it started
   - which cycle it started on
   - what runtime command, configuration change, or state change was applied
   - which output channels are expected to react
5. Given the monitoring requirement, when the dashboard is active, then it exposes the current prototype state including at minimum:
   - runtime state
   - current cycle
   - cadence
   - active scenario
   - edge status
   - quorum or consensus status
   - sensor values
   - compressor state
   - valid-artifact accumulation
   - dataset, training, model, and inference lifecycle state
   - replay or anomaly outputs
6. Given the need to keep result channels distinct, when the dashboard shows runtime results, then it presents explicit separation between:
   - SCADA divergence
   - consensus status or failure
   - fingerprint anomaly or replay behavior
7. Given the process-control requirement, when the operator changes compressor power or operating level from the dashboard, then the real prototype runtime uses that setting and the resulting sensor values reflect process variation honestly rather than a UI-only effect.
8. Given long-running demo observability needs, when the runtime and dashboard are left running over short or extended observation windows, then the operator can observe:
   - artifact growth over time
   - training behavior over time
   - inference behavior over time
   - replay behavior over time
   - model lifecycle behavior over time
9. Given the current ML limitation, when the dashboard shows fingerprint behavior, then it explicitly carries the runtime-valid-only limitation and does not falsely present the current fingerprint base as academically strong or fully solved.
10. Given the compressor-power observation goal, when the operator changes process power over a range such as lower to higher operating levels, then the dashboard supports honest observation of whether the current LSTM behavior treats that variation as normal or anomalous, without falsely claiming that the question is already resolved if the adequacy floor remains unmet.
11. Given the current architecture, when Story 4.6 is implemented, then it reuses existing runtime, scenario-control, persistence, dataset, training, inference, and replay behavior rather than introducing a parallel execution path.
12. Given focused validation, when Story 4.6 tests are run, then they prove:
   - runtime start and stop behavior through the UI control path
   - scenario activation through the UI control path without pipeline bypass
   - compressor control through the UI control path
   - transparent operator feedback for control actions
   - monitoring visibility of runtime, artifacts, model lifecycle, and replay or anomaly outputs
   - preservation of result-channel separation
   - real runtime validation of the dashboard against the approved local stack
13. Given the project testing rule, when Story 4.6 is closed, then the story record explicitly includes:
   - what was tested
   - exact commands executed
   - test results
   - real runtime behavior validated
   - remaining limitations

## Testing Requirements

- Testing is mandatory for this story.
- The story is incomplete unless it includes:
  - focused tests for runtime start and stop from the dashboard control path
  - focused tests for scenario activation from the dashboard control path
  - focused tests for compressor power or operating-level control from the dashboard control path
  - focused tests for transparent operator feedback on scenario/control actions
  - focused tests for monitoring visibility and output-channel separation
  - a real runtime validation pass proving the dashboard can control and observe the approved local prototype stack end-to-end
  - a limitations note stating that the fingerprint base remains runtime-valid only if the adequacy floor is still unmet

## Dependencies

- Story 4.2A persisted dataset artifacts
- Story 4.2 revalidated training path
- Story 4.3 fingerprint inference
- Story 4.3A continuous autonomous runtime loop and deferred fingerprint lifecycle
- Story 4.4 replay-oriented anomaly behavior
- Story 4.5 scenario-control without pipeline bypass
- Existing MinIO-backed persistence boundary

## Non-Goals

- no architecture redesign
- no new storage service
- no new service boundary
- no production-grade SCADA or HMI platform
- no production-grade role-based access control
- no cloud deployment scope
- no claims of meaningful-fingerprint validity before the adequacy floor is met

## Tasks / Subtasks

- [x] Define the operator dashboard scope and control model for the current local prototype. (AC: 1, 2, 3, 4, 5, 6, 11, 12)
- [x] Implement runtime start and stop control through the approved local runtime path. (AC: 1, 2, 12)
- [x] Implement scenario activation control through the approved scenario-control path without pipeline bypass. (AC: 3, 4, 6, 11, 12)
- [x] Implement compressor power or operating-level control through the approved process/runtime path. (AC: 7, 10, 12)
- [x] Implement operator feedback and monitoring views for runtime, artifacts, lifecycle, and replay/anomaly state. (AC: 4, 5, 6, 8, 9, 10, 12)
- [x] Add focused Story 4.6 tests and one real runtime validation pass. (AC: 12, 13)

## Technical Notes

- Story 4.6 should be treated as the final local operator dashboard for the prototype, not only as a passive presentation screen.
- The UI should control the existing prototype honestly and should not simulate control effects purely inside the frontend.
- Any backend hooks added for UI control should stay minimal and should expose existing runtime or scenario-control capabilities rather than creating new orchestration layers.
- The dashboard should make the demo transparent by showing:
  - what the operator changed
  - when the change took effect
  - which cycle it affected
  - which output channels are expected to react
- The UI should support observation of ML behavior honestly, especially where the current adequacy-limited fingerprint base means conclusions remain provisional.

## Real vs Simulated Boundary

- Real in this story:
  - local runtime start and stop behavior
  - scenario-control activation through the approved runtime path
  - valid-artifact accumulation
  - persisted dataset path
  - saved-model reuse
  - inference and replay output monitoring
  - operator control of compressor power through the real prototype flow
- Simulated or mock around this story:
  - compressor/process behavior
  - SCADA environment
  - SCADA replay/freeze scenario generation
  - edge-fault scenario generation
- Conceptual only beyond this story:
  - production SCADA or HMI scope
  - production historian, fleet monitoring, and enterprise control integration

## Academic Mapping

- This story makes the final Epic 4 prototype demonstrable as an operator-controlled local system rather than only a collection of backend services and logs.
- It preserves a defensible distinction between:
  - runtime control and scenario control
  - consensus and SCADA validation behavior
  - fingerprint anomaly and replay behavior
- It supports honest experimental observation by allowing the operator to vary process inputs, trigger scenarios, and observe resulting runtime and ML behavior without overstating fingerprint maturity.

## Dev Agent Record

### Agent Model Used

GPT-5 Codex

### Debug Log References

- Story 4.6 was implemented as a local in-process dashboard/control surface on top of the existing runtime loop rather than as a new service.
- The real runtime validation reused the approved MinIO boundary and the real `keras + torch` local ML stack.

### Completion Notes List

- Added a local operator dashboard/control-surface package under `src/parallel_truth_fingerprint/dashboard/`.
- Added `scripts/run_local_dashboard.py` as the Story 4.6 launcher for the local UI.
- Preserved the existing runtime path by reusing `run_autonomous_demo_loop(...)` with minimal hooks:
  - dynamic config provider
  - stop request callback
  - per-cycle observer callback
- Added explicit runtime start/stop control through the dashboard.
- Added scenario activation through the existing Story 4.5 scenario-control path, including:
  - `normal`
  - `scada_replay`
  - `scada_freeze`
  - `scada_divergence`
  - `single_edge_exclusion`
  - `quorum_loss`
- Added honest compressor power control through the real simulator/runtime flow rather than a frontend-only effect.
- Added transparent operator feedback that records:
  - action type
  - timestamp
  - applied cycle
  - runtime command
  - configuration change
  - expected reactive output channels
- Added dashboard monitoring views for:
  - runtime state
  - current cycle and cadence
  - active scenario
  - compressor and sensor state
  - edge and consensus state
  - valid-artifact accumulation
  - lifecycle state
  - SCADA divergence / consensus / fingerprint inference / replay behavior as distinct channels
- Added minimal Story 4.6 runtime support for explicit `scada_divergence` via the existing SCADA offset capability.
- Preserved deferred training and saved-model reuse during dashboard-controlled execution.
- Updated the README so Epic 4 and the local dashboard/control path are described honestly.
- Implemented only Story 4.6.

### What Was Tested

- Focused Story 4.6 dashboard endpoint and UI-control-path tests
- Existing Story 4.5 scenario-control tests
- Existing runtime-demo tests
- Existing Story 4.4 replay-behavior tests
- Existing Story 4.3A lifecycle tests
- Existing Story 4.3 inference tests
- Existing persistence tests
- Full regression suite
- Real MinIO-backed and real `keras + torch` dashboard smoke validation

### Exact Commands Executed

```powershell
$env:PYTHONPATH='src'
.\.venv\Scripts\python -m unittest tests.dashboard.test_control_surface tests.scenario_control.test_runtime tests.test_runtime_demo
.\.venv\Scripts\python -m unittest tests.lstm_service.test_replay_behavior tests.lstm_service.test_lifecycle tests.lstm_service.test_inference tests.persistence.test_service
.\.venv\Scripts\python -m unittest discover -s tests

venv\Scripts\uv.exe sync --extra ml-training
docker compose -f compose.local.yml up -d minio
Test-NetConnection 127.0.0.1 -Port 9000

$env:PYTHONPATH='src'
$env:RUN_REAL_DASHBOARD_SMOKE='1'
.\.venv\Scripts\python -m unittest tests.dashboard.test_control_surface_runtime_smoke

@'
from minio import Minio
client = Minio('localhost:9000', access_key='minioadmin', secret_key='minioadmin', secure=False)
latest = sorted(bucket.name for bucket in client.list_buckets() if bucket.name.startswith('dashboard-smoke-'))[-1]
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
latest = sorted(bucket.name for bucket in client.list_buckets() if bucket.name.startswith('dashboard-smoke-'))[-1]
model_metadata_key = sorted(obj.object_name for obj in client.list_objects(latest, recursive=True) if obj.object_name.startswith('fingerprint-models/') and obj.object_name.endswith('.json'))[-1]
replay_manifest_key = sorted(obj.object_name for obj in client.list_objects(latest, recursive=True) if obj.object_name.endswith('.manifest.json') and 'replay-dataset::' in obj.object_name)[-1]
model_metadata = json.loads(client.get_object(latest, model_metadata_key).read().decode('utf-8'))
replay_manifest = json.loads(client.get_object(latest, replay_manifest_key).read().decode('utf-8'))
print('LATEST_BUCKET', latest)
print('MODEL_METADATA_KEY', model_metadata_key)
print('SOURCE_DATASET_ID', model_metadata['source_dataset_id'])
print('TRAINING_WINDOW_COUNT', model_metadata['training_window_count'])
print('REPLAY_MANIFEST_KEY', replay_manifest_key)
print('REPLAY_VALIDATION_LEVEL', replay_manifest['adequacy_assessment']['validation_level'])
print('REPLAY_WINDOW_COUNT', replay_manifest['window_count'])
'@ | .\.venv\Scripts\python -
```

### Test Results

- `tests.dashboard.test_control_surface tests.scenario_control.test_runtime tests.test_runtime_demo` -> `Ran 31 tests` -> `OK`
- `tests.lstm_service.test_replay_behavior tests.lstm_service.test_lifecycle tests.lstm_service.test_inference tests.persistence.test_service` -> `Ran 13 tests` -> `OK`
- `python -m unittest discover -s tests` -> `Ran 121 tests` -> `OK (skipped=7)`
- `tests.dashboard.test_control_surface_runtime_smoke` -> `Ran 1 test` -> `OK`

### Real Runtime Behavior Validated

- Story 4.6 now exposes the approved local prototype flow through a real local dashboard/control surface rather than a passive display only.
- The real Story 4.6 smoke run validated:
  - dashboard start of the autonomous runtime
  - dashboard stop of the autonomous runtime
  - dashboard power control before and during runtime
  - dashboard scenario activation during runtime through the approved Story 4.5 path
  - dashboard monitoring of lifecycle state and output-channel separation
  - no pipeline bypass
- The live dashboard smoke changed compressor operating level from `80%` to `20%` through the UI control path and the later-cycle simulator snapshot reflected the real operating-level change.
- The live dashboard smoke activated `scada_replay` after normal-history accumulation and the later cycle emitted:
  - replay output through the existing replay channel
  - fingerprint lifecycle `training_events = ["reused"]`
  - continued output separation between SCADA divergence, consensus, fingerprint inference, and replay behavior
- The latest dashboard smoke bucket was `dashboard-smoke-20260402222805751238`.
- That bucket contained `19` objects:
  - `7` valid artifacts under `valid-consensus-artifacts/`
  - `10` dataset artifacts under `fingerprint-datasets/`
  - `2` model artifacts under `fingerprint-models/`
- Live MinIO inspection confirmed:
  - model metadata source dataset id:
    - `training-dataset::round-dashboard-20260402222805751238-001::round-dashboard-20260402222805751238-003::seq-2`
  - `training_window_count = 2`
  - replay manifest validation level:
    - `runtime_valid_only`
  - replay manifest window count:
    - `1`

### Remaining Limitations

- Story 4.6 remains runtime-valid only, not yet meaningful-fingerprint-valid.
- The adequacy floor is still unmet:
  - required 30 eligible normal artifacts
  - required 20 generated windows
- The real dashboard smoke corpus remained intentionally small and prototype-oriented.
- The local dashboard is a prototype control surface, not a production SCADA/HMI platform.
- Story 4.6 completes Epic 4 at prototype scope, but it does not remove the current ML adequacy limitation.

### File List

- `_bmad-output/implementation-artifacts/4-6-build-the-local-scada-inspired-operator-dashboard-and-control-surface.md`
- `README.md`
- `scripts/run_local_dashboard.py`
- `scripts/run_local_demo.py`
- `src/parallel_truth_fingerprint/config/runtime.py`
- `src/parallel_truth_fingerprint/dashboard/__init__.py`
- `src/parallel_truth_fingerprint/dashboard/control_surface.py`
- `src/parallel_truth_fingerprint/lstm_service/replay_behavior.py`
- `src/parallel_truth_fingerprint/scenario_control/__init__.py`
- `src/parallel_truth_fingerprint/scenario_control/runtime.py`
- `tests/dashboard/__init__.py`
- `tests/dashboard/test_control_surface.py`
- `tests/dashboard/test_control_surface_runtime_smoke.py`
- `tests/lstm_service/test_lifecycle_runtime_smoke.py`
- `tests/scenario_control/test_runtime.py`
- `tests/scenario_control/test_runtime_smoke.py`
- `tests/test_runtime_demo.py`

## Stabilization Follow-up

- Fixed the real dashboard start path so the live runtime now completes cycles instead of stopping on the first CometBFT commit.
- Surfaced runtime health and active failure state as primary dashboard information.
- Clarified stopped-state control behavior so scenario/power changes are shown as configuration-only until the next start.
