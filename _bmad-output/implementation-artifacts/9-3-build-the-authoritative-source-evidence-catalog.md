# Story 9.3: Build the Authoritative Source-Evidence Catalog

Status: done

<!-- Note: Validation is optional. Run validate-create-story for quality check before dev-story. -->

## Story

As a research owner,
I want a versioned catalog of every scientific, technical, dataset, profile, and protocol source,
so that each adopted claim or parameter can be traced to an exact authoritative location and scope.

## Acceptance Criteria

1. **Given** an existing or proposed project source **When** a source record is created **Then** it receives a stable source ID and records its organization or authors, title, publication or release date, exact version/edition, source type, official URL or repository, retrieval status, and local locator where applicable **And** the record identifies whether the source is primary, authoritative, peer-reviewed, vendor documentation, a standard, a dataset source, or a secondary reference.

2. **Given** source bytes are available locally **When** they are registered **Then** the record contains the exact filename, byte size, SHA-256 digest, retrieval date, and storage or archive locator **And** a content change creates a new immutable source identity rather than silently changing the existing record.

3. **Given** a source is paywalled, access-controlled, not yet acquired, or available only through an official landing page **When** it is catalogued **Then** its status and access limitation are explicit **And** the system does not fabricate local bytes, file sizes, hashes, license rights, or a completed acquisition state.

4. **Given** a project claim, profile fact, protocol rule, or externally sourced number **When** it references the catalog **Then** it identifies the source ID and an exact page, section, table, figure, field, commit, file, or other stable locator **And** the source record states the applicable claim scope and does not imply that unrelated values in the same document are transferable.

5. **Given** an externally asserted domain number cannot be measured or derived by the approved prototype **When** its source and intended use are validated **Then** the number resolves to applicable official documentation from the responsible standards body, manufacturer, protocol owner, or dataset owner and records the exact prototype component, bounded research question, evidence track, and final package element it affects **And** a scholarly or secondary reference may provide context but cannot be promoted into official direct-parameter evidence or substitute for missing transferability.

6. **Given** a dataset or vendor source has license, citation, notice, access, or redistribution restrictions **When** the source record is validated **Then** those restrictions and the permitted project use are preserved **And** restricted or large source data remains outside Git while its catalog metadata and checksums remain versionable.

7. **Given** two records refer to mirrors, aliases, or copies of the same source **When** catalog normalization runs **Then** the canonical source and each retrieval location remain identifiable without merging different versions or byte streams **And** conflicting versions, counts, or hashes are preserved as an explicit discrepancy rather than automatically resolved.

8. **Given** the source catalog is serialized or exported **When** the same validated records are processed repeatedly **Then** ordering and canonical representation are deterministic **And** malformed records, duplicate stable IDs, missing required locators, or invalid digests fail validation with actionable diagnostics.

9. **Given** the catalog identifies a source as suitable for future use **When** the catalog is finalized **Then** it records evidence and limitations only **And** catalog inclusion does not authorize downloading datasets, implementation, training, capture, experiments, or feature activation.

## Tasks / Subtasks

