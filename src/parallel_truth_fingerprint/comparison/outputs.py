"""Structured output and SCADA alert helpers for Story 3.3."""

from __future__ import annotations

from parallel_truth_fingerprint.contracts.scada_alert import (
    ScadaAlert,
    ScadaAlertType,
)
from parallel_truth_fingerprint.contracts.scada_comparison import ScadaComparisonResult
from parallel_truth_fingerprint.contracts.scada_comparison_output import (
    ScadaComparisonOutput,
    ScadaDivergenceClassification,
    SensorScadaComparisonOutput,
)


def build_scada_comparison_output(
    comparison_result: ScadaComparisonResult,
) -> ScadaComparisonOutput:
    """Build the Story 3.3 structured output from the Story 3.2 result."""

    sensor_outputs = []
    for item in comparison_result.sensor_comparisons:
        sensor_outputs.append(
            SensorScadaComparisonOutput(
                sensor_name=item.sensor_name,
                physical_value=item.physical_value,
                scada_value=item.scada_value,
                absolute_difference=item.absolute_difference,
                tolerance=item.tolerance,
                tolerance_evaluation="within_tolerance"
                if item.within_tolerance
                else "outside_tolerance",
                divergence_classification=(
                    ScadaDivergenceClassification.MATCH
                    if item.within_tolerance
                    else ScadaDivergenceClassification.DIVERGENT
                ),
                contextual_evidence=item.contextual_evidence,
            )
        )

    return ScadaComparisonOutput(
        round_identity=comparison_result.round_identity,
        scada_source_round_id=comparison_result.scada_source_round_id,
        sensor_outputs=tuple(sensor_outputs),
    )


def build_scada_divergence_alert(
    comparison_output: ScadaComparisonOutput,
) -> ScadaAlert | None:
    """Emit a SCADA divergence alert only when at least one sensor diverges."""

    divergent_outputs = tuple(
        output
        for output in comparison_output.sensor_outputs
        if output.divergence_classification == ScadaDivergenceClassification.DIVERGENT
    )
    if not divergent_outputs:
        return None

    return ScadaAlert(
        alert_type=ScadaAlertType.SCADA_DIVERGENCE,
        round_identity=comparison_output.round_identity,
        scada_source_round_id=comparison_output.scada_source_round_id,
        divergent_sensor_outputs=divergent_outputs,
    )


def format_scada_comparison_output_compact(
    comparison_output: ScadaComparisonOutput,
) -> str:
    """Render a compact deterministic summary of per-sensor comparison outputs."""

    parts = []
    for output in comparison_output.sensor_outputs:
        parts.append(
            f"{output.sensor_name}="
            f"{output.divergence_classification.value}"
            f"({output.physical_value}->{output.scada_value},"
            f"diff={output.absolute_difference},tol={output.tolerance})"
        )
    return (
        f"{comparison_output.round_identity.round_id}: "
        f"scada_source={comparison_output.scada_source_round_id} "
        f"outputs[{', '.join(parts)}]"
    )


def format_scada_alert_compact(alert: ScadaAlert | None) -> str:
    """Render a compact deterministic SCADA alert line."""

    if alert is None:
        return "none"
    divergent = ", ".join(
        f"{output.sensor_name}:{output.divergence_classification.value}"
        for output in alert.divergent_sensor_outputs
    )
    return (
        f"{alert.round_identity.round_id}: "
        f"alert={alert.alert_type.value} "
        f"divergent[{divergent}]"
    )


def format_scada_alert_detailed(alert: ScadaAlert | None) -> str:
    """Render a readable SCADA alert view."""

    if alert is None:
        return "scada_alert=none"

    lines = [
        f"alert_type={alert.alert_type.value}",
        f"round={alert.round_identity.round_id}",
        f"scada_source_round={alert.scada_source_round_id}",
    ]
    for output in alert.divergent_sensor_outputs:
        lines.append(
            f"sensor={output.sensor_name} "
            f"classification={output.divergence_classification.value} "
            f"physical={output.physical_value} "
            f"scada={output.scada_value} "
            f"diff={output.absolute_difference} "
            f"tolerance={output.tolerance}"
        )
    return "\n".join(lines)
