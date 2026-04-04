import os
import unittest
from unittest import mock

from parallel_truth_fingerprint.config.runtime import load_runtime_demo_config
from parallel_truth_fingerprint.edge_nodes.common.mqtt_io import PassiveMqttRelay


class RuntimeDemoConfigTest(unittest.TestCase):
    def test_runtime_demo_config_reads_environment(self) -> None:
        previous_transport = os.environ.get("MQTT_TRANSPORT")
        previous_steps = os.environ.get("DEMO_STEPS")
        previous_fault_mode = os.environ.get("DEMO_FAULT_MODE")
        previous_faulty_edges = os.environ.get("DEMO_FAULTY_EDGES")
        previous_rpc = os.environ.get("COMETBFT_RPC_URL")
        previous_cycle_interval = os.environ.get("DEMO_CYCLE_INTERVAL_SECONDS")
        previous_max_cycles = os.environ.get("DEMO_MAX_CYCLES")
        previous_train_after_cycles = os.environ.get(
            "DEMO_TRAIN_AFTER_ELIGIBLE_CYCLES"
        )
        previous_sequence_length = os.environ.get("DEMO_FINGERPRINT_SEQUENCE_LENGTH")
        previous_dashboard_host = os.environ.get("DEMO_DASHBOARD_HOST")
        previous_dashboard_port = os.environ.get("DEMO_DASHBOARD_PORT")
        previous_scenario_name = os.environ.get("DEMO_SCENARIO")
        previous_scenario_start_cycle = os.environ.get("DEMO_SCENARIO_START_CYCLE")
        previous_scada_mode = os.environ.get("DEMO_SCADA_MODE")
        previous_scada_start_cycle = os.environ.get("DEMO_SCADA_START_CYCLE")
        previous_scada_offset = os.environ.get("DEMO_SCADA_OFFSET_VALUE")
        previous_minio_endpoint = os.environ.get("MINIO_ENDPOINT")
        previous_minio_access_key = os.environ.get("MINIO_ACCESS_KEY")
        previous_minio_secret_key = os.environ.get("MINIO_SECRET_KEY")
        previous_minio_bucket = os.environ.get("MINIO_BUCKET")
        previous_minio_secure = os.environ.get("MINIO_SECURE")
        previous_log_path = os.environ.get("DEMO_LOG_PATH")
        try:
            os.environ["MQTT_TRANSPORT"] = "passive"
            os.environ["DEMO_STEPS"] = "5"
            os.environ["DEMO_FAULT_MODE"] = "single_edge_exclusion"
            os.environ["DEMO_FAULTY_EDGES"] = "edge-3"
            os.environ["COMETBFT_RPC_URL"] = "http://127.0.0.1:26657"
            os.environ["DEMO_CYCLE_INTERVAL_SECONDS"] = "75"
            os.environ["DEMO_MAX_CYCLES"] = "4"
            os.environ["DEMO_TRAIN_AFTER_ELIGIBLE_CYCLES"] = "12"
            os.environ["DEMO_FINGERPRINT_SEQUENCE_LENGTH"] = "3"
            os.environ["DEMO_DASHBOARD_HOST"] = "0.0.0.0"
            os.environ["DEMO_DASHBOARD_PORT"] = "9099"
            os.environ["DEMO_SCENARIO"] = "scada_replay"
            os.environ["DEMO_SCENARIO_START_CYCLE"] = "8"
            os.environ["DEMO_SCADA_MODE"] = "replay"
            os.environ["DEMO_SCADA_START_CYCLE"] = "7"
            os.environ["DEMO_SCADA_OFFSET_VALUE"] = "8.5"
            os.environ["MINIO_ENDPOINT"] = "127.0.0.1:9000"
            os.environ["MINIO_ACCESS_KEY"] = "demo-user"
            os.environ["MINIO_SECRET_KEY"] = "demo-secret"
            os.environ["MINIO_BUCKET"] = "demo-bucket"
            os.environ["MINIO_SECURE"] = "true"
            os.environ["DEMO_LOG_PATH"] = "logs/custom-demo.log"

            config = load_runtime_demo_config()

            self.assertEqual(config.mqtt_transport, "passive")
            self.assertEqual(config.demo_steps, 5)
            self.assertEqual(config.demo_fault_mode, "single_edge_exclusion")
            self.assertEqual(config.demo_faulty_edges, ("edge-3",))
            self.assertEqual(config.cometbft_rpc_url, "http://127.0.0.1:26657")
            self.assertEqual(config.demo_cycle_interval_seconds, 75.0)
            self.assertEqual(config.demo_max_cycles, 4)
            self.assertEqual(config.demo_train_after_eligible_cycles, 12)
            self.assertEqual(config.demo_fingerprint_sequence_length, 3)
            self.assertEqual(config.demo_dashboard_host, "0.0.0.0")
            self.assertEqual(config.demo_dashboard_port, 9099)
            self.assertEqual(config.demo_scenario_name, "scada_replay")
            self.assertEqual(config.demo_scenario_start_cycle, 8)
            self.assertEqual(config.demo_scada_mode, "replay")
            self.assertEqual(config.demo_scada_start_cycle, 7)
            self.assertEqual(config.demo_scada_offset_value, 8.5)
            self.assertEqual(config.minio_endpoint, "127.0.0.1:9000")
            self.assertEqual(config.minio_access_key, "demo-user")
            self.assertEqual(config.minio_secret_key, "demo-secret")
            self.assertEqual(config.minio_bucket, "demo-bucket")
            self.assertTrue(config.minio_secure)
            self.assertEqual(config.demo_log_path, "logs/custom-demo.log")
        finally:
            if previous_transport is None:
                os.environ.pop("MQTT_TRANSPORT", None)
            else:
                os.environ["MQTT_TRANSPORT"] = previous_transport
            if previous_steps is None:
                os.environ.pop("DEMO_STEPS", None)
            else:
                os.environ["DEMO_STEPS"] = previous_steps
            if previous_fault_mode is None:
                os.environ.pop("DEMO_FAULT_MODE", None)
            else:
                os.environ["DEMO_FAULT_MODE"] = previous_fault_mode
            if previous_faulty_edges is None:
                os.environ.pop("DEMO_FAULTY_EDGES", None)
            else:
                os.environ["DEMO_FAULTY_EDGES"] = previous_faulty_edges
            if previous_rpc is None:
                os.environ.pop("COMETBFT_RPC_URL", None)
            else:
                os.environ["COMETBFT_RPC_URL"] = previous_rpc
            if previous_cycle_interval is None:
                os.environ.pop("DEMO_CYCLE_INTERVAL_SECONDS", None)
            else:
                os.environ["DEMO_CYCLE_INTERVAL_SECONDS"] = previous_cycle_interval
            if previous_max_cycles is None:
                os.environ.pop("DEMO_MAX_CYCLES", None)
            else:
                os.environ["DEMO_MAX_CYCLES"] = previous_max_cycles
            if previous_train_after_cycles is None:
                os.environ.pop("DEMO_TRAIN_AFTER_ELIGIBLE_CYCLES", None)
            else:
                os.environ["DEMO_TRAIN_AFTER_ELIGIBLE_CYCLES"] = (
                    previous_train_after_cycles
                )
            if previous_sequence_length is None:
                os.environ.pop("DEMO_FINGERPRINT_SEQUENCE_LENGTH", None)
            else:
                os.environ["DEMO_FINGERPRINT_SEQUENCE_LENGTH"] = previous_sequence_length
            if previous_dashboard_host is None:
                os.environ.pop("DEMO_DASHBOARD_HOST", None)
            else:
                os.environ["DEMO_DASHBOARD_HOST"] = previous_dashboard_host
            if previous_dashboard_port is None:
                os.environ.pop("DEMO_DASHBOARD_PORT", None)
            else:
                os.environ["DEMO_DASHBOARD_PORT"] = previous_dashboard_port
            if previous_scenario_name is None:
                os.environ.pop("DEMO_SCENARIO", None)
            else:
                os.environ["DEMO_SCENARIO"] = previous_scenario_name
            if previous_scenario_start_cycle is None:
                os.environ.pop("DEMO_SCENARIO_START_CYCLE", None)
            else:
                os.environ["DEMO_SCENARIO_START_CYCLE"] = previous_scenario_start_cycle
            if previous_scada_mode is None:
                os.environ.pop("DEMO_SCADA_MODE", None)
            else:
                os.environ["DEMO_SCADA_MODE"] = previous_scada_mode
            if previous_scada_start_cycle is None:
                os.environ.pop("DEMO_SCADA_START_CYCLE", None)
            else:
                os.environ["DEMO_SCADA_START_CYCLE"] = previous_scada_start_cycle
            if previous_scada_offset is None:
                os.environ.pop("DEMO_SCADA_OFFSET_VALUE", None)
            else:
                os.environ["DEMO_SCADA_OFFSET_VALUE"] = previous_scada_offset
            if previous_minio_endpoint is None:
                os.environ.pop("MINIO_ENDPOINT", None)
            else:
                os.environ["MINIO_ENDPOINT"] = previous_minio_endpoint
            if previous_minio_access_key is None:
                os.environ.pop("MINIO_ACCESS_KEY", None)
            else:
                os.environ["MINIO_ACCESS_KEY"] = previous_minio_access_key
            if previous_minio_secret_key is None:
                os.environ.pop("MINIO_SECRET_KEY", None)
            else:
                os.environ["MINIO_SECRET_KEY"] = previous_minio_secret_key
            if previous_minio_bucket is None:
                os.environ.pop("MINIO_BUCKET", None)
            else:
                os.environ["MINIO_BUCKET"] = previous_minio_bucket
            if previous_minio_secure is None:
                os.environ.pop("MINIO_SECURE", None)
            else:
                os.environ["MINIO_SECURE"] = previous_minio_secure
            if previous_log_path is None:
                os.environ.pop("DEMO_LOG_PATH", None)
            else:
                os.environ["DEMO_LOG_PATH"] = previous_log_path


