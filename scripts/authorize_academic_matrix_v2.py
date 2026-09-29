"""Materialize and time-lock owner-approved Matrix V2 numeric authority.

This utility deliberately separates four irreversible stages:

``authorize``
    Validates an explicit, group-by-group human approval and publishes a new
    requirements inventory, ParameterEvidence.v1 catalog, and candidate config.
``verify``
    Runs the test suite *after* the decision freeze and preserves its output.
``lock-truth``
    Captures a stable, immutable inventory of the official source surface only
    after the post-freeze test lock. Full consumed-content identities remain
    the responsibility of preflight and every admitted cell.
``finalize``
    Builds the strict TemporalGateContext and publishes the runnable frozen
    config only if the independent parameter gate is accountable.

The command never chooses a scientific value.  Its only source of authority is
the supplied immutable owner-approval artifact, whose seven groups must all be
explicitly approved for the exact candidate config and requirements inventory.
"""

from __future__ import annotations

import argparse
from dataclasses import replace
from datetime import datetime, timezone
from decimal import Decimal, InvalidOperation
from hashlib import sha256
import json
import os
from pathlib import Path
import subprocess
import sys
import tempfile
from typing import Any, Mapping


PROJECT_ROOT = Path(__file__).resolve().parents[1]
SRC_ROOT = PROJECT_ROOT / "src"
if str(SRC_ROOT) not in sys.path:
    sys.path.insert(0, str(SRC_ROOT))

from parallel_truth_fingerprint.contracts.parameter_evidence import (  # noqa: E402
    AccountabilityOutcome,
    ApprovalState,
    AuthenticFeasibility,
    CategoryDisposition,
    CategoryState,
    DecisionAuthority,
    DecisionRecord,
    DecisionValue,
    InventoryCategory,
    NumericConsumerInventory,
    NumericValue,
    NumericValueKind,
    ParameterBinding,
    ParameterClass,
    ParameterEvidenceCatalog,
    ParameterRequirement,
    ParameterRevision,
    RecordState,
    RequiredParameterSet,
    TemporalGateContext,
    UncertaintyKind,
    UncertaintyRecord,
    ValueRole,
)
from parallel_truth_fingerprint.contracts.semantic_vocabulary import (  # noqa: E402
    SEMANTIC_VOCABULARY_VERSION,
    SyntheticStatus,
)
from parallel_truth_fingerprint.evidence.parameter_evidence import (  # noqa: E402
    canonical_parameter_catalog_bytes,
    decision_record_identity,
    load_parameter_catalog,
    parameter_catalog_identity,
    parameter_revision_identity,
    source_catalog_identity,
    validate_parameter_gate,
)
from parallel_truth_fingerprint.evidence.source_catalog import (  # noqa: E402
    load_source_catalog,
)
from parallel_truth_fingerprint.lstm_service.offline_training.academic_protocol import (  # noqa: E402
    canonical_json_hash,
)
from parallel_truth_fingerprint.lstm_service.offline_training.academic_runner import (  # noqa: E402
    config_identity,
    load_academic_config,
)
from parallel_truth_fingerprint.lstm_service.offline_training.academic_numeric_schema import (  # noqa: E402
    V2_NUMERIC_SCHEMA_IDENTITY,
    V2_NUMERIC_SCHEMA_VERSION,
)


APPROVAL_SCHEMA = "academic-matrix-v2-owner-approval-v1"
TEST_LOCK_SCHEMA = "academic-matrix-v2-test-lock-v1"
TRUTH_LOCK_SCHEMA = "academic-matrix-v2-truth-lock-v1"
TEMPORAL_CONTEXT_SCHEMA = "academic-matrix-v2-temporal-context-v1"
EXPERIMENT_ID = "thesis-evaluation-v2"
PROFILE_ID = "thesis-evaluation-v2"
EXPERIMENT_SCOPE = "academic-offline-evaluation"
COMPONENT = "academic-offline-evaluation-runner-v2"
QUESTION = (
    "How does the frozen PTF detector matrix perform across official "
    "ADFA-LD, LID-DS-2021, and HAI-23.05 benchmarks?"
)
EVIDENCE_TRACK = "official benchmark evaluation"
FINAL_OUTPUT = "thesis Matrix V2"
DECISION_ID = "decision:thesis-evaluation-v2:interactive-owner-approval-v2"
INVENTORY_ID = "numeric-consumer-inventory:thesis-evaluation-v2"
REQUIRED_SET_ID = "required-parameter-set:thesis-evaluation-v2"
DECISION_SOURCE_USES = (
    "use:std-bipm-si-brochure-9-v4.01-2026:unit-context",
    "use:tool-python-314-decimal:context-and-signals",
)

GROUPS = {
    "1": "compute-governance",
    "2": "randomness-and-execution-schedule",
    "3": "statistical-protocol",
    "4": "validation-role",
    "5": "dataset-allocation-and-support",
    "6": "window-and-preprocessing",
    "7": "model-and-stopping",
}

