---
stepsCompleted:
  - step-01-validate-prerequisites
  - step-02-design-epics
  - step-03-create-stories
  - step-04-final-validation
inputDocuments:
  - _bmad-output/planning-artifacts/prd.md
  - _bmad-output/planning-artifacts/prd-update-2026-05-21.md
  - _bmad-output/planning-artifacts/prd-update-2026-08-15.md
  - _bmad-output/planning-artifacts/architecture.md
  - _bmad-output/planning-artifacts/architecture-update-2026-05-21.md
  - _bmad-output/planning-artifacts/architecture-update-2026-08-15.md
  - _bmad-output/planning-artifacts/ux-design-specification.md
  - _bmad-output/planning-artifacts/epics.md
  - _bmad-output/planning-artifacts/epics-update-2026-05-21.md
  - _bmad-output/planning-artifacts/epics-update-2026-07-30.md
  - _bmad-output/planning-artifacts/epics-update-2026-08-15.md
  - _bmad-output/planning-artifacts/research/technical-scientifically-grounded-industrial-signal-and-anomaly-simulation-research-2026-08-15.md
  - _bmad-output/planning-artifacts/implementation-readiness-report-2026-08-15.md
---

# parallel-truth-fingerprint-prototype - Epic Breakdown

## Overview

This document provides the complete epic and story breakdown for
parallel-truth-fingerprint-prototype, decomposing the requirements from the
PRD, optional UX design, and architecture into implementable stories.

The August 2026 PRD and architecture overlays are controlling. Historical
identifiers remain visible for traceability, but an `AMENDED` or `SUPERSEDED`
item can be implemented only through its named August controllers. This
document is planning evidence and does not authorize implementation, dataset
acquisition, training, syscall capture, experiments, or activation.

## Requirements Inventory

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

FR76: Every executable v2 numeric parameter has a stable ID and exactly one of
`direct`, `derived`, `measured`, `preregistered_factor`, or `mock`. Its record
contains value, unit, class-specific authority, exact source/decision/
calibration/mock-admission locator, derivation and input IDs where applicable,
selected profile, experiment scope, approval identity, uncertainty/limitation,
authentic-reproduction feasibility, exact prototype component, bounded research
question, dataset/modality track, affected final-package element, and explicit
transferability rationale. Domain claims fail closed on missing, inapplicable,
or non-transferable official authority; preregistered factors use the frozen
decision as value authority; mocks additionally resolve an immutable approved
`MockAdmission.v1`. Anonymous legacy values run only in labelled
legacy-reproduction mode.

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
workload and captures the authentic kernel calls it actually emits through a
qualified Sysdig/eBPF or equivalent collector. Every workload behavior the
approved prototype can reproduce executes authentically. Only a specifically
unavailable behavior may use an approved `MockAdmission.v1`; convenience,
cost, timing, or an unfavorable result is insufficient. Syscalls are never
fabricated, renumbered, modified, or substituted.

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
results and is not an implementation-readiness gate. `legacy_demo` may show
live/current state only with persistent `DEMO - NOT PUBLISHED SCIENTIFIC
EVIDENCE` status. `frozen_evidence` reads one explicitly selected immutable
`G9_PASS` package, never a mutable `latest` identity, exposes no control route,
and rejects mutation requests server-side. Dashboard absence, styling, or
disagreement cannot block or alter scientific Epics 9-17B.

### NonFunctional Requirements

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

NFR39: Formal v2 startup, experiment freeze, and final evidence admission
reject every executable numeric parameter whose complete FR76 record or
class-specific authority cannot be resolved. `direct` uses applicable official
authority; `derived` uses validated inputs and deterministic dimensional
derivation; `measured` uses preserved calibration/pilot evidence;
`preregistered_factor` uses a pre-test frozen decision plus separately
documented feasibility constraints; and `mock` uses an approved capability-gap
admission plus official support for every asserted domain behavior and number.
No class is silently promoted into another.

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

### Additional Requirements

AR1: Preserve the brownfield local modular stack: Python domain/application
code, Go only at the ABCI boundary, MQTT, real OPC UA client/server boundary,
MinIO, CometBFT, Keras/Torch, and standard-library-first supporting code.

AR2: Keep scientific policy in pure domain/application boundaries and place
MQTT, OPC UA, MinIO, CometBFT, ML runtime, and syscall capture behind adapters;
the composition root and optional dashboard cannot own scientific decisions.

AR3: Maintain exactly two detector-facing transport families: versioned
physical observations/consensus/SCADA and separate host-syscall events. Syscalls
never enter physical consensus and truth is never published to a
detector-accessible topic.

AR4: Implement stable, versioned, canonically serialized contracts with strict
writers and semantic invariant tests for `ParameterEvidence.v1`,
`InstrumentProfile.v1`, `ExperimentSpec.v1`, `ScenarioTruth.v1`,
`SignalObservation.v2`, `ConsensusRoundInput.v2`, `ConsensusDecision.v2`,
`ScadaObservation.v2`, `SyscallEventBatch.v1`, `DetectorBundle.v1`,
`DetectorScore.v1`, `FusionDecision.v1`, `EvaluationResult.v1`, and
`ArtifactManifest.v1`.

AR5: Enforce the forbidden-field boundary of every contract: no truth or
labels in observations/scores, no syscalls in physical consensus, no
consensus-derived source in OPC evidence, no mutable fitting state in bundles,
and no analytics-to-control commands.

AR6: Preserve per-edge and aggregate physical records separately and maintain
experiment/run/round/edge/sensor/event identities, source/observed timestamps,
clock quality, exact profile hash, quality, and mutually consistent raw,
normalized, and engineering representations.

AR7: Preserve workload, host/VM, boot, container/cgroup, process/thread,
kernel/architecture, collector/filter, sequence/time, gaps/drops/duplicates,
capture mode, and raw segment URI/hash for custom syscalls; numeric IDs remain
categorical and ABI/kernel contextual.

AR8: Treat `DetectorBundle.v1` as atomic and content-addressed. Any change to
weights, preprocessing, features, vocabulary, calibration evidence, threshold,
or runtime creates a new bundle identity.

AR9: Use separate versioned topic ownership for physical observations,
physical consensus, physical SCADA, host syscalls, physical/syscall detector
scores, and fusion decisions, with source sequence, deduplication, gap evidence,
and bounded backpressure.

AR10: Use persistent MinIO storage with tested restoration and append-only,
role-separated namespaces for experiments, raw physical evidence, raw syscall
segments, consensus, SCADA, bundles, scores, fusion, restricted truth,
evaluation, and sources. Mutable aliases point to immutable objects but are not
scientific identity.

AR11: Preserve dataset-native boundaries: ADFA-LD and LID-DS are external
syscall benchmarks, HAI 23.05 is external native physical/SCADA evidence, and
only synchronized `PTFP-Custom-v1` is eligible for physical/syscall fusion.

AR12: Qualify custom syscall capture at the actual Linux kernel boundary. On
Docker Desktop this is the Linux VM/kernel, not Windows; if attribution,
ordering, loss, overhead, or replay qualification fails, formal capture moves
to an explicitly pinned Linux environment or remains blocked.

AR13: Run the OPC UA server as a separate pre-consensus boundary and read only
through a distinct real client session. Preserve the revision guard,
`DataValue` quality/timestamps, endpoint, namespace, NodeIds, attempts, latency,
freshness, security mode, and blocking reason.

AR14: Preserve v1 and v2 contracts through explicit routing and feature flags.
Never rewrite historical objects, load v1 bundles against v2 inputs, or use a
silent fallback when an enabled v2 source is absent or incompatible.

AR15: Make rollback select an explicit identity tuple covering profile,
parameter set, contract, collector/filter, dataset/split, bundle, fusion policy,
code, and runtime rather than a filename or latest timestamp.

AR16: Create no anonymous architectural default for noise, dynamics,
divergence, trust thresholds, tolerances, fault size, windows,
hyperparameters, anomaly thresholds, queues, capture loss, duration,
repetitions, or fusion weights. Missing provenance blocks formal v2 startup.

AR17: Preserve the ordered verification gates G1 provenance, G2 signal v2, G3
consensus parity, G4 independent SCADA, G5 physical bundle, G6 authentic
syscall capture, G7 external benchmarks, G8 synchronized custom evidence, and
G9 reproducible frozen-score/fusion result.

AR18: Fail closed on profile/schema/hash/bundle/version mismatch, Python/Go
parity failure, invalid OPC evidence, unknown external dataset layouts, truth
leakage, mixed configurations, post-unlock changes, or unverified evidence
storage.

AR19: Capture loss or attribution failure flags affected syscall segments and
follows the preregistered abort/exclusion policy; missing calls are never
silently interpreted as normal behavior.

AR20: Storage or analytics latency cannot block acquisition/control, and
dashboard disagreement can never override immutable artifacts or evaluator
output.

AR21: Reuse the existing stack and avoid new cloud services, production HMI,
frontend framework, broker, database, orchestration platform, or general-purpose
infrastructure unless a later approved change proves it indispensable.

AR22: Historical Epics 1-7 remain implemented baseline evidence. The May Epic
8 and July Epic 9-16 roadmaps are superseded planning history and are not
implementation dependencies.

AR23: Treat the updated readiness findings as decomposition constraints:
separate independently deliverable ADFA-LD and LID outcomes, model LID
acquisition/qualification and blocked state, split epic-sized source-ledger and
campaign work, own the Linux host-capture fallback decision, and keep candidate
comparison stories atomic.

AR24: No story or acceptance criterion may authorize implementation, dataset
download, training, syscall capture, experiment execution, feature activation,
or promotion merely because planning is complete.

### UX Design Requirements

All UX items are **OPTIONAL**, apply only if Epic 18 is separately activated,
and are excluded from implementation-readiness gates for scientific Epics
9-17.

UX-DR1: Reuse the existing locally served custom HTML/CSS/JavaScript dashboard;
do not require a frontend framework, build system, component library, visual
redesign, theme explorer, wireframe, or Figma artifact.

UX-DR2: Keep one compact desktop-first page that automatically reads current or
most recently published read models and identifies run identity and freshness;
no mobile application or production HMI behavior is required.

UX-DR3: Present raw mA, normalized span, engineering value/unit,
instrument-profile identity, quality, and freshness as linked representations
of one physical modality.

UX-DR4: Present physical, syscall, and fusion results as separate named
channels; fusion appears only when an immutable published result exists.

UX-DR5: Use explicit text states such as available, degraded, stale, missing,
blocked, invalid, aborted, and not published. Color or icons may support but
cannot replace the text meaning.

UX-DR6: Use simple native detail expanders for essential provenance,
identifiers, limitations, logs, or external artifact references without
recomputing or changing evidence.

UX-DR7: Provide no experiment-control forms or actions for scenario changes,
training, calibration, evaluation, fusion, promotion, relabelling, recovery, or
process control; read-only values are ordinary labelled text, not disabled
forms.

UX-DR8: Use the existing dark palette, system fonts, compact spacing,
responsive grid, and approximately 1100px stacking breakpoint only as optional
continuity guidance, not as acceptance criteria.

UX-DR9: Basic semantic headings, keyboard focus, readable contrast, text status
labels, and no distracting motion are optional best-effort improvements; no
formal WCAG target, certification, cross-browser matrix, or device lab is
required.

UX-DR10: The optional dashboard and every visual, responsive, accessibility,
component, or interaction recommendation remain non-blocking. Scientific
meaning and authority boundaries still govern any representation if the
dashboard is implemented.

### FR Coverage Map

FR1: Epic 10 - Preserve compressor physics while moving edge evidence to the
profile-owned current-domain boundary.

FR2: Epic 10 - Preserve one assigned sensor per edge through
`SignalObservation.v2`.

FR3: Epic 10 - Publish versioned physical observations through MQTT.

FR4: Epic 10 - Consume peer observations through the versioned physical path.

FR5: Epic 10 - Preserve independent non-trusted edge-local views.

FR6: Epic 11 - Execute current-domain CometBFT/ABCI consensus.

FR7: Epic 11 - Persist reconstructible trust ranking evidence.

FR8: Epic 11 - Exclude suspicious contributions under the declared basis.

FR9: Epic 11 - Identify round participants and correlation identities.

FR10: Epic 11 - Identify exclusions and evidence-based reasons.

FR11: Epic 11 - Expose complete round ranking and evidence references.

FR12: Epic 11 - Represent consensus failure explicitly and fail closed.

FR13: Epic 11 - Emit structured traceable consensus logs.

FR14: Epic 11 - Preserve the distinct consensus-failure state; Epic 18 may
optionally present it.

FR15: Epic 12 - Replace fake/projected SCADA with independent OPC UA evidence.

FR16: Epic 12 - Replace circular tolerance comparison with an eligible,
declared independent comparison.

FR17: Epic 12 - Produce explicit OPC integrity/comparison outcomes; Epic 18 may
optionally present them.

FR18: Epic 10 - Persist role-separated physical evidence; Epic 17A assembles
the synchronized custom evidence record.

FR19: Epic 13 - Replace the LSTM-only premise with fair physical candidates.

FR20: Epic 13 - Produce an immutable physical detector bundle.

FR21: Epic 13 - Produce frozen physical scores and decisions; Epic 17A handles
eligible paired fusion.

FR22: Epic 13 - Save and load the complete physical bundle without fitting.

FR23: Epic 13 - Evaluate replay/freeze and other preregistered conditions with
isolated truth.

FR24: Epics 15A, 15B, and 16 - Execute dataset-native external benchmark
tracks; Epic 17B reports them separately.

FR25: Epics 13, 14, 15A, 15B, 16, and 17A - Replace universal sample splitting
with group/run-before-window partitioning.

FR26: Epic 9 - Define complete immutable run identity; Epics 13-17B populate
the track-specific records.

FR27: Epics 13, 14, 15A, 15B, 16, 17A, and 17B - Replace one universal metric
set with protocol-appropriate outcomes.

FR28: Epic 9 - Define immutable role/version evidence history; Epics 13-17B
publish their records through it.

FR29: Epic 13 - Restrict runtime physical shadow inference to a compatible
custom bundle; Epic 17A permits only custom paired fusion.

FR30: Epic 9 - Freeze the complete v1 evidence baseline.

FR31: Epic 9 - Classify dataset and result provenance roles.

FR32: Epic 9 - Prevent fixtures/references from becoming measured results.

FR33: Epic 10 - Replace universal `ProcessSample` evidence with
`SignalObservation.v2` and profile-owned derivation.

FR34: Epic 10 - Define the versioned, provenance-bound `ExperimentSpec`.

FR35: Epic 10 - Support declared accelerated physical-only/test sessions;
Epic 17A admits only same-run authentic paired evidence.

FR36: Epic 10 - Generate and structurally isolate scenario truth.

FR37: Epic 10 - Define profile-owned context, units, and derived features.

FR38: Epic 10 - Define and preserve the preregistered experiment matrix; Epic
17A executes the formal paired campaign.

FR39: Epic 9 - Define group/run-before-window policy; Epics 10 and 13-17A
enforce it for their data.

FR40: Epic 9 - Define verified immutable publication and manifest-last rules;
Epics 10 and 17A apply them to custom evidence.

FR41: Epic 10 - Qualify physical experiment evidence; Epic 17A closes the
synchronized `DATASET_QUALIFIED` gate.

FR42: Epic 12 - Publish the pre-consensus plant/transmitter snapshot.

FR43: Epic 12 - Read OPC UA only through a distinct real client.

FR44: Epic 12 - Preserve OPC values, quality, timestamps, revision, and
correlation.

FR45: Epic 12 - Reject incomplete, stale, mixed, invalid, or unavailable OPC
evidence.

FR46: Epic 12 - Compare only eligible OPC evidence and persist diagnostics.

FR47: Epic 12 - Prove OPC/consensus causal source independence.

FR48: Epic 12 - Activate versioned OPC mode explicitly with no silent fallback.

FR49: Epic 13 - Separate physical training, validation, and calibration access.

FR50: Epic 13 - Freeze and bind the physical threshold before test.

FR51: Epic 13 - Reject stale or incompatible physical candidates.

FR52: Epic 13 - Report repeated scenario/regime-aware physical evaluation.

FR53: Epic 13 - Promote and roll back only explicit authorized physical
bundles.

FR54: Epic 13 - Serve inference-only physical shadow results without fitting.

FR55: Epic 16 - Replace HAI 20.07 acquisition with pinned HAI 23.05.

FR56: Epic 16 - Preserve HAI 23.05 native roles and chronology.

FR57: Epic 16 - Keep the HAI 23.05 detector and evaluation dataset-specific.

FR58: Epic 16 - Bound HAI claims to external native physical/SCADA evidence.

FR59: Epic 15B - Separate LID fixture, published-reference, and official-real
roles.

FR60: Epic 15B - Qualify the separately authorized official LID source/scope.

FR61: Epic 15B - Parse official LID layout with no fixture fallback.

FR62: Epic 15B - Split LID by official roles and complete groups.

FR63: Epic 15B - Execute only the later-authorized LID scope and report every
outcome or an explicit blocked state.

FR64: Epic 15B - Keep author-published metrics reference-only.

FR65: Epic 9 - Define the common provenance-rich evaluation envelope; Epic 17B
uses it for the final package.

FR66: Epic 17B - Produce separate result tables and the limitation matrix.

FR67: Epic 17B - Produce the immutable claim-to-evidence index.

FR68: Epic 18 (optional) - Present frozen custom detector evidence read-only.

FR69: Epic 18 (optional) - Present benchmark-native scope and limitations.

FR70: Epic 18 (optional) - Present distinct consensus, OPC, detector, and
fusion states without control authority.

FR71: Epic 18 (optional) - Present only authorized preregistered frozen anomaly
evidence without mutation.

FR72: Epic 9 - Establish the global two-modality semantic boundary; all later
epics enforce it and Epic 18 may present it.

FR73: Epic 10 - Define and preserve `SignalObservation.v2`.

FR74: Epic 10 - Separate process physics from profile-owned current derivation.

FR75: Epic 10 - Define `ExperimentSpec` and the 25%-75% preregistered reference.

FR76: Epic 9 - Establish the parameter provenance gate; later epics consume it.

FR77: Epic 10 - Establish isolated truth and controlled unlock.

FR78: Epic 13 - Compare physical custom candidates; Epic 16 applies the fair
candidate protocol to HAI.

FR79: Epic 14 - Run a controlled workload and capture authentic kernel calls.

FR80: Epic 14 - Define and preserve `SyscallEventBatch.v1`.

FR81: Epic 14 - Compare custom categorical syscall candidates; Epics 15A and
15B apply compatible candidate families to external syscall benchmarks.

FR82: Epic 15A - Preserve and evaluate ADFA-LD in its external syscall role.

FR83: Epic 15B - Preserve and evaluate the separately authorized LID-DS 2021
scope through its official schema.

FR84: Epic 16 - Preserve and evaluate HAI 23.05 in its native physical domain.

FR85: Epic 17A - Publish synchronized `PTFP-Custom-v1` from the physical and
authentic-syscall producers delivered by Epics 10 and 14.

FR86: Epic 9 - Define the leakage-safe lifecycle; Epics 13-17A enforce it for
their tracks and Epic 17B verifies it in the final evidence chain.

FR87: Epic 9 - Define immutable bundle/evidence identities; Epics 13-17A
produce exact bundles and scores.

FR88: Epic 9 - Define the evaluation envelope; Epics 13-17A generate
track-specific outcomes and Epic 17B reports them completely.

FR89: Epic 17A - Execute only preregistered custom same-run late fusion.

FR90: Epic 12 - Deliver independent fail-closed OPC UA evidence.

FR91: Epic 11 - Deliver deterministic current-domain consensus v2.

FR92: Epic 17B - Deliver the separate result tables, paired ablation,
limitation matrix, and claim evidence; Epic 18 may only project them.

FR93: Epic 18 (optional) - Present immutable evidence through the existing
read-only dashboard without becoming a readiness gate.

## Epic List

### Epic 9: Reproduce and Trust the Existing Prototype

The researcher can reconstruct the working v1 baseline, resolve every active
source and numeric parameter, distinguish measured evidence from mocks,
fixtures, and published references, and use stable manifests without changing
active v1 behavior.

**FRs covered:** FR26, FR28, FR30-FR32, FR39-FR40, FR65, FR72, FR76,
FR86-FR88.

**Dependencies:** Historical Epics 1-7 only. The superseded May Epic 8 is not a
dependency.

**Implementation notes:** Deliver the source/parameter ledgers, v1 golden
fixtures, versioned evidence/evaluation envelopes, immutable publication rules,
and gates needed by later epics. This epic does not execute a formal detector
campaign.

### Epic 10: Run Evidence-Grounded Physical Experiments

The researcher can declare controlled compressor experiments, execute physics
in engineering units, preserve primary raw-current evidence with quality and
profile-owned representations, isolate truth, and qualify physical experiment
artifacts.

**FRs covered:** FR1-FR5, FR18, FR33-FR41, FR73-FR77.

**Dependencies:** Epic 9.

**Implementation notes:** The simulator remains a controlled academic model,
not a real plant or validated digital twin. Accelerated physical-only evidence
does not become fusion evidence unless Epic 17A later pairs authentic syscalls
from the same runs.

### Epic 11: Validate Physical Evidence Through Current-Domain Consensus

The researcher can validate redundant physical observations through versioned
current-domain CometBFT/ABCI consensus and reconstruct deterministic identical
Python and Go decisions.

**FRs covered:** FR6-FR14, FR91.

**Dependencies:** Epics 9 and 10.

**Implementation notes:** Consensus consumes physical observations only,
declares its profile/comparison basis, preserves v1 compatibility, and remains
in shadow when Python/Go parity or versioned restart/query/state checks fail.

### Epic 12: Compare Against Independent OPC UA Evidence

The researcher can compare consensus against a genuinely independent,
pre-consensus OPC UA observation and obtain explicit quality, freshness,
correlation, availability, and causal-independence evidence.

**FRs covered:** FR15-FR17, FR42-FR48, FR90.

**Dependencies:** Epics 9-11.

**Implementation notes:** Use a separate server boundary and real
`asyncua.Client` over `opc.tcp`. Enabled v2 operation has no internal-object
read or consensus-projection fallback; invalid evidence fails closed.

### Epic 13: Train and Serve a Calibrated Physical Anomaly Detector

The researcher can compare LSTM-AE, GRU-AE, and declared baselines fairly,
calibrate without leakage, blindly evaluate controlled physical anomalies, and
serve an exact immutable physical bundle in inference-only shadow mode.

**FRs covered:** FR19-FR23, FR25, FR27, FR29, FR49-FR54, FR78, FR86-FR88.

**Dependencies:** Epics 9 and 10. It does not require Epics 11, 12, 14, 15A,
15B, or 16 to produce valid physical-detector evidence.

**Implementation notes:** The existing mixed-scale model is
`LEGACY_BASELINE`. Model family superiority, thresholds, windows, repetitions,
and targets are outcomes or evidenced/preregistered decisions, never premises.

### Epic 14: Capture and Detect Real Linux Edge Syscall Anomalies

The researcher can run an allowlisted controlled Linux edge workload, capture
the real kernel calls it actually emits, quantify attribution and capture
quality, and compare categorical normal-only syscall detectors.

**FRs covered:** FR25, FR27, FR79-FR81, FR85-FR88.

**Dependencies:** Epics 9 and 10.

**Implementation notes:** The workload may be mocked; syscalls may not be
fabricated. The epic owns a measured Docker Desktop Linux-VM capture decision
and an explicit pinned-Linux fallback or blocked outcome when the boundary
cannot qualify.

### Epic 15A: Reproduce ADFA-LD as an External Syscall Benchmark

The researcher can produce reproducible ADFA-LD anomaly results while
preserving official roles, trace identity, six attack families, categorical
semantics, archive/count evidence, and evaluation-only labels.

**FRs covered:** FR24-FR28, FR81-FR82, FR86-FR88.

**Dependencies:** Epic 9 only. It can proceed independently from Epic 14 and
Epic 15B.

**Implementation notes:** Dataset identifiers are never executed or treated as
continuous measurements, and timestamps are never fabricated. Results remain
external syscall benchmark evidence.

### Epic 15B: Qualify and Evaluate LID-DS 2021 Independently

The researcher can qualify a separately authorized official LID-DS 2021 scope,
preserve its official schema and grouping, execute reproducible categorical
anomaly evaluation, or publish an honest blocked/not-executed record when the
official source or scope cannot qualify.

**FRs covered:** FR24-FR28, FR59-FR64, FR81, FR83, FR86-FR88.

**Dependencies:** Epic 9 only. It neither depends on nor blocks Epic 15A.

