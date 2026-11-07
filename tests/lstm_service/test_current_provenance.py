from copy import deepcopy
from types import SimpleNamespace

from parallel_truth_fingerprint.lstm_service.dataset_builder import (
    build_normal_training_windows, evaluate_training_eligibility, evaluate_inference_eligibility,
)
from tests.lstm_service.test_dataset_builder import build_persisted_artifact


def test_retained_legacy_history_cannot_enter_new_training_windows():
    records = [build_persisted_artifact(index=i) for i in range(1, 5)]
    for record in records[:2]:
        record['validated_state'].pop('measurement_domain')
        record['consensus_context'].pop('schema_version')
        assert not evaluate_training_eligibility(record)[0]
        assert not evaluate_inference_eligibility(record)[0]
    class Store:
        config = SimpleNamespace(bucket='current-test')
        def list_json_objects(self, prefix):
            return [r['artifact_key'] for r in records]
        def load_json(self, key):
            return next(r for r in records if r['artifact_key'] == key)
    windows, manifest = build_normal_training_windows(artifact_store=Store(), sequence_length=2)
    assert len(windows) == 1
    assert manifest.selected_artifact_keys == tuple(r['artifact_key'] for r in records[2:])
    assert len(manifest.skipped_artifacts) == 2


def test_engineering_metadata_is_ignored_but_disagreeing_validated_current_is_blocked():
    record = build_persisted_artifact(index=1)
    changed = deepcopy(record)
    changed['validated_state']['structured_payload_snapshot']['payloads_by_sensor']['pressure']['process_data']['pv']['value'] = 99999
    assert evaluate_training_eligibility(changed)[0]
    changed['validated_state']['sensor_values']['pressure'] += .001
    assert not evaluate_training_eligibility(changed)[0]
