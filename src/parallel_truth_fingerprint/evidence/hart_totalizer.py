"""Documented HART SV lineage and episode-local counter increments.

The totalizer is a device-derived accumulated measurement, not a second
independent flow sensor. Absolute accumulated mass never enters the tensors.
"""
from collections import defaultdict
import math

from parallel_truth_fingerprint.sensor_simulation.mass_flow import validate_totalizer_configuration

SENSORS = ('mass_flow', 'pressure', 'rpm', 'temperature')
CONDITIONS = ('normal_stable', 'legitimate_transition', 'replay_same_regime', 'replay_hiding_change')
FEATURES = tuple(f'{domain}.{sensor}.loop_current_normalized'
                 if sensor != 'totalizer1_increment' else f'{domain}.mass_flow.totalizer1_increment_normalized'
                 for domain in ('physical', 'supervisory')
                 for sensor in (*SENSORS, 'totalizer1_increment'))


def validate_collection_contract(frozen):
    declared = 'hart_totalizer_configuration' in frozen
    marked = frozen.get('version') in {'documented-noise-hart-totalizer-v1','documented-noise-generic-receiver-hart-v1'}
    if declared != marked:
        raise ValueError('HART totalizer protocol version/configuration mismatch.')
    if marked:
        if frozen.get('version') == 'documented-noise-generic-receiver-hart-v1':
            from parallel_truth_fingerprint.evidence.generic_plant import validate_generic_contract
            validate_generic_contract(frozen)
        else:
            validate_totalizer_configuration(frozen['hart_totalizer_configuration'])
        if (frozen.get('auxiliary_measurement_domain') != 'hart_totalizer_mass_kg'
                or frozen['parameters']['edge_count'] != 4):
            raise ValueError('HART totalizer contract requires its kg domain and four edges.')
    return marked


def number(value, name):
    if isinstance(value, bool) or not isinstance(value, (int, float)) or not math.isfinite(value):
        raise ValueError(f'Finite numeric {name} is required.')
    return float(value)


def counter(state):
    value = number(state['behavioral_sensor_values']['mass_flow'].get('totalizer1_kg'), 'HART Totalizer1 kg')
    if value < 0:
        raise ValueError('HART Totalizer1 cannot be negative.')
    return value


def currents(state):
    return [(number(state['behavioral_sensor_values'][s].get('loop_current_ma'), 'current')-4)/16 for s in SENSORS]


def build_source_evidence(round_input, valid_state, persisted, *, include_all_sensors=False):
    """Export actual selected raw SV loaded back from persistence, not simulator state."""
    from parallel_truth_fingerprint.consensus.current_domain import source_event_id
    snapshot = persisted['validated_state']['structured_payload_snapshot']
    payloads = {state.owner_edge_id: state.observations_by_sensor['mass_flow']
                for state in round_input.replicated_states if state.owner_edge_id in valid_state.source_edges}
    selected = snapshot['selected_source_edge_id']
    if (selected not in payloads or tuple(persisted['consensus_context']['source_edges']) != valid_state.source_edges
            or snapshot['payloads_by_sensor']['mass_flow'] != payloads[selected].to_dict()
            or persisted['round_identity']['round_id'] != valid_state.round_identity.round_id):
        raise ValueError('Persisted HART selected source differs from actual agreed acquisition.')
    result = {'artifact_key': persisted['artifact_key'], 'selected_source_edge_id': selected,
            'persisted_round_id': persisted['round_identity']['round_id'],
            'persisted_source_snapshot': snapshot,
            'source_payloads_by_edge': {edge: payload.to_dict() for edge, payload in payloads.items()},
            'source_event_ids_by_edge': {edge: source_event_id(payload) for edge, payload in payloads.items()}}
    if include_all_sensors:
        selected_payloads = snapshot['payloads_by_sensor']
        all_payloads = {sensor: {
            state.owner_edge_id: state.observations_by_sensor[sensor]
            for state in round_input.replicated_states
            if state.owner_edge_id in valid_state.source_edges
        } for sensor in selected_payloads}
        all_identities = {}
        for sensor, replicas in all_payloads.items():
            if (set(replicas) != set(valid_state.source_edges)
                    or selected not in replicas
                    or selected_payloads[sensor] != replicas[selected].to_dict()):
                raise ValueError('Persisted generic source differs from actual selected acquisition.')
            identities = {edge: source_event_id(payload) for edge, payload in replicas.items()}
            if (len(set(identities.values())) != 1
                    or any(payload.process_data.loop_current_ma != valid_state.sensor_values[sensor]
                           or payload.to_dict() != selected_payloads[sensor]
                           for payload in replicas.values())):
                raise ValueError('Generic source replicas differ from actual current/source agreement.')
            all_identities[sensor] = identities
        result['source_payloads_by_sensor_by_edge'] = {
            sensor: {edge: payload.to_dict() for edge, payload in replicas.items()}
            for sensor, replicas in all_payloads.items()}
        result['source_event_ids_by_sensor_by_edge'] = all_identities
    return result


