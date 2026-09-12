# Physical feature schema v2

`parallel_truth_fingerprint.physical_features` is the current-domain, pure
feature boundary for `SignalObservation.v2`. A schema has an ordered list of
source-addressed features, a semantic schema ID and version, and a SHA-256
content identity derived from its canonical declaration. It declares the source
representation, unit, data type, compatible profile identities, missingness
policy, frozen preprocessing identity, and parameter-evidence references.

The builder projects only declared canonical observation values. It does not
read hardware, resolve aliases, fit scalers, reimplement transmitter conversion,
or read truth, labels, scenario semantics, future outcomes, detector decisions,
or fusion outputs. Operating context is an injected value that must carry an
immutable frozen experiment-specification identity and parameter evidence.

Features marked `excluded` or `unavailable` remain explicit. Profile mismatch,
unknown source path, unresolved authority, missing required feature, and
incompatible context all fail closed. Existing mixed-scale models are outside
this boundary: they are `LEGACY_BASELINE` under their v1 contract and never a
v2 schema, dataset, or detector path.
