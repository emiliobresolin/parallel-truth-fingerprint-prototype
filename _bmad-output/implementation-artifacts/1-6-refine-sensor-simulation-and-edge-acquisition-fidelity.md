# Story 1.6: Refine Sensor Simulation and Edge Acquisition Fidelity

Status: ready-for-dev

<!-- Note: Validation is optional. Run validate-create-story for quality check before dev-story. -->

## Story

As a researcher,
I want the simulated compressor operating state, transmitter-side observation, and edge acquisition payload to be modeled more faithfully,
so that the prototype preserves pre-PLC physical acquisition semantics without redesigning the existing MQTT, consensus, SCADA, persistence, or LSTM pillars.

## Scope Notes

- This story is limited to the sensor simulation layer and the Python edge acquisition service.
- It introduces a hidden compressor operating-state model such as `compressor_load_pct` or `driver_speed_pct`.
- It introduces a simulated transmitter-observation layer and a gateway acquisition payload that remains HART-inspired and defensible for the proposal.
- `PV` is mandatory and remains the primary measured variable.
- `SV` is optional and only appears when it has a real transmitter-side meaning for that sensor type.
- Generic compressor context must not be stored in `SV`.
- Suggested sensor ranges remain configurable prototype defaults, not plant-calibrated truth.
- This story is an additive, refinement-first correction. Preserve downstream contracts by default and introduce only additive optional fields if strictly required.

## Acceptance Criteria

1. Given the refined acquisition-fidelity boundary, when the simulator and edge acquisition path are updated, then the acquisition path follows exactly three layers: hidden compressor/process state, simulated transmitter observation, and gateway acquisition payload.
2. Given the hidden operating state such as `compressor_load_pct` or `driver_speed_pct`, when it changes, then it deterministically influences temperature, pressure, and RPM evolution in a plausible and explainable way.
3. Given the transmitter-side semantics, when a sensor observation is converted into a gateway payload, then `PV` is mandatory for every transmitter-style sensor and `SV` is optional and only present when justified by the sensor type.
4. Given the semantic guardrails, when the payload is emitted, then generic compressor context is not stored in `SV` and the payload preserves transmitter semantics rather than acting as a generic float wrapper.
5. Given the refined payload, when it is emitted, then it remains HART-inspired and includes `device_info`, `process_data`, `diagnostics`, `loop_current_ma`, `pv_percent_range`, and simple physics metrics.
6. Given the architecture invariants, when this story is implemented, then each edge still acquires only its assigned local sensor, remains an independent local observer, and the acquisition path remains pre-PLC and non-intrusive in meaning.
7. Given the additive/refinement-first constraint, when the story is implemented, then existing downstream contracts remain stable by default and only additive optional fields may be introduced if strictly required.
8. Given the downstream pipeline, when the revised payload is consumed later, then it remains suitable for consensus, SCADA comparison, and LSTM training without redesigning MQTT, CometBFT, fake OPC UA SCADA, MinIO, or the downstream LSTM flow.
9. Given the validation needs, when tests and demo evidence are produced, then they prove normal flow, hidden operating-state influence, edge isolation, PV/SV discipline, suspicious-edge behavior, replay/temporal inconsistency support, SCADA-divergence support, and evaluator-facing acquisition correctness.

## Tasks / Subtasks

- [ ] Define the hidden compressor operating-state model. (AC: 1, 2, 7)
  - [ ] Add a small internal process-state driver such as `compressor_load_pct` or `driver_speed_pct`.
  - [ ] Use it to drive temperature, pressure, and RPM evolution deterministically.
  - [ ] Keep the model simple, explainable, and suitable for demonstration.
- [ ] Introduce a simulated transmitter-observation contract. (AC: 1, 3, 4, 5)
  - [ ] Represent the sensor-side output as a transmitter-like observation rather than a bare numeric reading.
  - [ ] Keep the contract local to simulation and acquisition.
  - [ ] Preserve transmitter semantics without introducing a full protocol stack.