- [x] Task 1: Define the flat, versioned source-catalog contracts and identity model (AC: 1-3, 7-9)
  - [x] Add `src/parallel_truth_fingerprint/contracts/source_catalog.py` with explicit `SourceCatalog.v1` schema/version identity, frozen dataclasses, explicit `StrEnum` values, and deterministic `to_dict()` methods. Re-export only the intended public types from `contracts/__init__.py`.
  - [x] Keep the records flat and joined by stable IDs: `source_id` preserves the current logical compatibility identity; `source_revision_id` identifies one exact edition/release/full repository commit; `content_id` identifies one observed byte stream; and `retrieval_id` identifies one retrieval location/observation. Keep bounded-use and discrepancy records separate. Do not add a second family-ID layer, RDF, a database, or a registry service.
  - [x] Preserve all current catalog `source_id` values. If an existing source has no exact immutable version, retain its logical ID with an explicit `unknown_legacy`, `not_stated`, or mutable limitation; do not guess a version or break downstream references.
  - [x] Require a new `source_revision_id` and, for changed bytes, a new `content_id` whenever a bound version or local byte stream changes. Never overwrite a prior digest, version, retrieval observation, or source-use record. The new revision/content identity satisfies the immutable-identity requirement while `source_id` remains stable for compatibility.
  - [x] Separate `source_type`, issuer/owner role, authority role, peer-review status, retrieval/copy role, retrieval status, access status, rights/license status, redistribution status, and scientific evidence role. `official`, `primary`, `authoritative`, `peer_reviewed`, `author_copy`, and `publicly_accessible` are not synonyms.
  - [x] Pin the v1 serialized tokens. At minimum: `source_type` = `standard`, `official_specification`, `vendor_manual`, `dataset_release`, `dataset_manual`, `government_guidance`, `scholarly_paper`, `tool_documentation`, or `secondary_reference`; `classifications` is a sorted unique tuple drawn from `primary`, `authoritative`, `vendor_documentation`, `standard`, `dataset_source`, or `secondary_reference`; `issuer_role` = `standards_body`, `protocol_owner`, `government`, `manufacturer`, `dataset_owner`, `tool_owner`, `original_authors`, `publisher`, or `mirror_operator`; `authority_role` = `responsible_official`, `authoritative_for_scope`, `primary_context`, `contextual_only`, or `secondary_only`; `peer_review_status` = `peer_reviewed`, `not_peer_reviewed`, `unknown`, or `not_applicable`; `copy_role` = `official_copy`, `publisher_copy`, `author_copy`, `mirror_copy`, or `local_verification_copy`; `retrieval_status` = `local`, `link_only`, `restricted`, `pending`, or `unavailable`; `verification_status` = `verified`, `unverified`, `failed`, or `not_applicable`; `access_status` = `public`, `restricted`, `paywalled`, `pending`, `unavailable`, or `unknown`; `rights_status` = `declared`, `unknown`, `not_stated`, or `not_applicable`; `redistribution_status` = `allowed`, `prohibited`, `restricted`, or `unknown`; date-status = `known`, `unknown_legacy`, `not_stated`, or `not_applicable`; `claim_use` = `direct_value`, `capability`, `constraint`, `derivation_method`, `protocol_rule`, `dataset_identity`, `dataset_semantics`, `published_result`, `model_precedent`, or `contextual_only`; and source-use status = `located`, `unresolved`, `contextual_only`, or `inapplicable`. Peer review appears only in `peer_review_status`, and copy provenance only in `copy_role`/relations. Additions or meaning changes require a catalog schema-version change.
  - [x] Represent publication/release and retrieval dates as nullable ISO-8601 values plus their explicit date-status fields. A null date with `unknown_legacy`/`not_stated` requires a limitation; never mix a status token into a date field.
  - [x] Set `authorization_effect` to the closed value `none`; no catalog record or successful validation result may carry an activity authorization.

- [x] Task 2: Implement deterministic, structured, fail-closed validation (AC: 1-9)
  - [x] Add `src/parallel_truth_fingerprint/evidence/source_catalog.py`, reusing the package and semantic vocabulary established by Stories 9.1/9.2. Do not duplicate their canonicalization, evidence-role, scientific-status, or generic manifest concepts.
  - [x] Return a frozen validation result with stable rule IDs, field paths, offending IDs/tokens, and actionable explanations. At minimum cover unsupported schema/version, duplicate IDs, a source claiming immutable/qualified use without an exact version, mutated immutable identity, invalid digest, missing/mismatched local bytes, incomplete local metadata, fabricated local metadata, missing/unsafe/mutable locator, inapplicable scope, missing responsible authority, contextual source promoted as direct authority, unresolved rights used for redistribution, and unrecorded mirror conflict.
  - [x] Permit explicit `unknown_legacy`/`not_stated` metadata to remain structurally valid catalog evidence with a limitation, but reject that record from a qualified `SourceUse` or responsible direct-authority claim until the exact required fact is resolved.
  - [x] Store machine local locators relative to the supplied `documents/` root and reject empty paths, absolute paths, `..`, traversal, symlink/junction escape, or access outside that root. Only the legacy `checksums.sha256` projection may emit `../documents/...` because it is located in `catalog/`; translate that projection explicitly rather than feeding it back as a machine locator. Hash files as opaque binary streams and never deserialize or execute source content.
  - [x] Treat `main`, `master`, `latest`, repository roots, and living pages as mutable retrieval locations unless a release, edition, immutable URL, full commit, or verified local byte identity is also bound. A landing page may establish owner identity without becoming immutable content evidence.
  - [x] Keep metadata validation independent from optional local-byte verification. A checkout that lacks ignored PDFs may validate record structure but cannot report a `local` record's bytes as verified; G1 remains fail-closed for that local-copy claim until the declared archive is supplied and checked.
  - [x] Permit a restricted/paywalled source to remain byte-absent when it records the exact official landing page and edition, access limitation, lawful verification observation, verifier/date, and exact clause locator. A landing page alone never proves clause content or a direct number, and no local bytes, size, hash, or rights may be fabricated.
  - [x] Perform no network access, redirects, downloads, repository fetches, source scraping, claim extraction, license inference, or automatic metadata repair.