class AppTransportTest(unittest.TestCase):
    def test_passive_transport_is_usable_for_local_demo_wiring(self) -> None:
        from parallel_truth_fingerprint.app import create_transport, load_runtime_demo_config

        previous_transport = os.environ.get("MQTT_TRANSPORT")
        try:
            os.environ["MQTT_TRANSPORT"] = "passive"
            config = load_runtime_demo_config()

            transport = create_transport(config.mqtt_transport)

            self.assertIsInstance(transport, PassiveMqttRelay)
        finally:
            if previous_transport is None:
                os.environ.pop("MQTT_TRANSPORT", None)
            else:
                os.environ["MQTT_TRANSPORT"] = previous_transport


class DemoFormattingTest(unittest.TestCase):
    def test_default_faulty_edges_match_demo_modes(self) -> None:
        from scripts.run_local_demo import default_faulty_edges

        self.assertEqual(default_faulty_edges("none"), ())
        self.assertEqual(default_faulty_edges("single_edge_exclusion"), ("edge-3",))
        self.assertEqual(default_faulty_edges("quorum_loss"), ("edge-2", "edge-3"))

    def test_format_edge_summary_returns_compact_live_view(self) -> None:
        from scripts.run_local_demo import format_edge_summary

        class FakeEdge:
            def runtime_state(self):
                return {
                    "edge_id": "edge-1",
                    "published_observation_count": 3,
                    "peer_observation_count": 6,
                }

            def local_replicated_state(self):
                return {
                    "is_complete": True,
                    "is_validated": False,
                    "sensor_values": {
                        "pressure": 6.253,
                        "rpm": 3234.344,
                        "temperature": 78.254,
                    },
                }

        summary = format_edge_summary(FakeEdge())

        self.assertIn("edge-1:", summary)
        self.assertIn("published=3", summary)
        self.assertIn("consumed=6", summary)
        self.assertIn("complete=True", summary)
        self.assertIn("validated=False", summary)
        self.assertIn("temperature=78.254", summary)

    def test_default_demo_log_path_resolves_relative_and_absolute_paths(self) -> None:
        from scripts.run_local_demo import PROJECT_ROOT, default_demo_log_path

        relative = default_demo_log_path("logs/dev.log")
        absolute = default_demo_log_path(str(PROJECT_ROOT / "logs" / "abs.log"))

        self.assertEqual(relative, PROJECT_ROOT / "logs" / "dev.log")
        self.assertEqual(absolute, PROJECT_ROOT / "logs" / "abs.log")

    def test_build_demo_artifact_store_uses_minio_runtime_config(self) -> None:
        from parallel_truth_fingerprint.config.runtime import RuntimeDemoConfig
        from parallel_truth_fingerprint.persistence import MinioArtifactStore
        from scripts.run_local_demo import build_demo_artifact_store

        store = build_demo_artifact_store(
            RuntimeDemoConfig(
                mqtt_transport="passive",
                minio_endpoint="127.0.0.1:9000",
                minio_access_key="demo-user",
                minio_secret_key="demo-secret",
                minio_bucket="demo-bucket",
                minio_secure=True,
            )
        )

        self.assertIsInstance(store, MinioArtifactStore)
        self.assertEqual(store.config.endpoint, "127.0.0.1:9000")
        self.assertEqual(store.config.access_key, "demo-user")
        self.assertEqual(store.config.secret_key, "demo-secret")
        self.assertEqual(store.config.bucket, "demo-bucket")
        self.assertTrue(store.config.secure)

    def test_write_detailed_log_persists_json_payload(self) -> None:
        import json
        from pathlib import Path

        from scripts.run_local_demo import PROJECT_ROOT, write_detailed_log

        scratch_dir = PROJECT_ROOT / "tests" / "_tmp"
        path = scratch_dir / "demo.log"
        try:
            write_detailed_log(path, {"status": "ok", "items": [1, 2, 3]})
            payload = json.loads(path.read_text(encoding="utf-8"))

            self.assertEqual(payload["status"], "ok")
            self.assertEqual(payload["items"], [1, 2, 3])
        finally:
            if path.exists():
                path.unlink()
            if scratch_dir.exists():
                scratch_dir.rmdir()

    def test_format_round_summary_returns_compact_consensus_view(self) -> None:
        from parallel_truth_fingerprint.contracts.consensus_round_summary import (
            ConsensusRoundSummary,
            ExcludedEdgeSummary,
        )
        from parallel_truth_fingerprint.consensus.summary import format_round_summary
        from parallel_truth_fingerprint.contracts.consensus_status import ConsensusStatus

        summary = ConsensusRoundSummary(
            round_id="round-123",
            total_participants=3,
            quorum_required=2,
            valid_participants_after_exclusions=1,
            excluded_edge_ids=("edge-2", "edge-3"),
            exclusion_reasons=(
                "suspected_byzantine_behavior",
                "suspected_byzantine_behavior",
            ),
            excluded_edges=(
                ExcludedEdgeSummary(
                    edge_id="edge-2",
                    reason="suspected_byzantine_behavior",
                ),
                ExcludedEdgeSummary(
                    edge_id="edge-3",
                    reason="suspected_byzantine_behavior",
                ),
            ),
            final_consensus_status=ConsensusStatus.FAILED_CONSENSUS,
            has_consensused_valid_state=False,
        )

        formatted = format_round_summary(summary)

        self.assertIn("round-123:", formatted)
        self.assertIn("quorum=2", formatted)
        self.assertIn("status=failed_consensus", formatted)
        self.assertIn("valid_state=absent", formatted)

    def test_format_round_log_outputs_compact_and_detailed_views(self) -> None:
        from datetime import datetime, timedelta, timezone

        from parallel_truth_fingerprint.consensus.logging import (
            format_round_log_compact,
            format_round_log_detailed,
        )
        from parallel_truth_fingerprint.contracts.consensus_round_log import (
            ConsensusRoundLog,
        )
        from parallel_truth_fingerprint.contracts.consensus_status import ConsensusStatus
        from parallel_truth_fingerprint.contracts.exclusion_decision import ExclusionDecision
        from parallel_truth_fingerprint.contracts.exclusion_reason import ExclusionReason
        from parallel_truth_fingerprint.contracts.round_identity import RoundIdentity
        from parallel_truth_fingerprint.contracts.trust_evidence import (
            PairwiseDistanceEvidence,
            PerEdgeTrustEvidence,
            SensorDeviationEvidence,
        )
        from parallel_truth_fingerprint.contracts.trust_ranking import (
            TrustRankEntry,
            TrustRanking,
        )

        round_identity = RoundIdentity(
            round_id="round-456",
            window_started_at=datetime(2026, 3, 25, 12, 0, tzinfo=timezone.utc),
            window_ended_at=datetime(2026, 3, 25, 12, 1, tzinfo=timezone.utc),
        )
        round_log = ConsensusRoundLog(
            round_identity=round_identity,
            participating_edges=("edge-1", "edge-2", "edge-3"),
            trust_ranking=TrustRanking(
                round_identity=round_identity,
                participating_edges=("edge-1", "edge-2", "edge-3"),
                entries=(
                    TrustRankEntry(edge_id="edge-1", score=1.0),
                    TrustRankEntry(edge_id="edge-2", score=0.95),
                    TrustRankEntry(edge_id="edge-3", score=0.1),
                ),
            ),
            exclusions=(
                ExclusionDecision(
                    round_identity=round_identity,
                    edge_id="edge-3",
                    reason=ExclusionReason.SUSPECTED_BYZANTINE_BEHAVIOR,
                    detail="temperature:39.500",
                ),
            ),
            trust_evidence=(
                PerEdgeTrustEvidence(
                    round_identity=round_identity,
                    edge_id="edge-1",
                    score=1.0,
                    compatible_peer_count=2,
                    overall_normalized_deviation=0.0,
                    sensor_deviations=(
                        SensorDeviationEvidence(
                            sensor_name="temperature",
                            deviation_value=0.0,
                            unit="degC",
                        ),
                    ),
                    pairwise_distances=(
                        PairwiseDistanceEvidence(
                            peer_edge_id="edge-2",
                            sensor_name="temperature",
                            distance_value=0.0,
                            unit="degC",
                        ),
                    ),
                ),
            ),
            final_status=ConsensusStatus.SUCCESS,
            consensused_valid_state=None,
        )

        compact = format_round_log_compact(round_log)
        detailed = format_round_log_detailed(round_log)

        self.assertIn("round-456:", compact)
        self.assertIn("exclusions[edge-3:suspected_byzantine_behavior]", compact)
        self.assertIn("round=round-456", detailed)
        self.assertIn("edge=edge-1 score=1.000", detailed)
        self.assertIn("compatible_peers=2", detailed)
        self.assertIn("excluded=edge-3 reason=suspected_byzantine_behavior", detailed)

    def test_format_consensus_alert_outputs_none_and_failed_views(self) -> None:
        from datetime import datetime, timedelta, timezone

        from parallel_truth_fingerprint.consensus.alerts import (
            format_consensus_alert_compact,
            format_consensus_alert_detailed,
        )
        from parallel_truth_fingerprint.contracts.consensus_alert import (
            ConsensusAlert,
            ConsensusAlertType,
        )
        from parallel_truth_fingerprint.contracts.consensus_status import ConsensusStatus
        from parallel_truth_fingerprint.contracts.exclusion_decision import ExclusionDecision
        from parallel_truth_fingerprint.contracts.exclusion_reason import ExclusionReason
        from parallel_truth_fingerprint.contracts.round_identity import RoundIdentity
        from parallel_truth_fingerprint.contracts.trust_evidence import (
            PairwiseDistanceEvidence,
            PerEdgeTrustEvidence,
            SensorDeviationEvidence,
        )

        round_identity = RoundIdentity(
            round_id="round-789",
            window_started_at=datetime(2026, 3, 25, 12, 0, tzinfo=timezone.utc),
            window_ended_at=datetime(2026, 3, 25, 12, 1, tzinfo=timezone.utc),
        )
        alert = ConsensusAlert(
            alert_type=ConsensusAlertType.CONSENSUS_FAILED,
            round_identity=round_identity,
            final_status=ConsensusStatus.FAILED_CONSENSUS,
            exclusions=(
                ExclusionDecision(
                    round_identity=round_identity,
                    edge_id="edge-2",
                    reason=ExclusionReason.SUSPECTED_BYZANTINE_BEHAVIOR,
                    detail="temperature:70.000",
                ),
            ),
            trust_evidence=(
                PerEdgeTrustEvidence(
                    round_identity=round_identity,
                    edge_id="edge-2",
                    score=0.0,
                    compatible_peer_count=0,
                    overall_normalized_deviation=1.5,
                    sensor_deviations=(
                        SensorDeviationEvidence(
                            sensor_name="temperature",
                            deviation_value=70.0,
                            unit="degC",
                        ),
                    ),
                    pairwise_distances=(
                        PairwiseDistanceEvidence(
                            peer_edge_id="edge-1",
                            sensor_name="temperature",
                            distance_value=70.0,
                            unit="degC",
                        ),
                    ),
                ),
            ),
        )

        self.assertEqual(format_consensus_alert_compact(None), "none")
        self.assertEqual(format_consensus_alert_detailed(None), "consensus_alert=none")
        self.assertIn("alert=consensus_failed", format_consensus_alert_compact(alert))
        self.assertIn("alert_type=consensus_failed", format_consensus_alert_detailed(alert))

    def test_format_comparison_and_persistence_stage_outputs(self) -> None:
        from scripts.run_local_demo import (
            build_dataset_context,
            format_comparison_stage_compact,
            format_persistence_stage_compact,
        )

        comparison_completed = {
            "status": "completed",
            "compact": "round-1: scada_source=round-1 outputs[temperature=match]",
        }
        comparison_blocked = {
            "status": "blocked",
            "reason": "no_consensused_valid_state",
            "compact": None,
        }
        persistence_persisted = {
            "status": "persisted",
            "backend": "minio",
            "endpoint": "localhost:9000",
            "secure": False,
            "bucket": "valid-consensus-artifacts",
            "artifact_key": "valid-consensus-artifacts/round-1.json",
            "artifact_uri": "minio://valid-consensus-artifacts/valid-consensus-artifacts/round-1.json",
        }
        persistence_blocked = {
            "status": "blocked",
            "backend": "minio",
            "endpoint": "localhost:9000",
            "secure": False,
            "bucket": "valid-consensus-artifacts",
            "reason": "no_consensused_valid_state",
        }
        persistence_error = {
            "status": "error",
            "backend": "minio",
            "endpoint": "localhost:9000",
            "secure": False,
            "bucket": "valid-consensus-artifacts",
            "reason": "MinIO unavailable",
        }

        self.assertIn(
            "scada_source=round-1",
            format_comparison_stage_compact(comparison_completed),
        )
        self.assertEqual(
            format_comparison_stage_compact(comparison_blocked),
            "comparison=blocked stage=comparison reason=no_consensused_valid_state",
        )
        self.assertIn(
            "backend=minio",
            format_persistence_stage_compact(persistence_persisted),
        )
        self.assertIn(
            "endpoint=localhost:9000",
            format_persistence_stage_compact(persistence_persisted),
        )
        self.assertIn(
            "secure=false",
            format_persistence_stage_compact(persistence_persisted),
        )
        self.assertIn(
            "bucket=valid-consensus-artifacts",
            format_persistence_stage_compact(persistence_persisted),
        )
        self.assertIn(
            "artifact_key=valid-consensus-artifacts/round-1.json",
            format_persistence_stage_compact(persistence_persisted),
        )
        self.assertIn(
            "artifact_uri=minio://valid-consensus-artifacts/valid-consensus-artifacts/round-1.json",
            format_persistence_stage_compact(persistence_persisted),
        )
        self.assertEqual(
            format_persistence_stage_compact(persistence_blocked),
            (
                "persistence=blocked backend=minio endpoint=localhost:9000 "
                "secure=false bucket=valid-consensus-artifacts "
                "stage=persistence "
                "reason=no_consensused_valid_state"
            ),
        )
        self.assertEqual(
            format_persistence_stage_compact(persistence_error),
            (
                "persistence=error backend=minio endpoint=localhost:9000 "
                "secure=false bucket=valid-consensus-artifacts "
                "reason=MinIO unavailable"
            ),
        )
        comparison_output = type("ComparisonOutput", (), {"divergent_sensors": ()})()
        dataset_context = build_dataset_context(
            fault_mode="none",
            comparison_output=comparison_output,
        )
        self.assertEqual(dataset_context["scenario_label"], "normal")
        self.assertEqual(dataset_context["training_label"], "normal")
        self.assertTrue(dataset_context["training_eligible"])
        replay_stage = type(
            "ReplayStage",
            (),
            {"active": True, "mode": "replay"},
        )()
        replay_context = build_dataset_context(
            fault_mode="none",
            comparison_output=comparison_output,
            scada_replay_stage=replay_stage,
        )
        self.assertEqual(replay_context["scenario_label"], "scada_replay")
        self.assertEqual(replay_context["training_label"], "non_normal")
        self.assertFalse(replay_context["training_eligible"])
        scenario_stage = type(
            "ScenarioStage",
            (),
            {
                "scenario_label": "faulty_edge_exclusion",
                "training_label": "non_normal",
                "training_eligible": False,
                "training_eligibility_reason": "faulty_edge_exclusion",
            },
        )()
        scenario_context = build_dataset_context(
            fault_mode="single_edge_exclusion",
            comparison_output=comparison_output,
            scenario_control_stage=scenario_stage,
        )
        self.assertEqual(scenario_context["scenario_label"], "faulty_edge_exclusion")
        self.assertEqual(scenario_context["training_label"], "non_normal")
        self.assertFalse(scenario_context["training_eligible"])

    def test_format_cadence_and_fingerprint_lifecycle_outputs(self) -> None:
        from parallel_truth_fingerprint.lstm_service import FingerprintLifecycleStage
        from parallel_truth_fingerprint.lstm_service import ScadaReplayRuntimeStage
        from parallel_truth_fingerprint.scenario_control import RuntimeScenarioControlStage
        from scripts.run_local_demo import (
            build_cadence_stage,
            format_cadence_stage_compact,
            format_fingerprint_lifecycle_compact,
            format_replay_behavior_compact,
            format_scenario_control_compact,
            format_scada_runtime_scenario_compact,
        )
        from parallel_truth_fingerprint.contracts.fingerprint_inference import (
            FingerprintInferenceClassification,
        )
        from parallel_truth_fingerprint.contracts.replay_behavior import ReplayBehaviorResult

        cadence_stage = build_cadence_stage(
            cycle_index=3,
            configured_interval_seconds=60.0,
            elapsed_seconds=2.5,
            next_sleep_seconds=57.5,
            will_continue=True,
        )
        fingerprint_stage = FingerprintLifecycleStage(
            cycle_index=3,
            valid_artifact_count=3,
            eligible_history_count=3,
            eligible_history_threshold=10,
            window_count=2,
            latest_valid_artifact_key="valid-consensus-artifacts/round-3.json",
            model_status="model_available",
            training_events=("reused",),
            inference_status="completed",
            inference_result_count=2,
            dataset_manifest_object_key="fingerprint-datasets/runtime.manifest.json",
            model_metadata_object_key="fingerprint-models/runtime.json",
            source_dataset_validation_level="runtime_valid_only",
        )

        self.assertIn("cycle=3", format_cadence_stage_compact(cadence_stage))
        self.assertIn("interval_seconds=60.0", format_cadence_stage_compact(cadence_stage))
        lifecycle_text = format_fingerprint_lifecycle_compact(fingerprint_stage)
        self.assertIn("model_status=model_available", lifecycle_text)
        self.assertIn("training=reused", lifecycle_text)
        self.assertIn("eligible_history=3/10", lifecycle_text)
        self.assertIn("validation_level=runtime_valid_only", lifecycle_text)
        scenario_stage = RuntimeScenarioControlStage(
            configured_scenario="scada_replay",
            active_scenario="scada_replay",
            start_cycle=4,
            active=True,
            fault_mode="none",
            scada_mode="replay",
            scenario_label="scada_replay",
            training_label="non_normal",
            training_eligible=False,
            training_eligibility_reason="scada_replay",
            expected_output_channels=(
                "consensus_alert",
                "persistence_stage",
                "replay_behavior",
                "fingerprint_inference",
            ),
        )
        scenario_text = format_scenario_control_compact(scenario_stage)
        self.assertIn("configured=scada_replay", scenario_text)
        self.assertIn("current=scada_replay", scenario_text)
        self.assertIn("training_eligible=false", scenario_text)
        self.assertIn(
            "expected_outputs=consensus_alert,persistence_stage,replay_behavior,fingerprint_inference",
            scenario_text,
        )
        replay_stage = ScadaReplayRuntimeStage(
            active=True,
            mode="replay",
            start_cycle=4,
            replay_source_round_id="round-001",
        )
        replay_result = ReplayBehaviorResult(
            output_channel="scada_replay_behavior",
            scenario_mode="replay",
            current_round_id="round-004",
            scada_source_round_id="round-004",
            replay_source_round_id="round-001",
            model_id="model-001",
            source_dataset_id="training-dataset::round-001::round-003::seq-2",
            inference_dataset_id="replay-dataset::round-004::replay::round-001::seq-2",
            source_dataset_validation_level="runtime_valid_only",
            limitation_note="runtime-valid only",
            window_id="replay-window::round-004::round-001",
            artifact_keys=(
                "valid-consensus-artifacts/round-003.json",
                "valid-consensus-artifacts/round-001.json",
            ),
            anomaly_score=0.25,
            classification_threshold=0.05,
            classification=FingerprintInferenceClassification.ANOMALOUS,
            scada_divergent_sensors=("temperature",),
            consensus_final_status="success",
        )
        self.assertIn(
            "mode=replay",
            format_scada_runtime_scenario_compact(replay_stage),
        )
        replay_text = format_replay_behavior_compact(replay_result)
        self.assertIn("replay_behavior=completed", replay_text)
        self.assertIn("classification=anomalous", replay_text)
        self.assertIn("replay_source_round_id=round-001", replay_text)

    def test_run_autonomous_demo_loop_executes_multiple_cycles_and_respects_cadence(
        self,
    ) -> None:
        from parallel_truth_fingerprint.config.runtime import RuntimeDemoConfig
        from scripts import run_local_demo

        config = RuntimeDemoConfig(
            mqtt_transport="passive",
            demo_cycle_interval_seconds=5.0,
            demo_max_cycles=2,
        )
        base_cycle_result = {
            "simulator_snapshot": None,
            "node_status": {},
            "commit_receipt": object(),
            "committed_round": {},
            "consensus_summary": object(),
            "consensus_log": object(),
            "consensus_alert": None,
            "scada_state": None,
            "comparison_stage": {},
            "comparison_output": None,
            "scada_alert": None,
            "persistence_stage": {},
            "scenario_control_stage": mock.Mock(to_dict=mock.Mock(return_value={})),
            "scada_replay_stage": mock.Mock(to_dict=mock.Mock(return_value={})),
            "fingerprint_stage": object(),
            "fingerprint_inference_results": (),
            "replay_behavior_result": None,
            "replay_inference_results": (),
            "edges": (),
            "fault_edges": (),
        }
        cycle_results = (
            {"cycle_index": 1, **base_cycle_result},
            {"cycle_index": 2, **base_cycle_result},
        )
        sleep_mock = mock.Mock()

        with mock.patch.object(
            run_local_demo,
            "execute_demo_cycle",
            side_effect=cycle_results,
        ) as execute_cycle:
            with mock.patch.object(
                run_local_demo,
                "build_detailed_log_payload",
                side_effect=lambda **kwargs: {
                    "fingerprint_lifecycle": {
                        "model_status": "no_model_yet",
                        "training_events": ["deferred"],
                        "valid_artifact_count": kwargs["cycle_index"],
                        "eligible_history_count": kwargs["cycle_index"],
                        "window_count": 0,
                    }
                },
            ) as build_payload:
                with mock.patch.object(
                    run_local_demo,
                    "build_cycle_history_entry",
                    side_effect=lambda **kwargs: {
                        "cycle_index": kwargs["cycle_result"]["cycle_index"]
                    },
                ) as build_history:
                    with mock.patch.object(
                        run_local_demo,
                        "write_detailed_log",
                        return_value=run_local_demo.PROJECT_ROOT / "logs" / "loop.log",
                    ) as write_log:
                        with mock.patch.object(
                            run_local_demo,
                            "print_cycle_report",
                        ) as print_report:
                            payload = run_local_demo.run_autonomous_demo_loop(
                                config=config,
                                simulator=object(),
                                edges=(),
                                cometbft_client=object(),
                                artifact_store=object(),
                                scada_service=object(),
                                sleep_fn=sleep_mock,
                                monotonic_fn=mock.Mock(
                                    side_effect=(0.0, 0.25, 5.0, 5.5)
                                ),
                            )

        self.assertEqual(execute_cycle.call_count, 2)
        self.assertEqual(build_payload.call_count, 2)
        self.assertEqual(build_history.call_count, 2)
        self.assertEqual(write_log.call_count, 2)
        self.assertEqual(print_report.call_count, 2)
        sleep_mock.assert_called_once_with(4.75)
        self.assertEqual(payload["runtime"]["status"], "completed")
        self.assertEqual(payload["runtime"]["completed_cycles"], 2)

    def test_run_autonomous_demo_loop_marks_manual_stop_when_interrupted(self) -> None:
        from parallel_truth_fingerprint.config.runtime import RuntimeDemoConfig
        from scripts import run_local_demo

        config = RuntimeDemoConfig(
            mqtt_transport="passive",
            demo_cycle_interval_seconds=5.0,
            demo_max_cycles=0,
        )
        cycle_result = {
            "cycle_index": 1,
            "simulator_snapshot": None,
            "node_status": {},
            "commit_receipt": object(),
            "committed_round": {},
            "consensus_summary": object(),
            "consensus_log": object(),
            "consensus_alert": None,
            "scada_state": None,
            "comparison_stage": {},
            "comparison_output": None,
            "scada_alert": None,
            "persistence_stage": {},
            "scenario_control_stage": mock.Mock(to_dict=mock.Mock(return_value={})),
            "scada_replay_stage": mock.Mock(to_dict=mock.Mock(return_value={})),
            "fingerprint_stage": object(),
            "fingerprint_inference_results": (),
            "replay_behavior_result": None,
            "replay_inference_results": (),
            "edges": (),
            "fault_edges": (),
        }

        with mock.patch.object(
            run_local_demo,
            "execute_demo_cycle",
            return_value=cycle_result,
        ):
            with mock.patch.object(
                run_local_demo,
                "build_detailed_log_payload",
                return_value={
                    "fingerprint_lifecycle": {
                        "model_status": "no_model_yet",
                        "training_events": ["deferred"],
                        "valid_artifact_count": 1,
                        "eligible_history_count": 1,
                        "window_count": 0,
                    }
                },
            ):
                with mock.patch.object(
                    run_local_demo,
                    "build_cycle_history_entry",
                    return_value={"cycle_index": 1},
                ):
                    with mock.patch.object(
                        run_local_demo,
                        "write_detailed_log",
                        return_value=run_local_demo.PROJECT_ROOT / "logs" / "loop.log",
                    ) as write_log:
                        with mock.patch.object(
                            run_local_demo,
                            "print_cycle_report",
                        ):
                            payload = run_local_demo.run_autonomous_demo_loop(
                                config=config,
                                simulator=object(),
                                edges=(),
                                cometbft_client=object(),
                                artifact_store=object(),
                                scada_service=object(),
                                sleep_fn=mock.Mock(side_effect=KeyboardInterrupt),
                                monotonic_fn=mock.Mock(side_effect=(0.0, 0.2)),
                            )

        self.assertEqual(payload["runtime"]["status"], "stopped_manually")
        self.assertEqual(payload["runtime"]["completed_cycles"], 1)
        self.assertEqual(write_log.call_count, 2)

    def test_build_minio_runtime_metadata_splits_endpoint_and_secure_mode(self) -> None:
        from parallel_truth_fingerprint.persistence import MinioArtifactStore, MinioStoreConfig
        from scripts.run_local_demo import build_minio_runtime_metadata
        from tests.persistence.test_service import FakeMinioClient

        artifact_store = MinioArtifactStore(
            MinioStoreConfig(
                endpoint="127.0.0.1:9000",
                access_key="minioadmin",
                secret_key="minioadmin",
                bucket="valid-consensus-artifacts",
                secure=False,
            ),
            client=FakeMinioClient(),
        )

        metadata = build_minio_runtime_metadata(artifact_store)

        self.assertEqual(metadata["backend"], "minio")
        self.assertEqual(metadata["endpoint"], "127.0.0.1:9000")
        self.assertEqual(metadata["host"], "127.0.0.1")
        self.assertEqual(metadata["port"], 9000)
        self.assertFalse(metadata["secure"])
        self.assertEqual(metadata["bucket"], "valid-consensus-artifacts")

    def test_run_scada_comparison_and_persistence_blocks_without_valid_state(self) -> None:
        from parallel_truth_fingerprint.contracts.consensus_audit_package import (
            ConsensusAuditPackage,
        )
        from parallel_truth_fingerprint.contracts.consensus_result import ConsensusResult
        from parallel_truth_fingerprint.contracts.consensus_round_input import (
            ConsensusRoundInput,
        )
        from parallel_truth_fingerprint.contracts.consensus_status import ConsensusStatus
        from parallel_truth_fingerprint.contracts.exclusion_decision import (
            ExclusionDecision,
        )
        from parallel_truth_fingerprint.contracts.exclusion_reason import ExclusionReason
        from parallel_truth_fingerprint.contracts.round_identity import RoundIdentity
        from parallel_truth_fingerprint.contracts.trust_ranking import (
            TrustRankEntry,
            TrustRanking,
        )
        from parallel_truth_fingerprint.persistence import (
            MinioArtifactStore,
            MinioStoreConfig,
        )
        from scripts.run_local_demo import run_scada_comparison_and_persistence
        from tests.persistence.test_service import FakeMinioClient
        from datetime import datetime, timedelta, timezone

        round_identity = RoundIdentity(
            round_id="round-blocked",
            window_started_at=datetime(2026, 4, 1, 16, 0, tzinfo=timezone.utc),
            window_ended_at=datetime(2026, 4, 1, 16, 1, tzinfo=timezone.utc),
        )
        audit_package = ConsensusAuditPackage(
            round_input=ConsensusRoundInput(
                round_identity=round_identity,
                participating_edges=("edge-1", "edge-2", "edge-3"),
                replicated_states=(),
            ),
            trust_ranking=TrustRanking(
                round_identity=round_identity,
                participating_edges=("edge-1", "edge-2", "edge-3"),
                entries=(
                    TrustRankEntry(edge_id="edge-1", score=0.9),
                    TrustRankEntry(edge_id="edge-2", score=0.2),
                    TrustRankEntry(edge_id="edge-3", score=0.1),
                ),
            ),
            exclusions=(),
            trust_evidence=(),
            final_status=ConsensusStatus.FAILED_CONSENSUS,
            consensus_result=ConsensusResult(
                round_identity=round_identity,
                status=ConsensusStatus.FAILED_CONSENSUS,
                participating_edges=("edge-1", "edge-2", "edge-3"),
                trust_ranking=TrustRanking(
                    round_identity=round_identity,
                    participating_edges=("edge-1", "edge-2", "edge-3"),
                    entries=(
                        TrustRankEntry(edge_id="edge-1", score=0.9),
                        TrustRankEntry(edge_id="edge-2", score=0.2),
                        TrustRankEntry(edge_id="edge-3", score=0.1),
                    ),
                ),
                exclusions=(),
                consensused_valid_state=None,
            ),
            consensused_valid_state=None,
        )
        artifact_store = MinioArtifactStore(
            MinioStoreConfig(
                endpoint="localhost:9000",
                access_key="minioadmin",
                secret_key="minioadmin",
                bucket="valid-consensus-artifacts",
            ),
            client=FakeMinioClient(),
        )

        scada_state, comparison_stage, comparison_output, scada_alert, persistence_stage = (
            run_scada_comparison_and_persistence(
                consensus_audit=audit_package,
                artifact_store=artifact_store,
            )
        )
        self.assertIsNone(scada_state)
        self.assertIsNone(comparison_output)
        self.assertIsNone(scada_alert)
        self.assertEqual(comparison_stage["status"], "blocked")
        self.assertEqual(comparison_stage["reason"], "no_consensused_valid_state")
        self.assertFalse(comparison_stage["downstream_permitted"])
        self.assertEqual(persistence_stage["status"], "blocked")
        self.assertEqual(persistence_stage["reason"], "no_consensused_valid_state")
        self.assertEqual(persistence_stage["backend"], "minio")
        self.assertEqual(persistence_stage["endpoint"], "localhost:9000")
        self.assertEqual(persistence_stage["host"], "localhost")
        self.assertEqual(persistence_stage["port"], 9000)
        self.assertFalse(persistence_stage["secure"])
        self.assertEqual(persistence_stage["bucket"], "valid-consensus-artifacts")
        self.assertFalse(persistence_stage["write_confirmed"])

    def test_run_scada_comparison_and_persistence_persists_minio_artifact(self) -> None:
        from parallel_truth_fingerprint.persistence import (
            MinioArtifactStore,
            MinioStoreConfig,
        )
        from scripts.run_local_demo import run_scada_comparison_and_persistence
        from tests.persistence.test_service import FakeMinioClient

        from tests.persistence.test_service import build_valid_audit_package
        fake_client = FakeMinioClient()
        artifact_store = MinioArtifactStore(
            MinioStoreConfig(
                endpoint="localhost:9000",
                access_key="minioadmin",
                secret_key="minioadmin",
                bucket="valid-consensus-artifacts",
            ),
            client=fake_client,
        )

        audit_package = build_valid_audit_package()
        scada_state, comparison_stage, comparison_output, scada_alert, persistence_stage = (
            run_scada_comparison_and_persistence(
                consensus_audit=audit_package,
                artifact_store=artifact_store,
            )
        )

        self.assertIsNotNone(scada_state)
        self.assertIsNotNone(comparison_output)
        self.assertEqual(comparison_stage["status"], "completed")
        self.assertTrue(comparison_stage["downstream_permitted"])
        self.assertEqual(persistence_stage["status"], "persisted")
        self.assertTrue(persistence_stage["downstream_permitted"])
        self.assertEqual(persistence_stage["backend"], "minio")
        self.assertEqual(persistence_stage["endpoint"], "localhost:9000")
        self.assertEqual(persistence_stage["host"], "localhost")
        self.assertEqual(persistence_stage["port"], 9000)
        self.assertFalse(persistence_stage["secure"])
        self.assertEqual(persistence_stage["bucket"], "valid-consensus-artifacts")
        self.assertEqual(
            persistence_stage["object_name"],
            persistence_stage["artifact_key"],
        )
        self.assertTrue(
            persistence_stage["artifact_uri"].startswith(
                "minio://valid-consensus-artifacts/"
            )
        )
        self.assertEqual(persistence_stage["storage_action"], "put_object")
        self.assertEqual(persistence_stage["content_type"], "application/json")
        self.assertTrue(persistence_stage["write_confirmed"])
        self.assertIn("artifact_identity", persistence_stage["record"])
        self.assertIn("consensus_context", persistence_stage["record"])
        self.assertIn("validated_state", persistence_stage["record"])
        self.assertIn("dataset_context", persistence_stage["record"])
        self.assertIn("scada_context", persistence_stage["record"])
        self.assertIn(
            "structured_payload_snapshot",
            persistence_stage["record"]["validated_state"],
        )
        self.assertEqual(
            persistence_stage["record"]["dataset_context"]["scenario_label"],
            "normal",
        )
        self.assertTrue(
            persistence_stage["record"]["dataset_context"]["training_eligible"]
        )
        self.assertIn(
            ("valid-consensus-artifacts", persistence_stage["artifact_key"]),
            fake_client.objects,
        )

    def test_run_scada_comparison_and_persistence_reports_minio_runtime_errors(self) -> None:
        from scripts.run_local_demo import run_scada_comparison_and_persistence
        from tests.persistence.test_service import build_valid_audit_package

        class FailingStore:
            config = type(
                "Config",
                (),
                {
                    "endpoint": "localhost:9000",
                    "bucket": "valid-consensus-artifacts",
                },
            )()

            def save_json(self, object_name: str, payload: dict[str, object]) -> str:
                raise ConnectionError("MinIO connection refused")

        audit_package = build_valid_audit_package()
        _, _, comparison_output, _, persistence_stage = (
            run_scada_comparison_and_persistence(
                consensus_audit=audit_package,
                artifact_store=FailingStore(),
            )
        )

        self.assertIsNotNone(comparison_output)
        self.assertEqual(persistence_stage["status"], "error")
        self.assertEqual(persistence_stage["backend"], "minio")
        self.assertEqual(persistence_stage["endpoint"], "localhost:9000")
        self.assertEqual(persistence_stage["host"], "localhost")
        self.assertEqual(persistence_stage["port"], 9000)
        self.assertFalse(persistence_stage["secure"])
        self.assertEqual(persistence_stage["bucket"], "valid-consensus-artifacts")
        self.assertEqual(persistence_stage["reason"], "MinIO connection refused")
        self.assertFalse(persistence_stage["write_confirmed"])

    def test_run_scada_comparison_and_persistence_blocks_downstream_on_scada_divergence(self) -> None:
        from parallel_truth_fingerprint.persistence import (
            MinioArtifactStore,
            MinioStoreConfig,
        )
        from parallel_truth_fingerprint.scada import FakeOpcUaScadaService
        from scripts.run_local_demo import run_scada_comparison_and_persistence
        from tests.persistence.test_service import FakeMinioClient
        from tests.persistence.test_service import build_valid_audit_package

        fake_client = FakeMinioClient()
        artifact_store = MinioArtifactStore(
            MinioStoreConfig(
                endpoint="localhost:9000",
                access_key="minioadmin",
                secret_key="minioadmin",
                bucket="valid-consensus-artifacts",
            ),
            client=fake_client,
        )
        scada_service = FakeOpcUaScadaService(compressor_id="compressor-1")
        scada_service.set_sensor_override("temperature", mode="offset", offset=12.0)

        audit_package = build_valid_audit_package()
        scada_state, comparison_stage, comparison_output, scada_alert, persistence_stage = (
            run_scada_comparison_and_persistence(
                consensus_audit=audit_package,
                artifact_store=artifact_store,
                scada_service=scada_service,
            )
        )

        self.assertIsNotNone(scada_state)
        self.assertIsNotNone(comparison_output)
        self.assertIsNotNone(scada_alert)
        self.assertEqual(comparison_stage["status"], "blocked_downstream")
        self.assertEqual(comparison_stage["reason"], "scada_divergence_detected")
        self.assertFalse(comparison_stage["downstream_permitted"])
        self.assertEqual(comparison_stage["divergent_sensors"], ["temperature"])
        self.assertEqual(persistence_stage["status"], "blocked")
        self.assertEqual(persistence_stage["reason"], "scada_divergence_detected")
        self.assertFalse(persistence_stage["downstream_permitted"])
        self.assertFalse(persistence_stage["write_confirmed"])
        self.assertEqual(fake_client.objects, {})

    def test_execute_fingerprint_pipeline_for_cycle_blocks_when_no_quorum_or_scada_divergence(self) -> None:
        from parallel_truth_fingerprint.config.runtime import RuntimeDemoConfig
        from parallel_truth_fingerprint.lstm_service import ScadaReplayRuntimeStage
        from parallel_truth_fingerprint.persistence import (
            MinioArtifactStore,
            MinioStoreConfig,
        )
        from parallel_truth_fingerprint.scada import FakeOpcUaScadaService
        from parallel_truth_fingerprint.consensus import build_round_summary
        from scripts.run_local_demo import (
            execute_fingerprint_pipeline_for_cycle,
            run_scada_comparison_and_persistence,
        )
        from tests.persistence.test_service import FakeMinioClient
        from tests.persistence.test_service import build_valid_audit_package

        config = RuntimeDemoConfig(
            mqtt_transport="passive",
            demo_train_after_eligible_cycles=3,
            demo_fingerprint_sequence_length=2,
        )

        blocked_store = MinioArtifactStore(
            MinioStoreConfig(
                endpoint="localhost:9000",
                access_key="minioadmin",
                secret_key="minioadmin",
                bucket="valid-consensus-artifacts",
            ),
            client=FakeMinioClient(),
        )
        failed_audit = self._build_failed_consensus_audit_package()
        (
            scada_state,
            comparison_stage,
            comparison_output,
            _scada_alert,
            persistence_stage,
        ) = run_scada_comparison_and_persistence(
            consensus_audit=failed_audit,
            artifact_store=blocked_store,
        )
        fingerprint_stage, inference_results, replay_result, replay_inference_results = (
            execute_fingerprint_pipeline_for_cycle(
                cycle_index=1,
                config=config,
                artifact_store=blocked_store,
                scada_state=scada_state,
                comparison_output=comparison_output,
                comparison_stage=comparison_stage,
                persistence_stage=persistence_stage,
                scada_replay_stage=ScadaReplayRuntimeStage(
                    active=False,
                    mode="match",
                    start_cycle=0,
                ),
                consensus_summary=build_round_summary(failed_audit),
            )
        )
        self.assertEqual(fingerprint_stage.training_events, ("blocked",))
        self.assertEqual(fingerprint_stage.inference_status, "blocked:no_quorum_reached")
        self.assertEqual(inference_results, ())
        self.assertIsNone(replay_result)
        self.assertEqual(replay_inference_results, ())

        divergent_store = MinioArtifactStore(
            MinioStoreConfig(
                endpoint="localhost:9000",
                access_key="minioadmin",
                secret_key="minioadmin",
                bucket="valid-consensus-artifacts",
            ),
            client=FakeMinioClient(),
        )
        scada_service = FakeOpcUaScadaService(compressor_id="compressor-1")
        scada_service.set_sensor_override("temperature", mode="offset", offset=12.0)
        valid_audit = build_valid_audit_package(round_id="round-divergence")
        (
            scada_state,
            comparison_stage,
            comparison_output,
            _scada_alert,
            persistence_stage,
        ) = run_scada_comparison_and_persistence(
            consensus_audit=valid_audit,
            artifact_store=divergent_store,
            scada_service=scada_service,
        )
        fingerprint_stage, inference_results, replay_result, replay_inference_results = (
            execute_fingerprint_pipeline_for_cycle(
                cycle_index=2,
                config=config,
                artifact_store=divergent_store,
                scada_state=scada_state,
                comparison_output=comparison_output,
                comparison_stage=comparison_stage,
                persistence_stage=persistence_stage,
                scada_replay_stage=ScadaReplayRuntimeStage(
                    active=True,
                    mode="replay",
                    start_cycle=2,
                    replay_source_round_id="round-000",
                ),
                consensus_summary=build_round_summary(valid_audit),
            )
        )
        self.assertEqual(
            fingerprint_stage.inference_status,
            "blocked:scada_divergence_detected",
        )
        self.assertEqual(fingerprint_stage.training_events, ("blocked",))
        self.assertEqual(inference_results, ())
        self.assertIsNone(replay_result)
        self.assertEqual(replay_inference_results, ())

    def _build_failed_consensus_audit_package(self):
        from parallel_truth_fingerprint.contracts.consensus_audit_package import (
            ConsensusAuditPackage,
        )
        from parallel_truth_fingerprint.contracts.consensus_result import ConsensusResult
        from parallel_truth_fingerprint.contracts.consensus_round_input import (
            ConsensusRoundInput,
        )
        from parallel_truth_fingerprint.contracts.consensus_status import ConsensusStatus
        from parallel_truth_fingerprint.contracts.exclusion_decision import (
            ExclusionDecision,
        )
        from parallel_truth_fingerprint.contracts.exclusion_reason import ExclusionReason
        from parallel_truth_fingerprint.contracts.round_identity import RoundIdentity
        from parallel_truth_fingerprint.contracts.trust_ranking import (
            TrustRankEntry,
            TrustRanking,
        )
        from datetime import datetime, timezone

        round_identity = RoundIdentity(
            round_id="round-blocked",
            window_started_at=datetime(2026, 4, 1, 16, 0, tzinfo=timezone.utc),
            window_ended_at=datetime(2026, 4, 1, 16, 1, tzinfo=timezone.utc),
        )
        trust_ranking = TrustRanking(
            round_identity=round_identity,
            participating_edges=("edge-1", "edge-2", "edge-3"),
            entries=(
                TrustRankEntry(edge_id="edge-1", score=0.9),
                TrustRankEntry(edge_id="edge-2", score=0.2),
                TrustRankEntry(edge_id="edge-3", score=0.1),
            ),
        )
        exclusions = (
            ExclusionDecision(
                round_identity=round_identity,
                edge_id="edge-2",
                reason=ExclusionReason.SUSPECTED_BYZANTINE_BEHAVIOR,
                detail="score=0.2",
            ),
            ExclusionDecision(
                round_identity=round_identity,
                edge_id="edge-3",
                reason=ExclusionReason.SUSPECTED_BYZANTINE_BEHAVIOR,
                detail="score=0.1",
            ),
        )
        return ConsensusAuditPackage(
            round_input=ConsensusRoundInput(
                round_identity=round_identity,
                participating_edges=("edge-1", "edge-2", "edge-3"),
                replicated_states=(),
            ),
            trust_ranking=trust_ranking,
            exclusions=exclusions,
            trust_evidence=(),
            final_status=ConsensusStatus.FAILED_CONSENSUS,
            consensus_result=ConsensusResult(
                round_identity=round_identity,
                status=ConsensusStatus.FAILED_CONSENSUS,
                participating_edges=("edge-1", "edge-2", "edge-3"),
                trust_ranking=trust_ranking,
                exclusions=exclusions,
                consensused_valid_state=None,
            ),
            consensused_valid_state=None,
        )