**Implementation notes:** Acquisition/qualification precedes adapter and model
work. No scenario is a default requirement, fixtures never substitute for
official bytes, and author metrics stay reference-only.

### Epic 16: Evaluate HAI 23.05 in Its Native Physical Domain

The researcher can pin, qualify, process, train, calibrate, and evaluate HAI
23.05 while preserving native tags, units, chronology, official roles, labels,
and dataset-specific limitations.

**FRs covered:** FR24, FR26-FR28, FR55-FR58, FR78, FR84, FR86-FR88.

**Dependencies:** Epic 9 only. It can proceed independently from Epics 10-15B.

**Implementation notes:** HAI is external physical/SCADA evidence for a
different process. It is not converted wholesale to mA, merged with custom
rows, promoted as a compressor detector, or fused with ADFA/LID results.

### Epic 17A: Produce Synchronized Custom Evidence and Frozen Fusion Results

The researcher can produce immutable `PTFP-Custom-v1` runs containing aligned
physical observations and authentic edge syscalls, execute the preregistered
long-run campaign, freeze detector scores before truth unlock, and compare
physical-only, syscall-only, and simple late-fusion outcomes on the same runs.

**FRs covered:** FR18, FR21, FR25, FR27, FR29, FR35-FR41, FR49-FR54,
FR85-FR89.

**Dependencies:** Epics 9, 10, 13, and 14. Consensus/OPC evidence from Epics 11
and 12 is included where the preregistered custom protocol declares it.

**Implementation notes:** Split campaign setup, capture, long-run execution,
freeze, fusion, and paired ablation into independently verifiable work. Fusion
uses only compatible calibrated scores from aligned held-out custom windows.

### Epic 17B: Publish the Defensible Academic Evidence Package

The researcher can publish separate dataset/modality results, the paired
custom ablation, a capability/limitation matrix, and a reconstructible
claim-to-evidence index without selecting a global cross-domain champion or
inventing missing metrics.

**FRs covered:** FR24, FR26-FR28, FR65-FR67, FR88, FR92.

**Dependencies:** Epic 9; completed outputs from Epics 13, 14, 15A, 16, and
17A; and either a qualified measured Epic 15B result or its explicit
blocked/not-executed evidence record.

**Implementation notes:** A blocked LID outcome does not erase other valid
tracks. Every claim resolves to immutable source, split, bundle, threshold,
score, truth join, metric, uncertainty, status, and limitation evidence.

### Epic 18: Optionally Present Published Evidence in the Existing Dashboard

If separately activated, the researcher can demonstrate the already published
evidence through the existing lightweight local dashboard while keeping
physical representations, syscall evidence, detector channels, provenance,
freshness, and limitations understandable and read-only.

**FRs covered:** FR14, FR68-FR72, FR92-FR93.

**Dependencies:** Epic 17B. This epic is optional, terminal, presentation-only,
and excluded from scientific implementation-readiness gates.

**Implementation notes:** Reuse the current single-page HTML/CSS/JavaScript
surface. No redesign, frontend migration, mobile product, scientific controls,
or recalculation is required.

## Cross-Epic Mock Admission Guardrail

This guardrail applies to every story in Epics 9-18. A mock behavior, source, or
domain value is admissible only when an immutable capability-gap record proves
that the approved prototype boundary cannot directly reproduce the required
behavior or evidence. Convenience, cost reduction, an unfavorable authentic
result, or a desire to obtain an expected outcome is not sufficient.

Every admitted mock has a versioned admission record that identifies its exact
purpose and scope, the failed or unavailable direct-reproduction path, owner and
approval, replacement condition, and exact locator in applicable official
documentation supporting the represented behavior, constraints, and every
domain numeric value. Missing, non-official, or non-transferable documentation
blocks the mock. A mock remains labelled `mock` or `mock-derived`; it never
becomes measured, official-real, real-plant, or externally validated evidence.

Every admitted domain number or mock also proves material research relevance by
identifying the exact prototype component, bounded research question,
dataset/modality evidence track, and final result-table, paired-ablation,
capability/limitation-matrix, or claim-index element it can affect. The record
explains why the official source context is transferable to that exact use and
why authentic absence would prevent answering the bounded question. A value or
behavior that is merely illustrative, adjacent, convenient, or incapable of
changing a valid reported outcome is excluded. This relevance rule never
authorizes a common-metric cross-domain ranking: external datasets remain in
dataset-native tables, and only the synchronized custom campaign supports the
paired physical/syscall/fusion ablation.

Test fixtures using deliberately non-domain sentinel values are not scientific
mocks and remain test-only. If a fixture represents domain behavior or a domain
number, it must satisfy the same mock-admission rule. This guardrail can never
authorize fabricated syscalls, synthetic replacement of official dataset
records, consensus-projected OPC evidence, or mock substitution for any
authentic source that the prototype can reproduce directly.

The controlling contract identities are `DecisionRecord.v1` for researcher
value authority, `ParameterEvidence.v1` for each executable number, and
`MockAdmission.v1` for exceptional synthetic behavior. A source catalog entry
is evidence, not a decision, and cannot silently authorize a project-selected
factor.

## Epic 9: Reproduce and Trust the Existing Prototype

The researcher can reconstruct the working v1 baseline, resolve every active
source and numeric parameter, distinguish measured evidence from mocks,
fixtures, and published references, and use stable manifests without changing
active v1 behavior.

### Story 9.1: Freeze and Index the v1 Evidence Baseline

**FRs implemented:** FR30.

As a research owner,
I want an immutable and inspectable manifest of the complete v1 baseline,
So that later v2 work cannot rewrite history or misrepresent legacy evidence as
a final scientific result.

**Acceptance Criteria:**

**Given** the existing v1 repository, configuration, runtime, contracts, and
artifacts
**When** the baseline manifest is prepared
**Then** it identifies the code revision, dependency/runtime identity,
non-secret configuration, MQTT and consensus contracts, OPC/dashboard state
schemas, storage objects, datasets, models, and recorded experimental results
**And** every entry contains its role, version where available, locator, content
hash or explicit unverifiable status, and scientific-status label.

**Given** an expected baseline item is missing, mutable, corrupt, or cannot be
hashed
**When** the manifest is validated
**Then** the item is recorded with an explicit `missing`, `mutable`, `corrupt`,
or `unverifiable` status and limitation
**And** no value, identity, artifact, or successful result is inferred or
fabricated.

**Given** configuration contains credentials, private keys, tokens, or other
secret material
**When** configuration identity is recorded
**Then** the manifest records only safe field names, redacted values, or an
approved non-secret digest
**And** no secret content enters Git, the manifest, logs, or reports.

**Given** the referenced baseline entries have been inventoried
**When** the baseline is finalized
**Then** referenced immutable objects are verified before the complete manifest
is atomically published
**And** an existing finalized baseline cannot be overwritten or silently
repointed through a mutable `latest` identity.

**Given** existing v1 behavior includes implemented and exploratory outcomes
**When** scientific status is assigned
**Then** implemented runtime evidence, fixtures, published references, measured
results, and the experimental fingerprint baseline remain distinguishable
**And** the legacy detector is labelled as historical or `LEGACY_BASELINE`,
never as the final physical detector or a dataset.

**Given** v2 planning or later implementation consumes the baseline
**When** compatibility or regression evidence is evaluated
**Then** it resolves to the frozen v1 fixtures and manifest identities
**And** creating the baseline neither changes active v1 behavior nor authorizes
v2 implementation, activation, training, capture, or experimentation.

### Story 9.2: Establish the Semantic and Evidence-Role Vocabulary

**FRs implemented:** FR31, FR32, FR65, FR72.

As a research owner,
I want one versioned vocabulary for modalities, representations, models,
evidence roles, result roles, and scientific status,
So that contracts and reports cannot make incompatible or overstated claims.

**Acceptance Criteria:**

**Given** the controlling August requirements
**When** the semantic vocabulary is defined
**Then** the only detection modalities are `physical_instrumentation` and
`linux_host_syscall`
**And** 4-20 mA is classified as a physical representation while LSTM, GRU,
autoencoders, and baselines are classified as model families.

**Given** a dataset, run, artifact, or reported result
**When** its evidence identity is created
**Then** it uses an explicit source/evidence role and result role, including the
applicable distinctions among custom-generated evidence, official-real data,
test fixtures, published references, and locally measured results
**And** those general roles cannot erase dataset-native scope, official file
roles, modality, subset, or scientific limitations.

**Given** an artifact is labelled as a fixture or published reference
**When** a writer attempts to assign a locally measured result role
**Then** validation rejects the incompatible role combination
**And** no metric or artifact is silently copied into a measured-result
namespace.

**Given** a writer or report attempts to describe HAI as compressor data,
ADFA-LD or LID-DS as physical evidence, a controlled custom run as real-plant
evidence, an autoencoder as a dataset, or an external model as a compressor
detector
**When** semantic validation runs
**Then** the artifact or report record is rejected with a specific violated
rule
**And** the rejected record is not published as complete evidence.

**Given** historical v1 records use legacy or incomplete terminology
**When** they are indexed through the frozen baseline
**Then** their original bytes and labels remain unchanged
**And** any current interpretation is stored as a separate mapping with a
version, provenance, limitation, and `legacy` scientific status.

**Given** a contract, evaluator, report, or optional dashboard consumes semantic
identities
**When** it encounters an unknown, missing, or incompatible vocabulary version
**Then** it fails explicitly or presents the value as unsupported
**And** it never guesses a modality, evidence role, result role, or scientific
status.

**Given** the semantic validator test suite
**When** valid and invalid combinations are exercised
**Then** it covers both modalities, linked physical representations, model
families, dataset-native roles, fixture/reference/measured distinctions, and
the prohibited cross-domain claims
**And** passing these tests does not authorize implementation activity,
training, capture, experimentation, or feature activation.

### Story 9.3: Build the Authoritative Source-Evidence Catalog

**FRs implemented:** FR31, FR32, FR76.

As a research owner,
I want a versioned catalog of every scientific, technical, dataset, profile, and
protocol source,
So that each adopted claim or parameter can be traced to an exact authoritative
location and scope.

**Acceptance Criteria:**

**Given** an existing or proposed project source
**When** a source record is created
**Then** it receives a stable source ID and records its organization or authors,
title, publication or release date, exact version/edition, source type, official
URL or repository, retrieval status, and local locator where applicable
**And** the record identifies whether the source is primary, authoritative,
peer-reviewed, vendor documentation, a standard, a dataset source, or a
secondary reference.

**Given** source bytes are available locally
**When** they are registered
**Then** the record contains the exact filename, byte size, SHA-256 digest,
retrieval date, and storage or archive locator
**And** a content change creates a new immutable source identity rather than
silently changing the existing record.

**Given** a source is paywalled, access-controlled, not yet acquired, or
available only through an official landing page
**When** it is catalogued
**Then** its status and access limitation are explicit
**And** the system does not fabricate local bytes, file sizes, hashes, license
rights, or a completed acquisition state.

**Given** a project claim, profile fact, protocol rule, or externally sourced
number
**When** it references the catalog
**Then** it identifies the source ID and an exact page, section, table, figure,
field, commit, file, or other stable locator
**And** the source record states the applicable claim scope and does not imply
that unrelated values in the same document are transferable.

**Given** an externally asserted domain number cannot be measured or derived by
the approved prototype
**When** its source and intended use are validated
**Then** the number resolves to applicable official documentation from the
responsible standards body, manufacturer, protocol owner, or dataset owner and
records the exact prototype component, bounded research question, evidence
track, and final package element it affects
**And** a scholarly or secondary reference may provide context but cannot be
promoted into official direct-parameter evidence or substitute for missing
transferability.

**Given** a dataset or vendor source has license, citation, notice, access, or
redistribution restrictions
**When** the source record is validated
**Then** those restrictions and the permitted project use are preserved
**And** restricted or large source data remains outside Git while its catalog
metadata and checksums remain versionable.

**Given** two records refer to mirrors, aliases, or copies of the same source
**When** catalog normalization runs
**Then** the canonical source and each retrieval location remain identifiable
without merging different versions or byte streams
**And** conflicting versions, counts, or hashes are preserved as an explicit
discrepancy rather than automatically resolved.

**Given** the source catalog is serialized or exported
**When** the same validated records are processed repeatedly
**Then** ordering and canonical representation are deterministic
**And** malformed records, duplicate stable IDs, missing required locators, or
invalid digests fail validation with actionable diagnostics.

**Given** the catalog identifies a source as suitable for future use
**When** the catalog is finalized
**Then** it records evidence and limitations only
**And** catalog inclusion does not authorize downloading datasets,
implementation, training, capture, experiments, or feature activation.

### Story 9.4: Build the Parameter-Evidence Catalog and Validation Gate

**FRs implemented:** FR76.

As a research owner,
I want every executable v2 numeric parameter to have a complete and validated
evidence record,
So that experiments cannot silently inherit unsupported constants or universal
assumptions.

**Acceptance Criteria:**

**Given** an executable v2 numeric parameter
**When** its parameter-evidence record is created
**Then** it has a stable parameter ID and exactly one classification among
`direct`, `derived`, `measured`, `preregistered_factor`, or `mock`
**And** it records value, unit, class-specific authority, exact source,
decision, calibration, or mock-admission locator, derivation and input IDs,
applicable profile, experiment scope, approval identity, authentic-reproduction
feasibility, exact prototype component, bounded research question,
dataset/modality evidence track, affected final package element, explicit
transferability rationale, and any relevant uncertainty or limitation.

**Given** a preregistered factor also cites manufacturer or standards evidence
**When** authority resolution runs
**Then** `DecisionRecord.v1` remains the value authority while official sources
establish only applicable configurability, feasibility, or constraints
**And** a source catalog record can never be treated as proof that the
manufacturer selected the researcher's factor.

**Given** a parameter is classified as `direct`
**When** the record is validated
**Then** an externally asserted domain value that the prototype cannot measure
or derive resolves to applicable official documentation and an exact locator
whose scope applies to the selected instrument, protocol, dataset, component,
and research question
**And** citing a document does not make unrelated values in that document
transferable.

**Given** a parameter is classified as `derived`
**When** the record is validated
**Then** it contains a deterministic formula, version, referenced input
parameter IDs, units, and derivation output
**And** missing inputs, circular derivations, dimensional inconsistency, or a
non-reproducible result causes validation failure.

**Given** a parameter is classified as `measured`
**When** the record is validated
**Then** it resolves to a preserved pilot or calibration artifact with method,
environment, sample/run identity, timestamp, result, and uncertainty or observed
dispersion
**And** the measurement remains scoped to the environment and profile in which
it was obtained.

**Given** a parameter is classified as `preregistered_factor`
**When** the record is validated
**Then** it resolves to a frozen decision record created before the applicable
test or truth unlock and states its rationale, scope, owner, and authorization
status
**And** the 25%-75% request is represented only as
`speed_reference_pct` or `capacity_reference_pct`, never as power or as a
universal operating range.

**Given** a parameter is classified as `mock`
**When** the record is validated
**Then** it resolves to an approved immutable mock-admission record proving that
the prototype cannot directly reproduce the required behavior or evidence and
identifying the declared simulator or workload profile, limited purpose, exact
evidence track, and affected final comparison-package element
**And** applicable official documentation with an exact locator supports the
represented behavior, constraints, and every domain numeric value.

**Given** the prototype can directly reproduce the required behavior or
evidence, official documentation is absent or inapplicable, or the authentic
result is merely unfavorable
**When** mock admission or parameter validation is requested
**Then** validation fails closed with the capability-gap or source reason
**And** the mock cannot replace the authentic path, become a fallback value, or
be represented as sourced plant behavior, measured evidence, official-real
data, or an externally validated value.

**Given** an anonymous legacy constant is needed for reproduction
**When** it is registered
**Then** it is quarantined under an explicit legacy-reproduction identity and
limitation
**And** it cannot pass the formal v2 parameter gate or be silently copied into a
current profile.

**Given** a parameter record is missing, has multiple classifications, conflicts
with another active value, lacks applicable scope, or references an unresolved
source or decision
**When** formal v2 validation runs
**Then** validation fails closed with the parameter ID and specific reason
**And** no fallback value or architecture default is supplied.

**Given** valid parameter records are serialized repeatedly
**When** canonicalization and validation run
**Then** they produce deterministic ordering, representation, and content hashes
**And** validation covers noise, dynamics, tolerances, thresholds, windows,
queues, capture loss, duration, repetitions, and fusion settings without
inventing defaults.

**Given** all parameter records for an experiment validate
**When** the gate reports success
**Then** the result proves only that the declared numbers are accountable
**And** it does not authorize implementation, dataset acquisition, training,
capture, experiment execution, promotion, or activation.

### Story 9.5: Preserve v1 Contracts as Golden Versioned Fixtures

**FRs implemented:** FR28, FR30, FR32, FR86.

As a prototype maintainer,
I want the existing v1 contracts preserved as explicit golden fixtures,
So that v2 capabilities can be introduced without rewriting history or breaking
reproducibility.

**Acceptance Criteria:**

**Given** the verified v1 baseline
**When** the golden fixture set is assembled
**Then** it includes representative MQTT topics and observation payloads,
consensus transactions, states, queries and decisions, MinIO object keys and
contents, manifests, and legacy detector inputs and outputs
**And** existing dashboard read models may be included only as optional
compatibility fixtures.

**Given** a golden fixture
**When** it is registered
**Then** it records a stable contract ID, explicit `v1` version, evidence
provenance, expected validity, serialization form, and content hash
**And** it distinguishes contracts requiring byte identity from those allowing a
declared semantic comparison.

**Given** a test fixture contains a value intended only to exercise a contract
boundary
**When** fixture provenance is validated
**Then** a deliberately non-domain sentinel remains explicitly test-only
**And** any fixture that represents domain behavior or a domain numeric value
must resolve to the cross-epic mock-admission record and applicable official
documentation.

**Given** preserved historical v1 bytes
**When** compatibility support is added
**Then** the original bytes and object identities remain unchanged
**And** any adapted representation is emitted separately with its own version,
provenance, and hash.

**Given** v2 capabilities are disabled
**When** a preserved v1 artifact is replayed
**Then** explicit version routing selects the v1 reader and reproduces the
declared v1 behavior
**And** no v2 field, assumption, normalization, or default is silently injected.

**Given** an artifact has a missing, unknown, or unsupported contract version
**When** it enters a versioned reader
**Then** processing fails closed with the artifact identity and reason
**And** the artifact is not implicitly interpreted as either v1 or v2.

**Given** a v1 model or detector is presented with v2-only features
**When** compatibility is evaluated
**Then** the combination is rejected explicitly
**And** no field dropping, reshaping, normalization, or conversion occurs without
a separately versioned adapter contract.

**Given** the golden regression suite is evaluated repeatedly
**When** current behavior is compared with the fixtures
**Then** it verifies the declared byte-level or semantic expectations
deterministically
**And** any drift identifies the affected contract, fixture, expected result,
and observed result.

**Given** an optional dashboard compatibility fixture is absent or unsupported
**When** the core v1 regression suite is evaluated
**Then** the core evidence and detector contracts can still pass
**And** no UI or UX artifact becomes an implementation or readiness prerequisite.

**Given** the v1 fixture set passes validation
**When** its result is published
**Then** it demonstrates only preservation of the declared historical contracts
**And** it does not activate v2 behavior or authorize acquisition, training,
capture, experiments, deployment, or migration.

### Story 9.6: Define Immutable Artifact and Evaluation Manifests

**FRs implemented:** FR26, FR28, FR40, FR65, FR87, FR88.

As a research owner,
I want versioned manifests for artifacts, runs, bundles, and evaluation results,
So that every result can be reconstructed from exact immutable identities
without relying on hidden state or mutable aliases.

**Acceptance Criteria:**

**Given** an artifact enters the formal evidence chain
**When** its `ArtifactManifest.v1` record is created
**Then** it records a stable identity, evidence role, scientific status,
contract version, media type, byte size, content hash, immutable locator,
producer identity, creation timestamp, and provenance dependencies
**And** changing its content or identity-bearing metadata creates a new artifact
identity.

**Given** a formal run is identified
**When** its immutable run identity is assembled
**Then** it binds the experiment specification, profile, parameter set,
contracts, code revision, dependencies, runtime, collector or filter, dataset
and split, applicable mock-admission records, and applicable bundle or
fusion-policy identities
**And** unavailable or inapplicable components are explicit rather than
inferred.

**Given** an evaluated detector or fusion result
**When** its `EvaluationResult.v1` envelope is created
**Then** it identifies modality, track, dataset-native scope, runs, partitions,
bundle, preprocessing, calibration, frozen threshold, truth-unlock record,
evaluation code, metrics, uncertainty, status, and limitations
**And** it permits protocol-specific metrics without forcing one universal
metric set across incompatible tracks.

**Given** one manifest depends on other artifacts
**When** the provenance graph is validated
**Then** every dependency resolves to an immutable identity with the expected
role, version, and hash
**And** missing dependencies, cycles, hash mismatches, incompatible roles, or
mixed configurations fail closed.

**Given** a mutable alias such as `latest` exists for convenience
**When** it is referenced by a formal run or evaluation
**Then** the alias is resolved and recorded as an exact immutable identity
before use
**And** the mutable alias itself is never accepted as scientific identity.

**Given** artifacts for a result have been produced
**When** publication is requested
**Then** every referenced immutable object is verified before the complete
manifest or pointer is atomically published last
**And** an interrupted or partial publication cannot appear as a complete
result.

**Given** truth, labels, credentials, or other restricted material exists
**When** manifests are serialized
**Then** detector-facing manifests contain no truth, attack label, future
information, or secret value
**And** restricted evidence is represented only through authorized,
role-separated references needed by the evaluator.

**Given** the same valid manifest inputs are processed repeatedly
**When** canonical serialization runs
**Then** ordering, representation, identity, and content hashes are
deterministic
**And** the complete provenance chain can be inspected without a dashboard or
hidden database state.

**Given** a manifest or evaluation envelope passes validation
**When** its validation result is reported
**Then** the result establishes only structural integrity and provenance
completeness
**And** it does not authorize acquisition, fitting, training, capture,
evaluation execution, publication of scientific claims, deployment, or
activation.

### Story 9.7: Qualify Minimal Persistent Evidence Storage

**FRs implemented:** FR40.

As a research owner,
I want the prototype's formal evidence preserved in minimally qualified
persistent storage,
So that results remain reproducible without introducing production-grade
infrastructure.

**Acceptance Criteria:**

**Given** the existing MinIO storage configuration
**When** its academic-prototype qualification is performed
**Then** a declared test object remains available with identical bytes after a
service restart
**And** high availability, replication, multi-backend support, and production
disaster recovery are outside scope.

**Given** a formal evidence object is stored
**When** the write completes
**Then** its immutable key, byte size, and content hash are verified
**And** different content cannot silently overwrite or reuse that identity.

**Given** evidence has an assigned role
**When** its storage key is created
**Then** it uses the declared role-separated prefix
**And** detector-facing evidence remains structurally separate from restricted
truth and evaluation-only labels.

**Given** a small declared evidence fixture and its manifest
**When** the restoration smoke test is performed
**Then** the referenced object is restored and matches its original key, size,
and hash
**And** missing, corrupt, or mismatched evidence fails qualification explicitly.

**Given** storage is unavailable, incomplete, or unverified
**When** formal publication is attempted
**Then** no complete manifest is published and the blocking reason is recorded
**And** passing this story authorizes no capture, training, experiment,
deployment, control action, or dashboard work.

### Story 9.8: Define Partition, Freeze, and Activity-Authorization Records

**FRs implemented:** FR39, FR86.

As a research owner,
I want small immutable records for data partitioning, scientific freezes, and
authorized activities,
So that later experiments avoid leakage and remain within their explicitly
approved scope.

**Acceptance Criteria:**

**Given** a dataset or collection of experiment runs
**When** its partition record is frozen
**Then** it binds the source identity, grouping key, applicable train,
validation, calibration, and test membership, partition method, and any declared
random seed
**And** complete groups or runs are assigned before window or sequence
generation and cannot cross partitions.

**Given** a track is ready for fitting, calibration, testing, or fusion
**When** its scientific freeze record is created
**Then** it references the exact applicable partition, profile, parameter set,
preprocessing, features, candidate configuration, calibration method, threshold
policy, and fusion policy
**And** any identity-bearing change creates a new freeze record rather than
modifying the existing one.

**Given** test truth is structurally restricted
**When** model scores or decisions are produced
**Then** truth remains unavailable to detector-facing processing until the
applicable scores, decisions, and freeze identities are immutable
**And** post-unlock configuration changes invalidate the affected evaluation
rather than silently updating it.

