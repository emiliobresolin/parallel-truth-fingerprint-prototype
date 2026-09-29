"""Scientific metrics for the isolated academic evaluation path.

The legacy offline-training metrics intentionally keep their historical
zero-on-undefined behaviour.  This module is stricter: an undefined statistic
is represented by ``None`` together with a reason, thresholds are calibrated
from validation data only, and uncertainty is resampled at the independent
unit level (never at the overlapping-window level).
"""

from __future__ import annotations

from dataclasses import dataclass
from hashlib import sha256
import itertools
import json
import math
from statistics import mean, median, stdev
from typing import Callable, Iterable, Mapping, Sequence

import numpy as np


Scalar = float | None


def _canonical_hash(value: object) -> str:
    payload = json.dumps(
        value, sort_keys=True, separators=(",", ":"), ensure_ascii=False
    ).encode("utf-8")
    return f"sha256:{sha256(payload).hexdigest()}"


def _safe_ratio(numerator: int | float, denominator: int | float) -> Scalar:
    return None if denominator == 0 else float(numerator) / float(denominator)


@dataclass(frozen=True)
class ThresholdCalibration:
    """A validation-derived operating point frozen before test evaluation."""

    method: str
    value: float
    direction: str
    validation_support: dict[str, int]
    objective_name: str
    objective_value: Scalar
    sensitivity: tuple[dict[str, object], ...]
    identity: str

    def to_dict(self) -> dict[str, object]:
        return {
            "method": self.method,
            "value": self.value,
            "direction": self.direction,
            "validation_support": dict(self.validation_support),
            "objective_name": self.objective_name,
            "objective_value": self.objective_value,
            "sensitivity": [dict(row) for row in self.sensitivity],
            "identity": self.identity,
        }


def calibrate_threshold(
    scores: Sequence[float],
    truths: Sequence[int],
    *,
    method: str,
    quantile: float = 0.99,
    target_fpr: float = 0.01,
    sensitivity_quantiles: Sequence[float] = (0.90, 0.95, 0.975, 0.99, 0.995),
) -> ThresholdCalibration:
    """Calibrate a high-score-means-anomaly threshold on validation only.

    ``normal-quantile`` and ``target-fpr`` require only validation normals and
    are therefore suitable for normal-only anomaly-detector calibration.
    ``max-f1`` is available when a labelled validation partition contains both
    classes.  Callers must never pass test arrays; the runner enforces the
    partition role and records the calibration identity.
    """

    score_array, truth_array = _validated_binary_arrays(scores, truths)
    normal_scores = score_array[truth_array == 0]
    attack_scores = score_array[truth_array == 1]
    if normal_scores.size == 0:
        raise ValueError("Threshold calibration requires validation normal units.")
    normalized_sensitivity_quantiles = tuple(
        float(value) for value in sensitivity_quantiles
    )
    if (
        not normalized_sensitivity_quantiles
        or len(set(normalized_sensitivity_quantiles))
        != len(normalized_sensitivity_quantiles)
        or any(
            not math.isfinite(value) or not 0.0 < value < 1.0
            for value in normalized_sensitivity_quantiles
        )
    ):
        raise ValueError(
            "sensitivity_quantiles must be unique finite values strictly between zero and one."
        )

    if method == "normal-quantile":
        if not 0.0 < quantile < 1.0:
            raise ValueError("quantile must be strictly between zero and one.")
        threshold, attainable_fpr = _threshold_at_or_below_fpr(
            normal_scores, 1.0 - quantile
        )
        objective_name = "attained_validation_normal_fpr"
        objective_value: Scalar = attainable_fpr
    elif method == "target-fpr":
        if not 0.0 < target_fpr < 1.0:
            raise ValueError("target_fpr must be strictly between zero and one.")
        threshold, attainable_fpr = _threshold_at_or_below_fpr(
            normal_scores, target_fpr
        )
        objective_name = "attained_validation_normal_fpr"
        objective_value = attainable_fpr
    elif method == "max-f1":
        if attack_scores.size == 0:
            raise ValueError("max-f1 calibration requires validation attacks.")
        candidates = _candidate_thresholds(score_array)
        ranked: list[tuple[float, float, float]] = []
        for candidate in candidates:
            metrics = binary_operating_metrics(score_array, truth_array, candidate)
            f1 = metrics["f1"]
            fpr = metrics["false_positive_rate"]
            ranked.append(
                (
                    -1.0 if f1 is None else float(f1),
                    1.0 if fpr is None else float(fpr),
                    float(candidate),
                )
            )
        best = max(ranked, key=lambda row: (row[0], -row[1], row[2]))
        threshold = best[2]
        objective_name = "validation_f1"
        objective_value = best[0]
    else:
        raise ValueError(f"Unsupported threshold calibration method: {method!r}.")

    sensitivity_rows: list[dict[str, object]] = []
    for candidate_quantile in normalized_sensitivity_quantiles:
        candidate, attainable_fpr = _threshold_at_or_below_fpr(
            normal_scores, 1.0 - candidate_quantile
        )
        metrics = binary_operating_metrics(score_array, truth_array, candidate)
        sensitivity_rows.append(
            {
                "normal_quantile": candidate_quantile,
                "threshold": candidate,
                "attained_normal_fpr": attainable_fpr,
                "false_positive_rate": metrics["false_positive_rate"],
                "recall": metrics["recall"],
                "f1": metrics["f1"],
            }
        )

    support = {
        "total": int(truth_array.size),
        "normal": int(normal_scores.size),
        "attack": int(attack_scores.size),
    }
    identity_payload = {
        "method": method,
        "value": threshold,
        "direction": "higher-is-more-anomalous",
        "validation_support": support,
        "objective_name": objective_name,
        "objective_value": objective_value,
        "sensitivity_quantiles": list(normalized_sensitivity_quantiles),
        "score_sha256": _array_hash(score_array),
        "truth_sha256": _array_hash(truth_array),
    }
    return ThresholdCalibration(
        method=method,
        value=threshold,
        direction="higher-is-more-anomalous",
        validation_support=support,
        objective_name=objective_name,
        objective_value=objective_value,
        sensitivity=tuple(sensitivity_rows),
        identity=_canonical_hash(identity_payload),
    )


