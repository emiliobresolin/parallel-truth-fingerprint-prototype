---
type: implementation-readiness-report
date: 2026-08-22
project: parallel-truth-fingerprint-prototype
assessment_run: post-correct-course-rerun
status: READY
completedAt: 2026-08-22T14:41:08-03:00
assessor: BMAD Implementation Readiness workflow
stepsCompleted:
  - step-01-document-discovery
  - step-02-prd-analysis
  - step-03-epic-coverage-validation
  - step-04-ux-alignment
  - step-05-epic-quality-review
  - step-06-final-assessment
inputDocuments:
  controlling:
    - _bmad-output/planning-artifacts/prd.md
    - _bmad-output/planning-artifacts/architecture.md
    - _bmad-output/planning-artifacts/epics.md
    - _bmad-output/planning-artifacts/ux-design-specification.md
  historical_traceability_only:
    - _bmad-output/planning-artifacts/prd-update-2026-05-21.md
    - _bmad-output/planning-artifacts/prd-update-2026-08-15.md
    - _bmad-output/planning-artifacts/architecture-update-2026-05-21.md
    - _bmad-output/planning-artifacts/architecture-update-2026-08-15.md
    - _bmad-output/planning-artifacts/epics-update-2026-05-21.md
    - _bmad-output/planning-artifacts/epics-update-2026-07-30.md
    - _bmad-output/planning-artifacts/epics-update-2026-08-15.md
---

# Implementation Readiness Assessment Report

**Date:** 2026-08-22  
**Project:** parallel-truth-fingerprint-prototype  
**Run:** Post-Correct-Course rerun; preserves the earlier NOT READY report.

## Document Discovery

### PRD files found

**Controlling whole document:**

- `prd.md` - 67,771 bytes; updated 2026-08-22.

**Historical whole-document overlays:**

- `prd-update-2026-05-21.md` - 5,964 bytes.
- `prd-update-2026-08-15.md` - 51,767 bytes.

The approved consolidation makes `prd.md` the sole normative PRD. The dated
files remain traceability inputs only. No sharded PRD exists.

### Architecture files found

**Controlling whole document:**

- `architecture.md` - 60,886 bytes; updated 2026-08-22.

**Historical whole-document overlays:**

- `architecture-update-2026-05-21.md` - 8,168 bytes.
- `architecture-update-2026-08-15.md` - 26,351 bytes.

The approved consolidation makes `architecture.md` the sole normative
architecture. The dated files remain traceability inputs only. No sharded
architecture exists.

### Epic and story files found

**Controlling whole document:**

- `epics.md` - 271,159 bytes; updated 2026-08-22.

**Historical whole-document overlays:**

- `epics-update-2026-05-21.md` - 8,673 bytes.
- `epics-update-2026-07-30.md` - 42,442 bytes.
- `epics-update-2026-08-15.md` - 54,169 bytes.

The current 81-story package is contained in `epics.md`; dated files remain
traceability inputs only. No sharded epic/story package exists.

### UX files found

**Controlling whole document:**

- `ux-design-specification.md` - 38,727 bytes; updated 2026-08-22.

No sharded or duplicate UX document exists. UX and Epic 18 remain optional and
outside the scientific implementation-readiness gate.

### Discovery issues

- No whole-versus-sharded duplicates were found.
- No required document type is missing.
- Same-date collision avoided: this rerun uses
  `implementation-readiness-report-2026-08-22-rerun.md` and preserves the
  earlier `implementation-readiness-report-2026-08-22.md` NOT READY report.
- Dated overlays are not unresolved duplicates because the controlling reading
  rules in `prd.md` and `architecture.md` explicitly demote them to historical
  traceability.

### Proposed assessment selection

Use `prd.md`, `architecture.md`, `epics.md`, and
`ux-design-specification.md` as the controlling documents. Use dated overlays
only to audit identifier/supersession history, never as competing normative
requirements.

## PRD Analysis

The controlling PRD was read completely. The extraction below is verbatim
from its self-contained normative inventory; historical base wording is not
treated as a second requirement source.

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

### Extraction totals

- Functional requirements: **93/93**, unique identifiers FR1-FR93.
- Non-functional requirements: **52/52**, unique identifiers NFR1-NFR52.
- Duplicate or missing controlling identifiers: **0**.

### Additional Requirements

- Keep the project a local academic prototype for one compressor, three
  physical variables, and three logically independent edges.
- Preserve the brownfield Python services and existing Go ABCI/CometBFT, MQTT,
  OPC UA, and MinIO boundaries; avoid cloud, Kubernetes, service mesh, API
  gateway, Kafka, a new database, production HMI, or frontend migration.
- Use only official/primary applicable authority for external domain claims;
  separate manufacturer capability from researcher decision authority.
- Admit synthetic physical behavior only through the bounded signal-emulator
  capability gap; authentic Linux workload execution and kernel calls remain
  mandatory whenever reproducible.
- Keep ADFA-LD, LID-DS 2021, HAI 23.05, and PTFP-Custom-v1 in native and
  non-substitutable evidence roles; only the synchronized custom campaign is
  eligible for paired physical/syscall/fusion comparison.
- Keep the dashboard optional and nonblocking. `legacy_demo` is visibly
  non-scientific; `frozen_evidence` reads one immutable `G9_PASS` package and
  rejects mutation routes server-side.
- Treat planning approval as distinct from implementation, acquisition,
  training, capture, experiment, activation, deployment, and publication
  authorization.

### PRD Completeness Assessment

**PASS.** The PRD now contains one self-contained controlling inventory with
all 93 FRs and 52 NFRs. FR76, FR79, FR93, and NFR39 contain the strengthened
academic-veracity, authentic-workload, optional-presentation, and fail-closed
class-authority rules. Supersession is explicit, so dated overlays and the
earlier brownfield narrative are historical context rather than competing
normative contracts.

