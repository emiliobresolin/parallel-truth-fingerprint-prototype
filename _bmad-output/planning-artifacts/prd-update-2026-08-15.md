---
workflowType: prd
workflow: edit
classification:
  domain: industrial anomaly-detection research
  projectType: local academic research prototype
  complexity: high
inputDocuments:
  - _bmad-output/planning-artifacts/prd.md
  - _bmad-output/planning-artifacts/prd-update-2026-05-21.md
  - _bmad-output/planning-artifacts/epics-update-2026-07-30.md
  - _bmad-output/planning-artifacts/implementation-readiness-report-2026-08-15.md
stepsCompleted:
  - step-e-01-discovery
  - step-e-02-review
  - step-e-03-edit
lastEdited: 2026-08-15
editHistory:
  - date: 2026-08-15
    changes: Added binding individual dispositions for FR30-FR71 and NFR22-NFR37 and clarified downstream traceability.
type: prd-update
date: 2026-08-15
status: approved-for-planning-only
approval_scope: planning-only
approved_change_proposal: _bmad-output/planning-artifacts/sprint-change-proposal-2026-08-15.md
parent: _bmad-output/planning-artifacts/prd.md
controlling_research: _bmad-output/planning-artifacts/research/technical-scientifically-grounded-industrial-signal-and-anomaly-simulation-research-2026-08-15.md
validation_report: _bmad-output/planning-artifacts/implementation-readiness-report-2026-08-15.md
reference_archive: docs/reference-archive/
implementation_authorized: false
training_authorized: false
experiment_execution_authorized: false
partially_supersedes:
  - _bmad-output/planning-artifacts/prd-update-2026-05-21.md
  - _bmad-output/planning-artifacts/sprint-change-proposal-2026-07-28.md
  - _bmad-output/planning-artifacts/epics-update-2026-07-30.md
---

# PRD Update - Evidence-Grounded Physical and Syscall Anomaly Research

## 1. Authority and Reading Rule

This document is an additive overlay on `prd.md`. The base PRD remains
authoritative wherever this overlay is silent. Where the base PRD, the May PRD
overlay, the July change proposal, or the July epic requirements conflict with
this document, this document controls. It translates the Sprint Change Proposal
approved by Emilio on 2026-08-15 into product requirements; it does not silently
rewrite implementation history or previously produced results.

For identifier-level authority, the binding matrices in Sections 8.4 and 8.5
control every July FR30-FR71 and NFR22-NFR37 identifier. `RETAIN` keeps the
July normative sentence active under its original identifier. `AMEND ->` keeps
the stated intent only as narrowed or strengthened by the named controlling
requirements. `SUPERSEDE ->` replaces the July normative sentence with the
named controlling requirements. Requirement identifiers are never silently
renumbered, reused, or inferred from semantic similarity.

This overlay authorizes planning artifacts only. It does **not** authorize code
or configuration changes, dataset acquisition, model fitting, model promotion,
Linux syscall capture, simulator campaigns, or long-running experiments.

## 2. Revised Product Definition

The product is a local academic research testbed that preserves and compares
two, and only two, anomaly-detection modalities:

1. **Physical instrumentation:** observations of the simulated compressor as
   instrument signals, quality, and derived process representations.
2. **Linux host syscalls:** real kernel events emitted by controlled Linux edge
   workloads and captured at the kernel boundary.

A 4-20 mA loop is an electrical representation of the physical-instrumentation
modality. It is not a modality of its own. Raw current, normalized position in
the configured span, and the derived engineering value are three synchronized
representations of one physical observation. An autoencoder is a model family,
not a dataset, modality, or evidence source.

For the custom prototype, the edge-facing evidentiary boundary is the raw
instrument current plus signal quality and instrument-profile identity. The
compressor/process simulator may continue to calculate its internal physics in
engineering units. Conversion to temperature, pressure, or RPM is performed
once through the declared instrument profile for process semantics, SCADA
display, and interpretation. This is a project boundary; it does not claim that
every industrial control system performs all internal logic directly in mA.

The final dissertation question is not whether one model is universally best.
It is whether a preregistered, calibrated late fusion of physical-instrument
and Linux-host-syscall anomaly evidence improves the measured trade-offs over
either detector alone on the same held-out custom runs.

## 3. Evidence-Source Roles

| Evidence source | Modality | Required role | Explicit exclusion |
| --- | --- | --- | --- |
| ADFA-LD | Linux host syscalls | External ordered-syscall benchmark | Its numeric identifiers are not executed or presented as live edge syscalls |
| LID-DS 2021 | Linux host syscalls | External richer-syscall benchmark and methodological reference for Docker/Sysdig recording | Its example recording timings are not project parameters, and fixture replay is not custom experimental evidence |
| HAI 23.05 | Physical instrumentation/SCADA | External version-specific physical benchmark in its published representation | HAI is not converted wholesale to 4-20 mA, appended with prototype rows, or presented as compressor validation |
| PTFP-Custom-v1 | Both modalities | New synchronized dataset from the same controlled prototype runs | It is simulated research evidence, not real-plant data or a validated digital twin |

ADFA-LD, LID-DS 2021, and HAI 23.05 produce separate external benchmark
results. They are not joined row-by-row and cannot establish a physical-plus-
syscall fusion result. Only `PTFP-Custom-v1`, which observes both modalities in
the same run and correlation domain, is eligible for that comparison.

## 4. Product Success Criteria

The revised product succeeds when the approved implementation, once separately
authorized, can demonstrate all of the following without hidden state:

- every v2 physical observation preserves raw current, quality, profile,
  normalized span, and engineering derivation coherently end to end;
- every executable v2 numerical parameter resolves to a declared provenance
  category, source or decision locator, unit, derivation, profile, and approved
  experiment scope;
- the automatic 25%-75% schedule is represented as a preregistered speed or
  capacity reference factor, never as electrical power or a universal
  compressor operating recommendation;
- the OPC UA observation is created before consensus and read by an independent
  client, so consensus is never projected into the evidence source it is meant
  to compare;
- the custom syscall branch contains attributable kernel events generated by a
  controlled Linux edge workload, with capture loss and overhead recorded;