def binary_operating_metrics(
    scores: Sequence[float] | np.ndarray,
    truths: Sequence[int] | np.ndarray,
    threshold: float,
) -> dict[str, object]:
    """Return reconstructible binary operating-point metrics."""

    score_array, truth_array = _validated_binary_arrays(scores, truths)
    predictions = (score_array >= float(threshold)).astype(np.int64)
    tp = int(np.sum((truth_array == 1) & (predictions == 1)))
    tn = int(np.sum((truth_array == 0) & (predictions == 0)))
    fp = int(np.sum((truth_array == 0) & (predictions == 1)))
    fn = int(np.sum((truth_array == 1) & (predictions == 0)))
    precision = _safe_ratio(tp, tp + fp)
    recall = _safe_ratio(tp, tp + fn)
    specificity = _safe_ratio(tn, tn + fp)
    fpr = _safe_ratio(fp, fp + tn)
    fnr = _safe_ratio(fn, fn + tp)
    f1 = (
        None
        if precision is None or recall is None or precision + recall == 0.0
        else 2.0 * precision * recall / (precision + recall)
    )
    accuracy = _safe_ratio(tp + tn, tp + tn + fp + fn)
    balanced_accuracy = (
        None
        if recall is None or specificity is None
        else (recall + specificity) / 2.0
    )
    denominator = math.sqrt(
        float((tp + fp) * (tp + fn) * (tn + fp) * (tn + fn))
    )
    mcc = None if denominator == 0.0 else ((tp * tn) - (fp * fn)) / denominator
    undefined: dict[str, str] = {}
    for name, value in (
        ("precision", precision),
        ("recall", recall),
        ("specificity", specificity),
        ("false_positive_rate", fpr),
        ("false_negative_rate", fnr),
        ("f1", f1),
        ("accuracy", accuracy),
        ("balanced_accuracy", balanced_accuracy),
        ("mcc", mcc),
    ):
        if value is None:
            undefined[name] = "denominator is zero for the observed support"
    return {
        "threshold": float(threshold),
        "support": {
            "total": int(truth_array.size),
            "normal": int(np.sum(truth_array == 0)),
            "attack": int(np.sum(truth_array == 1)),
        },
        "confusion_matrix": {"tn": tn, "fp": fp, "fn": fn, "tp": tp},
        "accuracy": accuracy,
        "precision": precision,
        "recall": recall,
        "specificity": specificity,
        "f1": f1,
        "false_positive_rate": fpr,
        "false_negative_rate": fnr,
        "balanced_accuracy": balanced_accuracy,
        "mcc": mcc,
        "alert_rate": float(np.mean(predictions)),
        "undefined": undefined,
    }


def ranking_metrics(
    scores: Sequence[float] | np.ndarray,
    truths: Sequence[int] | np.ndarray,
) -> dict[str, object]:
    """Compute tie-aware AUROC and average precision without sklearn."""

    score_array, truth_array = _validated_binary_arrays(scores, truths)
    positives = int(np.sum(truth_array == 1))
    negatives = int(np.sum(truth_array == 0))
    undefined: dict[str, str] = {}
    if positives == 0 or negatives == 0:
        auroc: Scalar = None
        undefined["auroc"] = "both normal and attack support are required"
    else:
        ranks = _average_ranks(score_array)
        positive_rank_sum = float(np.sum(ranks[truth_array == 1]))
        auroc = (
            positive_rank_sum - (positives * (positives + 1) / 2.0)
        ) / float(positives * negatives)

    if positives == 0:
        auprc: Scalar = None
        undefined["auprc"] = "attack support is required"
    else:
        # Aggregate tied scores before advancing recall.  This makes AP
        # invariant to row order within a tied-score group.
        order = np.argsort(-score_array, kind="stable")
        ordered_scores = score_array[order]
        ordered_truth = truth_array[order]
        cumulative_tp = 0
        cumulative_fp = 0
        average_precision = 0.0
        start = 0
        while start < ordered_scores.size:
            end = start + 1
            while end < ordered_scores.size and ordered_scores[end] == ordered_scores[start]:
                end += 1
            group = ordered_truth[start:end]
            newly_positive = int(np.sum(group == 1))
            cumulative_tp += newly_positive
            cumulative_fp += int(np.sum(group == 0))
            precision_at_threshold = cumulative_tp / (cumulative_tp + cumulative_fp)
            average_precision += (newly_positive / positives) * precision_at_threshold
            start = end
        auprc = float(average_precision)

    return {
        "auroc": auroc,
        "auprc": auprc,
        "positive_prevalence": float(positives / truth_array.size),
        "undefined": undefined,
    }


def curve_points(
    scores: Sequence[float] | np.ndarray,
    truths: Sequence[int] | np.ndarray,
    *,
    max_points: int = 201,
) -> dict[str, list[dict[str, Scalar]]]:
    """Return compact ROC/PR points sufficient for reconstruction/plotting."""

    if not isinstance(max_points, int) or isinstance(max_points, bool) or max_points < 2:
        raise ValueError("max_points must be an integer of at least two.")
    score_array, truth_array = _validated_binary_arrays(scores, truths)
    candidates = _candidate_thresholds(score_array)
    if len(candidates) > max_points:
        positions = np.linspace(0, len(candidates) - 1, max_points, dtype=int)
        candidates = tuple(candidates[index] for index in positions.tolist())
    roc: list[dict[str, Scalar]] = []
    pr: list[dict[str, Scalar]] = []
    for threshold in reversed(candidates):
        values = binary_operating_metrics(score_array, truth_array, threshold)
        roc.append(
            {
                "threshold": float(threshold),
                "false_positive_rate": values["false_positive_rate"],  # type: ignore[dict-item]
                "true_positive_rate": values["recall"],  # type: ignore[dict-item]
            }
        )
        pr.append(
            {
                "threshold": float(threshold),
                "precision": values["precision"],  # type: ignore[dict-item]
                "recall": values["recall"],  # type: ignore[dict-item]
            }
        )
    return {"roc": roc, "precision_recall": pr}


def score_distribution(
    scores: Sequence[float] | np.ndarray,
    truths: Sequence[int] | np.ndarray,
) -> dict[str, dict[str, Scalar | int]]:
    score_array, truth_array = _validated_binary_arrays(scores, truths)
    return {
        name: _distribution(score_array[truth_array == label])
        for label, name in ((0, "normal"), (1, "attack"))
    }


