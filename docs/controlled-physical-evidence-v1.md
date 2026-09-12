# Controlled Physical Evidence v1

Story 10.6 currently provides only offline admission and collection-closure
checks. It does not execute an experiment, command hardware or an emulator,
start a broker, write a repository, emit a receipt, publish a manifest, read a
system clock, or create scientific evidence.

## Admission order

`PhysicalRunRequest` is a non-authorizing, non-published run-scope projection.
It is explicitly neither `RunManifest.v1` nor a publication receipt. Before a
separate owner can cause a run-created side effect, the pure gate requires:

1. An execution-eligible frozen `ExperimentSpec.v1` and its exact matrix row.
2. Exact immutable resolution of the projection, input trace, profile,
   parameter-gate result, and repository-qualification identities.
3. An exact qualified repository report.
4. Two independent delegated approvals in the exact projection scope:
   `feature_activation` and `experiment_execution`.
5. A third independent `physical_acquisition` approval only for declared
   `physical_hardware` modality.
6. Unique, positive, closed stream sequence intervals.

The gate has no default, alias, mutable lookup, planning-record substitution,
or authorization-grant behavior. Every resolver and authorization decision is
injected by the owning caller, and a rejected prerequisite creates no state.

## Collection closure

`validate_stream_completeness` preserves supplied `StreamRecord` objects
unchanged and reports, rather than repairs, missing, duplicate, divergent,
out-of-order, scope-mismatched, out-of-declaration, and hash-mismatched facts.
Stream identity is the exact `(stream_id, edge_id, sensor_id)` tuple; an edge
or sensor cannot be inferred from a tag or substituted by an aggregate.

The result is `complete` only if no reported defect exists. It has no G2,
signal qualification, recovery, retry, command, timing, outcome, or truth
interpretation. A caller that owns persistence must retain an incomplete result
and all available records without silently normalizing or replaying them.

## Public/restricted boundary and downstream owners

This module accepts no restricted-truth locator, meaning, parent, or outcome.
Restricted condition evidence remains owned by Stories 10.5 and 9.8. Immutable
object-first persistence, byte read-back, RunManifest assembly, and receipt-last
publication remain owned by Stories 9.6/9.7 and the later persistence adapter.
Story 10.7 owns signal qualification and G2; Epic 17A owns synchronization and
fusion eligibility.

## Current limitation

The formal upstream profile, source, parameter, mock-admission, provenance,
qualified repository, and activity-authorization records must be provided by
their owning implementations. Test fakes prove only this boundary's protocol;
they never qualify storage, authorize a run, or represent physical evidence.
Legacy runtime, MQTT, SCADA, dashboard, consensus, training, network, and
local-demo paths are intentionally not imported.
