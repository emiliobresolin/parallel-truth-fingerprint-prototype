# Story 9.5: Preserve v1 Contracts as Golden Versioned Fixtures

Status: review

<!-- Note: Planning READY does not authorize implementation or scientific activity. -->

## Story

As a prototype maintainer,
I want the existing v1 contracts preserved as explicit golden fixtures,
so that v2 capabilities can be introduced without rewriting history or breaking reproducibility.

## Acceptance Criteria

1. **Given** the verified Story 9.1 v1 baseline **When** the golden fixture set is assembled **Then** its independently declared core inventory covers representative MQTT topics and observation payloads; Python/Go consensus transactions, committed states, queries, status and exclusion decisions; MinIO-compatible object keys and content; existing dataset/artifact manifests; and available legacy detector input/output contracts **And** dashboard/read-model fixtures remain an optional group whose absence cannot fail the core set.

2. **Given** a fixture is registered **When** its identity is validated **Then** it records a stable logical fixture ID and immutable revision ID, `baseline_generation: v1`, exact native contract ID and explicit native version or `versionless` status, immutable Story 9.1 baseline provenance, origin, storage and serialization form, decoded byte length and SHA-256, Story 9.2 semantic identity, `expected_legacy_reader_outcome`, `expected_fixture_gate_outcome`, comparison mode, reader/comparator identity, limitations, prohibited uses, and `authorization_effect: none` **And** neither expected outcome is represented as scientific, domain, dataset, or model validity.

3. **Given** a versionless historical payload **When** the v1 reader is selected **Then** an immutable fixture registration binds its exact content hash to that reader before deserialization **And** arbitrary unregistered versionless bytes fail closed rather than being inferred as v1 from shape, filename, topic, object prefix, or an unrelated embedded token.

4. **Given** a deliberately non-domain sentinel or reconstructed fixture **When** it is used in the passing set **Then** it remains conspicuously test-only and cannot assert domain validity **And** every newly constructed or reconstructed fixture that represents domain behavior or a domain numeric value resolves an approved Story 9.4 mock admission, exact parameter revisions, and applicable Story 9.3 official source-use locators proving authentic reproduction unavailable and tightly linking the mock to its bounded prototype question and final dataset-comparison element; otherwise that requirement remains blocked.

5. **Given** preserved historical bytes contain domain-looking values or an anonymous legacy constant **When** they are registered **Then** they remain `legacy_v1` / `legacy_recorded` / `legacy` compatibility evidence with only `contract_fixture_replay` scope **And** replay cannot promote them to current domain evidence, a qualified mock, locally measured evidence, `official_real`, or a formal v2 parameter.

6. **Given** historical bytes or object identities are preserved **When** an envelope, decoded projection, or adapted representation is required **Then** the original bytes and object identities remain unchanged **And** every adapted output is a separate immutable fixture revision with its own contract/version, explicit field-level transformation, provenance, length, hash, and comparison rule.

7. **Given** v2 is disabled and a registered v1 fixture is replayed **When** explicit version routing runs **Then** the named v1 reader performs only pure parse, serialize, validate, or compare operations and reproduces `expected_legacy_reader_outcome`, including a documented unsafe acceptance or Python/Go divergence where historically observed **And** the separate Story 9.5 fixture gate evaluates `expected_fixture_gate_outcome` without claiming that its stricter policy was native v1 behavior or starting any MQTT, CometBFT, MinIO, OPC UA, dashboard, model, or training runtime.

8. **Given** a missing, unknown, unsupported, hash-mismatched, mutable, or incompatible version/fixture/reader/comparator is supplied, or a v1 detector/model input contains a v2-only, missing, extra, or permuted feature **When** registration or replay validation runs **Then** the fixture gate fails closed with stable rule ID, artifact/fixture/contract identity, field path, expected value, and observed value or reason **And** registered adversarial content separately records the named legacy reader's actual accept/reject behavior rather than being sanitized before that behavior can be tested.

9. **Given** the golden regression suite is run repeatedly **When** bytes, semantic values, ordering, encoding, version binding, or declared behavior have not changed **Then** outcome, canonical catalog bytes, hashes, and diagnostics are deterministic **And** any drift identifies the affected contract, fixture, comparison rule, expected result, and observed result without an automatic snapshot-regeneration or bless path.

10. **Given** every core golden fixture passes **When** the result is reported **Then** it proves only the declared historical contract preservation and incompatibility checks for that closed inventory **And** fixtures remain excluded from dataset roots, samples, windows, labels, denominators, metrics, rankings, truth, uncertainty, final cross-dataset result tables, and all implementation, acquisition, fitting, training, capture, experiment, promotion, activation, publication, deployment, or migration authorization.

