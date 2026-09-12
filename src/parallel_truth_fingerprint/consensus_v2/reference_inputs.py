"""Immutable public calculation inputs for the isolated Consensus.v2 reference."""
from __future__ import annotations

import hashlib
import re
from dataclasses import dataclass
from decimal import Decimal, InvalidOperation
from types import MappingProxyType
from typing import Mapping

from parallel_truth_fingerprint.contracts.scientific_governance import is_immutable_id

_DECIMAL = re.compile(r"-?(?:0|[1-9][0-9]*)(?:\.[0-9]+)?\Z")
MEAN_CURRENT_RESIDUAL_V1 = '{"algorithm":"mean_current_residual","version":"1"}'


def exact_decimal(value: str) -> Decimal:
    """Accept canonical base-10 strings only; floats and exponents are absent."""
    if not isinstance(value, str) or not _DECIMAL.fullmatch(value):
        raise ValueError("CV2_REFERENCE_DECIMAL")
    try:
        parsed = Decimal(value)
    except InvalidOperation as exc:
        raise ValueError("CV2_REFERENCE_DECIMAL") from exc
    if not parsed.is_finite():
        raise ValueError("CV2_REFERENCE_DECIMAL")
    return parsed


def _identity(value: str, code: str) -> str:
    if not is_immutable_id(value):
        raise ValueError(code)
    return value


@dataclass(frozen=True)
class ConsensusEvaluationObservationV2:
    """Exact public numeric projection bound to one immutable observation."""
    edge_id: str
    observation_id: str
    observation_canonical_hash: str
    current_value: str
    eligibility_reason_id: str | None
    eligibility_evidence_id: str

    def __post_init__(self) -> None:
        for name in ("edge_id", "observation_id", "observation_canonical_hash", "eligibility_evidence_id"):
            _identity(getattr(self, name), "CV2_REFERENCE_OBSERVATION_ID")
        if self.eligibility_reason_id is not None:
            _identity(self.eligibility_reason_id, "CV2_REFERENCE_ELIGIBILITY_REASON")
        exact_decimal(self.current_value)


@dataclass(frozen=True)
class ConsensusOperationClosureV2:
    """Closed, data-only mean-residual operation. No callable is accepted."""
    operation_id: str
    canonical_bytes: str
    canonical_bytes_hash: str
    conformance_vector_ids: tuple[str, ...]
    conformance_vector_hash: str
    minimum_participants: int
    max_abs_residual: str
    trace_max_events: int
    exclusion_reason_ids: Mapping[str, str]

    def __post_init__(self) -> None:
        _identity(self.operation_id, "CV2_REFERENCE_OPERATION_ID")
        if self.canonical_bytes != MEAN_CURRENT_RESIDUAL_V1:
            raise ValueError("CV2_REFERENCE_OPERATION_BYTES")
        expected = "sha256:" + hashlib.sha256(self.canonical_bytes.encode("ascii")).hexdigest()
        if self.canonical_bytes_hash != expected or self.operation_id != expected:
            raise ValueError("CV2_REFERENCE_OPERATION_HASH")
        vector = tuple(self.conformance_vector_ids)
        if not vector or vector != tuple(sorted(vector)) or len(vector) != len(set(vector)):
            raise ValueError("CV2_REFERENCE_CONFORMANCE_VECTOR")
        for value in vector: _identity(value, "CV2_REFERENCE_CONFORMANCE_VECTOR")
        vector_hash = "sha256:" + hashlib.sha256("\n".join(vector).encode("ascii")).hexdigest()
        if self.conformance_vector_hash != vector_hash:
            raise ValueError("CV2_REFERENCE_CONFORMANCE_HASH")
        if type(self.minimum_participants) is not int or self.minimum_participants < 1:
            raise ValueError("CV2_REFERENCE_MINIMUM_PARTICIPANTS")
        if type(self.trace_max_events) is not int or self.trace_max_events < 1:
            raise ValueError("CV2_REFERENCE_TRACE_BUDGET")
        if exact_decimal(self.max_abs_residual) < 0:
            raise ValueError("CV2_REFERENCE_RESIDUAL_BOUND")
        reasons = dict(self.exclusion_reason_ids)
        if set(reasons) != {"no_ranking", "residual"}:
            raise ValueError("CV2_REFERENCE_REASON_CLOSURE")
        for value in reasons.values(): _identity(value, "CV2_REFERENCE_REASON_CLOSURE")
        object.__setattr__(self, "conformance_vector_ids", vector)
        object.__setattr__(self, "exclusion_reason_ids", MappingProxyType(dict(sorted(reasons.items()))))
