"""Deterministic agreement of replicated acquired-current observations."""
from parallel_truth_fingerprint.consensus.current_domain import raw_current, same_observation, SPAN_MA, diagnostic_round
from parallel_truth_fingerprint.consensus.quorum import required_quorum
from parallel_truth_fingerprint.contracts.exclusion_decision import ExclusionDecision
from parallel_truth_fingerprint.contracts.exclusion_reason import ExclusionReason
from parallel_truth_fingerprint.contracts.trust_evidence import PairwiseDistanceEvidence, PerEdgeTrustEvidence, SensorDeviationEvidence
from parallel_truth_fingerprint.contracts.trust_ranking import TrustRankEntry, TrustRanking


def evaluate_trust(*, round_identity, participating_edges, replicated_states):
    by_edge = {state.owner_edge_id: state for state in replicated_states}
    if len(set(participating_edges)) != len(participating_edges) or not participating_edges:
        raise ValueError('Unique participating edges are required.')
    if len(by_edge) != len(replicated_states) or set(by_edge) != set(participating_edges):
        raise ValueError('Exactly one replicated view per participant is required.')
    sensors = set(replicated_states[0].observations_by_sensor)
    if not sensors or any(set(s.observations_by_sensor) != sensors for s in replicated_states):
        raise ValueError('Replicated current sensor schemas must agree.')
    for state in replicated_states:
        for payload in state.observations_by_sensor.values():
            raw_current(payload)
            same_observation(payload, payload)
    entries, exclusions, evidence = [], [], []
    quorum = required_quorum(len(participating_edges))
    for edge in participating_edges:
        state = by_edge[edge]
        peers = sorted(p for p in participating_edges if p != edge)
        distances, deviations, normalized = [], [], []
        compatible = 0
        for peer in peers:
            other = by_edge[peer]
            if all(same_observation(state.observations_by_sensor[s], other.observations_by_sensor[s]) for s in sensors):
                compatible += 1
            normalized.append(sum(abs(raw_current(state.observations_by_sensor[s])-raw_current(other.observations_by_sensor[s]))/SPAN_MA for s in sorted(sensors))/len(sensors))
        for sensor in sorted(sensors):
            differences = []
            for peer in peers:
                difference = abs(raw_current(state.observations_by_sensor[sensor])-raw_current(by_edge[peer].observations_by_sensor[sensor]))
                differences.append(difference)
                distances.append(PairwiseDistanceEvidence(peer_edge_id=peer, sensor_name=sensor, distance_value=diagnostic_round(difference), unit='mA'))
            deviations.append(SensorDeviationEvidence(sensor_name=sensor, deviation_value=diagnostic_round(sum(differences)/max(len(peers), 1)), unit='mA'))
        overall = diagnostic_round(sum(normalized)/max(len(peers), 1))
        score = diagnostic_round(1/(1+overall))
        entries.append(TrustRankEntry(edge_id=edge, score=score))
        evidence.append(PerEdgeTrustEvidence(round_identity=round_identity, edge_id=edge, score=score,
            compatible_peer_count=compatible, overall_normalized_deviation=overall,
            sensor_deviations=tuple(deviations), pairwise_distances=tuple(distances)))
        if compatible+1 < quorum:
            exclusions.append(ExclusionDecision(round_identity=round_identity, edge_id=edge,
                reason=ExclusionReason.INCONSISTENT_VIEW,
                detail=f'current-consensus-v2: compatible_peers={compatible}; required={quorum}; exact source event/current agreement'))
    entries.sort(key=lambda item: (-item.score, item.edge_id))
    exclusions.sort(key=lambda item: item.edge_id)
    evidence.sort(key=lambda item: item.edge_id)
    return (TrustRanking(round_identity=round_identity, participating_edges=participating_edges, entries=tuple(entries)),
            tuple(exclusions), tuple(evidence))
