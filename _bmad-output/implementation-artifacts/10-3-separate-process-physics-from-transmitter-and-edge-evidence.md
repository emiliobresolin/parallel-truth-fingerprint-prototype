# Story 10.3: Separate Process Physics From Transmitter and Edge Evidence

Status: done

<!-- Note: Planning READY does not authorize implementation, source acquisition, profile/mock admission, v2 route activation, observation production, broker execution, experiment execution, persistence, consensus, control, publication, or dashboard work. -->

## Story

As a simulator maintainer,
I want process physics separated from transmitter conversion and edge evidence,
so that engineering behavior is not confused with what the instrumented edge actually observes.

## Acceptance Criteria

1. **Given** the directly consumed implemented contracts for semantic/source use, numeric parameter and mock admission, v1 golden/quarantine behavior, canonical identity/audience/authorization, admitted profiles and conversions, and `SignalObservation.v2` **When** Story 10.3 is implemented **Then** it adds only an additive inactive v2 producer/integration path with small frozen in-memory values, pure engineering-frame/transmitter/observation composition, a canonical MQTT v2 codec and injected transport boundary, separate non-trusted edge-local views, documentation and focused offline tests **And** it creates no new top-level scientific record family, source/parameter/profile/mock/manifest framework, database, service, CLI, scheduler, truth record, persistence path, consensus/aggregate schema, OPC UA path, detector, runtime-demo rewrite, dashboard or UI. Missing or incompatible directly consumed prerequisites block implementation rather than receiving local substitutes.

2. **Given** an exact caller-supplied engineering input frame and its immutable trace, parameter-gate and admitted-mock lineage **When** the controlled process-state emulator produces one frame **Then** it returns only immutable canonical Decimal temperature, gauge-or-absolute pressure as explicitly declared, and rotational-speed values in exact engineering quantity/unit slots plus input/derivation/provenance references **And** it contains no current, normalized span, instrument quality, `SignalObservation`, edge/MQTT fields, truth, scenario meaning, detector/consensus result, or control command. It has no default state, random source, environment or clock sampling, implicit zero noise, clipping, float conversion or anonymous formula, and is labelled a controlled research mock rather than real-plant data, validated compressor dynamics or a digital twin.

3. **Given** any domain behavior or result-affecting value used by the v2 process-state emulator **When** its formal prerequisites are checked **Then** one exact Story 9.4 accountable parameter closure resolves every value through its correct direct, derived, measured, preregistered-factor or mock authority; each mock-classified behavior/value additionally requires an immutable `MockAdmission.v1` with structural state `valid` and approval state `approved`, an exact required `ParameterGateResult.v1` outcome `accountable`, authentic-path feasibility `unavailable_with_evidence`, and applicable Story 9.3 official source/use locators that bind the exact component, bounded question, PTFP-Custom track, final paired comparison, limitations, prohibited claims and replacement condition **And** convenience, cost, timing, an unfavorable authentic result, broad source lists, conditional planning prose, weak transfer, missing authority or a reproducible authentic path blocks the mock. The current planning YAML is migration input only and cannot by itself activate emission; later formal project-domain emulator output is `custom_generated` + `mock_derived` and never becomes authentic hardware, official-real, real-plant or externally validated evidence, while conspicuous test sentinels remain test-only fixtures and are rejected by formal resolvers.

4. **Given** one validated engineering channel, exact edge/sensor assignment, admitted `measurement_transmitter` handle, admitted diagnostic input and fully injected Story 10.2 identity/time/clock/correlation context **When** the shared transmitter-observation function runs **Then** it invokes Story 10.1 `engineering_or_reference_to_current` exactly once, preserves the resulting canonical raw mA unchanged, and delegates quality-first evaluation plus `current_to_normalized` and `current_to_engineering_or_reference` exclusively to the Story 10.2 controlled builder using the same exact profile/catalog/gate/parameter snapshot **And** when `conversion_disposition` is `convert`, the returned engineering representation equals the supplied process value exactly under the non-rounding profile contract; when it is `no_numeric_value`, both derived slots remain `not_derived` under the exact profile-owned reason, no round-trip equality is claimed, and inconsistent raw/diagnostic states are rejected. No process model, edge, MQTT adapter, batch/live wrapper or consumer reimplements an affine formula, inverse, quality rule or diagnostic meaning, accepts caller-supplied derived values, or clips, imputes, rounds, quantizes or compares with an implicit tolerance.

