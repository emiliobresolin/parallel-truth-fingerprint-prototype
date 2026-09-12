# Story 9.1: Freeze and Index the v1 Evidence Baseline

Status: done

## Story

As a research owner,
I want an immutable and inspectable manifest of the complete v1 baseline,
so that v2 work cannot rewrite history or misrepresent legacy evidence.

## Acceptance Criteria

1. **Complete, inspectable coverage.** Given the current v1 repository, declared runtime, and evidence roots, when the baseline manifest is prepared, then it covers the code revision and working-tree overlays, dependency/runtime identity, non-secret configuration identity, MQTT and consensus contracts, OPC UA and dashboard-state schemas, storage objects, datasets, models, and recorded experimental results; and every entry contains a stable ID, category, role, version when available, normalized locator, byte size when applicable, SHA-256 identity or explicit reason it cannot be verified, verification status, scientific-status label, a closed evidence-origin value when that origin is mechanically established, and limitation when applicable. An unresolved historical origin remains explicit and cannot be inferred from a directory name.
2. **Honest failure states.** Given an expected baseline item is missing, mutable, corrupt, unreadable, unhashable, or cannot otherwise be verified, when inventory and validation run, then the entry is explicitly classified as `missing`, `mutable`, `corrupt`, or `unverifiable` with the supporting limitation; and no identity, artifact, model, metric, or result is inferred, regenerated, downloaded, or fabricated to fill the gap.
3. **Secret-safe evidence.** Given configuration or runtime material can contain credentials, tokens, private keys, or other secrets, when it is inventoried, serialized, logged, or reported, then only approved non-secret values, safe field names, redacted placeholders, or an approved digest of canonical redacted content may appear; raw secrets and hashes of secret values never appear in Git, manifests, logs, exceptions, or reports.
4. **Immutable, manifest-last publication.** Given every entry claimed as immutable has been collected, when the baseline is finalized, then each referenced immutable object is reverified before the complete canonical manifest is atomically published under a content-addressed identity; an existing finalized identity cannot be overwritten; and no mutable `latest` alias, tag, pointer, or working path is used as the scientific identity.
5. **Scientific-role separation.** Given the frozen v1 material mixes runtime implementation, fixtures, publications, measurements, and experimental fingerprint history, when entries are classified, then `IMPLEMENTED_RUNTIME_EVIDENCE`, `FIXTURE`, `PUBLISHED_REFERENCE`, `MEASURED_RESULT`, `EXPERIMENTAL_FINGERPRINT_BASELINE`, and `LEGACY_BASELINE` remain distinguishable; a file's presence under a result directory alone never establishes `MEASURED_RESULT`; historical result tables without mechanically resolved origin remain `LEGACY_BASELINE` with a limitation; the historical detector and its outputs are `LEGACY_BASELINE`, never a final physical detector or a dataset; and optional dashboard artifacts remain presentation/compatibility evidence rather than scientific proof.
6. **Read-only compatibility boundary.** Given later v2 planning or implementation consumes this baseline, when it resolves a v1 item, then it uses the frozen baseline ID plus exact entry identities and fails closed on ambiguity or mismatch; creating, validating, or resolving the baseline changes no active v1 code, configuration, runtime state, logs, datasets, models, object-store state, training history, or dashboard state and grants no implementation, v2 activation, acquisition, training, capture, promotion, or experiment authorization.

## Tasks / Subtasks

- [x] Task 1: Define the baseline-specific contract and required inventory (AC: 1, 2, 5, 6)
  - [x] Add frozen dataclasses for `V1BaselineManifest.v1`, its entries, repository identity, explicit limitations, and validation result in `src/parallel_truth_fingerprint/contracts/v1_baseline.py`, following existing deterministic `to_dict()` patterns.
  - [x] Pin the Story 9.1 verification values to `verified`, `missing`, `mutable`, `corrupt`, and `unverifiable`; pin the six minimal scientific-status values named in AC 5. Do not implement the general Story 9.2 vocabulary.
  - [x] Define an allowlisted expected-inventory specification for every AC 1 category. Discovery may add observed entries but must never substitute for a missing required entry.
  - [x] Keep `V1BaselineManifest.v1` baseline-specific. Do not implement or name it as the reusable `ArtifactManifest.v1`/evaluation-manifest framework owned by Story 9.6.
  - [x] Carry only the amendment's closed `evidence_origin` values when mechanically established; do not infer origin from a directory name, and keep unresolved historical result tables as limited `LEGACY_BASELINE` entries until the Story 9.2 vocabulary can classify them explicitly.

