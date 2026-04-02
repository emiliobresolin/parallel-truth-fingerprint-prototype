"""Typed persisted artifact contracts for valid downstream records."""

from __future__ import annotations

from dataclasses import dataclass


@dataclass(frozen=True)
class ValidConsensusArtifactRecord:
    """Structured persisted artifact written only for valid rounds."""

    artifact_key: str
    persisted_at: str
    artifact_identity: dict[str, object]
    round_identity: dict[str, object]
    consensus_context: dict[str, object]
    validated_state: dict[str, object]
    dataset_context: dict[str, object]
    scada_context: dict[str, object]
    diagnostics: dict[str, object]

    def to_dict(self) -> dict[str, object]:
        """Return a serializable persisted artifact view."""

        return {
            "artifact_key": self.artifact_key,
            "persisted_at": self.persisted_at,
            "artifact_identity": self.artifact_identity,
            "round_identity": self.round_identity,
            "consensus_context": self.consensus_context,
            "validated_state": self.validated_state,
            "dataset_context": self.dataset_context,
            "scada_context": self.scada_context,
            "diagnostics": self.diagnostics,
        }
