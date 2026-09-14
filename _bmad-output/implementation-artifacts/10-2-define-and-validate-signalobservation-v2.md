# Story 10.2: Define and Validate `SignalObservation.v2`

Status: done

<!-- Note: Planning READY does not authorize implementation, source or dataset acquisition, emulator execution, observation production, physical acquisition, experiment execution, MQTT activation, persistence, consensus, feature activation, publication, control, or dashboard work. -->

## Story

As an edge evidence consumer,
I want one canonical physical observation contract,
so that primary raw current, pre-processing quality, profile-owned representations, identity, and time cannot drift across services or be confused with an aggregate.

## Acceptance Criteria

1. **Given** Stories 9.1-9.8 and 10.1 have supplied their intended public canonical identity, semantic vocabulary, exact source/use, parameter inventory/set/gate, canonical Decimal and `affine_map.v1`, immutable-reference/schema/audience, authorization, and admitted-profile contracts **When** Story 10.2 is implemented **Then** it adds only the `SignalObservation.v2` top-level machine-record family, shallow frozen nested leaf values, one identity-addressed canonical machine schema projection, pure construction/parsing/record validation/canonical serialization and hashing, documentation, and focused offline tests **And** it reuses those upstream contracts instead of creating another canonicalizer, hash/reference format, source or parameter catalog, profile/conversion/quality implementation, manifest family, database, service, workflow, v1 adapter, MQTT route, acquisition path, persistence writer, collection-order analyzer, aggregate/consensus record, experiment record, truth record, CLI, or UI; absent or incompatible upstream public contracts block implementation.

2. **Given** one source event for one physical measurement transmitter at one edge **When** the controlled builder creates `SignalObservation.v2` **Then** the immutable payload records fixed `contract_id: SignalObservation`, `schema_version: 2`, and `record_role: primary_per_edge`; one exact registered Story 9.6 audience/access class; exact experiment, run, round, edge, sensor, source-stream, source-boot, source-session, event and source-sequence identities; an opaque correlation binding with explicit evidence state; distinct caller-supplied canonical source and observed timestamps; a required clock-evidence snapshot; the exact Story 9.2 semantic identity; exact admitted `measurement_transmitter` profile logical ID, revision reference/hash, catalog/registry-snapshot reference/hash, exact `ParameterGateResult.v1` revision/content ID, and sorted consumed parameter revision IDs/hashes; the primary raw-current state in fixed unit `mA`; closed canonical diagnostic facts; the exact Story 10.1 quality/derivation trace; normalized-span and engineering representation states with shallow derivation facts, quantities and units; and a recomputable observation content ID **And** logical event ID, observation content ID, schema ID/hash, profile logical/revision/hash identities, parameter revision/hash identities, and any later artifact-manifest identity remain non-interchangeable and use documented acyclic preimages that exclude only their own derived self-ID. The builder consumes an admitted handle, but no Python handle identity, ordinary admission-result object or newly invented `ProfileAdmission` record is serialized.

3. **Given** immutable identity/time inputs, exact raw-current presence and canonical diagnostic facts, one exact Story 9.2 semantic identity, one immutable Story 10.1 admitted measurement-profile handle, and one pinned resolver snapshot **When** the controlled builder runs **Then** it preserves raw inputs unchanged, evaluates Story 10.1 measurement quality first, and only for `conversion_disposition: convert` invokes the exact profile-owned `current_to_normalized` and `current_to_engineering_or_reference` transforms **And** Story 10.1's public result must expose the ordered rule IDs, diagnostic IDs used, exact consumed parameter revisions/hashes and exact transform direction/revision/input/output facts; Story 10.2 blocks rather than inferring or reconstructing that trace locally. The public builder accepts no caller-supplied quality, normalized span, engineering value, unit, rule result, conversion disposition, parameter closure, or alternative formula; strict validation reconstructs admission from the serialized immutable underlying identities and exactly recomputes and compares every trace fact.

4. **Given** raw current or a derived numeric representation is available or unavailable **When** it is represented and validated **Then** raw current uses a closed discriminated state of `present` with one unchanged canonical Decimal string or `missing` with one profile-declared closed audience-safe reason token; each derived slot uses `derived` with its exact canonical Decimal value/unit/shallow derivation fact or `not_derived` with the exact closed quality/disposition reason token **And** JSON `null`, empty string, JSON numeric literal whether integer or floating-point, Boolean-as-number, NaN, Infinity, exponent notation, negative zero, implicit coercion, last-known-good substitution, fabricated zero, clipping, imputation, quantization, tolerance, epsilon, local affine calculation, or silent rounding fails closed. `quality: missing` may describe an event that explicitly reported no numeric current; complete absence of an expected event is not fabricated as an observation and belongs to Story 10.6 stream-completeness evidence.

5. **Given** the exact Story 10.1 quality result is `in_range`, `under_range`, `over_range`, `missing`, `uncertain`, or `fault` **When** representation invariants are checked **Then** raw current and diagnostics remain the primary unchanged pre-processing evidence, `convert` requires both normalized and engineering representations to be present and exactly recomputable, and `no_numeric_value` requires both to be explicitly `not_derived` **And** normalized span uses canonical unit `one`, is never clipped to `[0,1]`, and engineering quantity/unit exactly match the admitted profile. Every numeric quality boundary, precedence decision, conversion endpoint, clock bound or other result-affecting constant resolves to exact Story 9.4 evidence; no generic 4-20 mA, NAMUR, device-fault, timestamp-skew, freshness or tolerance rule is invented or transferred between instruments.

