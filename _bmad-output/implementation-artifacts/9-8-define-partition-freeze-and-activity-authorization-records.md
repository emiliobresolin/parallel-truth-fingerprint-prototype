# Story 9.8: Define Partition, Freeze, and Activity-Authorization Records

Status: done

<!-- Note: Planning READY does not authorize implementation, acquisition, capture, training, calibration, scoring, truth unlock, evaluation, fusion, promotion, activation, deployment, publication, control, storage mutation, or dashboard work. -->

## Story

As a research owner,
I want small immutable records for data partitioning, scientific freezes, and authorized activities,
so that later experiments avoid leakage and remain within their explicitly approved scope.

## Acceptance Criteria

1. **Given** Stories 9.1-9.7 have supplied their intended public contracts, validators, source/parameter gates, golden fixtures, immutable-reference/publication machinery and qualified repository **When** Story 9.8 is implemented **Then** it adds only the minimum governance contract family: `PartitionRecord.v1` with `PartitionMembership.v1` entries, `ScientificFreeze.v1`, `TruthUnlockRecord.v1`, `TruthJoinRecord.v1`, and `ActivityAuthorization.v1`, plus pure validation/gate results; every top-level record binds an exact Story 9.2 audience and must satisfy the registered audience/role graph **And** it reuses the upstream canonical identity, `BindingSlot.v1`, semantic/audience vocabulary, immutable references, structured diagnostics, publication receipts and repository port instead of creating substitutes, mutable lifecycle records, a second manifest framework, a database, workflow engine, scheduler, IAM/authentication service or new runtime service; absent prerequisites block implementation rather than being copied locally.

2. **Given** a dataset, source collection or collection of experiment runs has a complete immutable source/group inventory **When** detector-facing structural `PartitionRecord.v1` is validated and published **Then** the record binds the exact source-universe manifest, dataset/track identity, independently frozen eligibility/exclusion-policy identity, code-pinned partition-requirement profile and grouping/boundary scheme, method/code/dependency identity, caller-supplied canonical timestamp, applicable Story 9.3 source-use revisions, exact opaque group identities and exactly one disposition for every source-inventory group: one applicable `train`, `validation`, `calibration` or `test` membership, or profile-permitted `excluded` with a closed audience-safe non-truth reason and immutable detector-safe evidence reference **And** missing, extra, duplicate, conflicting, cross-role, mutable-alias, native-role/profile-mismatch, post-hoc/outcome-based exclusion, caller-invented reason or truth-bearing identity/reason/reference fails closed; exact membership is authoritative, and a method name or random seed can never reconstruct or replace it.

3. **Given** the selected partition method uses randomness **When** its partition record is validated **Then** the exact seed, RNG/algorithm, code/dependency identity and applicable Story 9.4 parameter/decision revision are bound without a default **And** a deterministic or official/native method carries an independently approved explicit not-applicable seed binding; no split ratio, fold count, minimum group count, seed or other domain/algorithmic numeric value is introduced by this story, inferred from legacy behavior or accepted from an unregistered caller-defined requirement profile.

4. **Given** downstream code proposes preprocessing/vocabulary/model fitting, selection, threshold selection, calibration, blind scoring or a window, sequence or other derived sample **When** the pure partition-use and derived-membership gates evaluate its exact activity/stage, input roles, complete ordered parent membership and boundary lineage **Then** the independently registered role-access profile permits fitting inputs from `train` only, selection and threshold inputs only from its declared `validation` or `calibration` roles, calibration inputs only from its declared calibration role, blind scoring only from frozen `test` observations without truth, and evaluator truth only after exact unlock **And** every derived parent resolves to one already assigned opaque source group, one partition record and one role before derivation, the child crosses none of the profile-required group, run, trace, file, boot, session, process, scenario, gap, schema, source or split boundaries, and group/partition/boundary/authorization metadata remains lineage rather than feature, vocabulary, preprocessing-fit or model input; unauthorized roles, cross-role use, pre-partition derivation, multi-group children, missing lineage and unknown or caller-defined profiles fail closed without creating samples, loading a dataset or changing acquisition/control state.

