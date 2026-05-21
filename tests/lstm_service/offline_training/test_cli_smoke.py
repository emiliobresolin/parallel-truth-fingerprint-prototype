"""Story 7.1 smoke test: CLI end-to-end against the dummy benchmark/model."""

from __future__ import annotations

import unittest

from parallel_truth_fingerprint.lstm_service.offline_training.cli import (
    main as cli_main,
)
from parallel_truth_fingerprint.lstm_service.offline_training.training.run import (
    TrainingRunRecord,
    execute_training_run,
)


class CliSmokeTests(unittest.TestCase):
    """End-to-end smoke for the offline training CLI."""

    def test_cli_dummy_run_exits_zero_and_returns_record(self) -> None:
        # AC2 + AC3: CLI invoked with --benchmark dummy --model dummy must
        # succeed and produce an in-memory TrainingRunRecord.
        record = cli_main(
            [
                "--benchmark",
                "dummy",
                "--model",
                "dummy",
                "--epochs",
                "2",
                "--batch-size",
                "4",
                "--learning-rate",
                "0.01",
                "--sequence-length",
                "5",
                "--seed",
                "123",
            ]
        )
        self.assertIsInstance(record, TrainingRunRecord)
        self.assertEqual(record.dataset_name, "dummy")
        self.assertEqual(record.model_name, "dummy")
        self.assertEqual(record.seed, 123)
        self.assertEqual(record.epochs_planned, 2)
        self.assertEqual(record.epochs_executed, 2)
        self.assertTrue(record.run_id)
        self.assertIn("learning_rate", record.hyperparameters)
        self.assertIn("batch_size", record.hyperparameters)
        # Placeholder metrics keys must already exist so downstream stories
        # can extend them without breaking the schema.
        self.assertIn("accuracy", record.metrics)
        self.assertIn("macro_f1", record.metrics)

    def test_execute_training_run_directly_is_deterministic(self) -> None:
        # AC3 + AC6: same seed/inputs => same record content (except run_id)
        record_a = execute_training_run(
            benchmark="dummy",
            model="dummy",
            epochs=1,
            batch_size=2,
            learning_rate=0.01,
            sequence_length=3,
            seed=7,
        )
        record_b = execute_training_run(
            benchmark="dummy",
            model="dummy",
            epochs=1,
            batch_size=2,
            learning_rate=0.01,
            sequence_length=3,
            seed=7,
        )
        self.assertEqual(record_a.metrics, record_b.metrics)
        self.assertEqual(record_a.hyperparameters, record_b.hyperparameters)
        self.assertEqual(record_a.epochs_executed, record_b.epochs_executed)

    def test_cli_rejects_unknown_benchmark(self) -> None:
        # The CLI must not silently swallow a typo.
        with self.assertRaises(ValueError):
            cli_main(
                [
                    "--benchmark",
                    "does-not-exist",
                    "--model",
                    "dummy",
                    "--epochs",
                    "1",
                    "--batch-size",
                    "2",
                    "--learning-rate",
                    "0.01",
                    "--sequence-length",
                    "3",
                    "--seed",
                    "0",
                ]
            )


class ScaffoldIsolationTests(unittest.TestCase):
    """AC4: the new module must not import any deprecated runtime code.

    The legacy lstm_service/__init__.py re-exports the deprecated modules
    (trainer/lifecycle/inference), so we cannot use sys.modules as the
    probe (importing any subpackage triggers the parent __init__). We
    instead do static-text inspection of every source file that lives
    under offline_training/* and reject any import naming the deprecated
    runtime modules from inside our new code.
    """

    DEPRECATED_RUNTIME_REFERENCES = (
        "parallel_truth_fingerprint.lstm_service.lifecycle",
        "parallel_truth_fingerprint.lstm_service.trainer",
        "parallel_truth_fingerprint.lstm_service.inference",
        "scripts.run_local_demo",
        "from parallel_truth_fingerprint.lstm_service.lifecycle",
        "from parallel_truth_fingerprint.lstm_service.trainer",
        "from parallel_truth_fingerprint.lstm_service.inference",
    )

    def test_no_offline_training_source_file_references_deprecated_runtime(
        self,
    ) -> None:
        import parallel_truth_fingerprint.lstm_service.offline_training as pkg
        from pathlib import Path

        root = Path(pkg.__file__).parent
        offences: list[tuple[str, str]] = []
        for source_path in root.rglob("*.py"):
            text = source_path.read_text(encoding="utf-8")
            for needle in self.DEPRECATED_RUNTIME_REFERENCES:
                if needle in text:
                    offences.append((str(source_path), needle))
        self.assertEqual(
            offences,
            [],
            (
                "Offline training source files must not reference deprecated "
                f"runtime modules. Offences: {offences}"
            ),
        )

    def test_train_lstm_offline_script_does_not_reference_deprecated_runtime(
        self,
    ) -> None:
        from pathlib import Path

        script_path = (
            Path(__file__).resolve().parents[3]
            / "scripts"
            / "train_lstm_offline.py"
        )
        self.assertTrue(
            script_path.exists(), f"Expected wrapper script at {script_path}"
        )
        text = script_path.read_text(encoding="utf-8")
        for needle in self.DEPRECATED_RUNTIME_REFERENCES:
            self.assertNotIn(
                needle,
                text,
                f"scripts/train_lstm_offline.py must not reference {needle}",
            )


if __name__ == "__main__":
    unittest.main()
