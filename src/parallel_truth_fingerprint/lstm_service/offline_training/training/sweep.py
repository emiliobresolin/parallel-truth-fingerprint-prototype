"""Story 7.9: hyperparameter sweep harness for the offline training track.

Drives `execute_training_run` across the cartesian product of a sweep
config grid, persists every resulting `TrainingRunRecord` via Story 7.3,
and provides `summarize_sweep` for the Markdown aggregation that feeds
the cross-benchmark report (Story 7.13).

Sweep config dict shape (mirrors the JSON file in scripts/sweeps/):

    {
        "benchmark": str,
        "models": [str, ...],
        "epochs": int,
        "seed": int,
        "extra_hyperparameters": {...},
        "grid": {
            "learning_rate": [float, ...],
            "batch_size": [int, ...],
            "sequence_length": [int, ...]
        }
    }
"""

from __future__ import annotations

import itertools
from typing import Sequence

from parallel_truth_fingerprint.lstm_service.offline_training.registry.training_history import (
    WrittenRun,
    record_training_run_to_artifact_store,
)
from parallel_truth_fingerprint.lstm_service.offline_training.training.run import (
    TrainingRunRecord,
    execute_training_run,
)


_REQUIRED_GRID_AXES: tuple[str, ...] = (
    "learning_rate",
    "batch_size",
    "sequence_length",
)


def run_sweep(
    config: dict,
    *,
    artifact_store,
) -> list[tuple[TrainingRunRecord, WrittenRun]]:
    """Execute every cell of `config['grid']` x `config['models']`."""

    benchmark = str(config.get("benchmark", "")).strip()
    if not benchmark:
        raise ValueError("Sweep config requires a non-empty 'benchmark' key.")

    models: Sequence[str] = config.get("models", ()) or ()
    if not models:
        raise ValueError("Sweep config requires at least one model in 'models'.")

    grid = config.get("grid") or {}
    missing = [axis for axis in _REQUIRED_GRID_AXES if axis not in grid]
    if missing:
        raise ValueError(
            f"Sweep config 'grid' is missing required axes: {missing}. "
            f"Required: {list(_REQUIRED_GRID_AXES)}."
        )
    for axis in _REQUIRED_GRID_AXES:
        if not grid[axis]:
            raise ValueError(f"Sweep config grid axis {axis!r} must be non-empty.")

    epochs = int(config.get("epochs", 1))
    seed = int(config.get("seed", 0))
    extra = dict(config.get("extra_hyperparameters", {}))

    learning_rates = list(grid["learning_rate"])
    batch_sizes = list(grid["batch_size"])
    sequence_lengths = list(grid["sequence_length"])

    results: list[tuple[TrainingRunRecord, WrittenRun]] = []
    for model_name, learning_rate, batch_size, sequence_length in itertools.product(
        models, learning_rates, batch_sizes, sequence_lengths
    ):
        record = execute_training_run(
            benchmark=benchmark,
            model=str(model_name),
            epochs=epochs,
            batch_size=int(batch_size),
            learning_rate=float(learning_rate),
            sequence_length=int(sequence_length),
            seed=seed,
            extra_hyperparameters=extra,
        )
        written = record_training_run_to_artifact_store(record, artifact_store)
        results.append((record, written))
    return results


def summarize_sweep(records: Sequence[TrainingRunRecord]) -> str:
    """Return a Markdown table sorted by macro_f1 descending."""

    if not records:
        return "_No training runs were executed in this sweep._\n"

    header = (
        "| run_id | model | learning_rate | batch_size | sequence_length | "
        "macro_f1 | accuracy | macro_precision | macro_recall |\n"
        "| --- | --- | ---: | ---: | ---: | ---: | ---: | ---: | ---: |\n"
    )

    rows = []
    for record in sorted(
        records, key=lambda r: r.metrics.get("macro_f1", 0.0), reverse=True
    ):
        rows.append(
            "| {run_id} | {model} | {lr:g} | {bs} | {seq} | "
            "{f1:.4f} | {acc:.4f} | {p:.4f} | {r:.4f} |".format(
                run_id=record.run_id,
                model=record.model_name,
                lr=float(record.hyperparameters.get("learning_rate", 0.0)),
                bs=int(record.hyperparameters.get("batch_size", 0)),
                seq=int(record.sequence_length),
                f1=record.metrics.get("macro_f1", 0.0),
                acc=record.metrics.get("accuracy", 0.0),
                p=record.metrics.get("macro_precision", 0.0),
                r=record.metrics.get("macro_recall", 0.0),
            )
        )
    return header + "\n".join(rows) + "\n"
