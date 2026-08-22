---
stepsCompleted:
  - step-01-document-discovery
  - step-02-prd-analysis
  - step-03-epic-coverage-validation
  - step-04-ux-alignment
  - step-05-epic-quality-review
  - step-06-final-assessment
inputDocuments:
  - _bmad-output/planning-artifacts/prd.md
  - _bmad-output/planning-artifacts/prd-update-2026-05-21.md
  - _bmad-output/planning-artifacts/prd-update-2026-08-15.md
  - _bmad-output/planning-artifacts/architecture.md
  - _bmad-output/planning-artifacts/architecture-update-2026-05-21.md
  - _bmad-output/planning-artifacts/architecture-update-2026-08-15.md
  - _bmad-output/planning-artifacts/epics.md
  - _bmad-output/planning-artifacts/ux-design-specification.md
excludedHistoricalDocuments:
  - _bmad-output/planning-artifacts/epics-update-2026-05-21.md
  - _bmad-output/planning-artifacts/epics-update-2026-07-30.md
  - _bmad-output/planning-artifacts/epics-update-2026-08-15.md
---

# Implementation Readiness Assessment Report

**Date:** 2026-08-22
**Project:** parallel-truth-fingerprint-prototype

## Document Discovery

### PRD Files Included

- `prd.md` — base PRD, 35,827 bytes, modified 2026-06-02.
- `prd-update-2026-05-21.md` — historical amendment, 5,964 bytes, modified
  2026-06-02.
- `prd-update-2026-08-15.md` — controlling overlay, 51,767 bytes, modified
  2026-08-15.

### Architecture Files Included

- `architecture.md` — base architecture, 45,234 bytes, modified 2026-06-02.
- `architecture-update-2026-05-21.md` — historical amendment, 8,168 bytes,
  modified 2026-06-02.
- `architecture-update-2026-08-15.md` — controlling overlay, 26,351 bytes,
  modified 2026-08-15.

### Epics and Stories File Included

- `epics.md` — current consolidated artifact, 266,383 bytes, modified
  2026-08-22.

The dated May, July, and August epic-update files are excluded from primary
assessment because the current `epics.md` consolidates the approved roadmap and
identifies the earlier roadmaps as superseded planning history.

### UX File Included

- `ux-design-specification.md` — optional presentation specification, 38,030
  bytes, modified 2026-08-15. It remains non-blocking for scientific readiness.

### Discovery Issues

- No sharded document variants were found.
- No whole-versus-sharded duplicates require resolution.
- No required document category is missing.
- The base-plus-overlay order for PRD and architecture is explicit; the
  2026-08-15 overlays control conflicts.

## PRD Analysis

The inventory below is the resolved active composite extracted after reading
prd.md, the 2026-05-21 amendment, and the controlling 2026-08-15 overlay in
full. Amendment and supersession wording is retained. For identifiers whose
August matrix refers to a historical July normative sentence rather than
restating it completely, the current consolidated requirements inventory is
used to render the resolved wording; that epic artifact is validated
independently in the next workflow step.

### Functional Requirements

FR1: **AMENDED -> FR73-FR76.** Preserve simulation of temperature, pressure,
and RPM for one compressor as internal engineering-unit physics while custom
edge evidence follows the cited current-domain instrument profile.

FR2: **AMENDED -> FR73-FR76.** Preserve one assigned physical sensor per edge,
with the edge receiving primary raw-current evidence and its profile-owned
representations.

FR3: **RETAINED/AMENDED -> FR73, FR91; NFR39-NFR50.** Each edge publishes its
versioned observation through the local MQTT boundary.

FR4: **RETAINED/AMENDED -> FR73, FR91; NFR39-NFR50.** Each edge consumes peer
observations without bypassing version, quality, provenance, or trust rules.

FR5: **RETAINED/AMENDED -> FR73, FR91; NFR39-NFR50.** Each edge maintains its
own non-trusted local replicated compressor view without shared mutable state
collapsing edge independence.

FR6: **RETAINED/AMENDED -> FR91.** The system executes the existing real
CometBFT plus Go ABCI Byzantine-style validation path using the versioned v2
physical contract when v2 is active.

FR7: **RETAINED/AMENDED -> FR91; NFR49-NFR50.** A successful consensus result
exposes and persists its trust ranking as reconstructible evidence.

FR8: **RETAINED/AMENDED -> FR91.** Consensus can exclude a suspicious edge
contribution under the declared current-domain comparison basis.

FR9: **RETAINED/AMENDED -> FR91.** Each consensus result identifies its
participating edges and correlation identities.

FR10: **RETAINED/AMENDED -> FR91.** Each consensus result identifies excluded
edges and the evidence-based reason for each exclusion.

FR11: **RETAINED/AMENDED -> FR91; NFR50.** Each consensus result exposes the
complete ranking and evidence references for every edge in the round.

FR12: **RETAINED/AMENDED -> FR91; NFR47-NFR48.** Failure to reach valid
consensus remains an explicit, fail-closed outcome.

FR13: **RETAINED/AMENDED -> FR91; NFR50.** The system emits structured,
traceable logs for each consensus round.

FR14: **RETAINED/AMENDED -> FR91, FR93.** Consensus failure remains a distinct
state and, if the optional dashboard is implemented, a distinct presentation.

FR15: **SUPERSEDED -> FR90.** Do not implement a fake or consensus-projected
SCADA source as v2 evidence; use the independent pre-consensus OPC UA path.

FR16: **SUPERSEDED -> FR90-FR91.** Do not retain an anonymous circular
sensor-tolerance comparison; use eligible OPC UA evidence and the declared
comparison basis.

FR17: **SUPERSEDED -> FR90, FR93.** SCADA divergence is replaced by explicit
independent-OPC integrity and comparison outcomes, optionally presented without
control authority.

FR18: **AMENDED -> FR85, FR87, FR92; NFR40, NFR49.** Persist immutable,
role-separated eligible evidence rather than one ambiguous valid-data object.

FR19: **SUPERSEDED -> FR77-FR89.** Do not implement an LSTM-only fingerprint
premise; compare declared physical and syscall candidates under isolated truth.

FR20: **SUPERSEDED -> FR78, FR81, FR87.** A fingerprint is an immutable,
track-specific detector bundle and result, not an assumed single model.

FR21: **SUPERSEDED -> FR87-FR89.** Detector scores, decisions, and optional
fusion follow frozen track-specific calibration and synchronized evidence.

FR22: **SUPERSEDED -> FR87.** Save and load complete immutable detector bundles
without fitting or threshold recalculation.

FR23: **SUPERSEDED -> FR75, FR77-FR89.** Replay/freeze is a preregistered,
truth-isolated evaluation condition rather than proof by one legacy model.

FR24: **AMENDED -> FR82-FR84.** External benchmark work uses separate,
dataset-native ADFA-LD, LID-DS 2021, and HAI 23.05 roles rather than one generic
benchmark adapter or result claim.

FR25: **SUPERSEDED -> FR86; NFR41.** A universal stratified 80/20 sample split
is prohibited; complete official groups or independent runs split before
window formation.

FR26: **RETAINED/AMENDED -> FR87-FR88; NFR40.** Persist complete architecture,
hyperparameter, execution, dependency, data, calibration, and runtime identity
for every measured detector run.

FR27: **SUPERSEDED -> FR77-FR88.** Evaluation uses labels only after freeze and
reports protocol-appropriate anomaly, temporal, event, uncertainty, and quality
outcomes rather than one universal supervised-classification metric set.

FR28: **AMENDED -> FR87, FR92; NFR49.** Persist immutable role- and
version-separated run, bundle, metric, and evidence records; a mutable shared
history prefix is not scientific identity.

FR29: **SUPERSEDED -> FR87, FR89.** External ADFA-LD, LID-DS, or HAI models
never become compressor detectors; only compatible custom bundles may run in
their own modality and only synchronized custom scores are fusion-eligible.

FR30: **RETAINED.** Capture a v1 golden baseline across runtime, contracts,
artifacts, dashboard state, and experimental fingerprint behavior.

FR31: **RETAINED.** Classify every dataset and run by controlled provenance
tier and result role without overriding dataset-native scope.

FR32: **RETAINED.** Prevent fixtures or published statistics from being
represented as locally measured execution results.

FR33: **SUPERSEDED -> FR73-FR74.** `SignalObservation.v2` and profile-owned
derivation replace one universal `ProcessSample` evidence contract; OPC UA has
its separate FR90 contract.

FR34: **AMENDED -> FR75-FR77.** Declare controlled experiments through a
versioned `ExperimentSpec` whose schedules, numbers, interventions, and truth
follow provenance and access controls.

FR35: **AMENDED -> FR74-FR75, FR85; NFR46.** Accelerated simulator sessions may
support declared physical-only or test evidence, but final fusion evidence
requires synchronized physical observations and authentic syscalls from the
same correlated runs.

FR36: **AMENDED -> FR77, FR86; NFR41.** Generate truth independently, keep it
structurally absent from detector contracts, and join it only after freeze.

FR37: **AMENDED -> FR73-FR75, FR78.** Feature context, units, derivatives, and
commanded state are profile-owned and evidence-referenced, while intervention
truth remains protected.

FR38: **AMENDED -> FR75-FR77, FR88; NFR51.** Execute a preregistered scenario
matrix and preserve valid, invalid, aborted, unfavorable, and recovery runs.

FR39: **AMENDED -> FR86; NFR41.** Split every official group or custom run
before windowing and prevent windows crossing trace, file, boot, session,
process, scenario, gap, schema, or split boundaries.

FR40: **AMENDED -> FR85; NFR40, NFR49-NFR50.** Publish immutable verified
artifacts first and atomically publish the complete manifest last.

FR41: **AMENDED -> FR85-FR86; NFR40-NFR41, NFR45-NFR46, NFR49, NFR51.** Close
`DATASET_QUALIFIED` only after synchronized-stream, leakage, capture-quality,
correlation, durability, completeness, and reporting checks pass.

FR42: **AMENDED -> FR90; NFR42.** Publish a pre-consensus plant/transmitter
snapshot through OPC UA without granting analytics actuator authority.

FR43: **AMENDED -> FR90.** Read OPC UA only through a distinct real `opc.tcp`
client; internal server-object access is not eligible v2 evidence.

FR44: **AMENDED -> FR90; NFR46, NFR50.** Preserve OPC UA values, status,
timestamps, schema, producer/revision, and correlation for reconstruction.

FR45: **AMENDED -> FR90; NFR47.** Reject incomplete, stale, mixed, invalid,
unavailable, or mis-correlated OPC UA observations explicitly.

FR46: **AMENDED -> FR90, FR92; NFR50.** Consume only eligible OPC UA
observations and preserve every comparison and fail-closed diagnostic.

FR47: **AMENDED -> FR90; NFR50.** Prove OPC and consensus causal source
independence through a reconstructible branch-isolation round-trip test.

FR48: **AMENDED -> FR90; NFR48, NFR52.** Activate independent OPC mode only
through explicit versioned authorization and never silently fall back to a
consensus projection.

FR49: **AMENDED -> FR86; NFR41, NFR43-NFR44.** Fit preprocessing on eligible
normal training evidence, select on declared validation evidence, and calibrate
independently under the same candidate budget.

