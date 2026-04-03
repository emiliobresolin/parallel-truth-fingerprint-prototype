"""Derived Story 5.3 explainability and evidence views for the dashboard."""

from __future__ import annotations

from datetime import datetime, timezone

from parallel_truth_fingerprint.dashboard.runtime_binding import (
    extract_divergent_sensors,
)
from parallel_truth_fingerprint.lstm_service.dataset_artifacts import (
    DATASET_PREFIX,
    DEFAULT_MIN_ELIGIBLE_ARTIFACT_COUNT,
    DEFAULT_MIN_WINDOW_COUNT,
)


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
    artifact_json_loader=None,
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
    replay_inference_results = latest_cycle.get("replay_inference_results") or []
    comparison_output = latest_cycle.get("comparison_output") or {}
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
    current_dataset_manifest_key = _current_dataset_manifest_key(lifecycle, cycle_history)
    current_dataset_manifest = _load_json_artifact(
        current_dataset_manifest_key,
        artifact_json_loader=artifact_json_loader,
    )
    current_model_metadata = _load_json_artifact(
        current_model_identity,
        artifact_json_loader=artifact_json_loader,
    )
    source_dataset_manifest_key = _source_dataset_manifest_key(
        lifecycle=lifecycle,
        current_model_metadata=current_model_metadata,
    )
    source_dataset_manifest = _load_json_artifact(
        source_dataset_manifest_key,
        artifact_json_loader=artifact_json_loader,
    )
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
    fingerprint_readiness = _build_fingerprint_readiness(
        lifecycle=lifecycle,
        operator_actions=operator_actions,
        fingerprint_results=fingerprint_results,
        replay_behavior=replay_behavior,
        replay_inference_results=replay_inference_results,
        comparison_output=comparison_output,
        source_dataset_manifest=source_dataset_manifest,
        source_dataset_manifest_key=source_dataset_manifest_key,
        current_dataset_manifest=current_dataset_manifest,
        current_dataset_manifest_key=current_dataset_manifest_key,
        current_model_metadata=current_model_metadata,
        current_model_identity=current_model_identity,
        latest_training_mode=latest_training_mode,
        first_training_cycle=first_training_cycle,
        limitation_note=limitation_note,
        validation_level=validation_level,
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
        "fingerprint_readiness": fingerprint_readiness,
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


def _build_fingerprint_readiness(
    *,
    lifecycle: dict[str, object],
    operator_actions: list[dict[str, object]],
    fingerprint_results: list[dict[str, object]],
    replay_behavior: dict[str, object],
    replay_inference_results: list[dict[str, object]],
    comparison_output: dict[str, object],
    source_dataset_manifest: dict[str, object] | None,
    source_dataset_manifest_key: str | None,
    current_dataset_manifest: dict[str, object] | None,
    current_dataset_manifest_key: str | None,
    current_model_metadata: dict[str, object] | None,
    current_model_identity: str | None,
    latest_training_mode: str,
    first_training_cycle: int | None,
    limitation_note: str,
    validation_level: str,
) -> dict[str, object]:
    adequacy_source = source_dataset_manifest or current_dataset_manifest or {}
    adequacy_assessment = adequacy_source.get("adequacy_assessment") or {}
    eligible_artifact_count = int(
        adequacy_assessment.get("eligible_artifact_count")
        or lifecycle.get("eligible_history_count")
        or 0
    )
    window_count = int(
        adequacy_assessment.get("window_count")
        or adequacy_source.get("window_count")
        or lifecycle.get("window_count")
        or 0
    )
    minimum_eligible = int(
        adequacy_assessment.get("minimum_eligible_artifact_count")
        or DEFAULT_MIN_ELIGIBLE_ARTIFACT_COUNT
    )
    minimum_windows = int(
        adequacy_assessment.get("minimum_window_count")
        or DEFAULT_MIN_WINDOW_COUNT
    )
    threshold_origin = _threshold_origin(
        fingerprint_results=fingerprint_results,
        replay_inference_results=replay_inference_results,
    )
    classification_threshold = _classification_threshold(
        fingerprint_results=fingerprint_results,
        replay_behavior=replay_behavior,
    )
    readiness_state = _readiness_state(
        validation_level=validation_level,
        current_model_identity=current_model_identity,
    )
    provenance = {
        "model_identity": current_model_identity or "not_available",
        "model_id": _string_or_default(
            (current_model_metadata or {}).get("model_id"),
        ),
        "source_dataset_id": _string_or_default(
            (current_model_metadata or {}).get("source_dataset_id")
            or (adequacy_source or {}).get("dataset_id"),
        ),
        "source_dataset_manifest_key": _string_or_default(source_dataset_manifest_key),
        "current_dataset_manifest_key": _string_or_default(current_dataset_manifest_key),
        "training_window_count": _string_or_default(
            (current_model_metadata or {}).get("training_window_count"),
        ),
        "threshold_origin": _string_or_default(threshold_origin),
        "classification_threshold": _string_or_default(classification_threshold),
        "current_limitation": limitation_note,
    }
    training_details = {
        "first_training_reference": _string_or_default(
            None if first_training_cycle is None else f"cycle {first_training_cycle}"
        ),
        "current_model_usage": latest_training_mode,
        "trained_at": _string_or_default(
            (current_model_metadata or {}).get("created_at"),
        ),
        "epochs": _string_or_default((current_model_metadata or {}).get("epochs")),
        "batch_size": _string_or_default(
            (current_model_metadata or {}).get("batch_size"),
        ),
        "loss_name": _string_or_default(
            (current_model_metadata or {}).get("loss_name"),
        ),
        "final_training_loss": _string_or_default(
            (current_model_metadata or {}).get("final_training_loss"),
        ),
        "sequence_length": _string_or_default(
            (current_model_metadata or {}).get("sequence_length"),
        ),
        "feature_schema": _feature_schema_text(
            (current_model_metadata or {}).get("feature_schema"),
        ),
    }
    working_now = _readiness_working_now(
        current_model_identity=current_model_identity,
        threshold_origin=threshold_origin,
        fingerprint_results=fingerprint_results,
        replay_behavior=replay_behavior,
    )
    evidence_available = _readiness_evidence_available(
        provenance=provenance,
        eligible_artifact_count=eligible_artifact_count,
        minimum_eligible=minimum_eligible,
        window_count=window_count,
        minimum_windows=minimum_windows,
    )
    not_proven_yet = _readiness_not_proven_yet(
        current_model_identity=current_model_identity,
        validation_level=validation_level,
        minimum_eligible=minimum_eligible,
        minimum_windows=minimum_windows,
    )
    evidence_matrix = _build_evidence_matrix(
        operator_actions=operator_actions,
        fingerprint_results=fingerprint_results,
        replay_behavior=replay_behavior,
        comparison_output=comparison_output,
        validation_level=validation_level,
        threshold_origin=threshold_origin,
        limitation_note=limitation_note,
    )
    return {
        "summary": readiness_state["summary"],
        "readiness_state": readiness_state,
        "adequacy_gate": {
            "validation_level": validation_level,
            "label": readiness_state["label"],
            "eligible_artifact_count": eligible_artifact_count,
            "minimum_eligible_artifact_count": minimum_eligible,
            "window_count": window_count,
            "minimum_window_count": minimum_windows,
            "adequacy_met": validation_level == "meaningful_fingerprint_valid",
            "summary": (
                f"Source dataset evidence: {eligible_artifact_count}/{minimum_eligible} eligible artifacts "
                f"and {window_count}/{minimum_windows} temporal windows."
            ),
        },
        "provenance": provenance,
        "training_details": training_details,
        "working_now": working_now,
        "evidence_available": evidence_available,
        "not_proven_yet": not_proven_yet,
        "evidence_matrix": evidence_matrix,
    }


def _readiness_state(
    *,
    validation_level: str,
    current_model_identity: str | None,
) -> dict[str, str]:
    if validation_level == "meaningful_fingerprint_valid":
        return {
            "raw_value": validation_level,
            "label": "Fingerprint readiness target met",
            "summary": (
                "The saved fingerprint model is backed by a dataset that meets the agreed "
                "adequacy floor."
            ),
            "explanation": (
                "The current model and its source dataset satisfy the stronger adequacy gate "
                "for a more defensible fingerprint claim."
            ),
        }
    if current_model_identity:
        return {
            "raw_value": validation_level,
            "label": "Runtime-valid only: fingerprint pipeline works, but readiness is still below target",
            "summary": (
                "A saved fingerprint model exists and the inference path is operating, but "
                "the source dataset remains below the stronger adequacy floor."
            ),
            "explanation": RUNTIME_VALID_ONLY_EXPLANATION,
        }
    return {
        "raw_value": validation_level,
        "label": "Fingerprint training evidence is still being accumulated",
        "summary": (
            "The prototype is still gathering normal-history evidence before a reusable "
            "fingerprint model can support the demo."
        ),
        "explanation": RUNTIME_VALID_ONLY_EXPLANATION,
    }


def _current_dataset_manifest_key(
    lifecycle: dict[str, object],
    cycle_history: list[dict[str, object]],
) -> str | None:
    manifest_key = lifecycle.get("dataset_manifest_object_key")
    if manifest_key:
        return str(manifest_key)
    for cycle_entry in reversed(cycle_history):
        candidate = (
            (cycle_entry.get("fingerprint_lifecycle") or {}).get("dataset_manifest_object_key")
        )
        if candidate:
            return str(candidate)
    return None


def _source_dataset_manifest_key(
    *,
    lifecycle: dict[str, object],
    current_model_metadata: dict[str, object] | None,
) -> str | None:
    source_dataset_id = (current_model_metadata or {}).get("source_dataset_id")
    if source_dataset_id:
        return f"{DATASET_PREFIX}{source_dataset_id}.manifest.json"
    manifest_key = lifecycle.get("dataset_manifest_object_key")
    return None if manifest_key is None else str(manifest_key)


def _load_json_artifact(
    object_key: str | None,
    *,
    artifact_json_loader,
) -> dict[str, object] | None:
    if not object_key or artifact_json_loader is None:
        return None
    try:
        payload = artifact_json_loader(str(object_key))
    except Exception:
        return None
    if not isinstance(payload, dict):
        return None
    return payload


def _threshold_origin(
    *,
    fingerprint_results: list[dict[str, object]],
    replay_inference_results: list[dict[str, object]],
) -> str | None:
    for result in list(fingerprint_results) + list(replay_inference_results):
        threshold_origin = result.get("threshold_origin")
        if threshold_origin:
            return str(threshold_origin)
    return None


def _classification_threshold(
    *,
    fingerprint_results: list[dict[str, object]],
    replay_behavior: dict[str, object],
) -> float | None:
    if fingerprint_results:
        threshold = fingerprint_results[0].get("classification_threshold")
        if threshold is not None:
            return float(threshold)
    threshold = replay_behavior.get("classification_threshold")
    if threshold is not None:
        return float(threshold)
    return None


def _feature_schema_text(feature_schema: object) -> str:
    if not feature_schema:
        return "not_available"
    return ", ".join(str(item) for item in feature_schema)


def _string_or_default(value: object) -> str:
    if value in (None, "", [], (), {}):
        return "not_available"
    return str(value)


def _readiness_working_now(
    *,
    current_model_identity: str | None,
    threshold_origin: str | None,
    fingerprint_results: list[dict[str, object]],
    replay_behavior: dict[str, object],
) -> list[str]:
    items = []
    if current_model_identity:
        items.append("A saved fingerprint model is available for reuse in the current run.")
    if threshold_origin:
        items.append(f"The anomaly decision threshold is traced to {threshold_origin}.")
    if fingerprint_results:
        items.append(
            "The generic fingerprint path is producing inference results for the current run."
        )
    if replay_behavior:
        items.append(
            "Replay or freeze behavior is being evaluated through the fingerprint path and kept separate from SCADA divergence."
        )
    return items or ["The run has not yet produced enough fingerprint evidence to show active readiness."]


def _readiness_evidence_available(
    *,
    provenance: dict[str, str],
    eligible_artifact_count: int,
    minimum_eligible: int,
    window_count: int,
    minimum_windows: int,
) -> list[str]:
    items = [
        (
            "Adequacy evidence is available: "
            f"{eligible_artifact_count}/{minimum_eligible} eligible artifacts and "
            f"{window_count}/{minimum_windows} windows."
        )
    ]
    if provenance["model_identity"] != "not_available":
        items.append(f"Model metadata path: {provenance['model_identity']}.")
    if provenance["source_dataset_id"] != "not_available":
        items.append(f"Source training dataset: {provenance['source_dataset_id']}.")
    if provenance["training_window_count"] != "not_available":
        items.append(
            f"Saved training window count: {provenance['training_window_count']}."
        )
    if provenance["threshold_origin"] != "not_available":
        items.append(f"Threshold origin: {provenance['threshold_origin']}.")
    return items


def _readiness_not_proven_yet(
    *,
    current_model_identity: str | None,
    validation_level: str,
    minimum_eligible: int,
    minimum_windows: int,
) -> list[str]:
    items = []
    if current_model_identity is None:
        items.append("A reusable fingerprint model has not been created yet.")
    if validation_level != "meaningful_fingerprint_valid":
        items.append(
            "The current fingerprint base is still runtime-valid only and has not met the "
            f"stronger adequacy floor of {minimum_eligible} eligible artifacts and {minimum_windows} windows."
        )
    items.append(
        "The prototype can show anomaly evidence, but it does not yet prove academically strong generalization from the current dataset."
    )
    return items


def _build_evidence_matrix(
    *,
    operator_actions: list[dict[str, object]],
    fingerprint_results: list[dict[str, object]],
    replay_behavior: dict[str, object],
    comparison_output: dict[str, object],
    validation_level: str,
    threshold_origin: str | None,
    limitation_note: str,
) -> list[dict[str, object]]:
    latest_fingerprint = fingerprint_results[0] if fingerprint_results else {}
    power_actions = [
        action
        for action in operator_actions
        if action.get("action") == "set_power"
    ]
    scenario_actions = [
        action
        for action in operator_actions
        if action.get("action") == "set_scenario"
    ]
    divergent_sensors = extract_divergent_sensors(comparison_output)

    normal_status = (
        "Observed"
        if fingerprint_results and not replay_behavior
        else "Not observed yet"
    )
    power_status = "Observed in this run" if power_actions else "Not exercised yet"
    replay_status = (
        "Observed through fingerprint path"
        if replay_behavior
        else (
            "Scenario configured but not currently observed"
            if any(
                (action.get("configuration_change") or {}).get("demo_scenario_name")
                in {"scada_replay", "scada_freeze"}
                for action in scenario_actions
            )
            else "Not exercised yet"
        )
    )
    divergence_status = (
        "Observed as a separate supervisory channel"
        if divergent_sensors
        else (
            "Scenario configured but not currently divergent"
            if any(
                (action.get("configuration_change") or {}).get("demo_scenario_name")
                == "scada_divergence"
                for action in scenario_actions
            )
            else "Not exercised yet"
        )
    )
    return [
        {
            "id": "normal_operation",
            "label": "Normal operation",
            "status": normal_status,
            "summary": (
                "The generic fingerprint path is evaluating normal-history windows from the current run."
                if fingerprint_results
                else "The run has not yet produced a generic fingerprint result for a normal-history window."
            ),
            "evidence": [
                f"classification={latest_fingerprint.get('classification', 'not_available')}",
                f"threshold_origin={threshold_origin or 'not_available'}",
                f"validation_level={validation_level}",
            ],
        },
        {
            "id": "power_variation",
            "label": "Compressor-power variation",
            "status": power_status,
            "summary": (
                "Operator-applied power changes can now be compared against resulting sensor behavior and the fingerprint output."
                if power_actions
                else "No power change has been applied in this run yet."
            ),
            "evidence": [
                f"power_changes={len(power_actions)}",
                limitation_note,
            ],
        },
        {
            "id": "replay_or_freeze",
            "label": "Replay / freeze behavior",
            "status": replay_status,
            "summary": (
                "Replay or freeze behavior is being evaluated through the fingerprint path."
                if replay_behavior
                else "Replay or freeze behavior has not been observed in the current dashboard state."
            ),
            "evidence": [
                f"classification={replay_behavior.get('classification', 'not_available')}",
                f"scenario_mode={replay_behavior.get('scenario_mode', 'not_available')}",
                f"anomaly_score={replay_behavior.get('anomaly_score', 'not_available')}",
            ],
        },
        {
            "id": "scada_divergence",
            "label": "SCADA divergence",
            "status": divergence_status,
            "summary": (
                "SCADA divergence remains a supervisory comparison channel, not a fingerprint channel."
            ),
            "evidence": [
                "This channel is intentionally separate from replay detection.",
                "divergent_sensors="
                + (", ".join(divergent_sensors) if divergent_sensors else "none"),
            ],
        },
    ]
