"""Unit tests for leakage-safe academic dataset preparation."""

from __future__ import annotations

import json
from pathlib import Path
import tempfile
import unittest
import zipfile

import numpy as np

from parallel_truth_fingerprint.lstm_service.offline_training.academic_protocol import (
    AcademicDataset,
    AcademicUnit,
    AcademicWindow,
    PAD_TOKEN,
    UNKNOWN_TOKEN,
    _parse_lid_consumed_archive,
    _parse_hai_timestamp,
    _stable_cap,
    _stable_unit_slice,
    PreparedPartition,
    aggregate_window_scores,
    audit_group_leakage,
    audit_window_parentage,
    fit_preprocessing,
    load_academic_dataset,
    prepare_dataset_arrays,
    support_summary,
    validate_academic_support,
    window_dataset,
)


def _unit(
    unit_id: str,
    partition: str,
    values: tuple[tuple[float | str, ...], ...],
    *,
    label: int = 0,
    class_name: str = "Normal",
    group_id: str | None = None,
    events: tuple[str, ...] = (),
) -> AcademicUnit:
    return AcademicUnit(
        unit_id=unit_id,
        group_id=group_id or f"group:{unit_id}",
        native_partition=partition,
        assigned_partition=partition,
        label=label,
        class_name=class_name,
        values=values,
        source_path=f"{unit_id}.source",
        source_sha256=f"sha256:{unit_id}",
        event_ids=events,
    )


def _dataset(
    units: tuple[AcademicUnit, ...],
    *,
    modality: str = "categorical-syscall",
    feature_names: tuple[str, ...] = ("feature",),
) -> AcademicDataset:
    return AcademicDataset(
        name="fixture",
        modality=modality,
        protocol="fixture-native-units-v1",
        units=units,
        feature_names=feature_names,
        label_names=("Normal", "Attack"),
        source_manifest={"fixture": True},
        phase="pilot",
    )


class DetectorInputIdentityTests(unittest.TestCase):
    def test_detector_input_identity_ignores_sampling_offset(self) -> None:
        values = (("open",), ("read",), ("close",))
        earlier = AcademicUnit(
            unit_id="earlier",
            group_id="sha256:full-stream-earlier",
            native_partition="training",
            assigned_partition="train",
            label=0,
            class_name="Normal",
            values=(),
            source_path="earlier.zip",
            source_sha256="sha256:earlier",
            sampled_sequences=((0, values),),
        )
        later = AcademicUnit(
            unit_id="later",
            group_id="sha256:full-stream-later",
            native_partition="validation",
            assigned_partition="validation",
            label=0,
            class_name="Normal",
            values=(),
            source_path="later.zip",
            source_sha256="sha256:later",
            sampled_sequences=((128, values),),
        )

        self.assertNotEqual(earlier.group_id, later.group_id)
        self.assertNotEqual(
            earlier.detector_input_identity,
            later.detector_input_identity,
        )
        self.assertEqual(
            earlier.detector_input_content_identity,
            later.detector_input_content_identity,
        )


