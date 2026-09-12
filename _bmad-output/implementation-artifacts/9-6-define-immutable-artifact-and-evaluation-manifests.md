# Story 9.6: Define Immutable Artifact and Evaluation Manifests

Status: review

<!-- Note: Planning READY does not authorize implementation or scientific activity. -->

## Story

As a research owner,
I want versioned manifests for artifacts, runs, bundles, and evaluation results,
so that every result can be reconstructed from exact immutable identities without relying on hidden state or mutable aliases.

## Acceptance Criteria

1. **Given** a formal artifact is registered **When** `ArtifactManifest.v1` is serialized or validated **Then** it records a stable logical artifact ID; exact Story 9.2 evidence role, result role, scientific status, synthetic status, dataset/native scope and limitations; audience/access class; contract ID/version and separately verified schema ID/hash; media type; exact byte size and lowercase SHA-256 content ID; qualified immutable locator; producer activity, agent, tool, code, dependency and runtime identities; caller-supplied canonical UTC creation time; applicable Story 9.3 source/license-use references; typed provenance dependencies; and `authorization_effect: none` **And** the artifact-content ID, manifest-revision ID and serialized-manifest byte hash remain distinct, every identity preimage and self-ID exclusion is documented, and any content or identity-bearing metadata change creates a new immutable revision without mutating the prior one.

2. **Given** a formal run is described **When** `RunManifest.v1` is assembled **Then** its immutable revision binds the exact experiment specification, run kind and track requirement profile, physical profile where applicable, Story 9.4 parameter set/gate, contract/schema set, clean code revision or immutable dirty-tree snapshot, dependency lock, interpreter/runtime/platform and container digest where used, seeds/determinism settings where result-affecting, collector/filter/capture configuration, dataset and partition/split, applicable approved mock admissions, bundle, preprocessing, calibration, frozen threshold and fusion policy **And** every closed slot is explicitly `bound`, `not_applicable` with an approved reason, or `unavailable_blocking` with a reason; omission, `null`, an empty token, caller-defined applicability, or inference from filenames/runtime state cannot make a formal run complete.

3. **Given** a detector bundle is referenced by a run, evaluation or later deployment record **When** `BundleManifest.v1` is assembled as a semantically classified artifact-composition record **Then** its immutable composition identity binds exact Story 9.2 role/status/audience fields, weights and architecture artifacts, feature schema and order or vocabulary as applicable, preprocessing, training and calibration dataset/split identities, frozen threshold and derivation, dependency/runtime identity, component roles, sizes and hashes, and any packaged bundle content hash **And** changing any component or binding creates a new bundle identity, mutable aliases/tags are rejected, and this generic contract never fits, recalibrates, loads, promotes, activates or pretends to qualify a detector; track-specific executable bundle rules remain with the later owning stories.

4. **Given** a detector or fusion outcome is recorded **When** `EvaluationResult.v1` is assembled **Then** it binds exactly one dataset family/version and dataset-native scope, one track, one modality or same-run two-modality fusion, exact evaluated support-set identity, runs, partitions, bundle, preprocessing, calibration, frozen threshold, score artifacts, frozen fusion policy where applicable, Story 9.8 truth-unlock/truth-join references, evaluation protocol and code, typed metrics, support/denominators, uncertainty or dispersion, resource and modality-quality evidence, execution outcome, finding disposition, limitations and final-output identity **And** the pinned evaluation protocol supplies the applicable metric requirement set, absent/inapplicable metrics are never coerced to zero, planned invalid/aborted/failed/unfavorable/inconclusive outcomes remain visible, and no universal metric set, cross-dataset scalar ranking, or global champion is inferred across incompatible tracks.

5. **Given** any artifact, run, bundle or evaluation root **When** its manifest dependency graph is validated **Then** every edge records a typed relation and expected immutable revision ID, target contract/version, evidence role and serialized-byte or subject-content hash; the bounded transitive closure is resolved from one pinned resolver snapshot and checked for missing targets, duplicate divergent IDs, self-dependencies, cycles, hash/size/version/role mismatch, ambiguous edges, incompatible or mixed profile/parameter/dataset/split/bundle/threshold/support identities, prohibited fixture/reference/mock promotion and restricted-truth taint **And** any violation fails closed with stable sorted rule IDs, record identity, field path and bounded/redacted expected/observed facts without rewriting the graph.

6. **Given** a mutable convenience alias such as `latest`, a branch, tag, lexicographic-last object or promotion pointer is supplied before formal assembly **When** alias resolution runs **Then** it resolves and verifies exactly one immutable target ID, locator and hash against one resolver snapshot, detects a target change/race, and emits a separate immutable resolution record **And** only the resolved immutable target may enter a formal manifest; a bare or unresolved alias is never accepted as a scientific identity and existing v1 aliases are never promoted automatically.

7. **Given** a complete manifest set is ready for publication **When** the Story 9.6 publication protocol is exercised against an injected write-once/read-back-capable repository **Then** immutable content-addressed objects are written first and read back by exact byte size/SHA-256, the complete immutable manifest is assembled/validated/written next, the full referenced closure and manifest are read back and reverified from one pinned repository snapshot immediately before completion, and a deterministic non-overwriting completion receipt referencing the exact manifest identity/hash is created in one conditional object operation last **And** interruption at any earlier point leaves no discoverable complete result, same-key/different-bytes fails, identical retry is idempotent, ETag is never assumed to be SHA-256, and no current MinIO/local adapter is claimed qualified until Story 9.7 proves its real durability and atomicity properties.

