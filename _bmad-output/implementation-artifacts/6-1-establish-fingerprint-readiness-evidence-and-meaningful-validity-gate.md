# Story 6.1: Establish Fingerprint Readiness Evidence and Meaningful-Validity Gate

Status: review

## Story

As a researcher and demo operator,
I want the prototype to present explicit fingerprint readiness evidence and a meaningful-validity gate derived from existing artifacts,
so that the fingerprint can be explained honestly and more defensibly during an academic demonstration without changing the ML architecture.

## Scope Notes

- This story is limited to readiness evidence, provenance visibility, and academically honest claim framing for the existing fingerprint path.
- It must preserve the five real pillars exactly as they already exist:
  - acquisition of sensor values
  - decentralization across edges
  - Byzantine consensus across edges
  - comparison between consensused data and SCADA data
  - LSTM-based fingerprint generation
- It must reuse the current:
  - persisted dataset artifacts
  - adequacy evaluation
  - trained-model metadata
  - inference results
  - replay behavior outputs
  - MinIO persistence boundary
- It must not add:
  - a new ML model family
  - a new anomaly engine
  - a new backend service
  - a new storage boundary
  - a new research scope

## Limitation Carried Forward

The fingerprint must still be presented honestly when the adequacy floor remains unmet. Until the source dataset reaches the approved floor of 30 eligible normal artifacts and 20 generated windows, the fingerprint remains runtime-valid only and must not be presented as academically strong.

## Acceptance Criteria

1. Given the existing persisted dataset artifacts, model metadata, lifecycle state, and inference outputs, when fingerprint readiness is presented, then the readiness view is derived from those existing artifacts only and does not require a new ML path.
2. Given the adequacy requirement, when readiness is evaluated, then the prototype explicitly distinguishes between:
   - `runtime_valid_only`
   - `meaningful_fingerprint_valid`
   and ties that distinction back to the approved adequacy floor of:
   - 30 eligible normal artifacts
   - 20 generated windows
3. Given the provenance requirement, when readiness evidence is shown, then it includes at minimum:
   - model identity
   - source dataset identity
   - training window count
   - threshold origin
   - current limitation statement
4. Given the bounded demo-evidence requirement, when fingerprint readiness is summarized, then the prototype can present a concise evidence matrix for at least:
   - normal operation
   - compressor-power variation
   - replay or freeze behavior
   - SCADA divergence as a separate non-fingerprint channel
5. Given the academic-honesty requirement, when the readiness state is below the meaningful-valid threshold, then the prototype explicitly says what is working, what evidence exists, and what is still not proven.
6. Given the operator-facing wording requirement, when readiness and limitation text is shown in the dashboard or operator surface, then it uses domain language such as fingerprint model, training adequacy, replay detection, anomaly evidence, or model provenance and does not reference internal delivery labels such as Story 4.3, Story 4.4, Story 6.1, or any other BMAD story numbers.
7. Given focused validation, when this story is closed, then testing proves that readiness summaries match the underlying dataset manifest, model metadata, and inference artifacts without overclaiming fingerprint strength.
8. Given the project testing-closeout rule, when Story 6.1 is closed, then the story record explicitly includes:
   - what was tested
   - exact commands executed
   - test results
   - real runtime behavior validated
   - remaining limitations

## Testing Requirements

- Testing is mandatory for this story.
- The story is incomplete unless it includes:
  - focused tests for readiness-state derivation from persisted artifacts
  - focused tests for model-provenance and threshold-origin display
  - focused tests that keep replay evidence distinct from SCADA divergence evidence
  - focused tests that ensure user-facing texts do not leak internal story labels
  - one real runtime validation pass confirming that the readiness view reflects a real local run and remains honest about adequacy limitations

## Dependencies

