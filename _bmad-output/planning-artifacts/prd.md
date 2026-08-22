---
stepsCompleted:
  - step-01-init
  - step-02-discovery
  - step-02b-vision
  - step-02c-executive-summary
  - step-03-success
  - step-04-journeys
  - step-05-domain
  - step-06-innovation-skipped
  - step-07-project-type
  - step-08-scoping
  - step-09-functional
  - step-10-nonfunctional
  - step-11-polish
inputDocuments:
  - /c:/Users/emili/Desktop/Projets/parallel-truth-fingerprint-prototype/_bmad-output/planning-artifacts/product-brief-parallel-truth-fingerprint-prototype-2026-03-23.md
  - /c:/Users/emili/Desktop/Projets/parallel-truth-fingerprint-prototype/docs/input/Arquitetura Baseada em Fonte de Verdade Paralela para Geração de Fingerprint Físico-Operacional em Sistemas Industriais Legados_DEFINIÇÃO_DO_PROBLEMA.txt
  - /c:/Users/emili/Desktop/Projets/parallel-truth-fingerprint-prototype/docs/input/Arquitetura Baseada em Fonte de Verdade Paralela para Geração de Fingerprint Físico-Operacional em Sistemas Industriais Legados_OBJECTIVOS.txt
  - /c:/Users/emili/Desktop/Projets/parallel-truth-fingerprint-prototype/docs/input/Arquitetura Baseada em Fonte de Verdade Paralela para Geração de Fingerprint Físico-Operacional em Sistemas Industriais Legados_METODOLOGIA_DE_PESQUISA.txt
  - /c:/Users/emili/Desktop/Projets/parallel-truth-fingerprint-prototype/docs/input/Arquitetura Baseada em Fonte de Verdade Paralela para Geração de Fingerprint Físico-Operacional em Sistemas Industriais Legados_FUNDAMENTACAO_TEORICA.txt
  - /c:/Users/emili/Desktop/Projets/parallel-truth-fingerprint-prototype/docs/input/Arquitetura Baseada em Fonte de Verdade Paralela para Geração de Fingerprint Físico-Operacional em Sistemas Industriais Legados_ARQUITETURA_PROPOSTA.txt
  - /c:/Users/emili/Desktop/Projets/parallel-truth-fingerprint-prototype/docs/input/Arquitetura Baseada em Fonte de Verdade Paralela para Geração de Fingerprint Físico-Operacional em Sistemas Industriais Legados_PLANO_DE_AVALIACAO_E_REFERENCE.txt
workflowType: 'prd'
status: 'controlling-consolidated-planning'
updatedAt: '2026-08-22'
supersedesNormativeOverlays:
  - _bmad-output/planning-artifacts/prd-update-2026-05-21.md
  - _bmad-output/planning-artifacts/prd-update-2026-08-15.md
approvedChangeProposal: _bmad-output/planning-artifacts/sprint-change-proposal-2026-08-22.md
documentCounts:
  productBriefs: 1
  research: 0
  brainstorming: 0
  projectDocs: 4
classification:
  projectType: iot_embedded
  domain: process_control
  complexity: medium
  projectContext: brownfield
---

# Product Requirements Document - parallel-truth-fingerprint-prototype

**Author:** Emilio
**Date:** 2026-03-23

## Controlling Reading Rule

This consolidated `prd.md` is the sole current normative PRD. The original
narrative and base-requirement sections remain for brownfield context, but the
Controlling Consolidated Requirements Inventory at the end of this document
governs every conflict. Dated PRD updates are historical traceability only and
are not additional normative layers. This PRD is planning evidence and does not
authorize implementation, dataset acquisition, training, syscall capture,
experiment execution, feature activation, deployment, or publication.

## Executive Summary

This PRD defines a simplified academic prototype for validating an industrial cybersecurity architecture based on a parallel source of truth for physical-operational fingerprint generation in legacy industrial systems. The prototype is limited to local execution and is intended for implementation planning, demonstration, and academic evaluation.

The prototype addresses a specific integrity problem: digital values exposed through PLC/SCADA paths may remain plausible even when they no longer faithfully represent the real process state. To preserve the approved research logic, the prototype implements an independent validation path based on decentralized edge observation, Byzantine-style trust evaluation, comparison between the consensused edge state and the SCADA state, and LSTM-based fingerprint generation for temporal anomaly detection.

The system under observation is one compressor with three simulated sensors: temperature, pressure, and RPM. Three simulated edges are used, with each edge associated with exactly one local sensor. Each edge performs pre-PLC physical acquisition semantics (conceptual HART / 4-20 mA reference) semantics (conceptual HART / 4–20 mA reference), publishes its observation via MQTT, consumes observations from the other edges, reconstructs a replicated shared view of the compressor state, and participates in a Byzantine-style validation round. Suspicious edge contributions are excluded within the active round, and the round produces a consolidated valid compressor state.

This consolidated state is the prototype's physical-side reference. It is compared sensor by sensor against a fake OPC UA SCADA state representing the logical supervisory view. When the configured tolerance is exceeded for temperature, pressure, or RPM, the system generates a specific SCADA divergence alert. Valid consolidated data is persisted to local MinIO storage. Normal-only stored data is then used by the LSTM service to train a reusable fingerprint model and to produce inference outputs consisting of anomaly score and normal/anomalous classification. Replay or other temporal inconsistency must be detectable through this fingerprint behavior.

This PRD does not redefine the architecture. It structures the approved prototype scope, preserves the existing RF/RNF requirements without modification, and translates existing success criteria into implementation-oriented acceptance criteria suitable for planning.

Implementation note: in the prototype, the real consensus implementation is CometBFT plus a Go ABCI application. BBD/FABA remains conceptual and theoretical inspiration from the approved PEP, not the literal runtime library used by the codebase. Fake OPC UA SCADA, MinIO persistence, and the local LSTM path remain real prototype targets, while the surrounding SCADA and cloud environments remain simulated locally.

### What Makes This Special

The defining architectural property of the prototype is that it does not treat the logical SCADA path as the primary source of trust. Instead, the trusted reference is the consensused state reconstructed from independent edge-side acquisition paths and validated through a Byzantine-style round.

The prototype also keeps two validation paths distinct. The first is an integrity comparison between the consensused state and the OPC UA SCADA state, producing a SCADA divergence alert when tolerance is exceeded. The second is a behavioral validation path in which an LSTM model learns normal temporal behavior from valid stored data and produces anomaly outputs capable of revealing replay-oriented or temporally inconsistent scenarios.

Its value for implementation planning is not additional feature breadth, but faithful preservation of the approved research sequence under reduced prototype complexity: simulated infrastructure, local execution, clear logs, and a final lightweight SCADA-inspired demo UI supported by logs, simple charts, and metrics, without unnecessary production-grade expansion.

## Reality Boundary

- Real in the prototype: MQTT messaging, CometBFT plus Go ABCI consensus, SCADA comparison logic, fake OPC UA service, MinIO persistence, local LSTM training and inference, observability, alerts, and the final lightweight demo UI when implemented.
- Simulated or mock in the prototype: physical sensors, compressor/process behavior, physical edge hardware, the SCADA environment itself, and the cloud environment represented locally.
- Conceptual only from the PEP/dissertation side unless explicitly re-approved for implementation: BBD/FABA as the theoretical consensus reference, Orion/Kafka-style cloud context-broker infrastructure, real cloud deployment, and a production-grade industrial HMI scope.

## Project Classification

