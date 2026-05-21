# Runtime Artifacts and Evidence Report

This document explains the runtime artifacts produced by the current
`parallel-truth-fingerprint-prototype` implementation and how those artifacts
support the PUCRS master's prototype claim: a local, inspectable "Parallel
Physical Truth Source" pipeline for legacy industrial systems.

The repository already uses `docs/` for project documentation and source input
material, so this report is intentionally stored at:

`docs/runtime-artifacts-and-evidence-report.md`

## Inspection Basis

This report was written from the repository implementation and live runtime
evidence observed on 2026-05-07 while the dashboard/runtime was running.

Important source areas inspected:

- Runtime orchestration: `scripts/run_local_demo.py`
- Runtime configuration: `src/parallel_truth_fingerprint/config/runtime.py`
- Sensor simulation: `src/parallel_truth_fingerprint/sensor_simulation/`
- Edge acquisition and MQTT exchange: `src/parallel_truth_fingerprint/edge_nodes/`
- Consensus: `src/parallel_truth_fingerprint/consensus/` and `abci/consensus_app/`
- Fake SCADA and comparison: `src/parallel_truth_fingerprint/scada/`, `src/parallel_truth_fingerprint/comparison/`
- MinIO persistence: `src/parallel_truth_fingerprint/persistence/`
- Dataset/model/fingerprint logic: `src/parallel_truth_fingerprint/lstm_service/`
- Dashboard/operator views: `src/parallel_truth_fingerprint/dashboard/`
- Scenario control: `src/parallel_truth_fingerprint/scenario_control/`
- BMAD planning and implementation artifacts: `_bmad-output/planning-artifacts/`, `_bmad-output/implementation-artifacts/`

The live MinIO bucket inspected was:

`valid-consensus-artifacts`

Because the runtime was active during inspection, object counts were increasing
as new cycles completed. The concrete samples below are therefore evidence
snapshots, not fixed final totals.

## Executive Explanation

In simple terms, the prototype simulates one industrial compressor and three
physical sensor channels: temperature, pressure, and RPM. Each of the three edge
nodes is responsible for one local sensor. The edges acquire simulated
transmitter-like values, publish their local observations over MQTT, consume the
other edges' observations, and independently reconstruct a local replicated view
of the compressor state.

That replicated edge view is not trusted yet. The runtime submits the round to a
local CometBFT network backed by a Go ABCI consensus application. The ABCI
application evaluates the edge views, computes trust evidence, excludes
inconsistent or suspected Byzantine participants when needed, checks quorum, and
commits a valid state only when enough valid participants remain.

The committed consensus state becomes the physical-side truth source for the
cycle. The fake OPC UA SCADA service then projects a logical supervisory state,
and the comparison service checks only temperature, pressure, and RPM against
configured tolerances. If SCADA diverges, the cycle is deliberately blocked
before downstream persistence and fingerprint processing. If consensus succeeds
and SCADA matches, a valid consensus artifact is written to MinIO.

The LSTM fingerprint path then builds temporal datasets from MinIO artifacts that
are both consensused and training-eligible normal behavior. It writes dataset
manifests and compressed window archives, trains a reusable LSTM autoencoder
when the configured runtime threshold is reached, saves the model and metadata,
and reuses that saved model for later inference. Inference produces anomaly
scores and normal/anomalous classifications that the dashboard presents as a
behavioral fingerprint channel, distinct from consensus failure and SCADA
divergence.

## Live Evidence Snapshot

The dashboard and MinIO were live during inspection. One dashboard state sample
captured at `2026-05-07T15:06:56Z` showed:

- Runtime UI status: `running`
- Current cycle: `100`
- Active scenario: `normal`
- Valid artifact count in dashboard state: `100`
- Latest artifact key: `valid-consensus-artifacts/round-20260507150641687734.json`
- Consensus status: `success`
- SCADA divergence channel: `none`
- Fingerprint model status: `model_available`
- Training event on current cycle: `reused`
- Fingerprint inference status: `completed`
- Fingerprint inference result count: `99`
- Replay behavior: `null`

The MinIO bucket was also live and growing. Around the same inspection window,
the bucket contained these observed prefixes:

- `valid-consensus-artifacts/`: valid per-round consensus JSON artifacts
- `fingerprint-datasets/`: dataset manifest JSON files and `.windows.npz` archives
- `fingerprint-models/`: one saved `.keras` model and one model metadata JSON

At one sampled point, MinIO contained `100` valid consensus JSON artifacts,
`182` dataset objects, and `2` model objects. A minute later, the live runtime had
advanced again and MinIO contained `101` valid consensus JSON artifacts,
`92` dataset manifest files, `92` dataset window archives, `1` model metadata
JSON, and `1` `.keras` model. This growth is itself useful evidence that the
autonomous runtime is actively producing new cycle artifacts.

## Prototype Pipeline

The implemented runtime pipeline follows this sequence:

