# Story 10.1: Define Evidence-Backed Instrument Profiles

Status: done

<!-- Note: Planning READY does not authorize implementation, source acquisition, device configuration, physical acquisition, experiment execution, feature activation, publication, control, storage mutation, or dashboard work. -->

## Story

As a research owner,
I want immutable evidence-backed profiles for the selected temperature, pressure, RPM, and command instruments,
so that current conversion and quality interpretation are explicit, reproducible, and auditable without promoting legacy defaults or unresolved evidence.

## Acceptance Criteria

1. **Given** Stories 9.1-9.8 have supplied their intended public canonical identity, semantic vocabulary, exact source revisions/uses, parameter inventory/set/gate, `BindingSlot.v1`, immutable-reference, repository, and authorization contracts **When** Story 10.1 is implemented **Then** it adds only `InstrumentProfile.v1` with small nested value objects, one flat immutable `instrument-profiles.v1.json` catalog as the sole new Story 10.1 machine-record family and profile authority, pure in-memory validation/admission/conversion/quality-or-conformance results, documentation, and focused offline tests **And** it reuses the upstream contracts and `affine_map.v1` instead of creating a second source/parameter/inventory/canonicalization/manifest framework, a CLI, database, service, workflow, acquisition adapter, simulator path, observation schema, experiment specification, runtime integration, or UI; exact bounded source/parameter records added through the Story 9.3/9.4 contracts remain upstream record families, and absent or incompatible upstream public contracts block implementation.

2. **Given** a proposed profile candidate **When** its exact revision and admission are evaluated **Then** the immutable profile payload binds schema/version, logical `profile_id`, profile role, manufacturer/model and selected variant/configuration slots, represented quantity kind, electrical and engineering/reference endpoint parameter revisions with units, a closed transform-binding set keyed by supported direction, role-specific quality-policy or command-conformance bindings, exact source-revision/use IDs and locators, the exact Story 9.4 independent inventory and required-set identities, approved logical component/track/experiment-class/final-output scope, limitations, predecessor identity when applicable, and recomputable canonical content hash **And** validation follows the acyclic dependency order `source/use -> parameter revisions -> independent inventory -> required set scoped to logical profile_id -> profile revision -> admission result`; the profile never binds its own Story 9.4 gate/admission result or a future exact experiment/run/observation/result, while the ordinary admission result binds the completed profile revision plus a freshly recomputed `accountable` parameter-gate result. Every numeric slot must resolve to one exact applicable `ParameterEvidence.v1` revision, and missing, duplicate, circular, pending, anonymous, legacy, non-finite, unit-incompatible, or scope-mismatched content blocks only that candidate.

3. **Given** the four initial catalog candidates **When** the Story 10.1 catalog is created **Then** all four are retained initially as immutable blocked planning candidates until every exact source, configuration, parameter, transform, policy, scope, and gate binding passes independently:
   - `instrument-profile-th320-0-100c-v1` binds only the archived Siemens SITRANS TH320 option D73 claim for Pt100, 0-100 degC and four-wire use; its exact 4-20 mA LRV/URV/direction and quality/configuration evidence remain blocking rather than inferred from D73;
   - `instrument-profile-p200-0-10bar-v1` retains provisional planning attributes `P200`, gauge 0-10 bar and two-wire 4-20 mA, while exact order-code/as-configured identity remains `unavailable_blocking`; the externally discovered SKU `7MF1565-3CA00-1AA1` is a research lead, not formal profile identity, until separately authorized acquisition archives official bytes/hash and Story 9.3 validates every selected option and use;
   - `instrument-profile-fb420-user-range-v1` binds only the documented programmable relation from user Min RPM to 4 mA and user Max RPM to 20 mA; exact project RPM LRV/URV, PPR/target geometry, decimal/direction, operating scope, as-configured state and quality evidence remain blocking, and neither manufacturer defaults nor legacy `1200-4200 rpm` may be substituted;
   - `instrument-profile-cds803-terminal53-linear-0-100-v1` binds the Danfoss 6-12/6-13 documented 4/20 mA values, separately binds the already planning-frozen project decision for 6-14/6-15 values 0/100, and requires verified parameter 6-19 current mode; the later 25/75 factors and derived 8/16 mA setpoints remain owned by Story 10.4.
   **And** a blocked candidate is neither an admitted profile nor proof of installed/configured hardware, a measured observation, physical acquisition, real-plant behavior, or experiment authorization; resolving one candidate never auto-selects, defaults, deletes, or unblocks another.