8. **Given** restricted truth, labels, attack annotations, future information, credentials, private keys or other secrets exist **When** manifests and graph views are built **Then** detector-facing roots contain neither those values nor truth-revealing names, locators, counts, timing, identifiers, hashes of low-entropy secrets or transitive restricted dependencies **And** an evaluator-only result may reference restricted evidence only through opaque exact role-separated identities after the required frozen unlock record resolves, without embedding row-level truth or granting a detector access path.

9. **Given** the same valid logical records and referenced bytes **When** parsing, canonical serialization, identity calculation and validation are repeated under different insertion order, locale, timezone, current directory or Windows/POSIX path conventions **Then** the project prerequisite encoder produces deterministic UTF-8/LF bytes, compact sorted object keys, schema-defined array order, strict duplicate/unknown-field rejection, finite canonical numeric representations and one final newline, producing identical identities, hashes and ordered diagnostics **And** no serializer/validator samples the clock, filesystem metadata, environment, alias state or unrestricted process configuration implicitly.

10. **Given** manifest, graph and publication validation passes **When** the result is reported **Then** it proves only schema conformance, deterministic representation, declared byte identity, resolvable typed lineage, role/version/configuration compatibility and publication-protocol completeness at validation time **And** it does not prove authorship, producer honesty, source authority, license legality, storage durability/restoration, scientific or metric correctness, statistical adequacy, reproducibility of execution, absence of all semantic leakage, dataset quality/comparability, mock realism, domain transferability, real-plant validity or authorization to implement, acquire, capture, fit, train, evaluate, promote, activate, publish claims or deploy.

## Amendment Acceptance Criteria

**Given** a manifest, freeze, gate, or activity record admits a domain-bearing dependency
**When** its closure is validated
**Then** it records and verifies the closed evidence origin, exact numeric-authority revision/hash, and â€” where mock-parameterized â€” prototype generation binding, field-level mock influence, current `DirectReproductionAssessment.v1`, official source-use locator/hash, and immutable output trace
**And** any missing, defaulted, stale, substituted, or relabelled dependency fails closed with `authorization_effect: none`.

- [ ] Add pure `unittest` coverage proving that an incomplete origin/mock/numeric closure cannot enter a manifest, freeze, or gate result and cannot create authorization.
## Tasks / Subtasks

- [x] Task 1: Enforce prerequisites and freeze the Story 9.6 contract boundary (AC: 1-10)
  - [x] Treat Stories 9.1-9.5 as hard implementation prerequisites. Require their intended public exports, immutable authorities and focused suites to exist and pass before Story 9.6 code begins. Stop rather than duplicate baseline identity, canonicalization, Story 9.2 vocabulary, Story 9.3 source/license records, Story 9.4 numeric/mock gates or Story 9.5 fixture identities.
  - [x] Define a closed `ManifestContractSet.v1` covering `ImmutableReference.v1`, `ProvenanceEdge.v1`, `BindingSlot.v1`, `ArtifactManifest.v1`, `RunManifest.v1`, `BundleManifest.v1`, `MetricRecord.v1`, `EvaluationResult.v1`, `AliasResolution.v1`, `PublicationReceipt.v1`, validation results and structured violations. Pin its schema ID/hash and canonical machine projection under an identity-addressed path; do not add a JSON Schema dependency, accept caller-defined fields, mutate an existing contract set or publish a `latest` schema alias.
  - [x] Define separate immutable run/bundle/evaluation requirement-profile references. Story 9.6 validates their generic structure and exact identity but supplies no real dataset/track profile; later owning stories must register the domain-specific required slots and metric sets in their own code-pinned or identity-addressed approved registries. Caller-supplied profile data can never register or approve itself. Unit tests use only conspicuous non-domain sentinel profiles in an injected closed test registry.
  - [x] Freeze the ownership table in `docs/evidence-manifests-v1.md`: 9.6 owns generic contracts, pure graph checks, alias pre-resolution and publication ordering; 9.7 owns real persistent-store qualification; 9.8 owns actual partition/freeze/truth-unlock/activity-authorization records; later epics own domain profiles, bundles, scores, metrics and executed results; 17B owns final claim packaging; Epic 18 remains optional presentation.
  - [x] Set `authorization_effect: none` on every planning, contract-definition, validation, alias-resolution and publication-protocol result. No passing path may start or authorize an external or scientific activity.

