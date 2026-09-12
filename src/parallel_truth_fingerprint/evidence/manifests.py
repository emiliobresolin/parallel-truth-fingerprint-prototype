"""Pure validation and identities for Story 9.6 manifest records."""

from __future__ import annotations

import hashlib
import json
import re
from collections.abc import Callable

from parallel_truth_fingerprint.contracts.evidence_manifest import (
    AccessClass, AliasResolution, ArtifactManifest, BindingDisposition, BundleManifest, EvaluationResult,
    ExecutionOutcome, ImmutableReference, ManifestViolation, PublicationReceipt, RequirementProfile, RunManifest,
)


_DIGEST = re.compile(r"sha256:[0-9a-f]{64}\Z")
_UTC = re.compile(r"[0-9]{4}-[0-9]{2}-[0-9]{2}T[0-9]{2}:[0-9]{2}:[0-9]{2}\.[0-9]{6}Z\Z")

MANIFEST_CONTRACT_TYPES = (
    "ImmutableReference.v1", "ProvenanceEdge.v1", "BindingSlot.v1", "RequirementProfile.v1",
    "ArtifactManifest.v1", "RunManifest.v1", "BundleManifest.v1",
    "MetricRecord.v1", "EvaluationResult.v1", "AliasResolution.v1",
    "PublicationReceipt.v1", "ManifestViolation.v1",
)


def canonical_manifest_bytes(record: object) -> bytes:
    return (json.dumps(record.to_dict(), sort_keys=True, ensure_ascii=False,
                       separators=(",", ":"), allow_nan=False) + "\n").encode("utf-8")


def manifest_contract_set_bytes() -> bytes:
    return (json.dumps({
        "schema_version": "manifest-contract-set.v1",
        "contract_types": MANIFEST_CONTRACT_TYPES,
        "authorization_effect": "none",
        "limitations": ["Generic structural contracts only; no activity authorization."],
    }, sort_keys=True, ensure_ascii=False, separators=(",", ":"), allow_nan=False) + "\n").encode("utf-8")


def manifest_contract_set_identity() -> str:
    return "sha256:" + hashlib.sha256(manifest_contract_set_bytes()).hexdigest()


def _identity(record: object, field: str) -> str:
    payload = record.to_dict()
    payload[field] = ""
    return "sha256:" + hashlib.sha256(
        (json.dumps(payload, sort_keys=True, ensure_ascii=False, separators=(",", ":"),
                    allow_nan=False) + "\n").encode("utf-8")
    ).hexdigest()


def artifact_manifest_identity(record: ArtifactManifest) -> str:
    return _identity(record, "manifest_revision_id")


def run_manifest_identity(record: RunManifest) -> str:
    return _identity(record, "manifest_revision_id")


def bundle_manifest_identity(record: BundleManifest) -> str:
    return _identity(record, "manifest_revision_id")


def evaluation_result_identity(record: EvaluationResult) -> str:
    return _identity(record, "manifest_revision_id")


def publication_receipt_identity(record: PublicationReceipt) -> str:
    return _identity(record, "receipt_id")


def alias_resolution_identity(record: AliasResolution) -> str:
    return _identity(record, "resolution_id")


def _violation(rule: str, record: str, field: str, expected: object, observed: object, text: str) -> ManifestViolation:
    def bounded(value: object) -> str:
        rendered = str(value).replace("\x00", "[NUL]")
        if any(marker in rendered.casefold() for marker in ("password=", "secret=", "token=", "access_key")):
            return "[REDACTED]"
        return "sha256:" + hashlib.sha256(rendered.encode("utf-8")).hexdigest()
    return ManifestViolation(rule, bounded(record), field, bounded(expected), bounded(observed), text)


