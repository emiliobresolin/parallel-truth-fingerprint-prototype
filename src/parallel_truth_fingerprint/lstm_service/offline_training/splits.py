"""Stratified train/test split with seed-recorded provenance.

Implements the methodological discipline of Assis Section 3.3.1 (per-worker
local split before training) with the 80/20 ratio explicitly named by the
advisor in the 2026-05-21 orientation meeting (action M1). The seed and
per-class counts are recorded so a SplitRecord is sufficient to reproduce
the exact split.

This module deliberately depends only on the Python standard library.
The project has no sklearn dependency and we keep the offline training
track lean for that reason.
"""

from __future__ import annotations

from collections import Counter, defaultdict
from dataclasses import dataclass, field
from random import Random
from typing import Sequence


@dataclass(frozen=True)
class SplitRecord:
    """Reproducible provenance for one stratified split."""

    seed: int
    train_ratio: float
    total_samples: int
    train_samples: int
    test_samples: int
    per_class_counts_train: dict[int, int] = field(default_factory=dict)
    per_class_counts_test: dict[int, int] = field(default_factory=dict)


def stratified_train_test_split(
    sequences: Sequence[object],
    labels: Sequence[int],
    *,
    train_ratio: float = 0.8,
    seed: int,
) -> tuple[
    tuple[object, ...],
    tuple[int, ...],
    tuple[object, ...],
    tuple[int, ...],
    SplitRecord,
]:
    """Split labeled sequences into stratified train/test partitions.

    Per-class shuffling uses an isolated ``random.Random(seed)`` so the
    output is fully reproducible from ``(sequences, labels, train_ratio,
    seed)``.

    Stratification rule per class:
        - shuffle the indices of that class with the seeded RNG
        - choose ``round(count * train_ratio)`` as the train portion
        - clamp to leave at least 1 sample in train and at least 1 sample
          in test for every class

    Raises ``ValueError`` for empty inputs, mismatched lengths, classes
    with fewer than 2 samples, or train_ratio outside ``(0, 1)``.
    """

    if not (0.0 < train_ratio < 1.0):
        raise ValueError(
            f"train_ratio must be strictly between 0 and 1; got {train_ratio!r}."
        )
    if len(sequences) != len(labels):
        raise ValueError(
            f"sequences and labels must align: got {len(sequences)} vs {len(labels)}."
        )
    if not sequences:
        raise ValueError("Cannot split an empty dataset.")

    indices_per_class: dict[int, list[int]] = defaultdict(list)
    for index, label in enumerate(labels):
        indices_per_class[int(label)].append(index)

    for class_id, indices in indices_per_class.items():
        if len(indices) < 2:
            raise ValueError(
                f"Class {class_id!r} has only {len(indices)} sample(s); "
                "stratification requires at least 2."
            )

    rng = Random(seed)
    train_indices: list[int] = []
    test_indices: list[int] = []

    # Process classes in sorted order so the seeded RNG advances
    # deterministically regardless of dict iteration order.
    for class_id in sorted(indices_per_class):
        class_indices = list(indices_per_class[class_id])
        rng.shuffle(class_indices)
        count = len(class_indices)
        proposed_train = int(round(count * train_ratio))
        # Clamp to keep at least 1 in train and 1 in test.
        clamped_train = min(max(proposed_train, 1), count - 1)
        train_indices.extend(class_indices[:clamped_train])
        test_indices.extend(class_indices[clamped_train:])

    # Re-shuffle the combined train and test sets so consumers cannot rely
    # on class order, but keep the order deterministic for the seed.
    rng.shuffle(train_indices)
    rng.shuffle(test_indices)

    x_train = tuple(sequences[i] for i in train_indices)
    y_train = tuple(int(labels[i]) for i in train_indices)
    x_test = tuple(sequences[i] for i in test_indices)
    y_test = tuple(int(labels[i]) for i in test_indices)

    per_class_train = dict(Counter(y_train))
    per_class_test = dict(Counter(y_test))

    record = SplitRecord(
        seed=seed,
        train_ratio=train_ratio,
        total_samples=len(sequences),
        train_samples=len(y_train),
        test_samples=len(y_test),
        per_class_counts_train=per_class_train,
        per_class_counts_test=per_class_test,
    )
    return x_train, y_train, x_test, y_test, record
