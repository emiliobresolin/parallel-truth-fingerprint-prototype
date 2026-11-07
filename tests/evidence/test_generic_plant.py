"""Versioned receiver provenance: actual payload encoding and tamper rejection."""
import copy
from dataclasses import asdict
from datetime import datetime, timezone
import json
import time
from types import SimpleNamespace
import unittest

from parallel_truth_fingerprint.sensor_simulation.generic_plant import (
    COLLECTION_VERSION,GenericReceiverCompressorSimulator,generic_device_configurations,
    generic_plant_configuration,generic_totalizer_configuration,generic_mass_flow_configuration,
    select_numerical_resolution,
)
from parallel_truth_fingerprint.edge_nodes.common.acquisition import EdgeAcquisitionService
from parallel_truth_fingerprint.consensus.current_domain import source_event_id
from parallel_truth_fingerprint.evidence.paired_replay import PairedReplayProtocol
from parallel_truth_fingerprint.evidence.generic_plant import validate_generic_contract,validate_generic_rows
from parallel_truth_fingerprint.evidence.hart_totalizer import (
    validate_collection_contract,validate_rows,build_source_evidence,
)


def source_inputs(payloads, edge_ids, round_id):
    """Actual encoded acquisitions copied into independent winning edge views."""
    round_input=SimpleNamespace(replicated_states=[
        SimpleNamespace(owner_edge_id=edge,observations_by_sensor=dict(payloads))
        for edge in edge_ids])
    valid=SimpleNamespace(source_edges=tuple(edge_ids),
        sensor_values={sensor:p.process_data.loop_current_ma for sensor,p in payloads.items()},
        round_identity=SimpleNamespace(round_id=round_id))
    persisted={'artifact_key':f'artifact/{round_id}',
        'round_identity':{'round_id':round_id},
        'consensus_context':{'source_edges':list(edge_ids)},
        'validated_state':{'structured_payload_snapshot':{
            'selected_source_edge_id':edge_ids[0],
            'payloads_by_sensor':{sensor:p.to_dict() for sensor,p in payloads.items()}}}}
    return round_input,valid,persisted


def generic_fixture():
    protocol=PairedReplayProtocol(train_rounds=16,calibration_rounds=12,block_rounds=4,settle_rounds=3,
        repetitions=1,interval_seconds=5,epochs=1,edge_count=4,simulation_seed=808)
    frozen={'version':COLLECTION_VERSION,'parameters':asdict(protocol),
        'generic_plant_configuration':generic_plant_configuration(),
        'generic_numerical_resolution':select_numerical_resolution(),
        'hart_totalizer_configuration':generic_totalizer_configuration(),
        'mass_flow_configuration':generic_mass_flow_configuration(),
        'operational_assumptions':None,'auxiliary_measurement_domain':'hart_totalizer_mass_kg'}
    simulator=GenericReceiverCompressorSimulator(modulated=False,sample_seconds=5,seed=808,
        internal_substeps=frozen['generic_numerical_resolution']['selected_substeps_per_round'])
    devices=generic_device_configurations()
    edges={name:EdgeAcquisitionService(cfg) for name,cfg in devices.items()}
    rows=[]
    for i,(phase,block,offset) in enumerate(protocol.profile_schedule()):
        simulator.set_demand_target(protocol.demand_target(phase,offset))
        receipt=simulator.condition_to_regime() if offset==0 and phase in {'train','source'} else None
        frame=simulator.step();snapshot=frame.to_dict()
        acquisition_start=time.time()
        payloads={edge.device_config.sensor_name:edge.acquire(snapshot=frame) for edge in edges.values()}
        acquisition_end=time.time()
        state={'source_round_id':f'r{i+1}','behavioral_sensor_values':{n:{'loop_current_ma':o.loop_current_ma}
            for n,o in frame.transmitter_observations.items()}}
        state['behavioral_sensor_values']['mass_flow']['totalizer1_kg']=frame.transmitter_observations['mass_flow'].sv.value
        state['sensor_values'] = {
            d.sensor_name: {'value':d.sensor_range.minimum + (
                frame.transmitter_observations[d.sensor_name].loop_current_ma-4)/16 * (
                d.sensor_range.maximum-d.sensor_range.minimum), 'unit':d.unit,'mode':'match'}
            for d in devices.values()
        }
        evidence=build_source_evidence(*source_inputs(payloads,list(edges),f'r{i+1}'),
            include_all_sensors=True)
        rows.append({'index':i+1,'profile':'unmodulated','phase':phase,'block':block,'offset':offset,'round_id':f'r{i+1}',
            'generation':{'acquisition_snapshot':snapshot,'simulation_seconds':simulator.simulation_seconds,
                'latent_engineering_state':dict(simulator.engineering_state),'generic_conditioning':receipt,
                'demand_target_pct':simulator.target_demand,'base_demand_pct':simulator.base_demand,
                'actual_demand_pct':simulator.current_demand},
            'physical_scada':state,'views':[],'edge_membership':list(edges),'consensus_source_edges':list(edges),
            'acquisition_window':{'start_epoch':acquisition_start,'end_epoch':acquisition_end},
            'consensused_values':{n:o.loop_current_ma for n,o in frame.transmitter_observations.items()},
            'hart_source_evidence':evidence,'baseline_persisted_artifact_key':evidence['artifact_key']})
    return rows,frozen


