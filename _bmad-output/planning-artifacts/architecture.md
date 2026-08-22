---
stepsCompleted:
  - 1
  - 2
  - 3
  - 4
  - 5
  - 6
  - 7
  - 8
inputDocuments:
  - /c:/Users/emili/Desktop/Projets/parallel-truth-fingerprint-prototype/_bmad-output/planning-artifacts/prd.md
  - /c:/Users/emili/Desktop/Projets/parallel-truth-fingerprint-prototype/_bmad-output/planning-artifacts/product-brief-parallel-truth-fingerprint-prototype-2026-03-23.md
  - /c:/Users/emili/Desktop/Projets/parallel-truth-fingerprint-prototype/docs/input/Arquitetura Baseada em Fonte de Verdade Paralela para Geração de Fingerprint Físico-Operacional em Sistemas Industriais Legados_DEFINIÇÃO_DO_PROBLEMA.txt
  - /c:/Users/emili/Desktop/Projets/parallel-truth-fingerprint-prototype/docs/input/Arquitetura Baseada em Fonte de Verdade Paralela para Geração de Fingerprint Físico-Operacional em Sistemas Industriais Legados_OBJECTIVOS.txt
  - /c:/Users/emili/Desktop/Projets/parallel-truth-fingerprint-prototype/docs/input/Arquitetura Baseada em Fonte de Verdade Paralela para Geração de Fingerprint Físico-Operacional em Sistemas Industriais Legados_METODOLOGIA_DE_PESQUISA.txt
  - /c:/Users/emili/Desktop/Projets/parallel-truth-fingerprint-prototype/docs/input/Arquitetura Baseada em Fonte de Verdade Paralela para Geração de Fingerprint Físico-Operacional em Sistemas Industriais Legados_FUNDAMENTACAO_TEORICA.txt
  - /c:/Users/emili/Desktop/Projets/parallel-truth-fingerprint-prototype/docs/input/Arquitetura Baseada em Fonte de Verdade Paralela para Geração de Fingerprint Físico-Operacional em Sistemas Industriais Legados_ARQUITETURA_PROPOSTA.txt
  - /c:/Users/emili/Desktop/Projets/parallel-truth-fingerprint-prototype/docs/input/Arquitetura Baseada em Fonte de Verdade Paralela para Geração de Fingerprint Físico-Operacional em Sistemas Industriais Legados_PLANO_DE_AVALIACAO_E_REFERENCE.txt
workflowType: 'architecture'
project_name: 'parallel-truth-fingerprint-prototype'
user_name: 'Emilio'
date: '2026-03-24'
lastStep: 8
status: 'controlling-consolidated-planning'
completedAt: '2026-08-22'
supersedesNormativeOverlays:
  - _bmad-output/planning-artifacts/architecture-update-2026-05-21.md
  - _bmad-output/planning-artifacts/architecture-update-2026-08-15.md
approvedChangeProposal: _bmad-output/planning-artifacts/sprint-change-proposal-2026-08-22.md
---

# Architecture Decision Document

_This document builds collaboratively through step-by-step discovery. Sections are appended as we work through each architectural decision together._

## Controlling Reading Rule

This consolidated `architecture.md` is the sole current normative architecture.
The original brownfield sections remain useful for v1 structure and context,
but the 2026-08-22 consolidation below controls every conflict involving v2,
scientific evidence, datasets, profiles, numeric parameters, mocks, workload,
truth, evaluation, authorization, or optional presentation. Dated architecture
updates are historical traceability only and are not additional normative
layers.

## Project Context Analysis

### Requirements Overview

**Functional Requirements:**
The PRD defines a compact but strict capability set centered on one compressor, three sensors, and three logically independent edges. Architecturally, the functional requirements establish a pipeline in which local sensor acquisition occurs first at the edge through pre-PLC physical acquisition semantics, using a simulated transmitter-side observation and HART-inspired collection logic; only after this local acquisition are edge observations exchanged through MQTT. Each edge then reconstructs its local replicated compressor-state view from self-observation plus peer observations. Each edge reconstructs its own local replicated compressor-state view from self-observation plus peer observations, Byzantine-style validation determines the valid system state, SCADA comparison operates only on the consensused state, valid data is persisted to local object storage, and the LSTM stage performs fingerprint training and inference downstream of validation.

The requirements also establish explicit observability obligations for the consensus process. The architecture must support identification of participating and excluded edges, reasons for exclusion, round-level trust ranking, explicit failed-consensus signaling, structured consensus logs, and alerts for failed consensus.

**Non-Functional Requirements:**
The non-functional requirements strongly constrain the architecture toward local execution, modular Python services, and presentation-grade transparency. Architecturally significant NFRs include:
- preservation of validation-before-trust
- strict separation between each edge-local replicated state and consensused valid state
- use of only consensused valid data for downstream processing
- reproducible local execution
- full traceability of each consensus round
- local integration with MQTT, HART-based collection semantics, OPC UA, MinIO, and LSTM service boundaries
- no unnecessary production-oriented complexity

**Scale & Complexity:**
This is a medium-complexity academic prototype. The system is intentionally constrained in scope, but the trust model and validation flow introduce non-trivial architectural discipline.

- Primary domain: industrial / OT-inspired local validation prototype
- Complexity level: medium
- Estimated architectural components: sensor simulation, edge services, MQTT broker interaction, consensus logic, SCADA comparison service, MinIO persistence layer, LSTM service, logging/observability support

### Technical Constraints & Dependencies

The architecture must preserve the following constraints and dependencies:

- local execution must not collapse the system into centralized behavior
- each edge must remain an independent logical node with its own local acquisition, MQTT publication/consumption, and consensus execution
- edge-local replicated-state reconstruction is an intermediate stage only and must not be treated as valid by default
- only the consensused valid state may feed SCADA comparison, persistence, and LSTM processing
- the SCADA side must be represented through a fake OPC UA service
- valid data persistence must use local MinIO object storage
- the LSTM service must train only on validated normal data
- the implementation must remain modular, simple, and suitable for demonstration and academic evaluation

### Real vs Simulated Component Classification

To keep the prototype academically valid without increasing scope, the architecture makes an explicit distinction between components that are implemented as real executable system pillars and components that represent a simulated environment.