DEFAULT_APPROVAL = (
    PROJECT_ROOT / "configs" / "experiments" / "thesis-evaluation-v2.approval-v1.json"
)
DEFAULT_CANDIDATE_CONFIG = (
    PROJECT_ROOT / "configs" / "experiments" / "thesis-evaluation-v2.json"
)
DEFAULT_REQUIREMENTS = (
    PROJECT_ROOT
    / "configs"
    / "experiments"
    / "thesis-evaluation-v2.parameter-requirements-v2.3-approved.json"
)
DEFAULT_CATALOG = (
    PROJECT_ROOT
    / "configs"
    / "experiments"
    / "thesis-evaluation-v2.parameter-evidence-v2.json"
)
DEFAULT_AUTHORIZED_CONFIG = (
    PROJECT_ROOT / "configs" / "experiments" / "thesis-evaluation-v2.authorized-v2.json"
)
DEFAULT_TEST_LOCK = (
    PROJECT_ROOT / "evidence" / "academic" / "governance" / "thesis-evaluation-v2-test-lock-v2.json"
)
DEFAULT_TEST_STDOUT = DEFAULT_TEST_LOCK.with_suffix(".stdout.txt")
DEFAULT_TEST_STDERR = DEFAULT_TEST_LOCK.with_suffix(".stderr.txt")
DEFAULT_TRUTH_LOCK = (
    PROJECT_ROOT / "evidence" / "academic" / "governance" / "thesis-evaluation-v2-truth-lock-v2.json"
)
DEFAULT_TEMPORAL_CONTEXT = (
    PROJECT_ROOT
    / "configs"
    / "experiments"
    / "thesis-evaluation-v2.temporal-context-v2.json"
)
DEFAULT_FROZEN_CONFIG = (
    PROJECT_ROOT / "configs" / "experiments" / "thesis-evaluation-v2.frozen-v2.json"
)


def _canonical_bytes(payload: object) -> bytes:
    return (
        json.dumps(payload, sort_keys=True, ensure_ascii=False, separators=(",", ":"), allow_nan=False)
        + "\n"
    ).encode("utf-8")


def _sha256(payload: bytes) -> str:
    return f"sha256:{sha256(payload).hexdigest()}"


def _canonical_decimal(value: object) -> str:
    """Render a JSON numeric literal in ParameterEvidence's canonical decimal form."""

    try:
        decimal = Decimal(str(value))
    except (InvalidOperation, ValueError) as exc:
        raise ValueError(f"Invalid numeric requirements value {value!r}") from exc
    if not decimal.is_finite():
        raise ValueError(f"Non-finite numeric requirements value {value!r}")
    if decimal == 0:
        return "0"
    return format(decimal.normalize(), "f")


def _now() -> str:
    return datetime.now(timezone.utc).isoformat(timespec="microseconds").replace("+00:00", "Z")


def _instant(value: object, *, field: str) -> datetime:
    if not isinstance(value, str) or not value.strip():
        raise ValueError(f"{field} must be a non-empty RFC 3339 timestamp")
    try:
        parsed = datetime.fromisoformat(value.replace("Z", "+00:00"))
    except ValueError as exc:
        raise ValueError(f"{field} is not an RFC 3339 timestamp: {value!r}") from exc
    if parsed.tzinfo is None:
        raise ValueError(f"{field} must include a timezone")
    return parsed.astimezone(timezone.utc)


def _read_json(path: Path) -> dict[str, object]:
    try:
        payload = json.loads(path.read_text(encoding="utf-8"))
    except (OSError, UnicodeError, json.JSONDecodeError) as exc:
        raise ValueError(f"Cannot read JSON artifact {path}: {exc}") from exc
    if not isinstance(payload, dict):
        raise ValueError(f"JSON artifact {path} must be an object")
    return payload


def _publish_immutable(path: Path, payload: bytes) -> None:
    """Atomically create an immutable artifact without replace semantics."""

    path = path.resolve()
    path.parent.mkdir(parents=True, exist_ok=True)
    if path.parent.is_symlink() or path.is_symlink():
        raise ValueError(f"Refusing symlinked immutable artifact path: {path}")
    if path.exists():
        if path.read_bytes() == payload:
            return
        raise ValueError(f"Refusing to replace existing immutable artifact: {path}")
    temporary: Path | None = None
    try:
        with tempfile.NamedTemporaryFile(
            mode="wb", dir=path.parent, prefix=f".{path.name}.", suffix=".tmp", delete=False
        ) as handle:
            temporary = Path(handle.name)
            handle.write(payload)
            handle.flush()
            os.fsync(handle.fileno())
        try:
            os.link(temporary, path)
        except FileExistsError:
            if path.read_bytes() != payload:
                raise ValueError(f"Concurrent immutable artifact conflict: {path}")
    finally:
        if temporary is not None:
            temporary.unlink(missing_ok=True)


def _relative(path: Path) -> str:
    try:
        return path.resolve().relative_to(PROJECT_ROOT.resolve()).as_posix()
    except ValueError as exc:
        raise ValueError(f"Artifact must remain below the project root: {path}") from exc


def _group_for_pointer(pointer: str) -> str:
    if pointer.startswith("/computational_budget/"):
        return "1"
    if pointer.startswith("/pilot_seeds/") or pointer.startswith("/confirmatory_seeds/"):
        return "2"
    if pointer == "/execution_protocol/confirmatory_batch_size":
        return "2"
    if pointer in {
        "/statistical_protocol/bootstrap_seed_offset",
        "/statistical_protocol/comparison_seed",
        "/validation_protocol/split_seed",
    } or pointer.endswith("/partition_seed"):
        return "2"
    if pointer.startswith("/statistical_protocol/"):
        return "3"
    if pointer.startswith("/validation_protocol/"):
        return "4"
    if any(token in pointer for token in ("/phase_allocation/", "/phase_caps/", "/minimum_support/")):
        return "5"
    if pointer.startswith("/datasets/") and (
        "/window/" in pointer
        or pointer.endswith("/numeric_clip")
        or pointer.endswith("/normal_validation_fraction")
        or pointer.endswith("/block_rows")
    ):
        return "6"
    if pointer.startswith("/datasets/") and "/models/" in pointer:
        return "7"
    raise ValueError(f"No explicit owner-decision group exists for numeric consumer {pointer!r}")


