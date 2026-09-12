"""Pure validation, deterministic encoding, and projections for SourceCatalog.v1."""

from __future__ import annotations

import hashlib
import json
import re
from dataclasses import fields
from datetime import date
from pathlib import Path
from typing import Callable, Iterable, Mapping
from urllib.parse import parse_qsl, urlsplit

from parallel_truth_fingerprint.contracts.semantic_vocabulary import SEMANTIC_VOCABULARY_VERSION
from parallel_truth_fingerprint.contracts.source_catalog import (
    SOURCE_CATALOG_SCHEMA_VERSION,
    AccessStatus,
    AuthorityRole,
    ClaimUse,
    Classification,
    ContentRecord,
    CopyRole,
    DateStatus,
    DiscrepancyRecord,
    IssuerRole,
    PeerReviewStatus,
    RelationRecord,
    RelationType,
    RetrievalRecord,
    RetrievalStatus,
    RightsStatus,
    SourceCatalog,
    SourceCatalogValidationResult,
    SourceCatalogViolation,
    SourceRecord,
    SourceRevision,
    SourceType,
    SourceUse,
    SourceUseStatus,
    VerificationStatus,
    RedistributionStatus,
)


SHA256_PATTERN = re.compile(r"^sha256:[0-9a-f]{64}$")
DATE_PATTERN = re.compile(r"^\d{4}-\d{2}-\d{2}$")
MUTABLE_SEGMENTS = frozenset({"latest", "main", "master", "head"})
LOCATOR_KINDS = frozenset({
    "document", "standard_clause", "repository", "dataset", "paper", "web_section",
})

STABLE_SOURCE_RULE_IDS = (
    "SRC-CONTEXT-PROMOTED",
    "SRC-DIGEST-INVALID",
    "SRC-DIRECT-AUTHORITY-INELIGIBLE",
    "SRC-ID-DUPLICATE",
    "SRC-IMMUTABLE-IDENTITY-MUTATED",
    "SRC-LOCAL-BYTES-MISMATCH",
    "SRC-LOCAL-METADATA-FABRICATED",
    "SRC-LOCAL-METADATA-INCOMPLETE",
    "SRC-LOCATOR-MUTABLE",
    "SRC-LOCATOR-UNSAFE",
    "SRC-METADATA-INCOMPLETE",
    "SRC-MIRROR-CONFLICT-UNRECORDED",
    "SRC-REFERENCE-UNRESOLVED",
    "SRC-RELATION-INVALID",
    "SRC-RIGHTS-UNRESOLVED",
    "SRC-SCHEMA-UNSUPPORTED",
    "SRC-TOKEN-INVALID",
    "SRC-USE-INAPPLICABLE",
)


def _is_enum_token(value: object, enum_type: type) -> bool:
    return _token(value) in {item.value for item in enum_type}


def _check_tokens(
    violations: list[SourceCatalogViolation],
    record_id: str,
    fields: tuple[tuple[str, object, type], ...],
) -> None:
    invalid = [(name, value) for name, value, enum_type in fields if not _is_enum_token(value, enum_type)]
    if invalid:
        violations.append(_violation(
            "SRC-TOKEN-INVALID", record_id, (name for name, _ in invalid),
            (value for _, value in invalid),
            "Serialized vocabulary tokens are closed for SourceCatalog.v1; change the schema version to add meanings.",
        ))


def _token(value: object) -> str:
    return str(value.value if hasattr(value, "value") else value)


def _nonblank(value: object) -> bool:
    return isinstance(value, str) and bool(value.strip()) and value == value.strip()


def _valid_date_pair(date_value: object, status: object) -> bool:
    if _token(status) == DateStatus.KNOWN.value:
        if not isinstance(date_value, str) or DATE_PATTERN.fullmatch(date_value) is None:
            return False
        try:
            date.fromisoformat(date_value)
        except ValueError:
            return False
        return True
    return date_value is None


def _violation(
    rule_id: str,
    record_id: object,
    fields: Iterable[str],
    tokens: Iterable[object],
    explanation: str,
) -> SourceCatalogViolation:
    return SourceCatalogViolation(
        rule_id=rule_id,
        record_id=_token(record_id),
        fields=tuple(sorted(set(fields))),
        offending_tokens=tuple(sorted({_token(item) for item in tokens if item is not None})),
        explanation=explanation,
    )


def _result(violations: Iterable[SourceCatalogViolation], *, supported: bool = True) -> SourceCatalogValidationResult:
    ordered = tuple(sorted(violations, key=lambda item: (item.rule_id, item.record_id, item.fields)))
    return SourceCatalogValidationResult(supported, supported and not ordered, ordered)


def _duplicate_ids(records: Iterable[object], field_name: str) -> set[str]:
    seen: set[str] = set()
    duplicate: set[str] = set()
    for record in records:
        identifier = str(getattr(record, field_name))
        if identifier in seen:
            duplicate.add(identifier)
        seen.add(identifier)
    return duplicate