def bootstrap_confidence_intervals(
    scores: Sequence[float] | np.ndarray,
    truths: Sequence[int] | np.ndarray,
    *,
    threshold: float,
    replicates: int,
    confidence_level: float,
    seed: int,
    cluster_ids: Sequence[str] | None = None,
    minimum_clusters: int = 2,
    minimum_class_carrying_clusters: int | None = None,
    minimum_valid_replicates: int | None = None,
    minimum_valid_fraction: float | None = None,
) -> dict[str, object]:
    """Bootstrap intervals at the declared independent sampling level.

    With no ``cluster_ids`` this is a class-stratified independent-unit
    bootstrap.  Supplying cluster identities switches to a cluster bootstrap:
    whole clusters are sampled and all observations belonging to a selected
    cluster travel together.  This prevents adjacent HAI blocks (or blocks
    belonging to one event/recording) from being treated as independent.

    Class-stratified intervals condition on the class support created by the
    frozen sampling design.  That qualification is returned with the numeric
    intervals instead of being left implicit.

    Clustered inference is fail-closed.  Its per-class cluster requirement and
    its minimum count and fraction of resamples containing both labels must be
    supplied explicitly from the preregistered protocol.  Keeping these
    arguments optional preserves the legacy call surface, but omitting any of
    them yields undefined clustered intervals rather than an implicit default.
    """

    if (
        not isinstance(replicates, int)
        or isinstance(replicates, bool)
        or replicates < 1
    ):
        raise ValueError("bootstrap replicates must be a positive integer.")
    if (
        not isinstance(confidence_level, (int, float))
        or isinstance(confidence_level, bool)
        or not math.isfinite(float(confidence_level))
        or not 0.0 < float(confidence_level) < 1.0
    ):
        raise ValueError("confidence_level must be between zero and one.")
    if (
        not isinstance(minimum_clusters, int)
        or isinstance(minimum_clusters, bool)
        or minimum_clusters < 2
    ):
        raise ValueError("minimum_clusters must be an integer of at least two.")
    if minimum_class_carrying_clusters is not None and (
        not isinstance(minimum_class_carrying_clusters, int)
        or isinstance(minimum_class_carrying_clusters, bool)
        or minimum_class_carrying_clusters < 2
    ):
        raise ValueError(
            "minimum_class_carrying_clusters must be an integer of at least two."
        )
    if minimum_valid_replicates is not None and (
        not isinstance(minimum_valid_replicates, int)
        or isinstance(minimum_valid_replicates, bool)
        or not 1 <= minimum_valid_replicates <= replicates
    ):
        raise ValueError(
            "minimum_valid_replicates must be an integer between one and "
            "the planned bootstrap replicate count."
        )
    if minimum_valid_fraction is not None and (
        not isinstance(minimum_valid_fraction, (int, float))
        or isinstance(minimum_valid_fraction, bool)
        or not math.isfinite(float(minimum_valid_fraction))
        or not 0.0 < float(minimum_valid_fraction) <= 1.0
    ):
        raise ValueError(
            "minimum_valid_fraction must be finite and greater than zero and "
            "at most one."
        )
    score_array, truth_array = _validated_binary_arrays(scores, truths)
    if cluster_ids is not None and len(cluster_ids) != score_array.size:
        raise ValueError("cluster_ids must align with scores and truths.")
    rng = np.random.default_rng(int(seed))
    names = (
        "accuracy",
        "precision",
        "recall",
        "specificity",
        "f1",
        "false_positive_rate",
        "false_negative_rate",
        "balanced_accuracy",
        "mcc",
        "auroc",
        "auprc",
    )
    samples: dict[str, list[float]] = {name: [] for name in names}
    design: dict[str, object]
    sampler: Callable[[], np.ndarray] | None
    invalid_reasons: list[dict[str, object]] = []
    if cluster_ids is None:
        by_label = [np.flatnonzero(truth_array == label) for label in (0, 1)]

        def sample_units() -> np.ndarray:
            sampled_parts = [
                rng.choice(indices, size=indices.size, replace=True)
                for indices in by_label
                if indices.size
            ]
            return np.concatenate(sampled_parts)

        sampler = sample_units
        design = {
            "method": "class-stratified independent-unit percentile bootstrap",
            "resampling_unit": "independent test unit",
            "independent_cluster_count": int(score_array.size),
            "minimum_clusters_required": minimum_clusters,
            "normal_cluster_count": int(np.sum(truth_array == 0)),
            "attack_cluster_count": int(np.sum(truth_array == 1)),
            "conditional_on_sampled_prevalence": True,
            "inferentially_valid": True,
            "undefined_reason": None,
            "undefined_reason_code": None,
            "undefined_reasons": [],
            "qualification": (
                "Intervals for prevalence-sensitive metrics are conditional on "
                "the frozen sampled class support; they do not estimate native prevalence uncertainty."
            ),
        }
    else:
        stable_clusters = tuple(str(value) for value in cluster_ids)
        if any(not value for value in stable_clusters):
            raise ValueError("cluster_ids must be non-empty stable identifiers.")
        members: dict[str, np.ndarray] = {
            cluster: np.flatnonzero(np.asarray(stable_clusters, dtype=object) == cluster)
            for cluster in sorted(set(stable_clusters))
        }
        labels_by_cluster = {
            cluster: frozenset(int(value) for value in truth_array[indices].tolist())
            for cluster, indices in members.items()
        }
        pure_clusters = all(len(labels) == 1 for labels in labels_by_cluster.values())
        normal_clusters = [
            cluster for cluster, labels in labels_by_cluster.items() if labels == {0}
        ]
        attack_clusters = [
            cluster for cluster, labels in labels_by_cluster.items() if labels == {1}
        ]
        normal_class_carrying_clusters = [
            cluster for cluster, labels in labels_by_cluster.items() if 0 in labels
        ]
        attack_class_carrying_clusters = [
            cluster for cluster, labels in labels_by_cluster.items() if 1 in labels
        ]
        if len(members) < minimum_clusters:
            invalid_reasons.append(
                {
                    "code": "insufficient_independent_clusters",
                    "message": (
                        f"at least {minimum_clusters} independent clusters are required; "
                        f"observed {len(members)}"
                    ),
                    "observed": len(members),
                    "required": minimum_clusters,
                }
            )
        missing_criteria = [
            name
            for name, value in (
                (
                    "minimum_class_carrying_clusters",
                    minimum_class_carrying_clusters,
                ),
                ("minimum_valid_replicates", minimum_valid_replicates),
                ("minimum_valid_fraction", minimum_valid_fraction),
            )
            if value is None
        ]
        if missing_criteria:
            invalid_reasons.append(
                {
                    "code": "bootstrap_criteria_not_preregistered",
                    "message": (
                        "cluster bootstrap requires explicit preregistered "
                        "class-carrying support and valid-replicate criteria"
                    ),
                    "missing_fields": missing_criteria,
                }
            )
        if minimum_class_carrying_clusters is not None:
            for class_label, class_name, observed in (
                (0, "normal", len(normal_class_carrying_clusters)),
                (1, "attack", len(attack_class_carrying_clusters)),
            ):
                if observed < minimum_class_carrying_clusters:
                    invalid_reasons.append(
                        {
                            "code": "insufficient_class_carrying_clusters",
                            "message": (
                                f"at least {minimum_class_carrying_clusters} independent "
                                f"clusters carrying class {class_label} ({class_name}) are "
                                f"required; observed {observed}"
                            ),
                            "class_label": class_label,
                            "class_name": class_name,
                            "observed": observed,
                            "required": minimum_class_carrying_clusters,
                        }
                    )

        if invalid_reasons:
            sampler = None
        elif pure_clusters:

            def sample_pure_clusters() -> np.ndarray:
                selected: list[np.ndarray] = []
                for population in (normal_clusters, attack_clusters):
                    draws = rng.choice(population, size=len(population), replace=True)
                    selected.extend(members[str(cluster)] for cluster in draws.tolist())
                return np.concatenate(selected)

            sampler = sample_pure_clusters
        else:
            population = tuple(members)

            def sample_mixed_clusters() -> np.ndarray:
                draws = rng.choice(population, size=len(population), replace=True)
                return np.concatenate([members[str(cluster)] for cluster in draws.tolist()])

            sampler = sample_mixed_clusters
        design = {
            "method": (
                "class-stratified cluster percentile bootstrap"
                if pure_clusters
                else "whole-cluster percentile bootstrap"
            ),
            "resampling_unit": "declared independent cluster",
            "independent_cluster_count": len(members),
            "minimum_clusters_required": minimum_clusters,
            "normal_cluster_count": len(normal_clusters),
            "attack_cluster_count": len(attack_clusters),
            "normal_class_carrying_cluster_count": len(
                normal_class_carrying_clusters
            ),
            "attack_class_carrying_cluster_count": len(
                attack_class_carrying_clusters
            ),
            "minimum_class_carrying_clusters_required": (
                minimum_class_carrying_clusters
            ),
            "mixed_label_cluster_count": sum(
                1 for labels in labels_by_cluster.values() if len(labels) > 1
            ),
            "minimum_valid_replicates_required": minimum_valid_replicates,
            "minimum_valid_fraction_required": minimum_valid_fraction,
            "attempted_replicates": 0,
            "valid_mixed_label_replicates": 0,
            "invalid_single_label_replicates": 0,
            "valid_mixed_label_fraction": None,
            "conditional_on_sampled_prevalence": bool(pure_clusters),
            "inferentially_valid": not invalid_reasons,
            "undefined_reason": (
                "; ".join(str(reason["message"]) for reason in invalid_reasons)
                if invalid_reasons
                else None
            ),
            "undefined_reason_code": (
                str(invalid_reasons[0]["code"]) if invalid_reasons else None
            ),
            "undefined_reasons": invalid_reasons,
            "qualification": (
                "Whole clusters, never adjacent blocks, are resampled. "
                + (
                    "Prevalence-sensitive intervals remain conditional on frozen per-class cluster support."
                    if pure_clusters
                    else "Mixed-label clusters allow sampled prevalence to vary across replicates."
                )
            ),
        }

    attempted_replicates = 0
    valid_mixed_label_replicates = 0
    for _ in range(replicates if sampler is not None else 0):
        sampled = sampler()
        attempted_replicates += 1
        if cluster_ids is not None:
            sampled_truth = truth_array[sampled]
            if not (np.any(sampled_truth == 0) and np.any(sampled_truth == 1)):
                continue
            valid_mixed_label_replicates += 1
        operating = binary_operating_metrics(
            score_array[sampled], truth_array[sampled], threshold
        )
        ranking = ranking_metrics(score_array[sampled], truth_array[sampled])
        combined = {**operating, **ranking}
        for name in names:
            value = combined.get(name)
            if isinstance(value, (int, float)) and math.isfinite(float(value)):
                samples[name].append(float(value))

    if cluster_ids is not None:
        valid_fraction = (
            float(valid_mixed_label_replicates / attempted_replicates)
            if attempted_replicates
            else None
        )
        if sampler is not None:
            count_requirement_met = (
                minimum_valid_replicates is not None
                and valid_mixed_label_replicates >= minimum_valid_replicates
            )
            fraction_requirement_met = (
                minimum_valid_fraction is not None
                and valid_fraction is not None
                and valid_fraction >= float(minimum_valid_fraction)
            )
            if not count_requirement_met or not fraction_requirement_met:
                invalid_reasons.append(
                    {
                        "code": "insufficient_valid_mixed_label_replicates",
                        "message": (
                            "mixed-label cluster bootstrap valid-replicate criterion "
                            "was not met"
                        ),
                        "attempted_replicates": attempted_replicates,
                        "valid_replicates": valid_mixed_label_replicates,
                        "valid_fraction": valid_fraction,
                        "minimum_valid_replicates_required": (
                            minimum_valid_replicates
                        ),
                        "minimum_valid_fraction_required": minimum_valid_fraction,
                        "count_requirement_met": count_requirement_met,
                        "fraction_requirement_met": fraction_requirement_met,
                    }
                )
        design.update(
            {
                "attempted_replicates": attempted_replicates,
                "valid_mixed_label_replicates": valid_mixed_label_replicates,
                "invalid_single_label_replicates": (
                    attempted_replicates - valid_mixed_label_replicates
                ),
                "valid_mixed_label_fraction": valid_fraction,
                "inferentially_valid": not invalid_reasons,
                "undefined_reason": (
                    "; ".join(str(reason["message"]) for reason in invalid_reasons)
                    if invalid_reasons
                    else None
                ),
                "undefined_reason_code": (
                    str(invalid_reasons[0]["code"]) if invalid_reasons else None
                ),
                "undefined_reasons": invalid_reasons,
            }
        )

    point = {
        **binary_operating_metrics(score_array, truth_array, threshold),
        **ranking_metrics(score_array, truth_array),
    }
    alpha = (1.0 - confidence_level) / 2.0
    result: dict[str, object] = {"design": design}
    for name in names:
        values = samples[name]
        estimate = point.get(name)
        interval_reason_code: str | None = None
        interval_reason: str | None = None
        if not bool(design["inferentially_valid"]):
            interval_reason_code = str(design["undefined_reason_code"])
            interval_reason = str(design["undefined_reason"])
        elif cluster_ids is not None:
            metric_valid_fraction = (
                float(len(values) / attempted_replicates)
                if attempted_replicates
                else 0.0
            )
            if (
                minimum_valid_replicates is not None
                and minimum_valid_fraction is not None
                and (
                    len(values) < minimum_valid_replicates
                    or metric_valid_fraction < float(minimum_valid_fraction)
                )
            ):
                interval_reason_code = "insufficient_valid_metric_replicates"
                interval_reason = (
                    "metric-specific finite bootstrap replicates did not meet the "
                    "preregistered count and fraction criteria"
                )
        interval_defined = bool(values) and interval_reason_code is None
        result[name] = {
            "estimate": float(estimate)
            if isinstance(estimate, (int, float))
            else None,
            "low": float(np.quantile(values, alpha)) if interval_defined else None,
            "high": (
                float(np.quantile(values, 1.0 - alpha))
                if interval_defined
                else None
            ),
            "valid_replicates": len(values),
            "planned_replicates": replicates,
            "attempted_replicates": attempted_replicates,
            "valid_replicate_fraction": (
                float(len(values) / attempted_replicates)
                if attempted_replicates
                else None
            ),
            "interval_defined": interval_defined,
            "undefined_reason_code": interval_reason_code,
            "undefined_reason": interval_reason,
        }
    return result