def validate_source_evidence(row, observation):
    """Bind snapshots/SCADA to selected persisted raw HART and quorum replicas."""
    import json
    from parallel_truth_fingerprint.consensus.current_domain import source_event_id
    from parallel_truth_fingerprint.edge_nodes.common.mqtt_io import deserialize_payload
    evidence = row.get('hart_source_evidence')
    if not isinstance(evidence, dict):
        raise ValueError('Missing selected/persisted raw HART source evidence.')
    source_edges = row['consensus_source_edges']
    by_edge, identities = evidence['source_payloads_by_edge'], evidence['source_event_ids_by_edge']
    if (set(by_edge) != set(source_edges) or set(identities) != set(source_edges)
            or len(source_edges) < 3 or len(set(source_edges)) != len(source_edges)
            or not set(source_edges).issubset(row['edge_membership'])):
        raise ValueError('HART raw source evidence differs from winning quorum.')
    selected = evidence['selected_source_edge_id']
    snapshot = evidence['persisted_source_snapshot']
    if (selected not in source_edges or snapshot['selected_source_edge_id'] != selected
            or not evidence.get('artifact_key') or evidence.get('persisted_round_id') != row['round_id']
            or evidence.get('artifact_key') != row.get('baseline_persisted_artifact_key')):
        raise ValueError('Persisted HART source owner is not an agreed source.')
    raw = snapshot['payloads_by_sensor']['mass_flow']
    if raw != by_edge[selected]:
        raise ValueError('Persisted HART payload differs from selected raw replica.')
    expected_identity = source_event_id(deserialize_payload(json.dumps(raw)))
    for edge, payload in by_edge.items():
        actual_identity = source_event_id(deserialize_payload(json.dumps(payload)))
        if actual_identity != expected_identity or identities[edge] != actual_identity:
            raise ValueError('HART raw SV/source identity disagrees across winning replicas.')
        if payload['process_data']['loop_current_ma'] != row['consensused_values']['mass_flow']:
            raise ValueError('HART source current differs from committed current.')
    if (raw['process_data'].get('sv') != observation.get('sv')
            or raw['process_data']['sv']['value'] != counter(row['physical_scada'])):
        raise ValueError('Persisted raw HART SV differs from acquisition snapshot/SCADA.')


