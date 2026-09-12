"""Pure, offline validation and replay for registered v1 golden fixtures."""

from __future__ import annotations

import base64
import hashlib
import json
import math
import re
from dataclasses import fields, replace
from pathlib import Path, PureWindowsPath
from typing import Callable, Mapping

from parallel_truth_fingerprint.contracts.semantic_vocabulary import (
    DomainScope,
    EvidenceOrigin,
    EvidenceRole,
    ResultRole,
    ScientificStatus,
    SemanticIdentity,
    SyntheticStatus,
)
from parallel_truth_fingerprint.contracts.v1_golden_fixture import *
from parallel_truth_fingerprint.evidence.semantic_validation import (
    parse_semantic_identity,
    validate_semantic_identity,
)
from parallel_truth_fingerprint.evidence.parameter_evidence import (
    mock_admission_identity,
    parameter_revision_identity,
)
from parallel_truth_fingerprint.evidence.source_catalog import validate_source_catalog


DIGEST = re.compile(r"^sha256:[0-9a-f]{64}$")
MAX_FIXTURE_BYTES = 1_048_576
STORY_9_5_CATALOG_ID = "sha256:9e954bd3291f34079e3b8a370d0f9496417a01b834b83333d8c8d1d5cf34d144"
MANDATORY_PROHIBITED_USES = frozenset({
    "dataset", "training", "metric", "truth", "final_result",
})
PROHIBITED_CONSUMER_USES = frozenset({
    "dataset_root", "sample", "window", "label", "metric", "ranking", "truth",
    "uncertainty", "training", "calibration", "final_result", "publication",
})
READERS = frozenset({
    "opaque.bytes.v1", "python.json.v1", "mqtt.raw-hart.v1",
    "python.consensus.v1", "go.consensus.v1", "persistence.json.v1",
    "manifest.json.v1", "detector.schema.v1",
})
COMPARATORS = {
    ComparisonMode.BYTE_EXACT.value: frozenset({"bytes.exact.v1"}),
    ComparisonMode.SEMANTIC_EXACT.value: frozenset({
        "json.type-strict.v1", "detector.feature-order.v1", "opaque-key.exact.v1",
    }),
}


def _requirement(
    requirement_id: str,
    reader: str,
    legacy: NativeReaderOutcome = NativeReaderOutcome.ACCEPTED,
    gate: FixtureGateOutcome = FixtureGateOutcome.UNVERIFIABLE,
    comparison: ComparisonMode = ComparisonMode.SEMANTIC_EXACT,
    group: FixtureGroup = FixtureGroup.CORE,
) -> V1GoldenFixtureRequirement:
    return V1GoldenFixtureRequirement(
        requirement_id, group, reader,
        (FixtureOrigin.FROZEN_HISTORICAL_BYTES,
         FixtureOrigin.RECONSTRUCTED_LEGACY_FIXTURE,
         FixtureOrigin.NON_DOMAIN_SENTINEL,
         FixtureOrigin.ADMITTED_DOMAIN_MOCK_FIXTURE),
        legacy, gate, comparison,
    )


_REQUIREMENTS = (
    _requirement("mqtt.topic", "opaque.bytes.v1", comparison=ComparisonMode.BYTE_EXACT),
    _requirement("mqtt.payload.basic", "python.json.v1"),
    _requirement("mqtt.payload.optional_sv", "mqtt.raw-hart.v1"),
    _requirement("mqtt.payload.malformed", "python.json.v1", NativeReaderOutcome.REJECTED,
                 FixtureGateOutcome.REJECTED),
    _requirement("mqtt.payload.truncated", "python.json.v1", NativeReaderOutcome.REJECTED,
                 FixtureGateOutcome.REJECTED),
    _requirement("mqtt.payload.duplicate_key", "python.json.v1", NativeReaderOutcome.ACCEPTED,
                 FixtureGateOutcome.REJECTED),
    _requirement("mqtt.payload.non_utf8", "python.json.v1", NativeReaderOutcome.REJECTED,
                 FixtureGateOutcome.REJECTED),
    _requirement("mqtt.version.missing", "python.json.v1"),
    _requirement("mqtt.version.unknown", "python.json.v1", NativeReaderOutcome.ACCEPTED,
                 FixtureGateOutcome.REJECTED),
    _requirement("consensus.python.transaction", "python.consensus.v1"),
    _requirement("consensus.go.transaction", "go.consensus.v1"),
    _requirement("consensus.committed.success", "go.consensus.v1"),
    _requirement("consensus.committed.exclusion", "go.consensus.v1"),
    _requirement("consensus.committed.failed", "go.consensus.v1"),
    _requirement("consensus.query.found", "go.consensus.v1"),
    _requirement("consensus.query.missing", "go.consensus.v1", NativeReaderOutcome.REJECTED,
                 FixtureGateOutcome.REJECTED),
    _requirement("consensus.ordering", "python.consensus.v1"),
    _requirement("consensus.divergence", "go.consensus.v1"),
    _requirement("persistence.object.key", "opaque.bytes.v1", comparison=ComparisonMode.BYTE_EXACT),
    _requirement("persistence.object.content", "persistence.json.v1"),
    _requirement("persistence.object.missing", "persistence.json.v1",
                 NativeReaderOutcome.NOT_INVOKED, FixtureGateOutcome.REJECTED),
    _requirement("persistence.object.corrupt", "persistence.json.v1",
                 NativeReaderOutcome.REJECTED, FixtureGateOutcome.REJECTED),
    _requirement("manifest.dataset", "manifest.json.v1"),
    _requirement("manifest.artifact", "manifest.json.v1"),
    _requirement("manifest.schema_mismatch", "manifest.json.v1", NativeReaderOutcome.ACCEPTED,
                 FixtureGateOutcome.REJECTED),
    _requirement("detector.input.schema", "detector.schema.v1"),
    _requirement("detector.output.recorded", "python.json.v1"),
    _requirement("detector.input.missing", "detector.schema.v1", NativeReaderOutcome.REJECTED,
                 FixtureGateOutcome.REJECTED),
    _requirement("detector.input.extra", "detector.schema.v1", NativeReaderOutcome.REJECTED,
                 FixtureGateOutcome.REJECTED),
    _requirement("detector.input.permuted", "detector.schema.v1", NativeReaderOutcome.REJECTED,
                 FixtureGateOutcome.REJECTED),
    _requirement("detector.input.v2_only", "detector.schema.v1", NativeReaderOutcome.REJECTED,
                 FixtureGateOutcome.REJECTED),
    _requirement("detector.value.nonfinite", "detector.schema.v1", NativeReaderOutcome.ACCEPTED,
                 FixtureGateOutcome.REJECTED),
    _requirement("dashboard.read_model", "python.json.v1", group=FixtureGroup.OPTIONAL_DASHBOARD),
)


