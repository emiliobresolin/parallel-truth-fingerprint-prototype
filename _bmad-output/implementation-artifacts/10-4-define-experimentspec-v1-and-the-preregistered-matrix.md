# Story 10.4: Define `ExperimentSpec.v1` and the Preregistered Matrix

Status: ready-for-dev

<!-- Note: Planning READY does not authorize implementation, source acquisition, profile/mock admission, feature activation, experiment execution, command emission, syscall capture, persistence, truth creation/unlock, training, evaluation, publication, or dashboard work. -->

## Story

As a research owner,
I want a versioned experiment specification and deterministic scenario matrix,
so that physical runs are declared before evidence collection without hidden schedules or numeric choices.

## Acceptance Criteria

1. **Given** only the applicable implemented public contracts for canonical identity/bytes, semantic/audience roles, source use, parameter/mock gates, v1 quarantine, immutable manifests, activity authorization, admitted profiles, `SignalObservation.v2`, and Story 10.3 producer inputs **When** Story 10.4 is implemented **Then** it adds only one flat immutable `ExperimentSpec.v1` contract, a pure validator/matrix projection, focused offline tests and documentation **And** it adds no runner, scheduler, controller command, process/transmitter/edge implementation, MQTT/broker, storage, truth record, dataset, detector, calibration, evaluation, CLI, service, database, dashboard or UI. An absent or incompatible prerequisite blocks implementation rather than receiving a local substitute.

2. **Given** a proposed `ExperimentSpec.v1` **When** it is canonically built and validated **Then** it has stable experiment and predeclared immutable run-identity bindings (never generated or allocated here), schema/version/content identity, exact decision/parameter/profile/mock-admission/code/runtime/input/manifest references, one closed `stimulus_identity` binding of either an immutable input-trace identity or a precommitted seed plus exact RNG/code/runtime identity, phases, schedule descriptors, opaque scenario/intervention/recovery references, expected stream contracts with exact schema/audience/profile bindings, partition/metric/stopping/abort/truth-unlock policy references, explicit applicability disposition and limitations **And** the current path accepts only input trace; a seed is an opaque precommitted input identity rather than an implied PRNG or domain numeric value. Every required slot is `bound`, independently permitted `not_applicable`, or `unavailable_blocking`; `null`, empty values, defaults, filenames, environment, host time, mutable runtime state or hidden code configuration cannot complete it. Any content or identity-bearing metadata change produces a new immutable identity.

3. **Given** a value or rule that can affect construction, declared schedule, matrix membership, command representation, evidence eligibility, stopping/abort behavior, partition, metric or comparison result **When** the spec validates it **Then** every executable numeric locus, including every locus declared by a schedule descriptor, resolves through exactly one applicable Story 9.4 `ParameterEvidence.v1` with matching quantity/unit/class/scope and its class-specific authority; every nonnumeric project choice resolves through an exact frozen applicable decision/binding, while source documents establish only their bounded claims **And** an unresolved duration, rate, noise, dynamic, tolerance, intervention magnitude, repetition, safety/abort limit, ordering, split, metric or code/runtime/input identity blocks rather than gaining a default. The v1 contract validates reference closure and declared-locus inventory only; Story 9.4 remains the sole evaluator of parameter semantics and source contents. Structural schema/version tokens and conspicuous test-only sentinels are not domain values; no legacy v1 value/formula may enter formal v2.

