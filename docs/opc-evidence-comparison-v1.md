# OPC evidence comparison v1

`validate_and_compare_opc_evidence` is an offline, pure gate between an
independent `ScadaObservation.v2` projection and a correlated
`ConsensusDecision.v2` projection. It has no OPC client, persistence, control,
dashboard, or consensus authority.

The gate accepts only the same-profile `same_profile_raw_current` basis in
`mA`. It requires immutable, resolver-confirmed identities for both inputs, the
endpoint/namespace/snapshot/profile closure, policy/basis, source references,
and three separately bound parameter identities: freshness, source/server skew,
and comparison tolerance. It never supplies a legacy tolerance or current
default. The parameter values are intentionally not read by this gate, so it
reports an eligible difference but no pass/fail classification.

All malformed, unavailable, stale, non-Good, timestamp-invalid, uncorrelated,
mixed-profile, mixed-unit, shared-branch, unresolved, or non-finite-value
inputs return `eligible=False`, an explicit diagnostic, and no difference.
The returned record is non-authorizing and must not be treated as persistence
permission or a mutation of either source branch.
