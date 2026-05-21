"""Story 7.13: cross-benchmark comparative report.

Reads the persisted training history (Story 7.3 store) and produces a
single Markdown report with three sections:

    1. Champion run per benchmark (one row per benchmark).
    2. Per-class metrics for each champion.
    3. Dataset provenance footer.

The report does not train anything; if a benchmark has no persisted run,
the report records that fact explicitly and continues.
"""

from __future__ import annotations

from typing import Iterable

from parallel_truth_fingerprint.lstm_service.offline_training.registry.training_history import (
    list_training_runs,
    read_training_run,
)
from parallel_truth_fingerprint.lstm_service.offline_training.training.run import (
    TrainingRunRecord,
)


DEFAULT_BENCHMARKS: tuple[str, ...] = ("adfa-ld", "lid-ds-2021")


def build_cross_benchmark_report(
    *,
    artifact_store,
    benchmarks: Iterable[str] | None = None,
) -> str:
    benchmark_list = tuple(benchmarks) if benchmarks is not None else DEFAULT_BENCHMARKS

    champions_per_benchmark: dict[str, TrainingRunRecord | None] = {}
    for benchmark in benchmark_list:
        champions_per_benchmark[benchmark] = _pick_champion(
            artifact_store=artifact_store, benchmark=benchmark
        )

    sections: list[str] = []
    sections.append("# Cross-Benchmark Comparative Report\n")
    sections.append(_render_section_one(champions_per_benchmark))
    sections.append(_render_section_two(champions_per_benchmark))
    sections.append(_render_section_three(champions_per_benchmark))
    return "\n".join(sections)


def _pick_champion(
    *, artifact_store, benchmark: str
) -> TrainingRunRecord | None:
    run_ids = list_training_runs(
        artifact_store=artifact_store, benchmark=benchmark
    )
    if not run_ids:
        return None
    best: TrainingRunRecord | None = None
    for run_id in run_ids:
        record = read_training_run(run_id, artifact_store=artifact_store)
        if best is None or record.metrics.get(
            "macro_f1", 0.0
        ) > best.metrics.get("macro_f1", 0.0):
            best = record
    return best


def _render_section_one(
    champions: dict[str, TrainingRunRecord | None],
) -> str:
    lines = ["## Champion runs per benchmark\n"]
    lines.append(
        "| benchmark | model | run_id | macro_f1 | accuracy | "
        "macro_precision | macro_recall | parameter_count |"
    )
    lines.append(
        "| --- | --- | --- | ---: | ---: | ---: | ---: | ---: |"
    )
    for benchmark, champion in champions.items():
        if champion is None:
            lines.append(
                f"| {benchmark} | _No runs persisted for `{benchmark}` yet._ "
                "| -- | -- | -- | -- | -- | -- |"
            )
            continue
        lines.append(
            "| {benchmark} | {model} | {run_id} | "
            "{f1:.4f} | {acc:.4f} | {p:.4f} | {r:.4f} | {params} |".format(
                benchmark=benchmark,
                model=champion.model_name,
                run_id=champion.run_id,
                f1=champion.metrics.get("macro_f1", 0.0),
                acc=champion.metrics.get("accuracy", 0.0),
                p=champion.metrics.get("macro_precision", 0.0),
                r=champion.metrics.get("macro_recall", 0.0),
                params=champion.parameter_count,
            )
        )
    return "\n".join(lines) + "\n"


def _render_section_two(
    champions: dict[str, TrainingRunRecord | None],
) -> str:
    lines = ["## Per-class metrics\n"]
    for benchmark, champion in champions.items():
        if champion is None:
            continue
        lines.append(f"### {benchmark} -- {champion.model_name} -- {champion.run_id}\n")
        lines.append(
            "| class | precision | recall | f1 | support_train | support_test |"
        )
        lines.append(
            "| --- | ---: | ---: | ---: | ---: | ---: |"
        )
        precision = champion.per_class_metrics.get("precision", ())
        recall = champion.per_class_metrics.get("recall", ())
        f1 = champion.per_class_metrics.get("f1", ())
        split = champion.split_record
        support_train = (
            split.per_class_counts_train if split is not None else {}
        )
        support_test = (
            split.per_class_counts_test if split is not None else {}
        )
        class_count = max(len(precision), len(recall), len(f1))
        for class_id in range(class_count):
            lines.append(
                "| {cls} | {p:.4f} | {r:.4f} | {f:.4f} | {st} | {ste} |".format(
                    cls=class_id,
                    p=float(precision[class_id]) if class_id < len(precision) else 0.0,
                    r=float(recall[class_id]) if class_id < len(recall) else 0.0,
                    f=float(f1[class_id]) if class_id < len(f1) else 0.0,
                    st=support_train.get(class_id, 0),
                    ste=support_test.get(class_id, 0),
                )
            )
        lines.append("")
    return "\n".join(lines) + "\n"


def _render_section_three(
    champions: dict[str, TrainingRunRecord | None],
) -> str:
    """Pull provenance straight from the persisted champion record.

    The provenance snapshot was captured by `execute_training_run` at
    training time, so this section does not require the original
    benchmark env var to still be configured at report time.
    """
    lines = ["## Dataset provenance\n"]
    rendered_any = False
    for benchmark, champion in champions.items():
        if champion is None:
            continue
        provenance = champion.dataset_provenance or {}
        if not provenance:
            lines.append(
                f"- **{benchmark}**: provenance was not captured for this run."
            )
            rendered_any = True
            continue
        lines.append(
            "- **{name}** -- origin: {origin}, year: {year}, version: `{version}`. "
            "citation: {citation}".format(
                name=benchmark,
                origin=provenance.get("origin", "?"),
                year=provenance.get("year", "?"),
                version=provenance.get("version", "?"),
                citation=provenance.get("citation", "?"),
            )
        )
        rendered_any = True
    if not rendered_any:
        lines.append("_No benchmarks had persisted runs to provenance._")
    lines.append("")
    return "\n".join(lines) + "\n"