## Tasks / Subtasks

- [x] Task 1: Enforce prerequisites and freeze an independent fixture-requirement inventory (AC: 1, 4-5, 10)
  - [ ] Treat Stories 9.1-9.4 as hard implementation prerequisites. Require their public contracts, resolvers, machine authorities, and focused suites to exist and pass before Story 9.5 code begins. Stop rather than duplicate canonicalization, evidence roles, source identities, parameter identities, mock admission, or baseline resolution.
  - [ ] Define `V1GoldenFixtureRequirementSet.v1` independently from caller-supplied catalog entries. Pin stable required slots for MQTT/topic/observation boundaries; Python and Go consensus transaction/state/query/decision boundaries; persistence object key/content and extant manifest boundaries; legacy detector input/output/schema/incompatibility boundaries; and a separate optional dashboard group. A catalog cannot pass by omitting a difficult required slot or declaring it not applicable.
  - [ ] Pin the exact v1 requirement-set identity in code, together with every required slot ID, cardinality, and core/optional group. Catalog data and a caller-supplied requirement file cannot jointly substitute a smaller inventory and still pass.
  - [ ] Require representative positive and adversarial paths: optional MQTT `sv` behavior; malformed/truncated/duplicate-key/non-UTF-8 payloads; missing/unknown versions; consensus success, exclusion, failed consensus, query-found/query-missing, ordering and one preserved Python/Go divergence; missing/corrupt object content; manifest/schema mismatch; detector missing/extra/permuted/v2-only features; and missing optional dashboard material. Each adversarial slot declares both its native-reader expectation and fixture-gate expectation.
  - [ ] Document the closed inventory in a compact slot table containing stable requirement ID, native reader, origin, expected legacy-reader outcome, expected gate outcome, and comparison mode, so completeness is auditable without inferring it from catalog contents.
  - [ ] Resolve every frozen historical item to exact Story 9.1 `baseline_id` and baseline entry identity. Where the verified baseline lacks a required byte/object/result, emit a stable blocked requirement result; do not capture a new live run, retrain, infer, copy an easy neighbor, or fabricate an oracle to make the inventory green.

- [x] Task 2: Define the flat fixture catalog, comparison, routing, and diagnostic contracts (AC: 2-3, 5-9)
  - [ ] Add `src/parallel_truth_fingerprint/contracts/v1_golden_fixture.py` with frozen dataclasses, tuple-backed collections/defensive copies, deterministic `to_dict()` methods, explicit `StrEnum` tokens, and schema identities for `V1GoldenFixtureCatalog.v1`, `V1GoldenFixtureEntry.v1`, `V1GoldenFixtureRequirementSet.v1`, `V1GoldenAdapterDeclaration.v1`, `V1GoldenReplayRequest.v1`, `V1GoldenReplayResult.v1`, and structured violations. Re-export only intended public types from `contracts/__init__.py`.
  - [ ] Keep `baseline_generation: v1` separate from the artifact's observed native contract version. Record `native_contract_id`, `native_version_status` (`explicit` or `versionless`), and the untouched native token where present. In particular, preserve the legacy persistence payload's embedded `"artifact_version": "2.0"`; never reinterpret or rewrite it as the fixture generation.
  - [ ] Pin exactly one fixture origin: `frozen_historical_bytes`, `reconstructed_legacy_fixture`, `non_domain_sentinel`, or `admitted_domain_mock_fixture`. A reconstruction must bind exact frozen v1 code/runtime/seed, may never be called an observed historical capture, and may enter the passing core only with conspicuous non-domain sentinels or the complete admitted-domain-mock evidence chain.
  - [ ] Reuse Story 9.2 axes exactly. Frozen historical records use the Story 9.2 mapping to `legacy_v1` + `legacy_recorded` + `legacy`; reconstructed legacy and non-domain sentinel records use `fixture_test` + `fixture_expected` + `test_only` + `not_applicable`; admitted domain mock fixtures use `fixture_test` + `fixture_expected` + `test_only` plus the exact applicable `mock`/`mock_derived` lineage and admission reference. Reject fixture promotion to `custom_generated`, `official_real`, `locally_measured`, `qualified`, or final-result roles.
  - [ ] Require immutable root-relative locators, storage encoding (`raw` or canonical base64 carrier), media type, character encoding/newline form where applicable, decoded byte length/hash, expected output/diagnostic identity, named reader, comparison mode, comparator version, environment/runtime limitation, and prohibited uses. Pin both outcome fields to explicit `accepted`, `rejected`, `not_invoked`, or `unverifiable`; a stable reason/diagnostic expectation is mandatory for any value other than `accepted`.
  - [ ] Pin comparison modes to `byte_exact` or `semantic_exact`. `semantic_exact` must name an allowlisted contract-specific comparator/version with exact compared fields and ordering rules; it cannot ignore result-affecting fields, default values, coerce types, or introduce an unevidenced epsilon/tolerance. Adversarial NaN/Infinity, duplicate-key, malformed, or non-UTF-8 bytes may be stored only to test the declared reader/gate outcomes and are never valid catalog JSON. SHA-256 establishes byte identity/change detection only, not authorship, provenance, scientific validity, or semantic equivalence.
  - [ ] Canonicalize only Story 9.5's catalog/result records using the prerequisite bounded encoder: UTF-8, LF, compact separators, sorted object keys and schema-defined arrays, `ensure_ascii=False`, `allow_nan=False`, and one final newline. Never canonicalize, pretty-print, or reserialize original historical wire/object bytes to make them match this representation.
  - [ ] Define separate logical and immutable identities for every requirement set, fixture entry, catalog, adapter declaration, replay request, and replay result. Pin each canonical identity preimage and self-ID exclusions; replay-result identity includes bound request/catalog/fixture identities, outcomes, and structured violations while excluding its own ID and mutable explanation text.
  - [ ] Return deterministically sorted violations with stable rule ID, fixture/requirement/contract ID, field path, bounded/redacted offending reference or token, expected value, observed value, and explanation. Secret or arbitrarily large malformed content is never echoed. Scientific outcome identity excludes mutable wording while retaining structured diagnostic facts.

