import unittest

from parallel_truth_fingerprint.edge_nodes.edge_1.service import TemperatureEdgeService
from parallel_truth_fingerprint.edge_nodes.edge_2.service import PressureEdgeService
from parallel_truth_fingerprint.edge_nodes.edge_3.service import RpmEdgeService
from parallel_truth_fingerprint.sensor_simulation.simulator import CompressorSimulator
from tests.reference_contracts import HART_TRANSMITTER_REFERENCE


class HartReferenceContractsTest(unittest.TestCase):
    def test_acquisition_payloads_follow_reference_semantics(self) -> None:
        snapshot = CompressorSimulator(seed=61).step(operating_state_pct=66.0)
        payloads = {
            "temperature": TemperatureEdgeService().acquire(snapshot=snapshot),
            "pressure": PressureEdgeService().acquire(snapshot=snapshot),
            "rpm": RpmEdgeService().acquire(snapshot=snapshot),
        }

        for sensor_name, payload in payloads.items():
            reference = HART_TRANSMITTER_REFERENCE[sensor_name]
            self.assertEqual(payload.process_data.pv.description, reference["pv_description"])

            if reference["expected_sv_description"] is None:
                self.assertIsNone(payload.process_data.sv)
            else:
                self.assertIsNotNone(payload.process_data.sv)
                self.assertEqual(
                    payload.process_data.sv.description,
                    reference["expected_sv_description"],
                )


if __name__ == "__main__":
    unittest.main()
