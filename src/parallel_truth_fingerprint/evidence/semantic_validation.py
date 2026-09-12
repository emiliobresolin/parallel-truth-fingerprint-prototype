"""Pure, deterministic validation for ``semantic-vocabulary.v1``."""

from __future__ import annotations

import re
from typing import Iterable, Mapping

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
    SemanticValidationResult,
    SemanticViolation,
    SyntheticStatus,
    UnsupportedSemanticIdentity,
)
from parallel_truth_fingerprint.contracts.v1_baseline import V1BaselineManifest


MOCK_ADMISSION_PTFP_SIGNAL_EMULATOR_V1 = (
    "mock-admission-ptfp-signal-emulator-v1"
)

STABLE_RULE_IDS = (
    "SEM-ADFA-AS-PHYSICAL",
    "SEM-AUTHENTIC-CAPTURE-PROVENANCE",
    "SEM-CUSTOM-AS-OFFICIAL-OR-REAL-PLANT",
    "SEM-CUSTOM-PHYSICAL-NOT-MOCK-DERIVED",
    "SEM-DATASET-NATIVE-SCOPE-MISSING",
    "SEM-DATASET-NATIVE-MISMATCH",
    "SEM-EXTERNAL-MODEL-AS-COMPRESSOR-DETECTOR",
    "SEM-FIXTURE-AS-MEASURED",
    "SEM-HAI-AS-COMPRESSOR",
    "SEM-IDENTITY-MISSING",
    "SEM-LEGACY-MAPPING-INCOMPLETE",
    "SEM-LID-AS-PHYSICAL",
    "SEM-MOCK-GENERATION-ORIGIN",
    "SEM-MOCK-INFLUENCE-INCOMPLETE",
    "SEM-NUMERIC-AUTHORITY-MISSING",
    "SEM-MODALITY-REQUIRED",
    "SEM-MODEL-AS-DATASET",
    "SEM-MODEL-ONLY-AS-DETECTOR",
    "SEM-OFFICIAL-NATIVE-SCOPE",
    "SEM-OFFICIAL-REAL-WITHOUT-SOURCE-QUALIFICATION",
    "SEM-ORIGIN-INCOMPATIBLE",
    "SEM-ORIGIN-MISSING",
    "SEM-ORIGIN-PROMOTION",
    "SEM-ORIGIN-UNKNOWN",
    "SEM-QUALIFIED-WITHOUT-GATE-REFERENCE",
    "SEM-REFERENCE-INVALID",
    "SEM-REFERENCE-AS-MEASURED",
    "SEM-REPRESENTATION-CROSS-MODALITY",
    "SEM-SYSCALL-SYNTHETIC",
    "SEM-TEST-FIXTURE-FORMAL-PATH",
    "SEM-TOKEN-UNKNOWN",
    "SEM-VERSION-MISSING",
    "SEM-VERSION-UNSUPPORTED",
)

SHA256_ID_PATTERN = re.compile(r"^sha256:[0-9a-f]{64}$")
NUMERIC_AUTHORITY_PATTERN = re.compile(
    r"^parameter-evidence:[a-z0-9][a-z0-9._-]*(?::[a-z0-9][a-z0-9._-]*)*:sha256:[0-9a-f]{64}$"
)
MUTABLE_REFERENCE_MARKERS = frozenset({"current", "head", "latest"})
DATASET_VERSIONS = {
    DatasetFamily.ADFA_LD.value: "ADFA-LD",
    DatasetFamily.LID_DS_2021.value: "LID-DS-2021",
    DatasetFamily.HAI_23_05.value: "HAI-23.05",
    DatasetFamily.PTFP_CUSTOM_V1.value: "PTFP-Custom-v1",
}


class SemanticWriteError(ValueError):
    """Raised when invalid semantics reach a scientific serialization boundary."""

LEGACY_LABEL_ASSIGNMENTS: Mapping[str, tuple[tuple[str, str], ...]] = {
    "IMPLEMENTED_RUNTIME_EVIDENCE": (("evidence_role", "runtime_evidence"),),
    "FIXTURE": (
        ("evidence_role", "fixture_test"),
        ("result_role", "fixture_expected"),
    ),
    "PUBLISHED_REFERENCE": (
        ("evidence_role", "published_reference"),
        ("result_role", "published_reference"),
    ),
    "MEASURED_RESULT": (("result_role", "locally_measured"),),
    "EXPERIMENTAL_FINGERPRINT_BASELINE": (
        ("evidence_role", "legacy_v1"),
        ("model_family", "baseline"),
    ),
    "LEGACY_BASELINE": (("evidence_role", "legacy_v1"),),
    "lstm_autoencoder": (("model_families", "autoencoder,lstm"),),
}


def legacy_assignment_for_label(label: str) -> tuple[tuple[str, str], ...] | None:
    """Return the explicit v1 interpretation without modifying its source entry."""

    return LEGACY_LABEL_ASSIGNMENTS.get(label)


def legacy_sensor_assignment(
    logical_channel: str,
    *,
    source_context: str,
) -> tuple[tuple[str, str], ...]:
    """Interpret a historical sensor label without claiming physical hardware."""

    if not logical_channel.strip() or not source_context.strip():
        raise ValueError("logical channel and preserved source context are required")
    return tuple(sorted((
        ("logical_channel", logical_channel),
        ("source_context", source_context),
        ("hardware_claim", "unsupported"),
    )))


def _raw_token(value: object) -> str:
    return str(value.value if hasattr(value, "value") else value)


def _violation(
    rule_id: str,
    fields: Iterable[str],
    tokens: Iterable[object],
    explanation: str,
) -> SemanticViolation:
    return SemanticViolation(
        rule_id=rule_id,
        fields=tuple(sorted(set(fields))),
        offending_tokens=tuple(sorted({_raw_token(token) for token in tokens if token is not None})),
        explanation=explanation,
    )


def _result(violations: Iterable[SemanticViolation], *, supported: bool = True) -> SemanticValidationResult:
    ordered = tuple(sorted(violations, key=lambda item: (item.rule_id, item.fields, item.offending_tokens)))
    return SemanticValidationResult(
        supported=supported,
        valid=supported and not ordered,
        violations=ordered,
    )


def _known(value: object, enum_type: type) -> bool:
    try:
        enum_type(value)
    except (TypeError, ValueError):
        return False
    return True


