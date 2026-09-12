"""Read-only ParameterEvidence.v1 accountability gate."""

from __future__ import annotations

import argparse
import sys
from pathlib import Path

ROOT = Path(__file__).resolve().parents[1]
sys.path.insert(0, str(ROOT / "src"))

from parallel_truth_fingerprint.contracts.parameter_evidence import AccountabilityOutcome
from parallel_truth_fingerprint.evidence.parameter_evidence import (
    canonical_parameter_catalog_bytes,
    load_parameter_catalog,
    validate_parameter_gate,
)
from parallel_truth_fingerprint.evidence.source_catalog import load_source_catalog


def parse_args() -> argparse.Namespace:
    parser = argparse.ArgumentParser(description="Validate numerical accountability without side effects.")
    parser.add_argument("--catalog", type=Path, required=True)
    parser.add_argument("--source-catalog", type=Path, required=True)
    parser.add_argument(
        "--consumer-inventory", type=Path, required=True,
        help="ParameterEvidence.v1 authority containing exactly one selected inventory",
    )
    parser.add_argument(
        "--required-set", type=Path, required=True,
        help="ParameterEvidence.v1 authority containing exactly one selected required set",
    )
    parser.add_argument("--evidence-root", type=Path)
    parser.add_argument("--canonical", action="store_true")
    return parser.parse_args()


def main() -> int:
    args = parse_args()
    try:
        catalog = load_parameter_catalog(args.catalog.read_bytes())
        source_catalog = load_source_catalog(args.source_catalog.read_bytes())
        inventory_catalog = load_parameter_catalog(args.consumer_inventory.read_bytes())
        required_catalog = load_parameter_catalog(args.required_set.read_bytes())
        if len(inventory_catalog.inventories) != 1 or len(required_catalog.required_sets) != 1:
            raise ValueError("selection files must contain exactly one inventory/required set")
        inventory = inventory_catalog.inventories[0]
        required_set = required_catalog.required_sets[0]
    except (OSError, TypeError, ValueError) as exc:
        print(f"PAR-INPUT-MALFORMED\t{exc}")
        return 2

    try:
        result = validate_parameter_gate(
            catalog, source_catalog, inventory, required_set, evidence_root=args.evidence_root
        )
    except (OSError, TypeError, ValueError) as exc:
        print(f"PAR-INPUT-MALFORMED\t{exc}")
        return 2
    if args.canonical:
        sys.stdout.buffer.write(canonical_parameter_catalog_bytes(catalog))
    print(f"gate_result_id={result.gate_result_id}")
    print(f"accountability_outcome={result.accountability_outcome}")
    print("authorization_effect=none")
    for item in result.violations:
        print(f"{item.rule_id}\t{item.record_id}\t{item.field_path}\t{item.offending_reference}")
    return 0 if result.accountability_outcome == AccountabilityOutcome.ACCOUNTABLE else 1


if __name__ == "__main__":
    raise SystemExit(main())
