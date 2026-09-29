"""Build thesis-ready Matrix V2 result tables from the completed V6 corpus.

This utility is intentionally read-only with respect to source evidence.  It
reads the authenticated V6 pilot artifacts and writes a dated reporting
package, keeping every source cell and its SHA-256 in the accompanying
manifest.
"""

from __future__ import annotations

import csv
import hashlib
import json
import math
from collections import defaultdict
from datetime import datetime, timezone
from pathlib import Path
from statistics import fmean, stdev
from typing import Any, Iterable


PROJECT_ROOT = Path(__file__).resolve().parents[1]
EXPERIMENT_ROOT = (
    PROJECT_ROOT
    / "evidence"
    / "academic"
    / "thesis-evaluation-v2"
    / "73c6eadb15c3c35a"
)
SOURCE_PHASE = EXPERIMENT_ROOT / "pilot"
SOURCE_CELLS = SOURCE_PHASE / "cells"
SOURCE_SUMMARY = SOURCE_PHASE / "run-summary.json"
REPORT_DIRECTORY = EXPERIMENT_ROOT / "reports"
THESIS_DOCUMENT = PROJECT_ROOT / "docs" / "matriz-v2-resultados-para-tese.md"

EXPECTED_CELL_COUNT = 23
T_CRITICAL_95 = {
    1: 12.706204736432095,
    2: 4.302652729749464,
    3: 3.182446305284263,
    4: 2.7764451051977987,
}

METRICS = (
    ("auroc", "AUROC"),
    ("auprc", "AUPRC"),
    ("balanced_accuracy", "Acurácia balanceada"),
    ("f1", "F1"),
    ("mcc", "MCC"),
)

DATASET_LABELS = {
    "adfa-ld": "ADFA-LD",
    "hai-23.05": "HAI 23.05",
    "lid-ds-2021": "LID-DS 2021",
}
MODEL_LABELS = {
    "categorical-unigram": "Unigrama categórico",
    "pca-autoencoder": "Autoencoder PCA",
    "recurrent-autoencoder": "Autoencoder recorrente",
    "robust-distance": "Distância robusta",
}
MODEL_ORDER = {
    "categorical-unigram": 0,
    "pca-autoencoder": 1,
    "robust-distance": 2,
    "recurrent-autoencoder": 3,
}


def _sha256(path: Path) -> str:
    return "sha256:" + hashlib.sha256(path.read_bytes()).hexdigest()


def _read_json(path: Path) -> dict[str, Any]:
    value = json.loads(path.read_text(encoding="utf-8"))
    if not isinstance(value, dict):
        raise ValueError(f"Expected an object in {path}")
    return value


def _finite(value: object) -> float | None:
    if isinstance(value, bool) or not isinstance(value, (int, float)):
        return None
    result = float(value)
    return result if math.isfinite(result) else None


def _fmt(value: float | None, digits: int = 4) -> str:
    return "—" if value is None else f"{value:.{digits}f}"


def _fmt_interval(summary: dict[str, Any], digits: int = 4) -> str:
    mean = _finite(summary.get("mean"))
    low = _finite(summary.get("ci_low"))
    high = _finite(summary.get("ci_high"))
    if low is None or high is None:
        return _fmt(mean, digits)
    return f"{_fmt(mean, digits)} [{_fmt(low, digits)}; {_fmt(high, digits)}]"


def _fmt_metric(summary: dict[str, Any], expected_executions: int) -> str:
    rendered = _fmt_interval(summary)
    metric_n = int(summary.get("n", 0))
    if metric_n and metric_n != expected_executions:
        return f"{rendered} (n={metric_n})"
    return rendered


def _fmt_mean_sd(summary: dict[str, Any], expected_executions: int) -> str:
    mean = _finite(summary.get("mean"))
    standard_deviation = _finite(summary.get("sd"))
    if mean is None:
        return "—"
    rendered = _fmt(mean)
    if standard_deviation is not None:
        rendered = f"{rendered} ± {_fmt(standard_deviation)}"
    metric_n = int(summary.get("n", 0))
    if metric_n and metric_n != expected_executions:
        rendered = f"{rendered} (n={metric_n})"
    return rendered


def _latex_escape(value: str) -> str:
    return (
        value.replace("\\", r"\textbackslash{}")
        .replace("&", r"\&")
        .replace("%", r"\%")
        .replace("_", r"\_")
        .replace("#", r"\#")
    )


