---
type: architecture-update
date: 2026-05-21
parent: _bmad-output/planning-artifacts/architecture.md
authority: course-correction-2026-05-21.md
status: approved-by-user-for-planning-only
---

# Architecture Update — 2026-05-21

This update is the architectural overlay for the course correction approved
on 2026-05-21. It documents the boundary between the **live runtime** (kept
intact for Epics 1–3) and the **offline benchmark-driven training track**
(new for Epic 7) and the **reintegration boundary** (Epic 8, post-validation).

The parent document `architecture.md` remains canonical for everything not
amended here. The deprecations below are explicit.

## A. Deprecations

The following architectural elements are deprecated as the basis for the
academic fingerprint claim. Their code remains in the tree until the offline
track produces validated metrics; then they are either re-purposed or removed.

- **`lstm_service/trainer.py::train_and_save_lstm_fingerprint`** — autoencoder
  trainer, in-process inside the live runtime. Deprecated as the academic
  fingerprint trainer. Retained only as a comparison baseline if needed.
- **`lstm_service/lifecycle.py::execute_deferred_fingerprint_lifecycle`** —
  trains and serves the autoencoder from inside the live runtime loop.
  Deprecated. Replaced by `inference-only` lifecycle after Epic 8.
- **`lstm_service/inference.py` reconstruction-error threshold** — `mean +
  3·std` thresholding on a normal-only baseline. Deprecated. Replaced by the
  supervised classifier output (multi-class probability + argmax) after
  Epic 8.
- **`DEMO_TRAIN_AFTER_ELIGIBLE_CYCLES` runtime knob** — deprecated. The
  runtime no longer trains; this environment variable becomes a no-op and
  must be removed in the next runtime cleanup pass.

## B. New architectural boundaries

The system gains two new logical boundaries (no new external dependencies
beyond what the project already vendors via `uv`):

### B.1 Offline benchmark training track

A new module, located at
`src/parallel_truth_fingerprint/lstm_service/offline_training/`, owns the
entire offline path. It is invoked exclusively by a new script,
`scripts/train_lstm_offline.py`, which is **not** imported by
`scripts/run_local_demo.py` and is **not** triggered by the runtime loop.

The module is organized as:

```
offline_training/
  benchmarks/
    base.py                    # BenchmarkAdapter protocol
    adfa_ld.py                 # ADFA-LD loader, label map, sequence builder
    lid_ds_2021.py             # LID-DS 2021 loader, label map, sequence builder
  splits.py                    # stratified 80/20 with recorded seed
  models/
    lstm_classifier.py         # supervised LSTM classifier
    gru_classifier.py          # GRU baseline (Assis 4.2.4 effect-of-model)
  training/
    run.py                     # one training run = one record
    history.py                 # training-history record schema + writer
    metrics.py                 # F1 (macro + per class), accuracy, precision,
                               # recall, FPR, confusion matrix
  registry/
    minio_writer.py            # writes runs to fingerprint-training-history/
    minio_reader.py            # lists and reads runs
```

`scripts/train_lstm_offline.py` exposes a CLI:

```
python scripts/train_lstm_offline.py \
  --benchmark adfa-ld \
  --model lstm-classifier \
  --epochs 30 \
  --batch-size 64 \
  --learning-rate 1e-3 \
  --sequence-length 50 \
  --seed 42
```

It performs: dataset load → stratified split → model build → fit → evaluate →
persist model + history record. Exits non-zero on any uncaught failure.

### B.2 Training-history store (MinIO)

New MinIO prefix: `fingerprint-training-history/`. Layout:

```
fingerprint-training-history/
  runs/
    <run_id>.json              # full record (FR26 + FR27 + FR28)
    <run_id>.model.keras       # model artifact
    <run_id>.confusion.json    # confusion matrix (separate for size)
  index/
    by-benchmark/
      adfa-ld.json             # list of run_ids on ADFA-LD
      lid-ds-2021.json         # list of run_ids on LID-DS 2021
    latest.json                # the single "currently endorsed" run for
                               # reintegration; updated by an explicit
                               # promotion command, not automatically
```

The store is read-only from the live runtime (Epic 8 reintegration); only
`scripts/train_lstm_offline.py` and `scripts/promote_lstm_run.py` write to
it.

### B.3 Reintegration boundary (Epic 8, future)

Once the offline track produces a run that satisfies Decision D6 of the
course correction:

1. The user runs `scripts/promote_lstm_run.py --run-id <id>` which writes
   that run id into `fingerprint-training-history/index/latest.json`.
2. The live runtime gains a new lightweight inference helper
   (`lstm_service/online_inference.py`) which **only loads** the promoted
   model and runs the classifier on the live consensus feature vectors.
3. The runtime never trains. The deprecated lifecycle module is removed in
   the same change set.

This split keeps the live runtime small and deterministic, and keeps the
academic claim grounded in offline, reproducible, benchmark-validated
training.

## C. Updated component map (overlay)

| Component | State after correction |
| --- | --- |
| sensor simulation | unchanged |
| edge nodes / MQTT | unchanged |
| consensus (CometBFT + Go ABCI) | unchanged |
| SCADA + comparison | unchanged |
| MinIO persistence (`valid-consensus-artifacts/`) | unchanged |
| MinIO persistence (`fingerprint-datasets/`) | frozen / read-only / kept for archival reference only |
| MinIO persistence (`fingerprint-models/`) | frozen / read-only / kept for archival reference only |
| **MinIO persistence (`fingerprint-training-history/`)** | **new — owned by offline track** |
| `lstm_service/trainer.py` | deprecated |
| `lstm_service/lifecycle.py` | deprecated |
| `lstm_service/inference.py` | deprecated for runtime; primitives may be reused for offline metrics if useful |
| **`lstm_service/offline_training/`** | **new** |
| **`scripts/train_lstm_offline.py`** | **new** |
| **`scripts/promote_lstm_run.py`** | **new (Epic 8)** |
| **`lstm_service/online_inference.py`** | **new (Epic 8)** |
| dashboard | new card showing the latest promoted run id and its metrics (Epic 8) |

## D. Cross-cutting rules (preserved)

These project-wide invariants are not relaxed by this update:

- Only consensused valid state may feed downstream stages (NFR4).
- SCADA divergence alerts and LSTM anomaly alerts remain distinct channels
  (NFR5). The supervised classifier output is a third channel; it does not
  replace either of the existing two.
- Scenario control may **not** bypass the offline training track. Triggering
  "scada_replay" or "single_edge_exclusion" must not inject samples into the
  benchmark dataset.
- The live runtime must never block on the offline track (NFR20).

## E. Notes on the third dataset reference

The advisor cited a third benchmark informally as "Dong Qing". A focused
search did not identify a public dataset of that exact name. The
architecture is dataset-agnostic: any new benchmark added later is one
new adapter module under `offline_training/benchmarks/` plus one entry in
the registry index. This update therefore does not pre-commit to a third
adapter.

## F. Risk register (delta)

| Risk | Mitigation |
| --- | --- |
| Demo loses its fingerprint card while offline track is built | Documented in `course-correction-2026-05-21.md`. Dashboard shows a "Fingerprint stage: offline benchmark validation in progress" placeholder until Epic 8. |
| ADFA-LD has known class imbalance | Stratified split (FR25) + per-class F1 (FR27) make this visible. |
| LID-DS 2021 is larger; training time may grow | Offline track is not on the runtime path; long jobs are acceptable. Record wall-clock time per run (D4). |
| "Dong Qing" reference unresolved | Open clarification; non-blocking. |