Nonblocking editorial debt remains in the historical narrative, which still
uses old LSTM-only, fake-SCADA, and mandatory-demo wording. The controlling
reading rule and complete inventory resolve implementation authority, but a
future prose cleanup would reduce reader friction.


## Epic Coverage Validation

### Epic FR Coverage Extracted

The controlling epic map claims implementation coverage for every identifier
from FR1 through FR93. The map uses Epics 9-18; Epic 18 is explicitly optional
and covers only conditional presentation requirements.

### Coverage Matrix

| FR Number | PRD Requirement | Epic Coverage | Status |
| --- | --- | --- | --- |
| FR1 | **AMENDED -> FR73-FR76.** Preserve simulation of temperature, pressure, and RPM for one compressor as internal engineering-unit physics while custom edge evidence follows the cited current-domain instrument profile. | Epic 10 - Preserve compressor physics while moving edge evidence to the profile-owned current-domain boundary. | ✓ Covered |
| FR2 | **AMENDED -> FR73-FR76.** Preserve one assigned physical sensor per edge, with the edge receiving primary raw-current evidence and its profile-owned representations. | Epic 10 - Preserve one assigned sensor per edge through `SignalObservation.v2`. | ✓ Covered |
| FR3 | **RETAINED/AMENDED -> FR73, FR91; NFR39-NFR50.** Each edge publishes its versioned observation through the local MQTT boundary. | Epic 10 - Publish versioned physical observations through MQTT. | ✓ Covered |
| FR4 | **RETAINED/AMENDED -> FR73, FR91; NFR39-NFR50.** Each edge consumes peer observations without bypassing version, quality, provenance, or trust rules. | Epic 10 - Consume peer observations through the versioned physical path. | ✓ Covered |
| FR5 | **RETAINED/AMENDED -> FR73, FR91; NFR39-NFR50.** Each edge maintains its own non-trusted local replicated compressor view without shared mutable state collapsing edge independence. | Epic 10 - Preserve independent non-trusted edge-local views. | ✓ Covered |
| FR6 | **RETAINED/AMENDED -> FR91.** The system executes the existing real CometBFT plus Go ABCI Byzantine-style validation path using the versioned v2 physical contract when v2 is active. | Epic 11 - Execute current-domain CometBFT/ABCI consensus. | ✓ Covered |
| FR7 | **RETAINED/AMENDED -> FR91; NFR49-NFR50.** A successful consensus result exposes and persists its trust ranking as reconstructible evidence. | Epic 11 - Persist reconstructible trust ranking evidence. | ✓ Covered |
| FR8 | **RETAINED/AMENDED -> FR91.** Consensus can exclude a suspicious edge contribution under the declared current-domain comparison basis. | Epic 11 - Exclude suspicious contributions under the declared basis. | ✓ Covered |
| FR9 | **RETAINED/AMENDED -> FR91.** Each consensus result identifies its participating edges and correlation identities. | Epic 11 - Identify round participants and correlation identities. | ✓ Covered |
| FR10 | **RETAINED/AMENDED -> FR91.** Each consensus result identifies excluded edges and the evidence-based reason for each exclusion. | Epic 11 - Identify exclusions and evidence-based reasons. | ✓ Covered |
| FR11 | **RETAINED/AMENDED -> FR91; NFR50.** Each consensus result exposes the complete ranking and evidence references for every edge in the round. | Epic 11 - Expose complete round ranking and evidence references. | ✓ Covered |
| FR12 | **RETAINED/AMENDED -> FR91; NFR47-NFR48.** Failure to reach valid consensus remains an explicit, fail-closed outcome. | Epic 11 - Represent consensus failure explicitly and fail closed. | ✓ Covered |
| FR13 | **RETAINED/AMENDED -> FR91; NFR50.** The system emits structured, traceable logs for each consensus round. | Epic 11 - Emit structured traceable consensus logs. | ✓ Covered |
| FR14 | **RETAINED/AMENDED -> FR91, FR93.** Consensus failure remains a distinct state and, if the optional dashboard is implemented, a distinct presentation. | Epic 11 - Preserve the distinct consensus-failure state; Epic 18 may optionally present it. | ✓ Covered |
| FR15 | **SUPERSEDED -> FR90.** Do not implement a fake or consensus-projected SCADA source as v2 evidence; use the independent pre-consensus OPC UA path. | Epic 12 - Replace fake/projected SCADA with independent OPC UA evidence. | ✓ Covered |
| FR16 | **SUPERSEDED -> FR90-FR91.** Do not retain an anonymous circular sensor-tolerance comparison; use eligible OPC UA evidence and the declared comparison basis. | Epic 12 - Replace circular tolerance comparison with an eligible, declared independent comparison. | ✓ Covered |
| FR17 | **SUPERSEDED -> FR90, FR93.** SCADA divergence is replaced by explicit independent-OPC integrity and comparison outcomes, optionally presented without control authority. | Epic 12 - Produce explicit OPC integrity/comparison outcomes; Epic 18 may optionally present them. | ✓ Covered |
| FR18 | **AMENDED -> FR85, FR87, FR92; NFR40, NFR49.** Persist immutable, role-separated eligible evidence rather than one ambiguous valid-data object. | Epic 10 - Persist role-separated physical evidence; Epic 17A assembles the synchronized custom evidence record. | ✓ Covered |
| FR19 | **SUPERSEDED -> FR77-FR89.** Do not implement an LSTM-only fingerprint premise; compare declared physical and syscall candidates under isolated truth. | Epic 13 - Replace the LSTM-only premise with fair physical candidates. | ✓ Covered |
| FR20 | **SUPERSEDED -> FR78, FR81, FR87.** A fingerprint is an immutable, track-specific detector bundle and result, not an assumed single model. | Epic 13 - Produce an immutable physical detector bundle. | ✓ Covered |
| FR21 | **SUPERSEDED -> FR87-FR89.** Detector scores, decisions, and optional fusion follow frozen track-specific calibration and synchronized evidence. | Epic 13 - Produce frozen physical scores and decisions; Epic 17A handles eligible paired fusion. | ✓ Covered |
| FR22 | **SUPERSEDED -> FR87.** Save and load complete immutable detector bundles without fitting or threshold recalculation. | Epic 13 - Save and load the complete physical bundle without fitting. | ✓ Covered |
| FR23 | **SUPERSEDED -> FR75, FR77-FR89.** Replay/freeze is a preregistered, truth-isolated evaluation condition rather than proof by one legacy model. | Epic 13 - Evaluate replay/freeze and other preregistered conditions with isolated truth. | ✓ Covered |
| FR24 | **AMENDED -> FR82-FR84.** External benchmark work uses separate, dataset-native ADFA-LD, LID-DS 2021, and HAI 23.05 roles rather than one generic benchmark adapter or result claim. | Epics 15A, 15B, and 16 - Execute dataset-native external benchmark tracks; Epic 17B reports them separately. | ✓ Covered |
| FR25 | **SUPERSEDED -> FR86; NFR41.** A universal stratified 80/20 sample split is prohibited; complete official groups or independent runs split before window formation. | Epics 13, 14, 15A, 15B, 16, and 17A - Replace universal sample splitting with group/run-before-window partitioning. | ✓ Covered |
| FR26 | **RETAINED/AMENDED -> FR87-FR88; NFR40.** Persist complete architecture, hyperparameter, execution, dependency, data, calibration, and runtime identity for every measured detector run. | Epic 9 - Define complete immutable run identity; Epics 13-17B populate the track-specific records. | ✓ Covered |
| FR27 | **SUPERSEDED -> FR77-FR88.** Evaluation uses labels only after freeze and reports protocol-appropriate anomaly, temporal, event, uncertainty, and quality outcomes rather than one universal supervised-classification metric set. | Epics 13, 14, 15A, 15B, 16, 17A, and 17B - Replace one universal metric set with protocol-appropriate outcomes. | ✓ Covered |
| FR28 | **AMENDED -> FR87, FR92; NFR49.** Persist immutable role- and version-separated run, bundle, metric, and evidence records; a mutable shared history prefix is not scientific identity. | Epic 9 - Define immutable role/version evidence history; Epics 13-17B publish their records through it. | ✓ Covered |
| FR29 | **SUPERSEDED -> FR87, FR89.** External ADFA-LD, LID-DS, or HAI models never become compressor detectors; only compatible custom bundles may run in their own modality and only synchronized custom scores are fusion-eligible. | Epic 13 - Restrict runtime physical shadow inference to a compatible custom bundle; Epic 17A permits only custom paired fusion. | ✓ Covered |
| FR30 | **RETAINED.** Capture a v1 golden baseline across runtime, contracts, artifacts, dashboard state, and experimental fingerprint behavior. | Epic 9 - Freeze the complete v1 evidence baseline. | ✓ Covered |
| FR31 | **RETAINED.** Classify every dataset and run by controlled provenance tier and result role without overriding dataset-native scope. | Epic 9 - Classify dataset and result provenance roles. | ✓ Covered |
| FR32 | **RETAINED.** Prevent fixtures or published statistics from being represented as locally measured execution results. | Epic 9 - Prevent fixtures/references from becoming measured results. | ✓ Covered |
| FR33 | **SUPERSEDED -> FR73-FR74.** `SignalObservation.v2` and profile-owned derivation replace one universal `ProcessSample` evidence contract; OPC UA has its separate FR90 contract. | Epic 10 - Replace universal `ProcessSample` evidence with `SignalObservation.v2` and profile-owned derivation. | ✓ Covered |
| FR34 | **AMENDED -> FR75-FR77.** Declare controlled experiments through a versioned `ExperimentSpec` whose schedules, numbers, interventions, and truth follow provenance and access controls. | Epic 10 - Define the versioned, provenance-bound `ExperimentSpec`. | ✓ Covered |
| FR35 | **AMENDED -> FR74-FR75, FR85; NFR46.** Accelerated simulator sessions may support declared physical-only or test evidence, but final fusion evidence requires synchronized physical observations and authentic syscalls from the same correlated runs. | Epic 10 - Support declared accelerated physical-only/test sessions; Epic 17A admits only same-run authentic paired evidence. | ✓ Covered |
| FR36 | **AMENDED -> FR77, FR86; NFR41.** Generate truth independently, keep it structurally absent from detector contracts, and join it only after freeze. | Epic 10 - Generate and structurally isolate scenario truth. | ✓ Covered |
| FR37 | **AMENDED -> FR73-FR75, FR78.** Feature context, units, derivatives, and commanded state are profile-owned and evidence-referenced, while intervention truth remains protected. | Epic 10 - Define profile-owned context, units, and derived features. | ✓ Covered |
| FR38 | **AMENDED -> FR75-FR77, FR88; NFR51.** Execute a preregistered scenario matrix and preserve valid, invalid, aborted, unfavorable, and recovery runs. | Epic 10 - Define and preserve the preregistered experiment matrix; Epic 17A executes the formal paired campaign. | ✓ Covered |
| FR39 | **AMENDED -> FR86; NFR41.** Split every official group or custom run before windowing and prevent windows crossing trace, file, boot, session, process, scenario, gap, schema, or split boundaries. | Epic 9 - Define group/run-before-window policy; Epics 10 and 13-17A enforce it for their data. | ✓ Covered |
| FR40 | **AMENDED -> FR85; NFR40, NFR49-NFR50.** Publish immutable verified artifacts first and atomically publish the complete manifest last. | Epic 9 - Define verified immutable publication and manifest-last rules; Epics 10 and 17A apply them to custom evidence. | ✓ Covered |
| FR41 | **AMENDED -> FR85-FR86; NFR40-NFR41, NFR45-NFR46, NFR49, NFR51.** Close `DATASET_QUALIFIED` only after synchronized-stream, leakage, capture-quality, correlation, durability, completeness, and reporting checks pass. | Epic 10 - Qualify physical experiment evidence; Epic 17A closes the synchronized `DATASET_QUALIFIED` gate. | ✓ Covered |
| FR42 | **AMENDED -> FR90; NFR42.** Publish a pre-consensus plant/transmitter snapshot through OPC UA without granting analytics actuator authority. | Epic 12 - Publish the pre-consensus plant/transmitter snapshot. | ✓ Covered |
| FR43 | **AMENDED -> FR90.** Read OPC UA only through a distinct real `opc.tcp` client; internal server-object access is not eligible v2 evidence. | Epic 12 - Read OPC UA only through a distinct real client. | ✓ Covered |
| FR44 | **AMENDED -> FR90; NFR46, NFR50.** Preserve OPC UA values, status, timestamps, schema, producer/revision, and correlation for reconstruction. | Epic 12 - Preserve OPC values, quality, timestamps, revision, and correlation. | ✓ Covered |
| FR45 | **AMENDED -> FR90; NFR47.** Reject incomplete, stale, mixed, invalid, unavailable, or mis-correlated OPC UA observations explicitly. | Epic 12 - Reject incomplete, stale, mixed, invalid, or unavailable OPC evidence. | ✓ Covered |
| FR46 | **AMENDED -> FR90, FR92; NFR50.** Consume only eligible OPC UA observations and preserve every comparison and fail-closed diagnostic. | Epic 12 - Compare only eligible OPC evidence and persist diagnostics. | ✓ Covered |
| FR47 | **AMENDED -> FR90; NFR50.** Prove OPC and consensus causal source independence through a reconstructible branch-isolation round-trip test. | Epic 12 - Prove OPC/consensus causal source independence. | ✓ Covered |
| FR48 | **AMENDED -> FR90; NFR48, NFR52.** Activate independent OPC mode only through explicit versioned authorization and never silently fall back to a consensus projection. | Epic 12 - Activate versioned OPC mode explicitly with no silent fallback. | ✓ Covered |
| FR49 | **AMENDED -> FR86; NFR41, NFR43-NFR44.** Fit preprocessing on eligible normal training evidence, select on declared validation evidence, and calibrate independently under the same candidate budget. | Epic 13 - Separate physical training, validation, and calibration access. | ✓ Covered |
| FR50 | **AMENDED -> FR87; NFR44.** Freeze the threshold before test and bind its origin and derivation to the immutable detector bundle. | Epic 13 - Freeze and bind the physical threshold before test. | ✓ Covered |
| FR51 | **AMENDED -> FR87; NFR48.** Reject detector candidates when any governing dataset, schema, preprocessing, calibration, bundle, dependency, or runtime identity is stale or incompatible. | Epic 13 - Reject stale or incompatible physical candidates. | ✓ Covered |
| FR52 | **AMENDED -> FR88; NFR43, NFR51.** Report only applicable scenario-, severity-, sensor-, regime-, repetition-, temporal-, and quality-aware metrics under fair budgets, retaining dispersion and limitations. | Epic 13 - Report repeated scenario/regime-aware physical evaluation. | ✓ Covered |
| FR53 | **AMENDED -> FR87; NFR48, NFR52.** Promotion and rollback select an explicit immutable compatible bundle and require separate activity authorization; planning approval cannot promote a model. | Epic 13 - Promote and roll back only explicit authorized physical bundles. | ✓ Covered |
| FR54 | **AMENDED -> FR87; NFR47-NFR48.** Runtime shadow inference loads an exact bundle, never fits, recalibrates, or guesses a latest artifact, and fails closed on absence or incompatibility. | Epic 13 - Serve inference-only physical shadow results without fitting. | ✓ Covered |
| FR55 | **SUPERSEDED -> FR84; NFR40.** Do not acquire HAI 20.07 for the new plan; pin and verify HAI 23.05 instead. | Epic 16 - Replace HAI 20.07 acquisition with pinned HAI 23.05. | ✓ Covered |
| FR56 | **SUPERSEDED -> FR84, FR86; NFR47.** HAI 23.05 native roles and chronology replace HAI 20.07 processing requirements. | Epic 16 - Preserve HAI 23.05 native roles and chronology. | ✓ Covered |
| FR57 | **SUPERSEDED -> FR84, FR87-FR88.** HAI 23.05 receives its own immutable preprocessing, detector, calibration, and evaluation path. | Epic 16 - Keep the HAI 23.05 detector and evaluation dataset-specific. | ✓ Covered |
| FR58 | **SUPERSEDED -> FR84, FR92; NFR38.** Report HAI 23.05 only as external native physical/SCADA evidence, never compressor validation. | Epic 16 - Bound HAI claims to external native physical/SCADA evidence. | ✓ Covered |
| FR59 | **AMENDED -> FR83, FR92; NFR51.** Only qualified official LID evidence may support a locally measured LID result; fixtures and published references remain separate roles. | Epic 15B - Separate LID fixture, published-reference, and official-real roles. | ✓ Covered |
| FR60 | **AMENDED -> FR83; NFR40, NFR50.** Qualify the declared official LID-DS 2021 source, version, layout, citation, license scope, file inventory, sizes, and hashes; no subset is mandatory until separately authorized. | Epic 15B - Qualify the separately authorized official LID source/scope. | ✓ Covered |
| FR61 | **AMENDED -> FR83; NFR47.** Preserve the official LID schema and grouping, reject ambiguous or empty layouts, and never substitute a fixture; no scenario is a default requirement. | Epic 15B - Parse official LID layout with no fixture fallback. | ✓ Covered |
| FR62 | **AMENDED -> FR83, FR86; NFR41.** Split LID by official roles and complete scenario/recording/trace/session groups before vocabulary fitting or windows. | Epic 15B - Split LID by official roles and complete groups. | ✓ Covered |
| FR63 | **AMENDED -> FR83, FR86, FR88; NFR43-NFR44, NFR51.** Execute only the LID scope, run count, stopping rules, and candidate budget declared by a later authorized protocol and report every outcome and limitation. | Epic 15B - Execute only the later-authorized LID scope and report every outcome or an explicit blocked state. | ✓ Covered |
| FR64 | **AMENDED -> FR83, FR86, FR92; NFR51.** Keep author-published LID metrics reference-only and outside fitting, calibration, selection, and local measured result calculations. | Epic 15B - Keep author-published metrics reference-only. | ✓ Covered |
| FR65 | **AMENDED -> FR88, FR92; NFR40, NFR50.** Use a common provenance-rich evaluation envelope without erasing modality- or dataset-specific semantics. | Epic 9 - Define the common provenance-rich evaluation envelope; Epic 17B uses it for the final package. | ✓ Covered |
| FR66 | **AMENDED -> FR92; NFR38.** Produce separate dataset and modality result tables plus a capability/limitation matrix; only the paired custom ablation may compare physical, syscall, and fusion outcomes on the same runs. | Epic 17B - Produce separate result tables and the limitation matrix. | ✓ Covered |
| FR67 | **AMENDED -> FR92; NFR50-NFR51.** Link each academic claim through immutable source, split, bundle, threshold, run, metric, limitation, and scientific-status evidence. | Epic 17B - Produce the immutable claim-to-evidence index. | ✓ Covered |
| FR68 | **AMENDED -> FR92-FR93; NFR50, NFR52.** An optional dashboard may display only frozen custom detector evidence and cannot create, recompute, promote, or alter scientific artifacts. | Epic 18 (optional) - Present frozen custom detector evidence read-only. | ✓ Covered |
| FR69 | **AMENDED -> FR92-FR93; NFR38, NFR51.** Optional presentation keeps HAI, ADFA-LD, and LID native scope, evidence role, result role, version, run, provenance, and limitations distinct. | Epic 18 (optional) - Present benchmark-native scope and limitations. | ✓ Covered |
| FR70 | **AMENDED -> FR93; NFR38, NFR42.** Optional presentation keeps consensus, OPC, SCADA divergence, replay/freeze, physical, syscall, and fusion states distinct and grants none of them control authority. | Epic 18 (optional) - Present distinct consensus, OPC, detector, and fusion states without control authority. | ✓ Covered |
| FR71 | **AMENDED -> FR75, FR87, FR93; NFR52.** An optional dashboard may replay or present only an already authorized preregistered frozen result; it cannot generate, fit, calibrate, promote, fuse, or rewrite evidence. | Epic 18 (optional) - Present only authorized preregistered frozen anomaly evidence without mutation. | ✓ Covered |
| FR72 | The system represents exactly two detection modalities: physical instrumentation and Linux host syscalls. It identifies 4-20 mA as a physical representation and autoencoders as models in contracts, documentation, reports, and any optional UI. | Epic 9 - Establish the global two-modality semantic boundary; all later epics enforce it and Epic 18 may present it. | ✓ Covered |
| FR73 | `SignalObservation.v2` preserves raw current in mA, current quality and diagnostics, instrument/profile identity, source and observation timestamps, sequence/correlation identity, deterministic normalized span, derived engineering value/unit, schema version, and parameter-evidence references; quality is evaluated before optional clipping or imputation. | Epic 10 - Define and preserve `SignalObservation.v2`. | ✓ Covered |
| FR74 | The process model may calculate temperature, pressure, and RPM in engineering units, but an edge receives primary evidence through its selected transmitter profile. Exactly one profile-owned conversion derives normalized span and engineering value from current; RPM remains 4-20 mA while supported by the selected cited shaft-speed profile. | Epic 10 - Separate process physics from profile-owned current derivation. | ✓ Covered |
| FR75 | A versioned `ExperimentSpec` declares phases, profile, run/seed, schedule, interventions, recovery, stopping rules, and evidence references. The requested 25%-75% variation is `speed_reference_pct` or `capacity_reference_pct` classified as `preregistered_factor`; it does not imply power, ramp, dwell, repetition, or safety limits. | Epic 10 - Define `ExperimentSpec` and the 25%-75% preregistered reference. | ✓ Covered |
| FR76 | Every executable v2 numeric parameter has a stable ID and exactly one of `direct`, `derived`, `measured`, `preregistered_factor`, or `mock`. Its record contains value, unit, class-specific authority, exact source/decision/ calibration/mock-admission locator, derivation and input IDs where applicable, selected profile, experiment scope, approval identity, uncertainty/limitation, authentic-reproduction feasibility, exact prototype component, bounded research question, dataset/modality track, affected final-package element, and explicit transferability rationale. Domain claims fail closed on missing, inapplicable, or non-transferable official authority; preregistered factors use the frozen decision as value authority; mocks additionally resolve an immutable approved `MockAdmission.v1`. Anonymous legacy values run only in labelled legacy-reproduction mode. | Epic 9 - Establish the parameter provenance gate; later epics consume it. | ✓ Covered |
| FR77 | `ScenarioTruth.v1`, attack labels, scenario names, interventions, future intervals, and evaluation-only metadata remain under a separate access boundary, absent from detector-facing training and inference contracts, and join frozen evidence only after the declared truth unlock. | Epic 10 - Establish isolated truth and controlled unlock. | ✓ Covered |
| FR78 | The physical track compares LSTM-AE, GRU-AE, and declared simpler or classical baselines fitted only on qualified normal training evidence under the same current-domain schema, complete-run partitions, budget, repetitions, and metrics. The current mixed-scale autoencoder is `LEGACY_BASELINE`, not the final detector or a dataset, and commanded 25%-75% transitions remain distinct from declared anomalies. | Epic 13 - Compare physical custom candidates; Epic 16 applies the fair candidate protocol to HAI. | ✓ Covered |
| FR79 | The custom syscall track runs an allowlisted controlled Linux edge workload and captures the authentic kernel calls it actually emits through a qualified Sysdig/eBPF or equivalent collector. Every workload behavior the approved prototype can reproduce executes authentically. Only a specifically unavailable behavior may use an approved `MockAdmission.v1`; convenience, cost, timing, or an unfavorable result is insufficient. Syscalls are never fabricated, renumbered, modified, or substituted. | Epic 14 - Run a controlled workload and capture authentic kernel calls. | ✓ Covered |
| FR80 | `SyscallEventBatch.v1` preserves run, edge, boot, container/process/session, categorical syscall name/direction, sequence/timestamps, kernel/ABI and collector identities, loss/duplicate/gap/queue evidence, and raw-segment hashes without labels or scenario truth. Fixture replay is test-only and excluded from formal custom evaluation. | Epic 14 - Define and preserve `SyscallEventBatch.v1`. | ✓ Covered |
| FR81 | The syscall anomaly track treats calls categorically and compares embedding-plus-LSTM, embedding-plus-GRU, and a transparent n-gram/STIDE-style baseline fitted on qualified normal evidence under the same group-safe protocol. Numeric syscall IDs are not continuous quantities and are not optimized with reconstruction MSE solely because they are numbers. | Epic 14 - Compare custom categorical syscall candidates; Epics 15A and 15B apply compatible candidate families to external syscall benchmarks. | ✓ Covered |
| FR82 | ADFA-LD remains an offline external syscall benchmark with official roles, trace identity, six attack families, source/archive hashes, known count discrepancies, categorical semantics, and labels confined to evaluation truth; the system neither fabricates timestamps nor executes dataset identifiers. | Epic 15A - Preserve and evaluate ADFA-LD in its external syscall role. | ✓ Covered |
| FR83 | A version-specific LID-DS 2021 adapter preserves official training/validation/test and scenario/recording boundaries plus the published syscall schema. LID may inform custom capture design, but its example durations, collector settings, and metrics remain cited references, not project constants. | Epic 15B - Preserve and evaluate the separately authorized LID-DS 2021 scope through its official schema. | ✓ Covered |
| FR84 | The system pins and verifies HAI 23.05, preserves native tags, units, chronology, official file roles, and separate labels, and uses a version-specific physical/SCADA adapter. Its preprocessing, detector, calibration, and evaluation remain separate; HAI is neither mass-converted to mA nor presented as compressor data. | Epic 16 - Preserve and evaluate HAI 23.05 in its native physical domain. | ✓ Covered |
| FR85 | `PTFP-Custom-v1` contains synchronized physical observations and captured Linux edge syscalls from the same experiment runs, immutable stream manifests, clock/correlation evidence, modality quality, profile/config identities, and separately protected truth. Custom rows are never inserted into or represented as HAI, ADFA-LD, or LID-DS data. | Epic 17A - Publish synchronized `PTFP-Custom-v1` from the physical and authentic-syscall producers delivered by Epics 10 and 14. | ✓ Covered |
| FR86 | Complete official groups or independent custom runs split before windowing. Preprocessing/vocabulary fitting uses training only; selection/thresholding uses declared validation/calibration only; and locked test evidence remains unavailable until model, schema, preprocessing, threshold, metrics, and policy are frozen. | Epic 9 - Define the leakage-safe lifecycle; Epics 13-17A enforce it for their tracks and Epic 17B verifies it in the final evidence chain. | ✓ Covered |
| FR87 | Every evaluated or deployed detector bundle immutably binds weights and architecture, feature order/schema or vocabulary, preprocessing, training/calibration dataset and split hashes, frozen threshold and derivation, dependency/runtime identity, and bundle hash. Load and inference never call `fit` or recalculate a threshold. | Epic 9 - Define immutable bundle/evidence identities; Epics 13-17A produce exact bundles and scores. | ✓ Covered |
| FR88 | Each track reports all applicable point/window and event/range outcomes, including PR-AUC, precision, recall, F1, false-positive behavior, false events per operating hour, time to detection, suitable confusion data, threshold sensitivity, resource cost, modality quality/availability, and repeated-run dispersion or uncertainty. Unfavorable and aborted planned runs remain visible. | Epic 9 - Define the evaluation envelope; Epics 13-17A generate track-specific outcomes and Epic 17B reports them completely. | ✓ Covered |
| FR89 | Late fusion uses only frozen calibrated physical and syscall scores from aligned windows of the same held-out `PTFP-Custom-v1` runs under a simple preregistered policy before truth unlock. External ADFA/LID syscall records are never joined with HAI physical rows to fabricate fusion. | Epic 17A - Execute only preregistered custom same-run late fusion. | ✓ Covered |
| FR90 | The OPC UA server receives a pre-consensus plant/transmitter snapshot and a distinct client reads it through `opc.tcp`, preserving `DataValue` status, source/server timestamps, schema, and correlation. Invalid, stale, mixed, missing, or unavailable evidence fails explicitly with no silent consensus fallback. | Epic 12 - Deliver independent fail-closed OPC UA evidence. | ✓ Covered |
| FR91 | Consensus v2 declares the instrument profile and comparison basis. Same-profile redundant observations may compare in current domain; cross-profile or cross-sensor aggregation uses documented dimensionless, uncertainty-aware residuals. Python and Go produce deterministic identical results from shared golden fixtures. | Epic 11 - Deliver deterministic current-domain consensus v2. | ✓ Covered |
| FR92 | The final package contains separate ADFA-LD, LID-DS 2021, HAI 23.05, and per-modality `PTFP-Custom-v1` tables, then a paired custom-only physical/syscall/fusion ablation and capability/limitation matrix. It selects no global cross-domain champion, and every claim resolves to source, version, split, bundle, threshold/calibration, run, raw score/metric, and limitation. | Epic 17B - Deliver the separate result tables, paired ablation, limitation matrix, and claim evidence; Epic 18 may only project them. | ✓ Covered |
| FR93 | **CONDITIONAL/OPTIONAL.** If Epic 18 is activated, a read-only dashboard displays raw mA, normalized span, and engineering value as linked physical representations; physical, syscall, and fusion channels separately; and scope, provenance, quality, bundle, threshold origin, and limitations. It cannot import, split, train, calibrate, promote, fuse, relabel, recompute, or rewrite results and is not an implementation-readiness gate. `legacy_demo` may show live/current state only with persistent `DEMO - NOT PUBLISHED SCIENTIFIC EVIDENCE` status. `frozen_evidence` reads one explicitly selected immutable `G9_PASS` package, never a mutable `latest` identity, exposes no control route, and rejects mutation requests server-side. Dashboard absence, styling, or disagreement cannot block or alter scientific Epics 9-17B. | **NOT FOUND** | ❌ MISSING |