- [x] Task 3: Assemble the reviewed shared v1 golden corpus without rewriting history (AC: 1-6, 9-10)
  - [ ] Add the shared, versioned, append-only authority under identity-addressed paths: `testdata/golden/v1/requirements/sha256-<digest>/requirements.v1.json`, `testdata/golden/v1/catalogs/sha256-<digest>/catalog.v1.json`, and `testdata/golden/v1/fixtures/<fixture-id>/sha256-<digest>/...`. Add a README with claim limits and the required-slot table. Future changes create a new identity path; no singleton mutable catalog, `latest` alias, in-place update, or automatic snapshot blessing is permitted.
  - [ ] Preserve exact historical bytes in canonical RFC 4648 base64 carriers when Git checkout newline conversion could alter them. Require the standard alphabet, padding, ASCII only, no BOM, whitespace, line wrapping, or trailing newline; use strict decoding equivalent to `base64.b64decode(..., validate=True)`, re-encoding equality, and an explicit maximum decoded size before allocation. Hash and size the decoded original bytes and separately validate the carrier identity/encoding.
  - [ ] Add a narrowly scoped `.gitattributes` rule for `testdata/golden/v1/** -text` so catalog and carrier bytes survive `core.autocrlf=true`; tests still verify decoded historical bytes rather than treating a transformed checkout as the original MinIO/Git blob.
  - [ ] Bind the sample MinIO artifact, when selected by Story 9.1, to its exact baseline/Git-blob identity and observed key/content. Use the current fake/in-memory object-store adapter for tests; do not claim live MinIO durability, object locking, versioning, atomicity, or WORM behavior.
  - [ ] Register current HART sample text only as exact byte-level, expected-invalid legacy material where applicable: comments, mojibake, or incomplete fragments are preserved limitations, never executable JSON, a valid domain observation, or official HART authority.
  - [ ] Create deterministic serializer-derived fixtures only as `reconstructed_legacy_fixture`, with fixed timestamps/input/order/seed and independently reviewed expected bytes. Such a fixture may satisfy a reader-divergence slot only as an explicitly reconstructed, non-historical oracle; it must use non-domain sentinels or pass the full admitted-domain-mock gate. The implementation under test must never generate and bless its own expected value in the same run.
  - [ ] For current logs, preserve the original baseline object and bind any bounded JSON projection by source hash plus an RFC 6901 JSON Pointer. Never rewrite an extracted projection and describe it as the original historical bytes.
  - [ ] Preserve only available detector input/output, feature-schema, model/runtime/hash, and recorded score/classification records. Missing model weights or champion-run bytes remain blocked/unverifiable; `.npz` or Keras bytes are byte-exact only when an original opaque baseline object exists, otherwise compare decoded arrays/contracts semantically without regenerating archives or executing Keras.
  - [ ] Register the existing small ADFA-LD/LID-DS adapter fixtures, if they are within the Story 9.1 baseline, only as legacy/test-only exclusion cases. They are not official dataset bytes, their numeric syscall tokens are never executable Linux events, and formal dataset qualification/evaluation must reject their fixture roots.
  - [ ] Keep SCADA/dashboard projection fixtures optional and outside the core pass/fail set. If present, use fixed inputs and `generated_at`; do not start a dashboard/browser/server and do not add or redesign any UI/UX.
  - [ ] Scan selected fixture carriers and catalog fields for credentials, access keys, private keys, tokens, `.env` contents, CometBFT keys, or secret-bearing log fragments. Redact by exclusion before registration; never hash low-entropy secret values into fixture metadata.

