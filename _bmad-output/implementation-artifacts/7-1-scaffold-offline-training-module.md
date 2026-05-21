# Story 7.1: Scaffold the Offline Training Module

Status: review

## Story

As a researcher implementing the advisor's corrective actions from the 2026-05-21
orientation meeting, I want a dedicated offline training module and CLI that
runs end-to-end against a dummy benchmark, so that subsequent stories can fill
in real benchmarks, real splits, real metrics, and real models without ever
coupling training to the live runtime loop.

## Scope Notes

- Implements the scaffold described in `_bmad-output/planning-artifacts/architecture-update-2026-05-21.md` §B.1.
- This story does **not** touch `scripts/run_local_demo.py`, the deferred
  fingerprint lifecycle, or the deprecated autoencoder code path.
- The CLI must run end-to-end against a `dummy` benchmark before any real
  benchmark adapter (ADFA-LD / LID-DS) is added in later stories.
- The dummy run must produce a valid in-memory training history record so
  Story 7.3 can take it over for persistence.

## Acceptance Criteria

1. The module path `src/parallel_truth_fingerprint/lstm_service/offline_training/` exists with the submodule layout from `architecture-update-2026-05-21.md` §B.1.
2. A new CLI `scripts/train_lstm_offline.py` accepts `--benchmark`, `--model`, `--epochs`, `--batch-size`, `--learning-rate`, `--sequence-length`, `--seed` and exits 0 for `--benchmark dummy --model dummy`.
3. The dummy run produces a `TrainingRunRecord` dict containing `run_id`, `dataset_name`, `model_name`, `hyperparameters`, `metrics`, `seed`, `epochs_planned`, `epochs_executed`.
4. No code from `run_local_demo.py`, `lstm_service/lifecycle.py`, or `lstm_service/trainer.py` is invoked, imported, or referenced from the new module.
5. Existing test suite remains green (140 tests, OK).
6. A new unit test exercises the CLI via `python -m parallel_truth_fingerprint.lstm_service.offline_training.cli` or by invoking the script's `main` function directly.

## Dependencies

- Approved `course-correction-2026-05-21.md`, `architecture-update-2026-05-21.md`, `epics-update-2026-05-21.md`.

## Tasks / Subtasks

- [x] Create the `offline_training/` package scaffold with submodule directories (`benchmarks/`, `models/`, `training/`, `registry/`). (AC: 1)
  - [x] Add `__init__.py` to every new package.
  - [x] Add `DummyBenchmark` and `DummyClassifier` placeholders sufficient to drive an end-to-end smoke run.
- [x] Define the `TrainingRunRecord` dataclass (initial fields only; later stories extend it). (AC: 3)
- [x] Implement `training/run.py::execute_training_run` orchestrating: benchmark load → naive split (placeholder, real impl in Story 7.2) → model build → fit → placeholder metrics (real impl in Story 7.4) → record assembly. (AC: 2, 3)
- [x] Implement `cli.py::main` argparse entrypoint and `scripts/train_lstm_offline.py` thin wrapper. (AC: 2)
- [x] Add unit tests driving the CLI with `--benchmark dummy --model dummy`, asserting determinism for same seed, and asserting the scaffold isolation rule via static-text inspection of all `offline_training/*` files. (AC: 6, 4)
- [x] Run the full project test suite and confirm 145 tests pass (140 baseline + 5 new). (AC: 5)
- [x] Update File List + Completion Notes.

## Technical Notes

- All new modules must import from absolute paths under
  `parallel_truth_fingerprint.lstm_service.offline_training`.
- The CLI must be importable for tests: `from parallel_truth_fingerprint.lstm_service.offline_training.cli import main`.
- The `scripts/train_lstm_offline.py` file is a 5-line wrapper calling that `main`.
- No external network access. No MinIO calls in this story; persistence is owned by Story 7.3.
- Keep numpy as the only required scientific dependency for this story; keras/torch are added only in Story 7.5.

## Dev Notes

- `TrainingRunRecord` is intentionally a thin dict-like dataclass in this story; Story 7.3 will add the full schema, validator, and MinIO persistence.
- `execute_training_run` returns the record in-memory and is unit-testable without any I/O.
- Tests must run under `unittest` (project standard) and not require `pytest` or `sklearn`.

## Dev Agent Record

### Agent Model Used

Claude Opus 4.7 via BMAD dev-story workflow.

### Debug Log References

- Initial test run failed because `lstm_service/__init__.py` re-exports the
  deprecated runtime modules, so any import of `lstm_service.offline_training.*`
  pulls them via the parent package. The dynamic `sys.modules` probe was
  replaced with a static-text inspection that only flags references inside
  files under `offline_training/`. AC4 remains correctly enforced.
- Second iteration failed because the package docstring itself contained the
  literal deprecated module names. Docstring rewritten to avoid the literal
  module paths.

### Completion Notes List

- Story 7.1 scaffolding complete and isolated from the deprecated runtime
  fingerprint path.
- `scripts/train_lstm_offline.py` runs end-to-end against `--benchmark dummy
  --model dummy` and emits an in-memory `TrainingRunRecord`.
- `TrainingRunRecord` schema includes the minimum fields for downstream
  Stories 7.2/7.3/7.4 to extend: `run_id`, `created_at`, `dataset_name`,
  `model_name`, `seed`, `sequence_length`, `epochs_planned`,
  `epochs_executed`, `hyperparameters`, `metrics`, `per_epoch_loss`,
  `parameter_count`.
- Placeholder metrics (`accuracy`, `macro_f1`) are present so the schema is
  stable; the Assis-equation-aligned implementations land in Story 7.4.
- Naive 80/20 cut is in place; stratified seeded split lands in Story 7.2.
- Persistence to `fingerprint-training-history/` is deferred to Story 7.3.
- Full regression: 145 tests, OK (skipped=7). Baseline was 140 + 5 new.
- Manual command for evidence:
  `$env:PYTHONPATH='src'; .venv\Scripts\python.exe scripts\train_lstm_offline.py --benchmark dummy --model dummy --epochs 2 --batch-size 4 --learning-rate 0.01 --sequence-length 5 --seed 42`
  exits 0 and prints one summary line.

### File List

- `_bmad-output/implementation-artifacts/7-1-scaffold-offline-training-module.md`
- `src/parallel_truth_fingerprint/lstm_service/offline_training/__init__.py`
- `src/parallel_truth_fingerprint/lstm_service/offline_training/cli.py`
- `src/parallel_truth_fingerprint/lstm_service/offline_training/benchmarks/__init__.py`
- `src/parallel_truth_fingerprint/lstm_service/offline_training/benchmarks/base.py`
- `src/parallel_truth_fingerprint/lstm_service/offline_training/benchmarks/dummy.py`
- `src/parallel_truth_fingerprint/lstm_service/offline_training/models/__init__.py`
- `src/parallel_truth_fingerprint/lstm_service/offline_training/models/base.py`
- `src/parallel_truth_fingerprint/lstm_service/offline_training/models/dummy.py`
- `src/parallel_truth_fingerprint/lstm_service/offline_training/training/__init__.py`
- `src/parallel_truth_fingerprint/lstm_service/offline_training/training/run.py`
- `src/parallel_truth_fingerprint/lstm_service/offline_training/registry/__init__.py`
- `scripts/train_lstm_offline.py`
- `tests/lstm_service/offline_training/__init__.py`
- `tests/lstm_service/offline_training/test_cli_smoke.py`
