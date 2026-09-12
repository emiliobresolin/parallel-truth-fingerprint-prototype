# Story 9.4: Build the Parameter-Evidence Catalog and Validation Gate

Status: done

<!-- Note: Planning READY does not authorize implementation or scientific activity. -->

## Story

As a research owner,
I want every executable v2 numeric parameter to have a complete and validated evidence record,
so that experiments cannot silently inherit unsupported constants or universal assumptions.

## Acceptance Criteria

1. **Given** an executable v2 numeric parameter **When** it is registered **Then** it has a stable parameter ID and exactly one class among `direct`, `derived`, `measured`, `preregistered_factor`, or `mock` **And** its record contains the value, unit, class-specific authority, exact source/decision/calibration/mock locator, derivation and input identities where applicable, profile and experiment scope, approval state, authentic-reproduction feasibility, component, bounded research question, evidence track, final-package element, transferability rationale, mandatory limitations, and typed uncertainty/dispersion when applicable or an explicit reasoned `not_applicable`.

2. **Given** a preregistered factor also cites vendor or standards documentation **When** its authority is evaluated **Then** the frozen `DecisionRecord.v1` remains the authority for the selected value **And** official sources establish only documented capability, feasibility, or constraints and never imply that a manufacturer selected the research factor.

3. **Given** a `direct` parameter **When** it is validated **Then** the value resolves to applicable official documentation from the responsible authority and an exact locator for the selected instrument, variant, protocol, dataset, component, and bounded question **And** proximity to another documented value or prestige of the source cannot transfer authority to an unrelated value or scope.

4. **Given** a `derived` parameter **When** it is validated **Then** it resolves to an immutable derivation operation/version, exact input parameter identities and units, and either a deterministically reproduced constant output or deterministic transform conformance outputs **And** missing inputs, cycles, zero spans, dimensional inconsistency, undeclared rounding, or a reproduced-value/conformance mismatch fails closed.

5. **Given** a `measured` parameter **When** it is validated **Then** it resolves to preserved pilot or calibration evidence containing method, environment/profile, sample and run identities, timestamp, result, dispersion or uncertainty, immutable locator, and content hash **And** the result remains limited to the evidenced environment and profile rather than becoming a universal constant.

6. **Given** a `preregistered_factor` parameter **When** it is validated **Then** it resolves to a frozen pre-test and pre-truth `DecisionRecord.v1` with rationale, scope, owner, approval state, freeze time, and truth/test-lock state **And** the current 25-75 decision means only `speed_reference_pct` or `capacity_reference_pct`, never power, efficiency, a universal operating range, or a manufacturer recommendation.

7. **Given** a `mock` parameter **When** it is validated **Then** it resolves to an approved immutable `MockAdmission.v1` proving the authentic path unavailable with evidence, naming the exact simulator/workload profile, limited purpose, component, question, track, and final-output linkage **And** every represented domain behavior and number resolves to applicable official documentation and an exact Story 9.3 source-use locator.

8. **Given** the authentic path is reproducible, official authority is absent or inapplicable, capability-gap evidence is unresolved, or the authentic result is merely inconvenient or unfavorable **When** mock validation runs **Then** validation fails with a stable capability/source reason **And** no mock fallback, substitution, real-plant claim, measured claim, `official_real` promotion, or external-validation claim is produced.

9. **Given** an anonymous legacy constant is required only for exact v1 reproduction **When** it is catalogued **Then** it retains a stable legacy-reproduction identity and explicit limitation **And** it cannot satisfy a formal v2 requirement, enter a current v2 profile, affect a formal result, or be silently copied into a new parameter record.

10. **Given** a missing or multiply classified parameter, overlapping active conflict, insufficient scope, unresolved authority/reference, invalid unit, or class promotion **When** the gate validates a declared formal scope **Then** it fails closed by parameter ID and stable rule ID **And** it supplies no default, fallback, inferred selection, or architecture-owned value.

11. **Given** parameter records and a complete required-parameter set **When** they are canonicalized and validated repeatedly **Then** their schema-defined ordering, exact numeric representation, serialization, identities, hashes, outcome, and diagnostics are deterministic **And** the declared scope accounts explicitly for noise, dynamics, tolerances, thresholds, windows, queues, capture-loss policy, duration, repetitions, and fusion settings as required or reasoned `not_applicable`, without inventing values.

12. **Given** every required parameter validates **When** the gate passes **Then** the result proves only numerical accountability for the exact catalog, required set, sources, decisions, measurements, mock admissions, and scope identities **And** `authorization_effect` remains `none`: no implementation, acquisition, fitting, training, capture, experiment, promotion, activation, publication, or deployment is authorized.

## Tasks / Subtasks