- Project Type: IoT / Embedded Prototype
- Domain: Industrial Process Control
- Complexity: Medium
- Project Context: Brownfield planning based on existing approved research artifacts and a completed Product Brief

## Success Criteria

### User Success

For the primary user, success means the researcher can run the prototype locally, observe each stage of the architecture, and demonstrate the intended research logic without needing production-grade infrastructure or a complex interface.

User success is achieved when the prototype:
- can be started and executed in a local environment
- exposes the current compressor state, consensus output, SCADA comparison results, persistence behavior, and LSTM outputs through clear logs, observable system state, and the final lightweight demo UI when that last layer is implemented
- supports demonstration of both normal operation and anomalous scenarios, including suspicious edge participation, SCADA divergence, and replay-oriented temporal inconsistency
- makes it possible to explain how each stage of the execution flow maps back to the approved architecture

For academic evaluators, success means the prototype is understandable, traceable, and structurally faithful to the approved research scope. For technical readers or future implementers, success means the prototype is sufficiently modular and explicit to support inspection and future extension.

### Business Success

For this PRD, business success is replaced by prototype validation success. The prototype is considered successful when it demonstrates the four core pillars of the approved research architecture within the intentionally simplified local environment:

- decentralized edge operation
- Byzantine-style validation with exclusion of suspicious edge contributions in the active round
- comparison between consensused edge state and SCADA state
- LSTM-based fingerprint generation and anomaly detection

Validation success also requires that the prototype remain simple, demonstrable, and implementation-focused, without introducing unnecessary production-oriented complexity.

### Technical Success

Technical success is achieved when the end-to-end pipeline executes in the intended sequence and preserves the architectural meaning defined by the approved documents.

Technical success requires all of the following:
- simulated sensor generation for one compressor across temperature, pressure, and RPM
- three simulated edges, each associated with one local sensor only
- pre-PLC physical acquisition semantics (conceptual HART / 4-20 mA reference) at the edge layer
- MQTT publication and cross-edge consumption of observations
- replicated shared compressor state across edges
- Byzantine-style trust evaluation and suspicious-edge exclusion during the active round
- generation of a consolidated valid compressor state
- fake OPC UA SCADA exposure of the logical supervisory state
- sensor-by-sensor comparison with configurable tolerance
- SCADA divergence alert generation when tolerance is exceeded
- persistence of valid data only into local MinIO storage
- LSTM training using normal data only
- generation of a reusable fingerprint model
- inference output containing anomaly score and normal/anomalous classification
- replay or temporal inconsistency detection through fingerprint behavior

### Measurable Outcomes

Because this is an academic prototype, the key outcomes are acceptance-based rather than growth-based.

The prototype must demonstrate:
- end-to-end execution from simulated sensor generation to LSTM inference
- exclusion of a suspicious edge during a consensus round
- SCADA divergence alerting when the logical state exceeds configured tolerance relative to the consensused state
- persistence of valid data only into MinIO
- LSTM training using only normal stored data
- generation and reuse of a fingerprint model
- anomaly output for at least one replay-oriented or temporally inconsistent scenario
- reproducible local execution
- clear logs and observable outputs for presentation and evaluation

## Product Scope

### MVP - Minimum Viable Product

For this PRD, the MVP is the minimum academically valid prototype required to demonstrate the approved architecture end to end.

The MVP includes:
- one compressor under observation
- three simulated sensors: temperature, pressure, RPM
- three simulated edges with one local sensor per edge
- pre-PLC physical acquisition semantics (conceptual HART / 4-20 mA reference)
- MQTT-based exchange and replicated edge state
- Byzantine-style validation and suspicious-edge exclusion
- consolidated valid compressor state generation
- fake OPC UA SCADA
- tolerance-based sensor-by-sensor comparison
- SCADA divergence alerting
- MinIO persistence of valid data only
- LSTM training on normal data only
- reusable fingerprint generation
- anomaly score and normal/anomalous classification
- replay-oriented anomaly demonstration
- clear logs and the final lightweight demo UI, plus supporting charts and metrics when needed

### Growth Features (Post-MVP)

Growth features are intentionally limited because this PRD targets a constrained academic prototype rather than a roadmap for product expansion.

Post-MVP extensions may include:
- expansion beyond one compressor while preserving the same architectural logic
- richer attack scenarios beyond the initial replay and SCADA divergence demonstrations
- more complete visualization and evaluation tooling
- more realistic edge-side acquisition behavior while preserving the current architectural sequence

### Vision (Future)

The future direction of this work is continued research-oriented refinement of the same architecture rather than expansion into a production platform.

Future work may include:
- broader multi-equipment scenarios
- richer experimental validation scenarios
- improved inspection and evaluation tooling for academic presentation and analysis
- eventual replacement of simulated acquisition semantics with more realistic edge-side acquisition mechanisms

## User Journeys

### Journey 1: Researcher - Normal Demonstration Path

The researcher starts the local prototype environment to demonstrate the approved architecture in its intended normal operating state. The local services for sensor simulation, edge acquisition, MQTT exchange, fake OPC UA SCADA, MinIO storage, and LSTM processing are launched in sequence.

As execution begins, the researcher observes the generated compressor readings for temperature, pressure, and RPM. Each edge acquires only its associated local sensor using the prototype's pre-PLC physical acquisition semantics, publishes its observation through MQTT, and consumes the observations from the other edges. The researcher verifies through logs and system state outputs that each edge now holds a replicated view of the compressor state.

The prototype then executes the Byzantine-style validation round. The researcher inspects the resulting trust information and the consolidated valid compressor state. That consolidated state is compared against the fake OPC UA SCADA state, and valid data is persisted to MinIO. The LSTM service then uses the stored normal data for training or inference and produces fingerprint-related outputs.

The journey succeeds when the researcher can show the full architectural pipeline end to end, explain the role of each stage, and demonstrate that the system behaves coherently under normal conditions.

### Journey 2: Researcher - Divergence and Suspicious Edge Scenario

The researcher runs a controlled demonstration scenario intended to show that the architecture does not trust every contributor or every logical value by default. During execution, one edge contributes suspicious data or behaves inconsistently within a validation round.

The researcher observes that the Byzantine-style validation logic evaluates trust and excludes the suspicious edge contribution from the active round. The system still produces a consolidated valid compressor state using the remaining acceptable observations. The researcher then introduces or observes a divergence between this consensused physical-side state and the logical SCADA state.

The comparison service evaluates temperature, pressure, and RPM against configured tolerances. When tolerance is exceeded, the system produces a specific SCADA divergence alert. The researcher uses this moment to show that the SCADA comparison path is a direct integrity check and is distinct from behavioral anomaly detection.

This journey succeeds when the prototype visibly excludes the suspicious edge in the round, produces a valid consolidated state, and generates a SCADA divergence alert under the expected condition.

### Journey 3: Researcher - Replay or Temporal Inconsistency Scenario

The researcher prepares or triggers a replay-oriented scenario in which values may remain individually plausible but become inconsistent over time. The prototype executes the same pipeline as before: local acquisition, MQTT sharing, replicated shared state, consensus, SCADA comparison, and valid-data persistence.

Because replay can remain difficult to detect through direct value comparison alone, the researcher focuses on the fingerprint path. The stored normal data is used by the LSTM service to train or load a reusable model of normal compressor behavior. During inference, the model evaluates the incoming sequence and produces an anomaly score and a normal/anomalous classification.

