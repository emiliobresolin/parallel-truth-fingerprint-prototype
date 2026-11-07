"""Authoritative acquired-current comparison regressions."""
from dataclasses import replace
import unittest

from parallel_truth_fingerprint.comparison import ComparisonBlockedError, ScadaToleranceProfile, compare_consensused_to_scada
from parallel_truth_fingerprint.scada import FakeOpcUaScadaService
from tests.comparison.test_service import build_valid_state


class CurrentDomainTests(unittest.TestCase):
    def setUp(self):
        self.valid = build_valid_state(temperature=12.0, pressure=10.0, rpm=16.0)
        self.service = FakeOpcUaScadaService()
        self.scada = self.service.project_state(self.valid)

    def compare(self, state):
        return compare_consensused_to_scada(valid_state=self.valid, scada_state=state)

    def test_display_changes_do_not_change_current_decision(self):
        display = {name: replace(item, value=-99999.0) for name, item in self.scada.sensor_values.items()}
        self.assertTrue(self.compare(replace(self.scada, sensor_values=display)).all_within_tolerance)

    def test_changed_current_with_same_display_is_detected_without_rounding(self):
        currents = dict(self.scada.behavioral_sensor_values)
        currents['temperature'] = replace(currents['temperature'], loop_current_ma=12.000000001)
        result = self.compare(replace(self.scada, behavioral_sensor_values=currents))
        self.assertFalse(result.all_within_tolerance)
        self.assertEqual(result.to_dict()['measurement_domain'], 'loop_current_ma')
        self.assertGreater(result.sensor_comparisons[0].absolute_difference, 0)

    def test_missing_and_nonfinite_currents_fail_closed(self):
        for value in (None, float('nan'), float('inf')):
            currents = dict(self.scada.behavioral_sensor_values)
            currents['temperature'] = replace(currents['temperature'], loop_current_ma=value)
            with self.assertRaises(ComparisonBlockedError):
                self.compare(replace(self.scada, behavioral_sensor_values=currents))
        with self.assertRaises(ComparisonBlockedError):
            self.compare(replace(self.scada, behavioral_sensor_values=None))

    def test_overrides_control_current_and_coherent_display(self):
        self.service.set_sensor_override('temperature', mode='offset', offset=1.0)
        state = self.service.project_state(self.valid)
        self.assertEqual(state.behavioral_sensor_values['temperature'].loop_current_ma, 13.0)
        self.assertEqual(state.sensor_values['temperature'].value, 48.0 + 9.0 / 16.0 * 47.0)
        self.assertFalse(self.compare(state).all_within_tolerance)

    def test_freeze_and_replay_keep_original_currents_and_source_ids(self):
        self.service.update_from_consensused_state(self.valid)
        self.service.set_sensor_override('temperature', mode='freeze', fixed_value=11.0)
        first = self.service.update_from_consensused_state(self.valid)
        next_valid = replace(self.valid, round_identity=replace(self.valid.round_identity, round_id='next'), sensor_values={**self.valid.sensor_values, 'temperature': 14.0})
        frozen = self.service.update_from_consensused_state(next_valid)
        self.assertEqual(frozen.behavioral_sensor_values['temperature'], first.behavioral_sensor_values['temperature'])
        self.service.set_sensor_override('temperature', mode='replay', replay_round_id=self.valid.round_identity.round_id)
        replay = self.service.project_state(next_valid)
        self.assertEqual(replay.behavioral_sensor_values['temperature'].loop_current_ma, 12.0)
        self.assertEqual(replay.behavioral_sensor_values['temperature'].source_round_id, self.valid.round_identity.round_id)
        self.assertEqual(replay.sensor_values['temperature'].value, self.scada.sensor_values['temperature'].value)

    def test_invalid_custom_ma_tolerances_rejected(self):
        for value in (-1, float('nan'), float('inf')):
            with self.assertRaises(ValueError):
                ScadaToleranceProfile(temperature=value)
