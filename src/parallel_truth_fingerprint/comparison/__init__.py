"""Comparison services for physical-side versus SCADA-side evaluation."""

from parallel_truth_fingerprint.comparison.service import (
    COMPARISON_SENSOR_ORDER,
    ComparisonBlockedError,
    ScadaToleranceProfile,
    compare_consensused_to_scada,
)

__all__ = [
    "COMPARISON_SENSOR_ORDER",
    "ComparisonBlockedError",
    "ScadaToleranceProfile",
    "compare_consensused_to_scada",
]