- Story 4.2A persisted dataset artifacts and adequacy evaluation
- Story 4.2 model training and persisted model metadata
- Story 4.3 fingerprint inference and threshold origin
- Story 4.4 replay-oriented anomaly behavior
- Story 4.6 local operator dashboard
- Story 5.3 translated status and evidence-view infrastructure

## Non-Goals

- no new ML architecture
- no new anomaly engine
- no architecture redesign
- no new backend service
- no new storage boundary
- no claim of academic strength before adequacy is actually met

## Tasks / Subtasks

- [x] Define the bounded fingerprint readiness states and evidence summary contract. (AC: 1, 2, 5, 6)
- [x] Expose provenance and threshold evidence from the current dataset/model/inference artifacts. (AC: 1, 3, 4)
- [x] Add a bounded evidence matrix for normal, power-variation, replay/freeze, and SCADA-divergence interpretation. (AC: 4, 5)
- [x] Replace internal story-number wording in operator-facing fingerprint texts with domain language. (AC: 6)
- [x] Add focused tests and one real runtime validation pass. (AC: 7, 8)

## Technical Notes

- The codebase already distinguishes `runtime_valid_only` from `meaningful_fingerprint_valid`; this story should package that distinction into a clearer readiness view rather than invent a new readiness engine.
- The source adequacy floor already exists in the current implementation and should remain the objective criterion.
- This story should clarify the difference between:
  - pipeline validity
  - model availability
  - meaningful fingerprint readiness
- Replay/freeze evidence must remain on the fingerprint side, while SCADA divergence remains on the SCADA-comparison side.

## Real vs Simulated Boundary

- Real in this story:
  - persisted dataset manifest and windows archive
  - adequacy assessment
  - saved model metadata
  - inference results
  - replay behavior outputs
  - MinIO persistence evidence
- Simulated or controlled in this story:
  - compressor/process behavior
  - replay/freeze scenario generation
  - SCADA environment

## Academic Mapping

- This story does not change the fingerprint mechanism.
- It strengthens the academic defensibility of the prototype by clarifying:
  - what evidence exists now
  - what threshold has or has not been met
  - what the prototype can already demonstrate
  - what still remains below an academically stronger adequacy bar

## Dev Agent Record

### Agent Model Used

GPT-5 Codex

### Debug Log References

- Story 6.1 was implemented as a derived dashboard evidence layer only.
- The dashboard now reads saved model metadata and dataset-manifest evidence from the existing MinIO artifact boundary instead of inventing training details in the UI.
- No new ML model, anomaly engine, runtime service, or storage boundary was introduced.

### Completion Notes List

- Extended the dashboard explainability view to include a new `fingerprint_readiness` section.
- Added readiness-state summaries that explicitly distinguish:
  - runtime-valid only
  - meaningful fingerprint validity
- Added an adequacy gate tied to the approved floor of:
  - 30 eligible artifacts
  - 20 temporal windows
- Added persisted provenance display for:
  - model identity
  - model id
  - source dataset id
  - training window count
  - threshold origin
  - limitation note
- Added training-detail display for demo use, including:
  - first training reference
  - current model usage
  - model creation time
  - epochs
  - batch size
  - loss name
  - final training loss
  - sequence length
  - feature schema
- Added a bounded behavior evidence matrix for:
  - normal operation
  - compressor-power variation
  - replay/freeze behavior
  - SCADA divergence as a separate non-fingerprint channel
- Added dashboard rendering for the new readiness evidence so the operator can show training details during the demo without opening raw MinIO objects.
- Implemented only Story 6.1.

### What Was Tested

- Focused readiness/evidence-view tests
- Existing dashboard control-surface tests
- Existing fingerprint-inference tests
- Existing pipeline/event dashboard tests to catch regressions
- Real dashboard smoke validation
- Full regression suite
- One live readiness probe through the real dashboard controller path showing model provenance and training details after training completed

### Exact Commands Executed

```powershell
$env:PYTHONPATH='src'
.\.venv\Scripts\python -m unittest tests.dashboard.test_evidence_view tests.dashboard.test_control_surface tests.lstm_service.test_inference
```

