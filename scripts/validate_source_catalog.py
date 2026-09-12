"""Read-only validator and deterministic projection reporter for SourceCatalog.v1."""

from __future__ import annotations

import argparse
import sys
from pathlib import Path

PROJECT_ROOT = Path(__file__).resolve().parents[1]
sys.path.insert(0, str(PROJECT_ROOT / "src"))

from parallel_truth_fingerprint.evidence.source_catalog import (
    canonical_catalog_bytes,
    checksum_projection,
    human_index_projection,
    load_source_catalog,
    validate_source_catalog,
)


def parse_args() -> argparse.Namespace:
    parser = argparse.ArgumentParser(description="Validate SourceCatalog.v1 without network or writes.")
    parser.add_argument(
        "--catalog",
        type=Path,
        default=Path("docs/reference-archive/catalog/source-catalog.v1.json"),
    )
    parser.add_argument(
        "--archive-root",
        type=Path,
        help="optional documents root used only to verify declared local opaque bytes",
    )
    parser.add_argument(
        "--prior-catalog",
        type=Path,
        help="optional prior catalog used only for append-only identity validation",
    )
    parser.add_argument("--check", action="store_true", help="compare all checked-in projections")
    parser.add_argument(
        "--projection",
        choices=("catalog", "index", "checksums", "summary"),
        default="summary",
        help="render a proposed deterministic representation to stdout",
    )
    return parser.parse_args()


def main() -> int:
    args = parse_args()
    try:
        catalog = load_source_catalog(args.catalog.read_bytes())
        prior_catalog = (
            load_source_catalog(args.prior_catalog.read_bytes()) if args.prior_catalog else None
        )
    except (OSError, TypeError, ValueError) as exc:
        print(f"SRC-CATALOG-PARSE-ERROR\tcatalog\t{exc}", file=sys.stderr)
        return 2
    result = validate_source_catalog(
        catalog, documents_root=args.archive_root, prior_catalog=prior_catalog
    )
    if not result.valid:
        for violation in result.violations:
            print(
                f"{violation.rule_id}\t{violation.record_id}\t{','.join(violation.fields)}\t"
                f"{violation.explanation}",
                file=sys.stderr,
            )
        return 1

    catalog_bytes = canonical_catalog_bytes(catalog)
    index_text = human_index_projection(catalog)
    checksums_text = checksum_projection(catalog)
    if args.check:
        catalog_dir = args.catalog.parent
        drift = []
        if args.catalog.read_bytes() != catalog_bytes:
            drift.append(args.catalog)
        if (catalog_dir / "index.md").read_text(encoding="utf-8") != index_text:
            drift.append(catalog_dir / "index.md")
        if (catalog_dir / "checksums.sha256").read_text(encoding="utf-8") != checksums_text:
            drift.append(catalog_dir / "checksums.sha256")
        if drift:
            for path in drift:
                print(f"projection drift: {path}", file=sys.stderr)
            return 1

    if args.projection == "catalog":
        sys.stdout.buffer.write(catalog_bytes)
    elif args.projection == "index":
        print(index_text, end="")
    elif args.projection == "checksums":
        print(checksums_text, end="")
    else:
        print(f"schema_version={catalog.schema_version}")
        print(f"sources={len(catalog.sources)}")
        print(f"revisions={len(catalog.revisions)}")
        print(f"contents={len(catalog.contents)}")
        print(f"retrievals={len(catalog.retrievals)}")
        print(f"uses={len(catalog.uses)}")
        print("authorization_effect=none")
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
