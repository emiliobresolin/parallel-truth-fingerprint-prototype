"""Local SCADA-inspired operator dashboard and control surface for Story 4.6."""

from __future__ import annotations

from collections import deque
from dataclasses import dataclass, replace
from datetime import datetime, timezone
from http import HTTPStatus
from http.server import BaseHTTPRequestHandler, ThreadingHTTPServer
import json
import threading

from parallel_truth_fingerprint.config.ranges import DEFAULT_COMPRESSOR_PROFILE
from parallel_truth_fingerprint.dashboard.evidence_view import (
    build_dashboard_explainability_view,
)
from parallel_truth_fingerprint.dashboard.event_timeline import (
    COMPONENT_DEFINITIONS,
    build_dashboard_event_views,
)
from parallel_truth_fingerprint.dashboard.guidance_view import (
    build_dashboard_guidance_view,
)
from parallel_truth_fingerprint.dashboard.pipeline_view import (
    build_dashboard_pipeline_view,
)
from parallel_truth_fingerprint.persistence import MinioArtifactStore, MinioStoreConfig
from parallel_truth_fingerprint.scenario_control import (
    SUPPORTED_DEMO_SCENARIOS,
    resolve_runtime_scenario_control_stage,
)


ACTION_LOG_LIMIT = 32
POWER_OUTPUT_CHANNELS = (
    "sensor_values",
    "consensus_alert",
    "persistence_stage",
    "fingerprint_inference",
)


def _utc_now() -> str:
    return datetime.now(timezone.utc).isoformat()


def _load_run_local_demo_module():
    from scripts import run_local_demo

    return run_local_demo


@dataclass(frozen=True)
class OperatorActionRecord:
    """Inspectable operator action shown in the dashboard."""

    action: str
    applied_at: str
    applies_on_cycle: int
    runtime_command: str
    configuration_change: dict[str, object]
    expected_output_channels: tuple[str, ...]
    effect_scope: str
    note: str

    def to_dict(self) -> dict[str, object]:
        return {
            "action": self.action,
            "applied_at": self.applied_at,
            "applies_on_cycle": self.applies_on_cycle,
            "runtime_command": self.runtime_command,
            "configuration_change": self.configuration_change,
            "expected_output_channels": list(self.expected_output_channels),
            "effect_scope": self.effect_scope,
            "note": self.note,
        }


