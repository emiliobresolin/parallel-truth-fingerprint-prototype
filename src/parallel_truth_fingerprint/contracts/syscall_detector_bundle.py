"""Immutable categorical syscall detector bundle, inference-only by design."""
from __future__ import annotations
from dataclasses import dataclass, asdict
import hashlib,json
@dataclass(frozen=True)
class SyscallDetectorBundle:
 model_id:str; vocabulary_id:str; preprocessing_id:str; training_partition_id:str; calibration_partition_id:str; threshold_id:str; capture_policy_id:str; code_id:str; dependency_id:str; runtime_id:str; content_id:str=""; authorization_effect:str="none"
 def computed_id(self)->str:
  x=asdict(self);x.pop("content_id");return "sha256:"+hashlib.sha256(json.dumps(x,sort_keys=True,separators=(",",":")).encode()).hexdigest()
 def validate(self)->None:
  if self.authorization_effect!="none" or any(not v.startswith("sha256:") for v in asdict(self).values() if isinstance(v,str) and v and v!="none"):raise ValueError("SYB1-IDENTITY")
  if self.content_id and self.content_id!=self.computed_id():raise ValueError("SYB1-CONTENT")
