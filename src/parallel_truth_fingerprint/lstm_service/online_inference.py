"""Story 8.2: live-runtime inference helper for the promoted classifier.

Reads the promotion pointer written by Story 8.1, looks up the persisted
training record, rebuilds the model topology from the recorded
hyperparameters + sequence length + label space, and re-fits it once on
the original training split so a real model handle is available in the
live runtime. The fit-on-load shortcut is intentional for the academic
demonstration: it keeps Story 8.2 fully self-contained without
introducing a model-weights persistence story. Future work can persist
weights into MinIO and skip the re-fit.

This module is offline-only at import time. Importing
`online_inference` does NOT trigger any benchmark load or model build.
The user must explicitly call `OnlineLstmInferencer.load(artifact_store=...)`
to materialise the model handle.
"""

from __future__ import annotations

from dataclasses import dataclass
import importlib
from typing import Sequence

from parallel_truth_fingerprint.lstm_service.offline_training.benchmarks import (
    load_benchmark,
)
from parallel_truth_fingerprint.lstm_service.offline_training.models import (
    load_model,
)
from parallel_truth_fingerprint.lstm_service.offline_training.registry.promotion import (
    read_promoted_run,
)
from parallel_truth_fingerprint.lstm_service.offline_training.registry.training_history import (
    read_training_run,
)
from parallel_truth_fingerprint.lstm_service.offline_training.splits import (
    stratified_train_test_split,
)


@dataclass(frozen=True)
class InferenceResult:
    predicted_class_id: int
    predicted_class_name: str
    class_probabilities: tuple[float, ...]
    promoted_run_id: str


@dataclass(frozen=True)
class OnlineLstmInferencer:
    """Holds a re-fitted classifier ready to score one window at a time."""

    promoted_run_id: str
    label_names: tuple[str, ...]
    sequence_length: int
    feature_count: int
    _classifier: object  # the ClassifierAdapter
    _model_handle: object  # the trained keras model

    @classmethod
    def load(cls, *, artifact_store) -> "OnlineLstmInferencer":
        promoted = read_promoted_run(artifact_store=artifact_store)
        if promoted is None:
            raise RuntimeError(
                "No training run is currently promoted to live-runtime. "
                "Run `python scripts/promote_lstm_run.py --run-id <id> "
                "--persist-local <store>` (or --persist for MinIO) before "
                "loading the online inferencer."
            )
        record = read_training_run(
            promoted.run_id, artifact_store=artifact_store
        )

        # Rebuild and re-fit. The dataset is re-loaded with the same
        # sequence_length and seed used at training time so the split is
        # bit-identical to the persisted record.
        data = load_benchmark(
            record.dataset_name,
            sequence_length=record.sequence_length,
            seed=record.seed,
        )
        x_train, y_train, _, _, _ = stratified_train_test_split(
            data.sequences, data.labels, train_ratio=0.8, seed=record.seed
        )
        classifier = load_model(record.model_name)
        learning_rate = float(record.hyperparameters.get("learning_rate", 1e-3))
        batch_size = int(record.hyperparameters.get("batch_size", 32))
        extra = dict(record.hyperparameters.get("extra", {}))
        handle = classifier.build(
            sequence_length=record.sequence_length,
            feature_count=data.feature_count,
            class_count=len(record.label_names),
            learning_rate=learning_rate,
            seed=record.seed,
            extra_hyperparameters=extra,
        )
        fit_result = classifier.fit(
            model_handle=handle,
            x_train=x_train,
            y_train=y_train,
            epochs=record.epochs_executed,
            batch_size=batch_size,
        )

        return cls(
            promoted_run_id=promoted.run_id,
            label_names=record.label_names,
            sequence_length=record.sequence_length,
            feature_count=data.feature_count,
            _classifier=classifier,
            _model_handle=fit_result.model_handle,
        )

    def predict_sequence(
        self, window: Sequence[Sequence[float]]
    ) -> InferenceResult:
        if len(window) != self.sequence_length:
            raise ValueError(
                f"Window must have {self.sequence_length} timesteps; "
                f"got {len(window)}."
            )
        for timestep in window:
            if len(timestep) != self.feature_count:
                raise ValueError(
                    f"Each timestep must have {self.feature_count} feature(s); "
                    f"got {len(timestep)}."
                )

        numpy = importlib.import_module("numpy")
        batched = numpy.asarray(
            [[list(timestep) for timestep in window]],
            dtype="float32",
        )
        probabilities = self._model_handle.predict(batched, verbose=0)[0]  # type: ignore[index]
        class_probabilities = tuple(float(value) for value in probabilities.tolist())
        predicted_id = int(probabilities.argmax())
        return InferenceResult(
            predicted_class_id=predicted_id,
            predicted_class_name=self.label_names[predicted_id],
            class_probabilities=class_probabilities,
            promoted_run_id=self.promoted_run_id,
        )