def _category_for_pointer(pointer: str, group: str) -> InventoryCategory:
    if group == "1":
        return InventoryCategory.DURATION_RAMP_DWELL_TIMING
    if group == "2":
        return InventoryCategory.REPETITIONS_SEEDS
    if group in {"4", "5"}:
        return InventoryCategory.SPLIT_CALIBRATION
    if group == "6":
        return InventoryCategory.PREPROCESSING_WINDOWS
    if group == "7":
        return InventoryCategory.MODEL_TRAINING_HYPERPARAMETERS_STOPPING
    if pointer.startswith("/statistical_protocol/threshold/"):
        return InventoryCategory.THRESHOLDS
    return InventoryCategory.METRICS_EVALUATION


def _approval_groups(payload: Mapping[str, object]) -> dict[str, Mapping[str, object]]:
    raw_groups = payload.get("groups")
    if not isinstance(raw_groups, list):
        raise ValueError("approval.groups must be an array")
    resolved: dict[str, Mapping[str, object]] = {}
    for item in raw_groups:
        if not isinstance(item, Mapping):
            raise ValueError("approval.groups entries must be objects")
        group_id = item.get("group")
        if not isinstance(group_id, str) or group_id not in GROUPS:
            raise ValueError(f"approval contains unknown group {group_id!r}")
        if group_id in resolved:
            raise ValueError(f"approval contains duplicate group {group_id!r}")
        if item.get("label") != GROUPS[group_id] or item.get("status") != "approved":
            raise ValueError(f"approval group {group_id} is not an exact approved candidate decision")
        resolved[group_id] = item
    if set(resolved) != set(GROUPS):
        missing = sorted(set(GROUPS) - set(resolved))
        raise ValueError(f"approval must separately approve every group; missing {missing}")
    return resolved


def validate_owner_approval(
    approval: Mapping[str, object], config: Mapping[str, object], *, approval_sha256: str
) -> dict[str, Mapping[str, object]]:
    """Reject anything short of a complete, exact owner approval."""

    expected = {
        "schema_version",
        "approval_id",
        "approved_by",
        "approved_at",
        "approval_channel",
        "approval_statement",
        "candidate_config_identity",
        "candidate_requirements_sha256",
        "groups",
        "authorization_effect",
        "limitations",
    }
    if set(approval) != expected:
        raise ValueError("approval artifact has unknown or missing fields")
    if approval.get("schema_version") != APPROVAL_SCHEMA:
        raise ValueError("unsupported owner-approval schema")
    if approval.get("authorization_effect") != "none":
        raise ValueError("approval artifact must not itself grant runtime authorization")
    for field in ("approval_id", "approved_by", "approval_channel", "approval_statement"):
        if not isinstance(approval.get(field), str) or not str(approval[field]).strip():
            raise ValueError(f"approval.{field} must be a non-empty string")
    _instant(approval.get("approved_at"), field="approval.approved_at")
    limitations = approval.get("limitations")
    if not isinstance(limitations, list) or not limitations or not all(
        isinstance(item, str) and item.strip() for item in limitations
    ):
        raise ValueError("approval.limitations must be a non-empty string array")
    if approval.get("candidate_config_identity") != config_identity(config):
        raise ValueError("approval is not bound to this exact candidate config")
    governance = config.get("numeric_authority")
    if not isinstance(governance, Mapping):
        raise ValueError("candidate config lacks numeric_authority")
    if approval.get("candidate_requirements_sha256") != governance.get("requirements_sha256"):
        raise ValueError("approval is not bound to this exact requirements inventory")
    if not approval_sha256.startswith("sha256:"):
        raise ValueError("approval identity must be a SHA-256 digest")
    return _approval_groups(approval)


def _decision(
    slots: list[Mapping[str, object]], approval: Mapping[str, object], *, freeze_time: str, approval_sha256: str
) -> DecisionRecord:
    values: list[DecisionValue] = []
    parameter_ids: list[str] = []
    for slot in slots:
        slot_id = slot["slot_id"]
        if not isinstance(slot_id, str):
            raise ValueError("requirements slot_id must be a string")
        parameter_id = f"academic-v2-parameter:{slot_id.split(':', maxsplit=1)[-1]}"
        parameter_ids.append(parameter_id)
        values.append(
            DecisionValue(
                parameter_id=parameter_id,
                value=NumericValue(
                    kind=NumericValueKind.SCALAR,
                    scalar=_canonical_decimal(slot["value"]),
                ),
                unit=str(slot["unit"]),
                quantity_kind=str(slot["quantity_kind"]),
                value_role=ValueRole.SINGLE,
            )
        )
    content_sha256 = _sha256(
        _canonical_bytes(
            {
                "approval_sha256": approval_sha256,
                "approval_id": approval["approval_id"],
                "approved_groups": sorted(GROUPS),
                "candidate_config_identity": approval["candidate_config_identity"],
                "candidate_requirements_sha256": approval["candidate_requirements_sha256"],
            }
        )
    )
    candidate = DecisionRecord(
        decision_id=DECISION_ID,
        record_sha256="",
        content_sha256=content_sha256,
        owner=str(approval["approved_by"]),
        approved_by=str(approval["approved_by"]),
        approved_at=str(approval["approved_at"]),
        freeze_time=freeze_time,
        mutable=False,
        test_locked=True,
        truth_locked=True,
        parameter_ids=tuple(parameter_ids),
        parameter_values=tuple(values),
        profile_id=PROFILE_ID,
        experiment_scope=EXPERIMENT_SCOPE,
        component=COMPONENT,
        question=QUESTION,
        evidence_track=EVIDENCE_TRACK,
        final_output=FINAL_OUTPUT,
        rationale=(
            "The human owner separately approved all seven Matrix V2 decision groups "
            "for the exact candidate config and requirements inventory. "
            "The cited sources constrain accountable numerical representation only; "
            "they are not represented as direct authority for these protocol choices."
        ),
        source_use_ids=DECISION_SOURCE_USES,
        prohibited_interpretations=(
            "No factor is a universal optimum, empirically measured constant, or direct source fact.",
            "No test outcome, pilot result, or batch result may select, alter, or shorten this schedule.",
            "Overlapping windows are not independent inferential units.",
        ),
        limitations=(
            "All values are owner-approved preregistered protocol factors for this thesis matrix only.",
            "HAI recording-cluster confidence intervals remain undefined when independent-recording support is inadequate.",
        ),
    )
    return replace(candidate, record_sha256=decision_record_identity(candidate))


