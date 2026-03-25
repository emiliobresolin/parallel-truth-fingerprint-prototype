# Story 2.1: Define Consensus Contracts and Trust-State Models

Status: review

<!-- Note: Validation is optional. Run validate-create-story for quality check before dev-story. -->

## Story

As a researcher,
I want explicit consensus contracts and trust-state models,
so that consensus outcomes are represented clearly and the system cannot confuse edge-local replicated state with validated state.

## Acceptance Criteria

1. Given the approved architecture constraints, when consensus-related contracts are implemented, then they include at least consensus round input, consensus result, trust ranking, exclusion details, and consensused valid state and the contracts keep edge-local replicated intermediate state distinct from consensused valid state.
2. Given the requirement for explicit auditability, when consensus-related contracts are implemented, then they carry a round-scoped identity model with round identifier and timestamp window consistently across consensus round input, trust ranking, exclusion decisions, and consensus result.
3. Given the requirement for explicit auditability, when a consensus result is produced, then it can represent both successful consensus and failed-consensus outcomes and it includes participating edges, excluded edges, typed reasons for exclusion, and explicit round status.
4. Given the prototype consensus architecture, when the contracts are defined, then they support independent consensus execution on each edge and they do not introduce any central authority, SCADA coupling, or comparison logic.
5. Given the consensus result invariants, when status is `success`, then consensused valid state must be present and when status is `failed_consensus`, then consensused valid state must be absent.

## Tasks / Subtasks

- [x] Define typed contracts for strict trust-state separation. (AC: 1, 4)
  - [x] Define a consensus round input contract that accepts only edge-local replicated state as input.
  - [x] Define a consensused valid state contract distinct from raw edge-local observation and edge-local replicated state.
  - [x] Keep all state types explicit so they cannot be confused in downstream code.
- [x] Define the round identity and status models. (AC: 2, 3, 5)
  - [x] Add an explicit round identity model with round identifier and timestamp window.
  - [x] Add an explicit enum-like consensus status contract limited to `success` and `failed_consensus`.
  - [x] Reuse the round identity consistently across consensus round input, trust ranking, exclusion decision, and consensus result.
- [x] Define the trust ranking and exclusion decision models. (AC: 1, 2, 3, 5)
  - [x] Add a typed trust ranking model for all participating edges in a round.
  - [x] Add a typed exclusion decision model that captures immediate exclusion per round, edge identity, typed primary reason, and optional detail.
  - [x] Keep exclusion decisions auditable and round-scoped.
- [x] Define the consensus result model, including failed-consensus as a first-class outcome. (AC: 1, 3, 5)
  - [x] Represent successful consensus and failed-consensus explicitly.
  - [x] Include participating edges, excluded edges, reasons for exclusion, trust ranking, and round status.
  - [x] Include consensused valid state only when consensus succeeds.
- [x] Align the contracts with the existing BBF-oriented consensus direction without implementing the algorithm yet. (AC: 4)
  - [x] Reuse the existing BBF/Byzantine reference from project artifacts as the conceptual basis for the contract shapes.
  - [x] Do not implement the consensus execution logic in this story.
  - [x] Keep the contract layer minimal and prototype-scoped.
- [x] Add focused tests for contract boundaries and failed-consensus representation. (AC: 1, 2, 3, 4, 5)
  - [x] Verify raw edge-local observation, edge-local replicated state, and consensused valid state remain distinct types.
  - [x] Verify failed-consensus can be represented without a consensused valid state.
  - [x] Verify exclusion decisions and trust rankings are auditable and round-scoped.
  - [x] Verify trust ranking references only participating edges for that round.
  - [x] Verify success/failure invariants tied to the explicit status contract.

## Dev Notes

