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
    note: str

    def to_dict(self) -> dict[str, object]:
        return {
            "action": self.action,
            "applied_at": self.applied_at,
            "applies_on_cycle": self.applies_on_cycle,
            "runtime_command": self.runtime_command,
            "configuration_change": self.configuration_change,
            "expected_output_channels": list(self.expected_output_channels),
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
            applies_on_cycle = 1 if not self._is_runtime_active_locked() else self._current_cycle_locked() + 1
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
                note=(
                    f"Dashboard configured scenario '{normalized_name}' "
                    f"to activate on cycle {applies_on_cycle}."
                ),
            )
            return self.build_dashboard_state()

    def set_power(self, operating_level_pct: float) -> dict[str, object]:
        """Update the compressor operating level for later cycles."""

        with self._lock:
            clamped_power = self._clamp_power(operating_level_pct)
            applies_on_cycle = 1 if not self._is_runtime_active_locked() else self._current_cycle_locked() + 1
            self._configured_power = clamped_power
            self._append_action(
                action="set_power",
                applies_on_cycle=applies_on_cycle,
                runtime_command=f"set_power({clamped_power})",
                configuration_change={"demo_power": clamped_power},
                expected_output_channels=POWER_OUTPUT_CHANNELS,
                note=(
                    f"Dashboard configured compressor operating level to {clamped_power}% "
                    f"starting on cycle {applies_on_cycle}."
                ),
            )
            return self.build_dashboard_state()

    def build_dashboard_state(self) -> dict[str, object]:
        """Return one inspectable dashboard state payload for the UI."""

        with self._lock:
            latest_payload = self._latest_runtime_payload or {}
            latest_cycle = latest_payload.get("latest_cycle") or {}
            runtime_info = latest_payload.get("runtime") or {}
            scenario_info = latest_payload.get("scenario_control") or {}
            fingerprint_lifecycle = latest_cycle.get("fingerprint_lifecycle") or {}
            simulator_snapshot = latest_cycle.get("simulator_snapshot") or {}

            validation_level = (
                fingerprint_lifecycle.get("source_dataset_validation_level")
                or "runtime_valid_only"
            )
            limitation_note = (
                fingerprint_lifecycle.get("limitation_note")
                or "The fingerprint base is still runtime-valid only, not yet meaningful-fingerprint-valid, because the adequacy floor remains below target."
            )

            return {
                "generated_at": _utc_now(),
                "runtime": {
                    "ui_status": self._runtime_status,
                    "is_running": self._is_runtime_active_locked(),
                    "last_runtime_status": self._last_runtime_status,
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
                },
                "operator_feedback": {
                    "actions": [action.to_dict() for action in reversed(self._action_log)],
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
                note=note,
            )
        )

    def _is_runtime_active_locked(self) -> bool:
        return self._runtime_status in {"starting", "running", "stopping"}

    def _current_cycle_locked(self) -> int:
        if self._latest_runtime_payload is None:
            return 0
        return int(self._latest_runtime_payload.get("runtime", {}).get("current_cycle", 0))

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
      font-family: "IBM Plex Mono", "Consolas", monospace;
      color: var(--text);
      background:
        radial-gradient(circle at top right, rgba(70,212,181,0.14), transparent 24rem),
        linear-gradient(160deg, #0c1014, var(--bg));
    }}
    .shell {{ width: min(1440px, calc(100vw - 2rem)); margin: 1rem auto 2rem; display: grid; gap: 1rem; }}
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
    .metrics, .controls, .grid {{ display: grid; gap: 1rem; }}
    .metrics {{ grid-template-columns: repeat(auto-fit, minmax(160px, 1fr)); }}
    .controls {{ grid-template-columns: repeat(auto-fit, minmax(260px, 1fr)); }}
    .grid {{ grid-template-columns: repeat(auto-fit, minmax(420px, 1fr)); align-items: start; }}
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
      </div>
      <div class="panel">
        <h2>Compressor Control</h2>
        <label>Operating Level (%)<input id="power-input" type="range" min="0" max="100" step="1"></label>
        <div class="muted">Current input: <span id="power-preview">0</span>%</div>
        <div class="row" style="margin-top: 0.75rem;"><button id="apply-power" class="ghost">Apply Power</button></div>
      </div>
    </section>

    <section class="grid">
      <div class="panel">
        <h2>Transparent Operator Feedback</h2>
        <div class="action-list" id="operator-actions"></div>
      </div>
      <div class="panel">
        <h2>Process and Sensor State</h2>
        <div class="pre" id="process-state"></div>
      </div>
      <div class="panel">
        <h2>Edge and Consensus State</h2>
        <div class="pre" id="edge-state"></div>
      </div>
      <div class="panel">
        <h2>Cycle History</h2>
        <div class="pre" id="cycle-history"></div>
      </div>
    </section>

    <section class="grid">
      <div class="panel"><h2>SCADA Divergence</h2><div class="pre" id="channel-scada"></div></div>
      <div class="panel"><h2>Consensus Status</h2><div class="pre" id="channel-consensus"></div></div>
      <div class="panel"><h2>Fingerprint Inference</h2><div class="pre" id="channel-fingerprint"></div></div>
      <div class="panel"><h2>Replay Behavior</h2><div class="pre" id="channel-replay"></div></div>
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
      document.getElementById("runtime-status").textContent = runtime.ui_status ?? "unknown";
      document.getElementById("current-cycle").textContent = runtime.current_cycle ?? 0;
      document.getElementById("cadence-seconds").textContent = `${{runtime.cycle_interval_seconds ?? 0}}s`;
      document.getElementById("active-scenario").textContent = monitoring.active_scenario ?? controls.configured_scenario ?? "normal";
      document.getElementById("configured-power").textContent = `${{controls.configured_power_pct ?? 0}}%`;
      document.getElementById("artifact-count").textContent = monitoring.valid_artifact_accumulation?.count ?? 0;
      document.getElementById("model-status").textContent = lifecycle.model_status ?? "unknown";
      document.getElementById("validation-level").textContent = state.limitations?.source_dataset_validation_level ?? "runtime_valid_only";
      document.getElementById("limitation-banner").textContent = state.limitations?.note ?? "";
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
      renderActions(state.operator_feedback?.actions ?? []);
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
      renderState(await response.json());
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
    renderState(initialState);
    setInterval(refreshState, 2000);
  </script>
</body>
</html>
"""