def _summary(values: Iterable[object]) -> dict[str, Any]:
    numeric = [number for value in values if (number := _finite(value)) is not None]
    if not numeric:
        return {
            "mean": None,
            "sd": None,
            "n": 0,
            "ci_low": None,
            "ci_high": None,
            "ci_method": "sem valor finito",
        }
    mean = fmean(numeric)
    if len(numeric) == 1:
        return {
            "mean": mean,
            "sd": None,
            "n": 1,
            "ci_low": None,
            "ci_high": None,
            "ci_method": "uma execução",
        }
    sample_sd = stdev(numeric)
    critical = T_CRITICAL_95.get(len(numeric) - 1)
    if critical is None:
        raise ValueError("The reporting package expects at most five seeded runs.")
    half_width = critical * sample_sd / math.sqrt(len(numeric))
    return {
        "mean": mean,
        "sd": sample_sd,
        "n": len(numeric),
        "ci_low": mean - half_width,
        "ci_high": mean + half_width,
        "ci_method": f"IC95% t de Student entre sementes, gl={len(numeric) - 1}",
    }


def _source_records() -> tuple[list[dict[str, Any]], dict[str, Any], list[dict[str, str]]]:
    summary = _read_json(SOURCE_SUMMARY)
    source_paths = sorted(SOURCE_CELLS.glob("*.json"))
    if len(source_paths) != EXPECTED_CELL_COUNT:
        raise ValueError(
            f"Expected {EXPECTED_CELL_COUNT} source cells, found {len(source_paths)}."
        )
    if summary.get("complete_cell_count") != EXPECTED_CELL_COUNT:
        raise ValueError("The source run summary does not report 23 complete cells.")
    if summary.get("failed") != []:
        raise ValueError("The source run summary contains retained failures.")

    records: list[dict[str, Any]] = []
    source_manifest: list[dict[str, str]] = []
    observed_config_ids: set[str] = set()
    observed_cell_ids: set[str] = set()
    for path in source_paths:
        cell = _read_json(path)
        if cell.get("status") != "complete":
            raise ValueError(f"Source cell is not complete: {path.name}")
        if cell.get("phase") != "pilot":
            raise ValueError(f"Unexpected source phase in {path.name}")
        blind_gate = cell.get("blind_test_gate")
        if not isinstance(blind_gate, dict) or not (
            blind_gate.get("calibration_frozen_before_test_scoring") is True
            and blind_gate.get("test_truth_used_for_fit_preprocessing_stopping_or_calibration")
            is False
        ):
            raise ValueError(f"Blind-test gate failed in {path.name}")
        data = cell.get("data")
        if not isinstance(data, dict):
            raise ValueError(f"Missing data audit in {path.name}")
        leakage = data.get("group_leakage_audit")
        if not isinstance(leakage, dict) or leakage.get("passed") is not True:
            raise ValueError(f"Leakage audit failed in {path.name}")
        if cell.get("evidence_origin") != "official_native":
            raise ValueError(f"Unexpected evidence origin in {path.name}")

        test = cell.get("test")
        if not isinstance(test, dict):
            raise ValueError(f"Missing test record in {path.name}")
        ranking = test.get("ranking")
        operating = test.get("operating")
        support = operating.get("support") if isinstance(operating, dict) else None
        calibration = cell.get("threshold_calibration")
        fit = cell.get("model_fit")
        if not all(
            isinstance(value, dict)
            for value in (ranking, operating, support, calibration, fit)
        ):
            raise ValueError(f"Incomplete metrics in {path.name}")

        cell_id = str(cell.get("cell_id"))
        if cell_id in observed_cell_ids:
            raise ValueError(f"Duplicate cell id: {cell_id}")
        observed_cell_ids.add(cell_id)
        config_identity = str(cell.get("config_identity"))
        observed_config_ids.add(config_identity)
        record = {
            "cell_id": cell_id,
            "dataset": str(cell.get("dataset")),
            "dataset_key": str(cell.get("dataset_key")),
            "model": str(cell.get("model")),
            "deterministic": bool(cell.get("deterministic")),
            "seed": int(cell.get("seed")),
            "completed_at_utc": str(cell.get("completed_at_utc")),
            "config_identity": config_identity,
            "evidence_origin": str(cell.get("evidence_origin")),
            "test_normal": int(support.get("normal")),
            "test_attack": int(support.get("attack")),
            "test_total": int(support.get("total")),
            "auroc": _finite(ranking.get("auroc")),
            "auprc": _finite(ranking.get("auprc")),
            "balanced_accuracy": _finite(operating.get("balanced_accuracy")),
            "f1": _finite(operating.get("f1")),
            "mcc": _finite(operating.get("mcc")),
            "false_positive_rate": _finite(operating.get("false_positive_rate")),
            "false_negative_rate": _finite(operating.get("false_negative_rate")),
            "recall": _finite(operating.get("recall")),
            "precision": _finite(operating.get("precision")),
            "threshold": _finite(calibration.get("value")),
            "validation_target_fpr": _finite(calibration.get("objective_value")),
            "fit_cpu_seconds": _finite(fit.get("fit_cpu_seconds")),
            "fit_wall_seconds": _finite(fit.get("fit_wall_seconds")),
            "epochs_executed": int(fit.get("epochs_executed")),
            "source_file": path.relative_to(PROJECT_ROOT).as_posix(),
            "source_sha256": _sha256(path),
        }
        records.append(record)
        source_manifest.append(
            {
                "cell_id": cell_id,
                "path": record["source_file"],
                "sha256": record["source_sha256"],
            }
        )

    if len(observed_config_ids) != 1:
        raise ValueError("Source cells do not share one frozen configuration identity.")
    expected_ids = set(summary.get("completed_now", []))
    if expected_ids != observed_cell_ids:
        raise ValueError("Source cells disagree with the run summary inventory.")
    if summary.get("config_identity") not in observed_config_ids:
        raise ValueError("Source configuration identity disagrees with run summary.")
    return records, summary, source_manifest