5. **Given** three configured logical edges **When** one immutable process frame fans out through the exact assignments **Then** producer orchestration exposes only the assigned engineering channel and profile scope to that edge's transmitter boundary, which constructs the edge-scoped `SignalObservation.v2` with explicit experiment/run/round/edge/sensor/source-stream/boot/session/event/sequence/correlation/time/clock facts; the receiving edge accepts only the resulting strictly validated current-domain observation/canonical bytes and retains schema-complete observations by content identity in a separately owned non-trusted local view **And** no edge receives a process frame or engineering-channel input, steps the process model, treats hidden engineering state as primary evidence, infers sensor identity from a tag, stores a float-only projection, overwrites prior content with an aggregate, shares a mutable view/dictionary with another edge, or changes local state before strict validation succeeds. Repeated or divergent event/sequence identities remain unclassified retained inputs; Story 10.6 alone owns duplicate/collision/staleness/gap/lateness/order/completeness detection and evidence.

6. **Given** a validated local observation and an explicitly injected v2 transport boundary **When** it publishes or consumes through MQTT **Then** the only logical topic is exactly `physical/observations/v2`, the payload is the exact Story 10.2 canonical bytes, every in-memory or subsequently authorized runtime adapter crosses the same encode/strict-parse/profile/provenance validation boundary before callbacks or view mutation, and publisher identity comes from the validated observation rather than a topic suffix or untrusted callback argument **And** malformed payloads, duplicate JSON object member names, unknown fields, wrong topic/schema/version/audience/edge/sensor/profile/parameter/mock identity, forbidden truth/syscall/score/fusion/control content, aggregate masquerade and noncanonical bytes fail explicitly with no partial delivery. MQTT is transport only and never a profile, trust, consensus, truth or control authority; Story 10.3 proves only codec/interface mechanics, not broker or runtime policy qualification.

7. **Given** the same immutable engineering frame, admitted dependencies and identical injected observation context **When** batch and live adapters are compared **Then** both call the same pure transmitter-observation function and produce exactly equal scientific fields, canonical bytes and observation content ID; the live test additionally crosses the v2 MQTT codec/receive validator **And** no second batch formula, binary float, `isclose`, epsilon or tolerance is introduced. A future nonzero parity tolerance requires exact Story 9.4 authority and belongs to Story 10.7 qualification; fake-client or passive-relay coverage proves adapter mechanics only, not real-broker interoperability, timing, delivery quality or scientific execution.

8. **Given** any profile, mock, parameter, assignment, context, transport policy, version or conversion dependency is absent, conditional, blocked, stale, forged, incompatible or unauthorized **When** v2 construction, emission or consumption is attempted **Then** the operation returns stable structured failure and emits/mutates nothing, with no v1 coercion, shape inference, field filtering, default, automatic version detection or fallback **And** existing `CompressorSimulator`, `SimulatedTransmitterObservation`, `RawHartPayload`, `edges/observations`, edge wrappers, scenario/demo runtime and their golden tests/bytes remain unchanged when the new v2 path is not explicitly constructed. None of the four blocked project profile candidates or the planning-conditional mock admission may produce a formal project-domain observation in this story.

9. **Given** MQTT, storage, analytics, detector, consensus, OPC UA, consumer, optional dashboard or validation failure **When** the v2 path handles the failure **Then** it can only reject/report/degrade evidence and cannot call, synthesize or modify a compressor/setpoint/actuator command **And** the modules accept read-only process frames from the later experiment-control boundary and contain no import, credential, callback or reverse conduit into control. Story 10.4 owns specification/profile selection/schedules and the 25/75 factors; 10.5 owns restricted truth; 10.6 owns authorized production/persistence/completeness; 10.7 owns real parity/G2 qualification; Epic 11 owns consensus; Epic 12 owns OPC; Epic 18 remains optional presentation.

