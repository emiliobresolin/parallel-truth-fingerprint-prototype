"""Closed numeric-consumer schema for the thesis evaluation v2 protocol.

The authority inventory must be complete by construction.  Discovering the
numbers that happen to be present in JSON is insufficient because an omitted
field could otherwise fall back to an executable default.  This module defines
the complete set and exact JSON type of every v2 numeric consumer independently
of the loaded configuration, then rejects missing, extra, coerced, and
non-finite values.
"""

from __future__ import annotations

from decimal import Decimal, InvalidOperation
from hashlib import sha256
import json
import re
from types import MappingProxyType
from typing import Mapping


V2_NUMERIC_SCHEMA_VERSION = "academic-v2-numeric-consumer-schema-v1"
_INTEGER = "integer"
_NUMBER = "number"
_MISSING = object()
_NUMERIC_STRING = re.compile(
    r"^[+-]?(?:\d+(?:\.\d*)?|\.\d+)(?:[eE][+-]?\d+)?$"
)


def _build_rules() -> dict[str, str]:
    """Return the explicit, protocol-owned v2 numeric JSON-pointer schema."""

    rules: dict[str, str] = {}

    def add(pointer: str, json_type: str) -> None:
        if pointer in rules:
            raise RuntimeError(f"duplicate v2 numeric-schema pointer: {pointer}")
        rules[pointer] = json_type

    for index in range(5):
        add(f"/pilot_seeds/{index}", _INTEGER)
    for index in range(50):
        add(f"/confirmatory_seeds/{index}", _INTEGER)

    add("/execution_protocol/confirmatory_batch_size", _INTEGER)
    add("/computational_budget/ask_first_cpu_hours", _NUMBER)
    add("/computational_budget/safety_factor", _NUMBER)
    add("/validation_protocol/early_stopping_fraction", _NUMBER)
    add("/validation_protocol/split_seed", _INTEGER)
    add("/validation_protocol/minimum_units_per_role", _INTEGER)

    statistical_integer_fields = (
        "bootstrap_replicates",
        "minimum_bootstrap_clusters",
        "minimum_class_carrying_clusters",
        "minimum_valid_bootstrap_replicates",
        "bootstrap_seed_offset",
        "minimum_stochastic_trials",
        "maximum_stochastic_trials",
        "comparison_seed",
        "permutation_replicates",
        "curve_max_points",
    )
    statistical_number_fields = (
        "confidence_level",
        "minimum_valid_bootstrap_fraction",
        "target_ci_half_width",
    )
    for field in statistical_integer_fields:
        add(f"/statistical_protocol/{field}", _INTEGER)
    for field in statistical_number_fields:
        add(f"/statistical_protocol/{field}", _NUMBER)
    add("/statistical_protocol/threshold/target_fpr", _NUMBER)
    add("/statistical_protocol/threshold/normal_quantile", _NUMBER)
    for index in range(5):
        add(
            f"/statistical_protocol/threshold/sensitivity_normal_quantiles/{index}",
            _NUMBER,
        )

    def add_common_dataset_fields(dataset: str) -> None:
        prefix = f"/datasets/{dataset}"
        add(f"{prefix}/partition_seed", _INTEGER)
        for phase in ("pilot", "confirmatory"):
            add(f"{prefix}/minimum_support/{phase}/test_normal", _INTEGER)
            add(f"{prefix}/minimum_support/{phase}/test_attack", _INTEGER)
        for field in ("sequence_length", "stride", "max_windows_per_unit"):
            add(f"{prefix}/window/{field}", _INTEGER)

    def add_phase_allocation(dataset: str, roles: tuple[str, ...]) -> None:
        prefix = f"/datasets/{dataset}/phase_allocation"
        for phase in ("pilot", "confirmatory"):
            for collection in ("offsets", "counts"):
                for role in roles:
                    add(f"{prefix}/{phase}/{collection}/{role}", _INTEGER)

    def add_categorical_models(dataset: str) -> None:
        prefix = f"/datasets/{dataset}/models"
        add(f"{prefix}/categorical-unigram/laplace_alpha", _NUMBER)
        add(f"{prefix}/robust-distance/hash_bins", _INTEGER)
        add(f"{prefix}/robust-distance/max_robust_z", _NUMBER)
        add(f"{prefix}/pca-autoencoder/hash_bins", _INTEGER)
        add(f"{prefix}/pca-autoencoder/latent_dimensions", _INTEGER)
        for field in (
            "epochs",
            "batch_size",
            "hidden_units",
            "latent_units",
            "embedding_dimensions",
            "patience",
        ):
            add(f"{prefix}/recurrent-autoencoder/{field}", _INTEGER)
        for field in ("learning_rate", "min_delta"):
            add(f"{prefix}/recurrent-autoencoder/{field}", _NUMBER)

    add_common_dataset_fields("adfa-ld")
    add("/datasets/adfa-ld/normal_validation_fraction", _NUMBER)
    add("/datasets/adfa-ld/numeric_clip", _NUMBER)
    for phase in ("pilot", "confirmatory"):
        for field in ("train", "validation", "test_normal", "test_attack_per_class"):
            add(f"/datasets/adfa-ld/phase_caps/{phase}/{field}", _INTEGER)
    add_phase_allocation(
        "adfa-ld", ("train", "validation", "test_normal", "attack_per_class")
    )
    add_categorical_models("adfa-ld")

    add_common_dataset_fields("lid-ds-2021")
    # Explicit even though categorical preprocessing does not scale tokens: the
    # shared preprocessing call consumes this value and may not use a fallback.
    add("/datasets/lid-ds-2021/numeric_clip", _NUMBER)
    for phase in ("pilot", "confirmatory"):
        add(
            f"/datasets/lid-ds-2021/phase_caps/{phase}/archives_per_scenario_partition",
            _INTEGER,
        )
    add_phase_allocation(
        "lid-ds-2021",
        ("training", "validation", "test-normal", "test-normal-and-attack"),
    )
    add_categorical_models("lid-ds-2021")

    add_common_dataset_fields("hai-23.05")
    add("/datasets/hai-23.05/block_rows", _INTEGER)
    add("/datasets/hai-23.05/numeric_clip", _NUMBER)
    for phase in ("pilot", "confirmatory"):
        add(f"/datasets/hai-23.05/phase_caps/{phase}/train/normal", _INTEGER)
        add(f"/datasets/hai-23.05/phase_caps/{phase}/validation/normal", _INTEGER)
        add(f"/datasets/hai-23.05/phase_caps/{phase}/test/total", _INTEGER)
    add_phase_allocation("hai-23.05", ("train", "validation", "test"))
    hai_models = "/datasets/hai-23.05/models"
    add(f"{hai_models}/robust-distance/max_robust_z", _NUMBER)
    add(f"{hai_models}/pca-autoencoder/latent_dimensions", _INTEGER)
    for field in (
        "epochs",
        "batch_size",
        "hidden_units",
        "latent_units",
        "patience",
    ):
        add(f"{hai_models}/recurrent-autoencoder/{field}", _INTEGER)
    for field in ("learning_rate", "min_delta"):
        add(f"{hai_models}/recurrent-autoencoder/{field}", _NUMBER)
    return dict(sorted(rules.items()))