def _aggregate_records(
    records: list[dict[str, Any]], summary: dict[str, Any]
) -> list[dict[str, Any]]:
    analysis = summary.get("analysis")
    if not isinstance(analysis, dict) or analysis.get("status") != "complete":
        raise ValueError("The source analysis is not complete.")
    groups = analysis.get("groups")
    if not isinstance(groups, dict):
        raise ValueError("The source analysis has no group summaries.")
    grouped: dict[tuple[str, str], list[dict[str, Any]]] = defaultdict(list)
    for record in records:
        grouped[(record["dataset"], record["model"])].append(record)

    aggregates: list[dict[str, Any]] = []
    for (dataset, model), entries in grouped.items():
        key = f"{dataset}/{model}"
        source_group = groups.get(key)
        if not isinstance(source_group, dict):
            raise ValueError(f"Missing source aggregate for {key}")
        source_metrics = source_group.get("metrics")
        if not isinstance(source_metrics, dict):
            raise ValueError(f"Missing source metrics for {key}")
        aggregate: dict[str, Any] = {
            "dataset": dataset,
            "model": model,
            "deterministic": bool(source_group.get("deterministic")),
            "executions": int(source_group.get("trial_count")),
            "seeds": [entry["seed"] for entry in sorted(entries, key=lambda item: item["seed"])],
            "test_normal": entries[0]["test_normal"],
            "test_attack": entries[0]["test_attack"],
            "test_total": entries[0]["test_total"],
            "fit_cpu_seconds": _summary(entry["fit_cpu_seconds"] for entry in entries),
            "fit_wall_seconds": _summary(entry["fit_wall_seconds"] for entry in entries),
            "false_positive_rate": _summary(
                entry["false_positive_rate"] for entry in entries
            ),
            "false_negative_rate": _summary(
                entry["false_negative_rate"] for entry in entries
            ),
            "recall": _summary(entry["recall"] for entry in entries),
            "precision": _summary(entry["precision"] for entry in entries),
        }
        if any(
            entry["test_normal"] != aggregate["test_normal"]
            or entry["test_attack"] != aggregate["test_attack"]
            for entry in entries
        ):
            raise ValueError(f"Test support changed within {key}")
        for metric, _ in METRICS:
            source_metric = source_metrics.get(metric)
            if not isinstance(source_metric, dict):
                raise ValueError(f"Missing {metric} aggregate for {key}")
            observed = _summary(entry[metric] for entry in entries)
            source_mean = _finite(source_metric.get("mean"))
            observed_mean = _finite(observed.get("mean"))
            if source_mean is not None and observed_mean is not None:
                if not math.isclose(source_mean, observed_mean, abs_tol=1e-12):
                    raise ValueError(f"Raw and source aggregate disagree for {key}/{metric}")
            aggregate[metric] = {
                "mean": source_mean,
                "sd": _finite(source_metric.get("sd")),
                "n": int(source_metric.get("n", 0)),
                "ci_low": _finite(source_metric.get("ci_low")),
                "ci_high": _finite(source_metric.get("ci_high")),
                "ci_method": str(source_metric.get("ci_method")),
            }
        aggregates.append(aggregate)
    return sorted(
        aggregates,
        key=lambda item: (item["dataset"], MODEL_ORDER.get(item["model"], 99)),
    )


