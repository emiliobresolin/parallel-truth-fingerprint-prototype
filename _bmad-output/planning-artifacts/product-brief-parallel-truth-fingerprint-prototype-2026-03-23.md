---
stepsCompleted:
  - 1
  - 2
  - 3
  - 4
  - 5
  - 6
inputDocuments:
  - /c:/Users/emili/Desktop/Projets/parallel-truth-fingerprint-prototype/docs/input/Arquitetura Baseada em Fonte de Verdade Paralela para Geração de Fingerprint Físico-Operacional em Sistemas Industriais Legados - Emilio Bresolin.pdf
  - /c:/Users/emili/Desktop/Projets/parallel-truth-fingerprint-prototype/docs/input/Arquitetura Baseada em Fonte de Verdade Paralela para GeraÃ§Ã£o de Fingerprint FÃ­sico-Operacional em Sistemas Industriais Legados_DEFINIÇÃO_DO_PROBLEMA.txt
  - /c:/Users/emili/Desktop/Projets/parallel-truth-fingerprint-prototype/docs/input/Arquitetura Baseada em Fonte de Verdade Paralela para GeraÃ§Ã£o de Fingerprint FÃ­sico-Operacional em Sistemas Industriais Legados_OBJECTIVOS.txt
  - /c:/Users/emili/Desktop/Projets/parallel-truth-fingerprint-prototype/docs/input/Arquitetura Baseada em Fonte de Verdade Paralela para GeraÃ§Ã£o de Fingerprint FÃ­sico-Operacional em Sistemas Industriais Legados_ARQUITETURA_PROPOSTA.txt
date: 2026-03-23
author: Emilio
---

# Product Brief: parallel-truth-fingerprint-prototype

## Executive Summary

This project is an academic prototype that translates an approved research architecture into a simplified but functional local proof of concept. The prototype addresses a central integrity problem in industrial legacy systems: supervisory and decision layers often rely on digital values exposed through PLC and SCADA paths without an independent mechanism to verify that these values still represent the real process state.

The prototype preserves the four architectural pillars defined in the approved research scope: decentralized edge observation, Byzantine-style trust validation between edges, comparison between the validated edge state and the SCADA state, and LSTM-based fingerprint generation for temporal anomaly detection. To keep the implementation feasible for a Master's degree prototype, physical sensors, PLC behavior, signal duplication hardware, SCADA infrastructure, and cloud infrastructure are simulated locally, while the architectural meaning of each layer is preserved.

The demonstration scenario is a single compressor monitored through three simulated sensors: temperature, pressure, and RPM. Three independent edge nodes perform local acquisition associated with one sensor each, exchange observations through MQTT, reconstruct a shared replicated view of the compressor state, execute a Byzantine-style validation round, exclude suspicious edges in that round, and produce a consolidated valid state. This consensused state is then compared against a fake OPC UA SCADA view, persisted to local object storage when valid, and used as the basis for LSTM training and inference. The prototype must detect at least one replay scenario through fingerprint behavior and must raise a separate alert when the SCADA view diverges from the consensused edge state beyond configurable tolerance.

Implementation note: in the prototype, the real consensus implementation is CometBFT plus a Go ABCI application. BBD/FABA remains conceptual inspiration from the approved PEP. The final lightweight SCADA-inspired demo UI is required for the final demonstration, but only as the last layer after the backend/runtime/services are complete and stable.

---

## Core Vision

### Problem Statement

Industrial legacy environments frequently assume that values exposed by PLC and SCADA layers are faithful representations of the physical process. This assumption creates a structural integrity risk: if the digital path is manipulated, delayed, replayed, or gradually drifted while remaining plausible, supervisory systems may continue operating on values that no longer correspond to the true process condition.

The approved research addresses this problem by introducing an independent validation path that does not rely exclusively on the logical supervisory domain. In the prototype, this principle must be preserved even though the physical instrumentation is simulated.

### Problem Impact

When this integrity gap is not addressed, silent attacks such as replay, false data injection, and gradual drift can remain difficult to identify because the exposed digital values may continue to look operationally plausible. As a result, systems that depend only on the logical path may validate, learn from, or react to already-compromised data.

For this academic prototype, the impact is framed as an architectural validation objective: the prototype must demonstrate that an independently reconstructed and consensused state can serve as a trustworthy reference for both SCADA integrity comparison and temporal anomaly analysis.

