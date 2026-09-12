"""Pure, fail-closed categorical syscall partition and window contracts.

This Story 14.4 boundary is deliberately offline.  It neither captures events,
reads raw bytes, fits a vocabulary, persists evidence, nor authorizes an
activity.  It admits only caller-supplied immutable identities and returns
deterministic diagnostics for every unavailable or boundary-crossing input.
"""
from __future__ import annotations

from dataclasses import dataclass
from enum import StrEnum
from typing import Callable, Iterable

from parallel_truth_fingerprint.contracts.scientific_governance import is_immutable_id


class SyscallPartitionRole(StrEnum):
    TRAIN = "train"
    VALIDATION = "validation"
    CALIBRATION = "calibration"
    TEST = "test"


@dataclass(frozen=True)
class SyscallPartitionMember:
    """A complete independent capture group assigned to one role."""
    run_id: str
    role: SyscallPartitionRole | str
    normal_eligible: bool
    run_manifest_id: str
    boot_id: str
    session_id: str
    container_id: str
    process_scope_id: str
    capture_group_id: str
    batch_ids: tuple[str, ...]


@dataclass(frozen=True)
class SyscallPartition:
    partition_id: str
    feature_schema_id: str
    parameter_evidence_ids: tuple[str, ...]
    members: tuple[SyscallPartitionMember, ...]
    authorization_effect: str = "none"


@dataclass(frozen=True)
class CategoricalSyscallEvent:
    """Detector-admissible metadata; categorical call names are never numeric values."""
    event_id: str
    batch_id: str
    raw_segment_id: str
    run_id: str
    boot_id: str
    session_id: str
    container_id: str
    process_scope_id: str
    capture_group_id: str
    collector_id: str
    filter_id: str
    kernel_id: str
    abi_id: str
    schema_id: str
    partition_id: str
    source_identity: str
    categorical_name: str
    direction: str
    sequence: int
    timestamp: str
    gap_before: bool
    loss_boundary_before: bool
    duplicate: bool
    queue_pressure: bool
    quality_id: str
    exclusion_policy_id: str


@dataclass(frozen=True)
class SyscallWindowParameters:
    parameter_evidence_id: str
    window_length: int
    stride: int
    padding: str
    exclusion_policy_id: str
    loss_policy_id: str


@dataclass(frozen=True)
class CategoricalSyscallWindow:
    """Lineage-only detector input; truth, labels and scenario meaning are absent."""
    window_id: str
    source_run_id: str
    event_ids: tuple[str, ...]
    batch_ids: tuple[str, ...]
    raw_segment_ids: tuple[str, ...]
    event_start: int
    event_end: int
    partition_id: str
    feature_schema_id: str
    preprocessing_id: str
    quality_ids: tuple[str, ...]
    exclusion_ids: tuple[str, ...]
    authorization_effect: str = "none"


@dataclass(frozen=True)
class SyscallPreprocessingFit:
    """Immutable fitted vocabulary state, validated but never fitted here."""
    preprocessing_id: str
    partition_id: str
    training_run_ids: tuple[str, ...]
    training_event_ids: tuple[str, ...]
    schema_id: str
    vocabulary_id: str
    vocabulary_mapping_hash: str
    frequency_state_hash: str
    unknown_event_policy_id: str
    algorithm_id: str
    parameter_evidence_ids: tuple[str, ...]
    code_id: str
    output_hash: str
    authorization_effect: str = "none"


@dataclass(frozen=True)
class SyscallPartitionDiagnostic:
    code: str
    subject_id: str


@dataclass(frozen=True)
class SyscallPartitionValidation:
    accepted: bool
    diagnostics: tuple[SyscallPartitionDiagnostic, ...]
    authorization_effect: str = "none"


ImmutableResolver = Callable[[str], bool]


def _immutable(resolver: ImmutableResolver, value: str | None) -> bool:
    return is_immutable_id(value) and resolver(value)


def _result(diagnostics: Iterable[SyscallPartitionDiagnostic]) -> SyscallPartitionValidation:
    ordered = tuple(sorted(set(diagnostics), key=lambda item: (item.code, item.subject_id)))
    return SyscallPartitionValidation(not ordered, ordered)