def per_class_detection_metrics(
    scores: Sequence[float],
    binary_truths: Sequence[int],
    class_names: Sequence[str],
    *,
    threshold: float,
) -> dict[str, dict[str, object]]:
    """Detection metrics per attack family, each compared with all normals."""

    if not (len(scores) == len(binary_truths) == len(class_names)):
        raise ValueError("scores, truths, and class_names must align.")
    score_array, truth_array = _validated_binary_arrays(scores, binary_truths)
    normalized_scores = score_array.tolist()
    normalized_truths = truth_array.tolist()
    results: dict[str, dict[str, object]] = {}
    unique_attacks = sorted(
        {name for name, truth in zip(class_names, normalized_truths) if truth == 1}
    )
    for attack_name in unique_attacks:
        keep = [
            index
            for index, (truth, name) in enumerate(zip(normalized_truths, class_names))
            if truth == 0 or name == attack_name
        ]
        subset_scores = [normalized_scores[index] for index in keep]
        subset_truths = [normalized_truths[index] for index in keep]
        results[attack_name] = {
            **binary_operating_metrics(subset_scores, subset_truths, threshold),
            **ranking_metrics(subset_scores, subset_truths),
        }
    return results


def event_metrics(
    predictions: Sequence[int],
    truths: Sequence[int],
    event_ids: Sequence[Sequence[str]],
) -> dict[str, object]:
    """Compute event detection without treating windows as events."""

    if not (len(predictions) == len(truths) == len(event_ids)):
        raise ValueError("predictions, truths, and event_ids must align.")
    _, truth_array = _validated_binary_arrays(
        np.zeros(len(truths), dtype=np.float64), truths
    )
    _, prediction_array = _validated_binary_arrays(
        np.zeros(len(predictions), dtype=np.float64), predictions
    )
    known_events: set[str] = set()
    detected_events: set[str] = set()
    false_alert_units = 0
    for prediction, truth, ids in zip(
        prediction_array.tolist(), truth_array.tolist(), event_ids
    ):
        if truth == 0 and prediction == 1:
            false_alert_units += 1
        if truth == 1:
            stable_ids = set(ids) or {"event-without-published-identifier"}
            known_events.update(stable_ids)
            if prediction == 1:
                detected_events.update(stable_ids)
    return {
        "event_count": len(known_events),
        "detected_event_count": len(detected_events),
        "event_recall": _safe_ratio(len(detected_events), len(known_events)),
        "false_alert_unit_count": false_alert_units,
    }