4. **Given** an immutable admitted-profile handle from the exact registry snapshot **When** one supported conversion is requested **Then** the converter accepts no raw/unadmitted profile, binds exactly one qualified `affine_map.v1` invocation revision per applicable direction key `current_to_normalized`, `current_to_engineering_or_reference`, and `engineering_or_reference_to_current`, and delegates all parsing/canonical Decimal arithmetic to Story 9.4 without deriving a local inverse **And** endpoint and midpoint vectors are exact; Story 9.4 `Inexact` and `Rounded` traps remain active, any inexact/rounded/zero-span/inverted-span or semantic unit/quantity mismatch fails, input and dependency identities remain preserved, and no tolerance, quantization, clipping, imputation or binary-float escape path exists in v1. Approximate conversion would require a future identity-bearing transform version with explicit quantum and rounding evidence.

5. **Given** an admitted `measurement_transmitter` profile and raw current/diagnostics **When** its pure measurement-quality evaluator runs **Then** it preserves the input unchanged and evaluates the exact ordered profile rules before any conversion, clipping, imputation, replacement, or normalization; returns one closed outcome from `in_range`, `under_range`, `over_range`, `missing`, `uncertain`, or `fault`; and returns the applied rule IDs plus a closed `conversion_disposition` of `convert` or `no_numeric_value` **And** `missing` always produces `no_numeric_value`, every other outcome's disposition and every numeric boundary/precedence rule are exact device-variant/configuration policy bindings, gaps/overlaps/contradictions or unresolved diagnostics block admission, and 4 mA alone never proves FB420 fault because it may be the configured minimum and may also occur during documented feedback-loss behavior.

6. **Given** an admitted `command_input` profile **When** a requested reference/current mapping is checked **Then** a separate pure command-conformance result verifies exact configuration mode, quantity/unit/direction and declared endpoint scope before permitting conversion, returns `conformant` or `blocked` with deterministic reason IDs and `convert` or `no_command_value`, and never emits measurement-quality/fault outcomes or calls command input raw sensor evidence **And** a command profile has no detector/evidence modality merely to satisfy a schema, cannot enter `SignalObservation.v2`, and is usable only later at an exact authorized experiment/control boundary. Measurement profiles bind the applicable Story 9.2 vocabulary version plus `physical_instrumentation` and representation tokens without inventing an `instrument_profile` entity kind or assigning command profiles a physical observation identity; gauge/absolute pressure, percent/dimensionless unity, Celsius affine semantics, RPM representation, audience, role, unit, direction and logical scope remain non-interchangeable.

7. **Given** the catalog and pure functions are tested **When** the focused Story 10.1 suite runs **Then** it covers strict parsing; canonical hash stability; the complete acyclic dependency graph; exact source/use/locator/hash, inventory/set/gate and unit/scope checks; immutable admission handles; rejection of direct conversion for structurally valid but blocked candidates; exact three-direction endpoint/midpoint mappings; `Inexact`/`Rounded` rejection; measurement quality before conversion; command/measurement separation; all four initial blockers; and stable diagnostic families `IPV1_SCHEMA_VERSION_TOKEN`, `IPV1_MUTABLE_ALIAS`, `IPV1_CONTENT_HASH`, `IPV1_SOURCE_USE_LOCATOR`, `IPV1_PARAMETER_GATE`, `IPV1_TRANSFORM_BINDING`, `IPV1_ROLE_QUANTITY_UNIT_DIRECTION`, `IPV1_ENDPOINT_SPAN`, `IPV1_QUALITY_COVERAGE`, `IPV1_DIAGNOSTIC_UNRESOLVED`, and `IPV1_AUTHORIZATION_EFFECT` **And** one side-effect guard proves imports/tests use no network, devices, source acquisition, datasets, simulator, MQTT, OPC UA, storage, control, clock/environment sampling, formal-evidence writes, or UI/dashboard.

