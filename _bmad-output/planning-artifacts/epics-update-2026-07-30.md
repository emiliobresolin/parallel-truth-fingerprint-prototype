---
stepsCompleted:
  - step-01-validate-prerequisites
  - step-02-design-epics
inputDocuments:
  - _bmad-output/planning-artifacts/prd.md
  - _bmad-output/planning-artifacts/architecture.md
  - _bmad-output/planning-artifacts/requirements.md
  - _bmad-output/planning-artifacts/scope.md
  - _bmad-output/planning-artifacts/prd-update-2026-05-21.md
  - _bmad-output/planning-artifacts/architecture-update-2026-05-21.md
  - _bmad-output/planning-artifacts/epics.md
  - _bmad-output/planning-artifacts/epics-update-2026-05-21.md
  - _bmad-output/planning-artifacts/research/technical-industrial-cyber-physical-dataset-selection-research-2026-07-29.md
  - docs/seminario-andamento/SeminarioDeAndamento.md
  - docs/seminario-andamento/evidence/evidence-index.md
  - docs/seminario-andamento/evidence/project-map.md
  - docs/seminario-andamento/evidence/custom-dataset/custom-dataset-analysis.md
  - docs/seminario-andamento/evidence/adfa-ld/adfa-ld-analysis.md
  - docs/seminario-andamento/tables/prototype-limitations.md
  - docs/seminario-andamento/tables/validation-scenarios.md
  - docs/seminario-andamento/tables/custom-dataset-summary.md
  - docs/seminario-andamento/tables/champion-run-summary.md
  - docs/input/[12] Shin et al. — HAI 1.0.pdf
workflowType: create-epics-and-stories
documentRole: additive-course-correction
parent: _bmad-output/planning-artifacts/epics.md
date: 2026-07-30
status: story-creation-in-progress
---

# parallel-truth-fingerprint-prototype - Epic Breakdown Update

## Overview

This additive planning document defines the next academically necessary work
without overwriting the implemented epic history in `epics.md`. It consolidates
the original PRD and Architecture, the May 2026 offline-training correction,
the Seminar de Andamento evidence, and the July 2026 technical research.

The July research is the controlling authority for the new work where it
conflicts with the May correction. In particular, the existing custom
autoencoder is no longer treated as dead or globally deprecated: v1 is retained
as an experimental baseline and a calibrated custom v2 becomes the primary
controlled cyber-physical evidence. The offline ADFA-LD/LID track remains
useful as auxiliary HIDS evidence. HAI 20.07 is the only new industrial public
dataset. OPC UA must become a real independent laboratory round-trip.

This document does not authorize implementation. It first establishes the
requirements inventory; epic design, story decomposition, and implementation
remain subsequent BMAD stages.

## Requirements Inventory

### Functional Requirements

#### Existing core behavior that must remain operational

FR1: The system can simulate temperature, pressure, and RPM for one compressor.

FR2: Each of the three logical edge nodes can collect only its assigned local
sensor through the existing pre-PLC/HART-inspired acquisition semantics.

FR3: Each edge can publish its observation through the real local MQTT broker.

FR4: Each edge can consume peer observations through the MQTT broker.

FR5: Each edge can maintain its own non-trusted local replicated view of the
compressor without shared mutable state collapsing edge independence.

FR6: The system can execute the existing CometBFT plus Go ABCI Byzantine-style
validation round.

FR7: A successful consensus result can expose and persist its trust ranking.

FR8: Consensus can exclude a suspicious edge contribution from the active
round.

FR9: Each consensus result can identify participating edges.

FR10: Each consensus result can identify excluded edges and the reason for each
exclusion.

FR11: Each consensus result can expose the ranking/evidence for every edge in
the round.

FR12: The system can represent failure to reach valid consensus as an explicit
outcome.

FR13: The system can emit structured, traceable logs for each consensus round.

FR14: The system can emit a distinct consensus-failure alert.

FR15: The system can expose a simulated logical SCADA state through an OPC UA
server.

FR16: The system can compare temperature, pressure, and RPM sensor by sensor
between the consensused physical-side state and an eligible SCADA observation
using configurable tolerances.

FR17: The system can emit a distinct SCADA-divergence alert and block invalid
downstream progression.

FR18: The system can persist only eligible, validated artifacts to local MinIO
storage.

#### Recovered and corrected custom fingerprint

FR19: The system can train a custom normal-behavior autoencoder using only
qualified normal custom-v2 training sessions.

FR20: The system can produce a versioned physical-operational fingerprint bundle
for the simulated compressor.

FR21: Custom-v2 inference can produce a normalized anomaly score, a frozen
normal/anomalous decision, score margin, and per-feature/per-sensor
contributions.

FR22: The system can save and load the actual model weights together with the
scaler, frozen threshold, feature schema, sequence length, dataset/split
identities, configuration, and hashes without retraining during load.

FR23: The custom fingerprint can be evaluated blindly against controlled
normal transitions and held-out offset, drift, freeze, replay/stale,
cross-sensor correlation-break, and recovery scenarios.

