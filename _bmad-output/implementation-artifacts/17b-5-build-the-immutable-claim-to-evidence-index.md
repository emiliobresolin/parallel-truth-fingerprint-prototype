# Story 17B.5: Build the Immutable Claim-to-Evidence Index

Status: ready-for-dev

## Story

### Story 17B.5: Build the Immutable Claim-to-Evidence Index
**FRs implemented:** FR26, FR28, FR65, FR67, FR88, FR92.

As an academic reviewer,
I want every publishable claim linked to its complete immutable evidence chain,
So that I can audit the result without relying on narrative, UI state, or a
mutable latest artifact.

**Acceptance Criteria:**

**Given** a claim proposed for the academic evidence package
**When** it enters the claim-to-evidence index
**Then** it receives a stable claim identity, bounded wording, scope, evidence
track, scientific status, and explicit supported, limited, or unsupported
disposition
**And** the index does not broaden the claim beyond its registered evidence.

**Given** a supported or limited claim
**When** its evidence chain is resolved
**Then** it identifies the exact source and version, role and split, dataset and
run, bundle and threshold, calibration where applicable, score or fusion
record, truth unlock and join, metric and uncertainty, result table or ablation
cell, limitation, code, runtime, and content hashes
**And** every locator is content-addressed or otherwise immutable and
machine-verifiable.

**Given** a claim depends on mock or mock-derived evidence
**When** its chain is indexed
**Then** the capability-gap record, official-document source and exact locator,
supported behaviors and numbers, transfer limitations, exact prototype
component, bounded research question, dataset/modality track, affected final
table, paired-ablation, matrix, or claim element, and mock status are included
**And** the wording cannot imply authentic reproduction, official-real data,
or measured plant behavior.

**Given** a claim lacks a required artifact, locator, applicable metric, or
valid support chain
**When** index validation runs
**Then** the claim is marked unsupported or blocked with the unresolved element
**And** it is rejected from supported conclusions without inventing or
substituting evidence.

**Given** a blocked, not-executed, failed, unavailable, neutral, uncertain, or
unfavorable result
**When** related claims are indexed
**Then** the actual status and limitations remain discoverable alongside any
permitted bounded conclusion
**And** the record cannot be hidden, softened, or redirected to a more favorable
track.

**Given** the complete index
**When** independence and reproducibility checks run
**Then** every link resolves without a dashboard, mutable alias, manual memory,
or hidden evaluator state
**And** orphan claims, orphan artifacts, duplicate identities, hash mismatches,
and circular support chains block the affected claim.

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

### Amendment enforcement: claim provenance

Every claim dependent on custom-generated or mock-parameterized evidence must resolve its origin, generator function/code/runtime/configuration, parameter revisions, admission, official source-use locator/hash, current reproduction assessment, immutable trace/output, limitations, and prohibited claims. A missing or mismatched element blocks the claim rather than weakening its wording.
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

- Canonical acceptance criteria: [_bmad-output/planning-artifacts/epics.md](../planning-artifacts/epics.md), Story 17B.5.
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