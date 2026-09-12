# Story 11.3: Implement the Deterministic Python Consensus Reference

Status: ready-for-dev

## Story

As a consensus maintainer, I want a pure Python reference evaluator for consensus v2, so that physical comparison and failure semantics have one inspectable executable reference.

## Acceptance Criteria

1. Given a canonically ordered, fully valid `ConsensusRoundInput.v2` and frozen `ConsensusParameterSet.v2`, when the reference evaluates, then it applies only their declared basis and a closed versioned canonical operation-registry identity in fixed order and returns one canonical `ConsensusDecision.v2` without mutable runtime state, I/O, defaults or legacy conversion. Malformed/mixed/hash-invalid prerequisite contracts are pre-evaluation `blocked` results with no decision; a valid round with declared per-observation eligibility defects may produce exclusions.
2. Given schema/profile/quality/freshness/sequence/correlation-invalid observations, when eligibility runs, then each is excluded with immutable evidence ID and explicit reason; source evidence is never repaired, rewritten or normalized.
3. Given eligible contributions, when residual/trust/ranking calculations run, then only exact frozen operation/parameter/derivation identities apply; the operation is from the internally interpreted closed registry, matches its frozen conformance-vector/hash closure, and has canonical input/output semantics. Unknown identity, dynamic import, callable/plugin or conformance mismatch blocks before calculation; declared tie/boundary policy uses exact numeric representation, never Python binary floats or hidden rounding.
4. Given a policy cannot produce a valid consensus, when evaluation completes, then it emits a distinct fail-closed decision with participants, exclusions, diagnostics and evidence references, explicit `no_ranking`, no winner and no reduced success.
5. Given identical canonical inputs and configuration, when evaluation repeats, then decision, complete successful ranking, exclusions, canonical serialization/hash and non-persisted structured trace are identical and reconstruct every operation/input/parameter identity. The trace has one complete bounded public event per evaluated operation/input, event size and maximum count derived from the frozen input/policy budget; an excess blocks before evaluation, never truncates. It contains only audience-compatible mathematical intermediates and opaque IDs, never restricted bytes/locators/counts/timing, truth or scenario labels.
6. Given the evaluator/tests run, when inspected, then they have no authority or import path to truth, syscalls, OPC, detector, command, persistence, network, CometBFT/Go, dashboard, clock/random/environment; passing tests does not activate consensus or G3.

## Tasks / Subtasks

- [ ] Add isolated `src/parallel_truth_fingerprint/consensus_v2/reference_evaluator.py` only after 11.1/11.2 public contracts exist. Consume validated immutable input/set and resolve only a closed canonical operation-registry identity interpreted internally; never accept a callable, plugin, dynamic import or injected execution. Return existing v2 decision plus in-memory bounded trace. Do not add contracts, service, transport, state, manifest, authorization or persistence.
- [ ] Fail closed on absent/mixed/hash-mismatched/inapplicable contracts or policies. Distinguish prerequisite `blocked` from evaluated consensus failure; neither ranks or falls back.
- [ ] Preserve legacy `consensus/engine.py`, `trust_model.py`, `quorum.py`, CometBFT, comparison/runtime/MQTT/storage/dashboard untouched. Their averages, hard-coded scales/thresholds, floats and I/O are v1-only.
- [ ] Add `docs/consensus-v2-reference-evaluator.md` and `tests/consensus_v2/test_reference_evaluator.py` with fixed non-domain `unittest` fixtures. Test all exclusion causes, ties/boundaries, no-ranking failure, canonical repeats/traces, policy failures and import/side-effect guards.

## Dev Notes

- Story 11.2 owns parameter selection; 11.4 owns Go/ABCI/CometBFT; 11.5 owns state/persistence; 11.6 owns G3. Current upstream v2 artifacts are planning-only, so formal evaluation remains blocked. No numeric/mock/plant claim or UI scope is added.

## Mandatory Academic Evidence Amendment

Before implementation, apply the relevant mandatory controls in [Academic Evidence Admission Amendment — 2026-08-31](../planning-artifacts/academic-evidence-admission-amendment-2026-08-31.md). This story must fail closed on an unresolved evidence origin, numeric authority, required mock closure, or prohibited dataset substitution. The amendment adds no activity authorization.

## BMAD Party Mode Review

- Final Party review: product/PM `9.75`, architecture `9.80`, academic/QA `9.75`, all without veto; aggregate `9.77`. Auto-approved for `ready-for-dev`; planning approval grants no activity authorization.
