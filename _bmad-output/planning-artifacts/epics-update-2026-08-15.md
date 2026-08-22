---
type: epics-and-stories-overlay
date: 2026-08-15
status: planning-overlay-under-approved-change
project: parallel-truth-fingerprint-prototype
change_authority: _bmad-output/planning-artifacts/sprint-change-proposal-2026-08-15.md
requirements_authority: _bmad-output/planning-artifacts/prd-update-2026-08-15.md
architecture_authority: _bmad-output/planning-artifacts/architecture-update-2026-08-15.md
controlling_research: _bmad-output/planning-artifacts/research/technical-scientifically-grounded-industrial-signal-and-anomaly-simulation-research-2026-08-15.md
reference_archive: docs/reference-archive/
preserves_history:
  - _bmad-output/planning-artifacts/epics.md
  - _bmad-output/planning-artifacts/epics-update-2026-05-21.md
supersedes_unimplemented_plan:
  - _bmad-output/planning-artifacts/epics-update-2026-07-30.md
requirements_covered:
  functional: FR72-FR93
  non_functional: NFR38-NFR52
implementation_authorized: false
training_authorized: false
dataset_acquisition_authorized: false
syscall_capture_authorized: false
experiment_execution_authorized: false
---

# Epics and Stories Update — Evidence-Grounded Physical and Syscall Research

## 1. Purpose and Authority

This dated overlay replaces only the unimplemented July Epics 9–16. Historical
Epics 1–8 and their delivered artifacts remain intact as implementation history.
Their scientific status is amended by Section 4; no result, model, log, or prior
planning artifact is silently rewritten.

The overlay decomposes the formally approved Sprint Change Proposal into
implementation-ready stories. It is a planning artifact only. Its acceptance
does **not** authorize code changes, dependency or dataset downloads, model
training, syscall capture, campaign execution, promotion, or mutation of
existing evidence. A separate explicit implementation authorization is required
before any story may move from planned to in progress.

## 2. Non-Negotiable Product Semantics

- The project has exactly two detection modalities: physical instrumentation
  and Linux host syscalls.
- In the custom prototype, raw 4–20 mA current is the primary edge evidence for
  configured current-loop instruments. Normalized span and engineering units
  are derived representations of the same physical modality.
- HAI remains in its native published SCADA representation; it is not converted
  wholesale to mA and does not validate the compressor.
- ADFA-LD and LID-DS are external syscall benchmarks. Their records are not
  executed as project syscalls.
- `PTFP-Custom-v1` is the only dataset eligible for physical-plus-syscall fusion
  claims because its modalities are captured from the same correlated runs.
- An autoencoder is a model, not a dataset or a modality.
- Scenario truth and attack labels are evaluation-only evidence and are absent
  from detector training and inference contracts.
- LSTM and GRU are candidates to be compared fairly with declared baselines;
  no architecture is designated the winner before evaluation.
- Analytics and dashboards have no authority over the industrial control path.

## 3. Global Source and Parameter Guardrails

Every executable v2 number must resolve through a stable `parameter_id` to one
of these classifications:

- `direct`: stated by an authoritative source for the selected profile;
- `derived`: produced by a recorded formula over sourced inputs;
- `measured`: produced by a preserved pilot or calibration;
- `preregistered_factor`: deliberately selected and frozen before test access;
- `mock`: explicitly limited to a named simulator profile and never presented
  as a real-plant fact.

Each entry records its value, unit, classification, source or decision ID,
exact locator, derivation, applicable instrument or workload profile, and
approved experiment. Missing provenance is a validation error, not a defaulting
condition. Runtime, tests, examples, environment files, model bundles, and
dashboard defaults may not introduce an anonymous scientific constant.

The 25%–75% schedule is the sole pre-approved numeric experimental factor in
this overlay. It is recorded as `speed_reference_pct` or
`capacity_reference_pct`, never as electrical power or a universal compressor
operating range. All other schedule shape, dwell, ramp, repetition, window,
threshold, tolerance, and stopping values require their own admissible ledger
entry before implementation or execution.

Primary guardrail sources include:

