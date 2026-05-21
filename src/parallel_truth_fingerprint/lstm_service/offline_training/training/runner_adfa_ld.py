"""Story 7.7 helper: first real training run on ADFA-LD.

Orchestrates configure_root -> execute_training_run -> persist via Story 7.3.
Reusable by `scripts/train_lstm_offline.py --persist` and by unit tests.
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


def run_first_adfa_ld_training(
    *,
    adfa_ld_root: Path | None = None,
    artifact_store,
    epochs: int = 30,
    batch_size: int = 64,
    learning_rate: float = 1e-3,
    sequence_length: int = 50,
    seed: int = 42,
    extra_hyperparameters: dict[str, object] | None = None,
) -> tuple[TrainingRunRecord, WrittenRun]:
    """Run ADFA-LD + LSTM end-to-end and persist the result.

    `adfa_ld_root` overrides the `ADFA_LD_PATH` env var for this call only.
    The env var is restored on exit so concurrent tests do not see drift.
    """

    previous_env = os.environ.get("ADFA_LD_PATH")
    if adfa_ld_root is not None:
        os.environ["ADFA_LD_PATH"] = str(adfa_ld_root)
    try:
        record = execute_training_run(
            benchmark="adfa-ld",
            model="lstm-classifier",
            epochs=epochs,
            batch_size=batch_size,
            learning_rate=learning_rate,
            sequence_length=sequence_length,
            seed=seed,
            extra_hyperparameters=extra_hyperparameters,
        )
    finally:
        if adfa_ld_root is not None:
            if previous_env is None:
                os.environ.pop("ADFA_LD_PATH", None)
            else:
                os.environ["ADFA_LD_PATH"] = previous_env

    written = record_training_run_to_artifact_store(record, artifact_store)
    return record, written
