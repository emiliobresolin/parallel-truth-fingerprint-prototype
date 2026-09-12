"""Pure, fail-closed physical partition, window, and preprocessing checks.

This Story 13.2 module is deliberately offline: it neither reads an artifact
store nor fits a model.  Callers supply immutable identities and observations;
every unresolved prerequisite or boundary violation rejects the candidate.
"""
from __future__ import annotations

from dataclasses import dataclass
from enum import StrEnum
from typing import Callable, Iterable

from parallel_truth_fingerprint.contracts.scientific_governance import is_immutable_id


class PhysicalPartitionRole(StrEnum):
    TRAIN = "train"
    VALIDATION = "validation"
    CALIBRATION = "calibration"
    TEST = "test"


@dataclass(frozen=True)
class PhysicalPartitionMember:
    run_id: str
    role: PhysicalPartitionRole | str
    normal_eligible: bool
    run_manifest_id: str


@dataclass(frozen=True)
class PhysicalPartition:
    partition_id: str
    feature_schema_id: str
    parameter_evidence_ids: tuple[str, ...]
    members: tuple[PhysicalPartitionMember, ...]
    authorization_effect: str = "none"


@dataclass(frozen=True)
class PhysicalObservation:
    """Public observation metadata only; values and labels stay outside this gate."""
    observation_id: str
    run_id: str
    experiment_id: str
    phase_id: str
    scenario_id: str
    profile_id: str
    schema_id: str
    partition_id: str
    sequence: int
    valid: bool
    gap_before: bool
    quality_id: str


@dataclass(frozen=True)
class WindowParameters:
    parameter_evidence_id: str
    window_length: int
    stride: int
    padding: str
    exclusion_policy_id: str


@dataclass(frozen=True)
class PhysicalWindow:
    window_id: str
    source_run_id: str
    observation_ids: tuple[str, ...]
    observation_start: int
    observation_end: int
    partition_id: str
    feature_schema_id: str
    preprocessing_id: str
    quality_ids: tuple[str, ...]
    exclusion_ids: tuple[str, ...]
    # Intentional detector-facing allowlist. No labels, truth, or scenario data.
    authorization_effect: str = "none"


@dataclass(frozen=True)
class PreprocessingFit:
    preprocessing_id: str
    partition_id: str
    training_run_ids: tuple[str, ...]
    schema_id: str
    profile_id: str
    feature_order: tuple[str, ...]
    missingness_policy_id: str
    algorithm_id: str
    parameter_evidence_ids: tuple[str, ...]
    output_hash: str
    authorization_effect: str = "none"


@dataclass(frozen=True)
class PartitionDiagnostic:
    code: str
    subject_id: str


@dataclass(frozen=True)
class PartitionValidation:
    accepted: bool
    diagnostics: tuple[PartitionDiagnostic, ...]
    authorization_effect: str = "none"


ImmutableResolver = Callable[[str], bool]


def _immutable(resolver: ImmutableResolver, value: str | None) -> bool:
    return is_immutable_id(value) and resolver(value)


def _result(diagnostics: Iterable[PartitionDiagnostic]) -> PartitionValidation:
    ordered = tuple(sorted(set(diagnostics), key=lambda item: (item.code, item.subject_id)))
    return PartitionValidation(not ordered, ordered)


def validate_physical_partition(partition: PhysicalPartition, *, immutable_resolver: ImmutableResolver) -> PartitionValidation:
    """Require one complete independent run in exactly one frozen role."""
    errors: list[PartitionDiagnostic] = []
    if partition.authorization_effect != "none":
        errors.append(PartitionDiagnostic("PPV1_PARTITION_AUTHORIZATION_EFFECT", partition.partition_id))
    for identity in (partition.partition_id, partition.feature_schema_id, *partition.parameter_evidence_ids):
        if not _immutable(immutable_resolver, identity):
            errors.append(PartitionDiagnostic("PPV1_PARTITION_REFERENCE_UNRESOLVED", str(identity)))
    if not partition.members:
        errors.append(PartitionDiagnostic("PPV1_PARTITION_EMPTY", partition.partition_id))
    run_ids = [member.run_id for member in partition.members]
    if len(run_ids) != len(set(run_ids)):
        errors.extend(PartitionDiagnostic("PPV1_RUN_ROLE_OVERLAP", item) for item in run_ids)
    for member in partition.members:
        if str(member.role) not in {role.value for role in PhysicalPartitionRole}:
            errors.append(PartitionDiagnostic("PPV1_PARTITION_ROLE_INVALID", member.run_id))
        for identity in (member.run_id, member.run_manifest_id):
            if not _immutable(immutable_resolver, identity):
                errors.append(PartitionDiagnostic("PPV1_RUN_REFERENCE_UNRESOLVED", str(identity)))
    return _result(errors)