- [Rockwell PointMax Analog I/O Manual](https://literature.rockwellautomation.com/idc/groups/literature/documents/um/5034-um003_-en-p.pdf)
  for electrical-to-engineering scaling examples;
- [NI current-loop scaling guidance](https://knowledge.ni.com/KnowledgeArticleDetails?id=kA00Z000000PASfSAO)
  for generic endpoint conversion;
- [Electro-Sensors FB420](https://www.electro-sensors.com/products/shaft-speed-sensors/fb420)
  as evidence that an RPM transmitter can use programmable 4–20 mA endpoints;
- [OPC UA `DataValue`](https://reference.opcfoundation.org/Core/Part4/v105/docs/7.11)
  for value, status, and timestamp semantics;
- [LID-DS Recording Framework](https://github.com/LID-DS/LID-DS/wiki/LID-DS-Recording-Framework%3A-Documentation-and-Installation)
  for the controlled Docker and Sysdig capture precedent;
- [official HAI repository](https://github.com/icsdataset/hai) for the versioned
  physical benchmark and its temporal evaluation guidance;
- [NIST AI RMF Measure](https://airc.nist.gov/airmf-resources/airmf/5-sec-core/)
  for documented test sets, metrics, uncertainty, comparison, and repeatable
  evaluation;
- the local [reference archive](../../docs/reference-archive/README.md) and
  parameter-evidence catalog for preserved copies, checksums, locators, and
  link-only restricted sources.

## 4. Historical Epics 1–8 Disposition

This table changes scientific and backlog status without deleting history.

| Historical stories | Disposition | Binding amendment |
|---|---|---|
| 1.1 | `RETAIN` | The architecture-driven local skeleton remains valid. |
| 1.2 and 1.6 | `AMEND` | Ranges, dynamics, and noise move to profile-scoped provenance; anonymous plausible values remain legacy-only. |
| 1.3 | `AMEND` | Acquisition must preserve `SignalObservation.v2`, with current as primary custom edge evidence. |
| 1.4 and 1.5 | `AMEND` | MQTT and visibility remain, using versioned envelopes, identity, sequence, and deduplication. |
| 2.1 and 2.2 | `AMEND` | Consensus declares an electrical comparison basis and instrument profile; Python and Go change atomically. |
| 2.3–2.5 | `RETAIN_AMEND` | Explicit failure handling remains and is adapted to v2 contracts. |
| 3.1 | `AMEND` | OPC UA receives a pre-consensus plant snapshot, not the consensus result. |
| 3.2–3.5 | `AMEND` | Comparison, persistence, and logs preserve status, timestamps, correlation, and coherent representations. |
| 4.1–4.4, including 4.2A | `LEGACY_BASELINE` | Existing dataset, model, threshold, and replay evidence remain inspectable but cannot support final claims. |
| 4.5 | `AMEND` | Scenarios are governed by `ExperimentSpec`; truth is isolated. |
| 4.6 | `AMEND` | The UI no longer owns or silently changes compressor reference generation. |
| 5.1–5.4 | `RETAIN_AMEND` | Presentation remains useful but becomes provenance-aware and read-only. |
| 6.1–6.5 | `LEGACY_BASELINE` | Readiness and replay outcomes remain exploratory evidence with explicit limitations. |
| 7.1–7.5 | `RETAIN_AMEND` | Reusable training and metric infrastructure must adopt group-safe splits, candidate fairness, and immutable evidence. |
| 7.6–7.9 | `AMEND` | ADFA-LD preserves trace identity, official roles, six attack families, and categorical syscall meaning. |
| 7.10–7.12 | `AMEND` | LID-DS uses its official layout, scenario groups, and release-specific environment. |
| 7.13 | `AMEND` | Reporting must not declare a global winner across incompatible domains. |
| 8.1 | `AMEND` | Promotion applies only to complete, compatible, immutable detector bundles. |
| 8.2 | `SUPERSEDE` | An ADFA/LID classifier cannot be promoted as a physical compressor detector. |
| 8.3 | `SUPERSEDE` | The current autoencoder is preserved as a baseline rather than deleted. |
| 8.4 | `AMEND` | External benchmark results remain separate from live physical runtime results. |
| July Epics 9–16 | `SUPERSEDE` | The unimplemented July roadmap is replaced by Epics 9–18 below. |

## 5. Requirements Coverage Map

The identifiers below follow the dated PRD overlay. Each FR has one primary
delivery epic; cross-cutting NFRs apply to every story that handles scientific
evidence.

| Requirement | Epic coverage | Coverage outcome |
|---|---:|---|
| FR72 | 10, 17, 18 | Two modalities and representation semantics govern acquisition, final comparison, and presentation. |
| FR73 | 10 | `SignalObservation.v2` preserves raw current at the custom edge boundary. |
| FR74 | 10 | Profile-based engineering derivation and internal process physics remain distinct. |
| FR75 | 10 | `ExperimentSpec` governs the preregistered 25%–75% reference factor. |
| FR76 | 9–11 | All executable parameters resolve to the provenance ledger and declared consumers. |
| FR77 | 10, 13–17 | Scenario truth is isolated from training, inference, capture, benchmarks, and fusion. |
| FR78 | 13, 16 | Physical LSTM-AE, GRU-AE, and baselines use one fair protocol on custom and HAI evidence. |
| FR79 | 14 | Controlled Linux edge workloads produce real kernel syscalls. |
| FR80 | 14 | `SyscallEventBatch.v1` preserves attribution, ordering, and capture loss. |
| FR81 | 14–15 | Categorical syscall candidates are compared fairly on custom and external evidence. |
| FR82 | 15 | ADFA-LD remains an external syscall benchmark with preserved trace identity. |
| FR83 | 15 | LID-DS 2021 remains an external benchmark and capture-method reference. |
| FR84 | 16 | HAI 23.05 remains a native external physical benchmark. |
| FR85 | 10, 14, 17 | Custom physical and syscall producers feed one synchronized locked dataset. |
| FR86 | 9, 13–17 | Complete groups are split before windows; preprocessing and threshold selection are isolated. |
| FR87 | 9, 13–17 | Detector deployment and evaluation artifacts form immutable atomic bundles. |
| FR88 | 9, 13–17 | Protocol-appropriate metrics and uncertainty are specified and reported completely. |
| FR89 | 17 | Late fusion is evaluated only on synchronized held-out custom runs. |
| FR90 | 12 | OPC UA becomes an independent pre-consensus laboratory boundary. |
| FR91 | 11 | Consensus uses a declared current-domain basis with Python/Go parity. |
| FR92 | 17–18 | External benchmark tables and paired custom ablation remain distinct, traceable, and correctly presented. |
| FR93 | 18 | The dashboard is a read-only evidence presentation layer. |

| NFR | Primary enforcement | Covered by |
|---|---|---|
| NFR38 semantic accuracy | Contract schemas and dataset cards | 10, 14–18 |
| NFR39 numeric provenance | Parameter validation gate | 9–18 |
| NFR40 reproducibility and immutability | Manifests, bundles, hashes, reconstruction | 9, 13–17 |
| NFR41 leakage and truth isolation | Storage and access boundaries | 10, 13–17 |
| NFR42 local OT safety | No analytics-to-control authority | 10–14, 18 |
| NFR43 fair candidate comparison | Shared protocols and frozen inputs | 13–17 |
| NFR44 no universal thresholds | Validation-only calibration and provenance | 9, 13–17 |
| NFR45 syscall capture quality | Drop, gap, attribution, overhead evidence | 14, 17 |
| NFR46 temporal/correlation integrity | Identifiers, timestamps, group-safe joins | 10, 12–17 |
| NFR47 resource isolation and explicit failure | Bounded paths and fail-closed consumers | 9, 12–18 |
| NFR48 versioned compatibility | Versioned schemas, adapters, and migration flags | 9–18 |
| NFR49 durable evidence storage | Persistent append-only verified artifacts | 9, 14–17 |
| NFR50 end-to-end traceability | Claim, source, manifest, score, and result linkage | 9–18 |
| NFR51 complete scientific reporting | Preserve failures and unfavorable outcomes | 13–17 |
| NFR52 planning-only authorization | Explicit state and workflow checks | 9–18 |

## 6. Epic Sequence and Gate Dependencies

```text
Epic 9
  |
Epic 10
  |-- Epic 11 --+
  |-- Epic 12 --+-- Epic 13 --+
  +-- Epic 14 ----------------+
Epic 15 ----------------------+--> Epic 17 --> Epic 18 (optional)
Epic 16 ----------------------+
```

The gates are evidence gates, not calendar milestones:

| Gate | Required outcome | Unlocks after separate implementation authority |
|---|---|---|
| G0 Planning Approved | Proposal and dated overlays are approved. | Implementation authorization decision only. |
| G1 Provenance Ready | Sources, parameter ledger, hashes, storage recovery, and v1 fixtures are complete. | Candidate v2 implementation. |
| G2 Signal v2 Valid | Conversion, quality, profile, and timestamp semantics survive end to end. | Current-domain consumers. |
| G3 Consensus v2 Valid | Python/Go results are deterministically equivalent and fully sourced. | Active consensus candidate. |
| G4 Independent SCADA Valid | Real protocol round trip and causal independence pass. | Valid independent SCADA evidence. |
| G5 Physical Bundle Frozen | Bundle replay is deterministic and inference performs no fit. | Shadow physical inference. |
| G6 Syscall Capture Qualified | Events are real, attributable, and accompanied by loss/overhead evidence. | Custom syscall evidence. |
| G7 External Benchmarks Qualified | ADFA-LD, LID-DS, and HAI sources, roles, splits, and licenses resolve. | External result tables. |
| G8 PTFP-Custom Locked | Synchronized runs and partitions are immutable and truth remains isolated. | Blind fusion evaluation. |
| G9 Final Evidence Reproducible | Frozen scores, paired ablation, and final matrix reconstruct from manifests. | Dissertation evidence package. |

Every new path advances `legacy -> shadow -> active`. Failure preserves prior
evidence and prevents only promotion. A truth leak, mixed schema, invalid join,
or incomplete required modality finalizes the affected formal run as aborted;
it is not silently discarded or relabeled.

## Epic 9: Evidence-Safe Baseline, Source Ledger, and Contract Freeze

**Goal:** Research owners can reproduce the v1 baseline and reject unsupported
v2 parameters before scientific evidence is produced.

**Requirements:** FR76, FR86–FR88; NFR39–NFR41, NFR48–NFR52.  
**Dependencies:** Approved planning overlays; no implementation dependency.  
**Guardrail:** This epic catalogs and freezes evidence; it does not legitimize a
legacy constant merely because that constant is recorded.

### Story 9.1: Freeze the v1 Evidence Baseline

As a research owner, I want an immutable manifest of v1 code, configuration,
models, datasets, and results so that later changes cannot rewrite the baseline.

**Dependencies:** None.  
**Acceptance Criteria:**

**Given** the existing v1 repository and artifacts, **when** the freeze is
prepared, **then** every included item has an identity, hash, role, and locator,
and missing or mutable items are listed as limitations rather than inferred.

### Story 9.2: Complete the Source and Parameter-Evidence Catalogs

As a researcher, I want every executable scientific parameter classified and
linked to evidence so that unsupported values fail review.

**Dependencies:** Story 9.1.  
**Acceptance Criteria:**

**Given** a parameter used by a v2 profile, **when** the catalog is validated,
**then** its value, unit, classification, locator, derivation, scope, and
decision authority resolve; otherwise validation fails without a fallback.

### Story 9.3: Preserve v1 Contracts as Golden Fixtures

As a maintainer, I want schemas and golden fixtures for current MQTT, consensus,
OPC UA, persistence, dataset, and promotion boundaries so that v2 migration is
measurable.

**Dependencies:** Story 9.1.  
**Acceptance Criteria:**

**Given** preserved representative v1 artifacts, **when** each fixture is
decoded and replayed by its declared legacy adapter, **then** the result matches
the frozen expectation and cannot be accepted by a v2 adapter implicitly.

### Story 9.4: Define Immutable Experiment and Evaluation Manifests

As an evaluator, I want experiment, source, provenance, and evaluation manifests
so that every output can be traced to declared inputs and policy.

**Dependencies:** Stories 9.1–9.3.  
**Acceptance Criteria:**

**Given** a planned or completed evidence unit, **when** its manifest is
validated, **then** schema identity, inputs, profiles, code/runtime identity,
authorization state, and artifact hashes resolve, and mutation creates a new
identity rather than overwriting the old one.

### Story 9.5: Pin Runtime Identities and Qualify Evidence Storage

As an operator, I want pinned dependency/image identities and restorable,
append-only evidence storage so that formal artifacts survive environment loss.

**Dependencies:** Story 9.4.  
**Acceptance Criteria:**

**Given** a formal artifact and its runtime manifest, **when** storage
verification and restoration are exercised, **then** content hashes and
namespace identities remain equal, while an unpinned runtime or unverified
object is ineligible for formal evidence.

**Epic 9 closure — G1:** v1 regression fixtures pass; storage restoration is
verified; and no proposed v2 parameter lacks admissible provenance. The gate
does not authorize implementation of later epics.

## Epic 10: Current-Domain Signal and Experiment Control v2

**Goal:** Research operators can run a source-governed physical experiment in
which edges receive canonical transmitter evidence and truth remains isolated.

**Requirements:** FR72–FR77, FR85; NFR38–NFR42, NFR46, NFR50, NFR52.  
**Dependencies:** Epic 9 / G1.  
**Guardrail:** Process physics may use engineering units internally; the custom
edge boundary preserves raw current and derives other representations from the
selected instrument profile.

### Story 10.1: Define Cited Instrument Profiles

As a research engineer, I want versioned temperature, pressure, and RPM
instrument profiles so that conversions and quality rules are auditable.

**Dependencies:** Story 9.2.  
**Acceptance Criteria:**

**Given** a selected instrument profile, **when** it is activated, **then** its
signal endpoints, engineering endpoints, units, quality semantics, source
locator, and derivations resolve; an incomplete profile cannot emit v2 evidence.

### Story 10.2: Define and Validate `SignalObservation.v2`

As an edge consumer, I want one canonical signal contract so that raw current,
normalized span, derived engineering value, quality, identity, and timestamps
cannot drift across services.

**Dependencies:** Story 10.1.  
**Acceptance Criteria:**

**Given** a valid profile and observation, **when** the contract is validated,
**then** all representations reconcile through the recorded derivation and
quality is assessed before any optional clipping; schema or profile mismatch
fails explicitly.

### Story 10.3: Separate Process Physics From Transmitter Emission

As a simulator maintainer, I want the plant model to retain physical units while
the transmitter adapter emits current so that realism and acquisition semantics
are not conflated.

**Dependencies:** Stories 10.1–10.2.  
**Acceptance Criteria:**

**Given** the same plant state and instrument profile, **when** batch and live
transmitter paths emit an observation, **then** their canonical signal features
are equivalent and consumers do not recompute profile conversion independently.

### Story 10.4: Define `ExperimentSpec`

As a research owner, I want an immutable experiment specification so that
profiles, factors, scenarios, stopping policy, seeds, and authorization are
declared before evidence collection.

**Dependencies:** Stories 9.2 and 9.4.  
**Acceptance Criteria:**

**Given** an experiment specification, **when** it is validated, **then** every
numeric field resolves to the parameter ledger and the specification cannot be
executed unless its authorization state permits that activity.

### Story 10.5: Generate the Preregistered 25%–75% Reference Schedule

As an experiment operator, I want automatic variation of the declared speed or
capacity reference so that detector behavior can be mapped across operating
regimes without manual intervention.

**Dependencies:** Story 10.4.  
**Acceptance Criteria:**

**Given** an approved `ExperimentSpec`, **when** the schedule is generated,
**then** its reference remains within the preregistered 25%–75% factor and all
other schedule characteristics resolve to separately admissible parameters;
the output is never labeled electrical power.

### Story 10.6: Isolate Scenario Truth and Correlation Identities

As an evaluator, I want scenario truth stored separately while observations
carry non-semantic correlation identities so that blind inference is possible.

**Dependencies:** Stories 10.4–10.5.  
**Acceptance Criteria:**

**Given** an active scenario, **when** producers and detectors operate, **then**
they can correlate run and observation identities without reading truth, attack
names, future state, or expected outcomes; only the evaluator role can unlock
truth after declared artifacts are frozen.

### Story 10.7: Persist Complete Raw Custom Physical Evidence

As a researcher, I want each physical cycle persisted with source identity and
quality so that derived datasets can be rebuilt without hidden runtime state.

**Dependencies:** Stories 10.2–10.6.  
**Acceptance Criteria:**

**Given** emitted custom observations, **when** persistence completes or fails,
**then** append-only artifacts preserve ordering, correlation, profile,
timestamps, quality, and raw current, while gaps and partial writes are explicit
and never synthesized.

**Epic 10 closure — G2:** Batch/live canonical features agree; raw current,
normalized span, engineering derivation, quality, timestamps, profile, and
correlation remain coherent end to end; truth is inaccessible to detectors.

## Epic 11: Current-Domain Consensus v2

**Goal:** Researchers can reproduce consensus and divergence decisions whose
comparison basis and numerical provenance are explicit and equivalent in Python
and Go.

**Requirements:** FR91; NFR39, NFR46, NFR48, NFR50, NFR52.  
**Dependencies:** Epic 10 / G2.  
**Guardrail:** Legacy divergence scales and trust thresholds do not migrate by
default; each v2 parameter must pass the evidence gate.

### Story 11.1: Define the Versioned Consensus v2 Contract

As a consensus consumer, I want transactions and committed views to declare
signal basis and instrument profile so that comparisons are semantically valid.

**Dependencies:** Story 10.2.  
**Acceptance Criteria:**

**Given** a consensus transaction, **when** validation occurs, **then** schema,
profile, basis, units, edge identity, sequence, and correlation resolve, and
incompatible observations cannot enter the same decision silently.

### Story 11.2: Replace Anonymous Divergence Parameters

As a research owner, I want divergence and trust configuration resolved through
the parameter ledger so that no attractive but unsupported number controls the
result.

**Dependencies:** Stories 9.2 and 11.1.  
**Acceptance Criteria:**

**Given** a v2 consensus profile, **when** it loads, **then** every scale,
tolerance, weight, and threshold resolves to admissible evidence or a
preregistered decision; any unresolved legacy value prevents activation.

### Story 11.3: Create Shared Python/Go Golden Parity Tests

As a maintainer, I want both implementations tested against identical fixtures
so that reference and live consensus cannot diverge unnoticed.

**Dependencies:** Stories 11.1–11.2.  
**Acceptance Criteria:**

**Given** valid, invalid, boundary, missing, and mixed-profile fixtures, **when**
Python and Go evaluate them, **then** committed fields, exclusions, failure
states, and canonical serialization are identical or the gate fails.

### Story 11.4: Add v2 State and Query Compatibility

As an auditor, I want v2 state and queries beside historical state so that new
semantics do not rewrite legacy AppHash evidence.

**Dependencies:** Story 11.3.  
**Acceptance Criteria:**

**Given** legacy and v2 records, **when** they are queried or replayed, **then**
each resolves through its declared adapter and historical hashes remain
unchanged; implicit cross-version decoding is rejected.

### Story 11.5: Specify Reproducible Divergence Sensitivity Analysis

As an evaluator, I want parameter sensitivity declared before test access so
that consensus conclusions expose dependence on defensible choices.

**Dependencies:** Stories 11.2–11.4.  
**Acceptance Criteria:**

**Given** a preregistered analysis specification, **when** sensitivity results
are produced, **then** each tested value has provenance, all planned outcomes
are retained, and no test result is used to retroactively select the primary
configuration.

**Epic 11 closure — G3:** Shared fixtures produce deterministic equivalent
Python/Go outcomes, historical state remains intact, and no anonymous numerical
constant controls v2 consensus.

## Epic 12: Independent OPC UA Laboratory Boundary

**Goal:** Evaluators can compare consensus against an independently transported
pre-consensus plant observation rather than a circular copy of consensus.

**Requirements:** FR90; NFR41–NFR42, NFR46–NFR50, NFR52.  
**Dependencies:** Epic 10 / G2.  
**Guardrail:** The OPC UA branch and consensus branch may share a plant snapshot
identity, but neither may derive its observed value from the other.

### Story 12.1: Feed OPC UA From the Pre-Consensus Plant Snapshot

As an evaluator, I want the OPC writer sourced before consensus so that the
comparison has an independent logical origin.

**Dependencies:** Stories 10.3 and 10.6.  
**Acceptance Criteria:**

**Given** a correlated plant snapshot, **when** it is published to both paths,
**then** OPC input is derived from that snapshot rather than committed consensus
state, and lineage proves the branch point.

### Story 12.2: Run the OPC UA Server as a Separate Boundary

As a laboratory operator, I want server state isolated from consumers so that
in-process object sharing cannot masquerade as protocol validation.

**Dependencies:** Story 12.1.  
**Acceptance Criteria:**

**Given** an OPC writer and server, **when** the consumer is absent or restarted,
**then** server behavior remains independent and exposes only declared nodes,
status, and timestamps through the configured endpoint.

### Story 12.3: Read Exclusively Through a Real `asyncua.Client`

As an evaluator, I want comparison input reconstructed through an OPC UA client
session so that the network protocol boundary is actually exercised.

**Dependencies:** Story 12.2.  
**Acceptance Criteria:**

**Given** a running server, **when** comparison reads a value, **then** it uses a
distinct `asyncua.Client` session and cannot fall back to server objects,
consensus memory, or cached truth.

### Story 12.4: Preserve OPC UA Quality, Timestamps, and Correlation

As a data analyst, I want `StatusCode`, source/server timestamps, schema, and
correlation retained so that validity and freshness can be evaluated.

**Dependencies:** Story 12.3.  
**Acceptance Criteria:**

**Given** a client `DataValue`, **when** it becomes comparison evidence, **then**
value, status, source timestamp, server timestamp, profile, and correlation are
preserved without substitution or silent timestamp fabrication.

### Story 12.5: Fail Closed on Invalid OPC UA Evidence

As an operator, I want invalid or unavailable observations classified explicitly
so that missing evidence is not treated as agreement.

**Dependencies:** Story 12.4.  
**Acceptance Criteria:**

**Given** bad, uncertain, stale, missing, mixed-schema, or mis-correlated OPC
evidence, **when** comparison runs, **then** it emits a typed invalid outcome and
does not persist a valid-state comparison.

### Story 12.6: Prove Causal Independence

As an academic evaluator, I want controlled causal tests so that circularity is
disproved rather than merely asserted.

**Dependencies:** Stories 12.1–12.5.  
**Acceptance Criteria:**

**Given** isolated modifications to consensus and OPC source inputs, **when**
the test matrix runs, **then** consensus-only changes cannot alter OPC source
values and OPC-only changes cannot alter consensus decisions; violations block
the gate.

**Epic 12 closure — G4:** A real OPC UA round trip preserves status and
timestamps, invalid evidence fails closed, and the causal-independence matrix
passes without in-memory shortcuts.

## Epic 13: Calibrated Physical Detector and Fingerprint v2

**Goal:** Researchers can compare physical anomaly candidates fairly and deploy
only a frozen, reproducible inference bundle.

**Requirements:** FR78, FR86–FR88; NFR40–NFR44, NFR48–NFR52.  
**Dependencies:** Epics 10 and 12 / G2 and G4.  
**Guardrail:** Training and calibration artifacts are separate from test and
truth. No runtime path fits preprocessing, trains a model, or recalibrates a
threshold.

### Story 13.1: Define the Physical Feature Schema

As a model developer, I want a versioned current-domain feature schema so that
every feature has one meaning, order, unit, and provenance.

**Dependencies:** Story 10.2.  
**Acceptance Criteria:**

**Given** a canonical physical observation, **when** features are built, **then**
the bundle-declared schema determines inclusion, order, representation, missing
policy, and profile compatibility; mixed physical units cannot dominate through
an undeclared scale.

### Story 13.2: Build Group-Safe Physical Partitions and Windows

As an evaluator, I want complete runs split before windowing so that temporal
neighbors and truth cannot leak between partitions.

**Dependencies:** Story 13.1.  
**Acceptance Criteria:**

**Given** immutable run groups, **when** training, calibration, and test
partitions and windows are created, **then** no window crosses a run, gap,
schema, or partition boundary, and preprocessing is fit only on declared normal
training evidence.

### Story 13.3: Compare LSTM-AE, GRU-AE, and Declared Baselines

As a researcher, I want candidate models evaluated under one protocol so that
architecture claims are evidence-based.

**Dependencies:** Story 13.2.  
**Acceptance Criteria:**

**Given** frozen partitions and a shared evaluation specification, **when** each
candidate runs, **then** it receives equivalent inputs and evaluation policy,
all model-specific choices have provenance, and failed or unfavorable runs are
retained.

### Story 13.4: Calibrate the Physical Decision Threshold

As an evaluator, I want threshold selection limited to independent normal
calibration evidence so that test outcomes do not tune the detector.

**Dependencies:** Story 13.3.  
**Acceptance Criteria:**

**Given** frozen candidate outputs on calibration data, **when** a threshold is
selected, **then** its method, inputs, value, and rationale are recorded before
test access; runtime data and test labels cannot alter it.

### Story 13.5: Build an Atomic Immutable Physical Detector Bundle

As an operator, I want model, preprocessing, feature schema, calibration
identity, threshold, and runtime identity packaged atomically so that inference
cannot mix incompatible parts.

**Dependencies:** Stories 13.1–13.4.  
**Acceptance Criteria:**

**Given** an approved candidate, **when** its bundle is saved and loaded, **then**
all component hashes and compatibility rules verify together; a missing,
changed, or mismatched component fails closed.

### Story 13.6: Produce the 25%–75% Regime and Anomaly Mapping

As a research owner, I want detector scores mapped to declared operating regimes
and scenario truth so that changing reference is not automatically labeled an
anomaly.

**Dependencies:** Stories 10.5–10.6 and 13.5.  
**Acceptance Criteria:**

**Given** frozen inference scores from the preregistered schedule, **when** the
evaluator unlocks truth, **then** it produces an auditable table of regime,
transition, scenario, score, decision, and outcome without changing the model or
threshold.

### Story 13.7: Serve Inference-Only Physical Shadow Results

As an operator, I want the frozen detector to run in shadow so that it can be
observed without controlling the plant or learning online.

**Dependencies:** Stories 13.5–13.6.  
**Acceptance Criteria:**

**Given** a compatible observation stream and bundle, **when** shadow inference
runs, **then** it emits versioned scores and health evidence without training,
recalibration, truth access, or control writes; incompatibility yields an
explicit unavailable result.

**Epic 13 closure — G5:** The physical bundle replays frozen scores in its
declared environment, rejects schema/hash mismatch, and performs inference only.

## Epic 14: Controlled Linux Edge Workload and Real Syscall Detection

**Goal:** Researchers can collect attributable kernel syscalls from controlled
Linux edge workloads and evaluate categorical syscall detectors.

**Requirements:** FR79–FR81, FR85–FR88; NFR41–NFR47, NFR50, NFR52.  
**Dependencies:** Epic 10 / G2; Epic 9 storage and manifests.  
**Guardrail:** Experimental syscalls are real calls observed at the Linux kernel
boundary. Fixture replay is test-only and cannot enter `PTFP-Custom-v1`.

### Story 14.1: Containerize an Allowlisted Linux Edge Workload

As a security researcher, I want a pinned Linux edge workload that performs
declared prototype functions so that its kernel behavior is attributable.

**Dependencies:** Stories 9.5 and 10.6.  
**Acceptance Criteria:**

**Given** a workload manifest, **when** the container runs, **then** image,
entrypoint, process tree, edge identity, permissions, and experiment correlation
are recorded, and unrelated infrastructure processes are outside its evidence
scope.

### Story 14.2: Qualify the Sysdig/eBPF Capture Boundary

As a laboratory operator, I want a capture spike that measures attribution,
loss, overhead, and platform compatibility so that the formal host boundary is
chosen from evidence.

**Dependencies:** Story 14.1.  
**Acceptance Criteria:**

**Given** the controlled workload on the candidate Linux boundary, **when**
capture is exercised, **then** collector, kernel, architecture, filters,
attribution, drops, gaps, overhead, and limitations are preserved; an
unreliable boundary cannot be promoted to formal capture.

### Story 14.3: Define `SyscallEventBatch.v1` and Separate Transport

As a detector consumer, I want syscall batches on a separate high-volume path
so that host events cannot enter physical consensus or overload its contract.

**Dependencies:** Story 14.2.  
**Acceptance Criteria:**

**Given** captured events, **when** a batch is emitted, **then** experiment,
edge, boot, process, ordering, timestamps, kernel/runtime identity, loss
counters, and raw-segment hash resolve, while labels are structurally absent.

### Story 14.4: Canonicalize, Group, Window, and Account for Loss

As a model developer, I want categorical event processing with explicit session
and loss boundaries so that sequences remain meaningful.

**Dependencies:** Story 14.3.  
**Acceptance Criteria:**

**Given** syscall batches with sessions, gaps, or backpressure, **when**
canonical sequences and windows are created, **then** syscall identity remains
categorical, no window crosses a declared boundary, and missing events are
reported rather than imputed as observed calls.

### Story 14.5: Compare Normal-Only Syscall Candidates

As a researcher, I want categorical LSTM, GRU, and n-gram/STIDE-style baselines
compared under one protocol so that recurrence is justified empirically.

**Dependencies:** Story 14.4.  
**Acceptance Criteria:**

**Given** group-safe normal training and independent evaluation evidence,
**when** candidates run, **then** they share declared inputs and evaluation
policy, never apply regression loss to numeric syscall IDs, and retain all
planned outcomes.

### Story 14.6: Correlate Captured Syscalls With Physical Experiments

As an evaluator, I want syscall evidence correlated with the same experiment
identities as physical evidence so that later paired analysis is possible.

**Dependencies:** Stories 10.6–10.7 and 14.3–14.5.  
**Acceptance Criteria:**

**Given** a custom experiment, **when** physical and syscall segments are
finalized, **then** their clocks, run identities, completeness, and correlation
evidence permit an explicit valid or invalid join without exposing truth to
detectors.

**Epic 14 closure — G6:** Captured events are real kernel calls attributable to
the declared workload, and capture loss, overhead, gaps, runtime identity, and
custom correlation are inspectable. Fixture-only evidence is excluded.

## Epic 15: Correct ADFA-LD and LID-DS External Syscall Benchmarks

**Goal:** Researchers can reproduce external syscall benchmark results without
misusing labels, trace groups, release layouts, or numeric syscall identity.

**Requirements:** FR81–FR83, FR86–FR88; NFR38–NFR45, NFR50–NFR52.  
**Dependencies:** Epic 9 / G1; independent of custom capture.  
**Guardrail:** ADFA-LD and LID-DS remain external benchmarks; neither supplies
runtime calls nor physical compressor evidence.

### Story 15.1: Freeze ADFA-LD Source Identity and Dataset Card

As a researcher, I want source hash, empirical inventory, official roles,
attack-family mapping, and limitations fixed so that ADFA-LD results resolve to
the exact local evidence.

**Dependencies:** Story 9.4.  
**Acceptance Criteria:**

**Given** the acquired ADFA-LD corpus, **when** it is cataloged, **then** source
identity, license/access notes, empirical counts, trace roles, six attack
families, and any discrepancy with publications are recorded without silently
repairing source data.

### Story 15.2: Preserve ADFA-LD Trace Identity Before Windowing

As an evaluator, I want official roles and trace groups fixed before windows so
that related events cannot leak across partitions.

**Dependencies:** Story 15.1.  
**Acceptance Criteria:**

**Given** ADFA-LD traces, **when** partitions and windows are constructed,
**then** complete trace identity and official role are preserved, no window
crosses a trace or partition, and additional calibration grouping is
preregistered.

### Story 15.3: Use Categorical ADFA-LD Syscall Semantics

As a model developer, I want numeric syscall tokens treated as categories so
that ordinal distance is not fabricated.

**Dependencies:** Story 15.2.  
**Acceptance Criteria:**

**Given** an ADFA-LD trace, **when** it is encoded, **then** tokens use a frozen
training-derived vocabulary with explicit unknown handling, and no token is
executed or interpreted as a continuous magnitude.

### Story 15.4: Implement the Official LID-DS 2021 Layout

As a researcher, I want a release-specific adapter for official scenario and
recording groups so that LID results match the published dataset semantics.

**Dependencies:** Story 9.4.  
**Acceptance Criteria:**

**Given** a pinned LID-DS 2021 source, **when** the adapter loads it, **then**
scenario, recording, process/context, event, and official partition identities
are preserved; unsupported layouts fail explicitly.

### Story 15.5: Isolate the Official LID Processing Environment

As a maintainer, I want the release-compatible LID environment pinned and
separate from the main runtime so that legacy dependencies cannot destabilize
the prototype.

**Dependencies:** Story 15.4.  
**Acceptance Criteria:**

**Given** the LID adapter manifest, **when** it executes, **then** its runtime
identity and outputs are reproducible through an isolated boundary, and version
conflicts cannot trigger an implicit parser substitution.

### Story 15.6: Compare Normal-Only External Syscall Candidates

As an academic evaluator, I want LSTM, GRU, and categorical baselines evaluated
under dataset-correct grouping so that results are comparable within each
benchmark.

**Dependencies:** Stories 15.2–15.5.  
**Acceptance Criteria:**

**Given** frozen benchmark partitions, **when** candidates are trained,
calibrated, and evaluated, **then** labels remain evaluation-only, preprocessing
uses training evidence only, and all candidates share each benchmark's declared
protocol.

### Story 15.7: Publish External Syscall Dataset Cards and Result Tables

As a dissertation reader, I want provenance, limitations, metrics, and results
reported separately for ADFA-LD and LID-DS so that incompatible datasets are not
collapsed into a false global ranking.

**Dependencies:** Story 15.6.  
**Acceptance Criteria:**

**Given** frozen benchmark outputs, **when** tables are generated, **then** each
result resolves to source, split, model bundle, score, metric policy, and known
limitation, including unsuccessful planned runs.

**Epic 15 closure — contributes to G7:** Both external syscall benchmarks have
resolvable source/version/license records, group-safe windows, categorical
semantics, label isolation, reproducible outputs, and separate result tables.

## Epic 16: HAI 23.05 External Physical Benchmark

**Goal:** Researchers can evaluate physical candidates on a published industrial
benchmark while preserving HAI's native meaning and limitations.

**Requirements:** FR78, FR84, FR86–FR88; NFR38–NFR44, NFR50–NFR52.  
**Dependencies:** Epic 9 / G1; model protocol concepts from Epic 13 may be reused
without sharing a compressor-trained bundle.  
**Guardrail:** HAI tags are not assumed to be current-loop signals and are not
mass-converted to mA.

### Story 16.1: Acquire and Pin HAI 23.05

As a researcher, I want the official repository state and file checksums fixed
so that the benchmark version is unambiguous.

**Dependencies:** Story 9.4.  
**Acceptance Criteria:**

**Given** an authorized acquisition, **when** HAI is cataloged, **then** release
identity, commit, files, hashes, roles, source link, and license limitations are
recorded; unverified files are excluded from formal results.

### Story 16.2: Implement a Version-Specific HAI Adapter

As a model developer, I want a HAI 23.05 adapter with checked label joins so
that features and evaluation truth remain aligned but isolated.

**Dependencies:** Story 16.1.  
**Acceptance Criteria:**

**Given** pinned HAI files, **when** the adapter loads them, **then** the declared
schema, file roles, timestamps, tag identity, and separate label relationship
validate; another HAI layout cannot load implicitly.

### Story 16.3: Preserve Native Tags, Units, and Continuity

As an evaluator, I want HAI preprocessing to respect its published
representation so that transformations do not invent transmitter semantics.

**Dependencies:** Story 16.2.  
**Acceptance Criteria:**

**Given** HAI observations, **when** features and windows are created, **then**
native tag/unit metadata and continuity boundaries remain traceable, complete
groups are split before windows, and preprocessing is fit on normal training
evidence only.

### Story 16.4: Compare HAI Physical Detector Candidates

As a researcher, I want LSTM-AE, GRU-AE, and declared baselines compared on one
HAI protocol so that conclusions do not depend on unequal preparation.

**Dependencies:** Story 16.3.  
**Acceptance Criteria:**

**Given** frozen HAI partitions, **when** candidates are trained, calibrated,
and evaluated, **then** each uses the same declared inputs and evaluation policy,
test labels do not tune the detector, and all planned outcomes are retained.

### Story 16.5: Evaluate Point, Window, and Temporal Events

As a dissertation reader, I want protocol-appropriate physical anomaly metrics,
including HAI's recommended temporal event evaluation, so that timing behavior
is visible.

**Dependencies:** Story 16.4.  
**Acceptance Criteria:**

**Given** frozen HAI scores and evaluation truth, **when** metrics are computed,
**then** metric versions, parameters, event mapping, uncertainty, and source
artifacts are recorded and can be reconstructed without retraining.

### Story 16.6: Publish the HAI Dataset Card and Limitations

As an academic reviewer, I want process mismatch, schema, license, and
generalization limits stated beside results so that HAI is not presented as
compressor validation.

**Dependencies:** Stories 16.1–16.5.  
**Acceptance Criteria:**

**Given** the completed HAI evaluation, **when** its report is generated,
**then** source, native representation, split, models, metrics, results, failed
runs, and limitations resolve, and the report explicitly rejects wholesale mA
conversion and compressor-specific claims.

**Epic 16 closure — completes G7 with Epic 15:** HAI source, adapter, native
semantics, split, truth isolation, metrics, and limitations are reproducible;
ADFA-LD and LID-DS are independently qualified by Epic 15.

## Epic 17: Synchronized Custom Dataset, Long Runs, Fusion, and Final Matrix

**Goal:** The research owner can make a reproducible paired claim about the
benefit or limitation of combining physical and syscall evidence.

**Requirements:** FR72, FR85–FR89, FR92; NFR38–NFR52.  
**Dependencies:** G5, G6, and G7; Epic 11 / G3 is required for consensus fields
used by the campaign.  
**Guardrail:** Fusion uses only synchronized held-out `PTFP-Custom-v1` runs and
frozen detector outputs. External benchmark scores are never joined to custom
scores or used as if observed in the same process.

### Story 17.1: Preregister the Formal Campaign

As a research owner, I want campaign conditions, partitions, repetitions,
metrics, stopping rules, calibration, and fusion policies frozen before
execution so that outcome-driven redesign is detectable.

**Dependencies:** Epics 9–16 planning outputs.  
**Acceptance Criteria:**

**Given** a proposed campaign, **when** preregistration is validated, **then**
every executable number has admissible provenance, required and abort
conditions are explicit, truth remains locked, and execution requires separate
authorization.

### Story 17.2: Capture and Lock `PTFP-Custom-v1`

As an evaluator, I want synchronized physical and syscall evidence finalized by
complete run so that valid paired comparisons can be constructed.

**Dependencies:** Story 17.1; G3–G6.  
**Acceptance Criteria:**

**Given** an authorized custom run, **when** it is finalized, **then** physical
and syscall segments, clocks, correlation, quality, gaps, capture health, and
manifest hashes produce an immutable valid, invalid, or aborted run status; no
missing event is fabricated.

### Story 17.3: Freeze Bundles, Thresholds, and Scores Before Truth Unlock

As an evaluator, I want all detector outputs committed before labels are visible
so that post-hoc tuning cannot alter the blind result.

**Dependencies:** Story 17.2 and G5–G6.  
**Acceptance Criteria:**

**Given** locked held-out runs, **when** physical and syscall inference
completes, **then** bundle identities, preprocessing, thresholds, score
artifacts, completeness, and hashes are frozen before evaluator-only truth
access is granted.

### Story 17.4: Execute Predeclared Simple Late Fusion

As a researcher, I want transparent late-fusion policies over calibrated scores
so that combined decisions are interpretable and reproducible.

**Dependencies:** Story 17.3.  
**Acceptance Criteria:**

**Given** paired frozen detector scores and a preregistered fusion policy,
**when** fusion is executed, **then** score calibration and availability rules
are enforced, incompatible or incomplete pairs fail explicitly, and no hidden
or test-fitted weight is introduced.

### Story 17.5: Perform the Paired Modality Ablation

As an academic evaluator, I want physical-only, syscall-only, and fusion
conditions evaluated on the same held-out runs/windows so that any observed gain
has a valid comparison basis.

**Dependencies:** Story 17.4.  
**Acceptance Criteria:**

**Given** frozen predictions and unlocked evaluation truth, **when** the
ablation is computed, **then** every condition uses identical eligible samples,
reports availability and exclusions, applies one frozen metric policy, and
retains unfavorable outcomes.

### Story 17.6: Produce Separate External and Custom Result Tables

As a dissertation reader, I want ADFA-LD, LID-DS, HAI, and PTFP-Custom results
presented in their correct domains so that benchmark context is not lost.

**Dependencies:** Story 17.5 and G7.  
**Acceptance Criteria:**

**Given** qualified result artifacts, **when** tables are generated, **then**
external syscall, external physical, and custom paired results remain separate,
use protocol-appropriate metrics, and contain source, model, split, uncertainty,
and limitation references.

### Story 17.7: Build the Final Matrix and Claim-to-Evidence Index

As a research owner, I want each dissertation claim mapped to capabilities,
results, and limitations so that reviewers can audit what the evidence supports.

**Dependencies:** Story 17.6.  
**Acceptance Criteria:**

**Given** final result tables, **when** the matrix and claim index are built,
**then** there is no global champion across incompatible datasets, every claim
resolves to immutable evidence and an explicit limitation, and unsupported
claims are marked unsupported rather than softened.

### Story 17.8: Reconstruct the Final Evidence Package

As an independent reviewer, I want every final table and matrix cell rebuilt
from manifests and frozen artifacts so that the result has no hidden state.

**Dependencies:** Story 17.7.  
**Acceptance Criteria:**

**Given** a clean declared evaluation environment and the evidence manifests,
**when** reconstruction runs, **then** source verification, joins, scores,
metrics, tables, and claim links reproduce without training or manual edits;
any mismatch blocks finalization.

**Epic 17 closure — G8 and G9:** `PTFP-Custom-v1` is immutable with isolated
truth; detector scores precede truth unlock; paired ablation is complete; and
all external tables, custom tables, final matrix, and claims reconstruct without
hidden state.

## Epic 18: Evidence-Backed Read-Only Dashboard

**Goal:** Demonstration viewers can inspect the two modalities, detector
channels, provenance, and evidence quality without changing scientific state.

**Requirements:** FR72, FR92–FR93; NFR38, NFR42, NFR50–NFR52.  
**Dependencies:** Optional after Epic 17 / G9; it must not block the evidence
package.  
**Guardrail:** The dashboard reads published artifacts only and never imports,
splits, trains, calibrates, promotes, fuses, relabels, or rewrites results.

### Story 18.1: Add Tolerant Versioned Read Models

As a demonstration operator, I want explicit v1 and v2 read adapters so that
historical and current evidence can be shown without semantic coercion.

**Dependencies:** Stories 9.3–9.4 and published v2 schemas.  
**Acceptance Criteria:**

**Given** a supported artifact, **when** the dashboard reads it, **then** the
declared version selects the adapter and missing or incompatible data appears as
unavailable; the dashboard never upgrades or mutates the source artifact.

### Story 18.2: Present Physical Signal Representations Correctly

As a viewer, I want raw current, normalized span, and engineering value shown as
representations of one physical modality so that the interface does not invent
a third modality.

**Dependencies:** Story 18.1 and `SignalObservation.v2`.  
**Acceptance Criteria:**

**Given** a physical observation, **when** it is displayed, **then** current,
normalized span, engineering value, unit, profile, quality, and derivation
identity remain linked and HAI native tags are not mislabeled as current.

### Story 18.3: Present Physical, Syscall, and Fusion Detector Channels

As a viewer, I want detector channels visually distinct so that scores and
availability are interpreted within their proper evidence source.

**Dependencies:** Stories 18.1–18.2 and published detector outputs.  
**Acceptance Criteria:**

**Given** available detector artifacts, **when** the dashboard renders them,
**then** physical, syscall, and fusion channels show bundle, threshold,
availability, correlation, and result role separately, without recomputing a
decision.

### Story 18.4: Display Benchmark Provenance and Limitations

As an academic reviewer, I want each result labeled by source, version, evidence
tier, role, and limitation so that benchmark and custom evidence cannot be
confused.

**Dependencies:** Story 18.1 and Stories 15.7, 16.6, 17.7.  
**Acceptance Criteria:**

**Given** a benchmark or custom result, **when** it is displayed, **then** its
dataset, version, modality, manifest, model, metric, scope, and limitations
resolve to published evidence, while missing provenance is visibly invalid.

### Story 18.5: Present Long-Run Completeness Without Calculating Science

As an operator, I want run completeness and collection health visible so that
aborted or degraded evidence is not mistaken for a valid result.

**Dependencies:** Stories 18.1–18.4 and Story 17.8.  
**Acceptance Criteria:**

**Given** published campaign manifests, **when** health is displayed, **then**
run status, modality availability, gaps, drops, correlation, and reconstruction
status come from immutable evaluator outputs; the dashboard performs no metric,
fusion, exclusion, or status recalculation.

**Epic 18 closure:** Presentation accurately distinguishes signal
representations, detector channels, datasets, provenance, completeness, and
limitations, and technical controls prove the dashboard has no write or
scientific-computation authority.

## 7. Backlog Activation Rule

The ordering and gates in this overlay define readiness, not authorization.
Before any story begins, a later approval record must identify the permitted
story or story range and activity type. Model training, dataset acquisition,
syscall capture, and formal experiment execution require explicit authorization
even if code implementation has separately been approved.

Until then, every Epic 9–18 story remains **planned / implementation not
authorized**.
