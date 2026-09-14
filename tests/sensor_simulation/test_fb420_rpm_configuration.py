from __future__ import annotations

import unittest

from parallel_truth_fingerprint.config.ranges import DEFAULT_COMPRESSOR_PROFILE
from parallel_truth_fingerprint.sensor_simulation.simulator import (
    _loop_current_from_percent,
    _percent_range,
)


class Fb420RpmConfigurationTests(unittest.TestCase):
    def test_selected_rpm_endpoints_map_to_documented_current_endpoints(self) -> None:
        rpm = DEFAULT_COMPRESSOR_PROFILE.rpm
        self.assertEqual((rpm.minimum, rpm.maximum), (500.0, 5000.0))
        self.assertEqual(_loop_current_from_percent(_percent_range(rpm.minimum, rpm)), 4.0)
        self.assertEqual(_loop_current_from_percent(_percent_range(rpm.maximum, rpm)), 20.0)


if __name__ == "__main__":
    unittest.main()
