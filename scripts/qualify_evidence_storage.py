"""Fail-closed entry point for the separately authorized live qualification."""
from __future__ import annotations

import argparse
import hashlib
from pathlib import Path
import shutil
import subprocess


def main() -> int:
    parser = argparse.ArgumentParser(description="Story 9.7 evidence-store qualification")
    parser.add_argument("--compose", default="compose.evidence.yml")
    parser.add_argument("--authorize-live", action="store_true")
    parser.add_argument("--project")
    parser.add_argument("--bucket")
    args = parser.parse_args()
    compose = Path(args.compose)
    if not compose.is_file():
        raise SystemExit("STORAGE-PREFLIGHT-COMPOSE-MISSING")
    digest = "sha256:" + hashlib.sha256(compose.read_bytes()).hexdigest()
    report = {"phase": "preflight", "compose_sha256": digest, "authorization_effect": "none"}
    if not args.authorize_live:
        print({**report, "qualification_result": "blocked", "rule_id": "STORAGE-LIVE-AUTHORIZATION-MISSING"})
        return 0
    if shutil.which("docker") is None or subprocess.run(
        ["docker", "version", "--format", "{{.Server.Version}}"], capture_output=True, text=True,
    ).returncode != 0:
        print({**report, "qualification_result": "blocked", "rule_id": "STORAGE-DOCKER-UNAVAILABLE"})
        return 0
    if not args.project or not args.bucket or args.bucket != "ptfp-formal-evidence-v1":
        raise SystemExit("STORAGE-LIVE-IDENTIFIERS-UNSAFE")
    raise SystemExit("STORAGE-LIVE-RUN-REQUIRES-REGISTERED-SOURCE-USES-AND-CAPABILITY-PROBE")


if __name__ == "__main__":
    raise SystemExit(main())