class WindowLineageTests(unittest.TestCase):
    def test_windows_are_created_inside_parent_partitions_and_include_tail(self) -> None:
        train = _unit("train-unit", "train", tuple((str(i),) for i in range(10)))
        validation = _unit("validation-unit", "validation", (("v",),))
        test = _unit("test-unit", "test", (("t",),), label=1, class_name="Attack")
        dataset = _dataset((train, validation, test))

        windowed = window_dataset(
            dataset,
            sequence_length=4,
            stride=3,
            max_windows_per_unit=2,
            aggregation="max",
        )

        self.assertEqual([window.start for window in windowed.partitions["train"]], [0, 6])
        self.assertEqual({window.unit_id for window in windowed.partitions["train"]}, {"train-unit"})
        self.assertEqual(windowed.partitions["validation"][0].values, (("v",), (PAD_TOKEN,), (PAD_TOKEN,), (PAD_TOKEN,)))
        self.assertEqual(windowed.partitions["test"][0].label, 1)
        self.assertTrue(audit_window_parentage(dataset, windowed.partitions)["passed"])

    def test_window_parameters_are_validated(self) -> None:
        dataset = _dataset((_unit("train", "train", (("a",),)),))
        cases = (
            ({"sequence_length": 0, "stride": 1, "max_windows_per_unit": 1, "aggregation": "max"}, "positive"),
            ({"sequence_length": 1, "stride": 1, "max_windows_per_unit": 1, "aggregation": "median"}, "aggregation"),
        )
        for keywords, message in cases:
            with self.subTest(keywords=keywords):
                with self.assertRaisesRegex(ValueError, message):
                    window_dataset(dataset, **keywords)

    def test_parentage_audit_detects_wrong_partition_and_duplicate_window_ids(self) -> None:
        dataset = _dataset((_unit("u", "train", (("a",),)),))
        window = AcademicWindow("duplicate", "u", 0, "Normal", (("a",),), (), 0)

        result = audit_window_parentage(
            dataset,
            {"train": (window,), "validation": (window,), "test": ()},
        )

        self.assertFalse(result["passed"])
        self.assertEqual(result["window_count"], 1)
        self.assertEqual(len(result["violations"]), 2)

    def test_preregistered_pilot_slices_reject_underfill_at_zero_offset(self) -> None:
        with tempfile.TemporaryDirectory() as temporary:
            root = Path(temporary)
            only_path = root / "only.trace"
            only_path.write_text("1", encoding="utf-8")
            with self.assertRaisesRegex(ValueError, "exceeds available support"):
                _stable_cap(
                    [only_path],
                    2,
                    101,
                    root,
                    offset=0,
                    require_exact=True,
                )

        only_unit = _unit("only", "train", (("1",),))
        with self.assertRaisesRegex(ValueError, "exceeds available support"):
            _stable_unit_slice(
                [only_unit],
                cap=2,
                offset=0,
                seed=101,
                stratum="pilot-train",
                require_exact=True,
            )


class PreprocessingTests(unittest.TestCase):
    def test_categorical_vocabulary_is_train_only_and_test_unknowns_use_unk(self) -> None:
        dataset = _dataset(
            (
                _unit("train-a", "train", (("open",), ("read",))),
                _unit("train-b", "train", (("read",), ("write",))),
                _unit("test", "test", (("never-seen",),)),
            )
        )
        windowed = window_dataset(
            dataset, sequence_length=3, stride=1, max_windows_per_unit=2, aggregation="max"
        )
        preprocessing = fit_preprocessing(dataset, windowed)
        prepared = prepare_dataset_arrays(dataset, windowed, preprocessing)

        self.assertEqual(preprocessing.vocabulary[:2], (PAD_TOKEN, UNKNOWN_TOKEN))
        self.assertEqual(set(preprocessing.vocabulary[2:]), {"open", "read", "write"})
        self.assertNotIn("never-seen", preprocessing.vocabulary)
        np.testing.assert_array_equal(prepared.partitions["test"].x[0, :, 0], [1, 0, 0])
        self.assertEqual(prepared.partitions["validation"].x.shape, (0, 3, 1))
        self.assertEqual(prepared.partitions["validation"].x.dtype, np.int32)

    def test_numeric_scaling_is_fitted_on_train_only_and_empty_test_shape_is_stable(self) -> None:
        dataset = _dataset(
            (
                _unit("train-a", "train", ((1.0, 10.0), (3.0, 10.0))),
                _unit("train-b", "train", ((5.0, 10.0), (7.0, 10.0))),
                _unit("validation", "validation", ((1000.0, -1000.0), (1000.0, -1000.0))),
            ),
            modality="numeric-multivariate",
            feature_names=("a", "b"),
        )
        windowed = window_dataset(
            dataset, sequence_length=2, stride=1, max_windows_per_unit=1, aggregation="mean"
        )
        preprocessing = fit_preprocessing(dataset, windowed, clip=2.0)
        prepared = prepare_dataset_arrays(dataset, windowed, preprocessing)

        np.testing.assert_allclose(preprocessing.center, [4.0, 10.0])
        np.testing.assert_allclose(preprocessing.scale, [np.sqrt(5.0), 1.0])
        np.testing.assert_array_equal(prepared.partitions["validation"].x, np.full((1, 2, 2), [[2.0, -2.0]], dtype=np.float32))
        self.assertEqual(prepared.partitions["test"].x.shape, (0, 2, 2))
        self.assertEqual(prepared.partitions["test"].x.dtype, np.float32)

    def test_fit_preprocessing_rejects_attack_contamination_and_empty_train(self) -> None:
        contaminated = _dataset(
            (_unit("attack", "train", (("exec",),), label=1, class_name="Attack"),)
        )
        contaminated_windows = window_dataset(
            contaminated, sequence_length=1, stride=1, max_windows_per_unit=1, aggregation="max"
        )
        no_train = _dataset((_unit("validation", "validation", (("read",),)),))
        no_train_windows = window_dataset(
            no_train, sequence_length=1, stride=1, max_windows_per_unit=1, aggregation="max"
        )

        with self.assertRaisesRegex(ValueError, "normal-only"):
            fit_preprocessing(contaminated, contaminated_windows)
        with self.assertRaisesRegex(ValueError, "without train windows"):
            fit_preprocessing(no_train, no_train_windows)