- [x] Task 2: Define exact canonical forms, identities, locators and safe diagnostics (AC: 1-3, 5-6, 8-10)
  - [x] Add `src/parallel_truth_fingerprint/contracts/evidence_manifest.py` with frozen dataclasses, tuple-backed collections/defensive copies, explicit `StrEnum` values and deterministic `to_dict()` methods. Re-export only the intended public API through `contracts/__init__.py`.
  - [x] Reuse the prerequisite bounded canonical encoder: UTF-8, LF, compact separators, sorted object keys, schema-defined array order, `ensure_ascii=False`, `allow_nan=False`, one final newline, duplicate-key and unknown-field rejection, strict JSON scalar types and Story 9.4 canonical decimal representation for identity-bearing measured values. Do not claim full RFC 8785/JCS conformance unless every normative requirement is separately implemented and tested.
  - [x] Accept lowercase `sha256:<64 hex>` only. Keep logical ID, subject/content digest, manifest-revision ID, schema ID/hash and externally observed canonical-manifest byte hash distinct. Define the complete canonical identity preimage for every record and exclude only its derived self-ID; a referring record binds the target's revision ID and serialized bytes hash so no record contains a circular self-hash.
  - [x] Require caller-supplied timestamps as frozen identity inputs in the single lexical form `YYYY-MM-DDTHH:MM:SS.ffffffZ`: zero-padded ASCII, exactly six fractional digits, UTC `Z`, no leap-second normalization, offset, whitespace or locale-sensitive form. Serialization and validation never call the clock; reject local/ambiguous time, filesystem mtime and silent timezone conversion.
  - [x] Define closed typed immutable locator forms resolved only by injected qualified resolvers. Reject mutable aliases/tags/branches, absolute/drive/UNC/device paths where root-relative form is required, dot/traversal/control/ADS segments, query/userinfo secrets and unqualified external URLs. Keep repository-blob, qualified object-store, root-relative filesystem and OCI-digest locators distinct; never feed an opaque object key to a filesystem path resolver.
  - [x] Emit deterministically sorted violations with stable rule ID, record/logical/revision identity, field path, expected value, observed value or reason and bounded explanation. Reject or redact secrets and arbitrarily large content before diagnostics; do not hash a credential as a redaction strategy.
  - [x] Any maximum byte, node, edge, depth, diagnostic or text bound used by the implementation must resolve to one exact Story 9.4 technical-safety parameter revision. No anonymous numeric guardrail is introduced by this story.

- [x] Task 3: Implement artifact, typed provenance and transitive semantic validation (AC: 1, 5, 8-10)
  - [x] Add `src/parallel_truth_fingerprint/evidence/manifests.py`, reusing Story 9.1 hashing/canonicalization and Story 9.2-9.5 resolvers. Keep it pure and offline except for explicitly injected bounded read operations; add no database, API, service, dynamic import, runtime hook or hidden state.
  - [x] Validate `ArtifactManifest.v1` byte size and content digest against the retrieved opaque bytes immediately before a successful observation. Hash original opaque bytes; never regenerate NPZ, Keras, ZIP, PDF or other backend/container-sensitive formats to manufacture an identity.
  - [x] Require producer lineage to bind the immutable generating activity plus responsible agent, tool, exact code/source-tree state, dependency lock and runtime/platform/container identities. A Git commit alone is insufficient for a dirty tree; bind a clean exact revision or a separately immutable snapshot/patch artifact. A container tag never substitutes for a digest.
  - [x] Resolve applicable Story 9.3 source revision/use and declared-rights records. Preserve `declared`, `concluded`, `unknown`, `restricted` and `not_applicable` distinctions; public access or possession never grants redistribution/publication rights, and manifest validity never constitutes legal analysis.
  - [x] Require one closed audience/access class on every manifest root. Restricted-truth artifact manifests, including their locators and metadata, exist only in the evaluator-authorized registry/view; a detector-facing root cannot reference them directly or transitively. Field-name scanning is only a defense-in-depth test and never the proof of semantic non-leakage.
  - [x] Support typed relations such as `used`, `was_generated_by`, `was_derived_from`, `evaluated_with` and `references` as a bounded project vocabulary inspired by PROV-DM. Do not infer derivation merely from shared usage/generation, implement RDF/PROV, or claim W3C PROV conformance.
  - [x] Traverse one resolver-snapshot closure with deterministic bounded cycle/mismatch detection. Enforce root-specific compatibility constraints rather than naÃ¯vely requiring one configuration across a legitimate declared multi-run evaluation.
  - [x] Propagate Story 9.2 semantic taint through the closure. A locally executed run over mock-derived input remains mock-derived; a published statistic remains reference-only; fixture replay never becomes an evaluation metric; legacy v1 never becomes formal v2; and every domain-bearing mock dependency resolves all applicable Story 9.3 official source uses, Story 9.4 parameter revisions and approved `MockAdmission.v1` including authentic-path unavailability and final dataset-comparison linkage.

