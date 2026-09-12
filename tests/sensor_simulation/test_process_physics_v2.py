from __future__ import annotations

import unittest

from parallel_truth_fingerprint.sensor_simulation.process_physics import EngineeringChannel, EngineeringFrame


class EngineeringFrameTests(unittest.TestCase):
    def test_frame_preserves_only_injected_canonical_engineering_values(self) -> None:
        def channel(name: str, unit: str) -> EngineeringChannel:
            return EngineeringChannel(name, name, unit, "1", "sha256:trace", "sha256:gate", "sha256:mock", "present")
        frame = EngineeringFrame(channel("temperature", "degC"), channel("pressure", "bar_g"),
                                channel("rotational_speed", "rpm"), "sha256:frame")
        frame.validate()
        invalid = EngineeringFrame(
            EngineeringChannel("temperature", "temperature", "degC", "SENTINEL", "sha256:trace", "sha256:gate", "sha256:mock", "present"),
            frame.pressure, frame.rotational_speed, frame.frame_trace_reference,
        )
        with self.assertRaisesRegex(ValueError, "PTEV2_PROCESS_PROFILE"):
            invalid.validate()


if __name__ == "__main__":
    unittest.main()