```text
Compressor/power input
-> simulated physical sensor acquisition
-> edge publication and peer consumption
-> replicated edge view
-> Byzantine consensus / quorum
-> valid committed state
-> SCADA comparison
-> persistence in MinIO
-> fingerprint dataset generation
-> LSTM model training/reuse
-> inference/anomaly score
-> dashboard/operator feedback
```

### 1. Compressor and Power Input

The runtime starts with a simulated compressor profile in
`src/parallel_truth_fingerprint/config/ranges.py`. The default compressor has:

- compressor operating level from `0.0` to `100.0`
- temperature range from `48.0` to `95.0 degC`
- pressure range from `1.8` to `8.5 bar`
- RPM range from `1200.0` to `4200.0 rpm`

The dashboard and runtime can set `demo_power`, which is passed through the
simulator path rather than directly rewriting downstream state.

### 2. Simulated Physical Sensor Acquisition

`CompressorSimulator` generates temperature, pressure, and RPM values with
normal operating variation, noise, and transmitter metadata. Each edge uses
`EdgeAcquisitionService` to acquire only its own sensor and build a HART-style
payload containing:

- process variable (`pv`)
- optional secondary variable (`sv`)
- loop current in mA
- percent of configured range
- physics metrics such as noise floor, rate of change, and local stability score
- diagnostics such as field-device malfunction, current saturation, and cold start

This is physical acquisition semantics represented in software. It is not real
4-20 mA or HART hardware.

### 3. Edge Publication and Peer Consumption

Each edge publishes its local payload through the configured MQTT transport. The
runtime supports:

- `passive`: in-memory relay for deterministic tests
- `real`: real MQTT using `paho-mqtt` against the local Mosquitto container

The live demo defaults to the real MQTT path. MQTT is transport only; it does not
validate trust.

### 4. Replicated Edge View

Each edge updates its own `EdgeLocalReplicatedState` from self and peer payloads.
The replicated state has:

- `state_type = edge_local_replicated_state`
- `owner_edge_id`
- `is_validated = false`
- `is_complete`
- current sensor values visible from that edge's local view

This is an important academic boundary. A complete replicated edge view is still
not a trusted state. It is only an input to consensus.

### 5. Byzantine Consensus and Quorum

The live runtime uses a local 3-validator CometBFT network plus a Go ABCI
application under `abci/consensus_app/`. The Python runtime submits the consensus
round to CometBFT and queries the committed ABCI state back through
`CometBftRpcClient`.

The ABCI application computes:

- participating edges
- pairwise normalized deviations
- compatible peer counts
- trust scores
- trust ranking
- exclusions and exclusion reasons
- final consensus status
- committed consensused valid state when quorum is met

The current quorum rule is strict majority:

```text
required_quorum = (participant_count // 2) + 1
```

For three participating edges, quorum is `2`.

### 6. Valid Committed State

If enough non-excluded edges remain, the runtime receives a committed
`ConsensusedValidState`. The current implementation averages the sensor values
from valid source edges and rounds them to three decimals.

If quorum is not reached, no valid state is produced, and the cycle is blocked
before SCADA comparison, persistence, and fingerprint evaluation.

### 7. SCADA Comparison

The fake SCADA path is implemented by `FakeOpcUaScadaService`. It projects a
logical supervisory state from the consensused state and can expose it through
OPC UA when the server is started.

The comparison rule is intentionally narrow. `compare_consensused_to_scada`
compares only:

- temperature
- pressure
- rpm

The default tolerances are:

- temperature: `2.0`
- pressure: `0.35`
- rpm: `120.0`

If any supervised value exceeds tolerance, the runtime emits a SCADA divergence
alert and blocks downstream persistence/fingerprint work for that cycle.

### 8. Persistence in MinIO

Only successful consensus plus successful SCADA comparison can produce a valid
artifact. `persist_valid_consensus_artifact` writes a JSON record under:

`valid-consensus-artifacts/<round_id>.json`

This persisted object is the audit-ready record for the cycle.

### 9. Fingerprint Dataset Generation

The LSTM dataset builder reads valid consensus artifacts from MinIO and keeps
only records that are:

- consensus-successful
- marked `training_label = normal`
- marked `training_eligible = true`
- not SCADA-divergent
- feature-schema compatible

It sorts eligible artifacts by `round_identity.window_ended_at` and object key,
then builds sliding temporal windows. In the current runtime, sequence length is
`2`, so each window contains two consecutive valid artifacts.

### 10. LSTM Model Training and Reuse

When no model exists and the configured eligible-history threshold is met, the
runtime persists a dataset manifest and windows archive, trains a Keras LSTM
autoencoder using the Torch backend, and saves both model bytes and model
metadata under `fingerprint-models/`.

After a model exists, the runtime reuses the latest saved model metadata key. It
does not automatically retrain on every later cycle.

### 11. Inference and Anomaly Score

The inference path loads:

- the saved model metadata JSON
- the saved `.keras` model
- the model source dataset manifest/windows
- the current inference dataset manifest/windows

It computes reconstruction error per temporal window. The classification
threshold is derived from the source dataset baseline errors:

`source_dataset_mean_plus_3std`

