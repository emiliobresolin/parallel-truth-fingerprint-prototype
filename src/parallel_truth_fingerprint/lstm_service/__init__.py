"""LSTM dataset-building and model-service package."""

from parallel_truth_fingerprint.lstm_service.dataset_builder import (
    build_normal_training_windows,
    evaluate_training_eligibility,
    extract_feature_vector,
)
from parallel_truth_fingerprint.lstm_service.dataset_artifacts import (
    evaluate_training_dataset_adequacy,
    load_persisted_training_dataset_artifacts,
    persist_training_dataset_artifacts,
)
from parallel_truth_fingerprint.lstm_service.inference import (
    run_lstm_fingerprint_inference_from_persisted_dataset,
)
from parallel_truth_fingerprint.lstm_service.lifecycle import (
    FingerprintLifecycleStage,
    execute_deferred_fingerprint_lifecycle,
    latest_model_metadata_key,
)
from parallel_truth_fingerprint.lstm_service.replay_behavior import (
    REPLAY_OUTPUT_CHANNEL,
    ScadaReplayRuntimeStage,
    configure_scada_replay_runtime_stage,
    persist_scada_replay_inference_dataset,
    run_scada_replay_behavior_detection,
)
from parallel_truth_fingerprint.lstm_service.trainer import (
    build_lstm_autoencoder,
    train_and_save_lstm_fingerprint,
    train_and_save_lstm_fingerprint_from_persisted_dataset,
)

__all__ = [
    "build_normal_training_windows",
    "build_lstm_autoencoder",
    "evaluate_training_eligibility",
    "evaluate_training_dataset_adequacy",
    "extract_feature_vector",
    "configure_scada_replay_runtime_stage",
    "execute_deferred_fingerprint_lifecycle",
    "FingerprintLifecycleStage",
    "load_persisted_training_dataset_artifacts",
    "latest_model_metadata_key",
    "persist_training_dataset_artifacts",
    "persist_scada_replay_inference_dataset",
    "REPLAY_OUTPUT_CHANNEL",
    "run_lstm_fingerprint_inference_from_persisted_dataset",
    "run_scada_replay_behavior_detection",
    "ScadaReplayRuntimeStage",
    "train_and_save_lstm_fingerprint",
    "train_and_save_lstm_fingerprint_from_persisted_dataset",
]