FR50: **AMENDED -> FR87; NFR44.** Freeze the threshold before test and bind its
origin and derivation to the immutable detector bundle.

FR51: **AMENDED -> FR87; NFR48.** Reject detector candidates when any governing
dataset, schema, preprocessing, calibration, bundle, dependency, or runtime
identity is stale or incompatible.

FR52: **AMENDED -> FR88; NFR43, NFR51.** Report only applicable
scenario-, severity-, sensor-, regime-, repetition-, temporal-, and
quality-aware metrics under fair budgets, retaining dispersion and limitations.

FR53: **AMENDED -> FR87; NFR48, NFR52.** Promotion and rollback select an
explicit immutable compatible bundle and require separate activity
authorization; planning approval cannot promote a model.

FR54: **AMENDED -> FR87; NFR47-NFR48.** Runtime shadow inference loads an exact
bundle, never fits, recalibrates, or guesses a latest artifact, and fails closed
on absence or incompatibility.

FR55: **SUPERSEDED -> FR84; NFR40.** Do not acquire HAI 20.07 for the new plan;
pin and verify HAI 23.05 instead.

FR56: **SUPERSEDED -> FR84, FR86; NFR47.** HAI 23.05 native roles and chronology
replace HAI 20.07 processing requirements.

FR57: **SUPERSEDED -> FR84, FR87-FR88.** HAI 23.05 receives its own immutable
preprocessing, detector, calibration, and evaluation path.

FR58: **SUPERSEDED -> FR84, FR92; NFR38.** Report HAI 23.05 only as external
native physical/SCADA evidence, never compressor validation.

FR59: **AMENDED -> FR83, FR92; NFR51.** Only qualified official LID evidence may
support a locally measured LID result; fixtures and published references remain
separate roles.

FR60: **AMENDED -> FR83; NFR40, NFR50.** Qualify the declared official LID-DS
2021 source, version, layout, citation, license scope, file inventory, sizes,
and hashes; no subset is mandatory until separately authorized.

FR61: **AMENDED -> FR83; NFR47.** Preserve the official LID schema and grouping,
reject ambiguous or empty layouts, and never substitute a fixture; no scenario
is a default requirement.

FR62: **AMENDED -> FR83, FR86; NFR41.** Split LID by official roles and complete
scenario/recording/trace/session groups before vocabulary fitting or windows.

FR63: **AMENDED -> FR83, FR86, FR88; NFR43-NFR44, NFR51.** Execute only the LID
scope, run count, stopping rules, and candidate budget declared by a later
authorized protocol and report every outcome and limitation.

FR64: **AMENDED -> FR83, FR86, FR92; NFR51.** Keep author-published LID metrics
reference-only and outside fitting, calibration, selection, and local measured
result calculations.

FR65: **AMENDED -> FR88, FR92; NFR40, NFR50.** Use a common provenance-rich
evaluation envelope without erasing modality- or dataset-specific semantics.

FR66: **AMENDED -> FR92; NFR38.** Produce separate dataset and modality result
tables plus a capability/limitation matrix; only the paired custom ablation may
compare physical, syscall, and fusion outcomes on the same runs.

FR67: **AMENDED -> FR92; NFR50-NFR51.** Link each academic claim through
immutable source, split, bundle, threshold, run, metric, limitation, and
scientific-status evidence.

FR68: **AMENDED -> FR92-FR93; NFR50, NFR52.** An optional dashboard may display
only frozen custom detector evidence and cannot create, recompute, promote, or
alter scientific artifacts.

FR69: **AMENDED -> FR92-FR93; NFR38, NFR51.** Optional presentation keeps HAI,
ADFA-LD, and LID native scope, evidence role, result role, version, run,
provenance, and limitations distinct.

FR70: **AMENDED -> FR93; NFR38, NFR42.** Optional presentation keeps consensus,
OPC, SCADA divergence, replay/freeze, physical, syscall, and fusion states
distinct and grants none of them control authority.

FR71: **AMENDED -> FR75, FR87, FR93; NFR52.** An optional dashboard may replay
or present only an already authorized preregistered frozen result; it cannot
generate, fit, calibrate, promote, fuse, or rewrite evidence.

FR72: The system represents exactly two detection modalities: physical
instrumentation and Linux host syscalls. It identifies 4-20 mA as a physical
representation and autoencoders as models in contracts, documentation,
reports, and any optional UI.

FR73: `SignalObservation.v2` preserves raw current in mA, current quality and
diagnostics, instrument/profile identity, source and observation timestamps,
sequence/correlation identity, deterministic normalized span, derived
engineering value/unit, schema version, and parameter-evidence references;
quality is evaluated before optional clipping or imputation.

FR74: The process model may calculate temperature, pressure, and RPM in
engineering units, but an edge receives primary evidence through its selected
transmitter profile. Exactly one profile-owned conversion derives normalized
span and engineering value from current; RPM remains 4-20 mA while supported
by the selected cited shaft-speed profile.

FR75: A versioned `ExperimentSpec` declares phases, profile, run/seed,
schedule, interventions, recovery, stopping rules, and evidence references.
The requested 25%-75% variation is `speed_reference_pct` or
`capacity_reference_pct` classified as `preregistered_factor`; it does not
imply power, ramp, dwell, repetition, or safety limits.

FR76: Every executable v2 numeric parameter has a stable ID, exactly one of
`direct`, `derived`, `measured`, `preregistered_factor`, or `mock`, and a record
of value, unit, source/decision and locator, derivation, applicable profile,
uncertainty/limitation where relevant, and authorized experiment. Anonymous
legacy values run only in labelled legacy-reproduction mode.

FR77: `ScenarioTruth.v1`, attack labels, scenario names, interventions, future
intervals, and evaluation-only metadata remain under a separate access
boundary, absent from detector-facing training and inference contracts, and
join frozen evidence only after the declared truth unlock.

FR78: The physical track compares LSTM-AE, GRU-AE, and declared simpler or
classical baselines fitted only on qualified normal training evidence under the
same current-domain schema, complete-run partitions, budget, repetitions, and
metrics. The current mixed-scale autoencoder is `LEGACY_BASELINE`, not the
final detector or a dataset, and commanded 25%-75% transitions remain distinct
from declared anomalies.

FR79: The custom syscall track runs an allowlisted controlled Linux edge
workload and captures the real kernel calls it actually emits through a
qualified Sysdig/eBPF or equivalent collector. The workload may be mocked; the
syscalls may not be fabricated or modified.

FR80: `SyscallEventBatch.v1` preserves run, edge, boot,
container/process/session, categorical syscall name/direction,
sequence/timestamps, kernel/ABI and collector identities,
loss/duplicate/gap/queue evidence, and raw-segment hashes without labels or
scenario truth. Fixture replay is test-only and excluded from formal custom
evaluation.

FR81: The syscall anomaly track treats calls categorically and compares
embedding-plus-LSTM, embedding-plus-GRU, and a transparent n-gram/STIDE-style
baseline fitted on qualified normal evidence under the same group-safe
protocol. Numeric syscall IDs are not continuous quantities and are not
optimized with reconstruction MSE solely because they are numbers.

FR82: ADFA-LD remains an offline external syscall benchmark with official
roles, trace identity, six attack families, source/archive hashes, known count
discrepancies, categorical semantics, and labels confined to evaluation truth;
the system neither fabricates timestamps nor executes dataset identifiers.

FR83: A version-specific LID-DS 2021 adapter preserves official
training/validation/test and scenario/recording boundaries plus the published
syscall schema. LID may inform custom capture design, but its example durations,
collector settings, and metrics remain cited references, not project constants.

FR84: The system pins and verifies HAI 23.05, preserves native tags, units,
chronology, official file roles, and separate labels, and uses a
version-specific physical/SCADA adapter. Its preprocessing, detector,
calibration, and evaluation remain separate; HAI is neither mass-converted to
mA nor presented as compressor data.

FR85: `PTFP-Custom-v1` contains synchronized physical observations and
captured Linux edge syscalls from the same experiment runs, immutable stream
manifests, clock/correlation evidence, modality quality, profile/config
identities, and separately protected truth. Custom rows are never inserted
into or represented as HAI, ADFA-LD, or LID-DS data.

FR86: Complete official groups or independent custom runs split before
windowing. Preprocessing/vocabulary fitting uses training only;
selection/thresholding uses declared validation/calibration only; and locked
test evidence remains unavailable until model, schema, preprocessing,
threshold, metrics, and policy are frozen.

FR87: Every evaluated or deployed detector bundle immutably binds weights and
architecture, feature order/schema or vocabulary, preprocessing,
training/calibration dataset and split hashes, frozen threshold and derivation,
dependency/runtime identity, and bundle hash. Load and inference never call
`fit` or recalculate a threshold.

FR88: Each track reports all applicable point/window and event/range outcomes,
including PR-AUC, precision, recall, F1, false-positive behavior, false events
per operating hour, time to detection, suitable confusion data, threshold
sensitivity, resource cost, modality quality/availability, and repeated-run
dispersion or uncertainty. Unfavorable and aborted planned runs remain visible.

FR89: Late fusion uses only frozen calibrated physical and syscall scores from
aligned windows of the same held-out `PTFP-Custom-v1` runs under a simple
preregistered policy before truth unlock. External ADFA/LID syscall records are
never joined with HAI physical rows to fabricate fusion.

FR90: The OPC UA server receives a pre-consensus plant/transmitter snapshot and
a distinct client reads it through `opc.tcp`, preserving `DataValue` status,
source/server timestamps, schema, and correlation. Invalid, stale, mixed,
missing, or unavailable evidence fails explicitly with no silent consensus
fallback.

FR91: Consensus v2 declares the instrument profile and comparison basis.
Same-profile redundant observations may compare in current domain;
cross-profile or cross-sensor aggregation uses documented dimensionless,
uncertainty-aware residuals. Python and Go produce deterministic identical
results from shared golden fixtures.

FR92: The final package contains separate ADFA-LD, LID-DS 2021, HAI 23.05, and
per-modality `PTFP-Custom-v1` tables, then a paired custom-only
physical/syscall/fusion ablation and capability/limitation matrix. It selects no
global cross-domain champion, and every claim resolves to source, version,
split, bundle, threshold/calibration, run, raw score/metric, and limitation.

FR93: **CONDITIONAL/OPTIONAL.** If Epic 18 is activated, a read-only dashboard
displays raw mA, normalized span, and engineering value as linked physical
representations; physical, syscall, and fusion channels separately; and scope,
provenance, quality, bundle, threshold origin, and limitations. It cannot
import, split, train, calibrate, promote, fuse, relabel, recompute, or rewrite
results and is not an implementation-readiness gate.

**Total Functional Requirements: 93.**

### Non-Functional Requirements

NFR1: **AMENDED -> NFR39, NFR44.** The prototype executes locally, while every
cadence or timing value is sourced, measured, or preregistered for its declared
use rather than inherited from a universal one-minute reference.

NFR2: **RETAINED.** The flow remains suitable for local academic demonstration
and inspection without hard real-time or high-frequency guarantees.

NFR3: **AMENDED -> NFR41-NFR42.** Preserve validation-before-trust; replicated
edge state is not valid until the applicable consensus decision completes.

