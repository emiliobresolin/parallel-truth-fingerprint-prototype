# Consensus v2 reference evaluator

`parallel_truth_fingerprint.consensus_v2.reference_evaluator` is a pure,
offline, non-activating boundary. It accepts already-validated immutable
`ConsensusRoundInputV2` and `ConsensusParameterSet` declarations plus their
explicit validation outcomes. It does not resolve records, access runtime
state, or accept a callable, plugin, dynamic import, float, default, or legacy
v1 calculation.

The evaluator requires an accompanying immutable public numeric projection
(`ConsensusEvaluationObservationV2`) for every input reference, and a closed
data-only operation (`ConsensusOperationClosureV2`). Numbers are canonical
base-10 strings parsed as `Decimal`; floats, implicit rounding, callables, and
plugins are not accepted. The sole operation registry entry is the exact
canonical `mean_current_residual` v1 definition, bound to its content hash,
conformance-vector hash, residual limit, participant minimum, reason IDs, and
trace budget. It produces a deterministic residual ranking or an explicit
`failure` with `no_ranking`.

Absent or mismatched projections, operation closure, parameter closure, or
trace budget return deterministic `blocked`, no decision, and no operation
events (`CV2_REFERENCE_OPERATION_INPUT_UNAVAILABLE` or a specific closure
diagnostic).

This is fail-closed behavior, not consensus activation, persistence, G3
qualification, or a scientific claim. A later contract revision must supply
the missing immutable public closure; legacy runtime behavior cannot fill it.
