"""Evaluator-only syscall outcomes after an exact truth unlock."""
from __future__ import annotations
from dataclasses import dataclass
@dataclass(frozen=True)
class SyscallEvaluationRequest:
    score_manifest_id:str; truth_unlock_id:str; truth_join_id:str; evaluation_authorization_id:str; evaluator_audience:str
@dataclass(frozen=True)
class SyscallEvaluationGate:
    allowed:bool; reason:str|None; authorization_effect:str="none"
def validate_syscall_evaluation(request:SyscallEvaluationRequest)->SyscallEvaluationGate:
    if request.evaluator_audience!="evaluator_restricted":return SyscallEvaluationGate(False,"SEVAL-AUDIENCE")
    if any(not x.startswith("sha256:") for x in (request.score_manifest_id,request.truth_unlock_id,request.truth_join_id,request.evaluation_authorization_id)):return SyscallEvaluationGate(False,"SEVAL-CLOSURE")
    return SyscallEvaluationGate(True,None)
