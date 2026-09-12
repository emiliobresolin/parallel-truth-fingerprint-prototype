"""Immutable, baseline-specific contracts for Story 9.1."""

from __future__ import annotations

from dataclasses import dataclass


@dataclass(frozen=True)
class DirtyOverlay:
    """One tracked worktree overlay observed independently of Git HEAD."""

    locator: str
    status_code: str
    byte_size: int | None
    sha256: str | None
    verification_status: str
    limitation: str | None = None
    origin: str = "tracked"

    def to_dict(self) -> dict[str, object]:
        return {
            "locator": self.locator,
            "status_code": self.status_code,
            "byte_size": self.byte_size,
            "sha256": self.sha256,
            "verification_status": self.verification_status,
            "origin": self.origin,
            "limitation": self.limitation,
        }


@dataclass(frozen=True)
class RepositoryIdentity:
    """Observed Git identity; it never claims that a worktree is clean."""

    head: str | None
    branch: str | None
    status_sha256: str | None
    status_verification: str
    ignored_status_sha256: str | None
    ignored_status_verification: str
    dirty_overlays: tuple[DirtyOverlay, ...]

    def to_dict(self) -> dict[str, object]:
        return {
            "head": self.head,
            "branch": self.branch,
            "status_sha256": self.status_sha256,
            "status_verification": self.status_verification,
            "ignored_status_sha256": self.ignored_status_sha256,
            "ignored_status_verification": self.ignored_status_verification,
            "dirty_overlays": [overlay.to_dict() for overlay in self.dirty_overlays],
        }


@dataclass(frozen=True)
class BaselineEntry:
    """One inspectable v1 input, limitation, or historical artifact."""

    entry_id: str
    category: str
    role: str
    version: str | None
    locator: str | None
    byte_size: int | None
    sha256: str | None
    verification_status: str
    scientific_status: str
    limitation: str | None = None
    observed_target: str | None = None
    evidence_origin: str | None = None

    def to_dict(self) -> dict[str, object]:
        return {
            "entry_id": self.entry_id,
            "category": self.category,
            "role": self.role,
            "version": self.version,
            "locator": self.locator,
            "byte_size": self.byte_size,
            "sha256": self.sha256,
            "verification_status": self.verification_status,
            "scientific_status": self.scientific_status,
            "limitation": self.limitation,
            "observed_target": self.observed_target,
            "evidence_origin": self.evidence_origin,
        }


@dataclass(frozen=True)
class V1BaselineManifest:
    """The Story 9.1-only v1 evidence baseline manifest."""

    schema_version: str
    baseline_id: str | None
    observed_at: str
    repository: RepositoryIdentity
    entries: tuple[BaselineEntry, ...]
    authorization_effect: str

    def to_identity_dict(self) -> dict[str, object]:
        """Return the canonical identity payload without its derived identifier."""

        return {
            "schema_version": self.schema_version,
            "observed_at": self.observed_at,
            "repository": self.repository.to_dict(),
            "entries": [entry.to_dict() for entry in self.entries],
            "authorization_effect": self.authorization_effect,
        }

    def to_dict(self) -> dict[str, object]:
        payload = self.to_identity_dict()
        payload["baseline_id"] = self.baseline_id
        return payload


@dataclass(frozen=True)
class BaselineValidationResult:
    """Pure validation outcome. It cannot authorize another activity."""

    valid: bool
    diagnostics: tuple[str, ...]
    authorization_effect: str = "none"

    def to_dict(self) -> dict[str, object]:
        return {
            "valid": self.valid,
            "diagnostics": list(self.diagnostics),
            "authorization_effect": self.authorization_effect,
        }
