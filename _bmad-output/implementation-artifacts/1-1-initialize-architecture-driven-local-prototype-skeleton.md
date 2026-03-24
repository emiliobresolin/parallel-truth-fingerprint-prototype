# Story 1.1: Initialize the Architecture-Driven Local Prototype Skeleton

Status: done

<!-- Note: Validation is optional. Run validate-create-story for quality check before dev-story. -->

## Story

As a researcher,
I want the local prototype skeleton initialized with the approved architecture-driven structure,
so that implementation starts from a reproducible foundation without introducing unintended framework constraints.

## Acceptance Criteria

1. Given the approved architecture and execution model, when the project is initialized, then it uses `uv init --bare` as the bootstrap approach and the repository structure reflects the defined logical service boundaries for edges, consensus, SCADA, comparison, persistence, LSTM, observability, scenario control, and optional minimal visualization.
2. Given the mixed local reproducibility model, when local orchestration files are created, then they allow MQTT broker containerization and optional MinIO/LSTM containerization and they do not change the architecture into a centralized or production-style deployment.

## Tasks / Subtasks

- [x] Bootstrap the Python project with `uv init --bare` and keep the bootstrap minimal. (AC: 1)
  - [x] Initialize `pyproject.toml` without adopting a framework starter or monolithic app scaffold.
  - [x] Keep the bootstrap focused on project metadata and dependency management only.
- [x] Create the architecture-driven source and support directory skeleton under the approved root layout. (AC: 1)
  - [x] Add the top-level directories required by the architecture: `src/parallel_truth_fingerprint/`, `tests/`, and `scripts/`.
  - [x] Under `src/parallel_truth_fingerprint/`, create the approved boundary folders: `config`, `contracts`, `sensor_simulation`, `edge_nodes`, `consensus`, `scada`, `comparison`, `persistence`, `lstm_service`, `observability`, `scenario_control`, and `visualization`.
  - [x] Add the edge-node substructure required by the architecture: `edge_nodes/common`, `edge_nodes/edge_1`, `edge_nodes/edge_2`, and `edge_nodes/edge_3`.
  - [x] Create minimal placeholder modules or package markers only where needed to preserve the agreed structure without inventing behavior.
- [x] Add local reproducibility scaffolding for mixed process/container orchestration. (AC: 2)
  - [x] Create `compose.local.yml` with a local MQTT broker service.
  - [x] Structure the compose file so MinIO and LSTM can be added as optional local services later without changing the architecture.
  - [x] Keep edge nodes and core orchestration as regular local Python-process responsibilities rather than container-only services.
- [x] Add initial project-level documentation and configuration stubs needed for the implementation flow. (AC: 1, 2)
  - [x] Add `.env.example` for local configuration placeholders.
  - [x] Add `.gitignore` suited to local Python/uv work and local artifact generation.
  - [x] Add `README.md` with a short bootstrap-oriented description of how local execution is intended to work at a high level.
- [x] Validate that the scaffold preserves architecture invariants. (AC: 1, 2)
  - [x] Confirm the structure does not collapse logical service boundaries.
  - [x] Confirm the bootstrap does not pre-implement business logic, consensus logic, payload logic, or ML logic.
  - [x] Confirm the execution model remains fully local and reproducibility-oriented only.

## Dev Notes

