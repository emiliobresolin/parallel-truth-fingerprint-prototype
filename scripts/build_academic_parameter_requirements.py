"""Inventory academic numeric consumers without inventing their authority.

This helper creates a deterministic *requirements* artifact.  It deliberately
leaves every ParameterEvidence.v1 revision unresolved; a researcher or source
decision must close those fields before the v2 preflight can execute data.
"""

from __future__ import annotations

import argparse
from hashlib import sha256
import json
import os
from pathlib import Path
import sys
import tempfile


PROJECT_ROOT = Path(__file__).resolve().parents[1]
SRC_ROOT = PROJECT_ROOT / "src"
if str(SRC_ROOT) not in sys.path:
    sys.path.insert(0, str(SRC_ROOT))

from parallel_truth_fingerprint.lstm_service.offline_training.academic_runner import (  # noqa: E402
    NUMERIC_REQUIREMENTS_SCHEMA,
    _numeric_config_leaves,
    load_academic_config,
)
from parallel_truth_fingerprint.lstm_service.offline_training.academic_numeric_schema import (  # noqa: E402
    V2_NUMERIC_SCHEMA_IDENTITY,
    V2_NUMERIC_SCHEMA_VERSION,
)


def _semantics(pointer: str) -> tuple[str, str]:
    lowered = pointer.casefold()
    if "ask_first_cpu_hours" in lowered:
        return "CPU-hour", "computational_budget"
    if "safety_factor" in lowered:
        return "one", "computational_budget"
    if "/execution_protocol/confirmatory_batch_size" in lowered:
        return "count", "repetition_count"
    if "seed" in lowered:
        return "count", "random_seed"
    if "minimum_class_carrying_clusters" in lowered:
        return "count", "independent_cluster_count"
    if "minimum_valid_bootstrap_replicates" in lowered or "bootstrap_replicates" in lowered:
        return "count", "bootstrap_replicate_count"
    if "minimum_valid_bootstrap_fraction" in lowered:
        return "one", "metric_parameter"
    if any(token in lowered for token in ("fraction", "fpr", "quantile", "confidence")):
        return "one", "split_fraction" if "fraction" in lowered else "metric_parameter"
    if "max_windows_per_unit" in lowered:
        return "count", "window_count"
    if any(token in lowered for token in ("sequence_length", "stride", "block_rows")):
        return "count", "window_length"
    if any(token in lowered for token in ("epoch", "patience", "batch_size")):
        return "count", "training_stopping"
    if any(token in lowered for token in ("trial", "replicate")):
        return "count", "repetition_count"
    if "minimum_bootstrap_clusters" in lowered or "minimum_units_per_role" in lowered:
        return "count", "sample_count"
    if "curve_max_points" in lowered:
        return "count", "metric_parameter"
    if "numeric_clip" in lowered:
        return "one", "model_hyperparameter"
    if "/models/" in lowered:
        return "one" if any(token in lowered for token in ("learning_rate", "min_delta", "alpha", "robust_z")) else "count", "model_hyperparameter"
    if "/phase_allocation/" in lowered and "/offsets/" in lowered:
        return "count", "sample_offset"
    if any(token in lowered for token in ("phase_caps", "minimum_support", "phase_allocation")):
        return "count", "sample_count"
    return "one", "metric_parameter"


def build(config: dict[str, object]) -> dict[str, object]:
    slots: list[dict[str, object]] = []
    for pointer, value, json_type in _numeric_config_leaves(config):
        unit, quantity_kind = _semantics(pointer)
        digest = sha256(pointer.encode("utf-8")).hexdigest()[:20]
        slots.append(
            {
                "slot_id": f"academic-numeric-slot:{digest}",
                "consumer_locator": pointer,
                "value": value,
                "json_type": json_type,
                "unit": unit,
                "quantity_kind": quantity_kind,
                "parameter_revision_id": None,
                "parameter_revision_sha256": None,
                "authority_status": "unresolved",
                "required_resolution": (
                    "Bind an immutable accountable ParameterEvidence.v1 revision with exact "
                    "value, unit, scope, and source/decision/calibration locator."
                ),
            }
        )
    return {
        "schema_version": NUMERIC_REQUIREMENTS_SCHEMA,
        "numeric_schema_version": V2_NUMERIC_SCHEMA_VERSION,
        "numeric_schema_identity": V2_NUMERIC_SCHEMA_IDENTITY,
        "experiment_id": config["experiment_id"],
        "authorization_effect": "none",
        "numeric_consumer_count": len(slots),
        "slots": slots,
        "limitations": [
            "This inventory supplies no values and grants no authority.",
            "Every unresolved slot blocks execution and scientific claims.",
        ],
    }