**Real implementation components**
- MQTT broker and MQTT-based inter-edge communication
- decentralized edge-service execution and edge-local replicated-state reconstruction
- consensus execution as a real executable validation component, implemented in the prototype through CometBFT plus a Go ABCI application
- comparison logic as a real executable service operating on available inputs
- local object storage used as the persistence target
- LSTM training and inference service executed as a real downstream component
- observability, audit logging, and alerting logic
- the final lightweight SCADA-inspired demo UI layer, implemented only after the backend/runtime/services are stable

**Simulated environment components**
- physical sensors and compressor process behavior
- edge hardware as physical devices
- SCADA environment, represented through a fake OPC UA service
- cloud environment, represented through local storage and local execution only
- industrial network and plant environment beyond the explicit local communication path used by the prototype

**Conceptual-only PEP elements**
- BBD/FABA as the theoretical consensus inspiration
- Orion/Kafka-style cloud context-broker infrastructure
- real cloud deployment
- production-grade SCADA/HMI scope

**Interpretation rule**
- real components must execute real code paths and produce actual runtime outputs inside the prototype
- simulated components may stand in for unavailable field or enterprise infrastructure, but they must still be exercised through the normal architecture
- no simulated environment component may be used to bypass validation, comparison, persistence, or LSTM boundaries

### Cross-Cutting Concerns Identified

The following concerns affect multiple architectural components and will drive subsequent design decisions:

- decentralized logical isolation of edges despite physical co-location
- explicit trust-state handling throughout the validation pipeline
- auditability and explainability of consensus rounds
- boundary control between edge-local replicated state, consensused valid state, and downstream consumers
- separation of integrity alerts from temporal anomaly alerts
- reproducible local orchestration of all services
- consistent logging and minimal visualization support for demonstration and evaluation

## Starter Template Evaluation

### Primary Technology Domain

Python-based local multi-service prototype for industrial / OT-inspired validation architecture.

### Starter Options Considered

**Option 1: uv application starter**
- Current and actively maintained
- Good default choice for Python application projects
- Provides project metadata, environment management, and dependency workflow
- Slightly opinionated for a single-application layout

**Option 2: uv bare project initialization**
- Current and actively maintained
- Minimal project bootstrap with only core project metadata
- Best fit when architecture should define structure explicitly rather than inherit a generic starter layout
- Avoids introducing unnecessary files or assumptions

**Option 3: Generic template engines (cookiecutter / copier)**
- Current and maintained
- Useful for reusable organization-wide scaffolds
- Not necessary for this prototype
- Would add indirection and template complexity without architectural benefit

### Selected Starter: uv bare project initialization

**Rationale for Selection:**
This prototype is not a conventional web app, SaaS, or packaged library. It is a local, modular Python system composed of logically independent edge services, a comparison path, a persistence path, and an LSTM path. A minimal `uv`-based bootstrap gives dependency and environment management without imposing an application structure that could blur the architecture. This keeps the implementation aligned with the PRD and preserves architectural control.

**Initialization Command:**

```bash
uv init --bare
```

**Architectural Decisions Provided by Starter:**

**Language & Runtime:**
- Python project initialized through `pyproject.toml`
- dependency and environment management supported through `uv`

**Styling Solution:**
- Not applicable at starter level
- the final lightweight SCADA-inspired demo UI should remain secondary to the service architecture and must be implemented only after the backend/runtime/services are stable

**Build Tooling:**
- lightweight Python project initialization
- no unnecessary framework or frontend tooling introduced by default

**Testing Framework:**
- not imposed by the starter
- can be selected explicitly later based on architecture decisions

**Code Organization:**
- starter does not impose a monolithic application layout
- architecture remains free to define separate logical modules/services for:
  - sensor simulation
  - edge nodes
  - consensus
  - SCADA comparison
  - persistence
  - LSTM processing
  - observability/logging

**Development Experience:**
- reproducible local project initialization
- clean dependency management
- low setup complexity
- suitable foundation for a modular local prototype

**Note:** Project initialization using this command should be the first implementation story.

## Core Architectural Decisions

### Decision Priority Analysis

**Critical Decisions (Block Implementation):**
- Runtime and project bootstrap: Python + `uv --bare`
- Service decomposition around logical responsibilities, not around deployment convenience
- MQTT as the inter-edge communication mechanism
- OPC UA fake SCADA as a separate logical service
- MinIO as the valid-data persistence target
- LSTM service isolated downstream of consensus and valid-data persistence
- explicit trust-state boundaries between edge-local replicated state and consensused valid state
- full consensus-round observability and audit logging
- controlled scenario and fault-injection support for demonstration and evaluation

**Important Decisions (Shape Architecture):**
- in-process vs service-style boundaries while preserving logical decentralization
- canonical message and state models between services
- structured logging and alert event format
- consensus result contract for downstream consumers
- local orchestration model for all services
- simulation behavior model for normal and controlled abnormal conditions

**Deferred Decisions (Post-MVP):**
- cloud deployment patterns
- advanced security hardening
- horizontal scaling strategy
- richer visualization tooling
- multi-equipment extension patterns

### Data Architecture

**Primary Data Model Decision:**
Use explicit typed domain models for:
- sensor observation
- shared replicated state
- consensus round input
- consensus round result
- consensused valid state
- SCADA comparison result
- persistence record
- LSTM training sample
- LSTM inference result
- alert event
- scenario-control event

**Rationale:**
The architecture depends on preserving state transitions and trust boundaries. Separate models are needed so the implementation cannot accidentally treat an edge-local replicated state as validated state.

**Persistence Decision:**
Use MinIO object storage only for valid downstream records. Persisted artifacts should include:
- consensused valid state records
- consensus metadata needed for traceability
- normal-only training data subsets
- trained fingerprint/model artifacts
- inference outputs and alert-relevant evidence as needed

**Validation Boundary Decision:**
No raw pre-consensus or potentially contaminated state may enter the training pipeline.

### Authentication & Security

**Authentication Decision:**
No end-user authentication layer is required for the MVP prototype.

**Security Decision:**
Architectural security is expressed through trust handling, not through production IAM:
- distrust all edge contributions until consensus
- distrust each edge-local replicated state until consensus result exists
- use only consensused valid state downstream
- keep SCADA divergence and LSTM anomaly paths separate
- preserve auditability of consensus decisions

**Rationale:**
This matches the academic prototype scope and avoids production-oriented complexity not required by the PRD.

### API & Communication Patterns

**Inter-Edge Communication Decision:**
Use MQTT publish/subscribe for edge-to-edge observation exchange.

