"""Opt-in t-mass F 300 current channel; plant dynamics are explicit assumptions."""
from dataclasses import dataclass, asdict
import math

from parallel_truth_fingerprint.sensor_simulation.operational_profiles import OperationalCompressorSimulator
from parallel_truth_fingerprint.sensor_simulation.transmitter_observation import (
    SimulatedTransmitterObservation, TransmitterVariableObservation, TransmitterDiagnosticsObservation,
)


@dataclass(frozen=True)
class MassFlowConfiguration:
    instrument: str = 'Endress+Hauser Proline t-mass F 300 HART'
    tag: str = 'FIT-101'
    gas: str = 'air'
    nominal_diameter_mm: int = 65
    sensor_version: str = 'SA unidirectional; without flow conditioners'
    lower_range_kg_h: float = 0.0
    upper_range_kg_h: float = 1000.0
    nominal_capacity_kg_h: float = 1000.0
    process_time_constant_seconds: float = 5.0
    output_damping_seconds: float = 1.0
    manual: str = 'BA01992D/06/EN/03.23-00, 2023-07-28'
    manual_url: str = 'https://bdih-download.endress.com/file/9bf358f8845b222e0c1c5d9b8b0573bf/BA01992DEN_0323-00.pdf'


@dataclass(frozen=True)
class HartTotalizerConfiguration:
    model: str = 'fit101-hart-totalizer1-v1'
    instrument: str = 'Endress+Hauser Proline t-mass F 300 HART'
    device_variable_code: int = 6
    dynamic_variable: str = 'SV'
    description: str = 'Totalizer_1_Mass'
    unit: str = 'kg'
    process_variable: str = 'Mass flow'
    mode: str = 'Forward flow total'
    initial_mass_kg: float = 0.0
    reset_policy: str = 'No reset during acquisition profile; reject unexplained decrease.'
    integration: str = 'Piecewise-constant internal measured mass flow times simulated dt/3600; before analog output damping/noise.'
    source_binding: str = 'SV identity/unit/value included in source_event_id; opaque digest compared by current-consensus-v2.'
    preprocessing: str = 'Within-episode differences, fixed capacity*interval/3600 normalization; omit first two records uniformly.'


def totalizer_configuration():
    return asdict(HartTotalizerConfiguration())


def validate_totalizer_configuration(value):
    if value != totalizer_configuration():
        raise ValueError('Frozen HART totalizer configuration differs from implementation.')


class MassFlowCompressorSimulator(OperationalCompressorSimulator):
    """Mass flow follows delivered compressor capacity with process and output lag."""

    def __init__(self, *, enable_hart_totalizer=False, **kwargs):
        super().__init__(**kwargs)
        self.enable_hart_totalizer = enable_hart_totalizer
        self.totalizer1_kg = 0.0
        self.flow_configuration = MassFlowConfiguration()
        self._flow = self.flow_configuration.nominal_capacity_kg_h*self.current_demand/100
        self._flow_output = self._flow
        self.engineering_state['mass_flow'] = self._flow

    def step(self, **kwargs):
        frame = super().step(**kwargs)
        c, dt = self.flow_configuration, self.sample_seconds
        delivered = (self.engineering_state['rpm']-self.profile.rpm.minimum)/(self.profile.rpm.maximum-self.profile.rpm.minimum)
        target = c.nominal_capacity_kg_h*delivered
        self._flow += (1-math.exp(-dt/c.process_time_constant_seconds))*(target-self._flow)
        if self.enable_hart_totalizer:
            self.totalizer1_kg += max(self._flow, 0.0)*dt/3600.0
        self._flow_output += (1-math.exp(-dt/c.output_damping_seconds))*(self._flow-self._flow_output)
        span = c.upper_range_kg_h-c.lower_range_kg_h
        current = max(4,min(20,4+16*(self._flow_output-c.lower_range_kg_h)/span+
            self._current_noise.sample_ma('mass_flow', multiplier=self._control.current_noise_multiplier)))
        pv = round(c.lower_range_kg_h+(current-4)/16*span,3)
        observation = SimulatedTransmitterObservation(sensor_name='mass_flow', operating_state_pct=self.current_demand,
            pv=TransmitterVariableObservation(pv,'kg/h',None,'Compressed_Air_Mass_Flow'),
            sv=TransmitterVariableObservation(self.totalizer1_kg,'kg',None,'Totalizer_1_Mass') if self.enable_hart_totalizer else None,
            loop_current_ma=current, pv_percent_range=round((current-4)/16*100,3),
            diagnostics=TransmitterDiagnosticsObservation('0x00',False,current<=4 or current>=20))
        frame.transmitter_observations['mass_flow'] = observation
        frame.sensors['mass_flow'] = pv
        self.engineering_state['mass_flow'] = self._flow
        frame.metadata['engineering_state'] = dict(self.engineering_state)
        frame.metadata['mass_flow_configuration'] = asdict(c)
        if self.enable_hart_totalizer:
            frame.metadata['hart_totalizer_configuration'] = totalizer_configuration()
            frame.metadata['hart_totalizer1_kg'] = self.totalizer1_kg
        frame.metadata['mass_flow_assumptions'] = 'Capacity, process lag and damping selection are prototype parameters; electrical noise uses the separately documented reference profile.'
        return frame
