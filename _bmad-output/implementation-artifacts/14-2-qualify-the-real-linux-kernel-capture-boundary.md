# Story 14.2: Qualify the Real Linux Kernel Capture Boundary

Status: done

## Story

### Story 14.2: Qualify the Real Linux Kernel Capture Boundary
**FRs implemented:** FR79.

As a laboratory operator,
I want the candidate Sysdig, eBPF, or equivalent capture boundary measured,
So that formal syscall evidence comes from a Linux kernel with known attribution
and quality.

**Acceptance Criteria:**

**Given** the controlled workload on a candidate capture environment
**When** the capture spike is declared
**Then** it records host or VM, boot, kernel, architecture, container runtime,
collector and version, capture mode, filter, workload, buffer, queue,
compression, storage, resource, and parameter identities
**And** on Docker Desktop the observed kernel is identified as its Linux VM
kernel, never the Windows host kernel.

**Given** known workload actions and process identities
**When** the collector observes the kernel boundary
**Then** the spike measures workload attribution, event ordering, duplicates,
gaps, drops, queue behavior, storage lag, capture overhead, and raw-to-canonical
replay
**And** unrelated infrastructure events remain distinguishable from workload
evidence.

**Given** any loss, overhead, capacity, duration, filter, buffer, or acceptance
limit used by the spike
**When** parameter validation runs
**Then** it resolves to direct, derived, measured, or preregistered parameter
evidence applicable to the environment
**And** values are not copied from tool examples as universal defaults.

**Given** raw capture segments from the spike
**When** replay qualification runs
**Then** immutable segment bytes, hashes, collector identity, ordering evidence,
and canonical events remain traceable
**And** missing calls are never invented to make replay complete.

**Given** attribution, ordering, loss, overhead, or replay fails the declared
policy
**When** the boundary decision is issued
**Then** formal capture is assigned to an explicitly pinned Linux VM or host, or
the activity receives a blocked result
**And** Docker Desktop is not promoted through an undocumented workaround.

**Given** the capture spike completes
**When** its qualification record is published
**Then** the selected or rejected boundary, measurements, raw evidence,
parameters, limitations, and fallback decision are immutable and inspectable
**And** qualification does not itself authorize formal syscall capture.

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

### Amendment enforcement: capture origin

Every formal event must resolve one-to-one to immutable `RawCaptureSegment.v1` bytes from the qualified collector with `capture_origin=host_capture`, raw hash, event range/offset, kernel/boot, cgroup/process, workload, collector/filter, and code/runtime identity. Fixture replay, injected/generated/replayed event, parser-only trace, external dataset sequence, or unknown origin is `test_fixture`/ineligible and blocks G6. Unit tests must reject every listed origin and every missing/mismatched raw-provenance field.
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

- Canonical acceptance criteria: [_bmad-output/planning-artifacts/epics.md](../planning-artifacts/epics.md), Story 14.2.
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
