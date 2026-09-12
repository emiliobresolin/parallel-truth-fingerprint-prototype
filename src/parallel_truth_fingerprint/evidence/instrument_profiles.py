"""Pure, injected admission checks for InstrumentProfile.v1."""

from __future__ import annotations

from dataclasses import dataclass
from decimal import Decimal, Inexact, Rounded, localcontext
from typing import Callable, Mapping

from parallel_truth_fingerprint.contracts.instrument_profile import (
    InstrumentProfile, InstrumentProfileRole, MeasurementQuality, TransformDirection,
)
from parallel_truth_fingerprint.contracts.scientific_governance import is_immutable_id


@dataclass(frozen=True)
class InstrumentProfileViolation:
    rule_id: str
    field: str
    explanation: str


@dataclass(frozen=True)
class AdmittedInstrumentProfile:
    profile_id: str
    profile_content_sha256: str
    registry_snapshot_id: str
    authorization_effect: str = "none"


@dataclass(frozen=True)
class InstrumentProfileAdmission:
    admitted: bool
    handle: AdmittedInstrumentProfile | None
    violations: tuple[InstrumentProfileViolation, ...]
    authorization_effect: str = "none"


@dataclass(frozen=True)
class ConversionResult:
    value: Decimal | None
    direction: str
    profile_content_sha256: str
    transform_revision_id: str
    conversion_disposition: str
    violations: tuple[InstrumentProfileViolation, ...] = ()
    authorization_effect: str = "none"


@dataclass(frozen=True)
class MeasurementQualityResult:
    quality: str
    conversion_disposition: str
    applied_rule_ids: tuple[str, ...]
    raw_current: Decimal | None
    authorization_effect: str = "none"


@dataclass(frozen=True)
class CommandConformanceResult:
    status: str
    conversion_disposition: str
    reason_ids: tuple[str, ...]
    authorization_effect: str = "none"


def _bad(rule_id: str, field: str, explanation: str) -> InstrumentProfileViolation:
    return InstrumentProfileViolation(rule_id, field, explanation)


def _immutable(value: str | None) -> bool:
    return is_immutable_id(value) and value.casefold() not in {"latest", "current"}


def admit_instrument_profile(profile: InstrumentProfile, *, registry_snapshot_id: str,
                             source_use_resolves: Callable[[str], bool],
                             parameter_gate_accountable: Callable[[str, str], bool]) -> InstrumentProfileAdmission:
    """Validate a candidate entirely from supplied immutable resolvers."""
    errors: list[InstrumentProfileViolation] = []
    if profile.schema_version != "InstrumentProfile.v1":
        errors.append(InstrumentProfileViolation("IPV1_SCHEMA_VERSION_TOKEN", "schema_version", "Unknown profile schema."))
    if profile.authorization_effect != "none":
        errors.append(InstrumentProfileViolation("IPV1_AUTHORIZATION_EFFECT", "authorization_effect", "Profiles never authorize activities."))
    if not is_immutable_id(profile.content_sha256) or profile.content_sha256 != profile.computed_content_sha256():
        errors.append(InstrumentProfileViolation("IPV1_CONTENT_HASH", "content_sha256", "Canonical profile digest does not recompute."))
    if not _immutable(registry_snapshot_id) or not _immutable(profile.numeric_inventory_id) or not _immutable(profile.required_parameter_set_id):
        errors.append(InstrumentProfileViolation("IPV1_PARAMETER_GATE", "numeric_inventory_id", "Required upstream identities are missing."))
    if (not profile.source_use_revision_ids or len(set(profile.source_use_revision_ids)) != len(profile.source_use_revision_ids)
            or not profile.source_locators or len(profile.source_locators) != len(profile.source_use_revision_ids)
            or any(not _immutable(item) or not source_use_resolves(item) for item in profile.source_use_revision_ids)):
        errors.append(InstrumentProfileViolation("IPV1_SOURCE_USE_LOCATOR", "source_use_revision_ids", "Exact source uses must resolve."))
    directions = [str(item.direction) for item in profile.transform_bindings]
    expected = {item.value for item in TransformDirection}
    if set(directions) != expected or len(directions) != len(set(directions)):
        errors.append(InstrumentProfileViolation("IPV1_TRANSFORM_BINDING", "transform_bindings", "The closed transform set must be unique and complete."))
    if profile.role not in {item.value for item in InstrumentProfileRole}:
        errors.append(InstrumentProfileViolation("IPV1_ROLE_QUANTITY_UNIT_DIRECTION", "role", "Unknown instrument role."))
    if not parameter_gate_accountable(profile.numeric_inventory_id, profile.required_parameter_set_id):
        errors.append(InstrumentProfileViolation("IPV1_PARAMETER_GATE", "required_parameter_set_id", "Upstream parameter gate is not accountable."))
    ordered = tuple(sorted(errors, key=lambda item: (item.rule_id, item.field)))
    handle = None if ordered else AdmittedInstrumentProfile(profile.profile_id, profile.content_sha256, registry_snapshot_id)
    return InstrumentProfileAdmission(not ordered, handle, ordered)


