"""Human- and machine-readable reporting for academic experiment artifacts."""

from __future__ import annotations

import csv
from datetime import datetime, timezone
import html
import json
import math
import os
from pathlib import Path
import tempfile
from typing import Mapping, Sequence

from parallel_truth_fingerprint.lstm_service.offline_training.academic_metrics import (
    binary_operating_metrics,
)
from parallel_truth_fingerprint.lstm_service.offline_training.academic_runner import (
    _recover_cell_transactions,
    _validate_publication_transaction,
    academic_paths,
    analysis_input_identity,
    analyze_completed_cells,
    confirmatory_batch_ledger,
    config_identity,
    load_completed_cells,
    validate_cell_raw_reconstruction,
    V2_CONFIRMATORY_BATCH_COUNT,
    V2_CONFIRMATORY_PREFLIGHT_INVOCATIONS,
    V2_CONFIRMATORY_STANDALONE_PREFLIGHT_INVOCATIONS,
)
from parallel_truth_fingerprint.lstm_service.offline_training.academic_protocol import (
    canonical_json_hash,
    file_sha256,
)


def build_academic_report(
    config: Mapping[str, object], *, project_root: Path, phase: str
) -> Path:
    """Build a non-selective report: every completed and failed cell is visible."""

    paths = academic_paths(config, project_root=project_root, phase=phase)
    _assert_safe_artifact_path(paths.root, paths.phase, "phase directory")
    if (
        config.get("schema_version") == "thesis-evaluation-config-v2"
        and paths.transactions.is_dir()
    ):
        _recover_cell_transactions(paths)
    _prepare_report_directory(paths.root, paths.reports)
    figures = paths.reports / f"{phase}-figures"
    _prepare_report_directory(paths.root, figures)
    cells = load_completed_cells(paths.phase)
    preflight = _optional_json(paths.phase / "preflight.json")
    run_summary = _optional_json(paths.phase / "run-summary.json")
    planned_matrix = _optional_json(paths.phase / "planned-matrix.json")
    batch_ledger = _optional_json(
        paths.phase / "confirmatory-batch-ledger.json"
    )
    retained_failures = _annotate_failure_resolution(
        _load_retained_failures(paths.phase, run_summary), cells
    )
    custom_audit = _audit_custom_campaign(project_root)
    integrity_rows = _artifact_integrity_rows(cells, config=config)
    eligibility = _eligibility_audit(
        config,
        phase=phase,
        cells=cells,
        preflight=preflight,
        run_summary=run_summary,
        planned_matrix=planned_matrix,
        batch_ledger=batch_ledger,
        retained_failures=retained_failures,
        integrity_rows=integrity_rows,
    )
    summary_analysis = _as_mapping(run_summary.get("analysis"))
    v2_confirmatory = (
        config.get("schema_version") == "thesis-evaluation-config-v2"
        and phase == "confirmatory"
    )
    confirmatory_analysis_ready = (
        eligibility.get("eligible") is True
        and summary_analysis.get("status") == "complete"
        and summary_analysis.get("outcome_aggregates_emitted") is True
        and run_summary.get("analysis_identity")
        == canonical_json_hash(summary_analysis)
    )
    if v2_confirmatory and not confirmatory_analysis_ready:
        for stale_figure in figures.glob("*.svg"):
            if stale_figure.is_file() or stale_figure.is_symlink():
                stale_figure.unlink()
        empty_rows: list[dict[str, object]] = []
        for name in (
            "per-run-metrics",
            "aggregate-metrics",
            "per-class-metrics",
            "threshold-sensitivity",
            "diagnostics",
        ):
            _write_csv(paths.reports / f"{phase}-{name}.csv", empty_rows)
        _write_csv(paths.reports / f"{phase}-artifact-integrity.csv", integrity_rows)
        _write_text(
            paths.reports / f"{phase}-custom-track-readiness.json",
            json.dumps(custom_audit, indent=2, sort_keys=True, ensure_ascii=False)
            + "\n",
        )
        report = _render_confirmatory_progress_markdown(
            config,
            cells=cells,
            preflight=preflight,
            run_summary=run_summary,
            retained_failures=retained_failures,
            integrity_rows=integrity_rows,
            eligibility=eligibility,
        )
        report_path = paths.reports / f"{phase}-academic-report.md"
        _write_text(report_path, report)
        return report_path

    analysis = (
        summary_analysis
        if confirmatory_analysis_ready
        else analyze_completed_cells(config, cells, phase=phase)
    )

    per_run_rows = _per_run_rows(cells)
    aggregate_rows = _aggregate_rows(analysis, cells)
    per_class_rows = _per_class_rows(cells)
    sensitivity_rows = _threshold_sensitivity_rows(cells, integrity_rows)
    diagnostic_rows = _diagnostic_rows(cells)
    _write_csv(paths.reports / f"{phase}-per-run-metrics.csv", per_run_rows)
    _write_csv(paths.reports / f"{phase}-aggregate-metrics.csv", aggregate_rows)
    _write_csv(paths.reports / f"{phase}-per-class-metrics.csv", per_class_rows)
    _write_csv(
        paths.reports / f"{phase}-threshold-sensitivity.csv", sensitivity_rows
    )
    _write_csv(paths.reports / f"{phase}-diagnostics.csv", diagnostic_rows)
    _write_csv(paths.reports / f"{phase}-artifact-integrity.csv", integrity_rows)
    _write_text(
        paths.reports / f"{phase}-custom-track-readiness.json",
        json.dumps(custom_audit, indent=2, sort_keys=True, ensure_ascii=False) + "\n",
    )

    figure_links: list[tuple[str, str]] = []
    for dataset in sorted({str(cell["dataset"]) for cell in cells}):
        selected = [cell for cell in cells if cell["dataset"] == dataset]
        trial_name = f"{_slug(dataset)}-trial-variation.svg"
        _write_trial_variation_svg(figures / trial_name, dataset, selected)
        figure_links.append((dataset, f"{phase}-figures/{trial_name}"))
        for model in sorted({str(cell["model"]) for cell in selected}):
            representative = min(
                (cell for cell in selected if cell["model"] == model),
                key=lambda cell: int(cell["seed"]),
            )
            curve_name = f"{_slug(dataset)}-{_slug(model)}-curves.svg"
            _write_curve_svg(figures / curve_name, dataset, model, representative)
            figure_links.append((f"{dataset} / {model}", f"{phase}-figures/{curve_name}"))

    report = _render_markdown(
        config,
        phase=phase,
        cells=cells,
        preflight=preflight,
        run_summary=run_summary,
        retained_failures=retained_failures,
        eligibility=eligibility,
        analysis=analysis,
        per_run_rows=per_run_rows,
        aggregate_rows=aggregate_rows,
        per_class_rows=per_class_rows,
        sensitivity_rows=sensitivity_rows,
        diagnostic_rows=diagnostic_rows,
        integrity_rows=integrity_rows,
        figure_links=figure_links,
        project_root=project_root,
        custom_audit=custom_audit,
    )
    report_path = paths.reports / f"{phase}-academic-report.md"
    _write_text(report_path, report)
    return report_path


def _render_confirmatory_progress_markdown(
    config: Mapping[str, object],
    *,
    cells: Sequence[Mapping[str, object]],
    preflight: Mapping[str, object],
    run_summary: Mapping[str, object],
    retained_failures: Sequence[Mapping[str, object]],
    integrity_rows: Sequence[Mapping[str, object]],
    eligibility: Mapping[str, object],
) -> str:
    """Render audit-only progress without exposing interim confirmatory outcomes."""

    progress = eligibility.get("batch_progress", [])
    progress_rows = (
        [
            {
                field: row.get(field)
                for field in (
                    "batch_id",
                    "expected_cell_count",
                    "authenticated_complete_cell_count",
                    "complete",
                )
            }
            for row in progress
            if isinstance(row, Mapping)
        ]
        if isinstance(progress, list)
        else []
    )
    budget = _as_mapping(run_summary.get("computational_budget"))
    if not budget:
        budget = _as_mapping(preflight.get("computational_load"))
    lines = [
        "# Academic evaluation report — confirmatory progress audit",
        "",
        "**Claim status:** INCOMPLETE — OUTCOME ANALYSIS WITHHELD",
        "",
        (
            "The frozen protocol prohibits confirmatory aggregates, comparisons, metric tables, "
            "and figures until every planned cell and prediction artifact in all five batches is "
            "authenticated. This progress report therefore contains integrity and failure metadata only."
        ),
        "",
        "## Progress and admission audit",
        "",
        f"- Experiment: `{config.get('experiment_id')}`",
        f"- Configuration identity: `{config_identity(config)}`",
        f"- Authenticated/available cell artifacts: {len(cells)}",
        f"- Historical failure artifacts retained: {len(retained_failures)}",
        f"- Preflight gate: `{'passed' if preflight.get('ready') is True else 'blocked or absent'}`",
        f"- Numeric-authority closure: `{eligibility.get('numeric_authority', 'missing')}`",
        f"- Evidence-origin closure: `{eligibility.get('evidence_origin', 'blocked')}`",
        f"- Pilot/confirmatory disjointness: `{eligibility.get('phase_disjointness', 'blocked')}`",
        "- Outcome aggregates emitted: `False`",
        "",
        "### Frozen five-batch ledger progress",
        "",
        *_markdown_table(progress_rows),
        "",
        "### Computational-cost gate",
        "",
        f"- Projection complete: `{budget.get('projection_complete')}`",
        (
            "- Confirmatory preflight invocations costed: "
            f"`{budget.get('confirmatory_preflight_invocations')}` total "
            f"(`{budget.get('confirmatory_standalone_preflight_invocations')}` standalone + "
            f"`{budget.get('confirmatory_batch_preflight_invocations')}` batch-local)"
        ),
        (
            "- Conservative full-protocol projection (CPU-h): "
            f"`{_fmt(budget.get('projected_total_cpu_hours_conservative'))}`"
        ),
        f"- Ask-first threshold (CPU-h): `{_fmt(budget.get('ask_first_cpu_hours'))}`",
        f"- Over-budget authorization recorded: `{budget.get('over_budget_authorized', False)}`",
        "",
        "### Artifact integrity (no outcome values)",
        "",
        *_markdown_table(integrity_rows),
        "",
        "### Blocking reasons",
        "",
    ]
    reasons = eligibility.get("reasons", [])
    if isinstance(reasons, list) and reasons:
        lines.extend(f"- {reason}" for reason in reasons)
    else:
        lines.append("- Run-summary analysis is absent or not authenticated as complete.")
    lines.extend(
        [
            "",
            "## Interpretation boundary",
            "",
            (
                "No between-seed estimate, confidence interval, model comparison, or figure may be "
                "interpreted from this document. Batch completion cannot alter the frozen remaining "
                "seed schedule. HAI recording-cluster uncertainty also remains distinct from training-seed "
                "variability; additional seeds cannot create missing independent recordings."
            ),
            "",
        ]
    )
    if retained_failures:
        lines.extend(
            [
                "## Retained failure history",
                "",
                "```json",
                json.dumps(_safe_failure_rows(retained_failures), indent=2, ensure_ascii=False),
                "```",
                "",
            ]
        )
    return "\n".join(lines)


