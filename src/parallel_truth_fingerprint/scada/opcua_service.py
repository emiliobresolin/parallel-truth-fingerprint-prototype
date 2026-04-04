"""Fake OPC UA logical SCADA service for the local prototype."""

from __future__ import annotations

from dataclasses import dataclass, replace
import importlib.util

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
}
SUPPORTED_OVERRIDE_MODES = {"match", "offset", "freeze", "replay"}


@dataclass(frozen=True)
class ScadaSensorOverride:
    """Additive logical-side divergence controls for one sensor."""

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
    ) -> None:
        self.endpoint_url = endpoint_url
        self.namespace_uri = namespace_uri
        self.compressor_id = compressor_id
        self._server = None
        self._namespace_index: int | None = None
        self._sensor_nodes: dict[str, object] = {}
        self._current_state: ScadaState | None = None
        self._history: list[ScadaState] = []
        self._frozen_values: dict[str, float] = {}
        self._overrides = {
            sensor_name: ScadaSensorOverride() for sensor_name in SUPPORTED_SCADA_SENSORS
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
        """Configure one additive logical-side divergence mode for a sensor."""

        self._validate_sensor_name(sensor_name)
        if mode not in SUPPORTED_OVERRIDE_MODES:
            raise ValueError(
                f"Unsupported SCADA override mode '{mode}'. "
                f"Expected one of {sorted(SUPPORTED_OVERRIDE_MODES)}."
            )

        override = ScadaSensorOverride(
            mode=mode,
            offset=offset,
            fixed_value=None if fixed_value is None else round(float(fixed_value), 3),
            replay_round_id=replay_round_id,
        )
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

    def clear_overrides(self) -> None:
        """Reset all sensors to normal matching behavior."""

        for sensor_name in SUPPORTED_SCADA_SENSORS:
            self._overrides[sensor_name] = ScadaSensorOverride()
        self._frozen_values.clear()

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

        missing = set(SUPPORTED_SCADA_SENSORS).difference(valid_state.sensor_values)
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
        for sensor_name in SUPPORTED_SCADA_SENSORS:
            base_value = round(float(valid_state.sensor_values[sensor_name]), 3)
            override = self._overrides[sensor_name]
            projected_value = self._apply_supervisory_override(
                sensor_name,
                base_value=base_value,
                override=override,
            )
            sensor_values[sensor_name] = ScadaSensorState(
                value=projected_value,
                unit=SCADA_SENSOR_UNITS[sensor_name],
                mode=override.mode,
            )
            if sensor_name in behavioral_sensor_values:
                behavioral_sensor_values[sensor_name] = self._apply_behavioral_override(
                    sensor_name=sensor_name,
                    current_state=behavioral_sensor_values[sensor_name],
                    override=override,
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
        for sensor_name in SUPPORTED_SCADA_SENSORS:
            node = await compressor_node.add_variable(namespace_index, sensor_name, 0.0)
            await node.set_writable()
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
            for sensor_name in SUPPORTED_SCADA_SENSORS
        }

    async def _write_state_to_server(self, logical_state: ScadaState) -> None:
        for sensor_name, sensor_state in logical_state.sensor_values.items():
            await self._sensor_nodes[sensor_name].write_value(sensor_state.value)

    def _apply_supervisory_override(
        self,
        sensor_name: str,
        *,
        base_value: float,
        override: ScadaSensorOverride,
    ) -> float:
        if override.mode == "match":
            return base_value
        if override.mode == "offset":
            return round(base_value + override.offset, 3)
        if override.mode == "freeze":
            if sensor_name in self._frozen_values:
                return self._frozen_values[sensor_name]
            frozen_value = base_value if override.fixed_value is None else override.fixed_value
            self._frozen_values[sensor_name] = round(float(frozen_value), 3)
            return self._frozen_values[sensor_name]
        if override.mode == "replay":
            return base_value
        raise ValueError(f"Unexpected SCADA override mode: {override.mode}")

    def _build_behavioral_sensor_values(
        self,
        *,
        valid_state: ConsensusedValidState,
        source_replicated_state: EdgeLocalReplicatedStateContract | None,
    ) -> dict[str, ScadaBehavioralSensorState]:
        if source_replicated_state is None:
            return {}

        missing = set(SUPPORTED_SCADA_SENSORS).difference(
            source_replicated_state.observations_by_sensor
        )
        if missing:
            raise ValueError(
                "SCADA projection is missing source replicated payloads for: "
                f"{sorted(missing)}"
            )

        round_id = valid_state.round_identity.round_id
        behavioral_sensor_values: dict[str, ScadaBehavioralSensorState] = {}
        for sensor_name in SUPPORTED_SCADA_SENSORS:
            payload = source_replicated_state.observations_by_sensor[sensor_name]
            behavioral_sensor_values[sensor_name] = self._behavioral_state_from_payload(
                payload,
                source_round_id=round_id,
            )
        return behavioral_sensor_values

    def _apply_behavioral_override(
        self,
        *,
        sensor_name: str,
        current_state: ScadaBehavioralSensorState,
        override: ScadaSensorOverride,
    ) -> ScadaBehavioralSensorState:
        if override.mode in {"match", "offset"}:
            return replace(current_state, mode=override.mode)

        if override.mode == "freeze":
            frozen_state = self._resolve_historical_behavioral_state(
                sensor_name,
                replay_round_id=override.replay_round_id,
            )
            return replace(frozen_state or current_state, mode="freeze")

        if override.mode == "replay":
            replay_state = self._resolve_historical_behavioral_state(
                sensor_name,
                replay_round_id=override.replay_round_id,
            )
            return replace(replay_state or current_state, mode="replay")

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
        return ScadaBehavioralSensorState(
            loop_current_ma=round(float(payload.process_data.loop_current_ma), 3),
            pv_percent_range=round(float(payload.process_data.pv_percent_range), 3),
            noise_floor=round(float(payload.process_data.physics_metrics.noise_floor), 6),
            rate_of_change_dtdt=round(
                float(payload.process_data.physics_metrics.rate_of_change_dtdt),
                6,
            ),
            local_stability_score=round(
                float(payload.process_data.physics_metrics.local_stability_score),
                6,
            ),
            field_device_malfunction=bool(payload.diagnostics.field_device_malfunction),
            loop_current_saturated=bool(payload.diagnostics.loop_current_saturated),
            cold_start=bool(payload.diagnostics.cold_start),
            source_round_id=source_round_id,
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
        if sensor_name not in SUPPORTED_SCADA_SENSORS:
            raise ValueError(
                f"Unsupported SCADA sensor '{sensor_name}'. "
                f"Expected one of {list(SUPPORTED_SCADA_SENSORS)}."
            )

    def _require_asyncua(self) -> None:
        if importlib.util.find_spec("asyncua") is None:
            raise RuntimeError(
                "Fake OPC UA SCADA service requires the 'asyncua' package. "
                "Install project dependencies before starting Story 3.1 runtime tests."
            )
