"""Fail-closed preflight for a live evidence-generation run.

This command deliberately does not start the runtime, containers, or training.
It checks that the immutable prerequisites needed before producing comparison
numbers are present as real bytes rather than fixtures or Git-LFS pointers.
"""
from __future__ import annotations

import argparse
import json
from pathlib import Path
import sys


REPOSITORY_ROOT = Path(__file__).resolve().parents[1]
sys.path.insert(0, str(REPOSITORY_ROOT / "src"))

from parallel_truth_fingerprint.contracts.parameter_evidence import AccountabilityOutcome
from parallel_truth_fingerprint.evidence.parameter_evidence import (
    load_parameter_catalog,
    validate_parameter_gate,
)
from parallel_truth_fingerprint.evidence.source_catalog import load_source_catalog


def _is_lfs_pointer(path: Path) -> bool:
    try:
        return path.read_bytes()[:64].startswith(b"version https://git-lfs.github.com/spec")
    except OSError:
        return True


def _files(root: Path, names: tuple[str, ...]) -> list[str]:
    failures: list[str] = []
    for name in names:
        path = root / name
        if not path.is_file() or path.stat().st_size == 0 or _is_lfs_pointer(path):
            failures.append(str(path))
    return failures


def _complete_hai_root(candidates: tuple[Path, ...], names: tuple[str, ...]) -> tuple[Path, list[str]]:
    """Prefer a candidate with every required real file over an incomplete legacy tree."""

    checked = tuple((candidate, _files(candidate, names)) for candidate in candidates)
    complete = next(((candidate, missing) for candidate, missing in checked if not missing), None)
    if complete is not None:
        return complete
    existing = next(((candidate, missing) for candidate, missing in checked if candidate.is_dir()), None)
    return existing or checked[0]


def _qualified_lid_scenarios(root: Path) -> tuple[Path, ...]:
    """Return official or legacy-compatible LID scenarios with real traces.

    The official 2021 release deliberately keeps each recording in an archive
    (``.zip`` containing ``.sc``, ``.pcap``, ``.json`` and ``.res``).  It must
    not be mistaken for an incomplete download merely because no legacy
    ``.sc2`` files have been materialised beside the archives.
    """

    if not root.is_dir():
        return ()
    qualified: list[Path] = []
    for scenario in root.iterdir():
        if not scenario.is_dir():
            continue
        # Legacy fixture/adapter layout: scenario/{normal,attack}/*.sc2.
        normal = scenario / "normal"
        attack = scenario / "attack"
        normal_traces = tuple(normal.glob("*.sc2")) if normal.is_dir() else ()
        attack_traces = tuple(attack.glob("*.sc2")) if attack.is_dir() else ()
        legacy_complete = all(
            trace.is_file() and trace.stat().st_size > 0 and not _is_lfs_pointer(trace)
            for trace in (*normal_traces, *attack_traces)
        ) and bool(normal_traces and attack_traces)

        # Published LID-DS 2021 layout.  ``training`` and ``validation`` are
        # normal reference recordings; the test folders preserve the official
        # normal / mixed-normal-and-attack partition without inferring labels
        # from filenames.
        official_roles = (
            scenario / "training",
            scenario / "validation",
            scenario / "test" / "normal",
            scenario / "test" / "normal_and_attack",
        )
        # Do not enumerate and open every archive here: a real LID release has
        # tens of thousands of recordings and preflight must remain a quick,
        # non-destructive gate.  Full parsing validates every archive when the
        # selected execution partition is actually consumed.
        role_samples = tuple(next((path for path in role.rglob("*.zip") if path.is_file()), None) for role in official_roles)
        official_complete = all(role_samples) and all(
            archive.stat().st_size > 0 and not _is_lfs_pointer(archive)
            for archive in role_samples
            if archive is not None
        )
        if legacy_complete or official_complete:
            qualified.append(scenario)
    return tuple(sorted(qualified))


