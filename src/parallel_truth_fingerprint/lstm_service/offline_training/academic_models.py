"""Academic anomaly detectors with reconstructible continuous scores.

All detectors fit normal training windows only.  The two transparent
baselines make representation assumptions visible; the PCA detector is a
linear autoencoder; and the recurrent autoencoder supplies the non-linear
sequence model requested by the experimental matrix.  Every score follows
one direction: larger means more anomalous.
"""

from __future__ import annotations

from dataclasses import dataclass
from hashlib import sha256
import math
import time
import tracemalloc
from typing import Mapping, Protocol

import numpy as np


# This registry is implementation-owned because the fit implementations below,
# rather than researcher configuration, determine whether a seed can change a
# fitted detector.  The v2 runner validates every declared classification
# against it before freezing an execution schedule.
MODEL_DETERMINISM: dict[str, bool] = {
    "categorical-unigram": True,
    "robust-distance": True,
    "pca-autoencoder": True,
    "recurrent-autoencoder": False,
}


def model_is_deterministic(name: str) -> bool:
    """Return the implementation-owned randomness classification."""

    try:
        return MODEL_DETERMINISM[name]
    except KeyError as exc:
        raise ValueError(f"Unknown academic detector: {name!r}.") from exc

from parallel_truth_fingerprint.lstm_service.offline_training.academic_protocol import (
    canonical_json_hash,
)
from parallel_truth_fingerprint.lstm_service.offline_training.models.lstm_classifier import (
    _load_keras_module,
)


@dataclass(frozen=True)
class ModelFitRecord:
    model_name: str
    model_family: str
    seed: int
    hyperparameters: dict[str, object]
    epochs_planned: int
    epochs_executed: int
    convergence: dict[str, tuple[float, ...]]
    parameter_count: int
    model_bytes: int
    fit_wall_seconds: float
    fit_cpu_seconds: float
    python_peak_bytes: int
    model_identity: str
    score_direction: str = "higher-is-more-anomalous"

    def to_dict(self) -> dict[str, object]:
        return {
            "model_name": self.model_name,
            "model_family": self.model_family,
            "seed": self.seed,
            "hyperparameters": dict(self.hyperparameters),
            "epochs_planned": self.epochs_planned,
            "epochs_executed": self.epochs_executed,
            "convergence": {
                name: list(values) for name, values in self.convergence.items()
            },
            "parameter_count": self.parameter_count,
            "model_bytes": self.model_bytes,
            "fit_wall_seconds": self.fit_wall_seconds,
            "fit_cpu_seconds": self.fit_cpu_seconds,
            "python_peak_bytes": self.python_peak_bytes,
            "model_identity": self.model_identity,
            "score_direction": self.score_direction,
        }


class FittedDetector(Protocol):
    name: str

    def score(self, x: np.ndarray) -> np.ndarray:
        """Return one finite, higher-is-more-anomalous score per window."""


def fit_detector(
    name: str,
    *,
    modality: str,
    train_x: np.ndarray,
    validation_x: np.ndarray,
    seed: int,
    config: Mapping[str, object],
    categorical_vocabulary_size: int | None = None,
) -> tuple[FittedDetector, ModelFitRecord]:
    """Fit one registered detector and measure its local resource use."""

    if train_x.ndim != 3 or train_x.shape[0] == 0:
        raise ValueError("train_x must be a non-empty (window, time, feature) array.")
    if validation_x.ndim != 3 or validation_x.shape[0] == 0:
        raise ValueError("validation_x must be a non-empty 3-D array.")
    if name == "categorical-unigram":
        detector: _BaseDetector = _CategoricalUnigramDetector(
            config,
            categorical_vocabulary_size=categorical_vocabulary_size,
        )
    elif name == "robust-distance":
        detector = _RobustDistanceDetector(modality, config)
    elif name == "pca-autoencoder":
        detector = _PcaAutoencoderDetector(modality, config)
    elif name == "recurrent-autoencoder":
        detector = _RecurrentAutoencoderDetector(
            modality,
            config,
            categorical_vocabulary_size=categorical_vocabulary_size,
        )
    else:
        raise ValueError(f"Unknown academic detector: {name!r}.")

    tracemalloc.start()
    wall_start = time.perf_counter()
    cpu_start = time.process_time()
    try:
        convergence, parameter_count, model_bytes = detector.fit(
            train_x, validation_x, seed=seed
        )
        fit_cpu = time.process_time() - cpu_start
        fit_wall = time.perf_counter() - wall_start
        _, peak = tracemalloc.get_traced_memory()
    finally:
        tracemalloc.stop()
    identity = detector.identity()
    recorded_hyperparameters = {str(key): value for key, value in config.items()}
    if categorical_vocabulary_size is not None:
        recorded_hyperparameters["train_fitted_vocabulary_size"] = int(
            categorical_vocabulary_size
        )
    record = ModelFitRecord(
        model_name=name,
        model_family=detector.family,
        seed=int(seed),
        hyperparameters=recorded_hyperparameters,
        epochs_planned=int(config.get("epochs", 0)),
        epochs_executed=max((len(values) for values in convergence.values()), default=0),
        convergence={name: tuple(values) for name, values in convergence.items()},
        parameter_count=int(parameter_count),
        model_bytes=int(model_bytes),
        fit_wall_seconds=float(fit_wall),
        fit_cpu_seconds=float(fit_cpu),
        python_peak_bytes=int(peak),
        model_identity=identity,
    )
    return detector, record


