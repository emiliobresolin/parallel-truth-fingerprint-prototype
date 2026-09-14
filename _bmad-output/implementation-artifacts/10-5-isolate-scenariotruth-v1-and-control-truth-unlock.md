# Story 10.5: Isolate `ScenarioTruth.v1` and Control Truth Unlock

Status: done

<!-- Note: Planning READY does not authorize implementation, source acquisition, feature activation, experiment execution, command emission, truth production/unlock/join, persistence, capture, training, evaluation, publication, dashboard work, or access to restricted data. -->

## Story

As an evaluator,
I want scenario truth stored separately and unlocked only after evidence is frozen,
so that physical evidence can be produced and scored without label leakage.

## Acceptance Criteria

1. **Given** only the applicable implemented public contracts for canonical identity/bytes, semantic and audience roles, source/parameter/mock gates, immutable manifests and qualified repository namespace registry, scientific freeze, `TruthUnlockRecord.v1`, `TruthJoinRecord.v1`, activity authorization, `ExperimentSpec.v1`, matrix, and `SignalObservation.v2` **When** Story 10.5 is implemented **Then** it adds one flat immutable `ScenarioTruth.v1` contract plus pure restricted-truth validation/access-decision helpers, documentation and focused offline tests **And** it adds no new manifest, authorization, join, evaluation, identity/IAM, scheduler, controller, storage adapter, database, service, CLI, MQTT route, detector, feature pipeline, dataset, dashboard or UI. Missing or incompatible prerequisites block implementation rather than receiving local copies.

2. **Given** a declared scenario-truth candidate bound to one frozen experiment/matrix declaration **When** `ScenarioTruth.v1` is canonically built and validated **Then** it contains schema/version/content identity, exact experiment and predeclared run bindings, opaque event and correlation identities, restricted condition/intervention interval references, declared-truth provenance, restricted writer identity, semantic/audience/namespace binding, caller-supplied canonical time facts and immutable parent references **And** it is append-only: any content or identity-bearing change yields a new record identity, never mutation. The record distinguishes declared restricted scenario truth from later achieved execution evidence; it makes no real-plant, authentic-hardware, successful-run, anomaly, safety, detector, metric or final-comparison claim.

3. **Given** an interval, condition, intervention, expected outcome, scenario name, label, truth locator or other restricted datum **When** it is placed in a detector-facing v2 observation, public serializer or declared transitive dependency that adopts the shared predicate **Then** strict forbidden-field and restricted-semantic-role/provenance validation rejects a direct truth field or any value, reference or identity that is absent from the immutable injected role/provenance map, restricted, mutable or incompatible with the public audience before serialization, publication or graph use **And** no declared label-derived projection, filename/tag/path, alias or dependency may enter as an indirect detector input. This story adds no MQTT, consensus, OPC, feature, bundle, score or report route; its generic tests operate only on injected mappings/contract fixtures and do not retrofit or normalize legacy v1 records. The closure does not prove absence of an undeclared external covert channel; every owner of a new public boundary must supply and conform to the same provenance/role map.

4. **Given** producers and detector-facing consumers need to correlate one run without truth access **When** they exchange public records **Then** they use only opaque experiment/run/event/correlation identities already bound by the applicable contracts, with no scenario or expected-result semantics exposed **And** syntax/namespace validation does not claim that an identifier is semantically safe. Scenario truth may be resolved only through the restricted evaluator audience and exact immutable references; public validators emit bounded audience-safe diagnostics with opaque references/rule IDs only.

5. **Given** truth is locked and a caller presents an already Story-9.8-validated unlock/join/action/closure result **When** the pure ScenarioTruth compatibility helper evaluates only its restricted truth reference and immutable parent identities **Then** an absent, premature, malformed, rejected or scope-mismatched upstream result is not compatible while detector-facing artifacts remain usable without truth **And** it returns only a bounded redacted non-published structured compatibility result with caller-supplied canonical time fact and no truth value, scenario name, interval, locator, support count or timing disclosure. A compatible result reveals no truth and neither executes nor grants unlock/join; identity/audience/action acceptance remains Story 9.8, and this result has no independent canonical identity, record, receipt or publication semantics. Durable attempt recording, if later authorized, belongs only to the qualified Story 9.6/9.7 path; this result is not IAM authentication, a stored ACL, credential, general capability, permission grant or actual I/O.

