from __future__ import annotations

import base64
import hashlib
import json
import subprocess
import sys
import tempfile
import unittest
from dataclasses import replace
from pathlib import Path

from parallel_truth_fingerprint.contracts.semantic_vocabulary import (
    DomainScope,
    EntityKind,
    EvidenceOrigin,
    EvidenceRole,
    ResultRole,
    ScientificStatus,
    SemanticIdentity,
    SyntheticStatus,
)
from parallel_truth_fingerprint.contracts.v1_golden_fixture import (
    ComparisonMode,
    FixtureGateOutcome,
    FixtureGroup,
    FixtureOrigin,
    NativeReaderOutcome,
    NativeVersionStatus,
    ReplayRoute,
    StorageEncoding,
    V1GoldenFixtureCatalog,
    V1GoldenFixtureEntry,
    V1GoldenAdapterDeclaration,
    V1GoldenReplayRequest,
)
from parallel_truth_fingerprint.evidence.v1_golden_fixtures import (
    GOLDEN_REQUIREMENT_SET,
    MAX_FIXTURE_BYTES,
    STORY_9_5_CATALOG_ID,
    canonical_catalog_bytes,
    canonical_requirement_set_bytes,
    catalog_identity,
    explicit_envelope_identity,
    fixture_revision_identity,
    load_catalog,
    load_registered_fixture_bytes,
    replay_fixture,
    replay_request_identity,
    validate_catalog,
    validate_fixture_use,
)


