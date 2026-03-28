"""Shared acquisition helpers for logically independent edge services.

The simulator represents the physical process.
Each edge behaves like a local sensor reader:
1. read the simulated physical measurement
2. interpret it at the acquisition boundary
3. construct the digital HART-style payload
"""

from __future__ import annotations

from dataclasses import dataclass, field
from datetime import datetime, timedelta, timezone

from parallel_truth_fingerprint.config.ranges import SensorRange, DEFAULT_COMPRESSOR_PROFILE
from parallel_truth_fingerprint.contracts.edge_local_replicated_state import (
    EdgeLocalReplicatedStateContract,
)
from parallel_truth_fingerprint.contracts.raw_hart_payload import (
    DeviceInfo,
    Diagnostics,
    PhysicsMetrics,
    ProcessData,
    ProcessVariable,
    RawHartPayload,
)
from parallel_truth_fingerprint.contracts.round_identity import RoundIdentity
from parallel_truth_fingerprint.edge_nodes.common.local_state import (
    EdgeLocalReplicatedState,
)
from parallel_truth_fingerprint.edge_nodes.common.mqtt_io import MqttTransport
from parallel_truth_fingerprint.sensor_simulation.simulator import (
    CompressorSimulator,
    SimulationSnapshot,
)
from parallel_truth_fingerprint.sensor_simulation.transmitter_observation import (
    TransmitterVariableObservation,
)


@dataclass(frozen=True)
class EdgeDeviceConfig:
    edge_id: str
    gateway_id: str
    sensor_name: str
    tag: str
    long_tag: str
    manufacturer_id: int
    device_type: int
    unit: str
    unit_code: int | None
    sensor_range: SensorRange


@dataclass
class EdgeRuntimeContext:
    acquisition_count: int = 0
    previous_pv: float | None = None
    last_payload_timestamp: str | None = None
    published_observation_count: int = 0
    peer_observation_count: int = 0
    observation_flow_log: list[dict[str, object]] = field(default_factory=list)


EDGE_DEVICE_CONFIGS: dict[str, EdgeDeviceConfig] = {
    "edge-1": EdgeDeviceConfig(
        edge_id="edge-1",
        gateway_id="GW-EDGE-01",
        sensor_name="temperature",
        tag="TIT-101",
        long_tag="Temperature_Compressor_Casing",
        manufacturer_id=26,
        device_type=33,
        unit="degC",
        unit_code=32,
        sensor_range=DEFAULT_COMPRESSOR_PROFILE.temperature,
    ),
    "edge-2": EdgeDeviceConfig(
        edge_id="edge-2",
        gateway_id="GW-EDGE-02",
        sensor_name="pressure",
        tag="PIT-101",
        long_tag="Pressure_Compressor_Discharge",
        manufacturer_id=38,
        device_type=44,
        unit="bar",
        unit_code=7,
        sensor_range=DEFAULT_COMPRESSOR_PROFILE.pressure,
    ),
    "edge-3": EdgeDeviceConfig(
        edge_id="edge-3",
        gateway_id="GW-EDGE-03",
        sensor_name="rpm",
        tag="RIT-101",
        long_tag="Speed_Compressor_Shaft",
        manufacturer_id=55,
        device_type=52,
        unit="rpm",
        unit_code=None,
        sensor_range=DEFAULT_COMPRESSOR_PROFILE.rpm,
    ),
}


def _stability_score(rate_of_change: float, noise_floor: float) -> float:
    score = 1.0 - min(0.95, abs(rate_of_change) * 0.015 + noise_floor * 0.1)
    return round(max(0.0, score), 3)


