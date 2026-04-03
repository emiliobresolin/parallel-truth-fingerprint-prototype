"""Derived Story 5.1 event and raw-log views for the local dashboard."""

from __future__ import annotations

from collections import defaultdict

from parallel_truth_fingerprint.dashboard.runtime_binding import (
    extract_divergent_sensors,
    extract_structured_comparison_output,
)


COMPONENT_DEFINITIONS = (
    {"id": "compressor", "label": "Compressor"},
    {"id": "temperature_sensor", "label": "Temperature Sensor"},
    {"id": "pressure_sensor", "label": "Pressure Sensor"},
    {"id": "rpm_sensor", "label": "RPM Sensor"},
    {"id": "edge_1", "label": "Edge 1"},
    {"id": "edge_2", "label": "Edge 2"},
    {"id": "edge_3", "label": "Edge 3"},
    {"id": "consensus", "label": "Consensus"},
    {"id": "scada_comparison", "label": "SCADA Comparison"},
    {"id": "fingerprint_lifecycle", "label": "Fingerprint / LSTM Lifecycle"},
)
COMPONENT_LABELS = {
    definition["id"]: definition["label"] for definition in COMPONENT_DEFINITIONS
}
COMPONENT_IDS = tuple(COMPONENT_LABELS)
SENSOR_COMPONENTS = (
    ("temperature_sensor", "temperature"),
    ("pressure_sensor", "pressure"),
    ("rpm_sensor", "rpm"),
)
EDGE_COMPONENT_MAP = {
    "edge-1": "edge_1",
    "edge-2": "edge_2",
    "edge-3": "edge_3",
}
GROUND_TRUTH_NOTE = (
    "Raw component logs are derived directly from the current runtime payload and "
    "remain the technical ground truth for this dashboard view."
)


def build_dashboard_event_views(
    *,
    generated_at: str,
    latest_runtime_payload: dict[str, object] | None,
    operator_actions: list[dict[str, object]],
) -> dict[str, object]:
    """Build global and component-scoped Story 5.1 views."""

    payload = latest_runtime_payload or {}
    latest_cycle = payload.get("latest_cycle") or {}
    cycle_history = payload.get("cycle_history") or []

    raw_logs = _build_component_raw_logs(latest_cycle=latest_cycle)
    event_entries = []
    event_entries.extend(_build_operator_action_events(operator_actions))
    event_entries.extend(
        _build_cycle_history_events(
            cycle_history=cycle_history,
            generated_at=generated_at,
        )
    )
    event_entries.extend(
        _build_latest_cycle_component_events(
            latest_cycle=latest_cycle,
            generated_at=generated_at,
        )
    )

    sorted_events = sorted(
        event_entries,
        key=lambda event: (int(event.get("cycle_index") or 0), int(event["sort_index"])),
        reverse=True,
    )
    component_timelines: dict[str, list[dict[str, object]]] = defaultdict(list)
    global_timeline: list[dict[str, object]] = []
    for event in sorted_events:
        public_event = {
            key: value for key, value in event.items() if key != "sort_index"
        }
        global_timeline.append(public_event)
        component_id = event.get("component")
        if component_id in COMPONENT_LABELS:
            component_timelines[component_id].append(public_event)

    for component_id in COMPONENT_IDS:
        if component_timelines[component_id]:
            continue
        component_timelines[component_id] = [
            _fallback_event(
                component_id=component_id,
                generated_at=generated_at,
            )
        ]

    return {
        "components": list(COMPONENT_DEFINITIONS),
        "global_timeline": global_timeline,
        "component_timelines": dict(component_timelines),
        "component_raw_logs": raw_logs,
        "raw_log_ground_truth_note": GROUND_TRUTH_NOTE,
    }


