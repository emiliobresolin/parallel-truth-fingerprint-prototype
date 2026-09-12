"""Narrow, fail-closed OPC UA v2 read boundary.

The adapter owns no server, writer, cache, consensus object, or fallback value.
Its only input channel is an injected OPC UA client session.  The concrete
``AsyncUaClientSession`` is deliberately thin; tests use ``OfflineOpcUaClient``
and therefore never open a socket.
"""
from __future__ import annotations

import hashlib
import json
import time
from dataclasses import asdict, dataclass
from datetime import datetime, timezone
from typing import Callable, Mapping, Protocol


SCADA_OBSERVATION_V2 = "ScadaObservation.v2"
_REQUIRED_NODES = frozenset({"raw_current_ma", "engineering_value", "revision", "profile", "correlation", "snapshot_ref"})


def _immutable(value: str) -> bool:
    return isinstance(value, str) and value.startswith("sha256:") and len(value) == 71 and all(c in "0123456789abcdef" for c in value[7:])


def _utc_now() -> str:
    return datetime.now(timezone.utc).strftime("%Y-%m-%dT%H:%M:%S.%fZ")


@dataclass(frozen=True)
class OpcUaDataValue:
    """Transport-preserving projection of an OPC UA ``DataValue``."""
    value: str | None
    status_code: str
    source_timestamp: str | None
    server_timestamp: str | None


class OpcUaClientSession(Protocol):
    """The sole runtime seam available to the evidence reader."""
    async def connect(self) -> None: ...
    async def namespace_index(self, namespace_uri: str) -> int: ...
    async def read(self, node_ids: Mapping[str, str]) -> Mapping[str, OpcUaDataValue]: ...
    async def disconnect(self) -> None: ...


@dataclass(frozen=True)
class OpcUaReadRequest:
    endpoint: str
    security_mode: str
    namespace_uri: str
    node_ids: Mapping[str, str]
    experiment_id: str
    run_id: str
    correlation_id: str
    expected_snapshot_ref: str
    expected_profile_ref: str
    enabled: bool = True

    def validate(self) -> None:
        if not self.endpoint.startswith("opc.tcp://") or not self.security_mode or not self.namespace_uri:
            raise ValueError("OPC2-REQUEST-ENDPOINT")
        if set(self.node_ids) != _REQUIRED_NODES or any(not isinstance(v, str) or not v for v in self.node_ids.values()):
            raise ValueError("OPC2-REQUEST-NODES")
        if any(not _immutable(v) for v in (self.experiment_id, self.run_id, self.correlation_id, self.expected_snapshot_ref, self.expected_profile_ref)):
            raise ValueError("OPC2-REQUEST-IDENTITY")


@dataclass(frozen=True)
class ScadaObservationV2:
    """Canonical outcome of one real-client attempt; never a cached reading."""
    schema_version: str
    endpoint: str
    security_mode: str
    namespace_uri: str
    namespace_index: int | None
    node_ids: Mapping[str, str]
    experiment_id: str
    run_id: str
    correlation_id: str
    snapshot_ref: str | None
    profile_ref: str | None
    raw_current_ma: OpcUaDataValue | None
    engineering_value: OpcUaDataValue | None
    attempts: int
    latency_ms: int
    client_observed_timestamp: str
    freshness_evidence: str | None
    blocking_reason: str | None
    error: str | None

    def validate(self) -> None:
        if self.schema_version != SCADA_OBSERVATION_V2 or not self.endpoint.startswith("opc.tcp://"):
            raise ValueError("OPC2-SCHEMA")
        if set(self.node_ids) != _REQUIRED_NODES or self.attempts != 1 or self.latency_ms < 0:
            raise ValueError("OPC2-DIAGNOSTICS")
        if any(not _immutable(v) for v in (self.experiment_id, self.run_id, self.correlation_id)):
            raise ValueError("OPC2-IDENTITY")
        succeeded = self.blocking_reason is None
        if succeeded:
            if not all((self.snapshot_ref, self.profile_ref, self.raw_current_ma, self.engineering_value, self.freshness_evidence)):
                raise ValueError("OPC2-SUCCESS-CLOSURE")
            if any(not _immutable(v) for v in (self.snapshot_ref, self.profile_ref, self.freshness_evidence)):
                raise ValueError("OPC2-SUCCESS-IDENTITY")
        elif any(v is not None for v in (self.snapshot_ref, self.profile_ref, self.raw_current_ma, self.engineering_value, self.freshness_evidence)):
            raise ValueError("OPC2-FAILURE-NO-FABRICATION")

    def canonical_bytes(self) -> bytes:
        self.validate()
        return json.dumps(asdict(self), sort_keys=True, separators=(",", ":"), ensure_ascii=True).encode("ascii")

    def content_id(self) -> str:
        return "sha256:" + hashlib.sha256(self.canonical_bytes()).hexdigest()


