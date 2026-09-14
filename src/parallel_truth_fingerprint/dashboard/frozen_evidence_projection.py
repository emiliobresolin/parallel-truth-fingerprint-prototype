"""Optional read-only dashboard projection of a frozen evidence package."""
from __future__ import annotations
from dataclasses import dataclass
from typing import Mapping
@dataclass(frozen=True)
class FrozenEvidenceProjection:
 package_receipt_id:str; claims:tuple[Mapping[str,object],...]; limitations:tuple[str,...]; read_only:bool=True; authorization_effect:str="none"
def project_frozen_evidence(*,package_receipt_id:str,claims:tuple[Mapping[str,object],...],limitations:tuple[str,...])->FrozenEvidenceProjection:
 if not package_receipt_id.startswith("sha256:"):raise ValueError("DASH-EVIDENCE-RECEIPT")
 if any("control" in str(c).lower() or "authorization" in str(c).lower() for c in claims):raise ValueError("DASH-READ-ONLY")
 return FrozenEvidenceProjection(package_receipt_id,claims,limitations)
