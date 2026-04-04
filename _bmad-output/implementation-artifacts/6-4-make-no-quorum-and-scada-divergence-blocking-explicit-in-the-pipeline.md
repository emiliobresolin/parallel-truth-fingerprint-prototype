# Story 6.4: Make No-Quorum and SCADA-Divergence Blocking Explicit in the Pipeline

Status: review

## Story

As a researcher and demo operator,
I want no-quorum and SCADA-divergence outcomes to appear as explicit blocking decisions in the pipeline,
so that the prototype clearly shows why a cycle was stopped and why no payload was forwarded downstream.

## Scope Notes

- This story is limited to making two already-intended blocking behaviors explicit and coherent in the live prototype:
  - no quorum / majority not reached
  - SCADA divergence on supervisory values
- It must preserve the five real pillars exactly as they already exist:
  - acquisition of sensor values
  - decentralization across edges
  - Byzantine consensus across edges
  - comparison between consensused data and SCADA data
  - LSTM-based fingerprint generation
- It must preserve the current architecture:
  - no new backend services
  - no new storage boundary
  - no fake UI-only behavior
  - no new anomaly engine
- It must keep the SCADA comparison rule narrow:
  - compare only temperature, pressure, and rpm
- It must make the blocked downstream behavior visible and honest in:
  - runtime state
  - dashboard messaging
  - persisted and non-persisted outcomes for the affected cycle

## Acceptance Criteria

1. Given the distributed-validation requirement, when valid participants remaining after exclusions fall below quorum, then the prototype emits an explicit no-quorum alert in the consensus stage and explains that no trusted payload was produced because majority was not reached.
2. Given the blocked-forwarding rule for failed consensus, when no quorum is reached, then that cycle does not advance to:
   - SCADA comparison
   - valid-artifact persistence
   - downstream fingerprint evaluation
   and the dashboard shows this as a deliberate security decision rather than a generic runtime failure.
3. Given the supervisory-validation boundary, when SCADA comparison is executed, then the divergence decision is based only on:
   - temperature
   - pressure
   - rpm
   even if the SCADA-side payload carries richer contextual fields for later-stage fingerprint evaluation.
4. Given the SCADA-integrity rule, when any of those supervisory values diverge beyond tolerance, then the prototype emits a SCADA-divergence alert and blocks that cycle from progressing further downstream.
5. Given the persistence-integrity rule, when a cycle is blocked by SCADA divergence, then no downstream-valid artifact for fingerprint use is treated as approved output for that cycle.
6. Given the alert-separation requirement, when no-quorum, SCADA divergence, and fingerprint anomaly are displayed, then they remain visually and semantically distinct:
   - no quorum = distributed validation refused to produce trusted data
   - SCADA divergence = supervisory values do not match the trusted committed state
   - fingerprint anomaly = behavioral inconsistency detected after trusted and supervisory checks
7. Given the operator-facing wording requirement, when the blocking state is shown in the dashboard, then it uses domain language such as no quorum reached, trusted payload not forwarded, or SCADA divergence blocked the cycle and does not reference internal story labels.
8. Given focused validation, when this story is closed, then tests and one real runtime validation pass prove that:
   - no-quorum cycles do not advance
   - SCADA-divergence cycles do not advance
   - alerts are distinct
   - the dashboard explains the block reason correctly
9. Given the project testing-closeout rule, when Story 6.4 is closed, then the story record explicitly includes:
   - what was tested
   - exact commands executed
   - test results
   - real runtime behavior validated
   - remaining limitations

## Testing Requirements

- Testing is mandatory for this story.
- The story is incomplete unless it includes:
  - focused tests for no-quorum alert derivation and blocked progression
  - focused tests for SCADA-divergence alert derivation and blocked progression
  - focused tests that keep no-quorum, SCADA divergence, and fingerprint anomaly distinct
  - focused dashboard tests for honest operator-facing blocking messages
  - one real runtime validation pass confirming that blocked cycles do not silently continue downstream

## Dependencies

- Story 2.2 Byzantine consensus evaluation
- Story 2.3 failed-consensus handling
- Story 3.2 SCADA comparison
- Story 3.3 structured SCADA alerts
- Story 3.4 valid-state persistence
- Story 4.3A continuous runtime loop
- Story 4.6 local operator dashboard
- Story 6.2 dashboard semantic/state correction
- Story 6.3 dashboard structural reorganization

## Non-Goals

- no new consensus algorithm
- no widened SCADA comparison engine
- no new persistence boundary
- no new fingerprint model logic
- no attempt to redesign the runtime architecture

## Tasks / Subtasks

- [x] Derive and surface an explicit no-quorum blocking state from the existing consensus outputs. (AC: 1, 2, 6, 7)
- [x] Enforce SCADA-divergence blocking semantics in the live pipeline while preserving the narrow comparison rule. (AC: 3, 4, 5)
- [x] Update dashboard runtime and pipeline views so blocked cycles are explained as deliberate validation decisions. (AC: 2, 6, 7)
- [ ] Add focused automated tests and one real runtime validation pass. (AC: 8, 9)