- This is a greenfield bootstrap story. Keep it strictly limited to initialization, structure, and reproducibility scaffolding.
- Do not implement sensor logic, edge logic, consensus logic, SCADA logic, persistence logic, or LSTM behavior here. Those belong to later stories in Epic 1 and later epics. [Source: [epics.md](/c:/Users/emili/Desktop/Projets/parallel-truth-fingerprint-prototype/_bmad-output/planning-artifacts/epics.md#L145)]
- The architecture explicitly requires `uv init --bare` as the starter decision and treats that as the first implementation priority. [Source: [architecture.md](/c:/Users/emili/Desktop/Projets/parallel-truth-fingerprint-prototype/_bmad-output/planning-artifacts/architecture.md#L115)]
- The project must remain architecture-driven, modular, local, and simple. Avoid adding framework opinionation, deployment platforms, or production-oriented orchestration. [Source: [prd.md](/c:/Users/emili/Desktop/Projets/parallel-truth-fingerprint-prototype/_bmad-output/planning-artifacts/prd.md#L495)] [Source: [prd.md](/c:/Users/emili/Desktop/Projets/parallel-truth-fingerprint-prototype/_bmad-output/planning-artifacts/prd.md#L504)] [Source: [prd.md](/c:/Users/emili/Desktop/Projets/parallel-truth-fingerprint-prototype/_bmad-output/planning-artifacts/prd.md#L508)] [Source: [prd.md](/c:/Users/emili/Desktop/Projets/parallel-truth-fingerprint-prototype/_bmad-output/planning-artifacts/prd.md#L511)]
- Mixed local process/container orchestration is allowed only as a reproducibility choice. It must not become an architectural redesign. MQTT broker should be containerized locally; MinIO and LSTM may be containerized later if useful. [Source: [architecture.md](/c:/Users/emili/Desktop/Projets/parallel-truth-fingerprint-prototype/_bmad-output/planning-artifacts/architecture.md#L750)]
- There is no `sprint-status.yaml`, no `project-context.md`, and no git history available in this workspace. Do not assume prior implementation artifacts exist.

### Project Structure Notes

- Use the approved directory skeleton from the architecture as the source of truth for file placement. The target structure includes:
  - `src/parallel_truth_fingerprint/app.py`
  - `src/parallel_truth_fingerprint/config/`
  - `src/parallel_truth_fingerprint/contracts/`
  - `src/parallel_truth_fingerprint/sensor_simulation/`
  - `src/parallel_truth_fingerprint/edge_nodes/common/`
  - `src/parallel_truth_fingerprint/edge_nodes/edge_1/`
  - `src/parallel_truth_fingerprint/edge_nodes/edge_2/`
  - `src/parallel_truth_fingerprint/edge_nodes/edge_3/`
  - `src/parallel_truth_fingerprint/consensus/`
  - `src/parallel_truth_fingerprint/scada/`
  - `src/parallel_truth_fingerprint/comparison/`
  - `src/parallel_truth_fingerprint/persistence/`
  - `src/parallel_truth_fingerprint/lstm_service/`
  - `src/parallel_truth_fingerprint/observability/`
  - `src/parallel_truth_fingerprint/scenario_control/`
  - `src/parallel_truth_fingerprint/visualization/`
  - `tests/`
  - `scripts/`
  - `compose.local.yml`
- Preserve service ownership from the beginning. This story should make it harder, not easier, to blur edge, consensus, SCADA, persistence, and LSTM boundaries. [Source: [architecture.md](/c:/Users/emili/Desktop/Projets/parallel-truth-fingerprint-prototype/_bmad-output/planning-artifacts/architecture.md#L542)]

### Technical Requirements

- Bootstrap command: `uv init --bare`. Use the official minimal initialization mode; do not replace it with a heavier starter. [Source: [architecture.md](/c:/Users/emili/Desktop/Projets/parallel-truth-fingerprint-prototype/_bmad-output/planning-artifacts/architecture.md#L115)] [Source: https://docs.astral.sh/uv/reference/cli/#uv-init]
- Dependency and project management should be centered on `uv` and `pyproject.toml`.
- The bootstrap must leave room for local Python processes plus local containerized infrastructure, with Docker Compose used only to start the local infrastructure services. [Source: https://docs.docker.com/reference/cli/docker/compose/up/]

### Architecture Compliance

- Preserve decentralized logical boundaries even though execution is local.
- Do not add any shared global runtime pattern that implies centralized execution.
- Do not pre-create data-flow shortcuts across service boundaries.
- Do not pre-bake consensus, persistence, or ML assumptions into the bootstrap.
- Keep the structure compatible with later explicit payload, trust-state, and scenario-control boundaries from the architecture and epics.

### Library / Framework Requirements

- Required now:
  - `uv` for project initialization and dependency management.
- Allowed orchestration support:
  - Docker Compose for local infrastructure startup only.
- Do not add web frameworks, ORM layers, task queues, or ML runtimes in this story unless they are strictly needed to complete the skeleton, which they should not be.

### File Structure Requirements

- Create files only where they support the agreed bootstrap structure.
- Prefer lightweight package markers and placeholders over speculative implementations.
- The compose file should name infrastructure services clearly and keep them aligned with the architecture:
  - MQTT broker required now
  - MinIO optional later
  - LSTM service optional later

### Testing Requirements

- Validate the scaffold structurally rather than behaviorally.
- Minimum checks for this story:
  - the expected directory structure exists
  - `pyproject.toml` exists and reflects `uv` initialization
  - `compose.local.yml` exists and includes the MQTT broker service
  - no unintended production framework or centralized service layout was introduced
- If you add tests, keep them limited to bootstrap/configuration sanity checks.

### References

- Story definition and acceptance criteria: [epics.md](/c:/Users/emili/Desktop/Projets/parallel-truth-fingerprint-prototype/_bmad-output/planning-artifacts/epics.md#L145)
- Starter requirement: [architecture.md](/c:/Users/emili/Desktop/Projets/parallel-truth-fingerprint-prototype/_bmad-output/planning-artifacts/architecture.md#L115)
- Approved project structure: [architecture.md](/c:/Users/emili/Desktop/Projets/parallel-truth-fingerprint-prototype/_bmad-output/planning-artifacts/architecture.md#L542)
- Execution model and mixed local orchestration: [architecture.md](/c:/Users/emili/Desktop/Projets/parallel-truth-fingerprint-prototype/_bmad-output/planning-artifacts/architecture.md#L750)
- Local, modular, simple constraints: [prd.md](/c:/Users/emili/Desktop/Projets/parallel-truth-fingerprint-prototype/_bmad-output/planning-artifacts/prd.md#L495) [prd.md](/c:/Users/emili/Desktop/Projets/parallel-truth-fingerprint-prototype/_bmad-output/planning-artifacts/prd.md#L499) [prd.md](/c:/Users/emili/Desktop/Projets/parallel-truth-fingerprint-prototype/_bmad-output/planning-artifacts/prd.md#L504) [prd.md](/c:/Users/emili/Desktop/Projets/parallel-truth-fingerprint-prototype/_bmad-output/planning-artifacts/prd.md#L508) [prd.md](/c:/Users/emili/Desktop/Projets/parallel-truth-fingerprint-prototype/_bmad-output/planning-artifacts/prd.md#L511)
- Official `uv init` CLI reference: https://docs.astral.sh/uv/reference/cli/#uv-init
- Official Docker Compose `up` reference: https://docs.docker.com/reference/cli/docker/compose/up/

## Dev Agent Record

### Agent Model Used

GPT-5 Codex

### Debug Log References

- No sprint status file found.
- No project-context file found.
- Git history unavailable because the workspace is not a git repository.

### Completion Notes List

- Story implemented with `uv init --bare` after installing `uv` into the local virtual environment.
- Approved source tree skeleton created under `src/parallel_truth_fingerprint/` with placeholder package markers only.
- Added `contracts/samples/` payload reference area and copied the raw HART and unified payload samples from `docs/input/`.
- Added `compose.local.yml`, `.env.example`, `.gitignore`, `README.md`, and infrastructure/documentation stubs.
- No business logic was implemented.

### File List

- `.env.example`
- `.gitignore`
- `README.md`
- `compose.local.yml`
- `docs/infrastructure/mosquitto.conf`
- `pyproject.toml`
- `scripts/README.md`
- `tests/README.md`
- `src/parallel_truth_fingerprint/__init__.py`
- `src/parallel_truth_fingerprint/app.py`
- `src/parallel_truth_fingerprint/comparison/__init__.py`
- `src/parallel_truth_fingerprint/config/__init__.py`
- `src/parallel_truth_fingerprint/consensus/__init__.py`
- `src/parallel_truth_fingerprint/contracts/__init__.py`
- `src/parallel_truth_fingerprint/contracts/samples/README.md`
- `src/parallel_truth_fingerprint/contracts/samples/hart_payload_sample.txt`
- `src/parallel_truth_fingerprint/contracts/samples/unified_hart_payload_sample.txt`
- `src/parallel_truth_fingerprint/edge_nodes/__init__.py`
- `src/parallel_truth_fingerprint/edge_nodes/common/__init__.py`
- `src/parallel_truth_fingerprint/edge_nodes/edge_1/__init__.py`
- `src/parallel_truth_fingerprint/edge_nodes/edge_2/__init__.py`
- `src/parallel_truth_fingerprint/edge_nodes/edge_3/__init__.py`
- `src/parallel_truth_fingerprint/lstm_service/__init__.py`
- `src/parallel_truth_fingerprint/observability/__init__.py`
- `src/parallel_truth_fingerprint/persistence/__init__.py`
- `src/parallel_truth_fingerprint/scada/__init__.py`
- `src/parallel_truth_fingerprint/scenario_control/__init__.py`
- `src/parallel_truth_fingerprint/sensor_simulation/__init__.py`
- `src/parallel_truth_fingerprint/visualization/__init__.py`
- `_bmad-output/implementation-artifacts/1-1-initialize-architecture-driven-local-prototype-skeleton.md`