- [x] Task 4: Implement formal run and generic detector-bundle manifests (AC: 2-3, 5-6, 8-10)
  - [x] Implement closed named run binding slots for experiment specification, run/track requirement profile, physical profile where applicable, parameter set/gate, contract/schema set, code snapshot, dependency lock, runtime/container, seed/determinism, collector/filter/capture, dataset, partition/split, mock admission, bundle, preprocessing, calibration, frozen threshold and fusion policy. Missing required slots fail; `not_applicable` is accepted only when the independently registered requirement profile permits it; `unavailable_blocking` remains inspectable but cannot yield a complete formal run.
  - [x] Keep exactly two modalities from Story 9.2. Fusion is a same-run result kind referencing the physical and syscall modalities on identical eligible custom support, not a third modality. External ADFA-LD, LID-DS and HAI identities never enter a cross-dataset fused run.
  - [x] Implement `BundleManifest.v1` as a generic immutable composition envelope satisfying FR87 identity mechanics. Bind exact component artifacts and hashes for weights, architecture, feature schema/order or vocabulary, preprocessing, training/calibration datasets and splits, frozen threshold/derivation, dependency/runtime and package bytes where they exist. The pinned bundle requirement profile controls legitimate modality-specific applicability.
  - [x] Reject current v1 model/run records as formal bundles when exact weights/architecture/schema/runtime identities are missing, inference fits a model on load, or a threshold is recalculated from current errors. Preserve these records as legacy evidence and limitations; do not repair, migrate, wrap or silently upgrade them.
  - [x] Make bundle/run construction data-only. It must not import or load Keras/Torch models, inspect model semantics, fit, infer, recalculate a threshold, choose a champion, promote or activate anything.

- [x] Task 5: Implement the common evaluation envelope without executing evaluation (AC: 4-5, 8-10)
  - [x] Implement `EvaluationResult.v1` as an evaluator/restricted-facing immutable envelope. Require exact refs for dataset family/version/native scope, track, modality/result kind, support set, run set, partitions, bundle, preprocessing, calibration, threshold, score artifact, fusion policy where applicable, truth unlock/join, evaluation protocol/code, metrics/uncertainty/resource/quality artifacts, status/limitations and final output.
  - [x] Keep orthogonal axes for structural validation, execution outcome (`complete`, `aborted`, `failed`, `invalidated`), finding disposition (`favorable`, `unfavorable`, `inconclusive`, `not_applicable`), scientific status, publication completeness and activity authorization. An unfavorable completed result remains a retained result; a blocked/aborted result remains visible without fabricated metrics.
  - [x] Define `MetricRecord.v1` with exact metric-definition/version reference, point/window/event/range or declared protocol level, direction, unit, canonical value when present, support/denominator, uncertainty or repeated-run dispersion method/evidence and availability reason. The immutable evaluation-protocol requirement profile decides applicability; the envelope never invents one universal scalar dictionary or coerces missing metrics to zero.
  - [x] Enforce the final-comparison boundary structurally: comparable results require the registered comparison policy to allow the same dataset/track/protocol/support, except the separately preregistered paired same-run `PTFP-Custom-v1` physical/syscall/fusion ablation. External datasets remain in separate native tables; no global cross-domain score, scalar ranking or champion is produced.
  - [x] Require exact future Story 9.8 truth-unlock and partition/freeze references for a complete real evaluation, but treat them as typed unresolved contracts until 9.8 supplies their schema and authorized records. Story 9.6 tests use evaluator-only non-domain sentinels and cannot publish a real evaluation as complete.
  - [x] Validate only recorded envelopes and immutable references. Do not join truth, compute confusion data/metrics/uncertainty, execute evaluation code, inspect labels, or write final report tables.

- [x] Task 6: Implement alias pre-resolution and manifest-last publication protocol (AC: 5-10)
  - [x] Implement explicit alias resolution outside formal manifests. Capture requested alias only in `AliasResolution.v1`, together with resolver snapshot, exact resolved ID/hash/locator and observation time; verify again before assembly to detect movement, then record only the immutable target in the scientific manifest. The resolution record is audit evidence, not a substitute scientific identity or authority grant.
  - [x] Explicitly reject current mutable `fingerprint-training-history/index/latest.json`, lexicographic-last object selection, image tags and Git branches as formal identities. Do not remove or change these legacy convenience paths in this story.
  - [x] Define a minimal injected write-once repository protocol with conditional create, bounded read-back and immutable-key conflict semantics. If the capability is absent, fail closed. Do not retrofit or claim guarantees for the current `MinioArtifactStore`, `LocalFileArtifactStore` or existing fake MinIO client.
  - [x] Publish immutable content-addressed subject objects first; read back and verify exact bytes, size and SHA-256; assemble/validate/publish the complete immutable manifest next; re-read and verify the full referenced closure plus manifest from the same pinned repository snapshot immediately before completion; then conditionally create a deterministic content-addressed `PublicationReceipt.v1` in one object-level operation last. The receipt references the exact manifest revision and serialized hash and is the only formal completeness signal; no mutable `complete` field is patched in place.
  - [x] Leave orphan/staged immutable objects inspectable but incomplete after interruption. Do not expose a complete receipt early, overwrite same-key different bytes, equate ETag with SHA-256, update `latest`, or claim crash durability, restoration, WORM, object-lock or backend atomicity; those are Story 9.7 qualification questions.