def build_authority_bundle(
    config: Mapping[str, object], approval: Mapping[str, object], *, approval_sha256: str, freeze_time: str
) -> tuple[dict[str, object], ParameterEvidenceCatalog]:
    """Turn a validated owner approval into immutable requirements and catalog data."""

    if config.get("experiment_id") != EXPERIMENT_ID:
        raise ValueError("authority builder supports only thesis-evaluation-v2")
    _instant(freeze_time, field="freeze_time")
    if _instant(freeze_time, field="freeze_time") < _instant(approval["approved_at"], field="approved_at"):
        raise ValueError("decision freeze cannot precede owner approval")
    validate_owner_approval(approval, config, approval_sha256=approval_sha256)
    governance = config.get("numeric_authority")
    assert isinstance(governance, Mapping)
    requirements_path = PROJECT_ROOT / str(governance["requirements_path"])
    requirements = _read_json(requirements_path)
    slots_raw = requirements.get("slots")
    if not isinstance(slots_raw, list) or requirements.get("numeric_consumer_count") != len(slots_raw):
        raise ValueError("candidate requirements inventory is malformed")
    slots: list[Mapping[str, object]] = []
    for slot in slots_raw:
        if not isinstance(slot, Mapping):
            raise ValueError("candidate requirements slot is malformed")
        if slot.get("authority_status") != "unresolved" or slot.get("parameter_revision_id") is not None:
            raise ValueError("candidate requirements must remain wholly unresolved before authorization")
        for field in ("slot_id", "consumer_locator", "value", "unit", "quantity_kind"):
            if not isinstance(slot.get(field), str) or not str(slot[field]).strip():
                raise ValueError(f"candidate requirements slot lacks {field}")
        _group_for_pointer(str(slot["consumer_locator"]))
        slots.append(slot)
    if len(slots) != 205:
        raise ValueError(f"expected 205 Matrix V2 numeric consumers, found {len(slots)}")

    decision = _decision(slots, approval, freeze_time=freeze_time, approval_sha256=approval_sha256)
    source_path = PROJECT_ROOT / str(governance["source_catalog_path"])
    source_catalog = load_source_catalog(source_path.read_bytes())
    revisions: list[ParameterRevision] = []
    requirements_records: list[ParameterRequirement] = []
    bindings: list[ParameterBinding] = []
    approved_slots: list[dict[str, object]] = []
    groups = _approval_groups(approval)
    for slot in slots:
        slot_id = str(slot["slot_id"])
        pointer = str(slot["consumer_locator"])
        group = _group_for_pointer(pointer)
        parameter_id = f"academic-v2-parameter:{slot_id.split(':', maxsplit=1)[-1]}"
        revision_id = f"{parameter_id}:revision-v1"
        candidate = ParameterRevision(
            parameter_id=parameter_id,
            parameter_revision_id=revision_id,
            revision_sha256="",
            parameter_class=ParameterClass.PREREGISTERED_FACTOR,
            value_role=ValueRole.SINGLE,
            value=NumericValue(
                kind=NumericValueKind.SCALAR,
                scalar=_canonical_decimal(slot["value"]),
            ),
            unit=str(slot["unit"]),
            quantity_kind=str(slot["quantity_kind"]),
            record_state=RecordState.VALID,
            approval_state=ApprovalState.PLANNING_FROZEN,
            migration_status="v2-owner-approved-preregistered-factor",
            profile_id=PROFILE_ID,
            experiment_scope=EXPERIMENT_SCOPE,
            authentic_reproduction_feasibility=AuthenticFeasibility.AVAILABLE,
            prototype_component=COMPONENT,
            consumer_locator=pointer,
            research_question=QUESTION,
            evidence_track=EVIDENCE_TRACK,
            final_package_element=FINAL_OUTPUT,
            transferability_rationale=(
                "Frozen for the approved Matrix V2 protocol only; no transfer or optimality claim."
            ),
            limitations=(
                "This is a human-approved protocol factor, not a direct empirical or source-derived value.",
            ),
            uncertainty=UncertaintyRecord(
                kind=UncertaintyKind.NOT_APPLICABLE,
                estimate=None,
                unit=None,
                method=None,
                component_ids=(),
                coverage=None,
                evidence_reference=None,
                rationale="A preregistered protocol choice has no measurement uncertainty.",
            ),
            owner=str(approval["approved_by"]),
            synthetic_status=SyntheticStatus.NOT_APPLICABLE,
            decision_authority=DecisionAuthority(decision_id=decision.decision_id),
        )
        revision = replace(candidate, revision_sha256=parameter_revision_identity(candidate))
        revisions.append(revision)
        requirements_records.append(
            ParameterRequirement(
                slot_id=slot_id,
                category=_category_for_pointer(pointer, group),
                consumer_locator=pointer,
                quantity_kind=str(slot["quantity_kind"]),
                unit=str(slot["unit"]),
                value_role=ValueRole.SINGLE,
                scope=EXPERIMENT_SCOPE,
                profile_id=PROFILE_ID,
                not_applicable_allowed=False,
            )
        )
        bindings.append(
            ParameterBinding(
                slot_id=slot_id,
                parameter_revision_id=revision.parameter_revision_id,
                parameter_revision_sha256=revision.revision_sha256,
                not_applicable=False,
                rationale=(
                    f"Owner-approved group {group} ({groups[group]['label']}) binds the exact "
                    "frozen config value to the immutable preregistered-factor revision."
                ),
            )
        )
        approved_slot = dict(slot)
        approved_slot["parameter_revision_id"] = revision.parameter_revision_id
        approved_slot["parameter_revision_sha256"] = revision.revision_sha256
        approved_slot["authority_status"] = "approved-preregistered-factor"
        approved_slots.append(approved_slot)

    required_categories = {record.category for record in requirements_records}
    dispositions = tuple(
        CategoryDisposition(
            category=category,
            state=(CategoryState.REQUIRED if category in required_categories else CategoryState.NOT_APPLICABLE),
            rationale=(
                "At least one approved Matrix V2 numeric consumer belongs to this category."
                if category in required_categories
                else "Matrix V2 has no executable numeric consumer in this category."
            ),
            owner_approved=True,
        )
        for category in InventoryCategory
    )
    inventory = NumericConsumerInventory(
        inventory_id=INVENTORY_ID,
        component_identity=V2_NUMERIC_SCHEMA_IDENTITY,
        contract_identity=V2_NUMERIC_SCHEMA_VERSION,
        code_identity=V2_NUMERIC_SCHEMA_IDENTITY,
        scope=EXPERIMENT_SCOPE,
        profile_id=PROFILE_ID,
        requirements=tuple(requirements_records),
        category_dispositions=dispositions,
    )
    required = RequiredParameterSet(
        required_set_id=REQUIRED_SET_ID,
        catalog_identity="",
        source_catalog_identity=source_catalog_identity(source_catalog),
        vocabulary_version=SEMANTIC_VOCABULARY_VERSION,
        inventory_id=inventory.inventory_id,
        scope=inventory.scope,
        profile_id=inventory.profile_id,
        experiment_id=EXPERIMENT_ID,
        component_identity=inventory.component_identity,
        bindings=tuple(bindings),
    )
    catalog = ParameterEvidenceCatalog(
        schema_version="parameter-evidence.v1",
        semantic_vocabulary_version=SEMANTIC_VOCABULARY_VERSION,
        source_catalog_identity=source_catalog_identity(source_catalog),
        parameter_revisions=tuple(revisions),
        derivations=(),
        decisions=(decision,),
        mock_admissions=(),
        measurements=(),
        inventories=(inventory,),
        required_sets=(required,),
        locus_audits=(),
        legacy_quarantine=(),
    )
    catalog = replace(
        catalog,
        required_sets=(replace(required, catalog_identity=parameter_catalog_identity(catalog)),),
    )
    # Exercise the strict parser before publishing.  Temporal ordering is tested later.
    load_parameter_catalog(canonical_parameter_catalog_bytes(catalog))
    approved_requirements = dict(requirements)
    approved_requirements["slots"] = approved_slots
    approved_requirements["limitations"] = [
        "Every executable v2 numeric consumer is bound to an immutable owner-approved preregistered-factor revision.",
        "This binding freezes values but does not waive leakage, support, cost, temporal, or HAI limitations.",
    ]
    return approved_requirements, catalog