MQTT broker infrastructure is a passive communication layer only. It relays published observations between edges through brokered publish/subscribe behavior, but it is not part of the trust model and does not participate in validation or consensus decisions.

**Protocol Boundary Decision:**
Use distinct protocol roles:
- HART-based collection semantics at the local acquisition boundary
- MQTT for decentralized inter-edge communication
- OPC UA for fake SCADA logical-state exposure
- object storage API for MinIO persistence

**Service Communication Pattern:**
Prefer event/message contracts between logical services rather than tightly coupled direct calls, even in local execution.

**Consensus Contract Decision:**
Consensus output must include:
- participating edges
- excluded edges
- reasons for exclusion
- trust ranking
- valid/invalid consensus status
- resulting consensused valid state when available

**Alerting Contract Decision:**
Keep two separate alert categories:
- SCADA divergence alert
- LSTM anomaly alert

### Frontend Architecture

Not a primary architecture driver for this prototype.

**Decision:**
No production UI architecture is required.
The only planned UI layer is the final lightweight SCADA-inspired demo interface.
It must:
- remain the last implementation layer after the backend/runtime/services are complete
- stay limited to one compressor and its sensors
- consume existing logs, runtime outputs, and simulator/scenario-control hooks rather than introducing a second parallel architecture
- provide interactive log visualization, current state display, alert display, scenario-status display, and a compressor-centric sensor view with live numeric values
- expose approved demo controls such as compressor power, replay activation, and damaged/faulty edge simulation without bypassing the pipeline

### Infrastructure & Deployment

**Execution Model Decision:**
Run all services locally, but preserve them as logically independent nodes/components.

**Decentralization Decision:**
Local execution must not collapse the architecture into a centralized design. Each edge must retain:
- its own local acquisition
- its own MQTT publish/consume behavior
- its own consensus execution context

Decentralization is therefore achieved at the edge layer. Each edge independently collects its local sensor data, publishes its own observations, consumes observations from the other edges, and builds its own local view of the system. The MQTT broker supports this exchange as infrastructure only.

**Orchestration Decision:**
Use a lightweight local orchestration approach suitable for development and demonstration, without introducing production platform machinery.

**Observability Decision:**
Structured logging is mandatory across services, with special emphasis on consensus-round traceability.

### Controlled Scenario & Fault-Injection Support

**Scenario Control Decision:**
The prototype must include explicit, controllable mechanisms to exercise the core research scenarios without changing the architecture itself.

The supported controlled scenarios must include:
- temporary removal or invalidation of one or more edges to observe consensus behavior
- failed-consensus scenarios when insufficient valid edges remain
- replay-style reintroduction of previously valid data to create temporal inconsistency
- SCADA-side manipulation that creates divergence relative to the consensused valid state

**Rationale:**
These capabilities are necessary to demonstrate Byzantine validation behavior, SCADA comparison behavior, and fingerprint-based anomaly detection during academic evaluation.

**Fault-Injection Boundary Decision:**
Scenario injection must occur through explicit control points in the simulation and service flow, not through ad hoc architectural shortcuts. The fault-injection mechanisms must preserve the same end-to-end path used in normal execution so that the demonstration remains faithful to the architecture.

### Sensor Simulation Behavior Model

**Simulation Model Decision:**
Sensor simulation must be simple but explicit.

Each simulated sensor must:
- operate within a defined normal range
- vary over time according to a realistic but simple pattern
- support controlled deviation from normal behavior when a scenario requires it

The simulation model must support:
- normal compressor behavior generation
- suspicious-edge contribution scenarios
- replay-oriented scenarios
- divergence-supporting scenarios for SCADA comparison
- anomaly-supporting temporal deviations for LSTM evaluation

**Rationale:**
The prototype must demonstrate the architectural logic under understandable and repeatable operating conditions. A controlled behavior model is necessary to make consensus validation, SCADA divergence, and LSTM anomaly behavior observable and explainable.

### Decision Impact Analysis

**Implementation Sequence:**
1. Initialize project with `uv --bare`
2. Define shared typed contracts and domain models
3. Implement sensor simulation and edge-local acquisition services
4. Implement scenario-control and fault-injection hooks in simulation and service boundaries
5. Implement MQTT exchange and shared-state reconstruction
6. Implement consensus engine and consensus result contracts
7. Implement fake OPC UA SCADA service
8. Implement SCADA comparison service
9. Implement MinIO persistence path for valid data only
10. Implement LSTM training/inference service
11. Implement observability, alerts, and minimal visualization support

**Cross-Component Dependencies:**
- consensus depends on edge observation exchange
- failed-consensus scenarios depend on explicit edge invalidation/removal controls
- SCADA comparison depends on consensused valid state only
- replay and temporal anomaly scenarios depend on controlled reuse or shaping of simulated observation streams
- persistence depends on consensus filtering
- LSTM depends on persisted validated normal data
- observability spans all components and is especially critical for consensus, scenario control, and downstream alert interpretation

## Implementation Patterns & Consistency Rules

### Pattern Categories Defined

**Critical Conflict Points Identified:**
The main agent-conflict risks for this project are:
- collapsing logically independent edges into shared implementation state
- confusing edge-local replicated state with consensused valid state
- allowing downstream services to consume non-validated data
- using inconsistent event, payload, and logging formats across services
- introducing scenario/fault injection in ways that bypass the normal pipeline
- mixing SCADA divergence logic with LSTM anomaly logic

### Naming Patterns

**Domain Model Naming Conventions:**
Use explicit, role-specific names for state and message objects. The following concepts must remain distinct in naming and in code:
- `sensor_observation`
- `shared_state`
- `consensus_round`
- `consensus_result`
- `consensused_valid_state`
- `scada_state`
- `comparison_result`
- `persistence_record`
- `training_sample`
- `inference_result`
- `alert_event`
- `scenario_control_event`

Do not use generic names such as `state`, `data`, or `result` when a trust boundary or pipeline stage is involved.

**Code Naming Conventions:**
- Python modules and files: `snake_case`
- classes and typed models: `PascalCase`
- functions, variables, and fields: `snake_case`
- constants: `UPPER_SNAKE_CASE`

**Service Naming Conventions:**
Service/module names must reflect logical responsibility:
- `sensor_simulation`
- `edge_node`
- `consensus`
- `scada_adapter`
- `comparison`
- `persistence`
- `lstm_service`
- `observability`
- `scenario_control`

### Structure Patterns

