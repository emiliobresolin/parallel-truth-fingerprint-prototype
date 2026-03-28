"""Simple upstream compressor sensor simulation."""

from __future__ import annotations

from dataclasses import dataclass, field
import random

from parallel_truth_fingerprint.config.ranges import (
    CompressorSimulationProfile,
    SensorRange,
)
from parallel_truth_fingerprint.sensor_simulation.behavior_model import (
    clamp,
    expected_sensor_values,
    temperature_driven_noise_level,
)
from parallel_truth_fingerprint.sensor_simulation.normal_profiles import (
    default_compressor_profile,
)
from parallel_truth_fingerprint.sensor_simulation.transmitter_observation import (
    SimulatedTransmitterObservation,
    TransmitterDiagnosticsObservation,
    TransmitterVariableObservation,
)


@dataclass
class SimulationControl:
    """Upstream-only input adjustments for later scenario control."""

    operating_state_offset: float = 0.0
    temperature_bias: float = 0.0
    pressure_bias: float = 0.0
    rpm_bias: float = 0.0
    noise_multiplier: float = 1.0

    @property
    def power_offset(self) -> float:
        """Backward-compatible alias for earlier simulator wording."""

        return self.operating_state_offset


@dataclass
class SimulationSnapshot:
    """Observable output from the sensor simulation layer."""

    compressor_id: str
    operating_state_pct: float
    sensors: dict[str, float]
    transmitter_observations: dict[str, SimulatedTransmitterObservation]
    metadata: dict[str, object] = field(default_factory=dict)

    @property
    def compressor_power(self) -> float:
        """Backward-compatible alias for earlier simulator wording."""

        return self.operating_state_pct

    def to_dict(self) -> dict[str, object]:
        """Return a simple inspectable representation for logs or display."""

        return {
            "compressor_id": self.compressor_id,
            "operating_state_pct": self.operating_state_pct,
            "sensors": self.sensors,
            "transmitter_observations": {
                sensor_name: observation.to_dict()
                for sensor_name, observation in self.transmitter_observations.items()
            },
            "metadata": self.metadata,
        }


def _percent_range(value: float, sensor_range: SensorRange) -> float:
    span = sensor_range.maximum - sensor_range.minimum
    if span <= 0:
        return 0.0
    return round(((value - sensor_range.minimum) / span) * 100.0, 3)


def _loop_current_from_percent(percent_range: float) -> float:
    return round(4.0 + (16.0 * (percent_range / 100.0)), 3)