class _BaseDetector:
    name = "base"
    family = "base"

    def fit(
        self, train_x: np.ndarray, validation_x: np.ndarray, *, seed: int
    ) -> tuple[dict[str, tuple[float, ...]], int, int]:
        raise NotImplementedError

    def score(self, x: np.ndarray) -> np.ndarray:
        raise NotImplementedError

    def identity(self) -> str:
        raise NotImplementedError


class _CategoricalUnigramDetector(_BaseDetector):
    name = "categorical-unigram"
    family = "transparent-categorical-frequency"

    def __init__(
        self,
        config: Mapping[str, object],
        *,
        categorical_vocabulary_size: int | None = None,
    ) -> None:
        self.alpha = float(config.get("laplace_alpha", 1.0))
        if self.alpha <= 0.0:
            raise ValueError("laplace_alpha must be positive.")
        if (
            not isinstance(categorical_vocabulary_size, int)
            or isinstance(categorical_vocabulary_size, bool)
            or categorical_vocabulary_size < 2
        ):
            raise ValueError(
                "categorical-unigram requires train-fitted vocabulary cardinality"
            )
        self.vocab_size = categorical_vocabulary_size
        self.negative_log_probability: np.ndarray | None = None

    def fit(
        self, train_x: np.ndarray, validation_x: np.ndarray, *, seed: int
    ) -> tuple[dict[str, tuple[float, ...]], int, int]:
        del validation_x, seed
        if not np.issubdtype(train_x.dtype, np.integer):
            raise ValueError("categorical-unigram requires integer token ids.")
        if np.any(train_x < 0) or np.any(train_x >= self.vocab_size):
            raise ValueError("training token IDs exceed the frozen train vocabulary")
        counts = np.bincount(
            train_x.reshape(-1), minlength=self.vocab_size
        ).astype(float)
        # Padding is not behaviour; exclude it from both denominator and score.
        counts[0] = 0.0
        denominator = float(np.sum(counts) + self.alpha * self.vocab_size)
        probabilities = (counts + self.alpha) / denominator
        self.negative_log_probability = -np.log(probabilities)
        return {}, self.vocab_size, int(self.negative_log_probability.nbytes)

    def score(self, x: np.ndarray) -> np.ndarray:
        if self.negative_log_probability is None:
            raise RuntimeError("Detector is not fitted.")
        raw = np.asarray(x)
        if not np.issubdtype(raw.dtype, np.integer):
            raise ValueError("categorical-unigram scoring requires integer token ids")
        flat = raw.reshape(x.shape[0], -1)
        if np.any(flat < 0) or np.any(flat >= self.vocab_size):
            raise ValueError(
                "scoring token IDs exceed the frozen vocabulary; unseen tokens must map to UNK"
            )
        costs = self.negative_log_probability[flat]
        mask = flat != 0
        denominator = np.maximum(np.sum(mask, axis=1), 1)
        return np.sum(costs * mask, axis=1) / denominator

    def identity(self) -> str:
        if self.negative_log_probability is None:
            raise RuntimeError("Detector is not fitted.")
        return _state_identity(
            self.name,
            {"alpha": self.alpha, "train_fitted_vocabulary_size": self.vocab_size},
            (self.negative_log_probability,),
        )