5. **Given** a track is ready for fitting, model selection, calibration, threshold selection, blind test scoring, fusion or a pre-truth evaluation closure **When** its `ScientificFreeze.v1` is created **Then** it binds one exact stage token from `fitting`, `model_selection`, `calibration`, `threshold_selection`, `blind_scoring`, `fusion` or `pretruth_evaluation`, the exact audience permitted by an independently registered code-pinned stage-requirement profile, caller-supplied canonical timestamp, and the exact applicable partition, source/instrument profile, parameter gate/set, input and feature/vocabulary schemas, preprocessing, candidate/model/bundle configuration, calibration method, threshold policy, detector-decision schema, metric/evaluation protocol and fusion policy through Story 9.6 immutable references or `BindingSlot.v1` states **And** the profile, not the caller, determines which slots are required, not applicable or blocking at that stage, thereby avoiding circular requirements for outputs that do not yet exist; `pretruth_evaluation` is evaluator-only, is issued before any truth access, binds the completed immutable score/decision closures and evaluator/protocol inputs, and cannot bind truth-derived output or its own/future `EvaluationResult.v1`; any identity-bearing change creates a new freeze linked to its predecessor rather than mutating, aliasing or silently widening the old record.

6. **Given** a blind-scoring freeze already binds the exact model/bundle, partition, schema/vocabulary, preprocessing, threshold, detector-decision schema, metric protocol and applicable policy **When** test observations are scored **Then** fields or references classified by the registered Story 9.2 semantics and source inventory as truth-bearing, outcome-bearing, locator-bearing or restricted-audience remain unavailable to detector-facing processing, transitive detector graphs and diagnostics while exact score and detector-decision sets are published immutably **And** evaluator-only `TruthUnlockRecord.v1` can validate only after an exact `pretruth_evaluation` freeze binds the prior blind-scoring freeze, completed score/decision closures and evaluator/protocol inputs, and after a prior exact evaluator-only `truth_unlock` authorization, restricted-truth opaque reference, declared owner/decision and caller-supplied canonical timestamp all resolve; the pinned blind-scoring profile must prove one exact score disposition and one detector-decision disposition for every frozen eligible test-support unit, including explicit retained non-success outcomes, while missing, extra, duplicate or wrong-support entries and absent/mismatched completion receipts keep truth locked with audience-safe diagnostics.

7. **Given** truth has been unlocked for one exact evaluator join **When** evaluator-only `TruthJoinRecord.v1` is validated **Then** it binds the granted unlock, a separately approved exact evaluator-only `restricted_truth_join` activity authorization, the same partition/support/freeze/score/detector-decision closures, the exact opaque restricted-truth artifact and evaluator/join code/protocol, and records the structural join outcome without copying row-level truth into detector-facing evidence; the later evaluation activity and `EvaluationResult.v1` require a third, exact evaluator-only `evaluation` authorization **And** if any bound identity differs or any configuration changes after unlock, the old unlock cannot be reused and the mismatched new or reuse evaluation candidate fails with stable scope-mismatch/invalidation diagnostics; a previously published evaluation is never rewritten, and any later invalidation is a separate retained Story 9.6 envelope/observation while a new freeze/unlock/join/evaluation lineage is required.

8. **Given** a later activity requires explicit approval **When** `ActivityAuthorization.v1` and the pure activity gate are evaluated **Then** one record binds an exact audience, one exact action token, one independently registered code-pinned action-requirement profile, complete immutable input/prerequisite identities, expected output contract roles without inventing future output IDs, declared owner, `approved` or `rejected` decision, caller-supplied canonical timestamp, limitations and `authorization_effect`; its `planned_activity_id` is the canonical digest of action token, requirement-profile revision, applicable exact scope slots, immutable inputs/prerequisites and expected output contract roles, excluding authorization decision/time/self-ID and future output IDs, and the proposed activity must independently recompute the same digest **And** the profile, not the caller, marks each track, dataset, run, component, environment and final-output scope slot as `bound`, independently permitted `not_applicable` or blocking through `BindingSlot.v1`; the closed v1 action registry has no wildcard and contains exactly `implementation`, `source_acquisition`, `dataset_acquisition`, `physical_acquisition`, `syscall_capture`, `experiment_execution`, `model_training`, `model_selection`, `calibration`, `threshold_selection`, `blind_scoring`, `truth_unlock`, `restricted_truth_join`, `evaluation`, `fusion`, `promotion`, `feature_activation`, `deployment`, and `scientific_publication`, while action profiles make the three truth-related actions evaluator-only and no action can substitute for or implicitly grant another action.

