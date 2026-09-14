"""Simulation configuration for normal compressor operating ranges."""

from dataclasses import dataclass


@dataclass(frozen=True)
class SensorRange:
    """Inclusive normal operating range for a simulated sensor."""

    minimum: float
    maximum: float


@dataclass(frozen=True)
class CompressorSimulationProfile:
    """Static configuration for the single simulated compressor."""

    compressor_id: str
    compressor_power: SensorRange
    temperature: SensorRange
    pressure: SensorRange
    rpm: SensorRange
    base_noise_floor: float


DEFAULT_COMPRESSOR_PROFILE = CompressorSimulationProfile(
    compressor_id="compressor-1",
    compressor_power=SensorRange(minimum=0.0, maximum=100.0),
    temperature=SensorRange(minimum=48.0, maximum=95.0),
    pressure=SensorRange(minimum=1.8, maximum=8.5),
    # FB420 prototype configuration: user-approved, bounded within the
    # archived manual's programmable 0..9999 RPM capability.  Its electrical
    # endpoints are 4 mA at 500 RPM and 20 mA at 5000 RPM.
    rpm=SensorRange(minimum=500.0, maximum=5000.0),
    base_noise_floor=0.15,
)
