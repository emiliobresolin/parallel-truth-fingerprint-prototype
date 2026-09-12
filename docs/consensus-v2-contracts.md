# Consensus v2 contracts

`consensus_v2` is an offline, immutable contract boundary. It defines canonical
input and decision records only; it neither selects parameters nor calculates
residuals, rankings, or trust. It cannot contact CometBFT, storage, MQTT,
devices, dashboards, or controls.

The only direct raw comparison form is `same_profile_raw_current`: all inputs
must reference the one identical profile and unit `mA`. A cross-profile or
cross-sensor input must instead declare `dimensionless_profile_residual`, with
at least two profile identities and immutable uncertainty-parameter identities.
The operation itself belongs to later parameter/reference-evaluator stories.

Every input binds an immutable G2-qualified public qualification result,
canonical observation hashes, positive source sequences, opaque correlation
identities, profiles, parameters, and a hashed versioned basis. Resolver-bound
validation additionally rejects non-public, mutable, unknown, or declared
forbidden semantic/provenance dependencies. Diagnostics and every record use
`authorization_effect: none`.

A successful decision ranks every included participant. A failure has no
ranking and no included participant; every non-included participant has one
immutable reason and nonempty evidence closure. This is representation only,
not consensus activation or a persistence permission.
