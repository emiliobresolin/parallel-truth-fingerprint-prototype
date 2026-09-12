# Scientific Governance v1

`scientific-governance.v1` is a read-only contract family. Validation is pure:
it does not read ambient state, write evidence, sample a clock, resolve an
alias, start a service, or execute an activity.

The five immutable record types are `PartitionRecord`, `ScientificFreeze`,
`TruthUnlockRecord`, `TruthJoinRecord`, and `ActivityAuthorization`.
Partition membership is exact and opaque: every inventory group has one role
(`train`, `validation`, `calibration`, `test`, or a profile-approved
`excluded`). A seed is reproducibility metadata, never a substitute for the
published membership list.

Profiles are code-owned and revision-pinned. They define audiences, applicable
roles, boundary requirements, and action scope; a candidate cannot register the
profile that validates it. The permitted action vocabulary is closed. The three
truth actions (`truth_unlock`, `restricted_truth_join`, and `evaluation`) are
evaluator-restricted only. Detector-facing graphs must not contain restricted
truth, locators, or row-level truth values.

Freezes are phase-specific. A blind-scoring closure precedes a pre-truth
evaluation closure; truth unlock, restricted join, and later evaluation each
need a distinct exact authorization. An authorization is a declared permission
for one precomputed scope, not authentication, a scheduler, a completion
receipt, revocation facility, or proof of scientific correctness.

This project deliberately sets no dataset-specific grouping key, partition
ratio, fold count, seed, threshold, duration, delay, or mock measurement here.
Those choices belong to later track owners and must be pinned to parameter and
source evidence. Legacy runtime/training records remain quarantined.

## Ownership and validation boundary

Story 9.6 owns evidence manifests, evaluation envelopes, and publication
closure. Story 9.7 owns qualified persistence. This contract owns only generic
partition, freeze, restricted-truth and activity gates; later dataset and track
stories own actual source inventories, native roles, grouping keys, stage
profiles, scenario truth, and scientific execution. No sentinel profile is a
scientific profile or a substitute for a later owner registration.

The stage vocabulary is closed: `fitting`, `model_selection`, `calibration`,
`threshold_selection`, `blind_scoring`, `fusion`, and
`pretruth_evaluation`. A profile supplies the exact binding slots for its stage.
Blind scoring closes partition/support, bundle, schema, preprocessing,
calibration, threshold, decision schema, and metric protocol. Pre-truth
evaluation additionally requires the exact blind-scoring predecessor and closes
score/decision dispositions plus evaluator/protocol inputs; it cannot bind
truth, a truth join, or an evaluation result.

Partition membership is published before any derived artifact is eligible for a
role. Every opaque inventory group receives exactly one membership or a
profile-approved exclusion backed by immutable evidence. The validator never
prints labels, paths, row counts, timing, scenario names, or truth values.

`TruthUnlockRecord` is evaluator-only and requires one score disposition and
one detector-decision disposition, each with a completion receipt, for every
frozen support unit. Missing, extra, duplicate, or wrong-support dispositions
keep truth locked. `TruthJoinRecord` separately binds the exact unlock and join
authorization. Detector-facing graphs cannot cite restricted truth, unlock, or
join lineage.

An `ActivityAuthorization` is valid only for one closed action token and one
exact profile-defined scope, immutable inputs, prerequisites, output roles, and
recomputed planned-activity digest. `truth_unlock`, `restricted_truth_join`,
and `evaluation` use the `evaluator_restricted` audience only. Approval is a
pure gate result, never activity execution or a global capability.