- [x] Task 3: Migrate the existing archive into one machine-readable authority (AC: 1-3, 6-8)
  - [x] Add `docs/reference-archive/catalog/source-catalog.v1.json` and explicitly migrate every current row from `catalog/index.md`; preserve the current source IDs, category meaning, status, URL, use statement, and every known limitation.
  - [x] Bind each current local record to its exact archived filename, byte size, SHA-256, local locator, and evidenced retrieval date. When a historical per-file date is unavailable, record `unknown_legacy` plus a limitation; never infer it from filesystem timestamps or the register's global baseline date.
  - [x] Preserve the current verified planning baseline as migration evidence, not a hard-coded shortcut: 64 unique source rows; 34 local content records; 34/34 registered local hashes valid; 23 link-only rows, 6 restricted rows, and 1 pending row. Recompute all identities during implementation and fail on unexplained drift.
  - [x] Register the newly adopted Story 9.3 technical sources without changing the historical 64-row baseline: `tool-python-314-hashlib`, `tool-python-314-json`, and `tool-python-314-dataclasses` as official Python 3.14 documentation observations (observed as 3.14.7 on 2026-08-22) with exact page, link-only status, and living-page limitation; and `std-spdx-301-licensing-profile` for the SPDX 3.0.1 Licensing Profile's `hasDeclaredLicense`, `hasConcludedLicense`, and missing-versus-`NoAssertionLicense` sections. All have bounded implementation-guidance scope and `authorization_effect: none`.
  - [x] Make `source-catalog.v1.json` the machine authority. Keep `index.md` as its deterministic human-readable projection and `checksums.sha256` as a deterministic compatibility/checksum projection; the three files must not become independent competing sources of truth.
  - [x] Update `docs/reference-archive/README.md` to explain the machine authority, projection/check mode, identity layers, ignored-byte policy, and authorization boundary.
  - [x] Preserve `parameter-evidence.csv`, the decision record, mock-admission record, and legacy quarantine as downstream/adjacent records. Validate CSV references with the standard library and preserve YAML references through unchanged IDs; if a migration audit scans the controlled YAML files, limit it to exact `source_id:` keys and do not present it as a general YAML parser. Full decision/mock contract parsing belongs to Story 9.4. Do not rewrite parameter classes or approve blocked records.
  - [x] Populate bounded source-use records, not only their schema: create one explicit exact-locator use for every currently adopted use referenced by `parameter-evidence.csv`, the decision record, and the mock-admission record. For every remaining `index.md` project-use statement, create an exact located use or preserve it as `unresolved` with the missing-locator limitation. No source may appear suitable for an adopted claim through a broad project-use phrase alone.