class LocalOperatorDashboardController:
    """Manage the real local runtime behind the Story 4.6 dashboard."""

    def __init__(self, base_config) -> None:
        self._base_config = base_config
        self._lock = threading.RLock()
        self._runtime_thread: threading.Thread | None = None
        self._stop_event = threading.Event()
        self._runtime_status = "stopped"
        self._latest_runtime_payload: dict[str, object] | None = None
        self._last_runtime_status = "not_started"
        self._configured_scenario = (
            base_config.demo_scenario_name.strip() or "normal"
        )
        self._scenario_start_cycle = max(base_config.demo_scenario_start_cycle, 1)
        self._configured_power = self._clamp_power(base_config.demo_power)
        self._last_error: str | None = None
        self._action_log: deque[OperatorActionRecord] = deque(maxlen=ACTION_LOG_LIMIT)
        self._artifact_store = MinioArtifactStore(
            MinioStoreConfig(
                endpoint=base_config.minio_endpoint,
                access_key=base_config.minio_access_key,
                secret_key=base_config.minio_secret_key,
                bucket=base_config.minio_bucket,
                secure=base_config.minio_secure,
            )
        )
        self._artifact_json_cache: dict[str, dict[str, object]] = {}

    def start_runtime(self) -> dict[str, object]:
        """Start the real autonomous runtime in the background."""

        with self._lock:
            if self._runtime_thread is not None and self._runtime_thread.is_alive():
                self._append_action(
                    action="start_runtime",
                    applies_on_cycle=self._current_cycle_locked() + 1,
                    runtime_command="start_runtime()",
                    configuration_change={},
                    expected_output_channels=("runtime_state",),
                    effect_scope="no_change_already_running",
                    note="Runtime start ignored because the dashboard runtime is already running.",
                )
                return self.build_dashboard_state()

            self._stop_event.clear()
            self._runtime_status = "starting"
            self._last_error = None
            self._latest_runtime_payload = None
            self._last_runtime_status = "starting"
            self._append_action(
                action="start_runtime",
                applies_on_cycle=1,
                runtime_command="start_runtime()",
                configuration_change={"runtime_state": "running"},
                expected_output_channels=(
                    "runtime_state",
                    "consensus_alert",
                    "persistence_stage",
                    "fingerprint_lifecycle",
                ),
                effect_scope="runtime_command_started",
                note="Dashboard requested the autonomous runtime to start from cycle 1.",
            )
            self._runtime_thread = threading.Thread(
                target=self._run_runtime,
                name="story-4-6-dashboard-runtime",
                daemon=True,
            )
            self._runtime_thread.start()
            return self.build_dashboard_state()

    def stop_runtime(self) -> dict[str, object]:
        """Request a clean runtime stop."""

        with self._lock:
            next_cycle = self._current_cycle_locked() + 1
            self._stop_event.set()
            if self._runtime_thread is not None and self._runtime_thread.is_alive():
                self._runtime_status = "stopping"
                note = "Dashboard requested the autonomous runtime to stop after the current cycle boundary."
            else:
                self._runtime_status = "stopped"
                note = "Dashboard stop request found the runtime already stopped."
            self._append_action(
                action="stop_runtime",
                applies_on_cycle=next_cycle,
                runtime_command="stop_runtime()",
                configuration_change={"runtime_state": "stopped"},
                expected_output_channels=("runtime_state",),
                effect_scope=(
                    "runtime_command_requested_stop"
                    if self._runtime_thread is not None and self._runtime_thread.is_alive()
                    else "no_change_already_stopped"
                ),
                note=note,
            )
            return self.build_dashboard_state()

    def set_scenario(self, scenario_name: str) -> dict[str, object]:
        """Update the configured demo scenario for the next eligible cycle."""

        normalized_name = scenario_name.strip() or "normal"
        if normalized_name not in SUPPORTED_DEMO_SCENARIOS:
            raise ValueError(
                f"Unsupported dashboard scenario '{normalized_name}'. "
                f"Expected one of {list(SUPPORTED_DEMO_SCENARIOS)}."
            )

        with self._lock:
            runtime_is_live = self._is_runtime_active_locked()
            applies_on_cycle = 1 if not runtime_is_live else self._current_cycle_locked() + 1
            self._configured_scenario = normalized_name
            self._scenario_start_cycle = applies_on_cycle
            self._append_action(
                action="set_scenario",
                applies_on_cycle=applies_on_cycle,
                runtime_command=f"set_scenario('{normalized_name}')",
                configuration_change={
                    "demo_scenario_name": normalized_name,
                    "demo_scenario_start_cycle": applies_on_cycle,
                },
                expected_output_channels=self._expected_outputs_locked(
                    normalized_name,
                    applies_on_cycle,
                ),
                effect_scope=(
                    "applies_next_cycle"
                    if runtime_is_live
                    else "configuration_only_until_next_start"
                ),
                note=(
                    f"Dashboard configured scenario '{normalized_name}' to activate on cycle "
                    f"{applies_on_cycle}. "
                    + (
                        "The runtime is live, so the change will affect the next eligible cycle."
                        if runtime_is_live
                        else "The runtime is stopped, so this only updates configured state until the next start."
                    )
                ),
            )
            return self.build_dashboard_state()

    def set_power(self, operating_level_pct: float) -> dict[str, object]:
        """Update the compressor operating level for later cycles."""

        with self._lock:
            clamped_power = self._clamp_power(operating_level_pct)
            runtime_is_live = self._is_runtime_active_locked()
            applies_on_cycle = 1 if not runtime_is_live else self._current_cycle_locked() + 1
            self._configured_power = clamped_power
            self._append_action(
                action="set_power",
                applies_on_cycle=applies_on_cycle,
                runtime_command=f"set_power({clamped_power})",
                configuration_change={"demo_power": clamped_power},
                expected_output_channels=POWER_OUTPUT_CHANNELS,
                effect_scope=(
                    "applies_next_cycle"
                    if runtime_is_live
                    else "configuration_only_until_next_start"
                ),
                note=(
                    f"Dashboard configured compressor operating level to {clamped_power}% "
                    f"starting on cycle {applies_on_cycle}. "
                    + (
                        "The runtime is live, so the change will affect the next eligible cycle."
                        if runtime_is_live
                        else "The runtime is stopped, so this only updates configured state until the next start."
                    )
                ),
            )
            return self.build_dashboard_state()

    def build_dashboard_state(self) -> dict[str, object]:
        """Return one inspectable dashboard state payload for the UI."""

        with self._lock:
            generated_at = _utc_now()
            latest_payload = self._latest_runtime_payload or {}
            latest_cycle = latest_payload.get("latest_cycle") or {}
            runtime_info = latest_payload.get("runtime") or {}
            scenario_info = latest_payload.get("scenario_control") or {}
            fingerprint_lifecycle = latest_cycle.get("fingerprint_lifecycle") or {}
            simulator_snapshot = latest_cycle.get("simulator_snapshot") or {}
            operator_actions = [
                action.to_dict() for action in reversed(self._action_log)
            ]

            validation_level = (
                fingerprint_lifecycle.get("source_dataset_validation_level")
                or "runtime_valid_only"
            )
            limitation_note = (
                fingerprint_lifecycle.get("limitation_note")
                or "The fingerprint base is still runtime-valid only, not yet meaningful-fingerprint-valid, because the adequacy floor remains below target."
            )
            event_views = build_dashboard_event_views(
                generated_at=generated_at,
                latest_runtime_payload=latest_payload,
                operator_actions=operator_actions,
            )
            explainability = build_dashboard_explainability_view(
                generated_at=generated_at,
                latest_runtime_payload=latest_payload,
                operator_actions=operator_actions,
                limitation_note=limitation_note,
                artifact_json_loader=self._load_dashboard_artifact_json,
            )
            pipeline_view = build_dashboard_pipeline_view(
                latest_runtime_payload=latest_payload,
                event_views=event_views,
            )
            guidance_view = build_dashboard_guidance_view(
                latest_runtime_payload=latest_payload,
                explainability=explainability,
                limitation_note=limitation_note,
            )

            return {
                "generated_at": generated_at,
                "runtime": {
                    "ui_status": self._runtime_status,
                    "is_running": self._is_runtime_active_locked(),
                    "last_runtime_status": self._last_runtime_status,
                    "status_note": self._runtime_status_note_locked(),
                    "current_cycle": runtime_info.get("current_cycle", 0),
                    "completed_cycles": runtime_info.get("completed_cycles", 0),
                    "cycle_interval_seconds": runtime_info.get(
                        "cycle_interval_seconds",
                        self._base_config.demo_cycle_interval_seconds,
                    ),
                    "configured_power_pct": self._configured_power,
                    "configured_scenario": self._configured_scenario,
                    "scenario_start_cycle": self._scenario_start_cycle,
                    "last_error": self._last_error,
                },
                "controls": {
                    "supported_scenarios": list(SUPPORTED_DEMO_SCENARIOS),
                    "configured_scenario": self._configured_scenario,
                    "scenario_start_cycle": self._scenario_start_cycle,
                    "configured_power_pct": self._configured_power,
                    "apply_mode": self._control_apply_mode_locked(),
                    "runtime_effect_note": self._control_runtime_note_locked(),
                },
                "operator_feedback": {
                    "actions": operator_actions,
                },
                "monitoring": {
                    "active_scenario": (
                        latest_cycle.get("scenario_control", {}).get("active_scenario")
                        or scenario_info.get("configured_scenario")
                        or self._configured_scenario
                    ),
                    "cadence": latest_cycle.get("runtime_cycle", {}).get("cadence_stage"),
                    "compressor_state": simulator_snapshot,
                    "sensor_values": simulator_snapshot.get("sensors", {}),
                    "edge_status": latest_cycle.get("edges", []),
                    "quorum_consensus": {
                        "summary": latest_cycle.get("consensus_summary"),
                        "alert": latest_cycle.get("consensus_alert"),
                    },
                    "valid_artifact_accumulation": {
                        "count": runtime_info.get("latest_valid_artifact_count"),
                        "latest_artifact_key": fingerprint_lifecycle.get(
                            "latest_valid_artifact_key"
                        ),
                    },
                    "lifecycle": fingerprint_lifecycle,
                    "scada_state": latest_cycle.get("scada_state"),
                    "comparison_output": latest_cycle.get("comparison_output"),
                    "cycle_history": latest_payload.get("cycle_history", []),
                },
                "channels": {
                    "scada_divergence": latest_cycle.get("scada_divergence_alert"),
                    "consensus": {
                        "summary": latest_cycle.get("consensus_summary"),
                        "alert": latest_cycle.get("consensus_alert"),
                    },
                    "fingerprint_inference": latest_cycle.get(
                        "fingerprint_inference_results",
                        [],
                    ),
                    "replay_behavior": latest_cycle.get("replay_behavior"),
                },
                "events": event_views,
                "pipeline": pipeline_view,
                "explainability": explainability,
                "guidance": guidance_view,
                "limitations": {
                    "source_dataset_validation_level": validation_level,
                    "note": limitation_note,
                },
            }

    def _run_runtime(self) -> None:
        run_local_demo = _load_run_local_demo_module()
        try:
            components = run_local_demo.build_demo_runtime_components(
                self._current_runtime_config()
            )
            final_payload = run_local_demo.run_autonomous_demo_loop(
                config=self._current_runtime_config(),
                simulator=components["simulator"],
                edges=components["edges"],
                cometbft_client=components["cometbft_client"],
                artifact_store=components["artifact_store"],
                scada_service=components["scada_service"],
                config_provider=self._current_runtime_config,
                stop_requested_fn=self._stop_event.is_set,
                cycle_observer=self._record_runtime_payload,
            )
            self._record_runtime_payload(final_payload)
        except Exception as exc:  # pragma: no cover
            with self._lock:
                self._last_error = str(exc)
                self._runtime_status = "stopped"
                self._last_runtime_status = "error"
                self._append_action(
                    action="runtime_error",
                    applies_on_cycle=self._current_cycle_locked() + 1,
                    runtime_command="runtime_error",
                    configuration_change={},
                    expected_output_channels=("runtime_state",),
                    effect_scope="runtime_error",
                    note=f"Dashboard runtime failed: {exc}",
                )
        finally:
            self._stop_event.clear()
            with self._lock:
                if self._runtime_status != "stopped":
                    self._runtime_status = "stopped"

    def _record_runtime_payload(self, runtime_payload: dict[str, object]) -> None:
        with self._lock:
            self._latest_runtime_payload = runtime_payload
            runtime_status = runtime_payload.get("runtime", {}).get("status", "unknown")
            self._last_runtime_status = runtime_status
            if runtime_status == "active":
                self._runtime_status = "running"
            elif self._runtime_status != "stopping":
                self._runtime_status = "stopped"

    def _current_runtime_config(self):
        with self._lock:
            return replace(
                self._base_config,
                demo_power=self._configured_power,
                demo_scenario_name=self._configured_scenario,
                demo_scenario_start_cycle=self._scenario_start_cycle,
                demo_fault_mode="none",
                demo_scada_mode="match",
                demo_scada_start_cycle=0,
            )

    def _expected_outputs_locked(
        self,
        scenario_name: str,
        applies_on_cycle: int,
    ) -> tuple[str, ...]:
        preview_stage = resolve_runtime_scenario_control_stage(
            config=replace(
                self._base_config,
                demo_scenario_name=scenario_name,
                demo_scenario_start_cycle=applies_on_cycle,
                demo_fault_mode="none",
                demo_scada_mode="match",
                demo_scada_start_cycle=0,
            ),
            cycle_index=applies_on_cycle,
        )
        return preview_stage.expected_output_channels

    def _append_action(
        self,
        *,
        action: str,
        applies_on_cycle: int,
        runtime_command: str,
        configuration_change: dict[str, object],
        expected_output_channels: tuple[str, ...],
        effect_scope: str,
        note: str,
    ) -> None:
        self._action_log.append(
            OperatorActionRecord(
                action=action,
                applied_at=_utc_now(),
                applies_on_cycle=applies_on_cycle,
                runtime_command=runtime_command,
                configuration_change=configuration_change,
                expected_output_channels=expected_output_channels,
                effect_scope=effect_scope,
                note=note,
            )
        )

    def _is_runtime_active_locked(self) -> bool:
        return self._runtime_status in {"starting", "running", "stopping"}

    def _current_cycle_locked(self) -> int:
        if self._latest_runtime_payload is None:
            return 0
        return int(self._latest_runtime_payload.get("runtime", {}).get("current_cycle", 0))

    def _runtime_status_note_locked(self) -> str:
        if self._last_error:
            return (
                "The last runtime attempt failed before a live cycle completed. "
                "Inspect the active failure message and fix the live path before trusting operator changes."
            )
        if self._runtime_status == "running":
            return (
                "The runtime is active. Watch cycle count and valid-artifact growth to confirm live continuity."
            )
        if self._runtime_status == "starting":
            return (
                "The runtime is starting. The first live cycle is still being established."
            )
        if self._runtime_status == "stopping":
            return "The runtime is stopping at the next safe cycle boundary."
        return (
            "The runtime is stopped. Start it from the dashboard before expecting live cycle effects."
        )

    def _control_apply_mode_locked(self) -> str:
        if self._runtime_status == "running":
            return "next_cycle"
        if self._runtime_status in {"starting", "stopping"}:
            return "queued_until_runtime_stabilizes"
        return "next_start"

    def _control_runtime_note_locked(self) -> str:
        apply_mode = self._control_apply_mode_locked()
        if apply_mode == "next_cycle":
            return (
                "Scenario and power changes are applied to the next eligible live cycle. "
                "They do not rewrite the current cycle retroactively."
            )
        if apply_mode == "queued_until_runtime_stabilizes":
            return (
                "The runtime is not in a stable running cycle yet. Control changes are queued and "
                "will only take effect once live cycling continues."
            )
        return (
            "The runtime is stopped. Control changes update configured state only and will not affect "
            "live cycles until the next start."
        )

    def _load_dashboard_artifact_json(
        self,
        object_key: str,
    ) -> dict[str, object] | None:
        cached = self._artifact_json_cache.get(object_key)
        if cached is not None:
            return cached
        try:
            payload = self._artifact_store.load_json(object_key)
        except Exception:
            return None
        self._artifact_json_cache[object_key] = payload
        return payload

    @staticmethod
    def _clamp_power(value: float) -> float:
        minimum = DEFAULT_COMPRESSOR_PROFILE.compressor_power.minimum
        maximum = DEFAULT_COMPRESSOR_PROFILE.compressor_power.maximum
        return round(min(max(float(value), minimum), maximum), 3)