def authorize(
    *, approval_path: Path, candidate_config_path: Path, requirements_path: Path,
    catalog_path: Path, authorized_config_path: Path,
) -> dict[str, str]:
    config = load_academic_config(candidate_config_path)
    approval_bytes = approval_path.read_bytes()
    approval = _read_json(approval_path)
    approval_sha256 = _sha256(approval_bytes)
    freeze_time = _now()
    requirements, catalog = build_authority_bundle(
        config, approval, approval_sha256=approval_sha256, freeze_time=freeze_time
    )
    requirements_bytes = json.dumps(
        requirements, sort_keys=True, indent=2, ensure_ascii=False, allow_nan=False
    ).encode("utf-8") + b"\n"
    catalog_bytes = canonical_parameter_catalog_bytes(catalog)
    _publish_immutable(requirements_path, requirements_bytes)
    _publish_immutable(catalog_path, catalog_bytes)
    candidate = json.loads(json.dumps(config))
    assert isinstance(candidate, dict)
    governance = candidate["numeric_authority"]
    assert isinstance(governance, dict)
    governance["requirements_path"] = _relative(requirements_path)
    governance["requirements_sha256"] = _sha256(requirements_bytes)
    governance["catalog_path"] = _relative(catalog_path)
    governance["catalog_sha256"] = _sha256(catalog_bytes)
    governance["inventory_id"] = INVENTORY_ID
    governance["required_set_id"] = REQUIRED_SET_ID
    governance["temporal_context_path"] = _relative(DEFAULT_TEMPORAL_CONTEXT)
    governance["temporal_context_sha256"] = "UNRESOLVED"
    config_bytes = json.dumps(
        candidate, sort_keys=True, indent=2, ensure_ascii=False, allow_nan=False
    ).encode("utf-8") + b"\n"
    _publish_immutable(authorized_config_path, config_bytes)
    return {
        "approval_sha256": approval_sha256,
        "decision_freeze_time": freeze_time,
        "requirements": str(requirements_path),
        "catalog": str(catalog_path),
        "authorized_config": str(authorized_config_path),
    }


