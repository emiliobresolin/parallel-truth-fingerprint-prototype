"""Statistical and integration checks for the documented sampled-noise profile."""
import json
import copy
import math
import statistics
import unittest

from parallel_truth_fingerprint.sensor_simulation.current_noise import (
    SampledCurrentNoise, noise_configuration, noise_rms_ma, validate_noise_configuration,
)
from parallel_truth_fingerprint.sensor_simulation.simulator import CompressorSimulator
from parallel_truth_fingerprint.sensor_simulation.operational_profiles import OperationalCompressorSimulator
from parallel_truth_fingerprint.sensor_simulation.mass_flow import MassFlowCompressorSimulator
from parallel_truth_fingerprint.evidence.paired_replay import verify_recorded_noise


class DocumentedCurrentNoiseTests(unittest.TestCase):
    def test_published_units_and_configuration_are_frozen(self):
        configuration = noise_configuration()
        self.assertEqual(configuration['rms_ma'], 782 / 1_000_000)
        self.assertEqual(configuration['reference_current_ma'], 3)
        self.assertEqual(configuration['reference_adc_samples_per_second'], 31000)
        self.assertIsNone(configuration['bandwidth_hz'])
        validate_noise_configuration(json.loads(json.dumps(configuration)))
        configuration['rms_ma'] *= 10
        with self.assertRaises(ValueError):
            validate_noise_configuration(configuration)
        with self.assertRaises(ValueError):
            validate_noise_configuration(None)
        self.assertEqual(noise_rms_ma(), 0.000782)

    def test_persisted_acquisition_noise_provenance_rejects_tampering(self):
        frame = CompressorSimulator(seed=606).step(operating_state_pct=50).to_dict()
        generation = dict(current_noise_configuration=noise_configuration(),
            current_noise_multiplier=1.0, acquisition_snapshot=frame)
        self.assertEqual(verify_recorded_noise(generation, noise_configuration()), frame)
        currents = {channel: observation['loop_current_ma']
            for channel, observation in frame['transmitter_observations'].items()}
        verify_recorded_noise(generation, noise_configuration(), currents)
        wrong_currents = dict(currents, rpm=currents['rpm'] + 0.001)
        with self.assertRaises(ValueError):
            verify_recorded_noise(generation, noise_configuration(), wrong_currents)
        changed = copy.deepcopy(generation)
        changed['current_noise_multiplier'] = 2
        changed['acquisition_snapshot']['metadata']['current_noise_ma'] *= 2
        changed['acquisition_snapshot']['metadata']['control_adjustments']['current_noise_multiplier'] = 2
        with self.assertRaises(ValueError):
            verify_recorded_noise(changed, noise_configuration())
        for key in ('current_noise_configuration', 'current_noise_ma', 'control_adjustments'):
            changed = copy.deepcopy(generation)
            del changed['acquisition_snapshot']['metadata'][key]
            with self.subTest(key=key), self.assertRaises(ValueError):
                verify_recorded_noise(changed, noise_configuration())

    def test_samples_have_reference_rms_zero_mean_and_small_lag_correlation(self):
        noise = SampledCurrentNoise(606)
        samples = [noise.sample_ma('temperature') for _ in range(100000)]
        sigma = noise_rms_ma()
        self.assertLess(abs(statistics.mean(samples)), 0.02 * sigma)
        self.assertLess(abs(statistics.pstdev(samples) / sigma - 1), 0.02)
        self.assertLess(abs(statistics.correlation(samples[:-1], samples[1:])), 0.02)

    def test_channel_reproducibility_independence_and_addition(self):
        left, right = SampledCurrentNoise(606), SampledCurrentNoise(606)
        temperature, pressure = [], []
        for _ in range(10000):
            value = left.sample_ma('temperature')
            right.sample_ma('mass_flow')
            self.assertEqual(value, right.sample_ma('temperature'))
            temperature.append(value)
            pressure.append(left.sample_ma('pressure'))
        self.assertLess(abs(statistics.correlation(temperature, pressure)), 0.04)
        self.assertNotEqual(temperature[:10], [SampledCurrentNoise(607).sample_ma('temperature') for _ in range(10)])

    def test_control_multiplier_and_invalid_values(self):
        for value in (-1, math.nan, math.inf, -math.inf, True, None, '1'):
            with self.subTest(value=value), self.assertRaises(ValueError):
                CompressorSimulator(seed=1).set_control_hook(current_noise_multiplier=value)
        enabled, disabled = SampledCurrentNoise(1), SampledCurrentNoise(1)
        self.assertEqual(disabled.sample_ma('rpm', multiplier=0), 0)
        enabled.sample_ma('rpm')
        self.assertEqual(disabled.sample_ma('rpm'), enabled.sample_ma('rpm'))
        left, right = SampledCurrentNoise(1), SampledCurrentNoise(1)
        self.assertEqual(left.sample_ma('rpm', multiplier=2), 2 * right.sample_ma('rpm'))

    def test_noise_scale_does_not_depend_on_demand_or_process_rng(self):
        low, high = CompressorSimulator(seed=1), CompressorSimulator(seed=1)
        for _ in range(20):
            low_current = low.step(operating_state_pct=25).transmitter_observations['rpm'].loop_current_ma
            high_current = high.step(operating_state_pct=75).transmitter_observations['rpm'].loop_current_ma
            self.assertAlmostEqual(low_current - 8, high_current - 16, places=13)
        noisy, quiet = CompressorSimulator(seed=2), CompressorSimulator(seed=2)
        quiet.set_control_hook(current_noise_multiplier=0)
        for _ in range(20):
            self.assertEqual(noisy.step().operating_state_pct, quiet.step().operating_state_pct)

    def test_nominal_endpoint_saturation_does_not_disable_noise(self):
        for demand, limit, comparison in ((0, 4, lambda x: x > 4), (100, 20, lambda x: x < 20)):
            simulator = CompressorSimulator(seed=8)
            values = [simulator.step(operating_state_pct=demand).transmitter_observations['rpm'].loop_current_ma for _ in range(200)]
            self.assertTrue(all(4 <= value <= 20 for value in values))
            self.assertIn(limit, values)
            self.assertTrue(any(comparison(value) for value in values))

    def test_all_four_channels_preserve_noise_precision_and_metadata(self):
        arguments = dict(modulated=False, sample_seconds=1, seed=606)
        three = OperationalCompressorSimulator(**arguments)
        four = MassFlowCompressorSimulator(**arguments)
        quiet = MassFlowCompressorSimulator(**arguments)
        quiet.set_control_hook(current_noise_multiplier=0)
        residuals = {channel: [] for channel in ('temperature', 'pressure', 'rpm', 'mass_flow')}
        for _ in range(1000):
            three_frame, frame, quiet_frame = three.step(), four.step(), quiet.step()
            self.assertEqual(frame.metadata['current_noise_configuration'], noise_configuration())
            self.assertEqual(frame.metadata['current_noise_ma'], noise_rms_ma())
            for channel in residuals:
                current = frame.transmitter_observations[channel].loop_current_ma
                self.assertEqual(json.loads(json.dumps(frame.to_dict()))['transmitter_observations'][channel]['loop_current_ma'], current)
                residuals[channel].append(current - quiet_frame.transmitter_observations[channel].loop_current_ma)
                if channel != 'mass_flow':
                    self.assertEqual(current, three_frame.transmitter_observations[channel].loop_current_ma)
        for channel, values in residuals.items():
            with self.subTest(channel=channel):
                self.assertLess(abs(statistics.pstdev(values) / noise_rms_ma() - 1), 0.1)
                self.assertTrue(any(abs(value - round(value, 3)) > 1e-8 for value in values))


if __name__ == '__main__':
    unittest.main()
