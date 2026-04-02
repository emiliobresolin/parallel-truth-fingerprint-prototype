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
        previous_log_path = os.environ.get("DEMO_LOG_PATH")
        previous_artifact_root = os.environ.get("DEMO_ARTIFACT_ROOT")
        try:
            os.environ["MQTT_TRANSPORT"] = "passive"
            os.environ["DEMO_STEPS"] = "5"
            os.environ["DEMO_FAULT_MODE"] = "single_edge_exclusion"
            os.environ["DEMO_FAULTY_EDGES"] = "edge-3"
            os.environ["COMETBFT_RPC_URL"] = "http://127.0.0.1:26657"
            os.environ["DEMO_LOG_PATH"] = "logs/custom-demo.log"
            os.environ["DEMO_ARTIFACT_ROOT"] = "artifacts/custom"

            config = load_runtime_demo_config()

            self.assertEqual(config.mqtt_transport, "passive")
            self.assertEqual(config.demo_steps, 5)
            self.assertEqual(config.demo_fault_mode, "single_edge_exclusion")
            self.assertEqual(config.demo_faulty_edges, ("edge-3",))
            self.assertEqual(config.cometbft_rpc_url, "http://127.0.0.1:26657")
            self.assertEqual(config.demo_log_path, "logs/custom-demo.log")
            self.assertEqual(config.demo_artifact_root, "artifacts/custom")
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
            if previous_log_path is None:
                os.environ.pop("DEMO_LOG_PATH", None)
            else:
                os.environ["DEMO_LOG_PATH"] = previous_log_path
            if previous_artifact_root is None:
                os.environ.pop("DEMO_ARTIFACT_ROOT", None)
            else:
                os.environ["DEMO_ARTIFACT_ROOT"] = previous_artifact_root


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
        from scripts.run_local_demo import (
            PROJECT_ROOT,
            default_demo_artifact_root,
            default_demo_log_path,
        )

        relative = default_demo_log_path("logs/dev.log")
        absolute = default_demo_log_path(str(PROJECT_ROOT / "logs" / "abs.log"))
        artifact_relative = default_demo_artifact_root("artifacts/dev")
        artifact_absolute = default_demo_artifact_root(
            str(PROJECT_ROOT / "artifacts" / "abs")
        )

        self.assertEqual(relative, PROJECT_ROOT / "logs" / "dev.log")
        self.assertEqual(absolute, PROJECT_ROOT / "logs" / "abs.log")
        self.assertEqual(artifact_relative, PROJECT_ROOT / "artifacts" / "dev")
        self.assertEqual(artifact_absolute, PROJECT_ROOT / "artifacts" / "abs")

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
            "artifact_key": "valid-consensus-artifacts/round-1.json",
            "artifact_path": "C:\\temp\\round-1.json",
        }
        persistence_blocked = {
            "status": "blocked",
            "reason": "no_consensused_valid_state",
        }

        self.assertIn(
            "scada_source=round-1",
            format_comparison_stage_compact(comparison_completed),
        )
        self.assertEqual(
            format_comparison_stage_compact(comparison_blocked),
            "comparison=blocked reason=no_consensused_valid_state",
        )
        self.assertIn(
            "artifact_key=valid-consensus-artifacts/round-1.json",
            format_persistence_stage_compact(persistence_persisted),
        )
        self.assertEqual(
            format_persistence_stage_compact(persistence_blocked),
            "persistence=blocked reason=no_consensused_valid_state",
        )

    def test_run_scada_comparison_and_persistence_blocks_without_valid_state(self) -> None:
        from pathlib import Path
        import shutil

        from parallel_truth_fingerprint.contracts.consensus_audit_package import (
            ConsensusAuditPackage,
        )
        from parallel_truth_fingerprint.contracts.consensus_result import ConsensusResult
        from parallel_truth_fingerprint.contracts.consensus_round_input import (
            ConsensusRoundInput,
        )
        from parallel_truth_fingerprint.contracts.consensus_status import ConsensusStatus
        from parallel_truth_fingerprint.contracts.round_identity import RoundIdentity
        from parallel_truth_fingerprint.contracts.trust_ranking import (
            TrustRankEntry,
            TrustRanking,
        )
        from scripts.run_local_demo import PROJECT_ROOT, run_scada_comparison_and_persistence
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
        artifact_root = PROJECT_ROOT / "tests" / "_tmp_artifacts_blocked"
        try:
            scada_state, comparison_stage, comparison_output, scada_alert, persistence_stage = (
                run_scada_comparison_and_persistence(
                    consensus_audit=audit_package,
                    artifact_root=artifact_root,
                )
            )
            self.assertIsNone(scada_state)
            self.assertIsNone(comparison_output)
            self.assertIsNone(scada_alert)
            self.assertEqual(comparison_stage["status"], "blocked")
            self.assertEqual(persistence_stage["status"], "blocked")
        finally:
            if artifact_root.exists():
                shutil.rmtree(artifact_root)

    def test_run_scada_comparison_and_persistence_persists_local_artifact(self) -> None:
        import shutil
        from pathlib import Path

        from tests.persistence.test_service import build_valid_audit_package
        from scripts.run_local_demo import PROJECT_ROOT, run_scada_comparison_and_persistence

        artifact_root = PROJECT_ROOT / "tests" / "_tmp_artifacts_success"
        try:
            audit_package = build_valid_audit_package()
            scada_state, comparison_stage, comparison_output, scada_alert, persistence_stage = (
                run_scada_comparison_and_persistence(
                    consensus_audit=audit_package,
                    artifact_root=artifact_root,
                )
            )

            self.assertIsNotNone(scada_state)
            self.assertIsNotNone(comparison_output)
            self.assertEqual(comparison_stage["status"], "completed")
            self.assertEqual(persistence_stage["status"], "persisted")
            persisted_path = Path(persistence_stage["artifact_path"])
            self.assertTrue(persisted_path.exists())
        finally:
            if artifact_root.exists():
                shutil.rmtree(artifact_root)


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
            demo_steps=1,
            demo_power=65.0,
            demo_fault_mode="none",
            demo_artifact_root="tests/_tmp_demo_artifacts",
        )

        with mock.patch.object(run_local_demo, "CometBftRpcClient", FakeClient):
            with mock.patch.object(run_local_demo, "load_runtime_demo_config", return_value=config):
                with mock.patch("sys.stdout"):
                    try:
                        run_local_demo.main()
                    finally:
                        from pathlib import Path
                        import shutil

                        artifact_root = run_local_demo.PROJECT_ROOT / "tests" / "_tmp_demo_artifacts"
                        if artifact_root.exists():
                            shutil.rmtree(artifact_root)


if __name__ == "__main__":
    unittest.main()