- [x] Task 2: Implement deterministic, read-only baseline collection (AC: 1, 2, 3, 6)
  - [x] Add `src/parallel_truth_fingerprint/evidence/__init__.py` and `src/parallel_truth_fingerprint/evidence/v1_baseline.py` for collection, canonical serialization, hashing, validation, resolution, and publication; add no service, database, workflow engine, UI component, or external dependency.
  - [x] Capture the verified Git `HEAD` plus branch and machine-stable `git status --porcelain=v1 -z` information. For in-scope dirty tracked overlays, record the observed file identity separately from `HEAD`; never require a clean/reset/commit operation and never hardcode the planning-time commit.
  - [x] Inventory Python identity and lockfiles, Go module files, Dockerfiles, Compose declarations, and declared image references. Runtime observations are observations, not proof of historical execution; missing tools or image digests remain `unverifiable`/`mutable`. Never pull images or start services.
  - [x] Inventory MQTT serializers/contracts, Python and Go consensus contracts, OPC UA contracts, dashboard read-model/state schemas, declared storage namespaces/objects, datasets, model records/weights, training history, and recorded result/evidence files.
  - [x] Represent committed content, dirty overlays, ignored/untracked evidence, mutable pointers, unavailable external storage, and excluded post-v1 planning material separately so none is silently attributed to the base commit.
  - [x] For dataset directories, build a sorted child inventory and root digest without parsing, executing, training from, copying, or modifying dataset content.

- [x] Task 3: Enforce safe locators and honest verification states (AC: 1, 2, 4)
  - [x] Normalize local locators to project-relative POSIX form and object-store locators to explicit bucket/key form. Reject absolute output locators, traversal, symlink/junction escape, and any resolved path outside an allowlisted root.
  - [x] Stream SHA-256 over regular files in binary mode; compare pre/post file identity and metadata so mutation during hashing produces `mutable`, not `verified`.
  - [x] Classify `corrupt` only when an expected digest fails or a declared safe structural validator fails. Without such an oracle, classify the item `unverifiable`, not corrupt.
  - [x] Never deserialize or execute model, dataset, archive, contract-sample, or evidence payloads merely to calculate identity; safe JSON structural checks may be used only where an explicit JSON contract is declared.
  - [x] Re-resolve and rehash every `verified` immutable entry immediately before publication; abort publication on mismatch while retaining the limitation in a validation result.

- [x] Task 4: Enforce secret exclusion and redacted configuration identity (AC: 3, 6)
  - [x] Define explicit approved non-secret configuration keys and a denylist covering at least password, secret, token, credential, private/access key, and CometBFT validator/node-key material.
  - [x] Do not open or hash `.env`, CometBFT private-key files, or other denylisted secret files. Record only their excluded/redacted status and safe locator/field-name metadata where needed.
  - [x] Produce a canonical redacted configuration view from tracked templates and allowlisted runtime fields. Secret-value changes must not affect its identity; approved non-secret changes must.
  - [x] Apply the same sanitizer before logging, exception formatting, human-readable summaries, and manifest serialization.

- [x] Task 5: Canonicalize and publish the manifest immutably (AC: 2, 4, 6)
  - [x] Serialize UTF-8 JSON deterministically with stable entry ordering, recursively stable keys, compact separators, `ensure_ascii=False`, and rejection of NaN/Infinity. Do not claim RFC 8785 compliance unless every RFC requirement is implemented and tested.
  - [x] Calculate `baseline_id` as `sha256:<digest>` over an explicitly documented canonical identity payload that excludes only its own derived `baseline_id` field. Evidence-relevant provenance, including the injected observation time, belongs to the hashed payload; fixed inputs and fixed observation time must produce byte-identical payload and identity.
  - [x] Publish only to `_bmad-output/evidence-artifacts/v1-baselines/sha256-<digest>/baseline-manifest.v1.json`; never create a baseline `latest` pointer.
  - [x] Write and flush a sibling temporary file, then use an atomic fail-if-target-exists publication primitive on the same filesystem. Do not use overwrite-capable `LocalFileArtifactStore.save_json()`, `MinioArtifactStore.save_json()`, or an unguarded `os.replace()` for the finalized identity.
  - [x] Make the complete manifest the final publication object. An interruption may leave only an identifiable staging artifact, never a partial manifest accepted as finalized; rerunning against an existing final identity must verify equality and refuse mutation.
  - [x] Set `authorization_effect` to `none` and expose no route, flag, pointer, or state transition that can authorize later activity.

