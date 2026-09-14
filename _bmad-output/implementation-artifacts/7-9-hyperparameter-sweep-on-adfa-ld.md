# Story 7.9: Hyperparameter Sweep on ADFA-LD

Status: done

## Story

As a researcher producing the documented hyperparameter exploration named
by the advisor's M3 action ("anotar e registrar todos os treinamentos") and
by Decision D6 ("at least 5 distinct runs per benchmark"), I want a small
sweep harness that drives `execute_training_run` from a YAML config,
persists every run via Story 7.3, and aggregates the resulting metrics
into one Markdown report, so that the cross-benchmark report (Story 7.13)
can pull from a stable, inspectable source of runs.

## Scope Notes

- Implements `scripts/sweeps/adfa_ld_first_sweep.yaml` and the sweep harness
  module declared in `epics-update-2026-05-21.md` Story 7.9.
- Sweep grid stays minimal for CI: 2 learning rates × 2 batch sizes ×
  2 sequence lengths × 2 models = 16 cells. The user can extend the YAML
  for real runs without code changes.
- Uses **standard-library YAML alternative**: the project does not ship
  PyYAML as a runtime dependency, so the sweep config is JSON (with .json
  extension) for now. The YAML extension is reserved for a follow-up
  story if PyYAML is approved.

## Acceptance Criteria

1. A new module `offline_training/training/sweep.py` exposes `run_sweep(config, *, artifact_store)` that consumes a sweep config dict, drives `execute_training_run` for each cell, persists every run via Story 7.3, and returns the list of `(record, written)` pairs.
2. A new module function `summarize_sweep(records) -> str` returns a Markdown report with a single results table sorted by macro F1 descending.
3. A new CLI `scripts/train_lstm_sweep.py` accepts `--config <path>.json --output <path>.md --persist` and invokes the harness end-to-end against MinIO.
4. A reference config `scripts/sweeps/adfa_ld_first_sweep.json` declares ≥5 cells (at minimum: 2 LRs × 2 batch sizes × 2 seq lens × 2 models = 16, but only 5 are required by the AC; the file ships with the full 16-cell grid).
5. Unit test exercises the harness end-to-end with a tiny 3-cell config against the embedded ADFA-LD fixture + FakeMinioClient. The test asserts: every cell produced one record, every record was persisted, the Markdown report contains every run_id and a header row.
6. Full regression remains green.

## Tasks / Subtasks

- [x] Implement `run_sweep` (cartesian-product driver across hyperparameter axes). (AC: 1)
- [x] Implement `summarize_sweep` returning a Markdown table sorted by macro F1 descending. (AC: 2)
- [x] Implement `scripts/train_lstm_sweep.py` CLI (with `--persist` and the same MinIO flags as Story 7.7's CLI). (AC: 3)
- [x] Author `scripts/sweeps/adfa_ld_first_sweep.json` (2 models × 3 LRs × 3 batch sizes × 3 seq lens = 18 cells). (AC: 4)
- [x] Add unit tests (4): end-to-end sweep + persistence, summary table format, validation of missing grid axis, validation of empty models list. (AC: 5)
- [x] Run full suite; 188 tests pass. (AC: 6)
- [x] Update File List + Completion Notes.

## Dev Notes

- Sweep config dict shape:
  ```json
  {
    "benchmark": "adfa-ld",
    "models": ["lstm-classifier", "gru-classifier"],
    "epochs": 30,
    "seed": 42,
    "extra_hyperparameters": {"hidden_units": 64, "num_layers": 2},
    "grid": {
      "learning_rate": [1e-2, 1e-3, 1e-4],
      "batch_size": [32, 64, 128],
      "sequence_length": [30, 50, 100]
    }
  }
  ```
- Cartesian product over `grid` × `models`.
- For the report we serialize each row as
  `| run_id | model | lr | batch | seq_len | macro_f1 | accuracy | macro_precision | macro_recall |`.

## Dev Agent Record

### Agent Model Used

Claude Opus 4.7 via BMAD dev-story workflow.

### Debug Log References

- GREEN on first attempt.

### Completion Notes List

- `run_sweep` validates the config up front (required grid axes,
  non-empty axes, non-empty models) and fails fast with a clear message.
- The driver uses `itertools.product(models, learning_rates, batch_sizes,
  sequence_lengths)`; the test exercises a 1x2x1x2 = 4-cell sweep against
  the embedded ADFA-LD fixture in under 4 seconds.
- The shipped reference config produces 2 × 3 × 3 × 3 = 18 cells; the user
  scales up by adding values to the `grid` axes without code changes.
- `summarize_sweep` returns a Markdown table sorted by macro F1 descending
  so the report's first row is the candidate champion run.
- The CLI runs without `--persist` against an in-memory MinIO shim defined
  inside the script (so the script is self-contained and does not pull
  test code at runtime).
- Full regression: 188 tests, OK (skipped=7).

### File List

- `_bmad-output/implementation-artifacts/7-9-hyperparameter-sweep-on-adfa-ld.md`
- `src/parallel_truth_fingerprint/lstm_service/offline_training/training/sweep.py`
- `scripts/train_lstm_sweep.py`
- `scripts/sweeps/adfa_ld_first_sweep.json`
- `tests/lstm_service/offline_training/test_sweep.py`