def _render_markdown(
    config: Mapping[str, object],
    *,
    phase: str,
    cells: Sequence[Mapping[str, object]],
    preflight: Mapping[str, object],
    run_summary: Mapping[str, object],
    retained_failures: Sequence[Mapping[str, object]],
    eligibility: Mapping[str, object],
    analysis: Mapping[str, object],
    per_run_rows: Sequence[Mapping[str, object]],
    aggregate_rows: Sequence[Mapping[str, object]],
    per_class_rows: Sequence[Mapping[str, object]],
    sensitivity_rows: Sequence[Mapping[str, object]],
    diagnostic_rows: Sequence[Mapping[str, object]],
    integrity_rows: Sequence[Mapping[str, object]],
    figure_links: Sequence[tuple[str, str]],
    project_root: Path,
    custom_audit: Mapping[str, object],
) -> str:
    failures: object = _safe_failure_rows(retained_failures)
    preflight_ready = preflight.get("ready") is True
    status = (
        "EXPLORATORY PILOT — NOT ELIGIBLE FOR FINAL CLAIMS"
        if phase == "pilot"
        else _confirmatory_status(eligibility)
    )
    budget = _as_mapping(run_summary.get("computational_budget"))
    if not budget:
        budget = _as_mapping(preflight.get("computational_load"))
    lines = [
        f"# Academic evaluation report — {phase}",
        "",
        f"**Claim status:** {status}",
        "",
        (
            "This report retains every planned outcome, calibrates operating thresholds on validation data, "
            "and evaluates the untouched test partition once per frozen cell. It does not select a global "
            "champion across datasets or modalities."
        ),
        "",
        "## Executive audit",
        "",
        f"- Experiment: `{config['experiment_id']}`",
        f"- Configuration identity: `{config_identity(config)}`",
        f"- Phase: `{phase}`",
        f"- Completed cells available: {len(cells)}",
        f"- Retained failed cells: {len(retained_failures)}",
        f"- Preflight gate: {'passed' if preflight_ready else 'not passed or not available'}",
        f"- Full-protocol cost projection complete: `{budget.get('projection_complete')}`",
        (
            (
                "- Confirmatory preflight invocations costed: "
                f"`{budget.get('confirmatory_preflight_invocations')}` total "
                f"(`{budget.get('confirmatory_standalone_preflight_invocations')}` standalone + "
                f"`{budget.get('confirmatory_batch_preflight_invocations')}` batch-local)"
            )
            if phase == "confirmatory"
            else (
                "- Phase preflight invocations costed: "
                f"`{budget.get('projected_preflight_invocations')}`"
            )
        ),
        (
            "- Conservative full-protocol CPU-hours: "
            f"`{_fmt(budget.get('projected_total_cpu_hours_conservative'))}` "
            f"(ask-first threshold `{_fmt(budget.get('ask_first_cpu_hours'))}`)"
        ),
        f"- Over-budget authorization recorded: `{budget.get('over_budget_authorized', False)}`",
        f"- Generated (UTC): {datetime.now(timezone.utc).isoformat().replace('+00:00', 'Z')}",
        "",
    ]
    lines.extend(
        [
            "### Admission and artifact-integrity gate",
            "",
            f"- Exact eligibility result: `{'pass' if eligibility['eligible'] else 'blocked'}`",
            f"- Numeric-authority closure: `{eligibility['numeric_authority']}`",
            f"- Evidence-origin closure: `{eligibility['evidence_origin']}`",
            f"- Pilot/confirmatory disjointness: `{eligibility['phase_disjointness']}`",
            "- Blocking reasons:",
        ]
    )
    eligibility_reasons = eligibility.get("reasons", [])
    if isinstance(eligibility_reasons, list) and eligibility_reasons:
        lines.extend(f"  - {reason}" for reason in eligibility_reasons)
    else:
        lines.append("  - none")
    lines.extend(["", *_markdown_table(integrity_rows), ""])
    if config.get("schema_version") == "thesis-evaluation-config-v1":
        lines.extend(
            [
                "**v1 inference rejection:** HAI block-bootstrap confidence intervals and every "
                "deterministic-involving paired significance/effect row from v1 are retained for audit but "
                "rejected for inference. They must not be cited as thesis evidence.",
                "",
            ]
        )

    legacy = _legacy_audit(config, project_root)
    if legacy:
        lines.extend(
            [
                "### Why the previous matrix cannot support the thesis claim",
                "",
                legacy,
                "",
            ]
        )
    lines.extend(
        [
            "### Controlled custom-track readiness",
            "",
            f"**Status:** {custom_audit.get('status', 'unknown')}",
            "",
            str(custom_audit.get("interpretation", "No custom evidence audit available.")),
            "",
        ]
    )
    custom_rows = custom_audit.get("summary_rows", [])
    lines.extend(_markdown_table(custom_rows if isinstance(custom_rows, list) else []))
    lines.append("")

    lines.extend(
        [
            "## Frozen experimental design",
            "",
            _design_text(config, phase),
            "",
            "### Dataset protocols and sampling limits",
            "",
        ]
    )
    lines.extend(_markdown_table(_protocol_rows(config, phase, cells)))
    lines.extend(["", "### Model and hyperparameter registry", ""])
    lines.extend(_markdown_table(_hyperparameter_rows(config)))
    lines.extend(
        [
            "",
            "### Leakage and support gates",
            "",
        ]
    )
    datasets = preflight.get("datasets", {})
    audit_rows: list[dict[str, object]] = []
    if isinstance(datasets, Mapping):
        for key, value in datasets.items():
            if not isinstance(value, Mapping):
                continue
            support = value.get("support", {})
            leakage = value.get("group_leakage_audit", {})
            parentage = value.get("window_parentage_audit", {})
            audit_rows.append(
                {
                    "dataset": key,
                    "status": value.get("status"),
                    "train units": _nested(support, "train", "units"),
                    "validation units": _nested(support, "validation", "units"),
                    "test normal": _nested(support, "test", "normal"),
                    "test attack": _nested(support, "test", "attack"),
                    "group overlap": _nested(leakage, "group_overlap_count"),
                    "window violations": len(parentage.get("violations", []))
                    if isinstance(parentage, Mapping)
                    else None,
                }
            )
    lines.extend(_markdown_table(audit_rows))
    lines.extend(
        [
            "",
            "The independent unit is a trace/recording for ADFA-LD and LID-DS. HAI point estimates use "
            "non-overlapping temporal blocks, but recording-cluster uncertainty is emitted only when the "
            "declared minimum independent recordings is met; adjacent blocks are never declared independent. "
            "Across-seed intervals are a separate training-variability estimand. Windows are created only after partition assignment. "
            "Preprocessing parameters and categorical vocabulary are fitted on normal training units only.",
            "",
            "## Aggregate results (no winner selection)",
            "",
        ]
    )
    lines.extend(_markdown_table(aggregate_rows))
    for dataset_name in sorted({str(row.get("dataset")) for row in aggregate_rows}):
        lines.extend(["", f"### {dataset_name}: protocol-specific results", ""])
        lines.extend(
            _markdown_table(
                [row for row in aggregate_rows if str(row.get("dataset")) == dataset_name]
            )
        )
    lines.extend(
        [
            "",
            "Across-seed intervals use Student-t uncertainty for genuine independent stochastic trials. A "
            "deterministic model is fitted once and is never copied across seed identifiers. Unit-bootstrap "
            "intervals are conditional on frozen sampled prevalence; cluster-bootstrap intervals preserve "
            "declared recording/event dependence. Display values use six decimals; JSON artifacts retain full precision.",
            "",
            "## Every completed run",
            "",
        ]
    )
    lines.extend(_markdown_table(per_run_rows))
    lines.extend(
        [
            "",
            "## Confusion matrices, score distributions, convergence, and cost",
            "",
            "These diagnostics prevent equal headline metrics from hiding different error modes, score overlap, "
            "optimization histories, or resource costs.",
            "",
        ]
    )
    lines.extend(_markdown_table(diagnostic_rows))
    lines.extend(
        [
            "",
            "## Threshold calibration and anomaly scores",
            "",
            "Thresholds below are frozen from validation scores only. Scores always use the same direction: "
            "larger means more anomalous. Test truth is used only after threshold freezing.",
            "",
        ]
    )
    threshold_rows = [
        {
            "dataset": row.get("dataset"),
            "model": row.get("model"),
            "seed": row.get("seed"),
            "threshold": row.get("threshold"),
            "validation normal": row.get("validation normal"),
            "validation attack": row.get("validation attack"),
            "attained validation FPR": row.get("validation FPR"),
            "test FPR": row.get("FPR"),
            "test FNR": row.get("FNR"),
        }
        for row in per_run_rows
    ]
    lines.extend(_markdown_table(threshold_rows))
    lines.extend(
        [
            "",
            "### Predeclared threshold sensitivity on the blind test set",
            "",
            "Each row applies a threshold that was derived only from a validation-normal quantile. "
            "The test labels are used to evaluate those already-fixed operating points, never to choose one.",
            "",
        ]
    )
    lines.extend(_markdown_table(sensitivity_rows))
    lines.extend(
        [
            "",
            "## Attack-family and event results",
            "",
        ]
    )
    lines.extend(_markdown_table(per_class_rows))
    lines.extend(
        [
            "",
            "## Ablation interpretation",
            "",
            "`categorical-unigram` and `robust-distance` are transparent reference baselines; "
            "`pca-autoencoder` removes non-linearity and recurrence; `recurrent-autoencoder` is the full "
            "sequence reconstruction model. Comparisons are made within each dataset only. A more complex "
            "model is supported only if its uncertainty-aware result and cost justify the difference.",
            "",
        ]
    )
    lines.extend(["", "## Figures", ""])
    for label, link in figure_links:
        lines.extend([f"### {label}", "", f"![{label}]({link})", ""])

    comparisons = analysis.get("paired_comparisons", {})
    comparison_rows: list[dict[str, object]] = []
    if isinstance(comparisons, Mapping):
        for key, comparison in comparisons.items():
            if isinstance(comparison, Mapping):
                comparison_rows.append(
                    {
                        "comparison": key,
                        "paired trials": comparison.get("paired_trials"),
                        "mean difference": _fmt(comparison.get("mean_difference")),
                        "Cohen dz": _fmt(comparison.get("cohen_dz")),
                        "raw p": _fmt(comparison.get("p_value")),
                        "Holm p": _fmt(comparison.get("holm_adjusted_p_value")),
                        "method": comparison.get("method"),
                        "inference status": (
                            "estimable"
                            if comparison.get("p_value") is not None
                            else f"undefined: {comparison.get('undefined', 'no genuine matched trials')}"
                        ),
                    }
                )
    lines.extend(["## Paired comparisons", ""])
    lines.extend(_markdown_table(comparison_rows))
    lines.extend(
        [
            "",
            "Inferential comparisons use the frozen primary metric only when both models have genuine, matched "
            "stochastic seeds. Deterministic estimates remain descriptive and are never broadcast across seeds. "
            "Undefined comparisons are reported, not converted to zero; Holm adjustment applies only to valid tests.",
            "",
            "## Repetition planning",
            "",
        ]
    )
    groups = analysis.get("groups", {})
    repetition_rows: list[dict[str, object]] = []
    if isinstance(groups, Mapping):
        for key, group in groups.items():
            if not isinstance(group, Mapping):
                continue
            plan = group.get("repetition_plan", {})
            if not isinstance(plan, Mapping):
                continue
            fit_cost = _as_mapping(group.get("fit_cost"))
            cpu_cost = _as_mapping(fit_cost.get("cpu_seconds"))
            repetition_rows.append(
                {
                    "cell family": key,
                    "planning trials attempted": plan.get("pilot_trials"),
                    "finite planning outcomes": plan.get("finite_pilot_trials"),
                    "planning determinate": plan.get("planning_determinate"),
                    "pilot SD point estimate": _fmt(plan.get("observed_sd")),
                    "target half-width": _fmt(plan.get("target_ci_half_width")),
                    "uncapped theoretical need": plan.get("uncapped_required_trials"),
                    "fixed execution trials": plan.get("fixed_execution_trials"),
                    "operational cap": plan.get("operational_trial_cap"),
                    "scheduled cap reached": plan.get("scheduled_cap_reached"),
                    "operational cap reached": plan.get("operational_cap_reached"),
                    "operational cap evidence": plan.get(
                        "operational_cap_reached_reason"
                    ),
                    "cap binding": plan.get("maximum_cap_binding"),
                    "projected half-width at cap": _fmt(
                        plan.get("projected_ci_half_width_at_cap")
                    ),
                    "target projected met at cap": plan.get(
                        "precision_target_projected_met_at_cap"
                    ),
                    "achieved seed half-width": _fmt(
                        plan.get("achieved_ci_half_width")
                    ),
                    "target observed met": plan.get(
                        "precision_target_observed_met"
                    ),
                    "mean fit CPU-s": _fmt(cpu_cost.get("mean")),
                    "projected fixed fit CPU-h": _fmt(
                        fit_cost.get(
                            "projected_fit_cpu_hours_at_fixed_execution_trials"
                        )
                    ),
                    "reason": plan.get("reason"),
                }
            )
    lines.extend(_markdown_table(repetition_rows))
    lines.extend(
        [
            "",
            "Epochs, windows, bootstrap replicates, and protocol cycles are not independent trials. Every "
            "stochastic family executes the frozen 50-seed schedule regardless of the pilot estimate. The "
            "uncapped need and projected half-width at 50 are conditional projections from a fragile five-seed "
            "sample-SD point estimate (with no variance upper bound), not a guarantee that 50 is sufficient. "
            "If the uncapped need exceeds 50, the cap remains binding and the precision target remains unmet. "
            "Seed replication quantifies training variability only and cannot repair too few independent units "
            "or recording clusters.",
            "",
            "## Reproducibility artifacts",
            "",
            f"- Machine-readable run table: `{phase}-per-run-metrics.csv`",
            f"- Machine-readable aggregate table: `{phase}-aggregate-metrics.csv`",
            f"- Machine-readable class table: `{phase}-per-class-metrics.csv`",
            f"- Machine-readable threshold sensitivity: `{phase}-threshold-sensitivity.csv`",
            f"- Machine-readable diagnostics: `{phase}-diagnostics.csv`",
            f"- Machine-readable artifact audit: `{phase}-artifact-integrity.csv`",
            f"- Custom-track readiness audit: `{phase}-custom-track-readiness.json`",
            "- Frozen configuration: `../frozen-config.json`",
            "- Numerical core hashes: `../numerical-core-manifest.json`",
            "- Each cell JSON records source, window, preprocessing, model, calibration, metric, timing, and artifact identities.",
            "- Each JSONL prediction artifact contains one row per independent test unit with score, threshold, truth, and prediction.",
            "",
            "## Interpretation boundary",
            "",
            (
                "Pilot results estimate feasibility and variance only; they must not be presented as final confirmatory evidence."
                if phase == "pilot"
                else "Confirmatory interpretation is allowed only when the claim status above is ELIGIBLE and every frozen cell is retained."
            ),
            " Cross-dataset averages are intentionally absent because label semantics and sensing modalities differ.",
            "",
            "### Dataset-specific limitations",
            "",
            "- ADFA-LD: official validation normals are split into validation/test at raw-trace level; "
            "byte-identical copies and contradictory label hashes are excluded and counted.",
            "- LID-DS 2021: published truth is recording-level, while a bounded label-blind sample of intact "
            "syscall sequences represents each recording; attack localization within a recording is unavailable.",
            "- HAI-23.05: the unit is a fixed non-overlapping temporal block; a block is positive when it overlaps "
            "a published attack event, so block-level and row-level metrics are not interchangeable. The available "
            "data provide 2 source recordings versus the configured minimum of 5 independent clusters; recording-cluster "
            "confidence intervals are therefore undefined with that reason retained. Fifty training seeds do not create "
            "three missing independent recordings, so across-seed intervals must not be substituted.",
            "- Controlled custom campaign: the legacy two-instance result remains smoke evidence and is not "
            "admitted into this official-benchmark matrix. It requires a separately powered paired campaign.",
            "",
        ]
    )
    if failures:
        lines.extend(["## Failed cells", "", "```json", json.dumps(failures, indent=2), "```", ""])
    return "\n".join(lines)


