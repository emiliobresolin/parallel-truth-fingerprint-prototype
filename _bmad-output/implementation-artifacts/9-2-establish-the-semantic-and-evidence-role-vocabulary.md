# Story 9.2: Establish the Semantic and Evidence-Role Vocabulary

Status: done

## Story

As a research owner,
I want one versioned vocabulary for modalities, representations, models, evidence roles, result roles, and scientific status,
so that contracts and reports cannot make incompatible or overstated claims.

## Acceptance Criteria

1. **Two modalities and correct kinds.** Given the controlling August requirements, when `SemanticVocabulary.v1` is defined, then the only detection modalities are `physical_instrumentation` and `linux_host_syscall`; 4-20 mA is a physical representation rather than a modality; and LSTM, GRU, autoencoder, and baseline are model-family tags rather than datasets, modalities, representations, or evidence sources.
2. **Orthogonal evidence identity.** Given a dataset, run, artifact, or reported result, when its semantic identity is created, then it records an explicit evidence role and result role that can distinguish custom-generated, official-real, test-fixture, published-reference, runtime, legacy, and locally measured material as applicable; and the general roles cannot erase or replace dataset family/version, dataset-native scope and file role, subset, modality, synthetic/mock lineage, scientific status, provenance references, or limitations.
3. **No role promotion.** Given fixture or published-reference material, when a writer assigns it a locally measured result role, then validation rejects the exact incompatible combination with a stable rule ID and actionable explanation; and the metric or artifact is not serialized or published into a measured-result namespace.
4. **Cross-domain claims fail closed.** Given a writer or report record describes HAI as compressor data, ADFA-LD or LID-DS as physical evidence, controlled custom evidence as official-real or real-plant evidence, an autoencoder/model as a dataset, or an external benchmark model as a compressor detector, when semantic validation runs, then the record is rejected with the specific violated rule and fields; and it is not presented as complete evidence.
5. **Historical labels remain immutable.** Given a frozen Story 9.1 entry uses legacy or incomplete terminology, when it receives a current interpretation, then the original entry bytes, labels, hash, and identity remain unchanged; and the interpretation is stored in a separate `LegacySemanticMapping.v1` record containing vocabulary version, baseline ID, entry ID, original field/value, current semantic assignment, provenance references, limitation, and forced `legacy` scientific status.
6. **Unknown semantics are never guessed.** Given a contract, evaluator, report, or optional presentation consumer receives an unknown, missing, or incompatible vocabulary version or token, when it resolves the semantic identity, then scientific writers and evaluators fail explicitly while presentation-only consumers may expose the original value as `unsupported`; and no consumer substitutes a default modality, representation, model family, evidence role, result role, scientific status, dataset scope, or synthetic status.
7. **Deterministic validation without authorization.** Given the semantic validator test suite, when valid and invalid combinations are exercised, then it covers both modalities, linked physical and categorical-syscall representations, multi-tag model families, dataset-native fields, fixture/reference/measured distinctions, mock lineage, legacy mappings, and every prohibited cross-domain claim; and passing validation changes no runtime or evidence state and authorizes no implementation activity, acquisition, training, capture, experiment, promotion, publication, feature activation, or dashboard work.

## Tasks / Subtasks