def _immutable_locator(locator: str) -> bool:
    lowered = locator.casefold()
    if not locator or any(token in lowered for token in (
        "latest", "current", "@", "?", "#", "password=", "secret=", "token=", "access_key",
    )):
        return False
    if ".." in locator or "\\" in locator or any(ord(character) < 32 for character in locator):
        return False
    def root_relative_body(prefix: str) -> bool:
        if locator.count(":") != 1:
            return False
        body = locator.removeprefix(prefix)
        segments = body.split("/")
        return (
            bool(body)
            and not body.startswith(("/", "./", "../"))
            and all(segment not in {"", ".", ".."} for segment in segments)
        )

    if locator.startswith("repo:"):
        return root_relative_body("repo:")
    if locator.startswith("object:"):
        return root_relative_body("object:")
    if locator.startswith("oci:sha256:"):
        return bool(_DIGEST.fullmatch(locator.removeprefix("oci:")))
    return False


def validate_artifact_manifest(
    record: ArtifactManifest,
    content: bytes,
    *,
    permitted_source_uses: frozenset[str] | None = None,
    dependency_resolver: Callable[[str], tuple[ImmutableReference, ...] | None] | None = None,
) -> tuple[ManifestViolation, ...]:
    violations: list[ManifestViolation] = []
    if str(record.access_class) not in {item.value for item in AccessClass}:
        violations.append(_violation("MANIFEST-ACCESS-INVALID", record.logical_artifact_id,
                                     "access_class", "closed access class", record.access_class,
                                     "Manifest roots use a closed audience vocabulary."))
    if record.manifest_revision_id != artifact_manifest_identity(record):
        violations.append(_violation("MANIFEST-REVISION-MISMATCH", record.logical_artifact_id,
                                     "manifest_revision_id", artifact_manifest_identity(record),
                                     record.manifest_revision_id, "Revision must bind immutable fields."))
    if not _UTC.fullmatch(record.created_at):
        violations.append(_violation("MANIFEST-TIMESTAMP-INVALID", record.logical_artifact_id,
                                     "created_at", "YYYY-MM-DDTHH:MM:SS.ffffffZ", record.created_at,
                                     "Creation time is a frozen lexical identity input."))
    if not _immutable_locator(record.locator):
        violations.append(_violation("MANIFEST-LOCATOR-MUTABLE", record.logical_artifact_id,
                                     "locator", "qualified immutable locator", record.locator,
                                     "Aliases and unsafe locators are forbidden."))
    lineage_fields = (
        record.producer_activity_id, record.producer_agent_id, record.tool_identity,
        record.code_identity, record.dependency_lock_sha256, record.runtime_identity,
    )
    if not all(isinstance(value, str) and value for value in lineage_fields):
        violations.append(_violation("MANIFEST-PRODUCER-LINEAGE-INCOMPLETE", record.logical_artifact_id,
                                     "producer_lineage", "activity/agent/tool/code/lock/runtime identities",
                                     "missing", "Formal artifacts require complete immutable producer lineage."))
    observed = "sha256:" + hashlib.sha256(content).hexdigest()
    if len(content) != record.byte_size or observed != record.content_sha256:
        violations.append(_violation("MANIFEST-CONTENT-HASH-MISMATCH", record.logical_artifact_id,
                                     "content", f"{record.byte_size}|{record.content_sha256}",
                                     f"{len(content)}|{observed}", "Opaque bytes must match declaration."))
    if not all(_DIGEST.fullmatch(value) for value in (record.content_sha256, record.schema_id, record.schema_sha256,
                                                       record.code_identity, record.dependency_lock_sha256)):
        violations.append(_violation("MANIFEST-DIGEST-INVALID", record.logical_artifact_id,
                                     "identity", "lowercase sha256 digest", "invalid", "Digest tokens are closed."))
    for edge in record.provenance_edges:
        if (edge.target.contract_id != edge.expected_contract_id
                or edge.target.contract_version != edge.expected_contract_version
                or (edge.expected_subject_sha256 is not None
                    and edge.target.subject_sha256 != edge.expected_subject_sha256)
                or edge.target.evidence_role != edge.expected_evidence_role):
            violations.append(_violation("MANIFEST-PROVENANCE-MISMATCH", record.logical_artifact_id,
                                         "provenance_edges", "declared target contract/version/hash",
                                         edge.target.contract_id + "|" + edge.target.contract_version,
                                         "Each typed edge binds the expected immutable target shape."))
        if (str(record.access_class) == AccessClass.DETECTOR_FACING.value
                and edge.target.contract_id.startswith("truth.")):
            violations.append(_violation("MANIFEST-TRUTH-TAINT", record.logical_artifact_id,
                                         "provenance_edges", "no restricted truth dependency",
                                         edge.target.contract_id,
                                         "Detector-facing roots cannot reference truth evidence."))
    if permitted_source_uses is not None:
        for source_use_id in record.source_use_ids:
            if source_use_id not in permitted_source_uses:
                violations.append(_violation("MANIFEST-SOURCE-USE-UNRESOLVED", record.logical_artifact_id,
                                             "source_use_ids", "registered Story 9.3 source use", source_use_id,
                                             "Manifest validity never infers source or license lineage."))
    if dependency_resolver is not None:
        for edge in record.provenance_edges:
            violations.extend(validate_dependency_closure(
                edge.target,
                resolver=dependency_resolver,
                detector_facing=str(record.access_class) == AccessClass.DETECTOR_FACING.value,
            ))
    return tuple(sorted(violations, key=lambda item: (item.rule_id, item.field_path)))