#### Offline benchmark track retained and amended

FR24: The system can run benchmark training and evaluation outside the live
runtime for ADFA-LD, LID-DS 2021, HAI 20.07, and custom v2 through
dataset-specific adapters and a shared evidence envelope.

FR25: Every v2 dataset must assign its official, temporal, session, file, or
trace-group split before window formation and record the policy and seed.
Legacy split behavior may remain available only for reproducibility of already
reported legacy runs.

FR26: Every measured training run can persist architecture, hyperparameters,
planned/executed epochs, parameter count, seed, training/validation curves,
wall-clock duration, and software/data versions.

FR27: Every measured run can persist the metrics appropriate to its protocol,
including macro/per-class F1, accuracy, precision, recall, FPR, confusion
matrix, and point/event-aware temporal metrics where applicable.

FR28: The training-history store can persist, list, and retrieve immutable run
records and artifacts by dataset, run ID, evidence tier, and result role.

FR29: Only an explicitly promoted and schema-compatible custom fingerprint
bundle can enter the physical runtime. ADFA-LD, LID-DS, and HAI models must
remain offline and cannot be promoted as compressor fingerprints.

#### Baseline, contracts, and evidence provenance

FR30: The system can capture a v1 golden baseline for runtime state, dashboard
state, MQTT/consensus contracts, MinIO object keys, dataset artifacts, and the
existing experimental fingerprint behavior.

FR31: The system can classify every dataset/run using controlled provenance
tiers such as `custom_generated`, `official_real`, `fixture_test`, and
`published_reference`, plus result roles such as `measured_result` and
`published_reference`.

FR32: The evidence gates can prevent a fixture or published statistic from
being represented as a measured execution result.

FR33: Batch generation, live runtime, consensus correlation, and OPC UA can
share a canonical versioned `ProcessSample` contract containing process values,
operating context, units, timestamps, cycle/session identity, source, and
correlation identifiers.

FR34: Controlled experiments can be declared through a versioned
`ExperimentSpec` containing phases, seed, logical cadence, duration, setpoint,
intervention, target sensor, severity, and recovery behavior.

#### Custom dataset v2 generation and qualification

FR35: The system can generate custom-v2 sessions in accelerated batch mode
using the same deterministic simulator/behavior core as the live runtime,
without sleeping or traversing MQTT, CometBFT, MinIO, or OPC UA for every
sample.

FR36: The experiment controller can produce cycle-level and event-level ground
truth independently from model predictions, and those labels cannot enter the
model feature tensor.

FR37: The custom-v2 feature schema can represent operating setpoint, setpoint
delta, cycles since setpoint change, explicit units, and true
`rate_of_change_dtdt = delta_value / delta_time`.

FR38: The custom generator can execute a pre-registered scenario matrix
covering steady regimes, commanded ramps, controlled anomalies, severity
levels, repetitions, and recovery, while preserving every run rather than only
favorable outcomes.

FR39: The custom-v2 builder can partition by complete session/seed before
windowing and prevent any window from crossing a session, scenario, split,
gap, cadence break, or schema version.

FR40: The system can publish raw/canonical/window artifacts immutably, verify
size and SHA-256, and publish the `status=complete` manifest last.

FR41: The system can qualify or reject a custom dataset through an explicit
`DATASET_QUALIFIED` gate based on schema, lineage, determinism, operational
coverage, repetitions, labels, split isolation, hashes, and artifact
completeness.

#### Independent laboratory OPC UA integration

FR42: An OPC UA server can receive and publish a plant snapshot created before
edge consensus, rather than projecting a `ConsensusedValidState`.

FR43: A logically independent OPC UA client can connect through `opc.tcp` and
read the server address space without accessing internal server objects.

FR44: The client can preserve value, `StatusCode`, source/server timestamps,
schema version, snapshot/revision identity, producer identity, and cycle/round
correlation for every required node.

FR45: The client can use a revision guard and reject incomplete, mixed,
unexpected, stale, `Bad`, `Uncertain`, unavailable, timed-out, or
mis-correlated snapshots.

FR46: The comparison path can consume only an eligible OPC UA observation and
can persist the full observation and any fail-closed diagnostic as evidence.

FR47: A causal round-trip test can change only the OPC branch and then only the
consensus branch, proving that each side of the comparison has an independent
source.

FR48: The independent OPC mode can be enabled through an initially disabled
feature flag, with no silent fallback to consensus projection when enabled.

#### Custom model preparation, calibration, evaluation, and promotion

FR49: The custom-v2 scaler can be fitted only on normal training data, early
stopping/model selection can use only validation data, and threshold selection
can use only an independent normal calibration partition.

FR50: The calibrated threshold can be frozen before normal/anomaly tests and
persisted as part of the model bundle with its origin and calibration hash.

FR51: The system can detect a stale or incompatible candidate when dataset,
feature schema, scaler, cadence, sequence length, configuration, or code
identity changes.