def _markdown_table(rows: list[list[str]]) -> str:
    head, *body = rows
    rendered = ["| " + " | ".join(head) + " |"]
    rendered.append("| " + " | ".join("---" for _ in head) + " |")
    rendered.extend("| " + " | ".join(row) + " |" for row in body)
    return "\n".join(rendered)


def _result_table(aggregates: list[dict[str, Any]]) -> str:
    rows = [
        [
            "Base",
            "Modelo",
            "Execuções",
            "AUROC",
            "AUPRC",
            "Acurácia balanceada",
            "F1",
            "MCC",
            "FPR média",
            "FNR média",
        ]
    ]
    for item in aggregates:
        rows.append(
            [
                DATASET_LABELS.get(item["dataset"], item["dataset"]),
                MODEL_LABELS.get(item["model"], item["model"]),
                str(item["executions"]),
                _fmt_metric(item["auroc"], item["executions"]),
                _fmt_metric(item["auprc"], item["executions"]),
                _fmt_metric(item["balanced_accuracy"], item["executions"]),
                _fmt_metric(item["f1"], item["executions"]),
                _fmt_metric(item["mcc"], item["executions"]),
                _fmt(item["false_positive_rate"]["mean"]),
                _fmt(item["false_negative_rate"]["mean"]),
            ]
        )
    return _markdown_table(rows)


def _support_table(aggregates: list[dict[str, Any]]) -> str:
    seen: set[str] = set()
    rows = [["Base", "Normais no teste", "Ataques no teste", "Total"]]
    for item in aggregates:
        if item["dataset"] in seen:
            continue
        seen.add(item["dataset"])
        rows.append(
            [
                DATASET_LABELS.get(item["dataset"], item["dataset"]),
                str(item["test_normal"]),
                str(item["test_attack"]),
                str(item["test_total"]),
            ]
        )
    return _markdown_table(rows)


def _repetition_table(aggregates: list[dict[str, Any]]) -> str:
    rows = [
        [
            "Base",
            "n",
            "AUROC média ± DP",
            "IC95% AUROC",
            "AUPRC média ± DP",
            "Acurácia balanceada média ± DP",
            "F1 média ± DP",
        ]
    ]
    for item in aggregates:
        if item["deterministic"]:
            continue
        rows.append(
            [
                DATASET_LABELS.get(item["dataset"], item["dataset"]),
                str(item["executions"]),
                _fmt_mean_sd(item["auroc"], item["executions"]),
                _fmt_interval(item["auroc"]),
                _fmt_mean_sd(item["auprc"], item["executions"]),
                _fmt_mean_sd(item["balanced_accuracy"], item["executions"]),
                _fmt_mean_sd(item["f1"], item["executions"]),
            ]
        )
    return _markdown_table(rows)


def _seed_table(records: list[dict[str, Any]]) -> str:
    seeded = [record for record in records if not record["deterministic"]]
    rows = [
        [
            "Base",
            "Semente",
            "AUROC",
            "AUPRC",
            "Acurácia balanceada",
            "F1",
            "FPR",
            "FNR",
            "Épocas",
        ]
    ]
    for item in sorted(seeded, key=lambda value: (value["dataset"], value["seed"])):
        rows.append(
            [
                DATASET_LABELS.get(item["dataset"], item["dataset"]),
                str(item["seed"]),
                _fmt(item["auroc"]),
                _fmt(item["auprc"]),
                _fmt(item["balanced_accuracy"]),
                _fmt(item["f1"]),
                _fmt(item["false_positive_rate"]),
                _fmt(item["false_negative_rate"]),
                str(item["epochs_executed"]),
            ]
        )
    return _markdown_table(rows)


def _difference_table(summary: dict[str, Any]) -> str:
    analysis = summary["analysis"]
    comparisons = analysis.get("paired_comparisons", {})
    if not isinstance(comparisons, dict):
        return ""
    rows = [["Base", "Comparação", "Diferença de AUROC", "Leitura"]]
    for key, value in sorted(comparisons.items()):
        if not isinstance(value, dict) or "recurrent-autoencoder" not in key:
            continue
        dataset, comparison = key.split("/", 1)
        difference = _finite(value.get("mean_difference"))
        left, right = comparison.split("-vs-", 1)
        rows.append(
            [
                DATASET_LABELS.get(dataset, dataset),
                f"{MODEL_LABELS.get(left, left)} vs. {MODEL_LABELS.get(right, right)}",
                _fmt(difference),
                "diferença descritiva; sem p-valor",
            ]
        )
    return _markdown_table(rows)


