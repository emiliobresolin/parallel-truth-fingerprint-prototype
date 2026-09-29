"""Resumable, leakage-safe execution of the thesis evaluation matrix.

The academic path is intentionally self-contained.  A cell is identified by
the frozen configuration, selected source units, preprocessing state, model
configuration, phase, and seed.  Completed cell and prediction artifacts are
content-addressed and never silently replaced.
"""

from __future__ import annotations

from dataclasses import dataclass
from datetime import datetime, timezone
from decimal import Decimal, InvalidOperation
from hashlib import sha256
import importlib.metadata
import json
import locale
import math
import os
from pathlib import Path
import platform
import sys
import tempfile
import time
from typing import Iterable, Mapping, Sequence

import numpy as np

from parallel_truth_fingerprint.lstm_service.offline_training.academic_numeric_schema import (
    V2_NUMERIC_SCHEMA_IDENTITY,
    V2_NUMERIC_SCHEMA_VERSION,
    v2_numeric_consumers,
    validate_v2_numeric_schema,
)
from parallel_truth_fingerprint.lstm_service.offline_training.academic_metrics import (
    aggregate_repeated_estimates,
    binary_operating_metrics,
    bootstrap_confidence_intervals,
    calibrate_threshold,
    curve_points,
    derive_repetition_count,
    event_metrics,
    holm_adjust,
    paired_comparison,
    per_class_detection_metrics,
    ranking_metrics,
    score_distribution,
)
from parallel_truth_fingerprint.lstm_service.offline_training.academic_models import (
    fit_detector,
    model_is_deterministic,
)
from parallel_truth_fingerprint.lstm_service.offline_training.academic_protocol import (
    AcademicDataset,
    DISJOINT_CONTENT_PRIORITY_SLICES_V2,
    DISJOINT_PRIORITY_SLICES_V1,
    PreparedDataset,
    PreparedPartition,
    aggregate_window_scores,
    audit_group_leakage,
    audit_window_parentage,
    canonical_json_hash,
    file_sha256,
    fit_preprocessing,
    load_academic_dataset,
    prepare_dataset_arrays,
    support_summary,
    validate_academic_support,
    window_dataset,
)
from parallel_truth_fingerprint.contracts.parameter_evidence import (
    AccountabilityOutcome,
    TemporalGateContext,
)
from parallel_truth_fingerprint.evidence.parameter_evidence import (
    load_parameter_catalog,
    validate_parameter_gate,
)
from parallel_truth_fingerprint.evidence.source_catalog import load_source_catalog


RUNNER_PROTOCOL_V1 = "thesis-evaluation-runner-v1"
RUNNER_PROTOCOL = "thesis-evaluation-runner-v2"
# Kept as the compatibility default because external tests and archived v1
# configs import this token.  New academic execution uses CONFIG_SCHEMA_V2 and
# receives the stricter, fail-closed gates below.
CONFIG_SCHEMA = "thesis-evaluation-config-v1"
CONFIG_SCHEMA_V2 = "thesis-evaluation-config-v2"
NUMERIC_REQUIREMENTS_SCHEMA = "academic-parameter-requirements-v2"
_SUPPORTED_CONFIG_SCHEMAS = {CONFIG_SCHEMA, CONFIG_SCHEMA_V2}
_OFFICIAL_DATASETS = {"adfa-ld", "lid-ds-2021", "hai-23.05"}
_MEMORY_PREPARED_CACHE: dict[str, PreparedDataset] = {}
V2_PILOT_TRIALS = 5
V2_CONFIRMATORY_TRIALS = 50
V2_CONFIRMATORY_BATCH_COUNT = 5
V2_CONFIRMATORY_BATCH_SIZE = 10
V2_CONFIRMATORY_STANDALONE_PREFLIGHT_INVOCATIONS = 1
V2_CONFIRMATORY_PREFLIGHT_INVOCATIONS = (
    V2_CONFIRMATORY_STANDALONE_PREFLIGHT_INVOCATIONS
    + V2_CONFIRMATORY_BATCH_COUNT
)
UINT32_MAX = (1 << 32) - 1


@dataclass(frozen=True)
class AcademicPaths:
    root: Path
    phase: Path
    cells: Path
    predictions: Path
    transactions: Path
    reports: Path


def load_academic_config(path: Path) -> dict[str, object]:
    """Load and minimally validate a researcher-controlled JSON config."""

    config_path = Path(path).resolve()
    try:
        value = json.loads(
            config_path.read_text(encoding="utf-8"),
            parse_constant=lambda token: (_ for _ in ()).throw(
                ValueError(f"non-finite JSON number is forbidden: {token}")
            ),
        )
    except (OSError, json.JSONDecodeError) as exc:
        raise ValueError(f"Cannot read academic config {config_path}: {exc}") from exc
    if not isinstance(value, dict):
        raise ValueError("Academic config must be a JSON object.")
    if value.get("schema_version") not in _SUPPORTED_CONFIG_SCHEMAS:
        raise ValueError(
            "schema_version must be one of "
            f"{sorted(_SUPPORTED_CONFIG_SCHEMAS)!r}, got {value.get('schema_version')!r}."
        )
    experiment_id = str(value.get("experiment_id", "")).strip()
    if not experiment_id or any(character not in "abcdefghijklmnopqrstuvwxyz0123456789-_" for character in experiment_id):
        raise ValueError("experiment_id must contain only lowercase letters, digits, '-' and '_'.")
    datasets = value.get("datasets")
    if not isinstance(datasets, dict) or not datasets:
        raise ValueError("datasets must be a non-empty object.")
    statistics = value.get("statistical_protocol")
    if not isinstance(statistics, dict):
        raise ValueError("statistical_protocol must be an object.")
    for phase in ("pilot", "confirmatory"):
        seeds = value.get(f"{phase}_seeds")
        if not isinstance(seeds, list) or not seeds:
            raise ValueError(f"{phase}_seeds must be a non-empty list.")
        if any(not isinstance(seed, int) or isinstance(seed, bool) for seed in seeds):
            raise ValueError(
                f"{phase}_seeds must contain only integers; "
                "string-equivalent duplicates are invalid."
            )
        normalized = [int(seed) for seed in seeds]
        for index, seed in enumerate(normalized):
            _validate_uint32_seed(seed, f"{phase}_seeds[{index}]")
        if len(normalized) != len(set(normalized)):
            raise ValueError(f"{phase}_seeds must not contain duplicates.")
    if value.get("schema_version") == CONFIG_SCHEMA_V2:
        validate_v2_numeric_schema(value)
        required_metrics = {
            "f1",
            "balanced_accuracy",
            "mcc",
            "auroc",
            "auprc",
        }
        reported_metrics = statistics.get("reported_metrics")
        if (
            not isinstance(reported_metrics, list)
            or not reported_metrics
            or any(not isinstance(item, str) for item in reported_metrics)
            or len(reported_metrics) != len(set(reported_metrics))
            or not required_metrics.issubset(reported_metrics)
        ):
            raise ValueError(
                "v2 statistical_protocol.reported_metrics must contain each required "
                "classification/ranking endpoint exactly once."
            )
        if statistics.get("primary_metric") not in reported_metrics:
            raise ValueError(
                "v2 statistical_protocol.primary_metric must be one of reported_metrics."
            )
        if statistics.get("multiplicity") != "Holm":
            raise ValueError(
                "v2 statistical_protocol.multiplicity must be 'Holm'."
            )
        governance = value.get("numeric_authority")
        if not isinstance(governance, dict):
            raise ValueError("v2 numeric_authority must be an object.")
        for field in (
            "requirements_path",
            "requirements_sha256",
            "temporal_context_path",
            "temporal_context_sha256",
        ):
            if not isinstance(governance.get(field), str) or not str(governance[field]).strip():
                raise ValueError(f"v2 numeric_authority.{field} is required.")
        if governance.get("numeric_schema_version") != V2_NUMERIC_SCHEMA_VERSION:
            raise ValueError(
                "v2 numeric_authority.numeric_schema_version does not match the "
                "implementation-owned complete numeric schema."
            )
        if governance.get("numeric_schema_identity") != V2_NUMERIC_SCHEMA_IDENTITY:
            raise ValueError(
                "v2 numeric_authority.numeric_schema_identity does not match the "
                "implementation-owned complete numeric schema."
            )
        for dataset_key, dataset_value in datasets.items():
            if not isinstance(dataset_value, dict):
                raise ValueError(f"datasets.{dataset_key} must be an object.")
            if dataset_value.get("evidence_origin") != "official_native":
                raise ValueError(
                    f"v2 official dataset {dataset_key!r} must declare evidence_origin='official_native'."
                )
            _validate_phase_allocation_shape(str(dataset_key), dataset_value)
            models = dataset_value.get("models")
            if not isinstance(models, Mapping) or not models:
                raise ValueError(f"datasets.{dataset_key}.models must be a non-empty object.")
            for model_name, model_value in models.items():
                if not isinstance(model_value, Mapping):
                    raise ValueError(
                        f"datasets.{dataset_key}.models.{model_name} must be an object."
                    )
                if "max_robust_z" in model_value:
                    max_robust_z = model_value.get("max_robust_z")
                    if (
                        not isinstance(max_robust_z, (int, float))
                        or isinstance(max_robust_z, bool)
                        or not math.isfinite(float(max_robust_z))
                        or float(max_robust_z) <= 0.0
                    ):
                        raise ValueError(
                            f"datasets.{dataset_key}.models.{model_name}.max_robust_z "
                            "must be finite and positive."
                        )
        validation_protocol = value.get("validation_protocol")
        if not isinstance(validation_protocol, dict):
            raise ValueError("v2 validation_protocol must be an object.")
        minimum_bootstrap_clusters = statistics.get("minimum_bootstrap_clusters")
        if (
            not isinstance(minimum_bootstrap_clusters, int)
            or isinstance(minimum_bootstrap_clusters, bool)
            or minimum_bootstrap_clusters < 2
        ):
            raise ValueError(
                "v2 statistical_protocol.minimum_bootstrap_clusters must be "
                "an integer of at least two."
            )
        minimum_class_clusters = statistics.get(
            "minimum_class_carrying_clusters"
        )
        if (
            not isinstance(minimum_class_clusters, int)
            or isinstance(minimum_class_clusters, bool)
            or minimum_class_clusters < 2
        ):
            raise ValueError(
                "v2 statistical_protocol.minimum_class_carrying_clusters must "
                "be an integer of at least two."
            )
        bootstrap_replicates = statistics.get("bootstrap_replicates")
        minimum_valid_replicates = statistics.get(
            "minimum_valid_bootstrap_replicates"
        )
        minimum_valid_fraction = statistics.get(
            "minimum_valid_bootstrap_fraction"
        )
        if (
            not isinstance(bootstrap_replicates, int)
            or isinstance(bootstrap_replicates, bool)
            or bootstrap_replicates < 1
            or not isinstance(minimum_valid_replicates, int)
            or isinstance(minimum_valid_replicates, bool)
            or not 1 <= minimum_valid_replicates <= bootstrap_replicates
        ):
            raise ValueError(
                "v2 minimum_valid_bootstrap_replicates must be between one and "
                "bootstrap_replicates."
            )
        if (
            not isinstance(minimum_valid_fraction, (int, float))
            or isinstance(minimum_valid_fraction, bool)
            or not math.isfinite(float(minimum_valid_fraction))
            or not 0.0 < float(minimum_valid_fraction) <= 1.0
        ):
            raise ValueError(
                "v2 minimum_valid_bootstrap_fraction must be finite in (0, 1]."
            )
        for seed_field in ("bootstrap_seed_offset", "comparison_seed"):
            _validate_uint32_seed(
                statistics.get(seed_field), f"statistical_protocol.{seed_field}"
            )
        fraction = validation_protocol.get("early_stopping_fraction")
        split_seed = validation_protocol.get("split_seed")
        minimum = validation_protocol.get("minimum_units_per_role")
        if (
            not isinstance(fraction, (int, float))
            or isinstance(fraction, bool)
            or not math.isfinite(float(fraction))
            or not 0.0 < float(fraction) < 1.0
        ):
            raise ValueError(
                "v2 validation_protocol.early_stopping_fraction must be finite and between zero and one."
            )
        _validate_uint32_seed(split_seed, "validation_protocol.split_seed")
        if (
            not isinstance(minimum, int)
            or isinstance(minimum, bool)
            or minimum < 1
        ):
            raise ValueError(
                "v2 validation_protocol.minimum_units_per_role must be a positive integer."
            )
        for dataset_key, dataset_value in datasets.items():
            if "partition_seed" in dataset_value:
                _validate_uint32_seed(
                    dataset_value.get("partition_seed"),
                    f"datasets.{dataset_key}.partition_seed",
                )
        _validate_v2_budget(value)
        _validate_v2_execution_schedule(value)
    return {str(key): item for key, item in value.items()}


def config_identity(config: Mapping[str, object]) -> str:
    return canonical_json_hash(config)


def _is_v2(config: Mapping[str, object]) -> bool:
    return config.get("schema_version") == CONFIG_SCHEMA_V2


def _runner_protocol(config: Mapping[str, object]) -> str:
    return RUNNER_PROTOCOL if _is_v2(config) else RUNNER_PROTOCOL_V1


def _validate_uint32_seed(value: object, field: str) -> int:
    if (
        not isinstance(value, int)
        or isinstance(value, bool)
        or not 0 <= value <= UINT32_MAX
    ):
        raise ValueError(f"{field} must be an integer in the uint32 range 0..{UINT32_MAX}.")
    return int(value)


def _validate_v2_budget(config: Mapping[str, object]) -> None:
    budget = config.get("computational_budget")
    if not isinstance(budget, Mapping):
        raise ValueError("v2 computational_budget must be an object.")
    safety_factor = budget.get("safety_factor")
    ask_first = budget.get("ask_first_cpu_hours")
    if (
        not isinstance(safety_factor, (int, float))
        or isinstance(safety_factor, bool)
        or not math.isfinite(float(safety_factor))
        or float(safety_factor) < 1.0
    ):
        raise ValueError(
            "v2 computational_budget.safety_factor must be finite and at least 1."
        )
    if (
        not isinstance(ask_first, (int, float))
        or isinstance(ask_first, bool)
        or not math.isfinite(float(ask_first))
        or float(ask_first) <= 0.0
    ):
        raise ValueError(
            "v2 computational_budget.ask_first_cpu_hours must be finite and positive."
        )


def _confirmatory_seed_batches(
    config: Mapping[str, object],
) -> tuple[tuple[int, ...], ...]:
    """Derive the immutable positional batches without duplicating seed authority."""

    seeds = config.get("confirmatory_seeds")
    execution = config.get("execution_protocol")
    if not isinstance(seeds, list) or not isinstance(execution, Mapping):
        raise ValueError(
            "v2 confirmatory_seeds and execution_protocol must be present before batching."
        )
    batch_size = execution.get("confirmatory_batch_size")
    if (
        not isinstance(batch_size, int)
        or isinstance(batch_size, bool)
        or batch_size <= 0
    ):
        raise ValueError("v2 confirmatory_batch_size must be a positive integer.")
    if len(seeds) % batch_size:
        raise ValueError(
            "v2 confirmatory seed count must be exactly divisible by the frozen batch size."
        )
    return tuple(
        tuple(int(seed) for seed in seeds[start : start + batch_size])
        for start in range(0, len(seeds), batch_size)
    )


def _validate_v2_execution_schedule(config: Mapping[str, object]) -> None:
    """Fail closed unless the fixed Iteration-3 seed ledger is self-consistent."""

    pilot_seeds = config.get("pilot_seeds")
    confirmatory_seeds = config.get("confirmatory_seeds")
    if not isinstance(pilot_seeds, list) or len(pilot_seeds) != V2_PILOT_TRIALS:
        raise ValueError(
            f"v2 pilot_seeds must contain exactly {V2_PILOT_TRIALS} seeds."
        )
    if (
        not isinstance(confirmatory_seeds, list)
        or len(confirmatory_seeds) != V2_CONFIRMATORY_TRIALS
    ):
        raise ValueError(
            "v2 confirmatory_seeds must contain exactly "
            f"{V2_CONFIRMATORY_TRIALS} seeds."
        )
    normalized_pilot = [
        _validate_uint32_seed(value, f"pilot_seeds[{index}]")
        for index, value in enumerate(pilot_seeds)
    ]
    normalized_confirmatory = [
        _validate_uint32_seed(value, f"confirmatory_seeds[{index}]")
        for index, value in enumerate(confirmatory_seeds)
    ]
    if len(normalized_pilot) != len(set(normalized_pilot)):
        raise ValueError("v2 pilot_seeds must not contain duplicates.")
    if len(normalized_confirmatory) != len(set(normalized_confirmatory)):
        raise ValueError("v2 confirmatory_seeds must not contain duplicates.")
    if set(normalized_pilot) & set(normalized_confirmatory):
        raise ValueError("v2 pilot and confirmatory seed schedules must be disjoint.")

    execution = config.get("execution_protocol")
    if not isinstance(execution, Mapping):
        raise ValueError("v2 execution_protocol must be an object.")
    if execution.get("confirmatory_batch_size") != V2_CONFIRMATORY_BATCH_SIZE:
        raise ValueError(
            "v2 execution_protocol.confirmatory_batch_size must be "
            f"{V2_CONFIRMATORY_BATCH_SIZE}."
        )
    if execution.get("seed_schedule_policy") != "all-configured-seeds-in-order":
        raise ValueError(
            "v2 execution_protocol.seed_schedule_policy must freeze all configured "
            "seeds in their declared order."
        )
    if (
        execution.get("interim_analysis_policy")
        != "withheld-until-full-matrix-authenticated"
    ):
        raise ValueError(
            "v2 execution_protocol.interim_analysis_policy must withhold outcomes "
            "until the full matrix is authenticated."
        )
    batches = _confirmatory_seed_batches(config)
    if len(batches) != V2_CONFIRMATORY_BATCH_COUNT:
        raise ValueError(
            "v2 confirmatory seeds must form exactly "
            f"{V2_CONFIRMATORY_BATCH_COUNT} positional batches."
        )

    statistics = config.get("statistical_protocol")
    if not isinstance(statistics, Mapping):
        raise ValueError("v2 statistical_protocol must be an object.")
    if statistics.get("maximum_stochastic_trials") != V2_CONFIRMATORY_TRIALS:
        raise ValueError(
            "v2 statistical_protocol.maximum_stochastic_trials must be "
            f"{V2_CONFIRMATORY_TRIALS}."
        )
    minimum_trials = statistics.get("minimum_stochastic_trials")
    if (
        not isinstance(minimum_trials, int)
        or isinstance(minimum_trials, bool)
        or not 2 <= minimum_trials <= V2_CONFIRMATORY_TRIALS
    ):
        raise ValueError(
            "v2 statistical_protocol.minimum_stochastic_trials must be an integer "
            "between 2 and 50."
        )
    target_half_width = statistics.get("target_ci_half_width")
    confidence_level = statistics.get("confidence_level")
    if (
        not isinstance(target_half_width, (int, float))
        or isinstance(target_half_width, bool)
        or not math.isfinite(float(target_half_width))
        or float(target_half_width) <= 0.0
    ):
        raise ValueError(
            "v2 statistical_protocol.target_ci_half_width must be finite and positive."
        )
    if (
        not isinstance(confidence_level, (int, float))
        or isinstance(confidence_level, bool)
        or not math.isfinite(float(confidence_level))
        or not 0.0 < float(confidence_level) < 1.0
    ):
        raise ValueError(
            "v2 statistical_protocol.confidence_level must be strictly between zero and one."
        )

    datasets = config.get("datasets")
    if not isinstance(datasets, Mapping):
        raise ValueError("v2 datasets must be an object.")
    for dataset_name, raw_dataset in datasets.items():
        if not isinstance(raw_dataset, Mapping):
            raise ValueError(f"datasets.{dataset_name} must be an object.")
        models = raw_dataset.get("models")
        if not isinstance(models, Mapping) or not models:
            raise ValueError(f"datasets.{dataset_name}.models must be non-empty.")
        for model_name, raw_model in models.items():
            if not isinstance(raw_model, Mapping):
                raise ValueError(
                    f"datasets.{dataset_name}.models.{model_name} must be an object."
                )
            declared = raw_model.get("deterministic")
            if not isinstance(declared, bool):
                raise ValueError(
                    f"datasets.{dataset_name}.models.{model_name}.deterministic "
                    "must be Boolean."
                )
            expected = model_is_deterministic(str(model_name))
            if declared is not expected:
                raise ValueError(
                    f"datasets.{dataset_name}.models.{model_name}.deterministic={declared!r} "
                    f"conflicts with the implementation-owned classification {expected!r}."
                )


def _validate_phase_allocation_shape(
    dataset_key: str, dataset: Mapping[str, object]
) -> None:
    allocation = dataset.get("phase_allocation")
    if not isinstance(allocation, Mapping):
        raise ValueError(f"datasets.{dataset_key}.phase_allocation must be an object.")
    allowed_methods = {DISJOINT_PRIORITY_SLICES_V1}
    if dataset_key == "lid-ds-2021":
        allowed_methods.add(DISJOINT_CONTENT_PRIORITY_SLICES_V2)
    if allocation.get("method") not in allowed_methods:
        raise ValueError(
            f"datasets.{dataset_key}.phase_allocation.method must be "
            f"one of {sorted(allowed_methods)!r}."
        )
    phase_records: dict[str, tuple[dict[str, int], dict[str, int]]] = {}
    for phase in ("pilot", "confirmatory"):
        phase_record = allocation.get(phase)
        if not isinstance(phase_record, Mapping):
            raise ValueError(
                f"datasets.{dataset_key}.phase_allocation.{phase} must be an object."
            )
        raw_offsets = phase_record.get("offsets")
        raw_counts = phase_record.get("counts")
        if not isinstance(raw_offsets, Mapping) or not raw_offsets:
            raise ValueError(
                f"datasets.{dataset_key}.phase_allocation.{phase}.offsets must be non-empty."
            )
        if not isinstance(raw_counts, Mapping) or set(raw_counts) != set(raw_offsets):
            raise ValueError(
                f"datasets.{dataset_key}.phase_allocation.{phase}.counts must match offsets."
            )
        for field_name, values in (("offsets", raw_offsets), ("counts", raw_counts)):
            if any(
                not isinstance(value, int)
                or isinstance(value, bool)
                or value < (1 if field_name == "counts" else 0)
                for value in values.values()
            ):
                raise ValueError(
                    f"datasets.{dataset_key}.phase_allocation.{phase}.{field_name} "
                    "contains an invalid integer."
                )
        phase_records[phase] = (
            {str(key): int(value) for key, value in raw_offsets.items()},
            {str(key): int(value) for key, value in raw_counts.items()},
        )
    pilot_offsets, pilot_counts = phase_records["pilot"]
    confirm_offsets, confirm_counts = phase_records["confirmatory"]
    if set(pilot_offsets) != set(confirm_offsets):
        raise ValueError(
            f"datasets.{dataset_key} phase allocation strata differ across phases."
        )
    for stratum in pilot_offsets:
        pilot_interval = (
            pilot_offsets[stratum],
            pilot_offsets[stratum] + pilot_counts[stratum],
        )
        confirm_interval = (
            confirm_offsets[stratum],
            confirm_offsets[stratum] + confirm_counts[stratum],
        )
        overlap = max(pilot_interval[0], confirm_interval[0]) < min(
            pilot_interval[1], confirm_interval[1]
        )
        if overlap:
            raise ValueError(
                f"datasets.{dataset_key} phase allocation overlaps for {stratum!r}: "
                f"pilot={pilot_interval}, confirmatory={confirm_interval}."
            )


