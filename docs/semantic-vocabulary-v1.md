# Semantic Vocabulary v1

This document is the human-readable companion to `semantic-vocabulary.v1`. The
code contract is authoritative for serialized tokens. A changed token or changed
meaning requires a new vocabulary version; v1 is never mutated in place.

Validation is pure and has `authorization_effect=none`. It does not authorize
acquisition, capture, training, experiments, publication, activation, or
presentation work.

## Closed vocabulary

| Axis | Exact v1 tokens | Meaning |
| --- | --- | --- |
| DetectionModality | `physical_instrumentation`, `linux_host_syscall` | The only detection modalities. Two modalities on one identity mean aligned support or fusion; there is no fusion modality. |
| RepresentationKind | `raw_current_ma`, `normalized_span`, `engineering_value`, `categorical_syscall_event` | An observation representation, never a modality. In particular, 4-20 mA belongs to `raw_current_ma`. |
| ModelFamily | `lstm`, `gru`, `autoencoder`, `baseline` | Sorted, unique model-family tags. A model is not a dataset, modality, representation, or evidence source. |
| EvidenceRole | `custom_generated`, `official_real`, `fixture_test`, `published_reference`, `runtime_evidence`, `legacy_v1` | Why the evidence exists and who/what produced its evidence track. |
| ResultRole | `none`, `locally_measured`, `published_reference`, `fixture_expected`, `legacy_recorded` | How a result value entered the record. This is independent from qualification and origin. |
| ScientificStatus | `qualified`, `unqualified`, `blocked`, `unsupported`, `test_only`, `reference_only`, `legacy` | Scientific usability decided by an owning gate, not by a favorable metric. |
| SyntheticStatus | `authentic`, `mock`, `mock_derived`, `not_applicable` | Orthogonal lineage. Mock lineage is not a result role. |
| EntityKind | `source`, `dataset`, `run`, `artifact`, `representation`, `model`, `detector_bundle`, `score`, `evaluation_result`, `fixture`, `legacy_mapping` | The kind of entity whose semantics are being declared. |
| DatasetFamily | `adfa_ld`, `lid_ds_2021`, `hai_23_05`, `ptfp_custom_v1` | Closed governed dataset families where a dataset is applicable. |
| DomainScope | `compressor_prototype`, `native_adfa_ld`, `native_lid_ds_2021`, `native_hai_23_05`, `ptfp_custom_controlled`, `real_plant`, `not_applicable` | The bounded domain in which the evidence can support a claim. |
| EvidenceOrigin | `official_native`, `authentic_capture`, `prototype_generated`, `mock_parameterized`, `measured`, `test_fixture` | Exactly one origin for domain-bearing evidence. Origin never substitutes for synthetic lineage. |

Explicit not-applicable tokens are used only where the vocabulary provides
them. Unknown or missing values are not guessed. Scientific consumers reject
unsupported or invalid identities. A presentation-only consumer may display an
`UnsupportedSemanticIdentity`, including the untouched raw version and payload,
but may not correct it, persist it as valid evidence, or affect scientific or
control state.

All semantic axes and the formal-evidence flag are explicit constructor inputs.
Numeric representations, scores, and evaluation results additionally carry at
least one immutable `numeric_authority_references` entry with the minimal shape
`parameter-evidence:<stable-id>:sha256:<64-lowercase-hex>`. Mutable aliases such
as `latest`, `current`, and `head` are rejected. This vocabulary checks only the
reference shape; Story 9.4 owns units, formulas, input identities, content
resolution, source locators, and parameter-gate closure.

## Evidence and dataset boundaries

`official_real` means qualified owner-origin dataset evidence in its native
scope. It does not mean real plant. It requires immutable source qualification.
`qualified` independently requires the immutable result of its owning gate.
`locally_measured` only says that this identified project execution calculated
the result; it may still be unqualified, blocked, or mock-derived.

The origins have these bounded meanings:

- `official_native`: pinned official bytes in the external dataset's native
  track.
- `authentic_capture`: an observation from a declared authentic acquisition
  boundary with immutable capture provenance.
- `prototype_generated`: output emitted by an identified prototype function.
- `mock_parameterized`: prototype-generated output influenced by an admitted
  unavailable external behavior. It also requires
  `generation_origin=prototype_generated` and a per-field influence map binding
  each affected field to exact parameter evidence and mock admission.
- `measured`: calibration or pilot evidence with its preserved method and
  provenance; it is not automatically qualified.
