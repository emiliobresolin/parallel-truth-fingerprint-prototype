---
stepsCompleted:
  - step-01-document-discovery
  - step-02-prd-analysis
  - step-03-epic-coverage-validation
  - step-04-ux-alignment
  - step-05-epic-quality-review
  - step-06-final-assessment
includedFiles:
  prd:
    - _bmad-output/planning-artifacts/prd.md
    - _bmad-output/planning-artifacts/prd-update-2026-05-21.md
    - _bmad-output/planning-artifacts/prd-update-2026-08-15.md
  architecture:
    - _bmad-output/planning-artifacts/architecture.md
    - _bmad-output/planning-artifacts/architecture-update-2026-05-21.md
    - _bmad-output/planning-artifacts/architecture-update-2026-08-15.md
  epics:
    - _bmad-output/planning-artifacts/epics.md
    - _bmad-output/planning-artifacts/epics-update-2026-05-21.md
    - _bmad-output/planning-artifacts/epics-update-2026-07-30.md
    - _bmad-output/planning-artifacts/epics-update-2026-08-15.md
  ux: []
status: needs-work
overall_readiness: NEEDS_WORK
assessed_by: Codex using BMAD implementation-readiness workflow
assessment_completed: 2026-08-15
---

# Implementation Readiness Assessment Report

**Date:** 2026-08-15
**Project:** parallel-truth-fingerprint-prototype

## Step 1 — Document Discovery

The document inventory was confirmed by Emilio on 2026-08-15.

### PRD Documents

| Document | Size (bytes) | Role |
| --- | ---: | --- |
| `prd.md` | 35,827 | Base historical PRD |
| `prd-update-2026-05-21.md` | 5,964 | Earlier overlay, applicable where not superseded |
| `prd-update-2026-08-15.md` | 32,947 | Controlling PRD overlay for the revised plan |

### Architecture Documents

| Document | Size (bytes) | Role |
| --- | ---: | --- |
| `architecture.md` | 45,234 | Base historical architecture |
| `architecture-update-2026-05-21.md` | 8,168 | Earlier overlay, applicable where not superseded |
| `architecture-update-2026-08-15.md` | 26,351 | Controlling architecture overlay for the revised plan |

### Epics and Stories Documents

| Document | Size (bytes) | Role |
| --- | ---: | --- |
| `epics.md` | 61,528 | Historical Epics 1–8 and base backlog |
| `epics-update-2026-05-21.md` | 8,673 | Earlier historical overlay |
| `epics-update-2026-07-30.md` | 42,442 | Superseded plan retained for traceability checks |
| `epics-update-2026-08-15.md` | 54,169 | Controlling revised Epics 9–18 |

### UX Documents

No dedicated UX design artifact was found. This is recorded as a warning for
the assessment. The absence is not treated as resolved merely because the
dashboard is planned as a read-only evidence surface.

### Duplicate and Selection Resolution

No conflicting whole-versus-sharded document formats were found. Dated files
are treated as overlays rather than accidental duplicates. The August 15
overlays control on conflict; base and earlier overlays remain in scope for
historical and supersession validation.

## Step 2 — PRD Analysis

The base PRD and both dated PRD overlays were read in full. Requirements below
retain their complete normative meaning and their effective disposition under
the controlling August overlay.

### Functional Requirements

#### Base requirements retained for historical and supersession traceability

- **FR1 — AMEND:** The system can simulate 3 sensors of one compressor.
- **FR2 — AMEND:** Each edge can collect only its local sensor.
- **FR3 — RETAIN/AMEND:** Each edge can publish data to MQTT.
- **FR4 — RETAIN/AMEND:** Each edge can consume data from the other edges.
- **FR5 — RETAIN/AMEND:** The system can maintain a shared view of the compressor.
- **FR6 — RETAIN/AMEND:** The system can execute Byzantine consensus between the edges.
- **FR7 — RETAIN/AMEND:** The consensus can produce trust ranking and this must be included in the package that goes to the bucket.
- **FR8 — RETAIN/AMEND:** The system can exclude a suspicious edge from the round.
- **FR9 — RETAIN/AMEND:** The system can expose the participating edges in each consensus round.
- **FR10 — RETAIN/AMEND:** The system can expose the excluded edges in each consensus round and the reason for exclusion.
- **FR11 — RETAIN/AMEND:** The system can expose the resulting trust ranking for all edges in the round.
- **FR12 — RETAIN/AMEND:** The system can explicitly indicate when a valid consensus cannot be achieved.
- **FR13 — RETAIN/AMEND:** The system can generate structured logs describing each consensus round.
- **FR14 — RETAIN/AMEND:** The system can generate alerts when consensus fails.
- **FR15 — SUPERSEDED:** The system can expose a fake SCADA in OPC UA.
- **FR16 — SUPERSEDED:** The system can execute sensor-by-sensor comparison with tolerance.
- **FR17 — SUPERSEDED:** The system can generate an alert when SCADA diverges from the consensused physical state.
- **FR18 — AMEND:** The system can persist valid data in local storage (bucket).
- **FR19 — SUPERSEDED:** The system can train an LSTM using normal data.
- **FR20 — SUPERSEDED:** The system can generate an equipment fingerprint.
- **FR21 — SUPERSEDED:** The system can generate anomaly score and normal/anomalous class.
- **FR22 — SUPERSEDED:** The system can save the model/fingerprint.
- **FR23 — SUPERSEDED:** The system can detect a replay scenario.

#### May overlay requirements retained for historical and supersession traceability