- [ ] Refine the simulator to emit transmitter-like observations. (AC: 1, 2, 5, 7)
  - [ ] Replace the earlier generic `compressor_power` framing with the hidden operating-state model.
  - [ ] Keep ranges configurable prototype defaults, not plant-calibrated truth.
  - [ ] Preserve deterministic behavior for tests and demos.
- [ ] Refine the edge acquisition interpreter. (AC: 1, 3, 4, 5, 6, 7, 8)
  - [ ] Read the simulated transmitter observation and map it into the current gateway payload shape.
  - [ ] Keep `PV` mandatory.
  - [ ] Treat `SV` as optional and sensor-justified only.
  - [ ] Do not store generic compressor context in `SV`.
- [ ] Add a narrow HART reference/contract layer for semantics and tests only. (AC: 5, 7, 9)
  - [ ] Keep that layer non-runtime and test/reference-only.
  - [ ] Use it only to defend payload semantics and field-side naming.
  - [ ] Do not alter the live runtime acquisition path.
- [ ] Add tests and observable evidence. (AC: 2, 3, 4, 6, 8, 9)
  - [ ] Verify normal flow.
  - [ ] Verify hidden operating-state influence.
  - [ ] Verify edge isolation.
  - [ ] Verify PV/SV discipline.
  - [ ] Verify suspicious-edge behavior remains representable.
  - [ ] Verify replay / temporal inconsistency remains representable.
  - [ ] Verify the payload carries enough context for later SCADA-divergence support.
  - [ ] Verify evaluator-facing logs and payload evidence.

## Dev Notes

- This story is an Epic 1 fidelity refinement and must be completed before Epic 3 begins. [Source: [epics.md](/c:/Users/emili/Desktop/Projets/parallel-truth-fingerprint-prototype/_bmad-output/planning-artifacts/epics.md)]
- The split proposal files in `docs/input/` remain the research source of truth for this story. Older simplified wording must be treated as superseded where it conflicts with the refined interpretation.
- The acquisition path is frozen as a 3-layer model:
  - hidden compressor/process state
  - simulated transmitter observation
  - gateway acquisition payload
- The hidden operating state belongs only in the simulator/process model or debug metadata when needed. It is not `PV` and not `SV`.
- `PV` is mandatory for every transmitter-style sensor.
- `SV` is optional and only appears when a defensible transmitter-side secondary variable exists for that sensor type.
- Suggested ranges remain configurable prototype defaults, not plant-calibrated truth.
- This story must be implemented as an additive/refinement-first correction.
- Preserve downstream contracts as much as possible.
- Do not break existing MQTT, consensus, SCADA, storage, or LSTM interfaces unless an additive optional field is strictly required.
- Prefer local refinement at the simulator/acquisition boundary over broad refactors.

### Project Structure Notes

- Primary implementation areas:
  - `src/parallel_truth_fingerprint/sensor_simulation/`
  - `src/parallel_truth_fingerprint/edge_nodes/common/`
  - `src/parallel_truth_fingerprint/contracts/`
  - `tests/sensor_simulation/`
  - `tests/edge_nodes/`
- Supporting areas if directly needed:
  - `docs/input/hart_payload_sample.txt`
  - `docs/input/unified_hart_payload_sample.txt`
- Do not touch unless strictly required by an additive optional field:
  - `edge_nodes/common/mqtt_io.py`
  - `consensus/`
  - `comparison/`
  - `scada/`
  - `persistence/`
  - `lstm_service/`

### Technical Requirements

- Keep one edge per local sensor.
- Keep the edge as a local reader/interpreter, not a controller or validator.
- Use a hidden operating-state driver such as `compressor_load_pct` or `driver_speed_pct`.
- Make the simulator output transmitter-like observations rather than only raw floats.
- Keep `PV` mandatory and `SV` optional.
- Preserve `loop_current_ma`, `pv_percent_range`, diagnostics, and simple physics metrics in the payload.
- Keep the payload suitable for later consensus, SCADA comparison, and LSTM without redesigning those systems.

### Architecture Compliance

