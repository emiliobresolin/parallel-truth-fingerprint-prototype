"""Pure, fail-closed assembly and verification for physical DetectorBundle.v1."""
from __future__ import annotations

from dataclasses import dataclass
from typing import Callable

from parallel_truth_fingerprint.contracts.detector_bundle import (
    DETECTOR_BUNDLE_SCHEMA, PHYSICAL_FEATURE_SCHEMA_VERSION,
    PHYSICAL_MODEL_CONTRACT_VERSION, BundleComponentHash, DetectorBundle,
    ScoreDirection, detector_bundle_identity, is_immutable_bundle_id,
    valid_component_slot,
)


_REQUIRED_COMPONENTS = frozenset((
    "architecture", "weights", "feature_schema", "preprocessing",
    "training_dataset", "training_split", "calibration_dataset",
    "calibration_split", "calibration_artifact", "threshold",
    "threshold_derivation", "profile_compatibility", "code",
    "dependency_lock", "runtime",
))


@dataclass(frozen=True)
class DeclaredBundleEnvironment:
    """Exact declared load environment; ambient runtime discovery is forbidden."""

    model_contract_version: str
    feature_schema_id: str
    feature_schema_version: str
    ordered_feature_names: tuple[str, ...]
    profile_compatibility_id: str
    code_identity: str
    dependency_lock_sha256: str
    runtime_identity: str


@dataclass(frozen=True)
class DetectorBundleValidation:
    valid: bool
    diagnostic_codes: tuple[str, ...]
    authorization_effect: str = "none"


@dataclass(frozen=True)
class DetectorBundleLoad:
    loaded: bool
    bundle: DetectorBundle | None
    diagnostic_codes: tuple[str, ...]
    authorization_effect: str = "none"


ComponentResolver = Callable[[str], str | None]


def _component_closure(bundle: DetectorBundle) -> tuple[str, ...]:
    expected = bundle.component_ids()
    components = tuple(bundle.component_hashes)
    names = tuple(component.name for component in components)
    codes: list[str] = []
    if len(names) != len(set(names)) or set(names) != _REQUIRED_COMPONENTS:
        codes.append("DB13_COMPONENT_CLOSURE_INVALID")
    if names != tuple(sorted(names)):
        codes.append("DB13_COMPONENT_ORDER_NONCANONICAL")
    for component in components:
        if (not valid_component_slot(component.name)
                or not is_immutable_bundle_id(component.artifact_id)
                or not is_immutable_bundle_id(component.serialized_sha256)):
            codes.append("DB13_COMPONENT_HASH_INVALID")
        elif expected.get(component.name) != component.artifact_id:
            codes.append("DB13_COMPONENT_BINDING_MISMATCH")
    return tuple(codes)


def validate_detector_bundle(bundle: DetectorBundle) -> DetectorBundleValidation:
    """Validate immutable structure only; no I/O, aliases, fitting, or inference."""
    codes: list[str] = []
    if bundle.schema_version != DETECTOR_BUNDLE_SCHEMA:
        codes.append("DB13_SCHEMA_UNSUPPORTED")
    if bundle.model_contract_version != PHYSICAL_MODEL_CONTRACT_VERSION:
        codes.append("DB13_MODEL_CONTRACT_INCOMPATIBLE")
    if bundle.feature_schema_version != PHYSICAL_FEATURE_SCHEMA_VERSION:
        codes.append("DB13_FEATURE_SCHEMA_INCOMPATIBLE")
    if str(bundle.score_direction) not in {item.value for item in ScoreDirection}:
        codes.append("DB13_SCORE_DIRECTION_INVALID")
    if not valid_component_slot(bundle.model_family):
        codes.append("DB13_MODEL_FAMILY_INVALID")
    features = tuple(bundle.ordered_feature_names)
    if not features or any(not valid_component_slot(name) for name in features) or len(features) != len(set(features)):
        codes.append("DB13_FEATURE_ORDER_INVALID")
    if bundle.authorization_effect != "none":
        codes.append("DB13_AUTHORIZATION_EFFECT_FORBIDDEN")
    if bundle.bundle_id != detector_bundle_identity(bundle):
        codes.append("DB13_BUNDLE_ID_MISMATCH")
    if any(not is_immutable_bundle_id(value) for value in bundle.component_ids().values()):
        codes.append("DB13_COMPONENT_ID_INVALID")
    codes.extend(_component_closure(bundle))
    return DetectorBundleValidation(not codes, tuple(sorted(set(codes))))


def assemble_detector_bundle(bundle: DetectorBundle) -> DetectorBundle:
    """Return the sole canonical ID for a fully specified immutable bundle.

    Assembly intentionally performs neither authorization nor persistence.
    """
    from dataclasses import replace
    provisional = replace(bundle, bundle_id="")
    candidate = replace(provisional, bundle_id=detector_bundle_identity(provisional))
    validation = validate_detector_bundle(candidate)
    if not validation.valid:
        raise ValueError(";".join(validation.diagnostic_codes))
    return candidate


def load_detector_bundle(bundle: DetectorBundle, *, environment: DeclaredBundleEnvironment,
                         component_resolver: ComponentResolver) -> DetectorBundleLoad:
    """Atomically verify a bundle against an explicit eligible environment.

    A resolver receives exact immutable component IDs only.  It must return the
    expected serialized SHA-256 for that same immutable object; absence or any
    mismatch fails the whole load.
    """
    validation = validate_detector_bundle(bundle)
    codes = list(validation.diagnostic_codes)
    if environment.model_contract_version != bundle.model_contract_version:
        codes.append("DB13_ENVIRONMENT_MODEL_CONTRACT_MISMATCH")
    if environment.feature_schema_id != bundle.feature_schema_id or environment.feature_schema_version != bundle.feature_schema_version:
        codes.append("DB13_ENVIRONMENT_SCHEMA_MISMATCH")
    if tuple(environment.ordered_feature_names) != tuple(bundle.ordered_feature_names):
        codes.append("DB13_ENVIRONMENT_FEATURE_ORDER_MISMATCH")
    if environment.profile_compatibility_id != bundle.profile_compatibility_id:
        codes.append("DB13_ENVIRONMENT_PROFILE_MISMATCH")
    if environment.code_identity != bundle.code_identity:
        codes.append("DB13_ENVIRONMENT_CODE_MISMATCH")
    if environment.dependency_lock_sha256 != bundle.dependency_lock_sha256:
        codes.append("DB13_ENVIRONMENT_DEPENDENCY_MISMATCH")
    if environment.runtime_identity != bundle.runtime_identity:
        codes.append("DB13_ENVIRONMENT_RUNTIME_MISMATCH")
    for component in bundle.component_hashes:
        observed = component_resolver(component.artifact_id)
        if observed is None:
            codes.append("DB13_COMPONENT_UNAVAILABLE")
        elif observed != component.serialized_sha256:
            codes.append("DB13_COMPONENT_HASH_MISMATCH")
    diagnostics = tuple(sorted(set(codes)))
    return DetectorBundleLoad(not diagnostics, bundle if not diagnostics else None, diagnostics)