def _json_bytes(value: object) -> bytes:
    return (json.dumps(value, sort_keys=True, ensure_ascii=False, separators=(",", ":"),
                       allow_nan=False) + "\n").encode("utf-8")


def _identity_payload(record: object, excluded: tuple[str, ...]) -> dict[str, object]:
    payload = record.to_dict()  # type: ignore[attr-defined]
    for name in excluded:
        payload[name] = ""
    return payload


def requirement_set_identity(record: V1GoldenFixtureRequirementSet) -> str:
    return "sha256:" + hashlib.sha256(_json_bytes(
        _identity_payload(record, ("requirement_set_id",))
    )).hexdigest()


_UNIDENTIFIED_REQUIREMENTS = V1GoldenFixtureRequirementSet(
    GOLDEN_REQUIREMENT_SCHEMA_VERSION, "", _REQUIREMENTS,
    ("Core completeness is code-owned; dashboard fixtures are optional.",
     "No scientific activity or validity is authorized."),
)
GOLDEN_REQUIREMENT_SET = replace(
    _UNIDENTIFIED_REQUIREMENTS,
    requirement_set_id=requirement_set_identity(_UNIDENTIFIED_REQUIREMENTS),
)


def fixture_revision_identity(record: V1GoldenFixtureEntry) -> str:
    return "sha256:" + hashlib.sha256(_json_bytes(
        _identity_payload(record, ("fixture_revision_id", "fixture_revision_sha256"))
    )).hexdigest()


def adapter_identity(record: V1GoldenAdapterDeclaration) -> str:
    return "sha256:" + hashlib.sha256(_json_bytes(
        _identity_payload(record, ("adapter_revision_id",))
    )).hexdigest()


def catalog_identity(catalog: V1GoldenFixtureCatalog) -> str:
    return "sha256:" + hashlib.sha256(_json_bytes(
        _identity_payload(catalog, ("catalog_id",))
    )).hexdigest()


def replay_request_identity(request: V1GoldenReplayRequest) -> str:
    return "sha256:" + hashlib.sha256(_json_bytes(
        _identity_payload(request, ("request_id",))
    )).hexdigest()


def explicit_envelope_identity(entry: V1GoldenFixtureEntry) -> str:
    """Derive the only envelope identity eligible for one registered explicit version."""

    return "sha256:" + hashlib.sha256(_json_bytes({
        "schema_version": "v1-golden-explicit-envelope.v1",
        "fixture_revision_id": entry.fixture_revision_id,
        "native_version": entry.native_version_token,
        "payload_sha256": entry.decoded_sha256,
    })).hexdigest()


def canonical_catalog_bytes(catalog: V1GoldenFixtureCatalog) -> bytes:
    return _json_bytes(catalog.to_dict())


def canonical_requirement_set_bytes(requirements: V1GoldenFixtureRequirementSet) -> bytes:
    return _json_bytes(requirements.to_dict())


def _bounded(value: object) -> str:
    text = str(value).replace("\x00", "[NUL]")
    lowered = text.casefold()
    if any(marker in lowered for marker in ("password=", "secret=", "token=", "private key")):
        return "[REDACTED]"
    return text[:160]


def _violation(
    rule: str, identity: object, contract: object, field: str, offending: object,
    expected: object, observed: object, explanation: str,
) -> V1GoldenViolation:
    return V1GoldenViolation(rule, _bounded(identity), _bounded(contract), field,
                             _bounded(offending), _bounded(expected), _bounded(observed), explanation)


def _safe_locator(locator: object) -> bool:
    if not isinstance(locator, str) or not locator or "\x00" in locator or "\\" in locator:
        return False
    if locator.startswith(("/", "~")) or "//" in locator or PureWindowsPath(locator).is_absolute():
        return False
    parts = locator.split("/")
    return all(part not in {"", ".", ".."} and ":" not in part for part in parts)


def _stable_id(value: object) -> bool:
    if not isinstance(value, str) or not value or value != value.strip():
        return False
    segments = {part.casefold() for part in re.split(r"[:/@]", value) if part}
    return not segments.intersection({"latest", "current"})


def _resolve_fixture_path(
    root: Path, locator: str, resolver: Callable[[Path], Path] | None = None,
) -> Path | None:
    if not _safe_locator(locator):
        return None
    resolve = resolver or (lambda item: item.resolve(strict=False))
    resolved_root = resolve(root)
    target = resolve(root / Path(locator))
    try:
        target.relative_to(resolved_root)
    except ValueError:
        return None
    if target.exists() and (not target.is_file() or target.is_symlink()):
        return None
    return target


def decode_carrier(carrier: bytes) -> bytes:
    if len(carrier) > MAX_FIXTURE_BYTES * 2 or not carrier or any(byte > 127 for byte in carrier):
        raise ValueError("carrier is not bounded ASCII")
    if any(chr(byte).isspace() for byte in carrier):
        raise ValueError("carrier whitespace is forbidden")
    try:
        decoded = base64.b64decode(carrier, validate=True)
    except (ValueError, base64.binascii.Error) as exc:
        raise ValueError("carrier is not strict RFC 4648 base64") from exc
    if len(decoded) > MAX_FIXTURE_BYTES or base64.b64encode(decoded) != carrier:
        raise ValueError("carrier is noncanonical or too large")
    return decoded


def load_registered_fixture_bytes(
    entry: V1GoldenFixtureEntry,
    *,
    fixture_root: Path | None = None,
    object_store: Mapping[str, bytes] | None = None,
    path_resolver: Callable[[Path], Path] | None = None,
) -> bytes:
    """Load only one already-registered opaque fixture without executing a reader."""

    if entry.filesystem_locator is not None:
        if fixture_root is None:
            raise ValueError("fixture_root is required for filesystem fixtures")
        path = _resolve_fixture_path(fixture_root, entry.filesystem_locator, path_resolver)
        if path is None or not path.is_file():
            raise ValueError("registered fixture locator is missing or unsafe")
        if path.stat().st_size > MAX_FIXTURE_BYTES * 2:
            raise ValueError("registered fixture carrier exceeds size bound")
        raw = path.read_bytes()
        payload = decode_carrier(raw) if str(entry.storage_encoding) == StorageEncoding.BASE64.value else raw
    elif entry.object_key is not None:
        if object_store is None or entry.object_key not in object_store:
            raise ValueError("registered opaque object key is unavailable")
        raw = object_store[entry.object_key]
        if len(raw) > MAX_FIXTURE_BYTES * 2:
            raise ValueError("registered fixture object exceeds size bound")
        payload = decode_carrier(raw) if str(entry.storage_encoding) == StorageEncoding.BASE64.value else raw
    else:
        raise ValueError("registered fixture has no storage identity")
    observed = "sha256:" + hashlib.sha256(payload).hexdigest()
    if len(payload) != entry.decoded_byte_length or observed != entry.decoded_sha256:
        raise ValueError("registered fixture bytes do not match size/hash")
    return payload