class UnitAggregationAndAuditTests(unittest.TestCase):
    def setUp(self) -> None:
        self.partition = PreparedPartition(
            x=np.zeros((3, 2, 1), dtype=np.float32),
            window_ids=("u:0", "u:1", "v:0"),
            unit_ids=("u", "u", "v"),
            labels=np.asarray([1, 1, 0], dtype=np.int64),
            class_names=("Attack", "Attack", "Normal"),
            event_ids=(("event-a",), ("event-b",), ()),
        )

    def test_window_scores_aggregate_to_independent_units(self) -> None:
        maximum = aggregate_window_scores(self.partition, [1.0, 3.0, 2.0], method="max")
        average = aggregate_window_scores(self.partition, [1.0, 3.0, 2.0], method="mean")
        percentile = aggregate_window_scores(self.partition, [1.0, 3.0, 2.0], method="p95")

        self.assertEqual(maximum["unit_ids"], ("u", "v"))
        np.testing.assert_array_equal(maximum["scores"], [3.0, 2.0])
        np.testing.assert_array_equal(average["scores"], [2.0, 2.0])
        np.testing.assert_allclose(percentile["scores"], [2.9, 2.0])
        np.testing.assert_array_equal(maximum["labels"], [1, 0])
        self.assertEqual(maximum["event_ids"], (("event-a", "event-b"), ()))
        self.assertEqual(maximum["window_counts"], (2, 1))

    def test_aggregation_rejects_misalignment_unknown_method_and_label_disagreement(self) -> None:
        with self.assertRaisesRegex(ValueError, "align"):
            aggregate_window_scores(self.partition, [1.0], method="max")
        with self.assertRaisesRegex(ValueError, "Unsupported"):
            aggregate_window_scores(self.partition, [1.0, 2.0, 3.0], method="median")
        inconsistent = PreparedPartition(
            x=self.partition.x,
            window_ids=self.partition.window_ids,
            unit_ids=self.partition.unit_ids,
            labels=np.asarray([1, 0, 0], dtype=np.int64),
            class_names=self.partition.class_names,
            event_ids=self.partition.event_ids,
        )
        with self.assertRaisesRegex(RuntimeError, "disagree"):
            aggregate_window_scores(inconsistent, [1.0, 2.0, 3.0], method="max")

    def test_group_audit_and_support_validation_fail_closed(self) -> None:
        dataset = _dataset(
            (
                _unit("train-a", "train", (("a",),), group_id="shared"),
                _unit("train-b", "train", (("b",),)),
                _unit("validation-a", "validation", (("a",),)),
                _unit("validation-b", "validation", (("b",),)),
                _unit("test-normal", "test", (("n",),), group_id="shared"),
                _unit("test-attack", "test", (("x",),), label=1, class_name="Attack"),
            )
        )

        leakage = audit_group_leakage(dataset)
        support = support_summary(dataset)
        validation = validate_academic_support(
            dataset, minimum_test_normal=2, minimum_test_attack=2
        )

        self.assertFalse(leakage["passed"])
        self.assertEqual(leakage["group_overlap_count"], 1)
        self.assertEqual(leakage["violations"]["groups"]["shared"], ["test", "train"])
        self.assertEqual(support["test"]["per_class"], {"Normal": 1, "Attack": 1})
        self.assertFalse(validation["passed"])
        self.assertEqual(len(validation["issues"]), 2)


