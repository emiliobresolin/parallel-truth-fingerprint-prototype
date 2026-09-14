# Story 14.3: Preserve Raw Capture and `SyscallEventBatch.v1`

Status: done

## Story

### Story 14.3: Preserve Raw Capture and `SyscallEventBatch.v1`
**FRs implemented:** FR79-FR80.

As a syscall evidence consumer,
I want authentic captured events preserved in a versioned categorical contract,
So that host behavior can be replayed without fabricating calls, time, or
quality.

**Acceptance Criteria:**

**Given** an authorized `host-capture` session on the qualified Linux boundary
**When** the collector closes a raw segment
**Then** append-only storage records segment URI and hash, byte and event counts,
capture start and end, collector and filter identity, host or VM, boot, kernel,
architecture, workload, container or cgroup, process scope, experiment, run,
edge, sequence, and correlation identities
**And** partial or failed segments remain explicit.

**Given** captured kernel events from one eligible segment
**When** `SyscallEventBatch.v1` is created
**Then** it preserves schema and capture mode, run, edge, boot, session,
container or cgroup, process and thread where applicable, categorical syscall
name and direction, ordered sequence and timestamps, kernel or ABI context,
collector and filter, gaps, drops, duplicates, queue evidence, and raw-segment
reference
**And** every event resolves to bytes actually captured from the declared
kernel boundary.

**Given** numeric syscall identifiers are available from a collector or source
ABI
**When** they are retained
**Then** they remain categorical identifiers bound to the exact kernel or ABI
context and canonical name mapping
**And** their numeric magnitude is never interpreted as a continuous physical
quantity.

**Given** batch serialization or transport
**When** forbidden-field and routing validation runs
**Then** truth, attack labels, scenario meaning, future intervals, physical
consensus fields, detector decisions, fusion outputs, and actuator commands are
rejected
**And** batches use the separate versioned `host/syscalls/v1` path rather than a
physical consensus topic.

**Given** bounded queues, backpressure, duplicates, gaps, drops, or storage lag
occur
**When** batches and segment manifests are finalized
**Then** the affected identities, counts, intervals, queue evidence, and declared
flag, exclusion, or abort outcome are preserved
**And** missing events are not synthesized or silently interpreted as normal.

**Given** `fixture-replay` input
**When** contract and transport tests execute
**Then** fixture provenance remains attached to every emitted batch
**And** the batch cannot enter a `host-capture` namespace, measured result, or
formal custom evaluation.

## Implementation plan

- [ ] Confirm every upstream artifact, schema, parameter, authorization, and code/runtime identity required by the acceptance criteria exists at its exact version and hash. Complete the prior story in Epic 14 before starting this work; never synthesize its planned outputs.
- [ ] Implement only the smallest pure contracts, validators, adapters, or command-line-facing functions needed by the canonical criteria, in the existing repository structure. Do not add a service, database, cloud component, control path, or UI dependency.
- [ ] Make all invalid, unavailable, unknown-version, and unauthorized paths explicit and reconstructible. Never substitute a legacy/default/latest value, cached output, fixture, or a successful alternative.
- [ ] Persist formal evidence atomically: publish immutable objects, verify read-back/hash/size, then publish the complete manifest/receipt. Leave incomplete/orphaned publication visible and non-successful.
- [ ] Add focused unittest coverage for canonical valid and invalid paths, version/schema rejection, authority/provenance failures, immutability, and every failure mode named in the criteria.
- [ ] Record only implementation facts in the Dev Agent Record. Do not claim scientific qualification or issue an activity authorization from this story.

## Amendment Acceptance Criteria

**Given** a syscall segment, batch, or G6 input
**When** it is considered formal custom evidence
**Then** every event range resolves to immutable raw bytes with `capture_origin=host_capture`, collector/filter, kernel/boot, cgroup/process/workload, and matching run identity
**And** replay, fixture, injection, generated/replayed sequence, external dataset bytes, unknown origin, or missing/overlapping/unmapped range is test-only/ineligible and blocks G6.

- [ ] Add negative `unittest` coverage for each prohibited origin and provenance break; prove a mixed valid-plus-fixture run cannot pass and no test-only sequence reaches `PTFP-Custom-v1`.
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

### Amendment enforcement: closed syscall origin

Add a closed capture-origin distinction: `host_capture` requires immutable raw-segment bytes/hash and may enter the formal path; every host-captured batch/event serializes `raw_segment_content_id`/hash and an exact ordered `raw_event_range` or canonical collector-record offset range that is within the segment, one-to-one, and reconstructible. Missing, overlapping, or unmapped ranges reject formal ingress. `fixture_replay` requires its own immutable test artifact identity/hash and is test-only; it cannot carry `host_capture`. Rewrapping, renumbering, or transporting a fixture must never convert it into formal custom syscall evidence.
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

- Canonical acceptance criteria: [_bmad-output/planning-artifacts/epics.md](../planning-artifacts/epics.md), Story 14.3.
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
