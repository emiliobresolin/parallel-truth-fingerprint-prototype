"""Artifact-reporting and command-line tests for the academic pipeline."""

from __future__ import annotations

import copy
from contextlib import redirect_stderr, redirect_stdout
import csv
from io import StringIO
import json
from pathlib import Path
from types import SimpleNamespace
import tempfile
import unittest
from unittest.mock import patch

from parallel_truth_fingerprint.lstm_service.offline_training import academic_report
from parallel_truth_fingerprint.lstm_service.offline_training.academic_report import (
    build_academic_report,
)
from parallel_truth_fingerprint.lstm_service.offline_training.academic_runner import (
    CONFIG_SCHEMA,
    academic_paths,
)
from scripts import run_academic_experiments as academic_cli


def _config(output_root: Path) -> dict[str, object]:
    return {
        "schema_version": CONFIG_SCHEMA,
        "experiment_id": "synthetic-report-test",
        "output_root": str(output_root),
        "pilot_seeds": [7, 13],
        "confirmatory_seeds": [101, 103],
        "statistical_protocol": {
            "primary_metric": "auroc",
            "reported_metrics": ["f1", "balanced_accuracy", "mcc", "auroc", "auprc"],
            "confidence_level": 0.95,
            "bootstrap_replicates": 20,
            "target_ci_half_width": 0.05,
            "minimum_stochastic_trials": 2,
            "maximum_stochastic_trials": 6,
            "comparison_seed": 29,
            "permutation_replicates": 100,
            "threshold": {"method": "target-fpr", "target_fpr": 0.05},
        },
        "datasets": {
            "synthetic": {
                "models": {
                    "fixed": {"deterministic": True},
                    "stochastic": {"deterministic": False},
                }
            }
        },
    }


def _completed_cell(
    model: str,
    seed: int,
    *,
    deterministic: bool,
    auroc: float,
) -> dict[str, object]:
    f1 = auroc - 0.1
    return {
        "schema_version": "academic-cell-result-v1",
        "cell_id": f"synthetic__{model}__seed-{seed}",
        "cell_identity": f"sha256:{model}-{seed}",
        "status": "complete",
        "dataset": "synthetic",
        "model": model,
        "seed": seed,
        "deterministic": deterministic,
        "threshold_calibration": {
            "method": "target-fpr",
            "value": 0.5,
            "objective_value": 0.05,
            "validation_support": {"total": 10, "normal": 10, "attack": 0},
        },
        "test": {
            "operating": {
                "support": {"total": 20, "normal": 10, "attack": 10},
                "f1": f1,
                "balanced_accuracy": auroc - 0.05,
                "mcc": auroc - 0.2,
                "false_positive_rate": 0.1,
                "false_negative_rate": 0.2,
            },
            "ranking": {"auroc": auroc, "auprc": auroc - 0.02},
            "bootstrap_unit_ci": {
                "f1": {"estimate": f1, "low": f1 - 0.1, "high": f1 + 0.1}
            },
            "per_attack_class": {
                "Attack-A": {
                    "support": {"total": 15, "normal": 10, "attack": 5},
                    "recall": 0.8,
                    "precision": 0.75,
                    "f1": 0.774193548,
                    "auroc": auroc,
                }
            },
            "events": {
                "event_count": 5,
                "detected_event_count": 4,
                "event_recall": 0.8,
                "false_alert_unit_count": 1,
            },
            "curves": {
                "roc": [
                    {"threshold": 1.0, "false_positive_rate": 0.0, "true_positive_rate": 0.0},
                    {"threshold": 0.5, "false_positive_rate": 0.1, "true_positive_rate": 0.8},
                    {"threshold": 0.0, "false_positive_rate": 1.0, "true_positive_rate": 1.0},
                ],
                "precision_recall": [
                    {"threshold": 1.0, "recall": 0.0, "precision": 1.0},
                    {"threshold": 0.5, "recall": 0.8, "precision": 0.75},
                    {"threshold": 0.0, "recall": 1.0, "precision": 0.5},
                ],
            },
        },
    }