- [x] Task 4: Enforce the legacy, sentinel, and admitted-domain-mock boundaries (AC: 4-5, 10)
  - [ ] Preserve domain-looking content without current Story 9.3/9.4 authority only when it is exact `frozen_historical_bytes` and only for `contract_fixture_replay`. A reconstruction does not inherit that carve-out merely by using v1 code/constants or a legacy label.
  - [ ] Permit `non_domain_sentinel` only when its ID, assertion scope, values, two expected outcome paths, role, and limitations make clear that it tests structure/rejection rather than a valid physical, consensus-quality, attack, model, or dataset claim.
  - [ ] Permit `admitted_domain_mock_fixture` only after Story 9.4 resolves a valid immutable `MockAdmission.v1`, exact parameter revision IDs, authentic-path unavailability evidence, bounded component/question/track/final-output linkage, and exact applicable Story 9.3 official source-use locators for every represented behavior and number. If the authentic path is reproducible or any authority is unresolved, fail closed without fallback.
  - [ ] Add a closed Story 9.5 use-policy validator that rejects fixture IDs/roots/roles for scientific dataset, label/truth, metric, ranking, uncertainty, training/calibration, or final-result uses. Regression-test it against current dataset/window consumers only; future manifests/report writers must integrate the same gate in their owning stories. Do not broadly retrofit future consumers here. Passing replay is never evidence of detector quality, dataset quality, domain fidelity, or experimental success.

- [x] Task 5: Implement explicit, read-only v1 registration, routing, replay, and drift reporting (AC: 3, 6-9)
  - [ ] Add `src/parallel_truth_fingerprint/evidence/v1_golden_fixtures.py`, reusing the prerequisite baseline resolver, semantic vocabulary, source catalog, parameter/mock gate, hashing, and canonicalization. Add no database, service, dependency, runtime hook, or competing general manifest framework.
  - [ ] Provide exactly two routes: registered fixture replay requires an exact catalog revision, fixture revision, and decoded content hash; explicit envelope replay requires a registered/versioned envelope whose own immutable identity binds the native version and payload hash. An out-of-band `v1` argument alone never authorizes arbitrary unregistered versionless bytes. Missing/unknown/unsupported versions fail before deserialization, and v1 is never inferred from shape, topic, filename, object prefix, Python type, or the embedded `artifact_version` token.
  - [ ] Keep `contract_fixture_replay` pure and offline: bounded byte loading, base64 decoding, parsing, serialization, validation, comparison, and diagnostic emission only. It must not publish MQTT, open network sockets, start CometBFT/Docker/MinIO/OPC/dashboard, mutate runtime configuration/state, load or execute a Keras model, train, capture, or write evidence.
  - [ ] Preserve current v1 quirks rather than repair them: MQTT default `json.dumps()` spacing/order/no-version behavior; Python consensus's compact sorted JSON but participant-order behavior; Go `encoding/json` output and its distinct ordering/rounding; persistence's indented JSON and internal version `2.0`; and detector records' environment-scoped nondeterminism. Any Python/Go disagreement is a declared legacy limitation, not a reason to change v1 to manufacture parity.
  - [ ] Require separately registered adapter input/output fixture identities and `V1GoldenAdapterDeclaration.v1` before any transformation. The declaration lists exact field-level mapping, order, type, input/output versions and hashes. Unknown fields, dropping, reshaping, default insertion, normalization, or conversion without that declaration fails; Story 9.5 need not create a v2 adapter merely to prove this rejection.
  - [ ] Use a closed code-owned reader/comparator registry; catalog data names allowlisted IDs and can never request a dynamic import or executable. Compare original bytes with `byte_exact`; use a closed type-strict semantic comparator only where declared.
  - [ ] Keep `expected_legacy_reader_outcome` separate from `expected_fixture_gate_outcome`: duplicate keys, invalid UTF-8, nonfinite numbers, unknown fields, and malformed payloads exercise the exact named Python/Go/native behavior when registered, while the fixture gate may independently reject present consumption as `registration_policy_rejected`. A harness rejection never counts as reproduced native behavior, and a reproduced unsafe native acceptance never counts as scientific validity.
  - [ ] Reject unexpected type changes, undeclared semantic exclusions, locale/timezone/path-separator dependence, and mutable aliases such as `latest` at the fixture-gate boundary without modifying the recorded native outcome.
  - [ ] Make replay results deterministic and side-effect-free, with stable exit/outcome tokens and sorted diagnostics. No `--update`, `--bless`, overwrite, migration, or write-back mode exists.