- scenario truth and benchmark labels are structurally absent from training and
  inference contracts and are unlocked only for evaluation after model,
  preprocessing, threshold, score, and fusion-policy evidence is frozen;
- LSTM and GRU candidates are evaluated under the same partitions and
  experimental budget as transparent baselines, with no winner asserted before
  measurement;
- ADFA-LD, LID-DS 2021, HAI 23.05, and PTFP-Custom-v1 results remain
  provenance-bound and are reported within their valid evidence roles;
- the final custom comparison uses the same held-out runs/windows for physical-
  only, syscall-only, and preregistered late-fusion ablations; and
- every reported claim can be reconstructed from immutable manifests and links
  to both supporting evidence and limitations.

Completeness statements such as "every parameter" and "truth is absent" are
structural acceptance conditions, not empirical thresholds or claims that a
performance value is universal. No favorable metric value is required to hide
or discard an otherwise valid run.

## 5. Scope Boundaries

### 5.1 In scope for the revised product backlog

- v1 evidence freeze, source catalog, parameter ledger, and versioned contracts;
- `SignalObservation.v2`, cited instrument profiles, and current-domain edge
  evidence while retaining internal process physics and derived engineering
  values;
- versioned experiment control, the preregistered 25%-75% reference schedule,
  correlation, immutable evidence, and isolated truth;
- current-domain physical consensus with deterministic Python/Go parity;
- independent pre-consensus OPC UA supervision;
- physical LSTM autoencoder and GRU autoencoder candidates plus declared
  baselines, using immutable preprocessing/calibration/model bundles;
- controlled Linux edge workloads, real syscall capture, a categorical syscall
  detector track, and capture-quality evidence;
- corrected external adapters and protocols for ADFA-LD, LID-DS 2021, and HAI
  23.05;
- synchronized `PTFP-Custom-v1` generation, long-run evaluation, paired
  ablation, late fusion, and the final claim-to-evidence matrix; and
- a presentation-only dashboard that reads, but cannot create or alter,
  scientific evidence.

### 5.2 Out of scope

- claiming that the simulator is a real plant, validated compressor digital
  twin, certified safety system, or IEC/ISA/NAMUR-conformant product;
- changing RPM to 1-5 V merely because rotation is involved; a documented
  4-20 mA shaft-speed profile is available;
- fabricating, intercepting, renumbering, or modifying syscalls;
- executing ADFA-LD numeric IDs as Linux calls or using fixture replay in the
  experimental matrix;
- converting all HAI tags to mA without documented transmitter profiles;
- training on, or exposing to inference, attack labels or scenario truth;
- selecting a global model champion across incompatible datasets or comparing
  raw losses, scores, or thresholds between unrelated domains;
- granting analytics, detectors, dashboards, or evaluators actuator authority;
  and
- implementation, training, capture, or campaign execution under this planning
  approval.

## 6. Functional Requirements

FR72-FR93 are the current August functional requirements after the historical
July inventory. Section 8.4 gives the binding individual disposition of every
FR30-FR71 identifier. These requirements are additive only where compatible;
an `AMEND ->` or `SUPERSEDE ->` row in Section 8.4 controls conflicting older
wording without renumbering it.

### 6.1 Scientific boundary and physical signal

- **FR72 - Two-modality semantic boundary.** The system shall represent only
  physical instrumentation and Linux host syscalls as detection modalities.
  Documentation, schemas, reports, and UI shall identify 4-20 mA as a physical
  representation and autoencoders as models.

- **FR73 - SignalObservation.v2.** Each custom edge observation shall preserve
  raw current in mA, current quality/diagnostics, instrument and profile
  identity, source and observation timestamps, sequence/correlation identity,
  deterministic normalized span, derived engineering value/unit, schema
  version, and parameter-evidence references. Signal quality shall be evaluated
  before any optional clipping or imputation.

- **FR74 - Profile-owned derivation and physics.** The process model may
  calculate temperature, pressure, and RPM in engineering units, but the edge
  shall receive its primary physical evidence through the selected transmitter
  profile. One profile-owned conversion shall derive normalized span and
  engineering value from the electrical observation; consumers shall not
  redefine that conversion independently. RPM shall remain 4-20 mA while the
  selected cited shaft-speed profile supports it.

- **FR75 - ExperimentSpec and reference schedule.** A versioned
  `ExperimentSpec` shall declare operating phases, profile, run/seed identity,
  schedule, interventions, recovery, stopping rules, and evidence references.
  The requested 25%-75% variation shall be stored as
  `speed_reference_pct` or `capacity_reference_pct` with classification
  `preregistered_factor`. Ramp, dwell, repetition, and safety limits shall be
  sourced, measured, or separately preregistered; they shall not be inferred
  from the 25%-75% bounds.

- **FR76 - Parameter provenance gate.** Every executable v2 numeric parameter
  shall have a stable parameter ID and exactly one classification: `direct`,
  `derived`, `measured`, `preregistered_factor`, or `mock`. Its record shall
  contain value, unit, source or decision ID, exact locator, derivation,
  applicable profile, uncertainty/limitation where relevant, and authorized
  experiment. Anonymous legacy values may execute only in an explicitly
  labelled legacy-reproduction mode.

- **FR77 - Isolated truth.** `ScenarioTruth.v1`, attack labels, scenario names,
  interventions, future intervals, and evaluation-only metadata shall be stored
  under a separate access boundary and shall not appear in detector-facing
  training or inference contracts. The evaluator may join truth only after the
  declared evidence freeze.

### 6.2 Detector candidates and live syscall evidence

- **FR78 - Physical detector candidates.** The physical track shall compare an
  LSTM autoencoder, a GRU autoencoder, and declared simpler or classical
  baselines fitted only on qualified normal training evidence and using the
  same current-domain feature schema, complete-run partitions, evaluation
  budget, repetitions, and metrics. The current mixed-scale autoencoder remains
  a `LEGACY_BASELINE`; it is not the final detector and is not a dataset. The
  result mapping shall distinguish commanded 25%-75% operating transitions
  from separately declared anomalous interventions.

