# Academic Evidence Admission Amendment — 2026-08-31

## Status and purpose

This amendment is mandatory pre-implementation planning context for Stories 9–18. It resolves the Party Mode review finding that evidence-origin, mock admission, prototype-generation provenance, and current authentic-path availability must be mechanically checkable rather than only described in prose.

It does not authorize implementation, acquisition, capture, experiment execution, storage mutation, training, evaluation, truth activity, publication, activation, or presentation. It introduces no scientific value, threshold, interval, seed, ratio, default, or dataset row.

## Closed evidence-origin model

Each domain-bearing record, event, result, and displayed claim SHALL declare exactly one closed `evidence_origin`:

- `official_native` — bytes from the pinned official dataset/version in its native track only;
- `authentic_capture` — an event or observation acquired from the declared authentic boundary;
- `prototype_generated` — emitted by the identified prototype function under immutable code/runtime/configuration/input lineage;
- `mock_parameterized` — represents a specifically unavailable external behavior or value through an admitted prototype function;
- `measured` — calibration/pilot evidence with preserved method, environment, date, uncertainty, and hash;
- `test_fixture` — conspicuous non-domain test-only material.

`prototype_generated` is not a mock merely because the prototype is simulated. `mock_parameterized` is a composite artifact origin only: it SHALL additionally declare `generation_origin=prototype_generated` and a closed per-field/derivation `mock_influence` map. That map identifies each mock-parameterized behavior/value and its exact admission and parameter revision; fields without mock influence retain their own direct/derived/measured/preregistered lineage. This preserves the fact that a real prototype function emitted the artifact without hiding a modelled external behavior. A `mock_parameterized` artifact without the required prototype generation binding is invalid. Neither origin may be promoted to `measured`, `authentic_capture`, `official_native`, real-plant, hardware-validated, or externally validated evidence.

## Numeric and mock-admission closure

Every numeric consumer SHALL expose the exact immutable `ParameterEvidence.v1` revision/content hash, unit, source/decision/calibration/mock locator, and, if derived, formula and immutable input identities. Missing, defaulted, substituted, invented, stale, or incompatible authority blocks the result and any claim.

For every `mock` parameter or `mock_parameterized` behavior, the consumer SHALL resolve all of the following on every formal producer, consumer, campaign qualification, and final-package gate:

1. an immutable approved `MockAdmission.v1`;
2. an accountable `ParameterGateResult.v1`;
3. an exact applicable official `SourceEvidence`/source-use revision, content hash, and locator for each asserted behavior and number;
4. a documented authentic-path assessment with the only passing disposition `unavailable_with_evidence`;
5. a bounded purpose, limitation, prohibited claims, replacement condition, and direct necessary final-comparison linkage; and
6. a binding to the exact permitted prototype generator.

Convenience, cost, timing, a weakly similar source, a favorable result, an old admission, or an unpinned runtime never establishes admissibility. If the declared applicable authentic external boundary can generate or capture the required artifact, the mock is forbidden; the mere fact that a simulator can emit a prototype-generated output is not evidence of that authentic external capability.

## Prototype-generation binding

The existing `MockAdmission.v1` / parameter-evidence contract SHALL be extended only as a pure immutable contract and validator — never as a new service, scheduler, workflow engine, or control authority. For a domain mock it must bind:

- `prototype_component_id`, module/entrypoint, interface schema/version, and exact code artifact content ID/hash;
- exact runtime identity; ordered configuration and `ParameterEvidence.v1` revisions/hashes;
- randomness mode (`deterministic` or `seeded`) and, when seeded, the seed's `ParameterEvidence.v1` revision/hash;
- permitted output record family and semantic provenance;
- required immutable emission-trace or output-manifest role and content identity; and
- prohibited output roles and claims.

A generic component name, runtime identity, admission ID, or later code/configuration is not a substitute. Missing/mismatched entrypoint, configuration, parameter, seed, trace, output role, or content identity fails closed.