def _current_domain_gate() -> tuple[dict[str, object], list[str]]:
    """Validate the executable 4--20 mA authority, never the planning ledger."""

    catalog_path = REPOSITORY_ROOT / "docs/reference-archive/catalog/parameter-evidence-current-domain.v1.json"
    source_path = REPOSITORY_ROOT / "docs/reference-archive/catalog/source-catalog.v1.json"
    try:
        catalog = load_parameter_catalog(catalog_path.read_bytes())
        source = load_source_catalog(source_path.read_bytes())
        result = validate_parameter_gate(catalog, source, catalog.inventories[0], catalog.required_sets[0])
    except (IndexError, OSError, TypeError, ValueError) as exc:
        return {
            "catalog": str(catalog_path),
            "accountability_outcome": "unavailable",
            "reason": type(exc).__name__,
        }, ["CURRENT_DOMAIN_PARAMETER_GATE_UNAVAILABLE"]
    report = {
        "catalog": str(catalog_path),
        "gate_result_id": result.gate_result_id,
        "accountability_outcome": str(result.accountability_outcome),
        "violations": [item.to_dict() for item in result.violations],
    }
    return report, ([] if result.accountability_outcome == AccountabilityOutcome.ACCOUNTABLE
                    else ["CURRENT_DOMAIN_PARAMETER_GATE_BLOCKED"])


def qualify(*, project_root: Path) -> dict[str, object]:
    """Return a deterministic, non-authorizing readiness report."""
    hai_candidates = (
        project_root / "datasets" / "HAI-23.05" / "hai-23.05",
        project_root / "datasets" / "HAI-23.05-kaggle" / "hai-23.05",
    )
    hai_names = (
        "hai-train1.csv", "hai-train2.csv", "hai-train3.csv", "hai-train4.csv",
        "hai-test1.csv", "hai-test2.csv", "label-test1.csv", "label-test2.csv",
    )
    hai_root, hai_missing = _complete_hai_root(hai_candidates, hai_names)
    lid_candidates = (
        project_root / "datasets" / "LID-DS-2021-real",
        project_root / "datasets" / "LID-DS-2021",
    )
    lid_checked = tuple(
        (candidate, _qualified_lid_scenarios(candidate)) for candidate in lid_candidates
    )
    lid_complete = next(
        ((candidate, scenarios) for candidate, scenarios in lid_checked if scenarios),
        None,
    )
    lid_root, lid_scenarios = lid_complete or next(
        ((candidate, scenarios) for candidate, scenarios in lid_checked if candidate.is_dir()),
        lid_checked[-1],
    )
    def trace_count(scenario: Path) -> int:
        legacy = sum(
            1 for role in ("normal", "attack") for _ in (scenario / role).glob("*.sc2")
        )
        # For archive layouts this is a count of independently validated role
        # samples, not an invented total recording count.
        official = sum(
            1
            for role in (scenario / "training", scenario / "validation", scenario / "test" / "normal", scenario / "test" / "normal_and_attack")
            if next((path for path in role.rglob("*.zip") if path.is_file()), None) is not None
        )
        return legacy + official
    lid_trace_count = sum(trace_count(scenario) for scenario in lid_scenarios)
    current_domain, current_domain_blockers = _current_domain_gate()
    blockers: list[str] = []
    if hai_missing:
        blockers.append("HAI_23_05_OFFICIAL_BYTES_UNAVAILABLE")
    if not lid_scenarios:
        blockers.append("LID_DS_2021_OFFICIAL_BYTES_UNAVAILABLE")
    blockers.extend(current_domain_blockers)
    return {
        "schema_version": "LiveEvidencePreflight.v1",
        "authorization_effect": "none",
        "runtime_may_start": not blockers,
        "blockers": blockers,
        "hai_23_05": {"root": str(hai_root), "missing_or_lfs_files": hai_missing},
        "lid_ds_2021": {
            "root": str(lid_root),
            "trace_count": lid_trace_count,
            "trace_count_basis": "all legacy .sc2 traces plus one non-empty official ZIP sample per required role",
            "has_normal_and_attack_roles": bool(lid_scenarios),
            "qualified_scenarios": [scenario.name for scenario in lid_scenarios],
        },
        "autoencoder": {
            "required_runtime_setting": "DEMO_DISABLE_RUNTIME_AUTOENCODER=false",
            "reason": (
                "runtime LSTM autoencoder is the custom-dataset fingerprint "
                "stage; benchmark metrics remain separately labelled by source"
            ),
        },
        "current_domain_parameter_gate": current_domain,
    }


def main() -> None:
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument("--project-root", type=Path, default=Path(__file__).resolve().parents[1])
    args = parser.parse_args()
    report = qualify(project_root=args.project_root.resolve())
    print(json.dumps(report, indent=2, sort_keys=True))
    if not report["runtime_may_start"]:
        raise SystemExit(2)


if __name__ == "__main__":
    main()
