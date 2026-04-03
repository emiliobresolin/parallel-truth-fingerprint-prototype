"""Derived Story 5.2 visual pipeline view for the local dashboard."""

from __future__ import annotations

from parallel_truth_fingerprint.dashboard.event_timeline import COMPONENT_LABELS


def build_dashboard_pipeline_view(
    *,
    latest_runtime_payload: dict[str, object] | None,
    event_views: dict[str, object],
) -> dict[str, object]:
    """Build a simple SCADA-inspired pipeline view from existing dashboard state."""

    payload = latest_runtime_payload or {}
    latest_cycle = payload.get("latest_cycle") or {}
    simulator_snapshot = latest_cycle.get("simulator_snapshot") or {}
    sensor_values = simulator_snapshot.get("sensors") or {}
    edges = latest_cycle.get("edges") or []
    consensus_summary = latest_cycle.get("consensus_summary") or {}
    scada_state = latest_cycle.get("scada_state") or {}
    comparison_output = latest_cycle.get("comparison_output") or {}
    lifecycle = latest_cycle.get("fingerprint_lifecycle") or {}
    fingerprint_results = latest_cycle.get("fingerprint_inference_results") or []
    replay_behavior = latest_cycle.get("replay_behavior") or {}

    nodes = {
        "compressor": _node(
            component_id="compressor",
            title="Compressor",
            kind="process",
            status=_latest_component_status(event_views, "compressor"),
            metrics=(
                ("Power", f"{simulator_snapshot.get('operating_state_pct', 0)}%"),
                ("Temp", _format_metric(sensor_values.get("temperature"))),
                ("Pressure", _format_metric(sensor_values.get("pressure"))),
                ("RPM", _format_metric(sensor_values.get("rpm"))),
            ),
        ),
        "temperature_sensor": _sensor_node(
            sensor_name="temperature",
            latest_cycle=latest_cycle,
            event_views=event_views,
        ),
        "pressure_sensor": _sensor_node(
            sensor_name="pressure",
            latest_cycle=latest_cycle,
            event_views=event_views,
        ),
        "rpm_sensor": _sensor_node(
            sensor_name="rpm",
            latest_cycle=latest_cycle,
            event_views=event_views,
        ),
        "edge_1": _edge_node(
            edge_id="edge-1",
            edges=edges,
            event_views=event_views,
        ),
        "edge_2": _edge_node(
            edge_id="edge-2",
            edges=edges,
            event_views=event_views,
        ),
        "edge_3": _edge_node(
            edge_id="edge-3",
            edges=edges,
            event_views=event_views,
        ),
        "consensus": _node(
            component_id="consensus",
            title="Consensus",
            kind="consensus",
            status=_latest_component_status(event_views, "consensus"),
            metrics=(
                ("Status", str(consensus_summary.get("final_consensus_status") or "unknown")),
                ("Round", str(consensus_summary.get("round_id") or "not_available")),
            ),
        ),
        "scada_source": _node(
            component_id="scada_source",
            log_component_id="scada_comparison",
            title="SCADA Workstation",
            kind="scada",
            status=_scada_source_status(scada_state),
            metrics=(
                ("Temp", _format_metric(_find_scada_value(scada_state, "temperature"))),
                ("Pressure", _format_metric(_find_scada_value(scada_state, "pressure"))),
                ("RPM", _format_metric(_find_scada_value(scada_state, "rpm"))),
            ),
        ),
        "scada_comparison": _node(
            component_id="scada_comparison",
            title="SCADA Comparison",
            kind="comparison",
            status=_latest_component_status(event_views, "scada_comparison"),
            metrics=(
                (
                    "Divergent sensors",
                    ", ".join(comparison_output.get("divergent_sensors") or [])
                    or "none",
                ),
                (
                    "Source round",
                    str(scada_state.get("source_round_id") or "not_available"),
                ),
            ),
        ),
        "fingerprint_lifecycle": _node(
            component_id="fingerprint_lifecycle",
            title="Fingerprint / LSTM",
            kind="fingerprint",
            status=_latest_component_status(event_views, "fingerprint_lifecycle"),
            metrics=(
                ("Model", str(lifecycle.get("model_status") or "no_model_yet")),
                ("Inference", str(lifecycle.get("inference_status") or "not_available")),
                ("Classification", _fingerprint_classification(fingerprint_results, replay_behavior)),
            ),
        ),
    }

    return {
        "flow_summary": "Power -> sensors -> edges -> consensus -> SCADA comparison -> fingerprint",
        "rows": [
            {
                "id": "process",
                "label": "Physical process",
                "nodes": [
                    nodes["compressor"],
                    nodes["temperature_sensor"],
                    nodes["pressure_sensor"],
                    nodes["rpm_sensor"],
                ],
            },
            {
                "id": "edges",
                "label": "Distributed edges",
                "nodes": [nodes["edge_1"], nodes["edge_2"], nodes["edge_3"]],
            },
            {
                "id": "decision",
                "label": "Consensus and supervisory interpretation",
                "nodes": [
                    nodes["consensus"],
                    nodes["scada_source"],
                    nodes["scada_comparison"],
                    nodes["fingerprint_lifecycle"],
                ],
            },
        ],
        "channel_separation": [
            {
                "id": "scada_divergence",
                "label": "SCADA divergence",
                "status": (
                    "active"
                    if latest_cycle.get("scada_divergence_alert") is not None
                    else "clear"
                ),
                "explanation": "Direct SCADA-vs-consensus mismatch remains separate from replay/fingerprint behavior.",
            },
            {
                "id": "consensus",
                "label": "Consensus status",
                "status": str(consensus_summary.get("final_consensus_status") or "unknown"),
                "explanation": "Consensus trust state stays distinct from SCADA comparison and fingerprint channels.",
            },
            {
                "id": "fingerprint",
                "label": "Fingerprint / replay",
                "status": _fingerprint_classification(fingerprint_results, replay_behavior),
                "explanation": "Behavioral anomaly output remains separate from the consensus and SCADA divergence channels.",
            },
        ],
    }