If the inference window's reconstruction error is above that threshold, the
classification is `anomalous`; otherwise it is `normal`.

### 12. Dashboard and Operator Feedback

The dashboard presents the runtime state through:

- current cycle and cadence
- compressor/sensor values
- edge cards and replicated-state completeness
- consensus status, quorum, exclusions, and alerts
- SCADA state and comparison results
- valid artifact accumulation
- fingerprint lifecycle, model status, inference status, readiness, and anomaly score
- event timeline and raw component logs
- scenario controls and power controls

The dashboard consumes runtime payloads and MinIO artifacts. It does not invent a
second validation path.

## MinIO Artifact Structure

The bucket name is:

`valid-consensus-artifacts`

Inside that bucket, the observed "folders" are object prefixes:

```text
valid-consensus-artifacts/
fingerprint-datasets/
fingerprint-models/
```

The first prefix has the same text as the bucket. A full MinIO URI therefore
looks like:

`minio://valid-consensus-artifacts/valid-consensus-artifacts/round-....json`

### `valid-consensus-artifacts/`

Purpose: store one JSON record per accepted runtime cycle.

Kind of files:

- `valid-consensus-artifacts/round-<timestamp>.json`

Created by:

- `persist_valid_consensus_artifact` in
  `src/parallel_truth_fingerprint/persistence/service.py`
- called from `run_scada_comparison_and_persistence` in
  `scripts/run_local_demo.py`

Created when:

- consensus succeeds
- a consensused valid state exists
- SCADA comparison has not blocked the cycle
- MinIO write succeeds

What it proves:

- the cycle reached the validation-before-trust boundary
- quorum was met
- the committed physical-side state is traceable
- SCADA comparison was evaluated
- the artifact is eligible or ineligible for training for explicit reasons

Used downstream by:

- dataset builder
- LSTM lifecycle
- dashboard valid artifact count
- audit/demo explanation

### `fingerprint-datasets/`

Purpose: store inspectable dataset artifacts derived from validated MinIO
history.

Kind of files:

- `*.manifest.json`
- `*.windows.npz`

Created by:

- `persist_training_dataset_artifacts` in
  `src/parallel_truth_fingerprint/lstm_service/dataset_artifacts.py`

Created when:

- the fingerprint lifecycle evaluates valid history
- before first training
- on later cycles when a model already exists and inference is run
- for replay/freeze evaluation datasets when those scenarios are active and a
  model exists

What it proves:

- the model/inference path is not reading hidden in-memory data
- dataset creation is traceable to specific valid artifacts
- training eligibility is explicit
- adequacy assessment is explicit

Used downstream by:

- LSTM trainer
- LSTM inference
- dashboard readiness/provenance view

### `fingerprint-models/`

Purpose: store the reusable LSTM fingerprint model and its metadata.

Kind of files:

- `*.keras`
- `*.json`

Created by:

- `train_and_save_lstm_fingerprint_from_persisted_dataset`
- `train_and_save_lstm_fingerprint`

Created when:

- no saved model metadata exists yet
- the configured runtime training threshold is met
- at least one temporal window exists

What it proves:

- the prototype trained a real local LSTM autoencoder
- the model is persisted and reusable
- model provenance is traceable to a source dataset

Used downstream by:

- LSTM inference
- replay behavior detection
- dashboard fingerprint readiness and evidence views

## Valid Consensus Artifacts

A consensus round represents one runtime validation cycle over the latest
replicated edge views. In the live demo, each cycle:

1. advances the compressor simulation
2. lets each edge acquire and publish observations
3. lets each edge consume peer observations
4. exports edge-local replicated views
5. submits those views to CometBFT/ABCI
6. receives a committed round result
7. proceeds only if a valid state exists

A "valid artifact" means the persisted JSON record for a cycle that passed the
required gates. It is not raw data. It is post-consensus and post-SCADA-comparison
evidence.

Only validated/consensused data should be persisted because the architecture is
explicitly designed to avoid training or auditing from untrusted replicated edge
state. Persisting raw or pre-consensus observations as downstream truth would
collapse the central research claim.

### Sample Valid Consensus Artifact

Sample object:

`valid-consensus-artifacts/round-20260507150641687734.json`

Captured from MinIO while the dashboard was running at cycle 100.

```json
{
  "artifact_key": "valid-consensus-artifacts/round-20260507150641687734.json",
  "persisted_at": "2026-05-07T15:06:43.867834+00:00",
  "round_identity": {
    "round_id": "round-20260507150641687734",
    "window_started_at": "2026-05-07T15:05:41.687734+00:00",
    "window_ended_at": "2026-05-07T15:06:41.687734+00:00"
  },
  "consensus_status": "success",
  "participating_edges": ["edge-1", "edge-2", "edge-3"],
  "quorum_required": 2,
  "source_edges": ["edge-1", "edge-2", "edge-3"],
  "exclusions": [],
  "sensor_values": {
    "pressure": 6.352,
    "rpm": 3126.027,
    "temperature": 76.757
  },
  "dataset_context": {
    "scenario_label": "normal",
    "training_label": "normal",
    "training_eligible": true,
    "training_eligibility_reason": "normal_validated_run"
  },
  "divergent_sensors": [],
  "persisted_record_type": "valid_consensus_artifact"
}
```

