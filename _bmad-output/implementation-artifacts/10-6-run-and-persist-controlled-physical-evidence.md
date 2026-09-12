# Story 10.6: Run and Persist Controlled Physical Evidence

Status: ready-for-dev

<!-- Planning READY does not authorize implementation, feature activation, experiment execution, physical acquisition, command emission, persistence, truth production, publication, dashboard work, source acquisition, or any scientific claim. Each later action requires its own exact approved authorization and fail-closed gate. -->

## Story

As an experiment operator,
I want an approved controlled physical experiment executed and its raw evidence preserved,
so that later analysis can reconstruct what each instrumented edge observed.

## Acceptance Criteria

1. **Given** the implemented public contracts and validators from Stories 9.1-9.8 and 10.1-10.5, an execution-eligible frozen `ExperimentSpec.v1` and matrix row, exact profiles/parameter set/mock-admission records, code/runtime/input identities, a non-published run-scope/binding projection, and an exact qualified evidence-repository report **When** a controlled run is requested **Then** the coordinator validates every identity, scope, audience, hash, canonical byte representation and requirement-profile slot before any control, producer, repository write, restricted-truth write, receipt creation or other run-created side effect. The projection is neither `RunManifest.v1` nor a receipt; read-only resolution of already immutable prerequisites occurs only through injected strict resolvers and cannot create state **And** absent, changed, stale, conditionally approved, `unavailable_blocking`, incompatible, unqualified or unauthorized input prevents startup with no default, legacy conversion, partial start or fallback. Every applied mock-classified behavior or value must itself resolve to immutable `MockAdmission.v1` state `valid`, approval `approved`, authentic-path status `unavailable_with_evidence`, exact applicable Story 9.3 official source/use locators, direct final paired-custom-comparison linkage and its required `ParameterGateResult.v1` state `accountable`; every other value class retains its own class-specific authority.

2. **Given** startup dependencies resolve **When** authorization is checked **Then** Story 9.8 alone validates two independent approved exact `ActivityAuthorization.v1` records: `feature_activation` for the v2 execution path and `experiment_execution` for the bound experiment/run **And** a future actual-hardware scope additionally requires its exact `physical_acquisition` authorization. Planning approval, a dashboard click, a mock-admission planning record, a repository qualification, or either authorization never substitutes for another action or grants future execution.

3. **Given** an authorized run is active **When** its immutable declared phases and schedule advance **Then** only the narrow experiment-control boundary applies the already-declared references to the engineering-domain research model or admitted emulator **And** the exact Story 10.3 producer path, approved Story 10.1 profile and Story 10.2 `SignalObservation.v2` contract emit assigned edge/sensor observations. Analytics, MQTT, consensus, storage, OPC, detector, syscall, UI/dashboard or presentation input has no route to control and cannot alter a command, schedule or reference.

4. **Given** control/schedule trace events and observations are emitted **When** run evidence is preserved **Then** append-only canonical artifacts retain the experiment/run/matrix-row/stream/edge/sensor/event/sequence/correlation identities; profile, source, parameter and applicable mock identities; caller-supplied source and observed time facts/clock quality; raw current, derived representations and pre-clipping quality/diagnostics **And** observations remain separate per edge and stream, without aggregate substitution, tag inference, float projection, clipping, relabelling or truth fields.

5. **Given** an expected record is missing, duplicated, divergent, late, out of order, invalid, corrupted or cannot be fully persisted **When** collection or finalization observes it **Then** the coordinator records the condition and exact affected identities/interval under the frozen stopping, exclusion, abort or recovery policy, retains all available unfavorable/invalid evidence, and records actual run status as `complete`, `aborted`, `failed` or `invalidated` **And** no record, timing, value, quality flag, normal state, retry, aggregate or success result is synthesized or silently normalized. An opaque recovery reference never causes an automatic re-command or replay unless its exact frozen policy expressly permits it; otherwise evidence is retained and the run aborts. This is execution collection evidence, not Story 10.7 signal qualification/G2.