def _build_component_raw_logs(*, latest_cycle: dict[str, object]) -> dict[str, object]:
    simulator_snapshot = latest_cycle.get("simulator_snapshot") or {}
    scada_state = latest_cycle.get("scada_state") or {}
    comparison_output = latest_cycle.get("comparison_output") or {}
    consensus_log = latest_cycle.get("consensus_log") or {}
    edges = latest_cycle.get("edges") or []

    raw_logs: dict[str, object] = {
        "compressor": _with_fallback(
            {
                "simulator_snapshot": simulator_snapshot,
                "runtime_cycle": latest_cycle.get("runtime_cycle"),
            },
            component_id="compressor",
        ),
        "consensus": _with_fallback(
            {
                "summary": latest_cycle.get("consensus_summary"),
                "log": consensus_log,
                "alert": latest_cycle.get("consensus_alert"),
                "committed_round_state": latest_cycle.get("committed_round_state"),
            },
            component_id="consensus",
        ),
        "scada_comparison": _with_fallback(
            {
                "scada_state": scada_state,
                "comparison_output": comparison_output,
                "divergence_alert": latest_cycle.get("scada_divergence_alert"),
                "runtime_scenario": latest_cycle.get("scada_runtime_scenario"),
            },
            component_id="scada_comparison",
        ),
        "fingerprint_lifecycle": _with_fallback(
            {
                "lifecycle": latest_cycle.get("fingerprint_lifecycle"),
                "fingerprint_inference_results": latest_cycle.get(
                    "fingerprint_inference_results"
                ),
                "replay_behavior": latest_cycle.get("replay_behavior"),
                "replay_inference_results": latest_cycle.get(
                    "replay_inference_results"
                ),
            },
            component_id="fingerprint_lifecycle",
        ),
    }

    for component_id, sensor_name in SENSOR_COMPONENTS:
        raw_logs[component_id] = _with_fallback(
            {
                "sensor_name": sensor_name,
                "simulator_value": (simulator_snapshot.get("sensors") or {}).get(
                    sensor_name
                ),
                "transmitter_observation": (
                    (simulator_snapshot.get("transmitter_observations") or {}).get(
                        sensor_name
                    )
                ),
            },
            component_id=component_id,
        )

    raw_edge_logs = {
        EDGE_COMPONENT_MAP[edge["runtime_state"]["edge_id"]]: edge
        for edge in edges
        if (edge.get("runtime_state") or {}).get("edge_id") in EDGE_COMPONENT_MAP
    }
    for component_id in ("edge_1", "edge_2", "edge_3"):
        raw_logs[component_id] = _with_fallback(
            raw_edge_logs.get(component_id, {}),
            component_id=component_id,
        )

    return raw_logs


def _build_operator_action_events(
    operator_actions: list[dict[str, object]],
) -> list[dict[str, object]]:
    events: list[dict[str, object]] = []
    for index, action in enumerate(reversed(operator_actions), start=1):
        component_id = _resolve_action_component(action)
        applies_on_cycle = int(action.get("applies_on_cycle") or 0)
        runtime_reference = f"planned cycle {applies_on_cycle}" if applies_on_cycle else "operator action"
        events.append(
            _event(
                component_id=component_id,
                cycle_index=applies_on_cycle,
                recorded_at=str(action.get("applied_at") or ""),
                runtime_reference=runtime_reference,
                message=_describe_action(action),
                source="operator_action",
                sort_index=index,
            )
        )
    return events


def _build_cycle_history_events(
    *,
    cycle_history: list[dict[str, object]],
    generated_at: str,
) -> list[dict[str, object]]:
    events: list[dict[str, object]] = []
    for index, cycle_entry in enumerate(cycle_history, start=100):
        cycle_index = int(cycle_entry.get("cycle_index") or 0)
        scenario_control = cycle_entry.get("scenario_control") or {}
        fingerprint_lifecycle = cycle_entry.get("fingerprint_lifecycle") or {}
        replay_behavior = cycle_entry.get("replay_behavior")
        events.append(
            _event(
                component_id="consensus",
                cycle_index=cycle_index,
                recorded_at=generated_at,
                runtime_reference=f"cycle {cycle_index}",
                message=(
                    "Consensus "
                    f"{cycle_entry.get('final_consensus_status', 'unknown')} "
                    f"for round {cycle_entry.get('round_id', 'unknown')}."
                ),
                source="cycle_history",
                sort_index=index,
            )
        )
        events.append(
            _event(
                component_id="fingerprint_lifecycle",
                cycle_index=cycle_index,
                recorded_at=generated_at,
                runtime_reference=f"cycle {cycle_index}",
                message=_describe_fingerprint_history(fingerprint_lifecycle),
                source="cycle_history",
                sort_index=index + 100,
            )
        )
        events.append(
            _event(
                component_id="scada_comparison",
                cycle_index=cycle_index,
                recorded_at=generated_at,
                runtime_reference=f"cycle {cycle_index}",
                message=_describe_scada_history(
                    scenario_control=scenario_control,
                    replay_behavior=replay_behavior,
                ),
                source="cycle_history",
                sort_index=index + 200,
            )
        )
    return events