def _mutable_locator(locator: object) -> bool:
    if not _nonblank(locator):
        return True
    parsed = urlsplit(locator)
    segments = {part.lower() for part in parsed.path.split("/") if part}
    query_tokens = [str(item).lower()
                    for pair in parse_qsl(parsed.query, keep_blank_values=True) for item in pair]
    for token in (*query_tokens, parsed.fragment.lower()):
        segments.update(part for part in re.split(r"[/\s:]+", token) if part)
    if segments.intersection(MUTABLE_SEGMENTS):
        return True
    if parsed.netloc.lower() == "github.com":
        parts = [part for part in parsed.path.split("/") if part]
        return len(parts) <= 2
    return False


def _valid_remote_locator(locator: object, *, allow_unavailable: bool = False) -> bool:
    if not _nonblank(locator):
        return False
    if str(locator).startswith("unavailable:"):
        return allow_unavailable
    parsed = urlsplit(locator)
    return parsed.scheme.lower() in {"http", "https"} and bool(parsed.netloc)


def _valid_exact_locator(kind: object, locator: object) -> bool:
    if kind not in LOCATOR_KINDS or not _nonblank(locator):
        return False
    value = str(locator)
    lowered = value.lower()
    page = re.search(r"\b(?:p|pp|page|pages)\.?\s*\d+", lowered) is not None
    if kind == "document":
        selectors = ("table", "section", "figure", "parameter", "option", "scaling", "specification")
        return page and (any(token in lowered for token in selectors) or len(re.findall(
            r"\b(?:p|pp|page|pages)\.?\s*\d+", lowered
        )) > 1 or re.search(r"\b(?:p|pp|page|pages)\.?\s*\d+\s*[-–]\s*\d+", lowered) is not None)
    if kind == "standard_clause":
        return any(token in lowered for token in ("clause", "section", "field", "table", "figure"))
    if kind == "repository":
        return re.search(r"\b[0-9a-f]{40}\b", lowered) is not None and "/" in value
    if kind == "dataset":
        return any(token in lowered for token in ("release", "version")) and any(
            token in lowered for token in ("file", "role", "sha256", "hash")
        )
    if kind == "paper":
        return ("doi" in lowered or "version" in lowered) and (
            page or any(token in lowered for token in ("section", "table", "figure"))
        )
    return len(value) >= 8 and (";" in value or "#" in value or "/" in value)


def _safe_local_path(
    root: Path,
    locator: object,
    resolver: Callable[[Path], Path] | None = None,
) -> Path | None:
    if not _nonblank(locator):
        return None
    relative = Path(locator)
    if relative.is_absolute() or any(part in {"", ".", ".."} for part in relative.parts):
        return None
    resolve = resolver or (lambda path: path.resolve(strict=False))
    resolved_root = resolve(root)
    resolved = resolve(resolved_root / relative)
    try:
        resolved.relative_to(resolved_root)
    except ValueError:
        return None
    return resolved


def _verify_file(path: Path, content: ContentRecord) -> bool:
    try:
        before = path.stat(follow_symlinks=False)
        if not path.is_file() or path.is_symlink():
            return False
        digest = hashlib.sha256()
        size = 0
        with path.open("rb") as stream:
            for chunk in iter(lambda: stream.read(1024 * 1024), b""):
                size += len(chunk)
                digest.update(chunk)
        after = path.stat(follow_symlinks=False)
    except OSError:
        return False
    signature_before = (before.st_dev, before.st_ino, before.st_size, before.st_mtime_ns)
    signature_after = (after.st_dev, after.st_ino, after.st_size, after.st_mtime_ns)
    return (
        signature_before == signature_after
        and size == content.byte_size
        and "sha256:" + digest.hexdigest() == content.sha256
    )