- [x] Task 6: Preserve historical interpretation and resolve exact frozen entries (AC: 5, 6)
  - [x] Label the legacy live autoencoder, its run records, and applicable outputs `LEGACY_BASELINE`/historical with their observed limitations; do not relabel original bytes.
  - [x] Record mutable `fingerprint-training-history/index/latest.json` as a convenience pointer plus its observed exact target; only the immutable target identity may be resolved scientifically.
  - [x] Add a read-only resolver that requires `baseline_id` and stable entry ID, verifies the stored digest/size, and fails closed on unknown ID, mutable-only locator, mismatch, or ambiguous target.
  - [x] Keep any later Story 9.2 vocabulary mapping separate and versioned so the frozen Story 9.1 bytes never need rewriting.

- [x] Task 7: Add a narrow CLI and inspection summary (AC: 1, 2, 3, 4, 6)
  - [x] Add `scripts/freeze_v1_baseline.py` as an explicit offline command that accepts repository/evidence roots and observation time, prints only a secret-safe summary, and returns non-zero on validation/publication failure.
  - [x] Default to read-only collection plus explicit publication; do not import runtime startup modules or trigger MQTT, CometBFT, MinIO writes, OPC UA, dashboard, training, capture, or experiments.
  - [x] The human-readable summary must show category counts and every non-verified limitation, but it is never the authoritative baseline and must resolve to the JSON identity.

- [x] Task 8: Prove the contract with focused and regression tests (AC: 1-6)
  - [x] Add `tests/evidence/__init__.py` and `tests/evidence/test_v1_baseline.py` using temporary directories, deterministic fixtures, fake object listings, and subprocess stubs; no network, Docker daemon, object-store write, or active service is required.
  - [x] Test complete expected inventory; stable ordering/bytes/digest; changed bytes changing identity; dirty-commit overlay identity; deterministic dataset root digest; and exact resolver success/fail-closed behavior.
  - [x] Test every explicit failure status, known digest/JSON corruption, unavailable MinIO, absent model weights/run records, mutable tag and `latest` pointer handling, mutation during hashing, path traversal, and symlink/junction escape.
  - [x] Use secret canaries to prove raw values and their digests never reach manifest bytes, summaries, logs, exceptions, or Git output; prove private CometBFT material is never opened.
  - [x] Test scientific-role incompatibilities: fixtures/publications/measurements stay distinct; normal-only custom data cannot become a supervised measured result; `LEGACY_BASELINE` cannot become a dataset or final physical detector; dashboard absence cannot fail the core scientific baseline.
  - [x] Test interrupted publication, existing-target refusal, manifest-last behavior, absence of a baseline `latest` alias, and `authorization_effect: none`.
  - [x] Snapshot all in-scope runtime/config/evidence paths before and after generation/validation and assert no changes; run `.\.venv\Scripts\python.exe -m unittest tests.evidence.test_v1_baseline` and then `.\.venv\Scripts\python.exe -m unittest discover -s tests`.

- [x] Task 9: Resolve the second adversarial review findings (AC: 1-6)
  - [x] Prevent raw configuration files and nested mutable `latest.json` pointers from resolving as immutable evidence.
  - [x] Reverify repository identity, including HEAD, status, and overlays, before publication.
  - [x] Reject secret-bearing or structurally unsafe mutable-pointer targets.
  - [x] Apply explicit non-secret allowlisting to Compose configuration identity.
  - [x] Include all existing thesis result tables in the required inventory.
  - [x] Sanitize secret-bearing Git status and rename/copy source metadata.
  - [x] Exclude derived/cache roots from recursive ignored-overlay hashing.
  - [x] Confine the publication root against symlink or junction escape.
  - [x] Validate observation time as an actual UTC calendar instant.
  - [x] Validate the full Docker SHA-256 digest syntax before describing a declaration as pinned.
  - [x] Classify non-regular mutable-pointer objects as unverifiable.
  - [x] Add a minimal closed evidence-origin field and keep unresolved historical tables out of `MEASURED_RESULT`.

