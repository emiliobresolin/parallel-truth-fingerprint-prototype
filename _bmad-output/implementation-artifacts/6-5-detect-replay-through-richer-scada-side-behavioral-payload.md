# Story 6.5: Detect Replay Through Richer SCADA-Side Behavioral Payload

Status: ready-for-qa

## Story

As a researcher and demo operator,
I want replay behavior to be evaluated from a richer SCADA-side behavioral payload while keeping the simple SCADA comparison rule narrow,
so that replay can be demonstrated as a fingerprint-level anomaly rather than only as an obvious supervisory mismatch.

## Scope Notes

- This story is limited to a bounded replay-behavior correction within the existing prototype architecture.
- It must preserve the five real pillars exactly as they already exist:
  - acquisition of sensor values
  - decentralization across edges
  - Byzantine consensus across edges
  - comparison between consensused data and SCADA data
  - LSTM-based fingerprint generation
- It must keep the SCADA-comparison rule narrow:
  - temperature
  - pressure
  - rpm
- It must not add:
  - a new anomaly engine
  - a new ML model family
  - a new service
  - a new storage boundary
  - a new research scope
- It must make the richer SCADA-side payload real in the prototype for replay evaluation, not just described in demo narration.

## Acceptance Criteria

1. Given the SCADA-side contract requirement, when the fake SCADA stage projects its runtime state, then it carries:
   - the three supervisory values used for SCADA comparison
   - richer behavioral and contextual fields needed for replay-oriented fingerprint evaluation
   and those richer fields remain distinct from the narrow supervisory comparison rule.
2. Given the comparison-boundary rule, when SCADA divergence is decided, then the decision still uses only:
   - temperature
   - pressure
   - rpm
   and does not widen into a richer multi-field comparison engine.
3. Given the replay-scenario requirement, when SCADA replay is activated after normal history exists, then the replayed SCADA-side state can preserve or reintroduce stale behavioral detail while top-level supervisory values may still remain plausible enough to avoid mandatory SCADA divergence.
4. Given the fingerprint-path requirement, when replay behavior is evaluated, then the anomaly decision is driven by the fingerprint or replay-behavior stage using the richer SCADA-side payload rather than only by replaying a previously persisted valid-consensus artifact.
5. Given the alert-separation requirement, when replay occurs, then replay success is defined by the fingerprint-side anomaly output and remains distinct from:
   - no-quorum alerts
   - SCADA-divergence alerts
   - generic runtime failures
6. Given the training-integrity rule, when replay cycles occur, then they remain excluded from normal training and the existing saved-model reuse flow remains intact unless an explicit later story changes it.
7. Given the operator-facing wording requirement, when replay is shown in the dashboard, then the UI explains it as a behavioral inconsistency detected through the fingerprint path and does not describe it as merely a SCADA mismatch.
8. Given focused validation, when this story is closed, then tests and one real runtime validation pass prove that replay can be surfaced through the fingerprint path while consensus still succeeds and SCADA divergence is not required to demonstrate the replay anomaly.
9. Given the project testing-closeout rule, when Story 6.5 is closed, then the story record explicitly includes:
   - what was tested
   - exact commands executed
   - test results
   - real runtime behavior validated
   - remaining limitations

## Testing Requirements

- Testing is mandatory for this story.
- The story is incomplete unless it includes:
  - focused tests for richer SCADA-side payload projection
  - focused tests proving SCADA comparison still only uses the three supervisory values
  - focused replay tests proving fingerprint anomaly can surface without requiring SCADA divergence
  - focused dashboard tests proving replay messaging stays distinct from divergence and no-quorum
  - one real runtime validation pass confirming replay is demonstrated through the fingerprint path

## Dependencies

- Story 3.1 fake OPC UA SCADA service
- Story 3.2 SCADA comparison
- Story 4.1 feature extraction and dataset building
- Story 4.3 fingerprint inference
- Story 4.4 replay-oriented anomaly behavior
- Story 4.5 scenario control
- Story 4.6 local operator dashboard
- Story 6.1 fingerprint readiness evidence
- Story 6.4 explicit blocking semantics for no-quorum and SCADA divergence

