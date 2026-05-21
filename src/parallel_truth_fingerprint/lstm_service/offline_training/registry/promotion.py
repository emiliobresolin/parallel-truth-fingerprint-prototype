"""Story 8.1: promote one TrainingRunRecord to live-runtime status.

The promotion writes the chosen run_id (plus a small provenance payload)
to `fingerprint-training-history/index/latest.json`. Story 8.2's online
inference helper reads from this single source of truth at runtime
start-up; the dashboard (Story 8.4) reads the same payload to display
which run is currently endorsed.
"""

from __future__ import annotations

from dataclasses import dataclass
from datetime import datetime, timezone

from parallel_truth_fingerprint.lstm_service.offline_training.registry.training_history import (
    HISTORY_PREFIX,
    RUNS_SUBPREFIX,
    read_training_run,
)


LATEST_INDEX_KEY_SUFFIX = "index/latest.json"


@dataclass(frozen=True)
class PromotedRun:
    """The single 'currently endorsed' run pointer."""

    run_id: str
    dataset_name: str
    model_name: str
    promoted_at: str
    previous_run_id: str | None


def latest_index_object_key(prefix: str = HISTORY_PREFIX) -> str:
    return f"{prefix}{LATEST_INDEX_KEY_SUFFIX}"


def promote_training_run(
    run_id: str,
    *,
    artifact_store,
    prefix: str = HISTORY_PREFIX,
) -> PromotedRun:
    """Endorse `run_id` as the run the live runtime should use.

    Raises ValueError if `run_id` does not point at an existing record in
    the configured store. Re-promoting the same id is a no-op (returns
    the existing pointer untouched).
    """

    # 1) Verify the run record exists. read_training_run uses the same
    # prefix layout (runs/<run_id>.json).
    try:
        record = read_training_run(run_id, artifact_store=artifact_store, prefix=prefix)
    except Exception as error:
        raise ValueError(
            f"Cannot promote unknown run id {run_id!r}. "
            f"Expected a record under {prefix}{RUNS_SUBPREFIX}{run_id}.json "
            f"(underlying error: {error})."
        ) from error

    # 2) If the same id is already promoted, return the existing payload.
    existing = read_promoted_run(artifact_store=artifact_store, prefix=prefix)
    if existing is not None and existing.run_id == run_id:
        return existing

    promoted_at = datetime.now(timezone.utc).isoformat()
    previous_run_id = existing.run_id if existing is not None else None

    payload = {
        "run_id": record.run_id,
        "dataset_name": record.dataset_name,
        "model_name": record.model_name,
        "promoted_at": promoted_at,
        "previous_run_id": previous_run_id,
    }
    artifact_store.save_json(latest_index_object_key(prefix), payload)

    return PromotedRun(
        run_id=record.run_id,
        dataset_name=record.dataset_name,
        model_name=record.model_name,
        promoted_at=promoted_at,
        previous_run_id=previous_run_id,
    )


def read_promoted_run(
    *,
    artifact_store,
    prefix: str = HISTORY_PREFIX,
) -> PromotedRun | None:
    """Return the currently-promoted run pointer, or None if not set."""
    try:
        payload = artifact_store.load_json(latest_index_object_key(prefix))
    except Exception:
        return None
    return PromotedRun(
        run_id=str(payload["run_id"]),
        dataset_name=str(payload["dataset_name"]),
        model_name=str(payload["model_name"]),
        promoted_at=str(payload["promoted_at"]),
        previous_run_id=(
            None
            if payload.get("previous_run_id") is None
            else str(payload["previous_run_id"])
        ),
    )