The researcher inspects the resulting anomaly output and explains that the alert emerges from temporal inconsistency rather than from a direct SCADA tolerance violation. This demonstrates the second downstream validation path defined by the approved architecture.

This journey succeeds when the replay-oriented or temporally inconsistent scenario produces anomaly behavior through the fingerprint path and remains clearly distinguishable from the SCADA divergence alert path.

### Journey 4: Academic Evaluator or Technical Reader - Inspection and Validation Path

The academic evaluator or technical reader does not need to operate the prototype as its primary user, but must be able to inspect and understand its structure, outputs, and architectural faithfulness. This journey begins during or after the demonstration, when the evaluator or reader observes the logs, state outputs, alerts, and the final lightweight demo UI if that last layer has been implemented.

The evaluator or reader follows the execution flow from simulated sensor generation to edge acquisition, MQTT replication, consensus, SCADA comparison, persistence, and LSTM output. They verify that the prototype remains simple, local, and academically scoped, and that the simulated layers do not alter the intended architectural meaning.

This journey succeeds when the evaluator or reader can trace requirements and behavior through the visible outputs and confirm that the implementation aligns with the approved scope, requirements, architecture, and prototype success criteria.

### Journey Requirements Summary

These journeys reveal the following capability requirements:

- local startup and execution of all prototype services
- observable logs and system state across the full pipeline
- support for normal demonstration flow
- support for suspicious edge and SCADA divergence scenarios
- support for replay-oriented or temporally inconsistent anomaly scenarios
- visible trust evaluation and suspicious-edge exclusion during consensus
- visible SCADA comparison and alert generation
- visible persistence behavior for valid data only
- visible LSTM training or inference outputs including anomaly score and classification
- reproducible execution that allows academic inspection and technical understanding

## Domain-Specific Requirements

### Compliance & Regulatory

This prototype is not intended as a certified industrial control product and does not claim regulatory compliance. However, it should remain structurally consistent with the types of concerns that exist in industrial process-control environments.

Relevant domain-aligned considerations are:
- preservation of the distinction between physical-side observation and logical supervisory state
- non-intrusive architectural positioning relative to the traditional PLC/SCADA path
- clear separation between simulated infrastructure and the real operational meaning of each architectural layer
- traceable behavior suitable for academic review and future comparison against industrial cybersecurity and OT-security frameworks

Because the prototype is local and academic in scope, formal compliance certification, audit programs, and production regulatory obligations are out of scope.

### Technical Constraints

The main domain-specific technical constraints are:

- the prototype must preserve decentralized behavior across edges rather than collapsing logic into a single trusted node
- consensus must operate as a Byzantine-style trust evaluation round with explicit suspicious-edge exclusion
- the SCADA comparison must remain a comparison between consensused edge state and OPC UA logical state, not a generic anomaly heuristic
- the LSTM path must remain distinct from the SCADA divergence path
- the system must remain simple, local, and demonstrable rather than optimized for production deployment
- execution frequency should stay aligned with the one-minute reference used in the approved materials
- logs and observable outputs must be clear enough to support architectural inspection during academic presentation

### Integration Requirements

The required domain-specific integrations for the prototype are limited and local:

- MQTT broker for cross-edge publication and consumption
- fake OPC UA SCADA service exposing the logical supervisory view
- local MinIO object storage for valid data persistence
- LSTM service consuming stored normal data and producing fingerprint inference outputs

These integrations must preserve the architectural sequence defined in the approved documents and must not introduce unnecessary external system dependencies.

### Risk Mitigations

Key domain-specific risks and the required mitigations are:

- Risk: loss of architectural fidelity through excessive simplification
  Mitigation: preserve the four core pillars and the exact execution order defined in the approved scope and architecture documents

- Risk: conflating SCADA divergence detection with behavioral anomaly detection
  Mitigation: keep the SCADA comparison alert path and the LSTM anomaly path as separate outputs

- Risk: training on contaminated or invalid data
  Mitigation: persist only valid data after consensus and restrict LSTM training to normal data only

- Risk: prototype drift toward production-grade complexity
  Mitigation: keep execution local, maintain simulated infrastructure, and avoid unnecessary expansion beyond the approved prototype scope

- Risk: unclear demonstration outputs
  Mitigation: ensure logs, state outputs, trust results, alerts, and the final lightweight demo UI remain easy to inspect during presentation

## IoT / Embedded Prototype Specific Requirements

### Project-Type Overview

This project is an IoT / embedded-style academic prototype in which the embedded and field-acquisition aspects are represented conceptually rather than through real industrial hardware. The prototype must preserve the architectural behavior of local edge acquisition, decentralized message exchange, consensus, supervisory comparison, persistence, and temporal inference while remaining fully executable in a local development environment.

The project is therefore not a hardware validation effort. It is a software prototype that simulates the operational roles normally performed by field sensors, acquisition interfaces, edge nodes, brokered communication, supervisory state exposure, storage, and downstream anomaly analysis.

The IoT / embedded classification should be interpreted only as an execution-style classification for planning purposes. Architecturally, the prototype remains an industrial / OT-inspired validation architecture centered on physical-versus-logical state comparison, Byzantine-style trust validation at the edge layer, and temporal fingerprint-based anomaly detection.

### Technical Architecture Considerations

The project-type-specific technical considerations are:

- each edge must behave as an independent logical node associated with one local sensor only
- even in a single-machine setup, the system must preserve decentralized behavior conceptually, with each edge maintaining its own local acquisition, MQTT publication and consumption, and consensus execution
- local acquisition behavior must preserve pre-PLC physical acquisition semantics (conceptual HART / 4-20 mA reference), without requiring real analog hardware
- communication between edges must use MQTT and a brokered publish/subscribe model
- each edge must consume the observations of the other edges and reconstruct a shared compressor state, but this shared state must not be trusted by default
- the final valid system state must be the result of Byzantine-style consensus, and only the consensused state is considered valid for downstream processing
- consensus must execute at the edge layer and must support suspicious-edge exclusion within the active round
- the logical supervisory side must be represented through a fake OPC UA SCADA service
- storage must remain local and object-oriented, with MinIO as the target implementation
- the machine-learning stage must remain downstream from consensus, filtering, and valid-data persistence, and must use an LSTM-only path within the current prototype scope

### Hardware Requirements

No real industrial hardware is required for the current prototype.

The hardware-oriented constraints for this PRD are:
- physical sensors are simulated
- edge devices as hardware are simulated
- analog HART / 4–20 mA acquisition hardware is not required
- PLC hardware integration is not required
- cloud infrastructure is not required

### Connectivity Protocol

The required connectivity model for the prototype is:

- MQTT for decentralized publication and consumption between edges
- OPC UA for the fake SCADA logical-state interface
- local object storage access for persistence of valid data
- local service-to-service interaction sufficient to support the execution flow in one machine or local environment

The protocol scope must remain minimal and aligned with the approved prototype architecture.

### Power Profile

Power constraints are not applicable to the current prototype because the system is executed locally with simulated components rather than deployed on constrained embedded hardware.

### Security Model

The security model for this prototype is architectural rather than production-operational.

The prototype must demonstrate:
- distrust of the logical path as the sole source of truth
- distrust of all edge contributions until validated through Byzantine-style consensus
- exclusion of suspicious edge participation within the active round
- separation between SCADA divergence alerts and fingerprint-based anomaly alerts
- restriction of LSTM training input to validated normal data only after consensus, filtering, and persistence of valid data

Advanced hardening, production-grade access control, and full OT-security controls are explicitly out of scope.