- **FR79 - Controlled Linux workload and authentic calls.** The custom syscall
  track shall run an allowlisted, controlled Linux edge workload that performs
  representative edge functions. Sysdig/eBPF or another qualified Linux kernel
  collector shall capture the calls the workload actually emits. The workload
  may be mocked; the syscalls themselves shall not be fabricated or modified.

- **FR80 - SyscallEventBatch.v1.** Captured custom syscall evidence shall use a
  versioned contract containing run, edge, boot, container/process/session,
  categorical syscall name and direction, sequence/timestamps, kernel/ABI and
  collector identities, loss/duplicate/gap/queue evidence, and raw-segment
  hashes. Labels and scenario truth shall be absent. Fixture replay shall be
  test-only and excluded from `PTFP-Custom-v1` evaluation.

- **FR81 - Syscall detector candidates.** The primary syscall anomaly track
  shall use categorical event semantics and compare embedding-plus-LSTM,
  embedding-plus-GRU, and an n-gram/STIDE-style transparent baseline fitted on
  qualified normal training evidence under the same group-safe protocol.
  Numeric syscall identifiers shall not be normalized as continuous quantities
  or optimized with reconstruction MSE solely because they are numbers.

### 6.3 External benchmarks and synchronized custom evidence

- **FR82 - ADFA-LD role.** The system shall treat ADFA-LD as an offline
  external syscall benchmark, preserve official roles, trace identity and six
  attack families, record source/archive hashes and known count discrepancies,
  use categorical semantics, and keep labels in evaluation truth. It shall not
  fabricate timestamps or execute dataset identifiers.

- **FR83 - LID-DS 2021 role.** The system shall implement a version-specific
  LID-DS 2021 adapter that preserves official training/validation/test and
  scenario/recording boundaries plus the published syscall schema. LID-DS may
  inform custom Docker/Sysdig capture design, but its example durations,
  collector settings, or reported metrics shall remain cited references rather
  than adopted project constants.

- **FR84 - HAI 23.05 role.** The system shall pin and verify HAI 23.05, preserve
  its native tags, units, chronology, official file roles, and separate labels,
  and use a version-specific physical/SCADA adapter. HAI preprocessing, model,
  calibration, and evaluation artifacts shall remain separate from custom and
  syscall artifacts. HAI shall not be mass-converted to mA or presented as a
  compressor dataset.

- **FR85 - PTFP-Custom-v1.** The system shall create a versioned custom dataset
  containing synchronized physical observations and captured Linux edge
  syscalls from the same experiment runs, with immutable stream manifests,
  correlation/clock evidence, modality quality, profile/config identities, and
  separately protected truth. Prototype-generated rows shall not be inserted
  into HAI or represented as ADFA-LD/LID-DS data.

### 6.4 Experimental protocol, fusion, and evidence presentation

- **FR86 - Leakage-safe lifecycle.** Complete official groups or independent
  custom runs shall be split before window formation. Preprocessing and
  vocabulary fitting shall use training evidence only; early stopping and
  threshold selection shall use declared validation/calibration evidence only;
  and locked test evidence shall remain unavailable until the model, feature
  schema, preprocessing, threshold, metrics, and evaluation policy are frozen.

- **FR87 - Immutable detector bundles.** Each evaluated or deployed detector
  shall bind model weights/architecture, feature order/schema or syscall
  vocabulary, preprocessing, training/calibration dataset and split hashes,
  frozen threshold and its derivation, dependency/runtime identity, and bundle
  hash. Loading or inference shall not call `fit` or recalculate the threshold.

- **FR88 - Protocol-appropriate evaluation.** Each track shall report all
  applicable point/window and event/range outcomes, including PR-AUC,
  precision, recall, F1, false-positive behavior, false events per operating
  hour, time to detection, confusion data where appropriate, threshold
  sensitivity, resource cost, modality availability/quality, and repeated-run
  dispersion or uncertainty. Unfavorable and aborted planned runs shall remain
  visible with their status and cause.

- **FR89 - Custom-only late fusion.** Physical and syscall detector scores may
  be fused only when produced for the same held-out `PTFP-Custom-v1` runs and
  aligned windows under frozen detector-specific calibration. Initial fusion
  policies shall be simple and preregistered before truth unlock. ADFA-LD or
  LID-DS syscall evidence shall never be concatenated or temporally joined with
  HAI physical rows to manufacture a fusion result.

- **FR90 - Independent OPC UA evidence.** The OPC UA server shall receive a
  pre-consensus plant/transmitter snapshot. A distinct client shall read the
  value through `opc.tcp` and preserve `DataValue` status, source/server
  timestamps, schema, and correlation. Invalid, stale, mixed, missing, or
  unavailable readings shall fail explicitly; the active v2 path shall not
  silently fall back to consensus projection.

- **FR91 - Current-domain consensus.** Consensus v2 shall declare the
  instrument profile and comparison basis. Redundant observations of the same
  profile may be compared in current domain; cross-profile or cross-sensor
  aggregation shall use documented dimensionless, uncertainty-aware residuals
  rather than anonymous physical-unit scales. Python and Go shall produce
  deterministic identical results from shared golden fixtures.

- **FR92 - Final result package.** Reporting shall produce separate result
  tables for ADFA-LD, LID-DS 2021, HAI 23.05, and each PTFP-Custom-v1 modality,
  followed by a paired custom-only physical/syscall/fusion ablation and a
  capability/limitation matrix. It shall not select a global champion across
  incompatible domains. Every claim shall link to source, version, split,
  model/bundle, threshold/calibration, run, raw score/metric, and limitation.

- **FR93 - Read-only evidence dashboard.** The dashboard shall display raw mA,
  normalized span, and engineering value as physical representations; physical,
  syscall, and fusion detector channels as distinct outputs; and dataset scope,
  provenance, quality, bundle, threshold origin, and limitations. It shall not
  import, split, train, calibrate, promote, fuse, relabel, or rewrite results.

## 7. Non-Functional Requirements

NFR38-NFR52 are the current August non-functional requirements after the
historical July inventory. Section 8.5 gives the binding individual
disposition of every NFR22-NFR37 identifier without renumbering it.

