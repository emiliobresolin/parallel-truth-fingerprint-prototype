"""Dummy benchmark used only for Story 7.1 scaffolding smoke tests.

Generates a small, deterministic synthetic dataset with two classes so that
the CLI pipeline (load -> split -> fit -> evaluate -> record) can be
exercised end-to-end without depending on ADFA-LD or LID-DS 2021 yet.

This adapter is NOT a substitute for the real benchmarks declared in the
course-correction document; it exists only to keep Story 7.1 self-contained.
"""

from __future__ import annotations

import random
from dataclasses import dataclass

from parallel_truth_fingerprint.lstm_service.offline_training.benchmarks.base import (
    BenchmarkAdapter,
    BenchmarkData,
    register_benchmark,
)


@dataclass(frozen=True)
class DummyBenchmark(BenchmarkAdapter):
    name: str = "dummy"

    def load(self, *, sequence_length: int, seed: int) -> BenchmarkData:
        if sequence_length <= 0:
            raise ValueError("sequence_length must be positive.")
        rng = random.Random(seed)

        # Two-class synthetic problem: class 0 is a low-mean sequence, class 1
        # is a high-mean sequence. Just enough signal for a classifier to
        # learn but not enough to be confused with a real benchmark.
        per_class_samples = 16
        feature_count = 3
        sequences: list[tuple[tuple[float, ...], ...]] = []
        labels: list[int] = []
        for class_id, base in ((0, 0.0), (1, 1.0)):
            for _ in range(per_class_samples):
                sequence = tuple(
                    tuple(
                        base + rng.gauss(0.0, 0.05)
                        for _ in range(feature_count)
                    )
                    for _ in range(sequence_length)
                )
                sequences.append(sequence)
                labels.append(class_id)

        return BenchmarkData(
            name=self.name,
            sequences=tuple(sequences),
            labels=tuple(labels),
            label_names=("class_zero", "class_one"),
            feature_count=feature_count,
            sequence_length=sequence_length,
            provenance={
                "origin": "synthetic",
                "year": 2026,
                "version": "dummy-1.0",
                "purpose": "Story 7.1 scaffolding smoke harness",
            },
        )


register_benchmark(DummyBenchmark())
