"""Classification metrics aligned with Assis Equations 2.1-2.5.

Implements the metric set explicitly named by the advisor in the
2026-05-21 orientation meeting (action M3): accuracy, precision, recall,
F1 (macro + per class), false positive rate, and the confusion matrix.

Standard-library + numpy only. No sklearn dependency on purpose.
"""

from __future__ import annotations

from dataclasses import dataclass
from typing import Sequence

import numpy as np


@dataclass(frozen=True)
class ClassificationMetrics:
    """One frozen record of supervised-classification metrics."""

    accuracy: float
    per_class_precision: tuple[float, ...]
    per_class_recall: tuple[float, ...]
    per_class_f1: tuple[float, ...]
    per_class_false_positive_rate: tuple[float, ...]
    macro_precision: float
    macro_recall: float
    macro_f1: float
    confusion_matrix: tuple[tuple[int, ...], ...]

    def as_run_metric_dict(self) -> dict[str, float]:
        """Flatten the scalar fields into the TrainingRunRecord.metrics dict."""
        return {
            "accuracy": float(self.accuracy),
            "macro_precision": float(self.macro_precision),
            "macro_recall": float(self.macro_recall),
            "macro_f1": float(self.macro_f1),
        }


def compute_classification_metrics(
    predictions: Sequence[int],
    truths: Sequence[int],
    *,
    class_count: int,
) -> ClassificationMetrics:
    """Compute the Assis-aligned metric set for one (predictions, truths) pair.

    Raises ``ValueError`` if lengths disagree or class_count is non-positive.
    Returns 0.0 for any precision/recall/F1/FPR whose denominator is zero
    (no NaN escapes this function).
    """

    if class_count <= 0:
        raise ValueError(f"class_count must be positive; got {class_count!r}.")
    if len(predictions) != len(truths):
        raise ValueError(
            "predictions and truths must align: "
            f"got {len(predictions)} vs {len(truths)}."
        )
    if not truths:
        raise ValueError("Cannot compute metrics on empty inputs.")

    pred_array = np.asarray(predictions, dtype=np.int64)
    true_array = np.asarray(truths, dtype=np.int64)

    # Confusion matrix: rows = truth, columns = prediction.
    confusion = np.zeros((class_count, class_count), dtype=np.int64)
    for true_value, pred_value in zip(true_array.tolist(), pred_array.tolist()):
        confusion[true_value, pred_value] += 1

    # Per-class counts derived from the confusion matrix.
    per_class_tp = np.diag(confusion).astype(np.float64)
    per_class_fp = confusion.sum(axis=0).astype(np.float64) - per_class_tp
    per_class_fn = confusion.sum(axis=1).astype(np.float64) - per_class_tp
    total = float(confusion.sum())
    per_class_tn = total - (per_class_tp + per_class_fp + per_class_fn)

    per_class_precision = _safe_divide(per_class_tp, per_class_tp + per_class_fp)
    per_class_recall = _safe_divide(per_class_tp, per_class_tp + per_class_fn)
    per_class_f1 = _safe_divide(
        2.0 * per_class_tp,
        (2.0 * per_class_tp) + per_class_fp + per_class_fn,
    )
    per_class_fpr = _safe_divide(per_class_fp, per_class_fp + per_class_tn)

    accuracy = float(per_class_tp.sum() / total) if total > 0 else 0.0
    macro_precision = float(per_class_precision.mean())
    macro_recall = float(per_class_recall.mean())
    macro_f1 = float(per_class_f1.mean())

    confusion_as_tuple = tuple(
        tuple(int(value) for value in row) for row in confusion.tolist()
    )

    return ClassificationMetrics(
        accuracy=accuracy,
        per_class_precision=tuple(float(v) for v in per_class_precision.tolist()),
        per_class_recall=tuple(float(v) for v in per_class_recall.tolist()),
        per_class_f1=tuple(float(v) for v in per_class_f1.tolist()),
        per_class_false_positive_rate=tuple(
            float(v) for v in per_class_fpr.tolist()
        ),
        macro_precision=macro_precision,
        macro_recall=macro_recall,
        macro_f1=macro_f1,
        confusion_matrix=confusion_as_tuple,
    )


def _safe_divide(numerator: np.ndarray, denominator: np.ndarray) -> np.ndarray:
    """Element-wise divide that returns 0.0 wherever denominator == 0."""
    safe_denominator = np.where(denominator == 0, 1.0, denominator)
    result = numerator / safe_denominator
    result = np.where(denominator == 0, 0.0, result)
    return result
