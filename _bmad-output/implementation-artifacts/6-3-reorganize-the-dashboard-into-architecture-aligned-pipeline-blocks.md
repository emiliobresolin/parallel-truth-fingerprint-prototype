# Story 6.3: Reorganize the Dashboard into Architecture-Aligned Pipeline Blocks

Status: review

## Story

As a researcher and demo operator,
I want the dashboard to be reorganized into architecture-aligned blocks with consistent hierarchy and collapse behavior,
so that the prototype becomes easier to read and explain on a normal laptop-sized screen during the demo.

## Scope Notes

- This story is limited to dashboard structure, grouping, hierarchy, and collapse behavior.
- It depends on Story 6.2 semantic/state correction first.
- It must preserve the five real pillars exactly as they already exist:
  - acquisition of sensor values
  - decentralization across edges
  - Byzantine consensus across edges
  - comparison between consensused data and SCADA data
  - LSTM-based fingerprint generation
- It must preserve the existing evidence layers and raw-log access.
- It must not add:
  - new backend services
  - new storage boundaries
  - new functional pipeline stages
  - fake UI-only behavior
  - enterprise-grade HMI scope

## Acceptance Criteria

1. Given the corrected dashboard semantics, when the layout is reorganized, then all sensors are grouped into one architecture-aligned block and all edges are grouped into one architecture-aligned block.
2. Given the downstream pipeline requirement, when the later stages are shown, then the dashboard presents clear separate sections for:
   - consensus
   - SCADA source and comparison
   - fingerprint and replay behavior
3. Given the hierarchy requirement, when the dashboard first loads on a normal laptop-sized window, then the initial viewport emphasizes:
   - runtime health
   - operator controls
   - current pipeline state
   - current evidence summary
   and lower-priority technical sections do not dominate the first view.
4. Given the raw-evidence requirement, when the dashboard is reorganized, then raw logs, deep technical state, and channel details remain available but are visually secondary and use standardized collapse or hide behavior.
5. Given the component-evidence requirement, when the operator interacts with a grouped block or component, then the dashboard still provides access to the relevant interpreted events and raw logs from prior stories.
6. Given the pipeline-clarity requirement, when a professor or evaluator views the dashboard, then the architecture can be understood in order from physical origin to later-stage interpretation without requiring them to mentally reconstruct the pipeline from scattered panels.
7. Given the operator-facing wording requirement, when grouped sections and labels are shown, then they use architecture and domain language and do not rely on internal story numbering or BMAD implementation jargon.
8. Given focused validation, when this story is closed, then tests and manual validation prove that the reorganized dashboard remains readable, accurate, and operator-usable without hiding technical evidence.
9. Given the project testing-closeout rule, when Story 6.3 is closed, then the story record explicitly includes:
   - what was tested
   - exact commands executed
   - test results
   - real runtime behavior validated
   - remaining limitations

## Testing Requirements

- Testing is mandatory for this story.
- The story is incomplete unless it includes:
  - focused tests for grouped dashboard sections and collapse behavior
  - focused tests that preserve access to interpreted events and raw logs
  - focused checks for primary information visibility in the initial viewport
  - one real dashboard validation pass on a normal laptop-sized window
  - explicit confirmation that raw technical evidence remains accessible

## Dependencies

- Story 6.2 semantic/state correction
- Story 5.1 interpreted events and raw logs
- Story 5.3 explainability and evidence summaries

## Non-Goals

- no new dashboard data sources
- no new runtime behavior
- no enterprise-grade SCADA/HMI redesign
- no removal of detailed technical evidence

## Tasks / Subtasks

- [x] Group the dashboard into architecture-aligned blocks for sensors, edges, and later-stage interpretation. (AC: 1, 2, 6)
- [x] Rebalance the initial viewport around runtime health, controls, pipeline state, and evidence summary. (AC: 3)
- [x] Standardize collapse or hide behavior for lower-priority technical sections. (AC: 4)
- [x] Preserve component-scoped interpreted events and raw logs inside the new structure. (AC: 5)
- [x] Replace any remaining internal story-number labels in operator-facing grouped sections. (AC: 7)
- [x] Add focused tests and one real dashboard validation pass. (AC: 8, 9)

## Technical Notes

- This story is about composition, hierarchy, and clarity, not new functionality.
- It should make the existing dashboard easier to explain without weakening traceability back to raw runtime evidence.
- The intended architecture order remains:
  - sensors as physical origin
  - edges as acquisition and decentralization
  - consensus as trusted committed state
  - SCADA comparison as supervisory validation
  - fingerprint as behavioral interpretation

## Real vs Simulated Boundary

- Real in this story:
  - live dashboard state
  - runtime health and lifecycle state
  - interpreted events and raw logs
- Simulated or controlled in this story:
  - compressor/process behavior
  - SCADA environment

## Academic Mapping

- This story does not add research functionality.
- It improves demo readiness by making the implemented prototype easier to understand while keeping the architecture and evidence honest.

## Dev Agent Record

### Agent Model Used

GPT-5 Codex

### Debug Log References

- Story 6.3 was implemented as a dashboard composition refactor only.
- No runtime behavior, storage boundary, pipeline stage, or evidence source was added.
- The main changes were:
  - making the pipeline the main workspace
  - splitting downstream stages into consensus, supervisory validation, and behavioral interpretation
  - moving component evidence inside the pipeline workspace
  - compressing current evidence into a smaller summary zone
  - standardizing lower-priority sections behind the same collapsed-details pattern