6. **Given** identity, event, sequence, timestamp, clock, correlation, semantic, audience, profile, parameter, diagnostic, quality, unit, representation, derivation or content-ID fields **When** strict parsing or validation runs **Then** unknown/duplicate/missing fields, mutable aliases, unregistered tokens, unsafe/unresolved opaque identities, stale/forged/blocked/command profile handles, wrong resolver snapshots, extra or incomplete parameter uses, unit/quantity mismatch, hash mismatch, and any silent v1 inference/default/coercion fail with stable structured diagnostics **And** both timestamps use the exact Story 9.6 caller-supplied UTC lexical form `YYYY-MM-DDTHH:MM:SS.ffffffZ`; neither is sampled, synthesized, copied from the other, or universally ordered. Clock and correlation use the exact closed variants/cardinalities in Dev Notes, separate measured facts from parameter-backed policy thresholds, and preserve unresolved evidence without any individual status claiming synchronization, pairwise join comparability or fusion eligibility.

7. **Given** an observation containing source-sequence identity **When** record validation runs **Then** `source_sequence` is a strict positive canonical integer bound to exact scope `(experiment_id, run_id, edge_id, source_boot_id, source_session_id, sensor_id, source_stream_id)` with no inferred identity, default or reset inside the same boot/session **And** the event key is that scope plus `event_id`, while the sequence key is that scope plus `source_sequence`. Equal event key and canonical content denotes idempotent identity semantics; divergent content for one event key or reuse of one sequence key by another event is a conflict. Detection across collections, reset transitions, duplicate/gap/late/out-of-order analysis, retained outcomes and stream completeness remain Story 10.6 responsibilities.

8. **Given** detector-facing or consensus-facing observation serialization and its immutable provenance closure **When** semantic, forbidden-content and audience validation runs **Then** only an exact registered Story 9.6 audience/access class permitted for physical detector/consensus use and Story 9.2 `physical_instrumentation` with linked `raw_current_ma`, `normalized_span`, and `engineering_value` representations are accepted; direct or transitive scenario truth, fault/attack/anomaly/training labels, future schedules or intervals, interventions, Linux syscalls, detector features/scores/decisions, fusion/consensus decisions, OPC/SCADA conclusions, actuator/command content, restricted locators, or truth-revealing names/counts/timing is rejected **And** all identity-bearing fields, including opaque correlation, must resolve through the pinned detector-safe identity/audience resolver and closure; arbitrary strings, regexes, free-text scans or field-name scans cannot prove safety.

9. **Given** a primary per-edge observation and any later aggregate physical record **When** contracts, serialization or persistence boundaries are checked **Then** `SignalObservation.v2.record_role` accepts only `primary_per_edge`, aggregate roles/fields/participant lists/rankings/consensus values are rejected, and no aggregate is created by this story **And** later Epic 11 aggregate/consensus records use their own contract, logical identity and content hash and reference exact immutable input-observation identities without overwriting, copying the event ID of, or masquerading as primary raw-current evidence.

10. **Given** canonical serialization, inspection and focused tests **When** the Story 10.2 suite runs repeatedly **Then** Story 9.6 canonical bytes and lowercase `sha256:<64 hex>` observation content IDs match an independently hand-authored canonical-byte/hash oracle and remain deterministic when the test harness explicitly sets and restores supported locale, timezone, current-working-directory and path contexts **And** production imports/builders/validators never sample those environment values, the clock, network, devices or services. The contract and stable diagnostics are inspectable without a dashboard; construction/validation results retain `authorization_effect: none`; and no formal project-domain observation may be emitted while every Story 10.1 candidate remains blocked.

11. **Given** academic provenance and mock/number policy **When** this story is reviewed or later implemented **Then** it adopts no new device value, compressor outcome, diagnostic or clock threshold, experiment factor, performance claim, or domain mock; source/observed time and source-scoped event identity are cited only as bounded precedent, while correlation, exact fields, UTC grammar, quality tokens, sequence scope and fail-closed behavior are identified as project choices **And** validation proves only internal contract integrity, not acquisition, physical fidelity, qualification, synchronization, fusion eligibility or final dataset comparability. Any future domain mock must satisfy Story 9.4's controlling `MockAdmission.v1`, using Story 9.3 exact source/use authority and Story 9.2 semantic lineage, and cannot be authorized by this contract story.

## Amendment Acceptance Criteria

**Given** custom physical evidence, its specification, persistence request, or qualification input
**When** it is admitted to a formal path
**Then** its closed origin, prototype generation binding, per-field mock influence, exact parameter authority, immutable trace, and current `DirectReproductionAssessment.v1` are resolved where applicable
**And** missing/mismatched generator, source-use, parameter, assessment, origin, or trace blocks formal evidence without creating a fallback or changing experiment control.

- [ ] Add focused non-domain `unittest` cases for valid reconstruction and every missing/mismatched closure element, including an authentically reproducible behavior that invalidates a prior mock admission.
## Tasks / Subtasks