def aggregate_repeated_estimates(
    values: Sequence[float], *, confidence_level: float = 0.95
) -> dict[str, Scalar | int]:
    """Describe independent-trial estimates without hiding dispersion."""

    if not 0.0 < confidence_level < 1.0:
        raise ValueError("confidence_level must be between zero and one.")
    clean = [float(value) for value in values if math.isfinite(float(value))]
    if not clean:
        return {
            "n": 0,
            "mean": None,
            "sd": None,
            "median": None,
            "iqr": None,
            "ci_low": None,
            "ci_high": None,
            "ci_method": "undefined: no finite independent trials",
        }
    estimate = mean(clean)
    sample_sd = stdev(clean) if len(clean) >= 2 else None
    if sample_sd is None:
        ci_low = ci_high = None
        ci_method = "undefined: at least two independent trials are required"
    else:
        critical = _student_t_quantile(
            0.5 + confidence_level / 2.0, degrees_of_freedom=len(clean) - 1
        )
        margin = critical * sample_sd / math.sqrt(len(clean))
        ci_low, ci_high = estimate - margin, estimate + margin
        ci_method = f"two-sided Student-t interval, df={len(clean) - 1}"
    q25, q75 = np.quantile(np.asarray(clean), (0.25, 0.75)).tolist()
    return {
        "n": len(clean),
        "mean": float(estimate),
        "sd": float(sample_sd) if sample_sd is not None else None,
        "median": float(median(clean)),
        "iqr": float(q75 - q25),
        "ci_low": float(ci_low) if ci_low is not None else None,
        "ci_high": float(ci_high) if ci_high is not None else None,
        "ci_method": ci_method,
    }


