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
    "load_persisted_training_dataset_artifacts",
    "persist_training_dataset_artifacts",
    "run_lstm_fingerprint_inference_from_persisted_dataset",
    "train_and_save_lstm_fingerprint",
    "train_and_save_lstm_fingerprint_from_persisted_dataset",
]