8. **Given** planning, Party Mode, validation, conversion, measurement quality, or command conformance produces an outcome **When** any consumer interprets it **Then** `authorization_effect: none` remains explicit; this story invents or newly adopts no domain mock, compressor value/outcome, accuracy, performance result, experiment factor, synthetic dataset, or other scientific number, while binding already approved values only through exact upstream evidence **And** it authorizes no source download, implementation, device purchase/configuration, acquisition, experiment, activation, persistence mutation, publication, control, or UI/UX work. Any future domain mock remains blocked unless authentic reproduction of the exact needed phenomenon is demonstrated unavailable and an approved `MockAdmission.v1` binds strongly applicable official documentation, every adopted value/assumption, narrow limitations, replacement conditions, and a direct necessary role in the final comparison between datasets.

## Tasks / Subtasks

- [ ] Task 1: Enforce prerequisites and exact source anchors (AC: 1-3, 7-8)
  - [ ] Require implemented public contracts and focused suites from Stories 9.1-9.8. Stop if their canonical identity, vocabulary, exact source-use, Story 9.4 inventory/set/gate, binding, immutable-reference/repository, or authorization APIs are absent; create no local substitutes.
  - [ ] Where a required bounded source use is absent, add it only through the implemented Story 9.3 source catalog and validator, preserving that upstream record family and identity; otherwise consume the existing exact revision. Do not treat the current English TH320 PDF as byte-identical to the archived Spanish source, or a web-indexed P200 page/PDF as formal local byte evidence.
  - [ ] Preserve P200 acquisition as a separately authorized `source_acquisition` activity. Until official bytes, hash, exact option selection and source use validate, retain the order-code/as-configured slot as `unavailable_blocking` and the externally observed SKU only as a non-authoritative research lead.
  - [ ] Invent or newly adopt no profile-specific mock or domain number. Reuse the planning-frozen 0/100 decision only through its exact implemented revision; the signal emulator's conditional admission and later `mock_derived` observations belong to Story 10.3.

- [ ] Task 2: Define the minimal contract, flat catalog, and admission boundary (AC: 1-3, 6-8)
  - [ ] Add `src/parallel_truth_fingerprint/contracts/instrument_profile.py` with `InstrumentProfile.v1`, closed profile/direction/measurement-quality/conversion-disposition tokens, minimal frozen nested values, strict parsing and deterministic serialization; re-export only intended public symbols.
  - [ ] Reuse, rather than redefine, Story 9.4 `NumericConsumerInventory.v1`, `RequiredParameterSet.v1`, exact parameter revisions, gate and `affine_map.v1`; each candidate merely binds upstream identities. Use `BindingSlot.v1` for independently permitted blocking/applicability states.
  - [ ] Add `docs/reference-archive/catalog/instrument-profiles.v1.json` as the sole new Story 10.1 machine-record family and profile authority. Store all four initially blocked content-addressed candidates without fabricated fields, fallbacks or mutable aliases; any exact source/parameter additions stay in their Story 9.3/9.4-owned catalogs.
  - [ ] Implement pure registry validation under `src/parallel_truth_fingerprint/evidence/instrument_profiles.py` with injected resolvers and the exact DAG in AC2. Return an ordinary immutable admitted handle/snapshot only after the profile and freshly recomputed upstream gate pass; conversion/quality/conformance functions accept only that handle.