- **FR24 — AMEND:** The system must provide a training execution path that runs offline, outside the live runtime loop, against public benchmark datasets. The track must support ADFA-LD as the first benchmark and LID-DS 2021 as the second benchmark. Adding a new benchmark must be a localized change through one adapter module.
- **FR25 — SUPERSEDED:** Every offline training run must use a stratified 80% train / 20% test split with an explicit `random_seed`. The split must be reproducible given the seed and the dataset version.
- **FR26 — RETAIN/AMEND:** Every offline training run must persist model architecture, layers, units, dropout, learning rate, batch size, optimizer, loss, planned and executed epochs, and model parameter count.
- **FR27 — SUPERSEDED:** Every offline training run must compute and persist macro F1, per-class F1, accuracy, precision, recall, false positive rate, and confusion matrix.
- **FR28 — AMEND:** The system must persist all training records under a dedicated history store, with one JSON document and one model artifact per run, supporting lookup by dataset and run ID.
- **FR29 — SUPERSEDED:** A supervised classifier may be attached to live runtime inference only after offline metrics clear a declared reintegration bar, while training remains outside the runtime loop.

#### Controlling August requirements

- **FR72 — Two-modality semantic boundary:** The system shall represent only physical instrumentation and Linux host syscalls as detection modalities. Documentation, schemas, reports, and UI shall identify 4-20 mA as a physical representation and autoencoders as models.
- **FR73 — `SignalObservation.v2`:** Each custom edge observation shall preserve raw current in mA, current quality/diagnostics, instrument and profile identity, source and observation timestamps, sequence/correlation identity, deterministic normalized span, derived engineering value/unit, schema version, and parameter-evidence references. Signal quality shall be evaluated before any optional clipping or imputation.
- **FR74 — Profile-owned derivation and physics:** The process model may calculate temperature, pressure, and RPM in engineering units, but the edge shall receive its primary physical evidence through the selected transmitter profile. One profile-owned conversion shall derive normalized span and engineering value from the electrical observation; consumers shall not redefine that conversion independently. RPM shall remain 4-20 mA while the selected cited shaft-speed profile supports it.
- **FR75 — `ExperimentSpec` and reference schedule:** A versioned `ExperimentSpec` shall declare operating phases, profile, run/seed identity, schedule, interventions, recovery, stopping rules, and evidence references. The requested 25%-75% variation shall be stored as `speed_reference_pct` or `capacity_reference_pct` with classification `preregistered_factor`. Ramp, dwell, repetition, and safety limits shall be sourced, measured, or separately preregistered; they shall not be inferred from the 25%-75% bounds.
- **FR76 — Parameter provenance gate:** Every executable v2 numeric parameter shall have a stable parameter ID and exactly one classification: `direct`, `derived`, `measured`, `preregistered_factor`, or `mock`. Its record shall contain value, unit, source or decision ID, exact locator, derivation, applicable profile, uncertainty/limitation where relevant, and authorized experiment. Anonymous legacy values may execute only in an explicitly labelled legacy-reproduction mode.
- **FR77 — Isolated truth:** `ScenarioTruth.v1`, attack labels, scenario names, interventions, future intervals, and evaluation-only metadata shall be stored under a separate access boundary and shall not appear in detector-facing training or inference contracts. The evaluator may join truth only after the declared evidence freeze.
- **FR78 — Physical detector candidates:** The physical track shall compare an LSTM autoencoder, a GRU autoencoder, and declared simpler or classical baselines fitted only on qualified normal training evidence and using the same current-domain feature schema, complete-run partitions, evaluation budget, repetitions, and metrics. The current mixed-scale autoencoder remains a `LEGACY_BASELINE`; it is not the final detector and is not a dataset. The result mapping shall distinguish commanded 25%-75% operating transitions from separately declared anomalous interventions.
- **FR79 — Controlled Linux workload and authentic calls:** The custom syscall track shall run an allowlisted, controlled Linux edge workload that performs representative edge functions. Sysdig/eBPF or another qualified Linux kernel collector shall capture the calls the workload actually emits. The workload may be mocked; the syscalls themselves shall not be fabricated or modified.
- **FR80 — `SyscallEventBatch.v1`:** Captured custom syscall evidence shall use a versioned contract containing run, edge, boot, container/process/session, categorical syscall name and direction, sequence/timestamps, kernel/ABI and collector identities, loss/duplicate/gap/queue evidence, and raw-segment hashes. Labels and scenario truth shall be absent. Fixture replay shall be test-only and excluded from `PTFP-Custom-v1` evaluation.
- **FR81 — Syscall detector candidates:** The primary syscall anomaly track shall use categorical event semantics and compare embedding-plus-LSTM, embedding-plus-GRU, and an n-gram/STIDE-style transparent baseline fitted on qualified normal training evidence under the same group-safe protocol. Numeric syscall identifiers shall not be normalized as continuous quantities or optimized with reconstruction MSE solely because they are numbers.
- **FR82 — ADFA-LD role:** The system shall treat ADFA-LD as an offline external syscall benchmark, preserve official roles, trace identity and six attack families, record source/archive hashes and known count discrepancies, use categorical semantics, and keep labels in evaluation truth. It shall not fabricate timestamps or execute dataset identifiers.
- **FR83 — LID-DS 2021 role:** The system shall implement a version-specific LID-DS 2021 adapter that preserves official training/validation/test and scenario/recording boundaries plus the published syscall schema. LID-DS may inform custom Docker/Sysdig capture design, but its example durations, collector settings, or reported metrics shall remain cited references rather than adopted project constants.
- **FR84 — HAI 23.05 role:** The system shall pin and verify HAI 23.05, preserve its native tags, units, chronology, official file roles, and separate labels, and use a version-specific physical/SCADA adapter. HAI preprocessing, model, calibration, and evaluation artifacts shall remain separate from custom and syscall artifacts. HAI shall not be mass-converted to mA or presented as a compressor dataset.
- **FR85 — `PTFP-Custom-v1`:** The system shall create a versioned custom dataset containing synchronized physical observations and captured Linux edge syscalls from the same experiment runs, with immutable stream manifests, correlation/clock evidence, modality quality, profile/config identities, and separately protected truth. Prototype-generated rows shall not be inserted into HAI or represented as ADFA-LD/LID-DS data.
- **FR86 — Leakage-safe lifecycle:** Complete official groups or independent custom runs shall be split before window formation. Preprocessing and vocabulary fitting shall use training evidence only; early stopping and threshold selection shall use declared validation/calibration evidence only; and locked test evidence shall remain unavailable until the model, feature schema, preprocessing, threshold, metrics, and evaluation policy are frozen.
- **FR87 — Immutable detector bundles:** Each evaluated or deployed detector shall bind model weights/architecture, feature order/schema or syscall vocabulary, preprocessing, training/calibration dataset and split hashes, frozen threshold and its derivation, dependency/runtime identity, and bundle hash. Loading or inference shall not call `fit` or recalculate the threshold.
- **FR88 — Protocol-appropriate evaluation:** Each track shall report all applicable point/window and event/range outcomes, including PR-AUC, precision, recall, F1, false-positive behavior, false events per operating hour, time to detection, confusion data where appropriate, threshold sensitivity, resource cost, modality availability/quality, and repeated-run dispersion or uncertainty. Unfavorable and aborted planned runs shall remain visible with their status and cause.
- **FR89 — Custom-only late fusion:** Physical and syscall detector scores may be fused only when produced for the same held-out `PTFP-Custom-v1` runs and aligned windows under frozen detector-specific calibration. Initial fusion policies shall be simple and preregistered before truth unlock. ADFA-LD or LID-DS syscall evidence shall never be concatenated or temporally joined with HAI physical rows to manufacture a fusion result.
- **FR90 — Independent OPC UA evidence:** The OPC UA server shall receive a pre-consensus plant/transmitter snapshot. A distinct client shall read the value through `opc.tcp` and preserve `DataValue` status, source/server timestamps, schema, and correlation. Invalid, stale, mixed, missing, or unavailable readings shall fail explicitly; the active v2 path shall not silently fall back to consensus projection.
- **FR91 — Current-domain consensus:** Consensus v2 shall declare the instrument profile and comparison basis. Redundant observations of the same profile may be compared in current domain; cross-profile or cross-sensor aggregation shall use documented dimensionless, uncertainty-aware residuals rather than anonymous physical-unit scales. Python and Go shall produce deterministic identical results from shared golden fixtures.
- **FR92 — Final result package:** Reporting shall produce separate result tables for ADFA-LD, LID-DS 2021, HAI 23.05, and each `PTFP-Custom-v1` modality, followed by a paired custom-only physical/syscall/fusion ablation and a capability/limitation matrix. It shall not select a global champion across incompatible domains. Every claim shall link to source, version, split, model/bundle, threshold/calibration, run, raw score/metric, and limitation.
- **FR93 — Read-only evidence dashboard:** The dashboard shall display raw mA, normalized span, and engineering value as physical representations; physical, syscall, and fusion detector channels as distinct outputs; and dataset scope, provenance, quality, bundle, threshold origin, and limitations. It shall not import, split, train, calibrate, promote, fuse, relabel, or rewrite results.

