"""Story 7.13 CLI: build the cross-benchmark comparative report.

Reads the MinIO-backed training history (default prefix
`fingerprint-training-history/`) and writes one Markdown report to the
`--output` path.

Usage:
    .venv\\Scripts\\python.exe scripts\\build_cross_benchmark_report.py \\
        --output _bmad-output\\implementation-artifacts\\7-13-cross-benchmark-report.md \\
        --benchmark adfa-ld --benchmark lid-ds-2021

Add `--persist`-style MinIO flags identical to scripts/train_lstm_offline.py.
"""

from __future__ import annotations

import argparse
import sys
from pathlib import Path


def main(argv: list[str] | None = None) -> int:
    parser = argparse.ArgumentParser(
        prog="build_cross_benchmark_report",
        description="Aggregate persisted training runs into one Markdown report.",
    )
    parser.add_argument("--output", required=True, type=Path)
    parser.add_argument(
        "--benchmark",
        action="append",
        default=None,
        help="Repeatable. Defaults to adfa-ld and lid-ds-2021 if omitted.",
    )
    parser.add_argument(
        "--persist-local",
        type=Path,
        default=None,
        help="Use a filesystem-backed store rooted at this path instead of MinIO.",
    )
    parser.add_argument("--minio-endpoint", type=str, default="localhost:9000")
    parser.add_argument("--minio-access-key", type=str, default="minioadmin")
    parser.add_argument("--minio-secret-key", type=str, default="minioadmin")
    parser.add_argument(
        "--minio-bucket", type=str, default="fingerprint-training-history"
    )
    parser.add_argument("--minio-secure", action="store_true")
    args = parser.parse_args(argv)

    from parallel_truth_fingerprint.lstm_service.offline_training.training.cross_benchmark_report import (
        build_cross_benchmark_report,
    )

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
    benchmarks = (
        tuple(args.benchmark)
        if args.benchmark
        else ("adfa-ld", "lid-ds-2021")
    )
    report = build_cross_benchmark_report(
        artifact_store=store, benchmarks=benchmarks
    )
    args.output.parent.mkdir(parents=True, exist_ok=True)
    args.output.write_text(report, encoding="utf-8")
    print(  # noqa: T201
        f"[cross-benchmark-report] benchmarks={benchmarks} "
        f"output={args.output}"
    )
    return 0


if __name__ == "__main__":
    sys.exit(main())
