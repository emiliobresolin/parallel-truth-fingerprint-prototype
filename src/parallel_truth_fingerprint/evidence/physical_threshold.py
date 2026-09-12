from __future__ import annotations
from dataclasses import dataclass
from parallel_truth_fingerprint.contracts.physical_threshold import PhysicalThreshold
@dataclass(frozen=True)
class ThresholdLoad:
    loaded: bool
    reason: str | None
    threshold: PhysicalThreshold | None
    authorization_effect: str = "none"
def load_frozen_threshold(threshold: PhysicalThreshold, *, candidate_id: str, preprocessing_id: str, feature_schema_id: str) -> ThresholdLoad:
    try: threshold.validate()
    except ValueError as exc: return ThresholdLoad(False,str(exc),None)
    if (threshold.candidate_id,threshold.preprocessing_id,threshold.feature_schema_id)!=(candidate_id,preprocessing_id,feature_schema_id): return ThresholdLoad(False,"PTHRESH-COMPATIBILITY",None)
    return ThresholdLoad(True,None,threshold)
