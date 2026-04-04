---
stepsCompleted:
  - step-01-validate-prerequisites
  - step-02-design-epics
  - step-03-create-stories
  - step-04-final-validation
inputDocuments:
  - /c:/Users/emili/Desktop/Projets/parallel-truth-fingerprint-prototype/_bmad-output/planning-artifacts/prd.md
  - /c:/Users/emili/Desktop/Projets/parallel-truth-fingerprint-prototype/_bmad-output/planning-artifacts/architecture.md
  - /c:/Users/emili/Desktop/Projets/parallel-truth-fingerprint-prototype/_bmad-output/planning-artifacts/product-brief-parallel-truth-fingerprint-prototype-2026-03-23.md
---

# parallel-truth-fingerprint-prototype - Epic Breakdown

## Overview

This document provides the complete epic and story breakdown for parallel-truth-fingerprint-prototype, decomposing the requirements from the PRD, UX Design if it exists, and Architecture requirements into implementable stories.

At this stage, `prd.md` and `architecture.md` are the only authoritative requirement sources. The product brief is retained in `inputDocuments` for supporting traceability only and must not introduce, modify, or expand requirements.

## Requirements Inventory

### Functional Requirements

FR1: The system can simulate 3 sensors of one compressor.
FR2: Each edge can collect only its local sensor.
FR3: Each edge can publish data to MQTT.
FR4: Each edge can consume data from the other edges.
FR5: The system can maintain a local replicated view of the compressor at each edge.
FR6: The system can execute Byzantine consensus between the edges.
FR7: The consensus can produce trust ranking and this must be included in the package that goes to the bucket.
FR8: The system can exclude a suspicious edge from the round.
FR9: The system can expose the participating edges in each consensus round.
FR10: The system can expose the excluded edges in each consensus round and the reason for exclusion.
FR11: The system can expose the resulting trust ranking for all edges in the round.
FR12: The system can explicitly indicate when a valid consensus cannot be achieved.
FR13: The system can generate structured logs describing each consensus round.
FR14: The system can generate alerts when consensus fails.
FR15: The system can expose a fake SCADA in OPC UA.
FR16: The system can execute sensor-by-sensor comparison with tolerance.
FR17: The system can generate an alert when SCADA diverges from the consensused physical state.
FR18: The system can persist valid data in local storage (bucket).
FR19: The system can train an LSTM using normal data.
FR20: The system can generate an equipment fingerprint.
FR21: The system can generate anomaly score and normal/anomalous class.
FR22: The system can save the model/fingerprint.
FR23: The system can detect a replay scenario.

### NonFunctional Requirements

NFR1: The prototype must execute locally with a collection cadence aligned with the one-minute reference defined in the approved materials.
NFR2: The execution flow must remain suitable for live demonstration and academic inspection, without requiring high-frequency or real-time optimization.
NFR3: The prototype must preserve validation-before-trust by ensuring that shared edge state is not treated as valid until Byzantine-style consensus has completed.
NFR4: Only consensused valid data may be used for downstream processing steps such as SCADA comparison, persistence, and LSTM training or inference.
NFR5: The prototype must keep SCADA divergence alerting and fingerprint-based anomaly alerting as distinct outputs.
NFR6: The prototype must run locally.
NFR7: The prototype must explicitly indicate when valid consensus cannot be achieved.
NFR8: The prototype must produce clear, structured logs that allow each pipeline stage and each consensus round to be inspected during demonstration and evaluation.
NFR9: The structured logs must provide full traceability of each consensus round, including identification of participating edges, excluded edges, and the reasons for exclusion.
NFR10: The prototype execution must be reproducible for academic presentation and validation.
NFR11: The prototype must integrate locally with MQTT for edge communication, HART-based collection semantics for sensor acquisition, OPC UA for fake SCADA exposure, MinIO for object storage, and an LSTM service for fingerprint training and inference.
NFR12: The integration model must remain simple and local, without requiring real cloud infrastructure or external industrial systems.
NFR13: The prototype must prioritize Python.
NFR14: The prototype must be simple and demonstrable.
NFR15: The prototype must have clear logs for presentation.
NFR16: The prototype must be modular.
NFR17: The prototype must permit future replacement of the local storage by a real cloud storage solution.

### Additional Requirements

- Epic 1 Story 1 must initialize the project with `uv init --bare`.
- The project structure must remain architecture-driven and must not introduce a framework or starter that imposes unintended constraints.
- Each edge must remain an independent logical node with its own local acquisition, MQTT publication and consumption, and consensus execution context, even in local execution.
- MQTT broker infrastructure is a passive message relay only. It supports publish/subscribe exchange between edges but is not part of the trust model.
- Each edge-local replicated state is an intermediate state only and must not be treated as valid by default.
- Only the consensused valid state may feed SCADA comparison, persistence, and LSTM processing.
- Consensus output must include participating edges, excluded edges, reasons for exclusion, trust ranking, valid or invalid consensus status, and resulting consensused valid state when available.
- Structured logging must be used throughout the system, with consensus-round logs capturing round identifier, participating edges, excluded edges, exclusion reasons, trust ranking, consensus success or failure status, and consensused valid state reference when available.
- Separate alert categories must be preserved for SCADA divergence alerts, LSTM anomaly alerts, and consensus-failure alerts.
- Scenario-control and fault-injection must be first-class architectural components.
- Scenario-control and fault-injection must be implemented only through explicit upstream control points and must not bypass the normal pipeline.
- Supported controlled scenarios must include temporary removal or invalidation of one or more edges, failed-consensus scenarios, replay-style reintroduction of previously valid data, and SCADA-side manipulation that creates divergence from the consensused valid state.
- Sensor simulation must use defined normal ranges, simple time-varying realistic patterns, and controlled deviations to support anomaly and divergence scenarios.
- No raw observations, pre-consensus edge-local replicated state, or invalid-round outputs may enter the LSTM training pipeline.
- The prototype remains fully local, but local orchestration may use a mixed process/container model when that improves reproducibility and setup simplicity.
- The MQTT broker should run as a local containerized service.
- The LSTM service may run as a local containerized service.
- MinIO may run as a local containerized service.
- Edge nodes and core Python orchestration logic may remain regular local Python processes.
- Mixed local process/container orchestration is a reproducibility and setup choice only and must not change architectural boundaries, collapse decentralization, or introduce production-oriented deployment complexity.
- Service ownership and module boundaries must remain explicit across sensor simulation, edge nodes, consensus, SCADA, comparison, persistence, LSTM service, observability, scenario control, and the final lightweight demo UI layer.
- State-boundary rules, service ownership rules, and scenario-control constraints are architectural invariants and must be treated as mandatory in all implementation stories.