### Update Mechanism

No OTA or embedded-device update mechanism is required for this prototype.

Implementation should assume a local development and demonstration workflow in which services are started, configured, and rerun directly by the researcher.

### Implementation Considerations

Implementation should remain consistent with the current prototype constraints:

- Python is the preferred implementation language
- execution must remain local
- local execution must not be interpreted as centralized architecture
- collection cadence should remain aligned with the one-minute reference
- logs must remain clear and presentation-friendly
- modular service boundaries should remain visible
- the final lightweight SCADA-inspired demo UI, plus logs and simple charts, may be used only to support explanation, not as a production interface
- no raw or potentially contaminated data should reach the LSTM training pipeline

## Project Scoping & Phased Development

### MVP Strategy & Philosophy

**MVP Approach:**  
The MVP is the minimum academically valid prototype required to demonstrate the approved architecture end to end. The goal is not market validation, monetization, or platform growth. The goal is to produce a simple, demonstrable, locally executable proof of concept that preserves the architectural meaning of the research proposal.

**Resource Requirements:**  
The prototype should be implementable as a modular Python-based local system composed of:
- sensor simulation
- three logical edge services
- MQTT broker integration
- fake OPC UA SCADA service
- local MinIO storage
- LSTM training/inference service
- logs and the final lightweight demo UI for demonstration support

### MVP Feature Set (Phase 1)

**Core User Journeys Supported:**
- researcher normal demonstration path
- researcher suspicious-edge and SCADA divergence scenario
- researcher replay or temporal inconsistency scenario
- academic evaluator or technical reader inspection path

**Must-Have Capabilities:**
- simulation of one compressor with temperature, pressure, and RPM sensors
- three logically independent edges, each tied to one local sensor
- pre-PLC physical acquisition semantics (conceptual HART / 4-20 mA reference)
- MQTT-based observation exchange between edges
- shared compressor-state reconstruction across edges without trusting that state by default
- Byzantine-style trust evaluation and suspicious-edge exclusion within the active round
- generation of a consensused valid compressor state, which is the only state considered valid for downstream steps
- use of only the consensused valid state for SCADA comparison, persistence, and LSTM processing
- fake OPC UA SCADA logical-state exposure
- sensor-by-sensor comparison between consensused state and SCADA state using configurable tolerance
- SCADA divergence alert generation
- persistence of valid data only into local MinIO storage
- LSTM training using validated normal data only
- reusable fingerprint model generation
- anomaly score and normal/anomalous classification
- replay-oriented or temporally inconsistent anomaly demonstration
- clear logs and the final lightweight demo UI, plus supporting charts and metrics when needed

### Post-MVP Features

**Phase 2 (Post-MVP):**
- expansion beyond one compressor while preserving the same decentralized logic
- richer attack scenarios beyond the initial replay and SCADA divergence demonstrations
- more complete evaluation and inspection tooling
- more realistic edge-side acquisition behavior while preserving the approved architecture

**Phase 3 (Expansion):**
- broader multi-equipment experimental scenarios
- richer academic validation scenarios
- replacement of simulated acquisition semantics with more realistic acquisition mechanisms where appropriate
- improved analysis and presentation tooling for extended research use

### Risk Mitigation Strategy

**Technical Risks:**  
The main technical risk is loss of architectural fidelity through oversimplification. Mitigation: preserve the exact execution order and trust model defined in the approved scope, requirements, and architecture documents.

**Market Risks:**  
Not applicable as a primary scope driver for this PRD. In this academic context, the equivalent risk is failure to demonstrate the research contribution clearly. Mitigation: ensure all key outputs are observable and that the prototype distinguishes clearly between SCADA divergence alerts and LSTM anomaly alerts.

**Resource Risks:**  
The main resource risk is overexpansion of scope beyond what is required for a local academic prototype. Mitigation: keep the implementation limited to one compressor, three sensors, three edges, local services, and the existing RF/RNF set without adding production-oriented complexity.

## Historical Base Functional Requirements

### Sensor Simulation & Edge Acquisition

- FR1: The system can simulate 3 sensors of one compressor.
- FR2: Each edge can collect only its local sensor.

### Edge Communication & Shared State

- FR3: Each edge can publish data to MQTT.
- FR4: Each edge can consume data from the other edges.
- FR5: The system can maintain a shared view of the compressor.

### Distributed Validation & Trust

- FR6: The system can execute Byzantine consensus between the edges.
- FR7: The consensus can produce trust ranking and this must be included in the package that goes to the bucket.
- FR8: The system can exclude a suspicious edge from the round.
- FR9: The system can expose the participating edges in each consensus round.
- FR10: The system can expose the excluded edges in each consensus round and the reason for exclusion.
- FR11: The system can expose the resulting trust ranking for all edges in the round.
- FR12: The system can explicitly indicate when a valid consensus cannot be achieved.
- FR13: The system can generate structured logs describing each consensus round.
- FR14: The system can generate alerts when consensus fails.

### SCADA Comparison & Integrity Alerting

- FR15: The system can expose a fake SCADA in OPC UA.
- FR16: The system can execute sensor-by-sensor comparison with tolerance.
- FR17: The system can generate an alert when SCADA diverges from the consensused physical state.

### Valid Data Persistence

- FR18: The system can persist valid data in local storage (bucket).

### Fingerprint Training & Inference

- FR19: The system can train an LSTM using normal data.
- FR20: The system can generate an equipment fingerprint.
- FR21: The system can generate anomaly score and normal/anomalous class.
- FR22: The system can save the model/fingerprint.

### Temporal Anomaly Detection

- FR23: The system can detect a replay scenario.

## Historical Base Non-Functional Requirements

### Performance

- NFR1: The prototype must execute locally with a collection cadence aligned with the one-minute reference defined in the approved materials.
- NFR2: The execution flow must remain suitable for live demonstration and academic inspection, without requiring high-frequency or real-time optimization.

### Security

- NFR3: The prototype must preserve validation-before-trust by ensuring that shared edge state is not treated as valid until Byzantine-style consensus has completed.
- NFR4: Only consensused valid data may be used for downstream processing steps such as SCADA comparison, persistence, and LSTM training or inference.
- NFR5: The prototype must keep SCADA divergence alerting and fingerprint-based anomaly alerting as distinct outputs.

### Reliability

- NFR6: The prototype must run locally.
- NFR7: The prototype must explicitly indicate when valid consensus cannot be achieved.
- NFR8: The prototype must produce clear, structured logs that allow each pipeline stage and each consensus round to be inspected during demonstration and evaluation.
- NFR9: The structured logs must provide full traceability of each consensus round, including identification of participating edges, excluded edges, and the reasons for exclusion.
- NFR10: The prototype execution must be reproducible for academic presentation and validation.

### Integration

- NFR11: The prototype must integrate locally with MQTT for edge communication, HART-based collection semantics for sensor acquisition, OPC UA for fake SCADA exposure, MinIO for object storage, and an LSTM service for fingerprint training and inference.
- NFR12: The integration model must remain simple and local, without requiring real cloud infrastructure or external industrial systems.

### Maintainability & Modularity

- NFR13: The prototype must prioritize Python.
- NFR14: The prototype must be simple and demonstrable.
- NFR15: The prototype must have clear logs for presentation.
- NFR16: The prototype must be modular.
- NFR17: The prototype must permit future replacement of the local storage by a real cloud storage solution.

## Controlling Consolidated Requirements Inventory