- [ ] Task 3: Implement exact profile conversion (AC: 2, 4, 6-8)
  - [ ] Bind a closed unique transform set by the three direction keys in AC4. Each binding identifies the exact Story 9.4 `affine_map.v1` invocation/parameter revisions; no local formula, Decimal parser, inverse derivation, tolerance or quantization is allowed.
  - [ ] Preserve exact input/profile/source/parameter/transform identities in ordinary results and keep `Inexact`/`Rounded` traps enabled. Fail on missing/duplicate directions, non-Decimal/non-finite inputs, zero/inverted spans and role/quantity/unit/direction mismatch.
  - [ ] Test exact endpoint and midpoint vectors in every applicable direction and prove a blocked candidate or forged/stale admitted handle cannot reach conversion.

- [ ] Task 4: Implement role-specific quality and command conformance (AC: 3, 5-8)
  - [ ] For measurement profiles only, evaluate ordered quality rules on preserved raw current/diagnostics and return the six closed outcomes plus explicit conversion disposition. Every numeric rule and nontrivial precedence decision resolves through the exact profile parameter/policy bindings.
  - [ ] Make `missing -> no_numeric_value` invariant. Keep all other conversions profile-policy specific; unresolved device diagnostics, rule gaps/overlaps and generic NAMUR/4-20 mA fault assumptions block the profile.
  - [ ] For command profiles only, return a separate conformance result and `convert`/`no_command_value` after exact mode/configuration/range checks. Never expose command status as sensor quality, observation, detector evidence or fault.
  - [ ] Keep device semantics isolated: TH320 option/fault/configuration, P200 signal behavior, FB420 feedback/open-output behavior and Danfoss input configuration cannot authorize each other's rules.

- [ ] Task 5: Document evidence, legacy quarantine, and downstream ownership (AC: 1-8)
  - [ ] Add `docs/instrument-profiles-v1.md` with the contract, dependency DAG, exact source-anchor table, initially blocked candidate matrix, transform bindings, role-specific evaluation order, stable diagnostic families, limitations, failure behavior and authorization boundary.
  - [ ] Leave `config/ranges.py`, `sensor_simulation`, `RawHartPayload`, edge acquisition, OPC UA/SCADA projection, legacy comparison/trust values and v1 tests unchanged. They remain legacy/golden paths and cannot select, admit or qualify a formal profile.
  - [ ] Preserve ownership: Story 10.2 owns persisted `SignalObservation.v2` and raw-current linkage; 10.3 owns simulator/transmitter/edge integration and any `mock_derived` observations; 10.4 owns profile selection plus 25/75 and 8/16 experiment values; 10.5 owns restricted truth; 10.6 executes authorized runs; 10.7 qualifies/publishes physical evidence; Epic 18 remains optional read-only presentation.
  - [ ] State that profiles describe bounded transfer/configuration claims and do not prove possession, installation, wiring, calibration, accuracy, acquisition, compressor physics, a real plant, a digital twin, or final dataset comparability.

- [ ] Task 6: Add focused deterministic offline tests (AC: 1-8)
  - [ ] Add standard-library `unittest` coverage in `tests/evidence/test_instrument_profiles.py`, splitting only for readability. Use conspicuous non-domain sentinels for mechanics and exact source-backed facts only in retained blocked candidate fixtures.
  - [ ] Cover every diagnostic family in AC7, canonical bytes/hash, duplicates/unknowns/aliases/self-cycles, source variant/locator/hash, inventory/set/gate completeness, exact admitted-handle closure, all transform directions and arithmetic traps, role/unit/scope isolation, measurement quality coverage/disposition, command conformance, and independent candidate blockers.
  - [ ] Prove no D73-to-active-configuration inference, no formal P200 SKU without archived exact evidence, no FB420 default or `1200-4200 rpm` fallback, no 4 mA fault inference, no Danfoss manufacturer attribution for 0/100 or 25/75, no terminal-53 voltage-mode admission, and no direct conversion of a blocked profile.
  - [ ] Run focused implemented Story 9.1-9.8 suites, Story 10.1 tests and full Python `unittest` discovery. If upstream stories are not implemented, record the prerequisite blocker rather than creating or testing partial stand-ins.

