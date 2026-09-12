# Story 10.7: Qualify and Publish Physical Experiment Evidence

Status: ready-for-dev

<!-- Planning READY does not authorize implementation, qualification execution, evidence acquisition, feature activation, training, consensus, syscall capture, truth unlock/join, fusion, deployment, publication, dashboard work or any scientific claim. Each later activity requires its own exact authorization and fail-closed gate. -->

## Story

As a research owner,
I want completed physical runs checked against the signal-v2 evidence gate,
so that only coherent and reconstructible physical evidence advances to later analysis.

## Acceptance Criteria

1. **Given** a completed or terminated immutable Story 10.6 run closure and an exact separately resolved Story 9.8 partition/freeze-membership closure with its declared boundary/gap policy **When** qualification begins **Then** a pure injected resolver reconstructs its public blind evidence from the exact `RunManifest.v1`, receipt, `ExperimentSpec.v1`, matrix, profile, parameter/mock/source, code/runtime/input, observation, trace and qualified-storage identities **And** an absent, stale, mutable, mismatched, incomplete, wrong-audience or unverified dependency produces an explicit non-published `blocked`, `incomplete` or `not_qualified` disposition with no repair, fallback, rewrite or command. A Story 10.6 partial/orphan closure with no final manifest/receipt is retained/referenced only through its already visible objects and returns such a non-published disposition; it creates no durable incomplete record.

2. **Given** reconstructed `SignalObservation.v2` canonical bytes **When** G2 signal invariants are checked **Then** raw current, profile endpoints/conversion direction, normalized span, engineering derivation/unit, pre-clipping quality/diagnostics, experiment/run/round/edge/sensor/event/sequence/correlation identity, source/observed timestamps, clock quality, parameter/source/profile identities and trace provenance remain mutually consistent end to end **And** under-range, over-range, fault, missing and invalid evidence remains visible without clipping, imputation, normalization, replacement or aggregate substitution.

3. **Given** the same frozen eligible inputs and a separately existing canonical feature-projection contract **When** their eligible batch and live projections are compared **Then** every feature identity, input closure and output canonical bytes is reconstructible and all discrepancies are reported **And** agreement is accepted only within an exact applicable immutable Story 9.4 evidence/preregistered tolerance; missing or inapplicable tolerance blocks the comparison rather than selecting a value or the better path. This story neither invents a feature schema nor trains, calibrates, thresholds or scores a detector.

4. **Given** the exact specification declares expected streams, boundaries and a partition-policy reference, and the separately resolved Story 9.8 frozen partition-membership/boundary/gap-policy closure is compatible **When** completeness and leakage validation runs **Then** missing, duplicate, late, out-of-order, invalid, partial, corrupted or mixed records carry affected opaque identities and per-record disposition resolved only from the exact frozen `ExperimentSpec.v1`/requirement-profile/parameter-policy identity **And** every derived window stays within one complete run, declared scenario boundary, schema, gap policy and frozen partition. An absent/incompatible policy or closure is `blocked`/`incomplete`, never inferred; no window, preprocessing input or report crosses a run, scenario, trace, schema, gap or partition boundary.

5. **Given** detector-facing physical evidence and restricted condition/truth evidence **When** adopted v2 public-boundary isolation is checked **Then** direct truth/label/scenario/future-interval/expected-outcome fields and declared transitive restricted or unregistered semantic/provenance/audience edges are rejected before qualification publication **And** public artifacts retain opaque correlation only. The public qualifier maps only public metadata and opaque restricted references permitted by the immutable Story 10.5/9.8 closure; it never resolves or reads restricted bytes, locators, counts or timings. This does not claim to detect arbitrary undeclared external covert channels; truth unlock, join and evaluation remain evaluator-only later activities.

6. **Given** qualification checks finish for any valid, invalid, aborted, failed, recovered, unfavorable, blocked or incomplete run **When** a formal result is authorized and recorded **Then** Story 10.7 owns one narrow flat canonical public `PhysicalEvidenceQualificationResult.v1` subject contract, manifested only through Story 9.6/9.7 machinery; it immutably retains actual run status, exact policy/partition-frozen closure, check dispositions, affected opaque identities, bounded public diagnostics and limitations without suppressing a negative outcome **And** only an actual `complete` run with every applicable frozen check passing receives `PHYSICAL_EVIDENCE_QUALIFIED` and an explicit G2-pass disposition. `qualified` is non-authorizing and is neither ScenarioTruth, completed-outcome evidence, `DATASET_QUALIFIED`, G8/G9 nor a scientific-publication claim. The public result binds only the examined immutable public closure and claim-safe modality, never a restricted parent; it does not rewrite Story 10.6 evidence or assert a real plant/hardware/digital twin.

