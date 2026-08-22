---
stepsCompleted: [1, 2, 3, 4, 5, 6]
inputDocuments:
  - 'C:/Users/emili/Downloads/autoencoder LSTM.md'
workflowType: 'research'
lastStep: 6
research_type: 'technical'
research_topic: 'Scientifically grounded industrial signal, syscall, and anomaly simulation for parallel truth fingerprinting'
research_goals: 'Replace unsupported constants and labeled-dataset shortcuts with traceable standards, manuals, papers, realistic edge telemetry, justified model choices, and an implementation-ready comparative evaluation plan.'
user_name: 'Emilio'
date: '2026-08-15'
web_research_enabled: true
source_verification: true
---

# Research Report: Technical

**Date:** 2026-08-15
**Author:** Emilio
**Research Type:** Technical

---

## Research Overview

This research re-evaluates the prototype after academic review identified unsupported simulator constants, mixed measurement domains, circular SCADA evidence, labelled-dataset shortcuts, and insufficient justification for model and threshold choices. It combines a repository audit with current primary sources: standards-owner pages, manufacturer manuals, official dataset repositories and loaders, peer-reviewed model papers, and NIST guidance. Every proposed numeric parameter is classified as direct, derived, measured, preregistered experimental factor, or explicit mock; a citation alone is never treated as proof that a parameter transfers to this compressor experiment.

The resulting design has two and only two detection modalities: physical instrumentation and Linux host syscalls. The custom physical stream preserves raw 4-20 mA as the edge evidence, uses deterministic span normalization for model input, and retains engineering-unit conversions for process simulation, supervision, and interpretation. The syscall stream captures real kernel calls emitted by controlled Linux edge workloads; it does not modify syscalls or execute ADFA-LD identifiers. ADFA-LD and LID-DS remain external syscall benchmarks, HAI remains an external physical/SCADA benchmark, and the new synchronized project dataset is the only evidence source eligible for physical-plus-syscall fusion.

The implementation recommendation is an incremental legacy-to-shadow-to-active migration with immutable manifests, versioned contracts, isolated truth, independent OPC UA supervision, Python/Go consensus parity, frozen model bundles and thresholds, and long-run reconstruction tests. The official-source archive and parameter-evidence ledger make every adopted claim and number inspectable while preserving unresolved license, version, and generalization limitations.

## Technical Research Scope Confirmation

**Research Topic:** Scientifically grounded industrial signal, syscall, and anomaly simulation for parallel truth fingerprinting

**Research Goals:** Replace unsupported constants and labeled-dataset shortcuts with traceable standards, manuals, papers, realistic edge telemetry, justified model choices, and an implementation-ready comparative evaluation plan.

**Technical Research Scope:**

- Architecture analysis - signal-domain boundaries, edge event generation, fingerprinting, dataset adapters, and evaluation pipeline
- Implementation approaches - standards-based signal conversion, syscall sequence generation, anomaly injection, and reproducible calibration
- Technology stack - current simulator and ML stack plus justified changes needed for ADFA-LD, LID-DS, HAI, LSTM, and GRU
- Integration patterns - instrument signals to edge features, process telemetry to host events, model outputs to comparative metrics
- Performance considerations - sampling, windowing, run duration, model calibration, resource use, and statistical validity

**Research Methodology:**

- Current web data with rigorous source verification
- Preference for standards, official manuals, dataset-owner publications, and peer-reviewed primary research
- Multi-source validation for critical numeric claims
- Explicit confidence levels and provenance for every adopted constant
- Clear separation between sourced values, derived values, configurable experimental factors, and mocks

**Scope Confirmed:** 2026-08-15

---

<!-- Content will be appended sequentially through research workflow steps -->

## Technology Stack Analysis

### Programming Languages

The executable prototype is primarily Python, with `requires-python = ">=3.14"` in `pyproject.toml`. The lockfile currently resolves Python libraries including asyncua 1.1.8, Keras 3.13.2, MinIO 7.2.20, NumPy 2.4.4, Paho MQTT 2.1.0, and Torch 2.11.0. Python remains suitable for orchestration, simulation, artifact processing, and ML experimentation. Python 3.14 is a stable release, but its newer concurrency modes do not by themselves justify changing the project's process boundaries; third-party extension compatibility must still be verified for any free-threaded build. [Python 3.14 release documentation](https://docs.python.org/3.14/whatsnew/3.14.html)

