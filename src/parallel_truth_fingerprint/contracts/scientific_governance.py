"""Immutable, offline-only governance contracts for scientific evidence v1.

These objects describe proposed evidence and approvals.  They never perform an
activity, resolve an alias, write storage, or expose restricted truth.
"""

from __future__ import annotations

import hashlib
import json
import re
from dataclasses import asdict, dataclass, fields, replace
from enum import StrEnum
from typing import Any


SCIENTIFIC_GOVERNANCE_VERSION = "scientific-governance.v1"
_DIGEST = re.compile(r"sha256:[0-9a-f]{64}\Z")
_UTC = re.compile(r"\d{4}-\d{2}-\d{2}T\d{2}:\d{2}:\d{2}Z\Z")


class PartitionRole(StrEnum):
    TRAIN = "train"
    VALIDATION = "validation"
    CALIBRATION = "calibration"
    TEST = "test"
    EXCLUDED = "excluded"


class FreezeStage(StrEnum):
    FITTING = "fitting"
    MODEL_SELECTION = "model_selection"
    CALIBRATION = "calibration"
    THRESHOLD_SELECTION = "threshold_selection"
    BLIND_SCORING = "blind_scoring"
    FUSION = "fusion"
    PRETRUTH_EVALUATION = "pretruth_evaluation"


class ActivityAction(StrEnum):
    IMPLEMENTATION = "implementation"
    SOURCE_ACQUISITION = "source_acquisition"
    DATASET_ACQUISITION = "dataset_acquisition"
    PHYSICAL_ACQUISITION = "physical_acquisition"
    SYSCALL_CAPTURE = "syscall_capture"
    EXPERIMENT_EXECUTION = "experiment_execution"
    MODEL_TRAINING = "model_training"
    MODEL_SELECTION = "model_selection"
    CALIBRATION = "calibration"
    THRESHOLD_SELECTION = "threshold_selection"
    BLIND_SCORING = "blind_scoring"
    TRUTH_UNLOCK = "truth_unlock"
    RESTRICTED_TRUTH_JOIN = "restricted_truth_join"
    EVALUATION = "evaluation"
    FUSION = "fusion"
    PROMOTION = "promotion"
    FEATURE_ACTIVATION = "feature_activation"
    DEPLOYMENT = "deployment"
    SCIENTIFIC_PUBLICATION = "scientific_publication"


def _plain(value: Any) -> Any:
    if isinstance(value, StrEnum):
        return value.value
    if isinstance(value, tuple):
        return [_plain(item) for item in value]
    if isinstance(value, dict):
        return {key: _plain(item) for key, item in value.items()}
    if hasattr(value, "to_dict"):
        return value.to_dict()
    return value


class _Record:
    authorization_effect = "none"

    def to_dict(self) -> dict[str, Any]:
        return {field.name: _plain(getattr(self, field.name)) for field in fields(self)}


def canonical_governance_bytes(record: _Record) -> bytes:
    """Return deterministic UTF-8 bytes; records never accept caller IDs."""
    return json.dumps(record.to_dict(), ensure_ascii=True, sort_keys=True, separators=(",", ":")).encode("ascii")


def governance_content_id(record: _Record) -> str:
    return "sha256:" + hashlib.sha256(canonical_governance_bytes(record)).hexdigest()


@dataclass(frozen=True)
class PartitionMembership(_Record):
    group_id: str
    disposition: PartitionRole | str
    exclusion_reason: str | None = None
    exclusion_evidence_id: str | None = None


@dataclass(frozen=True)
class PartitionRecord(_Record):
    audience: str
    source_universe_id: str
    track_id: str
    eligibility_policy_id: str
    profile_revision_id: str
    grouping_scheme_id: str
    method_identity: str
    created_at: str
    source_use_revision_ids: tuple[str, ...]
    memberships: tuple[PartitionMembership, ...]
    randomness_binding_id: str | None = None
    authorization_effect: str = "none"

    def __post_init__(self) -> None:
        object.__setattr__(self, "source_use_revision_ids", tuple(sorted(set(self.source_use_revision_ids))))
        object.__setattr__(self, "memberships", tuple(sorted(self.memberships, key=lambda item: item.group_id)))


@dataclass(frozen=True)
class ScientificFreeze(_Record):
    audience: str
    stage: FreezeStage | str
    profile_revision_id: str
    created_at: str
    bindings: tuple[tuple[str, str], ...]
    predecessor_freeze_id: str | None = None
    authorization_effect: str = "none"

    def __post_init__(self) -> None:
        object.__setattr__(self, "bindings", tuple(sorted(self.bindings)))


@dataclass(frozen=True)
class TruthUnlockRecord(_Record):
    audience: str
    partition_id: str
    support_id: str
    pretruth_freeze_id: str
    blind_scoring_freeze_id: str
    score_closure_id: str
    detector_decision_closure_id: str
    completion_receipt_ids: tuple[str, ...]
    restricted_truth_id: str
    authorization_id: str
    owner_id: str
    decision: str
    created_at: str
    authorization_effect: str = "none"


@dataclass(frozen=True)
class TruthJoinRecord(_Record):
    audience: str
    unlock_id: str
    authorization_id: str
    partition_id: str
    support_id: str
    freeze_id: str
    score_id: str
    detector_decision_id: str
    restricted_truth_id: str
    evaluator_identity: str
    join_outcome: str
    created_at: str
    authorization_effect: str = "none"


