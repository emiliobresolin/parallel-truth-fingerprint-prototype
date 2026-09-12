# SignalObservation.v2

`SignalObservation.v2` is an immutable, detector-facing, primary-per-edge physical record. It preserves one source event's raw current (`mA`), quality trace, normalized span (`one`) and profile-owned engineering representation. It is not an aggregate, persistence format, acquisition route, consensus result, or authorization.

The record has fixed contract/version/role fields, detector-safe scope and event identities, distinct source and observed fixed-microsecond UTC timestamps, clock/correlation evidence, semantic identity, admitted-profile/parameter closure, raw current, diagnostics, quality trace, two representation slots, and `observation_content_id`.

The canonical preimage is ASCII JSON with sorted keys and compact separators over every record field except `observation_content_id`; its identity is lowercase `sha256:<hex>`. Event identity is scoped by experiment/run/round/edge/sensor/stream/boot/session plus event ID. Sequence identity uses the same scope plus a positive source sequence. Cross-record collision, ordering and completeness analysis remain outside this contract.

Construction is pure and resolver-bound: raw facts are retained, resolver-owned quality/transform output is added, then canonical identity is calculated. Validation reparses strictly, resolves detector-safe identities/audience/semantic/profile closure through the injected snapshot, and compares quality and representations against a recomputation. Callers cannot provide derived fields.

Clock and correlation leaves preserve evidence states only; they never establish join, synchronization, fusion, or authorization eligibility. Unknown fields, duplicate JSON keys, noncanonical decimals/timestamps, JSON numeric current values, v1 shapes, aggregate roles, and mismatching hashes fail closed with `SOV2_*` structured diagnostics. The legacy HART/simulation/MQTT/persistence/consensus/SCADA path is quarantined and cannot be promoted by this contract.
