"""Integration tests for the resumable academic experiment runner."""

from __future__ import annotations

from dataclasses import dataclass, replace
import json
from pathlib import Path
import tempfile
import unittest
from unittest.mock import patch

import numpy as np

from parallel_truth_fingerprint.contracts.parameter_evidence import QuantityKind
from parallel_truth_fingerprint.lstm_service.offline_training import academic_runner
from parallel_truth_fingerprint.lstm_service.offline_training.academic_protocol import (
    AcademicDataset,
    AcademicUnit,
    PreparedDataset,
    PreparedPartition,
    file_sha256,
    fit_preprocessing,
    prepare_dataset_arrays,
    window_dataset,
)
from parallel_truth_fingerprint.lstm_service.offline_training.academic_runner import (
    CONFIG_SCHEMA,
    CONFIG_SCHEMA_V2,
    academic_paths,
    analyze_completed_cells,
    confirmatory_budget_issue,
    config_identity,
    load_academic_config,
    load_completed_cells,
    run_academic_phase,
    run_preflight,
)
from scripts.build_academic_parameter_requirements import (
    _contains_authority as requirements_contain_authority,
    _semantics as requirement_semantics,
    build as build_requirements,
    main as build_requirements_main,
)


def _config(output_root: Path) -> dict[str, object]:
    return {
        "schema_version": CONFIG_SCHEMA,
        "experiment_id": "synthetic-academic-test",
        "output_root": str(output_root),
        "pilot_seeds": [11, 22],
        "confirmatory_seeds": [101, 102, 103],
        "statistical_protocol": {
            "primary_metric": "auroc",
            "reported_metrics": ["f1", "balanced_accuracy", "mcc", "auroc", "auprc"],
            "confidence_level": 0.95,
            "bootstrap_replicates": 8,
            "bootstrap_seed_offset": 100,
            "target_ci_half_width": 0.02,
            "minimum_stochastic_trials": 2,
            "maximum_stochastic_trials": 6,
            "comparison_seed": 19,
            "permutation_replicates": 100,
            "threshold": {
                "method": "target-fpr",
                "target_fpr": 0.5,
                "normal_quantile": 0.5,
            },
        },
        "datasets": {
            "synthetic": {
                "minimum_support": {
                    "pilot": {"test_normal": 2, "test_attack": 2},
                    "confirmatory": {"test_normal": 2, "test_attack": 2},
                },
                "window": {
                    "sequence_length": 1,
                    "stride": 1,
                    "max_windows_per_unit": 1,
                    "aggregation": "max",
                },
                "models": {
                    "fixed-detector": {"deterministic": True},
                    "seeded-detector": {"deterministic": False},
                },
            }
        },
    }


def _unit(
    name: str,
    partition: str,
    value: float,
    *,
    label: int = 0,
    class_name: str = "Normal",
) -> AcademicUnit:
    return AcademicUnit(
        unit_id=f"synthetic:{name}",
        group_id=f"group:{name}",
        native_partition=partition,
        assigned_partition=partition,
        label=label,
        class_name=class_name,
        values=((value,),),
        source_path=f"{name}.csv",
        source_sha256=f"sha256:{name}",
        event_ids=(f"event:{name}",) if label else (),
    )


def _prepared_dataset() -> PreparedDataset:
    dataset = AcademicDataset(
        name="synthetic",
        modality="numeric-multivariate",
        protocol="synthetic-independent-unit-v1",
        units=(
            _unit("train-1", "train", 0.0),
            _unit("train-2", "train", 1.0),
            _unit("validation-1", "validation", 0.1),
            _unit("validation-2", "validation", 0.2),
            _unit("test-normal-1", "test", 0.1),
            _unit("test-normal-2", "test", 0.3),
            _unit("test-attack-1", "test", 4.0, label=1, class_name="Attack-A"),
            _unit("test-attack-2", "test", 5.0, label=1, class_name="Attack-B"),
        ),
        feature_names=("signal",),
        label_names=("Normal", "Attack-A", "Attack-B"),
        source_manifest={"origin": "synthetic test fixture"},
        phase="pilot",
    )
    windowed = window_dataset(
        dataset,
        sequence_length=1,
        stride=1,
        max_windows_per_unit=1,
        aggregation="max",
    )
    preprocessing = fit_preprocessing(dataset, windowed)
    return prepare_dataset_arrays(dataset, windowed, preprocessing)


class _FakeDetector:
    def __init__(self, seed: int) -> None:
        self._offset = seed * 1e-6

    def score(self, x: np.ndarray) -> np.ndarray:
        return np.asarray(x[:, 0, 0], dtype=np.float64) + self._offset


@dataclass(frozen=True)
class _FakeFitRecord:
    model: str
    seed: int

    def to_dict(self) -> dict[str, object]:
        return {
            "model": self.model,
            "seed": self.seed,
            "epochs_planned": 0,
            "epochs_executed": 0,
            "fit_wall_seconds": 0.0,
            "model_identity": "sha256:" + "a" * 64,
        }


def _fake_fit_detector(
    model_name: str,
    *,
    modality: str,
    train_x: np.ndarray,
    validation_x: np.ndarray,
    seed: int,
    config: object,
    categorical_vocabulary_size: int | None = None,
) -> tuple[_FakeDetector, _FakeFitRecord]:
    del modality, train_x, validation_x, config, categorical_vocabulary_size
    return _FakeDetector(seed), _FakeFitRecord(model_name, seed)


def _analysis_cell(
    model: str, seed: int, auroc: float, *, deterministic: bool
) -> dict[str, object]:
    return {
        "dataset": "synthetic",
        "model": model,
        "seed": seed,
        "deterministic": deterministic,
        "test": {
            "operating": {
                "f1": auroc - 0.1,
                "balanced_accuracy": auroc - 0.05,
                "mcc": auroc - 0.2,
            },
            "ranking": {"auroc": auroc, "auprc": auroc - 0.02},
        },
    }


