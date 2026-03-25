"""Deterministic Byzantine-style prototype consensus engine."""

from __future__ import annotations

from parallel_truth_fingerprint.consensus.quorum import required_quorum
from parallel_truth_fingerprint.consensus.trust_model import evaluate_trust
from parallel_truth_fingerprint.contracts.consensus_audit_package import (
    ConsensusAuditPackage,
)
from parallel_truth_fingerprint.contracts.consensus_result import ConsensusResult
from parallel_truth_fingerprint.contracts.consensus_round_input import ConsensusRoundInput
from parallel_truth_fingerprint.contracts.consensus_status import ConsensusStatus
from parallel_truth_fingerprint.contracts.consensused_valid_state import (
    ConsensusedValidState,
)
from parallel_truth_fingerprint.contracts.edge_local_replicated_state import (
    EdgeLocalReplicatedStateContract,
)


class ConsensusEngine:
    """Edge-local deterministic consensus evaluation."""

    def evaluate(self, round_input: ConsensusRoundInput) -> ConsensusAuditPackage:
        trust_ranking, exclusions = evaluate_trust(
            round_identity=round_input.round_identity,
            participating_edges=round_input.participating_edges,
            replicated_states=round_input.replicated_states,
        )

        excluded_edges = {decision.edge_id for decision in exclusions}
        valid_states = tuple(
            state
            for state in round_input.replicated_states
            if state.owner_edge_id not in excluded_edges
        )

        quorum = required_quorum(len(round_input.participating_edges))
        valid_state = None
        status = ConsensusStatus.FAILED_CONSENSUS

        if len(valid_states) >= quorum:
            valid_state = self._build_consensused_valid_state(
                round_input=round_input,
                valid_states=valid_states,
            )
            status = ConsensusStatus.SUCCESS

        result = ConsensusResult(
            round_identity=round_input.round_identity,
            status=status,
            participating_edges=round_input.participating_edges,
            trust_ranking=trust_ranking,
            exclusions=exclusions,
            consensused_valid_state=valid_state,
        )
        return ConsensusAuditPackage(
            round_input=round_input,
            trust_ranking=trust_ranking,
            exclusions=exclusions,
            final_status=status,
            consensus_result=result,
            consensused_valid_state=valid_state,
        )

    def _build_consensused_valid_state(
        self,
        *,
        round_input: ConsensusRoundInput,
        valid_states: tuple[EdgeLocalReplicatedStateContract, ...],
    ) -> ConsensusedValidState:
        """Build the valid state using simple averages over non-excluded edges."""

        sensor_values = {}
        for sensor_name in ("temperature", "pressure", "rpm"):
            values = [
                state.observations_by_sensor[sensor_name].process_data.pv.value
                for state in valid_states
            ]
            sensor_values[sensor_name] = round(sum(values) / len(values), 3)

        return ConsensusedValidState(
            round_identity=round_input.round_identity,
            source_edges=tuple(state.owner_edge_id for state in valid_states),
            sensor_values=sensor_values,
        )