**Project Organization:**
Organize code by logical service boundary first, not by technical layer alone. The implementation should make it difficult to accidentally mix responsibilities across:
- sensor simulation
- per-edge logic
- consensus processing
- SCADA state exposure and access
- comparison logic
- valid-data persistence
- LSTM training/inference
- observability and scenario control

**Edge Isolation Pattern:**
Each edge must be implemented as an independent logical unit with:
- its own acquisition flow
- its own MQTT publish/consume behavior
- its own local replicated view
- its own consensus execution context

Even if common helper code exists, no shared mutable runtime state should be used in a way that weakens logical edge separation.

**Test Structure Pattern:**
Tests should be organized by service or architectural boundary and should include:
- normal-path tests
- consensus-edge-case tests
- failed-consensus tests
- SCADA divergence tests
- replay/temporal inconsistency tests

### Format Patterns

**Message and Payload Format Rules:**
All inter-service payloads should use typed, explicit structures. Payload contracts must not rely on implicit or ad hoc field sets.

At minimum, message structures should consistently include:
- source or producing component
- timestamp
- round or scenario identifier where relevant
- payload type
- domain data fields
- trust/validation metadata where relevant

**Logging Format Rules:**
Structured logs must be used throughout the system. Consensus logs must be rich enough to support demonstration and auditability.

Consensus-round logs must consistently capture:
- round identifier
- participating edges
- excluded edges
- exclusion reasons
- trust ranking
- consensus success/failure status
- resulting consensused valid state reference when available

**Alert Format Rules:**
Use separate alert structures for:
- SCADA divergence alerts
- LSTM anomaly alerts
- consensus-failure alerts

These alert categories must not be merged into a single generic alert type without explicit category and cause fields.

### Communication Patterns

**Inter-Service Communication Pattern:**
Use explicit boundaries between protocols and responsibilities:
- HART-based collection semantics for local acquisition
- MQTT for inter-edge communication
- OPC UA for fake SCADA
- MinIO object storage API for valid persistence artifacts

Do not bypass these boundaries for convenience during implementation.

**Scenario-Control Pattern:**
Scenario-control and fault-injection must be implemented through explicit control points inside the simulation and service flow. They may alter inputs or service behavior, but they must not skip stages of the normal architecture.

Examples:
- edge invalidation may affect edge participation in a round
- replay control may reintroduce previously valid values into the normal flow
- SCADA manipulation may alter the logical SCADA side before comparison

Scenario control must not directly write downstream outputs that would normally be produced by consensus, comparison, persistence, or LSTM stages.

**State Management Pattern:**
Each edge-local replicated state is an intermediate state only. Consensused valid state is the only downstream-trusted state.

This distinction must be preserved in:
- naming
- models
- service interfaces
- persistence contracts
- training pipeline inputs

### Process Patterns

**Error Handling Patterns:**
Failed consensus must be treated as an explicit architectural outcome, not as an unstructured exception. Services should emit structured failure information when:
- insufficient valid edges remain
- consensus cannot produce a valid state
- downstream processing is blocked because no valid state exists

**Validation Boundary Pattern:**
Before SCADA comparison, persistence, or LSTM processing, services must check that the input state is explicitly marked as consensused valid state.

**Training Data Protection Pattern:**
The LSTM training pipeline may consume only validated normal data. No raw observations, pre-consensus edge-local replicated state, or invalid-round outputs may be used as training input.

### Enforcement Guidelines

**All AI Agents MUST:**
- preserve logical separation between raw edge-local state, edge-local replicated state, and consensused valid state
- route scenario and fault-injection through explicit control points without bypassing the normal pipeline
- keep SCADA divergence logic and LSTM anomaly logic separate in code, contracts, and alerts
- use structured logging for all consensus rounds and downstream alert-relevant events
- keep service/module ownership explicit and avoid cross-boundary leakage of responsibility

**Pattern Enforcement:**
- code reviews and future story acceptance criteria should check trust-boundary preservation
- new modules should declare which architectural boundary they belong to
- any violation of state-boundary or protocol-boundary rules should be treated as an architecture defect, not just a style issue

### Pattern Examples

**Good Examples:**
- `consensus_result` is produced from edge observations and contains trust metadata plus consensused valid state
- `comparison_service` accepts only `consensused_valid_state` and `scada_state`
- `lstm_service` trains from validated persisted records only
- `scenario_control` modifies upstream conditions but still lets the pipeline execute normally

**Anti-Patterns:**
- passing `shared_state` directly into persistence or LSTM training
- using one in-memory global structure to represent all edges without logical isolation
- emitting generic alerts without category separation
- injecting scenario outputs directly into comparison or LSTM stages
- mixing consensus logic with SCADA comparison logic in the same service module

## Project Structure & Boundaries

### Complete Project Directory Structure

This structure should now be read as a representative architecture map rather than a literal file inventory. Epic 1 and Epic 2 are implemented more fully than Epic 3 and Epic 4; the `scada/`, `comparison/`, `persistence/`, `lstm_service/`, and final demo UI areas remain planned boundaries until their respective epics are implemented.

