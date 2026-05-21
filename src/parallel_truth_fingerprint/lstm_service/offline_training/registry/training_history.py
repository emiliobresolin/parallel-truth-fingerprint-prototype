"""Persist offline TrainingRunRecord instances to the local MinIO bucket.

Layout (architecture-update-2026-05-21.md section B.2):

    fingerprint-training-history/
      runs/
        <run_id>.json
        <run_id>.confusion.json
      index/
        by-benchmark/
          <dataset>.json     ({"dataset": str, "run_ids": [str, ...]})

Reuses the project's existing `MinioArtifactStore`; in tests, the existing
`FakeMinioClient` is injected so no network is required.
"""

from __future__ import annotations

from dataclasses import dataclass

from parallel_truth_fingerprint.lstm_service.offline_training.splits import (
    SplitRecord,
)
from parallel_truth_fingerprint.lstm_service.offline_training.training.run import (
    TrainingRunRecord,
)


HISTORY_PREFIX = "fingerprint-training-history/"
RUNS_SUBPREFIX = "runs/"
INDEX_SUBPREFIX = "index/by-benchmark/"


@dataclass(frozen=True)
class WrittenRun:
    """Pointers returned by `write_training_run`."""

    run_id: str
    run_object_key: str
    confusion_object_key: str
    index_object_key: str


def serialize_training_run(record: TrainingRunRecord) -> dict[str, object]:
    """Convert a TrainingRunRecord into a JSON-safe dict."""

    return {
        "run_id": record.run_id,
        "created_at": record.created_at,
        "dataset_name": record.dataset_name,
        "model_name": record.model_name,
        "seed": int(record.seed),
        "sequence_length": int(record.sequence_length),
        "epochs_planned": int(record.epochs_planned),
        "epochs_executed": int(record.epochs_executed),
        "hyperparameters": dict(record.hyperparameters),
        "metrics": {key: float(value) for key, value in record.metrics.items()},
        "per_class_metrics": {
            key: [float(v) for v in values]
            for key, values in record.per_class_metrics.items()
        },
        "per_epoch_loss": [float(v) for v in record.per_epoch_loss],
        "parameter_count": int(record.parameter_count),
        "split_record": _serialize_split_record(record.split_record),
        "confusion_matrix": (
            None
            if record.confusion_matrix is None
            else [list(row) for row in record.confusion_matrix]
        ),
        "dataset_provenance": _normalize_provenance_for_json(
            record.dataset_provenance
        ),
        "label_names": list(record.label_names),
    }


def deserialize_training_run(payload: dict[str, object]) -> TrainingRunRecord:
    """Rebuild a TrainingRunRecord from its serialized dict."""

    return TrainingRunRecord(
        run_id=str(payload["run_id"]),
        created_at=str(payload["created_at"]),
        dataset_name=str(payload["dataset_name"]),
        model_name=str(payload["model_name"]),
        seed=int(payload["seed"]),
        sequence_length=int(payload["sequence_length"]),
        epochs_planned=int(payload["epochs_planned"]),
        epochs_executed=int(payload["epochs_executed"]),
        hyperparameters=dict(payload["hyperparameters"]),  # type: ignore[arg-type]
        metrics={
            str(key): float(value)
            for key, value in dict(payload["metrics"]).items()  # type: ignore[arg-type]
        },
        per_class_metrics={
            str(key): tuple(float(v) for v in values)
            for key, values in dict(  # type: ignore[arg-type]
                payload["per_class_metrics"]
            ).items()
        },
        per_epoch_loss=tuple(float(v) for v in payload["per_epoch_loss"]),  # type: ignore[arg-type]
        parameter_count=int(payload["parameter_count"]),
        split_record=_deserialize_split_record(payload.get("split_record")),
        confusion_matrix=_deserialize_confusion_matrix(
            payload.get("confusion_matrix")
        ),
        dataset_provenance=dict(payload.get("dataset_provenance") or {}),
        label_names=tuple(
            str(name) for name in (payload.get("label_names") or ())
        ),
    )


def write_training_run(
    record: TrainingRunRecord,
    *,
    artifact_store,
    prefix: str = HISTORY_PREFIX,
) -> WrittenRun:
    """Persist one TrainingRunRecord to the MinIO-backed training history."""

    payload = serialize_training_run(record)
    confusion_payload = {
        "run_id": record.run_id,
        "dataset_name": record.dataset_name,
        "confusion_matrix": (
            None
            if record.confusion_matrix is None
            else [list(row) for row in record.confusion_matrix]
        ),
    }
    run_object_key = f"{prefix}{RUNS_SUBPREFIX}{record.run_id}.json"
    confusion_object_key = (
        f"{prefix}{RUNS_SUBPREFIX}{record.run_id}.confusion.json"
    )
    index_object_key = (
        f"{prefix}{INDEX_SUBPREFIX}{record.dataset_name}.json"
    )

    artifact_store.save_json(run_object_key, payload)
    artifact_store.save_json(confusion_object_key, confusion_payload)
    _update_benchmark_index(
        artifact_store=artifact_store,
        index_object_key=index_object_key,
        dataset_name=record.dataset_name,
        run_id=record.run_id,
    )
    return WrittenRun(
        run_id=record.run_id,
        run_object_key=run_object_key,
        confusion_object_key=confusion_object_key,
        index_object_key=index_object_key,
    )