- [x] Task 4: Model exact claim applicability and responsible authority (AC: 1, 4, 5)
  - [x] Define a flat bounded source-use record with stable use ID, logical source ID, mandatory exact source-revision ID for every `located`/formal use, claim-use token, typed exact locator, supported scope, excluded scope/prohibited interpretations, applicable device/variant/profile/protocol/dataset/version, prototype component, bounded research question, evidence track, final-package element, transferability rationale, status, and limitations. A logical `source_id` alone is never sufficient scientific identity.
  - [x] Require locator kinds appropriate to the medium: printed/PDF page plus section/table/figure/parameter for documents; versioned clause/field for standards/specifications; full commit plus file/symbol for repositories; release/file/native role/hash for datasets; DOI/version plus exact page/section/table/figure for papers.
  - [x] Treat vendor manuals as official/authoritative only for their exact device, variant, revision, and documented fact; standards only for their stated scope; dataset-owner releases for exact dataset identity; papers for their reported methods/results; and tooling documentation only for tool behavior.
  - [x] Preserve the current authority distinctions: Danfoss 4/20 mA defaults may be exact direct-source facts; 0/100 and 25/75 remain researcher decisions; P200 remains blocked pending verified official bytes; FB420 does not supply project RPM endpoints; NI supports a scaling method; DOE supplies qualitative context; papers do not supply universal thresholds or model superiority.
  - [x] Permit the catalog to record a source as a candidate applicable authority, but leave executable value, unit, parameter class, class-specific sufficiency, dimensional derivation, decision/calibration/mock authority, conflicts, and G1/startup/freeze decisions to `ParameterEvidence.v1` in Story 9.4.

- [x] Task 5: Preserve access, license, citation, notice, and redistribution evidence (AC: 3, 6, 9)
  - [x] Record access state, local possession/verification, declared license or terms locator, citation/notice requirements, permitted project use, redistribution status, storage policy, and unresolved limitations independently.
  - [x] Do not infer a license from a URL, file extension, repository license, author-copy availability, public accessibility, citation permission, or local possession. Unknown rights block redistribution claims but do not fabricate a legal conclusion.
  - [x] Keep restricted, paywalled, and large dataset/source bytes outside Git. Preserve catalog metadata and checksums in Git; retain the existing ignored archive policy and do not stage ignored source bytes accidentally.
  - [x] Preserve author-copy, publisher-copy, translation, language edition, dataset archive, code, and documentation rights separately; one artifact's license never silently licenses another.

- [x] Task 6: Preserve canonical sources, mirrors, copies, aliases, and discrepancies (AC: 2, 7)
  - [x] Represent canonical-owner locators and each retrieval location separately. Identical hashes may share a content identity while retaining distinct retrieval observations; title or filename similarity alone never establishes equivalence.
  - [x] Implement only the relations required by current migration and AC7: `mirror_of`, `alias_of`, `byte_identical`, and `conflicts_with`. Add `translation_of` or `supersedes` only when an actual migrated record needs it; otherwise defer new relation tokens to a later schema version.
  - [x] Require every relation target to resolve; reject self-relations and duplicate edges. `byte_identical` requires equal verified hashes. If `supersedes` is actually adopted, require an acyclic revision chain under the same logical `source_id`.
  - [x] Preserve differing hashes, counts, versions, layouts, or owner/mirror statements in explicit discrepancy records with status and limitation. Never apply a newest-wins, official-looking-wins, or majority-vote resolution.
  - [x] Register historical third-party ADFA material as mirror/retrieval evidence rather than official owner bytes, and keep currently unpinned HAI/LID/tool repository locations visibly mutable until exact owner revisions are qualified.

- [x] Task 7: Provide deterministic serialization, projections, and a read-only validator command (AC: 8, 9)
  - [x] Define the exact Story 9.3 representation: UTF-8, LF, sorted object keys, schema-defined array ordering by stable IDs, compact separators for the machine file, `ensure_ascii=False`, `allow_nan=False`, and one final newline. Reject floats/NaN/Infinity in catalog identity data; use exact strings/integers where needed.
  - [x] Do not claim RFC 8785 conformance from `json.dumps(sort_keys=True)` alone. This story owns a bounded schema-specific deterministic encoding; Story 9.6 owns the general artifact-manifest canonicalization boundary.
  - [x] Add `scripts/validate_source_catalog.py` as a read-only check/report entry point with optional explicitly supplied archive root. It may render proposed deterministic projections to stdout or compare existing projections in `--check` mode, but it never writes files and must not download, update, authorize, or mutate scientific/runtime state.
  - [x] Ensure repeated parsing, validation, serialization, human-index projection, and checksum projection produce byte-identical outputs and stable ordered diagnostics.

