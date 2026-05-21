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
    cometbft_rpc_url: str = "http://127.0.0.1:26657"
    minio_endpoint: str = "localhost:9000"
    minio_access_key: str = "minioadmin"
    minio_secret_key: str = "minioadmin"
    minio_bucket: str = "valid-consensus-artifacts"
    minio_secure: bool = False
    demo_steps: int = 3
    demo_cycle_interval_seconds: float = 10.0
    demo_max_cycles: int = 0
    demo_train_after_eligible_cycles: int = 10
    demo_fingerprint_sequence_length: int = 2
    demo_power: float = 65.0
    demo_dashboard_host: str = "127.0.0.1"
    demo_dashboard_port: int = 8088
    demo_scenario_name: str = ""
    demo_scenario_start_cycle: int = 1
    demo_fault_mode: str = "none"
    demo_faulty_edges: tuple[str, ...] = ()
    demo_scada_mode: str = "match"
    demo_scada_start_cycle: int = 0
    demo_scada_offset_value: float = 6.0
    demo_log_path: str = "logs/run_local_demo.log"
    # Epic 8 (Story 8.3) opt-out switch: when True, the runtime loop skips
    # the deprecated in-runtime autoencoder lifecycle and surfaces an
    # explicit "offline" status to the dashboard.
    demo_disable_runtime_autoencoder: bool = False


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
        cometbft_rpc_url=os.getenv("COMETBFT_RPC_URL", "http://127.0.0.1:26657"),
        minio_endpoint=os.getenv("MINIO_ENDPOINT", "localhost:9000"),
        minio_access_key=os.getenv("MINIO_ACCESS_KEY", "minioadmin"),
        minio_secret_key=os.getenv("MINIO_SECRET_KEY", "minioadmin"),
        minio_bucket=os.getenv("MINIO_BUCKET", "valid-consensus-artifacts"),
        minio_secure=os.getenv("MINIO_SECURE", "false").strip().lower()
        in {"1", "true", "yes", "on"},
        demo_steps=int(os.getenv("DEMO_STEPS", "3")),
        demo_cycle_interval_seconds=float(os.getenv("DEMO_CYCLE_INTERVAL_SECONDS", "10")),
        demo_max_cycles=int(os.getenv("DEMO_MAX_CYCLES", "0")),
        demo_train_after_eligible_cycles=int(
            os.getenv("DEMO_TRAIN_AFTER_ELIGIBLE_CYCLES", "10")
        ),
        demo_fingerprint_sequence_length=int(
            os.getenv("DEMO_FINGERPRINT_SEQUENCE_LENGTH", "2")
        ),
        demo_power=float(os.getenv("DEMO_POWER", "65.0")),
        demo_dashboard_host=os.getenv("DEMO_DASHBOARD_HOST", "127.0.0.1"),
        demo_dashboard_port=int(os.getenv("DEMO_DASHBOARD_PORT", "8088")),
        demo_scenario_name=os.getenv("DEMO_SCENARIO", "").strip(),
        demo_scenario_start_cycle=int(os.getenv("DEMO_SCENARIO_START_CYCLE", "1")),
        demo_fault_mode=os.getenv("DEMO_FAULT_MODE", "none"),
        demo_faulty_edges=faulty_edges,
        demo_scada_mode=os.getenv("DEMO_SCADA_MODE", "match"),
        demo_scada_start_cycle=int(os.getenv("DEMO_SCADA_START_CYCLE", "0")),
        demo_scada_offset_value=float(os.getenv("DEMO_SCADA_OFFSET_VALUE", "6.0")),
        demo_log_path=os.getenv("DEMO_LOG_PATH", "logs/run_local_demo.log"),
        demo_disable_runtime_autoencoder=os.getenv(
            "DEMO_DISABLE_RUNTIME_AUTOENCODER", "false"
        ).strip().lower()
        in {"1", "true", "yes", "on"},
    )
