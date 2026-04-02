# Story 4.2A: Persist Inspectable Training Dataset Artifacts and Establish Normal-History Adequacy

Status: review

<!-- Note: Validation is optional. Run validate-create-story for quality check before dev-story. -->

## Story

As a researcher,
I want the normal-only temporal dataset to be persisted as an inspectable MinIO artifact and evaluated against an explicit adequacy gate,
so that the fingerprint path is reproducible, auditable, reusable, and academically honest before inference work begins.

## Rationale

- Story 4.1 owns dataset-building logic.
- Story 4.2 proved the runtime-valid training path, but it used the in-memory dataset output and a minimal smoke corpus.
- This corrective story makes the dataset explicit as a reusable prototype artifact and records whether the current dataset is only runtime-valid or also meaningful enough to support a stronger fingerprint claim.

## Scope Notes

- This story is limited to persisted dataset artifacts and adequacy evaluation.
- It builds on Story 4.1 outputs and does not replace Story 4.1 dataset-building logic.
- It must use the existing MinIO storage boundary.
- It must not add:
  - LSTM inference
  - anomaly scoring
  - replay detection logic
  - UI behavior
  - a new storage service
  - architecture redesign

## Acceptance Criteria

1. Given the in-memory dataset output from Story 4.1, when Story 4.2A executes, then it persists a real dataset artifact to MinIO rather than leaving the dataset only in memory.
2. Given the approved storage boundary, when the dataset artifact is written, then it uses the existing MinIO path under a dedicated dataset prefix and the preferred representation is:
   - `fingerprint-datasets/<dataset_id>.manifest.json`
   - `fingerprint-datasets/<dataset_id>.windows.npz`
3. Given the need for transparency and reproducibility, when the dataset manifest is persisted, then it records at least:
   - dataset id
   - creation timestamp
   - source bucket and source prefix
   - chronological ordering rule
   - sequence length
   - stride
   - overlap behavior
   - feature schema
   - selected artifact keys
   - skipped artifact keys and reasons
   - eligible artifact count
   - generated window count
   - tensor shape
   - training label or dataset purpose
4. Given the need for temporal reuse, when the windows artifact is persisted, then it stores the generated temporal windows in a reusable form and preserves the mapping between windows and their artifact keys, round ids, and timestamps.
5. Given the academic-strength requirement, when dataset adequacy is evaluated, then the system distinguishes between:
   - runtime-valid dataset generation
   - meaningful fingerprint-valid dataset adequacy
   and records the current adequacy status explicitly.
6. Given the prototype-default adequacy floor, when adequacy is evaluated, then the default floor is at least:
   - 30 eligible normal persisted artifacts
   - 20 generated windows
   and the result is recorded explicitly in the dataset manifest or directly associated metadata.
7. Given the project testing rule, when Story 4.2A is closed, then the story record explicitly includes:
   - what was tested
   - exact commands executed
   - test results
   - real runtime behavior validated
   - remaining limitations
8. Given focused validation, when Story 4.2A tests are run, then they prove:
   - MinIO-backed dataset artifact persistence
   - manifest inspectability
   - reusable windows artifact generation
   - chronology and eligibility traceability
   - adequacy gate evaluation
   - exclusion of invalid, failed-consensus, replay, faulty-edge, or SCADA-divergent records

## Testing Requirements

- Testing is mandatory for this story.
- The story is incomplete unless it includes:
  - focused tests for dataset artifact generation and adequacy evaluation
  - exact commands used to run those tests
  - reported results
  - a real runtime validation pass proving the dataset artifact is written to MinIO and can be inspected
  - a limitations note stating whether the adequacy floor was met or not met

## Dependencies

- Story 4.1 normal-only dataset-building logic
- Existing MinIO-backed persistence boundary
- Existing validated persisted artifact contract

## Non-Goals

- no LSTM inference
- no anomaly score generation
- no replay detection logic
- no UI changes
- no new storage system
- no architecture redesign
- no production-grade dataset platform

## Tasks / Subtasks

- [x] Define the persisted dataset-manifest contract. (AC: 2, 3, 5, 6, 8)
- [x] Define the reusable windows-artifact contract. (AC: 2, 4, 8)
- [x] Implement MinIO-backed dataset artifact persistence under `fingerprint-datasets/`. (AC: 1, 2, 8)
- [x] Implement explicit adequacy evaluation and adequacy-status recording. (AC: 5, 6, 8)
- [x] Add focused Story 4.2A tests plus one real runtime validation pass. (AC: 7, 8)

## Technical Notes

- The preferred persisted dataset representation is:
  - `fingerprint-datasets/<dataset_id>.manifest.json`
  - `fingerprint-datasets/<dataset_id>.windows.npz`
- Story 4.2A must preserve the existing MinIO boundary and must not introduce a second dataset-storage path.
- Story 4.2A makes the dataset inspectable and reusable without changing the dataset-building ownership established in Story 4.1.
- Story 4.2 revalidation depends on the persisted dataset path produced here.

## Real vs Simulated Boundary

- Real in this story:
  - MinIO-backed dataset artifact persistence
  - adequacy evaluation
  - inspectable reusable dataset outputs
- Simulated or mock around this story:
  - compressor/process behavior that produced the upstream validated artifacts
  - scenario generation that labels runs as normal or non-normal
- Conceptual only for later stories:
  - runtime inference
  - replay detection output
  - UI integration

## Academic Mapping

