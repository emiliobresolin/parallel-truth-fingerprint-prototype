"""Immutable input contracts for the offline Story 10.6 run-admission gate.

These contracts describe a request and observed stream facts only.  They do
not command equipment, read a clock, write a repository, or publish evidence.
"""

from __future__ import annotations

from dataclasses import dataclass
from enum import StrEnum


class ExecutionModality(StrEnum):
    ENGINEERING_MODEL = "engineering_model"
    ADMITTED_EMULATOR = "admitted_emulator"
    PHYSICAL_HARDWARE = "physical_hardware"


class StreamStatus(StrEnum):
    COMPLETE = "complete"
    INCOMPLETE = "incomplete"


@dataclass(frozen=True)
class RunScopeProjection:
    """A non-published run binding; explicitly neither manifest nor receipt."""

    projection_id: str
    experiment_spec_id: str
    matrix_row_id: str
    run_binding_id: str
    input_trace_id: str
    authorization_effect: str = "none"


@dataclass(frozen=True)
class StreamRequirement:
    stream_id: str
    edge_id: str
    sensor_id: str
    first_sequence: int
    last_sequence: int


@dataclass(frozen=True)
class PhysicalRunRequest:
    request_id: str
    projection: RunScopeProjection
    modality: ExecutionModality | str
    profile_revision_id: str
    parameter_gate_result_id: str
    repository_qualification_id: str
    authorization_ids: tuple[str, str]
    stream_requirements: tuple[StreamRequirement, ...]
    physical_acquisition_authorization_id: str | None = None
    authorization_effect: str = "none"

    def __post_init__(self) -> None:
        object.__setattr__(self, "authorization_ids", tuple(self.authorization_ids))
        object.__setattr__(self, "stream_requirements", tuple(self.stream_requirements))


@dataclass(frozen=True)
class StreamRecord:
    """Caller-supplied canonical observation bytes, retained without projection."""

    stream_id: str
    edge_id: str
    sensor_id: str
    source_sequence: int
    canonical_bytes: bytes
    content_sha256: str