## Dev Notes

### Scope and dependency boundaries

- This is one cohesive contract/catalog/pure-library story. The flat catalog is its sole new machine-record family and profile authority; the human guide is documentation, and any exact bounded additions to Story 9.3/9.4 catalogs remain upstream records. Validation, admission, conversion, measurement quality and command conformance are ordinary in-memory results, not evidence envelopes or lifecycle records.
- Stories 9.1-9.8 are planning artifacts at story-creation time. Implementation remains sequential and must stop if their intended public contracts/tests are absent.
- The profile carries approved logical applicability scope, not a future exact `ExperimentSpec` or run. Later records point to an exact admitted profile revision; the profile never points forward.
- A profile candidate can be content-addressed and retained while blocked. Only the registry's immutable admitted handle/snapshot can enter pure conversion/evaluation, and the handle is valid only for the exact catalog/dependency snapshot it binds.
- UI/UX is optional and out of scope. Planning approval and every result in this story have `authorization_effect: none`.

### Acyclic identity and admission

```text
exact source revision/use
  -> exact parameter/decision/derivation revisions
  -> Story 9.4 independent NumericConsumerInventory.v1
  -> Story 9.4 RequiredParameterSet.v1 scoped to logical profile_id
  -> exact InstrumentProfile.v1 revision
  -> ordinary admission result + immutable admitted handle
  -> later ExperimentSpec.v1 / SignalObservation.v2 references
```

- The exact profile does not bind its own Story 9.4 gate result. Admission recomputes that gate and binds both its outcome and the completed profile revision. This removes profile/gate and profile/parameter cycles.
- A parameter may scope to the logical `profile_id`; it cannot bind the future exact revision/hash whose payload includes it. Content hash is excluded from its own preimage.
- No `latest`, `current`, tag, sensor name, environment value or caller preference can select an eligible revision.

### Exact source anchors and formal-use state

| Source ID / role | Immutable local file or formal status | SHA-256 | Revision and exact locator | Story 10.1 interpretation |
| --- | --- | --- | --- | --- |
| `vendor-siemens-sitrans-th-2025` / TH320 D73 | `docs/reference-archive/documents/Siemens_SITRANS_TH320_TH420_FI01_2025-03_ES.pdf` | `72409ba9305e9073c19a08935207573ca10f1067814aec79c344ad19b3b99068` | FI01 2025-03 ES, archived PDF p. 4, option D73 | Direct only for Pt100 0-100 degC/four-wire option; the current English FI01 link is not the archived byte identity. Exact 4-20 mA LRV/URV/direction/configuration source use remains blocking. |
| `vendor-siemens-sitrans-p200-2025` / pressure candidate | No local bytes; catalog status `pending` | none | FI01 2025 planning locator printed p. 1/7; Industry Mall SKU page is a planning discovery | P200 gauge 0-10 bar/two-wire 4-20 mA remains provisional. Full order code/as-configured identity stays blocking until authorized archived evidence proves every selected option. |
| `vendor-electrosensors-fb420-datasheet-2025` / RPM output | `docs/reference-archive/documents/Electro-Sensors_FB420_2.0_ES730_Rev-I_2025.pdf` | `8a7f0dc5f4f26d0c9c07b6ebdd980a35a0120e9b7ee762c9945a58a6ed409eab` | ES730 Rev I, archived pp. 1-2 output/specification table | Direct only for programmable 4 mA at user minimum and 20 mA at user maximum; no project RPM endpoints. |
| `vendor-electrosensors-fb420-manual` / configuration and diagnostic limits | `docs/reference-archive/documents/Electro-Sensors_FB420_v2_990-003401_Rev-A.pdf` | `a93d9b37eaa57faf80a5e2f64be89337daed7d82e5de7a703aaf96c776e2de0b` | 990-003401 Rev A; Var 01 Pulse Per Rev, Var 02 MIN RPM, Var 03 MAX RPM, and the separate “Loss of Feedback Alert (the Blue LED)” subsection | Supports configurable meanings and the 4 mA ambiguity; exact project PPR/geometry/endpoints/configuration/policy remain blocking. |
| `vendor-danfoss-cds803-programming-2021` / command mapping | `docs/reference-archive/documents/Danfoss_VLT_CDS803_Programming_Guide_AU356039245821_2021.pdf` | `03485b6f6434ac1d17f96430e0ea5bea8d86a756089e51c782aaf52866ba47a2` | VLT CDS 803 Programming Guide AU356039245821 en-000201 / 130R0597; printed p. 54 Tables 60-63 (6-12 through 6-15), printed p. 55 Table 65 (6-19) | Direct for documented configurable relationships/defaults; project 0/100 requires its decision revision, current mode must be verified, and 25/75 plus 8/16 remain outside this profile. |