- [ ] Task 1: Enforce prerequisites and preserve the single-contract boundary (AC: 1, 10-11)
  - [ ] Require implemented public contracts and focused suites from Stories 9.1-9.8 and 10.1. Stop if canonical identity/Decimal/hash/reference, semantic/provenance classification, parameter closure/gate, immutable admitted-profile handles, quality results, or profile-owned transform results are absent or incompatible; create no local substitutes.
  - [ ] Define `SignalObservation.v2` as the only new top-level machine-record family. Nested clock, value-availability, diagnostic, profile-binding and representation objects have no independent registry or lifecycle.
  - [ ] Add one identity-addressed machine schema projection using the upstream schema-authority pattern; pin exact schema ID/hash, document the projection/hash preimage, reject mutable aliases, and add no JSON Schema dependency.
  - [ ] Keep all four project instrument candidates blocked. Use only conspicuous non-domain admitted-profile sentinels for unit tests; create or persist no formal project observation.

- [ ] Task 2: Define the immutable contract and strict canonical parser (AC: 1-2, 4, 6, 8-10)
  - [ ] Add `src/parallel_truth_fingerprint/contracts/signal_observation.py` with the exact top-level/nested wire table in Dev Notes, closed v2 tokens, shallow deeply immutable leaf values, explicit `present`/`missing` and `derived`/`not_derived` variants, and exact intended public exports through `contracts/__init__.py`. Reused upstream objects retain their own wire contracts; no nested observation value receives an independent content identity.
  - [ ] Reuse Story 9.6 duplicate-key rejection, canonical UTC, canonical encoding, immutable references, audience/provenance closure and content IDs, plus Story 9.4 canonical Decimal parsing. Reject floats, Booleans, nulls, unknown fields, noncanonical numbers/times/IDs, self-hash confusion and caller-provided IDs that do not recompute.
  - [ ] Pin raw unit `mA`, normalized unit `one`, profile-owned engineering quantity/unit and fixed `primary_per_edge`; preserve event ID, content ID, schema ID/hash and evidence revision/hash distinctions.
  - [ ] Define the exact observation content-ID preimage and canonical arrays/order. Include all identity-, time-, quality-, profile-, parameter-, provenance- and representation-bearing fields and exclude only the content ID itself. Diagnostics are unique and sorted by profile-declared diagnostic ID; parameter uses are unique and sorted by role plus target revision/hash; applied quality rules retain evaluator order.

- [ ] Task 3: Implement controlled construction and exact recomputation (AC: 2-5, 10-11)
  - [ ] Add pure logic under `src/parallel_truth_fingerprint/evidence/signal_observations.py` using injected immutable resolver snapshots. The public builder accepts raw acquisition facts plus an admitted measurement-profile handle and never accepts caller-owned derived/quality fields.
  - [ ] Resolve exact profile revision/hash, catalog/registry snapshot, gate result and parameter-use closure; reject blocked, stale, forged, aliased or `command_input` profiles and any missing/extra dependency. Serialize only immutable underlying identities and reconstruct admission during validation; never persist the runtime handle/admission-result object or invent a `ProfileAdmission` family.
  - [ ] Preserve raw current and diagnostics canonical value-exactly, invoke Story 10.1 quality first, then invoke only the two exact bound current transforms when disposition is `convert`. Require Story 10.1 to return exact ordered rule/diagnostic/parameter/transform traces and block if it does not.
  - [ ] Revalidate stored observations by independently recomputing quality and both representations from the same pinned closure. Compare exact Decimal, quantity, unit, disposition, rule, parameter and transform facts without tolerance, local math, clipping, imputation or rounding.

- [ ] Task 4: Validate identity, time, sequence, audience and aggregate separation (AC: 6-9)
  - [ ] Require all exact IDs including source boot/session, source/observed times, one closed clock-evidence snapshot and one closed correlation binding. Keep measured offset/uncertainty facts separate from parameter-backed policy thresholds; represent unavailable/unknown states explicitly and never invent a universal skew or join decision.
  - [ ] Validate the positive canonical sequence and deterministic composition of both event/sequence keys at record level without inferring a reset/default. Document idempotence/collision semantics; Story 10.6 owns cross-record collision detection, gaps, lateness, ordering, retained outcomes and completeness.
  - [ ] Enforce the exact Story 9.6 audience/access class and detector-safe semantic/provenance/identity closure for both detector and consensus consumers. Reject forbidden direct and transitive content with audience-safe diagnostics; arbitrary identity strings and textual scanning are insufficient.
  - [ ] Reject aggregate roles and fields in `SignalObservation.v2`. Do not implement a consensus/aggregate schema, computation, adapter or persistence projection.

