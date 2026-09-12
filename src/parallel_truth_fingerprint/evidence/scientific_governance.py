"""Pure, fail-closed gates for scientific-governance.v1.

Every fact is injected by the caller.  These gates never resolve an alias,
read truth, publish evidence, or execute an authorized activity.
"""
from __future__ import annotations

from dataclasses import dataclass

from parallel_truth_fingerprint.contracts.scientific_governance import (
    ActivityAction, ActivityAuthorization, FreezeStage, PartitionRecord,
    PartitionRole, ScientificFreeze, TruthJoinRecord, TruthUnlockRecord,
    is_canonical_timestamp, is_immutable_id,
)


@dataclass(frozen=True)
class GovernanceViolation:
    rule_id: str
    field: str
    explanation: str


@dataclass(frozen=True)
class GovernanceGateResult:
    allowed: bool
    violations: tuple[GovernanceViolation, ...]
    authorization_effect: str = "none"


@dataclass(frozen=True)
class SupportDisposition:
    """Opaque completed score or decision fact for one frozen support unit."""
    support_id: str
    disposition_id: str
    completion_receipt_id: str


@dataclass(frozen=True)
class GovernanceProfile:
    revision_id: str
    audience: str
    allowed_roles: tuple[str, ...] = ()
    permitted_exclusion_reasons: tuple[str, ...] = ()
    required_scope_slots: tuple[str, ...] = ()
    action: str | None = None
    expected_output_roles: tuple[str, ...] = ()
    freeze_stage: str | None = None
    required_binding_slots: tuple[str, ...] = ()
    required_predecessor_stage: str | None = None
    applicable_partition_roles: tuple[str, ...] = ()

    @classmethod
    def sentinel_partition(cls) -> "GovernanceProfile":
        return cls("profile-sentinel", "detector_facing", ("train", "validation", "calibration", "test", "excluded"), ("sentinel_excluded",))

    @classmethod
    def sentinel_action(cls) -> "GovernanceProfile":
        return cls("profile-action", "detector_facing", required_scope_slots=("track",), action="model_training", expected_output_roles=("detector_bundle",))

    @classmethod
    def sentinel_blind_scoring_freeze(cls) -> "GovernanceProfile":
        return cls("profile-blind-score", "detector_facing", freeze_stage="blind_scoring", required_binding_slots=("partition", "support", "bundle", "schema", "preprocessing", "calibration", "threshold", "decision_schema", "metric_protocol"), applicable_partition_roles=("test",))

    @classmethod
    def sentinel_pretruth_freeze(cls) -> "GovernanceProfile":
        return cls("profile-pretruth", "evaluator_restricted", freeze_stage="pretruth_evaluation", required_binding_slots=("partition", "support", "score_closure", "decision_closure", "evaluator", "metric_protocol"), required_predecessor_stage="blind_scoring", applicable_partition_roles=("test",))


def _result(violations: list[GovernanceViolation], *, permission: bool = False) -> GovernanceGateResult:
    items = tuple(sorted(violations, key=lambda item: (item.rule_id, item.field, item.explanation)))
    return GovernanceGateResult(not items, items, "permission" if permission and not items else "none")


def _exact_slots(bindings: tuple[tuple[str, str], ...], required: tuple[str, ...], violations: list[GovernanceViolation], field: str, rule: str) -> None:
    slots = [item[0] for item in bindings]
    if len(slots) != len(set(slots)) or set(slots) != set(required):
        violations.append(GovernanceViolation(rule, field, "Slots must be an exact, non-duplicated profile-defined set."))
    if any(not is_immutable_id(item[1]) for item in bindings):
        violations.append(GovernanceViolation("GOV-IMMUTABLE-REFERENCE", field, "Bindings must use immutable SHA-256 identities."))


