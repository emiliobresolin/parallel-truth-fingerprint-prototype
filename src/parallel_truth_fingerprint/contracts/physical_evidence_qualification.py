"""Immutable public result contract for controlled physical-evidence G2 checks.

This is a report of a supplied, already-completed closure.  It has no runner,
storage client, authorization issuer, truth reader, or publication side effect.
"""
from __future__ import annotations

import hashlib
import json
from dataclasses import dataclass, fields
from enum import StrEnum
from typing import Any


PHYSICAL_EVIDENCE_QUALIFICATION_VERSION = "PhysicalEvidenceQualificationResult.v1"


class QualificationDisposition(StrEnum):
    QUALIFIED = "qualified"
    BLOCKED = "blocked"
    INCOMPLETE = "incomplete"
    NOT_QUALIFIED = "not_qualified"


class QualificationCheckDisposition(StrEnum):
    PASS = "pass"
    FAIL = "fail"
    BLOCKED = "blocked"
    INCOMPLETE = "incomplete"


@dataclass(frozen=True)
class QualificationCheck:
    check_id: str
    disposition: QualificationCheckDisposition | str
    affected_ids: tuple[str, ...] = ()
    diagnostic_codes: tuple[str, ...] = ()

    def __post_init__(self) -> None:
        object.__setattr__(self, "affected_ids", tuple(sorted(set(self.affected_ids))))
        object.__setattr__(self, "diagnostic_codes", tuple(sorted(set(self.diagnostic_codes))))


@dataclass(frozen=True)
class PhysicalEvidenceQualificationResult:
    """Flat, public and non-authorizing qualification subject.

    ``closure_ids`` are opaque immutable identities only.  They deliberately
    contain neither restricted parents nor locators, values, labels or timing.
    """
    schema_version: str
    run_manifest_id: str
    run_receipt_id: str | None
    actual_run_status: str
    execution_modality: str
    closure_ids: tuple[str, ...]
    observation_ids: tuple[str, ...]
    checks: tuple[QualificationCheck, ...]
    disposition: QualificationDisposition | str
    limitations: tuple[str, ...]
    result_content_id: str
    authorization_effect: str = "none"

    def __post_init__(self) -> None:
        object.__setattr__(self, "closure_ids", tuple(sorted(set(self.closure_ids))))
        object.__setattr__(self, "observation_ids", tuple(sorted(set(self.observation_ids))))
        object.__setattr__(self, "checks", tuple(sorted(self.checks, key=lambda item: item.check_id)))
        object.__setattr__(self, "limitations", tuple(sorted(set(self.limitations))))

    def to_dict(self) -> dict[str, Any]:
        def plain(value: Any) -> Any:
            if isinstance(value, StrEnum): return value.value
            if isinstance(value, tuple): return [plain(item) for item in value]
            if hasattr(value, "__dataclass_fields__"):
                return {field.name: plain(getattr(value, field.name)) for field in fields(value)}
            return value
        return {field.name: plain(getattr(self, field.name)) for field in fields(self)}


def canonical_physical_evidence_qualification_bytes(record: PhysicalEvidenceQualificationResult) -> bytes:
    """Canonical ASCII preimage; ``result_content_id`` is excluded."""
    payload = record.to_dict()
    payload.pop("result_content_id", None)
    return json.dumps(payload, ensure_ascii=True, sort_keys=True, separators=(",", ":"), allow_nan=False).encode("ascii")


def physical_evidence_qualification_content_id(record: PhysicalEvidenceQualificationResult) -> str:
    return "sha256:" + hashlib.sha256(canonical_physical_evidence_qualification_bytes(record)).hexdigest()