This sample proves several things at once:

- all three edges participated
- quorum required was `2`
- no edges were excluded
- the consensus status was `success`
- SCADA matched the committed physical state
- the artifact was marked as normal and training-eligible
- the artifact can feed later dataset generation

### Quorum Representation

The quorum data appears in each valid artifact under `consensus_context`:

- `participating_edges`
- `quorum_required`
- `source_edges`
- `exclusions`
- `trust_ranking`
- `trust_evidence`
- `final_consensus_status`

The dashboard also presents quorum as "valid / quorum". In the normal sample,
this is effectively `3/2`.

### What Happens When Consensus Succeeds

When consensus succeeds:

- a `ConsensusedValidState` exists
- SCADA comparison can run
- if SCADA is within tolerance, persistence writes a valid JSON artifact
- the fingerprint lifecycle can build or update datasets from MinIO
- the dashboard increments valid artifact accumulation

### What Happens When Quorum or Consensus Fails

When quorum is not reached:

- no consensused valid state is produced
- SCADA comparison is blocked
- valid-artifact persistence is blocked
- downstream fingerprint evaluation is blocked
- the dashboard presents this as a deliberate validation refusal, not a generic runtime error

This is academically important because Byzantine validation must be able to say
"no trusted value exists for this cycle." Producing a fake downstream artifact
under no quorum would undermine the Byzantine validation pillar.

## Fingerprint Datasets

Fingerprint datasets are derived from valid consensus artifacts stored in MinIO.
They are the bridge between the distributed validation pipeline and the LSTM
fingerprint pipeline.

Each persisted dataset has:

- a manifest JSON
- a compressed `.windows.npz` archive

The manifest is the human-readable proof. The `.npz` archive is the model-ready
tensor data.

### Dataset Eligibility

The dataset builder considers a valid artifact eligible only if:

- `consensus_context.final_consensus_status == "success"`
- `dataset_context.training_label == "normal"`
- `dataset_context.training_eligible == true`
- `diagnostics.has_scada_divergence == false`
- the extracted feature schema matches previous selected artifacts

This keeps replay, SCADA divergence, quorum-loss, and faulty-edge scenarios out
of normal training data.

### Feature Schema

For each sensor, the extracted feature vector contains:

- `pv`
- `loop_current_ma`
- `pv_percent_range`
- `noise_floor`
- `rate_of_change_dtdt`
- `local_stability_score`
- `field_device_malfunction`
- `loop_current_saturated`
- `cold_start`

With three sensors, the current feature schema has `27` features.

### Temporal Windows

The current runtime default sequence length is `2`. A dataset with `100` eligible
artifacts therefore produces `99` sliding windows.

Each window records:

- window id
- source artifact keys
- round ids
- timestamps
- feature schema
- feature matrix
- label

### Sample Current Dataset Manifest

Sample object:

`fingerprint-datasets/training-dataset::round-20260507132718721578::round-20260507150641687734::seq-2.manifest.json`

```json
{
  "dataset_id": "training-dataset::round-20260507132718721578::round-20260507150641687734::seq-2",
  "created_at": "2026-05-07T15:06:44.125476+00:00",
  "source_bucket": "valid-consensus-artifacts",
  "source_prefix": "valid-consensus-artifacts/",
  "windows_object_key": "fingerprint-datasets/training-dataset::round-20260507132718721578::round-20260507150641687734::seq-2.windows.npz",
  "chronological_ordering_rule": "round_identity.window_ended_at_then_artifact_key",
  "sequence_length": 2,
  "stride": 1,
  "overlap_behavior": "sliding_stride_1",
  "feature_schema_count": 27,
  "selected_artifact_count": 100,
  "eligible_artifact_count": 100,
  "window_count": 99,
  "tensor_shape": [99, 2, 27],
  "training_label": "normal",
  "adequacy_assessment": {
    "validation_level": "meaningful_fingerprint_valid",
    "adequacy_met": true,
    "status_reason": "adequacy_floor_met",
    "minimum_eligible_artifact_count": 30,
    "minimum_window_count": 20,
    "eligible_artifact_count": 100,
    "window_count": 99
  }
}
```

This current dataset manifest proves that the runtime has accumulated enough
normal validated history to meet the configured stronger adequacy floor for the
dataset itself: at least `30` eligible artifacts and at least `20` windows.

### Runtime-Valid vs Meaningful Fingerprint Validation

The implementation distinguishes two validation levels:

- `runtime_valid_only`
- `meaningful_fingerprint_valid`

`runtime_valid_only` means the pipeline works technically: valid artifacts are
being persisted, datasets are being generated, models can be trained or reused,
and inference can run. It does not mean the normal-history basis is strong enough
for a robust academic fingerprint claim.

`meaningful_fingerprint_valid` means the source dataset meets the stronger floor:

