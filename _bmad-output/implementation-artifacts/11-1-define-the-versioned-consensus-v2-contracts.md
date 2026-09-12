# Story 11.1: Define the Versioned Consensus v2 Contracts

Status: ready-for-dev

<!-- Planning READY does not authorize implementation, consensus activation, Go/ABCI migration, CometBFT use, experiment execution, persistence, publication, control, dashboard work, or scientific claims. -->

## Story

As a consensus evidence consumer,
I want explicit input and decision contracts for physical consensus,
so that every comparison has a valid current-domain basis and reconstructible outcome.

## Acceptance Criteria

1. **Given** the implemented public v2 contracts from Stories 9.1-9.8 and 10.1-10.7 **When** `ConsensusRoundInput.v2` is canonically built or validated **Then** its flat immutable content binds schema/version/content identity; experiment/run/round; exact instrument-profile identities; immutable versioned comparison-basis ID/schema/hash/canonical bytes and units; quality-policy and parameter-evidence identities; the exact public `PhysicalEvidenceQualificationResult.v1` identity; participating edge `SignalObservation.v2` immutable references/canonical hashes; source sequences and opaque correlation identities **And** injected strict resolvers verify the qualification result is immutable, audience-compatible, `PHYSICAL_EVIDENCE_QUALIFIED` with explicit G2 pass and closes every cited observation/profile/parameter identity. Missing, stale, mixed, mutable, malformed or incompatible input fails without defaults, aggregation or a legacy conversion.

2. **Given** redundant observations from the same compatible profile **When** their basis is declared **Then** the only direct comparison basis is the preserved raw current domain with exact compatible units/profile/quality closure **And** normalized or engineering representations cannot substitute without a separately versioned declared basis. This story defines no tolerance, scale, weight, residual formula, ranking calculation or trust policy.

3. **Given** observations differ by sensor, profile, range or unit **When** a joint comparison is proposed **Then** the input must bind an exact documented dimensionless profile-aware residual definition, applicable input uncertainties, units, profiles and parameter-evidence identities **And** absent/incompatible support blocks construction; incompatible raw values are never averaged, ranked or coerced directly.

4. **Given** a consensus decision or explicit failure is represented **When** `ConsensusDecision.v2` is canonically built or validated **Then** it binds its exact round input/hash, immutable comparison-basis ID/schema/hash/canonical bytes, explicit outcome, complete participant list, included and excluded identities, evidence-based exclusion reason for every exclusion, opaque correlations, parameter identities and input evidence hashes. A successful outcome carries its complete ordered edge ranking; failure carries explicit `no_ranking`/empty-ranking plus complete participant/exclusion closure and diagnostics, never a reduced success or fabricated winner **And** failure is distinct from success. It is a representation/validation contract, not an evaluator result or a permission to persist/activate consensus.

5. **Given** a v2 consensus input, decision or declared public dependency semantic/provenance/audience graph **When** validation runs **Then** direct forbidden fields and every declared edge absent, restricted, mutable, audience-incompatible or unregistered in the immutable map—including syscalls, truth, labels, scenario meaning, detector score, fusion decision, OPC-derived substitute and actuator command—is rejected before canonical bytes exist **And** public records use opaque IDs only. The Story 10.5/9.8 map closure covers adopted boundaries, not arbitrary undeclared external covert channels; this story never reads restricted bytes/locators/counts/timing.

6. **Given** valid and invalid contract fixtures **When** canonical serialization/validation repeats across equivalent input orderings **Then** ordering, canonical bytes, content IDs, decision IDs and hashes are deterministic and every missing/mixed/stale/incompatible/malformed case returns bounded actionable diagnostics **And** no test/import starts network, broker, CometBFT, Go/ABCI, storage, control, dashboard, clock/random/environment default or a formal project activity.

## Tasks / Subtasks

- [ ] Task 1: Add only immutable v2 contract surface (AC: 1-4, 6)
  - [ ] Add `src/parallel_truth_fingerprint/contracts/consensus_v2.py` with closed frozen flat types such as `ConsensusRoundInputV2`, `ConsensusDecisionV2`, `ConsensusObservationRefV2`, `ComparisonBasisV2` and `ConsensusOutcomeV2`; strict parser/serializer, canonical bytes and recomputed content IDs only. Re-export narrowly only after upstream contracts exist.
  - [ ] Require injected immutable `SignalObservation.v2`/profile/parameter/basis/qualification resolvers. The basis is versioned ID/schema/hash/canonical bytes, and the qualification result must be immutable public G2-pass `PHYSICAL_EVIDENCE_QUALIFIED` closure for every cited input; never accept a legacy observation object, mutable dictionary, inferred source sequence/round/time, float coercion, `latest` alias or caller-selected applicability.
  - [ ] Model direct same-profile current basis separately from cross-profile/sensor dimensionless residual basis. Contract fields name required authority; Story 11.2 owns all parameter/residual/tolerance/weight/threshold selection and Story 11.3 owns calculations.