class LocalOperatorDashboardServer:
    """Small local HTTP server for the Story 4.6 operator dashboard."""

    def __init__(
        self,
        controller: LocalOperatorDashboardController,
        *,
        host: str = "127.0.0.1",
        port: int = 8088,
    ) -> None:
        self._controller = controller
        self._server = ThreadingHTTPServer(
            (host, port),
            self._build_handler(),
        )
        self._thread: threading.Thread | None = None

    @property
    def base_url(self) -> str:
        host, port = self._server.server_address[:2]
        return f"http://{host}:{port}"

    def start_in_background(self) -> None:
        if self._thread is not None and self._thread.is_alive():
            return
        self._thread = threading.Thread(
            target=self._server.serve_forever,
            name="story-4-6-dashboard-http",
            daemon=True,
        )
        self._thread.start()

    def serve_forever(self) -> None:
        self._server.serve_forever()

    def stop(self) -> None:
        self._controller.stop_runtime()
        self._server.shutdown()
        self._server.server_close()
        if self._thread is not None:
            self._thread.join(timeout=5)

    def _build_handler(self):
        controller = self._controller

        class DashboardHandler(BaseHTTPRequestHandler):
            def do_GET(self) -> None:  # noqa: N802
                if self.path == "/":
                    self._send_html(build_dashboard_html(controller.build_dashboard_state()))
                    return
                if self.path == "/api/state":
                    self._send_json(controller.build_dashboard_state())
                    return
                self.send_error(HTTPStatus.NOT_FOUND, "Route not found.")

            def do_POST(self) -> None:  # noqa: N802
                try:
                    payload = self._read_json_payload()
                    if self.path == "/api/runtime/start":
                        self._send_json(controller.start_runtime())
                        return
                    if self.path == "/api/runtime/stop":
                        self._send_json(controller.stop_runtime())
                        return
                    if self.path == "/api/control/scenario":
                        self._send_json(
                            controller.set_scenario(str(payload.get("scenario", "")))
                        )
                        return
                    if self.path == "/api/control/power":
                        self._send_json(
                            controller.set_power(float(payload.get("power", 0.0)))
                        )
                        return
                except ValueError as exc:
                    self._send_json({"error": str(exc)}, status=HTTPStatus.BAD_REQUEST)
                    return
                self.send_error(HTTPStatus.NOT_FOUND, "Route not found.")

            def log_message(self, format: str, *args) -> None:  # noqa: A003
                return

            def _read_json_payload(self) -> dict[str, object]:
                length = int(self.headers.get("Content-Length", "0"))
                if length <= 0:
                    return {}
                raw_payload = self.rfile.read(length).decode("utf-8")
                if not raw_payload.strip():
                    return {}
                return json.loads(raw_payload)

            def _send_html(self, html: str) -> None:
                encoded = html.encode("utf-8")
                self.send_response(HTTPStatus.OK)
                self.send_header("Content-Type", "text/html; charset=utf-8")
                self.send_header("Content-Length", str(len(encoded)))
                self.end_headers()
                self.wfile.write(encoded)

            def _send_json(
                self,
                payload: dict[str, object],
                *,
                status: HTTPStatus = HTTPStatus.OK,
            ) -> None:
                encoded = json.dumps(payload).encode("utf-8")
                self.send_response(status)
                self.send_header("Content-Type", "application/json; charset=utf-8")
                self.send_header("Content-Length", str(len(encoded)))
                self.end_headers()
                self.wfile.write(encoded)

        return DashboardHandler


