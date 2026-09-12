"""Read-only offline validator for the Story 9.5 v1 golden corpus."""

from __future__ import annotations

import argparse
import json
import sys
from pathlib import Path


ROOT = Path(__file__).resolve().parents[1]
sys.path.insert(0, str(ROOT / "src"))

from parallel_truth_fingerprint.contracts.v1_golden_fixture import FixtureGateOutcome
from parallel_truth_fingerprint.evidence.v1_golden_fixtures import load_catalog, validate_catalog


def parse_args() -> argparse.Namespace:
    parser = argparse.ArgumentParser(description="Validate registered v1 fixtures without side effects.")
    parser.add_argument("--catalog", required=True, type=Path)
    parser.add_argument("--fixture-root", required=True, type=Path)
    parser.add_argument("--machine", action="store_true")
    return parser.parse_args()


def main() -> int:
    args = parse_args()
    try:
        catalog = load_catalog(args.catalog.read_bytes())
        result = validate_catalog(catalog, fixture_root=args.fixture_root)
    except (OSError, TypeError, ValueError) as exc:
        print(f"GOLD-INPUT-MALFORMED\t{exc}")
        return 2
    if args.machine:
        print(json.dumps(result.to_dict(), sort_keys=True, ensure_ascii=False,
                         separators=(",", ":"), allow_nan=False))
    else:
        print(f"validation_id={result.validation_id}")
        print(f"fixture_gate_outcome={result.fixture_gate_outcome}")
        print("authorization_effect=none")
        for item in result.violations:
            print(
                f"{item.rule_id}\t{item.fixture_or_requirement_id}\t{item.contract_id}\t"
                f"{item.field_path}\t{item.expected_value}\t{item.observed_value}"
            )
    return 0 if result.fixture_gate_outcome == FixtureGateOutcome.ACCEPTED else 1


if __name__ == "__main__":
    raise SystemExit(main())