def _phase_allocation_audit(config: Mapping[str, object]) -> dict[str, object]:
    if not _is_v2(config):
        return {
            "passed": False,
            "status": "legacy-uncontrolled",
            "datasets": {},
            "reason": "v1 does not isolate pilot and confirmatory source units",
        }
    results: dict[str, object] = {}
    globally_passed = True
    for dataset_key, dataset in _dataset_configs(config).items():
        reasons: list[str] = []
        try:
            _validate_phase_allocation_shape(dataset_key, dataset)
        except ValueError as exc:
            reasons.append(str(exc))
        allocation = _mapping(
            dataset.get("phase_allocation"),
            f"datasets.{dataset_key}.phase_allocation",
        )
        intervals: dict[str, object] = {}
        expected = _expected_allocation_counts(dataset)
        for phase in ("pilot", "confirmatory"):
            phase_record = _mapping(
                allocation.get(phase),
                f"datasets.{dataset_key}.phase_allocation.{phase}",
            )
            offsets = _mapping(phase_record.get("offsets"), "offsets")
            counts = _mapping(phase_record.get("counts"), "counts")
            intervals[phase] = {
                str(key): [int(offsets[key]), int(offsets[key]) + int(counts[key])]
                for key in offsets
            }
            if expected.get(phase) != {str(key): int(value) for key, value in counts.items()}:
                reasons.append(
                    f"declared {phase} allocation counts do not equal frozen phase caps: "
                    f"declared={dict(counts)}, expected={expected.get(phase)}"
                )
        passed = not reasons
        globally_passed = globally_passed and passed
        results[dataset_key] = {
            "passed": passed,
            "method": allocation.get("method"),
            "intervals": intervals,
            "reasons": reasons,
            "identity": canonical_json_hash(
                {
                    "dataset": dataset_key,
                    "method": allocation.get("method"),
                    "intervals": intervals,
                }
            ),
        }
    return {
        "passed": globally_passed and bool(results),
        "status": "disjoint" if globally_passed and results else "blocked",
        "datasets": results,
        "identity": canonical_json_hash(results),
    }


def _expected_allocation_counts(
    dataset: Mapping[str, object],
) -> dict[str, dict[str, int]]:
    kind = str(dataset.get("kind", ""))
    phase_caps = _mapping(dataset.get("phase_caps"), "phase_caps")
    result: dict[str, dict[str, int]] = {}
    for phase in ("pilot", "confirmatory"):
        caps = _mapping(phase_caps.get(phase), f"phase_caps.{phase}")
        if kind == "adfa-ld":
            result[phase] = {
                "train": int(caps.get("train", 0)),
                "validation": int(caps.get("validation", 0)),
                "test_normal": int(caps.get("test_normal", 0)),
                "attack_per_class": int(caps.get("test_attack_per_class", 0)),
            }
        elif kind == "lid-ds-2021":
            value = int(caps.get("archives_per_scenario_partition", 0))
            result[phase] = {
                name: value
                for name in (
                    "training",
                    "validation",
                    "test-normal",
                    "test-normal-and-attack",
                )
            }
        elif kind == "hai-23.05":
            partition_counts: dict[str, int] = {}
            for partition in ("train", "validation", "test"):
                partition_cap = _mapping(caps.get(partition), f"{phase}.{partition}")
                partition_counts[partition] = int(
                    partition_cap.get(
                        "total",
                        int(partition_cap.get("normal", 0))
                        + int(partition_cap.get("attack", 0)),
                    )
                )
            result[phase] = partition_counts
        else:
            raise ValueError(f"Unsupported v2 dataset kind for phase allocation: {kind!r}.")
    return result


def _numeric_authority_gate(
    config: Mapping[str, object], *, project_root: Path
) -> dict[str, object]:
    """Resolve every numeric leaf through immutable ParameterEvidence.v1 authority."""

    if not _is_v2(config):
        return {
            "accountability_outcome": "legacy-not-evaluated",
            "authorization_effect": "none",
            "limitations": [
                "v1 numeric values are not closed under ParameterEvidence.v1 and cannot support claims"
            ],
        }
    governance = _mapping(config.get("numeric_authority"), "numeric_authority")
    violations: list[dict[str, str]] = []
    try:
        requirements_path = _governance_path(
            project_root, governance.get("requirements_path"), "requirements_path"
        )
        requirements_sha256 = str(governance.get("requirements_sha256", ""))
        requirements_payload = _read_verified_bytes(
            requirements_path,
            requirements_sha256,
            field="requirements_sha256",
        )
        requirements = json.loads(requirements_payload)
        if not isinstance(requirements, dict):
            raise ValueError("academic numeric requirements must be a JSON object")
    except (OSError, ValueError) as exc:
        return {
            "accountability_outcome": "blocked",
            "authorization_effect": "none",
            "gate_result_id": canonical_json_hash({"error": str(exc)}),
            "violations": [
                {
                    "rule_id": "ACADEMIC-PARAMETER-REQUIREMENTS-INVALID",
                    "field_path": "numeric_authority.requirements_path",
                    "explanation": str(exc),
                }
            ],
            "limitations": ["No numeric consumer may execute while authority is unresolved."],
        }
    if requirements.get("schema_version") != NUMERIC_REQUIREMENTS_SCHEMA:
        violations.append(
            {
                "rule_id": "ACADEMIC-PARAMETER-REQUIREMENTS-SCHEMA",
                "field_path": "schema_version",
                "explanation": "unsupported academic numeric-consumer inventory schema",
            }
        )
    if (
        requirements.get("numeric_schema_version") != V2_NUMERIC_SCHEMA_VERSION
        or requirements.get("numeric_schema_identity") != V2_NUMERIC_SCHEMA_IDENTITY
    ):
        violations.append(
            {
                "rule_id": "ACADEMIC-NUMERIC-SCHEMA-MISMATCH",
                "field_path": "numeric_schema_identity",
                "explanation": (
                    "requirements inventory is not bound to the complete "
                    "implementation-owned v2 numeric schema"
                ),
            }
        )
    if requirements.get("experiment_id") != config.get("experiment_id"):
        violations.append(
            {
                "rule_id": "ACADEMIC-PARAMETER-SCOPE-MISMATCH",
                "field_path": "experiment_id",
                "explanation": "requirements inventory is bound to another experiment",
            }
        )
    raw_slots = requirements.get("slots")
    if not isinstance(raw_slots, list):
        raw_slots = []
        violations.append(
            {
                "rule_id": "ACADEMIC-PARAMETER-INVENTORY-MISSING",
                "field_path": "slots",
                "explanation": "numeric consumer slots must be an array",
            }
        )
    declared: dict[str, Mapping[str, object]] = {}
    for index, raw_slot in enumerate(raw_slots):
        if not isinstance(raw_slot, Mapping):
            violations.append(
                {
                    "rule_id": "ACADEMIC-PARAMETER-SLOT-MALFORMED",
                    "field_path": f"slots/{index}",
                    "explanation": "slot must be an object",
                }
            )
            continue
        pointer = raw_slot.get("consumer_locator")
        slot_id = raw_slot.get("slot_id")
        if not isinstance(slot_id, str) or not slot_id.strip():
            violations.append(
                {
                    "rule_id": "ACADEMIC-PARAMETER-SLOT-ID-INVALID",
                    "field_path": f"slots/{index}/slot_id",
                    "explanation": "slot_id must be a non-empty immutable identifier",
                }
            )
        if not isinstance(pointer, str) or not pointer.startswith("/"):
            violations.append(
                {
                    "rule_id": "ACADEMIC-PARAMETER-LOCATOR-INVALID",
                    "field_path": f"slots/{index}/consumer_locator",
                    "explanation": "consumer locator must be an absolute JSON pointer",
                }
            )
            continue
        if pointer in declared:
            violations.append(
                {
                    "rule_id": "ACADEMIC-PARAMETER-LOCATOR-DUPLICATE",
                    "field_path": pointer,
                    "explanation": "numeric consumer is declared more than once",
                }
            )
        declared[pointer] = raw_slot
    actual = {
        pointer: {"value": value, "json_type": json_type}
        for pointer, value, json_type in _numeric_config_leaves(config)
    }
    for pointer in sorted(set(actual) - set(declared)):
        violations.append(
            {
                "rule_id": "ACADEMIC-PARAMETER-CONSUMER-UNDECLARED",
                "field_path": pointer,
                "explanation": "executable numeric value has no inventory slot",
            }
        )
    for pointer in sorted(set(declared) - set(actual)):
        violations.append(
            {
                "rule_id": "ACADEMIC-PARAMETER-CONSUMER-STALE",
                "field_path": pointer,
                "explanation": "inventory slot no longer resolves to an executable numeric value",
            }
        )
    for pointer in sorted(set(actual) & set(declared)):
        slot = declared[pointer]
        observed = actual[pointer]
        if slot.get("value") != observed["value"] or slot.get("json_type") != observed["json_type"]:
            violations.append(
                {
                    "rule_id": "ACADEMIC-PARAMETER-VALUE-MISMATCH",
                    "field_path": pointer,
                    "explanation": (
                        f"inventory value/type {slot.get('value')!r}/{slot.get('json_type')!r} "
                        f"does not match config {observed['value']!r}/{observed['json_type']!r}"
                    ),
                }
            )
        if not isinstance(slot.get("unit"), str) or not str(slot.get("unit")).strip():
            violations.append(
                {
                    "rule_id": "ACADEMIC-PARAMETER-UNIT-MISSING",
                    "field_path": pointer,
                    "explanation": "exact unit is required",
                }
            )
        if not isinstance(slot.get("quantity_kind"), str) or not str(
            slot.get("quantity_kind")
        ).strip():
            violations.append(
                {
                    "rule_id": "ACADEMIC-PARAMETER-QUANTITY-KIND-MISSING",
                    "field_path": pointer,
                    "explanation": "closed quantity kind is required",
                }
            )
        if not isinstance(slot.get("parameter_revision_id"), str) or not isinstance(
            slot.get("parameter_revision_sha256"), str
        ):
            violations.append(
                {
                    "rule_id": "ACADEMIC-PARAMETER-AUTHORITY-UNRESOLVED",
                    "field_path": pointer,
                    "explanation": "immutable ParameterEvidence.v1 revision ID/hash is unresolved",
                }
            )
    bindings = [dict(slot) for _, slot in sorted(declared.items())]
    if violations:
        return {
            "accountability_outcome": "blocked",
            "authorization_effect": "none",
            "requirements_path": str(requirements_path),
            "requirements_sha256": requirements_sha256,
            "numeric_consumer_count": len(actual),
            "resolved_consumer_count": sum(
                isinstance(slot.get("parameter_revision_id"), str)
                and isinstance(slot.get("parameter_revision_sha256"), str)
                for slot in declared.values()
            ),
            "bindings": bindings,
            "violations": violations,
            "gate_result_id": canonical_json_hash(
                {"requirements_sha256": requirements_sha256, "violations": violations}
            ),
            "limitations": ["No numeric consumer may execute while authority is unresolved."],
        }
    temporal_context: TemporalGateContext | None = None
    temporal_context_path: Path | None = None
    temporal_context_sha256 = str(
        governance.get("temporal_context_sha256", "")
    )
    try:
        temporal_context_path = _governance_path(
            project_root,
            governance.get("temporal_context_path"),
            "temporal_context_path",
        )
        temporal_payload = _read_verified_bytes(
            temporal_context_path,
            temporal_context_sha256,
            field="temporal_context_sha256",
        )
        temporal_context = _parse_temporal_gate_context(temporal_payload)
    except (OSError, TypeError, ValueError) as exc:
        violations.append(
            {
                "rule_id": "ACADEMIC-TEMPORAL-CONTEXT-INVALID",
                "field_path": "numeric_authority.temporal_context_path",
                "explanation": str(exc),
            }
        )
    try:
        catalog_path = _governance_path(
            project_root, governance.get("catalog_path"), "catalog_path"
        )
        source_path = _governance_path(
            project_root, governance.get("source_catalog_path"), "source_catalog_path"
        )
        catalog_sha256 = str(governance.get("catalog_sha256", ""))
        source_catalog_sha256 = str(
            governance.get("source_catalog_sha256", "")
        )
        catalog_payload = _read_verified_bytes(
            catalog_path, catalog_sha256, field="catalog_sha256"
        )
        source_payload = _read_verified_bytes(
            source_path,
            source_catalog_sha256,
            field="source_catalog_sha256",
        )
        catalog = load_parameter_catalog(catalog_payload)
        source_catalog = load_source_catalog(source_payload)
        inventory_id = str(governance.get("inventory_id", ""))
        required_set_id = str(governance.get("required_set_id", ""))
        inventory = next(
            item for item in catalog.inventories if item.inventory_id == inventory_id
        )
        required_set = next(
            item for item in catalog.required_sets if item.required_set_id == required_set_id
        )
        result = validate_parameter_gate(
            catalog,
            source_catalog,
            inventory,
            required_set,
            evidence_root=project_root,
            temporal_context=temporal_context,
        )
        if result.accountability_outcome != AccountabilityOutcome.ACCOUNTABLE:
            violations.extend(
                {
                    "rule_id": item.rule_id,
                    "field_path": item.field_path,
                    "explanation": item.explanation,
                }
                for item in result.violations
            )
        revisions = {
            item.parameter_revision_id: item for item in catalog.parameter_revisions
        }
        required_bindings = {
            item.slot_id: item for item in required_set.bindings
        }
        inventory_slots = {item.consumer_locator: item for item in inventory.requirements}
        for pointer, slot in declared.items():
            revision_id = str(slot["parameter_revision_id"])
            revision = revisions.get(revision_id)
            requirement = inventory_slots.get(pointer)
            binding = required_bindings.get(str(slot.get("slot_id", "")))
            if revision is None or requirement is None or binding is None:
                violations.append(
                    {
                        "rule_id": "ACADEMIC-PARAMETER-BINDING-UNRESOLVED",
                        "field_path": pointer,
                        "explanation": "catalog inventory/required-set/revision binding is incomplete",
                    }
                )
                continue
            if (
                requirement.slot_id != slot.get("slot_id")
                or str(requirement.unit) != str(slot.get("unit"))
                or str(requirement.quantity_kind)
                != str(slot.get("quantity_kind"))
            ):
                violations.append(
                    {
                        "rule_id": "ACADEMIC-PARAMETER-INVENTORY-MISMATCH",
                        "field_path": pointer,
                        "explanation": (
                            "requirements file slot ID/unit/quantity kind does not exactly "
                            "match the authenticated ParameterEvidence inventory"
                        ),
                    }
                )
            if (
                revision.revision_sha256 != slot.get("parameter_revision_sha256")
                or not _same_finite_decimal(revision.value.scalar, slot.get("value"))
                or str(revision.unit) != str(slot.get("unit"))
                or binding.parameter_revision_id != revision_id
                or binding.parameter_revision_sha256 != revision.revision_sha256
            ):
                violations.append(
                    {
                        "rule_id": "ACADEMIC-PARAMETER-BINDING-MISMATCH",
                        "field_path": pointer,
                        "explanation": "config value/unit/revision does not exactly match ParameterEvidence.v1",
                    }
                )
    except (OSError, StopIteration, TypeError, ValueError) as exc:
        violations.append(
            {
                "rule_id": "ACADEMIC-PARAMETER-CATALOG-INVALID",
                "field_path": "numeric_authority",
                "explanation": str(exc),
            }
        )
        result = None
    outcome = "accountable" if not violations else "blocked"
    return {
        "accountability_outcome": outcome,
        "authorization_effect": "none",
        "requirements_path": str(requirements_path),
        "requirements_sha256": requirements_sha256,
        "catalog_path": str(catalog_path) if "catalog_path" in locals() else None,
        "catalog_sha256": catalog_sha256 if "catalog_sha256" in locals() else None,
        "source_catalog_path": str(source_path) if "source_path" in locals() else None,
        "source_catalog_sha256": (
            source_catalog_sha256 if "source_catalog_sha256" in locals() else None
        ),
        "temporal_context_path": (
            str(temporal_context_path) if temporal_context_path is not None else None
        ),
        "temporal_context_sha256": temporal_context_sha256,
        "temporal_context_id": (
            temporal_context.context_id if temporal_context is not None else None
        ),
        "numeric_consumer_count": len(actual),
        "resolved_consumer_count": len(actual) if outcome == "accountable" else 0,
        "bindings": bindings,
        "parameter_gate": result.to_dict() if result is not None else None,
        "violations": violations,
        "gate_result_id": canonical_json_hash(
            {
                "requirements_sha256": requirements_sha256,
                "parameter_gate_id": result.gate_result_id if result is not None else None,
                "violations": violations,
            }
        ),
        "limitations": [
            "Numerical accountability only; this gate grants no scientific authorization."
        ],
    }


def _governance_path(project_root: Path, raw: object, field: str) -> Path:
    if not isinstance(raw, str) or not raw.strip():
        raise ValueError(f"numeric_authority.{field} is required")
    root = Path(project_root).resolve()
    path = Path(raw)
    if ".." in path.parts:
        raise ValueError(f"numeric_authority.{field} must not traverse '..'")
    candidate = root / path if not path.is_absolute() else path
    try:
        lexical_relative = candidate.absolute().relative_to(root)
    except ValueError as exc:
        raise ValueError(
            f"numeric_authority.{field} must stay inside the project root"
        ) from exc
    cursor = root
    for part in lexical_relative.parts:
        cursor = cursor / part
        if cursor.is_symlink():
            raise ValueError(
                f"numeric_authority.{field} must not traverse a symlink"
            )
    resolved = candidate.resolve()
    try:
        resolved.relative_to(root)
    except ValueError as exc:
        raise ValueError(f"numeric_authority.{field} must stay inside the project root") from exc
    if not resolved.is_file():
        raise ValueError(f"numeric_authority.{field} does not exist: {resolved}")
    return resolved


def _same_finite_decimal(left: object, right: object) -> bool:
    """Compare numeric authority values without mistaking spelling for value.

    The configuration inventory preserves JSON literals (for example ``12.0``),
    while ParameterEvidence.v1 intentionally requires canonical decimal strings
    (``12``).  Both must represent the same finite mathematical value; a binary
    float conversion would make large integers and exact protocol decimals unsafe.
    """

    try:
        first = Decimal(str(left))
        second = Decimal(str(right))
    except (InvalidOperation, ValueError):
        return False
    return first.is_finite() and second.is_finite() and first == second


def _read_verified_bytes(path: Path, expected_sha256: str, *, field: str) -> bytes:
    """Read once and authenticate the exact bytes subsequently parsed.

    Stat snapshots prevent a path replacement from making the hash check and
    parser observe different files. The digest is calculated from the in-memory
    payload, never by reopening the path.
    """

    if not isinstance(expected_sha256, str) or not expected_sha256.startswith(
        "sha256:"
    ):
        raise ValueError(f"{field} must be a sha256-prefixed digest")
    if path.is_symlink():
        raise ValueError(f"{field} target must not be a symlink: {path}")
    try:
        before = path.stat(follow_symlinks=False)
        with path.open("rb") as handle:
            opened = os.fstat(handle.fileno())
            payload = handle.read()
        after = path.stat(follow_symlinks=False)
    except OSError as exc:
        raise ValueError(f"cannot read immutable {field} target {path}: {exc}") from exc
    snapshot = lambda value: (
        value.st_dev,
        value.st_ino,
        value.st_size,
        value.st_mtime_ns,
    )
    if path.is_symlink() or not (
        snapshot(before) == snapshot(opened) == snapshot(after)
    ):
        raise ValueError(f"{field} target changed while it was being authenticated")
    observed = f"sha256:{sha256(payload).hexdigest()}"
    if observed != expected_sha256:
        raise ValueError(
            f"{field} does not match the immutable file: expected "
            f"{expected_sha256}, observed {observed}"
        )
    return payload


def _parse_temporal_gate_context(payload: bytes) -> TemporalGateContext:
    try:
        raw = json.loads(payload)
    except (UnicodeError, json.JSONDecodeError) as exc:
        raise ValueError(f"temporal gate context is not valid UTF-8 JSON: {exc}") from exc
    expected = {
        "context_id",
        "freeze_identity",
        "freeze_time",
        "test_identity",
        "test_time",
        "truth_identity",
        "truth_time",
    }
    if not isinstance(raw, dict) or set(raw) != expected:
        raise ValueError(
            "temporal gate context must contain exactly the TemporalGateContext fields"
        )
    if any(not isinstance(raw[field], str) or not raw[field].strip() for field in expected):
        raise ValueError("temporal gate context fields must be non-empty strings")
    return TemporalGateContext(**raw)


def _numeric_config_leaves(
    config: Mapping[str, object],
) -> list[tuple[str, str, str]]:
    if _is_v2(config):
        return v2_numeric_consumers(config)
    leaves: list[tuple[str, str, str]] = []

    def visit(value: object, pointer: str) -> None:
        if isinstance(value, bool) or value is None:
            return
        if isinstance(value, int):
            leaves.append((pointer, str(value), "integer"))
            return
        if isinstance(value, float):
            if not math.isfinite(value):
                raise ValueError(f"Non-finite numeric config value at {pointer}.")
            try:
                rendered = format(Decimal(str(value)), "f")
            except InvalidOperation as exc:
                raise ValueError(f"Invalid numeric config value at {pointer}.") from exc
            leaves.append((pointer, rendered, "number"))
            return
        if isinstance(value, Mapping):
            for key, item in sorted(value.items(), key=lambda pair: str(pair[0])):
                escaped = str(key).replace("~", "~0").replace("/", "~1")
                visit(item, f"{pointer}/{escaped}")
            return
        if isinstance(value, (list, tuple)):
            for index, item in enumerate(value):
                visit(item, f"{pointer}/{index}")

    visit(config, "")
    return leaves