FR52: Controlled evaluation can report point/window and event metrics by
scenario, severity, sensor, regime, and repeated seed/session, including false
events per hour and detection delay.

FR53: The system can promote a custom bundle only after
`DATASET_QUALIFIED` and `MODEL_VALIDATED_CONTROLLED` pass and can roll back to
an explicitly identified previous bundle.

FR54: The live runtime can load a promoted custom bundle for inference-only
shadow operation and cannot train, recalibrate, or silently select the
lexicographically latest artifact.

#### HAI 20.07 official cyber-physical benchmark

FR55: A separate acquisition/import command can validate the official HAI
20.07 source, pinned version/commit, four `.csv.gz` files, license/citation,
sizes, and SHA-256 values without downloading inside adapter `load()`.

FR56: The HAI adapter can stream the official files with bounded memory,
preserve the official train/test roles and chronology, and prevent windows
from crossing files, gaps, or cadence breaks.

FR57: HAI preprocessing, model, threshold, and evaluation can remain
dataset-specific and can produce locally measured point/window and event-aware
metrics with full provenance.

FR58: HAI results can be published as external cyber-physical evidence for a
different industrial process without being represented as validation of the
simulated compressor.

#### LID-DS 2021 official-scenario subset

FR59: The system can distinguish LID evidence tiers `fixture_test`,
`published_reference`, and `official_real`, and only `official_real` can
support a locally measured LID result.

FR60: A source-validation command can inventory the official LID-DS 2021
distribution and the pre-registered `CVE-2017-7529` subset, recording the raw
layout/name, official URL/citation, version, license notice and scope, file
inventory, sizes, and SHA-256 hashes.

FR61: The LID adapter can explicitly select `CVE-2017-7529`, consume the real
official layout, preserve raw scenario/trace identities, reject ambiguous or
empty layouts, and never fall back to the test fixture.

FR62: LID data can be split by official role or complete trace/session before
windowing, with no trace or source syscall/timestep shared across train,
validation, calibration, or test.

FR63: The system can complete at least one reproducible measured run on the
official `CVE-2017-7529` subset, report binary Normal-versus-Attack metrics
across all planned seeds, and label the scope as
`LID-DS 2021 — official-scenario subset`.

FR64: Metrics published by the LID authors can be recorded only as cited
`published_reference` data and cannot influence local training, threshold,
model selection, or measured-result calculations.

#### Comparative reporting and evidence index

FR65: Every evaluation can produce a common `EvaluationRecord` containing
dataset/subset, modality, evidence tier, result role, split protocol, model,
parameters, metrics, hashes, run ID, limitations, and artifact references.

FR66: The reporting path can produce separate HIDS and cyber-physical result
tables plus a cross-domain capability/limitation matrix, without selecting a
global champion from incompatible domains or comparing raw losses/scores.

FR67: A claim-to-evidence index can link each academic claim to its dataset,
manifest, split, model bundle, threshold, measured run, report, limitation, and
scientific status.

#### Optional dashboard demonstration

FR68: After model promotion and evidence gates, the dashboard can display
custom bundle identity, scientific status, score, threshold, margin, operating
regime, feature/sensor contributions, and OPC UA integrity state.

FR69: The dashboard can display HAI, ADFA-LD, and LID results with dataset,
subset, evidence tier, result role, split, run, provenance, and limitation,
clearly distinguishing fixture, published reference, and official measured
results.

FR70: The dashboard can present consensus failure, SCADA divergence, OPC
integrity failure, replay/freeze, and custom ML anomaly as distinct states and
channels.

FR71: The dashboard can demonstrate a pre-registered custom anomaly using the
promoted model without generating data, training, calibrating, changing a
split, or rewriting persisted results.

### NonFunctional Requirements

NFR1: The prototype must execute locally. The live cycle cadence must be
configurable from one authoritative runtime value and exposed consistently to
the dashboard; accelerated batch generation must use logical timestamps rather
than live sleeping.

NFR2: The live execution flow must remain suitable for academic demonstration
and inspection without requiring hard real-time or high-frequency guarantees.

NFR3: The prototype must preserve validation-before-trust: edge-local replicated
state is not valid until consensus completes.

NFR4: Only explicitly eligible, consensused data may enter valid persistence or
custom normal training; invalid and anomalous cycles remain available only in
their separate evidence/ground-truth paths.

NFR5: Consensus failure, OPC integrity failure, SCADA divergence, replay/freeze,
and ML anomaly must remain semantically distinct.

NFR6: The solution must require no paid license, institutional approval wait,
cloud account, PLC, physical HART instrument, or production SCADA system.

NFR7: All blocking failures must be explicit states rather than unstructured
success, empty result, or silent fallback.

NFR8: Structured logs must allow every pipeline stage and experiment run to be
inspected.

NFR9: Each online cycle must be traceable across process snapshot, edge
observations, consensus round, OPC observation, comparison, persistence, and
inference where eligible.

NFR10: Scientific runs must be reproducible from source/version, hashes,
configuration, seed, split, schema, preprocessing, model, and threshold.