- [x] Task 1: Define the flat versioned parameter, authority, consumer-inventory, requirement, and gate contracts (AC: 1-2, 4-12)
  - [x] Add `src/parallel_truth_fingerprint/contracts/parameter_evidence.py` with frozen dataclasses, explicit `StrEnum` tokens, tuple-backed nested collections/defensive copying, deterministic `to_dict()` methods, and schema identities for `ParameterEvidence.v1`, `DecisionRecord.v1`, `MockAdmission.v1`, `MeasurementEvidenceRef.v1`, `NumericConsumerInventory.v1`, `ParameterRequirement.v1`, `RequiredParameterSet.v1`, `NumericLocusAudit.v1`, and `ParameterGateResult.v1`. Re-export only the intended public types from `contracts/__init__.py`.
  - [x] Keep records flat and connected by immutable IDs. Separate `parameter_id` (logical parameter), `parameter_revision_id` (one exact value/authority/scope record), catalog identity, required-set identity, authority-record identity, and validation-result identity. Never resolve an executable value through `latest`, mutable aliases, file order, or a bare logical ID.
  - [x] Pin the v1 parameter classes exactly to `direct`, `derived`, `measured`, `preregistered_factor`, and `mock`. Require exactly one class-specific authority object matching the selected class and reject missing, extra, or contradictory authority branches.
  - [x] Enforce authority semantics, not a caller-selected label: a value adopted verbatim from an exact responsible-source use is `direct`; a deterministic output is `derived`; a preserved local observation is `measured`; a researcher-selected frozen value is `preregistered_factor`; and `mock` is permitted only when the immutable mock admission itself is genuinely the value authority and none of the other four applies. Reject relabelling a vendor value as `mock`, a researcher choice as `direct`/`mock`, or any other intentional class promotion even when only one authority branch was serialized.
  - [x] Require `value_role` independently of class and pin v1 exactly to `single`, `lower_endpoint`, and `upper_endpoint` so minimum/maximum records for the same consumer are not mistaken for conflicts. Any additional role requires a schema-version change. The conflict/selection slot is logical parameter plus scope/profile, consumer slot, and value role; `parameter_revision_id` is the selected value and is never part of that key. Numeric equality alone neither creates nor resolves a conflict.
  - [x] Pin structural record state to `valid`, `blocked`, `unresolved`, or `legacy_only`; approval/freeze state to `approved`, `planning_frozen`, `conditional`, `candidate`, `pending_source`, or `pending_decision`; parameter accountability outcome to `accountable` or `blocked`; and activity authorization to the closed value `none`. These axes remain separate on every record/result.
  - [x] Define typed numeric values instead of the current ambiguous strings: `scalar` with one canonical decimal; `interval` with lower/upper decimals and explicit inclusivity; `constant_result` derivation with a declared reproduced output; `observation_transform` with typed I/O and conformance vectors; and `unresolved` only for preserved planning evidence that cannot pass a formal required set. Reject booleans, integers/floats injected through JSON, NaN, Infinity, negative zero, free-form `0..100`, free-form formulas, and `UNRESOLVED` in executable value fields. Prefer separate scalar endpoint records when downstream consumers select LRV and URV independently.
  - [x] Parse canonical decimal strings directly and never construct scientific identity values from binary `float`. Pin the v1 arithmetic context to precision 50 and `ROUND_HALF_EVEN`, with traps for `FloatOperation`, `InvalidOperation`, `DivisionByZero`, `Overflow`, `Underflow`, `Inexact`, and `Rounded`; permit no implicit quantization, epsilon, tolerance, or alternate rounding mode. Therefore a non-terminating or precision-losing v1 result fails closed. Supporting explicit quantization later requires identity-bearing quantum/rounding metadata and a schema-version change.
  - [x] Pin the complete v1 unit vocabulary to `mA`, `percent`, `one`, `degC`, `bar`, `rpm`, `second`, `millisecond`, `count`, and `byte`. Pin the complete v1 `quantity_kind` vocabulary to `loop_current`, `normalized_span`, `temperature`, `pressure_gauge`, `pressure_absolute`, `rotational_speed`, `speed_reference`, `capacity_reference`, `power_reference`, `noise_amplitude`, `dynamic_factor`, `comparison_tolerance`, `decision_threshold`, `window_length`, `queue_capacity`, `capture_loss_fraction`, `duration`, `ramp_duration`, `dwell_duration`, `repetition_count`, `random_seed`, `model_hyperparameter`, `training_stopping`, `split_fraction`, `calibration_parameter`, `metric_parameter`, and `fusion_parameter`. Treat percent and dimensionless as distinguishable representations; treat Celsius as affine and forbid unrestricted multiplication/division of absolute temperatures. `rpm` is a bounded project unit token in v1, not a claim that BIPM supplies a project conversion. Any additional unit, quantity kind, operation, or meaning requires a schema-version change.
  - [x] Keep mandatory `limitations` separate from a typed `uncertainty` record. The latter identifies `uncertainty`, `dispersion`, or `not_applicable`; applicable records contain estimate/unit, method/model, sample or input identities, coverage information where applicable, and artifact/source reference, while `not_applicable` requires a scoped rationale. Observed dispersion is never silently promoted to measurement uncertainty.
  - [x] Define schema-specific canonical encoding exactly: UTF-8, LF, compact JSON separators, sorted object keys, `ensure_ascii=False`, `allow_nan=False`, schema-ordered arrays sorted by stable IDs, and one final newline. Canonical decimals must match ASCII `^-?(0|[1-9][0-9]*)(\.[0-9]*[1-9])?$`, with `-0`, exponent notation, whitespace, underscores, Unicode digits, specials, and redundant trailing zeros rejected. Evidence-record hash payloads omit their own self-ID fields; current time, filesystem mtime, and absolute paths are never identity inputs. `ParameterGateResult.v1` hashes its bound identities, outcome, and structured violation fields (`rule_id`, record/slot ID, field path, and offending token/reference), while excluding its own self-ID and human explanation text so wording changes cannot alter the scientific result identity.