```text
parallel-truth-fingerprint-prototype/
├── README.md
├── pyproject.toml
├── uv.lock
├── .env.example
├── .gitignore
├── compose.local.yml
├── docs/
│   └── input/
│       ├── ..._DEFINI��O_DO_PROBLEMA.txt
│       ├── ..._OBJECTIVOS.txt
│       ├── ..._ARQUITETURA_PROPOSTA.txt
│       └── Arquitetura Baseada em Fonte de Verdade Paralela para Geração de Fingerprint Físico-Operacional em Sistemas Industriais Legados - Emilio Bresolin.pdf
├── src/
│   └── parallel_truth_fingerprint/
│       ├── app.py
│       ├── config/
│       │   ├── settings.py
│       │   ├── ranges.py
│       │   ├── tolerances.py
│       │   └── scenarios.py
│       ├── contracts/
│       │   ├── sensor_observation.py
│       │   ├── shared_state.py
│       │   ├── consensus_round.py
│       │   ├── consensus_result.py
│       │   ├── consensused_valid_state.py
│       │   ├── scada_state.py
│       │   ├── comparison_result.py
│       │   ├── persistence_record.py
│       │   ├── training_sample.py
│       │   ├── inference_result.py
│       │   ├── alert_event.py
│       │   └── scenario_control_event.py
│       ├── sensor_simulation/
│       │   ├── simulator.py
│       │   ├── behavior_model.py
│       │   └── normal_profiles.py
│       ├── edge_nodes/
│       │   ├── common/
│       │   │   ├── acquisition.py
│       │   │   ├── mqtt_io.py
│       │   │   └── local_state.py
│       │   ├── edge_1/
│       │   │   └── service.py
│       │   ├── edge_2/
│       │   │   └── service.py
│       │   └── edge_3/
│       │       └── service.py
│       ├── consensus/
│       │   ├── engine.py
│       │   ├── trust_model.py
│       │   ├── round_evaluator.py
│       │   └── failure_policy.py
│       ├── scada/
│       │   ├── opcua_server.py
│       │   ├── state_provider.py
│       │   └── manipulation_controls.py
│       ├── comparison/
│       │   ├── comparator.py
│       │   ├── tolerance_rules.py
│       │   └── divergence_alerts.py
│       ├── persistence/
│       │   ├── minio_client.py
│       │   ├── writer.py
│       │   └── artifact_store.py
│       ├── lstm_service/
│       │   ├── dataset_builder.py
│       │   ├── trainer.py
│       │   ├── model_registry.py
│       │   └── inference.py
│       ├── observability/
│       │   ├── structured_logging.py
│       │   ├── consensus_trace.py
│       │   ├── metrics.py
│       │   └── alert_router.py
│       ├── scenario_control/
│       │   ├── controller.py
│       │   ├── edge_faults.py
│       │   ├── replay_scenarios.py
│       │   └── scada_faults.py
│       └── visualization/
│           ├── dashboard_data.py
│           └── simple_views.py
├── tests/
│   ├── sensor_simulation/
│   ├── edge_nodes/
│   ├── consensus/
│   ├── comparison/
│   ├── persistence/
│   ├── lstm_service/
│   ├── scenario_control/
│   ├── observability/
│   └── integration/
│       ├── normal_flow/
│       ├── failed_consensus/
│       ├── scada_divergence/
│       └── replay_anomaly/
└── scripts/
    ├── run_local_demo.py
    ├── run_training.py
    └── seed_normal_data.py
```

### Architectural Boundaries

**API Boundaries:**
- no public product API is required for the MVP
- MQTT message contracts form the inter-edge communication boundary
- OPC UA forms the logical SCADA exposure boundary
- MinIO object storage forms the valid-data persistence boundary

**Component Boundaries:**
- `sensor_simulation` produces upstream observations only
- `edge_nodes` perform acquisition, MQTT interaction, and local replicated-state handling
- `consensus` consumes edge observations and edge-local replicated state views and produces only consensus results and consensused valid state
- `scada` exposes logical supervisory state only
- `comparison` consumes only consensused valid state plus SCADA state
- `persistence` consumes only valid downstream records
- `lstm_service` consumes only validated persisted normal data and inference-time valid inputs
- `scenario_control` alters upstream conditions but must not bypass the pipeline
- `observability` records and routes logs, traces, and alerts without owning business logic

**Service Boundaries:**
- each edge service must remain logically independent
- no shared mutable state may bypass the per-edge boundary
- consensus execution must remain distinct from edge acquisition code
- comparison logic must remain distinct from consensus logic
- LSTM logic must remain distinct from both SCADA comparison and persistence writing

**Data Boundaries:**
- `shared_state` is intermediate only
- `consensused_valid_state` is the only downstream-trusted state
- raw observations and invalid states must never enter training data
- scenario-control events must be explicit and traceable

### Requirements to Structure Mapping

**Feature / Requirement Mapping:**
- Sensor Simulation & Edge Acquisition -> `sensor_simulation/`, `edge_nodes/`
- Edge Communication & Shared State -> `edge_nodes/common/`, `contracts/shared_state.py`
- Distributed Validation & Trust -> `consensus/`, `observability/consensus_trace.py`
- SCADA Comparison & Integrity Alerting -> `scada/`, `comparison/`
- Valid Data Persistence -> `persistence/`
- Fingerprint Training & Inference -> `lstm_service/`
- Temporal Anomaly Detection -> `scenario_control/replay_scenarios.py`, `lstm_service/inference.py`
- Consensus observability requirements -> `observability/`, `consensus/`
- Minimal demonstration support -> `visualization/`

**Cross-Cutting Concerns:**
- trust-boundary enforcement -> `contracts/`, `consensus/`, `comparison/`, `persistence/`, `lstm_service/`
- structured logging -> `observability/structured_logging.py`
- alert separation -> `comparison/divergence_alerts.py`, `observability/alert_router.py`, `lstm_service/inference.py`
- scenario traceability -> `scenario_control/`, `observability/`

### Integration Points

**Internal Communication:**
- sensor simulation -> edge-local acquisition flow
- edge nodes -> MQTT broker/topics
- edge-local replicated state -> consensus engine
- consensus result -> comparison / persistence / LSTM eligibility checks
- SCADA service -> comparison service
- persistence -> dataset builder / trainer
- scenario control -> simulation / edge participation / SCADA manipulation control points
- observability -> all components via structured event/log interfaces

**External Integrations:**
- MQTT broker
- fake OPC UA SCADA endpoint
- local MinIO service

**Data Flow:**
- sensor -> edge -> MQTT -> shared_state -> consensus_result -> consensused_valid_state -> SCADA comparison -> persistence -> LSTM
- scenario control may modify upstream conditions, but must not bypass the above flow

### File Organization Patterns

**Configuration Files:**
- `config/settings.py` for global runtime settings
- `config/ranges.py` for normal sensor ranges
- `config/tolerances.py` for SCADA comparison thresholds
- `config/scenarios.py` for explicit scenario control definitions

**Source Organization:**
- source code is organized by architectural responsibility
- shared domain contracts live in `contracts/`
- service implementations live in service-specific directories
- optional visualization remains isolated from core validation logic

**Test Organization:**
- service-level tests live beside their architectural boundary under `tests/`
- full-pipeline and scenario tests live under `tests/integration/`
- scenario-specific tests must verify that the normal pipeline is preserved

**Asset Organization:**
- no major static-asset subsystem is required
- any minimal visualization assets should remain isolated under `visualization/`

### Development Workflow Integration

**Development Server Structure:**
- local execution is orchestrated through top-level scripts
- services remain logically separate even if started from one orchestration entrypoint

**Execution Model:**
- the prototype remains fully local
- local orchestration may use a mixed process/container model where that improves reproducibility and setup simplicity
- MQTT broker should run as a local containerized service
- LSTM service may run as a local containerized service
- MinIO may run as a local containerized service
- edge nodes and core Python orchestration logic may remain regular local Python processes

