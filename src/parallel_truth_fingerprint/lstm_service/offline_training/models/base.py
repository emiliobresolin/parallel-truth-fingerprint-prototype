"""Classifier adapter contract for the offline training track."""

from __future__ import annotations

from dataclasses import dataclass, field
from typing import Protocol, Sequence


@dataclass(frozen=True)
class FitResult:
    """Outcome of a fit() call: trained model handle + per-epoch loss series."""

    model_handle: object
    epochs_executed: int
    per_epoch_loss: tuple[float, ...]
    parameter_count: int


class ClassifierAdapter(Protocol):
    """Every classifier adapter implements this contract."""

    name: str

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
        """Construct an untrained model handle."""

    def fit(
        self,
        *,
        model_handle: object,
        x_train: tuple[tuple[tuple[float, ...], ...], ...],
        y_train: tuple[int, ...],
        epochs: int,
        batch_size: int,
    ) -> FitResult:
        """Train the given model on the given data."""

    def predict(
        self,
        *,
        model_handle: object,
        x_test: tuple[tuple[tuple[float, ...], ...], ...],
    ) -> tuple[int, ...]:
        """Predict class ids for each test sequence."""


_REGISTRY: dict[str, ClassifierAdapter] = {}


def register_model(adapter: ClassifierAdapter) -> None:
    _REGISTRY[adapter.name] = adapter


def list_available_models() -> Sequence[str]:
    return tuple(sorted(_REGISTRY))


def load_model(name: str) -> ClassifierAdapter:
    if name not in _REGISTRY:
        raise ValueError(
            f"Unknown model {name!r}. Available: {list_available_models()}"
        )
    return _REGISTRY[name]
