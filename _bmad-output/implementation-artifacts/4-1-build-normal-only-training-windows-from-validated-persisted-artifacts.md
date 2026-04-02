# Story 4.1: Build Normal-Only Training Windows From Validated Persisted Artifacts

Status: review

<!-- Note: Validation is optional. Run validate-create-story for quality check before dev-story. -->

## Story

As a researcher,
I want training-ready temporal windows built only from validated persisted artifacts,
so that the fingerprint learns physical-operational behavior from the real trusted prototype pipeline.

## Scope Notes

- This story is limited to dataset-building for Epic 4.
- It must read only persisted `ValidConsensusArtifactRecord` objects from the MinIO-backed runtime storage path.
- One persisted valid artifact corresponds to one timestep in the temporal dataset builder.
- The dataset builder must select only normal eligible records for training.
- The core fingerprint input must stay tied to the current validated payload-driven prototype output.
- This story must not add:
  - LSTM training
  - inference
  - anomaly scoring
  - replay detection logic
  - UI behavior

## Acceptance Criteria

1. Given persisted valid artifacts in MinIO, when the dataset-building process runs, then it reads only validated `ValidConsensusArtifactRecord` inputs from the approved runtime storage boundary and does not consume raw observations, edge-local replicated state, or failed-consensus outputs.
2. Given the current payload-driven architecture, when fingerprint features are extracted, then the dataset builder derives them from the validated structured payload snapshot already stored in the persisted artifact, including per-sensor `PV.value`, `loop_current_ma`, `pv_percent_range`, `physics_metrics`, and transmitter diagnostics when present.
3. Given the approved modeling boundary, when dataset features are selected, then consensus metadata, trust ranking, exclusions, trust evidence, and SCADA divergence context are retained for traceability and eligibility but are not treated as the core fingerprint feature vector unless explicitly re-approved later.
4. Given the normal-only training rule, when candidate records are filtered for training, then only scenario-labeled normal validated artifacts are accepted and replay, faulty-edge, SCADA-divergence, failed-consensus, or otherwise non-normal runs are excluded from the training set.
5. Given the temporal nature of the fingerprint objective, when the builder emits training data, then it produces deterministic fixed-length chronological windows and a dataset manifest that records the selected artifacts, feature schema, sequence length, and eligibility decisions.
6. Given focused validation, when Story 4.1 tests are run, then they prove:
   - MinIO-backed valid artifact loading
   - normal-only eligibility filtering
   - deterministic feature extraction from the structured payload snapshot
   - fixed-length window generation
   - manifest traceability

## Dependencies

- Story 3.4 persisted valid artifacts in MinIO
- Story 3.5 runtime/log visibility for persisted artifacts
- Current `ValidConsensusArtifactRecord` contract

## Tasks / Subtasks

- [x] Define the Epic 4.1 dataset-building contracts. (AC: 1, 2, 3, 5, 6)
  - [x] Define the training-window record shape.
  - [x] Define the dataset manifest shape.
- [x] Implement MinIO-backed valid artifact loading for dataset-building. (AC: 1, 6)
  - [x] Read persisted valid artifacts from the configured bucket.
  - [x] Keep the loader deterministic and local-demo friendly.
- [x] Implement normal-only eligibility filtering. (AC: 3, 4, 6)
  - [x] Reject non-normal scenario runs.
  - [x] Reject failed-consensus or otherwise non-validated inputs.
- [x] Implement feature extraction from the structured validated payload snapshot. (AC: 2, 3, 6)
  - [x] Extract per-sensor physical-operational features.
  - [x] Keep traceability metadata separate from the core feature vector.
- [x] Implement fixed-length chronological window generation plus manifest output. (AC: 5, 6)
  - [x] Emit deterministic temporal windows.
  - [x] Persist or expose a dataset manifest for auditability.
- [x] Add focused Story 4.1 tests and preserve regression stability. (AC: 6)