## Non-Goals

- no widened SCADA divergence rule
- no new replay scenario families
- no new anomaly engine or model family
- no architecture redesign
- no claim that the replay source is a real industrial attacker

## Tasks / Subtasks

- [x] Extend the SCADA-side runtime contract so replay evaluation has access to richer behavioral payload fields while preserving the narrow supervisory comparison rule. (AC: 1, 2)
- [x] Re-anchor replay evaluation to the richer SCADA-side payload instead of relying only on replayed valid-consensus artifacts. (AC: 3, 4, 5)
- [x] Update dashboard wording and evidence so replay is shown as a fingerprint-side behavioral anomaly distinct from SCADA divergence and no-quorum. (AC: 5, 7)
- [x] Add focused automated tests and one real runtime validation pass. (AC: 8, 9)

## Technical Notes

- The current comparison service is already narrow and should remain narrow.
- The current replay behavior path is real, but it is still too tightly coupled to replayed valid-consensus artifacts for the stronger demo claim now desired.
- This story should make the richer SCADA-side payload explicit and real in the prototype rather than implying it informally in the demo.
- Replay cycles must continue to be excluded from normal training data.

## Real vs Simulated Boundary

- Real in this story:
  - SCADA-side runtime contract and payload projection
  - replay scenario-control path
  - fingerprint inference and replay-behavior output
  - dashboard evidence and alert separation
- Simulated or controlled in this story:
  - attacker behavior
  - SCADA replay injection
  - compressor/process behavior

## Academic Mapping

- This story does not add a new research pillar.
- It strengthens the replay demonstration so the prototype can show:
  - a narrow supervisory comparison on main SCADA values
  - a richer behavioral inconsistency detected by the fingerprint path
- That keeps replay distinct from both SCADA divergence and no-quorum behavior.

## Dev Agent Record

### Agent Model Used

GPT-5 Codex

### Debug Log References

- Focused unit and smoke validation were run from the local repo with `PYTHONPATH=src`.
- Real runtime validation used the MinIO-backed smoke paths for dashboard, scenario control, and replay behavior.

### Completion Notes List

- The fake SCADA service now projects two distinct layers:
  - narrow supervisory values used for SCADA comparison
  - richer behavioral sensor fields used for replay-oriented fingerprint evaluation
- Replay mode now preserves current supervisory values while reusing stale SCADA-side behavioral payload from historical state, so replay no longer depends on mandatory SCADA divergence.
- The SCADA comparison rule remains narrow to temperature, pressure, and rpm; richer payload is attached only as contextual evidence.
- Replay inference datasets now append a synthetic SCADA-state-driven final step instead of reusing a stale valid artifact as the replayed step.
- Scenario-control expectations were restored for `scada_replay` so replay is shown as a fingerprint/replay outcome rather than a supervisory block.
- Dashboard guidance and evidence text now describe replay as a richer behavioral inconsistency detected by the fingerprint path.

### What Was Tested

- `tests.scada.test_opcua_service`
- `tests.comparison.test_service`
- `tests.lstm_service.test_replay_behavior`
- `tests.scenario_control.test_runtime`
- `tests.dashboard.test_guidance_view`
- `tests.test_runtime_demo`
- `tests.dashboard.test_control_surface`
- `tests.dashboard.test_event_timeline`
- `tests.dashboard.test_evidence_view`
- `tests.dashboard.test_pipeline_view`
- `tests.scenario_control.test_runtime_smoke`
- `tests.lstm_service.test_replay_behavior_runtime_smoke`
- `tests.dashboard.test_control_surface_runtime_smoke`
- full `unittest discover -s tests`

### Exact Commands Executed

```powershell
$env:PYTHONPATH='src'
.\.venv\Scripts\python -m py_compile src\parallel_truth_fingerprint\scada\opcua_service.py src\parallel_truth_fingerprint\lstm_service\replay_behavior.py src\parallel_truth_fingerprint\scenario_control\runtime.py scripts\run_local_demo.py tests\scada\test_opcua_service.py tests\comparison\test_service.py tests\lstm_service\test_replay_behavior.py tests\lstm_service\test_replay_behavior_runtime_smoke.py tests\scenario_control\test_runtime.py tests\scenario_control\test_runtime_smoke.py tests\dashboard\test_control_surface_runtime_smoke.py tests\dashboard\test_guidance_view.py tests\test_runtime_demo.py
```

