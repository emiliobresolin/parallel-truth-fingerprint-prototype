"""Offline current-boundary and repeated runtime configuration regressions."""
from dataclasses import replace
from types import SimpleNamespace
import unittest

from parallel_truth_fingerprint.lstm_service.dataset_builder import extract_feature_vector
from parallel_truth_fingerprint.lstm_service.replay_behavior import configure_scada_replay_runtime_stage
from parallel_truth_fingerprint.scada import FakeOpcUaScadaService
from tests.comparison.test_service import build_valid_state
from tests.lstm_service.test_dataset_builder import build_persisted_artifact


class CurrentBoundaryRegressionTests(unittest.TestCase):
    def test_persisted_invalid_currents_are_rejected_before_model_input(self):
        for invalid in (None, float('nan'), float('inf'), -float('inf'), 'invalid'):
            with self.subTest(invalid=invalid):
                artifact = build_persisted_artifact(index=1)
                artifact['validated_state']['structured_payload_snapshot']['payloads_by_sensor']['temperature']['process_data']['loop_current_ma'] = invalid
                with self.assertRaisesRegex(ValueError, 'Finite acquired current'):
                    extract_feature_vector(artifact)
        artifact = build_persisted_artifact(index=1)
        del artifact['validated_state']['structured_payload_snapshot']['payloads_by_sensor']['temperature']['process_data']['loop_current_ma']
        with self.assertRaisesRegex(ValueError, 'Finite acquired current'):
            extract_feature_vector(artifact)

    def test_repeated_runtime_configuration_preserves_freeze_and_inactive_resets(self):
        service = FakeOpcUaScadaService()
        config = SimpleNamespace(demo_scada_mode='freeze', demo_scada_start_cycle=2)
        valid = build_valid_state(temperature=12.0, pressure=10.0, rpm=16.0)
        configure_scada_replay_runtime_stage(scada_service=service, config=config, cycle_index=2)
        frozen = service.update_from_consensused_state(valid)
        next_valid = replace(valid, round_identity=replace(valid.round_identity, round_id='next'), sensor_values={**valid.sensor_values, 'temperature': 15.0})
        configure_scada_replay_runtime_stage(scada_service=service, config=config, cycle_index=3)
        still_frozen = service.update_from_consensused_state(next_valid)
        self.assertEqual(still_frozen.behavioral_sensor_values, frozen.behavioral_sensor_values)
        self.assertEqual(still_frozen.sensor_values, frozen.sensor_values)
        self.assertEqual(still_frozen.behavioral_source_round_id, valid.round_identity.round_id)

        config.demo_scada_mode = 'match'
        configure_scada_replay_runtime_stage(scada_service=service, config=config, cycle_index=4)
        matched = service.update_from_consensused_state(next_valid)
        self.assertEqual(matched.behavioral_sensor_values['temperature'].loop_current_ma, 15.0)
        config.demo_scada_mode = 'freeze'
        configure_scada_replay_runtime_stage(scada_service=service, config=config, cycle_index=5)
        refrozen = service.update_from_consensused_state(next_valid)
        self.assertEqual(refrozen.behavioral_source_round_id, 'next')
        self.assertEqual(refrozen.behavioral_sensor_values['temperature'].loop_current_ma, 15.0)