def build_physical_windows(*, partition: PhysicalPartition, observations: Iterable[PhysicalObservation],
                           parameters: WindowParameters, preprocessing_id: str,
                           immutable_resolver: ImmutableResolver) -> tuple[PhysicalWindow, ...] | PartitionValidation:
    """Generate only complete, homogeneous, contiguous detector-facing windows.

    Padding is rejected unless explicitly represented as ``none``; this module
    never invents samples.  Any invalid or boundary-spanning candidate rejects
    the whole preparation rather than silently dropping evidence.
    """
    validation = validate_physical_partition(partition, immutable_resolver=immutable_resolver)
    errors = list(validation.diagnostics)
    for identity in (parameters.parameter_evidence_id, parameters.exclusion_policy_id, preprocessing_id):
        if not _immutable(immutable_resolver, identity):
            errors.append(PartitionDiagnostic("PPV1_WINDOW_REFERENCE_UNRESOLVED", str(identity)))
    if parameters.window_length < 1 or parameters.stride < 1 or parameters.padding != "none":
        errors.append(PartitionDiagnostic("PPV1_WINDOW_PARAMETERS_INVALID", parameters.parameter_evidence_id))
    rows = tuple(observations)
    member_roles = {member.run_id: str(member.role) for member in partition.members}
    expected = (partition.partition_id, partition.feature_schema_id)
    for item in rows:
        if item.run_id not in member_roles or item.partition_id != expected[0] or item.schema_id != expected[1]:
            errors.append(PartitionDiagnostic("PPV1_OBSERVATION_PARTITION_MISMATCH", item.observation_id))
        if not all(_immutable(immutable_resolver, value) for value in (item.observation_id, item.run_id, item.experiment_id, item.phase_id, item.scenario_id, item.profile_id, item.schema_id, item.partition_id, item.quality_id)):
            errors.append(PartitionDiagnostic("PPV1_OBSERVATION_REFERENCE_UNRESOLVED", item.observation_id))
        if not item.valid:
            errors.append(PartitionDiagnostic("PPV1_INVALID_OBSERVATION", item.observation_id))
    if errors:
        return _result(errors)
    windows: list[PhysicalWindow] = []
    ordered = sorted(rows, key=lambda item: (item.run_id, item.sequence, item.observation_id))
    start = 0
    while start < len(ordered):
        candidate = ordered[start:start + parameters.window_length]
        if len(candidate) < parameters.window_length:
            break
        first = candidate[0]
        invariant = (first.run_id, first.experiment_id, first.phase_id, first.scenario_id, first.profile_id, first.schema_id, first.partition_id)
        contiguous = all(item.sequence == first.sequence + offset and not (offset and item.gap_before)
                         and (item.run_id, item.experiment_id, item.phase_id, item.scenario_id, item.profile_id, item.schema_id, item.partition_id) == invariant
                         for offset, item in enumerate(candidate))
        if not contiguous:
            return _result((PartitionDiagnostic("PPV1_WINDOW_BOUNDARY_CROSSING", first.observation_id),))
        ids = tuple(item.observation_id for item in candidate)
        windows.append(PhysicalWindow(
            window_id=f"{first.run_id}:{first.sequence}:{candidate[-1].sequence}", source_run_id=first.run_id,
            observation_ids=ids, observation_start=first.sequence, observation_end=candidate[-1].sequence,
            partition_id=partition.partition_id, feature_schema_id=partition.feature_schema_id,
            preprocessing_id=preprocessing_id, quality_ids=tuple(item.quality_id for item in candidate), exclusion_ids=(),
        ))
        start += parameters.stride
    return tuple(windows)


def validate_preprocessing_fit(fit: PreprocessingFit, *, partition: PhysicalPartition,
                               immutable_resolver: ImmutableResolver) -> PartitionValidation:
    """Fit state may be learned only from declared normal training runs."""
    errors: list[PartitionDiagnostic] = []
    if validate_physical_partition(partition, immutable_resolver=immutable_resolver).accepted is False:
        errors.append(PartitionDiagnostic("PPV1_FIT_PARTITION_INVALID", partition.partition_id))
    allowed = {member.run_id for member in partition.members if str(member.role) == "train" and member.normal_eligible}
    if not fit.training_run_ids or set(fit.training_run_ids) != allowed:
        errors.append(PartitionDiagnostic("PPV1_FIT_TRAINING_CLOSURE_INVALID", fit.preprocessing_id))
    if fit.partition_id != partition.partition_id or fit.schema_id != partition.feature_schema_id:
        errors.append(PartitionDiagnostic("PPV1_FIT_PARTITION_OR_SCHEMA_MISMATCH", fit.preprocessing_id))
    if not fit.feature_order or len(fit.feature_order) != len(set(fit.feature_order)):
        errors.append(PartitionDiagnostic("PPV1_FIT_FEATURE_ORDER_INVALID", fit.preprocessing_id))
    for identity in (fit.preprocessing_id, fit.partition_id, fit.schema_id, fit.profile_id, fit.missingness_policy_id,
                     fit.algorithm_id, fit.output_hash, *fit.training_run_ids, *fit.parameter_evidence_ids):
        if not _immutable(immutable_resolver, identity):
            errors.append(PartitionDiagnostic("PPV1_FIT_REFERENCE_UNRESOLVED", str(identity)))
    return _result(errors)


def validate_frozen_preprocessing_application(*, fit: PreprocessingFit, partition: PhysicalPartition,
                                              role: PhysicalPartitionRole | str, schema_id: str, profile_id: str,
                                              feature_order: tuple[str, ...], missingness_policy_id: str,
                                              output_hash: str, immutable_resolver: ImmutableResolver) -> PartitionValidation:
    """Allow application only of the exact already-fitted immutable state."""
    errors = list(validate_preprocessing_fit(fit, partition=partition, immutable_resolver=immutable_resolver).diagnostics)
    if str(role) not in {"validation", "calibration", "test", "live"}:
        errors.append(PartitionDiagnostic("PPV1_APPLY_ROLE_INVALID", str(role)))
    if (schema_id, profile_id, feature_order, missingness_policy_id, output_hash) != (fit.schema_id, fit.profile_id, fit.feature_order, fit.missingness_policy_id, fit.output_hash):
        errors.append(PartitionDiagnostic("PPV1_FROZEN_PREPROCESSING_MISMATCH", fit.preprocessing_id))
    return _result(errors)
