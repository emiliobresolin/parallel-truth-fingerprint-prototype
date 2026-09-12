"""Fair normal-only categorical syscall candidate comparison closure."""
from __future__ import annotations
from dataclasses import dataclass

@dataclass(frozen=True)
class SyscallCandidatePlan:
    partition_id: str
    vocabulary_id: str
    training_budget_id: str
    validation_budget_id: str
    candidates: tuple[str, ...]
    content_id: str
    authorization_effect: str = "none"
@dataclass(frozen=True)
class SyscallCandidateGate:
    allowed: bool
    violations: tuple[str,...]
    authorization_effect: str = "none"
def validate_syscall_candidate_plan(plan: SyscallCandidatePlan) -> SyscallCandidateGate:
    problems=[]
    if len(plan.candidates)<2 or len(set(plan.candidates))!=len(plan.candidates): problems.append("SCV1-CANDIDATES")
    if any(not x.startswith("sha256:") for x in (plan.partition_id,plan.vocabulary_id,plan.training_budget_id,plan.validation_budget_id,plan.content_id)): problems.append("SCV1-IDENTITY")
    if any("test" in candidate or "truth" in candidate for candidate in plan.candidates): problems.append("SCV1-TRUTH-ACCESS")
    return SyscallCandidateGate(not problems,tuple(problems))