Each mock-derived output must carry a `GeneratedEvidenceProvenance.v1` reference (or a versioned equivalent owned by the relevant existing contract) binding its producer function/module, code/runtime, input/parameter identities, admission, official source-use locator/hash, origin, and immutable emission trace/output manifest. Authentic observations reject mock-generation provenance; it must not be attached merely to make a record look more complete.

## Fresh authentic-path assessment

An admission is not perpetual. Every run or campaign that would use a mock must include an immutable `DirectReproductionAssessment.v1` in its existing readiness/run-binding closure. It binds the exact behavior, prototype function, code/runtime/profile, attempt evidence, assessor/approval identity, source-use references, and one closed disposition:

- `still_unavailable_with_evidence` — eligible only if every other closure condition passes;
- `authentic_path_available` — mock and formal run are blocked; or
- `unresolved` — mock and formal run are blocked.

`DirectReproductionAssessment.v1` is a frozen data contract and pure validator, not a service or workflow engine. No clock default, TTL, or invented cadence is introduced. An older assessment, admission alone, or planning approval cannot satisfy this requirement.

## Authentic Linux syscall evidence

The declared prototype workload may be `prototype_generated`, but formal custom syscall evidence is `authentic_capture` only. Every formal syscall event/batch must resolve one-to-one to immutable raw-capture bytes from the qualified collector, with `capture_origin=host_capture`, raw content hash, event range/offset, collector/filter, kernel/boot, cgroup/process/workload, code/runtime, and run identities.

`fixture_replay`, injection, generated/replayed sequence, userspace parser output without raw capture, external dataset sequence, unknown origin, renumbered substitute, or a missing provenance field is `test_fixture`/ineligible and blocks G6, campaign qualification, and `PTFP-Custom-v1`. It remains visible as a test or incomplete artifact; it is never repaired, relabelled, or substituted. A passing neighboring segment or G6 ID is insufficient.

## Dataset and claim boundaries

ADFA-LD, LID-DS 2021, and HAI 23.05 accept only `official_native` formal dataset rows. Prototype-generated, mock-parameterized, fixture, replay, or custom data may be used only in isolated non-domain tests and never enter their formal splits, bundles, scores, G7/G9 records, or claims.

Only a synchronized `PTFP-Custom-v1` campaign may compare physical-only, syscall-only, and late-fusion results over the same runs/support. A final claim, result table, claim-to-evidence index, and optional dashboard projection must retain the exact origin, numeric-authority closure, generator provenance when applicable, current reproduction assessment, limitations, and prohibited claims. The dashboard renders these frozen facts; it never infers or calculates scientific status.

## Story ownership and required changes

| Owner stories | Required planning change |
| --- | --- |
| 9.2, 9.4, 9.5, 9.6, 9.8 | Own the closed origin vocabulary, parameter/mock closure, `MockAdmission.v1` generator binding, fixtures, manifests, and validator behavior. |
| 10.2–10.4, 10.6–10.7 | Preserve origin and generation provenance per custom physical observation; bind it in the experiment specification; revalidate it before formal persistence/qualification. |
| 11.1–11.6, 12.1–12.6, 13.1–13.8 | Every domain numeric consumer resolves the exact authority closure; unknown/default/mock-ID-only input fails closed. |
| 14.1–14.9 | Keep the workload authentic by default. Add closed capture-origin/raw-byte checks at 14.2, 14.3, and G6 in 14.9. |
| 15A.*, 15B.*, 16.* | Accept official-native dataset evidence only; test-only substitutes never reach formal result paths. |
| 17A.1–17A.4 | Bind generator closure at preregistration/readiness, require fresh assessment before a run, preserve per-range physical generation and syscall host-capture provenance, and reject any incomplete chain from `PTFP-Custom-v1`. |
| 17A.5–17B.6, 18.1–18.4 | Propagate and verify the closure in scores, fusion, claims, G9, tables, and read-only presentation. |

## Party Mode decision

John (PM), Winston (Architecture), and Quinn (QA/academic integrity) independently agreed that the preceding requirements are necessary targeted corrections. They preserve the local academic-prototype scope and do not add product infrastructure. Planning is conditionally aligned only after the referenced stories enforce this amendment and an adversarial re-review confirms the hard gates.
