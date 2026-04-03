# Story 6.1: Establish Fingerprint Readiness Evidence and Meaningful-Validity Gate

Status: drafted

## Story

As a researcher and demo operator,
I want the prototype to present explicit fingerprint readiness evidence and a meaningful-validity gate derived from existing artifacts,
so that the fingerprint can be explained honestly and more defensibly during an academic demonstration without changing the ML architecture.

## Scope Notes

- This story is limited to readiness evidence, provenance visibility, and academically honest claim framing for the existing fingerprint path.
- It must preserve the five real pillars exactly as they already exist:
  - acquisition of sensor values
  - decentralization across edges
  - Byzantine consensus across edges
  - comparison between consensused data and SCADA data
  - LSTM-based fingerprint generation
- It must reuse the current:
  - persisted dataset artifacts
  - adequacy evaluation
  - trained-model metadata
  - inference results
  - replay behavior outputs
  - MinIO persistence boundary
- It must not add:
  - a new ML model family
  - a new anomaly engine
  - a new backend service
  - a new storage boundary
  - a new research scope

## Limitation Carried Forward

The fingerprint must still be presented honestly when the adequacy floor remains unmet. Until the source dataset reaches the approved floor of 30 eligible normal artifacts and 20 generated windows, the fingerprint remains runtime-valid only and must not be presented as academically strong.

## Acceptance Criteria

1. Given the existing persisted dataset artifacts, model metadata, lifecycle state, and inference outputs, when fingerprint readiness is presented, then the readiness view is derived from those existing artifacts only and does not require a new ML path.
2. Given the adequacy requirement, when readiness is evaluated, then the prototype explicitly distinguishes between:
   - `runtime_valid_only`
   - `meaningful_fingerprint_valid`
   and ties that distinction back to the approved adequacy floor of:
   - 30 eligible normal artifacts
   - 20 generated windows
3. Given the provenance requirement, when readiness evidence is shown, then it includes at minimum:
   - model identity
   - source dataset identity
   - training window count
   - threshold origin
   - current limitation statement
4. Given the bounded demo-evidence requirement, when fingerprint readiness is summarized, then the prototype can present a concise evidence matrix for at least:
   - normal operation
   - compressor-power variation
   - replay or freeze behavior
   - SCADA divergence as a separate non-fingerprint channel
5. Given the academic-honesty requirement, when the readiness state is below the meaningful-valid threshold, then the prototype explicitly says what is working, what evidence exists, and what is still not proven.
6. Given the operator-facing wording requirement, when readiness and limitation text is shown in the dashboard or operator surface, then it uses domain language such as fingerprint model, training adequacy, replay detection, anomaly evidence, or model provenance and does not reference internal delivery labels such as Story 4.3, Story 4.4, Story 6.1, or any other BMAD story numbers.
7. Given focused validation, when this story is closed, then testing proves that readiness summaries match the underlying dataset manifest, model metadata, and inference artifacts without overclaiming fingerprint strength.
8. Given the project testing-closeout rule, when Story 6.1 is closed, then the story record explicitly includes:
   - what was tested
   - exact commands executed
   - test results
   - real runtime behavior validated
   - remaining limitations

## Testing Requirements

- Testing is mandatory for this story.
- The story is incomplete unless it includes:
  - focused tests for readiness-state derivation from persisted artifacts
  - focused tests for model-provenance and threshold-origin display
  - focused tests that keep replay evidence distinct from SCADA divergence evidence
  - focused tests that ensure user-facing texts do not leak internal story labels
  - one real runtime validation pass confirming that the readiness view reflects a real local run and remains honest about adequacy limitations

## Dependencies

- Story 4.2A persisted dataset artifacts and adequacy evaluation
- Story 4.2 model training and persisted model metadata
- Story 4.3 fingerprint inference and threshold origin
- Story 4.4 replay-oriented anomaly behavior
- Story 4.6 local operator dashboard
- Story 5.3 translated status and evidence-view infrastructure

## Non-Goals

- no new ML architecture
- no new anomaly engine
- no architecture redesign
- no new backend service
- no new storage boundary
- no claim of academic strength before adequacy is actually met

## Tasks / Subtasks

- [ ] Define the bounded fingerprint readiness states and evidence summary contract. (AC: 1, 2, 5, 6)
- [ ] Expose provenance and threshold evidence from the current dataset/model/inference artifacts. (AC: 1, 3, 4)
- [ ] Add a bounded evidence matrix for normal, power-variation, replay/freeze, and SCADA-divergence interpretation. (AC: 4, 5)
- [ ] Replace internal story-number wording in operator-facing fingerprint texts with domain language. (AC: 6)
- [ ] Add focused tests and one real runtime validation pass. (AC: 7, 8)

## Technical Notes

- The codebase already distinguishes `runtime_valid_only` from `meaningful_fingerprint_valid`; this story should package that distinction into a clearer readiness view rather than invent a new readiness engine.
- The source adequacy floor already exists in the current implementation and should remain the objective criterion.
- This story should clarify the difference between:
  - pipeline validity
  - model availability
  - meaningful fingerprint readiness
- Replay/freeze evidence must remain on the fingerprint side, while SCADA divergence remains on the SCADA-comparison side.

## Real vs Simulated Boundary

- Real in this story:
  - persisted dataset manifest and windows archive
  - adequacy assessment
  - saved model metadata
  - inference results
  - replay behavior outputs
  - MinIO persistence evidence
- Simulated or controlled in this story:
  - compressor/process behavior
  - replay/freeze scenario generation
  - SCADA environment

## Academic Mapping

- This story does not change the fingerprint mechanism.
- It strengthens the academic defensibility of the prototype by clarifying:
  - what evidence exists now
  - what threshold has or has not been met
  - what the prototype can already demonstrate
  - what still remains below an academically stronger adequacy bar
