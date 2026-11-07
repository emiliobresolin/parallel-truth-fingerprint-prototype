"""Strict versioned reconstruction of approved generic plant acquisition.

Reconstruction permits only 2e-10 relative/1e-9 absolute floating-point error;
raw digital current, SV, source-event and persistence comparisons remain exact.
"""
import math

from parallel_truth_fingerprint.sensor_simulation.generic_plant import (
    COLLECTION_VERSION, generic_plant_configuration, validate_generic_plant_configuration,
    generic_totalizer_configuration, generic_mass_flow_configuration,
    generic_device_configurations, GenericReceiverCompressorSimulator, select_numerical_resolution,
)


def is_generic(frozen):
    marked = frozen.get('version') == COLLECTION_VERSION
    declared = 'generic_plant_configuration' in frozen
    if marked != declared:
        raise ValueError('Generic model marker/configuration mismatch.')
    return marked


def compare_reconstruction(actual, expected, *, location='generic reconstruction'):
    if type(expected) is bool or expected is None or isinstance(expected,str):
        if type(actual) is not type(expected) or actual != expected:
            raise ValueError(f'{location} differs.')
    elif isinstance(expected,(int,float)):
        if (isinstance(actual,bool) or not isinstance(actual,(int,float)) or not math.isfinite(actual)
                or not math.isclose(actual,expected,rel_tol=2e-10,abs_tol=1e-9)):
            raise ValueError(f'{location} numeric value differs.')
    elif isinstance(expected,dict):
        if not isinstance(actual,dict) or set(actual)!=set(expected):
            raise ValueError(f'{location} fields differ.')
        for key in expected:
            compare_reconstruction(actual[key],expected[key],location=f'{location}.{key}')
    elif isinstance(expected,(list,tuple)):
        if not isinstance(actual,(list,tuple)) or len(actual)!=len(expected):
            raise ValueError(f'{location} sequence differs.')
        for i,(a,b) in enumerate(zip(actual,expected)):
            compare_reconstruction(a,b,location=f'{location}[{i}]')
    else:
        raise ValueError(f'Unsupported {location} data.')


def validate_generic_contract(frozen, *, verify_numerics=False):
    if not is_generic(frozen):
        return False
    validate_generic_plant_configuration(frozen['generic_plant_configuration'])
    if (frozen.get('hart_totalizer_configuration')!=generic_totalizer_configuration()
            or frozen.get('mass_flow_configuration')!=generic_mass_flow_configuration()
            or frozen.get('operational_assumptions') is not None
            or frozen['parameters']['interval_seconds']!=5.0
            or frozen['parameters']['edge_count']!=4
            or frozen['parameters']['simulation_seed']!=808):
        raise ValueError('Generic source recipe differs from approved configuration.')
    report = frozen.get('generic_numerical_resolution')
    if (not isinstance(report,dict) or report.get('selected_substeps_per_round') not in (6,12,24,48,96,192,384,768)
            or report.get('numerical_budget_ma')!=.000782 or not report.get('attempts')
            or report['attempts'][-1].get('passed') is not True
            or report['attempts'][-1].get('fine_substeps_per_round')!=report['selected_substeps_per_round']):
        raise ValueError('Missing frozen generic numerical qualification.')
    if verify_numerics:
        expected = select_numerical_resolution()
        for value in (report,expected):
            if not math.isfinite(value.get('wall_duration_seconds',math.nan)) or value['wall_duration_seconds']<0:
                raise ValueError('Invalid numerical qualification duration.')
        # Durations are measurements, not reproducible scientific settings.
        left = {k:v for k,v in report.items() if k!='wall_duration_seconds'}
        right = {k:v for k,v in expected.items() if k!='wall_duration_seconds'}
        compare_reconstruction(left,right,location='normal numerical qualification')
    return True