4. **Given** the planning-frozen `decision-custom-reference-window-v1`, the exact command-profile identity `instrument-profile-cds803-terminal53-linear-0-100-v1`, and their fully admitted future dependencies **When** the requested reference variation is declared **Then** it is named exactly `speed_reference_pct`, classified `preregistered_factor`, constrained by the decision's 25 and 75 percent factors, and represented by one explicit `ReferenceFactorBinding` containing the frozen decision revision, exact factor parameter revisions, command-profile revision, direct 0/100 profile parameter revisions and derived 8/16 parameter revisions **And** it is explicitly prohibited from meaning electrical power, manufacturer recommendation, universal compressor range, safety or efficiency limit. Danfoss AU356039245821 en-000201 / 130R0597, printed p. 54 Tables 60-63, supports only Terminal 53 6-12=4 mA and 6-13=20 mA configuration plus the correspondence of 6-14/6-15; the project decision, not Danfoss, selects 6-14=0 and 6-15=100. Within this exact frozen 0-100/4-20 mA command factor, 8 mA derives from 25 percent and 16 mA from 75 percent; these are not universal drive endpoints or `SignalObservation` conversion values. `capacity_reference_pct` is `unavailable_blocking` unless a separate immutable decision and exact applicable parameter records are bound; it cannot alias or reuse this speed decision or its 8/16 derivations. Any ramp, dwell, settling, order, repetition, noise, safety or tolerance remains separately evidenced/preregistered or blocks.

5. **Given** one structurally frozen immutable spec and an injected deterministic matrix projection **When** its declared rows are enumerated **Then** the result is a stable ordered projection of only the supplied predeclared run binding, a derived row-content ID, bound phase/reference/opaque scenario/intervention/recovery/expected-stream identities, planned disposition and allowed-outcome-policy reference **And** it neither claims nor records an achieved valid, invalid, aborted, unavailable or unfavorable outcome. A structurally frozen candidate may retain explicit `unavailable_blocking` slots but is not execution-eligible; only a fully bound candidate plus later matching authorization can become execution-eligible. The projection does not invent a timing cadence, generate a command, execute a run, allocate an execution-run identity, infer a missing scenario, attach scenario truth/labels/intervals, claim synchronized fusion eligibility, or persist an evidence artifact. The exact semantic content and restricted writer of `ScenarioTruth.v1` remain Story 10.5 responsibilities, and Story 10.6 alone records actual execution outcomes.

6. **Given** a physical-only, accelerated, fixture or otherwise incomplete proposal **When** it is declared or inspected **Then** its evidence role, dataset/track scope, synchronization and limitations are explicit and it is labelled only controlled custom physical or test evidence as applicable **And** it cannot be labelled real-plant, authentic hardware, validated digital twin, official-real, complete `PTFP-Custom-v1`, or fusion-eligible synchronized evidence merely because a spec/matrix validates structurally. The presently blocked pressure archive, unresolved RPM endpoints, planning-conditional signal-emulator admission and missing implemented prerequisites keep any project-domain executable spec `unavailable_blocking`.

7. **Given** a spec and matrix freeze succeeds structurally **When** a later caller asks to activate or execute it **Then** the candidate must first be execution-eligible with no `unavailable_blocking` slot, and the caller must independently present an exact approved Story 9.8 `ActivityAuthorization.v1` for the separately registered `feature_activation` or `experiment_execution` action with matching immutable spec/matrix/profile/parameter/mock/code/runtime/input scope **And** Story 10.4 only validates matching identities and reports `authorization_effect: none`; it does not issue, approve, mutate, cache, substitute for, or retroactively bless authorization. A post-freeze change, unresolved scope, pending/conditional admission, or activity mismatch fails closed and requires a new candidate identity and later authorization.

8. **Given** Story 10.4 tests, docs and planning fixtures run offline **When** their output is inspected **Then** canonical bytes/content IDs, strict parser behavior, declared run-binding preservation, closed stimulus binding, required-slot closure, parameter/unit/class/scope resolution including hidden descriptor loci, 25/75 and derived 8/16 provenance, explicit unavailable/not-applicable and structural-freeze/execution-eligibility states, matrix determinism/planned-disposition retention, truth isolation, immutability/new identity, authorization non-effect, legacy quarantine and command/control isolation are covered with conspicuous non-domain fixtures **And** no import/test uses network, source/dataset acquisition, device, broker, clock/random/environment default, Docker/MinIO, runtime demo, command, capture, persistence, formal project evidence write, training, evaluation, dashboard or UI. Absence of a dashboard/UI cannot block freeze, matrix projection or authorization-compatibility validation. Every Story 10.4-owned success/failure result retains `authorization_effect: none`.

## Amendment Acceptance Criteria

