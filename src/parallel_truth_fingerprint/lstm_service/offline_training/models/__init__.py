"""Supervised classifier implementations for the offline training track.

DummyClassifier (Story 7.1) is a deterministic majority-class baseline used
purely to exercise the pipeline end-to-end. Real LSTM (Story 7.5) and GRU
(Story 7.8) classifiers register themselves on import below.
"""

from parallel_truth_fingerprint.lstm_service.offline_training.models.base import (
    ClassifierAdapter,
    list_available_models,
    load_model,
)
from parallel_truth_fingerprint.lstm_service.offline_training.models.dummy import (
    DummyClassifier,
)
# Importing the LSTM/GRU modules triggers their register_model() side-effects
# so `load_model("lstm-classifier")` / `load_model("gru-classifier")` work
# without an explicit register call from the caller.
from parallel_truth_fingerprint.lstm_service.offline_training.models import (
    lstm_classifier as _lstm_classifier_registration,  # noqa: F401
)
from parallel_truth_fingerprint.lstm_service.offline_training.models import (
    gru_classifier as _gru_classifier_registration,  # noqa: F401
)

__all__ = [
    "ClassifierAdapter",
    "DummyClassifier",
    "list_available_models",
    "load_model",
]