def _safe_failure_rows(
    retained_failures: Sequence[Mapping[str, object]],
) -> list[dict[str, object]]:
    """Expose identifiers and resolution state without exception or outcome payloads."""

    fields = (
        "schema_version",
        "phase",
        "dataset",
        "model",
        "seed",
        "deterministic",
        "seed_position",
        "batch_id",
        "batch_position",
        "schedule_kind",
        "schedule_identity",
        "logical_cell_key",
        "resolution_status",
    )
    return [
        {field: failure.get(field) for field in fields if field in failure}
        for failure in retained_failures
    ]


def _per_run_rows(cells: Sequence[Mapping[str, object]]) -> list[dict[str, object]]:
    rows: list[dict[str, object]] = []
    for cell in sorted(cells, key=lambda item: (str(item["dataset"]), str(item["model"]), int(item["seed"]))):
        calibration = _as_mapping(cell.get("threshold_calibration"))
        test = _as_mapping(cell.get("test"))
        operating = _as_mapping(test.get("operating"))
        ranking = _as_mapping(test.get("ranking"))
        validation_support = _as_mapping(calibration.get("validation_support"))
        ci = _as_mapping(test.get("bootstrap_unit_ci"))
        f1_ci = _as_mapping(ci.get("f1"))
        auroc_ci = _as_mapping(ci.get("auroc"))
        auprc_ci = _as_mapping(ci.get("auprc"))
        balanced_ci = _as_mapping(ci.get("balanced_accuracy"))
        mcc_ci = _as_mapping(ci.get("mcc"))
        bootstrap_design = _as_mapping(ci.get("design"))
        rows.append(
            {
                "dataset": cell.get("dataset"),
                "dataset protocol": cell.get("dataset_protocol"),
                "evidence origin": cell.get("evidence_origin")
                or _nested(cell, "data", "evidence_origin"),
                "model": cell.get("model"),
                "seed": cell.get("seed"),
                "test n": _nested(operating, "support", "total"),
                "F1": _fmt(operating.get("f1")),
                "F1 unit-CI": _interval(f1_ci.get("low"), f1_ci.get("high")),
                "balanced accuracy": _fmt(operating.get("balanced_accuracy")),
                "balanced accuracy unit-CI": _interval(
                    balanced_ci.get("low"), balanced_ci.get("high")
                ),
                "MCC": _fmt(operating.get("mcc")),
                "MCC unit-CI": _interval(mcc_ci.get("low"), mcc_ci.get("high")),
                "AUROC": _fmt(ranking.get("auroc")),
                "AUROC unit-CI": _interval(auroc_ci.get("low"), auroc_ci.get("high")),
                "AUPRC": _fmt(ranking.get("auprc")),
                "AUPRC unit-CI": _interval(auprc_ci.get("low"), auprc_ci.get("high")),
                "FPR": _fmt(operating.get("false_positive_rate")),
                "FNR": _fmt(operating.get("false_negative_rate")),
                "threshold": _fmt(calibration.get("value")),
                "validation normal": validation_support.get("normal"),
                "validation attack": validation_support.get("attack"),
                "validation FPR": _fmt(calibration.get("objective_value")),
                "bootstrap unit": bootstrap_design.get("resampling_unit", "not recorded"),
                "independent clusters": bootstrap_design.get("independent_cluster_count"),
                "minimum clusters required": bootstrap_design.get(
                    "minimum_clusters_required"
                ),
                "cluster interval valid": bootstrap_design.get(
                    "inferentially_valid"
                ),
                "cluster interval undefined reason": bootstrap_design.get(
                    "undefined_reason"
                ),
                "bootstrap qualification": bootstrap_design.get(
                    "qualification", "not recorded in legacy cell"
                ),
            }
        )
    return rows


def _aggregate_rows(
    analysis: Mapping[str, object], cells: Sequence[Mapping[str, object]]
) -> list[dict[str, object]]:
    groups = analysis.get("groups", {})
    rows: list[dict[str, object]] = []
    if not isinstance(groups, Mapping):
        return rows
    for _, group in sorted(groups.items()):
        if not isinstance(group, Mapping):
            continue
        metrics = _as_mapping(group.get("metrics"))
        dataset_name = str(group.get("dataset"))
        model_name = str(group.get("model"))
        representative = next(
            (
                cell
                for cell in cells
                if str(cell.get("dataset")) == dataset_name
                and str(cell.get("model")) == model_name
            ),
            {},
        )
        row: dict[str, object] = {
            "dataset": dataset_name,
            "dataset protocol": representative.get("dataset_protocol"),
            "evidence origin": representative.get("evidence_origin")
            or _nested(representative, "data", "evidence_origin"),
            "model": model_name,
            "trials": group.get("trial_count"),
            "deterministic": group.get("deterministic"),
        }
        for metric_name, label in (
            ("f1", "F1 mean [seed CI]"),
            ("balanced_accuracy", "balanced accuracy mean [seed CI]"),
            ("mcc", "MCC mean [seed CI]"),
            ("auroc", "AUROC mean [seed CI]"),
            ("auprc", "AUPRC mean [seed CI]"),
        ):
            summary = _as_mapping(metrics.get(metric_name))
            row[label] = _estimate_interval(summary)
        rows.append(row)
    return rows


def _per_class_rows(cells: Sequence[Mapping[str, object]]) -> list[dict[str, object]]:
    rows: list[dict[str, object]] = []
    for cell in sorted(cells, key=lambda item: (str(item["dataset"]), str(item["model"]), int(item["seed"]))):
        test = _as_mapping(cell.get("test"))
        classes = _as_mapping(test.get("per_attack_class"))
        events = _as_mapping(test.get("events"))
        for class_name, values in sorted(classes.items()):
            metrics = _as_mapping(values)
            ranking = metrics
            rows.append(
                {
                    "dataset": cell.get("dataset"),
                    "dataset protocol": cell.get("dataset_protocol"),
                    "evidence origin": cell.get("evidence_origin")
                    or _nested(cell, "data", "evidence_origin"),
                    "model": cell.get("model"),
                    "seed": cell.get("seed"),
                    "attack class": class_name,
                    "attack support": _nested(metrics, "support", "attack"),
                    "recall": _fmt(metrics.get("recall")),
                    "precision": _fmt(metrics.get("precision")),
                    "F1": _fmt(metrics.get("f1")),
                    "AUROC": _fmt(ranking.get("auroc")),
                    "event recall (overall)": _fmt(events.get("event_recall")),
                }
            )
    return rows


