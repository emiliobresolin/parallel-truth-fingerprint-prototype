from __future__ import annotations

import hashlib
import json
import subprocess
import sys
import tempfile
import unittest
from dataclasses import replace
from pathlib import Path

from parallel_truth_fingerprint.contracts.source_catalog import (
    SOURCE_CATALOG_SCHEMA_VERSION,
    AccessStatus,
    AuthorityRole,
    Classification,
    ContentRecord,
    CopyRole,
    DateStatus,
    DiscrepancyRecord,
    IssuerRole,
    PeerReviewStatus,
    RedistributionStatus,
    RelationRecord,
    RelationType,
    RetrievalRecord,
    RetrievalStatus,
    RightsStatus,
    SourceCatalog,
    SourceRecord,
    SourceRevision,
    SourceCatalogValidationResult,
    SourceType,
    SourceUse,
    SourceUseStatus,
    VerificationStatus,
)
from parallel_truth_fingerprint.evidence.source_catalog import (
    canonical_catalog_bytes,
    checksum_projection,
    human_index_projection,
    load_source_catalog,
    validate_source_catalog,
)


class SourceCatalogTest(unittest.TestCase):
    DIGEST = "sha256:" + "a" * 64

    def _source(self, **overrides: object) -> SourceRecord:
        values: dict[str, object] = {
            "source_id": "vendor:test-manual",
            "organization_authors": ("Test Manufacturer",),
            "title": "Test Manual",
            "publication_date": "2025-01-01",
            "publication_date_status": DateStatus.KNOWN,
            "exact_version": "Rev A",
            "version_status": DateStatus.KNOWN,
            "source_type": SourceType.VENDOR_MANUAL,
            "classifications": (Classification.PRIMARY, Classification.VENDOR_DOCUMENTATION),
            "issuer_role": IssuerRole.MANUFACTURER,
            "authority_role": AuthorityRole.RESPONSIBLE_OFFICIAL,
            "peer_review_status": PeerReviewStatus.NOT_APPLICABLE,
            "official_url": "https://example.test/manual/rev-a.pdf",
            "applicable_scope": "Test device Rev A facts only.",
            "limitations": ("Synthetic unit-test record.",),
        }
        values.update(overrides)
        return SourceRecord(**values)  # type: ignore[arg-type]

    def _revision(self, **overrides: object) -> SourceRevision:
        values: dict[str, object] = {
            "source_revision_id": "vendor:test-manual:revision:rev-a",
            "source_id": "vendor:test-manual",
            "exact_version": "Rev A",
            "version_status": DateStatus.KNOWN,
            "release_date": "2025-01-01",
            "release_date_status": DateStatus.KNOWN,
            "immutable_locator": "https://example.test/manual/rev-a.pdf",
            "mutable_location": False,
            "limitations": (),
        }
        values.update(overrides)
        return SourceRevision(**values)  # type: ignore[arg-type]

    def _content(self, **overrides: object) -> ContentRecord:
        values: dict[str, object] = {
            "content_id": self.DIGEST,
            "source_revision_id": "vendor:test-manual:revision:rev-a",
            "filename": "manual.pdf",
            "byte_size": 3,
            "sha256": self.DIGEST,
            "media_type": "application/pdf",
        }
        values.update(overrides)
        return ContentRecord(**values)  # type: ignore[arg-type]

    def _retrieval(self, **overrides: object) -> RetrievalRecord:
        values: dict[str, object] = {
            "retrieval_id": "vendor:test-manual:retrieval:local",
            "source_revision_id": "vendor:test-manual:revision:rev-a",
            "content_id": self.DIGEST,
            "copy_role": CopyRole.LOCAL_VERIFICATION_COPY,
            "retrieval_status": RetrievalStatus.LOCAL,
            "verification_status": VerificationStatus.VERIFIED,
            "access_status": AccessStatus.PUBLIC,
            "rights_status": RightsStatus.UNKNOWN,
            "redistribution_status": RedistributionStatus.UNKNOWN,
            "retrieval_date": "2026-08-22",
            "retrieval_date_status": DateStatus.KNOWN,
            "local_locator": "manual.pdf",
            "remote_locator": "https://example.test/manual/rev-a.pdf",
            "license_terms_locator": None,
            "citation_notice": "Cite manufacturer and revision.",
            "permitted_project_use": "Academic verification.",
            "storage_policy": "Local verification archive outside Git.",
            "verifier": "unit-test",
            "limitations": ("Redistribution rights unresolved.",),
        }
        values.update(overrides)
        return RetrievalRecord(**values)  # type: ignore[arg-type]

    def _use(self, **overrides: object) -> SourceUse:
        values: dict[str, object] = {
            "use_id": "use:test-manual:scaling",
            "source_id": "vendor:test-manual",
            "source_revision_id": "vendor:test-manual:revision:rev-a",
            "claim_use": "direct_value",
            "locator_kind": "document",
            "exact_locator": "printed p. 4, Table 2, parameter X",
            "supported_scope": "Test device Rev A parameter X.",
            "excluded_scope": ("Other devices", "Universal endpoint"),
            "applicable_variant": "Test device Rev A",
            "prototype_component": "test profile",
            "research_question": "Can the documented fact configure the test profile?",
            "evidence_track": "synthetic test",
            "final_package_element": "test matrix",
            "transferability_rationale": "Exact device, revision, and field match.",
            "status": SourceUseStatus.LOCATED,
            "responsible_authority": True,
            "limitations": (),
        }
        values.update(overrides)
        return SourceUse(**values)  # type: ignore[arg-type]

    def _catalog(self, **overrides: object) -> SourceCatalog:
        values: dict[str, object] = {
            "schema_version": SOURCE_CATALOG_SCHEMA_VERSION,
            "semantic_vocabulary_version": "semantic-vocabulary.v1",
            "sources": (self._source(),),
            "revisions": (self._revision(),),
            "contents": (self._content(),),
            "retrievals": (self._retrieval(),),
            "uses": (self._use(),),
            "relations": (),
            "discrepancies": (),
        }
        values.update(overrides)
        return SourceCatalog(**values)  # type: ignore[arg-type]

    def _rules(self, catalog: SourceCatalog, root: Path | None = None) -> set[str]:
        return {item.rule_id for item in validate_source_catalog(catalog, documents_root=root).violations}

    def test_flat_contract_is_deterministic_and_has_no_authorization(self) -> None:
        catalog = self._catalog()
        self.assertEqual(catalog.authorization_effect, "none")
        self.assertEqual(catalog.sources[0].classifications,
                         (Classification.PRIMARY, Classification.VENDOR_DOCUMENTATION))
        self.assertEqual(catalog.to_dict(), json.loads(json.dumps(catalog.to_dict())))
        self.assertEqual(canonical_catalog_bytes(catalog), canonical_catalog_bytes(catalog))
        self.assertTrue(canonical_catalog_bytes(catalog).endswith(b"\n"))

    def test_duplicate_and_unresolved_identities_fail_closed(self) -> None:
        duplicate = self._catalog(sources=(self._source(), self._source()))
        unresolved = self._catalog(uses=(replace(self._use(), source_revision_id="missing"),))
        self.assertIn("SRC-ID-DUPLICATE", self._rules(duplicate))
        self.assertIn("SRC-REFERENCE-UNRESOLVED", self._rules(unresolved))

    def test_closed_vocabulary_and_typed_locator_fail_closed(self) -> None:
        bad_token = self._catalog(sources=(replace(self._source(), source_type="web_page"),))
        bad_locator = self._catalog(uses=(replace(self._use(), locator_kind="document_or_record"),))
        self.assertIn("SRC-TOKEN-INVALID", self._rules(bad_token))
        self.assertIn("SRC-USE-INAPPLICABLE", self._rules(bad_locator))

    def test_date_values_cannot_contradict_their_status(self) -> None:
        source = replace(self._source(), publication_date="2025-01-01",
                         publication_date_status=DateStatus.NOT_STATED)
        retrieval = replace(self._retrieval(), retrieval_date="yesterday",
                            retrieval_date_status=DateStatus.KNOWN)
        self.assertIn("SRC-METADATA-INCOMPLETE", self._rules(self._catalog(sources=(source,))))
        self.assertIn("SRC-METADATA-INCOMPLETE", self._rules(self._catalog(retrievals=(retrieval,))))

    def test_existing_stable_identity_cannot_be_mutated(self) -> None:
        prior = self._catalog()
        current = replace(prior, revisions=(replace(self._revision(), exact_version="Rev B"),))
        result = validate_source_catalog(current, prior_catalog=prior)
        self.assertIn("SRC-IMMUTABLE-IDENTITY-MUTATED",
                      {item.rule_id for item in result.violations})

    def test_identity_graph_cannot_splice_unrelated_records(self) -> None:
        other_source = replace(self._source(), source_id="vendor:other")
        other_revision = replace(self._revision(), source_revision_id="vendor:other:revision:a",
                                 source_id="vendor:other")
        catalog = self._catalog(
            sources=(self._source(), other_source),
            revisions=(self._revision(), other_revision),
            retrievals=(replace(self._retrieval(), source_revision_id=other_revision.source_revision_id),),
            uses=(replace(self._use(), source_id=other_source.source_id),),
        )
        violations = validate_source_catalog(catalog).violations
        graph_records = {item.record_id for item in violations
                         if item.rule_id == "SRC-REFERENCE-UNRESOLVED"}
        self.assertIn(self._retrieval().retrieval_id, graph_records)
        self.assertIn(self._use().use_id, graph_records)

    def test_prior_catalog_is_append_only_for_every_record_family(self) -> None:
        relation = RelationRecord("relation:test", RelationType.ALIAS_OF,
                                  self._source().source_id, self._revision().source_revision_id)
        discrepancy = DiscrepancyRecord("discrepancy:test", "metadata",
                                        self._source().source_id, self._revision().source_revision_id,
                                        "open", "Explicit test discrepancy.")
        prior = replace(self._catalog(), relations=(relation,), discrepancies=(discrepancy,))
        current = replace(prior, uses=(), relations=(), discrepancies=())
        violations = validate_source_catalog(current, prior_catalog=prior).violations
        mutated = {item.record_id for item in violations
                   if item.rule_id == "SRC-IMMUTABLE-IDENTITY-MUTATED"}
        self.assertTrue({self._use().use_id, relation.relation_id,
                         discrepancy.discrepancy_id}.issubset(mutated))

    def test_cli_can_compare_an_explicit_prior_catalog(self) -> None:
        prior = self._catalog()
        current = replace(prior, uses=())
        with tempfile.TemporaryDirectory() as directory:
            prior_path = Path(directory, "prior.json")
            current_path = Path(directory, "current.json")
            prior_path.write_bytes(canonical_catalog_bytes(prior))
            current_path.write_bytes(canonical_catalog_bytes(current))
            result = subprocess.run([
                sys.executable, "scripts/validate_source_catalog.py",
                "--catalog", str(current_path), "--prior-catalog", str(prior_path),
            ], check=False, capture_output=True, text=True)
        self.assertEqual(result.returncode, 1)
        self.assertIn("SRC-IMMUTABLE-IDENTITY-MUTATED", result.stderr)

    def test_logical_baseline_version_must_match_one_revision(self) -> None:
        source = replace(self._source(), exact_version="Rev Z")
        self.assertIn("SRC-METADATA-INCOMPLETE", self._rules(self._catalog(sources=(source,))))

    def test_digest_and_local_metadata_are_strict(self) -> None:
        invalid = self._catalog(contents=(replace(self._content(), sha256="SHA256:ABC"),))
        fabricated = self._catalog(retrievals=(replace(
            self._retrieval(), retrieval_status=RetrievalStatus.LINK_ONLY,
        ),))
        self.assertIn("SRC-DIGEST-INVALID", self._rules(invalid))
        self.assertIn("SRC-LOCAL-METADATA-FABRICATED", self._rules(fabricated))

    def test_local_bytes_are_verified_as_opaque_streams(self) -> None:
        with tempfile.TemporaryDirectory() as directory:
            root = Path(directory)
            payload = b"abc"
            (root / "manual.pdf").write_bytes(payload)
            digest = "sha256:" + hashlib.sha256(payload).hexdigest()
            catalog = self._catalog(
                contents=(replace(self._content(), content_id=digest, sha256=digest),),
                retrievals=(replace(self._retrieval(), content_id=digest),),
            )
            self.assertTrue(validate_source_catalog(catalog, documents_root=root).valid)
            (root / "manual.pdf").write_bytes(b"changed")
            self.assertIn("SRC-LOCAL-BYTES-MISMATCH", self._rules(catalog, root))

    def test_unsafe_paths_and_mutable_revisions_fail(self) -> None:
        unsafe = self._catalog(retrievals=(replace(self._retrieval(), local_locator="../escape.pdf"),))
        mutable = self._catalog(
            revisions=(replace(self._revision(), immutable_locator="https://github.com/org/repo/tree/main",
                               mutable_location=False),),
            contents=(), retrievals=(), uses=(),
        )
        self.assertIn("SRC-LOCATOR-UNSAFE", self._rules(unsafe))
        self.assertIn("SRC-LOCATOR-MUTABLE", self._rules(mutable))

    def test_mutable_query_and_malformed_remote_locator_fail(self) -> None:
        mutable = self._catalog(revisions=(replace(
            self._revision(), immutable_locator="https://example.test/archive?ref=refs/heads/main"
        ),), contents=(), retrievals=(), uses=())
        malformed = self._catalog(retrievals=(replace(
            self._retrieval(), remote_locator="official landing page"
        ),))
        false_unavailable = self._catalog(retrievals=(replace(
            self._retrieval(), content_id=None, local_locator=None,
            retrieval_status=RetrievalStatus.LINK_ONLY,
            remote_locator="unavailable:not-a-link",
        ),), contents=(), uses=())
        self.assertIn("SRC-LOCATOR-MUTABLE", self._rules(mutable))
        self.assertIn("SRC-LOCATOR-UNSAFE", self._rules(malformed))
        self.assertIn("SRC-LOCATOR-UNSAFE", self._rules(false_unavailable))

    def test_injected_resolver_always_exercises_escape_boundary(self) -> None:
        with tempfile.TemporaryDirectory() as directory:
            root = Path(directory).resolve()
            outside = root.parent / "forced-escape"

            def resolver(path: Path) -> Path:
                return root if path == Path(directory) else outside / path.name

            result = validate_source_catalog(self._catalog(), documents_root=Path(directory),
                                             path_resolver=resolver)
            self.assertIn("SRC-LOCATOR-UNSAFE", {item.rule_id for item in result.violations})

    def test_unknown_legacy_is_valid_metadata_but_not_direct_authority(self) -> None:
        source = replace(self._source(), exact_version=None, version_status=DateStatus.UNKNOWN_LEGACY)
        revision = replace(self._revision(), exact_version=None, version_status=DateStatus.UNKNOWN_LEGACY,
                           mutable_location=True, limitations=("Historical version was not recorded.",))
        catalog = self._catalog(sources=(source,), revisions=(revision,))
        self.assertIn("SRC-DIRECT-AUTHORITY-INELIGIBLE", self._rules(catalog))

    def test_contextual_sources_cannot_be_promoted_to_direct_authority(self) -> None:
        source = replace(self._source(), authority_role=AuthorityRole.CONTEXTUAL_ONLY,
                         source_type=SourceType.SCHOLARLY_PAPER,
                         issuer_role=IssuerRole.ORIGINAL_AUTHORS)
        self.assertIn("SRC-CONTEXT-PROMOTED", self._rules(self._catalog(sources=(source,))))

    def test_scholarly_direct_value_and_unobserved_formal_use_fail(self) -> None:
        scholarly = replace(self._source(), source_type=SourceType.SCHOLARLY_PAPER,
                            issuer_role=IssuerRole.ORIGINAL_AUTHORS,
                            authority_role=AuthorityRole.AUTHORITATIVE_FOR_SCOPE)
        promoted = self._catalog(sources=(scholarly,))
        unobserved = self._catalog(contents=(), retrievals=(), revisions=(replace(
            self._revision(), immutable_locator=None
        ),))
        self.assertIn("SRC-CONTEXT-PROMOTED", self._rules(promoted))
        self.assertIn("SRC-DIRECT-AUTHORITY-INELIGIBLE", self._rules(unobserved))

    def test_restricted_source_requires_lawful_observation_metadata(self) -> None:
        restricted = replace(
            self._retrieval(), content_id=None, local_locator=None,
            retrieval_status=RetrievalStatus.RESTRICTED, access_status=AccessStatus.RESTRICTED,
            verification_status=VerificationStatus.NOT_APPLICABLE, verifier=None,
            retrieval_date=None, retrieval_date_status=DateStatus.NOT_APPLICABLE, limitations=(),
        )
        self.assertIn("SRC-METADATA-INCOMPLETE",
                      self._rules(self._catalog(contents=(), retrievals=(restricted,), uses=())))

    def test_exact_locator_structure_is_medium_specific(self) -> None:
        self.assertIn("SRC-USE-INAPPLICABLE",
                      self._rules(self._catalog(uses=(replace(self._use(), exact_locator="x"),))))

    def test_rights_unknown_blocks_redistribution_claim(self) -> None:
        retrieval = replace(self._retrieval(), redistribution_status=RedistributionStatus.ALLOWED)
        self.assertIn("SRC-RIGHTS-UNRESOLVED", self._rules(self._catalog(retrievals=(retrieval,))))

    def test_declared_redistribution_requires_terms_locator(self) -> None:
        retrieval = replace(self._retrieval(), rights_status=RightsStatus.DECLARED,
                            redistribution_status=RedistributionStatus.ALLOWED,
                            license_terms_locator=None)
        self.assertIn("SRC-RIGHTS-UNRESOLVED", self._rules(self._catalog(retrievals=(retrieval,))))

    def test_relations_and_discrepancies_preserve_conflicts(self) -> None:
        second_source = replace(self._source(), source_id="mirror:test-manual")
        second_revision = replace(self._revision(), source_revision_id="mirror:test-manual:revision:rev-a",
                                  source_id="mirror:test-manual")
        second_content = replace(self._content(), content_id="sha256:" + "b" * 64,
                                 source_revision_id=second_revision.source_revision_id,
                                 sha256="sha256:" + "b" * 64, filename="mirror.pdf")
        relation = RelationRecord("relation:conflict", RelationType.CONFLICTS_WITH,
                                  self._revision().source_revision_id, second_revision.source_revision_id)
        discrepancy = DiscrepancyRecord("discrepancy:test", "hash", self._revision().source_revision_id,
                                        second_revision.source_revision_id, "open", "Hashes differ; unresolved.")
        catalog = self._catalog(
            sources=(self._source(), second_source), revisions=(self._revision(), second_revision),
            contents=(self._content(), second_content), retrievals=(), uses=(),
            relations=(relation,), discrepancies=(discrepancy,),
        )
        self.assertTrue(validate_source_catalog(catalog).valid)
        no_discrepancy = replace(catalog, discrepancies=())
        self.assertIn("SRC-MIRROR-CONFLICT-UNRECORDED", self._rules(no_discrepancy))

    def test_byte_identical_relation_requires_equal_hash(self) -> None:
        relation = RelationRecord("relation:bytes", RelationType.BYTE_IDENTICAL,
                                  "sha256:" + "a" * 64, "sha256:" + "b" * 64)
        catalog = replace(self._catalog(), relations=(relation,))
        self.assertIn("SRC-RELATION-INVALID", self._rules(catalog))

    def test_byte_identical_retrievals_are_representable(self) -> None:
        second = replace(self._retrieval(), retrieval_id="vendor:test-manual:retrieval:mirror",
                         copy_role=CopyRole.MIRROR_COPY)
        relation = RelationRecord("relation:bytes", RelationType.BYTE_IDENTICAL,
                                  self._retrieval().retrieval_id, second.retrieval_id)
        catalog = self._catalog(retrievals=(self._retrieval(), second), relations=(relation,))
        self.assertTrue(validate_source_catalog(catalog).valid)

    def test_mirror_hash_conflict_requires_valid_discrepancy(self) -> None:
        other_source = replace(self._source(), source_id="mirror:test-manual")
        other_revision = replace(self._revision(), source_revision_id="mirror:test:revision:a",
                                 source_id=other_source.source_id)
        other_digest = "sha256:" + "b" * 64
        other_content = replace(self._content(), content_id=other_digest, sha256=other_digest,
                                source_revision_id=other_revision.source_revision_id,
                                filename="mirror.pdf")
        relation = RelationRecord("relation:mirror", RelationType.MIRROR_OF,
                                  other_source.source_id, self._source().source_id)
        base = self._catalog(sources=(self._source(), other_source),
                             revisions=(self._revision(), other_revision),
                             contents=(self._content(), other_content), retrievals=(), uses=(),
                             relations=(relation,))
        self.assertIn("SRC-MIRROR-CONFLICT-UNRECORDED", self._rules(base))
        malformed = replace(base, discrepancies=(DiscrepancyRecord(
            "discrepancy:bad", "", other_source.source_id, "missing", "", ""
        ),))
        self.assertIn("SRC-RELATION-INVALID", self._rules(malformed))

    def test_parser_and_projections_are_deterministic(self) -> None:
        catalog = self._catalog()
        loaded = load_source_catalog(canonical_catalog_bytes(catalog))
        self.assertEqual(loaded, catalog)
        self.assertEqual(human_index_projection(catalog), human_index_projection(loaded))
        self.assertEqual(checksum_projection(catalog), checksum_projection(loaded))
        malformed = json.loads(canonical_catalog_bytes(catalog))
        malformed["guessed_authority"] = True
        with self.assertRaises(ValueError):
            load_source_catalog(json.dumps(malformed))

    def test_loader_rejects_malformed_nested_shapes_and_nonfinite_numbers(self) -> None:
        raw = json.loads(canonical_catalog_bytes(self._catalog()))
        raw["sources"][0]["organization_authors"] = "Manufacturer"
        with self.assertRaises(ValueError):
            load_source_catalog(json.dumps(raw))
        with self.assertRaises(ValueError):
            load_source_catalog('{"authorization_effect":"none","value":NaN}')
        with self.assertRaises(TypeError):
            SourceCatalogValidationResult(True, True, (), authorization_effect="authorize")

    def test_cli_reports_parse_errors_without_traceback(self) -> None:
        with tempfile.TemporaryDirectory() as directory:
            path = Path(directory, "bad.json")
            path.write_text('{"authorization_effect":"none"}', encoding="utf-8")
            result = subprocess.run(
                [sys.executable, "scripts/validate_source_catalog.py", "--catalog", str(path)],
                check=False, capture_output=True, text=True,
            )
        self.assertNotEqual(result.returncode, 0)
        self.assertIn("SRC-CATALOG-PARSE-ERROR", result.stderr)
        self.assertNotIn("Traceback", result.stderr)

    def test_all_retrieval_and_access_states_are_closed_tokens(self) -> None:
        self.assertEqual({item.value for item in RetrievalStatus},
                         {"local", "link_only", "restricted", "pending", "unavailable"})
        self.assertEqual({item.value for item in AccessStatus},
                         {"public", "restricted", "paywalled", "pending", "unavailable", "unknown"})
        self.assertEqual({item.value for item in RightsStatus},
                         {"declared", "unknown", "not_stated", "not_applicable"})

    def test_float_identity_data_is_rejected(self) -> None:
        catalog = self._catalog(sources=(replace(self._source(), applicable_scope=1.5),))
        with self.assertRaises(ValueError):
            canonical_catalog_bytes(catalog)

    def test_impossible_dates_and_unsafe_content_names_fail(self) -> None:
        impossible = self._catalog(sources=(replace(
            self._source(), publication_date="2025-02-31"
        ),))
        unsafe = self._catalog(contents=(replace(
            self._content(), filename="../manual.pdf", media_type=""
        ),))
        self.assertIn("SRC-METADATA-INCOMPLETE", self._rules(impossible))
        self.assertIn("SRC-LOCATOR-UNSAFE", self._rules(unsafe))

    def test_missing_dates_and_duplicate_projection_names_fail(self) -> None:
        revision = replace(self._revision(), release_date=None,
                           release_date_status=DateStatus.NOT_STATED, limitations=())
        other_digest = "sha256:" + "b" * 64
        duplicate_name = replace(self._content(), content_id=other_digest, sha256=other_digest)
        self.assertIn("SRC-METADATA-INCOMPLETE",
                      self._rules(self._catalog(revisions=(revision,))))
        self.assertIn("SRC-RELATION-INVALID",
                      self._rules(self._catalog(contents=(self._content(), duplicate_name))))

    def test_human_projection_preserves_every_revision_and_retrieval(self) -> None:
        second_revision = replace(self._revision(), source_revision_id="vendor:test-manual:revision:rev-a-copy")
        second_retrieval = replace(self._retrieval(), retrieval_id="vendor:test-manual:retrieval:mirror",
                                   source_revision_id=second_revision.source_revision_id,
                                   copy_role=CopyRole.MIRROR_COPY)
        catalog = self._catalog(revisions=(self._revision(), second_revision),
                                retrievals=(self._retrieval(), second_retrieval))
        projection = human_index_projection(catalog)
        self.assertIn(self._revision().source_revision_id, projection)
        self.assertIn(second_revision.source_revision_id, projection)
        self.assertEqual(projection.count("`vendor:test-manual`"), 2)

    def test_real_machine_catalog_migrates_legacy_inventory(self) -> None:
        path = Path("docs/reference-archive/catalog/source-catalog.v1.json")
        catalog = load_source_catalog(path.read_bytes())
        historical = [source for source in catalog.sources if "historical_64" in source.migration_tags]
        self.assertEqual(len(historical), 64)
        self.assertTrue({
            "tool-python-314-hashlib", "tool-python-314-json",
            "tool-python-314-dataclasses", "std-spdx-301-licensing-profile",
        }.issubset({source.source_id for source in catalog.sources}))
        self.assertEqual(len(catalog.contents), 34)
        self.assertEqual(len({content.sha256 for content in catalog.contents}), 34)
        historical_retrievals = [item for item in catalog.retrievals
                                 if item.source_revision_id.split(":revision:")[0]
                                 in {source.source_id for source in historical}]
        counts = {status.value: 0 for status in RetrievalStatus}
        for retrieval in historical_retrievals:
            counts[str(retrieval.retrieval_status)] += 1
        self.assertEqual(counts["local"], 34)
        self.assertEqual(counts["link_only"], 23)
        self.assertEqual(counts["restricted"], 6)
        self.assertEqual(counts["pending"], 1)
        self.assertTrue(any(item.retrieval_date is None and
                            item.retrieval_date_status == DateStatus.UNKNOWN_LEGACY
                            for item in historical_retrievals if item.retrieval_status == RetrievalStatus.LOCAL))
        self.assertEqual(path.read_bytes(), canonical_catalog_bytes(catalog))
        self.assertEqual(Path("docs/reference-archive/catalog/index.md").read_text(encoding="utf-8"),
                         human_index_projection(catalog))
        self.assertEqual(Path("docs/reference-archive/catalog/checksums.sha256").read_text(encoding="utf-8"),
                         checksum_projection(catalog))

    def test_migrated_authority_boundaries_remain_honest(self) -> None:
        catalog = load_source_catalog(Path(
            "docs/reference-archive/catalog/source-catalog.v1.json"
        ).read_bytes())
        sources = {source.source_id: source for source in catalog.sources}
        self.assertEqual(sources["vendor-doe-compressed-air-sourcebook"].authority_role,
                         AuthorityRole.CONTEXTUAL_ONLY)
        p200 = [use for use in catalog.uses if use.source_id == "vendor-siemens-sitrans-p200-2025"
                and use.exact_locator]
        self.assertTrue(p200)
        self.assertTrue(all(use.status == SourceUseStatus.UNRESOLVED for use in p200))
        rpm_endpoints = [use for use in catalog.uses if use.source_id == "vendor-electrosensors-fb420-manual"
                         and use.exact_locator]
        self.assertTrue(rpm_endpoints)
        self.assertTrue(all(use.status == SourceUseStatus.UNRESOLVED and not use.responsible_authority
                            for use in rpm_endpoints))
        decisions = [use for use in catalog.uses if use.source_id == "vendor-danfoss-cds803-programming-2021"
                     and use.exact_locator and ("DecisionRecord" in use.exact_locator
                                                or "reference_window" in use.exact_locator)]
        self.assertTrue(decisions)
        self.assertTrue(all(not use.responsible_authority for use in decisions))

    def test_every_adjacent_source_reference_has_a_bounded_use(self) -> None:
        catalog = load_source_catalog(Path(
            "docs/reference-archive/catalog/source-catalog.v1.json"
        ).read_bytes())
        exact_pairs = {(use.source_id, use.exact_locator) for use in catalog.uses if use.exact_locator}
        import csv
        with Path("docs/reference-archive/catalog/parameter-evidence.csv").open(
            encoding="utf-8", newline=""
        ) as stream:
            for row in csv.DictReader(stream):
                for source_id in row["source_ids"].split("|"):
                    self.assertIn((source_id, row["exact_locator"]), exact_pairs)
        for filename in ("decision-custom-reference-window-v1.yaml",
                         "mock-admission-ptfp-signal-emulator-v1.yaml"):
            lines = Path("docs/reference-archive/catalog", filename).read_text(encoding="utf-8").splitlines()
            for index, line in enumerate(lines):
                if "source_id:" not in line:
                    continue
                source_id = line.split("source_id:", 1)[1].strip()
                locator = next((candidate.split("locator:", 1)[1].strip()
                                for candidate in lines[index + 1:index + 5] if "locator:" in candidate), None)
                if locator:
                    self.assertIn((source_id, locator), exact_pairs)

    def test_read_only_command_checks_metadata_without_ignored_archive(self) -> None:
        command = [sys.executable, "scripts/validate_source_catalog.py", "--check"]
        metadata = subprocess.run(command, check=False, capture_output=True, text=True)
        self.assertEqual(metadata.returncode, 0, metadata.stderr)
        self.assertIn("authorization_effect=none", metadata.stdout)


if __name__ == "__main__":
    unittest.main()