**Given** a later activity requires explicit approval, including acquisition,
capture, training, calibration, evaluation, fusion, promotion, or activation
**When** its activity-authorization record is created
**Then** it identifies the permitted action, scope, input identities, decision,
owner, and timestamp
**And** a missing, rejected, or scope-mismatched record blocks only that activity
with an explicit reason.

**Given** these records and validators are implemented
**When** they are inspected
**Then** they remain flat, versioned, deterministic artifacts without requiring
a workflow engine, authorization service, scheduler, or dashboard
**And** this story performs no acquisition, capture, training, calibration,
evaluation, fusion, deployment, or activation.

## Epic 10: Run Evidence-Grounded Physical Experiments

The researcher can declare controlled compressor experiments, execute physics
in engineering units, preserve primary raw-current evidence with quality and
profile-owned representations, isolate truth, and qualify physical experiment
artifacts.

### Story 10.1: Define Evidence-Backed Instrument Profiles

**FRs implemented:** FR37, FR74, FR76.

As a research engineer,
I want versioned instrument profiles for temperature, pressure, and RPM,
So that current conversion and quality interpretation are explicit and
auditable.

**Acceptance Criteria:**

**Given** a proposed `InstrumentProfile.v1`
**When** it is registered
**Then** it records a stable profile ID, version, device or model, measured
variable, electrical endpoints, engineering endpoints and unit, conversion
direction, quality policy, source IDs and exact locators, approved scope, and
content hash
**And** every executable numeric field resolves to the parameter-evidence
catalog.

**Given** the initial formal temperature, pressure, RPM, and command profile
candidates
**When** their source bindings are checked
**Then** temperature resolves to Siemens TH320 option D73 at archived PDF p. 4,
pressure resolves to the exact Siemens P200 0-10 bar/4-20 mA variant only after
the pending official bytes are archived, RPM output resolves to the FB420
4-20 mA source, and command mapping resolves to Danfoss
AU356039245821 en-000201 printed p. 54, Tables 60-63
**And** unresolved pressure-source bytes or user minimum/maximum RPM endpoints
block only the dependent profile without inheriting 1.8-8.5 bar or
1200-4200 rpm from legacy mode.

**Given** a complete linear current profile
**When** its forward and inverse conversions are evaluated
**Then** process values convert to current and raw current converts to normalized
span and engineering value through the profile's single declared derivation
**And** any round-trip tolerance has its own admissible parameter-evidence
record.

**Given** an RPM observation is required
**When** its profile is selected
**Then** RPM remains represented through the cited 4-20 mA shaft-speed
transmitter profile
**And** it is not silently replaced by a generic voltage profile or treated as
a separate modality.

**Given** current is under-range, over-range, missing, or indicates a declared
instrument fault
**When** the profile applies its quality policy
**Then** quality is determined before any optional clipping or imputation
**And** the raw current and diagnostics remain preserved.

**Given** a profile is incomplete, has unresolved sources or parameters, uses
incompatible units, or falls outside its approved scope
**When** v2 validation is requested
**Then** validation fails with the profile identity and specific reason
**And** no anonymous default or legacy conversion is substituted.

**Given** valid profiles and their test fixtures
**When** validation and canonical serialization are repeated
**Then** conversions, quality outcomes, representation, and hashes are
deterministic
**And** defining the profiles does not authorize experiment execution or
activation.

### Story 10.2: Define and Validate `SignalObservation.v2`

**FRs implemented:** FR1-FR5, FR33, FR72-FR74.

As an edge evidence consumer,
I want one canonical physical observation contract,
So that raw current, quality, derived representations, identity, and time cannot
drift across services.

**Acceptance Criteria:**

**Given** a physical edge observation
**When** `SignalObservation.v2` is created
**Then** it records schema version, experiment, run, round, edge, sensor and
event identities, source sequence and correlation identity, source and observed
timestamps, clock quality, exact profile ID and hash, parameter-evidence
references, raw current in mA, current quality and diagnostics, normalized span,
derived engineering value, and engineering unit
**And** raw current remains the primary edge evidence.

**Given** a valid observation and matching instrument profile
**When** representation invariants are validated
**Then** normalized span and engineering value equal the single profile-owned
derivation from the preserved raw current
**And** downstream writers cannot supply an alternative conversion for the same
observation.

**Given** an observation is under-range, over-range, missing, uncertain, or
faulted under its profile policy
**When** it is validated
**Then** quality and diagnostics are evaluated before any optional clipping or
imputation
**And** the original current and pre-processing quality remain unchanged.

**Given** identity, sequence, timestamp, unit, profile, parameter, or
representation fields are missing or inconsistent
**When** contract validation runs
**Then** the observation fails closed with actionable field diagnostics
**And** it is not silently coerced to v1 or completed with defaults.

**Given** detector-facing or consensus-facing observation serialization
**When** forbidden-field validation runs
**Then** scenario truth, attack labels, future intervals, syscalls, detector
scores, fusion decisions, and actuator commands are rejected
**And** opaque correlation identities remain permitted.

**Given** per-edge observations and an aggregate physical record exist
**When** they are serialized or stored
**Then** their roles and identities remain distinct and traceable
**And** an aggregate never overwrites or masquerades as a primary per-edge
observation.

**Given** the same valid observation is serialized repeatedly
**When** canonicalization runs
**Then** representation, ordering, and content hash are deterministic
**And** the contract can be inspected without a dashboard.

### Story 10.3: Separate Process Physics From Transmitter and Edge Evidence

**FRs implemented:** FR1, FR33, FR35, FR37, FR74.

As a simulator maintainer,
I want process physics separated from transmitter conversion and edge evidence,
So that engineering behavior is not confused with what the instrumented edge
actually observes.

**Acceptance Criteria:**

**Given** the controlled compressor simulator
**When** it updates temperature, pressure, RPM, and related process state
**Then** the process model calculates in declared engineering units
**And** its outputs are labelled as a research mock rather than real-plant data
or a validated digital twin.

**Given** the controlled compressor model requires mocked behavior or a mocked
domain value
**When** its experiment profile is validated
**Then** an approved mock-admission record proves that the prototype cannot
directly reproduce that behavior and cites applicable official documentation
and exact locators for the behavior, constraints, and every numeric value
**And** a reproducible authentic path, missing documentation, or an unfavorable
authentic result prevents mock substitution.

**Given** a process value and an approved instrument profile
**When** the transmitter boundary emits evidence
**Then** only the selected profile converts the engineering value into raw
current and its derived representations
**And** the receiving edge treats raw current, profile identity, and quality as
its primary evidence.

**Given** configured physical edges
**When** observations are produced and consumed
**Then** each edge retains its assigned physical sensor identity and its own
non-trusted local replicated view
**And** shared mutable state cannot collapse the independence of edge views.

**Given** an edge publishes or consumes a physical observation through MQTT
**When** the v2 route is active
**Then** the declared physical-observation topic carries validated
`SignalObservation.v2` with source sequence and correlation evidence
**And** peer observations cannot bypass schema, profile, quality, provenance, or
version validation.

**Given** identical plant state, profile, parameters, and input trace
**When** batch and live transmitter paths are compared
**Then** they produce equivalent canonical representations within an evidenced
or preregistered tolerance
**And** the comparison never derives a second independent conversion path.

**Given** the profile, parameter set, version, or conversion result is missing
or incompatible
**When** v2 emission is attempted
**Then** that emission fails explicitly without a v1 or anonymous fallback
**And** existing v1 routing remains unchanged when v2 is disabled.

**Given** storage, MQTT, analytics, detector, or optional dashboard behavior
**When** any of those components fail
**Then** they cannot generate or change a compressor command
**And** only the experiment-control boundary retains command authority.

### Story 10.4: Define `ExperimentSpec.v1` and the Preregistered Matrix

**FRs implemented:** FR34, FR35, FR38, FR75, FR76.

As a research owner,
I want a versioned experiment specification and deterministic scenario matrix,
So that physical runs are declared before evidence collection without hidden
schedules or numeric choices.

**Acceptance Criteria:**

**Given** a proposed `ExperimentSpec.v1`
**When** it is registered
**Then** it records stable experiment and run identities, version and hash,
profile, parameter-set, and applicable mock-admission hashes, seed or input-trace
identity, phases, schedule, scenarios, interventions, recovery, expected
streams, applicable partition, metrics, stopping and abort policy,
truth-unlock rule, and evidence references
**And** unavailable or inapplicable fields are explicit rather than inferred.

**Given** an executable numeric field in the specification
**When** validation runs
**Then** it resolves to one applicable parameter-evidence ID with matching unit
and scope
**And** an unresolved duration, rate, noise, dynamic, tolerance, intervention,
repetition, or limit blocks validation instead of receiving a default.

**Given** the requested 25%-75% variation
**When** it is declared in the specification
**Then** it is named `speed_reference_pct` or `capacity_reference_pct` and
classified as `preregistered_factor`
**And** it is never labelled as electrical power or presented as a universal
compressor operating range.

**Given** the separately approved
`instrument-profile-cds803-terminal53-linear-0-100-v1` command profile
**When** the 25%-75% reference is represented as current
**Then** Danfoss AU356039245821 en-000201 printed p. 54, Tables 60-63 binds
6-12=4 mA and 6-13=20 mA, while
`decision-custom-reference-window-v1` binds the selected 6-14=0 and 6-15=100
reference configuration and authorizes 25 and 75 as preregistered factors
**And** 8 mA and 16 mA resolve through deterministic derivations over those
frozen inputs rather than through a manufacturer recommendation
**And** ramp, dwell, settling, ordering, repetitions, and safety limits remain
separate evidenced or preregistered parameters.

**Given** the declared scenarios and operating regimes
**When** the experiment matrix is generated
**Then** it deterministically enumerates the approved normal, intervention, and
recovery runs and their expected evidence streams
**And** it preserves valid, invalid, aborted, unfavorable, and recovery outcomes
rather than defining only successful cases.

**Given** an accelerated or physical-only session is declared
**When** its scope is validated
**Then** it is labelled as controlled custom physical or test evidence
**And** it is not marked as real-plant evidence or fusion-eligible synchronized
evidence.

**Given** a specification and matrix are frozen
**When** execution is later requested
**Then** their immutable identities must match an applicable approved
activity-authorization record
**And** changing either artifact creates a new identity and requires a new
authorization rather than mutating the frozen plan.

### Story 10.5: Isolate `ScenarioTruth.v1` and Control Truth Unlock

**FRs implemented:** FR36, FR77.

As an evaluator,
I want scenario truth stored separately and unlocked only after evidence is
frozen,
So that physical evidence can be produced and scored without label leakage.

**Acceptance Criteria:**

**Given** a declared experiment scenario
**When** its `ScenarioTruth.v1` record is created
**Then** it records schema version, experiment and run identities, opaque
correlation identity, condition or intervention intervals, truth provenance,
writer identity, and content hash
**And** the record is append-only in the restricted truth namespace.

**Given** observation, MQTT, consensus, feature, detector-input, bundle, score,
or detector-visible report contracts
**When** their forbidden-field validation runs
**Then** truth, attack labels, scenario names, intervention meaning, future
intervals, and expected outcomes are rejected
**And** no label-derived field or filename is accepted as an indirect detector
input.

**Given** producers and detector-facing consumers need to correlate evidence
from one run
**When** they exchange records
**Then** they use opaque experiment, run, event, and correlation identities
**And** those identities reveal no scenario or expected-result semantics.

**Given** truth remains locked
**When** a non-evaluator identity or premature evaluation attempts access
**Then** access fails explicitly and the attempt is recorded
**And** detector-facing artifacts remain usable without truth access.

**Given** the applicable observations, partitions, decisions, and other declared
evidence are immutable
**When** an authorized evaluator unlocks truth
**Then** the unlock record binds their exact hashes, the truth identity,
evaluator identity, and timestamp
**And** the join creates a separate evaluation artifact without modifying truth
or detector-facing evidence.

**Given** any detector-facing artifact contains truth or a post-unlock
identity-bearing artifact changes
**When** integrity validation runs
**Then** the affected evaluation fails closed
**And** neither an optional dashboard nor a report can override that result.

### Story 10.6: Run and Persist Controlled Physical Evidence

**FRs implemented:** FR18, FR35, FR38-FR41.

As an experiment operator,
I want an approved physical experiment executed and its raw evidence preserved,
So that later analysis can reconstruct what each instrumented edge observed.

**Acceptance Criteria:**

**Given** a frozen `ExperimentSpec.v1`, matrix, profiles, parameter set,
applicable mock-admission records, activity authorization, and qualified
evidence storage
**When** a physical run is requested
**Then** every identity and scope is validated before the run starts
**And** a missing, changed, incompatible, or unauthorized dependency prevents
startup without a fallback.

**Given** an authorized run is active
**When** its declared phases and schedule advance
**Then** only the experiment-control boundary applies the declared references to
the engineering-domain research model
**And** profile-backed transmitters emit `SignalObservation.v2` for the assigned
edge sensors without analytics-to-control input.

**Given** physical observations and control or schedule trace events are emitted
**When** they are persisted
**Then** append-only artifacts preserve experiment, run, stream, edge, sensor,
sequence, correlation, profile, source and observed timestamps, clock quality,
raw current, derived representations, and quality diagnostics
**And** per-edge observations remain separate from aggregate records.

**Given** an expected observation is missing, duplicated, late, out of order,
invalid, or cannot be persisted completely
**When** the run evidence is finalized
**Then** the condition and affected interval are recorded explicitly under the
specification's stopping, exclusion, or abort policy
**And** missing or invalid evidence is never synthesized or treated as normal.

**Given** a run completes, aborts, fails, recovers, or produces an unfavorable
result
**When** its artifacts are closed
**Then** the actual status and all available evidence remain immutable
**And** accelerated or physical-only runs remain labelled as non-fusion-eligible
until a later synchronized campaign satisfies Epic 17A.

**Given** all available objects for a run have been written
**When** publication is attempted
**Then** object identities and hashes are verified before the run manifest is
published last
**And** restricted truth remains outside detector-facing physical evidence.

### Story 10.7: Qualify and Publish Physical Experiment Evidence

**FRs implemented:** FR18, FR39-FR41.

As a research owner,
I want completed physical runs checked against the signal-v2 evidence gate,
So that only coherent and reconstructible physical evidence advances to later
analysis.

**Acceptance Criteria:**

**Given** a completed or terminated physical run
**When** qualification begins
**Then** the run reconstructs from its manifest and exact specification,
profile, parameter, code, runtime, observation, trace, and storage identities
**And** missing or mismatched dependencies fail qualification explicitly.

**Given** reconstructed `SignalObservation.v2` records
**When** signal invariants are evaluated
**Then** raw current, normalized span, engineering derivation, unit, profile,
quality, sequence, correlation, timestamps, and clock quality remain mutually
consistent end to end
**And** under-range, over-range, fault, and missing evidence remain visible
rather than being silently clipped or imputed.

**Given** the same frozen inputs are processed through eligible batch and live
paths
**When** their canonical features are compared
**Then** they agree within the applicable evidenced or preregistered tolerance
**And** the report identifies every discrepancy without selecting only the
better path.

**Given** the experiment specification declares expected streams and run
boundaries
**When** completeness and leakage checks run
**Then** missing, duplicate, late, out-of-order, invalid, partial, or mixed
records are reported with their affected identities
**And** any derived windows remain within one complete run, scenario, schema,
gap policy, and frozen partition.

**Given** detector-facing physical evidence and restricted truth
**When** isolation validation runs
**Then** detector-facing artifacts contain no truth, label, scenario meaning,
future interval, or expected outcome
**And** correlation can be resolved by an authorized evaluator only after the
applicable evidence is frozen.

**Given** all qualification checks complete
**When** the result is published
**Then** every valid, invalid, aborted, failed, recovery, and unfavorable run
retains its actual status, diagnostics, and limitations
**And** only passing evidence receives an explicit
`PHYSICAL_EVIDENCE_QUALIFIED` status.

**Given** the physical evidence satisfies the endpoint, round-trip, quality,
profile, timestamp, persistence, and truth-isolation checks
**When** gate G2 is reported as passed
**Then** the result remains limited to controlled custom physical evidence
**And** it neither closes synchronized `DATASET_QUALIFIED` nor authorizes
training, consensus activation, syscall capture, fusion, deployment, or
dashboard work.

## Epic 11: Validate Physical Evidence Through Current-Domain Consensus

The researcher can validate redundant physical observations through versioned
current-domain CometBFT/ABCI consensus and reconstruct deterministic identical
Python and Go decisions.

### Story 11.1: Define the Versioned Consensus v2 Contracts

**FRs implemented:** FR6, FR9, FR12-FR13, FR91.

As a consensus evidence consumer,
I want explicit input and decision contracts for physical consensus,
So that every comparison has a valid current-domain basis and reconstructible
outcome.

**Acceptance Criteria:**

**Given** a proposed `ConsensusRoundInput.v2`
**When** it is created
**Then** it records schema version, experiment, run and round identities,
instrument profile identities, comparison basis and units, quality policy,
parameter-evidence references, participating edge observations, source
sequences, and correlation identities
**And** every observation resolves to an immutable `SignalObservation.v2`.

**Given** redundant observations from the same compatible profile
**When** their comparison basis is declared
**Then** comparison may occur directly in the preserved current domain
**And** no engineering or normalized representation is substituted without an
explicit versioned basis.

**Given** observations represent different sensors, profiles, ranges, or units
**When** a joint comparison is requested
**Then** the input requires a documented dimensionless, profile-aware residual
with applicable uncertainty and parameter-evidence references
**And** incompatible raw values cannot be averaged or ranked directly.

**Given** a consensus round reaches a decision or fails to do so
**When** `ConsensusDecision.v2` is created
**Then** it records the explicit outcome, comparison basis, complete participant
list, complete edge ranking, included and excluded edges, evidence-based reason
for every exclusion, correlation identities, parameter references, and input
evidence hashes
**And** consensus failure remains distinct from a successful decision with an
empty or reduced participant set.

**Given** consensus input or decision contracts
**When** forbidden-field validation runs
**Then** syscalls, truth, labels, detector scores, fusion decisions, OPC-derived
substitutes, and actuator commands are rejected
**And** consensus remains limited to the physical instrumentation modality.

**Given** valid and invalid contract fixtures
**When** validation and canonical serialization are repeated
**Then** ordering, representation, decision identity, and hashes are
deterministic
**And** missing, mixed, stale, incompatible, or malformed inputs fail with
actionable diagnostics.

### Story 11.2: Resolve Comparison and Trust Parameters

**FRs implemented:** FR7-FR8, FR10-FR12, FR91.

As a research owner,
I want every consensus comparison and trust choice resolved through admissible
parameter evidence,
So that no anonymous or attractive legacy constant controls v2 decisions.

**Acceptance Criteria:**

**Given** a v2 consensus configuration
**When** parameter validation runs
**Then** every scale, uncertainty input, residual definition, tolerance, weight,
trust threshold, exclusion threshold, and boundary rule resolves to an
applicable parameter-evidence ID
**And** its unit, profile, comparison basis, experiment scope, and classification
are compatible.

**Given** a same-profile current-domain comparison
**When** its decision policy is configured
**Then** only parameters applicable to the cited electrical profile and quality
policy are accepted
**And** document citation alone does not make an unrelated tolerance or device
accuracy transferable.

**Given** a cross-sensor or cross-profile comparison
**When** its dimensionless residual is configured
**Then** the derivation, input uncertainties, units, and referenced profiles are
explicit and reproducible
**And** missing uncertainty support or dimensional inconsistency blocks the
configuration.

**Given** an anonymous v1 divergence scale, trust weight, or threshold exists
**When** v2 configuration loads
**Then** the value remains available only to labelled legacy reproduction
**And** it cannot migrate, activate, or become a default in v2.

**Given** a primary configuration and any sensitivity alternatives
**When** the analysis plan is frozen
**Then** the primary choice and every planned alternative reference admissible
parameter records before test or truth access
**And** later outcomes cannot retroactively select a new primary configuration.

**Given** a parameter is missing, conflicting, out of scope, or changed after
freeze
**When** consensus startup or evaluation is requested
**Then** the applicable activity fails closed with the parameter and decision
identity
**And** no fallback value is inferred from architecture, examples, or prior
results.

### Story 11.3: Implement the Deterministic Python Consensus Reference

**FRs implemented:** FR6-FR13, FR91.

As a consensus maintainer,
I want a pure Python reference evaluator for consensus v2,
So that the intended physical comparison and failure semantics have one
inspectable executable reference.

**Acceptance Criteria:**

**Given** validated `ConsensusRoundInput.v2` and a frozen v2 parameter set
**When** the Python reference evaluates the round
**Then** it applies the declared quality policy and comparison basis in a fixed
deterministic order
**And** it produces one canonical `ConsensusDecision.v2` without reading mutable
runtime state.

**Given** observations that fail the declared schema, profile, quality,
freshness, sequence, or correlation rules
**When** eligibility is evaluated
**Then** each affected edge is excluded with its evidence identity and explicit
reason
**And** exclusion never rewrites or repairs the source observation.

**Given** eligible contributions
**When** residuals, trust values, or rankings are calculated
**Then** the evaluator uses only the frozen parameter and derivation records
applicable to the declared basis
**And** ties and numerical boundaries follow an explicit deterministic policy.

**Given** the declared policy cannot produce a valid consensus result
**When** the round completes
**Then** the evaluator emits a distinct fail-closed consensus outcome containing
participants, exclusions, diagnostics, and evidence references
**And** it does not fabricate a winner, trust ranking, or reduced successful
state.

**Given** a round is evaluated repeatedly with identical ordered inputs and
configuration
**When** outputs and structured trace events are compared
**Then** decision fields, complete rankings, exclusions, reasons, serialization,
and hashes are identical
**And** the trace is sufficient to reconstruct every calculation step.

**Given** the reference evaluator executes
**When** its dependency boundaries are inspected
**Then** it has no authority to access truth, syscalls, OPC evidence, detector
outputs, actuator commands, persistence, or network transport
**And** passing its tests does not activate the live consensus path.

### Story 11.4: Integrate Consensus v2 With Go ABCI and CometBFT

**FRs implemented:** FR6, FR9, FR13, FR91.

As a prototype operator,
I want the real Go ABCI and CometBFT path to process consensus v2 rounds,
So that physical decisions are produced by the project's actual consensus
boundary rather than by a stand-alone simulation.

**Acceptance Criteria:**

**Given** an explicitly routed v2 consensus transaction
**When** the Go ABCI boundary decodes it
**Then** it validates schema, profile, basis, units, quality policy, parameter
references, observation identities, sequences, and correlation before execution
**And** unknown, mixed, malformed, or v1 payloads cannot enter the v2 evaluator
implicitly.

**Given** a valid v2 transaction
**When** real CometBFT delivers it through the Go ABCI path
**Then** the application executes the same declared comparison and failure rules
as the Python reference
**And** it produces the canonical `ConsensusDecision.v2` fields required for
commit.

**Given** included and excluded edge contributions
**When** the decision is committed
**Then** the committed record preserves the complete ranking, all participant
and exclusion identities, evidence-based reasons, input hashes, parameter
references, and round correlation
**And** a failed round is committed or reported as its explicit failure state,
never disguised as success.

**Given** shared valid, invalid, boundary, and failure fixtures
**When** Python and Go evaluate them
**Then** canonical decisions and structured calculation outcomes are identical
**And** any mismatch keeps the entire consensus v2 route in shadow.

**Given** consensus v2 is promoted or rolled back
**When** routing changes
**Then** Python contracts, Go transaction and state types, schemas, fixtures,
and downstream mapping move as one compatible versioned unit
**And** neither language implementation can activate independently.

**Given** CometBFT, ABCI, MQTT, storage, analytics, or optional presentation
fails
**When** the experiment-control boundary continues operating
**Then** consensus reports its own unavailable or failed evidence state
**And** it cannot create, alter, or authorize a compressor command.

### Story 11.5: Preserve Versioned State, Query, Restart, and Rollback

**FRs implemented:** FR7, FR9, FR11, FR13, FR91.

As an evidence auditor,
I want v1 and v2 consensus state to remain explicitly versioned and replayable,
So that current-domain consensus does not rewrite historical CometBFT evidence.

**Acceptance Criteria:**

**Given** existing v1 CometBFT state and new v2 state types
**When** v2 storage keys and state records are introduced
**Then** each version uses an explicit non-conflicting identity and decoder
**And** historical v1 bytes, keys, heights, and AppHash evidence remain
unchanged.

