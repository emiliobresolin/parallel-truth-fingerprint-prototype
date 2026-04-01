"""Comparison services for physical-side versus SCADA-side evaluation."""

from parallel_truth_fingerprint.comparison.outputs import (
    build_scada_comparison_output,
    build_scada_divergence_alert,
    format_scada_alert_compact,
    format_scada_alert_detailed,
    format_scada_comparison_output_compact,
)
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
    "build_scada_comparison_output",
    "build_scada_divergence_alert",
    "compare_consensused_to_scada",
    "format_scada_alert_compact",
    "format_scada_alert_detailed",
    "format_scada_comparison_output_compact",
]
