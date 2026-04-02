"""Focused tests for Epic 4 Story 4.3A lifecycle orchestration."""

from __future__ import annotations

from datetime import datetime, timedelta, timezone
from unittest import mock
import unittest

from parallel_truth_fingerprint.comparison import (
    ScadaToleranceProfile,
    build_scada_comparison_output,
    compare_consensused_to_scada,
)
from parallel_truth_fingerprint.contracts.fingerprint_inference import (
    FingerprintInferenceClassification,
    FingerprintInferenceResult,
)
from parallel_truth_fingerprint.lstm_service.lifecycle import (
    execute_deferred_fingerprint_lifecycle,
)
from parallel_truth_fingerprint.persistence import (
    MinioArtifactStore,
    MinioStoreConfig,
    persist_valid_consensus_artifact,
)
from parallel_truth_fingerprint.scada import FakeOpcUaScadaService
from tests.persistence.test_service import FakeMinioClient, build_valid_audit_package


def persist_valid_training_artifact(
    *,
    artifact_store,
    round_id: str,
    minute_offset: int,
    scenario_label: str = "normal",
    training_label: str = "normal",
    training_eligible: bool = True,
    training_reason: str = "story_4_3a_test",
) -> None:
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
    persist_valid_consensus_artifact(
        audit_package=audit_package,
        scada_state=scada_state,
        scada_comparison_output=comparison_output,
        dataset_context={
            "scenario_label": scenario_label,
            "training_label": training_label,
            "training_eligible": training_eligible,
            "training_eligibility_reason": training_reason,
        },
        artifact_store=artifact_store,
        persisted_at=datetime(2026, 4, 2, 20, 0, 0, tzinfo=timezone.utc)
        + timedelta(minutes=minute_offset),
    )


