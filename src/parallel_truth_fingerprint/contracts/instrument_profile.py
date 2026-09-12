"""Closed, immutable InstrumentProfile.v1 contract.

Profiles are descriptions, never live-device configuration or acquisition.
"""

from __future__ import annotations

import hashlib
import json
from dataclasses import dataclass, fields
from enum import StrEnum
from typing import Any


class InstrumentProfileRole(StrEnum):
    MEASUREMENT_TRANSMITTER = "measurement_transmitter"
    COMMAND_INPUT = "command_input"


class TransformDirection(StrEnum):
    CURRENT_TO_NORMALIZED = "current_to_normalized"
    CURRENT_TO_ENGINEERING_OR_REFERENCE = "current_to_engineering_or_reference"
    ENGINEERING_OR_REFERENCE_TO_CURRENT = "engineering_or_reference_to_current"


class MeasurementQuality(StrEnum):
    IN_RANGE = "in_range"
    UNDER_RANGE = "under_range"
    OVER_RANGE = "over_range"
    MISSING = "missing"
    UNCERTAIN = "uncertain"
    FAULT = "fault"


class ConversionDisposition(StrEnum):
    CONVERT = "convert"
    NO_NUMERIC_VALUE = "no_numeric_value"
    NO_COMMAND_VALUE = "no_command_value"


def _value(value: Any) -> Any:
    if isinstance(value, StrEnum):
        return value.value
    if isinstance(value, tuple):
        return [_value(item) for item in value]
    if hasattr(value, "to_dict"):
        return value.to_dict()
    return value


class _Record:
    def to_dict(self) -> dict[str, Any]:
        return {field.name: _value(getattr(self, field.name)) for field in fields(self)}


@dataclass(frozen=True)
class TransformBinding(_Record):
    direction: TransformDirection | str
    invocation_revision_id: str
    input_parameter_revision_ids: tuple[str, ...]
    output_parameter_revision_ids: tuple[str, ...]


@dataclass(frozen=True)
class InstrumentProfile(_Record):
    schema_version: str
    profile_id: str
    role: InstrumentProfileRole | str
    manufacturer: str
    model: str
    variant_slots: tuple[tuple[str, str], ...]
    quantity_kind: str
    unit: str
    source_use_revision_ids: tuple[str, ...]
    source_locators: tuple[str, ...]
    numeric_inventory_id: str
    required_parameter_set_id: str
    transform_bindings: tuple[TransformBinding, ...]
    policy_binding_ids: tuple[str, ...]
    scope_bindings: tuple[tuple[str, str], ...]
    limitations: tuple[str, ...]
    predecessor_id: str | None
    content_sha256: str
    authorization_effect: str = "none"

    def __post_init__(self) -> None:
        for name in ("variant_slots", "source_use_revision_ids", "source_locators", "policy_binding_ids", "scope_bindings", "limitations"):
            # Canonical ordering must not erase duplicate evidence bindings: the
            # admission boundary needs to be able to reject them explicitly.
            object.__setattr__(self, name, tuple(sorted(getattr(self, name))))
        object.__setattr__(self, "transform_bindings", tuple(sorted(
            self.transform_bindings, key=lambda item: str(item.direction),
        )))

    def without_content_hash(self) -> dict[str, Any]:
        value = self.to_dict()
        value.pop("content_sha256")
        return value

    def computed_content_sha256(self) -> str:
        encoded = json.dumps(self.without_content_hash(), sort_keys=True, ensure_ascii=True, separators=(",", ":")).encode("ascii")
        return "sha256:" + hashlib.sha256(encoded).hexdigest()


def parse_instrument_profile(payload: object) -> InstrumentProfile:
    """Strict, side-effect-free parser for the catalog payload shape.

    Parsing deliberately does not admit a profile; callers still require the
    exact source, parameter and registry resolvers at the admission boundary.
    """
    if not isinstance(payload, dict):
        raise ValueError("IPV1_SCHEMA_VERSION_TOKEN: object required")
    expected = {field.name for field in fields(InstrumentProfile)}
    if set(payload) != expected:
        raise ValueError("IPV1_SCHEMA_VERSION_TOKEN: fields invalid")
    collections = ("variant_slots", "source_use_revision_ids", "source_locators", "transform_bindings", "policy_binding_ids", "scope_bindings", "limitations")
    if any(not isinstance(payload[name], list) for name in collections):
        raise ValueError("IPV1_SCHEMA_VERSION_TOKEN: collections invalid")
    if any(not isinstance(item, str) for name in ("source_use_revision_ids", "source_locators", "policy_binding_ids", "limitations") for item in payload[name]):
        raise ValueError("IPV1_SCHEMA_VERSION_TOKEN: collection members invalid")
    if any(not isinstance(item, list) or len(item) != 2 or not all(isinstance(part, str) for part in item)
           for item in payload["variant_slots"] + payload["scope_bindings"]):
        raise ValueError("IPV1_SCHEMA_VERSION_TOKEN: slots invalid")
    transform_fields = {field.name for field in fields(TransformBinding)}
    bindings: list[TransformBinding] = []
    for value in payload["transform_bindings"]:
        if not isinstance(value, dict) or set(value) != transform_fields or any(
            not isinstance(value[name], list) for name in ("input_parameter_revision_ids", "output_parameter_revision_ids")
        ):
            raise ValueError("IPV1_SCHEMA_VERSION_TOKEN: transform binding invalid")
        bindings.append(TransformBinding(
            value["direction"], value["invocation_revision_id"],
            tuple(value["input_parameter_revision_ids"]), tuple(value["output_parameter_revision_ids"]),
        ))
    scalar_names = expected - set(collections) - {"predecessor_id", "authorization_effect"}
    if any(not isinstance(payload[name], str) for name in scalar_names | {"authorization_effect"}) or (
        payload["predecessor_id"] is not None and not isinstance(payload["predecessor_id"], str)
    ):
        raise ValueError("IPV1_SCHEMA_VERSION_TOKEN: scalar types invalid")
    return InstrumentProfile(
        **{name: payload[name] for name in expected - set(collections) - {"predecessor_id", "authorization_effect"}},
        variant_slots=tuple(tuple(item) for item in payload["variant_slots"]),
        source_use_revision_ids=tuple(payload["source_use_revision_ids"]),
        source_locators=tuple(payload["source_locators"]), transform_bindings=tuple(bindings),
        policy_binding_ids=tuple(payload["policy_binding_ids"]),
        scope_bindings=tuple(tuple(item) for item in payload["scope_bindings"]),
        limitations=tuple(payload["limitations"]), predecessor_id=payload["predecessor_id"],
        authorization_effect=payload["authorization_effect"],
    )