### Reality Boundary Notes

- Real in the prototype: MQTT-based inter-edge communication, CometBFT plus Go ABCI consensus execution, fake OPC UA logical-state service, comparison logic, MinIO persistence, local LSTM training/inference, observability, alerts, and the final lightweight demo UI layer when implemented.
- Simulated or mock in the prototype: physical sensors, compressor/process behavior, physical edge hardware, the SCADA environment itself, and the cloud environment represented locally.
- Conceptual only from the PEP/dissertation side unless explicitly re-approved for implementation: BBD/FABA as the theoretical consensus inspiration, Orion/Kafka-style cloud context-broker infrastructure, production SCADA/HMI scope, and real cloud deployment.

### UX Design Requirements

No separate UX design document exists for this workflow. The final lightweight demo UI remains constrained by the PRD and architecture, sits after the backend/runtime layers, and does not authorize a production-grade frontend scope.

### FR Coverage Map

FR1: Epic 1 - Simulate compressor sensors
FR2: Epic 1 - Local sensor collection per edge
FR3: Epic 1 - MQTT publish from each edge
FR4: Epic 1 - MQTT consume across edges
FR5: Epic 1 - Edge-local replicated compressor state
FR6: Epic 2 - Byzantine consensus execution
FR7: Epic 2 - Trust ranking included in persisted package
FR8: Epic 2 - Suspicious edge exclusion
FR9: Epic 2 - Participating-edge visibility
FR10: Epic 2 - Excluded-edge visibility and exclusion reason
FR11: Epic 2 - Full trust-ranking visibility
FR12: Epic 2 - Explicit failed-consensus outcome
FR13: Epic 2 - Structured consensus-round logs
FR14: Epic 2 - Alerts for consensus failure
FR15: Epic 3 - Fake OPC UA SCADA exposure
FR16: Epic 3 - Sensor-by-sensor comparison with configurable tolerance
FR17: Epic 3 - SCADA divergence alerting
FR18: Epic 3 - Persist valid data only
FR19: Epic 4 - Train LSTM with normal data
FR20: Epic 4 - Generate equipment fingerprint
FR21: Epic 4 - Produce anomaly score and classification
FR22: Epic 4 - Save model/fingerprint
FR23: Epic 4 - Detect replay scenario

## Epic List

### Epic 1: Reproducible Local Edge Observation Foundation
The researcher can start the local prototype, run the decentralized edge observation flow, and inspect the edge-local replicated compressor views produced through local acquisition and MQTT exchange without collapsing the architecture into a centralized design.
**FRs covered:** FR1, FR2, FR3, FR4, FR5

### Epic 2: Trusted Consensus Validation and Consensus Auditability
The researcher can validate edge contributions through Byzantine-style consensus, inspect trust ranking and exclusion decisions, and observe failed-consensus outcomes as explicit system results with full round traceability.
**FRs covered:** FR6, FR7, FR8, FR9, FR10, FR11, FR12, FR13, FR14

Prototype implementation note: the real consensus implementation in this prototype is CometBFT plus a Go ABCI application. BBD/FABA remains conceptual and theoretical inspiration from the approved PEP, not the literal runtime library used by the codebase.

### Epic 3: SCADA Integrity Comparison and Valid-State Persistence
The researcher can compare the consensused physical-side state against the logical SCADA state, receive per-sensor divergence alerts based on configurable tolerance, and persist only the valid structured consensus artifact to local storage.
**FRs covered:** FR15, FR16, FR17, FR18

### Epic 4: Fingerprint Dataset Preparation, LSTM Training, Replay Detection, and Controlled Demonstration Scenarios
The researcher can transform validated persisted artifacts into an inspectable temporal dataset, train a reusable LSTM fingerprint from validated normal data, generate anomaly outputs for replay-oriented temporal inconsistency, and execute controlled demonstration scenarios without bypassing the normal pipeline, with the final lightweight demo UI added only after the backend/runtime/services are complete.
**FRs covered:** FR19, FR20, FR21, FR22, FR23

## Epic 1: Reproducible Local Edge Observation Foundation

The researcher can start the local prototype, run the decentralized edge observation flow, and inspect the edge-local replicated compressor views produced through local acquisition and MQTT exchange without collapsing the architecture into a centralized design.

Traceability note: earlier Epic 1 wording used `compressor_power` as a simplified simulator driver. The refined interpretation, aligned to the split proposal files, is a hidden operating state such as `compressor_load_pct` or `driver_speed_pct` that drives transmitter-like observations. Story 1.6 formalizes that fidelity refinement before Epic 3 begins.

### Story 1.1: Initialize the Architecture-Driven Local Prototype Skeleton

As a researcher,
I want the local prototype skeleton initialized with the approved architecture-driven structure,
So that implementation starts from a reproducible foundation without introducing unintended framework constraints.

**Acceptance Criteria:**

**Given** the approved architecture and execution model
**When** the project is initialized
**Then** it uses `uv init --bare` as the bootstrap approach
**And** the repository structure reflects the defined logical service boundaries for edges, consensus, SCADA, comparison, persistence, LSTM, observability, scenario control, and the final lightweight demo UI layer.

**Given** the mixed local reproducibility model
**When** local orchestration files are created
**Then** they allow MQTT broker containerization and optional MinIO/LSTM containerization
**And** they do not change the architecture into a centralized or production-style deployment.

### Story 1.2: Implement Sensor Simulation With Controlled Normal Behavior

As a researcher,
I want simulated compressor sensors with explicit normal behavior ranges and patterns,
So that the prototype can produce realistic local observations for demonstration and later anomaly scenarios.

**Acceptance Criteria:**

**Given** the compressor prototype scope
**When** the sensor simulation runs
**Then** it produces temperature, pressure, and RPM values for one compressor
**And** each sensor follows a defined normal range and a simple time-varying behavior pattern driven by a hidden compressor operating state such as `compressor_load_pct` or `driver_speed_pct`
**And** those ranges remain configurable prototype-default plausible ranges, not plant-calibrated truth.

**Given** the physical behavior model
**When** the hidden operating state increases or decreases
**Then** higher operating state results in higher expected temperature, pressure, and RPM behavior
**And** lower operating state results in lower expected values across those variables.