10. **Given** the focused Story 10.3 suite and documentation **When** they are inspected or run offline **Then** they cover exact boundary ownership, mock/profile/parameter blocking, process-frame purity, one forward conversion, both Story 10.2 conversion dispositions, raw-current preservation, isolated edge views, canonical MQTT routing, batch/wire parity against the independent Story 10.2 canonical-byte/hash oracle, version quarantine and control isolation with conspicuous non-domain sentinels **And** imports/tests use no network, broker, source acquisition, device, runtime clock, random/environment default, storage, experiment, formal evidence write or UI. Every Story 10.3-owned success/failure result, including transport/view results, retains `authorization_effect: none`; actual v2 feature activation requires an exact Story 9.8 `feature_activation` authorization and later experiment use requires separate `experiment_execution` authorization.

## Tasks / Subtasks

- [ ] Task 1: Enforce prerequisites and quarantine the complete v1 physical path (AC: 1, 3, 8-10)
  - [ ] Require only the directly consumed implemented public contracts/tests for semantic/mock lineage, exact source/use, parameter/mock gate, v1 routing/quarantine, canonical bytes/audience/identity/authorization, admitted-profile traces/conversions and the controlled observation builder. Stop if one is absent/incompatible; create no local compatibility substitute merely because its originating story exists.
  - [ ] Keep `config/ranges.py`, `behavior_model.py`, `simulator.py`, `transmitter_observation.py`, legacy edge acquisition/local state/MQTT wrappers, runtime config/script, consensus/persistence/SCADA and dashboard unchanged. Their existing route remains `edges/observations`; no union payload or automatic v1/v2 parser is allowed.
  - [ ] Make the v2 path additive and inactive unless explicitly constructed after its gates pass. Add no default feature flag that silently selects v2 and do not wire it into `scripts/run_local_demo.py` in this story.
  - [ ] Treat the four real profile candidates and `mock-admission-ptfp-signal-emulator-v1` execution as blocked at story-creation time. Tests use only conspicuous non-domain `fixture_test`/`fixture_expected`/`test_only` sentinels; formal resolvers reject those fixture roles, and tests never commit a formal project observation or authorize activation.

- [ ] Task 2: Add the minimal engineering-state emulator boundary (AC: 2-3, 8-10)
  - [ ] Add `src/parallel_truth_fingerprint/sensor_simulation/process_physics.py` with a small frozen in-memory engineering frame and a deterministic scripted/input-trace adapter. Use Story 9.4 canonical Decimal/unit/reference types and immutable resolver snapshots; create no persisted `ProcessState` family, generator DSL, random/noise subsystem or alternate schema registry.
  - [ ] Restrict the formal frame to temperature, explicitly typed pressure, and rotational speed. Each present value binds exact quantity/unit, trace/derivation inputs, parameter closure and admitted mock identity; absent/unavailable channels are explicit and cannot become zero/default.
  - [ ] Validate the implemented Story 9.4 exact required-parameter closure for every authority class and require `MockAdmission.v1` structural state `valid`, approval state `approved`, exact required `ParameterGateResult.v1` outcome `accountable`, and `unavailable_with_evidence` for every mock-classified value, not the broad planning YAML. Reject unbacked dynamics/noise/lag/bias/secondary variables/diagnostics/timing and every quarantined legacy value or formula.
  - [ ] Preserve the component label `controlled engineering-state signal emulator` and machine-checkable `custom_generated`/`mock_derived` lineage; document prohibited real-plant/digital-twin/safety/energy/efficiency/control-performance claims.