def _write_phase_artifacts(
    config: dict[str, object], project_root: Path, phase: str
) -> list[dict[str, object]]:
    paths = academic_paths(config, project_root=project_root, phase=phase)
    paths.cells.mkdir(parents=True, exist_ok=True)
    if phase == "pilot":
        cells = [
            _completed_cell("fixed", 7, deterministic=True, auroc=0.80),
            _completed_cell("stochastic", 7, deterministic=False, auroc=0.75),
            _completed_cell("stochastic", 13, deterministic=False, auroc=0.85),
        ]
    else:
        cells = [
            _completed_cell("fixed", 101, deterministic=True, auroc=0.82),
            _completed_cell("stochastic", 101, deterministic=False, auroc=0.78),
            _completed_cell("stochastic", 103, deterministic=False, auroc=0.86),
        ]
    for cell in cells:
        (paths.cells / f"{cell['cell_id']}.json").write_text(
            json.dumps(cell), encoding="utf-8"
        )
    preflight = {
        "schema_version": "academic-preflight-v1",
        "ready": True,
        "datasets": {
            "synthetic": {
                "status": "ready",
                "support": {
                    "train": {"units": 10, "normal": 10, "attack": 0},
                    "validation": {"units": 10, "normal": 10, "attack": 0},
                    "test": {"units": 20, "normal": 10, "attack": 10},
                },
                "group_leakage_audit": {"passed": True, "group_overlap_count": 0},
                "window_parentage_audit": {"passed": True, "violations": []},
            }
        },
    }
    paths.phase.mkdir(parents=True, exist_ok=True)
    (paths.phase / "preflight.json").write_text(json.dumps(preflight), encoding="utf-8")
    (paths.phase / "run-summary.json").write_text(
        json.dumps({"failed": [], "complete_cell_count": len(cells)}), encoding="utf-8"
    )
    return cells


def _v2_admission_fixture(
    output_root: Path,
) -> tuple[
    dict[str, object],
    list[dict[str, object]],
    dict[str, object],
    dict[str, object],
    dict[str, object],
    dict[str, object],
    list[dict[str, object]],
]:
    config = _config(output_root)
    config["schema_version"] = "thesis-evaluation-config-v2"
    config["confirmatory_seeds"] = list(range(10001, 10051))
    config["execution_protocol"] = {
        "confirmatory_batch_size": 10,
        "seed_schedule_policy": "all-configured-seeds-in-order",
        "interim_analysis_policy": "withheld-until-full-matrix-authenticated",
    }
    config["datasets"]["synthetic"]["models"] = {  # type: ignore[index]
        "stochastic": {"deterministic": False}
    }
    identity = academic_report.config_identity(config)
    schedule_identity = academic_report._expected_schedule_identity(
        config, "confirmatory"
    )
    assert schedule_identity is not None
    planned_rows = academic_report._expected_logical_cells(config, "confirmatory")
    cells: list[dict[str, object]] = []
    for row in planned_rows:
        cell = _completed_cell(
            "stochastic", int(row["seed"]), deterministic=False, auroc=0.78
        )
        cell.update(
            {
                **row,
                "schema_version": "academic-cell-result-v2",
                "phase": "confirmatory",
                "config_identity": identity,
                "evidence_origin": "official_native",
                "numeric_authority": {"accountability_outcome": "accountable"},
                "blind_test_gate": {
                    "calibration_frozen_before_test_scoring": True,
                    "test_truth_used_for_fit_preprocessing_stopping_or_calibration": False,
                },
            }
        )
        cells.append(cell)
    planned_matrix = {
        "schema_version": "academic-logical-plan-v2",
        "phase": "confirmatory",
        "config_identity": identity,
        "schedule_identity": schedule_identity,
        "execution_schedule_adaptive": False,
        "planning_error": None,
        "cells": planned_rows,
    }
    budget = {
        "projection_complete": True,
        "projected_total_cpu_hours_conservative": 8.0,
        "ask_first_cpu_hours": 12.0,
        "over_budget_authorized": False,
        "eligibility_authorized": True,
        "projected_preflight_invocations": 6,
        "confirmatory_preflight_invocations": 6,
        "confirmatory_standalone_preflight_invocations": 1,
        "confirmatory_batch_preflight_invocations": 5,
    }
    preflight = {
        "schema_version": "academic-preflight-v2",
        "phase": "confirmatory",
        "config_identity": identity,
        "ready": True,
        "numeric_authority": {"accountability_outcome": "accountable"},
        "phase_allocation_audit": {"passed": True},
        "computational_load": dict(budget),
    }
    flags = {
        "exact_matrix_match": True,
        "prediction_artifacts_verified": True,
        "raw_evidence_reconstructed": True,
        "core_manifest_verified": True,
        "numeric_authority_accountable": True,
        "evidence_origins_valid": True,
        "phase_disjointness_passed": True,
        "validation_roles_disjoint": True,
        "repetition_planning_authenticated": True,
        "schema_versions_valid": True,
        "primary_outcomes_complete": True,
        "computational_budget_authorized": True,
        "confirmatory_batch_ledger_verified": True,
    }
    cell_ids = [str(cell["cell_id"]) for cell in cells]
    batch_ledger = academic_report.confirmatory_batch_ledger(config)
    batch_progress = [
        {
            "batch_id": f"batch-{index:02d}",
            "expected_cell_count": 10,
            "authenticated_complete_cell_count": 10,
            "complete": True,
        }
        for index in range(1, 6)
    ]
    run_summary = {
        "schema_version": "academic-run-summary-v2",
        "phase": "confirmatory",
        "config_identity": identity,
        "computational_budget": dict(budget),
        "batch_progress": batch_progress,
        "confirmatory_batch_ledger_identity": academic_report.canonical_json_hash(
            batch_ledger
        ),
        "analysis_input_identity": academic_report.analysis_input_identity(
            cells, planned_matrix
        ),
        "eligibility_gate": {
            "eligible": True,
            "phase": "confirmatory",
            "config_identity": identity,
            "planned_cell_ids": cell_ids,
            "authenticated_complete_cell_ids": cell_ids,
            "retained_failure_count": 0,
            **flags,
        },
    }
    run_summary["analysis"] = {
        "analysis_input_identity": run_summary["analysis_input_identity"],
        "planned_matrix_identity": academic_report.canonical_json_hash(planned_matrix),
    }
    integrity_rows = [
        {"cell id": cell["cell_id"], "status": "pass"} for cell in cells
    ]
    return (
        config,
        cells,
        preflight,
        run_summary,
        planned_matrix,
        batch_ledger,
        integrity_rows,
    )


