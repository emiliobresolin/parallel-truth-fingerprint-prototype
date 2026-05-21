"""Story 7.13: cross-benchmark comparative report tests."""

from __future__ import annotations

import os
import unittest
from pathlib import Path

os.environ.setdefault("KERAS_BACKEND", "torch")

from parallel_truth_fingerprint.lstm_service.offline_training.training.cross_benchmark_report import (  # noqa: E402
    build_cross_benchmark_report,
)
from parallel_truth_fingerprint.lstm_service.offline_training.training.runner_adfa_ld import (  # noqa: E402
    run_first_adfa_ld_training,
)
from parallel_truth_fingerprint.lstm_service.offline_training.training.runner_lid_ds_2021 import (  # noqa: E402
    run_first_lid_ds_2021_training,
)
from parallel_truth_fingerprint.persistence import (  # noqa: E402
    MinioArtifactStore,
    MinioStoreConfig,
)
from tests.persistence.test_service import FakeMinioClient  # noqa: E402


ADFA_FIXTURE = (
    Path(__file__).resolve().parent / "fixtures" / "adfa_ld_fixture"
)
LID_FIXTURE = (
    Path(__file__).resolve().parent / "fixtures" / "lid_ds_2021_fixture"
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


def _seed_two_benchmarks(store: MinioArtifactStore) -> tuple[str, str]:
    """Run one training on each benchmark; return both run ids."""
    record_adfa, _ = run_first_adfa_ld_training(
        adfa_ld_root=ADFA_FIXTURE,
        artifact_store=store,
        epochs=1,
        batch_size=2,
        learning_rate=1e-2,
        sequence_length=4,
        seed=42,
        extra_hyperparameters={"hidden_units": 4, "num_layers": 1},
    )
    record_lid, _ = run_first_lid_ds_2021_training(
        lid_ds_root=LID_FIXTURE,
        artifact_store=store,
        epochs=1,
        batch_size=2,
        learning_rate=1e-2,
        sequence_length=4,
        seed=42,
        extra_hyperparameters={"hidden_units": 4, "num_layers": 1},
    )
    return record_adfa.run_id, record_lid.run_id


class CrossBenchmarkReportTests(unittest.TestCase):
    def test_report_contains_champion_table_with_both_benchmarks(self) -> None:
        store = _fresh_store()
        adfa_run_id, lid_run_id = _seed_two_benchmarks(store)
        report = build_cross_benchmark_report(
            artifact_store=store,
            benchmarks=("adfa-ld", "lid-ds-2021"),
        )
        # Section 1 - champion table.
        self.assertIn("Champion runs per benchmark", report)
        self.assertIn("adfa-ld", report)
        self.assertIn("lid-ds-2021", report)
        self.assertIn(adfa_run_id, report)
        self.assertIn(lid_run_id, report)
        # Section 2 - per-class table headers.
        self.assertIn("Per-class metrics", report)
        self.assertIn("| class | precision | recall | f1", report)
        # Section 3 - provenance footer with the real origin/year strings
        # (not the env-var-missing fallback message). This proves the
        # provenance was captured at training time, not at report time.
        self.assertIn("Dataset provenance", report)
        self.assertIn("origin: ADFA-LD", report)
        self.assertIn("origin: LID-DS 2021", report)
        self.assertIn("year: 2013", report)
        self.assertIn("year: 2021", report)
        self.assertNotIn("provenance unavailable", report)

    def test_unknown_benchmark_does_not_raise(self) -> None:
        store = _fresh_store()
        _seed_two_benchmarks(store)
        report = build_cross_benchmark_report(
            artifact_store=store,
            benchmarks=("adfa-ld", "lid-ds-2021", "missing-benchmark"),
        )
        self.assertIn("_No runs persisted for `missing-benchmark` yet._", report)

    def test_champion_is_the_higher_macro_f1_run(self) -> None:
        store = _fresh_store()
        # Two ADFA runs with the same model and different seeds: the one
        # with the higher macro_f1 must be the champion.
        first, _ = run_first_adfa_ld_training(
            adfa_ld_root=ADFA_FIXTURE,
            artifact_store=store,
            epochs=1,
            batch_size=2,
            learning_rate=1e-2,
            sequence_length=4,
            seed=42,
            extra_hyperparameters={"hidden_units": 4, "num_layers": 1},
        )
        second, _ = run_first_adfa_ld_training(
            adfa_ld_root=ADFA_FIXTURE,
            artifact_store=store,
            epochs=1,
            batch_size=2,
            learning_rate=1e-2,
            sequence_length=4,
            seed=7,
            extra_hyperparameters={"hidden_units": 4, "num_layers": 1},
        )
        winner = max(
            (first, second), key=lambda r: r.metrics.get("macro_f1", 0.0)
        )
        report = build_cross_benchmark_report(
            artifact_store=store, benchmarks=("adfa-ld",)
        )
        # The champion table row for adfa-ld must mention the winning
        # run_id.
        self.assertIn(winner.run_id, report)


if __name__ == "__main__":
    unittest.main()
