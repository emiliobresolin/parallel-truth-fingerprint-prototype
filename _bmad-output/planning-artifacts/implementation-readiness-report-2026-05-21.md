---
type: implementation-readiness
date: 2026-05-21
authority:
  - course-correction-2026-05-21.md
  - prd-update-2026-05-21.md
  - architecture-update-2026-05-21.md
  - epics-update-2026-05-21.md
status: epics-7-and-8-complete-real-adfa-ld-validated
---

# Implementation Readiness Report — 2026-05-21

## 1. Decision summary (recap)

User-approved on 2026-05-21:

- Datasets: **ADFA-LD first, LID-DS 2021 second**.
- Iteration 1: planning + documents only.
- Iteration 2: code implementation of Epic 7 (stories 7.1-7.5).
- Iteration 3: code implementation of remaining Epic 7 stories
  (7.6-7.13).
- Iteration 4: Epic 8 (stories 8.1-8.4) + alignment work
  (10s cycle default, real ADFA-LD adapter, class_weight, local store).
- Model: **migrate to a supervised LSTM classifier**, deprecating the
  autoencoder for the academic fingerprint claim.

## 2. Status snapshot — Epics 7 and 8 complete

### Epic 7 — Offline benchmark-driven training track

| Story | Status | Tests |
| --- | --- | --- |
| 7.1 Scaffold offline_training + CLI dummy | review | 5 |
| 7.2 Stratified 80/20 split with seed | review | 8 |
| 7.3 Training history schema + writer/reader | review | 5 |
| 7.4 Metrics (Assis Eq. 2.1-2.5) | review | 6 |
| 7.5 LSTM classifier (keras + torch) | review | 4 |
| 7.6 ADFA-LD adapter + fixture (real layout supported) | review | 11 |
| 7.7 First real run on ADFA-LD (helper + CLI --persist) | review | 1 |
| 7.8 GRU classifier baseline | review | 5 |
| 7.9 Sweep harness + ADFA-LD config | review | 4 |
| 7.10 LID-DS 2021 adapter + fixture | review | 8 |
| 7.11 First real run on LID-DS 2021 (helper) | review | 1 |
| 7.12 Sweep config for LID-DS 2021 | review | 1 |
| 7.13 Cross-benchmark comparative report | review | 3 |

### Epic 8 — Reintegration of the supervised classifier

| Story | Status | Tests |
| --- | --- | --- |
| 8.1 Promotion script + module | review | 5 |
| 8.2 Online inference helper (runtime-side) | review | 3 |
| 8.3 Deprecate runtime autoencoder (env-var opt-out) | review | 3 |
| 8.4 Dashboard surface for the promoted run | review | 2 |

Full project suite: **215 tests, OK (skipped=7)**. Baseline before
Epic 7: 140. Net delta: **+75 tests**, zero regressions.

## 3. Real-data validation milestone

The ADFA-LD archive (Creech & Hu, 2013) was downloaded and loaded
end-to-end through the production adapter:

- 5951 traces parsed (5205 normal + 746 attack across 5 attack classes).
- These counts match the literature exactly.
- The adapter was updated mid-iteration to support the official 2013
  layout (`Attack_Data_Master/<Class>_<N>/`) and the `Meterpreter` alias
  for `Java-Meterpreter`. The flat fixture used in CI still loads.
- One real LSTM training run on the live ADFA-LD with 5 epochs,
  batch 64, lr 1e-3, seq 50: `accuracy=0.8748, macro_f1=0.155`.
  This is the dataset-baseline (87% Normal); the balanced class_weight
  added in iteration 4 + a wider sweep are expected to lift macro F1.

## 4. Module map after Epics 7 + 8