class AcademicReportTests(unittest.TestCase):
    def test_report_emits_nonselective_markdown_csv_and_svg_artifacts(self) -> None:
        with tempfile.TemporaryDirectory() as temporary:
            root = Path(temporary)
            config = _config(root / "evidence")
            _write_phase_artifacts(config, root, "pilot")

            report_path = build_academic_report(config, project_root=root, phase="pilot")
            paths = academic_paths(config, project_root=root, phase="pilot")
            markdown = report_path.read_text(encoding="utf-8")
            per_run_path = paths.reports / "pilot-per-run-metrics.csv"
            aggregate_path = paths.reports / "pilot-aggregate-metrics.csv"
            per_class_path = paths.reports / "pilot-per-class-metrics.csv"
            with per_run_path.open(encoding="utf-8", newline="") as handle:
                per_run_rows = list(csv.DictReader(handle))
            with aggregate_path.open(encoding="utf-8", newline="") as handle:
                aggregate_rows = list(csv.DictReader(handle))
            with per_class_path.open(encoding="utf-8", newline="") as handle:
                per_class_rows = list(csv.DictReader(handle))
            figures = sorted((paths.reports / "pilot-figures").glob("*.svg"))
            figure_texts = [figure.read_text(encoding="utf-8") for figure in figures]

        self.assertIn("EXPLORATORY PILOT", markdown)
        self.assertIn("Every completed run", markdown)
        self.assertIn("Threshold calibration and anomaly scores", markdown)
        self.assertIn("Paired comparisons", markdown)
        self.assertIn("Repetition planning", markdown)
        self.assertIn("synthetic / fixed", markdown)
        self.assertEqual(len(per_run_rows), 3)
        self.assertEqual(len(aggregate_rows), 2)
        self.assertEqual(len(per_class_rows), 3)
        self.assertEqual({row["model"] for row in per_run_rows}, {"fixed", "stochastic"})
        self.assertEqual(len(figures), 3)
        for text in figure_texts:
            self.assertTrue(text.startswith('<svg xmlns="http://www.w3.org/2000/svg"'))
            self.assertIn("</svg>", text)

    def test_file_count_alone_cannot_mark_confirmatory_matrix_eligible(self) -> None:
        with tempfile.TemporaryDirectory() as temporary:
            root = Path(temporary)
            config = _config(root / "evidence")
            _write_phase_artifacts(config, root, "confirmatory")

            report_path = build_academic_report(
                config, project_root=root, phase="confirmatory"
            )
            markdown = report_path.read_text(encoding="utf-8")

        self.assertIn("INCOMPLETE — NOT ELIGIBLE FOR FINAL CLAIMS", markdown)
        self.assertIn("Numeric-authority closure: `missing`", markdown)
        self.assertIn("prediction artifact is missing", markdown)
        self.assertNotIn("EXPLORATORY PILOT", markdown)

    def test_incomplete_v2_confirmatory_report_withholds_all_outcome_surfaces(self) -> None:
        with tempfile.TemporaryDirectory() as temporary:
            root = Path(temporary)
            config = _config(root / "evidence")
            config["schema_version"] = "thesis-evaluation-config-v2"
            _write_phase_artifacts(config, root, "confirmatory")
            paths = academic_paths(config, project_root=root, phase="confirmatory")
            stale_figure = paths.reports / "confirmatory-figures" / "stale.svg"
            stale_figure.parent.mkdir(parents=True, exist_ok=True)
            stale_figure.write_text("stale outcome figure", encoding="utf-8")

            report_path = build_academic_report(
                config, project_root=root, phase="confirmatory"
            )
            markdown = report_path.read_text(encoding="utf-8")
            per_run = (paths.reports / "confirmatory-per-run-metrics.csv").read_text(
                encoding="utf-8"
            )
            figures = list((paths.reports / "confirmatory-figures").glob("*.svg"))
            stale_removed = not stale_figure.exists()

        self.assertIn("OUTCOME ANALYSIS WITHHELD", markdown)
        self.assertIn("integrity and failure metadata only", markdown)
        self.assertNotIn("Every completed run", markdown)
        self.assertNotIn("Aggregate results", markdown)
        self.assertEqual(per_run.strip(), "no_rows")
        self.assertEqual(figures, [])
        self.assertTrue(stale_removed)

    def test_report_rejects_symlinked_report_directory(self) -> None:
        with tempfile.TemporaryDirectory() as temporary:
            root = Path(temporary)
            config = _config(root / "evidence")
            _write_phase_artifacts(config, root, "pilot")
            paths = academic_paths(config, project_root=root, phase="pilot")
            external = root / "external-reports"
            external.mkdir()
            paths.reports.parent.mkdir(parents=True, exist_ok=True)
            try:
                paths.reports.symlink_to(external, target_is_directory=True)
            except OSError as exc:
                self.skipTest(f"symlink creation is unavailable: {exc}")

            with self.assertRaisesRegex(RuntimeError, "report directory symlink"):
                build_academic_report(config, project_root=root, phase="pilot")

    def test_report_rejects_preexisting_output_symlink(self) -> None:
        with tempfile.TemporaryDirectory() as temporary:
            root = Path(temporary)
            config = _config(root / "evidence")
            _write_phase_artifacts(config, root, "pilot")
            paths = academic_paths(config, project_root=root, phase="pilot")
            paths.reports.mkdir(parents=True, exist_ok=True)
            external = root / "external.csv"
            external.write_text("do not overwrite", encoding="utf-8")
            output_link = paths.reports / "pilot-per-run-metrics.csv"
            try:
                output_link.symlink_to(external)
            except OSError as exc:
                self.skipTest(f"symlink creation is unavailable: {exc}")

            with self.assertRaisesRegex(RuntimeError, "report output symlink"):
                build_academic_report(config, project_root=root, phase="pilot")
            self.assertEqual(external.read_text(encoding="utf-8"), "do not overwrite")

    def test_progress_report_sanitizes_batch_and_failure_metadata(self) -> None:
        config = _config(Path("evidence"))
        report = academic_report._render_confirmatory_progress_markdown(
            config,
            cells=[],
            preflight={},
            run_summary={
                "batch_progress": [
                    {
                        "batch_id": "batch-01",
                        "expected_cell_count": 10,
                        "authenticated_complete_cell_count": 3,
                        "complete": False,
                        "interim_auroc": "SECRET_OUTCOME",
                    }
                ]
            },
            retained_failures=[
                {
                    "schema_version": "academic-cell-failure-v2",
                    "phase": "confirmatory",
                    "dataset": "synthetic",
                    "model": "stochastic",
                    "seed": 101,
                    "error_type": "SECRET_EXCEPTION_TYPE",
                    "error": "SECRET_EXCEPTION_AND_OUTCOME_CONTEXT",
                    "resolution_status": "unresolved",
                }
            ],
            integrity_rows=[],
            eligibility={
                "reasons": ["still incomplete"],
                "batch_progress": [
                    {
                        "batch_id": "batch-01",
                        "expected_cell_count": 10,
                        "authenticated_complete_cell_count": 3,
                        "complete": False,
                    }
                ],
            },
        )

        self.assertIn("batch-01", report)
        self.assertIn('"dataset": "synthetic"', report)
        self.assertNotIn("SECRET_OUTCOME", report)
        self.assertNotIn("SECRET_EXCEPTION_TYPE", report)
        self.assertNotIn("SECRET_EXCEPTION_AND_OUTCOME_CONTEXT", report)

    def test_v2_eligibility_recomputes_artifact_admission_boundaries(self) -> None:
        fixture = _v2_admission_fixture(Path("evidence"))
        (
            config,
            cells,
            preflight,
            run_summary,
            planned_matrix,
            batch_ledger,
            integrity_rows,
        ) = fixture

        def audit(
            *,
            current_cells: list[dict[str, object]] | None = None,
            current_preflight: dict[str, object] | None = None,
            current_summary: dict[str, object] | None = None,
            current_plan: dict[str, object] | None = None,
            current_ledger: dict[str, object] | None = None,
            failures: list[dict[str, object]] | None = None,
        ) -> dict[str, object]:
            return academic_report._eligibility_audit(
                config,
                phase="confirmatory",
                cells=current_cells if current_cells is not None else cells,
                preflight=current_preflight if current_preflight is not None else preflight,
                run_summary=current_summary if current_summary is not None else run_summary,
                planned_matrix=current_plan if current_plan is not None else planned_matrix,
                batch_ledger=(
                    current_ledger if current_ledger is not None else batch_ledger
                ),
                retained_failures=failures if failures is not None else [],
                integrity_rows=integrity_rows,
            )

        self.assertTrue(audit()["eligible"])

        tampered_cells = copy.deepcopy(cells)
        tampered_cells[0]["test"]["ranking"]["auroc"] = 0.99  # type: ignore[index]
        tampered_result = audit(current_cells=tampered_cells)
        self.assertFalse(tampered_result["eligible"])
        self.assertIn("full current cell contents", " ".join(tampered_result["reasons"]))

        mismatched_plan = copy.deepcopy(planned_matrix)
        mismatched_plan["cells"][0]["batch_position"] = 2  # type: ignore[index]
        plan_result = audit(current_plan=mismatched_plan)
        self.assertFalse(plan_result["eligible"])
        self.assertIn("frozen logical schedule", " ".join(plan_result["reasons"]))

        unresolved_result = audit(
            failures=[
                {
                    "dataset": "synthetic",
                    "model": "stochastic",
                    "seed": 999,
                    "resolution_status": "unresolved",
                }
            ]
        )
        self.assertFalse(unresolved_result["eligible"])
        self.assertIn("independently unresolved", " ".join(unresolved_result["reasons"]))

        unauthorized_summary = copy.deepcopy(run_summary)
        unauthorized_summary["computational_budget"].update(  # type: ignore[union-attr]
            {
                "projected_total_cpu_hours_conservative": 13.0,
                "over_budget_authorized": False,
            }
        )
        unauthorized_preflight = copy.deepcopy(preflight)
        unauthorized_preflight["computational_load"].update(  # type: ignore[union-attr]
            {"projected_total_cpu_hours_conservative": 13.0}
        )
        budget_result = audit(
            current_preflight=unauthorized_preflight,
            current_summary=unauthorized_summary,
        )
        self.assertFalse(budget_result["eligible"])
        self.assertIn("without authorization", " ".join(budget_result["reasons"]))

        incomplete_summary = copy.deepcopy(run_summary)
        incomplete_summary["computational_budget"]["projection_complete"] = False  # type: ignore[index]
        incomplete_result = audit(current_summary=incomplete_summary)
        self.assertFalse(incomplete_result["eligible"])
        self.assertIn("complete finite", " ".join(incomplete_result["reasons"]))

        wrong_preflight = copy.deepcopy(preflight)
        wrong_preflight["config_identity"] = "sha256:wrong"
        identity_result = audit(current_preflight=wrong_preflight)
        self.assertFalse(identity_result["eligible"])
        self.assertIn("preflight", " ".join(identity_result["reasons"]))

        tampered_ledger = copy.deepcopy(batch_ledger)
        tampered_ledger["batch_size"] = 9
        ledger_result = audit(current_ledger=tampered_ledger)
        self.assertFalse(ledger_result["eligible"])
        self.assertIn("batch ledger", " ".join(ledger_result["reasons"]))

        stale_progress = copy.deepcopy(run_summary)
        stale_progress["batch_progress"][0][  # type: ignore[index]
            "authenticated_complete_cell_count"
        ] = 9
        progress_result = audit(current_summary=stale_progress)
        self.assertFalse(progress_result["eligible"])
        self.assertIn("batch progress", " ".join(progress_result["reasons"]))

    def test_per_run_rows_expose_cluster_interval_failure_reason(self) -> None:
        cell = _completed_cell(
            "stochastic", 101, deterministic=False, auroc=0.80
        )
        cell["test"]["bootstrap_unit_ci"]["design"] = {  # type: ignore[index]
            "resampling_unit": "declared independent cluster",
            "independent_cluster_count": 2,
            "minimum_clusters_required": 5,
            "inferentially_valid": False,
            "undefined_reason": "at least 5 independent clusters are required; observed 2",
            "qualification": "whole recordings only",
        }

        row = academic_report._per_run_rows([cell])[0]

        self.assertEqual(row["independent clusters"], 2)
        self.assertEqual(row["minimum clusters required"], 5)
        self.assertFalse(row["cluster interval valid"])
        self.assertIn("observed 2", row["cluster interval undefined reason"])


