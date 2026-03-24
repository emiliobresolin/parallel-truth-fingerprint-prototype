import statistics
import unittest

from parallel_truth_fingerprint.sensor_simulation.simulator import CompressorSimulator


class CompressorSimulatorTest(unittest.TestCase):
    def test_step_produces_all_expected_outputs(self) -> None:
        simulator = CompressorSimulator(seed=7)

        reading = simulator.step()

        self.assertEqual(reading.compressor_id, "compressor-1")
        self.assertIn("temperature", reading.sensors)
        self.assertIn("pressure", reading.sensors)
        self.assertIn("rpm", reading.sensors)
        self.assertGreaterEqual(reading.compressor_power, 0.0)
        self.assertLessEqual(reading.compressor_power, 100.0)
        self.assertIn("step", reading.metadata)
        self.assertIn("noise_level", reading.metadata)

    def test_higher_power_raises_expected_sensor_values(self) -> None:
        simulator = CompressorSimulator(seed=21)

        low_power_reading = simulator.step(compressor_power=25.0)
        high_power_reading = simulator.step(compressor_power=85.0)

        self.assertLess(
            low_power_reading.sensors["temperature"],
            high_power_reading.sensors["temperature"],
        )
        self.assertLess(
            low_power_reading.sensors["pressure"],
            high_power_reading.sensors["pressure"],
        )
        self.assertLess(low_power_reading.sensors["rpm"], high_power_reading.sensors["rpm"])

    def test_higher_temperature_increases_variability_across_all_sensors(self) -> None:
        simulator = CompressorSimulator(seed=99)

        low_temperature_readings = [simulator.step(compressor_power=5.0) for _ in range(20)]
        high_temperature_readings = [simulator.step(compressor_power=95.0) for _ in range(20)]

        for sensor_name in ("temperature", "pressure", "rpm"):
            low_values = [reading.sensors[sensor_name] for reading in low_temperature_readings]
            high_values = [reading.sensors[sensor_name] for reading in high_temperature_readings]

            self.assertLess(
                statistics.pstdev(low_values),
                statistics.pstdev(high_values),
                msg=f"Expected higher variability for {sensor_name} at higher temperature",
            )

    def test_scenario_hooks_adjust_inputs_without_bypassing_simulation_output(self) -> None:
        simulator = CompressorSimulator(seed=13)
        simulator.set_control_hook(power_offset=10.0, temperature_bias=4.0)

        adjusted_reading = simulator.step(compressor_power=40.0)

        self.assertGreater(adjusted_reading.compressor_power, 40.0)
        self.assertIn("control_adjustments", adjusted_reading.metadata)
        self.assertIsInstance(adjusted_reading.sensors, dict)
        self.assertIn("temperature", adjusted_reading.sensors)


if __name__ == "__main__":
    unittest.main()
