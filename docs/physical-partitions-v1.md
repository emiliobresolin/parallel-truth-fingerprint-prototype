# Physical partitions and windows v1

`parallel_truth_fingerprint.evidence.physical_partitions` is the offline,
pure admission layer for Story 13.2. It does not acquire, fit, persist,
authorize, publish, or join truth.

A `PhysicalPartition` assigns each immutable, complete run to exactly one of
`train`, `validation`, `calibration`, or `test`. The validator rejects an
empty partition, duplicate run membership, unknown role, non-immutable or
unresolved references, and any authorization effect.

`build_physical_windows` accepts only observations with exact partition and
schema identities. A window must be complete and contiguous within one run,
experiment, phase, opaque scenario boundary, profile, schema, and partition.
Gaps, invalid observations, malformed parameter evidence, cross-boundary
windows, unresolved provenance, and padding other than explicit `none` reject
the candidate. The returned detector-facing `PhysicalWindow` carries source
run, observation range, partition, schema, preprocessing, quality, and
exclusions only; it has no label, truth, expected outcome, or scenario field.

`PreprocessingFit` is validated against the exact complete set of
normal-eligible training runs. Its schema, profile, ordered feature identity,
missingness policy, algorithm, parameter evidence, and output hash are
immutable. Application is permitted only to validation, calibration, test, or
live roles and only when every frozen identity matches exactly. The module has
no operation that fits or updates a preprocessing state during application.

All failures are returned as deterministic `PartitionValidation` diagnostics.
Callers must treat `accepted=False` as a hard rejection: invalid candidate
inputs cannot proceed to model comparison, calibration, or test evaluation.