### Completion Notes List

- Reworked the dashboard layout so runtime health and controls remain at the top, followed by a dominant pipeline workspace and a lighter evidence-summary column.
- Reorganized the pipeline into architecture-aligned grouped sections for:
  - physical origin and sensors
  - distributed edge acquisition
  - trusted committed state
  - supervisory validation
  - behavioral interpretation
- Kept distinct output channels inside the pipeline workspace as a separate grouped stage instead of a disconnected secondary panel.
- Moved component-scoped interpreted events and raw logs into an embedded `Component Evidence` drilldown inside the pipeline workspace so evidence access follows the selected architecture component.
- Consolidated translated status and startup-to-now evidence into a `Current Evidence Summary` panel instead of keeping several competing first-view cards.
- Kept `Fingerprint Readiness` visible but reduced its dominance by moving the behavior matrix behind an embedded details control.
- Standardized lower-priority surfaces as collapsed details:
  - operator feedback
  - demo guidance
  - operational event timeline
  - technical runtime state
  - raw channel details
- Implemented only Story 6.3.

### What Was Tested

- Focused dashboard pipeline-view tests
- Focused dashboard control-surface tests
- Real dashboard smoke validation
- Full regression suite
- One live dashboard HTML validation pass confirming the new grouped section hierarchy is present in the served page

### Exact Commands Executed

```powershell
$env:PYTHONPATH='src'
.\.venv\Scripts\python -m unittest tests.dashboard.test_pipeline_view tests.dashboard.test_control_surface
```

```powershell
$env:PYTHONPATH='src'
.\.venv\Scripts\python -m py_compile src\parallel_truth_fingerprint\dashboard\control_surface.py src\parallel_truth_fingerprint\dashboard\pipeline_view.py
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
.\.venv\Scripts\python -m unittest discover -s tests
```

```powershell
$env:PYTHONPATH='src'
@'
from urllib import request
from parallel_truth_fingerprint.config.runtime import RuntimeDemoConfig
from parallel_truth_fingerprint.dashboard import LocalOperatorDashboardController, LocalOperatorDashboardServer

config = RuntimeDemoConfig(mqtt_transport='passive', demo_dashboard_host='127.0.0.1', demo_dashboard_port=0)
controller = LocalOperatorDashboardController(config)
server = LocalOperatorDashboardServer(controller, host='127.0.0.1', port=0)
try:
    server.start_in_background()
    html = request.urlopen(server.base_url, timeout=5).read().decode('utf-8')
    checks = {
        'Prototype Pipeline': 'Prototype Pipeline' in html,
        'Current Evidence Summary': 'Current Evidence Summary' in html,
        'Component Evidence': 'Component Evidence' in html,
        'Transparent Operator Feedback': 'Transparent Operator Feedback' in html,
        'Embedded details count': html.count('embedded-details'),
        'Panel details count': html.count('<details class="panel">'),
    }
    for key, value in checks.items():
        print(key, value)
finally:
    server.stop()
'@ | .\.venv\Scripts\python -
```

### Test Results

- `tests.dashboard.test_pipeline_view tests.dashboard.test_control_surface` -> `Ran 10 tests` -> `OK`
- `python -m py_compile src\parallel_truth_fingerprint\dashboard\control_surface.py src\parallel_truth_fingerprint\dashboard\pipeline_view.py` -> `OK`
- `tests.dashboard.test_control_surface_runtime_smoke` -> `Ran 1 test` -> `OK`
- `python -m unittest discover -s tests` -> `Ran 137 tests` -> `OK (skipped=7)`

### Real Runtime Behavior Validated

- The real dashboard smoke still passed after the Story 6.3 composition refactor.
- The live dashboard state preserved:
  - component-scoped interpreted events
  - raw component logs
  - readiness evidence
  - channel separation
- The served dashboard HTML now includes the reorganized main-view hierarchy:
  - `Prototype Pipeline`
  - `Current Evidence Summary`
  - `Component Evidence`
  - `Transparent Operator Feedback`
- The live HTML validation pass reported:
  - `Prototype Pipeline True`
  - `Current Evidence Summary True`
  - `Component Evidence True`
  - `Transparent Operator Feedback True`
  - `Embedded details count 7`
  - `Panel details count 5`

### Remaining Limitations

- Story 6.3 improves structure and readability, but it does not change the underlying fingerprint adequacy limitation.
- The fingerprint remains runtime-valid only, not meaningfully fingerprint-valid, until the approved adequacy floor is met.
- The dashboard is now more architecture-aligned, but it remains a local prototype control surface rather than a production SCADA/HMI.

### File List

- `_bmad-output/implementation-artifacts/6-3-reorganize-the-dashboard-into-architecture-aligned-pipeline-blocks.md`
- `src/parallel_truth_fingerprint/dashboard/control_surface.py`
- `src/parallel_truth_fingerprint/dashboard/pipeline_view.py`
- `tests/dashboard/test_control_surface.py`
- `tests/dashboard/test_control_surface_runtime_smoke.py`
- `tests/dashboard/test_pipeline_view.py`
