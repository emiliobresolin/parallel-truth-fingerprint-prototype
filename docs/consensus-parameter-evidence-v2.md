# Consensus Parameter Evidence v2

`ConsensusParameterSet.v2` is a frozen configuration declaration, not an
evaluator or an activation record. It binds the exact v1 numeric inventory,
required parameter set, accountable gate result, parameter revisions, primary
decision, scientific freeze, partition lock, analysis plan, and operation-policy
identity. The validator accepts these only from injected read-only resolvers and
always reports `authorization_effect: none`.

Every required numeric consumer slot is present exactly once and supplies its
revision ID, revision content hash, class, quantity, unit, dimension, profile,
and experiment scope. IDs such as `latest`, `current`, `default`, `legacy`, and
`v1` are rejected. V1 scales, tolerances, weights, thresholds, and rounding
remain quarantined legacy-reproduction material and cannot become a v2 default.

Same-profile raw-current comparison may not introduce a residual input list.
Cross-profile comparison must name a distinct residual policy with canonical
operation/conformance identity, declared slot/unit/dimension closure, and at
least one explicit dimensionless measured or derived uncertainty binding.

Preregistered factors require their exact pre-test `DecisionRecord`. The
selected primary or sensitivity alternative must be named by the frozen plan;
an outcome cannot promote an undeclared alternative. A stale decision, freeze,
partition lock, parameter revision, gate, or any scope/profile mismatch produces
a `blocked` result for later owners to enact.

The current formal catalog is intentionally blocked until its complete evidenced
parameter universe has been supplied. A structurally valid test fixture does not
assert an admissible scientific configuration, execute consensus, calculate a
residual/trust/ranking, access truth, or authorize any activity.
