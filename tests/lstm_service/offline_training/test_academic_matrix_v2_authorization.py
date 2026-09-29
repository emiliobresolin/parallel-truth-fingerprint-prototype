"""Tests for explicit owner authorization of the thesis Matrix V2 protocol."""

from __future__ import annotations

from copy import deepcopy
import json
from pathlib import Path
import unittest

from parallel_truth_fingerprint.contracts.parameter_evidence import (
    AccountabilityOutcome,
    TemporalGateContext,
)
from parallel_truth_fingerprint.evidence.parameter_evidence import (
    source_catalog_identity,
    validate_parameter_gate,
)
from parallel_truth_fingerprint.evidence.source_catalog import load_source_catalog
from parallel_truth_fingerprint.lstm_service.offline_training.academic_runner import (
    config_identity,
    load_academic_config,
)
from scripts.authorize_academic_matrix_v2 import (
    APPROVAL_SCHEMA,
    INVENTORY_ID,
    REQUIRED_SET_ID,
    build_authority_bundle,
)


ROOT = Path(__file__).resolve().parents[3]
CONFIG_PATH = ROOT / "configs" / "experiments" / "thesis-evaluation-v2.json"
APPROVAL_PATH = ROOT / "configs" / "experiments" / "thesis-evaluation-v2.approval-v1.json"
SOURCE_CATALOG_PATH = ROOT / "docs" / "reference-archive" / "catalog" / "source-catalog.v1.json"


class AcademicMatrixV2AuthorizationTests(unittest.TestCase):
    def _approval(self, config: dict[str, object]) -> dict[str, object]:
        approval = json.loads(APPROVAL_PATH.read_text(encoding="utf-8"))
        assert isinstance(approval, dict)
        approval["candidate_config_identity"] = config_identity(config)
        authority = config["numeric_authority"]
        assert isinstance(authority, dict)
        approval["candidate_requirements_sha256"] = authority["requirements_sha256"]
        return approval

    def test_all_205_slots_become_valid_preregistered_factor_bindings(self) -> None:
        config = load_academic_config(CONFIG_PATH)
        approval = self._approval(config)
        requirements, catalog = build_authority_bundle(
            config,
            approval,
            approval_sha256="sha256:" + "a" * 64,
            freeze_time="2026-09-27T02:09:08.748648Z",
        )

        self.assertEqual(requirements["numeric_consumer_count"], 205)
        slots = requirements["slots"]
        assert isinstance(slots, list)
        self.assertEqual(len(slots), 205)
        self.assertTrue(all(slot["authority_status"] == "approved-preregistered-factor" for slot in slots))
        self.assertTrue(all(isinstance(slot["parameter_revision_id"], str) for slot in slots))
        self.assertEqual(len(catalog.parameter_revisions), 205)
        self.assertEqual(len(catalog.decisions), 1)
        self.assertEqual(catalog.inventories[0].inventory_id, INVENTORY_ID)
        self.assertEqual(catalog.required_sets[0].required_set_id, REQUIRED_SET_ID)

        source_catalog = load_source_catalog(SOURCE_CATALOG_PATH.read_bytes())
        self.assertEqual(catalog.source_catalog_identity, source_catalog_identity(source_catalog))
        context = TemporalGateContext(
            context_id="temporal-gate-context:test",
            freeze_identity=catalog.decisions[0].record_sha256,
            freeze_time="2026-09-27T02:09:08.748648Z",
            test_identity="sha256:" + "b" * 64,
            test_time="2026-09-27T02:10:08.748648Z",
            truth_identity="sha256:" + "c" * 64,
            truth_time="2026-09-27T02:11:08.748648Z",
        )
        gate = validate_parameter_gate(
            catalog,
            source_catalog,
            catalog.inventories[0],
            catalog.required_sets[0],
            evidence_root=ROOT,
            temporal_context=context,
        )
        self.assertEqual(gate.accountability_outcome, AccountabilityOutcome.ACCOUNTABLE)
        self.assertEqual(gate.violations, ())

    def test_authorization_requires_all_groups_and_exact_candidate_binding(self) -> None:
        config = load_academic_config(CONFIG_PATH)
        approval = self._approval(config)
        incomplete = deepcopy(approval)
        groups = incomplete["groups"]
        assert isinstance(groups, list)
        incomplete["groups"] = groups[:-1]
        with self.assertRaisesRegex(ValueError, "separately approve every group"):
            build_authority_bundle(
                config,
                incomplete,
                approval_sha256="sha256:" + "a" * 64,
                freeze_time="2026-09-27T02:09:08.748648Z",
            )

        stale = deepcopy(approval)
        stale["candidate_config_identity"] = "sha256:" + "0" * 64
        with self.assertRaisesRegex(ValueError, "exact candidate config"):
            build_authority_bundle(
                config,
                stale,
                approval_sha256="sha256:" + "a" * 64,
                freeze_time="2026-09-27T02:09:08.748648Z",
            )

    def test_approval_schema_stays_explicit_and_non_authorizing_by_itself(self) -> None:
        approval = json.loads(APPROVAL_PATH.read_text(encoding="utf-8"))
        self.assertEqual(approval["schema_version"], APPROVAL_SCHEMA)
        self.assertEqual(approval["authorization_effect"], "none")
        self.assertEqual([item["group"] for item in approval["groups"]], list("1234567"))


if __name__ == "__main__":
    unittest.main()
