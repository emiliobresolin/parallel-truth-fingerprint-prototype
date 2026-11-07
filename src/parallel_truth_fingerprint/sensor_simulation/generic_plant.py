"""Approved generic receiver plant; scientific choices documented in P14 sheet.

This opt-in model never changes legacy generators or global device defaults.
"""
from copy import deepcopy
from dataclasses import replace
from functools import lru_cache
import json
import hashlib
import math
from pathlib import Path
import time

from parallel_truth_fingerprint.config.ranges import DEFAULT_COMPRESSOR_PROFILE, SensorRange
from parallel_truth_fingerprint.sensor_simulation.receiver import ReceiverGasConfiguration, ReceiverGasState, advance_receiver
from parallel_truth_fingerprint.sensor_simulation.simulator import CompressorSimulator, SimulationSnapshot
from parallel_truth_fingerprint.sensor_simulation.current_noise import noise_configuration, noise_rms_ma
from parallel_truth_fingerprint.sensor_simulation.transmitter_observation import (
    SimulatedTransmitterObservation, TransmitterDiagnosticsObservation, TransmitterVariableObservation,
)

COLLECTION_VERSION = 'documented-noise-generic-receiver-hart-v1'
_CONFIG = json.loads(Path(__file__).with_name('generic_plant_config.json').read_text(encoding='utf-8'))
_CONFIG_SHA256 = '048fe17cb2366b1e7aa452455e465bf3e2d83a4224b04230410afa7693a0b818'
if hashlib.sha256(json.dumps(_CONFIG,sort_keys=True,separators=(',',':'),allow_nan=False).encode()).hexdigest() != _CONFIG_SHA256:
    raise ValueError('Packaged generic scientific configuration differs from approved values.')
GENERIC_COMPRESSOR_PROFILE = replace(DEFAULT_COMPRESSOR_PROFILE,
    temperature=SensorRange(0.0, 100.0), pressure=SensorRange(0.0, 10.0), rpm=SensorRange(0.0, 5000.0))


def generic_plant_configuration():
    return deepcopy(_CONFIG)


def validate_generic_plant_configuration(value):
    if json.dumps(value,sort_keys=True,allow_nan=False) != json.dumps(generic_plant_configuration(),sort_keys=True,allow_nan=False):
        raise ValueError('Generic plant configuration differs from approved frozen version.')


def generic_totalizer_configuration():
    from parallel_truth_fingerprint.sensor_simulation.mass_flow import totalizer_configuration
    result = totalizer_configuration()
    result.update(model='fit101-generic-outlet-totalizer1-v1',
        integration='Piecewise-constant receiver outlet mass flow times simulated dt; before analog damping/noise; includes declared unobserved conditioning.')
    return result


def generic_mass_flow_configuration():
    from parallel_truth_fingerprint.sensor_simulation.mass_flow import MassFlowConfiguration
    from dataclasses import asdict
    result = asdict(MassFlowConfiguration())
    result.update(process_time_constant_seconds=0.0, source='receiver_outlet_consumption',
                  generator_model=_CONFIG['model'])
    return result


def generic_device_configurations():
    from parallel_truth_fingerprint.edge_nodes.common.acquisition import EdgeDeviceConfig
    names = ('temperature', 'pressure', 'rpm', 'mass_flow')
    tags = ('TIT-101', 'PIT-101', 'RIT-101', 'FIT-101')
    result = {}
    for i, (sensor, tag) in enumerate(zip(names, tags), 1):
        item = _CONFIG['instruments'][tag]
        result[f'edge-{i}'] = EdgeDeviceConfig(edge_id=f'edge-{i}', gateway_id=f'GW-EDGE-0{i}',
            sensor_name=sensor, tag=tag, long_tag=item.get('long_tag', 'Compressed_Air_Mass_Flow'),
            manufacturer_id=int(item['manufacturer_id_hex'], 16), device_type=int(item['device_type_hex'], 16),
            unit='bar' if sensor == 'pressure' else item['unit'], unit_code={'temperature':32,'pressure':7}.get(sensor),
            sensor_range=SensorRange(float(item['lower_range']), float(item['upper_range'])))
    return result


