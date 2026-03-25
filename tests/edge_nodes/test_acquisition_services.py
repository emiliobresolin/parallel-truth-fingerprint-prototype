import unittest

from parallel_truth_fingerprint.edge_nodes.edge_1.service import TemperatureEdgeService
from parallel_truth_fingerprint.edge_nodes.edge_2.service import PressureEdgeService
from parallel_truth_fingerprint.edge_nodes.edge_3.service import RpmEdgeService
from parallel_truth_fingerprint.sensor_simulation.simulator import CompressorSimulator


class EdgeAcquisitionServicesTest(unittest.TestCase):
    def setUp(self) -> None:
        simulator = CompressorSimulator(seed=31)
        self.snapshot = simulator.step(compressor_power=60.0)

    def test_each_edge_acquires_only_its_assigned_sensor(self) -> None:
        edge_1_payload = TemperatureEdgeService().acquire(snapshot=self.snapshot)
        edge_2_payload = PressureEdgeService().acquire(snapshot=self.snapshot)
        edge_3_payload = RpmEdgeService().acquire(snapshot=self.snapshot)

        self.assertEqual(edge_1_payload.process_data.pv.unit, "degC")
        self.assertEqual(edge_2_payload.process_data.pv.unit, "bar")
        self.assertEqual(edge_3_payload.process_data.pv.unit, "rpm")

        self.assertEqual(
            edge_1_payload.process_data.pv.value,
            self.snapshot.sensors["temperature"],
        )
        self.assertEqual(
            edge_2_payload.process_data.pv.value,
            self.snapshot.sensors["pressure"],
        )
        self.assertEqual(
            edge_3_payload.process_data.pv.value,
            self.snapshot.sensors["rpm"],
        )

    def test_payload_follows_raw_hart_style_shape(self) -> None:
        payload = PressureEdgeService().acquire(snapshot=self.snapshot)

        serialized = payload.to_dict()

        self.assertEqual(serialized["protocol"], "HART")
        self.assertIn("gateway_id", serialized)
        self.assertIn("timestamp", serialized)
        self.assertIn("device_info", serialized)
        self.assertIn("process_data", serialized)
        self.assertIn("diagnostics", serialized)

        self.assertIn("pv", serialized["process_data"])
        self.assertIn("sv", serialized["process_data"])
        self.assertIn("loop_current_ma", serialized["process_data"])
        self.assertIn("pv_percent_range", serialized["process_data"])
        self.assertIn("physics_metrics", serialized["process_data"])

    def test_edge_services_keep_distinct_runtime_context(self) -> None:
        temperature_edge = TemperatureEdgeService()
        pressure_edge = PressureEdgeService()

        temperature_edge.acquire(snapshot=self.snapshot)
        temperature_edge.acquire(snapshot=self.snapshot)
        pressure_edge.acquire(snapshot=self.snapshot)

        temperature_state = temperature_edge.runtime_state()
        pressure_state = pressure_edge.runtime_state()

        self.assertEqual(temperature_state["acquisition_count"], 2)
        self.assertEqual(pressure_state["acquisition_count"], 1)
        self.assertNotEqual(
            temperature_state["last_payload_timestamp"],
            pressure_state["last_payload_timestamp"],
        )


if __name__ == "__main__":
    unittest.main()