### Candidate and proof boundaries

- All four candidates start blocked. Archived manufacturer documentation can close only its exact claim; it cannot prove selected project configuration, installed hardware, acquisition, measurement or real-plant behavior.
- The P200 research lead narrows future source acquisition but is not formal identity. Its full SKU may encode connector, seal or other options the project has not selected.
- TH320 D73 is an ordering option, not proof of active LRV/URV, direction or fault configuration. The separate mapping/configuration source use must be immutable and exact.
- FB420 documentation proves configurability, not the project's RPM range/PPR/geometry. A 4 mA value is ambiguous without the exact configuration and diagnostics.
- Danfoss 4/20 values are documented device facts; 0/100 are project choices; 25/75 and 8/16 belong to `ExperimentSpec.v1`. Terminal 53 must be verified in current mode before admission.

### Role-specific evaluation order

For a measurement transmitter:

1. Resolve an admitted handle and preserve raw current/diagnostics.
2. Apply the exact ordered profile policy and obtain one quality outcome plus `convert` or `no_numeric_value`.
3. Only when disposition is `convert`, invoke the bound exact transform direction.
4. Return ordinary derivation facts without clipping or imputation; Story 10.2 later persists the original and derived representations.

For a command input:

1. Resolve an admitted handle and validate exact current mode/configuration, requested quantity/unit/direction and declared endpoints.
2. Return command conformance plus `convert` or `no_command_value`.
3. Only when conformant, invoke the bound exact reference-to-current transform. This result is never measurement quality or `SignalObservation.v2`.

- There is no generic NAMUR/fault convention. Each numeric boundary and nontrivial precedence decision requires exact applicable source/parameter evidence.
- There is no tolerance in v1. Exact Decimal traps make an unrepresentable mapping fail rather than silently round. Accuracy/calibration/dynamic-response claims remain outside this story.

### Stable diagnostic families

- `IPV1_SCHEMA_VERSION_TOKEN`: malformed/unknown schema, version, field or token.
- `IPV1_MUTABLE_ALIAS`: `latest`, `current` or other non-identity selector.
- `IPV1_CONTENT_HASH`: canonical byte, digest, self-reference or snapshot mismatch.
- `IPV1_SOURCE_USE_LOCATOR`: absent/pending/wrong source revision, use, variant, bytes, hash or locator.
- `IPV1_PARAMETER_GATE`: missing/conflicting/circular/non-accountable inventory, required set or parameter binding.
- `IPV1_TRANSFORM_BINDING`: missing/duplicate/inapplicable transform direction or arithmetic trap.
- `IPV1_ROLE_QUANTITY_UNIT_DIRECTION`: incompatible role, modality/representation, quantity, unit, direction or logical scope.
- `IPV1_ENDPOINT_SPAN`: missing, inverted or zero endpoint span.
- `IPV1_QUALITY_COVERAGE`: measurement-rule gap, overlap, contradiction or missing disposition.
- `IPV1_DIAGNOSTIC_UNRESOLVED`: unknown/ambiguous device diagnostic or unsupported command configuration.
- `IPV1_AUTHORIZATION_EFFECT`: any result/profile/catalog that claims an authorization effect.