def validate_syscall_partition(partition: SyscallPartition, *, immutable_resolver: ImmutableResolver) -> SyscallPartitionValidation:
    """Require immutable, complete, non-overlapping capture-group assignment."""
    errors: list[SyscallPartitionDiagnostic] = []
    if partition.authorization_effect != "none":
        errors.append(SyscallPartitionDiagnostic("SPV1_PARTITION_AUTHORIZATION_EFFECT", partition.partition_id))
    for identity in (partition.partition_id, partition.feature_schema_id, *partition.parameter_evidence_ids):
        if not _immutable(immutable_resolver, identity):
            errors.append(SyscallPartitionDiagnostic("SPV1_PARTITION_REFERENCE_UNRESOLVED", str(identity)))
    if not partition.members:
        errors.append(SyscallPartitionDiagnostic("SPV1_PARTITION_EMPTY", partition.partition_id))
    group_ids = [member.capture_group_id for member in partition.members]
    if len(group_ids) != len(set(group_ids)):
        errors.extend(SyscallPartitionDiagnostic("SPV1_CAPTURE_GROUP_ROLE_OVERLAP", value) for value in group_ids)
    for member in partition.members:
        if str(member.role) not in {role.value for role in SyscallPartitionRole}:
            errors.append(SyscallPartitionDiagnostic("SPV1_PARTITION_ROLE_INVALID", member.capture_group_id))
        if not member.batch_ids:
            errors.append(SyscallPartitionDiagnostic("SPV1_CAPTURE_GROUP_BATCHES_EMPTY", member.capture_group_id))
        identities = (member.run_id, member.run_manifest_id, member.boot_id, member.session_id,
                      member.container_id, member.process_scope_id, member.capture_group_id, *member.batch_ids)
        if not all(_immutable(immutable_resolver, identity) for identity in identities):
            errors.append(SyscallPartitionDiagnostic("SPV1_CAPTURE_GROUP_REFERENCE_UNRESOLVED", member.capture_group_id))
    return _result(errors)


def canonicalize_categorical_syscalls(events: Iterable[CategoricalSyscallEvent], *,
                                      immutable_resolver: ImmutableResolver) -> tuple[CategoricalSyscallEvent, ...] | SyscallPartitionValidation:
    """Validate and order categorical events without mapping, dropping or guessing any call."""
    rows = tuple(events)
    errors: list[SyscallPartitionDiagnostic] = []
    seen: set[tuple[str, int]] = set()
    for event in rows:
        identities = (event.event_id, event.batch_id, event.raw_segment_id, event.run_id, event.boot_id,
                      event.session_id, event.container_id, event.process_scope_id, event.capture_group_id,
                      event.collector_id, event.filter_id, event.kernel_id, event.abi_id, event.schema_id,
                      event.partition_id, event.source_identity, event.quality_id, event.exclusion_policy_id)
        if not all(_immutable(immutable_resolver, identity) for identity in identities):
            errors.append(SyscallPartitionDiagnostic("SPV1_EVENT_REFERENCE_UNRESOLVED", event.event_id))
        if not event.categorical_name or not event.direction or not event.timestamp or event.sequence < 0:
            errors.append(SyscallPartitionDiagnostic("SPV1_EVENT_CATEGORICAL_FIELDS_INVALID", event.event_id))
        key = (event.raw_segment_id, event.sequence)
        if key in seen or event.duplicate:
            errors.append(SyscallPartitionDiagnostic("SPV1_EVENT_DUPLICATE_OR_AMBIGUOUS", event.event_id))
        seen.add(key)
    if errors:
        return _result(errors)
    return tuple(sorted(rows, key=lambda event: (event.run_id, event.raw_segment_id, event.sequence, event.event_id)))