- [x] Task 7: Add focused offline tests, documentation and a read-only validator (AC: 1-10)
  - [x] Add `tests/evidence/test_evidence_manifests.py` using standard-library `unittest`, temporary synthetic roots, fixed clocks, injected resolvers and conspicuous non-domain sentinel bytes. Add `tests/evidence/test_manifest_publication.py` only if separation improves clarity. Tests require no ignored archive, network, Docker, MinIO, CometBFT, OPC UA, ML backend, datasets, UI or dashboard.
  - [x] Test deterministic bytes/IDs across object insertion order, locale, timezone, cwd and path separator; every identity-bearing field change; exact preimage/self-ID behavior; malformed/uppercase/wrong-length hashes; duplicate/unknown JSON keys; nonfinite/negative-zero/bool-as-number errors; non-UTC time; unsafe/secret-bearing locators; and every Story 9.4-backed resource bound.
  - [x] Test graph missing/corrupt targets, size/hash/contract/version/role mismatch, duplicate divergent IDs, self/multi-node cycles, registered closure bounds, ambiguous edges, incompatible bindings, legitimate declared multi-run sets, cross-dataset fusion, mock/fixture/reference/legacy promotion and direct/transitive detector-facing truth leakage. Assert deterministic structured diagnostics, not only prose.
  - [x] Test distinct registered non-domain metric requirement profiles without imposing a universal metric set; absent/inapplicable metric handling; retained complete/unfavorable, invalidated, aborted and failed outcomes; and rejection of a purported real complete evaluation without exact partition/freeze/truth-unlock records.
  - [x] Test alias movement between resolve and assembly, bare `latest` rejection and frozen-target stability. Fault-inject before/after every write/read/verification and prove the completion receipt never appears early, exact-byte retry is idempotent, same-key/different-byte conflicts fail, and a repository lacking write-once/read-back capability is rejected.
  - [x] Test current legacy dataset/model/run/inference/promotion records as preserved non-formal inputs, including embedded native `artifact_version: 2.0`, mutable indexes and fit/rethreshold-on-load behavior; no automatic formal conversion is allowed.
  - [x] Add `scripts/validate_evidence_manifests.py` as a read-only offline inspector with deterministic exit codes and machine/human diagnostics. It accepts only explicit immutable roots/snapshots, performs no alias update, write, download, activity or scientific execution, and succeeds only for the structural boundary in AC10.
  - [x] Add `docs/evidence-manifests-v1.md` and the deterministic machine contract-set projection documenting schemas, identities/preimages, locator grammar, provenance relations, audience separation, requirement profiles, publication sequence, failure semantics, repository limitations, academic source scope and the final dataset-comparison boundary.
  - [x] Run the Story 9.1-9.5 focused suites, the Story 9.6 focused suites and full Python `unittest` discovery. Prove the validator/test paths do not write the real evidence store/reference archive, start services, access the network, load models, calculate thresholds/metrics, train, capture, evaluate, publish claims or touch dashboard/UI files.

## Dev Notes

### Scope and dependency boundaries

- This story creates the flat reusable evidence-manifest layer. It does not create a database, evidence service, workflow engine, API, live MinIO integration, real detector bundle, measured result, dataset, partition, freeze, truth-unlock record, activity authorization or final research claim.
- Stories 9.1-9.5 are hard implementation prerequisites and are currently planning artifacts. Implementation must remain sequential and stop if their exports, immutable authorities or tests are absent; placeholders would create competing identities.
- Story 9.7 owns persistent-store capability qualification, real no-overwrite enforcement, restart durability, restoration and failure recovery. The Story 9.6 injected protocol and fake tests prove only ordering and fail-closed client behavior.
- Story 9.8 owns actual `PartitionRecord`, freeze, truth-unlock and `ActivityAuthorization` contracts and semantics. Story 9.6 defines only typed reference slots and cannot claim a real evaluation complete before those records exist.
- Later physical, syscall, fusion and evaluation stories own track-specific requirement profiles, executable bundle validation, score production, applicable metric sets and scientific execution. Epic 17B owns final claim-to-evidence reconstruction.
- Epic 18 dashboard work is optional, presentation-only and non-blocking. This story requires no screen, route, component, visualization, browser test or UI/UX change; manifests and provenance remain inspectable through canonical files and the read-only command.
- `ready-for-dev` approves this planning artifact only. It does not authorize implementation, acquisition, fitting, training, capture, experiment execution, promotion, activation, scientific publication or deployment.

### Identity and provenance rules

- Keep `logical_id`, immutable record/revision ID, subject-content ID, schema ID/hash and serialized-record bytes hash separate. Equal subject bytes can appear in different semantic/provenance roles and therefore share a content ID while having different manifest revisions.
- Include caller-supplied `created_at` in the documented manifest identity preimage when required. Determinism means serializing the same frozen record repeatedly produces the same bytes; it does not silently erase a scientifically relevant creation observation.
- A referenced manifest's own derived revision ID cannot include itself. Referrers bind that revision ID plus the canonical target bytes hash; the publication receipt binds the complete root manifest revision/hash.
- SHA-256 proves byte identity/change detection only. It does not prove source authority, authenticity, authorship, semantic equivalence, scientific validity, license rights, storage durability or successful reproduction.
- Use W3C PROV-DM only as conceptual guidance for entity/activity/agent separation and typed relations. The flat project contracts are not an RDF implementation and do not claim PROV conformance. In particular, shared usage and generation do not by themselves establish derivation.
- Code identity binds a reproducible source-tree state. A dirty checkout needs an immutable patch/snapshot artifact; a commit name alone is insufficient. Dependency/runtime identity binds lock bytes and resolved environment; container images use digests, never tags. Serialize only an allowlisted safe environment identity and never a raw environment dump.
- Keep Story 9.3 source/license lineage exact. Unknown rights remain unknown and block any unsupported redistribution/publication claim. Repository license, public availability, possession or a URL does not license an input dataset or source copy.