def _contains(values: Iterable[object], token: object) -> bool:
    target = _raw_token(token)
    return any(_raw_token(value) == target for value in values)


def _nonblank(value: object) -> bool:
    return isinstance(value, str) and bool(value.strip())


def _immutable_reference(value: object) -> bool:
    if not (
        _nonblank(value)
        and value == value.strip()
        and ":" in value
        and not any(character.isspace() for character in value)
    ):
        return False
    segments = {segment.lower() for segment in re.split(r"[:/@]", value) if segment}
    return not segments.intersection(MUTABLE_REFERENCE_MARKERS)


def _numeric_authority_reference(value: object) -> bool:
    return isinstance(value, str) and NUMERIC_AUTHORITY_PATTERN.fullmatch(value) is not None


def _stable_identity(value: object) -> bool:
    if not _nonblank(value) or value != value.strip():
        return False
    segments = {segment.lower() for segment in re.split(r"[:/@]", value) if segment}
    return not segments.intersection(MUTABLE_REFERENCE_MARKERS)


def validate_semantic_identity(identity: SemanticIdentity) -> SemanticValidationResult:
    """Validate only explicit fields; never infer, mutate, authorize, or publish."""

    violations: list[SemanticViolation] = []
    if identity.vocabulary_version is None or not str(identity.vocabulary_version).strip():
        violations.append(_violation(
            "SEM-VERSION-MISSING", ("vocabulary_version",), (),
            "Provide the exact semantic vocabulary version.",
        ))
    elif identity.vocabulary_version != SEMANTIC_VOCABULARY_VERSION:
        violations.append(_violation(
            "SEM-VERSION-UNSUPPORTED", ("vocabulary_version",), (identity.vocabulary_version,),
            "The semantic vocabulary version is not supported by this validator.",
        ))
    if not _stable_identity(identity.identity_id):
        violations.append(_violation(
            "SEM-IDENTITY-MISSING", ("identity_id",), (identity.identity_id,),
            "A stable non-blank semantic identity without mutable aliases is required for provenance joins.",
        ))

    if type(identity.formal_evidence) is not bool:
        violations.append(_violation(
            "SEM-TOKEN-UNKNOWN", ("formal_evidence",), (identity.formal_evidence,),
            "formal_evidence must be an explicit boolean, not a truthy substitute.",
        ))

    enum_fields = (
        ("entity_kind", (identity.entity_kind,), EntityKind),
        ("modalities", identity.modalities, DetectionModality),
        ("representations", identity.representations, RepresentationKind),
        ("model_families", identity.model_families, ModelFamily),
        ("evidence_role", (identity.evidence_role,), EvidenceRole),
        ("result_role", (identity.result_role,), ResultRole),
        ("scientific_status", (identity.scientific_status,), ScientificStatus),
        ("synthetic_status", (identity.synthetic_status,), SyntheticStatus),
        ("domain_scope", (identity.domain_scope,), DomainScope),
    )
    if identity.dataset_family is not None:
        enum_fields += (("dataset_family", (identity.dataset_family,), DatasetFamily),)
    if identity.evidence_origin is not None:
        enum_fields += (("evidence_origin", (identity.evidence_origin,), EvidenceOrigin),)
    if identity.generation_origin is not None:
        enum_fields += (("generation_origin", (identity.generation_origin,), EvidenceOrigin),)
    for field_name, values, enum_type in enum_fields:
        unknown = tuple(value for value in values if not _known(value, enum_type))
        if unknown:
            violations.append(_violation(
                "SEM-TOKEN-UNKNOWN", (field_name,), unknown,
                f"Use an exact {SEMANTIC_VOCABULARY_VERSION} token; unknown values are never normalized.",
            ))

    origin_known = identity.evidence_origin is not None and _known(identity.evidence_origin, EvidenceOrigin)
    if identity.evidence_origin is None:
        violations.append(_violation(
            "SEM-ORIGIN-MISSING", ("evidence_origin",), (),
            "Every domain-bearing semantic identity requires one explicit evidence origin.",
        ))
    elif not origin_known:
        violations.append(_violation(
            "SEM-ORIGIN-UNKNOWN", ("evidence_origin",), (identity.evidence_origin,),
            "Use one closed EvidenceOrigin token; unknown origins cannot be promoted or guessed.",
        ))

    modality_required = {
        EntityKind.DATASET.value,
        EntityKind.RUN.value,
        EntityKind.REPRESENTATION.value,
        EntityKind.SCORE.value,
        EntityKind.EVALUATION_RESULT.value,
        EntityKind.DETECTOR_BUNDLE.value,
    }
    if _raw_token(identity.entity_kind) in modality_required and not identity.modalities:
        violations.append(_violation(
            "SEM-MODALITY-REQUIRED", ("entity_kind", "modalities"), (identity.entity_kind,),
            "Datasets, runs, representations, scores, and evaluation results must declare a modality.",
        ))

    physical_representations = {
        RepresentationKind.RAW_CURRENT_MA.value,
        RepresentationKind.NORMALIZED_SPAN.value,
        RepresentationKind.ENGINEERING_VALUE.value,
    }
    for representation in identity.representations:
        token = _raw_token(representation)
        incompatible = (
            token in physical_representations
            and not _contains(identity.modalities, DetectionModality.PHYSICAL_INSTRUMENTATION)
        ) or (
            token == RepresentationKind.CATEGORICAL_SYSCALL_EVENT.value
            and not _contains(identity.modalities, DetectionModality.LINUX_HOST_SYSCALL)
        )
        if incompatible:
            violations.append(_violation(
                "SEM-REPRESENTATION-CROSS-MODALITY", ("representations", "modalities"),
                (representation, *identity.modalities),
                "The representation is incompatible with the explicitly declared modality.",
            ))

    numeric_entity = _raw_token(identity.entity_kind) in {
        EntityKind.SCORE.value,
        EntityKind.EVALUATION_RESULT.value,
    }
    numeric_representation = any(
        _raw_token(item) in physical_representations
        for item in identity.representations
    )
    invalid_numeric_references = (
        (numeric_entity or numeric_representation)
        and (
            not identity.numeric_authority_references
            or any(not _numeric_authority_reference(item) for item in identity.numeric_authority_references)
        )
    )
    if invalid_numeric_references:
        violations.append(_violation(
            "SEM-NUMERIC-AUTHORITY-MISSING",
            ("entity_kind", "representations", "numeric_authority_references"),
            identity.numeric_authority_references,
            "Numeric identities require immutable authority references; Story 9.4 validates their full closure.",
        ))

    if _raw_token(identity.entity_kind) == EntityKind.DATASET.value and identity.model_families:
        violations.append(_violation(
            "SEM-MODEL-AS-DATASET", ("entity_kind", "model_families"),
            (identity.entity_kind, *identity.model_families),
            "Model-family tags cannot define a dataset identity.",
        ))
    if _raw_token(identity.entity_kind) == EntityKind.DETECTOR_BUNDLE.value and (
        not identity.model_families
        or not _immutable_reference(identity.detector_bundle_reference)
    ):
        violations.append(_violation(
            "SEM-MODEL-ONLY-AS-DETECTOR", ("entity_kind", "model_families", "detector_bundle_reference"),
            identity.model_families,
            "A model family alone is not a frozen compatible detector bundle.",
        ))

    evidence_role = _raw_token(identity.evidence_role)
    result_role = _raw_token(identity.result_role)
    origin = _raw_token(identity.evidence_origin) if identity.evidence_origin is not None else None
    if evidence_role == EvidenceRole.FIXTURE_TEST.value and result_role == ResultRole.LOCALLY_MEASURED.value:
        violations.append(_violation(
            "SEM-FIXTURE-AS-MEASURED", ("evidence_role", "result_role"),
            (identity.evidence_role, identity.result_role),
            "A fixture expected value cannot enter a locally measured result namespace.",
        ))
    if evidence_role == EvidenceRole.PUBLISHED_REFERENCE.value and result_role == ResultRole.LOCALLY_MEASURED.value:
        violations.append(_violation(
            "SEM-REFERENCE-AS-MEASURED", ("evidence_role", "result_role"),
            (identity.evidence_role, identity.result_role),
            "An externally published reference is not a locally measured result.",
        ))
    semantic_promotion = (
        result_role == ResultRole.PUBLISHED_REFERENCE.value
        and (
            evidence_role != EvidenceRole.PUBLISHED_REFERENCE.value
            or origin != EvidenceOrigin.OFFICIAL_NATIVE.value
            or _raw_token(identity.scientific_status) != ScientificStatus.REFERENCE_ONLY.value
        )
    ) or (
        (evidence_role == EvidenceRole.LEGACY_V1.value or result_role == ResultRole.LEGACY_RECORDED.value)
        and not (
            evidence_role == EvidenceRole.LEGACY_V1.value
            and result_role == ResultRole.LEGACY_RECORDED.value
            and _raw_token(identity.scientific_status) == ScientificStatus.LEGACY.value
        )
    ) or _raw_token(identity.scientific_status) == ScientificStatus.UNSUPPORTED.value or (
        origin == EvidenceOrigin.PROTOTYPE_GENERATED.value
        and _raw_token(identity.synthetic_status) == SyntheticStatus.AUTHENTIC.value
    ) or (
        origin == EvidenceOrigin.OFFICIAL_NATIVE.value
        and (
            identity.generation_origin is not None
            or identity.mock_admission_reference is not None
            or bool(identity.mock_influences)
        )
    )
    if semantic_promotion:
        violations.append(_violation(
            "SEM-ORIGIN-INCOMPATIBLE",
            ("evidence_role", "result_role", "scientific_status", "evidence_origin", "synthetic_status"),
            (identity.evidence_role, identity.result_role, identity.scientific_status,
             identity.evidence_origin, identity.synthetic_status),
            "Evidence role, result role, scientific status, origin, and synthetic lineage cannot promote one another.",
        ))
    if (
        evidence_role == EvidenceRole.OFFICIAL_REAL.value
        and not _immutable_reference(identity.source_qualification_reference)
    ):
        violations.append(_violation(
            "SEM-OFFICIAL-REAL-WITHOUT-SOURCE-QUALIFICATION",
            ("evidence_role", "source_qualification_reference"), (identity.evidence_role,),
            "Official-real means owner-origin evidence in native scope and requires its immutable source qualification.",
        ))
    if (
        _raw_token(identity.scientific_status) == ScientificStatus.QUALIFIED.value
        and not _immutable_reference(identity.owning_gate_reference)
    ):
        violations.append(_violation(
            "SEM-QUALIFIED-WITHOUT-GATE-REFERENCE",
            ("scientific_status", "owning_gate_reference"), (identity.scientific_status,),
            "Qualified status requires the immutable result of its owning gate.",
        ))

    family = _raw_token(identity.dataset_family) if identity.dataset_family is not None else None
    scope = _raw_token(identity.domain_scope)
    scientific_status = _raw_token(identity.scientific_status)
    is_physical = _contains(identity.modalities, DetectionModality.PHYSICAL_INSTRUMENTATION)
    is_syscall = _contains(identity.modalities, DetectionModality.LINUX_HOST_SYSCALL)
    is_fixture_semantics = (
        _raw_token(identity.entity_kind) == EntityKind.FIXTURE.value
        and evidence_role == EvidenceRole.FIXTURE_TEST.value
        and result_role == ResultRole.FIXTURE_EXPECTED.value
        and scientific_status == ScientificStatus.TEST_ONLY.value
        and origin == EvidenceOrigin.TEST_FIXTURE.value
        and scope == DomainScope.NOT_APPLICABLE.value
        and not identity.formal_evidence
    )

    if _raw_token(identity.entity_kind) == EntityKind.DATASET.value and family is None:
        violations.append(_violation(
            "SEM-DATASET-NATIVE-SCOPE-MISSING", ("entity_kind", "dataset_family"),
            (identity.entity_kind,),
            "A governed dataset identity must declare its closed dataset family.",
        ))

    custom_domain = (
        evidence_role == EvidenceRole.CUSTOM_GENERATED.value
        and not is_fixture_semantics
        and (bool(identity.modalities) or scope != DomainScope.NOT_APPLICABLE.value or identity.formal_evidence)
    )
    if custom_domain and family != DatasetFamily.PTFP_CUSTOM_V1.value:
        violations.append(_violation(
            "SEM-DATASET-NATIVE-MISMATCH", ("evidence_role", "dataset_family", "domain_scope"),
            (identity.evidence_role, identity.dataset_family, identity.domain_scope),
            "Domain-bearing custom evidence belongs to PTFP-Custom-v1 and cannot omit or borrow a dataset family.",
        ))
    if family == DatasetFamily.PTFP_CUSTOM_V1.value and not is_fixture_semantics and (
        scope != DomainScope.PTFP_CUSTOM_CONTROLLED.value
        or identity.dataset_version != DATASET_VERSIONS[DatasetFamily.PTFP_CUSTOM_V1.value]
    ):
        violations.append(_violation(
            "SEM-DATASET-NATIVE-MISMATCH", ("dataset_family", "dataset_version", "domain_scope"),
            (identity.dataset_family, identity.dataset_version, identity.domain_scope),
            "PTFP-Custom-v1 evidence retains its exact version and controlled custom scope.",
        ))

    expected_external = {
        DatasetFamily.ADFA_LD.value: (
            frozenset({DetectionModality.LINUX_HOST_SYSCALL.value}),
            DomainScope.NATIVE_ADFA_LD.value,
        ),
        DatasetFamily.LID_DS_2021.value: (
            frozenset({DetectionModality.LINUX_HOST_SYSCALL.value}),
            DomainScope.NATIVE_LID_DS_2021.value,
        ),
        DatasetFamily.HAI_23_05.value: (
            frozenset({DetectionModality.PHYSICAL_INSTRUMENTATION.value}),
            DomainScope.NATIVE_HAI_23_05.value,
        ),
    }
    if family in expected_external and not is_fixture_semantics:
        expected_modalities, expected_scope = expected_external[family]
        observed_modalities = frozenset(_raw_token(item) for item in identity.modalities)
        if (
            observed_modalities != expected_modalities
            or scope != expected_scope
            or identity.dataset_version != DATASET_VERSIONS[family]
        ):
            violations.append(_violation(
                "SEM-DATASET-NATIVE-MISMATCH",
                ("dataset_family", "dataset_version", "modalities", "domain_scope"),
                (identity.dataset_family, identity.dataset_version, *identity.modalities, identity.domain_scope),
                "External datasets retain their exact version, native modality, and bounded domain scope.",
            ))
        if (
            origin != EvidenceOrigin.OFFICIAL_NATIVE.value
            or evidence_role not in {
                EvidenceRole.OFFICIAL_REAL.value,
                EvidenceRole.PUBLISHED_REFERENCE.value,
            }
            or not _immutable_reference(identity.source_qualification_reference)
        ):
            violations.append(_violation(
                "SEM-ORIGIN-INCOMPATIBLE",
                ("dataset_family", "evidence_origin", "evidence_role", "source_qualification_reference"),
                (identity.dataset_family, identity.evidence_origin, identity.evidence_role,
                 identity.source_qualification_reference),
                "External dataset semantics require qualified official-native evidence or an isolated non-domain fixture.",
            ))
    if family == DatasetFamily.HAI_23_05.value and scope in {
        DomainScope.COMPRESSOR_PROTOTYPE.value, DomainScope.REAL_PLANT.value
    }:
        violations.append(_violation(
            "SEM-HAI-AS-COMPRESSOR", ("dataset_family", "domain_scope"),
            (identity.dataset_family, identity.domain_scope),
            "HAI 23.05 remains native external physical/SCADA evidence, not compressor data.",
        ))
    if family == DatasetFamily.ADFA_LD.value and is_physical:
        violations.append(_violation(
            "SEM-ADFA-AS-PHYSICAL", ("dataset_family", "modalities"),
            (identity.dataset_family, *identity.modalities),
            "ADFA-LD is native categorical Linux syscall evidence, not physical evidence.",
        ))
    if family == DatasetFamily.LID_DS_2021.value and is_physical:
        violations.append(_violation(
            "SEM-LID-AS-PHYSICAL", ("dataset_family", "modalities"),
            (identity.dataset_family, *identity.modalities),
            "LID-DS 2021 is native categorical Linux syscall evidence, not physical evidence.",
        ))
    if family == DatasetFamily.PTFP_CUSTOM_V1.value and (
        evidence_role == EvidenceRole.OFFICIAL_REAL.value
        or scope == DomainScope.REAL_PLANT.value
        or origin == EvidenceOrigin.OFFICIAL_NATIVE.value
    ):
        violations.append(_violation(
            "SEM-CUSTOM-AS-OFFICIAL-OR-REAL-PLANT",
            ("dataset_family", "evidence_role", "domain_scope", "evidence_origin"),
            (identity.dataset_family, identity.evidence_role, identity.domain_scope, identity.evidence_origin),
            "Controlled custom evidence is neither an official-native dataset nor real-plant evidence.",
        ))
    if family == DatasetFamily.PTFP_CUSTOM_V1.value and is_physical and not is_fixture_semantics and (
        _raw_token(identity.synthetic_status) not in {
            SyntheticStatus.MOCK.value, SyntheticStatus.MOCK_DERIVED.value
        }
        or origin != EvidenceOrigin.MOCK_PARAMETERIZED.value
        or identity.mock_admission_reference != MOCK_ADMISSION_PTFP_SIGNAL_EMULATOR_V1
    ):
        violations.append(_violation(
            "SEM-CUSTOM-PHYSICAL-NOT-MOCK-DERIVED",
            ("dataset_family", "modalities", "synthetic_status", "evidence_origin", "mock_admission_reference"),
            (identity.synthetic_status, identity.evidence_origin, identity.mock_admission_reference),
            "Current custom physical evidence must retain admitted mock lineage from the bounded signal emulator.",
        ))
    invalid_custom_syscall = False
    if family == DatasetFamily.PTFP_CUSTOM_V1.value and is_syscall and not is_fixture_semantics:
        if is_physical:
            invalid_custom_syscall = not _immutable_reference(identity.authentic_capture_reference)
        else:
            invalid_custom_syscall = (
                _raw_token(identity.synthetic_status) != SyntheticStatus.AUTHENTIC.value
                or origin != EvidenceOrigin.AUTHENTIC_CAPTURE.value
                or not _immutable_reference(identity.authentic_capture_reference)
            )
    if invalid_custom_syscall:
        violations.append(_violation(
            "SEM-SYSCALL-SYNTHETIC",
            ("dataset_family", "modalities", "synthetic_status", "evidence_origin",
             "authentic_capture_reference"),
            (identity.synthetic_status, identity.evidence_origin,
             identity.authentic_capture_reference),
            "Formal custom syscall evidence requires authentic host capture; generated or replayed syscalls remain fixtures.",
        ))
    if (
        _raw_token(identity.entity_kind) == EntityKind.DETECTOR_BUNDLE.value
        and family in {DatasetFamily.ADFA_LD.value, DatasetFamily.LID_DS_2021.value, DatasetFamily.HAI_23_05.value}
        and scope in {DomainScope.COMPRESSOR_PROTOTYPE.value, DomainScope.REAL_PLANT.value}
    ):
        violations.append(_violation(
            "SEM-EXTERNAL-MODEL-AS-COMPRESSOR-DETECTOR",
            ("entity_kind", "dataset_family", "domain_scope"),
            (identity.entity_kind, identity.dataset_family, identity.domain_scope),
            "An external benchmark model is not a compressor detector.",
        ))
    if family is not None and not is_fixture_semantics and (
        any(not _nonblank(value) for value in (
            identity.dataset_version,
            identity.dataset_native_scope,
            identity.dataset_native_role,
            identity.dataset_subset,
        ))
        or not identity.limitations
        or any(not _nonblank(limitation) for limitation in identity.limitations)
    ):
        violations.append(_violation(
            "SEM-DATASET-NATIVE-SCOPE-MISSING",
            ("dataset_version", "dataset_native_scope", "dataset_native_role", "dataset_subset", "limitations"),
            (identity.dataset_family,),
            "Governed dataset identities retain non-blank version, native scope, native file role, subset, and limitations.",
        ))

    if evidence_role == EvidenceRole.OFFICIAL_REAL.value and origin != EvidenceOrigin.OFFICIAL_NATIVE.value:
        violations.append(_violation(
            "SEM-ORIGIN-INCOMPATIBLE", ("evidence_role", "evidence_origin"),
            (identity.evidence_role, identity.evidence_origin),
            "Official-real evidence requires official-native origin in its qualified native scope.",
        ))
    if origin == EvidenceOrigin.OFFICIAL_NATIVE.value and (
        evidence_role not in {
            EvidenceRole.OFFICIAL_REAL.value,
            EvidenceRole.PUBLISHED_REFERENCE.value,
        }
        or not _immutable_reference(identity.source_qualification_reference)
    ):
        violations.append(_violation(
            "SEM-ORIGIN-INCOMPATIBLE",
            ("evidence_origin", "evidence_role", "source_qualification_reference"),
            (identity.evidence_origin, identity.evidence_role,
             identity.source_qualification_reference),
            "Official-native origin requires an eligible role and immutable source qualification.",
        ))
    expected_native_scopes = {
        DatasetFamily.ADFA_LD.value: DomainScope.NATIVE_ADFA_LD.value,
        DatasetFamily.LID_DS_2021.value: DomainScope.NATIVE_LID_DS_2021.value,
        DatasetFamily.HAI_23_05.value: DomainScope.NATIVE_HAI_23_05.value,
    }
    if origin == EvidenceOrigin.OFFICIAL_NATIVE.value and (
        family not in expected_native_scopes or scope != expected_native_scopes.get(family)
    ):
        violations.append(_violation(
            "SEM-OFFICIAL-NATIVE-SCOPE", ("evidence_origin", "dataset_family", "domain_scope"),
            (identity.evidence_origin, identity.dataset_family, identity.domain_scope),
            "Official-native origin is reserved for pinned owner-origin external datasets in native scope.",
        ))
    if (
        origin == EvidenceOrigin.AUTHENTIC_CAPTURE.value
        and not _immutable_reference(identity.authentic_capture_reference)
    ):
        violations.append(_violation(
            "SEM-AUTHENTIC-CAPTURE-PROVENANCE", ("evidence_origin", "authentic_capture_reference"),
            (identity.evidence_origin,),
            "Authentic capture requires its immutable qualified capture-boundary provenance reference.",
        ))
    if origin == EvidenceOrigin.TEST_FIXTURE.value and identity.formal_evidence:
        violations.append(_violation(
            "SEM-TEST-FIXTURE-FORMAL-PATH", ("evidence_origin", "formal_evidence"),
            (identity.evidence_origin, identity.formal_evidence),
            "Test fixtures are conspicuous non-domain material and cannot enter a formal evidence path.",
        ))
    synthetic = _raw_token(identity.synthetic_status)
    fixture_marked = (
        _raw_token(identity.entity_kind) == EntityKind.FIXTURE.value
        or origin == EvidenceOrigin.TEST_FIXTURE.value
        or evidence_role == EvidenceRole.FIXTURE_TEST.value
        or result_role == ResultRole.FIXTURE_EXPECTED.value
    )
    origin_lineage_incompatible = (
        origin == EvidenceOrigin.MOCK_PARAMETERIZED.value
        and synthetic not in {SyntheticStatus.MOCK.value, SyntheticStatus.MOCK_DERIVED.value}
    ) or (
        synthetic in {SyntheticStatus.MOCK.value, SyntheticStatus.MOCK_DERIVED.value}
        and origin != EvidenceOrigin.MOCK_PARAMETERIZED.value
    ) or (
        origin == EvidenceOrigin.TEST_FIXTURE.value
        and evidence_role != EvidenceRole.FIXTURE_TEST.value
    ) or (
        evidence_role == EvidenceRole.FIXTURE_TEST.value
        and origin != EvidenceOrigin.TEST_FIXTURE.value
    ) or (
        result_role == ResultRole.FIXTURE_EXPECTED.value
        and origin != EvidenceOrigin.TEST_FIXTURE.value
    ) or (
        fixture_marked and not is_fixture_semantics
    ) or (
        origin == EvidenceOrigin.AUTHENTIC_CAPTURE.value
        and (
            synthetic != SyntheticStatus.AUTHENTIC.value
            or identity.generation_origin is not None
            or identity.mock_admission_reference is not None
            or bool(identity.mock_influences)
        )
    )
    if origin_lineage_incompatible:
        violations.append(_violation(
            "SEM-ORIGIN-INCOMPATIBLE",
            ("evidence_origin", "evidence_role", "result_role", "synthetic_status"),
            (identity.evidence_origin, identity.evidence_role, identity.result_role, identity.synthetic_status),
            "Evidence origin, role, result role, and synthetic lineage are explicitly incompatible.",
        ))
    if origin == EvidenceOrigin.MOCK_PARAMETERIZED.value:
        if _raw_token(identity.generation_origin) != EvidenceOrigin.PROTOTYPE_GENERATED.value:
            violations.append(_violation(
                "SEM-MOCK-GENERATION-ORIGIN", ("evidence_origin", "generation_origin"),
                (identity.evidence_origin, identity.generation_origin),
                "Mock-parameterized evidence must bind the prototype-generated producer origin.",
            ))
        influence_paths = [influence.field_path for influence in identity.mock_influences]
        influence_paths_are_strings = all(isinstance(path, str) for path in influence_paths)
        domain_bearing_mock = bool(identity.modalities) or scope != DomainScope.NOT_APPLICABLE.value or identity.formal_evidence
        invalid_influences = (
            not identity.mock_influences
            or not identity.mock_admission_reference
            or (domain_bearing_mock and identity.mock_admission_reference != MOCK_ADMISSION_PTFP_SIGNAL_EMULATOR_V1)
            or not influence_paths_are_strings
            or any(influence_paths.count(path) > 1 for path in influence_paths)
            or any(
                not _nonblank(influence.field_path)
                or not _numeric_authority_reference(influence.parameter_evidence_reference)
                or not _nonblank(influence.mock_admission_reference)
                or influence.mock_admission_reference != identity.mock_admission_reference
                or (influence.derivation is not None and not _nonblank(influence.derivation))
                for influence in identity.mock_influences
            )
        )
        if invalid_influences:
            violations.append(_violation(
                "SEM-MOCK-INFLUENCE-INCOMPLETE",
                ("mock_influences", "mock_admission_reference"),
                (identity.mock_admission_reference,),
                "Every mock-influenced field requires one unique path, immutable parameter authority, and the exact current admission.",
            ))
    if origin in {
        EvidenceOrigin.PROTOTYPE_GENERATED.value,
        EvidenceOrigin.MOCK_PARAMETERIZED.value,
        EvidenceOrigin.TEST_FIXTURE.value,
    } and (
        evidence_role == EvidenceRole.OFFICIAL_REAL.value
        or scope == DomainScope.REAL_PLANT.value
    ):
        violations.append(_violation(
            "SEM-ORIGIN-PROMOTION", ("evidence_origin", "evidence_role", "domain_scope"),
            (identity.evidence_origin, identity.evidence_role, identity.domain_scope),
            "Prototype, mock, and fixture origins cannot be promoted to official-native or real-plant claims.",
        ))

    external_families = {
        DatasetFamily.ADFA_LD.value,
        DatasetFamily.LID_DS_2021.value,
        DatasetFamily.HAI_23_05.value,
    }
    if identity.formal_evidence and family in external_families and origin != EvidenceOrigin.OFFICIAL_NATIVE.value:
        violations.append(_violation(
            "SEM-ORIGIN-INCOMPATIBLE", ("formal_evidence", "dataset_family", "evidence_origin"),
            (identity.dataset_family, identity.evidence_origin),
            "Formal external dataset evidence accepts only pinned official-native origin.",
        ))

    reference_collections = {
        "numeric_authority_references": identity.numeric_authority_references,
        "provenance_references": identity.provenance_references,
        "qualification_references": identity.qualification_references,
    }
    invalid_reference_fields = [
        field_name
        for field_name, references in reference_collections.items()
        if any(not _immutable_reference(reference) for reference in references)
    ]
    if any(not _numeric_authority_reference(reference) for reference in identity.numeric_authority_references):
        invalid_reference_fields.append("numeric_authority_references")
    scalar_references = {
        "source_qualification_reference": identity.source_qualification_reference,
        "owning_gate_reference": identity.owning_gate_reference,
        "authentic_capture_reference": identity.authentic_capture_reference,
        "detector_bundle_reference": identity.detector_bundle_reference,
    }
    invalid_reference_fields.extend(
        field_name
        for field_name, reference in scalar_references.items()
        if reference is not None and not _immutable_reference(reference)
    )
    if identity.mock_admission_reference is not None and not _nonblank(identity.mock_admission_reference):
        invalid_reference_fields.append("mock_admission_reference")
    if any(not _nonblank(limitation) for limitation in identity.limitations):
        invalid_reference_fields.append("limitations")
    if invalid_reference_fields:
        violations.append(_violation(
            "SEM-REFERENCE-INVALID", invalid_reference_fields, (),
            "Explicit references and limitations must be non-blank immutable identifiers or text.",
        ))

    return _result(violations, supported=identity.vocabulary_version == SEMANTIC_VOCABULARY_VERSION)