- [x] Task 1: Define the minimal versioned semantic contract (AC: 1, 2, 6)
  - [x] Add `src/parallel_truth_fingerprint/contracts/semantic_vocabulary.py` with `SEMANTIC_VOCABULARY_VERSION = "semantic-vocabulary.v1"`, explicit `StrEnum` values, frozen dataclasses, and deterministic `to_dict()` output. Re-export the public types from `contracts/__init__.py` without changing existing imports.
  - [x] Pin these Story 9.2 axes and tokens; additions or changed meanings require a new vocabulary version rather than mutation:
    - `DetectionModality`: `physical_instrumentation`, `linux_host_syscall`.
    - `RepresentationKind`: `raw_current_ma`, `normalized_span`, `engineering_value`, `categorical_syscall_event`.
    - `ModelFamily`: `lstm`, `gru`, `autoencoder`, `baseline`; store a sorted unique tuple so `lstm` + `autoencoder` and `gru` + `autoencoder` are valid combinations.
    - `EvidenceRole`: `custom_generated`, `official_real`, `fixture_test`, `published_reference`, `runtime_evidence`, `legacy_v1`.
    - `ResultRole`: `none`, `locally_measured`, `published_reference`, `fixture_expected`, `legacy_recorded`.
    - `ScientificStatus`: `qualified`, `unqualified`, `blocked`, `unsupported`, `test_only`, `reference_only`, `legacy`.
    - `SyntheticStatus`: `authentic`, `mock`, `mock_derived`, `not_applicable`.
    - `EntityKind`: `source`, `dataset`, `run`, `artifact`, `representation`, `model`, `detector_bundle`, `score`, `evaluation_result`, `fixture`, `legacy_mapping`.
    - `DatasetFamily`: `adfa_ld`, `lid_ds_2021`, `hai_23_05`, `ptfp_custom_v1` when a governed dataset is applicable.
    - `DomainScope`: `compressor_prototype`, `native_adfa_ld`, `native_lid_ds_2021`, `native_hai_23_05`, `ptfp_custom_controlled`, `real_plant`, `not_applicable`.
  - [x] Define a machine-readable frozen `SemanticVocabularyDefinition` that exports the version and exact axis/token tables, plus one flat `SemanticIdentity` carrying vocabulary version, stable identity, entity kind, zero-to-two sorted unique modalities, representations/model-family tags as applicable, evidence role, result role, scientific status, synthetic status, dataset family/version/native scope/native role/subset, bounded domain scope, provenance and qualification references, detector-bundle reference when applicable, and limitations.
  - [x] Require explicit not-applicable handling rather than placeholder guesses. Modality-bearing datasets/runs/results require at least one modality; a two-modality identity denotes aligned physical/syscall support or fusion and never creates a third `fusion` modality.

- [x] Task 2: Implement deterministic semantic validation with stable diagnostics (AC: 1-4, 6)
  - [x] Add `src/parallel_truth_fingerprint/evidence/semantic_validation.py`, reusing the `evidence` package created by Story 9.1. If Story 9.1 is not implemented yet, do not duplicate its planned package or canonicalization logic; respect the implementation dependency stated below.
  - [x] Return a frozen `SemanticValidationResult` containing `supported`, `valid`, and an ordered tuple of structured violations. Each violation contains a stable rule ID, affected fields, offending tokens, and a concise explanation; callers must not parse free-text messages to determine policy.
  - [x] Implement at least these stable rules: `SEM-VERSION-MISSING`, `SEM-VERSION-UNSUPPORTED`, `SEM-TOKEN-UNKNOWN`, `SEM-MODALITY-REQUIRED`, `SEM-REPRESENTATION-CROSS-MODALITY`, `SEM-MODEL-AS-DATASET`, `SEM-MODEL-ONLY-AS-DETECTOR`, `SEM-FIXTURE-AS-MEASURED`, `SEM-REFERENCE-AS-MEASURED`, `SEM-OFFICIAL-REAL-WITHOUT-SOURCE-QUALIFICATION`, `SEM-QUALIFIED-WITHOUT-GATE-REFERENCE`, `SEM-HAI-AS-COMPRESSOR`, `SEM-ADFA-AS-PHYSICAL`, `SEM-LID-AS-PHYSICAL`, `SEM-CUSTOM-AS-OFFICIAL-OR-REAL-PLANT`, `SEM-CUSTOM-PHYSICAL-NOT-MOCK-DERIVED`, `SEM-SYSCALL-SYNTHETIC`, `SEM-EXTERNAL-MODEL-AS-COMPRESSOR-DETECTOR`, `SEM-DATASET-NATIVE-SCOPE-MISSING`, and `SEM-LEGACY-MAPPING-INCOMPLETE`.
  - [x] Validate explicit semantic fields only. Do not add heuristic/NLP scanning of arbitrary prose, rewrite Markdown, infer dataset identity from a directory name, or normalize an unknown token by spelling similarity.
  - [x] Sort violations deterministically by rule ID and field path. Repeated validation of the same identity must produce equal structured output.