### Evaluation and academic claim limits

- `EvaluationResult.v1` is an envelope, not an evaluator. It records the exact identities of already produced score, truth, metric, uncertainty, quality and resource artifacts; it does not compute or bless them.
- Protocol-specific metric applicability avoids manufacturing false comparability. ADFA-LD, LID-DS and HAI results remain separate dataset-native tables; only the preregistered same-run `PTFP-Custom-v1` physical/syscall/fusion ablation can be paired across modalities. There is no global cross-dataset champion.
- A locally executed artifact may still be mock-derived. Scientific status is determined from the complete semantic lineage, not from the final producer alone. Fixture success remains test-only, and a published statistic remains reference-only even if copied into a local file.
- This story introduces no mock, domain numeric value, metric result or tolerance. Tests use conspicuous non-domain sentinels. Any future domain-bearing mock referenced by a manifest is accepted only after the Story 9.4 admission proves authentic reproduction unavailable and binds exact applicable Story 9.3 official documentation, parameter revisions, bounded research purpose and strong final dataset-comparison linkage.
- Passing structural validation cannot prove metric correctness, statistical adequacy, absence of leakage by field-name scanning, external validity, real-plant fidelity or repeatability of the underlying execution. It reports the declared graph faithfully, including adverse and incomplete outcomes.

### Verified current repository behavior

- No general `evidence` package or formal artifact/run/bundle/evaluation manifest exists yet. Current `TrainingDatasetManifest`, `PersistedTrainingDatasetArtifact`, `FingerprintModelArtifact`, `TrainingRunRecord`, `FingerprintInferenceResult` and `ValidConsensusArtifactRecord` are legacy/runtime records, not Story 9.6 formal manifests.
- `persistence/artifact_store.py` and `persistence/local_filesystem.py` serialize indented insertion-order JSON with no canonical hash, exclusive create or read-back verification. The local adapter accepts unqualified path joins and creates directories, so it is not a trusted Story 9.6 resolver/writer boundary.
- `lstm_service/dataset_artifacts.py` currently writes the dataset manifest before its NPZ content. Interruption can expose a manifest without its subject bytes; Story 9.6 must not reuse this ordering as evidence of completeness.
- Existing object keys and IDs are based on round ranges, timestamps or UUIDs. Same-ID/different-bytes and same-input/different-ID behavior are possible. They remain legacy identities unless a later explicit source-aware conversion produces a separate formal manifest.
- Offline promotion writes `fingerprint-training-history/index/latest.json`, and lifecycle/replay code can choose the lexicographically latest object. These aliases remain convenience behavior only and are never formal identities.
- Current online inference can fit on load and current inference can recalculate a threshold from source errors. Existing model metadata lacks the complete weights/architecture/schema/dependency/runtime hashes required by FR87, so no current promoted v1 model may be silently represented as a frozen formal bundle.
- Current training provenance uses arbitrary mappings/stringification and can co-locate truth-derived metrics or class labels with run configuration. New contracts use closed fields, audience separation and secret-safe diagnostics; they do not serialize `MinioStoreConfig`, environment dumps, access keys, secret keys, private keys or label payloads.
- NPZ/Keras/ZIP bytes are backend/platform sensitive. Formal content identity hashes the actual retained opaque bytes; regeneration is not identity recovery.

### Project structure notes

- Contracts: `src/parallel_truth_fingerprint/contracts/evidence_manifest.py` and intended exports in `contracts/__init__.py`.
- Validation/identity/graph/alias boundary: `src/parallel_truth_fingerprint/evidence/manifests.py`.
- Publication protocol: keep in `evidence/manifests.py` unless a focused `src/parallel_truth_fingerprint/evidence/publication.py` materially improves cohesion.
- Machine contract authority and documentation: `docs/evidence/manifests/v1/contracts/sha256-<digest>/manifest-contract-set.v1.json` and `docs/evidence-manifests-v1.md`; no mutable singleton or `latest` contract path.
- Read-only validation command: `scripts/validate_evidence_manifests.py`.
- Tests: `tests/evidence/test_evidence_manifests.py` and optionally `tests/evidence/test_manifest_publication.py`.
- Do not modify current serializers, store layouts, training/inference, dataset/model artifacts, promotion/latest behavior, scientific data, or dashboard/UI in this story. Do not add a DB, API, service, RDF library, JSON Schema dependency, workflow framework or ML dependency.

### Technical research notes

