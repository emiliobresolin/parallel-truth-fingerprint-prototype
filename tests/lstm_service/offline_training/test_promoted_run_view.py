"""Story 8.4: dashboard-facing view of the promoted run."""

from __future__ import annotations

import os
import unittest
from pathlib import Path

os.environ.setdefault("KERAS_BACKEND", "torch")

from parallel_truth_fingerprint.lstm_service.offline_training.registry.promotion import (  # noqa: E402
    promote_training_run,
)
from parallel_truth_fingerprint.lstm_service.offline_training.training.runner_adfa_ld import (  # noqa: E402
    run_first_adfa_ld_training,
)
from parallel_truth_fingerprint.lstm_service.promoted_run_view import (  # noqa: E402
    build_promoted_run_dashboard_view,
)
from parallel_truth_fingerprint.persistence import (  # noqa: E402
    MinioArtifactStore,
    MinioStoreConfig,
)
from tests.persistence.test_service import FakeMinioClient  # noqa: E402


ADFA_FIXTURE = (
    Path(__file__).resolve().parent / "fixtures" / "adfa_ld_fixture"
)


def _fresh_store() -> MinioArtifactStore:
    return MinioArtifactStore(
        MinioStoreConfig(
            endpoint="localhost:0",
            access_key="x",
            secret_key="y",
            bucket="fingerprint-training-history",
            secure=False,
        ),
        client=FakeMinioClient(),
    )


class DashboardViewTests(unittest.TestCase):
    def test_none_branch_when_nothing_promoted(self) -> None:
        store = _fresh_store()
        view = build_promoted_run_dashboard_view(store)
        self.assertEqual(view["status"], "none")
        self.assertIsNone(view["run_id"])
        self.assertIsNone(view["macro_f1"])

    def test_promoted_branch_surfaces_champion_metrics(self) -> None:
        store = _fresh_store()
        record, _ = run_first_adfa_ld_training(
            adfa_ld_root=ADFA_FIXTURE,
            artifact_store=store,
            epochs=1,
            batch_size=2,
            learning_rate=1e-2,
            sequence_length=4,
            seed=42,
            extra_hyperparameters={"hidden_units": 4, "num_layers": 1},
        )
        promote_training_run(record.run_id, artifact_store=store)
        view = build_promoted_run_dashboard_view(store)
        self.assertEqual(view["status"], "promoted")
        self.assertEqual(view["run_id"], record.run_id)
        self.assertEqual(view["dataset_name"], "adfa-ld")
        self.assertEqual(view["model_name"], "lstm-classifier")
        self.assertIsNotNone(view["promoted_at"])
        self.assertEqual(view["macro_f1"], record.metrics["macro_f1"])
        self.assertEqual(view["accuracy"], record.metrics["accuracy"])
        self.assertEqual(view["parameter_count"], record.parameter_count)


if __name__ == "__main__":
    unittest.main()