def _threshold_sensitivity_rows(
    cells: Sequence[Mapping[str, object]],
    integrity_rows: Sequence[Mapping[str, object]],
) -> list[dict[str, object]]:
    rows: list[dict[str, object]] = []
    integrity = {
        str(row.get("cell id")): row.get("status") == "pass"
        for row in integrity_rows
    }
    for cell in sorted(
        cells,
        key=lambda item: (str(item["dataset"]), str(item["model"]), int(item["seed"])),
    ):
        if not integrity.get(str(cell.get("cell_id")), False):
            continue
        artifact = _as_mapping(cell.get("predictions_artifact"))
        prediction_path = Path(str(artifact.get("path", "")))
        if not prediction_path.is_file():
            continue
        scores: list[float] = []
        truths: list[int] = []
        for line in prediction_path.read_text(encoding="utf-8").splitlines():
            value = json.loads(line)
            if isinstance(value, Mapping):
                scores.append(float(value["score"]))
                truths.append(int(value["truth"]))
        calibration = _as_mapping(cell.get("threshold_calibration"))
        sensitivity = calibration.get("sensitivity", [])
        if not isinstance(sensitivity, list):
            continue
        for candidate in sensitivity:
            if not isinstance(candidate, Mapping):
                continue
            threshold = candidate.get("threshold")
            if not isinstance(threshold, (int, float)):
                continue
            metrics = binary_operating_metrics(scores, truths, float(threshold))
            rows.append(
                {
                    "dataset": cell.get("dataset"),
                    "model": cell.get("model"),
                    "seed": cell.get("seed"),
                    "validation normal quantile": _fmt(candidate.get("normal_quantile")),
                    "threshold": _fmt(threshold),
                    "attained validation FPR": _fmt(candidate.get("attained_normal_fpr")),
                    "test FPR": _fmt(metrics.get("false_positive_rate")),
                    "test recall": _fmt(metrics.get("recall")),
                    "test precision": _fmt(metrics.get("precision")),
                    "test F1": _fmt(metrics.get("f1")),
                    "test balanced accuracy": _fmt(metrics.get("balanced_accuracy")),
                }
            )
    return rows


def _artifact_integrity_rows(
    cells: Sequence[Mapping[str, object]],
    *,
    config: Mapping[str, object],
) -> list[dict[str, object]]:
    """Independently authenticate raw prediction artifacts used by the report."""

    rows: list[dict[str, object]] = []
    for cell in sorted(
        cells,
        key=lambda item: (
            str(item.get("dataset")),
            str(item.get("model")),
            int(item.get("seed", 0)),
        ),
    ):
        reasons: list[str] = []
        artifact = _as_mapping(cell.get("predictions_artifact"))
        raw_path = artifact.get("path")
        path = Path(str(raw_path)) if raw_path else Path()
        cell_artifact_path = cell.get("artifact_path")
        expected_predictions_dir = (
            Path(str(cell_artifact_path)).parent.parent / "predictions"
            if isinstance(cell_artifact_path, str) and cell_artifact_path
            else None
        )
        expected_hash = artifact.get("sha256")
        expected_rows = artifact.get("rows")
        actual_hash: str | None = None
        actual_rows = 0
        prediction_origins: set[str] = set()
        unit_ids: set[str] = set()
        reconstruction_identity: object = None
        unsafe_prediction_path = path.is_symlink()
        if unsafe_prediction_path:
            reasons.append("prediction artifact must not be a symlink")
        if (
            raw_path
            and expected_predictions_dir is not None
            and path.resolve().parent != expected_predictions_dir.resolve()
        ):
            unsafe_prediction_path = True
            reasons.append("prediction artifact escapes the frozen predictions directory")
        if unsafe_prediction_path:
            pass
        elif not raw_path or not path.is_file():
            reasons.append("prediction artifact is missing")
        else:
            actual_hash = file_sha256(path)
            if not isinstance(expected_hash, str) or actual_hash != expected_hash:
                reasons.append("prediction SHA-256 does not match the cell record")
            for line_number, raw_line in enumerate(
                path.read_text(encoding="utf-8").splitlines(), start=1
            ):
                try:
                    value = json.loads(raw_line)
                except json.JSONDecodeError:
                    reasons.append(f"prediction row {line_number} is not valid JSON")
                    continue
                if not isinstance(value, Mapping):
                    reasons.append(f"prediction row {line_number} is not an object")
                    continue
                actual_rows += 1
                unit_id = value.get("unit_id")
                if not isinstance(unit_id, str) or not unit_id:
                    reasons.append(f"prediction row {line_number} has no stable unit_id")
                elif unit_id in unit_ids:
                    reasons.append(f"prediction unit_id {unit_id!r} is duplicated")
                else:
                    unit_ids.add(unit_id)
                origin = value.get("evidence_origin")
                if isinstance(origin, str):
                    prediction_origins.add(origin)
                for numeric_name in ("score", "threshold"):
                    numeric = value.get(numeric_name)
                    if (
                        not isinstance(numeric, (int, float))
                        or isinstance(numeric, bool)
                        or not math.isfinite(float(numeric))
                    ):
                        reasons.append(
                            f"prediction row {line_number} has invalid {numeric_name}"
                        )
                if (
                    type(value.get("truth")) is not int
                    or value.get("truth") not in {0, 1}
                    or type(value.get("prediction")) is not int
                    or value.get("prediction") not in {0, 1}
                ):
                    reasons.append(f"prediction row {line_number} has non-binary truth/prediction")
            if not isinstance(expected_rows, int) or isinstance(expected_rows, bool):
                reasons.append("cell does not declare an integer prediction row count")
            elif actual_rows != expected_rows:
                reasons.append(
                    f"prediction row count mismatch: expected {expected_rows}, found {actual_rows}"
                )
            metric_support = _nested(cell, "test", "operating", "support", "total")
            if isinstance(metric_support, int) and expected_rows != metric_support:
                reasons.append(
                    "prediction row count does not match the operating-metric support"
                )
        cell_origin = cell.get("evidence_origin") or _nested(
            cell, "data", "evidence_origin"
        )
        if prediction_origins and prediction_origins != {str(cell_origin)}:
            reasons.append("prediction evidence_origin is inconsistent with the cell")
        if cell.get("schema_version") == "academic-cell-result-v2" and prediction_origins != {
            "official_native"
        }:
            reasons.append("v2 official prediction rows require evidence_origin=official_native")
        if cell.get("schema_version") == "academic-cell-result-v2":
            try:
                if not isinstance(cell_artifact_path, str) or not cell_artifact_path:
                    raise ValueError("cell artifact path is unavailable")
                _validate_publication_transaction(
                    cell,
                    cell_path=Path(cell_artifact_path),
                    prediction_path=path,
                )
                reconstruction = validate_cell_raw_reconstruction(
                    cell, config=config
                )
                reconstruction_identity = reconstruction.get("identity")
            except (OSError, TypeError, ValueError) as exc:
                reasons.append(f"raw-evidence reconstruction failed: {exc}")
        rows.append(
            {
                "cell id": cell.get("cell_id"),
                "dataset": cell.get("dataset"),
                "model": cell.get("model"),
                "seed": cell.get("seed"),
                "status": "pass" if not reasons else "fail",
                "expected rows": expected_rows,
                "actual rows": actual_rows,
                "expected SHA-256": expected_hash,
                "actual SHA-256": actual_hash,
                "evidence origin": cell_origin,
                "prediction origins": ", ".join(sorted(prediction_origins)) or "missing",
                "raw reconstruction identity": reconstruction_identity,
                "reasons": "; ".join(dict.fromkeys(reasons)) or "none",
            }
        )
    return rows


def _diagnostic_rows(cells: Sequence[Mapping[str, object]]) -> list[dict[str, object]]:
    rows: list[dict[str, object]] = []
    for cell in sorted(
        cells,
        key=lambda item: (str(item["dataset"]), str(item["model"]), int(item["seed"])),
    ):
        test = _as_mapping(cell.get("test"))
        operating = _as_mapping(test.get("operating"))
        confusion = _as_mapping(operating.get("confusion_matrix"))
        distribution = _as_mapping(test.get("score_distribution"))
        normal = _as_mapping(distribution.get("normal"))
        attack = _as_mapping(distribution.get("attack"))
        fit = _as_mapping(cell.get("model_fit"))
        convergence = _as_mapping(fit.get("convergence"))
        loss = convergence.get("loss", [])
        val_loss = convergence.get("val_loss", [])
        inference = _as_mapping(_as_mapping(cell.get("inference_cost")).get("test"))
        rows.append(
            {
                "dataset": cell.get("dataset"),
                "dataset protocol": cell.get("dataset_protocol"),
                "evidence origin": cell.get("evidence_origin")
                or _nested(cell, "data", "evidence_origin"),
                "model": cell.get("model"),
                "seed": cell.get("seed"),
                "TN/FP/FN/TP": "/".join(
                    str(confusion.get(name, "?")) for name in ("tn", "fp", "fn", "tp")
                ),
                "normal score median [IQR]": _median_iqr(normal),
                "attack score median [IQR]": _median_iqr(attack),
                "epochs planned/executed": f"{fit.get('epochs_planned', '?')}/{fit.get('epochs_executed', '?')}",
                "loss first→last": _first_last(loss),
                "val loss first→last": _first_last(val_loss),
                "parameters": fit.get("parameter_count"),
                "weight bytes": fit.get("model_bytes"),
                "fit wall-s": _fmt(fit.get("fit_wall_seconds")),
                "fit CPU-s": _fmt(fit.get("fit_cpu_seconds")),
                "test ms/window": _fmt(inference.get("milliseconds_per_window")),
                "model hash": fit.get("model_identity"),
                "prediction hash": _nested(cell, "predictions_artifact", "sha256"),
            }
        )
    return rows


def _legacy_audit(config: Mapping[str, object], project_root: Path) -> str:
    configured = config.get("legacy_report")
    if not configured:
        return ""
    path = Path(str(configured))
    if not path.is_absolute():
        path = project_root / path
    if not path.is_file():
        return f"The declared legacy report was not found at `{path}`; it is not used as evidence."
    text = path.read_text(encoding="utf-8")
    classified: list[dict[str, object]] = []
    for line in text.splitlines():
        if not line.startswith("|") or "run-" not in line or "---" in line:
            continue
        fields = [field.strip() for field in line.strip().strip("|").split("|")]
        if len(fields) < 3:
            continue
        classified.append(
            {
                "legacy result": fields[2],
                "benchmark": fields[0],
                "model": fields[1],
                "classification": "integration-smoke",
                "admissible": "no",
                "reason": (
                    "outcome-selected row; no predeclared repetitions, validation-only "
                    "score calibration, or uncertainty interval"
                ),
            }
        )
    introduction = (
        f"The legacy report `{path.name}` (SHA-256 `{file_sha256(path)}`) is retained but not pooled. "
        "Each displayed legacy run is classified below; missing raw evidence remains explicit."
    )
    return "\n\n".join((introduction, "\n".join(_markdown_table(classified))))