6. **Given** a run completes, aborts, fails, recovers or has an unfavorable result **When** its available evidence is closed **Then** raw blind physical evidence, per-edge closure information and control/trace evidence are immutable and reconstructible from their exact identities, the public closure binds opaque immutable identities of the applied `feature_activation`, `experiment_execution` and, where applicable, `physical_acquisition` authorization records plus the declared execution modality/boundary (`engineering_model`, admitted emulator or physical hardware) **And** accelerated or physical-only runs carry the predeclared `non_fusion_eligible` disposition until a later synchronized Epic 17A campaign qualifies them. A missing/partial closure remains visibly incomplete; neither a dashboard nor a later better run rewrites it.

7. **Given** all available public run objects are written **When** publication is attempted **Then** Story 9.6's object-first/read-back/full-closure protocol and Story 9.7's already-qualified repository port verify exact bytes, size and SHA-256 before publishing the immutable public blind-evidence `RunManifest.v1` and its deterministic completion receipt last **And** a write/read/verification fault never exposes a complete receipt early, while orphan immutable objects remain inspectable but incomplete. Restricted `ScenarioTruth.v1` and achieved restricted condition evidence use only the qualified restricted namespace and the Story 10.5/9.8 audience/role closure; no truth, scenario meaning, expected outcome, truth locator or restricted parent may enter detector-facing physical artifacts, diagnostics, manifests or names. Absence, failure or incompatibility of restricted condition evidence preserves already-written blind evidence but makes the run ineligible for truth unlock, join, evaluation or a completed-outcome claim.

8. **Given** the Story 10.6 implementation is tested or documented **When** it is inspected **Then** offline tests use only injected strict v2 control, producer, clock/trace and conditional-create/read-back repository doubles with conspicuous non-domain fixtures **And** prove pre-start closure/no side effect, exact authorization delegation, control exclusivity, canonical bytes/hashes, edge separation, object/manifest/receipt ordering, every persistence fault boundary, retained partial/unfavorable outcomes, collection defects, truth isolation and legacy import guards. Default tests/imports never start hardware, a broker, Docker/MinIO, network, services, dashboard, system clock/random/environment defaults, dataset/source acquisition, capture, detector, evaluation or a formal experiment; live hardware/storage execution is an explicit separately authorized operator action.

## Amendment Acceptance Criteria

**Given** custom physical evidence, its specification, persistence request, or qualification input
**When** it is admitted to a formal path
**Then** its closed origin, prototype generation binding, per-field mock influence, exact parameter authority, immutable trace, and current `DirectReproductionAssessment.v1` are resolved where applicable
**And** missing/mismatched generator, source-use, parameter, assessment, origin, or trace blocks formal evidence without creating a fallback or changing experiment control.

- [ ] Add focused non-domain `unittest` cases for valid reconstruction and every missing/mismatched closure element, including an authentically reproducible behavior that invalidates a prior mock admission.
## Tasks / Subtasks

- [ ] Task 1: Fail closed before any controlled-run side effect (AC: 1-2, 8)
  - [ ] Add only a narrow coordinator at `src/parallel_truth_fingerprint/experiment_control/controlled_physical_run.py` after the named upstream public exports exist. Inject immutable resolvers, trace/time facts, control boundary, Story 10.3 producer, repository port and strict validators; do not add copies of contracts, a scheduler, service, workflow engine, CLI daemon, database, IAM/authentication system or transport policy.
  - [ ] Require validated `ExperimentSpec.v1`/matrix exact-run binding, all profile/parameter/source/mock/code/runtime/input/trace identities, no `unavailable_blocking` slot, qualified exact repository report and a non-published run-scope/binding projection. It is not `RunManifest.v1` and cannot be advertised as a manifest or receipt. Resolve prerequisites read-only through injected strict resolvers before run-created side effects. Reject inferred IDs, `latest`, mutable aliases, environment/default configuration, caller-defined applicability, anonymous numbers and partial eligibility.
  - [ ] For every applied mock-classified behavior/value, resolve rather than merely reference a `valid`/`approved`/`unavailable_with_evidence` `MockAdmission.v1`, exact applicable official source/use locator, direct paired-custom-comparison linkage and `accountable` `ParameterGateResult.v1`. Keep other parameter classes at their own Story 9.4 authority; do not treat an approved-planning-conditional admission as executable.
  - [ ] Delegate action/profile/scope validation to Story 9.8: exact `feature_activation` plus exact `experiment_execution`; require `physical_acquisition` only for a real-hardware scope. The coordinator receives validated results and never issues, persists, broadens, renews or treats them as an identity-provider credential.
  - [ ] Preserve blocked starts as bounded, non-success diagnostics with no command, producer, write, truth, receipt or hidden state mutation.