- [x] Task 10: Resolve the third adversarial review findings (AC: 1-5)
  - [x] Redact mutable-pointer identity before hashing optional JSON fields.
  - [x] Reject symlinked finalized manifests.
  - [x] Validate non-environment Compose scalar values before identity hashing.
  - [x] Sanitize Git branch and excluded post-v1 secret-bearing paths.
  - [x] Preserve the invariant that `known_absence` entries cannot become verified evidence.
  - [x] Apply redacted configuration identity to configuration dirty overlays.
  - [x] Fall back to ordinary Git status for tracked/untracked overlays when ignored-status collection fails.
  - [x] Populate and validate mechanically established fixture origin.
  - [x] Remove incomplete final directories after publication-link failure.
  - [x] Include repository and overlay limitations in the CLI summary.
  - [x] Reject impossible metadata on `missing` entries.
  - [x] Add focused regression coverage for every third-review correction.

- [x] Task 11: Close the final pragmatic review findings (AC: 1, 3, 4, 6)
  - [x] Expand secret-path exclusion for common credential-file names.
  - [x] Inventory the remaining result-bearing validation table and Markdown companions.
  - [x] Require resolver input to match the actually published content-addressed manifest.
  - [x] Make identical publication reruns succeed before repository-state revalidation.
  - [x] Add focused tests for the four final corrections and complete Story 9.1.

## Dev Notes

### Scope and controlling decisions

- This story implements FR30 only: freeze and index the existing v1 baseline. It does not repair, reproduce, download, retrain, recapture, promote, or reinterpret missing history.
- The controlling architecture is the 2026-08-22 consolidation. Keep this a flat, versioned contract plus deterministic library and offline CLI inside the existing process; no new service, database, UI, or deployment component is justified.
- Planning approval and `ready-for-dev` status authorize implementation of this story only. They do not authorize scientific acquisition, training, capture, experimentation, v2 activation, or publication of claims.
- UI/UX is optional and out of scope. Dashboard files are indexed only as legacy state-schema/presentation evidence; no dashboard behavior or appearance is required for completion.

### Baseline contract and boundaries

- `V1BaselineManifest.v1` is a minimal aggregate needed to freeze v1. It should carry the architecture-compatible provenance fields useful here, but Story 9.6 still owns the reusable `ArtifactManifest.v1` and evaluation-manifest framework.
- Use a manifest-level repository identity containing base commit, branch, scoped worktree status identity, and individual dirty-overlay entries. `HEAD` alone cannot represent the current v1 state.
- Entry fields required by AC 1 are normative. Optional values must be absent/`null` rather than guessed. `verified` means the referenced bytes and locator were checked; a known hash on a mutable source does not make the source immutable.
- `corrupt` requires evidence: a mismatch against an expected digest or failure of an explicitly declared safe structure check. “Looks unusual” is not corruption.
- Baseline completeness means every expected category/item has an entry, including explicit absence. It does not mean every historical artifact is locally recoverable.
- Preserve original artifacts byte-for-byte. Interpretation and future semantic mappings are separate records; they never rewrite the baseline.

### Required inventory anchors

- Code and dependencies: tracked `src/`, `abci/consensus_app/`, `scripts/`, `pyproject.toml`, `uv.lock`, Go module files, Dockerfiles, and Compose declarations. Exclude `.git` internals, `.venv`, caches, `build/`, and temporary roots as non-authoritative/derived.
- Contracts: `src/parallel_truth_fingerprint/contracts/`, `src/parallel_truth_fingerprint/edge_nodes/common/mqtt_io.py`, consensus Python mapping/client files, `abci/consensus_app/internal/app/`, SCADA/OPC UA contracts and service schema, dashboard state builder/control surface, and contract samples.
- Evidence/artifacts: declared object namespaces `valid-consensus-artifacts/`, `fingerprint-datasets/`, `fingerprint-models/`, `fingerprint-training-history/runs/`, and `fingerprint-training-history/index/by-benchmark/`; local `_bmad-output/local-store`, `_bmad-output/results-evidence`, `docs/seminario-andamento/evidence`, tracked logs, embedded dataset fixtures, and the reference-archive checksum catalog.
- Configuration: `.env.example`, runtime config modules, and Compose non-secret fields. `.env`, `.cometbft` private keys/state, credentials, and secret values are not baseline bytes and must not be read or hashed.
- Ignored/untracked datasets and external object storage are outside the Git identity. Record their independent observed inventory/hash when safely available; otherwise record the exact limitation.

### Known v1 limitations to encode, not repair