- [ ] Task 3: Compose the sole transmitter-to-observation path (AC: 3-5, 7-10)
  - [ ] Add `src/parallel_truth_fingerprint/sensor_simulation/transmitter.py` with one pure shared function that accepts one validated channel, one exact assignment, admitted measurement profile, admitted diagnostic facts and fully injected Story 10.2 context/resolvers.
  - [ ] Invoke only Story 10.1 `engineering_or_reference_to_current`; feed its exact raw mA plus diagnostic facts into the Story 10.2 builder; preserve raw current in every valid case, require exact engineering round trip only for `conversion_disposition: convert`, require both derived slots `not_derived` for `no_numeric_value`, reject inconsistent raw/diagnostic states, and return the validated `SignalObservation.v2` or structured failure.
  - [ ] Assert through spies/traces that one forward transform and only the Story 10.2 quality-first reverse transformations run. Reject command profiles, mismatched channels/quantities/units/scopes, caller-derived fields, float math, clipping, imputation, local inverses and anonymous tolerances.
  - [ ] Keep the process frame internal: no edge callback receives the full frame, hidden control state or trace semantics as evidence.

- [ ] Task 4: Add v2 edge receive/binding, isolated local views and strict MQTT bytes (AC: 5-10)
  - [ ] Add `src/parallel_truth_fingerprint/edge_nodes/common/signal_acquisition.py` for immutable edge/sensor/profile receive binding and separately allocated non-trusted observation views. It accepts no process frame or engineering-channel input. Reuse Story 10.2 identity/context types; do not infer IDs, timestamps, sequence, correlation, clock or sensor from environment, tags or mutable counters.
  - [ ] Retain only schema-complete validated immutable observations by content identity without overwriting prior content. Repeated or divergent event/sequence identities may coexist as unclassified retained inputs; do not compute aggregate/latest/trusted state or duplicate/collision/stale/late/gap/order/completeness outcomes owned by Story 10.6.
  - [ ] Add `src/parallel_truth_fingerprint/edge_nodes/common/signal_mqtt.py` with the exact `physical/observations/v2` route, canonical codec and injected publisher/subscriber interface tested with a deterministic fake. Every path transports canonical bytes and strict-validates before callback/view mutation; never call legacy `serialize_payload`/`deserialize_payload` or construct a real broker connection here.
  - [ ] Require an immutable injected transport-policy shape and prohibit hidden defaults. Story 10.3 validates structure and byte-boundary mechanics only. Later authorized runtime binding classifies numeric result-affecting settings through Story 9.4, protocol semantics through exact OASIS/Paho source uses, nonnumeric project choices through frozen applicable decisions/bindings, and executable run authorization downstream; concrete broker/runtime choices and qualification belong to Stories 10.6/10.7.

- [ ] Task 5: Prove parity, failure atomicity and control isolation (AC: 4-10)
  - [ ] Define `batch` as direct invocation of the shared pure transmitter-observation function and `live` as the same invocation plus exact canonical MQTT encode/strict-decode using identical caller-supplied identity/time facts. Compare exact bytes/content ID; do not compare independently generated clocks or identifiers.
  - [ ] Prove malformed, forbidden or mismatched input fails before publish callback/local-view mutation and never retries through v1. Record only the small deterministic audience-safe diagnostic categories declared below.
  - [ ] Use a command/control spy and import/side-effect guard to prove no success or failure path can call the experiment-control boundary. Do not add control interfaces, credentials or dashboard callbacks.
  - [ ] Preserve current v1 tests and byte/route behavior. The deterministic injected fake proves interface mechanics only, not real-broker, QoS or delivery evidence; real route and parity qualification remain blocked until exact activation/execution authorization and Stories 10.6/10.7.