class AdfaAcademicLoaderTests(unittest.TestCase):
    def test_fixture_preserves_native_units_and_is_deterministic(self) -> None:
        fixture = Path(__file__).resolve().parent / "fixtures" / "adfa_ld_fixture"
        config = {
            "kind": "adfa-ld",
            "root": str(fixture),
            "partition_seed": 23,
            "normal_validation_fraction": 0.5,
            "phase_caps": {"pilot": {}},
        }

        first = load_academic_dataset("adfa", config, project_root=Path.cwd(), phase="pilot")
        repeated = load_academic_dataset("adfa", config, project_root=Path.cwd(), phase="pilot")

        self.assertEqual(first.identity, repeated.identity)
        self.assertEqual(len(first.partition("train")), 2)
        self.assertEqual(len(first.partition("validation")), 1)
        self.assertEqual(len(first.partition("test")), 11)
        self.assertTrue(all(unit.label == 0 for unit in first.partition("train")))
        self.assertTrue(all(unit.label == 0 for unit in first.partition("validation")))
        self.assertEqual(sum(unit.label == 1 for unit in first.partition("test")), 10)
        self.assertTrue(audit_group_leakage(first)["passed"])

    def test_loader_deduplicates_equal_normal_content_and_excludes_label_conflicts(self) -> None:
        with tempfile.TemporaryDirectory() as temporary:
            root = Path(temporary)
            training = root / "Training_Data_Master"
            validation = root / "Validation_Data_Master"
            attack = root / "Attack_Data_Master" / "Adduser"
            for directory in (training, validation, attack):
                directory.mkdir(parents=True, exist_ok=True)

            (training / "train-1.txt").write_text("1 2 3\n", encoding="utf-8")
            (training / "train-2.txt").write_text("4 5 6\n", encoding="utf-8")
            (validation / "duplicate-of-train.txt").write_text("1 2 3\n", encoding="utf-8")
            (validation / "validation-1.txt").write_text("7 8 9\n", encoding="utf-8")
            (validation / "validation-2.txt").write_text("10 11 12\n", encoding="utf-8")
            (validation / "conflicting-normal.txt").write_text("90 91 92\n", encoding="utf-8")
            (attack / "conflicting-attack.txt").write_text("90 91 92\n", encoding="utf-8")
            (attack / "attack.txt").write_text("100 101 102\n", encoding="utf-8")

            config = {
                "kind": "adfa-ld",
                "root": str(root),
                "partition_seed": 7,
                "normal_validation_fraction": 0.5,
                "phase_caps": {"pilot": {}},
            }
            dataset = load_academic_dataset(
                "adfa", config, project_root=Path.cwd(), phase="pilot"
            )

        inventory = dataset.source_manifest["native_inventory"]
        self.assertEqual(inventory["deduplicated_copy_count"], 1)
        self.assertEqual(inventory["contradictory_content_hash_groups_excluded"], 1)
        self.assertEqual(len(dataset.units), 5)
        self.assertNotIn("duplicate-of-train.txt", {unit.source_path for unit in dataset.units})
        self.assertFalse(any("conflicting" in unit.source_path for unit in dataset.units))
        self.assertTrue(audit_group_leakage(dataset)["passed"])

    def test_public_loader_rejects_unknown_phase_and_kind(self) -> None:
        with self.assertRaisesRegex(ValueError, "phase"):
            load_academic_dataset(
                "fixture", {"root": "."}, project_root=Path.cwd(), phase="exploratory"
            )
        with self.assertRaisesRegex(ValueError, "Unsupported"):
            load_academic_dataset(
                "fixture",
                {"kind": "unknown", "root": "."},
                project_root=Path.cwd(),
                phase="pilot",
            )


