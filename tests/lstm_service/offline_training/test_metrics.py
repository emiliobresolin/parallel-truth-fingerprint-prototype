"""Story 7.4: classification metrics, Assis Equations 2.1-2.5."""

from __future__ import annotations

import math
import unittest

from parallel_truth_fingerprint.lstm_service.offline_training.training.metrics import (
    ClassificationMetrics,
    compute_classification_metrics,
)


class BinaryMetricsTests(unittest.TestCase):
    """Hand-computed fixture for a 2-class classifier."""

    def test_perfect_classifier(self) -> None:
        predictions = (0, 1, 0, 1, 0, 1)
        truths = (0, 1, 0, 1, 0, 1)
        metrics = compute_classification_metrics(
            predictions, truths, class_count=2
        )
        self.assertIsInstance(metrics, ClassificationMetrics)
        self.assertAlmostEqual(metrics.accuracy, 1.0)
        self.assertAlmostEqual(metrics.macro_f1, 1.0)
        self.assertAlmostEqual(metrics.macro_precision, 1.0)
        self.assertAlmostEqual(metrics.macro_recall, 1.0)
        for class_id in (0, 1):
            self.assertAlmostEqual(metrics.per_class_f1[class_id], 1.0)
            self.assertAlmostEqual(metrics.per_class_precision[class_id], 1.0)
            self.assertAlmostEqual(metrics.per_class_recall[class_id], 1.0)
            self.assertAlmostEqual(
                metrics.per_class_false_positive_rate[class_id], 0.0
            )

    def test_known_binary_fixture(self) -> None:
        # 6 samples; predicted vs truth:
        #   idx: 0 1 2 3 4 5
        #   pred: 1 1 0 1 0 0
        #   true: 1 0 0 1 1 0
        # For class 1:
        #   TP = 2 (idx 0, 3)
        #   FP = 1 (idx 1)
        #   FN = 1 (idx 4)
        #   TN = 2 (idx 2, 5)
        # precision = 2/3, recall = 2/3, F1 = 2*2 / (2*2 + 1 + 1) = 4/6 = 0.6667
        # FPR class 1 = 1 / (1+2) = 1/3
        # Class 0 mirrors symmetrically.
        predictions = (1, 1, 0, 1, 0, 0)
        truths = (1, 0, 0, 1, 1, 0)
        metrics = compute_classification_metrics(
            predictions, truths, class_count=2
        )
        self.assertAlmostEqual(metrics.accuracy, 4 / 6, places=6)
        self.assertAlmostEqual(metrics.per_class_precision[1], 2 / 3, places=6)
        self.assertAlmostEqual(metrics.per_class_recall[1], 2 / 3, places=6)
        self.assertAlmostEqual(metrics.per_class_f1[1], 2 / 3, places=6)
        self.assertAlmostEqual(
            metrics.per_class_false_positive_rate[1], 1 / 3, places=6
        )
        # Macro is the simple mean of both classes; given the symmetry
        # macro == per_class[1] here.
        self.assertAlmostEqual(metrics.macro_f1, 2 / 3, places=6)
        # Confusion matrix layout: rows = truth, columns = prediction.
        #         pred 0   pred 1
        # true 0:   2        1
        # true 1:   1        2
        self.assertEqual(metrics.confusion_matrix, ((2, 1), (1, 2)))