- **NFR38 - Semantic accuracy.** Contracts, logs, reports, and UI shall use the
  two-modality definition consistently and shall not call 4-20 mA a modality,
  an autoencoder a dataset, HAI compressor data, or controlled custom data
  real-plant evidence.

- **NFR39 - Numeric accountability.** Formal v2 startup or experiment
  validation shall reject any executable numeric parameter that lacks the
  complete FR76 record. A literature citation shall not establish transferability
  unless the cited value applies to the selected profile; measured and
  preregistered values shall be reported as such.

- **NFR40 - Reproducibility and immutability.** Formal results shall be
  reconstructible from immutable identities for code, dependencies, container
  images, sources, datasets, profiles, configuration, splits, schemas, bundles,
  scores, truth-unlock record, fusion policy, and evaluation code.

- **NFR41 - Leakage resistance.** No detector-facing artifact shall contain
  truth, attack labels, future values, unauthorized partitions, or windows that
  cross run, trace, scenario, file, boot, session, process, gap, or official
  dataset boundaries.

- **NFR42 - OT safety and authority separation.** Control and experiment
  scheduling shall remain independent from security analytics. Detector,
  dashboard, storage, MQTT, OPC UA, capture, or evaluator failure shall never
  create or change an actuator/compressor command.

- **NFR43 - Fair candidate comparison.** LSTM, GRU, and baseline comparisons
  within one track shall use the same eligible data partitions, input schema,
  tuning access, declared budget, repetitions, and primary metrics. Model
  superiority shall be a measured outcome, not a requirement premise.

- **NFR44 - No universal threshold assumption.** Anomaly thresholds, window
  sizes, run duration, repetitions, ramp/dwell, queue/buffer capacity, capture
  loss tolerance, fusion weights, and performance targets shall be sourced for
  the selected profile, measured in a preserved pilot, or preregistered with
  sensitivity analysis. No reviewed publication is treated as supplying a
  universally valid value for these decisions.

- **NFR45 - Capture quality.** Custom syscall evidence shall expose workload
  attribution, collector/kernel identity, gaps, duplicates, drops, queue depth,
  storage lag, and measured overhead. Affected windows shall be flagged or
  invalidated by the preregistered policy rather than silently treated as
  normal.

- **NFR46 - Temporal and correlation integrity.** Every custom stream shall
  preserve source/observation time, ordered sequence, run/edge/boot/session
  identity, and declared clock/correlation uncertainty sufficient to prove a
  physical-syscall join. Unresolved or mixed identities shall prevent fusion.

- **NFR47 - Resource isolation and explicit failure.** Acquisition/control
  shall remain available when storage or analytics is degraded. High-volume
  syscall evidence shall use bounded queues and append-only segments; missing,
  partial, delayed, or aborted evidence shall be explicit rather than hidden.

- **NFR48 - Versioned compatibility.** v1 evidence shall remain replayable.
  v2 contracts, consensus state, storage namespaces, and model bundles shall be
  explicitly versioned. A v1 model shall not load against v2 features, and
  incompatible schemas or hashes shall fail closed.

- **NFR49 - Durable evidence storage.** Formal evidence shall use persistent,
  verified, restorable storage and append-only or content-addressed object keys.
  Mutable latest-only state shall not be the sole record of a scientific run.

- **NFR50 - End-to-end traceability.** A reported decision or metric shall
  resolve from experiment and source identities through raw segments,
  canonical observations, partitions/windows, bundle, score, truth join, and
  evaluation record without relying on a dashboard or hidden local state.

- **NFR51 - Complete scientific reporting.** All planned valid, invalid,
  aborted, and unfavorable runs shall be retained and reported with applicable
  uncertainty, resource/quality evidence, limitations, and the distinction
  between locally measured and externally published results.

- **NFR52 - Authorization boundary.** Planning approval shall be machine- and
  human-readable as distinct from implementation, training, dataset
  acquisition, syscall capture, and experiment authorization. No downstream
  workflow shall treat this overlay as permission to perform those actions.

## 8. Old-to-New and Supersession Traceability

### 8.1 Base PRD (`prd.md`)

| Prior item | Disposition | Controlling replacement or clarification |
| --- | --- | --- |
| Executive Summary, Reality Boundary, Success Criteria, MVP and journeys describing an LSTM-only normal-data fingerprint | AMEND | Sections 2-5; FR72, FR78, FR81, FR92; LSTM and GRU are candidates with baselines |
| FR1-FR2 sensor simulation/acquisition | AMEND | FR73-FR76; internal physics remains in engineering units while the custom edge preserves primary current-domain evidence |
| FR3-FR14 MQTT/shared state/consensus history | RETAIN/AMEND | Retained behavior is subject to versioned Signal v2, FR91, and NFR39-NFR50 |
| FR15-FR17 fake SCADA comparison | SUPERSEDE | FR90 creates an independent pre-consensus OPC UA source and real client; circular consensus projection is invalid for v2 evidence |
| FR18 valid-data persistence | AMEND | FR85, FR87, FR92 and NFR40/NFR49 require immutable, role-separated evidence rather than one ambiguous valid artifact |
| FR19-FR23 LSTM fingerprint and replay detection | SUPERSEDE | FR77-FR89 define isolated truth, candidate models, calibrated bundles, controlled anomalies, and custom-only fusion; the old autoencoder is legacy evidence |
| NFR1 fixed one-minute reference | AMEND | NFR39/NFR44; cadence is sourced, measured, or preregistered for each declared use rather than treated as universally valid |
| NFR3-NFR5 validation/trust and two distinct alert paths | AMEND | NFR41-NFR42 plus FR90-FR93; truth isolation and physical/syscall/fusion outputs are explicit without granting control authority |
| NFR11 LSTM service integration | SUPERSEDE | FR78/FR81 and NFR43 require detector candidates and baselines; no model family is preselected as universally superior |

### 8.2 May PRD overlay (`prd-update-2026-05-21.md`)