- [x] Task 2: Create one reviewed machine authority and migrate the current planning ledgers without upgrading their claims (AC: 1-3, 6-11)
  - [x] Add `docs/reference-archive/catalog/parameter-evidence.v1.json` as the sole machine authority. Use flat arrays joined by stable IDs for parameter revisions, decision records, mock admissions/support claims, measurement references, derivation specifications, numeric-consumer inventories/requirements, required binding sets, numeric-locus audit entries, and legacy quarantine entries; do not add a database, registry service, or workflow engine.
  - [x] Migrate every current row from `parameter-evidence.csv` (15 planning rows), `decision-custom-reference-window-v1.yaml`, `mock-admission-ptfp-signal-emulator-v1.yaml`, and `legacy-constant-quarantine-v1.csv` (20 quarantined legacy rows). Preserve original IDs, content identities, meanings, limitations, and blocked/conditional states. Never infer missing data from code defaults, filenames, modification times, nearby documentation, or the desired experimental outcome.
  - [x] Preserve every original planning status in `migration_status` and map it deterministically: `approved` and `approved_derived` to (`valid`, `approved`); `approved_planning_frozen` to (`valid`, `planning_frozen`); `approved_conditional` to (`valid`, `conditional`); `approved_profile_candidate` to (`valid`, `candidate`); `blocked_pending_source_archive` to (`blocked`, `pending_source`); and `blocked_unresolved_decision` to (`unresolved`, `pending_decision`). Accountability is recomputed by the gate and remains blocked whenever any reference, temporal proof, inventory slot, or class validator fails.
  - [x] Treat the existing CSV/YAML files as frozen migration inputs/compatibility snapshots registered by content identity, not competing runtime authorities. Update `docs/reference-archive/README.md` to identify the JSON authority and explain how compatibility records are audited; do not implement an ad hoc general YAML parser or add a YAML dependency for this story.
  - [x] Preserve the honest current blockers: the Siemens P200 pressure candidate lacks verified official source bytes; the FB420 does not define project RPM LRV/URV; the signal-emulator admission is planning-conditional and execution-blocked; no current row supplies a complete measured-evidence chain; and the 15-row ledger is not a complete formal v2 parameter universe.
  - [x] Resolve each adopted source reference through the exact Story 9.3 `source_revision_id` and bounded `source_use_id`. A logical `source_id`, broad project-use sentence, or candidate-applicable source is insufficient. If the required Story 9.3 record is unresolved, preserve the parameter as blocked rather than minting a source-use identity.
  - [x] Preserve the distinct current authorities: Danfoss 6-12=4 mA and 6-13=20 mA may be direct documented device facts; 6-14=0%, 6-15=100%, and the 25%/75% factors remain researcher decisions; the 8 mA/16 mA values remain derivations. Do not describe any of the project selections as Danfoss defaults, recommendations, power factors, or universal ranges.
  - [x] Audit the declared inputs of the existing derivations. Missing identities such as generic loop-current endpoints must be resolved to exact profile-scoped parameter revisions or remain blocked; do not silently retarget them to similarly valued command parameters.
  - [x] As an explicit Story 9.3 catalog mutation boundary, register `tool-python-314-decimal` with the exact Python 3.14 documentation revision/use and `std-bipm-si-brochure-9-v4.01-2026` with the exact BIPM edition/version/DOI and bounded unit-vocabulary use before Story 9.4 relies on them. Add exact located `std-jcgm-100-2008` source-use records for Introduction 0.1 (quantitative quality indication), 0.7 item 1 (complete components/method reporting), and 2.2.3 (uncertainty as dispersion associated with a result). Preserve Story 9.3 projections/tests and do not treat any of these technical sources as device-value authority.

- [x] Task 3: Implement deterministic structural, identity, scope, conflict, and source validation (AC: 1-3, 9-12)
  - [x] Add `src/parallel_truth_fingerprint/evidence/parameter_evidence.py`, reusing Stories 9.1-9.3 vocabulary, canonicalization, source-catalog, and evidence identities. If any prerequisite contract/export or its focused tests are absent, stop rather than create a duplicate enum, placeholder source resolver, or competing canonicalizer.
  - [x] Return frozen ordered violations containing stable rule ID, parameter/revision/authority ID, field path, offending reference/token, and actionable explanation. Consumers must not parse free text to decide pass/fail.
  - [x] Reject duplicate immutable IDs, overlapping active revisions without explicit immutable selection, conflicting values/units/classes/authorities, mutable aliases, unsupported schema/version, unresolvable references, invalid canonical decimals, invalid units, insufficient scope, and any silent class promotion. Multiple historical revisions may coexist, but the conflict/selection slot is the logical parameter plus scope/profile, consumer slot, and value role—never `parameter_revision_id`; exactly one immutable revision must be selected for each required slot.
  - [x] Require each parameter to bind quantity kind, profile/experiment scope, authentic-reproduction feasibility, prototype component, bounded research question, evidence track, final-package element, transferability rationale, typed uncertainty where applicable, limitations, owner/approval identity, and exact code/config consumer locator where applicable.
  - [x] Define FR76 scope precisely: every number that can affect formal v2 data generation, acquisition quality, preprocessing, modeling, decision, comparison, evaluation, or fusion belongs in a required set. Infrastructure-only values such as network ports are outside FR76 only when an explicit classification and rationale prove they cannot affect scientific evidence; names or code location alone do not provide that exemption.
  - [x] Do not use source-code scanning as scientific authority or automatic catalog completion. An explicit consumer/required-set inventory is controlling; optional static audits may report unregistered candidate numeric loci but may never infer a value, class, source, applicability, approval, or pass outcome.

- [x] Task 4: Validate `direct` source authority and transferability (AC: 2-3, 7-8, 10)
  - [x] Require a located Story 9.3 source-use record from the responsible manufacturer, standards/protocol body, or dataset owner, bound to the exact source revision, typed locator, documented numeric fact, selected variant/release, component, question, track, and final-package scope.
  - [x] Validate that the source-use claim type is `direct_value`, the official issuer is responsible for the exact fact, transferability is explicit and bounded, and prohibited interpretations do not conflict with the parameter use. A scholarly/contextual/secondary source, repository README, mirror, landing page, or neighboring table value cannot become direct authority.
  - [x] Permit link-only/restricted official evidence only when Story 9.3 can qualify the exact immutable edition and clause observation. Missing required bytes, digest mismatch, mutable-only content, or unresolved locator keeps the direct parameter blocked; validation never downloads or fabricates evidence.
  - [x] Apply the known device boundaries in tests: accept the exact Danfoss 4/20 mA documented facts when all identities resolve; reject Danfoss as authority for project 0/100 or 25/75 selections; keep P200 blocked without the official bytes; and reject FB420 as authority for anonymous 1200/4200 RPM endpoints.