The consensus application is a separate Go 1.24 module using CometBFT v1.0.0 (`abci/consensus_app/go.mod`). This remains an appropriate boundary because CometBFT defines ABCI as the interface between its state-machine replication engine and the replicated application, with protocol-buffer messages allowing applications in multiple languages. [CometBFT ABCI 2.0 specification](https://docs.cometbft.com/main/spec/abci/)

_Current languages:_ Python 3.14 for the prototype and Go 1.24 for the ABCI application.  
_Recommended evolution:_ retain both; add no new language until an evidence-backed edge syscall collector requires a Linux-specific sidecar.  
_Confidence:_ High, based on repository manifests and official documentation.

### Development Frameworks and Libraries

The current Python framework set is coherent but represents two ML problems that must remain separate:

- The runtime physical fingerprint is a Keras LSTM autoencoder over persisted compressor windows.
- The offline HIDS branch is composed of supervised Keras/Torch LSTM and GRU classifiers over labelled ADFA-LD and LID-DS-derived sequences.

Keras 3 officially supports TensorFlow, JAX, and PyTorch backends; retaining the Torch backend preserves the existing implementation while allowing controlled LSTM/GRU comparison through one API. [Keras 3 overview](https://keras.io/keras_3/) PyTorch supplies native LSTM and GRU sequence layers, but the presence of both implementations is not evidence that either is scientifically superior; model selection must be established later through preregistered baselines and ablation. [PyTorch LSTM](https://docs.pytorch.org/docs/stable/generated/torch.nn.LSTM.html) [PyTorch GRU](https://docs.pytorch.org/docs/stable/generated/torch.nn.GRU.html)

NumPy remains the numerical substrate for window arrays, normalization, deterministic simulation, and `.npz` artifacts. Its official API covers multidimensional arrays and numerical/statistical operations required by this prototype. [NumPy documentation](https://numpy.org/doc/stable/)

For OT-facing integration, asyncua supplies an asynchronous OPC UA client/server implementation, and Paho supplies MQTT 3.1, 3.1.1, and 5.0 client support. Both match the current fake-SCADA and edge publish/subscribe boundaries. [asyncua project](https://github.com/FreeOpcUa/opcua-asyncio) [Eclipse Paho Python client](https://eclipse.dev/paho/files/paho.mqtt.python/html/index.html)

The instrumentation layer needs a new explicit conversion/quality component rather than a new general-purpose framework. Its contract should retain three synchronized representations:

1. raw transmitter signal in mA;
2. normalized loop position `z = (I_mA - 4) / 16`, with device-specific fault/quality state;
3. engineering-unit value derived from the configured lower and upper range values for process physics and operator interpretation.

This is consistent with current Rockwell documentation, which describes input scaling as translation from electrical signal units into engineering units and maps 4, 12, and 20 mA to 0%, 50%, and 100%. [Rockwell PointMax analog I/O manual](https://literature.rockwellautomation.com/idc/groups/literature/documents/um/5034-um003_-en-p.pdf) The ML input can therefore use normalized instrument-domain features without erasing the engineering-unit representation needed by the compressor model.

RPM does not need to change to 1–5 V. A real Electro-Sensors FB420 shaft-speed sensor exposes programmable 4 mA and 20 mA RPM endpoints. [FB420 official product page](https://www.electro-sensors.com/products/shaft-speed-sensors/fb420) A selectable 4–20 mA/0–5 V tachometer also exists, confirming voltage is an alternative rather than a requirement. [Monarch F2A3X](https://monarchinstrument.com/product/f2a3x-frequency-to-analog-converter-tachometer-with-nist-certificate/)

_Major frameworks:_ Keras 3, Torch, NumPy, asyncua, Paho MQTT.  
_Required addition:_ a provenance-aware signal adapter and separate syscall-event adapter, both behind stable contracts.  
_Confidence:_ High for capabilities and signal architecture; model superiority remains unproven.

### Database and Storage Technologies

The prototype intentionally has no relational or NoSQL database. Its persistence boundary is MinIO object storage with a local-filesystem test/experiment alternative. The official MinIO Python SDK provides high-level APIs for MinIO or other Amazon S3-compatible object stores. [MinIO Python SDK](https://github.com/minio/minio-py)

Current artifact formats include JSON consensus and training metadata, NumPy `.npz` windows, native `.keras` models, ADFA-LD text traces, LID-DS syscall recordings, and HAI CSV time series. The storage architecture should be retained but strengthened with immutable experiment manifests containing source URL, source version/commit, SHA-256, acquisition time, schema version, unit/range metadata, label policy, split identity, random seed, and configuration digest.

Dataset formats require version-specific adapters:

- ADFA-LD is a set of numeric syscall-ID sequences intended for syscall-based HIDS evaluation. The official UNSW page grants academic use but prohibits commercial use. [UNSW ADFA IDS datasets](https://research.unsw.edu.au/projects/adfa-ids-datasets)
- LID-DS 2021 provides an official recording/dataloader framework and richer syscall records. Its project is GPLv3-or-later and should be isolated through a reproducible Linux container or clean-room schema-compatible adapter rather than importing its Python 3.7-era environment into the Python 3.14 runtime. [Official LID-DS repository](https://github.com/LID-DS/LID-DS)
- HAI releases use time-continuous CSV process telemetry, but layouts differ by release. HAI 23.05 includes separate label files, so a single assumed schema across HAI releases would be invalid. [Official HAI repository](https://github.com/icsdataset/hai) [HAI 23.05 files](https://github.com/icsdataset/hai/tree/master/hai-23.05)

Labels must be stored as evaluation metadata and excluded from unsupervised training features. The current ADFA-LD/LID-DS supervised paths can remain as historical baselines, but they cannot serve as the live edge pipeline requested by the revised research question.

_Primary storage:_ local MinIO plus a local-filesystem adapter.  
_Artifact formats:_ JSON, NPZ, Keras archives, dataset-native text/syscall records, and versioned CSV.  
_Required change:_ evidence manifests and version-specific dataset adapters; no database migration is justified.  
_Confidence:_ High.

## Architectural Patterns and Design

### Recommended Architecture Style

The recommended target is a **local, modular, event-driven research testbed with ports-and-adapters boundaries and isolated evaluation authority**. It is not a cloud microservice migration. The current Python orchestration, Go/CometBFT consensus application, MQTT broker, OPC UA service, MinIO store, and dashboard remain appropriate deployment boundaries, but scientific policy must move out of scripts and infrastructure adapters into versioned domain contracts and experiment specifications.

The dependency direction is:

```text
domain contracts
  -> application ports and use cases
    -> MQTT / OPC UA / MinIO / CometBFT / ML adapters
      -> local composition root and dashboard read model
```

This follows the ports-and-adapters principle of keeping the application testable independently of its external protocols. [Hexagonal Architecture, Alistair Cockburn](https://alistair.cockburn.us/hexagonal-architecture)

The architecture is divided into two evidence branches and a restricted evaluation branch:

```text
Experiment controller
  |
  +-- physical process model -> transmitter profile -> 4-20 mA -> edge acquisition
  |                                                        +-> physical consensus
  |                                                        +-> independent OPC UA path
  |                                                        +-> physical detector
  |
  +-- allowlisted edge workload -> actual Linux syscall capture -> syscall detector
  |
  +-- restricted scenario truth ----------------------------------------------+
                                                                              |
Frozen physical and syscall scores -> late fusion -> restricted evaluator <---+
```

ADFA-LD and LID-DS validate the syscall branch. HAI validates the physical time-series branch. Only the new synchronized project capture contains both modalities from the same runs and can support physical-only, syscall-only, and combined-detector claims.

### Industrial Signal Boundary

The signal contract is corrected to make **the received 4-20 mA current authoritative at the edge**. The project will preserve three non-conflicting representations:

1. `loop_current_ma`: the raw electrical measurement received or simulated at the acquisition boundary;
2. `normalized_current`: the deterministic span transformation `(I_mA - 4) / 16`, without clipping before quality classification;
3. `engineering_value`: a derived value calculated from the configured lower and upper range values for SCADA, operator display, and modules that explicitly require physical semantics.

The generic derived conversions are:

```text
normalized_current = (I_mA - 4 mA) / 16 mA
engineering_value = LRV + normalized_current * (URV - LRV)
```

At 12 mA the loop is at 50% of its configured span; the corresponding temperature, pressure, or RPM depends on that instrument's LRV and URV. Rockwell documents input scaling as translation from electrical signal units into engineering units, with 4, 12, and 20 mA corresponding to 0%, 50%, and 100% in its example. [Rockwell PointMax Analog I/O Modules User Manual, April 2025](https://literature.rockwellautomation.com/idc/groups/literature/documents/um/5034-um003_-en-p.pdf) NI documents the same endpoint scaling method. [NI 4-20 mA scaling guidance](https://knowledge.ni.com/KnowledgeArticleDetails?id=kA00Z000000PASfSAO)

This is a project-specific analysis boundary, not a claim that every industrial controller performs all internal calculations in mA. Industrial modules may expose signal units, percent of span, or engineering units to controller logic. In this prototype:

- the simulator retains engineering-domain state because compressor physics cannot be meaningfully generated from current alone;
- the transmitter is the only component that converts process state to current;
- edge acquisition, divergence input, and physical-detector input remain in the electrical domain, using mA or its deterministic span representation;
- SCADA and physical-analysis modules receive a separately derived engineering representation;
- raw current, normalization, calibration profile, engineering derivation, and quality state remain traceable in every artifact.

For redundant observations of the same sensor and scaling profile, divergence can be expressed directly in mA. A cross-sensor aggregate must first convert each residual to a dimensionless, profile-aware value, because the same current deviation does not imply the same measurement uncertainty or process risk for different instruments. Any weighting beyond the documented 16 mA span must be derived from cited device uncertainty or preregistered calibration data, not anonymous constants.

RPM remains 4-20 mA because real shaft-speed transmitters such as the Electro-Sensors FB420 provide programmable 4 mA and 20 mA RPM endpoints. [FB420 official product page](https://www.electro-sensors.com/products/shaft-speed-sensors/fb420)

### OT Zones, Conduits, and Control Authority

The prototype will apply a bounded local interpretation of OT zones and conduits:

| Zone | Components | Permitted authority |
|---|---|---|
| Experiment/control | Compressor physics, controller, automatic excitation schedule, transmitter profiles | Sole owner of setpoint and actuator-reference writes |
| Acquisition/edge | Electrical acquisition, signal-quality classification, edge buffers and publishers | Read measurements and publish evidence |
| Supervision | Independent OPC UA server/client boundary and dashboard | Read/subscribe by default |
| Security analytics | Physical autoencoder, syscall detector, divergence evidence and alerts | Read-only analysis; no actuator authority |
| Replay/evaluation | ADFA-LD, LID-DS, HAI adapters, labels, truth joins and metrics | Offline/restricted evaluation only |
| Artifact/orchestration | Run manifests, raw evidence, models, scores and reports | Start/stop/configure experiments and preserve evidence |

There is no analytics-to-control conduit. A detector timeout, false positive, crash, missing model, or bad-quality input must never alter the compressor command. The control loop continues if MQTT, MinIO, OPC UA, or analytics becomes unavailable. NIST SP 800-82 Rev. 3 recommends identifying OT components and flows while accounting for performance, reliability, and safety requirements. [NIST SP 800-82 Rev. 3](https://csrc.nist.gov/pubs/sp/800/82/r3/final) IEC 62443-3-2 defines the system-under-consideration and zone/conduit risk-assessment concepts; this testbed will demonstrate the pattern but will not claim formal IEC 62443 certification. [IEC 62443-3-2:2020](https://webstore.iec.ch/en/publication/30727)

The requested automatic 25%-75% variation belongs to the experiment controller. It will be named `speed_reference_pct` or `capacity_reference_pct`, not electrical power, unless a selected compressor/drive profile explicitly defines a power command. With a declared 0%-100% linear 4-20 mA reference profile, 25%-75% derives to 8-16 mA. Waveform, ramp rate, dwell time, sequence, and repetition count remain preregistered experimental factors or device-specific parameters; there is no universal standard value for them.

### Component and Contract Boundaries

#### 1. Experiment Control and Restricted Truth

`ExperimentSpec` owns the run ID, cited parameter-set IDs, schedule definition, seed or input trace, workload identity, dataset/split identity, timing policy, and expected repetitions. The scenario controller emits `ScenarioTruth.v1` to a restricted artifact namespace. Truth must not enter MQTT observation messages, consensus transactions, detector tensors, model-serving objects, or detector-visible dashboard payloads.

#### 2. Instrumentation and Signal Contract

`SignalObservation.v2` owns raw current, normalized current, derived engineering value, LRV/URV, units, signal quality, source and observed timestamps, device/transmitter identity, and calibration/profile provenance. One validated factory performs all conversions. Compatibility projections may generate the existing `RawHartPayload`, but downstream modules may not repeat conversion formulas independently.

#### 3. Edge Telemetry and Syscall Capture

Physical observations and syscalls use separate topics and schemas. `SyscallEventBatch.v1` contains ordered events, edge/boot/process/thread identity, collector and kernel provenance, source sequence, time information where available, capture-quality/drop counters, and an immutable raw-segment hash. Raw syscall data is batched and retained locally/object storage; it never enters CometBFT physical consensus.

Syscalls are captured from deterministic, allowlisted Linux edge workloads. ADFA numeric identifiers are not executed as portable Linux calls, and LID recordings are not described as calls between edges. Inter-edge behavior remains network/application traffic; syscalls are local host events caused by that workload.

#### 4. Physical Consensus

`ConsensusRoundInput.v2` explicitly declares the comparison basis, signal profile, quality policy, and contract version. Because the Python and Go implementations currently duplicate trust rules, the Python serializer/reference engine, Go transaction/state types, thresholds, query response, and downstream mapper must change atomically and share golden JSON/test vectors. Scenario labels, syscalls, and detector decisions remain outside consensus.

#### 5. Independent SCADA Boundary

The current SCADA path is circular because consensus is written to the fake OPC UA server before it is read back for comparison. The target path writes an independent pre-consensus plant/transmitter snapshot to the OPC UA server and reads it through a distinct client adapter. OPC UA `DataValue` status, `sourceTimestamp`, and `serverTimestamp` are retained. Loop current and engineering process value are exposed as separate analogue nodes; ML-normalized values use a research namespace. [OPC UA DataValue](https://reference.opcfoundation.org/Core/Part4/v105/docs/7.11) [OPC UA AnalogItem semantics](https://reference.opcfoundation.org/Core/Part8/v105/docs/5)

#### 6. Immutable Evidence and Model Registry

MinIO remains the artifact repository, with versioned namespaces for raw observations, syscall segments, restricted truth, valid-consensus datasets, models, detector outputs, fusion outputs, and evaluation reports. Every entity has a content hash, schema hash, parent-artifact references, activity/tool identity, code revision, and source/version/license metadata. W3C PROV supplies the entity/activity/agent and derivation vocabulary used as the lineage model. [W3C PROV-DM](https://www.w3.org/TR/prov-dm/)

A promoted detector is an atomic deployment bundle containing model weights, architecture, preprocessing/scaler, feature schema, sequence contract, vocabulary and unknown-token policy where relevant, calibration dataset hashes, frozen threshold, score direction, output schema, and runtime image/dependency digest. Changing a threshold creates a new bundle even when the weights are unchanged.

#### 7. Detectors and Dataset Adapters

All detector runners implement a common lifecycle—prepare, train on approved normal data, calibrate, infer with a frozen bundle, and evaluate—but do not share one feature tensor:

- physical branch: current-domain LSTM-AE and GRU-AE candidates plus simple statistical, PCA/Isolation Forest, and Conv1D baselines;
- syscall branch: categorical embedding plus LSTM/GRU next-event or categorical reconstruction, with STIDE/n-gram baseline;
- ADFA adapter: original sequence and official split provenance, no fabricated timestamps, six attack families preserved;
- LID adapter: official recording archive/layout and syscall schema in an isolated legacy-compatible Linux environment;
- HAI adapter: version-specific physical-tag, label, timestamp, and split handling;
- custom adapter: synchronized current-domain observations, captured edge syscalls, workload commands, and restricted truth.

NIST AI RMF requires documentation of test sets, metrics, tools, uncertainty, benchmark comparisons, and performance under conditions similar to deployment. [NIST AI RMF](https://airc.nist.gov/airmf-resources/airmf/5-sec-core/) No architecture or paper establishes LSTM or GRU as a universal winner; both remain candidates until controlled comparison.

#### 8. Late Fusion and Evaluation

`DetectorScore.v1` contains model/schema/calibration identity, window identity, score direction, raw and calibrated score, frozen threshold identity, decision, latency, missingness, and quality flags—but no truth. Fusion operates only on calibrated score artifacts and explicitly represents a missing modality. Simple OR, AND, maximum, or unweighted-mean rules may be preregistered. Learned weights are supervised and require a separate validation partition.

The evaluator joins frozen score hashes to restricted truth only after inference closes. Fair paired ablation on the same held-out custom runs compares physical-only, syscall-only, and preregistered fusion rules. Public ADFA/LID syscall results and HAI physical results remain separate benchmark tables rather than one invalid global loss average.

### Data Integrity, Security, and Reproducibility

Every run manifest will include:

- run ID and start/end times;
- source-code revision and dirty-tree indicator;
- dependency lock and container-image digests;
- seeds, workload/input traces, node allocation and repetition ID;
- every numeric parameter, unit, category, value, derivation, citation and approval status;
- instrument LRV/URV, conversion, uncertainty and quality-profile IDs;
- sampling, clock synchronization and measured timing-quality evidence;
- excitation schedule and actual command trace;
- dataset version, file hashes, license/access terms and immutable split;
- model, feature schema, preprocessing and threshold bundle hashes;
- raw, normalized, feature, score, truth and report artifact hashes.

Raw evidence is append-only and derived artifacts are reproducible from explicit parents. Source archives are kept unchanged. Labels are structurally isolated through credentials and object prefixes; detector identities cannot read them. Least-privilege and protected audit-information principles are consistent with NIST SP 800-53 AC-5, AC-6, and AU-9. [NIST SP 800-53 Rev. 5](https://csrc.nist.gov/pubs/sp/800/53/r5/upd1/final)

The reference-document archive requested during this workflow is itself part of provenance. Publicly downloadable official documents will be stored with their original URL and SHA-256. Paywalled standards and official web pages will be indexed by authoritative landing URL rather than copied without redistribution authority.

### Scalability and Reliability Patterns

Syscalls are the high-volume stream. They must be edge-batched into bounded segments, compressed where validated, written under append-only object keys, and accompanied by queue-depth, drop-count, and normalization-lag metrics. Capture loss invalidates or flags affected windows; it is not silently interpreted as normal behavior.

Consensus remains limited to one bounded physical observation per sensor/edge/round. Truth and large provenance objects are referenced by identifier/hash rather than embedded in consensus. OPC UA nodes are subscribed/read in batches, and slow storage or analytics I/O is decoupled from acquisition and control through bounded queues.

Model workers load an exact deployment bundle once, process only matching feature schemas, and record latency, memory, throughput, missingness, and failure status. Batch sizes, queue sizes, retention duration, syscall-drop tolerance, and resource limits are measured engineering decisions rather than literature-derived constants.

### Incremental Migration Pattern

The migration follows a strangler-style replacement: introduce versioned seams, run legacy and corrected paths in parallel, verify evidence, and retire old paths only after documented parity or intentional non-equivalence. [Strangler Fig Application, Martin Fowler](https://martinfowler.com/bliki/StranglerFigApplication.html)

1. Freeze and hash the current physical autoencoder, supervised ADFA/LID runs, payloads, model schemas, thresholds, and consensus/OPC/artifact contracts as `legacy-baseline`.
2. Introduce a parameter/provenance registry and source-document archive without changing behavior. Unsupported constants become quarantined legacy values, not approved parameters.
3. Introduce `SignalObservation.v2` and compute current, normalized current, engineering derivation, and quality in shadow. Verify v1 projections.
4. Dual-publish v1/v2 physical observations and add the separate syscall topic/capture path. Preserve strict v1 decoding.
5. Add consensus v2 in shadow, with versioned Python/Go state and golden cross-language tests. Do not rewrite existing CometBFT state in place.
6. Replace circular SCADA projection with an independent OPC UA writer/client path, initially in shadow.
7. Activate `ExperimentSpec`, the automatic 25%-75% reference schedule, independent truth logging, and complete evidence manifests.
8. Build a new current-domain physical feature schema, calibrate thresholds on normal validation data, and train LSTM/GRU/baseline candidates. Never load a v1 model against v2 features.
9. Correct ADFA and LID adapters, add actual Linux syscall capture and normal-only runtime HIDS, and add the version-specific HAI adapter.
10. Capture synchronized custom runs, freeze run-level splits before windowing, then enable late fusion and final paired ablations.
11. Extend the dashboard as a read-only view of signal basis, quality, provenance, detector/fusion outputs, and unlocked evaluation results.
12. Retire legacy paths only after archived replay and a documented migration decision.

### Architectural Trade-offs and Decisions

- Dual v1/v2 paths temporarily increase storage and implementation complexity but preserve rollback and scientifically auditable comparison.
- Carrying current, normalized current, and engineering value improves traceability but creates consistency risk; one immutable conversion factory and calibration-profile hash are mandatory.
- Strict truth isolation complicates evaluation joins but prevents label leakage and makes one-class claims defensible.
- Independent SCADA introduces timing, missing-data, and quality cases but removes the current circular validation.
- Late fusion requires detector-specific calibration and missing-modality policy but preserves separate physical and syscall evidence and enables valid ablation.
- A common artifact/evaluation contract is useful; a universal feature schema or raw-score scale across physical signals, syscalls, ADFA, LID, and HAI is scientifically invalid.
- Container/process zones on one host demonstrate logical separation but are not equivalent to physical industrial network segmentation or formal IEC 62443/IEC 61511 compliance.

_Overall architectural confidence:_ High for signal-boundary correction, truth isolation, dataset separation, independent SCADA, versioned migration, and provenance requirements. Medium for exact process decomposition, batching, resource limits, and fusion policy until implementation spikes and measured long-run evidence are available.

### Development Tools and Platforms

The project uses `uv` and `uv.lock` for Python dependency resolution. Official uv documentation confirms that project dependencies are declared in `pyproject.toml` and that lock/sync operations produce a reproducible environment when invoked with locked or frozen behavior. [uv dependency management](https://docs.astral.sh/uv/concepts/projects/dependencies/) [uv locking and syncing](https://docs.astral.sh/uv/concepts/projects/sync/)

Testing currently uses Python's standard-library `unittest`, with PowerShell and Python scripts for local orchestration, training, sweep execution, model promotion, and evidence generation. This is adequate for the prototype, but the revised plan needs schema-contract tests for instrument conversions, device fault regions, dataset-version loaders, edge syscall events, leakage prevention, and experiment-manifest reproducibility.

The existing LID-DS adapter is not compatible with the official 2021 representation: local code expects `normal/attack` directories and simplified `.sc2` rows, whereas the official loader represents training, validation, and test recording archives containing syscall, network, resource, result, and metadata files. The official LID schema includes timestamps, user/process/thread identity, syscall name, direction, and parameters. [LID-DS 2021 loader](https://github.com/LID-DS/LID-DS/blob/master/dataloader/data_loader_2021.py) [LID-DS syscall schema](https://github.com/LID-DS/LID-DS/blob/master/dataloader/syscall_2021.py)

For live edge evidence, ADFA numeric identifiers must not be replayed as if they were portable Linux calls. The recommended tool boundary is an allowlisted deterministic edge workload plus an actual Linux syscall capture sidecar, modeled after the official LID-DS Sysdig-and-Docker recording approach. [LID-DS recording framework](https://github.com/LID-DS/LID-DS/wiki/LID-DS-Recording-Framework%3A-Documentation-and-Installation)

_Build/environment tooling:_ uv, pyproject.toml, lockfile, Go modules.  
_Testing tooling:_ unittest plus new contract, leakage, and reproducibility suites.  
_Required platform capability:_ Linux-based syscall recording/replay harness; Windows remains suitable for orchestration but not as the evidentiary syscall source.  
_Confidence:_ High.

### Cloud Infrastructure and Deployment

The system is local-first. Python edge/orchestration processes communicate through an Eclipse Mosquitto 2 container; valid artifacts and models are written to a MinIO container; a digest-pinned three-validator CometBFT network communicates with three Go ABCI containers. Mosquitto officially implements MQTT 5.0, 3.1.1, and 3.1. [Mosquitto broker documentation](https://mosquitto.org/man/mosquitto-8.html) Docker Compose remains suitable for defining these local multi-container dependencies. [Docker Compose documentation](https://docs.docker.com/compose/)

No public-cloud service, Kubernetes cluster, serverless runtime, CDN, or data warehouse is justified for the master's prototype. A Linux container/VM is, however, required for authentic syscall capture. HAI and public HIDS datasets should be downloaded into a content-addressed dataset cache or mounted read-only, with redistribution constraints preserved.

Two reproducibility risks need correction before long-running experiments:

- `minio/minio:latest` is unpinned and the current local MinIO service has no persistent data volume; the attached autoencoder audit warns that its `.keras` model and associated metadata can be lost when the container is recreated.
- `eclipse-mosquitto:2` is only major-version pinned, while CometBFT is digest-pinned. Experimental infrastructure should use exact versions or digests and record them in every run manifest.

_Deployment model:_ local processes plus Docker Compose.  
_Edge capture extension:_ isolated Linux container or VM per capture profile.  
_Cloud posture:_ none required.  
_Confidence:_ High.

### Technology Adoption Trends

The evidence supports evolution of the current stack, not wholesale replacement:

1. Preserve Python/NumPy/Keras/Torch, MQTT, OPC UA, MinIO, and CometBFT boundaries.
2. Replace mixed-unit autoencoder tensors with a declared feature schema using normalized instrument-domain channels; preserve raw mA and engineering values outside that tensor for auditability and process semantics.
3. Keep RPM on 4–20 mA and bind its configured range to a cited real sensor profile.
4. Separate dataset ingestion from live event generation. ADFA-LD and LID-DS provide HIDS reference/evaluation semantics; live inputs must be syscalls actually emitted and captured on the edge workload.
5. Add HAI as a separate physical-process benchmark with a version-specific adapter and evaluation-only labels. Do not merge HAI process telemetry into syscall token space.
6. Treat the current supervised LSTM/GRU results as baselines. Add unsupervised or self-supervised normal-only sequence evaluation for the live edge path, with thresholds calibrated on held-out normal validation data.
7. Make every numerical configuration traceable as one of: standard/device value, value derived from a cited value, preregistered experimental factor, or measured/calibrated statistic. Unsupported production-like constants must be removed or explicitly labeled mock assumptions.

The current stack therefore remains viable, but its data contracts, provenance layer, dataset adapters, deployment pinning, and experimental protocol require major revision before implementation continues.

_Overall confidence:_ High for the stack inventory and compatibility findings. Medium for the final live syscall capture mechanism until a Linux capture spike compares Sysdig/eBPF/audit alternatives under the prototype's resource constraints.

## Integration Patterns Analysis

### Integration Boundary Model

The revised system needs two independent evidence planes and one restricted evaluation plane:

```text
Physical evidence plane
plant/process model
  -> transmitter profile
  -> raw electrical signal + quality classification
  -> edge acquisition
  -> normalized physical feature projection
  -> consensus / independent OPC UA comparison / physical detector

Host evidence plane
scenario controller command
  -> allowlisted edge workload
  -> actual Linux syscall capture
  -> syscall event normalization
  -> normal-only sequence detector

Restricted evaluation plane
scenario truth + frozen physical scores + frozen syscall scores
  -> per-modality evaluation
  -> late fusion on synchronized project runs only
  -> comparative and ablation reports
```

This separation corrects the statement that syscalls occur “between edges.” Syscalls occur inside each Linux edge process; MQTT/CometBFT messages occur between edges. ADFA-LD and LID-DS can guide syscall representation and benchmark evaluation, but they must not be executed as portable syscall scripts. HAI is a physical/SCADA time-series benchmark. None of the three public datasets was co-observed with this compressor prototype, so cross-modal fusion is valid only on a newly captured, synchronized project dataset.

### API Design Patterns

The prototype does not need GraphQL, an API gateway, a service mesh, or a new public REST platform. It already has appropriate narrow interfaces:

- typed Python contracts internally;
- JSON over MQTT for edge observations;
- CometBFT JSON-RPC and ABCI for consensus submission/commit;
- OPC UA for the logical SCADA boundary;
- an S3-compatible MinIO API for evidence artifacts;
- local HTTP/JSON endpoints for dashboard control and read models.

The required change is contract versioning, not protocol proliferation. Every cross-component JSON contract should be validated against a declared JSON Schema 2020-12 document and carry `schema_version`, `run_id`, source identity, event identity, source and observed time, and a provenance reference. [JSON Schema 2020-12](https://json-schema.org/draft/2020-12)

The current MQTT deserializer constructs dataclasses with strict field sets, so adding fields without explicit version routing would break compatibility. A `v2` envelope should initially coexist with the current payload. The live CometBFT path also strips observations to engineering `value` and `unit`; therefore changing only `RawHartPayload` would not change live consensus. The Python serializer, Go transaction/state schema, trust calculation, committed-state mapper, and downstream consumers must evolve together.

Proposed versioned API contracts:

1. `SignalObservation.v2` — raw electrical value, unclipped normalized value, engineering value/range/unit, signal quality, timestamps, device and profile provenance.
2. `SyscallEventBatch.v1` — bounded ordered events plus collector/kernel/container provenance and an immutable raw-capture hash.
3. `DetectorScore.v1` — detector/model/schema identity, window identity, raw score, score direction, calibrated score if applicable, threshold identity, decision, latency, and quality flags; no truth fields.
4. `ScenarioTruth.v1` — restricted interval/event ground truth emitted by the controller and inaccessible to detector credentials.
5. `FusionEvaluation.v1` — references frozen score objects and truth objects; it does not copy raw model inputs or average incomparable raw scores.

_RESTful/HTTP role:_ dashboard command/read interface only.  
_RPC role:_ CometBFT JSON-RPC and ABCI only.  
_GraphQL/gRPC/webhooks:_ no demonstrated need in the prototype.  
_Confidence:_ High.

### Communication Protocols

#### Instrument and HART-Inspired Acquisition

FieldComm documents HART as digital FSK communication superimposed on the traditional 4–20 mA analogue signal. [FieldComm HART application guide](https://www.fieldcommgroup.org/sites/default/files/imce_files/technology/documents/HART_ApplicationGuide_r7.1.pdf) The prototype does not implement a complete HART stack, and should describe its payload as `simulated-hart` or `hart-inspired` unless the implemented command/device-variable subset is verified against accessible specifications.

The transmitter adapter should be the only component that derives loop current from process physics. Edge acquisition should preserve the raw current, classify device/fault/under-range/over-range state before clipping, and then calculate normalized and engineering projections from one versioned scaling profile. Downstream components must not independently repeat conversion constants.

#### MQTT Edge Transport

The current real MQTT client publishes and subscribes without specifying QoS, so Paho's default QoS 0 applies. MQTT 5 defines QoS 0 as at-most-once, QoS 1 as at-least-once with possible duplicates, and QoS 2 as exactly-once for the MQTT delivery flow. [OASIS MQTT 5.0](https://docs.oasis-open.org/mqtt/mqtt/v5.0/mqtt-v5.0.html)

For consensus-relevant edge observations, the recommended prototype policy is MQTT 5 QoS 1 plus application-level identity, deduplication, and source sequence numbers. This choice favors observable delivery while acknowledging duplicate messages. Retained telemetry should be disabled. A stable consumer key such as `(source, event_id)` or `(edge_id, boot_id, source_seq)` prevents duplicate evidence from becoming duplicate observations.

Raw syscalls should not be broadcast one event at a time through the existing physical-observation topic. The edge-local collector should feed the local detector and immutable segment writer; MQTT may carry bounded batch envelopes or score/manifest notifications on a separate versioned topic. This protects the physical consensus path from high-rate host telemetry and preserves clear trust semantics.

#### OPC UA SCADA Boundary

The current fake SCADA is populated from the consensus result immediately before comparison, making the supposedly independent supervisory comparison circular. The corrected integration should use an independent pre-consensus plant/PLC snapshot written to the OPC UA server and read through an actual OPC UA client boundary. Consensus remains the candidate trusted state; SCADA remains an independent supervisory observation.

OPC UA `DataValue` associates a value with `StatusCode`, `sourceTimestamp`, and optionally `serverTimestamp`; the source timestamp is UTC and should remain unchanged when passed through servers. [OPC UA DataValue](https://reference.opcfoundation.org/Core/Part4/v105/docs/7.11) OPC UA Data Access also defines engineering-range/unit metadata for analogue items. [OPC UA AnalogItem semantics](https://reference.opcfoundation.org/specs/OPC-10000-8/5.3.2)

The SCADA namespace should expose loop current and process value as separate analogue nodes and keep normalized ML features in a distinct research namespace. SCADA comparison should include quality/status and timestamps as well as the selected value representation.

#### Consensus and Object Storage

CometBFT/ABCI remains the physical-state trust path. [CometBFT ABCI specification](https://docs.cometbft.com/main/spec/abci/) Syscall detector output must not enter the sensor-value consensus calculation. It is parallel security evidence combined only at the evaluation/fusion layer.

MinIO remains the evidence backbone. Runs should use versioned immutable-style object keys and content hashes. MinIO versioning assigns unique version IDs to mutations and protects against unintended overwrites; object locking can add WORM retention where the deployed edition supports it. [MinIO versioning](https://docs.min.io/aistor/administration/objects-and-versioning/versioning/) [MinIO object locking](https://docs.min.io/aistor/administration/object-locking-and-immutability/)

_Confidence:_ High for protocol semantics and current-path gaps; medium for MQTT syscall batching until throughput is measured.

### Data Formats and Standards

#### Canonical Physical Observation

The minimum physical event should contain:

```text
schema_version, run_id, event_id, edge_id, device_id, signal_id
source_timestamp_utc, observed_timestamp_utc, monotonic_ns, source_seq
clock_sync_method, measured_clock_offset_or_uncertainty
raw_adc_counts?, raw_current_ma?, raw_voltage_v?
normalized_value_unclipped
engineering_value, engineering_unit, lrv, urv
signal_quality, quality_reason
scaling_profile_id, simulation_profile_id?, provenance_manifest_id
```

The physical autoencoder receives only a frozen `feature_schema` projection, normally normalized electrical/diagnostic/temporal channels. Engineering values remain available for physical equations and operator displays. Raw measurements remain available for audit and reprocessing.

#### Canonical Syscall Event

The minimum syscall event should contain source/observed/monotonic time where available; node, boot, container, process and thread identity; syscall name and direction; ABI-bound raw number only when present; return value and sanitized typed arguments; collector/version; source sequence; and raw-capture hash. Syscall numbers remain categorical identifiers and must never be scaled as continuous magnitudes.

ADFA-LD can provide ordered positions but no authentic event timestamps or process/thread fields; missing fields must remain null rather than fabricated. LID-DS fields can map directly from its official record schema. HAI maps to the physical event family and must preserve its dataset-native units or controller counts.

#### Event Envelope and Time

CloudEvents 1.0.2 defines reusable envelope semantics including `specversion`, `type`, `source`, `id`, `time`, and `dataschema`, and requires uniqueness of `source` plus `id`. The project can adopt those envelope semantics without claiming that CloudEvents defines its payload. [CloudEvents 1.0.2](https://github.com/cloudevents/spec/blob/v1.0.2/cloudevents/spec.md)

OpenTelemetry's log data model distinguishes occurrence `Timestamp` from collection `ObservedTimestamp`, a useful precedent for edge and dataset events. [OpenTelemetry log data model](https://opentelemetry.io/docs/specs/otel/logs/data-model/) JSON UTC times should use RFC 3339; within each node, a monotonic clock and source sequence provide ordering even if wall time is corrected. [RFC 3339](https://datatracker.ietf.org/doc/html/rfc3339) Distributed hosts should record NTPv4 synchronization state, offset/delay/dispersion information, and actual observed uncertainty rather than assert a universal skew tolerance. [RFC 5905](https://www.rfc-editor.org/info/rfc5905/)

Half-open causal windows `[start, end)` should be used as a project contract to avoid double-membership at boundaries. Any allowed cross-node skew is a measured and preregistered experimental parameter, not a value copied from NTP documentation.

_Data serialization:_ schema-validated JSON for contracts and manifests; dataset-native CSV/text/syscall archives retained unchanged; NPZ/Keras used only for derived training/model artifacts.  
_Confidence:_ High.

### System Interoperability Approaches

The system should use explicit adapters and projections instead of a universal record that forces all modalities together:

- `TransmitterProfileAdapter`: process state to electrical signal and quality.
- `PhysicalFeatureProjector`: versioned physical observation to normalized model tensor.
- `ADFASequenceAdapter`: numeric categorical sequence plus official split/provenance; no fake time.
- `LIDRecordingAdapter`: official archive/record schema to canonical syscall events; labels moved to truth storage.
- `HAIVersionAdapter`: version-specific CSV/tag schema to canonical physical samples; labels stored separately.
- `RuntimeSyscallNormalizer`: collector-native event to canonical syscall event.
- `ScoreCalibrator`: detector-specific validation transform; fit only on the declared validation partition.
- `LateFusionEvaluator`: join frozen physical/syscall scores with restricted truth only for synchronized project runs.

HAI timestamps are published without an explicit UTC offset and should remain dataset-local/naive until a timezone is authoritatively documented. HAI replay needs two times: the original dataset time and the synthetic replay time. Labels are kept in an evaluation sidecar keyed by dataset version, file, and validated row/timestamp alignment.

The current persisted artifact can become internally inconsistent because it replaces one selected edge's PV with an averaged consensus PV while retaining that edge's current, percent range, and diagnostics. The v2 persistence contract must either store all source observations plus an explicitly recomputed canonical aggregate, or preserve the consensus scalar separately without implying its accompanying current came from the same aggregate.

_Point-to-point integrations:_ retained only at clearly named boundaries.  
_API gateway/service mesh/ESB:_ unnecessary for a single-host academic prototype.  
_Interoperability mechanism:_ versioned adapters, schemas, manifests, and immutable source references.  
_Confidence:_ High.

### Microservices and Event-Driven Integration

MQTT publish/subscribe remains the event-driven physical observation bus, but the broker is transport only and never a trust authority. CometBFT commit remains the authoritative valid-state transition. MinIO artifacts form the durable experimental record, not an event-sourced reconstruction of the whole runtime.

The dashboard is a downstream read model. It may display physical, syscall, fusion, provenance, clock-quality, and truth-unlocked evaluation views, but it must not calculate detector scores or secretly change experiment inputs. The requested automatic compressor excitation belongs to a versioned experiment/scenario controller, not UI-only behavior.

No distributed Saga or transaction coordinator is required. Atomicity is expressed through immutable artifact references and a run manifest that is finalized only after required artifacts are present. Missing artifacts remain visible quality failures rather than being silently substituted.

_Publish-subscribe:_ MQTT for edge observations and bounded notifications.  
_Command path:_ scenario controller to allowlisted workload/physical excitation.  
_State transition:_ CometBFT for physical consensus only.  
_Durable evidence:_ MinIO plus manifests and hashes.  
_Read model:_ dashboard.  
_Confidence:_ High.

### Label Isolation, Fusion, and Evaluation Integration

“Unlabelled” must mean that labels are absent from detector features, training targets, serving topics, and model-accessible storage. It must not mean deleting evaluation ground truth. The scenario controller writes a separate restricted truth object. Detector identities can write scores but cannot read truth. Models, preprocessing parameters, thresholds, feature schemas, and output scores are frozen and hashed before the evaluator joins them to truth.

Public-dataset roles:

- ADFA-LD: syscall-sequence benchmark for the syscall branch.
- LID-DS 2021: richer syscall/event benchmark and recording-schema reference for the syscall branch.
- HAI: physical time-series benchmark for the physical branch.
- New synchronized project capture: the only dataset that supports physical-only versus syscall-only versus combined-detector ablation for this compressor/edge system.

The phrase “four datasets” should therefore be corrected in the planning artifacts. An autoencoder is a model, not a dataset. The fourth evidentiary source is the new synchronized custom runtime dataset containing physical observations, per-edge syscall events, controller/workload records, and restricted ground truth.

Late fusion must operate on calibrated detector outputs, never raw ADFA/LID/HAI/autoencoder loss values. Preregistered simple rules can include OR, AND, maximum, or unweighted mean of calibrated scores. Any learned fusion weight is a supervised model and must be fit only on a separate validation set. Fair ablation uses the same held-out project runs/windows for physical-only, syscall-only, and fusion conditions.

_Confidence:_ High for modality separation and leakage controls; medium for the final fusion rule until validation evidence exists.

### Integration Security Patterns

The current Mosquitto configuration uses `allow_anonymous true` on a plaintext listener. This is acceptable only as an explicitly isolated single-host demonstration profile. Mosquitto officially supports password/ACL, certificate-based TLS, and client-certificate authentication. [Mosquitto configuration manual](https://mosquitto.org/man/mosquitto-conf-5.html)

Security work should be proportional to the thesis scope:

- bind unauthenticated demo services to the isolated local environment;
- use separate credentials/prefix permissions for detector scores and restricted truth;
- hash source datasets, capture segments, manifests, models, preprocessing objects, thresholds, and reports;
- use TLS and authenticated identities if traffic leaves the isolated host;
- record security mode in the experiment manifest;
- never expose truth fields in MQTT feature topics or detector-accessible MinIO prefixes.

OPC UA supports secure policies such as Basic256Sha256 and AES-based policies; older Basic128Rsa15 and Basic256 policies are marked deprecated in current profiles. [OPC UA security policies](https://reference.opcfoundation.org/specs/OPC-30001/5.3.2) The current fake SCADA may retain a no-security demonstration endpoint only if that limitation is explicit and the endpoint is local/read-only.

_OAuth/JWT/API gateway:_ not justified for this local prototype.  
_Primary controls:_ isolation, least-privilege object prefixes, contract validation, hashes, version pinning, and optional TLS/certificates.  
_Confidence:_ High.

## Implementation Approaches and Technology Adoption

### Technology Adoption Strategies

The implementation will use gradual, evidence-gated adoption rather than a big-bang rewrite. Every affected runtime path advances through `legacy -> shadow -> active`:

- `legacy` preserves the present behavior as a named historical baseline;
- `shadow` produces versioned evidence without controlling the v1 decision path;
- `active` is allowed only after contract, semantic, integration, replay, and rollback gates pass.

Rollback changes a reader or decision flag; it never deletes or rewrites v2 artifacts, source captures, CometBFT state, model bundles, or evaluation records. Changing an active scientific configuration during a formal run closes that run as `aborted` and starts a new `experiment_id`.

All numeric values use one mandatory provenance class:

| Class | Meaning | Correct use |
|---|---|---|
| `direct` | Copied from a cited standard, manual, or primary source | Signal range, device accuracy, documented fault band |
| `derived` | Deterministically calculated from cited inputs | `20 mA - 4 mA = 16 mA`; `4 + 16 * 0.25 = 8 mA` |
| `measured` | Obtained from a documented pilot/calibration procedure | Observed noise, capture overhead, settling behavior |
| `preregistered_factor` | Frozen research-design choice | Schedule, seed, dwell policy, repetitions, false-alarm budget |
| `mock` | Explicitly synthetic value or behavior | Simulator workload/state with generator and seed provenance |

A new configuration cannot start if a numeric field lacks provenance type, reference, units, and—where applicable—source locator or derivation. A citation does not make every value in a document applicable to this compressor; the parameter-evidence register must identify the exact page, section, table, equation, or project decision.

The official/primary reference archive is stored under `docs/reference-archive/`. Public verification copies have SHA-256 checksums; access-controlled IEC/ISA/NAMUR material is represented by official landing pages and licensing notes rather than unauthorized copies. NIST's Research Data Framework supports explicit version identification, provenance, and preservation of raw and derived research data. [NIST SP 1500-18 Rev. 2, RDaF 2.0](https://www.nist.gov/publications/nist-research-data-framework-rdaf-version-20)

### Development Workflows and Tooling

The repository remains Python/Go with Docker Compose. No cloud platform, database, API gateway, service mesh, or third language is introduced without an implementation spike showing a concrete need.

Python work uses the checked-in `uv.lock` and locked/frozen execution. Official uv documentation states that `--locked` fails when the lockfile is not current and `--frozen` uses the lockfile without re-resolving it. [uv locking and syncing](https://docs.astral.sh/uv/concepts/projects/sync/) Experimental manifests record Python, dependency, Torch/Keras, OS, kernel, and architecture versions.

Container images are pinned by digest. Docker documents that tags are mutable and that a digest provides reproducible image identity. [Docker build best practices](https://docs.docker.com/build/building/best-practices/) OCI descriptors define content digest and byte size and recommend verifying retrieved content. [OCI Image Specification v1.1.1](https://github.com/opencontainers/image-spec/blob/v1.1.1/descriptor.md)

Every wire and artifact contract gets an explicit JSON Schema 2020-12 `$schema`, stable `$id`, `schema_name`, and `schema_version`, plus semantic invariant tests for rules that structural validation cannot express. [JSON Schema 2020-12](https://json-schema.org/draft/2020-12)

The first implementation artifacts are golden v1 fixtures for MQTT observations, Python/Go consensus transactions and queries, OPC UA states, persisted evidence, feature schemas, thresholds, and model promotion records. New v2 contracts and fixtures live alongside them. Scientific rules move out of `scripts/run_local_demo.py` and UI callbacks into typed experiment, profile, detector-bundle, and evaluation contracts.

### Testing and Quality Assurance

Testing is layered by scientific failure mode:

1. **Source and profile tests** — every adopted device field resolves to the source register and parameter-evidence entry.
2. **Signal invariants** — cited 4, 12, and 20 mA endpoints; current-to-normalized-to-engineering round trips; quality classification before clipping; no loss of under-range, over-range, fault, or raw ADC/current evidence. Rockwell documents 4/12/20 mA as 0/50/100% for its example scaling. [Rockwell PointMax manual](https://literature.rockwellautomation.com/idc/groups/literature/documents/um/5034-um003_-en-p.pdf)
3. **Contract tests** — strict version routing, valid/invalid JSON fixtures, MQTT deduplication and gap detection, artifact schema hashes, and tolerant read-only dashboard projections.
4. **Consensus parity** — shared golden inputs produce identical deterministic Python and Go trust, exclusion, and committed-state results; restart/query/AppHash compatibility is exercised.
5. **SCADA independence** — changing consensus cannot mutate the OPC UA source observation; changing the independent source cannot mutate consensus; DataValue quality and timestamps survive the client/server boundary.
6. **Leakage tests** — truth, scenario label, attack label, and future interval fields are structurally absent from training and inference contracts. Preprocessing is fit on training data only; scikit-learn identifies fitting preprocessing on test data as leakage. [scikit-learn common pitfalls](https://scikit-learn.org/stable/common_pitfalls.html)
7. **Split/window tests** — split complete traces/runs/scenarios before windowing; a window cannot cross run, edge, boot, process/session, or official dataset partition.
8. **Model-bundle tests** — inference fails closed on feature-order/hash, scaler, vocabulary, profile, threshold, runtime, or model mismatch; the same frozen input replay produces the same scores within the declared environment.
9. **Syscall-capture quality** — event identity, ordering, session boundaries, collector provenance, queue state, and drop counters are persisted. Kernel capture can drop events when buffers fill, and affected metadata-dependent detection may become unreliable. [Falco dropped-event documentation](https://falco.org/docs/concepts/event-sources/kernel/dropped-events/)
10. **Experiment reconstruction** — raw evidence and manifests recreate normalized data, windows, detector scores, evaluation joins, and the final matrix without hidden state.

PyTorch explicitly warns that complete reproducibility is not guaranteed across releases and platforms and that deterministic operations can reduce performance. The project therefore records both the reproducibility configuration and its measured cost rather than promising universal bitwise identity. [PyTorch reproducibility](https://docs.pytorch.org/docs/stable/notes/randomness)

### Syscall Workload and Capture Implementation

The phrase "mocked syscalls" is replaced with **controlled/mock workload producing real Linux syscalls**.

Current Mosquitto, MinIO, CometBFT, and ABCI containers produce real syscalls, but they are infrastructure roles and cannot substitute for the edge workload. The current edge/orchestrator processes run locally; final ADFA/LID-comparable evidence requires identifiable Linux edge workloads in containers or a dedicated Linux VM/host.

```text
scenario controller
  -> allowlisted Linux edge workload
    -> real kernel syscalls
      -> Sysdig/eBPF raw capture and immutable segment
        -> canonical categorical events/windows
          -> normal-only syscall detector

restricted scenario truth ---------------------------------> evaluator only
```

Containers are isolated processes that share the Linux kernel. [Docker container concept](https://docs.docker.com/get-started/docker-concepts/the-basics/what-is-a-container/) On Windows, Docker Desktop runs Linux containers in a Linux VM, so the capture boundary is that VM rather than the Windows host. [Docker Desktop container security](https://docs.docker.com/security/faqs/containers/)

The official LID-DS recording framework is a direct methodological precedent: it requires Docker and Sysdig, builds scenario images, and records scenario executions. [LID-DS recording framework](https://github.com/LID-DS/LID-DS/wiki/LID-DS-Recording-Framework%3A-Documentation-and-Installation) Its example warm-up and recording durations are examples, not project constants. Sysdig supports container-aware system-event capture and durable trace files. [Official Sysdig repository](https://github.com/draios/sysdig)

Two modes remain strictly separated:

- `fixture-replay`: small recorded/synthetic canonical events for schema, MQTT, windowing, and detector tests only; excluded from experimental claims;
- `host-capture`: real syscalls emitted by controlled Linux edge workloads and captured at the kernel boundary; eligible for the custom experimental dataset.

The workload is mocked, not the calls. Normal behavior includes edge acquisition, serialization, MQTT exchange, consensus interaction, and evidence writes. Controlled safe deviations may change approved retry, connection, file-access, process, or timing behavior. The scenario controller records truth separately. It does not intercept, renumber, or modify Linux syscalls.

ADFA-LD remains an offline ordered-sequence benchmark because it lacks authentic timestamp/process/thread/argument/workload information. LID-DS remains an offline richer benchmark and capture-schema/scenario-method reference. Neither dataset's syscall numbers are executed as portable calls. Runtime events are categorical syscall names/directions plus documented, sanitized metadata; raw numeric IDs are retained only with ABI/kernel context and are never divided by a maximum or interpreted as continuous distance.

Before adopting the final collector, a Linux capture spike must containerize one edge, exercise its normal workload, capture/filter by container and process, measure drops and overhead, and validate raw-to-canonical replay. If Docker Desktop/WSL2 kernel instrumentation is not sufficiently reliable, the final campaign moves to a pinned dedicated Linux VM/host. Collector choice, buffer/batch policy, and loss tolerance remain measured/preregistered decisions.

### Deployment and Operations Practices

Compose gains explicit versioned profiles and health checks. `minio/minio:latest` and the major-only Mosquitto tag are replaced by verified immutable image references for formal experiments. MinIO receives persistent storage before new model training; every campaign performs a clean restoration test.

Artifact namespaces are append-only by run/stream/segment rather than repeatedly overwriting growing objects. MinIO versioning preserves full object versions and can consume substantial storage for mutation-heavy objects, so immutable chunk keys are preferred. [MinIO versioning](https://min.io/docs/minio/kubernetes/upstream/administration/object-management/object-versioning.html) Object Lock/WORM may be used for finalized evidence where supported and appropriately configured. [MinIO Object Lock](https://min.io/docs/minio/windows/administration/object-management/object-retention.html)

The controller remains available if MQTT, OPC UA, MinIO, or analytics fails. Acquisition uses bounded queues and records missingness/backpressure; detector or storage failure never creates an actuator command. The automatic 25%-75% excitation is a versioned experiment-controller state machine with `PRECHECK`, `ARMED`, `RAMP`, `SETTLE`, `HOLD`, `NEXT_SETPOINT`, `COMPLETE`, and `ABORT` states. Ramp and safety limits come from the selected device profile; settling is measured; dwell/sequence/duration are preregistered. Analytics has no write credential to the control namespace.

Every formal campaign freezes code, dependency and container hashes, transmitter profiles, experiment specification, input trace/seeds, model bundle, threshold, data splits, and evaluation policy. It records observed sequence gaps/duplicates, synchronization evidence, quality codes, bytes/capacity, collector drops, queue depth, inference latency/memory, restarts, profile/config changes, and closed-segment hashes.

NIST SP 1339 recommends integrating OT backups with change management, creating backups regularly, testing them, and exercising recovery. [NIST SP 1339](https://csrc.nist.gov/pubs/sp/1339/final) An interrupted or internally inconsistent campaign ends as `aborted`, never as a partial successful experiment.

### Team Organization and Skills

The prototype does not require a large operations organization, but it requires separation of responsibilities even when one researcher performs them at different checkpoints:

- **experiment designer** preregisters profiles, factors, splits, metrics, and acceptance policy;
- **implementer** changes contracts, adapters, collectors, models, and orchestration without final-test truth access;
- **reviewer/promoter** verifies source locators, tests, bundles, and readiness before changing a mutable runtime alias;
- **truth writer** records append-only scenario intervals without reading live detector output;
- **evaluator** gains truth access only after model, preprocessing, threshold, fusion policy, and score hashes are frozen.

Required skills are industrial 4-20 mA scaling and quality, OPC UA information modeling, Python/Keras/Torch sequence modeling, Go/CometBFT deterministic state, Linux container/syscall capture, data leakage prevention, temporal/event evaluation, and reproducible research-data management. NIST AI RMF emphasizes documented test sets, metrics, tools, uncertainty, benchmark comparisons, and deployment-like evaluation. [NIST AI RMF](https://airc.nist.gov/)

### Cost Optimization and Resource Management

The system remains local-first. Cost control is achieved by avoiding unjustified cloud infrastructure and by measuring before provisioning:

- measure syscall/event and physical-sample production rates in a pilot;
- derive storage capacity from measured rate and preregistered campaign duration;
- keep high-volume raw syscall capture local/MinIO and publish bounded score/manifest events;
- compress and chunk raw segments only after verifying replay and throughput/latency trade-offs;
- retain public datasets outside Git and identify them by checksum/version/license;
- use one immutable model bundle per candidate and content-addressed derived artifacts rather than silent copies;
- report deterministic-mode performance cost rather than enabling it without measurement;
- add classical-model dependencies only after Python 3.14 compatibility is verified, or isolate them in a pinned runner.

Retention duration, chunk size, queue size, batch size, allowed drop rate, and hardware budget are not imported from literature. They are measured or preregistered and included in the final limitations.

### Risk Assessment and Mitigation

| Risk | Mitigation and evidence gate |
|---|---|
| Current autoencoder is dominated by mixed physical scales and conflicting training profiles | Preserve as legacy; create current-domain schema v2; never load v1 weights against v2 features |
| Anonymous simulator/consensus/threshold constants | Parameter registry and startup provenance gate; quarantine old values |
| Current circular SCADA validation | Independent pre-consensus OPC UA writer and real client; independence tests |
| Averaged PV combined with one edge's current/diagnostics | Persist aggregate and per-edge observations separately with coherent provenance |
| Python/Go consensus divergence | Shared golden fixtures and deterministic parity tests before activation |
| Label leakage | Separate schemas, credentials, prefixes, processes, and dependency tests; freeze outputs before truth join |
| ADFA numeric IDs treated as continuous/replayed | Categorical representation; offline-only benchmark; no executable replay |
| LID adapter incompatible with official layout | Versioned official-schema adapter in isolated Linux environment |
| HAI version/layout/license ambiguity | Version-specific adapter, source hash/commit, preserved license caveat, exclude invalid/unknown version |
| Syscall collector loss or Docker Desktop incompatibility | Capture spike, drop/overhead metrics, dedicated Linux host fallback, quality flags |
| Threshold overfit or runtime recomputation | Frozen threshold artifact calibrated on declared validation data; full sensitivity/PR curve |
| Mutable container/dependency/storage state | Digest/lockfile pinning, persistent MinIO, checksums, tested restoration |
| Common-mode simulator/reference failure | Describe software paths as logically separate correlated views unless physically independent |
| Fusion of incompatible raw scores/datasets | Detector-specific calibration; late fusion only on synchronized custom runs |
| Long-run interruption or mixed configuration | Append-only run state, resume identity checks, abort on mixed bundles/configuration |

## Technical Research Recommendations

### Implementation Roadmap

1. **Freeze v1 and establish source/provenance gates.** Add v1 schemas, golden fixtures, immutable legacy model/run hashes, and the reference/parameter catalogs.
2. **Implement current-domain `SignalObservation.v2`.** Add source-backed instrument profiles; preserve raw current, normalized current, engineering derivation, quality, and timestamps through edge/MQTT state in dual mode.
3. **Implement experiment control and isolated truth.** Add `ExperimentSpec`, automatic 25%-75% reference schedule, correlation IDs, raw evidence for all cycles, and restricted truth storage.
4. **Implement physical consensus v2 atomically in Python and Go.** Add versioned transaction/query/state, current-domain basis, quality/profile requirements, and cross-language golden tests.
5. **Replace circular SCADA with an independent OPC UA path.** Run shadow comparison before cutover.
6. **Create the immutable physical-detector bundle.** Build current-domain LSTM-AE, GRU-AE and baselines; freeze preprocessing/schema/calibration/threshold; prohibit runtime fitting.
7. **Containerize one edge and validate real syscall capture.** Decide Sysdig/eBPF/host boundary from measured drops, overhead, attribution, and replay.
8. **Implement the syscall runtime and correct ADFA/LID adapters.** Separate topics/contracts, categorical events, group-first splits, label isolation, normal-only training, and historical supervised baseline retention.
9. **Add the version-specific HAI physical benchmark.** Preserve dataset-native units/splits/labels and provenance.
10. **Capture synchronized custom runs and activate late-fusion evaluation.** Freeze score calibrations/policy before truth unlock and perform paired ablation.
11. **Run long campaigns and build the final matrix.** Validate manifests, restoration, replay, missingness, resource measurements, confidence intervals, and limitations.
12. **Retire legacy paths only after archival replay and documented non-equivalence/equivalence decisions.**

### Technology Stack Recommendations

- Retain Python 3.14, NumPy, Keras 3 with Torch backend, asyncua, Paho MQTT, MinIO SDK, Go 1.24, CometBFT, Docker Compose, uv, and unittest.
- Add versioned JSON schemas, typed experiment/signal/syscall/detector/evaluation contracts, source-backed instrument profiles, and immutable bundle/manifests.
- Use an isolated Linux container/VM for official LID parsing and edge syscall capture; keep the main Python 3.14 runtime free of the legacy LID dependency stack.
- Add classical ML tooling only after compatibility verification; otherwise run it in a pinned offline environment.
- Do not add a cloud platform, Kubernetes, relational database, API gateway, service mesh, or general-purpose observability platform without measured necessity.

### Skill Development Requirements

- industrial signal acquisition, 4-20 mA quality/fault interpretation, uncertainty, and calibration-profile documentation;
- OPC UA DataValue, StatusCode, timestamps, AnalogItem ranges/units, client/server independence, and security modes;
- deterministic Python/Go contract evolution and CometBFT state compatibility;
- Linux namespaces, containers, tracepoints, Sysdig/eBPF capture, cgroup/container attribution, and loss accounting;
- categorical sequence modeling, normal-only novelty detection, threshold calibration, temporal splits, and event/range metrics;
- dataset licensing/versioning, provenance, immutable artifacts, backup/restoration, and preregistered experiment design.

### Success Metrics and KPIs

Success is measured without introducing universal numeric gates:

- executable-parameter provenance coverage by class and exact source/decision locator;
- verified source-document and artifact checksum completeness;
- v1/v2 contract replay status and explicit intentional differences;
- Python/Go consensus parity and deterministic restart/query results;
- signal round-trip/quality coverage and absence of silent clipping;
- SCADA independence and timestamp/quality join validity;
- truth/label leakage test results and split/window boundary integrity;
- model-bundle completeness, schema compatibility, frozen-threshold provenance, and reproducible replay;
- syscall capture availability, event/drop/duplicate rate, attribution, overhead, backlog and storage throughput;
- per-detector PR-AUC, event/range recall, false alarms per operating hour, time to detection, calibration sensitivity, parameter count, training/inference time and memory;
- paired physical-only, syscall-only, and fusion ablation on identical held-out custom runs;
- run completeness, missingness, scenario coverage, restart behavior, backup/restoration success, and matrix reconstruction from immutable artifacts;
- confidence intervals across independent runs and explicit limitations for dataset, host, device profile, simulator/mock behavior, and deployment generalization.

Thresholds, permitted loss, run duration, repetitions, promotion criteria, and operational budgets must be preregistered or derived from pilot measurements. The research sources define methods and constraints; they do not supply universally valid project values.

## Research Synthesis and Technical Conclusion

### Executive Summary

The current prototype is useful as a legacy demonstrator but is not yet suitable as final academic evidence. Its physical simulator, divergence calculation, SCADA tolerances, fault injections, autoencoder adequacy gates, training profile, and anomaly threshold contain project-selected values without adequate provenance. The existing autoencoder also combines engineering values with incompatible scales and uses runtime threshold behavior that is not frozen as an experimental artifact. The existing ADFA-LD and LID-DS paths are labelled offline classifiers rather than evidence derived from edge workloads, the LID adapter does not implement the official 2021 layout, and HAI has not yet been implemented.

The corrected study does not attempt to find a publication containing every desired number. Instead, it establishes a scientific governance rule: a number may enter an executable experiment only as a directly documented value, a transparent derivation from documented inputs, a measured calibration result, a preregistered experimental factor, or an explicitly labelled mock. Universal noise, window, threshold, fusion-weight, run-duration, and loss-tolerance values do not exist in the reviewed sources. These values must be measured or preregistered and subjected to sensitivity analysis.

The target system has two detection modalities:

1. **Physical instrumentation:** custom compressor observations whose primary edge evidence is raw 4-20 mA, together with quality and calibration provenance. Normalized current is a deterministic representation of the same physical modality, not a separate modality. Engineering values remain derived representations used by the process model, SCADA, and interpretation.
2. **Linux host syscalls:** real kernel calls produced by controlled, allowlisted edge workloads and captured on a pinned Linux environment. The workload is controlled or mocked; the syscalls themselves are not modified or fabricated.

ADFA-LD and LID-DS are external syscall benchmarks. HAI is an external physical/SCADA benchmark. The custom synchronized project dataset is a fourth evidence source, not an "autoencoder dataset"; the autoencoder is a model family applied separately to HAI and custom physical data. Only the custom dataset observes physical signals and syscalls in the same executions and can therefore support fusion claims.

### Consolidated Decision Record

| Concern | Final technical decision | Evidence boundary |
|---|---|---|
| Instrument signal | Preserve raw mA at edge; derive normalized span and engineering value once through a cited profile | Rockwell and NI scaling guidance; selected device manuals |
| RPM output | Retain 4-20 mA using a cited programmable shaft-speed transmitter profile | Electro-Sensors FB420 official material |
| Simulator constants | Quarantine anonymous legacy values; replace through the parameter-evidence gate | Direct, derived, measured, preregistered factor, or mock only |
| 25%-75% variation | Name it speed/capacity reference, not electrical power; treat bounds as a preregistered experimental factor | Device safety/profile limits still apply; no universal range claim |
| Divergence | Evaluate same-profile redundant signals in current domain; use dimensionless, uncertainty-aware residuals where profiles differ | No transfer of legacy 20/3/600 or 0.35/0.75 without evidence |
| SCADA | Use an independent pre-consensus OPC UA source and a real client read | Retain DataValue status and source/server timestamps |
| Physical detector | Compare LSTM-AE and GRU-AE with simpler baselines using frozen bundles and validation-only thresholds | No claim of recurrent superiority before results |
| Syscall capture | Containerize or isolate Linux edge workload and capture actual kernel events | LID-DS Docker + Sysdig method is precedent, not a source of project timing constants |
| ADFA-LD | Preserve official trace roles, six attack families, categorical semantics, and local archive hash discrepancy | Offline benchmark only; no syscall-ID execution or fake timestamps |
| LID-DS | Implement the official scenario/recording schema in an isolated compatible environment | Labels and exploit metadata remain evaluation-only |
| HAI | Pin one release and use its native, version-specific physical/SCADA schema | Do not mass-convert HAI tags to mA or merge its labels into features |
| Fusion | Fuse frozen calibrated detector outputs only on synchronized custom runs | Never concatenate ADFA/LID syscall records with HAI physical rows |

### HAI and Custom-Prototype Data Roles

The recommended initial HAI target is HAI 23.05, pinned by repository commit and file checksums. Its official repository describes four physical/HIL processes, continuous SCADA time-series files, four normal training datasets totaling 249 hours, and two test datasets totaling 79 hours with 52 attacks. Its current repository packaging includes version-specific label files; the adapter must validate the actual release layout instead of assuming one schema for every HAI version. [Official HAI repository](https://github.com/icsdataset/hai) [HAI 23.05 directory](https://github.com/icsdataset/hai/tree/master/hai-23.05)

HAI remains in its published representation, which includes engineering values, states, and PLC-style counts. A separate HAI model bundle is trained on its official normal data, calibrated on a declared normal temporal validation partition, and evaluated against its official test truth only after inference. The project-generated compressor data does not become HAI and is not appended to HAI files.

The project-generated evidence becomes a separately named, versioned dataset such as `PTFP-Custom-v1`. Its physical branch contains raw current, normalized span, derived engineering values, signal quality, device/profile identity, timestamps, per-edge observations, consensus results, independent SCADA observations, and detector outputs. Its host branch contains captured syscall events, collector and kernel identity, ordering, loss counters, and immutable raw-segment references. Restricted scenario truth is joined only during evaluation. This custom dataset is the primary dissertation evidence for paired physical-only, syscall-only, and combined detection.

### Model and Evaluation Strategy

LSTM and GRU are scientifically justified as sequence-model candidates because their gated recurrent structures address temporal dependencies, but the reviewed primary literature does not establish a universal winner. [LSTM original paper](https://doi.org/10.1162/neco.1997.9.8.1735) [GRU origin paper](https://aclanthology.org/D14-1179/) [Large empirical RNN comparison](https://proceedings.mlr.press/v37/jozefowicz15.html)

For physical streams, the candidate comparison includes LSTM-AE, GRU-AE, a simple persistence or robust statistical baseline, and at least one classical or convolutional alternative where the pinned runtime supports it. For syscall streams, numeric identifiers are categorical tokens rather than continuous magnitudes; candidates use embeddings and categorical sequence objectives, with a transparent n-gram or STIDE-style baseline. No syscall ID is divided by the dataset maximum and reconstructed with continuous MSE.

Training uses normal-only evidence and is therefore described as one-class or novelty detection. Preprocessing is fit only on the training partition. Thresholds are calibrated on declared validation evidence and frozen inside an immutable deployment bundle before test truth is unlocked. Evaluation reports raw score curves and sensitivity rather than hiding performance behind one selected cutoff.

The final reporting structure separates incompatible datasets while allowing comparable metrics:

| Evidence source | Modality | Principal comparison | Fusion eligible |
|---|---|---|---|
| ADFA-LD | Syscalls | recurrent categorical candidates vs transparent baseline | No |
| LID-DS 2021 | Syscalls | recurrent categorical candidates vs official-schema baselines | No |
| HAI 23.05 | Physical/SCADA | physical anomaly candidates and baselines | No custom-syscall fusion |
| PTFP-Custom-v1 | Physical | current-domain candidates and baselines | Yes |
| PTFP-Custom-v1 | Syscalls | captured-edge candidates and baseline | Yes |
| PTFP-Custom-v1 | Paired scores | preregistered late-fusion policies | Yes |

Reported outcomes include PR-AUC, event/range recall, false alarms per operating hour, time to detection, threshold sensitivity, model parameters, training/inference time, memory, modality availability, missingness, syscall drop/duplicate rates, and confidence intervals over independent runs. The HAI repository recommends eTaPR for time-series anomaly evaluation. [HAI performance-metric guidance](https://github.com/icsdataset/hai#performance-metric)

### Architecture, Security, and Operational Conclusion

The recommended architecture is a local modular testbed with one-way evidence flow from experiment control to acquisition, detection, immutable storage, and restricted evaluation. Truth, attack labels, and future intervals are structurally absent from model-facing contracts. Analytics has no authority to write compressor commands. This is consistent with the need to account for the reliability and safety characteristics of OT environments described by NIST SP 800-82 Rev. 3, which remains the final NIST OT guide while Revision 4 is still in draft. [NIST SP 800-82 Rev. 3](https://csrc.nist.gov/pubs/sp/800/82/r3/final)

Every formal experiment freezes code commit, dependency lock, container digest, instrument profiles, experiment specification, input trace or seed, dataset versions and hashes, data partitions, feature schema, model weights, preprocessing, calibration evidence, threshold, fusion policy, and evaluation code. MQTT duplicates, syscall capture drops, clock uncertainty, missing data, restarts, and configuration changes are evidence fields rather than silently discarded operational noise.

The migration proceeds `legacy -> shadow -> active`. Existing results remain archived as legacy baselines. New v2 contracts dual-run until signal preservation, Python/Go consensus parity, SCADA independence, label isolation, bundle reproducibility, capture quality, and artifact reconstruction pass their gates. A run containing mixed modes, unresolved artifacts, truth leakage, or unaccounted event loss is finalized as aborted rather than selectively reported.

### Priority Roadmap

1. Freeze and hash the current prototype, datasets, model behavior, and v1 contracts.
2. Complete the source catalog and parameter-evidence coverage gate.
3. Introduce `SignalObservation.v2` and cited instrument profiles in shadow mode.
4. Add experiment specifications, 25%-75% reference scheduling, correlation, and isolated truth.
5. Implement current-domain consensus v2 atomically in Python and Go.
6. Replace circular SCADA projection with an independent OPC UA writer/client path.
7. Create immutable physical-model bundles and compare LSTM-AE, GRU-AE, and baselines.
8. Containerize one edge and complete a Linux syscall-capture feasibility spike.
9. Implement the runtime syscall branch and correct ADFA-LD/LID-DS adapters.
10. Add the pinned, version-specific HAI adapter and physical benchmark runner.
11. Capture `PTFP-Custom-v1`, freeze paired splits, and evaluate late fusion.
12. Run long campaigns, reconstruct the complete matrix, and report limitations.

### Research Limitations and Open Decisions

- HAI repository text contains a CC BY-SA versus embedded CC BY metadata inconsistency; the conservative attribution/share-alike interpretation is retained pending owner clarification.
- The LID-DS software is GPL-3.0-or-later, but an independent recording-data redistribution license was not located; raw redistribution requires clarification.
- The official ADFA download endpoint was unavailable during verification; the local archive hash and empirical counts are recorded, including the paper/archive validation-count discrepancy.
- IEC, ISA, NAMUR, and some publisher documents are access-controlled. Their canonical landing pages are catalogued, while open manufacturer manuals supply implementable numeric profiles.
- A Docker Desktop/WSL2 capture path is not assumed reliable until measured. A pinned Linux VM or host is the fallback.
- The simulator remains a research mock, not a validated compressor digital twin. Its claims are limited to the declared instrument and workload profiles.
- No reviewed source supplies universal anomaly thresholds, sequence windows, run duration, repetitions, queue capacity, acceptable loss, or fusion weights.

### Source and Verification Method

Primary-source preference was enforced in this order: standards and government publications; manufacturer manuals; official dataset-owner repositories, papers, loaders, and technical manuals; original model papers; official software specifications and documentation. Repository behavior and constants were verified against the executable code. Critical sources and permitted local copies are indexed under `docs/reference-archive/` with hashes and access/licensing notes. Proprietary standards and raw datasets are referenced through metadata rather than silently redistributed.

NIST AI RMF's Measure function calls for documented test sets, metrics, tools, uncertainty, benchmark comparison, repeatable testing, evaluation, verification, and validation. This research operationalizes that guidance through immutable evidence, blinded truth, preregistered decisions, deployment-like long runs, and reconstruction of every reported result. [NIST AI RMF Measure](https://airc.nist.gov/airmf-resources/airmf/5-sec-core/)

### Final Technical Conclusion

The revised project is feasible without abandoning its existing Python, Go, MQTT, OPC UA, MinIO, CometBFT, Keras, and Torch foundations. Its academic validity depends less on adding new infrastructure than on correcting scientific boundaries: current-domain physical evidence, real captured edge syscalls, independent supervisory evidence, versioned external benchmarks, structurally isolated truth, immutable model and threshold bundles, and paired evaluation on the custom synchronized dataset.

The central dissertation claim must therefore be tested as an ablation, not assumed: whether a calibrated combination of physical anomaly evidence and edge-host syscall anomaly evidence improves detection quality or operational trade-offs over either modality alone. ADFA-LD, LID-DS, and HAI establish external benchmark context; `PTFP-Custom-v1` supplies the only defensible simultaneous evidence for that final comparison.