- `test_fixture`: conspicuous, non-domain, test-only material that cannot enter a
  formal evidence path.

ADFA-LD and LID-DS 2021 are external categorical Linux-syscall evidence. HAI
23.05 is external native physical/SCADA evidence; it is not compressor data and
does not imply wholesale 4-20 mA representation. Only PTFP-Custom-v1 may carry
aligned custom physical and syscall modalities. Under the approved prototype
boundary, its physical channel is mock-parameterized by the admitted signal
emulator, while formal custom syscalls require authentic host capture.
Governed versions are exactly `ADFA-LD`, `LID-DS-2021`, `HAI-23.05`, and
`PTFP-Custom-v1`. A dataset identity declares its family, and every governed
non-fixture record retains non-blank native scope, native role, subset, and at
least one limitation. Domain-bearing `custom_generated` evidence uses
`ptfp_custom_v1` in `ptfp_custom_controlled`; it cannot borrow a native external
scope or omit its family.

Published-reference results require published-reference evidence, official
native origin, and `reference_only` status. Legacy evidence/results remain the
exact `legacy_v1` + `legacy_recorded` + `legacy` combination. `unsupported` is a
presentation state, never a valid writable identity. Prototype-generated bytes
cannot claim authentic lineage, and official-native evidence cannot carry mock
or prototype-generation provenance.

Valid examples include:

- official-native ADFA-LD plus a separately identified local evaluation;
- custom mock-derived physical measurements with the exact admission and
  per-field parameter lineage;
- authentic custom syscall measurements bound to raw host capture;
- an author-produced local metric that remains unqualified;
- a test fixture with fixture-expected values;
- a model tagged with both `lstm` and `autoencoder`; and
- aligned two-modality PTFP-Custom-v1 evidence without inventing a `fusion`
  modality.

## Source context and non-conflation

In the physical-instrument context, a sensor is a device whose electrical signal
represents a measured physical property. The software-only custom physical source
is a `signal_emulator`, simulated channel, or logical channel. A historical
`sensor_id` proves only a preserved logical identifier; it does not prove physical
hardware, compressor measurement, or a digital twin.

Scenario, fault, attack, anomaly, incident, SCADA divergence, and suspected
Byzantine behavior are not synonyms. Scenario, fault, and attack belong to
declared truth or context. An anomaly is a deviation outcome from a frozen
detector or policy and establishes no cause before an authorized truth join.
Operational outcomes such as normal/anomalous, run success/failure, consensus
status, and SCADA divergence remain separate from scientific status, evidence
role, result role, scenario truth, fault, and attack labels.

A model is not a detector. A detector requires a compatible model together with
the frozen schema and vocabulary, preprocessing, calibration, threshold/decision
policy, runtime identity, and detector-bundle compatibility owned by later
stories. Likewise, evidence baseline, the `baseline` model-family tag, and the
historical `LEGACY_BASELINE` label have different meanings.

## Legacy interpretation

`LegacySemanticMapping.v1` references an exact Story 9.1 `baseline_id` and entry
ID. Validation resolves that frozen manifest entry and checks the actual original
field/value rather than trusting a caller-provided copy. It stores the original field/value, current interpretation, provenance, and
at least one limitation, and is always `legacy`. It never rewrites the original
entry bytes, label, hash, or identity and never upgrades historical evidence.

The explicit minimal interpretations are:

| Historical label | Current bounded interpretation |
| --- | --- |
| `IMPLEMENTED_RUNTIME_EVIDENCE` | runtime evidence only |
| `FIXTURE` | fixture-test evidence and fixture-expected result |
| `PUBLISHED_REFERENCE` | published-reference evidence/result |
| `MEASURED_RESULT` | locally measured, without implying qualified, authentic, or real plant |
| `EXPERIMENTAL_FINGERPRINT_BASELINE` | legacy-v1 evidence with a baseline model-family tag |
| `LEGACY_BASELINE` | legacy-v1 evidence only |

Historical `lstm_autoencoder` is interpreted as the two model tags `lstm` and
`autoencoder` with legacy status. Historical logical sensor labels retain their
channel and known simulator/emulator source context, using exactly the
`logical_channel`, `source_context`, and `hardware_claim=unsupported` fields.

The v1 parser rejects unknown top-level fields, wrong collection member types,
and malformed mock-influence records. It never drops or stringifies them into an
apparently supported identity.

## Stable validation diagnostics

