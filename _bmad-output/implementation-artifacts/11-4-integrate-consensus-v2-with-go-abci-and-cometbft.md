# Story 11.4: Integrate Consensus v2 With Go ABCI and CometBFT

Status: done

<!-- Planning approval does not authorize implementation, route activation, consensus execution, persistence, control, publication or dashboard work. -->

## Story

As a prototype operator, I want the real Go ABCI and CometBFT path to process consensus v2 rounds in shadow, so that the prototype's actual consensus boundary can be verified without claiming a qualified physical decision.

## Acceptance Criteria

1. Given an explicitly routed v2 transaction with exact immutable v2 schema/basis/profile/quality/parameter/observation identities, when the Go ABCI boundary decodes it, then strict versioned decoding validates schema, profile, basis, units, quality policy, parameter references, G2-qualified observation identities/hashes, sequences and correlation before evaluation; unknown, mixed, malformed and v1 payloads are rejected with no implicit conversion.
2. Given a valid v2 transaction containing only already G2-qualified immutable identifiers, when real CometBFT delivers it through the Go ABCI path, then the application uses the same closed canonical operation identity, exact numeric representation, comparison and failure rules as Story 11.3 and emits canonical `ConsensusDecision.v2` bytes through the bounded ABCI response/shadow boundary. It never resolves mutable external labels/current state, falls back on unavailable input, uses legacy scales/floats/defaults/engineering averages or treats the shadow artifact as a physical decision/result.
3. Given included/excluded contributions, when the ABCI result/event is emitted, then successful responses preserve complete canonical ranking, participants, exclusions/reasons, input hashes, parameter references and opaque correlation; failure emits explicit no-ranking failure, never success by omission. Durable v2 application keys, query, restart/replay and rollback evidence remain exclusively Story 11.5.
4. Given shared valid, invalid, boundary and failure fixture corpus, when offline Go codec/adapter fixtures run, then they establish byte/semantic parity only; a separately named opt-in isolated local CometBFT+ABCI transaction/commit/result-retrieval integration target using non-domain fixtures verifies exact v2 wire and canonical decision serialization, without ABCI Query or v2 application state. Mismatch keeps v2 shadow-only with bounded test/integration evidence, not durable v2 state. Only Story 11.6 records real-CometBFT G3 evidence; offline tests never claim it.
5. Given v2 promotion/rollback routing, when it changes, then Python contracts, Go types, transaction envelope, schemas and fixtures move as one exact versioned compatibility unit; neither language activates alone. Authorization/action validation is external and no route self-activates.
6. Given CometBFT, ABCI, MQTT, storage, analytics or presentation fails, when experiment control continues, then consensus reports unavailable/failed evidence only and has no actuator credential/conduit or command effect.

## Tasks / Subtasks

- [ ] Add an isolated parallel v2 boundary under the existing Go ABCI application, e.g. `abci/consensus_app/internal/app`, with strict v2 envelope discriminator, canonical Go v2 types/decoder and adapter to the frozen operation registry. Preserve v1 bytes, decoder, state and behavior unchanged; no v1-to-v2 conversion.
- [ ] Reject dynamic maps, unknown fields, float coercion, mutable aliases, mutable external resolution and unpinned schema/fixture/runtime identity. Do not write durable v2 state or implement Story 11.5 keys/query/restart/replay/rollback migration here.
- [ ] Add a shared versioned fixture corpus, ordinary offline Go codec/adapter tests, and a separately opt-in isolated local real-CometBFT+ABCI integration target. Default tests never start services; the opt-in target uses only non-domain fixtures/no physical-control activity. Test exact wire/canonical bytes, decoder/identity/basis/profile/unit/sequence/correlation failures, success/failure no-ranking, parity mismatch shadowing and no-control authority.
- [ ] Quarantine existing Go v1 `app.go` generic JSON/float/state behavior and Python legacy cometbft mapper/client; do not reuse their thresholds, state decoder or transport mapping. Pin existing Go/CometBFT dependencies; no upgrade/new dependency.
- [ ] Document `docs/consensus-v2-go-abci-integration.md` including exact shadow/activation boundary, v1 preservation, fixture parity and G3 limitation.

## Dev Notes

- Requires implemented/passing 11.1-11.3 and qualified physical/public inputs. Current artifacts are planning-only, so formal route activation is blocked. No new mock, domain value, UI/UX, truth, syscall, OPC, storage or control scope.
- Story 11.5 owns state/query/restart/rollback; Story 11.6 owns formal G3 qualification.

## Mandatory Academic Evidence Amendment

Before implementation, apply the relevant mandatory controls in [Academic Evidence Admission Amendment — 2026-08-31](../planning-artifacts/academic-evidence-admission-amendment-2026-08-31.md). This story must fail closed on an unresolved evidence origin, numeric authority, required mock closure, or prohibited dataset substitution. The amendment adds no activity authorization.

## BMAD Party Mode Review

- Final Party review: product/PM `9.65`, architecture `9.80`, academic/QA `9.80`, all without veto; aggregate `9.75`. Auto-approved for `ready-for-dev`; planning approval grants no activity authorization.

### References

- [Source: _bmad-output/planning-artifacts/epics.md#Story 11.4: Integrate Consensus v2 With Go ABCI and CometBFT]
- [Source: _bmad-output/planning-artifacts/architecture.md#Trust and authority boundaries]
- [Source: _bmad-output/implementation-artifacts/11-1-define-the-versioned-consensus-v2-contracts.md]
- [Source: _bmad-output/implementation-artifacts/11-3-implement-the-deterministic-python-consensus-reference.md]
