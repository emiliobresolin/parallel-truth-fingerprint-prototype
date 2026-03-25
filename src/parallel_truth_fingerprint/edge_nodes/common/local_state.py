"""Edge-owned intermediate replicated state helpers."""

from __future__ import annotations

from dataclasses import dataclass, field

from parallel_truth_fingerprint.contracts.raw_hart_payload import RawHartPayload


SENSOR_BY_TAG_PREFIX = {
    "T": "temperature",
    "P": "pressure",
    "R": "rpm",
}


def infer_sensor_name(payload: RawHartPayload) -> str:
    """Infer the logical sensor name from the device tag prefix."""

    tag_prefix = payload.device_info.tag[:1].upper()
    return SENSOR_BY_TAG_PREFIX[tag_prefix]


@dataclass
class EdgeLocalReplicatedState:
    """Intermediate, non-validated shared view reconstructed by one edge."""

    owner_edge_id: str
    observations: dict[str, RawHartPayload] = field(default_factory=dict)

    def update_from_payload(self, payload: RawHartPayload) -> None:
        sensor_name = infer_sensor_name(payload)
        self.observations[sensor_name] = payload

    def to_dict(self) -> dict[str, object]:
        sensor_values = {
            sensor_name: payload.process_data.pv.value
            for sensor_name, payload in self.observations.items()
        }
        return {
            "state_type": "edge_local_replicated_state",
            "owner_edge_id": self.owner_edge_id,
            "is_validated": False,
            "is_complete": all(
                sensor in sensor_values for sensor in ("temperature", "pressure", "rpm")
            ),
            "sensor_values": sensor_values,
        }