This execution model is a local reproducibility choice only. It must not change service boundaries, collapse decentralization, or introduce production-oriented deployment complexity.

**Build Process Structure:**
- project initialization and dependency management are handled through `uv`
- no framework build pipeline should dictate architecture

**Deployment Structure:**
- deployment remains local-only for the MVP
- structure should support reproducible local orchestration and reruns, not production hosting

## Architecture Validation Results

### Coherence Validation

**Decision Compatibility:**
The core decisions are compatible with one another. The architecture uses a minimal Python foundation, local execution, MQTT-based edge communication, fake OPC UA SCADA exposure, MinIO persistence, and an isolated LSTM stage without introducing unnecessary framework or deployment complexity. The mixed local process/container execution model remains compatible with the architecture because it is treated strictly as a reproducibility choice and does not alter service boundaries.

**Pattern Consistency:**
The implementation patterns support the architecture correctly. Naming rules, domain contracts, structured logging, and service-boundary rules all reinforce the trust-state distinctions required by the PRD. Scenario-control and fault-injection mechanisms are properly constrained to explicit upstream control points and do not bypass the normal pipeline.

**Structure Alignment:**
The proposed project structure matches the architecture decisions. The directory layout preserves service ownership, keeps consensus separate from comparison and persistence, isolates LSTM logic downstream of validation, and gives scenario control and observability first-class but bounded roles.

### Requirements Coverage Validation

**Feature Coverage:**
All PRD capability areas are architecturally covered:
- sensor simulation and edge acquisition
- MQTT-based communication and shared-state reconstruction
- Byzantine-style validation and trust ranking
- SCADA comparison and divergence alerting
- valid-data persistence
- LSTM training and inference
- replay-oriented anomaly detection
- consensus observability and failure handling

**Functional Requirements Coverage:**
All functional requirements have architectural support. In particular, the added consensus observability requirements are covered through:
- consensus result contracts
- structured consensus logging
- explicit failed-consensus signaling
- alert separation for consensus-related failures

**Non-Functional Requirements Coverage:**
All relevant NFRs are addressed architecturally:
- local execution
- modular Python implementation
- validation-before-trust
- reproducibility
- structured traceability of consensus rounds
- integration boundaries for MQTT, HART-based collection semantics, OPC UA, MinIO, and LSTM

### Implementation Readiness Validation

**Decision Completeness:**
The critical architectural decisions are complete for the current prototype scope. The document defines runtime foundation, service decomposition, communication boundaries, trust boundaries, persistence constraints, LSTM constraints, scenario-control behavior, and observability obligations.

**Structure Completeness:**
The project structure is specific enough to guide implementation. Core modules, contracts, integration points, and tests are all mapped to the architectural boundaries.

**Pattern Completeness:**
The implementation patterns are strong enough to prevent the main downstream risks:
- edge-local replicated state being mistaken for valid state
- edge decentralization being collapsed during implementation
- scenario control bypassing the normal pipeline
- SCADA and LSTM alert paths being merged
- invalid or contaminated data entering persistence or training

### Gap Analysis Results

**Critical Gaps:**
No critical architectural gaps identified for the current prototype scope.

**Important Gaps:**
No important gaps requiring architectural redesign were identified. The remaining work is implementation and later planning decomposition rather than additional architecture expansion.

**Nice-to-Have Gaps:**
Potential future refinements, already outside the MVP scope, include:
- more detailed local orchestration documentation
- richer minimal visualization conventions
- explicit examples of scenario-control payloads and log schemas

### Validation Issues Addressed

The architecture validation confirmed and preserved the following critical invariants:
- edges remain logically decentralized even in local execution
- each edge-local replicated state is intermediate only and never trusted by default
- only consensused valid state is used for downstream steps
- consensus rounds remain fully observable and auditable
- SCADA divergence alerts and LSTM anomaly alerts remain separate
- scenario-control and fault-injection mechanisms remain explicit architectural components and do not bypass the normal flow
- mixed local process/container orchestration is treated only as a reproducibility decision, not as architecture expansion

### Architecture Completeness Checklist

**Requirements Analysis**
- [x] Project context thoroughly analyzed
- [x] Scale and complexity assessed
- [x] Technical constraints identified
- [x] Cross-cutting concerns mapped

**Architectural Decisions**
- [x] Critical decisions documented
- [x] Technology stack and execution model specified
- [x] Integration patterns defined
- [x] validation-before-trust boundaries preserved

**Implementation Patterns**
- [x] Naming conventions established
- [x] Structure patterns defined
- [x] Communication patterns specified
- [x] Process patterns documented

**Project Structure**
- [x] Complete directory structure defined
- [x] Component boundaries established
- [x] Integration points mapped
- [x] Requirements to structure mapping complete

### Architecture Readiness Assessment

**Overall Status:** HISTORICAL V1 ASSESSMENT; SEE CONTROLLING V2 CONSOLIDATION

**Confidence Level:** High

**Key Strengths:**
- strict preservation of architectural meaning from the PRD
- explicit trust-state boundaries
- strong consensus observability and explainability support
- clean separation of downstream validation paths
- local execution model compatible with reproducibility and demonstration goals
- project structure aligned to service ownership and implementation boundaries

**Areas for Future Enhancement:**
- concrete example payloads for contracts
- more detailed scenario-control configuration examples
- expanded orchestration guidance if later needed for implementation convenience

### Implementation Handoff

**AI Agent Guidelines:**
- follow the architectural boundaries exactly as documented
- treat state-boundary rules as invariants, not guidelines
- do not route scenario control around the normal execution path
- keep SCADA comparison and LSTM anomaly logic separate
- preserve logical edge independence even if services share the same machine

**First Implementation Priority:**
Initialize the project with:

```bash
uv init --bare
```

Then implement the shared typed contracts and architectural skeleton before service logic.

## Controlling V2 Architecture Consolidation - 2026-08-22

### Scope and simplicity boundary

The target remains one local academic prototype operated by one researcher.
It retains the existing Python services, Go ABCI/CometBFT boundary, MQTT,
OPC UA, MinIO, and simple Python-served dashboard surface. This correction adds
flat evidence contracts and deterministic validators only. It adds no database,
workflow service, authorization server, service mesh, frontend framework,
production HMI, cloud platform, or additional scientific modality.

