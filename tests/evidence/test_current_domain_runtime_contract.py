from __future__ import annotations

import json
from pathlib import Path
import unittest

from parallel_truth_fingerprint.config.ranges import DEFAULT_COMPRESSOR_PROFILE
from parallel_truth_fingerprint.lstm_service.dataset_builder import extract_feature_vector
from parallel_truth_fingerprint.sensor_simulation.simulator import CompressorSimulator
from tests.lstm_service.test_dataset_builder import build_persisted_artifact


ROOT = Path(__file__).resolve().parents[2]


class CurrentDomainRuntimeContractTests(unittest.TestCase):
    def test_selected_rpm_projection_is_traceable_and_electrically_bounded(self) -> None:
        contract = json.loads(
            (ROOT / "docs/reference-archive/catalog/current-domain-runtime-contract.v1.json").read_text(
                encoding="utf-8"
            )
        )
        projection = contract["rpm_display_projection"]
        self.assertEqual(DEFAULT_COMPRESSOR_PROFILE.rpm.minimum, projection["selected_minimum_rpm"])
        self.assertEqual(DEFAULT_COMPRESSOR_PROFILE.rpm.maximum, projection["selected_maximum_rpm"])
        simulator = CompressorSimulator(seed=1)
        low = simulator.step(operating_state_pct=0).transmitter_observations["rpm"]
        high = simulator.step(operating_state_pct=100).transmitter_observations["rpm"]
        self.assertEqual(low.loop_current_ma, 4.0)
        self.assertEqual(high.loop_current_ma, 20.0)
        self.assertEqual(low.pv.value, 500.0)
        self.assertEqual(high.pv.value, 5000.0)

    def test_fingerprint_vector_excludes_engineering_and_physics_fields(self) -> None:
        schema, _ = extract_feature_vector(build_persisted_artifact(index=1))
        self.assertTrue(all(".pv" not in feature for feature in schema))
        self.assertTrue(all("physics" not in feature for feature in schema))
        self.assertTrue(any(feature.endswith("loop_current_ma") for feature in schema))


if __name__ == "__main__":
    unittest.main()
