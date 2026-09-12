"""Opaque, immutable records for the local physical shadow route.

They describe a selected bundle and the result of a replay gate.  They do not
open a route, load a model, grant authority, or contain truth/control fields.
"""
from __future__ import annotations

import hashlib
import json
from dataclasses import asdict, dataclass, replace
from enum import StrEnum


PHYSICAL_SHADOW_SELECTION_SCHEMA = "PhysicalShadowSelection.v1"
G5_QUALIFICATION_SCHEMA = "G5PhysicalShadowQualification.v1"


class ShadowRouteDisposition(StrEnum):
    ELIGIBLE = "eligible"
    BLOCKED = "blocked"
    ROLLED_BACK = "rolled_back"


class G5Disposition(StrEnum):
    QUALIFIED = "qualified"
    NOT_QUALIFIED = "not_qualified"
    INCOMPLETE = "incomplete"


@dataclass(frozen=True)
class PhysicalShadowSelection:
    """The complete explicit identity closure for one inference-only route."""

    schema_version: str
    bundle_id: str
    profile_id: str
    parameter_set_id: str
    feature_schema_id: str
    preprocessing_id: str
    threshold_id: str
    code_identity: str
    dependency_lock_sha256: str
    runtime_identity: str
    authorization_id: str
    selection_id: str = ""
    authorization_effect: str = "none"


@dataclass(frozen=True)
class G5QualificationResult:
    """A supplied replay result; no qualification or activation is issued."""

    schema_version: str
    selection_id: str
    bundle_id: str
    batch_score_ids: tuple[str, ...]
    shadow_score_ids: tuple[str, ...]
    tolerance_id: str | None
    discrepancy_ids: tuple[str, ...]
    disposition: G5Disposition | str
    diagnostic_codes: tuple[str, ...]
    result_id: str = ""
    authorization_effect: str = "none"

    def __post_init__(self) -> None:
        for name in ("batch_score_ids", "shadow_score_ids", "discrepancy_ids", "diagnostic_codes"):
            object.__setattr__(self, name, tuple(sorted(set(getattr(self, name)))))


def _canonical(value: object, identity: str) -> bytes:
    payload = asdict(value)
    payload[identity] = ""
    return json.dumps(payload, ensure_ascii=True, sort_keys=True, separators=(",", ":"), allow_nan=False).encode("ascii")


def physical_shadow_selection_identity(value: PhysicalShadowSelection) -> str:
    return "sha256:" + hashlib.sha256(_canonical(value, "selection_id")).hexdigest()


def g5_qualification_identity(value: G5QualificationResult) -> str:
    return "sha256:" + hashlib.sha256(_canonical(value, "result_id")).hexdigest()


def finalize_physical_shadow_selection(value: PhysicalShadowSelection) -> PhysicalShadowSelection:
    return replace(value, selection_id=physical_shadow_selection_identity(replace(value, selection_id="")))


def finalize_g5_qualification(value: G5QualificationResult) -> G5QualificationResult:
    return replace(value, result_id=g5_qualification_identity(replace(value, result_id="")))