### Missing Requirements

None. No PRD FR is absent from the controlling epic coverage map, and the epic
map contains no FR identifier outside the controlling PRD range.

### Coverage Statistics

- Total PRD FRs: **93**.
- FRs covered in epics: **93**.
- Missing PRD FRs: **0**.
- Extra epic-map FR identifiers not present in the PRD: **0**.
- Coverage percentage: **100.0%**.

**Result: PASS.** Every controlling functional requirement has a declared epic
implementation path. This step validates traceability only; story quality is
assessed separately.

## UX Alignment Assessment

### UX Document Status

**Found:** `_bmad-output/planning-artifacts/ux-design-specification.md` is a
complete whole-document UX specification. It is explicitly optional guidance
for Epic 18 rather than an implementation-readiness prerequisite.

### UX to PRD Alignment

**PASS.** The controlling UX boundary aligns with FR68-FR71 and FR92-FR93:

- exactly two modalities remain visible and separate;
- raw current, normalized span, and engineering value remain linked physical
  representations;
- `legacy_demo` carries the persistent non-scientific label;
- `frozen_evidence` loads one explicitly selected immutable `G9_PASS` package;
- missing, blocked, invalid, unavailable, and mock-derived states remain
  visible rather than being filled or improved;
- the dashboard performs no training, calibration, fusion, evaluation,
  relabelling, experiment control, or scientific mutation; and