def validate_source_catalog(
    catalog: SourceCatalog,
    *,
    documents_root: Path | None = None,
    path_resolver: Callable[[Path], Path] | None = None,
    prior_catalog: SourceCatalog | None = None,
) -> SourceCatalogValidationResult:
    """Validate catalog metadata and optionally verify declared local opaque bytes."""

    violations: list[SourceCatalogViolation] = []
    supported = (
        catalog.schema_version == SOURCE_CATALOG_SCHEMA_VERSION
        and catalog.semantic_vocabulary_version == SEMANTIC_VOCABULARY_VERSION
    )
    if not supported:
        violations.append(_violation(
            "SRC-SCHEMA-UNSUPPORTED", "catalog", ("schema_version", "semantic_vocabulary_version"),
            (catalog.schema_version, catalog.semantic_vocabulary_version),
            "Use the exact SourceCatalog.v1 and semantic-vocabulary.v1 versions.",
        ))

    collections = (
        (catalog.sources, "source_id"), (catalog.revisions, "source_revision_id"),
        (catalog.contents, "content_id"), (catalog.retrievals, "retrieval_id"),
        (catalog.uses, "use_id"), (catalog.relations, "relation_id"),
        (catalog.discrepancies, "discrepancy_id"),
    )
    for records, field_name in collections:
        for identifier in _duplicate_ids(records, field_name):
            violations.append(_violation(
                "SRC-ID-DUPLICATE", identifier, (field_name,), (identifier,),
                "Stable IDs are unique and immutable within one catalog.",
            ))

    if prior_catalog is not None:
        identity_sets = (
            (prior_catalog.sources, catalog.sources, "source_id"),
            (prior_catalog.revisions, catalog.revisions, "source_revision_id"),
            (prior_catalog.contents, catalog.contents, "content_id"),
            (prior_catalog.retrievals, catalog.retrievals, "retrieval_id"),
            (prior_catalog.uses, catalog.uses, "use_id"),
            (prior_catalog.relations, catalog.relations, "relation_id"),
            (prior_catalog.discrepancies, catalog.discrepancies, "discrepancy_id"),
        )
        for previous_records, current_records, id_field in identity_sets:
            previous = {getattr(item, id_field): item for item in previous_records}
            current = {getattr(item, id_field): item for item in current_records}
            for identifier in previous.keys() - current.keys():
                violations.append(_violation(
                    "SRC-IMMUTABLE-IDENTITY-MUTATED", identifier, (id_field,), (identifier,),
                    "An existing stable identity was removed; the catalog is append-only.",
                ))
            for identifier in previous.keys() & current.keys():
                if previous[identifier].to_dict() != current[identifier].to_dict():
                    violations.append(_violation(
                        "SRC-IMMUTABLE-IDENTITY-MUTATED", identifier, (id_field,), (identifier,),
                        "An existing stable identity changed; create a new revision/content/retrieval/use identity.",
                    ))

    sources = {item.source_id: item for item in catalog.sources}
    revisions = {item.source_revision_id: item for item in catalog.revisions}
    contents = {item.content_id: item for item in catalog.contents}
    retrievals = {item.retrieval_id: item for item in catalog.retrievals}
    all_ids = set(sources) | set(revisions) | set(contents) | {
        item.retrieval_id for item in catalog.retrievals
    }

    for source in catalog.sources:
        _check_tokens(violations, source.source_id, (
            ("publication_date_status", source.publication_date_status, DateStatus),
            ("version_status", source.version_status, DateStatus),
            ("source_type", source.source_type, SourceType),
            ("issuer_role", source.issuer_role, IssuerRole),
            ("authority_role", source.authority_role, AuthorityRole),
            ("peer_review_status", source.peer_review_status, PeerReviewStatus),
            *(("classifications", item, Classification) for item in source.classifications),
        ))
        missing = [name for name in (
            "source_id", "title", "official_url", "applicable_scope"
        ) if not _nonblank(getattr(source, name))]
        if (
            not source.organization_authors or not all(_nonblank(item) for item in source.organization_authors)
            or not source.classifications or not source.limitations
            or not all(_nonblank(item) for item in source.limitations)
        ):
            missing.extend(("organization_authors", "classifications", "limitations"))
        version_known = _token(source.version_status) == "known"
        if not _valid_date_pair(source.publication_date, source.publication_date_status):
            missing.append("publication_date")
        if version_known != _nonblank(source.exact_version):
            missing.append("exact_version")
        if missing:
            violations.append(_violation(
                "SRC-METADATA-INCOMPLETE", source.source_id, missing, (),
                "Required metadata and explicit unknown statuses must be preserved without guesses.",
            ))
        if not _valid_remote_locator(
            source.official_url,
            allow_unavailable=_token(source.version_status) == DateStatus.UNKNOWN_LEGACY.value,
        ):
            violations.append(_violation(
                "SRC-LOCATOR-UNSAFE", source.source_id, ("official_url",),
                (source.official_url,),
                "Official source locations must be absolute HTTP(S) URLs or an explicit unavailable legacy sentinel.",
            ))

        source_revisions = [item for item in catalog.revisions if item.source_id == source.source_id]
        if _token(source.version_status) == DateStatus.KNOWN.value and not any(
            item.exact_version == source.exact_version for item in source_revisions
        ):
            violations.append(_violation(
                "SRC-METADATA-INCOMPLETE", source.source_id,
                ("exact_version", "version_status"), (source.exact_version,),
                "Immutable logical-source baseline metadata must match at least one exact revision.",
            ))
        if _token(source.publication_date_status) == DateStatus.KNOWN.value and not any(
            item.release_date == source.publication_date for item in source_revisions
        ):
            violations.append(_violation(
                "SRC-METADATA-INCOMPLETE", source.source_id,
                ("publication_date", "publication_date_status"), (source.publication_date,),
                "Immutable logical-source baseline date must match at least one exact revision.",
            ))

    for revision in catalog.revisions:
        _check_tokens(violations, revision.source_revision_id, (
            ("version_status", revision.version_status, DateStatus),
            ("release_date_status", revision.release_date_status, DateStatus),
        ))
        if type(revision.mutable_location) is not bool:
            violations.append(_violation(
                "SRC-METADATA-INCOMPLETE", revision.source_revision_id,
                ("mutable_location",), (revision.mutable_location,),
                "Mutable-location state must be an explicit boolean.",
            ))
        if revision.source_id not in sources:
            violations.append(_violation(
                "SRC-REFERENCE-UNRESOLVED", revision.source_revision_id, ("source_id",),
                (revision.source_id,), "The logical source reference must resolve.",
            ))
        version_known = _token(revision.version_status) == "known"
        if version_known != _nonblank(revision.exact_version):
            violations.append(_violation(
                "SRC-METADATA-INCOMPLETE", revision.source_revision_id,
                ("exact_version", "version_status"), (revision.exact_version, revision.version_status),
                "Exact versions and unknown-version statuses cannot contradict each other.",
            ))
        if not _valid_date_pair(revision.release_date, revision.release_date_status):
            violations.append(_violation(
                "SRC-METADATA-INCOMPLETE", revision.source_revision_id,
                ("release_date", "release_date_status"), (revision.release_date, revision.release_date_status),
                "Release dates are nullable ISO-8601 values paired with an explicit date status.",
            ))
        if (
            _token(revision.release_date_status) in {
                DateStatus.UNKNOWN_LEGACY.value, DateStatus.NOT_STATED.value
            }
            and not revision.limitations
        ):
            violations.append(_violation(
                "SRC-METADATA-INCOMPLETE", revision.source_revision_id,
                ("release_date_status", "limitations"), (revision.release_date_status,),
                "An absent release date requires an explicit limitation.",
            ))
        has_verified_content_identity = any(
            content.source_revision_id == revision.source_revision_id for content in catalog.contents
        )
        if (
            revision.immutable_locator and _mutable_locator(revision.immutable_locator)
            and not revision.mutable_location and not has_verified_content_identity
        ):
            violations.append(_violation(
                "SRC-LOCATOR-MUTABLE", revision.source_revision_id,
                ("immutable_locator", "mutable_location"), (revision.immutable_locator,),
                "Mutable branches, living pages, and repository roots cannot claim immutable identity.",
            ))
        if revision.immutable_locator is not None and not _valid_remote_locator(revision.immutable_locator):
            violations.append(_violation(
                "SRC-LOCATOR-UNSAFE", revision.source_revision_id, ("immutable_locator",),
                (revision.immutable_locator,), "Immutable revision locators must be absolute HTTP(S) URLs.",
            ))
        if (not version_known or revision.mutable_location) and not revision.limitations:
            violations.append(_violation(
                "SRC-METADATA-INCOMPLETE", revision.source_revision_id, ("limitations",), (),
                "Unknown or mutable revision evidence requires an explicit limitation.",
            ))

    filenames: dict[str, str] = {}
    for content in catalog.contents:
        if content.source_revision_id not in revisions:
            violations.append(_violation(
                "SRC-REFERENCE-UNRESOLVED", content.content_id, ("source_revision_id",),
                (content.source_revision_id,), "Content must resolve to one exact source revision.",
            ))
        if (
            SHA256_PATTERN.fullmatch(content.content_id) is None
            or SHA256_PATTERN.fullmatch(content.sha256) is None
            or content.content_id != content.sha256
            or type(content.byte_size) is not int
            or content.byte_size < 0
        ):
            violations.append(_violation(
                "SRC-DIGEST-INVALID", content.content_id, ("content_id", "sha256", "byte_size"),
                (content.content_id, content.sha256),
                "Content identity is the exact lowercase SHA-256 digest with a nonnegative byte size.",
            ))
        if (
            not _nonblank(content.filename) or Path(content.filename).name != content.filename
            or not _nonblank(content.media_type)
        ):
            violations.append(_violation(
                "SRC-LOCATOR-UNSAFE", content.content_id, ("filename", "media_type"),
                (content.filename, content.media_type),
                "Content filenames are single safe archive names and require a media type.",
            ))
        previous_content = filenames.get(content.filename)
        if previous_content is not None and previous_content != content.content_id:
            violations.append(_violation(
                "SRC-RELATION-INVALID", content.content_id, ("filename",), (content.filename,),
                "One archive filename cannot identify different content byte streams.",
            ))
        filenames[content.filename] = content.content_id

    for retrieval in catalog.retrievals:
        _check_tokens(violations, retrieval.retrieval_id, (
            ("copy_role", retrieval.copy_role, CopyRole),
            ("retrieval_status", retrieval.retrieval_status, RetrievalStatus),
            ("verification_status", retrieval.verification_status, VerificationStatus),
            ("access_status", retrieval.access_status, AccessStatus),
            ("rights_status", retrieval.rights_status, RightsStatus),
            ("redistribution_status", retrieval.redistribution_status, RedistributionStatus),
            ("retrieval_date_status", retrieval.retrieval_date_status, DateStatus),
        ))
        if retrieval.source_revision_id not in revisions or (
            retrieval.content_id is not None and retrieval.content_id not in contents
        ):
            violations.append(_violation(
                "SRC-REFERENCE-UNRESOLVED", retrieval.retrieval_id,
                ("source_revision_id", "content_id"),
                (retrieval.source_revision_id, retrieval.content_id),
                "Retrieval references must resolve without guessing a copy or revision.",
            ))
        elif retrieval.content_id is not None and (
            contents[retrieval.content_id].source_revision_id != retrieval.source_revision_id
        ):
            violations.append(_violation(
                "SRC-REFERENCE-UNRESOLVED", retrieval.retrieval_id,
                ("source_revision_id", "content_id"),
                (retrieval.source_revision_id, retrieval.content_id),
                "Retrieved content must belong to the same exact source revision.",
            ))
        is_local = _token(retrieval.retrieval_status) == RetrievalStatus.LOCAL.value
        retrieval_date_known = (
            _token(retrieval.retrieval_date_status) == "known"
            and _valid_date_pair(retrieval.retrieval_date, retrieval.retrieval_date_status)
        )
        retrieval_date_unknown_legacy = (
            retrieval.retrieval_date is None
            and _token(retrieval.retrieval_date_status) == "unknown_legacy"
            and bool(retrieval.limitations)
        )
        local_complete = (
            retrieval.content_id is not None and _nonblank(retrieval.local_locator)
            and (retrieval_date_known or retrieval_date_unknown_legacy)
            and _nonblank(retrieval.verifier)
        )
        required_retrieval_fields = [name for name in (
            "remote_locator", "permitted_project_use", "storage_policy"
        ) if not _nonblank(getattr(retrieval, name))]
        if required_retrieval_fields:
            violations.append(_violation(
                "SRC-METADATA-INCOMPLETE", retrieval.retrieval_id,
                required_retrieval_fields, (),
                "Retrieval provenance, permitted use, and storage policy are mandatory and independent.",
            ))
        if not _valid_remote_locator(
            retrieval.remote_locator,
            allow_unavailable=_token(retrieval.retrieval_status) == RetrievalStatus.UNAVAILABLE.value,
        ):
            violations.append(_violation(
                "SRC-LOCATOR-UNSAFE", retrieval.retrieval_id, ("remote_locator",),
                (retrieval.remote_locator,),
                "Remote provenance locators must be absolute HTTP(S) locations.",
            ))
        if not _valid_date_pair(retrieval.retrieval_date, retrieval.retrieval_date_status):
            violations.append(_violation(
                "SRC-METADATA-INCOMPLETE", retrieval.retrieval_id,
                ("retrieval_date", "retrieval_date_status"),
                (retrieval.retrieval_date, retrieval.retrieval_date_status),
                "Retrieval dates are nullable ISO-8601 values paired with an explicit date status.",
            ))
        if (
            _token(retrieval.retrieval_date_status) in {
                DateStatus.UNKNOWN_LEGACY.value, DateStatus.NOT_STATED.value
            }
            and not retrieval.limitations
        ):
            violations.append(_violation(
                "SRC-METADATA-INCOMPLETE", retrieval.retrieval_id,
                ("retrieval_date_status", "limitations"), (retrieval.retrieval_date_status,),
                "An absent historical retrieval date requires an explicit limitation.",
            ))
        restricted = (
            _token(retrieval.retrieval_status) == RetrievalStatus.RESTRICTED.value
            or _token(retrieval.access_status) in {AccessStatus.RESTRICTED.value, AccessStatus.PAYWALLED.value}
        )
        if restricted and (
            not _nonblank(retrieval.verifier) or not retrieval_date_known or not retrieval.limitations
            or _token(retrieval.retrieval_status) != RetrievalStatus.RESTRICTED.value
            or _token(retrieval.access_status) not in {
                AccessStatus.RESTRICTED.value, AccessStatus.PAYWALLED.value
            }
        ):
            violations.append(_violation(
                "SRC-METADATA-INCOMPLETE", retrieval.retrieval_id,
                ("retrieval_status", "access_status", "retrieval_date", "verifier", "limitations"), (),
                "Restricted/paywalled evidence requires a dated lawful observation, verifier, and limitation.",
            ))
        if is_local and not local_complete:
            violations.append(_violation(
                "SRC-LOCAL-METADATA-INCOMPLETE", retrieval.retrieval_id,
                ("content_id", "local_locator", "retrieval_date", "verifier"), (),
                "Local claims require content, locator, historical retrieval date, and verifier.",
            ))
        if (
            is_local and retrieval.content_id in contents
            and retrieval.local_locator is not None
            and Path(retrieval.local_locator).name != contents[retrieval.content_id].filename
        ):
            violations.append(_violation(
                "SRC-LOCAL-METADATA-INCOMPLETE", retrieval.retrieval_id,
                ("local_locator", "content_id", "filename"),
                (retrieval.local_locator, contents[retrieval.content_id].filename),
                "The local locator filename must match its exact content record.",
            ))
        if not is_local and (retrieval.content_id is not None or retrieval.local_locator is not None):
            violations.append(_violation(
                "SRC-LOCAL-METADATA-FABRICATED", retrieval.retrieval_id,
                ("retrieval_status", "content_id", "local_locator"), (),
                "Byte-absent retrieval states cannot carry fabricated local metadata.",
            ))
        if retrieval.local_locator is not None:
            root = documents_root or Path(".")
            safe_path = _safe_local_path(root, retrieval.local_locator, path_resolver)
            if safe_path is None:
                violations.append(_violation(
                    "SRC-LOCATOR-UNSAFE", retrieval.retrieval_id, ("local_locator",),
                    (retrieval.local_locator,), "Local locators must stay beneath the supplied documents root.",
                ))
            elif documents_root is not None and retrieval.content_id in contents and not _verify_file(
                safe_path, contents[retrieval.content_id]
            ):
                violations.append(_violation(
                    "SRC-LOCAL-BYTES-MISMATCH", retrieval.retrieval_id,
                    ("local_locator", "content_id"), (retrieval.local_locator, retrieval.content_id),
                    "The opaque local byte stream is absent, unstable, or differs in size/digest.",
                ))
        if (
            _token(retrieval.redistribution_status) == RedistributionStatus.ALLOWED.value
            and (
                _token(retrieval.rights_status) != RightsStatus.DECLARED.value
                or not _valid_remote_locator(retrieval.license_terms_locator)
            )
        ):
            violations.append(_violation(
                "SRC-RIGHTS-UNRESOLVED", retrieval.retrieval_id,
                ("rights_status", "redistribution_status"),
                (retrieval.rights_status, retrieval.redistribution_status),
                "Unknown or unstated rights cannot support an allowed-redistribution claim.",
            ))

    for use in catalog.uses:
        _check_tokens(violations, use.use_id, (
            ("claim_use", use.claim_use, ClaimUse),
            ("status", use.status, SourceUseStatus),
        ))
        if type(use.responsible_authority) is not bool:
            violations.append(_violation(
                "SRC-METADATA-INCOMPLETE", use.use_id,
                ("responsible_authority",), (use.responsible_authority,),
                "Responsible-authority state must be an explicit boolean.",
            ))
        source = sources.get(use.source_id)
        revision = revisions.get(use.source_revision_id or "")
        if source is None or (use.source_revision_id is not None and revision is None):
            violations.append(_violation(
                "SRC-REFERENCE-UNRESOLVED", use.use_id, ("source_id", "source_revision_id"),
                (use.source_id, use.source_revision_id), "Every source use must resolve its declared identities.",
            ))
            continue
        if revision is not None and revision.source_id != use.source_id:
            violations.append(_violation(
                "SRC-REFERENCE-UNRESOLVED", use.use_id, ("source_id", "source_revision_id"),
                (use.source_id, use.source_revision_id),
                "A bounded use must bind a revision belonging to its declared logical source.",
            ))
        located = _token(use.status) == SourceUseStatus.LOCATED.value
        if located and (
            not _nonblank(use.locator_kind) or use.locator_kind not in LOCATOR_KINDS
            or not _nonblank(use.supported_scope) or not use.excluded_scope
            or not _nonblank(use.applicable_variant) or not _nonblank(use.prototype_component)
            or not _nonblank(use.research_question) or not _nonblank(use.evidence_track)
            or not _nonblank(use.final_package_element) or not _nonblank(use.transferability_rationale)
        ):
            violations.append(_violation(
                "SRC-USE-INAPPLICABLE", use.use_id,
                ("locator_kind", "supported_scope", "excluded_scope", "applicable_variant",
                 "prototype_component", "research_question", "evidence_track",
                 "final_package_element", "transferability_rationale"), (),
                "Located uses require a typed locator and complete bounded applicability fields.",
            ))
        if located and (
            revision is None or not _nonblank(use.exact_locator)
            or _token(revision.version_status) != "known" or revision.mutable_location
            or (
                revision.immutable_locator is None
                and not any(item.source_revision_id == revision.source_revision_id for item in catalog.contents)
            )
            or not any(item.source_revision_id == revision.source_revision_id for item in catalog.retrievals)
        ):
            violations.append(_violation(
                "SRC-DIRECT-AUTHORITY-INELIGIBLE", use.use_id,
                ("source_revision_id", "exact_locator", "status"), (),
                "Located/formal use requires one exact immutable revision and typed exact locator.",
            ))
        if located and not _valid_exact_locator(use.locator_kind, use.exact_locator):
            violations.append(_violation(
                "SRC-USE-INAPPLICABLE", use.use_id, ("locator_kind", "exact_locator"),
                (use.locator_kind, use.exact_locator),
                "Exact locators must carry the medium-specific coordinates required by SourceCatalog.v1.",
            ))
        if not located and not use.limitations:
            violations.append(_violation(
                "SRC-USE-INAPPLICABLE", use.use_id, ("status", "limitations"), (use.status,),
                "Unresolved, contextual, or inapplicable uses retain their explicit limitation.",
            ))
        if use.responsible_authority and source is not None and _token(source.authority_role) in {
            AuthorityRole.CONTEXTUAL_ONLY.value,
            AuthorityRole.SECONDARY_ONLY.value,
            AuthorityRole.PRIMARY_CONTEXT.value,
        }:
            violations.append(_violation(
                "SRC-CONTEXT-PROMOTED", use.use_id,
                ("responsible_authority", "authority_role", "claim_use"),
                (source.authority_role, use.claim_use),
                "Contextual, scholarly, or secondary evidence cannot become responsible direct authority.",
            ))
        if (
            use.responsible_authority and _token(use.claim_use) == ClaimUse.DIRECT_VALUE.value
            and source is not None and _token(source.source_type) in {
                SourceType.SCHOLARLY_PAPER.value,
                SourceType.SECONDARY_REFERENCE.value,
                SourceType.GOVERNMENT_GUIDANCE.value,
                SourceType.TOOL_DOCUMENTATION.value,
            }
        ):
            violations.append(_violation(
                "SRC-CONTEXT-PROMOTED", use.use_id,
                ("source_type", "claim_use", "responsible_authority"),
                (source.source_type, use.claim_use),
                "These source types may support their bounded methods/context, not project direct-value authority.",
            ))
        if located and _token(use.claim_use) == "direct_value" and not use.responsible_authority:
            violations.append(_violation(
                "SRC-DIRECT-AUTHORITY-INELIGIBLE", use.use_id,
                ("claim_use", "responsible_authority"), (use.claim_use,),
                "A located externally asserted direct value requires responsible applicable authority.",
            ))

        if located and _token(use.claim_use) == ClaimUse.DIRECT_VALUE.value and revision is not None:
            observations = [item for item in catalog.retrievals
                            if item.source_revision_id == revision.source_revision_id]
            evidence_observed = any(
                (
                    _token(item.retrieval_status) == RetrievalStatus.LOCAL.value
                    and _token(item.verification_status) == VerificationStatus.VERIFIED.value
                )
                or (
                    _token(item.retrieval_status) == RetrievalStatus.RESTRICTED.value
                    and _nonblank(item.verifier)
                    and _token(item.retrieval_date_status) == DateStatus.KNOWN.value
                )
                for item in observations
            )
            if not evidence_observed:
                violations.append(_violation(
                    "SRC-DIRECT-AUTHORITY-INELIGIBLE", use.use_id,
                    ("source_revision_id", "claim_use"), (use.source_revision_id,),
                    "Direct values require verified local bytes or a dated lawful restricted-source observation.",
                ))

    edge_keys: set[tuple[str, str, str]] = set()
    conflict_pairs: set[frozenset[str]] = set()
    for discrepancy in catalog.discrepancies:
        pair = frozenset((discrepancy.source_record_id, discrepancy.target_record_id))
        valid_discrepancy = (
            discrepancy.source_record_id != discrepancy.target_record_id
            and discrepancy.source_record_id in all_ids
            and discrepancy.target_record_id in all_ids
            and _nonblank(discrepancy.discrepancy_kind)
            and discrepancy.status in {"open", "resolved"}
            and _nonblank(discrepancy.limitation)
        )
        if not valid_discrepancy:
            violations.append(_violation(
                "SRC-RELATION-INVALID", discrepancy.discrepancy_id,
                ("discrepancy_kind", "source_record_id", "target_record_id", "status", "limitation"),
                (discrepancy.source_record_id, discrepancy.target_record_id, discrepancy.status),
                "Discrepancies require distinct resolved endpoints, kind, status, and explicit limitation.",
            ))
        else:
            conflict_pairs.add(pair)

    def content_ids_for(record_id: str) -> set[str]:
        if record_id in contents:
            return {record_id}
        if record_id in retrievals:
            content_id = retrievals[record_id].content_id
            return {content_id} if content_id is not None else set()
        if record_id in revisions:
            return {item.content_id for item in catalog.contents
                    if item.source_revision_id == record_id}
        if record_id in sources:
            source_revision_ids = {item.source_revision_id for item in catalog.revisions
                                   if item.source_id == record_id}
            return {item.content_id for item in catalog.contents
                    if item.source_revision_id in source_revision_ids}
        return set()

    for relation in catalog.relations:
        _check_tokens(violations, relation.relation_id, (
            ("relation_type", relation.relation_type, RelationType),
        ))
        edge = (_token(relation.relation_type), relation.source_record_id, relation.target_record_id)
        invalid = (
            relation.source_record_id == relation.target_record_id
            or edge in edge_keys
            or relation.source_record_id not in all_ids
            or relation.target_record_id not in all_ids
        )
        if _token(relation.relation_type) == RelationType.BYTE_IDENTICAL.value:
            invalid = invalid or (
                relation.source_record_id not in retrievals
                or relation.target_record_id not in retrievals
                or retrievals[relation.source_record_id].content_id is None
                or retrievals[relation.source_record_id].content_id
                != retrievals[relation.target_record_id].content_id
            )
        if invalid:
            violations.append(_violation(
                "SRC-RELATION-INVALID", relation.relation_id,
                ("relation_type", "source_record_id", "target_record_id"), edge,
                "Relations resolve distinct records; byte-identical edges require equal verified hashes.",
            ))
        if (
            _token(relation.relation_type) == RelationType.CONFLICTS_WITH.value
            and frozenset((relation.source_record_id, relation.target_record_id)) not in conflict_pairs
        ):
            violations.append(_violation(
                "SRC-MIRROR-CONFLICT-UNRECORDED", relation.relation_id,
                ("source_record_id", "target_record_id"), edge,
                "A conflicting mirror/version must retain an explicit unresolved discrepancy.",
            ))
        if _token(relation.relation_type) == RelationType.MIRROR_OF.value:
            source_content = content_ids_for(relation.source_record_id)
            target_content = content_ids_for(relation.target_record_id)
            if (
                source_content and target_content and source_content != target_content
                and frozenset((relation.source_record_id, relation.target_record_id)) not in conflict_pairs
            ):
                violations.append(_violation(
                    "SRC-MIRROR-CONFLICT-UNRECORDED", relation.relation_id,
                    ("source_record_id", "target_record_id"),
                    (relation.source_record_id, relation.target_record_id),
                    "Mirror records with different observed byte identities require an explicit discrepancy.",
                ))
        edge_keys.add(edge)

    return _result(violations, supported=supported)