- `30` eligible artifacts
- `20` generated windows

### Important Current Nuance

The live runtime has now accumulated a current dataset manifest with `100`
eligible artifacts and `99` windows, which meets the adequacy floor.

However, the saved model currently being reused was originally trained earlier
from this source dataset:

`training-dataset::round-20260507132718721578::round-20260507133620686690::seq-2`

That model source dataset had:

```json
{
  "eligible_artifact_count": 10,
  "window_count": 9,
  "validation_level": "runtime_valid_only",
  "adequacy_met": false,
  "minimum_eligible_artifact_count": 30,
  "minimum_window_count": 20
}
```

So the correct academic reading is:

- The current run has enough accumulated normal history to create a stronger
  dataset artifact.
- The currently reused model is still tied to an earlier source dataset below the
  stronger adequacy floor.
- Because the lifecycle reuses the saved model and does not automatically retrain
  later in the same run, the dashboard may honestly show `model_available` while
  also showing source dataset readiness as `runtime_valid_only`.

That is not a contradiction. It is an important provenance detail.

## Fingerprint Models

The model artifacts under `fingerprint-models/` represent the reusable LSTM
fingerprint generated from a persisted dataset.

The current implementation trains a Keras LSTM autoencoder using the Torch
backend. The model is saved as a `.keras` archive, and metadata is saved as JSON.

### Sample Model Metadata

Sample object:

`fingerprint-models/lstm-fingerprint-training-dataset-round-20260507132718721578-round-20260507133620686690-seq-2-20260507T133629363159+0000.json`

```json
{
  "model_id": "lstm-fingerprint-training-dataset-round-20260507132718721578-round-20260507133620686690-seq-2-20260507T133629363159+0000",
  "created_at": "2026-05-07T13:36:29.363159+00:00",
  "backend": "torch",
  "model_format": "keras",
  "model_type": "lstm_autoencoder",
  "source_dataset_id": "training-dataset::round-20260507132718721578::round-20260507133620686690::seq-2",
  "sequence_length": 2,
  "training_window_count": 9,
  "epochs": 1,
  "batch_size": 1,
  "loss_name": "mse",
  "model_object_key": "fingerprint-models/lstm-fingerprint-training-dataset-round-20260507132718721578-round-20260507133620686690-seq-2-20260507T133629363159+0000.keras",
  "metadata_object_key": "fingerprint-models/lstm-fingerprint-training-dataset-round-20260507132718721578-round-20260507133620686690-seq-2-20260507T133629363159+0000.json",
  "final_training_loss": 370910.625
}
```

This model metadata proves:

- a real model artifact was generated
- the model is an LSTM autoencoder
- the implementation used Keras with Torch backend
- the model is traceable to a specific source dataset
- the saved model can be reused by later inference cycles

### Model Reuse

Model reuse is valid in this prototype because the saved model is treated as a
runtime artifact with explicit provenance. Later cycles load the saved metadata
and model bytes from MinIO instead of retraining every cycle. This demonstrates
the intended lifecycle behavior:

1. collect valid normal history
2. train first reusable fingerprint model
3. save model and metadata
4. reuse model for later inference

The limitation is that reuse does not automatically upgrade the model's academic
adequacy claim when more history is accumulated later. The claim remains tied to
the model's source dataset until a retraining path is run.

### Threshold Origin and Anomaly Score

The inference code derives the threshold from reconstruction errors on the
source dataset:

`source_dataset_mean_plus_3std`

Dashboard sample from cycle 100:

```json
{
  "output_channel": "lstm_fingerprint",
  "source_dataset_validation_level": "runtime_valid_only",
  "inference_dataset_id": "training-dataset::round-20260507132718721578::round-20260507150641687734::seq-2",
  "window_id": "window::round-20260507150541458332::round-20260507150641687734",
  "anomaly_score": 360713.1875,
  "classification_threshold": 389961.76639000565,
  "threshold_origin": "source_dataset_mean_plus_3std",
  "classification": "normal"
}
```

This shows that:

- inference is running from persisted dataset artifacts
- the score is a reconstruction-error value
- the threshold is derived from the source training dataset
- the latest sampled window was classified as `normal`

### Evidence That Is Still Weak

The main weak claim is not the existence of the pipeline. The pipeline is running.
The weaker claim is the strength of a model trained from only `10` eligible
artifacts and `9` windows. The dashboard correctly surfaces this as
`runtime_valid_only` for the current reused model.

## Dashboard Interpretation Guide

The dashboard should be read as a live operator/evaluator view of the same
runtime pipeline, not as a separate simulation.

### Runtime Status

The top-level runtime status tells whether the autonomous runtime is active. In
the sample:

- `ui_status = running`
- `last_runtime_status = active`
- `current_cycle = 100`
- `cycle_interval_seconds = 60.0`

This means the dashboard is observing a real background runtime loop.

### Current Cycle

The current cycle is the count of completed runtime iterations. It should grow
over time when the runtime is running.

### Valid Artifact Growth

