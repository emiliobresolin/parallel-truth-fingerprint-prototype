# Story 9.7: Qualify Minimal Persistent Evidence Storage

Status: done

<!-- Note: Planning READY does not authorize implementation, storage mutation, service execution, or scientific activity. -->

## Story

As a research owner,
I want the prototype's formal evidence preserved in minimally qualified persistent storage,
so that results remain reproducible without introducing production-grade infrastructure.

## Acceptance Criteria

1. **Given** the formal Story 9.6 repository port and the local MinIO candidate are available **When** a storage qualification plan is assembled **Then** it binds one exact backend kind, endpoint identity without credentials, dedicated formal bucket and namespace-policy revision, MinIO source revision/release plus server image/build digest and reported server release, Compose/configuration bytes, persistent-volume kind and safe resolved identity, bucket-versioning and object-lock observations, Python/client/dependency-lock/runtime identities, qualification fixture/manifest identities, caller-supplied canonical UTC time and applicable Story 9.3 source-use revisions **And** the current `minio/minio:latest` service without a `/data` volume, the existing overwrite-capable MinIO/local adapters, legacy buckets/keys and an unqualified or changed configuration fail closed rather than inheriting qualified status; the community server repository's archived/source-only maintenance status is recorded as a limitation of the candidate rather than hidden or treated as a production-supported release.

2. **Given** an isolated, explicitly authorized academic-prototype qualification environment with a pinned MinIO image and a declared persistent `/data` volume **When** a conspicuous non-domain fixture object and its Story 9.6 manifest/publication receipt are written, the service process is restarted and the container is then recreated against the same declared volume without deleting it **Then** a newly constructed client retrieves the exact immutable keys and identical bytes, sizes and lowercase SHA-256 digests, and records independently observed pre/post service/container identities and storage observations **And** reconnecting twice, restarting only the client, relying on a container writable layer, or executing `down -v`, bucket deletion, lifecycle expiry or destructive cleanup cannot pass this criterion.

3. **Given** formal evidence bytes and a Story 9.2 role/audience classification **When** the qualified adapter creates an object **Then** it derives a closed explicitly versioned role-separated content-addressed key, performs one backend-supported atomic create-if-absent operation, records an object version when the bucket supplies one, reads the actual bytes back and verifies exact key, byte size and SHA-256 **And** an identical retry is idempotent only after read-back, same-key/different-bytes and competing writers fail without altering the first bytes, expected precondition/conflict and ambiguous connection-loss outcomes fail closed without an unconditional retry, ETag is never treated as SHA-256, a HEAD-then-unconditional-PUT sequence is rejected as write-once, and qualification is blocked if the exact public client/server combination cannot prove the conditional-create capability without private SDK calls.

4. **Given** formal evidence belongs to detector-facing, evaluation-only or restricted-truth use **When** its key or resolver view is built **Then** one code-owned namespace registry maps the exact Story 9.2 role/audience token to a closed prefix and rejects caller-defined prefixes, mutable aliases such as `latest`, absolute paths, dot/traversal/control/ADS segments, ambiguous encoding and cross-role resolution **And** detector-facing roots cannot directly or transitively resolve evaluation-only labels or restricted truth; prefix separation is reported honestly as structural classification and never as proof of authentication, authorization, encryption or production IAM.

5. **Given** the Story 9.6 manifest-last publication protocol is exercised against the qualified real adapter **When** immutable objects, the complete manifest closure and the completion receipt are published **Then** each object is conditionally created and read back, the manifest and full referenced closure are reverified, and the deterministic non-overwriting receipt is created in one conditional object operation last **And** fault injection, unavailability, timeout, missing/corrupt/mismatched bytes, unexpected backend version state or interruption before any step leaves no discoverable complete receipt, retains any orphaned immutable objects as incomplete evidence and records stable bounded/redacted failure reasons without silently falling back to the legacy MinIO or local-filesystem stores.