def _write_csv(path: Path, records: list[dict[str, Any]], aggregates: list[dict[str, Any]]) -> None:
    path.parent.mkdir(parents=True, exist_ok=True)
    aggregate_columns = [
        "dataset",
        "dataset_label",
        "model",
        "model_label",
        "deterministic",
        "executions",
        "seeds",
        "test_normal",
        "test_attack",
        "test_total",
    ]
    for metric, _ in METRICS:
        aggregate_columns.extend(
            [f"{metric}_mean", f"{metric}_ci_low", f"{metric}_ci_high", f"{metric}_sd"]
        )
    for metric in ("false_positive_rate", "false_negative_rate", "recall", "precision"):
        aggregate_columns.extend(
            [f"{metric}_mean", f"{metric}_ci_low", f"{metric}_ci_high", f"{metric}_sd"]
        )
    with path.open("w", newline="", encoding="utf-8") as handle:
        writer = csv.DictWriter(handle, fieldnames=aggregate_columns)
        writer.writeheader()
        for item in aggregates:
            row: dict[str, Any] = {
                "dataset": item["dataset"],
                "dataset_label": DATASET_LABELS.get(item["dataset"], item["dataset"]),
                "model": item["model"],
                "model_label": MODEL_LABELS.get(item["model"], item["model"]),
                "deterministic": item["deterministic"],
                "executions": item["executions"],
                "seeds": ";".join(str(seed) for seed in item["seeds"]),
                "test_normal": item["test_normal"],
                "test_attack": item["test_attack"],
                "test_total": item["test_total"],
            }
            for metric, _ in METRICS:
                value = item[metric]
                row.update(
                    {
                        f"{metric}_mean": value["mean"],
                        f"{metric}_ci_low": value["ci_low"],
                        f"{metric}_ci_high": value["ci_high"],
                        f"{metric}_sd": value["sd"],
                    }
                )
            for metric in ("false_positive_rate", "false_negative_rate", "recall", "precision"):
                value = item[metric]
                row.update(
                    {
                        f"{metric}_mean": value["mean"],
                        f"{metric}_ci_low": value["ci_low"],
                        f"{metric}_ci_high": value["ci_high"],
                        f"{metric}_sd": value["sd"],
                    }
                )
            writer.writerow(row)

    raw_path = path.with_name("matrix-v2-resultados-por-execucao.csv")
    raw_columns = [
        "cell_id",
        "dataset",
        "model",
        "deterministic",
        "seed",
        "test_normal",
        "test_attack",
        "test_total",
        "auroc",
        "auprc",
        "balanced_accuracy",
        "f1",
        "mcc",
        "false_positive_rate",
        "false_negative_rate",
        "recall",
        "precision",
        "threshold",
        "validation_target_fpr",
        "fit_cpu_seconds",
        "fit_wall_seconds",
        "epochs_executed",
        "source_file",
        "source_sha256",
    ]
    with raw_path.open("w", newline="", encoding="utf-8") as handle:
        writer = csv.DictWriter(handle, fieldnames=raw_columns)
        writer.writeheader()
        for record in sorted(records, key=lambda item: item["cell_id"]):
            writer.writerow({column: record[column] for column in raw_columns})


def _write_latex(path: Path, aggregates: list[dict[str, Any]]) -> None:
    lines = [
        "% Gerado por scripts/build_thesis_result_cutoff.py; nao editar manualmente.",
        r"\begin{table}[htbp]",
        r"\centering",
        r"\caption{Matriz V2: resultados disponíveis na data de corte.}",
        r"\label{tab:matrix-v2-resultados-corte}",
        r"\begin{tabular}{llrrrrr}",
        r"\toprule",
        r"Base & Modelo & n & AUROC & AUPRC & Acc. bal. & F1 \\",
        r"\midrule",
    ]
    for item in aggregates:
        label = f"{DATASET_LABELS.get(item['dataset'], item['dataset'])}"
        model = MODEL_LABELS.get(item["model"], item["model"])
        lines.append(
            " & ".join(
                [
                    _latex_escape(label),
                    _latex_escape(model),
                    str(item["executions"]),
                    _fmt_metric(item["auroc"], item["executions"]),
                    _fmt_metric(item["auprc"], item["executions"]),
                    _fmt_metric(item["balanced_accuracy"], item["executions"]),
                    _fmt_metric(item["f1"], item["executions"]),
                ]
            )
            + r" \\")
    lines.extend(
        [
            r"\bottomrule",
            r"\end{tabular}",
            r"\begin{flushleft}",
            r"\footnotesize Valores entre colchetes sao IC95\% entre sementes quando ha mais de uma execucao finita; (n=3) identifica uma metrica indefinida em parte das sementes. Valores sem colchetes provem de uma unica execucao deterministica. As metricas sao calculadas no teste apos calibracao do limiar somente na validacao.",
            r"\end{flushleft}",
            r"\end{table}",
            "",
        ]
    )
    path.write_text("\n".join(lines), encoding="utf-8")