- W3C PROV-DM distinguishes entities, activities, agents, usage, generation and derivation, and states that usage plus generation is not alone sufficient to establish derivation. Story 9.6 adopts only a small flat typed-relation vocabulary and does not claim W3C PROV conformance.
- RFC 8785 demonstrates that hashable JSON requires invariant representation beyond key sorting. The project uses its prerequisite bounded schema encoder; JCS conformance is not claimed without implementing and testing the full RFC.
- OCI Image Specification v1.1.1 descriptors bind media type, digest and size and require retrieved content to match the descriptor. Story 9.6 uses that as narrow conceptual support for byte verification and never treats ETag, a tag or a locator as the content digest or claims OCI conformance.
- SPDX 3.0.1 Licensing Profile distinguishes declared, concluded and unresolved license information. Story 9.6 preserves those states through Story 9.3 references without making legal conclusions or granting rights.
- Python 3.14 `json` documents that `allow_nan=True` is the default and that `sort_keys` controls dictionary ordering. The new bounded encoder explicitly rejects nonfinite values and duplicate/unknown fields; `sort_keys=True` alone is not a canonicalization proof.
- These authorities support manifest/provenance/serialization/license mechanics only. They do not support domain numbers, metric validity, mock realism, dataset equivalence or scientific conclusions. No new domain source or mock is required by this story.

### Testing standards

- Use standard-library `unittest`, table-driven `subTest()` cases, fixed clocks, temporary roots, deterministic non-domain sentinel bytes, injected resolvers and fake conditional stores. No new runtime dependency is required.
- Assert canonical bytes, record identities, exact hashes, structured rule IDs/field paths, audience/semantic state and publication call order. Never rely only on prose messages or an implementation-generated golden oracle.
- Exercise Windows path/UNC/drive/ADS/reparse and POSIX traversal cases through portable validators; real symlink/junction cases may be conditional, but an injected resolver must cover fail-closed containment on every platform.
- Fault-inject publication after every operation and assert no complete receipt is visible early. Fake-store success proves client protocol/order only, not real storage durability, WORM or recovery.
- Run full Python discovery because new public contract exports and the shared `evidence` package can affect imports even when no runtime integration is added.

## BMAD Party Mode Review

- Review panel: John (product scope), Winston (architecture), Quinn (QA/evidence integrity), and Amelia (developer readiness).
- Initial aggregate score: 8.90/10 - vetoed. The first round found that the bundle invariant required by FR87 was absent from the original epic ACs, the machine contract authority could be interpreted as a mutable singleton, caller-supplied requirement profiles could appear self-authorizing, the timestamp grammar was not lexically closed, audience separation needed to apply at every manifest root, and the publication sequence did not yet require a final closure-wide read-back before exposing completeness.
- Final product-scope score: 9.75/10 - no veto.
- Final architecture score: 9.65/10 - no veto.
- Final academic-evidence and QA score: 9.80/10 - no veto.
- Final developer-readiness score: 9.60/10 - no veto.
- Aggregate final score: 9.70/10.
- Auto-approval rule: score at least 9.0 with no veto.
- Decision: auto-approved as `ready-for-dev` after adding the generic bundle contract, identity-addressed schema authority, independently approved requirement-profile registries, exact UTC lexical form, root-level audience separation, full-closure re-verification, one-operation completion receipt, and explicit current-store/non-authorization boundaries.
- Academic-evidence finding: no domain value, metric, tolerance or mock is created. Existing primary authorities are sufficient for the bounded manifest mechanics only; any future domain-bearing mock still fails closed unless Story 9.4 proves authentic reproduction unavailable and resolves strongly applicable Story 9.3 official source-use and parameter evidence tied to the final dataset comparison.
- Boundary: this decision approves the planning artifact only; `authorization_effect` remains `none`.

### References