Valid artifact count shows how many accepted cycles have produced downstream
approved MinIO artifacts. Growth here is one of the easiest demo signals: each
new normal valid cycle should add a new JSON object under
`valid-consensus-artifacts/`.

### Edge Cards

Each edge card represents a logically independent edge service:

- edge 1: temperature
- edge 2: pressure
- edge 3: RPM

The edge cards show published observations, peer-consumed observations, and
whether the local replicated view is complete. The replicated view is still
marked unvalidated until consensus succeeds.

### Consensus Card

The consensus card should be read as the distributed trust decision:

- final consensus status
- round id
- valid participants versus quorum
- excluded edges if any
- consensus alert if quorum failed

For normal operation, expect `success` and valid participants at or above quorum.

### SCADA Comparison Card

The SCADA comparison card compares the consensused physical-side state against
the fake SCADA supervisory values. It is intentionally limited to temperature,
pressure, and RPM.

Expected normal state:

- divergent sensors: `none`
- decision: forwarded downstream

If `scada_divergence` is active, the card should show divergent sensors and the
cycle should be blocked before MinIO valid-artifact persistence and fingerprint
evaluation.

### Fingerprint / LSTM Card

The fingerprint card shows:

- model status
- inference status
- classification
- model reuse/training events
- anomaly score and threshold evidence through readiness/explainability panels

In the sample:

- `model_status = model_available`
- `training_events = ["reused"]`
- `inference_status = completed`
- `inference_result_count = 99`
- source dataset validation level: `runtime_valid_only`

The model is available and inference works, but the model's source training
dataset remains below the stronger academic adequacy floor.

### Evidence Summary and Readiness

The readiness panel is the best place to explain fingerprint maturity. In the
sample, it reports:

```text
Source dataset evidence: 10/30 eligible artifacts and 9/20 temporal windows.
```

That refers to the saved model's source dataset, not necessarily the latest
inference dataset. This is the correct conservative academic interpretation.

### Operational Event Timeline

The event timeline converts raw runtime state into component-scoped events. It
helps the professor follow what happened without reading full JSON immediately.

### Raw Logs and Raw Channel Details

The raw logs are the technical ground truth for the dashboard. They expose:

- compressor simulator snapshot
- sensor observations
- edge runtime state
- replicated edge views
- consensus summary and committed round state
- SCADA state and comparison output
- persistence stage
- fingerprint lifecycle
- fingerprint/replay channels

Use raw details when the evaluator asks "where did this dashboard statement come
from?"

## Real vs Simulated Parts

### Real in the Current Prototype

The following are real executable implementation paths in the current codebase:

- MQTT/Mosquitto messaging for the live runtime when `MQTT_TRANSPORT=real`
- real edge-to-edge publication and peer consumption through the MQTT boundary
- real edge-local replicated state reconstruction in each edge service
- real CometBFT-backed consensus path for the live local demo
- real Go ABCI deterministic trust/exclusion/quorum logic
- real committed round mapping back into Python consensus contracts
- real SCADA comparison logic on temperature, pressure, and RPM
- fake OPC UA SCADA service implemented with `asyncua`
- real MinIO object persistence for valid artifacts
- real dataset generation from persisted valid artifacts
- real `.npz` window archive persistence
- real Keras/Torch LSTM autoencoder training path
- real saved model metadata and model reuse
- real inference/anomaly score/classification path
- real dashboard state derived from runtime payloads and MinIO artifacts

### Simulated or Mocked in the Current Prototype

The following are simulated, controlled, or conceptual:

- compressor process behavior
- physical sensors
- physical edge hardware
- HART and 4-20 mA hardware semantics
- local acquisition hardware
- the plant SCADA environment
- SCADA process values, which are projected by the fake SCADA service
- attack scenarios such as SCADA replay, freeze, divergence, single-edge
  exclusion, and quorum loss
- real adversarial plant behavior
- production deployment, cloud infrastructure, and production HMI behavior

### Planned Architecture vs Current Implementation

The BMAD planning artifacts and PRD describe the approved architecture and note
that BBD/FABA is the theoretical inspiration. The current prototype implements
the consensus pillar with CometBFT plus a Go ABCI application. That is the actual
runtime implementation.

Likewise, Orion/Kafka-style cloud context-broker infrastructure remains
conceptual/out of scope. The current implementation uses local MinIO, local
MQTT/Mosquitto, local CometBFT, local Python services, and a local dashboard.

## Academic Alignment

The runtime artifacts support the approved PEP goals as follows.

### Physical Truth Source Parallel to SCADA/PLC

The valid consensus artifacts show a physical-side state derived from edge
acquisition and consensus, not from SCADA. The SCADA state is compared later as a
logical supervisory channel.

### Edge Decentralization

Each edge acquires only one local sensor, publishes its own observation, consumes
peer observations, and reconstructs a local shared view. The dashboard edge cards
and raw edge logs show this behavior.

### Byzantine Fault Tolerance and Quorum

The consensus context in each valid artifact records participating edges,
quorum, trust ranking, trust evidence, exclusions, and final status. No-quorum
cycles are blocked rather than forwarded.