9. **Given** an activity authorization is missing, rejected, malformed, uses a mutable alias, or mismatches the requested action, activity identity, scope, inputs, owner, required output roles or requirement-profile revision **When** the activity gate runs **Then** only that exact activity request is blocked with bounded deterministic diagnostics while unrelated acquisition/control and separately authorized activities remain available **And** an approved record is only recorded permission for that exact activity, not proof of owner authenticity, successful execution, scientific correctness, completion or permission to reuse it for another run; validation never mints approval, samples a clock/environment, calls a service, writes evidence or executes the requested activity.

10. **Given** the contracts and gates are tested and documented **When** the Story 9.8 suite runs **Then** canonical bytes, content IDs, strict parsing, ordering, profile ownership, complete partition closure, every declared boundary, stage applicability, truth isolation, publication closure, post-unlock mismatch, authorization locality and redaction are verified with conspicuous non-domain sentinel fixtures **And** no test/import/default CLI path uses a real dataset, creates a domain mock or measurement, invents a domain number, starts Docker/MinIO, downloads sources, captures signals/syscalls, fits a model, unlocks truth, evaluates, promotes, activates, controls equipment or touches a dashboard/UI; the planning artifact, non-authorization records and every validation/gate result have `authorization_effect: none` as a semantic boundary, whether represented by a common envelope field or result type, and only an exactly approved `ActivityAuthorization.v1` has a permission effect.

## Amendment Acceptance Criteria

**Given** a manifest, freeze, gate, or activity record admits a domain-bearing dependency
**When** its closure is validated
**Then** it records and verifies the closed evidence origin, exact numeric-authority revision/hash, and — where mock-parameterized — prototype generation binding, field-level mock influence, current `DirectReproductionAssessment.v1`, official source-use locator/hash, and immutable output trace
**And** any missing, defaulted, stale, substituted, or relabelled dependency fails closed with `authorization_effect: none`.

- [ ] Add pure `unittest` coverage proving that an incomplete origin/mock/numeric closure cannot enter a manifest, freeze, or gate result and cannot create authorization.
## Tasks / Subtasks

- [ ] Task 1: Enforce prerequisites, register source uses and freeze ownership (AC: 1-3, 5-10)
  - [ ] Treat Stories 9.1-9.7 as hard implementation prerequisites. Require their intended public identity/canonicalization, semantic/audience vocabulary, source catalog, parameter/mock gate, golden fixtures, immutable-reference/manifest/publication contracts and qualified repository with focused tests to exist and pass. Stop rather than create placeholder copies or adapt legacy mutable records into formal evidence.
  - [ ] Before making methodological claims, add exact Story 9.3 source-use revisions for the selected primary/official sources on named splits, group isolation, leakage avoidance, calibration/selection separation, pre-outcome freeze/blinding and provenance. Bind exact claim locators and limitations; these sources inform the project controls but do not dictate dataset grouping keys, partition ratios, algorithms or claim framework conformance.
  - [ ] Record the ownership table in `docs/scientific-governance-v1.md`: 9.6 owns general manifests, evaluation envelopes and publication closure; 9.7 owns qualified persistence; 9.8 owns only generic partition/freeze/unlock/activity contracts and gates; later dataset/track stories own source inventories, native roles, grouping keys, stage requirements, `ScenarioTruth` and scientific execution; Epic 18 presentation remains optional.
  - [ ] Introduce no domain mock, measurement, split ratio, seed, fold count, sample threshold, delay, expiry or duration. Any future result-affecting numeric partition/algorithm choice must resolve exactly through Story 9.4. Any future domain mock remains forbidden unless authentic reproduction is shown unavailable and a Story 9.4 `MockAdmission.v1` binds strongly applicable official documentation and a direct final dataset-comparison purpose.

- [ ] Task 2: Define the minimal flat immutable governance contracts (AC: 1-3, 5-10)
  - [ ] Add `src/parallel_truth_fingerprint/contracts/scientific_governance.py` with the five top-level v1 records and the subordinate `PartitionMembership.v1` shape. Use frozen standard-library value objects, strict versioned parsers, closed enums and intended exports in `contracts/__init__.py`; pure gate outcomes may be ordinary structured results and must not become another published evidence framework.
  - [ ] Reuse Story 9.6 immutable references, canonical bytes/content IDs, `BindingSlot.v1`, completion receipts and stable violations. Reject unknown/duplicate fields, implicit nulls, floats, local-time/naive timestamps, absolute or secret-bearing paths, mutable aliases, caller-provided hashes/IDs that do not recompute, Unicode/ordering ambiguities and truth-tainted detector-facing values.
  - [ ] Keep requirement profiles small, declarative, content-identified and code-owned in an independently registered registry. A candidate record cannot register the profile used to validate itself; unknown profile revisions and caller-local overrides fail closed. Later dataset stories register real partition profiles, later track stories register real freeze-stage profiles, and each later activity-owning story registers its action profile; Story 9.8 owns only schemas, registry mechanics and conspicuous sentinel profiles for tests. Profiles define allowed audiences, applicable roles, boundaries, eligibility/exclusion reasons, slots and input/output roles, not dataset-specific numeric policy.
  - [ ] Make authoritative records intrinsically immutable upon canonical publication. Draft validation is not a mutable `draft -> frozen -> approved` workflow, and a content change always produces a new identity.

