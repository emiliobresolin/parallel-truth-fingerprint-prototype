"""Native-schema HAI 23.05 benchmark adapter.

HAI stays a multivariate industrial-control dataset. Its published tag names
and numeric values are used directly; it is never relabelled as compressor
4--20 mA data. Labels are consumed only as targets from HAI's official test
label files. A bounded, deterministic reservoir keeps local CPU experiments
tractable and is recorded in provenance.
"""

from __future__ import annotations

from dataclasses import dataclass, field
import os
from pathlib import Path
import random
from typing import Iterator

from parallel_truth_fingerprint.evidence.hai_adapter import (
    Hai2305LayoutError,
    inspect_hai_23_05,
    iter_native_labels,
    iter_native_observations,
)
from parallel_truth_fingerprint.lstm_service.offline_training.benchmarks.base import (
    BenchmarkAdapter,
    BenchmarkData,
    register_benchmark,
)


_TRAIN_FILES = ("hai-train1.csv", "hai-train2.csv", "hai-train3.csv", "hai-train4.csv")
_TEST_LABEL_FILES = {
    "hai-test1.csv": "label-test1.csv",
    "hai-test2.csv": "label-test2.csv",
}


@dataclass(frozen=True)
class Hai2305Benchmark(BenchmarkAdapter):
    """Build native multivariate HAI windows for binary normal/attack training."""

    name: str = "hai-23.05"
    root_path: Path | None = None
    max_windows_per_class: int | None = None
    _: dict = field(default_factory=dict)

    def load(self, *, sequence_length: int, seed: int) -> BenchmarkData:
        if sequence_length <= 0:
            raise ValueError("sequence_length must be positive.")
        root = self._resolve_root_path()
        manifest = inspect_hai_23_05(root)
        cap = self.max_windows_per_class or int(
            os.getenv("HAI_MAX_WINDOWS_PER_CLASS", "1000")
        )
        if cap <= 0:
            raise ValueError("HAI_MAX_WINDOWS_PER_CLASS must be positive.")

        feature_names: tuple[str, ...] | None = None
        reservoirs: dict[int, list[tuple[tuple[float, ...], ...]]] = {0: [], 1: []}
        seen: dict[int, int] = {0: 0, 1: 0}
        rng = random.Random(seed)
        for file_name in _TRAIN_FILES:
            columns, windows = self._iter_file_windows(
                root / file_name, sequence_length=sequence_length, label_path=None
            )
            feature_names = self._require_consistent_schema(feature_names, columns, file_name)
            self._reservoir_add(windows, reservoirs, seen, cap, rng)
        for file_name, label_name in _TEST_LABEL_FILES.items():
            columns, windows = self._iter_file_windows(
                root / file_name,
                sequence_length=sequence_length,
                label_path=root / label_name,
            )
            feature_names = self._require_consistent_schema(feature_names, columns, file_name)
            self._reservoir_add(windows, reservoirs, seen, cap, rng)

        if feature_names is None or not reservoirs[0] or not reservoirs[1]:
            raise RuntimeError(
                "HAI-23.05 did not yield both Normal and Attack windows; "
                "check the official source or increase the sampling budget."
            )
        sequences = tuple(reservoirs[0] + reservoirs[1])
        labels = tuple([0] * len(reservoirs[0]) + [1] * len(reservoirs[1]))
        per_class_counts = {"Normal": len(reservoirs[0]), "Attack": len(reservoirs[1])}
        return BenchmarkData(
            name=self.name,
            sequences=sequences,
            labels=labels,
            label_names=("Normal", "Attack"),
            feature_count=len(feature_names),
            sequence_length=sequence_length,
            provenance={
                "origin": "HAI security dataset",
                "year": 2023,
                "version": "HAI-23.05",
                "source_root": str(root.resolve()),
                "schema": "HAI-23.05-native-multivariate-v1",
                "citation": "HIL-based Augmented ICS Security Dataset (HAI), 23.05 release.",
                "feature_semantics": "published native HAI tag values; no compressor or mA conversion",
                "feature_names": feature_names,
                "feature_count": len(feature_names),
                "per_class_counts": per_class_counts,
                "windows_seen_per_class": dict(seen),
                "max_windows_per_class": cap,
                "source_file_sha256": {
                    item.file_name: item.content_sha256
                    for item in (*manifest.observations, *manifest.labels)
                },
            },
        )

    def _resolve_root_path(self) -> Path:
        if self.root_path is not None:
            return Path(self.root_path)
        env_path = os.getenv("HAI_2305_PATH")
        if env_path:
            return Path(env_path)
        raise RuntimeError(
            "HAI-23.05 root is not configured. Set HAI_2305_PATH to the "
            "directory containing hai-train*.csv, hai-test*.csv and label-test*.csv."
        )

    @staticmethod
    def _require_consistent_schema(
        current: tuple[str, ...] | None,
        candidate: tuple[str, ...],
        file_name: str,
    ) -> tuple[str, ...]:
        if current is not None and current != candidate:
            raise Hai2305LayoutError(f"HAI feature schema changed in {file_name}")
        return candidate

    @staticmethod
    def _reservoir_add(
        windows: Iterator[tuple[int, tuple[tuple[float, ...], ...]]],
        reservoirs: dict[int, list[tuple[tuple[float, ...], ...]]],
        seen: dict[int, int],
        cap: int,
        rng: random.Random,
    ) -> None:
        for label, window in windows:
            seen[label] += 1
            target = reservoirs[label]
            if len(target) < cap:
                target.append(window)
                continue
            replace_at = rng.randrange(seen[label])
            if replace_at < cap:
                target[replace_at] = window

    @staticmethod
    def _iter_file_windows(
        path: Path,
        *,
        sequence_length: int,
        label_path: Path | None,
    ) -> tuple[tuple[str, ...], Iterator[tuple[int, tuple[tuple[float, ...], ...]]]]:
        observations = iter_native_observations(path)
        try:
            first_timestamp, first_tags = next(observations)
        except StopIteration as exc:
            raise Hai2305LayoutError(f"Empty HAI observation file: {path}") from exc
        columns = tuple(first_tags)

        def rows() -> Iterator[tuple[str, dict[str, float], int]]:
            if label_path is None:
                yield first_timestamp, first_tags, 0
                for timestamp, tags in observations:
                    yield timestamp, tags, 0
                return
            labels = iter_native_labels(label_path)
            try:
                label_timestamp, label = next(labels)
            except StopIteration as exc:
                raise Hai2305LayoutError(f"Empty HAI label file: {label_path}") from exc
            yield first_timestamp, first_tags, label
            for timestamp, tags in observations:
                try:
                    label_timestamp, label = next(labels)
                except StopIteration as exc:
                    raise Hai2305LayoutError(f"HAI labels ended before observations: {path}") from exc
                yield timestamp, tags, label
            try:
                next(labels)
            except StopIteration:
                return
            raise Hai2305LayoutError(f"HAI labels exceed observations: {path}")

        def windows() -> Iterator[tuple[int, tuple[tuple[float, ...], ...]]]:
            chunk: list[tuple[float, ...]] = []
            chunk_labels: list[int] = []
            for _, tags, label in rows():
                if tuple(tags) != columns:
                    raise Hai2305LayoutError(f"HAI feature schema changed within {path}")
                chunk.append(tuple(float(tags[name]) for name in columns))
                chunk_labels.append(label)
                if len(chunk) == sequence_length:
                    yield (1 if any(chunk_labels) else 0), tuple(chunk)
                    chunk = []
                    chunk_labels = []

        return columns, windows()


register_benchmark(Hai2305Benchmark())