- [ ] Task 5: Document academic boundaries, legacy quarantine and downstream ownership (AC: 1-11)
  - [ ] Add `docs/signal-observation-v2.md` with field/variant tables, canonical preimages, construction/validation order, profile/parameter closure, clock and sequence semantics, forbidden-content policy, diagnostics, failure modes, source-backed versus project-choice claims, and the no-authorization boundary.
  - [ ] Quarantine the existing v1 physical path (`RawHartPayload`/transmitter simulation, ranges/simulator, acquisition/MQTT/local state, consensus/persistence and SCADA) unchanged. No subclassing, whole-dict adapter, shape inference, default or projection may promote its floats, clipped/rounded values, inferred identities, one timestamp, diagnostics or hybrid aggregates to v2.
  - [ ] Preserve ownership: Story 10.3 owns process/transmitter/edge integration, mock-derived formal emission and the MQTT v2 route; 10.4 owns exact experiment/profile selection and factors; 10.5 owns restricted truth/correlation mapping; 10.6 owns authorized production, persistence and stream completeness; 10.7 owns G2 qualification/publication; Epic 11 owns aggregate/consensus records; Story 12 owns `ScadaObservation.v2`; later cross-modal work owns join qualification; Epic 18 is optional read-only presentation.
  - [ ] State that the current emulator can later produce only `custom_generated` + `mock_derived` evidence with exact approved mock lineage; deterministic profile conversion never promotes it to authentic, official-real, locally measured hardware or real-plant evidence.

- [ ] Task 6: Add deterministic offline contract and adversarial tests (AC: 1-11)
  - [ ] Add standard-library `unittest` coverage in `tests/evidence/test_signal_observations.py`, splitting only for readability. Cover strict schema/version/tokens, duplicate and unknown fields, immutable nested values, content preimage/hash, exact serialization and supported locale/timezone/CWD/path contexts.
  - [ ] Cover present/missing current, all six quality outcomes, both conversion dispositions, unclipped under/over values, raw preservation, exact unit/quantity, parameter/transform closure, blocked/stale/forged/command handles, caller-derived alternatives, Decimal traps and no v1 coercion/default.
  - [ ] Cover canonical source/observed timestamps, every clock/correlation variant and field cardinality, measured-versus-policy separation, boot/session sequence scope and deterministic event/sequence-key composition; prove Story 10.2 never performs cross-record collision, ordering, gap, lateness or completeness analysis.
  - [ ] Cover direct/transitive truth, labels, future schedules, syscalls, scores, fusion/consensus, OPC/SCADA conclusions, commands, revealing diagnostic fields, semantic correlation IDs and aggregate masquerade; assert stable structured diagnostic families, not free prose.
  - [ ] Add at least one independent hand-authored canonical byte string and SHA-256 oracle. Prove no formal project observation is admitted from a blocked Story 10.1 candidate or any quarantined v1 physical-path object/projection.
  - [ ] Run focused implemented Story 9.1-9.8 and 10.1 suites, Story 10.2 tests and full Python `unittest` discovery. If prerequisites are not implemented, record the prerequisite blocker rather than building partial stand-ins.

## Dev Notes

### Scope and dependency boundary

- This is a cohesive contract plus pure-library story. `SignalObservation.v2` is its only top-level machine-record family; the schema projection is authority for that family rather than a second scientific record. No observation catalog or sample project-domain observation is committed.
- Stories 9.1-9.8 and 10.1 are planning artifacts at story-creation time. Implementation must follow them and stop if their required public APIs are unavailable. All four real instrument profiles are deliberately blocked, so contract tests use only conspicuous sentinel evidence.
- The contract can preserve an explicitly missing reading emitted by a source. It cannot invent a record for an event that never arrived. Stream inventory/completeness belongs to Story 10.6.
- UI/UX is optional and out of scope. Inspectability means canonical bytes, structured diagnostics and documentation are sufficient; no dashboard is needed for correctness.
- READY and every result in this story have `authorization_effect: none`.

### Acyclic construction and identity

```text
Story 9.2 semantic identity + Story 9.6 detector-facing provenance closure
exact Story 10.1 admitted measurement-profile handle
  -> exact profile revision/hash + catalog/registry snapshot
  -> exact Story 9.4 parameter gate/use closure
raw current presence + raw diagnostics
caller-supplied event/sequence/time/clock facts
  -> Story 10.1 quality result
  -> when disposition=convert: exact profile-owned transforms
  -> SignalObservation.v2 canonical bytes
  -> observation content ID (self-ID excluded from its preimage)
  -> later Story 9.6 artifact/run manifests and Epic 11 input references
```

- `event_id` identifies the source occurrence within its declared scope. `observation_content_id` identifies canonical record bytes. The same event and same bytes can be idempotent; the same event and different bytes is a conflict, never an update.
- A later `ArtifactManifest.v1` identifies persisted batch/stream bytes and cannot replace the individual event or observation-content identity.
- A profile logical ID cannot substitute for exact profile revision/hash/catalog-snapshot/gate identity. Parameter revisions and parameter hashes likewise remain separate. The admitted handle is a builder capability only; validation reconstructs admission from those serialized immutable identities.

### Exact owned wire fields and variants

`SignalObservation.v2` owns the following exact top-level keys. A reused Story 9.x object or `ImmutableReference.v1` is serialized exactly under its upstream wire contract rather than copied into a second local shape.