NFR4: **AMENDED -> NFR41-NFR42; FR85-FR90.** Only explicitly eligible evidence
may progress, while invalid, anomalous, and truth data remain in separate
authorized paths.

NFR5: **AMENDED -> NFR38, NFR42; FR90-FR93.** Consensus, OPC integrity,
physical-detector, syscall-detector, and optional fusion outputs remain
semantically distinct without control authority.

NFR6: **RETAINED.** The prototype runs locally without requiring real cloud or
production industrial infrastructure.

NFR7: **RETAINED.** Every blocking failure is explicit rather than silent
success, empty normality, or fallback.

NFR8: **RETAINED.** Structured logs allow each pipeline stage and experiment
run to be inspected.

NFR9: **RETAINED/AMENDED -> NFR46, NFR50.** Every online cycle is traceable
across physical observation, consensus, OPC, persistence, detectors, and
eligible fusion.

NFR10: **RETAINED/AMENDED -> NFR40.** Academic execution is reproducible from
immutable source, configuration, code, data, split, bundle, and evaluation
identities.

NFR11: **SUPERSEDED -> FR72-FR93; NFR43.** Preserve local integration
boundaries, but do not require an LSTM-only service, fake OPC source, or mixed
modality semantics.

NFR12: **RETAINED.** The architecture stays local and simple, without
unnecessary cloud, Kubernetes, service mesh, API gateway, Kafka, new database,
or production-HMI scope.

NFR13: **RETAINED.** Python remains primary and Go remains confined to the
existing ABCI/consensus boundary.

NFR14: **RETAINED.** The prototype remains simple enough for one researcher to
run, inspect, and explain.

NFR15: **RETAINED/AMENDED -> NFR38, NFR50-NFR51.** Logs, manifests, metrics,
and any optional UI remain presentation-friendly without hiding evidence,
scope, or limitations.

NFR16: **RETAINED.** Modules preserve explicit ownership and trust boundaries.

NFR17: **RETAINED/AMENDED -> NFR49.** Object storage remains replaceable while
formal evidence is persistent, verified, restorable, and semantically stable.

NFR18: **RETAINED/AMENDED -> NFR40.** Repeated runs with the same frozen inputs
remain reproducible within a declared, evidenced numerical tolerance.

NFR19: **RETAINED/AMENDED -> NFR49-NFR50.** Run and evidence history remains
inspectable as flat versioned artifacts independently of any dashboard.

NFR20: **RETAINED/AMENDED -> NFR47.** Active acquisition/control never blocks
on import, batch generation, training, sweeps, evaluation, or reporting.

NFR21: **RETAINED/AMENDED -> NFR40, NFR50-NFR51.** Every source and run records
organization, year, version, subset, counts, schema, citation/location,
license/notice, evidence role, result role, and hashes.

NFR22: **AMENDED -> NFR40, NFR48.** Historical v1 evidence remains replayable
through explicit versions; incompatible v1/v2 artifacts fail closed.

NFR23: **AMENDED -> NFR40, NFR49-NFR50.** Content-addressed bulk artifacts
verify before the complete manifest or pointer is atomically published.

NFR24: **AMENDED -> NFR41.** Zero detector-facing leakage applies across every
official and custom run, trace, file, boot, session, process, gap, group, and
overlapping-window boundary.

NFR25: **AMENDED -> FR84-FR85; NFR47.** HAI and custom evidence processing uses
bounded-memory streaming or sharding and cannot hide partial evidence or
degrade acquisition/control.

NFR26: **RETAINED.** Credentials and private keys remain outside Git,
manifests, evidence, and reports; imported OPC, CSV, archive, and dataset fields
are untrusted input.

NFR27: **AMENDED -> FR90; NFR39, NFR44, NFR47.** Every invalid OPC observation
fails explicitly; no unsupported one-cycle timing limit applies without
parameter evidence or preregistration.

NFR28: **SUPERSEDED -> FR76, FR88; NFR39, NFR44, NFR51.** Fixed initial FPR,
false-event, detection-repetition, or similar targets do not enter v2 without a
complete sourced, measured, or preregistered decision record and full outcome
reporting.

NFR29: **AMENDED -> FR82-FR84; NFR40, NFR52.** Dataset use remains zero-cost
and redistribution-safe, but actionability depends on official source,
version, hashes, license scope, and separate authorization; blocked LID access
does not block ADFA-LD or other independent tracks.

NFR30: **AMENDED -> NFR38; FR84, FR92.** Claims cannot present custom data as a
real plant, HAI as compressor validation, syscall benchmarks as physical
evidence, a subset as a whole corpus, or UI as scientific validation.

NFR31: **AMENDED -> NFR47-NFR48.** Active v1 acquisition/control and historical
replay remain independent of offline import, training, and reporting failures.

NFR32: **AMENDED -> FR93; NFR42, NFR52.** Any optional dashboard has
presentation-only authority and cannot mutate evidence, analytics,
authorization, or actuator commands.

NFR33: **AMENDED -> FR87; NFR48.** Exact immutable detector bundles load
without fitting or recalibration and fail closed on any missing or incompatible
artifact, schema, runtime, or hash.

NFR34: **AMENDED -> FR73-FR74, FR87; NFR39, NFR44.** Batch and live processing
of the same canonical observation produce equivalent conversion, tensor,
score, and explanation within an evidenced or preregistered tolerance.

NFR35: **RETAINED.** Regression and new quality gates pass before a v2 feature
is enabled by default; test success does not authorize implementation or
activation.

NFR36: **AMENDED -> FR88; NFR51.** Every applicable final metric includes
repeated-run dispersion or uncertainty and never reports only a selected best
seed.

NFR37: **AMENDED -> NFR40, NFR48, NFR51.** May/June and v1 anomalies and
results remain immutable historical evidence and are never silently relabelled
as final custom-v2 or official-dataset results.

NFR38: Contracts, logs, reports, and any optional UI use exactly the two
modalities consistently and never call 4-20 mA a modality, an autoencoder a
dataset, HAI compressor data, or controlled custom data real-plant evidence.

NFR39: Formal v2 startup or experiment validation rejects every executable
numeric parameter lacking the complete FR76 record. Citations establish
transferability only for applicable selected profiles, and measured or
preregistered values are labelled as such.

NFR40: Formal results reconstruct from immutable code, dependency, container,
source, dataset, profile, configuration, split, schema, bundle, score,
truth-unlock, fusion-policy, and evaluation-code identities.

NFR41: No detector-facing artifact contains truth, attack labels, future
values, unauthorized partitions, or windows crossing run, trace, scenario,
file, boot, session, process, gap, or official dataset boundaries.

NFR42: Control and experiment scheduling remain independent from security
analytics. Detector, dashboard, storage, MQTT, OPC UA, capture, and evaluator
failure can never create or alter actuator/compressor commands.

NFR43: LSTM, GRU, and baseline comparisons within one track use the same
eligible partitions, schema, tuning access, declared budget, repetitions, and
primary metrics. Model superiority is measured, never presumed.

NFR44: Thresholds, windows, duration, repetitions, ramp/dwell, queue capacity,
capture-loss policy, fusion weights, and performance targets are selected by
applicable direct sources, preserved measurement, or preregistration with
sensitivity analysis; no publication supplies universal values.

NFR45: Custom syscall evidence exposes workload attribution, collector/kernel
identity, gaps, duplicates, drops, queue depth, storage lag, and measured
overhead. Affected windows follow the preregistered flag/exclusion/abort policy
and are never silently normal.

NFR46: Every custom stream preserves source/observation time, ordered sequence,
run/edge/boot/session identity, and declared clock/correlation uncertainty
sufficient to prove a physical-syscall join; unresolved or mixed identities
prevent fusion.

NFR47: Acquisition/control stays available when storage or analytics degrades.
High-volume syscalls use bounded queues and append-only segments, and missing,
partial, delayed, or aborted evidence is explicit.

NFR48: v1 evidence remains replayable while v2 contracts, consensus state,
storage namespaces, and bundles are explicitly versioned. Incompatible model,
schema, runtime, or hash identities fail closed.

NFR49: Formal evidence uses persistent, verified, restorable storage and
append-only or content-addressed keys; mutable latest-only state is never the
sole scientific record.

NFR50: Every reported decision or metric resolves from experiment and source
identities through raw segments, canonical observations, partitions/windows,
bundle, score, truth join, and evaluation record without UI or hidden state.

NFR51: All planned valid, invalid, aborted, and unfavorable runs are retained
and reported with applicable uncertainty, resource/quality evidence,
limitations, and locally-measured versus published-reference status.

NFR52: Planning approval is machine- and human-readable and remains distinct
from authorization to implement, download data, capture syscalls, train,
execute experiments, or activate a feature.

**Total Non-Functional Requirements: 52.**

### Additional Requirements

- The 2026-08-15 overlay controls every conflict with the base PRD, May
  amendment, July proposal, and July epic inventory; identifiers remain visible
  for traceability and are not silently reused.
- Approval remains planning-only. It authorizes no implementation, dataset
  acquisition, model fitting or promotion, Linux syscall capture, workload or
  simulator campaign, long-running experiment, or dashboard activation.
- The product has exactly two detection modalities: physical instrumentation
  and authentic Linux-host syscalls. A 4-20 mA loop is a physical
  representation; models and datasets are not modalities.
- ADFA-LD, LID-DS 2021, HAI 23.05, and PTFP-Custom-v1 retain distinct evidence
  roles. External datasets are never joined row-by-row; only synchronized
  PTFP-Custom-v1 runs may support the paired physical/syscall/fusion ablation.
- Scenario truth and dataset labels are evaluator-only and remain outside every
  detector-facing training and inference contract until the declared freeze.
- The 25%-75% request is a preregistered speed/capacity reference factor, not
  electrical power, a safety limit, or a universal compressor recommendation.
- Fixed thresholds, windows, timings, repetitions, queues, loss tolerances,
  fusion weights, and performance targets require direct, derived, measured, or
  preregistered evidence; no publication supplies a universal project value.
- Custom syscalls must be authentic captured kernel events. Workload behavior
  may be mocked only under the applicable evidence rules; syscalls may never be
  fabricated, renumbered, or modified.
- The simulator is controlled research evidence, not a real plant, validated
  compressor digital twin, certified safety system, or standards-conformant
  product.
- The dashboard is presentation-only and cannot create, alter, recompute,
  promote, fuse, relabel, or rewrite scientific evidence or control commands.

### PRD Completeness Assessment

**Strengths:** The composite defines 93 traceable FR identifiers, 52 traceable
NFR identifiers, explicit dataset roles, a two-modality boundary, leakage-safe
experimental lifecycle, immutable bundles, protocol-appropriate reporting,
and a strict planning-versus-execution authorization boundary. Historical
fixed-value and fake-OPC assumptions are explicitly superseded.

**Issues requiring later readiness resolution:**

1. **Fragmented normative source:** FR30-FR71 and NFR22-NFR37 rely on binding
   matrices that refer to the historical July epic inventory for their complete
   original sentences. The current epics.md reconciles them, but the PRD set
   is not a self-contained single normative specification.