- absence or non-activation of Epic 18 does not block the scientific package.

No UX requirement introduces a new controlling PRD capability.

### UX to Architecture Alignment

**PASS.** The architecture retains the existing Python-served local dashboard
surface and read-model/artifact boundaries, so the optional single-page
projection needs no new service, database, framework, build system, or control
plane. The controlling architecture independently requires server-side
rejection of mutation routes in `frozen_evidence`; hiding controls in the
browser is not treated as enforcement. Headless reconstruction and all G1-G9
scientific gates remain independent of presentation availability.

### Alignment Issues

No controlling misalignment was found.

### Warnings

Nonblocking historical prose remains in both documents. Later UX sections
still use generic "live/current/most recently published" language, and the
historical v1 architecture describes a final demo layer with controls. Their
respective controlling-reading and optional-mode sections explicitly limit
that language to `legacy_demo` and supersede control-surface guidance for Epic
18. A future editorial cleanup would reduce reader friction, but no
implementation ambiguity or readiness blocker remains.

**Result: PASS.** UX is present, proportionate to the academic prototype,
architecturally supported, and fully optional.

## Epic Quality Review

### Epic Structure and Dependency Validation

| Epic | User/researcher outcome | Declared prerequisites | Stories | Result |
| --- | --- | --- | ---: | --- |
| 9 | Reconstruct and trust the brownfield baseline and its evidence | Historical Epics 1-7 | 8 | PASS |
| 10 | Produce qualified physical experiment evidence | Epic 9 | 7 | PASS |
| 11 | Obtain deterministic current-domain consensus evidence | Epics 9-10 | 6 | PASS |
| 12 | Compare against genuinely independent OPC UA evidence | Epics 9-11 | 6 | PASS |
| 13 | Compare, calibrate, evaluate, and shadow-serve a physical detector | Epics 9-10 | 8 | PASS |
| 14 | Capture authentic Linux syscalls and evaluate categorical detectors | Epics 9-10 | 9 | PASS |
| 15A | Reproduce ADFA-LD in its native external benchmark role | Epic 9 | 6 | PASS |
| 15B | Qualify/evaluate LID-DS 2021 or publish an honest blocked state | Epic 9 | 7 | PASS |
| 16 | Evaluate HAI 23.05 in its native physical/SCADA domain | Epic 9 | 7 | PASS |
| 17A | Produce synchronized custom evidence and paired late-fusion results | Epics 9, 10, 13, 14; optional declared 11/12 evidence | 7 | PASS |
| 17B | Publish a reconstructible, claim-linked academic evidence package | Earlier independent results plus an explicit LID outcome | 6 | PASS |
| 18 | Optionally project published evidence in the existing dashboard | Epic 17B; terminal and optional | 4 | PASS |