```powershell
$env:PYTHONPATH='src'
.\.venv\Scripts\python -m unittest tests.scada.test_opcua_service tests.comparison.test_service tests.lstm_service.test_replay_behavior tests.scenario_control.test_runtime tests.dashboard.test_guidance_view tests.test_runtime_demo
```

```powershell
$env:PYTHONPATH='src'
.\.venv\Scripts\python -m unittest tests.dashboard.test_control_surface tests.dashboard.test_event_timeline tests.dashboard.test_evidence_view tests.dashboard.test_pipeline_view tests.scenario_control.test_runtime_smoke tests.lstm_service.test_replay_behavior_runtime_smoke
```

```powershell
docker compose -f compose.local.yml up -d mqtt-broker minio
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

- `py_compile` completed successfully.
- Focused contract/replay/dashboard/runtime suite: `Ran 43 tests` -> `OK`
- Broader dashboard/runtime suite: `Ran 20 tests` -> `OK (skipped=2)`
- Real dashboard smoke: `Ran 1 test` -> `OK`
- Real scenario-control smoke: `Ran 1 test` -> `OK`
- Real replay-behavior smoke: `Ran 1 test` -> `OK`
- Full regression: `Ran 140 tests` -> `OK (skipped=7)`

### Real Runtime Behavior Validated

- In the MinIO-backed real runtime smokes, `scada_replay` now:
  - keeps consensus successful
  - keeps SCADA comparison completed rather than blocked on mandatory divergence
  - persists the current cycle for downstream use
  - reuses the saved fingerprint model
  - emits a distinct `scada_replay_behavior` result through the fingerprint path
- The replay dataset now contains the recent real history plus a synthetic SCADA-state step keyed as `scada-state::...`, proving the replay evaluation is no longer just a stale valid-artifact replay.
- Dashboard/runtime smoke confirmed the replay channel is visible while SCADA divergence remains clear as a separate channel.

### Remaining Limitations

- This story makes replay detection real through richer SCADA-side behavioral payload, but it does not change the fingerprint adequacy gate. The model can still remain `runtime_valid_only` until the approved adequacy floor is met.
- The fully live consensus-backed CLI path remains dependent on the existing CometBFT environment health; Story 6.5 validation used the real MinIO-backed runtime smokes rather than claiming that separate environment issue is solved here.
- `scada_freeze` remains outside the tightened replay claim in this story. Story 6.5 corrects `scada_replay` specifically.

### File List

- `scripts/run_local_demo.py`
- `src/parallel_truth_fingerprint/contracts/__init__.py`
- `src/parallel_truth_fingerprint/scada/opcua_service.py`
- `src/parallel_truth_fingerprint/lstm_service/replay_behavior.py`
- `src/parallel_truth_fingerprint/scenario_control/runtime.py`
- `src/parallel_truth_fingerprint/dashboard/event_timeline.py`
- `src/parallel_truth_fingerprint/dashboard/evidence_view.py`
- `src/parallel_truth_fingerprint/dashboard/guidance_view.py`
- `tests/scada/test_opcua_service.py`
- `tests/comparison/test_service.py`
- `tests/lstm_service/test_replay_behavior.py`
- `tests/lstm_service/test_replay_behavior_runtime_smoke.py`
- `tests/scenario_control/test_runtime.py`
- `tests/scenario_control/test_runtime_smoke.py`
- `tests/dashboard/test_control_surface.py`
- `tests/dashboard/test_control_surface_runtime_smoke.py`
- `tests/dashboard/test_guidance_view.py`
- `tests/test_runtime_demo.py`
- `_bmad-output/implementation-artifacts/6-5-detect-replay-through-richer-scada-side-behavioral-payload.md`

### Change Log

- 2026-04-03: Story created and marked ready-for-dev.
- 2026-04-03: Story implemented, validated, and moved to ready-for-qa.
