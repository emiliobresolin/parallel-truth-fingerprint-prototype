"""Real runtime smoke validation for Epic 4 Story 4.3A."""

from __future__ import annotations

from datetime import datetime, timedelta, timezone
import importlib.util
import json
import os
from pathlib import Path
import socket
import unittest
from unittest import mock

from parallel_truth_fingerprint.comparison import (
    ScadaToleranceProfile,
    build_scada_comparison_output,
    build_scada_divergence_alert,
    compare_consensused_to_scada,
    format_scada_comparison_output_compact,
)
from parallel_truth_fingerprint.config.runtime import RuntimeDemoConfig
from parallel_truth_fingerprint.consensus import (
    build_consensus_alert,
    build_round_log,
    build_round_summary,
)
from parallel_truth_fingerprint.lstm_service import execute_deferred_fingerprint_lifecycle
from parallel_truth_fingerprint.persistence import (
    MinioArtifactStore,
    MinioStoreConfig,
    persist_valid_consensus_artifact,
)
from parallel_truth_fingerprint.scada import FakeOpcUaScadaService
from scripts import run_local_demo
from tests.persistence.test_service import build_valid_audit_package


def _real_runtime_lifecycle_smoke_enabled() -> bool:
    return os.getenv("RUN_REAL_RUNTIME_LIFECYCLE_SMOKE") == "1"


def _dependencies_available() -> bool:
    return (
        importlib.util.find_spec("keras") is not None
        and importlib.util.find_spec("torch") is not None
        and importlib.util.find_spec("minio") is not None
        and importlib.util.find_spec("numpy") is not None
    )


def _minio_available(host: str = "127.0.0.1", port: int = 9000) -> bool:
    try:
        with socket.create_connection((host, port), timeout=2):
            return True
    except OSError:
        return False


class _FakeReceipt:
    def __init__(self, cycle_index: int, round_id: str) -> None:
        self.height = cycle_index
        self.tx_hash = f"TX-{cycle_index:03d}"
        self.check_tx_code = 0
        self.deliver_tx_code = 0
        self.round_id = round_id