7. **Given** a complete public closure has a qualifying `PhysicalEvidenceQualificationResult.v1` candidate and a separately approved exact Story 9.8 `scientific_publication` authorization/profile scoped to that immutable closure and expected public result role **When** it is published **Then** it reuses Story 9.6's typed manifest and object-first/read-back/full-closure/receipt-last protocol through Story 9.7's exact qualified repository port **And** every required result object, manifest and receipt is verified immutably, while write/read/closure faults leave visible incomplete artifacts with no qualified status. No authorization from Story 10.6, or `evaluation`/truth authorization, substitutes; without the exact publication authorization, checking returns only a non-published disposition. No generic qualification framework, repository, bucket/prefix, mutable alias, database or service is created.

8. **Given** all G2 conditions pass **When** the gate is reported **Then** the claim is limited to controlled custom physical evidence and the declared execution modality **And** it neither closes `DATASET_QUALIFIED`, certifies synchronized paired streams, authorizes training, consensus activation, physical acquisition, syscall capture, truth unlock/join, fusion, deployment, scientific publication or dashboard work.

9. **Given** Story 10.7 code and documentation are tested **When** default tests/imports run **Then** they use only fixed conspicuous non-domain canonical fixtures and injected strict resolvers/projectors/repository doubles **And** never start hardware, broker, Docker/MinIO, network, dashboard, system clock/random/environment defaults, legacy runtime, source/dataset acquisition, control, capture, detector, truth unlock/join or formal qualification publication.

## Amendment Acceptance Criteria

**Given** custom physical evidence, its specification, persistence request, or qualification input
**When** it is admitted to a formal path
**Then** its closed origin, prototype generation binding, per-field mock influence, exact parameter authority, immutable trace, and current `DirectReproductionAssessment.v1` are resolved where applicable
**And** missing/mismatched generator, source-use, parameter, assessment, origin, or trace blocks formal evidence without creating a fallback or changing experiment control.

- [ ] Add focused non-domain `unittest` cases for valid reconstruction and every missing/mismatched closure element, including an authentically reproducible behavior that invalidates a prior mock admission.
## Tasks / Subtasks

- [ ] Task 1: Reconstruct immutable input closure without changing it (AC: 1, 6-9)
  - [ ] Add only `src/parallel_truth_fingerprint/evidence/physical_evidence_qualification.py` after all intended upstream public exports exist. Inject strict immutable resolvers and canonical validators; add no scheduler, command/control, store, database, service, broker, UI or authorization issuer.
  - [ ] Require the completed public blind-evidence closure from Story 10.6 plus exact receipt/manifest/spec/matrix/profile/parameter/mock/source/code/runtime/input/trace identities, Story 9.7 qualified repository identity and separately resolved Story 9.8 partition/freeze membership/boundary/gap closure. Re-read exact bytes/hash/size and reject `latest`, aliases, partial closure, unknown fields, implicit defaults and any `unavailable_blocking` slot. A missing final closure remains a non-published incomplete/not-qualified disposition and creates no durable record.
  - [ ] Define only the flat canonical public `PhysicalEvidenceQualificationResult.v1` subject contract, with opaque references/bounded public diagnostics and no restricted parent, then manifest it through existing Story 9.6/9.7 machinery. It is not a generic framework, lifecycle record, receipt or authorization.

- [ ] Task 2: Validate G2 signal and reconstruction invariants (AC: 2, 4, 6, 9)
  - [ ] Reuse Story 10.1 profile, Story 10.2 canonical observation, Story 10.3 producer and Story 10.4 spec validators. Independently recompute/compare only their declared exact representations and identities; no conversion, endpoint, time, quality or source default may be inferred here.
  - [ ] Preserve each under/over-range, fault, missing, invalid, duplicate, late, out-of-order, partial, corrupted and mixed record as a visible check result. Never clip, impute, merge, reorder away, select an edge, synthesize a record or reinterpret a collection defect as normal.
  - [ ] Enforce declared expected-stream/run/schema closure plus separately resolved frozen partition/boundary/gap-policy membership before any window/projection input. Resolve every defect’s eligibility from exact frozen spec/requirement-profile/parameter policy; absent/inapplicable policy blocks. This story does not create a freeze, choose a split, feature schema or downstream detector protocol.