@dataclass(frozen=True)
class ActivityAuthorization(_Record):
    audience: str
    action: ActivityAction | str
    profile_revision_id: str
    scope_slots: tuple[tuple[str, str], ...]
    input_ids: tuple[str, ...]
    prerequisite_ids: tuple[str, ...]
    expected_output_roles: tuple[str, ...]
    owner_id: str
    decision: str
    created_at: str
    limitations: tuple[str, ...]
    planned_activity_id: str
    authorization_effect: str = "permission"

    def __post_init__(self) -> None:
        for field_name in ("scope_slots", "input_ids", "prerequisite_ids", "expected_output_roles", "limitations"):
            object.__setattr__(self, field_name, tuple(sorted(set(getattr(self, field_name)))))

    def planned_payload(self) -> dict[str, Any]:
        return {"action": _plain(self.action), "profile_revision_id": self.profile_revision_id,
                "scope_slots": _plain(self.scope_slots), "input_ids": _plain(self.input_ids),
                "prerequisite_ids": _plain(self.prerequisite_ids), "expected_output_roles": _plain(self.expected_output_roles),
                "owner_id": self.owner_id}

    def computed_id(self) -> str:
        payload = json.dumps(self.planned_payload(), ensure_ascii=True, sort_keys=True, separators=(",", ":")).encode("ascii")
        return "sha256:" + hashlib.sha256(payload).hexdigest()

    def with_computed_id(self) -> "ActivityAuthorization":
        return replace(self, planned_activity_id=self.computed_id())


def is_immutable_id(value: str | None) -> bool:
    return bool(value and _DIGEST.fullmatch(value))


def is_canonical_timestamp(value: str) -> bool:
    return bool(_UTC.fullmatch(value))


def is_safe_opaque_identifier(value: str | None) -> bool:
    """Accept only an immutable identity, never a path, alias, or secret-like ID."""
    return is_immutable_id(value)


def _parse_string(value: object, rule: str, *, nullable: bool = False) -> str | None:
    if value is None and nullable:
        return None
    if not isinstance(value, str):
        raise ValueError(rule)
    return value


def _strict_record_payload(payload: object, expected: set[str]) -> dict[str, object]:
    if not isinstance(payload, dict):
        raise ValueError("GOV-PARSE-OBJECT-REQUIRED")
    if set(payload) != expected:
        raise ValueError("GOV-PARSE-FIELDS-INVALID")
    return payload


def parse_partition_record(payload: object) -> PartitionRecord:
    """Strictly parse a JSON-shaped partition record without filesystem access."""
    expected = {
        "audience", "source_universe_id", "track_id", "eligibility_policy_id",
        "profile_revision_id", "grouping_scheme_id", "method_identity", "created_at",
        "source_use_revision_ids", "memberships", "randomness_binding_id", "authorization_effect",
    }
    payload = _strict_record_payload(payload, expected)
    if payload.get("authorization_effect") != "none":
        raise ValueError("GOV-PARSE-FIELDS-INVALID")
    memberships = payload["memberships"]
    if not isinstance(memberships, list) or not isinstance(payload["source_use_revision_ids"], list):
        raise ValueError("GOV-PARSE-COLLECTION-INVALID")
    parsed: list[PartitionMembership] = []
    for item in memberships:
        if not isinstance(item, dict) or set(item) != {"group_id", "disposition", "exclusion_reason", "exclusion_evidence_id"}:
            raise ValueError("GOV-PARSE-MEMBERSHIP-INVALID")
        if any(not isinstance(item[key], str) and item[key] is not None for key in item):
            raise ValueError("GOV-PARSE-TYPE-INVALID")
        parsed.append(PartitionMembership(**item))
    kwargs = {key: payload[key] for key in expected - {"memberships", "source_use_revision_ids", "authorization_effect"}}
    if any(not isinstance(value, str) and value is not None for value in kwargs.values()):
        raise ValueError("GOV-PARSE-TYPE-INVALID")
    return PartitionRecord(
        **kwargs, source_use_revision_ids=tuple(payload["source_use_revision_ids"]), memberships=tuple(parsed),
    )


def parse_scientific_freeze(payload: object) -> ScientificFreeze:
    expected = {"audience", "stage", "profile_revision_id", "created_at", "bindings", "predecessor_freeze_id", "authorization_effect"}
    value = _strict_record_payload(payload, expected)
    if value["authorization_effect"] != "none" or not isinstance(value["bindings"], list):
        raise ValueError("GOV-PARSE-FIELDS-INVALID")
    bindings: list[tuple[str, str]] = []
    for item in value["bindings"]:
        if not isinstance(item, list) or len(item) != 2 or not all(isinstance(part, str) for part in item):
            raise ValueError("GOV-PARSE-BINDING-INVALID")
        bindings.append((item[0], item[1]))
    return ScientificFreeze(
        audience=_parse_string(value["audience"], "GOV-PARSE-TYPE-INVALID"),
        stage=_parse_string(value["stage"], "GOV-PARSE-TYPE-INVALID"),
        profile_revision_id=_parse_string(value["profile_revision_id"], "GOV-PARSE-TYPE-INVALID"),
        created_at=_parse_string(value["created_at"], "GOV-PARSE-TYPE-INVALID"), bindings=tuple(bindings),
        predecessor_freeze_id=_parse_string(value["predecessor_freeze_id"], "GOV-PARSE-TYPE-INVALID", nullable=True),
    )