def validate_run_manifest(
    record: RunManifest,
    *,
    profiles: dict[str, RequirementProfile] | None = None,
) -> tuple[ManifestViolation, ...]:
    violations: list[ManifestViolation] = []
    if record.manifest_revision_id != run_manifest_identity(record):
        violations.append(_violation("MANIFEST-REVISION-MISMATCH", record.logical_run_id,
                                     "manifest_revision_id", run_manifest_identity(record),
                                     record.manifest_revision_id, "Revision must bind immutable fields."))
    if not _UTC.fullmatch(record.created_at):
        violations.append(_violation("MANIFEST-TIMESTAMP-INVALID", record.logical_run_id,
                                     "created_at", "YYYY-MM-DDTHH:MM:SS.ffffffZ", record.created_at,
                                     "Creation time is a frozen lexical identity input."))
    if str(record.access_class) not in {item.value for item in AccessClass}:
        violations.append(_violation("MANIFEST-ACCESS-INVALID", record.logical_run_id,
                                     "access_class", "closed access class", record.access_class,
                                     "Manifest roots use a closed audience vocabulary."))
    names = [item.name for item in record.bindings]
    if len(names) != len(set(names)) or not names:
        violations.append(_violation("MANIFEST-RUN-SLOTS-INVALID", record.logical_run_id,
                                     "bindings", "unique nonempty slots", names, "Run slots are closed."))
    for slot in record.bindings:
        if str(slot.disposition) == BindingDisposition.UNAVAILABLE_BLOCKING.value:
            violations.append(_violation("MANIFEST-RUN-BLOCKED", record.logical_run_id, f"bindings/{slot.name}",
                                         "bound or approved not_applicable", slot.disposition,
                                         slot.reason or "Unavailable binding remains visible and blocks completion."))
        elif str(slot.disposition) == BindingDisposition.BOUND.value and slot.reference is None:
            violations.append(_violation("MANIFEST-RUN-SLOT-UNBOUND", record.logical_run_id, f"bindings/{slot.name}",
                                         "immutable reference", "missing", "Bound slots require exact references."))
    profile = None if profiles is None else profiles.get(record.requirement_profile.revision_id)
    if profiles is not None and profile is None:
        violations.append(_violation("MANIFEST-PROFILE-UNKNOWN", record.logical_run_id,
                                     "requirement_profile", "registered immutable profile",
                                     record.requirement_profile.revision_id,
                                     "Caller-supplied profiles cannot approve themselves."))
    if profile is not None:
        slots = {item.name: item for item in record.bindings}
        for required in profile.required_slots:
            if required not in slots:
                violations.append(_violation("MANIFEST-RUN-SLOT-MISSING", record.logical_run_id,
                                             f"bindings/{required}", "declared slot", "missing",
                                             "The registered profile requires this binding."))
        for slot in record.bindings:
            if str(slot.disposition) == BindingDisposition.NOT_APPLICABLE.value:
                if slot.name not in profile.not_applicable_slots or not slot.reason:
                    violations.append(_violation("MANIFEST-RUN-NOT-APPLICABLE-INVALID", record.logical_run_id,
                                                 f"bindings/{slot.name}", "profile-approved reason", slot.reason,
                                                 "Not-applicable disposition must be pre-approved by the profile."))
    return tuple(sorted(violations, key=lambda item: (item.rule_id, item.field_path)))