def _reject_floats(value: object) -> None:
    if isinstance(value, float):
        raise ValueError("floats are not permitted in SourceCatalog.v1 identity data")
    if isinstance(value, Mapping):
        for child in value.values():
            _reject_floats(child)
    elif isinstance(value, (list, tuple)):
        for child in value:
            _reject_floats(child)


def canonical_catalog_bytes(catalog: SourceCatalog) -> bytes:
    payload = catalog.to_dict()
    _reject_floats(payload)
    return (json.dumps(
        payload, sort_keys=True, ensure_ascii=False, separators=(",", ":"),
        allow_nan=False,
    ) + "\n").encode("utf-8")


def load_source_catalog(payload: bytes | str) -> SourceCatalog:
    def reject_constant(token: str) -> None:
        raise ValueError(f"non-finite JSON number is not permitted: {token}")

    raw = json.loads(payload, parse_constant=reject_constant)
    _reject_floats(raw)
    if not isinstance(raw, dict) or raw.get("authorization_effect") != "none":
        raise ValueError("invalid source catalog envelope")
    expected = {
        "schema_version", "semantic_vocabulary_version", "sources", "revisions", "contents",
        "retrievals", "uses", "relations", "discrepancies", "authorization_effect",
    }
    if set(raw) != expected:
        raise ValueError("unknown or missing source catalog fields")

    def records(name: str, record_type: type) -> tuple[object, ...]:
        values = raw[name]
        if not isinstance(values, list):
            raise ValueError(f"{name} must be an array")
        expected_fields = {item.name for item in fields(record_type) if item.init}
        loaded: list[object] = []
        for index, item in enumerate(values):
            if not isinstance(item, dict) or set(item) != expected_fields:
                raise ValueError(f"{name}[{index}] has unknown or missing fields")
            try:
                loaded.append(record_type(**item))
            except (TypeError, ValueError) as exc:
                raise ValueError(f"{name}[{index}] is malformed: {exc}") from exc
        return tuple(loaded)

    return SourceCatalog(
        schema_version=raw["schema_version"],
        semantic_vocabulary_version=raw["semantic_vocabulary_version"],
        sources=records("sources", SourceRecord),
        revisions=records("revisions", SourceRevision),
        contents=records("contents", ContentRecord),
        retrievals=records("retrievals", RetrievalRecord),
        uses=records("uses", SourceUse),
        relations=records("relations", RelationRecord),
        discrepancies=records("discrepancies", DiscrepancyRecord),
    )


