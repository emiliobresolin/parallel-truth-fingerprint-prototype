"""HART mass totalization, source integrity and matched temporal inputs."""
import copy
from dataclasses import replace
from datetime import datetime, timedelta, timezone
import json
import math
from pathlib import Path
import sys
import tempfile
import unittest

sys.path[:0] = [str(Path(__file__).resolve().parents[2]/'src'), str(Path(__file__).resolve().parents[2]/'scripts')]
from parallel_truth_fingerprint.sensor_simulation.mass_flow import MassFlowCompressorSimulator, MassFlowConfiguration, totalizer_configuration
from parallel_truth_fingerprint.contracts.raw_hart_payload import ProcessVariable
from parallel_truth_fingerprint.consensus.current_domain import source_event_id, same_observation
from parallel_truth_fingerprint.consensus.engine import ConsensusEngine
from parallel_truth_fingerprint.evidence.paired_replay import PairedReplayProtocol
from parallel_truth_fingerprint.evidence.hart_totalizer import prepare, feature_vectors, matched_currents, FEATURES, validate_collection_contract, build_source_evidence, validate_source_evidence
from tests.evidence.test_four_edge_replay import FourEdgeReplayTests
from parallel_truth_fingerprint.evidence.replay_evaluation import SequenceReplayScada


def fixture(*, technical=True):
    protocol = PairedReplayProtocol(train_rounds=16, calibration_rounds=12, block_rounds=4,
        settle_rounds=3, repetitions=1, interval_seconds=2, epochs=1, edge_count=4) if technical else PairedReplayProtocol(edge_count=4)
    frozen = {'parameters': {k: v for k, v in vars(protocol).items()},
              'mass_flow_configuration': vars(MassFlowConfiguration()),
              'hart_totalizer_configuration': totalizer_configuration()}
    simulator = MassFlowCompressorSimulator(modulated=False, sample_seconds=protocol.interval_seconds/3,
        seed=707, enable_hart_totalizer=True)
    rows, source = [], []
    template = FourEdgeReplayTests().acquire().replicated_states[0].observations_by_sensor['mass_flow']
    for index, (phase, block, offset) in enumerate(protocol.profile_schedule(), 1):
        simulator.set_demand_target(protocol.demand_target(phase, offset))
        for _ in range(3):
            frame = simulator.step()
        state = {'source_round_id': f'round{index}', 'behavioral_sensor_values': {
            sensor: {'loop_current_ma': observation.loop_current_ma}
            for sensor, observation in frame.transmitter_observations.items()}}
        state['behavioral_sensor_values']['mass_flow']['totalizer1_kg'] = frame.transmitter_observations['mass_flow'].sv.value
        row = {'index': index, 'round_id': f'round{index}', 'phase': phase, 'block': block, 'offset': offset,
               'physical_scada': state, 'generation': {'acquisition_snapshot': frame.to_dict(),
                   'simulation_seconds': simulator.simulation_seconds}, 'views': []}
        sv = frame.transmitter_observations['mass_flow'].sv
        payload = replace(template, timestamp=(datetime(2026,10,31,tzinfo=timezone.utc)+timedelta(seconds=index)).isoformat(),
            process_data=replace(template.process_data, loop_current_ma=frame.transmitter_observations['mass_flow'].loop_current_ma,
                                 sv=ProcessVariable(sv.value, sv.unit, sv.unit_code, sv.description)))
        edges = [f'edge-{i}' for i in range(1,5)]
        raw = payload.to_dict()
        row['edge_membership'] = edges
        row['consensus_source_edges'] = edges
        row['consensused_values'] = {sensor: observation.loop_current_ma for sensor, observation in frame.transmitter_observations.items()}
        row['hart_source_evidence'] = {'artifact_key': f'valid-consensus-artifacts/round{index}.json',
            'persisted_round_id': row['round_id'],
            'selected_source_edge_id': 'edge-1',
            'persisted_source_snapshot': {'selected_source_edge_id': 'edge-1', 'payloads_by_sensor': {'mass_flow': raw}},
            'source_payloads_by_edge': {edge: copy.deepcopy(raw) for edge in edges},
            'source_event_ids_by_edge': {edge: source_event_id(payload) for edge in edges}}
        row['baseline_persisted_artifact_key'] = row['hart_source_evidence']['artifact_key']
        if phase == 'source':
            if offset == 0:
                source = []
            source.append(copy.deepcopy(state))
        if phase in ('stable', 'transition'):
            normal, replay = (('normal_stable', 'replay_same_regime') if phase == 'stable' else ('legitimate_transition', 'replay_hiding_change'))
            row['views'] = [{'condition': normal, 'scada_state': copy.deepcopy(state), 'historical_state': None,
                             'comparison': {'divergent_sensors': []}},
                            {'condition': replay, 'scada_state': copy.deepcopy(source[offset]),
                             'historical_state': copy.deepcopy(source[offset]),
                             'comparison': {'divergent_sensors': ['mass_flow']}}]
        rows.append(row)
    return rows, frozen


