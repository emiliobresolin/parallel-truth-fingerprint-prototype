"""Benchmark adapters for the offline training track.

Each adapter exposes a BenchmarkAdapter implementation with `load()` returning
labeled sequences plus dataset provenance metadata. The DummyBenchmark is
provided by Story 7.1 as a deterministic smoke harness; real adapters
(ADFA-LD, LID-DS 2021) are added in later stories.
"""

from parallel_truth_fingerprint.lstm_service.offline_training.benchmarks.base import (
    BenchmarkAdapter,
    BenchmarkData,
    list_available_benchmarks,
    load_benchmark,
)
from parallel_truth_fingerprint.lstm_service.offline_training.benchmarks.dummy import (
    DummyBenchmark,
)
# Side-effect: importing these modules registers AdfaLdBenchmark under
# `adfa-ld` and LidDs2021Benchmark under `lid-ds-2021` so
# `load_benchmark(...)` works downstream without explicit registration
# calls from callers.
from parallel_truth_fingerprint.lstm_service.offline_training.benchmarks import (
    adfa_ld as _adfa_ld_registration,  # noqa: F401
)
from parallel_truth_fingerprint.lstm_service.offline_training.benchmarks import (
    lid_ds_2021 as _lid_ds_2021_registration,  # noqa: F401
)
# Registers `adfa-ld-embed` (6-class) and `adfa-ld-embed-binary` (Normal vs
# Attack): raw syscall tokens + sliding windows for the embedding classifiers.
from parallel_truth_fingerprint.lstm_service.offline_training.benchmarks import (
    adfa_ld_embedding as _adfa_ld_embedding_registration,  # noqa: F401
)

__all__ = [
    "BenchmarkAdapter",
    "BenchmarkData",
    "DummyBenchmark",
    "list_available_benchmarks",
    "load_benchmark",
]
