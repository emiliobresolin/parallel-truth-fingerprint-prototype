import math
import numpy as np
import pytest
import json
from pathlib import Path
import sys

from parallel_truth_fingerprint.evidence.replay_calibration import calibrate, anomalous, COMMON
from parallel_truth_fingerprint.evidence.replay_evaluation import fixed_threshold


def test_small_sample_and_zero_ties_do_not_admit_calibration_alerts():
    for scores in ([0.] * 59, list(range(59)), [1.] * 59):
        result = calibrate(scores, COMMON)
        assert result['threshold'] == math.nextafter(max(scores), math.inf)
        assert not any(anomalous(s, result['threshold'], COMMON) for s in scores)
    assert not anomalous(np.float32(0), calibrate([0.] * 59, COMMON)['threshold'], COMMON)


def test_public_rule_equivalence_and_attainable_fpr():
    from parallel_truth_fingerprint.lstm_service.offline_training.academic_metrics import _threshold_at_or_below_fpr
    scores = np.arange(200, dtype=float)
    expected, fpr = _threshold_at_or_below_fpr(scores, .01)
    result = calibrate(scores, COMMON)
    assert result['threshold'] == expected
    assert sum(anomalous(s, expected, COMMON) for s in scores) == 2
    assert result['attained_normal_fpr'] == fpr == .01
    assert anomalous(expected, expected, COMMON)


def test_legacy_and_invalid_inputs():
    assert calibrate([.1,.2,.3]) == fixed_threshold([.1,.2,.3])
    assert not anomalous(1., 1.)
    for scores in ([], [float('nan')], [float('inf')]):
        with pytest.raises(ValueError):
            calibrate(scores, COMMON)


@pytest.mark.parametrize('corruption', ['nonboundary', 'comparator', 'threshold', 'calibration_metadata'])
def test_verifier_rejects_inconsistent_reported_results(tmp_path, corruption):
    sys.path.insert(0, str(Path(__file__).resolve().parents[2]/'scripts'))
    from evaluate_contextual_error import verify_output, source_hashes
    from parallel_truth_fingerprint.evidence.contextual_replay import metrics
    def save(path, value):
        path.write_text(json.dumps(value), encoding='utf-8')
    source, output = tmp_path/'source', tmp_path/'evaluation'
    (source/'unmodulated').mkdir(parents=True)
    (output/'unmodulated').mkdir(parents=True)
    rows = [{'round_id': 'r1', 'block': 0, 'offset': 1, 'condition': 'normal_stable',
             'boundary': False, 'global_mse_score': 0., 'global_mse_anomalous': False,
             'comparator_anomalous': False}]
    save(source/'unmodulated/scores.json', rows)
    save(output/'source-hashes.json', source_hashes(source))
    save(output/'protocol.json', {'contextual_source': str(source), 'calibration_rule': COMMON})
    calibration = {'global_mse': dict(calibrate([0.]*59, COMMON), scores=[0.]*59)}
    profile = {'thresholds': {'global_mse': calibration['global_mse']['threshold']},
               'metrics': {m: metrics(rows,m+'_anomalous') for m in ('global_mse','comparator')},
               'metrics_without_boundary': {m: metrics(rows,m+'_anomalous',True) for m in ('global_mse','comparator')}}
    save(output/'unmodulated/calibration.json', calibration)
    save(output/'unmodulated/scores.json', rows)
    summary = {'status': 'completed', 'profiles': {'unmodulated': profile}}
    save(output/'summary.json', summary)
    save(output/'manifest.json', source_hashes(output))
    verify_output(output)
    if corruption == 'nonboundary':
        profile['metrics_without_boundary']['global_mse']['normal_stable']['alerts'] = 1
    elif corruption == 'comparator':
        rows[0]['comparator_anomalous'] = True
        save(output/'unmodulated/scores.json', rows)
    elif corruption == 'threshold':
        profile['thresholds']['global_mse'] = 10.
    else:
        calibration['global_mse']['target_fpr'] = .1
        save(output/'unmodulated/calibration.json', calibration)
    save(output/'summary.json', summary)
    (output/'manifest.json').unlink()
    save(output/'manifest.json', source_hashes(output))
    with pytest.raises(ValueError):
        verify_output(output)