class V1GoldenFixtureTest(unittest.TestCase):
    ROOT = Path("testdata/golden/v1")

    def _machine_catalog_path(self) -> Path:
        return self.ROOT / "catalogs" / (
            "sha256-" + STORY_9_5_CATALOG_ID.removeprefix("sha256:")
        ) / "catalog.v1.json"

    def _semantic(self) -> SemanticIdentity:
        return SemanticIdentity(
            vocabulary_version="semantic-vocabulary.v1",
            identity_id="semantic:fixture:sentinel:v1",
            entity_kind=EntityKind.FIXTURE,
            modalities=(), representations=(), model_families=(),
            evidence_role=EvidenceRole.FIXTURE_TEST,
            result_role=ResultRole.FIXTURE_EXPECTED,
            scientific_status=ScientificStatus.TEST_ONLY,
            synthetic_status=SyntheticStatus.NOT_APPLICABLE,
            evidence_origin=EvidenceOrigin.TEST_FIXTURE,
            domain_scope=DomainScope.NOT_APPLICABLE,
            numeric_authority_references=(), formal_evidence=False,
            generation_origin=EvidenceOrigin.TEST_FIXTURE,
            limitations=("Non-domain structure sentinel only.",),
        )

    def _entry(self, payload: bytes = b'{"case":"sentinel"}') -> V1GoldenFixtureEntry:
        entry = V1GoldenFixtureEntry(
            fixture_id="fixture:mqtt:payload-basic", fixture_revision_id="",
            fixture_revision_sha256="", requirement_id="mqtt.payload.basic",
            baseline_generation="v1", native_contract_id="RawHartPayload.versionless",
            native_version_status=NativeVersionStatus.VERSIONLESS, native_version_token=None,
            baseline_id="unavailable:no-published-story-9.1-baseline",
            baseline_entry_id="unavailable:mqtt.payload.basic", baseline_entry_sha256=None,
            origin=FixtureOrigin.NON_DOMAIN_SENTINEL,
            filesystem_locator="fixtures/mqtt-payload-basic/payload.b64", object_key=None,
            storage_encoding=StorageEncoding.BASE64, media_type="application/json",
            character_encoding="utf-8", newline_form="none",
            decoded_byte_length=len(payload),
            decoded_sha256="sha256:" + hashlib.sha256(payload).hexdigest(),
            carrier_sha256=None, semantic_identity=self._semantic(),
            expected_legacy_reader_outcome=NativeReaderOutcome.ACCEPTED,
            expected_fixture_gate_outcome=FixtureGateOutcome.UNVERIFIABLE,
            expected_reason="Story 9.1 baseline is not published in this workspace.",
            expected_output_sha256=None, reader_id="python.json.v1",
            comparison_mode=ComparisonMode.SEMANTIC_EXACT,
            comparator_id="json.type-strict.v1", comparator_version="1",
            compared_fields=("case",), order_rules="object keys unordered; array order exact",
            reconstruction_identity="sha256:" + "1" * 64,
            mock_admission_id=None, parameter_revision_bindings=(),
            limitations=("Non-domain sentinel; not historical capture.",),
            prohibited_uses=("dataset", "training", "metric", "truth", "final_result"),
        )
        revision_id = fixture_revision_identity(entry)
        return replace(entry, fixture_revision_id=revision_id, fixture_revision_sha256=revision_id)

    def _catalog(self, entry: V1GoldenFixtureEntry) -> V1GoldenFixtureCatalog:
        catalog = V1GoldenFixtureCatalog(
            schema_version="v1-golden-fixture-catalog.v1", catalog_id="",
            requirement_set_id=GOLDEN_REQUIREMENT_SET.requirement_set_id,
            entries=(entry,), adapters=(), limitations=("Fixture replay only.",),
        )
        return replace(catalog, catalog_id=catalog_identity(catalog))

    def _machine_catalog(self) -> V1GoldenFixtureCatalog:
        return load_catalog(self._machine_catalog_path().read_bytes())

    def _machine_entry(self, requirement_id: str) -> V1GoldenFixtureEntry:
        matches = [
            entry for entry in self._machine_catalog().entries
            if entry.requirement_id == requirement_id
        ]
        self.assertEqual(len(matches), 1, requirement_id)
        return matches[0]

    def test_code_owned_requirement_inventory_is_pinned_and_complete(self) -> None:
        requirements = {item.requirement_id: item for item in GOLDEN_REQUIREMENT_SET.requirements}
        self.assertEqual(GOLDEN_REQUIREMENT_SET.authorization_effect, "none")
        self.assertTrue({
            "mqtt.topic", "mqtt.payload.basic", "mqtt.payload.optional_sv",
            "consensus.python.transaction", "consensus.go.transaction",
            "consensus.query.found", "consensus.query.missing", "consensus.divergence",
            "persistence.object.content", "persistence.object.missing",
            "manifest.dataset", "manifest.artifact", "detector.input.schema",
            "detector.input.missing", "detector.input.extra", "detector.input.permuted",
        }.issubset(requirements))
        self.assertTrue(any(item.group == FixtureGroup.OPTIONAL_DASHBOARD
                            for item in requirements.values()))
        authorities = list(self.ROOT.glob("requirements/sha256-*/requirements.v1.json"))
        self.assertEqual(len(authorities), 1)
        self.assertEqual(authorities[0].read_bytes(),
                         canonical_requirement_set_bytes(GOLDEN_REQUIREMENT_SET))

    def test_catalog_and_fixture_identities_are_deterministic(self) -> None:
        entry = self._entry()
        catalog = self._catalog(entry)
        self.assertEqual(entry.fixture_revision_id, fixture_revision_identity(entry))
        self.assertEqual(catalog.catalog_id, catalog_identity(catalog))
        self.assertEqual(canonical_catalog_bytes(catalog), canonical_catalog_bytes(load_catalog(
            canonical_catalog_bytes(catalog)
        )))
        self.assertEqual(catalog.authorization_effect, "none")

    def test_registered_replay_checks_hash_before_reader_and_keeps_outcomes_separate(self) -> None:
        catalog = self._machine_catalog()
        entry = self._machine_entry("mqtt.payload.basic")
        payload = load_registered_fixture_bytes(entry, fixture_root=self.ROOT)
        request = V1GoldenReplayRequest(
            request_id="", route=ReplayRoute.REGISTERED_FIXTURE,
            catalog_id=catalog.catalog_id, fixture_revision_id=entry.fixture_revision_id,
            supplied_decoded_sha256=entry.decoded_sha256, envelope_id=None,
            native_version=None, payload_sha256=entry.decoded_sha256,
        )
        request = replace(request, request_id=replay_request_identity(request))
        result = replay_fixture(catalog, request, payload)
        self.assertEqual(result.legacy_reader_outcome, NativeReaderOutcome.ACCEPTED)
        self.assertEqual(result.fixture_gate_outcome, FixtureGateOutcome.UNVERIFIABLE)
        self.assertEqual(result.authorization_effect, "none")
        tampered = replay_fixture(catalog, request, payload + b"x")
        self.assertEqual(tampered.fixture_gate_outcome, FixtureGateOutcome.REJECTED)
        self.assertEqual(tampered.legacy_reader_outcome, NativeReaderOutcome.NOT_INVOKED)
        self.assertIn("GOLD-HASH-MISMATCH", {item.rule_id for item in tampered.violations})

    def test_unknown_version_and_out_of_band_v1_never_route_versionless_bytes(self) -> None:
        catalog = self._machine_catalog()
        entry = self._machine_entry("mqtt.payload.basic")
        request = V1GoldenReplayRequest(
            "", ReplayRoute.REGISTERED_FIXTURE, catalog.catalog_id,
            "fixture:unknown:sha256:" + "0" * 64, entry.decoded_sha256,
            None, "v1", entry.decoded_sha256,
        )
        request = replace(request, request_id=replay_request_identity(request))
        result = replay_fixture(catalog, request, b"unregistered-versionless-bytes")
        self.assertEqual(result.legacy_reader_outcome, NativeReaderOutcome.NOT_INVOKED)
        self.assertIn("GOLD-FIXTURE-UNKNOWN", {item.rule_id for item in result.violations})

    def test_explicit_envelope_and_adapter_routes_are_exact(self) -> None:
        catalog = self._machine_catalog()
        entry = self._machine_entry("persistence.object.content")
        self.assertEqual(entry.native_version_status, NativeVersionStatus.EXPLICIT)
        payload = load_registered_fixture_bytes(entry, fixture_root=self.ROOT)
        request = V1GoldenReplayRequest(
            "", ReplayRoute.EXPLICIT_ENVELOPE, catalog.catalog_id, entry.fixture_revision_id,
            entry.decoded_sha256, explicit_envelope_identity(entry), entry.native_version_token,
            entry.decoded_sha256,
        )
        request = replace(request, request_id=replay_request_identity(request))
        self.assertEqual(replay_fixture(catalog, request, payload).legacy_reader_outcome,
                         NativeReaderOutcome.ACCEPTED)
        wrong_version = replace(request, native_version="v1", request_id="")
        wrong_version = replace(wrong_version, request_id=replay_request_identity(wrong_version))
        self.assertIn("GOLD-ENVELOPE-INVALID", {
            item.rule_id for item in replay_fixture(catalog, wrong_version, payload).violations
        })
        forged_envelope = replace(request, envelope_id="sha256:" + "2" * 64, request_id="")
        forged_envelope = replace(
            forged_envelope, request_id=replay_request_identity(forged_envelope)
        )
        self.assertIn("GOLD-ENVELOPE-INVALID", {
            item.rule_id for item in replay_fixture(catalog, forged_envelope, payload).violations
        })
        undeclared_adapter = replace(request, adapter_revision_id="sha256:" + "3" * 64,
                                     request_id="")
        undeclared_adapter = replace(
            undeclared_adapter, request_id=replay_request_identity(undeclared_adapter)
        )
        self.assertIn("GOLD-ADAPTER-INVALID", {
            item.rule_id for item in replay_fixture(catalog, undeclared_adapter, payload).violations
        })

    def test_catalog_validation_fails_closed_without_shrinking_core_inventory(self) -> None:
        result = validate_catalog(self._catalog(self._entry()))
        self.assertEqual(result.fixture_gate_outcome, FixtureGateOutcome.REJECTED)
        self.assertIn("GOLD-REQUIREMENT-MISSING", {item.rule_id for item in result.violations})
        self.assertFalse(any(item.requirement_id.startswith("dashboard.") and item.group == FixtureGroup.CORE
                             for item in GOLDEN_REQUIREMENT_SET.requirements))
        rewritten = replace(
            self._entry(), fixture_id="fixture:latest",
            expected_fixture_gate_outcome=FixtureGateOutcome.ACCEPTED,
            fixture_revision_id="", fixture_revision_sha256="",
        )
        identity = fixture_revision_identity(rewritten)
        rewritten = replace(rewritten, fixture_revision_id=identity,
                            fixture_revision_sha256=identity)
        self.assertTrue({"GOLD-ID-MUTABLE", "GOLD-EXPECTATION-MISMATCH"}.issubset(
            {item.rule_id for item in validate_catalog(self._catalog(rewritten)).violations}
        ))

    def test_replay_rejects_a_self_hashed_incomplete_catalog_before_reader(self) -> None:
        entry = self._entry()
        catalog = self._catalog(entry)
        request = V1GoldenReplayRequest(
            "", ReplayRoute.REGISTERED_FIXTURE, catalog.catalog_id, entry.fixture_revision_id,
            entry.decoded_sha256, None, None, entry.decoded_sha256,
        )
        request = replace(request, request_id=replay_request_identity(request))
        result = replay_fixture(catalog, request, b'{"case":"sentinel"}')
        self.assertEqual(result.legacy_reader_outcome, NativeReaderOutcome.NOT_INVOKED)
        self.assertIn("GOLD-REQUIREMENT-MISSING", {item.rule_id for item in result.violations})

    def test_registered_semantic_comparator_detects_declared_output_drift(self) -> None:
        catalog = self._machine_catalog()
        entry = self._machine_entry("mqtt.payload.basic")
        drifted = replace(
            entry,
            expected_output_sha256="sha256:" + "0" * 64,
            fixture_revision_id="",
            fixture_revision_sha256="",
        )
        drifted_id = fixture_revision_identity(drifted)
        drifted = replace(
            drifted,
            fixture_revision_id=drifted_id,
            fixture_revision_sha256=drifted_id,
        )
        replacement_entries = tuple(
            drifted if item.fixture_id == entry.fixture_id else item
            for item in catalog.entries
        )
        drifted_catalog = replace(catalog, entries=replacement_entries, catalog_id="")
        drifted_catalog = replace(
            drifted_catalog,
            catalog_id=catalog_identity(drifted_catalog),
        )
        payload = load_registered_fixture_bytes(entry, fixture_root=self.ROOT)
        request = V1GoldenReplayRequest(
            "", ReplayRoute.REGISTERED_FIXTURE, drifted_catalog.catalog_id,
            drifted.fixture_revision_id, drifted.decoded_sha256, None, None,
            drifted.decoded_sha256,
        )
        request = replace(request, request_id=replay_request_identity(request))
        result = replay_fixture(drifted_catalog, request, payload)
        self.assertEqual(result.legacy_reader_outcome, NativeReaderOutcome.ACCEPTED)
        self.assertEqual(result.fixture_gate_outcome, FixtureGateOutcome.REJECTED)
        self.assertIn("GOLD-COMPARISON-DRIFT", {item.rule_id for item in result.violations})

    def test_locator_and_base64_carrier_boundaries(self) -> None:
        entry = self._entry()
        catalog = self._catalog(entry)
        for locator in ("../x", "/x", "C:/x", r"\\server\x", r"a\b", "a:b", "./x", "a//b"):
            with self.subTest(locator=locator):
                invalid = replace(entry, filesystem_locator=locator, fixture_revision_id="",
                                  fixture_revision_sha256="")
                invalid_id = fixture_revision_identity(invalid)
                invalid = replace(invalid, fixture_revision_id=invalid_id,
                                  fixture_revision_sha256=invalid_id)
                violations = validate_catalog(self._catalog(invalid)).violations
                self.assertIn("GOLD-LOCATOR-UNSAFE", {item.rule_id for item in violations})
        with tempfile.TemporaryDirectory() as directory:
            root = Path(directory)
            path = root / entry.filesystem_locator
            path.parent.mkdir(parents=True)
            path.write_bytes(base64.b64encode(b'{"case":"sentinel"}') + b"\n")
            self.assertIn("GOLD-CARRIER-NONCANONICAL", {
                item.rule_id for item in validate_catalog(catalog, fixture_root=root).violations
            })
            path.unlink()
            path.mkdir()
            self.assertIn("GOLD-CONTENT-MISSING", {
                item.rule_id for item in validate_catalog(catalog, fixture_root=root).violations
            })
            path.rmdir()
            outside = root / "outside.b64"
            outside.write_bytes(base64.b64encode(b'{"case":"sentinel"}'))
            try:
                path.symlink_to(outside)
            except OSError:
                pass
            else:
                self.assertIn("GOLD-CONTENT-MISSING", {
                    item.rule_id for item in validate_catalog(catalog, fixture_root=root).violations
                })

    def test_object_keys_are_opaque_but_never_filesystem_paths(self) -> None:
        entry = self._entry()
        object_entry = replace(entry, filesystem_locator=None,
                               object_key="bucket/../opaque:key", storage_encoding=StorageEncoding.RAW,
                               fixture_revision_id="", fixture_revision_sha256="")
        identity = fixture_revision_identity(object_entry)
        object_entry = replace(object_entry, fixture_revision_id=identity,
                               fixture_revision_sha256=identity)
        rules = {item.rule_id for item in validate_catalog(self._catalog(object_entry)).violations}
        self.assertNotIn("GOLD-LOCATOR-UNSAFE", rules)
        payload = b'{"case":"sentinel"}'
        object_entry = replace(
            object_entry, decoded_byte_length=len(payload),
            decoded_sha256="sha256:" + hashlib.sha256(payload).hexdigest(),
            fixture_revision_id="", fixture_revision_sha256="",
        )
        identity = fixture_revision_identity(object_entry)
        object_entry = replace(object_entry, fixture_revision_id=identity,
                               fixture_revision_sha256=identity)
        self.assertEqual(load_registered_fixture_bytes(
            object_entry, object_store={object_entry.object_key: payload}
        ), payload)
        with self.assertRaises(ValueError):
            load_registered_fixture_bytes(object_entry, object_store={})
        with self.assertRaises(ValueError):
            load_registered_fixture_bytes(
                object_entry, object_store={object_entry.object_key: payload + b"x"}
            )
        with self.assertRaises(ValueError):
            load_registered_fixture_bytes(
                object_entry,
                object_store={object_entry.object_key: b"x" * (MAX_FIXTURE_BYTES * 2 + 1)},
            )

    def test_semantic_promotion_domain_mock_and_secret_metadata_fail_closed(self) -> None:
        entry = self._entry()
        promoted_semantic = replace(
            entry.semantic_identity, evidence_role=EvidenceRole.OFFICIAL_REAL,
            scientific_status=ScientificStatus.QUALIFIED,
        )
        promoted = replace(entry, semantic_identity=promoted_semantic,
                           fixture_revision_id="", fixture_revision_sha256="")
        identity = fixture_revision_identity(promoted)
        promoted = replace(promoted, fixture_revision_id=identity,
                           fixture_revision_sha256=identity)
        self.assertIn("GOLD-SEMANTIC-PROMOTION", {
            item.rule_id for item in validate_catalog(self._catalog(promoted)).violations
        })
        mock_semantic = replace(
            entry.semantic_identity, synthetic_status=SyntheticStatus.MOCK,
            domain_scope=DomainScope.COMPRESSOR_PROTOTYPE,
        )
        unbound_mock = replace(
            entry, origin=FixtureOrigin.ADMITTED_DOMAIN_MOCK_FIXTURE,
            semantic_identity=mock_semantic, mock_admission_id="mock:missing",
            fixture_revision_id="", fixture_revision_sha256="",
        )
        identity = fixture_revision_identity(unbound_mock)
        unbound_mock = replace(unbound_mock, fixture_revision_id=identity,
                               fixture_revision_sha256=identity)
        self.assertIn("GOLD-MOCK-ADMISSION-INVALID", {
            item.rule_id for item in validate_catalog(self._catalog(unbound_mock)).violations
        })
        secret = replace(entry, limitations=("token=do-not-echo-this",),
                         fixture_revision_id="", fixture_revision_sha256="")
        identity = fixture_revision_identity(secret)
        secret = replace(secret, fixture_revision_id=identity, fixture_revision_sha256=identity)
        violations = validate_catalog(self._catalog(secret)).violations
        self.assertIn("GOLD-SECRET-MATERIAL", {item.rule_id for item in violations})
        self.assertNotIn("do-not-echo-this", json.dumps([item.to_dict() for item in violations]))

    def test_filesystem_resolver_escape_and_adapter_declaration_fail_closed(self) -> None:
        entry = self._entry()
        with tempfile.TemporaryDirectory() as directory:
            root = Path(directory)
            path = root / entry.filesystem_locator
            path.parent.mkdir(parents=True)
            path.write_bytes(base64.b64encode(b'{"case":"sentinel"}'))
            outside = root.parent / "outside-golden.bin"
            outside.write_bytes(path.read_bytes())
            try:
                resolver = lambda candidate: outside if candidate.name == "payload.b64" \
                    else candidate.resolve()
                self.assertIn("GOLD-CONTENT-MISSING", {
                    item.rule_id for item in validate_catalog(
                        self._catalog(entry), fixture_root=root, path_resolver=resolver
                    ).violations
                })
            finally:
                outside.unlink(missing_ok=True)
        adapter = V1GoldenAdapterDeclaration(
            "adapter:test", "sha256:" + "0" * 64, entry.fixture_revision_id,
            "sha256:" + "9" * 64, "input.v1", "output.v2", (),
            "unresolved:code", ("No undeclared transformation.",),
        )
        invalid_catalog = replace(self._catalog(entry), adapters=(adapter,), catalog_id="")
        invalid_catalog = replace(invalid_catalog, catalog_id=catalog_identity(invalid_catalog))
        self.assertTrue({"GOLD-ADAPTER-INVALID", "GOLD-ADAPTER-FIXTURE-UNKNOWN"}.issubset(
            {item.rule_id for item in validate_catalog(invalid_catalog).violations}
        ))

    def test_fixture_use_policy_rejects_scientific_consumers(self) -> None:
        self.assertEqual(validate_fixture_use("contract_fixture_replay"), ())
        for use in ("dataset_root", "sample", "window", "label", "metric", "ranking",
                    "truth", "uncertainty", "training", "calibration", "final_result"):
            self.assertIn("GOLD-USE-PROHIBITED", {
                item.rule_id for item in validate_fixture_use(use)
            })

    def test_loader_rejects_duplicate_keys_nonfinite_and_unknown_fields(self) -> None:
        payload = canonical_catalog_bytes(self._catalog(self._entry())).decode("utf-8")
        with self.assertRaises(ValueError):
            load_catalog(payload.replace('"schema_version":', '"schema_version":"duplicate",\n"schema_version":', 1))
        with self.assertRaises(ValueError):
            load_catalog(payload.replace('"limitations":[', '"unknown":NaN,"limitations":[', 1))

    def test_machine_authority_cli_is_read_only_and_honestly_blocked(self) -> None:
        catalog_path = self._machine_catalog_path()
        self.assertTrue(catalog_path.is_file())
        loaded = load_catalog(catalog_path.read_bytes())
        self.assertEqual(catalog_path.read_bytes(), canonical_catalog_bytes(loaded))
        for entry in loaded.entries:
            if entry.filesystem_locator is not None:
                payload = load_registered_fixture_bytes(entry, fixture_root=self.ROOT)
                self.assertEqual(len(payload), entry.decoded_byte_length)
        persistence = next(item for item in loaded.entries
                           if item.requirement_id == "persistence.object.content")
        self.assertEqual(persistence.native_version_token, "2.0")
        self.assertIn(b'"artifact_version":"2.0"', load_registered_fixture_bytes(
            persistence, fixture_root=self.ROOT
        ))
        command = [sys.executable, "scripts/validate_v1_golden_fixtures.py",
                   "--catalog", str(catalog_path), "--fixture-root", str(self.ROOT)]
        blocked = subprocess.run(command, capture_output=True, text=True, check=False)
        self.assertEqual(blocked.returncode, 1, blocked.stdout + blocked.stderr)
        self.assertIn("authorization_effect=none", blocked.stdout)
        malformed_command = list(command)
        malformed_command[malformed_command.index("--catalog") + 1] = "missing.json"
        malformed = subprocess.run(malformed_command, capture_output=True, text=True, check=False)
        self.assertEqual(malformed.returncode, 2)
        self.assertNotIn("Traceback", malformed.stdout + malformed.stderr)

    def test_every_available_machine_fixture_reproduces_its_declared_native_outcome(self) -> None:
        catalog_path = self._machine_catalog_path()
        catalog = load_catalog(catalog_path.read_bytes())
        for entry in catalog.entries:
            if entry.filesystem_locator is None:
                continue
            with self.subTest(requirement=entry.requirement_id):
                payload = load_registered_fixture_bytes(entry, fixture_root=self.ROOT)
                request = V1GoldenReplayRequest(
                    "", ReplayRoute.REGISTERED_FIXTURE, catalog.catalog_id,
                    entry.fixture_revision_id, entry.decoded_sha256, None, None,
                    entry.decoded_sha256,
                )
                request = replace(request, request_id=replay_request_identity(request))
                result = replay_fixture(catalog, request, payload)
                self.assertEqual(result.legacy_reader_outcome,
                                 entry.expected_legacy_reader_outcome,
                                 [item.to_dict() for item in result.violations])
                self.assertEqual(result.fixture_gate_outcome,
                                 entry.expected_fixture_gate_outcome,
                                 [item.to_dict() for item in result.violations])


if __name__ == "__main__":
    unittest.main()