- [x] Task 5: Validate derived parameters with an allowlisted exact operation registry (AC: 4, 10-11)
  - [x] Represent derived computations as data for a versioned allowlisted operation registry, never Python expressions and never `eval`, `exec`, dynamic import, or general AST execution. Pin the v1 registry exactly to `affine_map.v1`; additional operations require reviewed versioned additions.
  - [x] Split derived evidence into `constant_result` and `observation_transform`. A constant result declares one exact reproduced value, as for 8/16 mA. An observation transform declares typed observation variables, exact parameter input closure, output quantity kind/unit, and deterministic conformance vectors (including applicable endpoints and midpoint) with expected outputs; `signal.normalized_current` and profile-specific engineering conversion are transforms, not single fixed outputs.
  - [x] Bind every operand to an exact parameter revision or a separately declared typed observation variable. Observation variables such as loop current are inputs to a transform, not numeric parameters and not a loophole for undeclared constants. Reject unused declared inputs and every anonymous domain literal; allow only operation-defined mathematical/unit constants.
  - [x] For `affine_map.v1`, validate exact input/output endpoints, unit/dimension compatibility, nonzero input span, output unit, Decimal context, and declared output. Detect missing nodes and dependency cycles before evaluation; sort traversal and diagnostics by immutable ID.
  - [x] Reproduce and test the bounded current mappings without generalizing their claims: 4-20 mA to normalized span, normalized span to a validated profile LRV/URV, and the frozen 25%/75% speed/capacity references to 8 mA/16 mA under the exact Danfoss command profile. Use `I = I_low + (I_high - I_low) * (reference - reference_low) / (reference_high - reference_low)` with all five numeric inputs bound; do not hard-code 4, 16, or the reference endpoints inside a derivation. No pressure/RPM/temperature endpoint or research factor may be supplied by the derivation engine.
  - [x] Require exact equality under the pinned non-rounding v1 decimal policy. A non-terminating result, precision loss, unit coercion, endpoint alias, conformance-vector mismatch, constant-result mismatch, or division by zero fails rather than applying quantization or a hidden epsilon.

- [x] Task 6: Validate measured evidence and uncertainty without performing a measurement (AC: 5, 10-12)
  - [x] Define the minimal pre-Story-9.6 `MeasurementEvidenceRef.v1`: evidence ID/version, immutable locator and SHA-256, method/procedure identity, environment and instrument/profile identity, sample and run identities, measurement timestamp, result/unit, dispersion/uncertainty representation and method, limitations, and owner/approval state. Do not pre-implement the generic `ArtifactManifest.v1` owned by Story 9.6.
  - [x] Require the parameter value/unit and evidenced result/unit to agree, bind the result to the exact environment/profile and method, validate the referenced bytes through an injected read-only resolver, and reject missing/mutable/mismatched evidence or universalized scope.
  - [x] Resolve measurement artifacts only beneath an explicitly supplied evidence root using normalized root-relative locators. Reject empty/absolute paths, `..`, traversal, and symlink/junction escape; stream opaque binary bytes for size/SHA-256 without deserializing or executing them. Normalize diagnostic paths deterministically and never expose an absolute host path.
  - [x] Preserve the absence of a qualifying measured row in the current catalog. Use small synthetic immutable fixtures to test the measured path; do not run a pilot, calibration, simulator, hardware process, service, or experiment and do not fabricate a current measured value.
  - [x] Record dispersion and uncertainty with distinct typed kinds and keep the method and components reconstructable, following the project-owned `std-jcgm-100-2008` source-use scope. A manufacturer specification may support a bounded Type-B component but does not authorize an arbitrary noise distribution; a citation to GUM does not itself calculate, certify, or transfer uncertainty for a parameter.

- [x] Task 7: Validate preregistered decisions and mock admissions without confusing authority or lineage (AC: 2, 6-8, 10-12)
  - [x] Validate `DecisionRecord.v1` as immutable and content-hashed, approved by the research owner, scoped to the exact parameter/component/question/experiment/track/output, and explicit about rationale, units, source constraints, limitations, and prohibited interpretations. Record approval/freeze time and test/truth-lock declarations now, but distinguish declaration from temporal proof: an injected immutable gate context containing later freeze/test/truth identities and timestamps must prove ordering before a formal gate can treat the decision as independently verified. A decision record is value authority for a researcher choice but is not an activity authorization.
  - [x] Require official source-use references cited by a preregistered factor to have only capability/constraint/feasibility roles for that selection. Reject any record that treats a vendor/standard citation as proof that the vendor chose, recommends, or universally validates the project factor.
  - [x] Pin authentic-reproduction feasibility to `available`, `unavailable_with_evidence`, or `unresolved`. A `mock` class can pass only with `unavailable_with_evidence`, an approved immutable `MockAdmission.v1`, documented authentic-path assessment, applicable official source uses, complete behavior/number support, limited purpose, replacement condition, and exact final-result linkage.
  - [x] Replace the current mock admission's broad prose support list with structured immutable support claims. Each `mock_claim_id` records expected value/unit/quantity kind/scope where numeric, supported behavior, and exact Story 9.3 source-use identities; it does not reference a parameter revision. A `mock` parameter revision depends one-way on the immutable admission plus the applicable `mock_claim_id`, eliminating circular content identity. Every asserted mock behavior/number must resolve independently; a broad list of reputable sources cannot make unsupported behavior pass.
  - [x] Keep parameter authority class and Story 9.2 synthetic lineage orthogonal. A researcher-selected 25/75 factor driving the admitted physical signal emulator remains `preregistered_factor`; observations produced by the emulator are `mock_derived`. It is not a second `mock` parameter class, and the output can never become `official_real`, `measured`, or real-plant evidence.
  - [x] Propagate Story 9.2 lineage through derivation inputs: any output depending on a mock-derived input remains `mock_derived` even if its numeric parameter authority is direct, derived, measured, or preregistered. Derivation cannot launder synthetic origin into official or measured evidence.
  - [x] Preserve `mock-admission-ptfp-signal-emulator-v1` as bounded to a controlled physical current-domain signal emulator, not a compressor digital twin. Reject universal compressor noise, dynamics, delay, bias, safety, energy, efficiency, operating ranges, and any synthetic syscall substitution unless a separate complete admission proves a specifically unavailable authentic behavior.

