# Consensus v2 Go/ABCI shadow bridge

`abci/consensus_app/internal/app/v2_bridge.go` is an isolated, in-memory
boundary for the `ConsensusABCI.v2` transaction envelope. It is intentionally
not registered with `ConsensusApplication`: the existing v1 decoder, state,
`AppHash`, Query path, replay behavior and CometBFT runtime remain unchanged.

The bridge accepts only canonical JSON with exact fields, no duplicate or
unknown keys, pinned SHA-256 identities, a closed `Consensus.v2` input and a
fixed `consensus_v2_shadow` route. It rejects v1 payloads, mutable aliases,
non-canonical wire forms, missing identity closure and unpinned operation or
parameter identities. No v1-to-v2 conversion exists.

An application supplies a closed evaluator through `ConsensusV2Evaluator`.
The adapter has no resolver, plugin loading, storage, query, transport, clock,
control, actuator, or activation capability. It accepts only canonical v2
decision bytes and reports malformed input/evaluation failure as an explicit
shadow-only result with no decision bytes. A valid failure decision has an
empty ranking; it is not success by omission.

The Go unit tests use only conspicuous synthetic SHA-256 fixture identities and
never start CometBFT or any service. They verify canonical decoding, legacy and
unknown-field rejection, explicit failure behavior, and the absence of durable
v2 writes. They provide codec/adapter evidence only. They do not establish
real-CometBFT G3 evidence, route activation, durable v2 state, ABCI Query,
restart/replay/rollback support, or any physical/control result; those remain
the respective later-story boundaries.
