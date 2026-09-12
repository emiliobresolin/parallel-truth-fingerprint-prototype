"""Focused non-domain tests for Story 9.6 immutable manifest contracts."""

from __future__ import annotations

import hashlib
import subprocess
import sys
import unittest
from dataclasses import replace
from pathlib import Path

from parallel_truth_fingerprint.contracts.evidence_manifest import (
    AccessClass,
    ArtifactManifest,
    BindingDisposition,
    BindingSlot,
    BundleManifest,
    EvaluationResult,
    ExecutionOutcome,
    FindingDisposition,
    ImmutableReference,
    MetricRecord,
    ProvenanceEdge,
    ProvenanceRelation,
    RequirementProfile,
    RunManifest,
)
from parallel_truth_fingerprint.evidence.manifests import (
    artifact_manifest_identity,
    bundle_manifest_identity,
    canonical_manifest_bytes,
    alias_resolution_identity,
    evaluation_result_identity,
    manifest_contract_set_bytes,
    manifest_contract_set_identity,
    publish_manifest_last,
    resolve_alias,
    verify_alias_stable,
    validate_dependency_closure,
    run_manifest_identity,
    validate_artifact_manifest,
    validate_bundle_manifest,
    validate_evaluation_result,
    validate_run_manifest,
)


class _WriteOnceRepository:
    def __init__(self) -> None:
        self.items: dict[str, bytes] = {}

    def snapshot_id(self) -> str:
        return "snapshot:sentinel"

    def conditional_create(self, key: str, content: bytes) -> bool:
        if key in self.items:
            if self.items[key] != content:
                raise ValueError("conflict")
            return False
        self.items[key] = content
        return True

    def read(self, key: str, snapshot_id: str) -> bytes | None:
        return self.items.get(key) if snapshot_id == self.snapshot_id() else None


class _FailOnSecondWriteRepository(_WriteOnceRepository):
    def conditional_create(self, key: str, content: bytes) -> bool:
        if len(self.items) == 1:
            raise OSError("injected failure")
        return super().conditional_create(key, content)