2. **New academic-veracity rule not yet reflected in the PRD:** the approved
   epics now require every domain number and mock to prove authentic
   non-reproducibility where applicable, an exact official-document locator,
   transferability to the selected component, and material linkage to a bounded
   research question, evidence track, and final comparison-package element.
   FR76/NFR39 require provenance and applicability but do not yet state that
   complete strengthened rule.
3. **Dashboard authority ambiguity:** FR93 makes the dashboard read-only, while
   the later UX and epic artifacts make Epic 18 entirely optional and excluded
   from scientific readiness. The PRD does not state that optional/non-blocking
   status as explicitly.
4. **Academic source verification remains pending:** the PRD lists primary or
   official sources, but this step does not prove that each exact number, mock,
   dataset version, metric, and claimed transfer is supported by the cited
   locator. That evidence audit is required before a final readiness decision.

## Epic Coverage Validation

### Coverage Matrix

| FR Number | Resolved PRD Requirement | Epic Coverage | Story Coverage | Status |
| --- | --- | --- | --- | --- |
| FR1 | **AMENDED -> FR73-FR76.** Preserve simulation of temperature, pressure, and RPM for one compressor as internal engineering-unit physics while custom edge evidence follows the cited current-domain instrument profile. | Epic 10 - Preserve compressor physics while moving edge evidence to the profile-owned current-domain boundary. | 10.2, 10.3 | Covered |
| FR2 | **AMENDED -> FR73-FR76.** Preserve one assigned physical sensor per edge, with the edge receiving primary raw-current evidence and its profile-owned representations. | Epic 10 - Preserve one assigned sensor per edge through `SignalObservation.v2`. | 10.2 | Covered |
| FR3 | **RETAINED/AMENDED -> FR73, FR91; NFR39-NFR50.** Each edge publishes its versioned observation through the local MQTT boundary. | Epic 10 - Publish versioned physical observations through MQTT. | 10.2 | Covered |
| FR4 | **RETAINED/AMENDED -> FR73, FR91; NFR39-NFR50.** Each edge consumes peer observations without bypassing version, quality, provenance, or trust rules. | Epic 10 - Consume peer observations through the versioned physical path. | 10.2 | Covered |
| FR5 | **RETAINED/AMENDED -> FR73, FR91; NFR39-NFR50.** Each edge maintains its own non-trusted local replicated compressor view without shared mutable state collapsing edge independence. | Epic 10 - Preserve independent non-trusted edge-local views. | 10.2 | Covered |
| FR6 | **RETAINED/AMENDED -> FR91.** The system executes the existing real CometBFT plus Go ABCI Byzantine-style validation path using the versioned v2 physical contract when v2 is active. | Epic 11 - Execute current-domain CometBFT/ABCI consensus. | 11.1, 11.3, 11.4, 11.6 | Covered |
| FR7 | **RETAINED/AMENDED -> FR91; NFR49-NFR50.** A successful consensus result exposes and persists its trust ranking as reconstructible evidence. | Epic 11 - Persist reconstructible trust ranking evidence. | 11.2, 11.3, 11.5, 11.6 | Covered |
| FR8 | **RETAINED/AMENDED -> FR91.** Consensus can exclude a suspicious edge contribution under the declared current-domain comparison basis. | Epic 11 - Exclude suspicious contributions under the declared basis. | 11.2, 11.3, 11.6 | Covered |
| FR9 | **RETAINED/AMENDED -> FR91.** Each consensus result identifies its participating edges and correlation identities. | Epic 11 - Identify round participants and correlation identities. | 11.1, 11.3, 11.4, 11.5, 11.6 | Covered |
| FR10 | **RETAINED/AMENDED -> FR91.** Each consensus result identifies excluded edges and the evidence-based reason for each exclusion. | Epic 11 - Identify exclusions and evidence-based reasons. | 11.2, 11.3, 11.6 | Covered |
| FR11 | **RETAINED/AMENDED -> FR91; NFR50.** Each consensus result exposes the complete ranking and evidence references for every edge in the round. | Epic 11 - Expose complete round ranking and evidence references. | 11.2, 11.3, 11.5, 11.6 | Covered |
| FR12 | **RETAINED/AMENDED -> FR91; NFR47-NFR48.** Failure to reach valid consensus remains an explicit, fail-closed outcome. | Epic 11 - Represent consensus failure explicitly and fail closed. | 11.1, 11.2, 11.3, 11.6 | Covered |
| FR13 | **RETAINED/AMENDED -> FR91; NFR50.** The system emits structured, traceable logs for each consensus round. | Epic 11 - Emit structured traceable consensus logs. | 11.1, 11.3, 11.4, 11.5, 11.6 | Covered |
| FR14 | **RETAINED/AMENDED -> FR91, FR93.** Consensus failure remains a distinct state and, if the optional dashboard is implemented, a distinct presentation. | Epic 11 - Preserve the distinct consensus-failure state; Epic 18 may optionally present it. | 11.6, 18.2 | Covered |
| FR15 | **SUPERSEDED -> FR90.** Do not implement a fake or consensus-projected SCADA source as v2 evidence; use the independent pre-consensus OPC UA path. | Epic 12 - Replace fake/projected SCADA with independent OPC UA evidence. | 12.2, 12.6 | Covered |
| FR16 | **SUPERSEDED -> FR90-FR91.** Do not retain an anonymous circular sensor-tolerance comparison; use eligible OPC UA evidence and the declared comparison basis. | Epic 12 - Replace circular tolerance comparison with an eligible, declared independent comparison. | 12.4, 12.6 | Covered |
| FR17 | **SUPERSEDED -> FR90, FR93.** SCADA divergence is replaced by explicit independent-OPC integrity and comparison outcomes, optionally presented without control authority. | Epic 12 - Produce explicit OPC integrity/comparison outcomes; Epic 18 may optionally present them. | 12.6 | Covered |
| FR18 | **AMENDED -> FR85, FR87, FR92; NFR40, NFR49.** Persist immutable, role-separated eligible evidence rather than one ambiguous valid-data object. | Epic 10 - Persist role-separated physical evidence; Epic 17A assembles the synchronized custom evidence record. | 10.6, 10.7, 17A.3, 17A.4 | Covered |
| FR19 | **SUPERSEDED -> FR77-FR89.** Do not implement an LSTM-only fingerprint premise; compare declared physical and syscall candidates under isolated truth. | Epic 13 - Replace the LSTM-only premise with fair physical candidates. | 13.1, 13.3 | Covered |
| FR20 | **SUPERSEDED -> FR78, FR81, FR87.** A fingerprint is an immutable, track-specific detector bundle and result, not an assumed single model. | Epic 13 - Produce an immutable physical detector bundle. | 13.5, 13.8 | Covered |
| FR21 | **SUPERSEDED -> FR87-FR89.** Detector scores, decisions, and optional fusion follow frozen track-specific calibration and synchronized evidence. | Epic 13 - Produce frozen physical scores and decisions; Epic 17A handles eligible paired fusion. | 13.6, 13.8, 17A.5, 17A.6 | Covered |
| FR22 | **SUPERSEDED -> FR87.** Save and load complete immutable detector bundles without fitting or threshold recalculation. | Epic 13 - Save and load the complete physical bundle without fitting. | 13.5, 13.8 | Covered |
| FR23 | **SUPERSEDED -> FR75, FR77-FR89.** Replay/freeze is a preregistered, truth-isolated evaluation condition rather than proof by one legacy model. | Epic 13 - Evaluate replay/freeze and other preregistered conditions with isolated truth. | 13.7 | Covered |
| FR24 | **AMENDED -> FR82-FR84.** External benchmark work uses separate, dataset-native ADFA-LD, LID-DS 2021, and HAI 23.05 roles rather than one generic benchmark adapter or result claim. | Epics 15A, 15B, and 16 - Execute dataset-native external benchmark tracks; Epic 17B reports them separately. | 15A.1, 15A.4, 15A.6, 15B.5, 15B.7, 16.4, 16.7, 17A.7, 17B.1, 17B.2, 17B.4 | Covered |
| FR25 | **SUPERSEDED -> FR86; NFR41.** A universal stratified 80/20 sample split is prohibited; complete official groups or independent runs split before window formation. | Epics 13, 14, 15A, 15B, 16, and 17A - Replace universal sample splitting with group/run-before-window partitioning. | 13.2, 14.4, 15A.3, 15A.5, 15B.4, 15B.6, 16.3, 16.5, 17A.4, 17A.5 | Covered |
| FR26 | **RETAINED/AMENDED -> FR87-FR88; NFR40.** Persist complete architecture, hyperparameter, execution, dependency, data, calibration, and runtime identity for every measured detector run. | Epic 9 - Define complete immutable run identity; Epics 13-17B populate the track-specific records. | 9.6, 15A.3, 15A.6, 15B.7, 16.7, 17A.2, 17A.4, 17B.1, 17B.5, 17B.6 | Covered |
| FR27 | **SUPERSEDED -> FR77-FR88.** Evaluation uses labels only after freeze and reports protocol-appropriate anomaly, temporal, event, uncertainty, and quality outcomes rather than one universal supervised-classification metric set. | Epics 13, 14, 15A, 15B, 16, 17A, and 17B - Replace one universal metric set with protocol-appropriate outcomes. | 13.7, 14.8, 14.9, 15A.6, 15B.7, 16.6, 16.7, 17A.7, 17B.2, 17B.3 | Covered |
| FR28 | **AMENDED -> FR87, FR92; NFR49.** Persist immutable role- and version-separated run, bundle, metric, and evidence records; a mutable shared history prefix is not scientific identity. | Epic 9 - Define immutable role/version evidence history; Epics 13-17B publish their records through it. | 9.5, 9.6, 15A.1, 15A.6, 15B.7, 16.7, 17A.2, 17A.4, 17B.1, 17B.5, 17B.6 | Covered |
| FR29 | **SUPERSEDED -> FR87, FR89.** External ADFA-LD, LID-DS, or HAI models never become compressor detectors; only compatible custom bundles may run in their own modality and only synchronized custom scores are fusion-eligible. | Epic 13 - Restrict runtime physical shadow inference to a compatible custom bundle; Epic 17A permits only custom paired fusion. | 13.6, 13.8, 17A.5, 17A.6 | Covered |
| FR30 | **RETAINED.** Capture a v1 golden baseline across runtime, contracts, artifacts, dashboard state, and experimental fingerprint behavior. | Epic 9 - Freeze the complete v1 evidence baseline. | 9.1, 9.5 | Covered |
| FR31 | **RETAINED.** Classify every dataset and run by controlled provenance tier and result role without overriding dataset-native scope. | Epic 9 - Classify dataset and result provenance roles. | 9.2, 9.3 | Covered |
| FR32 | **RETAINED.** Prevent fixtures or published statistics from being represented as locally measured execution results. | Epic 9 - Prevent fixtures/references from becoming measured results. | 9.2, 9.3, 9.5 | Covered |
| FR33 | **SUPERSEDED -> FR73-FR74.** `SignalObservation.v2` and profile-owned derivation replace one universal `ProcessSample` evidence contract; OPC UA has its separate FR90 contract. | Epic 10 - Replace universal `ProcessSample` evidence with `SignalObservation.v2` and profile-owned derivation. | 10.2, 10.3 | Covered |
| FR34 | **AMENDED -> FR75-FR77.** Declare controlled experiments through a versioned `ExperimentSpec` whose schedules, numbers, interventions, and truth follow provenance and access controls. | Epic 10 - Define the versioned, provenance-bound `ExperimentSpec`. | 10.4, 17A.1 | Covered |
| FR35 | **AMENDED -> FR74-FR75, FR85; NFR46.** Accelerated simulator sessions may support declared physical-only or test evidence, but final fusion evidence requires synchronized physical observations and authentic syscalls from the same correlated runs. | Epic 10 - Support declared accelerated physical-only/test sessions; Epic 17A admits only same-run authentic paired evidence. | 10.3, 10.4, 10.6, 17A.1, 17A.3 | Covered |
| FR36 | **AMENDED -> FR77, FR86; NFR41.** Generate truth independently, keep it structurally absent from detector contracts, and join it only after freeze. | Epic 10 - Generate and structurally isolate scenario truth. | 10.5, 17A.1 | Covered |
| FR37 | **AMENDED -> FR73-FR75, FR78.** Feature context, units, derivatives, and commanded state are profile-owned and evidence-referenced, while intervention truth remains protected. | Epic 10 - Define profile-owned context, units, and derived features. | 10.1, 10.3, 17A.1, 17A.4 | Covered |
| FR38 | **AMENDED -> FR75-FR77, FR88; NFR51.** Execute a preregistered scenario matrix and preserve valid, invalid, aborted, unfavorable, and recovery runs. | Epic 10 - Define and preserve the preregistered experiment matrix; Epic 17A executes the formal paired campaign. | 10.4, 10.6, 17A.1, 17A.3 | Covered |
| FR39 | **AMENDED -> FR86; NFR41.** Split every official group or custom run before windowing and prevent windows crossing trace, file, boot, session, process, scenario, gap, schema, or split boundaries. | Epic 9 - Define group/run-before-window policy; Epics 10 and 13-17A enforce it for their data. | 9.8, 10.6, 10.7, 17A.4 | Covered |
| FR40 | **AMENDED -> FR85; NFR40, NFR49-NFR50.** Publish immutable verified artifacts first and atomically publish the complete manifest last. | Epic 9 - Define verified immutable publication and manifest-last rules; Epics 10 and 17A apply them to custom evidence. | 9.6, 9.7, 10.6, 10.7, 17A.2, 17A.3, 17A.4 | Covered |
| FR41 | **AMENDED -> FR85-FR86; NFR40-NFR41, NFR45-NFR46, NFR49, NFR51.** Close `DATASET_QUALIFIED` only after synchronized-stream, leakage, capture-quality, correlation, durability, completeness, and reporting checks pass. | Epic 10 - Qualify physical experiment evidence; Epic 17A closes the synchronized `DATASET_QUALIFIED` gate. | 10.6, 10.7, 17A.3, 17A.4 | Covered |
| FR42 | **AMENDED -> FR90; NFR42.** Publish a pre-consensus plant/transmitter snapshot through OPC UA without granting analytics actuator authority. | Epic 12 - Publish the pre-consensus plant/transmitter snapshot. | 12.1, 12.6 | Covered |
| FR43 | **AMENDED -> FR90.** Read OPC UA only through a distinct real `opc.tcp` client; internal server-object access is not eligible v2 evidence. | Epic 12 - Read OPC UA only through a distinct real client. | 12.2, 12.3, 12.6 | Covered |
| FR44 | **AMENDED -> FR90; NFR46, NFR50.** Preserve OPC UA values, status, timestamps, schema, producer/revision, and correlation for reconstruction. | Epic 12 - Preserve OPC values, quality, timestamps, revision, and correlation. | 12.3, 12.4, 12.6 | Covered |
| FR45 | **AMENDED -> FR90; NFR47.** Reject incomplete, stale, mixed, invalid, unavailable, or mis-correlated OPC UA observations explicitly. | Epic 12 - Reject incomplete, stale, mixed, invalid, or unavailable OPC evidence. | 12.3, 12.4, 12.6 | Covered |
| FR46 | **AMENDED -> FR90, FR92; NFR50.** Consume only eligible OPC UA observations and preserve every comparison and fail-closed diagnostic. | Epic 12 - Compare only eligible OPC evidence and persist diagnostics. | 12.4, 12.6 | Covered |
| FR47 | **AMENDED -> FR90; NFR50.** Prove OPC and consensus causal source independence through a reconstructible branch-isolation round-trip test. | Epic 12 - Prove OPC/consensus causal source independence. | 12.5, 12.6 | Covered |
| FR48 | **AMENDED -> FR90; NFR48, NFR52.** Activate independent OPC mode only through explicit versioned authorization and never silently fall back to a consensus projection. | Epic 12 - Activate versioned OPC mode explicitly with no silent fallback. | 12.2, 12.3, 12.6 | Covered |
| FR49 | **AMENDED -> FR86; NFR41, NFR43-NFR44.** Fit preprocessing on eligible normal training evidence, select on declared validation evidence, and calibrate independently under the same candidate budget. | Epic 13 - Separate physical training, validation, and calibration access. | 13.1, 13.2, 13.6, 17A.5 | Covered |
| FR50 | **AMENDED -> FR87; NFR44.** Freeze the threshold before test and bind its origin and derivation to the immutable detector bundle. | Epic 13 - Freeze and bind the physical threshold before test. | 13.4, 13.6, 17A.5 | Covered |
| FR51 | **AMENDED -> FR87; NFR48.** Reject detector candidates when any governing dataset, schema, preprocessing, calibration, bundle, dependency, or runtime identity is stale or incompatible. | Epic 13 - Reject stale or incompatible physical candidates. | 13.5, 13.8, 17A.5 | Covered |
| FR52 | **AMENDED -> FR88; NFR43, NFR51.** Report only applicable scenario-, severity-, sensor-, regime-, repetition-, temporal-, and quality-aware metrics under fair budgets, retaining dispersion and limitations. | Epic 13 - Report repeated scenario/regime-aware physical evaluation. | 13.3, 13.7, 17A.7 | Covered |
| FR53 | **AMENDED -> FR87; NFR48, NFR52.** Promotion and rollback select an explicit immutable compatible bundle and require separate activity authorization; planning approval cannot promote a model. | Epic 13 - Promote and roll back only explicit authorized physical bundles. | 13.8, 17A.2 | Covered |
| FR54 | **AMENDED -> FR87; NFR47-NFR48.** Runtime shadow inference loads an exact bundle, never fits, recalibrates, or guesses a latest artifact, and fails closed on absence or incompatibility. | Epic 13 - Serve inference-only physical shadow results without fitting. | 13.6, 13.8, 17A.5 | Covered |
| FR55 | **SUPERSEDED -> FR84; NFR40.** Do not acquire HAI 20.07 for the new plan; pin and verify HAI 23.05 instead. | Epic 16 - Replace HAI 20.07 acquisition with pinned HAI 23.05. | 16.1, 16.7 | Covered |
| FR56 | **SUPERSEDED -> FR84, FR86; NFR47.** HAI 23.05 native roles and chronology replace HAI 20.07 processing requirements. | Epic 16 - Preserve HAI 23.05 native roles and chronology. | 16.1, 16.2, 16.3, 16.6, 16.7 | Covered |
| FR57 | **SUPERSEDED -> FR84, FR87-FR88.** HAI 23.05 receives its own immutable preprocessing, detector, calibration, and evaluation path. | Epic 16 - Keep the HAI 23.05 detector and evaluation dataset-specific. | 16.2, 16.3, 16.4, 16.5, 16.6, 16.7 | Covered |
| FR58 | **SUPERSEDED -> FR84, FR92; NFR38.** Report HAI 23.05 only as external native physical/SCADA evidence, never compressor validation. | Epic 16 - Bound HAI claims to external native physical/SCADA evidence. | 16.6, 16.7 | Covered |
| FR59 | **AMENDED -> FR83, FR92; NFR51.** Only qualified official LID evidence may support a locally measured LID result; fixtures and published references remain separate roles. | Epic 15B - Separate LID fixture, published-reference, and official-real roles. | 15B.2, 15B.3, 15B.7 | Covered |
| FR60 | **AMENDED -> FR83; NFR40, NFR50.** Qualify the declared official LID-DS 2021 source, version, layout, citation, license scope, file inventory, sizes, and hashes; no subset is mandatory until separately authorized. | Epic 15B - Qualify the separately authorized official LID source/scope. | 15B.1, 15B.2, 15B.7 | Covered |
| FR61 | **AMENDED -> FR83; NFR47.** Preserve the official LID schema and grouping, reject ambiguous or empty layouts, and never substitute a fixture; no scenario is a default requirement. | Epic 15B - Parse official LID layout with no fixture fallback. | 15B.3, 15B.7 | Covered |
| FR62 | **AMENDED -> FR83, FR86; NFR41.** Split LID by official roles and complete scenario/recording/trace/session groups before vocabulary fitting or windows. | Epic 15B - Split LID by official roles and complete groups. | 15B.4, 15B.7 | Covered |
| FR63 | **AMENDED -> FR83, FR86, FR88; NFR43-NFR44, NFR51.** Execute only the LID scope, run count, stopping rules, and candidate budget declared by a later authorized protocol and report every outcome and limitation. | Epic 15B - Execute only the later-authorized LID scope and report every outcome or an explicit blocked state. | 15B.1, 15B.5, 15B.6, 15B.7 | Covered |
| FR64 | **AMENDED -> FR83, FR86, FR92; NFR51.** Keep author-published LID metrics reference-only and outside fitting, calibration, selection, and local measured result calculations. | Epic 15B - Keep author-published metrics reference-only. | 15B.7 | Covered |
| FR65 | **AMENDED -> FR88, FR92; NFR40, NFR50.** Use a common provenance-rich evaluation envelope without erasing modality- or dataset-specific semantics. | Epic 9 - Define the common provenance-rich evaluation envelope; Epic 17B uses it for the final package. | 9.2, 9.6, 17B.1, 17B.4, 17B.5, 17B.6 | Covered |
| FR66 | **AMENDED -> FR92; NFR38.** Produce separate dataset and modality result tables plus a capability/limitation matrix; only the paired custom ablation may compare physical, syscall, and fusion outcomes on the same runs. | Epic 17B - Produce separate result tables and the limitation matrix. | 17B.2, 17B.3, 17B.4, 17B.6 | Covered |
| FR67 | **AMENDED -> FR92; NFR50-NFR51.** Link each academic claim through immutable source, split, bundle, threshold, run, metric, limitation, and scientific-status evidence. | Epic 17B - Produce the immutable claim-to-evidence index. | 17B.1, 17B.5, 17B.6 | Covered |
| FR68 | **AMENDED -> FR92-FR93; NFR50, NFR52.** An optional dashboard may display only frozen custom detector evidence and cannot create, recompute, promote, or alter scientific artifacts. | Epic 18 (optional) - Present frozen custom detector evidence read-only. | 18.1, 18.2, 18.4 | Covered |
| FR69 | **AMENDED -> FR92-FR93; NFR38, NFR51.** Optional presentation keeps HAI, ADFA-LD, and LID native scope, evidence role, result role, version, run, provenance, and limitations distinct. | Epic 18 (optional) - Present benchmark-native scope and limitations. | 18.3 | Covered |
| FR70 | **AMENDED -> FR93; NFR38, NFR42.** Optional presentation keeps consensus, OPC, SCADA divergence, replay/freeze, physical, syscall, and fusion states distinct and grants none of them control authority. | Epic 18 (optional) - Present distinct consensus, OPC, detector, and fusion states without control authority. | 18.2, 18.4 | Covered |
| FR71 | **AMENDED -> FR75, FR87, FR93; NFR52.** An optional dashboard may replay or present only an already authorized preregistered frozen result; it cannot generate, fit, calibrate, promote, fuse, or rewrite evidence. | Epic 18 (optional) - Present only authorized preregistered frozen anomaly evidence without mutation. | 17A.5, 17A.6, 18.1, 18.3, 18.4 | Covered |
| FR72 | The system represents exactly two detection modalities: physical instrumentation and Linux host syscalls. It identifies 4-20 mA as a physical representation and autoencoders as models in contracts, documentation, reports, and any optional UI. | Epic 9 - Establish the global two-modality semantic boundary; all later epics enforce it and Epic 18 may present it. | 9.2, 10.2, 14.9, 17A.4, 17A.6, 18.2 | Covered |
| FR73 | `SignalObservation.v2` preserves raw current in mA, current quality and diagnostics, instrument/profile identity, source and observation timestamps, sequence/correlation identity, deterministic normalized span, derived engineering value/unit, schema version, and parameter-evidence references; quality is evaluated before optional clipping or imputation. | Epic 10 - Define and preserve `SignalObservation.v2`. | 10.2 | Covered |
| FR74 | The process model may calculate temperature, pressure, and RPM in engineering units, but an edge receives primary evidence through its selected transmitter profile. Exactly one profile-owned conversion derives normalized span and engineering value from current; RPM remains 4-20 mA while supported by the selected cited shaft-speed profile. | Epic 10 - Separate process physics from profile-owned current derivation. | 10.1, 10.2, 10.3 | Covered |
| FR75 | A versioned `ExperimentSpec` declares phases, profile, run/seed, schedule, interventions, recovery, stopping rules, and evidence references. The requested 25%-75% variation is `speed_reference_pct` or `capacity_reference_pct` classified as `preregistered_factor`; it does not imply power, ramp, dwell, repetition, or safety limits. | Epic 10 - Define `ExperimentSpec` and the 25%-75% preregistered reference. | 10.4, 17A.1 | Covered |
| FR76 | Every executable v2 numeric parameter has a stable ID, exactly one of `direct`, `derived`, `measured`, `preregistered_factor`, or `mock`, and a record of value, unit, source/decision and locator, derivation, applicable profile, uncertainty/limitation where relevant, and authorized experiment. Anonymous legacy values run only in labelled legacy-reproduction mode. | Epic 9 - Establish the parameter provenance gate; later epics consume it. | 9.3, 9.4, 10.1, 10.4, 17A.1, 17A.2 | Covered |
| FR77 | `ScenarioTruth.v1`, attack labels, scenario names, interventions, future intervals, and evaluation-only metadata remain under a separate access boundary, absent from detector-facing training and inference contracts, and join frozen evidence only after the declared truth unlock. | Epic 10 - Establish isolated truth and controlled unlock. | 10.5, 17A.1, 17A.5 | Covered |
| FR78 | The physical track compares LSTM-AE, GRU-AE, and declared simpler or classical baselines fitted only on qualified normal training evidence under the same current-domain schema, complete-run partitions, budget, repetitions, and metrics. The current mixed-scale autoencoder is `LEGACY_BASELINE`, not the final detector or a dataset, and commanded 25%-75% transitions remain distinct from declared anomalies. | Epic 13 - Compare physical custom candidates; Epic 16 applies the fair candidate protocol to HAI. | 13.1, 13.3, 16.4 | Covered |
| FR79 | The custom syscall track runs an allowlisted controlled Linux edge workload and captures the real kernel calls it actually emits through a qualified Sysdig/eBPF or equivalent collector. The workload may be mocked; the syscalls may not be fabricated or modified. | Epic 14 - Run a controlled workload and capture authentic kernel calls. | 14.1, 14.2, 14.3, 14.7, 14.9, 17A.3 | Covered |
| FR80 | `SyscallEventBatch.v1` preserves run, edge, boot, container/process/session, categorical syscall name/direction, sequence/timestamps, kernel/ABI and collector identities, loss/duplicate/gap/queue evidence, and raw-segment hashes without labels or scenario truth. Fixture replay is test-only and excluded from formal custom evaluation. | Epic 14 - Define and preserve `SyscallEventBatch.v1`. | 14.3, 14.4, 14.7, 14.9 | Covered |
| FR81 | The syscall anomaly track treats calls categorically and compares embedding-plus-LSTM, embedding-plus-GRU, and a transparent n-gram/STIDE-style baseline fitted on qualified normal evidence under the same group-safe protocol. Numeric syscall IDs are not continuous quantities and are not optimized with reconstruction MSE solely because they are numbers. | Epic 14 - Compare custom categorical syscall candidates; Epics 15A and 15B apply compatible candidate families to external syscall benchmarks. | 14.5, 14.6, 14.7, 14.8, 14.9, 15A.4, 15B.5 | Covered |
| FR82 | ADFA-LD remains an offline external syscall benchmark with official roles, trace identity, six attack families, source/archive hashes, known count discrepancies, categorical semantics, and labels confined to evaluation truth; the system neither fabricates timestamps nor executes dataset identifiers. | Epic 15A - Preserve and evaluate ADFA-LD in its external syscall role. | 15A.1, 15A.2, 15A.3, 15A.4, 15A.5, 15A.6 | Covered |
| FR83 | A version-specific LID-DS 2021 adapter preserves official training/validation/test and scenario/recording boundaries plus the published syscall schema. LID may inform custom capture design, but its example durations, collector settings, and metrics remain cited references, not project constants. | Epic 15B - Preserve and evaluate the separately authorized LID-DS 2021 scope through its official schema. | 15B.1, 15B.2, 15B.3, 15B.4, 15B.5, 15B.6, 15B.7 | Covered |
| FR84 | The system pins and verifies HAI 23.05, preserves native tags, units, chronology, official file roles, and separate labels, and uses a version-specific physical/SCADA adapter. Its preprocessing, detector, calibration, and evaluation remain separate; HAI is neither mass-converted to mA nor presented as compressor data. | Epic 16 - Preserve and evaluate HAI 23.05 in its native physical domain. | 16.1, 16.2, 16.3, 16.4, 16.5, 16.6, 16.7 | Covered |
| FR85 | `PTFP-Custom-v1` contains synchronized physical observations and captured Linux edge syscalls from the same experiment runs, immutable stream manifests, clock/correlation evidence, modality quality, profile/config identities, and separately protected truth. Custom rows are never inserted into or represented as HAI, ADFA-LD, or LID-DS data. | Epic 17A - Publish synchronized `PTFP-Custom-v1` from the physical and authentic-syscall producers delivered by Epics 10 and 14. | 14.9, 17A.1, 17A.2, 17A.3, 17A.4 | Covered |
| FR86 | Complete official groups or independent custom runs split before windowing. Preprocessing/vocabulary fitting uses training only; selection/thresholding uses declared validation/calibration only; and locked test evidence remains unavailable until model, schema, preprocessing, threshold, metrics, and policy are frozen. | Epic 9 - Define the leakage-safe lifecycle; Epics 13-17A enforce it for their tracks and Epic 17B verifies it in the final evidence chain. | 9.5, 9.8, 13.2, 14.4, 15A.3, 15B.4, 16.3, 17A.1, 17A.2, 17A.4 | Covered |
| FR87 | Every evaluated or deployed detector bundle immutably binds weights and architecture, feature order/schema or vocabulary, preprocessing, training/calibration dataset and split hashes, frozen threshold and derivation, dependency/runtime identity, and bundle hash. Load and inference never call `fit` or recalculate a threshold. | Epic 9 - Define immutable bundle/evidence identities; Epics 13-17A produce exact bundles and scores. | 9.6, 13.5, 13.6, 14.6, 14.7, 15A.5, 15B.6, 16.5, 17A.2, 17A.5, 17A.6 | Covered |
| FR88 | Each track reports all applicable point/window and event/range outcomes, including PR-AUC, precision, recall, F1, false-positive behavior, false events per operating hour, time to detection, suitable confusion data, threshold sensitivity, resource cost, modality quality/availability, and repeated-run dispersion or uncertainty. Unfavorable and aborted planned runs remain visible. | Epic 9 - Define the evaluation envelope; Epics 13-17A generate track-specific outcomes and Epic 17B reports them completely. | 9.6, 13.7, 14.8, 15A.6, 15B.7, 16.6, 16.7, 17A.7, 17B.1, 17B.2, 17B.3, 17B.5, 17B.6 | Covered |
| FR89 | Late fusion uses only frozen calibrated physical and syscall scores from aligned windows of the same held-out `PTFP-Custom-v1` runs under a simple preregistered policy before truth unlock. External ADFA/LID syscall records are never joined with HAI physical rows to fabricate fusion. | Epic 17A - Execute only preregistered custom same-run late fusion. | 17A.1, 17A.5, 17A.6, 17A.7 | Covered |
| FR90 | The OPC UA server receives a pre-consensus plant/transmitter snapshot and a distinct client reads it through `opc.tcp`, preserving `DataValue` status, source/server timestamps, schema, and correlation. Invalid, stale, mixed, missing, or unavailable evidence fails explicitly with no silent consensus fallback. | Epic 12 - Deliver independent fail-closed OPC UA evidence. | 12.2, 12.3, 12.4, 12.5, 12.6 | Covered |
| FR91 | Consensus v2 declares the instrument profile and comparison basis. Same-profile redundant observations may compare in current domain; cross-profile or cross-sensor aggregation uses documented dimensionless, uncertainty-aware residuals. Python and Go produce deterministic identical results from shared golden fixtures. | Epic 11 - Deliver deterministic current-domain consensus v2. | 11.1, 11.2, 11.3, 11.4, 11.5, 11.6 | Covered |
| FR92 | The final package contains separate ADFA-LD, LID-DS 2021, HAI 23.05, and per-modality `PTFP-Custom-v1` tables, then a paired custom-only physical/syscall/fusion ablation and capability/limitation matrix. It selects no global cross-domain champion, and every claim resolves to source, version, split, bundle, threshold/calibration, run, raw score/metric, and limitation. | Epic 17B - Deliver the separate result tables, paired ablation, limitation matrix, and claim evidence; Epic 18 may only project them. | 17B.1, 17B.2, 17B.3, 17B.4, 17B.5, 17B.6, 18.1, 18.3 | Covered |
| FR93 | **CONDITIONAL/OPTIONAL.** If Epic 18 is activated, a read-only dashboard displays raw mA, normalized span, and engineering value as linked physical representations; physical, syscall, and fusion channels separately; and scope, provenance, quality, bundle, threshold origin, and limitations. It cannot import, split, train, calibrate, promote, fuse, relabel, recompute, or rewrite results and is not an implementation-readiness gate. | Epic 18 (optional) - Present immutable evidence through the existing read-only dashboard without becoming a readiness gate. | 18.1, 18.2, 18.3, 18.4 | Covered |