**Given** custom physical evidence, its specification, persistence request, or qualification input
**When** it is admitted to a formal path
**Then** its closed origin, prototype generation binding, per-field mock influence, exact parameter authority, immutable trace, and current `DirectReproductionAssessment.v1` are resolved where applicable
**And** missing/mismatched generator, source-use, parameter, assessment, origin, or trace blocks formal evidence without creating a fallback or changing experiment control.

- [ ] Add focused non-domain `unittest` cases for valid reconstruction and every missing/mismatched closure element, including an authentically reproducible behavior that invalidates a prior mock admission.
## Tasks / Subtasks

- [ ] Task 1: Enforce the narrow planning-contract boundary and upstream gates (AC: 1, 3, 6-8)
  - [ ] Require only the directly consumed public exports and focused suites from Stories 9.1-9.8 and 10.1-10.3. Stop with structured prerequisite failure if canonicalization, semantic/audience, source/parameter/mock, manifest, activity authorization, admitted profile, observation or producer-input contracts are absent/incompatible; do not recreate compatibility types locally.
  - [ ] Keep `scenario_control/runtime.py`, `scripts/run_local_demo.py`, legacy scenarios, `CompressorSimulator`, legacy MQTT, persistence, consensus, SCADA and dashboard unchanged. Do not connect a formal spec to current runtime configuration or give the existing dashboard a new dependency.
  - [ ] Treat every current formal project-domain candidate as blocked: exact profiles are not all admitted, RPM endpoints are unresolved, the pressure source bytes are unarchived, and `mock-admission-ptfp-signal-emulator-v1` is planning-conditional. Fixtures are `fixture_test`/`fixture_expected`/`test_only`; formal resolvers reject them.

- [ ] Task 2: Add the smallest immutable spec and matrix contracts (AC: 1-2, 5-8)
  - [ ] Add `src/parallel_truth_fingerprint/contracts/experiment_spec.py` with frozen tuple-backed contract values, closed enum tokens, canonical `to_dict()`/strict parser hooks and deterministic content identity. Re-export only intended public types from `contracts/__init__.py`; do not introduce a generic workflow, scenario or truth-record family.
  - [ ] Model predeclared run bindings, the closed `stimulus_identity`, phases, schedule descriptors, expected stream contracts with schema/audience/profile bindings, policy references and applicability as compact immutable references/dispositions. A schedule descriptor identifies evidence-backed inputs and its complete numeric-locus inventory; it is not a timer, loop, command or execution plan. The current path admits immutable input-trace identity only; a later seed path must bind seed plus exact RNG/code/runtime identity.
  - [ ] Add one pure `ExperimentSpecValidator` and deterministic matrix projection in the same module unless a small adjacent helper makes the public contract clearer. Both accept injected immutable resolvers only; neither reads files, clocks, environment, config, services or runtime state.
  - [ ] Preserve separately: candidate validation, structural freeze, execution eligibility, later authorization and later execution. A matrix row retains the predeclared run binding plus a derived row-content ID but never allocates an execution-run identity or records actual outcome.
  - [ ] Return a content-addressed result with bounded audience-safe diagnostics and `authorization_effect: none` on every path.

- [ ] Task 3: Close numeric, decision and command-representation provenance (AC: 3-4, 6-8)
  - [ ] Resolve each declared numeric spec locus to the exact Story 9.4 parameter identity and verify closure, quantity/unit, class/scope, limitation and status against the injected gate result. Story 10.4 does not re-evaluate parameter semantics/source contents. Reject a concealed descriptor locus, domain value/formula/tolerance copied from legacy code, a source citation used as researcher-factor authority, class promotion, or a missing required parameter.
  - [ ] Implement an explicit `ReferenceFactorBinding` for the 25/75 speed declaration only through `decision-custom-reference-window-v1`, `instrument-profile-cds803-terminal53-linear-0-100-v1`, exact factor revisions, direct 0/100 parameter revisions and derived 8/16 parameter revisions. Verify 0/100 are frozen project selections, 4/20 are bounded documented profile facts, and 8/16 are deterministic command-factor representations whose inputs/profile match exactly. Reject `capacity_reference_pct` until its own decision and parameter records exist.
  - [ ] Do not create a schedule numeric merely to make a matrix executable. Missing ramp/dwell/settling/order/repetition/noise/safety/abort/tolerance/metric/split evidence remains explicit `unavailable_blocking` or independently permitted `not_applicable`.
  - [ ] Require a valid immutable approved `MockAdmission.v1`, an `accountable` required parameter-gate result and `unavailable_with_evidence` only for mock-classified behavior/value. Direct, derived, measured and preregistered-factor inputs retain their own exact authority and cannot be relabelled mock.

