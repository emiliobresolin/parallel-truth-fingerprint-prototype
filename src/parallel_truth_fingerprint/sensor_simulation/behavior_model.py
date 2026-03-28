"""Behavior helpers for the upstream compressor simulation."""

from __future__ import annotations

import math

from parallel_truth_fingerprint.config.ranges import CompressorSimulationProfile, SensorRange


def clamp(value: float, value_range: SensorRange) -> float:
    """Clamp a value to the configured range."""

    return max(value_range.minimum, min(value, value_range.maximum))


def normalized_operating_state(
    operating_state_pct: float,
    profile: CompressorSimulationProfile,
) -> float:
    """Convert the hidden operating state from the configured range to 0..1."""

    minimum = profile.compressor_power.minimum
    maximum = profile.compressor_power.maximum
    if maximum == minimum:
        return 0.0
    clamped = clamp(operating_state_pct, profile.compressor_power)
    return (clamped - minimum) / (maximum - minimum)


def normalized_power(power: float, profile: CompressorSimulationProfile) -> float:
    """Backward-compatible alias for the earlier simulator wording."""

    return normalized_operating_state(power, profile)


def time_pattern(step_index: int, period: float, phase_shift: float = 0.0) -> float:
    """Provide a stable oscillation for easy-to-observe simulated variation."""

    return math.sin((step_index / period) + phase_shift)


def expected_sensor_values(
    operating_state_pct: float,
    step_index: int,
    profile: CompressorSimulationProfile,
) -> dict[str, float]:
    """Return expected sensor values before noise is applied."""

    state_ratio = normalized_operating_state(operating_state_pct, profile)
    lagged_ratio = normalized_operating_state(
        operating_state_pct - (8.0 * time_pattern(step_index, period=8.5, phase_shift=0.1)),
        profile,
    )
    leading_ratio = normalized_operating_state(
        operating_state_pct + (6.0 * time_pattern(step_index, period=6.0, phase_shift=0.2)),
        profile,
    )

    temperature_ratio = 0.55 * state_ratio + 0.45 * lagged_ratio
    pressure_ratio = 0.72 * state_ratio + 0.28 * lagged_ratio
    rpm_ratio = 0.88 * state_ratio + 0.12 * leading_ratio

    temperature = (
        profile.temperature.minimum
        + (profile.temperature.maximum - profile.temperature.minimum) * temperature_ratio
        + 1.8 * time_pattern(step_index, period=4.0)
    )
    pressure = (
        profile.pressure.minimum
        + (profile.pressure.maximum - profile.pressure.minimum) * pressure_ratio
        + 0.15 * time_pattern(step_index, period=5.0, phase_shift=0.4)
    )
    rpm = (
        profile.rpm.minimum
        + (profile.rpm.maximum - profile.rpm.minimum) * rpm_ratio
        + 45.0 * time_pattern(step_index, period=3.5, phase_shift=0.7)
    )

    return {
        "temperature": clamp(temperature, profile.temperature),
        "pressure": clamp(pressure, profile.pressure),
        "rpm": clamp(rpm, profile.rpm),
    }


def temperature_driven_noise_level(
    temperature: float,
    profile: CompressorSimulationProfile,
    noise_multiplier: float = 1.0,
) -> float:
    """Increase noise as temperature rises, affecting all simulated sensors."""

    temperature_ratio = normalized_operating_state(
        temperature,
        CompressorSimulationProfile(
            compressor_id=profile.compressor_id,
            compressor_power=profile.temperature,
            temperature=profile.temperature,
            pressure=profile.pressure,
            rpm=profile.rpm,
            base_noise_floor=profile.base_noise_floor,
        ),
    )
    return profile.base_noise_floor + (temperature_ratio * 0.85 * noise_multiplier)
