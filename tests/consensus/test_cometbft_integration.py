from __future__ import annotations

import base64
from datetime import datetime, timezone
import json
import unittest

from parallel_truth_fingerprint.consensus.cometbft_client import (
    CometBftRpcClient,
    serialize_round_input,
)
from parallel_truth_fingerprint.consensus.cometbft_mapper import (
    committed_round_to_audit_package,
)
from parallel_truth_fingerprint.contracts.consensus_status import ConsensusStatus
from parallel_truth_fingerprint.contracts.exclusion_reason import ExclusionReason
from parallel_truth_fingerprint.contracts.round_identity import RoundIdentity
from tests.consensus.test_summary import make_replicated_state
from parallel_truth_fingerprint.contracts.consensus_round_input import (
    ConsensusRoundInput,
)


def make_round_input() -> ConsensusRoundInput:
    round_identity = RoundIdentity(
        round_id="round-cometbft-001",
        window_started_at=datetime(2026, 3, 26, 10, 0, tzinfo=timezone.utc),
        window_ended_at=datetime(2026, 3, 26, 10, 1, tzinfo=timezone.utc),
    )
    return ConsensusRoundInput(
        round_identity=round_identity,
        participating_edges=("edge-1", "edge-2", "edge-3"),
        replicated_states=(
            make_replicated_state(round_identity, "edge-1", 80.0, 6.0, 3200.0),
            make_replicated_state(round_identity, "edge-2", 81.0, 6.1, 3210.0),
            make_replicated_state(round_identity, "edge-3", 119.0, 9.4, 4700.0),
        ),
    )


class SerializeRoundInputTest(unittest.TestCase):
    def test_serialize_round_input_is_deterministic_and_sensor_based(self) -> None:
        round_input = make_round_input()

        serialized = serialize_round_input(round_input)
        payload = json.loads(serialized.decode("utf-8"))

        self.assertEqual(payload["round_id"], "round-cometbft-001")
        self.assertEqual(payload["participating_edges"], ["edge-1", "edge-2", "edge-3"])
        self.assertEqual(payload["replicated_states"][0]["owner_edge_id"], "edge-1")
        self.assertEqual(
            payload["replicated_states"][0]["sensor_values"]["temperature"]["value"],
            80.0,
        )
        self.assertEqual(
            payload["replicated_states"][1]["sensor_values"]["pressure"]["unit"],
            "bar",
        )


class CometBftRpcClientTest(unittest.TestCase):
    def test_broadcast_round_returns_commit_receipt(self) -> None:
        round_input = make_round_input()
        client = CometBftRpcClient("http://127.0.0.1:26657")

        client._json_rpc = lambda method, params, candidate_paths: {  # type: ignore[method-assign]
            "result": {
                "height": "9",
                "hash": "ABC123",
                "check_tx": {"code": 0},
                "tx_result": {"code": 0},
            }
        }

        receipt = client.broadcast_round(round_input)

        self.assertEqual(receipt.round_id, "round-cometbft-001")
        self.assertEqual(receipt.height, 9)
        self.assertEqual(receipt.tx_hash, "ABC123")
        self.assertEqual(receipt.deliver_tx_code, 0)

    def test_query_committed_round_decodes_abci_response(self) -> None:
        client = CometBftRpcClient("http://127.0.0.1:26657")
        encoded_value = base64.b64encode(
            json.dumps({"round_id": "round-cometbft-001", "final_status": "success"}).encode(
                "utf-8"
            )
        ).decode("ascii")
        client._get_json = lambda default_path, query, fallback_paths: {  # type: ignore[method-assign]
            "result": {
                "response": {
                    "code": 0,
                    "value": encoded_value,
                }
            }
        }

        committed_round = client.query_committed_round("round-cometbft-001")

        self.assertEqual(committed_round["round_id"], "round-cometbft-001")
        self.assertEqual(committed_round["final_status"], "success")


class CommittedRoundMapperTest(unittest.TestCase):
    def test_committed_round_to_audit_package_uses_committed_result_as_truth(self) -> None:
        round_input = make_round_input()
        committed_round = {
            "round_id": "round-cometbft-001",
            "window_started_at": "2026-03-26T10:00:00+00:00",
            "window_ended_at": "2026-03-26T10:01:00+00:00",
            "participating_edges": ["edge-1", "edge-2", "edge-3"],
            "replicated_states": [],
            "trust_ranking": [
                {"edge_id": "edge-1", "score": 1.0},
                {"edge_id": "edge-2", "score": 0.94},
                {"edge_id": "edge-3", "score": 0.23},
            ],
            "exclusions": [
                {
                    "edge_id": "edge-3",
                    "reason": "suspected_byzantine_behavior",
                    "detail": "compatible_peers=0",
                }
            ],
            "trust_evidence": [
                {
                    "edge_id": "edge-1",
                    "score": 1.0,
                    "compatible_peer_count": 2,
                    "overall_normalized_deviation": 0.0,
                    "sensor_deviations": [
                        {
                            "sensor_name": "temperature",
                            "deviation_value": 0.5,
                            "unit": "degC",
                        }
                    ],
                    "pairwise_distances": [
                        {
                            "peer_edge_id": "edge-2",
                            "sensor_name": "temperature",
                            "distance_value": 1.0,
                            "unit": "degC",
                        }
                    ],
                }
            ],
            "final_status": "success",
            "consensused_valid_state": {
                "source_edges": ["edge-1", "edge-2"],
                "sensor_values": {
                    "temperature": 80.5,
                    "pressure": 6.05,
                    "rpm": 3205.0,
                },
            },
            "commit_height": 9,
        }

        audit_package = committed_round_to_audit_package(round_input, committed_round)

        self.assertEqual(audit_package.final_status, ConsensusStatus.SUCCESS)
        self.assertEqual(audit_package.consensused_valid_state.source_edges, ("edge-1", "edge-2"))
        self.assertEqual(audit_package.exclusions[0].reason, ExclusionReason.SUSPECTED_BYZANTINE_BEHAVIOR)
        self.assertEqual(audit_package.trust_ranking.entries[0].edge_id, "edge-1")


if __name__ == "__main__":
    unittest.main()
