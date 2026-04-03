"""Derived Story 5.3 explainability and evidence views for the dashboard."""

from __future__ import annotations

from datetime import datetime, timezone


RUNTIME_VALID_ONLY_EXPLANATION = (
    "The fingerprint pipeline is running correctly, but the current model is still "
    "based on too little normal-history data to claim strong academic validation."
)


def build_dashboard_explainability_view(
    *,
    generated_at: str,
    latest_runtime_payload: dict[str, object] | None,
    operator_actions: list[dict[str, object]],
    limitation_note: str,
) -> dict[str, object]:
    """Build human-readable status translation and evidence summaries."""

    payload = latest_runtime_payload or {}
    runtime = payload.get("runtime") or {}
    latest_cycle = payload.get("latest_cycle") or {}
    cycle_history = payload.get("cycle_history") or []
    lifecycle = latest_cycle.get("fingerprint_lifecycle") or {}
    consensus_summary = latest_cycle.get("consensus_summary") or {}
    replay_behavior = latest_cycle.get("replay_behavior") or {}
    fingerprint_results = latest_cycle.get("fingerprint_inference_results") or []
    runtime_start_time = _find_runtime_start_time(operator_actions)
    elapsed_runtime = _compute_elapsed_runtime(
        runtime_start_time=runtime_start_time,
        generated_at=generated_at,
    )
    current_cycle = int(runtime.get("current_cycle") or 0)
    latest_valid_artifact_count = int(runtime.get("latest_valid_artifact_count") or 0)
    initial_valid_artifact_count = _initial_valid_artifact_count(cycle_history)
    valid_artifact_growth = max(
        latest_valid_artifact_count - initial_valid_artifact_count,
        0,
    )
    first_training_cycle = _first_training_cycle(cycle_history)
    latest_training_mode = _latest_training_mode(lifecycle)
    current_model_identity = _current_model_identity(lifecycle, cycle_history)
    validation_level = str(
        lifecycle.get("source_dataset_validation_level") or "runtime_valid_only"
    )
    translated_statuses = {
        "model_status": _translate_model_status(lifecycle),
        "validation_level": _translate_validation_level(validation_level),
        "consensus_status": _translate_consensus_status(consensus_summary),
        "replay_behavior": _translate_replay_behavior(replay_behavior),
        "training_adequacy": _translate_training_adequacy(lifecycle, validation_level),
        "anomaly_score": _translate_anomaly_score(
            fingerprint_results=fingerprint_results,
            replay_behavior=replay_behavior,
        ),
    }
    happened_already = _build_happened_already(
        current_cycle=current_cycle,
        latest_valid_artifact_count=latest_valid_artifact_count,
        first_training_cycle=first_training_cycle,
        latest_training_mode=latest_training_mode,
        current_model_identity=current_model_identity,
        replay_behavior=replay_behavior,
    )
    not_happened_yet = _build_not_happened_yet(
        lifecycle=lifecycle,
        first_training_cycle=first_training_cycle,
        replay_behavior=replay_behavior,
    )
    expected_next = _build_expected_next(
        lifecycle=lifecycle,
        current_model_identity=current_model_identity,
    )

    return {
        "translated_statuses": translated_statuses,
        "what_changed_since_startup": {
            "runtime_start_time": runtime_start_time,
            "elapsed_runtime": elapsed_runtime,
            "current_cycle_count": current_cycle,
            "valid_artifact_count_growth": {
                "initial_count": initial_valid_artifact_count,
                "current_count": latest_valid_artifact_count,
                "growth": valid_artifact_growth,
                "summary": (
                    f"Valid persisted artifacts grew from {initial_valid_artifact_count} "
                    f"to {latest_valid_artifact_count} in this run."
                ),
            },
            "training": {
                "has_training_happened": first_training_cycle is not None,
                "first_training_reference": None
                if first_training_cycle is None
                else f"cycle {first_training_cycle}",
                "current_model_usage": latest_training_mode,
                "current_model_identity": current_model_identity,
            },
            "questions_answered": {
                "has_fingerprint_been_created": _fingerprint_created_answer(
                    lifecycle=lifecycle,
                    current_model_identity=current_model_identity,
                ),
                "what_changed_since_startup": _what_changed_answer(
                    current_cycle=current_cycle,
                    valid_artifact_growth=valid_artifact_growth,
                    first_training_cycle=first_training_cycle,
                    latest_training_mode=latest_training_mode,
                ),
                "what_evidence_exists_in_this_run": _evidence_answer(
                    current_model_identity=current_model_identity,
                    latest_valid_artifact_count=latest_valid_artifact_count,
                    limitation_note=limitation_note,
                ),
                "what_is_expected_next": expected_next["summary"],
            },
            "happened_already": happened_already,
            "not_happened_yet": not_happened_yet,
            "expected_next": expected_next,
            "limitation": limitation_note,
        },
    }