- [x] Task 3: Preserve evidence, result, qualification, and mock lineage as separate facts (AC: 2-4, 7)
  - [x] Enforce fixture/reference incompatibilities without treating `official_real` as synonymous with “real plant.” `official_real` means qualified owner-origin dataset evidence within its native scope; Story 9.3 still owns source qualification.
  - [x] Require an immutable source-qualification reference for `official_real` and an owning-gate reference for `qualified`. Story 9.2 validates presence and semantic compatibility only; it neither creates nor approves those references.
  - [x] Keep `locally_measured` independent from qualification and synthetic lineage. A local metric may remain `unqualified`, `blocked`, or `mock_derived`; semantic validation never promotes it to `qualified`.
  - [x] Treat `mock`/`mock_derived` as lineage, not a result role. A custom physical run may be `custom_generated` + `locally_measured` + `mock_derived`; an authentic custom syscall capture may be `custom_generated` + `locally_measured` + `authentic`.
  - [x] Require a `MockAdmission.v1` provenance reference before accepting `mock` or `mock_derived` for domain evidence. This semantic check does not approve the mock, its behavior, or any number; Story 9.4 owns full parameter/mock admission validation.
  - [x] Preserve dataset-native semantics: ADFA-LD and LID-DS 2021 remain external categorical syscall evidence; HAI 23.05 remains external native physical/SCADA evidence and not compressor data; only `PTFP-Custom-v1` may carry aligned custom physical and syscall modalities.
  - [x] Under the current approved prototype boundary, custom physical observations require `mock`/`mock_derived` plus the exact admission reference, while formal syscall evidence requires `authentic`; fabricated, modified, or synthetic syscalls fail even if labelled custom-generated.
  - [x] Keep “baseline” meanings distinct: evidence baseline, baseline model-family tag, and `LEGACY_BASELINE` are never interchangeable.

- [x] Task 4: Define the historical interpretation mapping without rewriting v1 (AC: 5, 6)
  - [x] Add frozen `LegacySemanticMapping` and deterministic serialization in the semantic contract. It must reference exact Story 9.1 `baseline_id` and entry ID rather than a mutable path or copied payload.
  - [x] Force mapping `scientific_status` to `legacy`; require vocabulary version, original field/value, provenance reference, and at least one explicit limitation; reject mappings that claim to mutate, replace, qualify, or relabel the source entry.
  - [x] Provide explicit mappings for Story 9.1's minimal labels (`IMPLEMENTED_RUNTIME_EVIDENCE`, `FIXTURE`, `PUBLISHED_REFERENCE`, `MEASURED_RESULT`, `EXPERIMENTAL_FINGERPRINT_BASELINE`, `LEGACY_BASELINE`) without assuming `MEASURED_RESULT` means qualified or real-plant.
  - [x] Map historical logical `sensor` labels to their preserved logical channel plus known source context; never claim physical hardware when the source was the v1 simulator/signal emulator.
  - [x] Do not retrofit, edit, or execute legacy ADFA/LID adapters, historical reports, stored JSON, dashboard state, or training history in this story.

- [x] Task 5: Specify strict and presentation-only consumer behavior (AC: 3, 4, 6)
  - [x] Provide one parser/resolver that preserves the raw unknown version/token in its diagnostic. Unknown or missing semantics must never construct a valid enum through fallback or `Enum._missing_()` coercion.
  - [x] Scientific contracts, validators, evaluators, persistence writers, and report publishers require `supported=True` and `valid=True` before writing. Invalid identities produce no measured/complete output.
  - [x] Return a separate `UnsupportedSemanticIdentity` containing the untouched raw version/payload and violations when parsing cannot construct a supported identity. A presentation-only caller may render that object as unsupported, but may not turn it into `SemanticIdentity`, persist a corrected identity, infer a default, or affect scientific/control state. This creates no Epic 18 UI requirement.
  - [x] Keep operational outcomes (`normal`, `anomalous`, consensus status, SCADA divergence, run success/failure) separate from scientific status, evidence role, result role, scenario truth, fault, and attack labels.

