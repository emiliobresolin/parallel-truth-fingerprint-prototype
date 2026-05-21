---
type: epics-update
date: 2026-05-21
parent: _bmad-output/planning-artifacts/epics.md
authority:
  - course-correction-2026-05-21.md
  - prd-update-2026-05-21.md
  - architecture-update-2026-05-21.md
status: approved-by-user-for-planning-only
---

# Epics Update — 2026-05-21

This update introduces two new epics that implement the course correction and
records which existing stories are superseded for the academic fingerprint
claim. It is additive on top of `epics.md`.

## A. Superseded stories (for the academic fingerprint claim only)

These stories remain in the implemented set as evidence of the autoencoder
exploration, but they no longer carry the academic fingerprint claim. The
runtime code remains until Epic 8 removes it.

- **4.2** — Train and save a reusable local LSTM fingerprint model
- **4.2A** — Persist inspectable training dataset artifacts
- **4.3** — Implement fingerprint inference with anomaly score and
  classification (autoencoder-based)
- **4.3A** — Continuous autonomous runtime loop and deferred fingerprint
  lifecycle

## B. Epic 7 — Offline Benchmark-Driven LSTM Training Track (new)

Goal: produce an academically defensible supervised LSTM classifier trained
on public benchmark datasets, with full hyperparameter + metric history,
fully decoupled from the live runtime.

Covers FR24, FR25, FR26, FR27, FR28 and NFR18, NFR19, NFR20, NFR21.

### Story 7.1 — Scaffold the offline training module
- Create `src/parallel_truth_fingerprint/lstm_service/offline_training/`
  with the layout described in `architecture-update-2026-05-21.md` §B.1.
- Create `scripts/train_lstm_offline.py` with the CLI defined in §B.1.
- The script must run end-to-end on a dummy in-memory dataset (smoke test)
  before any real benchmark is added.
- Add a unit test that exercises the script with `--benchmark dummy`.
- No production behavior changed. No runtime code touched.

### Story 7.2 — Stratified 80/20 split utility with recorded seed
- Implement `offline_training/splits.py::stratified_train_test_split`.
- Mandatory inputs: feature sequences, labels, seed.
- Output: `(X_train, y_train, X_test, y_test, split_record)` where
  `split_record` is a dict carrying seed, ratios, per-class counts.
- Unit tests cover: imbalanced labels, deterministic output for fixed seed,
  rejection of empty class.

### Story 7.3 — Training history schema and writer
- Implement `offline_training/training/history.py` with the JSON schema for
  one training run record (fields enumerated in
  `course-correction-2026-05-21.md` §4 Decision D4).
- Implement `offline_training/registry/minio_writer.py` writing under
  `fingerprint-training-history/runs/`.
- Implement `offline_training/registry/minio_reader.py` listing under
  `fingerprint-training-history/index/by-benchmark/`.
- Unit tests cover: round-trip of one record, index update, schema
  validation of malformed records.

### Story 7.4 — Metrics implementation
- Implement `offline_training/training/metrics.py` covering: macro F1,
  per-class F1, accuracy, precision, recall, FPR, confusion matrix.
- Formulas must match Assis Section 2.2.2 Equations 2.1–2.5.
- Unit tests with hand-computed expected values for a 3-class fixture and a
  binary fixture.

### Story 7.5 — Supervised LSTM classifier model
- Implement `offline_training/models/lstm_classifier.py` building a small
  supervised LSTM classifier. Default architecture aligned with Assis
  Section 4.1.1 Table 4.1 sizing approach (2 LSTM layers, 64 hidden units,
  softmax head).
- Configurable hyperparameters: layers, hidden units, dropout, learning
  rate, batch size, epochs, optimizer (Adam default), loss
  (sparse categorical crossentropy default).
- Unit test: model builds, has expected parameter count for a 50×10 input,
  trains for 1 epoch on a fixture without raising.

### Story 7.6 — ADFA-LD benchmark adapter
- Implement `offline_training/benchmarks/adfa_ld.py`:
  download/extract or accept a local path, build sequences of syscall
  integers, build label vector across the 6 attack categories + normal.
- Document dataset version, sample counts per class, URL, citation in the
  module docstring (FR-NFR21 evidence).
- Unit test against a tiny embedded fixture file.

### Story 7.7 — First real training run on ADFA-LD
- Run `python scripts/train_lstm_offline.py --benchmark adfa-ld
  --model lstm-classifier --epochs 30 --batch-size 64
  --learning-rate 1e-3 --sequence-length 50 --seed 42`.