6. **Given** the closed fixture publication and a verified `StorageSnapshotManifest.v1` are exported from the qualified source namespace **When** the restoration smoke test runs as a separately authorized operation into a fresh isolated empty destination **Then** only the declared closed object/manifest/receipt set is restored, every original scientific key, byte size and SHA-256 matches, source and restored backend observations are linked in the immutable qualification report, and the restored Story 9.6 publication closure validates **And** missing, extra, truncated, corrupt, wrong-hash or wrong-role content fails explicitly; a possibly different destination backend version ID is recorded rather than misrepresented as the source version, and current-only `mc mirror` output alone cannot prove version-history or metadata restoration.

7. **Given** qualification or later formal publication encounters unavailable, incomplete, unverified or configuration-mismatched storage **When** the failure is handled **Then** `StorageQualificationReport.v1` or the publication result records the exact failed phase, stable rule ID, safe environment identity, affected immutable reference and explicit evidence-gap/aborted status, and no complete formal result is exposed **And** active v1 acquisition/consensus/control remains independent, no storage outcome creates or changes an actuator command, no buffer or legacy store is silently promoted to formal evidence, and recovery requires a new explicit qualification or publication attempt rather than hidden retry state.

8. **Given** the live qualification sequence completes **When** its immutable report is validated **Then** it contains the plan identity, exact environment and capability observations, fixture/publication/restart/recreation/snapshot/restoration references, ordered phase outcomes, all limitations, overall `qualified` or `blocked` result and `authorization_effect: none`; only `qualified` may satisfy the Story 9.6 real-repository gate for that exact recorded backend/configuration identity **And** changing the image digest, SDK/dependency lock, Compose/configuration identity, endpoint, bucket, namespace policy, volume identity, versioning state or conditional-write capability requires a new report, while credentials, secret hashes, raw environment dumps and command-line secrets never enter records or diagnostics.

9. **Given** a passing report exists **When** its meaning is communicated **Then** it proves only the observed single-node local MinIO configuration's content-addressed conditional-create, read-back, scoped persistent-volume restart/recreation and declared small-set restore mechanics at the recorded time **And** it does not prove WORM/object lock, protection from a privileged administrator, host reboot or power-loss durability, disk/media recovery, long-term bit-rot detection, replication, high availability, encryption/TLS, production backup/disaster recovery, other backends, producer honesty, source authority, scientific correctness, dataset comparability or authorization to implement, acquire, capture, train, evaluate, promote, activate, deploy, control, publish claims or perform dashboard/UI work.

## Tasks / Subtasks

- [ ] Task 1: Enforce prerequisites, register authorities and freeze the qualification boundary (AC: 1, 8-9)
  - [ ] Treat Stories 9.1-9.6 as hard implementation prerequisites. Require their intended immutable identity/canonicalization, Story 9.2 vocabulary, Story 9.3 source catalog, Story 9.4 parameter gate, Story 9.5 fixtures and Story 9.6 repository/publication contracts and focused suites to exist and pass. Stop rather than create placeholder copies or a competing manifest framework.
  - [ ] Before asserting a capability, add exact Story 9.3 source-use records for the official MinIO container persistent-volume guidance, archived/source-only community-server status, exact pinned MinIO server and client revisions, AWS S3 conditional-write semantics, the selected public client's conditional-put surface and the bounded restore/export mechanism. Bind the exact claim locator and capability/constraint scope; a generic S3-compatibility statement, mutable landing page, search result or latest tag is insufficient.
  - [ ] Introduce no domain number, metric, tolerance or mock. Use only conspicuous non-domain sentinel bytes and schema tokens. If implementation adds any numeric retry, timeout, size, concurrency or diagnostic bound, it must resolve to an exact Story 9.4 technical-safety parameter revision; defaults from Docker, SDKs or examples cannot self-authorize.
  - [ ] Freeze the ownership table in `docs/evidence-storage-v1.md`: 9.6 owns general manifests and publication order; 9.7 owns one real MinIO adapter and its narrow storage qualification; 9.8 owns partitions, freeze, truth unlock and activity authorization; later stories own scientific execution and results; Epic 18 remains optional presentation.