| Prior item | Disposition | Controlling replacement or clarification |
| --- | --- | --- |
| May deprecation of normal-only autoencoder training | SUPERSEDE | FR78 preserves v1 as legacy and evaluates new LSTM-AE/GRU-AE candidates on the physical track |
| FR24 generic offline benchmark track | AMEND | FR82-FR84 give ADFA-LD, LID-DS 2021, and HAI 23.05 different modality-specific roles |
| FR25 stratified 80/20 sample split | SUPERSEDE | FR86 and NFR41 require official/group/run split before windows; no generic random sample split controls all datasets |
| FR26 architecture/hyperparameter recording | RETAIN/AMEND | FR87, FR88 and NFR40 bind the complete preprocessing/calibration/runtime bundle and evaluation evidence |
| FR27 supervised classification metrics | SUPERSEDE | FR77, FR78, FR81, FR86 and FR88 establish normal-only anomaly candidates, evaluation-only labels, temporal/event metrics, and uncertainty |
| FR28 shared training-history prefix | AMEND | FR87, FR92 and NFR49 require immutable role/version namespaces and complete evidence, not a mutable shared directory convention |
| FR29 supervised ADFA/LID classifier reintegration | SUPERSEDE | External models never become compressor models; only compatible custom bundles may run in their same modality, and fusion is governed by FR89 |
| Modified FR23 replay via supervised classifier | SUPERSEDE | Replay/freeze is an evaluation scenario with isolated truth; neither external HIDS labels nor one fixed classifier defines the physical result |
| NFR18-NFR21 reproducibility/history/runtime separation/provenance | RETAIN/AMEND | NFR40, NFR47, NFR49-NFR51 strengthen immutable reconstruction, quality, roles, and limitations |

### 8.3 July planning overlays

This section applies to `sprint-change-proposal-2026-07-28.md` and the
requirements inventory in `epics-update-2026-07-30.md`. The unimplemented July
Epic 9-16 sequence is superseded by the approved August Epic 9-18 plan.

The table below is a thematic historical summary only. The one-row-per-
identifier matrices in Sections 8.4 and 8.5 are binding wherever a grouped
summary could otherwise permit more than one interpretation.

| July item | Disposition | Controlling replacement or clarification |
| --- | --- | --- |
| Physical/HIDS separation and independent OPC UA direction | AMEND | FR72 and FR90 preserve the separation while adding the synchronized custom fusion boundary |
| July FR19-FR23 custom autoencoder/fingerprint | AMEND | FR78, FR86-FR88; autoencoder remains a model candidate, v1 is legacy, and no threshold is universal |
| July FR24 generic ADFA/LID/HAI/custom benchmark envelope | SUPERSEDE | FR82-FR85 keep dataset-native adapters and roles; only evaluation records are common |
| July FR25 and FR39 group-first splitting | AMEND | FR86 and NFR41 preserve group-before-windowing and add truth/test freeze requirements |
| July FR33 `ProcessSample` boundary | SUPERSEDE | FR73-FR74 establish `SignalObservation.v2`, current-domain edge evidence, and profile-owned engineering derivation |
| July FR34-FR41 custom physical dataset v2 | AMEND | FR75-FR77 and FR85 extend the custom dataset to synchronized physical and real captured syscall evidence |
| July fixed scenario, seed, split, threshold, or repetition numbers | SUPERSEDE | FR76 and NFR39/NFR44 require direct, derived, measured, preregistered, or mock provenance; legacy values do not migrate automatically |
| July HAI 20.07 (FR55-FR58/Epic 13) | SUPERSEDE | FR84 pins HAI 23.05 as the initial external physical benchmark and preserves its native representation |
| July LID single-subset/optional-path framing (FR59-FR64/Epic 14) | AMEND | FR83 requires an official-schema LID-DS 2021 benchmark role; actual executable scope remains declared by the later authorized protocol |
| July FR65-FR67 common evaluation and evidence index | AMEND | FR88 and FR92 retain common reporting while prohibiting a global cross-domain champion |
| July FR68-FR71 dashboard | AMEND | FR93 makes all scientific behavior read-only and corrects modality/representation language |
| July 25%-75% operating variation | AMEND | FR75 classifies it as a preregistered speed/capacity-reference factor, not power or a universal range |
| July HIDS-only offline evidence | AMEND | FR79-FR85 add real captured edge syscalls and synchronized `PTFP-Custom-v1`; external datasets remain offline benchmarks |

### 8.4 Binding FR30-FR71 Dispositions

Each row below gives exactly one binding disposition. A controller list is
conjunctive: the retained intent is governed by all named requirements and by
the stated effect. A `RETAIN` row keeps the complete July sentence at
`epics-update-2026-07-30.md`, Section "Requirements Inventory," normative.

