# Story 14.1: Define an Allowlisted Linux Edge Workload

Status: done

## Story

### Story 14.1: Define an Allowlisted Linux Edge Workload
**FRs implemented:** FR79.

As a security researcher,
I want a pinned and attributable Linux edge workload for the prototype,
So that later kernel events can be tied to declared edge behavior rather than
unrelated infrastructure.

**Acceptance Criteria:**

**Given** a controlled workload profile
**When** its manifest is registered
**Then** it records image or executable identity, entrypoint, expected process
tree, edge and experiment roles, permissions, network and storage interactions,
configuration hash, code and dependency identity, applicable mock-admission
identity, and allowed activity scope
**And** secret values and unrelated host services remain outside the manifest.

**Given** the academic prototype functions assigned to the workload
**When** it executes normally
**Then** it performs only declared safe acquisition, serialization, MQTT,
consensus interaction, evidence-write, and approved deviation activities
**And** it does not generate arbitrary attack tooling or gain analytics-to-control
authority.

**Given** a declared workload behavior
**When** its execution path is selected
**Then** authentic allowlisted Linux execution is the default whenever the
approved prototype can reproduce the behavior
**And** only a specifically unavailable behavior may use an immutable approved
`MockAdmission.v1` whose exact official locators support its bounded behavior,
constraints, and every domain numeric value.

**Given** the prototype can directly reproduce the required workload behavior,
official documentation is missing or inapplicable, or authentic behavior merely
produces an unfavorable result
**When** a mocked workload is requested
**Then** the mock is rejected and the authentic path remains authoritative
**And** planning approval cannot waive the cross-epic mock-admission guardrail.

**Given** the workload process tree starts
**When** runtime identity is recorded
**Then** host or VM, boot, container, cgroup, process, thread where applicable,
kernel, architecture, edge, experiment, run, and correlation identities are
preserved
**And** Mosquitto, MinIO, CometBFT, ABCI, collector, and unrelated container
processes are excluded from the workload's evidence scope.

**Given** a proposed workload activity falls outside the allowlist or approved
experiment scope
**When** startup validation runs
**Then** that workload execution is blocked with an explicit reason
**And** no expanded privilege or activity is inferred from planning approval.

**Given** a fixture or recorded syscall sample is used for contract testing
**When** its workload role is assigned
**Then** it is explicitly marked `fixture-replay` and test-only
**And** it cannot be represented as host-captured evidence or admitted to formal
custom evaluation.

## Implementation plan

- [ ] Confirm every upstream artifact, schema, parameter, authorization, and code/runtime identity required by the acceptance criteria exists at its exact version and hash. Use only the exact immutable prerequisites named in the canonical acceptance criteria; absence is an explicit blocked state.
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

- Canonical acceptance criteria: [_bmad-output/planning-artifacts/epics.md](../planning-artifacts/epics.md), Story 14.1.
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