def validate_partition_record(record: PartitionRecord, *, inventory_groups: tuple[str, ...], profile: GovernanceProfile) -> GovernanceGateResult:
    violations: list[GovernanceViolation] = []
    if record.audience != profile.audience:
        violations.append(GovernanceViolation("GOV-PARTITION-AUDIENCE", "audience", "Audience is not allowed by the registered profile."))
    if record.profile_revision_id != profile.revision_id:
        violations.append(GovernanceViolation("GOV-PARTITION-PROFILE", "profile_revision_id", "Unknown or substituted profile revision."))
    if not is_canonical_timestamp(record.created_at):
        violations.append(GovernanceViolation("GOV-TIMESTAMP", "created_at", "Timestamp must be UTC to whole seconds."))
    for field in ("source_universe_id", "eligibility_policy_id", "grouping_scheme_id", "method_identity"):
        if not is_immutable_id(getattr(record, field)):
            violations.append(GovernanceViolation("GOV-IMMUTABLE-REFERENCE", field, "Reference must be an exact SHA-256 identity."))
    groups = [item.group_id for item in record.memberships]
    if len(groups) != len(set(groups)):
        violations.append(GovernanceViolation("GOV-PARTITION-GROUP-DUPLICATE", "memberships", "Each opaque group has exactly one disposition."))
    if len(inventory_groups) != len(set(inventory_groups)) or set(groups) != set(inventory_groups):
        violations.append(GovernanceViolation("GOV-PARTITION-INVENTORY-INCOMPLETE", "memberships", "Membership must close the supplied source inventory exactly."))
    for membership in record.memberships:
        role = str(membership.disposition)
        if role not in profile.allowed_roles:
            violations.append(GovernanceViolation("GOV-PARTITION-ROLE", "memberships", "Partition role is not profile-owned."))
        if role == PartitionRole.EXCLUDED.value:
            if membership.exclusion_reason not in profile.permitted_exclusion_reasons or not is_immutable_id(membership.exclusion_evidence_id):
                violations.append(GovernanceViolation("GOV-PARTITION-EXCLUSION", "memberships", "Exclusions require a profile-approved reason and evidence identity."))
        elif membership.exclusion_reason is not None or membership.exclusion_evidence_id is not None:
            violations.append(GovernanceViolation("GOV-PARTITION-EXCLUSION-CONFLICT", "memberships", "Non-excluded memberships carry no exclusion material."))
    if not record.source_use_revision_ids or len(record.source_use_revision_ids) != len(set(record.source_use_revision_ids)) or any(not is_immutable_id(item) for item in record.source_use_revision_ids):
        violations.append(GovernanceViolation("GOV-PARTITION-SOURCE-USE", "source_use_revision_ids", "Source-use revisions must be unique immutable identities."))
    return _result(violations)


def validate_scientific_freeze(record: ScientificFreeze, *, profile: GovernanceProfile, predecessor_stages: dict[str, str] | None = None, truth_tainted_ids: tuple[str, ...] = ()) -> GovernanceGateResult:
    violations: list[GovernanceViolation] = []
    if record.audience != profile.audience or record.profile_revision_id != profile.revision_id:
        violations.append(GovernanceViolation("GOV-FREEZE-PROFILE", "profile_revision_id", "Freeze requires its exact independently registered profile."))
    if str(record.stage) not in {item.value for item in FreezeStage} or str(record.stage) != profile.freeze_stage:
        violations.append(GovernanceViolation("GOV-FREEZE-STAGE", "stage", "Freeze stage is closed and profile-owned."))
    if not is_canonical_timestamp(record.created_at):
        violations.append(GovernanceViolation("GOV-TIMESTAMP", "created_at", "Timestamp must be UTC to whole seconds."))
    _exact_slots(record.bindings, profile.required_binding_slots, violations, "bindings", "GOV-FREEZE-BINDINGS")
    if profile.required_predecessor_stage:
        if not is_immutable_id(record.predecessor_freeze_id) or (predecessor_stages or {}).get(record.predecessor_freeze_id) != profile.required_predecessor_stage:
            violations.append(GovernanceViolation("GOV-FREEZE-PREDECESSOR", "predecessor_freeze_id", "Freeze requires the exact earlier-stage predecessor."))
    elif record.predecessor_freeze_id is not None and not is_immutable_id(record.predecessor_freeze_id):
        violations.append(GovernanceViolation("GOV-IMMUTABLE-REFERENCE", "predecessor_freeze_id", "Predecessor must be immutable."))
    values = {value for _, value in record.bindings}
    if values.intersection(truth_tainted_ids):
        violations.append(GovernanceViolation("GOV-FREEZE-TRUTH-TAINT", "bindings", "Detector/pretruth freezes cannot bind restricted truth."))
    if str(record.stage) == FreezeStage.PRETRUTH_EVALUATION.value and any(slot in {"evaluation_result", "truth", "truth_join"} for slot, _ in record.bindings):
        violations.append(GovernanceViolation("GOV-FREEZE-FUTURE-OUTPUT", "bindings", "Pre-truth freeze cannot bind truth or a future evaluation result."))
    return _result(violations)