**Functional requirement inventory:** 51 explicitly defined FRs were found in
the PRD document chain: FR1–FR29 and FR72–FR93. FR30–FR71 are not defined in
the selected PRD documents. The August PRD refers to the July inventory, so
their status must be resolved during epic coverage validation rather than
silently assumed.

### Non-Functional Requirements

#### Base requirements retained for historical and supersession traceability

- **NFR1 — AMEND:** The prototype must execute locally with a collection cadence aligned with the one-minute reference defined in the approved materials.
- **NFR2:** The execution flow must remain suitable for live demonstration and academic inspection, without requiring high-frequency or real-time optimization.
- **NFR3 — AMEND:** The prototype must preserve validation-before-trust by ensuring that shared edge state is not treated as valid until Byzantine-style consensus has completed.
- **NFR4 — AMEND:** Only consensused valid data may be used for downstream processing steps such as SCADA comparison, persistence, and LSTM training or inference.
- **NFR5 — AMEND:** The prototype must keep SCADA divergence alerting and fingerprint-based anomaly alerting as distinct outputs.
- **NFR6:** The prototype must run locally.
- **NFR7:** The prototype must explicitly indicate when valid consensus cannot be achieved.
- **NFR8:** The prototype must produce clear, structured logs that allow each pipeline stage and each consensus round to be inspected during demonstration and evaluation.
- **NFR9:** The structured logs must provide full traceability of each consensus round, including identification of participating edges, excluded edges, and the reasons for exclusion.
- **NFR10:** The prototype execution must be reproducible for academic presentation and validation.
- **NFR11 — SUPERSEDED:** The prototype must integrate locally with MQTT for edge communication, HART-based collection semantics for sensor acquisition, OPC UA for fake SCADA exposure, MinIO for object storage, and an LSTM service for fingerprint training and inference.
- **NFR12:** The integration model must remain simple and local, without requiring real cloud infrastructure or external industrial systems.
- **NFR13:** The prototype must prioritize Python.
- **NFR14:** The prototype must be simple and demonstrable.
- **NFR15:** The prototype must have clear logs for presentation.
- **NFR16:** The prototype must be modular.
- **NFR17:** The prototype must permit future replacement of the local storage by a real cloud storage solution.

#### May overlay requirements retained and strengthened by August

- **NFR18 — RETAIN/AMEND:** Each training run must be reproducible from dataset version, split seed, model architecture record, and hyperparameter record. Two runs with the same inputs must produce identical metrics within numerical tolerance.
- **NFR19 — RETAIN/AMEND:** The operator dashboard must be able to read the training history store and present each run as an inspectable dataset, architecture, hyperparameter, and metric record; until then, records must remain readable as flat JSON.
- **NFR20 — RETAIN/AMEND:** The live runtime loop must never block waiting for an offline training run. The tracks may share storage but not execution lifecycles.
- **NFR21 — RETAIN/AMEND:** Every benchmark must record origin organization, publication year, dataset version, sample count per class, feature schema, and acquisition URL or citation.

#### Controlling August requirements