Every epic expresses a researcher, evaluator, reviewer, or operator outcome;
none is merely a database, API, UI, or infrastructure milestone. All required
dependencies point backward. References to later epics describe optional
future consumption and do not withhold the current epic's outcome. No circular
or forward story dependency was found.

### Story Structure and Sizing

- Stories reviewed: **81/81**.
- Stories with complete `As a` / `I want` / `So that` structure: **81/81**.
- BDD scenarios: **510** total; every scenario contains matched
  `Given` / `When` / `Then` clauses.
- Scenario count per story: **5-12**.
- Explicit story-to-future-story references: **0**.
- FR traceability is present on every story.
- Happy paths, invalid or unavailable evidence, identity mismatch, leakage,
  blocked execution, and fail-closed outcomes are represented throughout.

Story 9.4 is the largest item at 12 scenarios and 109 lines. It remains one
cohesive deliverable: the `ParameterEvidence.v1` catalog and its class-aware
validation gate. Splitting the classes into separate stories would weaken the
single fail-closed invariant, so its size is acceptable; Sprint Planning may
re-estimate it without changing its acceptance boundary.

### Brownfield and Data-Structure Checks

This is a brownfield continuation, not a greenfield bootstrap. The controlling
architecture preserves the existing Python and Go runtime, so the historical
`uv init --bare` starter instruction does not require a new Epic 9 setup story.
Story 9.1 correctly begins with reconstruction and freezing of the working v1
baseline. No new database is introduced, and contracts/storage objects are
created only where their first evidence-producing story needs them.

