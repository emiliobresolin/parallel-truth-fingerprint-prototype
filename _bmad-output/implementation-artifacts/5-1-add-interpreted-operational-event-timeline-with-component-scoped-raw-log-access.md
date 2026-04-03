# Story 5.1: Add Interpreted Operational Event Timeline with Component-Scoped Raw Log Access

Status: review

## Story

As a researcher and demo operator,
I want the dashboard to present interpreted operational events globally and by component while preserving raw logs as technical ground truth,
so that I can explain the current runtime state without losing access to the underlying evidence.

## Scope Notes

- This story is limited to interpreted dashboard event views derived from existing runtime, cycle-history, operator-action, and latest-cycle state.
- It must not change:
  - the runtime/control architecture
  - the current dashboard control path
  - the MinIO persistence boundary
  - the dataset -> training -> model -> inference flow
- It must not add:
  - new backend services
  - new persistence boundaries
  - invented events
  - Story 5.2 visual pipeline work
  - Story 5.3 explainability summaries
  - Story 5.4 guidance-panel work

## Acceptance Criteria

1. The dashboard displays a global interpreted event timeline derived from existing runtime/log/state outputs.
2. The operator can filter or select events by component.
3. Component-scoped support is available at minimum for:
   - compressor
   - temperature sensor
   - pressure sensor
   - rpm sensor
   - edge 1
   - edge 2
   - edge 3
   - consensus
   - SCADA comparison
   - fingerprint / LSTM lifecycle
4. For each supported component, the operator can:
   - see interpreted events
   - open raw logs for the same component
   - keep raw logs as the ground truth
5. Event entries remain understandable and include:
   - timestamp or runtime reference
   - cycle context
   - component identity
   - interpreted meaning
6. Raw logs remain available and unmodified.

## Tasks / Subtasks

- [x] Add a derived event-timeline module that converts existing runtime state into global and component-scoped interpreted events. (AC: 1, 2, 3, 5)
- [x] Preserve raw component logs derived directly from the current runtime payload for the same component explorer. (AC: 3, 4, 6)
- [x] Wire interpreted events and raw logs into the dashboard state and UI. (AC: 1, 2, 3, 4, 5, 6)
- [x] Add focused Story 5.1 tests plus runtime smoke validation coverage. (AC: 1, 2, 3, 4, 5, 6)

## Dev Agent Record

### Agent Model Used

GPT-5 Codex

### Debug Log References

- Story 5.1 was implemented as a derived dashboard interpretation layer only.
- All interpreted events are built from existing runtime payloads, cycle history, and operator actions.
- Raw logs remain direct per-component slices of the runtime payload and are treated as technical ground truth.

### Completion Notes List

- Added `src/parallel_truth_fingerprint/dashboard/event_timeline.py` to build:
  - a global interpreted event timeline
  - component-scoped interpreted event timelines
  - component-scoped raw-log views
- Added required component support for:
  - compressor
  - temperature sensor
  - pressure sensor
  - rpm sensor
  - edge 1
  - edge 2
  - edge 3
  - consensus
  - SCADA comparison
  - fingerprint / LSTM lifecycle
- Added dashboard UI sections for:
  - `Operational Event Timeline`
  - `Component Log Explorer`
- Preserved raw component logs without rewriting or hiding the original data structure.
- Implemented only Story 5.1.

### What Was Tested

- Focused Story 5.1 event-timeline tests
- Existing dashboard control-surface tests
- Existing real dashboard smoke test
- Full regression suite

### Exact Commands Executed

```powershell
$env:PYTHONPATH='src'
.\.venv\Scripts\python -m unittest tests.dashboard.test_event_timeline tests.dashboard.test_control_surface
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

- `tests.dashboard.test_event_timeline tests.dashboard.test_control_surface` -> `Ran 7 tests` -> `OK`
- `tests.dashboard.test_control_surface_runtime_smoke` -> `Ran 1 test` -> `OK`
- `python -m unittest discover -s tests` -> `Ran 124 tests` -> `OK (skipped=7)`

### Real Runtime Behavior Validated

- The real Story 4.6 dashboard smoke still passed after adding the Story 5.1 timeline and component-log views.
- The runtime smoke now validates that the dashboard state includes:
  - `events.global_timeline`
  - `events.component_timelines`
  - `events.component_raw_logs`
- The real dashboard path still exposes:
  - runtime start/stop
  - power changes
  - scenario activation
  - replay behavior
  - saved-model reuse

### Remaining Limitations

- Story 5.1 is an interpretation layer only and does not change runtime behavior.
- The fingerprint base remains runtime-valid only, not yet meaningful-fingerprint-valid.
- Story 5.1 does not include the visual pipeline work from Story 5.2, the explainability summary work from Story 5.3, or the guidance panels from Story 5.4.

### File List

- `_bmad-output/implementation-artifacts/5-1-add-interpreted-operational-event-timeline-with-component-scoped-raw-log-access.md`
- `src/parallel_truth_fingerprint/dashboard/control_surface.py`
- `src/parallel_truth_fingerprint/dashboard/event_timeline.py`
- `tests/dashboard/test_control_surface.py`
- `tests/dashboard/test_control_surface_runtime_smoke.py`
- `tests/dashboard/test_event_timeline.py`
