# Consensus v2 G3 qualification

`qualify_consensus_v2` is an offline, pure assessment of references supplied by
the caller. It does not invoke CometBFT, call the Go ABCI app, resolve a
latest/default value, persist anything, or grant permission to activate v2.

The primary configuration, closure, parity fixtures, integration evidence,
versioned-state evidence, sensitivity plan/results, and provenance chain must
all be immutable identities accepted by the injected resolver. Parity requires
the ten preregistered case classes: valid, invalid, missing, stale,
mixed-profile, mixed-unit, boundary, exclusion, tie, and failure.

Any missing supplied evidence produces `incomplete`; an unresolvable identity
produces `blocked`; an observed failure produces `shadow`. A mismatch is blocked
unless it names a separately retained immutable diagnostic. Only an all-pass
closure is `qualified`. In every outcome, `authorization_effect` is `none`;
qualification never authorizes activation, experiments, training, fusion,
deployment, or presentation.