def _validate_support_closure(expected: tuple[str, ...], dispositions: tuple[SupportDisposition, ...], field: str, violations: list[GovernanceViolation]) -> None:
    ids = [item.support_id for item in dispositions]
    if len(expected) != len(set(expected)) or len(ids) != len(set(ids)) or set(ids) != set(expected):
        violations.append(GovernanceViolation("GOV-TRUTH-SUPPORT-CLOSURE", field, "Every frozen support unit needs exactly one disposition."))
    if any(not is_immutable_id(value) for item in dispositions for value in (item.support_id, item.disposition_id, item.completion_receipt_id)):
        violations.append(GovernanceViolation("GOV-TRUTH-DISPOSITION-REFERENCE", field, "Disposition and receipt identities must be immutable."))


def validate_truth_unlock(record: TruthUnlockRecord, *, expected_support_ids: tuple[str, ...], score_dispositions: tuple[SupportDisposition, ...], decision_dispositions: tuple[SupportDisposition, ...], granted_authorization_id: str, pretruth_freeze_id: str, blind_scoring_freeze_id: str, profile: GovernanceProfile) -> GovernanceGateResult:
    violations: list[GovernanceViolation] = []
    if record.audience != "evaluator_restricted" or profile.audience != "evaluator_restricted":
        violations.append(GovernanceViolation("GOV-TRUTH-AUDIENCE", "audience", "Truth unlock is evaluator-restricted only."))
    if record.decision != "granted" or record.authorization_id != granted_authorization_id:
        violations.append(GovernanceViolation("GOV-TRUTH-AUTHORIZATION", "authorization_id", "Unlock requires the exact granted truth-unlock authorization."))
    if record.pretruth_freeze_id != pretruth_freeze_id or record.blind_scoring_freeze_id != blind_scoring_freeze_id:
        violations.append(GovernanceViolation("GOV-TRUTH-FREEZE", "pretruth_freeze_id", "Unlock must bind the exact pre-truth and blind-score freezes."))
    for field in ("partition_id", "support_id", "restricted_truth_id", "score_closure_id", "detector_decision_closure_id", "authorization_id", "pretruth_freeze_id", "blind_scoring_freeze_id"):
        if not is_immutable_id(getattr(record, field)):
            violations.append(GovernanceViolation("GOV-IMMUTABLE-REFERENCE", field, "Reference must be immutable."))
    if not is_canonical_timestamp(record.created_at) or not record.owner_id:
        violations.append(GovernanceViolation("GOV-TRUTH-METADATA", "created_at", "Owner and canonical time are required."))
    _validate_support_closure(expected_support_ids, score_dispositions, "score_dispositions", violations)
    _validate_support_closure(expected_support_ids, decision_dispositions, "decision_dispositions", violations)
    receipt_ids = {item.completion_receipt_id for item in (*score_dispositions, *decision_dispositions)}
    if set(record.completion_receipt_ids) != receipt_ids or any(not is_immutable_id(value) for value in record.completion_receipt_ids):
        violations.append(GovernanceViolation("GOV-TRUTH-RECEIPTS", "completion_receipt_ids", "Unlock must cite exactly the closure receipts."))
    return _result(violations)