def validate_legacy_mapping(
    mapping: LegacySemanticMapping,
    *,
    baseline: V1BaselineManifest,
) -> SemanticValidationResult:
    violations: list[SemanticViolation] = []
    entries_by_id = {entry.entry_id: entry for entry in baseline.entries}
    source_entry = entries_by_id.get(mapping.entry_id)
    expected_assignment = legacy_assignment_for_label(mapping.original_value)
    forbidden_assignment_fields = {"mutate", "replace", "qualify", "relabel", "source_entry"}
    assignment_fields = [field_name for field_name, _ in mapping.current_semantic_assignment]
    duplicate_assignment_fields = len(assignment_fields) != len(set(assignment_fields))
    sensor_mapping_valid = False
    if mapping.original_field in {"sensor", "sensor_id"} and not duplicate_assignment_fields:
        assignment = dict(mapping.current_semantic_assignment)
        sensor_mapping_valid = (
            set(assignment) == {"logical_channel", "source_context", "hardware_claim"}
            and assignment.get("logical_channel") == mapping.original_value
            and _nonblank(assignment.get("source_context"))
            and assignment.get("hardware_claim") == ScientificStatus.UNSUPPORTED.value
        )
    source_field_matches = (
        sensor_mapping_valid
        or (
            source_entry is not None
            and mapping.original_field in source_entry.to_dict()
            and source_entry.to_dict()[mapping.original_field] == mapping.original_value
        )
    )
    exact_assignment = (
        expected_assignment is not None
        and mapping.current_semantic_assignment == tuple(sorted(expected_assignment))
    )
    incomplete = (
        mapping.vocabulary_version != SEMANTIC_VOCABULARY_VERSION
        or SHA256_ID_PATTERN.fullmatch(mapping.baseline_id) is None
        or baseline.baseline_id is None
        or mapping.baseline_id != baseline.baseline_id
        or source_entry is None
        or not source_field_matches
        or not _nonblank(mapping.mapping_id)
        or not _nonblank(mapping.original_field)
        or not (exact_assignment or sensor_mapping_valid)
        or not mapping.current_semantic_assignment
        or not mapping.provenance_references
        or any(not _immutable_reference(reference) for reference in mapping.provenance_references)
        or not mapping.limitations
        or any(not _nonblank(limitation) for limitation in mapping.limitations)
        or mapping.scientific_status != ScientificStatus.LEGACY
        or duplicate_assignment_fields
        or any(field_name in forbidden_assignment_fields for field_name, _ in mapping.current_semantic_assignment)
    )
    if incomplete:
        violations.append(_violation(
            "SEM-LEGACY-MAPPING-INCOMPLETE",
            ("vocabulary_version", "baseline_id", "entry_id", "original_field", "original_value",
             "current_semantic_assignment", "provenance_references", "limitations", "scientific_status"),
            (mapping.original_value, mapping.entry_id),
            "A legacy interpretation must bind a known frozen entry, known label, provenance, limitation, and forced legacy status without rewriting it.",
        ))
    return _result(violations)


