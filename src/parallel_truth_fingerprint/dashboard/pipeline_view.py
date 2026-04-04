"""Derived Story 5.2 visual pipeline view for the local dashboard."""

from __future__ import annotations

from parallel_truth_fingerprint.dashboard.event_timeline import COMPONENT_LABELS
from parallel_truth_fingerprint.dashboard.runtime_binding import (
    extract_divergent_sensors,
    extract_structured_comparison_output,
    extract_structured_divergence_alert,
)


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
    comparison_output = extract_structured_comparison_output(
        latest_cycle.get("comparison_output") or {}
    )
    comparison_stage = latest_cycle.get("comparison_stage") or {}
    divergence_alert = extract_structured_divergence_alert(
        latest_cycle.get("scada_divergence_alert") or {}
    )
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
            tone=_consensus_tone(consensus_summary),
            metrics=(
                ("Status", str(consensus_summary.get("final_consensus_status") or "unknown")),
                ("Round", str(consensus_summary.get("round_id") or "not_available")),
                (
                    "Valid / quorum",
                    _consensus_quorum_metric(consensus_summary),
                ),
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
            tone=_scada_comparison_tone(
                comparison_stage=comparison_stage,
                comparison_output=comparison_output,
            ),
            metrics=(
                (
                    "Divergent sensors",
                    ", ".join(extract_divergent_sensors(comparison_output)) or "none",
                ),
                (
                    "Source round",
                    str(scada_state.get("source_round_id") or "not_available"),
                ),
                (
                    "Decision",
                    _scada_comparison_decision(comparison_stage, comparison_output),
                ),
            ),
        ),
        "fingerprint_lifecycle": _node(
            component_id="fingerprint_lifecycle",
            title="Fingerprint / LSTM",
            kind="fingerprint",
            status=_latest_component_status(event_views, "fingerprint_lifecycle"),
            tone=_fingerprint_tone(fingerprint_results, replay_behavior, lifecycle),
            metrics=(
                ("Model", str(lifecycle.get("model_status") or "no_model_yet")),
                ("Inference", str(lifecycle.get("inference_status") or "not_available")),
                (
                    "Classification",
                    _fingerprint_classification(
                        fingerprint_results,
                        replay_behavior,
                        lifecycle,
                    ),
                ),
            ),
        ),
    }

    return {
        "flow_summary": "Power -> sensors -> edges -> consensus -> SCADA comparison -> fingerprint",
        "rows": [
            {
                "id": "physical_origin",
                "label": "Physical origin and sensors",
                "summary": "The compressor and its sensors are the physical origin of the process values.",
                "nodes": [
                    nodes["compressor"],
                    nodes["temperature_sensor"],
                    nodes["pressure_sensor"],
                    nodes["rpm_sensor"],
                ],
            },
            {
                "id": "edges",
                "label": "Distributed edge acquisition",
                "summary": "Each edge acquires, publishes, consumes peer observations, and reconstructs a local shared view.",
                "nodes": [nodes["edge_1"], nodes["edge_2"], nodes["edge_3"]],
            },
            {
                "id": "consensus",
                "label": "Trusted committed state",
                "summary": "Consensus produces the committed shared truth used downstream.",
                "nodes": [nodes["consensus"]],
            },
            {
                "id": "scada",
                "label": "Supervisory validation",
                "summary": "SCADA source values are compared against the consensused state as a later supervisory check.",
                "nodes": [nodes["scada_source"], nodes["scada_comparison"]],
            },
            {
                "id": "fingerprint",
                "label": "Behavioral interpretation",
                "summary": "The fingerprint path interprets behavior and keeps replay-oriented output distinct from SCADA divergence.",
                "nodes": [nodes["fingerprint_lifecycle"]],
            },
        ],
        "channel_separation": [
            {
                "id": "scada_divergence",
                "label": "SCADA divergence",
                "status": (
                    "blocked"
                    if _scada_divergence_is_active(
                        divergence_alert=divergence_alert,
                        comparison_output=comparison_output,
                    )
                    else "clear"
                ),
                "tone": (
                    "blocked"
                    if _scada_divergence_is_active(
                        divergence_alert=divergence_alert,
                        comparison_output=comparison_output,
                    )
                    else "clear"
                ),
                "explanation": "Direct SCADA-vs-consensus mismatch remains separate from replay/fingerprint behavior.",
            },
            {
                "id": "consensus",
                "label": "Consensus status",
                "status": _consensus_channel_status(consensus_summary),
                "tone": _consensus_tone(consensus_summary),
                "explanation": "Consensus trust state stays distinct from SCADA comparison and fingerprint channels.",
            },
            {
                "id": "fingerprint",
                "label": "Fingerprint / replay",
                "status": _fingerprint_channel_status(
                    fingerprint_results=fingerprint_results,
                    replay_behavior=replay_behavior,
                    lifecycle=lifecycle,
                ),
                "tone": _fingerprint_tone(fingerprint_results, replay_behavior, lifecycle),
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
    simulator_snapshot = latest_cycle.get("simulator_snapshot") or {}
    sensor_values = simulator_snapshot.get("sensors") or {}
    transmitter_observation = (
        simulator_snapshot.get("transmitter_observations") or {}
    ).get(sensor_name) or {}
    unit = ((transmitter_observation.get("pv") or {}).get("unit")) or "n/a"
    return _node(
        component_id=component_id,
        title=COMPONENT_LABELS[component_id],
        kind="sensor",
        status=_latest_component_status(event_views, component_id),
        metrics=(
            ("Value", _format_metric(sensor_values.get(sensor_name))),
            ("Unit", unit),
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
            ("Peer-consumed", str(runtime_state.get("peer_observation_count") or 0)),
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
    tone: str = "clear",
) -> dict[str, object]:
    return {
        "component_id": component_id,
        "log_component_id": log_component_id or component_id,
        "title": title,
        "kind": kind,
        "status": status,
        "tone": tone,
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
    lifecycle: dict[str, object],
) -> str:
    if replay_behavior:
        return str(replay_behavior.get("classification") or "not_available")
    if fingerprint_results:
        return str(fingerprint_results[0].get("classification") or "not_available")
    inference_status = str(lifecycle.get("inference_status") or "")
    if inference_status.startswith("blocked:"):
        return "blocked"
    return "not_available"


def _format_metric(value: object) -> str:
    if value is None:
        return "n/a"
    return str(value)


def _scada_divergence_is_active(
    *,
    divergence_alert: dict[str, object],
    comparison_output: dict[str, object],
) -> bool:
    if extract_divergent_sensors(comparison_output):
        return True
    if divergence_alert.get("divergent_sensors"):
        return True
    return False


def _consensus_tone(consensus_summary: dict[str, object]) -> str:
    status = str(consensus_summary.get("final_consensus_status") or "unknown")
    valid_participants = consensus_summary.get("valid_participants_after_exclusions")
    quorum_required = consensus_summary.get("quorum_required")
    if (
        status == "failed_consensus"
        and valid_participants is not None
        and quorum_required is not None
        and int(valid_participants) < int(quorum_required)
    ):
        return "blocked"
    return "clear" if status == "success" else "warning"


def _consensus_quorum_metric(consensus_summary: dict[str, object]) -> str:
    valid_participants = consensus_summary.get("valid_participants_after_exclusions")
    quorum_required = consensus_summary.get("quorum_required")
    if valid_participants is None or quorum_required is None:
        return "not_available"
    return f"{valid_participants}/{quorum_required}"


def _consensus_channel_status(consensus_summary: dict[str, object]) -> str:
    status = str(consensus_summary.get("final_consensus_status") or "unknown")
    if _consensus_tone(consensus_summary) == "blocked":
        return "no_quorum_block"
    return status


def _scada_comparison_tone(
    comparison_stage: dict[str, object],
    comparison_output: dict[str, object],
) -> str:
    if comparison_stage.get("status") in {"blocked", "blocked_downstream"}:
        return "blocked"
    return "clear" if not extract_divergent_sensors(comparison_output) else "warning"


def _scada_comparison_decision(
    comparison_stage: dict[str, object],
    comparison_output: dict[str, object],
) -> str:
    if comparison_stage.get("status") == "blocked":
        return "blocked_before_comparison"
    if extract_divergent_sensors(comparison_output):
        return "blocked_on_divergence"
    return "forwarded_downstream"


def _fingerprint_channel_status(
    *,
    fingerprint_results: list[dict[str, object]],
    replay_behavior: dict[str, object],
    lifecycle: dict[str, object],
) -> str:
    if replay_behavior:
        return str(replay_behavior.get("classification") or "not_available")
    if fingerprint_results:
        return str(fingerprint_results[0].get("classification") or "not_available")
    inference_status = str(lifecycle.get("inference_status") or "")
    if inference_status.startswith("blocked:"):
        return "blocked"
    return "not_available"


def _fingerprint_tone(
    fingerprint_results: list[dict[str, object]],
    replay_behavior: dict[str, object],
    lifecycle: dict[str, object],
) -> str:
    if replay_behavior:
        return "warning"
    if fingerprint_results:
        classification = str(fingerprint_results[0].get("classification") or "")
        return "warning" if classification == "anomalous" else "clear"
    inference_status = str(lifecycle.get("inference_status") or "")
    if inference_status.startswith("blocked:"):
        return "blocked"
    return "clear"