@unittest.skipUnless(
    _real_runtime_lifecycle_smoke_enabled(),
    "Set RUN_REAL_RUNTIME_LIFECYCLE_SMOKE=1 to run the Story 4.3A smoke test.",
)
@unittest.skipUnless(
    _dependencies_available(),
    "Required runtime dependencies for Story 4.3A are not installed.",
)
@unittest.skipUnless(
    _minio_available(),
    "Local MinIO is not reachable on 127.0.0.1:9000.",
)
class RuntimeLifecycleSmokeTests(unittest.TestCase):
    def test_real_runtime_loop_defers_then_trains_once_then_reuses_model(self) -> None:
        run_suffix = datetime.now(timezone.utc).strftime("%Y%m%d%H%M%S%f")
        bucket_name = f"runtime-lifecycle-smoke-{run_suffix}"
        log_relative_path = f"logs/runtime-lifecycle-smoke-{run_suffix}.json"
        log_path = run_local_demo.PROJECT_ROOT / log_relative_path
        store = MinioArtifactStore(
            MinioStoreConfig(
                endpoint="localhost:9000",
                access_key="minioadmin",
                secret_key="minioadmin",
                bucket=bucket_name,
                secure=False,
            )
        )
        config = RuntimeDemoConfig(
            mqtt_transport="passive",
            minio_endpoint="localhost:9000",
            minio_access_key="minioadmin",
            minio_secret_key="minioadmin",
            minio_bucket=bucket_name,
            demo_cycle_interval_seconds=0.05,
            demo_max_cycles=4,
            demo_train_after_eligible_cycles=3,
            demo_fingerprint_sequence_length=2,
            demo_log_path=log_relative_path,
        )
        base_time = datetime(2026, 4, 2, 21, 0, 0, tzinfo=timezone.utc)

        def cycle_executor(*, cycle_index: int, **kwargs) -> dict[str, object]:
            round_id = f"round-runtime-loop-{run_suffix}-{cycle_index:03d}"
            audit_package = build_valid_audit_package(round_id=round_id)
            scada_state = FakeOpcUaScadaService().project_state(
                audit_package.consensused_valid_state
            )
            comparison_output = build_scada_comparison_output(
                compare_consensused_to_scada(
                    valid_state=audit_package.consensused_valid_state,
                    scada_state=scada_state,
                    tolerance_profile=ScadaToleranceProfile(
                        temperature=1.0,
                        pressure=0.3,
                        rpm=100.0,
                    ),
                )
            )
            scada_alert = build_scada_divergence_alert(comparison_output)
            persistence_record = persist_valid_consensus_artifact(
                audit_package=audit_package,
                scada_state=scada_state,
                scada_comparison_output=comparison_output,
                dataset_context={
                    "scenario_label": "normal",
                    "training_label": "normal",
                    "training_eligible": True,
                    "training_eligibility_reason": "story_4_3a_runtime_smoke",
                },
                artifact_store=store,
                persisted_at=base_time + timedelta(minutes=cycle_index),
            )
            fingerprint_stage, inference_results = execute_deferred_fingerprint_lifecycle(
                cycle_index=cycle_index,
                artifact_store=store,
                sequence_length=config.demo_fingerprint_sequence_length,
                train_after_eligible_cycles=config.demo_train_after_eligible_cycles,
            )
            return {
                "cycle_index": cycle_index,
                "node_status": {
                    "node_info": {"version": "runtime-smoke"},
                    "sync_info": {"latest_block_height": str(cycle_index)},
                },
                "commit_receipt": _FakeReceipt(cycle_index, round_id),
                "committed_round": {"round_id": round_id, "commit_height": cycle_index},
                "consensus_summary": build_round_summary(audit_package),
                "consensus_log": build_round_log(audit_package),
                "consensus_alert": build_consensus_alert(
                    audit_package,
                    build_round_log(audit_package),
                ),
                "scada_state": scada_state,
                "comparison_stage": {
                    "status": "completed",
                    "compact": format_scada_comparison_output_compact(comparison_output),
                },
                "comparison_output": comparison_output,
                "scada_alert": scada_alert,
                "persistence_stage": {
                    "status": "persisted",
                    **run_local_demo.build_minio_runtime_metadata(store),
                    "artifact_key": persistence_record.artifact_key,
                    "object_name": persistence_record.artifact_key,
                    "artifact_uri": f"minio://{bucket_name}/{persistence_record.artifact_key}",
                    "storage_action": "put_object",
                    "content_type": "application/json",
                    "write_confirmed": True,
                    "record": persistence_record.to_dict(),
                },
                "fault_edges": (),
                "fingerprint_stage": fingerprint_stage,
                "fingerprint_inference_results": inference_results,
                "edges": (),
            }

        try:
            with mock.patch.object(
                run_local_demo,
                "execute_demo_cycle",
                side_effect=cycle_executor,
            ):
                with mock.patch.object(run_local_demo, "print_cycle_report"):
                    payload = run_local_demo.run_autonomous_demo_loop(
                        config=config,
                        simulator=object(),
                        edges=(),
                        cometbft_client=object(),
                        artifact_store=store,
                        sleep_fn=lambda _: None,
                        monotonic_fn=mock.Mock(
                            side_effect=(0.0, 0.01, 1.0, 1.01, 2.0, 2.01, 3.0, 3.01)
                        ),
                    )

            self.assertEqual(payload["runtime"]["status"], "completed")
            self.assertEqual(payload["runtime"]["completed_cycles"], 4)
            self.assertEqual(len(payload["cycle_history"]), 4)
            self.assertEqual(
                payload["cycle_history"][0]["fingerprint_lifecycle"]["training_events"],
                ["deferred"],
            )
            self.assertEqual(
                payload["cycle_history"][1]["fingerprint_lifecycle"]["training_events"],
                ["deferred"],
            )
            self.assertEqual(
                payload["cycle_history"][2]["fingerprint_lifecycle"]["training_events"],
                ["started", "completed"],
            )
            self.assertEqual(
                payload["cycle_history"][3]["fingerprint_lifecycle"]["training_events"],
                ["reused"],
            )
            self.assertEqual(
                payload["cycle_history"][3]["fingerprint_lifecycle"]["inference_status"],
                "completed",
            )

            valid_artifact_keys = store.list_json_objects(prefix="valid-consensus-artifacts/")
            model_metadata_keys = store.list_json_objects(prefix="fingerprint-models/")
            dataset_manifest_keys = store.list_json_objects(prefix="fingerprint-datasets/")
            self.assertEqual(len(valid_artifact_keys), 4)
            self.assertEqual(len(model_metadata_keys), 1)
            self.assertGreaterEqual(len(dataset_manifest_keys), 2)

            saved_log = json.loads(log_path.read_text(encoding="utf-8"))
            self.assertEqual(saved_log["runtime"]["status"], "completed")
            self.assertEqual(saved_log["runtime"]["completed_cycles"], 4)
            self.assertEqual(
                saved_log["latest_cycle"]["fingerprint_lifecycle"]["training_events"],
                ["reused"],
            )
            self.assertEqual(
                saved_log["latest_cycle"]["fingerprint_lifecycle"]["model_status"],
                "model_available",
            )
            self.assertEqual(
                saved_log["latest_cycle"]["fingerprint_inference_results"][0][
                    "output_channel"
                ],
                "lstm_fingerprint",
            )
        finally:
            log_path.unlink(missing_ok=True)


if __name__ == "__main__":
    unittest.main()
