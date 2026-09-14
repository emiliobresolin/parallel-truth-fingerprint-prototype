"""Story 7.10: LID-DS 2021 benchmark adapter tests."""

from __future__ import annotations

import os
import unittest
from collections import Counter
from pathlib import Path
import tempfile
import zipfile

from parallel_truth_fingerprint.lstm_service.offline_training.benchmarks import (
    load_benchmark,
)
from parallel_truth_fingerprint.lstm_service.offline_training.benchmarks.lid_ds_2021 import (
    LidDs2021Benchmark,
)


FIXTURE_PATH = (
    Path(__file__).resolve().parent / "fixtures" / "lid_ds_2021_fixture"
)


class LidDsConfigurationTests(unittest.TestCase):
    def test_missing_path_raises_with_actionable_message(self) -> None:
        previous = os.environ.pop("LID_DS_2021_PATH", None)
        try:
            adapter = LidDs2021Benchmark(root_path=None)
            with self.assertRaises(RuntimeError) as ctx:
                adapter.load(sequence_length=5, seed=0)
            self.assertIn("LID_DS_2021_PATH", str(ctx.exception))
        finally:
            if previous is not None:
                os.environ["LID_DS_2021_PATH"] = previous

    def test_env_var_is_honored_when_constructor_path_is_none(self) -> None:
        previous = os.environ.get("LID_DS_2021_PATH")
        os.environ["LID_DS_2021_PATH"] = str(FIXTURE_PATH)
        try:
            adapter = LidDs2021Benchmark(root_path=None)
            data = adapter.load(sequence_length=4, seed=0)
            self.assertEqual(data.name, "lid-ds-2021")
        finally:
            if previous is None:
                os.environ.pop("LID_DS_2021_PATH", None)
            else:
                os.environ["LID_DS_2021_PATH"] = previous


class LidDsFixtureLoadTests(unittest.TestCase):
    def setUp(self) -> None:
        self.adapter = LidDs2021Benchmark(root_path=FIXTURE_PATH)

    def test_label_space_is_normal_plus_per_scenario(self) -> None:
        data = self.adapter.load(sequence_length=5, seed=0)
        # Scenarios alphabetically: cve_2017_7529, cve_2019_5736.
        self.assertEqual(
            data.label_names,
            ("Normal", "cve_2017_7529-attack", "cve_2019_5736-attack"),
        )

    def test_per_class_counts_match_fixture(self) -> None:
        data = self.adapter.load(sequence_length=5, seed=0)
        counter = Counter(data.labels)
        # 2 normal traces per scenario = 4 normal samples.
        self.assertEqual(counter[0], 4)
        # 2 attack traces per scenario class.
        self.assertEqual(counter[1], 2)
        self.assertEqual(counter[2], 2)

    def test_feature_count_is_one_and_window_length_respected(self) -> None:
        data = self.adapter.load(sequence_length=5, seed=0)
        self.assertEqual(data.feature_count, 1)
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

    def test_provenance_lists_scenarios(self) -> None:
        data = self.adapter.load(sequence_length=5, seed=0)
        self.assertEqual(data.provenance["origin"], "LID-DS 2021")
        self.assertEqual(data.provenance["year"], 2021)
        self.assertEqual(data.provenance["feature_count"], 1)
        self.assertEqual(
            list(data.provenance["scenarios"]),
            ["cve_2017_7529", "cve_2019_5736"],
        )
        per_class = data.provenance["per_class_counts"]
        self.assertEqual(per_class["Normal"], 4)
        self.assertEqual(per_class["cve_2017_7529-attack"], 2)
        self.assertEqual(per_class["cve_2019_5736-attack"], 2)


class LidDsRegistryTests(unittest.TestCase):
    def test_registry_returns_lid_ds_2021(self) -> None:
        previous = os.environ.get("LID_DS_2021_PATH")
        os.environ["LID_DS_2021_PATH"] = str(FIXTURE_PATH)
        try:
            data = load_benchmark("lid-ds-2021", sequence_length=4, seed=0)
            self.assertEqual(data.name, "lid-ds-2021")
            self.assertEqual(len(data.label_names), 3)
        finally:
            if previous is None:
                os.environ.pop("LID_DS_2021_PATH", None)
            else:
                os.environ["LID_DS_2021_PATH"] = previous


class LidDsOfficialArchiveTests(unittest.TestCase):
    def test_official_archives_are_read_in_place_and_use_syscall_field(self) -> None:
        with tempfile.TemporaryDirectory() as directory:
            root = Path(directory) / "LID-DS-2021-real"
            scenario = root / "CVE-2020-example"
            for role, metadata_role in (
                ("training", "normal"),
                ("validation", "normal"),
                ("test/normal", "normal"),
                ("test/normal_and_attack", "attack"),
            ):
                archive = scenario / role / "recording.zip"
                archive.parent.mkdir(parents=True, exist_ok=True)
                with zipfile.ZipFile(archive, "w") as bundle:
                    bundle.writestr("recording.json", '{"container": [{"role": "' + metadata_role + '"}]}')
                    bundle.writestr("recording.sc", "1631064318497503973 0 1 app 1 read >\n1631064318497514940 0 1 app 1 write <\n")
            data = LidDs2021Benchmark(root_path=root).load(sequence_length=3, seed=0)
        self.assertEqual(data.provenance["source_layout"], "official-zip-recording")
        self.assertEqual(data.provenance["max_archives_per_scenario_partition"], 0)
        self.assertEqual(data.provenance["sampling_scope"], "complete official recording set")
        self.assertEqual(data.provenance["partition_counts"], {"training": 1, "validation": 1, "test-normal": 1, "test-normal-and-attack": 1})
        self.assertEqual(data.label_names, ("Normal", "CVE-2020-example-attack"))
        self.assertEqual(Counter(data.labels), Counter({0: 3, 1: 1}))
        self.assertLess(data.sequences[0][0][0], 1.0)


if __name__ == "__main__":
    unittest.main()