| July ID | July intent | Binding disposition | Controlling effect |
| --- | --- | --- | --- |
| FR30 | Capture a v1 golden baseline across runtime, contracts, artifacts, dashboard state, and experimental fingerprint behavior. | RETAIN | The complete July FR30 remains normative and preserves the pre-v2 evidence baseline. |
| FR31 | Classify datasets and runs by controlled provenance tier and result role. | RETAIN | The complete July FR31 remains normative; its categories supplement, but cannot override, the source-specific roles and semantic boundary in this overlay. |
| FR32 | Prevent fixtures or published statistics from being represented as measured execution results. | RETAIN | The complete July FR32 remains normative for every result and presentation path. |
| FR33 | Use one canonical `ProcessSample` contract across batch, runtime, consensus, and OPC UA. | SUPERSEDE -> FR73, FR74 | `SignalObservation.v2` and profile-owned derivation replace `ProcessSample` as the custom physical evidence boundary; OPC UA has its separate FR90 contract. |
| FR34 | Declare controlled experiments through `ExperimentSpec`. | AMEND -> FR75, FR76, FR77 | `ExperimentSpec` remains, but its schedule, numeric parameters, interventions, and truth must follow provenance and truth-isolation controls. |
| FR35 | Generate accelerated custom sessions from the deterministic simulator core while bypassing live integrations per sample. | AMEND -> FR74, FR75, FR85, NFR46 | Acceleration may support declared physical-only or test evidence, but it is not eligible as final `PTFP-Custom-v1` fusion evidence unless physical and authentic syscall streams originate from the same correlated run. |
| FR36 | Generate ground truth independently and exclude it from model features. | AMEND -> FR77, FR86, NFR41 | Truth must be structurally isolated from all training and inference contracts and joined only after the declared freeze. |
| FR37 | Include operating context, units, and correctly derived rates in the custom feature schema. | AMEND -> FR73, FR74, FR75, FR78 | Signal representations and derivatives must be profile-owned and evidence-referenced; commanded context must be distinguished from protected intervention truth before detector eligibility. |
| FR38 | Execute a preregistered scenario matrix and preserve every run. | AMEND -> FR75, FR76, FR77, FR88, NFR51 | Scenario choices and numeric factors require declared provenance; all valid, invalid, aborted, and unfavorable outcomes remain reportable without exposing truth to detectors. |
| FR39 | Split complete sessions or seeds before window formation and prevent boundary-crossing windows. | AMEND -> FR86, NFR41 | The rule extends to every official group and custom run, including file, trace, boot, session, process, gap, and schema boundaries. |
| FR40 | Publish immutable artifacts with verified hashes and publish the complete manifest last. | AMEND -> FR85, NFR40, NFR49, NFR50 | The manifest-last atomic publication rule remains mandatory within the immutable, reconstructible evidence chain. |
| FR41 | Qualify or reject the custom dataset through the `DATASET_QUALIFIED` gate. | AMEND -> FR85, FR86, NFR40, NFR41, NFR45, NFR46, NFR49, NFR51 | `DATASET_QUALIFIED` remains the gate name; it closes only after synchronized-stream, leakage, capture-quality, correlation, durability, and complete-reporting checks pass. |
| FR42 | Publish a pre-consensus plant snapshot through OPC UA. | AMEND -> FR90, NFR42 | The snapshot remains causally pre-consensus and cannot grant analytics or supervision actuator authority. |
| FR43 | Read OPC UA through an independent `opc.tcp` client. | AMEND -> FR90 | The distinct client and network-boundary read are mandatory; internal server-object access is not eligible evidence. |
| FR44 | Preserve OPC UA values, status, timestamps, schema, producer, revision, and correlation. | AMEND -> FR90, NFR46, NFR50 | The complete `DataValue` and identity chain must support temporal correlation and end-to-end reconstruction. |
| FR45 | Reject incomplete, stale, mixed, invalid, unavailable, or mis-correlated OPC UA snapshots. | AMEND -> FR90, NFR47 | Every listed invalid state fails explicitly; timing and availability policies remain sourced, measured, or preregistered. |
| FR46 | Consume only eligible OPC UA observations and preserve comparison diagnostics. | AMEND -> FR90, FR92, NFR50 | The observation and every fail-closed diagnostic become traceable evidence linked to the final result package. |
| FR47 | Prove OPC and consensus source independence through a causal round-trip test. | AMEND -> FR90, NFR50 | The branch-isolation test remains required and its evidence must be reconstructible from the source snapshot through the comparison result. |
| FR48 | Enable independent OPC mode through an initially disabled feature flag with no silent fallback. | AMEND -> FR90, NFR48, NFR52 | Brownfield activation remains explicit and versioned; when enabled, missing or incompatible independent evidence fails closed and never falls back to consensus projection. |
| FR49 | Fit preprocessing on normal training evidence, select models on validation evidence, and calibrate independently. | AMEND -> FR86, NFR41, NFR43, NFR44 | All candidates use the same leakage-safe partition access and declared comparison budget; calibration choices require recorded provenance. |
| FR50 | Freeze the calibrated threshold before test and bind its origin to the model bundle. | AMEND -> FR87, NFR44 | The threshold and derivation are immutable bundle evidence and cannot be recalculated during loading or inference. |
| FR51 | Reject stale or incompatible detector candidates when any governing identity changes. | AMEND -> FR87, NFR48 | Complete bundle and schema identities control compatibility; mismatches fail closed. |
| FR52 | Report scenario-, severity-, sensor-, regime-, and repetition-aware evaluation metrics. | AMEND -> FR88, NFR43, NFR51 | Only protocol-applicable metrics are required, under fair candidate budgets with dispersion, unfavorable results, and limitations retained. |
| FR53 | Promote only qualified and validated custom bundles and support verified rollback. | AMEND -> FR87, NFR48, NFR52 | Promotion and rollback must select an explicitly identified compatible immutable bundle and require separate activity authorization; planning approval cannot promote a model. |
| FR54 | Load a promoted custom bundle for inference-only shadow operation without retraining or latest-artifact guessing. | AMEND -> FR87, NFR47, NFR48 | Loading is inference-only, explicit, resource-isolated, and fail-closed on absent or incompatible bundle identity. |
| FR55 | Acquire and verify HAI 20.07 outside adapter loading. | SUPERSEDE -> FR84, NFR40 | HAI 23.05 replaces HAI 20.07; its official version, files, source, license/citation, sizes, and hashes must be pinned and reconstructible before adapter use. |
| FR56 | Stream HAI 20.07 while preserving official roles, chronology, and boundaries. | SUPERSEDE -> FR84, FR86, NFR47 | HAI 23.05 native roles and chronology replace the older version; processing remains group-safe, bounded, and isolated from active acquisition. |
| FR57 | Keep HAI 20.07 preprocessing, model, threshold, and evaluation dataset-specific. | SUPERSEDE -> FR84, FR87, FR88 | HAI 23.05 receives a separate immutable preprocessing, bundle, calibration, and protocol-appropriate evaluation path. |
| FR58 | Report HAI 20.07 as external physical evidence, not compressor validation. | SUPERSEDE -> FR84, FR92, NFR38 | HAI 23.05 replaces the version while preserving native physical/SCADA scope and the prohibition on compressor-validation claims. |
| FR59 | Distinguish fixture, published-reference, and official-real LID evidence. | AMEND -> FR83, FR92, NFR51 | Only qualified official LID evidence may support a locally measured LID result; other roles remain explicitly labelled and separated. |
| FR60 | Validate the official LID-DS 2021 source and a preregistered subset. | AMEND -> FR83, NFR40, NFR50 | Official acquisition must inventory version, layout, citation, license scope, files, sizes, and hashes; no specific subset becomes mandatory until an authorized protocol declares it. |
| FR61 | Select the declared LID scope, consume the official layout, and prohibit fixture fallback. | AMEND -> FR83, NFR47 | The adapter must preserve official schema and boundaries, reject ambiguous or empty sources, and never substitute a fixture; `CVE-2017-7529` is not a default requirement. |
| FR62 | Split LID by official role or complete trace before windowing. | AMEND -> FR83, FR86, NFR41 | Official roles, scenarios, recordings, traces, and sessions remain isolated before vocabulary fitting or window creation. |
| FR63 | Complete a reproducible measured run on a fixed LID subset with predefined repetitions. | AMEND -> FR83, FR86, FR88, NFR43, NFR44, NFR51 | Dataset scope, run count, stopping rules, and comparison budget come from a later authorized protocol; every executed outcome and limitation remains reportable. |
| FR64 | Keep published LID metrics cited and outside local training or selection. | AMEND -> FR83, FR86, FR92, NFR51 | Published results remain reference-only and cannot influence fitting, calibration, selection, or local measured-result calculations. |
| FR65 | Produce a common provenance-rich `EvaluationRecord`. | AMEND -> FR88, FR92, NFR40, NFR50 | The common record covers applicable metrics and immutable claim-to-raw-evidence identities without erasing dataset-specific semantics. |
| FR66 | Produce separate modality result tables and a cross-domain limitation matrix without a global champion. | AMEND -> FR92, NFR38 | Results remain dataset- and modality-bound; only the paired custom ablation may compare physical, syscall, and fusion outcomes on the same runs. |
| FR67 | Link every academic claim through a claim-to-evidence index. | AMEND -> FR92, NFR50, NFR51 | Each claim must resolve through immutable source, split, bundle, threshold, run, metric, limitation, and scientific-status evidence. |
| FR68 | Display custom detector identity, decision evidence, operating context, and OPC integrity. | AMEND -> FR93, FR92, NFR50, NFR52 | The dashboard may display only frozen evidence and cannot create, recompute, promote, or alter any scientific artifact. |
| FR69 | Display HAI, ADFA-LD, and LID results with provenance and limitations. | AMEND -> FR93, FR92, NFR38, NFR51 | Dataset-native scope, evidence role, result role, version, run, and limitations must remain visible and semantically distinct. |
| FR70 | Present consensus, OPC, SCADA-divergence, replay/freeze, and ML anomaly as distinct states. | AMEND -> FR93, NFR38, NFR42 | Those states remain distinct; physical, syscall, and fusion detector channels also remain separate and none gains control authority. |
| FR71 | Demonstrate a preregistered custom anomaly without mutating scientific evidence. | AMEND -> FR93, FR75, FR87, NFR52 | The dashboard may replay or present only an already authorized, preregistered, frozen result; it cannot generate data, fit, calibrate, promote, or rewrite evidence. |