```powershell
$env:PYTHONPATH='src'
.\.venv\Scripts\python -m unittest tests.dashboard.test_pipeline_view tests.dashboard.test_event_timeline
```

```powershell
docker compose -f compose.local.yml up -d mqtt-broker minio
```

```powershell
$env:PYTHONPATH='src'
$env:RUN_REAL_DASHBOARD_SMOKE='1'
.\.venv\Scripts\python -m unittest tests.dashboard.test_control_surface_runtime_smoke
```

```powershell
$env:PYTHONPATH='src'
.\.venv\Scripts\python -m unittest discover -s tests
```

```powershell
$env:PYTHONPATH='src'
@'
import json
import time
from dataclasses import replace
from datetime import datetime, timezone
from unittest import mock
from urllib import request

from parallel_truth_fingerprint.config.runtime import RuntimeDemoConfig
from parallel_truth_fingerprint.consensus import build_consensus_alert, build_round_log, build_round_summary
from parallel_truth_fingerprint.dashboard import LocalOperatorDashboardController, LocalOperatorDashboardServer
from parallel_truth_fingerprint.lstm_service import configure_scada_replay_runtime_stage, execute_deferred_fingerprint_lifecycle, run_scada_replay_behavior_detection
from parallel_truth_fingerprint.scenario_control import apply_runtime_scenario_control, resolve_runtime_scenario_control_stage
from scripts import run_local_demo
from tests.persistence.test_service import build_valid_audit_package

class _FakeReceipt:
    def __init__(self, cycle_index: int, round_id: str) -> None:
        self.height = cycle_index
        self.tx_hash = f"TX-{cycle_index:03d}"
        self.check_tx_code = 0
        self.deliver_tx_code = 0
        self.round_id = round_id

def build_variable_audit_package(*, round_id: str, temperature: float, pressure: float, rpm: float):
    audit_package = build_valid_audit_package(round_id=round_id)
    updated_values = {
        "temperature": float(temperature),
        "pressure": float(pressure),
        "rpm": float(rpm),
    }
    audit_package.consensused_valid_state.sensor_values.update(updated_values)
    audit_package.consensus_result.consensused_valid_state.sensor_values.update(updated_values)
    for state in audit_package.round_input.replicated_states:
        for sensor_name, value in updated_values.items():
            payload = state.observations_by_sensor[sensor_name]
            state.observations_by_sensor[sensor_name] = replace(
                payload,
                process_data=replace(
                    payload.process_data,
                    pv=replace(payload.process_data.pv, value=float(value)),
                ),
            )
    return audit_package

def json_request(method, url, payload=None):
    data = None if payload is None else json.dumps(payload).encode("utf-8")
    headers = {"Content-Type": "application/json"} if payload is not None else {}
    req = request.Request(url, data=data, headers=headers, method=method)
    with request.urlopen(req, timeout=10) as response:
        return json.loads(response.read().decode("utf-8"))

run_suffix = datetime.now(timezone.utc).strftime("%Y%m%d%H%M%S%f")
config = RuntimeDemoConfig(
    mqtt_transport="passive",
    minio_endpoint="localhost:9000",
    minio_access_key="minioadmin",
    minio_secret_key="minioadmin",
    minio_bucket=f"story-6-1-smoke-{run_suffix}",
    minio_secure=False,
    demo_cycle_interval_seconds=0.05,
    demo_max_cycles=0,
    demo_train_after_eligible_cycles=3,
    demo_fingerprint_sequence_length=2,
    demo_dashboard_host="127.0.0.1",
    demo_dashboard_port=0,
    demo_log_path=f"logs/story-6-1-smoke-{run_suffix}.json",
)
controller = LocalOperatorDashboardController(config)
server = LocalOperatorDashboardServer(controller, host="127.0.0.1", port=0)

def cycle_executor(*, cycle_index: int, config, artifact_store, scada_service, **kwargs):
    scenario_control_stage = resolve_runtime_scenario_control_stage(config=config, cycle_index=cycle_index)
    cycle_config = apply_runtime_scenario_control(config=config, scenario_stage=scenario_control_stage)
    power = float(cycle_config.demo_power)
    temperature = round(38.0 + (power * 0.52) + cycle_index, 3)
    pressure = round(1.4 + (power * 0.055) + (cycle_index * 0.05), 3)
    rpm = round(850.0 + (power * 28.0) + (cycle_index * 12.0), 3)
    round_id = f"round-story-6-1-{run_suffix}-{cycle_index:03d}"
    audit_package = build_variable_audit_package(round_id=round_id, temperature=temperature, pressure=pressure, rpm=rpm)
    scada_replay_stage = configure_scada_replay_runtime_stage(scada_service=scada_service, config=cycle_config, cycle_index=cycle_index)
    scada_state, comparison_stage, comparison_output, scada_alert, persistence_stage = run_local_demo.run_scada_comparison_and_persistence(
        consensus_audit=audit_package,
        artifact_store=artifact_store,
        scada_service=scada_service,
        fault_mode=cycle_config.demo_fault_mode,
        scenario_control_stage=scenario_control_stage,
        scada_replay_stage=scada_replay_stage,
    )
    fingerprint_stage, fingerprint_inference_results = execute_deferred_fingerprint_lifecycle(
        cycle_index=cycle_index,
        artifact_store=artifact_store,
        sequence_length=config.demo_fingerprint_sequence_length,
        train_after_eligible_cycles=config.demo_train_after_eligible_cycles,
    )
    replay_behavior_result, replay_inference_results = (
        run_scada_replay_behavior_detection(
            current_round_id=round_id,
            consensus_final_status="success",
            scada_state=scada_state,
            comparison_output=comparison_output,
            replay_stage=scada_replay_stage,
            artifact_store=artifact_store,
            sequence_length=config.demo_fingerprint_sequence_length,
        )
        if scada_state is not None and comparison_output is not None
        else (None, ())
    )
    return {
        "cycle_index": cycle_index,
        "simulator_snapshot": {
            "compressor_id": "compressor-1",
            "operating_state_pct": power,
            "sensors": {"temperature": temperature, "pressure": pressure, "rpm": rpm},
        },
        "node_status": {"node_info": {"version": "story-6-1-smoke"}, "sync_info": {"latest_block_height": str(cycle_index)}},
        "commit_receipt": _FakeReceipt(cycle_index, round_id),
        "committed_round": {"round_id": round_id, "commit_height": cycle_index},
        "consensus_summary": build_round_summary(audit_package),
        "consensus_log": build_round_log(audit_package),
        "consensus_alert": build_consensus_alert(audit_package, build_round_log(audit_package)),
        "scada_state": scada_state,
        "comparison_stage": comparison_stage,
        "comparison_output": comparison_output,
        "scada_alert": scada_alert,
        "persistence_stage": persistence_stage,
        "fault_edges": (),
        "scenario_control_stage": scenario_control_stage,
        "scada_replay_stage": scada_replay_stage,
        "fingerprint_stage": fingerprint_stage,
        "fingerprint_inference_results": fingerprint_inference_results,
        "replay_behavior_result": replay_behavior_result,
        "replay_inference_results": replay_inference_results,
        "edges": (),
    }

server.start_in_background()
try:
    with mock.patch.object(run_local_demo, "execute_demo_cycle", side_effect=cycle_executor):
        with mock.patch.object(run_local_demo, "print_cycle_report"):
            json_request("POST", f"{server.base_url}/api/runtime/start", {})
            state = None
            for _ in range(120):
                time.sleep(0.1)
                state = json_request("GET", f"{server.base_url}/api/state")
                if state["runtime"]["current_cycle"] >= 4:
                    break
            readiness = state["explainability"]["fingerprint_readiness"]
            print("READINESS_LABEL", readiness["readiness_state"]["label"])
            print("ADEQUACY_SUMMARY", readiness["adequacy_gate"]["summary"])
            print("MODEL_IDENTITY", readiness["provenance"]["model_identity"])
            print("MODEL_ID", readiness["provenance"]["model_id"])
            print("SOURCE_DATASET", readiness["provenance"]["source_dataset_id"])
            print("TRAINING_WINDOWS", readiness["provenance"]["training_window_count"])
            print("THRESHOLD_ORIGIN", readiness["provenance"]["threshold_origin"])
            print("FIRST_TRAINING", readiness["training_details"]["first_training_reference"])
            print("TRAINED_AT", readiness["training_details"]["trained_at"])
            print("MATRIX", [(item["label"], item["status"]) for item in readiness["evidence_matrix"]])
finally:
    server.stop()
'@ | .\.venv\Scripts\python -
```