def _pairs_no_duplicates(pairs: list[tuple[str, object]]) -> dict[str, object]:
    result: dict[str, object] = {}
    for key, value in pairs:
        if key in result:
            raise ValueError(f"duplicate JSON key: {key}")
        result[key] = value
    return result


def _loads_json(payload: bytes | str) -> object:
    def reject_constant(token: str) -> None:
        raise ValueError(f"nonfinite JSON token: {token}")
    return json.loads(payload, object_pairs_hook=_pairs_no_duplicates, parse_constant=reject_constant)


def _exact(data: object, cls: type) -> dict[str, object]:
    if not isinstance(data, dict):
        raise ValueError(f"{cls.__name__} must be an object")
    expected = {item.name for item in fields(cls) if item.init}
    if set(data) != expected:
        raise ValueError(f"{cls.__name__} has unknown or missing fields")
    return data


def load_catalog(payload: bytes | str) -> V1GoldenFixtureCatalog:
    raw = _loads_json(payload)
    if not isinstance(raw, dict) or raw.get("authorization_effect") != "none":
        raise ValueError("authorization_effect must be none")
    catalog_input = dict(raw)
    catalog_input.pop("authorization_effect")
    catalog_data = _exact(catalog_input, V1GoldenFixtureCatalog).copy()
    entries: list[V1GoldenFixtureEntry] = []
    for raw_entry in catalog_data["entries"]:  # type: ignore[union-attr]
        item = _exact(raw_entry, V1GoldenFixtureEntry).copy()
        semantic = parse_semantic_identity(item["semantic_identity"])  # type: ignore[arg-type]
        if not isinstance(semantic, SemanticIdentity):
            raise ValueError("fixture semantic identity is unsupported")
        item["semantic_identity"] = semantic
        item["parameter_revision_bindings"] = tuple(
            FixtureParameterRevisionBinding(**_exact(value, FixtureParameterRevisionBinding))
            for value in item["parameter_revision_bindings"]  # type: ignore[union-attr]
        )
        entries.append(V1GoldenFixtureEntry(**item))
    adapters = tuple(
        V1GoldenAdapterDeclaration(**_exact(value, V1GoldenAdapterDeclaration))
        for value in catalog_data["adapters"]  # type: ignore[union-attr]
    )
    return V1GoldenFixtureCatalog(
        schema_version=catalog_data["schema_version"],  # type: ignore[arg-type]
        catalog_id=catalog_data["catalog_id"],  # type: ignore[arg-type]
        requirement_set_id=catalog_data["requirement_set_id"],  # type: ignore[arg-type]
        entries=tuple(entries), adapters=adapters,
        limitations=tuple(catalog_data["limitations"]),  # type: ignore[arg-type]
    )


def _semantic_is_compatible(entry: V1GoldenFixtureEntry) -> bool:
    identity = entry.semantic_identity
    origin = str(entry.origin)
    semantic_validation = validate_semantic_identity(identity)
    if not semantic_validation.supported or not semantic_validation.valid:
        return False
    if origin == FixtureOrigin.FROZEN_HISTORICAL_BYTES.value:
        return (
            str(identity.evidence_role) == EvidenceRole.LEGACY_V1.value
            and str(identity.result_role) == ResultRole.LEGACY_RECORDED.value
            and str(identity.scientific_status) == ScientificStatus.LEGACY.value
        )
    if origin in {
        FixtureOrigin.RECONSTRUCTED_LEGACY_FIXTURE.value,
        FixtureOrigin.NON_DOMAIN_SENTINEL.value,
    }:
        return (
            str(identity.evidence_role) == EvidenceRole.FIXTURE_TEST.value
            and str(identity.result_role) == ResultRole.FIXTURE_EXPECTED.value
            and str(identity.scientific_status) == ScientificStatus.TEST_ONLY.value
            and str(identity.domain_scope) == DomainScope.NOT_APPLICABLE.value
            and str(identity.synthetic_status) == SyntheticStatus.NOT_APPLICABLE.value
        )
    return (
        origin == FixtureOrigin.ADMITTED_DOMAIN_MOCK_FIXTURE.value
        and str(identity.evidence_role) == EvidenceRole.FIXTURE_TEST.value
        and str(identity.result_role) == ResultRole.FIXTURE_EXPECTED.value
        and str(identity.scientific_status) == ScientificStatus.TEST_ONLY.value
        and str(identity.synthetic_status) in {
            SyntheticStatus.MOCK.value, SyntheticStatus.MOCK_DERIVED.value,
        }
        and bool(entry.mock_admission_id) and bool(entry.parameter_revision_bindings)
    )