Exactly two detection modalities exist: physical instrumentation and Linux
host syscalls. Raw mA, normalized span, and engineering value are linked
representations of the physical modality. External datasets retain native
scope. Only synchronized `PTFP-Custom-v1` runs can support the paired
physical/syscall/fusion ablation.

Planning approval never authorizes implementation, dataset acquisition,
training, syscall capture, experiment execution, model promotion, dashboard
activation, deployment, or publication. Each later activity requires its own
immutable authorization identity.

### Trust and authority boundaries

- Only the experiment/control boundary may write a command or schedule.
- Analytics, consensus, storage, OPC UA, capture, evaluation, and presentation
  identities have no actuator credentials or analytics-to-control conduit.
- The OPC UA source is a separate pre-consensus branch read through a distinct
  real `opc.tcp` client; consensus projection cannot substitute for it.
- Detector-facing writers cannot read restricted truth. Evaluation joins truth
  only after bundle, threshold, fusion-policy, and score identities freeze.
- Infrastructure or dashboard failure may degrade or abort evidence but cannot
  change a command, artifact identity, score, gate, or scientific status.

### Authoritative evidence contracts

All records are flat, versioned, canonically serializable, immutable after
approval/freeze, and owned by one validating boundary. No service is added.

| Contract | Required content | Owner and validator | Fail-closed condition |
| --- | --- | --- | --- |
| `DecisionRecord.v1` | decision ID; values/factors and units; rationale; bounded question; component, experiment, track, and final-output scope; owner/approval; freeze time; truth/test lock state; source constraints; prohibited interpretations | Research owner; decision validator at G1 | post-test, mutable, unapproved, truth-informed, or scope-mismatched decision |
| `MockAdmission.v1` | mock ID; capability gap; attempted or unavailable authentic path; official sources and exact locators; supported behavior and numbers; transfer rationale; component; bounded question; track; final output; limitations and prohibited claims; replacement condition; owner/approval | Research owner plus architecture validator at G1 and G9 | reproducible authentic path; convenience rationale; absent/inapplicable authority; weak transfer; missing result linkage; or real-plant/digital-twin claim |
| `ParameterEvidence.v1` | stable ID; value/unit/class; class-specific authority; exact source/decision/calibration/mock locator; derivation and input IDs; profile and experiment scope; approval; uncertainty/limitation; authentic-reproduction feasibility; component/question/track/final-output linkage; transfer rationale | Source/parameter registry; parameter validator at startup, experiment freeze, and G9 | incomplete, conflicting, circular, dimensionally invalid, non-transferable, unresolved, or class-promoted record |
| `InstrumentProfile.v1` | profile identity/hash; exact device/variant; electrical endpoints; engineering LRV/URV and unit; conversion direction; quality policy; parameter/source identities and locators; approved scope | Profile registry; profile validator at G1/G2 | anonymous endpoint, pending source, unresolved parameter, incompatible unit, or scope mismatch |
| `ExperimentSpec.v1` | immutable experiment/run identities; decision, parameter, profile, mock-admission, code/runtime/input hashes; phases; schedules; expected streams; split; metrics; abort/stopping and truth-unlock policy | Experiment controller; spec validator before activity authorization | inferred defaults, missing evidence identity, post-freeze change, or authorization mismatch |
| `ScenarioTruth.v1` | restricted immutable condition/intervention intervals, opaque correlation, provenance, writer, unlock, and hash | Restricted truth writer/evaluator | truth in any detector-facing contract or join before declared unlock |
| `SignalObservation.v2` | raw mA; pre-clipping quality/diagnostics; profile and parameter hashes; normalized and engineering representations; units; experiment/run/round/edge/sensor/event; sequence; source/observed time and clock quality | Acquisition boundary | representation mismatch, missing identity, bad profile, truth/label field, or silent coercion |
| `SyscallEventBatch.v1` | authentic categorical call events; workload/host-or-VM/boot/container/cgroup/process/thread; kernel/ABI/collector/filter; sequence/time; gaps/drops/duplicates/queue; capture mode; raw segment URI/hash | Linux capture boundary | fabricated/modified/substituted calls, fixture role in formal evidence, unknown attribution, or unhandled capture-quality failure |
| `DetectorBundle.v1` / `DetectorScore.v1` | immutable model/schema/preprocessing/data/split/calibration/threshold/runtime hashes and inference-only scores without truth | Track-specific model registry/detector | fit/recalibration during load or inference, mutable latest identity, truth field, or incompatibility |
| `FusionDecision.v1` / `EvaluationResult.v1` | same-run calibrated score references, frozen preregistered fusion policy, truth-unlock identity, metrics, uncertainty, limitations, and lineage | Fusion worker/restricted evaluator | cross-dataset fusion, pre-unlock truth, mismatched support, or retroactive choice |
| `ArtifactManifest.v1` | content/schema hashes, parents, activity/tool/code/runtime/source/license identity; complete manifest published last | Evidence registry | mutable alias as identity, missing object, digest mismatch, or incomplete manifest |

Class-specific authority is binding:

- `direct` uses official authority applicable to the exact selected profile;
- `derived` uses validated input IDs and deterministic dimensional derivation;
- `measured` uses preserved calibration or pilot method, environment, run,
  timestamp, uncertainty, and artifact hash;
- `preregistered_factor` uses a pre-test frozen `DecisionRecord.v1`, while
  official sources establish only capability or constraint;
- `mock` uses an approved `MockAdmission.v1` plus official support for every
  asserted domain behavior and number.

No class can be silently promoted into another. A citation is not value
authority for a researcher-selected factor and does not transfer unrelated
values from the same document.

### Exact command-profile and parameter mapping

`instrument-profile-cds803-terminal53-linear-0-100-v1` binds the archived
Danfoss VLT CDS 803 Programming Guide
`AU356039245821 en-000201 / 130R0597`, printed p. 54, Tables 60-63:

- parameter 6-12 is Terminal 53 Low Current, default 4 mA;
- parameter 6-13 is Terminal 53 High Current, default 20 mA;
- parameter 6-14 is the low reference/feedback value corresponding to 6-12;
- parameter 6-15 is the high reference/feedback value corresponding to 6-13.

The selected 6-14=0 and 6-15=100 values are project preregistration choices in
`decision-custom-reference-window-v1`, not Danfoss defaults or recommendations.
The same decision authorizes 25 and 75 as `speed_reference_pct` research
factors. Under the frozen profile:

```text
reference_current_ma = 4 mA + (20 mA - 4 mA) * reference_pct / 100
25% -> 8 mA
75% -> 16 mA
```

Ramp, dwell, settling, ordering, repetitions, timing, and safety remain
separate evidence records. The mapping makes no power, efficiency, operating
range, or safety claim.

The initial temperature candidate is Siemens TH320 option D73, archived PDF
p. 4, Pt100 0-100 degC four-wire with 4-20 mA output. The initial pressure
candidate is the exact Siemens P200 0-10 bar gauge/4-20 mA two-wire variant,
but remains blocked until official bytes are archived and hashed. The FB420
source supports a directly proportional 4-20 mA RPM profile with user-defined
endpoints; the project minimum and maximum RPM remain blocked until Emilio
freezes a decision within that documented capability. No legacy 1.8-8.5 bar or
1200-4200 rpm fallback is permitted.

### Bounded physical signal emulator admission

The only approved planning mock boundary is
`mock-admission-ptfp-signal-emulator-v1`. The capability gap is absence of a
physical compressor, selected instruments/drive, DAQ, and qualified real-plant
acquisition in the approved software-only prototype. Its sole purpose is to
produce controlled synthetic current-domain physical observations for
`PTFP-Custom-v1` and the same-run physical/syscall/fusion ablation.

The component is a controlled signal emulator plus profile conversion, not a
compressor digital twin. Official NIST, Rockwell, Danfoss, Siemens, FB420, and
DOE sources support only their exact bounded testbed, electrical, device, or
qualitative statements. They do not establish universal compressor dynamics,
noise, delay, bias, safety, energy, efficiency, or operating ranges.

Prohibited claims are: real plant; validated compressor dynamics or digital
twin; safety/energy/control-performance validation; manufacturer-endorsed
operating range; external validation; or a global cross-domain champion. The
admission is replaced if qualified real hardware and preserved calibration/
acquisition evidence become available under a new approved scope.

Every anonymous v1 engineering range, behavior weight, period, phase, offset,
noise value, secondary-variable formula, comparison tolerance, consensus scale,
or threshold is `formal_v2_status=disabled` in
`docs/reference-archive/catalog/legacy-constant-quarantine-v1.csv`. Exact v1
reproduction may retain them only under a visible legacy identity; they cannot
affect a formal v2 run, dataset, result table, gate, metric, or claim. Formal v2
may use a simpler scripted signal design rather than invent realism.

### Authentic Linux workload and syscall boundary

The default path is an allowlisted controlled Linux edge workload executing
authentically. Only a specifically unavailable behavior may be mocked after a
complete `MockAdmission.v1`; convenience, cost, timing, or an unfavorable
result is insufficient. Sysdig/eBPF or an equivalently qualified collector
captures the calls actually emitted by the named Linux kernel boundary.
Syscalls are never fabricated, renumbered, modified, replayed as executable
evidence, or substituted. Fixture replay is test-only. On Windows, the named
capture host is the Docker Desktop Linux VM/kernel or a separately pinned Linux
VM/host, never the Windows kernel.

### Data, fusion, and final comparison boundary

- ADFA-LD is external categorical syscall benchmark evidence.
- LID-DS 2021 is external syscall evidence and capture-method precedent, with
  actual version/layout/hash/license qualification required; an honest blocked
  result is acceptable.
- HAI 23.05 is external native physical/SCADA evidence, never compressor data.
- `PTFP-Custom-v1` alone contains synchronized custom physical observations and
  authentic Linux syscalls from the same correlated runs.

Each dataset has a separate native result table. No global metric, rank, or
champion compares incompatible datasets. Only the held-out synchronized custom
campaign may quantify physical-only, syscall-only, and frozen late-fusion
outcomes on identical support. Every final claim resolves through immutable
source, decision, parameter, mock admission, profile, split, bundle, threshold,
score, truth-unlock, metric, uncertainty, limitation, and status identities.

### Optional presentation modes

Epic 18 is optional, terminal, and excluded from scientific readiness gates.
If activated, `legacy_demo` may show live/current state only with persistent
`DEMO - NOT PUBLISHED SCIENTIFIC EVIDENCE` status. `frozen_evidence` loads one
explicit immutable `G9_PASS` package, never a mutable `latest` identity, and
exposes no control or mutation route. The server rejects mutation requests;
hiding buttons is insufficient. Styling, responsive behavior, and accessibility
suggestions remain optional guidance.

### Verification gates and failure semantics

| Gate | Required evidence |
| --- | --- |
| G1 Provenance | Complete class-specific source, decision, parameter, profile, mock-admission, and legacy-quarantine validation; all active hashes/licences resolve. |
| G2 Signal v2 | Profile endpoint, conversion, round-trip, pre-clipping quality, representation, identity, timestamp, and source invariants pass. |
| G3 Consensus v2 | Deterministic Python/Go golden parity and atomic versioned state/query migration pass. |
| G4 Independent OPC | Distinct real-client round trip preserves `DataValue` quality/time and branch-isolation tests prove no consensus projection. |
| G5 Physical bundle | Immutable inference-only bundle and declared-environment replay pass without truth leakage. |
| G6 Syscall capture | Authentic workload attribution, ordering, gaps/drops/duplicates, overhead, backpressure, raw hash, and canonical replay are recorded. |
| G7 External datasets | Exact owner source, version, layout, roles, hashes, citation, licence scope, and leakage-safe split qualify independently. |
| G8 PTFP-Custom | Synchronized immutable same-run streams, quality, partitions, and protected truth pass; mixed/incomplete runs remain explicit. |
| G9 Reproducible result | Frozen scores/fusion join truth only after unlock; separate tables and paired custom ablation rebuild from manifests with limitations. |

Profile, authority, source, decision, mock, schema, hash, bundle, version, or
scope mismatch fails closed. Missing calls are not normal. Invalid OPC evidence
is never replaced by consensus. Truth leakage, mixed identities, or post-unlock
changes abort the formal run. Unknown dataset layouts are rejected. Dashboard
output never overrides artifact/evaluator truth. An unresolved planning record
may remain honestly blocked without receiving an architecture default.

### Controlling handoff status

The normative planning architecture is complete for implementation-readiness
assessment. PM owns the consolidated PRD; the Solution Architect owns these
contracts and validators; PO/SM preserves epic traceability; Emilio owns frozen
research decisions and mock scope. The development team receives no activity
authorization from this document. Sprint Planning remains blocked until a fresh
implementation-readiness report returns `READY`.