- [x] Task 8: Define an independent numeric-consumer inventory, complete required bindings, and the fail-closed accountability gate (AC: 9-12)
  - [x] Define immutable `NumericConsumerInventory.v1` independently from `RequiredParameterSet.v1`. It binds a component/contract/schema/code identity and enumerates every result-affecting numeric consumer slot as a `ParameterRequirement.v1` with slot ID, category, quantity kind/unit constraints, scope, value role, and whether `not_applicable` is ever permitted. A required set only selects one exact parameter revision for every inventory slot; it cannot define, omit, or relax its own universe.
  - [x] Pin the complete v1 category vocabulary exactly to `ranges_endpoints`, `schedule_setpoints`, `noise`, `dynamics`, `tolerances`, `thresholds`, `preprocessing_windows`, `queues_backpressure`, `capture_loss_quality`, `duration_ramp_dwell_timing`, `repetitions_seeds`, `model_training_hyperparameters_stopping`, `split_calibration`, `metrics_evaluation`, and `fusion`. Each inventory category has slots or an owner-approved scope-specific `not_applicable`; a required set cannot mark a category `not_applicable` when any inventory slot exists for it.
  - [x] Require callers to provide an immutable consumer inventory and `RequiredParameterSet.v1`; validating only catalog-present records or a caller-authored set can never produce `accountable`. The set binds exact catalog/source/vocabulary/inventory versions, scope/profile/experiment/component identities, and one selected revision per slot with no extras. Formal-v2 consumers must declare gate-required bindings and expose no result-affecting numeric defaults.
  - [x] Do not treat the migrated 15 rows as a complete required set. Create a planning `NumericConsumerInventory.v1` plus baseline binding set that expose unresolved slots/categories and produce a deterministic `blocked` result until later profile/experiment owners provide complete immutable inventories and bindings. Formal Epics 10+ consumers supply exact run/profile inventories/sets; Story 9.4 does not choose their values.
  - [x] Reject missing/duplicate/conflicting parameters, unresolved source/decision/measurement/mock references, legacy-only influence, non-transferable scope, invalid derivations/units, incomplete categories, unknown class tokens, mutable identities, and catalog/required-set version mismatch. Never insert an architecture default, current code default, nearest matching record, or last-created revision.
  - [x] Return exact catalog, source-catalog, vocabulary, consumer-inventory, required-set, decision, measurement, mock, and validator identities; deterministic ordered diagnostics; `accountability_outcome`; explicit limitations; and `authorization_effect: none`. The result is evidence for later startup/freeze/G9 callers, not a runtime or authorization mechanism.
  - [x] Store the known-locus audit as `NumericLocusAudit.v1` inside the machine authority with the closed dispositions `formal_v2_required`, `legacy_v1_only`, `infrastructure_exempt`, and `unresolved_future_v2`. Each entry binds a normalized component/consumer locator, category, scope/profile/value role/lineage, rationale, and related inventory/parameter/legacy identity. The audit detects candidates and exemptions but never supplies value authority.

- [x] Task 9: Add a read-only validator command and comprehensive table-driven tests (AC: 1-12)
  - [x] Add `scripts/validate_parameter_evidence.py` as a read-only check/report entry point requiring explicit catalog, source-catalog, consumer-inventory, required-set, and optional evidence-root paths. Pin exit codes to `0` for `accountable`, `1` for well-formed but `blocked`, and `2` for malformed input or usage failure. It may render canonical output or diagnostics to stdout but never writes, repairs, selects, downloads, activates, or mutates scientific/runtime state.
  - [x] Add `tests/evidence/test_parameter_evidence.py` using standard-library `unittest`, `subTest()`, temporary directories, deterministic clocks, small opaque artifact fixtures, and injected source/evidence resolvers. Tests require no ignored archive, network, Docker, MinIO, MQTT, OPC UA, CometBFT, datasets, Keras, hardware, training, capture, experiment, or UI.
  - [x] Cover each class's valid fixture and every class-specific failure; vendor value relabelled `mock`; researcher choice relabelled `direct`/`mock`; canonical-decimal whitespace/underscore/Unicode/exponent/special rejection; interval order; unit/dimension, quantity-kind, gauge/absolute-pressure, semantic-percent, and affine-Celsius rules; constant-result versus transform behavior; missing/unused input, cycle, anonymous literal, zero-span, conformance/output mismatch, and forbidden rounding; measured artifact hash/scope/dispersion/uncertainty failures; preregistration post-test/truth-informed/mutable/unproven-order failures; and mock reproducible/unresolved/unsupported/convenience/unfavorable-result failures.
  - [x] Cover duplicate/conflicting historical revisions and exact-one slot selection, mutable alias rejection, independent-inventory closure, a self-declared incomplete required set, illegal `not_applicable`, exact source-use applicability, Danfoss/P200/FB420 boundaries, 25/75 semantics, 8/16 reproduction, legacy quarantine, all closed completeness categories, deterministic bytes/hashes/order/diagnostics, and current-migration `blocked` outcome without fabricated repair.
  - [x] Cover measurement path traversal, absolute/empty locators, real symlink/junction escape when supported, and an injected fake resolver on every platform so Windows tests require no administrator or Developer Mode. Cover binary streaming hash mismatch, deterministic root-relative diagnostics, CLI exit codes 0/1/2, identity independence from current time, mtime, absolute checkout path, and self-ID, and a human-explanation wording change that leaves the structured `ParameterGateResult.v1` identity unchanged.
  - [x] Audit known v1 scientific numeric loci—including simulation ranges/weights/periods/noise, comparison tolerances, consensus scales/thresholds, demo timing/windows, capture/queue/loss settings, repetitions, model hyperparameters/thresholds, and fusion settings—as legacy-only, non-scientific infrastructure with rationale, or unresolved future-v2 requirements. Detect legacy collisions by component, consumer key, profile, value role, and lineage—not numeric equality. Prove that v2 required sets cannot inherit them implicitly; the audit report itself is not value authority.
  - [x] Assert `authorization_effect == "none"` on every success/failure path and prove validation performs no network, document acquisition, configuration change, runtime startup, training, capture, experiment, publication, dashboard, or other side effect.
  - [x] Run the focused module followed by `unittest` discovery. Preserve the dirty worktree and do not alter v1 runtime behavior or unrelated user files merely to make tests pass.

