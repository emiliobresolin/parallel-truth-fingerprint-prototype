# Story 5.4: Add Demo Guidance Panels for "What Is Happening", "What Should Happen", and "What Changed"

Status: review

## Story

As a researcher and demo operator,
I want the dashboard to explain what the system is doing, what should happen, and what has changed in concise demo-oriented language,
so that the prototype can support a live academic demonstration without requiring constant verbal decoding of internal state.

## Scope Notes

- This story is limited to concise, derived dashboard guidance panels built from existing runtime, scenario, lifecycle, and evidence state.
- It must preserve:
  - the existing runtime/control architecture
  - the current scenario-control behavior
  - the current persistence/model flow
  - the Story 5.1 interpreted event model
  - the Story 5.3 explainability and evidence model
- It must not add:
  - new backend services
  - new ML logic
  - a tutorial engine
  - a chatbot/copilot

## Acceptance Criteria

1. The dashboard includes concise explanatory panels covering:
   - what the system is doing
   - what should happen during normal operation
   - what should change during replay
   - what should change during SCADA divergence
   - what evidence indicates success or anomaly
2. The dashboard explicitly communicates:
   - what has happened already
   - what has not happened yet
   - what is expected next
3. These sections are derived from existing runtime/scenario/lifecycle/evidence state rather than invented demo text.
4. The explanation layer does not overclaim ML strength or adequacy.
5. The operator retains access to raw technical evidence while using the guidance panels.

## Tasks / Subtasks

- [x] Add a derived guidance-view model using existing runtime, scenario, event, and explainability state. (AC: 1, 2, 3, 4)
- [x] Render concise demo-guidance panels in the dashboard UI. (AC: 1, 2, 3, 4, 5)
- [x] Add focused Story 5.4 tests plus runtime smoke validation coverage. (AC: 1, 2, 3, 4, 5)

## Dev Agent Record

### Agent Model Used

GPT-5 Codex

### Debug Log References

- Story 5.4 was implemented as a derived guidance layer on top of the existing runtime, event, and explainability state.
- The guidance panels reuse existing state and explicitly preserve access to raw evidence rather than inventing a new explanation backend.

### Completion Notes List

- Added `src/parallel_truth_fingerprint/dashboard/guidance_view.py` to derive concise demo-guidance panels from the current dashboard state.
- Added a `Demo Guidance` section to the dashboard UI.
- Added guidance panels for:
  - what is happening
  - what should happen
  - what changed
  - evidence signals
- Kept the guidance layer tied to existing state:
  - runtime/scenario state
  - consensus state
  - replay behavior
  - Story 5.3 explainability summaries
- Preserved the runtime-valid-only limitation explicitly and kept access to raw component logs and channel panels.
- Implemented only Story 5.4 in this pass.

### What Was Tested

- Focused Story 5.4 guidance-view tests
- Existing Story 5.2 dashboard control-surface tests
- Existing Story 5.1 and Story 5.3 derived-view tests
- Existing real dashboard smoke test
- Full regression suite

### Exact Commands Executed

```powershell
$env:PYTHONPATH='src'
.\.venv\Scripts\python -m unittest tests.dashboard.test_guidance_view tests.dashboard.test_control_surface
```

```powershell
$env:PYTHONPATH='src'
.\.venv\Scripts\python -m unittest tests.dashboard.test_pipeline_view tests.dashboard.test_event_timeline tests.dashboard.test_evidence_view
```

```powershell
$env:PYTHONPATH='src'
$env:RUN_REAL_DASHBOARD_SMOKE='1'
.\.venv\Scripts\python -m unittest tests.dashboard.test_control_surface_runtime_smoke
```

```powershell
$env:PYTHONPATH='src'
.\.venv\Scripts\python -m unittest discover -s tests
```

### Test Results

- `tests.dashboard.test_guidance_view tests.dashboard.test_control_surface` -> `Ran 6 tests` -> `OK`
- `tests.dashboard.test_pipeline_view tests.dashboard.test_event_timeline tests.dashboard.test_evidence_view` -> `Ran 7 tests` -> `OK`
- `tests.dashboard.test_control_surface_runtime_smoke` -> `Ran 1 test` -> `OK`
- `python -m unittest discover -s tests` -> `Ran 130 tests` -> `OK (skipped=7)`

### Real Runtime Behavior Validated

- The real Story 4.6 dashboard smoke still passed after adding the Story 5.4 guidance layer.
- The runtime smoke now validates that the dashboard state includes a `guidance` section with non-empty guidance panels.
- The real dashboard path still proves:
  - runtime start/stop
  - power changes through the real simulator/runtime path
  - replay behavior through the existing fingerprint path
  - saved-model reuse
  - explicit runtime-valid-only limitation

### Remaining Limitations

- Story 5.4 is a derived explanation layer only and does not change runtime behavior or ML capability.
- The fingerprint base remains runtime-valid only, not yet meaningful-fingerprint-valid.
- The guidance panels are demo-oriented summaries and should still be backed by the raw component logs and channel views when presenting evidence.

### File List

- `_bmad-output/implementation-artifacts/5-4-add-demo-guidance-panels-for-what-is-happening-what-should-happen-and-what-changed.md`
- `src/parallel_truth_fingerprint/dashboard/control_surface.py`
- `src/parallel_truth_fingerprint/dashboard/guidance_view.py`
- `tests/dashboard/test_control_surface.py`
- `tests/dashboard/test_control_surface_runtime_smoke.py`
- `tests/dashboard/test_guidance_view.py`

## Stabilization Follow-up

- Kept the guidance layer available while reducing its default visual dominance so runtime health, controls, and live continuity remain primary in the operator view.
- Preserved raw technical evidence access under the lighter dashboard hierarchy.