### SCADA-vs-Consensus Comparison

Each valid artifact includes SCADA context and comparison output. The dashboard
keeps SCADA divergence separate from consensus and fingerprint results.

### Physical-Operational Dataset

Dataset manifests list the exact valid artifacts selected for temporal windows.
The feature schema includes process values, loop current, percent range, local
stability, noise, rate of change, and diagnostic flags.

### LSTM Fingerprint Generation

Model metadata proves that a Keras/Torch LSTM autoencoder was trained from a
persisted dataset and saved for reuse. Inference results prove the model is used
to produce anomaly scores and classifications.

### Replay/Divergence Evidence Separation

The code and dashboard separate:

- no quorum: consensus channel
- SCADA divergence: direct supervisory comparison channel
- replay behavior: fingerprint/replay behavioral channel

Story 6.5 specifically corrected replay detection to use richer SCADA-side
behavioral payload while keeping the SCADA comparison rule narrow.

### Traceability and Auditability

The artifacts provide traceability from:

round id -> consensus context -> valid state -> SCADA comparison -> persisted
artifact -> dataset manifest -> model metadata -> inference result.

This is the key audit chain for explaining the prototype.

## Evaluation Guide for Professor or Demo

### Start the Runtime

Recommended sequence:

```powershell
docker compose -f compose.local.yml up -d mqtt-broker minio
.\scripts\init_cometbft_testnet.ps1
.\scripts\start_consensus_stack.ps1
$env:PYTHONPATH='src'
.\.venv\Scripts\python scripts\run_local_dashboard.py
```

Open:

- Dashboard: `http://127.0.0.1:8088`
- MinIO console: `http://127.0.0.1:9001`

MinIO login:

- user: `minioadmin`
- password: `minioadmin`

### Observe Cycle Growth

On the dashboard, show:

- runtime status changing to running
- current cycle increasing
- valid artifact count increasing
- latest artifact key changing by round

### Open MinIO and Show the Three Prefixes

In bucket `valid-consensus-artifacts`, show:

- `valid-consensus-artifacts/`
- `fingerprint-datasets/`
- `fingerprint-models/`

Open one valid artifact JSON and point to:

- `round_identity`
- `consensus_context`
- `validated_state`
- `dataset_context`
- `scada_context`
- `diagnostics`

Open one dataset manifest and point to:

- selected artifact keys
- window count
- tensor shape
- adequacy assessment

Open model metadata and point to:

- source dataset id
- training window count
- model object key
- final training loss
- model reuse evidence in dashboard

### Explain Each Runtime Block

Use the dashboard pipeline:

- compressor and sensors: simulated physical origin
- edges: decentralized acquisition and replication
- consensus: trusted committed state
- SCADA: supervisory comparison
- fingerprint: behavioral interpretation

### Trigger Scenarios

Supported scenarios in the current implementation:

- `normal`
- `scada_replay`
- `scada_freeze`
- `scada_divergence`
- `single_edge_exclusion`
- `quorum_loss`

The dashboard applies scenario changes to the next eligible cycle when runtime is
running.

### Expected Evidence by Scenario

Normal:

- consensus succeeds
- no exclusions
- SCADA comparison matches
- valid artifacts grow
- normal artifacts are training-eligible
- fingerprint model is deferred, trained, or reused depending on lifecycle stage

`single_edge_exclusion`:

- one edge receives deterministic inconsistent offsets
- consensus should exclude the faulty edge if enough peers remain
- consensus may still succeed with quorum
- artifact can be persisted if SCADA comparison passes, but dataset context marks
  it non-normal and training-ineligible

`quorum_loss`:

- multiple edges are made inconsistent
- valid participants fall below quorum
- no trusted payload is produced
- no SCADA comparison, persistence, or fingerprint evaluation should proceed for
  that cycle

`scada_divergence`:

- consensus can still succeed
- fake SCADA applies an offset to supervisory values
- comparison detects divergent sensors
- downstream persistence and fingerprint evaluation are blocked

`scada_replay`:

- consensus can still succeed
- SCADA comparison remains narrow and may stay clear
- richer SCADA-side behavioral payload is evaluated through the fingerprint/replay path
- replay behavior should appear as a distinct fingerprint-side channel when a saved model exists
- replay cycles remain non-normal for training

`scada_freeze`:

- SCADA values/behavior can be frozen through the fake SCADA override path
- the current replay/freeze path is implemented, but the strongest corrected
  replay claim in Story 6.5 is specifically about `scada_replay`

## Known Limitations and Honest Claims

- This is a local academic prototype, not a plant deployment.
- Sensors are simulated.
- Compressor behavior is modeled in software.
- SCADA is fake/simulated, though the OPC UA service path is implemented with
  real tooling.
- Physical signal duplication is represented conceptually through the parallel
  edge acquisition architecture; it is not real duplicated field wiring.
- HART and 4-20 mA semantics are represented in payloads and acquisition
  contracts, not by real analog hardware.