class HartTotalizerTests(unittest.TestCase):
    def test_new_collection_contract_requires_matching_version_config_and_domain(self):
        valid = {'version': 'documented-noise-hart-totalizer-v1',
                 'hart_totalizer_configuration': totalizer_configuration(),
                 'auxiliary_measurement_domain': 'hart_totalizer_mass_kg', 'parameters': {'edge_count': 4}}
        self.assertTrue(validate_collection_contract(valid))
        self.assertFalse(validate_collection_contract({'version': 'documented-noise-four-edge-v2'}))
        for key in ('hart_totalizer_configuration', 'auxiliary_measurement_domain', 'version'):
            changed = copy.deepcopy(valid)
            del changed[key]
            with self.subTest(key=key), self.assertRaises(ValueError):
                validate_collection_contract(changed)

    def test_accumulation_units_internal_flow_and_no_rng_or_legacy_change(self):
        args = dict(modulated=False, sample_seconds=2, seed=707)
        normal, enabled = MassFlowCompressorSimulator(**args), MassFlowCompressorSimulator(enable_hart_totalizer=True, **args)
        previous = 0
        for step in range(100):
            if step == 20:
                normal.set_demand_target(75)
                enabled.set_demand_target(75)
            old, new = normal.step(), enabled.step()
            expected = enabled._flow*2/3600
            self.assertAlmostEqual(enabled.totalizer1_kg-previous, expected, places=13)
            previous = enabled.totalizer1_kg
            self.assertIsNone(old.transmitter_observations['mass_flow'].sv)
            self.assertEqual(new.transmitter_observations['mass_flow'].sv.unit, 'kg')
            for sensor in old.transmitter_observations:
                self.assertEqual(old.transmitter_observations[sensor].loop_current_ma,
                                 new.transmitter_observations[sensor].loop_current_ma)

    def acquired(self):
        acquired = FourEdgeReplayTests().acquire()
        states = []
        for state in acquired.replicated_states:
            payloads = dict(state.observations_by_sensor)
            flow = payloads['mass_flow']
            payloads['mass_flow'] = replace(flow, process_data=replace(flow.process_data,
                sv=ProcessVariable(.123456789, 'kg', None, 'Totalizer_1_Mass')))
            states.append(replace(state, observations_by_sensor=payloads))
        return replace(acquired, replicated_states=tuple(states))

    def test_sv_binding_and_three_of_four_quorum_without_current_change(self):
        acquired = self.acquired()
        normal = acquired.replicated_states[0].observations_by_sensor['mass_flow']
        altered = replace(normal, process_data=replace(normal.process_data, sv=replace(normal.process_data.sv, value=.5)))
        self.assertFalse(same_observation(normal, altered))
        self.assertNotEqual(source_event_id(normal), source_event_id(altered))
        states = list(acquired.replicated_states)
        states[-1] = replace(states[-1], observations_by_sensor=dict(states[-1].observations_by_sensor, mass_flow=altered))
        result = ConsensusEngine().evaluate(replace(acquired, replicated_states=tuple(states)))
        self.assertEqual(result.consensused_valid_state.source_edges, ('edge-1', 'edge-2', 'edge-3'))
        states[-2] = replace(states[-2], observations_by_sensor=dict(states[-2].observations_by_sensor, mass_flow=altered))
        result = ConsensusEngine().evaluate(replace(acquired, replicated_states=tuple(states)))
        self.assertIsNone(result.consensused_valid_state)

    def test_malformed_auxiliary_replica_preserves_strict_input_rejection(self):
        acquired = self.acquired()
        original = acquired.replicated_states[-1]
        flow = original.observations_by_sensor['mass_flow']
        for secondary in [replace(flow.process_data.sv, value=math.nan), replace(flow.process_data.sv, unit='lb')]:
            malformed = replace(flow, process_data=replace(flow.process_data, sv=secondary))
            bad = replace(original, observations_by_sensor=dict(original.observations_by_sensor, mass_flow=malformed))
            with self.subTest(secondary=secondary), self.assertRaises(ValueError):
                ConsensusEngine().evaluate(replace(acquired, replicated_states=(*acquired.replicated_states[:-1], bad)))

    def test_new_sv_rejects_excluded_owner_and_disagreed_current(self):
        acquired = self.acquired()
        audit = ConsensusEngine().evaluate(acquired)
        service = SequenceReplayScada(sensor_names=('temperature', 'pressure', 'rpm', 'mass_flow'))
        owner = replace(acquired.replicated_states[0], owner_edge_id='excluded-edge')
        with self.assertRaisesRegex(ValueError, 'agreed source edge'):
            service.project_state(audit.consensused_valid_state, source_replicated_state=owner)
        source = acquired.replicated_states[0]
        flow = source.observations_by_sensor['mass_flow']
        altered = replace(source, observations_by_sensor=dict(source.observations_by_sensor,
            mass_flow=replace(flow, process_data=replace(flow.process_data, loop_current_ma=18))))
        with self.assertRaisesRegex(ValueError, 'unchanged acquired current'):
            service.project_state(audit.consensused_valid_state, source_replicated_state=altered)

    def test_real_acquisition_quorum_persistence_scada_and_historical_sv(self):
        import run_local_demo as demo
        from parallel_truth_fingerprint.edge_nodes.common.mqtt_io import PassiveMqttRelay
        from parallel_truth_fingerprint.edge_nodes.edge_1.service import TemperatureEdgeService
        from parallel_truth_fingerprint.edge_nodes.edge_2.service import PressureEdgeService
        from parallel_truth_fingerprint.edge_nodes.edge_3.service import RpmEdgeService
        from parallel_truth_fingerprint.edge_nodes.edge_4.service import MassFlowEdgeService
        from parallel_truth_fingerprint.persistence import MinioArtifactStore, MinioStoreConfig
        from tests.persistence.test_service import FakeMinioClient
        edges = [TemperatureEdgeService(), PressureEdgeService(), RpmEdgeService(), MassFlowEdgeService()]
        relay = PassiveMqttRelay()
        for edge in edges:
            edge.attach_transport(relay)
        simulator = MassFlowCompressorSimulator(modulated=False, sample_seconds=2/3, seed=707, enable_hart_totalizer=True)
        for _ in range(3):
            frame = simulator.step()
            for edge in edges:
                edge.publish_local_observation(edge.acquire(snapshot=frame))
        acquired = demo.build_consensus_round_input(edges)
        audit = ConsensusEngine().evaluate(acquired)
        service = SequenceReplayScada(sensor_names=('temperature', 'pressure', 'rpm', 'mass_flow'))
        service.select_phase('normal', 0)
        store = MinioArtifactStore(MinioStoreConfig(endpoint='localhost:9000', access_key='x', secret_key='x', bucket='hart-test'), client=FakeMinioClient())
        state, _, _, _, persisted = demo.run_scada_comparison_and_persistence(consensus_audit=audit,
            artifact_store=store, scada_service=service, campaign_id='hart-test')
        self.assertEqual(persisted['status'], 'persisted')
        saved = store.load_json(persisted['artifact_key'])
        evidence = build_source_evidence(acquired, audit.consensused_valid_state, saved)
        row = {'consensus_source_edges': list(audit.consensused_valid_state.source_edges),
               'edge_membership': list(acquired.participating_edges), 'consensused_values': audit.consensused_valid_state.sensor_values,
               'round_id': audit.consensused_valid_state.round_identity.round_id,
               'baseline_persisted_artifact_key': persisted['artifact_key'],
               'physical_scada': state.to_dict(), 'hart_source_evidence': evidence}
        validate_source_evidence(row, frame.to_dict()['transmitter_observations']['mass_flow'])
        self.assertEqual(saved['validated_state']['structured_payload_snapshot']['payloads_by_sensor']['mass_flow']['process_data']['sv']['value'],
                         frame.transmitter_observations['mass_flow'].sv.value)
        service.select_phase('replay', 0)
        replay = service.update_from_consensused_state(audit.consensused_valid_state, source_replicated_state=acquired.replicated_states[0])
        self.assertEqual(replay.behavioral_sensor_values['mass_flow'].totalizer1_kg, frame.transmitter_observations['mass_flow'].sv.value)
        tampered = copy.deepcopy(row)
        tampered['hart_source_evidence']['source_payloads_by_edge']['edge-4']['process_data']['sv']['value'] += .01
        with self.assertRaisesRegex(ValueError, 'identity disagrees'):
            validate_source_evidence(tampered, frame.to_dict()['transmitter_observations']['mass_flow'])

    def test_invalid_sv_rejected_and_legacy_hash_unchanged(self):
        old = FourEdgeReplayTests().acquire().replicated_states[0].observations_by_sensor['mass_flow']
        import hashlib
        expected = hashlib.sha256(json.dumps([old.gateway_id, old.device_info.tag, old.timestamp],
            ensure_ascii=True, separators=(',', ':')).encode('ascii')).hexdigest()
        self.assertEqual(source_event_id(old), expected)
        base = self.acquired().replicated_states[0].observations_by_sensor['mass_flow']
        for sv in [replace(base.process_data.sv, value=math.nan), replace(base.process_data.sv, value=-1),
                   replace(base.process_data.sv, value=True), replace(base.process_data.sv, unit='lb')]:
            with self.subTest(sv=sv), self.assertRaises(ValueError):
                source_event_id(replace(base, process_data=replace(base.process_data, sv=sv)))

    def test_sv_survives_quorum_scada_replay_and_legacy_serialization(self):
        acquired = self.acquired()
        audit = ConsensusEngine().evaluate(acquired)
        service = SequenceReplayScada(sensor_names=('temperature', 'pressure', 'rpm', 'mass_flow'))
        service.select_phase('normal', 0)
        state = service.update_from_consensused_state(audit.consensused_valid_state, source_replicated_state=acquired.replicated_states[0])
        self.assertEqual(state.behavioral_sensor_values['mass_flow'].totalizer1_kg, .123456789)
        self.assertNotIn('totalizer1_kg', state.to_dict()['behavioral_sensor_values']['temperature'])
        service.select_phase('replay', 0)
        replay = service.update_from_consensused_state(audit.consensused_valid_state, source_replicated_state=acquired.replicated_states[0])
        self.assertEqual(replay.behavioral_sensor_values['mass_flow'].totalizer1_kg, .123456789)

    def test_support_partitions_feature_count_and_matched_ablation(self):
        for technical, expected in ((True, [7, 5, 10, 8]), (False, [70, 46, 58, 560])):
            rows, frozen = fixture(technical=technical)
            tensors, ids, examples, reference = prepare(rows, frozen, technical=technical)
            self.assertEqual([len(tensors[k]) for k in ['fit', 'validation', 'calibration']]+[len(examples)], expected)
            self.assertEqual(reference, 1000*frozen['parameters']['interval_seconds']/3600)
            self.assertEqual(len(FEATURES), 10)
            self.assertTrue(all(e['offset'] >= 2 and len(e['physical_source_ids']) == 3 for e in examples))
            for e in examples:
                self.assertEqual(len(e['input_window'][0]), 10)
                self.assertEqual(len(matched_currents(e['input_window'])[0]), 8)
            self.assertFalse(set(ids['fit']) & set(ids['validation']))
            self.assertFalse(set(ids['validation']) & set(ids['calibration']))

    def test_absolute_offset_invariance_and_counter_reset_rejected(self):
        rows, frozen = fixture()
        _, _, original, _ = prepare(rows, frozen, technical=True)
        changed = copy.deepcopy(rows)
        for row in changed:
            for view in row['views']:
                if view['historical_state']:
                    view['scada_state']['behavioral_sensor_values']['mass_flow']['totalizer1_kg'] += 1000
                    view['historical_state']['behavioral_sensor_values']['mass_flow']['totalizer1_kg'] += 1000
        # Test preprocessing separately: validate_rows intentionally binds source SV,
        # while feature_vectors must be invariant to a constant episode offset.
        states = [row['physical_scada'] for row in rows[:5]]
        shifted = copy.deepcopy(states)
        for state in shifted:
            state['behavioral_sensor_values']['mass_flow']['totalizer1_kg'] += 1000
        a, b = feature_vectors(states, 1), feature_vectors(shifted, 1)
        for x, y in zip(a, b):
            for u, v in zip(x, y):
                self.assertAlmostEqual(u, v, places=12)
        shifted[2]['behavioral_sensor_values']['mass_flow']['totalizer1_kg'] = 0
        with self.assertRaises(ValueError):
            feature_vectors(shifted, 1)

    def test_missing_units_cadence_historical_tampering_fail_closed(self):
        rows, frozen = fixture()
        for mutation in ('missing', 'unit', 'cadence', 'history', 'config'):
            changed, contract = copy.deepcopy(rows), copy.deepcopy(frozen)
            if mutation == 'missing':
                del changed[0]['generation']['acquisition_snapshot']['transmitter_observations']['mass_flow']['sv']
            elif mutation == 'unit':
                changed[0]['generation']['acquisition_snapshot']['transmitter_observations']['mass_flow']['sv']['unit'] = 'lb'
            elif mutation == 'cadence':
                changed[1]['generation']['simulation_seconds'] += 1
            elif mutation == 'history':
                view = next(v for r in changed for v in r['views'] if v['historical_state'])
                view['scada_state']['behavioral_sensor_values']['mass_flow']['totalizer1_kg'] += 1
            else:
                contract['hart_totalizer_configuration']['device_variable_code'] = 8
            with self.subTest(mutation=mutation), self.assertRaises(ValueError):
                prepare(changed, contract, technical=True)

    def test_saved_models_reproduce_both_feature_dimensions_and_decisions(self):
        import numpy as np
        import torch
        from parallel_truth_fingerprint.lstm_service.trainer import _load_keras_module
        from evaluate_hart_totalizer import fit_variant, evaluate_components, variants, weight_hash
        from parallel_truth_fingerprint.evidence.replay_calibration import calibrate, COMMON, anomalous
        torch.set_num_threads(1)
        keras = _load_keras_module()
        rows, frozen = fixture()
        tensors, lineage, examples, reference = prepare(rows, frozen, technical=True)
        with tempfile.TemporaryDirectory() as directory:
            ids = None
            for variant in ('hart_totalizer', 'currents_only'):
                output = Path(directory)/variant
                summary = fit_variant(output, tensors, examples, lineage, reference,
                    variant=variant, technical=True, keras=keras, torch=torch, np=np)
                model = keras.models.model_from_json((output/'architecture.json').read_text())
                model.load_weights(str(output/'model.weights.h5'))
                self.assertEqual(weight_hash(model), summary['weights_sha256'])
                data, test = variants(tensors, examples, np, variant)
                self.assertEqual(test.shape, (8, 2, 10 if variant=='hart_totalizer' else 8))
                records = json.loads((output/'scores.json').read_text())
                current_ids = [(r['round_id'], r['condition']) for r in records]
                if ids is not None:
                    self.assertEqual(ids, current_ids)
                ids = current_ids
                calibration = evaluate_components(model, data['calibration'], keras, torch, np)
                scores = evaluate_components(model, test, keras, torch, np)
                for method, values in calibration.items():
                    threshold = calibrate(values.tolist(), COMMON)['threshold']
                    self.assertEqual(threshold, summary['thresholds'][method])
                    for i, record in enumerate(records):
                        self.assertAlmostEqual(record[method+'_score'], scores[method][i], places=12)
                        self.assertEqual(record[method+'_anomalous'], anomalous(scores[method][i], threshold, COMMON))


if __name__ == '__main__':
    unittest.main()