- **NFR38 — Semantic accuracy:** Contracts, logs, reports, and UI shall use the two-modality definition consistently and shall not call 4-20 mA a modality, an autoencoder a dataset, HAI compressor data, or controlled custom data real-plant evidence.
- **NFR39 — Numeric accountability:** Formal v2 startup or experiment validation shall reject any executable numeric parameter that lacks the complete FR76 record. A literature citation shall not establish transferability unless the cited value applies to the selected profile; measured and preregistered values shall be reported as such.
- **NFR40 — Reproducibility and immutability:** Formal results shall be reconstructible from immutable identities for code, dependencies, container images, sources, datasets, profiles, configuration, splits, schemas, bundles, scores, truth-unlock record, fusion policy, and evaluation code.
- **NFR41 — Leakage resistance:** No detector-facing artifact shall contain truth, attack labels, future values, unauthorized partitions, or windows that cross run, trace, scenario, file, boot, session, process, gap, or official dataset boundaries.
- **NFR42 — OT safety and authority separation:** Control and experiment scheduling shall remain independent from security analytics. Detector, dashboard, storage, MQTT, OPC UA, capture, or evaluator failure shall never create or change an actuator/compressor command.
- **NFR43 — Fair candidate comparison:** LSTM, GRU, and baseline comparisons within one track shall use the same eligible data partitions, input schema, tuning access, declared budget, repetitions, and primary metrics. Model superiority shall be a measured outcome, not a requirement premise.
- **NFR44 — No universal threshold assumption:** Anomaly thresholds, window sizes, run duration, repetitions, ramp/dwell, queue/buffer capacity, capture loss tolerance, fusion weights, and performance targets shall be sourced for the selected profile, measured in a preserved pilot, or preregistered with sensitivity analysis. No reviewed publication is treated as supplying a universally valid value for these decisions.
- **NFR45 — Capture quality:** Custom syscall evidence shall expose workload attribution, collector/kernel identity, gaps, duplicates, drops, queue depth, storage lag, and measured overhead. Affected windows shall be flagged or invalidated by the preregistered policy rather than silently treated as normal.
- **NFR46 — Temporal and correlation integrity:** Every custom stream shall preserve source/observation time, ordered sequence, run/edge/boot/session identity, and declared clock/correlation uncertainty sufficient to prove a physical-syscall join. Unresolved or mixed identities shall prevent fusion.
- **NFR47 — Resource isolation and explicit failure:** Acquisition/control shall remain available when storage or analytics is degraded. High-volume syscall evidence shall use bounded queues and append-only segments; missing, partial, delayed, or aborted evidence shall be explicit rather than hidden.
- **NFR48 — Versioned compatibility:** v1 evidence shall remain replayable. v2 contracts, consensus state, storage namespaces, and model bundles shall be explicitly versioned. A v1 model shall not load against v2 features, and incompatible schemas or hashes shall fail closed.
- **NFR49 — Durable evidence storage:** Formal evidence shall use persistent, verified, restorable storage and append-only or content-addressed object keys. Mutable latest-only state shall not be the sole record of a scientific run.
- **NFR50 — End-to-end traceability:** A reported decision or metric shall resolve from experiment and source identities through raw segments, canonical observations, partitions/windows, bundle, score, truth join, and evaluation record without relying on a dashboard or hidden local state.
- **NFR51 — Complete scientific reporting:** All planned valid, invalid, aborted, and unfavorable runs shall be retained and reported with applicable uncertainty, resource/quality evidence, limitations, and the distinction between locally measured and externally published results.
- **NFR52 — Authorization boundary:** Planning approval shall be machine- and human-readable as distinct from implementation, training, dataset acquisition, syscall capture, and experiment authorization. No downstream workflow shall treat this overlay as permission to perform those actions.

**Non-functional requirement inventory:** 36 explicitly defined NFRs were
found in the PRD document chain: NFR1–NFR21 and NFR38–NFR52. NFR22–NFR37 are
not defined in the selected PRD documents and require resolution against the
July planning inventory.

### Additional Requirements and Constraints

- Exactly two anomaly-detection modalities are permitted: physical
  instrumentation and Linux host syscalls.
- Raw 4–20 mA current, normalized span, and engineering value are synchronized
  representations of one physical observation, not separate modalities.
- Internal simulator physics may remain in engineering units, while the custom
  edge evidentiary boundary preserves raw electrical evidence, quality, and
  profile identity.
- Only `PTFP-Custom-v1` may support physical-plus-syscall fusion because both
  modalities originate from the same correlated held-out runs.
- ADFA-LD, LID-DS 2021, and HAI 23.05 remain separate external benchmarks and
  may not be row-joined or presented as custom runtime evidence.
- The controlled Linux workload may be mocked, but the syscalls eligible for
  the custom dataset must be authentic kernel events rather than fabricated or
  modified calls.
- Truth, labels, interventions, and future intervals must be structurally
  isolated from detector-facing artifacts until evidence freeze.
- No simulator, divergence, threshold, window, duration, loss, or fusion value
  becomes valid merely because a publication contains a similar number.
- The 25%–75% command is a preregistered speed/capacity-reference factor, not
  electrical power or a universal compressor safety recommendation.
- The project is a local academic testbed, not a certified OT product, real
  plant, validated digital twin, or production safety system.
- Planning approval does not authorize code/configuration changes, dependency
  or dataset acquisition, model fitting/promotion, syscall capture, workload
  execution, simulator campaigns, or long-running experiments.

### PRD Completeness Assessment

The August PRD overlay is detailed, testable, source-aware, and clear about the
scientific boundary. It corrects the earlier LSTM-only, labelled-classifier,
circular-SCADA, anonymous-parameter, and cross-dataset-fusion assumptions.

The principal structural concern is that the effective PRD remains an overlay
chain rather than a single consolidated specification. FR30–FR71 and
NFR22–NFR37 are absent from the selected PRD documents even though the August
overlay says its numbering continues the July inventory. Their current
disposition cannot be inferred safely from numbering alone. Epic coverage
validation must establish whether those requirements are retained, amended,
or superseded and whether any still-active requirement lacks a controlling
story.

