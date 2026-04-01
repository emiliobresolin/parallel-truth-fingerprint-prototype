"""Focused tests for Story 3.4 valid artifact persistence."""

from __future__ import annotations

from datetime import datetime, timedelta, timezone
import unittest

from parallel_truth_fingerprint.comparison import (
    ScadaToleranceProfile,
    build_scada_comparison_output,
    compare_consensused_to_scada,
)
from parallel_truth_fingerprint.contracts.consensus_audit_package import (
    ConsensusAuditPackage,
)
from parallel_truth_fingerprint.contracts.consensus_result import ConsensusResult
from parallel_truth_fingerprint.contracts.consensus_round_input import ConsensusRoundInput
from parallel_truth_fingerprint.contracts.consensus_status import ConsensusStatus
from parallel_truth_fingerprint.contracts.consensused_valid_state import (
    ConsensusedValidState,
)
from parallel_truth_fingerprint.contracts.edge_local_replicated_state import (
    EdgeLocalReplicatedStateContract,
)
from parallel_truth_fingerprint.contracts.raw_hart_payload import (
    DeviceInfo,
    Diagnostics,
    PhysicsMetrics,
    ProcessData,
    ProcessVariable,
    RawHartPayload,
)
from parallel_truth_fingerprint.contracts.round_identity import RoundIdentity
from parallel_truth_fingerprint.contracts.trust_ranking import TrustRankEntry, TrustRanking
from parallel_truth_fingerprint.persistence import (
    PersistenceBlockedError,
    MinioArtifactStore,
    MinioStoreConfig,
    persist_valid_consensus_artifact,
)
from parallel_truth_fingerprint.scada import FakeOpcUaScadaService


class FakeMinioClient:
    def __init__(self) -> None:
        self.buckets: set[str] = set()
        self.objects: dict[tuple[str, str], bytes] = {}

    def bucket_exists(self, bucket_name: str) -> bool:
        return bucket_name in self.buckets

    def make_bucket(self, bucket_name: str) -> None:
        self.buckets.add(bucket_name)

    def put_object(
        self,
        bucket_name: str,
        object_name: str,
        data,
        *,
        length: int,
        content_type: str,
    ) -> None:
        self.objects[(bucket_name, object_name)] = data.read(length)


def build_round_identity(round_id: str = "round-400") -> RoundIdentity:
    ended_at = datetime(2026, 4, 1, 15, 0, 0, tzinfo=timezone.utc)
    return RoundIdentity(
        round_id=round_id,
        window_started_at=ended_at - timedelta(minutes=1),
        window_ended_at=ended_at,
    )


def build_valid_audit_package(
    *,
    round_id: str = "round-400",
    status: ConsensusStatus = ConsensusStatus.SUCCESS,
) -> ConsensusAuditPackage:
    round_identity = build_round_identity(round_id)
    raw_observation = RawHartPayload(
        protocol="HART",
        gateway_id="GW-EDGE-01",
        timestamp="2026-04-01T15:00:00Z",
        device_info=DeviceInfo(
            tag="TIT-101",
            long_tag="Temperature_Compressor_Casing",
            manufacturer_id=26,
            device_type=33,
        ),
        process_data=ProcessData(
            pv=ProcessVariable(value=72.5, unit="degC", unit_code=32),
            sv=None,
            loop_current_ma=14.2,
            pv_percent_range=65.1,
            physics_metrics=PhysicsMetrics(
                noise_floor=0.2,
                rate_of_change_dtdt=0.5,
                local_stability_score=0.9,
            ),
        ),
        diagnostics=Diagnostics(
            device_status_hex="0x00",
            field_device_malfunction=False,
            loop_current_saturated=False,
            cold_start=False,
        ),
    )
    round_input = ConsensusRoundInput(
        round_identity=round_identity,
        participating_edges=("edge-1", "edge-2", "edge-3"),
        replicated_states=(
            EdgeLocalReplicatedStateContract(
                round_identity=round_identity,
                owner_edge_id="edge-1",
                participating_edges=("edge-1", "edge-2", "edge-3"),
                observations_by_sensor={"temperature": raw_observation},
                is_validated=False,
            ),
        ),
    )
    trust_ranking = TrustRanking(
        round_identity=round_identity,
        participating_edges=("edge-1", "edge-2", "edge-3"),
        entries=(
            TrustRankEntry(edge_id="edge-1", score=0.95),
            TrustRankEntry(edge_id="edge-2", score=0.92),
            TrustRankEntry(edge_id="edge-3", score=0.41),
        ),
    )
    valid_state = None
    if status == ConsensusStatus.SUCCESS:
        valid_state = ConsensusedValidState(
            round_identity=round_identity,
            source_edges=("edge-1", "edge-2"),
            sensor_values={
                "temperature": 72.5,
                "pressure": 5.3,
                "rpm": 3120.0,
            },
        )
    consensus_result = ConsensusResult(
        round_identity=round_identity,
        status=status,
        participating_edges=("edge-1", "edge-2", "edge-3"),
        trust_ranking=trust_ranking,
        exclusions=(),
        consensused_valid_state=valid_state,
    )
    return ConsensusAuditPackage(
        round_input=round_input,
        trust_ranking=trust_ranking,
        exclusions=(),
        trust_evidence=(),
        final_status=status,
        consensus_result=consensus_result,
        consensused_valid_state=valid_state,
    )


