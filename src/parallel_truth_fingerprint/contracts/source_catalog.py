"""Flat immutable contracts for the authoritative SourceCatalog.v1 ledger."""

from __future__ import annotations

from dataclasses import dataclass, field
from enum import StrEnum


SOURCE_CATALOG_SCHEMA_VERSION = "source-catalog.v1"


class SourceType(StrEnum):
    STANDARD = "standard"
    OFFICIAL_SPECIFICATION = "official_specification"
    VENDOR_MANUAL = "vendor_manual"
    DATASET_RELEASE = "dataset_release"
    DATASET_MANUAL = "dataset_manual"
    GOVERNMENT_GUIDANCE = "government_guidance"
    SCHOLARLY_PAPER = "scholarly_paper"
    TOOL_DOCUMENTATION = "tool_documentation"
    SECONDARY_REFERENCE = "secondary_reference"


class Classification(StrEnum):
    PRIMARY = "primary"
    AUTHORITATIVE = "authoritative"
    VENDOR_DOCUMENTATION = "vendor_documentation"
    STANDARD = "standard"
    DATASET_SOURCE = "dataset_source"
    SECONDARY_REFERENCE = "secondary_reference"


class IssuerRole(StrEnum):
    STANDARDS_BODY = "standards_body"
    PROTOCOL_OWNER = "protocol_owner"
    GOVERNMENT = "government"
    MANUFACTURER = "manufacturer"
    DATASET_OWNER = "dataset_owner"
    TOOL_OWNER = "tool_owner"
    ORIGINAL_AUTHORS = "original_authors"
    PUBLISHER = "publisher"
    MIRROR_OPERATOR = "mirror_operator"


class AuthorityRole(StrEnum):
    RESPONSIBLE_OFFICIAL = "responsible_official"
    AUTHORITATIVE_FOR_SCOPE = "authoritative_for_scope"
    PRIMARY_CONTEXT = "primary_context"
    CONTEXTUAL_ONLY = "contextual_only"
    SECONDARY_ONLY = "secondary_only"


class PeerReviewStatus(StrEnum):
    PEER_REVIEWED = "peer_reviewed"
    NOT_PEER_REVIEWED = "not_peer_reviewed"
    UNKNOWN = "unknown"
    NOT_APPLICABLE = "not_applicable"


class CopyRole(StrEnum):
    OFFICIAL_COPY = "official_copy"
    PUBLISHER_COPY = "publisher_copy"
    AUTHOR_COPY = "author_copy"
    MIRROR_COPY = "mirror_copy"
    LOCAL_VERIFICATION_COPY = "local_verification_copy"


class RetrievalStatus(StrEnum):
    LOCAL = "local"
    LINK_ONLY = "link_only"
    RESTRICTED = "restricted"
    PENDING = "pending"
    UNAVAILABLE = "unavailable"


class VerificationStatus(StrEnum):
    VERIFIED = "verified"
    UNVERIFIED = "unverified"
    FAILED = "failed"
    NOT_APPLICABLE = "not_applicable"


class AccessStatus(StrEnum):
    PUBLIC = "public"
    RESTRICTED = "restricted"
    PAYWALLED = "paywalled"
    PENDING = "pending"
    UNAVAILABLE = "unavailable"
    UNKNOWN = "unknown"


class RightsStatus(StrEnum):
    DECLARED = "declared"
    UNKNOWN = "unknown"
    NOT_STATED = "not_stated"
    NOT_APPLICABLE = "not_applicable"


class RedistributionStatus(StrEnum):
    ALLOWED = "allowed"
    PROHIBITED = "prohibited"
    RESTRICTED = "restricted"
    UNKNOWN = "unknown"


class DateStatus(StrEnum):
    KNOWN = "known"
    UNKNOWN_LEGACY = "unknown_legacy"
    NOT_STATED = "not_stated"
    NOT_APPLICABLE = "not_applicable"


class ClaimUse(StrEnum):
    DIRECT_VALUE = "direct_value"
    CAPABILITY = "capability"
    CONSTRAINT = "constraint"
    DERIVATION_METHOD = "derivation_method"
    PROTOCOL_RULE = "protocol_rule"
    DATASET_IDENTITY = "dataset_identity"
    DATASET_SEMANTICS = "dataset_semantics"
    PUBLISHED_RESULT = "published_result"
    MODEL_PRECEDENT = "model_precedent"
    CONTEXTUAL_ONLY = "contextual_only"


