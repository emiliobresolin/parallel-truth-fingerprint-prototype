"""Fake OPC UA logical SCADA service for the local prototype."""

from __future__ import annotations

from dataclasses import dataclass, replace
import importlib.util
from math import isfinite
from parallel_truth_fingerprint.config.ranges import DEFAULT_COMPRESSOR_PROFILE, SensorRange

from parallel_truth_fingerprint.contracts.edge_local_replicated_state import (
    EdgeLocalReplicatedStateContract,
)
from parallel_truth_fingerprint.contracts.raw_hart_payload import RawHartPayload
from parallel_truth_fingerprint.contracts.consensused_valid_state import (
    ConsensusedValidState,
)
from parallel_truth_fingerprint.contracts.scada_state import (
    ScadaBehavioralSensorState,
    ScadaSensorState,
    ScadaState,
)

SUPPORTED_SCADA_SENSORS = ("temperature", "pressure", "rpm")
SCADA_SENSOR_UNITS = {
    "temperature": "degC",
    "pressure": "bar",
    "rpm": "rpm",
    "mass_flow": "kg/h",
}
SUPPORTED_OVERRIDE_MODES = {"match", "offset", "freeze", "replay"}


@dataclass(frozen=True)
class ScadaSensorOverride:
    """Logical divergence controls; offset and fixed_value are in mA."""

    mode: str = "match"
    offset: float = 0.0
    fixed_value: float | None = None
    replay_round_id: str | None = None


