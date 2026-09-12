from __future__ import annotations

import hashlib
import inspect
import json
import unittest
from dataclasses import replace
from pathlib import Path

from parallel_truth_fingerprint.contracts.semantic_vocabulary import (
    SEMANTIC_VOCABULARY_VERSION,
    DatasetFamily,
    DetectionModality,
    DomainScope,
    EntityKind,
    EvidenceOrigin,
    EvidenceRole,
    LegacySemanticMapping,
    MockInfluence,
    ModelFamily,
    RepresentationKind,
    ResultRole,
    ScientificStatus,
    SemanticIdentity,
    SemanticVocabularyDefinition,
    SyntheticStatus,
    UnsupportedSemanticIdentity,
)
from parallel_truth_fingerprint.contracts.v1_baseline import (
    BaselineEntry,
    RepositoryIdentity,
    V1BaselineManifest,
)
from parallel_truth_fingerprint.evidence.semantic_validation import (
    MOCK_ADMISSION_PTFP_SIGNAL_EMULATOR_V1,
    STABLE_RULE_IDS,
    parse_semantic_identity,
    legacy_assignment_for_label,
    legacy_sensor_assignment,
    validate_legacy_mapping,
    validate_semantic_identity,
)


class SemanticVocabularyTest(unittest.TestCase):
    PARAMETER_AUTHORITY = "parameter-evidence:test:sha256:" + "1" * 64

    def _identity(self, **overrides: object) -> SemanticIdentity:
        values: dict[str, object] = {
            "vocabulary_version": SEMANTIC_VOCABULARY_VERSION,
            "identity_id": "semantic:test",
            "entity_kind": EntityKind.ARTIFACT,
            "modalities": (),
            "representations": (),
            "model_families": (),
            "evidence_role": EvidenceRole.RUNTIME_EVIDENCE,
            "result_role": ResultRole.NONE,
            "scientific_status": ScientificStatus.UNQUALIFIED,
            "synthetic_status": SyntheticStatus.NOT_APPLICABLE,
            "evidence_origin": EvidenceOrigin.PROTOTYPE_GENERATED,
            "domain_scope": DomainScope.NOT_APPLICABLE,
            "numeric_authority_references": (),
            "limitations": ("bounded test identity",),
            "formal_evidence": False,
        }
        values.update(overrides)
        return SemanticIdentity(**values)  # type: ignore[arg-type]

    def _rules(self, identity: SemanticIdentity) -> set[str]:
        return {
            violation.rule_id
            for violation in validate_semantic_identity(identity).violations
        }

    def _baseline(self) -> V1BaselineManifest:
        return V1BaselineManifest(
            schema_version="v1-evidence-baseline.v1",
            baseline_id="sha256:" + "a" * 64,
            observed_at="2026-09-01T00:00:00Z",
            repository=RepositoryIdentity(
                head="a" * 40,
                branch="test",
                status_sha256="sha256:" + "b" * 64,
                status_verification="verified",
                ignored_status_sha256="sha256:" + "c" * 64,
                ignored_status_verification="verified",
                dirty_overlays=(),
            ),
            entries=(BaselineEntry(
                entry_id="legacy:one",
                category="recorded_results",
                role="historical_result",
                version=None,
                locator="docs/result.json",
                byte_size=10,
                sha256="sha256:" + "d" * 64,
                verification_status="verified",
                scientific_status="MEASURED_RESULT",
                limitation="Historical result remains unqualified.",
                evidence_origin="measured",
            ),),
            authorization_effect="none",
        )

    def test_vocabulary_definition_exports_every_exact_token(self) -> None:
        expected = {
            "DetectionModality": {"physical_instrumentation", "linux_host_syscall"},
            "RepresentationKind": {
                "raw_current_ma", "normalized_span", "engineering_value",
                "categorical_syscall_event",
            },
            "ModelFamily": {"lstm", "gru", "autoencoder", "baseline"},
            "EvidenceRole": {
                "custom_generated", "official_real", "fixture_test",
                "published_reference", "runtime_evidence", "legacy_v1",
            },
            "ResultRole": {
                "none", "locally_measured", "published_reference",
                "fixture_expected", "legacy_recorded",
            },
            "ScientificStatus": {
                "qualified", "unqualified", "blocked", "unsupported",
                "test_only", "reference_only", "legacy",
            },
            "SyntheticStatus": {"authentic", "mock", "mock_derived", "not_applicable"},
            "EntityKind": {
                "source", "dataset", "run", "artifact", "representation", "model",
                "detector_bundle", "score", "evaluation_result", "fixture", "legacy_mapping",
            },
            "DatasetFamily": {"adfa_ld", "lid_ds_2021", "hai_23_05", "ptfp_custom_v1"},
            "DomainScope": {
                "compressor_prototype", "native_adfa_ld", "native_lid_ds_2021",
                "native_hai_23_05", "ptfp_custom_controlled", "real_plant", "not_applicable",
            },
            "EvidenceOrigin": {
                "official_native", "authentic_capture", "prototype_generated",
                "mock_parameterized", "measured", "test_fixture",
            },
        }
        definition = SemanticVocabularyDefinition.current().to_dict()
        self.assertEqual(definition["version"], "semantic-vocabulary.v1")
        self.assertEqual(
            {axis: set(tokens) for axis, tokens in definition["axes"].items()},
            expected,
        )

    def test_identity_normalizes_multi_value_tags_deterministically(self) -> None:
        identity = self._identity(
            entity_kind=EntityKind.RUN,
            modalities=(DetectionModality.LINUX_HOST_SYSCALL, DetectionModality.PHYSICAL_INSTRUMENTATION,
                        DetectionModality.LINUX_HOST_SYSCALL),
            representations=(RepresentationKind.CATEGORICAL_SYSCALL_EVENT,
                             RepresentationKind.RAW_CURRENT_MA),
            model_families=(ModelFamily.LSTM, ModelFamily.AUTOENCODER, ModelFamily.LSTM),
            evidence_role=EvidenceRole.CUSTOM_GENERATED,
            synthetic_status=SyntheticStatus.MOCK_DERIVED,
            evidence_origin=EvidenceOrigin.MOCK_PARAMETERIZED,
            generation_origin=EvidenceOrigin.PROTOTYPE_GENERATED,
            mock_admission_reference=MOCK_ADMISSION_PTFP_SIGNAL_EMULATOR_V1,
            mock_influences=(MockInfluence("physical.value", self.PARAMETER_AUTHORITY, MOCK_ADMISSION_PTFP_SIGNAL_EMULATOR_V1),),
            authentic_capture_reference="raw-capture:sha256:aligned",
            numeric_authority_references=(self.PARAMETER_AUTHORITY,),
            dataset_family=DatasetFamily.PTFP_CUSTOM_V1,
            dataset_version="PTFP-Custom-v1",
            dataset_native_scope="synchronized run",
            dataset_native_role="aligned observation",
            dataset_subset="train",
            domain_scope=DomainScope.PTFP_CUSTOM_CONTROLLED,
        )
        self.assertEqual(identity.modalities, (
            DetectionModality.LINUX_HOST_SYSCALL,
            DetectionModality.PHYSICAL_INSTRUMENTATION,
        ))
        self.assertEqual(identity.model_families, (ModelFamily.AUTOENCODER, ModelFamily.LSTM))
        self.assertEqual(identity.to_dict(), json.loads(json.dumps(identity.to_dict())))
        self.assertTrue(validate_semantic_identity(identity).valid)

    def test_representation_and_modality_rules(self) -> None:
        cases = (
            (RepresentationKind.RAW_CURRENT_MA, DetectionModality.LINUX_HOST_SYSCALL),
            (RepresentationKind.CATEGORICAL_SYSCALL_EVENT, DetectionModality.PHYSICAL_INSTRUMENTATION),
        )
        for representation, modality in cases:
            with self.subTest(representation=representation):
                identity = self._identity(
                    entity_kind=EntityKind.REPRESENTATION,
                    modalities=(modality,), representations=(representation,),
                )
                self.assertIn("SEM-REPRESENTATION-CROSS-MODALITY", self._rules(identity))

    def test_modality_bearing_entities_require_modality(self) -> None:
        for kind in (EntityKind.DATASET, EntityKind.RUN, EntityKind.SCORE, EntityKind.EVALUATION_RESULT):
            with self.subTest(kind=kind):
                self.assertIn("SEM-MODALITY-REQUIRED", self._rules(self._identity(entity_kind=kind)))

    def test_valid_examples_cover_roles_origins_and_native_scopes(self) -> None:
        valid = (
            self._identity(
                identity_id="adfa:evaluation", entity_kind=EntityKind.EVALUATION_RESULT,
                modalities=(DetectionModality.LINUX_HOST_SYSCALL,),
                representations=(RepresentationKind.CATEGORICAL_SYSCALL_EVENT,),
                evidence_role=EvidenceRole.OFFICIAL_REAL, result_role=ResultRole.LOCALLY_MEASURED,
                synthetic_status=SyntheticStatus.AUTHENTIC, evidence_origin=EvidenceOrigin.OFFICIAL_NATIVE,
                dataset_family=DatasetFamily.ADFA_LD, dataset_version="ADFA-LD",
                dataset_native_scope="Linux syscall traces", dataset_native_role="validation attack traces",
                dataset_subset="validation", domain_scope=DomainScope.NATIVE_ADFA_LD,
                source_qualification_reference="source-evidence:adfa:v1",
                numeric_authority_references=(self.PARAMETER_AUTHORITY,),
            ),
            self._identity(
                identity_id="custom:physical", entity_kind=EntityKind.RUN,
                modalities=(DetectionModality.PHYSICAL_INSTRUMENTATION,),
                representations=(RepresentationKind.RAW_CURRENT_MA,), evidence_role=EvidenceRole.CUSTOM_GENERATED,
                result_role=ResultRole.LOCALLY_MEASURED, synthetic_status=SyntheticStatus.MOCK_DERIVED,
                evidence_origin=EvidenceOrigin.MOCK_PARAMETERIZED,
                generation_origin=EvidenceOrigin.PROTOTYPE_GENERATED,
                mock_admission_reference=MOCK_ADMISSION_PTFP_SIGNAL_EMULATOR_V1,
                mock_influences=(MockInfluence("observations.current_ma", self.PARAMETER_AUTHORITY,
                                              MOCK_ADMISSION_PTFP_SIGNAL_EMULATOR_V1),),
                dataset_family=DatasetFamily.PTFP_CUSTOM_V1, dataset_version="PTFP-Custom-v1",
                dataset_native_scope="controlled synchronized campaign", dataset_native_role="physical observation",
                dataset_subset="held_out", domain_scope=DomainScope.PTFP_CUSTOM_CONTROLLED,
                numeric_authority_references=(self.PARAMETER_AUTHORITY,),
            ),
            self._identity(
                identity_id="custom:syscall", entity_kind=EntityKind.RUN,
                modalities=(DetectionModality.LINUX_HOST_SYSCALL,),
                representations=(RepresentationKind.CATEGORICAL_SYSCALL_EVENT,),
                evidence_role=EvidenceRole.CUSTOM_GENERATED, result_role=ResultRole.LOCALLY_MEASURED,
                synthetic_status=SyntheticStatus.AUTHENTIC, evidence_origin=EvidenceOrigin.AUTHENTIC_CAPTURE,
                authentic_capture_reference="raw-capture:sha256:abc",
                dataset_family=DatasetFamily.PTFP_CUSTOM_V1, dataset_version="PTFP-Custom-v1",
                dataset_native_scope="controlled synchronized campaign", dataset_native_role="host capture",
                dataset_subset="held_out", domain_scope=DomainScope.PTFP_CUSTOM_CONTROLLED,
            ),
            self._identity(
                identity_id="author:metric", entity_kind=EntityKind.EVALUATION_RESULT,
                modalities=(DetectionModality.PHYSICAL_INSTRUMENTATION,),
                evidence_role=EvidenceRole.CUSTOM_GENERATED, result_role=ResultRole.LOCALLY_MEASURED,
                synthetic_status=SyntheticStatus.MOCK_DERIVED,
                evidence_origin=EvidenceOrigin.MOCK_PARAMETERIZED,
                generation_origin=EvidenceOrigin.PROTOTYPE_GENERATED,
                mock_admission_reference=MOCK_ADMISSION_PTFP_SIGNAL_EMULATOR_V1,
                mock_influences=(MockInfluence("metric.value", self.PARAMETER_AUTHORITY,
                                              MOCK_ADMISSION_PTFP_SIGNAL_EMULATOR_V1),),
                dataset_family=DatasetFamily.PTFP_CUSTOM_V1,
                dataset_version="PTFP-Custom-v1",
                dataset_native_scope="controlled synchronized campaign",
                dataset_native_role="locally evaluated metric",
                dataset_subset="held_out",
                domain_scope=DomainScope.PTFP_CUSTOM_CONTROLLED,
                numeric_authority_references=(self.PARAMETER_AUTHORITY,),
            ),
            self._identity(
                identity_id="fixture:expected", entity_kind=EntityKind.FIXTURE,
                evidence_role=EvidenceRole.FIXTURE_TEST, result_role=ResultRole.FIXTURE_EXPECTED,
                scientific_status=ScientificStatus.TEST_ONLY, evidence_origin=EvidenceOrigin.TEST_FIXTURE,
                formal_evidence=False,
            ),
            self._identity(
                identity_id="author:published-reference", entity_kind=EntityKind.ARTIFACT,
                modalities=(DetectionModality.PHYSICAL_INSTRUMENTATION,),
                evidence_role=EvidenceRole.PUBLISHED_REFERENCE,
                result_role=ResultRole.PUBLISHED_REFERENCE,
                scientific_status=ScientificStatus.REFERENCE_ONLY,
                evidence_origin=EvidenceOrigin.OFFICIAL_NATIVE,
                dataset_family=DatasetFamily.HAI_23_05,
                dataset_version="HAI-23.05",
                dataset_native_scope="native physical/SCADA channels",
                dataset_native_role="published evaluation metric",
                dataset_subset="test",
                domain_scope=DomainScope.NATIVE_HAI_23_05,
                source_qualification_reference="source-evidence:hai:v1",
            ),
        )
        for identity in valid:
            with self.subTest(identity=identity.identity_id):
                result = validate_semantic_identity(identity)
                self.assertTrue(result.supported)
                self.assertTrue(result.valid, result.to_dict())

    def test_role_promotion_is_rejected(self) -> None:
        cases = (
            (EvidenceRole.FIXTURE_TEST, EvidenceOrigin.TEST_FIXTURE, "SEM-FIXTURE-AS-MEASURED"),
            (EvidenceRole.PUBLISHED_REFERENCE, EvidenceOrigin.OFFICIAL_NATIVE, "SEM-REFERENCE-AS-MEASURED"),
        )
        for role, origin, rule in cases:
            with self.subTest(role=role):
                identity = self._identity(evidence_role=role, evidence_origin=origin,
                                          result_role=ResultRole.LOCALLY_MEASURED)
                self.assertIn(rule, self._rules(identity))

    def test_qualification_references_are_required_without_promotion(self) -> None:
        official = self._identity(evidence_role=EvidenceRole.OFFICIAL_REAL,
                                  evidence_origin=EvidenceOrigin.OFFICIAL_NATIVE)
        qualified = self._identity(scientific_status=ScientificStatus.QUALIFIED)
        self.assertIn("SEM-OFFICIAL-REAL-WITHOUT-SOURCE-QUALIFICATION", self._rules(official))
        self.assertIn("SEM-QUALIFIED-WITHOUT-GATE-REFERENCE", self._rules(qualified))
        measured_unqualified = self._identity(result_role=ResultRole.LOCALLY_MEASURED,
                                               scientific_status=ScientificStatus.UNQUALIFIED)
        self.assertTrue(validate_semantic_identity(measured_unqualified).valid)

    def test_every_cross_domain_claim_fails_with_specific_rule(self) -> None:
        cases = (
            (self._identity(dataset_family=DatasetFamily.HAI_23_05,
                            modalities=(DetectionModality.PHYSICAL_INSTRUMENTATION,),
                            domain_scope=DomainScope.COMPRESSOR_PROTOTYPE), "SEM-HAI-AS-COMPRESSOR"),
            (self._identity(dataset_family=DatasetFamily.ADFA_LD,
                            modalities=(DetectionModality.PHYSICAL_INSTRUMENTATION,),
                            domain_scope=DomainScope.NATIVE_ADFA_LD), "SEM-ADFA-AS-PHYSICAL"),
            (self._identity(dataset_family=DatasetFamily.LID_DS_2021,
                            modalities=(DetectionModality.PHYSICAL_INSTRUMENTATION,),
                            domain_scope=DomainScope.NATIVE_LID_DS_2021), "SEM-LID-AS-PHYSICAL"),
            (self._identity(dataset_family=DatasetFamily.PTFP_CUSTOM_V1,
                            evidence_role=EvidenceRole.OFFICIAL_REAL,
                            domain_scope=DomainScope.REAL_PLANT), "SEM-CUSTOM-AS-OFFICIAL-OR-REAL-PLANT"),
            (self._identity(entity_kind=EntityKind.DATASET,
                            model_families=(ModelFamily.AUTOENCODER,),
                            modalities=(DetectionModality.PHYSICAL_INSTRUMENTATION,)), "SEM-MODEL-AS-DATASET"),
            (self._identity(entity_kind=EntityKind.DETECTOR_BUNDLE,
                            model_families=(ModelFamily.AUTOENCODER,),
                            modalities=(DetectionModality.PHYSICAL_INSTRUMENTATION,)), "SEM-MODEL-ONLY-AS-DETECTOR"),
            (self._identity(entity_kind=EntityKind.DETECTOR_BUNDLE,
                            dataset_family=DatasetFamily.HAI_23_05,
                            modalities=(DetectionModality.PHYSICAL_INSTRUMENTATION,),
                            domain_scope=DomainScope.COMPRESSOR_PROTOTYPE,
                            detector_bundle_reference="bundle:external"), "SEM-EXTERNAL-MODEL-AS-COMPRESSOR-DETECTOR"),
        )
        for identity, rule in cases:
            with self.subTest(rule=rule):
                self.assertIn(rule, self._rules(identity))

    def test_dataset_native_fields_are_required_and_retained(self) -> None:
        incomplete = self._identity(
            entity_kind=EntityKind.DATASET,
            modalities=(DetectionModality.LINUX_HOST_SYSCALL,),
            dataset_family=DatasetFamily.ADFA_LD,
            domain_scope=DomainScope.NATIVE_ADFA_LD,
        )
        self.assertIn("SEM-DATASET-NATIVE-SCOPE-MISSING", self._rules(incomplete))
        complete = replace(incomplete, dataset_version="ADFA-LD", dataset_native_scope="native traces",
                           dataset_native_role="training normal", dataset_subset="training",
                           limitations=("host provenance limits",))
        payload = complete.to_dict()
        for field in ("dataset_version", "dataset_native_scope", "dataset_native_role",
                      "dataset_subset", "limitations"):
            self.assertTrue(payload[field])

    def test_custom_physical_and_syscall_lineage_fail_closed(self) -> None:
        physical = self._identity(
            entity_kind=EntityKind.RUN, modalities=(DetectionModality.PHYSICAL_INSTRUMENTATION,),
            evidence_role=EvidenceRole.CUSTOM_GENERATED, dataset_family=DatasetFamily.PTFP_CUSTOM_V1,
            dataset_version="PTFP-Custom-v1", dataset_native_scope="controlled",
            dataset_native_role="physical", dataset_subset="test",
            domain_scope=DomainScope.PTFP_CUSTOM_CONTROLLED,
            synthetic_status=SyntheticStatus.AUTHENTIC,
        )
        syscall = replace(
            physical, identity_id="custom:fake-syscall",
            modalities=(DetectionModality.LINUX_HOST_SYSCALL,),
            representations=(RepresentationKind.CATEGORICAL_SYSCALL_EVENT,),
            synthetic_status=SyntheticStatus.MOCK_DERIVED,
            evidence_origin=EvidenceOrigin.PROTOTYPE_GENERATED,
        )
        self.assertIn("SEM-CUSTOM-PHYSICAL-NOT-MOCK-DERIVED", self._rules(physical))
        self.assertIn("SEM-SYSCALL-SYNTHETIC", self._rules(syscall))

    def test_all_evidence_origins_and_amendment_failures(self) -> None:
        self.assertEqual({item.value for item in EvidenceOrigin}, {
            "official_native", "authentic_capture", "prototype_generated",
            "mock_parameterized", "measured", "test_fixture",
        })
        cases = (
            (self._identity(evidence_origin=None), "SEM-ORIGIN-MISSING"),
            (self._identity(evidence_origin="invented"), "SEM-ORIGIN-UNKNOWN"),
            (self._identity(evidence_role=EvidenceRole.OFFICIAL_REAL,
                            evidence_origin=EvidenceOrigin.PROTOTYPE_GENERATED), "SEM-ORIGIN-INCOMPATIBLE"),
            (self._identity(evidence_origin=EvidenceOrigin.OFFICIAL_NATIVE,
                            dataset_family=DatasetFamily.PTFP_CUSTOM_V1), "SEM-OFFICIAL-NATIVE-SCOPE"),
            (self._identity(evidence_origin=EvidenceOrigin.AUTHENTIC_CAPTURE,
                            synthetic_status=SyntheticStatus.AUTHENTIC), "SEM-AUTHENTIC-CAPTURE-PROVENANCE"),
            (self._identity(evidence_origin=EvidenceOrigin.TEST_FIXTURE,
                            evidence_role=EvidenceRole.FIXTURE_TEST, formal_evidence=True), "SEM-TEST-FIXTURE-FORMAL-PATH"),
            (self._identity(evidence_origin=EvidenceOrigin.MOCK_PARAMETERIZED,
                            synthetic_status=SyntheticStatus.MOCK_DERIVED), "SEM-MOCK-GENERATION-ORIGIN"),
        )
        for identity, rule in cases:
            with self.subTest(rule=rule):
                self.assertIn(rule, self._rules(identity))

    def test_mock_influence_requires_exact_parameter_and_admission_per_field(self) -> None:
        incomplete = self._identity(
            evidence_origin=EvidenceOrigin.MOCK_PARAMETERIZED,
            generation_origin=EvidenceOrigin.PROTOTYPE_GENERATED,
            synthetic_status=SyntheticStatus.MOCK_DERIVED,
            mock_admission_reference=MOCK_ADMISSION_PTFP_SIGNAL_EMULATOR_V1,
            mock_influences=(MockInfluence("physical.value", "", MOCK_ADMISSION_PTFP_SIGNAL_EMULATOR_V1),),
        )
        self.assertIn("SEM-MOCK-INFLUENCE-INCOMPLETE", self._rules(incomplete))

    def test_unknown_or_missing_semantics_are_preserved_as_unsupported(self) -> None:
        payloads = (
            {"identity_id": "raw:missing-version", "entity_kind": "artifact"},
            {"vocabulary_version": "semantic-vocabulary.v99", "identity_id": "raw:version",
             "entity_kind": "artifact"},
            {"vocabulary_version": SEMANTIC_VOCABULARY_VERSION, "identity_id": "raw:token",
             "entity_kind": "spaceship"},
        )
        expected = ("SEM-VERSION-MISSING", "SEM-VERSION-UNSUPPORTED", "SEM-TOKEN-UNKNOWN")
        for raw, rule in zip(payloads, expected, strict=True):
            with self.subTest(rule=rule):
                resolved = parse_semantic_identity(raw)
                self.assertIsInstance(resolved, UnsupportedSemanticIdentity)
                self.assertEqual(resolved.to_dict()["raw_payload"], raw)
                self.assertIn(rule, {item["rule_id"] for item in resolved.to_dict()["violations"]})

    def test_supported_parser_constructs_identity_without_defaults(self) -> None:
        raw = self._identity().to_dict()
        resolved = parse_semantic_identity(raw)
        self.assertIsInstance(resolved, SemanticIdentity)
        self.assertEqual(resolved.to_dict(), raw)

    def test_violations_are_stably_sorted_and_structured(self) -> None:
        identity = self._identity(
            vocabulary_version="bad", entity_kind=EntityKind.DATASET,
            evidence_origin=None, result_role=ResultRole.LOCALLY_MEASURED,
            evidence_role=EvidenceRole.FIXTURE_TEST,
        )
        first = validate_semantic_identity(identity)
        second = validate_semantic_identity(identity)
        self.assertEqual(first, second)
        keys = [(v.rule_id, v.fields) for v in first.violations]
        self.assertEqual(keys, sorted(keys))
        self.assertTrue(all(v.fields and v.explanation for v in first.violations))

    def test_legacy_mapping_is_separate_deterministic_and_forced_legacy(self) -> None:
        baseline = self._baseline()
        original = json.dumps(baseline.to_dict(), sort_keys=True, separators=(",", ":")).encode()
        before = hashlib.sha256(original).hexdigest()
        mapping = LegacySemanticMapping(
            mapping_id="legacy-map:one",
            vocabulary_version=SEMANTIC_VOCABULARY_VERSION,
            baseline_id="sha256:" + "a" * 64,
            entry_id="legacy:one",
            original_field="scientific_status",
            original_value="MEASURED_RESULT",
            current_semantic_assignment=(("result_role", "locally_measured"),),
            provenance_references=("baseline-entry:legacy:one",),
            limitations=("Historical measurement is not automatically qualified.",),
        )
        self.assertEqual(mapping.scientific_status, ScientificStatus.LEGACY)
        self.assertTrue(validate_legacy_mapping(mapping, baseline=baseline).valid)
        self.assertEqual(mapping.to_dict(), LegacySemanticMapping(**{
            **mapping.__dict__, "current_semantic_assignment": (("result_role", "locally_measured"),)
        }).to_dict())
        after = json.dumps(baseline.to_dict(), sort_keys=True, separators=(",", ":")).encode()
        self.assertEqual(hashlib.sha256(after).hexdigest(), before)
        unknown = replace(mapping, entry_id="legacy:unknown")
        self.assertIn("SEM-LEGACY-MAPPING-INCOMPLETE",
                      {v.rule_id for v in validate_legacy_mapping(unknown, baseline=self._baseline()).violations})

    def test_legacy_mapping_requires_provenance_limitations_and_known_labels(self) -> None:
        base = LegacySemanticMapping(
            mapping_id="legacy-map:bad", vocabulary_version=SEMANTIC_VOCABULARY_VERSION,
            baseline_id="sha256:" + "b" * 64, entry_id="legacy:one",
            original_field="scientific_status", original_value="UNKNOWN_LEGACY_LABEL",
            current_semantic_assignment=(), provenance_references=(), limitations=(),
        )
        self.assertIn("SEM-LEGACY-MAPPING-INCOMPLETE",
                      {v.rule_id for v in validate_legacy_mapping(base, baseline=self._baseline()).violations})

    def test_every_minimal_legacy_label_and_sensor_context_has_explicit_mapping(self) -> None:
        for label in (
            "IMPLEMENTED_RUNTIME_EVIDENCE", "FIXTURE", "PUBLISHED_REFERENCE",
            "MEASURED_RESULT", "EXPERIMENTAL_FINGERPRINT_BASELINE", "LEGACY_BASELINE",
            "lstm_autoencoder",
        ):
            with self.subTest(label=label):
                self.assertTrue(legacy_assignment_for_label(label))
        sensor = dict(legacy_sensor_assignment(
            "sensor-temperature",
            source_context="v1 simulator/signal emulator",
        ))
        self.assertEqual(sensor["logical_channel"], "sensor-temperature")
        self.assertEqual(sensor["hardware_claim"], "unsupported")
        with self.assertRaises(ValueError):
            legacy_sensor_assignment("sensor-temperature", source_context="")

    def test_documentation_contains_every_token_and_rule_id(self) -> None:
        documentation = Path("docs/semantic-vocabulary-v1.md").read_text(encoding="utf-8")
        definition = SemanticVocabularyDefinition.current().to_dict()
        for tokens in definition["axes"].values():
            for token in tokens:
                self.assertIn(f"`{token}`", documentation)
        for rule_id in STABLE_RULE_IDS:
            self.assertIn(f"`{rule_id}`", documentation)

    def test_validation_has_no_authorization_or_state_effect(self) -> None:
        identity = self._identity()
        before = identity.to_dict()
        result = validate_semantic_identity(identity)
        self.assertEqual(identity.to_dict(), before)
        self.assertEqual(result.authorization_effect, "none")

    def test_review_semantic_axes_and_formal_path_are_explicit(self) -> None:
        parameters = inspect.signature(SemanticIdentity).parameters
        for field_name in (
            "modalities", "representations", "model_families", "evidence_role",
            "result_role", "scientific_status", "synthetic_status", "evidence_origin",
            "domain_scope", "formal_evidence", "numeric_authority_references",
        ):
            with self.subTest(field_name=field_name):
                self.assertIn(field_name, parameters)
                self.assertIs(parameters[field_name].default, inspect.Parameter.empty)

    def test_review_numeric_identities_require_authority_reference(self) -> None:
        self.assertIn("numeric_authority_references", SemanticIdentity.__dataclass_fields__)
        numeric = self._identity(
            entity_kind=EntityKind.EVALUATION_RESULT,
            modalities=(DetectionModality.PHYSICAL_INSTRUMENTATION,),
        )
        self.assertIn("SEM-NUMERIC-AUTHORITY-MISSING", self._rules(numeric))

    def test_review_legacy_mapping_rejects_promotion_short_hash_and_duplicates(self) -> None:
        base = LegacySemanticMapping(
            mapping_id="legacy-map:review", vocabulary_version=SEMANTIC_VOCABULARY_VERSION,
            baseline_id="sha256:" + "a" * 64, entry_id="legacy:one",
            original_field="scientific_status", original_value="MEASURED_RESULT",
            current_semantic_assignment=(("result_role", "locally_measured"),),
            provenance_references=("baseline-entry:legacy:one",),
            limitations=("Historical result remains unqualified.",),
        )
        invalid = (
            replace(base, current_semantic_assignment=(("scientific_status", "qualified"),
                                                       ("domain_scope", "real_plant"))),
            replace(base, baseline_id="sha256:x"),
            replace(base, current_semantic_assignment=(("result_role", "locally_measured"),
                                                       ("result_role", "published_reference"))),
        )
        for mapping in invalid:
            with self.subTest(mapping=mapping):
                self.assertFalse(validate_legacy_mapping(mapping, baseline=self._baseline()).valid)

    def test_review_dual_modality_formal_evidence_requires_authentic_syscall_reference(self) -> None:
        identity = self._identity(
            entity_kind=EntityKind.RUN,
            modalities=(DetectionModality.PHYSICAL_INSTRUMENTATION,
                        DetectionModality.LINUX_HOST_SYSCALL),
            representations=(RepresentationKind.RAW_CURRENT_MA,
                             RepresentationKind.CATEGORICAL_SYSCALL_EVENT),
            evidence_role=EvidenceRole.CUSTOM_GENERATED,
            result_role=ResultRole.LOCALLY_MEASURED,
            synthetic_status=SyntheticStatus.MOCK_DERIVED,
            evidence_origin=EvidenceOrigin.MOCK_PARAMETERIZED,
            generation_origin=EvidenceOrigin.PROTOTYPE_GENERATED,
            mock_admission_reference=MOCK_ADMISSION_PTFP_SIGNAL_EMULATOR_V1,
            mock_influences=(MockInfluence("physical.current_ma", self.PARAMETER_AUTHORITY,
                                          MOCK_ADMISSION_PTFP_SIGNAL_EMULATOR_V1),),
            dataset_family=DatasetFamily.PTFP_CUSTOM_V1,
            dataset_version="PTFP-Custom-v1", dataset_native_scope="aligned campaign",
            dataset_native_role="aligned observation", dataset_subset="held_out",
            domain_scope=DomainScope.PTFP_CUSTOM_CONTROLLED,
            formal_evidence=True,
        )
        self.assertIn("SEM-SYSCALL-SYNTHETIC", self._rules(identity))

    def test_review_nonformal_syscall_fixture_remains_valid_and_non_domain(self) -> None:
        identity = self._identity(
            entity_kind=EntityKind.FIXTURE,
            modalities=(DetectionModality.LINUX_HOST_SYSCALL,),
            representations=(RepresentationKind.CATEGORICAL_SYSCALL_EVENT,),
            evidence_role=EvidenceRole.FIXTURE_TEST,
            result_role=ResultRole.FIXTURE_EXPECTED,
            scientific_status=ScientificStatus.TEST_ONLY,
            synthetic_status=SyntheticStatus.NOT_APPLICABLE,
            evidence_origin=EvidenceOrigin.TEST_FIXTURE,
            dataset_family=DatasetFamily.PTFP_CUSTOM_V1,
            dataset_version="PTFP-Custom-v1-shaped-fixture",
            dataset_native_scope="non-domain parser fixture",
            dataset_native_role="test input", dataset_subset="fixture",
            domain_scope=DomainScope.NOT_APPLICABLE,
            formal_evidence=False,
        )
        self.assertTrue(validate_semantic_identity(identity).valid)

    def test_review_external_datasets_reject_substitution_and_native_mismatch(self) -> None:
        substituted = self._identity(
            entity_kind=EntityKind.DATASET,
            modalities=(DetectionModality.LINUX_HOST_SYSCALL,),
            evidence_role=EvidenceRole.RUNTIME_EVIDENCE,
            evidence_origin=EvidenceOrigin.PROTOTYPE_GENERATED,
            dataset_family=DatasetFamily.ADFA_LD, dataset_version="ADFA-LD",
            dataset_native_scope="native traces", dataset_native_role="training",
            dataset_subset="train", domain_scope=DomainScope.NATIVE_ADFA_LD,
            formal_evidence=False,
        )
        hai_as_syscall = self._identity(
            entity_kind=EntityKind.DATASET,
            modalities=(DetectionModality.LINUX_HOST_SYSCALL,),
            evidence_role=EvidenceRole.OFFICIAL_REAL,
            evidence_origin=EvidenceOrigin.OFFICIAL_NATIVE,
            source_qualification_reference="source-evidence:hai:v1",
            dataset_family=DatasetFamily.HAI_23_05, dataset_version="HAI-23.05",
            dataset_native_scope="native SCADA", dataset_native_role="test",
            dataset_subset="test", domain_scope=DomainScope.NATIVE_HAI_23_05,
            formal_evidence=True,
        )
        official_wrong_role = replace(
            hai_as_syscall,
            modalities=(DetectionModality.PHYSICAL_INSTRUMENTATION,),
            evidence_role=EvidenceRole.RUNTIME_EVIDENCE,
        )
        for identity in (substituted, hai_as_syscall, official_wrong_role):
            with self.subTest(identity=identity.identity_id):
                self.assertFalse(validate_semantic_identity(identity).valid)
        self.assertIn("SEM-DATASET-NATIVE-MISMATCH", self._rules(hai_as_syscall))

    def test_review_parser_returns_unsupported_for_known_but_invalid_semantics(self) -> None:
        invalid = self._identity(
            entity_kind=EntityKind.FIXTURE,
            evidence_role=EvidenceRole.FIXTURE_TEST,
            result_role=ResultRole.LOCALLY_MEASURED,
            scientific_status=ScientificStatus.TEST_ONLY,
            evidence_origin=EvidenceOrigin.TEST_FIXTURE,
        ).to_dict()
        self.assertIsInstance(parse_semantic_identity(invalid), UnsupportedSemanticIdentity)

    def test_review_scientific_serialization_gate_rejects_invalid_identity(self) -> None:
        from parallel_truth_fingerprint.evidence import semantic_validation

        self.assertTrue(hasattr(semantic_validation, "validated_semantic_payload"))
        invalid = self._identity(
            entity_kind=EntityKind.FIXTURE,
            evidence_role=EvidenceRole.FIXTURE_TEST,
            result_role=ResultRole.LOCALLY_MEASURED,
            scientific_status=ScientificStatus.TEST_ONLY,
            evidence_origin=EvidenceOrigin.TEST_FIXTURE,
        )
        with self.assertRaises(ValueError):
            semantic_validation.validated_semantic_payload(invalid)

    def test_review_fixture_and_authentic_capture_lineage_are_strict(self) -> None:
        qualified_domain_fixture = self._identity(
            entity_kind=EntityKind.FIXTURE,
            evidence_role=EvidenceRole.FIXTURE_TEST,
            result_role=ResultRole.FIXTURE_EXPECTED,
            scientific_status=ScientificStatus.QUALIFIED,
            owning_gate_reference="gate:fixture:v1",
            evidence_origin=EvidenceOrigin.TEST_FIXTURE,
            domain_scope=DomainScope.COMPRESSOR_PROTOTYPE,
        )
        authentic_with_mock = self._identity(
            evidence_origin=EvidenceOrigin.AUTHENTIC_CAPTURE,
            synthetic_status=SyntheticStatus.AUTHENTIC,
            authentic_capture_reference="raw-capture:sha256:abc",
            generation_origin=EvidenceOrigin.PROTOTYPE_GENERATED,
            mock_admission_reference=MOCK_ADMISSION_PTFP_SIGNAL_EMULATOR_V1,
            mock_influences=(MockInfluence("value", self.PARAMETER_AUTHORITY,
                                          MOCK_ADMISSION_PTFP_SIGNAL_EMULATOR_V1),),
        )
        for identity in (qualified_domain_fixture, authentic_with_mock):
            with self.subTest(identity=identity.identity_id):
                self.assertIn("SEM-ORIGIN-INCOMPATIBLE", self._rules(identity))

    def test_review_blank_identity_references_and_malformed_parser_types_fail(self) -> None:
        blank_identity = self._identity(identity_id="   ")
        official_with_blank_reference = self._identity(
            entity_kind=EntityKind.DATASET,
            modalities=(DetectionModality.LINUX_HOST_SYSCALL,),
            evidence_role=EvidenceRole.OFFICIAL_REAL,
            evidence_origin=EvidenceOrigin.OFFICIAL_NATIVE,
            source_qualification_reference="   ",
            dataset_family=DatasetFamily.ADFA_LD, dataset_version="ADFA-LD",
            dataset_native_scope="native", dataset_native_role="training",
            dataset_subset="train", domain_scope=DomainScope.NATIVE_ADFA_LD,
            formal_evidence=True,
        )
        self.assertIn("SEM-IDENTITY-MISSING", self._rules(blank_identity))
        self.assertIn("SEM-REFERENCE-INVALID", self._rules(official_with_blank_reference))
        malformed = self._identity().to_dict()
        malformed["provenance_references"] = "reference:one"
        malformed["formal_evidence"] = "false"
        self.assertIsInstance(parse_semantic_identity(malformed), UnsupportedSemanticIdentity)

    def test_review_detector_bundle_requires_model_and_bundle_reference(self) -> None:
        identity = self._identity(
            entity_kind=EntityKind.DETECTOR_BUNDLE,
            modalities=(DetectionModality.PHYSICAL_INSTRUMENTATION,),
            model_families=(),
            detector_bundle_reference=None,
        )
        self.assertIn("SEM-MODEL-ONLY-AS-DETECTOR", self._rules(identity))

    def test_review_origin_promotion_rule_is_exercised(self) -> None:
        identity = self._identity(
            evidence_origin=EvidenceOrigin.PROTOTYPE_GENERATED,
            domain_scope=DomainScope.REAL_PLANT,
        )
        self.assertIn("SEM-ORIGIN-PROMOTION", self._rules(identity))

    def test_review_documentation_tables_contain_exact_code_members(self) -> None:
        documentation = Path("docs/semantic-vocabulary-v1.md").read_text(encoding="utf-8")
        table_lines = documentation.splitlines()
        definition = SemanticVocabularyDefinition.current().to_dict()
        for axis, tokens in definition["axes"].items():
            matching = [line for line in table_lines if line.startswith(f"| {axis} |")]
            self.assertEqual(len(matching), 1, axis)
            rendered = matching[0]
            for token in tokens:
                self.assertIn(f"`{token}`", rendered)
        for rule_id in STABLE_RULE_IDS:
            self.assertEqual(
                sum(line.startswith(f"| `{rule_id}` |") for line in table_lines),
                1,
                rule_id,
            )

    def test_final_review_custom_domain_identity_is_closed(self) -> None:
        base = self._identity(
            entity_kind=EntityKind.RUN,
            modalities=(DetectionModality.PHYSICAL_INSTRUMENTATION,),
            representations=(RepresentationKind.RAW_CURRENT_MA,),
            evidence_role=EvidenceRole.CUSTOM_GENERATED,
            result_role=ResultRole.LOCALLY_MEASURED,
            synthetic_status=SyntheticStatus.MOCK_DERIVED,
            evidence_origin=EvidenceOrigin.MOCK_PARAMETERIZED,
            generation_origin=EvidenceOrigin.PROTOTYPE_GENERATED,
            mock_admission_reference=MOCK_ADMISSION_PTFP_SIGNAL_EMULATOR_V1,
            mock_influences=(MockInfluence("current_ma", self.PARAMETER_AUTHORITY,
                                          MOCK_ADMISSION_PTFP_SIGNAL_EMULATOR_V1),),
            numeric_authority_references=(self.PARAMETER_AUTHORITY,),
            domain_scope=DomainScope.PTFP_CUSTOM_CONTROLLED,
        )
        self.assertFalse(validate_semantic_identity(base).valid)
        foreign_scope = replace(
            base,
            dataset_family=DatasetFamily.PTFP_CUSTOM_V1,
            dataset_version="PTFP-Custom-v1",
            dataset_native_scope="controlled",
            dataset_native_role="physical observation",
            dataset_subset="test",
            domain_scope=DomainScope.NATIVE_ADFA_LD,
        )
        self.assertFalse(validate_semantic_identity(foreign_scope).valid)

    def test_final_review_governed_dataset_metadata_is_strict(self) -> None:
        base = self._identity(
            entity_kind=EntityKind.DATASET,
            modalities=(DetectionModality.LINUX_HOST_SYSCALL,),
            evidence_role=EvidenceRole.OFFICIAL_REAL,
            evidence_origin=EvidenceOrigin.OFFICIAL_NATIVE,
            source_qualification_reference="source-evidence:adfa:sha256:" + "2" * 64,
            dataset_family=DatasetFamily.ADFA_LD,
            dataset_version="ADFA-LD",
            dataset_native_scope="native traces",
            dataset_native_role="training",
            dataset_subset="train",
            domain_scope=DomainScope.NATIVE_ADFA_LD,
        )
        self.assertTrue(validate_semantic_identity(base).valid)
        invalid = (
            replace(base, dataset_family=None),
            replace(base, dataset_version="HAI-23.05"),
            replace(base, dataset_native_scope="   "),
            replace(base, limitations=()),
        )
        for identity in invalid:
            with self.subTest(identity=identity):
                self.assertFalse(validate_semantic_identity(identity).valid)

    def test_final_review_role_status_origin_matrix_rejects_promotion(self) -> None:
        invalid = (
            self._identity(result_role=ResultRole.PUBLISHED_REFERENCE),
            self._identity(evidence_role=EvidenceRole.LEGACY_V1,
                           result_role=ResultRole.LEGACY_RECORDED,
                           scientific_status=ScientificStatus.QUALIFIED,
                           owning_gate_reference="gate:legacy:sha256:" + "3" * 64),
            self._identity(scientific_status=ScientificStatus.UNSUPPORTED),
            self._identity(evidence_origin=EvidenceOrigin.PROTOTYPE_GENERATED,
                           synthetic_status=SyntheticStatus.AUTHENTIC),
            self._identity(evidence_origin=EvidenceOrigin.OFFICIAL_NATIVE,
                           evidence_role=EvidenceRole.PUBLISHED_REFERENCE,
                           source_qualification_reference="source:official:sha256:" + "4" * 64,
                           generation_origin=EvidenceOrigin.PROTOTYPE_GENERATED),
        )
        for identity in invalid:
            with self.subTest(identity=identity):
                self.assertFalse(validate_semantic_identity(identity).valid)

    def test_final_review_legacy_mapping_binds_exact_baseline_entry(self) -> None:
        baseline = self._baseline()
        mapping = LegacySemanticMapping(
            mapping_id="legacy-map:bound",
            vocabulary_version=SEMANTIC_VOCABULARY_VERSION,
            baseline_id=baseline.baseline_id or "",
            entry_id="legacy:one",
            original_field="scientific_status",
            original_value="MEASURED_RESULT",
            current_semantic_assignment=(("result_role", "locally_measured"),),
            provenance_references=("baseline-entry:legacy:one",),
            limitations=("Historical result remains unqualified.",),
        )
        self.assertTrue(validate_legacy_mapping(mapping, baseline=baseline).valid)
        for invalid in (
            replace(mapping, baseline_id="sha256:" + "f" * 64),
            replace(mapping, original_field="role"),
            replace(mapping, original_value="PUBLISHED_REFERENCE"),
        ):
            with self.subTest(mapping=invalid):
                self.assertFalse(validate_legacy_mapping(invalid, baseline=baseline).valid)
        sensor = replace(
            mapping,
            original_field="sensor",
            original_value="sensor-temperature",
            current_semantic_assignment=(
                ("logical_channel", "sensor-temperature"),
                ("source_context", "v1 simulator/signal emulator"),
                ("hardware_claim", "unsupported"),
                ("domain_scope", "real_plant"),
            ),
        )
        self.assertFalse(validate_legacy_mapping(sensor, baseline=baseline).valid)

    def test_final_review_parser_rejects_unknown_fields_and_bad_members(self) -> None:
        unknown = self._identity().to_dict()
        unknown["guessed_modality"] = "physical_instrumentation"
        malformed = self._identity().to_dict()
        malformed["limitations"] = ["valid", 7]
        bad_influence = self._identity().to_dict()
        bad_influence["mock_influences"] = [{
            "field_path": 7,
            "parameter_evidence_reference": self.PARAMETER_AUTHORITY,
            "mock_admission_reference": MOCK_ADMISSION_PTFP_SIGNAL_EMULATOR_V1,
            "derivation": [],
        }]
        for payload in (unknown, malformed, bad_influence):
            with self.subTest(payload=payload):
                self.assertIsInstance(parse_semantic_identity(payload), UnsupportedSemanticIdentity)

    def test_final_review_direct_types_fail_deterministically(self) -> None:
        wrong_boolean = self._identity(formal_evidence="false")
        mixed_references = self._identity(provenance_references=("source:one", 7))
        self.assertFalse(validate_semantic_identity(wrong_boolean).valid)
        self.assertFalse(validate_semantic_identity(mixed_references).valid)

    def test_final_review_mock_admission_and_influence_paths_are_exact(self) -> None:
        base = self._identity(
            modalities=(DetectionModality.PHYSICAL_INSTRUMENTATION,),
            evidence_origin=EvidenceOrigin.MOCK_PARAMETERIZED,
            synthetic_status=SyntheticStatus.MOCK_DERIVED,
            generation_origin=EvidenceOrigin.PROTOTYPE_GENERATED,
            mock_admission_reference="mock-admission:anything",
            mock_influences=(MockInfluence("value", self.PARAMETER_AUTHORITY,
                                          "mock-admission:anything"),),
            domain_scope=DomainScope.COMPRESSOR_PROTOTYPE,
        )
        duplicate = replace(
            base,
            mock_admission_reference=MOCK_ADMISSION_PTFP_SIGNAL_EMULATOR_V1,
            mock_influences=(
                MockInfluence("value", self.PARAMETER_AUTHORITY,
                              MOCK_ADMISSION_PTFP_SIGNAL_EMULATOR_V1),
                MockInfluence("value", "parameter-evidence:other:sha256:" + "5" * 64,
                              MOCK_ADMISSION_PTFP_SIGNAL_EMULATOR_V1),
            ),
        )
        self.assertFalse(validate_semantic_identity(base).valid)
        self.assertFalse(validate_semantic_identity(duplicate).valid)

    def test_final_review_identifiers_and_numeric_authority_are_immutable(self) -> None:
        numeric = self._identity(
            entity_kind=EntityKind.EVALUATION_RESULT,
            modalities=(DetectionModality.LINUX_HOST_SYSCALL,),
            numeric_authority_references=(self.PARAMETER_AUTHORITY,),
        )
        self.assertTrue(validate_semantic_identity(numeric).valid)
        invalid = (
            replace(numeric, identity_id="semantic:latest"),
            replace(numeric, numeric_authority_references=("x:y",)),
            replace(numeric, numeric_authority_references=("parameter-evidence:latest",)),
        )
        for identity in invalid:
            with self.subTest(identity=identity):
                self.assertFalse(validate_semantic_identity(identity).valid)


if __name__ == "__main__":
    unittest.main()