class LidConsumedEvidenceTests(unittest.TestCase):
    @staticmethod
    def _write_archive(
        path: Path,
        *,
        syscall_payload: str,
        pcap_payload: bytes,
        exploit: bool = False,
    ) -> None:
        metadata = {
            "container": [{"role": "victim"}, {"role": "attacker"}],
            "exploit": exploit,
        }
        with zipfile.ZipFile(path, "w") as bundle:
            bundle.writestr("trace.sc", syscall_payload)
            bundle.writestr("metadata.json", json.dumps(metadata))
            bundle.writestr("capture.pcap", pcap_payload)

    def test_lid_identity_hashes_only_consumed_members_not_packet_capture(self) -> None:
        with tempfile.TemporaryDirectory() as temporary:
            root = Path(temporary)
            first_path = root / "first.zip"
            second_path = root / "second.zip"
            changed_path = root / "changed.zip"
            self._write_archive(
                first_path,
                syscall_payload="0 1 2 3 4 open >\n0 1 2 3 4 read >\n",
                pcap_payload=b"packet-capture-a",
            )
            self._write_archive(
                second_path,
                syscall_payload="0 1 2 3 4 open >\n0 1 2 3 4 read >\n",
                pcap_payload=b"completely-different-packet-capture",
            )
            self._write_archive(
                changed_path,
                syscall_payload="0 1 2 3 4 open >\n0 1 2 3 4 write >\n",
                pcap_payload=b"packet-capture-a",
            )

            first_names, first_attack, first_identity = _parse_lid_consumed_archive(first_path)
            second_names, second_attack, second_identity = _parse_lid_consumed_archive(second_path)
            _, _, changed_identity = _parse_lid_consumed_archive(changed_path)

        self.assertEqual(first_names, ["open", "read"])
        self.assertFalse(first_attack)
        self.assertFalse(second_attack)
        self.assertEqual(first_identity, second_identity)
        self.assertNotEqual(first_identity, changed_identity)

    def test_lid_truth_comes_from_published_exploit_metadata(self) -> None:
        with tempfile.TemporaryDirectory() as temporary:
            archive = Path(temporary) / "attack.zip"
            self._write_archive(
                archive,
                syscall_payload="0 1 2 3 4 execve >\n",
                pcap_payload=b"ignored",
                exploit=True,
            )
            names, attack, identity = _parse_lid_consumed_archive(archive)

        self.assertEqual(names, ["execve"])
        self.assertTrue(attack)
        self.assertTrue(identity.startswith("sha256:"))

    def test_lid_confirmatory_slice_skips_pilot_valid_recordings(self) -> None:
        with tempfile.TemporaryDirectory() as temporary:
            root = Path(temporary)
            scenario = "Scenario-A"
            roles = (
                ("training", False),
                ("validation", False),
                ("test/normal", False),
                ("test/normal_and_attack", True),
            )
            for role, attack in roles:
                directory = root / scenario / Path(role)
                directory.mkdir(parents=True)
                for index in range(2):
                    self._write_archive(
                        directory / f"recording-{index}.zip",
                        syscall_payload=f"0 1 2 3 4 syscall_{role}_{index} >\n",
                        pcap_payload=b"ignored",
                        exploit=attack,
                    )
            config = {
                "kind": "lid-ds-2021",
                "evidence_origin": "official_native",
                "root": str(root),
                "scenarios": [scenario],
                "partition_seed": 2718,
                "phase_caps": {
                    "pilot": {"archives_per_scenario_partition": 1},
                    "confirmatory": {"archives_per_scenario_partition": 1},
                },
                "phase_allocation": {
                    "method": "disjoint-priority-slices-v1",
                    "pilot": {
                        "offsets": {
                            "training": 0,
                            "validation": 0,
                            "test-normal": 0,
                            "test-normal-and-attack": 0,
                        },
                        "counts": {
                            "training": 1,
                            "validation": 1,
                            "test-normal": 1,
                            "test-normal-and-attack": 1,
                        },
                    },
                    "confirmatory": {
                        "offsets": {
                            "training": 1,
                            "validation": 1,
                            "test-normal": 1,
                            "test-normal-and-attack": 1,
                        },
                        "counts": {
                            "training": 1,
                            "validation": 1,
                            "test-normal": 1,
                            "test-normal-and-attack": 1,
                        },
                    },
                },
                "window": {"sequence_length": 1, "max_windows_per_unit": 1},
            }

            pilot = load_academic_dataset(
                "lid-ds-2021", config, project_root=Path.cwd(), phase="pilot"
            )
            confirmatory = load_academic_dataset(
                "lid-ds-2021",
                config,
                project_root=Path.cwd(),
                phase="confirmatory",
            )

        self.assertEqual(len(pilot.units), 4)
        self.assertEqual(len(confirmatory.units), 4)
        self.assertFalse(
            {unit.unit_id for unit in pilot.units}
            & {unit.unit_id for unit in confirmatory.units}
        )
        self.assertFalse(
            {unit.group_id for unit in pilot.units}
            & {unit.group_id for unit in confirmatory.units}
        )

    def test_lid_confirmatory_slice_excludes_pilot_content_copies_across_roles(
        self,
    ) -> None:
        with tempfile.TemporaryDirectory() as temporary:
            root = Path(temporary)
            scenario = "Scenario-A"
            roles = (
                ("training", False, 2),
                ("validation", False, 3),
                ("test/normal", False, 2),
                ("test/normal_and_attack", True, 2),
            )
            archives_by_role: dict[str, list[Path]] = {}
            for role, attack, count in roles:
                directory = root / scenario / Path(role)
                directory.mkdir(parents=True)
                archives_by_role[role] = []
                for index in range(count):
                    archive = directory / f"recording-{index}.zip"
                    self._write_archive(
                        archive,
                        syscall_payload=f"0 1 2 3 4 syscall_{role}_{index} >\n",
                        pcap_payload=b"ignored",
                        exploit=attack,
                    )
                    archives_by_role[role].append(archive)

            # The pilot receives the highest-priority training archive and the
            # confirmatory validation slice receives the second-ranked validation
            # archive.  They contain the same detector-visible stream despite
            # having different paths and native roles.
            training_ranked = _stable_cap(
                archives_by_role["training"], 0, 2718, root
            )
            validation_ranked = _stable_cap(
                archives_by_role["validation"], 0, 2718, root
            )
            duplicate_payload = "0 1 2 3 4 shared_syscall >\n"
            self._write_archive(
                training_ranked[0],
                syscall_payload=duplicate_payload,
                pcap_payload=b"pilot-copy",
            )
            self._write_archive(
                validation_ranked[1],
                syscall_payload=duplicate_payload,
                pcap_payload=b"confirmatory-copy",
            )
            config = {
                "kind": "lid-ds-2021",
                "evidence_origin": "official_native",
                "root": str(root),
                "scenarios": [scenario],
                "partition_seed": 2718,
                "phase_caps": {
                    "pilot": {"archives_per_scenario_partition": 1},
                    "confirmatory": {"archives_per_scenario_partition": 1},
                },
                "phase_allocation": {
                    "method": "disjoint-content-priority-slices-v2",
                    "pilot": {
                        "offsets": {
                            "training": 0,
                            "validation": 0,
                            "test-normal": 0,
                            "test-normal-and-attack": 0,
                        },
                        "counts": {
                            "training": 1,
                            "validation": 1,
                            "test-normal": 1,
                            "test-normal-and-attack": 1,
                        },
                    },
                    "confirmatory": {
                        "offsets": {
                            "training": 1,
                            "validation": 1,
                            "test-normal": 1,
                            "test-normal-and-attack": 1,
                        },
                        "counts": {
                            "training": 1,
                            "validation": 1,
                            "test-normal": 1,
                            "test-normal-and-attack": 1,
                        },
                    },
                },
                "window": {"sequence_length": 4, "max_windows_per_unit": 1},
            }

            pilot = load_academic_dataset(
                "lid-ds-2021", config, project_root=Path.cwd(), phase="pilot"
            )
            confirmatory = load_academic_dataset(
                "lid-ds-2021",
                config,
                project_root=Path.cwd(),
                phase="confirmatory",
            )

        self.assertEqual(len(pilot.units), 4)
        self.assertEqual(len(confirmatory.units), 4)
        self.assertFalse(
            {unit.unit_id for unit in pilot.units}
            & {unit.unit_id for unit in confirmatory.units}
        )
        self.assertFalse(
            {unit.group_id for unit in pilot.units}
            & {unit.group_id for unit in confirmatory.units}
        )
        self.assertFalse(
            {unit.detector_input_identity for unit in pilot.units}
            & {unit.detector_input_identity for unit in confirmatory.units}
        )

    def test_lid_content_aware_phase_backfills_intra_phase_copies(self) -> None:
        with tempfile.TemporaryDirectory() as temporary:
            root = Path(temporary)
            scenario = "Scenario-A"
            roles = (
                ("training", False),
                ("validation", False),
                ("test/normal", False),
                ("test/normal_and_attack", True),
            )
            archives_by_role: dict[str, list[Path]] = {}
            for role, attack in roles:
                directory = root / scenario / Path(role)
                directory.mkdir(parents=True)
                archives_by_role[role] = []
                for index in range(3):
                    archive = directory / f"recording-{index}.zip"
                    self._write_archive(
                        archive,
                        syscall_payload=f"0 1 2 3 4 syscall_{role}_{index} >\n",
                        pcap_payload=b"ignored",
                        exploit=attack,
                    )
                    archives_by_role[role].append(archive)

            # The two highest-priority normal recordings are byte-identical
            # detector inputs in different native roles.  A content-aware V2
            # pilot must retain the training copy and backfill validation from
            # its next unique archive instead of relying on final deduplication.
            training_ranked = _stable_cap(
                archives_by_role["training"], 0, 2718, root
            )
            validation_ranked = _stable_cap(
                archives_by_role["validation"], 0, 2718, root
            )
            duplicate_payload = "0 1 2 3 4 shared_syscall >\n"
            self._write_archive(
                training_ranked[0],
                syscall_payload=duplicate_payload,
                pcap_payload=b"training-copy",
                exploit=False,
            )
            self._write_archive(
                validation_ranked[0],
                syscall_payload=duplicate_payload,
                pcap_payload=b"validation-copy",
                exploit=False,
            )
            config = {
                "kind": "lid-ds-2021",
                "evidence_origin": "official_native",
                "root": str(root),
                "scenarios": [scenario],
                "partition_seed": 2718,
                "phase_caps": {
                    "pilot": {"archives_per_scenario_partition": 1},
                    "confirmatory": {"archives_per_scenario_partition": 1},
                },
                "phase_allocation": {
                    "method": "disjoint-content-priority-slices-v2",
                    "pilot": {
                        "offsets": {
                            "training": 0,
                            "validation": 0,
                            "test-normal": 0,
                            "test-normal-and-attack": 0,
                        },
                        "counts": {
                            "training": 1,
                            "validation": 1,
                            "test-normal": 1,
                            "test-normal-and-attack": 1,
                        },
                    },
                    "confirmatory": {
                        "offsets": {
                            "training": 1,
                            "validation": 1,
                            "test-normal": 1,
                            "test-normal-and-attack": 1,
                        },
                        "counts": {
                            "training": 1,
                            "validation": 1,
                            "test-normal": 1,
                            "test-normal-and-attack": 1,
                        },
                    },
                },
                "window": {"sequence_length": 4, "max_windows_per_unit": 1},
            }

            pilot = load_academic_dataset(
                "lid-ds-2021", config, project_root=Path.cwd(), phase="pilot"
            )

        self.assertEqual(len(pilot.units), 4)
        self.assertEqual(
            pilot.source_manifest["deduplication"]["deduplicated_copy_count"], 0
        )
        self.assertEqual(
            pilot.source_manifest["within_phase_content_reservation"]
            ["excluded_duplicate_recording_count"],
            1,
        )
        self.assertEqual(len({unit.group_id for unit in pilot.units}), 4)
        self.assertEqual(
            len({unit.detector_input_identity for unit in pilot.units}), 4
        )

    def test_lid_content_aware_phase_rejects_contradictory_copy_semantics(
        self,
    ) -> None:
        with tempfile.TemporaryDirectory() as temporary:
            root = Path(temporary)
            scenario = "Scenario-A"
            roles = (
                ("training", False),
                ("validation", False),
                ("test/normal", False),
                ("test/normal_and_attack", True),
            )
            archives_by_role: dict[str, list[Path]] = {}
            for role, attack in roles:
                directory = root / scenario / Path(role)
                directory.mkdir(parents=True)
                archives_by_role[role] = []
                for index in range(2):
                    archive = directory / f"recording-{index}.zip"
                    self._write_archive(
                        archive,
                        syscall_payload=f"0 1 2 3 4 syscall_{role}_{index} >\n",
                        pcap_payload=b"ignored",
                        exploit=attack,
                    )
                    archives_by_role[role].append(archive)

            duplicate_payload = "0 1 2 3 4 contradictory_syscall >\n"
            self._write_archive(
                _stable_cap(archives_by_role["training"], 0, 2718, root)[0],
                syscall_payload=duplicate_payload,
                pcap_payload=b"normal-copy",
                exploit=False,
            )
            self._write_archive(
                _stable_cap(
                    archives_by_role["test/normal_and_attack"], 0, 2718, root
                )[0],
                syscall_payload=duplicate_payload,
                pcap_payload=b"attack-copy",
                exploit=True,
            )
            config = {
                "kind": "lid-ds-2021",
                "evidence_origin": "official_native",
                "root": str(root),
                "scenarios": [scenario],
                "partition_seed": 2718,
                "phase_caps": {
                    "pilot": {"archives_per_scenario_partition": 1},
                    "confirmatory": {"archives_per_scenario_partition": 1},
                },
                "phase_allocation": {
                    "method": "disjoint-content-priority-slices-v2",
                    "pilot": {
                        "offsets": {
                            "training": 0,
                            "validation": 0,
                            "test-normal": 0,
                            "test-normal-and-attack": 0,
                        },
                        "counts": {
                            "training": 1,
                            "validation": 1,
                            "test-normal": 1,
                            "test-normal-and-attack": 1,
                        },
                    },
                    "confirmatory": {
                        "offsets": {
                            "training": 1,
                            "validation": 1,
                            "test-normal": 1,
                            "test-normal-and-attack": 1,
                        },
                        "counts": {
                            "training": 1,
                            "validation": 1,
                            "test-normal": 1,
                            "test-normal-and-attack": 1,
                        },
                    },
                },
                "window": {"sequence_length": 4, "max_windows_per_unit": 1},
            }

            with self.assertRaisesRegex(ValueError, "contradictory"):
                load_academic_dataset(
                    "lid-ds-2021", config, project_root=Path.cwd(), phase="pilot"
                )


class HaiTimestampTests(unittest.TestCase):
    def test_official_single_digit_hour_minute_timestamp_is_supported(self) -> None:
        timestamp, resolution = _parse_hai_timestamp(
            "2022-08-17 0:00", source=Path("label-test2.csv"), row_number=2
        )

        self.assertEqual(timestamp.isoformat(), "2022-08-17T00:00:00")
        self.assertEqual(resolution, "minute")

    def test_second_resolution_remains_distinct(self) -> None:
        timestamp, resolution = _parse_hai_timestamp(
            "2022-08-17 00:00:01", source=Path("hai-test2.csv"), row_number=2
        )

        self.assertEqual(timestamp.isoformat(), "2022-08-17T00:00:01")
        self.assertEqual(resolution, "second")


if __name__ == "__main__":
    unittest.main()