This inventory is self-contained and authoritative for all 93 functional
requirements and 52 non-functional requirements. `RETAINED`, `AMENDED`, and
`SUPERSEDED` preserve identifier history while naming the current controlling
behavior. No requirement may be implemented from historical prose in
isolation from its named controller.

### Functional Requirements

FR1: **AMENDED -> FR73-FR76.** Preserve simulation of temperature, pressure,
and RPM for one compressor as internal engineering-unit physics while custom
edge evidence follows the cited current-domain instrument profile.

FR2: **AMENDED -> FR73-FR76.** Preserve one assigned physical sensor per edge,
with the edge receiving primary raw-current evidence and its profile-owned
representations.

FR3: **RETAINED/AMENDED -> FR73, FR91; NFR39-NFR50.** Each edge publishes its
versioned observation through the local MQTT boundary.

FR4: **RETAINED/AMENDED -> FR73, FR91; NFR39-NFR50.** Each edge consumes peer
observations without bypassing version, quality, provenance, or trust rules.

FR5: **RETAINED/AMENDED -> FR73, FR91; NFR39-NFR50.** Each edge maintains its
own non-trusted local replicated compressor view without shared mutable state
collapsing edge independence.

FR6: **RETAINED/AMENDED -> FR91.** The system executes the existing real
CometBFT plus Go ABCI Byzantine-style validation path using the versioned v2
physical contract when v2 is active.

FR7: **RETAINED/AMENDED -> FR91; NFR49-NFR50.** A successful consensus result
exposes and persists its trust ranking as reconstructible evidence.

FR8: **RETAINED/AMENDED -> FR91.** Consensus can exclude a suspicious edge
contribution under the declared current-domain comparison basis.

FR9: **RETAINED/AMENDED -> FR91.** Each consensus result identifies its
participating edges and correlation identities.

FR10: **RETAINED/AMENDED -> FR91.** Each consensus result identifies excluded
edges and the evidence-based reason for each exclusion.

FR11: **RETAINED/AMENDED -> FR91; NFR50.** Each consensus result exposes the
complete ranking and evidence references for every edge in the round.

FR12: **RETAINED/AMENDED -> FR91; NFR47-NFR48.** Failure to reach valid
consensus remains an explicit, fail-closed outcome.

FR13: **RETAINED/AMENDED -> FR91; NFR50.** The system emits structured,
traceable logs for each consensus round.

FR14: **RETAINED/AMENDED -> FR91, FR93.** Consensus failure remains a distinct
state and, if the optional dashboard is implemented, a distinct presentation.

FR15: **SUPERSEDED -> FR90.** Do not implement a fake or consensus-projected
SCADA source as v2 evidence; use the independent pre-consensus OPC UA path.

FR16: **SUPERSEDED -> FR90-FR91.** Do not retain an anonymous circular
sensor-tolerance comparison; use eligible OPC UA evidence and the declared
comparison basis.

FR17: **SUPERSEDED -> FR90, FR93.** SCADA divergence is replaced by explicit
independent-OPC integrity and comparison outcomes, optionally presented without
control authority.

FR18: **AMENDED -> FR85, FR87, FR92; NFR40, NFR49.** Persist immutable,
role-separated eligible evidence rather than one ambiguous valid-data object.

FR19: **SUPERSEDED -> FR77-FR89.** Do not implement an LSTM-only fingerprint
premise; compare declared physical and syscall candidates under isolated truth.

FR20: **SUPERSEDED -> FR78, FR81, FR87.** A fingerprint is an immutable,
track-specific detector bundle and result, not an assumed single model.

FR21: **SUPERSEDED -> FR87-FR89.** Detector scores, decisions, and optional
fusion follow frozen track-specific calibration and synchronized evidence.

FR22: **SUPERSEDED -> FR87.** Save and load complete immutable detector bundles
without fitting or threshold recalculation.

FR23: **SUPERSEDED -> FR75, FR77-FR89.** Replay/freeze is a preregistered,
truth-isolated evaluation condition rather than proof by one legacy model.

FR24: **AMENDED -> FR82-FR84.** External benchmark work uses separate,
dataset-native ADFA-LD, LID-DS 2021, and HAI 23.05 roles rather than one generic
benchmark adapter or result claim.

FR25: **SUPERSEDED -> FR86; NFR41.** A universal stratified 80/20 sample split
is prohibited; complete official groups or independent runs split before
window formation.

FR26: **RETAINED/AMENDED -> FR87-FR88; NFR40.** Persist complete architecture,
hyperparameter, execution, dependency, data, calibration, and runtime identity
for every measured detector run.

FR27: **SUPERSEDED -> FR77-FR88.** Evaluation uses labels only after freeze and
reports protocol-appropriate anomaly, temporal, event, uncertainty, and quality
outcomes rather than one universal supervised-classification metric set.

FR28: **AMENDED -> FR87, FR92; NFR49.** Persist immutable role- and
version-separated run, bundle, metric, and evidence records; a mutable shared
history prefix is not scientific identity.

FR29: **SUPERSEDED -> FR87, FR89.** External ADFA-LD, LID-DS, or HAI models
never become compressor detectors; only compatible custom bundles may run in
their own modality and only synchronized custom scores are fusion-eligible.

FR30: **RETAINED.** Capture a v1 golden baseline across runtime, contracts,
artifacts, dashboard state, and experimental fingerprint behavior.

FR31: **RETAINED.** Classify every dataset and run by controlled provenance
tier and result role without overriding dataset-native scope.

FR32: **RETAINED.** Prevent fixtures or published statistics from being
represented as locally measured execution results.

FR33: **SUPERSEDED -> FR73-FR74.** `SignalObservation.v2` and profile-owned
derivation replace one universal `ProcessSample` evidence contract; OPC UA has
its separate FR90 contract.

FR34: **AMENDED -> FR75-FR77.** Declare controlled experiments through a
versioned `ExperimentSpec` whose schedules, numbers, interventions, and truth
follow provenance and access controls.

FR35: **AMENDED -> FR74-FR75, FR85; NFR46.** Accelerated simulator sessions may
support declared physical-only or test evidence, but final fusion evidence
requires synchronized physical observations and authentic syscalls from the
same correlated runs.

FR36: **AMENDED -> FR77, FR86; NFR41.** Generate truth independently, keep it
structurally absent from detector contracts, and join it only after freeze.

FR37: **AMENDED -> FR73-FR75, FR78.** Feature context, units, derivatives, and
commanded state are profile-owned and evidence-referenced, while intervention
truth remains protected.

FR38: **AMENDED -> FR75-FR77, FR88; NFR51.** Execute a preregistered scenario
matrix and preserve valid, invalid, aborted, unfavorable, and recovery runs.

FR39: **AMENDED -> FR86; NFR41.** Split every official group or custom run
before windowing and prevent windows crossing trace, file, boot, session,
process, scenario, gap, schema, or split boundaries.

FR40: **AMENDED -> FR85; NFR40, NFR49-NFR50.** Publish immutable verified
artifacts first and atomically publish the complete manifest last.

FR41: **AMENDED -> FR85-FR86; NFR40-NFR41, NFR45-NFR46, NFR49, NFR51.** Close
`DATASET_QUALIFIED` only after synchronized-stream, leakage, capture-quality,
correlation, durability, completeness, and reporting checks pass.

FR42: **AMENDED -> FR90; NFR42.** Publish a pre-consensus plant/transmitter
snapshot through OPC UA without granting analytics actuator authority.