### Why Existing Solutions Fall Short

The approved research document identifies a recurring limitation in existing approaches: many detection mechanisms operate primarily on the digital domain, such as network traffic, logs, or already-digitized process values. When the logical path itself is the attack surface, these mechanisms may inherit the same trust assumptions they are supposed to validate.

This prototype therefore does not focus on generic anomaly detection alone. It preserves a combined architecture in which independent edge-side observation, distributed trust evaluation, physical-versus-logical comparison, and temporal fingerprinting work together. That combination is the essential gap addressed by the prototype.

### Proposed Solution

The prototype will implement a simplified local proof of concept of the approved architecture for one compressor using three simulated sensors: temperature, pressure, and RPM.

Each simulated edge is associated with one local sensor and runs a local Python acquisition service that represents independent physical-side observation at the edge. In architectural terms, this service stands in for local HART / 4-20 mA signal acquisition before the PLC path, preserving the research requirement that the edge first observes its own sensor locally and independently before any shared communication occurs. After this local acquisition, the edge publishes its observation through MQTT. The other edges consume those published observations so that every edge reconstructs a replicated view of the full compressor state. A Byzantine-style validation round is then executed over the shared observations to rank trust, exclude suspicious edges immediately in that round, and produce a consolidated valid compressor state.

In prototype terms, this consolidated state represents the physical side of the architecture. It is then compared through OPC UA against the fake SCADA state, which represents the logical side. The comparison is performed sensor by sensor for temperature, pressure, and RPM using configurable tolerance thresholds. Whenever the difference between the consensused state and the SCADA state exceeds the configured tolerance for any sensor, the system generates a specific SCADA divergence alert.

Valid consolidated data is then persisted to local object storage using MinIO. Stored normal data is used by the LSTM service to train a reusable fingerprint model of normal compressor behavior. During inference, the LSTM produces an anomaly score and a normal/anomalous classification. This behavioral analysis path is intended to detect replay attacks and other temporal inconsistencies that may not be revealed by direct SCADA comparison alone. The SCADA divergence alert and the LSTM anomaly alert remain distinct outputs of the architecture.

### Key Differentiators

The distinguishing characteristic of this prototype is not broader feature scope, but fidelity to the approved research logic under simplified implementation conditions.

Its main architectural differentiators are:
- the trusted reference is not the SCADA value, but the consensused state reconstructed from independent edge-side acquisition paths
- trust evaluation is distributed across edges and includes immediate exclusion of suspicious nodes in the active validation round
- SCADA comparison is a direct integrity check between the consensused physical-side state and the logical supervisory state exposed through OPC UA
- only valid normal data is used for LSTM training, reducing the risk of learning from suspicious or inconsistent observations
- temporal anomaly detection is separated from SCADA divergence detection, allowing replay and other behavioral inconsistencies to be identified through the fingerprint path even when direct value comparison is insufficient
- infrastructure is simplified for local execution, but the architectural sequence and research meaning of each stage are preserved

## Target Users

### Primary Users

The primary user of this prototype is the researcher acting as prototype operator and demonstrator during development, execution, validation, and academic presentation.

This user needs to:
- configure and run the local prototype services
- observe the simulated compressor state across temperature, pressure, and RPM
- inspect MQTT exchange, replicated edge state, consensus results, SCADA comparison results, stored valid data, and LSTM outputs
- trigger or replay demonstration scenarios, including normal behavior, SCADA divergence, suspicious edge participation, and replay-oriented anomaly cases
- explain how each architectural stage maps back to the approved research proposal

For this user, success means that the prototype is runnable locally, produces clear and traceable outputs, preserves the intended architectural sequence, and supports demonstration of the research argument without unnecessary interface complexity.

### Secondary Users

The first secondary user group is composed of academic evaluators, including the advisor and committee. These users do not operate the system as primary hands-on users, but they evaluate whether the prototype faithfully represents the approved research architecture and whether the results support the academic objective.

These users need to:
- understand how the prototype maps to the research problem and proposed architecture
- inspect the logic of decentralization, Byzantine-style validation, SCADA comparison, storage, and LSTM-based fingerprinting
- evaluate whether the implementation preserves the distinction between simulated infrastructure and real architectural behavior
- review logs, outputs, alerts, and demonstration evidence to assess coherence and validity

For this group, success means that the prototype is structurally clear, academically defensible, and capable of demonstrating the intended contribution with traceable evidence.