def _translate_model_status(lifecycle: dict[str, object]) -> dict[str, str]:
    raw_value = str(lifecycle.get("model_status") or "no_model_yet")
    if raw_value == "model_available":
        return {
            "raw_value": raw_value,
            "label": "Fingerprint model is available",
            "explanation": (
                "A fingerprint model has already been trained and saved for reuse in "
                "later cycles."
            ),
        }
    return {
        "raw_value": raw_value,
        "label": "Fingerprint model is not available yet",
        "explanation": (
            "The runtime has not yet created a reusable fingerprint model in this run."
        ),
    }


def _translate_validation_level(validation_level: str) -> dict[str, str]:
    if validation_level == "meaningful_fingerprint_valid":
        return {
            "raw_value": validation_level,
            "label": "Fingerprint adequacy target met",
            "explanation": (
                "The dataset has met the agreed adequacy floor for a stronger "
                "fingerprint claim."
            ),
        }
    return {
        "raw_value": validation_level,
        "label": "Runtime-valid only",
        "explanation": RUNTIME_VALID_ONLY_EXPLANATION,
    }


def _translate_consensus_status(consensus_summary: dict[str, object]) -> dict[str, str]:
    raw_value = str(consensus_summary.get("final_consensus_status") or "unknown")
    if raw_value == "success":
        return {
            "raw_value": raw_value,
            "label": "Consensus succeeded",
            "explanation": (
                "The edge views were committed successfully and the prototype produced "
                "a trusted consensused state."
            ),
        }
    if raw_value == "failed_consensus":
        return {
            "raw_value": raw_value,
            "label": "Consensus failed",
            "explanation": (
                "The edge views did not reach an acceptable committed result for this "
                "cycle."
            ),
        }
    return {
        "raw_value": raw_value,
        "label": "Consensus state is not yet available",
        "explanation": "The dashboard does not yet have a committed consensus result.",
    }


def _translate_replay_behavior(replay_behavior: dict[str, object]) -> dict[str, str]:
    if not replay_behavior:
        return {
            "raw_value": "none",
            "label": "No replay behavior currently detected",
            "explanation": (
                "The current dashboard state does not show a replay or freeze anomaly "
                "through the fingerprint path."
            ),
        }
    classification = replay_behavior.get("classification", "unknown")
    mode = replay_behavior.get("scenario_mode", "unknown")
    return {
        "raw_value": classification,
        "label": f"Replay behavior detected in {mode} mode",
        "explanation": (
            "The fingerprint path has evaluated the SCADA-side behavior and currently "
            f"classifies it as {classification}."
        ),
    }


def _translate_training_adequacy(
    lifecycle: dict[str, object],
    validation_level: str,
) -> dict[str, str]:
    eligible = int(lifecycle.get("eligible_history_count") or 0)
    threshold = int(lifecycle.get("eligible_history_threshold") or 0)
    if validation_level == "meaningful_fingerprint_valid":
        explanation = (
            "The current dataset has enough eligible history to satisfy the agreed "
            "adequacy target."
        )
        label = "Training adequacy target met"
    else:
        explanation = (
            "The training pipeline is active, but the current run has not yet met the "
            "agreed adequacy threshold for strong fingerprint claims."
        )
        label = "Training adequacy still below target"
    if threshold > 0:
        explanation = f"{explanation} Eligible history: {eligible}/{threshold}."
    return {
        "raw_value": validation_level,
        "label": label,
        "explanation": explanation,
    }


