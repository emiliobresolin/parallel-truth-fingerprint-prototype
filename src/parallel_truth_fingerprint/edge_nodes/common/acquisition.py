"""Shared acquisition helpers for logically independent edge services.

The simulator represents the physical process.
Each edge behaves like a local sensor reader:
1. read the simulated physical measurement
2. interpret it at the acquisition boundary
3. construct the digital HART-style payload
"""

from __future__ import annotations

from dataclasses import dataclass
from datetime import datetime, timezone

from parallel_truth_fingerprint.config.ranges import SensorRange, DEFAULT_COMPRESSOR_PROFILE
from parallel_truth_fingerprint.contracts.raw_hart_payload import (
    DeviceInfo,
    Diagnostics,
    PhysicsMetrics,
    ProcessData,
    ProcessVariable,
    RawHartPayload,
)
from parallel_truth_fingerprint.edge_nodes.common.local_state import (
    EdgeLocalReplicatedState,
)
from parallel_truth_fingerprint.edge_nodes.common.mqtt_io import PassiveMqttRelay
from parallel_truth_fingerprint.sensor_simulation.simulator import (
    CompressorSimulator,
    SimulationSnapshot,
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
    secondary_description: str
    sensor_range: SensorRange


@dataclass
class EdgeRuntimeContext:
    acquisition_count: int = 0
    previous_pv: float | None = None
    last_payload_timestamp: str | None = None
    published_observation_count: int = 0
    peer_observation_count: int = 0


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
        secondary_description="Compressor_Power",
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
        secondary_description="Compressor_Power",
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
        secondary_description="Compressor_Power",
        sensor_range=DEFAULT_COMPRESSOR_PROFILE.rpm,
    ),
}


def _percent_range(value: float, sensor_range: SensorRange) -> float:
    span = sensor_range.maximum - sensor_range.minimum
    if span <= 0:
        return 0.0
    return round(((value - sensor_range.minimum) / span) * 100.0, 3)


def _loop_current_from_percent(percent_range: float) -> float:
    return round(4.0 + (16.0 * (percent_range / 100.0)), 3)


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
        self._relay: PassiveMqttRelay | None = None
        self._replicated_state = EdgeLocalReplicatedState(owner_edge_id=device_config.edge_id)

    def acquire(
        self,
        *,
        snapshot: SimulationSnapshot | None = None,
        compressor_power: float | None = None,
    ) -> RawHartPayload:
        """Read, interpret, and encode one local physical measurement.

        The input snapshot is treated as the physical process observation.
        The edge then transforms that observation into a digital raw payload.
        """

        reading = snapshot or self._simulator.step(compressor_power=compressor_power)
        pv_value = round(reading.sensors[self.device_config.sensor_name], 3)
        percent_range = _percent_range(pv_value, self.device_config.sensor_range)
        loop_current = _loop_current_from_percent(percent_range)
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
                    unit=self.device_config.unit,
                    unit_code=self.device_config.unit_code,
                ),
                sv=ProcessVariable(
                    value=round(reading.compressor_power, 3),
                    unit="percent",
                    description=self.device_config.secondary_description,
                ),
                loop_current_ma=loop_current,
                pv_percent_range=percent_range,
                physics_metrics=physics_metrics,
            ),
            diagnostics=Diagnostics(
                device_status_hex="0x00",
                field_device_malfunction=False,
                loop_current_saturated=loop_current <= 4.0 or loop_current >= 20.0,
                cold_start=self._runtime.acquisition_count == 0,
            ),
        )

        self._runtime.acquisition_count += 1
        self._runtime.previous_pv = pv_value
        self._runtime.last_payload_timestamp = payload.timestamp
        return payload

    def attach_relay(
        self,
        relay: PassiveMqttRelay,
        *,
        topic: str = "edges/observations",
    ) -> None:
        """Attach the passive relay and subscribe for peer observations."""

        self._relay = relay
        relay.subscribe(
            topic=topic,
            subscriber_id=self.device_config.edge_id,
            callback=self.consume_peer_observation,
        )

    def publish_local_observation(
        self,
        payload: RawHartPayload,
        *,
        topic: str = "edges/observations",
    ) -> None:
        """Publish the local observation and update this edge's own replicated state."""

        self._replicated_state.update_from_payload(payload)
        self._runtime.published_observation_count += 1
        if self._relay is None:
            raise RuntimeError("Passive relay must be attached before publishing observations.")
        self._relay.publish(
            topic=topic,
            publisher_id=self.device_config.edge_id,
            payload=payload,
        )

    def consume_peer_observation(self, payload: RawHartPayload) -> None:
        """Consume a peer observation relayed by the passive MQTT broker."""

        self._replicated_state.update_from_payload(payload)
        self._runtime.peer_observation_count += 1

    def local_replicated_state(self) -> dict[str, object]:
        """Return this edge's own intermediate replicated shared view."""

        return self._replicated_state.to_dict()

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