- [x] Task 8: Add focused catalog, migration, and boundary tests (AC: 1-9)
  - [x] Add `tests/evidence/test_source_catalog.py` using standard-library `unittest` and temporary synthetic files. Tests must not require the ignored 97 MiB local archive, network, Docker, MinIO, runtime services, datasets, training, capture, experiments, or UI.
  - [x] Cover every retrieval/access state; all required metadata; local hash/size/date/locator verification; malformed/uppercase/non-64-character digests; missing files; mutation/mismatch; duplicate IDs; unsafe paths; symlink/junction escape; mutable URL-only identity; and deterministic bytes/order/diagnostics.
  - [x] Keep path-escape coverage portable on Windows: run a real symlink/junction case only when the test process can create it, and always exercise fail-closed escape behavior through an injected/fake path resolver so tests do not require administrator privileges or Developer Mode.
  - [x] Cover exact typed claim locators, scope/variant mismatches, contextual/scholarly/secondary/mirror sources rejected as responsible direct-number authority, Danfoss accepted/rejected boundaries, P200 blocked state, unresolved FB420 endpoints, and catalog records rejected as parameter or mock authorization.
  - [x] Cover byte-identical mirrors with separate retrievals, differing mirror hashes with explicit discrepancies, translations/author copies as distinct source copies, unknown rights blocking redistribution claims, and no automatic conflict resolution.
  - [x] Add migration tests proving all 64 current source IDs survive, the four new technical-source IDs exist, all 34 checksum rows bind to exactly one intended local source record, every current CSV/bounded-YAML use maps to the expected source-use record rather than only a source ID, and the human/checksum projections cannot drift from the machine catalog.
  - [x] Prove filesystem mtime, the global register baseline date, and current execution time cannot fill an unknown historical retrieval date. Prove successful HTTP retrieval or public accessibility cannot promote authority, rights, applicability, local verification, or acquisition status.
  - [x] Assert `authorization_effect == "none"` and prove validation performs no network/download, training, capture, experiment, activation, publication, runtime, or dashboard side effect.
  - [x] Run the focused module followed by `unittest` discovery; preserve the dirty worktree and never alter unrelated user files merely to make tests pass.

### Review Follow-ups (AI)

- [x] [AI-Review][Spec] Clarify that exact version/release authority lives in `SourceRevision`; immutable `SourceRecord` version fields preserve the migrated baseline and must match at least one revision.
- [x] [AI-Review][High] Enforce source/revision/content/retrieval/use graph consistency.
- [x] [AI-Review][High] Make prior-catalog validation append-only across every stable record family.
- [x] [AI-Review][High] Require adequate immutable/retrieval/access/authority evidence for formal located uses.
- [x] [AI-Review][High] Validate medium-specific exact locator structure.
- [x] [AI-Review][High] Make mirror, byte-identical, and discrepancy relationships representable and fail closed.
- [x] [AI-Review][Medium] Reject malformed nested JSON, collection shapes, floats, and caller-controlled authorization effects.
- [x] [AI-Review][Medium] Close date, rights, URL, mutable-query, content-path, and projection boundaries.
- [x] [AI-Review][Medium] Remove ignored-archive dependency from the focused unit suite and add regression coverage for every correction.

## Dev Notes

### Scope and dependency boundary

- This story creates source identity, retrieval/byte evidence, exact source-use scope, and limitations. It does not create `ParameterEvidence.v1`, decide an executable parameter class/value, admit a mock, authorize acquisition/execution, qualify a dataset result, build a generic artifact manifest, or modify runtime/UI behavior.
- Stories 9.1 and 9.2 are hard implementation prerequisites. Do not begin Story 9.3 implementation until Story 9.1's evidence package and Story 9.2's vocabulary exports exist and their focused tests pass; if they are absent, stop rather than create duplicate placeholder packages, enums, or canonicalization helpers. Reuse Story 9.2 source/evidence roles and fail closed on an unknown vocabulary version.
- Story 9.3 supplies immutable source-revision/use references that later semantic identities can cite. Passing source/source-use validation never assigns Story 9.2 `official_real` to dataset bytes; the later dataset gate must independently bind the owner source, exact release, layout, license scope, and content hashes.
- Story 9.4 consumes these records and owns numeric sufficiency, class-specific authority, derivation, decisions, calibrations, mock admission, and the parameter gate. A source catalog entry is evidence, never proof that a manufacturer selected a project factor.
- Stories 9.6-9.8 own the general artifact/evaluation manifest, persistent evidence qualification, and activity authorization. Do not pre-implement those stories here.
- `ready-for-dev` means this specification is implementation-ready; it does not authorize implementation. A separate immutable activity authorization is required before implementation begins, and further distinct authorization remains required for dataset/document acquisition, training, syscall capture, experiment execution, promotion, activation, publication, or deployment.
- UI/UX is optional and entirely out of scope. No dashboard screen, control, provenance browser, or visual redesign is required.