def derive_repetition_count(
    pilot_values: Sequence[float | None],
    *,
    target_half_width: float,
    confidence_level: float,
    minimum: int,
    maximum: int,
    required_pilot_trials: int | None = None,
    fixed_execution_trials: int | None = None,
) -> dict[str, object]:
    """Describe prospective precision from pilot dispersion, never epochs/windows.

    The pilot sample standard deviation is a point estimate only.  Prospective
    half-widths use the degrees of freedom of the *future* sample size, not the
    pilot degrees of freedom.  A fixed execution schedule is reported
    separately and is never shortened by this calculation.
    """

    if minimum < 2 or maximum < minimum:
        raise ValueError("Require 2 <= minimum <= maximum.")
    if target_half_width <= 0.0:
        raise ValueError("target_half_width must be positive.")
    if not 0.0 < confidence_level < 1.0:
        raise ValueError("confidence_level must be strictly between zero and one.")
    if required_pilot_trials is not None and required_pilot_trials < 2:
        raise ValueError("required_pilot_trials must be at least two when supplied.")
    if fixed_execution_trials is not None and fixed_execution_trials != maximum:
        raise ValueError("fixed_execution_trials must equal the configured maximum cap.")
    attempted = len(pilot_values)
    clean = [
        float(value)
        for value in pilot_values
        if isinstance(value, (int, float))
        and not isinstance(value, bool)
        and math.isfinite(float(value))
    ]
    required_outcomes_finite = (
        required_pilot_trials is None
        or (
            attempted == required_pilot_trials
            and len(clean) == required_pilot_trials
        )
    )
    probability = 0.5 + confidence_level / 2.0

    def prospective_half_width(sample_sd: float, trials: int) -> float:
        critical = _student_t_quantile(
            probability, degrees_of_freedom=trials - 1
        )
        return critical * sample_sd / math.sqrt(trials)

    def prospective_required_trials(sample_sd: float) -> int:
        if sample_sd == 0.0:
            return 2
        upper = 2
        while prospective_half_width(sample_sd, upper) > target_half_width:
            if upper >= 2_147_483_647:
                raise ArithmeticError(
                    "Prospective repetition need exceeds the supported integer range."
                )
            upper = min(upper * 2, 2_147_483_647)
        lower = 2
        while lower < upper:
            midpoint = (lower + upper) // 2
            if prospective_half_width(sample_sd, midpoint) <= target_half_width:
                upper = midpoint
            else:
                lower = midpoint + 1
        return lower

    uncapped_required: int | None
    recommended: int | None
    projected_half_width_at_cap: Scalar
    projected_half_width_at_recommended: Scalar
    if len(clean) < 2 or not required_outcomes_finite:
        uncapped_required = None
        recommended = None if required_pilot_trials is not None else maximum
        projected_half_width_at_cap = None
        projected_half_width_at_recommended = None
        reason = (
            f"precision planning is indeterminate: all {required_pilot_trials} "
            "pilot primary outcomes must be present and finite"
            if required_pilot_trials is not None
            else "fewer than two valid pilot trials"
        )
        observed_sd: Scalar = stdev(clean) if len(clean) >= 2 else None
    else:
        observed_sd = stdev(clean)
        uncapped_required = prospective_required_trials(observed_sd)
        recommended = min(max(uncapped_required, minimum), maximum)
        projected_half_width_at_cap = prospective_half_width(observed_sd, maximum)
        projected_half_width_at_recommended = (
            prospective_half_width(observed_sd, recommended)
        )
        reason = (
            "pilot variance was zero; fixed confirmatory cap remains unchanged"
            if observed_sd == 0.0 and fixed_execution_trials is not None
            else "pilot variance was zero; minimum repetition floor retained"
            if observed_sd == 0.0
            else (
                "prospective Student-t precision calculation from pilot SD; frozen cap "
                "binds before the target width but does not adapt execution"
                if uncapped_required > maximum
                else "prospective Student-t precision calculation from pilot SD; execution remains fixed"
                if fixed_execution_trials is not None
                else "Student-t precision calculation from pilot SD"
            )
        )
    return {
        "pilot_trials": attempted,
        "pilot_trials_expected": required_pilot_trials,
        "finite_pilot_trials": len(clean),
        "all_required_pilot_outcomes_finite": required_outcomes_finite,
        "planning_determinate": uncapped_required is not None,
        "observed_sd": observed_sd,
        "target_ci_half_width": target_half_width,
        "confidence_level": confidence_level,
        "minimum": minimum,
        "maximum": maximum,
        "configured_trial_cap": maximum,
        "operational_trial_cap": maximum,
        "uncapped_required_trials": uncapped_required,
        "recommended_total_trials": recommended,
        "fixed_execution_trials": fixed_execution_trials,
        "scheduled_execution_trials": fixed_execution_trials or recommended,
        "execution_schedule_adaptive": False if fixed_execution_trials is not None else None,
        "scheduled_cap_reached": (
            fixed_execution_trials == maximum
            if fixed_execution_trials is not None
            else recommended == maximum
            if recommended is not None
            else None
        ),
        "operational_cap_reached": None,
        "operational_cap_reached_reason": (
            "not observable from pilot precision planning; authenticate completed "
            "confirmatory trials separately"
        ),
        "projected_ci_half_width_at_cap": projected_half_width_at_cap,
        "projected_ci_half_width_at_recommended": projected_half_width_at_recommended,
        "precision_target_projected_met_at_cap": (
            None
            if projected_half_width_at_cap is None
            else projected_half_width_at_cap <= target_half_width + 1e-15
        ),
        "precision_target_projected_met": (
            None
            if projected_half_width_at_recommended is None
            else projected_half_width_at_recommended <= target_half_width + 1e-15
        ),
        "maximum_cap_binding": (
            None if uncapped_required is None else uncapped_required > maximum
        ),
        "precision_claim_status": "projection-only-not-a-sufficiency-guarantee",
        "dispersion_estimate_scope": "point sample SD from independent pilot seeds",
        "dispersion_estimate_limitations": [
            "Five pilot outcomes provide a fragile point estimate of training variability.",
            "No upper confidence bound for the population variance is applied.",
            "Seed replication cannot replace missing independent units or clusters.",
        ],
        "reason": reason,
        "planning_method": (
            "prospective pilot-SD Student-t precision projection at a fixed nonadaptive cap"
            if fixed_execution_trials is not None
            else "pilot-SD Student-t precision bound with frozen floor/cap"
        ),
    }


