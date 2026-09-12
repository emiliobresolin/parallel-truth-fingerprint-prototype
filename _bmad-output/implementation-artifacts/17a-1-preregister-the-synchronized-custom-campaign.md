# Story 17A.1: Preregister the Synchronized Custom Campaign

Status: ready-for-dev

## Story

### Story 17A.1: Preregister the Synchronized Custom Campaign
**FRs implemented:** FR34-FR38, FR75-FR77, FR85-FR86, FR89.

As a research owner,
I want every custom campaign and fusion decision frozen before execution,
So that the final paired result cannot be redesigned after observing evidence or
truth.

**Acceptance Criteria:**

**Given** a proposed `PTFP-Custom-v1` campaign
**When** its preregistration record is created
**Then** it binds exact experiment and run plan, physical and workload profiles,
applicable mock-admission records, parameter set, schedules, scenarios,
interventions, recovery, durations, repetitions, expected streams, clock and
correlation policy, partitions, windows, stopping and abort rules, metric
policy, truth-unlock rule, and code and runtime identities
**And** unavailable or inapplicable components are explicit.

**Given** physical and syscall detector use is planned
**When** campaign configuration is frozen
**Then** it identifies exact immutable bundle, schema or vocabulary,
preprocessing, calibration, threshold, score direction, compatibility, and
runtime identities for both modalities
**And** neither bundle may be selected or changed using campaign test truth.

**Given** late fusion is planned
**When** the fusion policy is preregistered
**Then** it declares the simple policy, calibrated score interpretation, window
alignment, availability and missing-modality rules, required quality, output
decision semantics, and every parameter identity before execution
**And** learned or test-fitted weights are outside this campaign unless a
separate supervised experiment is later authorized.

**Given** a campaign numeric value for schedule, duration, repetition, window,
clock tolerance, capture quality, alignment, detector threshold, fusion, metric,
or stopping policy
**When** parameter validation runs
**Then** it resolves to applicable direct, derived, measured, preregistered, or
properly admitted mock evidence
**And** no architecture, tool example, external benchmark, or desired outcome
supplies an anonymous value.

**Given** valid, invalid, aborted, incomplete, unfavorable, and recovery runs
are possible
**When** the run matrix is frozen
**Then** every planned condition and reporting treatment is explicit
**And** only successful or favorable runs cannot define the final campaign
after execution.

**Given** preregistration validation passes
**When** the record is published
**Then** all identities, decisions, parameters, limitations, owners, and hashes
are immutable and human- and machine-readable
**And** preregistration does not authorize campaign execution, capture,
training, fusion, activation, deployment, control changes, or UI work.

## Implementation plan

- [ ] Confirm every upstream artifact, schema, parameter, authorization, and code/runtime identity required by the acceptance criteria exists at its exact version and hash. Use only the exact immutable prerequisites named in the canonical acceptance criteria; absence is an explicit blocked state.
- [ ] Implement only the smallest pure contracts, validators, adapters, or command-line-facing functions needed by the canonical criteria, in the existing repository structure. Do not add a service, database, cloud component, control path, or UI dependency.
- [ ] Make all invalid, unavailable, unknown-version, and unauthorized paths explicit and reconstructible. Never substitute a legacy/default/latest value, cached output, fixture, or a successful alternative.
- [ ] Persist formal evidence atomically: publish immutable objects, verify read-back/hash/size, then publish the complete manifest/receipt. Leave incomplete/orphaned publication visible and non-successful.
- [ ] Add focused unittest coverage for canonical valid and invalid paths, version/schema rejection, authority/provenance failures, immutability, and every failure mode named in the criteria.
- [ ] Record only implementation facts in the Dev Agent Record. Do not claim scientific qualification or issue an activity authorization from this story.

## Amendment Acceptance Criteria

**Given** a synchronized custom campaign is preregistered, readied, run, or assembled
**When** a physical or syscall record is admitted
**Then** mock-parameterized physical evidence resolves its frozen generator/parameter/admission/source-use/trace closure and a new run-scoped `DirectReproductionAssessment.v1`; syscall evidence resolves its complete G6 `host_capture` raw-byte chain
**And** a mock ID, G6 ID, neighboring valid segment, old assessment, fixture, synthetic syscall, or alternate generator alone is insufficient for `PTFP-Custom-v1` eligibility.

- [ ] Add isolated tests that preserve an invalid/incomplete run while rejecting its synchronized-evidence eligibility and retain the precise blocking reason.
## Non-negotiable scientific guardrails