### Identity and authority rules

- Keep stable logical source, exact issuer version/revision, retrieved byte stream, and retrieval location distinguishable as `source_id`, `source_revision_id`, `content_id`, and `retrieval_id`. Current ledger `source_id` values are compatibility identities only; each adopted scientific use must resolve uniquely to an exact revision, and ambiguous/unresolved aliases fail closed rather than silently following changed content.
- For local bytes, SHA-256 is necessary but not sufficient: bind digest, size, exact filename, media type, retrieval date/status, and archive locator. A changed byte stream is a new immutable identity even when title and URL are unchanged.
- For link-only/restricted sources, absence of bytes is an explicit limitation, not a fake digest. An official landing page can establish issuer/existence while remaining insufficient for exact content or a direct numeric claim.
- `official`, `primary`, `peer_reviewed`, `authoritative`, `vendor`, `standard`, `dataset_owner`, and `secondary` are orthogonal facts. Applicability is bounded by exact source scope, not conferred by prestige or category.
- A source-use record proves what the cited locator states and where the project intends to use it. Story 9.4 still decides whether that evidence is sufficient and transferable for an executable parameter.
- Catalog inclusion never grants rights. Preserve declared terms and unknowns literally; do not make legal conclusions or redistribution assumptions.

### Existing archive intelligence

- At planning time, `catalog/index.md` contains 64 unique IDs: 17 standards/specifications, 11 manufacturer sources, 11 government sources, 12 dataset/model primary sources, and 13 tooling sources.
- The current statuses normalize to 34 local, 23 link-only, 6 restricted, and 1 pending. One link-only record preserves an observed 404; do not convert that observation into acquisition success or source disappearance.
- `checksums.sha256` has 34 entries; all 34 declared files exist and match, with no duplicate digest. The ignored local source archive is about 97 MiB. These matching totals do not prove row-to-file linkage; migration must establish the explicit relationship.
- `parameter-evidence.csv` has 15 source-linked parameter rows; the decision and mock records also resolve their current IDs. Preserve these references. Story 9.3 must not imply that the ledger covers every future parameter.
- All `docs/reference-archive/` material is currently untracked. The 30 PDFs are ignored by the local archive rule; the 3 Markdown and 1 text source copies are untracked but not ignored. Preserve the user's archive, add only intended versionable metadata/projections, decide deliberately whether those four small source copies belong in Git, keep ignored large/restricted bytes outside Git, and never clean/reset/stage unrelated files.

### Technical implementation guidance

- Use Python `>=3.14` and the standard library only. `hashlib.file_digest()` is suitable for opaque binary hashing; `json` supports sorted keys, compact separators, and rejection of NaN/Infinity. No dependency upgrade is required.
- Use explicit string enum values and frozen dataclasses, but remember `frozen=True` only emulates immutability. Store nested collections as tuples/frozen values and copy caller-owned mappings before retaining them.
- Do not parse the Markdown register as the runtime authority, infer metadata from filenames/mtime, scrape claims from source bytes, or auto-follow URLs. Migration is an explicit reviewed data conversion into the JSON contract.
- Keep structured rule IDs stable and sort validation failures by rule ID, record ID, and field path. Consumers must never parse free-text prose to decide scientific policy.
- Stream hashes and verify size/digest after reading. If the file changes during verification, report an explicit unstable/mismatch failure; do not publish a successful observation.

### Project Structure Notes

