"""Separate, write-once S3 adapter for formally qualified evidence only.

This module intentionally does not share the legacy MinIO or filesystem store
surface.  It uses the public Boto3 ``IfNoneMatch='*'`` request parameter and
never substitutes a HEAD-then-PUT sequence for atomic creation.
"""

from __future__ import annotations

from dataclasses import dataclass
import hashlib
import re
from typing import Any

from parallel_truth_fingerprint.contracts.evidence_manifest import AccessClass
from parallel_truth_fingerprint.contracts.evidence_storage import (
    CapabilityState, ObjectLockState, RolePrefixPolicy, StorageObjectObservation, VersioningState,
)


_SHA256 = re.compile(r"[0-9a-f]{64}\Z")
_OBJECT_ROLES = frozenset({"artifact", "manifest", "receipt", "snapshot"})


class EvidenceStoreConflict(RuntimeError):
    """A key is already occupied by unequal bytes or an unsafe backend state."""


class EvidenceStoreUnavailable(RuntimeError):
    """The formal endpoint could not provide a trustworthy response."""


@dataclass(frozen=True)
class FormalEvidenceStoreConfig:
    endpoint_url: str
    bucket: str
    namespace_policy_revision: str
    region_name: str = "us-east-1"


class FormalNamespacePolicy:
    """Code-owned, versioned mapping from Story 9.2 access classes to prefixes."""

    REVISION = "evidence-namespace-policy.v1"
    _PREFIXES = {
        AccessClass.DETECTOR_FACING.value: (RolePrefixPolicy.DETECTOR_FACING, "detector-facing"),
        AccessClass.EVALUATOR_RESTRICTED.value: (RolePrefixPolicy.EVALUATOR_RESTRICTED, "evaluator-restricted"),
        AccessClass.PUBLIC_REFERENCE.value: (RolePrefixPolicy.PUBLIC_REFERENCE, "public-reference"),
    }

    @classmethod
    def key_for(cls, access_class: AccessClass | str, object_role: str, content: bytes) -> str:
        access_token = str(access_class)
        if access_token not in cls._PREFIXES or object_role not in _OBJECT_ROLES:
            raise ValueError("STORAGE-NAMESPACE-INVALID")
        prefix = cls._PREFIXES[access_token][1]
        digest = hashlib.sha256(content).hexdigest()
        return f"formal/v1/{prefix}/{object_role}/sha256-{digest}"

    @classmethod
    def policy_for(cls, access_class: AccessClass | str) -> RolePrefixPolicy:
        try:
            return cls._PREFIXES[str(access_class)][0]
        except KeyError as exc:
            raise ValueError("STORAGE-NAMESPACE-INVALID") from exc


@dataclass(frozen=True)
class FormalWriteResult:
    created: bool
    immutable_key: str
    content_sha256: str
    byte_size: int
    backend_version_id: str | None
    backend_etag: str | None
    role_prefix_policy: RolePrefixPolicy
    authorization_effect: str = "none"

    def observation(self) -> StorageObjectObservation:
        return StorageObjectObservation(
            immutable_key=self.immutable_key,
            role_prefix_policy=self.role_prefix_policy,
            byte_size=self.byte_size,
            content_sha256=self.content_sha256,
            backend_version_id=self.backend_version_id,
            backend_etag=self.backend_etag,
            capability_state=CapabilityState.PROVEN,
        )


@dataclass(frozen=True)
class BucketObservation:
    versioning_state: VersioningState
    object_lock_state: ObjectLockState
    authorization_effect: str = "none"


