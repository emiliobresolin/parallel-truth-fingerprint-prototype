# Story 17B.1: Validate and Register the Final Evidence Tracks

Status: ready-for-dev

## Story

### Story 17B.1: Validate and Register the Final Evidence Tracks
**FRs implemented:** FR24, FR26, FR28, FR65, FR67, FR88, FR92.

As an academic evaluator,
I want every final evidence track registered with its exact scientific status
and immutable identities,
So that publication starts from qualified results rather than reconstructed or
preferred outcomes.

**Acceptance Criteria:**

**Given** completed or explicitly blocked outputs from the physical custom,
syscall custom, ADFA-LD, LID-DS 2021, HAI 23.05, and paired custom-fusion tracks
**When** final evidence admission runs
**Then** each track resolves its source and version, dataset role and split,
bundle and threshold, calibration where applicable, score manifest, truth
unlock, metric result, uncertainty, limitation, scientific status, code,
runtime, and content hash
**And** no result is recomputed, refitted, reselected, relabeled, or manually
completed during admission.

**Given** an evidence track that used an admitted scientific mock
**When** its status is registered
**Then** the capability-gap record, official-document locator, supported
behavior and numbers, provenance, and `mock` or `mock-derived` status required
by the Cross-Epic Mock Admission Guardrail remain attached
**And** the evidence cannot be promoted to measured, official-real, real-plant,
or authentically reproduced evidence.

**Given** any custom evidence or claim depends on a researcher-selected factor,
derived representation, or admitted emulator behavior
**When** the final registry is assembled
**Then** the exact immutable `DecisionRecord.v1`, `ParameterEvidence.v1`, and
`MockAdmission.v1` identities and their prohibited claims remain in the
admission and claim chain
**And** a source record cannot replace decision authority, a derivation cannot
hide its inputs, and a mock cannot lose its replacement condition.

**Given** the LID-DS 2021 track could not qualify or execute under its frozen
protocol
**When** the final registry is assembled
**Then** its immutable blocked or not-executed record and reason are retained
without fabricating measurements
**And** that status does not invalidate otherwise qualified independent tracks.

**Given** a required track artifact is missing, mutable, incompatible, or does
not resolve to its declared source
**When** admission validation runs
**Then** that track receives an explicit incomplete or blocked status with the
failed requirement
**And** it cannot supply a result, comparison, or academic claim.

**Given** the physical and syscall `PTFP-Custom-v1` tracks and their paired
ablation
**When** completeness is checked
**Then** their artifacts resolve to the same G8-qualified campaign identities
and the exact frozen Epic 17A evidence
**And** absence of mandatory custom evidence blocks the final G9 publication
package rather than being replaced by an external benchmark or mock.

**Given** all candidate evidence tracks have been checked
**When** the final track registry is frozen
**Then** qualified, limited, blocked, not-executed, failed, unavailable, and
unfavorable outcomes remain addressable with their reasons
**And** only registry-listed immutable artifacts may feed later Epic 17B
tables, matrices, indexes, and reconstruction.

## Implementation plan

- [ ] Confirm every upstream artifact, schema, parameter, authorization, and code/runtime identity required by the acceptance criteria exists at its exact version and hash. Use only the exact immutable prerequisites named in the canonical acceptance criteria; absence is an explicit blocked state.
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

### Amendment enforcement: final track closure

A mock-parameterized/prototype-generated dependency may be registered only with its frozen generator identity, current direct-reproduction assessment, exact parameter/admission/source-use closure, output trace, limitations, and prohibited claims. Preserve this provenance as a limitation; never collapse it into authentic, measured, or official-native evidence.
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

- Canonical acceptance criteria: [_bmad-output/planning-artifacts/epics.md](../planning-artifacts/epics.md), Story 17B.1.
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