def paired_comparison(
    left: Mapping[int, float],
    right: Mapping[int, float],
    *,
    seed: int = 0,
    monte_carlo_replicates: int = 20_000,
    left_randomness: str = "seeded",
    right_randomness: str = "seeded",
) -> dict[str, object]:
    """Paired effect and two-sided sign-flip permutation significance."""

    if left_randomness not in {"seeded", "deterministic"}:
        raise ValueError("left_randomness must be 'seeded' or 'deterministic'.")
    if right_randomness not in {"seeded", "deterministic"}:
        raise ValueError("right_randomness must be 'seeded' or 'deterministic'.")
    if monte_carlo_replicates < 1:
        raise ValueError("monte_carlo_replicates must be positive.")
    if left_randomness == "deterministic" or right_randomness == "deterministic":
        left_values = [float(value) for value in left.values() if math.isfinite(float(value))]
        right_values = [float(value) for value in right.values() if math.isfinite(float(value))]
        descriptive = (
            float(mean(left_values) - mean(right_values))
            if left_values and right_values
            else None
        )
        return {
            "paired_trials": 0,
            "mean_difference": descriptive,
            "cohen_dz": None,
            "p_value": None,
            "method": "descriptive difference only",
            "status": "descriptive-only",
            "undefined": (
                "inferential pairing requires genuine matched stochastic trials on both sides; "
                "deterministic estimates are never replicated across seed identifiers"
            ),
            "left_randomness": left_randomness,
            "right_randomness": right_randomness,
        }

    shared = sorted(set(left) & set(right))
    differences = np.asarray([left[key] - right[key] for key in shared], dtype=float)
    if differences.size < 2:
        return {
            "paired_trials": int(differences.size),
            "mean_difference": float(np.mean(differences)) if differences.size else None,
            "cohen_dz": None,
            "p_value": None,
            "status": "undefined",
            "undefined": "at least two paired trials are required",
        }
    mean_difference = float(np.mean(differences))
    sd_difference = float(np.std(differences, ddof=1))
    numerical_zero = max(abs(mean_difference), 1.0) * 1e-12
    cohen_dz = None if abs(sd_difference) <= numerical_zero else mean_difference / sd_difference
    observed = abs(mean_difference)
    if differences.size <= 16:
        permutations: Iterable[tuple[int, ...]] = itertools.product(
            (-1, 1), repeat=int(differences.size)
        )
        extreme = total = 0
        for signs in permutations:
            permuted = abs(float(np.mean(differences * np.asarray(signs))))
            extreme += int(permuted >= observed - 1e-15)
            total += 1
        p_value = extreme / total
        method = "exact paired sign-flip permutation"
    else:
        rng = np.random.default_rng(seed)
        extreme = 0
        for _ in range(monte_carlo_replicates):
            signs = rng.choice((-1.0, 1.0), size=differences.size)
            extreme += int(abs(float(np.mean(differences * signs))) >= observed)
        p_value = (extreme + 1) / (monte_carlo_replicates + 1)
        method = "Monte Carlo paired sign-flip permutation"
    return {
        "paired_trials": int(differences.size),
        "mean_difference": mean_difference,
        "sd_difference": sd_difference,
        "cohen_dz": cohen_dz,
        "p_value": float(p_value),
        "method": method,
        "status": "inferential",
    }


def holm_adjust(p_values: Mapping[str, Scalar]) -> dict[str, Scalar]:
    """Holm family-wise correction, retaining undefined comparisons."""

    defined = sorted(
        ((name, float(value)) for name, value in p_values.items() if value is not None),
        key=lambda row: row[1],
    )
    adjusted: dict[str, Scalar] = {name: None for name in p_values}
    running = 0.0
    count = len(defined)
    for rank, (name, value) in enumerate(defined):
        running = max(running, min(1.0, (count - rank) * value))
        adjusted[name] = running
    return adjusted


def _validated_binary_arrays(
    scores: Sequence[float] | np.ndarray,
    truths: Sequence[int] | np.ndarray,
) -> tuple[np.ndarray, np.ndarray]:
    score_array = np.asarray(scores, dtype=np.float64).reshape(-1)
    raw_truths = np.asarray(truths, dtype=object).reshape(-1)
    normalized_truths: list[int] = []
    for index, value in enumerate(raw_truths.tolist()):
        if isinstance(value, (bool, np.bool_)):
            raise ValueError(f"truths[{index}] must not be Boolean.")
        if isinstance(value, (int, np.integer)):
            normalized = int(value)
        elif isinstance(value, (float, np.floating)):
            numeric = float(value)
            if not math.isfinite(numeric):
                raise ValueError(f"truths[{index}] is non-finite.")
            if not numeric.is_integer():
                raise ValueError(f"truths[{index}] is fractional.")
            normalized = int(numeric)
        else:
            raise ValueError(
                f"truths[{index}] must be an integer-valued numeric label."
            )
        if normalized not in {0, 1}:
            raise ValueError("truths must contain only binary labels 0 and 1.")
        normalized_truths.append(normalized)
    truth_array = np.asarray(normalized_truths, dtype=np.int64)
    if score_array.size == 0:
        raise ValueError("scores must not be empty.")
    if score_array.size != truth_array.size:
        raise ValueError("scores and truths must align.")
    if not np.all(np.isfinite(score_array)):
        raise ValueError("scores must all be finite.")
    return score_array, truth_array


def _candidate_thresholds(scores: np.ndarray) -> tuple[float, ...]:
    unique = np.unique(scores)
    if unique.size == 1:
        value = float(unique[0])
        return (math.nextafter(value, -math.inf), value, math.nextafter(value, math.inf))
    midpoints = (unique[:-1] + unique[1:]) / 2.0
    return tuple(
        [math.nextafter(float(unique[0]), -math.inf)]
        + [float(value) for value in midpoints]
        + [math.nextafter(float(unique[-1]), math.inf)]
    )


def _threshold_at_or_below_fpr(
    normal_scores: np.ndarray, target_fpr: float
) -> tuple[float, float]:
    """Choose the most permissive attainable threshold not exceeding FPR."""

    candidates = _candidate_thresholds(np.asarray(normal_scores, dtype=float))
    attainable: list[tuple[float, float]] = []
    for candidate in candidates:
        observed = float(np.mean(normal_scores >= candidate))
        if observed <= target_fpr + 1e-15:
            attainable.append((float(candidate), observed))
    if not attainable:
        threshold = math.nextafter(float(np.max(normal_scores)), math.inf)
        return threshold, 0.0
    # Lowest threshold is the most sensitive while respecting the bound.
    return min(attainable, key=lambda row: row[0])


def _average_ranks(values: np.ndarray) -> np.ndarray:
    order = np.argsort(values, kind="stable")
    ranks = np.empty(values.size, dtype=float)
    start = 0
    while start < values.size:
        end = start + 1
        while end < values.size and values[order[end]] == values[order[start]]:
            end += 1
        average_rank = ((start + 1) + end) / 2.0
        ranks[order[start:end]] = average_rank
        start = end
    return ranks


