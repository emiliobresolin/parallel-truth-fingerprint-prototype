"""Behavior helpers for the upstream compressor simulation."""

from __future__ import annotations

import math

from parallel_truth_fingerprint.config.ranges import CompressorSimulationProfile, SensorRange


def clamp(value: float, value_range: SensorRange) -> float:
    """Clamp a value to the configured range."""

    return max(value_range.minimum, min(value, value_range.maximum))


def normalized_power(power: float, profile: CompressorSimulationProfile) -> float:
    """Convert power from the configured range to 0..1."""

    minimum = profile.compressor_power.minimum
    maximum = profile.compressor_power.maximum
    if maximum == minimum:
        return 0.0
    clamped = clamp(power, profile.compressor_power)
    return (clamped - minimum) / (maximum - minimum)


def time_pattern(step_index: int, period: float, phase_shift: float = 0.0) -> float:
    """Provide a stable oscillation for easy-to-observe simulated variation."""

    return math.sin((step_index / period) + phase_shift)


def expected_sensor_values(
    power: float,
    step_index: int,
    profile: CompressorSimulationProfile,
) -> dict[str, float]:
    """Return expected sensor values before noise is applied."""

    power_ratio = normalized_power(power, profile)

    temperature = (
        profile.temperature.minimum
        + (profile.temperature.maximum - profile.temperature.minimum) * power_ratio
        + 1.8 * time_pattern(step_index, period=4.0)
    )
    pressure = (
        profile.pressure.minimum
        + (profile.pressure.maximum - profile.pressure.minimum) * power_ratio
        + 0.15 * time_pattern(step_index, period=5.0, phase_shift=0.4)
    )
    rpm = (
        profile.rpm.minimum
        + (profile.rpm.maximum - profile.rpm.minimum) * power_ratio
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

    temperature_ratio = normalized_power(
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