- [ ] Task 2: Validate closure and modality isolation purely (AC: 1-5)
  - [ ] Add `src/parallel_truth_fingerprint/evidence/consensus_contract_validation.py` only when its upstream public packages exist. Inject resolvers and the immutable Story 10.5/9.8 role/provenance/audience map; perform no I/O, storage, authorization, evaluation, command, transport or publication.
  - [ ] Validate complete participant/included/excluded closure and one explicit reason per exclusion; require complete ranking only on success and `no_ranking`/empty ranking on failure. Reject success/failure ambiguity, direct incompatible raw comparison and declared semantic/provenance/audience-map leakage. Return bounded non-published `authorization_effect: none` diagnostics only.

- [ ] Task 3: Quarantine legacy consensus and test canonical contracts (AC: 1-6)
  - [ ] Preserve `consensus/engine.py`, `trust_model.py`, `cometbft_client.py`, `cometbft_mapper.py`, legacy `contracts/consensus_*`, HART payloads, MQTT, runtime, persistence and dashboard untouched. They contain engineering averages, anonymous scales/thresholds, float/datetime coercion or I/O and are v1-only.
  - [ ] Add `docs/consensus-v2-contracts.md`, `tests/contracts/test_consensus_v2.py` and optional `tests/evidence/test_consensus_contract_validation.py`. Use fixed conspicuous non-domain fixtures and standard-library `unittest`.
  - [ ] Test unknown/duplicate/alias keys; canonical byte/hash permutations; immutable observation closure; same-profile raw-current restriction; cross-profile residual/uncertainty/parameter closure; missing/mixed profile/basis/unit/sequence/correlation/hash; participant/ranking/exclusion closure; failure-versus-reduced-success; every declared forbidden/transitive semantic edge; and legacy/network/control/storage/dashboard import guards. If prerequisites remain planning-only, report blocked rather than adding placeholders or running consensus.

## Dev Notes

### Boundaries and current blockers

- Story 11.1 only defines/validates contracts. Story 11.2 resolves comparison and trust parameters; Story 11.3 implements the deterministic Python evaluator; Story 11.4 alone integrates Go ABCI/CometBFT. G3 parity is a later gate, not a claim here.
- Stories 10.6/10.7 own physical collection/G2. Consensus consumes eligible immutable public `SignalObservation.v2` references only; it cannot change commands, repair observations, replace independent OPC evidence, access truth or create an aggregate physical result.
- All upstream v2 artifacts remain planning-only. Current profile/parameter/mock blockers therefore prevent formal consensus activity. Party approval and every result in this story have `authorization_effect: none`.
- No mock, domain number, tolerance, scale, weight, threshold, residual formula, safety or plant claim is introduced. Legacy constants remain disabled for v2; UI/UX is optional and out of scope.

### Project structure

- New isolated contracts: `src/parallel_truth_fingerprint/contracts/consensus_v2.py`.
- Pure validator: `src/parallel_truth_fingerprint/evidence/consensus_contract_validation.py` only after upstream exports exist.
- Docs/tests as named above. No new dependency, service, database, broker route, storage prefix, Go code, dashboard, control path or runtime activation.

## BMAD Party Mode Review

- Initial review: product/PM `9.35`, architecture `9.70`, academic/QA `9.40`, all without veto. The story was revised for success-versus-failure ranking, immutable basis closure and G2-qualified public input closure.
- Final review: product/PM `9.75` (no veto), architecture `9.85` (no veto), academic/QA `9.70` (no veto); aggregate `9.77`.
- Decision: auto-approved for `ready-for-dev`; Party Mode authorizes this planning artifact only.

### References

- [Source: _bmad-output/planning-artifacts/epics.md#Story 11.1: Define the Versioned Consensus v2 Contracts]
- [Source: _bmad-output/planning-artifacts/prd.md#FR91]
- [Source: _bmad-output/planning-artifacts/prd.md#NFR47-NFR50]
- [Source: _bmad-output/planning-artifacts/architecture.md#Trust and authority boundaries]
- [Source: _bmad-output/planning-artifacts/architecture.md#Authoritative evidence contracts]
- [Source: _bmad-output/planning-artifacts/architecture.md#Verification gates and failure semantics]
- [Source: _bmad-output/implementation-artifacts/9-8-define-partition-freeze-and-activity-authorization-records.md]
- [Source: _bmad-output/implementation-artifacts/10-2-define-and-validate-signalobservation-v2.md]
- [Source: _bmad-output/implementation-artifacts/10-5-isolate-scenariotruth-v1-and-control-truth-unlock.md]
- [Source: _bmad-output/implementation-artifacts/10-7-qualify-and-publish-physical-experiment-evidence.md]

## Mandatory Academic Evidence Amendment

Before implementation, apply the relevant mandatory controls in [Academic Evidence Admission Amendment — 2026-08-31](../planning-artifacts/academic-evidence-admission-amendment-2026-08-31.md). This story must fail closed on an unresolved evidence origin, numeric authority, required mock closure, or prohibited dataset substitution. The amendment adds no activity authorization.
## Dev Agent Record

### Agent Model Used

### Debug Log References

### Completion Notes List

### File List
