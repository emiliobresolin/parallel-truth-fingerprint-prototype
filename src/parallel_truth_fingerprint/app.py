"""Bootstrap entrypoint for the current local demo wiring."""

from parallel_truth_fingerprint.config.runtime import load_runtime_demo_config
from parallel_truth_fingerprint.edge_nodes.common.mqtt_io import create_transport

def main() -> None:
    """Validate the configured MQTT transport for local demo wiring."""

    config = load_runtime_demo_config()
    create_transport(
        config.mqtt_transport,
        host=config.mqtt_broker_host,
        port=config.mqtt_broker_port,
    )
    print(
        f"Runtime transport '{config.mqtt_transport}' is ready for the local demo path "
        f"against {config.mqtt_broker_host}:{config.mqtt_broker_port}."
    )


if __name__ == "__main__":
    main()