def _repetition_planning_gate(
    config: Mapping[str, object], *, project_root: Path, phase: str
) -> dict[str, object]:
    if phase == "pilot" or not _is_v2(config):
        return {"passed": True, "status": "not-required-for-pilot"}
    rows = _logical_plan(config, phase, project_root=project_root)
    pilot_paths = academic_paths(config, project_root=project_root, phase="pilot")
    issues: list[str] = []
    try:
        if pilot_paths.transactions.is_dir():
            _recover_cell_transactions(pilot_paths)
        expected_pilot = _expected_descriptors(
            config, project_root=project_root, phase="pilot"
        )
        available_pilot = load_completed_cells(pilot_paths.phase)
    except Exception as exc:
        return {
            "passed": False,
            "status": "blocked",
            "reason": f"Cannot reconstruct authenticated pilot artifacts: {exc}",
            "issues": [str(exc)],
        }
    expected_by_id = {
        str(descriptor["cell_id"]): descriptor for descriptor in expected_pilot
    }
    available_by_id = {
        str(cell.get("cell_id")): cell for cell in available_pilot
    }
    if len(expected_by_id) != len(expected_pilot):
        issues.append("pilot plan contains duplicate cell identities")
    if len(available_by_id) != len(available_pilot):
        issues.append("pilot artifacts contain duplicate cell identities")
    missing_ids = sorted(set(expected_by_id) - set(available_by_id))
    extra_ids = sorted(set(available_by_id) - set(expected_by_id))
    if missing_ids:
        issues.append(f"pilot is missing {len(missing_ids)} planned cell artifacts")
    if extra_ids:
        issues.append(f"pilot contains {len(extra_ids)} unplanned cell artifacts")
    authenticated_cells: list[Mapping[str, object]] = []
    source_rows: list[dict[str, object]] = []
    for cell_id, descriptor in expected_by_id.items():
        cell = available_by_id.get(cell_id)
        if cell is None:
            continue
        try:
            cell_path = Path(str(cell.get("artifact_path", "")))
            _validate_resume_artifact(
                cell,
                descriptor=descriptor,
                cell_path=cell_path,
                predictions_dir=pilot_paths.predictions,
                config=config,
                project_root=project_root,
            )
            reconstruction = validate_cell_raw_reconstruction(cell, config=config)
        except Exception as exc:
            issues.append(f"pilot cell {cell_id} failed authentication: {exc}")
            continue
        authenticated_cells.append(cell)
        artifact = _mapping(cell.get("predictions_artifact"), "predictions_artifact")
        source_rows.append(
            {
                "cell_id": cell_id,
                "cell_sha256": file_sha256(cell_path),
                "prediction_sha256": artifact.get("sha256"),
                "raw_reconstruction_identity": reconstruction.get("identity"),
            }
        )

    statistics = _mapping(config.get("statistical_protocol"), "statistical_protocol")
    primary_metric = str(statistics.get("primary_metric", ""))
    stochastic_counts: dict[str, int] = {}
    planning: dict[str, object] = {}
    for row in rows:
        if not bool(row.get("deterministic", False)):
            key = f"{row['dataset']}/{row['model']}"
            stochastic_counts[key] = stochastic_counts.get(key, 0) + 1
    pilot_values: dict[str, dict[int, float | None]] = {}
    for cell in authenticated_cells:
        if bool(cell.get("deterministic", False)):
            continue
        key = f"{cell.get('dataset')}/{cell.get('model')}"
        seed = cell.get("seed")
        if type(seed) is not int:
            issues.append(f"{key}: pilot cell has an invalid seed")
            continue
        value = _cell_metric(cell, primary_metric)
        if seed in pilot_values.setdefault(key, {}):
            issues.append(f"{key}: duplicate authenticated pilot seed {seed}")
        pilot_values[key][seed] = value
    configured_pilot_seeds = tuple(int(seed) for seed in config["pilot_seeds"])  # type: ignore[index]
    for key, count in sorted(stochastic_counts.items()):
        values_by_seed = pilot_values.get(key, {})
        values = [values_by_seed.get(seed) for seed in configured_pilot_seeds]
        plan = derive_repetition_count(
            values,
            target_half_width=float(statistics["target_ci_half_width"]),
            confidence_level=float(statistics["confidence_level"]),
            minimum=int(statistics["minimum_stochastic_trials"]),
            maximum=int(statistics["maximum_stochastic_trials"]),
            required_pilot_trials=V2_PILOT_TRIALS,
            fixed_execution_trials=V2_CONFIRMATORY_TRIALS,
        )
        planning[key] = {
            **plan,
            "source": "authenticated-pilot-cell-primary-outcomes",
            "primary_metric": primary_metric,
            "pilot_seed_order": list(configured_pilot_seeds),
            "primary_outcomes": values,
        }
        if plan.get("pilot_trials_expected") != V2_PILOT_TRIALS:
            issues.append(f"{key}: expected pilot trial count is not {V2_PILOT_TRIALS}")
        if plan.get("finite_pilot_trials") != V2_PILOT_TRIALS:
            issues.append(f"{key}: fewer than all five pilot primary outcomes are finite")
        if plan.get("all_required_pilot_outcomes_finite") is not True:
            issues.append(f"{key}: pilot dispersion sufficiency is indeterminate")
        if plan.get("planning_determinate") is not True:
            issues.append(f"{key}: prospective precision planning is indeterminate")
        if plan.get("configured_trial_cap") != V2_CONFIRMATORY_TRIALS:
            issues.append(f"{key}: configured trial cap is not {V2_CONFIRMATORY_TRIALS}")
        if plan.get("fixed_execution_trials") != V2_CONFIRMATORY_TRIALS:
            issues.append(f"{key}: pilot plan does not authenticate the fixed 50-trial schedule")
        if count != V2_CONFIRMATORY_TRIALS:
            issues.append(f"{key}: frozen confirmatory ledger contains {count} trials, not 50")
    exact_pilot = (
        bool(expected_by_id)
        and len(authenticated_cells) == len(expected_by_id)
        and not missing_ids
        and not extra_ids
    )
    if not exact_pilot:
        issues.append("pilot artifact set is not an exact authenticated matrix")
    source_identity = canonical_json_hash(sorted(source_rows, key=lambda row: str(row["cell_id"])))
    return {
        "passed": bool(rows) and exact_pilot and not issues,
        "status": (
            "fixed-nonadaptive-50-after-complete-five-trial-pilot"
            if bool(rows) and not issues
            else "blocked"
        ),
        "planned_logical_cells": len(rows),
        "stochastic_trial_counts": stochastic_counts,
        "deterministic_trial_counts": {
            f"{row['dataset']}/{row['model']}": 1
            for row in rows
            if bool(row.get("deterministic", False))
        },
        "pilot_planning": planning,
        "pilot_source_cell_count": len(authenticated_cells),
        "pilot_source_authentication_identity": source_identity,
        "pilot_source_cells": sorted(source_rows, key=lambda row: str(row["cell_id"])),
        "issues": issues,
        "reason": "; ".join(issues) if issues else None,
        "schedule_identity": _phase_schedule_identity(config, phase),
        "identity": canonical_json_hash(
            {
                "rows": rows,
                "pilot_planning": planning,
                "pilot_source_authentication_identity": source_identity,
                "issues": issues,
            }
        ),
    }


def academic_paths(
    config: Mapping[str, object], *, project_root: Path, phase: str
) -> AcademicPaths:
    if phase not in {"pilot", "confirmatory"}:
        raise ValueError("phase must be 'pilot' or 'confirmatory'.")
    configured_root = Path(str(config.get("output_root", "evidence/academic")))
    if not configured_root.is_absolute():
        configured_root = Path(project_root) / configured_root
    digest = config_identity(config).split(":", 1)[1][:16]
    root = configured_root.resolve() / str(config["experiment_id"]) / digest
    return AcademicPaths(
        root=root,
        phase=root / phase,
        cells=root / phase / "cells",
        predictions=root / phase / "predictions",
        transactions=root / phase / "transactions",
        reports=root / "reports",
    )


def _requested_batch_id(
    config: Mapping[str, object], *, phase: str, confirmatory_batch: int | None
) -> str | None:
    if not (_is_v2(config) and phase == "confirmatory"):
        if confirmatory_batch is not None:
            raise ValueError(
                "confirmatory_batch is valid only for a v2 confirmatory execution."
            )
        return None
    if (
        not isinstance(confirmatory_batch, int)
        or isinstance(confirmatory_batch, bool)
        or not 1 <= confirmatory_batch <= V2_CONFIRMATORY_BATCH_COUNT
    ):
        raise ValueError(
            "v2 confirmatory execution requires confirmatory_batch in the range 1..5."
        )
    return f"batch-{confirmatory_batch:02d}"


def run_preflight(
    config: Mapping[str, object], *, project_root: Path, phase: str
) -> dict[str, object]:
    """Materialize protocol metadata and fail-closed leakage/support checks."""

    started = time.perf_counter()
    cpu_started = time.process_time()
    paths = _initialize_evidence(config, project_root=project_root, phase=phase)
    previous_preflight_path = paths.phase / "preflight.json"
    previous_preflight = (
        _read_json(previous_preflight_path)
        if previous_preflight_path.is_file()
        else {}
    )
    numeric_authority = _numeric_authority_gate(config, project_root=project_root)
    allocation_audit = _phase_allocation_audit(config)
    if (
        _is_v2(config)
        and numeric_authority.get("accountability_outcome") != "accountable"
    ):
        # Do not load or transform benchmark data to reconstruct confirmatory
        # planning while the authority gate already forbids numeric consumers.
        repetition_planning = {
            "passed": False,
            "status": "blocked",
            "reason": "Numeric authority must close before pilot evidence can be inspected.",
            "issues": ["numeric authority is unresolved"],
        }
    else:
        repetition_planning = _repetition_planning_gate(
            config, project_root=project_root, phase=phase
        )
    dataset_results: dict[str, object] = {}
    for dataset_key, raw_config in _dataset_configs(config).items():
        if _is_v2(config) and numeric_authority.get("accountability_outcome") != "accountable":
            dataset_results[dataset_key] = {
                "status": "blocked",
                "evidence_origin": raw_config.get("evidence_origin"),
                "error_type": "NumericAuthorityBlocked",
                "error": "No domain data were loaded because executable numeric authority is unresolved.",
            }
            continue
        if _is_v2(config) and repetition_planning.get("passed") is not True:
            dataset_results[dataset_key] = {
                "status": "blocked",
                "evidence_origin": raw_config.get("evidence_origin"),
                "error_type": "RepetitionPlanningBlocked",
                "error": str(repetition_planning.get("reason")),
            }
            continue
        dataset_allocation = allocation_audit.get("datasets", {}).get(dataset_key, {})  # type: ignore[union-attr]
        if _is_v2(config) and not (
            isinstance(dataset_allocation, Mapping) and dataset_allocation.get("passed") is True
        ):
            dataset_results[dataset_key] = {
                "status": "blocked",
                "evidence_origin": raw_config.get("evidence_origin"),
                "error_type": "PhaseAllocationBlocked",
                "error": "Pilot/confirmatory allocation is not explicitly disjoint.",
            }
            continue
        try:
            prepared = _prepare_one_dataset(
                dataset_key, raw_config, project_root=project_root, phase=phase
            )
            support_check = _support_check(prepared.dataset, raw_config, phase)
            result = _dataset_preflight_record(prepared, support_check=support_check)
            _, _, validation_role_split = _validation_role_partitions(
                prepared.partitions["validation"], config
            )
            result["validation_role_split"] = validation_role_split
            origin_check = _evidence_origin_check(prepared, raw_config, dataset_key)
            result["evidence_origin_gate"] = origin_check
            result["phase_disjointness"] = _observed_phase_disjointness(
                config,
                project_root=project_root,
                phase=phase,
                dataset_key=dataset_key,
                current_record=result,
            )
            result["status"] = (
                "ready"
                if support_check["passed"]
                and validation_role_split["passed"]
                and origin_check["passed"]
                and result["phase_disjointness"]["passed"]  # type: ignore[index]
                else "blocked"
            )
        except Exception as exc:  # preflight records every planned cell boundary
            result = {
                "status": "blocked",
                "evidence_origin": raw_config.get("evidence_origin"),
                "error_type": type(exc).__name__,
                "error": str(exc),
            }
        dataset_results[dataset_key] = result

    elapsed_seconds = time.perf_counter() - started
    elapsed_cpu_seconds = time.process_time() - cpu_started
    previous_representative_cpu = previous_preflight.get(
        "representative_elapsed_cpu_seconds",
        previous_preflight.get("elapsed_cpu_seconds"),
    )
    representative_elapsed_cpu_seconds = max(
        elapsed_cpu_seconds,
        float(previous_representative_cpu)
        if (
            previous_preflight.get("config_identity") == config_identity(config)
            and previous_preflight.get("phase") == phase
            and isinstance(previous_representative_cpu, (int, float))
        )
        else 0.0,
    )
    computational_load = _computational_load(
        config,
        dataset_results=dataset_results,
        paths=paths,
        phase=phase,
        project_root=project_root,
        current_preflight_cpu_seconds=representative_elapsed_cpu_seconds,
    )
    record: dict[str, object] = {
        "schema_version": "academic-preflight-v2" if _is_v2(config) else "academic-preflight-v1",
        "runner_protocol": _runner_protocol(config),
        "experiment_id": config["experiment_id"],
        "phase": phase,
        "config_identity": config_identity(config),
        "generated_at_utc": _utc_now(),
        "elapsed_seconds": elapsed_seconds,
        "elapsed_cpu_seconds": elapsed_cpu_seconds,
        "representative_elapsed_cpu_seconds": representative_elapsed_cpu_seconds,
        "environment": environment_manifest(),
        "numeric_authority": numeric_authority,
        "phase_allocation_audit": allocation_audit,
        "repetition_planning_gate": repetition_planning,
        "historical_admissibility": _legacy_admissibility(config, project_root),
        "datasets": dataset_results,
        "computational_load": computational_load,
        "ready": (
            bool(dataset_results)
            and (not _is_v2(config) or numeric_authority.get("accountability_outcome") == "accountable")
            and (not _is_v2(config) or allocation_audit.get("passed") is True)
            and (not _is_v2(config) or repetition_planning.get("passed") is True)
            and (
                not (_is_v2(config) and phase == "confirmatory")
                or computational_load.get("projection_complete") is True
            )
            and all(
                isinstance(item, dict) and item.get("status") == "ready"
                for item in dataset_results.values()
            )
        ),
    }
    _write_json(paths.phase / "preflight.json", record, immutable=False)
    return record


def confirmatory_budget_issue(
    preflight: Mapping[str, object] | None,
    *,
    allow_over_budget: bool,
    require_confirmatory: bool = True,
) -> str | None:
    """Return a launch-blocking cost issue; unknown cost is never waivable."""

    if not require_confirmatory:
        return None
    if preflight is None:
        return "Confirmatory budget is unknown; a complete confirmatory preflight is required."
    load = preflight.get("computational_load")
    if not isinstance(load, Mapping) or load.get("projection_complete") is not True:
        return (
            "Confirmatory budget projection is incomplete or unknown. Complete the five-trial "
            "pilot and full-matrix confirmatory preflight; over-budget authorization cannot "
            "waive missing cost evidence."
        )
    if (
        load.get("projected_preflight_invocations")
        != V2_CONFIRMATORY_PREFLIGHT_INVOCATIONS
        or load.get("confirmatory_preflight_invocations")
        != V2_CONFIRMATORY_PREFLIGHT_INVOCATIONS
        or load.get("confirmatory_standalone_preflight_invocations")
        != V2_CONFIRMATORY_STANDALONE_PREFLIGHT_INVOCATIONS
        or load.get("confirmatory_batch_preflight_invocations")
        != V2_CONFIRMATORY_BATCH_COUNT
    ):
        return (
            "Confirmatory cost projection does not cover the mandatory standalone preflight "
            "and all five batch-local preflight invocations."
        )
    estimate = load.get("projected_total_cpu_hours_conservative")
    threshold = load.get("ask_first_cpu_hours")
    if (
        not isinstance(estimate, (int, float))
        or isinstance(estimate, bool)
        or not math.isfinite(float(estimate))
        or float(estimate) < 0.0
    ):
        return "Conservative total confirmatory CPU-hour projection is unavailable."
    if (
        not isinstance(threshold, (int, float))
        or isinstance(threshold, bool)
        or not math.isfinite(float(threshold))
        or float(threshold) <= 0.0
    ):
        return "Frozen CPU-hour review threshold is unavailable."
    if float(estimate) > float(threshold) and not allow_over_budget:
        return (
            f"Confirmatory run blocked: conservative full-protocol projection "
            f"{float(estimate):.2f} CPU-h exceeds {float(threshold):.2f}. Obtain explicit "
            "authorization and set allow_over_budget=True."
        )
    return None


def _logical_schedule_key(value: Mapping[str, object]) -> tuple[object, ...]:
    dataset = value.get("dataset_key", value.get("dataset"))
    return (
        str(dataset),
        str(value.get("model")),
        value.get("seed"),
        value.get("batch_id"),
        value.get("schedule_identity"),
    )


def confirmatory_batch_ledger(
    config: Mapping[str, object],
) -> dict[str, object]:
    """Return the sole config-derived v2 confirmatory batch ledger."""

    if not _is_v2(config):
        raise ValueError("A confirmatory batch ledger is defined only for v2 configs.")
    batches = _confirmatory_seed_batches(config)
    flattened_seeds = [seed for batch in batches for seed in batch]
    if (
        len(batches) != V2_CONFIRMATORY_BATCH_COUNT
        or any(len(batch) != V2_CONFIRMATORY_BATCH_SIZE for batch in batches)
        or len(flattened_seeds) != V2_CONFIRMATORY_TRIALS
        or len(flattened_seeds) != len(set(flattened_seeds))
    ):
        raise ValueError(
            "The v2 confirmatory ledger requires five non-overlapping batches of ten seeds."
        )
    for index, seed in enumerate(flattened_seeds):
        _validate_uint32_seed(seed, f"confirmatory ledger seed[{index}]")
    ledger_batches: list[dict[str, object]] = []
    position = 0
    for batch_number, seeds in enumerate(batches, start=1):
        start = position + 1
        position += len(seeds)
        ledger_batches.append(
            {
                "batch_id": f"batch-{batch_number:02d}",
                "seed_position_start": start,
                "seed_position_end": position,
                "seeds": list(seeds),
            }
        )
    return {
        "schema_version": "academic-confirmatory-batch-ledger-v1",
        "config_identity": config_identity(config),
        "schedule_identity": _phase_schedule_identity(config, "confirmatory"),
        "trial_count": V2_CONFIRMATORY_TRIALS,
        "batch_count": V2_CONFIRMATORY_BATCH_COUNT,
        "batch_size": V2_CONFIRMATORY_BATCH_SIZE,
        "execution_schedule_adaptive": False,
        "batches": ledger_batches,
    }


def _confirmatory_batch_ledger_issue(
    config: Mapping[str, object], phase_path: Path
) -> str | None:
    """Authenticate the persisted ledger against the frozen config."""

    if not _is_v2(config):
        return None
    phase_directory = Path(phase_path)
    ledger_path = phase_directory / "confirmatory-batch-ledger.json"
    if phase_directory.is_symlink():
        return "confirmatory phase directory is a symlink"
    if ledger_path.is_symlink():
        return "confirmatory batch ledger is a symlink"
    if ledger_path.resolve().parent != phase_directory.resolve():
        return "confirmatory batch ledger escapes the phase directory"
    if not ledger_path.is_file():
        return "confirmatory batch ledger is missing"
    try:
        observed = _read_json(ledger_path)
        expected = confirmatory_batch_ledger(config)
    except Exception as exc:
        return f"confirmatory batch ledger cannot be authenticated: {exc}"
    if observed != expected:
        return "confirmatory batch ledger disagrees with the frozen configuration"
    return None


def _confirmatory_batch_order_issue(
    config: Mapping[str, object],
    *,
    phase: str,
    batch_id: str | None,
    logical_rows: Sequence[Mapping[str, object]],
    phase_path: Path,
    project_root: Path | None = None,
) -> str | None:
    """Require every earlier positional batch before launching or retrying one batch."""

    if not (_is_v2(config) and phase == "confirmatory"):
        return None
    if batch_id is None or not batch_id.startswith("batch-"):
        return "A valid positional confirmatory batch is required."
    try:
        batch_number = int(batch_id.removeprefix("batch-"))
    except ValueError:
        return f"Invalid confirmatory batch identifier: {batch_id!r}."
    ledger_issue = _confirmatory_batch_ledger_issue(config, phase_path)
    if ledger_issue is not None:
        return f"Confirmatory {batch_id} is blocked because {ledger_issue}."
    prior_batch_ids = {
        f"batch-{index:02d}" for index in range(1, batch_number)
    }
    expected_prior = {
        _logical_schedule_key(row)
        for row in logical_rows
        if row.get("batch_id") in prior_batch_ids
    }
    if batch_number > 1 and not expected_prior:
        return (
            f"Confirmatory {batch_id} is blocked because the frozen logical plan "
            "contains no earlier-batch cells to authenticate."
        )
    try:
        completed_cells = load_completed_cells(phase_path)
    except Exception as exc:
        return (
            f"Confirmatory {batch_id} is blocked because complete artifacts cannot be "
            f"loaded safely: {exc}"
        )
    completed_ids = [str(cell.get("cell_id")) for cell in completed_cells]
    if len(completed_ids) != len(set(completed_ids)):
        return (
            f"Confirmatory {batch_id} is blocked because complete artifacts contain "
            "duplicate cell_id values."
        )
    incompatible_cells = [
        cell
        for cell in completed_cells
        if cell.get("config_identity") != config_identity(config)
        or cell.get("phase") != phase
    ]
    if incompatible_cells:
        return (
            f"Confirmatory {batch_id} is blocked because complete artifacts have an "
            "incompatible phase or configuration identity."
        )
    expected_all = {_logical_schedule_key(row) for row in logical_rows}
    completed_all_keys = [_logical_schedule_key(cell) for cell in completed_cells]
    if len(completed_all_keys) != len(set(completed_all_keys)):
        return (
            f"Confirmatory {batch_id} is blocked because complete artifacts contain "
            "duplicate logical schedule artifacts."
        )
    unplanned_all = set(completed_all_keys) - expected_all
    if unplanned_all:
        return (
            f"Confirmatory {batch_id} is blocked because complete artifacts contain "
            f"{len(unplanned_all)} unplanned logical artifact(s)."
        )
    if batch_number <= 1:
        return None
    prior_cells = [
        cell
        for cell in completed_cells
        if cell.get("config_identity") == config_identity(config)
        and cell.get("phase") == phase
        and cell.get("batch_id") in prior_batch_ids
    ]
    completed_prior_keys = [_logical_schedule_key(cell) for cell in prior_cells]
    completed_prior = set(completed_prior_keys)
    missing = expected_prior - completed_prior
    if missing:
        missing_by_batch = {
            str(key[3]): sum(1 for item in missing if item[3] == key[3])
            for key in missing
        }
        details = ", ".join(
            f"{prior}: {count} missing"
            for prior, count in sorted(missing_by_batch.items())
        )
        return (
            f"Confirmatory {batch_id} is blocked until every logical cell in all "
            f"earlier batches is complete ({details}). Retrying {batch_id} is allowed "
            "after prior batches are complete; later batches cannot bypass the ledger."
        )
    if project_root is not None:
        try:
            descriptors = {
                _logical_schedule_key(descriptor): descriptor
                for descriptor in _expected_descriptors(
                    config, project_root=project_root, phase=phase
                )
                if descriptor.get("batch_id") in prior_batch_ids
            }
            cells_by_key = {
                _logical_schedule_key(cell): cell for cell in prior_cells
            }
            for logical_key in sorted(expected_prior, key=repr):
                descriptor = descriptors.get(logical_key)
                cell = cells_by_key.get(logical_key)
                if descriptor is None or cell is None:
                    raise ValueError(f"missing descriptor/artifact for {logical_key!r}")
                _validate_resume_artifact(
                    cell,
                    descriptor=descriptor,
                    cell_path=Path(str(cell.get("artifact_path"))),
                    predictions_dir=Path(phase_path) / "predictions",
                    config=config,
                    project_root=project_root,
                )
        except Exception as exc:
            return (
                f"Confirmatory {batch_id} is blocked because an earlier-batch "
                f"artifact failed authentication: {exc}"
            )
    return None