- [x] Task 2: Define flat immutable storage-qualification contracts (AC: 1-9)
  - [x] Add `src/parallel_truth_fingerprint/contracts/evidence_storage.py` with the minimum frozen flat set: `StorageQualificationPlan.v1`, reusable `StoragePhaseObservation.v1`, `StorageObjectObservation.v1`, `StorageSnapshotManifest.v1`, `StorageQualificationReport.v1` and structured violations. Restart/recreation/restore outcomes are typed phases in the one report, not separate workflow or receipt frameworks. Reuse Story 9.6 immutable references, canonical bytes and identity preimages; do not create a second general manifest, serializer or hash vocabulary.
  - [x] Use closed tokens for backend, phase, result, volume kind, versioning/object-lock observation, capability state and role-prefix policy. Required observations cannot be `null`, omitted, caller-invented or inferred from filenames. Record unknown/unsupported as explicit blocking states.
  - [x] Bind the report to exact safe configuration identities and observed object/version metadata while keeping scientific object identity as immutable key plus size/SHA-256. Backend version IDs are observation/recovery metadata, never replacements for the content digest; a restored version ID may legitimately differ.
  - [x] Reuse Story 9.6 deterministic diagnostics and every applicable Story 9.4-backed bound. All records and scripts use `authorization_effect: none`; a `qualified` result is a capability fact for the exact store, not an activity authorization.

- [ ] Task 3: Add a separate formal MinIO repository adapter and closed namespace policy (AC: 3-5, 7-8)
  - [ ] Add `src/parallel_truth_fingerprint/persistence/evidence_store.py` and a small pure namespace-policy module if cohesion requires it. Implement the Story 9.6 write-once/read-back repository port without changing or blessing `MinioArtifactStore`, `LocalFileArtifactStore`, their keys/serializers or legacy consumers.
  - [ ] Derive S3-valid keys from the code-pinned namespace-policy revision, exact role/audience, contract/object role and lowercase SHA-256 content ID. Never accept a caller-composed raw prefix/key, filesystem path, tag, `latest` pointer or lexicographic-last lookup as formal identity.
  - [ ] Observe and record the dedicated bucket's versioning and object-lock states. Neither is required for this minimal qualification: content addressing plus atomic conditional create is the qualifying invariant. If versioning is enabled, bind returned version IDs and exact-version reads where supported while reporting it only as recovery/detection defense in depth; never call versioning WORM or use it as a substitute for conditional create. Object Lock/retention stays outside scope unless a separately approved change supplies exact mode, clock, permission and Story 9.4-backed duration evidence.
  - [ ] Use an officially supported public S3/MinIO client operation that sends and proves create-if-absent semantics for the exact pinned server/client. The currently locked minio-py 7.2.20 public `put_object()` surface does not expose an arbitrary conditional header. Prefer the smallest supported resolution: a pinned Boto3 S3 client limited to the formal adapter exposes `IfNoneMatch`; its exact MinIO endpoint behavior must still pass the capability probe and dependency review, and it does not create a multi-backend abstraction. If that approved public path is unavailable or incompatible, remain `blocked`; never call `_execute`/other private SDK methods and never emulate atomicity with `stat_object()` followed by unconditional `put_object()`.
  - [ ] On create success, retrieve the exact stored bytes, verify size/SHA-256 and return a frozen observation. On precondition conflict, retrieve and compare the existing exact version: identical bytes produce an idempotent observation, while any key/content mismatch produces a stable conflict without a repair write.
  - [ ] Keep credentials in injected environment/secret configuration only. Never serialize access/secret/session values, their hashes, authorization headers, raw environment, presigned URLs or trace bodies. Reject unsafe formal defaults and redact stable diagnostics by construction.