def convert_admitted_profile(handle: AdmittedInstrumentProfile, profile: InstrumentProfile, direction: TransformDirection | str,
                             value: Decimal, *, transforms: Mapping[str, Callable[[Decimal], Decimal]]) -> ConversionResult:
    """Run only the profile-bound transform supplied by the upstream affine-map layer.

    This deliberately contains no affine formula or inverse derivation. The
    injected callable is the exact previously-qualified invocation revision.
    """
    if handle.profile_id != profile.profile_id or handle.profile_content_sha256 != profile.content_sha256 or not _immutable(handle.registry_snapshot_id):
        return ConversionResult(None, str(direction), profile.content_sha256, "", "no_numeric_value", (_bad("IPV1_CONTENT_HASH", "handle", "Handle is stale or forged."),))
    binding = next((item for item in profile.transform_bindings if str(item.direction) == str(direction)), None)
    if binding is None or str(direction) not in transforms or not _immutable(binding.invocation_revision_id):
        return ConversionResult(None, str(direction), profile.content_sha256, "", "no_numeric_value", (_bad("IPV1_TRANSFORM_BINDING", "direction", "No exact bound transform."),))
    if not isinstance(value, Decimal) or not value.is_finite():
        return ConversionResult(None, str(direction), profile.content_sha256, binding.invocation_revision_id, "no_numeric_value", (_bad("IPV1_TRANSFORM_BINDING", "value", "Finite Decimal required."),))
    try:
        with localcontext() as context:
            context.traps[Inexact] = True
            context.traps[Rounded] = True
            output = transforms[str(direction)](value)
            if not isinstance(output, Decimal) or not output.is_finite():
                raise ValueError("non-finite output")
    except Exception as error:
        return ConversionResult(None, str(direction), profile.content_sha256, binding.invocation_revision_id, "no_numeric_value", (_bad("IPV1_TRANSFORM_BINDING", "value", f"Exact affine transform rejected input: {type(error).__name__}."),))
    return ConversionResult(output, str(direction), profile.content_sha256, binding.invocation_revision_id, "convert")


def evaluate_measurement_quality(handle: AdmittedInstrumentProfile, profile: InstrumentProfile, raw_current: Decimal | None,
                                 diagnostics: tuple[str, ...], *, ordered_rules: tuple[tuple[str, str, Callable[[Decimal | None, tuple[str, ...]], bool]], ...]) -> MeasurementQualityResult:
    if handle.profile_id != profile.profile_id or profile.role != InstrumentProfileRole.MEASUREMENT_TRANSMITTER:
        return MeasurementQualityResult("fault", "no_numeric_value", ("IPV1_ROLE_QUANTITY_UNIT_DIRECTION",), raw_current)
    hits = [(rule_id, outcome) for rule_id, outcome, matches in ordered_rules if matches(raw_current, diagnostics)]
    if len(hits) != 1 or hits[0][1] not in {item.value for item in MeasurementQuality}:
        return MeasurementQualityResult("uncertain", "no_numeric_value", ("IPV1_QUALITY_COVERAGE",), raw_current)
    rule_id, outcome = hits[0]
    return MeasurementQualityResult(outcome, "no_numeric_value" if outcome == "missing" else "convert", (rule_id,), raw_current)


def check_command_conformance(handle: AdmittedInstrumentProfile, profile: InstrumentProfile, *, configuration_mode: str,
                              requested_quantity: str, requested_unit: str, requested_direction: str) -> CommandConformanceResult:
    if handle.profile_id != profile.profile_id or profile.role != InstrumentProfileRole.COMMAND_INPUT:
        return CommandConformanceResult("blocked", "no_command_value", ("IPV1_ROLE_QUANTITY_UNIT_DIRECTION",))
    scope = dict(profile.scope_bindings)
    required = {"configuration_mode": configuration_mode, "quantity_kind": requested_quantity, "unit": requested_unit}
    if any(scope.get(key) != value for key, value in required.items()) or requested_direction not in {str(item.direction) for item in profile.transform_bindings}:
        return CommandConformanceResult("blocked", "no_command_value", ("IPV1_DIAGNOSTIC_UNRESOLVED",))
    return CommandConformanceResult("conformant", "convert", ())
