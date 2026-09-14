"""Current-domain upstream compressor transmitter simulation.

The simulation starts with the value observed by an edge: loop current in the
official 4--20 mA interval. Engineering-unit PV values are derived only for
the legacy HART/dashboard envelope and are never fingerprint inputs.
"""

from __future__ import annotations

from dataclasses import dataclass, field
import random

from parallel_truth_fingerprint.config.ranges import (
    CompressorSimulationProfile,
    SensorRange,
)
from parallel_truth_fingerprint.sensor_simulation.behavior_model import clamp
from parallel_truth_fingerprint.sensor_simulation.normal_profiles import (
    default_compressor_profile,
)
from parallel_truth_fingerprint.sensor_simulation.transmitter_observation import (
    SimulatedTransmitterObservation,
    TransmitterDiagnosticsObservation,
    TransmitterVariableObservation,
)


LOOP_CURRENT_MIN_MA = 4.0
LOOP_CURRENT_MAX_MA = 20.0


@dataclass
class SimulationControl:
    """Electrical input adjustments for controlled demo scenarios."""

    operating_state_offset: float = 0.0
    temperature_current_bias_ma: float = 0.0
    pressure_current_bias_ma: float = 0.0
    rpm_current_bias_ma: float = 0.0
    current_noise_multiplier: float = 1.0

    @property
    def power_offset(self) -> float:
        """Backward-compatible name for the operating-state adjustment."""

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
        return self.operating_state_pct

    def to_dict(self) -> dict[str, object]:
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

_SECONDARY_VARIABLE_META = {
    "temperature": ("Sensor_Body_Temperature", "degC", 32),
    "pressure": ("Transmitter_Module_Temperature", "degC", 32),
}