class DemoFaultInjectionTest(unittest.TestCase):
    def test_inject_faults_can_preserve_quorum_with_single_faulty_edge(self) -> None:
        from parallel_truth_fingerprint.config.runtime import RuntimeDemoConfig
        from parallel_truth_fingerprint.consensus import ConsensusEngine, build_round_summary
        from scripts.run_local_demo import inject_faults

        from tests.consensus.test_summary import make_replicated_state
        from parallel_truth_fingerprint.contracts.consensus_round_input import (
            ConsensusRoundInput,
        )
        from parallel_truth_fingerprint.contracts.round_identity import RoundIdentity
        from datetime import datetime, timedelta, timezone

        round_identity = RoundIdentity(
            round_id="round-fault-single",
            window_started_at=datetime(2026, 3, 25, 12, 0, tzinfo=timezone.utc),
            window_ended_at=datetime(2026, 3, 25, 12, 1, tzinfo=timezone.utc),
        )
        round_input = ConsensusRoundInput(
            round_identity=round_identity,
            participating_edges=("edge-1", "edge-2", "edge-3"),
            replicated_states=(
                make_replicated_state(round_identity, "edge-1", 80.0, 6.0, 3200.0),
                make_replicated_state(round_identity, "edge-2", 82.0, 6.2, 3220.0),
                make_replicated_state(round_identity, "edge-3", 81.0, 6.1, 3210.0),
            ),
        )

        injected = inject_faults(
            round_input,
            RuntimeDemoConfig(
                mqtt_transport="passive",
                demo_fault_mode="single_edge_exclusion",
                demo_faulty_edges=("edge-3",),
            ),
        )
        summary = build_round_summary(ConsensusEngine().evaluate(injected))

        self.assertEqual(summary.final_consensus_status.value, "success")
        self.assertEqual(summary.valid_participants_after_exclusions, 2)
        self.assertEqual(summary.excluded_edge_ids, ("edge-3",))

    def test_inject_faults_can_force_failed_consensus(self) -> None:
        from parallel_truth_fingerprint.config.runtime import RuntimeDemoConfig
        from parallel_truth_fingerprint.consensus import (
            ConsensusEngine,
            build_round_summary,
        )
        from scripts.run_local_demo import inject_faults

        from tests.consensus.test_summary import make_replicated_state
        from parallel_truth_fingerprint.contracts.consensus_round_input import (
            ConsensusRoundInput,
        )
        from parallel_truth_fingerprint.contracts.round_identity import RoundIdentity
        from datetime import datetime, timedelta, timezone

        round_identity = RoundIdentity(
            round_id="round-fault-quorum",
            window_started_at=datetime(2026, 3, 25, 12, 0, tzinfo=timezone.utc),
            window_ended_at=datetime(2026, 3, 25, 12, 1, tzinfo=timezone.utc),
        )
        round_input = ConsensusRoundInput(
            round_identity=round_identity,
            participating_edges=("edge-1", "edge-2", "edge-3"),
            replicated_states=(
                make_replicated_state(round_identity, "edge-1", 80.0, 6.0, 3200.0),
                make_replicated_state(round_identity, "edge-2", 82.0, 6.2, 3220.0),
                make_replicated_state(round_identity, "edge-3", 81.0, 6.1, 3210.0),
            ),
        )

        injected = inject_faults(
            round_input,
            RuntimeDemoConfig(
                mqtt_transport="passive",
                demo_fault_mode="quorum_loss",
                demo_faulty_edges=("edge-2", "edge-3"),
            ),
        )
        summary = build_round_summary(ConsensusEngine().evaluate(injected))

        self.assertEqual(summary.final_consensus_status.value, "failed_consensus")
        self.assertEqual(summary.valid_participants_after_exclusions, 0)