| Key | Cardinality / exact form | Meaning |
| --- | --- | --- |
| `contract_id`, `schema_version`, `schema_ref`, `record_role` | Required singletons; `SignalObservation`, `2`, one exact schema reference, `primary_per_edge` | Contract/schema/role identity. |
| `audience_access_class`, `semantic_identity` | Required singletons using exact Stories 9.6 and 9.2 wire types | Physical detector/consensus access class and evidence semantics; neither substitutes for the other. |
| `experiment_id`, `run_id`, `round_id`, `edge_id`, `sensor_id` | One required detector-safe opaque ID each | Observation scope. |
| `source_stream_id`, `source_boot_id`, `source_session_id`, `event_id` | One required detector-safe opaque ID each | Producer epoch/session and event identity. |
| `source_sequence` | One required positive canonical JSON integer | Sequence inside the exact boot/session scope; not a scientific numeric value. |
| `correlation` | One required `CorrelationBinding.v2` leaf value | Opaque correlation plus the evidence state used to issue it. |
| `source_timestamp`, `observed_timestamp` | One required Story 9.6 canonical UTC string each | Source-occurrence and collection-observation times. |
| `clock` | One required `ClockEvidence.v2` leaf value | Recorded clock relation/evidence, not a join decision. |
| `profile_binding` | One required `ProfileBinding.v2` leaf value | Immutable identities underlying the admitted handle. |
| `raw_current` | One required `RawCurrent.v2` leaf value | Primary current evidence. |
| `diagnostics` | Required array, exact profile-declared cardinality | Unique `DiagnosticFact.v2` values sorted by `diagnostic_id`. |
| `quality_trace` | One required `QualityTrace.v2` leaf value | Exact Story 10.1 quality result and trace. |
| `normalized_span`, `engineering_value` | One required `RepresentationSlot.v2` each | Fixed linked representation slots, derived or explicitly not derived. |
| `observation_content_id` | One required recomputed lowercase SHA-256 content ID | Hash of the entire canonical record except this self-ID field. |

Exact Story-owned nested wire forms:

- `CorrelationBinding.v2`: exactly `correlation_id`, `evidence_state`, `method`, and `measured_uncertainty`. `evidence_state` is one of `evidence_present`, `unresolved`, or `unknown`; `method` is `present` with one immutable reference or `unavailable` with a closed reason. `measured_uncertainty` is exactly one of: `present` with canonical Decimal value, exact unit and immutable evidence reference; `not_applicable` with an exact immutable policy reference and closed reason; or `unavailable` with a closed reason. Variants are disjoint: `evidence_present` requires a present method and uncertainty `present` or policy-declared `not_applicable`; `unresolved` requires a present attempted method and uncertainty `unavailable`; `unknown` requires method and uncertainty both `unavailable`. No state asserts join eligibility.
- `ClockEvidence.v2`: exactly `source_clock_id`, `observed_clock_id`, `evidence_status`, `method`, `measured_offset`, `measured_uncertainty`, and `qualification_policy`. `evidence_status` is `qualified`, `unqualified`, `unresolved`, or `unknown`; each of the next four fields is a discriminated slot. A measured slot is `present` with canonical Decimal value, unit and immutable evidence reference or `unavailable` with a closed reason. Method/policy slots are `present` with one immutable reference or `unavailable` with a closed reason. `qualified` and `unqualified` both require present method/policy slots and exactly the measurements required by that policy; only the exact bound policy evaluation distinguishes their statuses. `unresolved` requires a present attempted method plus an unavailable policy or at least one unavailable policy-required measurement. `unknown` requires all four slots unavailable with closed reasons. The variants are mutually exclusive; status describes only local evidence under its policy and never pairwise or cross-modal eligibility. Numeric policy thresholds live only in the referenced Story 9.4 parameter closure, never in measured slots.
- `ProfileBinding.v2`: exactly `profile_id`, `profile_revision_ref`, `profile_canonical_bytes_hash`, `catalog_snapshot_ref`, `catalog_snapshot_hash`, `parameter_gate_result_ref`, and `consumed_parameters`. `consumed_parameters` is a nonempty unique array of `ParameterUse.v2` sorted by `(role, target revision ID, target bytes hash)`; each value contains exactly a closed profile-returned role plus one exact parameter immutable reference/hash.
- `DiagnosticFact.v2`: exactly `diagnostic_id`, `value_state`, `value_type`, `unit_binding`, and either `value` or `reason`. IDs, types, cardinality and allowed token values/reasons come from the admitted profile. `value_state` is `present` or `missing`; `value_type` is `boolean`, `canonical_decimal`, `canonical_integer`, or `closed_token`; decimal values use canonical strings, integers use canonical JSON integers, and the other types use only their exact native/token forms. `unit_binding` reuses upstream `BindingSlot.v1`: it is `bound` to one exact Story 9.4 unit or independently permitted `not_applicable` with a closed reason, never a fabricated unit token. `present` requires only `value`; `missing` requires only a closed profile-declared `reason`. Arbitrary maps, extra keys and free text are forbidden.
- `QualityTrace.v2`: exactly `outcome`, `conversion_disposition`, `applied_rule_ids`, `diagnostic_ids_used`, and `parameter_uses`. Tokens are the Story 10.1 tokens; rule and diagnostic arrays preserve evaluator order and contain only profile-declared unique IDs, while parameter uses follow the canonical order above.
- `RawCurrent.v2`: `present` has exactly `state`, `value`, `unit: mA`; `missing` has exactly `state`, `reason`, `unit: mA`. Value is canonical Decimal; reason is a closed profile-declared token.
- `RepresentationSlot.v2`: `derived` has exactly `state`, `value`, `quantity_kind`, `unit`, and `derivation`; `not_derived` has exactly `state`, `quantity_kind`, `unit`, and `reason`. `DerivationFact.v2` has exactly `direction`, `transform_revision_ref`, `profile_revision_ref`, `input_representation`, `output_representation`, and canonically ordered `parameter_uses`. Direction and input/output pairs are fixed to the corresponding Story 10.1 binding; reason is a closed quality/disposition token.

