"""Frozen physical anomaly thresholds; no fitting or recalibration API."""
from __future__ import annotations
from dataclasses import asdict, dataclass
import hashlib, json

def _id(value: str) -> bool: return value.startswith("sha256:") and len(value) == 71
@dataclass(frozen=True)
class PhysicalThreshold:
    candidate_id: str
    preprocessing_id: str
    feature_schema_id: str
    calibration_partition_id: str
    calibration_score_ids: tuple[str, ...]
    method_id: str
    score_direction: str
    threshold_value: str
    threshold_unit: str
    parameter_gate_id: str
    code_identity: str
    runtime_identity: str
    created_at: str
    content_id: str = ""
    authorization_effect: str = "none"
    def computed_id(self) -> str:
        value=asdict(self); value.pop("content_id")
        return "sha256:"+hashlib.sha256(json.dumps(value,sort_keys=True,separators=(",",":")).encode()).hexdigest()
    def validate(self) -> None:
        if self.score_direction not in {"higher_anomalous","lower_anomalous"} or not self.threshold_value or not self.threshold_unit or not self.created_at.endswith("Z"):
            raise ValueError("PTHRESH-SCHEMA")
        if any(not _id(v) for v in (self.candidate_id,self.preprocessing_id,self.feature_schema_id,self.calibration_partition_id,self.method_id,self.parameter_gate_id,self.code_identity,self.runtime_identity,*self.calibration_score_ids)):
            raise ValueError("PTHRESH-IDENTITY")
        if self.content_id and self.content_id != self.computed_id(): raise ValueError("PTHRESH-CONTENT")
