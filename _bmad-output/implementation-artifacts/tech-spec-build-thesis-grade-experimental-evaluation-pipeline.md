---
title: 'Build a Thesis-Grade Experimental Evaluation Pipeline'
type: 'feature'
created: '2026-09-14'
status: 'in-review'
execution_mode: 'plan-code-review'
spec_loop_iteration: 4
baseline_commit: '430089801e4d7eb3625710e842e14993241aab1d'
context:
  - '_bmad-output/planning-artifacts/academic-evidence-admission-amendment-2026-08-31.md'
  - 'docs/results-of-the-prototype.md'
  - 'C:/Users/emili/Downloads/PAPER - DECENTRALIZED FEDERATED LEARNING-BASED INTRUSION DETECTION IN IOT SYSTEMS.pdf'
---

# Build a Thesis-Grade Experimental Evaluation Pipeline

<frozen-after-approval reason="human-owned intent - do not modify unless human renegotiates">

## Intent

**Problem:** The report contains integration-smoke evidence: one selected run per dataset, one-epoch/tiny-support cells, and no score, threshold, dispersion, or uncertainty analysis. The earlier ADFA-LD binary result is inadmissible for generalization because windows from 99.77% of tested attack traces also entered training.

**Approach:** Preserve the demo and add a separate academic path using native group-safe partitions, validation-frozen preprocessing/models/thresholds, complete run retention, and dataset-specific statistical reporting. Follow Assis's breadth while adding leakage and uncertainty controls.

## Boundaries & Constraints

**Always:** Keep official datasets and custom modalities separate; split independent units before windowing; use validation only for selection, stopping, and calibration; persist hashes, seeds, unit IDs, scores, predictions, thresholds, resource measures, failures, and all planned cells; distinguish epochs, cycles, trials, windows, and bootstrap replicates; label pilot versus confirmatory evidence.

**Ask First:** Add an external dataset, change live control/consensus behavior, run a matrix estimated above 12 CPU-hours, or broaden claims beyond official benchmarks and controlled-prototype evidence.

**Never:** Tune on test truth; leak units across partitions; publish only champions; aggregate incompatible tracks; call simulation real-plant validation; suppress unfavorable results; overwrite legacy evidence.

## I/O & Edge-Case Matrix

| Scenario | Input / State | Expected Output / Behavior | Error Handling |
|----------|--------------|---------------------------|----------------|
| Legacy audit | Existing reports/runs | Each result classified as smoke, exploratory, or admissible | Missing raw evidence stays explicit |
| Benchmark | Official units/partitions | Immutable manifest; windows built after a zero-overlap split | Abort track on missing groups, labels, hashes, or support |
| Detector | Validation/test scores | Frozen validation-derived threshold and untouched test metrics | Reject test-derived/incompatible thresholds |
| Matrix | Complete/interrupted cells | All runs plus uncertainty and paired comparisons | Retain failures; resume by immutable identity |
| Rare class | Low/zero support | Support and availability remain visible | Emit undefined with reason, not zero |

</frozen-after-approval>

## Code Map

- `.../offline_training/academic_protocol.py` -- units, splits, post-split windows, leakage audit.
- `.../offline_training/academic_models.py` -- recurrent/autoencoder and transparent baselines.
- `.../offline_training/academic_metrics.py` -- calibration, uncertainty, effects, paired tests.
- `.../offline_training/academic_runner.py` -- resumable execution and immutable artifacts.
- `.../offline_training/academic_report.py` -- separated results, audit, ablations, limitations.
- `scripts/run_academic_experiments.py` -- preflight, pilot, confirmatory, report CLI.
- `configs/experiments/thesis-evaluation-v1.json` -- preserved exploratory-v1 matrix; never promote or overwrite.
- `configs/experiments/thesis-evaluation-v2.json` -- corrected matrix, disjoint phase allocation, and statistical protocol.
- `configs/experiments/thesis-evaluation-v2.parameter-requirements-v2.1.json` -- exhaustive schema-bound numeric-consumer inventory; unresolved authority blocks execution/claims. Prior inventory revisions remain preserved as historical evidence.
- `scripts/build_academic_parameter_requirements.py` -- deterministic, atomic requirements generation that refuses to erase authority-bearing slots.
- `.../contracts/parameter_evidence.py` and `.../evidence/parameter_evidence.py` -- controlling numeric-authority contract and fail-closed validator.
- `tests/lstm_service/offline_training/test_academic_*.py` -- scientific and regression tests.
- `_bmad-output/implementation-artifacts/academic-parameter-evidence-closure-plan.md` -- candidate human-decision groups, impacts and alternatives; grants no authority.
- `_bmad-output/implementation-artifacts/deferred-work.md` -- unresolved architectural findings that are not waived by this iteration.

