"""Deterministic majority-class baseline classifier (Story 7.1 only).

Exists to keep the Story 7.1 scaffold self-contained without dragging keras
+ torch into the smoke test. The real LSTM and GRU classifiers come in
Story 7.5 and Story 7.8.
"""

from __future__ import annotations

from collections import Counter
from dataclasses import dataclass

from parallel_truth_fingerprint.lstm_service.offline_training.models.base import (
    ClassifierAdapter,
    FitResult,
    register_model,
)


@dataclass
class _DummyHandle:
    majority_class: int = 0
    class_count: int = 0


@dataclass(frozen=True)
class DummyClassifier(ClassifierAdapter):
    name: str = "dummy"

    def build(
        self,
        *,
        sequence_length: int,
        feature_count: int,
        class_count: int,
        learning_rate: float,
        seed: int,
        extra_hyperparameters: dict[str, object],
    ) -> object:
        # learning_rate / seed / extra_hyperparameters are accepted to match
        # the contract; the dummy ignores them by design.
        del sequence_length, feature_count, learning_rate, seed, extra_hyperparameters
        return _DummyHandle(majority_class=0, class_count=class_count)

    def fit(
        self,
        *,
        model_handle: object,
        x_train: tuple[tuple[tuple[float, ...], ...], ...],
        y_train: tuple[int, ...],
        epochs: int,
        batch_size: int,
    ) -> FitResult:
        del batch_size
        if not isinstance(model_handle, _DummyHandle):
            raise TypeError("DummyClassifier.fit requires a DummyHandle.")
        if not y_train:
            raise ValueError("y_train must not be empty.")
        if not x_train:
            raise ValueError("x_train must not be empty.")
        counter = Counter(y_train)
        model_handle.majority_class = counter.most_common(1)[0][0]
        # Constant loss series so the record schema has something to record.
        loss_per_epoch = tuple(0.5 for _ in range(epochs))
        return FitResult(
            model_handle=model_handle,
            epochs_executed=epochs,
            per_epoch_loss=loss_per_epoch,
            parameter_count=0,
        )

    def predict(
        self,
        *,
        model_handle: object,
        x_test: tuple[tuple[tuple[float, ...], ...], ...],
    ) -> tuple[int, ...]:
        if not isinstance(model_handle, _DummyHandle):
            raise TypeError("DummyClassifier.predict requires a DummyHandle.")
        return tuple(model_handle.majority_class for _ in x_test)


register_model(DummyClassifier())