def _validate_slots(record_id: str, slots: tuple, *, prefix: str) -> list[ManifestViolation]:
    violations: list[ManifestViolation] = []
    names = [item.name for item in slots]
    if len(names) != len(set(names)) or not names:
        violations.append(_violation("MANIFEST-SLOTS-INVALID", record_id, prefix,
                                     "unique nonempty slots", names, "Slots are closed and named."))
    for slot in slots:
        if str(slot.disposition) == BindingDisposition.BOUND.value and slot.reference is None:
            violations.append(_violation("MANIFEST-SLOT-UNBOUND", record_id, f"{prefix}/{slot.name}",
                                         "immutable reference", "missing", "Bound slots need exact references."))
        if str(slot.disposition) == BindingDisposition.UNAVAILABLE_BLOCKING.value:
            violations.append(_violation("MANIFEST-SLOT-BLOCKED", record_id, f"{prefix}/{slot.name}",
                                         "bound or approved not_applicable", slot.disposition,
                                         slot.reason or "Unavailable binding blocks completion."))
    return violations


def validate_bundle_manifest(
    record: BundleManifest,
    *,
    profiles: dict[str, RequirementProfile] | None = None,
) -> tuple[ManifestViolation, ...]:
    violations = _validate_slots(record.logical_bundle_id, record.component_artifacts, prefix="components")
    if record.modality not in {"physical", "syscall"}:
        violations.append(_violation("MANIFEST-BUNDLE-MODALITY-INVALID", record.logical_bundle_id,
                                     "modality", "physical or syscall", record.modality,
                                     "Fusion is a same-run result kind, not a third detector modality."))
    if record.manifest_revision_id != bundle_manifest_identity(record):
        violations.append(_violation("MANIFEST-REVISION-MISMATCH", record.logical_bundle_id,
                                     "manifest_revision_id", bundle_manifest_identity(record),
                                     record.manifest_revision_id, "Revision must bind composition."))
    if not _UTC.fullmatch(record.created_at):
        violations.append(_violation("MANIFEST-TIMESTAMP-INVALID", record.logical_bundle_id,
                                     "created_at", "YYYY-MM-DDTHH:MM:SS.ffffffZ", record.created_at,
                                     "Creation time is a frozen lexical identity input."))
    if str(record.access_class) not in {AccessClass.DETECTOR_FACING.value, AccessClass.PUBLIC_REFERENCE.value}:
        violations.append(_violation("MANIFEST-BUNDLE-ACCESS-INVALID", record.logical_bundle_id,
                                     "access_class", "detector/public composition", record.access_class,
                                     "Detector bundles cannot be restricted-truth roots."))
    profile = None if profiles is None else profiles.get(record.requirement_profile.revision_id)
    if profiles is not None and profile is None:
        violations.append(_violation("MANIFEST-PROFILE-UNKNOWN", record.logical_bundle_id,
                                     "requirement_profile", "registered immutable profile",
                                     record.requirement_profile.revision_id,
                                     "Caller-supplied profiles cannot approve themselves."))
    if profile is not None:
        components = {slot.name: slot for slot in record.component_artifacts}
        for required in profile.required_slots:
            if required not in components:
                violations.append(_violation("MANIFEST-BUNDLE-SLOT-MISSING", record.logical_bundle_id,
                                             f"components/{required}", "declared component", "missing",
                                             "The registered profile requires this component."))
        for slot in record.component_artifacts:
            if str(slot.disposition) == BindingDisposition.NOT_APPLICABLE.value and (
                slot.name not in profile.not_applicable_slots or not slot.reason
            ):
                violations.append(_violation("MANIFEST-BUNDLE-NOT-APPLICABLE-INVALID", record.logical_bundle_id,
                                             f"components/{slot.name}", "profile-approved reason", slot.reason,
                                             "Not-applicable components must be profile-approved."))
    return tuple(sorted(violations, key=lambda item: (item.rule_id, item.field_path)))


