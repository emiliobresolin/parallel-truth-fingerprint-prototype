# Story 1.2: Implement Sensor Simulation With Controlled Normal Behavior

Status: ready-for-dev

<!-- Note: Validation is optional. Run validate-create-story for quality check before dev-story. -->

## Story

As a researcher,
I want simulated compressor sensors with explicit normal behavior ranges and patterns,
so that the prototype can produce realistic local observations for demonstration and later anomaly scenarios.

## Acceptance Criteria

1. Given the compressor prototype scope, when the sensor simulation runs, then it produces temperature, pressure, and RPM values for one compressor and each sensor follows a defined normal range and a simple time-varying behavior pattern driven by compressor operational context, including `compressor_power`.
2. Given the physical behavior model, when `compressor_power` changes, then higher power results in higher expected temperature, pressure, and RPM behavior and lower power results in lower expected values across those variables.
3. Given the required simulation realism, when temperature increases, then the simulation increases sensor noise and variability for temperature, pressure, and RPM and that temperature-driven noise model is implemented only in the sensor simulation layer.
4. Given the architecture constraints for scenario support, when the simulation layer is implemented, then it exposes explicit upstream control points for later deviation and fault-injection scenarios and those control points do not bypass the normal observation pipeline.

## Tasks / Subtasks

- [ ] Define the simulation configuration model for one compressor and three sensors. (AC: 1, 2)
  - [ ] Add configuration placeholders for normal ranges, baseline operating values, and `compressor_power`.
  - [ ] Keep the configuration simple and local, without introducing scenario execution logic outside the simulation boundary.
- [ ] Implement a simple operational behavior model in `sensor_simulation/`. (AC: 1, 2)
  - [ ] Generate temperature, pressure, and RPM readings for one compressor.
  - [ ] Make the generated readings vary over time in a simple, observable pattern.
  - [ ] Make the three sensor behaviors respond coherently to `compressor_power`.
- [ ] Implement the temperature-driven noise model in the simulation layer only. (AC: 3)
  - [ ] Increase variability as temperature rises.
  - [ ] Ensure noise affects temperature, pressure, and RPM outputs.
  - [ ] Keep this model isolated from consensus, comparison, persistence, and LSTM concerns.
- [ ] Expose upstream scenario-control hooks without implementing full scenarios yet. (AC: 4)
  - [ ] Define simple input/control points that later stories can use for controlled deviations.
  - [ ] Ensure those hooks alter simulated inputs only and do not bypass later acquisition, MQTT, or consensus flow.
- [ ] Add observability for the simulation stage. (AC: 1, 2, 3)
  - [ ] Make outputs easy to inspect through logs or simple local state output.
  - [ ] Keep the observability focused on simulation behavior, not downstream validation states.
- [ ] Add minimal tests or checks for simulation structure and behavior. (AC: 1, 2, 3, 4)
  - [ ] Verify the simulator produces all three sensor outputs.
  - [ ] Verify `compressor_power` affects expected sensor directionality.
  - [ ] Verify rising temperature increases noise/variability.

## Dev Notes