## Tasks & Acceptance

**Execution:**
- [ ] Preserve v1 cells/reports as exploratory diagnostic evidence and prevent their promotion into v2.
- [ ] Bind every executable numeric slot to an immutable, validated `ParameterEvidence.v1` revision/hash; missing, stale, incompatible, or invented authority must fail closed.
- [ ] Attach exactly one closed `evidence_origin` to every benchmark unit, prediction, result, and displayed claim; official benchmarks require `official_native`.
- [ ] Make pilot and confirmatory units disjoint by immutable model-input identity, including normalized ADFA sequences, detector-visible LID streams, and content/time-aware HAI groups.
- [ ] Add preflight for support, native partitions, historical admissibility, estimated cost, and leakage.
- [ ] Add group/time-safe protocols and post-split windowing without altering legacy adapters.
- [ ] Add model/baseline scores, validation-only thresholds, classification/ranking/event metrics, uncertainty, and resource measures.
- [ ] Add a resumable runner retaining predictions/failures. Freeze exactly 50 unique confirmatory seeds for every genuinely stochastic model, execute them non-adaptively in five immutable positional batches of ten, and execute each deterministic dataset/model cell once per phase.
- [ ] Use the five pilot trials only to estimate and disclose dispersion and the uncapped theoretical repetition need. Report the 50-trial cap, whether it is reached/binding, projected confidence-interval half-width at 50, and whether the target is projected to be met; never let that estimate shorten the frozen confirmatory schedule or imply that 50 repairs too few independent units.
- [ ] Withhold confirmatory outcome aggregation, inferential tables, comparisons, figures, and report claims until the entire frozen matrix is authenticated; intermediate batch artifacts expose progress/integrity/failures only and cannot alter later batches.
- [ ] Require a complete, known cost projection for the full five-batch protocol. An explicit over-budget authorization may waive only a known estimate above 12 CPU-hours, never an absent or incomplete estimate.
- [ ] Report all cells, per-class and ROC/PR results, score/threshold distributions, confusion matrices, convergence, ablations, comparisons, costs, limitations, and hashes.
- [ ] Execute preflight, pilot, and the feasible confirmatory matrix; publish a thesis-readiness verdict.
- [ ] Publish immutable cell and prediction artifacts transactionally under concurrent writers, with crash recovery that never admits an orphaned half-pair; close the inventory writer's final check/replace race against non-cooperating writers.
- [ ] Persist authenticated calibration rows and reconstruct thresholds, predictions, classification/ranking/class/event metrics, curves, and bootstrap outputs independently from raw evidence before admitting a cell or report.
- [ ] Define and enforce a complete typed v2 numeric-consumer schema, rejecting omitted execution defaults, booleans, numeric strings, unknown numeric leaves, and inventory/schema drift.
- [ ] Recompute pilot repetition planning exclusively from authenticated pilot cells and raw primary outcomes, never from editable derived summaries.
- [ ] Enforce preregistered class-carrying cluster support and valid-replicate criteria for mixed-label cluster bootstrap inference.
- [ ] Reject non-finite, non-integral, and out-of-domain labels before any integer conversion.
- [ ] Fit categorical vocabulary/cardinality from training metadata only and route unseen validation/test identifiers through one frozen unknown token.