- Contract: `src/parallel_truth_fingerprint/contracts/source_catalog.py`.
- Validation/serialization/projection: `src/parallel_truth_fingerprint/evidence/source_catalog.py`.
- Machine authority: `docs/reference-archive/catalog/source-catalog.v1.json`.
- Human/checksum projections: `docs/reference-archive/catalog/index.md` and `docs/reference-archive/catalog/checksums.sha256`.
- Read-only command: `scripts/validate_source_catalog.py`.
- Tests: `tests/evidence/test_source_catalog.py`.
- Documentation: `docs/reference-archive/README.md`.
- Do not add a database, API route, source service, workflow engine, web crawler, download manager, RDF store, UI component, generic manifest framework, or scientific activity runner.

### Technical Research Notes

- W3C PROV-DM distinguishes fixed-aspect entities, revisions, specializations, and alternate entities. That supports separate family/version/copy relationships, but this prototype needs only flat IDs and relations rather than a PROV/RDF implementation.
- RFC 8785 confirms why hashable JSON needs invariant serialization and stronger constraints than key sorting. The story therefore defines a bounded deterministic schema representation and does not overclaim full JCS compliance.
- Python 3.14 documents `hashlib.file_digest()` for binary file hashing and notes its updated non-blocking-file behavior; use normal blocking binary files and close them explicitly.
- The SPDX 3.0.1 Licensing Profile's `hasDeclaredLicense` and `hasConcludedLicense` sections distinguish declared from concluded license information and missing information from an explicit `NoAssertionLicense`. Use that distinction only as conceptual guidance for preserving declared terms/unknowns; do not claim legal analysis or SPDX conformance.

### Testing Standards

- Use `unittest` with table-driven `subTest()` cases, temporary directories, small binary fixtures, and deterministic clocks supplied by the test.
- Assert structured rule IDs and field paths, exact canonical bytes, and source/reference resolution. Do not assert only human message text.
- Keep the focused suite independent of ignored local documents. Add a read-only real-archive validation command for the implementation environment, while unit tests exercise equivalent synthetic fixtures.
- Run full discovery because new public contract exports and the shared `evidence` package can affect existing imports even without runtime changes.

### References