- [x] Task 6: Publish a concise human-readable vocabulary reference (AC: 1-6)
  - [x] Add `docs/semantic-vocabulary-v1.md` as the human-readable companion to the code contract: exact tokens, definitions, valid examples, prohibited combinations/rule IDs, legacy mapping behavior, source contexts, and version-change policy.
  - [x] Define `sensor` in the physical-instrument context and call software-generated physical channels `signal_emulator` or simulated/logical channels. A `sensor_id` alone never proves hardware.
  - [x] State explicitly that scenario, fault, attack, anomaly, incident, SCADA divergence, and suspected Byzantine behavior are not synonyms: scenario/fault/attack belong to declared truth/context, while anomaly is a detector/policy deviation outcome and does not establish cause before authorized truth join.
  - [x] Ensure documentation says a model is not a detector: a detector requires the compatible model plus schema/vocabulary, preprocessing, calibration, frozen threshold/decision policy, runtime identity, and bundle compatibility owned by later stories.

- [x] Task 7: Add table-driven semantic tests and regression checks (AC: 1-7)
  - [x] Add `tests/evidence/test_semantic_vocabulary.py` using standard-library `unittest`; reuse `tests/evidence/__init__.py` from Story 9.1 and use no network, Docker, MinIO, runtime service, training, capture, experiment, or dashboard fixture.
  - [x] Test every enum token, version, deterministic `to_dict()`, unique/sorted modalities and model tags, representation/modality compatibility, dataset-native field retention, and the full structured rule-ID matrix.
  - [x] Test valid examples: official ADFA-LD plus local evaluation; custom mock-derived physical measurement; authentic custom syscall measurement; author-published metric; test fixture; combined `lstm` + `autoencoder`; and aligned two-modality custom evidence without a `fusion` modality token.
  - [x] Test every AC 3/4 prohibition, unqualified `official_real`/`qualified` claims without the required references, synthetic custom evidence presented as official-real/real-plant, a model artifact presented as a complete detector, fabricated/replayed syscalls presented as formal evidence, unknown/missing/incompatible versions/tokens, and failure to retain dataset-native role/subset/limitations.
  - [x] Test legacy mappings against a small frozen Story 9.1 fixture: source bytes/hash remain unchanged, mapping identity is deterministic, `legacy` is forced, provenance/limitation is required, and unknown source entries fail closed.
  - [x] Prove the human-readable token tables contain every code token and stable rule ID, so code and documentation cannot drift silently.
  - [x] Run `.\.venv\Scripts\python.exe -m unittest tests.evidence.test_semantic_vocabulary` followed by `.\.venv\Scripts\python.exe -m unittest discover -s tests`; preserve the dirty worktree and do not alter unrelated files to make tests pass.

- [x] Task 8: Resolve focused code-review findings (AC: 2-7)
  - [x] [AI-Review][High] Require every semantic axis and formal-path flag explicitly; add minimal immutable numeric-authority references for numeric representations, scores, and evaluation results while leaving full authority validation to Story 9.4.
  - [x] [AI-Review][High] Bind each legacy label to its exact allowed interpretation, validate complete baseline hashes, and reject duplicate or promotional assignments.
  - [x] [AI-Review][High] Require authentic syscall provenance on formal syscall support, including aligned two-modality evidence, while preserving isolated non-domain fixture behavior.
  - [x] [AI-Review][High] Enforce native modality, scope, origin, role, and qualification compatibility for ADFA-LD, LID-DS 2021, and HAI 23.05 without a caller-controlled bypass.
  - [x] [AI-Review][High] Return unsupported diagnostics for semantically invalid parsed payloads and provide a fail-closed scientific serialization gate.
  - [x] [AI-Review][Medium] Force fixtures to non-domain/test-only semantics and reject mock-generation lineage on authentic captures.
  - [x] [AI-Review][Medium] Reject blank identities/references and malformed parser collection/boolean types deterministically.
  - [x] [AI-Review][Medium] Reject incomplete detector bundles rather than accepting a missing model or bundle reference.
  - [x] [AI-Review][Medium] Exercise every anti-promotion rule and verify exact documentation table membership rather than substring presence.