NFR11: The system must preserve the existing local MQTT, CometBFT/ABCI, OPC UA,
MinIO, Keras/Torch, and dashboard integration boundaries.

NFR12: The architecture must remain a local academic prototype and must not add
unnecessary cloud, Kubernetes, service mesh, API gateway, Kafka, new database,
or production-HMI scope.

NFR13: Python must remain the primary language; Go remains confined to the
existing ABCI/consensus boundary.

NFR14: The implementation must remain simple enough for one researcher to run,
inspect, and explain.

NFR15: Logs, manifests, metrics, and UI language must be presentation-friendly
without hiding technical ground truth.

NFR16: Modules must preserve explicit ownership and trust boundaries.

NFR17: The object-storage abstraction must remain replaceable without changing
dataset or model semantics.

NFR18: Repeating the same deterministic generation/import configuration must
reproduce the same sample identities, split assignments, canonical values, and
hashes within declared numerical tolerance.

NFR19: Training/evaluation history must remain inspectable as flat,
schema-versioned records even when the dashboard is unavailable.

NFR20: The live runtime must never block on dataset import, batch generation,
offline training, sweep, or report generation.

NFR21: Every dataset and run must record source organization, year, version,
subset, counts, schema, URL/citation, license/notice, evidence tier, result
role, and hashes.

NFR22: With v2 feature flags disabled, the current runtime, MQTT topics,
CometBFT contracts, historical MinIO keys, v1 artifacts, ADFA-LD flow, current
dashboard state keys, and experimental fingerprint baseline must remain
compatible.

NFR23: Bulk artifacts must be immutable/content-addressed and verified before
the complete manifest or promotion pointer is published.

NFR24: There must be zero session, file, trace, or overlapping-window leakage
between train, validation, calibration, and test partitions.

NFR25: HAI import and custom generation must support bounded-memory streaming
or sharding and must not require materializing the full public dataset as
Python tuples.

NFR26: Credentials and private keys must remain outside Git, manifests, and
reports; downloaded data and OPC/CSV fields must be treated as untrusted input.

NFR27: The OPC evidence gate must reject 100% of `Bad`, `Uncertain`, stale,
mixed-revision, missing-node, schema-mismatched, and mis-correlated observations
within at most one live cycle.

NFR28: Before final evaluation, custom-v2 targets must be pre-registered. The
initial research targets are normal-window FPR at most 5%, at most one false
event per hour, and detection in at least four of five repetitions for each
selected scenario/severity; all observed results must still be reported if a
target is missed.

NFR29: Dataset use must remain zero-cost and immediately actionable. Data with
unclear redistribution scope must not be committed or redistributed; scripts,
manifests, hashes, and citations provide reproducibility.

NFR30: Scientific language must not claim that custom v2 is a real plant or
validated digital twin, that HAI validates the compressor, that HIDS datasets
validate physical behavior, that an LID subset represents the full corpus, or
that the dashboard supplies scientific validation.

NFR31: Failure of HAI/LID import, offline training, or report generation must
not crash or degrade the active v1 runtime.

NFR32: The dashboard must be read-only with respect to datasets, splits,
training, calibration, metrics, manifests, and promotion.

NFR33: A promoted model bundle must load without refit/retraining and must be
rejected when any required artifact or hash is missing or incompatible.

NFR34: Batch and live processing of the same canonical sample must produce
equivalent features, tensor, score, and explanation within a frozen tolerance.

NFR35: The complete regression suite and new unit/integration/smoke gates must
pass before a v2 feature is enabled by default.

NFR36: Every final metric must report repeated-run dispersion or uncertainty,
not only the best seed or a single selected result.

NFR37: The current exploratory anomalies and May/June results must remain
historical evidence and must not be silently relabeled as final custom-v2 or
official-LID results.

### Additional Requirements

#### Authority and historical correction

- The July 2026 technical research supersedes the May 2026 global deprecation
  of the custom autoencoder. Custom v1 becomes
  `experimental_live_fingerprint_baseline`; custom v2 is a new candidate and
  can become `academically_validated_custom_fingerprint` only after its gates.
- The May offline ADFA-LD/LID architecture remains historical and reusable, but
  its random stratified 80/20 split must not govern temporal industrial data or
  trace-windowed LID v2 evaluation.
- Existing runs and artifacts are immutable history. Runs executed only on the
  embedded LID fixture must be reclassified as test evidence, regardless of
  legacy story titles containing “real”.
- The existing `epics.md` remains the implementation history. This update adds
  new epics/stories and must not renumber or rewrite completed historical work.
- The May 2026 Epic 8 and its Stories 8.1--8.4 are explicitly
  `SUPERSEDED — NOT AUTHORIZED`. They remain historical planning evidence but
  are not an implementation dependency and must not trigger removal of the
  custom autoencoder, automatic classifier reintegration, or any code change.

#### Technology and dependency constraints

- Reuse the existing Python, NumPy, Keras/Torch, `asyncua`, MinIO, MQTT,
  CometBFT/ABCI, and `unittest` stack.