## Dev Notes

### Scope and dependency boundary

- This story owns numeric evidence sufficiency, the five parameter authority classes, `DecisionRecord.v1`, `MockAdmission.v1`, the minimal measured-evidence bridge, complete required-parameter declarations, and a deterministic accountability gate. It does not implement or activate any parameter consumer.
- Stories 9.1, 9.2, and 9.3 are hard implementation prerequisites. Their focused tests and exact public exports must exist before this story begins. Stop if they are absent; do not create local substitutes for the evidence baseline, vocabulary, source identities, source-use records, or canonicalization rules.
- Story 9.3 catalog inclusion means only that source evidence exists with a bounded use. This story independently decides whether that use is sufficient and transferable for one parameter class/value/scope.
- Story 9.5 owns golden v1 fixtures and replay. Story 9.6 owns the general `ArtifactManifest.v1`, provenance graph, run identities, and evaluation manifests. Story 9.7 owns persistent-storage qualification. Story 9.8 owns scientific partition/freeze/activity authorization. Epics 10+ own actual instrument profiles, experiment specs, acquisition, capture, models, evaluation, and required parameter sets for those activities.
- `ready-for-dev` means only that the implementation specification is complete. It does not authorize implementation. Implementation, document/data acquisition, calibration, training, syscall capture, experiment execution, model promotion, activation, publication, and deployment each remain separately unauthorized until the controlling immutable authorization exists.
- UI/UX is optional and entirely out of scope. Do not add or change dashboard screens, controls, visualizations, APIs, or frontend behavior for this story.

### Honest current-state boundary

- The current planning ledger has 15 unique rows: 5 direct, 4 derived, and 6 preregistered-factor candidates, with no qualifying measured row and no parameter whose numeric authority is currently `mock`. Its statuses include three explicit blockers (`blocked_pending_source_archive` plus two `blocked_unresolved_decision`) and several conditional/candidate records; the real migrated gate must remain red.
- A `mock` parameter class is not the same as downstream `mock_derived` lineage. Most numbers used by an admitted emulator remain direct, derived, or preregistered according to who selected the number.
- Current blocked facts must remain visible: P200 official bytes are not qualified; RPM endpoints are unresolved; the physical signal-emulator admission is conditional; none of the current 26 source occurrences binds an exact Story 9.3 source revision/use yet; and two existing derived records reference four missing input IDs (`signal.loop_current_low`, `signal.loop_current_high`, `instrument.profile.lrv`, and `instrument.profile.urv`). `signal.engineering_value` also has the non-executable placeholder unit `configured engineering unit`. These defects are regression fixtures, not values to repair implicitly.
- Existing v1 ranges, simulation weights/periods/noise, secondary formulas, tolerances, consensus scales/thresholds, demo cadence, window counts, ML hyperparameters, and decision thresholds are not silently grandfathered into v2. The current 20-entry quarantine is internally consistent but not exhaustive for result-affecting runtime/offline defaults. Exact v1 reproduction may retain quarantined identities; formal v2 must supply evidence or declare the category inapplicable for its exact scope.
- Operational/infrastructure numbers are not automatically scientific parameters, but an explicit consumer classification must establish that they cannot affect evidence. Queue capacity, timing, capture loss, preprocessing windows, repetitions, thresholds, and fusion settings normally affect evidence and therefore cannot be dismissed as infrastructure defaults.
- Completeness comes from an independently frozen consumer inventory, not from the parameter binding set. A later formal component that adds or changes a result-affecting numeric slot must create a new inventory identity and cannot retain a passing old set.

### Numeric, unit, and derivation design

- Use canonical decimal strings and the standard-library `decimal` module. Python's official documentation confirms exact decimal representation and exposes traps for accidental float mixing. Record the context and rounding rule in each derivation identity; reject NaN/Infinity and avoid binary-float construction.
- Keep v1 derivations deliberately small. A data-driven allowlisted `affine_map.v1` operation covers the documented 4-20 mA normalization, engineering conversion, and 25/75-to-8/16 mapping. It is safer and more reviewable than a general expression language.
- Keep fixed derived values and observation transforms distinct. A transform is qualified by its immutable operation/input closure and conformance vectors, not by pretending it has one universal output value.
- Unit validation is bounded to the project's declared units, dimensions, and semantic quantity kinds, guided by the BIPM SI Brochure and the existing JCGM/GUM record. This story does not claim UCUM implementation or full symbolic dimensional algebra.
- GUM requires a quantitative indication of measurement-result quality and a complete account of uncertainty components/methods. Use that to require explicit measured-result uncertainty evidence; do not treat GUM as a source of device values, uncertainty numbers, or automatic transferability.

### Current code intelligence