- [ ] Task 3: Implement partition and derived-membership validation (AC: 2-4, 9-10)
  - [ ] Add pure offline validation under `src/parallel_truth_fingerprint/evidence/scientific_governance.py` using injected resolvers/registries. Validate the exact source-universe closure and give every opaque inventory group exactly one partition membership or independently permitted exclusion disposition, with no label/name/path/count/timing leakage through group identities, reason text or diagnostics.
  - [ ] Verify native/official roles only against the exact dataset-owned requirement profile and Story 9.3 source-use revision. Do not silently merge, relabel or randomly redistribute a native split; unsupported or unresolved semantics block only that partition candidate.
  - [ ] For randomized methods, verify the exact Story 9.4 seed/decision binding plus RNG/algorithm/code/dependency identity. For every method, treat recorded membership - not seed replay - as the scientific authority.
  - [ ] Implement a generic derived-membership gate that consumes, but does not invent, complete parent/boundary lineage. Reject pre-partition derivation and crossings of every boundary required by the pinned profile; create no windows, sequences, feature arrays or train/test loaders.
  - [ ] Implement the code-owned stage/action-to-role matrix from FR86. Reject train/validation/calibration/test cross-use and prove that structural lineage metadata is excluded from feature, vocabulary, preprocessing-fit and model input payloads while remaining available through separate immutable manifest edges.

- [ ] Task 4: Implement phase-aware freeze and restricted truth-unlock validation (AC: 5-7, 9-10)
  - [ ] Validate the exact freeze-stage registry in AC5 without requiring later-stage outputs at earlier stages. Later stages may bind a prior freeze, but no alias such as `current`, `best`, `champion` or `latest` is an identity. `pretruth_evaluation` must be created before truth access, bind completed score/decision closures plus evaluator/protocol inputs, and reject truth-derived or future/self-referential evaluation outputs.
  - [ ] Require the blind-scoring freeze to close every detector-facing decision before test truth can resolve: exact partition/support, bundle/model, schema/vocabulary, preprocessing/features, calibration, threshold, detector-decision schema, metric/evaluation protocol and applicable fusion policy.
  - [ ] Validate `TruthUnlockRecord.v1` only in the evaluation-only audience against profile-defined one-to-one closure of the exact frozen test-support universe and its published score/detector-decision dispositions and completion receipts, the prior exact `truth_unlock` authorization and the opaque restricted-truth artifact. Keep row-level truth, attack/scenario names, locators and revealing diagnostics out of detector-facing records and graphs; missing, extra, duplicate, wrong-support and omitted non-success outputs keep truth locked.
  - [ ] Validate `TruthJoinRecord.v1` as the exact evaluator-only join reference required by Story 9.6 `EvaluationResult.v1`. Require a granted matching unlock, a separate exact `restricted_truth_join` authorization and identical partition/support/freeze/score/decision/truth/evaluator identities; record only structural outcome and safe lineage, never truth rows. The later evaluation requires its own exact `evaluation` authorization.
  - [ ] Add a pure post-unlock consistency gate. Any changed identity returns deterministic mismatch/invalidation facts for the affected evaluation and requires a new immutable lineage; never rewrite the old freeze, unlock, join, scores, decisions or evaluation.