def validate_truth_join(record: TruthJoinRecord, *, unlock_id: str, authorization_id: str, profile: GovernanceProfile, detector_references: tuple[str, ...] = ()) -> GovernanceGateResult:
    violations: list[GovernanceViolation] = []
    if record.audience != "evaluator_restricted" or profile.audience != "evaluator_restricted":
        violations.append(GovernanceViolation("GOV-JOIN-AUDIENCE", "audience", "Restricted truth joins are evaluator-only."))
    if record.unlock_id != unlock_id or record.authorization_id != authorization_id:
        violations.append(GovernanceViolation("GOV-JOIN-LINEAGE", "unlock_id", "Join requires exact granted unlock and join authorization."))
    if record.join_outcome not in {"joined", "not_joined"}:
        violations.append(GovernanceViolation("GOV-JOIN-OUTCOME", "join_outcome", "Join outcome is structural and closed."))
    for field in ("unlock_id", "authorization_id", "partition_id", "support_id", "freeze_id", "score_id", "detector_decision_id", "restricted_truth_id"):
        if not is_immutable_id(getattr(record, field)):
            violations.append(GovernanceViolation("GOV-IMMUTABLE-REFERENCE", field, "Reference must be immutable."))
    if not record.evaluator_identity or not is_canonical_timestamp(record.created_at):
        violations.append(GovernanceViolation("GOV-JOIN-METADATA", "created_at", "Evaluator identity and canonical time are required."))
    restricted = {record.restricted_truth_id, record.unlock_id, record.authorization_id}
    if restricted.intersection(detector_references):
        violations.append(GovernanceViolation("GOV-JOIN-DETECTOR-TAINT", "detector_references", "Detector-facing graph cannot reference restricted lineage."))
    return _result(violations)


def validate_activity_authorization(record: ActivityAuthorization, *, profile: GovernanceProfile) -> GovernanceGateResult:
    violations: list[GovernanceViolation] = []
    if record.decision not in {"approved", "rejected"}:
        violations.append(GovernanceViolation("GOV-AUTH-DECISION", "decision", "Decision is closed to approved or rejected."))
    if str(record.action) not in {item.value for item in ActivityAction}:
        violations.append(GovernanceViolation("GOV-AUTH-ACTION", "action", "Action is not in the closed v1 registry."))
    if record.profile_revision_id != profile.revision_id or str(record.action) != profile.action:
        violations.append(GovernanceViolation("GOV-AUTH-PROFILE", "profile_revision_id", "Action must use its independently registered exact profile."))
    if record.audience != profile.audience:
        violations.append(GovernanceViolation("GOV-AUTH-AUDIENCE", "audience", "Audience is not allowed by action profile."))
    if str(record.action) in {"truth_unlock", "restricted_truth_join", "evaluation"} and record.audience != "evaluator_restricted":
        violations.append(GovernanceViolation("GOV-AUTH-TRUTH-AUDIENCE", "audience", "Truth actions are evaluator-only."))
    _exact_slots(record.scope_slots, profile.required_scope_slots, violations, "scope_slots", "GOV-AUTH-SCOPE")
    if any(not is_immutable_id(value) for value in (*record.input_ids, *record.prerequisite_ids)):
        violations.append(GovernanceViolation("GOV-AUTH-IMMUTABLE-REFERENCE", "input_ids", "Inputs and prerequisites must be immutable identities."))
    if tuple(record.expected_output_roles) != tuple(profile.expected_output_roles):
        violations.append(GovernanceViolation("GOV-AUTH-OUTPUT-ROLES", "expected_output_roles", "Output roles must be profile-owned."))
    if not is_canonical_timestamp(record.created_at) or not record.owner_id:
        violations.append(GovernanceViolation("GOV-AUTH-METADATA", "created_at", "Owner and canonical timestamp are required."))
    if record.planned_activity_id != record.computed_id():
        violations.append(GovernanceViolation("GOV-AUTH-PLANNED-ID", "planned_activity_id", "Pre-decision activity digest does not recompute."))
    return _result(violations, permission=record.decision == "approved")