- `config/ranges.py` contains the legacy 0-100 operating state, 48-95 degC, 1.8-8.5 bar, 1200-4200 rpm, and 0.15 base-noise defaults. `sensor_simulation/behavior_model.py` adds legacy mixture weights, offsets, oscillation periods/phases, and noise coupling. They remain exact-v1-reproduction evidence only.
- `comparison/service.py` contains legacy default tolerances 2.0 degC, 0.35 bar, and 120 rpm. `consensus/trust_model.py` contains legacy normalization scales 20/3/600 and thresholds 0.35/0.75. None may become a formal-v2 universal threshold through code existence.
- `config/runtime.py`, `lstm_service/lifecycle.py`, `lstm_service/trainer.py`, and `lstm_service/inference.py` expose cadence, cycle/window, sequence, training, architecture, and threshold defaults that later v2 scopes must either evidence or explicitly exclude. Dashboard display of a value does not make it authoritative and requires no UI work here.
- Preserve the existing frozen-dataclass and deterministic `to_dict()` style, use Python `>=3.14`, and add no dependency. Hash referenced opaque evidence without executing or deserializing it.

### Project Structure Notes

- Contracts: `src/parallel_truth_fingerprint/contracts/parameter_evidence.py`.
- Validation/canonicalization: `src/parallel_truth_fingerprint/evidence/parameter_evidence.py`.
- Machine authority: `docs/reference-archive/catalog/parameter-evidence.v1.json`.
- Frozen migration inputs: `docs/reference-archive/catalog/parameter-evidence.csv`, `decision-custom-reference-window-v1.yaml`, `mock-admission-ptfp-signal-emulator-v1.yaml`, and `legacy-constant-quarantine-v1.csv`.
- Read-only command: `scripts/validate_parameter_evidence.py`.
- Tests: `tests/evidence/test_parameter_evidence.py`.
- Documentation: `docs/reference-archive/README.md`.
- Explicit Story 9.3 mutation boundary for the Decimal/BIPM/JCGM source records/uses: `docs/reference-archive/catalog/source-catalog.v1.json`, its deterministic `index.md`/`checksums.sha256` projections when affected, and `tests/evidence/test_source_catalog.py`. Run the Story 9.3 focused suite after these catalog additions before the Story 9.4 focused suite.
- Do not add a database, API route, registry service, workflow engine, configuration UI, scientific dashboard, formula interpreter, unit-framework dependency, runtime hook, experiment runner, or activity-authorization mechanism.

### Technical Research Notes

- Python 3.14 `decimal` supports exact decimal representation and controllable precision/rounding/traps. Adopt it for catalog arithmetic and register `tool-python-314-decimal` in the implemented Story 9.3 source catalog as bounded technical implementation guidance, observed on 2026-08-22; it is not domain-value authority.
- JCGM 100:2008 states that a measurement result needs quantitative quality information and that detailed uncertainty reporting identifies the contributing components and the method used for each. The existing `std-jcgm-100-2008` source remains the primary uncertainty-method reference after Story 9.3 binds the exact located use; the story does not infer any uncertainty value from it.
- The BIPM SI Brochure, 9th edition (2019), version 4.01 of the official text updated in 2026, supplies the official unit-system context. Register `std-bipm-si-brochure-9-v4.01-2026` through Story 9.3 with the exact edition/version/DOI and bounded unit-vocabulary use before qualifying it; do not use it as authority for device ranges or project factors.

### Testing Standards

- Use standard-library `unittest`, table-driven `subTest()` cases, temporary directories, deterministic clocks, exact canonical bytes, and injected resolvers. Assert stable rule IDs and field paths rather than only prose messages.
- Keep tests independent of ignored source bytes and live services. Real-catalog validation may be an explicit read-only developer command, but unit tests use small synthetic sources and opaque evidence objects.
- A structurally valid catalog may still produce a blocked gate. Tests must prove that unresolved truth is preserved and that no repair/default path exists.
- Run full discovery because new public exports and the shared `evidence` boundary can affect existing imports even without runtime integration.

### Amendment enforcement: numeric and mock authority

Extend the existing `MockAdmission.v1` validation with the amendment's immutable prototype-generation binding. A domain mock passes only when the exact entrypoint, code/configuration/parameter/seed closure, permitted output role, emission trace, official source-use locator/hash, and current authentic-path assessment all resolve. Use a pure frozen contract/validator; do not create a new service or grant authorization.
## BMAD Party Mode Review

- Final architecture/scope score: 9.6/10 — no veto.
- Final academic-evidence/prototype-focus score: 9.7/10 — no veto.
- Final QA/developer-readiness score: 9.7/10 — no veto.
- Aggregate score: 9.67/10.
- Auto-approval rule: score at least 9.0 with no veto.
- Decision: auto-approved as `ready-for-dev` after all identity, completeness, transform, authority-precedence, canonicalization, source-boundary, path-safety, and testability vetoes were corrected and re-scored.
- Boundary: this decision approves the planning artifact only; `authorization_effect` remains `none`.

### References