class GenericReceiverCompressorSimulator(CompressorSimulator):
    """Five-second observation step with separately selected internal resolution."""
    def __init__(self, *, modulated, sample_seconds, seed, internal_substeps,
                 enable_hart_totalizer=True):
        if isinstance(sample_seconds, bool) or sample_seconds != 5.0:
            raise ValueError('Approved generic plant requires five-second acquired intervals.')
        if (isinstance(internal_substeps, bool) or not isinstance(internal_substeps, int)
                or internal_substeps not in (3,6,12,24,48,96,192,384,768)):
            raise ValueError('Unrecognized bounded generic integration resolution.')
        if not isinstance(modulated, bool) or enable_hart_totalizer is not True:
            raise ValueError('Generic mode requires a boolean profile and HART totalization.')
        super().__init__(profile=GENERIC_COMPRESSOR_PROFILE, seed=seed)
        self.modulated = modulated
        self.sample_seconds = float(sample_seconds)
        self.internal_substeps = internal_substeps
        self._ticks = 0
        self.simulation_seconds = 0.0
        self.target_demand = self.base_demand = self.current_demand = 50.0
        self.receiver_state = ReceiverGasState.from_pressure_temperature(
            configuration=ReceiverGasConfiguration(volume_m3=6.0,
                specific_heat_cp_j_kg_k=1000.0, specific_heat_cv_j_kg_k=713.0),
            pressure_abs_pa=801325.0, temperature_k=303.15)
        self._pressure_output_bar = 7.0
        self._flow_output_kg_h = 500.0
        self.totalizer1_kg = 0.0
        self._last_interval_mass_kg = 0.0
        self._qin = self._qout = 500.0/3600
        self._rpm = 2500.0
        self.engineering_state = {}
        self._refresh_engineering()

    def set_demand_target(self, value):
        if isinstance(value, bool) or not isinstance(value, (int,float)) or not math.isfinite(value) or value not in (50.0,75.0):
            raise ValueError('Generic demand targets must be the approved 50/75 percent.')
        self.target_demand = float(value)

    def _refresh_engineering(self):
        state = self.receiver_state
        self.engineering_state = {'temperature':state.temperature_k-273.15,
            'pressure':state.gauge_pressure_pa(ambient_pressure_pa=101325.0)/100000,
            'rpm':self._rpm, 'mass_flow':self._qout*3600}

    def physical_state(self):
        return {'receiver':self.receiver_state.to_dict(), 'simulation_seconds':self.simulation_seconds,
            'ticks':self._ticks, 'base_demand_pct':self.base_demand,
            'actual_demand_pct':self.current_demand, 'demand_target_pct':self.target_demand,
            'pressure_output_bar':self._pressure_output_bar, 'flow_output_kg_h':self._flow_output_kg_h,
            'totalizer1_kg':self.totalizer1_kg, 'qin_kg_s':self._qin, 'qout_kg_s':self._qout,
            'rpm':self._rpm, 'phase_seconds':self.simulation_seconds%120.0}

    def _advance_physics(self):
        dt = self.sample_seconds/self.internal_substeps
        initial_total = self.totalizer1_kg
        for _ in range(self.internal_substeps):
            delta = 25.0*dt/60.0
            self.base_demand += max(-delta, min(delta, self.target_demand-self.base_demand))
            wave = math.sin(2*math.pi*self.simulation_seconds/120.0) if self.modulated else 0.0
            self.current_demand = self.base_demand+5.0*wave
            pressure = self.receiver_state.gauge_pressure_pa(ambient_pressure_pa=101325.0)
            capacity = max(.1, min(1.0, (750000.0-pressure)/100000.0))
            self._rpm = 5000.0*capacity
            self._qin = (1000.0/3600.0)*capacity
            self._qout = (1000.0/3600.0)*self.current_demand/100.0
            self.receiver_state = advance_receiver(self.receiver_state, duration_seconds=dt,
                inlet_mass_flow_kg_s=self._qin, outlet_mass_flow_kg_s=self._qout,
                inlet_temperature_k=303.15, wall_heat_flow_w=0.0)
            pressure_bar = self.receiver_state.gauge_pressure_pa(ambient_pressure_pa=101325.0)/100000.0
            self._pressure_output_bar += -math.expm1(-dt/2.0)*(pressure_bar-self._pressure_output_bar)
            self._flow_output_kg_h += -math.expm1(-dt/1.0)*(self._qout*3600-self._flow_output_kg_h)
            self.totalizer1_kg += self._qout*dt
            self._ticks += 1
            self.simulation_seconds = self._ticks*dt
        self._last_interval_mass_kg = self.totalizer1_kg-initial_total
        self._refresh_engineering()

    def noiseless_currents(self):
        values = dict(self.engineering_state, pressure=self._pressure_output_bar, mass_flow=self._flow_output_kg_h)
        ranges = {'temperature':(0,100), 'pressure':(0,10), 'rpm':(0,5000), 'mass_flow':(0,1000)}
        result = {}
        for name, (low,high) in ranges.items():
            if not math.isfinite(values[name]) or not low <= values[name] <= high:
                raise ValueError(f'Generic process exceeds approved nominal {name} range.')
            result[name] = 4+16*(values[name]-low)/(high-low)
        return result

    def step(self, *, operating_state_pct=None, compressor_power=None):
        if (self._control.operating_state_offset != 0 or any(getattr(self._control,n)!=0
                for n in ('temperature_current_bias_ma','pressure_current_bias_ma','rpm_current_bias_ma'))):
            raise ValueError('Generic model does not support undeclared physical/current biases.')
        self._advance_physics()
        observations = {}
        meta = {'temperature':('degC',32,'Receiver_Air_Temperature'),
                'pressure':('bar',7,'Receiver_Gauge_Pressure'),
                'rpm':('rpm',None,'Shaft_Speed'), 'mass_flow':('kg/h',None,'Compressed_Air_Mass_Flow')}
        for name,value in self.noiseless_currents().items():
            current = max(4.0,min(20.0,value+self._current_noise.sample_ma(name,multiplier=self._control.current_noise_multiplier)))
            unit, code, description = meta[name]
            span = {'temperature':100,'pressure':10,'rpm':5000,'mass_flow':1000}[name]
            observations[name] = SimulatedTransmitterObservation(sensor_name=name,
                operating_state_pct=self.current_demand,
                pv=TransmitterVariableObservation(round((current-4)/16*span,3),unit,code,description),
                sv=TransmitterVariableObservation(self.totalizer1_kg,'kg',None,'Totalizer_1_Mass') if name=='mass_flow' else None,
                loop_current_ma=current,pv_percent_range=round((current-4)/16*100,3),
                diagnostics=TransmitterDiagnosticsObservation('0x00',False,not 4<current<20))
        snapshot = SimulationSnapshot(compressor_id=self.profile.compressor_id, operating_state_pct=self.current_demand,
            sensors={n:o.pv.value for n,o in observations.items()},transmitter_observations=observations,
            metadata={'step':self._step_index,'input_domain':'loop_current_ma',
                'operational_model':_CONFIG['model'],'generic_plant_configuration':generic_plant_configuration(),
                'selected_substeps_per_round':self.internal_substeps,'modulated':self.modulated,
                'current_noise_configuration':noise_configuration(),'current_noise_ma':noise_rms_ma(self._control.current_noise_multiplier),
                'current_noise_statistic':'pre-saturation RMS, mA',
                'control_adjustments':vars(self._control).copy(),
                'simulation_seconds':self.simulation_seconds,'simulation_timestep_seconds':self.sample_seconds,
                'engineering_state':dict(self.engineering_state),'receiver_state':self.physical_state(),
                'actual_demand_pct':self.current_demand,'base_demand_pct':self.base_demand,'demand_target_pct':self.target_demand,
                'device_cold_start_by_sensor':{name:False for name in observations},
                'hidden_process_state':{'driver':'air_consumption_pct','operating_state_pct':self.current_demand},
                'mass_flow_configuration':generic_mass_flow_configuration(),
                'hart_totalizer_configuration':generic_totalizer_configuration(),'hart_totalizer1_kg':self.totalizer1_kg,
                'interval_outlet_mass_kg':self._last_interval_mass_kg,
                'display_projection':'engineering_units_derived_from_loop_current'})
        self._step_index += 1
        return snapshot

    def condition_to_regime(self):
        """Advance unobserved model time, conserving counter and demand phase."""
        before = self.physical_state()
        start = time.monotonic()
        previous = None
        passed = 0
        differences = None
        for cycle in range(1,201):
            trajectory = []
            for _ in range(24):
                self._advance_physics()
                trajectory.append((self.receiver_state.mass_kg,self.receiver_state.internal_energy_j,
                                   self._pressure_output_bar,self._flow_output_kg_h,self.base_demand))
            if previous is not None:
                differences = [max(abs(a[j]-b[j])/max(abs(b[j]),1.0) for a,b in zip(trajectory,previous)) for j in range(5)]
                passed = passed+1 if max(differences)<=1e-8 and self.base_demand==self.target_demand else 0
                if passed>=2:
                    return {'kind':'generic-regime-conditioning-v1','before':before,'after':self.physical_state(),
                        'cycles':cycle,'window_seconds':120.0,'simulated_duration_seconds':cycle*120.0,
                        'wall_duration_seconds':time.monotonic()-start,'relative_differences':differences,
                        'converged':True,'acquired_observations':0,'noise_draws':0}
            previous = trajectory
        raise ValueError('Generic receiver failed bounded regime conditioning.')