- Prefer Python standard-library `csv`, `gzip`, `hashlib`, `json`,
  `dataclasses`, `time.perf_counter`, and `tracemalloc`.
- Do not add pandas, scikit-learn, PyYAML, PyArrow, jsonschema, a new broker,
  database, API framework, or cloud service unless a later approved change
  proves it indispensable.
- Keep `run_local_demo.py` and the current `scada/opcua_service.py` as the v1
  path/facade until baseline and migration gates pass.
- The only scientifically necessary new process boundary is the independent
  OPC UA server; dataset adapters remain offline modules/CLIs.

#### Contracts and module boundaries

- Add versioned contracts for `ProcessSample`, `ExperimentSpec`, dataset/source
  manifest, OPC UA observation, evaluation record, and model bundle.
- Add a pure v2 feature encoder shared by batch and live paths.
- Add a `dataset_generation` package for scenario running, custom batch,
  ground truth, parity/equivalence, and HAI import.
- Add independent `opcua_server` and `opcua_client` modules while preserving
  the legacy facade during migration.
- Add v2 dataset builder/artifact, preprocessing, calibration, bundle, split,
  inference, and evaluation modules without changing v1 artifact contracts.

#### Artifact lineage and publication

- Required lineage:
  `raw_hash -> canonical_hash -> split_manifest -> windows_hash ->
  scaler_hash -> model_hash -> threshold_calibration_hash -> metrics_hash ->
  evidence_index`.
- Write and validate shards/bulk before publishing the complete manifest.
- Dataset, scaler, model, threshold, schema, and evaluation are an indivisible
  promoted bundle for custom inference.
- Use explicit promotion IDs and rollback targets; never infer the champion by
  filename order or most-recent timestamp alone.

#### OPC UA evidence boundary

- The plant snapshot must branch to the edges and OPC writer before consensus.
- Use stable string NodeIds and resolve namespace index from a configured URI.
- Read `DataValue` fields through a separate `asyncua.Client` session over
  `opc.tcp`.
- Use a revision-A/read-batch/revision-B guard to reject mixed snapshots.
- Persist endpoint, namespace, node identities, status/timestamps, attempts,
  latency, freshness, security mode, and blocking reason.
- `SecurityMode=None` may be used only by explicit laboratory flag and cannot
  support a production-security claim.

#### Scientific protocol

- Pre-register scenario matrix, seeds, session lengths, operational regimes,
  split/grouping rules, sequence lengths, hyperparameter search, calibration
  method, target metrics, and stopping rules before final evaluation.
- Ground truth is generated by the experiment specification before prediction.
- The detector must not receive scenario label, expected class, intervention,
  or training eligibility as input features.
- Normal commanded transitions must be represented and evaluated separately
  from anomalous uncommanded changes.
- Never choose threshold or hyperparameters after inspecting anomaly-test or
  official test outcomes.
- Persist all planned repetitions, including failed or unfavorable runs.

#### HAI 20.07

- Use HAI 20.07, the corrected HAI 1.0 release, as the only new industrial
  public dataset.
- Acquire explicitly from the official repository and pin a reproducible
  repository state; record local SHA-256 values for the four source files.
- Preserve the official chronological file roles and evaluate temporal events.
- Keep HAI model/schema/scaler/threshold isolated from custom and HIDS models.

#### LID-DS 2021

- Initial measured scope is only the official `CVE-2017-7529` scenario.
- Unit fixtures remain small and synthetic and can prove only parser behavior.
- Official bytes, source and member hashes, real layout, trace inventory, split,
  and processed outputs are mandatory before `OFFICIAL_DATA_QUALIFIED`.
- Persist separate states `OFFICIAL_DATA_QUALIFIED`, `OFFICIAL_RUN_COMPLETE`,
  and `SUBSET_MODEL_GATE_PASSED`; training completion does not imply a passed
  quality gate.
- Report author metrics as `published_reference`, visually and semantically
  separate from local `measured_result`.
- A real-subset result authorizes only a claim about the selected official
  scenario, not the entire LID corpus or physical fingerprint.
- Missing official data produces an explicit non-executed/blocked status with
  no metric fabrication and does not block custom, OPC UA, or HAI work.

#### QA and operational gates

- Add golden v1, contract/invariant, batch/live parity, dataset qualification,
  model calibration, OPC round-trip/fail-closed, real HAI, real LID, comparison,
  and dashboard regression tests.
- Keep real external-data/infrastructure smokes opt-in through explicit
  variables such as `RUN_REAL_OPCUA_SMOKE`, `RUN_REAL_HAI_SMOKE`,
  `RUN_REAL_LID_SMOKE`, and `RUN_REAL_CUSTOM_V2_SMOKE`.
- The dashboard remains the last, optional demonstration layer. The academic
  critical path ends with reproducible comparison and claim-to-evidence
  indexing.

### UX Design Requirements

No standalone UX Design Specification was found. The existing dashboard is
already implemented, so the following additive requirements are extracted from
the Architecture, Seminar evidence, and technical research rather than
authorizing a redesign.

