"""Runtime/demo configuration helpers."""

from __future__ import annotations

from dataclasses import dataclass
import os


@dataclass(frozen=True)
class RuntimeDemoConfig:
    mqtt_transport: str = "real"
    mqtt_broker_host: str = "localhost"
    mqtt_broker_port: int = 1883
    mqtt_topic: str = "edges/observations"
    demo_steps: int = 3
    demo_power: float = 65.0
    demo_fault_mode: str = "none"
    demo_faulty_edges: tuple[str, ...] = ()


def load_runtime_demo_config() -> RuntimeDemoConfig:
    """Load local runtime/demo settings from environment variables."""

    faulty_edges_raw = os.getenv("DEMO_FAULTY_EDGES", "")
    faulty_edges = tuple(
        edge_id.strip() for edge_id in faulty_edges_raw.split(",") if edge_id.strip()
    )

    return RuntimeDemoConfig(
        mqtt_transport=os.getenv("MQTT_TRANSPORT", "real"),
        mqtt_broker_host=os.getenv("MQTT_BROKER_HOST", "localhost"),
        mqtt_broker_port=int(os.getenv("MQTT_BROKER_PORT", "1883")),
        mqtt_topic=os.getenv("MQTT_TOPIC", "edges/observations"),
        demo_steps=int(os.getenv("DEMO_STEPS", "3")),
        demo_power=float(os.getenv("DEMO_POWER", "65.0")),
        demo_fault_mode=os.getenv("DEMO_FAULT_MODE", "none"),
        demo_faulty_edges=faulty_edges,
    )