class SourceUseStatus(StrEnum):
    LOCATED = "located"
    UNRESOLVED = "unresolved"
    CONTEXTUAL_ONLY = "contextual_only"
    INAPPLICABLE = "inapplicable"


class RelationType(StrEnum):
    MIRROR_OF = "mirror_of"
    ALIAS_OF = "alias_of"
    BYTE_IDENTICAL = "byte_identical"
    CONFLICTS_WITH = "conflicts_with"


def _token(value: object) -> object:
    return value.value if isinstance(value, StrEnum) else value


def _sorted_unique(values: object) -> tuple[object, ...]:
    if not isinstance(values, (list, tuple)):
        raise TypeError("array-valued SourceCatalog fields require a list or tuple")
    items = tuple(values)
    by_token = {str(_token(item)): item for item in items}
    return tuple(by_token[key] for key in sorted(by_token))


@dataclass(frozen=True)
class SourceRecord:
    source_id: str
    organization_authors: tuple[str, ...]
    title: str
    publication_date: str | None
    publication_date_status: DateStatus | str
    exact_version: str | None
    version_status: DateStatus | str
    source_type: SourceType | str
    classifications: tuple[Classification | str, ...]
    issuer_role: IssuerRole | str
    authority_role: AuthorityRole | str
    peer_review_status: PeerReviewStatus | str
    official_url: str
    applicable_scope: str
    limitations: tuple[str, ...]
    migration_tags: tuple[str, ...] = ()

    def __post_init__(self) -> None:
        object.__setattr__(self, "organization_authors", _sorted_unique(self.organization_authors))
        object.__setattr__(self, "classifications", _sorted_unique(self.classifications))
        object.__setattr__(self, "limitations", _sorted_unique(self.limitations))
        object.__setattr__(self, "migration_tags", _sorted_unique(self.migration_tags))

    def to_dict(self) -> dict[str, object]:
        return {
            "source_id": self.source_id,
            "organization_authors": list(self.organization_authors),
            "title": self.title,
            "publication_date": self.publication_date,
            "publication_date_status": _token(self.publication_date_status),
            "exact_version": self.exact_version,
            "version_status": _token(self.version_status),
            "source_type": _token(self.source_type),
            "classifications": [_token(item) for item in self.classifications],
            "issuer_role": _token(self.issuer_role),
            "authority_role": _token(self.authority_role),
            "peer_review_status": _token(self.peer_review_status),
            "official_url": self.official_url,
            "applicable_scope": self.applicable_scope,
            "limitations": list(self.limitations),
            "migration_tags": list(self.migration_tags),
        }


@dataclass(frozen=True)
class SourceRevision:
    source_revision_id: str
    source_id: str
    exact_version: str | None
    version_status: DateStatus | str
    release_date: str | None
    release_date_status: DateStatus | str
    immutable_locator: str | None
    mutable_location: bool
    limitations: tuple[str, ...]

    def __post_init__(self) -> None:
        object.__setattr__(self, "limitations", _sorted_unique(self.limitations))

    def to_dict(self) -> dict[str, object]:
        return {
            "source_revision_id": self.source_revision_id,
            "source_id": self.source_id,
            "exact_version": self.exact_version,
            "version_status": _token(self.version_status),
            "release_date": self.release_date,
            "release_date_status": _token(self.release_date_status),
            "immutable_locator": self.immutable_locator,
            "mutable_location": self.mutable_location,
            "limitations": list(self.limitations),
        }


@dataclass(frozen=True)
class ContentRecord:
    content_id: str
    source_revision_id: str
    filename: str
    byte_size: int
    sha256: str
    media_type: str

    def to_dict(self) -> dict[str, object]:
        return self.__dict__.copy()


@dataclass(frozen=True)
class RetrievalRecord:
    retrieval_id: str
    source_revision_id: str
    content_id: str | None
    copy_role: CopyRole | str
    retrieval_status: RetrievalStatus | str
    verification_status: VerificationStatus | str
    access_status: AccessStatus | str
    rights_status: RightsStatus | str
    redistribution_status: RedistributionStatus | str
    retrieval_date: str | None
    retrieval_date_status: DateStatus | str
    local_locator: str | None
    remote_locator: str
    license_terms_locator: str | None
    citation_notice: str | None
    permitted_project_use: str
    storage_policy: str
    verifier: str | None
    limitations: tuple[str, ...]

    def __post_init__(self) -> None:
        object.__setattr__(self, "limitations", _sorted_unique(self.limitations))

    def to_dict(self) -> dict[str, object]:
        payload = self.__dict__.copy()
        for name in ("copy_role", "retrieval_status", "verification_status", "access_status",
                     "rights_status", "redistribution_status", "retrieval_date_status"):
            payload[name] = _token(payload[name])
        payload["limitations"] = list(self.limitations)
        return payload