- [ ] Task 6: Document evidence limits and add focused deterministic tests (AC: 1-10)
  - [ ] Add `docs/process-transmitter-edge-v2.md` with the one-way dependency diagram, exact ownership table, mock/parameter gate, route/validation order, batch/live definition, source-backed versus project-choice ledger, v1 quarantine, failure diagnostics, downstream ownership and explicit no-authorization/no-UI boundary.
  - [ ] Add `tests/sensor_simulation/test_process_transmitter_v2.py`, `tests/edge_nodes/test_signal_v2_route.py`, and one small `tests/integration/test_signal_v2_batch_live_parity.py`; split further only if needed for clarity.
  - [ ] Cover every diagnostic category and every AC using exact sentinel Decimal/profile/mock/context/transport fixtures. Include malformed payloads and duplicate JSON object member names, unknown/forbidden fields, both conversion dispositions, profile/assignment/semantic mismatch, local-view independence/content-addressed non-overwrite/deferred collision classification, no pre-validation mutation, exact parity and failure-no-emission.
  - [ ] Add adversarial guards proving no formal v2 import/call reaches the legacy ranges, behavior model, simulator conversion/rounding/diagnostics, acquisition stability/clock/round-window logic or legacy MQTT codec/topic, and no current blocked project profile/mock emits formal evidence.
  - [ ] Compare route/parity outputs with the independent Story 10.2 canonical-byte/hash oracle so a shared encoder defect cannot self-confirm. Run focused implemented prerequisite suites, all Story 10.3 tests and full Python `unittest` discovery. If prerequisites are not implemented, record the prerequisite blocker rather than creating partial stand-ins or claiming runtime proof.

## Dev Notes

### Minimal scope and authority

- This story creates an inactive integration path, not a second simulator product or runtime. The only detector/consensus-facing physical event remains `SignalObservation.v2`; process frames, assignments, adapter results and local views are ordinary in-memory objects.
- The directly consumed upstream contracts are planning artifacts at story-creation time. Implementation is sequential and stops when a required public API is absent.
- Story 10.3 implements route mechanics but does not activate the route or execute an experiment. `feature_activation` and `experiment_execution` are distinct Story 9.8 actions.
- UI/UX is optional and wholly out of scope. Inspectability comes from canonical bytes, structured diagnostics, docs and tests. A later optional dashboard may consume validated read-only observations but is never a Story 10.3 acceptance dependency.

### One-way dependency and conversion ownership

```text
later ExperimentSpec/run context supplies exact trace + identities + times
  -> ordinary immutable engineering frame
     (temperature / pressure kind / rotational speed, canonical units)
  -> exact admitted Story 10.1 measurement profile
     engineering_or_reference_to_current exactly once
  -> raw current + profile-declared diagnostic input
  -> Story 10.2 controlled SignalObservation.v2 builder
     quality first
     current_to_normalized
     current_to_engineering_or_reference
  -> validated canonical SignalObservation.v2
  -> batch return OR physical/observations/v2 canonical MQTT bytes
  -> strict receive validation
  -> separately owned non-trusted edge-local view
```

- The forward conversion and both reverse representations are different bound directions of the same exact admitted profile, not independent formulas. An exact engineering round trip is mandatory only when Story 10.2 returns `conversion_disposition: convert`; `no_numeric_value` keeps both derived slots `not_derived` under the profile-owned reason.
- Process state may be common immutable input for the three transmitter calls. Edge-local mutable views and runtime contexts may not be shared.
- The edge observes raw current and complete linked representations. It never treats hidden process/controller state as primary evidence.

### Process-frame and mock rules

- Prefer a deterministic scripted/input-trace state source over unsupported realism. Story 10.4 later owns the actual specification, trace/seed, selection, schedule and factor identities.
- No stochastic behavior is implied. Absence of noise is an explicit scope-specific `not_applicable` decision/binding, not a numeric zero/default.
- Every generator coefficient, endpoint, trace choice or other result-affecting input belongs to the Story 9.4 inventory/required set. Output samples are trace-derived observations, not each a new parameter record.
- The existing mock-admission YAML is frozen planning/migration input with `status: approved_planning_conditional` and an explicit execution gate. Formal code consumes only the implemented canonical Story 9.4 record/gate.
- `mock_derived` describes only later formal synthetic lineage after all gates/authorizations; test fixtures use distinct `fixture_test`/`fixture_expected`/`test_only` roles and cannot pass formal resolvers. Direct device endpoints remain direct parameters, deterministic transforms remain derived, researcher trace/factors remain preregistered, and measured values remain measured. Parameter class and synthetic lineage cannot be conflated.

### Edge, MQTT and parity semantics

