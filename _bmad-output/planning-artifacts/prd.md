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

## Functional Requirements

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

## Non-Functional Requirements

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