def run_academic_phase(
    config: Mapping[str, object],
    *,
    project_root: Path,
    phase: str,
    dataset_filter: Sequence[str] = (),
    model_filter: Sequence[str] = (),
    confirmatory_batch: int | None = None,
    allow_over_budget: bool = False,
) -> dict[str, object]:
    """Run every requested dataset/model/seed cell and retain all outcomes."""

    batch_id = _requested_batch_id(
        config, phase=phase, confirmatory_batch=confirmatory_batch
    )
    if allow_over_budget and not (_is_v2(config) and phase == "confirmatory"):
        raise ValueError(
            "allow_over_budget is valid only for a v2 confirmatory execution."
        )
    if _is_v2(config) and phase == "confirmatory" and (
        dataset_filter or model_filter
    ):
        raise ValueError(
            "v2 confirmatory batches must run the complete dataset/model matrix; "
            "--dataset and --model filters are forbidden."
        )
    paths = _initialize_evidence(config, project_root=project_root, phase=phase)
    selected_datasets = set(dataset_filter)
    selected_models = set(model_filter)
    known_datasets = set(_dataset_configs(config))
    known_models = {
        name
        for dataset_config in _dataset_configs(config).values()
        for name in _model_configs(dataset_config)
    }
    unknown_datasets = selected_datasets - known_datasets
    unknown_models = selected_models - known_models
    if unknown_datasets or unknown_models:
        raise ValueError(
            "Unknown academic filters: "
            f"datasets={sorted(unknown_datasets)}, models={sorted(unknown_models)}"
        )
    planned: list[dict[str, object]] = []
    completed: list[str] = []
    resumed: list[str] = []
    failed: list[dict[str, str]] = []
    started = time.perf_counter()
    cpu_started = time.process_time()
    preflight = run_preflight(config, project_root=project_root, phase=phase)
    try:
        all_logical_rows = _filtered_logical_plan(
            config,
            phase,
            project_root=project_root,
            dataset_filter=selected_datasets,
            model_filter=selected_models,
        )
    except ValueError:
        all_logical_rows = _provisional_filtered_logical_plan(
            config,
            phase,
            dataset_filter=selected_datasets,
            model_filter=selected_models,
        )
    invocation_rows = [
        row
        for row in all_logical_rows
        if batch_id is None or row.get("batch_id") == batch_id
    ]
    if not preflight.get("ready"):
        reason = "Academic preflight is blocked; no model fit or test scoring was attempted."
        for row in invocation_rows:
            failure = _logical_failure(
                config,
                phase=phase,
                row=row,
                error_type="PreflightBlocked",
                error=reason,
            )
            failed.append({key: str(value) for key, value in failure.items()})
            _persist_failure(paths, failure)
        return _finalize_phase_summary(
            config,
            project_root=project_root,
            paths=paths,
            phase=phase,
            planned=planned,
            logical_rows=all_logical_rows,
            completed=completed,
            resumed=resumed,
            failed=failed,
            preflight=preflight,
            started=started,
            cpu_started=cpu_started,
            invocation_batch_id=batch_id,
            allow_over_budget=allow_over_budget,
        )

    budget_issue = confirmatory_budget_issue(
        preflight,
        allow_over_budget=allow_over_budget,
        require_confirmatory=(_is_v2(config) and phase == "confirmatory"),
    )
    if budget_issue is not None:
        for row in invocation_rows:
            failure = _logical_failure(
                config,
                phase=phase,
                row=row,
                error_type="ConfirmatoryCostGateBlocked",
                error=budget_issue,
            )
            failed.append({key: str(value) for key, value in failure.items()})
            _persist_failure(paths, failure)
        return _finalize_phase_summary(
            config,
            project_root=project_root,
            paths=paths,
            phase=phase,
            planned=planned,
            logical_rows=all_logical_rows,
            completed=completed,
            resumed=resumed,
            failed=failed,
            preflight=preflight,
            started=started,
            cpu_started=cpu_started,
            invocation_batch_id=batch_id,
            allow_over_budget=allow_over_budget,
        )

    batch_order_issue = _confirmatory_batch_order_issue(
        config,
        phase=phase,
        batch_id=batch_id,
        logical_rows=all_logical_rows,
        phase_path=paths.phase,
        project_root=project_root,
    )
    if batch_order_issue is not None:
        for row in invocation_rows:
            failure = _logical_failure(
                config,
                phase=phase,
                row=row,
                error_type="ConfirmatoryBatchOrderBlocked",
                error=batch_order_issue,
            )
            failed.append({key: str(value) for key, value in failure.items()})
            _persist_failure(paths, failure)
        return _finalize_phase_summary(
            config,
            project_root=project_root,
            paths=paths,
            phase=phase,
            planned=planned,
            logical_rows=all_logical_rows,
            completed=completed,
            resumed=resumed,
            failed=failed,
            preflight=preflight,
            started=started,
            cpu_started=cpu_started,
            invocation_batch_id=batch_id,
            allow_over_budget=allow_over_budget,
        )

    for dataset_key, dataset_config in _dataset_configs(config).items():
        if selected_datasets and dataset_key not in selected_datasets:
            continue
        try:
            prepared = _prepare_one_dataset(
                dataset_key, dataset_config, project_root=project_root, phase=phase
            )
            support_check = _support_check(prepared.dataset, dataset_config, phase)
            if not support_check["passed"]:
                raise RuntimeError(
                    "Academic support gate failed: " + "; ".join(support_check["issues"])
                )
        except Exception as exc:
            affected = [
                row for row in invocation_rows if row["dataset"] == dataset_key
            ]
            for row in affected:
                failure = _logical_failure(
                    config,
                    phase=phase,
                    row=row,
                    error_type=type(exc).__name__,
                    error=str(exc),
                )
                failed.append({key: str(value) for key, value in failure.items()})
                _persist_failure(paths, failure)
            continue

        for model_name, model_config in _model_configs(dataset_config).items():
            if selected_models and model_name not in selected_models:
                continue
            schedule_entries = [
                entry
                for entry in _schedule_entries(config, model_config, phase)
                if batch_id is None or entry.get("batch_id") == batch_id
            ]
            for schedule_entry in schedule_entries:
                seed = int(schedule_entry["seed"])
                descriptor = _cell_descriptor(
                    config,
                    prepared,
                    dataset_key=dataset_key,
                    model_name=model_name,
                    model_config=model_config,
                    phase=phase,
                    seed=seed,
                    schedule_entry=schedule_entry,
                )
                planned.append(descriptor)
                cell_id = str(descriptor["cell_id"])
                cell_path = paths.cells / f"{cell_id}.json"
                if cell_path.is_file():
                    try:
                        existing = _read_json(cell_path)
                        _validate_resume_artifact(
                            existing,
                            descriptor=descriptor,
                            cell_path=cell_path,
                            predictions_dir=paths.predictions,
                            config=config,
                            project_root=project_root,
                        )
                    except Exception as exc:
                        failure = {
                                "dataset": dataset_key,
                                "model": model_name,
                                "seed": str(seed),
                                "error_type": "ResumeIntegrityError",
                                "error": str(exc),
                            }
                        failed.append(failure)
                        _persist_failure(paths, {**failure, **descriptor})
                    else:
                        resumed.append(cell_id)
                    continue
                try:
                    cell, prediction_rows = _execute_cell(
                        config,
                        prepared,
                        descriptor=descriptor,
                        model_name=model_name,
                        model_config=model_config,
                        seed=seed,
                        predictions_dir=paths.predictions,
                        numeric_authority=_mapping(
                            preflight.get("numeric_authority"), "numeric_authority"
                        ),
                        project_root=project_root,
                    )
                    _publish_cell_transaction(
                        paths,
                        cell=cell,
                        prediction_rows=prediction_rows,
                    )
                    completed.append(cell_id)
                except Exception as exc:
                    failure = {
                            "dataset": dataset_key,
                            "model": model_name,
                            "seed": str(seed),
                            "error_type": type(exc).__name__,
                            "error": str(exc),
                        }
                    failed.append(failure)
                    _persist_failure(paths, {**failure, **descriptor})
    return _finalize_phase_summary(
        config,
        project_root=project_root,
        paths=paths,
        phase=phase,
        planned=planned,
        logical_rows=all_logical_rows,
        completed=completed,
        resumed=resumed,
        failed=failed,
        preflight=preflight,
        started=started,
        cpu_started=cpu_started,
        invocation_batch_id=batch_id,
        allow_over_budget=allow_over_budget,
    )


def load_completed_cells(phase_path: Path) -> list[dict[str, object]]:
    phase_directory = Path(phase_path)
    cells_path = phase_directory / "cells"
    if phase_directory.is_symlink():
        raise ValueError("unsafe phase artifact directory symlink")
    if cells_path.is_symlink():
        raise ValueError("unsafe cells artifact directory symlink")
    if not cells_path.is_dir():
        return []
    resolved_cells_path = cells_path.resolve()
    if resolved_cells_path.parent != phase_directory.resolve():
        raise ValueError("cells artifact directory escapes the phase directory")
    cells: list[dict[str, object]] = []
    for path in sorted(cells_path.glob("*.json")):
        if path.is_symlink() or path.resolve().parent != resolved_cells_path:
            raise ValueError(f"unsafe cell artifact path: {path}")
        value = _read_json(path)
        if value.get("status") == "complete":
            value["artifact_path"] = str(path.resolve())
            cells.append(value)
    return cells


def analysis_input_identity(
    cells: Sequence[Mapping[str, object]],
    planned_matrix: Mapping[str, object],
) -> str:
    """Bind analysis to complete cell payloads and the immutable logical plan.

    ``artifact_path`` is injected while loading and is deliberately excluded;
    every field persisted in each cell artifact remains identity-bearing.
    """

    normalized_cells = []
    for cell in cells:
        payload = {
            str(key): value
            for key, value in cell.items()
            if key != "artifact_path"
        }
        normalized_cells.append(payload)
    normalized_cells.sort(
        key=lambda value: (
            str(value.get("cell_id", "")),
            canonical_json_hash(value),
        )
    )
    return canonical_json_hash(
        {
            "cells": normalized_cells,
            "planned_matrix_binding": dict(planned_matrix),
        }
    )


def _logical_failure(
    config: Mapping[str, object],
    *,
    phase: str,
    row: Mapping[str, object],
    error_type: str,
    error: str,
) -> dict[str, object]:
    logical_key = canonical_json_hash(
        {
            "config_identity": config_identity(config),
            "phase": phase,
            "dataset": row.get("dataset"),
            "model": row.get("model"),
            "seed": row.get("seed"),
            "seed_position": row.get("seed_position"),
            "batch_id": row.get("batch_id"),
            "batch_position": row.get("batch_position"),
            "schedule_identity": row.get("schedule_identity"),
        }
    )
    return {
        "schema_version": (
            "academic-cell-failure-v2" if _is_v2(config) else "academic-cell-failure-v1"
        ),
        "runner_protocol": _runner_protocol(config),
        "config_identity": config_identity(config),
        "phase": phase,
        "dataset": row.get("dataset"),
        "model": row.get("model"),
        "seed": row.get("seed"),
        "deterministic": row.get("deterministic"),
        "seed_position": row.get("seed_position"),
        "batch_id": row.get("batch_id"),
        "batch_position": row.get("batch_position"),
        "schedule_kind": row.get("schedule_kind"),
        "schedule_identity": row.get("schedule_identity"),
        "logical_cell_key": logical_key,
        "error_type": error_type,
        "error": error,
    }


def _validate_resume_artifact(
    cell: Mapping[str, object],
    *,
    descriptor: Mapping[str, object],
    cell_path: Path,
    predictions_dir: Path,
    config: Mapping[str, object],
    project_root: Path,
) -> None:
    expected_cells_dir = Path(predictions_dir).parent / "cells"
    if cell_path.is_symlink() or cell_path.resolve().parent != expected_cells_dir.resolve():
        raise ValueError("completed cell artifact path escapes the frozen cells directory")
    expected_schema = "academic-cell-result-v2" if _is_v2(config) else "academic-cell-result-v1"
    if cell.get("schema_version") != expected_schema or cell.get("status") != "complete":
        raise ValueError("completed cell schema/status is incompatible")
    for field in (
        "cell_id",
        "cell_identity",
        "runner_protocol",
        "config_identity",
        "dataset_key",
        "dataset",
        "model",
        "seed",
        "deterministic",
        "phase",
    ):
        if cell.get(field) != descriptor.get(field):
            raise ValueError(f"completed cell {field} does not match the planned descriptor")
    if not _is_v2(config):
        return
    for field in (
        "seed_position",
        "batch_id",
        "batch_position",
        "schedule_kind",
        "schedule_identity",
        "result_dataset_identity",
    ):
        if cell.get(field) != descriptor.get(field):
            raise ValueError(
                f"completed cell {field} does not match the frozen trial ledger"
            )
    if cell.get("evidence_origin") != "official_native":
        raise ValueError("v2 official cell lacks evidence_origin=official_native")
    if cell.get("validation_role_assignment_identity") != descriptor.get(
        "validation_role_assignment_identity"
    ):
        raise ValueError("v2 validation-role assignment is stale or incompatible")
    authority = _mapping(cell.get("numeric_authority"), "cell.numeric_authority")
    if authority.get("accountability_outcome") != "accountable":
        raise ValueError("v2 cell numeric authority is not accountable")
    blind_gate = _mapping(cell.get("blind_test_gate"), "cell.blind_test_gate")
    if (
        blind_gate.get("calibration_frozen_before_test_scoring") is not True
        or blind_gate.get("test_truth_used_for_fit_preprocessing_stopping_or_calibration")
        is not False
    ):
        raise ValueError("blind-test lifecycle gate is absent or invalid")
    current_core = _numerical_core_manifest(project_root, config)
    if cell.get("numerical_core_identity") != current_core.get("identity"):
        raise ValueError("cell numerical-core identity is stale")
    artifact = _mapping(cell.get("predictions_artifact"), "predictions_artifact")
    raw_path = artifact.get("path")
    if not isinstance(raw_path, str) or not raw_path:
        raise ValueError("prediction artifact path is missing")
    raw_prediction_path = Path(raw_path)
    if raw_prediction_path.is_symlink():
        raise ValueError("prediction artifact path must not be a symlink")
    prediction_path = raw_prediction_path.resolve()
    if prediction_path.parent != predictions_dir.resolve():
        raise ValueError("prediction artifact path escapes the frozen predictions directory")
    if not prediction_path.is_file() or file_sha256(prediction_path) != artifact.get("sha256"):
        raise ValueError("prediction artifact is missing or has a mismatched SHA-256")
    expected_rows = artifact.get("rows")
    if not isinstance(expected_rows, int) or isinstance(expected_rows, bool) or expected_rows < 1:
        raise ValueError("prediction artifact row count is invalid")
    rows = prediction_path.read_text(encoding="utf-8").splitlines()
    if len(rows) != expected_rows:
        raise ValueError("prediction artifact row count does not match")
    metric_support = _nested_mapping_value(cell, "test", "operating", "support", "total")
    if metric_support != expected_rows:
        raise ValueError("prediction rows do not match test metric support")
    seen_units: set[str] = set()
    prediction_rows: list[dict[str, object]] = []
    for index, line in enumerate(rows, start=1):
        try:
            value = json.loads(line)
        except json.JSONDecodeError as exc:
            raise ValueError(f"prediction row {index} is invalid JSON") from exc
        if not isinstance(value, Mapping):
            raise ValueError(f"prediction row {index} is not an object")
        unit_id = value.get("unit_id")
        if not isinstance(unit_id, str) or not unit_id or unit_id in seen_units:
            raise ValueError(f"prediction row {index} has a missing/duplicate unit identity")
        seen_units.add(unit_id)
        if value.get("evidence_origin") != "official_native":
            raise ValueError(f"prediction row {index} has incompatible evidence_origin")
        if value.get("cell_identity") != descriptor.get("cell_identity"):
            raise ValueError(f"prediction row {index} has incompatible cell identity")
        if type(value.get("truth")) is not int or value.get("truth") not in {0, 1}:
            raise ValueError(f"prediction row {index} has a non-binary label")
        if (
            type(value.get("prediction")) is not int
            or value.get("prediction") not in {0, 1}
        ):
            raise ValueError(f"prediction row {index} has a non-binary label/prediction")
        for numeric_name in ("score", "threshold"):
            numeric = value.get(numeric_name)
            if (
                not isinstance(numeric, (int, float))
                or isinstance(numeric, bool)
                or not math.isfinite(float(numeric))
            ):
                raise ValueError(f"prediction row {index} has invalid {numeric_name}")
        prediction_rows.append(dict(value))
    _validate_publication_transaction(
        cell,
        cell_path=cell_path,
        prediction_path=prediction_path,
    )
    validate_cell_raw_reconstruction(
        cell,
        config=config,
        prediction_rows=prediction_rows,
    )


def _validate_publication_transaction(
    cell: Mapping[str, object],
    *,
    cell_path: Path,
    prediction_path: Path,
) -> None:
    publication = _mapping(
        cell.get("publication_transaction"), "cell.publication_transaction"
    )
    cell_id = str(cell.get("cell_id", ""))
    phase_path = cell_path.parent.parent
    transactions_dir = phase_path / "transactions"
    expected_manifest = transactions_dir / f"{cell_id}.transaction.json"
    if (
        publication.get("transaction_id")
        != f"academic-cell-publication:{cell_id}"
        or publication.get("manifest_path") != str(expected_manifest.resolve())
        or expected_manifest.is_symlink()
        or not expected_manifest.is_file()
    ):
        raise ValueError("cell publication transaction is missing or incompatible")
    manifest = _read_json(expected_manifest)
    identity = manifest.get("identity")
    core = {key: value for key, value in manifest.items() if key != "identity"}
    if (
        manifest.get("schema_version")
        != "academic-cell-publication-transaction-v1"
        or manifest.get("state") != "committed"
        or manifest.get("transaction_id") != publication.get("transaction_id")
        or manifest.get("cell_id") != cell_id
        or identity != canonical_json_hash(core)
    ):
        raise ValueError("cell publication transaction manifest failed authentication")
    if (
        manifest.get("cell_target_path") != str(cell_path.resolve())
        or manifest.get("prediction_target_path") != str(prediction_path.resolve())
        or manifest.get("cell_sha256") != file_sha256(cell_path)
        or manifest.get("prediction_sha256") != file_sha256(prediction_path)
    ):
        raise ValueError("cell publication transaction target/hash mismatch")
    for field, expected_hash in (
        ("cell_payload_path", manifest.get("cell_sha256")),
        ("prediction_payload_path", manifest.get("prediction_sha256")),
    ):
        payload_path = Path(str(manifest.get(field, "")))
        if (
            payload_path.is_symlink()
            or payload_path.resolve().parent != transactions_dir.resolve()
            or not payload_path.is_file()
            or file_sha256(payload_path) != expected_hash
        ):
            raise ValueError("cell publication recovery payload is unauthenticated")


def _validated_raw_evidence_rows(
    rows: Sequence[Mapping[str, object]],
    *,
    role: str,
    cell: Mapping[str, object],
) -> dict[str, object]:
    if not rows:
        raise ValueError(f"{role} raw evidence rows must not be empty")
    unit_ids: list[str] = []
    truths: list[int] = []
    scores: list[float] = []
    class_names: list[str] = []
    event_ids: list[tuple[str, ...]] = []
    cluster_ids: list[str] = []
    predictions: list[int] = []
    thresholds: list[float] = []
    seen: set[str] = set()
    for index, row in enumerate(rows, start=1):
        if row.get("role") != role:
            raise ValueError(f"{role} row {index} has an incompatible role")
        unit_id = row.get("unit_id")
        if not isinstance(unit_id, str) or not unit_id or unit_id in seen:
            raise ValueError(f"{role} row {index} has a missing/duplicate unit_id")
        seen.add(unit_id)
        truth = row.get("truth")
        if type(truth) is not int or truth not in {0, 1}:
            raise ValueError(f"{role} row {index} has an invalid binary truth")
        score = row.get("score")
        if (
            not isinstance(score, (int, float))
            or isinstance(score, bool)
            or not math.isfinite(float(score))
        ):
            raise ValueError(f"{role} row {index} has an invalid finite score")
        class_name = row.get("class_name")
        cluster_id = row.get("resampling_cluster_id")
        raw_events = row.get("event_ids")
        window_count = row.get("window_count")
        if not isinstance(class_name, str) or not class_name:
            raise ValueError(f"{role} row {index} has an invalid class_name")
        if not isinstance(cluster_id, str) or not cluster_id:
            raise ValueError(f"{role} row {index} has an invalid cluster identity")
        if (
            not isinstance(raw_events, list)
            or any(not isinstance(value, str) or not value for value in raw_events)
        ):
            raise ValueError(f"{role} row {index} has invalid event_ids")
        if (
            type(window_count) is not int
            or window_count < 1
        ):
            raise ValueError(f"{role} row {index} has an invalid window_count")
        if row.get("evidence_origin") != "official_native":
            raise ValueError(f"{role} row {index} has incompatible evidence_origin")
        if row.get("cell_identity") != cell.get("cell_identity"):
            raise ValueError(f"{role} row {index} has incompatible cell_identity")
        if row.get("phase") != cell.get("phase"):
            raise ValueError(f"{role} row {index} has incompatible phase")
        unit_ids.append(unit_id)
        truths.append(truth)
        scores.append(float(score))
        class_names.append(class_name)
        event_ids.append(tuple(raw_events))
        cluster_ids.append(cluster_id)
        if role == "blind-test":
            prediction = row.get("prediction")
            threshold = row.get("threshold")
            if type(prediction) is not int or prediction not in {0, 1}:
                raise ValueError(f"blind-test row {index} has an invalid prediction")
            if (
                not isinstance(threshold, (int, float))
                or isinstance(threshold, bool)
                or not math.isfinite(float(threshold))
            ):
                raise ValueError(f"blind-test row {index} has an invalid threshold")
            predictions.append(prediction)
            thresholds.append(float(threshold))
    return {
        "unit_ids": unit_ids,
        "truths": truths,
        "scores": scores,
        "class_names": class_names,
        "event_ids": event_ids,
        "cluster_ids": cluster_ids,
        "predictions": predictions,
        "thresholds": thresholds,
    }


def _require_reconstruction_match(
    actual: object, expected: object, *, field: str
) -> None:
    if canonical_json_hash(_json_safe(actual)) != canonical_json_hash(
        _json_safe(expected)
    ):
        raise ValueError(f"raw-evidence reconstruction mismatch at {field}")


def validate_cell_raw_reconstruction(
    cell: Mapping[str, object],
    *,
    config: Mapping[str, object],
    prediction_rows: Sequence[Mapping[str, object]] | None = None,
) -> dict[str, object]:
    """Recompute every admitted outcome from authenticated calibration/test rows."""

    if not _is_v2(config):
        return {"passed": True, "status": "legacy-not-required"}
    binding = _mapping(cell.get("raw_evidence_binding"), "raw_evidence_binding")
    if binding.get("schema_version") != "academic-cell-raw-evidence-v1":
        raise ValueError("v2 cell raw-evidence binding is missing or unsupported")
    validation = _mapping(
        cell.get("validation_calibration"), "validation_calibration"
    )
    raw_calibration = validation.get("raw_rows")
    if not isinstance(raw_calibration, list) or any(
        not isinstance(row, Mapping) for row in raw_calibration
    ):
        raise ValueError("validation-calibration raw rows are missing or malformed")
    calibration_rows = [dict(row) for row in raw_calibration]
    calibration_identity = canonical_json_hash(calibration_rows)
    if (
        validation.get("raw_rows_identity") != calibration_identity
        or binding.get("calibration_rows_identity") != calibration_identity
    ):
        raise ValueError("validation-calibration raw row identity mismatch")
    if prediction_rows is None:
        artifact = _mapping(cell.get("predictions_artifact"), "predictions_artifact")
        path = Path(str(artifact.get("path", "")))
        if path.is_symlink() or not path.is_file():
            raise ValueError("blind-test raw evidence artifact is unavailable")
        loaded_rows: list[dict[str, object]] = []
        for index, line in enumerate(path.read_text(encoding="utf-8").splitlines(), 1):
            try:
                row = json.loads(line)
            except json.JSONDecodeError as exc:
                raise ValueError(f"blind-test raw row {index} is invalid JSON") from exc
            if not isinstance(row, dict):
                raise ValueError(f"blind-test raw row {index} is not an object")
            loaded_rows.append(row)
        prediction_rows = loaded_rows
    normalized_prediction_rows = [dict(row) for row in prediction_rows]
    test_identity = canonical_json_hash(normalized_prediction_rows)
    if binding.get("test_rows_identity") != test_identity:
        raise ValueError("blind-test raw row identity mismatch")

    calibration_values = _validated_raw_evidence_rows(
        calibration_rows, role="validation-calibration", cell=cell
    )
    test_values = _validated_raw_evidence_rows(
        normalized_prediction_rows, role="blind-test", cell=cell
    )
    statistical = _mapping(config.get("statistical_protocol"), "statistical_protocol")
    threshold_config = _mapping(statistical.get("threshold"), "threshold")
    if (
        threshold_config.get("direction") != "higher-is-more-anomalous"
        or threshold_config.get("calibration_partition")
        != "validation-calibration"
    ):
        raise ValueError("raw reconstruction requires the frozen v2 threshold lifecycle")
    recalibrated = calibrate_threshold(
        calibration_values["scores"],  # type: ignore[arg-type]
        calibration_values["truths"],  # type: ignore[arg-type]
        method=str(threshold_config["method"]),
        quantile=float(threshold_config["normal_quantile"]),
        target_fpr=float(threshold_config["target_fpr"]),
        sensitivity_quantiles=tuple(
            float(value)
            for value in threshold_config["sensitivity_normal_quantiles"]  # type: ignore[union-attr]
        ),
    )
    _require_reconstruction_match(
        cell.get("threshold_calibration"),
        recalibrated.to_dict(),
        field="threshold_calibration",
    )
    scores = np.asarray(test_values["scores"], dtype=np.float64)
    truths = np.asarray(test_values["truths"], dtype=np.int64)
    reconstructed_predictions = (scores >= recalibrated.value).astype(np.int64)
    _require_reconstruction_match(
        test_values["predictions"],
        reconstructed_predictions.tolist(),
        field="prediction rows",
    )
    for threshold in test_values["thresholds"]:  # type: ignore[union-attr]
        if float(threshold) != float(recalibrated.value):
            raise ValueError("blind-test row threshold differs from frozen calibration")

    bootstrap = bootstrap_confidence_intervals(
        scores,
        truths,
        threshold=recalibrated.value,
        replicates=int(statistical["bootstrap_replicates"]),
        confidence_level=float(statistical["confidence_level"]),
        seed=int(cell["seed"]) + int(statistical["bootstrap_seed_offset"]),
        cluster_ids=tuple(str(value) for value in test_values["cluster_ids"]),
        minimum_clusters=int(statistical["minimum_bootstrap_clusters"]),
        minimum_class_carrying_clusters=int(
            statistical["minimum_class_carrying_clusters"]
        ),
        minimum_valid_replicates=int(
            statistical["minimum_valid_bootstrap_replicates"]
        ),
        minimum_valid_fraction=float(
            statistical["minimum_valid_bootstrap_fraction"]
        ),
    )
    expected_test = {
        "operating": binary_operating_metrics(scores, truths, recalibrated.value),
        "ranking": ranking_metrics(scores, truths),
        "bootstrap_unit_ci": bootstrap,
        "per_attack_class": per_class_detection_metrics(
            scores.tolist(),
            truths.tolist(),
            tuple(str(value) for value in test_values["class_names"]),
            threshold=recalibrated.value,
        ),
        "events": event_metrics(
            reconstructed_predictions.tolist(),
            truths.tolist(),
            tuple(tuple(value) for value in test_values["event_ids"]),
        ),
        "curves": curve_points(
            scores,
            truths,
            max_points=int(statistical["curve_max_points"]),
        ),
        "score_distribution": score_distribution(scores, truths),
    }
    _require_reconstruction_match(cell.get("test"), expected_test, field="test metrics")
    expected_validation = {
        "unit_support": _binary_support(calibration_values["truths"]),
        "score_distribution": score_distribution(
            calibration_values["scores"],  # type: ignore[arg-type]
            calibration_values["truths"],  # type: ignore[arg-type]
        ),
        "raw_rows": calibration_rows,
        "raw_rows_identity": calibration_identity,
    }
    _require_reconstruction_match(
        validation, expected_validation, field="validation_calibration"
    )
    reconstruction_identity = canonical_json_hash(
        {
            "cell_identity": cell.get("cell_identity"),
            "calibration_rows_identity": calibration_identity,
            "test_rows_identity": test_identity,
            "threshold_calibration": recalibrated.to_dict(),
            "test": expected_test,
        }
    )
    return {
        "passed": True,
        "status": "independently-reconstructed-from-authenticated-raw-rows",
        "calibration_row_count": len(calibration_rows),
        "test_row_count": len(normalized_prediction_rows),
        "identity": reconstruction_identity,
    }