def validate_all_source_evidence(row, observations):
    """Bind every generic raw source to its actual persisted/quorum observation.

    These comparisons remain exact even when numerical reconstruction of the
    simulated plant permits floating-point tolerance. Wall-clock acquisition
    windows are distinct from the simulated clock and conditioning intervals.
    """
    import json
    from datetime import datetime
    from parallel_truth_fingerprint.consensus.current_domain import source_event_id
    from parallel_truth_fingerprint.edge_nodes.common.mqtt_io import deserialize_payload

    validate_source_evidence(row, observations['mass_flow'])
    evidence = row['hart_source_evidence']
    snapshot = evidence['persisted_source_snapshot']
    selected = evidence['selected_source_edge_id']
    source_edges = row['consensus_source_edges']
    sensor_payloads = evidence.get('source_payloads_by_sensor_by_edge')
    sensor_identities = evidence.get('source_event_ids_by_sensor_by_edge')
    if (not isinstance(sensor_payloads, dict) or not isinstance(sensor_identities, dict)
            or set(sensor_payloads) != set(observations)
            or set(sensor_identities) != set(observations)
            or set(snapshot['payloads_by_sensor']) != set(observations)):
        raise ValueError('Missing all-sensor generic source proof.')
    if (sensor_payloads['mass_flow'] != evidence['source_payloads_by_edge']
            or sensor_identities['mass_flow'] != evidence['source_event_ids_by_edge']):
        raise ValueError('Generic and HART totalizer source proofs disagree.')
    acquisition = row.get('acquisition_window')
    if not isinstance(acquisition, dict):
        raise ValueError('Missing actual acquisition window for generic sources.')
    start = number(acquisition.get('start_epoch'), 'acquisition start')
    end = number(acquisition.get('end_epoch'), 'acquisition end')
    if start >= end:
        raise ValueError('Actual acquisition window must be ordered.')

    def identity(raw):
        if not isinstance(raw, dict) or raw.get('protocol') != 'HART':
            raise ValueError('Generic raw source protocol must be HART.')
        timestamp = raw.get('timestamp')
        if not isinstance(timestamp, str):
            raise ValueError('Generic raw timestamp must be timezone-aware.')
        try:
            parsed = datetime.fromisoformat(timestamp.replace('Z', '+00:00'))
            if parsed.tzinfo is None or parsed.utcoffset() is None:
                raise ValueError('Generic raw timestamp must be timezone-aware.')
            epoch = parsed.timestamp()
        except (ValueError, OverflowError, OSError) as error:
            raise ValueError('Generic raw timestamp must be timezone-aware and valid.') from error
        if not math.isfinite(epoch) or not start <= epoch <= end:
            raise ValueError('Generic raw timestamp is outside actual acquisition window.')
        return source_event_id(deserialize_payload(json.dumps(raw)))

    for sensor in observations:
        replicas, identities = sensor_payloads[sensor], sensor_identities[sensor]
        if (not isinstance(replicas, dict) or not isinstance(identities, dict)
                or set(replicas) != set(source_edges) or set(identities) != set(source_edges)):
            raise ValueError('Generic sensor proof differs from winning quorum.')
        raw = snapshot['payloads_by_sensor'][sensor]
        if replicas[selected] != raw:
            raise ValueError('Generic persisted payload differs from selected raw replica.')
        expected_identity = identity(raw)
        expected_current = row['consensused_values'][sensor]
        if raw['process_data']['loop_current_ma'] != expected_current:
            raise ValueError('Generic persisted source current differs from committed current.')
        for edge, payload in replicas.items():
            actual_identity = identity(payload)
            if (payload != raw or actual_identity != expected_identity or identities[edge] != actual_identity
                    or payload['process_data']['loop_current_ma'] != expected_current):
                raise ValueError('Generic raw source payload/identity/current disagrees across winning replicas.')


def validate_rows(rows, frozen):
    generic=(frozen.get('version')=='documented-noise-generic-receiver-hart-v1'
             or 'generic_plant_configuration' in frozen)
    if generic:
        from parallel_truth_fingerprint.evidence.generic_plant import validate_generic_contract
        validate_generic_contract(frozen)
    else:
        validate_totalizer_configuration(frozen.get('hart_totalizer_configuration'))
    interval = number(frozen['parameters']['interval_seconds'], 'interval')
    if frozen['parameters']['edge_count'] != 4 or interval <= 0:
        raise ValueError('HART totalizer evaluation requires four edges and positive cadence.')
    previous = None
    by_id = {r['round_id']: r for r in rows}
    if len(by_id) != len(rows):
        raise ValueError('Duplicate source round.')
    for row in rows:
        generation = row['generation']
        snap = generation['acquisition_snapshot']
        if generic:
            if snap['metadata'].get('hart_totalizer_configuration') != frozen['hart_totalizer_configuration']:
                raise ValueError('Generic acquired HART counter recipe differs.')
        else:
            validate_totalizer_configuration(snap['metadata'].get('hart_totalizer_configuration'))
        observation = snap['transmitter_observations']['mass_flow']
        sv = observation.get('sv')
        if (not isinstance(sv, dict) or sv.get('unit') != 'kg'
                or sv.get('description') != 'Totalizer_1_Mass'):
            raise ValueError('Acquired HART SV must be Totalizer1 mass in kg.')
        value = number(sv.get('value'), 'acquired HART SV')
        if value != counter(row['physical_scada']) or value != snap['metadata'].get('hart_totalizer1_kg'):
            raise ValueError('HART SV differs from its acquired/physical reference.')
        validate_source_evidence(row, observation)
        if previous:
            elapsed = number(generation['simulation_seconds'], 'simulation time')-number(previous['generation']['simulation_seconds'], 'simulation time')
            if row['index'] != previous['index']+1 or (not generic and not math.isclose(elapsed, interval, rel_tol=1e-9, abs_tol=1e-7)):
                raise ValueError('Acquisition cadence or ordering differs from the declared simulation.')
            if value < counter(previous['physical_scada']):
                raise ValueError('Unexpected HART totalizer reset/decrease.')
        for view in row['views']:
            if view.get('historical_state'):
                source = view['historical_state']['source_round_id']
                if source not in by_id or by_id[source]['phase'] != 'source':
                    raise ValueError('HART replay must use acquired reserved source.')
                expected = counter(by_id[source]['physical_scada'])
                if counter(view['historical_state']) != expected or counter(view['scada_state']) != expected:
                    raise ValueError('Replay failed to preserve historical HART totalizer.')
            elif counter(view['scada_state']) != value:
                raise ValueError('Normal HART supervision differs from acquisition.')
        previous = row
    if generic:
        from parallel_truth_fingerprint.evidence.generic_plant import validate_generic_rows
        validate_generic_rows(rows,frozen)
    return interval