- [x] Task 6: Add focused shared Python/Go fixture tests and a read-only validation command (AC: 1-10)
  - [ ] Add `tests/evidence/test_v1_golden_fixtures.py` covering requirement completeness, exact pinned requirement-set identity, every origin/comparison/version and both expected-outcome paths, hash/size drift, strict carrier corruption, duplicate IDs/JSON keys, malformed bytes, secret canaries, diagnostic redaction/bounds, optional dashboard absence, and `authorization_effect: none`.
  - [ ] Reject filesystem fixture locators containing absolute/drive/UNC/device paths, ADS, backslashes, empty or dot segments, `..`, NUL, non-regular files, symlinks/junctions, or any resolved target outside the fixture root. Real symlink/junction creation tests are conditional where Windows privileges/filesystems do not allow them; an injected fake resolver exercises the same escape rule on every platform.
  - [ ] Keep opaque MinIO/object-store keys in a separate identity type and validator; never feed them to the filesystem locator resolver. A traversal-like object key may be preserved and compared without becoming a local filesystem path.
  - [ ] Add `abci/consensus_app/internal/app/v1_golden_test.go` using `runtime.Caller`-anchored repository resolution plus a deterministic explicit testdata-root fallback for `-trimpath` to consume the same bounded consensus fixtures. Test transaction decode, `evaluateRound` at fixed height, committed/query JSON, persisted-state/app-hash behavior, success/exclusion/failure paths, and declared reader/gate or Python/Go divergences without starting CometBFT or Docker.
  - [ ] Add detector tests for exact legacy feature order/schema, missing/extra/permuted/v2-only features, NaN/Infinity, wrong model/hash identity, and preserved recorded outputs. Do not train, load Keras, recalculate a threshold, or report a fixture classification as a performance metric.
  - [ ] Add fake-store persistence tests for exact opaque key/content, missing object, wrong content/hash, traversal-like object keys, and internal `artifact_version: 2.0` preservation. State explicitly that fake-store success proves adapter compatibility only.
  - [ ] Add `scripts/validate_v1_golden_fixtures.py` as a read-only offline entry point with deterministic exit codes `0=valid`, `1=fixture or expectation violation`, and `2=catalog/invocation error`; render machine JSON or concise human diagnostics without changing fixtures or runtime state.
  - [ ] Run the Story 9.1-9.4 focused suites, the Story 9.5 Python suite, `go test ./...` within `abci/consensus_app`, and full Python `unittest` discovery. Tests use temporary roots, injected resolvers/fake stores/fixed clocks, no network or service dependency, and no writes to the real reference archive, baseline, evidence store, datasets, models, results, logs, or runtime configuration.

## Dev Notes

### Scope and dependency boundaries

- This is a preservation and regression story, not a cleanup of v1 behavior. Existing serializers, readers, native version tokens, ordering, rounding, and known limitations remain observable. A cleaner representation is a separately versioned adapted fixture, never a rewrite of the original.
- Historical reader behavior and present fixture-gate policy are separate outputs. The suite may pass by proving that a known unsafe v1 acceptance is reproduced and then contained by the new gate; it must never report that containment as native v1 behavior or scientific validity.
- Stories 9.1, 9.2, 9.3, and 9.4 are hard implementation prerequisites. At planning time they are only `ready-for-dev`; Story 9.5 implementation must remain sequential and stop if their exports or tests are absent.
- Story 9.6 owns general `ArtifactManifest.v1`, evaluation envelopes, run manifests, and provenance graphs. Story 9.5 owns only its fixture-specific catalog, requirement set, router, comparators, and replay results.
- Story 9.7 owns live persistent-evidence-storage qualification. Fake/local object-store fixtures do not prove MinIO durability, immutability, versioning, or disaster recovery.
- Story 9.8 owns partition freeze and activity authorization. Story 9.5 always emits `authorization_effect: none`.
- Epic 11 later owns deterministic v2 Python/Go parity and consensus migration. Story 9.5 freezes distinct observed v1 Python and Go expectations and must not silently repair their disagreements.
- Later physical/syscall/dataset/evaluation stories own authentic acquisition, leakage-safe partitions, training, calibration, blinded evaluation, and final comparisons. FR86 coverage here is limited to fixture exclusion, preserved legacy schema/split identities where available, and explicit incompatibility checks.
- Epic 18 dashboard work is optional and presentation-only. No UI/UX asset is required by this story.