def _audit_custom_campaign(project_root: Path) -> dict[str, object]:
    root = Path(project_root) / "evidence" / "custom-dataset"
    files = sorted(root.glob("*/current-syscall-windows.jsonl")) if root.is_dir() else []
    rows: list[dict[str, object]] = []
    file_hashes: dict[str, str] = {}
    for path in files:
        file_hashes[str(path.relative_to(project_root)).replace("\\", "/")] = file_sha256(path)
        for raw_line in path.read_text(encoding="utf-8").splitlines():
            value = json.loads(raw_line)
            if not isinstance(value, dict):
                continue
            schema = value.get("current_feature_schema", [])
            vector = value.get("current_feature_vector", [])
            active_quality_flags = 0
            if isinstance(schema, list) and isinstance(vector, list):
                for name, feature in zip(schema, vector):
                    if (
                        isinstance(name, str)
                        and any(token in name for token in ("malfunction", "saturated", "cold_start"))
                        and isinstance(feature, (int, float))
                        and float(feature) != 0.0
                    ):
                        active_quality_flags += 1
            results = value.get("autoencoder_results", [])
            if not isinstance(results, list):
                results = []
            rows.append(
                {
                    "campaign": value.get("campaign_id"),
                    "scenario": value.get("scenario_label"),
                    "round": value.get("round_id"),
                    "physical_quality_flags": active_quality_flags,
                    "autoencoder_results": len(results),
                    "classifications": [
                        result.get("classification")
                        for result in results
                        if isinstance(result, Mapping)
                    ],
                    "validation_levels": [
                        result.get("source_dataset_validation_level")
                        for result in results
                        if isinstance(result, Mapping)
                    ],
                }
            )
    campaigns = sorted({str(row["campaign"]) for row in rows if row.get("campaign")})
    scenarios: dict[str, int] = {}
    for row in rows:
        scenario = str(row.get("scenario", "missing"))
        scenarios[scenario] = scenarios.get(scenario, 0) + 1
    scored_rows = sum(int(row["autoencoder_results"]) > 0 for row in rows)
    classifications: dict[str, int] = {}
    validation_levels: dict[str, int] = {}
    for row in rows:
        for value in row["classifications"]:  # type: ignore[union-attr]
            name = str(value)
            classifications[name] = classifications.get(name, 0) + 1
        for value in row["validation_levels"]:  # type: ignore[union-attr]
            name = str(value)
            validation_levels[name] = validation_levels.get(name, 0) + 1
    active_flag_rows = sum(int(row["physical_quality_flags"]) > 0 for row in rows)
    summary_rows = [
        {
            "campaigns": len(campaigns),
            "round rows": len(rows),
            "normal rows": scenarios.get("normal", 0),
            "edge-exclusion rows": scenarios.get("faulty_edge_exclusion", 0),
            "rows with AE score": scored_rows,
            "AE anomaly classifications": classifications.get("anomaly", 0),
            "rows with physical quality flag": active_flag_rows,
            "validation levels": ", ".join(
                f"{name}:{count}" for name, count in sorted(validation_levels.items())
            ) or "none",
        }
    ]
    blocking_reasons = [
        "no frozen, powered custom-campaign preregistration is bound to these files",
        f"only {scored_rows}/{len(rows)} rows contain an autoencoder result",
        "available autoencoder results are marked runtime_valid_only",
        "scenario truth does not provide separate physical/syscall/replay/pipeline labels",
    ]
    ready = False
    interpretation = (
        "The existing files are integration evidence only. `faulty_edge_exclusion` is a cyber/availability "
        "condition, while every captured physical vector has zero malfunction, saturation, and cold-start "
        "flags; it cannot be relabelled as a physical anomaly. A new paired pilot must capture separate "
        "physical, syscall, replay, and pipeline-outcome truth for every run, then derive confirmatory "
        "repetitions from between-pair dispersion."
    )
    return {
        "schema_version": "custom-track-readiness-v1",
        "status": "READY" if ready else "BLOCKED — INTEGRATION-SMOKE ONLY",
        "root": str(root.resolve()),
        "source_file_sha256": file_hashes,
        "campaign_ids": campaigns,
        "scenario_row_counts": scenarios,
        "row_count": len(rows),
        "scored_row_count": scored_rows,
        "classification_counts": classifications,
        "validation_level_counts": validation_levels,
        "physical_quality_flag_row_count": active_flag_rows,
        "blocking_reasons": blocking_reasons,
        "summary_rows": summary_rows,
        "interpretation": interpretation,
    }


def _protocol_rows(
    config: Mapping[str, object],
    phase: str,
    cells: Sequence[Mapping[str, object]],
) -> list[dict[str, object]]:
    rows: list[dict[str, object]] = []
    datasets = _as_mapping(config.get("datasets"))
    for dataset_name, raw_dataset in sorted(datasets.items()):
        dataset = _as_mapping(raw_dataset)
        representative = next(
            (cell for cell in cells if str(cell.get("dataset")) == str(dataset_name)),
            {},
        )
        phase_caps = _as_mapping(dataset.get("phase_caps"))
        allocation = _as_mapping(dataset.get("phase_allocation"))
        rows.append(
            {
                "dataset": dataset_name,
                "kind": dataset.get("kind", dataset_name),
                "protocol id": representative.get("dataset_protocol")
                or dataset.get("protocol_id")
                or "not recorded",
                "evidence origin": representative.get("evidence_origin")
                or _nested(representative, "data", "evidence_origin")
                or dataset.get("evidence_origin")
                or "missing",
                "phase": phase,
                "phase caps": _compact_json(phase_caps.get(phase, {})),
                "phase allocation": _compact_json(allocation.get(phase, {})),
                "window": _compact_json(dataset.get("window", {})),
                "minimum support": _compact_json(
                    _as_mapping(dataset.get("minimum_support")).get(phase, {})
                ),
            }
        )
    return rows


def _hyperparameter_rows(config: Mapping[str, object]) -> list[dict[str, object]]:
    rows: list[dict[str, object]] = []
    datasets = _as_mapping(config.get("datasets"))
    for dataset_name, raw_dataset in sorted(datasets.items()):
        models = _as_mapping(_as_mapping(raw_dataset).get("models"))
        for model_name, raw_model in sorted(models.items()):
            model = _as_mapping(raw_model)
            parameters = [
                (name, value)
                for name, value in sorted(model.items())
                if name != "deterministic"
            ]
            if not parameters:
                parameters = [("(none)", "not applicable")]
            for name, value in parameters:
                rows.append(
                    {
                        "dataset": dataset_name,
                        "model": model_name,
                        "randomness": (
                            "deterministic"
                            if bool(model.get("deterministic", False))
                            else "seeded"
                        ),
                        "parameter": name,
                        "value": _compact_json(value),
                        "numeric authority": (
                            "see authenticated ParameterEvidence.v1 gate"
                            if config.get("parameter_evidence")
                            or config.get("numeric_authority")
                            else "missing — result blocked"
                        ),
                    }
                )
    return rows


def _design_text(config: Mapping[str, object], phase: str) -> str:
    statistics = _as_mapping(config.get("statistical_protocol"))
    threshold = _as_mapping(statistics.get("threshold"))
    seeds = config.get(f"{phase}_seeds", [])
    execution = _as_mapping(config.get("execution_protocol"))
    schedule_note = ""
    if config.get("schema_version") == "thesis-evaluation-config-v2":
        schedule_note = (
            " Each deterministic dataset/model fit is executed once in this phase."
            if phase == "pilot"
            else (
                " Every genuinely stochastic family executes all 50 seeds in five immutable "
                f"positional batches of {execution.get('confirmatory_batch_size', 10)}; each "
                "deterministic dataset/model fit executes once in batch 1. Outcome analysis is "
                "withheld until the full matrix is authenticated, and no batch result may alter "
                "the remaining schedule."
            )
        )
    return (
        f"The `{phase}` seed schedule is `{seeds}`. The primary metric is "
        f"`{statistics.get('primary_metric', 'auroc')}`; confidence level is "
        f"`{statistics.get('confidence_level', 0.95)}`; unit-bootstrap replicates are "
        f"`{statistics.get('bootstrap_replicates', 2000)}`. Cluster inference requires "
        f"`{statistics.get('minimum_class_carrying_clusters')}` class-carrying clusters "
        "per class and at least "
        f"`{statistics.get('minimum_valid_bootstrap_replicates')}` / "
        f"`{statistics.get('minimum_valid_bootstrap_fraction')}` valid mixed-label "
        "replicates. The operating threshold method is "
        f"`{threshold.get('method', 'target-fpr')}` with target validation FPR "
        f"`{threshold.get('target_fpr', 0.01)}`. Hyperparameters and dataset caps come from the "
        f"content-addressed frozen configuration.{schedule_note}"
    )


def _compact_json(value: object) -> str:
    return json.dumps(value, sort_keys=True, separators=(",", ":"), ensure_ascii=False)


def _confirmatory_status(
    eligibility: Mapping[str, object],
) -> str:
    eligible = eligibility.get("eligible") is True
    return "ELIGIBLE FOR PREDECLARED CONFIRMATORY CLAIMS" if eligible else "INCOMPLETE — NOT ELIGIBLE FOR FINAL CLAIMS"