6. **Given** an evaluator-only truth unlock is proposed **When** `ScenarioTruth` compatibility is checked with the existing Story 9.8 `TruthUnlockRecord.v1` and `ActivityAuthorization.v1` **Then** Story 9.8 alone validates the exact evaluator audience, `truth_unlock` action, prior immutable `pretruth_evaluation` freeze, complete score/detector-decision closure and receipts, evaluator/protocol, caller-supplied canonical timestamp and approved exact authorization; Story 10.5 verifies only that the already validated opaque truth reference and its immutable parent identities are compatible with that closure **And** it reuses rather than defines, issues, persists, authenticates or executes a second unlock mechanism, discloses truth rows, performs a join or evaluates metrics. Every result has `authorization_effect: none`.

7. **Given** truth has been unlocked for one exact evaluator join **When** a later `TruthJoinRecord.v1`, evaluation candidate or post-unlock artifact is checked against this truth record **Then** Story 9.8 must validate the granted exact unlock and separately approved evaluator-only `restricted_truth_join` authorization; Story 10.5 verifies only unchanged truth-reference compatibility with that immutable closure, while the later evaluation still requires its own distinct Story 9.8 `evaluation` authorization **And** changed truth, score, decision, support, profile, parameter, code, runtime, matrix, evaluator or protocol identity invalidates the old lineage and fails closed without rewriting prior truth, blind evidence, unlock or join. Story 10.5 produces no join, row-level truth copy, evaluation record, metric, artifact write or dashboard override.

8. **Given** the Story 10.5 suite and documentation run offline **When** inspected **Then** they cover canonical bytes/content identities, append-only replacement, restricted namespace/audience closure, opaque correlation, forbidden direct/transitive leakage, absence of truth-independent detector impact, locked compatibility denial/redacted non-published result, evaluator-only unlock compatibility, post-unlock invalidation, truth/join separation, v1 quarantine and control/UI isolation using conspicuous non-domain fixtures **And** no test/import uses network, source or dataset acquisition, broker, device, system clock/random/environment default, Docker/MinIO, persistence, runtime demo, command, capture, detector, training, evaluation, dashboard or a formal project truth artifact. Every Story 10.5-owned success/failure result retains `authorization_effect: none`.

## Tasks / Subtasks

- [ ] Task 1: Enforce narrow upstream reuse and legacy truth quarantine (AC: 1, 3-8)
  - [ ] Require only applicable public exports/tests from Stories 9.1-9.8 and 10.1-10.4: canonicalization, audience/semantic graph, source/parameter gates, manifest/namespace port, freeze, upstream unlock/join/authorization gates, profile/observation and experiment/matrix contracts. Stop if an export is absent/incompatible; create no substitute `TruthUnlockRecord`, `TruthJoinRecord`, authorization type, registry or storage path.
  - [ ] Preserve `scenario_control/runtime.py`, `config/runtime.py`, `scripts/run_local_demo.py`, dashboard control surface, legacy acquisition/MQTT, persistence, consensus, SCADA, sensor simulation and training/inference unchanged. Their scenario/training labels, mutable configuration, filenames and state are v1-only and are forbidden v2 truth inputs.
  - [ ] Treat all project-domain truth production as blocked at story creation because upstream v2 APIs, formal experiment eligibility, profile/mock gates and qualified restricted persistence do not yet exist. Fixtures use only `fixture_test`/`fixture_expected`/`test_only` roles; formal resolvers reject them.