Exact leaf codes may specialize a family without changing its meaning; callers branch on structured family/token fields, never free-form text.

### Legacy quarantine and downstream ownership

- Legacy `config/ranges.py` values 48-95 degC, 1.8-8.5 bar and 1200-4200 rpm, the simulator's `4 + 16 * percent/100`, implicit simulator activation, duplicated edge/SCADA metadata, HART-inspired shapes and anonymous comparison/trust tolerances remain v1/golden only.
- Story 10.1 neither edits nor executes those paths. Story 10.2 owns `SignalObservation.v2`; 10.3 owns explicit runtime/emulator integration; 10.4 owns experiment selection/factors; 10.5 owns truth; 10.6 owns execution; 10.7 owns qualification/publication.
- Passing Story 10.1 proves only canonical, evidence-accountable transfer/configuration bindings for an exact admitted revision. It cannot prove instrument possession, wiring, configuration correctness in a live device, calibration, accuracy, acquisition, physical fidelity, experiment permission, dataset quality or final cross-dataset comparability.

### Academic mock/number guardrail

- Story 10.1 invents or newly adopts no domain number. It can bind the existing 0/100 project decision only after its exact Story 9.4 lineage passes; no manufacturer source is credited for that choice.
- No domain mock is needed to define the profile contract. An official device profile does not depend on `MockAdmission.v1`; later emulator observations bind both the exact profile and admitted mock lineage and remain `mock_derived`.
- A future mock is forbidden when authentic reproduction of the needed phenomenon is feasible. If genuinely unavailable, exact strongly applicable official locators/values, all assumptions/limitations/replacement conditions and a direct necessary role in the final physical-versus-syscall dataset comparison are mandatory.

### Project structure notes

- Contract: `src/parallel_truth_fingerprint/contracts/instrument_profile.py` plus intended exports.
- Pure admission/conversion/evaluation: `src/parallel_truth_fingerprint/evidence/instrument_profiles.py`.
- Sole new Story 10.1 machine-record family and profile authority: `docs/reference-archive/catalog/instrument-profiles.v1.json`; bounded upstream source/parameter additions retain Story 9.3/9.4 ownership.
- Human guide: `docs/instrument-profiles-v1.md`.
- Tests: `tests/evidence/test_instrument_profiles.py` unless split only for readability.
- No CLI, dependency, database, service, dynamic plugin, environment-selected profile or mutable registry index.

## BMAD Party Mode Review

- Review panel: John (product scope), Winston (architecture), Quinn (academic evidence/QA), and Amelia (developer readiness).
- Initial product-scope score: 8.40/10 - vetoed.
- Initial architecture score: 8.35/10 - vetoed.
- Initial academic-evidence and QA score: 8.60/10 - vetoed.
- Initial developer-readiness score: 8.30/10 - vetoed.
- Initial aggregate score: 8.41/10 - not approved.
- Initial findings: the draft asserted the complete P200 order code before formal archived evidence, bundled a nonessential CLI, made the profile bind its own parameter-gate result, left transform cardinality and post-quality conversion disposition ambiguous, mixed measurement quality with command conformance, allowed an approximate-tolerance escape from exact Decimal arithmetic, and lacked exact source anchors and stable diagnostic families.
- Final product-scope score: 9.35/10 - no veto.
- Final architecture score: 9.80/10 - no veto.
- Final academic-evidence and QA score: 9.60/10 - no veto.
- Final developer-readiness score: 9.50/10 - no veto.
- Aggregate final score: 9.56/10.
- Auto-approval rule: score at least 9.0 with no veto.
- Decision: auto-approved as `ready-for-dev` after removing the nonessential CLI, making the profile catalog the sole new machine-record family, correcting the acyclic source/parameter/profile/admission DAG, requiring immutable admitted handles and exact non-rounded transform bindings, separating measurement quality from command conformance, retaining all four initial candidates as independently blocked, downgrading the complete P200 SKU to a non-authoritative research lead, and adding exact source anchors and stable diagnostic families.
- Boundary: Party Mode can approve only this planning artifact; `authorization_effect` remains `none`.