def _load_decision(config: Mapping[str, object]) -> DecisionRecord:
    governance = config.get("numeric_authority")
    if not isinstance(governance, Mapping):
        raise ValueError("config lacks numeric_authority")
    catalog_path = PROJECT_ROOT / str(governance["catalog_path"])
    catalog = load_parameter_catalog(catalog_path.read_bytes())
    if len(catalog.decisions) != 1 or catalog.decisions[0].decision_id != DECISION_ID:
        raise ValueError("authorized Matrix V2 catalog must contain exactly one frozen decision")
    return catalog.decisions[0]


def _artifact_identity(payload: Mapping[str, object]) -> str:
    bare = dict(payload)
    bare["identity"] = ""
    return _sha256(_canonical_bytes(bare))


def _load_lock(path: Path, *, schema: str) -> dict[str, object]:
    payload = _read_json(path)
    if payload.get("schema_version") != schema:
        raise ValueError(f"unsupported lock schema in {path}")
    if payload.get("identity") != _artifact_identity(payload):
        raise ValueError(f"lock identity mismatch: {path}")
    return payload


def _source_tree_snapshot(root: Path) -> dict[str, object]:
    """Capture a stable raw-source inventory without parsing outcome content.

    Hashing every ZIP's decompressed syscall stream merely to establish the
    temporal order would duplicate the costly phase preflight. The later
    preflight/cell loader already authenticates each consumed source payload
    and binds it into ``AcademicDataset.identity``. This lock instead proves
    that the configured raw source surface was present and unchanged across a
    two-pass metadata snapshot after the test lock, without reading labels or
    model outcomes before execution is eligible.
    """

    root = root.resolve()
    try:
        root.relative_to(PROJECT_ROOT.resolve())
    except ValueError as exc:
        raise ValueError(f"dataset root escapes project scope: {root}") from exc
    if not root.is_dir() or root.is_symlink():
        raise ValueError(f"dataset root must be a non-symlink directory: {root}")

    def capture() -> list[dict[str, object]]:
        entries: list[dict[str, object]] = []
        for candidate in sorted(root.rglob("*"), key=lambda item: item.as_posix()):
            if candidate.is_symlink():
                raise ValueError(f"dataset source inventory rejects symlink: {candidate}")
            if not candidate.is_file():
                continue
            stat = candidate.stat(follow_symlinks=False)
            entries.append(
                {
                    "path": candidate.relative_to(root).as_posix(),
                    "byte_size": stat.st_size,
                    "mtime_ns": stat.st_mtime_ns,
                }
            )
        return entries

    first = capture()
    second = capture()
    if first != second:
        raise RuntimeError(f"dataset source inventory changed while being locked: {root}")
    return {
        "root": _relative(root),
        "file_count": len(first),
        "byte_count": sum(int(item["byte_size"]) for item in first),
        "inventory_identity": canonical_json_hash(first),
        "entries": first,
    }


def verify(*, authorized_config_path: Path, test_lock_path: Path, stdout_path: Path, stderr_path: Path) -> dict[str, str]:
    config = load_academic_config(authorized_config_path)
    decision = _load_decision(config)
    freeze = _instant(decision.freeze_time, field="decision.freeze_time")
    started_at = _now()
    completed = subprocess.run(
        [sys.executable, "-m", "pytest", "-q"],
        cwd=PROJECT_ROOT,
        check=False,
        capture_output=True,
        text=True,
        encoding="utf-8",
        errors="replace",
    )
    completed_at = _now()
    if completed.returncode != 0:
        raise RuntimeError(
            "Post-freeze test suite failed; no test lock was published.\n"
            + completed.stdout
            + completed.stderr
        )
    if _instant(completed_at, field="test.completed_at") <= freeze:
        raise RuntimeError("post-freeze test completion must occur after the decision freeze")
    stdout_bytes = completed.stdout.encode("utf-8")
    stderr_bytes = completed.stderr.encode("utf-8")
    _publish_immutable(stdout_path, stdout_bytes)
    _publish_immutable(stderr_path, stderr_bytes)
    lock: dict[str, object] = {
        "schema_version": TEST_LOCK_SCHEMA,
        "experiment_id": EXPERIMENT_ID,
        "config_identity": config_identity(config),
        "freeze_identity": decision.record_sha256,
        "started_at": started_at,
        "completed_at": completed_at,
        "command": [sys.executable, "-m", "pytest", "-q"],
        "exit_code": completed.returncode,
        "passed": True,
        "stdout_artifact": {
            "path": _relative(stdout_path),
            "sha256": _sha256(stdout_bytes),
            "byte_size": len(stdout_bytes),
        },
        "stderr_artifact": {
            "path": _relative(stderr_path),
            "sha256": _sha256(stderr_bytes),
            "byte_size": len(stderr_bytes),
        },
        "identity": "",
    }
    lock["identity"] = _artifact_identity(lock)
    _publish_immutable(test_lock_path, _canonical_bytes(lock))
    return {"test_lock": str(test_lock_path), "test_identity": str(lock["identity"])}