def validate_catalog(
    catalog: V1GoldenFixtureCatalog,
    *,
    fixture_root: Path | None = None,
    path_resolver: Callable[[Path], Path] | None = None,
    baseline_manifest: object | None = None,
    parameter_catalog: object | None = None,
    source_catalog: object | None = None,
) -> V1GoldenCatalogValidationResult:
    violations: list[V1GoldenViolation] = []
    if catalog.schema_version != GOLDEN_CATALOG_SCHEMA_VERSION:
        violations.append(_violation("GOLD-SCHEMA-UNSUPPORTED", "catalog", "catalog",
                                     "schema_version", catalog.schema_version,
                                     GOLDEN_CATALOG_SCHEMA_VERSION, catalog.schema_version,
                                     "Only the closed Story 9.5 catalog schema is supported."))
    if catalog.catalog_id != catalog_identity(catalog):
        violations.append(_violation("GOLD-CATALOG-HASH-MISMATCH", "catalog", "catalog",
                                     "catalog_id", catalog.catalog_id, catalog_identity(catalog),
                                     catalog.catalog_id, "Catalog identity must bind canonical content."))
    if catalog.requirement_set_id != GOLDEN_REQUIREMENT_SET.requirement_set_id:
        violations.append(_violation("GOLD-REQUIREMENT-SET-MISMATCH", "catalog", "catalog",
                                     "requirement_set_id", catalog.requirement_set_id,
                                     GOLDEN_REQUIREMENT_SET.requirement_set_id,
                                     catalog.requirement_set_id,
                                     "Caller data cannot replace the code-owned inventory."))
    requirements = {item.requirement_id: item for item in GOLDEN_REQUIREMENT_SET.requirements}
    by_requirement: dict[str, list[V1GoldenFixtureEntry]] = {}
    fixture_ids: set[str] = set()
    revision_ids: set[str] = set()
    for entry in catalog.entries:
        by_requirement.setdefault(entry.requirement_id, []).append(entry)
        if entry.fixture_id in fixture_ids or entry.fixture_revision_id in revision_ids:
            violations.append(_violation("GOLD-ID-DUPLICATE", entry.fixture_id,
                                         entry.native_contract_id, "fixture_revision_id",
                                         entry.fixture_revision_id, "unique", "duplicate",
                                         "Fixture logical/revision identities must be unique."))
        fixture_ids.add(entry.fixture_id)
        revision_ids.add(entry.fixture_revision_id)
        expected_revision = fixture_revision_identity(entry)
        if entry.fixture_revision_id != expected_revision or entry.fixture_revision_sha256 != expected_revision:
            violations.append(_violation("GOLD-FIXTURE-HASH-MISMATCH", entry.fixture_id,
                                         entry.native_contract_id, "fixture_revision_id",
                                         entry.fixture_revision_id, expected_revision,
                                         entry.fixture_revision_sha256,
                                         "Fixture revision must bind every immutable declaration."))
        requirement = requirements.get(entry.requirement_id)
        if requirement is None:
            violations.append(_violation("GOLD-REQUIREMENT-UNKNOWN", entry.fixture_id,
                                         entry.native_contract_id, "requirement_id",
                                         entry.requirement_id, "code-owned requirement",
                                         entry.requirement_id, "Unknown slots cannot expand the inventory."))
        elif str(entry.origin) not in {str(item) for item in requirement.allowed_origins}:
            violations.append(_violation("GOLD-ORIGIN-INELIGIBLE", entry.fixture_id,
                                         entry.native_contract_id, "origin", entry.origin,
                                         requirement.allowed_origins, entry.origin,
                                         "Fixture origin is not permitted for this slot."))
        elif (
            str(entry.expected_legacy_reader_outcome)
            != str(requirement.expected_legacy_reader_outcome)
            or str(entry.expected_fixture_gate_outcome)
            != str(requirement.expected_fixture_gate_outcome)
            or str(entry.comparison_mode) != str(requirement.comparison_mode)
            or entry.reader_id != requirement.native_reader_id
        ):
            violations.append(_violation(
                "GOLD-EXPECTATION-MISMATCH", entry.fixture_id, entry.native_contract_id,
                "requirement_expectation", entry.requirement_id,
                f"{requirement.native_reader_id}|{requirement.expected_legacy_reader_outcome}|"
                f"{requirement.expected_fixture_gate_outcome}|{requirement.comparison_mode}",
                f"{entry.reader_id}|{entry.expected_legacy_reader_outcome}|"
                f"{entry.expected_fixture_gate_outcome}|{entry.comparison_mode}",
                "Catalog entries cannot rewrite the independent expected behavior.",
            ))
        if not all(_stable_id(item) for item in (
            entry.fixture_id, entry.requirement_id, entry.native_contract_id,
            entry.reader_id, entry.comparator_id, entry.comparator_version,
        )):
            violations.append(_violation(
                "GOLD-ID-MUTABLE", entry.fixture_id, entry.native_contract_id, "identity",
                entry.fixture_id, "stable non-mutable identities", entry.fixture_id,
                "Mutable aliases such as latest/current are forbidden.",
            ))
        enum_values = (
            (entry.origin, FixtureOrigin), (entry.native_version_status, NativeVersionStatus),
            (entry.storage_encoding, StorageEncoding),
            (entry.expected_legacy_reader_outcome, NativeReaderOutcome),
            (entry.expected_fixture_gate_outcome, FixtureGateOutcome),
            (entry.comparison_mode, ComparisonMode),
        )
        if any(str(value) not in {item.value for item in enum_type}
               for value, enum_type in enum_values):
            violations.append(_violation(
                "GOLD-TOKEN-INVALID", entry.fixture_id, entry.native_contract_id, "closed_tokens",
                entry.fixture_id, "closed Story 9.5 tokens", "unknown",
                "Fixture policy tokens are closed and type-strict.",
            ))
        if entry.baseline_generation != "v1":
            violations.append(_violation("GOLD-GENERATION-MISMATCH", entry.fixture_id,
                                         entry.native_contract_id, "baseline_generation",
                                         entry.baseline_generation, "v1", entry.baseline_generation,
                                         "Fixture generation is separate from native version."))
        if str(entry.native_version_status) == NativeVersionStatus.EXPLICIT.value:
            version_ok = bool(entry.native_version_token)
        else:
            version_ok = str(entry.native_version_status) == NativeVersionStatus.VERSIONLESS.value \
                and entry.native_version_token is None
        if not version_ok:
            violations.append(_violation("GOLD-VERSION-BINDING-INVALID", entry.fixture_id,
                                         entry.native_contract_id, "native_version_status",
                                         entry.native_version_status, "explicit token or versionless/null",
                                         entry.native_version_token, "Native version binding is inconsistent."))
        if not DIGEST.fullmatch(entry.decoded_sha256) or type(entry.decoded_byte_length) is not int \
                or entry.decoded_byte_length < 0 or entry.decoded_byte_length > MAX_FIXTURE_BYTES:
            violations.append(_violation("GOLD-CONTENT-IDENTITY-INVALID", entry.fixture_id,
                                         entry.native_contract_id, "decoded_sha256",
                                         entry.decoded_sha256, "bounded SHA-256 content", entry.decoded_byte_length,
                                         "Decoded byte identity must be exact and bounded."))
        if entry.filesystem_locator is not None and entry.object_key is not None:
            violations.append(_violation("GOLD-STORAGE-AMBIGUOUS", entry.fixture_id,
                                         entry.native_contract_id, "storage", "both", "exactly one", "both",
                                         "Filesystem locators and opaque object keys are distinct types."))
        if entry.filesystem_locator is not None and not _safe_locator(entry.filesystem_locator):
            violations.append(_violation("GOLD-LOCATOR-UNSAFE", entry.fixture_id,
                                         entry.native_contract_id, "filesystem_locator",
                                         entry.filesystem_locator, "safe root-relative locator",
                                         entry.filesystem_locator, "Unsafe local fixture locator."))
        if entry.filesystem_locator is None and entry.object_key is None:
            violations.append(_violation("GOLD-STORAGE-MISSING", entry.fixture_id,
                                         entry.native_contract_id, "storage", "none", "one locator", "none",
                                         "A fixture requires one storage identity."))
        if entry.reader_id not in READERS or entry.comparator_id not in COMPARATORS.get(
            str(entry.comparison_mode), frozenset()
        ):
            violations.append(_violation("GOLD-ROUTER-UNSUPPORTED", entry.fixture_id,
                                         entry.native_contract_id, "reader_or_comparator",
                                         f"{entry.reader_id}|{entry.comparator_id}", "closed registry",
                                         "unsupported", "Catalog data cannot request executable code."))
        if not entry.limitations or not MANDATORY_PROHIBITED_USES.issubset(entry.prohibited_uses):
            violations.append(_violation("GOLD-CLAIM-BOUNDARY-MISSING", entry.fixture_id,
                                         entry.native_contract_id, "prohibited_uses", entry.prohibited_uses,
                                         sorted(MANDATORY_PROHIBITED_USES), entry.prohibited_uses,
                                         "Fixture-only claim limits are mandatory."))
        if str(entry.expected_legacy_reader_outcome) != NativeReaderOutcome.ACCEPTED.value \
                or str(entry.expected_fixture_gate_outcome) != FixtureGateOutcome.ACCEPTED.value:
            if not entry.expected_reason:
                violations.append(_violation("GOLD-EXPECTED-REASON-MISSING", entry.fixture_id,
                                             entry.native_contract_id, "expected_reason", "", "nonblank", "",
                                             "Non-accepted outcomes require an exact expected reason."))
        if not _semantic_is_compatible(entry):
            violations.append(_violation("GOLD-SEMANTIC-PROMOTION", entry.fixture_id,
                                         entry.native_contract_id, "semantic_identity",
                                         entry.semantic_identity.identity_id, "fixture/legacy-only semantics",
                                         entry.semantic_identity.scientific_status,
                                         "Golden fixtures cannot become current scientific evidence."))
        if str(entry.origin) in {
            FixtureOrigin.RECONSTRUCTED_LEGACY_FIXTURE.value,
            FixtureOrigin.NON_DOMAIN_SENTINEL.value,
        } and not DIGEST.fullmatch(entry.reconstruction_identity or ""):
            violations.append(_violation("GOLD-RECONSTRUCTION-UNBOUND", entry.fixture_id,
                                         entry.native_contract_id, "reconstruction_identity",
                                         entry.reconstruction_identity, "sha256 identity",
                                         entry.reconstruction_identity,
                                         "Reconstructed bytes require exact code/runtime/seed closure."))
        if entry.baseline_id.startswith("unavailable:") or entry.baseline_entry_id.startswith("unavailable:"):
            violations.append(_violation("GOLD-BASELINE-UNAVAILABLE", entry.fixture_id,
                                         entry.native_contract_id, "baseline_id", entry.baseline_id,
                                         "published Story 9.1 baseline and entry", "unavailable",
                                         "Missing historical baseline remains explicit and blocked."))
        elif not DIGEST.fullmatch(entry.baseline_id) or not DIGEST.fullmatch(
            entry.baseline_entry_sha256 or ""
        ):
            violations.append(_violation("GOLD-BASELINE-BINDING-INVALID", entry.fixture_id,
                                         entry.native_contract_id, "baseline_provenance",
                                         entry.baseline_entry_id, "immutable baseline IDs", "invalid",
                                         "Historical provenance must bind exact Story 9.1 identity."))
        else:
            manifest_entries = getattr(baseline_manifest, "entries", ())
            matching_baseline = [item for item in manifest_entries
                                 if getattr(item, "entry_id", None) == entry.baseline_entry_id]
            if getattr(baseline_manifest, "baseline_id", None) != entry.baseline_id \
                    or len(matching_baseline) != 1 \
                    or getattr(matching_baseline[0], "sha256", None) != entry.baseline_entry_sha256:
                violations.append(_violation(
                    "GOLD-BASELINE-BINDING-INVALID", entry.fixture_id, entry.native_contract_id,
                    "baseline_provenance", entry.baseline_entry_id,
                    "exact published Story 9.1 entry", "unresolved/mismatched",
                    "Fixture provenance must resolve to the exact baseline object.",
                ))
        if str(entry.origin) == FixtureOrigin.ADMITTED_DOMAIN_MOCK_FIXTURE.value:
            admissions = getattr(parameter_catalog, "mock_admissions", ())
            admission = next((item for item in admissions
                              if item.mock_admission_id == entry.mock_admission_id), None)
            revisions = {item.parameter_revision_id: item
                         for item in getattr(parameter_catalog, "parameter_revisions", ())}
            bound = {item.parameter_revision_id: item.revision_sha256
                     for item in entry.parameter_revision_bindings}
            source_result = validate_source_catalog(source_catalog) if source_catalog is not None else None
            admission_ok = (
                admission is not None
                and admission.record_sha256 == mock_admission_identity(admission)
                and str(admission.reproduction_disposition) == "still_unavailable_with_evidence"
                and all(item in revisions and bound[item] == revisions[item].revision_sha256
                        and revisions[item].revision_sha256 == parameter_revision_identity(revisions[item])
                        for item in bound)
                and bool(bound)
                and source_result is not None and source_result.valid
                and all(
                    any(use.use_id == use_id and str(use.status) == "located"
                        and bool(use.exact_locator) for use in source_catalog.uses)
                    for claim in admission.support_claims for use_id in claim.source_use_ids
                )
            )
            if not admission_ok:
                violations.append(_violation(
                    "GOLD-MOCK-ADMISSION-INVALID", entry.fixture_id, entry.native_contract_id,
                    "mock_admission_id", entry.mock_admission_id,
                    "qualified Story 9.3/9.4 closure", "unresolved",
                    "Domain-bearing reconstructed fixtures require complete official-source, mock, and parameter closure.",
                ))
        text_fields = json.dumps(entry.to_dict(), ensure_ascii=False).casefold()
        if any(marker in text_fields for marker in ("password=", "secret=", "token=", "private key")):
            violations.append(_violation("GOLD-SECRET-MATERIAL", entry.fixture_id,
                                         entry.native_contract_id, "entry", "[REDACTED]", "no secrets",
                                         "[REDACTED]", "Secret-bearing fixture metadata is forbidden."))
        if fixture_root is not None and entry.filesystem_locator is not None:
            path = _resolve_fixture_path(fixture_root, entry.filesystem_locator, path_resolver)
            if path is None or not path.is_file():
                violations.append(_violation("GOLD-CONTENT-MISSING", entry.fixture_id,
                                             entry.native_contract_id, "filesystem_locator",
                                             entry.filesystem_locator, "regular fixture file", "missing/unsafe",
                                             "Fixture bytes must resolve within the fixture root."))
            else:
                carrier = path.read_bytes()
                try:
                    decoded = decode_carrier(carrier) if str(entry.storage_encoding) == StorageEncoding.BASE64.value \
                        else carrier
                except ValueError:
                    violations.append(_violation("GOLD-CARRIER-NONCANONICAL", entry.fixture_id,
                                                 entry.native_contract_id, "storage_encoding", "carrier",
                                                 "strict RFC 4648", "invalid",
                                                 "Carrier must be ASCII, unwrapped, canonical, and bounded."))
                else:
                    digest = "sha256:" + hashlib.sha256(decoded).hexdigest()
                    carrier_digest = "sha256:" + hashlib.sha256(carrier).hexdigest()
                    if len(decoded) != entry.decoded_byte_length or digest != entry.decoded_sha256:
                        violations.append(_violation("GOLD-HASH-MISMATCH", entry.fixture_id,
                                                     entry.native_contract_id, "decoded_content",
                                                     digest, entry.decoded_sha256, digest,
                                                     "Fixture bytes drifted from registration."))
                    if entry.carrier_sha256 is not None and carrier_digest != entry.carrier_sha256:
                        violations.append(_violation("GOLD-CARRIER-HASH-MISMATCH", entry.fixture_id,
                                                     entry.native_contract_id, "carrier_sha256",
                                                     carrier_digest, entry.carrier_sha256, carrier_digest,
                                                     "Carrier identity drifted."))
    for requirement in GOLDEN_REQUIREMENT_SET.requirements:
        count = len(by_requirement.get(requirement.requirement_id, ()))
        if requirement.group == FixtureGroup.CORE and count != requirement.cardinality:
            violations.append(_violation("GOLD-REQUIREMENT-MISSING", requirement.requirement_id,
                                         requirement.native_reader_id, "cardinality", count,
                                         requirement.cardinality, count,
                                         "Every pinned core slot requires its exact cardinality."))
        if requirement.group == FixtureGroup.OPTIONAL_DASHBOARD and count > requirement.cardinality:
            violations.append(_violation("GOLD-REQUIREMENT-CARDINALITY", requirement.requirement_id,
                                         requirement.native_reader_id, "cardinality", count,
                                         f"0..{requirement.cardinality}", count,
                                         "Optional groups may be absent but cannot be duplicated."))
    adapter_ids = {item.adapter_revision_id for item in catalog.adapters}
    for adapter in catalog.adapters:
        if adapter.adapter_revision_id != adapter_identity(adapter) or not adapter.field_mappings \
                or not DIGEST.fullmatch(adapter.code_identity):
            violations.append(_violation("GOLD-ADAPTER-INVALID", adapter.adapter_id, "adapter",
                                         "adapter_revision_id", adapter.adapter_revision_id,
                                         adapter_identity(adapter), adapter.adapter_revision_id,
                                         "Adapters require exact separate input/output and field mapping."))
        if adapter.input_fixture_revision_id not in revision_ids \
                or adapter.output_fixture_revision_id not in revision_ids:
            violations.append(_violation("GOLD-ADAPTER-FIXTURE-UNKNOWN", adapter.adapter_id, "adapter",
                                         "fixture_revision", adapter.adapter_revision_id,
                                         "registered input/output", "unknown",
                                         "Adapter endpoints must be separately registered fixtures."))
    del adapter_ids
    outcome = FixtureGateOutcome.REJECTED if violations else FixtureGateOutcome.ACCEPTED
    structured = tuple(sorted(violations, key=lambda item: (
        item.rule_id, item.fixture_or_requirement_id, item.field_path,
        item.expected_value, item.observed_value,
    )))
    payload = {
        "catalog_id": catalog.catalog_id,
        "requirement_set_id": GOLDEN_REQUIREMENT_SET.requirement_set_id,
        "fixture_gate_outcome": outcome.value,
        "violations": [{key: value for key, value in item.to_dict().items() if key != "explanation"}
                       for item in structured],
        "authorization_effect": "none",
    }
    return V1GoldenCatalogValidationResult(
        "sha256:" + hashlib.sha256(_json_bytes(payload)).hexdigest(), catalog.catalog_id,
        GOLDEN_REQUIREMENT_SET.requirement_set_id, outcome, structured,
        ("Contract fixture replay only; no scientific validity or activity authorization.",),
    )


