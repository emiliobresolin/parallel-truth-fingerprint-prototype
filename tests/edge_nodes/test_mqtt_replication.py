import unittest

from parallel_truth_fingerprint.edge_nodes.common.mqtt_io import PassiveMqttRelay
from parallel_truth_fingerprint.edge_nodes.edge_1.service import TemperatureEdgeService
from parallel_truth_fingerprint.edge_nodes.edge_2.service import PressureEdgeService
from parallel_truth_fingerprint.edge_nodes.edge_3.service import RpmEdgeService
from parallel_truth_fingerprint.sensor_simulation.simulator import CompressorSimulator


class EdgeMqttReplicationTest(unittest.TestCase):
    def setUp(self) -> None:
        simulator = CompressorSimulator(seed=41)
        self.snapshot = simulator.step(compressor_power=70.0)
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


if __name__ == "__main__":
    unittest.main()