def _eligibility_audit(
    config: Mapping[str, object],
    *,
    phase: str,
    cells: Sequence[Mapping[str, object]],
    preflight: Mapping[str, object],
    run_summary: Mapping[str, object],
    planned_matrix: Mapping[str, object],
    batch_ledger: Mapping[str, object],
    retained_failures: Sequence[Mapping[str, object]],
    integrity_rows: Sequence[Mapping[str, object]],
) -> dict[str, object]:
    """Recompute admission from authenticated identities, never from a file count."""

    reasons: list[str] = []
    gate = _as_mapping(run_summary.get("eligibility_gate"))
    configuration_identity = config_identity(config)
    actual_ids = [str(cell.get("cell_id", "")) for cell in cells]
    planned_ids = gate.get("planned_cell_ids", [])
    authenticated_ids = gate.get("authenticated_complete_cell_ids", [])
    if phase != "confirmatory":
        reasons.append("pilot evidence is exploratory by contract")
    if config.get("schema_version") != "thesis-evaluation-config-v2":
        reasons.append("only the corrected v2 configuration schema can be admitted")
    if (
        preflight.get("schema_version") != "academic-preflight-v2"
        or preflight.get("ready") is not True
        or preflight.get("phase") != phase
        or preflight.get("config_identity") != configuration_identity
    ):
        reasons.append("authenticated v2 preflight is missing or blocked")
    if (
        run_summary.get("schema_version") != "academic-run-summary-v2"
        or run_summary.get("phase") != phase
        or run_summary.get("config_identity") != configuration_identity
    ):
        reasons.append("v2 run summary is absent or bound to another phase/configuration")
    if gate.get("phase") != phase or gate.get("config_identity") != configuration_identity:
        reasons.append("eligibility gate is absent or bound to another phase/configuration")
    required_gate_flags = [
        "exact_matrix_match",
        "prediction_artifacts_verified",
        "raw_evidence_reconstructed",
        "core_manifest_verified",
        "numeric_authority_accountable",
        "evidence_origins_valid",
        "phase_disjointness_passed",
        "validation_roles_disjoint",
        "repetition_planning_authenticated",
        "schema_versions_valid",
        "primary_outcomes_complete",
        "computational_budget_authorized",
    ]
    if (
        config.get("schema_version") == "thesis-evaluation-config-v2"
        and phase == "confirmatory"
    ):
        required_gate_flags.append("confirmatory_batch_ledger_verified")
    for flag in required_gate_flags:
        if gate.get(flag) is not True:
            reasons.append(f"eligibility gate did not authenticate {flag}")
    if not isinstance(planned_ids, list) or not planned_ids:
        reasons.append("planned cell identities are absent")
    elif len(planned_ids) != len(set(str(value) for value in planned_ids)):
        reasons.append("planned cell identities contain duplicates")
    if not isinstance(authenticated_ids, list):
        reasons.append("authenticated cell identities are absent")
    elif set(str(value) for value in authenticated_ids) != set(str(value) for value in planned_ids):
        reasons.append("authenticated cells do not exactly match the planned matrix")
    if set(actual_ids) != set(str(value) for value in planned_ids) or len(actual_ids) != len(set(actual_ids)):
        reasons.append("report cell identities do not exactly match the planned matrix")
    _audit_planned_matrix(
        config,
        planned_matrix,
        phase=phase,
        configuration_identity=configuration_identity,
        cells=cells,
        reasons=reasons,
    )
    _audit_confirmatory_batch_ledger(
        config,
        batch_ledger,
        phase=phase,
        configuration_identity=configuration_identity,
        reasons=reasons,
    )
    if (
        config.get("schema_version") == "thesis-evaluation-config-v2"
        and phase == "confirmatory"
    ):
        try:
            expected_ledger_identity = canonical_json_hash(
                confirmatory_batch_ledger(config)
            )
        except Exception:
            expected_ledger_identity = None
        if run_summary.get("confirmatory_batch_ledger_identity") != expected_ledger_identity:
            reasons.append("run summary is not bound to the frozen confirmatory batch ledger")
    batch_progress = _recomputed_batch_progress(
        config,
        phase=phase,
        cells=cells,
        planned_matrix=planned_matrix,
        integrity_rows=integrity_rows,
    )
    if phase == "confirmatory" and config.get("schema_version") == "thesis-evaluation-config-v2":
        if _normalized_batch_progress(run_summary.get("batch_progress")) != batch_progress:
            reasons.append(
                "run-summary batch progress disagrees with the authenticated logical schedule"
            )
    current_analysis_identity = analysis_input_identity(cells, planned_matrix)
    summary_analysis = _as_mapping(run_summary.get("analysis"))
    if (
        run_summary.get("analysis_input_identity") != current_analysis_identity
        or summary_analysis.get("analysis_input_identity") != current_analysis_identity
        or summary_analysis.get("planned_matrix_identity")
        != canonical_json_hash(planned_matrix)
    ):
        reasons.append("run-summary analysis is not bound to the full current cell contents")
    unresolved_failure_count = sum(
        failure.get("resolution_status") != "resolved-by-authenticated-completion"
        for failure in retained_failures
    )
    if unresolved_failure_count:
        reasons.append(
            f"{unresolved_failure_count} retained failure artifacts remain independently unresolved"
        )
    if gate.get("retained_failure_count") != unresolved_failure_count:
        reasons.append("runner retained-failure count disagrees with the report audit")
    if gate.get("retained_failure_count") != 0:
        reasons.append("the runner did not certify zero unresolved retained failures")
    _audit_computational_budget(preflight, run_summary, reasons=reasons)
    if len(integrity_rows) != len(cells) or any(
        row.get("status") != "pass" for row in integrity_rows
    ):
        reasons.append("one or more prediction artifacts failed independent report verification")
    for cell in cells:
        if cell.get("schema_version") != "academic-cell-result-v2":
            reasons.append(f"cell {cell.get('cell_id')} is not a v2 result")
        if cell.get("phase") != phase or cell.get("config_identity") != configuration_identity:
            reasons.append(f"cell {cell.get('cell_id')} has incompatible phase/config identity")
        if cell.get("evidence_origin") != "official_native":
            reasons.append(f"cell {cell.get('cell_id')} lacks official_native origin")
        authority = _as_mapping(cell.get("numeric_authority"))
        if authority.get("accountability_outcome") != "accountable":
            reasons.append(f"cell {cell.get('cell_id')} lacks accountable numeric authority")
    numeric_gate = _as_mapping(preflight.get("numeric_authority"))
    numeric_status = str(numeric_gate.get("accountability_outcome", "missing"))
    if numeric_status != "accountable":
        reasons.append("ParameterEvidence.v1 closure is not accountable")
    allocation = _as_mapping(preflight.get("phase_allocation_audit"))
    phase_disjointness = "pass" if allocation.get("passed") is True else "blocked"
    if phase_disjointness != "pass":
        reasons.append("pilot/confirmatory source-unit disjointness is not authenticated")
    origin_ok = bool(cells) and all(
        cell.get("evidence_origin") == "official_native" for cell in cells
    )
    if not origin_ok:
        reasons.append("official benchmark evidence-origin closure failed")
    return {
        "eligible": not reasons and gate.get("eligible") is True,
        "numeric_authority": numeric_status,
        "evidence_origin": "pass" if origin_ok else "blocked",
        "phase_disjointness": phase_disjointness,
        "batch_progress": batch_progress,
        "reasons": list(dict.fromkeys(reasons)),
    }


def _audit_confirmatory_batch_ledger(
    config: Mapping[str, object],
    observed: Mapping[str, object],
    *,
    phase: str,
    configuration_identity: str,
    reasons: list[str],
) -> None:
    if not (
        config.get("schema_version") == "thesis-evaluation-config-v2"
        and phase == "confirmatory"
    ):
        return
    try:
        expected = confirmatory_batch_ledger(config)
    except Exception as exc:
        reasons.append(f"frozen confirmatory batch ledger cannot be derived: {exc}")
        return
    if observed.get("config_identity") != configuration_identity or dict(observed) != expected:
        reasons.append(
            "frozen confirmatory batch ledger is absent or disagrees with the configuration"
        )


def _expected_logical_cells(
    config: Mapping[str, object], phase: str
) -> list[dict[str, object]]:
    """Reconstruct the v2 logical schedule without trusting stored progress."""

    schedule_identity = _expected_schedule_identity(config, phase)
    seeds = config.get(f"{phase}_seeds")
    datasets = config.get("datasets")
    if (
        config.get("schema_version") != "thesis-evaluation-config-v2"
        or not isinstance(schedule_identity, str)
        or not isinstance(seeds, list)
        or not seeds
        or not isinstance(datasets, Mapping)
    ):
        return []
    execution = config.get("execution_protocol")
    batch_size = (
        execution.get("confirmatory_batch_size")
        if isinstance(execution, Mapping)
        else None
    )
    if phase == "confirmatory" and (
        not isinstance(batch_size, int)
        or isinstance(batch_size, bool)
        or batch_size <= 0
    ):
        return []
    if phase == "confirmatory":
        try:
            confirmatory_batch_ledger(config)
        except Exception:
            return []
    rows: list[dict[str, object]] = []
    for dataset_name, raw_dataset in datasets.items():
        if not isinstance(raw_dataset, Mapping):
            return []
        models = raw_dataset.get("models")
        if not isinstance(models, Mapping):
            return []
        for model_name, raw_model in models.items():
            if not isinstance(raw_model, Mapping):
                return []
            deterministic = raw_model.get("deterministic") is True
            if deterministic:
                entries = [
                    {
                        "seed": seeds[0],
                        "seed_position": 1,
                        "batch_id": "batch-01" if phase == "confirmatory" else None,
                        "batch_position": None,
                        "schedule_kind": "deterministic-singleton",
                    }
                ]
            else:
                entries = []
                for seed_position, seed in enumerate(seeds, start=1):
                    entries.append(
                        {
                            "seed": seed,
                            "seed_position": seed_position,
                            "batch_id": (
                                f"batch-{((seed_position - 1) // int(batch_size)) + 1:02d}"
                                if phase == "confirmatory"
                                else None
                            ),
                            "batch_position": (
                                ((seed_position - 1) % int(batch_size)) + 1
                                if phase == "confirmatory"
                                else None
                            ),
                            "schedule_kind": (
                                "fixed-nonadaptive-confirmatory-seeds"
                                if phase == "confirmatory"
                                else "independent-seed-trials"
                            ),
                        }
                    )
            for entry in entries:
                rows.append(
                    {
                        "dataset": str(dataset_name),
                        "model": str(model_name),
                        **entry,
                        "schedule_identity": schedule_identity,
                        "deterministic": deterministic,
                    }
                )
    return rows


def _normalized_batch_progress(value: object) -> list[dict[str, object]] | None:
    if not isinstance(value, list):
        return None
    normalized: list[dict[str, object]] = []
    allowed_fields = {
        "batch_id",
        "expected_cell_count",
        "authenticated_complete_cell_count",
        "complete",
    }
    for row in value:
        if not isinstance(row, Mapping) or set(row) != allowed_fields:
            return None
        expected_count = row.get("expected_cell_count")
        complete_count = row.get("authenticated_complete_cell_count")
        complete = row.get("complete")
        if (
            not isinstance(row.get("batch_id"), str)
            or not isinstance(expected_count, int)
            or isinstance(expected_count, bool)
            or expected_count < 0
            or not isinstance(complete_count, int)
            or isinstance(complete_count, bool)
            or complete_count < 0
            or not isinstance(complete, bool)
        ):
            return None
        normalized.append(
            {
                "batch_id": row["batch_id"],
                "expected_cell_count": expected_count,
                "authenticated_complete_cell_count": complete_count,
                "complete": complete,
            }
        )
    return normalized