### 8.5 Binding NFR22-NFR37 Dispositions

| July ID | July intent | Binding disposition | Controlling effect |
| --- | --- | --- | --- |
| NFR22 | Preserve v1 compatibility when v2 feature flags are disabled. | AMEND -> NFR40, NFR48 | Historical evidence remains replayable through explicit versions and identities; incompatible v1/v2 artifacts fail closed. |
| NFR23 | Publish immutable verified bulk artifacts before their complete manifest or promotion pointer. | AMEND -> NFR40, NFR49, NFR50 | Content-addressed artifacts must verify before the complete manifest or pointer is atomically published, preserving full reconstruction. |
| NFR24 | Permit zero partition leakage across sessions, files, traces, or overlapping windows. | AMEND -> NFR41 | Zero detector-facing leakage applies to every official and custom boundary enumerated by NFR41. |
| NFR25 | Process HAI imports and custom generation with bounded memory or sharding. | AMEND -> FR84, FR85, NFR47 | The bounded-memory/sharded constraint remains mandatory for HAI and custom evidence; resource pressure must not degrade acquisition or hide partial evidence. |
| NFR26 | Keep credentials and private keys outside evidence and treat imported fields as untrusted. | RETAIN | The complete July NFR26 remains normative for source acquisition, parsing, storage, and reporting. |
| NFR27 | Reject every invalid OPC observation within one live cycle. | AMEND -> FR90, NFR39, NFR44, NFR47 | Every listed invalid observation must be rejected explicitly; the unsupported one-cycle limit is removed and any timing target requires parameter provenance or preregistration. |
| NFR28 | Use fixed initial FPR, false-event, and detection-repetition targets. | SUPERSEDE -> FR76, FR88, NFR39, NFR44, NFR51 | The 5%, one-false-event-per-hour, and four-of-five values do not enter v2 automatically; they may return only through a complete sourced, measured, or preregistered decision record, with all outcomes reported. |
| NFR29 | Require zero-cost, immediately actionable datasets and restrict redistribution. | AMEND -> FR82, FR83, FR84, NFR40, NFR52 | Zero-cost and redistribution safeguards remain; actionability depends on official-source, version, checksum, license-scope, and authorization qualification, and unresolved LID access cannot block ADFA-LD. |
| NFR30 | Prohibit invalid cross-domain and real-plant scientific claims. | AMEND -> NFR38, FR84, FR92 | The two-modality vocabulary, HAI native role, custom-data limitation, dataset scope, and no-global-champion rule control all claims. |
| NFR31 | Isolate active v1 runtime from offline import, training, and reporting failures. | AMEND -> NFR47, NFR48 | Acquisition/control availability and v1 replayability remain independent of degraded or failed offline evidence work. |
| NFR32 | Keep the dashboard read-only over scientific evidence and promotion. | AMEND -> FR93, NFR42, NFR52 | The dashboard has presentation-only authority and cannot mutate evidence, analytics, authorization, or actuator commands. |
| NFR33 | Load promoted bundles without refitting and reject missing or incompatible artifacts. | AMEND -> FR87, NFR48 | Complete immutable bundle identity is required; load and inference cannot fit, recalibrate, guess, or accept mismatched schemas or hashes. |
| NFR34 | Require equivalent batch and live results for the same canonical sample. | AMEND -> FR73, FR74, FR87, NFR39, NFR44 | Canonical conversion, tensor, score, and explanation equivalence remains required; its numerical tolerance must have a complete provenance or preregistration record. |
| NFR35 | Pass regression and new quality gates before enabling v2 by default. | RETAIN | The complete July NFR35 remains normative; passing tests does not itself authorize implementation or activation. |
| NFR36 | Report repeated-run dispersion or uncertainty for every final metric. | AMEND -> FR88, NFR51 | Every applicable final metric includes repeated-run dispersion or uncertainty and cannot report only the best seed or selected outcome. |
| NFR37 | Preserve exploratory anomalies and prior results as historical evidence without relabelling. | AMEND -> NFR40, NFR48, NFR51 | May/June and v1 artifacts retain immutable historical identities and cannot be represented as final custom-v2 or official-dataset results. |