def _failure(request: OpcUaReadRequest, reason: str, error: str | None, started: float, now: Callable[[], str]) -> ScadaObservationV2:
    return ScadaObservationV2(SCADA_OBSERVATION_V2, request.endpoint, request.security_mode, request.namespace_uri, None,
        dict(request.node_ids), request.experiment_id, request.run_id, request.correlation_id, None, None, None, None,
        1, max(0, int((time.monotonic() - started) * 1000)), now(), None, reason, error)


async def read_scada_observation(
    request: OpcUaReadRequest,
    session_factory: Callable[[str, str], OpcUaClientSession],
    *, now: Callable[[], str] = _utc_now,
) -> ScadaObservationV2:
    """Use one fresh session and return an explicit result for every outcome."""
    request.validate()
    started = time.monotonic()
    if not request.enabled:
        return _failure(request, "v2_mode_disabled", None, started, now)
    session = session_factory(request.endpoint, request.security_mode)
    connected = False
    try:
        await session.connect(); connected = True
        index = await session.namespace_index(request.namespace_uri)
        values = await session.read(request.node_ids)
        if set(values) != _REQUIRED_NODES:
            return _failure(request, "incomplete_node_read", None, started, now)
        meta = {key: values[key].value for key in ("revision", "profile", "correlation", "snapshot_ref")}
        if (meta["revision"] != request.expected_snapshot_ref or meta["snapshot_ref"] != request.expected_snapshot_ref or
                meta["profile"] != request.expected_profile_ref or meta["correlation"] != request.correlation_id):
            return _failure(request, "mixed_snapshot_identity", None, started, now)
        raw, engineering = values["raw_current_ma"], values["engineering_value"]
        if raw.value is None or engineering.value is None or not raw.status_code or not engineering.status_code:
            return _failure(request, "invalid_datavalue", None, started, now)
        observation = ScadaObservationV2(SCADA_OBSERVATION_V2, request.endpoint, request.security_mode, request.namespace_uri,
            index, dict(request.node_ids), request.experiment_id, request.run_id, request.correlation_id,
            request.expected_snapshot_ref, request.expected_profile_ref, raw, engineering, 1,
            max(0, int((time.monotonic() - started) * 1000)), now(), request.expected_snapshot_ref, None, None)
        observation.validate()
        return observation
    except Exception as exc:  # transport errors become evidence, never substitute a value
        return _failure(request, "client_read_failed", type(exc).__name__, started, now)
    finally:
        if connected:
            try:
                await session.disconnect()
            except Exception:
                pass


class OfflineOpcUaClient:
    """Injected deterministic test fake; it has no network implementation."""
    def __init__(self, values: Mapping[str, OpcUaDataValue], *, namespace_index: int = 2, error: Exception | None = None) -> None:
        self.values, self._namespace_index, self.error = dict(values), namespace_index, error
        self.connected = self.disconnected = False

    async def connect(self) -> None:
        self.connected = True
        if self.error: raise self.error

    async def namespace_index(self, namespace_uri: str) -> int:
        if self.error: raise self.error
        return self._namespace_index

    async def read(self, node_ids: Mapping[str, str]) -> Mapping[str, OpcUaDataValue]:
        if self.error: raise self.error
        return self.values

    async def disconnect(self) -> None:
        self.disconnected = True


class AsyncUaClientSession:
    """Production adapter: creates a distinct ``asyncua.Client`` per request."""
    def __init__(self, endpoint: str, security_mode: str) -> None:
        self._endpoint, self._security_mode, self._client = endpoint, security_mode, None

    async def connect(self) -> None:
        # A security policy/certificate mapping is an authorization-bearing
        # configuration, not a harmless default.  Until one is supplied by the
        # separately configured server boundary, reject it rather than opening
        # an anonymous/insecure session while claiming the requested mode.
        if self._security_mode != "None":
            raise RuntimeError("OPC2-UNSUPPORTED-SECURITY-MODE")
        from asyncua import Client
        self._client = Client(self._endpoint)
        await self._client.connect()

    async def namespace_index(self, namespace_uri: str) -> int:
        assert self._client is not None
        return await self._client.get_namespace_index(namespace_uri)

    async def read(self, node_ids: Mapping[str, str]) -> Mapping[str, OpcUaDataValue]:
        assert self._client is not None
        result: dict[str, OpcUaDataValue] = {}
        for name, node_id in node_ids.items():
            value = await self._client.get_node(node_id).read_data_value()
            result[name] = OpcUaDataValue(
                None if value.Value is None else str(value.Value.Value), str(value.StatusCode),
                None if value.SourceTimestamp is None else value.SourceTimestamp.isoformat(),
                None if value.ServerTimestamp is None else value.ServerTimestamp.isoformat())
        return result

    async def disconnect(self) -> None:
        if self._client is not None:
            await self._client.disconnect()