- [ ] Task 5: Implement local, exact-scope activity authorization (AC: 8-10)
  - [ ] Define the exact closed v1 action registry from AC8. Reject unknown tokens, wildcards, compound actions, broadened scopes, future-ID fabrication and reuse across activity instances. Require evaluator-only audiences for `truth_unlock`, `restricted_truth_join` and `evaluation`; detector-facing records or graphs cannot reference those authorizations or restricted truth directly or transitively.
  - [ ] Define and recompute `planned_activity_id` from only the pre-decision fields in AC8. Validate exact profile-applicable scope and complete prerequisite/input identities through the code-owned action profile. Later outputs reuse Story 9.6's existing producer-activity identity in their manifests, and the gate is supplied the exact authorization separately; do not require a new Story 9.6 manifest field or relation unless that upstream contract is explicitly revised first.
  - [ ] Return a pure allowed/blocked gate result with stable localized rule IDs. Missing, rejected or mismatched authorization blocks only the named activity and never changes global state, cancels another activity or interrupts unrelated acquisition/control.
  - [ ] Document the one-researcher prototype limitation honestly: the record preserves declared owner/decision/scope but does not authenticate a person, implement ACLs/signatures/revocation/expiry/one-use counters, monitor execution or prove compliance. Do not add a service or mutable `current authorization` index.

- [ ] Task 6: Add deterministic offline conformance and isolation tests (AC: 1-10)
  - [ ] Add focused standard-library `unittest` coverage in `tests/evidence/test_scientific_governance.py`, splitting files only if readability requires it. Use fixed caller-supplied timestamps and conspicuous strings such as `SENTINEL_GROUP_ALPHA`; fixtures are schema mechanics and cannot become scientific artifacts.
  - [ ] Test canonical byte/ID stability across insertion order, locale, path and timezone; strict parsing; source/group inventory closure; duplicate/missing/extra/cross-role groups; invalid, post-hoc or truth-bearing exclusions; native-role mismatch; randomized seed and method bindings; mutable aliases; and every declared derivation boundary.
  - [ ] Test every freeze stage/slot, including `pretruth_evaluation` ordering and rejection of truth-derived/future/self-referential outputs; the exact stage/action-to-role matrix and negative cross-role cases; exclusion of lineage metadata from learned/detector inputs; unknown or self-registered profiles; not-applicable misuse; unavailable-blocking states; and any identity change producing a new freeze.
  - [ ] Test one-to-one frozen support closure for score and detector-decision dispositions, including missing/extra/duplicate/wrong-support/retained-failure cases; wrong audience/freeze/truth/evaluator/receipt/authorization; restricted-tainted detector graphs or diagnostics; and post-unlock changes.
  - [ ] Test approved, rejected, absent, malformed, wildcard, action/scope/input/owner/output-role/profile/audience mismatch, exact planned-activity digest recomputation, non-substitutability and cross-audience isolation of `truth_unlock`, `restricted_truth_join` and `evaluation`, and attempted authorization reuse. Prove one denied request does not globally block another or touch control/acquisition state.
  - [ ] Add import/side-effect guards proving no default unit path loads datasets, imports legacy training/runtime/dashboard modules, uses filesystem/network/Docker/MinIO, samples clocks/environment, executes activities or writes formal evidence.

- [ ] Task 7: Provide a read-only validator and implementation guide (AC: 1-10)
  - [ ] Add `scripts/validate_scientific_governance.py` only as a read-only local parser/validator for explicitly supplied records and registries. It must never create an authorization, infer approval, resolve mutable aliases, publish, unlock truth or execute any governed action.
  - [ ] Add `docs/scientific-governance-v1.md` with the five-record model, closed vocabularies, profile ownership, stage/slot table, partition-before-derivation rule, truth audience boundary, authorization matrix, deterministic failure semantics, source limitations, legacy quarantine, no-mock/no-number rule and proof boundaries.
  - [ ] Run Stories 9.1-9.7 focused tests, Story 9.8 tests and full Python `unittest` discovery. No passing fake/unit test may claim that an activity occurred, an owner was authenticated, a dataset is scientifically valid or an evaluation is comparable.

## Dev Notes

### Scope and dependency boundaries

- This is a contract-and-validation story, not an execution story. It defines exactly five top-level governance records and pure gates. `TruthJoinRecord.v1` is included because Story 9.6 requires an exact truth-join reference in a complete `EvaluationResult.v1`; it records the restricted evaluator join without performing it. The story does not split a real dataset, generate a window, freeze a live model, reveal truth, evaluate, authorize itself or perform an activity.
- Stories 9.1-9.7 are currently planning artifacts. Implementation must stay sequential and stop if their intended public modules, registries and focused suites are absent. Story 9.8-local stand-ins would create incompatible scientific identities.
- `ready-for-dev` on this planning artifact has `authorization_effect: none`. Because the machine-readable authorization contract does not exist before this story is implemented, implementing Story 9.8 itself still requires a separate explicit human decision; the story cannot self-authorize or retroactively bless its own implementation.
- UI/UX and dashboard work are not required. Epic 18 remains optional read-only presentation; no screen, route, component, chart, browser test or control-surface edit belongs here.

