"""Read-only validator for supplied governance records; never authorizes work."""

from __future__ import annotations

import argparse
import json
from pathlib import Path

from parallel_truth_fingerprint.contracts.scientific_governance import parse_partition_record, parse_scientific_freeze
from parallel_truth_fingerprint.evidence.scientific_governance import (
    GovernanceProfile, validate_partition_record, validate_scientific_freeze,
)


def main() -> int:
    parser = argparse.ArgumentParser(description="Validate; never publish or authorize.")
    parser.add_argument("record", type=Path)
    parser.add_argument("--kind", choices=("partition", "freeze"), default="partition")
    parser.add_argument("--inventory", type=Path, help="JSON array of opaque source-group IDs (partition only)")
    parser.add_argument("--profile-revision", required=True)
    parser.add_argument("--audience", required=True)
    parser.add_argument("--stage", help="Exact freeze stage (freeze only)")
    parser.add_argument("--required-binding-slot", action="append", default=[])
    parser.add_argument("--predecessor", action="append", default=[], metavar="ID=STAGE")
    arguments = parser.parse_args()
    payload = json.loads(arguments.record.read_text(encoding="utf-8"))
    if arguments.kind == "partition":
        if arguments.inventory is None:
            raise SystemExit("GOV-CLI-INVENTORY-REQUIRED")
        record = parse_partition_record(payload)
        inventory = json.loads(arguments.inventory.read_text(encoding="utf-8"))
        if not isinstance(inventory, list) or any(not isinstance(item, str) for item in inventory):
            raise SystemExit("GOV-CLI-INVENTORY-INVALID")
        profile = GovernanceProfile(arguments.profile_revision, arguments.audience,
                                    ("train", "validation", "calibration", "test", "excluded"))
        result = validate_partition_record(record, inventory_groups=tuple(inventory), profile=profile)
    else:
        if not arguments.stage:
            raise SystemExit("GOV-CLI-STAGE-REQUIRED")
        predecessor_stages = {}
        for item in arguments.predecessor:
            if item.count("=") != 1:
                raise SystemExit("GOV-CLI-PREDECESSOR-INVALID")
            key, value = item.split("=", 1)
            predecessor_stages[key] = value
        record = parse_scientific_freeze(payload)
        profile = GovernanceProfile(arguments.profile_revision, arguments.audience,
                                    freeze_stage=arguments.stage,
                                    required_binding_slots=tuple(arguments.required_binding_slot))
        result = validate_scientific_freeze(record, profile=profile, predecessor_stages=predecessor_stages)
    print(json.dumps({"allowed": result.allowed, "authorization_effect": result.authorization_effect,
                      "violations": [item.__dict__ for item in result.violations]}, sort_keys=True))
    return 0 if result.allowed else 1


if __name__ == "__main__":
    raise SystemExit(main())