**Given** the required simulation realism
**When** temperature increases
**Then** the simulation increases sensor noise and variability for temperature, pressure, and RPM
**And** that temperature-driven noise model is implemented only in the sensor simulation layer.

**Given** the architecture constraints for scenario support
**When** the simulation layer is implemented
**Then** it exposes explicit upstream control points for later deviation and fault-injection scenarios
**And** those control points do not bypass the normal observation pipeline.

### Story 1.3: Implement Logically Independent Edge Acquisition Services

As a researcher,
I want each edge to acquire only its own local sensor through pre-PLC acquisition semantics,
So that the prototype preserves decentralized physical-side observation even on one machine.

**Acceptance Criteria:**

**Given** three logical edge nodes
**When** the local edge services run
**Then** Edge 1 acquires only temperature, Edge 2 only pressure, and Edge 3 only RPM
**And** each edge uses pre-PLC physical acquisition semantics (conceptual HART / 4-20 mA reference) at the local acquisition boundary.

**Given** the payload-driven data model
**When** an edge emits a local acquisition payload
**Then** it follows the raw HART-style payload structure used by the project
**And** the edge interprets a simulated transmitter observation and maps it into the gateway payload while preserving PV/SV semantics
**And** `PV` is mandatory, `SV` is optional and sensor-justified, and generic equipment context is not stored in `SV`
**And** it includes process variables, loop current, diagnostics, and available local physics metrics needed for downstream enrichment.

**Given** local co-location on one machine
**When** edge services execute
**Then** each edge maintains its own acquisition flow and local runtime context
**And** no shared mutable state collapses the decentralized edge model.

### Story 1.4: Implement MQTT Exchange and Shared State Reconstruction

As a researcher,
I want each edge to publish its local observation and consume the others through MQTT,
So that every edge reconstructs its own local replicated compressor-state view needed for later validation.

**Acceptance Criteria:**

**Given** active edge services and a local MQTT broker
**When** an edge collects a local observation
**Then** it publishes that observation through MQTT
**And** the other edges consume it through the brokered publish/subscribe flow while the broker remains a passive message relay only.

**Given** cross-edge observation exchange
**When** all current sensor observations are received
**Then** each edge reconstructs its own local replicated view containing temperature, pressure, and RPM from its own sensor data plus peer data received through MQTT
**And** that edge-local replicated state is explicitly marked or handled as non-validated and not yet valid for downstream processing.

### Story 1.5: Add Observation-Flow Logging and Demonstration Visibility

As a researcher,
I want clear logs and observable state for the acquisition and MQTT replication flow,
So that the decentralized observation stage is demonstrable and traceable before consensus is introduced.

**Acceptance Criteria:**

**Given** the sensor simulation and edge communication flow
**When** the prototype runs
**Then** logs show sensor generation, local edge acquisition, MQTT publication, MQTT consumption, and shared-state reconstruction
**And** the outputs are presentation-friendly and reproducible.

**Given** the trust-boundary rules
**When** an edge-local replicated state is displayed or logged
**Then** it is distinguishable from future consensused valid state
**And** the system does not present it as validated output.

**Given** optional minimal visualization support
**When** an edge-local replicated intermediate state is shown to support demonstration
**Then** it may be displayed through logs, simple charts, or simple metrics
**And** it remains clearly identified as non-validated intermediate state.

### Story 1.6: Refine Sensor Simulation and Edge Acquisition Fidelity

As a researcher,
I want the simulated compressor operating state, transmitter-side observation, and edge acquisition payload to be modeled more faithfully,
So that the prototype preserves pre-PLC physical acquisition semantics without redesigning the existing MQTT, consensus, SCADA, persistence, or LSTM pillars.

**Acceptance Criteria:**

**Given** the refined acquisition-fidelity boundary
**When** the simulator and edge acquisition path are updated
**Then** the acquisition path follows exactly three layers: hidden compressor/process state, simulated transmitter observation, and gateway acquisition payload
**And** the hidden operating state such as `compressor_load_pct` or `driver_speed_pct` deterministically influences temperature, pressure, and RPM.

**Given** the transmitter-side semantics
**When** a sensor observation is converted into a gateway payload
**Then** `PV` is mandatory for every transmitter-style sensor
**And** `SV` is optional and only appears when it has a defensible transmitter-side meaning for that sensor type
**And** generic compressor context is not stored in `SV`.

**Given** the downstream architectural constraints
**When** the refined payload is emitted
**Then** it remains HART-inspired and includes `device_info`, `process_data`, `diagnostics`, `loop_current_ma`, `pv_percent_range`, and simple physics metrics
**And** it remains suitable for later consensus, SCADA comparison, and LSTM training without redesigning those downstream pillars.

**Given** the implementation guardrails
**When** this fidelity refinement is implemented
**Then** it preserves existing downstream contracts by default
**And** only additive optional fields may be introduced if strictly required
**And** MQTT, CometBFT, fake OPC UA SCADA, MinIO, and downstream LSTM remain unchanged.

## Epic 2: Trusted Consensus Validation and Consensus Auditability

The researcher can validate edge contributions through Byzantine-style consensus, inspect trust ranking and exclusion decisions, and observe failed-consensus outcomes as explicit system results with full round traceability.

### Story 2.1: Define Consensus Contracts and Trust-State Models

As a researcher,
I want explicit consensus contracts and trust-state models,
So that consensus outcomes are represented clearly and the system cannot confuse edge-local replicated state with validated state.

**Acceptance Criteria:**

**Given** the approved architecture constraints
**When** consensus-related contracts are implemented
**Then** they include at least consensus round input, consensus result, trust ranking, exclusion details, and consensused valid state
**And** the contracts keep edge-local replicated intermediate state distinct from consensused valid state.

**Given** the requirement for explicit auditability
**When** a consensus result is produced
**Then** it can represent both successful consensus and failed-consensus outcomes
**And** it includes participating edges, excluded edges, reasons for exclusion, and round status.

**Given** the payload-driven architecture
**When** consensus contracts are finalized
**Then** they define the transformation from raw HART-style edge payloads into a unified consensused payload
**And** that unified payload carries the data needed downstream, including process data, loop current, physics metrics, diagnostics, trust metadata, and any additive optional context fields explicitly present in the refined payload model.

### Story 2.2: Implement Byzantine-Style Consensus Evaluation

As a researcher,
I want the system to evaluate edge contributions through Byzantine-style consensus,
So that suspicious edge data is filtered before any state is trusted.

**Acceptance Criteria:**