- [ ] Task 3: Compare canonical batch/live projections without detector work (AC: 3, 4, 6, 9)
  - [ ] Consume a future existing canonical projection interface only after its schema, frozen inputs and batch/live eligibility are supplied. Bind exact input/output identities and report every mismatch, including unavailable path, different canonical bytes/feature order, boundary breach and tolerance failure.
  - [ ] Require the comparison tolerance to resolve to one applicable immutable Story 9.4 evidence/preregistered record. Do not create any numerical tolerance, feature assumption, preprocessing, fitting, calibration, threshold, score, selected path or performance claim.

- [ ] Task 4: Prove public truth isolation and publish only the qualification result (AC: 5-9)
  - [ ] Reuse the Story 10.5/9.8 immutable semantic-role/provenance/audience-map closure on each adopted public boundary. Reject direct or declared transitive truth leaks; correlate with opaque public IDs only. Map no restricted bytes/locators/counts/timings, do not read truth values, create an unlock/join, evaluate metrics or claim arbitrary covert-channel detection.
  - [ ] Add `src/parallel_truth_fingerprint/evidence/physical_evidence_publication.py` only if a narrow adapter is needed to invoke existing Story 9.6/9.7 publication ports. Require exact independently approved `scientific_publication` authorization before a formal result object/write; write result objects first, exact read back, assemble/reverify closure and issue the existing receipt last. Fault or absent authorization leaves no qualified/G2-pass publication.
  - [ ] Bind `PHYSICAL_EVIDENCE_QUALIFIED` and G2 only to an actual complete run with fully passing frozen checks and claim-safe execution modality. Keep accelerated/physical-only evidence non-fusion-eligible; do not close G8/`DATASET_QUALIFIED` or claim a scientific publication.

- [ ] Task 5: Document and test the qualification boundary (AC: 1-9)
  - [ ] Add `docs/physical-evidence-qualification-v2.md` explaining reconstruction inputs, G2 checks, status table, public/restricted boundary, parity/tolerance gate, publication ordering, current blockers, controlled-emulator limitations and downstream exclusions.
  - [ ] Add `tests/evidence/test_physical_evidence_qualification.py`, optional `tests/evidence/test_physical_feature_parity.py`, and an offline closure-fault test only if the established layout supports it. Use injected fixed non-domain fixtures/fakes; default discovery has zero live side effects.
  - [ ] Test each absent/mismatched identity/receipt/hash; profile/current/normalized/engineering/unit/quality/time/sequence/correlation violation; each defect/disposition and window boundary; every batch/live mismatch and missing/inapplicable tolerance; direct/transitive truth leakage; required restricted evidence absence preserving blind evidence but denying later eligibility; publication faults; full actual-status retention; and G2/downstream/UI/legacy import guards.

## Dev Notes

### Ownership and required order

- Story 10.6 owns execution, collection, restricted/public persistence and run outcome. Story 10.7 is read-only reconstruction, qualification and immutable qualification-result publication; it never commands, recovers, replays, writes a run observation or repairs evidence.
- Required order: validated upstream contracts/gates -> separately authorized Story 10.6 run with completed blind closure -> Story 10.7 read-only reconstruction -> G2/completeness/isolation/parity checks -> immutable qualification result publication. The later evaluator-only truth-unlock/join sequence remains Story 9.8; this is not a workflow engine.
- G2 is not G8/G9. It does not prove a real plant, synchronized physical/syscall campaign, `DATASET_QUALIFIED`, detector readiness or final paired comparison.

### Current hard blockers and academic limits

- All v2 contracts, repository qualification, profiles, evidence runs and authorizations remain planning-only. Current blockers include missing P200 official bytes/hash, unresolved FB420 endpoints/configuration, incomplete TH320 and Danfoss Terminal 53 evidence, and emulator admission only `approved_planning_conditional`. Implementation must report those blockers, never replace them with fixtures or legacy demo data.
- No domain number, tolerance, feature behavior, quality policy, mock value or claim is created here. Every applied mock needs valid/approved/unavailable-with-evidence admission, accountable parameter gate, exact applicable official locators and direct paired-custom-comparison linkage. Convenience/cost/timing/unfavorable results never justify a mock; emulator evidence cannot claim a real plant, hardware, digital twin, safety, energy, efficiency or control performance.
- UI/UX is optional and out of scope.

