"""Focused tests for Epic 4 Story 4.5 scenario-control."""

from __future__ import annotations

import unittest

from parallel_truth_fingerprint.config.runtime import RuntimeDemoConfig
from parallel_truth_fingerprint.scenario_control import (
    apply_runtime_scenario_control,
    resolve_runtime_scenario_control_stage,
)


class RuntimeScenarioControlTests(unittest.TestCase):
    def test_explicit_scada_replay_scenario_stays_normal_until_start_cycle(self) -> None:
        config = RuntimeDemoConfig(
            mqtt_transport="passive",
            demo_scenario_name="scada_replay",
            demo_scenario_start_cycle=4,
        )

        stage = resolve_runtime_scenario_control_stage(config=config, cycle_index=2)

        self.assertEqual(stage.configured_scenario, "scada_replay")
        self.assertEqual(stage.active_scenario, "normal")
        self.assertFalse(stage.active)
        self.assertTrue(stage.training_eligible)
        self.assertEqual(stage.expected_output_channels[0], "consensus_alert")

    def test_explicit_scada_replay_scenario_activates_and_excludes_training(self) -> None:
        config = RuntimeDemoConfig(
            mqtt_transport="passive",
            demo_scenario_name="scada_replay",
            demo_scenario_start_cycle=4,
        )

        stage = resolve_runtime_scenario_control_stage(config=config, cycle_index=4)
        cycle_config = apply_runtime_scenario_control(
            config=config,
            scenario_stage=stage,
        )

        self.assertTrue(stage.active)
        self.assertEqual(stage.active_scenario, "scada_replay")
        self.assertEqual(stage.scenario_label, "scada_replay")
        self.assertFalse(stage.training_eligible)
        self.assertEqual(stage.scada_mode, "replay")
        self.assertEqual(
            stage.expected_output_channels,
            (
                "consensus_alert",
                "persistence_stage",
                "replay_behavior",
                "fingerprint_inference",
            ),
        )
        self.assertEqual(cycle_config.demo_scada_mode, "replay")
        self.assertEqual(cycle_config.demo_scada_start_cycle, 4)
        self.assertEqual(cycle_config.demo_fault_mode, "none")

    def test_explicit_fault_scenario_maps_to_existing_fault_runtime_mode(self) -> None:
        config = RuntimeDemoConfig(
            mqtt_transport="passive",
            demo_scenario_name="single_edge_exclusion",
            demo_scenario_start_cycle=2,
        )

        stage = resolve_runtime_scenario_control_stage(config=config, cycle_index=2)
        cycle_config = apply_runtime_scenario_control(
            config=config,
            scenario_stage=stage,
        )

        self.assertTrue(stage.active)
        self.assertEqual(stage.fault_mode, "single_edge_exclusion")
        self.assertEqual(stage.scenario_label, "faulty_edge_exclusion")
        self.assertFalse(stage.training_eligible)
        self.assertEqual(cycle_config.demo_fault_mode, "single_edge_exclusion")
        self.assertEqual(cycle_config.demo_scada_mode, "match")

    def test_legacy_scada_mode_is_derived_into_explicit_scenario_control(self) -> None:
        config = RuntimeDemoConfig(
            mqtt_transport="passive",
            demo_scada_mode="freeze",
            demo_scada_start_cycle=3,
        )

        stage = resolve_runtime_scenario_control_stage(config=config, cycle_index=3)

        self.assertEqual(stage.configured_scenario, "scada_freeze")
        self.assertEqual(stage.active_scenario, "scada_freeze")
        self.assertEqual(stage.scada_mode, "freeze")
        self.assertFalse(stage.training_eligible)

    def test_explicit_scada_divergence_scenario_uses_offset_mode(self) -> None:
        config = RuntimeDemoConfig(
            mqtt_transport="passive",
            demo_scenario_name="scada_divergence",
            demo_scenario_start_cycle=2,
        )

        stage = resolve_runtime_scenario_control_stage(config=config, cycle_index=2)
        cycle_config = apply_runtime_scenario_control(
            config=config,
            scenario_stage=stage,
        )

        self.assertTrue(stage.active)
        self.assertEqual(stage.active_scenario, "scada_divergence")
        self.assertEqual(stage.scada_mode, "offset")
        self.assertFalse(stage.training_eligible)
        self.assertEqual(
            stage.expected_output_channels,
            (
                "scada_divergence_alert",
                "persistence_stage",
            ),
        )
        self.assertEqual(cycle_config.demo_scada_mode, "offset")
        self.assertEqual(cycle_config.demo_scada_start_cycle, 2)

    def test_legacy_conflicting_scenarios_are_rejected(self) -> None:
        config = RuntimeDemoConfig(
            mqtt_transport="passive",
            demo_fault_mode="single_edge_exclusion",
            demo_scada_mode="replay",
        )

        with self.assertRaises(ValueError):
            resolve_runtime_scenario_control_stage(config=config, cycle_index=1)


if __name__ == "__main__":
    unittest.main()