class _RobustDistanceDetector(_BaseDetector):
    name = "robust-distance"
    family = "transparent-robust-distance"

    def __init__(self, modality: str, config: Mapping[str, object]) -> None:
        self.modality = modality
        self.hash_bins = (
            int(config.get("hash_bins", 128))
            if modality == "categorical-syscall"
            else 0
        )
        self.max_robust_z = float(config.get("max_robust_z", 20.0))
        if not math.isfinite(self.max_robust_z) or self.max_robust_z <= 0.0:
            raise ValueError("max_robust_z must be finite and positive.")
        self.center: np.ndarray | None = None
        self.scale: np.ndarray | None = None

    def fit(
        self, train_x: np.ndarray, validation_x: np.ndarray, *, seed: int
    ) -> tuple[dict[str, tuple[float, ...]], int, int]:
        del validation_x, seed
        features = _window_features(train_x, self.modality, self.hash_bins)
        self.center = np.median(features, axis=0)
        mad = np.median(np.abs(features - self.center), axis=0) * 1.4826
        fallback = np.std(features, axis=0)
        self.scale = np.where(mad > 1e-8, mad, np.where(fallback > 1e-8, fallback, 1.0))
        size = self.center.nbytes + self.scale.nbytes
        return {}, int(self.center.size * 2), int(size)

    def score(self, x: np.ndarray) -> np.ndarray:
        if self.center is None or self.scale is None:
            raise RuntimeError("Detector is not fitted.")
        features = _window_features(x, self.modality, self.hash_bins)
        robust_z = np.clip(
            np.abs((features - self.center) / self.scale),
            0.0,
            self.max_robust_z,
        )
        return np.mean(robust_z * robust_z, axis=1)

    def identity(self) -> str:
        if self.center is None or self.scale is None:
            raise RuntimeError("Detector is not fitted.")
        parameters: dict[str, object] = {
            "modality": self.modality,
            "max_robust_z": self.max_robust_z,
        }
        if self.modality == "categorical-syscall":
            parameters["hash_bins"] = self.hash_bins
        return _state_identity(
            self.name,
            parameters,
            (self.center, self.scale),
        )


class _PcaAutoencoderDetector(_BaseDetector):
    name = "pca-autoencoder"
    family = "linear-autoencoder"

    def __init__(self, modality: str, config: Mapping[str, object]) -> None:
        self.modality = modality
        self.hash_bins = (
            int(config.get("hash_bins", 128))
            if modality == "categorical-syscall"
            else 0
        )
        self.latent_dimensions = int(config.get("latent_dimensions", 16))
        if self.latent_dimensions < 1:
            raise ValueError("latent_dimensions must be positive.")
        self.center: np.ndarray | None = None
        self.scale: np.ndarray | None = None
        self.components: np.ndarray | None = None

    def fit(
        self, train_x: np.ndarray, validation_x: np.ndarray, *, seed: int
    ) -> tuple[dict[str, tuple[float, ...]], int, int]:
        del validation_x, seed
        features = _window_features(train_x, self.modality, self.hash_bins)
        self.center = np.mean(features, axis=0)
        self.scale = np.std(features, axis=0)
        self.scale = np.where(self.scale > 1e-8, self.scale, 1.0)
        standardized = (features - self.center) / self.scale
        _, singular_values, right = np.linalg.svd(
            standardized, full_matrices=False
        )
        rank = min(
            self.latent_dimensions,
            right.shape[0],
            max(1, train_x.shape[0] - 1),
        )
        self.components = right[:rank]
        total_variance = float(np.sum(singular_values * singular_values))
        retained = float(np.sum(singular_values[:rank] ** 2))
        explained = 0.0 if total_variance == 0.0 else retained / total_variance
        size = self.center.nbytes + self.scale.nbytes + self.components.nbytes
        parameters = self.center.size * 2 + self.components.size
        return {"explained_variance": (explained,)}, int(parameters), int(size)

    def score(self, x: np.ndarray) -> np.ndarray:
        if self.center is None or self.scale is None or self.components is None:
            raise RuntimeError("Detector is not fitted.")
        features = _window_features(x, self.modality, self.hash_bins)
        standardized = (features - self.center) / self.scale
        encoded = standardized @ self.components.T
        reconstructed = encoded @ self.components
        return np.mean((standardized - reconstructed) ** 2, axis=1)

    def identity(self) -> str:
        if self.center is None or self.scale is None or self.components is None:
            raise RuntimeError("Detector is not fitted.")
        parameters: dict[str, object] = {
            "modality": self.modality,
            "latent_dimensions": self.latent_dimensions,
        }
        if self.modality == "categorical-syscall":
            parameters["hash_bins"] = self.hash_bins
        return _state_identity(
            self.name,
            parameters,
            (self.center, self.scale, self.components),
        )