All nested values are shallow and included in the parent observation hash. They are not independently hashed record families. Unknown keys, duplicate keys, invalid variant combinations, wrong cardinality/order and free prose fail closed.

### Minimal value and derivation states

| Concern | Allowed state | Required invariant |
| --- | --- | --- |
| Raw current | `present` | Exact canonical Decimal string plus fixed `mA`; unchanged from builder input. |
| Raw current | `missing` | Exact profile-declared safe reason token; no numeric key, null, zero or substituted value. |
| Derived representation | `derived` | Exact canonical Decimal, quantity/unit and immutable Story 10.1 transform invocation. |
| Derived representation | `not_derived` | Exact closed quality/disposition reason token; no numeric key or fabricated value. |
| Quality disposition | `convert` | Both normalized and engineering slots are `derived` and exactly recompute. |
| Quality disposition | `no_numeric_value` | Both derived slots are `not_derived`; raw/diagnostic evidence remains. |

- `normalized_span` is dimensionless with unit `one`. Values outside the nominal span remain visible when the exact profile policy permits conversion.
- Raw measurements and derived results are observations, not adopted `ParameterEvidence.v1` constants. Result-affecting endpoints, quality rules, transform configuration and any clock bound remain parameter evidence.
- Static bytes cannot prove historic call order. The controlled builder enforces quality-before-conversion, while validation independently recomputes the same sequence and accepts only the resulting exact record.

### Clock and sequence semantics

- OpenTelemetry distinguishes event/source `Timestamp` from collection-system `ObservedTimestamp`; this supports preserving the two facts. It does not dictate this project's exact field set or mandatory presence.
- RFC 5905 supports retaining actual synchronization method/state and measured offset/dispersion facts. It supplies no universal project skew tolerance. Any later permitted bound must be an exact applicable parameter/policy binding.
- Story 9.6's exact fixed-microsecond `Z` grammar is a project canonicalization rule. It is stricter than general RFC 3339 and must be described as such.
- `observed_timestamp >= source_timestamp` is not a universal invariant because the values can originate from distinct clocks. Ordering can be assessed only when exact clock evidence establishes comparability.
- Sequence identity is scoped to `(experiment_id, run_id, edge_id, source_boot_id, source_session_id, sensor_id, source_stream_id)`. A sequence reset is valid only under a different exact boot/session identity and is never guessed or defaulted.
- Story 10.2 validates the record fields and documents event/sequence-key collision semantics. Story 10.6 detects collisions, resets, gaps, lateness and ordering across an arrival collection and owns completeness outcomes.
- Clock/correlation `unknown`, `unresolved` or `unqualified` preserves evidence but cannot assert synchronized or cross-source fusion eligibility. Even `qualified` describes only the exact local evidence under its bound policy; later join/fusion validators decide pairwise eligibility.

### Semantic, mock and aggregate boundaries

- This is one `physical_instrumentation` observation with three linked representations, not three modalities. Story 9.2 governs evidence/result/scientific/synthetic roles and dataset scope; the separate exact Story 9.6 audience/access class governs detector/consensus access.
- Every identity-bearing field must be issued/resolved through the pinned detector-safe namespace and provenance closure. Being syntactically opaque is insufficient: an arbitrary ID could still encode restricted meaning, and regex/free-text scanning cannot establish semantic safety.
- Current software-emulator output later remains `custom_generated` and `mock_derived`, bound to the exact approved signal-emulator `MockAdmission.v1`; conversion through an official instrument profile does not turn software output into authentic hardware evidence.
- Genuine future instrument observations may be authentic when their own acquisition/provenance gates pass, so the contract does not universally force mock lineage. Mechanical tests remain `fixture_test`/`fixture_expected`/`test_only`/`not_applicable` and cannot enter a formal observation stream.
- `SignalObservation.v2` is always primary and per-edge. Epic 11 aggregate records have another contract/identity and exact parent references. Story 10.2 introduces no aggregate schema or aggregate arithmetic.
- Opaque correlation is a join handle, not truth. The mapping to restricted scenario truth belongs outside detector-facing evidence under Story 10.5/9.8 controls.

### Stable diagnostic families