- Persist the run record + model + confusion matrix to MinIO under
  `fingerprint-training-history/runs/`.
- Manually record the run id, macro F1, accuracy in
  `_bmad-output/implementation-artifacts/7-7-first-adfa-ld-run.md`.

### Story 7.8 — GRU classifier baseline (Assis 4.2.4 effect-of-model)
- Implement `offline_training/models/gru_classifier.py` with the same
  hyperparameter surface as `lstm_classifier.py`.
- Run the same training command as Story 7.7 with `--model gru-classifier`.
- Record the run for comparative analysis.

### Story 7.9 — Hyperparameter sweep on ADFA-LD
- Drive `scripts/train_lstm_offline.py` from a small sweep config
  (`scripts/sweeps/adfa_ld_first_sweep.yaml`) covering at least:
  learning rate ∈ {1e-2, 1e-3, 1e-4}, batch size ∈ {32, 64, 128},
  sequence length ∈ {30, 50, 100}. 5 runs minimum per model.
- Persist all runs. Aggregate metrics into a Markdown table under
  `_bmad-output/implementation-artifacts/7-9-adfa-ld-sweep-summary.md`.

### Story 7.10 — LID-DS 2021 benchmark adapter
- Mirror of Story 7.6 for LID-DS 2021. Document version, scenarios, label
  map, sample counts per class.

### Story 7.11 — First real training run on LID-DS 2021
- Mirror of Story 7.7 on LID-DS 2021.

### Story 7.12 — Hyperparameter sweep on LID-DS 2021
- Mirror of Story 7.9 on LID-DS 2021.

### Story 7.13 — Cross-benchmark comparative report
- Produce `_bmad-output/implementation-artifacts/7-13-cross-benchmark-report.md`
  comparing the best run on each benchmark across models. Format aligned
  with Assis Section 4.2.5 (table per metric, per class).

### Acceptance gate for Epic 7

Epic 7 is closed only when:

- Macro F1 ≥ 0.85 on at least one benchmark test split.
- Accuracy ≥ 0.90 on at least one benchmark test split.
- All runs are persisted under `fingerprint-training-history/runs/`.
- The cross-benchmark report (Story 7.13) is written.

## C. Epic 8 — Reintegration of the Supervised Classifier (new, gated)

Goal: connect the promoted offline-trained classifier into the live runtime
**only after Epic 7 has passed its acceptance gate**. Covers FR29 and
removes the deprecated autoencoder path.

### Story 8.1 — Promotion script
- Implement `scripts/promote_lstm_run.py --run-id <id>`.
- Writes the chosen run id into
  `fingerprint-training-history/index/latest.json`.
- Unit test against a MinIO mock.

### Story 8.2 — Live runtime online inference helper
- Implement `lstm_service/online_inference.py`.
- Loads the promoted model on runtime start, runs per-window classification
  on the live consensus feature vectors, emits the result as a new
  `lstm_classifier` channel.
- Must not touch `valid-consensus-artifacts/` or
  `fingerprint-training-history/runs/`.

### Story 8.3 — Removal of the deprecated autoencoder path
- Remove `train_and_save_lstm_fingerprint`, the deferred fingerprint
  lifecycle, the autoencoder inference, and the
  `DEMO_TRAIN_AFTER_ELIGIBLE_CYCLES` runtime knob.
- Update `run_local_demo.py` to use `online_inference` only.
- Update README and the runtime artifacts report accordingly.

### Story 8.4 — Dashboard surface for the promoted run
- The dashboard fingerprint card shows: promoted run id, dataset,
  architecture, macro F1, accuracy, link to the run record JSON.
- Until Story 8.1 has been executed once, the card shows a "no promoted
  classifier" state and a hint to run the offline training first.

## D. Updated FR Coverage Map (additions)

| FR | Owning epic |
| --- | --- |
| FR24, FR25, FR26, FR27, FR28 | Epic 7 |
| FR29 | Epic 8 |

## E. Execution order

The user has approved (on 2026-05-21) **planning only**. Once code work is
authorized, the order is:

1. Stories 7.1 → 7.5 (scaffolding, splits, history, metrics, model).
2. Story 7.6 → 7.7 (ADFA-LD adapter + first real run).
3. Stories 7.8, 7.9 (GRU baseline + sweep on ADFA-LD).
4. Stories 7.10 → 7.12 (LID-DS 2021).
5. Story 7.13 (cross-benchmark report).
6. Acceptance gate review.
7. Epic 8 stories in order.