- The planning-time repository is dirty and includes a runtime-affecting cycle-interval overlay. Recompute at implementation time and record the exact base commit plus scoped overlay identities; do not hardcode or clean the planning-time state.
- `fingerprint-training-history/index/latest.json` is mutable and points to the May 2026 multiclass GRU run, not the later reported binary champion. Record pointer and exact target separately.
- No project model-weight artifact is present; the promoted run record does not prove recoverable weights. The weights remain `missing`, and online refitting is not a reconstruction method.
- The reported June binary champion run JSON/weights and historical `fingerprint-datasets.zip` are absent from the working tree and remain `missing`/`unverifiable` as applicable.
- The preserved custom dataset has only 13 normal-only windows, `adequacy_met=false`, and `runtime_valid_only`; it cannot support a supervised scientific-result claim.
- Local ADFA-LD content is ignored by Git and must have an independent deterministic inventory/root digest or an explicit limitation. Do not redownload or regenerate it.
- `compose.local.yml` uses mutable Mosquitto and MinIO tags; the declarations are `mutable` unless a separately observed digest is recorded. CometBFT is digest-pinned. Docker inspection is optional and read-only; absence of the daemon is `unverifiable`, not a reason to pull.
- August planning/reference artifacts that postdate v1 are provenance/context or explicit exclusions, never original v1 runtime evidence merely because they are present locally.

### Existing code to reuse and avoid

- Reuse frozen dataclass and deterministic `to_dict()` conventions from `src/parallel_truth_fingerprint/contracts/dataset_artifact.py`, `fingerprint_model.py`, `training_dataset.py`, and `persistence_record.py`.
- Reuse read-only artifact-store interfaces/fakes where helpful, but do not call existing `LocalFileArtifactStore.save_json()` or `MinioArtifactStore.save_json()` for final publication: both allow overwrite and lack manifest-last atomic guarantees.
- Do not import runtime startup/control modules from the baseline library or CLI. Reference their source/schema files as evidence instead.
- No dependency update is part of this historical freeze. Use the repository's Python `>=3.14` constraint, current lockfiles, and standard library hashing/JSON/path/process primitives.

### Determinism, safety, and publication guidance

- Invoke Git and optional runtime inspection with argument arrays, no shell, bounded timeout, captured output, and deterministic decoding. `git status --porcelain=v1 -z` is the stable machine-readable worktree form; `git rev-parse --verify HEAD` verifies the commit object.
- Hash binary files in blocking mode and close them after `hashlib.file_digest()`. Sort normalized locators by Unicode code point before aggregate hashing.
- Keep observation time injectable and include it in the canonical identity payload. Tests must supply a fixed value; a real collection records its actual observation boundary instead of pretending that two observations at different times are the same event.
- An overwrite-preventing atomic publication primitive is mandatory. A pre-check followed by overwrite-capable replacement has a race and is insufficient. If the platform cannot provide the guarantee, fail safely and report the limitation.
- The generated manifest is an implementation artifact, not a source-code change to commit blindly. Never add datasets, model binaries, `.env`, private keys, or other ignored secret/bulk material to Git.

### Testing standards

- Follow the repository's `unittest` convention. Tests must be self-contained and deterministic, with temporary directories and fakes; they must not depend on the developer's dirty worktree contents, local Docker/Go availability, MinIO, network access, or current clock.
- Focus tests on scientific misclassification, secret leakage, false immutability, and side effects—not on UI rendering.
- Run the focused module before the full suite. Do not modify or clean unrelated user files to make tests pass.

### Project Structure Notes

- New contract: `src/parallel_truth_fingerprint/contracts/v1_baseline.py`.
- New evidence boundary: `src/parallel_truth_fingerprint/evidence/__init__.py` and `src/parallel_truth_fingerprint/evidence/v1_baseline.py`.
- New explicit offline entry point: `scripts/freeze_v1_baseline.py`.
- New tests: `tests/evidence/__init__.py` and `tests/evidence/test_v1_baseline.py`.
- Generated output: `_bmad-output/evidence-artifacts/v1-baselines/sha256-<digest>/baseline-manifest.v1.json`.
- Do not place authoritative code in ignored `build/`, generated evidence in mutable `logs/`, or scientific identity behind `latest`.
- There is no previous dedicated Epic 9 story artifact. Existing v1 code is historical implementation evidence; Stories 9.2-9.8 remain downstream and must not be absorbed here.