def _canonical_legacy_json(value: object) -> bytes:
    """Preserve the closed JSON projection used only by named v1 readers."""

    return json.dumps(
        value,
        sort_keys=True,
        ensure_ascii=False,
        separators=(",", ":"),
        allow_nan=True,
    ).encode("utf-8")


def _decode_legacy_json(payload: bytes) -> object:
    return json.loads(payload.decode("utf-8"))


def _read_python_json_v1(payload: bytes) -> tuple[NativeReaderOutcome, bytes | None]:
    return NativeReaderOutcome.ACCEPTED, _canonical_legacy_json(_decode_legacy_json(payload))


def _read_mqtt_raw_hart_v1(payload: bytes) -> tuple[NativeReaderOutcome, bytes | None]:
    from parallel_truth_fingerprint.edge_nodes.common.mqtt_io import deserialize_payload

    decoded = deserialize_payload(payload.decode("utf-8"))
    return NativeReaderOutcome.ACCEPTED, _canonical_legacy_json(decoded.to_dict())


def _read_python_consensus_v1(payload: bytes) -> tuple[NativeReaderOutcome, bytes | None]:
    """Offline v1 Python consensus transaction boundary; never starts CometBFT."""

    decoded = _decode_legacy_json(payload)
    if not isinstance(decoded, dict):
        return NativeReaderOutcome.REJECTED, None
    return NativeReaderOutcome.ACCEPTED, _canonical_legacy_json(decoded)


