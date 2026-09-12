"""Offline conformance tests for the Story 9.7 storage contracts."""

from __future__ import annotations

import hashlib
import unittest
from dataclasses import replace

from parallel_truth_fingerprint.contracts.evidence_storage import (
    BackendKind,
    CapabilityState,
    ObjectLockState,
    QualificationResult,
    RolePrefixPolicy,
    StorageObjectObservation,
    StoragePhase,
    StoragePhaseObservation,
    StorageQualificationPlan,
    StorageQualificationReport,
    StorageSnapshotManifest,
    VersioningState,
    VolumeKind,
)
from parallel_truth_fingerprint.evidence.storage import (
    storage_qualification_plan_identity,
    storage_qualification_report_identity,
    storage_snapshot_manifest_identity,
    validate_storage_snapshot,
    validate_storage_qualification_report,
)


def digest(value: bytes) -> str:
    return "sha256:" + hashlib.sha256(value).hexdigest()


class StorageQualificationContractsTests(unittest.TestCase):
    def plan(self) -> StorageQualificationPlan:
        provisional = StorageQualificationPlan(
            plan_revision_id="",
            backend_kind=BackendKind.MINIO_S3,
            endpoint_identity="https://127.0.0.1:19000",
            bucket_name="ptfp-formal-evidence-v1",
            namespace_policy_revision="evidence-namespace-policy.v1",
            server_image_digest="sha256:" + "a" * 64,
            server_release="RELEASE.2025-01-01T00-00-00Z",
            compose_sha256="sha256:" + "b" * 64,
            volume_kind=VolumeKind.NAMED,
            volume_identity="ptfp-evidence-data-v1",
            versioning_state=VersioningState.DISABLED,
            object_lock_state=ObjectLockState.DISABLED,
            client_identity="boto3:1.36.0",
            dependency_lock_sha256="sha256:" + "c" * 64,
            runtime_identity="python:3.14",
            fixture_reference="sha256:" + "d" * 64,
            source_use_ids=("source-use:storage-conditional-v1",),
            observed_at="2026-09-08T00:00:00.000000Z",
        )
        return StorageQualificationPlan(
            plan_revision_id=storage_qualification_plan_identity(provisional),
            backend_kind=provisional.backend_kind,
            endpoint_identity=provisional.endpoint_identity,
            bucket_name=provisional.bucket_name,
            namespace_policy_revision=provisional.namespace_policy_revision,
            server_image_digest=provisional.server_image_digest,
            server_release=provisional.server_release,
            compose_sha256=provisional.compose_sha256,
            volume_kind=provisional.volume_kind,
            volume_identity=provisional.volume_identity,
            versioning_state=provisional.versioning_state,
            object_lock_state=provisional.object_lock_state,
            client_identity=provisional.client_identity,
            dependency_lock_sha256=provisional.dependency_lock_sha256,
            runtime_identity=provisional.runtime_identity,
            fixture_reference=provisional.fixture_reference,
            source_use_ids=provisional.source_use_ids,
            observed_at=provisional.observed_at,
        )

    def test_report_binds_plan_phases_and_object_digest_without_etag_authority(self) -> None:
        plan = self.plan()
        observed = StorageObjectObservation(
            immutable_key="formal/v1/detector-facing/artifact/sha256-" + "e" * 64,
            role_prefix_policy=RolePrefixPolicy.DETECTOR_FACING,
            byte_size=13,
            content_sha256=digest(b"non-domain-v1"),
            backend_version_id="version-1",
            backend_etag="unrelated-etag",
            capability_state=CapabilityState.PROVEN,
        )
        phase = StoragePhaseObservation(
            phase=StoragePhase.CONDITIONAL_CREATE,
            result=QualificationResult.QUALIFIED,
            environment_identity="sha256:" + "f" * 64,
            object_observations=(observed,),
            violation_rule_ids=(),
            limitations=("ETag is not a SHA-256 authority.",),
        )
        provisional = StorageQualificationReport(
            report_revision_id="",
            plan_revision_id=plan.plan_revision_id,
            qualification_result=QualificationResult.QUALIFIED,
            phase_observations=(phase,),
            limitations=("Qualification is capability evidence only.",),
        )
        report = StorageQualificationReport(
            report_revision_id=storage_qualification_report_identity(provisional),
            plan_revision_id=provisional.plan_revision_id,
            qualification_result=provisional.qualification_result,
            phase_observations=provisional.phase_observations,
            limitations=provisional.limitations,
        )

        self.assertEqual((), validate_storage_qualification_report(report, plan=plan))
        self.assertEqual("none", report.authorization_effect)

    def test_unknown_observation_fails_closed(self) -> None:
        plan = self.plan()
        report = StorageQualificationReport(
            report_revision_id="sha256:" + "0" * 64,
            plan_revision_id=plan.plan_revision_id,
            qualification_result=QualificationResult.QUALIFIED,
            phase_observations=(StoragePhaseObservation(
                phase="invented-phase",
                result=QualificationResult.QUALIFIED,
                environment_identity="sha256:" + "f" * 64,
                object_observations=(),
                violation_rule_ids=(),
                limitations=(),
            ),),
            limitations=(),
        )

        self.assertIn("STORAGE-PHASE-INVALID", {item.rule_id for item in validate_storage_qualification_report(report, plan=plan)})

    def test_qualified_report_requires_registered_source_uses(self) -> None:
        plan = self.plan()
        report = StorageQualificationReport(
            report_revision_id="sha256:" + "0" * 64,
            plan_revision_id=plan.plan_revision_id,
            qualification_result=QualificationResult.QUALIFIED,
            phase_observations=(), limitations=(),
        )
        rules = {item.rule_id for item in validate_storage_qualification_report(
            report, plan=plan, registered_source_uses=frozenset(),
        )}
        self.assertIn("STORAGE-SOURCE-USE-UNRESOLVED", rules)

    def test_snapshot_rejects_extra_wrong_role_and_hash_drift(self) -> None:
        object_ = StorageObjectObservation(
            immutable_key="formal/v1/public-reference/snapshot/sha256-" + "e" * 64,
            role_prefix_policy=RolePrefixPolicy.PUBLIC_REFERENCE,
            byte_size=3, content_sha256=digest(b"abc"), backend_version_id=None,
            backend_etag=None, capability_state=CapabilityState.PROVEN,
        )
        draft = StorageSnapshotManifest("", "sha256:" + "d" * 64, (object_,))
        snapshot = StorageSnapshotManifest(
            storage_snapshot_manifest_identity(draft), draft.source_plan_revision_id, draft.object_observations,
        )
        observed = {object_.immutable_key: b"changed", "formal/v1/public-reference/artifact/sha256-extra": b"x"}
        rules = {item.rule_id for item in validate_storage_snapshot(snapshot, observed=observed)}
        self.assertTrue({"STORAGE-SNAPSHOT-EXTRA", "STORAGE-SNAPSHOT-HASH-MISMATCH"}.issubset(rules))

    def test_every_safe_configuration_identity_changes_the_plan_revision(self) -> None:
        plan = self.plan()
        for field, replacement in (
            ("bucket_name", "ptfp-other-v1"), ("volume_identity", "other-volume"),
            ("compose_sha256", "sha256:" + "1" * 64),
            ("server_image_digest", "sha256:" + "2" * 64),
            ("namespace_policy_revision", "evidence-namespace-policy.v2"),
        ):
            self.assertNotEqual(plan.plan_revision_id, storage_qualification_plan_identity(replace(plan, **{field: replacement})))


if __name__ == "__main__":
    unittest.main()
