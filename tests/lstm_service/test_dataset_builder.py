"""Focused tests for Epic 4 Story 4.1 dataset-building."""

from __future__ import annotations

from copy import deepcopy
from datetime import datetime, timedelta, timezone
import unittest

from parallel_truth_fingerprint.lstm_service import (
    build_normal_training_windows,
    evaluate_training_eligibility,
    extract_feature_vector,
)
from parallel_truth_fingerprint.persistence import MinioArtifactStore, MinioStoreConfig
from tests.persistence.test_service import FakeMinioClient


def build_persisted_artifact(
    *,
    index: int,
    scenario_label: str = "normal",
    training_eligible: bool = True,
    has_scada_divergence: bool = False,
) -> dict[str, object]:
    ended_at = datetime(2026, 4, 1, 18, index, 0, tzinfo=timezone.utc)
    round_id = f"round-{500 + index}"
    pressure = 5.0 + (index * 0.1)
    rpm = 3100.0 + (index * 10.0)
    temperature = 70.0 + (index * 0.5)
    return {
        "artifact_key": f"valid-consensus-artifacts/{round_id}.json",
        "persisted_at": (ended_at + timedelta(seconds=5)).isoformat(),
        "artifact_identity": {
            "artifact_type": "valid_consensus_artifact",
            "artifact_version": "2.0",
            "record_id": f"valid-consensus-artifact::valid-consensus-artifacts/{round_id}.json",
        },
        "round_identity": {
            "round_id": round_id,
            "window_started_at": (ended_at - timedelta(minutes=1)).isoformat(),
            "window_ended_at": ended_at.isoformat(),
        },
        "consensus_context": {
            "final_consensus_status": "success",
            "participating_edges": ["edge-1", "edge-2", "edge-3"],
            "quorum_required": 2,
            "source_edges": ["edge-1", "edge-2", "edge-3"],
            "trust_ranking": [],
            "exclusions": [],
            "trust_evidence": [],
        },
        "validated_state": {
            "state_type": "consensused_valid_state",
            "source_edges": ["edge-1", "edge-2", "edge-3"],
            "sensor_values": {
                "temperature": temperature,
                "pressure": pressure,
                "rpm": rpm,
            },
            "structured_payload_snapshot": {
                "snapshot_type": "validated_source_view",
                "selected_source_edge_id": "edge-1",
                "payloads_by_sensor": {
                    "pressure": {
                        "protocol": "HART",
                        "gateway_id": "GW-EDGE-02",
                        "timestamp": ended_at.isoformat(),
                        "device_info": {
                            "tag": "PIT-101",
                            "long_tag": "Pressure_Compressor_Discharge",
                            "manufacturer_id": 26,
                            "device_type": 35,
                        },
                        "process_data": {
                            "pv": {
                                "value": pressure,
                                "unit": "bar",
                                "unit_code": 7,
                                "description": "Process_Pressure",
                            },
                            "sv": {
                                "value": 31.5,
                                "unit": "degC",
                                "unit_code": 32,
                                "description": "Transmitter_Module_Temperature",
                            },
                            "loop_current_ma": 13.1 + (index * 0.1),
                            "pv_percent_range": 50.0 + index,
                            "physics_metrics": {
                                "noise_floor": 0.1,
                                "rate_of_change_dtdt": 0.2 + (index * 0.01),
                                "local_stability_score": 0.97,
                            },
                        },
                        "diagnostics": {
                            "device_status_hex": "0x00",
                            "field_device_malfunction": False,
                            "loop_current_saturated": False,
                            "cold_start": False,
                        },
                    },
                    "rpm": {
                        "protocol": "HART",
                        "gateway_id": "GW-EDGE-03",
                        "timestamp": ended_at.isoformat(),
                        "device_info": {
                            "tag": "RIT-101",
                            "long_tag": "Rotation_Compressor_Shaft",
                            "manufacturer_id": 26,
                            "device_type": 39,
                        },
                        "process_data": {
                            "pv": {
                                "value": rpm,
                                "unit": "rpm",
                                "unit_code": None,
                                "description": "Shaft_Speed",
                            },
                            "loop_current_ma": 14.8,
                            "pv_percent_range": 61.0 + index,
                            "physics_metrics": {
                                "noise_floor": 2.5,
                                "rate_of_change_dtdt": 12.0 + index,
                                "local_stability_score": 0.94,
                            },
                        },
                        "diagnostics": {
                            "device_status_hex": "0x00",
                            "field_device_malfunction": False,
                            "loop_current_saturated": False,
                            "cold_start": False,
                        },
                    },
                    "temperature": {
                        "protocol": "HART",
                        "gateway_id": "GW-EDGE-01",
                        "timestamp": ended_at.isoformat(),
                        "device_info": {
                            "tag": "TIT-101",
                            "long_tag": "Temperature_Compressor_Casing",
                            "manufacturer_id": 26,
                            "device_type": 33,
                        },
                        "process_data": {
                            "pv": {
                                "value": temperature,
                                "unit": "degC",
                                "unit_code": 32,
                                "description": "Process_Temperature",
                            },
                            "sv": {
                                "value": 52.0,
                                "unit": "degC",
                                "unit_code": 32,
                                "description": "Sensor_Body_Temperature",
                            },
                            "loop_current_ma": 14.0 + (index * 0.1),
                            "pv_percent_range": 60.0 + index,
                            "physics_metrics": {
                                "noise_floor": 0.3,
                                "rate_of_change_dtdt": 0.4 + (index * 0.02),
                                "local_stability_score": 0.91,
                            },
                        },
                        "diagnostics": {
                            "device_status_hex": "0x00",
                            "field_device_malfunction": False,
                            "loop_current_saturated": False,
                            "cold_start": False,
                        },
                    },
                },
            },
        },
        "dataset_context": {
            "scenario_label": scenario_label,
            "training_label": "normal" if training_eligible else "non_normal",
            "training_eligible": training_eligible,
            "training_eligibility_reason": (
                "normal_validated_run"
                if training_eligible
                else f"scenario:{scenario_label}"
            ),
        },
        "scada_context": {
            "scada_state": {
                "compressor_id": "compressor-1",
                "source_round_id": round_id,
                "timestamp": ended_at.isoformat(),
                "sensor_values": {},
            },
            "comparison_output": {
                "round_identity": {
                    "round_id": round_id,
                    "window_started_at": (ended_at - timedelta(minutes=1)).isoformat(),
                    "window_ended_at": ended_at.isoformat(),
                },
                "scada_source_round_id": round_id,
                "divergent_sensors": ["pressure"] if has_scada_divergence else [],
                "sensor_outputs": [],
            },
            "divergence_alert": None,
        },
        "diagnostics": {
            "final_consensus_status": "success",
            "has_scada_divergence": has_scada_divergence,
            "divergent_sensors": ["pressure"] if has_scada_divergence else [],
            "participating_edges": ["edge-1", "edge-2", "edge-3"],
            "persisted_record_type": "valid_consensus_artifact",
        },
    }