### Minimal record model

- `PartitionRecord.v1` states the complete exact membership of an immutable source universe. The source inventory and code-owned profile decide which boundaries and roles exist; the record never derives those facts from filenames or labels.
- `ScientificFreeze.v1` is phase-aware. A fitting freeze cannot bind a not-yet-produced bundle, a blind-scoring freeze must bind the completed detector configuration before test input is scored, and a `pretruth_evaluation` freeze closes scores, decisions and evaluator/protocol inputs before truth access without binding a future result. `BindingSlot.v1` makes applicability explicit without a universal oversized record.
- `TruthUnlockRecord.v1` is an evaluator-only issuance/lineage record for one exact join. It points to opaque truth and immutable closures but does not contain truth rows, grant general access or act as an IAM capability; its authorization effect is none.
- `TruthJoinRecord.v1` is the immutable evaluator-only lineage fact for the exact authorized join consumed by Story 9.6. It is not a truth dataset, detector input or join executor.
- `ActivityAuthorization.v1` records an exact declared decision and only the audience/scope slots made applicable by its pinned action profile. Its planned-activity digest is computable before the decision and independently recomputed by the gate. Later evidence uses Story 9.6's existing producer-activity identity; the authorization is a separate gate input. This is not a request queue, policy engine, identity provider, signature, scheduler or completion receipt.
- These schemas may conceptually align with provenance and authorization literature, but the project must not claim W3C PROV, Croissant, NIST ABAC/audit, OSF registration or scikit-learn conformance and must not add those systems as dependencies.

### Leakage and evaluation ordering

1. Construct and publish a complete opaque source/group inventory behind the correct audience boundary.
2. Assign complete groups/runs to exact partition roles and publish the partition before deriving windows/sequences.
3. Fit train-owned preprocessing/model state; use only the profile-approved validation/calibration roles for selection, thresholding or calibration.
4. Publish the blind-scoring freeze before test observations reach the detector.
5. Publish exactly one score disposition and detector-decision disposition for every frozen test-support unit, with completion receipts, while test truth remains restricted; then publish the non-self-referential `pretruth_evaluation` freeze.
6. Authorize the exact `truth_unlock` activity and issue `TruthUnlockRecord.v1`; then authorize `restricted_truth_join` against that exact unlock and issue `TruthJoinRecord.v1`; then authorize `evaluation` against that exact join. This is immutable validation ordering, not a workflow engine.
7. Execute and publish the later evaluation through Story 9.6 only under that exact `evaluation` authorization. Any identity change requires a new lineage; the old evidence remains immutable and cannot be silently reinterpreted.

The sequence is a project control derived from FR86/NFR41/NFR52 and supported by leakage, holdout-reuse and preregistration literature. No cited source independently mandates this exact schema or order.

### Academic evidence and mock guardrail

- No mock, domain measurement, scientific outcome or adopted numeric value is needed. `schema_version: 1`, hashes, exact observed timestamps, membership cardinalities computed from listed entries and conspicuous structural sentinels are metadata or test mechanics, not claims about compressor behavior or dataset performance.
- A random seed is recorded reproducibility state, not a universal scientific constant. Story 9.8 supplies no default. If a real method uses randomness, the exact seed and method identities must be deliberately selected, frozen and resolved through Story 9.4; the resulting exact membership remains authoritative.
- Group-safe splitting, split-before-learned-preprocessing, calibration independence and locked-test discipline are methodologically supported, but they do not authorize 80/20, a fold count, a minimum sample count, a particular RNG or a grouping key. Dataset/track owners must bind those choices to exact official dataset semantics and/or approved parameter evidence.
- Tampu, Eklund and Haj-Hosseini provide illustrative medical-imaging evidence of leakage from source-level overlap. Their study does not transfer a subject-level grouping key or any numeric rule to this project's industrial or syscall datasets.
- If a future story requires a domain mock, it must first prove that authentic reproduction of the needed phenomenon is unavailable, then bind a Story 9.4 `MockAdmission.v1` to exact strongly applicable official documentation, every adopted number/assumption, a narrow limitation statement and a direct role in the final comparison between datasets. Story 9.8 creates no exception.

### Verified current repository behavior and quarantine

