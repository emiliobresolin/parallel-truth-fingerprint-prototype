"""Story 7.9 CLI: drive a hyperparameter sweep from a JSON config file.

Usage:
    .venv\\Scripts\\python.exe scripts\\train_lstm_sweep.py \\
        --config scripts\\sweeps\\adfa_ld_first_sweep.json \\
        --output _bmad-output\\implementation-artifacts\\7-9-adfa-ld-sweep-summary.md \\
        --persist

Requires ADFA_LD_PATH for adfa-ld sweeps. --persist writes every run via
Story 7.3's MinIO-backed training history.
"""

from __future__ import annotations

import argparse
import json
import sys
from pathlib import Path


def main(argv: list[str] | None = None) -> int:
    parser = argparse.ArgumentParser(
        prog="train_lstm_sweep",
        description="Drive a hyperparameter sweep of the offline training track.",
    )
    parser.add_argument("--config", required=True, type=Path)
    parser.add_argument("--output", required=True, type=Path)
    parser.add_argument("--persist", action="store_true")
    parser.add_argument(
        "--persist-local",
        type=Path,
        default=None,
        help=(
            "Persist runs to a local filesystem store rooted at this path. "
            "Use when MinIO is not available; alternative to --persist."
        ),
    )
    parser.add_argument("--minio-endpoint", type=str, default="localhost:9000")
    parser.add_argument("--minio-access-key", type=str, default="minioadmin")
    parser.add_argument("--minio-secret-key", type=str, default="minioadmin")
    parser.add_argument(
        "--minio-bucket", type=str, default="fingerprint-training-history"
    )
    parser.add_argument("--minio-secure", action="store_true")
    args = parser.parse_args(argv)

    config = json.loads(args.config.read_text(encoding="utf-8"))

    from parallel_truth_fingerprint.lstm_service.offline_training.training.sweep import (
        run_sweep,
        summarize_sweep,
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
    elif args.persist:
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
    else:
        # Without --persist we still need an artifact_store-like object that
        # accepts save_json calls; reuse the FakeMinioClient-backed store so
        # the harness contract remains intact.
        from parallel_truth_fingerprint.persistence import (
            MinioArtifactStore,
            MinioStoreConfig,
        )
        # Importing tests.persistence.test_service from a runtime script is
        # awkward; instead provide a minimal inline shim.
        from io import BytesIO

        class _InMemoryClient:
            def __init__(self) -> None:
                self.buckets: set[str] = set()
                self.objects: dict[tuple[str, str], bytes] = {}

            def bucket_exists(self, bucket_name: str) -> bool:
                return bucket_name in self.buckets

            def make_bucket(self, bucket_name: str) -> None:
                self.buckets.add(bucket_name)

            def put_object(
                self,
                bucket_name: str,
                object_name: str,
                data,
                *,
                length: int,
                content_type: str,
            ) -> None:
                self.objects[(bucket_name, object_name)] = data.read(length)

            def list_objects(
                self,
                bucket_name: str,
                *,
                prefix: str = "",
                recursive: bool = False,
            ):
                for (current_bucket, object_name), payload in sorted(
                    self.objects.items()
                ):
                    if current_bucket != bucket_name:
                        continue
                    if not object_name.startswith(prefix):
                        continue
                    yield type(
                        "MinioObject",
                        (),
                        {"object_name": object_name, "size": len(payload)},
                    )()

            def get_object(self, bucket_name: str, object_name: str):
                payload = self.objects[(bucket_name, object_name)]

                class _Response:
                    def __init__(self, data: bytes) -> None:
                        self._data = data

                    def read(self) -> bytes:
                        return self._data

                    def close(self) -> None:
                        return None

                    def release_conn(self) -> None:
                        return None

                return _Response(payload)

        store = MinioArtifactStore(
            MinioStoreConfig(
                endpoint="in-memory",
                access_key="",
                secret_key="",
                bucket=args.minio_bucket,
                secure=False,
            ),
            client=_InMemoryClient(),
        )

    results = run_sweep(config, artifact_store=store)
    report = summarize_sweep([record for record, _ in results])
    args.output.parent.mkdir(parents=True, exist_ok=True)
    args.output.write_text(report, encoding="utf-8")
    if args.persist_local is not None:
        persist_label = f"local:{args.persist_local}"
    elif args.persist:
        persist_label = "minio"
    else:
        persist_label = "in-memory"
    print(  # noqa: T201
        f"[sweep] cells={len(results)} report={args.output} "
        f"persist={persist_label}"
    )
    return 0


if __name__ == "__main__":
    sys.exit(main())
