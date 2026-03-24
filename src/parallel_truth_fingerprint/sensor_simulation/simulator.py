"""Simple upstream compressor sensor simulation."""

from __future__ import annotations

from dataclasses import dataclass, field
import random

from parallel_truth_fingerprint.config.ranges import (
    CompressorSimulationProfile,
    DEFAULT_COMPRESSOR_PROFILE,
)
from parallel_truth_fingerprint.sensor_simulation.behavior_model import (
    clamp,
    expected_sensor_values,
    temperature_driven_noise_level,
)
from parallel_truth_fingerprint.sensor_simulation.normal_profiles import (
    default_compressor_profile,
)


@dataclass
class SimulationControl:
    """Upstream-only input adjustments for later scenario control."""

    power_offset: float = 0.0
    temperature_bias: float = 0.0
    pressure_bias: float = 0.0
    rpm_bias: float = 0.0
    noise_multiplier: float = 1.0


@dataclass
class SimulationSnapshot:
    """Observable output from the sensor simulation layer."""

    compressor_id: str
    compressor_power: float
    sensors: dict[str, float]
    metadata: dict[str, object] = field(default_factory=dict)

    def to_dict(self) -> dict[str, object]:
        """Return a simple inspectable representation for logs or display."""

        return {
            "compressor_id": self.compressor_id,
            "compressor_power": self.compressor_power,
            "sensors": self.sensors,
            "metadata": self.metadata,
        }


class CompressorSimulator:
    """Generate simple, observable compressor sensor readings."""

    def __init__(
        self,
        profile: CompressorSimulationProfile | None = None,
        *,
        seed: int | None = None,
    ) -> None:
        self.profile = profile or default_compressor_profile()
        self._rng = random.Random(seed)
        self._step_index = 0
        self._control = SimulationControl()

    def set_control_hook(
        self,
        *,
        power_offset: float = 0.0,
        temperature_bias: float = 0.0,
        pressure_bias: float = 0.0,
        rpm_bias: float = 0.0,
        noise_multiplier: float = 1.0,
    ) -> None:
        """Adjust simulation inputs without bypassing the normal output flow."""

        self._control = SimulationControl(
            power_offset=power_offset,
            temperature_bias=temperature_bias,
            pressure_bias=pressure_bias,
            rpm_bias=rpm_bias,
            noise_multiplier=noise_multiplier,
        )

    def step(self, *, compressor_power: float | None = None) -> SimulationSnapshot:
        """Advance the simulation by one step and return current sensor readings."""

        requested_power = (
            compressor_power if compressor_power is not None else self._default_power()
        )
        effective_power = clamp(
            requested_power + self._control.power_offset,
            self.profile.compressor_power,
        )
        expected_values = expected_sensor_values(
            effective_power,
            self._step_index,
            self.profile,
        )
        biased_values = {
            "temperature": expected_values["temperature"] + self._control.temperature_bias,
            "pressure": expected_values["pressure"] + self._control.pressure_bias,
            "rpm": expected_values["rpm"] + self._control.rpm_bias,
        }

        noise_level = temperature_driven_noise_level(
            biased_values["temperature"],
            self.profile,
            noise_multiplier=self._control.noise_multiplier,
        )
        sensors = self._apply_noise(biased_values, noise_level)

        snapshot = SimulationSnapshot(
            compressor_id=self.profile.compressor_id,
            compressor_power=effective_power,
            sensors=sensors,
            metadata={
                "step": self._step_index,
                "noise_level": round(noise_level, 4),
                "control_adjustments": {
                    "power_offset": self._control.power_offset,
                    "temperature_bias": self._control.temperature_bias,
                    "pressure_bias": self._control.pressure_bias,
                    "rpm_bias": self._control.rpm_bias,
                    "noise_multiplier": self._control.noise_multiplier,
                },
            },
        )
        self._step_index += 1
        return snapshot

    def _default_power(self) -> float:
        midpoint = (
            self.profile.compressor_power.minimum + self.profile.compressor_power.maximum
        ) / 2
        return midpoint + (6.0 * self._rng.uniform(-1.0, 1.0))

    def _apply_noise(
        self,
        expected_values: dict[str, float],
        noise_level: float,
    ) -> dict[str, float]:
        return {
            "temperature": round(
                clamp(
                    expected_values["temperature"] + self._rng.uniform(-1.0, 1.0) * noise_level * 5.0,
                    self.profile.temperature,
                ),
                3,
            ),
            "pressure": round(
                clamp(
                    expected_values["pressure"] + self._rng.uniform(-1.0, 1.0) * noise_level * 0.35,
                    self.profile.pressure,
                ),
                3,
            ),
            "rpm": round(
                clamp(
                    expected_values["rpm"] + self._rng.uniform(-1.0, 1.0) * noise_level * 60.0,
                    self.profile.rpm,
                ),
                3,
            ),
        }