def _read_go_consensus_v1(payload: bytes) -> tuple[NativeReaderOutcome, bytes | None]:
    """Offline Go wire-shape boundary; behavioral execution stays in Go tests."""

    decoded = _decode_legacy_json(payload)
    if not isinstance(decoded, dict):
        return NativeReaderOutcome.REJECTED, None
    return NativeReaderOutcome.ACCEPTED, _canonical_legacy_json(decoded)


def _read_persistence_json_v1(payload: bytes) -> tuple[NativeReaderOutcome, bytes | None]:
    decoded = _decode_legacy_json(payload)
    if not isinstance(decoded, dict):
        return NativeReaderOutcome.REJECTED, None
    return NativeReaderOutcome.ACCEPTED, _canonical_legacy_json(decoded)


def _read_manifest_json_v1(payload: bytes) -> tuple[NativeReaderOutcome, bytes | None]:
    decoded = _decode_legacy_json(payload)
    if not isinstance(decoded, dict):
        return NativeReaderOutcome.REJECTED, None
    return NativeReaderOutcome.ACCEPTED, _canonical_legacy_json(decoded)


def _read_detector_schema_v1(payload: bytes) -> tuple[NativeReaderOutcome, bytes | None]:
    decoded = _decode_legacy_json(payload)
    if not isinstance(decoded, dict):
        return NativeReaderOutcome.REJECTED, None
    features = decoded.get("features")
    expected = decoded.get("expected_features")
    if type(features) is not list or type(expected) is not list or features != expected:
        return NativeReaderOutcome.REJECTED, None
    return NativeReaderOutcome.ACCEPTED, _canonical_legacy_json(decoded)