### Academic-Veracity and Mock-Admission Quality Check

**PASS.** The cross-epic guardrail applies to every story and names the three
non-interchangeable authorities: `DecisionRecord.v1`,
`ParameterEvidence.v1`, and `MockAdmission.v1`.

- The only admitted planning mock is the bounded physical signal emulator.
  Its record states the unavailable real-hardware path, exact official
  locators, supported behavior, transfer rationale, prototype component,
  bounded question, tracks, final outputs, prohibited claims, and replacement
  condition. Authentic Linux workload execution and captured kernel calls are
  explicitly excluded from the admission.
- The parameter catalog contains **15** records with no missing
  component/question/track/final-output/transferability field.
- Three unresolved values remain honestly blocked: the pressure profile until
  official source bytes are archived, and the RPM lower/upper endpoints until
  a preregistered decision freezes them. No legacy fallback is allowed.
- The official Danfoss programming guide is locally archived and its recorded
  SHA-256 matches the file. Direct 4/20 mA values, researcher-selected 0/100
  mapping, researcher-selected 25/75 factors, and derived 8/16 mA values retain
  distinct authority classes.
- All **20** inventoried legacy constants are disabled for formal v2 and
  limited to exact labelled v1 reproduction.

These blocked parameter records are intentional execution gates, not missing
planning decisions disguised as defaults. Their stories require fail-closed
resolution before any affected formal activity.