- `SOV2_SCHEMA_VERSION_TOKEN`: malformed/unknown schema, version, field, variant or token.
- `SOV2_CONTENT_ID`: canonical byte, digest, self-preimage or schema-projection mismatch.
- `SOV2_RECORD_ROLE`: anything other than the singleton primary per-edge role.
- `SOV2_IDENTITY`: missing/malformed/aliased/conflicting event or scope identity.
- `SOV2_SEQUENCE`: invalid record scope/value or event/sequence-key composition; cross-record collision/order outcomes remain Story 10.6.
- `SOV2_TIMESTAMP_CLOCK`: invalid/missing/synthesized time, invalid clock variant/cardinality, measured/policy conflation or overclaimed relation.
- `SOV2_CORRELATION_EVIDENCE`: invalid/unsafe identity, evidence variant/cardinality or overclaimed correlation result.
- `SOV2_SEMANTIC_ROLE`: wrong modality/representation/evidence/scope classification.
- `SOV2_AUDIENCE_IDENTITY`: unresolved, restricted or incompatible Story 9.6 audience/access class or detector-safe identity closure.
- `SOV2_PROFILE_REFERENCE`: blocked/stale/forged/command/wrong-snapshot profile binding.
- `SOV2_PARAMETER_CLOSURE`: missing, extra, stale or inconsistent gate/parameter-use binding.
- `SOV2_RAW_CURRENT_PRIMARY`: mutated, substituted, clipped, imputed or invalid raw-current state.
- `SOV2_QUALITY_RECOMPUTE`: quality, diagnostic, rule-order or disposition mismatch.
- `SOV2_REPRESENTATION_RECOMPUTE`: missing/extra/mismatched derivation or transform invocation.
- `SOV2_UNIT_QUANTITY`: raw, normalized or engineering quantity/unit mismatch.
- `SOV2_FORBIDDEN_FIELD`: direct or transitive restricted/foreign-modality/decision/control content.
- `SOV2_AGGREGATE_MASQUERADE`: aggregate role, content, identity reuse or primary-record overwrite attempt.
- `SOV2_AUTHORIZATION_EFFECT`: any contract/result claiming an authorization effect.

Leaf codes may specialize a family without changing its meaning. Consumers branch on structured family/token fields, never free-form message text; detector-facing diagnostics remain audience-safe.

### Repository hazards and legacy quarantine

- The existing v1 physical path spans `RawHartPayload`/transmitter simulation, ranges/simulator, acquisition/MQTT/local replicated state, consensus/persistence and SCADA. Across that path, floats, clipping/rounding, anonymous conversions, one generated timestamp, inferred/mutable identity, permissive JSON, hardcoded diagnostics, truth-bearing dictionaries and hybrid aggregate/edge projections violate v2 invariants. It remains unchanged and quarantined; no subclass, whole-dict adapter, shape inference, default, or projection can promote it to `SignalObservation.v2`.
- Story 10.3 owns explicit producer integration; Story 10.6 owns retained stream/persistence outcomes; Epic 11 owns consensus records. The strict v2 parser rejects unknown/forbidden legacy content rather than silently filtering it.
- Passing this contract proves exact internal linkage, not physical truth, quality qualification, synchronized joins or comparability.

### Academic evidence and project-choice ledger

| Claim | Exact source/status | Bounded use in Story 10.2 |
| --- | --- | --- |
| Event/source timestamp differs from collector-observed timestamp | `docs/reference-archive/documents/OpenTelemetry_Log_Data_Model_v1.60.0.md`, SHA-256 `3ee2c391a5d3262130582df89a3dc5a5640d837d010734ea79458fe3ece31173` | Supports preserving two time facts; does not make both mandatory generally or prove clock comparability. |
| Event identity can use a source-scoped ID and repeated delivery can retain that identity | `docs/reference-archive/documents/CloudEvents_Core_Spec_v1.0.2.md`, SHA-256 `e327435c858d19fd171e4ab9781a01fc22dfa949d23c4220976529ebd16a1aa3` | Bounded precedent for source-scoped occurrence identity/idempotence only; no correlation, CloudEvents conformance or transport claim. |
| Actual clock synchronization state/offset/dispersion evidence should be retained rather than replaced by an invented universal bound | `docs/reference-archive/documents/IETF_RFC5905_NTPv4_2010-06.txt`, SHA-256 `8b7abd903c60202e2953ee012fefa6916666c3b0c71825c748cdd262024fb268` | Supports measured clock-evidence concepts only; does not authorize a project skew/freshness threshold or require NTP. |
| Opaque correlation, exact fields, fixed UTC grammar, six quality tokens, sequence scope, variants, diagnostics and fail-closed behavior | Controlling PRD/architecture, Stories 9.2/9.4/9.6/10.1 and this story | Explicit project contract choices, not external scientific facts. |

- No domain mock or scientific number is needed here. Structural version numbers, identifiers, sequence integers and recorded timestamps are metadata, not simulated physical outcomes.
- Device-specific current mapping, endpoints and diagnostic meaning can enter only through one exact admitted Story 10.1 profile and its exact official-source/parameter bindings. Generic 4 mA, 20 mA, NAMUR or legacy status booleans are never universal evidence.
- If authentic production of a future required phenomenon is feasible, a mock is not admissible. If genuinely unavailable, exact official support, the admitted values/assumptions, limitations/replacement conditions and necessary final-comparison role must all resolve before use.

### Project structure notes