- [ ] Task 4: Preserve truth, execution and control boundaries (AC: 5-8)
  - [ ] Permit only opaque scenario/intervention/recovery and truth-unlock-policy references in the spec. Reject labels, truth intervals, future annotations, detector scores, syscalls, fusion decisions, actuator state/commands and consumer-visible outcomes; Story 10.5 alone defines restricted `ScenarioTruth.v1`.
  - [ ] Project matrix rows from frozen declarations without creating commands, clock-based schedules, retries, execution IDs, persistence records or any achieved outcome. Each row retains only its predeclared run binding, derived row-content ID, planned disposition and allowed-outcome policy. Story 10.6 owns actual authorized execution/collection/persistence/outcomes and Story 10.7 owns qualification/G2; no local fallback to a demo scenario is permitted.
  - [ ] Validate a supplied authorization reference only for identity/scope/action compatibility after execution-eligibility rejects every `unavailable_blocking` slot, and prove no result can approve or invoke activation/execution/control. Do not add credentials, controller callbacks, feature flags, event consumers or dashboard hooks.

- [ ] Task 5: Document and test the limited contract (AC: 1-8)
  - [ ] Add `docs/experiment-spec-v1.md` with a one-way ownership diagram, required-reference table, numeric authority ledger, exact 25/75-to-8/16 derivation boundary, applicability rules, matrix projection semantics, truth/control/authorization limits, current blockers and downstream ownership.
  - [ ] Add `tests/contracts/test_experiment_spec.py` and, only if needed, `tests/contracts/test_experiment_matrix.py`. Use exact Decimal and immutable conspicuous sentinel fixtures; do not create project-domain specs or new source/catalog files.
  - [ ] Test strict unknown/duplicate fields, canonical byte/hash oracle, absent/generated/derived run-binding rejection, closed trace-versus-seed stimulus binding, empty/defaulted/inferred slot rejection, every parameter class, concealed descriptor numeric rejection, 25/75 speed provenance and blocked capacity alias, wrong command profile/derivation inputs, blocked profile/mock states, no implicit schedule numeric, matrix ordering/planned-disposition/allowed-outcome-policy retention without achieved outcome, truth leakage, new identity after any change, structural-freeze versus execution-eligibility, authorization mismatch/non-effect, dashboard-independence, command import/call guard and v1 quarantine.
  - [ ] Run focused implemented prerequisite suites, the Story 10.4 suite and full Python `unittest` discovery. If upstream contracts are still planning-only, record the prerequisite blocker instead of implementing placeholders or claiming a formal runtime proof.

## Dev Notes

### Minimal scope, ownership and authorization

- This is a flat plan contract, not an experiment-control subsystem. It makes declared input identities inspectable before evidence collection; it does not make them executable.
- The minimal flow is: immutable decision/parameter/profile/mock/input references -> `ExperimentSpec.v1` strict validation -> structural freeze (which may retain blockers) -> deterministic matrix projection -> execution-eligibility closure -> later independently authorized feature activation/execution -> Story 10.6 collection. Neither the spec nor the matrix can write a command.
- UI/UX is optional and out of scope. A later read-only dashboard may display already authorized immutable evidence, never plan validation as a readiness substitute.
- Every created or validated value in this story has `authorization_effect: none`. `ready-for-dev` concerns this planning document only.

### Exact reference-factor boundary