- Topic: exactly `physical/observations/v2`. Do not append or infer a trusted publisher from `/{publisher_id}`; the validated observation carries edge/source identity. The topic is routing metadata, not authorization.
- Batch: call the shared pure function and return its validated observation/canonical bytes.
- Live: call the same function, publish those bytes, then strict-parse/revalidate the received bytes before callback/view mutation.
- Under identical injected identity/time/input facts, parity is exact. Real network timing and delivery are not part of the scientific payload comparison and are evaluated later as evidence.
- MQTT may duplicate or lose messages depending on a later selected delivery policy. The local view retains content-addressed observations without overwriting, but makes no scientific duplicate/collision/staleness/lateness/order/completeness decision; Story 10.6 owns those outcomes.
- The OASIS standard defines MQTT version/QoS/retain/delivery semantics but does not select this project's delivery profile. This story accepts only an injected transport interface and validates codec mechanics; a later authorized runtime binding must not rely on hidden defaults.
- Paho MQTT remains an existing optional `runtime-demo` dependency (`>=2.1,<3`), but no Paho client or broker construction belongs to this story. A deterministic injected fake is sufficient for its offline interface tests.

### Legacy quarantine

- Formal v2 never imports or adapts legacy process ranges, mixture weights, periods/phases, oscillations, noise floor/multipliers, secondary-variable formulas, float rounding/clamping, `4 + 16 * percent/100`, endpoint-as-saturation logic, hardcoded healthy diagnostics, stability score, one-minute round, inferred cold start, one generated timestamp, tag-prefix sensor inference or permissive JSON.
- Those values and behaviors remain exact v1-reproduction-only under `legacy-constant-quarantine-v1.csv`. Existence in code is not evidence and cannot promote a value into direct, measured, preregistered or mock authority.
- No full HART implementation is claimed. Legacy `RawHartPayload` remains HART-inspired v1 and is not a v2 producer input.

### Stable diagnostic categories

- `PTEV2_PREREQUISITE_ADMISSION`: absent/incompatible upstream contract, resolver, parameter authority, profile binding or mock admission.
- `PTEV2_PROCESS_PROFILE`: invalid frame quantity/unit/trace, forbidden/default/quarantined behavior, assignment mismatch or conversion-ownership/quality-disposition failure.
- `PTEV2_OBSERVATION_CONTEXT`: missing/inferred/defaulted identity, sequence, time, clock or correlation fact.
- `PTEV2_TRANSPORT_VIEW`: wrong route, malformed/noncanonical/forbidden payload, or mutation-before-validation/shared-view failure.
- `PTEV2_PARITY_BOUNDARY`: batch/live mismatch, version fallback, command/control conduit, or any Story 10.3 result claiming activation/execution authority.

Leaf codes may specialize a family. Consumers branch on structured family/token fields, never free prose; detector-facing diagnostics remain audience-safe.

### Current repository hazards

- `CompressorSimulator.step()` currently bundles engineering sensors with float transmitter observations. Its local percent/current conversions, noise, clipping, rounding and secondary variables are v1-only; v2 must not call it.
- `EdgeAcquisitionService` owns a simulator, receives a whole snapshot, rounds values, samples one host timestamp, invents physics/stability/cold-start/round facts and emits `RawHartPayload`. The v2 edge instead receives one exact current-domain observation context and never builds those fields.
- `EdgeLocalReplicatedState` infers sensors from tag prefixes and overwrites one payload per sensor. The v2 view retains schema-complete immutable observation content and remains explicitly non-trusted.
- `mqtt_io.py` uses permissive noncanonical JSON and a publisher topic suffix. Keep it unchanged as v1; `signal_mqtt.py` is strict v2 bytes only and never imports its codec.
- Current consensus/persistence can discard current/profile/time or combine aggregate engineering values with one edge's raw fields. Story 10.3 does not feed those paths; Epics 11 and Story 10.6 own their v2 replacements.

### Source-backed and project-choice ledger