class DatasetBuilderTests(unittest.TestCase):
    def build_store(self) -> MinioArtifactStore:
        return MinioArtifactStore(
            MinioStoreConfig(
                endpoint="localhost:9000",
                access_key="minioadmin",
                secret_key="minioadmin",
                bucket="valid-consensus-artifacts",
            ),
            client=FakeMinioClient(),
        )

    def test_extract_feature_vector_is_deterministic_from_payload_snapshot(self) -> None:
        artifact = build_persisted_artifact(index=1)

        schema, values = extract_feature_vector(artifact)

        self.assertEqual(schema[0], "pressure.pv")
        self.assertEqual(schema[9], "rpm.pv")
        self.assertEqual(schema[18], "temperature.pv")
        self.assertEqual(values[0], 5.1)
        self.assertEqual(values[1], 13.2)
        self.assertEqual(values[9], 3110.0)
        self.assertEqual(values[18], 70.5)
        self.assertEqual(len(schema), 27)
        self.assertEqual(len(values), 27)

    def test_evaluate_training_eligibility_rejects_non_normal_records(self) -> None:
        missing_context = build_persisted_artifact(index=1)
        missing_context.pop("dataset_context")
        scada_divergent = build_persisted_artifact(
            index=2,
            scenario_label="scada_divergence",
            training_eligible=False,
            has_scada_divergence=True,
        )
        faulty_edge = build_persisted_artifact(
            index=3,
            scenario_label="faulty_edge_exclusion",
            training_eligible=False,
        )

        self.assertEqual(
            evaluate_training_eligibility(missing_context),
            (False, "missing_dataset_context"),
        )
        self.assertEqual(
            evaluate_training_eligibility(scada_divergent),
            (False, "training_label_not_normal"),
        )
        self.assertEqual(
            evaluate_training_eligibility(faulty_edge),
            (False, "training_label_not_normal"),
        )

    def test_build_normal_training_windows_reads_minio_and_emits_manifest(self) -> None:
        store = self.build_store()
        for index in range(1, 5):
            artifact = build_persisted_artifact(index=index)
            store.save_json(artifact["artifact_key"], artifact)

        windows, manifest = build_normal_training_windows(
            artifact_store=store,
            sequence_length=3,
        )

        self.assertEqual(len(windows), 2)
        self.assertEqual(windows[0].round_ids, ("round-501", "round-502", "round-503"))
        self.assertEqual(windows[1].round_ids, ("round-502", "round-503", "round-504"))
        self.assertEqual(manifest.sequence_length, 3)
        self.assertEqual(manifest.eligible_record_count, 4)
        self.assertEqual(manifest.window_count, 2)
        self.assertEqual(
            manifest.selected_artifact_keys[0],
            "valid-consensus-artifacts/round-501.json",
        )
        self.assertEqual(manifest.skipped_artifacts, {})
        self.assertIn("temperature.pv", manifest.feature_schema)

    def test_build_normal_training_windows_filters_non_normal_and_divergent_records(self) -> None:
        store = self.build_store()
        normal = build_persisted_artifact(index=1)
        faulty = build_persisted_artifact(
            index=2,
            scenario_label="faulty_edge_exclusion",
            training_eligible=False,
        )
        divergent = build_persisted_artifact(
            index=3,
            scenario_label="scada_divergence",
            training_eligible=False,
            has_scada_divergence=True,
        )
        mismatched_schema = deepcopy(build_persisted_artifact(index=4))
        del mismatched_schema["validated_state"]["structured_payload_snapshot"][
            "payloads_by_sensor"
        ]["temperature"]

        for artifact in (normal, faulty, divergent, mismatched_schema):
            store.save_json(artifact["artifact_key"], artifact)

        windows, manifest = build_normal_training_windows(
            artifact_store=store,
            sequence_length=2,
        )

        self.assertEqual(windows, ())
        self.assertEqual(manifest.eligible_record_count, 1)
        self.assertEqual(manifest.window_count, 0)
        self.assertEqual(
            manifest.skipped_artifacts["valid-consensus-artifacts/round-502.json"],
            "training_label_not_normal",
        )
        self.assertEqual(
            manifest.skipped_artifacts["valid-consensus-artifacts/round-503.json"],
            "training_label_not_normal",
        )
        self.assertEqual(
            manifest.skipped_artifacts["valid-consensus-artifacts/round-504.json"],
            "feature_schema_mismatch",
        )


if __name__ == "__main__":
    unittest.main()
