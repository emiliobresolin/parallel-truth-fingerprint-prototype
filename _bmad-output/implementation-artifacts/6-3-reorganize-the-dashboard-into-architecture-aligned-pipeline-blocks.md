# Story 6.3: Reorganize the Dashboard into Architecture-Aligned Pipeline Blocks

Status: drafted

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

- [ ] Group the dashboard into architecture-aligned blocks for sensors, edges, and later-stage interpretation. (AC: 1, 2, 6)
- [ ] Rebalance the initial viewport around runtime health, controls, pipeline state, and evidence summary. (AC: 3)
- [ ] Standardize collapse or hide behavior for lower-priority technical sections. (AC: 4)
- [ ] Preserve component-scoped interpreted events and raw logs inside the new structure. (AC: 5)
- [ ] Replace any remaining internal story-number labels in operator-facing grouped sections. (AC: 7)
- [ ] Add focused tests and one real dashboard validation pass. (AC: 8, 9)

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