class EvidenceManifestContractTests(unittest.TestCase):
    def _reference(self, revision: str = "sha256:" + "1" * 64) -> ImmutableReference:
        return ImmutableReference(
            revision_id=revision,
            serialized_sha256="sha256:" + "2" * 64,
            subject_sha256="sha256:" + "3" * 64,
            contract_id="sentinel.contract",
            contract_version="v1",
            locator="repo:sentinel/object",
            evidence_role="fixture_test",
        )

    def _artifact(self) -> ArtifactManifest:
        manifest = ArtifactManifest(
            logical_artifact_id="artifact:sentinel",
            manifest_revision_id="",
            content_sha256="sha256:" + hashlib.sha256(b"sentinel").hexdigest(),
            byte_size=8,
            evidence_identity={"identity_id": "semantic:fixture:sentinel:v1"},
            access_class=AccessClass.DETECTOR_FACING,
            contract_id="sentinel.contract",
            contract_version="v1",
            schema_id="sha256:" + "4" * 64,
            schema_sha256="sha256:" + "5" * 64,
            media_type="application/octet-stream",
            locator="repo:sentinel/object",
            created_at="2026-09-08T12:00:00.000000Z",
            producer_activity_id="activity:sentinel",
            producer_agent_id="agent:sentinel",
            tool_identity="tool:sentinel",
            code_identity="sha256:" + "6" * 64,
            dependency_lock_sha256="sha256:" + "7" * 64,
            runtime_identity="runtime:sentinel",
            source_use_ids=(),
            provenance_edges=(ProvenanceEdge(
                ProvenanceRelation.WAS_GENERATED_BY, self._reference(), "sentinel.contract", "v1",
                "sha256:" + "3" * 64, "fixture_test",
            ),),
            limitations=("Non-domain sentinel.",),
        )
        return replace(manifest, manifest_revision_id=artifact_manifest_identity(manifest))

    def test_artifact_identity_is_canonical_and_metadata_sensitive(self) -> None:
        artifact = self._artifact()
        self.assertEqual(artifact.manifest_revision_id, artifact_manifest_identity(artifact))
        self.assertTrue(canonical_manifest_bytes(artifact).endswith(b"\n"))
        changed = replace(artifact, media_type="application/json", manifest_revision_id="")
        self.assertNotEqual(artifact.manifest_revision_id, artifact_manifest_identity(changed))
        self.assertEqual(validate_artifact_manifest(artifact, b"sentinel"), ())
        source_bound = replace(artifact, source_use_ids=("use:missing",), manifest_revision_id="")
        source_bound = replace(source_bound, manifest_revision_id=artifact_manifest_identity(source_bound))
        self.assertIn("MANIFEST-SOURCE-USE-UNRESOLVED", {
            item.rule_id for item in validate_artifact_manifest(
                source_bound, b"sentinel", permitted_source_uses=frozenset()
            )
        })

    def test_machine_contract_set_is_identity_addressed_and_canonical(self) -> None:
        identity = manifest_contract_set_identity()
        path = Path("docs/evidence/manifests/v1/contracts") / (
            "sha256-" + identity.removeprefix("sha256:")
        ) / "manifest-contract-set.v1.json"
        self.assertEqual(path.read_bytes(), manifest_contract_set_bytes())
        result = subprocess.run(
            [sys.executable, "scripts/validate_evidence_manifests.py", "--contract-set", str(path), "--machine"],
            capture_output=True, text=True, check=False,
        )
        self.assertEqual(result.returncode, 0, result.stdout + result.stderr)
        self.assertIn('"valid":true', result.stdout)

    def test_documentation_freezes_the_cross_story_ownership_boundary(self) -> None:
        documentation = Path("docs/evidence-manifests-v1.md").read_text(encoding="utf-8")
        for owner in (
            "Story 9.6", "Story 9.7", "Story 9.8", "Later owning stories",
            "Story 17B", "Epic 18",
        ):
            with self.subTest(owner=owner):
                self.assertIn(owner, documentation)

    def test_artifact_rejects_noncanonical_time_alias_and_content_drift(self) -> None:
        artifact = self._artifact()
        bad = replace(artifact, created_at="2026-09-08T12:00:00Z")
        self.assertIn("MANIFEST-TIMESTAMP-INVALID", {item.rule_id for item in validate_artifact_manifest(bad, b"sentinel")})
        alias = replace(artifact, locator="repo:sentinel/latest")
        self.assertIn("MANIFEST-LOCATOR-MUTABLE", {item.rule_id for item in validate_artifact_manifest(alias, b"sentinel")})
        self.assertIn("MANIFEST-CONTENT-HASH-MISMATCH", {item.rule_id for item in validate_artifact_manifest(artifact, b"changed")})
        secret_locator = replace(artifact, locator="object:bucket/item?token=not-for-identity")
        secret_violations = validate_artifact_manifest(secret_locator, b"sentinel")
        self.assertIn("MANIFEST-LOCATOR-MUTABLE", {item.rule_id for item in secret_violations})
        self.assertNotIn("not-for-identity", str([item.to_dict() for item in secret_violations]))
        for unsafe_locator in (
            "repo://double", "repo:/absolute", "repo:./relative", "repo:folder/../escape",
            "repo:.", "repo:folder/.", "repo:folder//child",
            "repo:folder/control\nname", "repo:folder/control\x1fname",
            "object:C:/drive", "oci:sha256:" + "A" * 64,
        ):
            with self.subTest(locator=unsafe_locator):
                unsafe = replace(artifact, locator=unsafe_locator)
                self.assertIn("MANIFEST-LOCATOR-MUTABLE", {
                    item.rule_id for item in validate_artifact_manifest(unsafe, b"sentinel")
                })
        mismatched_edge = replace(artifact.provenance_edges[0], expected_contract_version="v2")
        provenance_bad = replace(artifact, provenance_edges=(mismatched_edge,))
        self.assertIn("MANIFEST-PROVENANCE-MISMATCH", {
            item.rule_id for item in validate_artifact_manifest(provenance_bad, b"sentinel")
        })

    def test_artifact_rejects_unknown_access_and_direct_truth_taint(self) -> None:
        artifact = self._artifact()
        unknown_access = replace(artifact, access_class="unclassified")
        self.assertIn("MANIFEST-ACCESS-INVALID", {
            item.rule_id for item in validate_artifact_manifest(unknown_access, b"sentinel")
        })
        truth_reference = replace(self._reference(), contract_id="truth.unlock.v1")
        truth_edge = replace(artifact.provenance_edges[0], target=truth_reference)
        tainted = replace(artifact, provenance_edges=(truth_edge,))
        self.assertIn("MANIFEST-TRUTH-TAINT", {
            item.rule_id for item in validate_artifact_manifest(tainted, b"sentinel")
        })

    def test_artifact_requires_complete_producer_lineage(self) -> None:
        artifact = self._artifact()
        incomplete = replace(artifact, producer_agent_id="")
        self.assertIn("MANIFEST-PRODUCER-LINEAGE-INCOMPLETE", {
            item.rule_id for item in validate_artifact_manifest(incomplete, b"sentinel")
        })

    def test_artifact_rejects_transitive_truth_taint_with_injected_resolver(self) -> None:
        artifact = self._artifact()
        direct = artifact.provenance_edges[0].target
        truth = replace(self._reference("sha256:" + "a" * 64), contract_id="truth.unlock.v1")
        rules = {item.rule_id for item in validate_artifact_manifest(
            artifact, b"sentinel", dependency_resolver=lambda revision: {
                direct.revision_id: (truth,), truth.revision_id: (),
            }.get(revision),
        )}
        self.assertIn("MANIFEST-TRUTH-TAINT", rules)

    def test_diagnostics_are_bounded_without_hashing_secrets(self) -> None:
        artifact = self._artifact()
        oversized = replace(artifact, locator="x" * 10_000)
        violation = next(item for item in validate_artifact_manifest(oversized, b"sentinel")
                         if item.rule_id == "MANIFEST-LOCATOR-MUTABLE")
        self.assertRegex(violation.observed_value, r"^sha256:[0-9a-f]{64}$")
        secret = replace(artifact, locator="object:bucket/item?token=private")
        secret_violation = next(item for item in validate_artifact_manifest(secret, b"sentinel")
                                if item.rule_id == "MANIFEST-LOCATOR-MUTABLE")
        self.assertEqual(secret_violation.observed_value, "[REDACTED]")

    def test_run_requires_closed_slots_and_blocks_unavailable_slot(self) -> None:
        run = RunManifest(
            logical_run_id="run:sentinel", manifest_revision_id="",
            run_kind="sentinel", requirement_profile=self._reference(),
            bindings=(BindingSlot("dataset", BindingDisposition.UNAVAILABLE_BLOCKING, None, "not collected"),),
            access_class=AccessClass.DETECTOR_FACING,
            created_at="2026-09-08T12:00:00.000000Z", limitations=("No execution.",),
        )
        run = replace(run, manifest_revision_id=run_manifest_identity(run))
        self.assertIn("MANIFEST-RUN-BLOCKED", {item.rule_id for item in validate_run_manifest(run)})
        invalid_time = replace(run, created_at="2026-09-08T12:00:00Z")
        self.assertIn("MANIFEST-TIMESTAMP-INVALID", {item.rule_id for item in validate_run_manifest(invalid_time)})

    def test_run_profile_closes_required_and_not_applicable_slots(self) -> None:
        profile_ref = self._reference()
        profile = RequirementProfile(
            "profile:sentinel", profile_ref.revision_id, ("dataset", "runtime"), ("runtime",), (),
            ("Test-only profile.",),
        )
        run = RunManifest(
            "run:profile", "", "sentinel", profile_ref,
            (BindingSlot("dataset", BindingDisposition.BOUND, self._reference("sha256:" + "d" * 64), None),
             BindingSlot("runtime", BindingDisposition.NOT_APPLICABLE, None, "no runtime for sentinel")),
            AccessClass.DETECTOR_FACING, "2026-09-08T12:00:00.000000Z", ("No execution.",),
        )
        run = replace(run, manifest_revision_id=run_manifest_identity(run))
        self.assertEqual(validate_run_manifest(run, profiles={profile_ref.revision_id: profile}), ())

    def test_bundle_composition_requires_immutable_bound_components(self) -> None:
        bundle = BundleManifest(
            logical_bundle_id="bundle:sentinel", manifest_revision_id="",
            requirement_profile=self._reference(), modality="physical",
            component_artifacts=(BindingSlot("weights", BindingDisposition.BOUND, None, None),),
            access_class=AccessClass.DETECTOR_FACING,
            created_at="2026-09-08T12:00:00.000000Z", limitations=("No model loaded.",),
            package_content_sha256=None,
        )
        bundle = replace(bundle, manifest_revision_id=bundle_manifest_identity(bundle))
        self.assertIn("MANIFEST-SLOT-UNBOUND", {item.rule_id for item in validate_bundle_manifest(bundle)})

    def test_bundle_profile_closes_component_applicability(self) -> None:
        profile_ref = self._reference()
        profile = RequirementProfile(
            "profile:bundle", profile_ref.revision_id, ("weights", "architecture"), ("package",), (),
            ("Test-only bundle profile.",),
        )
        bundle = BundleManifest(
            "bundle:profile", "", profile_ref, "physical",
            (BindingSlot("weights", BindingDisposition.BOUND, self._reference("sha256:" + "d" * 64), None),
             BindingSlot("package", BindingDisposition.NOT_APPLICABLE, None, "unpackaged sentinel")),
            AccessClass.DETECTOR_FACING, "2026-09-08T12:00:00.000000Z", ("No model loaded.",), None,
        )
        bundle = replace(bundle, manifest_revision_id=bundle_manifest_identity(bundle))
        rules = {item.rule_id for item in validate_bundle_manifest(
            bundle, profiles={profile_ref.revision_id: profile},
        )}
        self.assertIn("MANIFEST-BUNDLE-SLOT-MISSING", rules)

    def test_bundle_rejects_non_detector_modality(self) -> None:
        bundle = BundleManifest(
            "bundle:modality", "", self._reference(), "fusion",
            (BindingSlot("weights", BindingDisposition.BOUND, self._reference(), None),),
            AccessClass.DETECTOR_FACING, "2026-09-08T12:00:00.000000Z", ("Sentinel only.",), None,
        )
        bundle = replace(bundle, manifest_revision_id=bundle_manifest_identity(bundle))
        self.assertIn("MANIFEST-BUNDLE-MODALITY-INVALID", {
            item.rule_id for item in validate_bundle_manifest(bundle)
        })

    def test_complete_evaluation_requires_restricted_future_truth_bindings(self) -> None:
        result = EvaluationResult(
            logical_evaluation_id="evaluation:sentinel", manifest_revision_id="",
            dataset_family="sentinel", dataset_version="v1", native_scope="not_applicable",
            track="sentinel", modality_or_result_kind="physical", requirement_profile=self._reference(),
            support_set=self._reference("sha256:" + "8" * 64), run_references=(self._reference(),),
            bindings=(BindingSlot("score_artifact", BindingDisposition.BOUND, self._reference(), None),),
            metrics=(), execution_outcome=ExecutionOutcome.COMPLETE,
            finding_disposition=FindingDisposition.UNFAVORABLE,
            access_class=AccessClass.EVALUATOR_RESTRICTED,
            created_at="2026-09-08T12:00:00.000000Z", limitations=("Sentinel only.",),
            final_output=None,
        )
        result = replace(result, manifest_revision_id=evaluation_result_identity(result))
        rules = {item.rule_id for item in validate_evaluation_result(result)}
        self.assertTrue({"MANIFEST-EVALUATION-INCOMPLETE", "MANIFEST-METRICS-MISSING"}.issubset(rules))

    def test_metrics_and_cross_dataset_fusion_fail_closed(self) -> None:
        result = EvaluationResult(
            "evaluation:fusion", "", "ADFA-LD", "v1", "native", "benchmark", "fusion",
            self._reference(), self._reference("sha256:" + "8" * 64), (self._reference(),), (),
            (MetricRecord(self._reference("sha256:" + "f" * 64), "point", "higher", "one", None,
                          None, None, None),), ExecutionOutcome.ABORTED,
            FindingDisposition.INCONCLUSIVE, AccessClass.EVALUATOR_RESTRICTED,
            "2026-09-08T12:00:00.000000Z", ("No execution.",), None,
        )
        result = replace(result, manifest_revision_id=evaluation_result_identity(result))
        rules = {item.rule_id for item in validate_evaluation_result(result)}
        self.assertTrue({"MANIFEST-METRIC-AVAILABILITY-MISSING", "MANIFEST-FUSION-DATASET-INCOMPATIBLE"}.issubset(rules))

    def test_custom_fusion_requires_paired_modality_run_bindings(self) -> None:
        result = EvaluationResult(
            "evaluation:custom-fusion", "", "PTFP-Custom-v1", "v1", "native", "custom", "fusion",
            self._reference(), self._reference("sha256:" + "8" * 64), (self._reference(),),
            (BindingSlot("score_artifact", BindingDisposition.BOUND, self._reference(), None),), (),
            ExecutionOutcome.ABORTED, FindingDisposition.INCONCLUSIVE,
            AccessClass.EVALUATOR_RESTRICTED, "2026-09-08T12:00:00.000000Z", ("Sentinel only.",), None,
        )
        result = replace(result, manifest_revision_id=evaluation_result_identity(result))
        self.assertIn("MANIFEST-FUSION-PAIRING-INCOMPLETE", {
            item.rule_id for item in validate_evaluation_result(result)
        })

    def test_evaluation_profile_closes_required_slots_and_metrics(self) -> None:
        profile_ref = self._reference()
        profile = RequirementProfile(
            "profile:evaluation", profile_ref.revision_id, ("score_artifact", "partition_freeze"), (),
            ("sha256:" + "e" * 64,), ("Test-only evaluation profile.",),
        )
        result = EvaluationResult(
            "evaluation:profile", "", "sentinel", "v1", "not_applicable", "sentinel", "physical",
            profile_ref, self._reference("sha256:" + "8" * 64), (self._reference(),),
            (BindingSlot("score_artifact", BindingDisposition.BOUND, self._reference(), None),),
            (MetricRecord(self._reference("sha256:" + "f" * 64), "point", "higher", "one", "1",
                          self._reference(), None, None),),
            ExecutionOutcome.ABORTED, FindingDisposition.INCONCLUSIVE,
            AccessClass.EVALUATOR_RESTRICTED, "2026-09-08T12:00:00.000000Z", ("Sentinel only.",), None,
        )
        result = replace(result, manifest_revision_id=evaluation_result_identity(result))
        rules = {item.rule_id for item in validate_evaluation_result(
            result, profiles={profile_ref.revision_id: profile},
        )}
        self.assertIn("MANIFEST-EVALUATION-SLOT-MISSING", rules)
        self.assertIn("MANIFEST-METRIC-DEFINITION-UNREGISTERED", rules)

    def test_alias_resolution_and_manifest_last_receipt_are_immutable(self) -> None:
        reference = self._reference()
        resolved = resolve_alias(
            "release:sentinel", snapshot_id="snapshot:sentinel",
            resolver=lambda alias, snapshot: reference if (alias, snapshot) == ("release:sentinel", "snapshot:sentinel") else None,
            observed_at="2026-09-08T12:00:00.000000Z",
        )
        self.assertEqual(resolved.resolved_target, reference)
        self.assertEqual(resolved.resolution_id, alias_resolution_identity(resolved))
        verify_alias_stable(resolved, resolver=lambda *_: reference)
        with self.assertRaisesRegex(ValueError, "MANIFEST-ALIAS-MOVED"):
            verify_alias_stable(resolved, resolver=lambda *_: self._reference("sha256:" + "e" * 64))
        with self.assertRaisesRegex(ValueError, "MANIFEST-ALIAS-MUTABLE"):
            resolve_alias("latest", snapshot_id="snapshot:sentinel", resolver=lambda *_: reference,
                          observed_at="2026-09-08T12:00:00.000000Z")
        repository = _WriteOnceRepository()
        receipt = publish_manifest_last(
            repository=repository, snapshot_id="snapshot:sentinel",
            subject_key="objects/sha256-subject", subject_bytes=b"sentinel",
            manifest_key="manifests/sha256-manifest", manifest_bytes=b'{"sentinel":true}\n',
            manifest_revision_id="sha256:" + "9" * 64,
        )
        self.assertTrue(receipt.receipt_id.startswith("sha256:"))
        self.assertEqual(len(repository.items), 3)
        with self.assertRaisesRegex(ValueError, "MANIFEST-PUBLICATION-CONFLICT"):
            publish_manifest_last(
                repository=repository, snapshot_id="snapshot:sentinel",
                subject_key="objects/sha256-subject", subject_bytes=b"different",
                manifest_key="manifests/sha256-other", manifest_bytes=b'{}\n',
                manifest_revision_id="sha256:" + "c" * 64,
            )
        self.assertEqual(len(repository.items), 3)

    def test_interrupted_publication_never_exposes_a_receipt(self) -> None:
        repository = _FailOnSecondWriteRepository()
        with self.assertRaisesRegex(ValueError, "MANIFEST-PUBLICATION-CONFLICT"):
            publish_manifest_last(
                repository=repository, snapshot_id="snapshot:sentinel",
                subject_key="objects/sha256-subject", subject_bytes=b"sentinel",
                manifest_key="manifests/sha256-manifest", manifest_bytes=b'{}\n',
                manifest_revision_id="sha256:" + "9" * 64,
        )
        self.assertEqual(tuple(repository.items), ("objects/sha256-subject",))

    def test_publication_rechecks_referenced_closure_before_receipt(self) -> None:
        repository = _WriteOnceRepository()
        repository.items["objects/sha256-reference"] = b"corrupt"
        with self.assertRaisesRegex(ValueError, "MANIFEST-PUBLICATION-READBACK-FAILED"):
            publish_manifest_last(
                repository=repository, snapshot_id="snapshot:sentinel",
                subject_key="objects/sha256-subject", subject_bytes=b"sentinel",
                manifest_key="manifests/sha256-manifest", manifest_bytes=b'{}\n',
                manifest_revision_id="sha256:" + "9" * 64,
                referenced_objects=(("objects/sha256-reference", b"expected"),),
            )
        self.assertEqual(set(repository.items), {"objects/sha256-reference", "objects/sha256-subject", "manifests/sha256-manifest"})

    def test_dependency_closure_rejects_cycle_missing_target_and_truth_taint(self) -> None:
        root = self._reference()
        truth = self._reference("sha256:" + "a" * 64)
        truth = replace(truth, contract_id="truth.unlock.v1")
        cycle = self._reference("sha256:" + "b" * 64)
        graph = {
            root.revision_id: (truth, cycle),
            cycle.revision_id: (root,),
        }
        rules = {item.rule_id for item in validate_dependency_closure(
            root, resolver=lambda revision: graph.get(revision), detector_facing=True,
        )}
        self.assertTrue({"MANIFEST-TRUTH-TAINT", "MANIFEST-NONFORMAL-TAINT", "MANIFEST-GRAPH-CYCLE", "MANIFEST-GRAPH-TARGET-MISSING"}.issubset(rules))

    def test_dependency_closure_rejects_duplicate_divergent_identity(self) -> None:
        root = self._reference()
        duplicate = self._reference("sha256:" + "a" * 64)
        divergent = replace(duplicate, serialized_sha256="sha256:" + "b" * 64)
        graph = {root.revision_id: (duplicate, divergent), duplicate.revision_id: ()}
        rules = {item.rule_id for item in validate_dependency_closure(
            root, resolver=lambda revision: graph.get(revision), detector_facing=False,
        )}
        self.assertIn("MANIFEST-GRAPH-DUPLICATE-DIVERGENT", rules)


if __name__ == "__main__":
    unittest.main()