Initial assessment: **substantively strong but not yet proven implementation
ready** pending full requirement-to-story coverage and resolution of the
numbering/authority gap.

## Step 3 — Epic Coverage Validation

The base epics, May overlay, superseded July plan, and controlling August
Epics 9–18 overlay were read completely. Coverage below distinguishes a
historical implementation path, a superseding replacement, and a current
delivery epic.

### Coverage Matrix

| FR | PRD requirement | Epic/story coverage | Status |
| --- | --- | --- | --- |
| FR1 | Simulate three compressor sensors | Historical Epic 1; amended by Epic 10 signal profiles and transmitter boundary | Covered / amended |
| FR2 | One assigned local sensor per edge | Historical Epic 1; amended by Epic 10 `SignalObservation.v2` | Covered / amended |
| FR3 | Publish edge observations through MQTT | Historical Epic 1; v2 envelope path governed by Epics 10 and 14 | Covered / amended |
| FR4 | Consume peer observations through MQTT | Historical Epic 1; v2 compatibility governed by Epics 9–10 | Covered / amended |
| FR5 | Maintain a non-trusted replicated compressor view | Historical Epic 1; trust boundary preserved by Epics 10–11 | Covered / amended |
| FR6 | Execute Byzantine-style consensus | Historical Epic 2; current-domain v2 path in Epic 11 | Covered / amended |
| FR7 | Expose and persist trust ranking | Historical Epic 2; versioned evidence in Epics 9 and 11 | Covered / amended |
| FR8 | Exclude suspicious edge contributions | Historical Epic 2; parity and parameter evidence in Epic 11 | Covered / amended |
| FR9 | Identify participating edges | Historical Epic 2; v2 identity/correlation in Epic 11 | Covered / amended |
| FR10 | Identify exclusions and reasons | Historical Epic 2; deterministic v2 decision in Epic 11 | Covered / amended |
| FR11 | Expose full round trust evidence | Historical Epic 2; v2 committed/query evidence in Epic 11 | Covered / amended |
| FR12 | Represent failed consensus explicitly | Historical Epic 2; fail-closed v2 compatibility in Epic 11 | Covered / amended |
| FR13 | Structured consensus logs | Historical Epic 2; manifests and v2 traceability in Epics 9 and 11 | Covered / amended |
| FR14 | Consensus-failure alert | Historical Epic 2; distinct presentation retained by Epic 18 | Covered / amended |
| FR15 | Fake OPC UA SCADA exposure | Superseded by FR90; Epic 12 Stories 12.1–12.3 | Covered by replacement |
| FR16 | Sensor-by-sensor comparison with tolerance | Superseded by FR90/FR91; Epics 11–12 replace anonymous tolerance and circular source | Covered by replacement |
| FR17 | SCADA divergence alert | Superseded by FR90; Epic 12 fail-closed comparison, Epic 18 presentation | Covered by replacement |
| FR18 | Persist valid data locally | Historical Epic 3; amended by Epics 9–10 and 17 immutable role-separated evidence | Covered / amended |
| FR19 | Train an LSTM on normal data | Superseded by FR78/FR86; Epic 13 fair physical candidates | Covered by replacement |
| FR20 | Generate equipment fingerprint | Superseded by FR78/FR87; Epic 13 immutable physical detector bundle | Covered by replacement |
| FR21 | Produce anomaly score and class | Superseded by FR87–FR89; Epics 13–14 and 17 detector/fusion outputs | Covered by replacement |
| FR22 | Save model/fingerprint | Superseded by FR87; Epic 13 atomic bundle and Epic 17 evidence freeze | Covered by replacement |
| FR23 | Detect replay | Superseded by FR75/FR78/FR88; Epics 10, 13, and 17 controlled blind evaluation | Covered by replacement |
| FR24 | Offline benchmark-driven track | Amended by FR82–FR84; Epics 15–16 keep modality-specific benchmark roles | Covered / amended |
| FR25 | Generic stratified 80/20 split | Superseded by FR86; Epics 13–17 split complete groups before windows | Covered by replacement |
| FR26 | Record architecture and hyperparameters | Retained/amended by FR87/FR88; Epics 9 and 13–16 | Covered / amended |
| FR27 | Supervised classification metrics | Superseded by FR88; Epics 13–17 use protocol-appropriate metrics | Covered by replacement |
| FR28 | Persist and inspect training history | Amended by FR87/FR92 and NFR49; Epics 9, 13–17 | Covered / amended |
| FR29 | Gate live classifier reintegration | Superseded by immutable same-modality bundles; Epic 13 Stories 13.5 and 13.7 | Covered by replacement |
| FR72 | Two-modality semantic boundary | Epics 10, 17, and 18 | Covered |
| FR73 | `SignalObservation.v2` | Epic 10 Stories 10.1–10.3 and 10.7 | Covered |
| FR74 | Profile-owned derivation and physics | Epic 10 Stories 10.1–10.3 | Covered |
| FR75 | `ExperimentSpec` and 25%–75% reference | Epic 10 Stories 10.4–10.5 | Covered |
| FR76 | Parameter provenance gate | Epic 9 Story 9.2; Epics 10–11 consumers | Covered |
| FR77 | Isolated truth | Epic 10 Story 10.6; enforced through Epics 13–17 | Covered |
| FR78 | Physical detector candidates | Epic 13 Stories 13.1–13.7; Epic 16 HAI candidates | Covered |
| FR79 | Controlled workload and authentic syscalls | Epic 14 Stories 14.1–14.2 | Covered |
| FR80 | `SyscallEventBatch.v1` | Epic 14 Stories 14.3–14.4 | Covered |
| FR81 | Categorical syscall candidates | Epic 14 Story 14.5 and Epic 15 Stories 15.3/15.6 | Covered |
| FR82 | ADFA-LD external role | Epic 15 Stories 15.1–15.3 and 15.7 | Covered |
| FR83 | LID-DS 2021 official role | Epic 15 Stories 15.4–15.7 | Covered |
| FR84 | HAI 23.05 native physical role | Epic 16 Stories 16.1–16.6 | Covered |
| FR85 | Synchronized `PTFP-Custom-v1` | Epics 10 and 14 producers; Epic 17 Story 17.2 | Covered |
| FR86 | Leakage-safe lifecycle | Epic 9 contracts; Epics 13–17 partitions/evaluation | Covered |
| FR87 | Immutable detector bundles | Epics 9, 13–17 | Covered |
| FR88 | Protocol-appropriate evaluation | Epics 9, 13–17 | Covered |
| FR89 | Custom-only late fusion | Epic 17 Stories 17.3–17.5 | Covered |
| FR90 | Independent OPC UA evidence | Epic 12 Stories 12.1–12.6 | Covered |
| FR91 | Current-domain consensus | Epic 11 Stories 11.1–11.5 | Covered |
| FR92 | Final result package | Epic 17 Stories 17.6–17.8; Epic 18 presentation | Covered |
| FR93 | Read-only evidence dashboard | Epic 18 Stories 18.1–18.5 | Covered |