- [x] Task 9: Resolve final focused code-review findings (AC: 2-7)
  - [x] [AI-Review][High] Close custom/domain identity to the PTFP custom dataset family and controlled scope.
  - [x] [AI-Review][High] Validate governed external dataset metadata, family/version compatibility, and explicit limitations.
  - [x] [AI-Review][High] Close evidence-role, result-role, scientific-status, origin, and synthetic-lineage promotion combinations.
  - [x] [AI-Review][High] Bind legacy mappings to the exact frozen Story 9.1 baseline entry and require the exact sensor mapping key set.
  - [x] [AI-Review][Medium] Make semantic parsing fail closed on unknown fields, malformed collection members, and invalid mock-influence values.
  - [x] [AI-Review][Medium] Validate direct contract boolean and collection member types deterministically.
  - [x] [AI-Review][High] Require the exact current mock admission and unique mock-influence field paths.
  - [x] [AI-Review][High] Reject mutable identifiers and require minimally structured immutable numeric-authority references.

## Dev Notes

### Scope and dependency boundary

- This story implements FR31, FR32, FR65's shared semantic portion, and FR72. It defines meaning and validates explicit semantic assignments; it does not build the source catalog, parameter gate, golden fixture corpus, general manifests, storage qualification, authorization records, dataset adapters, evaluations, reports, or UI.
- Story 9.1 is an implementation dependency for real legacy mappings. Implement and verify its frozen baseline contract first; Story 9.2 may use small isolated fixtures while developing its own contract but must not duplicate or absorb Story 9.1.
- Stories 9.3 and 9.4 own source authority and parameter/mock-admission completeness. Story 9.5 owns golden bytes/replay, Story 9.6 owns `ArtifactManifest.v1` and `EvaluationResult.v1`, and Story 9.8 owns activity authorization.
- `ready-for-dev` authorizes only this bounded implementation. It grants no dataset acquisition, training, capture, experiment, promotion, scientific publication, activation, or dashboard work.
- UI/UX is optional and out of scope. The only presentation behavior defined here is the safe semantic contract: unsupported stays visible and never becomes a guessed value.

### Semantic meanings and non-conflation rules

- **Sensor vs emulator:** NIST's OT-context definition treats a sensor as a device whose voltage/current represents a measured physical property. The software-only custom physical source is an admitted signal emulator, not physical hardware, compressor measurement, or digital twin.
- **Scenario/fault/attack/anomaly:** a scenario is a preregistered condition/schedule; a fault is a declared non-adversarial or cause-unspecified failure condition; an attack requires malicious/unauthorized truth; an anomaly is deviation from a frozen expected profile. A detector anomaly never proves attack or fault by itself.
- **Dataset/model/detector:** a dataset is a versioned observation collection with provenance/native roles/partitions/limitations; a model is a learned or declared computational family/parameterization; a detector is a frozen compatible inference bundle. These entity kinds are not interchangeable.
- **Runtime/fixture/reference/measurement:** runtime evidence proves implemented execution only; a fixture proves a test boundary; a published reference reports an external claim; a locally measured result comes from this project's identified execution. None automatically means qualified, favorable, final, or real-plant.
- **Mock lineage:** non-domain sentinel fixtures are test-only and not scientific mocks. Domain behavior/values require the cross-epic mock guardrail. Every downstream artifact remains `mock_derived` even when the project computes its metric locally.
- Official/glossary definitions are context-specific source material for this project contract, not claims of one universal terminology across every discipline.

### Required valid and invalid examples

- Valid: ADFA-LD identity = `linux_host_syscall` + `official_real` + native ADFA-LD scope; a local evaluation may add `locally_measured` without becoming physical or compressor evidence.
- Valid: HAI 23.05 identity = `physical_instrumentation` + `official_real` + native HAI scope; it remains external physical/SCADA evidence, not compressor data and not wholesale 4-20 mA data.
- Valid: controlled PTFP custom physical identity = `physical_instrumentation` + `custom_generated` + `mock`/`mock_derived` with the exact admission reference; its local result may be `locally_measured` but never real-plant or official-real.
- Valid: custom Linux capture = `linux_host_syscall` + `custom_generated` + `authentic`; a replayed fixture is `fixture_test`/`fixture_expected` and cannot enter formal evidence.
- Invalid: `fusion` as a third modality. Fusion is an evaluation/result kind referencing both allowed modalities on aligned custom support.
- Invalid: `runtime_valid_only`, `normal`, `anomalous`, `failed_consensus`, or SCADA divergence used as evidence role, result role, or scientific qualification.