| Item | Exact authority/status | Allowed interpretation |
| --- | --- | --- |
| Bounded signal-emulator purpose and limits | Implemented Story 9.4 `MockAdmission.v1` migrated from `docs/reference-archive/catalog/mock-admission-ptfp-signal-emulator-v1.yaml` | Supports only the controlled current-domain emulator after its exact gate passes; not dynamics, realism, hardware or execution authority. |
| Legacy values/formulas | `docs/reference-archive/catalog/legacy-constant-quarantine-v1.csv` | Exact v1 reproduction only; every listed value is disabled for formal v2. |
| Profile-owned electrical/engineering conversions and diagnostics | Exact admitted Story 10.1 profile plus Story 9.3/9.4 source/parameter closure | Story 10.3 delegates; no source claim or formula is re-adopted locally. |
| MQTT transport, duplicate and ordering semantics | `docs/reference-archive/documents/OASIS_MQTT_v5.0_2019-03-07.pdf`, SHA-256 `e8f8e9d2467618d5c5a6398bdf971cb90cdbe2c8e33242e028f442bee8e5de20`, sections 3.3 and 4.3-4.6 | Protocol precedent only; does not choose project QoS, retain, keepalive, port, retry, queue or completeness policy. |
| Paho callback/client behavior | Project pin `paho-mqtt>=2.1,<3` plus official Eclipse Paho Python 2.x client/migration documentation | Implementation API guidance only; fake-client tests are not broker evidence. |
| Topic, one assigned channel per edge, batch/live definitions and exact parity | Controlling PRD/architecture and this story | Explicit project integration choices, not external scientific facts. |

- No new domain behavior or numeric value is adopted by this story. Structural versions/topic tokens and test-only conspicuous sentinels are contract mechanics, not physical claims.
- No new domain source is adopted for these inactive mechanics. A newly discovered unresolved physical claim, diagnostic meaning or result-affecting numeric value remains blocked and routes formal research/acquisition through Stories 9.3 and 9.8 before it can become READY.

### Downstream ownership

- Story 10.4: `ExperimentSpec.v1`, immutable trace/seed, selected assignments/profiles, schedule, phases, 25/75 factors, 8/16 mA command representations, stopping/abort policy.
- Story 10.5: `ScenarioTruth.v1` and restricted correlation-to-truth mapping.
- Story 10.6: authorized run execution, actual project observation production, persistent artifacts, collisions/gaps/late/order/completeness outcomes.
- Story 10.7: real eligible batch/live comparison, discrepancy report, physical qualification and G2.
- Epic 11: current-domain consensus input/decision and trusted aggregate state. Epic 12: independent OPC evidence. Epic 17A: synchronized physical/syscall eligibility. Epic 18: optional read-only presentation.

### Project structure notes

- Engineering frames: `src/parallel_truth_fingerprint/sensor_simulation/process_physics.py`.
- Sole transmitter composition: `src/parallel_truth_fingerprint/sensor_simulation/transmitter.py`.
- V2 edge binding/view: `src/parallel_truth_fingerprint/edge_nodes/common/signal_acquisition.py`.
- V2 canonical MQTT transport: `src/parallel_truth_fingerprint/edge_nodes/common/signal_mqtt.py`.
- Human guide: `docs/process-transmitter-edge-v2.md`.
- Tests: `tests/sensor_simulation/test_process_transmitter_v2.py`, `tests/edge_nodes/test_signal_v2_route.py`, and `tests/integration/test_signal_v2_batch_live_parity.py`.
- No new dependency, schema family, catalog, CLI, database, service, runtime/demo/dashboard edit, persistence/consensus/OPC/truth integration or formal data artifact.

### Amendment enforcement: bounded generator

The emulator emits `prototype_generated`. A mock-parameterized artifact retains `generation_origin=prototype_generated` and identifies only its affected behavior/value in the per-field mock-influence map when that parameter class is `mock` and passes the complete current admission closure. Accept only the bound entrypoint/configuration/parameter/seed closure; no inline arithmetic, default, legacy constant, or alternate signal generator may produce formal evidence.
## BMAD Party Mode Review