def build_dashboard_html(initial_state: dict[str, object]) -> str:
    """Return the local Story 4.6 dashboard page."""

    initial_state_json = json.dumps(initial_state)
    component_option_markup = "\n".join(
        (
            f'<option value="{definition["id"]}">{definition["label"]}</option>'
            for definition in COMPONENT_DEFINITIONS
        )
    )
    return f"""<!DOCTYPE html>
<html lang="en">
<head>
  <meta charset="utf-8">
  <meta name="viewport" content="width=device-width, initial-scale=1">
  <title>Parallel Truth Fingerprint Operator Dashboard</title>
  <style>
    :root {{
      --bg: #0f1418;
      --panel: #172126;
      --panel-2: #10171b;
      --text: #e9f0ec;
      --muted: #92a6a0;
      --teal: #46d4b5;
      --amber: #f7bd59;
      --line: rgba(255,255,255,0.09);
    }}
    * {{ box-sizing: border-box; }}
    body {{
      margin: 0;
      font-family: "Segoe UI", system-ui, -apple-system, BlinkMacSystemFont, sans-serif;
      color: var(--text);
      background:
        radial-gradient(circle at top right, rgba(70,212,181,0.14), transparent 24rem),
        linear-gradient(160deg, #0c1014, var(--bg));
    }}
    .shell {{ width: min(1320px, calc(100vw - 1.5rem)); margin: 0.75rem auto 2rem; display: grid; gap: 1rem; }}
    .panel {{
      background: linear-gradient(180deg, rgba(255,255,255,0.02), transparent), var(--panel);
      border: 1px solid var(--line);
      border-radius: 18px;
      padding: 1rem;
    }}
    .hero {{ display: grid; gap: 0.9rem; }}
    .hero h1 {{ margin: 0; font-size: clamp(1.5rem, 2vw, 2.3rem); letter-spacing: 0.08em; text-transform: uppercase; }}
    .muted {{ color: var(--muted); }}
    .banner {{
      border-left: 4px solid var(--amber);
      background: rgba(247,189,89,0.08);
      border-radius: 12px;
      padding: 0.8rem 1rem;
    }}
    .status-banner {{
      border-left: 4px solid var(--teal);
      background: rgba(70,212,181,0.08);
      border-radius: 12px;
      padding: 0.8rem 1rem;
      font-size: 0.9rem;
    }}
    .error-banner {{
      border-left: 4px solid #ff7d5c;
      background: rgba(255,125,92,0.1);
      border-radius: 12px;
      padding: 0.8rem 1rem;
      font-size: 0.88rem;
      line-height: 1.5;
    }}
    .metrics, .controls, .secondary-grid {{ display: grid; gap: 1rem; }}
    .metrics {{ grid-template-columns: repeat(auto-fit, minmax(160px, 1fr)); }}
    .controls {{ grid-template-columns: repeat(auto-fit, minmax(260px, 1fr)); }}
    .workspace {{
      display: grid;
      gap: 1rem;
      grid-template-columns: minmax(0, 1.8fr) minmax(320px, 1fr);
      align-items: start;
    }}
    .summary-stack {{
      display: grid;
      gap: 1rem;
      align-content: start;
    }}
    .summary-card {{
      display: grid;
      gap: 1rem;
      align-content: start;
    }}
    .summary-section {{
      display: grid;
      gap: 0.75rem;
    }}
    .secondary-grid {{
      grid-template-columns: repeat(auto-fit, minmax(320px, 1fr));
      align-items: start;
    }}
    .metric {{
      background: var(--panel-2);
      border: 1px solid var(--line);
      border-radius: 14px;
      padding: 0.85rem 1rem;
    }}
    .metric span {{ display: block; }}
    .metric .label {{ color: var(--muted); font-size: 0.75rem; text-transform: uppercase; letter-spacing: 0.08em; margin-bottom: 0.25rem; }}
    .metric .value {{ font-size: 1.05rem; font-weight: 700; }}
    h2 {{ margin: 0 0 0.85rem; color: var(--teal); font-size: 0.95rem; text-transform: uppercase; letter-spacing: 0.08em; }}
    label {{ display: grid; gap: 0.45rem; margin-bottom: 0.8rem; color: var(--muted); font-size: 0.85rem; }}
    input, select, button {{
      font: inherit;
      border-radius: 12px;
      border: 1px solid var(--line);
      padding: 0.7rem 0.85rem;
    }}
    input, select {{ background: var(--panel-2); color: var(--text); }}
    button {{
      cursor: pointer;
      background: linear-gradient(135deg, var(--teal), #2aa1c0);
      color: #071012;
      font-weight: 700;
    }}
    button:disabled {{
      cursor: not-allowed;
      opacity: 0.45;
    }}
    button.secondary {{ background: linear-gradient(135deg, var(--amber), #d46f3d); }}
    button.ghost {{ background: var(--panel-2); color: var(--text); }}
    .row {{ display: flex; flex-wrap: wrap; gap: 0.7rem; }}
    .pre {{
      white-space: pre-wrap;
      word-break: break-word;
      background: var(--panel-2);
      border: 1px solid var(--line);
      border-radius: 12px;
      padding: 0.8rem;
      max-height: 24rem;
      overflow: auto;
      font-size: 0.8rem;
      font-family: "IBM Plex Mono", "Consolas", monospace;
    }}
    .action-list {{ display: grid; gap: 0.7rem; }}
    .action {{
      background: var(--panel-2);
      border: 1px solid var(--line);
      border-radius: 12px;
      padding: 0.8rem;
      font-size: 0.82rem;
    }}
    .action strong {{ color: var(--teal); }}
    .event {{
      background: var(--panel-2);
      border: 1px solid var(--line);
      border-radius: 12px;
      padding: 0.8rem;
      font-size: 0.82rem;
    }}
    .event strong {{ color: var(--teal); }}
    .event small {{ display: block; color: var(--muted); margin-bottom: 0.35rem; }}
    .status-card {{
      background: var(--panel-2);
      border: 1px solid var(--line);
      border-radius: 12px;
      padding: 0.8rem;
      font-size: 0.82rem;
    }}
    .status-card strong {{ color: var(--teal); display: block; margin-bottom: 0.35rem; }}
    .bullet-list {{
      margin: 0;
      padding-left: 1rem;
      display: grid;
      gap: 0.45rem;
      font-size: 0.84rem;
    }}
    .pipeline-workspace {{
      display: grid;
      gap: 1rem;
      align-content: start;
    }}
    .section-header {{
      display: flex;
      align-items: flex-start;
      justify-content: space-between;
      gap: 1rem;
      flex-wrap: wrap;
    }}
    .pipeline-flow {{ color: var(--muted); font-size: 0.82rem; }}
    .pipeline-stage-stack {{ display: grid; gap: 1rem; }}
    .pipeline-stage {{
      display: grid;
      gap: 0.85rem;
      padding: 0.95rem;
      border-radius: 14px;
      border: 1px solid var(--line);
      background: rgba(255,255,255,0.015);
    }}
    .pipeline-stage-header {{
      display: grid;
      gap: 0.3rem;
    }}
    .pipeline-stage-summary {{
      color: var(--muted);
      font-size: 0.83rem;
      line-height: 1.45;
    }}
    .pipeline-row {{ display: grid; gap: 0.75rem; grid-template-columns: repeat(auto-fit, minmax(220px, 1fr)); }}
    .pipeline-label {{
      color: var(--muted);
      font-size: 0.78rem;
      letter-spacing: 0.08em;
      text-transform: uppercase;
      margin-bottom: 0.05rem;
    }}
    .pipeline-card {{
      background: linear-gradient(180deg, rgba(255,255,255,0.03), transparent), var(--panel-2);
      border: 1px solid var(--line);
      border-radius: 14px;
      padding: 0.85rem;
      display: grid;
      gap: 0.55rem;
      min-height: 7.6rem;
    }}
    .pipeline-card.process {{ border-color: rgba(70, 212, 181, 0.35); }}
    .pipeline-card.sensor {{ border-color: rgba(247, 189, 89, 0.35); }}
    .pipeline-card.edge {{ border-color: rgba(42, 161, 192, 0.35); }}
    .pipeline-card.consensus {{ border-color: rgba(70, 212, 181, 0.28); }}
    .pipeline-card.scada {{ border-color: rgba(184, 150, 255, 0.28); }}
    .pipeline-card.comparison {{ border-color: rgba(255, 125, 92, 0.28); }}
    .pipeline-card.fingerprint {{ border-color: rgba(255, 210, 105, 0.28); }}
    .pipeline-card h3 {{
      margin: 0;
      font-size: 0.94rem;
      letter-spacing: 0.03em;
    }}
    .pipeline-status {{
      font-size: 0.8rem;
      line-height: 1.45;
      color: var(--text);
      min-height: 3.3rem;
    }}
    .pipeline-metrics {{
      display: grid;
      gap: 0.4rem;
      grid-template-columns: repeat(auto-fit, minmax(7rem, 1fr));
    }}
    .pipeline-metric {{
      border: 1px solid var(--line);
      border-radius: 10px;
      padding: 0.5rem 0.6rem;
      background: rgba(255,255,255,0.02);
    }}
    .pipeline-metric .metric-label {{
      display: block;
      color: var(--muted);
      font-size: 0.7rem;
      text-transform: uppercase;
      letter-spacing: 0.08em;
      margin-bottom: 0.2rem;
    }}
    .pipeline-metric .metric-value {{ font-size: 0.88rem; font-weight: 700; }}
    .pipeline-card button {{
      background: var(--panel);
      color: var(--text);
      border: 1px solid var(--line);
      padding: 0.55rem 0.7rem;
    }}
    .channel-strip {{
      display: grid;
      gap: 0.75rem;
      grid-template-columns: repeat(auto-fit, minmax(180px, 1fr));
    }}
    .channel-badge {{
      border: 1px solid var(--line);
      border-radius: 12px;
      padding: 0.75rem;
      background: rgba(255,255,255,0.02);
      font-size: 0.8rem;
    }}
    .channel-badge strong {{ display: block; color: var(--teal); margin-bottom: 0.3rem; }}
    .channel-badge .muted {{ font-size: 0.76rem; }}
    .guidance-grid {{ display: grid; gap: 0.9rem; grid-template-columns: repeat(auto-fit, minmax(250px, 1fr)); }}
    .guidance-card {{
      background: var(--panel-2);
      border: 1px solid var(--line);
      border-radius: 12px;
      padding: 0.85rem;
      display: grid;
      gap: 0.55rem;
      font-size: 0.82rem;
    }}
    .guidance-card strong {{ color: var(--teal); display: block; }}
    details.panel {{
      padding: 0;
      overflow: hidden;
    }}
    details.panel > summary {{
      list-style: none;
      cursor: pointer;
      padding: 1rem;
      display: flex;
      align-items: center;
      justify-content: space-between;
      gap: 1rem;
    }}
    details.panel > summary::-webkit-details-marker {{ display: none; }}
    details.panel > summary::after {{
      content: "Open";
      color: var(--muted);
      font-size: 0.78rem;
      letter-spacing: 0.08em;
      text-transform: uppercase;
    }}
    details.panel[open] > summary::after {{ content: "Hide"; }}
    .details-body {{
      padding: 0 1rem 1rem;
      display: grid;
      gap: 1rem;
    }}
    .details-grid {{
      display: grid;
      gap: 1rem;
      grid-template-columns: repeat(auto-fit, minmax(260px, 1fr));
    }}
    details.embedded-details {{
      border: 1px solid var(--line);
      border-radius: 14px;
      background: rgba(255,255,255,0.02);
      overflow: hidden;
    }}
    details.embedded-details > summary {{
      list-style: none;
      cursor: pointer;
      padding: 0.85rem 1rem;
      display: flex;
      align-items: center;
      justify-content: space-between;
      gap: 1rem;
    }}
    details.embedded-details > summary::-webkit-details-marker {{ display: none; }}
    details.embedded-details > summary::after {{
      content: "Open";
      color: var(--muted);
      font-size: 0.76rem;
      letter-spacing: 0.08em;
      text-transform: uppercase;
    }}
    details.embedded-details[open] > summary::after {{ content: "Hide"; }}
    .embedded-body {{
      padding: 0 1rem 1rem;
      display: grid;
      gap: 1rem;
    }}
    .subpanel {{
      display: grid;
      gap: 0.6rem;
    }}
    @media (max-width: 1100px) {{
      .shell {{ width: min(100vw - 1rem, 1320px); }}
      .workspace {{ grid-template-columns: 1fr; }}
    }}
  </style>
</head>
<body>
  <div class="shell">
    <section class="panel hero">
      <div>
        <h1>Parallel Truth Fingerprint</h1>
        <div class="muted">Local SCADA-inspired operator dashboard and control surface for the real prototype flow.</div>
      </div>
      <div class="banner" id="limitation-banner"></div>
      <div class="status-banner" id="runtime-note"></div>
      <div class="error-banner" id="runtime-error" hidden></div>
      <div class="metrics">
        <div class="metric"><span class="label">Runtime</span><span class="value" id="runtime-status">unknown</span></div>
        <div class="metric"><span class="label">Current Cycle</span><span class="value" id="current-cycle">0</span></div>
        <div class="metric"><span class="label">Cadence</span><span class="value" id="cadence-seconds">0s</span></div>
        <div class="metric"><span class="label">Scenario</span><span class="value" id="active-scenario">normal</span></div>
        <div class="metric"><span class="label">Power</span><span class="value" id="configured-power">0%</span></div>
        <div class="metric"><span class="label">Valid Artifacts</span><span class="value" id="artifact-count">0</span></div>
        <div class="metric"><span class="label">Model Status</span><span class="value" id="model-status">unknown</span></div>
        <div class="metric"><span class="label">Fingerprint Validation</span><span class="value" id="validation-level">runtime_valid_only</span></div>
      </div>
    </section>

    <section class="controls">
      <div class="panel">
        <h2>Runtime Control</h2>
        <div class="row">
          <button id="start-runtime">Start Runtime</button>
          <button id="stop-runtime" class="secondary">Stop Runtime</button>
        </div>
      </div>
      <div class="panel">
        <h2>Scenario Control</h2>
        <label>Scenario<select id="scenario-select"></select></label>
        <button id="apply-scenario" class="ghost">Apply Scenario</button>
        <div class="muted" id="scenario-effect-note" style="margin-top: 0.75rem;"></div>
      </div>
      <div class="panel">
        <h2>Compressor Control</h2>
        <label>Operating Level (%)<input id="power-input" type="range" min="0" max="100" step="1"></label>
        <div class="muted">Current input: <span id="power-preview">0</span>%</div>
        <div class="row" style="margin-top: 0.75rem;"><button id="apply-power" class="ghost">Apply Power</button></div>
        <div class="muted" id="power-effect-note" style="margin-top: 0.75rem;"></div>
      </div>
    </section>

    <section class="workspace">
      <div class="panel pipeline-workspace">
        <div class="section-header">
          <div>
            <h2>Prototype Pipeline</h2>
            <div class="pipeline-flow" id="pipeline-flow-summary"></div>
          </div>
          <div class="muted">Physical origin to behavioral interpretation</div>
        </div>
        <div class="pipeline-stage-stack" id="pipeline-stage-stack"></div>
        <details class="embedded-details" id="component-log-details">
          <summary><span>Component Evidence</span></summary>
          <div class="embedded-body">
            <label>Component<select id="component-select">{component_option_markup}</select></label>
            <div class="muted" id="raw-log-note"></div>
            <div class="details-grid">
              <div class="subpanel">
                <div class="muted">Interpreted component events</div>
                <div class="action-list" id="component-events"></div>
              </div>
              <div class="subpanel">
                <div class="muted">Raw component log</div>
                <div class="pre" id="component-raw-log"></div>
              </div>
            </div>
          </div>
        </details>
      </div>

      <div class="summary-stack">
        <div class="panel summary-card">
          <h2>Current Evidence Summary</h2>
          <div class="summary-section">
            <div class="muted">Current interpretation</div>
            <div class="action-list" id="translated-statuses"></div>
          </div>
          <div class="summary-section">
            <div class="muted">Current run facts</div>
            <div class="action-list" id="startup-facts"></div>
          </div>
          <div class="details-grid">
            <div class="subpanel">
              <div class="muted">Happened already</div>
              <ul class="bullet-list" id="happened-already"></ul>
            </div>
            <div class="subpanel">
              <div class="muted">Not happened yet</div>
              <ul class="bullet-list" id="not-happened-yet"></ul>
            </div>
            <div class="subpanel">
              <div class="muted">Expected next</div>
              <ul class="bullet-list" id="expected-next"></ul>
            </div>
          </div>
        </div>

        <div class="panel summary-card">
          <h2>Fingerprint Readiness</h2>
          <div class="muted" id="readiness-summary"></div>
          <div class="details-grid">
            <div class="subpanel">
              <div class="muted">Readiness gate</div>
              <div class="action-list" id="readiness-gate"></div>
            </div>
            <div class="subpanel">
              <div class="muted">Model provenance</div>
              <div class="action-list" id="readiness-provenance"></div>
            </div>
            <div class="subpanel">
              <div class="muted">Training details</div>
              <div class="action-list" id="readiness-training-details"></div>
            </div>
          </div>
          <div class="details-grid">
            <div class="subpanel">
              <div class="muted">Working now</div>
              <ul class="bullet-list" id="readiness-working-now"></ul>
            </div>
            <div class="subpanel">
              <div class="muted">Evidence available</div>
              <ul class="bullet-list" id="readiness-evidence-available"></ul>
            </div>
            <div class="subpanel">
              <div class="muted">Not proven yet</div>
              <ul class="bullet-list" id="readiness-not-proven"></ul>
            </div>
          </div>
          <details class="embedded-details">
            <summary><span>Evidence by Behavior</span></summary>
            <div class="embedded-body">
              <div class="guidance-grid" id="readiness-matrix"></div>
            </div>
          </details>
        </div>
      </div>
    </section>

    <section class="secondary-grid">
      <details class="panel">
        <summary><h2>Transparent Operator Feedback</h2></summary>
        <div class="details-body">
          <div class="action-list" id="operator-actions"></div>
        </div>
      </details>
      <details class="panel">
        <summary><h2>Demo Guidance</h2></summary>
        <div class="details-body">
          <div class="muted" id="guidance-note"></div>
          <div class="guidance-grid" id="guidance-panels"></div>
        </div>
      </details>
      <details class="panel">
        <summary><h2>Operational Event Timeline</h2></summary>
        <div class="details-body">
          <div class="muted">Interpreted events derived from current runtime, cycle history, and operator actions.</div>
          <div class="action-list" id="global-events"></div>
        </div>
      </details>
      <details class="panel">
        <summary><h2>Technical Runtime State</h2></summary>
        <div class="details-body">
          <div class="details-grid">
            <div class="subpanel">
              <h2>Process and Sensor State</h2>
              <div class="pre" id="process-state"></div>
            </div>
            <div class="subpanel">
              <h2>Edge and Consensus State</h2>
              <div class="pre" id="edge-state"></div>
            </div>
            <div class="subpanel">
              <h2>Cycle History</h2>
              <div class="pre" id="cycle-history"></div>
            </div>
          </div>
        </div>
      </details>
      <details class="panel">
        <summary><h2>Raw Channel Details</h2></summary>
        <div class="details-body">
          <div class="details-grid">
            <div class="subpanel"><h2>SCADA Divergence</h2><div class="pre" id="channel-scada"></div></div>
            <div class="subpanel"><h2>Consensus Status</h2><div class="pre" id="channel-consensus"></div></div>
            <div class="subpanel"><h2>Fingerprint Inference</h2><div class="pre" id="channel-fingerprint"></div></div>
            <div class="subpanel"><h2>Replay Behavior</h2><div class="pre" id="channel-replay"></div></div>
          </div>
        </div>
      </details>
    </section>
  </div>
  <script>
    const initialState = {initial_state_json};
    async function postJson(url, payload = {{}}) {{
      const response = await fetch(url, {{
        method: "POST",
        headers: {{ "Content-Type": "application/json" }},
        body: JSON.stringify(payload),
      }});
      return response.json();
    }}
    function formatJson(value) {{
      return JSON.stringify(value ?? {{}}, null, 2);
    }}
    function renderBulletList(rootId, items, emptyText) {{
      const root = document.getElementById(rootId);
      root.innerHTML = "";
      if (!items.length) {{
        const li = document.createElement("li");
        li.textContent = emptyText;
        root.appendChild(li);
        return;
      }}
      for (const item of items) {{
        const li = document.createElement("li");
        li.textContent = item;
        root.appendChild(li);
      }}
    }}
    function renderEvents(rootId, events, emptyText) {{
      const root = document.getElementById(rootId);
      root.innerHTML = "";
      if (!events.length) {{
        root.innerHTML = `<div class="muted">${{emptyText}}</div>`;
        return;
      }}
      for (const event of events) {{
        const div = document.createElement("div");
        div.className = "event";
        div.innerHTML = `
          <small>${{event.runtime_reference ?? "runtime"}} | ${{event.recorded_at ?? "n/a"}}</small>
          <div><strong>${{event.component_label ?? event.component ?? "component"}}</strong></div>
          <div>${{event.message ?? "No interpreted event message available."}}</div>
        `;
        root.appendChild(div);
      }}
    }}
    function renderTranslatedStatuses(translatedStatuses) {{
      const root = document.getElementById("translated-statuses");
      root.innerHTML = "";
      const entries = Object.entries(translatedStatuses ?? {{}});
      if (!entries.length) {{
        root.innerHTML = '<div class="muted">No translated statuses available yet.</div>';
        return;
      }}
      for (const [, status] of entries) {{
        const div = document.createElement("div");
        div.className = "status-card";
        div.innerHTML = `
          <strong>${{status.label ?? "Status"}}</strong>
          <div class="muted">raw=${{status.raw_value ?? "unknown"}}</div>
          <div>${{status.explanation ?? ""}}</div>
        `;
        root.appendChild(div);
      }}
    }}
    function renderLabelValueList(rootId, items, emptyText) {{
      const root = document.getElementById(rootId);
      root.innerHTML = "";
      if (!items.length) {{
        root.innerHTML = `<div class="muted">${{emptyText}}</div>`;
        return;
      }}
      for (const item of items) {{
        const div = document.createElement("div");
        div.className = "action";
        div.innerHTML = `
          <div><strong>${{item.label ?? "Field"}}</strong></div>
          <div>${{item.value ?? "not_available"}}</div>
        `;
        root.appendChild(div);
      }}
    }}
    function renderPipeline(pipelineView) {{
      document.getElementById("pipeline-flow-summary").textContent =
        pipelineView?.flow_summary ?? "No pipeline summary available yet.";
      const stageRoot = document.getElementById("pipeline-stage-stack");
      stageRoot.innerHTML = "";
      for (const row of pipelineView?.rows ?? []) {{
        const stage = document.createElement("section");
        stage.className = "pipeline-stage";
        const titleMarkup = `
          <div class="pipeline-stage-header">
            <div class="pipeline-label">${{row.label ?? "Pipeline stage"}}</div>
            <div class="pipeline-stage-summary">${{row.summary ?? ""}}</div>
          </div>
        `;
        const cards = document.createElement("div");
        cards.className = `pipeline-row ${{row.id ?? ""}}`;
        for (const node of row.nodes ?? []) {{
          const card = document.createElement("div");
          card.className = `pipeline-card ${{node.kind ?? ""}}`;
          const metricsMarkup = (node.metrics ?? [])
            .map(
              (metric) => `
                <div class="pipeline-metric">
                  <span class="metric-label">${{metric.label ?? "Metric"}}</span>
                  <span class="metric-value">${{metric.value ?? "n/a"}}</span>
                </div>
              `
            )
            .join("");
          card.innerHTML = `
            <h3>${{node.title ?? "Component"}}</h3>
            <div class="pipeline-status">${{node.status ?? "No live status available yet."}}</div>
            <div class="pipeline-metrics">${{metricsMarkup}}</div>
            <button type="button" data-component="${{node.log_component_id ?? node.component_id}}">Open logs</button>
          `;
          card.querySelector("button")?.addEventListener("click", (event) => {{
            const componentId = event.currentTarget.dataset.component;
            const componentSelect = document.getElementById("component-select");
            componentSelect.value = componentId;
            document.getElementById("component-log-details").open = true;
            renderState(window.__dashboardState ?? initialState);
          }});
          cards.appendChild(card);
        }}
        stage.innerHTML = titleMarkup;
        stage.appendChild(cards);
        stageRoot.appendChild(stage);
      }}
      if ((pipelineView?.channel_separation ?? []).length) {{
        const stage = document.createElement("section");
        stage.className = "pipeline-stage";
        stage.innerHTML = `
          <div class="pipeline-stage-header">
            <div class="pipeline-label">Distinct output channels</div>
            <div class="pipeline-stage-summary">These channels remain separate so the operator can tell consensus, SCADA divergence, and replay behavior apart.</div>
          </div>
        `;
        const channelRoot = document.createElement("div");
        channelRoot.className = "channel-strip";
        for (const channel of pipelineView?.channel_separation ?? []) {{
          const badge = document.createElement("div");
          badge.className = "channel-badge";
          badge.innerHTML = `
            <strong>${{channel.label ?? "Channel"}}</strong>
            <div class="muted">status=${{channel.status ?? "unknown"}}</div>
            <div>${{channel.explanation ?? ""}}</div>
          `;
          channelRoot.appendChild(badge);
        }}
        stage.appendChild(channelRoot);
        stageRoot.appendChild(stage);
      }}
    }}
    function renderGuidance(guidanceView) {{
      document.getElementById("guidance-note").textContent =
        guidanceView?.raw_evidence_note ?? "";
      const root = document.getElementById("guidance-panels");
      root.innerHTML = "";
      for (const panel of guidanceView?.panels ?? []) {{
        const card = document.createElement("div");
        card.className = "guidance-card";
        const bulletsMarkup = (panel.bullets ?? [])
          .map((bullet) => `<li>${{bullet}}</li>`)
          .join("");
        card.innerHTML = `
          <strong>${{panel.title ?? "Guidance"}}</strong>
          <div>${{panel.summary ?? ""}}</div>
          <ul class="bullet-list">${{bulletsMarkup}}</ul>
        `;
        root.appendChild(card);
      }}
      if (!(guidanceView?.panels ?? []).length) {{
        root.innerHTML = '<div class="muted">No demo guidance is available yet.</div>';
      }}
    }}
    function renderFingerprintReadiness(readinessView) {{
      document.getElementById("readiness-summary").textContent =
        readinessView?.summary ?? "No fingerprint readiness evidence is available yet.";
      renderLabelValueList(
        "readiness-gate",
        [
          {{
            label: "Readiness state",
            value: readinessView?.readiness_state?.label ?? "not_available",
          }},
          {{
            label: "Adequacy gate",
            value: readinessView?.adequacy_gate?.summary ?? "not_available",
          }},
          {{
            label: "Validation level",
            value: readinessView?.adequacy_gate?.validation_level ?? "runtime_valid_only",
          }},
        ],
        "No readiness gate is available yet."
      );
      renderLabelValueList(
        "readiness-provenance",
        [
          {{
            label: "Model identity",
            value: readinessView?.provenance?.model_identity ?? "not_available",
          }},
          {{
            label: "Model id",
            value: readinessView?.provenance?.model_id ?? "not_available",
          }},
          {{
            label: "Source dataset",
            value: readinessView?.provenance?.source_dataset_id ?? "not_available",
          }},
          {{
            label: "Training windows",
            value: readinessView?.provenance?.training_window_count ?? "not_available",
          }},
          {{
            label: "Threshold origin",
            value: readinessView?.provenance?.threshold_origin ?? "not_available",
          }},
        ],
        "No model provenance is available yet."
      );
      renderLabelValueList(
        "readiness-training-details",
        [
          {{
            label: "First training",
            value: readinessView?.training_details?.first_training_reference ?? "not_available",
          }},
          {{
            label: "Current model usage",
            value: readinessView?.training_details?.current_model_usage ?? "not_available",
          }},
          {{
            label: "Trained at",
            value: readinessView?.training_details?.trained_at ?? "not_available",
          }},
          {{
            label: "Epochs / batch",
            value: `${{readinessView?.training_details?.epochs ?? "not_available"}} / ${{readinessView?.training_details?.batch_size ?? "not_available"}}`,
          }},
          {{
            label: "Loss / final loss",
            value: `${{readinessView?.training_details?.loss_name ?? "not_available"}} / ${{readinessView?.training_details?.final_training_loss ?? "not_available"}}`,
          }},
          {{
            label: "Sequence / features",
            value: `${{readinessView?.training_details?.sequence_length ?? "not_available"}} / ${{readinessView?.training_details?.feature_schema ?? "not_available"}}`,
          }},
        ],
        "No training details are available yet."
      );
      renderBulletList(
        "readiness-working-now",
        readinessView?.working_now ?? [],
        "No active readiness evidence is available yet."
      );
      renderBulletList(
        "readiness-evidence-available",
        readinessView?.evidence_available ?? [],
        "No readiness evidence is available yet."
      );
      renderBulletList(
        "readiness-not-proven",
        readinessView?.not_proven_yet ?? [],
        "No outstanding readiness limitations are listed."
      );
      const root = document.getElementById("readiness-matrix");
      root.innerHTML = "";
      for (const item of readinessView?.evidence_matrix ?? []) {{
        const card = document.createElement("div");
        card.className = "guidance-card";
        const bulletsMarkup = (item.evidence ?? [])
          .map((bullet) => `<li>${{bullet}}</li>`)
          .join("");
        card.innerHTML = `
          <strong>${{item.label ?? "Evidence"}}</strong>
          <div class="muted">status=${{item.status ?? "unknown"}}</div>
          <div>${{item.summary ?? ""}}</div>
          <ul class="bullet-list">${{bulletsMarkup}}</ul>
        `;
        root.appendChild(card);
      }}
      if (!(readinessView?.evidence_matrix ?? []).length) {{
        root.innerHTML = '<div class="muted">No behavior evidence matrix is available yet.</div>';
      }}
    }}
    function renderStartupEvidence(evidenceView) {{
      const whatChanged = evidenceView?.what_changed_since_startup ?? {{}};
      renderLabelValueList(
        "startup-facts",
        [
          {{
            label: "Runtime start",
            value: whatChanged.runtime_start_time ?? "not_available",
          }},
          {{
            label: "Elapsed runtime",
            value: whatChanged.elapsed_runtime ?? "not_available",
          }},
          {{
            label: "Current cycle",
            value: whatChanged.current_cycle_count ?? "0",
          }},
          {{
            label: "Artifact growth",
            value: whatChanged.valid_artifact_count_growth?.summary ?? "not_available",
          }},
          {{
            label: "Fingerprint created",
            value: whatChanged.questions_answered?.has_fingerprint_been_created ?? "not_available",
          }},
          {{
            label: "Current model usage",
            value: whatChanged.training?.current_model_usage ?? "not_available",
          }},
        ],
        "No current-run evidence is available yet."
      );
      renderBulletList(
        "happened-already",
        whatChanged.happened_already ?? [],
        "No completed evidence is available yet."
      );
      renderBulletList(
        "not-happened-yet",
        whatChanged.not_happened_yet ?? [],
        "No pending milestones are currently listed."
      );
      const expectedItems = [];
      if (whatChanged.expected_next?.summary) {{
        expectedItems.push(whatChanged.expected_next.summary);
      }}
      document.getElementById("limitation-banner").textContent = whatChanged.limitation ?? "";
      renderBulletList(
        "expected-next",
        expectedItems,
        "No next-step prediction is available yet."
      );
    }}
    function renderActions(actions) {{
      const root = document.getElementById("operator-actions");
      root.innerHTML = "";
      if (!actions.length) {{
        root.innerHTML = '<div class="muted">No operator actions yet.</div>';
        return;
      }}
      for (const action of actions) {{
        const div = document.createElement("div");
        div.className = "action";
        div.innerHTML = `
          <div><strong>${{action.action}}</strong> <span class="muted">applied_at=${{action.applied_at}}</span></div>
          <div class="muted">cycle=${{action.applies_on_cycle}} command=${{action.runtime_command}}</div>
          <div class="muted">effect_scope=${{action.effect_scope ?? "unknown"}}</div>
          <div class="muted">config=${{JSON.stringify(action.configuration_change)}}</div>
          <div class="muted">expected_outputs=${{action.expected_output_channels.join(", ")}}</div>
          <div>${{action.note}}</div>
        `;
        root.appendChild(div);
      }}
    }}
    function renderState(state) {{
      const runtime = state.runtime ?? {{}};
      const controls = state.controls ?? {{}};
      const monitoring = state.monitoring ?? {{}};
      const lifecycle = monitoring.lifecycle ?? {{}};
      const channels = state.channels ?? {{}};
      const events = state.events ?? {{}};
      const pipeline = state.pipeline ?? {{}};
      const explainability = state.explainability ?? {{}};
      const guidance = state.guidance ?? {{}};
      document.getElementById("runtime-status").textContent = runtime.ui_status ?? "unknown";
      document.getElementById("current-cycle").textContent = runtime.current_cycle ?? 0;
      document.getElementById("cadence-seconds").textContent = `${{runtime.cycle_interval_seconds ?? 0}}s`;
      document.getElementById("active-scenario").textContent = monitoring.active_scenario ?? controls.configured_scenario ?? "normal";
      document.getElementById("configured-power").textContent = `${{controls.configured_power_pct ?? 0}}%`;
      document.getElementById("artifact-count").textContent = monitoring.valid_artifact_accumulation?.count ?? 0;
      document.getElementById("model-status").textContent = lifecycle.model_status ?? "unknown";
      document.getElementById("validation-level").textContent = state.limitations?.source_dataset_validation_level ?? "runtime_valid_only";
      document.getElementById("limitation-banner").textContent = state.limitations?.note ?? "";
      document.getElementById("runtime-note").textContent = runtime.status_note ?? "";
      const runtimeError = document.getElementById("runtime-error");
      if (runtime.last_error) {{
        runtimeError.hidden = false;
        runtimeError.textContent = `Active failure: ${{runtime.last_error}}`;
      }} else {{
        runtimeError.hidden = true;
        runtimeError.textContent = "";
      }}
      const applyMode = controls.apply_mode ?? "next_start";
      document.getElementById("scenario-effect-note").textContent =
        controls.runtime_effect_note ?? "";
      document.getElementById("power-effect-note").textContent =
        controls.runtime_effect_note ?? "";
      document.getElementById("apply-scenario").textContent =
        applyMode === "next_cycle"
          ? "Apply Next Cycle"
          : applyMode === "queued_until_runtime_stabilizes"
            ? "Queue Scenario"
            : "Save For Next Start";
      document.getElementById("apply-power").textContent =
        applyMode === "next_cycle"
          ? "Apply Next Cycle"
          : applyMode === "queued_until_runtime_stabilizes"
            ? "Queue Power Change"
            : "Save For Next Start";
      document.getElementById("start-runtime").disabled =
        runtime.ui_status === "starting" || runtime.ui_status === "running";
      document.getElementById("stop-runtime").disabled =
        runtime.ui_status === "stopped";
      const scenarioSelect = document.getElementById("scenario-select");
      if (!scenarioSelect.options.length) {{
        for (const scenario of controls.supported_scenarios ?? []) {{
          const option = document.createElement("option");
          option.value = scenario;
          option.textContent = scenario;
          scenarioSelect.appendChild(option);
        }}
      }}
      scenarioSelect.value = controls.configured_scenario ?? "normal";
      const powerInput = document.getElementById("power-input");
      powerInput.value = String(controls.configured_power_pct ?? 0);
      document.getElementById("power-preview").textContent = powerInput.value;
      const componentSelect = document.getElementById("component-select");
      if (events.components?.length && !componentSelect.dataset.initialized) {{
        componentSelect.innerHTML = "";
        for (const component of events.components) {{
          const option = document.createElement("option");
          option.value = component.id;
          option.textContent = component.label;
          componentSelect.appendChild(option);
        }}
        componentSelect.dataset.initialized = "true";
      }}
      const selectedComponent = componentSelect.value || "compressor";
      renderActions(state.operator_feedback?.actions ?? []);
      renderPipeline(pipeline);
      renderTranslatedStatuses(explainability.translated_statuses ?? {{}});
      renderFingerprintReadiness(explainability.fingerprint_readiness ?? {{}});
      renderGuidance(guidance);
      renderStartupEvidence(explainability);
      renderEvents(
        "global-events",
        events.global_timeline ?? [],
        "No interpreted events available yet."
      );
      renderEvents(
        "component-events",
        events.component_timelines?.[selectedComponent] ?? [],
        "No interpreted events available for this component yet."
      );
      document.getElementById("component-raw-log").textContent = formatJson(
        events.component_raw_logs?.[selectedComponent] ?? {{}}
      );
      document.getElementById("raw-log-note").textContent =
        events.raw_log_ground_truth_note ?? "";
      document.getElementById("process-state").textContent = formatJson({{
        compressor_state: monitoring.compressor_state,
        sensor_values: monitoring.sensor_values,
        scada_state: monitoring.scada_state,
        comparison_output: monitoring.comparison_output,
      }});
      document.getElementById("edge-state").textContent = formatJson({{
        edge_status: monitoring.edge_status,
        quorum_consensus: monitoring.quorum_consensus,
        lifecycle: monitoring.lifecycle,
      }});
      document.getElementById("cycle-history").textContent = formatJson(monitoring.cycle_history ?? []);
      document.getElementById("channel-scada").textContent = formatJson(channels.scada_divergence);
      document.getElementById("channel-consensus").textContent = formatJson(channels.consensus);
      document.getElementById("channel-fingerprint").textContent = formatJson(channels.fingerprint_inference);
      document.getElementById("channel-replay").textContent = formatJson(channels.replay_behavior);
    }}
    async function refreshState() {{
      const response = await fetch("/api/state");
      const state = await response.json();
      window.__dashboardState = state;
      renderState(state);
    }}
    document.getElementById("start-runtime").addEventListener("click", async () => {{ await postJson("/api/runtime/start"); await refreshState(); }});
    document.getElementById("stop-runtime").addEventListener("click", async () => {{ await postJson("/api/runtime/stop"); await refreshState(); }});
    document.getElementById("apply-scenario").addEventListener("click", async () => {{
      await postJson("/api/control/scenario", {{ scenario: document.getElementById("scenario-select").value }});
      await refreshState();
    }});
    document.getElementById("apply-power").addEventListener("click", async () => {{
      await postJson("/api/control/power", {{ power: Number(document.getElementById("power-input").value) }});
      await refreshState();
    }});
    document.getElementById("power-input").addEventListener("input", (event) => {{
      document.getElementById("power-preview").textContent = event.target.value;
    }});
    document.getElementById("component-select").addEventListener("change", () => {{
      renderState(window.__dashboardState ?? initialState);
    }});
    window.__dashboardState = initialState;
    renderState(initialState);
    setInterval(async () => {{
      const response = await fetch("/api/state");
      const state = await response.json();
      window.__dashboardState = state;
      renderState(state);
    }}, 2000);
  </script>
</body>
</html>
"""