class AcademicConfigurationTests(unittest.TestCase):
    def test_committed_numeric_inventory_and_hash_are_generated_not_hardcoded(self) -> None:
        repository_root = Path(__file__).resolve().parents[3]
        config_path = (
            repository_root / "configs" / "experiments" / "thesis-evaluation-v2.json"
        )
        requirements_path = repository_root / "configs" / "experiments" / (
            "thesis-evaluation-v2.parameter-requirements-v2.1.json"
        )
        config = load_academic_config(config_path)
        committed = json.loads(requirements_path.read_text(encoding="utf-8"))

        self.assertEqual(committed, build_requirements(config))
        self.assertEqual(
            config["numeric_authority"]["requirements_sha256"],  # type: ignore[index]
            file_sha256(requirements_path),
        )

    def test_numeric_inventory_uses_domain_semantics_for_counts_and_offsets(self) -> None:
        self.assertEqual(
            requirement_semantics(
                "/datasets/adfa-ld/phase_allocation/pilot/counts/train"
            ),
            ("count", "sample_count"),
        )
        self.assertEqual(
            requirement_semantics(
                "/datasets/adfa-ld/phase_allocation/pilot/offsets/train"
            ),
            ("count", "sample_offset"),
        )
        self.assertEqual(
            requirement_semantics(
                "/datasets/hai-23.05/window/max_windows_per_unit"
            ),
            ("count", "window_count"),
        )
        self.assertEqual(
            requirement_semantics("/validation_protocol/minimum_units_per_role"),
            ("count", "sample_count"),
        )
        self.assertEqual(
            requirement_semantics(
                "/statistical_protocol/minimum_class_carrying_clusters"
            ),
            ("count", QuantityKind.INDEPENDENT_CLUSTER_COUNT.value),
        )
        self.assertEqual(
            requirement_semantics("/statistical_protocol/bootstrap_replicates"),
            ("count", QuantityKind.BOOTSTRAP_REPLICATE_COUNT.value),
        )

    def test_numeric_inventory_generator_refuses_destructive_targets(self) -> None:
        repository_root = Path(__file__).resolve().parents[3]
        config_path = (
            repository_root / "configs" / "experiments" / "thesis-evaluation-v2.json"
        )
        with self.assertRaises(SystemExit):
            build_requirements_main(
                ["--config", str(config_path), "--output", str(config_path)]
            )

        with tempfile.TemporaryDirectory() as temporary:
            output = Path(temporary) / "requirements.json"
            output.write_text(
                json.dumps(
                    {
                        "slots": [
                            {
                                "authority_status": "resolved",
                                "parameter_revision_id": "revision-1",
                                "parameter_revision_sha256": "sha256:" + "0" * 64,
                            }
                        ]
                    }
                ),
                encoding="utf-8",
            )
            before = output.read_bytes()
            with self.assertRaises(SystemExit):
                build_requirements_main(
                    ["--config", str(config_path), "--output", str(output)]
                )
            self.assertEqual(output.read_bytes(), before)

        unresolved = build_requirements(load_academic_config(config_path))
        partial = json.loads(json.dumps(unresolved))
        partial["slots"][0]["authority_locator"] = "human-work-in-progress"
        self.assertFalse(requirements_contain_authority(unresolved))
        self.assertTrue(requirements_contain_authority(partial))

    def test_v2_rejects_incomplete_reporting_policy_and_degenerate_robust_cap(self) -> None:
        repository_root = Path(__file__).resolve().parents[3]
        source = json.loads(
            (
                repository_root
                / "configs"
                / "experiments"
                / "thesis-evaluation-v2.json"
            ).read_text(encoding="utf-8")
        )
        cases = (
            (
                "reported_metrics",
                lambda value: value["statistical_protocol"].update(
                    {"reported_metrics": []}
                ),
            ),
            (
                "multiplicity",
                lambda value: value["statistical_protocol"].update(
                    {"multiplicity": "none"}
                ),
            ),
            (
                "max_robust_z",
                lambda value: value["datasets"]["adfa-ld"]["models"][
                    "robust-distance"
                ].update({"max_robust_z": 0.0}),
            ),
        )
        with tempfile.TemporaryDirectory() as temporary:
            for message, mutate in cases:
                candidate = json.loads(json.dumps(source))
                mutate(candidate)
                path = Path(temporary) / f"{message}.json"
                path.write_text(json.dumps(candidate), encoding="utf-8")
                with self.subTest(message=message), self.assertRaisesRegex(
                    ValueError, message
                ):
                    load_academic_config(path)

    def test_temporal_gate_context_parser_is_exact(self) -> None:
        payload = {
            "context_id": "academic-temporal-context:test",
            "freeze_identity": "sha256:" + "1" * 64,
            "freeze_time": "2026-09-26T12:00:00-03:00",
            "test_identity": "sha256:" + "2" * 64,
            "test_time": "2026-09-26T12:01:00-03:00",
            "truth_identity": "sha256:" + "3" * 64,
            "truth_time": "2026-09-26T12:02:00-03:00",
        }
        parsed = academic_runner._parse_temporal_gate_context(
            json.dumps(payload).encode("utf-8")
        )
        self.assertEqual(parsed.context_id, payload["context_id"])

        with self.assertRaisesRegex(ValueError, "exactly"):
            academic_runner._parse_temporal_gate_context(
                json.dumps({**payload, "status": "invented"}).encode("utf-8")
            )

    def test_v2_confirmatory_schedule_is_exactly_fifty_in_five_batches(self) -> None:
        repository_root = Path(__file__).resolve().parents[3]
        config = load_academic_config(
            repository_root
            / "configs"
            / "experiments"
            / "thesis-evaluation-v2.json"
        )
        rows = academic_runner._logical_plan(
            config, "confirmatory", project_root=repository_root
        )
        stochastic: dict[str, list[dict[str, object]]] = {}
        deterministic: list[dict[str, object]] = []
        for row in rows:
            if row["deterministic"]:
                deterministic.append(row)
            else:
                stochastic.setdefault(
                    f"{row['dataset']}/{row['model']}", []
                ).append(row)

        self.assertEqual(len(rows), 158)
        self.assertEqual(len(deterministic), 8)
        self.assertTrue(all(len(family) == 50 for family in stochastic.values()))
        self.assertEqual(len(stochastic), 3)
        self.assertEqual(
            {
                row["batch_id"]
                for family in stochastic.values()
                for row in family
            },
            {f"batch-{index:02d}" for index in range(1, 6)},
        )
        self.assertTrue(all(row["batch_id"] == "batch-01" for row in deterministic))
        with self.assertRaisesRegex(ValueError, "requires confirmatory_batch"):
            academic_runner._requested_batch_id(
                config, phase="confirmatory", confirmatory_batch=None
            )
        self.assertEqual(
            academic_runner._requested_batch_id(
                config, phase="confirmatory", confirmatory_batch=3
            ),
            "batch-03",
        )

    def test_over_budget_authorization_never_waives_unknown_cost(self) -> None:
        self.assertIsNotNone(
            confirmatory_budget_issue(None, allow_over_budget=True)
        )
        self.assertIsNotNone(
            confirmatory_budget_issue(
                {"computational_load": {"projection_complete": False}},
                allow_over_budget=True,
            )
        )
        complete = {
            "computational_load": {
                "projection_complete": True,
                "projected_preflight_invocations": 6,
                "confirmatory_preflight_invocations": 6,
                "confirmatory_standalone_preflight_invocations": 1,
                "confirmatory_batch_preflight_invocations": 5,
                "projected_total_cpu_hours_conservative": 13.0,
                "ask_first_cpu_hours": 12.0,
            }
        }
        self.assertIsNotNone(
            confirmatory_budget_issue(complete, allow_over_budget=False)
        )
        self.assertIsNone(
            confirmatory_budget_issue(complete, allow_over_budget=True)
        )
        non_finite = json.loads(json.dumps(complete))
        non_finite["computational_load"][  # type: ignore[index]
            "projected_total_cpu_hours_conservative"
        ] = float("inf")
        self.assertIsNotNone(
            confirmatory_budget_issue(non_finite, allow_over_budget=True)
        )

    def test_blocked_v2_preflight_retains_full_batch_progress_counts(self) -> None:
        repository_root = Path(__file__).resolve().parents[3]
        config = load_academic_config(
            repository_root
            / "configs"
            / "experiments"
            / "thesis-evaluation-v2.json"
        )
        with tempfile.TemporaryDirectory() as temporary:
            config["output_root"] = str(Path(temporary) / "academic-output")
            with patch.object(
                academic_runner,
                "_prepare_one_dataset",
                side_effect=AssertionError(
                    "blocked numeric authority must not prepare benchmark data"
                ),
            ):
                summary = run_academic_phase(
                    config,
                    project_root=repository_root,
                    phase="confirmatory",
                    confirmatory_batch=1,
                )
            paths = academic_paths(
                config, project_root=repository_root, phase="confirmatory"
            )
            preflight = json.loads(
                (paths.phase / "preflight.json").read_text(encoding="utf-8")
            )
            ledger = json.loads(
                (paths.phase / "confirmatory-batch-ledger.json").read_text(
                    encoding="utf-8"
                )
            )

        self.assertEqual(summary["planned_cell_count"], 158)
        self.assertEqual(
            preflight["repetition_planning_gate"]["status"], "blocked"
        )
        self.assertEqual(
            preflight["computational_load"]["projected_preflight_invocations"],
            6,
        )
        self.assertEqual(
            preflight["computational_load"]["confirmatory_preflight_invocations"],
            6,
        )
        self.assertEqual(
            preflight["computational_load"][
                "confirmatory_standalone_preflight_invocations"
            ],
            1,
        )
        self.assertEqual(
            preflight["computational_load"][
                "confirmatory_batch_preflight_invocations"
            ],
            5,
        )
        self.assertTrue(
            summary["eligibility_gate"]["confirmatory_batch_ledger_verified"]
        )
        self.assertEqual(
            summary["confirmatory_batch_ledger_identity"],
            academic_runner.canonical_json_hash(ledger),
        )
        self.assertEqual(
            [row["expected_cell_count"] for row in summary["batch_progress"]],
            [38, 30, 30, 30, 30],
        )
        self.assertTrue(
            all(
                row["authenticated_complete_cell_count"] == 0
                and row["complete"] is False
                for row in summary["batch_progress"]
            )
        )

    def test_v2_rejects_non_uint32_seeds_and_unsafe_budget_values(self) -> None:
        repository_root = Path(__file__).resolve().parents[3]
        source = repository_root / "configs" / "experiments" / "thesis-evaluation-v2.json"
        base = json.loads(source.read_text(encoding="utf-8"))
        cases = (
            ("negative seed", ("pilot_seeds", 0, -1), "uint32"),
            ("oversized seed", ("confirmatory_seeds", 0, 2**32), "uint32"),
            ("small safety factor", ("computational_budget", "safety_factor", 0.5), "at least 1"),
            ("zero review threshold", ("computational_budget", "ask_first_cpu_hours", 0), "positive"),
        )
        with tempfile.TemporaryDirectory() as temporary:
            path = Path(temporary) / "config.json"
            for label, (container, key, value), message in cases:
                with self.subTest(label=label):
                    config = json.loads(json.dumps(base))
                    config[container][key] = value
                    path.write_text(json.dumps(config), encoding="utf-8")
                    with self.assertRaisesRegex(ValueError, message):
                        load_academic_config(path)

    def test_schedule_generation_revalidates_mutated_v2_seed_ledger(self) -> None:
        repository_root = Path(__file__).resolve().parents[3]
        config = json.loads(
            (
                repository_root
                / "configs"
                / "experiments"
                / "thesis-evaluation-v2.json"
            ).read_text(encoding="utf-8")
        )
        config["confirmatory_seeds"][0] = -1
        model = config["datasets"]["adfa-ld"]["models"]["categorical-unigram"]

        with self.assertRaisesRegex(ValueError, "uint32"):
            academic_runner._schedule_entries(config, model, "pilot")

    def test_v2_phase_allocation_rejects_pilot_confirmatory_overlap(self) -> None:
        repository_root = Path(__file__).resolve().parents[3]
        source = repository_root / "configs" / "experiments" / "thesis-evaluation-v2.json"
        config = json.loads(source.read_text(encoding="utf-8"))
        config["datasets"]["adfa-ld"]["phase_allocation"]["confirmatory"][  # type: ignore[index]
            "offsets"
        ]["train"] = 0
        with tempfile.TemporaryDirectory() as temporary:
            path = Path(temporary) / "config.json"
            path.write_text(json.dumps(config), encoding="utf-8")

            with self.assertRaisesRegex(ValueError, "overlaps"):
                load_academic_config(path)

    def test_v2_lid_content_identity_phase_allocation_method_is_accepted(self) -> None:
        repository_root = Path(__file__).resolve().parents[3]
        source = repository_root / "configs" / "experiments" / "thesis-evaluation-v2.json"
        config = json.loads(source.read_text(encoding="utf-8"))
        config["datasets"]["lid-ds-2021"]["phase_allocation"][  # type: ignore[index]
            "method"
        ] = "disjoint-content-priority-slices-v2"
        with tempfile.TemporaryDirectory() as temporary:
            path = Path(temporary) / "config.json"
            path.write_text(json.dumps(config), encoding="utf-8")

            loaded = load_academic_config(path)

        self.assertEqual(
            loaded["datasets"]["lid-ds-2021"]["phase_allocation"]["method"],  # type: ignore[index]
            "disjoint-content-priority-slices-v2",
        )

    def test_v2_randomness_classification_cannot_be_relabelled_in_config(self) -> None:
        repository_root = Path(__file__).resolve().parents[3]
        source = repository_root / "configs" / "experiments" / "thesis-evaluation-v2.json"
        config = json.loads(source.read_text(encoding="utf-8"))
        config["datasets"]["adfa-ld"]["models"]["recurrent-autoencoder"][  # type: ignore[index]
            "deterministic"
        ] = True
        with tempfile.TemporaryDirectory() as temporary:
            path = Path(temporary) / "config.json"
            path.write_text(json.dumps(config), encoding="utf-8")

            with self.assertRaisesRegex(ValueError, "implementation-owned classification"):
                load_academic_config(path)

    def test_config_load_identity_and_output_path_are_content_addressed(self) -> None:
        with tempfile.TemporaryDirectory() as temporary:
            root = Path(temporary)
            config = _config(root / "evidence")
            path = root / "config.json"
            path.write_text(json.dumps(config), encoding="utf-8")

            loaded = load_academic_config(path)
            identity = config_identity(loaded)
            reordered = dict(reversed(list(loaded.items())))
            changed = {**loaded, "pilot_seeds": [11, 23]}
            paths = academic_paths(loaded, project_root=root, phase="pilot")

        self.assertEqual(identity, config_identity(reordered))
        self.assertNotEqual(identity, config_identity(changed))
        self.assertTrue(identity.startswith("sha256:"))
        self.assertEqual(paths.root.parent.name, "synthetic-academic-test")
        self.assertEqual(paths.root.name, identity.split(":", 1)[1][:16])
        self.assertEqual(paths.cells, paths.phase / "cells")
        self.assertEqual(paths.predictions, paths.phase / "predictions")

    def test_config_validation_rejects_bad_schema_id_and_duplicate_seeds(self) -> None:
        with tempfile.TemporaryDirectory() as temporary:
            path = Path(temporary) / "config.json"
            cases = (
                ({**_config(Path(temporary)), "schema_version": "wrong"}, "schema_version"),
                ({**_config(Path(temporary)), "experiment_id": "Upper Case"}, "experiment_id"),
                ({**_config(Path(temporary)), "pilot_seeds": [1, "1"]}, "duplicates"),
            )
            for value, message in cases:
                with self.subTest(message=message):
                    path.write_text(json.dumps(value), encoding="utf-8")
                    with self.assertRaisesRegex(ValueError, message):
                        load_academic_config(path)

    def test_invalid_phase_is_rejected_before_writing(self) -> None:
        with tempfile.TemporaryDirectory() as temporary:
            with self.assertRaisesRegex(ValueError, "phase"):
                academic_paths(
                    _config(Path(temporary)), project_root=Path(temporary), phase="draft"
                )