### Test Results

- `tests.dashboard.test_evidence_view tests.dashboard.test_control_surface tests.lstm_service.test_inference` -> `Ran 13 tests` -> `OK`
- `tests.dashboard.test_pipeline_view tests.dashboard.test_event_timeline` -> `Ran 7 tests` -> `OK`
- `tests.dashboard.test_control_surface_runtime_smoke` -> `Ran 1 test` -> `OK`
- `python -m unittest discover -s tests` -> `Ran 136 tests` -> `OK (skipped=7)`

### Real Runtime Behavior Validated

- The real dashboard smoke still passed after adding Story 6.1 readiness evidence.
- The live dashboard state now surfaces training provenance and readiness details from persisted artifacts.
- A live readiness probe through the real dashboard controller path produced:
  - `READINESS_LABEL Runtime-valid only: fingerprint pipeline works, but readiness is still below target`
  - `ADEQUACY_SUMMARY Source dataset evidence: 3/30 eligible artifacts and 2/20 temporal windows.`
  - `MODEL_IDENTITY fingerprint-models/lstm-fingerprint-training-dataset-round-story-6-1-...json`
  - `MODEL_ID lstm-fingerprint-training-dataset-round-story-6-1-...`
  - `SOURCE_DATASET training-dataset::round-story-6-1-...::seq-2`
  - `TRAINING_WINDOWS 2`
  - `THRESHOLD_ORIGIN source_dataset_mean_plus_3std`
  - `FIRST_TRAINING cycle 3`
  - `TRAINED_AT 2026-04-03T13:33:52.472195+00:00`
  - `MATRIX [('Normal operation', 'Observed'), ('Compressor-power variation', 'Not exercised yet'), ('Replay / freeze behavior', 'Not exercised yet'), ('SCADA divergence', 'Not exercised yet')]`
- This validates that the dashboard can now show the operator:
  - what model was trained
  - what dataset trained it
  - how many windows supported training
  - where the anomaly threshold came from
  - when the first training happened

### Remaining Limitations

- Story 6.1 improves fingerprint evidence visibility but does not increase fingerprint adequacy by itself.
- The fingerprint base remains runtime-valid only, not meaningfully fingerprint-valid, until the adequacy floor is actually met.
- The behavior evidence matrix is intentionally bounded to the current prototype scope and does not claim stronger generalization than the current dataset supports.

### File List

- `_bmad-output/implementation-artifacts/6-1-establish-fingerprint-readiness-evidence-and-meaningful-validity-gate.md`
- `src/parallel_truth_fingerprint/dashboard/control_surface.py`
- `src/parallel_truth_fingerprint/dashboard/evidence_view.py`
- `tests/dashboard/test_control_surface.py`
- `tests/dashboard/test_control_surface_runtime_smoke.py`
- `tests/dashboard/test_evidence_view.py`
- `tests/lstm_service/test_inference.py`
