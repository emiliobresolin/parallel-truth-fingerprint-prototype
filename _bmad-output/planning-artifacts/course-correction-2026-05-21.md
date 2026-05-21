---
type: course-correction
date: 2026-05-21
triggered_by: orientation meeting with advisor (Prof. Fabiano)
status: approved-by-user-for-planning-only
applies_to:
  - _bmad-output/planning-artifacts/prd.md
  - _bmad-output/planning-artifacts/architecture.md
  - _bmad-output/planning-artifacts/epics.md
  - _bmad-output/planning-artifacts/requirements.md
scope_decision: planning-only (no code changes yet)
---

# Course Correction — 2026-05-21

This document records a major mid-implementation course correction triggered by
the orientation meeting with the advisor (Prof. Fabiano) and approved by the
user (Emilio) on 2026-05-21. It is the single authoritative entry point for the
pivot of the LSTM/fingerprint stage of the prototype. All downstream documents
(`prd.md`, `architecture.md`, `epics.md`) must be updated to reflect the
decisions captured here.

The pivot does not change Epics 1–3 (sensor simulation, edge nodes, Byzantine
consensus, SCADA comparison, MinIO persistence). It rewrites the assumptions of
Epic 4 (LSTM training, inference, fingerprint lifecycle) and adds a new
benchmark-driven offline training track.

## 1. Trigger

During the orientation meeting (recorded summary attached to the project
backlog), the advisor evaluated the dashboard, the 31 executed cycles, the
29 valid artifacts, and the deferred fingerprint state. Four explicit corrective
actions were issued:

- **M1** — Decouple LSTM training from the live pipeline. Train it in isolation
  using normal data and labeled anomalies, with an 80% train / 20% test split.
- **M2** — Search and evaluate public benchmark datasets (LID-DS / Leipzig,
  ADFA-LD, and a third dataset informally cited as "Dong Qing") and adapt them
  to the compressor / Edge Device case.
- **M3** — Record every training run: hyperparameters, number of epochs,
  architecture, F1, accuracy. Keep an inspectable training history.
- **M4** — Only after the offline benchmark validation reaches acceptable
  metrics, reintegrate the trained LSTM into the live pipeline for real-time
  anomaly detection.

All four actions were issued under the explicit reference of the approach used
in the doctoral thesis of F. A. M. do Nascimento ("Assis"), 2023, PUCRS, which
is already cited as reference [4] in the project's evaluation plan
(`docs/input/..._PLANO_DE_AVALIACAO_E_REFERENCE.txt`, line 81).

## 2. Anchors in the Assis thesis

The advisor's instructions correspond directly to the following sections of the
Assis thesis (the thesis PDF is the canonical reference for the methodological
discipline this prototype is being pulled toward):

- **Train/test split discipline** — Assis, Section 3.3.1, worker lifecycle:
  the worker collects the dataset locally, *"pre-processes it, which includes
  splitting it in 75% for training and 25% for testing"*. The advisor mandates
  **80/20** for our case; the principle is identical: every training run must
  have an explicit, recorded, reproducible split.
- **Hyperparameter table** — Assis, Table 4.2 (Hyper-parameters for the
  models): number of layers, neurons per layer, learning rate, batch size,
  number of training epochs, optimizer, loss function, dropout rate, weight
  initialization. Our project must produce an equivalent table per training
  run.
- **Model parameter count per dataset** — Assis, Table 4.1: number of
  parameters per architecture per dataset. Our project must record this for
  each (model, dataset) pair.
- **Evaluation metrics** — Assis, Section 2.2.2 and Section 4.1.3,
  Equations 2.1–2.5: Accuracy, Precision, Recall, F1-score, FPR. The advisor
  explicitly named F1 and accuracy as the minimum metrics for every training
  run.
- **Benchmark dataset discipline** — Assis, Section 2.2.1 and Table 2.3:
  benchmark datasets must be public, peer-reviewed and dataset-properties
  documented (number of samples, features, classes). Our project must adopt
  the same discipline for ADFA-LD and LID-DS.
- **Train/inference separation** — Assis, Chapter 3: Workers, Aggregators
  and Planners are distinct components; training is not coupled with
  real-time inference. Our project must mirror this separation by lifting
  training out of `run_local_demo.py` into a dedicated offline track.

## 3. Pre-correction state (what exists today)

Evidence reviewed before this correction:

- `src/parallel_truth_fingerprint/lstm_service/trainer.py` —
  `train_and_save_lstm_fingerprint` builds an **LSTM autoencoder** (encoder
  LSTM → RepeatVector → decoder LSTM → TimeDistributed Dense), compiled with
  Adam + MSE. It trains only on normal data, in-process, during the live
  runtime loop.
- `src/parallel_truth_fingerprint/lstm_service/lifecycle.py` —
  `execute_deferred_fingerprint_lifecycle` is invoked from the live runtime
  loop. Training is triggered when `eligible_history_count >=
  train_after_eligible_cycles` (default 10, configurable to 30).
- `src/parallel_truth_fingerprint/lstm_service/inference.py` — Inference is
  threshold-based (mean + 3·std reconstruction error). There is no F1, no
  accuracy, no precision, no recall, no train/test split, no labeled anomalies,
  no benchmark dataset adapter.
- The runtime currently produces 29 valid artifacts and 0 fingerprints. The
  pipeline blocks at the documented adequacy floor (`30` eligible artifacts,
  `20` windows).
- The runtime cannot demonstrate an academically defensible fingerprint claim
  because the model never sees labeled anomalies, never reports F1/accuracy,
  and never validates against public datasets.

## 4. Decisions approved on 2026-05-21

The following decisions are confirmed by the user (Emilio) and are the
authoritative input for updating `prd.md`, `architecture.md` and `epics.md`.

