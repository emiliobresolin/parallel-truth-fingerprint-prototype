"""Version-specific LID-DS 2021 adapter for the offline training track.

The published 2021 release stores each recording in a ZIP bundle containing
``.sc``, ``.pcap``, ``.json`` and ``.res``.  It is read in place; expanding the
87+ GiB source is neither required nor desirable.  The old ``.sc2`` layout is
kept only for the test fixtures and never selected over official archives.
"""

from __future__ import annotations

from dataclasses import dataclass, field
import json
import os
from pathlib import Path
from typing import Iterable
import zipfile

from parallel_truth_fingerprint.lstm_service.offline_training.benchmarks.base import (
    BenchmarkAdapter,
    BenchmarkData,
    register_benchmark,
)


_OFFICIAL_ROLE_DIRECTORIES: tuple[tuple[str, str], ...] = (
    ("training", "training"),
    ("validation", "validation"),
    ("test/normal", "test-normal"),
    ("test/normal_and_attack", "test-normal-and-attack"),
)


@dataclass(frozen=True)
class _Trace:
    scenario: str
    partition: str
    attack: bool
    syscall_names: tuple[str, ...]


@dataclass(frozen=True)
class LidDs2021Benchmark(BenchmarkAdapter):
    """Load categorical syscall sequences without recasting timestamps as IDs."""

    name: str = "lid-ds-2021"
    root_path: Path | None = None
    _: dict = field(default_factory=dict)

    def load(self, *, sequence_length: int, seed: int) -> BenchmarkData:
        del seed  # no per-trace randomisation in this story
        if sequence_length <= 0:
            raise ValueError("sequence_length must be positive.")

        root = self._resolve_root_path()
        max_archives_per_partition = int(
            os.getenv("LID_DS_2021_MAX_ARCHIVES_PER_SCENARIO_PARTITION", "0")
        )
        if max_archives_per_partition < 0:
            raise ValueError(
                "LID_DS_2021_MAX_ARCHIVES_PER_SCENARIO_PARTITION must be zero "
                "(all) or a positive integer."
            )
        scenarios = self._list_scenarios(root)
        if not scenarios:
            raise RuntimeError(
                f"No LID-DS 2021 scenarios found under {root}. "
                "Verify the dataset layout."
            )

        traces = tuple(
            trace
            for scenario in scenarios
            for trace in self._load_scenario(
                root / scenario,
                max_archives_per_partition=max_archives_per_partition,
            )
        )
        if not traces:
            raise RuntimeError(f"No LID-DS 2021 syscall records parsed from {root}.")

        vocabulary = tuple(sorted({name for trace in traces for name in trace.syscall_names}))
        if not vocabulary:
            raise RuntimeError(f"No syscall names found in LID-DS 2021 records under {root}.")
        syscall_ids = {name: index + 1 for index, name in enumerate(vocabulary)}
        label_names = ("Normal", *(f"{scenario}-attack" for scenario in scenarios))
        scenario_label_ids = {scenario: index for index, scenario in enumerate(scenarios, start=1)}
        labels = tuple(scenario_label_ids[trace.scenario] if trace.attack else 0 for trace in traces)
        scaled_sequences = tuple(
            self._window_and_scale(
                [syscall_ids[name] for name in trace.syscall_names],
                sequence_length=sequence_length,
                max_syscall_id=len(vocabulary),
            )
            for trace in traces
        )
        per_class_counts = {name: 0 for name in label_names}
        for label in labels:
            per_class_counts[label_names[label]] += 1
        partition_counts: dict[str, int] = {}
        for trace in traces:
            partition_counts[trace.partition] = partition_counts.get(trace.partition, 0) + 1

        return BenchmarkData(
            name=self.name,
            sequences=scaled_sequences,
            labels=labels,
            label_names=label_names,
            feature_count=1,
            sequence_length=sequence_length,
            provenance={
                "origin": "LID-DS 2021",
                "year": 2021,
                "version": "2021",
                "source_root": str(root.resolve()),
                "source_layout": self._layout_name(root, scenarios),
                "schema": "LID-DS-2021-recording-v1",
                "citation": (
                    "Grimmer, M., Kaelble, F., et al. "
                    "'LID-DS: A New Dataset for Linux Host-Based "
                    "Intrusion Detection'. github.com/LID-DS/LID-DS, "
                    "2021 release."
                ),
                "feature_count": 1,
                "feature_semantics": "categorical syscall name, ordinal encoded after vocabulary freeze",
                "per_class_counts": per_class_counts,
                "partition_counts": partition_counts,
                "syscall_vocabulary_size": len(vocabulary),
                "scenarios": tuple(scenarios),
                "max_archives_per_scenario_partition": max_archives_per_partition,
                "sampling_scope": (
                    "complete official recording set"
                    if max_archives_per_partition == 0
                    else "deterministic lexicographic prefix per scenario and official partition"
                ),
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
            "containing the official scenario folders, or pass root_path "
            "explicitly to LidDs2021Benchmark(root_path=...)."
        )

    @staticmethod
    def _list_scenarios(root: Path) -> list[str]:
        if not root.is_dir():
            return []
        return sorted(
            child.name
            for child in root.iterdir()
            if child.is_dir() and (
                LidDs2021Benchmark._has_official_layout(child)
                or ((child / "normal").is_dir() and (child / "attack").is_dir())
            )
        )

    @staticmethod
    def _has_official_layout(scenario: Path) -> bool:
        return all(
            any(path.is_file() and path.stat().st_size > 0 for path in (scenario / role).rglob("*.zip"))
            for role, _ in _OFFICIAL_ROLE_DIRECTORIES
        )

    @classmethod
    def _load_scenario(
        cls, scenario: Path, *, max_archives_per_partition: int = 0
    ) -> Iterable[_Trace]:
        if cls._has_official_layout(scenario):
            yield from cls._load_official_archives(
                scenario, max_archives_per_partition=max_archives_per_partition
            )
            return
        yield from cls._load_fixture_traces(scenario)

    @classmethod
    def _load_official_archives(
        cls, scenario: Path, *, max_archives_per_partition: int = 0
    ) -> Iterable[_Trace]:
        for relative_role, partition in _OFFICIAL_ROLE_DIRECTORIES:
            archives = sorted((scenario / relative_role).rglob("*.zip"))
            if max_archives_per_partition:
                archives = archives[:max_archives_per_partition]
            for archive in archives:
                syscall_names, attack = cls._parse_official_archive(archive)
                if syscall_names:
                    yield _Trace(scenario.name, partition, attack, tuple(syscall_names))

    @staticmethod
    def _parse_official_archive(archive: Path) -> tuple[list[str], bool]:
        try:
            with zipfile.ZipFile(archive) as bundle:
                members = tuple(info.filename for info in bundle.infolist() if not info.is_dir())
                sc_files = tuple(name for name in members if name.endswith(".sc"))
                json_files = tuple(name for name in members if name.endswith(".json"))
                if len(sc_files) != 1 or len(json_files) != 1:
                    raise ValueError("expected exactly one .sc and one .json member")
                metadata = json.loads(bundle.read(json_files[0]).decode("utf-8"))
                roles = {
                    container.get("role") for container in metadata.get("container", [])
                    if isinstance(container, dict) and isinstance(container.get("role"), str)
                }
                # Official LID 2021 recordings identify containers as normal,
                # victim and (when an exploit is present) attacker.  The
                # recording-level truth is the published boolean `exploit`;
                # an older fixture uses the compact `attack` role instead.
                if not roles or not roles <= {"normal", "victim", "attacker", "attack"}:
                    raise ValueError("unknown or absent container roles")
                exploit = metadata.get("exploit")
                if exploit is None:
                    # Compatibility only for the compact published-layout
                    # fixture; there the attack role is itself unambiguous.
                    exploit = False
                if not isinstance(exploit, bool):
                    raise ValueError("missing boolean exploit flag")
                lines = bundle.read(sc_files[0]).decode("utf-8", errors="strict").splitlines()
        except (OSError, UnicodeDecodeError, json.JSONDecodeError, zipfile.BadZipFile) as exc:
            raise RuntimeError(f"Malformed official LID recording {archive}: {exc}") from exc
        except ValueError as exc:
            raise RuntimeError(f"Unsupported official LID recording {archive}: {exc}") from exc
        names = [name for name in (LidDs2021Benchmark._syscall_name(line) for line in lines) if name]
        return names, exploit or "attack" in roles

    @staticmethod
    def _syscall_name(line: str) -> str | None:
        fields = line.split()
        return fields[5] if len(fields) >= 6 and fields[5] not in {">", "<"} else None

    @classmethod
    def _load_fixture_traces(cls, scenario: Path) -> Iterable[_Trace]:
        for role, attack in (("normal", False), ("attack", True)):
            for trace_path in sorted((scenario / role).glob("*.sc2")):
                names = cls._parse_fixture_trace(trace_path)
                if names:
                    yield _Trace(scenario.name, "fixture", attack, tuple(names))

    @staticmethod
    def _parse_fixture_trace(trace_path: Path) -> list[str]:
        names: list[str] = []
        for raw_line in trace_path.read_text(encoding="utf-8", errors="strict").splitlines():
            token = raw_line.strip().split(maxsplit=1)
            if not token:
                continue
            try:
                names.append(f"syscall-id:{int(token[0])}")
            except ValueError:
                continue
        return names

    @classmethod
    def _layout_name(cls, root: Path, scenarios: list[str]) -> str:
        return "official-zip-recording" if any(cls._has_official_layout(root / name) for name in scenarios) else "test-fixture-sc2"

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