### Verified current repository behavior

- `edge_nodes/common/mqtt_io.py` builds `edges/observations/{publisher_id}` and uses default `json.dumps(payload.to_dict())`: insertion order, spaces, ASCII escaping, nonfinite floats permitted, no newline, and no version. Deserialization ignores unknown top-level fields; the passive relay bypasses byte serialization.
- Acquisition injects current UTC timestamps and the simulator is stateful/random unless controlled. Golden replay must use frozen or fixed inputs rather than runtime acquisition.
- `consensus/cometbft_client.py` sorts states, sensors, and JSON keys and emits compact UTF-8, but preserves participating-edge order, permits nonfinite floats, carries no version, and preserves the datetime lexical form produced by `isoformat()`.
- The Go ABCI structs are unversioned. `CheckTx` performs only shallow nonempty checks; unknown JSON fields are ignored; duplicate owner/round identities can become last-write-wins. Go query bytes use compact `json.Marshal`.
- Current Python and Go consensus are not identical: ordering differs, Python banker rounding and Go `math.Round` differ on half ties, and their nonfinite-number behavior differs. Golden fixtures must expose the divergence independently instead of treating either implementation as a circular oracle for the other.
- Go app-state hashing uses compact JSON over the state with `LastAppHash` excluded; disk persistence is indented and non-atomic. Story 9.5 may freeze this exact behavior but cannot claim storage qualification.
- `persist_valid_consensus_artifact()` writes `valid-consensus-artifacts/{round_id}.json`, defaults to current time, depends on source/input order, and embeds the historical native token `artifact_version: 2.0`.
- MinIO/local JSON writers use indented, insertion-ordered JSON and do not provide the canonical representation used by the new catalog. The local filesystem adapter currently has path/newline hazards; fixture loading must enforce normalized root-relative containment and not reuse that writer as a trusted fixture sink.
- Dataset, model, detector, SCADA, and dashboard contracts are mostly unversioned. NPZ/Keras bytes are unsafe to regenerate as byte-identical across ZIP/backend/platform versions. Existing legacy detector logs show varying scores and therefore support preserved recorded-output assertions only, with exact runtime limitations.
- `docs/seminario-andamento/evidence/minio/sample-valid-consensus-artifact.pretty.json` is a useful observed artifact, but the Git LF blob and current CRLF checkout differ under `core.autocrlf=true`. Base64 carriers avoid falsely treating checkout conversion as historical byte identity.
- Existing HART sample text contains comments/mojibake and one incomplete fragment. Existing ADFA-LD/LID-DS small fixture trees are test data, not official source bytes or authentic custom syscall capture.

### Scientific and academic claim limits

- Golden replay can prove exact selected byte preservation, deterministic named reader behavior, drift detection, and declared incompatibility only. It cannot prove v1 scientific correctness, compressor/plant fidelity, calibration, MQTT QoS/delivery, BFT safety/liveness, MinIO durability, detector quality, attack detection, dataset quality, external validity, or cross-dataset conclusions.
- Use `contract_fixture_replay` consistently. Do not confuse this with the project's replay/freeze attack scenario.
- A frozen expected detector classification is a fixture oracle, not a measured metric or successful detection result. SHA-256 is a byte-identity/change-detection mechanism, not evidence of source authority or semantic equivalence.
- No numeric tolerance is introduced by this story. If a later adapter/comparator needs one, it must resolve an exact Story 9.4 parameter revision and become part of the comparator/version identity.
- No mock is admitted merely because authentic behavior is difficult, slow, inconvenient, or unfavorable. New domain-bearing fixtures stay blocked until authentic-path unavailability, official source applicability, parameter authority, bounded research purpose, and final comparison linkage all resolve.
- Only frozen historical bytes receive the legacy-domain carve-out. A reconstructed domain-bearing vector must meet the same Story 9.3/9.4 admission chain as any other new domain mock; deterministic regeneration alone supplies no academic authority.

