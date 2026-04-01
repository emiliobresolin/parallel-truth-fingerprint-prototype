"""Typed persisted artifact contracts for valid downstream records."""

from __future__ import annotations

from dataclasses import dataclass


@dataclass(frozen=True)
class ValidConsensusArtifactRecord:
    """Structured persisted artifact written only for valid rounds."""

    artifact_key: str
    persisted_at: str
    consensus_state: dict[str, object]
    trust_scores: tuple[dict[str, object], ...]
    excluded_edges: tuple[dict[str, object], ...]
    scada_comparison_results: dict[str, object]
    diagnostics: dict[str, object]

    def to_dict(self) -> dict[str, object]:
        """Return a serializable persisted artifact view."""

        return {
            "artifact_key": self.artifact_key,
            "persisted_at": self.persisted_at,
            "consensus_state": self.consensus_state,
            "trust_scores": list(self.trust_scores),
            "excluded_edges": list(self.excluded_edges),
            "scada_comparison_results": self.scada_comparison_results,
            "diagnostics": self.diagnostics,
        }