class EdgeAcquisitionService:
    """Acquire a single local sensor and emit a raw HART-style payload.

    This service models physical acquisition semantics only. It does not
    validate, replicate, or publish data.
    """

    def __init__(
        self,
        device_config: EdgeDeviceConfig,
        *,
        simulator: CompressorSimulator | None = None,
    ) -> None:
        self.device_config = device_config
        self._simulator = simulator or CompressorSimulator()
        self._runtime = EdgeRuntimeContext()
        self._transport: MqttTransport | None = None
        self._replicated_state = EdgeLocalReplicatedState(owner_edge_id=device_config.edge_id)

    def acquire(
        self,
        *,
        snapshot: SimulationSnapshot | None = None,
        operating_state_pct: float | None = None,
        compressor_power: float | None = None,
    ) -> RawHartPayload:
        """Read, interpret, and encode one local physical measurement.

        The input snapshot is treated as the physical process observation.
        The edge then transforms that observation into a digital raw payload.
        """

        reading = snapshot or self._simulator.step(
            operating_state_pct=operating_state_pct,
            compressor_power=compressor_power,
        )
        transmitter_observation = reading.transmitter_observations[self.device_config.sensor_name]
        self._runtime.observation_flow_log.append(
            {
                "stage": "process_state_generation",
                "edge_id": self.device_config.edge_id,
                "sensor_name": self.device_config.sensor_name,
                "operating_state_pct": reading.operating_state_pct,
                "hidden_process_state": reading.metadata.get("hidden_process_state"),
            }
        )
        self._runtime.observation_flow_log.append(
            {
                "stage": "sensor_generation",
                "edge_id": self.device_config.edge_id,
                "sensor_name": self.device_config.sensor_name,
                "operating_state_pct": reading.operating_state_pct,
                "value": transmitter_observation.pv.value,
            }
        )
        self._runtime.observation_flow_log.append(
            {
                "stage": "transmitter_observation",
                "edge_id": self.device_config.edge_id,
                "sensor_name": self.device_config.sensor_name,
                "observation": transmitter_observation.to_dict(),
            }
        )

        pv_value = round(transmitter_observation.pv.value, 3)
        percent_range = transmitter_observation.pv_percent_range
        loop_current = transmitter_observation.loop_current_ma
        rate_of_change = 0.0
        if self._runtime.previous_pv is not None:
            rate_of_change = round(pv_value - self._runtime.previous_pv, 3)

        noise_floor = round(float(reading.metadata.get("noise_level", 0.0)), 3)
        physics_metrics = PhysicsMetrics(
            noise_floor=noise_floor,
            rate_of_change_dtdt=rate_of_change,
            local_stability_score=_stability_score(rate_of_change, noise_floor),
        )

        # The payload is the digital representation of the interpreted
        # physical measurement at the edge acquisition boundary.
        payload = RawHartPayload(
            protocol="HART",
            gateway_id=self.device_config.gateway_id,
            timestamp=datetime.now(timezone.utc).isoformat(timespec="microseconds"),
            device_info=DeviceInfo(
                tag=self.device_config.tag,
                long_tag=self.device_config.long_tag,
                manufacturer_id=self.device_config.manufacturer_id,
                device_type=self.device_config.device_type,
            ),
            process_data=ProcessData(
                pv=ProcessVariable(
                    value=pv_value,
                    unit=transmitter_observation.pv.unit,
                    unit_code=transmitter_observation.pv.unit_code,
                    description=transmitter_observation.pv.description,
                ),
                sv=self._payload_secondary_variable(transmitter_observation.sv),
                loop_current_ma=loop_current,
                pv_percent_range=percent_range,
                physics_metrics=physics_metrics,
            ),
            diagnostics=Diagnostics(
                device_status_hex=transmitter_observation.diagnostics.device_status_hex,
                field_device_malfunction=transmitter_observation.diagnostics.field_device_malfunction,
                loop_current_saturated=transmitter_observation.diagnostics.loop_current_saturated,
                cold_start=self._runtime.acquisition_count == 0,
            ),
        )

        self._runtime.acquisition_count += 1
        self._runtime.previous_pv = pv_value
        self._runtime.last_payload_timestamp = payload.timestamp
        self._runtime.observation_flow_log.append(
            {
                "stage": "local_edge_acquisition",
                "edge_id": self.device_config.edge_id,
                "sensor_name": self.device_config.sensor_name,
                "payload_timestamp": payload.timestamp,
                "pv_value": pv_value,
                "sv_present": payload.process_data.sv is not None,
            }
        )
        return payload

    def _payload_secondary_variable(
        self,
        secondary_variable: TransmitterVariableObservation | None,
    ) -> ProcessVariable | None:
        if secondary_variable is None:
            return None
        return ProcessVariable(
            value=secondary_variable.value,
            unit=secondary_variable.unit,
            unit_code=secondary_variable.unit_code,
            description=secondary_variable.description,
        )

    def attach_transport(
        self,
        transport: MqttTransport,
        *,
        topic: str = "edges/observations",
    ) -> None:
        """Attach the selected transport and subscribe for peer observations."""

        self._transport = transport
        transport.subscribe(
            topic=topic,
            subscriber_id=self.device_config.edge_id,
            callback=self.consume_peer_observation,
        )

    def attach_relay(
        self,
        relay: MqttTransport,
        *,
        topic: str = "edges/observations",
    ) -> None:
        """Backward-compatible alias for tests and earlier story code."""

        self.attach_transport(relay, topic=topic)

    def publish_local_observation(
        self,
        payload: RawHartPayload,
        *,
        topic: str = "edges/observations",
    ) -> None:
        """Publish the local observation and update this edge's own replicated state."""

        self._replicated_state.update_from_payload(payload)
        self._runtime.published_observation_count += 1
        self._runtime.observation_flow_log.append(
            {
                "stage": "edge_local_replicated_state",
                "edge_id": self.device_config.edge_id,
                "state": self._replicated_state.to_dict(),
            }
        )
        if self._transport is None:
            raise RuntimeError("MQTT transport must be attached before publishing observations.")
        self._transport.publish(
            topic=topic,
            publisher_id=self.device_config.edge_id,
            payload=payload,
        )
        self._runtime.observation_flow_log.append(
            {
                "stage": "mqtt_publication",
                "edge_id": self.device_config.edge_id,
                "topic": topic,
                "payload_timestamp": payload.timestamp,
            }
        )

    def consume_peer_observation(self, publisher_id: str, payload: RawHartPayload) -> None:
        """Consume a peer observation relayed by the passive MQTT broker."""

        self._replicated_state.update_from_payload(payload)
        self._runtime.peer_observation_count += 1
        self._runtime.observation_flow_log.append(
            {
                "stage": "mqtt_consumption",
                "edge_id": self.device_config.edge_id,
                "publisher_id": publisher_id,
                "source_tag": payload.device_info.tag,
                "payload_timestamp": payload.timestamp,
            }
        )
        self._runtime.observation_flow_log.append(
            {
                "stage": "edge_local_replicated_state",
                "edge_id": self.device_config.edge_id,
                "state": self._replicated_state.to_dict(),
            }
        )

    def local_replicated_state(self) -> dict[str, object]:
        """Return this edge's own intermediate replicated shared view."""

        return self._replicated_state.to_dict()

    def replicated_state_contract(
        self,
        *,
        round_identity: RoundIdentity,
        participating_edges: tuple[str, ...],
    ) -> EdgeLocalReplicatedStateContract:
        """Export the current edge-local replicated state as a typed contract."""

        return EdgeLocalReplicatedStateContract(
            round_identity=round_identity,
            owner_edge_id=self.device_config.edge_id,
            participating_edges=participating_edges,
            observations_by_sensor=dict(self._replicated_state.observations),
            is_validated=False,
        )

    def consensus_round_identity(self) -> RoundIdentity:
        """Build a small round identity anchored to the last local acquisition timestamp."""

        if self._runtime.last_payload_timestamp is None:
            raise RuntimeError("At least one acquisition is required before building a round.")

        window_ended_at = datetime.fromisoformat(
            self._runtime.last_payload_timestamp.replace("Z", "+00:00")
        )
        window_started_at = window_ended_at - timedelta(minutes=1)
        return RoundIdentity(
            round_id=f"round-{window_ended_at.strftime('%Y%m%d%H%M%S%f')}",
            window_started_at=window_started_at,
            window_ended_at=window_ended_at,
        )

    def observation_flow_log(self) -> list[dict[str, object]]:
        """Return the upstream observation-flow events for this edge."""

        return list(self._runtime.observation_flow_log)

    def runtime_state(self) -> dict[str, object]:
        """Return a small inspectable snapshot of this edge's local runtime context."""

        return {
            "edge_id": self.device_config.edge_id,
            "sensor_name": self.device_config.sensor_name,
            "acquisition_count": self._runtime.acquisition_count,
            "last_payload_timestamp": self._runtime.last_payload_timestamp,
            "published_observation_count": self._runtime.published_observation_count,
            "peer_observation_count": self._runtime.peer_observation_count,
        }