def _normal_benchmark(substeps, modulated):
    simulator = GenericReceiverCompressorSimulator(modulated=modulated,sample_seconds=5,seed=0,internal_substeps=substeps)
    result = []
    # Both transition directions and steady demand, with the same fixed recipe.
    for target in (50,75,50,75,50):
        simulator.set_demand_target(target)
        for _ in range(24):
            simulator._advance_physics()
            result.append((simulator.noiseless_currents(),simulator._last_interval_mass_kg))
    return result


@lru_cache(maxsize=1)
def _resolution_report_json():
    started = time.monotonic()
    coarse = {m:_normal_benchmark(3,m) for m in (False,True)}
    attempts = []
    for fine in (6,12,24,48,96,192,384,768):
        finer = {m:_normal_benchmark(fine,m) for m in (False,True)}
        maxima = {}
        mass_error = 0.0
        for m in (False,True):
            for (a,ma),(b,mb) in zip(coarse[m],finer[m]):
                for n in a:
                    maxima[n] = max(maxima.get(n,0.0),abs(a[n]-b[n]))
                mass_error = max(mass_error,16*abs(ma-mb)/((1000/3600)*5))
        passed = max(*maxima.values(),mass_error)<=.000782
        attempts.append({'coarse_substeps_per_round':fine//2,'fine_substeps_per_round':fine,
                         'max_current_difference_ma':maxima,'max_totalizer_equivalent_difference_ma':mass_error,'passed':passed})
        if passed:
            return json.dumps({'recipe':'normal-only-five-segments-both-profiles-v1','acquisition_seconds':5.0,
                'selected_substeps_per_round':fine,'numerical_budget_ma':.000782,
                'benchmark_rounds_per_profile':120,'attempts':attempts,
                'wall_duration_seconds':time.monotonic()-started})
        coarse = finer
    raise ValueError('Generic numerical resolution failed the approved bounded budget.')


def select_numerical_resolution():
    return json.loads(_resolution_report_json())