- This is a local academic prototype. Keep the implementation small, explicit, deterministic, and independent of the optional dashboard.
- Do not invent or inherit numbers, tolerances, labels, defaults, fixtures, legacy contracts, or authority. Every scientific parameter must have immutable identity and exactly one permitted authority class (`direct`, `derived`, `measured`, `preregistered_factor`, or an approved `mock`).
- Treat missing prerequisites and authorization as an explicit blocked result. `ready-for-dev` authorizes planning only; it does not authorize implementation, acquisition, persistence, capture, training, evaluation, truth activity, activation, publication, or presentation.
- Preserve immutable evidence objects before manifests/receipts; read back and verify content identity, hash, and size. Retain incomplete, failed, recovered, and unfavorable outcomes.
- Keep truth and labels restricted; detector-facing artifacts must not carry truth, expected outcomes, or semantic scenario information. Only evaluator-only, separately authorized post-freeze activities may unlock/join truth.
- Unit tests use `unittest`, injected dependencies, and non-domain fixtures. Default tests must not start network, Docker, MinIO, MQTT, CometBFT, hardware, capture, control, dashboard, or scientific activity. Live/integration tests are opt-in, isolated, and separately authorized.

## Existing-code and scope notes

- Follow the current Python/Go repository patterns established by Stories 9â€“11; preserve versioned v1 behavior and quarantine legacy/demo material when reproduction requires it.
- No numbers, thresholds, intervals, weights, or tolerances are specified by this story beyond those already present in immutable, applicable evidence or preregistered records. Fail closed if such evidence is absent.
- Dataset boundaries are native and separate: ADFA-LD/LID-DS 2021 are syscall evidence; HAI 23.05 is not compressor evidence; only synchronized PTFP-Custom-v1 can support paired physical/syscall/fusion comparison.

### Amendment enforcement: campaign freeze

Preregistration must bind the approved generator closure, expected emission-trace role, formal capture-origin policy, and per-run direct-reproduction assessment requirement. It cannot pre-authorize an unassessed future mock or a synthetic syscall path.
## BMAD Party Mode Review

### Initial independent review

| Perspective | Reviewer | Score | Veto | Findings |
| --- | --- | ---: | --- | --- |
| Product / PM | John (PM) | 9.2 | No | Scope is minimal and the criteria preserve the stated academic outcome without turning the dashboard into a dependency. |
| Architecture | Winston (Architect) | 9.3 | No | Versioning, isolation, fail-closed behavior, and existing-structure constraints are explicit. |
| Academic / QA | Quinn (QA) | 9.4 | No | Acceptance evidence, negative paths, provenance, and isolated unittest requirements are testable. |

### Corrections applied

- Added explicit prohibition on planned-output substitution and legacy/default fallback.
- Added atomic evidence publication/read-back and non-successful incomplete-state handling.
- Added exact authority, truth-separation, and opt-in test constraints to make the canonical criteria implementable without scope expansion.

### Final review

| Perspective | Reviewer | Score | Veto | Decision |
| --- | --- | ---: | --- | --- |
| Product / PM | John (PM) | 9.4 | No | Approved |
| Architecture | Winston (Architect) | 9.5 | No | Approved |
| Academic / QA | Quinn (QA) | 9.5 | No | Approved |

Final average: **9.47/10**. Vetoes: **none**. Decision: **approved for planning (ready-for-dev)**. This decision grants no scientific or implementation activity authorization.

## References

- Canonical acceptance criteria: [_bmad-output/planning-artifacts/epics.md](../planning-artifacts/epics.md), Story 17A.1.
- Current control state: [_bmad-output/implementation-artifacts/sprint-status.yaml](sprint-status.yaml).
- Governing requirements and authority constraints: _bmad-output/planning-artifacts/prd.md and prd-update-2026-08-15.md.
- Architecture and project guardrails: _bmad-output/planning-artifacts/architecture.md, architecture-update-2026-08-15.md, and existing Stories 9â€“11.

## Mandatory Academic Evidence Amendment

Before implementation, apply the relevant mandatory controls in [Academic Evidence Admission Amendment — 2026-08-31](../planning-artifacts/academic-evidence-admission-amendment-2026-08-31.md). This story must fail closed on an unresolved evidence origin, numeric authority, required mock closure, or prohibited dataset substitution. The amendment adds no activity authorization.
## Dev Agent Record

### Agent Model Used

Planning artifact only; implementation has not started.

### Debug Log References

None.

### Completion Notes List

- Complete canonical context analysis and Party Mode review recorded.
- Status is ready-for-dev; no code, evidence, or authorization was produced.

### File List

- Planned implementation work is intentionally not performed by this story-planning task.