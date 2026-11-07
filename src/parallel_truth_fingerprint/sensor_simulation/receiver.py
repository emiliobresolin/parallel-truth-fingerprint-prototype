"""Explicit, inactive ideal-gas receiver mass/energy model in SI units.

Sources and integration status: ``docs/receiver-gas-model.md``.  This pure
component is not selected by any acquisition service or experiment launcher.
There are no plant defaults, transmitter limits or fitted time constants.
"""

from __future__ import annotations

from dataclasses import dataclass
import math
from numbers import Real


def _finite_real(name: str, value: object, *, positive: bool = False,
                 nonnegative: bool = False) -> float:
    if isinstance(value, bool) or not isinstance(value, Real):
        raise ValueError(f"{name} must be a finite real number.")
    try:
        result = float(value)
    except (OverflowError, ValueError) as exc:
        raise ValueError(f"{name} must be a finite real number.") from exc
    if not math.isfinite(result):
        raise ValueError(f"{name} must be finite.")
    if positive and result <= 0:
        raise ValueError(f"{name} must be positive.")
    if nonnegative and result < 0:
        raise ValueError(f"{name} must be nonnegative.")
    return result


@dataclass(frozen=True)
class ReceiverGasConfiguration:
    """Required volume and constant gas properties; no selected plant profile."""

    volume_m3: float
    specific_heat_cp_j_kg_k: float
    specific_heat_cv_j_kg_k: float

    def __post_init__(self) -> None:
        for name in ("volume_m3", "specific_heat_cp_j_kg_k", "specific_heat_cv_j_kg_k"):
            object.__setattr__(self, name, _finite_real(name, getattr(self, name), positive=True))
        if self.specific_heat_cp_j_kg_k <= self.specific_heat_cv_j_kg_k:
            raise ValueError("Specific heats must satisfy cp > cv and R = cp - cv > 0.")
        _finite_real("cp/cv", self.specific_heat_cp_j_kg_k / self.specific_heat_cv_j_kg_k,
                     positive=True)

    @property
    def gas_constant_j_kg_k(self) -> float:
        return self.specific_heat_cp_j_kg_k - self.specific_heat_cv_j_kg_k

    def to_dict(self) -> dict[str, object]:
        return {
            "model": "well-mixed-ideal-gas-receiver-v1",
            "temperature_measurement_point": "receiver_gas",
            "volume_m3": self.volume_m3,
            "specific_heat_cp_j_kg_k": self.specific_heat_cp_j_kg_k,
            "specific_heat_cv_j_kg_k": self.specific_heat_cv_j_kg_k,
            "gas_constant_j_kg_k": self.gas_constant_j_kg_k,
            "assumptions": [
                "Rigid fixed volume; perfectly mixed ideal gas.",
                "Constant specific heats, cp > cv, R = cp - cv.",
                "Forward nonnegative mass flows; negligible kinetic/potential energy.",
                "Boundary inputs constant during each step; wall heat explicitly supplied.",
                "Gas temperature is distinct from receiver wall and compressor casing.",
            ],
            "numerical_method": "Analytic constant-boundary mass and energy balance.",
        }


@dataclass(frozen=True)
class ReceiverGasState:
    """Immutable conserved mass and internal energy, with derived observables."""

    configuration: ReceiverGasConfiguration
    mass_kg: float
    internal_energy_j: float

    def __post_init__(self) -> None:
        if not isinstance(self.configuration, ReceiverGasConfiguration):
            raise ValueError("configuration must be a ReceiverGasConfiguration.")
        for name in ("mass_kg", "internal_energy_j"):
            object.__setattr__(self, name, _finite_real(name, getattr(self, name), positive=True))
        # Ensure every promised observable is representable before exposing state.
        _finite_real("temperature_k", self.temperature_k, positive=True)
        _finite_real("pressure_abs_pa", self.pressure_abs_pa, positive=True)

    @classmethod
    def from_pressure_temperature(
        cls, *, configuration: ReceiverGasConfiguration,
        pressure_abs_pa: float, temperature_k: float,
    ) -> ReceiverGasState:
        if not isinstance(configuration, ReceiverGasConfiguration):
            raise ValueError("configuration must be a ReceiverGasConfiguration.")
        pressure = _finite_real("pressure_abs_pa", pressure_abs_pa, positive=True)
        temperature = _finite_real("temperature_k", temperature_k, positive=True)
        try:
            mass = pressure * configuration.volume_m3 / (
                configuration.gas_constant_j_kg_k * temperature)
            energy = mass * configuration.specific_heat_cv_j_kg_k * temperature
            return cls(configuration=configuration, mass_kg=mass, internal_energy_j=energy)
        except (OverflowError, ZeroDivisionError) as exc:
            raise ValueError("Initial receiver state exceeds finite numerical precision.") from exc

    @property
    def temperature_k(self) -> float:
        return (self.internal_energy_j / self.mass_kg
                / self.configuration.specific_heat_cv_j_kg_k)

    @property
    def pressure_abs_pa(self) -> float:
        return (self.mass_kg * self.configuration.gas_constant_j_kg_k
                * self.temperature_k / self.configuration.volume_m3)

    def gauge_pressure_pa(self, *, ambient_pressure_pa: float) -> float:
        ambient = _finite_real("ambient_pressure_pa", ambient_pressure_pa, positive=True)
        return self.pressure_abs_pa - ambient

    def to_dict(self) -> dict[str, object]:
        return {
            "configuration": self.configuration.to_dict(),
            "mass_kg": self.mass_kg,
            "internal_energy_j": self.internal_energy_j,
            "temperature_k": self.temperature_k,
            "pressure_abs_pa": self.pressure_abs_pa,
        }


