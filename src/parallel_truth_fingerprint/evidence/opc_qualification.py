"""Pure G4 qualification closure for independent OPC evidence."""
from __future__ import annotations
from dataclasses import dataclass
from typing import Iterable

@dataclass(frozen=True)
class OpcQualificationResult:
    qualified: bool
    gate: str
    violations: tuple[str, ...]
    authorization_effect: str = "none"

def qualify_opc_evidence(*, comparison_results: Iterable[object], causal_paths_demonstrated: bool,
                         publication_receipt_id: str | None) -> OpcQualificationResult:
    """Require complete immutable comparisons and demonstrated independent paths."""
    violations: list[str] = []
    comparisons = tuple(comparison_results)
    if not comparisons: violations.append("OPCG4-COMPARISONS-MISSING")
    if any(not getattr(item, "eligible", False) for item in comparisons): violations.append("OPCG4-COMPARISON-INELIGIBLE")
    if not causal_paths_demonstrated: violations.append("OPCG4-CAUSAL-INDEPENDENCE")
    if not isinstance(publication_receipt_id, str) or not publication_receipt_id.startswith("sha256:"):
        violations.append("OPCG4-PUBLICATION-RECEIPT")
    return OpcQualificationResult(not violations, "G4" if not violations else "blocked", tuple(violations))