FR43: **AMENDED -> FR90.** Read OPC UA only through a distinct real `opc.tcp`
client; internal server-object access is not eligible v2 evidence.

FR44: **AMENDED -> FR90; NFR46, NFR50.** Preserve OPC UA values, status,
timestamps, schema, producer/revision, and correlation for reconstruction.

FR45: **AMENDED -> FR90; NFR47.** Reject incomplete, stale, mixed, invalid,
unavailable, or mis-correlated OPC UA observations explicitly.

FR46: **AMENDED -> FR90, FR92; NFR50.** Consume only eligible OPC UA
observations and preserve every comparison and fail-closed diagnostic.

FR47: **AMENDED -> FR90; NFR50.** Prove OPC and consensus causal source
independence through a reconstructible branch-isolation round-trip test.

FR48: **AMENDED -> FR90; NFR48, NFR52.** Activate independent OPC mode only
through explicit versioned authorization and never silently fall back to a
consensus projection.

FR49: **AMENDED -> FR86; NFR41, NFR43-NFR44.** Fit preprocessing on eligible
normal training evidence, select on declared validation evidence, and calibrate
independently under the same candidate budget.

FR50: **AMENDED -> FR87; NFR44.** Freeze the threshold before test and bind its
origin and derivation to the immutable detector bundle.

FR51: **AMENDED -> FR87; NFR48.** Reject detector candidates when any governing
dataset, schema, preprocessing, calibration, bundle, dependency, or runtime
identity is stale or incompatible.

FR52: **AMENDED -> FR88; NFR43, NFR51.** Report only applicable
scenario-, severity-, sensor-, regime-, repetition-, temporal-, and
quality-aware metrics under fair budgets, retaining dispersion and limitations.

FR53: **AMENDED -> FR87; NFR48, NFR52.** Promotion and rollback select an
explicit immutable compatible bundle and require separate activity
authorization; planning approval cannot promote a model.

FR54: **AMENDED -> FR87; NFR47-NFR48.** Runtime shadow inference loads an exact
bundle, never fits, recalibrates, or guesses a latest artifact, and fails closed
on absence or incompatibility.

FR55: **SUPERSEDED -> FR84; NFR40.** Do not acquire HAI 20.07 for the new plan;
pin and verify HAI 23.05 instead.

FR56: **SUPERSEDED -> FR84, FR86; NFR47.** HAI 23.05 native roles and chronology
replace HAI 20.07 processing requirements.

FR57: **SUPERSEDED -> FR84, FR87-FR88.** HAI 23.05 receives its own immutable
preprocessing, detector, calibration, and evaluation path.

FR58: **SUPERSEDED -> FR84, FR92; NFR38.** Report HAI 23.05 only as external
native physical/SCADA evidence, never compressor validation.

FR59: **AMENDED -> FR83, FR92; NFR51.** Only qualified official LID evidence may
support a locally measured LID result; fixtures and published references remain
separate roles.

FR60: **AMENDED -> FR83; NFR40, NFR50.** Qualify the declared official LID-DS
2021 source, version, layout, citation, license scope, file inventory, sizes,
and hashes; no subset is mandatory until separately authorized.

FR61: **AMENDED -> FR83; NFR47.** Preserve the official LID schema and grouping,
reject ambiguous or empty layouts, and never substitute a fixture; no scenario
is a default requirement.

FR62: **AMENDED -> FR83, FR86; NFR41.** Split LID by official roles and complete
scenario/recording/trace/session groups before vocabulary fitting or windows.

FR63: **AMENDED -> FR83, FR86, FR88; NFR43-NFR44, NFR51.** Execute only the LID
scope, run count, stopping rules, and candidate budget declared by a later
authorized protocol and report every outcome and limitation.

FR64: **AMENDED -> FR83, FR86, FR92; NFR51.** Keep author-published LID metrics
reference-only and outside fitting, calibration, selection, and local measured
result calculations.

FR65: **AMENDED -> FR88, FR92; NFR40, NFR50.** Use a common provenance-rich
evaluation envelope without erasing modality- or dataset-specific semantics.

FR66: **AMENDED -> FR92; NFR38.** Produce separate dataset and modality result
tables plus a capability/limitation matrix; only the paired custom ablation may
compare physical, syscall, and fusion outcomes on the same runs.

FR67: **AMENDED -> FR92; NFR50-NFR51.** Link each academic claim through
immutable source, split, bundle, threshold, run, metric, limitation, and
scientific-status evidence.

FR68: **AMENDED -> FR92-FR93; NFR50, NFR52.** An optional dashboard may display
only frozen custom detector evidence and cannot create, recompute, promote, or
alter scientific artifacts.

FR69: **AMENDED -> FR92-FR93; NFR38, NFR51.** Optional presentation keeps HAI,
ADFA-LD, and LID native scope, evidence role, result role, version, run,
provenance, and limitations distinct.

FR70: **AMENDED -> FR93; NFR38, NFR42.** Optional presentation keeps consensus,
OPC, SCADA divergence, replay/freeze, physical, syscall, and fusion states
distinct and grants none of them control authority.

FR71: **AMENDED -> FR75, FR87, FR93; NFR52.** An optional dashboard may replay
or present only an already authorized preregistered frozen result; it cannot
generate, fit, calibrate, promote, fuse, or rewrite evidence.

FR72: The system represents exactly two detection modalities: physical
instrumentation and Linux host syscalls. It identifies 4-20 mA as a physical
representation and autoencoders as models in contracts, documentation,
reports, and any optional UI.

FR73: `SignalObservation.v2` preserves raw current in mA, current quality and
diagnostics, instrument/profile identity, source and observation timestamps,
sequence/correlation identity, deterministic normalized span, derived
engineering value/unit, schema version, and parameter-evidence references;
quality is evaluated before optional clipping or imputation.

FR74: The process model may calculate temperature, pressure, and RPM in
engineering units, but an edge receives primary evidence through its selected
transmitter profile. Exactly one profile-owned conversion derives normalized
span and engineering value from current; RPM remains 4-20 mA while supported
by the selected cited shaft-speed profile.

FR75: A versioned `ExperimentSpec` declares phases, profile, run/seed,
schedule, interventions, recovery, stopping rules, and evidence references.
The requested 25%-75% variation is `speed_reference_pct` or
`capacity_reference_pct` classified as `preregistered_factor`; it does not
imply power, ramp, dwell, repetition, or safety limits.

FR76: Every executable v2 numeric parameter has a stable ID and exactly one of
`direct`, `derived`, `measured`, `preregistered_factor`, or `mock`. Its record
contains value, unit, class-specific authority, exact source/decision/
calibration/mock-admission locator, derivation and input IDs where applicable,
selected profile, experiment scope, approval identity, uncertainty/limitation,
authentic-reproduction feasibility, exact prototype component, bounded research
question, dataset/modality track, affected final-package element, and explicit
transferability rationale. Domain claims fail closed on missing, inapplicable,
or non-transferable official authority; preregistered factors use the frozen
decision as value authority; mocks additionally resolve an immutable approved
`MockAdmission.v1`. Anonymous legacy values run only in labelled
legacy-reproduction mode.

FR77: `ScenarioTruth.v1`, attack labels, scenario names, interventions, future
intervals, and evaluation-only metadata remain under a separate access
boundary, absent from detector-facing training and inference contracts, and
join frozen evidence only after the declared truth unlock.