V2_NUMERIC_RULES: Mapping[str, str] = MappingProxyType(_build_rules())
V2_NUMERIC_SCHEMA_IDENTITY = "sha256:" + sha256(
    json.dumps(
        {
            "schema_version": V2_NUMERIC_SCHEMA_VERSION,
            "rules": dict(V2_NUMERIC_RULES),
        },
        sort_keys=True,
        separators=(",", ":"),
        ensure_ascii=True,
    ).encode("ascii")
).hexdigest()


def _decode_pointer(pointer: str) -> tuple[str, ...]:
    return tuple(
        segment.replace("~1", "/").replace("~0", "~")
        for segment in pointer.removeprefix("/").split("/")
    )


def _pointer_value(config: Mapping[str, object], pointer: str) -> object:
    current: object = config
    for segment in _decode_pointer(pointer):
        if isinstance(current, Mapping):
            if segment not in current:
                return _MISSING
            current = current[segment]
        elif isinstance(current, (list, tuple)):
            if not segment.isdecimal() or int(segment) >= len(current):
                return _MISSING
            current = current[int(segment)]
        else:
            return _MISSING
    return current


def _scalar_leaves(value: object, pointer: str = "") -> list[tuple[str, object]]:
    leaves: list[tuple[str, object]] = []
    if isinstance(value, Mapping):
        for key, item in sorted(value.items(), key=lambda pair: str(pair[0])):
            escaped = str(key).replace("~", "~0").replace("/", "~1")
            leaves.extend(_scalar_leaves(item, f"{pointer}/{escaped}"))
    elif isinstance(value, (list, tuple)):
        for index, item in enumerate(value):
            leaves.extend(_scalar_leaves(item, f"{pointer}/{index}"))
    else:
        leaves.append((pointer, value))
    return leaves