def _expected_descriptors(
    config: Mapping[str, object], *, project_root: Path, phase: str
) -> list[dict[str, object]]:
    descriptors: list[dict[str, object]] = []
    for dataset_key, dataset_config in _dataset_configs(config).items():
        prepared = _prepare_one_dataset(
            dataset_key, dataset_config, project_root=project_root, phase=phase
        )
        for model_name, model_config in _model_configs(dataset_config).items():
            for schedule_entry in _schedule_entries(config, model_config, phase):
                seed = int(schedule_entry["seed"])
                descriptors.append(
                    _cell_descriptor(
                        config,
                        prepared,
                        dataset_key=dataset_key,
                        model_name=model_name,
                        model_config=model_config,
                        phase=phase,
                        seed=seed,
                        schedule_entry=schedule_entry,
                    )
                )
    return descriptors


def _retained_failure_records(phase_path: Path) -> list[dict[str, object]]:
    failure_dir = Path(phase_path) / "failures"
    if failure_dir.is_symlink():
        raise ValueError("failure artifact directory must not be a symlink")
    if not failure_dir.is_dir():
        return []
    if failure_dir.resolve().parent != Path(phase_path).resolve():
        raise ValueError("failure artifact directory escapes the phase directory")
    return [_read_json(path) for path in sorted(failure_dir.glob("*.json"))]


def _finalize_phase_summary(
    config: Mapping[str, object],
    *,
    project_root: Path,
    paths: AcademicPaths,
    phase: str,
    planned: Sequence[Mapping[str, object]],
    logical_rows: Sequence[Mapping[str, object]],
    completed: Sequence[str],
    resumed: Sequence[str],
    failed: Sequence[Mapping[str, object]],
    preflight: Mapping[str, object],
    started: float,
    cpu_started: float,
    invocation_batch_id: str | None = None,
    allow_over_budget: bool = False,
) -> dict[str, object]:
    authentication_errors: list[str] = []
    previous_summary_path = paths.phase / "run-summary.json"
    previous_summary = (
        _read_json(previous_summary_path)
        if previous_summary_path.is_file()
        else {}
    )
    try:
        expected = (
            _expected_descriptors(config, project_root=project_root, phase=phase)
            if preflight.get("ready") is True
            else list(planned)
        )
    except Exception as exc:
        expected = list(planned)
        authentication_errors.append(f"cannot reconstruct full planned descriptors: {exc}")
    expected_by_id = {str(item.get("cell_id")): item for item in expected}
    if len(expected_by_id) != len(expected):
        authentication_errors.append("planned descriptors contain duplicate cell_id values")
    try:
        available = load_completed_cells(paths.phase)
    except Exception as exc:
        available = []
        authentication_errors.append(f"cannot load complete cell artifacts safely: {exc}")
    available_by_id = {str(item.get("cell_id")): item for item in available}
    duplicate_available_cell_ids = len(available_by_id) != len(available)
    if duplicate_available_cell_ids:
        authentication_errors.append("complete cell artifacts contain duplicate cell_id values")
    planned_matrix_path = paths.phase / "planned-matrix.json"
    if planned_matrix_path.is_file():
        planned_matrix = _read_json(planned_matrix_path)
    else:
        planned_matrix = {}
        authentication_errors.append("immutable planned-matrix artifact is missing")
    current_analysis_input_identity = analysis_input_identity(
        available, planned_matrix
    )
    authenticated: list[str] = []
    for cell_id, descriptor in expected_by_id.items():
        cell = available_by_id.get(cell_id)
        if cell is None:
            authentication_errors.append(f"planned cell is missing: {cell_id}")
            continue
        try:
            _validate_resume_artifact(
                cell,
                descriptor=descriptor,
                cell_path=Path(str(cell.get("artifact_path", paths.cells / f"{cell_id}.json"))),
                predictions_dir=paths.predictions,
                config=config,
                project_root=project_root,
            )
        except Exception as exc:
            authentication_errors.append(f"{cell_id}: {exc}")
        else:
            authenticated.append(cell_id)
    extra_ids = sorted(set(available_by_id) - set(expected_by_id))
    if extra_ids:
        authentication_errors.append(f"unplanned complete cells are present: {extra_ids}")
    completed_logical = {
        (str(cell.get("dataset")), str(cell.get("model")), str(cell.get("seed")))
        for cell in available
        if str(cell.get("cell_id")) in authenticated
    }
    try:
        retained_failures = _retained_failure_records(paths.phase)
    except Exception as exc:
        retained_failures = []
        authentication_errors.append(f"cannot load retained failure artifacts safely: {exc}")
    unresolved_failures = [
        item
        for item in retained_failures
        if (
            str(item.get("dataset")),
            str(item.get("model")),
            str(item.get("seed")),
        )
        not in completed_logical
    ]
    current_core = _numerical_core_manifest(project_root, config)
    stored_core_path = paths.root / "numerical-core-manifest.json"
    core_verified = (
        stored_core_path.is_file()
        and _read_json(stored_core_path).get("identity") == current_core.get("identity")
    )
    exact_matrix = (
        bool(expected_by_id)
        and set(authenticated) == set(expected_by_id)
        and len(authenticated) == len(expected_by_id)
        and not extra_ids
    )
    origins_valid = bool(available) and all(
        cell.get("evidence_origin") == "official_native" for cell in available
    )
    schemas_valid = bool(available) and all(
        cell.get("schema_version")
        == ("academic-cell-result-v2" if _is_v2(config) else "academic-cell-result-v1")
        for cell in available
    )
    statistical_protocol = _mapping(
        config.get("statistical_protocol"), "statistical_protocol"
    )
    primary_metric = str(statistical_protocol.get("primary_metric", "auroc"))
    primary_outcomes_complete = bool(available) and all(
        _cell_metric(cell, primary_metric) is not None for cell in available
    )
    numeric_accountable = (
        not _is_v2(config)
        or _nested_mapping_value(preflight, "numeric_authority", "accountability_outcome")
        == "accountable"
    )
    allocation_passed = (
        not _is_v2(config)
        or (
            _nested_mapping_value(preflight, "phase_allocation_audit", "passed") is True
            and all(
                isinstance(value, Mapping)
                and _nested_mapping_value(value, "phase_disjointness", "passed") is True
                for value in _mapping(preflight.get("datasets"), "datasets").values()
            )
        )
    )
    preflight_datasets = _mapping(preflight.get("datasets"), "datasets")
    validation_roles_disjoint = (
        not _is_v2(config)
        or (
            bool(preflight_datasets)
            and all(
                _nested_mapping_value(
                    value, "validation_role_split", "passed"
                )
                is True
                and _nested_mapping_value(
                    value, "validation_role_split", "independent_roles"
                )
                is True
                for value in preflight_datasets.values()
                if isinstance(value, Mapping)
            )
            and all(isinstance(value, Mapping) for value in preflight_datasets.values())
        )
    )
    repetition_planning_authenticated = (
        not _is_v2(config)
        or (
            _nested_mapping_value(preflight, "repetition_planning_gate", "passed")
            is True
            and (
                phase != "confirmatory"
                or _nested_mapping_value(
                    preflight, "repetition_planning_gate", "status"
                )
                == "fixed-nonadaptive-50-after-complete-five-trial-pilot"
            )
        )
    )
    prediction_verified = exact_matrix and not authentication_errors
    raw_evidence_reconstructed = exact_matrix and not authentication_errors
    gate_reasons = list(authentication_errors)
    batch_ledger_issue = (
        _confirmatory_batch_ledger_issue(config, paths.phase)
        if _is_v2(config) and phase == "confirmatory"
        else None
    )
    if batch_ledger_issue is not None:
        gate_reasons.append(batch_ledger_issue)
    if unresolved_failures:
        gate_reasons.append(f"{len(unresolved_failures)} planned cell failures remain unresolved")
    budget_issue = confirmatory_budget_issue(
        preflight,
        allow_over_budget=allow_over_budget,
        require_confirmatory=(_is_v2(config) and phase == "confirmatory"),
    )
    if budget_issue is not None:
        gate_reasons.append(budget_issue)
    flags = {
        "exact_matrix_match": exact_matrix,
        "prediction_artifacts_verified": prediction_verified,
        "raw_evidence_reconstructed": raw_evidence_reconstructed,
        "core_manifest_verified": core_verified,
        "numeric_authority_accountable": numeric_accountable,
        "evidence_origins_valid": origins_valid,
        "phase_disjointness_passed": allocation_passed,
        "validation_roles_disjoint": validation_roles_disjoint,
        "repetition_planning_authenticated": repetition_planning_authenticated,
        "schema_versions_valid": schemas_valid,
        "primary_outcomes_complete": primary_outcomes_complete,
        "computational_budget_authorized": budget_issue is None,
        "confirmatory_batch_ledger_verified": batch_ledger_issue is None,
    }
    for flag_name, passed in flags.items():
        if not passed:
            gate_reasons.append(f"eligibility flag failed: {flag_name}")
    gate_eligible = (
        _is_v2(config)
        and phase == "confirmatory"
        and preflight.get("ready") is True
        and all(flags.values())
        and not unresolved_failures
    )
    eligibility_gate = {
        "eligible": gate_eligible,
        "phase": phase,
        "config_identity": config_identity(config),
        **flags,
        "planned_cell_ids": sorted(expected_by_id),
        "authenticated_complete_cell_ids": sorted(authenticated),
        "retained_failure_count": len(unresolved_failures),
        "historical_failure_count": len(retained_failures),
        "reasons": gate_reasons,
        "identity": canonical_json_hash(
            {
                "phase": phase,
                "config_identity": config_identity(config),
                "flags": flags,
                "planned": sorted(expected_by_id),
                "authenticated": sorted(authenticated),
                "unresolved_failures": len(unresolved_failures),
                "analysis_input_identity": current_analysis_input_identity,
            }
        ),
    }
    confirmatory_analysis_withheld = (
        _is_v2(config) and phase == "confirmatory" and not gate_eligible
    )
    frozen_repetition_plans = _nested_mapping_value(
        preflight, "repetition_planning_gate", "pilot_planning"
    )
    analysis = (
        {
            "phase": phase,
            "status": "withheld-until-full-matrix-authenticated",
            "outcome_aggregates_emitted": False,
            "reason": (
                "Confirmatory outcome analysis is prohibited until every frozen cell and "
                "prediction artifact is authenticated and no planned failure remains unresolved."
            ),
        }
        if confirmatory_analysis_withheld
        else analyze_completed_cells(
            config,
            available,
            phase=phase,
            frozen_repetition_plans=(
                frozen_repetition_plans
                if isinstance(frozen_repetition_plans, Mapping)
                else None
            ),
        )
    )
    analysis = {
        **analysis,
        "analysis_input_identity": current_analysis_input_identity,
        "planned_matrix_identity": canonical_json_hash(planned_matrix),
    }
    batch_progress: list[dict[str, object]] = []
    if _is_v2(config) and phase == "confirmatory":
        progress_source = list(logical_rows)
        valid_batch_ids = {
            f"batch-{index:02d}"
            for index in range(1, V2_CONFIRMATORY_BATCH_COUNT + 1)
        }
        unassigned_unplanned_artifact = any(
            available_by_id[cell_id].get("batch_id") not in valid_batch_ids
            for cell_id in extra_ids
        )
        for batch_number in range(1, V2_CONFIRMATORY_BATCH_COUNT + 1):
            current_batch_id = f"batch-{batch_number:02d}"
            expected_ids = {
                cell_id
                for cell_id, descriptor in expected_by_id.items()
                if descriptor.get("batch_id") == current_batch_id
            }
            complete_ids = expected_ids & set(authenticated)
            unplanned_batch_ids = {
                cell_id
                for cell_id in extra_ids
                if available_by_id[cell_id].get("batch_id") == current_batch_id
            }
            expected_count = sum(
                row.get("batch_id") == current_batch_id for row in progress_source
            )
            batch_progress.append(
                {
                    "batch_id": current_batch_id,
                    "expected_cell_count": expected_count,
                    "authenticated_complete_cell_count": len(complete_ids),
                    "complete": (
                        bool(expected_ids)
                        and len(expected_ids) == expected_count
                        and complete_ids == expected_ids
                        and not unplanned_batch_ids
                        and not unassigned_unplanned_artifact
                        and not duplicate_available_cell_ids
                        and batch_ledger_issue is None
                    ),
                }
            )
    elapsed_seconds = time.perf_counter() - started
    elapsed_cpu_seconds = time.process_time() - cpu_started
    prior_cumulative_cpu = 0.0
    if (
        previous_summary.get("config_identity") == config_identity(config)
        and previous_summary.get("phase") == phase
    ):
        previous_value = previous_summary.get(
            "evidence_generation_cpu_seconds_cumulative",
            previous_summary.get("elapsed_cpu_seconds"),
        )
        if (
            isinstance(previous_value, (int, float))
            and not isinstance(previous_value, bool)
            and math.isfinite(float(previous_value))
            and float(previous_value) >= 0.0
        ):
            prior_cumulative_cpu = float(previous_value)
    cumulative_cpu_seconds = prior_cumulative_cpu + elapsed_cpu_seconds
    summary: dict[str, object] = {
        "schema_version": "academic-run-summary-v2" if _is_v2(config) else "academic-run-summary-v1",
        "runner_protocol": _runner_protocol(config),
        "experiment_id": config.get("experiment_id"),
        "config_identity": config_identity(config),
        "phase": phase,
        "invocation_batch_id": invocation_batch_id,
        "generated_at_utc": _utc_now(),
        "elapsed_seconds": elapsed_seconds,
        "elapsed_cpu_seconds": elapsed_cpu_seconds,
        "evidence_generation_cpu_seconds_cumulative": cumulative_cpu_seconds,
        "planned_cell_count": len(expected_by_id) if expected_by_id else len(logical_rows),
        "complete_cell_count": len(available),
        "completed_now": list(completed),
        "resumed": list(resumed),
        "failed": [dict(value) for value in failed],
        "batch_progress": batch_progress,
        "computational_budget": {
            "projection_complete": _nested_mapping_value(
                preflight, "computational_load", "projection_complete"
            ),
            "projected_preflight_invocations": _nested_mapping_value(
                preflight,
                "computational_load",
                "projected_preflight_invocations",
            ),
            "confirmatory_preflight_invocations": _nested_mapping_value(
                preflight,
                "computational_load",
                "confirmatory_preflight_invocations",
            ),
            "confirmatory_standalone_preflight_invocations": _nested_mapping_value(
                preflight,
                "computational_load",
                "confirmatory_standalone_preflight_invocations",
            ),
            "confirmatory_batch_preflight_invocations": _nested_mapping_value(
                preflight,
                "computational_load",
                "confirmatory_batch_preflight_invocations",
            ),
            "projected_total_cpu_hours_conservative": _nested_mapping_value(
                preflight,
                "computational_load",
                "projected_total_cpu_hours_conservative",
            ),
            "ask_first_cpu_hours": _nested_mapping_value(
                preflight, "computational_load", "ask_first_cpu_hours"
            ),
            "over_budget_authorized": bool(allow_over_budget),
            "eligibility_authorized": budget_issue is None,
            "authorization_issue": budget_issue,
        },
        "confirmatory_analysis_withheld": confirmatory_analysis_withheld,
        "eligibility_gate": eligibility_gate,
        "analysis": analysis,
        "planned_matrix_identity": canonical_json_hash(planned_matrix),
        "analysis_input_identity": current_analysis_input_identity,
        "analysis_identity": canonical_json_hash(analysis),
        "confirmatory_batch_ledger_identity": (
            canonical_json_hash(confirmatory_batch_ledger(config))
            if _is_v2(config)
            and phase == "confirmatory"
            and batch_ledger_issue is None
            else None
        ),
    }
    _write_json(paths.phase / "run-summary.json", summary, immutable=False)
    if invocation_batch_id is not None:
        batch_record: dict[str, object] = {
            "schema_version": "academic-confirmatory-batch-progress-v1",
            "runner_protocol": _runner_protocol(config),
            "config_identity": config_identity(config),
            "schedule_identity": _phase_schedule_identity(config, phase),
            "batch_id": invocation_batch_id,
            "generated_at_utc": summary["generated_at_utc"],
            "batch_progress": batch_progress,
            "completed_now": list(completed),
            "resumed": list(resumed),
            "failures": [dict(value) for value in failed],
            "computational_budget": summary["computational_budget"],
            "artifact_integrity": {
                "authenticated_complete_cell_count": len(authenticated),
                "expected_full_matrix_cell_count": len(expected_by_id),
                "unplanned_complete_cell_ids": extra_ids,
                "authentication_errors": authentication_errors,
            },
            "outcome_aggregates_emitted": False,
            "later_batch_schedule_mutable": False,
        }
        invocation_identity = canonical_json_hash(batch_record)
        batch_record["invocation_identity"] = invocation_identity
        _write_json(
            paths.phase / "batches" / f"{invocation_batch_id}-progress.json",
            batch_record,
            immutable=False,
        )
        _write_json(
            paths.phase
            / "batches"
            / "history"
            / f"{invocation_batch_id}-{invocation_identity[-12:]}.json",
            batch_record,
            immutable=True,
        )
    return summary


def analyze_completed_cells(
    config: Mapping[str, object],
    cells: Sequence[Mapping[str, object]],
    *,
    phase: str,
    frozen_repetition_plans: Mapping[str, object] | None = None,
) -> dict[str, object]:
    """Aggregate trials, derive precision-based repetition counts, compare models."""

    statistics = _mapping(config.get("statistical_protocol"), "statistical_protocol")
    confidence = float(statistics.get("confidence_level", 0.95))
    primary_metric = str(statistics.get("primary_metric", "auroc"))
    metric_names = tuple(
        str(name)
        for name in statistics.get(
            "reported_metrics",
            ["f1", "balanced_accuracy", "mcc", "auroc", "auprc"],
        )
    )
    grouped: dict[tuple[str, str], list[Mapping[str, object]]] = {}
    for cell in cells:
        grouped.setdefault((str(cell["dataset"]), str(cell["model"])), []).append(cell)

    groups: dict[str, object] = {}
    values_by_dataset_model: dict[str, dict[str, dict[int, float]]] = {}
    for (dataset_name, model_name), rows in sorted(grouped.items()):
        key = f"{dataset_name}/{model_name}"
        estimates: dict[str, object] = {}
        for metric_name in metric_names:
            values = [
                value
                for row in rows
                if (value := _cell_metric(row, metric_name)) is not None
            ]
            estimates[metric_name] = aggregate_repeated_estimates(
                values, confidence_level=confidence
            )
        primary_values = [_cell_metric(row, primary_metric) for row in rows]
        primary_by_seed = {
            int(row["seed"]): value
            for row, value in zip(rows, primary_values)
            if value is not None
        }
        values_by_dataset_model.setdefault(dataset_name, {})[model_name] = primary_by_seed
        deterministic = all(bool(row.get("deterministic", False)) for row in rows)
        if _is_v2(config) and phase == "confirmatory" and not deterministic:
            frozen = (
                frozen_repetition_plans.get(key)
                if isinstance(frozen_repetition_plans, Mapping)
                else None
            )
            repetition = dict(frozen) if isinstance(frozen, Mapping) else {}
            repetition.update(
                {
                    "status": "frozen-from-authenticated-pilot",
                    "configured_trial_cap": V2_CONFIRMATORY_TRIALS,
                    "operational_trial_cap": V2_CONFIRMATORY_TRIALS,
                    "fixed_execution_trials": V2_CONFIRMATORY_TRIALS,
                    "scheduled_execution_trials": V2_CONFIRMATORY_TRIALS,
                    "scheduled_cap_reached": True,
                    "operational_cap_reached": len(rows)
                    == V2_CONFIRMATORY_TRIALS,
                    "operational_cap_reached_reason": (
                        "authenticated completed confirmatory trials equal the frozen cap"
                        if len(rows) == V2_CONFIRMATORY_TRIALS
                        else "authenticated completed confirmatory trials remain below the frozen cap"
                    ),
                    "execution_schedule_adaptive": False,
                    "reason": (
                        "Prospective precision planning was frozen from five pilot outcomes; "
                        "confirmatory outcomes never revise the 50-seed schedule."
                    ),
                }
            )
        else:
            repetition = derive_repetition_count(
                (
                    primary_values
                    if _is_v2(config) and phase == "pilot" and not deterministic
                    else list(primary_by_seed.values())
                ),
                target_half_width=float(statistics.get("target_ci_half_width", 0.025)),
                confidence_level=confidence,
                minimum=int(statistics.get("minimum_stochastic_trials", 10)),
                maximum=int(statistics.get("maximum_stochastic_trials", 30)),
                required_pilot_trials=(
                    V2_PILOT_TRIALS
                    if _is_v2(config) and phase == "pilot" and not deterministic
                    else None
                ),
                fixed_execution_trials=(
                    V2_CONFIRMATORY_TRIALS
                    if _is_v2(config) and phase == "pilot" and not deterministic
                    else None
                ),
            )
        if deterministic:
            repetition = {
                **repetition,
                "status": "deterministic-single-fit-per-phase",
                "planning_determinate": None,
                "uncapped_required_trials": None,
                "recommended_total_trials": 1,
                "fixed_execution_trials": 1,
                "scheduled_execution_trials": 1,
                "operational_trial_cap": 1,
                "scheduled_cap_reached": True,
                "operational_cap_reached": len(rows) == 1,
                "operational_cap_reached_reason": (
                    "the deterministic singleton fit is authenticated"
                    if len(rows) == 1
                    else "the deterministic singleton fit is not yet authenticated"
                ),
                "maximum_cap_binding": False,
                "projected_ci_half_width_at_cap": None,
                "precision_target_projected_met_at_cap": None,
                "execution_schedule_adaptive": False,
                "reason": (
                    "deterministic fit executed once in this phase; uncertainty is "
                    "estimated from independent test units or declared clusters"
                ),
            }
        primary_summary = _mapping(
            estimates.get(primary_metric), f"{key}.{primary_metric}"
        )
        achieved_low = primary_summary.get("ci_low")
        achieved_high = primary_summary.get("ci_high")
        achieved_half_width = (
            (float(achieved_high) - float(achieved_low)) / 2.0
            if isinstance(achieved_low, (int, float))
            and isinstance(achieved_high, (int, float))
            and math.isfinite(float(achieved_low))
            and math.isfinite(float(achieved_high))
            else None
        )
        if _is_v2(config) and phase == "confirmatory" and not deterministic:
            target_half_width = float(
                statistics.get("target_ci_half_width", 0.025)
            )
            repetition.update(
                {
                    "confirmatory_trials_attempted": len(rows),
                    "confirmatory_primary_outcomes_usable": primary_summary.get("n"),
                    "achieved_ci_half_width": achieved_half_width,
                    "precision_target_observed_met": (
                        None
                        if achieved_half_width is None
                        else achieved_half_width <= target_half_width + 1e-15
                    ),
                    "achieved_precision_scope": (
                        "across-seed training variability only; it does not estimate or "
                        "repair uncertainty from too few independent units or clusters"
                    ),
                }
            )
        fit_wall_values = [
            float(value)
            for row in rows
            if isinstance(row.get("model_fit"), Mapping)
            and isinstance((value := row["model_fit"].get("fit_wall_seconds")), (int, float))  # type: ignore[index,union-attr]
        ]
        fit_cpu_values = [
            float(value)
            for row in rows
            if isinstance(row.get("model_fit"), Mapping)
            and isinstance((value := row["model_fit"].get("fit_cpu_seconds")), (int, float))  # type: ignore[index,union-attr]
        ]
        recommended_raw = repetition.get("recommended_total_trials")
        recommended = (
            int(recommended_raw)
            if isinstance(recommended_raw, int) and not isinstance(recommended_raw, bool)
            else None
        )
        fixed_raw = repetition.get("fixed_execution_trials")
        fixed_trials = (
            int(fixed_raw)
            if isinstance(fixed_raw, int) and not isinstance(fixed_raw, bool)
            else None
        )
        mean_cpu = float(np.mean(fit_cpu_values)) if fit_cpu_values else None
        groups[key] = {
            "dataset": dataset_name,
            "model": model_name,
            "deterministic": deterministic,
            "trial_count": len(rows),
            "seeds": sorted(int(row["seed"]) for row in rows),
            "metrics": estimates,
            "repetition_plan": repetition,
            "fit_cost": {
                "wall_seconds": aggregate_repeated_estimates(
                    fit_wall_values, confidence_level=confidence
                ),
                "cpu_seconds": aggregate_repeated_estimates(
                    fit_cpu_values, confidence_level=confidence
                ),
                "projected_fit_cpu_hours_at_recommended_trials": (
                    None
                    if mean_cpu is None or recommended is None
                    else mean_cpu * recommended / 3600.0
                ),
                "projected_fit_cpu_hours_at_fixed_execution_trials": (
                    None
                    if mean_cpu is None or fixed_trials is None
                    else mean_cpu * fixed_trials / 3600.0
                ),
                "projection_scope": "fit only at pilot support; excludes larger confirmatory caps, preflight, scoring, and bootstrap",
            },
        }

    comparisons: dict[str, object] = {}
    raw_p_values: dict[str, float | None] = {}
    for dataset_name, model_map in sorted(values_by_dataset_model.items()):
        names = sorted(model_map)
        for left_index, left_name in enumerate(names):
            for right_name in names[left_index + 1 :]:
                left_values = model_map[left_name]
                right_values = model_map[right_name]
                key = f"{dataset_name}/{left_name}-vs-{right_name}"
                left_deterministic = bool(
                    _mapping(groups[f"{dataset_name}/{left_name}"], "group").get(
                        "deterministic", False
                    )
                )
                right_deterministic = bool(
                    _mapping(groups[f"{dataset_name}/{right_name}"], "group").get(
                        "deterministic", False
                    )
                )
                comparison = paired_comparison(
                    left_values,
                    right_values,
                    seed=int(statistics.get("comparison_seed", 99173)),
                    monte_carlo_replicates=int(
                        statistics.get("permutation_replicates", 20000)
                    ),
                    left_randomness=("deterministic" if left_deterministic else "seeded"),
                    right_randomness=("deterministic" if right_deterministic else "seeded"),
                )
                comparisons[key] = comparison
                value = comparison.get("p_value")
                raw_p_values[key] = float(value) if isinstance(value, (int, float)) else None
    adjusted = holm_adjust(raw_p_values)
    for key, value in adjusted.items():
        comparison = comparisons[key]
        if isinstance(comparison, dict):
            comparison["holm_adjusted_p_value"] = value

    return {
        "phase": phase,
        "status": "complete",
        "outcome_aggregates_emitted": True,
        "primary_metric": primary_metric,
        "confidence_level": confidence,
        "groups": groups,
        "paired_comparisons": comparisons,
        "multiplicity_control": "Holm family-wise adjustment within generated report",
    }