class ThreeClassMetricsTests(unittest.TestCase):
    def test_three_class_imbalanced_fixture(self) -> None:
        # 9 samples, classes {0,1,2}:
        #   idx:  0 1 2 3 4 5 6 7 8
        #   pred: 0 0 0 1 1 2 1 2 0
        #   true: 0 0 1 1 1 2 0 2 2
        # Hand-derivation by truth-vs-prediction enumeration:
        # class 0:
        #   TP (pred=0 & true=0): idx 0, 1 -> TP=2
        #   FP (pred=0 & true!=0): idx 2 (true=1), idx 8 (true=2) -> FP=2
        #   FN (pred!=0 & true=0): idx 6 (pred=1) -> FN=1
        #   precision = 2 / (2+2) = 0.5
        #   recall    = 2 / (2+1) = 2/3
        #   F1        = 2*2 / (2*2 + 2 + 1) = 4/7
        # class 1:
        #   TP (pred=1 & true=1): idx 3, 4 -> TP=2
        #   FP (pred=1 & true!=1): idx 6 (true=0) -> FP=1
        #   FN (pred!=1 & true=1): idx 2 (pred=0) -> FN=1
        #   precision = 2/3, recall = 2/3, F1 = 4/6 = 2/3
        # class 2:
        #   TP (pred=2 & true=2): idx 5, 7 -> TP=2
        #   FP (pred=2 & true!=2): none -> FP=0
        #   FN (pred!=2 & true=2): idx 8 (pred=0) -> FN=1
        #   precision = 2/2 = 1.0, recall = 2/3, F1 = 4/5 = 0.8
        # Accuracy = correct (idx 0,1,3,4,5,7) / 9 = 6/9.
        predictions = (0, 0, 0, 1, 1, 2, 1, 2, 0)
        truths = (0, 0, 1, 1, 1, 2, 0, 2, 2)
        metrics = compute_classification_metrics(
            predictions, truths, class_count=3
        )
        self.assertAlmostEqual(metrics.accuracy, 6 / 9, places=6)
        self.assertAlmostEqual(metrics.per_class_precision[0], 0.5, places=6)
        self.assertAlmostEqual(metrics.per_class_recall[0], 2 / 3, places=6)
        self.assertAlmostEqual(metrics.per_class_f1[0], 4 / 7, places=6)
        self.assertAlmostEqual(metrics.per_class_precision[1], 2 / 3, places=6)
        self.assertAlmostEqual(metrics.per_class_recall[1], 2 / 3, places=6)
        self.assertAlmostEqual(metrics.per_class_f1[1], 2 / 3, places=6)
        self.assertAlmostEqual(metrics.per_class_precision[2], 1.0, places=6)
        self.assertAlmostEqual(metrics.per_class_recall[2], 2 / 3, places=6)
        self.assertAlmostEqual(metrics.per_class_f1[2], 0.8, places=6)
        self.assertAlmostEqual(
            metrics.macro_f1,
            (4 / 7 + 2 / 3 + 0.8) / 3,
            places=6,
        )
        # Confusion matrix sanity (rows = truth, cols = pred):
        #         pred 0  pred 1  pred 2
        # true 0:   2       1       0
        # true 1:   1       2       0
        # true 2:   1       0       2
        self.assertEqual(
            metrics.confusion_matrix,
            ((2, 1, 0), (1, 2, 0), (1, 0, 2)),
        )


class ZeroDivisionTests(unittest.TestCase):
    def test_class_never_predicted_returns_zero_precision_and_f1(self) -> None:
        # Class 1 exists in truth but classifier always predicts 0.
        predictions = (0, 0, 0, 0)
        truths = (0, 1, 0, 1)
        metrics = compute_classification_metrics(
            predictions, truths, class_count=2
        )
        # Class 1: TP=0, FP=0, FN=2 -> precision undefined -> 0.0,
        #          recall = 0/2 = 0, F1 = 0
        self.assertEqual(metrics.per_class_precision[1], 0.0)
        self.assertEqual(metrics.per_class_recall[1], 0.0)
        self.assertEqual(metrics.per_class_f1[1], 0.0)
        # Must not raise, must not be NaN.
        for value in (
            metrics.macro_precision,
            metrics.macro_recall,
            metrics.macro_f1,
        ):
            self.assertFalse(math.isnan(value))

    def test_class_never_in_truth_yields_zero_fpr_safe(self) -> None:
        # Class 2 declared but never appears in truth or prediction.
        predictions = (0, 1, 0, 1)
        truths = (0, 1, 0, 1)
        metrics = compute_classification_metrics(
            predictions, truths, class_count=3
        )
        # Class 2: TP=0, FP=0, FN=0, TN=4 -> precision=0, recall=0, FPR=0/(0+4)=0
        self.assertEqual(metrics.per_class_false_positive_rate[2], 0.0)
        self.assertEqual(metrics.per_class_precision[2], 0.0)
        self.assertEqual(metrics.per_class_recall[2], 0.0)


class RunIntegrationTests(unittest.TestCase):
    def test_execute_training_run_exposes_full_metric_key_set(self) -> None:
        from parallel_truth_fingerprint.lstm_service.offline_training.training.run import (
            execute_training_run,
        )

        record = execute_training_run(
            benchmark="dummy",
            model="dummy",
            epochs=1,
            batch_size=2,
            learning_rate=0.01,
            sequence_length=3,
            seed=5,
        )
        for key in (
            "accuracy",
            "macro_precision",
            "macro_recall",
            "macro_f1",
        ):
            self.assertIn(key, record.metrics)
            self.assertIsInstance(record.metrics[key], float)
        # confusion_matrix exposed as a separate attribute on the record
        self.assertIsNotNone(record.confusion_matrix)
        self.assertEqual(len(record.confusion_matrix), 2)  # dummy has 2 classes
        for row in record.confusion_matrix:
            self.assertEqual(len(row), 2)


if __name__ == "__main__":
    unittest.main()
