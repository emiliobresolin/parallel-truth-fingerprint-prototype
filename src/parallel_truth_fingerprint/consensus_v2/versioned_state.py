"""Pure, fail-closed versioned state contracts for Consensus v1 and v2.

These records deliberately do not read or write an ABCI store.  They make the
identity that a future state/query/replay boundary must preserve explicit, so a
caller cannot silently decode v1 bytes as v2 (or select a ``latest`` route).
"""
from __future__ import annotations

import hashlib
import json
import re
from dataclasses import dataclass
from enum import StrEnum
from types import MappingProxyType
from typing import Any, Mapping

from parallel_truth_fingerprint.contracts.scientific_governance import is_immutable_id


V1_CONSENSUS_SCHEMA = "Consensus.v1"
V2_CONSENSUS_SCHEMA = "Consensus.v2"
V2_TO_V1_PROJECTION_SCHEMA = "ConsensusV2ToV1Projection.v1"
_VERSIONS = {"v1": V1_CONSENSUS_SCHEMA, "v2": V2_CONSENSUS_SCHEMA}
_HASH = re.compile(r"sha256:[0-9a-f]{64}\Z")


class VersionedConsensusStateError(ValueError):
    """A stable, bounded reason why versioned-state qualification failed."""

    def __init__(self, code: str) -> None:
        self.code = code
        super().__init__(code)


def _identity(value: object, code: str) -> str:
    if not isinstance(value, str) or not is_immutable_id(value):
        raise VersionedConsensusStateError(code)
    return value


def _hash(value: object, code: str) -> str:
    if not isinstance(value, str) or not _HASH.fullmatch(value):
        raise VersionedConsensusStateError(code)
    return value


def _canonical(value: Mapping[str, Any]) -> bytes:
    return json.dumps(value, sort_keys=True, separators=(",", ":"), ensure_ascii=True, allow_nan=False).encode("ascii")


def _frozen(value: Mapping[str, Any]) -> Mapping[str, Any]:
    return MappingProxyType(dict(value))


@dataclass(frozen=True)
class VersionedConsensusState:
    """An immutable state byte record whose route and decoder are explicit."""

    contract_version: str
    schema_identity: str
    storage_key: str
    height: int
    app_hash: str
    state_bytes: bytes
    state_sha256: str
    state_id: str

    def __post_init__(self) -> None:
        expected = _VERSIONS.get(self.contract_version)
        if expected is None:
            raise VersionedConsensusStateError("VCS_UNKNOWN_VERSION")
        if self.schema_identity != expected:
            raise VersionedConsensusStateError("VCS_SCHEMA_VERSION_MISMATCH")
        if not isinstance(self.storage_key, str) or not self.storage_key.startswith(f"consensus/{self.contract_version}/"):
            raise VersionedConsensusStateError("VCS_STORAGE_KEY")
        if type(self.height) is not int or self.height < 0:
            raise VersionedConsensusStateError("VCS_HEIGHT")
        _hash(self.app_hash, "VCS_APP_HASH")
        if not isinstance(self.state_bytes, bytes) or not self.state_bytes:
            raise VersionedConsensusStateError("VCS_STATE_BYTES")
        expected_hash = "sha256:" + hashlib.sha256(self.state_bytes).hexdigest()
        if self.state_sha256 != expected_hash:
            raise VersionedConsensusStateError("VCS_STATE_HASH")
        _identity(self.state_id, "VCS_STATE_ID")
        identity = versioned_state_id(self.contract_version, self.schema_identity, self.storage_key, self.height, self.app_hash, self.state_sha256)
        if self.state_id != identity:
            raise VersionedConsensusStateError("VCS_STATE_ID_HASH")


def versioned_state_id(contract_version: str, schema_identity: str, storage_key: str, height: int, app_hash: str, state_sha256: str) -> str:
    """Return the deterministic content identity excluding the state bytes."""
    payload = {"contract_version": contract_version, "schema_identity": schema_identity, "storage_key": storage_key, "height": height, "app_hash": app_hash, "state_sha256": state_sha256}
    return "sha256:" + hashlib.sha256(_canonical(payload)).hexdigest()


@dataclass(frozen=True)
class VersionedQuery:
    """A version-selected query; aliases and implicit/default versions are invalid."""

    contract_version: str
    schema_identity: str
    storage_key: str

    def __post_init__(self) -> None:
        expected = _VERSIONS.get(self.contract_version)
        if expected is None:
            raise VersionedConsensusStateError("VCQ_UNKNOWN_VERSION")
        if self.schema_identity != expected:
            raise VersionedConsensusStateError("VCQ_SCHEMA_VERSION_MISMATCH")
        if not isinstance(self.storage_key, str) or not self.storage_key.startswith(f"consensus/{self.contract_version}/"):
            raise VersionedConsensusStateError("VCQ_STORAGE_KEY")


@dataclass(frozen=True)
class VersionedQueryResponse:
    contract_version: str
    schema_identity: str
    state: VersionedConsensusState | None
    status: str


