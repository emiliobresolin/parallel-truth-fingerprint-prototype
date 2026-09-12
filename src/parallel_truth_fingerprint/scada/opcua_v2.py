"""Injected, read-only OPC UA v2 projection boundary.

No server is created here: callers provide a writer after independently
authorizing runtime execution.
"""
from __future__ import annotations

from dataclasses import dataclass
from typing import Protocol

from parallel_truth_fingerprint.contracts.preconsensus_snapshot import PreConsensusSnapshot

class OpcWriter(Protocol):
    def write_snapshot(self, snapshot_id: str, values: dict[str, str]) -> None: ...

@dataclass(frozen=True)
class OpcProjectionResult:
    available: bool
    reason: str | None
    snapshot_content_id: str
    authorization_effect: str = "none"

def project_preconsensus_snapshot(snapshot: PreConsensusSnapshot, writer: OpcWriter | None) -> OpcProjectionResult:
    """Validate before injected output; absence is explicit and has no fallback."""
    try:
        snapshot.validate()
    except ValueError:
        return OpcProjectionResult(False, "invalid_snapshot", snapshot.content_id())
    if writer is None:
        return OpcProjectionResult(False, "writer_unavailable", snapshot.content_id())
    writer.write_snapshot(snapshot.content_id(), {
        "engineering_value": snapshot.engineering_value,
        "engineering_unit": snapshot.engineering_unit,
        "raw_current_ma": snapshot.raw_current_ma,
        "quality_outcome": snapshot.quality_outcome,
    })
    return OpcProjectionResult(True, None, snapshot.content_id())
