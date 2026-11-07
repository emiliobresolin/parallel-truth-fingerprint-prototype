"""Four-sensor propagation, quorum, and real syscall association boundaries."""
from dataclasses import replace
from pathlib import Path
import sys
import tempfile
import unittest

sys.path.insert(0,str(Path(__file__).resolve().parents[2]/'scripts'))
sys.path.insert(0,str(Path(__file__).resolve().parents[2]/'src'))
import run_local_demo as demo
from run_nightly_collection import infrastructure
from evaluate_replay_training_offline import current_indices
from parallel_truth_fingerprint.config.runtime import RuntimeDemoConfig
from parallel_truth_fingerprint.consensus.engine import ConsensusEngine
from parallel_truth_fingerprint.consensus.quorum import required_quorum
from parallel_truth_fingerprint.evidence.paired_syscalls import associate, trace_events
from parallel_truth_fingerprint.evidence.replay_evaluation import SequenceReplayScada
from parallel_truth_fingerprint.edge_nodes.common.mqtt_io import PassiveMqttRelay
from parallel_truth_fingerprint.edge_nodes.edge_1.service import TemperatureEdgeService
from parallel_truth_fingerprint.edge_nodes.edge_2.service import PressureEdgeService
from parallel_truth_fingerprint.edge_nodes.edge_3.service import RpmEdgeService
from parallel_truth_fingerprint.edge_nodes.edge_4.service import MassFlowEdgeService
from parallel_truth_fingerprint.sensor_simulation.mass_flow import MassFlowCompressorSimulator
from parallel_truth_fingerprint.sensor_simulation.operational_profiles import OperationalCompressorSimulator
from parallel_truth_fingerprint.lstm_service.replay_behavior import extract_scada_behavioral_feature_vector


class FourEdgeReplayTests(unittest.TestCase):
    def acquire(self):
        edges = [TemperatureEdgeService(),PressureEdgeService(),RpmEdgeService(),MassFlowEdgeService()]
        relay = PassiveMqttRelay()
        for edge in edges:
            edge.attach_transport(relay)
        simulator = MassFlowCompressorSimulator(modulated=True,sample_seconds=5/3,seed=202)
        for _ in range(3):
            frame = simulator.step()
            for edge in edges:
                edge.publish_local_observation(edge.acquire(snapshot=frame))
        return demo.build_consensus_round_input(edges)

    def test_flow_crosses_mqtt_consensus_supervision_and_feature_boundary(self):
        acquired = self.acquire()
        audit = ConsensusEngine().evaluate(acquired)
        self.assertEqual(required_quorum(4),3)
        self.assertEqual(len(audit.consensused_valid_state.source_edges),4)
        scada = SequenceReplayScada(sensor_names=('temperature','pressure','rpm','mass_flow'))
        state = scada.update_from_consensused_state(audit.consensused_valid_state,
                    source_replicated_state=acquired.replicated_states[0])
        self.assertEqual(state.sensor_values['mass_flow'].unit,'kg/h')
        comparison = demo.compare_consensused_to_scada(valid_state=audit.consensused_valid_state,scada_state=state)
        self.assertFalse(demo.build_scada_comparison_output(comparison).divergent_sensors)
        schema, vector = extract_scada_behavioral_feature_vector(state)
        self.assertEqual(len(current_indices(schema)),4)
        self.assertEqual(len(vector),20)
        payload = acquired.replicated_states[0].observations_by_sensor['mass_flow']
        self.assertEqual(payload.device_info.manufacturer_id,0x11)
        self.assertEqual(payload.device_info.device_type,0x1160)

    def test_fourth_inconsistent_view_is_excluded_with_three_remaining(self):
        acquired = self.acquire()
        faulty = demo.inject_faults(acquired,RuntimeDemoConfig(demo_fault_mode='single_edge_exclusion',demo_faulty_edges=('edge-4',)))
        audit = ConsensusEngine().evaluate(faulty)
        self.assertEqual(audit.consensused_valid_state.source_edges,('edge-1','edge-2','edge-3'))
        self.assertEqual([e.edge_id for e in audit.exclusions],['edge-4'])

    def test_flow_dynamics_respond_to_load_without_changing_legacy_currents(self):
        a = MassFlowCompressorSimulator(modulated=False,sample_seconds=5/3,seed=202)
        b = OperationalCompressorSimulator(modulated=False,sample_seconds=5/3,seed=202)
        before = a.step().sensors['mass_flow']
        b.step()
        a.set_demand_target(75)
        b.set_demand_target(75)
        for _ in range(100):
            frame, legacy = a.step(), b.step()
            for sensor in ('temperature','pressure','rpm'):
                self.assertEqual(frame.transmitter_observations[sensor],legacy.transmitter_observations[sensor])
        self.assertGreater(frame.sensors['mass_flow'],before+150)
        current = frame.transmitter_observations['mass_flow'].loop_current_ma
        self.assertAlmostEqual(frame.sensors['mass_flow'],(current-4)/16*1000,places=2)

    def test_trace_event_boundaries_and_interleaved_threads(self):
        rows = [{'acquisition_window':{'start_epoch':1.,'end_epoch':2.}},
                {'acquisition_window':{'start_epoch':3.,'end_epoch':4.}}]
        streams = [[(.9,'outside'),(1.,'read'),(2.,'outside'),(3.5,'write')],[(1.5,'poll'),(4.,'outside')]]
        self.assertEqual(associate(rows,streams),[['read','poll'],['write']])
        rows[1]['acquisition_window']['start_epoch']=1.5
        with self.assertRaises(ValueError):
            associate(rows,streams)

    def test_unfinished_syscall_is_counted_once(self):
        with tempfile.TemporaryDirectory() as temp:
            p=Path(temp)/'trace'
            p.write_text('1.000 read(3, <unfinished ...>\n1.100 <... read resumed>) = 2\n1.200 close(3) = 0\n')
            self.assertEqual(list(trace_events(p)),[(1.,'read'),(1.2,'close')])

    def test_four_validator_infrastructure_keeps_three_validator_default(self):
        for count in (3,4):
            topology=infrastructure(Path('D:/isolated'),validator_count=count)
            self.assertEqual(len(topology['volumes']),count)
            self.assertEqual(sum(k.startswith('abci-') for k in topology['services']),count)