def feature_vectors(states, reference_mass_kg):
    """First sample warms counter history; consecutive increments follow."""
    reference = number(reference_mass_kg, 'reference mass')
    if reference <= 0:
        raise ValueError('Positive fixed totalizer normalization is required.')
    result = []
    for previous, current in zip(states, states[1:]):
        delta = counter(current)-counter(previous)
        if delta < 0:
            raise ValueError('Counter reset/decrease inside an episode.')
        result.append(currents(current)+[delta/reference])
    return result


def matched_currents(window):
    return [sample[:4]+sample[5:9] for sample in window]


def prepare(rows, frozen, *, technical=False):
    """Split observations, then difference and window; no shared partition history."""
    interval = validate_rows(rows, frozen)
    reference = number(frozen['mass_flow_configuration']['upper_range_kg_h'], 'configured upper flow')*interval/3600
    training = [r for r in rows if r['phase'] == 'train']
    calibration = [r for r in rows if r['phase'] == 'calibration']
    expected = (16, 12) if technical else (120, 60)
    if (len(training), len(calibration)) != expected:
        raise ValueError('Unexpected fixed training/calibration support.')
    split = int(len(training)*.6)
    partitions = {'fit': training[:split], 'validation': training[split:], 'calibration': calibration}
    tensors, lineage = {}, {}
    for name, selected in partitions.items():
        vectors = feature_vectors([r['physical_scada'] for r in selected], reference)
        tensors[name] = [[vectors[i]+vectors[i], vectors[i+1]+vectors[i+1]] for i in range(len(vectors)-1)]
        lineage[name] = [r['round_id'] for r in selected]
    groups = defaultdict(list)
    for row in rows:
        for view in row['views']:
            if view['condition'] not in CONDITIONS:
                raise ValueError('Unknown HART condition.')
            groups[row['phase'], row['block'], view['condition']].append((row, view))
    examples = []
    for (_, block, condition), selected in groups.items():
        if [r['offset'] for r, _ in selected] != list(range(frozen['parameters']['block_rounds'])):
            raise ValueError('Incomplete/noncontiguous HART episode.')
        physical = feature_vectors([r['physical_scada'] for r, _ in selected], reference)
        supervisory = feature_vectors([v['scada_state'] for _, v in selected], reference)
        for i in range(1, len(physical)):
            row, view = selected[i+1]
            sources = selected[i-1:i+2]
            examples.append({'round_id': row['round_id'], 'block': block, 'offset': row['offset'],
                'condition': condition, 'boundary': False,
                'physical_source_ids': [r['round_id'] for r, _ in sources],
                'supervisory_source_ids': [(v['historical_state']['source_round_id'] if v.get('historical_state') else r['round_id']) for r, v in sources],
                'input_window': [physical[i-1]+supervisory[i-1], physical[i]+supervisory[i]],
                'comparator_anomalous': bool(view['comparison']['divergent_sensors'])})
    expected_count = 8 if technical else 560
    if len(examples) != expected_count:
        raise ValueError('Unexpected HART test support after uniform two-record warmup.')
    return tensors, lineage, examples, reference
