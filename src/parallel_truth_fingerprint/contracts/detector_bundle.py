"""Immutable, inference-only physical ``DetectorBundle.v1`` records.

The contract binds opaque, already-frozen evidence identities.  It deliberately
does not import a model runtime and exposes no fitting, calibration, alias, or
publication operation.
"""
from __future__ import annotations

import hashlib
import json
import re
from dataclasses import dataclass, fields
from enum import StrEnum
from typing import Any


DETECTOR_BUNDLE_SCHEMA = "DetectorBundle.v1"
PHYSICAL_FEATURE_SCHEMA_VERSION = "PhysicalFeatureSchema.v2"
PHYSICAL_MODEL_CONTRACT_VERSION = "PhysicalDetectorModel.v2"
_DIGEST = re.compile(r"sha256:[0-9a-f]{64}\Z")
_SLOT = re.compile(r"[a-z][a-z0-9_]*\Z")


class ScoreDirection(StrEnum):
    HIGHER_ANOMALOUS = "higher_anomalous"
    LOWER_ANOMALOUS = "lower_anomalous"


@dataclass(frozen=True)
class BundleComponentHash:
    """The exact serialized hash of a named immutable bundle component."""

    name: str
    artifact_id: str
    serialized_sha256: str


@dataclass(frozen=True)
class DetectorBundle:
    """Complete content-addressed physical detector composition.

    Every identifier is opaque.  In particular, neither this record nor its
    canonical representation carries a threshold value, observations, labels,
    truth, or an activation decision.
    """

    schema_version: str
    model_family: str
    model_contract_version: str
    architecture_id: str
    weights_id: str
    feature_schema_id: str
    feature_schema_version: str
    ordered_feature_names: tuple[str, ...]
    preprocessing_state_id: str
    training_dataset_id: str
    training_split_id: str
    calibration_dataset_id: str
    calibration_split_id: str
    calibration_artifact_id: str
    threshold_id: str
    threshold_derivation_id: str
    score_direction: ScoreDirection | str
    profile_compatibility_id: str
    code_identity: str
    dependency_lock_sha256: str
    runtime_identity: str
    component_hashes: tuple[BundleComponentHash, ...]
    bundle_id: str = ""
    authorization_effect: str = "none"

    def to_dict(self) -> dict[str, Any]:
        def plain(value: Any) -> Any:
            if isinstance(value, StrEnum):
                return value.value
            if isinstance(value, tuple):
                return [plain(item) for item in value]
            if hasattr(value, "__dataclass_fields__"):
                return {field.name: plain(getattr(value, field.name)) for field in fields(value)}
            return value
        return {field.name: plain(getattr(self, field.name)) for field in fields(self)}

    def component_ids(self) -> dict[str, str]:
        return {
            "architecture": self.architecture_id,
            "weights": self.weights_id,
            "feature_schema": self.feature_schema_id,
            "preprocessing": self.preprocessing_state_id,
            "training_dataset": self.training_dataset_id,
            "training_split": self.training_split_id,
            "calibration_dataset": self.calibration_dataset_id,
            "calibration_split": self.calibration_split_id,
            "calibration_artifact": self.calibration_artifact_id,
            "threshold": self.threshold_id,
            "threshold_derivation": self.threshold_derivation_id,
            "profile_compatibility": self.profile_compatibility_id,
            "code": self.code_identity,
            "dependency_lock": self.dependency_lock_sha256,
            "runtime": self.runtime_identity,
        }


def canonical_detector_bundle_bytes(bundle: DetectorBundle) -> bytes:
    """Return the one canonical byte representation used for the bundle ID."""
    payload = bundle.to_dict()
    payload["bundle_id"] = ""
    return (json.dumps(payload, sort_keys=True, ensure_ascii=True,
                       separators=(",", ":"), allow_nan=False) + "\n").encode("ascii")


def detector_bundle_identity(bundle: DetectorBundle) -> str:
    return "sha256:" + hashlib.sha256(canonical_detector_bundle_bytes(bundle)).hexdigest()


def is_immutable_bundle_id(value: object) -> bool:
    return isinstance(value, str) and _DIGEST.fullmatch(value) is not None


def valid_component_slot(value: object) -> bool:
    return isinstance(value, str) and _SLOT.fullmatch(value) is not None