def environment_manifest() -> dict[str, object]:
    package_versions: dict[str, str | None] = {}
    for distribution in ("numpy", "keras", "torch"):
        try:
            package_versions[distribution] = importlib.metadata.version(distribution)
        except importlib.metadata.PackageNotFoundError:
            package_versions[distribution] = None
    manifest: dict[str, object] = {
        "python": sys.version,
        "python_executable": sys.executable,
        "platform": platform.platform(),
        "machine": platform.machine(),
        "processor": platform.processor(),
        "logical_cpu_count": os.cpu_count(),
        "numpy": np.__version__,
        "package_versions": package_versions,
        "numpy_build_configuration": repr(getattr(np.__config__, "CONFIG", "unavailable")),
        "keras_backend": os.environ.get("KERAS_BACKEND", "unspecified"),
        "python_hash_seed": os.environ.get("PYTHONHASHSEED", "unspecified"),
        "locale_encoding": locale.getencoding(),
        "thread_environment": {
            name: os.environ.get(name, "unspecified")
            for name in (
                "OMP_NUM_THREADS",
                "MKL_NUM_THREADS",
                "OPENBLAS_NUM_THREADS",
                "NUMEXPR_NUM_THREADS",
            )
        },
    }
    try:
        import torch

        manifest["torch"] = torch.__version__
        manifest["torch_cuda_available"] = bool(torch.cuda.is_available())
        manifest["torch_thread_count"] = int(torch.get_num_threads())
        manifest["torch_deterministic_algorithms"] = bool(
            torch.are_deterministic_algorithms_enabled()
        )
        manifest["torch_cudnn_version"] = torch.backends.cudnn.version()
        manifest["torch_cudnn_deterministic"] = bool(torch.backends.cudnn.deterministic)
        manifest["torch_cudnn_benchmark"] = bool(torch.backends.cudnn.benchmark)
        manifest["accelerators"] = [
            torch.cuda.get_device_name(index)
            for index in range(torch.cuda.device_count())
        ]
    except ImportError:
        manifest["torch"] = None
    return manifest


def _validation_role_partitions(
    validation: PreparedPartition,
    config: Mapping[str, object],
) -> tuple[PreparedPartition, PreparedPartition, dict[str, object]]:
    """Separate model selection from threshold calibration without cluster leakage.

    V1 artifacts retain their historical shared-validation behavior and are
    explicitly marked non-independent.  V2 assigns whole declared dependence
    clusters to one role using a stable, predeclared hash priority.  Labels do
    not participate in the assignment or its identity.
    """

    if not _is_v2(config):
        shared_units = sorted(set(validation.unit_ids))
        shared_clusters = sorted(
            set(validation.cluster_ids or validation.unit_ids)
        )
        return validation, validation, {
            "passed": True,
            "method": "legacy-shared-validation-v1",
            "independent_roles": False,
            "early_stopping_units": len(shared_units),
            "calibration_units": len(shared_units),
            "early_stopping_windows": len(validation.window_ids),
            "calibration_windows": len(validation.window_ids),
            "shared_unit_count": len(shared_units),
            "shared_cluster_count": len(shared_clusters),
            "limitation": (
                "The v1 model-selection and threshold-calibration roles share "
                "validation observations and remain exploratory only."
            ),
        }

    protocol = _mapping(config.get("validation_protocol"), "validation_protocol")
    fraction = float(protocol.get("early_stopping_fraction"))
    seed = protocol.get("split_seed")
    minimum_units = protocol.get("minimum_units_per_role")
    if not math.isfinite(fraction) or not 0.0 < fraction < 1.0:
        raise ValueError("early_stopping_fraction must be finite and between zero and one")
    _validate_uint32_seed(seed, "validation_protocol.split_seed")
    if (
        not isinstance(minimum_units, int)
        or isinstance(minimum_units, bool)
        or minimum_units < 1
    ):
        raise ValueError("minimum_units_per_role must be a positive integer")
    if validation.labels.size != len(validation.window_ids):
        raise ValueError("validation labels and window identities are misaligned")
    if validation.labels.size == 0 or np.any(validation.labels != 0):
        raise ValueError(
            "v2 early-stopping and threshold-calibration validation must be non-empty and normal-only"
        )

    clusters = validation.cluster_ids or validation.unit_ids
    if len(clusters) != len(validation.window_ids):
        raise ValueError("validation cluster identities and windows are misaligned")
    if any(not str(cluster) for cluster in clusters):
        raise ValueError("validation cluster identities must be non-empty")

    unit_cluster: dict[str, str] = {}
    for unit_id, cluster_id in zip(validation.unit_ids, clusters):
        prior = unit_cluster.setdefault(str(unit_id), str(cluster_id))
        if prior != str(cluster_id):
            raise ValueError(
                f"validation unit {unit_id!r} spans multiple dependence clusters"
            )
    cluster_units: dict[str, set[str]] = {}
    for unit_id, cluster_id in unit_cluster.items():
        cluster_units.setdefault(cluster_id, set()).add(unit_id)
    if len(cluster_units) < 2:
        raise ValueError(
            "v2 validation-role separation requires at least two independent clusters"
        )

    ordered_clusters = sorted(
        cluster_units,
        key=lambda cluster_id: (
            sha256(f"{seed}:{cluster_id}".encode("utf-8")).hexdigest(),
            cluster_id,
        ),
    )
    total_units = len(unit_cluster)
    candidates: list[tuple[float, int, int, int]] = []
    for boundary in range(1, len(ordered_clusters)):
        stopping_units = sum(
            len(cluster_units[cluster_id])
            for cluster_id in ordered_clusters[:boundary]
        )
        calibration_units = total_units - stopping_units
        if stopping_units >= minimum_units and calibration_units >= minimum_units:
            candidates.append(
                (
                    abs(stopping_units - fraction * total_units),
                    boundary,
                    stopping_units,
                    calibration_units,
                )
            )
    if not candidates:
        raise ValueError(
            "v2 validation clusters cannot satisfy minimum_units_per_role without dependence leakage"
        )
    _, boundary, stopping_unit_count, calibration_unit_count = min(candidates)
    stopping_clusters = set(ordered_clusters[:boundary])
    calibration_clusters = set(ordered_clusters[boundary:])
    stopping_indices = [
        index
        for index, cluster_id in enumerate(clusters)
        if str(cluster_id) in stopping_clusters
    ]
    calibration_indices = [
        index
        for index, cluster_id in enumerate(clusters)
        if str(cluster_id) in calibration_clusters
    ]
    stopping = _subset_prepared_partition(validation, stopping_indices)
    calibration = _subset_prepared_partition(validation, calibration_indices)
    stopping_units = sorted(set(stopping.unit_ids))
    calibration_units = sorted(set(calibration.unit_ids))
    if set(stopping_units) & set(calibration_units):
        raise RuntimeError("validation role split leaked a unit across roles")
    if stopping_clusters & calibration_clusters:
        raise RuntimeError("validation role split leaked a dependence cluster across roles")

    stopping_identity = canonical_json_hash(
        {
            "role": "early-stopping",
            "units": stopping_units,
            "clusters": sorted(stopping_clusters),
            "windows": sorted(stopping.window_ids),
        }
    )
    calibration_identity = canonical_json_hash(
        {
            "role": "threshold-calibration",
            "units": calibration_units,
            "clusters": sorted(calibration_clusters),
            "windows": sorted(calibration.window_ids),
        }
    )
    audit: dict[str, object] = {
        "passed": True,
        "method": "stable-disjoint-cluster-priority-v1",
        "independent_roles": True,
        "split_seed": seed,
        "configured_early_stopping_fraction": fraction,
        "minimum_units_per_role": minimum_units,
        "early_stopping_units": stopping_unit_count,
        "calibration_units": calibration_unit_count,
        "early_stopping_windows": len(stopping.window_ids),
        "calibration_windows": len(calibration.window_ids),
        "early_stopping_clusters": len(stopping_clusters),
        "calibration_clusters": len(calibration_clusters),
        "shared_unit_count": 0,
        "shared_cluster_count": 0,
        "early_stopping_identity": stopping_identity,
        "calibration_identity": calibration_identity,
        "assignment_identity": canonical_json_hash(
            {
                "method": "stable-disjoint-cluster-priority-v1",
                "seed": seed,
                "fraction": fraction,
                "minimum_units_per_role": minimum_units,
                "early_stopping_identity": stopping_identity,
                "calibration_identity": calibration_identity,
            }
        ),
    }
    return stopping, calibration, audit


def _subset_prepared_partition(
    partition: PreparedPartition, indices: Sequence[int]
) -> PreparedPartition:
    normalized = np.asarray(tuple(int(index) for index in indices), dtype=np.int64)
    if normalized.size == 0:
        raise ValueError("prepared partition subset cannot be empty")
    clusters = partition.cluster_ids or partition.unit_ids
    origins = partition.evidence_origins or tuple(
        "test_fixture" for _ in partition.window_ids
    )
    return PreparedPartition(
        x=partition.x[normalized],
        window_ids=tuple(partition.window_ids[index] for index in normalized),
        unit_ids=tuple(partition.unit_ids[index] for index in normalized),
        labels=partition.labels[normalized],
        class_names=tuple(partition.class_names[index] for index in normalized),
        event_ids=tuple(partition.event_ids[index] for index in normalized),
        cluster_ids=tuple(clusters[index] for index in normalized),
        evidence_origins=tuple(origins[index] for index in normalized),
    )


def _execute_cell(
    config: Mapping[str, object],
    prepared: PreparedDataset,
    *,
    descriptor: Mapping[str, object],
    model_name: str,
    model_config: Mapping[str, object],
    seed: int,
    predictions_dir: Path,
    numeric_authority: Mapping[str, object],
    project_root: Path,
) -> tuple[dict[str, object], list[dict[str, object]]]:
    train = prepared.partitions["train"]
    validation = prepared.partitions["validation"]
    test = prepared.partitions["test"]
    early_stopping_validation, calibration_validation, validation_roles = (
        _validation_role_partitions(validation, config)
    )
    detector, fit_record = fit_detector(
        model_name,
        modality=prepared.dataset.modality,
        train_x=train.x,
        validation_x=early_stopping_validation.x,
        seed=seed,
        config=model_config,
        categorical_vocabulary_size=(
            len(prepared.preprocessing.vocabulary)
            if prepared.dataset.modality == "categorical-syscall"
            else None
        ),
    )
    fit_record_payload = fit_record.to_dict()
    model_identity = fit_record_payload.get("model_identity")
    if not isinstance(model_identity, str) or not model_identity:
        if _is_v2(config):
            raise RuntimeError("v2 model fit did not expose an immutable model identity")
        model_identity = canonical_json_hash(
            {
                "legacy_fit_record": fit_record_payload,
                "model": model_name,
                "seed": int(seed),
            }
        )
    validation_scores, validation_timing = _score_with_timing(
        detector, calibration_validation.x
    )
    aggregation = prepared.windowed.aggregation
    validation_units = aggregate_window_scores(
        calibration_validation, validation_scores, method=aggregation
    )
    statistical = _mapping(config.get("statistical_protocol"), "statistical_protocol")
    threshold_config = _mapping(statistical.get("threshold"), "threshold")
    if str(
        threshold_config.get("direction", "higher-is-more-anomalous")
    ) != "higher-is-more-anomalous":
        raise ValueError("Academic threshold direction must be higher-is-more-anomalous.")
    expected_calibration_partition = (
        "validation-calibration" if _is_v2(config) else "validation"
    )
    if (
        str(
            threshold_config.get(
                "calibration_partition", expected_calibration_partition
            )
        )
        != expected_calibration_partition
    ):
        raise ValueError(
            "Academic threshold calibration_partition must be "
            f"{expected_calibration_partition!r}."
        )
    sensitivity_quantiles = threshold_config.get(
        "sensitivity_normal_quantiles", (0.90, 0.95, 0.975, 0.99, 0.995)
    )
    if not isinstance(sensitivity_quantiles, (list, tuple)):
        raise ValueError("sensitivity_normal_quantiles must be an array")
    calibration = calibrate_threshold(
        validation_units["scores"],
        validation_units["labels"],
        method=str(threshold_config.get("method", "target-fpr")),
        quantile=float(threshold_config.get("normal_quantile", 0.99)),
        target_fpr=float(threshold_config.get("target_fpr", 0.01)),
        sensitivity_quantiles=tuple(float(value) for value in sensitivity_quantiles),
    )
    # The operating point is now frozen. The blind test tensor is not scored
    # until after this lifecycle boundary has been materialized in memory.
    test_gate_identity = canonical_json_hash(
        {
            "preprocessing_identity": prepared.preprocessing.identity,
            "model_identity": model_identity,
            "calibration_identity": calibration.identity,
            "model_fit_window_identity": prepared.windowed.model_fit_identity,
            "early_stopping_role_identity": validation_roles.get(
                "early_stopping_identity"
            ),
            "calibration_role_identity": validation_roles.get(
                "calibration_identity"
            ),
            "test_truth_used": False,
        }
    )
    test_scores, test_timing = _score_with_timing(detector, test.x)
    test_units = aggregate_window_scores(test, test_scores, method=aggregation)
    scores = np.asarray(test_units["scores"], dtype=np.float64)
    truths = np.asarray(test_units["labels"], dtype=np.int64)
    predictions = (scores >= calibration.value).astype(np.int64)
    classes = tuple(str(value) for value in test_units["class_names"])
    events = tuple(tuple(str(item) for item in value) for value in test_units["event_ids"])

    operating = binary_operating_metrics(scores, truths, calibration.value)
    ranking = ranking_metrics(scores, truths)
    bootstrap = bootstrap_confidence_intervals(
        scores,
        truths,
        threshold=calibration.value,
        replicates=int(statistical.get("bootstrap_replicates", 2000)),
        confidence_level=float(statistical.get("confidence_level", 0.95)),
        seed=int(seed) + int(statistical.get("bootstrap_seed_offset", 1000003)),
        cluster_ids=tuple(str(value) for value in test_units["cluster_ids"]),
        minimum_clusters=int(statistical.get("minimum_bootstrap_clusters", 2)),
        minimum_class_carrying_clusters=int(
            statistical["minimum_class_carrying_clusters"]
        ) if _is_v2(config) else None,
        minimum_valid_replicates=int(
            statistical["minimum_valid_bootstrap_replicates"]
        ) if _is_v2(config) else None,
        minimum_valid_fraction=float(
            statistical["minimum_valid_bootstrap_fraction"]
        ) if _is_v2(config) else None,
    )
    predictions_path = predictions_dir / f"{descriptor['cell_id']}.jsonl"
    calibration_rows = [
        {
            "role": "validation-calibration",
            "unit_id": unit_id,
            "truth": int(truth),
            "class_name": class_name,
            "score": float(score),
            "window_count": int(window_count),
            "event_ids": list(event_ids),
            "resampling_cluster_id": cluster_id,
            "evidence_origin": evidence_origin,
            "cell_identity": descriptor["cell_identity"],
            "phase": descriptor["phase"],
        }
        for unit_id, truth, class_name, score, window_count, event_ids, cluster_id, evidence_origin in zip(
            validation_units["unit_ids"],
            np.asarray(validation_units["labels"], dtype=np.int64).tolist(),
            tuple(str(value) for value in validation_units["class_names"]),
            np.asarray(validation_units["scores"], dtype=np.float64).tolist(),
            validation_units["window_counts"],
            tuple(
                tuple(str(item) for item in value)
                for value in validation_units["event_ids"]
            ),
            validation_units["cluster_ids"],
            validation_units["evidence_origins"],
        )
    ]
    prediction_rows = [
        {
            "role": "blind-test",
            "unit_id": unit_id,
            "truth": int(truth),
            "class_name": class_name,
            "score": float(score),
            "threshold": float(calibration.value),
            "prediction": int(prediction),
            "window_count": int(window_count),
            "event_ids": list(event_ids),
            "resampling_cluster_id": cluster_id,
            "evidence_origin": evidence_origin,
            "cell_identity": descriptor["cell_identity"],
            "phase": descriptor["phase"],
        }
        for unit_id, truth, class_name, score, prediction, window_count, event_ids, cluster_id, evidence_origin in zip(
            test_units["unit_ids"],
            truths.tolist(),
            classes,
            scores.tolist(),
            predictions.tolist(),
            test_units["window_counts"],
            events,
            test_units["cluster_ids"],
            test_units["evidence_origins"],
        )
    ]
    prediction_payload = _jsonl_bytes(prediction_rows)
    prediction_sha256 = f"sha256:{sha256(prediction_payload).hexdigest()}"
    transaction_id = f"academic-cell-publication:{descriptor['cell_id']}"
    transaction_manifest_path = (
        predictions_dir.parent
        / "transactions"
        / f"{descriptor['cell_id']}.transaction.json"
    )

    cell = {
        "schema_version": "academic-cell-result-v2" if _is_v2(config) else "academic-cell-result-v1",
        **dict(descriptor),
        "status": "complete",
        "completed_at_utc": _utc_now(),
        "dataset": prepared.dataset.name,
        "dataset_protocol": prepared.dataset.protocol,
        "evidence_origin": prepared.dataset.evidence_origin,
        "modality": prepared.dataset.modality,
        "model": model_name,
        "deterministic": bool(model_config.get("deterministic", False)),
        "seed": int(seed),
        "numeric_authority": dict(numeric_authority),
        "numerical_core_identity": _numerical_core_manifest(
            project_root, config
        )["identity"],
        "blind_test_gate": {
            "identity": test_gate_identity,
            "calibration_frozen_before_test_scoring": True,
            "test_truth_used_for_fit_preprocessing_stopping_or_calibration": False,
        },
        "partition_roles": {
            "fit": "train normals only",
            "preprocessing": "train only",
            "early_stopping": (
                "validation-early-stopping only"
                if _is_v2(config)
                else "shared validation (legacy exploratory)"
            ),
            "threshold_calibration": (
                "validation-calibration only"
                if _is_v2(config)
                else "validation only"
            ),
            "final_metrics": "blind test only",
        },
        "validation_role_split": validation_roles,
        "data": _dataset_preflight_record(
            prepared,
            support_check={"passed": True, "issues": []},
        ),
        "model_fit": fit_record_payload,
        "threshold_calibration": calibration.to_dict(),
        "validation_calibration": {
            "unit_support": _binary_support(validation_units["labels"]),
            "score_distribution": score_distribution(
                validation_units["scores"], validation_units["labels"]
            ),
            "raw_rows": calibration_rows,
            "raw_rows_identity": canonical_json_hash(calibration_rows),
        },
        "test": {
            "operating": operating,
            "ranking": ranking,
            "bootstrap_unit_ci": bootstrap,
            "per_attack_class": per_class_detection_metrics(
                scores.tolist(), truths.tolist(), classes, threshold=calibration.value
            ),
            "events": event_metrics(predictions.tolist(), truths.tolist(), events),
            "curves": curve_points(
                scores,
                truths,
                max_points=int(statistical.get("curve_max_points", 201)),
            ),
            "score_distribution": score_distribution(scores, truths),
        },
        "inference_cost": {
            "validation_calibration": validation_timing,
            "test": test_timing,
        },
        "predictions_artifact": {
            "path": str(predictions_path.resolve()),
            "sha256": prediction_sha256,
            "rows": len(prediction_rows),
            "format": "JSON Lines; one independent test unit per row",
        },
        "publication_transaction": {
            "transaction_id": transaction_id,
            "manifest_path": str(transaction_manifest_path.resolve()),
        },
        "raw_evidence_binding": {
            "schema_version": "academic-cell-raw-evidence-v1",
            "calibration_rows_identity": canonical_json_hash(calibration_rows),
            "test_rows_identity": canonical_json_hash(prediction_rows),
        },
    }
    return cell, prediction_rows


def _score_with_timing(detector: object, x: np.ndarray) -> tuple[np.ndarray, dict[str, object]]:
    start = time.perf_counter()
    cpu_start = time.process_time()
    scores = np.asarray(detector.score(x), dtype=np.float64).reshape(-1)  # type: ignore[attr-defined]
    wall = time.perf_counter() - start
    cpu = time.process_time() - cpu_start
    if scores.size != x.shape[0] or not np.all(np.isfinite(scores)):
        raise RuntimeError("Detector returned invalid or non-finite window scores.")
    return scores, {
        "windows": int(scores.size),
        "wall_seconds": float(wall),
        "cpu_seconds": float(cpu),
        "milliseconds_per_window": None if not scores.size else 1000.0 * wall / scores.size,
    }


