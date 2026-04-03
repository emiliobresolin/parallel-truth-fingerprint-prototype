# Story 6.2: Correct Dashboard Semantic Mapping and Runtime-State Binding

Status: review

## Story

As a researcher and demo operator,
I want the dashboard to reflect the real architecture and the real runtime payload correctly,
so that the UI stops misrepresenting sensor, edge, SCADA-comparison, and fingerprint state during the demo.

## Scope Notes

- This story is limited to semantic correction and runtime-state binding for the current dashboard.
- It must preserve the five real pillars exactly as they already exist:
  - acquisition of sensor values
  - decentralization across edges
  - Byzantine consensus across edges
  - comparison between consensused data and SCADA data
  - LSTM-based fingerprint generation
- It must preserve the current runtime/control architecture and reuse the existing payloads.
- It must not add:
  - a new backend service
  - a new storage boundary
  - new pipeline stages
  - new runtime logic beyond what is strictly needed to expose existing state correctly
- This story corrects truthfulness first. It does not perform the later structural layout reorganization of Story 6.3.

## Architecture Reminder

- Sensors are the physical origin.
- Edges perform acquisition, publication, peer consumption, and local replicated-view reconstruction.
- Consensus produces the committed trusted state.
- SCADA comparison happens after the consensused state exists.
- Fingerprint and replay interpretation happen after the SCADA-comparison stage.

## Acceptance Criteria

1. Given the physical-origin requirement, when sensor cards are rendered, then they show only sensor-layer concepts such as:
   - sensor identity
   - live physical value
   - engineering unit
   - timestamp or live-status note
   and they do not display SCADA-comparison or replicated-edge concepts on the sensor layer.
2. Given the edge-layer requirement, when edge cards are rendered, then they show edge-layer concepts such as:
   - acquisition status
   - published observations
   - peer-consumed observations
   - replicated local-view status
   and they read those values from the real edge runtime payload fields.
3. Given the SCADA-comparison requirement, when the dashboard renders comparison and divergence state, then it reads the structured comparison payload correctly from the current runtime state and displays comparison semantics in the SCADA-comparison stage rather than on the sensor cards.
4. Given the component log and event views from prior stories, when the operator inspects component-scoped evidence, then interpreted events, raw logs, and pipeline summaries are bound to the same underlying runtime payload shape.
5. Given a live runtime cycle, when the dashboard is compared with terminal/runtime logs, then key displayed values match the real runtime state for:
   - sensor values
   - edge publish and peer-consumption counts
   - comparison classification
   - divergent sensors when present
6. Given the operator-facing wording requirement, when runtime state, limitation notes, and dashboard labels are shown, then they use architecture-correct domain names and do not expose internal delivery labels such as Story 4.6, Story 5.1, Story 6.2, or any other BMAD story numbers.
7. Given the raw-evidence requirement, when semantic corrections are applied, then raw logs and technical evidence remain accessible and unmodified as ground truth.
8. Given focused validation, when this story is closed, then tests prove that the dashboard is reading the correct runtime fields and payload shapes rather than presenting placeholder or misbound data.
9. Given the project testing-closeout rule, when Story 6.2 is closed, then the story record explicitly includes:
   - what was tested
   - exact commands executed
   - test results
   - real runtime behavior validated
   - remaining limitations

## Testing Requirements

- Testing is mandatory for this story.
- The story is incomplete unless it includes:
  - focused tests for sensor-card semantics
  - focused tests for edge-card counter binding against the real runtime field names
  - focused tests for SCADA-comparison structured payload mapping
  - focused tests for component-log and event-view consistency
  - focused tests that ensure operator-facing labels do not leak internal story references
  - one real runtime validation pass comparing dashboard values with live runtime logs

## Dependencies

- Story 4.6 local operator dashboard
- Story 5.1 component-scoped interpreted events and raw logs
- Story 5.2 visual pipeline baseline
- Story 5.3 translated status and evidence view

## Non-Goals