- [ ] Task 2: Add only the restricted ScenarioTruth contract and pure validation (AC: 1-4, 8)
  - [ ] Add `src/parallel_truth_fingerprint/contracts/scenario_truth.py` with frozen tuple-backed values, closed enum tokens, strict parser/`to_dict()` hooks, canonical bytes/content ID and no implicit IDs/time/defaults. Re-export only intended v2 types from `contracts/__init__.py` after upstream contracts exist; until then tests import exact modules rather than the eager legacy package root.
  - [ ] Model restricted intervals as opaque immutable interval/trace references plus caller-supplied canonical time facts and declared provenance, not unbacked duration/cadence numbers, execution outcomes or public labels. Bind exact parent experiment/matrix/run/trace identities and explicit restricted audience/namespace identity.
  - [ ] Add a pure validator in `src/parallel_truth_fingerprint/evidence/scenario_truth_validation.py` only if the upstream `evidence` package/exports exist; otherwise stop. It accepts injected immutable resolvers, validates reference/audience/semantic closure and never reads a filesystem, environment, clock, transport, service or runtime configuration.
  - [ ] Keep append-only semantics at contract level: replacement creates a fresh canonical identity. Story 10.6 later owns an authorized durable restricted write through Story 9.6/9.7; no local prefix, bucket, directory or database table is invented here.

- [ ] Task 3: Make truth leakage impossible at public boundaries (AC: 3-4, 8)
  - [ ] Define one closed generic forbidden-truth field plus immutable injected semantic-role/provenance-map check for v2 contract serializers and injected public mapping fixtures. Reject direct truth keys and every value/reference/identity that is absent, restricted, mutable or audience-incompatible in the map, including declared transitive parent/diagnostic references, before a public graph/serialization result exists.
  - [ ] Specify the predicate for any later `SignalObservation.v2` or public MQTT/consensus/OPC/feature/detector/bundle/score/report v2 projection without adding or editing those routes in this story. Opaque public IDs are references only; grammar cannot prove semantic safety. Undeclared covert encodings are prohibited design inputs, and every future public-boundary owner must provide map closure rather than claiming this story can detect arbitrary external semantics.
  - [ ] Do not import, modify or sanitize legacy `RawHartPayload`, `RuntimeScenarioControlStage`, `dataset_context`, consensus state, SCADA state or dashboard state. A test failure identifies a new v2 boundary defect; it does not relabel old demo records as formal evidence.

- [ ] Task 4: Reuse exact unlock/join ordering without creating access control (AC: 5-7)
  - [ ] Add one pure restricted-truth compatibility helper that returns `compatible`/`not_compatible` plus bounded redacted diagnostics and caller-provided canonical time. Its non-published result has no independent ID/record/receipt/publication semantics; it performs no I/O, does not authenticate users, store attempts, grant a token/permission, expose truth or claim that namespace/audience tokens enforce security.
  - [ ] Delegate all unlock record/action/profile/closure validation to Story 9.8, including exact evaluator-only `truth_unlock` authorization, `pretruth_evaluation` freeze and blind score/decision closure. Story 10.5 checks only compatibility of the opaque ScenarioTruth reference and immutable parents. Keep truth locked if that compatibility fails.
  - [ ] For a later join/evaluation candidate, check only unchanged ScenarioTruth-reference compatibility with an already Story-9.8-validated `TruthJoinRecord.v1` and separate `restricted_truth_join` authorization. A mismatch returns deterministic invalidation facts; Story 10.5 never executes a join/evaluation, creates a replacement authorization or substitutes for the later distinct `evaluation` authorization.
  - [ ] Prove no result imports or calls command/control, experiment execution, MQTT, persistence, dashboard or detector paths. A dashboard/report cannot read restricted content or override a deny/invalidation result.

- [ ] Task 5: Document and test the restricted planning contract (AC: 1-8)
  - [ ] Add `docs/scenario-truth-v1.md` with ownership flow, restricted/public field table, audience and opaque-ID rules, append-only/namespace limitation, access-decision order, reuse of Story 9.8 unlock/join records, invalidation, legacy quarantine and downstream ownership.
  - [ ] Add `tests/contracts/test_scenario_truth.py` and optional `tests/evidence/test_scenario_truth_validation.py`. Use exact canonical non-domain sentinels and injected resolvers/mappings; do not create a real project truth record, namespace write or evaluator action.
  - [ ] Test strict unknown/duplicate/alias keys, canonical byte/hash oracle, parent/audience/namespace mismatch, inferred timestamp/ID rejection, append-only new identity, opaque-ID nonsemantic handling, absent/restricted/mutable/audience-incompatible provenance roles and declared transitive leaks, blind detector usability, non-published compatibility-result redaction/no-ID/no-permission, Story-9.8 evaluator/action/freeze/authorization/closure delegation, post-unlock invalidation, no row-level join, no authorization effect, legacy import guards and dashboard/control isolation.
  - [ ] Run focused prerequisite suites, Story 10.5 tests and full Python `unittest` discovery. If upstream contracts remain planning-only, report a prerequisite blocker rather than adding placeholder types, synthetic truth, local storage or a runtime proof.

