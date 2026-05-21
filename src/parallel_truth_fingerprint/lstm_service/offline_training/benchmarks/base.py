"""Benchmark adapter contract for the offline training track."""

from __future__ import annotations

from dataclasses import dataclass, field
from typing import Protocol, Sequence


@dataclass(frozen=True)
class BenchmarkData:
    """One loaded benchmark = sequences + labels + provenance.

    `sequences` is shape (n_samples, sequence_length, n_features) as a nested
    tuple of floats. `labels` is shape (n_samples,) integer class ids.
    `label_names` aligns positionally to the integer ids.
    `provenance` carries the dataset-version metadata mandated by NFR21
    (origin, year, version, citation, per-class counts).
    """

    name: str
    sequences: tuple[tuple[tuple[float, ...], ...], ...]
    labels: tuple[int, ...]
    label_names: tuple[str, ...]
    feature_count: int
    sequence_length: int
    provenance: dict[str, object] = field(default_factory=dict)


class BenchmarkAdapter(Protocol):
    """Every benchmark adapter implements this contract."""

    name: str

    def load(self, *, sequence_length: int, seed: int) -> BenchmarkData:
        """Load the benchmark and return labeled sequences.

        Implementations must be deterministic for a given seed and sequence
        length. They must not write to disk and must not perform any network
        I/O without explicit configuration.
        """


_REGISTRY: dict[str, BenchmarkAdapter] = {}


def register_benchmark(adapter: BenchmarkAdapter) -> None:
    _REGISTRY[adapter.name] = adapter


def list_available_benchmarks() -> Sequence[str]:
    return tuple(sorted(_REGISTRY))


def load_benchmark(
    name: str, *, sequence_length: int, seed: int
) -> BenchmarkData:
    if name not in _REGISTRY:
        raise ValueError(
            f"Unknown benchmark {name!r}. Available: {list_available_benchmarks()}"
        )
    return _REGISTRY[name].load(sequence_length=sequence_length, seed=seed)