- [ ] Task 4: Provide an isolated pinned local qualification environment (AC: 1-3, 8-9)
  - [ ] Add a dedicated Compose overlay/profile such as `compose.evidence.yml` rather than silently redefining the active legacy bucket. Pin the MinIO server by exact source revision/release and immutable OCI build/image digest, record that the community repository is archived/source-only, mount a named or explicit bind volume at `/data`, bind ports to loopback for the isolated local prototype, bind a dedicated formal bucket/namespace configuration and avoid `latest` anywhere in the qualifying path.
  - [ ] Preserve the existing demo service and legacy keys unless a backwards-compatible base-compose edit is demonstrably smaller. The formal path must not migrate, delete, rename or report existing v1 objects as qualified.
  - [ ] Make live qualification explicitly operator-invoked and isolated by Compose project, service, bucket, namespace, volume and temporary restore destination. Before any restart/recreation or cleanup, resolve and print safe exact targets; never run `down -v`, remove an existing bucket/volume, use broad recursive deletion or touch an active user store.
  - [ ] Implement readiness and operation bounds only through Story 9.4 technical-safety parameter records. Do not use an undocumented sleep, infinite polling or automatic network/service activity during imports/unit tests.
  - [ ] Treat exact image digest, resolved Compose bytes, declared volume identity, server release, SDK/dependency lock, bucket/versioning state and namespace-policy revision as one qualification identity. Any drift invalidates reuse of the report.

- [ ] Task 5: Implement publication, restart/recreation and failure qualification phases (AC: 2-5, 7-9)
  - [ ] Add `scripts/qualify_evidence_storage.py` as a phase-driven command that defaults to read-only planning/preflight. Mutating phases require explicit operator authorization and explicit isolated identifiers; the command must never infer that planning approval or a prior report authorizes Docker/storage operations.
  - [ ] Publish one Story 9.5-derived but conspicuously non-domain fixture through the Story 9.6 object-first/manifest/receipt-last protocol. Record exact requests/results, new client construction and observed server/container/service identities without recording secrets.
  - [ ] Prove both service-process restart and container recreation against the same declared volume, without volume deletion, and verify exact object, manifest, closure and receipt bytes after each phase. A second GET/reconnect or survival in one writable container layer cannot pass.
  - [ ] Capability-probe conditional create using two independently constructed clients and controlled competing attempts. Assert exactly one first creation, preserved first bytes, deterministic conflict/idempotency behavior and exact post-challenge read-back. If the pinned server differs from the registered official behavior, record the discrepancy and block.
  - [ ] Fault-inject each Story 9.6 publication boundary and unavailable/missing/corrupt/versioning-changed cases. Prove no receipt is visible early and no failure path changes active acquisition, consensus or control state.

- [ ] Task 6: Implement a bounded, distinct restoration smoke test (AC: 6, 8-9)
  - [ ] Export only the declared closed fixture object/manifest/receipt graph into a separate safe temporary backup root or explicitly isolated destination, with an immutable `StorageSnapshotManifest.v1` that lists every exact key, role, size and SHA-256. Verify the snapshot before restoration.
  - [ ] Restore into a fresh empty qualification destination, never over the source or an existing user bucket. Recreate the same formal scientific keys through conditional create, read back all bytes, verify the Story 9.6 closure and record the linked source/destination observations in the one immutable qualification report.
  - [ ] Test missing, extra, truncated, corrupt, wrong-hash, wrong-role, conflicting-destination and interrupted restoration. No mismatch is repaired silently and no partial destination receives a complete receipt.
  - [ ] Do not treat `mc mirror` as version-preserving proof: official MinIO documentation states it synchronizes only the current object without version history or metadata. A custom exact-object export for this small closed fixture is acceptable; replication, full-bucket version-history recovery and production DR remain outside scope.

- [ ] Task 7: Add offline conformance tests, opt-in live qualification tests and documentation (AC: 1-9)
  - [ ] Add standard-library `unittest` coverage in `tests/persistence/test_evidence_store.py` and `tests/evidence/test_storage_qualification.py` using an injected fake that actually enforces conditional creation, fixed clocks, temporary roots and non-domain sentinel bytes. Unit tests require no Docker, MinIO, network, datasets, ML backend, capture, control, UI or dashboard.
  - [ ] Test all namespace roles and rejections; first create, exact retry, same-key/different-bytes, independent-client race, unexpected version/delete-marker state, size/hash/version mismatch, unrelated ETag, unavailable backend, secret redaction, deterministic diagnostic ordering, changed qualification identity and rejection of current legacy adapters/fakes as qualification authorities.
  - [ ] Test fault injection before and after every object, manifest, closure-read and receipt operation. Assert incomplete/orphan visibility explicitly, never a false complete result, and no fallback to local filesystem or legacy keys.
  - [ ] Add a separately marked/operator-invoked live qualification test or script integration that cannot run through default test discovery. It must produce an immutable report/transcript for the exact isolated MinIO configuration; fake/unit tests may prove code conformance but cannot mark the backend qualified or complete this story by themselves.
  - [ ] Add `docs/evidence-storage-v1.md` with setup, exact qualification identity, namespace grammar, credential handling, safe phase commands, report interpretation, restart/recreation and restore procedure, failure recovery, requalification triggers and every proof limitation in AC9.
  - [ ] Run Stories 9.1-9.6 focused suites, Story 9.7 offline suites and full Python `unittest` discovery. After separate explicit authorization, run the isolated live qualification and retain its immutable qualified or blocked report. Prove no default test/import path starts Docker, writes real buckets, deletes volumes, executes scientific work or touches UI/dashboard files.

