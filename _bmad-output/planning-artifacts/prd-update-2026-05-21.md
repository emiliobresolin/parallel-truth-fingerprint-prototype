---
type: prd-update
date: 2026-05-21
parent: _bmad-output/planning-artifacts/prd.md
authority: course-correction-2026-05-21.md
status: approved-by-user-for-planning-only
---

# PRD Update — 2026-05-21

This update reflects the decisions captured in
`course-correction-2026-05-21.md`. It is an additive overlay on `prd.md`;
the parent PRD remains the canonical document for everything not amended
here. When the next PRD revision rolls in, the editorial guidance below
should be applied in place.

## A. Functional Requirements (changes)

### Superseded

These existing FRs are kept for traceability but no longer drive the academic
fingerprint claim:

- **FR19** (`The system can train an LSTM using normal data`) — superseded
  for the academic claim. Normal-only autoencoder training is deprecated.
- **FR20** (`The system can generate an equipment fingerprint`) — re-scoped:
  the fingerprint claim is now established against public benchmark datasets,
  not against runtime-collected normal-only data.
- **FR21** (`The system can generate anomaly score and normal/anomalous
  class`) — re-scoped: the classifier produces multi-class outputs aligned
  with the benchmark label space (e.g., normal vs. Hydra-FTP, Hydra-SSH,
  Adduser, Java/Meterpreter, Webshell for ADFA-LD).
- **FR22** (`The system can save the model/fingerprint`) — extended: every
  training run must save the model **plus** a training history record (see
  FR24 below).

### New

- **FR24 — Offline benchmark-driven training track.** The system must
  provide a training execution path that runs offline, outside the live
  runtime loop, against public benchmark datasets. The track must support
  ADFA-LD as the first benchmark and LID-DS 2021 as the second benchmark.
  Adding a new benchmark must be a localized change (one adapter module).

- **FR25 — Stratified 80/20 train/test split with recorded seed.** Every
  offline training run must use a stratified 80% train / 20% test split with
  an explicit `random_seed`. The split must be reproducible given the seed
  and the dataset version.

- **FR26 — Hyperparameter and architecture recording.** Every offline
  training run must persist: model architecture (layers, units, dropout),
  hyperparameters (learning rate, batch size, optimizer, loss), number of
  planned and actually executed epochs, and the model parameter count.
  Equivalent in scope to Assis Tables 4.1 and 4.2.

- **FR27 — Supervised classification metrics.** Every offline training run
  must compute and persist: macro F1, per-class F1, accuracy, precision,
  recall, false positive rate (FPR), and confusion matrix. These are the
  metrics named by the advisor (M3) and the equations 2.1–2.5 of Assis
  Section 2.2.2.

- **FR28 — Training history store.** The system must persist all training
  records under a dedicated MinIO prefix `fingerprint-training-history/`,
  with one JSON document per run and one model artifact per run. The store
  must support listing runs by dataset and by run id.

- **FR29 — Reintegration boundary.** The supervised classifier may only be
  attached to the live runtime inference path after the offline track
  produces metrics above the bar declared in Decision D6 of the course
  correction document. The reintegration must not move training back into
  the runtime loop.

### Modified

- **FR23 (`The system can detect a replay scenario`)** — wording unchanged,
  but the implementation is now expected to use the supervised classifier
  (after reintegration) instead of the autoencoder reconstruction-error
  threshold. Until reintegration, replay detection remains demonstrable via
  the SCADA-side payload behavior and scenario control, not via the LSTM.

## B. Non-Functional Requirements (changes)

### New

- **NFR18 — Reproducible training runs.** Each training run must be
  reproducible from: dataset version, split seed, model architecture record,
  and hyperparameter record. Two runs with the same inputs must produce
  identical metrics within numerical tolerance.

- **NFR19 — Inspectable training history.** The operator dashboard must be
  able to read the training history store and present each training run as
  an inspectable record (dataset, architecture, hyperparameters, metrics).
  Until the dashboard work lands, the records must be readable as flat JSON.

- **NFR20 — Live runtime cannot block on training.** The live runtime loop
  must never block waiting for an offline training run. The two tracks
  share MinIO but do not share execution lifecycles.

- **NFR21 — Benchmark dataset provenance.** Every benchmark used must be
  recorded with: origin organization, year of publication, dataset version
  string, sample count per class, feature schema, and the URL or citation
  used to obtain it. This mirrors the dataset table style of Assis Table
  2.3.

## C. Updated FR Coverage Map (additions)

| FR | Owning epic |
| --- | --- |
| FR24 | Epic 7 — Offline Benchmark-Driven LSTM Training Track |
| FR25 | Epic 7 |
| FR26 | Epic 7 |
| FR27 | Epic 7 |
| FR28 | Epic 7 |
| FR29 | Epic 8 — Reintegration of the Supervised Classifier (post-validation) |

## D. Editorial guidance for the next full PRD revision

When the PRD is rewritten end-to-end, the editor should:

1. Replace the wording of FR19 with: *"The system can train a supervised LSTM
   classifier on public benchmark datasets, using normal and anomalous
   labeled sequences."*
2. Replace the wording of FR21 with: *"The system can produce multi-class
   classification outputs aligned with the benchmark label space, plus the
   per-window anomaly probability."*
3. Add the four-line block: dataset, split seed, hyperparameters, metrics —
   as a required output for every training run.
4. Reference `course-correction-2026-05-21.md` in the changelog of the PRD.