### Project structure notes

- Contracts: `src/parallel_truth_fingerprint/contracts/v1_golden_fixture.py` and intended exports in `contracts/__init__.py`.
- Validation/replay: `src/parallel_truth_fingerprint/evidence/v1_golden_fixtures.py`.
- Shared fixture authority: `testdata/golden/v1/`.
- Git byte policy: the narrowly scoped `testdata/golden/v1/** -text` addition in `.gitattributes`.
- Python tests: `tests/evidence/test_v1_golden_fixtures.py`.
- Go tests: `abci/consensus_app/internal/app/v1_golden_test.go`.
- Read-only command: `scripts/validate_v1_golden_fixtures.py`.
- Do not add a database, API, service, broker test harness, container workflow, dashboard/UI, snapshot library, JSON-schema dependency, model runner, dataset writer, scientific evaluator, or general manifest framework.

### Technical research notes

- RFC 4648 defines the standard Base64 alphabet, padding, canonical encoding considerations, and default rejection of non-alphabet characters. Story 9.5 narrows this further to one unwrapped, whitespace-free carrier representation so decoded historical-byte identity is unambiguous.
- RFC 8785 explains why hashable JSON requires invariant serialization and stronger constraints than merely sorting keys. The Story 9.5 catalog uses the project's bounded schema encoder and does not claim full JCS conformance or alter historical bytes.
- Python's official `json` documentation confirms that `sort_keys` can support regression comparisons, while `allow_nan=True` is the default and produces non-standard JSON tokens. The new catalog encoder rejects nonfinite values, but v1 historical behavior remains preserved as data and limitation.
- Go's official `encoding/json` documentation states that map keys are sorted during `Marshal`; this helps explain observed query/state bytes but does not establish Python/Go semantic parity.
- No new domain-number source is created by this story. Any domain-bearing admitted mock resolves already-qualified Story 9.3 source-use and Story 9.4 parameter/mock identities; otherwise it remains blocked.

### Testing standards

- Use standard-library Python `unittest` and Go `testing`, table-driven/subtest cases, temporary directories, deterministic clocks, fixed runtime inputs, injected resolvers, and fake stores. No new Python or Go dependency is required.
- Assert structured rule IDs, identities, field paths, and exact expected/observed values rather than only prose messages.
- Test byte and semantic modes independently. The expected oracle must be committed/reviewed before the test run and must not be produced by the same code path under assertion.
- Exercise locale/timezone/path/newline/order/hash changes and prove replay performs no write, network, runtime, model, dataset, or evidence mutation.
- Run full discovery because prerequisite public exports and the shared `evidence` package can affect existing imports even without runtime integration.

## BMAD Party Mode Review

- Initial aggregate score: 8.62/10 - vetoed. The review found that universal harness rejection would have rewritten actual v1 reader behavior, reconstructed domain-bearing fixtures could bypass the mock gate, one owner-excerpt origin expanded scope, and repository identity/path/append-only details were incomplete.
- Final architecture and product-scope score: 9.55/10 - no veto.
- Final academic-evidence and scientific-integrity score: 9.8/10 - no veto.
- Final QA and developer-readiness score: 9.6/10 - no veto.
- Aggregate final score: 9.65/10.
- Auto-approval rule: score at least 9.0 with no veto.
- Decision: auto-approved as `ready-for-dev` after the reader-versus-gate split, reconstructed-domain guardrail, scope reduction, immutable identity preimages, content-addressed layout, independent inventory pinning, canonical carrier/Git policy, path/object-key separation, and bounded use-policy enforcement were corrected and re-scored.
- Boundary: this decision approves the planning artifact only; `authorization_effect` remains `none`.

### References