### Missing Requirements

No explicitly defined PRD FR in the selected PRD chain lacks an implementation
path. Coverage is therefore **51 of 51 explicit PRD FRs**.

This does not close the following critical authority defect:

#### Critical: FR30–FR71 exist only in the superseded July epic inventory

- **Observed condition:** the July epic update defines 42 additional FRs,
  FR30–FR71. The August PRD says its numbering continues that inventory but
  does not reproduce or individually dispose every identifier. The August
  epic overlay formally claims FR72–FR93 and supersedes the July Epics 9–16.
- **Impact:** an implementer cannot determine from the controlling PRD alone
  whether each July requirement is active, replaced, narrowed, or removed.
  Semantic similarity to new requirements is not a safe substitute for an
  explicit disposition record.
- **Examples:** July FR35 accelerated batch generation, FR40 manifest-last
  publication, FR41 `DATASET_QUALIFIED`, FR48 OPC feature flag, and FR53
  promotion/rollback have related August stories but no identifier-level
  controlling disposition. July FR55–FR58 are explicitly replaced in topic by
  HAI 23.05, while other identifiers are only grouped in broader trace rows.
- **Recommendation:** before implementation authorization, add one binding
  FR30–FR71 disposition matrix to the PRD overlay with exactly one outcome per
  identifier: `RETAIN`, `AMEND -> FRxx`, or `SUPERSEDE -> FRxx/NFRxx`. Update
  the epic coverage table to reference that matrix.

### Requirements Found in Epics but Not Defined in the PRD Chain

- **FR30–FR71:** 42 identifiers in the July epic inventory; authority is
  unresolved as described above.
- The August epic overlay does not introduce unnumbered new functional
  requirements outside FR72–FR93, but its closure gates and guardrails impose
  additional acceptance constraints that must remain traceable to FR/NFRs and
  architecture decisions.

### Coverage Statistics

- Explicit FRs defined in selected PRD documents: **51**
- Explicit PRD FRs with historical, replacement, or current epic coverage:
  **51**
- Missing implementation paths among explicit PRD FRs: **0**
- Formal explicit-PRD coverage: **100%**
- Extra July FR identifiers lacking controlling PRD definitions/dispositions:
  **42**
- Coverage conclusion: **semantically complete for the August plan, formally
  incomplete at the requirement-authority boundary**.

## Step 4 — UX Alignment Assessment

### UX Document Status

**Not found.** No whole or sharded UX design specification exists under the
planning-artifacts directory.

UX is nevertheless explicitly implied and required:

- the base PRD describes a lightweight SCADA-inspired demonstration UI;
- FR93 requires a read-only evidence dashboard;
- FR72 and NFR38 require correct modality and representation language in UI;
- Epic 18 contains five dashboard stories for versioned read models, signal
  representation, detector channels, provenance, limitations, and run health;
- the architecture assigns the dashboard a presentation-only, least-privilege,
  read-only role over immutable evidence.

### PRD ↔ Architecture Alignment

The controlling architecture supports the principal product constraints:

- versioned v1/v2 read adapters can preserve historical evidence;
- dashboard identities cannot read restricted truth or write control;
- raw current, normalized span, engineering value, physical score, syscall
  score, and fusion result remain distinct representations/channels;
- incompatible or missing data is presented as unavailable rather than
  silently coerced;
- the dashboard consumes immutable artifacts and cannot import, split, train,
  calibrate, promote, fuse, relabel, or recompute scientific results;
- dashboard disagreement cannot override evaluator artifacts.

No architecture-level contradiction with FR93 was found.

### Alignment Issues

1. **No interaction or information-architecture specification.** Epic 18 says
   what evidence must be visible but not how a researcher moves between live
   run health, modality views, dataset cards, detector evidence, final matrix,
   and raw provenance.
2. **No explicit state catalogue.** The UI must distinguish unavailable,
   incomplete, invalid, aborted, truth-locked, truth-unlocked, schema-mismatch,
   missing-modality, capture-loss, stale OPC, and legacy-only evidence. Those
   states are present in backend requirements but not assembled into one UX
   behavior table.
3. **No visual semantics for safety-critical distinctions.** Physical,
   syscall, fusion, consensus failure, OPC invalidity, and SCADA divergence
   must not be conflated by color, icon, wording, or placement, but no design
   rule currently governs those distinctions.
4. **No responsiveness or data-volume behavior.** The dashboard may display
   long-run timelines, raw logs, evidence tables, and provenance chains, but
   loading, pagination, virtualization, refresh, and degraded-storage behavior
   are unspecified.
5. **No accessibility/localization requirements.** Keyboard operation,
   contrast, non-color-only status communication, readable typography, and
   Portuguese/English terminology have not been decided.