class CompressorSimulator:
    """Generate current-first transmitter readings for the local prototype."""

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
        temperature_current_bias_ma: float = 0.0,
        pressure_current_bias_ma: float = 0.0,
        rpm_current_bias_ma: float = 0.0,
        current_noise_multiplier: float = 1.0,
    ) -> None:
        """Adjust electrical input without bypassing the normal data flow."""

        resolved_offset = (
            operating_state_offset if operating_state_offset is not None else power_offset or 0.0
        )
        self._control = SimulationControl(
            operating_state_offset=resolved_offset,
            temperature_current_bias_ma=temperature_current_bias_ma,
            pressure_current_bias_ma=pressure_current_bias_ma,
            rpm_current_bias_ma=rpm_current_bias_ma,
            current_noise_multiplier=current_noise_multiplier,
        )

    def step(
        self,
        *,
        operating_state_pct: float | None = None,
        compressor_power: float | None = None,
    ) -> SimulationSnapshot:
        """Advance one current-domain acquisition cycle."""

        requested_operating_state = self._resolve_operating_state(
            operating_state_pct=operating_state_pct,
            compressor_power=compressor_power,
        )
        effective_operating_state = clamp(
            requested_operating_state + self._control.operating_state_offset,
            self.profile.compressor_power,
        )
        loop_currents, current_noise_ma = self._build_loop_currents(
            effective_operating_state
        )
        transmitter_observations = self._build_transmitter_observations(
            loop_currents,
            operating_state_pct=effective_operating_state,
        )
        # Display/protocol projections only. The LSTM dataset builder ignores them.
        sensors = {
            sensor_name: observation.pv.value
            for sensor_name, observation in transmitter_observations.items()
        }

        snapshot = SimulationSnapshot(
            compressor_id=self.profile.compressor_id,
            operating_state_pct=effective_operating_state,
            sensors=sensors,
            transmitter_observations=transmitter_observations,
            metadata={
                "step": self._step_index,
                "input_domain": "loop_current_ma",
                "current_noise_ma": round(current_noise_ma, 4),
                "hidden_process_state": {
                    "driver": "compressor_load_pct",
                    "operating_state_pct": round(effective_operating_state, 3),
                },
                "control_adjustments": {
                    "operating_state_offset": self._control.operating_state_offset,
                    "temperature_current_bias_ma": self._control.temperature_current_bias_ma,
                    "pressure_current_bias_ma": self._control.pressure_current_bias_ma,
                    "rpm_current_bias_ma": self._control.rpm_current_bias_ma,
                    "current_noise_multiplier": self._control.current_noise_multiplier,
                },
                "display_projection": "engineering_units_derived_from_loop_current",
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
        midpoint = (
            self.profile.compressor_power.minimum + self.profile.compressor_power.maximum
        ) / 2
        return midpoint + (6.0 * self._rng.uniform(-1.0, 1.0))

    def _build_loop_currents(
        self, operating_state_pct: float
    ) -> tuple[dict[str, float], float]:
        state_ratio = (operating_state_pct - self.profile.compressor_power.minimum) / (
            self.profile.compressor_power.maximum - self.profile.compressor_power.minimum
        )
        base_current = LOOP_CURRENT_MIN_MA + (
            (LOOP_CURRENT_MAX_MA - LOOP_CURRENT_MIN_MA) * state_ratio
        )
        # This acquisition jitter is an explicit prototype electrical policy,
        # not a claim about a public benchmark or a physical compressor.
        current_noise_ma = (
            0.0
            if state_ratio in {0.0, 1.0}
            else (0.02 + (0.08 * state_ratio)) * self._control.current_noise_multiplier
        )
        biases = {
            "temperature": self._control.temperature_current_bias_ma,
            "pressure": self._control.pressure_current_bias_ma,
            "rpm": self._control.rpm_current_bias_ma,
        }
        currents = {
            sensor_name: round(
                max(
                    LOOP_CURRENT_MIN_MA,
                    min(
                        LOOP_CURRENT_MAX_MA,
                        base_current
                        + bias
                        + self._rng.uniform(-current_noise_ma, current_noise_ma),
                    ),
                ),
                3,
            )
            for sensor_name, bias in biases.items()
        }
        return currents, current_noise_ma

    def _build_transmitter_observations(
        self,
        loop_currents: dict[str, float],
        *,
        operating_state_pct: float,
    ) -> dict[str, SimulatedTransmitterObservation]:
        observations: dict[str, SimulatedTransmitterObservation] = {}
        for sensor_name, loop_current in loop_currents.items():
            sensor_range = getattr(self.profile, sensor_name)
            percent_range = _percent_from_loop_current(loop_current)
            pv_value = _engineering_value_from_loop_current(loop_current, sensor_range)
            sensor_meta = SENSOR_TRANSMITTER_META[sensor_name]
            observations[sensor_name] = SimulatedTransmitterObservation(
                sensor_name=sensor_name,
                operating_state_pct=round(operating_state_pct, 3),
                pv=TransmitterVariableObservation(
                    value=pv_value,
                    unit=sensor_meta["unit"],
                    unit_code=sensor_meta["unit_code"],
                    description=sensor_meta["pv_description"],
                ),
                sv=_secondary_variable_from_loop_current(sensor_name, loop_current),
                loop_current_ma=loop_current,
                pv_percent_range=percent_range,
                diagnostics=TransmitterDiagnosticsObservation(
                    device_status_hex="0x00",
                    field_device_malfunction=False,
                    loop_current_saturated=(
                        loop_current <= LOOP_CURRENT_MIN_MA
                        or loop_current >= LOOP_CURRENT_MAX_MA
                    ),
                ),
            )
        return observations


def _percent_from_loop_current(loop_current_ma: float) -> float:
    return round(((loop_current_ma - LOOP_CURRENT_MIN_MA) / 16.0) * 100.0, 3)


def _percent_range(value: float, sensor_range: SensorRange) -> float:
    """Map a display endpoint to percent range for conversion verification.

    This compatibility helper is used only to verify the configured endpoint
    mapping; runtime generation remains current-first in `_build_loop_currents`.
    """

    span = sensor_range.maximum - sensor_range.minimum
    if span <= 0:
        raise ValueError("Sensor range maximum must exceed its minimum.")
    return (float(value) - sensor_range.minimum) / span


def _loop_current_from_percent(percent_range: float) -> float:
    """Derive a 4–20 mA verification value from a normalized endpoint."""

    return round(
        LOOP_CURRENT_MIN_MA
        + ((LOOP_CURRENT_MAX_MA - LOOP_CURRENT_MIN_MA) * float(percent_range)),
        3,
    )


def _engineering_value_from_loop_current(
    loop_current_ma: float,
    sensor_range: SensorRange,
) -> float:
    """Derive a display PV after the electrical value has been generated."""

    percent = _percent_from_loop_current(loop_current_ma) / 100.0
    return round(
        sensor_range.minimum + ((sensor_range.maximum - sensor_range.minimum) * percent),
        3,
    )


def _secondary_variable_from_loop_current(
    sensor_name: str, loop_current_ma: float
) -> TransmitterVariableObservation | None:
    """Derive optional HART display metadata after current acquisition.

    Secondary variables remain outside the fingerprint schema; they only keep
    the transmitter envelope compatible with the documented HART view.
    """

    metadata = _SECONDARY_VARIABLE_META.get(sensor_name)
    if metadata is None:
        return None
    description, unit, unit_code = metadata
    percent = _percent_from_loop_current(loop_current_ma) / 100.0
    return TransmitterVariableObservation(
        value=round(20.0 + (20.0 * percent), 3),
        unit=unit,
        unit_code=unit_code,
        description=description,
    )