### References

- [Source: _bmad-output/planning-artifacts/epics.md#Story 10.1: Define Evidence-Backed Instrument Profiles]
- [Source: _bmad-output/planning-artifacts/epics.md#Cross-Epic Mock Admission Guardrail]
- [Source: _bmad-output/planning-artifacts/prd.md#FR37]
- [Source: _bmad-output/planning-artifacts/prd.md#FR73-FR76]
- [Source: _bmad-output/planning-artifacts/prd.md#NFR39-NFR44]
- [Source: _bmad-output/planning-artifacts/prd.md#NFR47-NFR52]
- [Source: _bmad-output/planning-artifacts/architecture.md#Controlling V2 Architecture Consolidation - 2026-08-22]
- [Source: _bmad-output/planning-artifacts/architecture.md#Authoritative evidence contracts]
- [Source: _bmad-output/planning-artifacts/architecture.md#Verified instrument and command profiles]
- [Source: _bmad-output/implementation-artifacts/9-3-build-the-authoritative-source-evidence-catalog.md]
- [Source: _bmad-output/implementation-artifacts/9-4-build-the-parameter-evidence-catalog-and-validation-gate.md]
- [Source: _bmad-output/implementation-artifacts/9-5-preserve-v1-contracts-as-golden-versioned-fixtures.md]
- [Source: _bmad-output/implementation-artifacts/9-6-define-immutable-artifact-and-evaluation-manifests.md]
- [Source: _bmad-output/implementation-artifacts/9-8-define-partition-freeze-and-activity-authorization-records.md]
- [Siemens SITRANS TH320/TH420 FI01 ordering data, current English planning reference](https://cache.industry.siemens.com/dl/files/161/109765161/att_1322130/v1/sitranst_th320_th420_fi01_en.pdf)
- [Siemens Industry Mall: P200 planning lead 7MF1565-3CA00-1AA1](https://mall.industry.siemens.com/mall/en/en/Catalog/Product/7MF1565-3CA00-1AA1)
- [Siemens SITRANS P200/P210/P220 FI01 planning reference](https://support.industry.siemens.com/cs/attachments/109765047/sitransp_p200_p210_p220_fi01_en.pdf)
- [Electro-Sensors FB420 product page](https://www.electro-sensors.com/products/shaft-speed-switches/fb420)
- [Electro-Sensors FB420 v2.0 Standard manual, Rev. A](https://www.electro-sensors.com/application/files/4817/1095/7949/FB420_v2.0_Standard_990-003401_Rev_A.pdf)
- [Danfoss VLT CDS 803 Programming Guide AU356039245821 en-000201](https://assets.danfoss.com/documents/273384/AU356039245821en-000201.pdf)

## Mandatory Academic Evidence Amendment

Before implementation, apply the relevant mandatory controls in [Academic Evidence Admission Amendment — 2026-08-31](../planning-artifacts/academic-evidence-admission-amendment-2026-08-31.md). This story must fail closed on an unresolved evidence origin, numeric authority, required mock closure, or prohibited dataset substitution. The amendment adds no activity authorization.
## Dev Agent Record

### Agent Model Used

### Debug Log References

### Completion Notes List

### File List
