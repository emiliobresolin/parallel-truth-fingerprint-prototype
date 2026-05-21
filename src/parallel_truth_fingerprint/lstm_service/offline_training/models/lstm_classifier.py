"""Supervised LSTM classifier on the Keras torch backend.

Implements the model adapter used by Story 7.7 (first real run on ADFA-LD)
and by every subsequent benchmark run in Epic 7. Sizing is aligned with the
Assis Section 4.1.1 / Table 4.1 reference (a small stacked LSTM with a
softmax head); the exact number of layers and hidden units is exposed via
`extra_hyperparameters` so Story 7.9's sweep can vary them.
"""

from __future__ import annotations

from dataclasses import dataclass
import importlib
import importlib.util
import os

from parallel_truth_fingerprint.lstm_service.offline_training.models.base import (
    ClassifierAdapter,
    FitResult,
    register_model,
)


DEFAULT_HIDDEN_UNITS = 64
DEFAULT_NUM_LAYERS = 2


@dataclass(frozen=True)
class LstmClassifier(ClassifierAdapter):
    name: str = "lstm-classifier"

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
        # Best-effort determinism for the torch backend.
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
            x = keras.layers.LSTM(
                hidden_units,
                return_sequences=return_sequences,
                name=f"lstm_layer_{layer_index + 1}",
            )(x)
        outputs = keras.layers.Dense(
            class_count, activation="softmax", name="class_softmax"
        )(x)
        model = keras.Model(
            inputs, outputs, name="supervised_lstm_classifier"
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
        # Story 8.2 / Assis Table 4.10 inspired: balance the loss by class
        # frequency so a 87% Normal vs 13% attack dataset (ADFA-LD) does
        # not collapse to majority-class prediction. Pure-numpy frequency
        # inversion to avoid an sklearn dependency.
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


def _balanced_class_weights(y_array) -> dict[int, float]:
    """Inverse-frequency weights (matches sklearn 'balanced' formula).

    weight(c) = n_samples / (n_classes * n_samples_of_c).
    Pure numpy; no sklearn dependency.
    """
    numpy = importlib.import_module("numpy")
    unique, counts = numpy.unique(y_array, return_counts=True)
    total = int(y_array.shape[0])
    n_classes = int(unique.shape[0]) if unique.shape[0] > 0 else 1
    weights: dict[int, float] = {}
    for class_id, count in zip(unique.tolist(), counts.tolist()):
        denom = max(int(count) * n_classes, 1)
        weights[int(class_id)] = float(total) / float(denom)
    return weights


def _load_keras_module():
    """Force the Keras torch backend, mirroring the legacy trainer."""
    backend = os.getenv("KERAS_BACKEND")
    if backend and backend != "torch":
        raise RuntimeError(
            "Story 7.5 requires KERAS_BACKEND=torch. "
            "Clear the variable or set it to 'torch'."
        )
    os.environ["KERAS_BACKEND"] = "torch"

    if importlib.util.find_spec("keras") is None:
        raise RuntimeError(
            "Story 7.5 requires the 'keras' package. "
            "Install project ML dependencies before training."
        )
    if importlib.util.find_spec("torch") is None:
        raise RuntimeError(
            "Story 7.5 requires the 'torch' package for the approved Keras backend."
        )
    return importlib.import_module("keras")


register_model(LstmClassifier())
