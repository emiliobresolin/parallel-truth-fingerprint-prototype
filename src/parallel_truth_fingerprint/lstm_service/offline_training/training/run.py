"""Orchestrate one offline training run end-to-end.

Wires together: benchmark load -> stratified split (Story 7.2) -> model
build -> fit -> Assis-aligned metrics (Story 7.4) -> record assembly.
Story 7.3 will add MinIO persistence on top of this record.
"""

from __future__ import annotations

from dataclasses import dataclass, field
from datetime import datetime, timezone
import uuid

from parallel_truth_fingerprint.lstm_service.offline_training.benchmarks import (
    load_benchmark,
)
from parallel_truth_fingerprint.lstm_service.offline_training.models import (
    load_model,
)
from parallel_truth_fingerprint.lstm_service.offline_training.splits import (
    SplitRecord,
    stratified_train_test_split,
)
from parallel_truth_fingerprint.lstm_service.offline_training.training.metrics import (
    ClassificationMetrics,
    compute_classification_metrics,
)


@dataclass(frozen=True)
class TrainingRunRecord:
    """One end-to-end training run, in-memory.

    Story 7.3 adds MinIO persistence and a JSON schema validator on top of
    this dataclass. Story 7.5 swaps the dummy classifier for a real LSTM
    classifier; nothing in this schema needs to change for that swap.
    """

    run_id: str
    created_at: str
    dataset_name: str
    model_name: str
    seed: int
    sequence_length: int
    epochs_planned: int
    epochs_executed: int
    hyperparameters: dict[str, object]
    metrics: dict[str, float]
    per_class_metrics: dict[str, tuple[float, ...]] = field(default_factory=dict)
    per_epoch_loss: tuple[float, ...] = field(default_factory=tuple)
    parameter_count: int = 0
    split_record: SplitRecord | None = None
    confusion_matrix: tuple[tuple[int, ...], ...] | None = None
    dataset_provenance: dict[str, object] = field(default_factory=dict)
    label_names: tuple[str, ...] = ()


def execute_training_run(
    *,
    benchmark: str,
    model: str,
    epochs: int,
    batch_size: int,
    learning_rate: float,
    sequence_length: int,
    seed: int,
    extra_hyperparameters: dict[str, object] | None = None,
) -> TrainingRunRecord:
    """Run one end-to-end training cycle and return its record."""

    extra = dict(extra_hyperparameters or {})

    data = load_benchmark(benchmark, sequence_length=sequence_length, seed=seed)
    if not data.sequences:
        raise ValueError(f"Benchmark {benchmark!r} returned no sequences.")

    x_train, y_train, x_test, y_test, split_record = stratified_train_test_split(
        data.sequences, data.labels, train_ratio=0.8, seed=seed
    )

    classifier = load_model(model)
    handle = classifier.build(
        sequence_length=data.sequence_length,
        feature_count=data.feature_count,
        class_count=len(data.label_names),
        learning_rate=learning_rate,
        seed=seed,
        extra_hyperparameters=extra,
    )
    fit_result = classifier.fit(
        model_handle=handle,
        x_train=x_train,
        y_train=y_train,
        epochs=epochs,
        batch_size=batch_size,
    )
    predictions = classifier.predict(
        model_handle=fit_result.model_handle, x_test=x_test
    )

    metrics: ClassificationMetrics = compute_classification_metrics(
        predictions, y_test, class_count=len(data.label_names)
    )

    record = TrainingRunRecord(
        run_id=_build_run_id(benchmark, model),
        created_at=datetime.now(timezone.utc).isoformat(),
        dataset_name=benchmark,
        model_name=model,
        seed=seed,
        sequence_length=sequence_length,
        epochs_planned=epochs,
        epochs_executed=fit_result.epochs_executed,
        hyperparameters={
            "learning_rate": learning_rate,
            "batch_size": batch_size,
            "extra": extra,
        },
        metrics=metrics.as_run_metric_dict(),
        per_class_metrics={
            "precision": metrics.per_class_precision,
            "recall": metrics.per_class_recall,
            "f1": metrics.per_class_f1,
            "false_positive_rate": metrics.per_class_false_positive_rate,
        },
        per_epoch_loss=fit_result.per_epoch_loss,
        parameter_count=fit_result.parameter_count,
        split_record=split_record,
        confusion_matrix=metrics.confusion_matrix,
        dataset_provenance=dict(data.provenance),
        label_names=tuple(data.label_names),
    )
    return record


def _build_run_id(benchmark: str, model: str) -> str:
    stamp = datetime.now(timezone.utc).strftime("%Y%m%dT%H%M%S")
    suffix = uuid.uuid4().hex[:8]
    return f"run-{benchmark}-{model}-{stamp}-{suffix}"