def _distribution(values: np.ndarray) -> dict[str, Scalar | int]:
    if values.size == 0:
        return {
            "n": 0,
            "mean": None,
            "sd": None,
            "min": None,
            "q25": None,
            "median": None,
            "q75": None,
            "max": None,
        }
    quantiles = np.quantile(values, (0.0, 0.25, 0.5, 0.75, 1.0)).tolist()
    return {
        "n": int(values.size),
        "mean": float(np.mean(values)),
        "sd": float(np.std(values, ddof=1)) if values.size > 1 else None,
        "min": float(quantiles[0]),
        "q25": float(quantiles[1]),
        "median": float(quantiles[2]),
        "q75": float(quantiles[3]),
        "max": float(quantiles[4]),
    }


def _array_hash(values: np.ndarray) -> str:
    contiguous = np.ascontiguousarray(values)
    digest = sha256()
    digest.update(str(contiguous.dtype).encode("ascii"))
    digest.update(str(contiguous.shape).encode("ascii"))
    digest.update(contiguous.tobytes())
    return f"sha256:{digest.hexdigest()}"


def _normal_quantile(probability: float) -> float:
    """Acklam's inverse-normal approximation (adequate for CI planning)."""

    if not 0.0 < probability < 1.0:
        raise ValueError("probability must be strictly between zero and one.")
    a = (
        -39.69683028665376,
        220.9460984245205,
        -275.9285104469687,
        138.357751867269,
        -30.66479806614716,
        2.506628277459239,
    )
    b = (
        -54.47609879822406,
        161.5858368580409,
        -155.6989798598866,
        66.80131188771972,
        -13.28068155288572,
    )
    c = (
        -0.007784894002430293,
        -0.3223964580411365,
        -2.400758277161838,
        -2.549732539343734,
        4.374664141464968,
        2.938163982698783,
    )
    d = (
        0.007784695709041462,
        0.3224671290700398,
        2.445134137142996,
        3.754408661907416,
    )
    lower = 0.02425
    upper = 1.0 - lower
    if probability < lower:
        q = math.sqrt(-2.0 * math.log(probability))
        return (
            (((((c[0] * q + c[1]) * q + c[2]) * q + c[3]) * q + c[4]) * q + c[5])
            / ((((d[0] * q + d[1]) * q + d[2]) * q + d[3]) * q + 1.0)
        )
    if probability > upper:
        q = math.sqrt(-2.0 * math.log(1.0 - probability))
        return -(
            (((((c[0] * q + c[1]) * q + c[2]) * q + c[3]) * q + c[4]) * q + c[5])
            / ((((d[0] * q + d[1]) * q + d[2]) * q + d[3]) * q + 1.0)
        )
    q = probability - 0.5
    r = q * q
    return (
        (((((a[0] * r + a[1]) * r + a[2]) * r + a[3]) * r + a[4]) * r + a[5])
        * q
        / (((((b[0] * r + b[1]) * r + b[2]) * r + b[3]) * r + b[4]) * r + 1.0)
    )


def _student_t_quantile(probability: float, *, degrees_of_freedom: int) -> float:
    """Numerically invert the Student-t CDF without an optional SciPy dependency."""

    if not 0.0 < probability < 1.0:
        raise ValueError("probability must be strictly between zero and one.")
    if degrees_of_freedom < 1:
        raise ValueError("degrees_of_freedom must be positive.")
    if probability == 0.5:
        return 0.0
    if probability < 0.5:
        return -_student_t_quantile(
            1.0 - probability, degrees_of_freedom=degrees_of_freedom
        )
    low, high = 0.0, max(1.0, _normal_quantile(probability))
    while _student_t_cdf(high, degrees_of_freedom) < probability:
        high *= 2.0
        if high > 1e12:
            raise ArithmeticError("Student-t quantile failed to bracket the probability.")
    for _ in range(120):
        midpoint = (low + high) / 2.0
        if _student_t_cdf(midpoint, degrees_of_freedom) < probability:
            low = midpoint
        else:
            high = midpoint
    return (low + high) / 2.0


def _student_t_cdf(value: float, degrees_of_freedom: int) -> float:
    if value == 0.0:
        return 0.5
    degrees = float(degrees_of_freedom)
    x = degrees / (degrees + value * value)
    tail = 0.5 * _regularized_incomplete_beta(degrees / 2.0, 0.5, x)
    return 1.0 - tail if value > 0.0 else tail


def _regularized_incomplete_beta(a: float, b: float, x: float) -> float:
    """Regularized incomplete beta via a stable continued fraction."""

    if x <= 0.0:
        return 0.0
    if x >= 1.0:
        return 1.0
    log_prefactor = (
        math.lgamma(a + b)
        - math.lgamma(a)
        - math.lgamma(b)
        + a * math.log(x)
        + b * math.log1p(-x)
    )
    prefactor = math.exp(log_prefactor)
    if x < (a + 1.0) / (a + b + 2.0):
        return prefactor * _beta_continued_fraction(a, b, x) / a
    return 1.0 - prefactor * _beta_continued_fraction(b, a, 1.0 - x) / b


def _beta_continued_fraction(a: float, b: float, x: float) -> float:
    max_iterations = 300
    epsilon = 3e-14
    floor = 1e-300
    qab = a + b
    qap = a + 1.0
    qam = a - 1.0
    c = 1.0
    d = 1.0 - qab * x / qap
    if abs(d) < floor:
        d = floor
    d = 1.0 / d
    result = d
    for iteration in range(1, max_iterations + 1):
        doubled = 2 * iteration
        numerator = iteration * (b - iteration) * x / (
            (qam + doubled) * (a + doubled)
        )
        d = 1.0 + numerator * d
        if abs(d) < floor:
            d = floor
        c = 1.0 + numerator / c
        if abs(c) < floor:
            c = floor
        d = 1.0 / d
        result *= d * c
        numerator = -(a + iteration) * (qab + iteration) * x / (
            (a + doubled) * (qap + doubled)
        )
        d = 1.0 + numerator * d
        if abs(d) < floor:
            d = floor
        c = 1.0 + numerator / c
        if abs(c) < floor:
            c = floor
        d = 1.0 / d
        delta = d * c
        result *= delta
        if abs(delta - 1.0) <= epsilon:
            return result
    raise ArithmeticError("Incomplete-beta continued fraction did not converge.")


__all__ = [
    "ThresholdCalibration",
    "aggregate_repeated_estimates",
    "binary_operating_metrics",
    "bootstrap_confidence_intervals",
    "calibrate_threshold",
    "curve_points",
    "derive_repetition_count",
    "event_metrics",
    "holm_adjust",
    "paired_comparison",
    "per_class_detection_metrics",
    "ranking_metrics",
    "score_distribution",
]