## Dev Notes

### Scope and ownership

- This story defines restricted truth representation and pure compatibility gates. It does not produce actual conditions, run evidence, labels, truth writes, unlocks, joins, metrics or scientific results.
- The one-way order is: Story 10.4 opaque declared references -> later Story 10.6 authorized execution/immutable blind evidence -> Story 9.8 `pretruth_evaluation` freeze -> exact evaluator-only `truth_unlock` authorization and upstream `TruthUnlockRecord.v1` -> exact evaluator-only `restricted_truth_join` authorization and upstream `TruthJoinRecord.v1` -> later independently authorized evaluation. This is immutable validation order, not a workflow engine.
- UI/UX is optional and out of scope. The existing dashboard is a legacy mutable demo/control surface, not a restricted evaluator interface and not a truth/unlock dependency.

### Restricted versus public evidence

```text
ExperimentSpec/matrix: opaque scenario + truth-unlock-policy references only
  -> ScenarioTruth.v1: restricted audience, immutable interval/provenance references
  -> blind observations / scores / decisions: no truth fields or transitive truth edges
  -> pretruth evaluation freeze (Story 9.8)
  -> evaluator-only unlock + join authorizations/records (Story 9.8)
  -> later separate evaluation artifact
```

- `ScenarioTruth.v1` represents declared restricted truth, not proof that an intervention occurred. Story 10.6 owns actual execution/outcome evidence; later evaluation determines how truth is used.
- Public opaque IDs may correlate records but never encode scenario semantics. Syntax alone cannot prove absence of semantic leakage; every public value/reference/identity therefore needs an immutable declared provenance/role and audience mapping. This closes adopted v2 boundaries but does not prove absence of undeclared external covert channels.
- The qualified repository namespace is a structural/audience boundary only. This prototype does not claim user authentication, IAM, encryption, ACLs, signatures, revocation, expiry, one-use capability or real access-control enforcement.

### Upstream reuse and current blockers

- Story 9.8 owns `ScientificFreeze.v1`, `TruthUnlockRecord.v1`, `TruthJoinRecord.v1`, `ActivityAuthorization.v1`, their evaluator-only action profiles and validation ordering. Reuse them; do not introduce a competing record or action token.
- Story 9.6 owns immutable artifact/evaluation manifests and Story 9.7 owns qualified persistence. A pure compatibility result is neither a durable write nor an access grant.
- All upstream v2 contracts are currently planning-only. The existing scenario runtime exposes semantic labels and mutable config; it must remain quarantined v1. A future implementation stops rather than adapting it.

### Academic, mock and numeric guardrails

- No mock, physical behavior, dataset value, scenario duration, interval numeric, cadence, tolerance, metric, threshold or performance outcome is introduced. Structural versions, hashes, caller-supplied canonical time facts and conspicuous fixtures are contract mechanics, not physical claims.
- If a future domain mock is required, it must prove authentic reproduction unavailable and bind a valid/approved/accountable Story 9.4 `MockAdmission.v1`, exact strongly applicable official sources, every value/assumption/limitation and direct final paired custom-comparison linkage. This story creates no exception.
- New methodological, cryptographic, privacy or access-control claims require new source research before they may be made. No such external claim is needed for this bounded contract.

### Current repository hazards

- `scenario_control/runtime.py` exposes `scenario_label`, `training_label`, fault/SCADA modes and mutable demo defaults; `config/runtime.py` reads environment values. Neither is a truth source or allowed import.
- `scripts/run_local_demo.py` carries scenario/training labels into `dataset_context`, persistence and runtime artifacts. It stays unchanged as legacy demo behavior and is prohibited from v2 truth/detector paths.
- Dashboard control, legacy MQTT, persistence, consensus, SCADA and LSTM services can start runtime, write state, infer or expose values. They must not be imported by ScenarioTruth code or tests.

