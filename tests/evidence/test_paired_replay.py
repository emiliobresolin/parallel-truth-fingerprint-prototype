"""Behavioral assumptions and paired observations, without tuning against test scores."""
from dataclasses import asdict
from pathlib import Path
import sys
import unittest

sys.path.insert(0, str(Path(__file__).resolve().parents[2] / 'src'))
from parallel_truth_fingerprint.sensor_simulation.operational_profiles import OperationalCompressorSimulator, OperationalAssumptions
from parallel_truth_fingerprint.evidence.paired_replay import PairedReplayProtocol, replay_view, paired_metrics
from parallel_truth_fingerprint.contracts.scada_state import ScadaState, ScadaSensorState, ScadaBehavioralSensorState


class PairedReplayTests(unittest.TestCase):
    def test_simulation_seed_can_change_without_changing_training_seed(self):
        p = PairedReplayProtocol(simulation_seed=202)
        p.validate()
        self.assertEqual(p.seed, 101)
        self.assertEqual(p.simulation_seed, 202)
        with self.assertRaises(ValueError):
            PairedReplayProtocol(simulation_seed=-1).validate()

    def test_fixed_protocol_counts_and_normal_reference_coverage(self):
        p = PairedReplayProtocol()
        self.assertEqual(len(p.profile_schedule()), 690)
        self.assertEqual(len(p.schedule()), 1380)
        self.assertEqual(sum(phase in {'stable', 'transition'} for phase, _, _ in p.profile_schedule()), 300)
        for phase, length in [('train', p.train_rounds), ('calibration', p.calibration_rounds)]:
            targets = {p.demand_target(phase, i) for i in range(length)}
            self.assertEqual(targets, {50, 75})

    def test_channels_are_distinct_and_old_fixed_argument_is_not_used(self):
        s = OperationalCompressorSimulator(modulated=False, sample_seconds=5/3, seed=101)
        frame = s.step(compressor_power=65)
        self.assertEqual(frame.operating_state_pct, 50)
        currents = [p.loop_current_ma for p in frame.transmitter_observations.values()]
        self.assertEqual(len(set(currents)), 3)
        self.assertTrue(all(4 <= value <= 20 for value in currents))
        self.assertAlmostEqual(s.engineering_state['pressure'], 7)

    def test_ramp_is_bounded_and_thermal_response_is_slower(self):
        s = OperationalCompressorSimulator(modulated=False, sample_seconds=5/3, seed=101)
        before = dict(s.engineering_state)
        s.set_demand_target(75)
        s.step()
        self.assertLess(s.base_demand, 51)
        for _ in range(71):
            s.step()
        self.assertEqual(s.base_demand, 75)
        rpm_target = 500 + 4500 * .75
        temp_target = 55 + 30 * .75
        rpm_remaining = (rpm_target - s.engineering_state['rpm']) / (rpm_target - before['rpm'])
        temp_remaining = (temp_target - s.engineering_state['temperature']) / (temp_target - before['temperature'])
        self.assertGreater(temp_remaining, rpm_remaining)
        self.assertLess(abs(s.engineering_state['pressure'] - 7), .1)

    def test_modulation_is_smooth_bounded_and_reproducible(self):
        a = OperationalCompressorSimulator(modulated=True, sample_seconds=5/3, seed=101)
        b = OperationalCompressorSimulator(modulated=True, sample_seconds=5/3, seed=101)
        values = []
        for _ in range(144):
            x, y = a.step(), b.step()
            self.assertEqual(x.to_dict(), y.to_dict())
            values.append(x.operating_state_pct)
        self.assertGreater(max(values) - min(values), 9)
        self.assertTrue(all(45 <= x <= 55 for x in values))
        self.assertLess(max(abs(y-x) for x,y in zip(values, values[1:])), .5)

    def test_historical_view_does_not_modify_the_live_view(self):
        def state(number):
            return ScadaState('c', f'r-{number}', f't-{number}', {'rpm': ScadaSensorState(number, 'rpm')},
                f'r-{number}', {'rpm': ScadaBehavioralSensorState(loop_current_ma=number, source_round_id=f'r-{number}')})
        old, current = state(5), state(10)
        projected = replay_view(current, old)
        self.assertEqual(projected.sensor_values['rpm'].value, 5)
        self.assertEqual(projected.timestamp, 't-10')
        self.assertEqual(projected.behavioral_source_round_id, 'r-5')
        self.assertEqual(current.sensor_values['rpm'].value, 10)
        self.assertEqual(old.sensor_values['rpm'].mode, 'match')


if __name__ == '__main__':
    unittest.main()
