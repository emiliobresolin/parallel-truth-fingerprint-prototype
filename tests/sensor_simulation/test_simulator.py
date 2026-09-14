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
        self.assertEqual(reading.metadata["input_domain"], "loop_current_ma")
        self.assertIn("current_noise_ma", reading.metadata)
        self.assertIn("hidden_process_state", reading.metadata)

    def test_higher_power_raises_loop_current_and_derived_display_values(self) -> None:
        simulator = CompressorSimulator(seed=21)

        low_power_reading = simulator.step(operating_state_pct=25.0)
        high_power_reading = simulator.step(operating_state_pct=85.0)

        for sensor_name in ("temperature", "pressure", "rpm"):
            self.assertLess(
                low_power_reading.transmitter_observations[sensor_name].loop_current_ma,
                high_power_reading.transmitter_observations[sensor_name].loop_current_ma,
            )
            self.assertLess(
                low_power_reading.sensors[sensor_name],
                high_power_reading.sensors[sensor_name],
            )

    def test_loop_current_stays_inside_the_official_interval(self) -> None:
        simulator = CompressorSimulator(seed=99)

        for operating_state in (0.0, 50.0, 100.0):
            reading = simulator.step(operating_state_pct=operating_state)
            for observation in reading.transmitter_observations.values():
                self.assertGreaterEqual(observation.loop_current_ma, 4.0)
                self.assertLessEqual(observation.loop_current_ma, 20.0)

    def test_scenario_hooks_adjust_inputs_without_bypassing_simulation_output(self) -> None:
        simulator = CompressorSimulator(seed=13)
        simulator.set_control_hook(
            operating_state_offset=10.0,
            temperature_current_bias_ma=0.5,
        )

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
        self.assertEqual(temperature_observation.sv.description, "Sensor_Body_Temperature")
        self.assertEqual(pressure_observation.sv.description, "Transmitter_Module_Temperature")
        self.assertIsNone(rpm_observation.sv)
        self.assertNotEqual(
            temperature_observation.sv.description if temperature_observation.sv else "",
            "Compressor_Power",
        )


if __name__ == "__main__":
    unittest.main()
