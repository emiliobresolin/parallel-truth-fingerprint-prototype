"""Immutable, detector-facing contracts for frozen physical blind scores.

The records deliberately have a closed field set: no truth, label, scenario,
attack, intervention, or expected-outcome value can enter this boundary.
"""
from __future__ import annotations

import hashlib
import json
from dataclasses import dataclass, fields, replace
from enum import StrEnum
from typing import Any


DETECTOR_SCORE_SCHEMA = "DetectorScore.v1"
PHYSICAL_SCORE_MANIFEST_SCHEMA = "PhysicalScoreManifest.v1"


class ScoreDecision(StrEnum):
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
class DetectorScore(_Record):
    """One immutable score or explicitly retained unavailable outcome."""

    schema_version: str
    bundle_id: str
    window_id: str
    input_hash: str
    raw_score: str | None
    calibrated_score: str | None
    score_direction: str
    threshold_id: str
    decision: ScoreDecision | str
    latency_evidence_id: str | None
    missingness_id: str
    input_quality_id: str
    profile_id: str
    run_correlation_id: str
    code_identity: str
    runtime_identity: str
    unavailability_reason_id: str | None
    score_id: str = ""
    authorization_effect: str = "none"


@dataclass(frozen=True)
class PhysicalScoreManifest(_Record):
    """The complete pre-truth closure for exactly one test-window inventory."""

    schema_version: str
    bundle_id: str
    partition_id: str
    planned_window_ids: tuple[str, ...]
    scores: tuple[DetectorScore, ...]
    resource_evidence_ids: tuple[str, ...]
    failure_evidence_ids: tuple[str, ...]
    code_identity: str
    runtime_identity: str
    manifest_id: str = ""
    authorization_effect: str = "none"

    def __post_init__(self) -> None:
        object.__setattr__(self, "planned_window_ids", tuple(sorted(set(self.planned_window_ids))))
        object.__setattr__(self, "scores", tuple(sorted(self.scores, key=lambda item: item.window_id)))
        object.__setattr__(self, "resource_evidence_ids", tuple(sorted(set(self.resource_evidence_ids))))
        object.__setattr__(self, "failure_evidence_ids", tuple(sorted(set(self.failure_evidence_ids))))


def _canonical(record: _Record, identity_field: str) -> bytes:
    payload = record.to_dict()
    payload[identity_field] = ""
    return json.dumps(payload, ensure_ascii=True, sort_keys=True, separators=(",", ":"), allow_nan=False).encode("ascii")


def detector_score_identity(score: DetectorScore) -> str:
    return "sha256:" + hashlib.sha256(_canonical(score, "score_id")).hexdigest()


def physical_score_manifest_identity(manifest: PhysicalScoreManifest) -> str:
    return "sha256:" + hashlib.sha256(_canonical(manifest, "manifest_id")).hexdigest()


def finalize_detector_score(score: DetectorScore) -> DetectorScore:
    return replace(score, score_id=detector_score_identity(replace(score, score_id="")))


def finalize_physical_score_manifest(manifest: PhysicalScoreManifest) -> PhysicalScoreManifest:
    return replace(manifest, manifest_id=physical_score_manifest_identity(replace(manifest, manifest_id="")))
