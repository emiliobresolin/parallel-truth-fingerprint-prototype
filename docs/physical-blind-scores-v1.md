# Frozen blind physical scores v1

`physical_blind_scores` creates detector-facing `DetectorScore.v1` records
only after the exact immutable physical bundle, declared environment,
partition, frozen preprocessing, frozen threshold, profile, code/runtime, and
blind-scoring authorization validate. Dependencies are injected; the module
does not fit, tune, select, calibrate, impute, use aliases, read truth, or
perform I/O.

Every planned test window is represented in `PhysicalScoreManifest.v1` exactly
once. A valid result contains raw and calibrated scores and a normal or
anomalous decision. Invalid or unavailable paths preserve a record with no
numeric score, an explicit non-normal decision, and an immutable reason
identity; they cannot be silently filtered into a successful stream.

The contract field set is deliberately closed and carries no truth, scenario,
attack, intervention, label, or expected-outcome data. Score and manifest IDs
are canonical SHA-256 content addresses. `validate_physical_score_manifest`
requires exact inventory closure before its immutable manifest identity can be
accepted by a later, separately authorized publisher or evaluator.
