"""Fail-closed label and categorical-cardinality regression tests."""

from __future__ import annotations

import math
import unittest

import numpy as np

from parallel_truth_fingerprint.lstm_service.offline_training.academic_models import (
    _CategoricalUnigramDetector,
    _RecurrentAutoencoderDetector,
)
from parallel_truth_fingerprint.lstm_service.offline_training.academic_protocol import (
    AcademicUnit,
    PreparedPartition,
)


def _unit(label: object) -> AcademicUnit:
    return AcademicUnit(
        unit_id="unit-a",
        group_id="group-a",
        native_partition="test",
        assigned_partition="test",
        label=label,  # type: ignore[arg-type]
        class_name="Normal",
        values=(("read",),),
        source_path="fixture.sc",
        source_sha256="sha256:" + "a" * 64,
    )


class AcademicInputIntegrityTests(unittest.TestCase):
    def test_academic_unit_rejects_boolean_fractional_and_nonfinite_labels(self) -> None:
        for label, message in (
            (True, "Boolean"),
            (0.5, "fractional"),
            (math.nan, "non-finite"),
            (math.inf, "non-finite"),
        ):
            with self.subTest(label=label), self.assertRaisesRegex(ValueError, message):
                _unit(label)

    def test_prepared_partition_rejects_fraction_before_integer_conversion(self) -> None:
        with self.assertRaisesRegex(ValueError, "fractional"):
            PreparedPartition(
                x=np.zeros((1, 1, 1), dtype=np.float32),
                window_ids=("window-a",),
                unit_ids=("unit-a",),
                labels=np.asarray([0.25], dtype=np.float64),
                class_names=("Normal",),
                event_ids=((),),
            )

    def test_recurrent_categorical_model_requires_train_fitted_cardinality(self) -> None:
        train = np.asarray([[[2], [3]]], dtype=np.int32)
        validation = np.asarray([[[1], [0]]], dtype=np.int32)
        detector = _RecurrentAutoencoderDetector(
            "categorical-syscall", {}, categorical_vocabulary_size=None
        )
        with self.assertRaisesRegex(ValueError, "train-fitted vocabulary"):
            detector.fit(train, validation, seed=1)

    def test_validation_token_cannot_expand_frozen_train_cardinality(self) -> None:
        train = np.asarray([[[2], [3]]], dtype=np.int32)
        validation = np.asarray([[[4], [1]]], dtype=np.int32)
        detector = _RecurrentAutoencoderDetector(
            "categorical-syscall", {}, categorical_vocabulary_size=4
        )
        with self.assertRaisesRegex(ValueError, "exceed the frozen train vocabulary"):
            detector.fit(train, validation, seed=1)

    def test_unigram_reserves_train_fitted_unknown_id_even_if_unseen_in_train(self) -> None:
        detector = _CategoricalUnigramDetector(
            {"laplace_alpha": 1.0}, categorical_vocabulary_size=4
        )
        train = np.asarray([[[2], [3]]], dtype=np.int32)
        detector.fit(train, train, seed=1)

        score = detector.score(np.asarray([[[1], [0]]], dtype=np.int32))
        self.assertTrue(np.all(np.isfinite(score)))
        with self.assertRaisesRegex(ValueError, "map to UNK"):
            detector.score(np.asarray([[[4], [0]]], dtype=np.int32))


if __name__ == "__main__":
    unittest.main()