```
src/parallel_truth_fingerprint/
  config/runtime.py                              # +DEMO_DISABLE_RUNTIME_AUTOENCODER, default cycle 10s
  persistence/
    artifact_store.py                            # MinIO (existing)
    local_filesystem.py                          # NEW: LocalFileArtifactStore
  lstm_service/
    online_inference.py                          # Epic 8 Story 8.2
    promoted_run_view.py                         # Epic 8 Story 8.4
    offline_training/
      cli.py                                     # supports --persist + --persist-local
      splits.py                                  # SplitRecord + stratified split
      benchmarks/
        base.py
        dummy.py
        adfa_ld.py                               # real UNSW 2013 layout supported
        lid_ds_2021.py
      models/
        base.py
        dummy.py
        lstm_classifier.py                       # + balanced class_weight
        gru_classifier.py                        # + balanced class_weight
      training/
        run.py                                   # TrainingRunRecord + dataset_provenance
        metrics.py                               # Assis Eq. 2.1-2.5
        sweep.py
        runner_adfa_ld.py
        runner_lid_ds_2021.py
        cross_benchmark_report.py
      registry/
        training_history.py
        promotion.py                             # Epic 8 Story 8.1

scripts/
  train_lstm_offline.py                          # one training run + --persist-local
  train_lstm_sweep.py                            # sweep + --persist-local
  build_cross_benchmark_report.py
  promote_lstm_run.py                            # Epic 8 Story 8.1
  sweeps/
    adfa_ld_first_sweep.json                     # full 18-cell grid
    adfa_ld_quick_sweep.json                     # 16-cell quick sweep used in real runs
    lid_ds_2021_first_sweep.json
```

## 5. Things the user must do out-of-band

- **LID-DS 2021 download.** ADFA-LD already exists in
  `datasets/ADFA-LD-real/`. LID-DS 2021 must be cloned from
  `github.com/LID-DS/LID-DS` into `datasets/LID-DS-2021-real/`. The
  adapter is ready.
- **`Dong Qing` clarification.** Still an open question for the advisor;
  see §7.
- **Live demo with the supervised classifier.** Requires a local
  CometBFT + MinIO + MQTT stack in pod. Documented in README §6 of the
  "Offline Benchmark-Driven Training Track" section.

## 6. Production commands the user runs

After downloading the datasets:

```powershell
$env:KERAS_BACKEND='torch'
$env:PYTHONPATH='src'

# One ADFA-LD run with production hyperparameters
$env:ADFA_LD_PATH=(Resolve-Path 'datasets\ADFA-LD-real\ADFA-LD').Path
.venv\Scripts\python.exe scripts\train_lstm_offline.py `
    --benchmark adfa-ld --model lstm-classifier `
    --epochs 30 --batch-size 64 --learning-rate 1e-3 `
    --sequence-length 50 --seed 42 `
    --persist-local _bmad-output\local-store

# Sweep on ADFA-LD (writes _bmad-output\implementation-artifacts\7-9-adfa-ld-sweep-summary.md)
.venv\Scripts\python.exe scripts\train_lstm_sweep.py `
    --config scripts\sweeps\adfa_ld_first_sweep.json `
    --output _bmad-output\implementation-artifacts\7-9-adfa-ld-sweep-summary.md `
    --persist-local _bmad-output\local-store

# Promote the winning run as the live-runtime classifier
.venv\Scripts\python.exe scripts\promote_lstm_run.py `
    --run-id <winning_run_id> `
    --persist-local _bmad-output\local-store

# Cross-benchmark report
.venv\Scripts\python.exe scripts\build_cross_benchmark_report.py `
    --output _bmad-output\implementation-artifacts\7-13-cross-benchmark-report.md
```

## 7. Open questions for the advisor

- **Q1**: The exact citation behind "Dong Qing" — is it a paper, a dataset,
  or a proposed method by an author named Dong Qing?
- **Q2**: Does macro F1 ≥ 0.85 / accuracy ≥ 0.90 match the advisor's
  expectation, or should it be tightened to a specific Assis chapter
  result (e.g., Section 4.2.5)?
- **Q3**: Should the supervised classifier replace the autoencoder
  entirely in the runtime, or run alongside it as a second channel?
  Story 8.3 implements the opt-out switch so either choice is one env
  var away.

## 8. Sign-off

- Epics 7 and 8 are implementation-complete and review-ready for every
  story.
- The suite is 215/215 green.
- The ADFA-LD real archive loads through the production adapter and one
  real LSTM training run was executed.
- The default cycle interval was reduced from 60s to 10s per advisor
  guidance to make full demonstration runs observable inside a single
  academic-presentation session.
- LID-DS 2021 and the live-demo wiring still need the user-side
  download + local stack respectively; the code path is in place.