### Technical Research Notes

- No library or framework upgrade is required. This story freezes the versions recorded by `uv.lock`, Go module files, Compose declarations, and observed runtime identity instead of substituting a newer environment.
- Python's official `hashlib.file_digest()` documentation requires a binary, blocking file object and warns that the file object's state is unspecified afterward; close files deterministically.
- Python's official JSON documentation supports stable key ordering and compact separators, but that alone is not equivalent to RFC 8785; this story requires a documented project canonical form, not an unsupported compliance claim.
- Python's official filesystem documentation describes atomic replacement but replacement can overwrite an existing target; the implementation must combine atomic finalization with exclusive no-overwrite semantics.
- Docker's official documentation treats digests as content-addressable identities and tags as names that can move. Inspection may record a locally observed digest, but it must not pull or mutate runtime state.

### References

- [Source: _bmad-output/planning-artifacts/epics.md#Epic 9: Reproduce and Trust the Existing Prototype]
- [Source: _bmad-output/planning-artifacts/epics.md#Story 9.1: Freeze and Index the v1 Evidence Baseline]
- [Source: _bmad-output/planning-artifacts/epics.md#Stories 9.2-9.8]
- [Source: _bmad-output/planning-artifacts/prd.md#Controlling Consolidated Requirements Inventory — FR30]
- [Source: _bmad-output/planning-artifacts/prd.md#NonFunctional Requirements — NFR26, NFR38-NFR40, NFR48-NFR52]
- [Source: _bmad-output/planning-artifacts/architecture.md#Controlling V2 Architecture Consolidation - 2026-08-22]
- [Source: _bmad-output/planning-artifacts/architecture.md#Authoritative evidence contracts]
- [Source: _bmad-output/planning-artifacts/architecture.md#Scope and simplicity boundary]
- [Source: pyproject.toml]
- [Source: uv.lock]
- [Source: abci/consensus_app/go.mod]
- [Source: abci/consensus_app/go.sum]
- [Source: compose.local.yml]
- [Source: compose.consensus.yml]
- [Source: src/parallel_truth_fingerprint/contracts/dataset_artifact.py]
- [Source: src/parallel_truth_fingerprint/persistence/artifact_store.py]
- [Source: src/parallel_truth_fingerprint/persistence/local_filesystem.py]
- [Source: docs/reference-archive/catalog/checksums.sha256]
- [Git status porcelain format](https://git-scm.com/docs/git-status)
- [Git revision verification](https://git-scm.com/docs/git-rev-parse.html)
- [Python `hashlib`](https://docs.python.org/3/library/hashlib.html)
- [Python `json`](https://docs.python.org/3/library/json.html)
- [Python `os`](https://docs.python.org/3/library/os.html)
- [Docker image inspection](https://docs.docker.com/reference/cli/docker/image/inspect/)
- [Docker image digests](https://docs.docker.com/reference/cli/docker/image/ls/#list-image-digests---digests)

## Mandatory Academic Evidence Amendment

Before implementation, apply the relevant mandatory controls in [Academic Evidence Admission Amendment — 2026-08-31](../planning-artifacts/academic-evidence-admission-amendment-2026-08-31.md). This story must fail closed on an unresolved evidence origin, numeric authority, required mock closure, or prohibited dataset substitution. The amendment adds no activity authorization.
## Dev Agent Record

### Agent Model Used

Codex (GPT-5)

### Debug Log References

- `PYTHONPATH=src .\.venv\Scripts\python.exe -m unittest tests.evidence.test_v1_baseline -v` — 39 tests passed; 1 skipped where local symlink creation is unavailable.
- Safe non-training regression slice (`comparison`, `config`, `consensus`, `dashboard`, `edge_nodes`, `persistence`, `scada`, `scenario_control`, and `sensor_simulation`) — 94 tests passed; 2 environment-dependent tests skipped.
- `PYTHONPATH=src .\.venv\Scripts\python.exe -m compileall -q src scripts/freeze_v1_baseline.py` — passed.
- `PYTHONPATH=src .\.venv\Scripts\python.exe scripts\freeze_v1_baseline.py --help` — passed; no collection or publication was requested.
- Final pragmatic closure: 67 focused Story 9.1 tests passed with 3 environment-dependent symlink skips; 92 safe non-training regression tests, compileall, CLI help, and diff whitespace checks passed.
- Per Emilio's selected pragmatic option, the repository-wide discovery command was replaced by the 94-test non-training regression slice because the omitted suites exercise unrelated model training and are not required to validate this offline inventory boundary.

### Completion Notes List

- Implemented the baseline-specific contract, deterministic offline collector, fail-closed resolver, redacted configuration identity, and no-overwrite manifest-last publisher.
- Corrected review findings: exact MQTT source locator, credential-safe configuration redaction, pinned role/category scientific-status compatibility, and Windows-absolute mutable-pointer rejection.
- The user's decision is recorded as a human bootstrap authorization for local Story 9.1 implementation only; it is not an `ActivityAuthorization.v1` record and did not authorize evidence collection, publication, or scientific activity.
- No project baseline was collected or published. Publication assertions used only disposable unit-test directories.
- Added explicit category/role compatibility, corrupt legacy-pointer JSON classification, and a before/after filesystem snapshot proving collection, validation, and resolution are read-only.
- Completed Task 8 under the user-approved research-prototype rule: focused Story 9.1 coverage plus the safe non-training regression slice is sufficient; production-style exhaustive regression is non-blocking.
- Resolved the full thesis-relevant review set: explicit evidence-root roles, complete runtime/known-absence anchors, exact directory children, separated overlay origins, honest legacy/result classification, safe Compose identity, ancestor-aware secret exclusion, structural validation, and limitation-bearing CLI output.
- Preserved the pragmatic boundary: no network, service startup, training, real baseline collection, or publication occurred.
- Resolved the second adversarial review set: false resolver immutability, repository revalidation, pointer/Compose/Git sanitization, complete result-table coverage, derived-root exclusion, confined output, UTC/digest validation, and origin-safe historical result classification.
- Validation after the second review: 52 focused tests pass with 2 environment-dependent symlink skips; 92 safe non-training regression tests pass; compileall, CLI help, and diff whitespace checks pass. No real baseline was collected or published.
- Resolved the third adversarial review set with redacted pointer/overlay identities, Git fallback and sanitization, origin invariants, honest absence handling, safer publication recovery, and complete CLI limitations.
- Validation after the third review: 63 focused tests pass with 3 environment-dependent symlink skips; 92 safe non-training regression tests pass; compileall, CLI help, and diff whitespace checks pass. No real baseline was collected or published.
- Closed the final four review findings: common credential filenames are excluded, all result-bearing validation/Markdown tables are inventoried, resolution requires exact published manifest bytes, and identical publication reruns are idempotent before repository revalidation.
- Story 9.1 is complete under Emilio's explicit pragmatic closure decision. No further broad adversarial review is required; no real baseline, training, service, network, or experiment activity was executed.

### File List

- `src/parallel_truth_fingerprint/contracts/v1_baseline.py`
- `src/parallel_truth_fingerprint/contracts/__init__.py`
- `src/parallel_truth_fingerprint/evidence/__init__.py`
- `src/parallel_truth_fingerprint/evidence/v1_baseline.py`
- `scripts/freeze_v1_baseline.py`
- `tests/evidence/__init__.py`
- `tests/evidence/test_v1_baseline.py`
- `_bmad-output/implementation-artifacts/9-1-freeze-and-index-the-v1-evidence-baseline.md`
- `_bmad-output/implementation-artifacts/sprint-status.yaml`

## Change Log

- 2026-08-31 — Implemented Story 9.1 within Emilio's local-only authorization; focused isolated tests pass, while the prohibited broad regression command remains pending.
- 2026-08-31 — Addressed the Story 9.1 local review findings and expanded isolated unit coverage; no baseline collection, publication, or external activity occurred.
- 2026-08-31 — Completed pragmatic Task 8 coverage (28 focused + 94 safe regression tests), added corrupt-pointer and category/role enforcement, and moved Story 9.1 to review.
- 2026-08-31 — Addressed all nine thesis-relevant code-review items with 39 focused and 94 safe regression tests; returned Story 9.1 to review.
- 2026-09-01 — Addressed all 12 thesis-relevant findings from the second adversarial review, amended the Story 9.1 origin boundary, and expanded focused coverage to 52 passing tests.
- 2026-09-01 — Addressed all 12 thesis-relevant findings from the third adversarial review and expanded focused coverage to 63 passing tests.
- 2026-09-01 — Closed the final four pragmatic review findings, reached 67 focused passing tests, and marked Story 9.1 done by explicit user decision.