def _recomputed_batch_progress(
    config: Mapping[str, object],
    *,
    phase: str,
    cells: Sequence[Mapping[str, object]],
    planned_matrix: Mapping[str, object],
    integrity_rows: Sequence[Mapping[str, object]],
) -> list[dict[str, object]]:
    if not (
        config.get("schema_version") == "thesis-evaluation-config-v2"
        and phase == "confirmatory"
    ):
        return []
    expected_rows = _expected_logical_cells(config, phase)
    expected_keys = [_logical_schedule_key(row) for row in expected_rows]
    raw_planned = planned_matrix.get("cells")
    planned_rows = (
        [row for row in raw_planned if isinstance(row, Mapping)]
        if isinstance(raw_planned, list)
        else []
    )
    raw_planned_count = len(raw_planned) if isinstance(raw_planned, list) else -1
    planned_keys = [_logical_schedule_key(row) for row in planned_rows]
    plan_exact = (
        bool(expected_keys)
        and len(planned_rows) == raw_planned_count
        and len(planned_keys) == len(set(planned_keys))
        and set(planned_keys) == set(expected_keys)
    )
    integrity_by_cell: dict[str, list[Mapping[str, object]]] = {}
    for row in integrity_rows:
        integrity_by_cell.setdefault(str(row.get("cell id", "")), []).append(row)
    authenticated_key_counts: dict[str, int] = {}
    compromised_batches: set[str] = set()
    progress_globally_compromised = False
    if plan_exact:
        planned_key_set = set(planned_keys)
        valid_batch_ids = {
            f"batch-{index:02d}"
            for index in range(1, V2_CONFIRMATORY_BATCH_COUNT + 1)
        }
        for cell in cells:
            cell_id = str(cell.get("cell_id", ""))
            checks = integrity_by_cell.get(cell_id, [])
            authority = _as_mapping(cell.get("numeric_authority"))
            blind_gate = _as_mapping(cell.get("blind_test_gate"))
            logical_key = _logical_schedule_key(cell)
            cell_batch_id = cell.get("batch_id")
            artifact_incompatible = (
                cell.get("phase") != phase
                or cell.get("config_identity") != config_identity(config)
                or logical_key not in planned_key_set
            )
            if artifact_incompatible:
                if isinstance(cell_batch_id, str) and cell_batch_id in valid_batch_ids:
                    compromised_batches.add(cell_batch_id)
                else:
                    progress_globally_compromised = True
            if (
                len(checks) == 1
                and checks[0].get("status") == "pass"
                and cell.get("schema_version") == "academic-cell-result-v2"
                and cell.get("status") == "complete"
                and cell.get("phase") == phase
                and cell.get("config_identity") == config_identity(config)
                and cell.get("evidence_origin") == "official_native"
                and authority.get("accountability_outcome") == "accountable"
                and blind_gate.get("calibration_frozen_before_test_scoring") is True
                and blind_gate.get(
                    "test_truth_used_for_fit_preprocessing_stopping_or_calibration"
                )
                is False
                and logical_key in planned_key_set
            ):
                authenticated_key_counts[logical_key] = (
                    authenticated_key_counts.get(logical_key, 0) + 1
                )
    authenticated_keys = {
        key for key, count in authenticated_key_counts.items() if count == 1
    }
    progress: list[dict[str, object]] = []
    for batch_number in range(1, V2_CONFIRMATORY_BATCH_COUNT + 1):
        batch_id = f"batch-{batch_number:02d}"
        batch_keys = {
            _logical_schedule_key(row)
            for row in expected_rows
            if row.get("batch_id") == batch_id
        }
        complete_keys = batch_keys & authenticated_keys
        progress.append(
            {
                "batch_id": batch_id,
                "expected_cell_count": len(batch_keys),
                "authenticated_complete_cell_count": len(complete_keys),
                "complete": (
                    bool(batch_keys)
                    and complete_keys == batch_keys
                    and batch_id not in compromised_batches
                    and not progress_globally_compromised
                ),
            }
        )
    return progress


def _audit_planned_matrix(
    config: Mapping[str, object],
    planned_matrix: Mapping[str, object],
    *,
    phase: str,
    configuration_identity: str,
    cells: Sequence[Mapping[str, object]],
    reasons: list[str],
) -> None:
    """Bind report admission to the frozen logical schedule, not only cell IDs."""

    if (
        planned_matrix.get("schema_version") != "academic-logical-plan-v2"
        or planned_matrix.get("phase") != phase
        or planned_matrix.get("config_identity") != configuration_identity
        or planned_matrix.get("planning_error") is not None
        or planned_matrix.get("execution_schedule_adaptive") is not False
    ):
        reasons.append("frozen v2 planned matrix is absent, invalid, or identity-incompatible")
        return
    schedule_identity = planned_matrix.get("schedule_identity")
    if not isinstance(schedule_identity, str) or not schedule_identity:
        reasons.append("planned matrix has no authenticated schedule identity")
        return
    if schedule_identity != _expected_schedule_identity(config, phase):
        reasons.append("planned matrix schedule identity does not match the frozen configuration")
    raw_planned_cells = planned_matrix.get("cells")
    if not isinstance(raw_planned_cells, list) or not raw_planned_cells:
        reasons.append("planned matrix contains no logical cells")
        return
    planned_cells = [row for row in raw_planned_cells if isinstance(row, Mapping)]
    if len(planned_cells) != len(raw_planned_cells):
        reasons.append("planned matrix contains malformed logical cells")
        return
    if any(row.get("schedule_identity") != schedule_identity for row in planned_cells):
        reasons.append("planned logical cells disagree with the frozen schedule identity")
    if any(cell.get("schedule_identity") != schedule_identity for cell in cells):
        reasons.append("completed cells disagree with the frozen schedule identity")
    planned_keys = [_logical_schedule_key(row) for row in planned_cells]
    actual_keys = [_logical_schedule_key(cell) for cell in cells]
    expected_keys = [
        _logical_schedule_key(row) for row in _expected_logical_cells(config, phase)
    ]
    if len(planned_keys) != len(set(planned_keys)):
        reasons.append("planned matrix contains duplicate logical schedule keys")
    if (
        not expected_keys
        or len(expected_keys) != len(set(expected_keys))
        or set(planned_keys) != set(expected_keys)
        or len(planned_keys) != len(expected_keys)
    ):
        reasons.append("planned matrix does not exactly match the config-derived logical schedule")
    if len(actual_keys) != len(set(actual_keys)) or set(actual_keys) != set(planned_keys):
        reasons.append("completed cells do not exactly match the frozen logical schedule")


def _logical_schedule_key(row: Mapping[str, object]) -> str:
    fields = (
        "dataset",
        "model",
        "seed",
        "deterministic",
        "seed_position",
        "batch_id",
        "batch_position",
        "schedule_kind",
        "schedule_identity",
    )
    return canonical_json_hash({field: row.get(field) for field in fields})


def _expected_schedule_identity(
    config: Mapping[str, object], phase: str
) -> str | None:
    seeds = config.get(f"{phase}_seeds")
    if not isinstance(seeds, list) or not seeds:
        return None
    payload: dict[str, object] = {
        "config_identity": config_identity(config),
        "phase": phase,
        "seeds": list(seeds),
    }
    if config.get("schema_version") == "thesis-evaluation-config-v2" and phase == "confirmatory":
        execution = config.get("execution_protocol")
        if not isinstance(execution, Mapping):
            return None
        batch_size = execution.get("confirmatory_batch_size")
        if (
            not isinstance(batch_size, int)
            or isinstance(batch_size, bool)
            or batch_size <= 0
            or len(seeds) % batch_size
        ):
            return None
        payload["execution_protocol"] = execution
        payload["batches"] = [
            list(seeds[start : start + batch_size])
            for start in range(0, len(seeds), batch_size)
        ]
    return canonical_json_hash(payload)


def _audit_computational_budget(
    preflight: Mapping[str, object],
    run_summary: Mapping[str, object],
    *,
    reasons: list[str],
) -> None:
    """Require a complete finite estimate and explicit authorization above threshold."""

    preflight_budget = _as_mapping(preflight.get("computational_load"))
    summary_budget = _as_mapping(run_summary.get("computational_budget"))
    estimate = summary_budget.get("projected_total_cpu_hours_conservative")
    threshold = summary_budget.get("ask_first_cpu_hours")
    if (
        preflight_budget.get("projection_complete") is not True
        or preflight_budget.get("projected_preflight_invocations")
        != V2_CONFIRMATORY_PREFLIGHT_INVOCATIONS
        or preflight_budget.get("confirmatory_preflight_invocations")
        != V2_CONFIRMATORY_PREFLIGHT_INVOCATIONS
        or preflight_budget.get("confirmatory_standalone_preflight_invocations")
        != V2_CONFIRMATORY_STANDALONE_PREFLIGHT_INVOCATIONS
        or preflight_budget.get("confirmatory_batch_preflight_invocations")
        != V2_CONFIRMATORY_BATCH_COUNT
        or summary_budget.get("projection_complete") is not True
        or summary_budget.get("projected_preflight_invocations")
        != V2_CONFIRMATORY_PREFLIGHT_INVOCATIONS
        or summary_budget.get("confirmatory_preflight_invocations")
        != V2_CONFIRMATORY_PREFLIGHT_INVOCATIONS
        or summary_budget.get("confirmatory_standalone_preflight_invocations")
        != V2_CONFIRMATORY_STANDALONE_PREFLIGHT_INVOCATIONS
        or summary_budget.get("confirmatory_batch_preflight_invocations")
        != V2_CONFIRMATORY_BATCH_COUNT
        or not _is_finite_number(estimate)
        or float(estimate) < 0.0
        or not _is_finite_number(threshold)
        or float(threshold) <= 0.0
    ):
        reasons.append("complete finite computational-cost projection is not authenticated")
        return
    if summary_budget.get("eligibility_authorized") is not True:
        reasons.append("runner did not authenticate the computational-budget authorization")
    preflight_estimate = preflight_budget.get("projected_total_cpu_hours_conservative")
    preflight_threshold = preflight_budget.get("ask_first_cpu_hours")
    if (
        not _is_finite_number(preflight_estimate)
        or not _is_finite_number(preflight_threshold)
        or float(preflight_estimate) != float(estimate)
        or float(preflight_threshold) != float(threshold)
    ):
        reasons.append("run-summary computational budget disagrees with preflight")
    if (
        float(estimate) > float(threshold)
        and summary_budget.get("over_budget_authorized") is not True
    ):
        reasons.append("projected cost exceeds the ask-first threshold without authorization")


def _is_finite_number(value: object) -> bool:
    return (
        isinstance(value, (int, float))
        and not isinstance(value, bool)
        and math.isfinite(float(value))
    )


def _assert_safe_artifact_path(root: Path, path: Path, label: str) -> None:
    if root.is_symlink() or root.parent.is_symlink():
        raise RuntimeError(
            "academic experiment root and identity directory must not be symlinks"
        )
    if path.is_symlink():
        raise RuntimeError(f"unsafe {label} symlink: {path}")
    resolved_root = root.resolve()
    resolved_path = path.resolve()
    if resolved_path != resolved_root and not resolved_path.is_relative_to(resolved_root):
        raise RuntimeError(f"unsafe {label} outside the experiment root: {path}")


def _prepare_report_directory(root: Path, *directories: Path) -> None:
    for directory in directories:
        _assert_safe_artifact_path(root, directory, "report directory")
        directory.mkdir(parents=True, exist_ok=True)
        _assert_safe_artifact_path(root, directory, "report directory")


def _assert_safe_output_file(path: Path) -> None:
    if path.is_symlink():
        raise RuntimeError(f"refusing report output symlink: {path}")
    if path.resolve().parent != path.parent.resolve():
        raise RuntimeError(f"report output escapes its parent directory: {path}")


def _write_text(path: Path, value: str) -> None:
    path.parent.mkdir(parents=True, exist_ok=True)
    _assert_safe_output_file(path)
    temporary_path: Path | None = None
    try:
        with tempfile.NamedTemporaryFile(
            mode="w",
            encoding="utf-8",
            newline="\n",
            dir=path.parent,
            prefix=f".{path.name}.",
            suffix=".tmp",
            delete=False,
        ) as handle:
            temporary_path = Path(handle.name)
            handle.write(value)
            handle.flush()
            os.fsync(handle.fileno())
        _assert_safe_output_file(path)
        os.replace(temporary_path, path)
        temporary_path = None
    finally:
        if temporary_path is not None:
            temporary_path.unlink(missing_ok=True)