**Acceptance Criteria:**
- Given a numeric consumer, when preflight resolves its configuration, then the exact `ParameterEvidence.v1` revision/hash, value, unit, authority locator, scope, and derivation lineage are present and valid or the affected result/claim is blocked.
- Given an official benchmark record/result/claim, when serialized or displayed, then its sole `evidence_origin` is `official_native`; custom evidence remains in its own closed origin and track.
- Given pilot and confirmatory phases, when manifests are frozen, then their independent unit identities are disjoint and pilot truth cannot expose a confirmatory test observation.
- Given source units, when splits/windows are built, then each unit occurs in one partition and the leakage audit passes.
- Given validation data, when testing begins, then preprocessing, model, and threshold identities are frozen and test truth cannot affect them.
- Given a planned matrix, when execution ends or stops, then every cell has raw outputs or an explicit failure and can resume safely.
- Given the v2 confirmatory matrix, when it is frozen, then every stochastic dataset/model family has the same ordered 50-seed schedule partitioned into five non-overlapping ten-seed batches, every deterministic dataset/model cell appears once per phase, and the stored plan authenticates seed position and batch identity.
- Given a pilot repetition analysis, when fewer than all five primary outcomes are finite, then precision planning is indeterminate and confirmatory execution remains blocked; otherwise the uncapped need is computed prospectively, the projection at the fixed cap of 50 is explicit, and execution still uses all 50 seeds.
- Given an incomplete confirmatory matrix, when a batch completes or a report is requested, then only audit/progress/failure information is published and no outcome aggregate, comparison, or figure is emitted.
- Given a confirmatory launch, when computational cost is checked, then the projection covers all five invocations and is complete and known; only an explicit authorization can allow a known total above 12 CPU-hours.
- Given repeated runs, when reported, then estimates include support, dispersion, confidence intervals, effect, paired significance, and multiplicity policy.
- Given HAI recording-cluster uncertainty, when fewer than the required independent recordings are available, then the interval is undefined with the observed and required counts and reason displayed; across-seed training variability remains separately labelled and cannot substitute for recording independence.
- Given anomaly scores, when reported, then calibration/value, score direction/distribution, AUROC, AUPRC, operating-point confusion metrics, FPR/FNR, and sensitivity are reconstructible.
- Given distinct tracks, when published, then each has its own protocol/table/limits and no global champion is implied.
- Given a cell publication interrupted at any write boundary or racing another writer, when recovery/admission runs, then exactly one authenticated prediction/cell pair is visible, partial transactions are quarantined or completed deterministically, and no approved inventory is replaced after its final integrity check.
- Given persisted calibration and test rows, when a cell or report is admitted, then an independent reconstruction from authenticated unit IDs, truths, scores, and clusters reproduces the frozen threshold, predictions, confusion/ranking/class/event metrics, curves, and bootstrap outputs or admission fails closed.
- Given any executable v2 numeric consumer, when configuration is loaded or inventory is generated, then it belongs to the explicit typed schema and has an exact inventory slot; Boolean coercion, numeric strings, implicit numeric defaults, unknown numeric leaves, and schema/inventory drift are rejected.
- Given completed pilot cells, when repetition planning is authenticated, then every primary outcome is recomputed from authenticated cell/raw evidence and a modified summary field cannot alter the plan.
- Given recording-cluster bootstrap inference, when support or resampling is evaluated, then both classes have the preregistered number of class-carrying independent clusters and the required count/fraction of valid mixed-label replicates is met; otherwise the interval is undefined with a reason.
- Given source labels, when protocol arrays are constructed, then non-finite, fractional, Boolean, or unsupported labels fail before integer conversion.
- Given categorical validation/test tokens absent from training, when preprocessing and the recurrent architecture are frozen, then vocabulary size comes only from train-fitted metadata and every unseen identifier maps to the same reserved unknown token without expanding cardinality.

## Design Notes

The claim unit is an independent trace, recording, temporal block, event, or campaign pair - never an overlapping window. Assis supplies the presentation scaffold; this path adds trials, frozen calibration, uncertainty, effects, multiplicity control, and raw predictions.