def lock_truth(*, authorized_config_path: Path, test_lock_path: Path, truth_lock_path: Path) -> dict[str, str]:
    config = load_academic_config(authorized_config_path)
    decision = _load_decision(config)
    test_lock = _load_lock(test_lock_path, schema=TEST_LOCK_SCHEMA)
    if test_lock.get("experiment_id") != EXPERIMENT_ID or test_lock.get("config_identity") != config_identity(config):
        raise ValueError("test lock is not bound to the authorized Matrix V2 config")
    if test_lock.get("freeze_identity") != decision.record_sha256 or test_lock.get("passed") is not True:
        raise ValueError("test lock is not a successful post-freeze lock")
    test_time = _instant(test_lock.get("completed_at"), field="test_lock.completed_at")
    freeze_time = _instant(decision.freeze_time, field="decision.freeze_time")
    if test_time <= freeze_time:
        raise ValueError("test lock must follow decision freeze")
    datasets = config.get("datasets")
    if not isinstance(datasets, Mapping):
        raise ValueError("authorized config lacks datasets")
    source_snapshots: dict[str, dict[str, object]] = {}
    for name, dataset_config in sorted(datasets.items()):
        if not isinstance(name, str) or not isinstance(dataset_config, Mapping):
            raise ValueError("dataset configuration is malformed")
        raw_root = dataset_config.get("root")
        if not isinstance(raw_root, str) or not raw_root.strip():
            raise ValueError(f"dataset {name!r} lacks a source root")
        source_snapshots[name] = _source_tree_snapshot(PROJECT_ROOT / raw_root)
    truth_locked_at = _now()
    if _instant(truth_locked_at, field="truth_locked_at") <= test_time:
        raise RuntimeError("truth lock must follow the post-freeze test lock")
    lock: dict[str, object] = {
        "schema_version": TRUTH_LOCK_SCHEMA,
        "experiment_id": EXPERIMENT_ID,
        "config_identity": config_identity(config),
        "freeze_identity": decision.record_sha256,
        "test_lock_identity": test_lock["identity"],
        "truth_locked_at": truth_locked_at,
        "source_snapshots": source_snapshots,
        "limitations": [
            "This artifact locks a stable raw-source metadata inventory after test lock; it intentionally does not parse labels, scores, or model outcomes.",
            "Preflight and every admitted cell must still bind complete consumed-content and result-dataset identities before any claim is allowed.",
            "It does not replace phase-specific support, leakage, cost, or uncertainty gates.",
        ],
        "identity": "",
    }
    lock["identity"] = _artifact_identity(lock)
    _publish_immutable(truth_lock_path, _canonical_bytes(lock))
    return {"truth_lock": str(truth_lock_path), "truth_identity": str(lock["identity"])}


def finalize(
    *, authorized_config_path: Path, test_lock_path: Path, truth_lock_path: Path,
    temporal_context_path: Path, frozen_config_path: Path,
) -> dict[str, str]:
    config = load_academic_config(authorized_config_path)
    decision = _load_decision(config)
    test_lock = _load_lock(test_lock_path, schema=TEST_LOCK_SCHEMA)
    truth_lock = _load_lock(truth_lock_path, schema=TRUTH_LOCK_SCHEMA)
    expected_config = config_identity(config)
    for lock, label in ((test_lock, "test"), (truth_lock, "truth")):
        if lock.get("experiment_id") != EXPERIMENT_ID or lock.get("config_identity") != expected_config:
            raise ValueError(f"{label} lock is not bound to the authorized config")
        if lock.get("freeze_identity") != decision.record_sha256:
            raise ValueError(f"{label} lock does not bind the frozen decision")
    if truth_lock.get("test_lock_identity") != test_lock.get("identity"):
        raise ValueError("truth lock does not bind the exact successful test lock")
    if test_lock.get("passed") is not True or test_lock.get("exit_code") != 0:
        raise ValueError("finalization requires a successful post-freeze test lock")
    freeze = _instant(decision.freeze_time, field="decision.freeze_time")
    tested = _instant(test_lock.get("completed_at"), field="test_lock.completed_at")
    truth = _instant(truth_lock.get("truth_locked_at"), field="truth_lock.truth_locked_at")
    if not freeze < tested < truth:
        raise ValueError("temporal order must be freeze < test lock < truth lock")
    seed = {
        "freeze_identity": decision.record_sha256,
        "test_identity": test_lock["identity"],
        "truth_identity": truth_lock["identity"],
        "freeze_time": decision.freeze_time,
        "test_time": test_lock["completed_at"],
        "truth_time": truth_lock["truth_locked_at"],
    }
    context: dict[str, object] = {
        "context_id": "temporal-gate-context:thesis-evaluation-v2:"
        + _sha256(_canonical_bytes(seed)).split(":", maxsplit=1)[1][:20],
        **seed,
    }
    # The runner deliberately accepts only this exact contract shape.
    if set(context) != {
        "context_id", "freeze_identity", "freeze_time", "test_identity", "test_time",
        "truth_identity", "truth_time",
    }:
        raise AssertionError("TemporalGateContext payload drift")
    context_bytes = json.dumps(
        context, sort_keys=True, indent=2, ensure_ascii=False, allow_nan=False
    ).encode("utf-8") + b"\n"
    _publish_immutable(temporal_context_path, context_bytes)
    temporal_context = TemporalGateContext(**context)
    governance = config.get("numeric_authority")
    assert isinstance(governance, Mapping)
    source_path = PROJECT_ROOT / str(governance["source_catalog_path"])
    catalog_path = PROJECT_ROOT / str(governance["catalog_path"])
    source_catalog = load_source_catalog(source_path.read_bytes())
    catalog = load_parameter_catalog(catalog_path.read_bytes())
    inventory = next(item for item in catalog.inventories if item.inventory_id == INVENTORY_ID)
    required_set = next(item for item in catalog.required_sets if item.required_set_id == REQUIRED_SET_ID)
    gate = validate_parameter_gate(
        catalog,
        source_catalog,
        inventory,
        required_set,
        evidence_root=PROJECT_ROOT,
        temporal_context=temporal_context,
    )
    if gate.accountability_outcome != AccountabilityOutcome.ACCOUNTABLE:
        details = "; ".join(
            f"{item.rule_id}:{item.field_path}" for item in gate.violations[:10]
        )
        raise ValueError(f"independent parameter gate did not close: {details}")
    frozen = json.loads(json.dumps(config))
    assert isinstance(frozen, dict)
    frozen_governance = frozen["numeric_authority"]
    assert isinstance(frozen_governance, dict)
    frozen_governance["temporal_context_path"] = _relative(temporal_context_path)
    frozen_governance["temporal_context_sha256"] = _sha256(context_bytes)
    frozen_bytes = json.dumps(
        frozen, sort_keys=True, indent=2, ensure_ascii=False, allow_nan=False
    ).encode("utf-8") + b"\n"
    _publish_immutable(frozen_config_path, frozen_bytes)
    return {
        "temporal_context": str(temporal_context_path),
        "frozen_config": str(frozen_config_path),
        "parameter_gate_result": gate.gate_result_id,
    }


