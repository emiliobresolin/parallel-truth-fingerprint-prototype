"""Offline tests for the separate formal evidence-store adapter."""

from __future__ import annotations

import hashlib
import unittest

from parallel_truth_fingerprint.contracts.evidence_manifest import AccessClass
from parallel_truth_fingerprint.persistence.evidence_store import (
    EvidenceStoreConflict,
    EvidenceStoreUnavailable,
    FormalEvidenceStore,
    FormalEvidenceStoreConfig,
    FormalNamespacePolicy,
)
from parallel_truth_fingerprint.contracts.evidence_storage import ObjectLockState, VersioningState


class ConditionalClient:
    def __init__(self) -> None:
        self.objects: dict[tuple[str, str], bytes] = {}
        self.last_get: dict[str, object] | None = None

    def put_object(self, **kwargs):
        key = (kwargs["Bucket"], kwargs["Key"])
        if key in self.objects and kwargs.get("IfNoneMatch") == "*":
            raise RuntimeError("PreconditionFailed")
        self.objects[key] = kwargs["Body"]
        return {"VersionId": "v1", "ETag": "not-a-content-digest"}

    def get_object(self, **kwargs):
        self.last_get = kwargs
        return {"Body": _Body(self.objects[(kwargs["Bucket"], kwargs["Key"])]), "VersionId": "v1", "ETag": "not-a-content-digest"}


class _Body:
    def __init__(self, data: bytes) -> None:
        self.data = data

    def read(self) -> bytes:
        return self.data


class EvidenceStoreTests(unittest.TestCase):
    def setUp(self) -> None:
        self.client = ConditionalClient()
        self.store = FormalEvidenceStore(
            FormalEvidenceStoreConfig(
                endpoint_url="http://127.0.0.1:19000",
                bucket="ptfp-formal-evidence-v1",
                namespace_policy_revision="evidence-namespace-policy.v1",
            ), client=self.client,
        )

    def test_key_is_code_owned_content_addressed_and_rejects_unsafe_roles(self) -> None:
        content = b"PTFP-STORAGE-QUALIFICATION-SENTINEL-V1"
        key = self.store.key_for(AccessClass.DETECTOR_FACING, "artifact", content)

        self.assertEqual(
            "formal/v1/detector-facing/artifact/sha256-" + hashlib.sha256(content).hexdigest(), key,
        )
        with self.assertRaises(ValueError):
            self.store.key_for("../../truth", "artifact", content)
        with self.assertRaises(ValueError):
            self.store.key_for(AccessClass.DETECTOR_FACING, "latest", content)

    def test_all_access_classes_use_distinct_closed_roots(self) -> None:
        content = b"PTFP-STORAGE-QUALIFICATION-SENTINEL-V1"
        keys = {
            role: self.store.key_for(role, "artifact", content)
            for role in AccessClass
        }
        self.assertIn("/detector-facing/", keys[AccessClass.DETECTOR_FACING])
        self.assertIn("/evaluator-restricted/", keys[AccessClass.EVALUATOR_RESTRICTED])
        self.assertIn("/public-reference/", keys[AccessClass.PUBLIC_REFERENCE])
        self.assertEqual(3, len(set(keys.values())))

    def test_conditional_create_readback_is_idempotent_only_for_identical_bytes(self) -> None:
        content = b"PTFP-STORAGE-QUALIFICATION-SENTINEL-V1"
        first = self.store.create(AccessClass.DETECTOR_FACING, "artifact", content)
        self.assertEqual("v1", self.client.last_get["VersionId"])
        retry = self.store.create(AccessClass.DETECTOR_FACING, "artifact", content)

        self.assertTrue(first.created)
        self.assertFalse(retry.created)
        self.assertEqual(first.content_sha256, retry.content_sha256)
        altered = b"different sentinel"
        altered_key = self.store.key_for(AccessClass.DETECTOR_FACING, "artifact", altered)
        self.client.objects[(self.store.config.bucket, altered_key)] = b"wrong preexisting bytes"
        with self.assertRaises(EvidenceStoreConflict):
            self.store.create(AccessClass.DETECTOR_FACING, "artifact", altered)

    def test_unavailable_backend_exposes_only_stable_redacted_reason(self) -> None:
        class UnavailableClient:
            def put_object(self, **kwargs):
                raise RuntimeError("access_key=unsafe secret=unsafe")

        store = FormalEvidenceStore(self.store.config, client=UnavailableClient())
        with self.assertRaisesRegex(EvidenceStoreUnavailable, "STORAGE-CONDITIONAL-CREATE-UNAVAILABLE") as raised:
            store.create(AccessClass.PUBLIC_REFERENCE, "artifact", b"non-domain")
        self.assertNotIn("unsafe", str(raised.exception))

    def test_bucket_observations_are_explicit_and_not_write_authority(self) -> None:
        class BucketClient(ConditionalClient):
            def get_bucket_versioning(self, **kwargs): return {"Status": "Enabled"}
            def get_object_lock_configuration(self, **kwargs): return {"ObjectLockConfiguration": {"ObjectLockEnabled": "Enabled"}}
        store = FormalEvidenceStore(self.store.config, client=BucketClient())
        observation = store.observe_bucket()
        self.assertEqual(VersioningState.ENABLED, observation.versioning_state)
        self.assertEqual(ObjectLockState.ENABLED, observation.object_lock_state)
        self.assertEqual("none", observation.authorization_effect)


if __name__ == "__main__":
    unittest.main()