- [ ] Task 2: Execute only the frozen controlled trace (AC: 3-5, 8)
  - [ ] Apply only caller-supplied frozen phase/trace facts through one experiment-control interface. The interface must not infer a dwell, cadence, queue capacity, timeout, retry, settling, recovery, tolerance, noise, process formula or command value; any such result-affecting policy needs an already valid Story 9.4 record and bound `ExperimentSpec.v1` slot.
  - [ ] Connect exactly the Story 10.3 process/physics-to-transmitter producer with Story 10.1 profile and Story 10.2 canonical `SignalObservation.v2`; consume canonical bytes and verified identity, never full legacy snapshots, tag-to-sensor inference, floats, rounding, clipping or an unprofiled current conversion.
  - [ ] Collect explicit per-edge/per-stream trace and observation facts. Detect and retain missing, duplicate, divergent, late, out-of-order, invalid and persistence-failure intervals under the frozen policy; do not calculate G2, normalize a defect or silently retry it away. An opaque recovery reference cannot auto-recommand/replay unless the exact frozen policy permits it; otherwise retain and abort.
  - [ ] Keep actual restricted condition/intervention/outcome evidence separate from public observations. Durable restricted writes use the Story 10.5 contract and only the qualified restricted repository namespace after its exact audience/semantic closure; public artifacts carry opaque IDs only.

- [ ] Task 3: Preserve and close immutable evidence without qualifying it (AC: 4-7, 8)
  - [ ] Add `src/parallel_truth_fingerprint/evidence/physical_run_persistence.py` only when the upstream evidence/repository packages exist. Map already canonical control/trace and `SignalObservation.v2` bytes to the existing Story 9.6 manifests/repository protocol; keep separate edge stream closure and explicit actual disposition. Do not introduce a competing generic evidence schema, bucket/prefix, mutable run state or aggregate record.
  - [ ] Write content-addressed objects first, exact-byte read back each, assemble/validate the complete run manifest, re-read the manifest and all references from one pinned snapshot, then conditionally create the existing deterministic completion receipt last. Faults leave immutable orphans and an explicit incomplete disposition, never a fake complete result or overwrite.
  - [ ] Bind only observed/reconstructible facts. The public blind-evidence `RunManifest.v1` binds opaque authorization identities and declared execution modality/boundary, never any restricted truth parent/locator/meaning. Preserve unsuccessful, aborted, failed, invalidated, recovered and unfavorable available evidence. Mark accelerated/physical-only evidence only with the predeclared non-fusion-eligible status; no Epic 17A synchronization, fusion qualification, G2 decision, detector evaluation or scientific-publication status belongs here. If restricted condition evidence is absent/invalid, leave public evidence intact but deny later truth-unlock/join/evaluation eligibility and any completed-outcome claim.

- [ ] Task 4: Document the bounded execution boundary and test it offline (AC: 1-8)
  - [ ] Add `docs/controlled-physical-evidence-v1.md` covering prerequisite/authorization order, control boundary, public/restricted evidence table, collection-defect dispositions, immutable publication order, incomplete/orphan semantics, current blockers, mock limitations, legacy quarantine and downstream ownership.
  - [ ] Add focused `tests/experiment_control/test_controlled_physical_run.py`, `tests/evidence/test_physical_run_persistence.py` and, if the current test layout supports it, `tests/integration/test_controlled_physical_run_failures.py`. Use fixed non-domain sentinels and injected fakes only.
  - [ ] Test read-only prerequisite resolution versus blocked-start zero-side-effect; missing/stale/mixed/mismatched prerequisites; each authorization absence/scope/decision failure; mock admission/parameter-gate/value-class failure; real-hardware action locality; only-control invocation; canonical-byte/hash and edge/stream separation; raw/derived/quality preservation; every collection defect including non-permitted recovery; truth/public transitive leak rejection; absence/failure of restricted condition evidence with preserved blind evidence but denied later eligibility; every object/read-back/manifest/receipt fault; idempotent same-byte retry versus conflicting bytes; retained incomplete/unfavorable/recovery disposition; and imports that reject legacy runtime, MQTT, persistence, dashboard, consensus/SCADA/training/network/system-time/environment paths.
  - [ ] Run focused prerequisite suites, Story 10.6 tests and full Python `unittest` discovery. If upstream implementations, qualifying report, evidence records or authorizations are absent, report the blocker; do not add placeholders, use planning records as permission, generate a domain run, claim qualification or run a local demo.