class _RecurrentAutoencoderDetector(_BaseDetector):
    name = "recurrent-autoencoder"
    family = "nonlinear-recurrent-autoencoder"

    def __init__(
        self,
        modality: str,
        config: Mapping[str, object],
        *,
        categorical_vocabulary_size: int | None = None,
    ) -> None:
        self.modality = modality
        self.config = {str(key): value for key, value in config.items()}
        self.categorical_vocabulary_size = categorical_vocabulary_size
        self.model = None
        self.vocab_size = 0

    def fit(
        self, train_x: np.ndarray, validation_x: np.ndarray, *, seed: int
    ) -> tuple[dict[str, tuple[float, ...]], int, int]:
        categorical_cardinality: int | None = None
        if self.modality == "categorical-syscall":
            categorical_cardinality = self.categorical_vocabulary_size
            if (
                not isinstance(categorical_cardinality, int)
                or isinstance(categorical_cardinality, bool)
                or categorical_cardinality < 2
            ):
                raise ValueError(
                    "categorical recurrent models require train-fitted vocabulary "
                    "cardinality including PAD and UNK metadata"
                )
            for role, values in (("train", train_x), ("validation", validation_x)):
                tokens = np.asarray(values)
                if not np.issubdtype(tokens.dtype, np.integer):
                    raise ValueError(f"{role} categorical tokens must be integer IDs")
                if np.any(tokens < 0) or np.any(tokens >= categorical_cardinality):
                    raise ValueError(
                        f"{role} categorical token IDs exceed the frozen train vocabulary"
                    )
        keras = _load_keras_module()
        keras.utils.set_random_seed(int(seed))
        epochs = int(self.config.get("epochs", 10))
        batch_size = int(self.config.get("batch_size", 64))
        hidden_units = int(self.config.get("hidden_units", 32))
        latent_units = int(self.config.get("latent_units", 16))
        learning_rate = float(self.config.get("learning_rate", 1e-3))
        patience = int(self.config.get("patience", 3))
        if min(epochs, batch_size, hidden_units, latent_units) <= 0:
            raise ValueError("epochs, batch_size, hidden_units and latent_units must be positive.")
        sequence_length = int(train_x.shape[1])
        feature_count = int(train_x.shape[2])
        inputs = keras.Input(shape=(sequence_length, feature_count), name="sequence")
        if self.modality == "categorical-syscall":
            # Cardinality is supplied only by train-fitted preprocessing.  The
            # validation tensor can contain PAD=0 or UNK=1 but can never expand it.
            assert categorical_cardinality is not None
            self.vocab_size = categorical_cardinality
            embedding_dimensions = int(self.config.get("embedding_dimensions", 16))
            tokens = keras.layers.Reshape((sequence_length,), name="tokens")(inputs)
            encoded_input = keras.layers.Embedding(
                self.vocab_size,
                embedding_dimensions,
                mask_zero=True,
                name="embedding",
            )(tokens)
            latent = keras.layers.LSTM(latent_units, name="encoder")(encoded_input)
            repeated = keras.layers.RepeatVector(sequence_length)(latent)
            decoded = keras.layers.LSTM(
                hidden_units, return_sequences=True, name="decoder"
            )(repeated)
            outputs = keras.layers.TimeDistributed(
                keras.layers.Dense(self.vocab_size, activation="softmax"),
                name="token_reconstruction",
            )(decoded)
            loss = "sparse_categorical_crossentropy"
            train_target = train_x.reshape(train_x.shape[0], sequence_length)
            validation_target = validation_x.reshape(
                validation_x.shape[0], sequence_length
            )
            train_weight = (train_target != 0).astype(np.float32)
            validation_weight = (validation_target != 0).astype(np.float32)
        elif self.modality == "numeric-multivariate":
            latent = keras.layers.LSTM(latent_units, name="encoder")(inputs)
            repeated = keras.layers.RepeatVector(sequence_length)(latent)
            decoded = keras.layers.LSTM(
                hidden_units, return_sequences=True, name="decoder"
            )(repeated)
            outputs = keras.layers.TimeDistributed(
                keras.layers.Dense(feature_count), name="value_reconstruction"
            )(decoded)
            loss = "mse"
            train_target = train_x
            validation_target = validation_x
            train_weight = None
            validation_weight = None
        else:
            raise ValueError(f"Unsupported recurrent-autoencoder modality: {self.modality!r}.")
        self.model = keras.Model(inputs, outputs, name="academic_recurrent_autoencoder")
        self.model.compile(
            optimizer=keras.optimizers.Adam(learning_rate=learning_rate), loss=loss
        )
        callbacks = [
            keras.callbacks.EarlyStopping(
                monitor="val_loss",
                patience=patience,
                min_delta=float(self.config.get("min_delta", 1e-5)),
                restore_best_weights=True,
            )
        ]
        validation_data = (
            (validation_x, validation_target, validation_weight)
            if validation_weight is not None
            else (validation_x, validation_target)
        )
        history = self.model.fit(
            train_x,
            train_target,
            sample_weight=train_weight,
            validation_data=validation_data,
            epochs=epochs,
            batch_size=batch_size,
            shuffle=True,
            verbose=0,
            callbacks=callbacks,
        )
        convergence = {
            str(name): tuple(float(value) for value in values)
            for name, values in history.history.items()
        }
        arrays = [np.asarray(array) for array in self.model.get_weights()]
        return convergence, int(self.model.count_params()), int(sum(array.nbytes for array in arrays))

    def score(self, x: np.ndarray) -> np.ndarray:
        if self.model is None:
            raise RuntimeError("Detector is not fitted.")
        if self.modality == "categorical-syscall":
            raw_tokens = np.asarray(x)
            if not np.issubdtype(raw_tokens.dtype, np.integer):
                raise ValueError("categorical scoring requires integer token IDs")
            if np.any(raw_tokens < 0) or np.any(raw_tokens >= self.vocab_size):
                raise ValueError(
                    "scoring token IDs exceed the frozen train vocabulary; "
                    "unseen tokens must map to UNK"
                )
        prediction = np.asarray(
            self.model.predict(
                x,
                batch_size=int(self.config.get("batch_size", 64)),
                verbose=0,
            )
        )
        if self.modality == "numeric-multivariate":
            return np.mean((np.asarray(x, dtype=float) - prediction) ** 2, axis=(1, 2))
        targets = np.asarray(x, dtype=np.int64).reshape(x.shape[0], x.shape[1])
        probabilities = np.take_along_axis(
            prediction, targets[..., np.newaxis], axis=-1
        ).squeeze(-1)
        losses = -np.log(np.clip(probabilities, 1e-12, 1.0))
        mask = targets != 0
        return np.sum(losses * mask, axis=1) / np.maximum(np.sum(mask, axis=1), 1)

    def identity(self) -> str:
        if self.model is None:
            raise RuntimeError("Detector is not fitted.")
        arrays = tuple(np.asarray(array) for array in self.model.get_weights())
        return _state_identity(
            self.name,
            {
                "modality": self.modality,
                "train_fitted_vocabulary_size": (
                    self.vocab_size if self.modality == "categorical-syscall" else None
                ),
                **self.config,
            },
            arrays,
        )


