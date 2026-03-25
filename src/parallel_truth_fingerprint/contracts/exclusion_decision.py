"""Per-round exclusion decision contracts."""

from __future__ import annotations

from dataclasses import dataclass

from parallel_truth_fingerprint.contracts.exclusion_reason import ExclusionReason
from parallel_truth_fingerprint.contracts.round_identity import RoundIdentity


@dataclass(frozen=True)
class ExclusionDecision:
    """Immediate round-scoped exclusion decision."""

    round_identity: RoundIdentity
    edge_id: str
    reason: ExclusionReason
    detail: str | None = None
