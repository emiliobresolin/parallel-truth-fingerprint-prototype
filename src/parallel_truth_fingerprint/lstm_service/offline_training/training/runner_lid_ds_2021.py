"""Story 7.11 helper: first real training run on LID-DS 2021.

Twin of `runner_adfa_ld.py` for the LID-DS 2021 benchmark. Same
orchestration: configure env -> execute_training_run -> persist via
Story 7.3 -> return (record, written).
"""

from __future__ import annotations

import os
from pathlib import Path

from parallel_truth_fingerprint.lstm_service.offline_training.registry.training_history import (
    WrittenRun,
    record_training_run_to_artifact_store,
)
from parallel_truth_fingerprint.lstm_service.offline_training.training.run import (
    TrainingRunRecord,
    execute_training_run,
)


def run_first_lid_ds_2021_training(
    *,
    lid_ds_root: Path | None = None,
    artifact_store,
    epochs: int = 30,
    batch_size: int = 64,
    learning_rate: float = 1e-3,
    sequence_length: int = 50,
    seed: int = 42,
    extra_hyperparameters: dict[str, object] | None = None,
) -> tuple[TrainingRunRecord, WrittenRun]:
    previous_env = os.environ.get("LID_DS_2021_PATH")
    if lid_ds_root is not None:
        os.environ["LID_DS_2021_PATH"] = str(lid_ds_root)
    try:
        record = execute_training_run(
            benchmark="lid-ds-2021",
            model="lstm-classifier",
            epochs=epochs,
            batch_size=batch_size,
            learning_rate=learning_rate,
            sequence_length=sequence_length,
            seed=seed,
            extra_hyperparameters=extra_hyperparameters,
        )
    finally:
        if lid_ds_root is not None:
            if previous_env is None:
                os.environ.pop("LID_DS_2021_PATH", None)
            else:
                os.environ["LID_DS_2021_PATH"] = previous_env

    written = record_training_run_to_artifact_store(record, artifact_store)
    return record, written
