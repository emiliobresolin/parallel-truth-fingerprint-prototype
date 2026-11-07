"""Explicit calibration rules for replay, preserving the historical protocol."""
import math

LEGACY = 'mean-plus-3std'
COMMON = 'target-fpr'


def calibrate(scores, rule=LEGACY):
    values = [float(s) for s in scores]
    if not values or any(not math.isfinite(s) for s in values):
        raise ValueError('Finite, nonempty normal calibration scores required.')
    if rule == LEGACY:
        from .replay_evaluation import fixed_threshold
        return fixed_threshold(values)
    if rule != COMMON:
        raise ValueError('Unknown calibration rule.')
    import numpy as np
    from parallel_truth_fingerprint.lstm_service.offline_training.academic_metrics import _threshold_at_or_below_fpr
    threshold, observed = _threshold_at_or_below_fpr(np.asarray(values, dtype=float), .01)
    if not math.isfinite(threshold):
        raise ValueError('Finite calibration threshold required.')
    return {'threshold': threshold, 'count': len(values), 'method': COMMON,
            'target_fpr': .01, 'attained_normal_fpr': observed,
            'decision': 'score >= threshold', 'floor': None}


def anomalous(score, threshold, rule=LEGACY):
    # Convert before comparison: NumPy float32 would round nextafter(0,+inf) to zero.
    score, threshold = float(score), float(threshold)
    if not math.isfinite(score) or not math.isfinite(threshold):
        raise ValueError('Nonfinite score or threshold.')
    if rule == COMMON:
        return score >= threshold
    if rule == LEGACY:
        return score > threshold
    raise ValueError('Unknown calibration rule.')