- [Source: _bmad-output/planning-artifacts/epics.md#Story 9.6: Define Immutable Artifact and Evaluation Manifests]
- [Source: _bmad-output/planning-artifacts/epics.md#Cross-Epic Mock Admission Guardrail]
- [Source: _bmad-output/planning-artifacts/prd.md#FR26]
- [Source: _bmad-output/planning-artifacts/prd.md#FR28]
- [Source: _bmad-output/planning-artifacts/prd.md#FR40]
- [Source: _bmad-output/planning-artifacts/prd.md#FR65]
- [Source: _bmad-output/planning-artifacts/prd.md#FR87-FR88]
- [Source: _bmad-output/planning-artifacts/prd.md#NFR26]
- [Source: _bmad-output/planning-artifacts/prd.md#NFR40-NFR41]
- [Source: _bmad-output/planning-artifacts/prd.md#NFR48-NFR52]
- [Source: _bmad-output/planning-artifacts/architecture.md#Controlling V2 Architecture Consolidation - 2026-08-22]
- [Source: _bmad-output/planning-artifacts/architecture.md#Authoritative evidence contracts]
- [Source: _bmad-output/planning-artifacts/architecture.md#Verification gates and failure semantics]
- [Source: _bmad-output/implementation-artifacts/9-1-freeze-and-index-the-v1-evidence-baseline.md]
- [Source: _bmad-output/implementation-artifacts/9-2-establish-the-semantic-and-evidence-role-vocabulary.md]
- [Source: _bmad-output/implementation-artifacts/9-3-build-the-authoritative-source-evidence-catalog.md]
- [Source: _bmad-output/implementation-artifacts/9-4-build-the-parameter-evidence-catalog-and-validation-gate.md]
- [Source: _bmad-output/implementation-artifacts/9-5-preserve-v1-contracts-as-golden-versioned-fixtures.md]
- [Source: src/parallel_truth_fingerprint/contracts/dataset_artifact.py]
- [Source: src/parallel_truth_fingerprint/contracts/fingerprint_model.py]
- [Source: src/parallel_truth_fingerprint/contracts/fingerprint_inference.py]
- [Source: src/parallel_truth_fingerprint/contracts/persistence_record.py]
- [Source: src/parallel_truth_fingerprint/contracts/training_dataset.py]
- [Source: src/parallel_truth_fingerprint/persistence/artifact_store.py]
- [Source: src/parallel_truth_fingerprint/persistence/local_filesystem.py]
- [Source: src/parallel_truth_fingerprint/lstm_service/dataset_artifacts.py]
- [Source: src/parallel_truth_fingerprint/lstm_service/inference.py]
- [Source: src/parallel_truth_fingerprint/lstm_service/offline_training/registry/training_history.py]
- [Source: src/parallel_truth_fingerprint/lstm_service/offline_training/registry/promotion.py]
- [W3C PROV-DM](https://www.w3.org/TR/prov-dm/)
- [RFC 8785: JSON Canonicalization Scheme](https://www.rfc-editor.org/rfc/rfc8785.html)
- [RFC 3339: Date and Time on the Internet](https://www.rfc-editor.org/rfc/rfc3339.html)
- [OCI Image Specification v1.1.1 descriptor](https://github.com/opencontainers/image-spec/blob/v1.1.1/descriptor.md)
- [SPDX 3.0.1 Licensing Profile](https://spdx.github.io/spdx-spec/v3.0.1/model/Licensing/Licensing/)
- [Python 3.14 `json`](https://docs.python.org/3.14/library/json.html)

## Mandatory Academic Evidence Amendment

Before implementation, apply the relevant mandatory controls in [Academic Evidence Admission Amendment â€” 2026-08-31](../planning-artifacts/academic-evidence-admission-amendment-2026-08-31.md). This story must fail closed on an unresolved evidence origin, numeric authority, required mock closure, or prohibited dataset substitution. The amendment adds no activity authorization.
## Dev Agent Record

### Agent Model Used

### Debug Log References

### Completion Notes List

- 2026-09-08: Completed Task 1 boundary audit. Added and tested the explicit cross-story ownership table; the generic manifest authority remains non-authorizing.
- 2026-09-08: Task 2 progress: tightened immutable repository/object locator validation to reject absolute paths, relative roots and segments, traversal, empty segments, and control characters; focused and prerequisite suites pass. Resource-limit authority remains fail-closed pending an exact Story 9.4 technical-safety revision.
- 2026-09-08: Completed Task 2. Replaced the anonymous diagnostic truncation with deterministic fixed-size hashes for non-secret facts and explicit secret redaction.
- 2026-09-08: Task 3 progress: graph closure now rejects duplicate divergent immutable revision identities; focused tests pass.
- 2026-09-08: Task 3 progress: artifact roots now reject unknown access classes and direct restricted-truth dependencies from detector-facing roots; focused and prerequisite suites pass.
- 2026-09-08: Task 3 progress: injected dependency resolvers now enforce transitive restricted-truth taint checks during artifact validation; focused tests pass.
- 2026-09-08: Task 4 progress: bundle validation now resolves an injected registered requirement profile, enforces required components and profile-approved not-applicable bindings, and rejects non-detector/public access; focused tests pass.
- 2026-09-08: Task 5 progress: evaluation validation now resolves an injected registered requirement profile, requires its binding slots, and rejects metric definitions not registered by that profile; focused and prerequisite suites pass.
- 2026-09-08: Task 6 progress: manifest-last publication now rechecks the declared referenced closure in the pinned snapshot before receipt creation; corrupt closure leaves no receipt; focused tests pass.
- 2026-09-08: Task 4 progress: bundle modality is now closed to physical/syscall; fusion remains a same-run result kind rather than a detector modality; focused and prerequisite suites pass.
- 2026-09-08: Task 3 progress: artifact validation now requires immutable producer activity, agent, tool, code, dependency-lock, and runtime lineage; focused and prerequisite suites pass.
- 2026-09-08: Task 7 progress: expanded the evidence-manifests documentation with canonical identities, locator grammar, bounded diagnostics, profiles, graph closure, and manifest-last readback semantics; focused suite and read-only contract validator pass.
- 2026-09-08: Task 5 progress: PTFP-Custom-v1 fusion results now require bound physical and syscall run references, preventing single-modality or implicit fusion; focused and prerequisite suites pass.
- 2026-09-08: Regression validation: installed the declared Python runtime dependencies (`numpy`, `minio`, `keras`, and CPU `torch`) and executed all test modules: 407 passed, 11 explicitly opt-in tests skipped.
- 2026-09-08: Definition of Done verified: contracts, validators, documentation, identity-addressed contract authority, and the complete regression suite satisfy Story 9.6's structural-only scope. No execution, training, capture, truth join, publication claim, activation, or storage qualification was performed.

### File List

- docs/evidence-manifests-v1.md (modified)
- src/parallel_truth_fingerprint/evidence/manifests.py (modified)
- tests/evidence/test_evidence_manifests.py (modified)