- This story is limited to the simulation layer only. Do not implement edge acquisition, MQTT publishing/consumption, local replicated-state assembly, consensus, SCADA comparison, persistence, or LSTM logic here. Those belong to later stories. [Source: [epics.md](/c:/Users/emili/Desktop/Projets/parallel-truth-fingerprint-prototype/_bmad-output/planning-artifacts/epics.md#L164)]
- The architecture requires sensor simulation to be simple but explicit, with defined normal ranges, realistic but simple time-varying behavior, and support for controlled deviation. [Source: [architecture.md](/c:/Users/emili/Desktop/Projets/parallel-truth-fingerprint-prototype/_bmad-output/planning-artifacts/architecture.md#L316)]
- Preserve strict edge independence conceptually: this story prepares upstream simulated observations only. It must not create any centralized state manager or any fake “global truth” artifact.
- MQTT is not part of the trust model. It is passive relay infrastructure used later between edges; nothing in this story should treat MQTT as a validation component. [Source: [architecture.md](/c:/Users/emili/Desktop/Projets/parallel-truth-fingerprint-prototype/_bmad-output/planning-artifacts/architecture.md#L236)]
- Edge-local replicated state is a later-stage artifact built per edge from self-observation plus peer observations. This story should not create or name any output as `consensused_valid_state`, and it should not imply that simulation output is already replicated or validated. [Source: [architecture.md](/c:/Users/emili/Desktop/Projets/parallel-truth-fingerprint-prototype/_bmad-output/planning-artifacts/architecture.md#L35)] [Source: [architecture.md](/c:/Users/emili/Desktop/Projets/parallel-truth-fingerprint-prototype/_bmad-output/planning-artifacts/architecture.md#L492)]
- Keep the story simple and observable. The outputs should be easy to inspect during development and later demonstration, but should remain upstream-only.

### Project Structure Notes

- Primary implementation area:
  - `src/parallel_truth_fingerprint/sensor_simulation/`
- Supporting configuration areas if needed:
  - `src/parallel_truth_fingerprint/config/`
  - optionally `src/parallel_truth_fingerprint/contracts/` only if a lightweight internal simulation output contract is needed
- Do not touch:
  - `edge_nodes/`
  - `consensus/`
  - `scada/`
  - `comparison/`
  - `persistence/`
  - `lstm_service/`
  - `observability/` beyond minimal simulation-stage logging helpers
- Payload sample references are available in:
  - `src/parallel_truth_fingerprint/contracts/samples/hart_payload_sample.txt`
  - `src/parallel_truth_fingerprint/contracts/samples/unified_hart_payload_sample.txt`
  Use them for future compatibility awareness, but do not force full acquisition-payload implementation in this story if it would blur the story boundary with Story 1.3.

### Technical Requirements

- Simulate one compressor only.
- Simulate three sensors only: temperature, pressure, RPM.
- Add `compressor_power` as the operational context driver.
- Temperature-driven noise must influence all three simulated sensor outputs.
- The behavior model should remain understandable and deterministic enough for testing, even if light randomness is used.
- If randomness is used, provide a controllable seed or deterministic mode so later tests and demonstrations stay reproducible.

### Architecture Compliance

- The simulation layer must remain upstream-only.
- No trust, validation, or consensus semantics may be embedded into the simulation output.
- No edge-local replicated state should be produced here.
- No MQTT behavior should be implemented here.
- Scenario hooks must alter simulation conditions only; they must not inject downstream results.

### Library / Framework Requirements

- Stay within the current local Python project structure.
- Do not add new frameworks or external infrastructure dependencies for this story.
- Use only lightweight Python standard-library approaches unless an existing project dependency is clearly required.

### File Structure Requirements

- Prefer implementing behavior in new files under `sensor_simulation/`, such as:
  - `simulator.py`
  - `behavior_model.py`
  - `normal_profiles.py`
- Add config helpers only if they are directly needed by the simulator.
- Keep names aligned with the approved architecture.

### Testing Requirements

- Add focused simulation tests only.
- Validate:
  - three sensor outputs exist
  - `compressor_power` changes expected output direction
  - temperature-driven noise raises variability
  - scenario-control hooks remain upstream-only
- Do not write tests for MQTT, consensus, SCADA, persistence, or LSTM in this story.

### References

- Story definition and acceptance criteria: [epics.md](/c:/Users/emili/Desktop/Projets/parallel-truth-fingerprint-prototype/_bmad-output/planning-artifacts/epics.md#L164)
- Simulation model requirement: [architecture.md](/c:/Users/emili/Desktop/Projets/parallel-truth-fingerprint-prototype/_bmad-output/planning-artifacts/architecture.md#L316)
- Edge-local replicated state and pipeline context: [architecture.md](/c:/Users/emili/Desktop/Projets/parallel-truth-fingerprint-prototype/_bmad-output/planning-artifacts/architecture.md#L35)
- MQTT passive relay clarification: [architecture.md](/c:/Users/emili/Desktop/Projets/parallel-truth-fingerprint-prototype/_bmad-output/planning-artifacts/architecture.md#L236)
- Intermediate-state trust boundary: [architecture.md](/c:/Users/emili/Desktop/Projets/parallel-truth-fingerprint-prototype/_bmad-output/planning-artifacts/architecture.md#L492)
- Payload sample references: [hart_payload_sample.txt](/c:/Users/emili/Desktop/Projets/parallel-truth-fingerprint-prototype/src/parallel_truth_fingerprint/contracts/samples/hart_payload_sample.txt), [unified_hart_payload_sample.txt](/c:/Users/emili/Desktop/Projets/parallel-truth-fingerprint-prototype/src/parallel_truth_fingerprint/contracts/samples/unified_hart_payload_sample.txt)

## Dev Agent Record

### Agent Model Used

GPT-5 Codex

### Debug Log References

- Story generated after Story 1.1 implementation.
- Git is now present in the workspace, but no commit history analysis was required for this story-generation step.
- No sprint-status file exists yet.

### Completion Notes List

- Story 1.2 context generated with updated terminology for edge-local replicated state.
- MQTT explicitly constrained to passive relay infrastructure outside the trust model.
- Story kept intentionally simple, observable, and simulation-only.

### File List

- `_bmad-output/implementation-artifacts/1-2-implement-sensor-simulation-with-controlled-normal-behavior.md`