def _translate_anomaly_score(
    *,
    fingerprint_results: list[dict[str, object]],
    replay_behavior: dict[str, object],
) -> dict[str, str]:
    if fingerprint_results:
        first = fingerprint_results[0]
        return {
            "raw_value": str(first.get("anomaly_score", "not_available")),
            "label": "Fingerprint anomaly score available",
            "explanation": (
                "The anomaly score is the reconstruction-error signal used by the "
                "fingerprint model for the latest inference window."
            ),
        }
    if replay_behavior:
        return {
            "raw_value": str(replay_behavior.get("anomaly_score", "not_available")),
            "label": "Replay anomaly score available",
            "explanation": (
                "The replay behavior view includes an anomaly score from the existing "
                "fingerprint path."
            ),
        }
    return {
        "raw_value": "not_available",
        "label": "No anomaly score available yet",
        "explanation": (
            "The current dashboard state has not yet produced an inference result with "
            "an anomaly score."
        ),
    }


def _find_runtime_start_time(operator_actions: list[dict[str, object]]) -> str | None:
    start_actions = [
        action.get("applied_at")
        for action in operator_actions
        if action.get("action") == "start_runtime"
        and action.get("applied_at")
        and action.get("effect_scope") != "no_change_already_running"
    ]
    if not start_actions:
        return None
    return sorted((str(timestamp) for timestamp in start_actions), reverse=True)[0]


def _compute_elapsed_runtime(
    *,
    runtime_start_time: str | None,
    generated_at: str,
) -> str:
    if runtime_start_time is None:
        return "not_available"
    try:
        started = datetime.fromisoformat(runtime_start_time)
        generated = datetime.fromisoformat(generated_at)
    except ValueError:
        return "not_available"
    elapsed = max(int((generated - started).total_seconds()), 0)
    hours, remainder = divmod(elapsed, 3600)
    minutes, seconds = divmod(remainder, 60)
    return f"{hours:02d}:{minutes:02d}:{seconds:02d}"


def _initial_valid_artifact_count(cycle_history: list[dict[str, object]]) -> int:
    if not cycle_history:
        return 0
    lifecycle = (cycle_history[0].get("fingerprint_lifecycle") or {})
    return int(lifecycle.get("valid_artifact_count") or 0)


def _first_training_cycle(cycle_history: list[dict[str, object]]) -> int | None:
    for cycle_entry in cycle_history:
        lifecycle = cycle_entry.get("fingerprint_lifecycle") or {}
        if "completed" in (lifecycle.get("training_events") or []):
            return int(cycle_entry.get("cycle_index") or 0)
    return None


def _latest_training_mode(lifecycle: dict[str, object]) -> str:
    training_events = list(lifecycle.get("training_events") or [])
    if "completed" in training_events:
        return "retrained_this_cycle"
    if "reused" in training_events:
        return "reused_existing_model"
    if "deferred" in training_events:
        return "training_deferred"
    return "not_available"


def _current_model_identity(
    lifecycle: dict[str, object],
    cycle_history: list[dict[str, object]],
) -> str | None:
    model_identity = lifecycle.get("model_metadata_object_key")
    if model_identity:
        return str(model_identity)
    for cycle_entry in reversed(cycle_history):
        candidate = (
            (cycle_entry.get("fingerprint_lifecycle") or {}).get("model_metadata_object_key")
        )
        if candidate:
            return str(candidate)
    return None


def _build_happened_already(
    *,
    current_cycle: int,
    latest_valid_artifact_count: int,
    first_training_cycle: int | None,
    latest_training_mode: str,
    current_model_identity: str | None,
    replay_behavior: dict[str, object],
) -> list[str]:
    happened = []
    if current_cycle > 0:
        happened.append(f"The runtime has completed {current_cycle} cycles in this run.")
    if latest_valid_artifact_count > 0:
        happened.append(
            f"The run has already persisted {latest_valid_artifact_count} valid artifacts."
        )
    if first_training_cycle is not None:
        happened.append(
            f"Fingerprint training first completed on cycle {first_training_cycle}."
        )
    if latest_training_mode == "reused_existing_model":
        happened.append("The current cycle reused the saved fingerprint model.")
    if current_model_identity is not None:
        happened.append(f"Current model identity: {current_model_identity}.")
    if replay_behavior:
        happened.append(
            "Replay-oriented anomaly behavior has already been observed in this run."
        )
    return happened or ["The runtime has not accumulated enough evidence yet."]