def record_training_run_to_artifact_store(
    record: TrainingRunRecord, artifact_store
) -> WrittenRun:
    """One-shot helper used by Story 7.7 and downstream stories."""
    return write_training_run(record, artifact_store=artifact_store)


def list_training_runs(
    *,
    artifact_store,
    benchmark: str | None = None,
    prefix: str = HISTORY_PREFIX,
) -> tuple[str, ...]:
    """Return run_ids for one benchmark, or for all benchmarks if None."""

    if benchmark is not None:
        index_object_key = f"{prefix}{INDEX_SUBPREFIX}{benchmark}.json"
        try:
            payload = artifact_store.load_json(index_object_key)
        except Exception:
            return ()
        return tuple(str(run_id) for run_id in payload.get("run_ids", []))

    all_run_ids: list[str] = []
    index_prefix = f"{prefix}{INDEX_SUBPREFIX}"
    for index_object_key in artifact_store.list_json_objects(prefix=index_prefix):
        payload = artifact_store.load_json(index_object_key)
        all_run_ids.extend(str(run_id) for run_id in payload.get("run_ids", []))
    return tuple(all_run_ids)


def read_training_run(
    run_id: str,
    *,
    artifact_store,
    prefix: str = HISTORY_PREFIX,
) -> TrainingRunRecord:
    """Load one TrainingRunRecord by its run_id."""
    run_object_key = f"{prefix}{RUNS_SUBPREFIX}{run_id}.json"
    payload = artifact_store.load_json(run_object_key)
    return deserialize_training_run(payload)


def _serialize_split_record(record: SplitRecord | None) -> dict[str, object] | None:
    if record is None:
        return None
    return {
        "seed": int(record.seed),
        "train_ratio": float(record.train_ratio),
        "total_samples": int(record.total_samples),
        "train_samples": int(record.train_samples),
        "test_samples": int(record.test_samples),
        "per_class_counts_train": {
            str(class_id): int(count)
            for class_id, count in record.per_class_counts_train.items()
        },
        "per_class_counts_test": {
            str(class_id): int(count)
            for class_id, count in record.per_class_counts_test.items()
        },
    }


def _deserialize_split_record(payload: object) -> SplitRecord | None:
    if payload is None:
        return None
    if not isinstance(payload, dict):
        raise TypeError("split_record payload must be a dict or None.")
    return SplitRecord(
        seed=int(payload["seed"]),
        train_ratio=float(payload["train_ratio"]),
        total_samples=int(payload["total_samples"]),
        train_samples=int(payload["train_samples"]),
        test_samples=int(payload["test_samples"]),
        per_class_counts_train={
            int(class_id): int(count)
            for class_id, count in dict(payload["per_class_counts_train"]).items()
        },
        per_class_counts_test={
            int(class_id): int(count)
            for class_id, count in dict(payload["per_class_counts_test"]).items()
        },
    )


def _deserialize_confusion_matrix(
    payload: object,
) -> tuple[tuple[int, ...], ...] | None:
    if payload is None:
        return None
    return tuple(tuple(int(v) for v in row) for row in payload)  # type: ignore[union-attr]


def _normalize_provenance_for_json(provenance: dict[str, object]) -> dict[str, object]:
    """Make provenance values JSON-safe (lists for tuples, str keys for dicts)."""
    result: dict[str, object] = {}
    for key, value in provenance.items():
        result[str(key)] = _to_json_safe(value)
    return result


def _to_json_safe(value: object) -> object:
    if isinstance(value, dict):
        return {str(k): _to_json_safe(v) for k, v in value.items()}
    if isinstance(value, (list, tuple)):
        return [_to_json_safe(v) for v in value]
    if isinstance(value, (str, int, float, bool)) or value is None:
        return value
    return str(value)


def _update_benchmark_index(
    *,
    artifact_store,
    index_object_key: str,
    dataset_name: str,
    run_id: str,
) -> None:
    try:
        existing = artifact_store.load_json(index_object_key)
    except Exception:
        existing = {"dataset": dataset_name, "run_ids": []}

    run_ids = list(existing.get("run_ids", []))
    if run_id not in run_ids:
        run_ids.append(run_id)
    artifact_store.save_json(
        index_object_key,
        {"dataset": dataset_name, "run_ids": run_ids},
    )