**Given** a state or decision query
**When** it reaches the ABCI query boundary
**Then** the requested contract version selects the matching v1 or v2 route and
returns its declared schema identity
**And** missing or unknown versions fail explicitly rather than attempting
cross-version decoding.

**Given** a supported compatibility projection from v2 to a v1 consumer
**When** the adapter is invoked
**Then** the projection is separately versioned and tested and preserves its
source v2 evidence identity
**And** no missing v2 fact is inferred from a v1 field or written back into
historical state.

**Given** committed v2 rounds and a pinned code and runtime identity
**When** the consensus services restart and replay
**Then** state, query responses, decisions, heights, and application hashes
reconstruct deterministically
**And** corruption, version mismatch, or an unpinned runtime fails the restart
qualification.

**Given** consensus decisions and structured round logs are persisted
**When** an auditor reconstructs a round
**Then** immutable records resolve participants, rankings, exclusions, reasons,
inputs, parameters, code, runtime, height, and decision outcome without a
dashboard or hidden state
**And** mutable aliases are not accepted as evidence identity.

**Given** consensus v2 requires rollback
**When** an authorized explicit version identity is selected
**Then** routing returns to the previously verified path without deleting or
rewriting v1 or v2 transactions, state, decisions, logs, or manifests
**And** the rollback itself is recorded as evidence.

### Story 11.6: Qualify Consensus v2 and Close Gate G3

**FRs implemented:** FR6-FR14, FR91.

As a research owner,
I want consensus v2 qualified against shared reference and integration evidence,
So that its physical decisions are deterministic, reconstructible, and honest
about parameter sensitivity.

**Acceptance Criteria:**

**Given** shared fixtures covering valid, invalid, missing, stale, mixed-profile,
mixed-unit, boundary, exclusion, tie, and consensus-failure cases
**When** the Python reference and Go implementation evaluate them
**Then** decision fields, rankings, exclusions, reasons, failure states,
structured traces, canonical serialization, and hashes are identical
**And** every mismatch is retained with its fixture and diagnostic.

**Given** a declared integration fixture
**When** it travels through the real CometBFT and Go ABCI transaction, commit,
state, and query path
**Then** the resulting v2 decision matches the Python reference for the same
frozen inputs
**And** the test does not substitute a local function call for the consensus
boundary.

**Given** committed v1 and v2 evidence
**When** restart, replay, query, compatibility, and rollback checks execute
**Then** v2 behavior remains deterministic and historical v1 state and AppHash
evidence remain unchanged
**And** an unknown version or incompatible runtime fails closed.

**Given** a frozen primary configuration and preregistered sensitivity
alternatives
**When** sensitivity results are produced
**Then** every planned value and outcome is retained with its parameter evidence
and limitation
**And** test or truth results cannot retroactively change the primary
configuration or hide an unfavorable alternative.

**Given** a reported consensus decision
**When** its provenance chain is reconstructed
**Then** it resolves from experiment and round identities through raw physical
observations, profile, basis, parameter set, Python and Go code, runtime, ABCI
state, logs, and immutable decision record
**And** reconstruction requires no UI or mutable latest-only state.

**Given** parity, integration, state, query, restart, compatibility, provenance,
and sensitivity checks complete
**When** gate G3 is evaluated
**Then** any failure keeps consensus v2 in shadow with a specific blocking
reason
**And** passing G3 records consensus qualification only; it does not authorize
default activation, experiments, detector training, fusion, deployment, or
dashboard work.

## Epic 12: Compare Against Independent OPC UA Evidence

The researcher can compare consensus against a genuinely independent,
pre-consensus OPC UA observation and obtain explicit quality, freshness,
correlation, availability, and causal-independence evidence.

### Story 12.1: Publish the Pre-Consensus Plant and Transmitter Snapshot

**FRs implemented:** FR42.

As an evidence producer,
I want the OPC UA branch sourced from a correlated pre-consensus snapshot,
So that it cannot become a circular projection of the consensus result.

**Acceptance Criteria:**

**Given** an authorized physical experiment cycle
**When** the process and transmitter state is sampled before consensus
**Then** a versioned snapshot records experiment, run, cycle, source sequence,
correlation and revision identities, source timestamp and clock quality, exact
instrument profile, engineering process value, transmitted raw current,
quality, and parameter references
**And** the snapshot contains no committed consensus value or ranking.

**Given** the physical edge and OPC UA writer consume evidence from the same
cycle
**When** lineage is recorded
**Then** both branches reference the same immutable pre-consensus snapshot
identity
**And** neither branch uses the other branch's observed or derived output as its
source.

**Given** a snapshot's process value and transmitter representations
**When** consistency validation runs
**Then** current and engineering fields reconcile through the exact cited
instrument profile
**And** invalid quality, profile, parameter, timestamp, sequence, or correlation
prevents publication to the OPC branch.

**Given** a snapshot revision has already been accepted by the OPC writer
**When** an older, duplicate, or conflicting revision arrives
**Then** the revision guard rejects or explicitly classifies it according to the
declared policy
**And** the writer cannot silently replace newer evidence with stale state.

**Given** snapshot creation or OPC publication fails
**When** the experiment-control path continues
**Then** the OPC branch records missing or unavailable evidence for that cycle
**And** it cannot alter the physical command, edge observation, or consensus
input.

**Given** snapshots are persisted
**When** an auditor follows their provenance
**Then** the OPC and edge branch point is reconstructible from immutable
identities and hashes
**And** no dashboard or in-memory server object is required to establish the
source lineage.

### Story 12.2: Run OPC UA as a Separate Server Boundary

**FRs implemented:** FR15, FR43, FR48, FR90.

As a laboratory operator,
I want OPC UA state exposed by a separate local server boundary,
So that protocol evidence cannot be replaced by shared in-process objects.

**Acceptance Criteria:**

**Given** the OPC UA server configuration
**When** the server starts
**Then** it exposes an explicit `opc.tcp` endpoint, application identity,
security mode, namespace identity, and versioned NodeIds
**And** incomplete or conflicting endpoint configuration fails startup without
an anonymous default.

**Given** a validated pre-consensus snapshot
**When** the OPC writer updates the server
**Then** it writes only the declared snapshot revision, value, profile,
correlation, quality, and source-time fields
**And** the server neither reads nor derives values from consensus state.

**Given** current and engineering representations are exposed
**When** the address space is inspected
**Then** raw current and engineering value use distinct declared analogue nodes
with their applicable units, profile, and range metadata
**And** any normalized research value is optional and confined to an explicitly
labelled research namespace.

**Given** a value is accepted by the server
**When** its OPC UA `DataValue` is produced
**Then** value, `StatusCode`, source timestamp, server timestamp, revision,
profile, and correlation remain available to protocol clients
**And** absent or invalid source information is represented explicitly rather
than fabricated.

**Given** the OPC consumer is absent, disconnected, or restarted
**When** the writer and server continue
**Then** server behavior remains independent of the consumer lifecycle
**And** no client-side cache or object reference becomes authoritative server
state.

**Given** the server, writer, or OPC transport fails
**When** the control and physical evidence paths operate
**Then** the OPC branch records its unavailable or failed state
**And** it cannot generate, alter, or authorize compressor commands, consensus
decisions, or detector results.

### Story 12.3: Read OPC UA Through a Real Client Contract

**FRs implemented:** FR43-FR45, FR48, FR90.

As an OPC evidence consumer,
I want observations read through a distinct real OPC UA client session,
So that comparison evidence proves the protocol boundary was exercised.

**Acceptance Criteria:**

**Given** independent OPC mode is explicitly enabled
**When** an observation is requested
**Then** a distinct `asyncua.Client` connects to the declared `opc.tcp` endpoint
and reads the versioned namespace and NodeIds
**And** internal server objects, writer memory, consensus state, cached truth,
and projected fallback values are inaccessible to the adapter.

**Given** a client read succeeds
**When** `ScadaObservation.v2` is created
**Then** it records schema version, endpoint and security mode, namespace and
NodeIds, experiment, run and correlation identities, snapshot revision,
profile, raw current and engineering values with units, `StatusCode`, source and
server timestamps, client-observed timestamp, attempts, latency, freshness
evidence, and source snapshot reference
**And** the original `DataValue` semantics remain distinguishable from client
diagnostics.

**Given** multiple nodes are required for one observation
**When** their values are assembled
**Then** the declared revision guard, profile, correlation, and timestamp policy
proves they belong to one eligible snapshot
**And** mixed revisions or identities produce an explicit invalid observation.

**Given** the client cannot connect, authenticate, resolve nodes, or complete a
coherent read
**When** the attempt ends
**Then** endpoint, attempt, latency, error, and blocking reason are recorded
without fabricating a value or timestamp
**And** no consensus or last-known-good value is substituted.

**Given** v2 OPC mode is disabled or an artifact declares another version
**When** routing occurs
**Then** existing v1 behavior remains unchanged and the explicit matching route
is selected where supported
**And** an enabled missing or incompatible v2 source fails closed rather than
falling back silently.

**Given** valid and invalid `ScadaObservation.v2` fixtures
**When** validation and canonical serialization run
**Then** field invariants, ordering, representation, and hashes are deterministic
**And** consensus-derived values, truth, labels, detector outputs, fusion
decisions, and actuator commands are rejected.

### Story 12.4: Validate and Compare Eligible OPC UA Evidence

**FRs implemented:** FR16, FR44-FR46, FR90.

As an academic evaluator,
I want OPC integrity checked before comparison with consensus,
So that unavailable or invalid protocol evidence cannot masquerade as agreement
or divergence.

**Acceptance Criteria:**

**Given** a `ScadaObservation.v2`
**When** OPC integrity validation runs
**Then** schema, endpoint, namespace, NodeIds, profile, snapshot revision,
correlation, units, `StatusCode`, source and server timestamps, freshness,
attempts, and value consistency are evaluated
**And** every freshness or timing limit resolves to applicable parameter
evidence rather than an architectural default.

**Given** bad, uncertain, stale, missing, mixed-revision, mixed-profile,
mis-correlated, inconsistent, or unavailable OPC evidence
**When** eligibility is decided
**Then** the evidence receives an explicit invalid or unavailable outcome with
diagnostics and source references
**And** no valid-state comparison is calculated or persisted.

**Given** eligible OPC evidence and a correlated `ConsensusDecision.v2`
**When** comparison begins
**Then** both inputs resolve to the same experiment, run, cycle or round,
profile context, and pre-consensus branch identity
**And** neither input is derived from or silently substituted for the other.

**Given** compatible same-profile values
**When** the comparison is calculated
**Then** it uses the declared current-domain basis or another explicitly
versioned eligible basis
**And** cross-profile or cross-sensor comparison requires the documented
dimensionless, uncertainty-aware residual defined for consensus v2.

**Given** a comparison tolerance, uncertainty, or classification boundary
**When** the comparison policy loads
**Then** each numeric choice resolves to an applicable parameter-evidence ID
**And** anonymous legacy sensor tolerances or values selected after seeing the
result are rejected.

**Given** an eligible comparison completes
**When** its result is persisted
**Then** it records OPC integrity separately from comparison outcome and binds
both inputs, values, units, basis, difference or residual, parameters,
timestamps, correlation, diagnostics, code, and runtime identities
**And** the result has no authority to modify consensus, OPC source state, or
experiment control.

### Story 12.5: Prove OPC and Consensus Causal Path Independence

**FRs implemented:** FR47, FR90.

As an academic evaluator,
I want controlled causal tests of the OPC and consensus branches,
So that software-path independence is demonstrated rather than merely asserted.

**Acceptance Criteria:**

**Given** a fixed pre-consensus snapshot and OPC path
**When** only consensus inputs, parameters, or committed state are varied after
the branch point
**Then** the OPC source snapshot and client-read values remain unchanged
**And** any observed OPC change is reported as a causal-independence violation.

**Given** fixed physical observations and consensus configuration
**When** only OPC writer, server, node, transport, or client conditions are
varied after the branch point
**Then** the consensus input and decision remain unchanged
**And** any observed consensus change is reported as a causal-independence
violation.

**Given** the shared pre-consensus snapshot itself changes
**When** both branches process the new revision
**Then** each branch may change only through its documented lineage from that
common source
**And** the test distinguishes common-source dependence from cross-branch
dependence.

**Given** the OPC server or client is stopped, disconnected, delayed, or
restarted
**When** consensus continues
**Then** OPC evidence becomes explicitly unavailable, delayed, or newly read
according to its own state
**And** no in-memory, last-known, or consensus-projected fallback produces valid
OPC evidence.

**Given** the causal test matrix completes
**When** its traces and dependency evidence are inspected
**Then** snapshot, writer, server, client, consensus, and comparison identities
and transitions are reconstructible
**And** violations block independent-OPC qualification.

**Given** all causal software-path tests pass
**When** the conclusion is reported
**Then** it is limited to logical and transport-path independence in the
controlled prototype
**And** it does not claim independent physical instrumentation, plant
redundancy, or real-world SCADA validation.

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

## Epic 13: Train and Serve a Calibrated Physical Anomaly Detector

The researcher can compare LSTM-AE, GRU-AE, and declared baselines fairly,
calibrate without leakage, blindly evaluate controlled physical anomalies, and
serve an exact immutable physical bundle in inference-only shadow mode.

### Story 13.1: Define the Physical Feature Schema

**FRs implemented:** FR19, FR49, FR78.

As a model developer,
I want one versioned current-domain physical feature schema,
So that every detector candidate receives features with explicit meaning,
ordering, units, provenance, and compatibility.

**Acceptance Criteria:**

**Given** a proposed physical feature schema
**When** it is registered
**Then** it records a stable schema ID, version and hash, ordered feature names,
source fields, representations, units, data types, profile compatibility,
missingness policy, and parameter-evidence references
**And** unavailable or excluded features are explicit rather than inferred.

**Given** a `SignalObservation.v2`
**When** physical features are constructed
**Then** every current, normalized, engineering, quality, temporal, or approved
operating-context feature derives through its declared canonical observation and
profile path
**And** the feature builder does not reimplement transmitter conversion.

**Given** an operating reference such as `speed_reference_pct` or
`capacity_reference_pct` is included as context
**When** its feature role is validated
**Then** it resolves to the frozen experiment specification and applicable
parameter evidence
**And** it reveals no scenario truth, intervention meaning, or future outcome.

**Given** mixed profiles, units, representations, or scales
**When** one tensor is requested
**Then** the schema applies only its declared compatible projection and
preprocessing path
**And** incompatible or undeclared mixing fails closed rather than allowing one
scale to dominate silently.

**Given** the existing mixed-scale autoencoder or its inputs
**When** they are catalogued for comparison
**Then** they remain explicitly labelled `LEGACY_BASELINE` under their v1
contract
**And** they cannot be treated as the final physical detector, a dataset, or a
compatible v2 feature path.

**Given** batch and live feature construction receive identical canonical
observations and frozen preprocessing state
**When** their outputs are compared
**Then** order, values, missingness, and representation agree within an
evidenced or preregistered tolerance
**And** truth, labels, future values, detector decisions, and fusion outputs are
absent from both paths.

### Story 13.2: Build Leakage-Safe Physical Partitions and Windows

**FRs implemented:** FR25, FR49, FR86.

As an evaluator,
I want complete physical runs partitioned before preprocessing and windowing,
So that temporal neighbors, fitted state, and test information cannot leak
between lifecycle stages.

**Acceptance Criteria:**

**Given** qualified physical run manifests
**When** the physical partition record is frozen
**Then** complete independent runs are assigned to the applicable training,
validation, calibration, and locked-test roles before any window is generated
**And** one run cannot appear in more than one role.

**Given** a frozen partition and feature schema
**When** sequences or windows are generated
**Then** no window crosses a run, experiment, declared phase or scenario
boundary, gap, invalid interval, profile, schema, or partition
**And** window length, stride, padding, and exclusion rules resolve to parameter
evidence.

**Given** preprocessing requires fitted state
**When** that state is learned
**Then** it uses only eligible normal training evidence and records the exact
training runs, schema, algorithm, parameters, and output hash
**And** validation, calibration, test, truth, and future observations remain
inaccessible.

**Given** frozen preprocessing is applied to validation, calibration, test, or
live observations
**When** transformation runs
**Then** it loads the exact training-fitted state without fitting or updating it
**And** schema, profile, feature-order, missingness, or hash mismatch fails
closed.

**Given** partitioned windows are persisted
**When** their lineage is inspected
**Then** every window resolves to its source run, observation range, partition,
feature schema, preprocessing identity, quality, and exclusions
**And** detector-facing window artifacts contain no truth or label fields.

**Given** partition or leakage validation finds overlap, boundary crossing,
truth exposure, mixed identity, or undeclared exclusion
**When** dataset preparation completes
**Then** the affected physical candidate input is rejected with diagnostics
**And** no model comparison, calibration, or test evaluation may use it.

### Story 13.3: Compare Physical Detector Candidates Fairly

**FRs implemented:** FR19, FR52, FR78.

As a researcher,
I want LSTM-AE, GRU-AE, and declared simpler or classical baselines compared
under one frozen protocol,
So that model-family conclusions follow evidence rather than the original
LSTM-only premise.

**Acceptance Criteria:**

**Given** the physical candidate plan
**When** it is frozen before fitting
**Then** it includes LSTM-AE, GRU-AE, and at least one declared transparent
simpler or classical baseline with architecture and parameter identities
**And** no candidate is designated superior in advance.

**Given** the candidate set
**When** training and selection execute
**Then** every candidate receives the same eligible feature schema, complete-run
partitions, preprocessing inputs, tuning access, declared resource budget,
repetitions, and primary selection metrics
**And** model-specific exceptions are preregistered and reported rather than
hidden.

**Given** a candidate requires fitted model state
**When** fitting runs
**Then** it uses only qualified normal training evidence and the exact frozen
preprocessing state
**And** calibration, locked test, truth, labels, and future evidence remain
unavailable.

**Given** hyperparameters, sequence dimensions, optimization settings, stopping
rules, or resource limits
**When** a candidate configuration is validated
**Then** every executable numeric choice resolves to applicable evidence or a
frozen preregistered decision
**And** no architecture example or legacy constant becomes a silent default.

**Given** candidate fitting or validation succeeds, fails, stops early, exceeds
its declared budget, or produces an unfavorable result
**When** the comparison record is published
**Then** every planned run retains its configuration, seed, inputs, outputs,
status, resource evidence, diagnostics, and limitations
**And** the report does not select only successful repetitions or the best seed.

**Given** validation-only comparison results
**When** a candidate is selected for calibration
**Then** the preregistered selection rule is applied without test or truth access
**And** the selected candidate identity and all non-selected outcomes are frozen
before calibration begins.

### Story 13.4: Calibrate and Freeze the Physical Threshold

**FRs implemented:** FR50.

As an evaluator,
I want the physical anomaly threshold calibrated independently and frozen before
test access,
So that held-out outcomes cannot tune the detector decision boundary.

**Acceptance Criteria:**

**Given** the selected frozen candidate and its declared calibration partition
**When** calibration scores are produced
**Then** inference loads the exact candidate and preprocessing state without
fitting or updating either
**And** locked test evidence, test truth, scenario labels, and future runtime
observations remain inaccessible.

**Given** a threshold calibration method
**When** its configuration is validated
**Then** the method, score direction, inputs, parameters, applicable assumptions,
and selection rationale resolve to evidence or preregistered decisions
**And** no universal percentile, loss value, target rate, or threshold is
invented.

**Given** calibration completes
**When** the threshold record is frozen
**Then** it binds candidate, preprocessing, feature schema, calibration runs and
scores, partition, method, score direction, threshold value and unit,
parameters, code, runtime, timestamp, and content hash
**And** a change to any identity-bearing component creates a new threshold
identity.

**Given** preregistered threshold-sensitivity alternatives
**When** they are frozen
**Then** every alternative is identified before test or truth unlock and uses
the same eligible calibration evidence
**And** later evaluation cannot replace the primary threshold with the
best-looking alternative.

**Given** calibration evidence is missing, mixed, stale, insufficient under the
declared policy, or incompatible with the selected candidate
**When** threshold freeze is requested
**Then** calibration fails with explicit diagnostics
**And** no legacy, latest, test-derived, or runtime-derived threshold is
substituted.

**Given** a frozen threshold is later loaded
**When** inference or replay begins
**Then** the exact threshold and score direction are verified without
recalculation
**And** runtime inference has no operation that fits, recalibrates, or mutates
the threshold.

### Story 13.5: Build the Immutable Physical `DetectorBundle.v1`

**FRs implemented:** FR20, FR22, FR51, FR87.

As a prototype operator,
I want the selected physical detector packaged as one atomic immutable bundle,
So that inference cannot mix compatible-looking but scientifically different
components.

**Acceptance Criteria:**

**Given** an approved calibrated physical candidate
**When** `DetectorBundle.v1` is assembled
**Then** it binds model family, architecture, weights, ordered feature schema,
preprocessing state, training and calibration dataset and split hashes, frozen
threshold and derivation, score direction, profile compatibility, code,
dependencies, runtime, and component hashes
**And** the bundle receives one canonical content-addressed identity.

**Given** any weight, architecture field, feature order, profile rule,
preprocessing value, dataset or split, calibration artifact, threshold,
dependency, or runtime identity changes
**When** bundling is requested
**Then** a new bundle identity is created
**And** the existing bundle remains immutable and reconstructible.

**Given** a saved bundle
**When** it is loaded in an eligible declared environment
**Then** every required component, schema, version, hash, feature order, runtime,
and profile compatibility rule verifies atomically before inference
**And** a missing, stale, changed, or incompatible component fails the entire
load.

**Given** bundle load or inference code
**When** its callable operations are inspected and exercised
**Then** it contains no training, preprocessing fit, vocabulary fit, threshold
calibration, truth access, or online-update path
**And** load never guesses or resolves a mutable `latest` artifact.

**Given** a v1 legacy model or mixed-scale autoencoder artifact
**When** it is presented with the v2 physical feature schema
**Then** compatibility validation rejects the combination explicitly
**And** no implicit reshaping, rescaling, field dropping, or adapter inference
occurs.

**Given** the bundle is published
**When** its artifact manifest is finalized
**Then** all immutable components are verified before the complete bundle
manifest is published last
**And** publication alone does not promote, deploy, activate, or authorize the
bundle.

### Story 13.6: Produce Frozen Blind Physical Scores

**FRs implemented:** FR21, FR29, FR49-FR50, FR54, FR87.

As an evaluator,
I want the exact physical bundle to produce immutable scores on locked test
evidence before truth unlock,
So that later metrics cannot influence preprocessing, calibration, or detector
decisions.

**Acceptance Criteria:**

**Given** a frozen physical bundle, locked complete-run test partition, metric
policy, and applicable activity authorization
**When** blind test inference is requested
**Then** all bundle, schema, preprocessing, partition, profile, code, dependency,
runtime, and input hashes verify before scoring
**And** any incompatibility blocks scoring without fitting or fallback.

**Given** an eligible physical test window
**When** inference completes
**Then** `DetectorScore.v1` records bundle and window identities, raw and
calibrated score, score direction, frozen threshold identity, decision, latency,
missingness, input quality, profile, run correlation, code, and runtime identity
**And** it contains no truth, scenario, attack, intervention, or expected-outcome
field.

**Given** frozen preprocessing and threshold state
**When** test windows are scored
**Then** inference only transforms and predicts with the loaded bundle
**And** it never fits, tunes, selects, recalibrates, imputes through undeclared
state, or changes the threshold.

**Given** a window is missing, low quality, boundary-crossing, incompatible, or
cannot be scored
**When** the score stream is finalized
**Then** the unavailable or invalid score and its reason are preserved
**And** it is not represented as a normal decision or silently removed.

**Given** identical frozen inputs and declared runtime
**When** blind scoring is repeated
**Then** score records and decisions reproduce within the applicable evidenced
or preregistered tolerance
**And** every discrepancy is retained with environment and resource diagnostics.

**Given** all planned test windows have been processed or explicitly accounted
for
**When** the score manifest is published
**Then** score objects, missingness, failures, resource evidence, and hashes are
frozen before truth unlock
**And** only the immutable score-manifest identity may enter evaluation.

### Story 13.7: Evaluate Physical Regimes and Anomalies After Truth Unlock

**FRs implemented:** FR23, FR27, FR52, FR88.

As a research owner,
I want frozen physical scores evaluated against separately protected truth,
So that operating transitions and declared anomalies are reported without
retroactively changing the detector.

**Acceptance Criteria:**

**Given** immutable score, bundle, threshold, partition, metric-policy, and truth
identities
**When** the authorized evaluator unlocks truth
**Then** it joins truth to scores only through frozen experiment, run, window,
event, and correlation identities
**And** no score, decision, threshold, preprocessing state, partition, or model
artifact is modified.