def validate_evaluation_result(
    record: EvaluationResult,
    *,
    profiles: dict[str, RequirementProfile] | None = None,
) -> tuple[ManifestViolation, ...]:
    violations = _validate_slots(record.logical_evaluation_id, record.bindings, prefix="bindings")
    if record.manifest_revision_id != evaluation_result_identity(record):
        violations.append(_violation("MANIFEST-REVISION-MISMATCH", record.logical_evaluation_id,
                                     "manifest_revision_id", evaluation_result_identity(record),
                                     record.manifest_revision_id, "Revision must bind evaluation."))
    if not _UTC.fullmatch(record.created_at):
        violations.append(_violation("MANIFEST-TIMESTAMP-INVALID", record.logical_evaluation_id,
                                     "created_at", "YYYY-MM-DDTHH:MM:SS.ffffffZ", record.created_at,
                                     "Creation time is a frozen lexical identity input."))
    if str(record.access_class) != "evaluator_restricted":
        violations.append(_violation("MANIFEST-EVALUATION-ACCESS-INVALID", record.logical_evaluation_id,
                                     "access_class", "evaluator_restricted", record.access_class,
                                     "Evaluation envelopes are evaluator-only."))
    if str(record.execution_outcome) == ExecutionOutcome.COMPLETE.value:
        required = {"partition_freeze", "truth_unlock", "truth_join", "score_artifact"}
        present = {item.name for item in record.bindings if str(item.disposition) == BindingDisposition.BOUND.value}
        missing = sorted(required - present)
        if missing:
            violations.append(_violation("MANIFEST-EVALUATION-INCOMPLETE", record.logical_evaluation_id,
                                         "bindings", "bound partition/truth/score refs", missing,
                                         "A complete evaluation requires future Story 9.8 references."))
    if not record.metrics and str(record.execution_outcome) == ExecutionOutcome.COMPLETE.value:
        violations.append(_violation("MANIFEST-METRICS-MISSING", record.logical_evaluation_id,
                                     "metrics", "protocol-declared records", "none",
                                     "Complete results cannot fabricate an empty universal metric set."))
    for metric in record.metrics:
        if metric.value is None and not metric.availability_reason:
            violations.append(_violation("MANIFEST-METRIC-AVAILABILITY-MISSING", record.logical_evaluation_id,
                                         "metrics", "value or availability reason", "missing",
                                         "Inapplicable metrics stay explicit rather than becoming zero."))
        if metric.value is not None and (metric.support_reference is None or not metric.direction or not metric.unit):
            violations.append(_violation("MANIFEST-METRIC-IDENTITY-INCOMPLETE", record.logical_evaluation_id,
                                         "metrics", "definition/direction/unit/support", "incomplete",
                                         "Recorded metric values bind their protocol support and direction."))
    if record.modality_or_result_kind == "fusion" and record.dataset_family != "PTFP-Custom-v1":
        violations.append(_violation("MANIFEST-FUSION-DATASET-INCOMPATIBLE", record.logical_evaluation_id,
                                     "dataset_family", "PTFP-Custom-v1 same-run support", record.dataset_family,
                                     "External datasets cannot enter cross-dataset fusion."))
    if record.modality_or_result_kind == "fusion" and record.dataset_family == "PTFP-Custom-v1":
        paired = {
            slot.name for slot in record.bindings
            if str(slot.disposition) == BindingDisposition.BOUND.value and slot.reference is not None
        }
        if not {"physical_run", "syscall_run"}.issubset(paired):
            violations.append(_violation("MANIFEST-FUSION-PAIRING-INCOMPLETE", record.logical_evaluation_id,
                                         "bindings", "bound physical_run and syscall_run",
                                         sorted(paired),
                                         "Custom fusion must bind both same-run modality executions."))
    profile = None if profiles is None else profiles.get(record.requirement_profile.revision_id)
    if profiles is not None and profile is None:
        violations.append(_violation("MANIFEST-PROFILE-UNKNOWN", record.logical_evaluation_id,
                                     "requirement_profile", "registered immutable profile",
                                     record.requirement_profile.revision_id,
                                     "Caller-supplied profiles cannot approve themselves."))
    if profile is not None:
        bindings = {slot.name: slot for slot in record.bindings}
        for required in profile.required_slots:
            if required not in bindings:
                violations.append(_violation("MANIFEST-EVALUATION-SLOT-MISSING", record.logical_evaluation_id,
                                             f"bindings/{required}", "declared evaluation binding", "missing",
                                             "The registered profile requires this binding."))
        for metric in record.metrics:
            if metric.metric_definition.revision_id not in profile.metric_definition_ids:
                violations.append(_violation("MANIFEST-METRIC-DEFINITION-UNREGISTERED",
                                             record.logical_evaluation_id, "metrics/definition",
                                             "profile-registered metric definition",
                                             metric.metric_definition.revision_id,
                                             "Metrics must be selected by the registered profile."))
    return tuple(sorted(violations, key=lambda item: (item.rule_id, item.field_path)))


