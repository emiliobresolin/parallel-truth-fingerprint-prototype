"""Supervised GRU classifier baseline (Assis Section 4.2.4 effect-of-model).

Mirrors `lstm_classifier.py` API for direct comparability in Story 7.9's
hyperparameter sweep and Story 7.13's cross-benchmark report.
"""

from __future__ import annotations

from dataclasses import dataclass
import importlib

from parallel_truth_fingerprint.lstm_service.offline_training.models.base import (
    ClassifierAdapter,
    FitResult,
    register_model,
)
from parallel_truth_fingerprint.lstm_service.offline_training.models.lstm_classifier import (
    _balanced_class_weights,
    _load_keras_module,
)


DEFAULT_HIDDEN_UNITS = 64
DEFAULT_NUM_LAYERS = 2


@dataclass(frozen=True)
class GruClassifier(ClassifierAdapter):
    name: str = "gru-classifier"

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
        keras = _load_keras_module()
        keras.utils.set_random_seed(int(seed))

        hidden_units = int(extra_hyperparameters.get("hidden_units", DEFAULT_HIDDEN_UNITS))
        num_layers = int(extra_hyperparameters.get("num_layers", DEFAULT_NUM_LAYERS))
        if num_layers < 1:
            raise ValueError(
                f"num_layers must be >= 1; got {num_layers!r}."
            )

        inputs = keras.Input(
            shape=(sequence_length, feature_count), name="input_sequence"
        )
        x = inputs
        for layer_index in range(num_layers):
            return_sequences = layer_index < (num_layers - 1)
            x = keras.layers.GRU(
                hidden_units,
                return_sequences=return_sequences,
                name=f"gru_layer_{layer_index + 1}",
            )(x)
        outputs = keras.layers.Dense(
            class_count, activation="softmax", name="class_softmax"
        )(x)
        model = keras.Model(
            inputs, outputs, name="supervised_gru_classifier"
        )
        model.compile(
            optimizer=keras.optimizers.Adam(learning_rate=float(learning_rate)),
            loss="sparse_categorical_crossentropy",
            metrics=["accuracy"],
        )
        return model

    def fit(
        self,
        *,
        model_handle: object,
        x_train: tuple[tuple[tuple[float, ...], ...], ...],
        y_train: tuple[int, ...],
        epochs: int,
        batch_size: int,
    ) -> FitResult:
        numpy = importlib.import_module("numpy")
        x_array = numpy.asarray(x_train, dtype="float32")
        y_array = numpy.asarray(y_train, dtype="int64")
        class_weight = _balanced_class_weights(y_array)
        history = model_handle.fit(  # type: ignore[union-attr]
            x_array,
            y_array,
            epochs=int(epochs),
            batch_size=int(batch_size),
            verbose=0,
            class_weight=class_weight,
        )
        per_epoch_loss = tuple(float(value) for value in history.history.get("loss", []))
        return FitResult(
            model_handle=model_handle,
            epochs_executed=int(epochs),
            per_epoch_loss=per_epoch_loss,
            parameter_count=int(model_handle.count_params()),  # type: ignore[union-attr]
        )

    def predict(
        self,
        *,
        model_handle: object,
        x_test: tuple[tuple[tuple[float, ...], ...], ...],
    ) -> tuple[int, ...]:
        numpy = importlib.import_module("numpy")
        x_array = numpy.asarray(x_test, dtype="float32")
        probabilities = model_handle.predict(x_array, verbose=0)  # type: ignore[union-attr]
        argmax = probabilities.argmax(axis=1).tolist()
        return tuple(int(value) for value in argmax)


register_model(GruClassifier())
