# Consensus v2 versioned state boundary

`parallel_truth_fingerprint.consensus_v2.versioned_state` is an offline,
side-effect-free contract boundary for Story 11.5. It introduces no ABCI
database, durable application key, service, query handler, or runtime route.

`VersionedConsensusState` binds one byte sequence to an explicit `v1` or `v2`
route, schema identity, storage-key namespace, height, AppHash, byte hash and
content identity. A v1 record is not a v2 record: cross-version schemas,
unqualified keys, malformed bytes and invalid identities are rejected.

`VersionedQuery` has no default/latest version. `resolve_versioned_query` only
selects a record with the requested version, schema and exact key. Missing and
ambiguous records are explicit outcomes/errors; it never attempts a decoder
fallback.

`V2ToV1Projection` is a separately versioned, one-way evidence descriptor.
It binds declared projected fields to its source v2 state identity and cannot
create absent facts or write to historical state.

`qualify_restart` accepts only pinned immutable code/runtime identities and an
ordered exact reconstruction of state identities. Any missing, corrupt or
reordered replay is rejected. `ConsensusRoundEvidence` makes the immutable
references needed for an audit reconstruction explicit. `RollbackEvidence`
records an authorization-backed version route selection; it has no mutation or
deletion operation.