UX-DR1: With v2 flags disabled, existing dashboard API/state keys and the
current operator flow must remain compatible.

UX-DR2: The dashboard must obtain live cadence from the authoritative runtime
state/configuration and must not display a hard-coded `10s` when the configured
cycle is `30s` or another value.

UX-DR3: Fingerprint presentation must distinguish `model_available`,
`candidate_custom_fingerprint`, `MODEL_VALIDATED_CONTROLLED`, and `DEMO_READY`;
availability alone cannot be presented as scientific validation.

UX-DR4: The custom fingerprint view must show bundle/model ID, source dataset,
schema, scaler identity, threshold origin/value, score, margin, operating
regime, and limitation statement.

UX-DR5: The dashboard must show distinct visual states for consensus failure,
OPC unavailable/integrity failure, SCADA divergence, replay/freeze, and custom
ML anomaly.

UX-DR6: HAI, ADFA-LD, and LID result views must show dataset modality, subset,
evidence tier, result role, split protocol, run ID, provenance, and limitation.

UX-DR7: LID presentation must visibly distinguish `fixture_test`,
`published_reference`, and `official_real`, and must name the measured scope
`CVE-2017-7529` rather than imply full-corpus evaluation.

UX-DR8: The dashboard must provide links/identifiers to persisted manifests,
bundles, metrics, and evidence instead of recomputing them.

UX-DR9: Raw logs and technical evidence must remain accessible behind the
interpreted operator view.

UX-DR10: The dashboard must remain read-only for dataset import, generation,
splitting, training, calibration, metrics, and promotion.

UX-DR11: The optional anomaly demo must use existing scenario-control hooks and
the promoted custom bundle; UI-only effects or rewritten historical results are
forbidden.

UX-DR12: Every dashboard claim must include scope/limitation language that
prevents presenting simulated custom data as plant data, HAI as compressor
validation, HIDS as physical evidence, or the dashboard as the scientific
experiment.

### FR Coverage Map

FR1: Historical Epic 1 - Simulate the three compressor sensors.

FR2: Historical Epic 1 - Preserve one assigned local sensor per edge.

FR3: Historical Epic 1 - Publish edge observations through MQTT.

FR4: Historical Epic 1 - Consume peer observations through MQTT.

FR5: Historical Epic 1 - Maintain isolated edge-local replicated views.

FR6: Historical Epic 2 - Execute Byzantine-style consensus.

FR7: Historical Epic 2 - Persist the consensus trust ranking.

FR8: Historical Epic 2 - Exclude suspicious edge contributions.

FR9: Historical Epic 2 - Identify consensus participants.

FR10: Historical Epic 2 - Identify exclusions and reasons.

FR11: Historical Epic 2 - Expose full round trust evidence.

FR12: Historical Epic 2 - Represent failed consensus explicitly.

FR13: Historical Epic 2 - Emit structured consensus logs.

FR14: Historical Epic 2 - Emit consensus-failure alerts.

FR15: Historical Epic 3 - Expose simulated SCADA state through OPC UA.

FR16: Historical Epic 3 - Compare physical and SCADA sensor values.

FR17: Historical Epic 3 - Emit and enforce SCADA-divergence decisions.

FR18: Historical Epic 3 - Persist eligible valid artifacts only.

FR19: Epic 11 - Train the qualified custom normal-behavior autoencoder.

FR20: Epic 11 - Produce the versioned compressor fingerprint bundle.

FR21: Epic 11 - Produce score, classification, margin, and contributions.

FR22: Epic 11 - Save/load the complete model bundle without retraining.

FR23: Epic 11 - Evaluate controlled held-out temporal anomalies.

FR24: Epic 15 - Execute the complete multi-benchmark evidence track.

FR25: Epic 9 - Establish split-before-windowing protocols.

FR26: Epic 9 - Record architecture, hyperparameters, curves, and runtime.

FR27: Epic 9 - Record protocol-appropriate classification/event metrics.

FR28: Epic 9 - Store and retrieve immutable training/evaluation history.

FR29: Epic 11 - Restrict live promotion to a compatible custom bundle.

FR30: Epic 9 - Freeze and verify the v1 golden baseline.

FR31: Epic 9 - Classify dataset and result provenance tiers.

FR32: Epic 9 - Prevent fixtures/references from becoming measured evidence.

FR33: Epic 9 - Define the canonical versioned ProcessSample contract.

FR34: Epic 9 - Define the versioned ExperimentSpec contract.

FR35: Epic 10 - Generate deterministic accelerated custom sessions.

FR36: Epic 10 - Generate independent cycle/event ground truth.

FR37: Epic 10 - Produce the contextual custom-v2 feature schema.

FR38: Epic 10 - Execute the pre-registered scenario/repetition matrix.

FR39: Epic 10 - Partition by session before leakage-safe windowing.

FR40: Epic 10 - Publish verified immutable artifacts and manifest last.