def _window_features(x: np.ndarray, modality: str, hash_bins: int) -> np.ndarray:
    if x.ndim != 3:
        raise ValueError("Window input must be three-dimensional.")
    if modality == "categorical-syscall":
        if hash_bins < 2:
            raise ValueError("hash_bins must be at least two.")
        flattened = np.asarray(x, dtype=np.int64).reshape(x.shape[0], -1)
        output = np.zeros((x.shape[0], hash_bins), dtype=np.float64)
        for row_index, row in enumerate(flattened):
            non_padding = row[row != 0]
            if non_padding.size:
                bins = np.mod(non_padding, hash_bins)
                output[row_index] = np.bincount(bins, minlength=hash_bins)
                output[row_index] /= non_padding.size
        return output
    if modality == "numeric-multivariate":
        numeric = np.asarray(x, dtype=np.float64)
        return np.concatenate(
            (
                np.mean(numeric, axis=1),
                np.std(numeric, axis=1),
                np.min(numeric, axis=1),
                np.max(numeric, axis=1),
                numeric[:, -1, :] - numeric[:, 0, :],
            ),
            axis=1,
        )
    raise ValueError(f"Unsupported feature modality: {modality!r}.")


def _state_identity(
    name: str, configuration: Mapping[str, object], arrays: tuple[np.ndarray, ...]
) -> str:
    digest = sha256()
    digest.update(canonical_json_hash({"name": name, "configuration": dict(configuration)}).encode("ascii"))
    for array in arrays:
        contiguous = np.ascontiguousarray(array)
        digest.update(str(contiguous.dtype).encode("ascii"))
        digest.update(str(contiguous.shape).encode("ascii"))
        digest.update(contiguous.tobytes())
    return f"sha256:{digest.hexdigest()}"


__all__ = ["FittedDetector", "ModelFitRecord", "fit_detector"]