### Existing repository intelligence

- Reuse frozen dataclass, `StrEnum`, `__post_init__()` invariant, and deterministic `to_dict()` patterns in `contracts/consensus_status.py`, `consensus_alert.py`, `consensus_result.py`, and `scada_comparison_output.py`.
- Do not reuse the current benchmark/model registries' silent duplicate overwrite behavior. Vocabulary token/version registration is closed and explicit; duplicate or unknown values fail.
- Existing semantic fields are mostly free-form strings: dataset adequacy level/labels, model type, training dataset/model names, dataset provenance, scenario label, and fault mode. Story 9.2 adds the shared contract but does not migrate every legacy writer.
- Historical ADFA/LID adapters scale syscall IDs as continuous floats, infer version from directory names, and lose some native roles; the old comparative report can select macro-F1 “champions.” Preserve these as legacy limitations/mappings. Do not silently make them August-compliant or repair them here.
- The v1 `lstm_autoencoder` string maps to both `lstm` and `autoencoder`, with `legacy` status; it is never a dataset or final physical detector.
- Preserve all current user changes. Never reset, clean, rewrite, or commit the dirty worktree as part of story implementation.

### Technical implementation guidance

- Use Python `StrEnum` with explicit string values; do not use `auto()` because serialized tokens are a versioned public contract. Convert enum values explicitly in `to_dict()` where exact `str` objects are required.
- `@dataclass(frozen=True)` emulates read-only instances but does not make nested mutable values safe. Store tuples/frozen values and copy mappings into deterministic immutable representations at construction.
- Keep parsing bounded: reject oversized/untrusted semantic payloads before generic JSON decoding where a file/network boundary is later introduced. This story itself needs no new parser service or dependency.
- Use stable JSON-compatible dictionaries/lists only. Deterministic `to_dict()` ordering supports regression; Story 9.6 remains the owner of general canonical manifest hashing.
- No dependency upgrade is required. Use the repository's Python `>=3.14` and standard library only.

### Testing standards

- Use `unittest` and table-driven `subTest()` cases. Assert structured rule IDs and field paths, not only message prose.
- Tests must be deterministic and independent of the current clock, worktree state, external datasets, network, Docker, Go, MinIO, runtime services, and optional dashboard.
- The full suite is required because exporting new contracts and adding the shared `evidence` package can affect imports even when runtime behavior should remain unchanged.

### Project Structure Notes

- New contract: `src/parallel_truth_fingerprint/contracts/semantic_vocabulary.py`.
- New validator: `src/parallel_truth_fingerprint/evidence/semantic_validation.py`; reuse Story 9.1's package boundary.
- Public exports: `src/parallel_truth_fingerprint/contracts/__init__.py` only where the project already exports contract types.
- Human-readable contract: `docs/semantic-vocabulary-v1.md`.
- Tests: `tests/evidence/test_semantic_vocabulary.py`; reuse the Story 9.1 test package.
- Do not create a database, registry service, API route, workflow engine, dashboard component, generic report migration, or generated evidence package in this story.

### Technical Research Notes

- Python 3.14's official `StrEnum` documentation confirms that members are strings usable in most string contexts, while noting that exact-`str` checks may require `str(member)`. Explicit values are preferable here because token spelling is part of the vocabulary version.
- Python's official dataclass documentation states that `frozen=True` emulates immutability rather than creating truly immutable objects; nested values therefore remain tuples/frozen structures by contract.
- Python's official JSON documentation provides deterministic key ordering and compact separators, but the story only needs stable contract serialization; it does not claim RFC 8785 canonicalization or own manifest hashing.
- NIST provides multiple context-dependent definitions and directs readers back to the named source context. The project definitions preserve that limitation instead of claiming universal terminology.

### References