- Preserve pre-PLC non-intrusive semantics.
- Preserve MQTT/Mosquitto unchanged.
- Preserve CometBFT unchanged.
- Preserve fake OPC UA SCADA unchanged.
- Preserve MinIO unchanged.
- Preserve downstream LSTM unchanged.
- Keep the HART reference/contract layer non-runtime and test/reference-only.
- Do not claim real HART hardware or a full HART protocol stack.

### Library / Framework Requirements

- Prefer staying within the current Python project structure.
- Any HART reference/contract dependency must remain narrow, non-runtime, and test/reference-only.
- Do not introduce unnecessary infrastructure or protocol complexity.

### File Structure Requirements

- Likely implementation areas:
  - `src/parallel_truth_fingerprint/sensor_simulation/simulator.py`
  - `src/parallel_truth_fingerprint/sensor_simulation/behavior_model.py`
  - `src/parallel_truth_fingerprint/edge_nodes/common/acquisition.py`
  - `src/parallel_truth_fingerprint/contracts/raw_hart_payload.py`
  - new or refined simulation/acquisition contracts if needed
- Keep downstream interfaces stable unless an additive optional field is strictly required.

### Testing Requirements

- Add focused tests for:
  - normal flow
  - hidden operating-state influence
  - edge isolation
  - PV/SV discipline
  - suspicious edge
  - replay / temporal inconsistency
  - SCADA-divergence support
  - evaluator-facing evidence in logs and payloads
- Keep tests deterministic and demonstration-friendly.

### Previous Story Intelligence

- Story 1.2 established the simulator foundation but used earlier simplified `compressor_power` wording. This story refines that wording and behavior into a hidden operating-state model without changing Epic 1 intent.
- Story 1.3 established one-edge-per-sensor acquisition and pre-PLC semantics. This story refines the acquisition interpretation so the edge reads a simulated transmitter observation and maps it into the gateway payload while preserving PV/SV discipline.
- Story 1.5 established observability and demonstration visibility. This story should extend that observability to show the hidden process state, transmitter observation, and gateway payload creation clearly.

### References

- Split proposal source of truth:
  - [ARQUITETURA_PROPOSTA.txt](/c:/Users/emili/Desktop/Projets/parallel-truth-fingerprint-prototype/docs/input/Arquitetura%20Baseada%20em%20Fonte%20de%20Verdade%20Paralela%20para%20Gera%C3%A7%C3%A3o%20de%20Fingerprint%20F%C3%ADsico-Operacional%20em%20Sistemas%20Industriais%20Legados_ARQUITETURA_PROPOSTA.txt)
  - [REVISAO_DA_LITERATURA.txt](/c:/Users/emili/Desktop/Projets/parallel-truth-fingerprint-prototype/docs/input/Arquitetura%20Baseada%20em%20Fonte%20de%20Verdade%20Paralela%20para%20Gera%C3%A7%C3%A3o%20de%20Fingerprint%20F%C3%ADsico-Operacional%20em%20Sistemas%20Industriais%20Legados_REVISAO_DA_LITERATURA.txt)
  - [hart_payload_sample.txt](/c:/Users/emili/Desktop/Projets/parallel-truth-fingerprint-prototype/docs/input/hart_payload_sample.txt)
  - [unified_hart_payload_sample.txt](/c:/Users/emili/Desktop/Projets/parallel-truth-fingerprint-prototype/docs/input/unified_hart_payload_sample.txt)
- Planning artifact:
  - [epics.md](/c:/Users/emili/Desktop/Projets/parallel-truth-fingerprint-prototype/_bmad-output/planning-artifacts/epics.md)

## Dev Agent Record

### Agent Model Used

GPT-5 Codex

### Debug Log References

- Story created from the approved freeze for Epic 1 Story 1.6.
- No development should start before this story artifact is created and approved.

### Completion Notes List

- Finalized Story 1.6 as an additive/refinement-first correction.
- Preserved downstream contracts by default and limited changes to the simulator/acquisition boundary.
- Captured the 3-layer acquisition model, PV/SV discipline, and non-runtime HART reference rule.

### File List

- `_bmad-output/implementation-artifacts/1-6-refine-sensor-simulation-and-edge-acquisition-fidelity.md`