def _parse_enum(raw: object, enum_type: type, field_name: str, violations: list[SemanticViolation]) -> object:
    try:
        return enum_type(raw)
    except (TypeError, ValueError):
        violations.append(_violation(
            "SEM-TOKEN-UNKNOWN", (field_name,), (raw,),
            f"Unknown {field_name} token; no fallback or spelling normalization is permitted.",
        ))
        return raw


def parse_semantic_identity(raw_payload: Mapping[str, object]) -> SemanticIdentity | UnsupportedSemanticIdentity:
    """Parse a complete explicit payload or preserve it untouched as unsupported."""

    raw = dict(raw_payload)
    version = raw.get("vocabulary_version")
    violations: list[SemanticViolation] = []
    allowed_fields = {
        "vocabulary_version", "identity_id", "entity_kind", "modalities", "representations",
        "model_families", "evidence_role", "result_role", "scientific_status", "synthetic_status",
        "evidence_origin", "generation_origin", "mock_influences", "dataset_family",
        "dataset_version", "dataset_native_scope", "dataset_native_role", "dataset_subset",
        "domain_scope", "numeric_authority_references", "provenance_references",
        "qualification_references", "source_qualification_reference", "owning_gate_reference",
        "mock_admission_reference", "authentic_capture_reference", "detector_bundle_reference",
        "limitations", "formal_evidence",
    }
    unknown_fields = tuple(sorted(str(field) for field in raw if field not in allowed_fields))
    if unknown_fields:
        violations.append(_violation(
            "SEM-TOKEN-UNKNOWN", unknown_fields, (),
            "Unknown semantic fields are rejected rather than silently discarded.",
        ))
    if version is None or not str(version).strip():
        violations.append(_violation(
            "SEM-VERSION-MISSING", ("vocabulary_version",), (),
            "The raw semantic payload does not declare a vocabulary version.",
        ))
    elif version != SEMANTIC_VOCABULARY_VERSION:
        violations.append(_violation(
            "SEM-VERSION-UNSUPPORTED", ("vocabulary_version",), (version,),
            "The raw vocabulary version is preserved but unsupported.",
        ))
    if violations:
        return UnsupportedSemanticIdentity(version, raw, _result(violations, supported=False).violations)

    required = {
        "identity_id", "entity_kind", "modalities", "representations", "model_families",
        "evidence_role", "result_role", "scientific_status", "synthetic_status",
        "evidence_origin", "domain_scope", "numeric_authority_references", "formal_evidence",
    }
    missing = sorted(required.difference(raw))
    if missing:
        violations.append(_violation(
            "SEM-TOKEN-UNKNOWN", tuple(missing), (),
            "Required semantic fields are missing; the parser does not supply defaults.",
        ))
        return UnsupportedSemanticIdentity(version, raw, _result(violations, supported=False).violations)

    scalar_specs = {
        "entity_kind": EntityKind,
        "evidence_role": EvidenceRole,
        "result_role": ResultRole,
        "scientific_status": ScientificStatus,
        "synthetic_status": SyntheticStatus,
        "evidence_origin": EvidenceOrigin,
        "domain_scope": DomainScope,
    }
    parsed: dict[str, object] = {}
    for field_name, enum_type in scalar_specs.items():
        parsed[field_name] = _parse_enum(raw.get(field_name), enum_type, field_name, violations)
    for field_name, enum_type in (
        ("modalities", DetectionModality),
        ("representations", RepresentationKind),
        ("model_families", ModelFamily),
    ):
        values = raw.get(field_name)
        if not isinstance(values, (list, tuple)):
            violations.append(_violation(
                "SEM-TOKEN-UNKNOWN", (field_name,), (values,),
                f"{field_name} must be an explicit token list.",
            ))
            continue
        parsed[field_name] = tuple(
            _parse_enum(value, enum_type, field_name, violations) for value in values
        )
    if not isinstance(raw.get("identity_id"), str):
        violations.append(_violation(
            "SEM-TOKEN-UNKNOWN", ("identity_id",), (raw.get("identity_id"),),
            "identity_id must be an explicit string.",
        ))
    if type(raw.get("formal_evidence")) is not bool:
        violations.append(_violation(
            "SEM-TOKEN-UNKNOWN", ("formal_evidence",), (raw.get("formal_evidence"),),
            "formal_evidence must be an explicit JSON boolean.",
        ))
    parsed_collections: dict[str, tuple[object, ...]] = {}
    for field_name in (
        "numeric_authority_references",
        "provenance_references",
        "qualification_references",
        "limitations",
    ):
        values = raw.get(field_name, [])
        if not isinstance(values, (list, tuple)):
            violations.append(_violation(
                "SEM-TOKEN-UNKNOWN", (field_name,), (values,),
                f"{field_name} must be an explicit list.",
            ))
            continue
        if any(not isinstance(value, str) for value in values):
            violations.append(_violation(
                "SEM-TOKEN-UNKNOWN", (field_name,), values,
                f"{field_name} members must be explicit strings.",
            ))
            continue
        parsed_collections[field_name] = tuple(values)

    optional_string_fields = (
        "dataset_version", "dataset_native_scope", "dataset_native_role", "dataset_subset",
        "source_qualification_reference", "owning_gate_reference", "mock_admission_reference",
        "authentic_capture_reference", "detector_bundle_reference",
    )
    for field_name in optional_string_fields:
        value = raw.get(field_name)
        if value is not None and not isinstance(value, str):
            violations.append(_violation(
                "SEM-TOKEN-UNKNOWN", (field_name,), (value,),
                f"{field_name} must be a string or null.",
            ))
    dataset_family = raw.get("dataset_family")
    parsed["dataset_family"] = (
        None if dataset_family is None
        else _parse_enum(dataset_family, DatasetFamily, "dataset_family", violations)
    )
    generation_origin = raw.get("generation_origin")
    parsed["generation_origin"] = (
        None if generation_origin is None
        else _parse_enum(generation_origin, EvidenceOrigin, "generation_origin", violations)
    )
    influences: list[MockInfluence] = []
    raw_influences = raw.get("mock_influences", [])
    if isinstance(raw_influences, (list, tuple)):
        for item in raw_influences:
            if not isinstance(item, Mapping):
                violations.append(_violation(
                    "SEM-TOKEN-UNKNOWN", ("mock_influences",), (item,),
                    "Mock influence entries must be structured mappings.",
                ))
                continue
            influence_fields = {
                "field_path", "parameter_evidence_reference", "mock_admission_reference", "derivation"
            }
            if set(item).difference(influence_fields) or not {
                "field_path", "parameter_evidence_reference", "mock_admission_reference"
            }.issubset(item):
                violations.append(_violation(
                    "SEM-TOKEN-UNKNOWN", ("mock_influences",), tuple(item),
                    "Mock influence fields must match the closed v1 record.",
                ))
                continue
            if (
                not isinstance(item.get("field_path"), str)
                or not isinstance(item.get("parameter_evidence_reference"), str)
                or not isinstance(item.get("mock_admission_reference"), str)
                or (item.get("derivation") is not None and not isinstance(item.get("derivation"), str))
            ):
                violations.append(_violation(
                    "SEM-TOKEN-UNKNOWN", ("mock_influences",), (),
                    "Mock influence values must retain their exact string or null types.",
                ))
                continue
            influences.append(MockInfluence(
                field_path=item["field_path"],  # type: ignore[arg-type]
                parameter_evidence_reference=item["parameter_evidence_reference"],  # type: ignore[arg-type]
                mock_admission_reference=item["mock_admission_reference"],  # type: ignore[arg-type]
                derivation=item.get("derivation"),  # type: ignore[arg-type]
            ))
    else:
        violations.append(_violation(
            "SEM-TOKEN-UNKNOWN", ("mock_influences",), (raw_influences,),
            "mock_influences must be an explicit list.",
        ))
    if violations:
        return UnsupportedSemanticIdentity(version, raw, _result(violations, supported=False).violations)

    identity = SemanticIdentity(
        vocabulary_version=str(version),
        identity_id=str(raw["identity_id"]),
        entity_kind=parsed["entity_kind"],  # type: ignore[arg-type]
        modalities=parsed["modalities"],  # type: ignore[arg-type]
        representations=parsed["representations"],  # type: ignore[arg-type]
        model_families=parsed["model_families"],  # type: ignore[arg-type]
        evidence_role=parsed["evidence_role"],  # type: ignore[arg-type]
        result_role=parsed["result_role"],  # type: ignore[arg-type]
        scientific_status=parsed["scientific_status"],  # type: ignore[arg-type]
        synthetic_status=parsed["synthetic_status"],  # type: ignore[arg-type]
        evidence_origin=parsed["evidence_origin"],  # type: ignore[arg-type]
        generation_origin=parsed["generation_origin"],  # type: ignore[arg-type]
        mock_influences=tuple(influences),
        dataset_family=parsed["dataset_family"],  # type: ignore[arg-type]
        dataset_version=raw.get("dataset_version"),  # type: ignore[arg-type]
        dataset_native_scope=raw.get("dataset_native_scope"),  # type: ignore[arg-type]
        dataset_native_role=raw.get("dataset_native_role"),  # type: ignore[arg-type]
        dataset_subset=raw.get("dataset_subset"),  # type: ignore[arg-type]
        domain_scope=parsed["domain_scope"],  # type: ignore[arg-type]
        numeric_authority_references=parsed_collections["numeric_authority_references"],  # type: ignore[arg-type]
        formal_evidence=raw["formal_evidence"],  # type: ignore[arg-type]
        provenance_references=parsed_collections["provenance_references"],  # type: ignore[arg-type]
        qualification_references=parsed_collections["qualification_references"],  # type: ignore[arg-type]
        source_qualification_reference=raw.get("source_qualification_reference"),  # type: ignore[arg-type]
        owning_gate_reference=raw.get("owning_gate_reference"),  # type: ignore[arg-type]
        mock_admission_reference=raw.get("mock_admission_reference"),  # type: ignore[arg-type]
        authentic_capture_reference=raw.get("authentic_capture_reference"),  # type: ignore[arg-type]
        detector_bundle_reference=raw.get("detector_bundle_reference"),  # type: ignore[arg-type]
        limitations=parsed_collections["limitations"],  # type: ignore[arg-type]
    )
    validation = validate_semantic_identity(identity)
    if not validation.supported or not validation.valid:
        return UnsupportedSemanticIdentity(version, raw, validation.violations)
    return identity


def validated_semantic_payload(identity: SemanticIdentity) -> dict[str, object]:
    """Serialize only identities that pass the scientific semantic gate."""

    validation = validate_semantic_identity(identity)
    if not validation.supported or not validation.valid:
        rule_ids = ", ".join(violation.rule_id for violation in validation.violations)
        raise SemanticWriteError(f"semantic identity is not writable: {rule_ids}")
    return identity.to_dict()