FR41: Epic 10 - Qualify or reject the custom dataset explicitly.

FR42: Epic 12 - Publish a pre-consensus plant snapshot through OPC UA.

FR43: Epic 12 - Read the server through an independent opc.tcp client.

FR44: Epic 12 - Preserve DataValue quality, timestamps, and correlation.

FR45: Epic 12 - Reject stale, invalid, mixed, or unavailable snapshots.

FR46: Epic 12 - Compare only eligible OPC observations and persist evidence.

FR47: Epic 12 - Prove causal independence of OPC and consensus branches.

FR48: Epic 12 - Provide opt-in OPC mode with no silent fallback.

FR49: Epic 11 - Isolate training, validation, and calibration roles.

FR50: Epic 11 - Freeze and persist the independently calibrated threshold.

FR51: Epic 11 - Detect stale or incompatible fingerprint candidates.

FR52: Epic 11 - Report repeated controlled evaluation by scenario/regime.

FR53: Epic 11 - Promote and roll back only gate-approved bundles.

FR54: Epic 11 - Run promoted inference-only shadow operation.

FR55: Epic 13 - Acquire and qualify official HAI 20.07 files.

FR56: Epic 13 - Stream HAI while preserving chronology and official roles.

FR57: Epic 13 - Produce dataset-specific measured HAI evaluation.

FR58: Epic 13 - Bound HAI claims to external cyber-physical evidence.

FR59: Epic 14 - Enforce LID fixture/reference/official evidence tiers.

FR60: Epic 14 - Inventory and hash the official CVE-2017-7529 subset.

FR61: Epic 14 - Parse the real official scenario with no fixture fallback.

FR62: Epic 14 - Split LID by complete official trace/session.

FR63: Epic 14 - Execute and report the official measured subset run.

FR64: Epic 14 - Keep author metrics as published references only.

FR65: Epic 9 - Define the shared versioned EvaluationRecord envelope.

FR66: Epic 15 - Produce separate HIDS/cyber-physical tables and matrix.

FR67: Epic 15 - Produce the claim-to-evidence index.

FR68: Epic 16 - Display promoted custom evidence and OPC integrity.

FR69: Epic 16 - Display benchmark provenance, tier, scope, and limitation.

FR70: Epic 16 - Display distinct failure/anomaly channels.

FR71: Epic 16 - Demonstrate a pre-registered anomaly without mutation.

## Epic List

Historical Epics 1--7 and their implemented artifacts remain intact. The May
2026 Epic 8 is historical only and is `SUPERSEDED — NOT AUTHORIZED`. The new
roadmap therefore begins at Epic 9.

### Epic 9: Evidence-Safe Baseline and Reproducible Experiment Foundation

The researcher can reproduce the working v1 prototype, distinguish measured
evidence from fixtures and published references, and create inspectable,
versioned experiment/evaluation records without changing active v1 behavior.

**FRs covered:** FR25, FR26, FR27, FR28, FR30, FR31, FR32, FR33, FR34, FR65

**Dependencies:** Historical Epics 1--7 only. The superseded Epic 8 is not a
dependency.

**Implementation boundary:** Deliver only the minimum shared envelopes for
process samples, experiments, provenance, manifests, splits, and evaluation.
Do not force HIDS, cyber-physical, custom, and OPC data to share one feature
schema.

**Epic closure gate:** Golden v1 regression passes; v1 artifacts remain
unchanged; v2 namespaces and schema versions are additive; v2 flags remain off;
and provenance gates reject fixtures and published metrics as measured results.

### Epic 10: Qualified Custom Compressor Dataset v2

The researcher can generate plausible, deterministic, independently labelled
compressor experiments across operating speeds, normal transitions, controlled
anomalies, repetitions, and recovery, and can prove whether the resulting
dataset is scientifically qualified before model training.

**FRs covered:** FR35, FR36, FR37, FR38, FR39, FR40, FR41

**Dependencies:** Epic 9.

**Implementation boundary:** The simulator remains a controlled synthetic
plant, not a real plant or validated digital twin. Ground truth is independent
from prediction and cannot enter the feature tensor.

**Epic closure gate:** Deterministic generation and batch/live parity pass;
labels are independent; split leakage is zero; all lineage hashes resolve;
manifests are complete/atomic; scenario coverage and repetitions meet the
pre-registered protocol; and `DATASET_QUALIFIED` passes.

### Epic 11: Calibrated and Promotable Custom Fingerprint

The researcher can train, calibrate, blindly evaluate, explain, save, promote,
roll back, and run a compressor-specific fingerprint in inference-only shadow
mode using the qualified custom dataset.

**FRs covered:** FR19, FR20, FR21, FR22, FR23, FR29, FR49, FR50, FR51, FR52,
FR53, FR54

**Dependencies:** Epics 9 and 10.

**Implementation boundary:** Custom v1 remains an experimental baseline. HAI,
ADFA-LD, and LID models cannot be promoted as compressor models. Current
exploratory anomalies cannot be relabelled as final custom-v2 evidence.