def resolve_alias(
    alias: str,
    *,
    snapshot_id: str,
    resolver: Callable[[str, str], ImmutableReference | None],
    observed_at: str,
) -> AliasResolution:
    """Resolve exactly once outside formal manifests; bare mutable IDs fail closed."""

    if not alias or any(token in alias.casefold() for token in ("latest", "current", "branch", "tag")):
        raise ValueError("MANIFEST-ALIAS-MUTABLE")
    if not _UTC.fullmatch(observed_at):
        raise ValueError("MANIFEST-TIMESTAMP-INVALID")
    target = resolver(alias, snapshot_id)
    if target is None or not _immutable_locator(target.locator):
        raise ValueError("MANIFEST-ALIAS-UNRESOLVED")
    provisional = AliasResolution("", alias, snapshot_id, target, observed_at)
    return AliasResolution(alias_resolution_identity(provisional), alias, snapshot_id, target, observed_at)


def verify_alias_stable(
    resolution: AliasResolution,
    *,
    resolver: Callable[[str, str], ImmutableReference | None],
) -> None:
    """Require the alias target to remain identical before formal assembly."""

    observed = resolver(resolution.requested_alias, resolution.resolver_snapshot_id)
    if observed != resolution.resolved_target:
        raise ValueError("MANIFEST-ALIAS-MOVED")