class FingerprintLifecycleTests(unittest.TestCase):
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

    def test_lifecycle_defers_training_until_history_threshold_is_reached(self) -> None:
        store = self.build_store()
        persist_valid_training_artifact(
            artifact_store=store,
            round_id="round-001",
            minute_offset=0,
        )
        persist_valid_training_artifact(
            artifact_store=store,
            round_id="round-002",
            minute_offset=1,
        )

        stage, inference_results = execute_deferred_fingerprint_lifecycle(
            cycle_index=2,
            artifact_store=store,
            sequence_length=2,
            train_after_eligible_cycles=3,
        )

        self.assertEqual(stage.valid_artifact_count, 2)
        self.assertEqual(stage.eligible_history_count, 2)
        self.assertEqual(stage.window_count, 1)
        self.assertEqual(stage.model_status, "no_model_yet")
        self.assertEqual(stage.training_events, ("deferred",))
        self.assertEqual(stage.inference_status, "skipped_no_model")
        self.assertEqual(stage.inference_result_count, 0)
        self.assertEqual(stage.latest_valid_artifact_key, "valid-consensus-artifacts/round-002.json")
        self.assertEqual(inference_results, ())

    def test_lifecycle_trains_once_when_threshold_is_reached(self) -> None:
        store = self.build_store()
        for minute_offset, round_id in enumerate(("round-001", "round-002", "round-003")):
            persist_valid_training_artifact(
                artifact_store=store,
                round_id=round_id,
                minute_offset=minute_offset,
            )

        fake_adequacy = type(
            "Adequacy",
            (),
            {"validation_level": "runtime_valid_only"},
        )()
        fake_persisted_dataset = type(
            "PersistedDataset",
            (),
            {
                "manifest_object_key": "fingerprint-datasets/runtime.manifest.json",
                "adequacy_assessment": fake_adequacy,
            },
        )()
        fake_model_metadata = type(
            "ModelMetadata",
            (),
            {"metadata_object_key": "fingerprint-models/lstm-runtime.json"},
        )()

        with mock.patch(
            "parallel_truth_fingerprint.lstm_service.lifecycle.persist_training_dataset_artifacts",
            return_value=fake_persisted_dataset,
        ) as persist_dataset:
            with mock.patch(
                "parallel_truth_fingerprint.lstm_service.lifecycle.train_and_save_lstm_fingerprint_from_persisted_dataset",
                return_value=fake_model_metadata,
            ) as train_model:
                stage, inference_results = execute_deferred_fingerprint_lifecycle(
                    cycle_index=3,
                    artifact_store=store,
                    sequence_length=2,
                    train_after_eligible_cycles=3,
                )

        persist_dataset.assert_called_once()
        train_model.assert_called_once()
        self.assertEqual(stage.valid_artifact_count, 3)
        self.assertEqual(stage.eligible_history_count, 3)
        self.assertEqual(stage.window_count, 2)
        self.assertEqual(stage.model_status, "model_available")
        self.assertEqual(stage.training_events, ("started", "completed"))
        self.assertEqual(stage.inference_status, "skipped_until_next_cycle")
        self.assertEqual(
            stage.dataset_manifest_object_key,
            "fingerprint-datasets/runtime.manifest.json",
        )
        self.assertEqual(
            stage.model_metadata_object_key,
            "fingerprint-models/lstm-runtime.json",
        )
        self.assertEqual(stage.source_dataset_validation_level, "runtime_valid_only")
        self.assertEqual(inference_results, ())

    def test_lifecycle_reuses_saved_model_without_retraining(self) -> None:
        store = self.build_store()
        for minute_offset, round_id in enumerate(("round-001", "round-002", "round-003")):
            persist_valid_training_artifact(
                artifact_store=store,
                round_id=round_id,
                minute_offset=minute_offset,
            )
        store.save_json(
            "fingerprint-models/existing-model.json",
            {"model_id": "existing-model"},
        )

        fake_adequacy = type(
            "Adequacy",
            (),
            {"validation_level": "runtime_valid_only"},
        )()
        fake_persisted_dataset = type(
            "PersistedDataset",
            (),
            {
                "manifest_object_key": "fingerprint-datasets/runtime.manifest.json",
                "adequacy_assessment": fake_adequacy,
            },
        )()
        fake_inference_result = FingerprintInferenceResult(
            output_channel="lstm_fingerprint",
            model_id="existing-model",
            source_dataset_id="training-dataset::round-001::round-003::seq-2",
            inference_dataset_id="training-dataset::round-001::round-003::seq-2",
            source_dataset_validation_level="runtime_valid_only",
            limitation_note="runtime-valid only",
            window_id="window::round-001::round-002",
            artifact_keys=(
                "valid-consensus-artifacts/round-001.json",
                "valid-consensus-artifacts/round-002.json",
            ),
            round_ids=("round-001", "round-002"),
            timestamps=(
                "2026-04-02T20:00:00+00:00",
                "2026-04-02T20:01:00+00:00",
            ),
            anomaly_score=0.01,
            classification_threshold=0.02,
            threshold_origin="source_dataset_mean_plus_3std",
            classification=FingerprintInferenceClassification.NORMAL,
        )

        with mock.patch(
            "parallel_truth_fingerprint.lstm_service.lifecycle.persist_training_dataset_artifacts",
            return_value=fake_persisted_dataset,
        ) as persist_dataset:
            with mock.patch(
                "parallel_truth_fingerprint.lstm_service.lifecycle.train_and_save_lstm_fingerprint_from_persisted_dataset",
            ) as train_model:
                with mock.patch(
                    "parallel_truth_fingerprint.lstm_service.lifecycle.run_lstm_fingerprint_inference_from_persisted_dataset",
                    return_value=(fake_inference_result,),
                ) as run_inference:
                    stage, inference_results = execute_deferred_fingerprint_lifecycle(
                        cycle_index=4,
                        artifact_store=store,
                        sequence_length=2,
                        train_after_eligible_cycles=3,
                    )

        persist_dataset.assert_called_once()
        train_model.assert_not_called()
        run_inference.assert_called_once()
        self.assertEqual(stage.model_status, "model_available")
        self.assertEqual(stage.training_events, ("reused",))
        self.assertEqual(stage.inference_status, "completed")
        self.assertEqual(stage.inference_result_count, 1)
        self.assertEqual(
            stage.model_metadata_object_key,
            "fingerprint-models/existing-model.json",
        )
        self.assertEqual(stage.source_dataset_validation_level, "runtime_valid_only")
        self.assertEqual(inference_results, (fake_inference_result,))


if __name__ == "__main__":
    unittest.main()