def _build_not_happened_yet(
    *,
    lifecycle: dict[str, object],
    first_training_cycle: int | None,
    replay_behavior: dict[str, object],
) -> list[str]:
    pending = []
    validation_level = str(
        lifecycle.get("source_dataset_validation_level") or "runtime_valid_only"
    )
    if first_training_cycle is None:
        pending.append("The first fingerprint training event has not happened yet.")
    if str(lifecycle.get("model_status") or "no_model_yet") != "model_available":
        pending.append("There is no reusable fingerprint model yet.")
    if not replay_behavior:
        pending.append("No replay-oriented anomaly is active in the current dashboard state.")
    if validation_level != "meaningful_fingerprint_valid":
        pending.append(
            "The run has not yet reached the agreed adequacy floor for a stronger "
            "fingerprint claim."
        )
    return pending


def _build_expected_next(
    *,
    lifecycle: dict[str, object],
    current_model_identity: str | None,
) -> dict[str, object]:
    eligible = int(lifecycle.get("eligible_history_count") or 0)
    threshold = int(lifecycle.get("eligible_history_threshold") or 0)
    training_events = list(lifecycle.get("training_events") or [])
    if "deferred" in training_events and threshold > eligible:
        remaining = threshold - eligible
        return {
            "summary": (
                f"Collect {remaining} more eligible normal-history cycles before the "
                "first fingerprint training can start."
            ),
            "evidence": {
                "eligible_history_count": eligible,
                "eligible_history_threshold": threshold,
            },
        }
    if "completed" in training_events:
        return {
            "summary": (
                "The next eligible cycle should reuse the newly trained model for "
                "inference rather than retraining immediately."
            ),
            "evidence": {"current_model_identity": current_model_identity},
        }
    if "reused" in training_events:
        return {
            "summary": (
                "The runtime should continue reusing the saved model on later eligible "
                "cycles unless the run is reset or a new training path is introduced."
            ),
            "evidence": {"current_model_identity": current_model_identity},
        }
    return {
        "summary": "Continue the run to accumulate more evidence in the dashboard.",
        "evidence": {},
    }


def _fingerprint_created_answer(
    *,
    lifecycle: dict[str, object],
    current_model_identity: str | None,
) -> str:
    if str(lifecycle.get("model_status") or "no_model_yet") == "model_available":
        return (
            "Yes. A fingerprint model already exists for this run and the dashboard can "
            f"trace it to {current_model_identity or 'the saved model metadata path'}."
        )
    return "No. The current run has not yet produced a reusable fingerprint model."


def _what_changed_answer(
    *,
    current_cycle: int,
    valid_artifact_growth: int,
    first_training_cycle: int | None,
    latest_training_mode: str,
) -> str:
    parts = [
        f"The runtime has advanced to cycle {current_cycle}.",
        f"Valid artifact growth is +{valid_artifact_growth}.",
    ]
    if first_training_cycle is not None:
        parts.append(f"Training first happened on cycle {first_training_cycle}.")
    if latest_training_mode == "reused_existing_model":
        parts.append("The current cycle reused the saved model.")
    elif latest_training_mode == "retrained_this_cycle":
        parts.append("The current cycle retrained the fingerprint model.")
    return " ".join(parts)


def _evidence_answer(
    *,
    current_model_identity: str | None,
    latest_valid_artifact_count: int,
    limitation_note: str,
) -> str:
    model_text = (
        f"Current model identity: {current_model_identity}."
        if current_model_identity
        else "No saved model identity is available yet."
    )
    return (
        f"The run currently shows {latest_valid_artifact_count} valid persisted artifacts. "
        f"{model_text} {limitation_note}"
    )