**Given** the preregistered 25%-75% speed or capacity reference schedule
**When** regime-aware evaluation runs
**Then** commanded regimes and transitions remain distinct from declared
anomaly scenarios and intervention truth
**And** a reference change is not automatically counted as an anomaly.

**Given** the physical evaluation applicability matrix
**When** results are calculated
**Then** applicable point or window and event or range outcomes include the
declared subset of PR-AUC, precision, recall, F1, false-positive behavior, false
events per operating hour, time to detection, suitable confusion data,
threshold sensitivity, resource cost, modality quality or availability, and
repeated-run dispersion or uncertainty
**And** inapplicable metrics are marked with their reason rather than fabricated.

**Given** planned scenarios, severities, sensors, regimes, repetitions,
transitions, recovery periods, and quality states
**When** results are stratified
**Then** the report preserves every applicable declared stratum and sample or
event support
**And** aggregation cannot hide a failed, unfavorable, invalid, or low-quality
stratum.

**Given** preregistered threshold-sensitivity alternatives
**When** sensitivity is evaluated
**Then** all planned alternatives and outcomes are reported against the same
frozen scores and truth
**And** none replaces the frozen primary threshold or detector decision record.

**Given** completed, failed, aborted, unavailable, or unfavorable candidate and
test runs
**When** the evaluation package is published
**Then** statuses, metrics, dispersion, resource and quality evidence,
limitations, locally measured role, and immutable provenance are retained
**And** no selected best seed or model-family superiority claim replaces the
complete evidence.

### Story 13.8: Serve an Authorized Physical Bundle in Shadow and Close G5

**FRs implemented:** FR20-FR22, FR29, FR51, FR53-FR54.

As a prototype operator,
I want an explicitly selected immutable physical bundle served in inference-only
shadow mode,
So that detector behavior can be reproduced without control authority or online
learning.

**Acceptance Criteria:**

**Given** a bundle is proposed for the local physical shadow route
**When** selection is requested
**Then** an explicit record binds bundle, profile, parameter set, feature schema,
preprocessing, threshold, code, dependency, and runtime identities
**And** a separate applicable activity authorization is required; planning
approval or a mutable `latest` name is insufficient.

**Given** a selected compatible bundle and live `SignalObservation.v2` stream
**When** shadow inference runs
**Then** it uses the bundle's exact feature, preprocessing, model, score
direction, and threshold contracts to emit `DetectorScore.v1`
**And** it has no truth access, training, fitting, recalibration, online update,
promotion decision, or actuator-write capability.

**Given** the bundle or input stream is absent, stale, corrupt, unverified, or
incompatible by profile, schema, feature order, version, hash, dependency, or
runtime
**When** shadow inference is requested
**Then** it emits an explicit unavailable or incompatible detector state with
diagnostics
**And** it never guesses another bundle, adapts fields silently, or treats the
failure as a normal decision.

**Given** a previously verified physical bundle is selected for rollback
**When** an authorized rollback occurs
**Then** the local shadow route points to that exact immutable identity
**And** no observations, bundles, thresholds, scores, evaluations, or manifests
are deleted or rewritten.

**Given** frozen test inputs, score fixtures, and the bundle's declared
environment
**When** G5 replay qualification runs
**Then** load, batch and shadow feature parity, inference-only behavior, scores,
decisions, and failure-on-mismatch checks reproduce within applicable evidenced
or preregistered tolerances
**And** every discrepancy is recorded rather than hidden by recalibration.

**Given** the G5 checks complete
**When** the gate result is issued
**Then** any failure blocks shadow selection or returns it to the last verified
explicit identity with a recorded reason
**And** passing G5 qualifies only the physical bundle and local shadow path; it
does not authorize control, syscall capture, fusion, broader deployment, or UI
work.

## Epic 14: Capture and Detect Real Linux Edge Syscall Anomalies

The researcher can run an allowlisted controlled Linux edge workload, capture
the real kernel calls it actually emits, quantify attribution and capture
quality, and compare categorical normal-only syscall detectors.

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

### Story 14.4: Build Categorical Syscall Partitions and Windows

**FRs implemented:** FR25, FR80, FR86.

As a model developer,
I want authentic syscall streams canonicalized and partitioned with explicit
session and loss boundaries,
So that detector sequences preserve categorical meaning without leakage.

**Acceptance Criteria:**

**Given** immutable host-capture segments and batches
**When** categorical canonicalization runs
**Then** each syscall retains its ordered categorical name and direction,
kernel or ABI context, source identity, sequence, timestamp, and raw-segment
lineage
**And** unknown or unmapped events remain explicit rather than being guessed or
dropped silently.

**Given** qualified custom capture runs
**When** the partition record is frozen
**Then** complete independent runs and applicable boot, session, container,
process, and capture-group identities are assigned before windowing to training,
validation, calibration, and locked-test roles
**And** no group appears in more than one role.

**Given** a frozen partition and categorical feature specification
**When** sequences or windows are generated
**Then** no window crosses a run, boot, session, container, process, raw segment,
gap, loss-policy boundary, collector or filter, kernel or ABI, schema, or
partition
**And** window and exclusion parameters resolve to admissible evidence.

**Given** vocabulary, embedding index, frequency state, or other preprocessing
requires fitting
**When** it is learned
**Then** it uses only eligible normal training evidence and records exact input,
mapping, unknown-event policy, parameters, code, and output hashes
**And** validation, calibration, test, truth, and future events remain
inaccessible.

**Given** loss, gaps, duplicates, queue pressure, or incomplete attribution
affects a segment
**When** windows are prepared
**Then** the preregistered flag, exclusion, or abort policy is applied and the
affected windows retain quality evidence
**And** missing events are never imputed as observed calls or treated as normal.

**Given** prepared categorical windows
**When** lineage and leakage validation runs
**Then** every window resolves to source segments, batches, groups, partition,
vocabulary, preprocessing, capture quality, and exclusions
**And** truth, labels, scenario meaning, and fixture-only evidence are absent
from formal detector inputs.

### Story 14.5: Compare Normal-Only Categorical Syscall Candidates

**FRs implemented:** FR81.

As a security researcher,
I want recurrent and transparent categorical syscall detectors compared under
one frozen protocol,
So that sequence-model claims are measured rather than assumed.

**Acceptance Criteria:**

**Given** the custom syscall candidate plan
**When** it is frozen before fitting
**Then** it includes embedding-plus-LSTM, embedding-plus-GRU, and a transparent
n-gram or STIDE-style baseline with exact architecture and parameter identities
**And** no candidate is designated superior in advance.

**Given** the candidate set
**When** fitting and selection run
**Then** candidates receive the same eligible categorical schema, group-safe
partitions, vocabulary and preprocessing inputs, tuning access, declared budget,
repetitions, capture-quality policy, and primary metrics
**And** model-specific exceptions are preregistered and reported.

**Given** a candidate requires fitted state
**When** it is trained
**Then** it uses only qualified normal training sequences from authentic
host-capture evidence
**And** calibration, locked test, truth, labels, future events, and fixture replay
remain inaccessible.

**Given** syscall names or ABI-specific numeric IDs
**When** a model objective is configured
**Then** events remain categorical through explicit vocabulary or sequence
semantics
**And** numeric IDs are not treated as continuous values or optimized with
reconstruction MSE solely because they are numbers.

**Given** model dimensions, windows, hyperparameters, stopping rules, resource
budgets, or repetitions
**When** configuration validation runs
**Then** every executable numeric choice resolves to applicable evidence or a
frozen preregistered decision
**And** tool examples, external dataset settings, and architecture defaults do
not become silent custom-capture constants.

**Given** candidate runs succeed, fail, abort, exceed quality or resource
limits, or produce unfavorable results
**When** the comparison record is published
**Then** every planned configuration, seed, input, output, status, capture
quality, resource evidence, diagnostic, and limitation remains visible
**And** the preregistered validation-only selection rule freezes one candidate
for calibration without test or truth access.

### Story 14.6: Calibrate and Bundle the Custom Syscall Detector

**FRs implemented:** FR81, FR87.

As an evaluator,
I want the selected categorical syscall candidate calibrated and packaged
immutably,
So that later scoring uses one exact vocabulary, model, and decision threshold.

**Acceptance Criteria:**

**Given** the selected frozen candidate and declared syscall calibration
partition
**When** calibration scores are produced
**Then** the exact vocabulary, preprocessing, feature specification, model, and
capture-quality policy load without fitting or updating
**And** locked test, truth, scenario labels, future events, and fixture replay
remain inaccessible.

**Given** a syscall threshold method and any sensitivity alternatives
**When** calibration is validated and frozen
**Then** score direction, method, inputs, parameters, primary threshold, planned
alternatives, rationale, and hashes are recorded before test or truth access
**And** no threshold or target rate is copied from an external benchmark or
selected from later results.

**Given** the calibrated candidate
**When** its `DetectorBundle.v1` is assembled
**Then** it binds model family, architecture, weights or state, ordered
categorical schema, vocabulary, unknown-event policy, preprocessing, training
and calibration source and split hashes, capture compatibility, frozen threshold
and derivation, score direction, code, dependencies, runtime, and component
hashes
**And** the complete bundle receives one content-addressed identity.

**Given** any vocabulary, preprocessing, model, training or calibration data,
capture compatibility rule, threshold, dependency, or runtime identity changes
**When** bundling is requested
**Then** a new bundle identity is created
**And** the previous bundle remains immutable.

**Given** a saved syscall bundle
**When** load and inference-only validation run
**Then** every component, version, hash, categorical order, capture context, and
runtime identity verifies atomically
**And** load contains no fit, vocabulary update, recalibration, truth access, or
mutable `latest` fallback.

**Given** calibration or bundle inputs are missing, stale, mixed, fixture-only,
or incompatible
**When** publication is attempted
**Then** the bundle fails closed with explicit diagnostics
**And** no legacy, physical-detector, external-dataset, or partial artifact is
substituted.

### Story 14.7: Produce Frozen Blind Syscall Scores

**FRs implemented:** FR79-FR81, FR87.

As an evaluator,
I want the exact custom syscall bundle to score locked host-capture evidence
before truth unlock,
So that later outcomes cannot alter the categorical detector or its threshold.

**Acceptance Criteria:**

**Given** a frozen syscall bundle, locked complete-group test partition, metric
policy, and applicable activity authorization
**When** blind test inference is requested
**Then** bundle, vocabulary, schema, preprocessing, partition, capture context,
threshold, code, dependency, runtime, and input hashes verify before scoring
**And** mismatch or fixture-only provenance blocks formal scoring.

**Given** an eligible categorical syscall window
**When** inference completes
**Then** `DetectorScore.v1` records bundle and window identities, raw and
calibrated score, score direction, frozen threshold, decision, latency,
missingness, capture quality, run and workload correlation, code, and runtime
identity
**And** it contains no truth, attack label, scenario meaning, intervention, or
expected outcome.

**Given** frozen vocabulary, preprocessing, model, and threshold state
**When** test windows are scored
**Then** inference only transforms and predicts with the loaded bundle
**And** it never fits, extends the vocabulary, tunes, recalibrates, or changes
the decision policy.

**Given** a window is affected by unresolved attribution, gaps, drops,
duplicates, boundary crossing, incompatible ABI or kernel, or capture-quality
failure
**When** score production runs
**Then** the invalid or unavailable score and declared flag, exclusion, or abort
reason are preserved
**And** the window is not silently scored as normal or removed from accounting.

**Given** identical frozen inputs and declared runtime
**When** blind scoring is repeated
**Then** score records and decisions reproduce within applicable evidenced or
preregistered tolerances
**And** discrepancies retain collector, kernel, workload, quality, resource, and
runtime diagnostics.

**Given** all planned locked-test windows are scored or explicitly accounted for
**When** the score manifest is finalized
**Then** score objects, invalid and unavailable windows, capture quality,
resource evidence, and hashes are frozen before truth unlock
**And** only the immutable score-manifest identity may enter evaluation.

### Story 14.8: Evaluate the Custom Syscall Detector After Truth Unlock

**FRs implemented:** FR27, FR81, FR88.

As a research owner,
I want frozen custom syscall scores evaluated against separately protected
scenario truth,
So that categorical anomaly performance is reported without hiding capture
limitations or changing the detector.

**Acceptance Criteria:**

**Given** immutable score, bundle, threshold, partition, capture, metric-policy,
and truth identities
**When** the authorized evaluator unlocks truth
**Then** it joins truth to scores only through frozen experiment, run, workload,
window, event, and correlation identities
**And** no score, decision, vocabulary, preprocessing, threshold, partition, or
model artifact is modified.

**Given** the syscall evaluation applicability matrix
**When** outcomes are calculated
**Then** applicable point or window and event or range results include the
declared subset of PR-AUC, precision, recall, F1, false-positive behavior, false
events per operating hour, time to detection, suitable confusion data,
threshold sensitivity, resource cost, capture quality or availability, and
repeated-run dispersion or uncertainty
**And** inapplicable metrics are marked with their reason rather than fabricated.

**Given** workload activities, scenarios, repetitions, process scopes, kernel
or ABI contexts, capture modes, and quality states
**When** results are stratified
**Then** the report preserves each applicable declared stratum and its support
**And** aggregation cannot hide attribution failure, loss, aborted capture, an
unfavorable model result, or an unavailable window.

**Given** preregistered threshold-sensitivity alternatives
**When** sensitivity is evaluated
**Then** every planned alternative is reported against the same frozen scores
and truth
**And** none replaces the frozen primary threshold or score decisions.

**Given** fixture replay, external ADFA or LID data, and authentic custom
host-capture evidence coexist in the project
**When** custom evaluation inputs are selected
**Then** only qualified custom host-capture evidence enters this result
**And** fixtures and external benchmarks remain separately labelled and cannot
inflate locally measured custom outcomes.

**Given** all planned candidate, capture, and test runs
**When** the evaluation package is published
**Then** successful, failed, blocked, aborted, invalid, unavailable, and
unfavorable statuses retain metrics, dispersion, capture and resource evidence,
limitations, and immutable provenance
**And** no selected best seed or recurrent-model superiority claim replaces the
complete result set.

### Story 14.9: Correlate Custom Streams and Close Syscall Capture Gate G6

**FRs implemented:** FR27, FR72, FR79-FR81, FR85.

As an evidence owner,
I want authentic syscall segments correlated with their physical experiment
runs and capture qualification finalized,
So that later paired analysis can distinguish eligible joins from incomplete or
fabricated evidence.

**Acceptance Criteria:**

**Given** physical evidence from Epic 10 and syscall host-capture evidence from
the controlled workload
**When** their correlation record is assembled
**Then** it binds the same experiment and run identities plus edge, workload,
host or VM, boot, session, stream, source and observed time, clock quality and
uncertainty, segment, sequence, and manifest identities
**And** physical and syscall payloads remain in separate modality-specific
artifacts.

**Given** candidate physical and syscall intervals
**When** join eligibility is checked
**Then** clock, correlation, completeness, configuration, run-boundary, and
quality evidence yield an explicit eligible or ineligible outcome with reasons
**And** no timestamp, event, observation, or missing interval is fabricated to
force alignment.

**Given** the G6 capture evidence
**When** authenticity and quality validation runs
**Then** raw segment hashes, collector and filter, actual Linux kernel and ABI,
workload and process attribution, ordering, gaps, duplicates, drops, queue and
storage behavior, measured overhead, replay, and limitations are reconstructible
**And** all thresholds or acceptance limits resolve to admissible parameter
evidence.

**Given** Docker Desktop or another candidate boundary cannot satisfy the
declared capture policy
**When** G6 is decided
**Then** the pinned-Linux fallback evidence is evaluated or the formal capture
track remains explicitly blocked
**And** fixtures, fabricated calls, infrastructure-container calls, or external
dataset sequences cannot substitute for the controlled edge workload.

**Given** detector-facing custom stream artifacts
**When** truth-boundary validation runs
**Then** neither modality stream, window, bundle, nor score contains scenario
truth, labels, future intervals, or expected outcomes
**And** only a later authorized evaluator may join truth after applicable
artifacts are frozen.

**Given** all G6 checks complete
**When** the gate result is issued
**Then** passing requires real Linux kernel calls attributable to the declared
workload with inspectable capture quality and correlation readiness
**And** it neither assembles `PTFP-Custom-v1`, closes G8, performs fusion, nor
authorizes further capture, training, deployment, control, or UI work.

## Epic 15A: Reproduce ADFA-LD as an External Syscall Benchmark

The researcher can produce reproducible ADFA-LD anomaly results while
preserving official roles, trace identity, six attack families, categorical
semantics, archive and count evidence, and evaluation-only labels.

### Story 15A.1: Pin and Inventory the Official ADFA-LD Source

**FRs implemented:** FR24, FR28, FR82.

As a benchmark owner,
I want the exact ADFA-LD source and empirical inventory preserved,
So that every later result resolves to official external benchmark evidence.

**Acceptance Criteria:**

**Given** an ADFA-LD source candidate
**When** source qualification runs
**Then** it resolves to the official owner or distribution location and records
release identity where available, retrieval date, archive and extracted-byte
hashes, sizes, license or access notes, citation, and exact source locators
**And** mirrors remain distinguishable from the canonical official source.

**Given** the qualified local corpus
**When** empirical inventory runs
**Then** it records official directory or file roles, complete trace identities,
normal and attack trace counts, token counts, six attack-family mappings, empty
or malformed files, and archive-to-extracted lineage
**And** inventory values are measured from the exact local bytes rather than
copied from a publication.

**Given** official documentation, publications, mirrors, or local bytes disagree
on counts, names, roles, or attack-family membership
**When** the dataset card is finalized
**Then** every discrepancy and source locator remains visible
**And** the corpus is not silently repaired, merged, renamed, or trimmed to
match a preferred count.

**Given** the official source is unavailable, access-restricted beyond the
approved scope, corrupt, incomplete, or fails hash and inventory validation
**When** qualification completes
**Then** the ADFA-LD track receives an explicit blocked or unqualified status
with the reason
**And** fixtures, published metrics, mirrors of unknown identity, or custom
syscall evidence cannot substitute for official-real ADFA-LD data.

**Given** the ADFA-LD dataset card
**When** its scientific role is validated
**Then** it is labelled as an offline external syscall benchmark with official
roles and dataset-native limitations
**And** it is never represented as live capture, compressor evidence, physical
evidence, or fusion-eligible custom data.

**Given** source qualification and inventory pass
**When** the immutable source manifest is published
**Then** it binds official source, local bytes, hashes, roles, counts,
discrepancies, license or access evidence, tool, code, and runtime identities
**And** planning completion does not itself authorize acquisition, training, or
benchmark execution.

### Story 15A.2: Parse Categorical Traces and Isolate ADFA-LD Labels

**FRs implemented:** FR82.

As a benchmark adapter maintainer,
I want ADFA-LD traces parsed without changing their categorical or official
meaning,
So that detector inputs remain faithful to the source while labels stay
evaluation-only.

**Acceptance Criteria:**

**Given** the qualified ADFA-LD source manifest
**When** the version-specific adapter discovers files
**Then** each file resolves to its exact official role, trace identity, source
path and hash, and applicable attack-family identity
**And** unknown paths, duplicate trace identities, or unsupported layouts fail
explicitly rather than being coerced.

**Given** a valid ADFA-LD trace
**When** its syscall sequence is parsed
**Then** original token order and categorical identity are preserved with source
trace and position lineage
**And** tokens are neither executed nor translated into fabricated runtime
calls.

**Given** numeric syscall tokens
**When** the adapter represents them
**Then** they remain categorical values under the documented ADFA-LD vocabulary
context
**And** numeric distance, physical magnitude, or continuous regression meaning
is not inferred.

**Given** the source does not provide trustworthy event timestamps
**When** canonical trace records are created
**Then** sequence position is preserved as source ordering evidence
**And** wall-clock time, inter-event duration, capture rate, and synthetic
timestamps are not fabricated.

**Given** normal and attack trace metadata
**When** detector-facing and evaluator-facing artifacts are written
**Then** official role, attack-family labels, and evaluation truth remain in a
separate restricted artifact linked by opaque trace identity
**And** detector-facing sequences and filenames reveal no label or attack-family
semantics.

**Given** valid, empty, malformed, unknown-token, and unsupported-layout
fixtures derived from the official schema
**When** parsing and canonical serialization repeat
**Then** records, failures, ordering, trace identities, and hashes are
deterministic
**And** fixtures remain test-only under the cross-epic mock and fixture
guardrail.

### Story 15A.3: Build Trace-Safe ADFA-LD Partitions and Windows

**FRs implemented:** FR25-FR26, FR82, FR86.

As an evaluator,
I want official roles and complete ADFA-LD traces preserved before windowing,
So that related sequence content and fitted vocabulary cannot leak across
benchmark stages.

**Acceptance Criteria:**

**Given** the qualified trace inventory and official roles
**When** the benchmark partition record is frozen
**Then** official roles remain authoritative and every complete trace has one
explicit lifecycle assignment
**And** traces cannot be moved across official roles to improve a result.

**Given** an additional validation or calibration subdivision is required
inside an eligible official normal-data role
**When** it is declared
**Then** the method, complete-trace memberships, seed where applicable, purpose,
and evidence references are preregistered before fitting or test access
**And** attack traces and locked evaluation truth cannot guide the subdivision.

**Given** frozen partitions and categorical trace records
**When** sequences or windows are generated
**Then** no window crosses a trace, file, official role, partition, malformed or
excluded interval, schema, or source boundary
**And** length, stride, padding, and exclusion choices resolve to admissible
parameter evidence.

**Given** vocabulary, unknown-token mapping, frequency state, or preprocessing
requires fitting
**When** that state is learned
**Then** it uses only eligible normal training traces and records input traces,
mapping, parameters, code, runtime, and output hashes
**And** validation, calibration, locked test, attack labels, and future traces
remain inaccessible.

**Given** frozen preprocessing is applied outside training
**When** an unknown or incompatible token, schema, vocabulary, or trace role is
encountered
**Then** the declared unknown or failure policy is applied without extending or
refitting the vocabulary
**And** the affected trace or window remains explicitly accounted for.

**Given** prepared ADFA-LD windows
**When** lineage and leakage validation runs
**Then** each window resolves to archive, source file, trace, official role,
partition, vocabulary, preprocessing, positions, and exclusion evidence
**And** labels, attack families, fabricated timestamps, and cross-trace content
are absent from detector inputs.

### Story 15A.4: Compare ADFA-LD Categorical Detector Candidates

**FRs implemented:** FR24, FR81-FR82.

As an academic evaluator,
I want recurrent and transparent categorical candidates compared under one
ADFA-LD-native protocol,
So that benchmark conclusions are fair within the dataset and not borrowed from
the custom track.

**Acceptance Criteria:**

**Given** the ADFA-LD candidate plan
**When** it is frozen before fitting
**Then** it declares embedding-plus-LSTM, embedding-plus-GRU, and a transparent
n-gram or STIDE-style baseline with exact architecture and parameter identities
**And** no candidate is designated superior in advance.

**Given** the candidates
**When** fitting and validation selection run
**Then** they receive the same eligible ADFA-LD traces, partitions, categorical
schema, vocabulary and preprocessing inputs, tuning access, declared budget,
repetitions, and primary selection metrics
**And** model-specific exceptions are preregistered and reported.

**Given** a candidate requires fitted state
**When** it is trained
**Then** it uses only eligible official normal training evidence and exact frozen
preprocessing
**And** calibration, locked test, attack labels, attack-family truth, and future
traces remain inaccessible.

**Given** categorical ADFA-LD tokens and model objectives
**When** candidate configuration is validated
**Then** token identity remains categorical through explicit vocabulary or
sequence semantics
**And** numeric IDs are not executed, treated as continuous values, or optimized
with reconstruction MSE solely because they are numbers.

**Given** windows, model dimensions, hyperparameters, stopping rules, budgets,
or repetitions
**When** parameter validation runs
**Then** every executable numeric choice resolves to applicable ADFA-LD track
evidence or a frozen preregistered decision
**And** custom-capture, LID, HAI, or publication-example values do not migrate
silently.

**Given** candidate runs succeed, fail, abort, exceed budget, or produce
unfavorable validation results
**When** the comparison record is published
**Then** all planned configurations, seeds, inputs, outputs, statuses, resources,
diagnostics, and limitations remain visible
**And** the preregistered validation-only rule freezes one candidate for
calibration without test or truth access.

### Story 15A.5: Calibrate, Bundle, and Freeze Blind ADFA-LD Scores

