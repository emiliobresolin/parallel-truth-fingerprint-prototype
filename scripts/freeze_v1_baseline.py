"""Explicit offline command for Story 9.1 v1 baseline collection."""

from __future__ import annotations

import argparse
import sys
from collections import Counter
from pathlib import Path

from parallel_truth_fingerprint.contracts.v1_baseline import V1BaselineManifest
from parallel_truth_fingerprint.evidence.v1_baseline import (
    ALLOWED_EVIDENCE_ROOT_CATEGORIES,
    BaselineError,
    DEFAULT_EXPECTED_INVENTORY,
    build_manifest,
    publish_manifest,
    validate_manifest,
)


def parse_evidence_root(value: str, project_root: Path) -> tuple[str, str]:
    """Parse CATEGORY=PATH so scientific evidence is never role-guessed."""

    category, separator, raw_path = value.partition("=")
    if not separator or category not in ALLOWED_EVIDENCE_ROOT_CATEGORIES or not raw_path:
        allowed = ", ".join(sorted(ALLOWED_EVIDENCE_ROOT_CATEGORIES))
        raise BaselineError(f"evidence root must use an allowed CATEGORY=PATH form ({allowed})")
    candidate = Path(raw_path)
    resolved = (
        candidate.resolve(strict=False)
        if candidate.is_absolute()
        else (project_root / candidate).resolve(strict=False)
    )
    try:
        locator = resolved.relative_to(project_root).as_posix()
    except ValueError as error:
        raise BaselineError("evidence roots must remain within the project root") from error
    return category, locator


def format_summary(manifest: V1BaselineManifest) -> list[str]:
    """Build the non-authoritative, secret-safe inspection summary."""

    entries = manifest.entries
    counts = Counter(entry.category for entry in entries)
    lines = [f"baseline_id={manifest.baseline_id}"]
    lines.append("categories=" + ",".join(f"{key}:{counts[key]}" for key in sorted(counts)))
    if manifest.repository.status_verification != "verified":
        lines.append(
            "limitation=repository_status:unverifiable:Git HEAD/status identity could not be verified"
        )
    if manifest.repository.ignored_status_verification != "verified":
        lines.append(
            "limitation=ignored_status:unverifiable:ignored-worktree identity could not be verified"
        )
    for overlay in manifest.repository.dirty_overlays:
        if overlay.verification_status != "verified":
            lines.append(
                f"limitation=overlay:{overlay.locator}:{overlay.verification_status}:"
                f"{overlay.limitation}"
            )
    for entry in entries:
        if entry.verification_status != "verified":
            lines.append(
                f"limitation={entry.entry_id}:{entry.verification_status}:{entry.limitation}"
            )
    return lines


def parse_args() -> argparse.Namespace:
    parser = argparse.ArgumentParser(description="Freeze the local v1 baseline offline.")
    parser.add_argument("--project-root", type=Path, required=True)
    parser.add_argument(
        "--evidence-root",
        action="append",
        default=[],
        metavar="CATEGORY=PATH",
        help="additional project-contained evidence root with an explicit scientific category",
    )
    parser.add_argument("--observed-at", required=True)
    parser.add_argument("--publish", action="store_true")
    return parser.parse_args()


def main() -> int:
    args = parse_args()
    try:
        project_root = args.project_root.resolve(strict=False)
        inventory = None
        if args.evidence_root:
            inventory = {key: tuple(value) for key, value in DEFAULT_EXPECTED_INVENTORY.items()}
            additions: dict[str, list[str]] = {}
            for evidence_root in args.evidence_root:
                category, locator = parse_evidence_root(evidence_root, project_root)
                additions.setdefault(category, []).append(locator)
            for category, locators in additions.items():
                inventory[category] = tuple(sorted({*inventory.get(category, ()), *locators}))
        manifest = build_manifest(
            project_root=project_root,
            observed_at=args.observed_at,
            expected_inventory=inventory,
            include_declared_runtime=True,
        )
        validate_manifest(manifest)
        for line in format_summary(manifest):
            print(line)
        if args.publish:
            print(f"published={publish_manifest(project_root, manifest)}")
        return 0
    except (BaselineError, OSError, ValueError) as error:
        print(f"baseline-error: {error}", file=sys.stderr)
        return 1


if __name__ == "__main__":
    raise SystemExit(main())
