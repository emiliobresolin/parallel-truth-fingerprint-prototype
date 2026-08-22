---
type: sprint-change-proposal
date: 2026-08-22
status: completed-planning-correction
change_classification: major
delivery_path: direct-adjustment-with-normative-consolidation
approval_scope: planning-only
approved_by: Emilio
approved_at: 2026-08-22T14:15:07-03:00
implementation_authorized: false
dataset_acquisition_authorized: false
training_authorized: false
syscall_capture_authorized: false
experiment_execution_authorized: false
dashboard_activation_authorized: false
handoff_to:
  - product-manager
  - solution-architect
  - product-owner-scrum-master
  - research-owner
triggered_by:
  - implementation-readiness status NOT READY on 2026-08-22
  - PRD and architecture contract lag behind approved academic-veracity rules
  - incorrect authority linkage for the 25%-75% preregistered factors
  - incomplete evidence for the derived 8-16 mA representation
  - no formal mock-admission record for the custom physical signal emulator
  - conditional dashboard and dataset qualification inconsistencies
controlling_readiness_report:
  - _bmad-output/planning-artifacts/implementation-readiness-report-2026-08-22.md
post_correction_readiness_report: _bmad-output/planning-artifacts/implementation-readiness-report-2026-08-22-rerun.md
post_correction_readiness_result: READY
correction_application_status: complete
reference_archive:
  - docs/reference-archive/
---

# Sprint Change Proposal - Close the Academic-Veracity Readiness Blockers

## 1. Issue Summary

The 2026-08-22 implementation-readiness assessment found that the detailed
story package is complete and structurally sound, but the project cannot enter
implementation under one coherent scientific contract. The issue was exposed
by the combined review of Stories 9.3, 9.4, 10.4, 14.1, and 17B.1 rather than by
one failed implementation story.

The trigger combines two change types:

- a strengthened stakeholder requirement: every scientific mock and domain
  number must be necessary, authoritative, transferable, and materially linked
  to the final dataset comparison; and
- a correction of a prior planning mismatch: the epics contain this rule, but
  the controlling PRD and architecture do not yet define an implementable
  contract for it.

The story package received a Party Mode structural score of 8.7/10. The
implementation-readiness package received 6.0/10 with academic and architecture
vetoes. This proposal corrects the vetoes without adding product UI, a new
service, a new database, or a new scientific claim.

## 2. Evidence Supporting the Change

### 2.1 Readiness evidence

The controlling readiness report records three blocking findings:

1. PRD FR76/NFR39 and architecture `ParameterEvidence.v1` omit the complete
   authentic-reproduction, official-authority, transferability, component,
   research-question, evidence-track, and final-result linkage required by the
   approved stories.
2. The parameter ledger treats 25% and 75% as researcher-selected factors but
   points their `source_id` at Danfoss, conflating decision authority with
   manufacturer evidence. The 8 mA and 16 mA derivations also lacked an exact
   selected command-profile locator.
3. The repository has no approved mock-admission record for the simulator that
   would generate the custom physical stream used in the dissertation's paired
   physical/syscall/fusion comparison.

The same report also found a fragmented PRD, conditional external-dataset
qualification work, and optional-dashboard wording conflicts. These do not
require additional scientific epics, but they should be corrected before the
next readiness run.

### 2.2 Repository evidence

The current brownfield simulator contains anonymous legacy values that cannot
be promoted into formal v2 merely because the demo already uses them:

