import os
import unittest

from parallel_truth_fingerprint.config.runtime import load_runtime_demo_config
from parallel_truth_fingerprint.edge_nodes.common.mqtt_io import PassiveMqttRelay


class RuntimeDemoConfigTest(unittest.TestCase):
    def test_runtime_demo_config_reads_environment(self) -> None:
        previous_transport = os.environ.get("MQTT_TRANSPORT")
        previous_steps = os.environ.get("DEMO_STEPS")
        try:
            os.environ["MQTT_TRANSPORT"] = "passive"
            os.environ["DEMO_STEPS"] = "5"

            config = load_runtime_demo_config()

            self.assertEqual(config.mqtt_transport, "passive")
            self.assertEqual(config.demo_steps, 5)
        finally:
            if previous_transport is None:
                os.environ.pop("MQTT_TRANSPORT", None)
            else:
                os.environ["MQTT_TRANSPORT"] = previous_transport
            if previous_steps is None:
                os.environ.pop("DEMO_STEPS", None)
            else:
                os.environ["DEMO_STEPS"] = previous_steps


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
                    sensor_deviations=(
                        SensorDeviationEvidence(
                            sensor_name="temperature",
                            deviation_value=0.0,
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
        self.assertIn("excluded=edge-3 reason=suspected_byzantine_behavior", detailed)


if __name__ == "__main__":
    unittest.main()