### Critical Violations

None.

### Major Issues

None.

### Minor Concerns

- The Epic 14 summary note says broadly that the workload "may be mocked."
  Story 14.1, the cross-epic guardrail, PRD, and architecture narrow this to a
  specifically unavailable behavior backed by a complete admission record;
  convenience, cost, timing, or unfavorable authentic results are rejected.
  This is noncontrolling editorial shorthand, but tightening it later would
  reduce reader friction.
- Historical v1 terminology remains elsewhere in the planning documents. The
  consolidated controlling sections resolve authority, so this is editorial
  debt rather than an implementation defect.

**Result: PASS.** No structural, dependency, sizing, acceptance-criteria, or
academic-veracity defect blocks implementation planning.

## Summary and Recommendations

### Overall Readiness Status

# READY

The controlling PRD, architecture, epics/stories, and optional UX specification
are mutually aligned and sufficiently complete for Sprint Planning. The earlier
`NOT READY` result is resolved by the 2026-08-22 controlling consolidations,
evidence records, mock-admission boundary, source archival, and story revisions.

Readiness authorizes planning only. It does not authorize implementation,
dataset acquisition, model training, syscall capture, experiment execution,
dashboard activation, deployment, control, or publication.

### Assessment Summary

- Document set: complete, unambiguous controlling whole documents; dated
  overlays are historical traceability only.