**Given** each edge has built its own local replicated state from self-observation plus peer observations
**When** a consensus round executes
**Then** the system evaluates edge contributions and produces a trust ranking for all participating edges
**And** it excludes suspicious edge contributions within the active round when required.

**Given** a successful consensus round
**When** the round completes
**Then** the system produces a consensused valid state
**And** that state is the only state marked as valid for downstream use.

### Story 2.3: Implement Failed-Consensus Handling as an Explicit Outcome

As a researcher,
I want the system to signal when valid consensus cannot be achieved,
So that consensus failure is observable and handled as part of the architecture rather than hidden as a generic error.

**Acceptance Criteria:**

**Given** a round where insufficient valid edges remain
**When** the consensus engine cannot produce a valid state
**Then** it emits an explicit failed-consensus outcome
**And** it does not emit a consensused valid state for downstream processing.

**Given** a failed-consensus outcome
**When** the round result is recorded
**Then** the result identifies participating edges, excluded edges, and reasons for exclusion
**And** the system blocks downstream stages that require a consensused valid state.

### Story 2.4: Add Consensus Round Logging and Exclusion Visibility

As a researcher,
I want each consensus round to be fully traceable in logs and outputs,
So that I can explain which edges participated, which were excluded, and why the trust decision was made.

**Acceptance Criteria:**

**Given** any consensus round
**When** the round is executed
**Then** structured logs capture the round identifier, participating edges, trust ranking, excluded edges, exclusion reasons, and round success or failure status
**And** the logs remain clear enough for academic demonstration and evaluation.

**Given** a suspicious-edge exclusion
**When** the exclusion is logged or displayed
**Then** the output identifies exactly which edge was excluded
**And** it records the reason for exclusion in a structured and inspectable form.

**Given** the unified payload-driven data model
**When** consensus observability is implemented
**Then** consensus logs and outputs follow the same structured payload conventions used by downstream stages
**And** they preserve visibility of both trust decisions and the resulting consensused payload state when available.

### Story 2.5: Generate Consensus Failure Alerts

As a researcher,
I want explicit alerts when consensus fails,
So that critical trust-breakdown conditions are visible during demonstration and evaluation.

**Acceptance Criteria:**

**Given** a consensus failure caused by loss of quorum
**When** the round completes
**Then** the system generates a consensus-related alert
**And** that alert remains distinct from future SCADA divergence and LSTM anomaly alerts.

**Given** a consensus-related alert
**When** it is emitted
**Then** it references the associated round outcome and exclusion context
**And** it does not bypass the normal consensus execution path.

## Epic 3: SCADA Integrity Comparison and Valid-State Persistence

The researcher can compare the consensused physical-side state against the logical SCADA state, receive per-sensor divergence alerts based on configurable tolerance, and persist only the valid structured consensus artifact to local storage.

### Story 3.1: Implement Fake OPC UA Logical SCADA Service

As a researcher,
I want the logical supervisory state to be exposed through a realistic local SCADA interface,
So that the prototype prioritizes industrial alignment without adding production complexity.

**Acceptance Criteria:**

**Given** the approved local prototype scope
**When** the SCADA component is implemented
**Then** the preferred implementation is a simple local Python OPC UA server
**And** it represents the logical supervisory state rather than the physical truth source.

**Given** the controlled demonstration scenarios
**When** SCADA-side divergence behavior is exercised
**Then** the SCADA layer can intentionally produce replayed, frozen, or offset supervisory values
**And** those values remain part of the normal comparison pipeline as a logical-state divergence source.

### Story 3.2: Implement Sensor-by-Sensor SCADA Comparison on Consensused Valid Payloads

As a researcher,
I want SCADA comparison to use simple sensor-by-sensor configurable tolerance as the core behavior,
So that divergence is evaluated in a defensible, explainable, and prototype-scaled way.

**Acceptance Criteria:**

**Given** a consensused valid payload and current SCADA state
**When** the comparison service executes
**Then** it compares temperature, pressure, and RPM sensor by sensor using configurable tolerance against the current SCADA values
**And** it may attach contextual evidence from the payload, physics metrics, or diagnostics when that helps explain the result.

**Given** the approved scope guardrails
**When** comparison logic is implemented
**Then** configurable tolerance remains the core decision rule
**And** optional contextual evidence does not replace that core rule.

**Given** no consensused valid state exists
**When** comparison would otherwise run
**Then** the comparison service remains blocked
**And** it does not execute against edge-local replicated intermediate state or invalid consensus output.

### Story 3.3: Produce Structured Per-Sensor SCADA Comparison Outputs and Alerts

As a researcher,
I want structured comparison outputs for each sensor,
So that SCADA divergence can be explained clearly and remain separate from other alert paths.

**Acceptance Criteria:**

**Given** a comparison between consensused valid payloads and SCADA values
**When** the comparison completes
**Then** the output for each sensor includes the consensused physical value, the SCADA value, the tolerance-based evaluation, optional contextual evidence when present, and a divergence classification
**And** the format remains consistent with the unified payload-driven design.

**Given** divergence is detected
**When** an alert is emitted
**Then** the system generates a SCADA divergence alert as a separate alert path
**And** it remains distinct from consensus failure alerts and LSTM anomaly alerts.

### Story 3.4: Persist Structured Consensus Artifacts Only for Valid States

As a researcher,
I want valid structured consensus artifacts persisted in local storage,
So that downstream training and audit evidence use only validated data.

**Acceptance Criteria:**

**Given** a successful consensus outcome
**When** persistence executes
**Then** the stored artifact includes at least timestamp, consensus_state based on the unified payload, trust_scores, excluded_edges, SCADA comparison results, and diagnostics
**And** it is written only for valid consensused states.

**Given** a failed consensus outcome, any edge-local replicated intermediate state, or other non-validated data
**When** persistence would otherwise execute
**Then** the system blocks persistence of that data as valid artifact
**And** invalid or pre-consensus data does not enter the training-ready storage path.

### Story 3.5: Add Payload-Driven Observability for Comparison and Persistence

As a researcher,
I want logs and outputs to reflect the full payload-driven pipeline through comparison and persistence,
So that the system remains explainable and auditable during demonstration.

**Acceptance Criteria:**

**Given** edge contributions, consensus results, SCADA comparison, and persistence actions
**When** the prototype runs
**Then** logs reflect those stages using the agreed payload structure
**And** they show excluded edges, comparison outcomes, and persistence actions in a presentation-ready format.

