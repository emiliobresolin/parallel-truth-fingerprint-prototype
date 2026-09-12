# Frozen blind syscall scores v1

`syscall_blind_scores` is a pure, detector-facing pre-truth boundary for the
custom host-capture track. It validates the exact frozen categorical bundle,
complete-group test partition, fitted vocabulary/preprocessing, capture context,
metric policy, code/runtime identities, and applicable authorization before an
injected predictor is called. It performs no fitting, vocabulary extension,
calibration, truth access, publication, storage, capture, or I/O.

`DetectorScore.v1` records only score and capture lineage: bundle/window/input,
raw and calibrated values, threshold decision, latency, missingness, capture
quality/context, run/workload correlations, and code/runtime identities. Its
closed shape excludes labels, truth, attacks, scenarios, interventions, and
expected outcomes. Invalid or unavailable windows retain an explicit non-normal
outcome with an immutable reason; they are never dropped or converted to normal.

`SyscallScoreManifest.v1` has canonical SHA-256 identities and requires every
planned test window exactly once. A later separately authorized evaluator must
admit the frozen manifest identity, never an alias, mutable bundle, or partial
score stream.