**FRs implemented:** FR25, FR82, FR87.

As an evaluator,
I want the selected ADFA-LD candidate calibrated and scored as one immutable
benchmark path,
So that labels and held-out outcomes cannot change its vocabulary, model, or
threshold.

**Acceptance Criteria:**

**Given** the selected candidate and declared ADFA-LD calibration subdivision
**When** calibration scores and the threshold are produced
**Then** exact vocabulary, preprocessing, candidate, source, partition, method,
score direction, inputs, parameters, primary threshold, sensitivity alternatives,
and hashes are frozen
**And** locked test traces and evaluation labels remain inaccessible.

**Given** the calibrated candidate
**When** its `DetectorBundle.v1` is assembled
**Then** it binds ADFA-LD archive and inventory, official roles, split and trace
hashes, categorical schema, vocabulary, unknown policy, preprocessing, model
architecture and weights or state, calibration evidence, threshold, score
direction, code, dependencies, runtime, and component hashes
**And** the complete bundle receives one content-addressed identity.

**Given** the saved bundle
**When** load and inference-only validation run
**Then** every component, version, hash, trace role, vocabulary order, threshold,
and runtime identity verifies atomically
**And** load never fits, extends vocabulary, recalibrates, accesses labels, or
guesses a mutable `latest` artifact.

**Given** the locked eligible ADFA-LD evaluation traces
**When** blind scoring executes
**Then** `DetectorScore.v1` binds bundle, trace or window, source positions, raw
and calibrated score, direction, threshold, decision, missingness, status, code,
and runtime
**And** it contains no label, attack-family identity, fabricated timestamp,
future value, or custom-capture claim.

**Given** a trace or window is empty, malformed, unknown, incompatible, or
cannot be scored
**When** the score set is finalized
**Then** its invalid or unavailable status and diagnostic remain visible
**And** it is not silently removed, repaired, or represented as normal.

**Given** every planned locked trace is scored or explicitly accounted for
**When** the score manifest is published
**Then** bundle, threshold, score, invalid-input, resource, provenance, and hash
evidence is immutable before label unlock
**And** only that frozen score-manifest identity may enter ADFA-LD evaluation.

### Story 15A.6: Evaluate and Publish the ADFA-LD Benchmark Result

**FRs implemented:** FR24, FR26-FR28, FR82, FR88.

As a dissertation reader,
I want ADFA-LD results reported with dataset-native scope, families, provenance,
and limitations,
So that the external benchmark is reproducible without fabricated temporal or
runtime claims.

**Acceptance Criteria:**

**Given** immutable ADFA-LD scores, bundle, threshold, partitions, metric policy,
and restricted official labels
**When** the authorized evaluator unlocks labels
**Then** it joins them only through frozen trace and window identities
**And** no score, decision, vocabulary, preprocessing, threshold, partition, or
model artifact changes.

**Given** the ADFA-LD metric applicability matrix
**When** benchmark outcomes are calculated
**Then** applicable trace or window and event or range results include the
declared subset of PR-AUC, precision, recall, F1, false-positive behavior,
suitable confusion data, threshold sensitivity, resource cost, and repeated-run
dispersion or uncertainty
**And** unavailable metrics are marked with their dataset-specific reason.

**Given** ADFA-LD lacks trustworthy wall-clock event timestamps or operating
duration for a requested temporal metric
**When** time-to-detection, false-events-per-hour, or latency reporting is
considered
**Then** no timestamp, seconds-based duration, or hourly rate is fabricated
**And** a preregistered sequence-position measure, if applicable, remains
explicitly distinct from elapsed time.

**Given** official roles, complete traces, the six attack families, trace
lengths, repetitions, and unknown or malformed cases
**When** results are stratified
**Then** each applicable declared group and its support remain visible
**And** aggregation cannot hide a failed family, short or malformed trace,
unfavorable candidate, or unavailable result.

**Given** author-published ADFA-LD statistics or results
**When** they appear beside local execution outcomes
**Then** they remain labelled as published-reference evidence with exact source
locators
**And** they are never copied into the locally measured result role or used to
fill a missing local run.

**Given** source, adapter, partition, categorical semantics, leakage, bundle,
score, truth-unlock, metric, provenance, and reporting checks complete
**When** the ADFA-LD G7 component is decided
**Then** passing produces an immutable `ADFA_LD_BENCHMARK_QUALIFIED` result, while
failure produces its explicit blocked or unqualified record with all limitations
**And** neither outcome represents live capture, physical evidence, LID or HAI
results, custom detector validation, fusion evidence, deployment, or UI work.

## Epic 15B: Qualify and Evaluate LID-DS 2021 Independently

The researcher can qualify a separately authorized official LID-DS 2021 scope,
preserve its official schema and grouping, execute reproducible categorical
anomaly evaluation, or publish an honest blocked or not-executed record when the
official source or scope cannot qualify.

### Story 15B.1: Authorize the Exact LID-DS 2021 Scope or Record No Execution

**FRs implemented:** FR60, FR63, FR83.

As a research owner,
I want the intended LID-DS 2021 scope authorized before acquisition or adapter
work,
So that no scenario, recording, run count, or model budget becomes an implicit
benchmark requirement.

**Acceptance Criteria:**

**Given** a proposed LID-DS 2021 benchmark activity
**When** its activity-authorization record is prepared
**Then** it identifies the exact official version, source candidate, permitted
scenario and recording scope, file or group roles where known, acquisition and
license scope, allowed processing stages, run count, stopping rules, candidate
budget, owner, decision, and timestamp
**And** every executable numeric choice resolves to parameter evidence or a
preregistered decision.

**Given** no LID scenario or subset has been separately authorized
**When** the track is planned or invoked
**Then** no scenario, recording, subset, sample limit, or example configuration
is selected by default
**And** the track publishes an immutable `not_executed` record rather than
guessing scope.

**Given** fixture data, author-published examples, metrics, or documentation
describes a possible LID scope
**When** authorization is evaluated
**Then** those materials remain fixture or published-reference evidence
**And** they cannot grant permission, become official-real bytes, or define a
local measured run implicitly.

**Given** an authorization is rejected, incomplete, expired, or mismatched to a
requested activity
**When** source acquisition, parsing, fitting, calibration, or evaluation is
requested
**Then** only that activity is blocked with an explicit reason
**And** ADFA-LD, HAI, custom capture, and other independent tracks remain
unblocked.

**Given** an exact scope is approved
**When** later artifacts are created
**Then** every source, parser, partition, candidate, bundle, score, and result
references the immutable authorization identity
**And** any scope change requires a new authorization rather than modifying the
approved record.

### Story 15B.2: Qualify the Official LID Source and Isolated Environment

**FRs implemented:** FR59-FR60, FR83.

As a benchmark owner,
I want the authorized LID-DS 2021 source and compatible processing environment
verified,
So that local results resolve to official bytes and a reproducible versioned
boundary.

**Acceptance Criteria:**

**Given** an authorized LID-DS 2021 scope
**When** the source candidate is qualified
**Then** it resolves to the official owner or release location and records exact
version, retrieval date, citation, license or access terms, archive and
extracted-byte hashes, file inventory, sizes, and official scope locators
**And** mirrors remain distinguishable from the canonical official source.

**Given** the local authorized source bytes
**When** empirical inventory runs
**Then** discovered scenarios, recordings, official roles, schemas, files,
groups, and empty or malformed content are recorded without altering the source
**And** discrepancies with documentation or author examples remain explicit.

**Given** the release requires dependencies incompatible with the main
prototype runtime
**When** the LID processing boundary is prepared
**Then** its code, dependencies, container or equivalent environment, operating
system, runtime, parser, and source identities are pinned and isolated
**And** version conflict cannot trigger an implicit parser, schema, or dependency
substitution.

**Given** the source is missing, unauthorized, corrupt, empty, ambiguous,
unsupported, or outside the approved license or scenario scope
**When** qualification completes
**Then** the LID track receives an explicit blocked or unqualified record with
the exact reason
**And** fixtures, mocks, published statistics, custom capture, ADFA-LD, or a
different LID release cannot substitute for official-real bytes.

**Given** author documentation provides example durations, collector settings,
counts, metrics, or model configurations
**When** the source and environment manifest is finalized
**Then** those values remain published-reference evidence with exact locators
**And** none becomes a project runtime or experimental constant without its own
applicable parameter-evidence and authorization record.

**Given** source and environment qualification pass
**When** their immutable manifest is published
**Then** it binds authorization, official source, local bytes, hashes, inventory,
license, code, dependency, runtime, and limitation identities
**And** qualification alone does not authorize parsing beyond scope, training,
or benchmark execution.

### Story 15B.3: Parse the Authorized Official LID-DS 2021 Layout

**FRs implemented:** FR59, FR61, FR83.

As a benchmark adapter maintainer,
I want a version-specific adapter for the authorized official LID layout,
So that scenario, recording, process context, events, roles, and labels retain
their published meaning.

**Acceptance Criteria:**

**Given** the qualified source, environment, and authorization manifests
**When** the LID adapter discovers content
**Then** every accepted file and record resolves to its exact version, official
role, scenario, recording or group, source path and hash, and published schema
**And** content outside the authorized scope remains inventoried but is not
processed as an executed result.

**Given** a supported official record
**When** it is parsed
**Then** the adapter preserves the published syscall and event fields,
categorical identity, ordering and time fields where officially present,
process or context identity, and source lineage
**And** it does not coerce the record into ADFA-LD, custom capture, or physical
schemas.

**Given** official normal or attack metadata and labels
**When** detector-facing and evaluator-facing artifacts are written
**Then** labels, scenario outcomes, attack identity, and evaluation-only fields
remain in a separate restricted artifact linked by opaque official group and
record identities
**And** detector-facing fields, paths, and filenames reveal no label semantics.

**Given** an unknown version, schema, field type, role, scenario layout,
recording structure, empty group, duplicate identity, or malformed record
**When** parsing is attempted
**Then** the affected content fails explicitly with source and layout diagnostics
**And** no fixture, alternate release adapter, inferred field, or fabricated
event fills the gap.

**Given** valid and invalid fixtures derived from the official versioned schema
**When** parsing and canonical serialization repeat
**Then** records, failures, group identities, ordering, timestamps where present,
and hashes are deterministic
**And** fixtures remain test-only and cannot enter official-real LID results.

**Given** the authorized source parses successfully
**When** the adapter manifest is finalized
**Then** it binds source, authorization, official roles and groups, schema,
parser, environment, output, truth, discrepancy, and limitation identities
**And** parser success does not imply dataset qualification, fitting, or
evaluation authorization.

### Story 15B.4: Build Official-Group-Safe LID Partitions and Windows

**FRs implemented:** FR25, FR62, FR83, FR86.

As an evaluator,
I want LID-DS 2021 partitioned by official roles and complete native groups,
So that scenario and recording relationships cannot leak across benchmark
stages.

**Acceptance Criteria:**

**Given** parsed content within the authorized scope
**When** the LID partition record is frozen
**Then** official training, validation, and test roles remain authoritative and
complete applicable scenario, recording, trace, session, and process groups are
assigned before vocabulary fitting or windowing
**And** one group cannot cross lifecycle roles or partitions.

**Given** an additional calibration subdivision is required within an eligible
official role
**When** it is declared
**Then** complete-group membership, method, seed where applicable, purpose,
source, and authorization are preregistered
**And** locked test labels or outcomes cannot guide the subdivision.

**Given** frozen partitions and categorical LID records
**When** windows are generated
**Then** no window crosses an official role, scenario, recording, trace, session,
process, gap, schema, file, source, or partition boundary
**And** window, padding, stride, exclusion, and timing choices resolve to
applicable parameter evidence.

**Given** vocabulary, embedding indices, frequency state, or preprocessing
requires fitting
**When** it is learned
**Then** it uses only eligible official normal training groups and records exact
groups, schema, mapping, unknown policy, parameters, code, environment, and
output hashes
**And** validation, calibration, test, labels, and future records remain
inaccessible.

**Given** frozen preprocessing is applied outside training
**When** unknown categories, schema drift, group mismatch, or unsupported
records are encountered
**Then** the declared unknown or failure policy applies without refitting or
implicit layout conversion
**And** every affected group and window remains explicitly accounted for.

**Given** prepared LID windows
**When** lineage, scope, and leakage validation runs
**Then** every window resolves to authorization, source, official role,
scenario, recording, group, record range, partition, vocabulary, preprocessing,
and exclusion identities
**And** labels, fixture-only content, unauthorized scenarios, and cross-group
records are absent from detector inputs.

### Story 15B.5: Compare Authorized LID Categorical Detector Candidates

**FRs implemented:** FR24, FR63, FR81, FR83.

As an academic evaluator,
I want categorical sequence candidates compared under the exact authorized
LID-native protocol,
So that locally measured results do not exceed the qualified source or scope.

**Acceptance Criteria:**

**Given** the authorized LID candidate plan
**When** it is frozen before fitting
**Then** it declares embedding-plus-LSTM, embedding-plus-GRU, and a transparent
n-gram or STIDE-style baseline with exact architecture, source, scope, and
parameter identities
**And** no candidate or scenario is designated superior or mandatory in advance.

**Given** the candidate set
**When** fitting and validation selection run
**Then** candidates receive the same eligible official groups, partitions,
published categorical schema, vocabulary and preprocessing inputs, tuning
access, authorized budget, repetitions, and primary metrics
**And** model-specific exceptions are preregistered and reported.

**Given** a candidate requires fitted state
**When** it is trained
**Then** it uses only eligible official normal training groups within the
authorized scope and exact frozen preprocessing
**And** calibration, locked test, labels, scenario outcomes, author metrics, and
future records remain inaccessible.

**Given** categorical syscall fields or numeric identifiers in the published
schema
**When** the model objective is configured
**Then** the adapter's official categorical semantics and kernel or ABI context
where supplied remain binding
**And** identifiers are not treated as continuous measurements solely because
they are numeric.

**Given** windows, model dimensions, hyperparameters, stopping rules, run count,
resource budget, or repetitions
**When** parameter and authorization validation runs
**Then** every choice resolves to applicable LID track evidence and the exact
authorized scope
**And** author examples, ADFA-LD, custom capture, or another LID scenario do not
migrate silently.

**Given** candidate runs succeed, fail, block, abort, exceed budget, or produce
unfavorable validation outcomes
**When** the comparison record is published
**Then** all planned configurations, groups, seeds, inputs, outputs, statuses,
resources, diagnostics, and limitations remain visible
**And** the preregistered validation-only rule freezes one candidate for
calibration without test or truth access.

### Story 15B.6: Calibrate, Bundle, and Freeze Blind LID Scores

**FRs implemented:** FR25, FR63, FR83, FR87.

As an evaluator,
I want the selected LID candidate calibrated and scored as one immutable
authorized benchmark path,
So that held-out labels and outcomes cannot change its schema, model, or
threshold.

**Acceptance Criteria:**

**Given** the selected candidate and authorized LID calibration groups
**When** calibration scores and threshold are produced
**Then** exact source, scope, roles, groups, schema, vocabulary, preprocessing,
candidate, method, score direction, inputs, parameters, primary threshold,
sensitivity alternatives, and hashes are frozen
**And** locked test groups and evaluation labels remain inaccessible.

**Given** the calibrated candidate
**When** its `DetectorBundle.v1` is assembled
**Then** it binds authorization, official source and version, file and group
hashes, roles and partitions, categorical schema, vocabulary, unknown policy,
preprocessing, model architecture and weights or state, calibration evidence,
threshold, score direction, code, dependencies, isolated runtime, and component
hashes
**And** the complete bundle receives one content-addressed identity.

**Given** the saved bundle
**When** load and inference-only validation run
**Then** every component, version, hash, official role, group scope, categorical
order, threshold, and runtime identity verifies atomically
**And** load never fits, extends vocabulary, recalibrates, accesses labels,
switches scenarios, or guesses a mutable artifact.

**Given** locked eligible LID test groups within the authorized scope
**When** blind scoring executes
**Then** `DetectorScore.v1` binds bundle, group, record or window, source
positions or official time where present, raw and calibrated score, direction,
threshold, decision, missingness, status, code, and runtime
**And** it contains no label, scenario outcome, attack identity, unauthorized
record, fixture claim, or published metric.

**Given** a group or window is empty, malformed, unknown, incompatible,
unauthorized, or cannot be scored
**When** the score set is finalized
**Then** its invalid, unavailable, blocked, or out-of-scope status and diagnostics
remain visible
**And** it is not silently removed, repaired, replaced by a fixture, or
represented as normal.

**Given** every planned authorized test group is scored or explicitly accounted
for
**When** the score manifest is published
**Then** authorization, bundle, threshold, score, invalid-input, resource,
provenance, environment, and hash evidence is immutable before label unlock
**And** only that frozen score-manifest identity may enter local LID evaluation.

### Story 15B.7: Publish the LID Result or Honest Blocked State

**FRs implemented:** FR24, FR26-FR28, FR59-FR64, FR83, FR88.

As a dissertation reader,
I want the LID-DS 2021 track reported whether it executes or remains blocked,
So that unavailable official evidence or authorization is not hidden behind
fixtures or published statistics.

**Acceptance Criteria:**

**Given** exact scope authorization, official source qualification, or adapter
qualification is absent or failed
**When** the LID result is requested
**Then** an immutable `not_executed`, `blocked`, or `unqualified` record identifies
the failed prerequisite, attempted scope, available evidence, and limitation
**And** no local model metric, score, official-real claim, or successful run is
fabricated.

**Given** immutable authorized LID scores, bundle, threshold, partitions, metric
policy, and restricted official labels
**When** the evaluator unlocks labels
**Then** it joins them only through frozen official group, record, and window
identities
**And** no source, scope, score, decision, vocabulary, preprocessing, threshold,
partition, or model artifact changes.

**Given** the LID metric applicability matrix
**When** local outcomes are calculated
**Then** applicable point or window and event or range results include the
declared subset of PR-AUC, precision, recall, F1, false-positive behavior, false
events per operating hour, time to detection, suitable confusion data,
threshold sensitivity, resource cost, and repeated-run dispersion or
uncertainty when supported by official data semantics
**And** unavailable metrics are marked with their dataset-specific reason rather
than inferred from author examples.

**Given** official roles, scenarios, recordings, groups, repetitions, categorical
contexts, and invalid or unavailable cases within the authorized scope
**When** results are stratified
**Then** each applicable declared group and its support remain visible
**And** aggregation cannot hide a failed scenario, excluded recording, blocked
run, unfavorable candidate, or unavailable result.

**Given** author-published LID metrics, examples, or reference results
**When** they appear beside local outcomes
**Then** they remain labelled published-reference evidence with exact source
locators
**And** they stay outside fitting, calibration, selection, thresholding, and
local measured-result calculations.

**Given** the LID track completes in any allowed state
**When** its G7 component record is published
**Then** passing execution produces `LID_DS_2021_BENCHMARK_QUALIFIED`, while
non-execution or failure retains its honest status, provenance, outcomes, and
limitations
**And** no LID state blocks ADFA-LD, HAI, custom capture, later evidence packaging,
or optional presentation, nor does it claim live capture, physical evidence,
fusion, deployment, or control authority.

## Epic 16: Evaluate HAI 23.05 in Its Native Physical Domain

The researcher can pin, qualify, process, train, calibrate, and evaluate HAI
23.05 while preserving native tags, units, chronology, official roles, labels,
and dataset-specific limitations.

### Story 16.1: Pin and Qualify the Official HAI 23.05 Source

**FRs implemented:** FR55-FR56, FR84.

As a benchmark owner,
I want the exact official HAI 23.05 source and inventory preserved,
So that every result resolves to the intended external physical and SCADA
benchmark version.

**Acceptance Criteria:**

**Given** a HAI source candidate
**When** source qualification runs
**Then** it resolves to the official repository and HAI 23.05 version, release,
tag, or commit identity and records retrieval date, citation, license or access
terms, official file roles, archive or repository state, local file sizes, and
content hashes
**And** mirrors remain distinguishable from the canonical official source.

**Given** the qualified local HAI 23.05 bytes
**When** empirical inventory runs
**Then** files, official roles, row counts, time coverage, tag and label files,
schemas, empty or malformed content, and source-to-local lineage are recorded
**And** measured inventory remains distinct from documentation or publication
claims.

**Given** HAI 20.07, another HAI release, a mirror, or a locally modified copy
is presented
**When** version validation runs
**Then** it is rejected from the HAI 23.05 track or registered under a distinct
non-target identity
**And** no compatibility assumption silently treats it as HAI 23.05.

**Given** official documentation, publications, repository metadata, and local
bytes disagree
**When** the dataset card is finalized
**Then** each discrepancy, exact locator, affected file or role, and limitation
remains visible
**And** source bytes are not silently repaired or trimmed to match a preferred
count.

**Given** official HAI 23.05 is missing, inaccessible, corrupt, incomplete,
unverified, or outside authorized license scope
**When** source qualification completes
**Then** the track receives an explicit blocked or unqualified status with its
reason
**And** mocks, custom physical rows, HAI 20.07, fixtures, or published metrics
cannot substitute for official-real HAI 23.05 evidence.

**Given** the source manifest is published
**When** its scientific role is validated
**Then** HAI 23.05 is labelled as external native physical and SCADA benchmark
evidence for a different process
**And** it is not represented as compressor data, custom testbed evidence,
current-loop evidence by default, or fusion-eligible data.

### Story 16.2: Implement the Version-Specific HAI 23.05 Adapter

**FRs implemented:** FR56-FR57, FR84.

As a benchmark adapter maintainer,
I want HAI 23.05 parsed with its native schema and isolated labels,
So that features and evaluation truth remain aligned without changing the
dataset's physical meaning.

**Acceptance Criteria:**

**Given** the qualified HAI 23.05 source manifest
**When** the adapter discovers files
**Then** each accepted file resolves to its exact official role, source path and
hash, version-specific schema, time coverage, and applicable tag or label
relationships
**And** an unknown release, role, or layout fails explicitly.

**Given** a supported HAI data file
**When** native observations are parsed
**Then** timestamps, chronology, tag names, values, data types, native units and
metadata where supplied, file role, row identity, and source lineage are
preserved
**And** tags are not renamed or coerced into compressor sensor identities.

**Given** official HAI label data
**When** its relationship to observation rows or intervals is validated
**Then** the adapter applies only the documented version-specific alignment rule
and records its source, parameters, discrepancies, and output hash
**And** labels, attacks, future intervals, and outcome fields are stored as
separate restricted truth linked by opaque identities.

**Given** a tag lacks official current-loop semantics
**When** physical representation is assigned
**Then** its native representation and unit remain authoritative
**And** it is not converted to mA or bound to a custom `InstrumentProfile.v1`
without separately applicable official documentation and the cross-epic mock
guardrail.

**Given** duplicate timestamps, chronology breaks, missing fields, schema drift,
unknown tags, invalid types, label misalignment, or unsupported files
**When** parsing runs
**Then** the affected records or files receive explicit diagnostics and status
**And** no inferred value, label, timestamp, alternate adapter, or custom row is
substituted.

**Given** valid and invalid fixtures derived from the official HAI 23.05 schema
**When** parsing and canonical serialization repeat
**Then** records, failures, chronology, identities, label joins, and hashes are
deterministic
**And** fixtures remain test-only and cannot enter official-real HAI results.

### Story 16.3: Build Native HAI Partitions, Preprocessing, and Windows

**FRs implemented:** FR25, FR56-FR57, FR84, FR86.

As a model developer,
I want HAI 23.05 prepared through its native roles, tags, units, and chronology,
So that detector inputs remain leakage-safe without inventing transmitter
semantics.

**Acceptance Criteria:**

**Given** parsed HAI 23.05 files and official roles
**When** the partition record is frozen
**Then** complete official files and applicable independent chronological groups
are assigned to their dataset-native lifecycle roles before preprocessing fit
or windowing
**And** one group cannot cross training, validation, calibration, or locked-test
roles.

**Given** an additional validation or calibration subdivision is required
inside an eligible official normal-data role
**When** it is declared
**Then** complete-group membership, chronological policy, purpose, seed where
applicable, source, and parameter evidence are preregistered
**And** locked test labels or outcomes cannot guide the subdivision.

**Given** frozen partitions and native HAI observations
**When** windows are generated
**Then** no window crosses an official role, file, chronological discontinuity,
invalid interval, schema change, tag-set change, group, or partition boundary
**And** window, stride, padding, continuity, and exclusion choices resolve to
applicable parameter evidence.