- This story is contract-definition only. Do not implement the consensus algorithm itself here. That belongs to Story 2.2. [Source: [epics.md](/c:/Users/emili/Desktop/Projets/parallel-truth-fingerprint-prototype/_bmad-output/planning-artifacts/epics.md#L283)]
- Preserve the architectural separation exactly:
  - raw edge-local observation
  - edge-local replicated state
  - consensused valid state
  These must be different typed contracts, not aliases of one another. [Source: [architecture.md](/c:/Users/emili/Desktop/Projets/parallel-truth-fingerprint-prototype/_bmad-output/planning-artifacts/architecture.md#L518)]
- The consensus round input must be based only on edge-local replicated state. It must not accept raw observations directly, and it must not include SCADA/comparison concerns. [Source: [architecture.md](/c:/Users/emili/Desktop/Projets/parallel-truth-fingerprint-prototype/_bmad-output/planning-artifacts/architecture.md#L664)]
- Failed-consensus is a first-class outcome. The result model must represent it explicitly and must not include a consensused valid state in that case. [Source: [epics.md](/c:/Users/emili/Desktop/Projets/parallel-truth-fingerprint-prototype/_bmad-output/planning-artifacts/epics.md#L311)]
- Consensus must be executed independently on each edge later. These contracts must support decentralized execution and must not imply a central coordinator or authoritative consensus service. [Source: [docs/input/PROTOCOPO_ARCHITECTURE.md](/c:/Users/emili/Desktop/Projets/parallel-truth-fingerprint-prototype/docs/input/PROTOCOPO_ARCHITECTURE.md#L23)]
- The output must be explicitly auditable. Round-scoped trust ranking, exclusion decisions, reasons, and status need typed homes now so later stories can log them cleanly. [Source: [architecture.md](/c:/Users/emili/Desktop/Projets/parallel-truth-fingerprint-prototype/_bmad-output/planning-artifacts/architecture.md#L37)]
- Add a round identity model and carry it everywhere in the consensus contract layer. Round identifier plus timestamp window must be present in consensus round input, trust ranking, exclusion decision, and consensus result so auditability is guaranteed consistently.
- Consensus status must not be a loose string. Use a minimal explicit enum-like contract with only:
  - `success`
  - `failed_consensus`
- Exclusion reasons must not be free-form only. Use a minimal typed reason set such as:
  - `insufficient_data`
  - `inconsistent_view`
  - `trust_below_threshold`
  - `suspected_byzantine_behavior`
  An optional detail field may exist, but the primary reason must remain typed and bounded.
- Keep contract models minimal and serializable. Prefer simple dataclass-style models and standard-library Python only. Avoid unnecessary inheritance complexity.
- The user asked to try to use the existing BBF framework. No implemented BBF code was found in the current workspace, so this story should treat the existing BBF/Byzantine reference in the project documents as the design anchor for contract shape only, without adding a new framework or algorithm here.

### Project Structure Notes

- Primary implementation areas:
  - `src/parallel_truth_fingerprint/contracts/`
  - `tests/consensus/`
- Supporting areas if directly needed:
  - `src/parallel_truth_fingerprint/consensus/` only for minimal contract placement convenience, not algorithm logic
  - current edge-state contract files and helpers for reference
- Do not touch:
  - `scada/`
  - `comparison/`
  - `persistence/`
  - `lstm_service/`
- Keep the contract boundary clean so Story 2.2 can implement execution logic on top of it later.

### Technical Requirements

- Define typed contracts for:
  - round identity
  - consensus round input
  - trust ranking
  - exclusion decision
  - consensus result
  - consensused valid state
- Consensus round input must accept only edge-local replicated state.
- Every consensus-related contract must carry the round identity.
- Exclusion decisions must be immediate and round-specific.
- Exclusion reasons must use a bounded typed reason set with optional detail.
- Consensus status must use an explicit limited status model:
  - `success`
  - `failed_consensus`
- Consensus result must support:
  - success with consensused valid state
  - failed-consensus without consensused valid state
- Invariants must hold:
  - if status is `success`, consensused valid state must be present
  - if status is `failed_consensus`, consensused valid state must be absent
  - exclusion decisions must always be round-scoped
  - trust ranking must reference only participating edges for that round
- Contracts must be auditable and easy to serialize/log later.
- Keep the contract set minimal and prototype-scoped.

### Architecture Compliance

- No central authority may be implied by these contracts.
- No SCADA or comparison logic may appear in these contracts.
- No persistence or LSTM semantics may appear in these contracts.
- These contracts must preserve validation-before-trust by keeping edge-local replicated state separate from consensused valid state.
- The contract design must support later independent execution on each edge.

### Library / Framework Requirements

- Stay within the current local Python project structure.
- Use standard-library Python only unless an existing project dependency is clearly required.
- Do not add any new consensus framework dependency in this story.
- Use the existing BBF/Byzantine project reference as conceptual guidance only.

### File Structure Requirements

- Prefer adding contract files such as:
  - `src/parallel_truth_fingerprint/contracts/round_identity.py`
  - `src/parallel_truth_fingerprint/contracts/consensus_round_input.py`
  - `src/parallel_truth_fingerprint/contracts/trust_ranking.py`
  - `src/parallel_truth_fingerprint/contracts/exclusion_decision.py`
  - `src/parallel_truth_fingerprint/contracts/consensus_result.py`
  - `src/parallel_truth_fingerprint/contracts/consensused_valid_state.py`
  - optionally `src/parallel_truth_fingerprint/contracts/consensus_status.py`
  - optionally `src/parallel_truth_fingerprint/contracts/exclusion_reason.py`
- Keep names aligned with the approved architecture.

### Testing Requirements

- Add focused contract tests only.
- Validate:
  - strict state-type separation
  - round identity propagation across contracts
  - explicit bounded status model
  - explicit bounded exclusion-reason model
  - explicit failed-consensus representation
  - auditable trust ranking and exclusion models
- Do not write tests for SCADA, comparison, persistence, or LSTM in this story.

### Previous Story Intelligence

- Epic 1 implementation now provides:
  - raw edge-local observation payloads
  - edge-local replicated state reconstruction
  - observation-flow logging and runtime/demo MQTT support
- Story 2.1 must build the next trust boundary on top of those outputs, not reinterpret them.
- The current upstream code already treats edge-local replicated state as intermediate and non-validated. Preserve that semantics in the new contracts.

### Git Intelligence Summary

- Most recent commit titles:
  - `Story 1.5 MQTT`
  - `Stroy 1.3 and 1.4`
  - `Stroy 1.2`
- The implemented codebase now has a clear upstream boundary. Story 2.1 should define the contract boundary immediately downstream of that, before any consensus execution logic is added.

### References

- Story definition and acceptance criteria: [epics.md](/c:/Users/emili/Desktop/Projets/parallel-truth-fingerprint-prototype/_bmad-output/planning-artifacts/epics.md#L260)
- Consensus input / output requirements: [architecture.md](/c:/Users/emili/Desktop/Projets/parallel-truth-fingerprint-prototype/_bmad-output/planning-artifacts/architecture.md#L191)
- Trust-boundary separation: [architecture.md](/c:/Users/emili/Desktop/Projets/parallel-truth-fingerprint-prototype/_bmad-output/planning-artifacts/architecture.md#L518)
- Auditability requirements: [architecture.md](/c:/Users/emili/Desktop/Projets/parallel-truth-fingerprint-prototype/_bmad-output/planning-artifacts/architecture.md#L37)
- Byzantine consensus execution reference: [PROTOCOPO_ARCHITECTURE.md](/c:/Users/emili/Desktop/Projets/parallel-truth-fingerprint-prototype/docs/input/PROTOCOPO_ARCHITECTURE.md#L23)

## Dev Agent Record

### Agent Model Used

GPT-5 Codex

### Debug Log References

- Story created from Epic 2, Story 2.1 with explicit state-separation constraints from the user.
- No sprint-status file exists yet.
- Existing BBF/Byzantine reference was found in project docs, but no implemented BBF code exists in the current workspace.
- `venv\\Scripts\\python -m unittest tests.consensus.test_consensus_contracts`
- `venv\\Scripts\\python -m unittest discover -s tests`

### Completion Notes List

- Ultimate context engine analysis completed - comprehensive developer guide created.
- Added explicit dataclass-style contracts for round identity, consensus round input, trust ranking, exclusion decision, consensus result, and consensused valid state.
- Added bounded enum-style models for consensus status and exclusion reasons using standard-library Python only.
- Enforced invariants so successful consensus requires a consensused valid state and failed consensus forbids it.
- Kept consensus round input restricted to edge-local replicated state and avoided any SCADA, comparison, persistence, or LSTM coupling.
- Preserved decentralized semantics by keeping the contracts edge-execution-friendly and free of any central-authority assumptions.
- Added focused consensus contract tests for state separation, round identity propagation, bounded status/reason models, failed-consensus representation, and trust/exclusion auditability.

### File List

- `_bmad-output/implementation-artifacts/2-1-define-consensus-contracts-and-trust-state-models.md`
- `src/parallel_truth_fingerprint/contracts/__init__.py`
- `src/parallel_truth_fingerprint/contracts/consensus_result.py`
- `src/parallel_truth_fingerprint/contracts/consensus_round_input.py`
- `src/parallel_truth_fingerprint/contracts/consensus_status.py`
- `src/parallel_truth_fingerprint/contracts/consensused_valid_state.py`
- `src/parallel_truth_fingerprint/contracts/edge_local_replicated_state.py`
- `src/parallel_truth_fingerprint/contracts/exclusion_decision.py`
- `src/parallel_truth_fingerprint/contracts/exclusion_reason.py`
- `src/parallel_truth_fingerprint/contracts/round_identity.py`
- `src/parallel_truth_fingerprint/contracts/trust_ranking.py`
- `tests/consensus/__init__.py`
- `tests/consensus/test_consensus_contracts.py`

### Change Log

- 2026-03-25: Implemented Story 2.1 consensus contracts, bounded status/reason models, invariants, and focused contract tests.
