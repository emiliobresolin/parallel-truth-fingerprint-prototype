"""Pure custom physical/syscall correlation gate; never asserts fusion eligibility."""
from __future__ import annotations
from dataclasses import dataclass
@dataclass(frozen=True)
class CorrelationGate:
    correlated:bool; reason:str|None; authorization_effect:str="none"
def validate_custom_correlation(*, physical_run_id:str, syscall_run_id:str, campaign_id:str, correlation_id:str, same_campaign:bool)->CorrelationGate:
    if not same_campaign:return CorrelationGate(False,"SCORR-CAMPAIGN-MISMATCH")
    if any(not x.startswith("sha256:") for x in (physical_run_id,syscall_run_id,campaign_id,correlation_id)):return CorrelationGate(False,"SCORR-IDENTITY")
    return CorrelationGate(True,None)
