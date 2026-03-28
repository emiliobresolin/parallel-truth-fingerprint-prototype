import statistics
import unittest

from parallel_truth_fingerprint.sensor_simulation.simulator import CompressorSimulator


class CompressorSimulatorTest(unittest.TestCase):
    def test_step_produces_all_expected_outputs(self) -> None:
        simulator = CompressorSimulator(seed=7)

        reading = simulator.step()

        self.assertEqual(reading.compressor_id, "compressor-1")
        self.assertGreaterEqual(reading.operating_state_pct, 0.0)
        self.assertLessEqual(reading.operating_state_pct, 100.0)
        self.assertIn("temperature", reading.sensors)
        self.assertIn("pressure", reading.sensors)
        self.assertIn("rpm", reading.sensors)
        self.assertIn("temperature", reading.transmitter_observations)
        self.assertIn("pressure", reading.transmitter_observations)
        self.assertIn("rpm", reading.transmitter_observations)
        self.assertIn("step", reading.metadata)
        self.assertIn("noise_level", reading.metadata)
        self.assertIn("hidden_process_state", reading.metadata)

    def test_higher_power_raises_expected_sensor_values(self) -> None:
        simulator = CompressorSimulator(seed=21)

        low_power_reading = simulator.step(operating_state_pct=25.0)
        high_power_reading = simulator.step(operating_state_pct=85.0)

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

        low_temperature_readings = [simulator.step(operating_state_pct=5.0) for _ in range(20)]
        high_temperature_readings = [simulator.step(operating_state_pct=95.0) for _ in range(20)]

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
        simulator.set_control_hook(operating_state_offset=10.0, temperature_bias=4.0)

        adjusted_reading = simulator.step(operating_state_pct=40.0)

        self.assertGreater(adjusted_reading.operating_state_pct, 40.0)
        self.assertIn("control_adjustments", adjusted_reading.metadata)
        self.assertIsInstance(adjusted_reading.sensors, dict)
        self.assertIn("temperature", adjusted_reading.sensors)

    def test_transmitter_observations_preserve_pv_and_optional_sv_semantics(self) -> None:
        simulator = CompressorSimulator(seed=5)

        reading = simulator.step(operating_state_pct=62.0)

        temperature_observation = reading.transmitter_observations["temperature"]
        pressure_observation = reading.transmitter_observations["pressure"]
        rpm_observation = reading.transmitter_observations["rpm"]

        self.assertEqual(temperature_observation.pv.description, "Process_Temperature")
        self.assertEqual(pressure_observation.pv.description, "Process_Pressure")
        self.assertEqual(rpm_observation.pv.description, "Shaft_Speed")
        self.assertIsNotNone(temperature_observation.sv)
        self.assertIsNotNone(pressure_observation.sv)
        self.assertIsNone(rpm_observation.sv)
        self.assertNotEqual(
            temperature_observation.sv.description if temperature_observation.sv else "",
            "Compressor_Power",
        )


if __name__ == "__main__":
    unittest.main()