```text
Danfoss Tables 60-63: Terminal 53 current/reference configurability
  + DecisionRecord.v1: selected 0/100 reference window; frozen 25/75 speed factors
  + exact 0-100 / 4-20 mA command profile
  + ReferenceFactorBinding: decision + factor + profile + 0/100 + 8/16 revisions
  -> derived command representations: 25% = 8 mA; 75% = 16 mA
  -> ExperimentSpec.v1 reference declarations
  -> deterministic matrix descriptors only
  -> later authorized control/execution (Story 10.6), never this story
```

- The manufacturer does not recommend 25/75 and does not establish power, safety, efficiency, a universal compressor operating range, timing or repetition. The decision is the value authority only for `speed_reference_pct`; `capacity_reference_pct` needs a different exact frozen decision and parameter closure.
- `8 mA` and `16 mA` are exact command-factor derivations only under the selected frozen command profile and inputs; do not generalize them as real-drive endpoints or `SignalObservation` conversion values.
- Any new result-affecting number or physical behavior triggers Story 9.3/9.4 research and gate work before it may enter an executable spec. No new source is adopted merely to make this story pass.

### Mock, profile and current blocker rules

- A mock-classified value may appear only after its own immutable `MockAdmission.v1` is structurally `valid`, approval state `approved`, required `ParameterGateResult.v1` outcome `accountable`, and authentic-path feasibility `unavailable_with_evidence`, with exact strongly applicable official source/use locators and direct final paired custom-comparison linkage.
- The current planning YAML is migration input, not an active execution admission. The physical path remains a controlled signal emulator, never real plant/hardware/digital-twin evidence.
- Do not hide blockers with legacy 48-95 degC, 1.8-8.5 bar, 1200-4200 RPM, noise, timing, formula, tolerance or scenario defaults. The current P200 archive and RPM endpoint blockers make formal project-domain execution unavailable.

### Truth, stream and matrix boundaries

- The spec can bind opaque IDs and a truth-unlock-policy reference, but it cannot carry `ScenarioTruth.v1`, labels, intervals or intervention semantics available to detector-facing consumers. Story 10.5 owns the restricted record and unlock.
- Expected-stream descriptors name contracts and applicability only. They do not claim a successful physical stream, authentic syscall capture, synchronization, data completeness or fusion eligibility; those facts arise only in later authorized work.
- The matrix enumerator preserves only the declared planned disposition and allowed-outcome policy, never an achieved outcome. It is not a scheduler and must not sample time, derive cadence, allocate execution IDs or filter evidence.

### Current repository hazards and structure

- `scenario_control/runtime.py` and `config/runtime.py` are v1 demo/control paths. They use mutable config and scenario behavior; formal v2 must not import or adapt them.
- Existing `contracts/` has legacy mutable application records but no v2 evidence/ExperimentSpec public API. Add the smallest new module after upstream Stories 9.1-9.8, 10.1-10.3 provide their intended exports; do not reuse a legacy data class because similarly named fields exist.
- Keep all current demo, dashboard, MQTT, persistence, consensus, SCADA, sensor simulation and existing test behavior unchanged.

### Downstream ownership

- Story 10.5 owns restricted scenario truth and truth unlock implementation.
- Story 10.6 owns independently authorized run execution, commands, evidence collection, stream completeness, persistence and formal project-domain artifacts.
- Story 10.7 owns G2/real parity qualification and publication of physical experiment evidence.
- Epic 11 owns consensus, Epic 12 independent OPC evidence, Epic 17A synchronized custom campaign/fusion eligibility, and Epic 18 optional presentation.

### Project structure notes

- Contract and pure validator/matrix: `src/parallel_truth_fingerprint/contracts/experiment_spec.py`.
- Public exports only: `src/parallel_truth_fingerprint/contracts/__init__.py`.
- Human documentation: `docs/experiment-spec-v1.md`.
- Focused tests: `tests/contracts/test_experiment_spec.py` and optional `tests/contracts/test_experiment_matrix.py`.
- No new dependency, source/catalog artifact, runtime configuration, command executor, storage layer, service, CLI, UI/dashboard edit or formal experiment data.