def _finite_decimal(value: object) -> Decimal | None:
    if type(value) not in (int, float):
        return None
    try:
        parsed = Decimal(str(value))
    except (InvalidOperation, ValueError):
        return None
    if not parsed.is_finite() or (parsed == 0 and parsed.is_signed()):
        return None
    return parsed


def _render_number(value: int | float) -> str:
    parsed = _finite_decimal(value)
    if parsed is None:  # pragma: no cover - guarded by schema validation
        raise ValueError(f"invalid finite JSON number {value!r}")
    return format(parsed, "f")


def validate_v2_numeric_schema(config: Mapping[str, object]) -> None:
    """Fail closed unless the config exactly implements the numeric schema."""

    issues: list[str] = []
    for pointer, expected_type in V2_NUMERIC_RULES.items():
        value = _pointer_value(config, pointer)
        if value is _MISSING:
            issues.append(f"missing numeric consumer {pointer}")
            continue
        if expected_type == _INTEGER:
            if type(value) is not int:
                issues.append(
                    f"{pointer} must be a JSON integer (Boolean/string coercion forbidden)"
                )
        elif _finite_decimal(value) is None:
            issues.append(
                f"{pointer} must be a finite JSON number "
                "(Boolean/string coercion forbidden)"
            )

    for pointer, value in _scalar_leaves(config):
        if type(value) in (int, float) and pointer not in V2_NUMERIC_RULES:
            issues.append(f"unknown numeric consumer {pointer}")
        elif (
            isinstance(value, str)
            and _NUMERIC_STRING.fullmatch(value.strip()) is not None
        ):
            issues.append(f"numeric string is forbidden at {pointer}")

    if issues:
        raise ValueError("v2 numeric schema violation: " + "; ".join(sorted(set(issues))))


def v2_numeric_consumers(
    config: Mapping[str, object],
) -> list[tuple[str, str, str]]:
    """Return validated numeric consumers in stable JSON-pointer order."""

    validate_v2_numeric_schema(config)
    consumers: list[tuple[str, str, str]] = []
    for pointer, json_type in V2_NUMERIC_RULES.items():
        value = _pointer_value(config, pointer)
        if json_type == _INTEGER:
            rendered = str(value)
        else:
            rendered = _render_number(value)  # type: ignore[arg-type]
        consumers.append((pointer, rendered, json_type))
    return consumers


__all__ = [
    "V2_NUMERIC_RULES",
    "V2_NUMERIC_SCHEMA_IDENTITY",
    "V2_NUMERIC_SCHEMA_VERSION",
    "v2_numeric_consumers",
    "validate_v2_numeric_schema",
]
