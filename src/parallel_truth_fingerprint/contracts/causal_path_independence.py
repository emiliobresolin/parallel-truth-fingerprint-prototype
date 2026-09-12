"""Immutable, non-authorizing records for OPC/consensus causal-path tests."""
from __future__ import annotations

import hashlib
import json
from dataclasses import dataclass, fields
from enum import StrEnum
from typing import Any


CAUSAL_PATH_INDEPENDENCE_SCHEMA = "CausalPathIndependenceResult.v1"


class CausalVariation(StrEnum):
    CONSENSUS_ONLY = "consensus_only"
    OPC_ONLY = "opc_only"
    COMMON_SOURCE = "common_source"
    OPC_UNAVAILABLE = "opc_unavailable"


class OpcEvidenceState(StrEnum):
    AVAILABLE = "available"
    UNAVAILABLE = "unavailable"
    DELAYED = "delayed"
    NEWLY_READ = "newly_read"


class CausalCheckDisposition(StrEnum):
    PASS = "pass"
    FAIL = "fail"
    BLOCKED = "blocked"
    INCOMPLETE = "incomplete"


class CausalIndependenceDisposition(StrEnum):
    DEMONSTRATED = "demonstrated"
    VIOLATED = "violated"
    BLOCKED = "blocked"
    INCOMPLETE = "incomplete"


@dataclass(frozen=True)
class CausalPathTrace:
    """Identity-only trace for one side of a controlled branch comparison.

    It holds no values, labels, truth, or network objects.  A trace's two
    lineage fields explicitly bind both derived branches to its snapshot.
    """

    trace_id: str
    snapshot_id: str
    writer_id: str
    server_id: str
    client_id: str
    opc_condition_id: str
    opc_evidence_state: OpcEvidenceState | str
    opc_observation_id: str | None
    opc_evidence_valid: bool
    opc_fallback_kind: str
    consensus_configuration_id: str
    consensus_input_id: str
    consensus_decision_id: str
    comparison_id: str | None
    opc_lineage_snapshot_id: str
    consensus_lineage_snapshot_id: str


@dataclass(frozen=True)
class CausalPathCase:
    case_id: str
    variation: CausalVariation | str
    baseline: CausalPathTrace
    varied: CausalPathTrace
    transition_evidence_ids: tuple[str, ...]

    def __post_init__(self) -> None:
        object.__setattr__(self, "transition_evidence_ids", tuple(sorted(set(self.transition_evidence_ids))))


@dataclass(frozen=True)
class CausalPathCheck:
    check_id: str
    disposition: CausalCheckDisposition | str
    diagnostic_codes: tuple[str, ...] = ()
    evidence_ids: tuple[str, ...] = ()

    def __post_init__(self) -> None:
        object.__setattr__(self, "diagnostic_codes", tuple(sorted(set(self.diagnostic_codes))))
        object.__setattr__(self, "evidence_ids", tuple(sorted(set(self.evidence_ids))))


@dataclass(frozen=True)
class CausalPathIndependenceResult:
    schema_version: str
    cases: tuple[CausalPathCase, ...]
    checks: tuple[CausalPathCheck, ...]
    disposition: CausalIndependenceDisposition | str
    limitations: tuple[str, ...]
    result_content_id: str
    authorization_effect: str = "none"

    def __post_init__(self) -> None:
        object.__setattr__(self, "cases", tuple(sorted(self.cases, key=lambda item: item.case_id)))
        object.__setattr__(self, "checks", tuple(sorted(self.checks, key=lambda item: item.check_id)))
        object.__setattr__(self, "limitations", tuple(sorted(set(self.limitations))))

    def to_dict(self) -> dict[str, Any]:
        def plain(value: Any) -> Any:
            if isinstance(value, StrEnum):
                return value.value
            if isinstance(value, tuple):
                return [plain(item) for item in value]
            if hasattr(value, "__dataclass_fields__"):
                return {field.name: plain(getattr(value, field.name)) for field in fields(value)}
            return value
        return {field.name: plain(getattr(self, field.name)) for field in fields(self)}


def canonical_causal_path_independence_bytes(record: CausalPathIndependenceResult) -> bytes:
    payload = record.to_dict()
    payload.pop("result_content_id", None)
    return json.dumps(payload, ensure_ascii=True, sort_keys=True, separators=(",", ":"), allow_nan=False).encode("ascii")


def causal_path_independence_content_id(record: CausalPathIndependenceResult) -> str:
    return "sha256:" + hashlib.sha256(canonical_causal_path_independence_bytes(record)).hexdigest()