class ValidArtifactPersistenceTests(unittest.TestCase):
    def test_persist_valid_artifact_writes_required_content(self) -> None:
        audit_package = build_valid_audit_package()
        scada_state = FakeOpcUaScadaService().project_state(audit_package.consensused_valid_state)
        comparison_result = compare_consensused_to_scada(
            valid_state=audit_package.consensused_valid_state,
            scada_state=scada_state,
            tolerance_profile=ScadaToleranceProfile(
                temperature=1.0,
                pressure=0.3,
                rpm=100.0,
            ),
        )
        comparison_output = build_scada_comparison_output(comparison_result)

        client = FakeMinioClient()
        store = MinioArtifactStore(
            MinioStoreConfig(
                endpoint="localhost:9000",
                access_key="minioadmin",
                secret_key="minioadmin",
                bucket="valid-consensus-artifacts",
            ),
            client=client,
        )

        record = persist_valid_consensus_artifact(
            audit_package=audit_package,
            scada_comparison_output=comparison_output,
            artifact_store=store,
            persisted_at=datetime(2026, 4, 1, 15, 1, 0, tzinfo=timezone.utc),
        )

        self.assertEqual(
            record.artifact_key,
            "valid-consensus-artifacts/round-400.json",
        )
        saved = client.objects[("valid-consensus-artifacts", record.artifact_key)].decode("utf-8")
        self.assertIn('"persisted_at": "2026-04-01T15:01:00+00:00"', saved)
        self.assertIn('"consensus_state"', saved)
        self.assertIn('"trust_scores"', saved)
        self.assertIn('"excluded_edges"', saved)
        self.assertIn('"scada_comparison_results"', saved)
        self.assertIn('"diagnostics"', saved)

    def test_persistence_is_blocked_for_failed_consensus(self) -> None:
        audit_package = build_valid_audit_package(status=ConsensusStatus.FAILED_CONSENSUS)
        comparison_output = build_scada_comparison_output(
            compare_consensused_to_scada(
                valid_state=ConsensusedValidState(
                    round_identity=build_round_identity("round-shadow"),
                    source_edges=("edge-1", "edge-2"),
                    sensor_values={
                        "temperature": 72.5,
                        "pressure": 5.3,
                        "rpm": 3120.0,
                    },
                ),
                scada_state=FakeOpcUaScadaService().project_state(
                    ConsensusedValidState(
                        round_identity=build_round_identity("round-shadow"),
                        source_edges=("edge-1", "edge-2"),
                        sensor_values={
                            "temperature": 72.5,
                            "pressure": 5.3,
                            "rpm": 3120.0,
                        },
                    )
                ),
            )
        )
        store = MinioArtifactStore(
            MinioStoreConfig(
                endpoint="localhost:9000",
                access_key="minioadmin",
                secret_key="minioadmin",
                bucket="valid-consensus-artifacts",
            ),
            client=FakeMinioClient(),
        )

        with self.assertRaises(PersistenceBlockedError):
            persist_valid_consensus_artifact(
                audit_package=audit_package,
                scada_comparison_output=comparison_output,
                artifact_store=store,
            )

    def test_minio_store_creates_bucket_before_first_write(self) -> None:
        client = FakeMinioClient()
        store = MinioArtifactStore(
            MinioStoreConfig(
                endpoint="localhost:9000",
                access_key="minioadmin",
                secret_key="minioadmin",
                bucket="valid-consensus-artifacts",
            ),
            client=client,
        )

        object_name = store.save_json("valid-consensus-artifacts/round-401.json", {"ok": True})

        self.assertEqual(object_name, "valid-consensus-artifacts/round-401.json")
        self.assertIn("valid-consensus-artifacts", client.buckets)
        self.assertIn(
            ("valid-consensus-artifacts", "valid-consensus-artifacts/round-401.json"),
            client.objects,
        )
