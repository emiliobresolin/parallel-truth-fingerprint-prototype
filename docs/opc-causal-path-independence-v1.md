# OPC/Consensus Causal-Path Independence v1

`CausalPathIndependenceResult.v1` is a deterministic, identity-only assessment
of a supplied controlled test matrix. It does not start an OPC UA server or
client, contact a network, run consensus, use a cache, publish evidence, or
authorize qualification.

Each baseline/varied trace preserves immutable identities for the shared
pre-consensus snapshot, writer, server, client, OPC condition and observation,
consensus configuration/input/decision, optional comparison, and both branch
lineages. The OPC and consensus lineage fields must point to that trace's exact
snapshot. The caller injects an immutable-object resolver; missing identities
are incomplete and unresolvable identities are blocked.

The required matrix has exactly four controlled variations:

- `consensus_only`: snapshot and OPC observation must remain unchanged while a
  consensus configuration or input changes.
- `opc_only`: snapshot and consensus configuration, input, and decision must
  remain unchanged while the declared OPC condition changes.
- `common_source`: the snapshot must change, with each resulting branch bound
  directly to its own new snapshot.
- `opc_unavailable`: an unavailable, delayed, or newly-read OPC state is
  explicit while the consensus branch continues unchanged.

Every trace forbids a fallback (`opc_fallback_kind` must be `none`). An
available or newly-read OPC state requires a retained valid observation;
unavailable or delayed states cannot fabricate one. A detected cross-branch
change or fallback yields `violated`, which prevents this assessment from
demonstrating independent-OPC causal behavior. This is not Gate G4 and grants
no activation or scientific authority.

A passing result is deliberately limited to logical and transport-path
independence in the controlled prototype. It makes no claim about independent
physical instrumentation, plant redundancy, or real-world SCADA validation.