class AcademicExecutionAndResumeTests(unittest.TestCase):
    def test_v2_unresolved_numeric_authority_blocks_before_dataset_loading(self) -> None:
        repository_root = Path(__file__).resolve().parents[3]
        config = load_academic_config(
            repository_root
            / "configs"
            / "experiments"
            / "thesis-evaluation-v2.json"
        )
        with tempfile.TemporaryDirectory() as temporary:
            config["output_root"] = str(Path(temporary) / "academic-output")
            with patch.object(academic_runner, "_prepare_one_dataset") as prepare:
                preflight = run_preflight(
                    config, project_root=repository_root, phase="pilot"
                )

        self.assertFalse(preflight["ready"])
        self.assertEqual(
            preflight["numeric_authority"]["accountability_outcome"], "blocked"
        )
        expected_count = json.loads(
            (
                repository_root
                / "configs"
                / "experiments"
                / "thesis-evaluation-v2.parameter-requirements-v2.1.json"
            ).read_text(encoding="utf-8")
        )["numeric_consumer_count"]
        self.assertEqual(
            preflight["numeric_authority"]["numeric_consumer_count"], expected_count
        )
        self.assertEqual(preflight["numeric_authority"]["resolved_consumer_count"], 0)
        self.assertEqual(
            len(preflight["numeric_authority"]["violations"]), expected_count
        )
        self.assertTrue(
            all(
                dataset["error_type"] == "NumericAuthorityBlocked"
                for dataset in preflight["datasets"].values()
            )
        )
        prepare.assert_not_called()

    def test_v2_validation_roles_are_deterministic_and_cluster_disjoint(self) -> None:
        validation = PreparedPartition(
            x=np.arange(6, dtype=np.float32).reshape(6, 1, 1),
            window_ids=tuple(f"window-{index}" for index in range(6)),
            unit_ids=tuple(f"unit-{index}" for index in range(6)),
            labels=np.zeros(6, dtype=np.int64),
            class_names=("Normal",) * 6,
            event_ids=((),) * 6,
            cluster_ids=("cluster-a", "cluster-a", "cluster-b", "cluster-c", "cluster-d", "cluster-d"),
            evidence_origins=("official_native",) * 6,
        )
        config = {
            "schema_version": CONFIG_SCHEMA_V2,
            "validation_protocol": {
                "early_stopping_fraction": 0.5,
                "split_seed": 424242,
                "minimum_units_per_role": 2,
            },
        }

        stopping, calibration, audit = academic_runner._validation_role_partitions(
            validation, config
        )
        repeated = academic_runner._validation_role_partitions(validation, config)

        self.assertTrue(audit["passed"])
        self.assertTrue(audit["independent_roles"])
        self.assertEqual(audit["shared_unit_count"], 0)
        self.assertEqual(audit["shared_cluster_count"], 0)
        self.assertEqual(audit["early_stopping_windows"], len(stopping.window_ids))
        self.assertEqual(audit["calibration_windows"], len(calibration.window_ids))
        self.assertFalse(set(stopping.unit_ids) & set(calibration.unit_ids))
        self.assertFalse(set(stopping.cluster_ids) & set(calibration.cluster_ids))
        self.assertEqual(audit["assignment_identity"], repeated[2]["assignment_identity"])

    def test_v2_validation_roles_fail_closed_for_one_dependence_cluster(self) -> None:
        validation = PreparedPartition(
            x=np.arange(4, dtype=np.float32).reshape(4, 1, 1),
            window_ids=tuple(f"window-{index}" for index in range(4)),
            unit_ids=tuple(f"unit-{index}" for index in range(4)),
            labels=np.zeros(4, dtype=np.int64),
            class_names=("Normal",) * 4,
            event_ids=((),) * 4,
            cluster_ids=("one-recording",) * 4,
            evidence_origins=("official_native",) * 4,
        )
        config = {
            "schema_version": CONFIG_SCHEMA_V2,
            "validation_protocol": {
                "early_stopping_fraction": 0.5,
                "split_seed": 1,
                "minimum_units_per_role": 1,
            },
        }

        with self.assertRaisesRegex(ValueError, "independent clusters"):
            academic_runner._validation_role_partitions(validation, config)

    def test_preflight_execution_artifacts_and_resume_are_end_to_end(self) -> None:
        with tempfile.TemporaryDirectory() as temporary:
            project_root = Path(temporary)
            config = _config(project_root / "academic-output")
            prepared = _prepared_dataset()
            with patch.object(academic_runner, "_prepare_one_dataset", return_value=prepared), patch.object(
                academic_runner, "fit_detector", side_effect=_fake_fit_detector
            ):
                preflight = run_preflight(config, project_root=project_root, phase="pilot")
                first = run_academic_phase(config, project_root=project_root, phase="pilot")
                second = run_academic_phase(config, project_root=project_root, phase="pilot")

            paths = academic_paths(config, project_root=project_root, phase="pilot")
            frozen = json.loads((paths.root / "frozen-config.json").read_text(encoding="utf-8"))
            cells = load_completed_cells(paths.phase)
            prediction_paths = sorted(paths.predictions.glob("*.jsonl"))

            self.assertTrue(preflight["ready"])
            self.assertEqual(preflight["datasets"]["synthetic"]["status"], "ready")
            self.assertEqual(first["planned_cell_count"], 3)
            self.assertEqual(len(first["completed_now"]), 3)
            self.assertEqual(first["resumed"], [])
            self.assertEqual(first["failed"], [])
            self.assertEqual(second["planned_cell_count"], 3)
            self.assertEqual(second["completed_now"], [])
            self.assertEqual(len(second["resumed"]), 3)
            self.assertEqual(second["failed"], [])
            self.assertGreaterEqual(
                second["evidence_generation_cpu_seconds_cumulative"],
                first["evidence_generation_cpu_seconds_cumulative"]
                + second["elapsed_cpu_seconds"],
            )
            self.assertEqual(len(cells), 3)
            self.assertEqual(len(prediction_paths), 3)
            self.assertEqual(frozen, config)
            self.assertTrue((paths.root / "provenance.json").is_file())
            self.assertTrue((paths.phase / "preflight.json").is_file())
            self.assertTrue((paths.phase / "run-summary.json").is_file())
            for prediction_path in prediction_paths:
                rows = [json.loads(line) for line in prediction_path.read_text(encoding="utf-8").splitlines()]
                self.assertEqual(len(rows), 4)
                self.assertEqual({row["truth"] for row in rows}, {0, 1})
                self.assertTrue(all(row["unit_id"].startswith("synthetic:") for row in rows))
            for cell in cells:
                self.assertEqual(cell["partition_roles"]["threshold_calibration"], "validation only")
                self.assertEqual(cell["threshold_calibration"]["validation_support"]["attack"], 0)
                self.assertEqual(cell["predictions_artifact"]["rows"], 4)

    def test_immutable_writer_accepts_identical_bytes_and_rejects_conflicts(self) -> None:
        with tempfile.TemporaryDirectory() as temporary:
            artifact = Path(temporary) / "cell.json"
            academic_runner._write_json(artifact, {"value": 1}, immutable=True)
            original = artifact.read_bytes()
            academic_runner._write_json(artifact, {"value": 1}, immutable=True)

            with self.assertRaisesRegex(RuntimeError, "Immutable artifact conflict"):
                academic_runner._write_json(artifact, {"value": 2}, immutable=True)

            self.assertEqual(artifact.read_bytes(), original)
            self.assertEqual(list(artifact.parent.glob(".*.tmp")), [])

    def test_governance_reader_hashes_the_exact_bytes_it_returns(self) -> None:
        with tempfile.TemporaryDirectory() as temporary:
            artifact = Path(temporary) / "authority.json"
            payload = b'{"authority":"frozen"}\n'
            artifact.write_bytes(payload)
            expected = "sha256:" + academic_runner.sha256(payload).hexdigest()

            self.assertEqual(
                academic_runner._read_verified_bytes(
                    artifact, expected, field="authority_sha256"
                ),
                payload,
            )
            with self.assertRaisesRegex(ValueError, "does not match"):
                academic_runner._read_verified_bytes(
                    artifact,
                    "sha256:" + "0" * 64,
                    field="authority_sha256",
                )

    def test_atomic_writer_rejects_output_symlink(self) -> None:
        with tempfile.TemporaryDirectory() as temporary:
            root = Path(temporary)
            external = root / "external.json"
            external.write_text('{"untouched": true}\n', encoding="utf-8")
            artifact = root / "artifact.json"
            try:
                artifact.symlink_to(external)
            except OSError as exc:
                self.skipTest(f"symlink creation is unavailable: {exc}")

            with self.assertRaisesRegex(RuntimeError, "must not traverse a symlink"):
                academic_runner._write_json(
                    artifact, {"untouched": False}, immutable=False
                )
            self.assertEqual(
                external.read_text(encoding="utf-8"), '{"untouched": true}\n'
            )

    def test_committed_cell_transaction_recovers_interrupted_pair_publication(self) -> None:
        with tempfile.TemporaryDirectory() as temporary:
            project_root = Path(temporary)
            config = _config(project_root / "academic-output")
            paths = academic_paths(config, project_root=project_root, phase="pilot")
            for directory in (
                paths.phase,
                paths.cells,
                paths.predictions,
                paths.transactions,
            ):
                directory.mkdir(parents=True, exist_ok=True)
            cell_id = "dataset__model__seed-1__transaction"
            rows = [{"unit_id": "unit-a", "truth": 0, "score": 0.1}]
            prediction_payload = academic_runner._jsonl_bytes(rows)
            prediction_hash = "sha256:" + academic_runner.sha256(
                prediction_payload
            ).hexdigest()
            manifest_path = paths.transactions / f"{cell_id}.transaction.json"
            cell = {
                "cell_id": cell_id,
                "status": "complete",
                "predictions_artifact": {
                    "path": str((paths.predictions / f"{cell_id}.jsonl").resolve()),
                    "sha256": prediction_hash,
                    "rows": 1,
                },
                "publication_transaction": {
                    "transaction_id": f"academic-cell-publication:{cell_id}",
                    "manifest_path": str(manifest_path.resolve()),
                },
            }
            original_atomic_write = academic_runner._atomic_write
            canonical_cell = paths.cells / f"{cell_id}.json"

            def interrupt_cell_target(
                path: Path, payload: bytes, *, immutable: bool
            ) -> None:
                if Path(path) == canonical_cell:
                    raise OSError("simulated crash before canonical cell publication")
                original_atomic_write(path, payload, immutable=immutable)

            with patch.object(
                academic_runner,
                "_atomic_write",
                side_effect=interrupt_cell_target,
            ), self.assertRaisesRegex(OSError, "simulated crash"):
                academic_runner._publish_cell_transaction(
                    paths, cell=cell, prediction_rows=rows
                )

            canonical_prediction = paths.predictions / f"{cell_id}.jsonl"
            self.assertTrue(manifest_path.is_file())
            self.assertTrue(canonical_prediction.is_file())
            self.assertFalse(canonical_cell.exists())

            academic_runner._recover_cell_transactions(paths)

            self.assertTrue(canonical_cell.is_file())
            recovered = json.loads(canonical_cell.read_text(encoding="utf-8"))
            academic_runner._validate_publication_transaction(
                recovered,
                cell_path=canonical_cell,
                prediction_path=canonical_prediction,
            )

    def test_v2_cell_identity_binds_truth_and_source_provenance(self) -> None:
        repository_root = Path(__file__).resolve().parents[3]
        config = load_academic_config(
            repository_root
            / "configs"
            / "experiments"
            / "thesis-evaluation-v2.json"
        )
        original = _prepared_dataset()
        official_units = tuple(
            replace(unit, evidence_origin="official_native")
            for unit in original.dataset.units
        )
        prepared = replace(
            original,
            dataset=replace(
                original.dataset,
                units=official_units,
                evidence_origin="official_native",
            ),
        )
        changed_units = list(official_units)
        changed_units[-1] = replace(
            changed_units[-1],
            label=0,
            class_name="Normal",
            event_ids=(),
            source_sha256="sha256:corrected-truth-source",
        )
        corrected = replace(
            prepared,
            dataset=replace(prepared.dataset, units=tuple(changed_units)),
        )
        role_audit = {"assignment_identity": "sha256:" + "a" * 64}
        model_config = {"deterministic": True, "max_robust_z": 20.0}
        with patch.object(
            academic_runner,
            "_validation_role_partitions",
            return_value=(
                prepared.partitions["validation"],
                prepared.partitions["validation"],
                role_audit,
            ),
        ):
            first = academic_runner._cell_descriptor(
                config,
                prepared,
                dataset_key="adfa-ld",
                model_name="robust-distance",
                model_config=model_config,
                phase="pilot",
                seed=101,
            )
            second = academic_runner._cell_descriptor(
                config,
                corrected,
                dataset_key="adfa-ld",
                model_name="robust-distance",
                model_config=model_config,
                phase="pilot",
                seed=101,
            )

        self.assertEqual(
            prepared.dataset.model_input_identity,
            corrected.dataset.model_input_identity,
        )
        self.assertNotEqual(
            first["result_dataset_identity"], second["result_dataset_identity"]
        )
        self.assertNotEqual(first["cell_identity"], second["cell_identity"])

    def test_numerical_core_manifest_covers_schema_and_dataset_parsers(self) -> None:
        repository_root = Path(__file__).resolve().parents[3]
        config = load_academic_config(
            repository_root
            / "configs"
            / "experiments"
            / "thesis-evaluation-v2.json"
        )
        files = academic_runner._numerical_core_manifest(
            repository_root, config
        )["files"]
        self.assertTrue(
            {
                "src/parallel_truth_fingerprint/lstm_service/offline_training/academic_numeric_schema.py",
                "src/parallel_truth_fingerprint/lstm_service/offline_training/benchmarks/adfa_ld.py",
                "src/parallel_truth_fingerprint/lstm_service/offline_training/benchmarks/lid_ds_2021.py",
                "src/parallel_truth_fingerprint/evidence/hai_adapter.py",
                "src/parallel_truth_fingerprint/evidence/source_catalog.py",
            }.issubset(files)
        )

    def test_v2_raw_rows_reconstruct_threshold_predictions_and_all_metrics(self) -> None:
        repository_root = Path(__file__).resolve().parents[3]
        config = load_academic_config(
            repository_root
            / "configs"
            / "experiments"
            / "thesis-evaluation-v2.json"
        )
        original = _prepared_dataset()
        official_units = tuple(
            replace(unit, evidence_origin="official_native")
            for unit in original.dataset.units
        )
        official_dataset = replace(
            original.dataset,
            units=official_units,
            evidence_origin="official_native",
        )
        official_partitions = {
            name: replace(
                partition,
                evidence_origins=("official_native",) * len(partition.window_ids),
            )
            for name, partition in original.partitions.items()
        }
        prepared = replace(
            original,
            dataset=official_dataset,
            windowed=replace(original.windowed, evidence_origin="official_native"),
            partitions=official_partitions,
        )
        validation = prepared.partitions["validation"]
        role_audit = {
            "assignment_identity": "sha256:" + "b" * 64,
            "early_stopping_identity": "sha256:" + "c" * 64,
            "calibration_identity": "sha256:" + "d" * 64,
        }
        descriptor = {
            "cell_id": "synthetic__fixed-detector__seed-101__raw-evidence",
            "cell_identity": "sha256:" + "e" * 64,
            "runner_protocol": academic_runner.RUNNER_PROTOCOL,
            "config_identity": config_identity(config),
            "dataset_key": "synthetic",
            "dataset": "synthetic",
            "model": "fixed-detector",
            "seed": 101,
            "deterministic": True,
            "phase": "pilot",
            "validation_role_assignment_identity": role_audit["assignment_identity"],
        }
        with tempfile.TemporaryDirectory() as temporary, patch.object(
            academic_runner, "fit_detector", side_effect=_fake_fit_detector
        ), patch.object(
            academic_runner,
            "_validation_role_partitions",
            return_value=(validation, validation, role_audit),
        ):
            cell, prediction_rows = academic_runner._execute_cell(
                config,
                prepared,
                descriptor=descriptor,
                model_name="fixed-detector",
                model_config={"deterministic": True},
                seed=101,
                predictions_dir=Path(temporary) / "predictions",
                numeric_authority={"accountability_outcome": "accountable"},
                project_root=repository_root,
            )

        reconstructed = academic_runner.validate_cell_raw_reconstruction(
            cell, config=config, prediction_rows=prediction_rows
        )
        self.assertTrue(reconstructed["passed"])
        self.assertEqual(reconstructed["calibration_row_count"], 2)
        self.assertEqual(reconstructed["test_row_count"], 4)

        tampered = json.loads(json.dumps(cell))
        tampered["test"]["operating"]["f1"] = 0.123456  # type: ignore[index]
        with self.assertRaisesRegex(ValueError, "test metrics"):
            academic_runner.validate_cell_raw_reconstruction(
                tampered, config=config, prediction_rows=prediction_rows
            )

    def test_existing_cell_with_wrong_identity_is_reported_and_not_overwritten(self) -> None:
        with tempfile.TemporaryDirectory() as temporary:
            project_root = Path(temporary)
            config = _config(project_root / "academic-output")
            config["datasets"]["synthetic"]["models"] = {  # type: ignore[index]
                "fixed-detector": {"deterministic": True}
            }
            prepared = _prepared_dataset()
            with patch.object(academic_runner, "_prepare_one_dataset", return_value=prepared), patch.object(
                academic_runner, "fit_detector", side_effect=_fake_fit_detector
            ):
                first = run_academic_phase(config, project_root=project_root, phase="pilot")
                paths = academic_paths(config, project_root=project_root, phase="pilot")
                cell_path = next(paths.cells.glob("*.json"))
                corrupted = json.loads(cell_path.read_text(encoding="utf-8"))
                corrupted["cell_identity"] = "sha256:wrong"
                cell_path.write_text(json.dumps(corrupted), encoding="utf-8")
                before = cell_path.read_bytes()
                second = run_academic_phase(config, project_root=project_root, phase="pilot")

            self.assertEqual(len(first["completed_now"]), 1)
            self.assertEqual(second["completed_now"], [])
            self.assertEqual(second["resumed"], [])
            self.assertEqual(
                second["failed"][0]["error_type"], "ResumeIntegrityError"
            )
            self.assertEqual(cell_path.read_bytes(), before)

    def test_confirmatory_batch_order_requires_all_prior_logical_cells(self) -> None:
        config = {
            "schema_version": CONFIG_SCHEMA_V2,
            "experiment_id": "ordered",
            "confirmatory_seeds": list(range(1, 51)),
            "execution_protocol": {"confirmatory_batch_size": 10},
        }
        schedule_identity = academic_runner._phase_schedule_identity(
            config, "confirmatory"
        )
        rows = [
            {
                "dataset": "dataset-a",
                "model": "model-a",
                "seed": 1,
                "batch_id": "batch-01",
                "schedule_identity": schedule_identity,
            },
            {
                "dataset": "dataset-a",
                "model": "model-a",
                "seed": 2,
                "batch_id": "batch-02",
                "schedule_identity": schedule_identity,
            },
        ]
        with tempfile.TemporaryDirectory() as temporary:
            phase_path = Path(temporary)
            (phase_path / "confirmatory-batch-ledger.json").write_text(
                json.dumps(academic_runner.confirmatory_batch_ledger(config)),
                encoding="utf-8",
            )
            issue = academic_runner._confirmatory_batch_order_issue(
                config,
                phase="confirmatory",
                batch_id="batch-02",
                logical_rows=rows,
                phase_path=phase_path,
            )
            self.assertIn("batch-01: 1 missing", str(issue))

            cells = phase_path / "cells"
            cells.mkdir()
            prior = {
                **rows[0],
                "dataset_key": rows[0]["dataset"],
                "status": "complete",
                "cell_id": "prior-a",
                "config_identity": config_identity(config),
                "phase": "confirmatory",
            }
            (cells / "prior.json").write_text(json.dumps(prior), encoding="utf-8")
            self.assertIsNone(
                academic_runner._confirmatory_batch_order_issue(
                    config,
                    phase="confirmatory",
                    batch_id="batch-02",
                    logical_rows=rows,
                    phase_path=phase_path,
                )
            )

            duplicate = {**prior, "cell_id": "prior-b"}
            duplicate_path = cells / "duplicate.json"
            duplicate_path.write_text(json.dumps(duplicate), encoding="utf-8")
            duplicate_issue = academic_runner._confirmatory_batch_order_issue(
                config,
                phase="confirmatory",
                batch_id="batch-02",
                logical_rows=rows,
                phase_path=phase_path,
            )
            self.assertIn("duplicate logical schedule", str(duplicate_issue))
            duplicate_path.unlink()

            extra = {
                **prior,
                "cell_id": "extra",
                "seed": 999,
            }
            extra_path = cells / "extra.json"
            extra_path.write_text(json.dumps(extra), encoding="utf-8")
            extra_issue = academic_runner._confirmatory_batch_order_issue(
                config,
                phase="confirmatory",
                batch_id="batch-02",
                logical_rows=rows,
                phase_path=phase_path,
            )
            self.assertIn("unplanned logical artifact", str(extra_issue))
            extra_path.unlink()

            ledger_path = phase_path / "confirmatory-batch-ledger.json"
            tampered_ledger = json.loads(ledger_path.read_text(encoding="utf-8"))
            tampered_ledger["batch_size"] = 9
            ledger_path.write_text(json.dumps(tampered_ledger), encoding="utf-8")
            ledger_issue = academic_runner._confirmatory_batch_order_issue(
                config,
                phase="confirmatory",
                batch_id="batch-02",
                logical_rows=rows,
                phase_path=phase_path,
            )
            self.assertIn("ledger disagrees", str(ledger_issue))

    def test_completed_cell_loader_rejects_symlinked_artifact(self) -> None:
        with tempfile.TemporaryDirectory() as temporary:
            root = Path(temporary)
            phase_path = root / "phase"
            cells_path = phase_path / "cells"
            cells_path.mkdir(parents=True)
            external = root / "external.json"
            external.write_text(
                json.dumps({"status": "complete", "cell_id": "external"}),
                encoding="utf-8",
            )
            link = cells_path / "linked.json"
            try:
                link.symlink_to(external)
            except OSError as exc:
                self.skipTest(f"symlink creation is unavailable: {exc}")

            with self.assertRaisesRegex(ValueError, "unsafe cell artifact path"):
                load_completed_cells(phase_path)

    def test_resume_validation_rejects_symlinked_prediction_artifact(self) -> None:
        with tempfile.TemporaryDirectory() as temporary:
            root = Path(temporary)
            predictions = root / "predictions"
            cells = root / "cells"
            predictions.mkdir()
            cells.mkdir()
            prediction_target = predictions / "target.jsonl"
            prediction_target.write_text("{}\n", encoding="utf-8")
            prediction_link = predictions / "linked.jsonl"
            try:
                prediction_link.symlink_to(prediction_target)
            except OSError as exc:
                self.skipTest(f"symlink creation is unavailable: {exc}")

            descriptor = {
                "cell_id": "cell-a",
                "cell_identity": "sha256:cell",
                "runner_protocol": "academic-runner-v2",
                "config_identity": "sha256:config",
                "dataset_key": "dataset-a",
                "dataset": "dataset-a",
                "model": "model-a",
                "seed": 1,
                "deterministic": False,
                "phase": "confirmatory",
                "seed_position": 1,
                "batch_id": "batch-01",
                "batch_position": 1,
                "schedule_kind": "fixed-nonadaptive-confirmatory-seeds",
                "schedule_identity": "sha256:schedule",
                "validation_role_assignment_identity": "sha256:validation",
            }
            cell = {
                **descriptor,
                "schema_version": "academic-cell-result-v2",
                "status": "complete",
                "evidence_origin": "official_native",
                "numeric_authority": {"accountability_outcome": "accountable"},
                "blind_test_gate": {
                    "calibration_frozen_before_test_scoring": True,
                    "test_truth_used_for_fit_preprocessing_stopping_or_calibration": False,
                },
                "numerical_core_identity": "sha256:core",
                "predictions_artifact": {
                    "path": str(prediction_link),
                    "sha256": file_sha256(prediction_target),
                    "rows": 1,
                },
            }
            cell_path = cells / "cell-a.json"
            cell_path.write_text(json.dumps(cell), encoding="utf-8")
            config = {"schema_version": CONFIG_SCHEMA_V2}

            with patch.object(
                academic_runner,
                "_numerical_core_manifest",
                return_value={"identity": "sha256:core"},
            ), self.assertRaisesRegex(ValueError, "must not be a symlink"):
                academic_runner._validate_resume_artifact(
                    cell,
                    descriptor=descriptor,
                    cell_path=cell_path,
                    predictions_dir=predictions,
                    config=config,
                    project_root=root,
                )

    def test_analysis_input_identity_binds_full_cells_and_planned_matrix(self) -> None:
        cells = [{"cell_id": "cell-a", "metric": 0.5, "artifact_path": "A"}]
        plan = {"config_identity": "sha256:config", "cells": [{"seed": 1}]}
        original = academic_runner.analysis_input_identity(cells, plan)

        relocated = [{**cells[0], "artifact_path": "B"}]
        changed_cell = [{**cells[0], "metric": 0.6}]
        changed_plan = {**plan, "cells": [{"seed": 2}]}
        self.assertEqual(
            original, academic_runner.analysis_input_identity(relocated, plan)
        )
        self.assertNotEqual(
            original, academic_runner.analysis_input_identity(changed_cell, plan)
        )
        self.assertNotEqual(
            original, academic_runner.analysis_input_identity(cells, changed_plan)
        )