## Verification

**Commands:**
- `$env:PYTHONPATH='src'; .\.venv\Scripts\python.exe -m pytest -q tests\lstm_service\offline_training` -- all academic tests pass from a source checkout.
- `.\.venv\Scripts\python.exe scripts\run_academic_experiments.py preflight --phase confirmatory --config configs\experiments\thesis-evaluation-v2.json` -- authority, provenance, time alignment, phase disjointness, zero-leakage, repetition-planning, and full-protocol cost gates are explicit. This mandatory standalone check plus the fresh check inside each of the five batch invocations are all included in the cost projection.
- `.\.venv\Scripts\python.exe scripts\run_academic_experiments.py pilot --config configs\experiments\thesis-evaluation-v2.json` -- executes only after numeric authority closes; otherwise persists an explicit blocked preflight.
- After numeric authority closes, pilot planning is determinate, and any required over-budget approval is explicit, run the confirmatory invocations separately and in order: `confirmatory --seed-batch 1`, then `confirmatory --seed-batch 2`, through `confirmatory --seed-batch 5`, always with the same v2 config and without dataset/model filters or interim outcome analysis. A nonzero exit stops the sequence; it does not authorize later batches.
- `.\.venv\Scripts\python.exe scripts\run_academic_experiments.py report --phase confirmatory --config configs\experiments\thesis-evaluation-v2.json` -- reconstructs only authenticated cells, authenticates the frozen five-batch ledger, withholds incomplete outcomes, and cannot promote v1 artifacts.

## Spec Change Log

### Iteration 2 — acceptance/adversarial correction (2026-09-15)

**Trigger:** Three independent reviews found that exploratory v1 artifacts were complete but not academically admissible. The controlling admission amendment was not fully represented in the original task list.

**KEEP:** Separate academic path; raw scores/predictions; validation-derived operating points; group-before-window construction; per-dataset reporting; complete unfavorable-result retention; preserved v1 evidence; pilot/confirmatory labels.

**Known-bad v1 evidence:** `thesis-evaluation-v1` remains an immutable exploratory diagnostic. It must not be relabelled, copied into v2, or used as confirmatory evidence. In particular, its HAI block-bootstrap intervals and deterministic-involving significance rows are rejected for inference.

**Corrections:** Add fail-closed numeric authority and evidence-origin closure; disjoint pilot/confirmatory allocations; calibration-before-test lifecycle; train-only identities; timestamp and finite-value guards; event/recording-clustered HAI uncertainty; genuine-seed-only inference; pilot-derived confirmatory repetitions; exhaustive failure and resume integrity; complete code/environment provenance; exact eligibility; dataset-specific protocol/hyperparameter tables.

**Execution consequence:** Technical correction and verification may proceed. No confirmatory matrix may run until authority closure passes and the total estimated CPU cost is at most 12 hours or the user explicitly authorizes the larger run.

### Iteration 3 — fixed-cap confirmatory hardening (2026-09-20)

**Trigger:** The requested 50-seed confirmatory protocol exposed an intent gap: the implementation still used a 30-seed cap, allowed the pilot recommendation to truncate execution, had no immutable five-batch ledger, published partial-batch analyses, and allowed an over-budget switch to bypass unknown cost.

**KEEP:** All frozen intent and boundaries; v1 isolation; fail-closed numeric authority; disjoint pilot/confirmatory allocations; validation-only selection/calibration; raw predictions and complete failure history; dataset-specific inference; Assis as presentation structure only.

**Known-bad current behavior:** The pre-correction v2 configuration and inventory describe 30 confirmatory seeds; the runner slices that list using a pilot-derived recommendation; partial resumes overwrite the canonical summary with interim analysis; and the CLI budget override also accepts missing/incomplete projections. Those behaviors are not admissible under this iteration.