## 9. Requirement-to-Revised-Epic Allocation

| Revised epic | Principal requirements |
| --- | --- |
| Epic 9 - Evidence-safe baseline and provenance | FR76, FR86-FR88; NFR39-NFR41, NFR48-NFR52 |
| Epic 10 - Current-domain signal and experiment control | FR73-FR77, FR85; NFR38-NFR42, NFR46, NFR50 |
| Epic 11 - Current-domain consensus | FR91; NFR39, NFR46, NFR48, NFR50 |
| Epic 12 - Independent OPC UA | FR90; NFR41, NFR42, NFR46-NFR50 |
| Epic 13 - Physical detector v2 | FR78, FR86-FR88; NFR40-NFR44, NFR48-NFR51 |
| Epic 14 - Real custom syscalls | FR79-FR81, FR85-FR88; NFR41-NFR47, NFR50 |
| Epic 15 - ADFA-LD and LID-DS 2021 | FR81-FR83, FR86-FR88; NFR38-NFR45, NFR50-NFR51 |
| Epic 16 - HAI 23.05 | FR78, FR84, FR86-FR88; NFR38-NFR44, NFR50-NFR51 |
| Epic 17 - Synchronized dataset, long runs, fusion and matrix | FR72, FR85-FR89, FR92; NFR38-NFR51 |
| Epic 18 - Read-only evidence dashboard | FR72, FR92-FR93; NFR38, NFR42, NFR50-NFR52 |

### 9.1 Historical Identifier Resolution

FR30-FR71 and NFR22-NFR37 are not assigned new identifiers. An amended or
superseded identifier follows every controlling requirement named in Sections
8.4 and 8.5 and the corresponding revised-epic allocation above. A retained
identifier remains normative and must be cited explicitly by its implementing
revised epic or story before implementation authorization. The superseded July
Epic 9-16 sequence supplies historical context, not implementation authority.

## 10. Source Basis

The requirements above use the controlling research and the local
`docs/reference-archive/` catalog. Primary official links include:

- `epics-update-2026-07-30.md`, Section "Requirements Inventory" - historical
  source and exact locator for FR30-FR71 and NFR22-NFR37; those identifiers are
  incorporated only through the binding dispositions in Sections 8.4 and 8.5,
  while the July Epic 9-16 sequence remains superseded;

- [Rockwell PointMax Analog I/O Modules User Manual](https://literature.rockwellautomation.com/idc/groups/literature/documents/um/5034-um003_-en-p.pdf) - electrical-to-engineering scaling and 4/12/20 mA examples;
- [NI 4-20 mA scaling guidance](https://knowledge.ni.com/KnowledgeArticleDetails?id=kA00Z000000PASfSAO) - two-endpoint linear scaling;
- [Electro-Sensors FB420 official product page](https://www.electro-sensors.com/products/shaft-speed-sensors/fb420) - programmable 4 mA and 20 mA RPM endpoints;
- [UNSW ADFA IDS datasets](https://research.unsw.edu.au/projects/adfa-ids-datasets) - official dataset owner and academic-use boundary;
- [Official LID-DS repository](https://github.com/LID-DS/LID-DS) and [LID-DS recording framework](https://github.com/LID-DS/LID-DS/wiki/LID-DS-Recording-Framework%3A-Documentation-and-Installation) - versioned syscall benchmark and Docker/Sysdig methodological precedent;
- [Official HAI repository](https://github.com/icsdataset/hai) and [HAI 23.05 files](https://github.com/icsdataset/hai/tree/master/hai-23.05) - versioned physical/SCADA benchmark;
- [OPC UA DataValue](https://reference.opcfoundation.org/Core/Part4/v105/docs/7.11) - status and source/server timestamp semantics;
- [LSTM original paper](https://doi.org/10.1162/neco.1997.9.8.1735), [GRU original paper](https://aclanthology.org/D14-1179/), and [empirical RNN comparison](https://proceedings.mlr.press/v37/jozefowicz15.html) - temporal-model candidacy without a universal winner;
- [NIST AI RMF Measure](https://airc.nist.gov/airmf-resources/airmf/5-sec-core/) - documented test sets, metrics, uncertainty, benchmark comparison, and repeatable TEVV; and
- [NIST SP 800-82 Rev. 3](https://csrc.nist.gov/pubs/sp/800/82/r3/final) - OT performance, reliability, safety, component, and flow considerations.

## 11. Approval Status and Next Decision

- **Source change proposal:** approved by Emilio on 2026-08-15.
- **This overlay's scope:** translation of that approval into PRD planning.
- **Planning status:** approved-change overlay, ready for architecture and epic
  alignment review.
- **Implementation:** not authorized.
- **Dataset acquisition:** not authorized.
- **Model training or promotion:** not authorized.
- **Syscall capture or workload execution:** not authorized.
- **Experiment campaign or long run:** not authorized.
- **Requirement-authority amendment:** planning alignment only; it grants no
  implementation, acquisition, training, promotion, capture, workload, or
  experiment authority.
- **Next planning gate:** create the bounded Epic 18 UX specification, update
  the revised epic/story coverage to cite Sections 8.4 and 8.5, then rerun
  implementation readiness. Implementation remains blocked unless that review
  returns `READY` and a separate activity-specific authorization is recorded.

Any of those execution activities requires a separate explicit authorization
after the PRD, architecture, epic/story, and readiness artifacts are aligned.