- Initial review: product/PM `8.70` (no veto), architecture `8.20` (veto), academic/QA `8.60` (veto); aggregate `8.50`. The story was revised rather than approved.
- Applied corrections: reduced direct prerequisites and diagnostic taxonomy; kept UI/dashboard optional; narrowed MQTT to canonical codec plus deterministic injected interface; kept real broker/runtime policy qualification downstream; moved engineering input strictly to the transmitter boundary; made `no_numeric_value` a valid non-round-trip result; deferred collision/staleness/completeness outcomes to Story 10.6; separated fixture roles from formal mock lineage; made mock gate axes exact (`valid`, `approved`, `accountable`, `unavailable_with_evidence`); and added the independent Story 10.2 canonical-byte/hash oracle.
- Final review: product/PM `9.40` (no veto), architecture `9.60` (no veto), academic/QA `9.70` (no veto); aggregate `9.57`.
- Decision: auto-approved for `ready-for-dev` because the aggregate is at least `9.0` and no reviewer veto remains.
- Boundary: Party Mode approves only this planning artifact; every Story 10.3-owned result has `authorization_effect: none`.

### References

- [Source: _bmad-output/planning-artifacts/epics.md#Story 10.3: Separate Process Physics From Transmitter and Edge Evidence]
- [Source: _bmad-output/planning-artifacts/prd.md#FR73-FR76]
- [Source: _bmad-output/planning-artifacts/prd.md#NFR38-NFR42]
- [Source: _bmad-output/planning-artifacts/prd.md#NFR44-NFR50]
- [Source: _bmad-output/planning-artifacts/prd.md#NFR52]
- [Source: _bmad-output/planning-artifacts/architecture.md#Controlling V2 Architecture Consolidation - 2026-08-22]
- [Source: _bmad-output/planning-artifacts/architecture.md#Bounded physical signal emulator admission]
- [Source: _bmad-output/planning-artifacts/architecture-update-2026-08-15.md#Physical Signal and Experiment Boundary]
- [Source: _bmad-output/planning-artifacts/architecture-update-2026-08-15.md#MQTT Edge Transport]
- [Source: _bmad-output/implementation-artifacts/9-2-establish-the-semantic-and-evidence-role-vocabulary.md]
- [Source: _bmad-output/implementation-artifacts/9-3-build-the-authoritative-source-evidence-catalog.md]
- [Source: _bmad-output/implementation-artifacts/9-4-build-the-parameter-evidence-catalog-and-validation-gate.md]
- [Source: _bmad-output/implementation-artifacts/9-5-preserve-v1-contracts-as-golden-versioned-fixtures.md]
- [Source: _bmad-output/implementation-artifacts/9-6-define-immutable-artifact-and-evaluation-manifests.md]
- [Source: _bmad-output/implementation-artifacts/9-8-define-partition-freeze-and-activity-authorization-records.md]
- [Source: _bmad-output/implementation-artifacts/10-1-define-evidence-backed-instrument-profiles.md]
- [Source: _bmad-output/implementation-artifacts/10-2-define-and-validate-signalobservation-v2.md]
- [Source: docs/reference-archive/catalog/mock-admission-ptfp-signal-emulator-v1.yaml]
- [Source: docs/reference-archive/catalog/legacy-constant-quarantine-v1.csv]
- [Source: docs/reference-archive/documents/OASIS_MQTT_v5.0_2019-03-07.pdf]
- [Eclipse Paho MQTT Python client documentation](https://eclipse.dev/paho/files/paho.mqtt.python/html/client.html)
- [Eclipse Paho MQTT Python 2.x migration documentation](https://eclipse.dev/paho/files/paho.mqtt.python/html/migrations.html)
- [OASIS MQTT Version 5.0](https://docs.oasis-open.org/mqtt/mqtt/v5.0/mqtt-v5.0.html)

## Mandatory Academic Evidence Amendment

Before implementation, apply the relevant mandatory controls in [Academic Evidence Admission Amendment — 2026-08-31](../planning-artifacts/academic-evidence-admission-amendment-2026-08-31.md). This story must fail closed on an unresolved evidence origin, numeric authority, required mock closure, or prohibited dataset substitution. The amendment adds no activity authorization.
## Dev Agent Record

### Agent Model Used

### Debug Log References

### Completion Notes List

### File List
