"""Build the custom mA + Linux edge-syscall dataset from one live capture."""

from __future__ import annotations

import argparse
import json
from pathlib import Path
import sys


ROOT = Path(__file__).resolve().parents[1]
sys.path.insert(0, str(ROOT / "src"))


def main() -> None:
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument("--run-id", required=True)
    parser.add_argument("--capture-dir", type=Path, required=True)
    parser.add_argument("--output-dir", type=Path, default=None)
    parser.add_argument("--minio-endpoint", default="localhost:9000")
    parser.add_argument("--minio-access-key", default="minioadmin")
    parser.add_argument("--minio-secret-key", default="minioadmin")
    parser.add_argument("--minio-bucket", default="ptfp-syscall-live")
    parser.add_argument("--minio-secure", action="store_true")
    args = parser.parse_args()

    from parallel_truth_fingerprint.evidence.custom_campaign import (
        build_synchronized_campaign_dataset,
    )
    from parallel_truth_fingerprint.persistence import MinioArtifactStore, MinioStoreConfig

    runtime_path = args.capture_dir / "runtime.json"
    runtime_payload = json.loads(runtime_path.read_text(encoding="utf-8"))
    store = MinioArtifactStore(
        MinioStoreConfig(
            endpoint=args.minio_endpoint,
            access_key=args.minio_access_key,
            secret_key=args.minio_secret_key,
            bucket=args.minio_bucket,
            secure=args.minio_secure,
        )
    )
    keys = [
        str(cycle["artifact_key"])
        for cycle in runtime_payload.get("cycle_history", [])
        if isinstance(cycle, dict) and cycle.get("persistence_status") == "persisted"
    ]
    artifacts = []
    for key in keys:
        artifact = store.load_json(key)
        artifact["artifact_key"] = key
        artifacts.append(artifact)
    output_dir = args.output_dir or (ROOT / "evidence" / "custom-dataset" / args.run_id)
    manifest = build_synchronized_campaign_dataset(
        campaign_id=args.run_id,
        capture_directory=args.capture_dir,
        runtime_payload=runtime_payload,
        artifacts=artifacts,
        output_directory=output_dir,
    )
    print(json.dumps(manifest.to_dict(), indent=2, sort_keys=True))


if __name__ == "__main__":
    main()