### Missing Requirements

No functional requirements are missing from either the epic coverage map or explicit story-level traceability.

### Coverage Statistics

- Total PRD FRs: 93
- FRs declared in the epic coverage map: 93
- FRs referenced by detailed stories: 93
- Missing FRs: 0
- Coverage percentage: 100.0%
- Epics-only FR identifiers not present in the resolved PRD inventory: 0

The matrix validates requirement presence only. Story quality, architectural
alignment, optional UX scope, and scientific-source truthfulness are assessed
in later steps.

## UX Alignment Assessment

### UX Document Status

**Found:** `ux-design-specification.md`, completed 2026-08-15.

The specification is explicitly optional, presentation-only, desktop-first,
single-page, and non-blocking. It reuses the existing Python-served
HTML/CSS/JavaScript dashboard and requires no redesign, frontend framework,
mobile product, formal accessibility certification, production HMI, or complex
interaction model.

### UX to PRD Alignment

Aligned areas:

- Exactly two modalities remain visible: physical instrumentation and Linux
  host syscalls.
- Raw mA, normalized span, engineering value, profile, unit, quality, and
  freshness remain linked representations of one physical modality.
- Physical, syscall, and fusion results remain separate channels.
- External datasets retain their native scope and cannot appear as synchronized
  custom fusion evidence.