SENSOR_TRANSMITTER_META = {
    "temperature": {
        "unit": "degC",
        "unit_code": 32,
        "pv_description": "Process_Temperature",
    },
    "pressure": {
        "unit": "bar",
        "unit_code": 7,
        "pv_description": "Process_Pressure",
    },
    "rpm": {
        "unit": "rpm",
        "unit_code": None,
        "pv_description": "Shaft_Speed",
    },
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
        operating_state_offset: float | None = None,
        power_offset: float | None = None,
        temperature_bias: float = 0.0,
        pressure_bias: float = 0.0,
        rpm_bias: float = 0.0,
        noise_multiplier: float = 1.0,
    ) -> None:
        """Adjust simulation inputs without bypassing the normal output flow."""

        resolved_offset = (
            operating_state_offset if operating_state_offset is not None else power_offset or 0.0
        )
        self._control = SimulationControl(
            operating_state_offset=resolved_offset,
            temperature_bias=temperature_bias,
            pressure_bias=pressure_bias,
            rpm_bias=rpm_bias,
            noise_multiplier=noise_multiplier,
        )

    def step(
        self,
        *,
        operating_state_pct: float | None = None,
        compressor_power: float | None = None,
    ) -> SimulationSnapshot:
        """Advance the simulation by one step and return current sensor readings."""

        requested_operating_state = self._resolve_operating_state(
            operating_state_pct=operating_state_pct,
            compressor_power=compressor_power,
        )
        effective_operating_state = clamp(
            requested_operating_state + self._control.operating_state_offset,
            self.profile.compressor_power,
        )
        expected_values = expected_sensor_values(
            effective_operating_state,
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
        transmitter_observations = self._build_transmitter_observations(
            sensors,
            operating_state_pct=effective_operating_state,
        )

        snapshot = SimulationSnapshot(
            compressor_id=self.profile.compressor_id,
            operating_state_pct=effective_operating_state,
            sensors=sensors,
            transmitter_observations=transmitter_observations,
            metadata={
                "step": self._step_index,
                "noise_level": round(noise_level, 4),
                "hidden_process_state": {
                    "driver": "compressor_load_pct",
                    "operating_state_pct": round(effective_operating_state, 3),
                },
                "control_adjustments": {
                    "operating_state_offset": self._control.operating_state_offset,
                    "temperature_bias": self._control.temperature_bias,
                    "pressure_bias": self._control.pressure_bias,
                    "rpm_bias": self._control.rpm_bias,
                    "noise_multiplier": self._control.noise_multiplier,
                },
            },
        )
        self._step_index += 1
        return snapshot

    def _resolve_operating_state(
        self,
        *,
        operating_state_pct: float | None,
        compressor_power: float | None,
    ) -> float:
        if operating_state_pct is not None:
            return operating_state_pct
        if compressor_power is not None:
            return compressor_power
        return self._default_operating_state()

    def _default_operating_state(self) -> float:
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
                    expected_values["temperature"]
                    + self._rng.uniform(-1.0, 1.0) * noise_level * 5.0,
                    self.profile.temperature,
                ),
                3,
            ),
            "pressure": round(
                clamp(
                    expected_values["pressure"]
                    + self._rng.uniform(-1.0, 1.0) * noise_level * 0.35,
                    self.profile.pressure,
                ),
                3,
            ),
            "rpm": round(
                clamp(
                    expected_values["rpm"]
                    + self._rng.uniform(-1.0, 1.0) * noise_level * 60.0,
                    self.profile.rpm,
                ),
                3,
            ),
        }

    def _build_transmitter_observations(
        self,
        sensors: dict[str, float],
        *,
        operating_state_pct: float,
    ) -> dict[str, SimulatedTransmitterObservation]:
        observations: dict[str, SimulatedTransmitterObservation] = {}
        for sensor_name, pv_value in sensors.items():
            sensor_range = getattr(self.profile, sensor_name)
            percent_range = _percent_range(pv_value, sensor_range)
            loop_current = _loop_current_from_percent(percent_range)
            sensor_meta = SENSOR_TRANSMITTER_META[sensor_name]

            observations[sensor_name] = SimulatedTransmitterObservation(
                sensor_name=sensor_name,
                operating_state_pct=round(operating_state_pct, 3),
                pv=TransmitterVariableObservation(
                    value=round(pv_value, 3),
                    unit=sensor_meta["unit"],
                    unit_code=sensor_meta["unit_code"],
                    description=sensor_meta["pv_description"],
                ),
                sv=self._secondary_variable_for(
                    sensor_name,
                    pv_value=pv_value,
                    operating_state_pct=operating_state_pct,
                ),
                loop_current_ma=loop_current,
                pv_percent_range=percent_range,
                diagnostics=TransmitterDiagnosticsObservation(
                    device_status_hex="0x00",
                    field_device_malfunction=False,
                    loop_current_saturated=loop_current <= 4.0 or loop_current >= 20.0,
                ),
            )
        return observations

    def _secondary_variable_for(
        self,
        sensor_name: str,
        *,
        pv_value: float,
        operating_state_pct: float,
    ) -> TransmitterVariableObservation | None:
        if sensor_name == "temperature":
            return TransmitterVariableObservation(
                value=round(
                    clamp(
                        21.0 + (operating_state_pct * 0.18) + (pv_value * 0.32),
                        SensorRange(minimum=20.0, maximum=75.0),
                    ),
                    3,
                ),
                unit="degC",
                unit_code=32,
                description="Sensor_Body_Temperature",
            )

        if sensor_name == "pressure":
            return TransmitterVariableObservation(
                value=round(
                    clamp(
                        24.0 + (operating_state_pct * 0.12) + (self._step_index % 3) * 0.4,
                        SensorRange(minimum=20.0, maximum=55.0),
                    ),
                    3,
                ),
                unit="degC",
                unit_code=32,
                description="Transmitter_Module_Temperature",
            )

        return None