- Contract: `src/parallel_truth_fingerprint/contracts/signal_observation.py` plus intended exports.
- Pure builder/parser/record validation: `src/parallel_truth_fingerprint/evidence/signal_observations.py`.
- Identity-addressed schema projection: follow the implemented Story 9.6 schema-authority layout; do not create a mutable `latest` alias or a second manifest framework.
- Human guide: `docs/signal-observation-v2.md`.
- Tests: `tests/evidence/test_signal_observations.py` unless split only for readability.
- No observation catalog, project-domain fixture, CLI, dependency, database, service, MQTT/OPC adapter, persistence writer, aggregate schema, runtime execution or UI.

### Amendment enforcement: observation provenance

For each custom-generated observation, serialize the closed `evidence_origin`; require the exact generation-binding and immutable emission-trace/output-manifest reference in addition to the existing origin/mock lineage. A `mock_parameterized` observation also declares `generation_origin=prototype_generated` and per-field mock influence. Authentic observations reject mock-generation provenance. A missing or mismatched producer identity, input closure, origin, influence map, or trace fails validation without relabelling the observation.
## BMAD Party Mode Review

- Review panel: John (product scope), Winston (architecture), Quinn (academic evidence/QA), and Amelia (developer readiness).
- Initial product-scope score: 8.60/10 - no veto, below the auto-approval threshold.
- Initial architecture score: 8.45/10 - vetoed.
- Initial academic-evidence and QA score: 8.30/10 - vetoed.
- Initial developer-readiness score: 8.00/10 - vetoed.
- Initial aggregate score: 8.34/10 - not approved.
- Initial findings: the first draft crossed into Story 10.6 collection-order/completeness analysis, omitted required boot/session and correlation-evidence identity from NFR46, treated the admitted runtime handle ambiguously as serialized evidence, conflated Story 9.2 semantics with Story 9.6 audience, left clock/correlation/diagnostic/derivation wire variants under-specified, overstated CloudEvents correlation support, repeated legacy/mock boundaries excessively, and lacked an independent canonical byte/hash oracle.
- Focused second-round QA scores: Quinn 8.90/10 and Amelia 8.80/10 - both vetoed until overlapping correlation states, missing `unresolved` clock semantics, a fabricated diagnostic unit token and incorrect `MockAdmission.v1` ownership were corrected.
- Final product-scope score: 9.40/10 - no veto.
- Final architecture score: 9.70/10 - no veto.
- Final academic-evidence and QA score: 9.60/10 - no veto.
- Final developer-readiness score: 9.50/10 - no veto.
- Aggregate final score: 9.55/10.
- Auto-approval rule: aggregate score at least 9.0 with no reviewer veto.
- Decision: auto-approved as `ready-for-dev` after restricting the story to record-level contract behavior; adding exact boot/session, audience and correlation evidence; serializing only immutable underlying profile/gate/catalog/parameter identities; defining mutually exclusive shallow wire variants and canonical order; separating measured clock/correlation facts from policy thresholds; binding diagnostics to the admitted profile; correcting source/MockAdmission attribution; and requiring an independent canonical oracle.
- Boundary: Party Mode can approve only this planning artifact; `authorization_effect` remains `none`.

### References

- [Source: _bmad-output/planning-artifacts/epics.md#Story 10.2: Define and Validate `SignalObservation.v2`]
- [Source: _bmad-output/planning-artifacts/prd.md#FR72-FR74]
- [Source: _bmad-output/planning-artifacts/prd.md#NFR39-NFR42]
- [Source: _bmad-output/planning-artifacts/prd.md#NFR44-NFR50]
- [Source: _bmad-output/planning-artifacts/prd.md#NFR52]
- [Source: _bmad-output/planning-artifacts/architecture.md#Controlling V2 Architecture Consolidation - 2026-08-22]
- [Source: _bmad-output/planning-artifacts/architecture.md#Authoritative evidence contracts]
- [Source: _bmad-output/implementation-artifacts/9-2-establish-the-semantic-and-evidence-role-vocabulary.md]
- [Source: _bmad-output/implementation-artifacts/9-4-build-the-parameter-evidence-catalog-and-validation-gate.md]
- [Source: _bmad-output/implementation-artifacts/9-5-preserve-v1-contracts-as-golden-versioned-fixtures.md]
- [Source: _bmad-output/implementation-artifacts/9-6-define-immutable-artifact-and-evaluation-manifests.md]
- [Source: _bmad-output/implementation-artifacts/9-8-define-partition-freeze-and-activity-authorization-records.md]
- [Source: _bmad-output/implementation-artifacts/10-1-define-evidence-backed-instrument-profiles.md]
- [Source: docs/reference-archive/documents/OpenTelemetry_Log_Data_Model_v1.60.0.md]
- [Source: docs/reference-archive/documents/CloudEvents_Core_Spec_v1.0.2.md]
- [Source: docs/reference-archive/documents/IETF_RFC5905_NTPv4_2010-06.txt]

## Mandatory Academic Evidence Amendment

Before implementation, apply the relevant mandatory controls in [Academic Evidence Admission Amendment — 2026-08-31](../planning-artifacts/academic-evidence-admission-amendment-2026-08-31.md). This story must fail closed on an unresolved evidence origin, numeric authority, required mock closure, or prohibited dataset substitution. The amendment adds no activity authorization.
## Dev Agent Record

### Agent Model Used

### Debug Log References

### Completion Notes List

### File List
