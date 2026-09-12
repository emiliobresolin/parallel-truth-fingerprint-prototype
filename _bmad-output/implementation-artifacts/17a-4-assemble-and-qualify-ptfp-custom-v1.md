# Story 17A.4: Assemble and Qualify `PTFP-Custom-v1`

Status: ready-for-dev

## Story

### Story 17A.4: Assemble and Qualify `PTFP-Custom-v1`
**FRs implemented:** FR18, FR25-FR26, FR28, FR37, FR39-FR41, FR72, FR85-FR86.

As an evidence owner,
I want complete synchronized runs assembled into an immutable custom dataset,
So that paired detector conditions use only authentic same-run evidence with
isolated truth.

**Acceptance Criteria:**

**Given** finalized campaign run manifests
**When** `PTFP-Custom-v1` admission runs
**Then** each candidate run must contain compatible physical observations and
authentic workload-attributed Linux syscall segments from the same experiment
and run with resolvable clock, correlation, configuration, completeness, and
quality evidence
**And** external ADFA-LD, LID, HAI, fixture, or fabricated records are rejected.

**Given** an admitted custom run
**When** its dataset manifest entry is created
**Then** it binds physical and syscall stream manifests, workload and control
trace, profiles and parameters, mock admissions, capture and runtime identity,
clock and correlation evidence, modality quality, optional declared consensus
and OPC evidence, and a separate restricted-truth reference
**And** modality-specific source artifacts remain distinct.

**Given** complete custom runs
**When** the `PTFP-Custom-v1` partition is frozen
**Then** whole independent runs are assigned before physical or syscall windows
are generated to the applicable lifecycle roles
**And** no run or derived window can cross a partition, run, scenario, gap,
schema, configuration, clock-policy, or modality-quality boundary.

**Given** physical and syscall windows are proposed as a pair
**When** alignment validation runs
**Then** both resolve to the same held-out run and declared alignment interval,
clock policy, quality policy, configuration, and immutable source ranges
**And** missing, duplicated, mis-correlated, mixed, or boundary-crossing windows
receive an explicit ineligible reason rather than forced alignment.

**Given** detector-facing dataset artifacts
**When** truth-boundary validation runs
**Then** observations, syscall events, features, windows, partitions, and future
score inputs contain no truth, labels, scenario meaning, intervention meaning,
or expected outcomes
**And** truth remains locked under the preregistered evaluator-only rule.

**Given** synchronized-stream, leakage, capture-authenticity, clock,
correlation, modality-quality, storage, completeness, provenance, mock-admission,
and truth-isolation checks complete
**When** G8 is decided
**Then** only passing evidence receives immutable `DATASET_QUALIFIED` and
`PTFP_CUSTOM_V1_QUALIFIED` identities, while every invalid, incomplete, or
aborted run remains preserved with its reason
**And** passing G8 neither executes detector scoring or fusion nor authorizes
training, truth unlock, deployment, control, or UI work.

## Implementation plan

- [ ] Confirm every upstream artifact, schema, parameter, authorization, and code/runtime identity required by the acceptance criteria exists at its exact version and hash. Complete the prior story in Epic 17a before starting this work; never synthesize its planned outputs.
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

### Amendment enforcement: complete dataset admission

Reconstruct each accepted custom physical output through admission → generation binding → immutable trace → observation. Reconstruct each accepted syscall range through G6 → `host_capture` raw bytes/hash → collector/kernel/process chain. A passing G6 identifier, a mock ID, or a neighboring valid segment alone is insufficient; missing/mixed/alternate provenance rejects the formal dataset.
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

- Canonical acceptance criteria: [_bmad-output/planning-artifacts/epics.md](../planning-artifacts/epics.md), Story 17A.4.
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