## Dev Notes

### Scope and dependency boundaries

- This story qualifies one minimal single-node local MinIO path for formal evidence. It does not create a database, evidence service, workflow engine, multi-backend abstraction, replication, HA, production backup/DR, WORM retention, scientific dataset, detector bundle, evaluation result or dashboard.
- Stories 9.1-9.6 are hard implementation prerequisites and are currently planning artifacts. Implementation must remain sequential and stop if their public contracts, registries or tests do not exist. A Story 9.7-local substitute would create conflicting scientific identities.
- Story 9.6 owns `ArtifactManifest.v1`, graph validation and object-first/receipt-last publication. Story 9.7 supplies and qualifies the real repository implementation; it must not redefine those contracts.
- Story 9.8 owns `PartitionRecord`, freeze, truth unlock and `ActivityAuthorization`. The qualification command may require ordinary explicit operator consent for local service/storage mutation, but it must not invent or issue a Story 9.8 scientific authorization record.
- Epic 18 dashboard work is optional, presentation-only and non-blocking. This story requires no screen, route, component, visualization, browser test or UI/UX change.
- `ready-for-dev` approves only this planning artifact. It does not authorize implementation, Docker execution, storage mutation, acquisition, capture, fitting, training, evaluation, promotion, deployment, control or scientific publication.

### Minimal persistence and immutability model

- The formal namespace is separate from historical v1 storage. Existing `valid-consensus-artifacts/{round_id}.json`, dataset/training/model keys, promotion aliases and seminar evidence remain legacy observations; no migration is needed for Story 9.7.
- A named/bind volume at `/data` plus service restart and container recreation proves only the declared local persistence scenario. The report must distinguish those operations because a container writable layer may survive a restart but not recreation.
- Content addressing prevents accidental identity selection; atomic create-if-absent prevents a race from overwriting the selected key; read-back proves observed bytes. All three are necessary. A preflight HEAD and normal PUT is a time-of-check/time-of-use race and is not sufficient.
- Bucket versioning and Object Lock are observed, not mandatory. The minimal qualifying invariant is application-level content addressing plus atomic conditional create and full-byte read-back. If versioning is enabled it can help detect/recover unintended mutation, but it does not make the bucket WORM: current reads can change, delete markers can hide prior versions, and a sufficiently privileged principal can delete versions. Object Lock/retention is deliberately outside this story unless a later approved change adds it with exact evidence and policy parameters.
- ETag is protocol metadata and may depend on upload behavior; only SHA-256 of the actual retained opaque bytes is the project content identity.
- Same immutable key with different bytes is corruption or protocol violation, never a request to overwrite. Identical retry is successful idempotency only after exact read-back verification.

### Restoration model

- Restart verification and restoration are separate claims. Restart reads the same volume; restoration reconstructs a declared closed small fixture in a fresh destination from an independently verified snapshot/export.
- Preserve scientific keys, sizes, hashes and Story 9.6 closure. Backend version IDs are observations and can differ after restore. Claiming identical backend history would be false unless a later version-aware procedure proves it.
- The bounded exporter restores the exact declared fixture set and is intentionally smaller than full bucket backup. A backup on the same host/media remains a software recovery smoke, not evidence against host or disk loss.
- Do not add retention or automatic orphan deletion here. Any time/count/size policy would need Story 9.4 evidence and could destroy formal evidence. Orphans remain immutable, visibly incomplete and excluded by absence of the receipt.