- Missing, stale, degraded, invalid, blocked, aborted, legacy, and unpublished
  states remain explicit rather than receiving fabricated values.
- The dashboard cannot train, calibrate, promote, fuse, evaluate, relabel,
  recompute, control, or rewrite scientific evidence.

### UX to Architecture Alignment

Aligned areas:

- The controlling architecture places the dashboard at the outer composition
  boundary with presentation-only authority.
- The existing local Python HTTP/HTML/CSS/JavaScript surface can support the
  bounded display without a frontend migration or new service.
- Separate dashboard credentials, no truth access, immutable evidence reads,
  and no analytics-to-control conduit support the read-only UX.
- Architecture-level failure semantics ensure dashboard absence or disagreement
  cannot alter acquisition, control, artifacts, evaluator output, or G9.
- Story 18.4 explicitly hides or disables historical operator controls in the
  evidence mode and rejects mutation requests, resolving the existing
  dashboard-control-surface risk at story level.

### Alignment Issues

1. **Optionality mismatch — Epic 18 only.** FR93 uses mandatory “shall” wording
   and the architecture promotion order ends with read-only presentation,
   whereas the UX specification and current Epic 18 declare the dashboard
   optional and excluded from scientific implementation-readiness gates. The
   later approved product decision is clear, but the PRD/architecture wording
   should be amended before Epic 18 itself is authorized.