def _prepare_one_dataset(
    dataset_key: str,
    dataset_config: Mapping[str, object],
    *,
    project_root: Path,
    phase: str,
) -> PreparedDataset:
    cache_key = canonical_json_hash(
        {
            "dataset_key": dataset_key,
            "dataset_config": dict(dataset_config),
            "project_root": str(Path(project_root).resolve()),
            "phase": phase,
        }
    )
    cached = _MEMORY_PREPARED_CACHE.get(cache_key)
    if cached is not None:
        return cached
    dataset = load_academic_dataset(
        dataset_key, dataset_config, project_root=project_root, phase=phase
    )
    window = _mapping(dataset_config.get("window"), f"datasets.{dataset_key}.window")
    windowed = window_dataset(
        dataset,
        sequence_length=int(window.get("sequence_length", 64)),
        stride=int(window.get("stride", 32)),
        max_windows_per_unit=int(window.get("max_windows_per_unit", 4)),
        aggregation=str(window.get("aggregation", "p95")),
    )
    preprocessing = fit_preprocessing(
        dataset,
        windowed,
        clip=float(dataset_config.get("numeric_clip", 10.0)),
    )
    prepared = prepare_dataset_arrays(dataset, windowed, preprocessing)
    _MEMORY_PREPARED_CACHE[cache_key] = prepared
    return prepared


def _dataset_preflight_record(
    prepared: PreparedDataset, *, support_check: Mapping[str, object]
) -> dict[str, object]:
    dataset = prepared.dataset
    unit_ids = [unit.unit_id for unit in dataset.units]
    group_ids = [unit.group_id for unit in dataset.units]
    detector_input_ids = [unit.detector_input_identity for unit in dataset.units]
    detector_input_content_ids = [
        unit.detector_input_content_identity for unit in dataset.units
    ]
    return {
        "dataset_name": dataset.name,
        "dataset_identity": dataset.identity,
        "protocol": dataset.protocol,
        "phase": dataset.phase,
        "modality": dataset.modality,
        "evidence_origin": dataset.evidence_origin,
        "feature_count": len(dataset.feature_names),
        "source_manifest": dataset.source_manifest,
        "selected_unit_identity_manifest": {
            "unit_ids": unit_ids,
            "group_ids": group_ids,
            "detector_input_ids": detector_input_ids,
            "detector_input_content_ids": detector_input_content_ids,
            "identity": canonical_json_hash(
                {
                    "unit_ids": sorted(unit_ids),
                    "group_ids": sorted(group_ids),
                    "detector_input_ids": sorted(detector_input_ids),
                    "detector_input_content_ids": sorted(
                        detector_input_content_ids
                    ),
                }
            ),
        },
        "support": support_summary(dataset),
        "support_gate": dict(support_check),
        "group_leakage_audit": audit_group_leakage(dataset),
        "window_parentage_audit": audit_window_parentage(
            dataset, prepared.windowed.partitions
        ),
        "windowing": {
            "identity": prepared.windowed.identity,
            "training_identity": prepared.windowed.training_identity,
            "model_fit_identity": prepared.windowed.model_fit_identity,
            "sequence_length": prepared.windowed.sequence_length,
            "stride": prepared.windowed.stride,
            "aggregation": prepared.windowed.aggregation,
            "window_count": {
                name: len(prepared.windowed.partitions[name])
                for name in ("train", "validation", "test")
            },
        },
        "preprocessing": prepared.preprocessing.to_dict(),
        "array_shapes": {
            name: list(prepared.partitions[name].x.shape)
            for name in ("train", "validation", "test")
        },
        "array_bytes": {
            name: int(prepared.partitions[name].x.nbytes)
            for name in ("train", "validation", "test")
        },
    }


def _support_check(
    dataset: AcademicDataset, dataset_config: Mapping[str, object], phase: str
) -> dict[str, object]:
    configured = _mapping(
        dataset_config.get("minimum_support", {}), "minimum_support"
    )
    phase_config = configured.get(phase, configured)
    limits = _mapping(phase_config, f"minimum_support.{phase}")
    return validate_academic_support(
        dataset,
        minimum_test_normal=int(limits.get("test_normal", 2)),
        minimum_test_attack=int(limits.get("test_attack", 2)),
    )


def _evidence_origin_check(
    prepared: PreparedDataset,
    dataset_config: Mapping[str, object],
    dataset_key: str,
) -> dict[str, object]:
    strict = "evidence_origin" in dataset_config
    expected = dataset_config.get("evidence_origin", prepared.dataset.evidence_origin)
    observed = {prepared.dataset.evidence_origin}
    observed.update(unit.evidence_origin for unit in prepared.dataset.units)
    for partition in prepared.partitions.values():
        observed.update(partition.evidence_origins)
    reasons: list[str] = []
    if strict and dataset_key in _OFFICIAL_DATASETS and expected != "official_native":
        reasons.append("official benchmark config must declare official_native")
    if strict and observed != {expected}:
        reasons.append(
            f"records expose origins incompatible with the declared origin {expected!r}: "
            f"{sorted(observed)}"
        )
    elif not strict and len(observed) != 1:
        reasons.append(
            f"legacy records do not expose exactly one consistent origin: {sorted(observed)}"
        )
    return {
        "passed": not reasons,
        "expected": expected,
        "observed": sorted(observed),
        "reasons": reasons,
    }


def _observed_phase_disjointness(
    config: Mapping[str, object],
    *,
    project_root: Path,
    phase: str,
    dataset_key: str,
    current_record: Mapping[str, object],
) -> dict[str, object]:
    if not _is_v2(config):
        return {
            "passed": True,
            "status": "not-enforced-for-v1",
            "limitation": "v1 remains exploratory and cannot be promoted",
        }
    configured = _phase_allocation_audit(config)
    configured_dataset = _nested_mapping_value(
        configured, "datasets", dataset_key, "passed"
    )
    if configured_dataset is not True:
        return {"passed": False, "status": "configured-allocation-blocked"}
    if phase == "pilot":
        return {
            "passed": True,
            "status": "configured-disjoint-slice; confirmatory observation pending",
            "configured_allocation_identity": _nested_mapping_value(
                configured, "datasets", dataset_key, "identity"
            ),
        }
    pilot_path = academic_paths(
        config, project_root=project_root, phase="pilot"
    ).phase / "preflight.json"
    if not pilot_path.is_file():
        return {
            "passed": False,
            "status": "pilot-preflight-missing",
            "reason": "confirmatory allocation cannot be opened before authenticated pilot preflight",
        }
    pilot = _read_json(pilot_path)
    if (
        pilot.get("schema_version") != "academic-preflight-v2"
        or pilot.get("config_identity") != config_identity(config)
        or pilot.get("ready") is not True
    ):
        return {
            "passed": False,
            "status": "pilot-preflight-incompatible",
        }
    pilot_manifest = _nested_mapping_value(
        pilot, "datasets", dataset_key, "selected_unit_identity_manifest"
    )
    current_manifest = current_record.get("selected_unit_identity_manifest")
    if not isinstance(pilot_manifest, Mapping) or not isinstance(current_manifest, Mapping):
        return {"passed": False, "status": "selection-manifest-missing"}
    overlaps: dict[str, list[str]] = {}
    for key in (
        "unit_ids",
        "group_ids",
        "detector_input_ids",
        "detector_input_content_ids",
    ):
        if key not in pilot_manifest or key not in current_manifest:
            overlaps[key] = ["missing-manifest-field"]
            continue
        pilot_values = pilot_manifest[key]
        current_values = current_manifest[key]
        if not isinstance(pilot_values, list) or not isinstance(current_values, list):
            overlaps[key] = ["malformed-manifest"]
            continue
        shared = sorted(set(str(value) for value in pilot_values) & set(str(value) for value in current_values))
        if shared:
            overlaps[key] = shared
    return {
        "passed": not overlaps,
        "status": "observed-disjoint" if not overlaps else "observed-overlap",
        "overlap_counts": {key: len(values) for key, values in overlaps.items()},
        "overlap_examples": {key: values[:10] for key, values in overlaps.items()},
        "pilot_manifest_identity": pilot_manifest.get("identity"),
        "current_manifest_identity": current_manifest.get("identity"),
    }


def _cell_descriptor(
    config: Mapping[str, object],
    prepared: PreparedDataset,
    *,
    dataset_key: str,
    model_name: str,
    model_config: Mapping[str, object],
    phase: str,
    seed: int,
    schedule_entry: Mapping[str, object] | None = None,
) -> dict[str, object]:
    validation_role_assignment_identity: object = None
    if _is_v2(config):
        _, _, validation_role_split = _validation_role_partitions(
            prepared.partitions["validation"], config
        )
        validation_role_assignment_identity = validation_role_split.get(
            "assignment_identity"
        )
    payload: dict[str, object] = {
        "runner_protocol": _runner_protocol(config),
        "config_identity": config_identity(config),
        "phase": phase,
        "dataset_key": dataset_key,
        "window_identity": prepared.windowed.identity,
        "model_fit_window_identity": prepared.windowed.model_fit_identity,
        "preprocessing_identity": prepared.preprocessing.identity,
        "model": model_name,
        "model_config": dict(model_config),
        "seed": int(seed),
    }
    if schedule_entry is not None and _is_v2(config):
        payload["seed_position"] = schedule_entry.get("seed_position")
        payload["batch_id"] = schedule_entry.get("batch_id")
        payload["batch_position"] = schedule_entry.get("batch_position")
        payload["schedule_kind"] = schedule_entry.get("schedule_kind")
        payload["schedule_identity"] = schedule_entry.get("schedule_identity")
    if _is_v2(config):
        payload["dataset_model_input_identity"] = prepared.dataset.model_input_identity
        # Model fitting remains truth-blind, but result/resume identity must also
        # bind the exact labels, source hashes, events, and provenance used for
        # evaluation. Otherwise corrected labels could silently resume stale
        # predictions under the same detector-input identity.
        payload["result_dataset_identity"] = prepared.dataset.identity
        payload["evidence_origin"] = prepared.dataset.evidence_origin
        payload["validation_role_assignment_identity"] = (
            validation_role_assignment_identity
        )
    else:
        payload["dataset_identity"] = prepared.dataset.identity
    identity = canonical_json_hash(payload)
    safe_dataset = "".join(character if character.isalnum() else "-" for character in dataset_key)
    safe_model = "".join(character if character.isalnum() else "-" for character in model_name)
    descriptor = {
        "cell_id": f"{safe_dataset}__{safe_model}__seed-{seed}__{identity[-12:]}",
        "cell_identity": identity,
        "runner_protocol": _runner_protocol(config),
        "config_identity": config_identity(config),
        "dataset_key": dataset_key,
        "dataset": dataset_key,
        "model": model_name,
        "seed": int(seed),
        "deterministic": bool(model_config.get("deterministic", False)),
        "phase": phase,
    }
    if schedule_entry is not None and _is_v2(config):
        descriptor.update(
            {
                "seed_position": schedule_entry.get("seed_position"),
                "batch_id": schedule_entry.get("batch_id"),
                "batch_position": schedule_entry.get("batch_position"),
                "schedule_kind": schedule_entry.get("schedule_kind"),
                "schedule_identity": schedule_entry.get("schedule_identity"),
            }
        )
    if _is_v2(config):
        descriptor["result_dataset_identity"] = prepared.dataset.identity
        descriptor["validation_role_assignment_identity"] = (
            validation_role_assignment_identity
        )
    return descriptor


def _initialize_evidence(
    config: Mapping[str, object], *, project_root: Path, phase: str
) -> AcademicPaths:
    if _is_v2(config):
        validate_v2_numeric_schema(config)
        _validate_v2_budget(config)
        _validate_v2_execution_schedule(config)
    paths = academic_paths(config, project_root=project_root, phase=phase)
    if paths.root.is_symlink() or paths.root.parent.is_symlink():
        raise RuntimeError("academic experiment root and identity directory must not be symlinks")
    paths.root.mkdir(parents=True, exist_ok=True)
    resolved_root = paths.root.resolve()
    for path in (
        paths.phase,
        paths.cells,
        paths.predictions,
        paths.transactions,
        paths.reports,
    ):
        if path.is_symlink() or not path.resolve().is_relative_to(resolved_root):
            raise RuntimeError(f"unsafe academic artifact directory: {path}")
        path.mkdir(parents=True, exist_ok=True)
        if path.is_symlink() or not path.resolve().is_relative_to(resolved_root):
            raise RuntimeError(f"unsafe academic artifact directory: {path}")
    if _is_v2(config):
        _recover_cell_transactions(paths)
    _write_json(paths.root / "frozen-config.json", dict(config), immutable=True)
    _write_json(
        paths.root / "numerical-core-manifest.json",
        _numerical_core_manifest(project_root, config),
        immutable=True,
    )
    planning_error: str | None = None
    try:
        logical_cells = _logical_plan(config, phase, project_root=project_root)
    except ValueError as exc:
        if not (_is_v2(config) and phase == "confirmatory"):
            raise
        logical_cells = []
        planning_error = str(exc)
    planned_matrix: dict[str, object] = {
        "schema_version": "academic-logical-plan-v2" if _is_v2(config) else "academic-logical-plan-v1",
        "config_identity": config_identity(config),
        "phase": phase,
        "cells": logical_cells,
        "planning_error": planning_error,
    }
    if _is_v2(config):
        planned_matrix.update(
            {
                "schedule_identity": _phase_schedule_identity(config, phase),
                "execution_schedule_adaptive": False,
                "trial_definition": "one independent model fit at one frozen seed",
                "excluded_trial_surrogates": [
                    "epochs",
                    "windows",
                    "bootstrap replicates",
                    "cycles",
                ],
            }
        )
    _write_json(paths.phase / "planned-matrix.json", planned_matrix, immutable=True)
    if _is_v2(config) and phase == "confirmatory":
        ledger_path = paths.phase / "confirmatory-batch-ledger.json"
        prior_phase_state = any(
            candidate.exists()
            for candidate in (
                paths.phase / "preflight.json",
                paths.phase / "run-summary.json",
                paths.phase / "failures",
                paths.phase / "batches",
            )
        ) or any(paths.cells.glob("*.json"))
        if ledger_path.is_symlink():
            raise RuntimeError("confirmatory batch ledger must not be a symlink")
        if not ledger_path.exists() and prior_phase_state:
            raise RuntimeError(
                "immutable confirmatory batch ledger is missing from an existing phase"
            )
        _write_json(
            ledger_path,
            confirmatory_batch_ledger(config),
            immutable=True,
        )
    _write_json(
        paths.root / "provenance.json",
        {
            "schema_version": "academic-provenance-v2" if _is_v2(config) else "academic-provenance-v1",
            "runner_protocol": _runner_protocol(config),
            "config_identity": config_identity(config),
            "environment": environment_manifest(),
        },
        immutable=True,
    )
    return paths


def _dataset_configs(config: Mapping[str, object]) -> dict[str, Mapping[str, object]]:
    raw = _mapping(config.get("datasets"), "datasets")
    return {str(key): _mapping(value, f"datasets.{key}") for key, value in raw.items()}


def _model_configs(dataset_config: Mapping[str, object]) -> dict[str, Mapping[str, object]]:
    raw = _mapping(dataset_config.get("models"), "models")
    if not raw:
        raise ValueError("Each dataset must declare at least one model.")
    return {str(key): _mapping(value, f"models.{key}") for key, value in raw.items()}


def _phase_schedule_identity(config: Mapping[str, object], phase: str) -> str:
    payload: dict[str, object] = {
        "config_identity": config_identity(config),
        "phase": phase,
        "seeds": list(config[f"{phase}_seeds"]),  # type: ignore[index]
    }
    if _is_v2(config) and phase == "confirmatory":
        payload["execution_protocol"] = config.get("execution_protocol")
        payload["batches"] = [
            list(batch) for batch in _confirmatory_seed_batches(config)
        ]
    return canonical_json_hash(payload)


def _schedule_entries(
    config: Mapping[str, object],
    model_config: Mapping[str, object],
    phase: str,
) -> tuple[dict[str, object], ...]:
    """Return the immutable trial ledger for one dataset/model family."""

    if _is_v2(config):
        # Callers may supply an in-memory mapping rather than one returned by
        # load_academic_config.  Revalidate the complete frozen schedule at the
        # point where it becomes executable.
        _validate_v2_execution_schedule(config)
    seeds = tuple(int(value) for value in config[f"{phase}_seeds"])  # type: ignore[index]
    schedule_identity = _phase_schedule_identity(config, phase)
    deterministic = bool(model_config.get("deterministic", False))
    if deterministic:
        return (
            {
                "seed": seeds[0],
                "seed_position": 1,
                "batch_id": (
                    "batch-01" if _is_v2(config) and phase == "confirmatory" else None
                ),
                "batch_position": None,
                "schedule_kind": "deterministic-singleton",
                "schedule_identity": schedule_identity,
            },
        )
    if not (_is_v2(config) and phase == "confirmatory"):
        return tuple(
            {
                "seed": seed,
                "seed_position": index,
                "batch_id": None,
                "batch_position": None,
                "schedule_kind": "independent-seed-trials",
                "schedule_identity": schedule_identity,
            }
            for index, seed in enumerate(seeds, start=1)
        )

    entries: list[dict[str, object]] = []
    global_position = 0
    for batch_number, batch_seeds in enumerate(
        _confirmatory_seed_batches(config), start=1
    ):
        batch_id = f"batch-{batch_number:02d}"
        for batch_position, seed in enumerate(batch_seeds, start=1):
            global_position += 1
            entries.append(
                {
                    "seed": int(seed),
                    "seed_position": global_position,
                    "batch_id": batch_id,
                    "batch_position": batch_position,
                    "schedule_kind": "fixed-nonadaptive-confirmatory-seeds",
                    "schedule_identity": schedule_identity,
                }
            )
    return tuple(entries)


def _model_seeds(
    config: Mapping[str, object],
    model_config: Mapping[str, object],
    phase: str,
    *,
    dataset_name: str = "",
    model_name: str = "",
    project_root: Path | None = None,
) -> tuple[int, ...]:
    del dataset_name, model_name, project_root
    return tuple(
        int(entry["seed"])
        for entry in _schedule_entries(config, model_config, phase)
    )


def _logical_plan(
    config: Mapping[str, object], phase: str, *, project_root: Path | None = None
) -> list[dict[str, object]]:
    rows: list[dict[str, object]] = []
    for dataset_name, dataset_config in _dataset_configs(config).items():
        for model_name, model_config in _model_configs(dataset_config).items():
            for schedule_entry in _schedule_entries(config, model_config, phase):
                rows.append(
                    {
                        "dataset": dataset_name,
                        "model": model_name,
                        **schedule_entry,
                        "deterministic": bool(model_config.get("deterministic", False)),
                    }
                )
    return rows


def _filtered_logical_plan(
    config: Mapping[str, object],
    phase: str,
    *,
    project_root: Path,
    dataset_filter: set[str],
    model_filter: set[str],
) -> list[dict[str, object]]:
    return [
        row
        for row in _logical_plan(config, phase, project_root=project_root)
        if (not dataset_filter or row["dataset"] in dataset_filter)
        and (not model_filter or row["model"] in model_filter)
    ]


def _provisional_filtered_logical_plan(
    config: Mapping[str, object],
    phase: str,
    *,
    dataset_filter: set[str],
    model_filter: set[str],
) -> list[dict[str, object]]:
    """Upper-bound cells used only to materialize failures when planning is blocked."""

    rows: list[dict[str, object]] = []
    for dataset_name, dataset_config in _dataset_configs(config).items():
        if dataset_filter and dataset_name not in dataset_filter:
            continue
        for model_name, model_config in _model_configs(dataset_config).items():
            if model_filter and model_name not in model_filter:
                continue
            for schedule_entry in _schedule_entries(config, model_config, phase):
                rows.append(
                    {
                        "dataset": dataset_name,
                        "model": model_name,
                        **schedule_entry,
                        "deterministic": bool(model_config.get("deterministic", False)),
                        "planning_status": "provisional-failure-boundary-only",
                    }
                )
    return rows


def _numerical_core_manifest(
    project_root: Path, config: Mapping[str, object]
) -> dict[str, object]:
    module_root = Path(__file__).resolve().parent
    code_root = module_root.parents[3]
    sources = (
        module_root / "academic_numeric_schema.py",
        module_root / "academic_protocol.py",
        module_root / "academic_metrics.py",
        module_root / "academic_models.py",
        module_root / "benchmarks" / "base.py",
        module_root / "benchmarks" / "adfa_ld.py",
        module_root / "benchmarks" / "lid_ds_2021.py",
        module_root / "models" / "base.py",
        module_root / "models" / "lstm_classifier.py",
        module_root / "academic_runner.py",
        module_root / "academic_report.py",
        code_root / "scripts" / "run_academic_experiments.py",
        code_root
        / "src"
        / "parallel_truth_fingerprint"
        / "contracts"
        / "semantic_vocabulary.py",
        code_root
        / "src"
        / "parallel_truth_fingerprint"
        / "contracts"
        / "source_catalog.py",
        code_root
        / "src"
        / "parallel_truth_fingerprint"
        / "contracts"
        / "parameter_evidence.py",
        code_root
        / "src"
        / "parallel_truth_fingerprint"
        / "evidence"
        / "parameter_evidence.py",
        code_root
        / "src"
        / "parallel_truth_fingerprint"
        / "evidence"
        / "source_catalog.py",
        code_root
        / "src"
        / "parallel_truth_fingerprint"
        / "evidence"
        / "hai_adapter.py",
    )
    resolved_root = code_root.resolve()
    files: dict[str, str] = {}
    for path in sources:
        resolved = path.resolve()
        if not resolved.is_file():
            raise ValueError(f"Numerical-core source is missing: {resolved}")
        try:
            name = resolved.relative_to(resolved_root).as_posix()
        except ValueError:
            name = str(resolved)
        files[name] = file_sha256(resolved)
    environment = environment_manifest()
    identity = canonical_json_hash(
        {
            "runner_protocol": _runner_protocol(config),
            "config_identity": config_identity(config),
            "environment": environment,
            "files": files,
        }
    )
    return {
        "schema_version": "academic-numerical-core-v2" if _is_v2(config) else "academic-numerical-core-v1",
        "runner_protocol": _runner_protocol(config),
        "config_identity": config_identity(config),
        "environment": environment,
        "files": files,
        "identity": identity,
    }


def _legacy_admissibility(
    config: Mapping[str, object], project_root: Path
) -> dict[str, object]:
    configured = config.get("legacy_report")
    if not configured:
        return {
            "classification": "missing",
            "admissible_for_confirmatory_claims": False,
            "reason": "no legacy report declared",
        }
    path = Path(str(configured))
    if not path.is_absolute():
        path = Path(project_root) / path
    if not path.is_file():
        return {
            "path": str(path.resolve()),
            "classification": "missing",
            "admissible_for_confirmatory_claims": False,
            "reason": "declared legacy report does not exist",
        }
    text = path.read_text(encoding="utf-8")
    champion_rows = sum(
        1
        for line in text.splitlines()
        if line.startswith("|") and "run-" in line and "---" not in line
    )
    return {
        "path": str(path.resolve()),
        "sha256": file_sha256(path),
        "classification": "integration-smoke",
        "admissible_for_confirmatory_claims": False,
        "champion_row_count": champion_rows,
        "reasons": [
            "outcome-selected champion rows instead of a predeclared repeated matrix",
            "no validation-only anomaly threshold evidence",
            "no independent-trial dispersion or unit-level confidence interval",
        ],
    }


