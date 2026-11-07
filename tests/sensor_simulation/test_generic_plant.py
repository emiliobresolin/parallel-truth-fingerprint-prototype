"""Approved reference model physics, instrumental projection and qualification."""
import copy
import json
import math
from pathlib import Path
import unittest

from parallel_truth_fingerprint.sensor_simulation.generic_plant import (
    GenericReceiverCompressorSimulator, generic_plant_configuration,
    validate_generic_plant_configuration,generic_device_configurations,
    generic_totalizer_configuration,select_numerical_resolution,
)
from parallel_truth_fingerprint.sensor_simulation.current_noise import SampledCurrentNoise
from parallel_truth_fingerprint.edge_nodes.common.acquisition import EDGE_DEVICE_CONFIGS,EdgeAcquisitionService


class GenericPlantTests(unittest.TestCase):
    def simulator(self,**kwargs):
        return GenericReceiverCompressorSimulator(modulated=False,sample_seconds=5,seed=808,internal_substeps=384,**kwargs)

    def test_configuration_matches_reviewed_values_and_detaches(self):
        reviewed=json.loads((Path(__file__).resolve().parents[2]/'testdata/generic-plant/reviewed-configuration.json').read_text(encoding='utf-8'))
        config=generic_plant_configuration()
        for key in ('plant','instruments','invariants'):
            self.assertEqual(config[key],reviewed[key])
        config['plant']['receiver']['volume_m3']=3
        self.assertEqual(generic_plant_configuration()['plant']['receiver']['volume_m3'],6)
        with self.assertRaises(ValueError): validate_generic_plant_configuration(config)
        changed=generic_plant_configuration()
        changed['plant']['production']['volumetric_efficiency']=True
        with self.assertRaises(ValueError): validate_generic_plant_configuration(changed)

    def test_analytic_equilibrium_and_currents(self):
        s=self.simulator();s.set_control_hook(current_noise_multiplier=0)
        initial=s.receiver_state
        frame=s.step()
        for name,expected in {'temperature':8.8,'pressure':15.2,'rpm':12.,'mass_flow':12.}.items():
            self.assertAlmostEqual(frame.transmitter_observations[name].loop_current_ma,expected,places=10)
        self.assertAlmostEqual(s.receiver_state.mass_kg,initial.mass_kg,places=10)
        self.assertAlmostEqual(s.totalizer1_kg,500/3600*5,places=12)
        self.assertIsNone(frame.transmitter_observations['temperature'].sv)
        self.assertIsNone(frame.transmitter_observations['pressure'].sv)
        self.assertEqual(frame.metadata['device_cold_start_by_sensor'],{n:False for n in frame.sensors})

    def test_outlet_totalizer_independent_of_production_during_ramp(self):
        s=self.simulator();s.set_control_hook(current_noise_multiplier=0);s.set_demand_target(75)
        initial=s.receiver_state.mass_kg; frame=s.step()
        n=s.internal_substeps;dt=5/n
        expected=sum((1000/3600)*(50+(25/60)*dt*i)/100*dt for i in range(1,n+1))
        self.assertAlmostEqual(s.totalizer1_kg,expected,places=12)
        self.assertAlmostEqual(frame.transmitter_observations['mass_flow'].sv.value,expected,places=12)
        self.assertNotAlmostEqual(s.receiver_state.mass_kg,initial,places=5)
        self.assertNotEqual(s.physical_state()['qin_kg_s'],s.physical_state()['qout_kg_s'])

    def test_noise_does_not_modify_physical_mass_or_energy(self):
        a,b=self.simulator(),self.simulator();b.set_control_hook(current_noise_multiplier=0)
        for target in (75,75,50,50):
            a.set_demand_target(target);b.set_demand_target(target)
            a.step();b.step()
            self.assertEqual(a.physical_state(),b.physical_state())

    def test_new_device_profiles_preserve_old_globals(self):
        before=copy.deepcopy(EDGE_DEVICE_CONFIGS); devices=generic_device_configurations()
        self.assertEqual(devices['edge-1'].long_tag,'Temperature_Receiver_Air')
        self.assertEqual(devices['edge-2'].sensor_range.maximum,10)
        self.assertEqual(devices['edge-3'].sensor_range.minimum,0)
        self.assertEqual(devices['edge-3'].manufacturer_id,0x006118)
        self.assertEqual(devices['edge-3'].device_type,0xE43C)
        self.assertEqual(EDGE_DEVICE_CONFIGS,before)
        frame=self.simulator().step()
        for d in devices.values():
            payload=EdgeAcquisitionService(d).acquire(snapshot=frame)
            self.assertFalse(payload.diagnostics.cold_start)
            self.assertEqual(payload.device_info.manufacturer_id,d.manufacturer_id)
            self.assertEqual(payload.process_data.loop_current_ma,frame.transmitter_observations[d.sensor_name].loop_current_ma)

    def test_cold_start_hook_requires_actual_sensor_boolean_flags(self):
        d=generic_device_configurations()['edge-1'];s=self.simulator();frame=s.step()
        for flags in ({'temperature':False},{n:0 for n in frame.sensors}):
            frame.metadata['device_cold_start_by_sensor']=flags
            with self.assertRaises(ValueError): EdgeAcquisitionService(d).acquire(snapshot=frame)

    def test_scada_uses_selected_instrument_scales_and_keeps_currents(self):
        from datetime import datetime, timedelta, timezone
        from parallel_truth_fingerprint.contracts.consensused_valid_state import ConsensusedValidState
        from parallel_truth_fingerprint.contracts.round_identity import RoundIdentity
        from parallel_truth_fingerprint.evidence.replay_evaluation import SequenceReplayScada
        from parallel_truth_fingerprint.scada.opcua_service import FakeOpcUaScadaService
        stamp=datetime(2026,11,2,tzinfo=timezone.utc)
        currents={'temperature':8.8,'pressure':15.2,'rpm':12.0,'mass_flow':12.0}
        state=ConsensusedValidState(round_identity=RoundIdentity('generic-round',stamp-timedelta(seconds=5),stamp),
            source_edges=('edge-1','edge-2','edge-3','edge-4'),sensor_values=currents)
        ranges={d.sensor_name:d.sensor_range for d in generic_device_configurations().values()}
        service=SequenceReplayScada(sensor_names=tuple(currents),sensor_ranges=ranges)
        ranges['temperature']=type(ranges['temperature'])(0,200)
        projected=service.project_state(state)
        for name,expected in {'temperature':30,'pressure':7,'rpm':2500,'mass_flow':500}.items():
            self.assertAlmostEqual(projected.sensor_values[name].value,expected,places=10)
            self.assertEqual(projected.behavioral_sensor_values[name].loop_current_ma,currents[name])
        legacy=FakeOpcUaScadaService(sensor_names=tuple(currents)).project_state(state)
        self.assertAlmostEqual(legacy.sensor_values['temperature'].value,62.1)
        service.set_sensor_override('temperature',mode='offset',offset=1)
        changed=service.project_state(state)
        self.assertAlmostEqual(changed.sensor_values['temperature'].value,36.25)
        self.assertEqual(changed.behavioral_sensor_values['temperature'].loop_current_ma,9.8)

    def test_scada_rejects_incomplete_nonfinite_or_reversed_ranges(self):
        from parallel_truth_fingerprint.scada.opcua_service import FakeOpcUaScadaService
        from parallel_truth_fingerprint.config.ranges import SensorRange
        ranges={d.sensor_name:d.sensor_range for d in generic_device_configurations().values()}
        for invalid in ({},dict(ranges,temperature=SensorRange(100,0)),
                        dict(ranges,temperature=SensorRange(0,float('nan'))),
                        dict(ranges,temperature=SensorRange(False,100))):
            with self.subTest(invalid=invalid),self.assertRaises(ValueError):
                FakeOpcUaScadaService(sensor_names=tuple(ranges),sensor_ranges=invalid)

    def test_conditioning_is_explicit_and_keeps_counter_phase_noise(self):
        s=self.simulator();receipt=s.condition_to_regime()
        self.assertEqual(receipt['cycles'],3)
        self.assertEqual(receipt['simulated_duration_seconds'],360)
        self.assertEqual(s.simulation_seconds,360)
        self.assertAlmostEqual(s.totalizer1_kg,50,places=9)
        self.assertEqual(receipt['noise_draws'],0)
        self.assertEqual(receipt['after']['phase_seconds'],receipt['before']['phase_seconds'])
        frame=s.step()
        expected=SampledCurrentNoise(808)
        for name,value in s.noiseless_currents().items():
            self.assertAlmostEqual(frame.transmitter_observations[name].loop_current_ma-value,expected.sample_ma(name),places=13)

    def test_modulated_conditioning_converges_entire_hidden_trajectory(self):
        s=GenericReceiverCompressorSimulator(modulated=True,sample_seconds=5,seed=808,internal_substeps=384)
        receipt=s.condition_to_regime()
        self.assertLess(receipt['cycles'],200)
        self.assertLessEqual(max(receipt['relative_differences']),1e-8)
        self.assertEqual(receipt['after']['phase_seconds'],0)
        self.assertGreater(receipt['after']['totalizer1_kg'],0)

    def test_normal_only_refinement_freezes_finer_accepted_resolution(self):
        report=select_numerical_resolution()
        self.assertEqual(report['selected_substeps_per_round'],384)
        self.assertEqual(report['recipe'],'normal-only-five-segments-both-profiles-v1')
        self.assertTrue(report['attempts'][-1]['passed'])
        self.assertTrue(all(not r['passed'] for r in report['attempts'][:-1]))
        self.assertLessEqual(max(report['attempts'][-1]['max_current_difference_ma'].values()),.000782)
        self.assertLessEqual(report['attempts'][-1]['max_totalizer_equivalent_difference_ma'],.000782)

    def test_invalid_modes_and_unapproved_controls_rejected(self):
        for kwargs in (dict(sample_seconds=2),dict(internal_substeps=True),dict(internal_substeps=5),dict(enable_hart_totalizer=False)):
            options=dict(modulated=False,sample_seconds=5,seed=808,internal_substeps=384);options.update(kwargs)
            with self.subTest(kwargs=kwargs),self.assertRaises(ValueError): GenericReceiverCompressorSimulator(**options)
        s=self.simulator();before=s.physical_state();s.set_control_hook(temperature_current_bias_ma=1)
        with self.assertRaises(ValueError): s.step()
        self.assertEqual(s.physical_state(),before)


if __name__=='__main__':unittest.main()