### Amendment enforcement: preregistered generation closure

The frozen specification/matrix must bind the permitted prototype-generation binding, required output trace role, and the exact parameter/admission closure for each mock-parameterized behavior. No later generator, configuration, source locator, or seed identity may be selected after results are visible.
## BMAD Party Mode Review

- Initial review: product/PM `8.80` (no veto), architecture `8.60` (veto), academic/QA `8.80` (no veto); aggregate `8.73`. The story was revised rather than approved.
- Applied corrections: made run bindings predeclared rather than execution-allocated; separated structural freeze from execution eligibility; limited this story to reference closure while preserving Story 9.4 as parameter/source semantics evaluator; made the matrix retain planned disposition and allowed-outcome policy rather than actual outcomes; closed trace-versus-seed stimulus binding; added schema/audience/profile stream bindings; added the exact `ReferenceFactorBinding`; restricted the 25/75 and 8/16 mapping to `speed_reference_pct`; explicitly blocked a `capacity_reference_pct` alias; and made UI absence non-blocking.
- Final review: product/PM `9.70` (no veto), architecture `9.70` (no veto), academic/QA `9.70` (no veto); aggregate `9.70`.
- Decision: auto-approved for `ready-for-dev` because the aggregate is at least `9.0` and no reviewer veto remains.
- Boundary: Party Mode approves only this planning artifact; every Story 10.4-owned result has `authorization_effect: none`.

### References

- [Source: _bmad-output/planning-artifacts/epics.md#Story 10.4: Define `ExperimentSpec.v1` and the Preregistered Matrix]
- [Source: _bmad-output/planning-artifacts/prd.md#FR75-FR77]
- [Source: _bmad-output/planning-artifacts/prd.md#NFR38-NFR42]
- [Source: _bmad-output/planning-artifacts/prd.md#NFR44-NFR52]
- [Source: _bmad-output/planning-artifacts/architecture.md#Controlling V2 Architecture Consolidation - 2026-08-22]
- [Source: _bmad-output/planning-artifacts/architecture.md#Exact command-profile and parameter mapping]
- [Source: _bmad-output/planning-artifacts/architecture.md#Bounded physical signal emulator admission]
- [Source: _bmad-output/implementation-artifacts/9-3-build-the-authoritative-source-evidence-catalog.md]
- [Source: _bmad-output/implementation-artifacts/9-4-build-the-parameter-evidence-catalog-and-validation-gate.md]
- [Source: _bmad-output/implementation-artifacts/9-6-define-immutable-artifact-and-evaluation-manifests.md]
- [Source: _bmad-output/implementation-artifacts/9-8-define-partition-freeze-and-activity-authorization-records.md]
- [Source: _bmad-output/implementation-artifacts/10-1-define-evidence-backed-instrument-profiles.md]
- [Source: _bmad-output/implementation-artifacts/10-2-define-and-validate-signalobservation-v2.md]
- [Source: _bmad-output/implementation-artifacts/10-3-separate-process-physics-from-transmitter-and-edge-evidence.md]
- [Source: docs/reference-archive/catalog/decision-custom-reference-window-v1.yaml]
- [Source: docs/reference-archive/catalog/parameter-evidence.csv]
- [Source: docs/reference-archive/catalog/mock-admission-ptfp-signal-emulator-v1.yaml]
- [Source: docs/reference-archive/catalog/legacy-constant-quarantine-v1.csv]
- [Danfoss VLT CDS 803 Programming Guide](https://assets.danfoss.com/documents/273384/AU356039245821en-000201.pdf)

## Mandatory Academic Evidence Amendment

Before implementation, apply the relevant mandatory controls in [Academic Evidence Admission Amendment — 2026-08-31](../planning-artifacts/academic-evidence-admission-amendment-2026-08-31.md). This story must fail closed on an unresolved evidence origin, numeric authority, required mock closure, or prohibited dataset substitution. The amendment adds no activity authorization.
## Dev Agent Record

### Agent Model Used

### Debug Log References

### Completion Notes List

### File List