def _write_trial_variation_svg(
    path: Path, dataset: str, cells: Sequence[Mapping[str, object]]
) -> None:
    width, height = 860, 420
    left, top, plot_width, plot_height = 70, 45, 740, 300
    colors = {"f1": "#2563eb", "auroc": "#dc2626", "auprc": "#059669"}
    grouped: dict[str, list[Mapping[str, object]]] = {}
    for cell in cells:
        grouped.setdefault(str(cell["model"]), []).append(cell)
    svg = _svg_start(width, height, f"Trial variation — {dataset}")
    svg.extend(_axes(left, top, plot_width, plot_height, y_min=0.0, y_max=1.0))
    model_count = max(len(grouped), 1)
    x_step = plot_width / max(sum(len(rows) for rows in grouped.values()) + model_count, 2)
    x = left + x_step
    label_positions: list[tuple[float, str]] = []
    for model, rows in sorted(grouped.items()):
        model_start = x
        for row in sorted(rows, key=lambda item: int(item["seed"])):
            for metric, color in colors.items():
                value = _raw_metric(row, metric)
                if value is None:
                    continue
                y = top + (1.0 - min(max(value, 0.0), 1.0)) * plot_height
                svg.append(f'<circle cx="{x:.2f}" cy="{y:.2f}" r="4" fill="{color}"/>')
            x += x_step
        label_positions.append(((model_start + x - x_step) / 2.0, model))
        x += x_step
    for label_x, label in label_positions:
        svg.append(f'<text x="{label_x:.2f}" y="370" text-anchor="middle" font-size="11">{html.escape(label)}</text>')
    legend_x = left
    for metric, color in colors.items():
        svg.append(f'<rect x="{legend_x}" y="392" width="12" height="12" fill="{color}"/>')
        svg.append(f'<text x="{legend_x + 18}" y="403" font-size="12">{metric.upper()}</text>')
        legend_x += 105
    svg.extend(["</g>", "</svg>"])
    _write_text(path, "\n".join(svg) + "\n")


def _write_curve_svg(
    path: Path, dataset: str, model: str, cell: Mapping[str, object]
) -> None:
    width, height = 900, 430
    svg = _svg_start(width, height, f"ROC and precision-recall — {dataset} / {model}")
    curves = _as_mapping(_as_mapping(cell.get("test")).get("curves"))
    panels = (
        ("ROC", 55, _curve_xy(curves.get("roc"), "false_positive_rate", "true_positive_rate"), "FPR", "TPR"),
        ("Precision–recall", 495, _curve_xy(curves.get("precision_recall"), "recall", "precision"), "Recall", "Precision"),
    )
    for title, left, points, x_label, y_label in panels:
        top, panel_width, panel_height = 55, 340, 290
        svg.extend(_axes(left, top, panel_width, panel_height, y_min=0.0, y_max=1.0))
        if points:
            coordinates = " ".join(
                f"{left + x * panel_width:.2f},{top + (1.0 - y) * panel_height:.2f}"
                for x, y in points
            )
            svg.append(f'<polyline points="{coordinates}" fill="none" stroke="#2563eb" stroke-width="2"/>')
        svg.append(f'<text x="{left + panel_width / 2}" y="38" text-anchor="middle" font-size="15">{html.escape(title)}</text>')
        svg.append(f'<text x="{left + panel_width / 2}" y="375" text-anchor="middle" font-size="12">{html.escape(x_label)}</text>')
        svg.append(f'<text x="{left - 40}" y="{top + panel_height / 2}" text-anchor="middle" font-size="12" transform="rotate(-90 {left - 40} {top + panel_height / 2})">{html.escape(y_label)}</text>')
    svg.append(f'<text x="450" y="410" text-anchor="middle" font-size="11">Representative frozen seed: {cell.get("seed")}; curves are not pooled across datasets.</text>')
    svg.extend(["</g>", "</svg>"])
    _write_text(path, "\n".join(svg) + "\n")


def _curve_xy(value: object, x_name: str, y_name: str) -> list[tuple[float, float]]:
    points: list[tuple[float, float]] = []
    if not isinstance(value, list):
        return points
    for row in value:
        if not isinstance(row, Mapping):
            continue
        x, y = row.get(x_name), row.get(y_name)
        if isinstance(x, (int, float)) and isinstance(y, (int, float)):
            points.append((float(x), float(y)))
    return points


def _svg_start(width: int, height: int, title: str) -> list[str]:
    return [
        f'<svg xmlns="http://www.w3.org/2000/svg" width="{width}" height="{height}" viewBox="0 0 {width} {height}">',
        '<rect width="100%" height="100%" fill="white"/>',
        f'<text x="{width / 2}" y="22" text-anchor="middle" font-size="17" font-family="sans-serif">{html.escape(title)}</text>',
        '<g font-family="sans-serif" fill="#111827">',
    ]


def _axes(left: int, top: int, width: int, height: int, *, y_min: float, y_max: float) -> list[str]:
    lines = [
        f'<rect x="{left}" y="{top}" width="{width}" height="{height}" fill="#f9fafb" stroke="#374151"/>',
    ]
    for index in range(6):
        fraction = index / 5.0
        y = top + (1.0 - fraction) * height
        value = y_min + fraction * (y_max - y_min)
        lines.append(f'<line x1="{left}" y1="{y:.2f}" x2="{left + width}" y2="{y:.2f}" stroke="#e5e7eb"/>')
        lines.append(f'<text x="{left - 8}" y="{y + 4:.2f}" text-anchor="end" font-size="10">{value:.1f}</text>')
    return lines


def _raw_metric(cell: Mapping[str, object], name: str) -> float | None:
    test = _as_mapping(cell.get("test"))
    for section_name in ("operating", "ranking"):
        value = _as_mapping(test.get(section_name)).get(name)
        if isinstance(value, (int, float)) and math.isfinite(float(value)):
            return float(value)
    return None


def _write_csv(path: Path, rows: Sequence[Mapping[str, object]]) -> None:
    path.parent.mkdir(parents=True, exist_ok=True)
    _assert_safe_output_file(path)
    fieldnames = list(rows[0]) if rows else ["no_rows"]
    temporary_path: Path | None = None
    try:
        with tempfile.NamedTemporaryFile(
            mode="w",
            encoding="utf-8",
            newline="",
            dir=path.parent,
            prefix=f".{path.name}.",
            suffix=".tmp",
            delete=False,
        ) as handle:
            temporary_path = Path(handle.name)
            writer = csv.DictWriter(handle, fieldnames=fieldnames)
            writer.writeheader()
            writer.writerows(rows)
            handle.flush()
            os.fsync(handle.fileno())
        _assert_safe_output_file(path)
        os.replace(temporary_path, path)
        temporary_path = None
    finally:
        if temporary_path is not None:
            temporary_path.unlink(missing_ok=True)


def _markdown_table(rows: Sequence[Mapping[str, object]]) -> list[str]:
    if not rows:
        return ["_No rows available._"]
    columns = list(rows[0])
    result = [
        "| " + " | ".join(columns) + " |",
        "| " + " | ".join("---" for _ in columns) + " |",
    ]
    for row in rows:
        result.append(
            "| "
            + " | ".join(str(row.get(column, "")).replace("|", "\\|") for column in columns)
            + " |"
        )
    return result


def _estimate_interval(summary: Mapping[str, object]) -> str:
    estimate = _fmt(summary.get("mean"))
    low, high = summary.get("ci_low"), summary.get("ci_high")
    return estimate if low is None or high is None else f"{estimate} [{_fmt(low)}, {_fmt(high)}]"


def _interval(low: object, high: object) -> str:
    return "undefined" if low is None or high is None else f"[{_fmt(low)}, {_fmt(high)}]"


def _median_iqr(distribution: Mapping[str, object]) -> str:
    median = distribution.get("median")
    q25 = distribution.get("q25")
    q75 = distribution.get("q75")
    if median is None or q25 is None or q75 is None:
        return "undefined"
    return f"{_fmt(median)} [{_fmt(q25)}, {_fmt(q75)}]"


def _first_last(values: object) -> str:
    if not isinstance(values, list) or not values:
        return "not iterative"
    return f"{_fmt(values[0])} → {_fmt(values[-1])}"


def _fmt(value: object) -> str:
    if isinstance(value, bool):
        return str(value)
    if isinstance(value, (int, float)) and math.isfinite(float(value)):
        return f"{float(value):.6f}"
    return "undefined"


def _nested(value: object, *keys: str) -> object:
    current = value
    for key in keys:
        if not isinstance(current, Mapping):
            return None
        current = current.get(key)
    return current


def _as_mapping(value: object) -> Mapping[str, object]:
    return value if isinstance(value, Mapping) else {}


def _optional_json(path: Path) -> dict[str, object]:
    if path.is_symlink():
        raise RuntimeError(f"refusing symlinked academic JSON artifact: {path}")
    if not path.is_file():
        return {}
    value = json.loads(path.read_text(encoding="utf-8"))
    return value if isinstance(value, dict) else {}


def _load_retained_failures(
    phase_path: Path, run_summary: Mapping[str, object]
) -> list[dict[str, object]]:
    retained: list[dict[str, object]] = []
    latest = run_summary.get("failed", [])
    if isinstance(latest, list):
        retained.extend(dict(value) for value in latest if isinstance(value, Mapping))
    failure_dir = Path(phase_path) / "failures"
    if failure_dir.is_symlink():
        raise RuntimeError("refusing symlinked academic failure directory")
    if failure_dir.is_dir():
        if failure_dir.resolve().parent != Path(phase_path).resolve():
            raise RuntimeError("academic failure directory escapes the phase directory")
        for path in sorted(failure_dir.glob("*.json")):
            value = _optional_json(path)
            if value:
                retained.append(value)
    deduplicated: dict[str, dict[str, object]] = {}
    for value in retained:
        identity = json.dumps(value, sort_keys=True, separators=(",", ":"), ensure_ascii=False)
        deduplicated[identity] = value
    return list(deduplicated.values())


def _annotate_failure_resolution(
    failures: Sequence[Mapping[str, object]],
    cells: Sequence[Mapping[str, object]],
) -> list[dict[str, object]]:
    completed = {
        _failure_resolution_key(cell)
        for cell in cells
        if cell.get("status") == "complete"
    }
    annotated: list[dict[str, object]] = []
    for failure in failures:
        key = _failure_resolution_key(failure)
        annotated.append(
            {
                **dict(failure),
                "resolution_status": (
                    "resolved-by-authenticated-completion"
                    if key in completed
                    else "unresolved"
                ),
            }
        )
    return annotated


def _failure_resolution_key(record: Mapping[str, object]) -> tuple[object, ...]:
    if record.get("schema_version") in {
        "academic-cell-result-v2",
        "academic-cell-failure-v2",
    }:
        return (
            record.get("config_identity"),
            record.get("phase"),
            record.get("dataset"),
            record.get("model"),
            record.get("seed"),
            record.get("seed_position"),
            record.get("batch_id"),
            record.get("batch_position"),
            record.get("schedule_identity"),
        )
    return (
        record.get("dataset"),
        record.get("model"),
        record.get("seed"),
    )


def _slug(value: str) -> str:
    return "".join(character if character.isalnum() else "-" for character in value).strip("-")


__all__ = ["build_academic_report"]
