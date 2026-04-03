"""Derived Story 5.4 demo-guidance panels for the dashboard."""

from __future__ import annotations


def build_dashboard_guidance_view(
    *,
    latest_runtime_payload: dict[str, object] | None,
    explainability: dict[str, object],
    limitation_note: str,
) -> dict[str, object]:
    """Build concise, demo-oriented guidance panels from existing state."""

    payload = latest_runtime_payload or {}
    runtime = payload.get("runtime") or {}
    latest_cycle = payload.get("latest_cycle") or {}
    lifecycle = latest_cycle.get("fingerprint_lifecycle") or {}
    consensus_summary = latest_cycle.get("consensus_summary") or {}
    replay_behavior = latest_cycle.get("replay_behavior") or {}
    scada_divergence = latest_cycle.get("scada_divergence_alert")
    explainability_state = explainability.get("what_changed_since_startup") or {}
    active_scenario = str(
        (latest_cycle.get("scenario_control") or {}).get("active_scenario") or "normal"
    )
    current_cycle = int(runtime.get("current_cycle") or 0)
    model_status = str(lifecycle.get("model_status") or "no_model_yet")
    consensus_status = str(
        consensus_summary.get("final_consensus_status") or "unknown"
    )

    what_is_happening = {
        "title": "What Is Happening",
        "summary": (
            f"The runtime is {runtime.get('status', 'inactive')} on cycle {current_cycle} "
            f"with scenario {active_scenario}. Consensus is {consensus_status}, and "
            f"the fingerprint lifecycle currently reports {model_status}."
        ),
        "bullets": _what_is_happening_bullets(
            active_scenario=active_scenario,
            consensus_status=consensus_status,
            lifecycle=lifecycle,
            replay_behavior=replay_behavior,
            scada_divergence=scada_divergence,
        ),
    }
    what_should_happen = {
        "title": "What Should Happen",
        "summary": (
            "Use these expectations to explain the normal path and the scenario-specific "
            "changes without collapsing the output channels together."
        ),
        "bullets": _what_should_happen_bullets(
            active_scenario=active_scenario,
            model_status=model_status,
        ),
    }
    what_changed = {
        "title": "What Changed",
        "summary": str(
            (explainability_state.get("questions_answered") or {}).get(
                "what_changed_since_startup"
            )
            or "No interpreted change summary is available yet."
        ),
        "bullets": _what_changed_bullets(explainability_state),
    }
    evidence_panel = {
        "title": "Evidence Signals",
        "summary": (
            "Use these signals to judge whether the prototype is behaving correctly in "
            "the current run."
        ),
        "bullets": _evidence_signal_bullets(
            explainability_state=explainability_state,
            replay_behavior=replay_behavior,
            scada_divergence=scada_divergence,
            limitation_note=limitation_note,
        ),
    }

    return {
        "panels": [
            what_is_happening,
            what_should_happen,
            what_changed,
            evidence_panel,
        ],
        "raw_evidence_note": (
            "These guidance panels summarize existing runtime state only. Use the "
            "component log explorer, channel panels, and raw logs below as ground truth."
        ),
    }


def _what_is_happening_bullets(
    *,
    active_scenario: str,
    consensus_status: str,
    lifecycle: dict[str, object],
    replay_behavior: dict[str, object],
    scada_divergence: object,
) -> list[str]:
    bullets = [
        f"Active scenario: {active_scenario}.",
        f"Consensus channel currently reports: {consensus_status}.",
        f"Fingerprint lifecycle status: {lifecycle.get('inference_status') or 'not_available'}.",
    ]
    if replay_behavior:
        bullets.append(
            "Replay behavior is currently visible through the fingerprint/replay channel."
        )
    else:
        bullets.append(
            "Replay behavior is not currently active in the fingerprint/replay channel."
        )
    if scada_divergence is not None:
        bullets.append(
            "SCADA divergence is currently active as a direct comparison signal."
        )
    else:
        bullets.append(
            "SCADA divergence is currently clear in the direct comparison channel."
        )
    return bullets


def _what_should_happen_bullets(
    *,
    active_scenario: str,
    model_status: str,
) -> list[str]:
    bullets = [
        "Normal operation should keep edges aligned, let consensus succeed, and keep valid artifacts accumulating over time.",
        "Replay or freeze should show up through the fingerprint/replay behavior path rather than pretending to be a consensus failure.",
        "SCADA divergence should appear in the SCADA comparison channel without redefining the consensus result.",
    ]
    if model_status == "model_available":
        bullets.append(
            "A saved model already exists, so later cycles should normally reuse it rather than retraining every cycle."
        )
    else:
        bullets.append(
            "Training should remain deferred until enough eligible history exists."
        )
    if active_scenario != "normal":
        bullets.append(
            f"The current scenario emphasis is {active_scenario}, so the operator should watch the matching channel reaction first."
        )
    return bullets


def _what_changed_bullets(explainability_state: dict[str, object]) -> list[str]:
    bullets = []
    bullets.extend(list(explainability_state.get("happened_already") or []))
    not_yet = list(explainability_state.get("not_happened_yet") or [])
    if not_yet:
        bullets.append("Pending or not yet observed:")
        bullets.extend(not_yet)
    expected_next = (explainability_state.get("expected_next") or {}).get("summary")
    if expected_next:
        bullets.append(f"Expected next: {expected_next}")
    return bullets or ["No interpreted startup-to-now change evidence is available yet."]


def _evidence_signal_bullets(
    *,
    explainability_state: dict[str, object],
    replay_behavior: dict[str, object],
    scada_divergence: object,
    limitation_note: str,
) -> list[str]:
    evidence = [
        str(
            (explainability_state.get("questions_answered") or {}).get(
                "what_evidence_exists_in_this_run"
            )
            or "No interpreted evidence summary is available yet."
        ),
        limitation_note,
    ]
    if replay_behavior:
        evidence.append(
            f"Replay channel classification: {replay_behavior.get('classification') or 'unknown'}."
        )
    if scada_divergence is not None:
        evidence.append(
            "SCADA divergence channel is active, so direct comparison mismatch is currently observable."
        )
    return evidence