- [Source: _bmad-output/planning-artifacts/epics.md#Story 9.5: Preserve v1 Contracts as Golden Versioned Fixtures]
- [Source: _bmad-output/planning-artifacts/epics.md#Cross-Epic Mock Admission Guardrail]
- [Source: _bmad-output/planning-artifacts/prd.md#FR28]
- [Source: _bmad-output/planning-artifacts/prd.md#FR30]
- [Source: _bmad-output/planning-artifacts/prd.md#FR32]
- [Source: _bmad-output/planning-artifacts/prd.md#FR86]
- [Source: _bmad-output/planning-artifacts/prd.md#NFR22-NFR23]
- [Source: _bmad-output/planning-artifacts/prd.md#NFR35]
- [Source: _bmad-output/planning-artifacts/prd.md#NFR40-NFR41]
- [Source: _bmad-output/planning-artifacts/prd.md#NFR48-NFR52]
- [Source: _bmad-output/planning-artifacts/architecture.md#Controlling V2 Architecture Consolidation - 2026-08-22]
- [Source: _bmad-output/planning-artifacts/architecture.md#Authoritative evidence contracts]
- [Source: _bmad-output/implementation-artifacts/9-1-freeze-and-index-the-v1-evidence-baseline.md]
- [Source: _bmad-output/implementation-artifacts/9-2-establish-the-semantic-and-evidence-role-vocabulary.md]
- [Source: _bmad-output/implementation-artifacts/9-3-build-the-authoritative-source-evidence-catalog.md]
- [Source: _bmad-output/implementation-artifacts/9-4-build-the-parameter-evidence-catalog-and-validation-gate.md]
- [Source: src/parallel_truth_fingerprint/edge_nodes/common/mqtt_io.py]
- [Source: src/parallel_truth_fingerprint/consensus/cometbft_client.py]
- [Source: src/parallel_truth_fingerprint/consensus/cometbft_mapper.py]
- [Source: abci/consensus_app/internal/app/types.go]
- [Source: abci/consensus_app/internal/app/app.go]
- [Source: src/parallel_truth_fingerprint/persistence/artifact_store.py]
- [Source: src/parallel_truth_fingerprint/persistence/local_filesystem.py]
- [Source: src/parallel_truth_fingerprint/persistence/service.py]
- [Source: src/parallel_truth_fingerprint/lstm_service/dataset_artifacts.py]
- [Source: src/parallel_truth_fingerprint/lstm_service/inference.py]
- [Source: src/parallel_truth_fingerprint/lstm_service/replay_behavior.py]
- [Source: docs/seminario-andamento/evidence/minio/sample-valid-consensus-artifact.pretty.json]
- [RFC 8785: JSON Canonicalization Scheme](https://www.rfc-editor.org/rfc/rfc8785.html)
- [RFC 4648: Base-N Encodings](https://www.rfc-editor.org/rfc/rfc4648.html)
- [Python 3.14 `json`](https://docs.python.org/3.14/library/json.html)
- [Go `encoding/json`](https://pkg.go.dev/encoding/json)

## Mandatory Academic Evidence Amendment

Before implementation, apply the relevant mandatory controls in [Academic Evidence Admission Amendment — 2026-08-31](../planning-artifacts/academic-evidence-admission-amendment-2026-08-31.md). This story must fail closed on an unresolved evidence origin, numeric authority, required mock closure, or prohibited dataset substitution. The amendment adds no activity authorization.
## Dev Agent Record

### Agent Model Used

GPT-5.6 Codex

### Debug Log References

- `PYTHONPATH=src .\\venv\\Scripts\\python.exe -m unittest tests.evidence.test_v1_golden_fixtures tests.lstm_service.test_dataset_builder -q` — 21 tests passed.
- `go test ./...` from `abci/consensus_app` — passed using the repository's portable Go toolchain.
- `PYTHONPATH=src .\\venv\\Scripts\\python.exe -m unittest discover -s tests -t . -q` — passed.

### Completion Notes List

- Implemented the code-owned requirement set, immutable identity-addressed corpus, strict carrier/loading boundaries, closed route/reader/comparator registries, deterministic replay diagnostics, and read-only validator.
- Resolved review follow-ups for structural catalog validation before replay, explicit-envelope identity binding, bounded raw loading, dataset-root exclusion, named reader routing, comparator drift detection, and Go fixture integrity/status coverage.
- The catalog intentionally remains `unverifiable` for baseline provenance: Story 9.1 records that no historical baseline was published. This is a stable blocked-evidence result, not a passing scientific claim or fabricated baseline.

### File List

- `src/parallel_truth_fingerprint/contracts/v1_golden_fixture.py`
- `src/parallel_truth_fingerprint/contracts/__init__.py`
- `src/parallel_truth_fingerprint/evidence/v1_golden_fixtures.py`
- `src/parallel_truth_fingerprint/lstm_service/dataset_builder.py`
- `tests/evidence/test_v1_golden_fixtures.py`
- `tests/lstm_service/test_dataset_builder.py`
- `abci/consensus_app/internal/app/v1_golden_test.go`
- `scripts/validate_v1_golden_fixtures.py`
- `testdata/golden/v1/`
- `.gitattributes`