6. **No user-validation criterion.** The intended viewers are researcher,
   operator, professor, and evaluator, but there is no lightweight usability
   walkthrough demonstrating that each can find the evidence needed for the
   presentation and audit tasks.

### Warnings and Readiness Effect

- Missing UX documentation is **not a blocker for backend/scientific Epics
  9–17**, because the architecture deliberately keeps the dashboard outside
  scientific computation and the evidence package does not depend on it.
- Missing UX documentation **is a blocker for starting Epic 18**. Before that
  epic is authorized, create a bounded UX specification covering navigation,
  state catalogue, visual semantics, accessibility, data-volume behavior, and
  a small evaluator walkthrough. It must preserve the read-only architecture
  and must not expand into a production HMI.
- The UX artifact should cite FR72, FR92, FR93, NFR38, NFR42, NFR50–NFR52 and
  Stories 18.1–18.5 directly.

## Step 5 — Epic Quality Review

### Structural Verification

- Revised epics reviewed: **10** (Epics 9–18).
- Revised stories reviewed: **62**.
- Stories with an explicit researcher/operator/evaluator/maintainer/viewer
  actor: **62 of 62**.
- Stories with a dependency declaration: **62 of 62**.
- Stories with Given/When/Then acceptance criteria: **62 of 62**.
- Numeric forward story dependencies detected: **0**.
- Database/entity timing violations: **not applicable**; the architecture uses
  versioned object artifacts and contracts rather than a new relational schema.
- Brownfield integration is handled explicitly through v1 freeze, golden
  fixtures, legacy/shadow/active migration, and immutable historical evidence.

### Epic-Level Assessment

| Epic | User/evaluator outcome | Independence and quality finding |
| --- | --- | --- |
| 9 | Reproduce and audit the v1 baseline before v2 evidence | Valuable research outcome, but Stories 9.1/9.2/9.5 are broad cross-system work units |
| 10 | Run a source-governed physical experiment with isolated truth | Cohesive and backward-dependent; Story 10.7 is broad but bounded by the signal contract |
| 11 | Reproduce current-domain consensus decisions in Python and Go | Cohesive; dependencies point backward; parity and failure behavior are testable |
| 12 | Obtain causally independent OPC UA evidence | Strong evaluator value and clean sequential decomposition |
| 13 | Compare and freeze a physical detector | Coherent outcome; model-comparison Story 13.3 is too large as one implementation unit |
| 14 | Capture real edge syscalls and evaluate a host detector | Strong research value; platform-fallback path and comparison story need refinement |
| 15 | Reproduce ADFA-LD and LID-DS results | Couples two independently valuable benchmarks and allows LID access to block epic closure |
| 16 | Evaluate physical candidates on HAI 23.05 | Cohesive external benchmark; comparison Story 16.4 is oversized |
| 17 | Capture custom evidence, fuse modalities, produce all final tables, and reconstruct the package | Delivers the core dissertation outcome but combines multiple epics' worth of campaign and reporting work |
| 18 | Let viewers inspect evidence safely | Clear user-facing outcome; implementation remains blocked by the missing UX specification |

### Critical Violations

No circular or forward dependency was found, and no revised epic lacks all
researcher/evaluator value. There is therefore no critical dependency-cycle
violation in the August backlog itself.

The requirement-authority defect for FR30–FR71 remains critical at the planning
package level and must be corrected before implementation authorization, as
documented in Step 3.

### Major Issues

#### 1. Epic 17 combines two independently deliverable outcomes

- **Problem:** custom campaign capture and paired fusion (Stories 17.1–17.5)
  are combined with cross-benchmark reporting and full-package reconstruction
  (Stories 17.6–17.8).
- **Effect:** the custom physical/syscall fusion result cannot close as an epic
  until unrelated external benchmark gate G7 and the entire final reporting
  package are complete.
- **Remediation:** split the epic into:
  1. synchronized custom campaign and paired ablation; and
  2. final multi-benchmark tables, claim index, and evidence reconstruction.
  Preserve the same FRs and gate ordering; do not change scientific scope.

#### 2. Epic 15 couples ADFA-LD and LID-DS availability

- **Problem:** ADFA-LD and LID-DS are separate datasets, runtimes, licenses,
  source-access risks, schemas, and result tables, yet one closure gate requires
  both.
- **Effect:** unavailable or legally unresolved LID data can prevent closure of
  otherwise reproducible ADFA work.
- **Remediation:** split into two epics or define independent dataset gates and
  an explicit aggregate external-syscall gate. Do not treat a partial result as
  full completion.

#### 3. LID-DS has an unmodelled acquisition/qualification predecessor

- **Problem:** Story 15.4 begins with a “pinned LID-DS 2021 source,” but no
  preceding August story acquires, inventories, hashes, licenses, and qualifies
  the official recording distribution. Story 9.4 defines manifest structure;
  it does not create the LID source artifact.
- **Effect:** the adapter story depends on an artifact that no story owns.
- **Remediation:** add a LID source-acquisition and qualification story before
  adapter implementation. It must support an explicit blocked state, record the
  unresolved recording-data license, and prohibit fixture fallback.

#### 4. Several candidate-comparison stories are not atomic

- **Affected:** Stories 13.3, 14.5, 15.6, and 16.4.
- **Problem:** each can encompass candidate implementation, hyperparameter
  protocol, training, calibration, repeated inference, metrics, resource
  measurement, and comparison. Story 15.6 additionally spans two datasets.
- **Effect:** completion and review cannot be attributed to one bounded change;
  a failed candidate or dataset can leave the story ambiguously partial.
- **Remediation:** for each modality/dataset, separate:
  1. protocol and baseline adapters;
  2. candidate model implementation/contract tests;
  3. authorized measured runs; and
  4. frozen comparison report.
  Training/execution stories must remain separately authorized from code work.

#### 5. Story 9.2 is epic-sized

- **Problem:** “every executable scientific parameter” spans simulator,
  instruments, experiment scheduling, consensus, OPC, physical ML, syscall
  capture, external adapters, storage, evaluation, fusion, and dashboard.
