"""Training repetitions retain shared experimental support."""
import copy
import sys
from pathlib import Path
import pytest

sys.path.insert(0, str(Path(__file__).resolve().parents[2] / 'scripts'))
from evaluate_hart_multiseed import SEEDS, PROFILES, VARIANTS, aggregate
from evaluate_hart_totalizer import evaluate_collection


def records():
    return {seed: {'profiles': {profile: {variant: {'metrics': {
        'lstm': {'normal': {'count': 140, 'rate_role': 'false_positive_rate', 'rate': index / 100}},
        'direct_gap': {'normal': {'count': 140, 'rate_role': 'false_positive_rate', 'rate': 0.0}},
    }} for variant in VARIANTS} for profile in PROFILES}} for index, seed in enumerate(SEEDS)}


def test_training_variation_preserves_shared_support():
    result = aggregate(records())['modulated']['hart_totalizer']['lstm']['normal']
    assert result['training_fits'] == 5
    assert result['evaluations_per_fit'] == 140
    assert result['mean_rate'] == pytest.approx(.02)
    assert result['sample_sd_rate'] > 0


@pytest.mark.parametrize('change', ['missing_seed', 'support', 'control', 'condition'])
def test_incompatible_repetitions_are_rejected(change):
    data = copy.deepcopy(records())
    if change == 'missing_seed':
        del data[101]
    else:
        metrics = data[211]['profiles']['modulated']['hart_totalizer']['metrics']
        if change == 'support':
            metrics['lstm']['normal']['count'] = 139
        elif change == 'control':
            metrics['direct_gap']['normal']['rate'] = .5
        else:
            metrics['lstm']['attack'] = metrics['lstm'].pop('normal')
    with pytest.raises(ValueError):
        aggregate(data)


def test_invalid_seed_fails_before_loading_data_or_training():
    with pytest.raises(ValueError, match='Unsupported'):
        evaluate_collection('missing-source', 'unused-output', seed=999)
    with pytest.raises(ValueError, match='versioned'):
        evaluate_collection('missing-source', 'unused-output', seed=211)