## Technical Notes

- The consensus engine already distinguishes successful and failed consensus; this story should expose the no-quorum case as an explicit trusted-state blocking decision rather than inventing a new trust model.
- The SCADA comparison service already compares only temperature, pressure, and rpm. That narrow rule should stay intact.
- The current runtime flow allows SCADA divergence to remain a visible alert while still persisting a valid-consensus artifact. This story intentionally tightens that gating behavior for demo correctness.
- Blocked cycles must remain inspectable in logs and runtime state even when nothing is forwarded downstream.

## Real vs Simulated Boundary

- Real in this story:
  - consensus quorum evaluation
  - SCADA comparison on supervisory values
  - runtime blocking and persistence outcomes
  - dashboard alerting and stage visibility
- Simulated or controlled in this story:
  - compressor/process behavior
  - injected edge faults
  - fake SCADA environment

## Academic Mapping

- This story does not add new research scope.
- It strengthens the academic demonstrability of the prototype by making two security and validation decisions explicit:
  - distributed validation refusal when no quorum is reached
  - supervisory-validation refusal when SCADA diverges from trusted committed state

## Dev Agent Record

### Agent Model Used

GPT-5 Codex

### Debug Log References

- `logs/story-6-4-no-quorum-20260403.json`
- `logs/story-6-4-scada-divergence-20260403.json`

### Completion Notes List

- No-quorum cycles now surface an explicit consensus-stage blocking reason and do not create downstream comparison, persistence, or fingerprint results.
- SCADA divergence now blocks downstream persistence and fingerprint evaluation for that cycle instead of silently allowing approved artifact flow.
- Dashboard runtime notes, pipeline cards, channel badges, guidance text, and component timelines all explain blocked cycles as deliberate validation decisions.
- Story-adjacent replay and scenario-control smokes were updated to reflect the interim 6.4 behavior, where replay remains blocked by the SCADA supervisory gate until Story 6.5 changes the replay payload semantics.

### What Was Tested

- `python -m py_compile` on changed runtime/dashboard/test files
- Focused unit coverage for runtime gating, dashboard pipeline/event wording, and scenario-output expectations
- Real MinIO-backed dashboard/scenario/replay smokes with the Story 6.4 blocked-cycle semantics
- Full `unittest` regression suite
- Direct CLI live runtime attempts for `quorum_loss` and `scada_divergence` scenarios

### Exact Commands Executed

```powershell
$env:PYTHONPATH='src'
.\.venv\Scripts\python -m py_compile scripts\run_local_demo.py src\parallel_truth_fingerprint\dashboard\control_surface.py src\parallel_truth_fingerprint\dashboard\event_timeline.py src\parallel_truth_fingerprint\dashboard\pipeline_view.py src\parallel_truth_fingerprint\dashboard\guidance_view.py src\parallel_truth_fingerprint\dashboard\evidence_view.py src\parallel_truth_fingerprint\scenario_control\runtime.py tests\test_runtime_demo.py tests\dashboard\test_control_surface.py tests\dashboard\test_control_surface_runtime_smoke.py tests\dashboard\test_pipeline_view.py tests\scenario_control\test_runtime.py tests\scenario_control\test_runtime_smoke.py tests\lstm_service\test_replay_behavior_runtime_smoke.py
```

```powershell
$env:PYTHONPATH='src'
.\.venv\Scripts\python -m unittest tests.test_runtime_demo tests.dashboard.test_pipeline_view tests.dashboard.test_event_timeline tests.scenario_control.test_runtime
```

```powershell
$env:PYTHONPATH='src'
.\.venv\Scripts\python -m unittest tests.dashboard.test_control_surface tests.dashboard.test_evidence_view tests.dashboard.test_guidance_view tests.dashboard.test_control_surface_runtime_smoke tests.scenario_control.test_runtime_smoke
```

```powershell
$env:PYTHONPATH='src'
.\.venv\Scripts\python -m unittest tests.lstm_service.test_replay_behavior_runtime_smoke tests.lstm_service.test_replay_behavior tests.lstm_service.test_inference_runtime_smoke
```

```powershell
docker compose -f compose.local.yml up -d mqtt-broker minio
& .\scripts\init_cometbft_testnet.ps1
docker compose -f compose.consensus.yml up -d --force-recreate
```

```powershell
$env:PYTHONPATH='src'
$env:MINIO_BUCKET='story-6-4-no-quorum-20260403'
$env:DEMO_LOG_PATH='logs/story-6-4-no-quorum-20260403.json'
$env:DEMO_MAX_CYCLES='1'
$env:DEMO_CYCLE_INTERVAL_SECONDS='1'
$env:DEMO_SCENARIO='quorum_loss'
$env:DEMO_SCENARIO_START_CYCLE='1'
.\.venv\Scripts\python scripts\run_local_demo.py
```