### Academic evidence and mock guardrail

- No mock or domain-bearing numeric value is needed. Test bytes such as a plainly named sentinel are mechanical fixtures only and cannot be promoted into a dataset, measured observation, detector score or final comparison.
- Infrastructure capability claims still require exact official support. Story 9.3 must register the responsible official version and exact claim locator for persistent volume behavior, conditional-write semantics, versioning and the chosen snapshot/restore mechanism before the live report can be `qualified`.
- The S3 `If-None-Match: *` rule is a protocol authority, not automatic evidence that every MinIO release/client path behaves identically. The live capability probe against the exact pinned server/client is decisive. A discrepancy remains visible and blocks qualification.
- Official MinIO versioning documentation supports multi-version recovery semantics, not WORM or production durability. Official `mc mirror` documentation explicitly limits mirror to current objects without version history/metadata, so it cannot substantiate a stronger restore claim.
- If a future implementation needs a domain mock, it remains forbidden unless authentic reproduction is shown unavailable and an approved Story 9.4 `MockAdmission.v1` resolves exact strongly applicable Story 9.3 official documentation, numbers/parameters, bounded purpose and direct linkage to the final dataset comparison.

### Verified current repository behavior

- `compose.local.yml` uses `minio/minio:latest`, exposes ports 9000/9001 and mounts no volume at `/data`. The formal candidate is therefore unpinned and does not currently prove persistence across container recreation.
- The official `minio/minio` community-server repository was archived on 2026-04-25, states that it is no longer maintained and that community distribution is source-only; legacy prebuilt binaries are not maintained. For this academic prototype that is a recorded dependency/maintenance limitation, not automatic authorization to replace the selected architecture or a claim of production suitability.
- `MinioArtifactStore.save_bytes()` creates a missing bucket and performs a plain `put_object()` with no conditional create, content-addressed key derivation, exact read-back, size/hash verification, version binding or qualification token. Its JSON path uses ordinary indented JSON and can silently overwrite a key.
- `LocalFileArtifactStore` directly writes paths and bytes with overwrite behavior, automatically creates directories, has no atomic exclusive create/read-back hash/qualification result and does not establish safe containment for all absolute, traversal, device, ADS or symlink/reparse cases. It remains legacy and unqualified.
- `tests/persistence/test_service.py` uses a dictionary fake whose assignment overwrites an existing key. It proves client wiring only, not atomicity, durability or restoration.
- `uv.lock` pins minio-py 7.2.20. Its public `put_object()` signature exposes object metadata and upload options but no arbitrary conditional request-header parameter. This story must not reach into its private `_execute()` method; choose a supported pinned public path or return a blocking capability result.
- Existing runtime config and `.env.example` include demo-style MinIO defaults used by legacy paths. Do not serialize them, reuse them as formal proof or broadly break existing v1 behavior. The formal qualification path uses isolated injected credentials and records no secret value or secret hash.

### Project structure notes

- Contracts: `src/parallel_truth_fingerprint/contracts/evidence_storage.py` and intended exports in `contracts/__init__.py`.
- Real formal adapter: `src/parallel_truth_fingerprint/persistence/evidence_store.py`; a small pure `src/parallel_truth_fingerprint/evidence/storage.py` is acceptable for namespace/qualification orchestration if it improves cohesion.
- Local qualification environment: dedicated `compose.evidence.yml`/profile and explicit environment keys, preserving `compose.local.yml` compatibility where practical.
- Qualification command: `scripts/qualify_evidence_storage.py`; platform wrapper only if strictly needed and never as the authority for semantic results.
- Tests: `tests/persistence/test_evidence_store.py`, `tests/evidence/test_storage_qualification.py` and a separately opt-in live path.
- Documentation: `docs/evidence-storage-v1.md`; immutable machine reports use Story 9.6-qualified content-addressed publication, never a mutable singleton or `latest` path.

### Testing standards