def advance_receiver(
    state: ReceiverGasState, *, duration_seconds: float,
    inlet_mass_flow_kg_s: float, outlet_mass_flow_kg_s: float,
    inlet_temperature_k: float, wall_heat_flow_w: float,
) -> ReceiverGasState:
    """Return the exact constant-boundary evolution, without mutating ``state``.

    The balances are dm/dt=qin-qout and
    dU/dt=qin*cp*Tin-qout*cp*T+Q, with U=m*cv*T.  Q is positive
    into the gas; supplying zero is an explicit adiabatic boundary choice.

    Defining c=qin+(R/cv)*qout and H=qin*cp*Tin+Q gives
    dT/dt=(H/cv-c*T)/m.  The analytic solution uses the exact integral
    L=integral(dt/m) and expm1/log1p to retain small-step accuracy.
    Constant heat may be negative, but a step that exhausts mass or reaches
    nonpositive energy/temperature is rejected.  Arithmetic outside finite
    floating-point representability is rejected rather than clipped.
    """
    if not isinstance(state, ReceiverGasState):
        raise ValueError("state must be a ReceiverGasState.")
    dt = _finite_real("duration_seconds", duration_seconds, positive=True)
    qin = _finite_real("inlet_mass_flow_kg_s", inlet_mass_flow_kg_s, nonnegative=True)
    qout = _finite_real("outlet_mass_flow_kg_s", outlet_mass_flow_kg_s, nonnegative=True)
    tin = _finite_real("inlet_temperature_k", inlet_temperature_k, positive=True)
    heat = _finite_real("wall_heat_flow_w", wall_heat_flow_w)
    gas = state.configuration

    try:
        mass_change = _finite_real("mass change", (qin - qout) * dt)
        mass = _finite_real("remaining mass", math.fsum((state.mass_kg, mass_change)),
                            positive=True)
        x = _finite_real("relative mass change", mass_change / state.mass_kg)
        if x <= -1:
            raise ValueError("Step is too close to mass exhaustion for finite precision.")
        log_ratio_over_x = math.log1p(x) / x if x else 1.0
        integral_inverse_mass = _finite_real(
            "integral of inverse mass", (dt / state.mass_kg) * log_ratio_over_x,
            positive=True)
        c = _finite_real("thermal mass-flow coefficient",
                         qin + (gas.gas_constant_j_kg_k / gas.specific_heat_cv_j_kg_k) * qout,
                         nonnegative=True)
        exponent = _finite_real("thermal exponent", c * integral_inverse_mass,
                                nonnegative=True)
        decay = math.exp(-exponent)
        phi = -math.expm1(-exponent) / exponent if exponent else 1.0
        inlet_heat_capacity_flow = qin * gas.specific_heat_cp_j_kg_k
        inlet_enthalpy_flow = inlet_heat_capacity_flow * tin
        if qin > 0 and (inlet_heat_capacity_flow == 0 or inlet_enthalpy_flow == 0):
            raise ValueError("Incoming enthalpy underflows finite numerical precision.")
        enthalpy_heat = _finite_real(
            "incoming enthalpy and wall heat",
            math.fsum((inlet_enthalpy_flow, heat)))
        forcing = _finite_real(
            "thermal forcing",
            (enthalpy_heat / gas.specific_heat_cv_j_kg_k)
            * integral_inverse_mass * phi)
        temperature = _finite_real(
            "resulting temperature", math.fsum((state.temperature_k * decay, forcing)),
            positive=True)
        energy = _finite_real("resulting internal energy",
                              mass * gas.specific_heat_cv_j_kg_k * temperature,
                              positive=True)
        return ReceiverGasState(configuration=gas, mass_kg=mass, internal_energy_j=energy)
    except (OverflowError, ZeroDivisionError) as exc:
        raise ValueError("Receiver evolution exceeds finite numerical precision.") from exc
