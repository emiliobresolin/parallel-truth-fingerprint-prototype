"""Story 8.4: dashboard-facing read-only view of the promoted classifier.

A thin formatter built on top of Story 8.1's `read_promoted_run` and
Story 7.3's `read_training_run`. Returns a JSON-safe dict so the live
dashboard (and any other inspection surface) can embed the promoted
run's identity + champion metrics without coupling to Keras/torch.
"""

from __future__ import annotations

from parallel_truth_fingerprint.lstm_service.offline_training.registry.promotion import (
    read_promoted_run,
)
from parallel_truth_fingerprint.lstm_service.offline_training.registry.training_history import (
    read_training_run,
)


def build_promoted_run_dashboard_view(artifact_store) -> dict[str, object]:
    """Return a dict ready to embed into the dashboard state payload."""
    promoted = read_promoted_run(artifact_store=artifact_store)
    if promoted is None:
        return {
            "status": "none",
            "run_id": None,
            "dataset_name": None,
            "model_name": None,
            "promoted_at": None,
            "previous_run_id": None,
            "macro_f1": None,
            "accuracy": None,
            "parameter_count": None,
        }

    try:
        record = read_training_run(
            promoted.run_id, artifact_store=artifact_store
        )
    except Exception:
        return {
            "status": "promoted",
            "run_id": promoted.run_id,
            "dataset_name": promoted.dataset_name,
            "model_name": promoted.model_name,
            "promoted_at": promoted.promoted_at,
            "previous_run_id": promoted.previous_run_id,
            "macro_f1": None,
            "accuracy": None,
            "parameter_count": None,
        }

    metrics = record.metrics or {}
    return {
        "status": "promoted",
        "run_id": promoted.run_id,
        "dataset_name": promoted.dataset_name,
        "model_name": promoted.model_name,
        "promoted_at": promoted.promoted_at,
        "previous_run_id": promoted.previous_run_id,
        "macro_f1": (
            None
            if "macro_f1" not in metrics
            else float(metrics["macro_f1"])
        ),
        "accuracy": (
            None
            if "accuracy" not in metrics
            else float(metrics["accuracy"])
        ),
        "parameter_count": int(record.parameter_count),
    }