## Technical Notes

- Epic 4 technical decision: use `keras` with the `torch` backend for the downstream LSTM implementation.
- This story does not train a model yet, but its outputs must already be compatible with that stack.
- This explicit `keras + torch backend` decision replaces any prior implicit assumption that Epic 4 would use a TensorFlow-backed Keras path. The current repository did not lock an explicit TensorFlow requirement before this decision.
- Backend configuration rule for later stories: set `KERAS_BACKEND=torch` before importing `keras`.
- The core fingerprint feature vector should come from:
  - `validated_state.structured_payload_snapshot.payloads_by_sensor`
  - `process_data.pv`
  - `process_data.loop_current_ma`
  - `process_data.pv_percent_range`
  - `process_data.physics_metrics`
  - `diagnostics`
- Traceability-only or eligibility-supporting fields may include:
  - `artifact_identity`
  - `round_identity`
  - `consensus_context`
  - `scada_context`
  - scenario labels or dataset manifest labels
- One persisted valid artifact equals one timestep. Fixed-length windows should be built chronologically from that sequence of timesteps.
- Keep the implementation local, simple, and reviewable. Do not introduce external training infrastructure or a second storage path.

## Real vs Simulated Boundary

- Real in this story:
  - MinIO-backed artifact loading
  - dataset-building logic
  - deterministic feature extraction
  - temporal window generation
  - manifest generation
- Simulated or mock around this story:
  - compressor/process behavior that produced the upstream validated artifacts
  - scenario generation used to label runs as normal or non-normal
- Conceptual only for later stories:
  - actual LSTM training
  - inference
  - replay detection output
  - UI integration

## Academic Mapping

- This story converts validated physical-operational records into the temporal learning substrate required for physical-operational fingerprint generation.
- It preserves the methodological rule that only trusted validated data may move into the learning path.
- It keeps the fingerprint tied to physical-operational behavior rather than to SCADA-only mismatch summaries or consensus-only metadata.

## Dev Notes

- Story 4.1 must build directly on the rich validated artifact shape now persisted to MinIO.
- Do not flatten the dataset to a value-only CSV-style view unless that flattening is a deterministic internal feature-matrix step derived from the richer structured record.
- Do not allow replay, faulty-edge, SCADA-divergence, or failed-consensus records into the normal-only training set.
- Do not start LSTM training in this story.

## Dev Agent Record

### Agent Model Used

GPT-5 Codex

### Debug Log References

- Story created from the approved Epic 4 direction after the explicit input-boundary and ML-stack revisions.

### Completion Notes List

- Standalone Story 4.1 artifact created and implemented.
- Added typed training-window and dataset-manifest contracts.
- Added MinIO-backed JSON listing/loading support to the artifact store for dataset-building.
- Implemented deterministic normal-only dataset-building from persisted valid artifacts.
- Added explicit dataset-context metadata to persisted artifacts so normal-only eligibility is real instead of inferred.
- Added focused Story 4.1 tests and preserved full regression stability.

### File List

- `_bmad-output/implementation-artifacts/4-1-build-normal-only-training-windows-from-validated-persisted-artifacts.md`
- `src/parallel_truth_fingerprint/contracts/persistence_record.py`
- `src/parallel_truth_fingerprint/contracts/training_dataset.py`
- `src/parallel_truth_fingerprint/contracts/__init__.py`
- `src/parallel_truth_fingerprint/persistence/artifact_store.py`
- `src/parallel_truth_fingerprint/persistence/service.py`
- `src/parallel_truth_fingerprint/lstm_service/__init__.py`
- `src/parallel_truth_fingerprint/lstm_service/dataset_builder.py`
- `scripts/run_local_demo.py`
- `tests/persistence/test_service.py`
- `tests/test_runtime_demo.py`
- `tests/lstm_service/__init__.py`
- `tests/lstm_service/test_dataset_builder.py`