### Downstream ownership

- Story 10.6 owns separately authorized execution, actual condition/outcome evidence and durable restricted truth/evidence writes.
- Story 10.7 owns physical qualification/G2 and publication boundaries.
- Story 9.8 owns unlock/join/evaluation authorization and records; Story 9.6 evaluation manifests consume the exact join identity.
- Epics 13-17 consume only blind records until their exact evaluator gates; Epic 18 remains optional read-only presentation after frozen evidence.

### Project structure notes

- Restricted contract: `src/parallel_truth_fingerprint/contracts/scenario_truth.py`.
- Pure validator/access decision: `src/parallel_truth_fingerprint/evidence/scenario_truth_validation.py` only after the upstream evidence package exists.
- Narrow public exports: `src/parallel_truth_fingerprint/contracts/__init__.py`.
- Human guide: `docs/scenario-truth-v1.md`.
- Focused tests: `tests/contracts/test_scenario_truth.py` and optional `tests/evidence/test_scenario_truth_validation.py`.
- No new dependency, bucket/prefix, raw truth file, database, service, scheduler, authorization provider, execution/control integration, dashboard/UI change or formal evidence artifact.

## BMAD Party Mode Review

- Initial review: product/PM `8.70` (no veto), architecture `9.25` (veto), academic/QA `8.80` (veto); aggregate `8.92`. The story was revised rather than approved.
- Applied corrections: changed impossible universal covert-channel detection into an immutable declared provenance/role/audience-map closure at each adopted v2 public boundary; stated its honest external-channel limitation; replaced a competing audit receipt/access result with a redacted non-published compatibility result; delegated all unlock/join/action/profile/closure validation to Story 9.8; retained Story 10.5 only for ScenarioTruth reference/parent compatibility; and made the separate later `evaluation` authorization explicit.
- Final review: product/PM `9.60` (no veto), architecture `9.75` (no veto), academic/QA `9.70` (no veto); aggregate `9.68`.
- Decision: auto-approved for `ready-for-dev` because the aggregate is at least `9.0` and no reviewer veto remains.
- Boundary: Party Mode approves only this planning artifact; every Story 10.5-owned result has `authorization_effect: none`.

### References

- [Source: _bmad-output/planning-artifacts/epics.md#Story 10.5: Isolate `ScenarioTruth.v1` and Control Truth Unlock]
- [Source: _bmad-output/planning-artifacts/prd.md#FR77]
- [Source: _bmad-output/planning-artifacts/prd.md#NFR40-NFR42]
- [Source: _bmad-output/planning-artifacts/prd.md#NFR48-NFR52]
- [Source: _bmad-output/planning-artifacts/architecture.md#Trust and authority boundaries]
- [Source: _bmad-output/planning-artifacts/architecture.md#Authoritative evidence contracts]
- [Source: _bmad-output/implementation-artifacts/9-2-establish-the-semantic-and-evidence-role-vocabulary.md]
- [Source: _bmad-output/implementation-artifacts/9-6-define-immutable-artifact-and-evaluation-manifests.md]
- [Source: _bmad-output/implementation-artifacts/9-7-qualify-minimal-persistent-evidence-storage.md]
- [Source: _bmad-output/implementation-artifacts/9-8-define-partition-freeze-and-activity-authorization-records.md]
- [Source: _bmad-output/implementation-artifacts/10-2-define-and-validate-signalobservation-v2.md]
- [Source: _bmad-output/implementation-artifacts/10-4-define-experimentspec-v1-and-the-preregistered-matrix.md]

## Mandatory Academic Evidence Amendment

Before implementation, apply the relevant mandatory controls in [Academic Evidence Admission Amendment — 2026-08-31](../planning-artifacts/academic-evidence-admission-amendment-2026-08-31.md). This story must fail closed on an unresolved evidence origin, numeric authority, required mock closure, or prohibited dataset substitution. The amendment adds no activity authorization.
## Dev Agent Record

### Agent Model Used

### Debug Log References

### Completion Notes List

### File List