- no full layout redesign
- no new services
- no new storage boundary
- no new runtime-control path
- no removal of raw evidence access

## Tasks / Subtasks

- [x] Correct dashboard extraction of SCADA-comparison fields from the current runtime payload shape. (AC: 3, 4, 5)
- [x] Correct edge-card binding to the actual runtime counter fields. (AC: 2, 5)
- [x] Remove downstream comparison semantics from the sensor layer and keep sensor cards architecture-correct. (AC: 1, 3)
- [x] Align component-scoped events/raw logs with the same corrected payload mapping. (AC: 4, 7)
- [x] Replace internal story-number wording in operator-facing labels and notes with domain language. (AC: 6)
- [x] Add focused tests and one real runtime validation pass. (AC: 8, 9)

## Technical Notes

- This story should correct payload binding before any later structural dashboard cleanup.
- The dashboard currently wraps and reuses multiple runtime views; the fix should prefer one canonical interpretation of the payload shape per layer.
- The main architectural separation to preserve is:
  - sensor layer
  - edge layer
  - consensus layer
  - SCADA-comparison layer
  - fingerprint layer

## Real vs Simulated Boundary

- Real in this story:
  - dashboard controller state
  - runtime payloads
  - terminal/runtime logs
  - MinIO-backed artifact/lifecycle state
- Simulated or controlled in this story:
  - compressor/process behavior
  - SCADA environment

## Academic Mapping

- This story does not change the prototype architecture.
- It makes the dashboard trustworthy as an explanatory surface by ensuring that each layer shows the right concepts and the right values from the real runtime.

## Dev Agent Record

### Agent Model Used

GPT-5 Codex

### Debug Log References

- Story 6.2 was implemented as a dashboard truthfulness and binding fix only.
- No runtime/control architecture, consensus flow, persistence boundary, or ML logic was changed.
- The main runtime-payload fix was normalizing wrapped `structured` comparison and divergence payloads so the pipeline and event views read the same data shape as the saved runtime logs.

### Completion Notes List

- Added `src/parallel_truth_fingerprint/dashboard/runtime_binding.py` as the shared dashboard payload-binding layer for wrapped runtime objects.
- Corrected SCADA-comparison mapping so dashboard pipeline cards and component events read `comparison_output["structured"]` when the runtime payload is wrapped.
- Corrected edge-card counters to use the real `peer_observation_count` runtime field instead of a non-existent `consumed_observation_count` field.
- Corrected sensor cards so they now show only sensor-layer concepts:
  - live physical value
  - engineering unit
  - sensor-layer interpreted status
- Removed downstream SCADA-comparison semantics from sensor component events and raw sensor logs.
- Kept SCADA divergence and comparison semantics in the SCADA-comparison stage where they belong.
- Replaced operator-facing fingerprint limitation wording that exposed internal story numbers with domain language.
- Implemented only Story 6.2.

### What Was Tested

- Focused dashboard pipeline-view tests
- Focused interpreted-event and raw-log tests
- Existing dashboard control-surface tests
- Existing fingerprint inference tests for operator-facing limitation wording
- Real dashboard smoke validation
- Full regression suite
- Real runtime-log parity check comparing dashboard-derived values with the saved live runtime log

### Exact Commands Executed

