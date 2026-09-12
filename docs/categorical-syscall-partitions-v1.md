# Categorical syscall partitions and windows v1

`parallel_truth_fingerprint.evidence.syscall_partitions` is Story 14.4's
offline, pure admission boundary. It does not capture syscalls, retrieve raw
bytes, fit preprocessing, persist evidence, authorize activity, or join truth.

`SyscallPartition` assigns every declared immutable capture group to exactly
one of `train`, `validation`, `calibration`, or `test`. Each member binds the
complete run, manifest, boot, session, container, process scope, capture group,
and batch closure. Empty partitions, duplicate capture groups, unknown roles,
empty batch sets, unresolved references, and authorization effects reject.

`canonicalize_categorical_syscalls` keeps the supplied categorical call name,
direction, source identity, sequence, timestamp, raw-segment lineage, and
kernel/ABI context intact. It neither maps unknown calls to a guess nor drops
them. Missing categorical fields, unresolved provenance, duplicate/ambiguous
raw-segment sequence positions, and explicit duplicates reject.

`build_syscall_windows` accepts only exact partition/schema and declared capture
scope/batch closure. A complete window cannot cross a run, boot, session,
container, process scope, capture group, raw segment, batch, collector, filter,
kernel, ABI, schema, partition, exclusion policy, gap, or loss-policy boundary.
Padding other than explicit `none` is rejected; absent or affected evidence is
never imputed as a normal call. Returned detector-facing windows expose only
opaque lineage, quality, exclusion, and preprocessing identities—never truth,
labels, scenario meaning, or expected outcomes.

`validate_syscall_preprocessing_fit` admits an already-fitted immutable
vocabulary/frequency state only when its input closure is exactly all
normal-eligible training runs. It records immutable vocabulary mapping,
unknown-event policy, algorithm, parameter, code, input-event and output hash
identities. Validation, calibration, test, truth, and future evidence are not
eligible fit inputs.

All failures are deterministic `SyscallPartitionValidation` diagnostics and
must be treated as hard rejection by callers.
