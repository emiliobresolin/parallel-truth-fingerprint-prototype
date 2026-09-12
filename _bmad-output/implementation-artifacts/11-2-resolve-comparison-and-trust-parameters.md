# Story 11.2: Resolve Comparison and Trust Parameters

Status: ready-for-dev

<!-- Planning approval does not authorize implementation, consensus activation, evaluation, persistence, publication, control or dashboard work. -->

## Story

As a research owner,
I want every consensus comparison and trust choice resolved through admissible parameter evidence,
so that no anonymous or attractive legacy constant controls v2 decisions.

## Acceptance Criteria

1. **Given** an implemented v2 consensus configuration and Stories 9.1-9.4, 9.6-9.8, 10.1-10.7 and 11.1 public contracts **When** a `ConsensusParameterSet.v2` is built or validated **Then** it binds immutable Story 9.4 `NumericConsumerInventory.v1`, matching `RequiredParameterSet.v1` and accountable `ParameterGateResult.v1` identities with exact component/schema/scope/basis/profile closure, and cannot relax their closed required-slot inventory. Every numeric slot (scale, uncertainty, tolerance, weight and thresholds) binds an exact immutable `ParameterEvidence` revision/schema/hash/canonical bytes; residual/boundary logic binds a distinct immutable versioned canonical policy/operation identity declaring slots, units/dimensions and deterministic conformance closure. Applicable `DecisionRecord` identity is required only for a class/policy that needs it **And** absence, conflict, alias, stale revision, class promotion, float/rounding/default or scope mismatch is an explicit blocked result.

2. **Given** a same-profile raw-current comparison **When** its policy is selected **Then** every parameter is applicable to the cited electrical profile and quality policy **And** an official citation does not transfer unrelated accuracy or tolerance. Given a cross-profile/sensor proposal, its dimensionless residual, derivation, units, input uncertainties and parameter identities must be explicit and reproducible; absent uncertainty support or dimensional inconsistency blocks it.

3. **Given** a primary configuration or sensitivity alternative **When** it is frozen **Then** primary and every alternative bind exact pre-test `DecisionRecord`, frozen analysis-plan and already Story-9.8-validated `ScientificFreeze.v1`/partition-lock identities before test or truth access; an alternative absent from that frozen plan is rejected **And** later outcome cannot choose, replace or promote a primary. A post-freeze change invalidates the old set and returns a blocker with parameter/decision identities for later consumers.

4. **Given** a legacy v1 divergence scale, weight, threshold or comparison tolerance **When** v2 loading/validation runs **Then** it remains only a visibly labelled legacy-reproduction value **And** cannot migrate, activate, derive a default or affect a v2 run, gate, result or claim.

5. **Given** parameter validation runs **When** it is inspected **Then** it performs only pure injected resolution and returns bounded non-published `authorization_effect: none` results; later startup/evaluation owners enact a returned blocker **And** it neither calculates residual/trust/ranking nor invokes or authorizes Python evaluator, Go/ABCI, CometBFT, MQTT, storage, truth, OPC, syscall, control, UI/dashboard or activity.

6. **Given** tests/docs run **When** default discovery executes **Then** fixed conspicuous non-domain identity fixtures and injected resolvers prove complete closure, class-specific authority, same/cross-profile restrictions, freeze/alternative invariance, blocked current catalog and legacy quarantine **And** no test/import starts services, network, clock/random/environment defaults or formal activity.

## Tasks / Subtasks

- [ ] Add a flat frozen canonical `ConsensusParameterSet.v2` and pure validator, e.g. `src/parallel_truth_fingerprint/consensus_v2_parameters.py` and `evidence/consensus_parameter_validation.py`, only after upstream public exports exist. Bind slot-to-exact parameter revision, basis/quality/profile/experiment scope, primary/sensitivity plan and decision freeze identity; no value calculation or substitute registry.
- [ ] Inject Story 9.4 parameter/decision/mock resolvers. Enforce class authority: direct exact official use; derived validated inputs/dimensional derivation; measured preserved method; preregistered factor frozen before test; mock only valid/approved/unavailable-with-evidence admission, official support for each behavior/value and final paired-comparison linkage. Do not use citation prestige as value authority.
- [ ] Keep `consensus/trust_model.py`, `consensus/engine.py`, comparison defaults/rounding, legacy contracts/tests, runtime demo and dashboard untouched/quarantined. Their hard-coded scales, thresholds and tolerances are never v2 input.
- [ ] Add `docs/consensus-parameter-evidence-v2.md` and focused standard-library `unittest` tests. Prove missing/duplicate/conflicting/out-of-scope/post-freeze parameters, unknown sensitivity plan, cross-profile uncertainty/dimension failure, no default/legacy migration and no side effects. Report the current formal set as blocked until the complete evidenced parameter universe exists.

## Dev Notes

- Story 11.2 owns parameter selection/freeze only. Story 11.3 evaluates with a validated frozen set; 11.4 integrates Go/ABCI; 11.6 closes G3. Passing means accountable configuration, never authorization or a consensus/G3 claim.
- Current 9.4 and domain/profile/mock evidence remain planning-only/incomplete. No new numeric claim is permitted; UI/UX remains optional and out of scope.

## Mandatory Academic Evidence Amendment

Before implementation, apply the relevant mandatory controls in [Academic Evidence Admission Amendment — 2026-08-31](../planning-artifacts/academic-evidence-admission-amendment-2026-08-31.md). This story must fail closed on an unresolved evidence origin, numeric authority, required mock closure, or prohibited dataset substitution. The amendment adds no activity authorization.

## BMAD Party Mode Review

- Initial review identified missing independent numeric-inventory/gate closure, residual-policy identity and freeze binding; the story was revised.
- Final review: product/PM `9.65`, architecture `9.85`, academic/QA `9.80`, all without veto; aggregate `9.77`.
- Decision: auto-approved for `ready-for-dev`. Party Mode approves this planning artifact only and grants no activity authorization.

### References

- [Source: _bmad-output/planning-artifacts/epics.md#Story 11.2: Resolve Comparison and Trust Parameters]
- [Source: _bmad-output/planning-artifacts/prd.md#FR91]
- [Source: _bmad-output/planning-artifacts/architecture.md#Authoritative evidence contracts]
- [Source: _bmad-output/implementation-artifacts/9-4-build-the-parameter-evidence-catalog-and-validation-gate.md]
- [Source: _bmad-output/implementation-artifacts/11-1-define-the-versioned-consensus-v2-contracts.md]