- MQTT, CometBFT, MinIO, Keras, Torch, and the dashboard run locally.
- The consensus implementation is CometBFT plus Go ABCI, not a literal BBD/FABA
  runtime.
- Current saved model reuse is valid runtime behavior, but the model adequacy
  claim remains tied to the model's original source dataset.
- In the inspected live run, the current accumulated dataset had enough history
  for `meaningful_fingerprint_valid`, but the reused model was trained earlier
  from a `runtime_valid_only` source dataset.
- `runtime_valid_only` is useful evidence that the end-to-end pipeline works; it
  is not the same as strong academic fingerprint validation.
- The default runtime can train earlier than the stronger adequacy floor unless
  `DEMO_TRAIN_AFTER_ELIGIBLE_CYCLES` is raised to `30`.
- Once the first model exists, the lifecycle reuses it and does not
  automatically retrain later in the same run.
- Attack scenarios are controlled software scenarios, not real adversary actions
  against hardware.
- The dashboard is a local explanatory/operator surface, not a production HMI.

## Final Summary Table

| Artifact / File Type | Location | Generated By | Triggered When | Contains | Used By | Academic Meaning |
|---|---|---|---|---|---|---|
| Valid consensus JSON | `valid-consensus-artifacts/round-*.json` | `persist_valid_consensus_artifact` | Consensus succeeds and SCADA comparison does not block | round identity, consensus context, trust evidence, valid state, dataset context, SCADA context, diagnostics | dataset builder, dashboard, audit review | Proof that a cycle passed validation-before-trust and produced persisted physical-side truth |
| Dataset manifest JSON | `fingerprint-datasets/*.manifest.json` | `persist_training_dataset_artifacts` | Fingerprint lifecycle builds training or inference dataset | source bucket/prefix, selected artifacts, skipped artifacts, feature schema, window count, tensor shape, adequacy assessment | trainer, inference, dashboard readiness | Traceable bridge from validated artifacts to physical-operational ML dataset |
| Dataset windows archive | `fingerprint-datasets/*.windows.npz` | `persist_training_dataset_artifacts` | Same dataset generation step as manifest | compressed tensors, window ids, artifact keys, round ids, timestamps, labels | LSTM trainer and inference | Model-ready temporal representation of validated normal history or scenario evaluation windows |
| Model metadata JSON | `fingerprint-models/*.json` | `train_and_save_lstm_fingerprint` | First model training after configured threshold and available windows | model id, source dataset id, feature schema, sequence length, training window count, epochs, batch size, loss, object keys | inference, dashboard readiness | Provenance for the generated physical-operational fingerprint |
| Saved LSTM model | `fingerprint-models/*.keras` | `train_and_save_lstm_fingerprint` | Same training event as metadata | serialized Keras model archive | inference and replay behavior detection | Reusable trained fingerprint model |
| Fingerprint inference result | dashboard/runtime payload, not a separate MinIO artifact in current implementation | `run_lstm_fingerprint_inference_from_persisted_dataset` | Saved model exists and current dataset has windows | output channel, model id, dataset ids, anomaly score, threshold, threshold origin, classification | dashboard fingerprint card, readiness view, event timeline | Evidence that the saved LSTM fingerprint is actively classifying temporal windows |
| Replay behavior result | dashboard/runtime payload, not a separate standalone MinIO result artifact | `run_scada_replay_behavior_detection` | Replay/freeze scenario active and saved model exists | replay mode, source rounds, anomaly score, threshold, classification, SCADA divergent sensors | dashboard replay/fingerprint channel | Evidence that replay behavior is treated as behavioral fingerprint output, distinct from SCADA divergence |
| Runtime detailed log | `logs/run_local_demo.log` or configured `DEMO_LOG_PATH` | `write_detailed_log` | Each runtime cycle / stop state | latest cycle payload, cycle history, raw edge logs, consensus, SCADA, persistence, fingerprint lifecycle | dashboard-like inspection, manual audit | Local trace of the full pipeline outside MinIO |
| Dashboard state JSON | `http://127.0.0.1:8088/api/state` | `LocalOperatorDashboardController` | Dashboard state request | runtime status, controls, monitoring, channels, event views, pipeline, readiness, raw logs | professor demo, operator explanation | Human-readable live interpretation of runtime artifacts and channels |

## Final Interpretation

The artifacts show that the prototype is not only printing a demo narrative. It
is creating a traceable chain of runtime evidence:

```text
edge observations
-> committed consensus state
-> SCADA comparison
-> MinIO valid artifact
-> normal-only dataset manifest/windows
-> saved LSTM model metadata/model bytes
-> inference anomaly score/classification
-> dashboard evidence
```

The strongest current claim is that the runtime pipeline and artifact chain are
working end to end and are inspectable. The careful academic claim is that
fingerprint strength depends on the source dataset used to train the active
model. In the inspected run, the live history had grown strong enough to create a
meaningfully adequate current dataset, but the active reused model was still
provenanced to an earlier runtime-valid-only dataset. That distinction is exactly
the kind of honest traceability the artifact design is meant to provide.