def _build_latest_cycle_component_events(
    *,
    latest_cycle: dict[str, object],
    generated_at: str,
) -> list[dict[str, object]]:
    if not latest_cycle:
        return []

    events: list[dict[str, object]] = []
    cycle_index = int(
        (latest_cycle.get("runtime_cycle") or {}).get("current_cycle")
        or (latest_cycle.get("fingerprint_lifecycle") or {}).get("cycle_index")
        or 0
    )
    runtime_reference = f"cycle {cycle_index}" if cycle_index else "latest runtime state"
    simulator_snapshot = latest_cycle.get("simulator_snapshot") or {}
    sensors = simulator_snapshot.get("sensors") or {}
    transmitter_observations = simulator_snapshot.get("transmitter_observations") or {}
    edges = latest_cycle.get("edges") or []
    comparison_output = latest_cycle.get("comparison_output") or {}
    structured_comparison = extract_structured_comparison_output(comparison_output)
    consensus_summary = latest_cycle.get("consensus_summary") or {}
    fingerprint_lifecycle = latest_cycle.get("fingerprint_lifecycle") or {}
    replay_behavior = latest_cycle.get("replay_behavior") or {}

    if simulator_snapshot:
        events.append(
            _event(
                component_id="compressor",
                cycle_index=cycle_index,
                recorded_at=generated_at,
                runtime_reference=runtime_reference,
                message=(
                    f"Compressor operating at {simulator_snapshot.get('operating_state_pct')}% "
                    f"with live sensor values {sensors}."
                ),
                source="latest_cycle",
                sort_index=500,
            )
        )
    for order, (component_id, sensor_name) in enumerate(SENSOR_COMPONENTS, start=1):
        sensor_value = sensors.get(sensor_name)
        transmitter_observation = transmitter_observations.get(sensor_name) or {}
        unit = ((transmitter_observation.get("pv") or {}).get("unit")) or ""
        if sensor_value is None and not transmitter_observation:
            continue
        value_with_unit = _format_value_with_unit(sensor_value, unit)
        message = f"{COMPONENT_LABELS[component_id]} reported {value_with_unit} on {runtime_reference}."
        events.append(
            _event(
                component_id=component_id,
                cycle_index=cycle_index,
                recorded_at=generated_at,
                runtime_reference=runtime_reference,
                message=message,
                source="latest_cycle",
                sort_index=500 + order,
            )
        )
    for order, edge in enumerate(edges, start=1):
        runtime_state = edge.get("runtime_state") or {}
        edge_id = runtime_state.get("edge_id")
        component_id = EDGE_COMPONENT_MAP.get(edge_id)
        if component_id is None:
            continue
        events.append(
            _event(
                component_id=component_id,
                cycle_index=cycle_index,
                recorded_at=generated_at,
                runtime_reference=runtime_reference,
                message=edge.get("summary")
                or (
                    f"{COMPONENT_LABELS[component_id]} published "
                    f"{runtime_state.get('published_observation_count', 0)} "
                    "observations on the latest cycle."
                ),
                source="latest_cycle",
                sort_index=520 + order,
            )
        )
    if consensus_summary:
        events.append(
            _event(
                component_id="consensus",
                cycle_index=cycle_index,
                recorded_at=generated_at,
                runtime_reference=runtime_reference,
                message=(
                    "Consensus "
                    f"{consensus_summary.get('final_consensus_status', 'unknown')} "
                    f"committed round {consensus_summary.get('round_id', 'unknown')}."
                ),
                source="latest_cycle",
                sort_index=540,
            )
        )
    if structured_comparison:
        divergent_sensors = extract_divergent_sensors(comparison_output)
        message = (
            "SCADA comparison reports divergence on "
            f"{', '.join(divergent_sensors)}."
            if divergent_sensors
            else "SCADA comparison reports that all monitored sensors match the consensused state."
        )
        events.append(
            _event(
                component_id="scada_comparison",
                cycle_index=cycle_index,
                recorded_at=generated_at,
                runtime_reference=runtime_reference,
                message=message,
                source="latest_cycle",
                sort_index=541,
            )
        )
    if fingerprint_lifecycle:
        events.append(
            _event(
                component_id="fingerprint_lifecycle",
                cycle_index=cycle_index,
                recorded_at=generated_at,
                runtime_reference=runtime_reference,
                message=_describe_latest_fingerprint_state(
                    fingerprint_lifecycle=fingerprint_lifecycle,
                    replay_behavior=replay_behavior,
                ),
                source="latest_cycle",
                sort_index=542,
            )
        )
    return events


def _event(
    *,
    component_id: str,
    cycle_index: int,
    recorded_at: str,
    runtime_reference: str,
    message: str,
    source: str,
    sort_index: int,
) -> dict[str, object]:
    return {
        "event_id": f"{component_id}:{source}:{cycle_index}:{sort_index}",
        "component": component_id,
        "component_label": COMPONENT_LABELS.get(component_id, "Global"),
        "cycle_index": cycle_index,
        "recorded_at": recorded_at,
        "runtime_reference": runtime_reference,
        "message": message,
        "source": source,
        "sort_index": sort_index,
    }


