# Story 12.6: Qualify Independent OPC UA Evidence and Close Gate G4

Status: ready-for-dev

## Story

### Story 12.6: Qualify Independent OPC UA Evidence and Close Gate G4
**FRs implemented:** FR15-FR17, FR42-FR48, FR90.

As a research owner,
I want the independent OPC UA path qualified as a complete evidence boundary,
So that later reports can distinguish valid comparison evidence from transport
or integrity failure.

**Acceptance Criteria:**

**Given** an approved pre-consensus snapshot and active OPC v2 path
**When** the G4 round-trip fixture executes
**Then** evidence travels through snapshot writer, separate OPC UA server,
`opc.tcp`, distinct `asyncua.Client`, `ScadaObservation.v2`, integrity
validation, and eligible comparison
**And** no in-process object read or consensus projection substitutes for a
protocol step.

**Given** successful client reads
**When** round-trip invariants are checked
**Then** values, units, profile, revision, `StatusCode`, source and server
timestamps, client-observed time, correlation, endpoint, namespace, and NodeIds
remain coherent and reconstructible
**And** any allowed tolerance has applicable parameter evidence.

**Given** invalid, uncertain, stale, missing, mixed, mis-correlated,
unavailable, disconnected, or restarted OPC conditions
**When** the failure matrix executes
**Then** each condition yields its explicit integrity and comparison status
**And** none produces a valid comparison through cached, internal, or consensus
fallback data.

**Given** the causal-independence matrix
**When** consensus-only, OPC-only, and common-snapshot variations are evaluated
**Then** the expected branch isolation and common-source lineage hold
**And** the conclusion remains limited to software and transport-path
independence.

**Given** valid, invalid, failed, and unfavorable OPC comparison runs
**When** G4 evidence is published
**Then** immutable manifests retain inputs, outputs, diagnostics, parameters,
code, runtime, transport evidence, causal tests, outcomes, and limitations
**And** reconstruction requires neither an optional dashboard nor mutable hidden
state.

**Given** all G4 checks complete
**When** the gate decision is issued
**Then** any failure keeps independent OPC v2 in shadow with a specific blocking
reason
**And** passing G4 authorizes no default activation, experiment execution,
detector training, syscall capture, fusion, deployment, control action, or UI
work.

## Implementation plan

- [ ] Confirm every upstream artifact, schema, parameter, authorization, and code/runtime identity required by the acceptance criteria exists at its exact version and hash. Complete the prior story in Epic 12 before starting this work; never synthesize its planned outputs.
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

- Canonical acceptance criteria: [_bmad-output/planning-artifacts/epics.md](../planning-artifacts/epics.md), Story 12.6.
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