- **Effect:** the story cannot reach a stable definition of done incrementally,
  and all later work depends on it.
- **Remediation:** retain one catalogue/schema story, then create domain-scoped
  ledger-completion stories or explicit gate checklists for signal, consensus,
  physical ML, syscall capture, external datasets, and evaluation. G1 closes
  only when all declared scopes pass.

#### 6. Host-capture fallback is architectural but not owned by a story

- **Problem:** Story 14.2 may prove Docker Desktop/WSL capture unreliable, and
  the architecture specifies a pinned Linux VM/host fallback. No story selects,
  provisions, and requalifies that fallback boundary.
- **Effect:** a legitimate negative spike result blocks the branch without a
  planned remediation path.
- **Remediation:** extend Story 14.2 with an explicit selected-boundary output
  and add a conditional fallback qualification story. Do not weaken capture
  evidence simply to pass the gate.

#### 7. Story 17.2 is an operational campaign disguised as one story

- **Problem:** it covers all synchronized runs, two raw streams, clock and
  correlation evidence, quality, gaps, capture health, immutable manifests,
  and final valid/invalid/aborted classification.
- **Effect:** progress and failures cannot be isolated, and code readiness is
  conflated with authorization to run a long experiment.
- **Remediation:** split contract/tool implementation from pilot validation,
  authorized campaign execution, and dataset finalization/locking.

### Minor Concerns

1. Several epic titles are solution-centric (`Current-Domain Consensus v2`,
   `HAI 23.05 External Physical Benchmark`) even though their goals correctly
   state researcher/evaluator value. Retitle only if editorial consistency is
   desired; the goals are sufficient to avoid a value-less technical epic.
2. Some dependencies use gate names or implicit artifacts rather than the
   exact producing story, such as “published v2 schemas,” “published detector
   outputs,” or G3–G7. Add artifact IDs/producing stories to reduce ambiguity.
3. Acquisition stories should define explicit `blocked` outcomes for official
   endpoint failure or unresolved licensing instead of relying only on closure
   prose.
4. Empirical story ACs correctly avoid inventing thresholds, but each must
   reference the exact preregistration or parameter-ledger artifact that will
   supply its run count, stopping rule, and pass/exclusion policy.
5. Epic 18 has technically testable ACs but lacks the UX behavior specification
   identified in Step 4.

### Best-Practice Conclusion

The revised backlog has strong semantics, backward-only sequencing, explicit
actors, BDD acceptance criteria, scientific guardrails, and traceability. It is
not yet implementation-ready as written because several stories and Epic 17
are too large, LID source acquisition has no owner, the capture fallback has no
owner, and the formal FR30–FR71 authority gap remains unresolved.

## Summary and Recommendations

### Overall Readiness Status

**NEEDS WORK — implementation should not begin yet.**

The package is scientifically much stronger than the prior plan: it has a
coherent two-modality boundary, authentic syscall-capture design, native HAI
scope, source-backed instrumentation, isolated truth, immutable detector
bundles, independent OPC UA evidence, custom-only fusion, and 100% semantic
epic coverage for the FRs explicitly defined in the PRD chain.

Readiness is withheld because the controlling requirement authority is not
complete and several backlog units are too large or depend on artifacts that no
story owns. These are planning defects, not a rejection of the technical
direction.

### Critical Issues Requiring Immediate Action

1. **Resolve the requirement-authority gap.** Add a binding disposition for
   every FR30–FR71 and NFR22–NFR37 identifier from the July inventory. Each
   must be explicitly retained, amended to a current identifier, or superseded.
2. **Do not authorize implementation from semantic similarity alone.** The
   current August epic map covers FR72–FR93, but an implementer must not infer
   the status of the intervening identifiers.

### Major Corrections Required

1. Split Epic 17 into a synchronized custom campaign/paired-fusion epic and a
   final multi-benchmark evidence-package epic.
2. Separate ADFA-LD and LID-DS completion gates, or split Epic 15, so external
   LID access/license issues do not obscure valid ADFA progress.
3. Add an owned LID-DS acquisition, checksum, layout, version, and license-
   qualification story before its adapter story.
4. Split Stories 13.3, 14.5, 15.6, and 16.4 into bounded protocol/model,
   execution, and frozen-report work. Preserve separate authorization for code,
   training, dataset acquisition, and experiments.
5. Decompose Story 9.2 into a catalogue contract plus domain-scoped parameter
   coverage gates.
6. Add a conditional pinned-Linux fallback qualification story after the
   Docker Desktop/WSL syscall-capture spike.
7. Split Story 17.2 into capture tooling, pilot qualification, authorized
   campaign execution, and immutable dataset finalization.

### UX Correction Required Before Epic 18

Create a bounded evidence-dashboard UX specification covering navigation,
state catalogue, visual semantics, accessibility/localization, long-run data
volume, and evaluator walkthroughs. This does not block scientific/backend
Epics 9–17, but it blocks Epic 18.

### Recommended Next Steps

1. Amend the August PRD with the FR30–FR71 and NFR22–NFR37 disposition matrix.
2. Amend the August epic overlay using the seven major corrections above,
   without changing the approved scientific scope or adding numeric defaults.
3. Create the small Epic 18 UX specification or explicitly defer Epic 18 while
   keeping the final evidence package independent from the dashboard.
4. Re-run this readiness workflow against the amended artifacts.
5. Only after a `READY` result, create a separate authorization record naming
   the exact first story range and allowed activity types. Dataset acquisition,
   training, syscall capture, and experiment execution must remain separately
   authorized.

### Final Note

This assessment identified **19 actionable findings across four categories**:
one critical requirement-authority defect, seven major epic/story design
issues, six UX-definition gaps, and five minor traceability/editorial concerns.
The revised scientific direction should be preserved. Correct the planning
structure before implementation so that later agents do not reintroduce
unsupported constants, dataset-role confusion, label leakage, circular SCADA
evidence, or untraceable experiment choices.