**Given** scaling, imputation, feature selection, or other preprocessing
requires fitted state
**When** it is learned
**Then** it uses only eligible normal training evidence and records exact files,
groups, tags, native units, missingness policy, parameters, code, runtime, and
output hashes
**And** validation, calibration, test, labels, and future rows remain
inaccessible.

**Given** frozen preprocessing is applied outside training
**When** tag, unit, order, schema, chronology, or missingness incompatibility is
encountered
**Then** the declared failure or missingness policy applies without refitting or
silent tag coercion
**And** each transformed feature remains traceable to its native tag, unit,
source group, and transformation.

**Given** prepared HAI windows
**When** lineage and leakage validation runs
**Then** every window resolves to source, official role, file, row and time
range, partition, native tags and units, preprocessing, quality, and exclusions
**And** labels, attack intervals, custom rows, mA assumptions, and cross-boundary
content are absent from detector inputs.

### Story 16.4: Compare HAI Physical Detector Candidates Fairly

**FRs implemented:** FR24, FR57, FR78, FR84.

As an academic evaluator,
I want LSTM-AE, GRU-AE, and declared simpler baselines compared under one
HAI-native protocol,
So that external physical benchmark conclusions follow equal preparation rather
than compressor assumptions.

**Acceptance Criteria:**

**Given** the HAI candidate plan
**When** it is frozen before fitting
**Then** it declares LSTM-AE, GRU-AE, and at least one simpler or classical
baseline with exact architecture, source, schema, and parameter identities
**And** no candidate is designated superior in advance.

**Given** the candidate set
**When** fitting and validation selection run
**Then** candidates receive the same eligible HAI files and groups, partitions,
native tag feature schema, preprocessing inputs, tuning access, declared budget,
repetitions, and primary metrics
**And** model-specific exceptions are preregistered and reported.

**Given** a candidate requires fitted state
**When** it is trained
**Then** it uses only eligible normal HAI training evidence and exact frozen
preprocessing
**And** calibration, locked test, labels, attack intervals, future rows, and
custom data remain inaccessible.

**Given** model dimensions, windows, hyperparameters, stopping rules, resource
budgets, repetitions, or targets
**When** parameter validation runs
**Then** every executable numeric choice resolves to applicable HAI track
evidence or a frozen preregistered decision
**And** compressor, ADFA-LD, LID, custom-capture, or publication-example values
do not migrate silently.

**Given** a compressor-trained model, physical bundle, feature schema, threshold,
or profile
**When** it is presented to the HAI candidate path
**Then** compatibility validation rejects it unless a separately versioned
HAI-native artifact was fitted under this protocol
**And** no wholesale mA conversion or implicit adapter makes it compatible.

**Given** candidate runs succeed, fail, abort, exceed budget, or produce
unfavorable validation outcomes
**When** the comparison record is published
**Then** all planned configurations, seeds, inputs, outputs, statuses, resources,
quality evidence, diagnostics, and limitations remain visible
**And** the preregistered validation-only rule freezes one candidate for
calibration without test or truth access.

### Story 16.5: Calibrate, Bundle, and Freeze Blind HAI Scores

**FRs implemented:** FR25, FR57, FR84, FR87.

As an evaluator,
I want the selected HAI candidate calibrated and scored through one immutable
dataset-specific path,
So that held-out labels and temporal outcomes cannot change its preprocessing,
model, or threshold.

**Acceptance Criteria:**

**Given** the selected candidate and declared HAI calibration groups
**When** calibration scores and threshold are produced
**Then** exact source, roles, groups, native feature schema, preprocessing,
candidate, method, score direction, inputs, parameters, primary threshold,
sensitivity alternatives, and hashes are frozen
**And** locked test evidence and evaluation labels remain inaccessible.

**Given** the calibrated candidate
**When** its `DetectorBundle.v1` is assembled
**Then** it binds HAI 23.05 source, files and roles, partition and group hashes,
native ordered tags and units, preprocessing and missingness policy, model
architecture and weights or state, calibration evidence, threshold, score
direction, code, dependencies, runtime, and component hashes
**And** the complete HAI-specific bundle receives one content-addressed identity.

**Given** the saved bundle
**When** load and inference-only validation run
**Then** every component, version, hash, file role, tag and unit order,
preprocessing, threshold, and runtime identity verifies atomically
**And** load never fits, recalibrates, accesses labels, changes tag semantics, or
guesses a mutable artifact.

**Given** locked eligible HAI test windows
**When** blind scoring executes
**Then** `DetectorScore.v1` binds bundle, file, group, window and time identities,
raw and calibrated score, direction, threshold, decision, missingness, quality,
latency, code, and runtime
**And** it contains no label, attack interval, expected outcome, compressor
identity, custom-data claim, or fusion field.

**Given** a window is discontinuous, missing, malformed, incompatible,
out-of-scope, or cannot be scored
**When** the score set is finalized
**Then** its invalid or unavailable status and diagnostic remain visible
**And** it is not silently repaired, removed, converted to mA, or represented as
normal.

**Given** every planned locked test window is scored or explicitly accounted for
**When** the score manifest is published
**Then** bundle, threshold, score, invalid-input, quality, resource, provenance,
and hash evidence is immutable before label unlock
**And** only that frozen score-manifest identity may enter HAI evaluation.

### Story 16.6: Evaluate HAI Point, Window, and Temporal Event Outcomes

**FRs implemented:** FR27, FR56-FR58, FR84, FR88.

As a dissertation reader,
I want frozen HAI scores evaluated with dataset-appropriate point and temporal
metrics,
So that anomaly timing and detection quality are visible without changing the
detector.

**Acceptance Criteria:**

**Given** immutable HAI scores, bundle, threshold, partitions, metric policy, and
restricted official labels
**When** the authorized evaluator unlocks labels
**Then** it joins them only through frozen file, group, row, time, window, and
event identities
**And** no source, score, decision, preprocessing, threshold, partition, or model
artifact changes.

**Given** the HAI metric applicability matrix
**When** outcomes are calculated
**Then** applicable point or window and event or range results include the
declared subset of PR-AUC, precision, recall, F1, false-positive behavior, false
events per operating hour, time to detection, suitable confusion data,
threshold sensitivity, resource cost, data quality or availability, and
repeated-run dispersion or uncertainty
**And** unavailable metrics are marked with their HAI-specific reason.

**Given** an official or separately preregistered HAI temporal event protocol
**When** point or window decisions are mapped to events
**Then** metric version, source locator, event construction, overlap and merge
policy, time unit, parameters, input identities, and output hash are recorded
**And** no undocumented grace period, duration, or detection rule is invented.

**Given** official roles, files, attack or anomaly intervals, tag groups,
operating periods, repetitions, discontinuities, and quality states
**When** results are stratified
**Then** every applicable declared group and its support remain visible
**And** aggregation cannot hide a missed event, false event, chronology break,
unfavorable candidate, invalid window, or unavailable result.

**Given** preregistered threshold-sensitivity alternatives
**When** sensitivity is evaluated
**Then** all planned alternatives and temporal outcomes are reported against the
same frozen scores and truth
**And** none replaces the frozen primary threshold or score decisions.

**Given** all planned candidate and test runs
**When** the HAI evaluation result is published
**Then** successful, failed, aborted, invalid, unavailable, and unfavorable
statuses retain metrics, uncertainty, quality, resource evidence, limitations,
and immutable provenance
**And** no selected best seed, model superiority, compressor validation, or
custom-fusion claim replaces the complete result set.

### Story 16.7: Publish the HAI Dataset Card, Result, and G7 Component

**FRs implemented:** FR24, FR26-FR28, FR55-FR58, FR84, FR88.

As an academic reviewer,
I want HAI 23.05 provenance, native semantics, results, and limitations published
together,
So that the benchmark cannot be misrepresented as compressor or custom-fusion
validation.

**Acceptance Criteria:**

**Given** completed HAI source, adapter, partition, candidate, bundle, score,
truth-unlock, and evaluation artifacts
**When** the result package is assembled
**Then** it resolves to official source and version, files and roles, hashes,
native tags and units, chronology, partitions, preprocessing, candidates,
bundle, threshold, scores, metric versions, outcomes, resources, and limitations
**And** reconstruction requires no UI or mutable hidden state.

**Given** author-published HAI statistics, metrics, or reference results
**When** they appear beside local outcomes
**Then** they remain labelled published-reference evidence with exact source
locators
**And** they are not copied into fitting, calibration, selection, thresholding,
or locally measured result fields.

**Given** local custom physical rows, ADFA-LD, LID, or captured syscall evidence
**When** HAI result inputs are validated
**Then** none is inserted, appended, aligned, or represented as part of HAI
23.05
**And** the HAI table remains independently dataset-native.

**Given** HAI tags and results
**When** scientific claims and limitations are written
**Then** the report explicitly preserves their native representation and
different-process scope
**And** it rejects wholesale mA conversion, compressor detector promotion,
real-plant claims beyond the dataset, and cross-dataset fusion.

**Given** source, adapter, native semantics, leakage, bundle, score, temporal
evaluation, provenance, and reporting checks complete
**When** the HAI G7 component is decided
**Then** passing produces `HAI_23_05_BENCHMARK_QUALIFIED`, while failure produces
its explicit blocked or unqualified record with all outcomes and limitations
**And** the record does not overwrite the independent ADFA-LD or LID component
status.

**Given** the HAI result package is finalized
**When** it is consumed by later evidence packaging or optional presentation
**Then** only immutable published artifacts and dataset-specific limitations may
be projected
**And** publication authorizes no retraining, fusion, deployment, control action,
or dashboard implementation.

## Epic 17A: Produce Synchronized Custom Evidence and Frozen Fusion Results

The researcher can produce immutable `PTFP-Custom-v1` runs containing aligned
physical observations and authentic edge syscalls, execute the preregistered
long-run campaign, freeze detector scores before truth unlock, and compare
physical-only, syscall-only, and simple late-fusion outcomes on the same runs.

### Story 17A.1: Preregister the Synchronized Custom Campaign

**FRs implemented:** FR34-FR38, FR75-FR77, FR85-FR86, FR89.

As a research owner,
I want every custom campaign and fusion decision frozen before execution,
So that the final paired result cannot be redesigned after observing evidence or
truth.

**Acceptance Criteria:**

**Given** a proposed `PTFP-Custom-v1` campaign
**When** its preregistration record is created
**Then** it binds exact experiment and run plan, physical and workload profiles,
applicable mock-admission records, parameter set, schedules, scenarios,
interventions, recovery, durations, repetitions, expected streams, clock and
correlation policy, partitions, windows, stopping and abort rules, metric
policy, truth-unlock rule, and code and runtime identities
**And** unavailable or inapplicable components are explicit.

**Given** physical and syscall detector use is planned
**When** campaign configuration is frozen
**Then** it identifies exact immutable bundle, schema or vocabulary,
preprocessing, calibration, threshold, score direction, compatibility, and
runtime identities for both modalities
**And** neither bundle may be selected or changed using campaign test truth.

**Given** late fusion is planned
**When** the fusion policy is preregistered
**Then** it declares the simple policy, calibrated score interpretation, window
alignment, availability and missing-modality rules, required quality, output
decision semantics, and every parameter identity before execution
**And** learned or test-fitted weights are outside this campaign unless a
separate supervised experiment is later authorized.

**Given** a campaign numeric value for schedule, duration, repetition, window,
clock tolerance, capture quality, alignment, detector threshold, fusion, metric,
or stopping policy
**When** parameter validation runs
**Then** it resolves to applicable direct, derived, measured, preregistered, or
properly admitted mock evidence
**And** no architecture, tool example, external benchmark, or desired outcome
supplies an anonymous value.

**Given** valid, invalid, aborted, incomplete, unfavorable, and recovery runs
are possible
**When** the run matrix is frozen
**Then** every planned condition and reporting treatment is explicit
**And** only successful or favorable runs cannot define the final campaign
after execution.

**Given** preregistration validation passes
**When** the record is published
**Then** all identities, decisions, parameters, limitations, owners, and hashes
are immutable and human- and machine-readable
**And** preregistration does not authorize campaign execution, capture,
training, fusion, activation, deployment, control changes, or UI work.

### Story 17A.2: Verify and Authorize Campaign Readiness

**FRs implemented:** FR26, FR28, FR40, FR53, FR76, FR85-FR87.

As a campaign operator,
I want every required physical, syscall, storage, timing, and detector dependency
verified before a formal run starts,
So that synchronized evidence cannot rely on silent fallbacks or mixed
configurations.

**Acceptance Criteria:**

**Given** a frozen campaign preregistration
**When** readiness validation runs
**Then** G1 provenance, G2 physical signal, G5 physical bundle, G6 authentic
syscall capture, persistent evidence storage, profile, parameter, workload,
collector, clock, correlation, schema, topic, and runtime identities resolve
exactly
**And** each prerequisite references its immutable passing evidence.

**Given** consensus or independent OPC evidence is included by the declared
campaign protocol
**When** readiness is evaluated
**Then** the applicable G3 or G4 evidence and exact versioned identities are
required
**And** an undeclared consensus or OPC dependency is neither required nor added
implicitly.

**Given** any physical simulator or controlled workload behavior is mocked
**When** readiness validation reaches it
**Then** the exact approved mock-admission and official-documentation records
required by the cross-epic guardrail remain valid for the campaign scope
**And** syscall events themselves must still be authentic captured Linux kernel
calls.

**Given** the proposed campaign execution activity
**When** authorization is checked
**Then** an approved activity record matches the exact preregistration, run
matrix, profiles, mock admissions, capture boundary, bundles, thresholds,
fusion policy, code, runtime, and evidence-storage identities
**And** planning approval or authorization for another run cannot start the
campaign.

**Given** a required identity is missing, stale, unverified, blocked,
incompatible, or changed after freeze
**When** campaign startup is requested
**Then** startup fails closed with the exact prerequisite and run scope
**And** no v1 route, fixture, external dataset, latest bundle, simulated syscall,
or reduced successful configuration is substituted.

**Given** all required readiness checks pass
**When** the readiness manifest is published
**Then** it records the exact campaign-ready identities, checks, outcomes,
limitations, and authorization without executing a run
**And** a later identity change invalidates readiness and requires a new check.

### Story 17A.3: Execute and Preserve Synchronized Custom Runs

**FRs implemented:** FR18, FR35, FR38, FR40-FR41, FR79, FR85.

As a campaign operator,
I want each authorized run to preserve physical and authentic syscall streams
from the same controlled experiment,
So that later paired analysis has real correlated evidence rather than aligned
surrogates.

**Acceptance Criteria:**

**Given** an exact passing readiness manifest and matching activity authorization
**When** a campaign run starts
**Then** all preregistered profile, parameter, mock-admission, workload, capture,
bundle, storage, code, runtime, clock, and correlation identities are reverified
**And** any mismatch prevents the run from entering formal campaign status.

**Given** an authorized run is active
**When** the declared schedule and workload advance
**Then** the physical branch preserves primary raw-current
`SignalObservation.v2` evidence while the identified Linux workload emits and
the qualified collector captures its actual kernel calls
**And** both branches share immutable experiment and run correlation without
sharing modality payloads.

**Given** consensus or OPC streams are included in the preregistered protocol
**When** those producers operate
**Then** they use their exact qualified versioned boundaries and correlation
identities
**And** absence or invalidity follows the campaign's declared policy without
substitution between OPC, consensus, physical, or syscall evidence.

**Given** source and observed timestamps, sequences, clocks, gaps, duplicates,
drops, queue pressure, storage lag, capture overhead, or quality changes occur
**When** stream evidence is written
**Then** each modality preserves its own timing, ordering, quality, and affected
interval diagnostics
**And** no missing physical observation, syscall, timestamp, or status is
fabricated.

**Given** a run completes, fails, aborts, recovers, becomes incomplete, or
produces an unfavorable outcome
**When** it is closed
**Then** its actual status, all available modality artifacts, control and
workload trace, quality, resource evidence, and limitations remain immutable
**And** failed evidence collection cannot change or create compressor commands.

**Given** all available run objects have been written
**When** publication is attempted
**Then** physical, syscall, optional consensus and OPC, control, workload,
restricted truth, and diagnostic objects remain role-separated and are verified
before the complete run manifest is published last
**And** partial publication cannot appear as a complete synchronized run.

### Story 17A.4: Assemble and Qualify `PTFP-Custom-v1`

**FRs implemented:** FR18, FR25-FR26, FR28, FR37, FR39-FR41, FR72, FR85-FR86.

As an evidence owner,
I want complete synchronized runs assembled into an immutable custom dataset,
So that paired detector conditions use only authentic same-run evidence with
isolated truth.

**Acceptance Criteria:**

**Given** finalized campaign run manifests
**When** `PTFP-Custom-v1` admission runs
**Then** each candidate run must contain compatible physical observations and
authentic workload-attributed Linux syscall segments from the same experiment
and run with resolvable clock, correlation, configuration, completeness, and
quality evidence
**And** external ADFA-LD, LID, HAI, fixture, or fabricated records are rejected.

**Given** an admitted custom run
**When** its dataset manifest entry is created
**Then** it binds physical and syscall stream manifests, workload and control
trace, profiles and parameters, mock admissions, capture and runtime identity,
clock and correlation evidence, modality quality, optional declared consensus
and OPC evidence, and a separate restricted-truth reference
**And** modality-specific source artifacts remain distinct.

**Given** complete custom runs
**When** the `PTFP-Custom-v1` partition is frozen
**Then** whole independent runs are assigned before physical or syscall windows
are generated to the applicable lifecycle roles
**And** no run or derived window can cross a partition, run, scenario, gap,
schema, configuration, clock-policy, or modality-quality boundary.

**Given** physical and syscall windows are proposed as a pair
**When** alignment validation runs
**Then** both resolve to the same held-out run and declared alignment interval,
clock policy, quality policy, configuration, and immutable source ranges
**And** missing, duplicated, mis-correlated, mixed, or boundary-crossing windows
receive an explicit ineligible reason rather than forced alignment.

**Given** detector-facing dataset artifacts
**When** truth-boundary validation runs
**Then** observations, syscall events, features, windows, partitions, and future
score inputs contain no truth, labels, scenario meaning, intervention meaning,
or expected outcomes
**And** truth remains locked under the preregistered evaluator-only rule.

**Given** synchronized-stream, leakage, capture-authenticity, clock,
correlation, modality-quality, storage, completeness, provenance, mock-admission,
and truth-isolation checks complete
**When** G8 is decided
**Then** only passing evidence receives immutable `DATASET_QUALIFIED` and
`PTFP_CUSTOM_V1_QUALIFIED` identities, while every invalid, incomplete, or
aborted run remains preserved with its reason
**And** passing G8 neither executes detector scoring or fusion nor authorizes
training, truth unlock, deployment, control, or UI work.

### Story 17A.5: Freeze Paired Physical and Syscall Scores Before Truth

**FRs implemented:** FR21, FR25, FR29, FR49-FR51, FR54, FR71, FR77, FR87, FR89.

As an evaluator,
I want exact physical and syscall bundles to score the same held-out custom runs
before truth unlock,
So that paired comparison and fusion cannot alter either detector after seeing
outcomes.

**Acceptance Criteria:**

**Given** G8-qualified held-out custom runs, exact frozen physical and syscall
bundles, and matching activity authorization
**When** blind inference begins
**Then** both bundle, threshold, schema or vocabulary, preprocessing, partition,
runtime, input, and compatibility identities verify before scoring
**And** either detector remains inference-only with no fitting, tuning,
recalibration, truth access, or fallback bundle.

**Given** eligible modality-specific windows
**When** physical and syscall inference execute
**Then** each produces its own immutable `DetectorScore.v1` with bundle, source
window, calibrated score, direction, threshold, decision, quality or
missingness, latency, run correlation, code, and runtime identity
**And** scores contain no truth, label, scenario meaning, expected outcome, or
fusion decision.

**Given** physical and syscall score records are proposed as paired inputs
**When** pair validation runs
**Then** they resolve to the same qualified held-out run and declared aligned
window under the frozen clock, availability, quality, and configuration policy
**And** raw losses, incompatible calibration scales, source features, or
external benchmark scores are not compared or combined directly.

**Given** one modality is invalid, unavailable, missing, low quality, or cannot
score an aligned window
**When** paired score accounting runs
**Then** both the available score and missing-modality state remain visible with
the declared eligibility or exclusion reason
**And** no score, event, or normal decision is fabricated for the absent
modality.

**Given** identical qualified inputs and declared runtimes
**When** modality scoring is repeated
**Then** scores and decisions reproduce within applicable evidenced or
preregistered tolerances
**And** discrepancies retain modality, quality, capture, resource, and runtime
diagnostics.

**Given** all planned held-out paired windows are scored or explicitly accounted
for
**When** the paired score manifests are finalized
**Then** both modality scores, missingness, exclusions, failures, resources,
quality, alignment, and hashes are frozen before fusion or truth unlock
**And** only those immutable score-manifest identities may enter late fusion.

### Story 17A.6: Execute Preregistered Truth-Blind Late Fusion

**FRs implemented:** FR21, FR29, FR71-FR72, FR87, FR89.

As a researcher,
I want a simple frozen late-fusion policy applied to compatible custom scores,
So that combined decisions remain transparent and independent of evaluation
truth.

**Acceptance Criteria:**

**Given** immutable paired physical and syscall scores from G8-qualified held-out
custom windows
**When** fusion input validation runs
**Then** run, window, alignment, bundle, threshold, calibration, score direction,
quality, availability, policy, code, and runtime identities match the frozen
campaign
**And** external ADFA-LD, LID, HAI, fixture, raw event, raw feature, or raw-loss
inputs are rejected.

**Given** the preregistered simple fusion policy
**When** a complete eligible score pair is evaluated
**Then** only the declared transparent operation and parameter evidence are used
to produce the combined decision
**And** no learned, test-fitted, post-unlock, or hidden weight or transformation
is introduced.

**Given** one or both modality scores are missing, invalid, incompatible, stale,
or below the declared quality policy
**When** fusion is attempted
**Then** the exact preregistered missing-modality or unavailable-result rule is
applied with an explicit reason
**And** an absent modality is not replaced, assigned a normal score, or silently
dropped to make a complete pair.

**Given** an eligible or unavailable fusion outcome
**When** `FusionDecision.v1` is created
**Then** it binds physical and syscall score identities, aligned window, frozen
policy and parameters, input availability and quality, operation, combined
score where applicable, decision, diagnostics, code, runtime, and content hash
**And** it contains no truth, label, scenario meaning, expected outcome, or
control command.

**Given** identical paired scores and frozen policy
**When** fusion repeats
**Then** availability handling, combined values, decisions, diagnostics,
serialization, and hashes are deterministic
**And** any mismatch blocks the affected fusion result rather than selecting a
more favorable implementation.

**Given** every planned pair is fused or explicitly accounted for
**When** the fusion manifest is published
**Then** complete, incomplete, unavailable, invalid, and unfavorable fusion
outcomes remain immutable before truth unlock
**And** only the frozen fusion-manifest identity may enter paired evaluation.

### Story 17A.7: Perform the Paired Modality Ablation After Truth Unlock

**FRs implemented:** FR24, FR27, FR52, FR88-FR89.

As an academic evaluator,
I want physical-only, syscall-only, and fusion conditions evaluated on the same
held-out custom evidence,
So that any measured benefit or limitation of combination has a valid paired
comparison basis.

**Acceptance Criteria:**

**Given** immutable physical scores, syscall scores, fusion decisions, bundles,
thresholds, partitions, alignment, metric policy, and restricted truth
**When** the authorized evaluator unlocks truth
**Then** it joins truth only through frozen experiment, run, window, event, and
correlation identities
**And** no input score, decision, model, threshold, policy, partition, or
eligibility rule changes.

**Given** the primary paired-ablation cohort
**When** physical-only, syscall-only, and fusion outcomes are compared
**Then** all three conditions use the exact same eligible held-out runs, aligned
windows, truth, exclusions, and frozen metric policy
**And** sample support and every exclusion reason are reported for each
condition.

**Given** modality availability produces a secondary cohort with different
support
**When** availability or degraded-mode analysis is reported
**Then** it is separated from the primary paired comparison with its own
eligibility, support, missingness, quality, and limitations
**And** it cannot be presented as a paired fusion gain.

**Given** the custom metric applicability matrix
**When** outcomes and paired differences are calculated
**Then** applicable point or window and event or range metrics, false-positive
behavior, detection timing, resource cost, modality availability or quality,
paired deltas, and repeated-run dispersion or uncertainty are computed under the
same frozen definitions
**And** unavailable metrics or comparisons receive explicit reasons.

