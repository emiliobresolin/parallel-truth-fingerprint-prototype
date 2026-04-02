"""Focused tests for Epic 4 Story 4.4 replay-oriented anomaly behavior."""

from __future__ import annotations

import unittest
from unittest import mock

from parallel_truth_fingerprint.contracts.fingerprint_inference import (
    FingerprintInferenceClassification,
    FingerprintInferenceResult,
)
from parallel_truth_fingerprint.lstm_service import (
    REPLAY_OUTPUT_CHANNEL,
    ScadaReplayRuntimeStage,
    configure_scada_replay_runtime_stage,
    load_persisted_training_dataset_artifacts,
    persist_scada_replay_inference_dataset,
    run_scada_replay_behavior_detection,
)
from parallel_truth_fingerprint.persistence import MinioArtifactStore, MinioStoreConfig
from parallel_truth_fingerprint.scada import FakeOpcUaScadaService
from tests.lstm_service.test_dataset_builder import build_persisted_artifact
from tests.persistence.test_service import FakeMinioClient, build_valid_audit_package


class ReplayBehaviorTests(unittest.TestCase):
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

    def seed_persisted_artifacts(self, store: MinioArtifactStore) -> None:
        for index in range(1, 4):
            store.save_json(
                f"valid-consensus-artifacts/round-50{index}.json",
                build_persisted_artifact(index=index),
            )
        store.save_json(
            "valid-consensus-artifacts/round-504.json",
            build_persisted_artifact(
                index=4,
                scenario_label="scada_replay",
                training_eligible=False,
            ),
        )

    def test_configure_scada_replay_runtime_stage_activates_after_start_cycle(self) -> None:
        scada_service = FakeOpcUaScadaService(compressor_id="compressor-1")
        scada_service.update_from_consensused_state(
            build_valid_audit_package(round_id="round-001").consensused_valid_state
        )
        scada_service.update_from_consensused_state(
            build_valid_audit_package(round_id="round-002").consensused_valid_state
        )
        config = type(
            "Config",
            (),
            {
                "demo_scada_mode": "replay",
                "demo_scada_start_cycle": 2,
            },
        )()

        inactive_stage = configure_scada_replay_runtime_stage(
            scada_service=scada_service,
            config=config,
            cycle_index=1,
        )
        active_stage = configure_scada_replay_runtime_stage(
            scada_service=scada_service,
            config=config,
            cycle_index=2,
        )

        self.assertFalse(inactive_stage.active)
        self.assertEqual(inactive_stage.mode, "match")
        self.assertTrue(active_stage.active)
        self.assertEqual(active_stage.mode, "replay")
        self.assertEqual(active_stage.replay_source_round_id, "round-001")

    def test_persist_scada_replay_inference_dataset_reuses_stale_history(self) -> None:
        store = self.build_store()
        self.seed_persisted_artifacts(store)
        replay_stage = ScadaReplayRuntimeStage(
            active=True,
            mode="replay",
            start_cycle=4,
            replay_source_round_id="round-501",
        )

        persisted_dataset = persist_scada_replay_inference_dataset(
            artifact_store=store,
            current_round_id="round-504",
            replay_stage=replay_stage,
            sequence_length=2,
        )
        windows, manifest = load_persisted_training_dataset_artifacts(
            manifest_object_key=persisted_dataset.manifest_object_key,
            artifact_store=store,
        )

        self.assertEqual(manifest.training_label, "replay_evaluation")
        self.assertEqual(manifest.window_count, 1)
        self.assertEqual(
            manifest.selected_artifact_keys,
            (
                "valid-consensus-artifacts/round-503.json",
                "valid-consensus-artifacts/round-501.json",
            ),
        )
        self.assertEqual(len(windows), 1)
        self.assertEqual(
            windows[0].round_ids,
            ("round-503", "round-501"),
        )
        manifest_payload = store.load_json(persisted_dataset.manifest_object_key)
        self.assertEqual(
            manifest_payload["adequacy_assessment"]["validation_level"],
            "runtime_valid_only",
        )

    def test_persist_scada_replay_inference_dataset_supports_freeze_by_reusing_previous_round(
        self,
    ) -> None:
        store = self.build_store()
        self.seed_persisted_artifacts(store)
        freeze_stage = ScadaReplayRuntimeStage(
            active=True,
            mode="freeze",
            start_cycle=4,
        )

        persisted_dataset = persist_scada_replay_inference_dataset(
            artifact_store=store,
            current_round_id="round-504",
            replay_stage=freeze_stage,
            sequence_length=2,
        )
        windows, manifest = load_persisted_training_dataset_artifacts(
            manifest_object_key=persisted_dataset.manifest_object_key,
            artifact_store=store,
        )

        self.assertEqual(manifest.training_label, "freeze_evaluation")
        self.assertEqual(
            windows[0].artifact_keys,
            (
                "valid-consensus-artifacts/round-503.json",
                "valid-consensus-artifacts/round-503.json",
            ),
        )

    def test_run_scada_replay_behavior_detection_wraps_generic_inference_in_distinct_channel(
        self,
    ) -> None:
        store = self.build_store()
        store.save_json(
            "fingerprint-models/model-001.json",
            {"model_id": "model-001"},
        )
        replay_stage = ScadaReplayRuntimeStage(
            active=True,
            mode="replay",
            start_cycle=4,
            replay_source_round_id="round-501",
        )
        comparison_output = type(
            "ComparisonOutput",
            (),
            {"divergent_sensors": ("temperature", "pressure")},
        )()
        scada_state = type("ScadaState", (), {"source_round_id": "round-504"})()
        fake_persisted_dataset = type(
            "PersistedDataset",
            (),
            {
                "manifest_object_key": "fingerprint-datasets/replay.manifest.json",
            },
        )()
        fake_inference_result = FingerprintInferenceResult(
            output_channel="lstm_fingerprint",
            model_id="model-001",
            source_dataset_id="training-dataset::round-501::round-503::seq-2",
            inference_dataset_id="replay-dataset::round-504::replay::round-501::seq-2",
            source_dataset_validation_level="runtime_valid_only",
            limitation_note="runtime-valid only",
            window_id="replay-window::round-504::round-501",
            artifact_keys=(
                "valid-consensus-artifacts/round-503.json",
                "valid-consensus-artifacts/round-501.json",
            ),
            round_ids=("round-503", "round-501"),
            timestamps=(
                "2026-04-01T18:03:00+00:00",
                "2026-04-01T18:01:00+00:00",
            ),
            anomaly_score=0.5,
            classification_threshold=0.1,
            threshold_origin="source_dataset_mean_plus_3std",
            classification=FingerprintInferenceClassification.ANOMALOUS,
        )

        with mock.patch(
            "parallel_truth_fingerprint.lstm_service.replay_behavior.persist_scada_replay_inference_dataset",
            return_value=fake_persisted_dataset,
        ) as persist_dataset:
            with mock.patch(
                "parallel_truth_fingerprint.lstm_service.replay_behavior.run_lstm_fingerprint_inference_from_persisted_dataset",
                return_value=(fake_inference_result,),
            ) as run_inference:
                replay_result, inference_results = run_scada_replay_behavior_detection(
                    current_round_id="round-504",
                    consensus_final_status="success",
                    scada_state=scada_state,
                    comparison_output=comparison_output,
                    replay_stage=replay_stage,
                    artifact_store=store,
                    sequence_length=2,
                )

        persist_dataset.assert_called_once()
        run_inference.assert_called_once()
        self.assertEqual(
            run_inference.call_args.kwargs["threshold_stddev_multiplier"],
            0.0,
        )
        self.assertEqual(inference_results, (fake_inference_result,))
        self.assertIsNotNone(replay_result)
        self.assertEqual(replay_result.output_channel, REPLAY_OUTPUT_CHANNEL)
        self.assertEqual(replay_result.scenario_mode, "replay")
        self.assertEqual(replay_result.classification.value, "anomalous")
        self.assertEqual(
            replay_result.scada_divergent_sensors,
            ("temperature", "pressure"),
        )
        self.assertEqual(replay_result.consensus_final_status, "success")
        self.assertEqual(replay_result.source_dataset_validation_level, "runtime_valid_only")


if __name__ == "__main__":
    unittest.main()
