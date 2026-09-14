"""Persist a source-separated evaluation record for custom live campaigns."""

from __future__ import annotations

import argparse
import sys
from pathlib import Path


def main(argv: list[str] | None = None) -> int:
    parser = argparse.ArgumentParser()
    parser.add_argument("--dataset-file", action="append", required=True, type=Path)
    parser.add_argument("--seed", type=int, default=42)
    parser.add_argument("--minio-endpoint", default="localhost:9000")
    parser.add_argument("--minio-access-key", default="minioadmin")
    parser.add_argument("--minio-secret-key", default="minioadmin")
    parser.add_argument("--minio-bucket", default="fingerprint-training-history")
    parser.add_argument("--minio-secure", action="store_true")
    args = parser.parse_args(argv)

    from parallel_truth_fingerprint.evidence.custom_campaign_evaluation import (
        build_custom_campaign_evaluation,
    )
    from parallel_truth_fingerprint.lstm_service.offline_training.registry.training_history import (
        record_training_run_to_artifact_store,
    )
    from parallel_truth_fingerprint.persistence import MinioArtifactStore, MinioStoreConfig

    record = build_custom_campaign_evaluation(tuple(args.dataset_file), seed=args.seed)
    store = MinioArtifactStore(MinioStoreConfig(
        endpoint=args.minio_endpoint, access_key=args.minio_access_key,
        secret_key=args.minio_secret_key, bucket=args.minio_bucket,
        secure=args.minio_secure,
    ))
    written = record_training_run_to_artifact_store(record, store)
    print(
        f"[custom-campaign] persisted run_id={written.run_id} key={written.run_object_key} "
        f"accuracy={record.metrics['accuracy']:.4f} macro_f1={record.metrics['macro_f1']:.4f}"
    )
    return 0


if __name__ == "__main__":
    sys.exit(main())
