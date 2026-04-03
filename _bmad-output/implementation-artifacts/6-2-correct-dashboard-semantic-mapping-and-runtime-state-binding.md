# Story 6.2: Correct Dashboard Semantic Mapping and Runtime-State Binding

Status: drafted

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

- [ ] Correct dashboard extraction of SCADA-comparison fields from the current runtime payload shape. (AC: 3, 4, 5)
- [ ] Correct edge-card binding to the actual runtime counter fields. (AC: 2, 5)
- [ ] Remove downstream comparison semantics from the sensor layer and keep sensor cards architecture-correct. (AC: 1, 3)
- [ ] Align component-scoped events/raw logs with the same corrected payload mapping. (AC: 4, 7)
- [ ] Replace internal story-number wording in operator-facing labels and notes with domain language. (AC: 6)
- [ ] Add focused tests and one real runtime validation pass. (AC: 8, 9)

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