**Epic closure gate:** Scaler, early stopping, and threshold use only their
authorized partitions; blind repeated evaluation is complete; all planned
outcomes and dispersion are reported; the bundle is complete, loadable without
refit, promotable, and rollback-safe; and shadow mode cannot train.

### Epic 12: Independent OPC UA Laboratory Validation

The researcher can demonstrate a genuine `opc.tcp` server/client round-trip
whose SCADA observation is causally independent from consensus, while
preserving quality, freshness, correlation, and fail-closed evidence.

**FRs covered:** FR42, FR43, FR44, FR45, FR46, FR47, FR48

**Dependencies:** Epic 9. It can proceed in parallel with Epics 10, 13, and 14.

**Implementation boundary:** The existing projected/in-memory OPC path remains
available only as v1 compatibility during migration. Laboratory operation does
not support a production OPC-security claim.

**Epic closure gate:** Independent TCP round-trip and causal-independence tests
pass; `Bad`, `Uncertain`, stale, mixed, missing, mismatched, and unavailable
observations fail closed; and enabled OPC mode contains no consensus-projection
fallback.

### Epic 13: HAI 20.07 External Cyber-Physical Evidence

The researcher can acquire, verify, process, train, and evaluate official HAI
20.07 data reproducibly as external cyber-physical evidence.

**FRs covered:** FR55, FR56, FR57, FR58

**Dependencies:** Epic 9. It can proceed in parallel with Epics 10, 12, and 14.

**Implementation boundary:** The HAI model, features, scaler, and threshold
remain dataset-specific and cannot be promoted as a compressor fingerprint.

**Epic closure gate:** The official source files, citation, license notice,
version, sizes, and hashes are qualified; chronological roles and temporal
boundaries are preserved; and locally measured point/event results and
limitations are persisted reproducibly.

### Epic 14: LID-DS 2021 Official-Scenario HIDS Evidence

The researcher can execute a locally measured result on the real official
`CVE-2017-7529` subset and clearly distinguish it from synthetic fixtures and
author-published reference metrics.

**FRs covered:** FR59, FR60, FR61, FR62, FR63, FR64

**Dependencies:** Epic 9. It can proceed in parallel with Epics 10, 12, and 13.

**Implementation boundary:** There is no fixture fallback or metric
fabrication. Problems obtaining official data do not block Epics 10--13 but
leave this Epic explicitly incomplete.

**Epic closure gate:** Official data and file hashes are qualified; the real
scenario parser and trace-isolated split pass; every planned seed is executed;
locally measured and author-published results remain separate; and the reported
scope is the official scenario subset, never the complete corpus.

### Epic 15: Defensible Multi-Track Academic Evidence Package

The researcher can report custom, HAI, ADFA-LD, and LID evidence in compatible,
scientifically bounded views and trace every claim to its source, split, model,
threshold, run, artifact, and limitation.

**FRs covered:** FR24, FR66, FR67

**Dependencies:** Epic 9; completed outputs from Epics 11--14; historical
ADFA-LD evidence from Epic 7. A partial package may be generated while Epic 14
is externally blocked, but it cannot satisfy the full completion gate.

**Implementation boundary:** Produce separate HIDS and cyber-physical result
tables plus a capability/limitation matrix. Never select a global champion or
compare incompatible raw loss, score, or threshold values.

**Epic closure gate:** `PARTIAL_EVIDENCE_PACKAGE` may explicitly show LID as
`not_executed/blocked` without invented metrics. `ACADEMIC_EVIDENCE_COMPLETE`
requires Epic 14's official measured run, complete separate tables, and a
claim-to-evidence index in which every claim resolves to evidence and a stated
limitation.

### Epic 16: Evidence-Backed Demonstration Dashboard

The researcher can demonstrate the promoted custom fingerprint, OPC integrity
state, and benchmark evidence through a truthful, read-only dashboard without
altering datasets, training, calibration, promotion, or persisted results.

**FRs covered:** FR68, FR69, FR70, FR71

**Dependencies:** Epics 11, 12, and 15.

**Implementation boundary:** This Epic is optional and presentation-only. It
cannot create scientific validity, trigger training, fabricate an anomaly, or
hide fixture/reference/measured distinctions.

**Epic closure gate:** The dashboard consumes persisted evidence, shows the
authoritative live cadence and distinct failure/anomaly channels, remains
read-only for scientific artifacts, and completes the separate milestone
`FULL_DEMONSTRATION_COMPLETE`.

### Dependency Summary

```text
Historical Epics 1--7
          |
        Epic 9
    /      |      |      \
 Epic 10  Epic 12 Epic 13 Epic 14
    |
 Epic 11
    \      |      |      /
           Epic 15
              |
           Epic 16 (optional)
```

All dependencies point backward. Epic 10 delivers a qualified dataset without
requiring Epic 11. Epics 12--14 remain independent after Epic 9. The academic
critical path ends at `ACADEMIC_EVIDENCE_COMPLETE` in Epic 15; the separate
demo milestone ends after optional Epic 16.