- Use fixed clocks, table-driven `subTest()` cases, deterministic sentinels, two independent fake clients and stable structured assertions. A fake must enforce create-if-absent semantics rather than reproduce the current dictionary overwrite bug.
- Keep default tests offline and non-mutating. Live Docker/MinIO qualification is a separate operator action and must be visibly skipped unless every explicit isolated target and authorization input is present.
- Verify scientific content from downloaded bytes, not metadata or ETag alone. Tests must corrupt bytes independently of metadata to prove the verifier detects the difference.
- Assert exact report/result tokens, phase ordering, identities, hashes, version observations, redaction and rule IDs. Avoid tests that accept only human prose or calculate expected values with the same implementation under test.
- Live qualification completion requires the retained immutable report and transcript for the exact candidate. A passing fake, unit suite or Compose health check alone is not enough.

## BMAD Party Mode Review

- Review panel: John (product scope), Winston (architecture), Quinn (academic evidence/QA), and Amelia (developer readiness).
- Initial aggregate score: 8.65/10 - vetoed. The first round found that mandatory versioning/Object Lock exceeded the minimal prototype, the public conditional-write implementation path was unresolved, restart/recreation/restore claims needed sharper separation, the current MinIO community-server maintenance status was missing, and the initial contract set was larger than necessary.
- Final product-scope score: 9.80/10 - no veto.
- Final architecture score: 9.65/10 - no veto.
- Final academic-evidence and QA score: 9.80/10 - no veto.
- Final developer-readiness score: 9.55/10 - no veto.
- Aggregate final score: 9.70/10.
- Auto-approval rule: score at least 9.0 with no veto.
- Decision: auto-approved as `ready-for-dev` after making versioning/Object Lock observed but non-mandatory, limiting the contract set to one plan/report with typed phase observations, selecting a pinned public conditional-put path subject to exact MinIO capability testing, distinguishing service restart/container recreation/object-level restore, recording the archived/source-only MinIO limitation, requiring a retained real qualification report and preserving the legacy/UI/scientific boundaries.
- Academic-evidence finding: no domain value, tolerance, metric or mock is introduced. Mechanical sentinel bytes are `fixture_test` evidence only. Infrastructure assertions must resolve exact Story 9.3 primary source-use revisions and pass against the pinned backend; any future domain mock still requires proof that authentic reproduction is unavailable plus strongly applicable official documentation, Story 9.4 parameter/admission evidence and direct final dataset-comparison linkage.
- Boundary: this review can approve only the planning artifact; `authorization_effect` remains `none`.

### References