def resolve_versioned_query(query: VersionedQuery, records: tuple[VersionedConsensusState, ...]) -> VersionedQueryResponse:
    """Resolve exactly one qualified record, never decoding across versions."""
    matches = tuple(item for item in records if item.contract_version == query.contract_version and item.schema_identity == query.schema_identity and item.storage_key == query.storage_key)
    if len(matches) > 1:
        raise VersionedConsensusStateError("VCQ_AMBIGUOUS_STATE")
    return VersionedQueryResponse(query.contract_version, query.schema_identity, matches[0] if matches else None, "found" if matches else "missing")


@dataclass(frozen=True)
class V2ToV1Projection:
    """A separately versioned, one-way compatibility projection.

    ``projected_fields`` contains only explicitly supplied facts.  It is an
    evidence descriptor, not a converter that guesses absent v2 facts.
    """

    projection_schema: str
    source_v2_state_id: str
    target_v1_schema_identity: str
    projected_fields: Mapping[str, str]
    projection_id: str

    def __post_init__(self) -> None:
        if self.projection_schema != V2_TO_V1_PROJECTION_SCHEMA or self.target_v1_schema_identity != V1_CONSENSUS_SCHEMA:
            raise VersionedConsensusStateError("VCP_SCHEMA")
        _identity(self.source_v2_state_id, "VCP_SOURCE_ID")
        if not isinstance(self.projected_fields, Mapping) or not self.projected_fields or any(not isinstance(k, str) or not k or not isinstance(v, str) or not v for k, v in self.projected_fields.items()):
            raise VersionedConsensusStateError("VCP_FIELDS")
        object.__setattr__(self, "projected_fields", _frozen(self.projected_fields))
        expected = "sha256:" + hashlib.sha256(_canonical({"projection_schema": self.projection_schema, "source_v2_state_id": self.source_v2_state_id, "target_v1_schema_identity": self.target_v1_schema_identity, "projected_fields": dict(self.projected_fields)})).hexdigest()
        if self.projection_id != expected:
            raise VersionedConsensusStateError("VCP_ID")


@dataclass(frozen=True)
class RestartQualification:
    """Pinned identities and a complete replay result for one restart claim."""

    code_identity: str
    runtime_identity: str
    requested_state_ids: tuple[str, ...]
    reconstructed_state_ids: tuple[str, ...]
    status: str

    def __post_init__(self) -> None:
        _identity(self.code_identity, "VCR_CODE_IDENTITY")
        _identity(self.runtime_identity, "VCR_RUNTIME_IDENTITY")
        for item in self.requested_state_ids + self.reconstructed_state_ids:
            _identity(item, "VCR_STATE_ID")
        if self.requested_state_ids != self.reconstructed_state_ids or self.status != "qualified":
            raise VersionedConsensusStateError("VCR_REPLAY_MISMATCH")


def qualify_restart(code_identity: object, runtime_identity: object, expected: tuple[VersionedConsensusState, ...], reconstructed: tuple[VersionedConsensusState, ...]) -> RestartQualification:
    """Purely qualify exact replay identity; corrupt or reordered state fails."""
    _identity(code_identity, "VCR_CODE_IDENTITY")
    _identity(runtime_identity, "VCR_RUNTIME_IDENTITY")
    expected_ids = tuple(item.state_id for item in expected)
    actual_ids = tuple(item.state_id for item in reconstructed)
    return RestartQualification(str(code_identity), str(runtime_identity), expected_ids, actual_ids, "qualified")


@dataclass(frozen=True)
class ConsensusRoundEvidence:
    """Immutable references required to reconstruct a v2 round without aliases."""

    round_id: str
    participant_ids: tuple[str, ...]
    ranking_ids: tuple[str, ...]
    exclusion_ids: tuple[str, ...]
    input_id: str
    parameter_id: str
    code_identity: str
    runtime_identity: str
    state_id: str
    decision_id: str
    log_id: str

    def __post_init__(self) -> None:
        for item in (self.round_id, self.input_id, self.parameter_id, self.code_identity, self.runtime_identity, self.state_id, self.decision_id, self.log_id) + self.participant_ids + self.ranking_ids + self.exclusion_ids:
            _identity(item, "VCE_IMMUTABLE_ID")
        if self.participant_ids != tuple(sorted(set(self.participant_ids))) or set(self.ranking_ids).difference(self.participant_ids):
            raise VersionedConsensusStateError("VCE_PARTICIPANT_CLOSURE")


class RollbackStatus(StrEnum):
    ROUTED = "routed"


@dataclass(frozen=True)
class RollbackEvidence:
    """An authorization-backed route selection; it never mutates stored data."""

    authorization_id: str
    from_version: str
    to_version: str
    prior_verified_state_id: str
    rollback_id: str
    status: RollbackStatus = RollbackStatus.ROUTED

    def __post_init__(self) -> None:
        _identity(self.authorization_id, "VCRB_AUTHORIZATION")
        _identity(self.prior_verified_state_id, "VCRB_STATE_ID")
        if self.from_version not in _VERSIONS or self.to_version not in _VERSIONS or self.from_version == self.to_version:
            raise VersionedConsensusStateError("VCRB_VERSION")
        expected = "sha256:" + hashlib.sha256(_canonical({"authorization_id": self.authorization_id, "from_version": self.from_version, "to_version": self.to_version, "prior_verified_state_id": self.prior_verified_state_id})).hexdigest()
        if self.rollback_id != expected:
            raise VersionedConsensusStateError("VCRB_ID")