class AcademicRepeatedAnalysisTests(unittest.TestCase):
    def test_analysis_aggregates_trials_plans_repetitions_and_pairs_models(self) -> None:
        with tempfile.TemporaryDirectory() as temporary:
            config = _config(Path(temporary))
            statistics = config["statistical_protocol"]
            statistics["minimum_stochastic_trials"] = 3  # type: ignore[index]
            statistics["maximum_stochastic_trials"] = 9  # type: ignore[index]
            statistics["target_ci_half_width"] = 0.01  # type: ignore[index]
            cells = [
                _analysis_cell("fixed", 11, 0.70, deterministic=True),
                _analysis_cell("stochastic", 11, 0.60, deterministic=False),
                _analysis_cell("stochastic", 22, 0.80, deterministic=False),
                _analysis_cell("stochastic", 33, 0.70, deterministic=False),
            ]

            analysis = analyze_completed_cells(config, cells, phase="pilot")

        fixed = analysis["groups"]["synthetic/fixed"]
        stochastic = analysis["groups"]["synthetic/stochastic"]
        comparison = analysis["paired_comparisons"]["synthetic/fixed-vs-stochastic"]
        self.assertEqual(fixed["trial_count"], 1)
        self.assertEqual(fixed["repetition_plan"]["recommended_total_trials"], 1)
        self.assertIn("deterministic fit", fixed["repetition_plan"]["reason"])
        self.assertEqual(stochastic["trial_count"], 3)
        self.assertEqual(stochastic["metrics"]["auroc"]["n"], 3)
        self.assertAlmostEqual(stochastic["metrics"]["auroc"]["mean"], 0.7)
        self.assertEqual(stochastic["repetition_plan"]["recommended_total_trials"], 9)
        self.assertEqual(comparison["paired_trials"], 0)
        self.assertEqual(comparison["method"], "descriptive difference only")
        self.assertEqual(comparison["status"], "descriptive-only")
        self.assertIn("deterministic", comparison["undefined"])
        self.assertIn("p_value", comparison)
        self.assertIn("holm_adjusted_p_value", comparison)
        self.assertEqual(analysis["primary_metric"], "auroc")


if __name__ == "__main__":
    unittest.main()
