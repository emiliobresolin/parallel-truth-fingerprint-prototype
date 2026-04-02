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

    def list_objects(
        self,
        bucket_name: str,
        *,
        prefix: str = "",
        recursive: bool = False,
    ):
        for (current_bucket, object_name), payload in sorted(self.objects.items()):
            if current_bucket != bucket_name:
                continue
            if not object_name.startswith(prefix):
                continue
            yield type(
                "MinioObject",
                (),
                {
                    "object_name": object_name,
                    "size": len(payload),
                },
            )()

    def get_object(self, bucket_name: str, object_name: str):
        payload = self.objects[(bucket_name, object_name)]

        class FakeResponse:
            def __init__(self, data: bytes) -> None:
                self._data = data

            def read(self) -> bytes:
                return self._data

            def close(self) -> None:
                return None

            def release_conn(self) -> None:
                return None

        return FakeResponse(payload)


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
    temperature_observation = RawHartPayload(
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
            pv=ProcessVariable(
                value=72.5,
                unit="degC",
                unit_code=32,
                description="Process_Temperature",
            ),
            sv=ProcessVariable(
                value=54.1,
                unit="degC",
                unit_code=32,
                description="Sensor_Body_Temperature",
            ),
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
    pressure_observation = RawHartPayload(
        protocol="HART",
        gateway_id="GW-EDGE-02",
        timestamp="2026-04-01T15:00:00Z",
        device_info=DeviceInfo(
            tag="PIT-101",
            long_tag="Pressure_Compressor_Discharge",
            manufacturer_id=26,
            device_type=35,
        ),
        process_data=ProcessData(
            pv=ProcessVariable(
                value=5.3,
                unit="bar",
                unit_code=7,
                description="Process_Pressure",
            ),
            sv=ProcessVariable(
                value=31.8,
                unit="degC",
                unit_code=32,
                description="Transmitter_Module_Temperature",
            ),
            loop_current_ma=13.7,
            pv_percent_range=52.6,
            physics_metrics=PhysicsMetrics(
                noise_floor=0.1,
                rate_of_change_dtdt=0.12,
                local_stability_score=0.96,
            ),
        ),
        diagnostics=Diagnostics(
            device_status_hex="0x00",
            field_device_malfunction=False,
            loop_current_saturated=False,
            cold_start=False,
        ),
    )
    rpm_observation = RawHartPayload(
        protocol="HART",
        gateway_id="GW-EDGE-03",
        timestamp="2026-04-01T15:00:00Z",
        device_info=DeviceInfo(
            tag="RIT-101",
            long_tag="Rotation_Compressor_Shaft",
            manufacturer_id=26,
            device_type=39,
        ),
        process_data=ProcessData(
            pv=ProcessVariable(
                value=3120.0,
                unit="rpm",
                unit_code=None,
                description="Shaft_Speed",
            ),
            sv=None,
            loop_current_ma=14.9,
            pv_percent_range=64.0,
            physics_metrics=PhysicsMetrics(
                noise_floor=3.5,
                rate_of_change_dtdt=15.4,
                local_stability_score=0.93,
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
                observations_by_sensor={
                    "temperature": temperature_observation,
                    "pressure": pressure_observation,
                    "rpm": rpm_observation,
                },
                is_validated=False,
            ),
            EdgeLocalReplicatedStateContract(
                round_identity=round_identity,
                owner_edge_id="edge-2",
                participating_edges=("edge-1", "edge-2", "edge-3"),
                observations_by_sensor={
                    "temperature": temperature_observation,
                    "pressure": pressure_observation,
                    "rpm": rpm_observation,
                },
                is_validated=False,
            ),
            EdgeLocalReplicatedStateContract(
                round_identity=round_identity,
                owner_edge_id="edge-3",
                participating_edges=("edge-1", "edge-2", "edge-3"),
                observations_by_sensor={
                    "temperature": temperature_observation,
                    "pressure": pressure_observation,
                    "rpm": rpm_observation,
                },
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
            source_edges=("edge-1", "edge-2", "edge-3"),
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
            scada_state=scada_state,
            scada_comparison_output=comparison_output,
            dataset_context={
                "scenario_label": "normal",
                "training_label": "normal",
                "training_eligible": True,
                "training_eligibility_reason": "normal_validated_run",
            },
            artifact_store=store,
            persisted_at=datetime(2026, 4, 1, 15, 1, 0, tzinfo=timezone.utc),
        )

        self.assertEqual(
            record.artifact_key,
            "valid-consensus-artifacts/round-400.json",
        )
        saved = client.objects[("valid-consensus-artifacts", record.artifact_key)].decode("utf-8")
        self.assertIn('"persisted_at": "2026-04-01T15:01:00+00:00"', saved)
        self.assertIn('"artifact_identity"', saved)
        self.assertIn('"round_identity"', saved)
        self.assertIn('"consensus_context"', saved)
        self.assertIn('"validated_state"', saved)
        self.assertIn('"dataset_context"', saved)
        self.assertIn('"scada_context"', saved)
        self.assertIn('"diagnostics"', saved)
        persisted = record.to_dict()
        self.assertEqual(
            persisted["artifact_identity"]["artifact_type"],
            "valid_consensus_artifact",
        )
        self.assertEqual(
            persisted["dataset_context"]["scenario_label"],
            "normal",
        )
        self.assertTrue(persisted["dataset_context"]["training_eligible"])
        self.assertEqual(persisted["artifact_identity"]["artifact_version"], "2.0")
        self.assertEqual(
            persisted["consensus_context"]["final_consensus_status"],
            "success",
        )
        self.assertEqual(
            persisted["consensus_context"]["participating_edges"],
            ["edge-1", "edge-2", "edge-3"],
        )
        self.assertEqual(persisted["consensus_context"]["quorum_required"], 2)
        self.assertIn("trust_ranking", persisted["consensus_context"])
        self.assertIn("trust_evidence", persisted["consensus_context"])
        self.assertEqual(
            persisted["validated_state"]["structured_payload_snapshot"][
                "selected_source_edge_id"
            ],
            "edge-1",
        )
        payloads = persisted["validated_state"]["structured_payload_snapshot"][
            "payloads_by_sensor"
        ]
        self.assertEqual(
            payloads["temperature"]["device_info"]["tag"],
            "TIT-101",
        )
        self.assertEqual(
            payloads["pressure"]["process_data"]["pv"]["description"],
            "Process_Pressure",
        )
        self.assertEqual(
            payloads["pressure"]["process_data"]["loop_current_ma"],
            13.7,
        )
        self.assertEqual(
            payloads["rpm"]["process_data"]["physics_metrics"]["local_stability_score"],
            0.93,
        )
        self.assertEqual(
            persisted["scada_context"]["scada_state"]["sensor_values"]["pressure"]["unit"],
            "bar",
        )
        self.assertIn(
            "sensor_outputs",
            persisted["scada_context"]["comparison_output"],
        )
        self.assertIsNone(persisted["scada_context"]["divergence_alert"])

    def test_persistence_is_blocked_for_failed_consensus(self) -> None:
        audit_package = build_valid_audit_package(status=ConsensusStatus.FAILED_CONSENSUS)
        shadow_state = ConsensusedValidState(
            round_identity=build_round_identity("round-shadow"),
            source_edges=("edge-1", "edge-2"),
            sensor_values={
                "temperature": 72.5,
                "pressure": 5.3,
                "rpm": 3120.0,
            },
        )
        comparison_output = build_scada_comparison_output(
            compare_consensused_to_scada(
                valid_state=shadow_state,
                scada_state=FakeOpcUaScadaService().project_state(shadow_state),
            )
        )
        scada_state = FakeOpcUaScadaService().project_state(shadow_state)
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
                scada_state=scada_state,
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
