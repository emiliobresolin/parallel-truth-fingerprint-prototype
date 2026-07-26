"""Embedding/sliding-window ADFA-LD adapters for the offline training track.

Story 7.9 (the original ADFA-LD adapter docstring) anticipated a
sliding-window variant. This module delivers it as a *separate* registered
benchmark so the original `adfa-ld` adapter (one fixed leading window per
trace, scaled-to-[0,1] single feature) stays bit-for-bit unchanged and all
its tests keep passing.

Two improvements over `adfa-ld`, both grounded in the gap analysis in
`_bmad-output/implementation-artifacts/real-data-evidence-2026-05-21.md`
(which named "more epochs, multi-feature inputs, syscall embeddings, and
sliding-window oversampling" as the route to the advisor's D6 metric bar):

1. **Raw integer syscall tokens** instead of a single normalised float.
   The values are emitted as integers (carried as floats to honour the
   `BenchmarkData.sequences` float contract). A paired embedding classifier
   (`models/embedding_classifiers.py`) consumes them through a Keras
   `Embedding` layer, which is the standard representation for syscall
   sequence classification and the single biggest lever over the
   normalised-scalar input that produced macro F1 ~= 0.18.

2. **Sliding windows over the whole trace** instead of only the first
   `sequence_length` syscalls. Each trace yields up to
   `max_windows_per_trace` evenly-spaced windows, so the model sees the
   full behavioural signature of a trace and minority attack classes get
   more representation.

Two registered names:

- ``adfa-ld-embed``         -> 6-class framing (Normal + 5 attack families),
                              faithful to ADFA-LD's labels.
- ``adfa-ld-embed-binary``  -> 2-class anomaly framing (Normal vs Attack),
                              which is exactly the prototype's runtime job
                              ("capture whatever could be wrong") and a
                              common, legitimate ADFA-LD evaluation.

Both reuse the real-data loader, layout detection, and provenance discipline
of `AdfaLdBenchmark`; only the windowing + label space + value encoding
change.
"""

from __future__ import annotations

from dataclasses import dataclass

from parallel_truth_fingerprint.lstm_service.offline_training.benchmarks.adfa_ld import (
    ADFA_LD_LABEL_NAMES,
    AdfaLdBenchmark,
)
from parallel_truth_fingerprint.lstm_service.offline_training.benchmarks.base import (
    BenchmarkData,
    register_benchmark,
)


BINARY_LABEL_NAMES: tuple[str, ...] = ("Normal", "Attack")


@dataclass(frozen=True)
class AdfaLdEmbeddingBenchmark(AdfaLdBenchmark):
    """ADFA-LD adapter emitting raw syscall tokens + sliding windows.

    `binary=False` keeps the 6-class label space; `binary=True` collapses
    every attack family into a single ``Attack`` class for the anomaly
    framing. `max_windows_per_trace` bounds the per-trace window count so the
    expanded sample set stays tractable for local CPU training.
    """

    name: str = "adfa-ld-embed"
    binary: bool = False
    max_windows_per_trace: int = 4
    # Normal traces are the easy majority class; one leading window per normal
    # trace (5,205 windows) is ample and keeps the attack minority from being
    # swamped 7:1. Attack traces (the minority) get the full sliding coverage
    # up to `max_windows_per_trace`. This both balances the label space and
    # keeps the expanded sample set small enough for local CPU training.
    normal_max_windows_per_trace: int = 1

    def load(self, *, sequence_length: int, seed: int) -> BenchmarkData:
        del seed  # deterministic: windowing is a fixed function of the trace.
        if sequence_length <= 0:
            raise ValueError("sequence_length must be positive.")
        if self.max_windows_per_trace <= 0:
            raise ValueError("max_windows_per_trace must be positive.")
        if self.normal_max_windows_per_trace <= 0:
            raise ValueError("normal_max_windows_per_trace must be positive.")

        root = self._resolve_root_path()
        sequences_int, raw_labels = self._load_raw_traces(root)
        if not sequences_int:
            raise RuntimeError(
                f"No ADFA-LD traces found under {root}. Verify the dataset layout."
            )

        max_syscall_id = max(max(trace) for trace in sequences_int)
        label_names = BINARY_LABEL_NAMES if self.binary else ADFA_LD_LABEL_NAMES

        windows: list[tuple[tuple[float, ...], ...]] = []
        window_labels: list[int] = []
        for trace, raw_label in zip(sequences_int, raw_labels):
            mapped_label = self._map_label(raw_label)
            # raw_label 0 == Normal in both framings.
            cap = (
                self.normal_max_windows_per_trace
                if raw_label == 0
                else self.max_windows_per_trace
            )
            for window in self._sliding_windows(trace, sequence_length, cap):
                # Raw integer token per timestep, carried as float to honour
                # the BenchmarkData float contract; the embedding model casts
                # back to an int index.
                windows.append(tuple((float(value),) for value in window))
                window_labels.append(mapped_label)

        per_class_counts = {label_name: 0 for label_name in label_names}
        for label_index in window_labels:
            per_class_counts[label_names[label_index]] += 1

        return BenchmarkData(
            name=self.name,
            sequences=tuple(windows),
            labels=tuple(window_labels),
            label_names=label_names,
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
                # vocab_size is the embedding input dimension the paired
                # classifier needs; +1 because syscall ids are 0-indexed.
                "vocab_size": int(max_syscall_id) + 1,
                "windowing": "sliding",
                "max_windows_per_trace": int(self.max_windows_per_trace),
                "normal_max_windows_per_trace": int(
                    self.normal_max_windows_per_trace
                ),
                "framing": "binary" if self.binary else "multiclass",
                "window_count": len(windows),
                "trace_count": len(sequences_int),
            },
        )

    def _map_label(self, raw_label: int) -> int:
        if not self.binary:
            return raw_label
        return 0 if raw_label == 0 else 1

    def _sliding_windows(
        self, trace: list[int], sequence_length: int, max_windows: int
    ) -> list[tuple[int, ...]]:
        """Return up to `max_windows` evenly-spaced windows of the trace.

        Traces shorter than `sequence_length` yield a single right-padded
        window (matching the leading-window behaviour for short traces).
        Longer traces are sampled at a stride that spreads the windows across
        the whole trace, so the head, middle, and tail of the behavioural
        signature are all represented. With `max_windows == 1` this collapses
        to the original leading-window rule.
        """
        length = len(trace)
        if length <= sequence_length:
            padded = list(trace) + [0] * (sequence_length - length)
            return [tuple(padded)]
        if max_windows == 1:
            return [tuple(trace[:sequence_length])]

        span = length - sequence_length
        denom = max(max_windows - 1, 1)
        stride = max(span // denom, 1)

        windows: list[tuple[int, ...]] = []
        start = 0
        while start + sequence_length <= length and len(windows) < max_windows:
            windows.append(tuple(trace[start : start + sequence_length]))
            start += stride
        # Guarantee the trailing window (covering the tail) is present.
        tail_start = length - sequence_length
        tail_window = tuple(trace[tail_start : tail_start + sequence_length])
        if tail_window not in windows:
            if len(windows) >= max_windows:
                windows[-1] = tail_window
            else:
                windows.append(tail_window)
        return windows


register_benchmark(AdfaLdEmbeddingBenchmark())
register_benchmark(
    AdfaLdEmbeddingBenchmark(name="adfa-ld-embed-binary", binary=True)
)
