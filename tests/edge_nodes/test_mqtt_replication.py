import unittest

from parallel_truth_fingerprint.edge_nodes.common.mqtt_io import (
    PassiveMqttRelay,
    RealMqttTransport,
    create_transport,
)
from parallel_truth_fingerprint.edge_nodes.edge_1.service import TemperatureEdgeService
from parallel_truth_fingerprint.edge_nodes.edge_2.service import PressureEdgeService
from parallel_truth_fingerprint.edge_nodes.edge_3.service import RpmEdgeService
from parallel_truth_fingerprint.sensor_simulation.simulator import CompressorSimulator


class EdgeMqttReplicationTest(unittest.TestCase):
    def setUp(self) -> None:
        simulator = CompressorSimulator(seed=41)
        self.snapshot = simulator.step(operating_state_pct=70.0)
        self.relay = PassiveMqttRelay()
        self.edge_1 = TemperatureEdgeService()
        self.edge_2 = PressureEdgeService()
        self.edge_3 = RpmEdgeService()

        self.edge_1.attach_relay(self.relay)
        self.edge_2.attach_relay(self.relay)
        self.edge_3.attach_relay(self.relay)

    def test_edge_publishes_its_own_local_payload(self) -> None:
        payload = self.edge_1.acquire(snapshot=self.snapshot)

        self.edge_1.publish_local_observation(payload)

        self.assertEqual(len(self.relay.published_messages()), 1)
        published = self.relay.published_messages()[0]
        self.assertEqual(published["publisher_id"], "edge-1")
        self.assertEqual(
            published["payload"].process_data.pv.value,
            self.snapshot.sensors["temperature"],
        )

    def test_peer_observations_are_consumed_through_passive_relay(self) -> None:
        self.edge_1.publish_local_observation(self.edge_1.acquire(snapshot=self.snapshot))
        self.edge_2.publish_local_observation(self.edge_2.acquire(snapshot=self.snapshot))

        edge_3_state = self.edge_3.runtime_state()

        self.assertEqual(edge_3_state["peer_observation_count"], 2)
        self.assertEqual(edge_3_state["published_observation_count"], 0)

    def test_each_edge_builds_its_own_non_validated_local_replicated_state(self) -> None:
        self.edge_1.publish_local_observation(self.edge_1.acquire(snapshot=self.snapshot))
        self.edge_2.publish_local_observation(self.edge_2.acquire(snapshot=self.snapshot))
        self.edge_3.publish_local_observation(self.edge_3.acquire(snapshot=self.snapshot))

        for edge_service in (self.edge_1, self.edge_2, self.edge_3):
            replicated = edge_service.local_replicated_state()
            self.assertTrue(replicated["is_complete"])
            self.assertFalse(replicated["is_validated"])
            self.assertEqual(replicated["state_type"], "edge_local_replicated_state")
            self.assertIn("temperature", replicated["sensor_values"])
            self.assertIn("pressure", replicated["sensor_values"])
            self.assertIn("rpm", replicated["sensor_values"])

    def test_observation_flow_log_captures_upstream_stages(self) -> None:
        payload = self.edge_1.acquire(snapshot=self.snapshot)
        self.edge_1.publish_local_observation(payload)

        stages = [entry["stage"] for entry in self.edge_1.observation_flow_log()]

        self.assertIn("process_state_generation", stages)
        self.assertIn("sensor_generation", stages)
        self.assertIn("transmitter_observation", stages)
        self.assertIn("local_edge_acquisition", stages)
        self.assertIn("mqtt_publication", stages)
        self.assertIn("edge_local_replicated_state", stages)


class FakeMqttClient:
    def __init__(self) -> None:
        self.connected_to = None
        self.published = []
        self.subscriptions = []
        self.callbacks = {}
        self.loop_started = False

    def connect(self, host: str, port: int, keepalive: int) -> None:
        self.connected_to = (host, port, keepalive)

    def loop_start(self) -> None:
        self.loop_started = True

    def publish(self, topic: str, payload: str) -> None:
        self.published.append((topic, payload))
        for pattern, callbacks in self.callbacks.items():
            if pattern.endswith("/#"):
                prefix = pattern[:-2]
                if not topic.startswith(prefix):
                    continue
            elif pattern != topic:
                continue
            for callback in callbacks:
                callback(topic, payload)

    def subscribe(self, topic: str) -> None:
        self.subscriptions.append(topic)

    def message_callback_add(self, topic: str, callback) -> None:
        self.callbacks.setdefault(topic, []).append(callback)


class TransportSelectionTest(unittest.TestCase):
    def test_create_transport_returns_passive_relay_for_tests(self) -> None:
        transport = create_transport("passive")

        self.assertIsInstance(transport, PassiveMqttRelay)

    def test_real_transport_is_available_behind_same_boundary(self) -> None:
        transport = RealMqttTransport(
            host="localhost",
            port=1883,
            client_factory=FakeMqttClient,
        )

        received_payloads = []
        transport.subscribe(
            topic="edges/observations",
            subscriber_id="edge-2",
            callback=lambda publisher_id, payload: received_payloads.append((publisher_id, payload)),
        )
        sample_payload = PressureEdgeService().acquire(
            snapshot=CompressorSimulator(seed=52).step(operating_state_pct=58.0)
        )

        transport.publish(
            topic="edges/observations",
            publisher_id="edge-1",
            payload=sample_payload,
        )

        self.assertEqual(len(received_payloads), 1)
        self.assertEqual(received_payloads[0][0], "edge-1")
        self.assertEqual(received_payloads[0][1].process_data.pv.unit, "bar")
        self.assertEqual(transport._client.connected_to, ("localhost", 1883, 60))
        self.assertTrue(transport._client.loop_started)

    def test_serialization_roundtrip_supports_missing_secondary_variable(self) -> None:
        transport = RealMqttTransport(
            host="localhost",
            port=1883,
            client_factory=FakeMqttClient,
        )
        received_payloads = []
        transport.subscribe(
            topic="edges/observations",
            subscriber_id="edge-1",
            callback=lambda publisher_id, payload: received_payloads.append((publisher_id, payload)),
        )
        sample_payload = RpmEdgeService().acquire(
            snapshot=CompressorSimulator(seed=53).step(operating_state_pct=61.0)
        )

        transport.publish(
            topic="edges/observations",
            publisher_id="edge-3",
            payload=sample_payload,
        )

        self.assertEqual(len(received_payloads), 1)
        self.assertIsNone(received_payloads[0][1].process_data.sv)


if __name__ == "__main__":
    unittest.main()