```powershell
$env:PYTHONPATH='src'
.\.venv\Scripts\python -m unittest tests.dashboard.test_pipeline_view tests.dashboard.test_event_timeline tests.dashboard.test_control_surface tests.lstm_service.test_inference
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
import json
from pathlib import Path
from parallel_truth_fingerprint.dashboard.event_timeline import build_dashboard_event_views
from parallel_truth_fingerprint.dashboard.pipeline_view import build_dashboard_pipeline_view

payload = json.loads(Path("logs/run_local_demo.log").read_text(encoding="utf-8"))
events = build_dashboard_event_views(
    generated_at="2026-04-03T00:00:00+00:00",
    latest_runtime_payload=payload,
    operator_actions=[],
)
pipeline = build_dashboard_pipeline_view(
    latest_runtime_payload=payload,
    event_views=events,
)
process_nodes = {node["component_id"]: node for node in pipeline["rows"][0]["nodes"]}
edge_nodes = {node["component_id"]: node for node in pipeline["rows"][1]["nodes"]}
comparison_node = {node["component_id"]: node for node in pipeline["rows"][2]["nodes"]}["scada_comparison"]
print("TEMP_SENSOR_METRICS", {metric["label"]: metric["value"] for metric in process_nodes["temperature_sensor"]["metrics"]})
print("EDGE1_METRICS", {metric["label"]: metric["value"] for metric in edge_nodes["edge_1"]["metrics"]})
print("SCADA_COMPARISON_METRICS", {metric["label"]: metric["value"] for metric in comparison_node["metrics"]})
print("TEMP_EVENT", events["component_timelines"]["temperature_sensor"][0]["message"])
print("SCADA_EVENT", events["component_timelines"]["scada_comparison"][0]["message"])
print("TEMP_RAW_KEYS", sorted(events["component_raw_logs"]["temperature_sensor"].keys()))
'@ | .\.venv\Scripts\python -
```

### Test Results

- `tests.dashboard.test_pipeline_view tests.dashboard.test_event_timeline tests.dashboard.test_control_surface tests.lstm_service.test_inference` -> `Ran 16 tests` -> `OK`
- `tests.dashboard.test_control_surface_runtime_smoke` -> `Ran 1 test` -> `OK`
- `python -m unittest discover -s tests` -> `Ran 134 tests` -> `OK (skipped=7)`

### Real Runtime Behavior Validated

- The real dashboard smoke still passed after the Story 6.2 semantic-binding fixes.
- A real saved runtime log from `logs/run_local_demo.log` now produces dashboard values that align with the runtime payload:
  - `TEMP_SENSOR_METRICS {'Value': '76.912', 'Unit': 'degC'}`
  - `EDGE1_METRICS {'Published': '81', 'Peer-consumed': '162', 'Replicated': 'True'}`
  - `SCADA_COMPARISON_METRICS {'Divergent sensors': 'none', 'Source round': 'round-20260403123123312824'}`
  - `TEMP_EVENT Temperature Sensor reported 76.912 degC on cycle 27.`
  - `SCADA_EVENT SCADA comparison reports that all monitored sensors match the consensused state.`
  - `TEMP_RAW_KEYS ['sensor_name', 'simulator_value', 'transmitter_observation']`
- The dashboard now reflects the intended architecture more honestly:
  - sensors = physical-origin values
  - edges = publication and peer-consumption state
  - SCADA comparison = later-stage comparison semantics

### Remaining Limitations

- Story 6.2 corrects dashboard truthfulness and payload binding; it does not yet perform the broader structural reorganization planned for Story 6.3.
- The fingerprint base is still runtime-valid only, not yet meaningfully fingerprint-valid, because the adequacy floor remains below target.
- Raw evidence is still the ground truth; the dashboard remains a derived interpretation layer on top of the runtime payload.

### File List

- `_bmad-output/implementation-artifacts/6-2-correct-dashboard-semantic-mapping-and-runtime-state-binding.md`
- `src/parallel_truth_fingerprint/dashboard/event_timeline.py`
- `src/parallel_truth_fingerprint/dashboard/pipeline_view.py`
- `src/parallel_truth_fingerprint/dashboard/runtime_binding.py`
- `src/parallel_truth_fingerprint/lstm_service/inference.py`
- `tests/dashboard/test_control_surface.py`
- `tests/dashboard/test_control_surface_runtime_smoke.py`
- `tests/dashboard/test_event_timeline.py`
- `tests/dashboard/test_pipeline_view.py`
- `tests/lstm_service/test_inference.py`
- `tests/lstm_service/test_inference_runtime_smoke.py`
- `tests/lstm_service/test_replay_behavior_runtime_smoke.py`
