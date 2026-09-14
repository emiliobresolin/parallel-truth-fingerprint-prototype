"""Story 8.1 CLI: endorse a TrainingRunRecord as the live-runtime model.

Writes the chosen run id to
`<bucket>/fingerprint-training-history/index/latest.json`. The Epic 8
online inference helper reads from this single source of truth at
runtime start-up.

Usage (local filesystem store, no MinIO required):
    .venv\\Scripts\\python.exe scripts\\promote_lstm_run.py \\
        --run-id run-adfa-ld-lstm-classifier-... \\
        --persist-local _bmad-output\\local-store

Usage (real MinIO):
    .venv\\Scripts\\python.exe scripts\\promote_lstm_run.py \\
        --run-id run-adfa-ld-lstm-classifier-... \\
        --persist
"""

from __future__ import annotations

import argparse
import json
import sys
from dataclasses import asdict
from pathlib import Path


def main(argv: list[str] | None = None) -> int:
    parser = argparse.ArgumentParser(
        prog="promote_lstm_run",
        description="Endorse one training run as the live-runtime classifier.",
    )
    parser.add_argument("--run-id", required=True, type=str)
    parser.add_argument(
        "--persist-local",
        type=Path,
        default=None,
        help=(
            "Use a filesystem-backed store rooted at this path. "
            "Alternative to --persist when MinIO is not available."
        ),
    )
    parser.add_argument("--persist", action="store_true")
    parser.add_argument("--minio-endpoint", type=str, default="localhost:9000")
    parser.add_argument("--minio-access-key", type=str, default="minioadmin")
    parser.add_argument("--minio-secret-key", type=str, default="minioadmin")
    parser.add_argument(
        "--minio-bucket", type=str, default="fingerprint-training-history"
    )
    parser.add_argument("--minio-secure", action="store_true")
    args = parser.parse_args(argv)

    if args.persist_local is None and not args.persist:
        parser.error("Either --persist-local <path> or --persist is required.")

    if args.persist_local is not None:
        from parallel_truth_fingerprint.persistence import (
            LocalFileArtifactStore,
            LocalFileStoreConfig,
        )

        store = LocalFileArtifactStore(
            LocalFileStoreConfig(
                bucket=args.minio_bucket,
                root_path=Path(args.persist_local),
            )
        )
    else:
        from parallel_truth_fingerprint.persistence import (
            MinioArtifactStore,
            MinioStoreConfig,
        )

        store = MinioArtifactStore(
            MinioStoreConfig(
                endpoint=args.minio_endpoint,
                access_key=args.minio_access_key,
                secret_key=args.minio_secret_key,
                bucket=args.minio_bucket,
                secure=args.minio_secure,
            )
        )

    from parallel_truth_fingerprint.lstm_service.offline_training.registry.promotion import (
        promote_training_run,
    )

    promoted = promote_training_run(args.run_id, artifact_store=store)
    print(json.dumps(asdict(promoted), indent=2))  # noqa: T201
    return 0


if __name__ == "__main__":
    sys.exit(main())