def _fallback_event(*, component_id: str, generated_at: str) -> dict[str, object]:
    return {
        "event_id": f"{component_id}:not-available",
        "component": component_id,
        "component_label": COMPONENT_LABELS[component_id],
        "cycle_index": 0,
        "recorded_at": generated_at,
        "runtime_reference": "not_started",
        "message": f"No runtime data is available yet for {COMPONENT_LABELS[component_id]}.",
        "source": "dashboard_state",
    }


def _with_fallback(payload: dict[str, object], *, component_id: str) -> dict[str, object]:
    has_signal = any(
        value not in (None, "", (), [], {})
        for value in payload.values()
    )
    if has_signal:
        return payload
    return {
        "status": "not_available",
        "note": f"No raw runtime data is available yet for {COMPONENT_LABELS[component_id]}.",
    }


def _resolve_action_component(action: dict[str, object]) -> str:
    action_name = str(action.get("action") or "")
    if action_name == "set_power":
        return "compressor"
    if action_name == "set_scenario":
        scenario_name = str(
            (action.get("configuration_change") or {}).get("demo_scenario_name") or ""
        )
        if scenario_name.startswith("scada_"):
            return "scada_comparison"
        if scenario_name in {"single_edge_exclusion", "quorum_loss"}:
            return "consensus"
    return "fingerprint_lifecycle"


def _describe_action(action: dict[str, object]) -> str:
    action_name = str(action.get("action") or "unknown_action")
    configuration_change = action.get("configuration_change") or {}
    if action_name == "set_power":
        return (
            "Operator set compressor power to "
            f"{configuration_change.get('demo_power')}%."
        )
    if action_name == "set_scenario":
        return (
            "Operator activated scenario "
            f"{configuration_change.get('demo_scenario_name', 'unknown')}."
        )
    if action_name == "start_runtime":
        return "Operator started the autonomous runtime."
    if action_name == "stop_runtime":
        return "Operator requested the autonomous runtime to stop."
    if action_name == "runtime_error":
        return str(action.get("note") or "Runtime error recorded.")
    return str(action.get("note") or action_name)


def _describe_fingerprint_history(fingerprint_lifecycle: dict[str, object]) -> str:
    training_events = list(fingerprint_lifecycle.get("training_events") or [])
    training_summary = ", ".join(training_events) if training_events else "none"
    return (
        "Fingerprint lifecycle "
        f"model_status={fingerprint_lifecycle.get('model_status', 'unknown')}, "
        f"training_events={training_summary}, "
        f"inference_status={fingerprint_lifecycle.get('inference_status', 'unknown')}."
    )


def _describe_scada_history(
    *,
    scenario_control: dict[str, object],
    replay_behavior: dict[str, object] | None,
) -> str:
    active_scenario = scenario_control.get("active_scenario", "normal")
    if replay_behavior is not None:
        return (
            "Replay behavior classified the latest SCADA-side state as "
            f"{replay_behavior.get('classification', 'unknown')} "
            f"under {replay_behavior.get('scenario_mode', 'unknown')} mode."
        )
    if active_scenario == "scada_divergence":
        return "SCADA comparison is running in explicit divergence mode."
    if active_scenario in {"scada_replay", "scada_freeze"}:
        return f"SCADA comparison is preparing {active_scenario} behavior."
    return "SCADA comparison is monitoring the latest consensused state."


def _describe_latest_fingerprint_state(
    *,
    fingerprint_lifecycle: dict[str, object],
    replay_behavior: dict[str, object],
) -> str:
    model_status = fingerprint_lifecycle.get("model_status", "unknown")
    inference_status = fingerprint_lifecycle.get("inference_status", "unknown")
    training_events = ", ".join(fingerprint_lifecycle.get("training_events") or []) or "none"
    if replay_behavior:
        return (
            "Fingerprint lifecycle "
            f"model_status={model_status}, inference_status={inference_status}, "
            f"training_events={training_events}, replay_classification="
            f"{replay_behavior.get('classification', 'unknown')}."
        )
    return (
        "Fingerprint lifecycle "
        f"model_status={model_status}, inference_status={inference_status}, "
        f"training_events={training_events}."
    )


def _format_value_with_unit(value: object, unit: str) -> str:
    rendered_value = "n/a" if value is None else str(value)
    return rendered_value if not unit else f"{rendered_value} {unit}"