def _sensor_node(
    *,
    sensor_name: str,
    latest_cycle: dict[str, object],
    event_views: dict[str, object],
) -> dict[str, object]:
    component_id = f"{sensor_name}_sensor"
    comparison_output = latest_cycle.get("comparison_output") or {}
    sensor_output = next(
        (
            output
            for output in comparison_output.get("sensor_outputs") or []
            if output.get("sensor_name") == sensor_name
        ),
        {},
    )
    scada_state = latest_cycle.get("scada_state") or {}
    return _node(
        component_id=component_id,
        title=COMPONENT_LABELS[component_id],
        kind="sensor",
        status=_latest_component_status(event_views, component_id),
        metrics=(
            ("Process", _format_metric(sensor_output.get("physical_value"))),
            ("SCADA", _format_metric(sensor_output.get("scada_value") or _find_scada_value(scada_state, sensor_name))),
            (
                "Comparison",
                str(sensor_output.get("divergence_classification") or "not_available"),
            ),
        ),
    )


def _edge_node(
    *,
    edge_id: str,
    edges: list[dict[str, object]],
    event_views: dict[str, object],
) -> dict[str, object]:
    edge = next(
        (
            candidate
            for candidate in edges
            if (candidate.get("runtime_state") or {}).get("edge_id") == edge_id
        ),
        {},
    )
    component_id = edge_id.replace("-", "_")
    runtime_state = edge.get("runtime_state") or {}
    replicated_state = edge.get("replicated_state") or {}
    return _node(
        component_id=component_id,
        title=COMPONENT_LABELS[component_id],
        kind="edge",
        status=_latest_component_status(event_views, component_id),
        metrics=(
            ("Published", str(runtime_state.get("published_observation_count") or 0)),
            ("Consumed", str(runtime_state.get("consumed_observation_count") or 0)),
            ("Replicated", str(replicated_state.get("is_complete") or False)),
        ),
    )


def _node(
    *,
    component_id: str,
    title: str,
    kind: str,
    status: str,
    metrics: tuple[tuple[str, str], ...],
    log_component_id: str | None = None,
) -> dict[str, object]:
    return {
        "component_id": component_id,
        "log_component_id": log_component_id or component_id,
        "title": title,
        "kind": kind,
        "status": status,
        "metrics": [{"label": label, "value": value} for label, value in metrics],
    }


def _latest_component_status(
    event_views: dict[str, object],
    component_id: str,
) -> str:
    timeline = (event_views.get("component_timelines") or {}).get(component_id) or []
    if not timeline:
        return "No live status available yet."
    return str(timeline[0].get("message") or "No interpreted status available yet.")


def _scada_source_status(scada_state: dict[str, object]) -> str:
    if not scada_state:
        return "SCADA source state is not available yet."
    source_round_id = scada_state.get("source_round_id")
    if source_round_id:
        return f"Supervisory values are being projected from {source_round_id}."
    return "SCADA source is active but source-round metadata is not available."


def _find_scada_value(scada_state: dict[str, object], sensor_name: str) -> object:
    sensor_values = scada_state.get("sensor_values") or {}
    entry = sensor_values.get(sensor_name) or {}
    return entry.get("value")


def _fingerprint_classification(
    fingerprint_results: list[dict[str, object]],
    replay_behavior: dict[str, object],
) -> str:
    if replay_behavior:
        return str(replay_behavior.get("classification") or "not_available")
    if fingerprint_results:
        return str(fingerprint_results[0].get("classification") or "not_available")
    return "not_available"


def _format_metric(value: object) -> str:
    if value is None:
        return "n/a"
    return str(value)