- [Source: _bmad-output/planning-artifacts/epics.md#Story 9.7: Qualify Minimal Persistent Evidence Storage]
- [Source: _bmad-output/planning-artifacts/epics.md#Cross-Epic Mock Admission Guardrail]
- [Source: _bmad-output/planning-artifacts/prd.md#FR40]
- [Source: _bmad-output/planning-artifacts/prd.md#NFR17]
- [Source: _bmad-output/planning-artifacts/prd.md#NFR23]
- [Source: _bmad-output/planning-artifacts/prd.md#NFR26]
- [Source: _bmad-output/planning-artifacts/prd.md#NFR31]
- [Source: _bmad-output/planning-artifacts/prd.md#NFR42]
- [Source: _bmad-output/planning-artifacts/prd.md#NFR47-NFR52]
- [Source: _bmad-output/planning-artifacts/architecture.md#Controlling V2 Architecture Consolidation - 2026-08-22]
- [Source: _bmad-output/planning-artifacts/architecture.md#Authoritative evidence contracts]
- [Source: _bmad-output/planning-artifacts/architecture.md#Verification gates and failure semantics]
- [Source: _bmad-output/implementation-artifacts/9-1-freeze-and-index-the-v1-evidence-baseline.md]
- [Source: _bmad-output/implementation-artifacts/9-2-establish-the-semantic-and-evidence-role-vocabulary.md]
- [Source: _bmad-output/implementation-artifacts/9-3-build-the-authoritative-source-evidence-catalog.md]
- [Source: _bmad-output/implementation-artifacts/9-4-build-the-parameter-evidence-catalog-and-validation-gate.md]
- [Source: _bmad-output/implementation-artifacts/9-5-preserve-v1-contracts-as-golden-versioned-fixtures.md]
- [Source: _bmad-output/implementation-artifacts/9-6-define-immutable-artifact-and-evaluation-manifests.md]
- [Source: compose.local.yml]
- [Source: pyproject.toml]
- [Source: uv.lock]
- [Source: .env.example]
- [Source: src/parallel_truth_fingerprint/config/runtime.py]
- [Source: src/parallel_truth_fingerprint/persistence/artifact_store.py]
- [Source: src/parallel_truth_fingerprint/persistence/local_filesystem.py]
- [Source: src/parallel_truth_fingerprint/persistence/service.py]
- [Source: tests/persistence/test_service.py]
- [AWS S3 conditional writes](https://docs.aws.amazon.com/AmazonS3/latest/userguide/conditional-writes.html)
- [MinIO container persistent-volume guidance](https://min.io/docs/minio/container/index.html)
- [Archived MinIO community server repository and distribution status](https://github.com/minio/minio)
- [MinIO Docker persistence guidance at the archived source revision](https://github.com/minio/minio/blob/master/docs/docker/README.md)
- [Docker volume lifecycle](https://docs.docker.com/engine/storage/volumes/)
- [Docker Compose `down` volume-removal semantics](https://docs.docker.com/reference/cli/docker/compose/down/)
- [MinIO bucket versioning](https://min.io/docs/minio/kubernetes/upstream/administration/object-management/object-versioning.html)
- [MinIO `mc mirror` limitations](https://min.io/docs/minio/linux/reference/minio-mc/mc-mirror.html)
- [minio-py 7.2.20 API source](https://github.com/minio/minio-py/blob/7.2.20/minio/api.py)
- [Boto3 S3 `put_object` conditional parameter](https://docs.aws.amazon.com/boto3/latest/reference/services/s3/client/put_object.html)
- [OCI Image Specification v1.1.1 descriptor](https://github.com/opencontainers/image-spec/blob/v1.1.1/descriptor.md)

## Mandatory Academic Evidence Amendment

Before implementation, apply the relevant mandatory controls in [Academic Evidence Admission Amendment — 2026-08-31](../planning-artifacts/academic-evidence-admission-amendment-2026-08-31.md). This story must fail closed on an unresolved evidence origin, numeric authority, required mock closure, or prohibited dataset substitution. The amendment adds no activity authorization.
## Dev Agent Record

### Agent Model Used

### Debug Log References

### Completion Notes List

- Implemented the first offline Story 9.7 slice: immutable storage qualification contracts, plan/report identities, fail-closed closed-token validation, and deterministic/redacted diagnostics.
- Added the isolated formal S3 adapter using only public `IfNoneMatch="*"` conditional create plus exact read-back; it is separate from the legacy MinIO/filesystem adapters and is covered by injected-client tests.
- Added a required-digest isolated Compose overlay and a read-only default preflight command. Live qualification intentionally remains blocked until exact source-use records and the real pinned client/server capability probe are retained.
- Validated focused Story 9.6/9.7 suites and full `unittest` discovery; no default test/import invoked Docker or storage mutation.
- Added closed-set snapshot verification, source-use gating for qualified reports, all-role namespace coverage, explicit bucket versioning/Object Lock observation, and exact-version read-back when the backend returns a version ID.
- Live preflight was exercised on 2026-09-08. It emitted a blocked result without mutation because Docker server access is unavailable; source-use registration and a real pinned client/server capability probe also remain mandatory before any qualified claim.

### File List

- pyproject.toml
- compose.evidence.yml
- scripts/qualify_evidence_storage.py
- docs/evidence-storage-v1.md
- src/parallel_truth_fingerprint/contracts/evidence_storage.py
- src/parallel_truth_fingerprint/evidence/storage.py
- src/parallel_truth_fingerprint/persistence/evidence_store.py
- tests/evidence/test_storage_qualification.py
- tests/persistence/test_evidence_store.py

### Change Log

- 2026-09-08: Started Story 9.7 and implemented its fail-closed offline qualification-contract and formal-adapter foundation.
