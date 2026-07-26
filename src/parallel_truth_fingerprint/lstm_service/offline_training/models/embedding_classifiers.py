"""Embedding-based supervised classifiers on the Keras torch backend.

These models pair with the `adfa-ld-embed` / `adfa-ld-embed-binary`
benchmarks (raw integer syscall tokens + sliding windows). They replace the
single normalised-scalar input of `lstm-classifier` with a learned
`Embedding` over the syscall vocabulary — the standard representation for
syscall-sequence classification and the change identified in the
2026-05-21 real-data evidence note as the route to the advisor's D6 metric
bar.

Topology: Input(seq, 1) -> Reshape(seq,) -> Embedding(vocab, embed_dim)
-> stacked LSTM/GRU -> Dropout -> Dense softmax. Keras 3's Embedding casts
the float-carried token ids to int internally, so no Lambda layer is
needed.

`fit` and `predict` (including the inverse-frequency class weighting that
keeps the 87%/13% ADFA-LD imbalance from collapsing to majority class) are
inherited unchanged from `LstmClassifier`.

Registered names:
    lstm-embedding-classifier
    gru-embedding-classifier

Tunable via `extra_hyperparameters` (set by the sweep config):
    vocab_size    (default 512; >= max syscall id + 1)
    embed_dim     (default 64)
    hidden_units  (default 64)
    num_layers    (default 1)
    dropout       (default 0.3)
"""

from __future__ import annotations

from dataclasses import dataclass

from parallel_truth_fingerprint.lstm_service.offline_training.models.base import (
    register_model,
)
from parallel_truth_fingerprint.lstm_service.offline_training.models.lstm_classifier import (
    LstmClassifier,
    _load_keras_module,
)


DEFAULT_VOCAB_SIZE = 512
DEFAULT_EMBED_DIM = 64
DEFAULT_HIDDEN_UNITS = 64
DEFAULT_NUM_LAYERS = 1
DEFAULT_DROPOUT = 0.3


@dataclass(frozen=True)
class _EmbeddingRnnClassifier(LstmClassifier):
    """Shared build for the embedding LSTM/GRU classifiers.

    Inherits `fit`/`predict` (with balanced class weights) from
    `LstmClassifier`; only `build` differs. `rnn_kind` selects the recurrent
    cell.
    """

    name: str = "lstm-embedding-classifier"
    rnn_kind: str = "lstm"

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
        if feature_count != 1:
            raise ValueError(
                "Embedding classifier expects feature_count == 1 "
                f"(one syscall token per timestep); got {feature_count!r}."
            )
        keras = _load_keras_module()
        keras.utils.set_random_seed(int(seed))

        vocab_size = int(extra_hyperparameters.get("vocab_size", DEFAULT_VOCAB_SIZE))
        embed_dim = int(extra_hyperparameters.get("embed_dim", DEFAULT_EMBED_DIM))
        hidden_units = int(
            extra_hyperparameters.get("hidden_units", DEFAULT_HIDDEN_UNITS)
        )
        num_layers = int(extra_hyperparameters.get("num_layers", DEFAULT_NUM_LAYERS))
        dropout = float(extra_hyperparameters.get("dropout", DEFAULT_DROPOUT))
        if vocab_size < 2:
            raise ValueError(f"vocab_size must be >= 2; got {vocab_size!r}.")
        if embed_dim < 1:
            raise ValueError(f"embed_dim must be >= 1; got {embed_dim!r}.")
        if num_layers < 1:
            raise ValueError(f"num_layers must be >= 1; got {num_layers!r}.")

        rnn_layer = keras.layers.LSTM if self.rnn_kind == "lstm" else keras.layers.GRU

        inputs = keras.Input(
            shape=(sequence_length, feature_count), name="input_sequence"
        )
        # Drop the singleton feature dim so Embedding sees (batch, seq) token
        # ids. Keras 3 Embedding casts the float-carried ids to int32.
        x = keras.layers.Reshape((sequence_length,), name="tokens")(inputs)
        x = keras.layers.Embedding(
            input_dim=vocab_size,
            output_dim=embed_dim,
            name="syscall_embedding",
        )(x)
        for layer_index in range(num_layers):
            return_sequences = layer_index < (num_layers - 1)
            x = rnn_layer(
                hidden_units,
                return_sequences=return_sequences,
                name=f"{self.rnn_kind}_layer_{layer_index + 1}",
            )(x)
        if dropout > 0.0:
            x = keras.layers.Dropout(dropout, name="dropout")(x)
        outputs = keras.layers.Dense(
            class_count, activation="softmax", name="class_softmax"
        )(x)
        model = keras.Model(
            inputs,
            outputs,
            name=f"supervised_{self.rnn_kind}_embedding_classifier",
        )
        model.compile(
            optimizer=keras.optimizers.Adam(learning_rate=float(learning_rate)),
            loss="sparse_categorical_crossentropy",
            metrics=["accuracy"],
        )
        return model


@dataclass(frozen=True)
class LstmEmbeddingClassifier(_EmbeddingRnnClassifier):
    name: str = "lstm-embedding-classifier"
    rnn_kind: str = "lstm"


@dataclass(frozen=True)
class GruEmbeddingClassifier(_EmbeddingRnnClassifier):
    name: str = "gru-embedding-classifier"
    rnn_kind: str = "gru"


register_model(LstmEmbeddingClassifier())
register_model(GruEmbeddingClassifier())