def _report_text(
    *,
    records: list[dict[str, Any]],
    aggregates: list[dict[str, Any]],
    summary: dict[str, Any],
    generated_at: str,
    excluded_cells: int,
) -> str:
    source_cpu_seconds = _finite(summary.get("elapsed_cpu_seconds")) or 0.0
    source_wall_seconds = _finite(summary.get("elapsed_seconds")) or 0.0
    result_table = _result_table(aggregates)
    recurrent = next(
        item
        for item in aggregates
        if item["dataset"] == "hai-23.05" and item["model"] == "recurrent-autoencoder"
    )
    adfa = next(
        item
        for item in aggregates
        if item["dataset"] == "adfa-ld" and item["model"] == "recurrent-autoencoder"
    )
    lid = next(
        item
        for item in aggregates
        if item["dataset"] == "lid-ds-2021" and item["model"] == "recurrent-autoencoder"
    )
    return f"""# Matriz V2 — resultados disponíveis na data de corte

Gerado em UTC: `{generated_at}`  
Fonte dos dados: `{SOURCE_PHASE.relative_to(PROJECT_ROOT).as_posix()}`  
Configuração: `{summary['config_identity']}`

## Decisão de corte e escopo

Este pacote fecha a coleta de resultados para a redação da tese na data indicada acima. Ele utiliza somente os **23 registros completos, autenticados e verificados** do corpus V6. Todos os registros têm origem `official_native`, validação de separação entre grupos aprovada e teste cego preservado: o limiar foi definido na validação antes da pontuação do teste.

As tabelas não estimam, preenchem nem misturam execuções ausentes. Há `{excluded_cells}` artefato(s) de uma execução interrompida fora deste conjunto; eles não são usados aqui. Assim, cada número abaixo pode ser rastreado a um arquivo de célula e à sua soma SHA-256 no manifesto.

## Base estatística da tese

Este corpus é a base estatística empírica da tese: os números são medições observadas nas execuções concluídas, não projeções. O autoencoder recorrente possui cinco repetições por base; para cada métrica, o relatório calcula média, desvio padrão e IC95% t de Student usando as sementes efetivamente executadas. As métricas de cada célula foram calculadas no teste mantido separado, depois que o limiar já estava congelado pela validação. Além disso, os artefatos de célula preservam reamostragem por unidade de teste com 2.000 repetições nas condições em que a unidade independente qualifica para esse cálculo.

Em outras palavras, a tese pode afirmar que apresenta **resultados estatísticos da Matriz V2 até a data de corte**. A inferência é sempre vinculada ao tamanho amostral executado: `n=5` para o autoencoder recorrente em cada base e `n=1` para cada método determinístico. A ausência de p-valor entre alguns métodos determinísticos não elimina as estatísticas existentes; ela apenas define que a comparação entre esses métodos deve permanecer descritiva.

## Desenho efetivamente executado

- Bases: ADFA-LD, HAI 23.05 e LID-DS 2021.
- Modelos: unigrama categórico quando aplicável, autoencoder PCA, distância robusta e autoencoder recorrente.
- Autoencoder recorrente: cinco execuções independentes por base, com sementes `101, 211, 307, 419, 523`.
- Modelos determinísticos: uma execução autenticada por combinação base/modelo.
- Métrica principal: AUROC. AUPRC, acurácia balanceada, F1, MCC, FPR e FNR complementam a leitura.

## Suporte de teste

{_support_table(aggregates)}

## Tabela principal de resultados

{result_table}

**Leitura da tabela:** valores entre colchetes são IC95% calculados entre as sementes do autoencoder recorrente. Valores sem colchetes vêm de uma execução determinística. Quando uma métrica não é definida em alguma semente, a tabela informa o `n` efetivamente usado para ela. FPR e FNR são médias para manter a tabela legível; os valores por semente estão na tabela seguinte. Esses formatos não devem ser confundidos: os intervalos entre sementes descrevem variação de treinamento; os arquivos de célula também preservam intervalos por unidade de teste.

## Estatísticas de repetição do autoencoder recorrente

{_repetition_table(aggregates)}

Esta tabela mostra a estatística calculada diretamente das repetições concluídas. Média, desvio padrão e IC95% usam as sementes que foram efetivamente executadas em cada base.

## Resultado do autoencoder recorrente por semente

{_seed_table(records)}

## Diferenças descritivas de AUROC

{_difference_table(summary)}

Estas diferenças mostram o que foi observado no conjunto executado. Não há p-valor nesta tabela porque as comparações incluem modelos determinísticos com uma única execução e, portanto, não formam pares estocásticos repetidos equivalentes.

## Limites que precisam aparecer na tese

- Os intervalos do autoencoder recorrente medem apenas a variação entre sementes. Eles não substituem o intervalo calculado pelas unidades de teste de cada célula.
- Em HAI 23.05, os blocos temporais não sobrepostos foram preservados, mas há somente duas gravações-fonte; por isso não há intervalo por agrupamento de gravações nessa base.
- F1 pode ficar indefinido quando uma execução não produz verdadeiro positivo; o símbolo `—` preserva essa informação e não deve ser trocado por zero.
- Como o intervalo t entre sementes não é limitado ao intervalo matemático da métrica, uma extremidade pode ultrapassar 0 ou 1. Os valores são mantidos sem recorte para não alterar o cálculo original.

## Texto curto para a seção de resultados da tese

> A Matriz V2 reuniu 23 execuções completas nas bases ADFA-LD, HAI 23.05 e LID-DS 2021. O autoencoder recorrente foi executado cinco vezes por base, com sementes previamente registradas, enquanto os métodos determinísticos foram ajustados uma vez por combinação. A métrica principal foi AUROC, calculada no conjunto de teste após o congelamento do limiar com dados de validação.

> Nos resultados disponíveis na data de corte, o autoencoder recorrente apresentou AUROC médio de {_fmt(adfa['auroc']['mean'])} no ADFA-LD (IC95% {_fmt(adfa['auroc']['ci_low'])}–{_fmt(adfa['auroc']['ci_high'])}), {_fmt(recurrent['auroc']['mean'])} no HAI 23.05 (IC95% {_fmt(recurrent['auroc']['ci_low'])}–{_fmt(recurrent['auroc']['ci_high'])}) e {_fmt(lid['auroc']['mean'])} no LID-DS 2021 (IC95% {_fmt(lid['auroc']['ci_low'])}–{_fmt(lid['auroc']['ci_high'])}). A tabela principal apresenta também AUPRC, acurácia balanceada, F1, MCC e as taxas de falso positivo e falso negativo para permitir a leitura conjunta de ordenação e operação no limiar calibrado.

> Os resultados devem ser interpretados no escopo das bases, das divisões e dos modelos efetivamente executados. As comparações com métodos determinísticos são apresentadas como diferenças descritivas, pois cada um deles possui uma única execução autenticada. Não se devem atribuir a este conjunto resultados de execuções que não foram concluídas.

## Nota de custo computacional

O corpus reportado consumiu `{source_cpu_seconds / 3600.0:.4f}` CPU-h e `{source_wall_seconds / 3600.0:.4f}` horas de relógio na execução que o produziu. Esse valor é apenas contexto de processamento; não é uma métrica de qualidade do detector.

## Reprodutibilidade

Execute:

```powershell
 .venv\\Scripts\\python.exe scripts\\build_thesis_result_cutoff.py
```

O comando relê as células-fonte, verifica inventário, estado, configuração, origem, separação de grupos e teste cego antes de reescrever as tabelas derivadas.
"""