```powershell
$env:PYTHONPATH='src'
$env:MINIO_BUCKET='story-6-4-scada-divergence-20260403'
$env:DEMO_LOG_PATH='logs/story-6-4-scada-divergence-20260403.json'
$env:DEMO_MAX_CYCLES='1'
$env:DEMO_CYCLE_INTERVAL_SECONDS='1'
$env:DEMO_SCENARIO='scada_divergence'
$env:DEMO_SCENARIO_START_CYCLE='1'
.\.venv\Scripts\python scripts\run_local_demo.py
```

```powershell
$env:PYTHONPATH='src'
$env:RUN_REAL_DASHBOARD_SMOKE='1'
.\.venv\Scripts\python -m unittest tests.dashboard.test_control_surface_runtime_smoke
```

```powershell
$env:PYTHONPATH='src'
$env:RUN_REAL_SCENARIO_CONTROL_SMOKE='1'
.\.venv\Scripts\python -m unittest tests.scenario_control.test_runtime_smoke
```

```powershell
$env:PYTHONPATH='src'
$env:RUN_REAL_REPLAY_BEHAVIOR_SMOKE='1'
.\.venv\Scripts\python -m unittest tests.lstm_service.test_replay_behavior_runtime_smoke
```

```powershell
$env:PYTHONPATH='src'
.\.venv\Scripts\python -m unittest discover -s tests
```

### Test Results

- `tests.test_runtime_demo tests.dashboard.test_pipeline_view tests.dashboard.test_event_timeline tests.scenario_control.test_runtime` -> `Ran 37 tests` -> `OK`
- `tests.dashboard.test_control_surface tests.dashboard.test_evidence_view tests.dashboard.test_guidance_view tests.dashboard.test_control_surface_runtime_smoke tests.scenario_control.test_runtime_smoke` -> `Ran 14 tests` -> `OK (skipped=2)`
- `tests.lstm_service.test_replay_behavior_runtime_smoke tests.lstm_service.test_replay_behavior tests.lstm_service.test_inference_runtime_smoke` -> `Ran 6 tests` -> `OK (skipped=2)`
- `tests.dashboard.test_control_surface_runtime_smoke` with `RUN_REAL_DASHBOARD_SMOKE=1` -> `Ran 1 test` -> `OK`
- `tests.scenario_control.test_runtime_smoke` with `RUN_REAL_SCENARIO_CONTROL_SMOKE=1` -> `Ran 1 test` -> `OK`
- `tests.lstm_service.test_replay_behavior_runtime_smoke` with `RUN_REAL_REPLAY_BEHAVIOR_SMOKE=1` -> `Ran 1 test` -> `OK`
- `python -m unittest discover -s tests` -> `Ran 139 tests` -> `OK (skipped=7)`

### Real Runtime Behavior Validated

- The updated blocked-cycle semantics were validated through the real MinIO-backed dashboard, scenario-control, and replay smokes.
- Two direct CLI live-runtime attempts were executed against the local CometBFT stack:
  - `quorum_loss`
  - `scada_divergence`
- Both direct CLI attempts failed before cycle execution with `CometBFT RPC call failed ... timed out waiting for tx to be included in a block`, so the fully live consensus path is still an environment blocker outside this story’s pipeline-gating code.

### Remaining Limitations

- The fully live CLI runtime validation path is still blocked by the current CometBFT timeout before the cycle logic runs.
- Replay remains blocked at the SCADA supervisory gate in the current architecture; Story 6.5 is still needed to make replay demonstrably fingerprint-first on richer SCADA-side payload.
- The fingerprint readiness limitation remains unchanged: runtime-valid evidence is available, but stronger adequacy still depends on accumulating enough normal-history artifacts/windows.

### File List

- `scripts/run_local_demo.py`
- `src/parallel_truth_fingerprint/dashboard/control_surface.py`
- `src/parallel_truth_fingerprint/dashboard/event_timeline.py`
- `src/parallel_truth_fingerprint/dashboard/evidence_view.py`
- `src/parallel_truth_fingerprint/dashboard/guidance_view.py`
- `src/parallel_truth_fingerprint/dashboard/pipeline_view.py`
- `src/parallel_truth_fingerprint/scenario_control/runtime.py`
- `tests/dashboard/test_control_surface.py`
- `tests/dashboard/test_control_surface_runtime_smoke.py`
- `tests/dashboard/test_event_timeline.py`
- `tests/dashboard/test_pipeline_view.py`
- `tests/lstm_service/test_replay_behavior_runtime_smoke.py`
- `tests/scenario_control/test_runtime.py`
- `tests/scenario_control/test_runtime_smoke.py`
- `tests/test_runtime_demo.py`

### Change Log

- 2026-04-03: Story created and marked ready-for-dev.
- 2026-04-03: Implemented explicit no-quorum and SCADA-divergence blocking semantics across runtime, dashboard, and story-adjacent tests; left the final fully live CLI validation marked as blocked by the current CometBFT timeout.