## Dev Notes

### Scope and ownership

- This is the smallest execution/preservation coordinator. It does not make a physical-domain claim, validate signals (Story 10.7/G2), create a generic transport, add consensus/OPC, capture syscalls, synchronize modalities, train/evaluate a detector, publish a scientific result, or provide UI/UX.
- The immutable sequence is: qualified upstream contracts and source/parameter/profile/mock gates -> execution-eligible frozen spec/matrix/run scope -> `feature_activation` authorization -> exact `experiment_execution` authorization -> optional exact `physical_acquisition` authorization for real hardware -> control/producer collection -> objects/read-back -> `RunManifest.v1` -> full closure/read-back -> receipt last. This specifies validation order, not a scheduler or permission system.
- Story 10.7 reconstructs, qualifies and reports this evidence and closes G2. Epic 17A alone can establish synchronized paired custom evidence/fusion eligibility. Epic 18 remains optional read-only presentation.

### Current hard blockers and academic integrity

- All v2 prerequisites are planning-only today. An implementation must stop unless the intended outputs of Stories 9.1-9.8 and 10.1-10.5 exist and pass their focused tests, and Story 9.7 has an exact qualified `StorageQualificationReport.v1`; fakes prove protocol behavior only, never real storage qualification.
- Current domain profile/mock blockers include missing archived official P200 bytes/hash, unresolved FB420 RPM endpoints/configuration, incomplete exact TH320 4-20 mA/configuration evidence, incomplete Danfoss Terminal 53 current-mode verification and only `approved_planning_conditional` emulator admission. No formal real run is eligible while any persists.
- The allowed emulator is a controlled current-domain research boundary only. It cannot support a real-plant, authentic-hardware, compressor-dynamics/digital-twin, safety, energy, efficiency, control-performance, manufacturer-endorsed-range or external-validation claim. Every asserted mock behavior/value needs applicable official evidence and direct paired-custom-comparison linkage; convenience, cost, timing or an unfavorable result never justifies one.
- No v1 number, range, formula, phase, period, noise, timing, threshold or legacy 1200-4200 RPM fallback may enter v2. Structural identifiers and non-domain test sentinels are not domain parameters.

### Repository and integration guardrails

- Do not import, edit or adapt `scripts/run_local_demo.py`, `scenario_control/runtime.py`, `config/runtime.py`, legacy `edge_nodes/common/acquisition.py`, `mqtt_io.py`, `local_state.py`, `persistence/service.py`, `artifact_store.py`, `local_filesystem.py`, dashboard, consensus/CometBFT, SCADA, sensor simulation or training. They are mutable v1 demo paths with labels/defaults, tag inference, network/service side effects or non-qualified persistence.
- `experiment_control` is a narrow control ownership boundary, not a general runtime. `physical_run_persistence` is an adapter to existing Story 9.6/9.7 ports, not a new store. No dependency change is expected; use standard-library `unittest` and existing project canonicalization/contracts rather than a new framework.
- The repository namespace is a structural/audience boundary, not a claim of IAM, encryption, ACLs, authentication, signatures, retention/WORM or crash recovery beyond Story 9.7's exact qualified evidence.

### Project structure notes

- Coordinator: `src/parallel_truth_fingerprint/experiment_control/controlled_physical_run.py`.
- Persistence adapter: `src/parallel_truth_fingerprint/evidence/physical_run_persistence.py` only after upstream packages/exports exist.
- Explicit human guide: `docs/controlled-physical-evidence-v1.md`.
- Offline focused tests: `tests/experiment_control/test_controlled_physical_run.py`, `tests/evidence/test_physical_run_persistence.py`, and optional `tests/integration/test_controlled_physical_run_failures.py`.
- No new dashboard/control surface, broker route, database, generic scheduler, service, bucket/prefix, credential, hardware default, official data download or formal evidence fixture.