**Corrections:** Freeze 50 unique stochastic seeds and five positional batches of ten; validate implementation-owned randomness classifications; run deterministic cells once per phase; require all five finite pilot primary outcomes for a descriptive planning estimate; calculate the prospective uncapped need and projection at 50 without adapting execution; withhold outcome analysis until exact-matrix completion; distinguish seed uncertainty from HAI recording-cluster uncertainty; and enforce complete known cost at both CLI and runner boundaries, including the mandatory standalone preflight plus the five batch-local revalidations.

**Execution consequence:** Regenerate the exhaustive numeric-consumer inventory and its hash with all new bindings unresolved. Technical tests may proceed, but scientific execution remains blocked until human-approved numeric authority closes. After closure, confirmation must be invoked batch-by-batch without dataset/model filters or between-batch adaptation.

**Review closure (2026-09-21):** The Iteration 3 adversarial pass additionally closed strict prior-batch authentication, duplicate-cell rejection, full cell-content plus planned-matrix analysis identity, cumulative pilot CPU accounting across resumes, planned-epoch/early-stopping cost scaling, the mandatory standalone plus five batch-local preflight invocations, report-side cost/failure/plan revalidation, stale-figure removal, audit-only metadata allowlists, early CLI option rejection, and atomic authority-preserving inventory regeneration. Numeric quantity semantics now distinguish repetitions, sample counts, sample offsets and window counts. The regenerated inventory contains 201 unresolved slots and is bound by `sha256:b05f19b9c18199f87d9f950226e89d171f39efe2bdfdb068d6c624b69a2947a0`; no authority record was invented.

**Final static hardening (2026-09-22):** The closing audit bound the persisted confirmatory batch ledger to the configuration and final admission, rejected extra/duplicate logical artifacts before later batches, reconstructed displayed batch progress from the config-derived plan and authenticated artifacts, separated a scheduled cap from a cap actually reached by completed trials, and rejected symlinked cell, prediction and report inputs/outputs. Non-cooperating concurrent writers remain an explicit transactional-publication item in `deferred-work.md`; the cooperative inventory lock is not represented as a complete concurrency proof.

**Acceptance interpretation:** Paired significance is required only where genuine matched stochastic repetitions exist on both sides. A deterministic-involving comparison remains descriptive with the inferential fields explicitly undefined; duplicating a deterministic estimate across seed labels would create false replication and is prohibited. This is not repaired by adding artificial deterministic runs.

**Residual boundary:** The review findings recorded in `deferred-work.md` remain blocking design work for complete evidence reconstruction and numeric-schema closure; they are not silently treated as accepted. The candidate approval sequence and exact decision alternatives are documented in `academic-parameter-evidence-closure-plan.md`. Technical verification comes first, and no v2 preflight or scientific execution is authorized by these implementation changes.

### Iteration 4 — evidence reconstruction and schema closure (2026-09-22)

**Trigger:** The user authorized the remaining technical work required before generating thesis numbers. The residual review findings are code-identity-changing admission defects and therefore cannot remain deferred until after pilot execution.

**KEEP:** Every Iteration 2/3 safeguard; the immutable 50-seed/five-batch schedule; v1 isolation; raw result retention; validation-only calibration; exact-matrix withholding; authenticated cost governance; the unresolved human authority gate; and the prohibition on scientific execution by the agent.

**Known-bad state avoided:** Independent cell/prediction writes can strand half-published evidence; derived metrics and pilot summaries can be trusted without raw reconstruction; numeric consumers can evade an inferred inventory through defaults/coercion; invalid labels can be silently truncated; bootstrap intervals can be produced without adequate class-carrying clusters; and categorical cardinality can learn from validation/test identifiers.

**Corrections:** Make publication recoverable and concurrency-safe; make raw calibration/test rows the reconstructible source of truth; close a typed, exhaustive numeric schema; derive pilot planning from authenticated cells; formalize cluster-bootstrap validity; validate labels before conversion; and freeze categorical vocabulary from training metadata with a reserved unknown token.

**Execution consequence:** Return the specification to implementation. Regenerate the requirements inventory only after schema closure, then request the manual academic test command. Pilot, confirmatory preflight, matrix execution, report generation, and human parameter approvals remain outside this coding pass.