def build_syscall_windows(*, partition: SyscallPartition, events: Iterable[CategoricalSyscallEvent],
                          parameters: SyscallWindowParameters, preprocessing_id: str,
                          immutable_resolver: ImmutableResolver) -> tuple[CategoricalSyscallWindow, ...] | SyscallPartitionValidation:
    """Build complete homogeneous windows, rejecting rather than excluding ambiguity."""
    errors = list(validate_syscall_partition(partition, immutable_resolver=immutable_resolver).diagnostics)
    for identity in (parameters.parameter_evidence_id, parameters.exclusion_policy_id, parameters.loss_policy_id, preprocessing_id):
        if not _immutable(immutable_resolver, identity):
            errors.append(SyscallPartitionDiagnostic("SPV1_WINDOW_REFERENCE_UNRESOLVED", str(identity)))
    if parameters.window_length < 1 or parameters.stride < 1 or parameters.padding != "none":
        errors.append(SyscallPartitionDiagnostic("SPV1_WINDOW_PARAMETERS_INVALID", parameters.parameter_evidence_id))
    canonical = canonicalize_categorical_syscalls(events, immutable_resolver=immutable_resolver)
    if isinstance(canonical, SyscallPartitionValidation):
        errors.extend(canonical.diagnostics)
        return _result(errors)
    members = {member.run_id: member for member in partition.members}
    for event in canonical:
        member = members.get(event.run_id)
        if member is None or event.partition_id != partition.partition_id or event.schema_id != partition.feature_schema_id:
            errors.append(SyscallPartitionDiagnostic("SPV1_EVENT_PARTITION_MISMATCH", event.event_id))
        elif (event.boot_id, event.session_id, event.container_id, event.process_scope_id, event.capture_group_id) != (
                member.boot_id, member.session_id, member.container_id, member.process_scope_id, member.capture_group_id):
            errors.append(SyscallPartitionDiagnostic("SPV1_EVENT_CAPTURE_SCOPE_MISMATCH", event.event_id))
        elif event.batch_id not in member.batch_ids:
            errors.append(SyscallPartitionDiagnostic("SPV1_EVENT_BATCH_UNDECLARED", event.event_id))
    if errors:
        return _result(errors)
    windows: list[CategoricalSyscallWindow] = []
    start = 0
    while start < len(canonical):
        candidate = canonical[start:start + parameters.window_length]
        if len(candidate) < parameters.window_length:
            break
        first = candidate[0]
        boundary = (first.run_id, first.boot_id, first.session_id, first.container_id, first.process_scope_id,
                    first.capture_group_id, first.raw_segment_id, first.batch_id, first.collector_id, first.filter_id,
                    first.kernel_id, first.abi_id, first.schema_id, first.partition_id, first.exclusion_policy_id)
        contiguous = all(event.sequence == first.sequence + index and not (index and (event.gap_before or event.loss_boundary_before))
                         and (event.run_id, event.boot_id, event.session_id, event.container_id, event.process_scope_id,
                              event.capture_group_id, event.raw_segment_id, event.batch_id, event.collector_id, event.filter_id,
                              event.kernel_id, event.abi_id, event.schema_id, event.partition_id, event.exclusion_policy_id) == boundary
                         for index, event in enumerate(candidate))
        if not contiguous:
            return _result((SyscallPartitionDiagnostic("SPV1_WINDOW_BOUNDARY_CROSSING", first.event_id),))
        windows.append(CategoricalSyscallWindow(
            window_id=f"{first.run_id}:{first.raw_segment_id}:{first.sequence}:{candidate[-1].sequence}",
            source_run_id=first.run_id, event_ids=tuple(event.event_id for event in candidate),
            batch_ids=tuple(event.batch_id for event in candidate), raw_segment_ids=tuple(event.raw_segment_id for event in candidate),
            event_start=first.sequence, event_end=candidate[-1].sequence, partition_id=partition.partition_id,
            feature_schema_id=partition.feature_schema_id, preprocessing_id=preprocessing_id,
            quality_ids=tuple(event.quality_id for event in candidate), exclusion_ids=(first.exclusion_policy_id,),
        ))
        start += parameters.stride
    return tuple(windows)


def validate_syscall_preprocessing_fit(fit: SyscallPreprocessingFit, *, partition: SyscallPartition,
                                       immutable_resolver: ImmutableResolver) -> SyscallPartitionValidation:
    """Permit fitting state only from the exact declared normal training run closure."""
    errors: list[SyscallPartitionDiagnostic] = []
    if not validate_syscall_partition(partition, immutable_resolver=immutable_resolver).accepted:
        errors.append(SyscallPartitionDiagnostic("SPV1_FIT_PARTITION_INVALID", fit.preprocessing_id))
    allowed = {member.run_id for member in partition.members if str(member.role) == "train" and member.normal_eligible}
    if not fit.training_run_ids or set(fit.training_run_ids) != allowed or not fit.training_event_ids:
        errors.append(SyscallPartitionDiagnostic("SPV1_FIT_TRAINING_CLOSURE_INVALID", fit.preprocessing_id))
    if fit.partition_id != partition.partition_id or fit.schema_id != partition.feature_schema_id:
        errors.append(SyscallPartitionDiagnostic("SPV1_FIT_PARTITION_OR_SCHEMA_MISMATCH", fit.preprocessing_id))
    if fit.authorization_effect != "none":
        errors.append(SyscallPartitionDiagnostic("SPV1_FIT_AUTHORIZATION_EFFECT", fit.preprocessing_id))
    identities = (fit.preprocessing_id, fit.partition_id, *fit.training_run_ids, *fit.training_event_ids, fit.schema_id,
                  fit.vocabulary_id, fit.vocabulary_mapping_hash, fit.frequency_state_hash, fit.unknown_event_policy_id,
                  fit.algorithm_id, *fit.parameter_evidence_ids, fit.code_id, fit.output_hash)
    if not all(_immutable(immutable_resolver, identity) for identity in identities):
        errors.append(SyscallPartitionDiagnostic("SPV1_FIT_REFERENCE_UNRESOLVED", fit.preprocessing_id))
    return _result(errors)