def publish_manifest_last(
    *,
    repository,
    snapshot_id: str,
    subject_key: str,
    subject_bytes: bytes,
    manifest_key: str,
    manifest_bytes: bytes,
    manifest_revision_id: str,
    referenced_objects: tuple[tuple[str, bytes], ...] = (),
) -> PublicationReceipt:
    """Injected write-once protocol; only its final receipt marks completeness."""

    required = ("conditional_create", "read", "snapshot_id")
    if any(not hasattr(repository, name) for name in required) or repository.snapshot_id() != snapshot_id:
        raise ValueError("MANIFEST-REPOSITORY-UNQUALIFIED")

    def write_then_verify(key: str, content: bytes) -> None:
        try:
            created = repository.conditional_create(key, content)
        except Exception as exc:
            raise ValueError("MANIFEST-PUBLICATION-CONFLICT") from exc
        read_back = repository.read(key, snapshot_id)
        if read_back != content:
            raise ValueError("MANIFEST-PUBLICATION-READBACK-FAILED")
        if not created and read_back != content:
            raise ValueError("MANIFEST-PUBLICATION-CONFLICT")

    write_then_verify(subject_key, subject_bytes)
    write_then_verify(manifest_key, manifest_bytes)
    for key, expected_bytes in ((subject_key, subject_bytes), (manifest_key, manifest_bytes), *referenced_objects):
        if repository.read(key, snapshot_id) != expected_bytes:
            raise ValueError("MANIFEST-PUBLICATION-READBACK-FAILED")
    receipt = PublicationReceipt(
        "", manifest_revision_id,
        "sha256:" + hashlib.sha256(manifest_bytes).hexdigest(), snapshot_id,
    )
    receipt = PublicationReceipt(
        publication_receipt_identity(receipt), receipt.manifest_revision_id,
        receipt.manifest_serialized_sha256, receipt.repository_snapshot_id,
    )
    receipt_key = "receipts/sha256-" + receipt.receipt_id.removeprefix("sha256:")
    write_then_verify(receipt_key, canonical_manifest_bytes(receipt))
    return receipt


def validate_dependency_closure(
    root: ImmutableReference,
    *,
    resolver: Callable[[str], tuple[ImmutableReference, ...] | None],
    detector_facing: bool,
) -> tuple[ManifestViolation, ...]:
    """Validate a single injected immutable closure without querying ambient state."""

    violations: list[ManifestViolation] = []
    active: set[str] = set()
    visited: set[str] = set()
    resolved: dict[str, ImmutableReference] = {}

    def visit(node: ImmutableReference) -> None:
        prior = resolved.get(node.revision_id)
        if prior is not None and prior != node:
            violations.append(_violation(
                "MANIFEST-GRAPH-DUPLICATE-DIVERGENT", root.revision_id, "dependency",
                "one immutable shape per revision ID", node.revision_id,
                "A revision ID cannot resolve to divergent serialized bytes or metadata.",
            ))
            return
        resolved[node.revision_id] = node
        if node.revision_id in active:
            violations.append(_violation("MANIFEST-GRAPH-CYCLE", root.revision_id,
                                         "dependency", "acyclic closure", node.revision_id,
                                         "Typed provenance may not contain cycles."))
            return
        if node.revision_id in visited:
            return
        if not _DIGEST.fullmatch(node.revision_id) or not _DIGEST.fullmatch(node.serialized_sha256):
            violations.append(_violation("MANIFEST-GRAPH-REFERENCE-INVALID", root.revision_id,
                                         "dependency", "immutable revision and byte hash", node.revision_id,
                                         "Dependency identities are closed lowercase digests."))
            return
        dependencies = resolver(node.revision_id)
        if dependencies is None:
            violations.append(_violation("MANIFEST-GRAPH-TARGET-MISSING", root.revision_id,
                                         "dependency", "resolvable immutable target", node.revision_id,
                                         "The pinned snapshot does not resolve this target."))
            return
        active.add(node.revision_id)
        for child in sorted(dependencies, key=lambda item: item.revision_id):
            if detector_facing and child.contract_id.startswith("truth."):
                violations.append(_violation("MANIFEST-TRUTH-TAINT", root.revision_id,
                                             "dependency", "no restricted truth dependency", child.contract_id,
                                             "Detector-facing roots cannot traverse truth evidence."))
            if detector_facing and child.evidence_role in {"fixture_test", "legacy_v1"}:
                violations.append(_violation("MANIFEST-NONFORMAL-TAINT", root.revision_id,
                                             "dependency", "formal detector evidence", child.evidence_role,
                                             "Fixture replay and legacy evidence cannot promote into formal roots."))
            visit(child)
        active.remove(node.revision_id)
        visited.add(node.revision_id)

    visit(root)
    return tuple(sorted(violations, key=lambda item: (item.rule_id, item.field_path, item.observed_value)))
