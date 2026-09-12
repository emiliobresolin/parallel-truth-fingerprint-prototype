"""Read-only inspector for the Story 9.6 manifest contract authority."""

from __future__ import annotations

import argparse
import sys
from pathlib import Path

from parallel_truth_fingerprint.evidence.manifests import (
    manifest_contract_set_bytes,
    manifest_contract_set_identity,
)


def main(argv: list[str] | None = None) -> int:
    parser = argparse.ArgumentParser(description="Validate an explicit immutable manifest contract set.")
    parser.add_argument("--contract-set", required=True, type=Path)
    parser.add_argument("--machine", action="store_true")
    args = parser.parse_args(argv)
    try:
        expected = manifest_contract_set_bytes()
        supplied = args.contract_set.read_bytes()
    except OSError as exc:
        print(f"invocation_error={exc}")
        return 2
    if supplied != expected:
        print("valid=false" if not args.machine else '{"valid":false,"rule_id":"MANIFEST-CONTRACT-SET-MISMATCH"}')
        return 1
    identity = manifest_contract_set_identity()
    if args.machine:
        print('{"authorization_effect":"none","contract_set_id":"' + identity + '","valid":true}')
    else:
        print(f"valid=true\ncontract_set_id={identity}\nauthorization_effect=none")
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