### Amendment enforcement: run-scoped provenance

Before a mock-derived physical observation or trace is persisted formally, validate `GeneratedEvidenceProvenance.v1` (or the owned versioned equivalent): producer function/module, code/runtime, input and `ParameterEvidence.v1` identities, admission, official source-use locator/hash, origin, and immutable trace/output identity. Also resolve a newly produced run-scoped `DirectReproductionAssessment.v1`, bound to exact behavior, generation binding, code/runtime/profile, attempt evidence, assessor/approval, and source uses. Only `still_unavailable_with_evidence` passes; `authentic_path_available`, `unresolved`, old/prior-run, or mismatched assessment blocks startup and persistence. Absence, mismatch, or relabelling blocks formal persistence; no TTL, default clock, or new service is introduced.
## BMAD Party Mode Review

- Initial review: product/PM `9.45` (no veto), architecture `9.35` (no veto), academic/QA `9.35` (no veto). All reviewers identified precision corrections, so the story was revised before approval.
- Applied corrections: replaced the pre-start `RunManifest.v1` draft with a non-published scope/binding projection; permitted only injected read-only prerequisite resolution before run-created effects; bound opaque authorization identities and claim-safe execution modality in the public closure; separated blind public closure from restricted condition evidence and its downstream ineligibility; made every applied mock value/behavior resolve to the accountable admissible evidence closure; and prohibited recovery re-command/replay absent an exact frozen policy.
- Final review: product/PM retains `9.45` with its two required corrections applied (the reviewer became unavailable before a redundant rescore); architecture `9.80` (no veto); academic/QA `9.70` (no veto). Aggregate `9.65`; no reviewer veto remains.
- Decision: auto-approved for `ready-for-dev` because the aggregate is at least `9.0` and no veto remains.
- Boundary: Party Mode approves this planning artifact only. It grants no implementation, activation, experiment, physical acquisition, command, persistence, truth, publication or dashboard authorization.

### References

- [Source: _bmad-output/planning-artifacts/epics.md#Story 10.6: Run and Persist Controlled Physical Evidence]
- [Source: _bmad-output/planning-artifacts/prd.md#FR85]
- [Source: _bmad-output/planning-artifacts/prd.md#NFR39-NFR41]
- [Source: _bmad-output/planning-artifacts/prd.md#NFR45-NFR46]
- [Source: _bmad-output/planning-artifacts/prd.md#NFR49-NFR51]
- [Source: _bmad-output/planning-artifacts/architecture.md#Trust and authority boundaries]
- [Source: _bmad-output/planning-artifacts/architecture.md#Authoritative evidence contracts]
- [Source: _bmad-output/planning-artifacts/architecture.md#Bounded physical signal emulator admission]
- [Source: _bmad-output/planning-artifacts/architecture.md#Verification gates and failure semantics]
- [Source: _bmad-output/implementation-artifacts/9-6-define-immutable-artifact-and-evaluation-manifests.md]
- [Source: _bmad-output/implementation-artifacts/9-7-qualify-minimal-persistent-evidence-storage.md]
- [Source: _bmad-output/implementation-artifacts/9-8-define-partition-freeze-and-activity-authorization-records.md]
- [Source: _bmad-output/implementation-artifacts/10-1-define-evidence-backed-instrument-profiles.md]
- [Source: _bmad-output/implementation-artifacts/10-2-define-and-validate-signalobservation-v2.md]
- [Source: _bmad-output/implementation-artifacts/10-3-separate-process-physics-from-transmitter-and-edge-evidence.md]
- [Source: _bmad-output/implementation-artifacts/10-4-define-experimentspec-v1-and-the-preregistered-matrix.md]
- [Source: _bmad-output/implementation-artifacts/10-5-isolate-scenariotruth-v1-and-control-truth-unlock.md]

## Mandatory Academic Evidence Amendment

Before implementation, apply the relevant mandatory controls in [Academic Evidence Admission Amendment — 2026-08-31](../planning-artifacts/academic-evidence-admission-amendment-2026-08-31.md). This story must fail closed on an unresolved evidence origin, numeric authority, required mock closure, or prohibited dataset substitution. The amendment adds no activity authorization.
## Dev Agent Record

### Agent Model Used

### Debug Log References

### Completion Notes List

### File List