class DemoConsensusPathTest(unittest.TestCase):
    def test_demo_uses_cometbft_client_for_live_consensus_path(self) -> None:
        from parallel_truth_fingerprint.config.runtime import RuntimeDemoConfig
        from scripts import run_local_demo

        committed_round = {
            "round_id": "round-20260326100000000000",
            "window_started_at": "2026-03-26T10:00:00+00:00",
            "window_ended_at": "2026-03-26T10:01:00+00:00",
            "participating_edges": ["edge-1", "edge-2", "edge-3"],
            "replicated_states": [],
            "trust_ranking": [
                {"edge_id": "edge-1", "score": 1.0},
                {"edge_id": "edge-2", "score": 0.99},
                {"edge_id": "edge-3", "score": 0.98},
            ],
            "exclusions": [],
            "trust_evidence": [],
            "final_status": "success",
            "consensused_valid_state": {
                "source_edges": ["edge-1", "edge-2", "edge-3"],
                "sensor_values": {
                    "temperature": 80.0,
                    "pressure": 6.0,
                    "rpm": 3200.0,
                },
            },
            "commit_height": 11,
        }

        class FakeClient:
            def __init__(self, rpc_url: str) -> None:
                self.rpc_url = rpc_url

            def status(self):
                return {
                    "node_info": {"version": "1.0.0"},
                    "sync_info": {"latest_block_height": "10"},
                }

            def broadcast_round(self, round_input):
                return type(
                    "Receipt",
                    (),
                    {
                        "round_id": round_input.round_identity.round_id,
                        "height": 11,
                        "tx_hash": "DEADBEEF",
                        "check_tx_code": 0,
                        "deliver_tx_code": 0,
                    },
                )()

            def query_committed_round(self, round_id: str):
                payload = dict(committed_round)
                payload["round_id"] = round_id
                return payload

        config = RuntimeDemoConfig(
            mqtt_transport="passive",
            cometbft_rpc_url="http://127.0.0.1:26657",
            minio_endpoint="localhost:9000",
            minio_access_key="minioadmin",
            minio_secret_key="minioadmin",
            minio_bucket="valid-consensus-artifacts",
            demo_steps=1,
            demo_max_cycles=1,
            demo_power=65.0,
            demo_fault_mode="none",
        )
        from parallel_truth_fingerprint.persistence import MinioArtifactStore, MinioStoreConfig
        from tests.persistence.test_service import FakeMinioClient

        fake_client = FakeMinioClient()
        artifact_store = MinioArtifactStore(
            MinioStoreConfig(
                endpoint="localhost:9000",
                access_key="minioadmin",
                secret_key="minioadmin",
                bucket="valid-consensus-artifacts",
            ),
            client=fake_client,
        )

        with mock.patch.object(run_local_demo, "CometBftRpcClient", FakeClient):
            with mock.patch.object(run_local_demo, "load_runtime_demo_config", return_value=config):
                with mock.patch.object(
                    run_local_demo,
                    "build_demo_artifact_store",
                    return_value=artifact_store,
                ):
                    with mock.patch("time.sleep", return_value=None):
                        with mock.patch.object(
                            run_local_demo,
                            "write_detailed_log",
                            return_value=run_local_demo.PROJECT_ROOT / "logs" / "test-runtime-demo.log",
                        ):
                            with mock.patch("sys.stdout"):
                                run_local_demo.main()

        self.assertTrue(fake_client.objects)


if __name__ == "__main__":
    unittest.main()
