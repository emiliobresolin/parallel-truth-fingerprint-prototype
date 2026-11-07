"""Explicit toy operating dynamics, opt-in for the paired replay experiment.

Not a calibrated compressor model. Numerical response parameters are declared
emulation assumptions; the legacy current-first simulator is unchanged.
"""
from dataclasses import dataclass
import math

from parallel_truth_fingerprint.sensor_simulation.simulator import CompressorSimulator
from parallel_truth_fingerprint.sensor_simulation.current_noise import noise_rms_ma


@dataclass(frozen=True)
class OperationalAssumptions:
    low_demand_pct: float = 50.0
    high_demand_pct: float = 75.0
    modulation_amplitude_pct: float = 5.0
    modulation_period_seconds: float = 120.0
    ramp_seconds: float = 60.0
    rpm_time_constant_seconds: float = 10.0
    pressure_time_constant_seconds: float = 20.0
    temperature_time_constant_seconds: float = 90.0
    pressure_reference_bar: float = 7.0
    pressure_capacity_error_gain_bar: float = 1.0
    temperature_intercept_c: float = 55.0
    temperature_demand_gain_c: float = 30.0


class OperationalCompressorSimulator(CompressorSimulator):
    def __init__(self, *, modulated, sample_seconds, seed, assumptions=None):
        super().__init__(seed=seed)
        if not math.isfinite(sample_seconds) or sample_seconds <= 0:
            raise ValueError('Positive simulation timestep required.')
        self.assumptions = assumptions or OperationalAssumptions()
        self.modulated = modulated
        self.sample_seconds = sample_seconds
        self.simulation_seconds = 0.0
        self.target_demand = self.assumptions.low_demand_pct
        self.base_demand = self.target_demand
        self.current_demand = self.base_demand
        ratio = self.current_demand / 100
        self.engineering_state = {
            'rpm': self.profile.rpm.minimum + ratio * (self.profile.rpm.maximum - self.profile.rpm.minimum),
            'pressure': self.assumptions.pressure_reference_bar,
            'temperature': self.assumptions.temperature_intercept_c + self.assumptions.temperature_demand_gain_c * ratio,
        }

    def set_demand_target(self, value):
        if not math.isfinite(value) or not 0 <= value <= 100:
            raise ValueError('Demand outside 0..100%.')
        self.target_demand = float(value)

    def step(self, *, compressor_power=None, operating_state_pct=None):
        # This opt-in simulator is driven only by set_demand_target, not the
        # legacy fixed DEMO_POWER argument passed by the acquisition helper.
        a = self.assumptions
        delta = (a.high_demand_pct - a.low_demand_pct) * self.sample_seconds / a.ramp_seconds
        self.base_demand += max(-delta, min(delta, self.target_demand - self.base_demand))
        wave = math.sin(2 * math.pi * self.simulation_seconds / a.modulation_period_seconds) if self.modulated else 0.0
        self.current_demand = self.base_demand + a.modulation_amplitude_pct * wave
        snapshot = super().step(operating_state_pct=self.current_demand)
        snapshot.metadata.update(
            operational_model='uncalibrated-first-order-emulation-v1', modulated=self.modulated,
            simulation_seconds=self.simulation_seconds, simulation_timestep_seconds=self.sample_seconds,
            demand_target_pct=self.target_demand, base_demand_pct=self.base_demand,
            actual_demand_pct=self.current_demand, engineering_state=dict(self.engineering_state),
        )
        self.simulation_seconds += self.sample_seconds
        return snapshot

    def _build_loop_currents(self, operating_state_pct):
        a, state, dt = self.assumptions, self.engineering_state, self.sample_seconds
        demand = operating_state_pct / 100
        rpm_target = self.profile.rpm.minimum + demand * (self.profile.rpm.maximum - self.profile.rpm.minimum)
        state['rpm'] += (1 - math.exp(-dt / a.rpm_time_constant_seconds)) * (rpm_target - state['rpm'])
        delivered = (state['rpm'] - self.profile.rpm.minimum) / (self.profile.rpm.maximum - self.profile.rpm.minimum)
        pressure_target = a.pressure_reference_bar + a.pressure_capacity_error_gain_bar * (delivered - demand)
        temperature_target = a.temperature_intercept_c + a.temperature_demand_gain_c * demand
        for name, target, tau in [('pressure', pressure_target, a.pressure_time_constant_seconds),
                                  ('temperature', temperature_target, a.temperature_time_constant_seconds)]:
            state[name] += (1 - math.exp(-dt / tau)) * (target - state[name])
        noise = noise_rms_ma(self._control.current_noise_multiplier)
        currents = {}
        for name in ('temperature', 'pressure', 'rpm'):
            limits = getattr(self.profile, name)
            state[name] = max(limits.minimum, min(limits.maximum, state[name]))
            value = 4 + 16 * (state[name] - limits.minimum) / (limits.maximum - limits.minimum)
            currents[name] = max(4, min(20, value + self._current_noise.sample_ma(
                name, multiplier=self._control.current_noise_multiplier)))
        return currents, noise
