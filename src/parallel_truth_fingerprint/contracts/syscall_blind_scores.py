"""Immutable, truth-blind syscall detector scoring contracts."""
from __future__ import annotations

import hashlib
import json
from dataclasses import asdict, dataclass, fields, replace
from enum import StrEnum
from typing import Any

SYSCALL_DETECTOR_SCORE_SCHEMA = "DetectorScore.v1"
SYSCALL_SCORE_MANIFEST_SCHEMA = "SyscallScoreManifest.v1"


class SyscallScoreDecision(StrEnum):
    NORMAL = "normal"
    ANOMALOUS = "anomalous"
    UNAVAILABLE = "unavailable"
    INVALID = "invalid"


def _plain(value: Any) -> Any:
    if isinstance(value, StrEnum):
        return value.value
    if isinstance(value, tuple):
        return [_plain(item) for item in value]
    if hasattr(value, "__dataclass_fields__"):
        return {field.name: _plain(getattr(value, field.name)) for field in fields(value)}
    return value


class _Record:
    def to_dict(self) -> dict[str, Any]:
        return {field.name: _plain(getattr(self, field.name)) for field in fields(self)}


@dataclass(frozen=True)
class SyscallDetectorScore(_Record):
    schema_version: str
    bundle_id: str
    window_id: str
    input_hash: str
    raw_score: str | None
    calibrated_score: str | None
    score_direction: str
    threshold_id: str
    decision: SyscallScoreDecision | str
    latency_evidence_id: str | None
    missingness_id: str
    capture_quality_id: str
    capture_context_id: str
    run_correlation_id: str
    workload_correlation_id: str
    code_identity: str
    runtime_identity: str
    unavailability_reason_id: str | None
    score_id: str = ""
    authorization_effect: str = "none"


@dataclass(frozen=True)
class SyscallScoreManifest(_Record):
    schema_version: str
    bundle_id: str
    partition_id: str
    planned_window_ids: tuple[str, ...]
    scores: tuple[SyscallDetectorScore, ...]
    resource_evidence_ids: tuple[str, ...]
    failure_evidence_ids: tuple[str, ...]
    code_identity: str
    runtime_identity: str
    manifest_id: str = ""
    authorization_effect: str = "none"

    def __post_init__(self) -> None:
        object.__setattr__(self, "planned_window_ids", tuple(sorted(set(self.planned_window_ids))))
        object.__setattr__(self, "scores", tuple(sorted(self.scores, key=lambda score: score.window_id)))
        object.__setattr__(self, "resource_evidence_ids", tuple(sorted(set(self.resource_evidence_ids))))
        object.__setattr__(self, "failure_evidence_ids", tuple(sorted(set(self.failure_evidence_ids))))


def _canonical(record: _Record, identity_field: str) -> bytes:
    body = record.to_dict()
    body[identity_field] = ""
    return json.dumps(body, ensure_ascii=True, sort_keys=True, separators=(",", ":"), allow_nan=False).encode("ascii")


def syscall_detector_score_identity(score: SyscallDetectorScore) -> str:
    return "sha256:" + hashlib.sha256(_canonical(score, "score_id")).hexdigest()


def syscall_score_manifest_identity(manifest: SyscallScoreManifest) -> str:
    return "sha256:" + hashlib.sha256(_canonical(manifest, "manifest_id")).hexdigest()


def finalize_syscall_detector_score(score: SyscallDetectorScore) -> SyscallDetectorScore:
    return replace(score, score_id=syscall_detector_score_identity(replace(score, score_id="")))


def finalize_syscall_score_manifest(manifest: SyscallScoreManifest) -> SyscallScoreManifest:
    return replace(manifest, manifest_id=syscall_score_manifest_identity(replace(manifest, manifest_id="")))


@dataclass(frozen=True)
class SyscallBlindScore:
    """Small boundary record used by lightweight callers before manifest assembly."""
    bundle_id: str
    partition_id: str
    event_batch_id: str
    score_value: str | None
    score_status: str
    code_id: str
    runtime_id: str
    content_id: str = ""
    authorization_effect: str = "none"

    def computed_id(self) -> str:
        body = asdict(self)
        body.pop("content_id")
        return "sha256:" + hashlib.sha256(
            json.dumps(body, sort_keys=True, separators=(",", ":"), allow_nan=False).encode("ascii")
        ).hexdigest()

    def validate(self) -> None:
        if self.score_status not in {"scored", "unavailable", "invalid"}:
            raise ValueError("SSCORE-STATUS")
        if self.score_status == "scored" and self.score_value is None:
            raise ValueError("SSCORE-VALUE")
        identities = (self.bundle_id, self.partition_id, self.event_batch_id, self.code_id, self.runtime_id)
        if any(not value.startswith("sha256:") for value in identities):
            raise ValueError("SSCORE-ID")
        if self.content_id and self.content_id != self.computed_id():
            raise ValueError("SSCORE-HASH")