2. **Live/current versus frozen-package mismatch — Epic 18 only.** The UX
   repeatedly describes automatically loading the current or most recently
   published read model and showing the system while it operates. Story 18.1
   instead requires an explicitly selected immutable package with `G9_PASS`.
   A mutable `latest` or live payload cannot be the scientific identity. Epic
   18 must either define two visibly distinct modes—historical live-demo state
   and frozen evidence-package presentation—or narrow the UX to the exact
   selected package. Neither mode may present unqualified live state as a
   published result.
3. **Existing controls require a mode boundary.** The brownfield dashboard has
   runtime, scenario, and compressor controls. Architecture and Story 18.4
   require those routes to be unavailable in the evidence-only mode. The
   acceptance criteria cover the requirement, but implementation must prove
   server-side rejection rather than merely hide buttons.

### Warnings

- Visual palette, spacing, the approximate 1100px breakpoint, responsive
  behavior, accessibility suggestions, and component patterns are guidance
  only and cannot become scientific acceptance gates.
- Dashboard output is never scientific validation and cannot repair missing
  provenance, invalid evidence, an unsupported number, or an inadmissible mock.
- These UX issues do **not** block scientific Epics 9-17B. They condition only
  separate authorization of the optional Epic 18.

## Epic Quality Review

### Structural Results

- Detailed epics reviewed: 12.
- Detailed stories reviewed: 81.
- BDD acceptance scenarios reviewed: 505.
- Stories with complete As-a/I-want/So-that and Given/When/Then structure:
  81/81.
- Stories with explicit FR traceability: 81/81.
- Forward story dependencies: 0.
- Placeholders: 0.
- Broad upfront database/entity creation: none.
- Brownfield project foundation: present; the historical `uv init --bare`
  starter has already been applied and is not a new Epic 9 dependency.

### Epic Best-Practice Assessment

| Epic | User/research value | Stories | Dependency result | Assessment |
| --- | --- | ---: | --- | --- |
| 9 | Researcher can reconstruct and trust the brownfield baseline and its evidence rules. | 8 | Historical Epics 1-7 only | Pass |
| 10 | Researcher can produce qualified evidence-grounded physical experiments. | 7 | Epic 9 | Pass |
| 11 | Researcher can validate physical evidence through deterministic current-domain consensus. | 6 | Epics 9-10 | Pass |
| 12 | Researcher can compare against causally independent OPC UA evidence. | 6 | Epics 9-11 | Pass |
| 13 | Researcher can compare, calibrate, freeze, evaluate, and shadow a physical detector. | 8 | Epics 9-10; no future dependency | Pass |
| 14 | Researcher can capture authentic Linux syscalls and evaluate a categorical detector. | 9 | Epics 9-10 | Pass |
| 15A | Researcher can reproduce ADFA-LD independently as an external syscall benchmark. | 6 | Epic 9 only | Pass |
| 15B | Researcher can qualify/evaluate LID-DS 2021 or preserve an honest blocked state. | 7 | Epic 9 only; does not block 15A | Pass |
| 16 | Researcher can evaluate HAI 23.05 in its native physical/SCADA domain. | 7 | Epic 9 only | Pass |
| 17A | Researcher can produce synchronized custom evidence and a truth-blind paired fusion result. | 7 | Earlier producer epics only | Pass |
| 17B | Researcher can publish and reconstruct the defensible academic evidence package. | 6 | Earlier evidence tracks; blocked LID is admissible evidence | Pass |
| 18 | Researcher may optionally present a frozen package in the existing dashboard. | 4 | Epic 17B; terminal/non-blocking | Conditional pass subject to UX issues |

All epics describe researcher or evaluator outcomes rather than infrastructure
milestones. Every declared dependency points backward. Independent benchmark
tracks do not block one another, and Epic 17B explicitly accepts the qualified
LID result or its honest blocked/not-executed record.

### Acceptance-Criteria Quality

- Every story includes happy-path, failure, invalid/missing evidence, provenance,
  immutability, and authority-boundary behavior appropriate to its scope.
- Criteria are testable through contract validation, exact identities, hashes,
  manifests, statuses, deterministic replay/reconstruction, or explicit gate
  decisions rather than subjective visual approval.
- No story depends on a later-numbered story in the same epic.
- Storage and namespaces are introduced when their evidence consumers first
  need them; there is no all-tables-upfront story.
- Brownfield compatibility is covered through baseline freeze, versioned
  fixtures/contracts, shadow activation, explicit routing, fail-closed mismatch,
  and immutable rollback identities.

### Critical Violations

None found. There are no technical-only epics, circular dependencies, forward
story dependencies, missing BDD structures, or epic-sized stories that require
future functionality to become useful.

### Major Issue

1. **Architecture contract lags the strengthened academic-veracity story
   rules.** The current architecture defines `ParameterEvidence.v1` with ID,
   value, unit, class, source/decision locator, derivation, profile, and
   experiment scope. The approved Cross-Epic Mock Admission Guardrail and
   Stories 9.3, 9.4, and 17B.5 additionally require authentic-reproduction
   feasibility, official-source authority for externally asserted domain
   values, exact prototype component, bounded research question,
   dataset/modality track, affected final package element, and explicit
   transferability. A developer cannot implement one authoritative contract
   while those required fields remain absent from the controlling architecture.

   **Remediation:** amend the PRD FR76/NFR39 wording and the architecture-owned
   source/parameter/mock-admission contracts before implementation
   authorization. The architecture must name validation ownership and
   fail-closed behavior for every new field. This is a scientific readiness
   blocker, not a request to weaken the stories.

### Minor Concerns

1. **Story 9.4 is large but cohesive:** 101 lines and 11 acceptance scenarios
   cover all five parameter classifications, mock rejection, deterministic
   serialization, and the G1-style gate. It remains one bounded validator, but
   the later create-story workflow should decompose implementation into schema,
   class-specific validators, relevance/transfer checks, canonicalization, and
   gate tests.
2. **Stories 9.3, 9.5, and 9.6 are foundation-heavy:** their source catalog,
   golden fixtures, and manifest work is necessary user-facing research value,
   but implementation tasks should remain narrow and avoid creating unused
   infrastructure.
3. **Epic 18 is structurally valid but conditionally aligned:** the optionality,
   frozen-versus-live presentation, and server-side control rejection issues
   documented in the UX assessment must be resolved only if Epic 18 is
   separately activated.

### Best-Practice Verdict

The epic/story decomposition passes structural quality review for scientific
Epics 9-17B. The stories are ordered, traceable, independently completable, and
testable. Readiness still cannot pass until the architecture/PRD contract lag
and the forthcoming academic-source audit are resolved.

## Academic Veracity Audit

### Scope and Method

This audit applies the approved Cross-Epic Mock Admission Guardrail to the
currently active scientific claims, parameter records, mock boundaries,
dataset identities, and final comparison design. It does not authorize a
download, runtime, experiment, model fit, capture, or implementation.

The local source register, `parameter-evidence.csv`, and seven relevant archived
PDFs were checked. Their computed SHA-256 values match
`docs/reference-archive/catalog/checksums.sha256`. Exact pages were extracted,
and the four pages carrying the core Rockwell, Electro-Sensors, Danfoss, and HAI
claims were also rendered and visually inspected. Current official owner,
manufacturer, standards-body, kernel, Docker, and primary-paper pages were
checked where the archive intentionally stores only a link.

Status meanings:

- **PASS:** the current planning claim and its bounded transfer are supported.
- **CONDITIONAL:** the source establishes identity or method, but the formal run
  must still pin and qualify the actual artifact under an existing story gate.
- **BLOCKED:** the current record cannot authorize formal implementation or
  execution until the stated evidence defect is corrected.

### Audit Results