**Given** comparison or persistence is blocked because no consensused valid state exists
**When** the block occurs
**Then** the blocked flow is logged explicitly
**And** the output makes clear that the pipeline stopped for trust-boundary reasons rather than silent failure.

## Epic 4: Fingerprint Dataset Preparation, LSTM Training, Replay Detection, and Controlled Demonstration Scenarios

The researcher can transform validated persisted artifacts into an inspectable temporal dataset, train a reusable LSTM fingerprint from validated normal data, generate anomaly outputs for replay-oriented temporal inconsistency, and execute controlled demonstration scenarios without bypassing the normal pipeline.

Implementation note: Epic 4 has two explicit validation levels that must remain visible in story wording and story closeout.
- Runtime-valid: the dataset path, training path, persistence path, and model save/load path execute successfully with the approved local stack.
- Meaningful fingerprint-valid: the dataset is persisted as an inspectable artifact and the normal-history base is large enough to support an academically honest temporal fingerprint claim.

Dataset note: the only approved Epic 4 input source remains validated persisted `ValidConsensusArtifactRecord` objects from MinIO. No raw observations, edge-local replicated state, failed-consensus outputs, or non-normal scenario runs may enter the fingerprint training path.

Dataset artifact note: the temporal dataset must become a real persisted and inspectable prototype artifact under the existing MinIO boundary. The preferred local representation is:
- `fingerprint-datasets/<dataset_id>.manifest.json`
- `fingerprint-datasets/<dataset_id>.windows.npz`

Testing rule: every Epic 4 development story is incomplete unless it records:
1. what was tested
2. exact commands executed
3. test results
4. what real runtime behavior was validated
5. what limitations still remain

### Story 4.1: Build Normal-Only Training Windows From Validated Persisted Artifacts

As a researcher,
I want training-ready temporal windows built only from validated persisted artifacts,
So that the fingerprint path learns from the real trusted prototype pipeline using deterministic, reviewable dataset-building logic.

**Acceptance Criteria:**

**Given** persisted consensus artifacts in local storage
**When** the dataset-building process runs
**Then** it selects only valid consensused records marked as normal for training
**And** it excludes raw edge payloads, edge-local replicated intermediate state, failed-consensus outputs, and other non-validated data.

**Given** the payload-driven architecture
**When** training sequences are derived
**Then** they retain the complete relevant structure from the persisted artifacts, including process variables, loop current, physics metrics, diagnostics, SCADA comparison context, and other additive optional fields that exist in the approved payload model
**And** they do not reduce the fingerprint input to a value-only or arbitrarily flattened subset.

**Given** the prototype demonstration scope
**When** temporal sequences are prepared
**Then** they use a simple fixed-length sequence window aligned with the collection cadence
**And** the sequence length remains sufficient for demonstration without introducing unnecessary complexity.

**Given** the current story-responsibility boundary
**When** Story 4.1 completes
**Then** it owns validated artifact selection, chronological ordering, feature extraction, and fixed-length window generation
**And** it may emit in-memory manifest and window objects for immediate use
**But** it does not own persisted dataset artifact generation or adequacy evaluation, which belong to Story 4.2A.

### Story 4.2A: Persist Inspectable Training Dataset Artifacts and Establish Normal-History Adequacy

As a researcher,
I want the normal-only temporal dataset to be persisted as an inspectable MinIO artifact and evaluated against an explicit adequacy gate,
So that the fingerprint path is reproducible, auditable, reusable, and academically honest before inference work begins.

**Acceptance Criteria:**

**Given** the in-memory dataset output from Story 4.1
**When** Story 4.2A executes
**Then** it persists a real dataset artifact to MinIO rather than leaving the dataset only in memory.

**Given** the approved storage boundary
**When** the dataset artifact is written
**Then** it uses the existing MinIO path under a dedicated dataset prefix
**And** the preferred representation is:
- `fingerprint-datasets/<dataset_id>.manifest.json`
- `fingerprint-datasets/<dataset_id>.windows.npz`

**Given** the need for transparency and reproducibility
**When** the dataset manifest is persisted
**Then** it records at least dataset id, creation timestamp, source bucket and prefix, chronological ordering rule, sequence length, stride, overlap behavior, feature schema, selected artifact keys, skipped artifact keys and reasons, eligible artifact count, generated window count, tensor shape, and dataset purpose.

**Given** the need for temporal reuse
**When** the windows artifact is persisted
**Then** it stores the generated temporal windows in a reusable form
**And** it preserves the mapping between windows and their artifact keys, round ids, and timestamps.

**Given** the academic-strength requirement
**When** dataset adequacy is evaluated
**Then** the system distinguishes between runtime-valid dataset generation and meaningful fingerprint-valid dataset adequacy
**And** it records the current adequacy status explicitly.

**Given** the prototype-default adequacy floor
**When** adequacy is evaluated
**Then** the default floor is at least 30 eligible normal persisted artifacts and 20 generated windows
**And** the result is recorded explicitly in the dataset manifest or directly associated metadata.

### Story 4.2: Train and Save a Reusable Local LSTM Fingerprint Model

As a researcher,
I want the system to train and save an LSTM fingerprint model from the approved normal-only dataset path,
So that the prototype can validate the real local training path now and later support a more meaningful temporal fingerprint claim once dataset adequacy is satisfied.

**Acceptance Criteria:**

**Given** a prepared normal training dataset
**When** model training executes
**Then** the system trains an LSTM model for the compressor physical-operational fingerprint
**And** it saves the resulting model or fingerprint artifact for reuse.

**Given** the project scope
**When** the training flow is implemented
**Then** it remains a simple local component within the prototype pipeline
**And** it does not require separate deployment, separate containerization, or distributed ML infrastructure.

**Given** the corrected Epic 4 dataset boundary
**When** Story 4.2 is fully validated
**Then** the trainer consumes the persisted dataset artifact path introduced by Story 4.2A rather than relying only on in-memory dataset objects.

**Given** the distinction between runtime validation and fingerprint meaningfulness
**When** Story 4.2 validation is recorded
**Then** the story explicitly distinguishes runtime-valid training from meaningful fingerprint-valid training
**And** it does not claim academically strong fingerprint readiness if the dataset adequacy gate has not yet been satisfied.

### Epic 4 Sequencing Note

Story 4.3 remains blocked until Story 4.2A is complete and Story 4.2 has been revalidated against the persisted dataset artifact path. Runtime-valid model training alone is not sufficient to open inference if the dataset artifact and normal-history adequacy gate are still missing.

