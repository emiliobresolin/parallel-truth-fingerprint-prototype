# ScenarioTruth.v1

`ScenarioTruth.v1` is an immutable, evaluator-restricted declaration of
scenario truth. It is a planning contract, not evidence that an intervention
occurred, a run succeeded, or a detector result is correct.

The record binds opaque immutable experiment, matrix, predeclared-run, trace,
event, correlation, condition-interval, intervention-interval, provenance and
writer identities. Its only audience is `evaluator_restricted`; its only
namespace is `restricted_truth`; and every result produced by its validators
has `authorization_effect: none`.

Public contracts use opaque IDs only. `validate_public_boundary` rejects direct
truth/scenario/label fields and any declared provenance graph edge that is
unresolved, mutable, restricted, or not detector-facing. This is a declared
map-closure rule, not a claim to detect undeclared covert channels.

The validator reads only injected identity metadata. It performs no I/O,
storage, authentication, authorization, unlock, join, evaluation, scheduler,
controller, detector, or dashboard operation. Story 9.8 remains the owner of
freeze, unlock, join and authorization validation. Once it has validated that
closure, `assess_truth_compatibility` compares only the opaque truth identity
and parent identity tuple, returning a redacted, non-published compatibility
result. Changed parents or truth identity fail closed.

The contract is append-only: a content-bearing change gives a different
content identity. It does not create a storage namespace or claim that its
audience token implements IAM, encryption, ACLs, or credentials. Legacy
runtime scenario labels, configuration, control, MQTT, persistence and UI are
outside this v1 contract and must not be used as inputs.