def human_index_projection(catalog: SourceCatalog) -> str:
    sources = {item.source_id: item for item in catalog.sources}
    retrievals_by_revision: dict[str, list[RetrievalRecord]] = {}
    for retrieval in catalog.retrievals:
        retrievals_by_revision.setdefault(retrieval.source_revision_id, []).append(retrieval)
    lines = [
        "# Source Register (SourceCatalog.v1 projection)", "",
        "This file is generated deterministically from `source-catalog.v1.json`; edit the machine authority, not this projection.",
        "Catalog inclusion has `authorization_effect: none` and does not authorize acquisition, training, capture, experiments, or publication.",
        "", "| Source ID | Revision ID | Title / version | Official source | Retrieval | Bounded scope |",
        "|---|---|---|---|---|---|",
    ]
    for revision in catalog.revisions:
        source = sources[revision.source_id]
        observations = retrievals_by_revision.get(revision.source_revision_id) or [None]
        version = revision.exact_version or _token(revision.version_status)
        title = source.title.replace("|", "\\|")
        scope = source.applicable_scope.replace("|", "\\|")
        for retrieval in observations:
            status = _token(retrieval.retrieval_status) if retrieval else "unavailable"
            lines.append(
                f"| `{source.source_id}` | `{revision.source_revision_id}` | {title} -- {version} | "
                f"{source.official_url} | `{status}` | {scope} |"
            )
    lines.extend(("", "## Exact source uses", "", "| Use ID | Source revision | Status | Exact locator |", "|---|---|---|---|"))
    for use in catalog.uses:
        locator = (use.exact_locator or "unresolved").replace("|", "\\|")
        lines.append(
            f"| `{use.use_id}` | `{use.source_revision_id or 'unresolved'}` | `{_token(use.status)}` | {locator} |"
        )
    return "\n".join(lines) + "\n"


def checksum_projection(catalog: SourceCatalog) -> str:
    lines = ["# Deterministic compatibility projection from source-catalog.v1.json."]
    for content in sorted(catalog.contents, key=lambda item: item.filename):
        lines.append(f"{content.sha256.removeprefix('sha256:')}  ../documents/{content.filename}")
    return "\n".join(lines) + "\n"