- [Source: _bmad-output/planning-artifacts/epics.md#Cross-Epic Mock Admission Guardrail]
- [Source: _bmad-output/planning-artifacts/epics.md#Story 9.4: Build the Parameter-Evidence Catalog and Validation Gate]
- [Source: _bmad-output/planning-artifacts/prd.md#FR76]
- [Source: _bmad-output/planning-artifacts/prd.md#NFR39-NFR40]
- [Source: _bmad-output/planning-artifacts/prd.md#NFR44]
- [Source: _bmad-output/planning-artifacts/prd.md#NFR48-NFR52]
- [Source: _bmad-output/planning-artifacts/architecture.md#Controlling V2 Architecture Consolidation - 2026-08-22]
- [Source: _bmad-output/planning-artifacts/architecture.md#Authoritative evidence contracts]
- [Source: _bmad-output/planning-artifacts/architecture.md#Exact command-profile and parameter mapping]
- [Source: _bmad-output/planning-artifacts/architecture.md#Bounded physical signal emulator admission]
- [Source: _bmad-output/implementation-artifacts/9-1-freeze-and-index-the-v1-evidence-baseline.md]
- [Source: _bmad-output/implementation-artifacts/9-2-establish-the-semantic-and-evidence-role-vocabulary.md]
- [Source: _bmad-output/implementation-artifacts/9-3-build-the-authoritative-source-evidence-catalog.md]
- [Source: docs/reference-archive/catalog/parameter-evidence.csv]
- [Source: docs/reference-archive/catalog/decision-custom-reference-window-v1.yaml]
- [Source: docs/reference-archive/catalog/mock-admission-ptfp-signal-emulator-v1.yaml]
- [Source: docs/reference-archive/catalog/legacy-constant-quarantine-v1.csv]
- [Source: docs/reference-archive/catalog/index.md#Standards and specifications]
- [Source: src/parallel_truth_fingerprint/config/ranges.py]
- [Source: src/parallel_truth_fingerprint/config/runtime.py]
- [Source: src/parallel_truth_fingerprint/sensor_simulation/behavior_model.py]
- [Source: src/parallel_truth_fingerprint/comparison/service.py]
- [Source: src/parallel_truth_fingerprint/consensus/trust_model.py]
- [Source: src/parallel_truth_fingerprint/lstm_service/lifecycle.py]
- [Source: src/parallel_truth_fingerprint/lstm_service/trainer.py]
- [Source: src/parallel_truth_fingerprint/lstm_service/inference.py]
- [Python 3.14 `decimal`](https://docs.python.org/3.14/library/decimal.html)
- [JCGM 100:2008 (GUM)](https://www.bipm.org/documents/20126/2071204/JCGM_100_2008_E.pdf)
- [BIPM SI Brochure](https://www.bipm.org/en/publications/si-brochure/)

## Mandatory Academic Evidence Amendment

Before implementation, apply the relevant mandatory controls in [Academic Evidence Admission Amendment — 2026-08-31](../planning-artifacts/academic-evidence-admission-amendment-2026-08-31.md). This story must fail closed on an unresolved evidence origin, numeric authority, required mock closure, or prohibited dataset substitution. The amendment adds no activity authorization.
## Dev Agent Record

### Agent Model Used

GPT-5 Codex

### Debug Log References

- 2026-09-04: Verified Stories 9.1-9.3 focused prerequisites (145 tests, 3 expected skips) before implementation.
- 2026-09-04: Executed the Story 9.3 source-catalog suite after Decimal/BIPM/JCGM additions (37 tests passed).
- 2026-09-04: Executed the Story 9.4 focused suite and CLI 0/1/2 paths (13 tests passed).
- 2026-09-04: Executed safe repository regression discovery excluding separately unauthorized training/offline-training suites (275 tests passed, 6 expected skips).
- 2026-09-04: `compileall` and `git diff --check` passed; no network, acquisition, training, capture, experiment, publication, or activation was performed.
- 2026-09-04: Implemented all 12 accepted code-review corrections and reran the focused parameter/source suite (51 tests passed), the full evidence suite (159 tests passed, 3 expected skips), and the safe repository regression (276 tests passed, 6 expected skips).

### Completion Notes List

- Implemented immutable flat ParameterEvidence.v1 contracts with closed authority, numeric, unit, quantity, inventory, uncertainty, lineage, decision, mock, measurement, audit, and gate types.
- Added deterministic canonical serialization, exact Decimal affine-map reproduction, structured stable diagnostics, path-safe opaque measurement verification, and a fail-closed accountability gate whose authorization effect is always `none`.
- Migrated all 15 planning rows, the frozen decision with exact selected values, the conditional structured mock admission, 20 legacy quarantine entries, and 28 normalized numeric-locus audit entries into the sole JSON machine authority without repairing unresolved evidence.
- Registered and validated the bounded Python Decimal, BIPM SI Brochure, and exact JCGM source uses while preserving Story 9.3 projections.
- Preserved the honest planning outcome as `blocked`: P200 bytes, RPM decisions, two transform input closures, the engineering-unit placeholder, temporal decision proof, and the independent noise slot remain unresolved.
- Added a read-only CLI with exit codes 0 accountable, 1 blocked, and 2 malformed/usage; documented authority and compatibility-snapshot handling.
- Closed the review findings with exact inventory/set object binding, per-revision and structured-record digests, bound source-catalog validation, temporal proof identities, semantic derivation and uncertainty checks, active-revision conflict rejection, complete mock-generator closure, strict JSON scalar types, and traceback-free malformed-input handling.
- Kept unresolved machine records explicit and blocked instead of fabricating evidence; review correction changes add no activity authorization and do not execute training, capture, acquisition, or experiments.

### File List

- `_bmad-output/implementation-artifacts/9-4-build-the-parameter-evidence-catalog-and-validation-gate.md`
- `_bmad-output/implementation-artifacts/sprint-status.yaml`
- `docs/reference-archive/README.md`
- `docs/reference-archive/catalog/checksums.sha256`
- `docs/reference-archive/catalog/index.md`
- `docs/reference-archive/catalog/parameter-evidence.csv`
- `docs/reference-archive/catalog/parameter-evidence.v1.json`
- `docs/reference-archive/catalog/source-catalog.v1.json`
- `scripts/validate_parameter_evidence.py`
- `src/parallel_truth_fingerprint/contracts/__init__.py`
- `src/parallel_truth_fingerprint/contracts/parameter_evidence.py`
- `src/parallel_truth_fingerprint/evidence/parameter_evidence.py`
- `tests/evidence/test_parameter_evidence.py`

## Change Log

- 2026-09-04: Implemented Story 9.4 parameter authority, migration, deterministic accountability validation, read-only CLI, documentation, and focused regression coverage; moved to review.
- 2026-09-04: Resolved all 12 accepted review findings, expanded focused regression coverage, preserved the honest blocked planning baseline, and completed Story 9.4 without another broad adversarial review as authorized by the owner.