class GenericEvidenceTests(unittest.TestCase):
    @classmethod
    def setUpClass(cls):cls.rows,cls.frozen=generic_fixture()

    def test_new_contract_and_reconstructed_payloads(self):
        self.assertTrue(validate_collection_contract(self.frozen))
        self.assertTrue(validate_generic_contract(self.frozen,verify_numerics=True))
        self.assertEqual(validate_rows(self.rows,self.frozen),5)

    def test_export_all_sources_is_opt_in_and_legacy_shape_is_unchanged(self):
        from parallel_truth_fingerprint.edge_nodes.common.mqtt_io import deserialize_payload
        row=self.rows[0]
        evidence=row['hart_source_evidence']
        payloads={sensor:deserialize_payload(json.dumps(raw)) for sensor,raw in
            evidence['persisted_source_snapshot']['payloads_by_sensor'].items()}
        inputs=source_inputs(payloads,row['edge_membership'],row['round_id'])
        legacy=build_source_evidence(*inputs)
        self.assertEqual(legacy,{key:value for key,value in evidence.items() if key not in {
            'source_payloads_by_sensor_by_edge','source_event_ids_by_sensor_by_edge'}})
        for group in ('source_payloads_by_sensor_by_edge','source_event_ids_by_sensor_by_edge'):
            self.assertEqual(set(evidence[group]),set(payloads))
            self.assertTrue(all(set(v)==set(row['consensus_source_edges'])
                for v in evidence[group].values()))

    def test_export_rejects_persisted_source_substitution_before_serializing(self):
        from parallel_truth_fingerprint.edge_nodes.common.mqtt_io import deserialize_payload
        row=self.rows[0]
        payloads={sensor:deserialize_payload(json.dumps(raw)) for sensor,raw in
            row['hart_source_evidence']['persisted_source_snapshot']['payloads_by_sensor'].items()}
        inputs=source_inputs(payloads,row['edge_membership'],row['round_id'])
        inputs[2]['validated_state']['structured_payload_snapshot']['payloads_by_sensor']['temperature']['timestamp']='2000-01-01T00:00:00+00:00'
        with self.assertRaisesRegex(ValueError,'actual selected acquisition'):
            build_source_evidence(*inputs,include_all_sensors=True)

    @staticmethod
    def replace_recorded_source(row,sensor,mutate,*,refresh_identities=False):
        from parallel_truth_fingerprint.edge_nodes.common.mqtt_io import deserialize_payload
        evidence=row['hart_source_evidence']
        raw=copy.deepcopy(evidence['persisted_source_snapshot']['payloads_by_sensor'][sensor])
        mutate(raw)
        evidence['persisted_source_snapshot']['payloads_by_sensor'][sensor]=copy.deepcopy(raw)
        for edge in row['consensus_source_edges']:
            evidence['source_payloads_by_sensor_by_edge'][sensor][edge]=copy.deepcopy(raw)
            if refresh_identities:
                evidence['source_event_ids_by_sensor_by_edge'][sensor][edge]=source_event_id(
                    deserialize_payload(json.dumps(raw)))
        if sensor=='mass_flow':
            evidence['source_payloads_by_edge']=copy.deepcopy(
                evidence['source_payloads_by_sensor_by_edge'][sensor])
            evidence['source_event_ids_by_edge']=copy.deepcopy(
                evidence['source_event_ids_by_sensor_by_edge'][sensor])

    def test_raw_timestamp_requires_actual_acquisition_window_and_timezone(self):
        for sensor in ('temperature','pressure','rpm','mass_flow'):
            for kind in ('old','future','naive'):
                changed=copy.deepcopy(self.rows)
                row=changed[0]
                timestamp={'old':'2000-01-01T00:00:00+00:00',
                    'future':datetime.fromtimestamp(row['acquisition_window']['end_epoch']+10,
                        tz=timezone.utc).isoformat(),
                    'naive':'2026-11-02T12:00:00'}[kind]
                self.replace_recorded_source(row,sensor,lambda raw:raw.update(timestamp=timestamp),
                    refresh_identities=True)
                with self.subTest(sensor=sensor,kind=kind),self.assertRaisesRegex(
                        ValueError,'timestamp'):
                    validate_generic_rows(changed,self.frozen)

    def test_wrong_protocol_rejected_for_every_raw_sensor(self):
        for sensor in ('temperature','pressure','rpm','mass_flow'):
            changed=copy.deepcopy(self.rows)
            self.replace_recorded_source(changed[0],sensor,lambda raw:raw.update(protocol='MODBUS'))
            with self.subTest(sensor=sensor),self.assertRaisesRegex(ValueError,'protocol'):
                validate_generic_rows(changed,self.frozen)

    def test_source_timestamp_substitution_with_retained_source_ids_rejected(self):
        # Stay inside the actual window; timestamp/source identity must still
        # match the independently saved winning-replica IDs.
        for sensor in ('temperature','pressure','rpm','mass_flow'):
            changed=copy.deepcopy(self.rows)
            row=changed[0]
            start=row['acquisition_window']['start_epoch']
            end=row['acquisition_window']['end_epoch']
            original=row['hart_source_evidence']['persisted_source_snapshot']['payloads_by_sensor'][sensor]['timestamp']
            candidates=[datetime.fromtimestamp(start+(end-start)*fraction,
                tz=timezone.utc) for fraction in (.5,.25,.75)]
            candidate=next(item for item in candidates if item.isoformat()!=original)
            self.assertTrue(start <= candidate.timestamp() <= end)
            stamp=candidate.isoformat()
            self.replace_recorded_source(row,sensor,lambda raw:raw.update(timestamp=stamp))
            with self.subTest(sensor=sensor),self.assertRaises(ValueError):
                validate_generic_rows(changed,self.frozen)

    def test_coherent_observation_current_tamper_cannot_replace_saved_raw_source(self):
        changed=copy.deepcopy(self.rows)
        row=changed[0];sensor='temperature';delta=1e-12
        row['generation']['acquisition_snapshot']['transmitter_observations'][sensor]['loop_current_ma']+=delta
        row['physical_scada']['behavioral_sensor_values'][sensor]['loop_current_ma']+=delta
        row['consensused_values'][sensor]+=delta
        row['hart_source_evidence']['persisted_source_snapshot']['payloads_by_sensor'][sensor]['process_data']['loop_current_ma']+=delta
        with self.assertRaisesRegex(ValueError,'selected raw replica'):
            validate_generic_rows(changed,self.frozen)

    def test_nonselected_replica_metadata_must_match_selected_persisted_payload(self):
        for mutate in (
            lambda raw:raw['process_data']['pv'].update(unit='psi'),
            lambda raw:raw['process_data']['pv'].update(value=0),
            lambda raw:raw['diagnostics'].update(device_status_hex='0x01'),
        ):
            changed=copy.deepcopy(self.rows)
            # These fields are intentionally outside source_event_id; the
            # capture proof still requires the raw MQTT copy to be unchanged.
            peer=changed[0]['hart_source_evidence']['source_payloads_by_sensor_by_edge']['pressure']['edge-2']
            mutate(peer)
            with self.subTest(mutate=mutate),self.assertRaisesRegex(ValueError,'raw source payload'):
                validate_generic_rows(changed,self.frozen)

    def test_missing_sensor_quorum_proof_is_rejected(self):
        changed=copy.deepcopy(self.rows)
        del changed[0]['hart_source_evidence']['source_payloads_by_sensor_by_edge']['pressure']['edge-4']
        with self.assertRaisesRegex(ValueError,'winning quorum'):
            validate_generic_rows(changed,self.frozen)
        changed=copy.deepcopy(self.rows)
        changed[0]['edge_membership'].append('edge-5')
        with self.assertRaisesRegex(ValueError,'quorum/membership'):
            validate_generic_rows(changed,self.frozen)

    def test_shortened_schedule_is_rejected(self):
        with self.assertRaisesRegex(ValueError,'complete frozen schedule'):
            validate_generic_rows(self.rows[:-1],self.frozen)

    def test_invalid_version_configuration_seed_and_resolution_rejected(self):
        for mutate in (
            lambda x:x.update(version='documented-noise-hart-totalizer-v1'),
            lambda x:x['parameters'].update(simulation_seed=707),
            lambda x:x['generic_plant_configuration']['plant']['receiver'].update(volume_m3=3),
            lambda x:x['generic_numerical_resolution'].update(selected_substeps_per_round=768),
            lambda x:x['hart_totalizer_configuration'].update(model='old-counter'),
        ):
            changed=copy.deepcopy(self.frozen);mutate(changed)
            with self.subTest(mutate=mutate),self.assertRaises(ValueError):validate_collection_contract(changed)

    def test_hidden_state_clock_and_conditioning_tampering_rejected(self):
        for mutate in (
            lambda x:x[0]['generation'].update(generic_conditioning=None),
            lambda x:x[0]['generation']['generic_conditioning'].update(simulated_duration_seconds=120),
            lambda x:x[1]['generation'].update(simulation_seconds=370.1),
            lambda x:x[1]['generation']['latent_engineering_state'].update(temperature=99),
            lambda x:x[1]['generation']['acquisition_snapshot']['metadata']['receiver_state']['receiver'].update(mass_kg=100),
            lambda x:x[1]['generation'].update(generic_conditioning=x[0]['generation']['generic_conditioning']),
        ):
            changed=copy.deepcopy(self.rows);mutate(changed)
            with self.subTest(mutate=mutate),self.assertRaises(ValueError):validate_generic_rows(changed,self.frozen)

    def test_persisted_instrument_identity_and_exact_current_tampering_rejected(self):
        for sensor in ('temperature','pressure','rpm','mass_flow'):
            changed=copy.deepcopy(self.rows)
            changed[0]['hart_source_evidence']['persisted_source_snapshot']['payloads_by_sensor'][sensor]['device_info']['manufacturer_id']+=1
            with self.subTest(sensor=sensor),self.assertRaises(ValueError):validate_generic_rows(changed,self.frozen)
        changed=copy.deepcopy(self.rows)
        changed[0]['consensused_values']['pressure']+=1e-12
        with self.assertRaises(ValueError):validate_generic_rows(changed,self.frozen)

    def test_reconstruction_tolerance_does_not_relax_source_binding(self):
        changed=copy.deepcopy(self.rows)
        changed[0]['generation']['latent_engineering_state']['temperature']+=1e-11
        self.assertTrue(validate_generic_rows(changed,self.frozen))
        changed[0]['physical_scada']['behavioral_sensor_values']['temperature']['loop_current_ma']+=1e-12
        with self.assertRaises(ValueError):validate_generic_rows(changed,self.frozen)

    def test_legacy_display_scale_in_generic_scada_is_rejected(self):
        changed=copy.deepcopy(self.rows)
        changed[0]['physical_scada']['sensor_values']['temperature']['value']=62.1
        with self.assertRaisesRegex(ValueError,'SCADA projection'):
            validate_generic_rows(changed,self.frozen)


if __name__=='__main__':unittest.main()