- This story upgrades the temporal learning substrate from an in-memory builder result into a real inspectable dataset artifact.
- It makes chronology, eligibility, and adequacy visible enough for academic explanation and reuse.
- It prevents a minimal smoke corpus from being misrepresented as a substantively meaningful fingerprint dataset.

## Dev Agent Record

### Agent Model Used

GPT-5 Codex

### Debug Log References

- Story implemented after the approved Epic 4 corrective planning pass.
- Runtime validation required bringing local MinIO up after Docker Desktop was reopened.

### Completion Notes List

- Added typed dataset-artifact contracts for persisted dataset metadata and adequacy assessment.
- Implemented MinIO-backed dataset artifact persistence under `fingerprint-datasets/`.
- Persisted two inspectable dataset outputs:
  - `fingerprint-datasets/<dataset_id>.manifest.json`
  - `fingerprint-datasets/<dataset_id>.windows.npz`
- Added explicit adequacy evaluation with the approved prototype-default floor:
  - minimum 30 eligible normal persisted artifacts
  - minimum 20 generated windows
- Added focused tests proving:
  - dataset artifact generation
  - adequacy evaluation
  - exclusion of replay, faulty-edge, SCADA-divergent, failed-consensus, and missing-context records
- Added a gated real MinIO smoke test that writes and reads the persisted dataset artifacts through the live storage path.
- Runtime validation confirmed that the smoke dataset is `runtime_valid_only` and does not meet the meaningful-fingerprint adequacy floor.
- Story 4.3 remains blocked.

### What Was Tested

- Focused Story 4.2A dataset-artifact tests
- Existing Story 4.1 dataset-builder tests
- Existing persistence tests for the valid-artifact boundary
- Full regression suite
- Real MinIO-backed smoke validation for manifest and `.npz` dataset writes

### Exact Commands Executed

```powershell
venv\Scripts\uv.exe sync --extra ml-training
docker compose -f compose.local.yml up -d minio

$env:PYTHONPATH='src'
.\.venv\Scripts\python -m unittest tests.lstm_service.test_dataset_artifacts
.\.venv\Scripts\python -m unittest tests.lstm_service.test_dataset_builder
.\.venv\Scripts\python -m unittest tests.persistence.test_service
.\.venv\Scripts\python -m unittest discover -s tests

$env:RUN_REAL_DATASET_ARTIFACT_SMOKE='1'
.\.venv\Scripts\python -m unittest tests.lstm_service.test_dataset_artifacts_runtime_smoke

@'
from minio import Minio
client = Minio('localhost:9000', access_key='minioadmin', secret_key='minioadmin', secure=False)
buckets = sorted([bucket.name for bucket in client.list_buckets() if bucket.name.startswith('fingerprint-datasets-smoke-')])
print('LATEST_BUCKET', buckets[-1])
print('OBJECTS', sorted(obj.object_name for obj in client.list_objects(buckets[-1], recursive=True)))
'@ | .\.venv\Scripts\python -
```

### Test Results

- `tests.lstm_service.test_dataset_artifacts` -> `Ran 3 tests` -> `OK`
- `tests.lstm_service.test_dataset_builder` -> `Ran 4 tests` -> `OK`
- `tests.persistence.test_service` -> `Ran 3 tests` -> `OK`
- `python -m unittest discover -s tests` -> `Ran 92 tests` -> `OK (skipped=2)`
- `tests.lstm_service.test_dataset_artifacts_runtime_smoke` -> `Ran 1 test` -> `OK`

### Real Runtime Behavior Validated

- Local MinIO was reachable on `localhost:9000`.
- The real storage path wrote the dataset manifest JSON to MinIO under `fingerprint-datasets/`.
- The real storage path wrote the reusable windows archive to MinIO under `fingerprint-datasets/`.
- The persisted manifest was immediately inspectable through the live MinIO API.
- The persisted `.npz` windows artifact was immediately readable back through the live MinIO API.
- The runtime smoke bucket contained:
  - 4 upstream valid-artifact JSON objects under `valid-consensus-artifacts/`
  - 2 generated dataset-artifact objects under `fingerprint-datasets/`
- The replay-labeled artifact was excluded from the persisted dataset manifest with reason `training_label_not_normal`.
- The live manifest recorded `validation_level=runtime_valid_only` and `adequacy_met=false`.

### Remaining Limitations

- The runtime smoke corpus remained intentionally small:
  - 3 eligible normal persisted artifacts
  - 2 generated windows
  - tensor shape `[2, 2, 27]`
- The default adequacy floor was not met:
  - required 30 eligible artifacts
  - required 20 generated windows
- Story 4.2 still requires revalidation against the persisted dataset artifact path produced here.
- Story 4.3 remains blocked until `4.1 -> 4.2A -> 4.2 revalidation` is complete.

### File List

- `_bmad-output/implementation-artifacts/4-2a-persist-inspectable-training-dataset-artifacts-and-establish-normal-history-adequacy.md`
- `README.md`
- `pyproject.toml`
- `uv.lock`
- `src/parallel_truth_fingerprint/contracts/__init__.py`
- `src/parallel_truth_fingerprint/contracts/dataset_artifact.py`
- `src/parallel_truth_fingerprint/lstm_service/__init__.py`
- `src/parallel_truth_fingerprint/lstm_service/dataset_artifacts.py`
- `tests/lstm_service/test_dataset_artifacts.py`
- `tests/lstm_service/test_dataset_artifacts_runtime_smoke.py`