### Story 4.3: Implement Fingerprint Inference With Anomaly Score and Classification

As a researcher,
I want inference outputs with anomaly score and normal/anomalous classification,
So that temporal behavior can be evaluated during execution.

**Acceptance Criteria:**

**Given** a saved fingerprint model and valid runtime input
**When** inference executes
**Then** the system produces an anomaly score and a normal/anomalous classification
**And** the result remains distinct from SCADA divergence and consensus-failure outputs.

**Given** runtime inference input
**When** the inference path runs
**Then** it consumes only valid downstream inputs derived from the approved persisted payload pipeline
**And** it does not accept non-validated state as inference input.

### Story 4.4: Detect SCADA-Side Replay as a Behavioral Anomaly

As a researcher,
I want SCADA-side replay behavior to produce anomaly output through the fingerprint path,
So that the prototype demonstrates temporal inconsistency detection without redefining replay as a consensus or comparison problem.

**Acceptance Criteria:**

**Given** a controlled replay scenario
**When** the SCADA layer provides previously valid, frozen, or replayed supervisory values
**Then** the edge layer and consensus continue defining the trusted physical reference
**And** the replay origin remains on the SCADA side rather than in edge or physical payload generation.

**Given** a SCADA-side replay condition
**When** the scenario flows through the normal pipeline over time
**Then** the LSTM inference path can identify temporal inconsistency and produce anomaly behavior
**And** replay detection is positioned as a behavioral anomaly rather than a consensus trust failure.

**Given** a replay scenario
**When** SCADA comparison also executes
**Then** direct SCADA comparison may or may not detect the issue depending on the case
**And** the fingerprint path remains the intended mechanism for detecting the temporal anomaly.

### Story 4.5: Implement Scenario-Control for Demonstration Without Pipeline Bypass

As a researcher,
I want controlled fault-injection and scenario-control capabilities for replay, SCADA divergence, and edge invalidation,
So that demonstrations can exercise the full architecture faithfully.

**Acceptance Criteria:**

**Given** the approved demonstration scenarios
**When** scenario-control is implemented
**Then** it supports edge invalidation or removal, SCADA-side replayed, frozen, or offset values, and other approved divergence behaviors
**And** those controls operate through explicit upstream control points.

**Given** a controlled scenario is activated
**When** the prototype runs
**Then** the data still flows through sensor simulation, edge acquisition, MQTT exchange, consensus, SCADA comparison, persistence, and LSTM inference as applicable
**And** scenario-control does not inject outputs directly into downstream stages.

### Story 4.6: Build the Final Lightweight SCADA-Inspired Demo UI Layer

As a researcher,
I want a lightweight SCADA-inspired demo interface for the final presentation,
So that I can observe the prototype behavior and trigger approved scenarios without creating a second parallel architecture.

**Acceptance Criteria:**

**Given** the backend/runtime/services are complete and stable
**When** the final demo layer is implemented
**Then** it is treated as the last implementation layer
**And** it consumes existing logs, runtime outputs, and simulator/scenario-control hooks rather than introducing a second parallel architecture.

**Given** the operator-facing demo goals
**When** the interface is rendered
**Then** it shows interactive system-log visualization, a visual representation of the compressor and its sensors, and live numeric sensor values directly on the compressor view
**And** it remains scoped to one compressor only.

**Given** the approved simulator controls
**When** the operator changes compressor power from `0%` to `100%`
**Then** that action flows through the existing simulator control path
**And** temperature, pressure, and RPM respond consistently with the existing behavior model.

**Given** the approved demonstration scenarios
**When** the operator triggers replay simulation or damaged/faulty edge simulation from the UI
**Then** those actions use the existing scenario-control hooks
**And** they continue through the normal MQTT, consensus, SCADA comparison, persistence, and LSTM paths as applicable.

**Given** the visual direction for the demo
**When** the UI is designed and implemented
**Then** it is SCADA-inspired in layout style and operator feel only
**And** it remains lightweight and demo-oriented rather than becoming a production-grade industrial HMI.

## Mini-Epic 5: Demo Explainability, Operational Visualization, and Evidence-Guided Dashboard Refinement

Mini-Epic 5 is a bounded demo-readiness layer on top of the implemented Epic 4 dashboard and runtime. It does not change the four research pillars, replace the existing runtime/control path, or introduce new services or storage boundaries.

Scope boundary:

- In scope:
  - interpreted operational events derived from existing runtime/log/state outputs
  - optional raw-log access alongside interpreted views
  - component-scoped event/log inspection
  - visual operational pipeline and live component state overlays
  - human-readable status translation and startup-to-now evidence summaries
  - demo-guidance panels derived from existing runtime, scenario, lifecycle, and evidence state
- Out of scope:
  - changes to the runtime/control architecture
  - new backend services or persistence layers
  - new ML logic or new anomaly engines
  - enterprise-grade SCADA/HMI features
  - fake backend behavior for demo polish

Sequencing note:

- The approved Epic 5 implementation order is:
  - Story 5.1
  - Story 5.3
  - Story 5.2
  - Story 5.4
- This order is intentional: interpreted evidence and explainability are established before the visual pipeline and final demo-guidance layer.

### Story 5.1: Add Interpreted Operational Event Timeline with Component-Scoped Raw Log Access

As a researcher and demo operator,
I want the dashboard to present interpreted operational events globally and by component while preserving raw logs as technical ground truth,
So that I can explain the current runtime state without losing access to the underlying evidence.

**Acceptance Criteria:**

**Given** the existing runtime/log/state outputs
**When** the dashboard is rendered
**Then** it shows a global interpreted event timeline derived from current runtime, cycle-history, and operator-action state
**And** it does not invent events that are not traceable to those existing sources.

**Given** the component-scoped inspection requirement
**When** the operator selects a dashboard component
**Then** the dashboard shows interpreted events and raw logs for that same component
**And** raw logs remain available as technical ground truth.

**Given** the minimum supported component set
**When** the component log explorer is used
**Then** it supports:
- compressor
- temperature sensor
- pressure sensor
- rpm sensor
- edge 1
- edge 2
- edge 3
- consensus
- SCADA comparison
- fingerprint / LSTM lifecycle

### Story 5.3: Add Human-Readable Status Translation and "What Changed Since Startup" Evidence View

As a researcher and demo operator,
I want the dashboard to translate technical runtime state into human-readable explanations and summarize what changed since startup,
So that I can explain the current prototype run honestly during the live demo without decoding raw metadata on the fly.