def validate_generic_rows(rows,frozen):
    validate_generic_contract(frozen,verify_numerics=True)
    if not rows:
        raise ValueError('Generic observations are missing.')
    profile=rows[0]['profile']
    if profile not in ('unmodulated','modulated'):
        raise ValueError('Unknown generic demand profile.')
    simulator=GenericReceiverCompressorSimulator(modulated=profile=='modulated',sample_seconds=5,
        seed=808,internal_substeps=frozen['generic_numerical_resolution']['selected_substeps_per_round'])
    from parallel_truth_fingerprint.evidence.paired_replay import PairedReplayProtocol
    protocol=PairedReplayProtocol(**frozen['parameters'])
    if len(rows)!=len(protocol.profile_schedule()):
        raise ValueError('Generic acquisition must contain the exact complete frozen schedule.')
    devices=generic_device_configurations()
    for index,row in enumerate(rows,1):
        if (row.get('edge_membership') != list(devices)
                or len(row.get('consensus_source_edges',[]))*3 <= len(devices)*2):
            raise ValueError('Generic winning quorum/membership differs from four-edge contract.')
        phase,block,offset=row['phase'],row['block'],row['offset']
        schedule=protocol.profile_schedule()
        if index>len(schedule) or (phase,block,offset)!=schedule[index-1]:
            raise ValueError('Generic schedule differs from frozen acquisition protocol.')
        if row['index']!=index or row['profile']!=profile:
            raise ValueError('Generic acquisition ordering/profile differs.')
        simulator.set_demand_target(protocol.demand_target(phase,offset))
        receipts=row['generation'].get('generic_conditioning')
        should_condition=(phase=='train' and offset==0) or (phase=='source' and offset==0)
        if should_condition:
            expected=simulator.condition_to_regime()
            if not isinstance(receipts,dict):
                raise ValueError('Missing declared generic conditioning receipt.')
            duration=receipts.get('wall_duration_seconds')
            if isinstance(duration,bool) or not isinstance(duration,(int,float)) or not math.isfinite(duration) or duration<0:
                raise ValueError('Invalid actual conditioning duration.')
            compare_reconstruction({k:v for k,v in receipts.items() if k!='wall_duration_seconds'},
                {k:v for k,v in expected.items() if k!='wall_duration_seconds'},location='conditioning')
        elif receipts is not None:
            raise ValueError('Unexpected generic conditioning or cadence gap.')
        expected=simulator.step().to_dict()
        acquired=row['generation']['acquisition_snapshot']
        compare_reconstruction(acquired,expected,location='generic acquired snapshot')
        from parallel_truth_fingerprint.evidence.hart_totalizer import validate_all_source_evidence
        validate_all_source_evidence(row, acquired['transmitter_observations'])
        generation=row['generation']
        compare_reconstruction(generation['simulation_seconds'],simulator.simulation_seconds,location='generic simulation clock')
        compare_reconstruction(generation['latent_engineering_state'],simulator.engineering_state,location='generic hidden state')
        for field,expected_value in [('demand_target_pct',simulator.target_demand),('base_demand_pct',simulator.base_demand),('actual_demand_pct',simulator.current_demand)]:
            compare_reconstruction(generation[field],expected_value,location=field)
        raw_all=row['hart_source_evidence']['persisted_source_snapshot']['payloads_by_sensor']
        if set(raw_all)!=set(expected['transmitter_observations']):
            raise ValueError('Generic persisted source must contain all four sensors.')
        for device in devices.values():
            sensor=device.sensor_name
            observation=acquired['transmitter_observations'][sensor]
            raw=raw_all[sensor]
            expected_device={'tag':device.tag,'long_tag':device.long_tag,
                'manufacturer_id':device.manufacturer_id,'device_type':device.device_type}
            if (raw['device_info']!=expected_device or raw['gateway_id']!=device.gateway_id
                    or raw['process_data']['pv']!=observation['pv']
                    or raw['process_data'].get('sv')!=observation.get('sv')
                    or raw['process_data']['loop_current_ma']!=observation['loop_current_ma']
                    or raw['process_data']['loop_current_ma']!=row['consensused_values'][sensor]
                    or raw['process_data']['pv_percent_range']!=observation['pv_percent_range']
                    or raw['process_data'].get('physics_metrics','missing') is not None
                    or raw['diagnostics']!=dict(observation['diagnostics'],cold_start=False)):
                raise ValueError('Generic raw instrument identity/value/startup differs from persisted acquisition.')
            # Exact source-to-consensus comparisons above are deliberately not numerical tolerances.
            if row['physical_scada']['behavioral_sensor_values'][sensor]['loop_current_ma']!=observation['loop_current_ma']:
                raise ValueError('Generic SCADA differs from actual acquired digital current.')
            projected = device.sensor_range.minimum + (observation['loop_current_ma']-4)/16 * (
                device.sensor_range.maximum-device.sensor_range.minimum)
            compare_reconstruction(row['physical_scada']['sensor_values'][sensor],
                {'value':projected,'unit':device.unit,'mode':'match'},location='generic SCADA projection')
    return True