Writers and evaluators decide policy from structured rule IDs and field paths,
not explanation prose. Violations are sorted by rule ID and field path.

| Rule ID | Rejected condition |
| --- | --- |
| `SEM-VERSION-MISSING` | No vocabulary version. |
| `SEM-VERSION-UNSUPPORTED` | A version other than v1. |
| `SEM-TOKEN-UNKNOWN` | Any unknown or omitted required semantic token. |
| `SEM-MODALITY-REQUIRED` | A modality-bearing entity has no modality. |
| `SEM-REPRESENTATION-CROSS-MODALITY` | A physical representation is assigned to syscall-only evidence or conversely. |
| `SEM-MODEL-AS-DATASET` | Model-family tags are used to define a dataset. |
| `SEM-MODEL-ONLY-AS-DETECTOR` | A model is presented as a complete detector bundle. |
| `SEM-FIXTURE-AS-MEASURED` | Fixture material is promoted to a local measurement. |
| `SEM-REFERENCE-AS-MEASURED` | A published reference is promoted to a local measurement. |
| `SEM-OFFICIAL-REAL-WITHOUT-SOURCE-QUALIFICATION` | Official-real lacks immutable source qualification. |
| `SEM-QUALIFIED-WITHOUT-GATE-REFERENCE` | Qualified lacks its owning-gate result. |
| `SEM-HAI-AS-COMPRESSOR` | HAI is described as compressor or real-plant evidence. |
| `SEM-ADFA-AS-PHYSICAL` | ADFA-LD is described as physical evidence. |
| `SEM-LID-AS-PHYSICAL` | LID-DS 2021 is described as physical evidence. |
| `SEM-CUSTOM-AS-OFFICIAL-OR-REAL-PLANT` | Controlled custom evidence is promoted to official-native or real plant. |
| `SEM-CUSTOM-PHYSICAL-NOT-MOCK-DERIVED` | Current custom physical evidence loses its admitted mock lineage. |
| `SEM-SYSCALL-SYNTHETIC` | Generated, replayed, or synthetic syscalls enter formal custom evidence. |
| `SEM-EXTERNAL-MODEL-AS-COMPRESSOR-DETECTOR` | An external benchmark model is presented as a compressor detector. |
| `SEM-DATASET-NATIVE-SCOPE-MISSING` | Dataset family, version, native scope, native role, subset, or limitations are missing. |
| `SEM-DATASET-NATIVE-MISMATCH` | A governed dataset has the wrong version/modality/scope, or custom domain evidence omits its PTFP family. |
| `SEM-IDENTITY-MISSING` | The stable semantic identity is blank or uses a mutable alias. |
| `SEM-LEGACY-MAPPING-INCOMPLETE` | A legacy mapping is unknown, mutable in intent, or lacks source identity, provenance, or limitation. |
| `SEM-ORIGIN-MISSING` | Evidence origin is unresolved. |
| `SEM-ORIGIN-UNKNOWN` | Evidence origin is outside the closed axis. |
| `SEM-ORIGIN-INCOMPATIBLE` | Origin, role, result role, status, or synthetic lineage form an incompatible promotion. |
| `SEM-OFFICIAL-NATIVE-SCOPE` | Official-native origin is attached outside an eligible native external dataset scope. |
| `SEM-AUTHENTIC-CAPTURE-PROVENANCE` | Authentic capture lacks immutable boundary provenance. |
| `SEM-TEST-FIXTURE-FORMAL-PATH` | Test fixture enters a formal evidence path. |
| `SEM-MOCK-GENERATION-ORIGIN` | Mock-parameterized output lacks prototype-generation binding. |
| `SEM-MOCK-INFLUENCE-INCOMPLETE` | A mock-influenced field lacks a unique path, exact parameter authority, or the current admission. |
| `SEM-NUMERIC-AUTHORITY-MISSING` | A numeric representation, score, or evaluation lacks a structured immutable parameter-evidence reference. |
| `SEM-ORIGIN-PROMOTION` | Prototype, mock, or fixture origin is promoted to official or real-plant evidence. |
| `SEM-REFERENCE-INVALID` | An explicit identity, provenance, qualification, capture, bundle, or authority reference is blank or not immutable in form. |

Invalid identities are not eligible for measured-result or complete-evidence
namespaces. Scientific persistence and publication code uses the fail-closed
serialization gate, which requires `supported=true` and `valid=true` before
returning a writable payload.