def _parser() -> argparse.ArgumentParser:
    parser = argparse.ArgumentParser(description=__doc__)
    subcommands = parser.add_subparsers(dest="command", required=True)

    authorize_parser = subcommands.add_parser("authorize", help="publish owner-approved authority artifacts")
    authorize_parser.add_argument("--approval", type=Path, default=DEFAULT_APPROVAL)
    authorize_parser.add_argument("--config", type=Path, default=DEFAULT_CANDIDATE_CONFIG)
    authorize_parser.add_argument("--requirements-output", type=Path, default=DEFAULT_REQUIREMENTS)
    authorize_parser.add_argument("--catalog-output", type=Path, default=DEFAULT_CATALOG)
    authorize_parser.add_argument("--authorized-config-output", type=Path, default=DEFAULT_AUTHORIZED_CONFIG)

    verify_parser = subcommands.add_parser("verify", help="run and preserve post-freeze tests")
    verify_parser.add_argument("--config", type=Path, default=DEFAULT_AUTHORIZED_CONFIG)
    verify_parser.add_argument("--test-lock-output", type=Path, default=DEFAULT_TEST_LOCK)
    verify_parser.add_argument("--stdout-output", type=Path, default=DEFAULT_TEST_STDOUT)
    verify_parser.add_argument("--stderr-output", type=Path, default=DEFAULT_TEST_STDERR)

    truth_parser = subcommands.add_parser("lock-truth", help="lock official input identities after tests")
    truth_parser.add_argument("--config", type=Path, default=DEFAULT_AUTHORIZED_CONFIG)
    truth_parser.add_argument("--test-lock", type=Path, default=DEFAULT_TEST_LOCK)
    truth_parser.add_argument("--truth-lock-output", type=Path, default=DEFAULT_TRUTH_LOCK)

    finalize_parser = subcommands.add_parser("finalize", help="publish temporal context and runnable frozen config")
    finalize_parser.add_argument("--config", type=Path, default=DEFAULT_AUTHORIZED_CONFIG)
    finalize_parser.add_argument("--test-lock", type=Path, default=DEFAULT_TEST_LOCK)
    finalize_parser.add_argument("--truth-lock", type=Path, default=DEFAULT_TRUTH_LOCK)
    finalize_parser.add_argument("--temporal-context-output", type=Path, default=DEFAULT_TEMPORAL_CONTEXT)
    finalize_parser.add_argument("--frozen-config-output", type=Path, default=DEFAULT_FROZEN_CONFIG)
    return parser


def main(argv: list[str] | None = None) -> int:
    args = _parser().parse_args(argv)
    if args.command == "authorize":
        result = authorize(
            approval_path=args.approval,
            candidate_config_path=args.config,
            requirements_path=args.requirements_output,
            catalog_path=args.catalog_output,
            authorized_config_path=args.authorized_config_output,
        )
    elif args.command == "verify":
        result = verify(
            authorized_config_path=args.config,
            test_lock_path=args.test_lock_output,
            stdout_path=args.stdout_output,
            stderr_path=args.stderr_output,
        )
    elif args.command == "lock-truth":
        result = lock_truth(
            authorized_config_path=args.config,
            test_lock_path=args.test_lock,
            truth_lock_path=args.truth_lock_output,
        )
    elif args.command == "finalize":
        result = finalize(
            authorized_config_path=args.config,
            test_lock_path=args.test_lock,
            truth_lock_path=args.truth_lock,
            temporal_context_path=args.temporal_context_output,
            frozen_config_path=args.frozen_config_output,
        )
    else:  # pragma: no cover - argparse makes this unreachable.
        raise AssertionError(args.command)
    print(json.dumps(result, sort_keys=True, ensure_ascii=False))
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