| Legacy group | Current examples | Formal treatment |
| --- | --- | --- |
| Engineering ranges | 48-95 degC, 1.8-8.5 bar, 1200-4200 rpm | Quarantine as `legacy_only`; do not source-retrofit or migrate automatically |
| Behavior mixture | 0.55/0.45, 0.72/0.28, 0.88/0.12 | Quarantine; no compressor-physics claim |
| Oscillation and lag | periods 8.5/6/4/5/3.5, phases 0.1/0.2/0.4/0.7, offsets 8/6/1.8/0.15/45 | Quarantine; replace only through direct, derived, measured, preregistered, or admitted-mock records |
| Noise | base 0.15, multiplier 0.85, sensor multipliers 5/0.35/60 | Quarantine; no universal noise model exists |
| Secondary variables | fixed coefficients, offsets, and 20-75/20-55 degC clamps | Quarantine or remove from formal v2 |
| Comparison | 2 degC, 0.35 bar, 120 rpm | Quarantine; future tolerance must be measured or preregistered |
| Consensus | scales 20/3/600 and thresholds 0.35/0.75 | Quarantine; future policy must be measured or preregistered |

These values may remain available for exact v1 reproduction with a visible
legacy limitation. They cannot affect a formal v2 run, dataset, table, or claim.

### 2.3 New official-source finding

The official Danfoss CDS 803 Programming Guide closes the missing electrical
mapping evidence:

- parameter 6-12 is Terminal 53 Low Current, default 4 mA;
- parameter 6-13 is Terminal 53 High Current, default 20 mA;
- parameter 6-14 is the low reference/feedback value corresponding to 6-12;
- parameter 6-15 is the high reference/feedback value corresponding to 6-13.