@dataclass(frozen=True)
class SourceUse:
    use_id: str
    source_id: str
    source_revision_id: str | None
    claim_use: ClaimUse | str
    locator_kind: str
    exact_locator: str | None
    supported_scope: str
    excluded_scope: tuple[str, ...]
    applicable_variant: str
    prototype_component: str
    research_question: str
    evidence_track: str
    final_package_element: str
    transferability_rationale: str
    status: SourceUseStatus | str
    responsible_authority: bool
    limitations: tuple[str, ...]

    def __post_init__(self) -> None:
        object.__setattr__(self, "excluded_scope", _sorted_unique(self.excluded_scope))
        object.__setattr__(self, "limitations", _sorted_unique(self.limitations))

    def to_dict(self) -> dict[str, object]:
        payload = self.__dict__.copy()
        payload["claim_use"] = _token(self.claim_use)
        payload["status"] = _token(self.status)
        payload["excluded_scope"] = list(self.excluded_scope)
        payload["limitations"] = list(self.limitations)
        return payload


@dataclass(frozen=True)
class RelationRecord:
    relation_id: str
    relation_type: RelationType | str
    source_record_id: str
    target_record_id: str

    def to_dict(self) -> dict[str, object]:
        return {
            "relation_id": self.relation_id,
            "relation_type": _token(self.relation_type),
            "source_record_id": self.source_record_id,
            "target_record_id": self.target_record_id,
        }


@dataclass(frozen=True)
class DiscrepancyRecord:
    discrepancy_id: str
    discrepancy_kind: str
    source_record_id: str
    target_record_id: str
    status: str
    limitation: str

    def to_dict(self) -> dict[str, object]:
        return self.__dict__.copy()


@dataclass(frozen=True)
class SourceCatalog:
    schema_version: str
    semantic_vocabulary_version: str
    sources: tuple[SourceRecord, ...]
    revisions: tuple[SourceRevision, ...]
    contents: tuple[ContentRecord, ...]
    retrievals: tuple[RetrievalRecord, ...]
    uses: tuple[SourceUse, ...]
    relations: tuple[RelationRecord, ...]
    discrepancies: tuple[DiscrepancyRecord, ...]
    authorization_effect: str = field(default="none", init=False)

    def __post_init__(self) -> None:
        order = {
            "sources": "source_id", "revisions": "source_revision_id", "contents": "content_id",
            "retrievals": "retrieval_id", "uses": "use_id", "relations": "relation_id",
            "discrepancies": "discrepancy_id",
        }
        for name, identifier in order.items():
            records = tuple(getattr(self, name))
            object.__setattr__(self, name, tuple(sorted(records, key=lambda item: getattr(item, identifier))))

    def to_dict(self) -> dict[str, object]:
        return {
            "schema_version": self.schema_version,
            "semantic_vocabulary_version": self.semantic_vocabulary_version,
            "sources": [item.to_dict() for item in self.sources],
            "revisions": [item.to_dict() for item in self.revisions],
            "contents": [item.to_dict() for item in self.contents],
            "retrievals": [item.to_dict() for item in self.retrievals],
            "uses": [item.to_dict() for item in self.uses],
            "relations": [item.to_dict() for item in self.relations],
            "discrepancies": [item.to_dict() for item in self.discrepancies],
            "authorization_effect": self.authorization_effect,
        }


@dataclass(frozen=True)
class SourceCatalogViolation:
    rule_id: str
    record_id: str
    fields: tuple[str, ...]
    offending_tokens: tuple[str, ...]
    explanation: str

    def to_dict(self) -> dict[str, object]:
        return {
            "rule_id": self.rule_id,
            "record_id": self.record_id,
            "fields": list(self.fields),
            "offending_tokens": list(self.offending_tokens),
            "explanation": self.explanation,
        }


@dataclass(frozen=True)
class SourceCatalogValidationResult:
    supported: bool
    valid: bool
    violations: tuple[SourceCatalogViolation, ...]
    authorization_effect: str = field(default="none", init=False)

    def to_dict(self) -> dict[str, object]:
        return {
            "supported": self.supported,
            "valid": self.valid,
            "violations": [item.to_dict() for item in self.violations],
            "authorization_effect": self.authorization_effect,
        }
