# Process, transmitter, and edge v2 boundary

The inactive v2 path is one-way: `EngineeringFrame` → injected profile forward
conversion → `SignalObservation.v2` builder → canonical bytes on
`physical/observations/v2` → strict parser → edge-local non-trusted view.

Process frames are controlled research-mock inputs, not plant data, a digital
twin, safety evidence, or a control surface. They never reach an edge. The
transmitter invokes one admitted forward conversion; quality and both reverse
representations remain owned by the `SignalObservation.v2` resolver. MQTT is
only a byte boundary, never profile, truth, consensus, or control authority.

Each receiver has an explicit edge/sensor/profile binding and retains validated
records by content ID in its own mapping. It makes no freshness, ordering,
collision, aggregate, trust, or completeness judgement. Invalid, wrong-route,
noncanonical, and binding-mismatched inputs are rejected before delivery or
view mutation. This path has `authorization_effect: none`; feature activation
and experiment execution require their separate governance authorizations.

The legacy `edges/observations` route and legacy acquisition/MQTT codecs remain
quarantined and untouched. The in-memory MQTT relay demonstrates interface and
canonical-codec mechanics only; it is not broker, QoS, timing, persistence, or
runtime qualification.
