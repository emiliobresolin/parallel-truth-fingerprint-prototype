"""ADFA-LD benchmark adapter for the offline training track.

ADFA-LD reference (NFR21 provenance evidence):
    Creech, G., and Hu, J. "Generation of a New IDS Test Dataset: Time to
    Retire the KDD Collection". IEEE WCNC 2013.
    Host: UNSW Canberra Cyber, "ADFA Intrusion Detection Datasets".

How to obtain the real dataset (out of band, once per developer machine):
    1. Visit the UNSW Canberra Cyber dataset page for ADFA-LD.
    2. Download the archive (typically ADFA-LD.zip) and unzip it.
    3. The archive expands into three top-level subdirectories:
         - Training_Data_Master/
         - Validation_Data_Master/
         - Attack_Data_Master/<AttackName>/
       where <AttackName> is one of:
         Adduser, Hydra_FTP, Hydra_SSH, Java_Meterpreter, Web_Shell
       (folder names may include or omit underscores depending on the
       distribution; this adapter accepts both styles via
       `_ATTACK_DIRECTORY_ALIASES`).
    4. Either:
       - export ADFA_LD_PATH=<path-to-unzipped-root>
       - or pass `AdfaLdBenchmark(root_path=Path("..."))` explicitly.
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


ADFA_LD_LABEL_NAMES: tuple[str, ...] = (
    "Normal",
    "Adduser",
    "Hydra-FTP",
    "Hydra-SSH",
    "Java-Meterpreter",
    "Web-Shell",
)

# Attack subdirectory name PREFIXES tolerated under Attack_Data_Master/.
# Each tuple maps a label index (1..5) to a list of acceptable folder-name
# prefixes seen in different official distributions of ADFA-LD. The official
# 2013 archive groups traces under per-run subdirectories like
# `Adduser_1/`, `Adduser_2/`, ..., `Adduser_10/`; embedded test fixtures
# typically flatten that into a single `Adduser/` folder. Both layouts are
# detected: any directory whose name starts with one of the listed prefixes
# is treated as belonging to that attack class. `Meterpreter` collapses into
# the Java-Meterpreter class because the official 2013 archive uses both
# `Java_Meterpreter_*` and `Meterpreter_*` for the same attack vector.
_ATTACK_DIRECTORY_PREFIXES: dict[int, tuple[str, ...]] = {
    1: ("Adduser", "adduser"),
    2: ("Hydra_FTP", "Hydra-FTP", "hydra_ftp"),
    3: ("Hydra_SSH", "Hydra-SSH", "hydra_ssh"),
    4: (
        "Java_Meterpreter",
        "Java-Meterpreter",
        "java_meterpreter",
        "Meterpreter",
        "meterpreter",
    ),
    5: ("Web_Shell", "Web-Shell", "webshell"),
}

_NORMAL_DIRECTORIES: tuple[str, ...] = (
    "Training_Data_Master",
    "Validation_Data_Master",
)


@dataclass(frozen=True)
class AdfaLdBenchmark(BenchmarkAdapter):
    """ADFA-LD adapter producing fixed-length scaled syscall sequences."""

    name: str = "adfa-ld"
    root_path: Path | None = None
    _: dict = field(default_factory=dict)  # filler so dataclass accepts root_path keyword

    def load(self, *, sequence_length: int, seed: int) -> BenchmarkData:
        del seed  # Story 7.6 has no per-trace randomisation.
        if sequence_length <= 0:
            raise ValueError("sequence_length must be positive.")

        root = self._resolve_root_path()
        sequences_int, labels = self._load_raw_traces(root)
        if not sequences_int:
            raise RuntimeError(
                f"No ADFA-LD traces found under {root}. Verify the dataset layout."
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

        per_class_counts = {
            label_name: 0 for label_name in ADFA_LD_LABEL_NAMES
        }
        for label_index in labels:
            per_class_counts[ADFA_LD_LABEL_NAMES[label_index]] += 1

        return BenchmarkData(
            name=self.name,
            sequences=scaled_sequences,
            labels=tuple(labels),
            label_names=ADFA_LD_LABEL_NAMES,
            feature_count=1,
            sequence_length=sequence_length,
            provenance={
                "origin": "ADFA-LD",
                "year": 2013,
                "version": root.name,
                "citation": (
                    "Creech, G., and Hu, J. "
                    "'Generation of a New IDS Test Dataset: Time to Retire "
                    "the KDD Collection'. IEEE WCNC 2013."
                ),
                "feature_count": 1,
                "per_class_counts": per_class_counts,
                "max_syscall_id": int(max_syscall_id),
            },
        )

    def _resolve_root_path(self) -> Path:
        if self.root_path is not None:
            return Path(self.root_path)
        env_path = os.environ.get("ADFA_LD_PATH")
        if env_path:
            return Path(env_path)
        raise RuntimeError(
            "ADFA-LD root path is not configured. "
            "Set the ADFA_LD_PATH environment variable to the directory "
            "containing Training_Data_Master/, Validation_Data_Master/, "
            "and Attack_Data_Master/, or pass root_path explicitly to "
            "AdfaLdBenchmark(root_path=...). See the module docstring for "
            "the official obtain-and-unzip steps."
        )

    def _load_raw_traces(
        self, root: Path
    ) -> tuple[list[list[int]], list[int]]:
        sequences: list[list[int]] = []
        labels: list[int] = []

        # Normal traces (label 0) from both Training and Validation.
        for sub in _NORMAL_DIRECTORIES:
            directory = root / sub
            if not directory.is_dir():
                continue
            for trace_path in sorted(directory.iterdir()):
                if trace_path.is_file():
                    parsed = self._parse_trace_file(trace_path)
                    if parsed:
                        sequences.append(parsed)
                        labels.append(0)

        # Attack traces from Attack_Data_Master/<AttackName>[_<N>]/.
        # Supports both layouts:
        #   - flat (test fixtures):   Attack_Data_Master/Adduser/*.txt
        #   - real (UNSW 2013 zip):   Attack_Data_Master/Adduser_1/*.txt,
        #                             Attack_Data_Master/Adduser_2/*.txt, ...
        attack_root = root / "Attack_Data_Master"
        if attack_root.is_dir():
            for label_index, prefixes in _ATTACK_DIRECTORY_PREFIXES.items():
                for attack_dir in self._find_attack_directories(attack_root, prefixes):
                    for trace_path in sorted(attack_dir.iterdir()):
                        if trace_path.is_file():
                            parsed = self._parse_trace_file(trace_path)
                            if parsed:
                                sequences.append(parsed)
                                labels.append(label_index)

        return sequences, labels

    @staticmethod
    def _find_attack_directories(
        attack_root: Path, prefixes: tuple[str, ...]
    ) -> list[Path]:
        """Return every direct subdir of attack_root whose name matches one
        of the configured prefixes (exact match, prefix+underscore+digits,
        or prefix-dash variants). Sorted deterministically so per-class
        sample order does not depend on filesystem iteration order.
        """
        matches: list[Path] = []
        for child in sorted(attack_root.iterdir()):
            if not child.is_dir():
                continue
            name = child.name
            for prefix in prefixes:
                if name == prefix:
                    matches.append(child)
                    break
                if name.startswith(prefix + "_") or name.startswith(prefix + "-"):
                    suffix = name[len(prefix) + 1 :]
                    # Accept numeric suffixes (Adduser_1, Adduser_10) and
                    # also bare suffixes (Adduser_extra) which a few
                    # mirrors include.
                    if suffix.isdigit() or suffix.isalnum():
                        matches.append(child)
                        break
        return matches

    @staticmethod
    def _parse_trace_file(trace_path: Path) -> list[int]:
        content = trace_path.read_text(encoding="utf-8", errors="ignore")
        tokens = content.replace("\n", " ").split()
        ints: list[int] = []
        for token in tokens:
            try:
                ints.append(int(token))
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
        """Take the first `sequence_length` syscalls; right-pad with 0s.

        Story 7.6 uses a fixed leading-window rule. Story 7.9 may extend
        with sliding-window variants; the contract here intentionally
        keeps one window per trace so per-class counts stay predictable.
        """
        truncated = list(trace[:sequence_length])
        if len(truncated) < sequence_length:
            truncated.extend([0] * (sequence_length - len(truncated)))
        scale = max(max_syscall_id, 1)
        return tuple((float(value) / scale,) for value in truncated)


register_benchmark(AdfaLdBenchmark())