Exact locator: Danfoss `AU356039245821en-000201 / 130R0597`, printed p. 54,
Tables 60-63, Parameter Group 6-1, available from the
[official Danfoss PDF](https://assets.danfoss.com/documents/273384/AU356039245821en-000201.pdf).

This source proves that a selected profile can configure 4 mA and 20 mA as the
low and high references. It does not make 25% or 75% manufacturer values. Once
the project freezes 6-14 as 0 and 6-15 as 100 for its declared mock profile,
25% and 75% remain preregistered research factors and 8 mA and 16 mA become
transparent derived representations.

Additional official instrument evidence supports a minimal formal profile:

- Siemens SITRANS TH320 FI 01 2025, PDF p. 4, option D73, identifies a Pt100
  0-100 degC four-wire configuration with 4-20 mA output. [Official Siemens
  temperature PDF](https://cache.industry.siemens.com/dl/files/161/109765161/att_1324085/v1/sitranst_th320_th420_fi01_es.pdf)
- Siemens SITRANS P200 FI 01 2025, selection table p. 1/7, lists a 0-10 bar
  gauge-pressure version and a 4-20 mA two-wire output. [Official Siemens
  pressure PDF](https://support.industry.siemens.com/cs/attachments/109765047/sitransp_p200_p210_p220_fi01_fr.pdf)
- Electro-Sensors FB420 ES730 Rev I, PDF pp. 1-2, specifies a directly
  proportional 4-20 mA shaft-speed output with user-programmable minimum and
  maximum RPM endpoints. [Official FB420 page](https://www.electro-sensors.com/products/shaft-speed-sensors/fb420)
- NIST IR 8089, PDF p. 8 (document p. 1), supports bounded testbeds that emulate
  real systems without replicating an entire plant; PDF p. 54 (document p. 47)
  limits conclusions to the represented model and purpose. [Official NIST
  publication](https://csrc.nist.gov/pubs/ir/8089/final)
- The DOE Compressed Air Sourcebook, section 5 and Figure 2.8, supports only
  qualitative variable-speed/capacity limitations and design dependence. It is
  not authority for one universal pressure, temperature, RPM, noise, lag, or
  efficiency curve. [Official DOE sourcebook](https://www.energy.gov/sites/prod/files/2016/03/f30/Improving%20Compressed%20Air%20Sourcebook%20version%203.pdf)

The new Danfoss and Siemens pressure PDFs must be archived with byte size,
SHA-256, retrieval date, and stable source IDs before their values can pass the
formal parameter gate. The proposal cites them for planning; it does not claim
that acquisition is already complete.

## 3. Impact Analysis

### 3.1 Epic impact

| Epic | Impact | Required action |
| --- | --- | --- |
| 9 | Global contracts and gates are incomplete in upstream artifacts. | Keep the epic; align Stories 9.3/9.4 terminology with the final PRD/architecture contracts. |
| 10 | Instrument profiles and 25%-75%/8-16 mA mapping need exact source and decision separation. | Keep the epic; add the Danfoss parameter locator and formal mock-profile boundary to Stories 10.1/10.4. |
| 11-13 | Consume numeric and profile contracts. | No scope change; they remain blocked by G1 until records validate. |
| 14 | “The workload may be mocked” is too permissive when the workload behavior is directly reproducible. | Keep the epic; make authentic controlled workload the default and mock only an exceptional capability-gap path. |
| 15A-16 | External datasets require actual version/layout/license/hash qualification. | No scope change; existing honest blocked states remain correct. |
| 17A-17B | Final custom ablation and publication package consume mock/relevance records. | No new story; preserve the complete records in final admission and claim index. |
| 18 | Dashboard wording conflicts across PRD, architecture, and UX. | Keep optional and terminal; distinguish live demo from frozen evidence mode only if activated. |

No epic is obsolete. No new epic is required. The order remains Epic 9 first,
then the independent producer/evaluator tracks, with optional Epic 18 last.

### 3.2 Story impact

The stories remain the correct size and structure. Only bounded consistency
edits are required:

- Story 9.3: distinguish official source authority from decision authority.
- Story 9.4: bind `ParameterEvidence.v1` to `DecisionRecord.v1` and
  `MockAdmission.v1` where applicable.
- Story 10.1: name the exact selected temperature, pressure, RPM, and command
  profile sources; unresolved endpoint choices remain blocked.
- Story 10.4: bind 25%/75% to a preregistration decision and 8/16 mA to the
  Danfoss 6-12 through 6-15 mapping plus a deterministic derivation.
- Story 14.1: replace permissive general mock wording with authentic controlled
  execution by default and an exceptional, fully admitted mock branch.
- Story 17B.1: preserve the three contract identities and all limitations in
  final evidence admission.
- Stories 18.1/18.4: apply only if Epic 18 is activated; evidence mode reads an
  exact `G9_PASS` package and rejects mutations server-side.

### 3.3 PRD conflicts

The controlling PRD overlay is incomplete in four places:

- FR76 lacks the full evidence/relevance/mock-admission fields.
- NFR39 does not make the class-specific authority rules explicit.
- FR79 permits a mocked workload without stating that reproducible behavior
  must remain authentic.
- FR93 uses mandatory wording even though Epic 18 is optional and non-blocking.

The PRD is also fragmented because FR30-FR71 and NFR22-NFR37 depend on
historical normative prose. A consolidated `prd.md` should become the sole
current normative PRD, while dated overlays remain historical traceability.

### 3.4 Architecture conflicts

The current architecture has one incomplete `ParameterEvidence.v1` row and no
owner contract for a preregistration decision or mock admission. It also states
the 8-16 mA mapping without the exact programming-guide locator and uses broad
“control or mock the workload” wording.

The correction affects flat evidence contracts, validators, gates, and
manifests only. It does not require a workflow service, authorization server,
database migration, frontend framework, or additional infrastructure.

### 3.5 UX impact

UX is not a scientific readiness gate. If Epic 18 is never activated, no UX
work is required. If it is activated, the specification must name two distinct
presentation states:

- `legacy_demo`: may show current/live prototype activity with a persistent
  “DEMO - NOT PUBLISHED SCIENTIFIC EVIDENCE” status; and
- `frozen_evidence`: reads only an explicitly selected immutable `G9_PASS`
  package and exposes no control route.

Visual styling remains advisory and optional.

### 3.6 Secondary artifact impact

- `docs/reference-archive/catalog/index.md`: add the Danfoss programming guide
  and Siemens P200 source identities and exact locators.
- `docs/reference-archive/catalog/checksums.sha256`: add hashes only after exact
  official bytes are archived.
- `docs/reference-archive/catalog/parameter-evidence.csv`: repair decision and
  derivation authority; do not approve unresolved RPM endpoints or simulator
  dynamics.
- Add flat, versioned planning records for the preregistration decision, the
  signal-emulator mock admission, and the legacy-constant quarantine inventory.
- `sprint-status.yaml`: N/A because no epic or story is added, removed,
  renumbered, or moved.
- Code, tests, runtime configuration, datasets, and deployment artifacts: no
  mutation is authorized by this proposal.

## 4. Path Forward Evaluation

### Option 1 - Direct adjustment

**Viable.** Correct the existing PRD, architecture, source/parameter records,
and limited story wording. Preserve all 12 epics and 81 stories.

- Planning effort: medium
- Implementation effort impact: low to medium, mainly validators and contracts
- Scientific risk after correction: low to medium
- Scope impact: no additional product feature

### Option 2 - Rollback

**Not viable.** Formal Epics 9-18 have not been implemented, so there is no v2
work to roll back. Reverting the strengthened stories would recreate the
academic-validity problem.

- Effort: low
- Scientific risk: critical

### Option 3 - Reduce the MVP or dissertation claim

**Not required as the primary path.** The current claim is already bounded to
whether calibrated late fusion improves the physical/syscall trade-off on the
synchronized custom campaign. External datasets remain context, not pooled
evidence. Reducing this further would not fix the missing evidence contracts.

- Effort: medium
- Benefit: limited
- Scientific risk: medium because it may weaken the intended comparison without
  resolving provenance

### Recommended approach

Use **Option 1: Direct adjustment with normative consolidation**.

This is the smallest change that can produce `READY`. It keeps the academic
prototype focused, preserves the approved stories, and prevents unsupported
legacy constants or convenient mocks from entering formal evidence.

## 5. Detailed Change Proposals

### 5.1 PRD FR76 - parameter provenance and research relevance

**Current:**

> Every executable v2 numeric parameter has a stable ID, one classification,
> value, unit, source or decision ID, locator, derivation, profile, limitation,
> and experiment scope.

**Proposed:**

> Every executable v2 numeric parameter shall have a stable parameter ID and
> exactly one classification: `direct`, `derived`, `measured`,
> `preregistered_factor`, or `mock`. The record shall contain value, unit,
> class-specific authority, exact source/decision/calibration/mock-admission
> locator, derivation and input IDs where applicable, selected profile,
> experiment scope, approval identity, uncertainty/limitation, authentic
> reproduction feasibility, exact prototype component, bounded research
> question, dataset/modality track, affected final package element, and an
> explicit transferability rationale. A domain claim shall fail closed when its
> official authority is missing, inapplicable, or unable to support the exact
> use. A preregistered factor shall use its frozen decision as value authority;
> official sources establish only applicable capability or constraint. A mock
> shall additionally reference an approved immutable `MockAdmission.v1`.

**Rationale:** Implements the already approved story rule without pretending
that a manufacturer selected the researcher's experimental factors.

### 5.2 PRD NFR39 - class-specific accountability

**Current:**

> Formal v2 rejects any executable numeric parameter lacking the complete FR76
> record; a citation alone does not establish transferability.

**Proposed:**

> Formal v2 startup, experiment freeze, and final evidence admission shall
> reject every executable numeric parameter whose complete FR76 record or
> class-specific authority cannot be resolved. `direct` uses applicable official
> authority; `derived` uses validated inputs and deterministic dimensional
> derivation; `measured` uses preserved calibration/pilot evidence;
> `preregistered_factor` uses a pre-test frozen decision and separately
> documented feasibility constraints; `mock` uses an approved capability-gap
> admission plus official support for every asserted domain behavior and
> number. No class may be silently promoted into another.

**Rationale:** Gives an implementer one deterministic validation rule.

### 5.3 PRD FR79 - controlled workload authenticity

**Current:**

> The workload may be mocked; the syscalls themselves shall not be fabricated
> or modified.

**Proposed:**

> The custom syscall track shall execute an allowlisted controlled Linux edge
> workload and capture the authentic kernel calls it actually emits. Every
> workload behavior that the approved prototype can reproduce shall execute
> authentically. Only a specifically unavailable behavior may use a mock after
> an approved `MockAdmission.v1`; convenience, cost, timing, or an unfavorable
> result is insufficient. The emitted syscalls shall never be fabricated,
> renumbered, modified, or substituted.

**Rationale:** Aligns the PRD with Linux/Sysdig feasibility and Story 14.1.

### 5.4 PRD FR93 - optional dashboard

**Current:**

> The dashboard shall display evidence and shall not mutate scientific results.

**Proposed:**

> **Conditional/optional.** If Epic 18 is separately activated, the existing
> dashboard may present either visibly non-scientific live demo state or an
> explicitly selected immutable `G9_PASS` evidence package. Frozen-evidence
> mode shall expose no mutation route and shall reject mutation requests
> server-side. Dashboard absence, styling, or disagreement shall not block or
> alter scientific Epics 9-17B, evidence, control, evaluation, or publication.

**Rationale:** Preserves the requested simple “show it happening” dashboard
without making UI/UX mandatory.

### 5.5 Architecture - evidence contracts

**Current:**

> `ParameterEvidence.v1`: ID, value, unit, class, source/decision locator,
> derivation, profile, and experiment scope.

**Proposed authoritative contracts:**

| Contract | Required content | Owner | Fail-closed condition |
| --- | --- | --- | --- |
| `DecisionRecord.v1` | decision ID, values/factors, rationale, question, scope, owner, approval, freeze time, truth/test lock state, source constraints | Research owner | post-test, mutable, unapproved, or scope-mismatched decision |
| `MockAdmission.v1` | mock ID, capability gap, attempted/unavailable authentic path, official sources and exact locators, supported behavior/numbers, transfer rationale, component, question, track, final output, limitations, replacement condition, owner/approval | Research owner plus architecture validator | reproducible authentic path, absent/inapplicable authority, weak transfer, missing result linkage, or real-plant claim |
| `ParameterEvidence.v1` | stable ID, value/unit/class, class authority reference, exact locator, derivation/input IDs, profile/experiment scope, approval, uncertainty/limitation, authentic feasibility, component/question/track/final-output linkage, transfer rationale | Source/parameter registry | incomplete, conflicting, circular, dimensionally invalid, non-transferable, or unresolved record |

All remain flat deterministic artifacts. No service is added.

### 5.6 Architecture - reference mapping

**Current:**

> Under a separately declared linear 0%-100%, 4-20 mA command profile,
> 25%-75% derives to 8-16 mA.

**Proposed:**

> `InstrumentProfile.v1` for the simulated CDS 803 command input shall bind
> Danfoss AU356039245821en-000201, printed p. 54, Tables 60-63: 6-12=4 mA,
> 6-13=20 mA, 6-14=0 reference units, and 6-15=100 reference units. The 0 and
> 100 configuration is an explicitly selected mock-profile configuration, not a
> universal default. `DecisionRecord.v1` authorizes 25 and 75 as
> `preregistered_factor`; `ParameterEvidence.v1` derives 8 and 16 mA from the
> frozen profile. Ramp, dwell, settling, repetition, and safety remain separate
> records.

**Rationale:** Closes the exact locator and authority gap.

### 5.7 Architecture - bounded signal emulator

Add `MockAdmission.v1` named `mock-admission-ptfp-signal-emulator-v1` with this
planning content:

- capability gap: the approved prototype contains no physical compressor,
  temperature/pressure/RPM instruments, drive, DAQ hardware, or real-plant data
  acquisition path;
- unavailable authentic evidence: simultaneous real compressor measurements
  cannot be produced inside the approved software-only academic boundary;
- purpose: produce controlled synthetic physical observations for
  `PTFP-Custom-v1` and the paired physical/syscall/fusion ablation;
- exact component: custom current-domain signal emulator and instrument-profile
  conversion path;
- bounded research question: whether frozen calibrated late fusion improves
  detection quality or operational trade-offs over either custom modality on
  the same runs;
- final outputs: custom dataset manifest, physical result table, syscall result
  table, paired ablation table, capability/limitation matrix, and claim index;
- official support: NIST IR 8089 testbed boundary, Rockwell current scaling,
  Danfoss CDS 803 reference mapping, Siemens TH320 temperature profile,
  Siemens P200 pressure profile, FB420 RPM profile, and DOE qualitative
  compressor limitations;
- prohibited claims: real plant, validated compressor dynamics, digital twin,
  safety/energy performance, manufacturer-endorsed operating range, or external
  validation;
- replacement condition: qualified real hardware and preserved calibration/
  acquisition evidence becomes available under a newly approved scope.

Only official/source-backed device/profile numbers, derived values, measured
values, and frozen preregistered factors may enter this mock. All anonymous
legacy dynamics, noise, bias, tolerance, and threshold constants remain
formal-disabled until separately resolved. The emulator may use a simpler
scripted signal design; realism is not increased by unsupported equations.

### 5.8 Source and parameter ledger

After proposal approval:

1. Add stable source IDs for the Danfoss programming guide and Siemens P200.
2. Archive the exact official bytes if retrieval succeeds; otherwise retain an
   explicit link-only/pending status and keep dependent parameters blocked.
3. Create `decision-custom-reference-window-v1` for 25% and 75%, with Emilio as
   decision owner and the final paired ablation as the affected result.
4. Replace the Danfoss `source_id` on the 25%/75% rows with that decision ID.
5. Bind 8/16 mA to the Danfoss source, selected command profile, 25%/75% input
   parameter IDs, and deterministic formula.
6. Add or propose the 0-100 degC TH320 and 0-10 bar P200 profile endpoints with
   their exact official locators.
7. Keep RPM engineering endpoints unresolved until a user-min/user-max profile
   decision is frozen within the FB420 documented capability.
8. Create a complete legacy-constant quarantine inventory. Do not invent source
   records for old values.

### 5.9 Epics and stories

Apply only the wording needed to reference the authoritative contracts and
sources above. Do not add stories, acceptance scenarios, UI requirements, or
implementation scope. The Cross-Epic Mock Admission Guardrail remains
controlling.

### 5.10 UX specification

If retained as a current planning artifact, amend it to state that live/current
state is `legacy_demo`, never the identity of a scientific result. A selected
frozen package is the only `frozen_evidence` source. All palette, layout,
responsive, and accessibility suggestions remain optional guidance.

## 6. Recommended Sequencing

1. Approve this planning-only proposal.
2. Consolidate PRD requirements and apply FR76/NFR39/FR79/FR93 corrections.
3. Consolidate architecture and add the three evidence contracts, ownership,
   validators, gates, and exact mapping locator.
4. Repair the source catalog, parameter ledger, decision record, mock admission,
   and legacy quarantine inventory.
5. Apply bounded consistency edits to epics and optional UX.
6. Run Party Mode adversarial review over the corrected artifact set.
7. Re-run Check Implementation Readiness.
8. Enter Sprint Planning only if the new report says `READY`.

No implementation, acquisition, training, capture, experiment, dashboard
activation, or deployment occurs in steps 1-7.

## 7. Effort, Risk, and Timeline Impact

### Effort

- Planning/document correction: medium
- New source verification: low to medium
- Epic/story change: low
- UI/UX change: none unless optional Epic 18 is activated
- Runtime/code change authorized now: none

### Risks and mitigations

| Risk | Level | Mitigation |
| --- | --- | --- |
| Treating preregistered factors as manufacturer values | High | Separate `DecisionRecord.v1` from official capability sources |
| Overstating mock compressor realism | High | Rename the formal boundary as a controlled signal emulator and attach explicit prohibited claims |
| Reintroducing legacy constants | High | Machine-readable quarantine plus fail-closed G1 validation |
| Source URL changes | Medium | Archive exact bytes and SHA-256; use stable document number/version |
| Pressure/RPM endpoint overgeneralization | Medium | Bind exact device variant/profile and keep unresolved choices blocked |
| Additional UI scope | Low | Epic 18 remains optional, terminal, and non-blocking |
| Delayed implementation start | Medium | Intentional; avoids implementing an academically invalid contract |

The correction adds a documentation and evidence review cycle before sprint
planning. It does not expand the prototype into a production product.

## 8. Implementation Handoff

### Change scope

**Major planning correction.** The project goal and epic structure remain, but
the PRD and architecture require coordinated normative updates. Route to the
Product Manager and Solution Architect, with the Product Owner/Scrum Master and
research owner maintaining traceability.

### Responsibilities

- Product Manager: consolidate the PRD and own FR76/NFR39/FR79/FR93 wording.
- Solution Architect: own the evidence contracts, validators, fail-closed gates,
  mock boundary, and exact profile/source bindings.
- Product Owner/Scrum Master: apply bounded epic/story consistency changes and
  preserve ordering/coverage.
- Research owner: approve the preregistration decision, mock admission scope,
  source transfer rationale, and prohibited claims.
- UX owner: act only if Epic 18 is activated; preserve optionality.
- Development team: receive no implementation handoff until readiness is
  `READY` and a later activity authorization exists.

### Success criteria

The correction is complete only when:

- one self-contained controlling PRD defines all 93 FRs and 52 NFRs;
- one controlling architecture implements every strengthened evidence field and
  validation owner;
- 25%/75% use a frozen decision as value authority;
- 8/16 mA resolve through the exact Danfoss 6-12 through 6-15 profile and
  deterministic derivation;
- the formal signal emulator has a complete mock admission and prohibited-claim
  boundary;
- all current anonymous simulator, comparison, consensus, and detector constants
  are either resolved or explicitly formal-disabled/legacy-only;
- authentic workload/syscall requirements are unambiguous;
- external dataset qualifications remain fail-closed and non-substitutable;
- optional dashboard language is consistent across PRD, architecture, epics,
  and UX;
- Party Mode finds no score below 7 and no veto; and
- a fresh implementation-readiness workflow returns `READY`.

## 9. Change Navigation Checklist

| Item | Status | Finding |
| --- | --- | --- |
| 1.1 Triggering story | [N/A] | Cross-artifact readiness review; Stories 9.3/9.4/10.4/14.1/17B.1 exposed the mismatch collectively. |
| 1.2 Core problem | [x] | Strengthened academic requirement is absent from upstream implementable contracts. |
| 1.3 Evidence | [x] | Readiness report, repository constants, official documents, and parameter ledger inspected. |
| 2.1 Current epic viability | [x] | Epic 9 remains viable after contract alignment. |
| 2.2 Epic-level changes | [x] | Bounded wording only; no new epic. |
| 2.3 Remaining epics | [x] | Consumers remain valid and fail closed on G1. |
| 2.4 Obsolete/new epics | [N/A] | None obsolete; none required. |
| 2.5 Order/priority | [x] | Existing order retained; Epic 9 remains prerequisite. |
| 3.1 PRD | [x] | Approved: consolidate and amend FR76/NFR39/FR79/FR93. |
| 3.2 Architecture | [x] | Approved: add complete contracts, ownership, gates, source/profile mapping, and mock admission. |
| 3.3 UX | [x] | Approved: conditional wording only if Epic 18 is retained/activated. |
| 3.4 Other artifacts | [x] | Approved: repair source/parameter ledgers; add decision/mock/quarantine records. |
| 4.1 Direct adjustment | [x] Viable | Medium effort; lowest scientific risk. |
| 4.2 Rollback | [N/A] Not viable | No formal v2 implementation to roll back; would weaken validity. |
| 4.3 MVP review | [x] | Claim already bounded; no additional scope reduction required. |
| 4.4 Selected path | [x] | Direct adjustment with normative consolidation. |
| 5.1 Issue summary | [x] | Sections 1-2. |
| 5.2 Impact | [x] | Section 3. |
| 5.3 Recommended path | [x] | Section 4. |
| 5.4 MVP/action plan | [x] | Sections 5-7. |
| 5.5 Handoff | [x] | Section 8. |
| 6.1 Checklist review | [x] | All applicable analysis items addressed. |
| 6.2 Proposal accuracy | [x] | Checked against controlling readiness report and exact source locators. |
| 6.3 User approval | [x] | Emilio explicitly approved the complete batch proposal on 2026-08-22. Approval is planning-only under Section 11. |
| 6.4 Sprint status | [N/A] | No epic/story add, removal, renumbering, or move. |
| 6.5 Next steps | [x] | Route the approved planning correction to PM, Architect, PO/SM, and research-owner responsibilities; implementation remains blocked until a fresh readiness result is `READY`. |

## 10. Party Mode Review

### John - academic value and focus: 9/10

The correction strengthens the only defensible final claim and removes
unsupported compressor realism. The new sources directly support the selected
instrument and command profiles. No UI or unrelated metric expansion was added.

### Winston - necessity and architecture simplicity: 9/10

Three flat records and deterministic validators are sufficient. No service,
database, workflow engine, or frontend migration is introduced. The mock is
explicitly bounded to the missing hardware capability.

### Bob - scope and testability: 9/10

Every correction has a fail-closed acceptance condition, owner, locator, and
handoff. Legacy values have one unambiguous disposition. The existing stories
remain implementable after upstream alignment.

**Average: 9.0/10. No score below 7. No veto. Party Mode recommends approval.**

Party Mode approval does not replace the explicit user approval required by the
Correct Course workflow.

## 11. Approval Boundary

Approval of this proposal authorizes only edits to planning documents and
source/evidence catalogs needed to close the readiness findings. It does not
authorize:

- application code or runtime configuration changes;
- dataset or model artifact acquisition beyond explicit source-document
  archival required for planning evidence;
- model training, calibration, evaluation, or promotion;
- Linux workload execution or syscall capture;
- simulator or experiment execution;
- dashboard activation;
- deployment, external communication, or publication.

After approval, the artifact corrections will be applied and reviewed in batch.
The project will then repeat implementation readiness. Sprint Planning remains
blocked until that result is `READY`.

## 12. Correction Application and Final Handoff

**Application status: COMPLETE.** The approved planning-only correction was
applied to the controlling PRD, architecture, epics/stories, optional UX
specification, and official-source/evidence catalog. No application code,
runtime configuration, dataset execution, model training, syscall capture,
experiment, dashboard activation, deployment, or publication was authorized or
performed.

The post-correction implementation-readiness report is
`_bmad-output/planning-artifacts/implementation-readiness-report-2026-08-22-rerun.md`.
It completed all six workflow steps on 2026-08-22 and returned **READY** with:

- 93/93 FR coverage;
- 0 critical violations;
- 0 major issues;
- aligned optional UX/presentation boundaries;
- complete story/dependency validation; and
- explicit fail-closed execution gates for the pending P200 archive and
  unresolved FB420 RPM endpoints.

The Correct Course success criteria are therefore satisfied. Sprint Planning
is unblocked as the next BMAD planning workflow, while implementation and every
scientific activity remain subject to their separate authorization boundaries.
