# Physical post-truth evaluation v1

`physical_evaluation` is an evaluator-only, pure boundary for Story 13.7. It
joins an already validated `PhysicalScoreManifest.v1` to restricted truth only
when an injected authorization validator accepts the exact post-truth action,
authorization identity, and truth-unlock identity.

The frozen plan binds the score manifest, bundle, threshold, partition, metric
policy, experiment, window/run/event/correlation inventory, declared strata,
and preregistered sensitivity thresholds by immutable identities. A join must
match every one of those identities. Commanded regime and transition identities
are separate fields from scenario, severity, and restricted anomaly truth, so a
reference transition is never inferred to be anomalous.

Evaluation is read-only: it cannot score, alter decisions, calibrate a
threshold, fit preprocessing, unlock truth, write evidence, or publish. It
reports only declared metrics supported by the supplied closure; inapplicable
metrics retain an immutable reason. Invalid or incomplete closure returns an
immutable `invalid` record with diagnostic codes rather than silently dropping
scores, strata, failed/unavailable outcomes, sensitivity alternatives, quality,
resource evidence, or limitations.