_NATIVE_READERS: dict[str, Callable[[bytes], tuple[NativeReaderOutcome, bytes | None]]] = {
    "opaque.bytes.v1": lambda payload: (NativeReaderOutcome.ACCEPTED, payload),
    "python.json.v1": _read_python_json_v1,
    "mqtt.raw-hart.v1": _read_mqtt_raw_hart_v1,
    "python.consensus.v1": _read_python_consensus_v1,
    "go.consensus.v1": _read_go_consensus_v1,
    "persistence.json.v1": _read_persistence_json_v1,
    "manifest.json.v1": _read_manifest_json_v1,
    "detector.schema.v1": _read_detector_schema_v1,
}


def _compare_bytes_exact(payload: bytes, reader_output: bytes | None) -> bytes:
    del reader_output
    return payload


def _compare_json_type_strict(payload: bytes, reader_output: bytes | None) -> bytes:
    del payload
    if reader_output is None:
        raise ValueError("accepted semantic comparison requires reader output")
    # A second strict parse makes the comparison boundary explicit.  The compact
    # output preserves JSON scalar types and array order; it introduces no
    # defaults, field drops, coercions, or numerical tolerance.
    return _canonical_legacy_json(_decode_legacy_json(reader_output))


def _compare_detector_feature_order(payload: bytes, reader_output: bytes | None) -> bytes:
    del payload
    if reader_output is None:
        raise ValueError("accepted detector comparison requires reader output")
    decoded = _decode_legacy_json(reader_output)
    if not isinstance(decoded, dict) or type(decoded.get("features")) is not list:
        raise ValueError("detector output lacks an ordered feature list")
    return _canonical_legacy_json(decoded)


_COMPARATORS: dict[str, Callable[[bytes, bytes | None], bytes]] = {
    "bytes.exact.v1": _compare_bytes_exact,
    "json.type-strict.v1": _compare_json_type_strict,
    "detector.feature-order.v1": _compare_detector_feature_order,
    "opaque-key.exact.v1": _compare_bytes_exact,
}


def _native_reader(reader_id: str, payload: bytes) -> tuple[NativeReaderOutcome, bytes | None]:
    reader = _NATIVE_READERS.get(reader_id)
    if reader is None:
        return NativeReaderOutcome.REJECTED, None
    try:
        return reader(payload)
    except (UnicodeError, json.JSONDecodeError, TypeError, ValueError):
        return NativeReaderOutcome.REJECTED, None


def _comparison_output(
    comparator_id: str,
    payload: bytes,
    reader_output: bytes | None,
) -> bytes | None:
    comparator = _COMPARATORS.get(comparator_id)
    if comparator is None:
        return None
    try:
        return comparator(payload, reader_output)
    except (UnicodeError, json.JSONDecodeError, TypeError, ValueError):
        return None


def _replay_result(
    request: V1GoldenReplayRequest,
    fixture_revision_id: str | None,
    legacy: NativeReaderOutcome,
    gate: FixtureGateOutcome,
    output: bytes | None,
    violations: list[V1GoldenViolation],
) -> V1GoldenReplayResult:
    ordered = tuple(sorted(violations, key=lambda item: (
        item.rule_id, item.fixture_or_requirement_id, item.field_path,
        item.expected_value, item.observed_value,
    )))
    output_hash = "sha256:" + hashlib.sha256(output).hexdigest() if output is not None else None
    payload = {
        "request_id": request.request_id, "catalog_id": request.catalog_id,
        "fixture_revision_id": fixture_revision_id,
        "legacy_reader_outcome": legacy.value, "fixture_gate_outcome": gate.value,
        "observed_output_sha256": output_hash,
        "violations": [{key: value for key, value in item.to_dict().items() if key != "explanation"}
                       for item in ordered], "authorization_effect": "none",
    }
    return V1GoldenReplayResult(
        "sha256:" + hashlib.sha256(_json_bytes(payload)).hexdigest(), request.request_id,
        request.catalog_id, fixture_revision_id, legacy, gate, output_hash, ordered,
        ("Replay proves only registered v1 compatibility behavior.",),
    )


