"""Run the isolated thesis-grade evaluation pipeline.

Examples:
    .venv\\Scripts\\python.exe scripts\\run_academic_experiments.py preflight
    .venv\\Scripts\\python.exe scripts\\run_academic_experiments.py run --phase pilot
    .venv\\Scripts\\python.exe scripts\\run_academic_experiments.py report --phase pilot
"""

from __future__ import annotations

import argparse
import json
import os
from pathlib import Path
import sys


PROJECT_ROOT = Path(__file__).resolve().parents[1]
SRC_ROOT = PROJECT_ROOT / "src"
if str(SRC_ROOT) not in sys.path:
    sys.path.insert(0, str(SRC_ROOT))
os.environ.setdefault("KERAS_BACKEND", "torch")

from parallel_truth_fingerprint.lstm_service.offline_training.academic_report import (  # noqa: E402
    build_academic_report,
)
from parallel_truth_fingerprint.lstm_service.offline_training.academic_runner import (  # noqa: E402
    academic_paths,
    confirmatory_budget_issue,
    load_academic_config,
    run_academic_phase,
    run_preflight,
)


DEFAULT_CONFIG = PROJECT_ROOT / "configs" / "experiments" / "thesis-evaluation-v2.json"


def build_parser() -> argparse.ArgumentParser:
    parser = argparse.ArgumentParser(
        description="Leakage-safe, resumable academic anomaly-detection evaluation."
    )
    parser.add_argument(
        "command",
        choices=("preflight", "run", "pilot", "confirmatory", "report", "all"),
    )
    parser.add_argument("--config", type=Path, default=DEFAULT_CONFIG)
    parser.add_argument("--phase", choices=("pilot", "confirmatory"), default="pilot")
    parser.add_argument("--dataset", action="append", default=[])
    parser.add_argument("--model", action="append", default=[])
    parser.add_argument(
        "--seed-batch",
        dest="seed_batch",
        type=int,
        choices=range(1, 6),
        help="Required v2 confirmatory positional batch (1 through 5).",
    )
    parser.add_argument(
        "--experiment-dir",
        type=Path,
        help="Optional experiment root used to verify report reconstruction location.",
    )
    parser.add_argument(
        "--allow-over-budget",
        action="store_true",
        help="Explicitly authorize a confirmatory run above the frozen CPU-hour review threshold.",
    )
    return parser


def main(argv: list[str] | None = None) -> int:
    args = build_parser().parse_args(argv)
    config = load_academic_config(args.config)
    if args.command == "pilot":
        args.phase = "pilot"
    elif args.command == "confirmatory":
        args.phase = "confirmatory"
    usage_issue = _usage_issue(args, config)
    if usage_issue is not None:
        print(usage_issue, file=sys.stderr)
        return 5
    if args.experiment_dir is not None:
        expected_parent = academic_paths(
            config, project_root=PROJECT_ROOT, phase=args.phase
        ).root.parent.resolve()
        if args.experiment_dir.resolve() not in {
            expected_parent,
            academic_paths(config, project_root=PROJECT_ROOT, phase=args.phase).root.resolve(),
        }:
            raise SystemExit(
                f"--experiment-dir does not match the frozen config: expected {expected_parent}"
            )
    preflight: dict[str, object] | None = None
    run_failed = False
    if args.command in {"preflight", "all"}:
        preflight = run_preflight(config, project_root=PROJECT_ROOT, phase=args.phase)
        print(json.dumps({"preflight_ready": preflight["ready"]}, indent=2))
        if not preflight["ready"]:
            print(
                "Preflight did not pass; inspect preflight.json. No experiment cells were run.",
                file=sys.stderr,
            )
            return 2
    if args.command in {"run", "pilot", "confirmatory", "all"}:
        is_v2_confirmatory = (
            config.get("schema_version") == "thesis-evaluation-config-v2"
            and args.phase == "confirmatory"
        )
        if is_v2_confirmatory:
            if preflight is None:
                preflight_path = academic_paths(
                    config, project_root=PROJECT_ROOT, phase=args.phase
                ).phase / "preflight.json"
                if preflight_path.is_file():
                    loaded = json.loads(preflight_path.read_text(encoding="utf-8"))
                    preflight = loaded if isinstance(loaded, dict) else None
            issue = _confirmatory_budget_issue(
                preflight, allow_over_budget=args.allow_over_budget
            )
            if issue is not None:
                print(issue, file=sys.stderr)
                return 4
        summary = run_academic_phase(
            config,
            project_root=PROJECT_ROOT,
            phase=args.phase,
            dataset_filter=args.dataset,
            model_filter=args.model,
            confirmatory_batch=args.seed_batch,
            allow_over_budget=args.allow_over_budget,
        )
        print(
            json.dumps(
                {
                    "seed_batch": summary.get("invocation_batch_id"),
                    "planned": summary["planned_cell_count"],
                    "completed_now": len(summary["completed_now"]),
                    "resumed": len(summary["resumed"]),
                    "failed": len(summary["failed"]),
                    "confirmatory_analysis_withheld": summary.get(
                        "confirmatory_analysis_withheld"
                    ),
                },
                indent=2,
            )
        )
        run_failed = bool(summary["failed"])
        if run_failed and args.command != "all":
            return 3
    if args.command in {"report", "all"}:
        report = build_academic_report(
            config, project_root=PROJECT_ROOT, phase=args.phase
        )
        print(str(report))
    paths = academic_paths(config, project_root=PROJECT_ROOT, phase=args.phase)
    print(str(paths.root))
    return 3 if run_failed else 0


def _usage_issue(
    args: argparse.Namespace, config: dict[str, object]
) -> str | None:
    """Reject ignored or unsafe option combinations before any artifact is written."""

    is_v2_confirmatory = (
        config.get("schema_version") == "thesis-evaluation-config-v2"
        and args.phase == "confirmatory"
    )
    if args.command == "all" and is_v2_confirmatory:
        return (
            "v2 confirmatory execution cannot use 'all': run 'preflight' once, then "
            "run 'confirmatory --seed-batch N' for batches 1 through 5 in order, and "
            "build the report only after the matrix is complete."
        )
    if args.command in {"preflight", "report"} and (args.dataset or args.model):
        return f"--dataset and --model are not consumed by the {args.command!r} command."
    if args.command in {"preflight", "report"} and args.seed_batch is not None:
        return f"--seed-batch is not consumed by the {args.command!r} command."
    if args.command in {"preflight", "report"} and args.allow_over_budget:
        return f"--allow-over-budget is not consumed by the {args.command!r} command."
    if is_v2_confirmatory and args.command in {"run", "confirmatory"}:
        if args.seed_batch is None:
            return "v2 confirmatory execution requires exactly one immutable --seed-batch (1..5)."
        if args.dataset or args.model:
            return "v2 confirmatory execution forbids --dataset and --model filters."
    elif args.seed_batch is not None:
        return "--seed-batch is valid only for v2 confirmatory execution."
    if args.allow_over_budget and not (
        is_v2_confirmatory and args.command in {"run", "confirmatory"}
    ):
        return "--allow-over-budget is valid only for v2 confirmatory execution."
    return None


def _confirmatory_budget_issue(
    preflight: dict[str, object] | None, *, allow_over_budget: bool = False
) -> str | None:
    return confirmatory_budget_issue(
        preflight,
        allow_over_budget=allow_over_budget,
        require_confirmatory=True,
    )


if __name__ == "__main__":
    raise SystemExit(main())