### Legacy quarantine and project structure

- Never import or adapt `scripts/run_local_demo.py`, `scenario_control/runtime.py`, `config/runtime.py`, `sensor_simulation`, legacy acquisition/MQTT/local state, persistence, dashboard, consensus/SCADA or training. They carry mutable labels/defaults, transformations or side effects and are not v2 evidence.
- Expected narrow files: `evidence/physical_evidence_qualification.py`, optional `evidence/physical_evidence_publication.py`, documentation and focused standard-library `unittest` tests. No dependency addition is expected.

## BMAD Party Mode Review

- Initial review: product/PM `9.55` (no veto), architecture `8.50` (no veto), academic/QA `9.55` (no veto). The architecture score was below the automatic threshold, so the story was revised rather than approved.
- Applied corrections: made partial/orphan Story 10.6 evidence a non-published incomplete/not-qualified disposition; resolved the Story 9.8 partition/freeze/boundary/gap closure read-only instead of treating it as `ExperimentSpec.v1` state; added per-record frozen acceptance-policy binding; defined the narrow public `PhysicalEvidenceQualificationResult.v1`; forbade resolution of restricted content; required a distinct exact `scientific_publication` authorization for durable publication; and narrowed `qualified`/G2 to a complete run with every frozen check passing.
- Final review: product/PM `9.75` (no veto), architecture `9.75` (no veto), academic/QA `9.85` (no veto); aggregate `9.78`.
- Decision: auto-approved for `ready-for-dev` because the aggregate is at least `9.0` and no reviewer veto remains.
- Boundary: Party Mode approves this planning artifact only. It grants no qualification execution, evidence acquisition, feature activation, training, consensus, capture, truth, fusion, deployment, publication or dashboard authorization.

### References

- [Source: _bmad-output/planning-artifacts/epics.md#Story 10.7: Qualify and Publish Physical Experiment Evidence]
- [Source: _bmad-output/planning-artifacts/prd.md#FR73-FR76]
- [Source: _bmad-output/planning-artifacts/prd.md#FR85-FR86]
- [Source: _bmad-output/planning-artifacts/prd.md#NFR40-NFR42]
- [Source: _bmad-output/planning-artifacts/architecture.md#Authoritative evidence contracts]
- [Source: _bmad-output/planning-artifacts/architecture.md#Verification gates and failure semantics]
- [Source: _bmad-output/implementation-artifacts/9-6-define-immutable-artifact-and-evaluation-manifests.md]
- [Source: _bmad-output/implementation-artifacts/9-7-qualify-minimal-persistent-evidence-storage.md]
- [Source: _bmad-output/implementation-artifacts/9-8-define-partition-freeze-and-activity-authorization-records.md]
- [Source: _bmad-output/implementation-artifacts/10-1-define-evidence-backed-instrument-profiles.md]
- [Source: _bmad-output/implementation-artifacts/10-2-define-and-validate-signalobservation-v2.md]
- [Source: _bmad-output/implementation-artifacts/10-3-separate-process-physics-from-transmitter-and-edge-evidence.md]
- [Source: _bmad-output/implementation-artifacts/10-4-define-experimentspec-v1-and-the-preregistered-matrix.md]
- [Source: _bmad-output/implementation-artifacts/10-5-isolate-scenariotruth-v1-and-control-truth-unlock.md]
- [Source: _bmad-output/implementation-artifacts/10-6-run-and-persist-controlled-physical-evidence.md]

## Mandatory Academic Evidence Amendment

Before implementation, apply the relevant mandatory controls in [Academic Evidence Admission Amendment — 2026-08-31](../planning-artifacts/academic-evidence-admission-amendment-2026-08-31.md). This story must fail closed on an unresolved evidence origin, numeric authority, required mock closure, or prohibited dataset substitution. The amendment adds no activity authorization.
## Dev Agent Record

### Agent Model Used

### Debug Log References

### Completion Notes List

### File List