class FormalEvidenceStore:
    """Narrow injected-client adapter which fails closed on uncertain writes."""

    def __init__(self, config: FormalEvidenceStoreConfig, *, client: Any | None = None) -> None:
        if config.namespace_policy_revision != FormalNamespacePolicy.REVISION:
            raise ValueError("STORAGE-NAMESPACE-REVISION-UNQUALIFIED")
        if not config.endpoint_url or not config.bucket or any(token in config.bucket.casefold() for token in ("legacy", "latest")):
            raise ValueError("STORAGE-CONFIG-UNSAFE")
        self.config = config
        self._client = client

    def key_for(self, access_class: AccessClass | str, object_role: str, content: bytes) -> str:
        return FormalNamespacePolicy.key_for(access_class, object_role, content)

    def create(self, access_class: AccessClass | str, object_role: str, content: bytes) -> FormalWriteResult:
        key = self.key_for(access_class, object_role, content)
        digest = "sha256:" + hashlib.sha256(content).hexdigest()
        policy = FormalNamespacePolicy.policy_for(access_class)
        try:
            response = self._client_or_create().put_object(
                Bucket=self.config.bucket, Key=key, Body=content, IfNoneMatch="*",
            )
        except Exception as exc:
            if self._is_precondition_failure(exc):
                return self._existing_or_conflict(key, content, digest, policy)
            raise EvidenceStoreUnavailable("STORAGE-CONDITIONAL-CREATE-UNAVAILABLE") from exc
        return self._readback(key, content, digest, policy, created=True, response=response)

    def read(self, immutable_key: str) -> bytes:
        if not immutable_key.startswith("formal/v1/") or ".." in immutable_key or "\\" in immutable_key:
            raise ValueError("STORAGE-KEY-UNSAFE")
        try:
            return self._client_or_create().get_object(Bucket=self.config.bucket, Key=immutable_key)["Body"].read()
        except Exception as exc:
            raise EvidenceStoreUnavailable("STORAGE-READ-UNAVAILABLE") from exc

    def observe_bucket(self) -> BucketObservation:
        """Record backend configuration as observation, never as write authority."""
        client = self._client_or_create()
        try:
            versioning = client.get_bucket_versioning(Bucket=self.config.bucket)
            versioning_state = VersioningState.ENABLED if versioning.get("Status") == "Enabled" else VersioningState.DISABLED
        except Exception as exc:
            raise EvidenceStoreUnavailable("STORAGE-VERSIONING-OBSERVATION-UNAVAILABLE") from exc
        try:
            lock = client.get_object_lock_configuration(Bucket=self.config.bucket)
            enabled = lock.get("ObjectLockConfiguration", {}).get("ObjectLockEnabled") == "Enabled"
            lock_state = ObjectLockState.ENABLED if enabled else ObjectLockState.DISABLED
        except Exception as exc:
            text = str(exc).casefold()
            if "notfound" in text or "nosuchobjectlockconfiguration" in text:
                lock_state = ObjectLockState.DISABLED
            else:
                raise EvidenceStoreUnavailable("STORAGE-OBJECT-LOCK-OBSERVATION-UNAVAILABLE") from exc
        return BucketObservation(versioning_state, lock_state)

    def _existing_or_conflict(self, key: str, content: bytes, digest: str, policy: RolePrefixPolicy) -> FormalWriteResult:
        try:
            return self._readback(key, content, digest, policy, created=False, response=None)
        except EvidenceStoreConflict:
            raise
        except EvidenceStoreUnavailable as exc:
            raise EvidenceStoreUnavailable("STORAGE-CONFLICT-AMBIGUOUS") from exc

    def _readback(self, key: str, content: bytes, digest: str, policy: RolePrefixPolicy, *, created: bool, response: Any | None) -> FormalWriteResult:
        try:
            read_args: dict[str, object] = {"Bucket": self.config.bucket, "Key": key}
            if response is not None and response.get("VersionId"):
                read_args["VersionId"] = response["VersionId"]
            observed = self._client_or_create().get_object(**read_args)
            actual = observed["Body"].read()
        except Exception as exc:
            raise EvidenceStoreUnavailable("STORAGE-READBACK-UNAVAILABLE") from exc
        if actual != content or "sha256:" + hashlib.sha256(actual).hexdigest() != digest:
            raise EvidenceStoreConflict("STORAGE-CONFLICT-CONTENT-MISMATCH")
        metadata = response or observed
        return FormalWriteResult(
            created=created, immutable_key=key, content_sha256=digest, byte_size=len(actual),
            backend_version_id=metadata.get("VersionId"), backend_etag=metadata.get("ETag"),
            role_prefix_policy=policy,
        )

    def _client_or_create(self) -> Any:
        if self._client is not None:
            return self._client
        try:
            import boto3
        except ImportError as exc:
            raise EvidenceStoreUnavailable("STORAGE-BOTO3-DEPENDENCY-MISSING") from exc
        self._client = boto3.client("s3", endpoint_url=self.config.endpoint_url, region_name=self.config.region_name)
        return self._client

    @staticmethod
    def _is_precondition_failure(exc: Exception) -> bool:
        text = str(exc).casefold()
        response = getattr(exc, "response", None)
        code = "" if not isinstance(response, dict) else str(response.get("Error", {}).get("Code", "")).casefold()
        return "precondition" in text or code in {"preconditionfailed", "412"}