**Acceptance Criteria:**

**Given** the current lifecycle, consensus, replay, and fingerprint outputs
**When** the dashboard is rendered
**Then** it translates technical labels into human-readable explanations
**And** it keeps the runtime-valid-only limitation explicit.

**Given** the startup-to-now evidence requirement
**When** the dashboard is rendered
**Then** it shows:
- runtime start time
- elapsed runtime
- current cycle count
- valid artifact growth
- whether training has happened
- when training first happened
- whether the current model was reused or retrained
- current model identity if available
- what has happened already
- what has not happened yet
- what is expected next

### Story 5.2: Add Visual Operational Pipeline and Live Component State Overlay

As a researcher and demo operator,
I want the dashboard to show the prototype as a visual operational pipeline with live interpreted state per component,
So that a professor or evaluator can understand the real runtime flow without reading developer-oriented JSON blocks.

**Acceptance Criteria:**

**Given** the live dashboard state
**When** the visual pipeline is rendered
**Then** it shows:
- compressor
- temperature sensor
- pressure sensor
- rpm sensor
- edge 1
- edge 2
- edge 3
- consensus
- SCADA-side system/computer view
- SCADA comparison
- fingerprint / LSTM stage

**Given** the visual operational flow requirement
**When** the operator changes compressor power and the runtime advances
**Then** the visual pipeline shows the cause/effect path:
- power -> sensors -> edges -> consensus -> SCADA comparison -> fingerprint
**And** the values shown are derived from the real runtime state rather than UI-only effects.

**Given** the Story 5.1 component evidence model
**When** the operator interacts with a major pipeline box
**Then** that box can expose or link to its component-scoped interpreted events and raw logs.

### Story 5.4: Add Demo Guidance Panels for "What Is Happening", "What Should Happen", and "What Changed"

As a researcher and demo operator,
I want the dashboard to explain what the system is doing, what should happen, and what has changed in concise demo-oriented language,
So that the prototype can support a live academic demonstration without requiring constant verbal decoding of internal state.

**Acceptance Criteria:**

**Given** the current runtime, scenario, lifecycle, and evidence state
**When** the dashboard is rendered
**Then** it includes concise guidance panels explaining:
- what the system is doing
- what should happen during normal operation
- what should change during replay
- what should change during SCADA divergence
- what evidence indicates success or anomaly

**Given** the run-progress requirement
**When** the dashboard is rendered
**Then** it explicitly communicates:
- what has happened already
- what has not happened yet
- what is expected next

**Given** the academic-honesty requirement
**When** the guidance panels describe fingerprint behavior
**Then** they do not overclaim ML strength or dataset adequacy
**And** they preserve access to raw technical evidence.

## Mini-Epic 6: Fingerprint Readiness and Architecture-Aligned Dashboard Correction

Mini-Epic 6 is a bounded stabilization and demo-credibility layer on top of the implemented prototype. It preserves the five real pillars exactly as they already exist:

- acquisition of sensor values
- decentralization across edges
- Byzantine consensus across edges
- comparison between consensused data and SCADA data
- LSTM-based fingerprint generation

This mini-epic does not add a new research scope. It strengthens how the existing fingerprint is evidenced and how the existing dashboard reflects the real architecture and runtime state.

Scope boundary:

- In scope:
  - fingerprint readiness evidence derived from existing dataset, model, inference, and runtime artifacts
  - domain-correct user-facing naming for fingerprint and dashboard elements
  - semantic correction of dashboard state mapping against the current runtime payload
  - architecture-aligned grouping of sensors, edges, consensus, SCADA comparison, and fingerprint stages
  - clearer dashboard hierarchy and standardized collapse behavior
  - explicit no-quorum and SCADA-divergence blocking semantics in the visible demo path
  - replay behavior aligned to a richer SCADA-side payload while keeping the simple SCADA comparison rule narrow
- Out of scope:
  - new sensors, new edge roles, or changes to the five pillars
  - new ML model families, new anomaly engines, or training-policy redesign
  - new services, new persistence boundaries, or architecture changes
  - fake UI-only behavior or enterprise-grade SCADA/HMI redesign

Sequencing note:

- The safest implementation order is:
  - Story 6.2
  - Story 6.1
  - Story 6.3
  - Story 6.4
  - Story 6.5
- This order is intentional:
  - first correct dashboard truthfulness and state mapping
  - then expose stronger fingerprint readiness evidence
  - then reorganize the UI around the corrected architecture and evidence model
  - then make blocking security and supervisory decisions explicit in the live path
  - then strengthen replay so the fingerprint alert is demonstrably distinct from simple SCADA divergence

Execution gate note:

- Stories 6.4 and 6.5 are to be implemented one at a time.
- Each story must complete its own QA pass before the next story begins.
- The intended order is:
  - Story 6.4 development
  - Story 6.4 QA validation
  - Story 6.5 development
  - Story 6.5 QA validation

### Story 6.1: Establish Fingerprint Readiness Evidence and Meaningful-Validity Gate

As a researcher and demo operator,
I want the prototype to present explicit fingerprint readiness evidence and a meaningful-validity gate derived from existing artifacts,
So that the fingerprint can be explained honestly and more defensibly during an academic demonstration without changing the ML architecture.

**Acceptance Criteria:**

**Given** the existing persisted dataset, model metadata, lifecycle state, and inference outputs
**When** fingerprint readiness is presented in the prototype
**Then** it derives its readiness summary from those existing artifacts only
**And** it does not add a new ML model or a new anomaly engine.

**Given** the adequacy-driven readiness requirement
**When** the fingerprint readiness state is evaluated
**Then** it explicitly distinguishes between:
- `runtime_valid_only`
- `meaningful_fingerprint_valid`
**And** it ties that distinction back to the approved adequacy floor of:
- 30 eligible normal artifacts
- 20 generated windows

**Given** the model-provenance requirement
**When** readiness evidence is shown
**Then** it includes at minimum:
- model identity
- source dataset identity
- training window count
- threshold origin
- current limitation statement

**Given** the bounded evidence-matrix requirement
**When** the fingerprint is explained for demo purposes
**Then** the prototype can summarize evidence for at least:
- normal operation
- compressor-power variation
- replay or freeze behavior
- SCADA divergence as a separate non-fingerprint channel

**Given** the operator-facing wording requirement
**When** readiness and limitation text is shown in the UI or dashboard
**Then** it uses domain language such as fingerprint model, training adequacy, replay detection, or anomaly evidence
**And** it does not reference internal delivery labels such as Story 4.3, Story 4.4, or other BMAD story numbers.