The second secondary user group is composed of technical readers or future implementers who may study the prototype to understand, reproduce, or extend the architecture.

These users need to:
- understand the modular structure of the prototype
- inspect the data flow from local acquisition through MQTT exchange, consensus, SCADA comparison, storage, and LSTM inference
- identify which parts were simplified for the academic prototype and which architectural properties were intentionally preserved
- use the prototype as a reference for future refinement, experimentation, or expansion

For this group, success means that the prototype is understandable, modular, and sufficiently documented to support extension without ambiguity about its intended architectural meaning.

As a future-facing reference only, an industrial analyst or operator may eventually benefit from the architectural ideas behind the prototype, especially for understanding integrity divergence and anomaly behavior. However, this role is not treated as a direct user of the current academic prototype.

### User Journey

The primary interaction journey begins with the researcher starting the local environment and launching the simulated services for sensor generation, edge acquisition, MQTT communication, fake SCADA, storage, and LSTM processing. The researcher then observes the current compressor state, sensor readings, consensus output, SCADA comparison results, and anomaly outputs through logs and, if present, a minimal local visualization layer used only as a demonstration aid.

During the demonstration flow, the researcher presents the normal operating path first: local edge acquisition, MQTT sharing, replicated compressor state, Byzantine-style validation, consensused state generation, SCADA comparison, persistence of valid data, and LSTM-based fingerprint processing. The researcher then introduces controlled scenarios such as SCADA divergence or replay-oriented temporal inconsistency and uses the outputs to explain how the architecture distinguishes between direct logical divergence alerts and behavioral anomaly alerts.

Academic evaluators interact with the prototype primarily through observation and analysis of the demonstration, the generated outputs, and the architectural explanation. Their key moment of value is when the prototype clearly shows that the consensused edge state acts as an independent reference against the logical SCADA state and that replay-oriented inconsistency can be surfaced through the LSTM path.

Technical readers and future implementers interact with the prototype by inspecting its structure, artifacts, and execution flow after or alongside the demonstration. Their key moment of value is when they can follow the architecture end to end and understand exactly how the simplified implementation preserves the intended research logic.

## Success Metrics

The success of this academic prototype is defined primarily through demonstrable architectural fidelity and end-to-end execution rather than business or market metrics. The prototype is considered successful if it preserves the four core pillars of the approved research while executing the full pipeline locally in a clear and reproducible way.

The minimum success condition is that the prototype demonstrates the complete architectural flow from simulated sensor generation through local edge acquisition, MQTT exchange, replicated shared state, Byzantine-style validation, SCADA comparison, valid-data persistence, and LSTM-based inference.

From the perspective of the primary user, success means the prototype can be executed locally, explained coherently during presentation, and used to show that the independent edge-side path produces a trustworthy reference for both SCADA integrity checking and temporal anomaly detection.

### Business Objectives

For this academic prototype, business objectives are replaced by prototype validation objectives:

- demonstrate decentralized operation across three independent simulated edges
- demonstrate Byzantine-style validation that ranks trust and excludes a suspicious edge within the active round
- demonstrate production of a valid consolidated compressor state after consensus
- demonstrate comparison between the consensused edge state and the fake OPC UA SCADA state
- demonstrate tolerance-based SCADA divergence alerting when the logical state deviates from the consensused state
- demonstrate persistence of valid data only into local MinIO storage
- demonstrate LSTM training using only normal data
- demonstrate generation and reuse of a fingerprint model
- demonstrate anomaly output based on temporal inconsistency, especially replay-oriented behavior
- demonstrate that the prototype remains locally executable, modular, and presentation-ready

### Key Performance Indicators

The key indicators for this prototype are acceptance-based and observable during execution:

- End-to-end pipeline execution:
  The full pipeline must run from simulated sensor generation to LSTM inference without breaking the architectural sequence.

- Decentralized edge behavior:
  Each edge must acquire only its associated local sensor before publishing through MQTT, and all edges must reconstruct a replicated view of temperature, pressure, and RPM.

- Consensus behavior:
  A Byzantine-style validation round must produce trust evaluation results and exclude a suspicious edge in the affected round.

- Consolidated state generation:
  The system must produce a valid compressor state after exclusion of suspicious contributions.

- SCADA comparison behavior:
  The consensused state must be compared against the fake OPC UA SCADA state sensor by sensor for temperature, pressure, and RPM using configurable tolerance.

