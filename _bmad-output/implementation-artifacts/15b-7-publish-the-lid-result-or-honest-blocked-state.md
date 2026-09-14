# Story 15B.7: Publish the LID Result or Honest Blocked State

Status: in-progress

## Story

### Story 15B.7: Publish the LID Result or Honest Blocked State
**FRs implemented:** FR24, FR26-FR28, FR59-FR64, FR83, FR88.

As a dissertation reader,
I want the LID-DS 2021 track reported whether it executes or remains blocked,
So that unavailable official evidence or authorization is not hidden behind
fixtures or published statistics.

**Acceptance Criteria:**

**Given** exact scope authorization, official source qualification, or adapter
qualification is absent or failed
**When** the LID result is requested
**Then** an immutable `not_executed`, `blocked`, or `unqualified` record identifies
the failed prerequisite, attempted scope, available evidence, and limitation
**And** no local model metric, score, official-real claim, or successful run is
fabricated.

**Given** immutable authorized LID scores, bundle, threshold, partitions, metric
policy, and restricted official labels
**When** the evaluator unlocks labels
**Then** it joins them only through frozen official group, record, and window
identities
**And** no source, scope, score, decision, vocabulary, preprocessing, threshold,
partition, or model artifact changes.

**Given** the LID metric applicability matrix
**When** local outcomes are calculated
**Then** applicable point or window and event or range results include the
declared subset of PR-AUC, precision, recall, F1, false-positive behavior, false
events per operating hour, time to detection, suitable confusion data,
threshold sensitivity, resource cost, and repeated-run dispersion or
uncertainty when supported by official data semantics
**And** unavailable metrics are marked with their dataset-specific reason rather
than inferred from author examples.

**Given** official roles, scenarios, recordings, groups, repetitions, categorical
contexts, and invalid or unavailable cases within the authorized scope
**When** results are stratified
**Then** each applicable declared group and its support remain visible
**And** aggregation cannot hide a failed scenario, excluded recording, blocked
run, unfavorable candidate, or unavailable result.

**Given** author-published LID metrics, examples, or reference results
**When** they appear beside local outcomes
**Then** they remain labelled published-reference evidence with exact source
locators
**And** they stay outside fitting, calibration, selection, thresholding, and
local measured-result calculations.

**Given** the LID track completes in any allowed state
**When** its G7 component record is published
**Then** passing execution produces `LID_DS_2021_BENCHMARK_QUALIFIED`, while
non-execution or failure retains its honest status, provenance, outcomes, and
limitations
**And** no LID state blocks ADFA-LD, HAI, custom capture, later evidence packaging,
or optional presentation, nor does it claim live capture, physical evidence,
fusion, deployment, or control authority.

## Implementation plan

- [ ] Confirm every upstream artifact, schema, parameter, authorization, and code/runtime identity required by the acceptance criteria exists at its exact version and hash. Complete the prior story in Epic 15b before starting this work; never synthesize its planned outputs.
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

- Canonical acceptance criteria: [_bmad-output/planning-artifacts/epics.md](../planning-artifacts/epics.md), Story 15B.7.
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
