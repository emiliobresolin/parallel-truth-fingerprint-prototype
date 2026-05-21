"""Story 7.6: ADFA-LD benchmark adapter tests using an embedded fixture."""

from __future__ import annotations

import os
import unittest
from collections import Counter
from pathlib import Path

from parallel_truth_fingerprint.lstm_service.offline_training.benchmarks import (
    load_benchmark,
)
from parallel_truth_fingerprint.lstm_service.offline_training.benchmarks.adfa_ld import (
    ADFA_LD_LABEL_NAMES,
    AdfaLdBenchmark,
)


FIXTURE_PATH = (
    Path(__file__).resolve().parent / "fixtures" / "adfa_ld_fixture"
)


class AdfaLdConfigurationTests(unittest.TestCase):
    def test_missing_path_raises_with_actionable_message(self) -> None:
        # Clear ADFA_LD_PATH if set, to exercise the failure mode.
        previous = os.environ.pop("ADFA_LD_PATH", None)
        try:
            adapter = AdfaLdBenchmark(root_path=None)
            with self.assertRaises(RuntimeError) as ctx:
                adapter.load(sequence_length=5, seed=0)
            self.assertIn("ADFA_LD_PATH", str(ctx.exception))
        finally:
            if previous is not None:
                os.environ["ADFA_LD_PATH"] = previous

    def test_env_var_is_honored_when_constructor_path_is_none(self) -> None:
        previous = os.environ.get("ADFA_LD_PATH")
        os.environ["ADFA_LD_PATH"] = str(FIXTURE_PATH)
        try:
            adapter = AdfaLdBenchmark(root_path=None)
            data = adapter.load(sequence_length=4, seed=0)
            self.assertEqual(data.name, "adfa-ld")
        finally:
            if previous is None:
                os.environ.pop("ADFA_LD_PATH", None)
            else:
                os.environ["ADFA_LD_PATH"] = previous


class AdfaLdFixtureLoadTests(unittest.TestCase):
    def setUp(self) -> None:
        self.adapter = AdfaLdBenchmark(root_path=FIXTURE_PATH)

    def test_load_returns_all_six_classes(self) -> None:
        data = self.adapter.load(sequence_length=5, seed=0)
        self.assertEqual(data.label_names, ADFA_LD_LABEL_NAMES)
        present_classes = sorted(set(data.labels))
        self.assertEqual(present_classes, [0, 1, 2, 3, 4, 5])

    def test_per_class_sample_counts_match_fixture(self) -> None:
        data = self.adapter.load(sequence_length=5, seed=0)
        counter = Counter(data.labels)
        # 2 normal traces from Training + 2 from Validation = 4 normal samples.
        self.assertEqual(counter[0], 4)
        # Each attack subdir holds 2 traces -> 2 samples per attack class.
        for attack_id in (1, 2, 3, 4, 5):
            self.assertEqual(counter[attack_id], 2)

    def test_feature_count_is_one_and_sequence_length_respected(self) -> None:
        data = self.adapter.load(sequence_length=5, seed=0)
        self.assertEqual(data.feature_count, 1)
        self.assertEqual(data.sequence_length, 5)
        for sequence in data.sequences:
            self.assertEqual(len(sequence), 5)
            for timestep in sequence:
                self.assertEqual(len(timestep), 1)

    def test_features_are_scaled_to_zero_one(self) -> None:
        data = self.adapter.load(sequence_length=5, seed=0)
        for sequence in data.sequences:
            for timestep in sequence:
                value = timestep[0]
                self.assertGreaterEqual(value, 0.0)
                self.assertLessEqual(value, 1.0)

    def test_short_traces_are_right_padded_with_zero(self) -> None:
        # The fixture trace `UAD-0002.txt` has 15 syscalls. Request a window
        # length larger than that and expect right-padded zeros.
        data = self.adapter.load(sequence_length=20, seed=0)
        # Find the Adduser samples (label=1) and check they have trailing 0s.
        adduser_sequences = [
            seq
            for seq, label in zip(data.sequences, data.labels)
            if label == 1
        ]
        # At least one Adduser sample must end with a 0.0 padding entry.
        self.assertTrue(
            any(seq[-1] == (0.0,) for seq in adduser_sequences),
            "Expected at least one padded Adduser sample to end with 0.0.",
        )

    def test_provenance_records_origin_and_counts(self) -> None:
        data = self.adapter.load(sequence_length=5, seed=0)
        self.assertEqual(data.provenance["origin"], "ADFA-LD")
        self.assertEqual(data.provenance["year"], 2013)
        self.assertEqual(data.provenance["feature_count"], 1)
        per_class = data.provenance["per_class_counts"]
        self.assertEqual(per_class["Normal"], 4)
        self.assertEqual(per_class["Adduser"], 2)
        self.assertGreater(int(data.provenance["max_syscall_id"]), 0)

    def test_load_is_deterministic_for_a_given_seed(self) -> None:
        data_a = self.adapter.load(sequence_length=5, seed=11)
        data_b = self.adapter.load(sequence_length=5, seed=11)
        self.assertEqual(data_a.sequences, data_b.sequences)
        self.assertEqual(data_a.labels, data_b.labels)


class AdfaLdNestedLayoutTests(unittest.TestCase):
    """Cover the official UNSW 2013 layout: Attack_Data_Master/<Class>_<N>/.

    The real ADFA-LD archive groups attack traces under per-run
    subdirectories like `Adduser_1/`, `Adduser_2/`, etc. The embedded
    `adfa_ld_nested_fixture` mirrors that layout with one trace per
    attack subdirectory and includes a `Meterpreter_1` folder that must
    collapse into the Java-Meterpreter class.
    """

    NESTED_FIXTURE = (
        Path(__file__).resolve().parent
        / "fixtures"
        / "adfa_ld_nested_fixture"
    )

    def test_nested_layout_loads_all_classes_and_collapses_meterpreter(
        self,
    ) -> None:
        adapter = AdfaLdBenchmark(root_path=self.NESTED_FIXTURE)
        data = adapter.load(sequence_length=6, seed=0)
        self.assertEqual(data.label_names, ADFA_LD_LABEL_NAMES)
        counter = Counter(data.labels)
        # 1 trace Training + 1 Validation = 2 normal samples.
        self.assertEqual(counter[0], 2)
        # Adduser: 2 nested subdirs x 1 trace = 2 samples.
        self.assertEqual(counter[1], 2)
        # Hydra_FTP: 1 nested subdir x 1 trace = 1 sample.
        self.assertEqual(counter[2], 1)
        # Hydra_SSH: 1.
        self.assertEqual(counter[3], 1)
        # Java_Meterpreter + Meterpreter collapsed = 2 samples in class 4.
        self.assertEqual(counter[4], 2)
        # Web_Shell: 1.
        self.assertEqual(counter[5], 1)


class AdfaLdRegistryTests(unittest.TestCase):
    def test_registry_returns_adfa_ld(self) -> None:
        previous = os.environ.get("ADFA_LD_PATH")
        os.environ["ADFA_LD_PATH"] = str(FIXTURE_PATH)
        try:
            data = load_benchmark("adfa-ld", sequence_length=4, seed=0)
            self.assertEqual(data.name, "adfa-ld")
            self.assertEqual(len(data.label_names), 6)
        finally:
            if previous is None:
                os.environ.pop("ADFA_LD_PATH", None)
            else:
                os.environ["ADFA_LD_PATH"] = previous


if __name__ == "__main__":
    unittest.main()