FR78: The physical track compares LSTM-AE, GRU-AE, and declared simpler or
classical baselines fitted only on qualified normal training evidence under the
same current-domain schema, complete-run partitions, budget, repetitions, and
metrics. The current mixed-scale autoencoder is `LEGACY_BASELINE`, not the
final detector or a dataset, and commanded 25%-75% transitions remain distinct
from declared anomalies.

FR79: The custom syscall track runs an allowlisted controlled Linux edge
workload and captures the authentic kernel calls it actually emits through a
qualified Sysdig/eBPF or equivalent collector. Every workload behavior the
approved prototype can reproduce executes authentically. Only a specifically
unavailable behavior may use an approved `MockAdmission.v1`; convenience,
cost, timing, or an unfavorable result is insufficient. Syscalls are never
fabricated, renumbered, modified, or substituted.

FR80: `SyscallEventBatch.v1` preserves run, edge, boot,
container/process/session, categorical syscall name/direction,
sequence/timestamps, kernel/ABI and collector identities,
loss/duplicate/gap/queue evidence, and raw-segment hashes without labels or
scenario truth. Fixture replay is test-only and excluded from formal custom
evaluation.

FR81: The syscall anomaly track treats calls categorically and compares
embedding-plus-LSTM, embedding-plus-GRU, and a transparent n-gram/STIDE-style
baseline fitted on qualified normal evidence under the same group-safe
protocol. Numeric syscall IDs are not continuous quantities and are not
optimized with reconstruction MSE solely because they are numbers.

FR82: ADFA-LD remains an offline external syscall benchmark with official
roles, trace identity, six attack families, source/archive hashes, known count
discrepancies, categorical semantics, and labels confined to evaluation truth;
the system neither fabricates timestamps nor executes dataset identifiers.

FR83: A version-specific LID-DS 2021 adapter preserves official
training/validation/test and scenario/recording boundaries plus the published
syscall schema. LID may inform custom capture design, but its example durations,
collector settings, and metrics remain cited references, not project constants.

FR84: The system pins and verifies HAI 23.05, preserves native tags, units,
chronology, official file roles, and separate labels, and uses a
version-specific physical/SCADA adapter. Its preprocessing, detector,
calibration, and evaluation remain separate; HAI is neither mass-converted to
mA nor presented as compressor data.

FR85: `PTFP-Custom-v1` contains synchronized physical observations and
captured Linux edge syscalls from the same experiment runs, immutable stream
manifests, clock/correlation evidence, modality quality, profile/config
identities, and separately protected truth. Custom rows are never inserted
into or represented as HAI, ADFA-LD, or LID-DS data.

FR86: Complete official groups or independent custom runs split before
windowing. Preprocessing/vocabulary fitting uses training only;
selection/thresholding uses declared validation/calibration only; and locked
test evidence remains unavailable until model, schema, preprocessing,
threshold, metrics, and policy are frozen.

FR87: Every evaluated or deployed detector bundle immutably binds weights and
architecture, feature order/schema or vocabulary, preprocessing,
training/calibration dataset and split hashes, frozen threshold and derivation,
dependency/runtime identity, and bundle hash. Load and inference never call
`fit` or recalculate a threshold.

FR88: Each track reports all applicable point/window and event/range outcomes,
including PR-AUC, precision, recall, F1, false-positive behavior, false events
per operating hour, time to detection, suitable confusion data, threshold
sensitivity, resource cost, modality quality/availability, and repeated-run
dispersion or uncertainty. Unfavorable and aborted planned runs remain visible.

FR89: Late fusion uses only frozen calibrated physical and syscall scores from
aligned windows of the same held-out `PTFP-Custom-v1` runs under a simple
preregistered policy before truth unlock. External ADFA/LID syscall records are
never joined with HAI physical rows to fabricate fusion.

FR90: The OPC UA server receives a pre-consensus plant/transmitter snapshot and
a distinct client reads it through `opc.tcp`, preserving `DataValue` status,
source/server timestamps, schema, and correlation. Invalid, stale, mixed,
missing, or unavailable evidence fails explicitly with no silent consensus
fallback.

FR91: Consensus v2 declares the instrument profile and comparison basis.
Same-profile redundant observations may compare in current domain;
cross-profile or cross-sensor aggregation uses documented dimensionless,
uncertainty-aware residuals. Python and Go produce deterministic identical
results from shared golden fixtures.

FR92: The final package contains separate ADFA-LD, LID-DS 2021, HAI 23.05, and
per-modality `PTFP-Custom-v1` tables, then a paired custom-only
physical/syscall/fusion ablation and capability/limitation matrix. It selects no
global cross-domain champion, and every claim resolves to source, version,
split, bundle, threshold/calibration, run, raw score/metric, and limitation.

FR93: **CONDITIONAL/OPTIONAL.** If Epic 18 is activated, a read-only dashboard
displays raw mA, normalized span, and engineering value as linked physical
representations; physical, syscall, and fusion channels separately; and scope,
provenance, quality, bundle, threshold origin, and limitations. It cannot
import, split, train, calibrate, promote, fuse, relabel, recompute, or rewrite
results and is not an implementation-readiness gate. `legacy_demo` may show
live/current state only with persistent `DEMO - NOT PUBLISHED SCIENTIFIC
EVIDENCE` status. `frozen_evidence` reads one explicitly selected immutable
`G9_PASS` package, never a mutable `latest` identity, exposes no control route,
and rejects mutation requests server-side. Dashboard absence, styling, or
disagreement cannot block or alter scientific Epics 9-17B.

### NonFunctional Requirements

NFR1: **AMENDED -> NFR39, NFR44.** The prototype executes locally, while every
cadence or timing value is sourced, measured, or preregistered for its declared
use rather than inherited from a universal one-minute reference.

NFR2: **RETAINED.** The flow remains suitable for local academic demonstration
and inspection without hard real-time or high-frequency guarantees.

NFR3: **AMENDED -> NFR41-NFR42.** Preserve validation-before-trust; replicated
edge state is not valid until the applicable consensus decision completes.

NFR4: **AMENDED -> NFR41-NFR42; FR85-FR90.** Only explicitly eligible evidence
may progress, while invalid, anomalous, and truth data remain in separate
authorized paths.

NFR5: **AMENDED -> NFR38, NFR42; FR90-FR93.** Consensus, OPC integrity,
physical-detector, syscall-detector, and optional fusion outputs remain
semantically distinct without control authority.

NFR6: **RETAINED.** The prototype runs locally without requiring real cloud or
production industrial infrastructure.

NFR7: **RETAINED.** Every blocking failure is explicit rather than silent
success, empty normality, or fallback.

NFR8: **RETAINED.** Structured logs allow each pipeline stage and experiment
run to be inspected.

NFR9: **RETAINED/AMENDED -> NFR46, NFR50.** Every online cycle is traceable
across physical observation, consensus, OPC, persistence, detectors, and
eligible fusion.

NFR10: **RETAINED/AMENDED -> NFR40.** Academic execution is reproducible from
immutable source, configuration, code, data, split, bundle, and evaluation
identities.

NFR11: **SUPERSEDED -> FR72-FR93; NFR43.** Preserve local integration
boundaries, but do not require an LSTM-only service, fake OPC source, or mixed
modality semantics.

NFR12: **RETAINED.** The architecture stays local and simple, without
unnecessary cloud, Kubernetes, service mesh, API gateway, Kafka, new database,
or production-HMI scope.

NFR13: **RETAINED.** Python remains primary and Go remains confined to the
existing ABCI/consensus boundary.

NFR14: **RETAINED.** The prototype remains simple enough for one researcher to
run, inspect, and explain.

