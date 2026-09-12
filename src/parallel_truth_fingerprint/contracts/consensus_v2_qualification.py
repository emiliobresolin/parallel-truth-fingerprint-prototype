"""Immutable, non-authorizing G3 consensus-v2 qualification report.

The record only describes supplied evidence.  It cannot run consensus, query a
node, publish a result, or promote v2 out of shadow mode.
"""
from __future__ import annotations

import hashlib
import json
from dataclasses import dataclass, fields
from enum import StrEnum
from typing import Any


CONSENSUS_V2_QUALIFICATION_SCHEMA = "ConsensusV2QualificationResult.v1"


class ConsensusV2QualificationDisposition(StrEnum):
    QUALIFIED = "qualified"
    SHADOW = "shadow"
    BLOCKED = "blocked"
    INCOMPLETE = "incomplete"


class ConsensusV2CheckDisposition(StrEnum):
    PASS = "pass"
    FAIL = "fail"
    BLOCKED = "blocked"
    INCOMPLETE = "incomplete"


@dataclass(frozen=True)
class ConsensusV2QualificationCheck:
    check_id: str
    disposition: ConsensusV2CheckDisposition | str
    evidence_ids: tuple[str, ...] = ()
    diagnostic_codes: tuple[str, ...] = ()

    def __post_init__(self) -> None:
        object.__setattr__(self, "evidence_ids", tuple(sorted(set(self.evidence_ids))))
        object.__setattr__(self, "diagnostic_codes", tuple(sorted(set(self.diagnostic_codes))))


@dataclass(frozen=True)
class ConsensusV2QualificationResult:
    """A reproducible G3 assessment with no activation authority."""
    schema_version: str
    primary_configuration_id: str
    closure_ids: tuple[str, ...]
    checks: tuple[ConsensusV2QualificationCheck, ...]
    disposition: ConsensusV2QualificationDisposition | str
    limitations: tuple[str, ...]
    result_content_id: str
    authorization_effect: str = "none"

    def __post_init__(self) -> None:
        object.__setattr__(self, "closure_ids", tuple(sorted(set(self.closure_ids))))
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


def canonical_consensus_v2_qualification_bytes(record: ConsensusV2QualificationResult) -> bytes:
    payload = record.to_dict()
    payload.pop("result_content_id", None)
    return json.dumps(payload, ensure_ascii=True, sort_keys=True, separators=(",", ":"), allow_nan=False).encode("ascii")


def consensus_v2_qualification_content_id(record: ConsensusV2QualificationResult) -> str:
    return "sha256:" + hashlib.sha256(canonical_consensus_v2_qualification_bytes(record)).hexdigest()
