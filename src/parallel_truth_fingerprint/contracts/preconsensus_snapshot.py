"""Immutable source snapshot shared by the edge and independent OPC branches."""
from __future__ import annotations

import hashlib
import json
from dataclasses import dataclass, asdict


def _digest(value: str) -> bool:
    return value.startswith("sha256:") and len(value) == 71 and all(ch in "0123456789abcdef" for ch in value[7:])


@dataclass(frozen=True)
class PreConsensusSnapshot:
    experiment_id: str
    run_id: str
    cycle_id: str
    source_sequence: int
    correlation_id: str
    source_timestamp: str
    clock_evidence_id: str
    profile_revision_id: str
    parameter_gate_id: str
    engineering_value: str
    engineering_unit: str
    raw_current_ma: str
    quality_outcome: str
    snapshot_content_id: str = ""
    authorization_effect: str = "none"

    def canonical_bytes(self) -> bytes:
        body = asdict(self); body.pop("snapshot_content_id")
        return json.dumps(body, sort_keys=True, separators=(",", ":"), ensure_ascii=True).encode("ascii")

    def content_id(self) -> str:
        return "sha256:" + hashlib.sha256(self.canonical_bytes()).hexdigest()

    def validate(self) -> None:
        if self.authorization_effect != "none" or self.source_sequence <= 0 or not self.source_timestamp.endswith("Z"):
            raise ValueError("PCSNP-SCHEMA")
        if any(not _digest(value) for value in (self.experiment_id, self.run_id, self.cycle_id, self.correlation_id, self.clock_evidence_id, self.profile_revision_id, self.parameter_gate_id)):
            raise ValueError("PCSNP-IMMUTABLE-IDENTITY")
        if self.quality_outcome not in {"in_range", "under_range", "over_range", "missing", "uncertain", "fault"}:
            raise ValueError("PCSNP-QUALITY")
        if self.snapshot_content_id and self.snapshot_content_id != self.content_id():
            raise ValueError("PCSNP-CONTENT-ID")