def _computational_load(
    config: Mapping[str, object],
    *,
    dataset_results: Mapping[str, object],
    paths: AcademicPaths,
    phase: str,
    project_root: Path,
    current_preflight_cpu_seconds: float,
) -> dict[str, object]:
    rows: list[dict[str, object]] = []
    planning_errors: list[str] = []
    for dataset_name, dataset_config in _dataset_configs(config).items():
        record = dataset_results.get(dataset_name)
        counts = {
            partition: int(
                _nested_mapping_value(record, "windowing", "window_count", partition) or 0
            )
            for partition in ("train", "validation", "test")
        }
        early_stopping_windows = _nested_mapping_value(
            record, "validation_role_split", "early_stopping_windows"
        )
        calibration_windows = _nested_mapping_value(
            record, "validation_role_split", "calibration_windows"
        )
        if not isinstance(early_stopping_windows, int) or isinstance(
            early_stopping_windows, bool
        ):
            early_stopping_windows = counts["validation"]
        if not isinstance(calibration_windows, int) or isinstance(
            calibration_windows, bool
        ):
            calibration_windows = counts["validation"]
        for model_name, model_config in _model_configs(dataset_config).items():
            try:
                trial_count = len(
                    _model_seeds(
                        config,
                        model_config,
                        phase,
                        dataset_name=dataset_name,
                        model_name=model_name,
                        project_root=project_root,
                    )
                )
            except ValueError as exc:
                if bool(model_config.get("deterministic", False)):
                    trial_count = 1
                else:
                    trial_count = 0
                    planning_errors.append(str(exc))
            rows.append(
                {
                    "dataset": dataset_name,
                    "model": model_name,
                    "trials": trial_count,
                    "train_windows": counts["train"],
                    "validation_windows": counts["validation"],
                    "early_stopping_windows": early_stopping_windows,
                    "calibration_windows": calibration_windows,
                    "test_windows": counts["test"],
                    "epochs_per_trial": int(model_config.get("epochs", 0)),
                    "fit_projection_basis": (
                        "cpu-per-executed-epoch-per-train-plus-early-stopping-window"
                        if int(model_config.get("epochs", 0)) > 0
                        else "cpu-per-train-window"
                    ),
                }
            )
    observed_cells = load_completed_cells(paths.root / "pilot")
    projected_fit = 0.0
    projected_inference = 0.0
    projected_families = 0
    for row in rows:
        matching = [
            cell
            for cell in observed_cells
            if cell.get("dataset") == row["dataset"] and cell.get("model") == row["model"]
        ]
        fit_rates: list[float] = []
        inference_rates: list[float] = []
        for cell in matching:
            fit_cpu = _nested_mapping_value(cell, "model_fit", "fit_cpu_seconds")
            pilot_train = _nested_mapping_value(
                cell, "data", "windowing", "window_count", "train"
            )
            pilot_early_stopping = _nested_mapping_value(
                cell, "validation_role_split", "early_stopping_windows"
            )
            pilot_calibration = _nested_mapping_value(
                cell, "validation_role_split", "calibration_windows"
            )
            epochs_executed = _nested_mapping_value(
                cell, "model_fit", "epochs_executed"
            )
            validation_cpu = _nested_mapping_value(
                cell,
                "inference_cost",
                "validation_calibration",
                "cpu_seconds",
            )
            if validation_cpu is None:
                validation_cpu = _nested_mapping_value(
                    cell, "inference_cost", "validation", "cpu_seconds"
                )
            test_cpu = _nested_mapping_value(cell, "inference_cost", "test", "cpu_seconds")
            pilot_validation = _nested_mapping_value(
                cell, "data", "windowing", "window_count", "validation"
            )
            pilot_test = _nested_mapping_value(
                cell, "data", "windowing", "window_count", "test"
            )
            if not isinstance(pilot_early_stopping, (int, float)) or isinstance(
                pilot_early_stopping, bool
            ):
                pilot_early_stopping = pilot_validation
            if not isinstance(pilot_calibration, (int, float)) or isinstance(
                pilot_calibration, bool
            ):
                pilot_calibration = pilot_validation
            recurrent_fit = int(row["epochs_per_trial"]) > 0
            fit_input_windows = 0.0
            if isinstance(pilot_train, (int, float)) and not isinstance(
                pilot_train, bool
            ):
                fit_input_windows = float(pilot_train)
                if (
                    recurrent_fit
                    and isinstance(pilot_early_stopping, (int, float))
                    and not isinstance(pilot_early_stopping, bool)
                ):
                    fit_input_windows += float(pilot_early_stopping)
            executed_epochs = (
                int(epochs_executed)
                if recurrent_fit
                and isinstance(epochs_executed, int)
                and not isinstance(epochs_executed, bool)
                and epochs_executed > 0
                else 1
            )
            if isinstance(fit_cpu, (int, float)) and fit_input_windows > 0:
                fit_rates.append(
                    float(fit_cpu) / (fit_input_windows * executed_epochs)
                )
            if (
                isinstance(validation_cpu, (int, float))
                and isinstance(test_cpu, (int, float))
                and isinstance(pilot_calibration, (int, float))
                and isinstance(pilot_test, (int, float))
                and float(pilot_calibration) + float(pilot_test) > 0
            ):
                inference_rates.append(
                    (float(validation_cpu) + float(test_cpu))
                    / (float(pilot_calibration) + float(pilot_test))
                )
        if fit_rates and inference_rates and int(row["trials"]) > 0:
            epoch_scale = max(int(row["epochs_per_trial"]), 1)
            projected_fit_windows = int(row["train_windows"])
            if int(row["epochs_per_trial"]) > 0:
                projected_fit_windows += int(row["early_stopping_windows"])
            projected_fit += (
                float(np.mean(fit_rates))
                * projected_fit_windows
                * epoch_scale
                * int(row["trials"])
            )
            projected_inference += (
                float(np.mean(inference_rates))
                * (int(row["calibration_windows"]) + int(row["test_windows"]))
                * int(row["trials"])
            )
            projected_families += 1
    pilot_summary_path = paths.root / "pilot" / "run-summary.json"
    pilot_preflight_path = paths.root / "pilot" / "preflight.json"
    pilot_summary = _read_json(pilot_summary_path) if pilot_summary_path.is_file() else {}
    pilot_preflight = _read_json(pilot_preflight_path) if pilot_preflight_path.is_file() else {}
    observed_total = pilot_summary.get(
        "evidence_generation_cpu_seconds_cumulative",
        pilot_summary.get("elapsed_cpu_seconds"),
    )
    observed_preflight = pilot_preflight.get(
        "representative_elapsed_cpu_seconds",
        pilot_preflight.get("elapsed_cpu_seconds"),
    )
    known_pilot_components = 0.0
    for cell in observed_cells:
        component_paths = [
            ("model_fit", "fit_cpu_seconds"),
            ("inference_cost", "test", "cpu_seconds"),
        ]
        validation_component = _nested_mapping_value(
            cell,
            "inference_cost",
            "validation_calibration",
            "cpu_seconds",
        )
        if validation_component is None:
            component_paths.append(("inference_cost", "validation", "cpu_seconds"))
        else:
            component_paths.append(
                ("inference_cost", "validation_calibration", "cpu_seconds")
            )
        for path in component_paths:
            value = _nested_mapping_value(cell, *path)
            if isinstance(value, (int, float)):
                known_pilot_components += float(value)
    pilot_overhead = (
        max(
            float(observed_total)
            - known_pilot_components
            - (
                float(observed_preflight)
                if isinstance(observed_preflight, (int, float))
                else 0.0
            ),
            0.0,
        )
        if isinstance(observed_total, (int, float))
        else 0.0
    )
    cell_scale = (
        sum(int(row["trials"]) for row in rows) / len(observed_cells)
        if observed_cells
        else 0.0
    )
    projected_overhead = pilot_overhead * cell_scale
    preflight_candidates = [float(current_preflight_cpu_seconds)]
    if isinstance(observed_preflight, (int, float)) and not isinstance(
        observed_preflight, bool
    ):
        preflight_candidates.append(float(observed_preflight))
    projected_preflight_per_invocation = max(preflight_candidates)
    preflight_invocations = (
        V2_CONFIRMATORY_PREFLIGHT_INVOCATIONS
        if _is_v2(config) and phase == "confirmatory"
        else 1
    )
    projected_preflight = projected_preflight_per_invocation * preflight_invocations
    raw_total = projected_fit + projected_inference + projected_overhead + projected_preflight
    budget = config.get("computational_budget", {})
    budget_mapping = budget if isinstance(budget, Mapping) else {}
    if _is_v2(config):
        _validate_v2_budget(config)
    safety_factor = float(budget_mapping.get("safety_factor", 2.0))
    ask_first_cpu_hours = float(budget_mapping.get("ask_first_cpu_hours", 0.0))
    pilot_gate = pilot_summary.get("eligibility_gate")
    pilot_timing_authenticated = (
        not (_is_v2(config) and phase == "confirmatory")
        or (
            isinstance(pilot_gate, Mapping)
            and pilot_summary.get("schema_version") == "academic-run-summary-v2"
            and pilot_summary.get("phase") == "pilot"
            and pilot_summary.get("config_identity") == config_identity(config)
            and pilot_gate.get("exact_matrix_match") is True
            and pilot_gate.get("prediction_artifacts_verified") is True
            and pilot_gate.get("numeric_authority_accountable") is True
            and pilot_gate.get("schema_versions_valid") is True
        )
    )
    estimate_complete = (
        projected_families == len(rows)
        and bool(rows)
        and not planning_errors
        and isinstance(observed_total, (int, float))
        and not isinstance(observed_total, bool)
        and math.isfinite(float(observed_total))
        and float(observed_total) >= 0.0
        and math.isfinite(projected_preflight_per_invocation)
        and projected_preflight_per_invocation >= 0.0
        and math.isfinite(raw_total)
        and raw_total >= 0.0
        and pilot_timing_authenticated
    )
    try:
        planned_logical_cells = len(
            _logical_plan(config, phase, project_root=project_root)
        )
    except ValueError:
        planned_logical_cells = sum(int(row["trials"]) for row in rows)
    return {
        "planned_logical_cells": planned_logical_cells,
        "per_cell_family": rows,
        "projected_fit_cpu_hours_from_pilot": projected_fit / 3600.0 if projected_families else None,
        "projected_inference_cpu_hours_from_pilot": projected_inference / 3600.0 if projected_families else None,
        "projected_overhead_cpu_hours_from_pilot": projected_overhead / 3600.0 if observed_cells else None,
        "projected_preflight_invocations": preflight_invocations,
        "confirmatory_preflight_invocations": (
            V2_CONFIRMATORY_PREFLIGHT_INVOCATIONS
            if _is_v2(config) and phase == "confirmatory"
            else 0
        ),
        "confirmatory_standalone_preflight_invocations": (
            V2_CONFIRMATORY_STANDALONE_PREFLIGHT_INVOCATIONS
            if _is_v2(config) and phase == "confirmatory"
            else 0
        ),
        "confirmatory_batch_preflight_invocations": (
            V2_CONFIRMATORY_BATCH_COUNT
            if _is_v2(config) and phase == "confirmatory"
            else 0
        ),
        "current_preflight_cpu_seconds": current_preflight_cpu_seconds,
        "projected_preflight_cpu_hours_per_invocation": (
            projected_preflight_per_invocation / 3600.0
            if math.isfinite(projected_preflight_per_invocation)
            else None
        ),
        "projected_preflight_cpu_hours": (
            projected_preflight / 3600.0
            if math.isfinite(projected_preflight_per_invocation)
            else None
        ),
        "projected_total_cpu_hours": raw_total / 3600.0 if estimate_complete else None,
        "projected_total_cpu_hours_conservative": (
            raw_total * safety_factor / 3600.0 if estimate_complete else None
        ),
        "safety_factor": safety_factor,
        "ask_first_cpu_hours": ask_first_cpu_hours,
        "projection_family_coverage": f"{projected_families}/{len(rows)}",
        "projection_complete": estimate_complete,
        "pilot_timing_authenticated": pilot_timing_authenticated,
        "planning_errors": planning_errors,
        "cpu_hour_estimate_reason": (
            "pilot-measured fit, validation/test inference, run overhead, the mandatory "
            "standalone preflight, and all five batch-local preflight invocations scaled to "
            "the fixed 50-trial confirmatory protocol, then "
            "multiplied by the frozen safety factor"
            if estimate_complete
            else "complete authenticated pilot timing for every cell family is required"
        ),
    }


def _nested_mapping_value(value: object, *keys: str) -> object:
    current = value
    for key in keys:
        if not isinstance(current, Mapping):
            return None
        current = current.get(key)
    return current


def _persist_failure(paths: AcademicPaths, failure: Mapping[str, object]) -> None:
    failure_dir = paths.phase / "failures"
    timestamp = datetime.now(timezone.utc).strftime("%Y%m%dT%H%M%S%fZ")
    identity = canonical_json_hash(dict(failure))[-12:]
    schema_version = failure.get("schema_version")
    if schema_version not in {"academic-cell-failure-v1", "academic-cell-failure-v2"}:
        schema_version = (
            "academic-cell-failure-v2"
            if failure.get("runner_protocol") == RUNNER_PROTOCOL
            else "academic-cell-failure-v1"
        )
    _write_json(
        failure_dir / f"failure-{timestamp}-{identity}.json",
        {
            "schema_version": schema_version,
            "recorded_at_utc": _utc_now(),
            **dict(failure),
        },
        immutable=True,
    )


def _mapping(value: object, name: str) -> Mapping[str, object]:
    if not isinstance(value, Mapping):
        raise ValueError(f"{name} must be an object.")
    return value


def _binary_support(labels: object) -> dict[str, int]:
    raw = np.asarray(labels, dtype=object).reshape(-1)
    normalized: list[int] = []
    for index, value in enumerate(raw.tolist()):
        if isinstance(value, (bool, np.bool_)):
            raise ValueError(f"labels[{index}] must not be Boolean")
        if isinstance(value, (int, np.integer)):
            label = int(value)
        elif isinstance(value, (float, np.floating)):
            numeric = float(value)
            if not math.isfinite(numeric):
                raise ValueError(f"labels[{index}] is non-finite")
            if not numeric.is_integer():
                raise ValueError(f"labels[{index}] is fractional")
            label = int(numeric)
        else:
            raise ValueError(f"labels[{index}] is not numeric")
        if label not in {0, 1}:
            raise ValueError(f"labels[{index}] is not binary")
        normalized.append(label)
    array = np.asarray(normalized, dtype=np.int64)
    return {
        "total": int(array.size),
        "normal": int(np.sum(array == 0)),
        "attack": int(np.sum(array == 1)),
    }


def _cell_metric(cell: Mapping[str, object], name: str) -> float | None:
    test = cell.get("test")
    if not isinstance(test, Mapping):
        return None
    for section_name in ("operating", "ranking"):
        section = test.get(section_name)
        if isinstance(section, Mapping):
            value = section.get(name)
            if isinstance(value, (int, float)) and math.isfinite(float(value)):
                return float(value)
    return None


def _expand_deterministic_values(
    values: Mapping[int, float], target_seeds: Sequence[int]
) -> dict[int, float]:
    if len(values) == 1 and target_seeds:
        only = next(iter(values.values()))
        return {int(seed): float(only) for seed in target_seeds}
    return {int(seed): float(value) for seed, value in values.items()}


def _json_bytes(value: object) -> bytes:
    return (
        json.dumps(
            _json_safe(value),
            sort_keys=True,
            indent=2,
            ensure_ascii=False,
            allow_nan=False,
        )
        + "\n"
    ).encode("utf-8")


def _json_safe(value: object) -> object:
    if isinstance(value, Mapping):
        return {str(key): _json_safe(item) for key, item in value.items()}
    if isinstance(value, (list, tuple)):
        return [_json_safe(item) for item in value]
    if isinstance(value, np.ndarray):
        return _json_safe(value.tolist())
    if isinstance(value, np.generic):
        return _json_safe(value.item())
    if isinstance(value, Path):
        return str(value)
    if isinstance(value, float) and not math.isfinite(value):
        return None
    return value


def _write_json(path: Path, value: object, *, immutable: bool) -> None:
    payload = _json_bytes(value)
    _atomic_write(path, payload, immutable=immutable)


def _write_jsonl(path: Path, rows: Sequence[Mapping[str, object]], *, immutable: bool) -> None:
    _atomic_write(path, _jsonl_bytes(rows), immutable=immutable)


def _jsonl_bytes(rows: Sequence[Mapping[str, object]]) -> bytes:
    return b"".join(
        json.dumps(
            _json_safe(row), sort_keys=True, ensure_ascii=False, allow_nan=False
        ).encode("utf-8")
        + b"\n"
        for row in rows
    )


def _publish_cell_transaction(
    paths: AcademicPaths,
    *,
    cell: Mapping[str, object],
    prediction_rows: Sequence[Mapping[str, object]],
) -> None:
    """Journal and recoverably publish a prediction/cell artifact pair."""

    cell_id = cell.get("cell_id")
    if (
        not isinstance(cell_id, str)
        or not cell_id
        or Path(cell_id).name != cell_id
    ):
        raise RuntimeError("Cell publication requires a safe immutable cell_id.")
    publication = _mapping(
        cell.get("publication_transaction"), "cell.publication_transaction"
    )
    transaction_id = f"academic-cell-publication:{cell_id}"
    manifest_path = paths.transactions / f"{cell_id}.transaction.json"
    if (
        publication.get("transaction_id") != transaction_id
        or publication.get("manifest_path") != str(manifest_path.resolve())
    ):
        raise RuntimeError("Cell publication transaction binding is inconsistent.")

    prediction_payload = _jsonl_bytes(prediction_rows)
    prediction_hash = f"sha256:{sha256(prediction_payload).hexdigest()}"
    expected_prediction = _mapping(
        cell.get("predictions_artifact"), "cell.predictions_artifact"
    )
    prediction_path = paths.predictions / f"{cell_id}.jsonl"
    if (
        expected_prediction.get("path") != str(prediction_path.resolve())
        or expected_prediction.get("sha256") != prediction_hash
        or expected_prediction.get("rows") != len(prediction_rows)
    ):
        raise RuntimeError("Prediction payload does not match its cell binding.")

    cell_payload = _json_bytes(cell)
    cell_hash = f"sha256:{sha256(cell_payload).hexdigest()}"
    prediction_payload_path = paths.transactions / (
        f"{cell_id}.prediction.{prediction_hash.split(':', 1)[1]}.jsonl"
    )
    cell_payload_path = paths.transactions / (
        f"{cell_id}.cell.{cell_hash.split(':', 1)[1]}.json"
    )
    _atomic_write(prediction_payload_path, prediction_payload, immutable=True)
    _atomic_write(cell_payload_path, cell_payload, immutable=True)

    manifest_core: dict[str, object] = {
        "schema_version": "academic-cell-publication-transaction-v1",
        "state": "committed",
        "transaction_id": transaction_id,
        "cell_id": cell_id,
        "cell_target_path": str((paths.cells / f"{cell_id}.json").resolve()),
        "cell_payload_path": str(cell_payload_path.resolve()),
        "cell_sha256": cell_hash,
        "prediction_target_path": str(prediction_path.resolve()),
        "prediction_payload_path": str(prediction_payload_path.resolve()),
        "prediction_sha256": prediction_hash,
        "prediction_rows": len(prediction_rows),
    }
    manifest = {
        **manifest_core,
        "identity": canonical_json_hash(manifest_core),
    }
    _write_json(manifest_path, manifest, immutable=True)
    _recover_cell_transaction(paths, manifest_path)


def _recover_cell_transactions(paths: AcademicPaths) -> None:
    """Complete every committed transaction before artifacts are discovered."""

    if paths.transactions.is_symlink():
        raise RuntimeError("Cell transaction directory must not be a symlink.")
    for manifest_path in sorted(paths.transactions.glob("*.transaction.json")):
        _recover_cell_transaction(paths, manifest_path)


def _recover_cell_transaction(paths: AcademicPaths, manifest_path: Path) -> None:
    manifest = _read_json(manifest_path)
    if manifest.get("schema_version") != "academic-cell-publication-transaction-v1":
        raise RuntimeError(f"Unsupported cell transaction schema: {manifest_path}")
    identity = manifest.get("identity")
    manifest_core = {key: value for key, value in manifest.items() if key != "identity"}
    if identity != canonical_json_hash(manifest_core):
        raise RuntimeError(f"Cell transaction identity mismatch: {manifest_path}")
    cell_id = manifest.get("cell_id")
    transaction_id = manifest.get("transaction_id")
    if (
        manifest.get("state") != "committed"
        or not isinstance(cell_id, str)
        or transaction_id != f"academic-cell-publication:{cell_id}"
    ):
        raise RuntimeError(f"Cell transaction is not a committed closed record: {manifest_path}")
    expected_manifest = paths.transactions / f"{cell_id}.transaction.json"
    if manifest_path.is_symlink() or manifest_path.resolve() != expected_manifest.resolve():
        raise RuntimeError("Cell transaction manifest escapes its frozen directory.")

    cell_target = paths.cells / f"{cell_id}.json"
    prediction_target = paths.predictions / f"{cell_id}.jsonl"
    if (
        manifest.get("cell_target_path") != str(cell_target.resolve())
        or manifest.get("prediction_target_path") != str(prediction_target.resolve())
    ):
        raise RuntimeError("Cell transaction target binding is inconsistent.")
    cell_payload_path = Path(str(manifest.get("cell_payload_path", "")))
    prediction_payload_path = Path(
        str(manifest.get("prediction_payload_path", ""))
    )
    for payload_path, expected_hash in (
        (cell_payload_path, manifest.get("cell_sha256")),
        (prediction_payload_path, manifest.get("prediction_sha256")),
    ):
        if (
            payload_path.is_symlink()
            or payload_path.resolve().parent != paths.transactions.resolve()
            or not payload_path.is_file()
            or file_sha256(payload_path) != expected_hash
        ):
            raise RuntimeError(
                f"Cell transaction payload is missing or unauthenticated: {payload_path}"
            )
    _atomic_write(
        prediction_target,
        prediction_payload_path.read_bytes(),
        immutable=True,
    )
    _atomic_write(cell_target, cell_payload_path.read_bytes(), immutable=True)
    if (
        file_sha256(prediction_target) != manifest.get("prediction_sha256")
        or file_sha256(cell_target) != manifest.get("cell_sha256")
    ):
        raise RuntimeError("Recovered cell transaction failed final hash verification.")


def _atomic_write(path: Path, payload: bytes, *, immutable: bool) -> None:
    if path.parent.is_symlink():
        raise RuntimeError(f"Artifact parent directory must not be a symlink: {path.parent}")
    path.parent.mkdir(parents=True, exist_ok=True)
    if path.parent.is_symlink() or path.is_symlink():
        raise RuntimeError(f"Artifact path must not traverse a symlink: {path}")
    if path.exists():
        existing = path.read_bytes()
        if immutable:
            if existing != payload:
                raise RuntimeError(f"Immutable artifact conflict: {path}")
            return
    temporary_path: Path | None = None
    try:
        with tempfile.NamedTemporaryFile(
            mode="wb",
            dir=path.parent,
            prefix=f".{path.name}.",
            suffix=".tmp",
            delete=False,
        ) as handle:
            temporary_path = Path(handle.name)
            handle.write(payload)
            handle.flush()
            os.fsync(handle.fileno())
        if path.is_symlink():
            raise RuntimeError(f"Artifact path became a symlink before publication: {path}")
        if immutable:
            try:
                # Atomic create-without-replace.  Unlike a final exists/check +
                # os.replace sequence, a concurrent writer can never be silently
                # overwritten between verification and publication.
                os.link(temporary_path, path)
            except FileExistsError:
                if path.is_symlink():
                    raise RuntimeError(
                        f"Artifact path became a symlink before publication: {path}"
                    )
                if path.read_bytes() != payload:
                    raise RuntimeError(f"Immutable artifact conflict: {path}")
            temporary_path.unlink(missing_ok=True)
            temporary_path = None
        else:
            os.replace(temporary_path, path)
            temporary_path = None
    finally:
        if temporary_path is not None:
            temporary_path.unlink(missing_ok=True)


def _read_json(path: Path) -> dict[str, object]:
    if Path(path).is_symlink():
        raise ValueError(f"Refusing symlinked JSON artifact: {path}")
    value = json.loads(Path(path).read_text(encoding="utf-8"))
    if not isinstance(value, dict):
        raise ValueError(f"Expected JSON object in {path}.")
    return value


def _utc_now() -> str:
    return datetime.now(timezone.utc).isoformat().replace("+00:00", "Z")


__all__ = [
    "AcademicPaths",
    "CONFIG_SCHEMA",
    "CONFIG_SCHEMA_V2",
    "NUMERIC_REQUIREMENTS_SCHEMA",
    "RUNNER_PROTOCOL",
    "V2_CONFIRMATORY_BATCH_COUNT",
    "V2_CONFIRMATORY_PREFLIGHT_INVOCATIONS",
    "V2_CONFIRMATORY_STANDALONE_PREFLIGHT_INVOCATIONS",
    "academic_paths",
    "analyze_completed_cells",
    "confirmatory_batch_ledger",
    "confirmatory_budget_issue",
    "config_identity",
    "environment_manifest",
    "load_academic_config",
    "load_completed_cells",
    "run_academic_phase",
    "run_preflight",
    "validate_cell_raw_reconstruction",
]