class AcademicCliTests(unittest.TestCase):
    def _write_config(self, root: Path) -> Path:
        path = root / "config.json"
        path.write_text(json.dumps(_config(root / "output")), encoding="utf-8")
        return path

    def test_all_command_routes_filters_through_each_stage(self) -> None:
        with tempfile.TemporaryDirectory() as temporary:
            root = Path(temporary)
            config_path = self._write_config(root)
            report_path = root / "report.md"
            stdout = StringIO()
            with patch.object(
                academic_cli, "run_preflight", return_value={"ready": True}
            ) as preflight, patch.object(
                academic_cli,
                "run_academic_phase",
                return_value={
                    "planned_cell_count": 1,
                    "completed_now": ["cell"],
                    "resumed": [],
                    "failed": [],
                },
            ) as run, patch.object(
                academic_cli, "build_academic_report", return_value=report_path
            ) as report, patch.object(
                academic_cli,
                "academic_paths",
                return_value=SimpleNamespace(root=root / "evidence-root"),
            ), redirect_stdout(stdout):
                result = academic_cli.main(
                    [
                        "all",
                        "--config",
                        str(config_path),
                        "--phase",
                        "pilot",
                        "--dataset",
                        "synthetic",
                        "--model",
                        "fixed",
                    ]
                )

        self.assertEqual(result, 0)
        self.assertEqual(preflight.call_count, 1)
        self.assertEqual(run.call_args.kwargs["dataset_filter"], ["synthetic"])
        self.assertEqual(run.call_args.kwargs["model_filter"], ["fixed"])
        self.assertEqual(report.call_count, 1)
        self.assertIn('"preflight_ready": true', stdout.getvalue())
        self.assertIn('"completed_now": 1', stdout.getvalue())
        self.assertIn(str(report_path), stdout.getvalue())

    def test_failed_preflight_stops_all_before_execution(self) -> None:
        with tempfile.TemporaryDirectory() as temporary:
            root = Path(temporary)
            config_path = self._write_config(root)
            stderr = StringIO()
            with patch.object(
                academic_cli, "run_preflight", return_value={"ready": False}
            ), patch.object(academic_cli, "run_academic_phase") as run, patch.object(
                academic_cli, "build_academic_report"
            ) as report, redirect_stderr(stderr):
                result = academic_cli.main(["all", "--config", str(config_path)])

        self.assertEqual(result, 2)
        run.assert_not_called()
        report.assert_not_called()
        self.assertIn("No experiment cells were run", stderr.getvalue())

    def test_v2_confirmatory_all_is_rejected_before_preflight(self) -> None:
        config = {
            "schema_version": "thesis-evaluation-config-v2",
            "experiment_id": "v2-cli-test",
        }
        stderr = StringIO()
        with patch.object(
            academic_cli, "load_academic_config", return_value=config
        ), patch.object(academic_cli, "run_preflight") as preflight, redirect_stderr(stderr):
            result = academic_cli.main(["all", "--phase", "confirmatory"])

        self.assertEqual(result, 5)
        preflight.assert_not_called()
        self.assertIn("cannot use 'all'", stderr.getvalue())

    def test_all_builds_failure_report_before_returning_nonzero(self) -> None:
        with tempfile.TemporaryDirectory() as temporary:
            root = Path(temporary)
            config_path = self._write_config(root)
            report_path = root / "failure-report.md"
            with patch.object(
                academic_cli, "run_preflight", return_value={"ready": True}
            ), patch.object(
                academic_cli,
                "run_academic_phase",
                return_value={
                    "planned_cell_count": 1,
                    "completed_now": [],
                    "resumed": [],
                    "failed": [{"error": "synthetic failure"}],
                },
            ), patch.object(
                academic_cli, "build_academic_report", return_value=report_path
            ) as report, patch.object(
                academic_cli,
                "academic_paths",
                return_value=SimpleNamespace(root=root / "evidence-root"),
            ), redirect_stdout(StringIO()):
                result = academic_cli.main(["all", "--config", str(config_path)])

        self.assertEqual(result, 3)
        report.assert_called_once()

    def test_ignored_report_filters_are_rejected_before_report_build(self) -> None:
        with tempfile.TemporaryDirectory() as temporary:
            root = Path(temporary)
            config_path = self._write_config(root)
            with patch.object(academic_cli, "build_academic_report") as report, redirect_stderr(
                StringIO()
            ):
                result = academic_cli.main(
                    ["report", "--config", str(config_path), "--dataset", "synthetic"]
                )

        self.assertEqual(result, 5)
        report.assert_not_called()

    def test_run_command_returns_nonzero_when_any_cell_fails(self) -> None:
        with tempfile.TemporaryDirectory() as temporary:
            root = Path(temporary)
            config_path = self._write_config(root)
            with patch.object(
                academic_cli,
                "run_academic_phase",
                return_value={
                    "planned_cell_count": 1,
                    "completed_now": [],
                    "resumed": [],
                    "failed": [{"error": "synthetic failure"}],
                },
            ), redirect_stdout(StringIO()):
                result = academic_cli.main(["run", "--config", str(config_path)])

        self.assertEqual(result, 3)

    def test_v2_confirmatory_requires_one_seed_batch_and_forbids_filters(self) -> None:
        config = {
            "schema_version": "thesis-evaluation-config-v2",
            "experiment_id": "v2-cli-test",
        }
        with patch.object(academic_cli, "load_academic_config", return_value=config), redirect_stderr(
            StringIO()
        ):
            missing = academic_cli.main(["confirmatory"])
            filtered = academic_cli.main(
                ["confirmatory", "--seed-batch", "1", "--dataset", "adfa-ld"]
            )

        self.assertEqual(missing, 5)
        self.assertEqual(filtered, 5)

    def test_over_budget_switch_does_not_waive_missing_projection(self) -> None:
        with tempfile.TemporaryDirectory() as temporary:
            root = Path(temporary)
            config = {
                "schema_version": "thesis-evaluation-config-v2",
                "experiment_id": "v2-cli-test",
            }
            paths = SimpleNamespace(root=root / "root", phase=root / "confirmatory")
            with patch.object(
                academic_cli, "load_academic_config", return_value=config
            ), patch.object(
                academic_cli, "academic_paths", return_value=paths
            ), patch.object(
                academic_cli, "run_academic_phase"
            ) as run, redirect_stderr(StringIO()):
                result = academic_cli.main(
                    [
                        "confirmatory",
                        "--seed-batch",
                        "1",
                        "--allow-over-budget",
                    ]
                )

        self.assertEqual(result, 4)
        run.assert_not_called()


if __name__ == "__main__":
    unittest.main()
