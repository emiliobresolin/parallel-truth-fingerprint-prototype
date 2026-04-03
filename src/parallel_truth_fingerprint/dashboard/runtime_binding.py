"""Helpers for reading the dashboard runtime payload consistently."""

from __future__ import annotations


def extract_structured_payload(
    payload: dict[str, object] | None,
) -> dict[str, object]:
    """Return the structured payload for wrapped dashboard/runtime objects."""

    if not isinstance(payload, dict):
        return {}
    structured = payload.get("structured")
    if isinstance(structured, dict):
        return structured
    return payload


def extract_structured_comparison_output(
    comparison_output: dict[str, object] | None,
) -> dict[str, object]:
    """Return the structured SCADA comparison payload regardless of wrapping."""

    return extract_structured_payload(comparison_output)


def find_sensor_comparison_output(
    comparison_output: dict[str, object] | None,
    sensor_name: str,
) -> dict[str, object] | None:
    """Return the structured comparison entry for one sensor when available."""

    structured = extract_structured_comparison_output(comparison_output)
    for sensor_output in structured.get("sensor_outputs") or []:
        if sensor_output.get("sensor_name") == sensor_name:
            return sensor_output
    return None


def extract_divergent_sensors(
    comparison_output: dict[str, object] | None,
) -> tuple[str, ...]:
    """Return divergent sensors from the structured comparison payload."""

    structured = extract_structured_comparison_output(comparison_output)
    return tuple(str(sensor_name) for sensor_name in structured.get("divergent_sensors") or [])


def extract_structured_divergence_alert(
    divergence_alert: dict[str, object] | None,
) -> dict[str, object]:
    """Return the structured divergence alert payload regardless of wrapping."""

    return extract_structured_payload(divergence_alert)