- [Source: _bmad-output/planning-artifacts/epics.md#Cross-Epic Mock Admission Guardrail]
- [Source: _bmad-output/planning-artifacts/epics.md#Epic 9: Reproduce and Trust the Existing Prototype]
- [Source: _bmad-output/planning-artifacts/epics.md#Story 9.2: Establish the Semantic and Evidence-Role Vocabulary]
- [Source: _bmad-output/planning-artifacts/prd.md#Controlling Consolidated Requirements Inventory — FR31, FR32, FR65, FR72]
- [Source: _bmad-output/planning-artifacts/prd.md#NonFunctional Requirements — NFR30, NFR37-NFR40, NFR48, NFR50-NFR52]
- [Source: _bmad-output/planning-artifacts/architecture.md#Controlling V2 Architecture Consolidation - 2026-08-22]
- [Source: _bmad-output/planning-artifacts/architecture.md#Authoritative evidence contracts]
- [Source: _bmad-output/planning-artifacts/architecture.md#Bounded physical signal emulator admission]
- [Source: _bmad-output/planning-artifacts/architecture.md#Authentic Linux workload and syscall boundary]
- [Source: _bmad-output/planning-artifacts/architecture.md#Data, fusion, and final comparison boundary]
- [Source: _bmad-output/planning-artifacts/ux-design-specification.md#Controlling Optional-Mode Boundary]
- [Source: _bmad-output/implementation-artifacts/9-1-freeze-and-index-the-v1-evidence-baseline.md]
- [Source: docs/reference-archive/README.md#Authority and storage policy]
- [Source: docs/reference-archive/catalog/index.md]
- [Source: docs/reference-archive/catalog/mock-admission-ptfp-signal-emulator-v1.yaml]
- [Source: src/parallel_truth_fingerprint/contracts/consensus_status.py]
- [Source: src/parallel_truth_fingerprint/contracts/scada_comparison_output.py]
- [Source: src/parallel_truth_fingerprint/contracts/dataset_artifact.py]
- [Source: src/parallel_truth_fingerprint/contracts/fingerprint_model.py]
- [Source: src/parallel_truth_fingerprint/lstm_service/offline_training/benchmarks/base.py]
- [Source: src/parallel_truth_fingerprint/lstm_service/offline_training/registry/training_history.py]
- [Python `enum` and `StrEnum`](https://docs.python.org/3/library/enum.html)
- [Python `dataclasses`](https://docs.python.org/3/library/dataclasses.html)
- [Python `json`](https://docs.python.org/3/library/json.html)
- [NIST sensor glossary](https://csrc.nist.gov/glossary/term/sensor)
- [NIST attack glossary](https://csrc.nist.gov/glossary/term/attack)
- [NIST anomaly glossary](https://csrc.nist.gov/glossary/term/anomaly)
- [NIST SP 800-94](https://nvlpubs.nist.gov/nistpubs/Legacy/SP/nistspecialpublication800-94.pdf)

## Amendment Acceptance Criteria: Evidence Origin

**Given** a domain-bearing artifact, event, result, or claim
**When** semantic-role validation runs
**Then** it requires exactly one closed `EvidenceOrigin` token: `official_native`, `authentic_capture`, `prototype_generated`, `mock_parameterized`, `measured`, or `test_fixture`
**And** `SyntheticStatus` remains orthogonal lineage rather than a substitute for evidence origin.

**Given** a `mock_parameterized` artifact
**When** its provenance is validated
**Then** it also requires `generation_origin=prototype_generated` and a per-field/derivation mock-influence map resolving every affected value to the exact parameter and admission closure
**And** an official-native custom/fixture record, authentic capture without its required boundary provenance, test fixture in a formal path, or mock-parameterized record without prototype generation fails with stable semantic rule IDs.

- [x] Add a closed `EvidenceOrigin` enum and pure semantic validator with stable missing, unknown, incompatible, official-native-scope, authentic-capture-provenance, and test-fixture-formal-path failures. Keep it versioned and free of activity authorization.
- [x] Add `unittest` cases for all six origins, mixed direct/mock field lineage, missing/unknown origin, prohibited origin pairing, and origin promotion. Fixtures remain non-domain and test-only.

## Mandatory Academic Evidence Amendment

Before implementation, apply the relevant mandatory controls in [Academic Evidence Admission Amendment — 2026-08-31](../planning-artifacts/academic-evidence-admission-amendment-2026-08-31.md). This story must fail closed on an unresolved evidence origin, numeric authority, required mock closure, or prohibited dataset substitution. The amendment adds no activity authorization.
## Dev Agent Record

### Agent Model Used

GPT-5 Codex

### Implementation Plan

- Define the closed immutable vocabulary and flat semantic identity contract.
- Implement pure deterministic validation and strict unsupported parsing.
- Preserve origin, evidence/result role, qualification, synthetic lineage, and v1 interpretation as orthogonal facts.
- Publish the human-readable reference and prove code/document synchronization with table-driven tests.

### Debug Log References

- RED: focused test import failed because `semantic_vocabulary` did not exist.
- GREEN: 20 focused Story 9.2 tests passed.
- Regression: 87 evidence tests passed with 3 environment-dependent symlink skips.
- Safe regression: 97 tests passed with 3 skips; the selected suite excludes training, network, Docker, MinIO, capture, experiment, and dashboard activity.
- `compileall` and `git diff --check` passed; only existing Windows CRLF conversion warnings were reported.
- Final focused RED phase reproduced 14 invalid acceptances plus malformed-input errors before the eight review patches.
- Final GREEN/regression phase passed 41 focused semantic tests, 108 evidence tests, and 118 safe regression tests with 3 environment-dependent symlink skips.

### Completion Notes List

- Added the exact v1 semantic axes, deterministic immutable serialization, sorted multi-tags, and explicit unsupported semantics.
- Added 33 stable structured diagnostic rule IDs covering role promotion, cross-domain claims, dataset-native retention, qualification references, numeric authority, origin compatibility, mock influence, and authentic capture provenance.
- Added separate immutable legacy mappings for Story 9.1 labels, the historical `lstm_autoencoder` tag, and logical sensor context without rewriting frozen v1 evidence.
- Added the mandatory closed EvidenceOrigin model and per-field mock influence binding without introducing activity authorization or infrastructure.
- Published the synchronized human-readable vocabulary and validated every code token and stable rule ID appears in it.
- The requested full repository discovery was intentionally replaced by the previously approved safe non-training regression boundary; no training or external activity was triggered.
- Resolved 9 focused code-review findings: semantic defaults removed, numeric authority minimally referenced, legacy promotion blocked, mixed-modality syscall provenance retained, external dataset substitution closed, invalid parsing/writing failed closed, fixture/authentic lineage separated, references hardened, and detector bundles completed.
- Final review-fix validation: 33 focused tests, 100 evidence tests, and 110 safe regression tests passed; 3 environment-dependent symlink tests were skipped.
- Resolved the final 8 focused review groups: closed custom/native dataset identity, version and limitation retention, role/status/origin promotion, exact frozen baseline binding, strict parsing/direct types, exact mock admission, unique mock influence paths, and immutable numeric authority syntax.
- Final completion validation: 41 focused tests, 108 evidence tests, and 118 safe non-training regression tests passed; 3 environment-dependent symlink tests were skipped. `compileall` and `git diff --check` passed.

### File List

- `_bmad-output/implementation-artifacts/9-2-establish-the-semantic-and-evidence-role-vocabulary.md`
- `_bmad-output/implementation-artifacts/sprint-status.yaml`
- `docs/semantic-vocabulary-v1.md`
- `src/parallel_truth_fingerprint/contracts/__init__.py`
- `src/parallel_truth_fingerprint/contracts/semantic_vocabulary.py`
- `src/parallel_truth_fingerprint/evidence/semantic_validation.py`
- `tests/evidence/test_semantic_vocabulary.py`

## Change Log

- 2026-09-01: Implemented and tested Semantic Vocabulary v1, deterministic validation, evidence-origin amendment controls, legacy mappings, strict unsupported parsing, and synchronized documentation; moved Story 9.2 to review.
- 2026-09-01: Addressed 9 focused code-review findings, added minimal numeric-authority references and fail-closed scientific serialization, expanded the suite to 33 focused tests, and returned Story 9.2 to review.
- 2026-09-01: Addressed the final 8 focused review groups, expanded the suite to 41 semantic tests, completed safe regression validation, and closed Story 9.2 without another broad adversarial review per the approved prototype workflow.
