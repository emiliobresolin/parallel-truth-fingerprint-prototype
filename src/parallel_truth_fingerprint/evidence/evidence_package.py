"""Final claim/evidence package reconstruction without publication side effects."""
from __future__ import annotations
from dataclasses import dataclass
@dataclass(frozen=True)
class ClaimEvidence:
 claim_id:str; evidence_ids:tuple[str,...]; limitation_ids:tuple[str,...]
@dataclass(frozen=True)
class EvidencePackageDecision:
 accepted:bool; gate:str; missing_claims:tuple[str,...]; authorization_effect:str="none"
def reconstruct_evidence_package(*,claims:tuple[ClaimEvidence,...],required_claim_ids:tuple[str,...],final_receipt_id:str|None)->EvidencePackageDecision:
 seen={c.claim_id for c in claims if c.evidence_ids}
 missing=tuple(sorted(set(required_claim_ids)-seen))
 if not final_receipt_id or not final_receipt_id.startswith("sha256:"):return EvidencePackageDecision(False,"G9",tuple(sorted(set(missing)|{"receipt"})))
 return EvidencePackageDecision(not missing,"G9",missing)