def main(argv: list[str] | None = None) -> int:
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument(
        "--config",
        type=Path,
        default=PROJECT_ROOT / "configs" / "experiments" / "thesis-evaluation-v2.json",
    )
    parser.add_argument(
        "--output",
        type=Path,
        default=PROJECT_ROOT
        / "configs"
        / "experiments"
        / "thesis-evaluation-v2.parameter-requirements-v2.1.json",
    )
    args = parser.parse_args(argv)
    config_path = args.config.resolve()
    output_path = args.output.resolve()
    same_existing_file = False
    if args.config.exists() and args.output.exists():
        try:
            same_existing_file = os.path.samefile(args.config, args.output)
        except OSError:
            same_existing_file = False
    if config_path == output_path or same_existing_file:
        parser.error("--output must not overwrite --config")
    config = load_academic_config(args.config)
    payload = json.dumps(
        build(config), sort_keys=True, indent=2, ensure_ascii=False, allow_nan=False
    ) + "\n"
    args.output.parent.mkdir(parents=True, exist_ok=True)
    if args.output.parent.is_symlink() or args.output.is_symlink():
        parser.error("inventory output and parent must not be symlinks")
    temporary_path: Path | None = None
    try:
        with tempfile.NamedTemporaryFile(
            mode="wb",
            dir=args.output.parent,
            prefix=f".{args.output.name}.",
            suffix=".tmp",
            delete=False,
        ) as handle:
            temporary_path = Path(handle.name)
            handle.write(payload.encode("utf-8"))
            handle.flush()
            os.fsync(handle.fileno())
        try:
            # Hard-link publication is atomic and has no replace semantics.  A
            # cooperating or non-cooperating writer that wins the target name
            # cannot be overwritten in a final check/replace race.
            os.link(temporary_path, args.output)
        except FileExistsError:
            issue = _existing_inventory_issue(args.output)
            if issue is not None:
                parser.error(issue)
            if args.output.read_bytes() != payload.encode("utf-8"):
                parser.error(
                    "refusing to replace an existing immutable unresolved inventory; "
                    "publish the revised schema to a new --output path"
                )
    finally:
        if temporary_path is not None:
            temporary_path.unlink(missing_ok=True)
    print(args.output)
    return 0


def _contains_authority(payload: object) -> bool:
    """Fail closed when regeneration could erase a human authority decision."""

    top_level_fields = {
        "schema_version",
        "numeric_schema_version",
        "numeric_schema_identity",
        "experiment_id",
        "authorization_effect",
        "numeric_consumer_count",
        "slots",
        "limitations",
    }
    slot_fields = {
        "slot_id",
        "consumer_locator",
        "value",
        "json_type",
        "unit",
        "quantity_kind",
        "parameter_revision_id",
        "parameter_revision_sha256",
        "authority_status",
        "required_resolution",
    }
    if (
        not isinstance(payload, dict)
        or set(payload) != top_level_fields
        or payload.get("authorization_effect") != "none"
        or not isinstance(payload.get("slots"), list)
    ):
        return True
    for slot in payload["slots"]:
        if not isinstance(slot, dict) or set(slot) != slot_fields:
            return True
        if slot.get("authority_status") != "unresolved":
            return True
        if slot.get("parameter_revision_id") is not None:
            return True
        if slot.get("parameter_revision_sha256") is not None:
            return True
    return False


def _existing_inventory_issue(path: Path) -> str | None:
    if path.is_symlink():
        return "refusing to replace an inventory through --output symlink"
    if not path.exists():
        return None
    try:
        existing = json.loads(path.read_text(encoding="utf-8"))
    except (OSError, UnicodeError, json.JSONDecodeError) as exc:
        return f"refusing to overwrite unreadable existing inventory: {exc}"
    if _contains_authority(existing):
        return (
            "refusing to overwrite an inventory containing resolved, partial, "
            "or otherwise authority-bearing content"
        )
    return None


if __name__ == "__main__":
    raise SystemExit(main())
