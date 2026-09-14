# Story 18.4: Enforce and Verify the Optional Presentation-Only Mode

Status: done

## Story

### Story 18.4: Enforce and Verify the Optional Presentation-Only Mode
**FRs implemented:** FR68, FR70-FR71, FR93.

As a prototype owner,
I want the dashboard evidence mode to be explicitly read-only and independently
verifiable,
So that a convenient demonstration cannot alter science, runtime behavior, or
project readiness.

**Acceptance Criteria:**

**Given** the existing local dashboard also contains operator controls
**When** the optional Epic 18 evidence mode is activated
**Then** runtime, scenario, compressor, actuator, experiment, model, threshold,
fusion, truth, and evidence mutation controls are absent or disabled in that
mode and mutating requests are rejected
**And** the evidence mode exposes only the minimum local read-only navigation
needed to inspect the selected published package.

**Given** a mutation request reaches the local server while
`frozen_evidence` mode is active
**When** any route attempts to change runtime, scenario, compressor, actuator,
experiment, model, threshold, fusion, truth, or evidence state
**Then** the server rejects it independently of whether controls are hidden in
the browser
**And** the selected package and every scientific artifact remain byte-for-byte
unchanged.

**Given** the evidence dashboard is absent, disabled, stopped, malformed, stale,
or unavailable
**When** acquisition, consensus, storage, analytics, evaluation, reconstruction,
or control paths operate
**Then** their behavior and authorization remain independent and unchanged
**And** dashboard failure can never create or alter a command, score, artifact,
gate decision, or scientific status.

**Given** presentation verification fixtures are needed
**When** they are admitted
**Then** non-domain sentinel inputs may test empty, malformed, missing, or unsafe
states without becoming scientific mocks, while every fixture representing
domain behavior or numbers satisfies the Cross-Epic Mock Admission Guardrail
**And** no fixture is presented as a measured prototype or official-dataset
result.

**Given** the exact frozen G9 package and declared local presentation
environment
**When** automated contract and page-level verification runs
**Then** it checks deterministic projection, separate modalities and channels,
linked physical representations, native result scopes, status and limitation
visibility, immutable locators, unavailable and invalid states, safe rendering,
and rejection of every mutation path
**And** verification consumes frozen artifacts without executing training,
inference, fusion, truth relabeling, evaluation, or control.

**Given** a researcher follows the minimal local demonstration instructions
**When** the evidence-only page is opened
**Then** the selected package identity and publication status are visible and
the main physical, syscall, fusion, result, provenance, quality, and limitation
views can be inspected without editing scientific state
**And** no redesign, frontend migration, mobile-specific behavior, animation,
or advanced UX acceptance criterion is required.

**Given** all Epic 18 presentation checks finish
**When** their outcome is recorded
**Then** the optional dashboard is marked available or unavailable with exact
environment, package, verification, failure, and limitation evidence
**And** either outcome leaves G9, implementation readiness, headless
reconstruction, and all scientific evidence unchanged.

## Implementation plan

- [ ] Confirm every upstream artifact, schema, parameter, authorization, and code/runtime identity required by the acceptance criteria exists at its exact version and hash. Complete the prior story in Epic 18 before starting this work; never synthesize its planned outputs.
- [ ] Implement only the smallest pure contracts, validators, adapters, or command-line-facing functions needed by the canonical criteria, in the existing repository structure. Do not add a service, database, cloud component, control path, or UI dependency.
- [ ] Make all invalid, unavailable, unknown-version, and unauthorized paths explicit and reconstructible. Never substitute a legacy/default/latest value, cached output, fixture, or a successful alternative.
- [ ] Persist formal evidence atomically: publish immutable objects, verify read-back/hash/size, then publish the complete manifest/receipt. Leave incomplete/orphaned publication visible and non-successful.
- [ ] Add focused unittest coverage for canonical valid and invalid paths, version/schema rejection, authority/provenance failures, immutability, and every failure mode named in the criteria.
- [ ] Record only implementation facts in the Dev Agent Record. Do not claim scientific qualification or issue an activity authorization from this story.

## Amendment Acceptance Criteria

**Given** the optional read-only projection presents formal evidence
**When** it displays an evidence item, result, or limitation
**Then** it renders only frozen origin, parameter/claim provenance, generator and source-use closure where applicable, current reproduction assessment, and prohibited-claim limitation
**And** it never calculates, infers, hides, promotes, or modifies scientific status, control, authorization, or evidence identity.

- [ ] Add injected, non-network `unittest` cases proving the projection rejects incomplete provenance and cannot turn custom/mock/fixture evidence into official, authentic, or measured presentation.
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

- Canonical acceptance criteria: [_bmad-output/planning-artifacts/epics.md](../planning-artifacts/epics.md), Story 18.4.
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
