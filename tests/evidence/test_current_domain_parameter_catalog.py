from __future__ import annotations

from pathlib import Path
import unittest

from parallel_truth_fingerprint.contracts.parameter_evidence import AccountabilityOutcome
from parallel_truth_fingerprint.evidence.parameter_evidence import (
    canonical_parameter_catalog_bytes,
    load_parameter_catalog,
    validate_parameter_gate,
)
from parallel_truth_fingerprint.evidence.source_catalog import load_source_catalog


ROOT = Path(__file__).resolve().parents[2]


class CurrentDomainParameterCatalogTests(unittest.TestCase):
    def test_archived_current_domain_gate_is_accountable(self) -> None:
        catalog_path = ROOT / "docs/reference-archive/catalog/parameter-evidence-current-domain.v1.json"
        catalog = load_parameter_catalog(catalog_path.read_bytes())
        source = load_source_catalog((ROOT / "docs/reference-archive/catalog/source-catalog.v1.json").read_bytes())

        self.assertEqual(catalog_path.read_bytes(), canonical_parameter_catalog_bytes(catalog))
        self.assertEqual(len(catalog.parameter_revisions), 1)
        self.assertEqual(catalog.parameter_revisions[0].value.to_dict()["lower"], "4")
        self.assertEqual(catalog.parameter_revisions[0].value.to_dict()["upper"], "20")
        result = validate_parameter_gate(catalog, source, catalog.inventories[0], catalog.required_sets[0])
        self.assertEqual(result.accountability_outcome, AccountabilityOutcome.ACCOUNTABLE,
                         [item.to_dict() for item in result.violations])


if __name__ == "__main__":
    unittest.main()