- `offline_training/splits.py` performs a legacy label/sample-level randomized split with a default train ratio and retains only seed/ratio/counts, not exact group membership. It cannot prove the Story 9.8 partition contract.
- `offline_training/training/run.py` receives already-built sequences, uses the legacy split and evaluates labeled test data immediately. Benchmark adapters discard or merge source trace/recording/native-role identities before that split; multiple windows from one source can therefore cross roles.
- `dataset_builder.py` builds sliding windows across a global eligible-record list containing `training_label`, without proving run/trace/gap/schema/partition boundaries. `scenario_control/runtime.py` exposes scenario/training labels in demo runtime state. Neither shape is formal restricted truth or detector-facing v2 evidence.
- `registry/training_history.py`, `registry/promotion.py`, `online_inference.py`, `cross_benchmark_report.py` and LSTM lifecycle/inference paths use mutable indexes, hidden/default decisions, refitting or threshold recalculation and have no formal freeze/unlock/activity gate. They remain v1/legacy and must not be retrofitted or treated as qualifying evidence in this story.
- Existing dashboard controls directly start/change demo runtime behavior. A click is not an `ActivityAuthorization.v1`, and Story 9.8 must not edit or gate the dashboard.

### Project structure notes

- Contracts: `src/parallel_truth_fingerprint/contracts/scientific_governance.py` and intended exports from `src/parallel_truth_fingerprint/contracts/__init__.py`.
- Pure validators/gates: `src/parallel_truth_fingerprint/evidence/scientific_governance.py`; no service, persistence implementation or dynamic discovery.
- Read-only validator: `scripts/validate_scientific_governance.py`.
- Tests: `tests/evidence/test_scientific_governance.py` unless a later readability-driven split is justified.
- Human guide: `docs/scientific-governance-v1.md`. Machine records are stored only through the Story 9.6/9.7 immutable publication/repository path, never a singleton or `latest` alias.

### Testing and proof boundaries

- Prefer table-driven `unittest` cases, fixed inputs, injected resolvers and exact structured assertions. Expected canonical bytes/IDs must come from reviewed Story 9.5-style golden fixtures rather than being calculated only with the function under test.
- Keep diagnostics bounded, deterministic and audience-safe. Detector-facing failures may identify a stable opaque reference and rule ID but not truth value, attack/scenario name, restricted path, support count or timing pattern.
- Passing proves only that the supplied immutable records are canonical, closed under their registered profiles and mutually consistent for the requested gate. A join outcome proves declared lineage, not that truth rows or metrics are correct. It cannot prove dataset quality, semantic completeness, absence of every leakage source, fairness/comparability, model validity, owner authenticity, permission outside the exact record, successful execution or scientific correctness.

## BMAD Party Mode Review

- Review panel: John (product scope), Winston (architecture), Quinn (academic evidence/QA), and Amelia (developer readiness).
- Initial product-scope score: 9.20/10 - no veto.
- Initial architecture score: 8.85/10 - vetoed.
- Initial academic-evidence and QA score: 8.40/10 - vetoed.
- Initial developer-readiness score: 8.60/10 - vetoed.
- Initial aggregate score: 8.76/10 - not approved. The first round found ambiguous compound action names, incomplete test-support closure, permissive exclusions, no explicit stage-to-partition-role gate, incomplete audience isolation, an underdefined planned-activity identity and a circular generic evaluation freeze/order.
- Final product-scope score: 9.60/10 - no veto.
- Final architecture score: 9.65/10 - no veto.
- Final academic-evidence and QA score: 9.80/10 - no veto.
- Final developer-readiness score: 9.70/10 - no veto.
- Aggregate final score: 9.69/10.
- Auto-approval rule: score at least 9.0 with no veto.
- Decision: auto-approved as `ready-for-dev` after making all actions exact and non-substitutable, making action scopes profile-applicable, closing every source group and every frozen test-support disposition, enforcing FR86 stage-to-role access, separating lineage metadata from learned inputs, adding exact audience isolation, defining a pre-decision planned-activity digest, making the evaluation freeze explicitly pre-truth and ordering unlock, join and evaluation authorization without circularity.
- Product-scope finding: the five records are the smallest complete set because Story 9.6 already requires an exact truth-join reference. No database, service, scheduler, IAM system, workflow engine, runtime integration or UI/dashboard work was added.
- Academic-evidence finding: no mock, domain measurement, outcome, split ratio, fold count, default seed or performance number is introduced. Methodological sources authorize no project-specific numeric choice or grouping key. Any future domain mock remains blocked without authentic-unavailability evidence, exact strongly applicable official support and direct final dataset-comparison linkage.
- Boundary: Party Mode can approve only this planning artifact; `authorization_effect` remains `none`.