NFR15: **RETAINED/AMENDED -> NFR38, NFR50-NFR51.** Logs, manifests, metrics,
and any optional UI remain presentation-friendly without hiding evidence,
scope, or limitations.

NFR16: **RETAINED.** Modules preserve explicit ownership and trust boundaries.

NFR17: **RETAINED/AMENDED -> NFR49.** Object storage remains replaceable while
formal evidence is persistent, verified, restorable, and semantically stable.

NFR18: **RETAINED/AMENDED -> NFR40.** Repeated runs with the same frozen inputs
remain reproducible within a declared, evidenced numerical tolerance.

NFR19: **RETAINED/AMENDED -> NFR49-NFR50.** Run and evidence history remains
inspectable as flat versioned artifacts independently of any dashboard.

NFR20: **RETAINED/AMENDED -> NFR47.** Active acquisition/control never blocks
on import, batch generation, training, sweeps, evaluation, or reporting.

NFR21: **RETAINED/AMENDED -> NFR40, NFR50-NFR51.** Every source and run records
organization, year, version, subset, counts, schema, citation/location,
license/notice, evidence role, result role, and hashes.

NFR22: **AMENDED -> NFR40, NFR48.** Historical v1 evidence remains replayable
through explicit versions; incompatible v1/v2 artifacts fail closed.

NFR23: **AMENDED -> NFR40, NFR49-NFR50.** Content-addressed bulk artifacts
verify before the complete manifest or pointer is atomically published.

NFR24: **AMENDED -> NFR41.** Zero detector-facing leakage applies across every
official and custom run, trace, file, boot, session, process, gap, group, and
overlapping-window boundary.

NFR25: **AMENDED -> FR84-FR85; NFR47.** HAI and custom evidence processing uses
bounded-memory streaming or sharding and cannot hide partial evidence or
degrade acquisition/control.

NFR26: **RETAINED.** Credentials and private keys remain outside Git,
manifests, evidence, and reports; imported OPC, CSV, archive, and dataset fields
are untrusted input.

NFR27: **AMENDED -> FR90; NFR39, NFR44, NFR47.** Every invalid OPC observation
fails explicitly; no unsupported one-cycle timing limit applies without
parameter evidence or preregistration.

NFR28: **SUPERSEDED -> FR76, FR88; NFR39, NFR44, NFR51.** Fixed initial FPR,
false-event, detection-repetition, or similar targets do not enter v2 without a
complete sourced, measured, or preregistered decision record and full outcome
reporting.

NFR29: **AMENDED -> FR82-FR84; NFR40, NFR52.** Dataset use remains zero-cost
and redistribution-safe, but actionability depends on official source,
version, hashes, license scope, and separate authorization; blocked LID access
does not block ADFA-LD or other independent tracks.

NFR30: **AMENDED -> NFR38; FR84, FR92.** Claims cannot present custom data as a
real plant, HAI as compressor validation, syscall benchmarks as physical
evidence, a subset as a whole corpus, or UI as scientific validation.

NFR31: **AMENDED -> NFR47-NFR48.** Active v1 acquisition/control and historical
replay remain independent of offline import, training, and reporting failures.

NFR32: **AMENDED -> FR93; NFR42, NFR52.** Any optional dashboard has
presentation-only authority and cannot mutate evidence, analytics,
authorization, or actuator commands.

NFR33: **AMENDED -> FR87; NFR48.** Exact immutable detector bundles load
without fitting or recalibration and fail closed on any missing or incompatible
artifact, schema, runtime, or hash.

NFR34: **AMENDED -> FR73-FR74, FR87; NFR39, NFR44.** Batch and live processing
of the same canonical observation produce equivalent conversion, tensor,
score, and explanation within an evidenced or preregistered tolerance.

NFR35: **RETAINED.** Regression and new quality gates pass before a v2 feature
is enabled by default; test success does not authorize implementation or
activation.

NFR36: **AMENDED -> FR88; NFR51.** Every applicable final metric includes
repeated-run dispersion or uncertainty and never reports only a selected best
seed.

NFR37: **AMENDED -> NFR40, NFR48, NFR51.** May/June and v1 anomalies and
results remain immutable historical evidence and are never silently relabelled
as final custom-v2 or official-dataset results.

NFR38: Contracts, logs, reports, and any optional UI use exactly the two
modalities consistently and never call 4-20 mA a modality, an autoencoder a
dataset, HAI compressor data, or controlled custom data real-plant evidence.

NFR39: Formal v2 startup, experiment freeze, and final evidence admission
reject every executable numeric parameter whose complete FR76 record or
class-specific authority cannot be resolved. `direct` uses applicable official
authority; `derived` uses validated inputs and deterministic dimensional
derivation; `measured` uses preserved calibration/pilot evidence;
`preregistered_factor` uses a pre-test frozen decision plus separately
documented feasibility constraints; and `mock` uses an approved capability-gap
admission plus official support for every asserted domain behavior and number.
No class is silently promoted into another.

NFR40: Formal results reconstruct from immutable code, dependency, container,
source, dataset, profile, configuration, split, schema, bundle, score,
truth-unlock, fusion-policy, and evaluation-code identities.

NFR41: No detector-facing artifact contains truth, attack labels, future
values, unauthorized partitions, or windows crossing run, trace, scenario,
file, boot, session, process, gap, or official dataset boundaries.

NFR42: Control and experiment scheduling remain independent from security
analytics. Detector, dashboard, storage, MQTT, OPC UA, capture, and evaluator
failure can never create or alter actuator/compressor commands.

NFR43: LSTM, GRU, and baseline comparisons within one track use the same
eligible partitions, schema, tuning access, declared budget, repetitions, and
primary metrics. Model superiority is measured, never presumed.

NFR44: Thresholds, windows, duration, repetitions, ramp/dwell, queue capacity,
capture-loss policy, fusion weights, and performance targets are selected by
applicable direct sources, preserved measurement, or preregistration with
sensitivity analysis; no publication supplies universal values.

NFR45: Custom syscall evidence exposes workload attribution, collector/kernel
identity, gaps, duplicates, drops, queue depth, storage lag, and measured
overhead. Affected windows follow the preregistered flag/exclusion/abort policy
and are never silently normal.

NFR46: Every custom stream preserves source/observation time, ordered sequence,
run/edge/boot/session identity, and declared clock/correlation uncertainty
sufficient to prove a physical-syscall join; unresolved or mixed identities
prevent fusion.

NFR47: Acquisition/control stays available when storage or analytics degrades.
High-volume syscalls use bounded queues and append-only segments, and missing,
partial, delayed, or aborted evidence is explicit.

NFR48: v1 evidence remains replayable while v2 contracts, consensus state,
storage namespaces, and bundles are explicitly versioned. Incompatible model,
schema, runtime, or hash identities fail closed.

NFR49: Formal evidence uses persistent, verified, restorable storage and
append-only or content-addressed keys; mutable latest-only state is never the
sole scientific record.

NFR50: Every reported decision or metric resolves from experiment and source
identities through raw segments, canonical observations, partitions/windows,
bundle, score, truth join, and evaluation record without UI or hidden state.

NFR51: All planned valid, invalid, aborted, and unfavorable runs are retained
and reported with applicable uncertainty, resource/quality evidence,
limitations, and locally-measured versus published-reference status.

NFR52: Planning approval is machine- and human-readable and remains distinct
from authorization to implement, download data, capture syscalls, train,
execute experiments, or activate a feature.