def _thesis_text(report_relative_path: str) -> str:
    return f"""# Resultados da Matriz V2 para a tese

Use este documento junto com o relatório derivado em `{report_relative_path}`. O texto foi fechado a partir de 23 resultados completos disponíveis na data de corte; não incorpora valores previstos ou execuções interrompidas.

## Como apresentar o conjunto de dados

1. Diga que a Matriz V2 avaliou ADFA-LD, HAI 23.05 e LID-DS 2021.
2. Informe que o autoencoder recorrente foi repetido em cinco sementes e que os métodos determinísticos têm uma execução autenticada por combinação.
3. Defina AUROC como métrica principal e apresente AUPRC, acurácia balanceada, F1, MCC, FPR e FNR como métricas complementares.
4. Explique que a calibração do limiar ocorreu na validação e que o conjunto de teste foi pontuado somente depois disso.
5. Trate as diferenças que envolvem métodos de uma única execução como descritivas; não use p-valores inexistentes.
6. Em HAI 23.05, não apresente intervalo por agrupamento de gravações: há duas gravações-fonte, menos que o mínimo de cinco exigido para esse cálculo.

## Frase-base para metodologia

> Os resultados foram obtidos a partir de células autenticadas da Matriz V2. Para cada célula, o processamento foi ajustado com dados de treinamento, o limiar foi definido exclusivamente na validação e as métricas foram calculadas no teste mantido separado. O autoencoder recorrente foi repetido em cinco sementes fixas; os métodos determinísticos foram executados uma vez por combinação base/modelo.

## Frase-base para resultados

> A análise utilizou 23 execuções completas. A tabela de resultados apresenta, por base e modelo, AUROC, AUPRC, acurácia balanceada, F1, MCC, FPR e FNR. Para o autoencoder recorrente, os intervalos de 95% representam a variação observada entre as cinco sementes. Para modelos determinísticos, a tabela mostra o valor da execução autenticada.

## Frase-base para a base estatística

> Os resultados estatísticos da Matriz V2 foram calculados a partir de 23 execuções completas. Em cada base, o autoencoder recorrente foi repetido com cinco sementes fixas, permitindo estimar média, desvio padrão e intervalo de confiança de 95% entre sementes. As métricas foram obtidas no conjunto de teste separado após a calibração do limiar na validação; portanto, os valores apresentados correspondem às medições realizadas pelo experimento.

## Regra simples para não errar na redação

Escreva apenas o que a tabela mostra. Não complete células ausentes por média, não transforme diferenças descritivas em significância estatística e não apresente o custo de CPU como resultado de desempenho.
"""


