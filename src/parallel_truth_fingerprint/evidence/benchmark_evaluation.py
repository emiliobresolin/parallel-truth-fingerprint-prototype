"""Shared immutable benchmark evaluation closures for ADFA-LD, LID-DS and HAI.

The functions consume only already-frozen identities; they do not download,
train, calibrate, or infer a substitute result.
"""
from __future__ import annotations
from dataclasses import dataclass
import hashlib,json

_FAMILIES={"adfa_ld","lid_ds_2021","hai_23_05"}
def _ref(value:str)->bool:return value.startswith("sha256:") and len(value)==71
@dataclass(frozen=True)
class BenchmarkEvaluation:
 family:str; source_manifest_id:str; parser_id:str; partition_id:str; bundle_id:str; score_manifest_id:str; truth_join_id:str|None; metric_protocol_id:str; status:str; content_id:str=""; authorization_effect:str="none"
 def computed_id(self)->str:
  x=self.__dict__.copy();x.pop("content_id");return "sha256:"+hashlib.sha256(json.dumps(x,sort_keys=True,separators=(",",":")).encode()).hexdigest()
 def validate(self,*,require_truth:bool)->None:
  if self.family not in _FAMILIES or self.status not in {"complete","blocked","unqualified"}:raise ValueError("BEVAL-SCHEMA")
  if any(not _ref(x) for x in (self.source_manifest_id,self.parser_id,self.partition_id,self.bundle_id,self.score_manifest_id,self.metric_protocol_id)):raise ValueError("BEVAL-CLOSURE")
  if require_truth and not _ref(self.truth_join_id or ""):raise ValueError("BEVAL-TRUTH-JOIN")
  if self.content_id and self.content_id!=self.computed_id():raise ValueError("BEVAL-CONTENT")
@dataclass(frozen=True)
class BenchmarkPublicationGate:
 allowed:bool; reason:str|None; authorization_effect:str="none"
def validate_benchmark_publication(result:BenchmarkEvaluation)->BenchmarkPublicationGate:
 try:result.validate(require_truth=result.status=="complete")
 except ValueError as exc:return BenchmarkPublicationGate(False,str(exc))
 return BenchmarkPublicationGate(result.status=="complete",None if result.status=="complete" else "BEVAL-NONCOMPLETE")