### References

- [Source: _bmad-output/planning-artifacts/epics.md#Story 9.8: Define Partition, Freeze, and Activity-Authorization Records]
- [Source: _bmad-output/planning-artifacts/epics.md#Cross-Epic Mock Admission Guardrail]
- [Source: _bmad-output/planning-artifacts/prd.md#FR39]
- [Source: _bmad-output/planning-artifacts/prd.md#FR77]
- [Source: _bmad-output/planning-artifacts/prd.md#FR86]
- [Source: _bmad-output/planning-artifacts/prd.md#NFR39-NFR44]
- [Source: _bmad-output/planning-artifacts/prd.md#NFR47-NFR52]
- [Source: _bmad-output/planning-artifacts/architecture.md#Controlling V2 Architecture Consolidation - 2026-08-22]
- [Source: _bmad-output/planning-artifacts/architecture.md#Authoritative evidence contracts]
- [Source: _bmad-output/planning-artifacts/architecture.md#Verification gates and failure semantics]
- [Source: _bmad-output/planning-artifacts/ux-design-specification.md]
- [Source: _bmad-output/implementation-artifacts/9-1-freeze-and-index-the-v1-evidence-baseline.md]
- [Source: _bmad-output/implementation-artifacts/9-2-establish-the-semantic-and-evidence-role-vocabulary.md]
- [Source: _bmad-output/implementation-artifacts/9-3-build-the-authoritative-source-evidence-catalog.md]
- [Source: _bmad-output/implementation-artifacts/9-4-build-the-parameter-evidence-catalog-and-validation-gate.md]
- [Source: _bmad-output/implementation-artifacts/9-5-preserve-v1-contracts-as-golden-versioned-fixtures.md]
- [Source: _bmad-output/implementation-artifacts/9-6-define-immutable-artifact-and-evaluation-manifests.md]
- [Source: _bmad-output/implementation-artifacts/9-7-qualify-minimal-persistent-evidence-storage.md]
- [W3C PROV-DM Recommendation](https://www.w3.org/TR/2013/REC-prov-dm-20130430/)
- [MLCommons Croissant 1.1 split semantics](https://docs.mlcommons.org/croissant/docs/croissant-spec-1.1.html#splits)
- [scikit-learn: cross-validation iterators for grouped data](https://scikit-learn.org/stable/modules/cross_validation.html#cross-validation-iterators-for-grouped-data)
- [scikit-learn: data leakage](https://scikit-learn.org/stable/common_pitfalls.html#data-leakage)
- [scikit-learn: probability calibration](https://scikit-learn.org/stable/modules/calibration.html)
- [Cawley and Talbot (2010), JMLR: selection bias and model-selection overfitting](https://www.jmlr.org/papers/v11/cawley10a.html)
- [Tampu, Eklund and Haj-Hosseini (2022), Scientific Data: leakage from source-level overlap](https://doi.org/10.1038/s41597-022-01618-6)
- [Kapoor and Narayanan (2023), Patterns: leakage and reproducibility failures](https://doi.org/10.1016/j.patter.2023.100804)
- [Nosek et al. (2018), PNAS: preregistration and prediction/postdiction](https://doi.org/10.1073/pnas.1708274114)
- [OSF Registrations: time-stamped read-only research plans](https://help.osf.io/article/330-welcome-to-registrations)
- [Dwork et al. (2015), NeurIPS: adaptive reuse of holdout data](https://papers.neurips.cc/paper_files/paper/2015/hash/bad5f33780c42f2588878a9d07405083-Abstract.html)
- [NIST SP 800-162: attribute-based access-control concepts](https://csrc.nist.gov/pubs/sp/800/162/upd2/final)

## Mandatory Academic Evidence Amendment

Before implementation, apply the relevant mandatory controls in [Academic Evidence Admission Amendment — 2026-08-31](../planning-artifacts/academic-evidence-admission-amendment-2026-08-31.md). This story must fail closed on an unresolved evidence origin, numeric authority, required mock closure, or prohibited dataset substitution. The amendment adds no activity authorization.
## Dev Agent Record

### Agent Model Used

### Debug Log References

- 2026-09-12: Stories 9.1-9.7 focused prerequisite suite passed (202 tests; 3 skipped).
- 2026-09-12: Initial Story 9.8 contract and pure-validator tests pass; full Python discovery passed (442 tests; 10 skipped).

### Completion Notes List

### File List