- [Source: _bmad-output/planning-artifacts/epics.md#Cross-Epic Mock Admission Guardrail]
- [Source: _bmad-output/planning-artifacts/epics.md#Epic 9: Reproduce and Trust the Existing Prototype]
- [Source: _bmad-output/planning-artifacts/epics.md#Story 9.3: Build the Authoritative Source-Evidence Catalog]
- [Source: _bmad-output/planning-artifacts/prd.md#Controlling Consolidated Requirements Inventory — FR31, FR32, FR76]
- [Source: _bmad-output/planning-artifacts/prd.md#NonFunctional Requirements — NFR38-NFR40, NFR48-NFR52]
- [Source: _bmad-output/planning-artifacts/architecture.md#Controlling V2 Architecture Consolidation - 2026-08-22]
- [Source: _bmad-output/planning-artifacts/architecture.md#Authoritative evidence contracts]
- [Source: _bmad-output/planning-artifacts/architecture.md#Verification gates and failure semantics]
- [Source: _bmad-output/implementation-artifacts/9-2-establish-the-semantic-and-evidence-role-vocabulary.md]
- [Source: docs/reference-archive/README.md#Authority and storage policy]
- [Source: docs/reference-archive/catalog/index.md]
- [Source: docs/reference-archive/catalog/checksums.sha256]
- [Source: docs/reference-archive/catalog/parameter-evidence.csv]
- [Source: docs/reference-archive/catalog/decision-custom-reference-window-v1.yaml]
- [Source: docs/reference-archive/catalog/mock-admission-ptfp-signal-emulator-v1.yaml]
- [Source: docs/reference-archive/catalog/legacy-constant-quarantine-v1.csv]
- [Source: src/parallel_truth_fingerprint/contracts/dataset_artifact.py]
- [Source: src/parallel_truth_fingerprint/contracts/__init__.py]
- [W3C PROV-DM](https://www.w3.org/TR/prov-dm/)
- [RFC 8785: JSON Canonicalization Scheme](https://www.rfc-editor.org/rfc/rfc8785.html)
- [Python 3.14 `hashlib`](https://docs.python.org/3.14/library/hashlib.html)
- [Python 3.14 `json`](https://docs.python.org/3.14/library/json.html)
- [Python 3.14 `dataclasses`](https://docs.python.org/3.14/library/dataclasses.html)
- [SPDX 3.0.1 Licensing Profile](https://spdx.github.io/spdx-spec/v3.0.1/model/Licensing/Licensing/)

## Mandatory Academic Evidence Amendment

Before implementation, apply the relevant mandatory controls in [Academic Evidence Admission Amendment — 2026-08-31](../planning-artifacts/academic-evidence-admission-amendment-2026-08-31.md). This story must fail closed on an unresolved evidence origin, numeric authority, required mock closure, or prohibited dataset substitution. The amendment adds no activity authorization.
## Dev Agent Record

### Agent Model Used

OpenAI Codex (GPT-5)

### Implementation Plan

- Define flat immutable source, revision, content, retrieval, bounded-use, relation, discrepancy, and validation contracts.
- Migrate the existing archive into one deterministic machine authority while preserving all historical IDs and unknowns.
- Add fail-closed validation, deterministic projections, a read-only command, and focused boundary tests.

### Debug Log References

- Prerequisite evidence suite before implementation: 108 tests passed, 3 skipped symlink cases.
- Focused Story 9.3 module after review corrections: 37 tests passed.
- Read-only metadata and local archive checks: 69 sources, 69 revisions, 34 contents, 69 retrievals, and 92 uses validated.
- Evidence discovery after review corrections: 145 tests passed, 3 skipped symlink cases.
- Safe comparison/HART regression boundary: 10 tests passed.
- A raw discovery invocation without the project import path produced three import errors; rerunning with `src` explicitly loaded passed. No product defect was involved.
- Full repository discovery was intentionally not run because unrelated tests may trigger training or other scientific activity prohibited by the standing authorization boundary.

### Completion Notes List

- Added deterministic `SourceCatalog.v1` contracts with closed vocabulary tokens and stable structured diagnostics.
- Migrated all 64 historical source IDs, added four implementation-reference sources, and registered the historical ADFA mirror separately.
- Bound all 34 declared local files to exact filename, size, digest, retrieval, and archive location without using filesystem timestamps as historical evidence.
- Preserved 92 bounded or explicitly unresolved source uses, including every current CSV and controlled YAML reference.
- Kept direct numeric authority, qualitative context, derivation methods, researcher decisions, access, rights, and redistribution as separate facts.
- Added medium-specific locator kinds, immutable-identity mutation detection, opaque byte checks, path-escape protection, relation/discrepancy rules, and deterministic JSON/Markdown/checksum projections.
- Validation and the CLI remain read-only and have `authorization_effect: none`; no acquisition, download, training, capture, experiment, activation, publication, or deployment occurred.
- Resolved all nine accepted review groups: graph consistency, append-only history, formal-use qualification, exact locators, relation/discrepancy semantics, strict parsing, metadata/projection boundaries, and clean-checkout test isolation.
- Exact version/release authority now resides in `SourceRevision`; immutable logical-source version/date fields are documented and validated as migration-baseline metadata matching at least one revision.
- `byte_identical` now relates separate retrieval observations sharing one verified content identity, avoiding impossible duplicate content IDs.

### File List

- `_bmad-output/implementation-artifacts/9-3-build-the-authoritative-source-evidence-catalog.md`
- `_bmad-output/implementation-artifacts/sprint-status.yaml`
- `docs/reference-archive/README.md`
- `docs/reference-archive/catalog/source-catalog.v1.json`
- `docs/reference-archive/catalog/index.md`
- `docs/reference-archive/catalog/checksums.sha256`
- `scripts/validate_source_catalog.py`
- `src/parallel_truth_fingerprint/contracts/__init__.py`
- `src/parallel_truth_fingerprint/contracts/source_catalog.py`
- `src/parallel_truth_fingerprint/evidence/source_catalog.py`
- `tests/evidence/test_source_catalog.py`

### Change Log

- 2026-09-04: Implemented and validated the authoritative SourceCatalog.v1 ledger; moved Story 9.3 to review.
- 2026-09-04: Addressed code review findings - 9 grouped follow-ups resolved; 37 focused and 155 safe regression tests passed; Story 9.3 concluded.
