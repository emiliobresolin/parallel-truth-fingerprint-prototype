# Story 17B.2: Publish Separate Dataset and Modality Result Tables

Status: ready-for-dev

## Story

### Story 17B.2: Publish Separate Dataset and Modality Result Tables
**FRs implemented:** FR24, FR27, FR66, FR88, FR92.

As a researcher,
I want results published in dataset-native and modality-specific tables,
So that distinct evidence domains remain interpretable without false global
comparisons.

**Acceptance Criteria:**

**Given** the frozen final track registry and metric applicability rules
**When** result tables are assembled
**Then** ADFA-LD, LID-DS 2021, HAI 23.05, `PTFP-Custom-v1` physical, and
`PTFP-Custom-v1` syscall evidence appear in separate identified tables
**And** external benchmark records are never inserted into custom paired rows.

**Given** a table for a specific dataset and modality
**When** its rows and columns are populated
**Then** only frozen dataset-native metrics, support, uncertainty or dispersion,
quality, resource observations, scientific status, and applicable limitations
are reported
**And** every value resolves to the admitted immutable metric evidence.

**Given** a desired metric was not defined, applicable, measured, or qualified
for that evidence track
**When** the table is produced
**Then** it is shown as unavailable or not applicable with an explicit reason
**And** no value is inferred, converted, projected, copied from literature, or
fabricated to complete the table.

**Given** published reference numbers accompany an external dataset
**When** they are displayed for context
**Then** they remain visibly separate from prototype-measured results with exact
official or primary-source locators and non-equivalence limitations
**And** they are not treated as rerun measurements or inputs to a calculated
prototype comparison.

**Given** results differ in dataset, modality, representation, task, support,
truth, split, metric, or operating conditions
**When** the publication tables are organized
**Then** no cross-domain aggregate score, leaderboard, rank, or global champion
is calculated or implied
**And** comparison language is limited to valid within-track or explicitly
paired custom evidence.

**Given** a qualified, limited, blocked, not-executed, failed, unavailable, or
unfavorable track
**When** its table is finalized
**Then** the actual status, support, missing values, failure reasons, and
limitations remain visible
**And** omission cannot be used to make the evidence package appear more
complete or favorable.

## Implementation plan

- [ ] Confirm every upstream artifact, schema, parameter, authorization, and code/runtime identity required by the acceptance criteria exists at its exact version and hash. Complete the prior story in Epic 17b before starting this work; never synthesize its planned outputs.
- [ ] Implement only the smallest pure contracts, validators, adapters, or command-line-facing functions needed by the canonical criteria, in the existing repository structure. Do not add a service, database, cloud component, control path, or UI dependency.
- [ ] Make all invalid, unavailable, unknown-version, and unauthorized paths explicit and reconstructible. Never substitute a legacy/default/latest value, cached output, fixture, or a successful alternative.
- [ ] Persist formal evidence atomically: publish immutable objects, verify read-back/hash/size, then publish the complete manifest/receipt. Leave incomplete/orphaned publication visible and non-successful.
- [ ] Add focused unittest coverage for canonical valid and invalid paths, version/schema rejection, authority/provenance failures, immutability, and every failure mode named in the criteria.
- [ ] Record only implementation facts in the Dev Agent Record. Do not claim scientific qualification or issue an activity authorization from this story.

## Amendment Acceptance Criteria

**Given** a final track, table, ablation, limitation, claim, reconstruction, or G9 input
**When** it refers to evidence or a numeric result
**Then** it verifies and retains its exact origin and numeric-authority closure; custom mock-parameterized evidence additionally retains generator binding, field-level influence, current reproduction assessment, official source-use locator/hash, trace, limitations, and prohibited claims
**And** official ADFA-LD, LID-DS 2021, and HAI 23.05 rows are `official_native` only; custom, mock, replay, or fixture substitution blocks the result/claim/G9 element rather than being summarized as a success.

- [ ] Add non-domain `unittest` cases showing an incomplete closure, cross-dataset substitution, or provenance promotion cannot publish a table, claim, or G9 decision.
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

- Canonical acceptance criteria: [_bmad-output/planning-artifacts/epics.md](../planning-artifacts/epics.md), Story 17B.2.
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