- SCADA divergence alerting:
  A specific SCADA divergence alert must be generated when the tolerance threshold is exceeded for at least one sensor.

- Valid-data persistence:
  Only data considered valid after consensus must be persisted into MinIO.

- LSTM training integrity:
  The training flow must use normal data only.

- Fingerprint generation:
  The LSTM service must generate a reusable model or fingerprint artifact for later inference.

- Anomaly inference:
  The inference flow must produce an anomaly score and a normal/anomalous classification.

- Replay or temporal inconsistency detection:
  At least one replay-oriented or temporally inconsistent scenario must trigger anomaly behavior through the fingerprint path.

- Demonstration quality:
  Logs must make each pipeline stage understandable, system state and alerts must be observable, and the demonstration must be reproducible. Simple local charts or visualization may support explanation but are optional rather than required.

## MVP Scope

### Core Features

For this project, the MVP scope is the minimum academically valid prototype capable of demonstrating the approved architecture end to end while preserving the four research pillars.

The core features in scope are:

- simulation of one compressor with three sensors: temperature, pressure, and RPM
- three simulated edges, each associated with exactly one local sensor
- a local Python acquisition service on each edge representing independent HART / 4-20 mA acquisition semantics before the PLC path
- MQTT-based publication of local edge observations
- cross-edge consumption of published observations so that each edge reconstructs a replicated shared compressor state
- Byzantine-style validation over the shared observations
- trust ranking of participating edges
- immediate exclusion of suspicious edge contributions within the active round
- generation of a consolidated valid compressor state after consensus
- a fake OPC UA SCADA service representing the logical supervisory view
- sensor-by-sensor comparison between the consensused state and the SCADA state for temperature, pressure, and RPM
- configurable tolerance thresholds for SCADA comparison
- generation of a specific SCADA divergence alert when tolerance is exceeded
- persistence of valid data only into local MinIO storage
- LSTM training using only normal data
- generation of a reusable fingerprint model
- inference output including anomaly score and normal/anomalous classification
- demonstration of replay or temporal inconsistency detection through fingerprint behavior
- clear logs for each pipeline stage
- optional simple local charts or minimal local visualization to support demonstration of compressor state, sensor values, logs, and alerts

This scope is intentionally limited to what is necessary to validate the architectural logic of the research in a simplified but functional local prototype.

### Out of Scope for MVP

The following items are explicitly out of scope for this prototype:

- real physical sensors and industrial hardware
- real PLC integration
- real analog HART / 4-20 mA acquisition hardware
- real industrial network or protocol stack beyond the defined simulation
- production-grade user interface
- multi-equipment plant coverage
- cloud deployment
- high-frequency or real-time optimization beyond the one-minute collection reference
- advanced security hardening
- benchmarking against large datasets
- multi-model machine learning experimentation beyond a single LSTM-based path

These exclusions are intentional and preserve the prototype as a focused academic proof of concept rather than a production-ready industrial system.

### MVP Success Criteria

The MVP is successful if it demonstrates the complete architectural sequence locally and makes each critical stage observable and explainable during execution.

The essential scope-level success criteria are:

- the prototype runs end to end from simulated sensor generation to LSTM inference
- decentralized edge acquisition and replicated state sharing are visible in execution
- the consensus round produces trust evaluation and excludes a suspicious edge when required
- a valid consolidated compressor state is produced after consensus
- SCADA comparison is executed through the fake OPC UA path using configurable tolerance
- SCADA divergence alerting occurs when the logical state deviates beyond tolerance
- only valid data is persisted to MinIO
- LSTM training uses normal data only
- a reusable fingerprint artifact is produced
- replay-oriented or temporally inconsistent behavior is detectable through anomaly output
- logs and outputs are sufficiently clear to support demonstration and academic evaluation
- the demonstration is reproducible in the local environment

### Future Vision

Near-term future evolution of this prototype may include limited research-driven extensions that remain faithful to the same architectural direction.

Relevant future extensions include:

- replacing parts of the simulated acquisition path with more realistic edge-side acquisition behavior
- expanding the prototype beyond one compressor while preserving decentralized validation logic
- introducing richer attack scenarios beyond the initial replay and SCADA divergence demonstrations
- improving visualization and evaluation tooling to make architectural stages, alerts, and results easier to inspect during presentation and analysis

These future directions are extensions of the same academic line of work and do not change the intended scope of the current prototype.