def main() -> int:
    records, summary, source_manifest = _source_records()
    aggregates = _aggregate_records(records, summary)
    REPORT_DIRECTORY.mkdir(parents=True, exist_ok=True)
    confirmatory_cells = list((EXPERIMENT_ROOT / "confirmatory" / "cells").glob("*.json"))
    generated_at = datetime.now(timezone.utc).isoformat().replace("+00:00", "Z")

    report_path = REPORT_DIRECTORY / "matrix-v2-resultados-data-de-corte.md"
    aggregate_csv = REPORT_DIRECTORY / "matrix-v2-resultados-agregados.csv"
    latex_path = REPORT_DIRECTORY / "matrix-v2-tabela-resultados.tex"
    manifest_path = REPORT_DIRECTORY / "matrix-v2-resultados-data-de-corte.manifest.json"

    report_path.write_text(
        _report_text(
            records=records,
            aggregates=aggregates,
            summary=summary,
            generated_at=generated_at,
            excluded_cells=len(confirmatory_cells),
        ),
        encoding="utf-8",
    )
    _write_csv(aggregate_csv, records, aggregates)
    _write_latex(latex_path, aggregates)
    THESIS_DOCUMENT.write_text(
        _thesis_text(report_path.relative_to(PROJECT_ROOT).as_posix()),
        encoding="utf-8",
    )

    outputs = [
        report_path,
        aggregate_csv,
        aggregate_csv.with_name("matrix-v2-resultados-por-execucao.csv"),
        latex_path,
        THESIS_DOCUMENT,
    ]
    manifest = {
        "schema_version": "thesis-result-cutoff-v1",
        "generated_at_utc": generated_at,
        "reporting_status": "closed-for-thesis-writing",
        "collection_cutoff_decision": (
            "O titular do trabalho determinou o encerramento da coleta e o uso do "
            "corpus V6 disponível de 23 células completas para a redação da tese."
        ),
        "experiment_id": summary["experiment_id"],
        "source_phase": summary["phase"],
        "config_identity": summary["config_identity"],
        "source_run_summary": {
            "path": SOURCE_SUMMARY.relative_to(PROJECT_ROOT).as_posix(),
            "sha256": _sha256(SOURCE_SUMMARY),
            "analysis_input_identity": summary.get("analysis_input_identity"),
            "analysis_identity": summary.get("analysis_identity"),
        },
        "reported_cell_count": len(records),
        "reported_failure_count": 0,
        "excluded_non_source_cell_count": len(confirmatory_cells),
        "source_cells": source_manifest,
        "reporting_rules": [
            "Only complete source cells with status complete are included.",
            "No missing execution is estimated or added.",
            "Seeded summaries retain the original source aggregation and interval.",
            "Deterministic cells remain single authenticated executions.",
        ],
        "outputs": [
            {
                "path": output.relative_to(PROJECT_ROOT).as_posix(),
                "sha256": _sha256(output),
            }
            for output in outputs
        ],
    }
    manifest_path.write_text(
        json.dumps(manifest, ensure_ascii=False, indent=2) + "\n", encoding="utf-8"
    )
    print(report_path.relative_to(PROJECT_ROOT).as_posix())
    print(aggregate_csv.relative_to(PROJECT_ROOT).as_posix())
    print(latex_path.relative_to(PROJECT_ROOT).as_posix())
    print(THESIS_DOCUMENT.relative_to(PROJECT_ROOT).as_posix())
    print(manifest_path.relative_to(PROJECT_ROOT).as_posix())
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
