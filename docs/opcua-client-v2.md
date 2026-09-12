# OPC UA real-client contract v2

`parallel_truth_fingerprint.scada.opcua_client` is the only v2 read adapter.
It creates a new `asyncua.Client` for each enabled request and accepts neither
server objects, writer state, consensus state, cached readings, truth, nor
projected values as inputs.

The request declares the `opc.tcp` endpoint, security mode, namespace URI, and
exact six-node address map. The read returns a frozen `ScadaObservationV2`:
the two measurement `OpcUaDataValue` values preserve OPC status/source/server
time independently from client-side attempt, latency, and observation-time
diagnostics. Revision, snapshot reference, profile, and correlation must all
match the declared immutable identities. Any mismatch, missing node, transport
failure, disabled route, or unsupported security configuration produces an
explicit failure receipt containing no measurement or substituted timestamp.

The default test seam is `OfflineOpcUaClient`, an injected in-memory fake with
no network capability. Production uses `AsyncUaClientSession`; it currently
accepts only the declared `None` security mode. A certificate/security-policy
mapping must be explicitly implemented and supplied before another mode can be
used; it is never silently downgraded.
