"""Evaluation closure for synchronized custom current/syscall campaigns.

This is deliberately separate from public benchmark adapters.  It evaluates
the persisted runtime-autoencoder classifications against the scenario labels
of a finite custom campaign; it neither retrains the model nor recasts public
datasets as compressor/current data.
"""

from __future__ import annotations

from collections import Counter
from datetime import datetime, timezone
from hashlib import sha256
import json
from pathlib import Path
import uuid

from parallel_truth_fingerprint.lstm_service.offline_training.splits import SplitRecord
from parallel_truth_fingerprint.lstm_service.offline_training.training.metrics import (
    compute_classification_metrics,
)
from parallel_truth_fingerprint.lstm_service.offline_training.training.run import (
    TrainingRunRecord,
)


CUSTOM_DATASET_NAME = "custom-current-syscall"


def build_custom_campaign_evaluation(
    dataset_files: tuple[Path, ...], *, seed: int = 42
) -> TrainingRunRecord:
    """Build an honest held-out-like record from persisted campaign rows.

    A row is normal only when its scenario label is exactly ``normal``.  A
    non-normal scenario is the positive anomaly class.  The prediction comes
    solely from the autoencoder result that contains that row's ``round_id``;
    missing or unrelated results fail closed rather than being counted.
    """

    if len(dataset_files) < 2:
        raise ValueError("At least one normal and one non-normal campaign file are required.")
    truths: list[int] = []
    predictions: list[int] = []
    campaign_ids: list[str] = []
    file_hashes: dict[str, str] = {}
    for path in dataset_files:
        source = Path(path)
        payload = source.read_bytes()
        file_hashes[str(source.resolve())] = f"sha256:{sha256(payload).hexdigest()}"
        for raw_line in payload.decode("utf-8").splitlines():
            if not raw_line.strip():
                continue
            row = json.loads(raw_line)
            round_id = _require_string(row, "round_id", source)
            campaign_ids.append(_require_string(row, "campaign_id", source))
            label = _require_string(row, "scenario_label", source)
            result = _result_for_round(row, round_id, source)
            truths.append(0 if label == "normal" else 1)
            predictions.append(1 if result["classification"] == "anomalous" else 0)
    if not truths or len(set(truths)) != 2:
        raise ValueError("Campaign evaluation requires both normal and non-normal rows.")

    metrics = compute_classification_metrics(predictions, truths, class_count=2)
    count = len(truths)
    test_counts = dict(Counter(truths))
    return TrainingRunRecord(
        run_id=f"run-custom-current-syscall-runtime-autoencoder-{datetime.now(timezone.utc):%Y%m%dT%H%M%S}-{uuid.uuid4().hex[:8]}",
        created_at=datetime.now(timezone.utc).isoformat(),
        dataset_name=CUSTOM_DATASET_NAME,
        model_name="runtime-lstm-autoencoder+edge-syscalls",
        seed=seed,
        sequence_length=2,
        epochs_planned=0,
        epochs_executed=0,
        hyperparameters={
            "evaluation_mode": "persisted_runtime_inference",
            "campaign_ids": tuple(sorted(set(campaign_ids))),
        },
        metrics=metrics.as_run_metric_dict(),
        per_class_metrics={
            "precision": metrics.per_class_precision,
            "recall": metrics.per_class_recall,
            "f1": metrics.per_class_f1,
            "false_positive_rate": metrics.per_class_false_positive_rate,
        },
        parameter_count=0,
        split_record=SplitRecord(
            seed=seed,
            train_ratio=0.0,
            total_samples=count,
            train_samples=0,
            test_samples=count,
            per_class_counts_train={},
            per_class_counts_test=test_counts,
        ),
        confusion_matrix=metrics.confusion_matrix,
        dataset_provenance={
            "origin": "PTFP synchronized live compressor campaign",
            "year": datetime.now(timezone.utc).year,
            "version": "PTFP-Custom-current-syscall-v1",
            "citation": "Locally captured runtime artifacts, 4-20 mA feature contract and Linux edge syscall traces.",
            "campaign_ids": tuple(sorted(set(campaign_ids))),
            "dataset_file_sha256": file_hashes,
            "row_count": count,
            "evaluation_unit": "one persisted runtime inference per campaign row",
            "limitation": "Short integration campaign; this is traceability evidence, not a statistically powered generalization claim.",
        },
        label_names=("Normal", "NonNormalScenario"),
    )


def _require_string(row: object, key: str, source: Path) -> str:
    value = row.get(key) if isinstance(row, dict) else None
    if not isinstance(value, str) or not value:
        raise ValueError(f"{source} has no valid {key!r}.")
    return value


def _result_for_round(row: object, round_id: str, source: Path) -> dict[str, object]:
    results = row.get("autoencoder_results") if isinstance(row, dict) else None
    if not isinstance(results, list):
        raise ValueError(f"{source} has no autoencoder result list.")
    matching = [
        result
        for result in results
        if isinstance(result, dict)
        and round_id in result.get("round_ids", ())
        and result.get("classification") in {"normal", "anomalous"}
    ]
    if len(matching) != 1:
        raise ValueError(
            f"{source} must contain exactly one autoencoder result for round {round_id}; found {len(matching)}."
        )
    return matching[0]