- PRD: **93 FRs and 52 NFRs**, with no missing or duplicate controlling IDs.
- Epic coverage: **93/93 FRs, 100.0%**.
- UX: aligned, technically supported, proportionate, and optional.
- Epics/stories: **12 epics, 81 stories, 510 matched BDD scenarios**; no forward
  or circular dependency.
- Academic veracity: one bounded conditional physical-emulator admission;
  authentic syscalls remain mandatory; 15 parameter records retain distinct
  authority classes; 20 legacy constants are quarantined from formal v2.
- Critical violations: **0**.
- Major issues: **0**.
- Nonblocking editorial concerns: **2**.

### Critical Issues Requiring Immediate Action

None for Sprint Planning.

The following are deliberate **execution gates**, not readiness defects:

1. archive and hash the exact official Siemens P200 source before activating
   the pressure profile;
2. freeze the FB420 RPM lower endpoint in a pre-test `DecisionRecord.v1`; and
3. freeze the FB420 RPM upper endpoint in the same or a compatible pre-test
   decision.

Any affected formal profile, experiment, or result remains blocked until those
records validate. No default, legacy value, convenient mock, or adjacent source
may bypass the block.

### Recommended Next Steps

1. Proceed to BMAD Sprint Planning using `prd.md`, `architecture.md`, and
   `epics.md` as the sole controlling planning inputs and this report as the
   readiness gate.
2. Schedule Epic 9 first and treat G1 provenance as the initial implementation
   gate. Preserve the separation among source evidence, researcher decisions,
   parameter derivations/measurements, and exceptional mock admissions.
3. Resolve the three blocked parameter records before scheduling any affected
   formal physical acquisition or campaign activity; independent stories and
   external tracks may proceed according to their declared dependencies.
4. Keep Epic 18 out of the scientific critical path. Activate it only if the
   lightweight demonstration is desired; retain the persistent
   `legacy_demo` warning or the immutable read-only `frozen_evidence` mode.
5. During story implementation, require separate activity authorization and
   enforce G1-G9 fail-closed. An unfavorable or unavailable result is reportable
   evidence and never justification for a fallback or fabricated value.

### Final Note

This assessment found no critical or major planning issue. Two minor editorial
concerns remain in superseded/historical prose, while three unresolved values
are transparently blocked by design. They do not prevent Sprint Planning
because the controlling contracts and stories define exact owners, resolution
paths, and fail-closed consequences.

The project is **READY for Sprint Planning** and remains **not authorized for
implementation or scientific execution** until the corresponding later
authorizations are issued.
