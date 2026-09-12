# Story 16.7: Publish the HAI Dataset Card, Result, and G7 Component

Status: ready-for-dev

## Story

### Story 16.7: Publish the HAI Dataset Card, Result, and G7 Component
**FRs implemented:** FR24, FR26-FR28, FR55-FR58, FR84, FR88.

As an academic reviewer,
I want HAI 23.05 provenance, native semantics, results, and limitations published
together,
So that the benchmark cannot be misrepresented as compressor or custom-fusion
validation.

**Acceptance Criteria:**

**Given** completed HAI source, adapter, partition, candidate, bundle, score,
truth-unlock, and evaluation artifacts
**When** the result package is assembled
**Then** it resolves to official source and version, files and roles, hashes,
native tags and units, chronology, partitions, preprocessing, candidates,
bundle, threshold, scores, metric versions, outcomes, resources, and limitations
**And** reconstruction requires no UI or mutable hidden state.

**Given** author-published HAI statistics, metrics, or reference results
**When** they appear beside local outcomes
**Then** they remain labelled published-reference evidence with exact source
locators
**And** they are not copied into fitting, calibration, selection, thresholding,
or locally measured result fields.

**Given** local custom physical rows, ADFA-LD, LID, or captured syscall evidence
**When** HAI result inputs are validated
**Then** none is inserted, appended, aligned, or represented as part of HAI
23.05
**And** the HAI table remains independently dataset-native.

**Given** HAI tags and results
**When** scientific claims and limitations are written
**Then** the report explicitly preserves their native representation and
different-process scope
**And** it rejects wholesale mA conversion, compressor detector promotion,
real-plant claims beyond the dataset, and cross-dataset fusion.

**Given** source, adapter, native semantics, leakage, bundle, score, temporal
evaluation, provenance, and reporting checks complete
**When** the HAI G7 component is decided
**Then** passing produces `HAI_23_05_BENCHMARK_QUALIFIED`, while failure produces
its explicit blocked or unqualified record with all outcomes and limitations
**And** the record does not overwrite the independent ADFA-LD or LID component
status.

**Given** the HAI result package is finalized
**When** it is consumed by later evidence packaging or optional presentation
**Then** only immutable published artifacts and dataset-specific limitations may
be projected
**And** publication authorizes no retraining, fusion, deployment, control action,
or dashboard implementation.

## Implementation plan

- [ ] Confirm every upstream artifact, schema, parameter, authorization, and code/runtime identity required by the acceptance criteria exists at its exact version and hash. Complete the prior story in Epic 16 before starting this work; never synthesize its planned outputs.
- [ ] Implement only the smallest pure contracts, validators, adapters, or command-line-facing functions needed by the canonical criteria, in the existing repository structure. Do not add a service, database, cloud component, control path, or UI dependency.
- [ ] Make all invalid, unavailable, unknown-version, and unauthorized paths explicit and reconstructible. Never substitute a legacy/default/latest value, cached output, fixture, or a successful alternative.
- [ ] Persist formal evidence atomically: publish immutable objects, verify read-back/hash/size, then publish the complete manifest/receipt. Leave incomplete/orphaned publication visible and non-successful.
- [ ] Add focused unittest coverage for canonical valid and invalid paths, version/schema rejection, authority/provenance failures, immutability, and every failure mode named in the criteria.
- [ ] Record only implementation facts in the Dev Agent Record. Do not claim scientific qualification or issue an activity authorization from this story.

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

- Canonical acceptance criteria: [_bmad-output/planning-artifacts/epics.md](../planning-artifacts/epics.md), Story 16.7.
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