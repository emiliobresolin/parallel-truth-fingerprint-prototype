"""Truth-blind, content-addressed late-fusion plan validation."""
from __future__ import annotations
from dataclasses import dataclass
@dataclass(frozen=True)
class FrozenFusionPlan:
 physical_scores_id:str; syscall_scores_id:str; pairing_manifest_id:str; policy_id:str; partition_id:str; truth_unlocked:bool=False; authorization_effect:str="none"
def validate_fusion_plan(plan:FrozenFusionPlan)->tuple[bool,tuple[str,...]]:
 bad=[]
 if plan.truth_unlocked:bad.append("FUSION-TRUTH-UNLOCKED")
 if any(not x.startswith("sha256:") for x in (plan.physical_scores_id,plan.syscall_scores_id,plan.pairing_manifest_id,plan.policy_id,plan.partition_id)):bad.append("FUSION-IMMUTABLE-CLOSURE")
 return not bad,tuple(bad)