### D1 — Migrate to a supervised LSTM classifier

The current LSTM autoencoder is **deprecated** for the academic fingerprint
claim. It is replaced by a supervised LSTM classifier trained on labeled
sequences (normal + anomaly classes) drawn from the public benchmark datasets
selected in D2.

Justification: F1 and accuracy on a supervised classifier are the metrics the
advisor explicitly named (M3). They cannot be reported on an unsupervised
autoencoder without injecting synthetic ground truth, which would not satisfy
the academic comparison against the Assis approach.

### D2 — Benchmark datasets: ADFA-LD first, LID-DS 2021 second

The benchmark plan is executed in this order:

1. **ADFA-LD** (Creech & Hu, UNSW Canberra, 2013) — Linux system call traces,
   roughly 5,951 traces (5,205 normal + 746 attack across 6 attack categories).
   First benchmark because it is small, well-known, easy to load, and serves
   as the smoke test for the offline training track.
2. **LID-DS 2021** (Database Systems group, Universität Leipzig) — modern
   syscall traces with real CVEs, framework, and evaluation library. Second
   benchmark because it is larger and exercises the offline track with a
   richer label space and class imbalance.

A third dataset informally cited as "Dong Qing" by the advisor was not
identified in the public literature. It is treated as **open clarification**
to be confirmed with the advisor in the next meeting; the offline track must
not block on it.

### D3 — 80/20 train/test split mandated per training run

Every training run is a tuple `(dataset, model, hyperparameters, split, seed)`.
The split is **80% train / 20% test**, stratified by class label, with an
explicit `random_seed` recorded with the run. This matches the methodological
discipline of Assis Section 3.3.1, with the ratio adjusted to the value
explicitly named by the advisor.

### D4 — Training history must be persisted per run

For every offline training run, persist the following record on disk
(alongside the model artifact):

- run id, timestamp, git commit
- dataset name, dataset version, dataset split seed
- model architecture (layers, units per layer, dropout)
- hyperparameters (learning rate, batch size, optimizer, loss)
- number of epochs (planned and actually executed)
- final training loss, final validation loss
- **F1 (macro and per class)**, **accuracy**, precision, recall, FPR,
  confusion matrix
- training wall clock time
- inference wall clock time per window
- inference resource footprint (model file size in bytes, parameter count)

This record is the project's equivalent of Assis Tables 4.1 and 4.2. It must
be inspectable by the dashboard once reintegration (D6) happens.

### D5 — Offline training track is fully decoupled from the live pipeline

`run_local_demo.py` and `execute_deferred_fingerprint_lifecycle` must stop
training LSTM models. The live runtime keeps producing valid consensus
artifacts; it does **not** train, evaluate, or serve the supervised
classifier. Offline training is executed by a new dedicated script (see
`architecture-update`) that reads benchmark datasets and writes models and
metrics under a new MinIO prefix.

The live pipeline temporarily loses its fingerprint stage. This is the
explicit trade-off approved by the user under scope choice
"plano + documentos BMAD". The reintegration is staged as D6.

### D6 — Reintegration only after acceptable metrics

The supervised classifier is reintegrated into the live pipeline for
real-time anomaly detection **only** after the offline track demonstrates
acceptable metrics on both ADFA-LD and (when ready) LID-DS 2021.

Acceptance bar (academic defensibility, aligned with Assis Section 4.2):

- Macro F1 ≥ 0.85 on the test split of at least one benchmark
- Accuracy ≥ 0.90 on the test split of at least one benchmark
- A documented hyperparameter sweep with at least 5 distinct runs per
  benchmark, persisted under D4
- A documented architecture comparison (at minimum: LSTM vs GRU, matching
  Assis Section 4.2.4 effect-of-model experiments)

Reintegration only changes the inference path inside the runtime; training
remains offline.

## 5. Documents to update as a consequence of this correction

The following BMAD planning documents are now out of sync with the approved
decisions and must be updated in a separate task. This correction document
does not modify them in place; it only authorizes the update.

| Document | Update required |
| --- | --- |
| `prd.md` | Replace FR19/FR20/FR22 phrasing to reflect supervised classifier + benchmark-first training. Add FRs for offline training track, training history record, and F1/accuracy reporting. |
| `requirements.md` | Mirror PRD changes. Add the explicit dataset adoption list (ADFA-LD, LID-DS 2021) and the 80/20 + seed discipline. |
| `architecture.md` | Mark the autoencoder-in-runtime path as deprecated. Add the offline training module, the benchmark adapter, the training-history store, and the future reintegration boundary. |
| `epics.md` | Add Epic 7 (Offline Benchmark-Driven LSTM Training Track) with stories as listed in `epics-update-2026-05-21.md`. Mark Epic 4 stories 4.2, 4.2A, 4.3, 4.3A as superseded for the fingerprint claim. |
| `scope.md` | Restate that the academic fingerprint claim is established offline against public benchmarks; the live runtime keeps the consensus/SCADA pillars unchanged. |

## 6. Out of scope of this correction

- No code is modified by this correction. Code changes follow the updated
  documents in a separate task.
- The Byzantine consensus stack, the SCADA comparison stack, the MinIO
  persistence stack, the scenario control, and the operator dashboard
  (except the fingerprint-card semantics) are not changed by this
  correction.
- The "Dong Qing" dataset reference is left as an open clarification.

## 7. Traceability matrix to the meeting notes

| Meeting action | Document decision |
| --- | --- |
| M1 (decouple LSTM, 80/20 train/test) | D1, D3, D5 |
| M2 (benchmark datasets) | D2 |
| M3 (record hyperparameters, epochs, architecture, F1, accuracy) | D4 |
| M4 (reintegrate after validation) | D6 |