class FakeOpcUaScadaService:
    """Expose the logical SCADA-side view through a local OPC UA server.

    The service stays deliberately small:
    - it consumes the consensused valid state
    - it projects a logical supervisory state
    - it exposes temperature, pressure, and rpm over OPC UA
    - it supports additive match/offset/freeze/replay supervisory overrides
    """

    def __init__(
        self,
        *,
        endpoint_url: str = "opc.tcp://127.0.0.1:4841/ptf/scada/server/",
        namespace_uri: str = "urn:parallel-truth-fingerprint:scada",
        compressor_id: str = "compressor-1",
        sensor_names: tuple[str, ...] = SUPPORTED_SCADA_SENSORS,
        sensor_ranges: dict[str, SensorRange] | None = None,
    ) -> None:
        self.endpoint_url = endpoint_url
        self.namespace_uri = namespace_uri
        self.compressor_id = compressor_id
        if not set(SUPPORTED_SCADA_SENSORS).issubset(sensor_names) or set(sensor_names)-set(SCADA_SENSOR_UNITS):
            raise ValueError('Unsupported SCADA sensor configuration.')
        self.sensor_names = tuple(sensor_names)
        if sensor_ranges is None:
            sensor_ranges = {
                name: SensorRange(0.0, 1000.0) if name == 'mass_flow'
                else getattr(DEFAULT_COMPRESSOR_PROFILE, name)
                for name in self.sensor_names
            }
        if not isinstance(sensor_ranges, dict) or set(sensor_ranges) != set(self.sensor_names):
            raise ValueError('SCADA display ranges must cover exactly the configured sensors.')
        for limits in sensor_ranges.values():
            if (not isinstance(limits, SensorRange)
                    or any(isinstance(v, bool) or not isinstance(v, (int, float)) or not isfinite(v)
                           for v in (limits.minimum, limits.maximum))
                    or limits.minimum >= limits.maximum):
                raise ValueError('SCADA display ranges must be finite increasing SensorRange values.')
        self._sensor_ranges = dict(sensor_ranges)
        self._server = None
        self._namespace_index: int | None = None
        self._sensor_nodes: dict[str, object] = {}
        self._current_state: ScadaState | None = None
        self._history: list[ScadaState] = []
        self._frozen_values: dict[str, float] = {}
        self._frozen_states: dict[str, ScadaBehavioralSensorState] = {}
        self._current_nodes: dict[str, object] = {}
        self._totalizer_nodes: dict[str, object] = {}
        self._totalizer_available_nodes: dict[str, object] = {}
        self._overrides = {
            sensor_name: ScadaSensorOverride() for sensor_name in self.sensor_names
        }

    @property
    def namespace_index(self) -> int | None:
        """Return the namespace index used by the running OPC UA server."""

        return self._namespace_index

    def current_state(self) -> ScadaState | None:
        """Return the latest logical SCADA state."""

        return self._current_state

    def history(self) -> tuple[ScadaState, ...]:
        """Return previously projected logical SCADA states."""

        return tuple(self._history)

    def set_sensor_override(
        self,
        sensor_name: str,
        *,
        mode: str = "match",
        offset: float = 0.0,
        fixed_value: float | None = None,
        replay_round_id: str | None = None,
    ) -> None:
        """Configure divergence in acquired-current mA before display projection."""

        self._validate_sensor_name(sensor_name)
        if mode not in SUPPORTED_OVERRIDE_MODES:
            raise ValueError(
                f"Unsupported SCADA override mode '{mode}'. "
                f"Expected one of {sorted(SUPPORTED_OVERRIDE_MODES)}."
            )

        if not isfinite(float(offset)) or (fixed_value is not None and not isfinite(float(fixed_value))):
            raise ValueError("Overrides must be finite mA values.")
        override = ScadaSensorOverride(
            mode=mode,
            offset=offset,
            fixed_value=None if fixed_value is None else float(fixed_value),
            replay_round_id=replay_round_id,
        )
        if override.mode == "freeze" and self._overrides[sensor_name] == override:
            return
        self._frozen_states.pop(sensor_name, None)
        self._overrides[sensor_name] = override
        if mode != "freeze":
            self._frozen_values.pop(sensor_name, None)
        elif override.fixed_value is not None:
            self._frozen_values[sensor_name] = override.fixed_value

    def clear_sensor_override(self, sensor_name: str) -> None:
        """Reset one sensor to normal matching behavior."""

        self._validate_sensor_name(sensor_name)
        self._overrides[sensor_name] = ScadaSensorOverride()
        self._frozen_values.pop(sensor_name, None)
        self._frozen_states.pop(sensor_name, None)

    def clear_overrides(self) -> None:
        """Reset all sensors to normal matching behavior."""

        for sensor_name in self.sensor_names:
            self._overrides[sensor_name] = ScadaSensorOverride()
        self._frozen_values.clear()
        self._frozen_states.clear()

    def update_from_consensused_state(
        self,
        valid_state: ConsensusedValidState,
        *,
        source_replicated_state: EdgeLocalReplicatedStateContract | None = None,
    ) -> ScadaState:
        """Project logical supervisory values from the current valid state."""

        logical_state = self.project_state(
            valid_state,
            source_replicated_state=source_replicated_state,
        )
        self._current_state = logical_state
        self._history.append(logical_state)
        return logical_state

    def project_state(
        self,
        valid_state: ConsensusedValidState,
        *,
        source_replicated_state: EdgeLocalReplicatedStateContract | None = None,
    ) -> ScadaState:
        """Build one logical SCADA state without writing it to the OPC UA server."""

        missing = set(self.sensor_names).symmetric_difference(valid_state.sensor_values)
        if missing:
            raise ValueError(
                "ConsensusedValidState is missing SCADA sensor values for: "
                f"{sorted(missing)}"
            )

        sensor_values: dict[str, ScadaSensorState] = {}
        behavioral_sensor_values = self._build_behavioral_sensor_values(
            valid_state=valid_state,
            source_replicated_state=source_replicated_state,
        )
        for sensor_name in self.sensor_names:
            override = self._overrides[sensor_name]
            current = self._apply_behavioral_override(
                sensor_name=sensor_name,
                current_state=behavioral_sensor_values[sensor_name],
                override=override,
            )
            behavioral_sensor_values[sensor_name] = current
            sensor_range = self._sensor_ranges[sensor_name]
            projected_value = sensor_range.minimum + (current.loop_current_ma - 4.0) / 16.0 * (sensor_range.maximum - sensor_range.minimum)
            sensor_values[sensor_name] = ScadaSensorState(
                value=projected_value,
                unit=SCADA_SENSOR_UNITS[sensor_name],
                mode=override.mode,
            )

        return ScadaState(
            compressor_id=self.compressor_id,
            source_round_id=valid_state.round_identity.round_id,
            timestamp=valid_state.round_identity.window_ended_at.isoformat(),
            sensor_values=sensor_values,
            behavioral_source_round_id=self._behavioral_source_round_id(
                behavioral_sensor_values
            ),
            behavioral_sensor_values=behavioral_sensor_values or None,
        )

    async def start(self) -> None:
        """Start the local OPC UA server for the fake SCADA layer."""

        if self._server is not None:
            return

        self._require_asyncua()
        from asyncua import Server

        server = Server()
        await server.init()
        server.set_endpoint(self.endpoint_url)
        server.set_server_name("Parallel Truth Fingerprint Fake SCADA")
        namespace_index = await server.register_namespace(self.namespace_uri)
        compressor_node = await server.nodes.objects.add_object(
            namespace_index,
            self.compressor_id,
        )

        sensor_nodes: dict[str, object] = {}
        for sensor_name in self.sensor_names:
            node = await compressor_node.add_variable(namespace_index, sensor_name, 0.0)
            await node.set_writable()
            await node.add_property(namespace_index, "unit", SCADA_SENSOR_UNITS[sensor_name])
            current_node = await compressor_node.add_variable(namespace_index, f"{sensor_name}_current_ma", 0.0)
            await current_node.add_property(namespace_index, "unit", "mA")
            self._current_nodes[sensor_name] = current_node
            if sensor_name == 'mass_flow':
                totalizer_node = await compressor_node.add_variable(namespace_index, 'mass_flow_totalizer1_kg', 0.0)
                await totalizer_node.add_property(namespace_index, 'unit', 'kg')
                available_node = await totalizer_node.add_property(namespace_index, 'available', False)
                self._totalizer_nodes[sensor_name] = totalizer_node
                self._totalizer_available_nodes[sensor_name] = available_node
            sensor_nodes[sensor_name] = node

        self._server = server
        self._namespace_index = namespace_index
        self._sensor_nodes = sensor_nodes
        await self._server.start()

        if self._current_state is not None:
            await self._write_state_to_server(self._current_state)

    async def stop(self) -> None:
        """Stop the local OPC UA server if it is running."""

        if self._server is None:
            return
        await self._server.stop()
        self._server = None
        self._namespace_index = None
        self._sensor_nodes = {}
        self._current_nodes = {}

    async def publish_consensused_state(
        self,
        valid_state: ConsensusedValidState,
        *,
        source_replicated_state: EdgeLocalReplicatedStateContract | None = None,
    ) -> ScadaState:
        """Project and publish one logical SCADA state."""

        logical_state = self.update_from_consensused_state(
            valid_state,
            source_replicated_state=source_replicated_state,
        )
        if self._server is not None:
            await self._write_state_to_server(logical_state)
        return logical_state

    async def read_live_values(self) -> dict[str, float]:
        """Read the currently exposed OPC UA variable values from the running server."""

        if self._server is None:
            raise RuntimeError("OPC UA server must be running before reading live values.")
        return {
            sensor_name: await self._sensor_nodes[sensor_name].read_value()
            for sensor_name in self.sensor_names
        }

    async def _write_state_to_server(self, logical_state: ScadaState) -> None:
        for sensor_name, sensor_state in logical_state.sensor_values.items():
            await self._sensor_nodes[sensor_name].write_value(sensor_state.value)
            await self._current_nodes[sensor_name].write_value(logical_state.behavioral_sensor_values[sensor_name].loop_current_ma)
            if sensor_name in self._totalizer_nodes:
                totalizer = logical_state.behavioral_sensor_values[sensor_name].totalizer1_kg
                await self._totalizer_available_nodes[sensor_name].write_value(totalizer is not None)
                if totalizer is not None:
                    await self._totalizer_nodes[sensor_name].write_value(totalizer)

    def _build_behavioral_sensor_values(
        self,
        *,
        valid_state: ConsensusedValidState,
        source_replicated_state: EdgeLocalReplicatedStateContract | None,
    ) -> dict[str, ScadaBehavioralSensorState]:
        round_id = valid_state.round_identity.round_id
        behavioral_sensor_values: dict[str, ScadaBehavioralSensorState] = {}
        for sensor_name in self.sensor_names:
            current = float(valid_state.sensor_values[sensor_name])
            if not isfinite(current):
                raise ValueError("SCADA projection requires finite acquired currents in mA.")
            state = ScadaBehavioralSensorState(source_round_id=round_id)
            if source_replicated_state is not None:
                payload = source_replicated_state.observations_by_sensor.get(sensor_name)
                if payload is not None:
                    secondary = payload.process_data.sv
                    if secondary is not None and secondary.description == 'Totalizer_1_Mass':
                        if (source_replicated_state.owner_edge_id not in valid_state.source_edges
                                or float(payload.process_data.loop_current_ma) != current):
                            raise ValueError('HART totalizer projection requires an agreed source edge and unchanged acquired current.')
                    state = self._behavioral_state_from_payload(payload, source_round_id=round_id)
            behavioral_sensor_values[sensor_name] = replace(
                state, loop_current_ma=current, pv_percent_range=(current - 4.0) / 16.0 * 100.0,
            )
        return behavioral_sensor_values

    def _apply_behavioral_override(
        self,
        *,
        sensor_name: str,
        current_state: ScadaBehavioralSensorState,
        override: ScadaSensorOverride,
    ) -> ScadaBehavioralSensorState:
        if override.mode == "match":
            return current_state
        if override.mode == "offset":
            value = current_state.loop_current_ma + override.offset
            if not isfinite(value):
                raise ValueError("SCADA override produced a nonfinite current.")
            return replace(current_state, loop_current_ma=value, pv_percent_range=(value - 4.0) / 16.0 * 100.0, mode="offset")

        if override.mode == "freeze":
            if sensor_name not in self._frozen_states:
                value = current_state.loop_current_ma if override.fixed_value is None else override.fixed_value
                self._frozen_states[sensor_name] = replace(current_state, loop_current_ma=value, pv_percent_range=(value - 4.0) / 16.0 * 100.0, mode="freeze")
            return self._frozen_states[sensor_name]

        if override.mode == "replay":
            replay_state = self._resolve_historical_behavioral_state(
                sensor_name,
                replay_round_id=override.replay_round_id,
            )
            if replay_state is None:
                raise ValueError("SCADA replay requires a recorded source state.")
            return replace(replay_state, mode="replay")

        raise ValueError(f"Unexpected SCADA override mode: {override.mode}")

    def _resolve_historical_behavioral_state(
        self,
        sensor_name: str,
        *,
        replay_round_id: str | None,
    ) -> ScadaBehavioralSensorState | None:
        if not self._history:
            return None

        if replay_round_id is not None:
            for logical_state in self._history:
                if logical_state.source_round_id != replay_round_id:
                    continue
                behavioral_state = (logical_state.behavioral_sensor_values or {}).get(
                    sensor_name
                )
                if behavioral_state is not None:
                    return behavioral_state
            return None

        latest_behavioral = (self._history[-1].behavioral_sensor_values or {}).get(
            sensor_name
        )
        return latest_behavioral

    def _behavioral_state_from_payload(
        self,
        payload: RawHartPayload,
        *,
        source_round_id: str,
    ) -> ScadaBehavioralSensorState:
        metrics = payload.process_data.physics_metrics
        totalizer = None
        secondary = payload.process_data.sv
        if secondary is not None and secondary.description == 'Totalizer_1_Mass':
            from parallel_truth_fingerprint.consensus.current_domain import source_event_id
            source_event_id(payload)  # validate documented SV identity, unit and numeric value
            totalizer = float(secondary.value)
        return ScadaBehavioralSensorState(
            loop_current_ma=round(float(payload.process_data.loop_current_ma), 3),
            pv_percent_range=round(float(payload.process_data.pv_percent_range), 3),
            noise_floor=None if metrics is None else float(metrics.noise_floor),
            rate_of_change_dtdt=round(
                float(metrics.rate_of_change_dtdt),
                6,
            ) if metrics is not None else None,
            local_stability_score=round(
                float(metrics.local_stability_score),
                6,
            ) if metrics is not None else None,
            field_device_malfunction=bool(payload.diagnostics.field_device_malfunction),
            loop_current_saturated=bool(payload.diagnostics.loop_current_saturated),
            cold_start=bool(payload.diagnostics.cold_start),
            source_round_id=source_round_id,
            totalizer1_kg=totalizer,
        )

    def _behavioral_source_round_id(
        self,
        behavioral_sensor_values: dict[str, ScadaBehavioralSensorState],
    ) -> str | None:
        for sensor_name in sorted(behavioral_sensor_values):
            sensor_state = behavioral_sensor_values[sensor_name]
            if sensor_state.mode in {"replay", "freeze"} and sensor_state.source_round_id:
                return sensor_state.source_round_id
        for sensor_name in sorted(behavioral_sensor_values):
            source_round_id = behavioral_sensor_values[sensor_name].source_round_id
            if source_round_id:
                return source_round_id
        return None

    def _validate_sensor_name(self, sensor_name: str) -> None:
        if sensor_name not in self.sensor_names:
            raise ValueError(
                f"Unsupported SCADA sensor '{sensor_name}'. "
                f"Expected one of {list(self.sensor_names)}."
            )

    def _require_asyncua(self) -> None:
        if importlib.util.find_spec("asyncua") is None:
            raise RuntimeError(
                "Fake OPC UA SCADA service requires the 'asyncua' package. "
                "Install project dependencies before starting Story 3.1 runtime tests."
            )
