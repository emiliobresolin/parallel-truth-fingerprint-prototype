"""Pure pre-consensus revision guard; never mutates an OPC or control branch."""
from __future__ import annotations

from dataclasses import dataclass
from parallel_truth_fingerprint.contracts.preconsensus_snapshot import PreConsensusSnapshot

@dataclass(frozen=True)
class SnapshotDecision:
    accepted: bool
    classification: str
    authorization_effect: str = "none"

def guard_snapshot(snapshot: PreConsensusSnapshot, *, known: dict[tuple[str, str, int], str]) -> SnapshotDecision:
    snapshot.validate()
    key = (snapshot.run_id, snapshot.cycle_id, snapshot.source_sequence)
    identity = snapshot.content_id()
    prior = known.get(key)
    if prior is None: return SnapshotDecision(True, "new")
    if prior == identity: return SnapshotDecision(False, "idempotent_duplicate")
    return SnapshotDecision(False, "conflicting_revision")
