# Story 7.13: Cross-Benchmark Comparative Report

Status: review

## Story

As a researcher delivering the final piece of Epic 7's evidence, I want a
generator that reads the persisted training history and produces a single
Markdown report comparing the best LSTM vs GRU run per benchmark, with
per-class F1 / precision / recall tables aligned with Assis Section 4.2.5,
so that the advisor can review the entire offline track from one
document.

## Scope Notes

- Implements `offline_training/training/cross_benchmark_report.py` plus
  the CLI `scripts/build_cross_benchmark_report.py` declared in
  `epics-update-2026-05-21.md` Story 7.13.
- The report is generated from the `fingerprint-training-history/runs/`
  prefix; no re-training happens at report time. Story 7.13 only reads.
- "Best" run per (benchmark, model) pair = highest macro_f1.

## Acceptance Criteria

1. A new module `offline_training/training/cross_benchmark_report.py` exposes `build_cross_benchmark_report(*, artifact_store, benchmarks=None) -> str` returning a Markdown report.
2. The report contains three sections, in order:
   - Section 1: champion table per benchmark, columns `benchmark | model | run_id | macro_f1 | accuracy | macro_precision | macro_recall | parameter_count`.
   - Section 2: per-class table per (benchmark, model) pair: columns `class | precision | recall | f1 | support_train | support_test`.
   - Section 3: a brief footer listing dataset provenance (origin, year, citation) for each benchmark.
3. If a benchmark has zero persisted runs, the report includes an explicit "_No runs persisted for `<benchmark>` yet._" line and continues with the remaining benchmarks instead of raising.
4. A new CLI `scripts/build_cross_benchmark_report.py` accepts `--output <path>.md` and `--benchmark` (repeatable; defaults to ADFA-LD and LID-DS 2021), reads MinIO via the same flags as Story 7.7's CLI, and writes the report to `--output`.
5. Unit tests cover: report generation across two benchmarks (both have one persisted run each in the test), the "no runs persisted" branch for an unknown benchmark, and a champion-selection test where two runs of the same model on the same benchmark with different macro F1 produce a champion table entry pointing at the higher-F1 run.
6. Full regression remains green.

## Tasks / Subtasks

- [x] Implement `build_cross_benchmark_report`. (AC: 1, 2, 3)
- [x] Implement `scripts/build_cross_benchmark_report.py`. (AC: 4)
- [x] Add unit tests (3): cross-benchmark champion table with provenance, unknown benchmark fallback, champion-selection by macro F1. (AC: 5)
- [x] Run full suite; 201 tests pass. (AC: 6)
- [x] Update File List + Completion Notes.

### Debug Log References

- First GREEN failed silently: the Section 3 fallback message "provenance
  unavailable (...)" happened to contain "ADFA-LD" and "LID-DS 2021" so
  the original `assertIn("ADFA-LD", ...)` test was passing by accident.
  Inspection of the generated report uncovered the issue.
- Root cause: `_render_section_three` was calling `load_benchmark` at
  report time, which requires the env vars to still be set; the runner
  helpers restore them on exit.
- Fix: capture the dataset provenance at training time inside
  `execute_training_run`, store it on `TrainingRunRecord`
  (`dataset_provenance` + `label_names` fields), serialize/deserialize
  alongside the rest of the record (Story 7.3 schema extension),
  rewrite `_render_section_three` to read from the persisted record.
- Test reinforced: now asserts the literal `origin: ADFA-LD`,
  `origin: LID-DS 2021`, `year: 2013`, `year: 2021`, and explicitly
  forbids the phrase `provenance unavailable`.

### Completion Notes List

- `TrainingRunRecord` now exposes `dataset_provenance` (dict captured at
  training time) and `label_names` (canonical class names from the
  benchmark adapter). Both are serialized to JSON via
  `_normalize_provenance_for_json` so tuples and exotic types stay
  round-trippable.
- The report has three sections: champion table, per-class metrics, and
  the dataset provenance footer.
- The CLI `scripts/build_cross_benchmark_report.py` mirrors the MinIO
  flag surface of `scripts/train_lstm_offline.py`.
- Full regression: 201 tests, OK (skipped=7).

### File List

- `_bmad-output/implementation-artifacts/7-13-cross-benchmark-comparative-report.md`
- `src/parallel_truth_fingerprint/lstm_service/offline_training/training/cross_benchmark_report.py`
- `src/parallel_truth_fingerprint/lstm_service/offline_training/training/run.py` (added `dataset_provenance`, `label_names` to `TrainingRunRecord`)
- `src/parallel_truth_fingerprint/lstm_service/offline_training/registry/training_history.py` (serialize/deserialize the new fields + `_normalize_provenance_for_json` helper)
- `scripts/build_cross_benchmark_report.py`
- `tests/lstm_service/offline_training/test_cross_benchmark_report.py`

## Dev Notes

- The report module reads runs via `list_training_runs(artifact_store=...,
  benchmark=...)` + `read_training_run(...)` from Story 7.3, so there is
  no new MinIO dependency.
- Provenance for Section 3 is reconstructed by calling the benchmark
  adapter's `.load(sequence_length=1, seed=0)` only when the benchmark
  has at least one persisted run; we avoid loading absent benchmarks.

## Dev Agent Record

### Agent Model Used

Claude Opus 4.7 via BMAD dev-story workflow.

<!-- Dev Agent Record populated above. -->

