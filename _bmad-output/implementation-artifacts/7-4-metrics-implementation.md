# Story 7.4: Metrics Implementation

Status: done

## Story

As a researcher mirroring Assis Equations 2.1–2.5, I want a metrics module
that computes Accuracy, Precision, Recall, F1 (macro + per class), False
Positive Rate, and the confusion matrix for any multi-class supervised
classifier output, so that every offline training run reports the exact
metrics the advisor named in meeting action M3.

## Scope Notes

- Implements `offline_training/training/metrics.py` declared in
  `architecture-update-2026-05-21.md` §B.1.
- Stays standard-library + numpy only (no sklearn).
- Formulas must match Assis Section 2.2.2 Equations 2.1–2.5.
- Story 7.4 lands BEFORE Story 7.3 because the history record schema needs
  the real metric keys to lock in.

## Acceptance Criteria

1. A new module `offline_training/training/metrics.py` exposes a function `compute_classification_metrics(predictions, truths, *, class_count)` returning a `ClassificationMetrics` dataclass.
2. `ClassificationMetrics` exposes: `accuracy: float`, `per_class_precision: tuple[float, ...]`, `per_class_recall: tuple[float, ...]`, `per_class_f1: tuple[float, ...]`, `macro_precision: float`, `macro_recall: float`, `macro_f1: float`, `per_class_false_positive_rate: tuple[float, ...]`, `confusion_matrix: tuple[tuple[int, ...], ...]`.
3. Values match Assis Equations 2.1 (Accuracy), 2.2 (Recall), 2.3 (FPR), 2.4 (Precision), 2.5 (F1). Verified against hand-computed fixtures for a binary case and a 3-class case.
4. Zero-division edge cases return 0.0 (not NaN, not raise) and are covered by a dedicated test.
5. The placeholder `_placeholder_macro_f1` in `training/run.py` is removed; `execute_training_run` now calls `compute_classification_metrics` and populates `metrics` with the full key set: `accuracy`, `macro_precision`, `macro_recall`, `macro_f1`, `per_class_precision`, `per_class_recall`, `per_class_f1`, `per_class_false_positive_rate`. The `confusion_matrix` is exposed as a separate attribute on the run record.
6. The dummy benchmark + dummy classifier (majority-class baseline) produces well-defined metrics (the test asserts the macro_f1 lies in `[0.0, 1.0]` and the confusion matrix shape matches the class count).
7. All previously-green tests stay green. New tests bring the suite to 153 + new.

## Tasks / Subtasks

- [x] Implement `compute_classification_metrics` with numpy and the explicit Assis formulas. (AC: 1, 2, 3, 4)
- [x] Add unit tests with hand-computed fixtures: 2-class perfect, 2-class known fixture, 3-class imbalanced, and two zero-division edge cases. (AC: 3, 4)
- [x] Wire `execute_training_run` to use the real metrics, add `confusion_matrix` and `per_class_metrics` attributes to `TrainingRunRecord`, remove the placeholder helper. (AC: 5)
- [x] Update CLI summary line to print `macro_precision`/`macro_recall` in addition to `accuracy`/`macro_f1`. (cosmetic but useful)
- [x] Story 7.1 smoke tests already accept the new metric key set (assertions still hold). (AC: 6)
- [x] Run full suite; 159 tests pass.
- [x] Update File List + Completion Notes.

## Dev Notes

- Assis Equation 2.1 (Accuracy):  `(TP + TN) / (TP + TN + FP + FN)` — extended to multi-class as the fraction of correct predictions overall.
- Assis Equation 2.2 (Detection Rate / Recall):  `TP / (TP + FN)` per class.
- Assis Equation 2.3 (FPR):  `FP / (FP + TN)` per class.
- Assis Equation 2.4 (Precision):  `TP / (TP + FP)` per class.
- Assis Equation 2.5 (F1):  `2 / (1/Recall + 1/Precision) = 2*TP / (2*TP + FP + FN)` per class.
- Macro = simple arithmetic mean across classes.

## Dev Agent Record

### Agent Model Used

Claude Opus 4.7 via BMAD dev-story workflow.

### Debug Log References

- First GREEN failed because the hand-derived 3-class fixture in the test
  was wrong (forgot to count `idx=2 pred=0 true=1` as FP of class 0). The
  implementation was correct from the start; the test fixture was rewritten
  with an explicit per-index TP/FP/FN enumeration to make the calculation
  reviewable and to add a confusion-matrix sanity check.

### Completion Notes List

- `compute_classification_metrics` implements Assis Equations 2.1-2.5
  exactly. Zero-division is centralised in `_safe_divide` so every
  per-class result returns 0.0 (never NaN, never raise).
- `TrainingRunRecord` now exposes `per_class_metrics` (dict of
  precision/recall/f1/false_positive_rate per class) and
  `confusion_matrix` (tuple-of-tuples). Story 7.3 will serialise these to
  MinIO as JSON.
- CLI summary line now prints `accuracy`, `macro_precision`,
  `macro_recall`, `macro_f1`.
- The dummy classifier always predicts class 0; on the dummy benchmark's
  6-sample 80/20 test split this yields `accuracy=0.5`,
  `macro_precision=0.25`, `macro_recall=0.5`, `macro_f1=0.3333` — exactly
  what the metric definitions require, and visible in the CLI output.
- Full regression: 159 tests, OK (skipped=7).

### File List

- `_bmad-output/implementation-artifacts/7-4-metrics-implementation.md`
- `src/parallel_truth_fingerprint/lstm_service/offline_training/training/metrics.py`
- `src/parallel_truth_fingerprint/lstm_service/offline_training/training/run.py`
- `src/parallel_truth_fingerprint/lstm_service/offline_training/cli.py`
- `tests/lstm_service/offline_training/test_metrics.py`
