# Story 5.2: Add Visual Operational Pipeline and Live Component State Overlay

Status: review

## Story

As a researcher and demo operator,
I want the dashboard to show the prototype as a visual operational pipeline with live interpreted state per component,
so that a professor or evaluator can understand the real runtime flow without reading developer-oriented JSON blocks.

## Scope Notes

- This story is limited to a simple SCADA/HMI-inspired visual pipeline derived from the existing runtime and dashboard state.
- It must preserve:
  - the existing runtime/control architecture
  - the current scenario-control path
  - the current persistence and model flow
  - the Story 5.1 interpreted/raw log model
  - the Story 5.3 explainability model
- It must not add:
  - fake UI-only process effects
  - new backend services
  - new storage boundaries
  - Story 5.4 guidance-panel work

## Acceptance Criteria

1. The dashboard visually shows:
   - compressor
   - temperature sensor
   - pressure sensor
   - rpm sensor
   - edge 1
   - edge 2
   - edge 3
   - consensus
   - SCADA-side system/computer view
   - SCADA comparison
   - fingerprint / LSTM stage
2. The UI visually shows the operational path:
   - power -> sensors -> edges -> consensus -> SCADA comparison -> fingerprint
3. The SCADA-side values are shown as a distinct visual source, not merged into consensused values.
4. Sensor and compressor values update live as runtime changes.
5. Compressor power changes visibly affect the displayed process state and sensor values using the real runtime state, not UI-only effects.
6. Each major component or box shows interpreted live status.
7. Each major component or box can expose or link to its scoped interpreted events and raw logs from Story 5.1.
8. Channel separation remains explicit in the visual design:
   - SCADA divergence
   - consensus status/failure
   - fingerprint anomaly/replay behavior

## Tasks / Subtasks

- [x] Add a derived visual pipeline view model for the current dashboard state. (AC: 1, 2, 3, 4, 5, 6, 8)
- [x] Render a simple SCADA-inspired pipeline layout in the dashboard using the existing state only. (AC: 1, 2, 3, 4, 5, 6)
- [x] Link each major box to the component-scoped interpreted/raw views from Story 5.1. (AC: 6, 7)
- [x] Add focused Story 5.2 tests plus runtime smoke validation coverage. (AC: 1, 2, 3, 4, 5, 6, 7, 8)

## Dev Agent Record

### Agent Model Used

GPT-5 Codex

### Debug Log References

- Story 5.2 was implemented as a derived dashboard visualization layer only.
- The visual pipeline is driven by the existing runtime payload, Story 5.1 component events/logs, and existing channel separation.

### Completion Notes List

- Added `src/parallel_truth_fingerprint/dashboard/pipeline_view.py` to derive a visual operational pipeline from the current runtime payload.
- Added a `Visual Operational Pipeline` section to the dashboard UI.
- Added major visual boxes for:
  - compressor
  - temperature sensor
  - pressure sensor
  - rpm sensor
  - edge 1
  - edge 2
  - edge 3
  - consensus
  - SCADA workstation/source
  - SCADA comparison
  - fingerprint / LSTM
- Kept the SCADA source visually distinct from consensused values and the SCADA comparison stage.
- Added explicit output-channel separation badges for:
  - SCADA divergence
  - consensus status
  - fingerprint / replay behavior
- Added `Open logs` hooks on each major visual box that reuse the Story 5.1 component log explorer instead of inventing a second evidence path.
- Implemented only Story 5.2 in this pass before moving on to Story 5.4.

### What Was Tested

- Focused Story 5.2 pipeline-view tests
- Existing Story 5.1 dashboard control-surface tests
- Existing Story 5.1 and Story 5.3 derived-view tests
- Existing real dashboard smoke test
- Full regression suite

### Exact Commands Executed

```powershell
$env:PYTHONPATH='src'
.\.venv\Scripts\python -m unittest tests.dashboard.test_pipeline_view tests.dashboard.test_control_surface
```

```powershell
$env:PYTHONPATH='src'
.\.venv\Scripts\python -m unittest tests.dashboard.test_event_timeline tests.dashboard.test_evidence_view
```

```powershell
docker compose -f compose.local.yml up -d minio
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

- `tests.dashboard.test_pipeline_view tests.dashboard.test_control_surface` -> `Ran 6 tests` -> `OK`
- `tests.dashboard.test_event_timeline tests.dashboard.test_evidence_view` -> `Ran 5 tests` -> `OK`
- `tests.dashboard.test_control_surface_runtime_smoke` -> `Ran 1 test` -> `OK`
- `python -m unittest discover -s tests` -> `Ran 128 tests` -> `OK (skipped=7)`

### Real Runtime Behavior Validated

- The real Story 4.6 dashboard smoke still passed after adding the Story 5.2 visual pipeline layer.
- The runtime smoke now validates that the dashboard state includes:
  - `pipeline.flow_summary`
  - visual pipeline rows
  - major pipeline nodes including the compressor card
- The live dashboard smoke confirmed that the compressor card reflects real operating-level changes through the existing runtime path.
- The visual pipeline keeps the SCADA workstation/source distinct from the SCADA comparison stage and keeps output-channel separation visible.

### Remaining Limitations

- Story 5.2 is a visual layer only and does not change runtime behavior, persistence, or ML logic.
- The fingerprint base remains runtime-valid only, not yet meaningful-fingerprint-valid.
- Story 5.2 does not include the demo-guidance panels from Story 5.4.

### File List

- `_bmad-output/implementation-artifacts/5-2-add-visual-operational-pipeline-and-live-component-state-overlay.md`
- `src/parallel_truth_fingerprint/dashboard/control_surface.py`
- `src/parallel_truth_fingerprint/dashboard/pipeline_view.py`
- `tests/dashboard/test_control_surface.py`
- `tests/dashboard/test_control_surface_runtime_smoke.py`
- `tests/dashboard/test_pipeline_view.py`

## Stabilization Follow-up

- Reduced always-visible dashboard density so the pipeline remains visible without overwhelming the initial operator viewport.
- Kept the visual pipeline linked to the existing component log explorer while moving lower-priority technical detail behind collapsible sections.