**Given** the observed fusion result is favorable, neutral, uncertain,
unfavorable, failed, or unavailable
**When** the academic conclusion is assigned
**Then** the actual outcome, uncertainty, assumptions, capture and physical
quality, exclusions, resource trade-offs, and limitations remain visible
**And** no model, threshold, fusion policy, cohort, seed, or metric is changed to
manufacture improvement.

**Given** external ADFA-LD, LID, and HAI results
**When** custom paired evaluation runs
**Then** those benchmarks remain outside every sample, score, truth join,
metric, and paired delta
**And** they may later provide separate context only.

**Given** all planned custom conditions and runs are evaluated
**When** the frozen fusion-result package is published
**Then** it binds dataset, partitions, bundles, thresholds, scores, fusion
policy, truth unlock, metrics, results, resources, quality, uncertainty,
limitations, code, runtime, and manifest hashes
**And** it contributes a reproducible G9 candidate result without replacing the
final cross-track evidence packaging and reconstruction owned by Epic 17B.

## Epic 17B: Publish the Defensible Academic Evidence Package

The researcher can publish separate dataset and modality results, the paired
custom ablation, a capability and limitation matrix, and a reconstructible
claim-to-evidence index without selecting a global cross-domain champion or
inventing missing metrics.

### Story 17B.1: Validate and Register the Final Evidence Tracks

**FRs implemented:** FR24, FR26, FR28, FR65, FR67, FR88, FR92.

As an academic evaluator,
I want every final evidence track registered with its exact scientific status
and immutable identities,
So that publication starts from qualified results rather than reconstructed or
preferred outcomes.

**Acceptance Criteria:**

**Given** completed or explicitly blocked outputs from the physical custom,
syscall custom, ADFA-LD, LID-DS 2021, HAI 23.05, and paired custom-fusion tracks
**When** final evidence admission runs
**Then** each track resolves its source and version, dataset role and split,
bundle and threshold, calibration where applicable, score manifest, truth
unlock, metric result, uncertainty, limitation, scientific status, code,
runtime, and content hash
**And** no result is recomputed, refitted, reselected, relabeled, or manually
completed during admission.

**Given** an evidence track that used an admitted scientific mock
**When** its status is registered
**Then** the capability-gap record, official-document locator, supported
behavior and numbers, provenance, and `mock` or `mock-derived` status required
by the Cross-Epic Mock Admission Guardrail remain attached
**And** the evidence cannot be promoted to measured, official-real, real-plant,
or authentically reproduced evidence.

**Given** any custom evidence or claim depends on a researcher-selected factor,
derived representation, or admitted emulator behavior
**When** the final registry is assembled
**Then** the exact immutable `DecisionRecord.v1`, `ParameterEvidence.v1`, and
`MockAdmission.v1` identities and their prohibited claims remain in the
admission and claim chain
**And** a source record cannot replace decision authority, a derivation cannot
hide its inputs, and a mock cannot lose its replacement condition.

**Given** the LID-DS 2021 track could not qualify or execute under its frozen
protocol
**When** the final registry is assembled
**Then** its immutable blocked or not-executed record and reason are retained
without fabricating measurements
**And** that status does not invalidate otherwise qualified independent tracks.

**Given** a required track artifact is missing, mutable, incompatible, or does
not resolve to its declared source
**When** admission validation runs
**Then** that track receives an explicit incomplete or blocked status with the
failed requirement
**And** it cannot supply a result, comparison, or academic claim.

**Given** the physical and syscall `PTFP-Custom-v1` tracks and their paired
ablation
**When** completeness is checked
**Then** their artifacts resolve to the same G8-qualified campaign identities
and the exact frozen Epic 17A evidence
**And** absence of mandatory custom evidence blocks the final G9 publication
package rather than being replaced by an external benchmark or mock.

**Given** all candidate evidence tracks have been checked
**When** the final track registry is frozen
**Then** qualified, limited, blocked, not-executed, failed, unavailable, and
unfavorable outcomes remain addressable with their reasons
**And** only registry-listed immutable artifacts may feed later Epic 17B
tables, matrices, indexes, and reconstruction.

### Story 17B.2: Publish Separate Dataset and Modality Result Tables

**FRs implemented:** FR24, FR27, FR66, FR88, FR92.

As a researcher,
I want results published in dataset-native and modality-specific tables,
So that distinct evidence domains remain interpretable without false global
comparisons.

**Acceptance Criteria:**

**Given** the frozen final track registry and metric applicability rules
**When** result tables are assembled
**Then** ADFA-LD, LID-DS 2021, HAI 23.05, `PTFP-Custom-v1` physical, and
`PTFP-Custom-v1` syscall evidence appear in separate identified tables
**And** external benchmark records are never inserted into custom paired rows.

**Given** a table for a specific dataset and modality
**When** its rows and columns are populated
**Then** only frozen dataset-native metrics, support, uncertainty or dispersion,
quality, resource observations, scientific status, and applicable limitations
are reported
**And** every value resolves to the admitted immutable metric evidence.

**Given** a desired metric was not defined, applicable, measured, or qualified
for that evidence track
**When** the table is produced
**Then** it is shown as unavailable or not applicable with an explicit reason
**And** no value is inferred, converted, projected, copied from literature, or
fabricated to complete the table.

**Given** published reference numbers accompany an external dataset
**When** they are displayed for context
**Then** they remain visibly separate from prototype-measured results with exact
official or primary-source locators and non-equivalence limitations
**And** they are not treated as rerun measurements or inputs to a calculated
prototype comparison.

**Given** results differ in dataset, modality, representation, task, support,
truth, split, metric, or operating conditions
**When** the publication tables are organized
**Then** no cross-domain aggregate score, leaderboard, rank, or global champion
is calculated or implied
**And** comparison language is limited to valid within-track or explicitly
paired custom evidence.

**Given** a qualified, limited, blocked, not-executed, failed, unavailable, or
unfavorable track
**When** its table is finalized
**Then** the actual status, support, missing values, failure reasons, and
limitations remain visible
**And** omission cannot be used to make the evidence package appear more
complete or favorable.

### Story 17B.3: Publish the Paired Custom-Only Ablation Table

**FRs implemented:** FR27, FR66, FR88, FR92.

As an academic evaluator,
I want the frozen physical-only, syscall-only, and fusion results presented as
a paired custom ablation,
So that the contribution and limitations of fusion are reported on genuinely
comparable evidence.

**Acceptance Criteria:**

**Given** the immutable Epic 17A primary paired-ablation result
**When** the custom ablation table is assembled
**Then** physical-only, syscall-only, and fusion columns use the exact same
eligible held-out runs, aligned windows, truth, exclusions, metric definitions,
and sample support
**And** every cell resolves to a frozen score, fusion, truth-join, or metric
artifact.

**Given** modality availability or quality produced a secondary or degraded
cohort
**When** those results are reported
**Then** they appear separately with their own eligibility, support,
missingness, quality, and limitation evidence
**And** they cannot be merged into or described as the primary paired fusion
comparison.

**Given** applicable custom metrics and repeated-run evidence
**When** paired results are displayed
**Then** point or window and event or range performance, false-positive
behavior, detection timing, resources, availability or quality, paired deltas,
and uncertainty or dispersion are reported exactly where frozen and applicable
**And** unsupported cells carry explicit unavailable or not-applicable reasons.

**Given** the measured fusion result is favorable, neutral, uncertain,
unfavorable, failed, or unavailable
**When** the ablation conclusion is written
**Then** the actual result, uncertainty, assumptions, exclusions, quality,
resource trade-offs, and limitations remain visible
**And** no bundle, threshold, fusion policy, cohort, seed, metric, or result is
recomputed or reselected for publication.

**Given** ADFA-LD, LID-DS 2021, HAI 23.05, literature, fixture, or mock evidence
**When** ablation admission is validated
**Then** it is excluded from all paired samples, scores, deltas, and claims
**And** only the synchronized G8-qualified `PTFP-Custom-v1` campaign may support
the physical-versus-syscall-versus-fusion ablation.

**Given** the paired table is finalized
**When** its manifest is frozen
**Then** it binds the exact dataset, partitions, bundles, thresholds, score and
fusion manifests, truth unlock, metrics, support, exclusions, resources,
quality, uncertainty, limitations, code, runtime, and content hash
**And** it remains a custom-only result rather than a global model ranking.

### Story 17B.4: Build the Capability and Limitation Matrix

**FRs implemented:** FR24, FR65-FR66, FR92.

As a researcher,
I want a matrix that states what each evidence track can and cannot support,
So that readers can distinguish demonstrated capability from scope boundaries
and missing evidence.

**Acceptance Criteria:**

**Given** the frozen registry, result tables, custom ablation, and project claim
boundaries
**When** the capability and limitation matrix is assembled
**Then** each row identifies a precise capability or claim and each evidence
column identifies its dataset, modality, representation, task, and scientific
status
**And** no cell erases dataset-native semantics to force apparent equivalence.

**Given** evidence for a matrix cell
**When** its support level is assigned
**Then** the cell states supported, limited, unsupported, blocked,
not-executed, failed, or not-applicable as justified by immutable evidence and
an exact locator
**And** absence of evidence is never converted into support.

**Given** custom physical, custom syscall, and custom fusion claims
**When** their limitations are recorded
**Then** the controlled-prototype scope, source and capture boundaries,
physical quality, clock and alignment assumptions, mock-derived elements, run
support, and lack of real-plant validation remain explicit
**And** the synchronized custom result is not generalized to unrelated plants,
hosts, workloads, or attack classes.

**Given** external ADFA-LD, LID-DS 2021, and HAI 23.05 evidence
**When** their capabilities are mapped
**Then** external provenance, different process or host context, published
versus measured status, metric differences, and any blocked execution remain
explicit
**And** none is represented as a synchronized substitute for the custom fusion
campaign.

**Given** optional consensus or OPC evidence is referenced
**When** its capability is stated
**Then** it is limited to its declared logical or contextual role with source,
independence, timing, quality, and mock-admission limitations
**And** consensus-projected OPC or other unsupported plant behavior is never
reported as measured process evidence.

**Given** the matrix is finalized
**When** claims and limitations are checked
**Then** every support statement resolves to admitted result evidence and every
limitation resolves to a recorded boundary, status, or failure
**And** unresolved or ambiguous cells block the affected claim rather than the
independent evidence package.

### Story 17B.5: Build the Immutable Claim-to-Evidence Index

**FRs implemented:** FR26, FR28, FR65, FR67, FR88, FR92.

As an academic reviewer,
I want every publishable claim linked to its complete immutable evidence chain,
So that I can audit the result without relying on narrative, UI state, or a
mutable latest artifact.

**Acceptance Criteria:**

**Given** a claim proposed for the academic evidence package
**When** it enters the claim-to-evidence index
**Then** it receives a stable claim identity, bounded wording, scope, evidence
track, scientific status, and explicit supported, limited, or unsupported
disposition
**And** the index does not broaden the claim beyond its registered evidence.

**Given** a supported or limited claim
**When** its evidence chain is resolved
**Then** it identifies the exact source and version, role and split, dataset and
run, bundle and threshold, calibration where applicable, score or fusion
record, truth unlock and join, metric and uncertainty, result table or ablation
cell, limitation, code, runtime, and content hashes
**And** every locator is content-addressed or otherwise immutable and
machine-verifiable.

**Given** a claim depends on mock or mock-derived evidence
**When** its chain is indexed
**Then** the capability-gap record, official-document source and exact locator,
supported behaviors and numbers, transfer limitations, exact prototype
component, bounded research question, dataset/modality track, affected final
table, paired-ablation, matrix, or claim element, and mock status are included
**And** the wording cannot imply authentic reproduction, official-real data,
or measured plant behavior.

**Given** a claim lacks a required artifact, locator, applicable metric, or
valid support chain
**When** index validation runs
**Then** the claim is marked unsupported or blocked with the unresolved element
**And** it is rejected from supported conclusions without inventing or
substituting evidence.

**Given** a blocked, not-executed, failed, unavailable, neutral, uncertain, or
unfavorable result
**When** related claims are indexed
**Then** the actual status and limitations remain discoverable alongside any
permitted bounded conclusion
**And** the record cannot be hidden, softened, or redirected to a more favorable
track.

**Given** the complete index
**When** independence and reproducibility checks run
**Then** every link resolves without a dashboard, mutable alias, manual memory,
or hidden evaluator state
**And** orphan claims, orphan artifacts, duplicate identities, hash mismatches,
and circular support chains block the affected claim.

### Story 17B.6: Reconstruct the Final Evidence Package and Decide G9

**FRs implemented:** FR26, FR28, FR65-FR67, FR88, FR92.

As an academic reviewer,
I want the complete evidence package reconstructed from frozen manifests in a
declared evaluation environment,
So that G9 reflects reproducible evidence rather than hand-edited publication
outputs.

**Acceptance Criteria:**

**Given** the frozen final track registry, result artifacts, manifests, and
declared evaluation environment
**When** package reconstruction begins
**Then** compatibility, content hashes, code and runtime identities, source
locators, role and split identities, bundles, thresholds, scores, truth joins,
metrics, statuses, and limitation references verify before publication outputs
are produced
**And** no model training, inference rerun, truth relabeling, threshold change,
metric redefinition, or result reselection occurs.

**Given** verified frozen inputs
**When** the final package is reconstructed
**Then** it deterministically produces the separate dataset and modality tables,
paired custom-only ablation, capability and limitation matrix, and immutable
claim-to-evidence index
**And** blocked, not-executed, failed, unavailable, neutral, uncertain,
unfavorable, and mock-derived statuses remain intact.

**Given** a prior generated package from the same frozen inputs and declared
environment
**When** reconstruction outputs are compared
**Then** normalized content, references, row and cell provenance, ordering,
serialization, and applicable hashes match the declared reproducibility policy
**And** any unexplained mismatch blocks G9 rather than being manually repaired.

**Given** the LID-DS 2021 track is validly blocked or not executed
**When** the complete package is evaluated
**Then** its evidence record, reason, and limitation are included while all
other tracks are judged independently
**And** no fabricated LID measurement is required to close the package.

**Given** final academic conclusions
**When** G9 validation checks them against the package
**Then** every supported statement resolves through the claim index to exact
immutable evidence and all cross-domain comparisons obey the separate-table
and custom-only paired-ablation rules
**And** a global cross-domain champion, invented metric, missing limitation, or
unsupported mock claim fails the gate.

**Given** all mandatory custom evidence, reconstruction, provenance,
scientific-status, limitation, and claim-resolution checks pass
**When** the G9 decision is recorded
**Then** the immutable final evidence-package manifest receives `G9_PASS` with
the exact inputs, outputs, environment, validation results, and hashes;
otherwise it receives an explicit blocking decision and reasons
**And** G9 neither requires UI or dashboard work nor authorizes implementation,
deployment, plant control, or further scientific claims.

## Epic 18: Optionally Present Published Evidence in the Existing Dashboard

If separately activated, the researcher can demonstrate the already published
evidence through the existing lightweight local dashboard while keeping
physical representations, syscall evidence, detector channels, provenance,
freshness, and limitations understandable and read-only.

Epic 18 has two explicit, non-interchangeable modes: `legacy_demo` may show the
current prototype operating under a persistent `DEMO - NOT PUBLISHED
SCIENTIFIC EVIDENCE` label; `frozen_evidence` reads one exact immutable
`G9_PASS` package and exposes no control or mutation route. Neither mode is a
scientific readiness gate.

### Story 18.1: Bind a Read-Only Projection to the Frozen Evidence Package

**FRs implemented:** FR68, FR71, FR92-FR93.

As a researcher,
I want the existing dashboard to read one exact published evidence package,
So that the demonstration reflects immutable G9 evidence without recalculation
or mutable latest-state assumptions.

**Acceptance Criteria:**

**Given** Epic 18 has been separately activated and an exact Epic 17B package
manifest is selected
**When** the dashboard evidence projection loads
**Then** the manifest identity, `G9_PASS` decision, schema, content hashes,
source locators, result artifacts, and declared compatibility evidence verify
before any result is displayed
**And** an absent, blocked, mutable, incompatible, or hash-mismatched package is
shown as unavailable with the reason rather than as published evidence.

**Given** the dashboard is showing live/current prototype state instead of an
explicitly selected immutable `G9_PASS` package
**When** the page loads
**Then** its mode is `legacy_demo` and the persistent status reads
`DEMO - NOT PUBLISHED SCIENTIFIC EVIDENCE`
**And** no live/latest value is presented as a frozen scientific result.

**Given** a verified package
**When** the dashboard payload is assembled
**Then** fields are projected directly from the frozen track registry, result
tables, custom ablation, capability and limitation matrix, and
claim-to-evidence index
**And** the projection cannot import, split, train, infer, calibrate, promote,
fuse, relabel, recompute, rank, or rewrite scientific artifacts.

**Given** a package value is unavailable, not applicable, blocked,
not-executed, failed, neutral, uncertain, unfavorable, or mock-derived
**When** it is projected
**Then** its exact status, reason, provenance, and limitation remain visible
**And** the dashboard does not fill, normalize, reinterpret, or improve it.

**Given** a projection field or source locator supplied by the package
**When** it is parsed and rendered
**Then** it is treated as untrusted input, validated against the declared
read-only schema, and safely encoded for presentation
**And** unknown fields, invalid identities, unsafe locators, and malformed
values fail closed without altering the package or local runtime.

**Given** the page refreshes or the projection is loaded again
**When** the selected package identity is unchanged
**Then** all scientific values, statuses, ordering, references, and limitations
remain deterministic under the declared presentation rules
**And** evidence generation time, package identity, and last verification time
remain distinct from live process freshness.

### Story 18.2: Present Linked Physical Representations and Distinct Channels

**FRs implemented:** FR14, FR68, FR70, FR72, FR93.

As a demonstration viewer,
I want the existing page to show linked physical values and separate evidence
channels,
So that I can understand what happened without confusing representations,
modalities, models, or control states.

**Acceptance Criteria:**

**Given** an admitted published physical observation
**When** its compact dashboard view is rendered
**Then** raw mA, normalized span, and engineering value are linked through the
same source, observation, run, sensor, profile, and conversion identities
**And** unit, profile, quality, validity, freshness, provenance, and applicable
limitations are visible without recalculating any representation.

**Given** physical, syscall, and fusion evidence in the package
**When** detector outcomes are presented
**Then** physical and Linux-host-syscall modalities occupy distinct channels
and frozen fusion occupies a separate derived-result channel
**And** bundle, threshold and origin, score or decision status, quality or
missingness, run support, and limitation evidence remain attached.

**Given** the project semantic boundary
**When** labels and explanatory text are rendered
**Then** exactly two modalities are named: physical instrumentation and Linux
host syscalls
**And** 4-20 mA is described only as a physical representation, while LSTM,
GRU, autoencoders, and baselines are described only as models.

**Given** custom syscall evidence is referenced
**When** its channel is displayed
**Then** it resolves only to frozen authentic captured kernel-event evidence
with workload attribution, collector and kernel identity, gaps, drops,
quality, and limitations where applicable
**And** fabricated syscalls, domain-representing convenience fixtures, or
external benchmark events are never presented as custom captured evidence.

**Given** consensus, consensus failure, OPC integrity, SCADA divergence,
replay or freeze, physical detection, syscall detection, and fusion states
exist in the published package
**When** their compact statuses are displayed
**Then** each remains semantically distinct with its own source, time, status,
quality, and limitation
**And** none is rendered as an actuator command, operating instruction, or
grant of control authority.

**Given** a channel or linked representation is unavailable or invalid
**When** the page is rendered
**Then** the absent or invalid state and exact reason are shown instead of a
normal value, inferred score, forced link, or hidden panel
**And** the remaining independent published channels stay inspectable.

### Story 18.3: Present Separate Results, Claims, and Limitations

**FRs implemented:** FR69, FR71, FR92-FR93.

As an academic reviewer,
I want the final evidence package projected in its native scopes,
So that the dashboard demonstrates the publication without creating stronger
or broader claims.

**Acceptance Criteria:**

**Given** the frozen Epic 17B result tables
**When** published results are presented
**Then** ADFA-LD, LID-DS 2021, HAI 23.05, `PTFP-Custom-v1` physical, and
`PTFP-Custom-v1` syscall results remain in separate identified views with their
dataset role, version, support, metrics, status, provenance, and limitations
**And** published-reference and prototype-measured values remain visibly
distinct.

**Given** the frozen paired custom ablation
**When** physical-only, syscall-only, and fusion results are displayed together
**Then** only the exact primary same-support `PTFP-Custom-v1` comparison and any
separately identified availability or degraded cohort are projected
**And** external benchmarks never appear as paired samples or fusion gains.

**Given** the capability and limitation matrix
**When** a capability or evidence track is inspected
**Then** its supported, limited, unsupported, blocked, not-executed, failed, or
not-applicable status and exact limitation are presented from the frozen matrix
**And** controlled custom evidence is not called real-plant evidence, HAI is
not called compressor validation, and syscall benchmarks are not called
physical evidence.

**Given** a published claim
**When** its evidence details are requested
**Then** the page projects the stable claim identity, bounded wording,
scientific status, source and version, split, bundle, threshold or calibration,
run, score or metric, uncertainty, limitation, and immutable evidence locators
from the claim-to-evidence index
**And** a dashboard label, visual emphasis, or missing locator cannot create
support for a claim.

**Given** mock or mock-derived evidence appears in a result, limitation, or
claim chain
**When** it is rendered
**Then** its capability-gap basis, official-document source and exact locator,
supported scope, transfer limitation, and mock status remain explicit as
required by the Cross-Epic Mock Admission Guardrail
**And** it is never styled or described as measured, official-real,
authentically reproduced, or real-plant evidence.

**Given** all result views are assembled
**When** headings, ordering, highlights, and summaries are checked
**Then** no cross-domain aggregate score, leaderboard, rank, or global champion
is calculated or implied
**And** unavailable metrics, blocked LID execution, failed or unfavorable
outcomes, uncertainty, and limitations remain visible.

### Story 18.4: Enforce and Verify the Optional Presentation-Only Mode

**FRs implemented:** FR68, FR70-FR71, FR93.

As a prototype owner,
I want the dashboard evidence mode to be explicitly read-only and independently
verifiable,
So that a convenient demonstration cannot alter science, runtime behavior, or
project readiness.

**Acceptance Criteria:**

**Given** the existing local dashboard also contains operator controls
**When** the optional Epic 18 evidence mode is activated
**Then** runtime, scenario, compressor, actuator, experiment, model, threshold,
fusion, truth, and evidence mutation controls are absent or disabled in that
mode and mutating requests are rejected
**And** the evidence mode exposes only the minimum local read-only navigation
needed to inspect the selected published package.

**Given** a mutation request reaches the local server while
`frozen_evidence` mode is active
**When** any route attempts to change runtime, scenario, compressor, actuator,
experiment, model, threshold, fusion, truth, or evidence state
**Then** the server rejects it independently of whether controls are hidden in
the browser
**And** the selected package and every scientific artifact remain byte-for-byte
unchanged.

**Given** the evidence dashboard is absent, disabled, stopped, malformed, stale,
or unavailable
**When** acquisition, consensus, storage, analytics, evaluation, reconstruction,
or control paths operate
**Then** their behavior and authorization remain independent and unchanged
**And** dashboard failure can never create or alter a command, score, artifact,
gate decision, or scientific status.

**Given** presentation verification fixtures are needed
**When** they are admitted
**Then** non-domain sentinel inputs may test empty, malformed, missing, or unsafe
states without becoming scientific mocks, while every fixture representing
domain behavior or numbers satisfies the Cross-Epic Mock Admission Guardrail
**And** no fixture is presented as a measured prototype or official-dataset
result.

**Given** the exact frozen G9 package and declared local presentation
environment
**When** automated contract and page-level verification runs
**Then** it checks deterministic projection, separate modalities and channels,
linked physical representations, native result scopes, status and limitation
visibility, immutable locators, unavailable and invalid states, safe rendering,
and rejection of every mutation path
**And** verification consumes frozen artifacts without executing training,
inference, fusion, truth relabeling, evaluation, or control.

**Given** a researcher follows the minimal local demonstration instructions
**When** the evidence-only page is opened
**Then** the selected package identity and publication status are visible and
the main physical, syscall, fusion, result, provenance, quality, and limitation
views can be inspected without editing scientific state
**And** no redesign, frontend migration, mobile-specific behavior, animation,
or advanced UX acceptance criterion is required.

**Given** all Epic 18 presentation checks finish
**When** their outcome is recorded
**Then** the optional dashboard is marked available or unavailable with exact
environment, package, verification, failure, and limitation evidence
**And** either outcome leaves G9, implementation readiness, headless
reconstruction, and all scientific evidence unchanged.