def replay_fixture(
    catalog: V1GoldenFixtureCatalog,
    request: V1GoldenReplayRequest,
    decoded_payload: bytes,
) -> V1GoldenReplayResult:
    violations: list[V1GoldenViolation] = []
    if request.request_id != replay_request_identity(request):
        violations.append(_violation("GOLD-REQUEST-HASH-MISMATCH", request.request_id,
                                     "replay-request", "request_id", request.request_id,
                                     replay_request_identity(request), request.request_id,
                                     "Replay request identity must bind route and content identities."))
        return _replay_result(request, request.fixture_revision_id,
                              NativeReaderOutcome.NOT_INVOKED, FixtureGateOutcome.REJECTED,
                              None, violations)
    if request.catalog_id != catalog.catalog_id or catalog.catalog_id != catalog_identity(catalog):
        violations.append(_violation("GOLD-CATALOG-HASH-MISMATCH", "catalog", "catalog",
                                     "catalog_id", request.catalog_id, catalog.catalog_id,
                                     request.catalog_id, "Replay requires the exact registered catalog."))
        return _replay_result(request, request.fixture_revision_id,
                              NativeReaderOutcome.NOT_INVOKED, FixtureGateOutcome.REJECTED,
                              None, violations)
    # A missing historical baseline is an explicitly retained provenance state.  It
    # must keep the fixture-gate outcome unverifiable, but it must not prevent the
    # bounded legacy reader from reproducing its declared behavior.  Every other
    # catalog violation is structural and blocks replay before bytes are consumed.
    catalog_validation = validate_catalog(catalog)
    structural_violations = [
        item for item in catalog_validation.violations
        if item.rule_id != "GOLD-BASELINE-UNAVAILABLE"
    ]
    if structural_violations:
        return _replay_result(
            request, request.fixture_revision_id, NativeReaderOutcome.NOT_INVOKED,
            FixtureGateOutcome.REJECTED, None, structural_violations,
        )
    matches = [item for item in catalog.entries if item.fixture_revision_id == request.fixture_revision_id]
    if len(matches) != 1:
        violations.append(_violation("GOLD-FIXTURE-UNKNOWN", request.fixture_revision_id,
                                     "unknown", "fixture_revision_id", request.fixture_revision_id,
                                     "one registered revision", len(matches),
                                     "Unregistered bytes are never inferred as v1."))
        return _replay_result(request, request.fixture_revision_id,
                              NativeReaderOutcome.NOT_INVOKED, FixtureGateOutcome.REJECTED,
                              None, violations)
    entry = matches[0]
    if request.adapter_revision_id is not None:
        adapters = [item for item in catalog.adapters
                    if item.adapter_revision_id == request.adapter_revision_id]
        if len(adapters) != 1 or adapters[0].input_fixture_revision_id != entry.fixture_revision_id:
            violations.append(_violation("GOLD-ADAPTER-INVALID", entry.fixture_id,
                                         entry.native_contract_id, "adapter_revision_id",
                                         request.adapter_revision_id, "registered exact adapter", "unknown",
                                         "Transformations require a separately registered exact adapter."))
            return _replay_result(request, entry.fixture_revision_id,
                                  NativeReaderOutcome.NOT_INVOKED, FixtureGateOutcome.REJECTED,
                                  None, violations)
    digest = "sha256:" + hashlib.sha256(decoded_payload).hexdigest()
    if len(decoded_payload) > MAX_FIXTURE_BYTES or digest != entry.decoded_sha256 \
            or request.supplied_decoded_sha256 != entry.decoded_sha256 \
            or request.payload_sha256 != entry.decoded_sha256:
        violations.append(_violation("GOLD-HASH-MISMATCH", entry.fixture_id,
                                     entry.native_contract_id, "decoded_sha256", digest,
                                     entry.decoded_sha256, digest,
                                     "Content identity is checked before selecting a reader."))
        return _replay_result(request, entry.fixture_revision_id,
                              NativeReaderOutcome.NOT_INVOKED, FixtureGateOutcome.REJECTED,
                              None, violations)
    if str(request.route) == ReplayRoute.EXPLICIT_ENVELOPE.value:
        if not request.envelope_id or str(entry.native_version_status) != NativeVersionStatus.EXPLICIT.value \
                or request.native_version != entry.native_version_token \
                or request.envelope_id != explicit_envelope_identity(entry):
            violations.append(_violation("GOLD-ENVELOPE-INVALID", entry.fixture_id,
                                         entry.native_contract_id, "envelope", request.envelope_id,
                                         entry.native_version_token, request.native_version,
                                         "Explicit envelope route binds version and payload hash."))
            return _replay_result(request, entry.fixture_revision_id,
                                  NativeReaderOutcome.NOT_INVOKED, FixtureGateOutcome.REJECTED,
                                  None, violations)
    elif str(request.route) != ReplayRoute.REGISTERED_FIXTURE.value:
        violations.append(_violation("GOLD-ROUTE-UNSUPPORTED", entry.fixture_id,
                                     entry.native_contract_id, "route", request.route,
                                     tuple(item.value for item in ReplayRoute), request.route,
                                     "Only two explicit replay routes exist."))
        return _replay_result(request, entry.fixture_revision_id,
                              NativeReaderOutcome.NOT_INVOKED, FixtureGateOutcome.REJECTED,
                              None, violations)
    legacy, reader_output = _native_reader(entry.reader_id, decoded_payload)
    output = _comparison_output(entry.comparator_id, decoded_payload, reader_output)
    if legacy == NativeReaderOutcome.ACCEPTED and output is None:
        violations.append(_violation("GOLD-COMPARATOR-FAILED", entry.fixture_id,
                                     entry.native_contract_id, "comparator_id", entry.comparator_id,
                                     "accepted closed comparator", "no comparison output",
                                     "The named semantic comparator could not produce a bounded output."))
    gate = FixtureGateOutcome(str(entry.expected_fixture_gate_outcome))
    if legacy != NativeReaderOutcome(str(entry.expected_legacy_reader_outcome)):
        violations.append(_violation("GOLD-LEGACY-OUTCOME-DRIFT", entry.fixture_id,
                                     entry.native_contract_id, "legacy_reader_outcome", legacy,
                                     entry.expected_legacy_reader_outcome, legacy,
                                     "Named legacy reader behavior drifted."))
        gate = FixtureGateOutcome.REJECTED
    if entry.expected_output_sha256 is not None:
        observed = "sha256:" + hashlib.sha256(output or b"").hexdigest()
        if observed != entry.expected_output_sha256:
            violations.append(_violation("GOLD-COMPARISON-DRIFT", entry.fixture_id,
                                         entry.native_contract_id, "expected_output_sha256", observed,
                                         entry.expected_output_sha256, observed,
                                         "Declared comparison output drifted."))
            gate = FixtureGateOutcome.REJECTED
    return _replay_result(request, entry.fixture_revision_id, legacy, gate, output, violations)


def validate_fixture_use(use: str) -> tuple[V1GoldenViolation, ...]:
    if use == "contract_fixture_replay":
        return ()
    if use in PROHIBITED_CONSUMER_USES or use != "contract_fixture_replay":
        return (_violation("GOLD-USE-PROHIBITED", "fixture-use-policy", "fixture",
                           "use", use, "contract_fixture_replay", use,
                           "Fixtures cannot enter scientific consumers or authorize activity."),)
    return ()


def validate_fixture_consumer_source(
    consumer_use: str, source_locator: str,
) -> tuple[V1GoldenViolation, ...]:
    """Reject a Story 9.5 fixture root at a scientific-consumer boundary.

    This narrow helper intentionally does not classify ordinary runtime object
    prefixes.  It only recognizes the immutable golden-fixture namespace so
    legacy dataset builders cannot accidentally treat the corpus as input data.
    """

    normalized = source_locator.replace("\\", "/")
    if "testdata/golden/v1" not in normalized:
        return ()
    return validate_fixture_use(consumer_use)