| Item | Authentic reproduction and source finding | Transfer to this prototype and final comparison | Status |
| --- | --- | --- | --- |
| Archived-source integrity | Rockwell, Electro-Sensors, Danfoss, HAI, DOE, NIST IR 8089, and Jozefowicz PDF hashes exactly match the source-register checksum file. | Establishes immutable document identity only; it does not by itself establish transferability. | PASS |
| 4-20 mA normalized span | Rockwell 5034-UM003A-EN-P, PDF p. 22, “Scaling,” Table 7 directly maps 4 mA to 0%, 12 mA to 50%, and 20 mA to 100%. The NI official scaling article independently describes two-point linear scaling. | `(I_mA-4)/16` is a transparent derivation only for a declared linear 4-20 mA profile. It is one representation of the physical signal, not another modality. It can affect the custom physical table and paired custom ablation. | PASS |
| Engineering-unit conversion | The [NI 4-20 mA scaling guidance](https://knowledge.ni.com/KnowledgeArticleDetails?id=kA00Z000000PASfSAO&l=en-US) supports deriving a straight-line scale from two known endpoints. | `LRV+z*(URV-LRV)` is valid only when LRV, URV, units, and the selected instrument profile are independently frozen. The formula does not authorize anonymous endpoint values. | PASS |
| RPM 4-20 mA profile | Electro-Sensors FB420 2.0 ES730 Rev I, PDF pp. 1-2, states that output is directly proportional to shaft speed and specifies programmable endpoints: 4 mA at user minimum RPM and 20 mA at user maximum RPM. The [official product page](https://www.electro-sensors.com/products/shaft-speed-sensors/fb420) agrees. | Strong transfer exists to the prototype's bounded RPM-observation component. It supports a sensor representation, not a universal compressor-speed range, drive command, or safety limit. Exact user minimum/maximum RPM values still belong to the selected profile. | PASS |
| Requested 25%-75% schedule | No manufacturer document makes 25% or 75% an official CDS 803 operating recommendation. The Danfoss guide supports a scalable current reference, while DOE shows that part-load behavior and minimum useful speed vary by compressor design. | These are legitimate researcher-selected factors only as `preregistered_factor`. The current ledger incorrectly couples them to the Danfoss source and has no frozen decision ID, bounded-question linkage, or final-result locator. The values are not rejected, but the current records cannot authorize execution. | BLOCKED |
| Derived 8-16 mA schedule | Arithmetic `4+16*0.25=8` and `4+16*0.75=16` is correct under a linear 0%-100%/4-20 mA command profile. Danfoss AJ330233902305, PDF p. 29, §4.4.3, establishes only that terminals 53/54 support scalable 0/4-20 mA inputs; p. 72 defines the analog reference. | The cited guide does not prove that the selected CDS 803 configuration maps exactly 4 mA to 0% and 20 mA to 100%. The derived values must remain proposed until the exact device/profile configuration or a separately authorized experimental mapping is frozen and linked. | BLOCKED |
| Compressor/process simulator | NIST IR 8089, PDF p. 8, explicitly supports a bounded testbed that emulates industrial systems without replicating a whole plant; PDF p. 54 limits conclusions to the represented process and use. DOE Sourcebook §5 and Figure 2.8 support qualitative variable-speed/capacity/power relationships and show design-dependent limitations. | The repository has no real compressor/plant acquisition boundary, so a bounded research simulator may be admissible in principle. However, the active ledger contains zero `mock` records and no immutable capability-gap/admission record for process dynamics, noise, delay, faults, or any domain number. Official sources do not supply one universal compressor model. Formal simulator work is blocked until each included behavior/value is admitted and linked to an output that can change the custom comparison; otherwise it must be removed from formal mode. | BLOCKED |
| Linux workload and syscalls | Linux tracepoints provide authentic kernel hooks; the [official Sysdig repository](https://github.com/draios/sysdig) documents OS-level syscall/event capture and durable trace files; the [official LID-DS repository](https://github.com/LID-DS/LID-DS) supplies the controlled Docker-recording precedent. Docker Desktop runs Linux containers inside its Linux VM, so that VM/kernel is the named host-capture boundary on Windows. | Authentic calls are reproducible and therefore may not be mocked. The project should execute a controlled allowlisted workload and capture what it actually emits. A workload behavior may be mocked only after the same capability-gap rule; “mocked workload” is not permission to fabricate, renumber, replay as executable, or modify syscall evidence. This supports the custom syscall table and paired ablation. | PASS |
| OPC UA observation semantics | OPC UA Part 4, [DataValue §7.11](https://reference.opcfoundation.org/specs/OPC-10000-4/7.11), defines value, StatusCode, source timestamp, and server timestamp. Part 8, [BaseAnalogType §5.3.2.2](https://reference.opcfoundation.org/specs/OPC-10000-8/5.3.2), defines engineering units and instrument/engineering ranges. | These specifications support the observation contract and validity checks. They do not prove causal independence. Independence must come from the prototype's separate source, credentials, process, timestamps, and non-consensus projection, and must be tested as designed. | PASS |
| ADFA-LD | The [UNSW owner page](https://research.unsw.edu.au/projects/adfa-ids-datasets) identifies ADFA-LD as a Linux system-call HIDS evaluation dataset and grants academic, non-commercial use. | It remains an offline categorical syscall benchmark. The actual archive, empirical layout/count discrepancy, owner terms, and hashes must be pinned by the qualification story. Failure yields an honest blocked result, never substitute or synthetic records. | CONDITIONAL |
| LID-DS 2021 | The official repository identifies LID-DS and its 2021 loader/recording framework. Its GPL statement clearly covers the program; an independent raw recording-data redistribution grant was not established by the inspected owner material. | It may inform schema and real-capture method and may be evaluated only after version/layout/hash/license qualification. Raw redistribution remains blocked until license scope is resolved. The story's honest blocked/not-executed state is academically valid and does not block the other tracks. | CONDITIONAL |
| HAI 23.05 | HAI Technical Details v4.0, PDF p. 2, identifies HAI/HAIEnd 23.05 and its versioned training/test summary; p. 31 defines four training CSVs, two testing CSVs, and a label CSV. The [official HAI repository](https://github.com/icsdataset/hai) confirms the HIL-based ICS scope, 23.05 identity, files, and CC BY-SA 4.0 license. | It is external physical/SCADA benchmark evidence, not compressor evidence and not custom-fusion input. Actual Git commit/LFS objects, file hashes, and observed layout must still pass the version-specific qualification story before a formal result. | CONDITIONAL |
| LSTM/GRU and baselines | Primary LSTM and GRU papers establish the model families. Jozefowicz et al., PDF pp. 1 and 8, and the [PMLR paper page](https://proceedings.mlr.press/v37/jozefowicz15.html) show task-dependent results rather than a universal winner. | The sources justify candidacy, not superiority. Validation-only selection within each dataset/track, transparent baselines, frozen preprocessing/thresholds, and unfavorable-result retention are required. | PASS |
| Final dataset comparison | This is an explicit inference from the owner sources: ADFA-LD and LID-DS are syscall benchmarks, HAI is an ICS physical/SCADA dataset, and only PTFP-Custom-v1 contains synchronized physical and syscall evidence from the same runs. | A common global numeric ranking would be invalid. Separate dataset-native result tables plus a capability/limitation matrix are correct; only the synchronized custom campaign may support a quantitative physical-only/syscall-only/fusion paired ablation. | PASS |

Audit totals: **8 PASS, 3 CONDITIONAL, 3 BLOCKED**. The conditional
dataset findings are already handled by fail-closed qualification stories. The
three blocked findings prevent formal implementation authorization because they
affect the global parameter/mock gate and the custom dataset that supplies the
dissertation's final paired comparison.

### Required Evidence Corrections

1. Replace the 25% and 75% ledger `source_id` with immutable preregistration
   decision records. Link each record to the experiment controller, the bounded
   fusion research question, the custom physical/syscall track, and the exact
   paired-ablation output. Danfoss and DOE may support plausibility and limits;
   neither is the authority for the researcher's chosen endpoints.
2. Keep 8 mA and 16 mA `proposed` until an exact selected CDS 803 command-profile
   configuration establishes the 0%-100%/4-20 mA mapping. Record both the
   profile evidence and the arithmetic derivation.
3. Add an architecture-owned `MockAdmission` contract, or equivalent required
   fields in `ParameterEvidence`, for capability gap, failed authentic path,
   official authority and locator, transferability, exact component, bounded
   question, evidence track, affected final output, approval, and replacement
   condition.
4. Inventory every formal compressor/process mock behavior and number. Admit
   each with the complete contract or remove/disable it in formal v2 mode. No
   anonymous legacy simulator value may migrate.
5. Clarify that the Linux workload is a controlled experimental workload first;
   authentic kernel events are mandatory. Mocking any reproducible workload
   behavior for convenience is forbidden.

## Final Assessment

### Overall Readiness Status

**NOT READY**

The planning package has complete story coverage and strong scientific
boundaries, but implementation cannot start under one coherent, enforceable
normative contract. The blockers are upstream contract and evidence-record
defects, not missing stories or a request for more UI/UX.

### Blocking Issues

1. **PRD and architecture lag the approved academic-veracity guardrail.** FR76
   and NFR39 do not contain the complete authentic-reproduction, official-source,
   transferability, component/question/track/result-linkage rule. The
   architecture's `ParameterEvidence.v1` omits the fields and validation owner
   required by Stories 9.3, 9.4, and 17B.5.
2. **The only proposed experiment-bound values are not yet executable.** The
   25%/75% records conflate a researcher decision with a manufacturer source;
   8/16 mA lacks evidence for the exact selected linear CDS 803 command profile.
3. **The formal simulator has no admitted mocks.** The sources justify bounded
   testbed research and qualitative behavior, but the ledger contains no mock
   admission for the simulator behavior or numbers that would produce the
   synchronized custom dataset and final paired ablation.

### Non-Blocking but Required Follow-Up

- Consolidate the fragmented PRD so FR30-FR71 and NFR22-NFR37 do not depend on
  historical July normative prose.
- Preserve dataset-specific qualification gates: pin actual ADFA-LD, LID-DS
  2021, and HAI 23.05 artifacts, layouts, owner terms, and hashes before their
  corresponding formal runs. A qualified blocked LID result remains acceptable.
- If optional Epic 18 is activated, reconcile mandatory-versus-optional PRD
  wording, separate live-demo state from a selected frozen `G9_PASS` package,
  and prove server-side rejection of mutation routes. None of this blocks
  scientific Epics 9-17B after the three global blockers are corrected.
- Decompose Story 9.4 into narrow implementation tasks during create-story; do
  not split or expand its scientific acceptance boundary.

### Party Mode Gate

The story package remains approved: John **9/10**, Winston **8/10**, Bob
**9/10**, average **8.7/10**, no veto. It is focused, necessary, testable, and
does not require UI/UX for scientific completion.

Implementation readiness is not approved: John **5/10** (unresolved academic
authority), Winston **6/10** (contract mismatch), Bob **7/10** (testable stories
but an unimplementable authoritative schema), average **6.0/10**, with academic
and architecture vetoes. Under the agreed scoring rule, there is no automatic
approval.

### Recommended Next Steps

1. Run **Correct Course** over the three blockers.
2. Amend PRD FR76/NFR39 and the controlled-workload wording; amend architecture
   contracts and fail-closed validation ownership to match the approved stories.
3. Correct the parameter ledger and create the complete simulator mock-admission
   inventory without inventing any replacement values.
4. Re-run **Check Implementation Readiness**. Proceed to sprint planning only
   after a `READY` result.

### Assessment Metadata

- Assessment date: 2026-08-22
- Assessor: BMAD implementation-readiness workflow with Party Mode review
- Requirements coverage: 93/93 FRs, 100%
- Story structure: 81/81 complete; 505 BDD scenarios
- Scientific authorization: withheld pending the three blocking corrections