### Story 6.2: Correct Dashboard Semantic Mapping and Runtime-State Binding

As a researcher and demo operator,
I want the dashboard to reflect the real architecture and the real runtime payload correctly,
So that the UI stops misrepresenting sensor, edge, SCADA-comparison, and fingerprint state during the demo.

**Acceptance Criteria:**

**Given** the pipeline architecture
**When** sensor cards are rendered
**Then** they show only sensor-layer concepts such as:
- sensor identity
- live physical value
- unit
- timestamp or live-status note
**And** they do not show SCADA-comparison or replicated-edge concepts on the sensor layer.

**Given** the edge-layer requirement
**When** edge cards are rendered
**Then** they show edge-layer concepts such as:
- acquisition status
- published observations
- peer-consumed observations
- replicated local view status
**And** they read those values from the real edge runtime payload fields.

**Given** the SCADA-comparison requirement
**When** the dashboard renders comparison and divergence state
**Then** it reads the structured comparison payload correctly from the current runtime state
**And** comparison semantics appear in the SCADA-comparison stage rather than on the sensor cards.

**Given** the current event and raw-log views
**When** the operator inspects component-scoped evidence
**Then** interpreted events, raw logs, and pipeline summaries are bound to the same underlying runtime state shape
**And** displayed values match live runtime logs for a cycle under inspection.

**Given** the operator-facing wording requirement
**When** runtime state, limitation notes, and pipeline labels are shown
**Then** they use architecture-correct domain names
**And** they do not expose internal story references such as Story 4.6, Story 5.1, or similar implementation labels.

### Story 6.3: Reorganize the Dashboard into Architecture-Aligned Pipeline Blocks

As a researcher and demo operator,
I want the dashboard to be reorganized into architecture-aligned blocks with consistent hierarchy and collapse behavior,
So that the prototype becomes easier to read and explain on a normal laptop-sized screen during the demo.

**Acceptance Criteria:**

**Given** the corrected dashboard semantics
**When** the dashboard layout is reorganized
**Then** it groups all sensors into one block
**And** it groups all edges into one block
**And** it presents the downstream pipeline in clear later-stage sections for:
- consensus
- SCADA source and comparison
- fingerprint and replay behavior

**Given** the hierarchy requirement
**When** the dashboard first loads
**Then** the initial viewport emphasizes:
- runtime health
- operator controls
- the current pipeline state
- the current evidence summary
**And** lower-priority technical sections do not dominate the first view.

**Given** the raw-evidence requirement
**When** the dashboard is reorganized
**Then** raw logs, deep technical state, and channel details remain available
**But** they are secondary to the main operator view and use standardized collapse or hide behavior.

**Given** the user-facing naming requirement
**When** grouped sections and labels are shown
**Then** they use architecture and domain language that a professor or evaluator can understand directly
**And** they do not rely on internal story numbering or implementation jargon.

### Story 6.4: Make No-Quorum and SCADA-Divergence Blocking Explicit in the Pipeline

As a researcher and demo operator,
I want no-quorum and SCADA-divergence outcomes to appear as explicit blocking decisions in the pipeline,
So that the demo shows exactly why a cycle was stopped and why no downstream payload was forwarded.

**Acceptance Criteria:**

**Given** the distributed-validation requirement
**When** valid participants remaining after exclusions fall below quorum
**Then** the prototype shows an explicit no-quorum alert in the consensus stage
**And** it explains that no trusted payload was produced because majority was not reached
**And** it does not present this as a generic runtime crash.

**Given** the blocked-forwarding rule
**When** no quorum is reached
**Then** the cycle does not advance to:
- SCADA comparison
- valid-artifact persistence
- downstream fingerprint evaluation
**And** the dashboard makes that blocked progression visible.

**Given** the supervisory-validation rule
**When** SCADA comparison is executed
**Then** the divergence decision is based only on:
- temperature
- pressure
- rpm
**Even if** the SCADA-side payload carries richer contextual fields for later stages.

**Given** the SCADA-integrity requirement
**When** any of those supervisory values diverge beyond tolerance
**Then** the prototype emits a SCADA-divergence alert
**And** it stops the cycle from progressing further downstream for that cycle.

**Given** the alert-separation requirement
**When** no-quorum, SCADA divergence, and fingerprint anomaly are displayed
**Then** they remain clearly distinct in meaning and pipeline location:
- no quorum = distributed validation refused to produce trusted data
- SCADA divergence = supervisory values do not match the trusted committed state
- fingerprint anomaly = behavioral inconsistency detected after trusted and supervisory checks

### Story 6.5: Detect Replay Through Richer SCADA-Side Behavioral Payload

As a researcher and demo operator,
I want replay behavior to be evaluated from a richer SCADA-side behavioral payload while keeping the simple SCADA comparison rule narrow,
So that replay can be demonstrated as a fingerprint-level anomaly rather than only as an obvious supervisory mismatch.

**Acceptance Criteria:**

**Given** the SCADA-side contract requirement
**When** the fake SCADA stage projects its state
**Then** it carries:
- the three supervisory values used for comparison
- richer behavioral and contextual fields needed for replay-oriented fingerprint evaluation
**And** those richer fields remain distinct from the narrow SCADA-comparison decision rule.

**Given** the comparison-boundary rule
**When** SCADA divergence is decided
**Then** the decision still uses only:
- temperature
- pressure
- rpm
**And** it does not widen into a richer multi-field comparison engine.

**Given** the replay-scenario requirement
**When** SCADA replay is activated after normal history exists
**Then** the replayed SCADA-side state can preserve or reintroduce stale behavioral detail while top-level supervisory values may still appear plausible
**So that** replay success is not defined only by obvious SCADA divergence.

**Given** the fingerprint-path requirement
**When** replay behavior is evaluated
**Then** the anomaly decision is driven by the fingerprint or replay-behavior stage using the richer SCADA-side payload
**And** replay can be surfaced even when consensus succeeded and SCADA divergence is absent or weak.

**Given** the training-integrity rule
**When** replay cycles occur
**Then** they remain excluded from normal training
**And** the existing saved-model reuse flow remains intact unless an explicit later story changes it.

**Given** the demo-clarity requirement
**When** replay is shown in the dashboard
**Then** the UI explains it as a behavioral inconsistency detected by the fingerprint path
**And** it keeps replay distinct from:
- no-quorum alerts
- SCADA-divergence alerts
