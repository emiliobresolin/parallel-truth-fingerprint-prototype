# Story 18.1: Bind a Read-Only Projection to the Frozen Evidence Package

Status: ready-for-dev

## Story

### Story 18.1: Bind a Read-Only Projection to the Frozen Evidence Package
**FRs implemented:** FR68, FR71, FR92-FR93.

As a researcher,
I want the existing dashboard to read one exact published evidence package,
So that the demonstration reflects immutable G9 evidence without recalculation
or mutable latest-state assumptions.

**Acceptance Criteria:**

**Given** Epic 18 has been separately activated and an exact Epic 17B package
manifest is selected
**When** the dashboard evidence projection loads
**Then** the manifest identity, `G9_PASS` decision, schema, content hashes,
source locators, result artifacts, and declared compatibility evidence verify
before any result is displayed
**And** an absent, blocked, mutable, incompatible, or hash-mismatched package is
shown as unavailable with the reason rather than as published evidence.

**Given** the dashboard is showing live/current prototype state instead of an
explicitly selected immutable `G9_PASS` package
**When** the page loads
**Then** its mode is `legacy_demo` and the persistent status reads
`DEMO - NOT PUBLISHED SCIENTIFIC EVIDENCE`
**And** no live/latest value is presented as a frozen scientific result.

**Given** a verified package
**When** the dashboard payload is assembled
**Then** fields are projected directly from the frozen track registry, result
tables, custom ablation, capability and limitation matrix, and
claim-to-evidence index
**And** the projection cannot import, split, train, infer, calibrate, promote,
fuse, relabel, recompute, rank, or rewrite scientific artifacts.

**Given** a package value is unavailable, not applicable, blocked,
not-executed, failed, neutral, uncertain, unfavorable, or mock-derived
**When** it is projected
**Then** its exact status, reason, provenance, and limitation remain visible
**And** the dashboard does not fill, normalize, reinterpret, or improve it.

**Given** a projection field or source locator supplied by the package
**When** it is parsed and rendered
**Then** it is treated as untrusted input, validated against the declared
read-only schema, and safely encoded for presentation
**And** unknown fields, invalid identities, unsafe locators, and malformed
values fail closed without altering the package or local runtime.

**Given** the page refreshes or the projection is loaded again
**When** the selected package identity is unchanged
**Then** all scientific values, statuses, ordering, references, and limitations
remain deterministic under the declared presentation rules
**And** evidence generation time, package identity, and last verification time
remain distinct from live process freshness.

## Implementation plan

- [ ] Confirm every upstream artifact, schema, parameter, authorization, and code/runtime identity required by the acceptance criteria exists at its exact version and hash. Use only the exact immutable prerequisites named in the canonical acceptance criteria; absence is an explicit blocked state.
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

- Canonical acceptance criteria: [_bmad-output/planning-artifacts/epics.md](../planning-artifacts/epics.md), Story 18.1.
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