"""CLI entrypoint for the offline LSTM training track."""

from __future__ import annotations

import argparse
from collections.abc import Sequence

from parallel_truth_fingerprint.lstm_service.offline_training.registry.training_history import (
    record_training_run_to_artifact_store,
)
from parallel_truth_fingerprint.lstm_service.offline_training.training.run import (
    TrainingRunRecord,
    execute_training_run,
)


def build_argument_parser() -> argparse.ArgumentParser:
    parser = argparse.ArgumentParser(
        prog="train_lstm_offline",
        description=(
            "Run one offline supervised-classifier training cycle against a "
            "benchmark dataset. Decoupled from the live runtime."
        ),
    )
    parser.add_argument("--benchmark", required=True, type=str)
    parser.add_argument("--model", required=True, type=str)
    parser.add_argument("--epochs", required=True, type=int)
    parser.add_argument("--batch-size", required=True, type=int)
    parser.add_argument("--learning-rate", required=True, type=float)
    parser.add_argument("--sequence-length", required=True, type=int)
    parser.add_argument("--seed", required=True, type=int)
    parser.add_argument(
        "--persist",
        action="store_true",
        help=(
            "Persist the resulting TrainingRunRecord to MinIO under "
            "fingerprint-training-history/. Requires a reachable MinIO "
            "instance with the configured credentials."
        ),
    )
    parser.add_argument(
        "--persist-local",
        type=str,
        default=None,
        help=(
            "Persist the resulting TrainingRunRecord to a local filesystem "
            "store rooted at this path. Alternative to --persist when MinIO "
            "is not available."
        ),
    )
    parser.add_argument(
        "--minio-endpoint",
        type=str,
        default="localhost:9000",
        help="MinIO endpoint, only used with --persist.",
    )
    parser.add_argument(
        "--minio-access-key",
        type=str,
        default="minioadmin",
        help="MinIO access key, only used with --persist.",
    )
    parser.add_argument(
        "--minio-secret-key",
        type=str,
        default="minioadmin",
        help="MinIO secret key, only used with --persist.",
    )
    parser.add_argument(
        "--minio-bucket",
        type=str,
        default="fingerprint-training-history",
        help="MinIO bucket, only used with --persist.",
    )
    parser.add_argument(
        "--minio-secure",
        action="store_true",
        help="Use HTTPS for MinIO, only used with --persist.",
    )
    return parser


def main(argv: Sequence[str] | None = None) -> TrainingRunRecord:
    parser = build_argument_parser()
    args = parser.parse_args(argv)
    record = execute_training_run(
        benchmark=args.benchmark,
        model=args.model,
        epochs=args.epochs,
        batch_size=args.batch_size,
        learning_rate=args.learning_rate,
        sequence_length=args.sequence_length,
        seed=args.seed,
    )
    if args.persist_local is not None:
        artifact_store = _build_local_store(args)
        written = record_training_run_to_artifact_store(record, artifact_store)
        print(  # noqa: T201
            f"[offline-training] persisted run_id={written.run_id} "
            f"key={written.run_object_key} backend=local:{args.persist_local}"
        )
    elif args.persist:
        artifact_store = _build_minio_store(args)
        written = record_training_run_to_artifact_store(record, artifact_store)
        print(  # noqa: T201 — operator-facing CLI summary
            f"[offline-training] persisted run_id={written.run_id} "
            f"key={written.run_object_key} backend=minio"
        )
    print(  # noqa: T201 — operator-facing CLI summary
        f"[offline-training] run_id={record.run_id} "
        f"dataset={record.dataset_name} model={record.model_name} "
        f"epochs={record.epochs_executed}/{record.epochs_planned} "
        f"accuracy={record.metrics.get('accuracy', 0.0):.4f} "
        f"macro_precision={record.metrics.get('macro_precision', 0.0):.4f} "
        f"macro_recall={record.metrics.get('macro_recall', 0.0):.4f} "
        f"macro_f1={record.metrics.get('macro_f1', 0.0):.4f}"
    )
    return record


def _build_local_store(args):
    """Filesystem-backed store with the same surface as MinioArtifactStore."""
    from pathlib import Path

    from parallel_truth_fingerprint.persistence import (
        LocalFileArtifactStore,
        LocalFileStoreConfig,
    )

    return LocalFileArtifactStore(
        LocalFileStoreConfig(
            bucket=args.minio_bucket,
            root_path=Path(args.persist_local),
        )
    )


def _build_minio_store(args):
    """Lazy import so the smoke path (without --persist) does not pull MinIO."""
    from parallel_truth_fingerprint.persistence import (
        MinioArtifactStore,
        MinioStoreConfig,
    )

    return MinioArtifactStore(
        MinioStoreConfig(
            endpoint=args.minio_endpoint,
            access_key=args.minio_access_key,
            secret_key=args.minio_secret_key,
            bucket=args.minio_bucket,
            secure=args.minio_secure,
        )
    )


if __name__ == "__main__":  # pragma: no cover - manual entrypoint
    main()
