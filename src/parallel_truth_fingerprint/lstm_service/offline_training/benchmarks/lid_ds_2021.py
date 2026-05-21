"""LID-DS 2021 benchmark adapter for the offline training track.

LID-DS 2021 reference (NFR21 provenance evidence):
    Grimmer, M., Kaelble, F., et al. "LID-DS: A New Dataset for Linux
    Host-Based Intrusion Detection." (Updated 2021 release.) Hosted by the
    Database Systems group, Universitaet Leipzig, at
    `github.com/LID-DS/LID-DS`.

How to obtain the real dataset (out of band, once per developer machine):
    1. Clone or download the LID-DS 2021 release archive from the GitHub
       repository.
    2. Unzip into a root directory whose immediate subdirectories are
       scenario names (one CVE per scenario), each containing a `normal/`
       and an `attack/` subdirectory of .sc2 trace files.
    3. Either:
       - export LID_DS_2021_PATH=<absolute-path-to-root>
       - or pass `LidDs2021Benchmark(root_path=Path("..."))` explicitly.
"""

from __future__ import annotations

from dataclasses import dataclass, field
from pathlib import Path
import os

from parallel_truth_fingerprint.lstm_service.offline_training.benchmarks.base import (
    BenchmarkAdapter,
    BenchmarkData,
    register_benchmark,
)


@dataclass(frozen=True)
class LidDs2021Benchmark(BenchmarkAdapter):
    """LID-DS 2021 adapter producing fixed-length scaled syscall sequences."""

    name: str = "lid-ds-2021"
    root_path: Path | None = None
    _: dict = field(default_factory=dict)

    def load(self, *, sequence_length: int, seed: int) -> BenchmarkData:
        del seed  # no per-trace randomisation in this story
        if sequence_length <= 0:
            raise ValueError("sequence_length must be positive.")

        root = self._resolve_root_path()
        scenarios = self._list_scenarios(root)
        if not scenarios:
            raise RuntimeError(
                f"No LID-DS 2021 scenarios found under {root}. "
                "Verify the dataset layout."
            )

        # Label space: 0 = Normal (any scenario), then one attack class per
        # scenario in alphabetical order.
        label_names: list[str] = ["Normal"]
        scenario_label_ids: dict[str, int] = {}
        for index, scenario in enumerate(scenarios, start=1):
            label_names.append(f"{scenario}-attack")
            scenario_label_ids[scenario] = index

        sequences_int: list[list[int]] = []
        labels: list[int] = []
        for scenario in scenarios:
            scenario_dir = root / scenario
            normal_dir = scenario_dir / "normal"
            attack_dir = scenario_dir / "attack"
            if normal_dir.is_dir():
                for trace_path in sorted(normal_dir.iterdir()):
                    if trace_path.is_file():
                        parsed = self._parse_trace_file(trace_path)
                        if parsed:
                            sequences_int.append(parsed)
                            labels.append(0)
            if attack_dir.is_dir():
                for trace_path in sorted(attack_dir.iterdir()):
                    if trace_path.is_file():
                        parsed = self._parse_trace_file(trace_path)
                        if parsed:
                            sequences_int.append(parsed)
                            labels.append(scenario_label_ids[scenario])

        if not sequences_int:
            raise RuntimeError(
                f"No LID-DS 2021 traces parsed from {root}. "
                "Verify the .sc2 file format and folder layout."
            )

        max_syscall_id = max(max(trace) for trace in sequences_int)
        scaled_sequences = tuple(
            self._window_and_scale(
                trace,
                sequence_length=sequence_length,
                max_syscall_id=max_syscall_id,
            )
            for trace in sequences_int
        )

        per_class_counts = {name: 0 for name in label_names}
        for label_index in labels:
            per_class_counts[label_names[label_index]] += 1

        return BenchmarkData(
            name=self.name,
            sequences=scaled_sequences,
            labels=tuple(labels),
            label_names=tuple(label_names),
            feature_count=1,
            sequence_length=sequence_length,
            provenance={
                "origin": "LID-DS 2021",
                "year": 2021,
                "version": root.name,
                "citation": (
                    "Grimmer, M., Kaelble, F., et al. "
                    "'LID-DS: A New Dataset for Linux Host-Based "
                    "Intrusion Detection'. github.com/LID-DS/LID-DS, "
                    "2021 release."
                ),
                "feature_count": 1,
                "per_class_counts": per_class_counts,
                "max_syscall_id": int(max_syscall_id),
                "scenarios": tuple(scenarios),
            },
        )

    def _resolve_root_path(self) -> Path:
        if self.root_path is not None:
            return Path(self.root_path)
        env_path = os.environ.get("LID_DS_2021_PATH")
        if env_path:
            return Path(env_path)
        raise RuntimeError(
            "LID-DS 2021 root path is not configured. "
            "Set the LID_DS_2021_PATH environment variable to the directory "
            "containing one subdirectory per scenario, each with normal/ "
            "and attack/ subdirectories of .sc2 trace files, or pass "
            "root_path explicitly to LidDs2021Benchmark(root_path=...). "
            "See the module docstring for the official obtain-and-unzip steps."
        )

    @staticmethod
    def _list_scenarios(root: Path) -> list[str]:
        return sorted(
            child.name
            for child in root.iterdir()
            if child.is_dir()
            and (child / "normal").is_dir()
            and (child / "attack").is_dir()
        )

    @staticmethod
    def _parse_trace_file(trace_path: Path) -> list[int]:
        ints: list[int] = []
        for raw_line in trace_path.read_text(encoding="utf-8", errors="ignore").splitlines():
            stripped = raw_line.strip()
            if not stripped:
                continue
            first_token = stripped.split()[0]
            try:
                ints.append(int(first_token))
            except ValueError:
                continue
        return ints

    @staticmethod
    def _window_and_scale(
        trace: list[int],
        *,
        sequence_length: int,
        max_syscall_id: int,
    ) -> tuple[tuple[float, ...], ...]:
        truncated = list(trace[:sequence_length])
        if len(truncated) < sequence_length:
            truncated.extend([0] * (sequence_length - len(truncated)))
        scale = max(max_syscall_id, 1)
        return tuple((float(value) / scale,) for value in truncated)


register_benchmark(LidDs2021Benchmark())
