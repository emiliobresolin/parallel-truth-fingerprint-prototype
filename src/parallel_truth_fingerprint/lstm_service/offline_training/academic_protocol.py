"""Leakage-safe dataset protocols for thesis-grade experiments.

This module is deliberately separate from the historical benchmark adapters.
It assigns independent source units to train/validation/test *before* creating
windows, fits preprocessing on train only, and preserves the parent unit for
unit-level inference and uncertainty analysis.
"""

from __future__ import annotations

import csv
from dataclasses import dataclass, field
from datetime import datetime
from hashlib import sha256
import heapq
import json
import math
from pathlib import Path
from typing import Iterable, Iterator, Mapping, Sequence
import zipfile

import numpy as np

from parallel_truth_fingerprint.evidence.hai_adapter import inspect_hai_23_05
from parallel_truth_fingerprint.lstm_service.offline_training.benchmarks.adfa_ld import (
    _ATTACK_DIRECTORY_PREFIXES,
)
from parallel_truth_fingerprint.lstm_service.offline_training.benchmarks.lid_ds_2021 import (
    LidDs2021Benchmark,
)


PARTITIONS = ("train", "validation", "test")
PAD_TOKEN = "<PAD>"
UNKNOWN_TOKEN = "<UNK>"
EVIDENCE_ORIGINS = frozenset(
    {
        "official_native",
        "authentic_capture",
        "prototype_generated",
        "mock_parameterized",
        "measured",
        "test_fixture",
    }
)
OFFICIAL_DATASETS = frozenset({"adfa-ld", "lid-ds-2021", "hai-23.05"})
DISJOINT_PRIORITY_SLICES_V1 = "disjoint-priority-slices-v1"
DISJOINT_CONTENT_PRIORITY_SLICES_V2 = "disjoint-content-priority-slices-v2"
PHASE_ALLOCATION_METHODS = frozenset(
    {DISJOINT_PRIORITY_SLICES_V1, DISJOINT_CONTENT_PRIORITY_SLICES_V2}
)


def canonical_json_hash(value: object) -> str:
    payload = json.dumps(
        value, sort_keys=True, separators=(",", ":"), ensure_ascii=False
    ).encode("utf-8")
    return f"sha256:{sha256(payload).hexdigest()}"


def file_sha256(path: Path) -> str:
    digest = sha256()
    with Path(path).open("rb") as handle:
        for chunk in iter(lambda: handle.read(1024 * 1024), b""):
            digest.update(chunk)
    return f"sha256:{digest.hexdigest()}"


def _validate_evidence_origin(value: object, *, subject: str) -> str:
    if not isinstance(value, str) or value not in EVIDENCE_ORIGINS:
        raise ValueError(
            f"{subject} requires exactly one closed evidence_origin; got {value!r}."
        )
    return value


def _validate_binary_label(value: object, *, subject: str) -> int:
    """Validate a binary label before any potentially lossy integer cast."""

    if isinstance(value, (bool, np.bool_)):
        raise ValueError(f"{subject} must not use a Boolean as a binary label.")
    if isinstance(value, (int, np.integer)):
        normalized = int(value)
    elif isinstance(value, (float, np.floating)):
        numeric = float(value)
        if not math.isfinite(numeric):
            raise ValueError(f"{subject} contains a non-finite binary label.")
        if not numeric.is_integer():
            raise ValueError(f"{subject} contains a fractional binary label.")
        normalized = int(numeric)
    else:
        raise ValueError(
            f"{subject} binary label must be an integer-valued number, got {value!r}."
        )
    if normalized not in {0, 1}:
        raise ValueError(f"{subject} label must be binary (0 or 1).")
    return normalized


def _validated_binary_label_array(value: object, *, subject: str) -> np.ndarray:
    raw = np.asarray(value, dtype=object).reshape(-1)
    return np.asarray(
        [
            _validate_binary_label(item, subject=f"{subject}[{index}]")
            for index, item in enumerate(raw.tolist())
        ],
        dtype=np.int64,
    )


def _parse_lid_consumed_archive(archive: Path) -> tuple[list[str], bool, str]:
    """Read only the LID members consumed by the experiment and hash them.

    Official archives also contain packet captures.  Reading those multi-GB
    payloads solely to establish provenance makes preflight needlessly slow and
    can exhaust local storage caches.  The detector consumes exactly one
    syscall trace and one metadata document, so its source identity is the
    length-delimited hash of those two member payloads.
    """

    names, _, attack, detector_identity, _, _ = _project_lid_consumed_archive(
        archive,
        sequence_length=None,
        max_sequences=0,
        selection_seed=0,
        selection_identity=archive.name,
    )
    return names, attack, detector_identity


def _project_lid_consumed_archive(
    archive: Path,
    *,
    sequence_length: int | None,
    max_sequences: int,
    selection_seed: int,
    selection_identity: str,
) -> tuple[
    list[str],
    tuple[tuple[int, tuple[tuple[str, ...], ...]], ...],
    bool,
    str,
    str,
    int,
]:
    """Stream a recording and retain a deterministic sample of intact sequences."""

    if sequence_length is not None and sequence_length <= 0:
        raise ValueError("sequence_length must be positive when projecting LID recordings.")
    if max_sequences < 0:
        raise ValueError("max_sequences cannot be negative.")
    if sequence_length is not None and max_sequences == 0:
        raise ValueError("Projected LID recordings require a positive max_sequences cap.")

    all_names: list[str] = []
    retained: list[tuple[int, int, tuple[tuple[str, ...], ...]]] = []
    current: list[tuple[str, ...]] = []
    current_start = 0
    parsed_count = 0
    try:
        with zipfile.ZipFile(archive) as bundle:
            members = tuple(info for info in bundle.infolist() if not info.is_dir())
            sc_files = tuple(info for info in members if info.filename.endswith(".sc"))
            json_files = tuple(info for info in members if info.filename.endswith(".json"))
            if len(sc_files) != 1 or len(json_files) != 1:
                raise ValueError("expected exactly one .sc and one .json member")
            metadata_payload = bundle.read(json_files[0])
            metadata = json.loads(metadata_payload.decode("utf-8"))
            canonical_metadata = json.dumps(
                metadata, sort_keys=True, separators=(",", ":"), ensure_ascii=False
            ).encode("utf-8")
            source_digest = sha256(b"lid-consumed-members-v2\0")
            source_digest.update(int(sc_files[0].file_size).to_bytes(8, "big"))
            detector_digest = sha256(b"lid-detector-visible-syscall-stream-v2\0")
            with bundle.open(sc_files[0], "r") as syscall_handle:
                for raw_line in syscall_handle:
                    source_digest.update(raw_line)
                    try:
                        line = raw_line.decode("utf-8", errors="strict")
                    except UnicodeDecodeError as exc:
                        raise RuntimeError(
                            f"Malformed official LID recording {archive}: {exc}"
                        ) from exc
                    name = LidDs2021Benchmark._syscall_name(line)
                    if name is None:
                        continue
                    encoded_name = name.encode("utf-8")
                    detector_digest.update(len(encoded_name).to_bytes(8, "big"))
                    detector_digest.update(encoded_name)
                    if sequence_length is None:
                        all_names.append(name)
                    else:
                        if not current:
                            current_start = parsed_count
                        current.append((name,))
                        if len(current) == sequence_length:
                            _retain_lid_sequence(
                                retained,
                                start=current_start,
                                values=tuple(current),
                                cap=max_sequences,
                                seed=selection_seed,
                                identity=selection_identity,
                            )
                            current = []
                    parsed_count += 1
                if current:
                    _retain_lid_sequence(
                        retained,
                        start=current_start,
                        values=tuple(current),
                        cap=max_sequences,
                        seed=selection_seed,
                        identity=selection_identity,
                    )
            source_digest.update(len(canonical_metadata).to_bytes(8, "big"))
            source_digest.update(canonical_metadata)
    except RuntimeError:
        raise
    except (OSError, UnicodeDecodeError, json.JSONDecodeError, zipfile.BadZipFile) as exc:
        raise RuntimeError(f"Malformed official LID recording {archive}: {exc}") from exc
    except ValueError as exc:
        raise RuntimeError(f"Unsupported official LID recording {archive}: {exc}") from exc

    roles = {
        container.get("role")
        for container in metadata.get("container", [])
        if isinstance(container, dict) and isinstance(container.get("role"), str)
    }
    if not roles or not roles <= {"normal", "victim", "attacker", "attack"}:
        raise RuntimeError(
            f"Unsupported official LID recording {archive}: unknown or absent container roles"
        )
    exploit = metadata.get("exploit", False)
    if not isinstance(exploit, bool):
        raise RuntimeError(
            f"Unsupported official LID recording {archive}: missing boolean exploit flag"
        )
    sampled = tuple(
        (start, values)
        for _, start, values in sorted(retained, key=lambda item: item[1])
    )
    return (
        all_names,
        sampled,
        bool(exploit or "attack" in roles),
        f"sha256:{detector_digest.hexdigest()}",
        f"sha256:{source_digest.hexdigest()}",
        parsed_count,
    )


def _retain_lid_sequence(
    retained: list[tuple[int, int, tuple[tuple[str, ...], ...]]],
    *,
    start: int,
    values: tuple[tuple[str, ...], ...],
    cap: int,
    seed: int,
    identity: str,
) -> None:
    priority = _stable_priority(seed, f"{identity}:sequence:{start}")
    item = (-priority, start, values)
    if len(retained) < cap:
        heapq.heappush(retained, item)
    elif priority < -retained[0][0]:
        heapq.heapreplace(retained, item)


@dataclass(frozen=True)
class AcademicUnit:
    """One independent claim unit (trace, recording, or temporal block)."""

    unit_id: str
    group_id: str
    native_partition: str
    assigned_partition: str
    label: int
    class_name: str
    values: tuple[tuple[float | str, ...], ...]
    source_path: str
    source_sha256: str
    order: int = 0
    event_ids: tuple[str, ...] = ()
    sampled_sequences: tuple[
        tuple[int, tuple[tuple[float | str, ...], ...]], ...
    ] = ()
    evidence_origin: str = "test_fixture"
    resampling_cluster_id: str = ""

    def __post_init__(self) -> None:
        _validate_evidence_origin(self.evidence_origin, subject="AcademicUnit")
        if self.assigned_partition not in PARTITIONS:
            raise ValueError(
                f"AcademicUnit assigned_partition must be one of {PARTITIONS}: "
                f"{self.assigned_partition!r}."
            )
        _validate_binary_label(self.label, subject="AcademicUnit")
        if not self.unit_id or not self.group_id:
            raise ValueError("AcademicUnit unit_id and group_id must be non-empty.")

    @property
    def cluster_id(self) -> str:
        """Independent resampling cluster, conservative when dependence is known."""

        return self.resampling_cluster_id or self.unit_id

    @property
    def detector_input_identity(self) -> str:
        """Legacy hash of detector values and sampling positions, never truth."""

        return canonical_json_hash(
            {
                "values": self.values,
                "sampled_sequences": [
                    {"start": start, "values": values}
                    for start, values in self.sampled_sequences
                ],
            }
        )

    @property
    def detector_input_content_identity(self) -> str:
        """Hash detector-visible model values with non-model lineage omitted."""

        return canonical_json_hash(
            {
                "values": self.values,
                "sampled_sequences": [
                    values for _, values in self.sampled_sequences
                ],
            }
        )

    def model_input_identity_dict(self) -> dict[str, object]:
        """Identity projection safe to bind preprocessing/model fitting."""

        return {
            "unit_id": self.unit_id,
            "group_id": self.group_id,
            "native_partition": self.native_partition,
            "assigned_partition": self.assigned_partition,
            "detector_input_identity": self.detector_input_identity,
            "sampled_sequence_starts": [start for start, _ in self.sampled_sequences],
            "evidence_origin": self.evidence_origin,
        }

    def identity_dict(self) -> dict[str, object]:
        return {
            "unit_id": self.unit_id,
            "group_id": self.group_id,
            "native_partition": self.native_partition,
            "assigned_partition": self.assigned_partition,
            "label": self.label,
            "class_name": self.class_name,
            "source_path": self.source_path,
            "source_sha256": self.source_sha256,
            "order": self.order,
            "event_ids": list(self.event_ids),
            "sampled_sequence_starts": [start for start, _ in self.sampled_sequences],
            "sampled_sequence_lengths": [
                len(sequence) for _, sequence in self.sampled_sequences
            ],
            "detector_input_identity": self.detector_input_identity,
            "evidence_origin": self.evidence_origin,
            "resampling_cluster_id": self.cluster_id,
        }


@dataclass(frozen=True)
class AcademicDataset:
    name: str
    modality: str
    protocol: str
    units: tuple[AcademicUnit, ...]
    feature_names: tuple[str, ...]
    label_names: tuple[str, ...]
    source_manifest: dict[str, object]
    phase: str
    evidence_origin: str = "test_fixture"

    def __post_init__(self) -> None:
        _validate_evidence_origin(self.evidence_origin, subject="AcademicDataset")
        if self.name in OFFICIAL_DATASETS and self.evidence_origin != "official_native":
            raise ValueError(
                f"Official benchmark {self.name!r} requires evidence_origin='official_native'."
            )
        mismatched = sorted(
            unit.unit_id
            for unit in self.units
            if unit.evidence_origin != self.evidence_origin
        )
        if mismatched:
            raise ValueError(
                "AcademicDataset and every AcademicUnit must declare exactly the same "
                f"closed evidence_origin; mismatches: {mismatched[:5]}"
            )
        unit_ids = [unit.unit_id for unit in self.units]
        if len(unit_ids) != len(set(unit_ids)):
            raise ValueError("AcademicDataset unit_id values must be unique.")

    def partition(self, name: str) -> tuple[AcademicUnit, ...]:
        if name not in PARTITIONS:
            raise ValueError(f"Unknown academic partition: {name!r}.")
        return tuple(unit for unit in self.units if unit.assigned_partition == name)

    @property
    def identity(self) -> str:
        """Full result identity, including truth and provenance."""

        return canonical_json_hash(
            {
                "name": self.name,
                "modality": self.modality,
                "protocol": self.protocol,
                "phase": self.phase,
                "feature_names": self.feature_names,
                "units": [unit.identity_dict() for unit in self.units],
                "source_manifest": self.source_manifest,
                "evidence_origin": self.evidence_origin,
            }
        )

    @property
    def model_input_identity(self) -> str:
        """Label-, class-, and event-free identity for model lifecycle binding."""

        return canonical_json_hash(
            {
                "name": self.name,
                "modality": self.modality,
                "protocol": self.protocol,
                "phase": self.phase,
                "feature_names": self.feature_names,
                "units": [unit.model_input_identity_dict() for unit in self.units],
                "evidence_origin": self.evidence_origin,
            }
        )


@dataclass(frozen=True)
class AcademicWindow:
    window_id: str
    unit_id: str
    label: int
    class_name: str
    values: tuple[tuple[float | str, ...], ...]
    event_ids: tuple[str, ...]
    start: int
    evidence_origin: str = "test_fixture"
    cluster_id: str = ""

    def __post_init__(self) -> None:
        _validate_binary_label(self.label, subject="AcademicWindow")
        _validate_evidence_origin(self.evidence_origin, subject="AcademicWindow")


@dataclass(frozen=True)
class WindowedDataset:
    dataset_name: str
    modality: str
    sequence_length: int
    stride: int
    aggregation: str
    partitions: dict[str, tuple[AcademicWindow, ...]]
    identity: str
    training_identity: str = ""
    model_fit_identity: str = ""
    evidence_origin: str = "test_fixture"


@dataclass(frozen=True)
class PreprocessingState:
    modality: str
    method: str
    feature_names: tuple[str, ...]
    vocabulary: tuple[str, ...] = ()
    center: tuple[float, ...] = ()
    scale: tuple[float, ...] = ()
    clip: float | None = None
    identity: str = ""

    def to_dict(self) -> dict[str, object]:
        return {
            "modality": self.modality,
            "method": self.method,
            "feature_names": list(self.feature_names),
            "vocabulary": list(self.vocabulary),
            "center": list(self.center),
            "scale": list(self.scale),
            "clip": self.clip,
            "identity": self.identity,
        }


@dataclass(frozen=True)
class PreparedPartition:
    x: np.ndarray
    window_ids: tuple[str, ...]
    unit_ids: tuple[str, ...]
    labels: np.ndarray
    class_names: tuple[str, ...]
    event_ids: tuple[tuple[str, ...], ...]
    cluster_ids: tuple[str, ...] = ()
    evidence_origins: tuple[str, ...] = ()

    def __post_init__(self) -> None:
        labels = _validated_binary_label_array(
            self.labels, subject="PreparedPartition.labels"
        )
        if labels.size != len(self.window_ids):
            raise ValueError("PreparedPartition labels and window_ids must align.")


@dataclass(frozen=True)
class PreparedDataset:
    dataset: AcademicDataset
    windowed: WindowedDataset
    preprocessing: PreprocessingState
    partitions: dict[str, PreparedPartition]


def load_academic_dataset(
    name: str,
    config: Mapping[str, object],
    *,
    project_root: Path,
    phase: str,
) -> AcademicDataset:
    """Load selected official units under a dataset-specific protocol."""

    if phase not in {"pilot", "confirmatory"}:
        raise ValueError("phase must be 'pilot' or 'confirmatory'.")
    kind = str(config.get("kind", name))
    root = _resolve_path(project_root, str(config.get("root", "")))
    if kind == "adfa-ld":
        return _load_adfa_ld(root, config, phase=phase)
    if kind == "lid-ds-2021":
        return _load_lid_ds_2021(root, config, phase=phase)
    if kind == "hai-23.05":
        return _load_hai_23_05(root, config, phase=phase)
    raise ValueError(f"Unsupported academic dataset kind: {kind!r}.")


def window_dataset(
    dataset: AcademicDataset,
    *,
    sequence_length: int,
    stride: int,
    max_windows_per_unit: int,
    aggregation: str,
) -> WindowedDataset:
    """Create windows strictly inside already assigned source units."""

    if sequence_length <= 0 or stride <= 0 or max_windows_per_unit <= 0:
        raise ValueError("sequence_length, stride, and max_windows_per_unit must be positive.")
    if aggregation not in {"max", "mean", "p95"}:
        raise ValueError("aggregation must be one of: max, mean, p95.")
    partitions: dict[str, tuple[AcademicWindow, ...]] = {}
    identity_rows: list[dict[str, object]] = []
    for partition in PARTITIONS:
        windows: list[AcademicWindow] = []
        for unit in dataset.partition(partition):
            if unit.sampled_sequences:
                if len(unit.sampled_sequences) > max_windows_per_unit:
                    raise ValueError(
                        f"Unit {unit.unit_id!r} contains more sampled sequences than permitted."
                    )
                candidates = tuple(
                    (
                        raw_start,
                        _pad_single_sequence(values, sequence_length=sequence_length),
                    )
                    for raw_start, values in unit.sampled_sequences
                )
            else:
                candidates = tuple(
                    _sliding_windows(
                        unit.values,
                        sequence_length=sequence_length,
                        stride=stride,
                        max_windows=max_windows_per_unit,
                    )
                )
            for start, values in candidates:
                window_id = f"{unit.unit_id}::window-{start:09d}"
                windows.append(
                    AcademicWindow(
                        window_id=window_id,
                        unit_id=unit.unit_id,
                        label=unit.label,
                        class_name=unit.class_name,
                        values=values,
                        event_ids=unit.event_ids,
                        start=start,
                        evidence_origin=unit.evidence_origin,
                        cluster_id=unit.cluster_id,
                    )
                )
                identity_rows.append(
                    {
                        "window_id": window_id,
                        "unit_id": unit.unit_id,
                        "partition": partition,
                        "start": start,
                    }
                )
        partitions[partition] = tuple(windows)
    audit = audit_window_parentage(dataset, partitions)
    if not audit["passed"]:
        raise RuntimeError(f"Post-split window leakage detected: {audit['violations']}")
    window_parameters = {
        "sequence_length": sequence_length,
        "stride": stride,
        "max_windows_per_unit": max_windows_per_unit,
        "aggregation": aggregation,
    }
    identity = canonical_json_hash(
        {
            "dataset_model_input_identity": dataset.model_input_identity,
            **window_parameters,
            "windows": identity_rows,
        }
    )
    training_identity = canonical_json_hash(
        {
            "dataset": dataset.name,
            "phase": dataset.phase,
            "units": [
                unit.model_input_identity_dict() for unit in dataset.partition("train")
            ],
            **window_parameters,
            "windows": [row for row in identity_rows if row["partition"] == "train"],
        }
    )
    model_fit_identity = canonical_json_hash(
        {
            "dataset": dataset.name,
            "phase": dataset.phase,
            "units": [
                unit.model_input_identity_dict()
                for partition in ("train", "validation")
                for unit in dataset.partition(partition)
            ],
            **window_parameters,
            "windows": [
                row
                for row in identity_rows
                if row["partition"] in {"train", "validation"}
            ],
        }
    )
    return WindowedDataset(
        dataset_name=dataset.name,
        modality=dataset.modality,
        sequence_length=sequence_length,
        stride=stride,
        aggregation=aggregation,
        partitions=partitions,
        identity=identity,
        training_identity=training_identity,
        model_fit_identity=model_fit_identity,
        evidence_origin=dataset.evidence_origin,
    )


def fit_preprocessing(
    dataset: AcademicDataset,
    windowed: WindowedDataset,
    *,
    clip: float = 10.0,
) -> PreprocessingState:
    """Fit categorical vocabulary or numeric scaling on train windows only."""

    train = windowed.partitions["train"]
    if not train:
        raise ValueError("Cannot fit preprocessing without train windows.")
    if any(window.label != 0 for window in train):
        raise ValueError("Academic anomaly detectors require normal-only training units.")
    validation = windowed.partitions["validation"]
    if any(window.label != 0 for window in validation):
        raise ValueError(
            "Academic reconstruction early-stopping validation must be normal-only."
        )
    if not isinstance(clip, (int, float)) or isinstance(clip, bool):
        raise ValueError("Preprocessing clip must be a finite positive number.")
    if not math.isfinite(float(clip)) or float(clip) <= 0.0:
        raise ValueError("Preprocessing clip must be a finite positive number.")
    if dataset.modality == "categorical-syscall":
        source_tokens = {
            str(value)
            for unit in dataset.partition("train")
            for row in unit.values
            for value in row
        }
        reserved = sorted(source_tokens & {PAD_TOKEN, UNKNOWN_TOKEN})
        if reserved:
            raise ValueError(
                "Training categorical values collide with reserved preprocessing "
                f"tokens: {reserved}."
            )
        raw_tokens = {
            str(value)
            for window in train
            for row in window.values
            for value in row
            if str(value) != PAD_TOKEN
        }
        observed = sorted(raw_tokens)
        vocabulary = (PAD_TOKEN, UNKNOWN_TOKEN, *observed)
        payload = {
            "modality": dataset.modality,
            "method": "train-only-categorical-vocabulary-v1",
            "feature_names": dataset.feature_names,
            "vocabulary": vocabulary,
            "training_window_identity": windowed.training_identity,
        }
        return PreprocessingState(
            modality=dataset.modality,
            method="train-only-categorical-vocabulary-v1",
            feature_names=dataset.feature_names,
            vocabulary=tuple(vocabulary),
            identity=canonical_json_hash(payload),
        )
    if dataset.modality == "numeric-multivariate":
        raw = np.asarray([window.values for window in train], dtype=np.float64)
        if raw.size == 0 or not np.all(np.isfinite(raw)):
            raise ValueError("Numeric training features must be non-empty and finite.")
        flattened_rows = raw.reshape(-1, raw.shape[-1])
        center = np.mean(flattened_rows, axis=0)
        scale = np.std(flattened_rows, axis=0)
        scale = np.where(scale < 1e-12, 1.0, scale)
        payload = {
            "modality": dataset.modality,
            "method": "train-only-standardization-v1",
            "feature_names": dataset.feature_names,
            "center": center.tolist(),
            "scale": scale.tolist(),
            "clip": clip,
            "training_window_identity": windowed.training_identity,
        }
        return PreprocessingState(
            modality=dataset.modality,
            method="train-only-standardization-v1",
            feature_names=dataset.feature_names,
            center=tuple(float(value) for value in center.tolist()),
            scale=tuple(float(value) for value in scale.tolist()),
            clip=float(clip),
            identity=canonical_json_hash(payload),
        )
    raise ValueError(f"Unsupported modality: {dataset.modality!r}.")


def prepare_dataset_arrays(
    dataset: AcademicDataset,
    windowed: WindowedDataset,
    preprocessing: PreprocessingState,
) -> PreparedDataset:
    partitions: dict[str, PreparedPartition] = {}
    for partition in PARTITIONS:
        windows = windowed.partitions[partition]
        if not windows:
            feature_count = len(dataset.feature_names)
            dtype = np.int32 if dataset.modality == "categorical-syscall" else np.float32
            x = np.empty((0, windowed.sequence_length, feature_count), dtype=dtype)
        elif dataset.modality == "categorical-syscall":
            lookup = {token: index for index, token in enumerate(preprocessing.vocabulary)}
            if lookup.get(PAD_TOKEN) != 0 or lookup.get(UNKNOWN_TOKEN) != 1:
                raise ValueError(
                    "Categorical preprocessing must freeze PAD=0 and UNK=1 from train metadata."
                )
            unknown = lookup[UNKNOWN_TOKEN]
            rows = [
                [
                    [lookup.get(str(value), unknown) for value in timestep]
                    for timestep in window.values
                ]
                for window in windows
            ]
            x = np.asarray(rows, dtype=np.int32)
        else:
            raw = np.asarray([window.values for window in windows], dtype=np.float32)
            center = np.asarray(preprocessing.center, dtype=np.float32)
            scale = np.asarray(preprocessing.scale, dtype=np.float32)
            x = (raw - center) / scale
            if preprocessing.clip is not None:
                x = np.clip(x, -preprocessing.clip, preprocessing.clip)
            if not np.all(np.isfinite(x)):
                raise ValueError(
                    f"Prepared numeric features for partition {partition!r} are non-finite."
                )
        partition_labels = _validated_binary_label_array(
            [window.label for window in windows],
            subject=f"prepared partition {partition!r} labels",
        )
        partitions[partition] = PreparedPartition(
            x=x,
            window_ids=tuple(window.window_id for window in windows),
            unit_ids=tuple(window.unit_id for window in windows),
            labels=partition_labels,
            class_names=tuple(window.class_name for window in windows),
            event_ids=tuple(window.event_ids for window in windows),
            cluster_ids=tuple(window.cluster_id or window.unit_id for window in windows),
            evidence_origins=tuple(window.evidence_origin for window in windows),
        )
    return PreparedDataset(
        dataset=dataset,
        windowed=windowed,
        preprocessing=preprocessing,
        partitions=partitions,
    )


def aggregate_window_scores(
    partition: PreparedPartition,
    scores: Sequence[float] | np.ndarray,
    *,
    method: str,
) -> dict[str, object]:
    """Aggregate window scores back to independent source units."""

    score_array = np.asarray(scores, dtype=float).reshape(-1)
    if score_array.size != len(partition.window_ids):
        raise ValueError("Window scores must align with prepared windows.")
    validated_labels = _validated_binary_label_array(
        partition.labels, subject="aggregate_window_scores labels"
    )
    grouped: dict[str, list[int]] = {}
    for index, unit_id in enumerate(partition.unit_ids):
        grouped.setdefault(unit_id, []).append(index)
    unit_ids: list[str] = []
    unit_scores: list[float] = []
    labels: list[int] = []
    class_names: list[str] = []
    event_ids: list[tuple[str, ...]] = []
    cluster_ids: list[str] = []
    evidence_origins: list[str] = []
    window_counts: list[int] = []
    for unit_id, indices in grouped.items():
        values = score_array[indices]
        if method == "max":
            aggregate = float(np.max(values))
        elif method == "mean":
            aggregate = float(np.mean(values))
        elif method == "p95":
            aggregate = float(np.quantile(values, 0.95))
        else:
            raise ValueError(f"Unsupported aggregation method: {method!r}.")
        first = indices[0]
        if any(
            int(validated_labels[index]) != int(validated_labels[first])
            for index in indices
        ):
            raise RuntimeError(f"Window labels disagree within unit {unit_id!r}.")
        unit_ids.append(unit_id)
        unit_scores.append(aggregate)
        labels.append(int(validated_labels[first]))
        class_names.append(partition.class_names[first])
        merged_events = sorted(
            {event for index in indices for event in partition.event_ids[index]}
        )
        event_ids.append(tuple(merged_events))
        partition_clusters = (
            partition.cluster_ids
            if partition.cluster_ids
            else partition.unit_ids
        )
        if any(partition_clusters[index] != partition_clusters[first] for index in indices):
            raise RuntimeError(f"Window cluster identities disagree within unit {unit_id!r}.")
        cluster_ids.append(partition_clusters[first])
        partition_origins = (
            partition.evidence_origins
            if partition.evidence_origins
            else tuple("test_fixture" for _ in partition.unit_ids)
        )
        if any(partition_origins[index] != partition_origins[first] for index in indices):
            raise RuntimeError(f"Window evidence origins disagree within unit {unit_id!r}.")
        evidence_origins.append(partition_origins[first])
        window_counts.append(len(indices))
    return {
        "unit_ids": tuple(unit_ids),
        "scores": np.asarray(unit_scores, dtype=np.float64),
        "labels": np.asarray(labels, dtype=np.int64),
        "class_names": tuple(class_names),
        "event_ids": tuple(event_ids),
        "cluster_ids": tuple(cluster_ids),
        "evidence_origins": tuple(evidence_origins),
        "window_counts": tuple(window_counts),
    }


def audit_group_leakage(dataset: AcademicDataset) -> dict[str, object]:
    memberships: dict[str, set[str]] = {}
    unit_memberships: dict[str, set[str]] = {}
    for unit in dataset.units:
        memberships.setdefault(unit.group_id, set()).add(unit.assigned_partition)
        unit_memberships.setdefault(unit.unit_id, set()).add(unit.assigned_partition)
    group_violations = {
        key: sorted(value) for key, value in memberships.items() if len(value) != 1
    }
    unit_violations = {
        key: sorted(value)
        for key, value in unit_memberships.items()
        if len(value) != 1
    }
    return {
        "passed": not group_violations and not unit_violations,
        "group_count": len(memberships),
        "unit_count": len(unit_memberships),
        "group_overlap_count": len(group_violations),
        "unit_overlap_count": len(unit_violations),
        "violations": {
            "groups": group_violations,
            "units": unit_violations,
        },
    }


def audit_window_parentage(
    dataset: AcademicDataset,
    partitions: Mapping[str, Sequence[AcademicWindow]],
) -> dict[str, object]:
    parent_partition = {
        unit.unit_id: unit.assigned_partition for unit in dataset.units
    }
    violations: list[dict[str, str]] = []
    seen_windows: set[str] = set()
    for partition, windows in partitions.items():
        for window in windows:
            expected = parent_partition.get(window.unit_id)
            if expected != partition:
                violations.append(
                    {
                        "window_id": window.window_id,
                        "actual": partition,
                        "expected": str(expected),
                    }
                )
            if window.window_id in seen_windows:
                violations.append(
                    {
                        "window_id": window.window_id,
                        "actual": partition,
                        "expected": "unique window identity",
                    }
                )
            seen_windows.add(window.window_id)
    return {
        "passed": not violations,
        "window_count": len(seen_windows),
        "violations": violations,
    }


def support_summary(dataset: AcademicDataset) -> dict[str, object]:
    summary: dict[str, object] = {}
    for partition in PARTITIONS:
        units = dataset.partition(partition)
        class_counts: dict[str, int] = {}
        for unit in units:
            class_counts[unit.class_name] = class_counts.get(unit.class_name, 0) + 1
        summary[partition] = {
            "units": len(units),
            "normal": sum(unit.label == 0 for unit in units),
            "attack": sum(unit.label == 1 for unit in units),
            "per_class": class_counts,
        }
    return summary


def validate_academic_support(
    dataset: AcademicDataset,
    *,
    minimum_test_normal: int,
    minimum_test_attack: int,
) -> dict[str, object]:
    if (
        isinstance(minimum_test_normal, bool)
        or isinstance(minimum_test_attack, bool)
        or minimum_test_normal < 0
        or minimum_test_attack < 0
    ):
        raise ValueError("Minimum academic supports must be non-negative integers.")
    issues: list[str] = []
    support = support_summary(dataset)
    train = support["train"]  # type: ignore[assignment]
    validation = support["validation"]  # type: ignore[assignment]
    test = support["test"]  # type: ignore[assignment]
    if train["normal"] < 2:  # type: ignore[index]
        issues.append("train partition has fewer than two normal units")
    if train["attack"] != 0:  # type: ignore[index]
        issues.append("normal-only anomaly protocol found attacks in train")
    if validation["normal"] < 2:  # type: ignore[index]
        issues.append("validation partition has fewer than two normal units")
    if validation["attack"] != 0:  # type: ignore[index]
        issues.append("normal-only anomaly protocol found attacks in validation")
    if test["normal"] < minimum_test_normal:  # type: ignore[index]
        issues.append(
            f"test normal support {test['normal']} is below {minimum_test_normal}"  # type: ignore[index]
        )
    if test["attack"] < minimum_test_attack:  # type: ignore[index]
        issues.append(
            f"test attack support {test['attack']} is below {minimum_test_attack}"  # type: ignore[index]
        )
    return {"passed": not issues, "support": support, "issues": issues}


def _parse_adfa_trace(path: Path) -> tuple[str, ...]:
    integers: list[str] = []
    for token in path.read_text(encoding="utf-8", errors="strict").split():
        try:
            integers.append(str(int(token)))
        except ValueError as exc:
            raise ValueError(f"Invalid ADFA-LD syscall token in {path}: {token!r}") from exc
    if not integers:
        raise ValueError(f"Empty ADFA-LD trace: {path}")
    return tuple(integers)


def _adfa_detector_identity(integers: Sequence[str]) -> str:
    return canonical_json_hash(
        {
            "projection": "adfa-parsed-syscall-id-sequence-v2",
            "syscall_ids": list(integers),
        }
    )


def _load_adfa_ld(
    root: Path, config: Mapping[str, object], *, phase: str
) -> AcademicDataset:
    required = (
        root / "Training_Data_Master",
        root / "Validation_Data_Master",
        root / "Attack_Data_Master",
    )
    missing = [str(path) for path in required if not path.is_dir()]
    if missing:
        raise ValueError(f"ADFA-LD missing native directories: {missing}")
    seed = int(config.get("partition_seed", 1729))
    normal_validation_fraction = float(config.get("normal_validation_fraction", 0.5))
    if not 0.0 < normal_validation_fraction < 1.0:
        raise ValueError("normal_validation_fraction must be between zero and one.")

    raw_training_files = sorted((root / "Training_Data_Master").glob("*.txt"))
    raw_validation_files = sorted((root / "Validation_Data_Master").glob("*.txt"))

    raw_attack_files: list[tuple[Path, str]] = []
    attack_root = root / "Attack_Data_Master"
    family_names = {
        1: "Adduser",
        2: "Hydra-FTP",
        3: "Hydra-SSH",
        4: "Java-Meterpreter",
        5: "Web-Shell",
    }
    for class_id, prefixes in _ATTACK_DIRECTORY_PREFIXES.items():
        for directory in sorted(path for path in attack_root.iterdir() if path.is_dir()):
            if any(
                directory.name == prefix
                or directory.name.startswith(prefix + "_")
                or directory.name.startswith(prefix + "-")
                for prefix in prefixes
            ):
                raw_attack_files.extend(
                    (path, family_names[class_id])
                    for path in sorted(directory.iterdir())
                    if path.is_file()
                )

    # The model consumes parsed integer syscall IDs, not raw formatting.
    # Deduplicate on that detector-visible normalized sequence so whitespace
    # or byte-level differences cannot conceal cross-partition leakage.
    descriptors: list[tuple[Path, str, str, int, str, str]] = []
    descriptors.extend(
        (
            path,
            "Training_Data_Master",
            "Normal",
            0,
            file_sha256(path),
            _adfa_detector_identity(_parse_adfa_trace(path)),
        )
        for path in raw_training_files
    )
    descriptors.extend(
        (
            path,
            "Validation_Data_Master",
            "Normal",
            0,
            file_sha256(path),
            _adfa_detector_identity(_parse_adfa_trace(path)),
        )
        for path in raw_validation_files
    )
    descriptors.extend(
        (
            path,
            "Attack_Data_Master",
            family,
            1,
            file_sha256(path),
            _adfa_detector_identity(_parse_adfa_trace(path)),
        )
        for path, family in raw_attack_files
    )
    by_hash: dict[str, list[tuple[Path, str, str, int, str, str]]] = {}
    for descriptor in descriptors:
        by_hash.setdefault(descriptor[5], []).append(descriptor)
    contradictory_hashes: dict[str, list[dict[str, str | int]]] = {}
    duplicate_copy_count = 0
    canonical_descriptors: list[tuple[Path, str, str, int, str, str]] = []
    native_preference = {
        "Training_Data_Master": 0,
        "Validation_Data_Master": 1,
        "Attack_Data_Master": 2,
    }
    for digest, group in sorted(by_hash.items()):
        semantics = {(item[2], item[3]) for item in group}
        if len(semantics) != 1:
            contradictory_hashes[digest] = [
                {
                    "path": item[0].relative_to(root).as_posix(),
                    "class_name": item[2],
                    "label": item[3],
                }
                for item in group
            ]
            continue
        canonical = min(
            group,
            key=lambda item: (
                native_preference[item[1]],
                item[0].relative_to(root).as_posix(),
            ),
        )
        canonical_descriptors.append(canonical)
        duplicate_copy_count += len(group) - 1

    hash_by_path = {descriptor[0]: descriptor[4] for descriptor in canonical_descriptors}
    input_hash_by_path = {
        descriptor[0]: descriptor[5] for descriptor in canonical_descriptors
    }
    training_files = sorted(
        descriptor[0]
        for descriptor in canonical_descriptors
        if descriptor[1] == "Training_Data_Master"
    )
    official_validation = sorted(
        descriptor[0]
        for descriptor in canonical_descriptors
        if descriptor[1] == "Validation_Data_Master"
    )
    ranked_validation = sorted(
        official_validation,
        key=lambda path: _stable_priority(seed, path.relative_to(root).as_posix()),
    )
    validation_count = min(
        max(int(round(len(ranked_validation) * normal_validation_fraction)), 1),
        max(len(ranked_validation) - 1, 1),
    )
    validation_files = ranked_validation[:validation_count]
    test_normal_files = ranked_validation[validation_count:]

    attack_files = sorted(
        (
            descriptor[0],
            descriptor[2],
        )
        for descriptor in canonical_descriptors
        if descriptor[1] == "Attack_Data_Master"
    )

    caps = _phase_caps(config, phase)
    require_exact_caps = config.get("phase_allocation") is not None
    training_files = _stable_cap(
        training_files,
        _cap(caps, "train"),
        seed,
        root,
        offset=_phase_rank_start(config, phase, "train"),
        require_exact=require_exact_caps,
    )
    validation_files = _stable_cap(
        validation_files,
        _cap(caps, "validation"),
        seed + 1,
        root,
        offset=_phase_rank_start(config, phase, "validation"),
        require_exact=require_exact_caps,
    )
    test_normal_files = _stable_cap(
        test_normal_files,
        _cap(caps, "test_normal"),
        seed + 2,
        root,
        offset=_phase_rank_start(config, phase, "test_normal"),
        require_exact=require_exact_caps,
    )
    attacks_by_family: dict[str, list[Path]] = {}
    for path, family in attack_files:
        attacks_by_family.setdefault(family, []).append(path)
    selected_attacks: list[tuple[Path, str]] = []
    attack_cap = _cap(caps, "test_attack_per_class")
    for family, files in sorted(attacks_by_family.items()):
        selected_attacks.extend(
            (path, family)
            for path in _stable_cap(
                files,
                attack_cap,
                seed + 3,
                root,
                offset=_phase_rank_start(
                    config, phase, f"attack_per_class:{family}", fallback="attack_per_class"
                ),
                require_exact=require_exact_caps,
            )
        )

    units: list[AcademicUnit] = []
    order = 0
    for files, native, assigned in (
        (training_files, "Training_Data_Master", "train"),
        (validation_files, "Validation_Data_Master", "validation"),
        (test_normal_files, "Validation_Data_Master", "test"),
    ):
        for path in files:
            units.append(
                _adfa_unit(
                    root,
                    path,
                    native_partition=native,
                    assigned_partition=assigned,
                    class_name="Normal",
                    label=0,
                    order=order,
                    content_sha256=hash_by_path[path],
                    detector_input_sha256=input_hash_by_path[path],
                )
            )
            order += 1
    for path, family in selected_attacks:
        units.append(
            _adfa_unit(
                root,
                path,
                native_partition="Attack_Data_Master",
                assigned_partition="test",
                class_name=family,
                label=1,
                order=order,
                content_sha256=hash_by_path[path],
                detector_input_sha256=input_hash_by_path[path],
            )
        )
        order += 1

    inventory = {
        "Training_Data_Master": len(raw_training_files),
        "Validation_Data_Master": len(raw_validation_files),
        "Attack_Data_Master": len(raw_attack_files),
        "attack_per_class": {
            family: sum(candidate_family == family for _, candidate_family in raw_attack_files)
            for family in sorted(set(candidate_family for _, candidate_family in raw_attack_files))
        },
        "unique_noncontradictory_content_hashes": len(canonical_descriptors),
        "deduplicated_copy_count": duplicate_copy_count,
        "contradictory_content_hash_groups_excluded": len(contradictory_hashes),
    }
    source_manifest = {
        "source_description": "ADFA-LD official 2013 archive",
        "evidence_origin": "official_native",
        "root": str(root.resolve()),
        "layout": "Training_Data_Master/Validation_Data_Master/Attack_Data_Master",
        "native_inventory": inventory,
        "selection_phase": phase,
        "selection_caps": caps,
        "phase_allocation": _phase_allocation_audit(config, phase),
        "selected_content_identity": canonical_json_hash(
            [unit.identity_dict() for unit in units]
        ),
        "normal_validation_split": {
            "source": "Validation_Data_Master",
            "method": "seeded stable unit split before windowing",
            "fraction": normal_validation_fraction,
            "seed": seed,
        },
        "deduplication": {
            "identity": "SHA-256 of parsed normalized detector-visible syscall ID sequence",
            "canonical_preference": [
                "Training_Data_Master",
                "Validation_Data_Master",
                "Attack_Data_Master",
            ],
            "contradictory_groups": contradictory_hashes,
        },
    }
    return AcademicDataset(
        name="adfa-ld",
        modality="categorical-syscall",
        protocol=(
            "adfa-ld-native-normal-only-v2"
            if config.get("phase_allocation") is not None
            else "adfa-ld-native-normal-only-v1"
        ),
        units=tuple(units),
        feature_names=("syscall_id",),
        label_names=("Normal", *tuple(sorted(attacks_by_family))),
        source_manifest=source_manifest,
        phase=phase,
        evidence_origin="official_native",
    )


def _adfa_unit(
    root: Path,
    path: Path,
    *,
    native_partition: str,
    assigned_partition: str,
    class_name: str,
    label: int,
    order: int,
    content_sha256: str,
    detector_input_sha256: str,
) -> AcademicUnit:
    integers = _parse_adfa_trace(path)
    relative = path.relative_to(root).as_posix()
    unit_id = f"adfa-ld:{relative}"
    return AcademicUnit(
        unit_id=unit_id,
        group_id=detector_input_sha256,
        native_partition=native_partition,
        assigned_partition=assigned_partition,
        label=label,
        class_name=class_name,
        values=tuple((token,) for token in integers),
        source_path=relative,
        source_sha256=content_sha256,
        order=order,
        event_ids=(unit_id,) if label else (),
        evidence_origin="official_native",
        resampling_cluster_id=unit_id,
    )


def _load_lid_ds_2021(
    root: Path, config: Mapping[str, object], *, phase: str
) -> AcademicDataset:
    if not root.is_dir():
        raise ValueError(f"LID-DS 2021 root does not exist: {root}")
    configured = config.get("scenarios")
    available = sorted(
        path.name
        for path in root.iterdir()
        if path.is_dir() and not path.name.startswith("__")
    )
    scenarios = [str(value) for value in configured] if isinstance(configured, list) else available
    absent = sorted(set(scenarios) - set(available))
    if absent:
        raise ValueError(f"Configured LID-DS scenarios are absent: {absent}")
    if not scenarios:
        raise ValueError("No LID-DS scenarios selected.")
    seed = int(config.get("partition_seed", 1729))
    caps = _phase_caps(config, phase)
    cap_per_role = _cap(caps, "archives_per_scenario_partition")
    window_config = config.get("window", {})
    if not isinstance(window_config, Mapping):
        raise ValueError("LID-DS window configuration must be an object.")
    sequence_length = int(window_config.get("sequence_length", 128))
    max_sequences = int(window_config.get("max_windows_per_unit", 4))
    if sequence_length <= 0 or max_sequences <= 0:
        raise ValueError("LID-DS sequence_length and max_windows_per_unit must be positive.")
    roles = (
        ("training", "training", "train"),
        ("validation", "validation", "validation"),
        ("test/normal", "test-normal", "test"),
        ("test/normal_and_attack", "test-normal-and-attack", "test"),
    )
    units: list[AcademicUnit] = []
    inventory: dict[str, dict[str, object]] = {}
    quality_exclusions: list[dict[str, str]] = []
    parsed_syscall_counts: list[int] = []
    projected_archives: dict[Path, tuple] = {}

    def project_archive(archive: Path, relative: str) -> tuple:
        """Parse an archive once while building phase-isolated content slices."""

        cached = projected_archives.get(archive)
        if cached is None:
            cached = _project_lid_consumed_archive(
                archive,
                sequence_length=sequence_length,
                max_sequences=max_sequences,
                selection_seed=seed,
                selection_identity=relative,
            )
            projected_archives[archive] = cached
        return cached

    def projection_detector_input_content_identity(
        sampled_sequences: tuple[tuple[int, tuple[tuple[str, ...], ...]], ...],
    ) -> str:
        """Match AcademicUnit.detector_input_content_identity before construction."""

        return canonical_json_hash(
            {
                "values": (),
                "sampled_sequences": [values for _, values in sampled_sequences],
            }
        )

    def require_consistent_content_semantics(
        *,
        group_id: str,
        detector_input_content_id: str,
        semantics: tuple[int, str],
        known_groups: Mapping[str, tuple[int, str]],
        known_detector_inputs: Mapping[str, tuple[int, str]],
        archive: Path,
    ) -> None:
        """Reject one model-visible stream carrying incompatible truth semantics."""

        group_semantics = known_groups.get(group_id)
        input_semantics = known_detector_inputs.get(detector_input_content_id)
        if (
            group_semantics is not None
            and group_semantics != semantics
            or input_semantics is not None
            and input_semantics != semantics
        ):
            raise ValueError(
                "LID-DS content-identical recordings carry contradictory "
                f"label/class semantics at {archive}."
            )

    def reserved_pilot_content_semantics(
    ) -> tuple[dict[str, tuple[int, str]], dict[str, tuple[int, str]]]:
        """Return detector and group identities reserved by the pilot.

        Archive-path offsets alone are insufficient because the official corpus
        contains semantic copies under distinct paths and, occasionally, in
        distinct native roles.  Confirmatory selection must exclude all content
        identities admitted to the pilot, not just the pilot archive paths.
        """

        allocation = config.get("phase_allocation")
        if (
            phase != "confirmatory"
            or not isinstance(allocation, Mapping)
            or allocation.get("method") != DISJOINT_CONTENT_PRIORITY_SLICES_V2
        ):
            return {}, {}
        pilot_cap = _cap(
            _phase_caps(config, "pilot"), "archives_per_scenario_partition"
        )
        if pilot_cap == 0:
            return {}, {}
        reserved_group_semantics: dict[str, tuple[int, str]] = {}
        reserved_detector_input_semantics: dict[str, tuple[int, str]] = {}
        for pilot_scenario in scenarios:
            pilot_scenario_root = root / pilot_scenario
            for relative_role, native_partition, assigned_partition in roles:
                role_root = pilot_scenario_root / Path(relative_role)
                archives = sorted(role_root.rglob("*.zip")) if role_root.is_dir() else []
                if not archives:
                    raise ValueError(
                        f"LID-DS scenario {pilot_scenario!r} is missing "
                        f"{relative_role!r} archives."
                    )
                stratum = f"{pilot_scenario}:{native_partition}"
                rank_start = _phase_rank_start(
                    config,
                    "pilot",
                    stratum,
                    fallback=native_partition,
                )
                retained_for_role = 0
                valid_before_slice = 0
                for archive in _stable_cap(archives, 0, seed, root):
                    relative = archive.relative_to(root).as_posix()
                    (
                        _,
                        sampled_sequences,
                        attack,
                        detector_input_sha256,
                        _,
                        _,
                    ) = project_archive(archive, relative)
                    if not sampled_sequences:
                        continue
                    if valid_before_slice < rank_start:
                        valid_before_slice += 1
                        continue
                    if assigned_partition in {"train", "validation"} and attack:
                        raise ValueError(
                            "Attack-labelled LID-DS recording found in normal-only "
                            f"fit/early-stopping partition: {archive}"
                        )
                    detector_input_content_identity = (
                        projection_detector_input_content_identity(sampled_sequences)
                    )
                    semantics = (
                        1 if attack else 0,
                        f"{pilot_scenario}-attack" if attack else "Normal",
                    )
                    require_consistent_content_semantics(
                        group_id=detector_input_sha256,
                        detector_input_content_id=detector_input_content_identity,
                        semantics=semantics,
                        known_groups=reserved_group_semantics,
                        known_detector_inputs=reserved_detector_input_semantics,
                        archive=archive,
                    )
                    if (
                        detector_input_sha256 in reserved_group_semantics
                        or detector_input_content_identity
                        in reserved_detector_input_semantics
                    ):
                        # The pilot selection itself must be content-unique.
                        # Otherwise confirmatory reservation would reproduce a
                        # later deduplication loss instead of the admitted pilot
                        # content slice.
                        valid_before_slice += 1
                        continue
                    reserved_group_semantics[detector_input_sha256] = semantics
                    reserved_detector_input_semantics[
                        detector_input_content_identity
                    ] = semantics
                    retained_for_role += 1
                    valid_before_slice += 1
                    if retained_for_role >= pilot_cap:
                        break
                if retained_for_role < pilot_cap:
                    raise ValueError(
                        f"LID-DS scenario {pilot_scenario!r} role {relative_role!r} "
                        "cannot reserve the configured pilot content slice."
                    )
        return reserved_group_semantics, reserved_detector_input_semantics

    (
        pilot_reserved_group_semantics,
        pilot_reserved_detector_input_semantics,
    ) = reserved_pilot_content_semantics()
    allocation = config.get("phase_allocation")
    content_isolation_required = (
        isinstance(allocation, Mapping)
        and allocation.get("method") == DISJOINT_CONTENT_PRIORITY_SLICES_V2
    )
    selected_group_ids: set[str] = set()
    selected_detector_input_ids: set[str] = set()
    selected_group_semantics: dict[str, tuple[int, str]] = {}
    selected_detector_input_semantics: dict[str, tuple[int, str]] = {}
    excluded_pilot_content_copies = 0
    excluded_intra_phase_content_copies = 0
    order = 0
    for scenario in scenarios:
        scenario_root = root / scenario
        inventory[scenario] = {}
        for relative_role, native_partition, assigned_partition in roles:
            role_root = scenario_root / Path(relative_role)
            archives = sorted(role_root.rglob("*.zip")) if role_root.is_dir() else []
            inventory[scenario][native_partition] = len(archives)
            if not archives:
                raise ValueError(
                    f"LID-DS scenario {scenario!r} is missing {relative_role!r} archives."
                )
            # Rank before parsing, then retain the first N *valid* recordings.
            # Empty syscall traces are excluded by a label-blind quality rule
            # and backfilled from the next ranked archive so support does not
            # depend on a corrupt/empty member happening to land in the cap.
            stratum = f"{scenario}:{native_partition}"
            rank_start = _phase_rank_start(
                config,
                phase,
                stratum,
                fallback=native_partition,
            )
            ranked = _stable_cap(archives, 0, seed, root)
            retained_for_role = 0
            valid_before_slice = 0
            for archive in ranked:
                relative = archive.relative_to(root).as_posix()
                (
                    _,
                    sampled_sequences,
                    attack,
                    detector_input_sha256,
                    consumed_source_sha256,
                    parsed_count,
                ) = project_archive(archive, relative)
                if not sampled_sequences:
                    quality_exclusions.append(
                        {
                            "path": relative,
                            "reason": "consumed .sc member contains no parseable syscall names",
                        }
                    )
                    continue
                if valid_before_slice < rank_start:
                    valid_before_slice += 1
                    continue
                # Training is a normal-only boundary.  A malformed or surprising
                # published recording fails closed instead of contaminating fit.
                if assigned_partition in {"train", "validation"} and attack:
                    raise ValueError(
                        "Attack-labelled LID-DS recording found in normal-only "
                        f"fit/early-stopping partition: {archive}"
                    )
                valid_before_slice += 1
                detector_input_content_identity = projection_detector_input_content_identity(
                    sampled_sequences
                )
                class_name = f"{scenario}-attack" if attack else "Normal"
                semantics = (1 if attack else 0, class_name)
                if (
                    detector_input_sha256 in pilot_reserved_group_semantics
                    or detector_input_content_identity
                    in pilot_reserved_detector_input_semantics
                ):
                    require_consistent_content_semantics(
                        group_id=detector_input_sha256,
                        detector_input_content_id=detector_input_content_identity,
                        semantics=semantics,
                        known_groups=pilot_reserved_group_semantics,
                        known_detector_inputs=pilot_reserved_detector_input_semantics,
                        archive=archive,
                    )
                    excluded_pilot_content_copies += 1
                    continue
                if content_isolation_required:
                    require_consistent_content_semantics(
                        group_id=detector_input_sha256,
                        detector_input_content_id=detector_input_content_identity,
                        semantics=semantics,
                        known_groups=selected_group_semantics,
                        known_detector_inputs=selected_detector_input_semantics,
                        archive=archive,
                    )
                if content_isolation_required and (
                    detector_input_sha256 in selected_group_ids
                    or detector_input_content_identity in selected_detector_input_ids
                ):
                    excluded_intra_phase_content_copies += 1
                    continue
                unit_id = f"lid-ds-2021:{relative}"
                parsed_syscall_counts.append(parsed_count)
                units.append(
                    AcademicUnit(
                        unit_id=unit_id,
                        group_id=detector_input_sha256,
                        native_partition=native_partition,
                        assigned_partition=assigned_partition,
                        label=1 if attack else 0,
                        class_name=class_name,
                        values=(),
                        source_path=relative,
                        source_sha256=consumed_source_sha256,
                        order=order,
                        event_ids=(unit_id,) if attack else (),
                        sampled_sequences=sampled_sequences,
                        evidence_origin="official_native",
                        resampling_cluster_id=unit_id,
                    )
                )
                if content_isolation_required:
                    selected_group_ids.add(detector_input_sha256)
                    selected_detector_input_ids.add(detector_input_content_identity)
                    selected_group_semantics[detector_input_sha256] = semantics
                    selected_detector_input_semantics[
                        detector_input_content_identity
                    ] = semantics
                order += 1
                retained_for_role += 1
                if cap_per_role and retained_for_role >= cap_per_role:
                    break
            if cap_per_role and retained_for_role < cap_per_role:
                raise ValueError(
                    f"LID-DS scenario {scenario!r} role {relative_role!r} has only "
                    f"{retained_for_role} valid recordings below requested cap {cap_per_role}."
                )
    selected_unit_count = len(units)
    units, deduplication = _deduplicate_content_units(units)
    if content_isolation_required and len(units) != selected_unit_count:
        raise ValueError(
            "LID-DS content-aware phase selection admitted duplicate content "
            "before final deduplication."
        )
    source_manifest = {
        "source_description": "LID-DS 2021 official ZIP recordings",
        "evidence_origin": "official_native",
        "root": str(root.resolve()),
        "layout": "scenario/{training,validation,test/{normal,normal_and_attack}}/*.zip",
        "native_inventory": inventory,
        "selected_scenarios": scenarios,
        "selection_phase": phase,
        "selection_caps": caps,
        "phase_allocation": _phase_allocation_audit(config, phase),
        "quality_exclusions": {
            "criterion": "empty parsed syscall sequence; independent of attack label",
            "count": len(quality_exclusions),
            "recordings": quality_exclusions,
        },
        "within_recording_sampling": {
            "method": "seeded priority sample of intact non-overlapping syscall sequences",
            "label_blind": True,
            "sequence_length": sequence_length,
            "maximum_sequences_per_recording": max_sequences,
            "seed": seed,
            "parsed_syscall_count": {
                "minimum": min(parsed_syscall_counts) if parsed_syscall_counts else 0,
                "maximum": max(parsed_syscall_counts) if parsed_syscall_counts else 0,
                "total": sum(parsed_syscall_counts),
            },
        },
        "selected_content_identity": canonical_json_hash(
            [unit.identity_dict() for unit in units]
        ),
        "deduplication": deduplication,
    }
    if content_isolation_required:
        source_manifest["within_phase_content_reservation"] = {
            "method": "global-content-identity-exclusion-v1",
            "selected_group_count": len(selected_group_ids),
            "selected_detector_input_content_count": len(selected_detector_input_ids),
            "excluded_duplicate_recording_count": excluded_intra_phase_content_copies,
        }
        source_manifest["cross_phase_content_reservation"] = {
            "method": "global-pilot-content-identity-exclusion-v1",
            "reserved_pilot_group_count": len(pilot_reserved_group_semantics),
            "reserved_pilot_detector_input_content_identity": (
                canonical_json_hash(
                    sorted(pilot_reserved_detector_input_semantics)
                )
                if pilot_reserved_detector_input_semantics
                else None
            ),
            "reserved_pilot_detector_input_content_count": len(
                pilot_reserved_detector_input_semantics
            ),
            "reserved_pilot_group_identity": (
                canonical_json_hash(sorted(pilot_reserved_group_semantics))
                if pilot_reserved_group_semantics
                else None
            ),
            "excluded_confirmatory_recording_count": excluded_pilot_content_copies,
        }
    return AcademicDataset(
        name="lid-ds-2021",
        modality="categorical-syscall",
        protocol=(
            "lid-ds-2021-native-recording-v4"
            if isinstance(config.get("phase_allocation"), Mapping)
            and config["phase_allocation"].get("method")
            == DISJOINT_CONTENT_PRIORITY_SLICES_V2
            else (
                "lid-ds-2021-native-recording-v2"
                if config.get("phase_allocation") is not None
                else "lid-ds-2021-native-recording-v1"
            )
        ),
        units=tuple(units),
        feature_names=("syscall_name",),
        label_names=("Normal", *(f"{scenario}-attack" for scenario in scenarios)),
        source_manifest=source_manifest,
        phase=phase,
        evidence_origin="official_native",
    )


def _load_hai_23_05(
    root: Path, config: Mapping[str, object], *, phase: str
) -> AcademicDataset:
    manifest = inspect_hai_23_05(root)
    block_rows = int(config.get("block_rows", 128))
    if block_rows <= 0:
        raise ValueError("HAI block_rows must be positive.")
    seed = int(config.get("partition_seed", 1729))
    caps = _phase_caps(config, phase)
    file_hashes = {
        item.file_name: item.content_sha256
        for item in (*manifest.observations, *manifest.labels)
    }
    roles = (
        (("hai-train1.csv", "hai-train2.csv"), None, "train", "train"),
        # Two native normal recordings are reserved for validation so early
        # stopping and threshold calibration can use disjoint source clusters.
        (("hai-train3.csv", "hai-train4.csv"), None, "validation", "validation"),
        (("hai-test1.csv",), "label-test1.csv", "test1", "test"),
        (("hai-test2.csv",), "label-test2.csv", "test2", "test"),
    )
    candidates_by_partition: dict[str, list[AcademicUnit]] = {
        "train": [],
        "validation": [],
        "test": [],
    }
    legacy_units: list[AcademicUnit] = []
    strict_phase_allocation = config.get("phase_allocation") is not None
    feature_names: tuple[str, ...] | None = None
    inventory: dict[str, dict[str, object]] = {}
    for observation_names, label_name, native_partition, assigned_partition in roles:
        for observation_name in observation_names:
            label_path = root / label_name if label_name else None
            phase_offset = _phase_rank_start(
                config, phase, assigned_partition, fallback=assigned_partition
            )
            requested_normal = _hai_cap(caps, assigned_partition, "normal")
            requested_attack = _hai_cap(caps, assigned_partition, "attack")
            requested_total = _hai_total_cap(caps, assigned_partition)
            blocks, columns, total_counts = _select_hai_blocks(
                root / observation_name,
                label_path=label_path,
                block_rows=block_rows,
                seed=seed,
                # Retain enough candidates per native file for a second,
                # partition-global priority slice below. The final cap is a
                # dataset-partition total, never an accidental per-file cap.
                normal_cap=(
                    requested_normal + phase_offset
                    if strict_phase_allocation and requested_normal
                    else requested_normal
                ),
                attack_cap=(
                    requested_attack + phase_offset
                    if strict_phase_allocation and requested_attack
                    else requested_attack
                ),
                total_cap=(
                    requested_total + phase_offset
                    if strict_phase_allocation
                    and requested_total is not None
                    and requested_total > 0
                    else requested_total
                ),
                source_sha256=file_hashes[observation_name],
                native_partition=native_partition,
                assigned_partition=assigned_partition,
                rank_start=0,
            )
            if feature_names is None:
                feature_names = columns
            elif feature_names != columns:
                raise ValueError(f"HAI feature schema differs in {observation_name}.")
            inventory[observation_name] = total_counts
            if strict_phase_allocation:
                candidates_by_partition[assigned_partition].extend(blocks)
            else:
                legacy_units.extend(blocks)
    if feature_names is None:
        raise ValueError("HAI-23.05 yielded no feature schema.")
    units: list[AcademicUnit] = []
    partition_selection: dict[str, object] = {}
    for assigned_partition, candidates in (
        candidates_by_partition.items() if strict_phase_allocation else ()
    ):
        phase_offset = _phase_rank_start(
            config, phase, assigned_partition, fallback=assigned_partition
        )
        total_cap = _hai_total_cap(caps, assigned_partition)
        if total_cap is not None:
            selected_partition = _stable_unit_slice(
                candidates,
                cap=total_cap,
                offset=phase_offset,
                seed=seed,
                stratum=f"hai:{assigned_partition}:all",
                require_exact=True,
            )
        else:
            selected_partition = []
            for label, label_name in ((0, "normal"), (1, "attack")):
                label_candidates = [unit for unit in candidates if unit.label == label]
                cap = _hai_cap(caps, assigned_partition, label_name)
                if not label_candidates and cap == 0:
                    continue
                selected_partition.extend(
                    _stable_unit_slice(
                        label_candidates,
                        cap=cap,
                        offset=phase_offset,
                        seed=seed,
                        stratum=f"hai:{assigned_partition}:{label_name}",
                        require_exact=True,
                    )
                )
        units.extend(selected_partition)
        partition_selection[assigned_partition] = {
            "candidate_count": len(candidates),
            "selected_count": len(selected_partition),
            "selected_normal": sum(unit.label == 0 for unit in selected_partition),
            "selected_attack": sum(unit.label == 1 for unit in selected_partition),
            "rank_start": phase_offset,
            "total_cap": total_cap,
        }
    if not strict_phase_allocation:
        units = legacy_units
    units = sorted(units, key=lambda unit: (unit.assigned_partition, unit.order, unit.unit_id))
    source_manifest = {
        "source_description": "HAI-23.05 official native CSV release",
        "evidence_origin": "official_native",
        "root": str(root.resolve()),
        "schema": manifest.schema_version,
        "source_file_sha256": file_hashes,
        "block_rows": block_rows,
        "native_inventory": inventory,
        "partition_global_selection": partition_selection,
        "selection_phase": phase,
        "selection_caps": caps,
        "phase_allocation": _phase_allocation_audit(config, phase),
        "selected_content_identity": canonical_json_hash(
            [unit.identity_dict() for unit in units]
        ),
        "partition_policy": {
            "train": "hai-train1 and hai-train2 normal recordings",
            "validation": (
                "hai-train3 and hai-train4 normal recordings; source-cluster-disjoint "
                "early-stopping/calibration split (no published test truth)"
            ),
            "test": "hai-test1 and hai-test2 with published labels, untouched until evaluation",
        },
    }
    return AcademicDataset(
        name="hai-23.05",
        modality="numeric-multivariate",
        protocol=(
            "hai-23.05-native-file-temporal-block-v2"
            if strict_phase_allocation
            else "hai-23.05-native-file-temporal-block-v1"
        ),
        units=tuple(units),
        feature_names=feature_names,
        label_names=("Normal", "Attack"),
        source_manifest=source_manifest,
        phase=phase,
        evidence_origin="official_native",
    )


def _parse_hai_timestamp(
    raw: str, *, source: Path | None, row_number: int
) -> tuple[datetime, str]:
    text = raw.strip()
    if not text:
        raise ValueError(f"Empty HAI timestamp at {source}:{row_number}")
    normalized = text[:-1] + "+00:00" if text.endswith("Z") else text
    separator = "T" if "T" in normalized else " " if " " in normalized else None
    if separator is not None:
        date_part, clock_part = normalized.split(separator, 1)
        hour, colon, remainder = clock_part.partition(":")
        if colon and len(hour) == 1 and hour.isdigit():
            normalized = f"{date_part}{separator}0{hour}:{remainder}"
    try:
        timestamp = datetime.fromisoformat(normalized)
    except ValueError as exc:
        raise ValueError(
            f"Invalid HAI timestamp at {source}:{row_number}: {raw!r}"
        ) from exc
    time_text = text.replace("T", " ").split(" ", 1)
    clock = time_text[1] if len(time_text) == 2 else ""
    clock = clock.split("+", 1)[0].rstrip("Z")
    if "." in clock:
        resolution = "microsecond"
    elif clock.count(":") >= 2:
        resolution = "second"
    elif clock.count(":") == 1:
        resolution = "minute"
    else:
        raise ValueError(
            f"HAI timestamp resolution is unsupported at {source}:{row_number}: {raw!r}"
        )
    return timestamp, resolution


def _select_hai_blocks(
    observation_path: Path,
    *,
    label_path: Path | None,
    block_rows: int,
    seed: int,
    normal_cap: int,
    attack_cap: int,
    total_cap: int | None,
    source_sha256: str,
    native_partition: str,
    assigned_partition: str,
    rank_start: int = 0,
) -> tuple[list[AcademicUnit], tuple[str, ...], dict[str, object]]:
    if rank_start < 0:
        raise ValueError("HAI phase allocation rank_start cannot be negative.")
    if rank_start and (
        total_cap == 0 or (total_cap is None and (normal_cap == 0 or attack_cap == 0))
    ):
        raise ValueError(
            "HAI disjoint rank slices require explicit positive caps for every selected stratum."
        )
    selected: dict[int, list[tuple[int, str, AcademicUnit]]] = {0: [], 1: []}
    selected_all: list[tuple[int, str, AcademicUnit]] = []
    counts: dict[str, object] = {"normal": 0, "attack": 0, "dropped_partial": 0}
    with observation_path.open("r", encoding="utf-8", newline="") as observations:
        observation_reader = csv.reader(observations)
        header = next(observation_reader, None)
        if not header or header[0] != "timestamp" or len(header) < 2:
            raise ValueError(f"Unsupported HAI observation schema: {observation_path}")
        feature_names = tuple(header[1:])
        label_handle = label_path.open("r", encoding="utf-8", newline="") if label_path else None
        try:
            label_reader = csv.reader(label_handle) if label_handle else None
            if label_reader is not None:
                label_header = next(label_reader, None)
                if label_header != ["timestamp", "label"]:
                    raise ValueError(f"Unsupported HAI label schema: {label_path}")
            rows: list[tuple[float, ...]] = []
            row_timestamps: list[datetime] = []
            row_events: set[str] = set()
            block_index = 0
            event_index = 0
            in_attack = False
            previous_observation_timestamp: datetime | None = None
            previous_label_timestamp: datetime | None = None
            observed_label_resolutions: set[str] = set()
            for row_number, row in enumerate(observation_reader, start=0):
                if len(row) != len(header):
                    raise ValueError(f"Malformed HAI row {observation_path}:{row_number + 2}")
                try:
                    values = tuple(float(value) for value in row[1:])
                except ValueError as exc:
                    raise ValueError(
                        f"Non-numeric HAI feature at {observation_path}:{row_number + 2}"
                    ) from exc
                if not all(math.isfinite(value) for value in values):
                    raise ValueError(
                        f"Non-finite HAI feature at {observation_path}:{row_number + 2}"
                    )
                observation_timestamp, _ = _parse_hai_timestamp(
                    row[0], source=observation_path, row_number=row_number + 2
                )
                if (
                    previous_observation_timestamp is not None
                    and observation_timestamp <= previous_observation_timestamp
                ):
                    raise ValueError(
                        f"HAI observation timestamps are not strictly increasing at "
                        f"{observation_path}:{row_number + 2}"
                    )
                previous_observation_timestamp = observation_timestamp
                label = 0
                if label_reader is not None:
                    label_row = next(label_reader, None)
                    if label_row is None or len(label_row) != 2 or label_row[1] not in {"0", "1"}:
                        raise ValueError(
                            f"HAI label alignment failed at {label_path}:{row_number + 2}"
                        )
                    label_timestamp, label_resolution = _parse_hai_timestamp(
                        label_row[0], source=label_path, row_number=row_number + 2
                    )
                    observed_label_resolutions.add(label_resolution)
                    if (
                        previous_label_timestamp is not None
                        and (
                            label_timestamp < previous_label_timestamp
                            or (
                                label_resolution != "minute"
                                and label_timestamp == previous_label_timestamp
                            )
                        )
                    ):
                        raise ValueError(
                            f"HAI label timestamps are not monotonic at "
                            f"{label_path}:{row_number + 2}"
                        )
                    previous_label_timestamp = label_timestamp
                    if label_resolution == "minute":
                        aligned = observation_timestamp.replace(
                            second=0, microsecond=0
                        ) == label_timestamp.replace(second=0, microsecond=0)
                    else:
                        aligned = observation_timestamp == label_timestamp
                    if not aligned:
                        raise ValueError(
                            f"HAI timestamp alignment failed at {label_path}:{row_number + 2}: "
                            f"observation={row[0]!r}, label={label_row[0]!r}, "
                            f"resolution={label_resolution}"
                        )
                    label = int(label_row[1])
                if label and not in_attack:
                    event_index += 1
                    in_attack = True
                elif not label:
                    in_attack = False
                if label:
                    row_events.add(f"{observation_path.name}:event-{event_index:04d}")
                rows.append(values)
                row_timestamps.append(observation_timestamp)
                if len(rows) < block_rows:
                    continue
                block_label = 1 if row_events else 0
                name = "attack" if block_label else "normal"
                counts[name] += 1
                start = block_index * block_rows
                unit_id = f"hai-23.05:{observation_path.name}:rows-{start:09d}-{start + block_rows - 1:09d}"
                unit = AcademicUnit(
                    unit_id=unit_id,
                    group_id=canonical_json_hash(
                        {
                            "projection": "hai-detector-visible-time-series-block-v2",
                            "values": rows,
                        }
                    ),
                    native_partition=native_partition,
                    assigned_partition=assigned_partition,
                    label=block_label,
                    class_name="Attack" if block_label else "Normal",
                    values=tuple(rows),
                    source_path=observation_path.name,
                    source_sha256=source_sha256,
                    order=start,
                    event_ids=tuple(sorted(row_events)),
                    evidence_origin="official_native",
                    resampling_cluster_id=f"hai-23.05:{observation_path.name}",
                )
                if total_cap is not None:
                    # Test selection is label-blind: the published truth does
                    # not decide which blocks enter evaluation.
                    _priority_reservoir_add(
                        selected_all,
                        unit,
                        cap=total_cap + rank_start if total_cap else 0,
                        seed=seed,
                    )
                else:
                    cap = attack_cap if block_label else normal_cap
                    _priority_reservoir_add(
                        selected[block_label],
                        unit,
                        cap=cap + rank_start if cap else 0,
                        seed=seed,
                    )
                rows = []
                row_timestamps = []
                row_events = set()
                block_index += 1
            if rows:
                counts["dropped_partial"] = len(rows)
            if label_reader is not None and next(label_reader, None) is not None:
                raise ValueError(f"HAI labels exceed observations: {label_path}")
            if len(observed_label_resolutions) > 1:
                raise ValueError(
                    f"HAI label timestamp resolution changes within {label_path}: "
                    f"{sorted(observed_label_resolutions)}"
                )
            counts["timestamp_alignment"] = {
                "observation_policy": "strictly-increasing parsed timestamps",
                "label_policy": (
                    "exact-second equality when seconds are present; "
                    "minute-floor equality for minute-resolution labels"
                ),
                "label_resolutions": sorted(observed_label_resolutions),
                "passed": True,
            }
        finally:
            if label_handle is not None:
                label_handle.close()
    if total_cap is not None:
        retained = _priority_slice(
            selected_all, cap=total_cap, rank_start=rank_start, seed=seed,
            stratum=f"{assigned_partition}:{observation_path.name}:all",
        )
    else:
        retained = []
        for block_label, cap in ((0, normal_cap), (1, attack_cap)):
            if not selected[block_label] and cap == 0:
                continue
            retained.extend(
                _priority_slice(
                    selected[block_label], cap=cap, rank_start=rank_start, seed=seed,
                    stratum=(
                        f"{assigned_partition}:{observation_path.name}:"
                        f"{'attack' if block_label else 'normal'}"
                    ),
                )
            )
    retained.sort(key=lambda unit: unit.order)
    counts["selected_normal"] = sum(unit.label == 0 for unit in retained)
    counts["selected_attack"] = sum(unit.label == 1 for unit in retained)
    counts["phase_rank_start"] = rank_start
    counts["selected_detector_input_identities"] = [
        unit.group_id for unit in retained
    ]
    return retained, feature_names, counts


def _priority_reservoir_add(
    heap: list[tuple[int, str, AcademicUnit]],
    unit: AcademicUnit,
    *,
    cap: int,
    seed: int,
) -> None:
    if cap < 0:
        raise ValueError("Reservoir cap cannot be negative.")
    priority = _stable_priority(seed, unit.unit_id)
    item = (-priority, unit.unit_id, unit)
    if cap == 0:
        heap.append(item)
        return
    if len(heap) < cap:
        heapq.heappush(heap, item)
        return
    if priority < -heap[0][0]:
        heapq.heapreplace(heap, item)


def _deduplicate_content_units(
    units: Sequence[AcademicUnit],
) -> tuple[list[AcademicUnit], dict[str, object]]:
    """Collapse byte-identical recording copies without crossing partitions."""

    by_group: dict[str, list[AcademicUnit]] = {}
    for unit in units:
        by_group.setdefault(unit.group_id, []).append(unit)
    retained: list[AcademicUnit] = []
    contradictory: dict[str, list[dict[str, object]]] = {}
    removed_copies = 0
    partition_preference = {"train": 0, "validation": 1, "test": 2}
    for group_id, group in sorted(by_group.items()):
        semantics = {(unit.label, unit.class_name) for unit in group}
        if len(semantics) != 1:
            contradictory[group_id] = [unit.identity_dict() for unit in group]
            continue
        retained.append(
            min(
                group,
                key=lambda unit: (
                    partition_preference[unit.assigned_partition],
                    unit.unit_id,
                ),
            )
        )
        removed_copies += len(group) - 1
    retained.sort(key=lambda unit: (unit.assigned_partition, unit.order, unit.unit_id))
    return retained, {
        "identity": "SHA-256 of the normalized detector-visible syscall-name stream",
        "deduplicated_copy_count": removed_copies,
        "contradictory_content_hash_groups_excluded": len(contradictory),
        "contradictory_groups": contradictory,
    }


def _sliding_windows(
    values: Sequence[tuple[float | str, ...]],
    *,
    sequence_length: int,
    stride: int,
    max_windows: int,
) -> Iterator[tuple[int, tuple[tuple[float | str, ...], ...]]]:
    if not values:
        return
    feature_count = len(values[0])
    if any(len(row) != feature_count for row in values):
        raise ValueError("Feature count changed within a source unit.")
    if len(values) <= sequence_length:
        padding_value: float | str = PAD_TOKEN if isinstance(values[0][0], str) else 0.0
        padded = list(values)
        padded.extend(
            [tuple(padding_value for _ in range(feature_count))]
            * (sequence_length - len(values))
        )
        yield 0, tuple(padded)
        return
    starts = list(range(0, len(values) - sequence_length + 1, stride))
    tail = len(values) - sequence_length
    if starts[-1] != tail:
        starts.append(tail)
    if len(starts) > max_windows:
        positions = np.linspace(0, len(starts) - 1, max_windows, dtype=int)
        starts = sorted({starts[index] for index in positions.tolist()})
    for start in starts:
        yield start, tuple(values[start : start + sequence_length])


def _pad_single_sequence(
    values: Sequence[tuple[float | str, ...]], *, sequence_length: int
) -> tuple[tuple[float | str, ...], ...]:
    if not values:
        raise ValueError("A preselected sequence cannot be empty.")
    if len(values) > sequence_length:
        raise ValueError("A preselected sequence exceeds the configured sequence length.")
    feature_count = len(values[0])
    if any(len(row) != feature_count for row in values):
        raise ValueError("Feature count changed within a preselected sequence.")
    padding_value: float | str = PAD_TOKEN if isinstance(values[0][0], str) else 0.0
    padded = list(values)
    padded.extend(
        [tuple(padding_value for _ in range(feature_count))]
        * (sequence_length - len(values))
    )
    return tuple(padded)


def _resolve_path(project_root: Path, configured: str) -> Path:
    if not configured:
        raise ValueError("Academic dataset root is required in the frozen config.")
    path = Path(configured)
    if not path.is_absolute():
        path = project_root / path
    return path.resolve()


def _stable_priority(seed: int, identity: str) -> int:
    digest = sha256(f"{seed}:{identity}".encode("utf-8")).digest()
    return int.from_bytes(digest[:8], "big")


def _stable_cap(
    paths: Sequence[Path],
    cap: int,
    seed: int,
    root: Path,
    *,
    offset: int = 0,
    require_exact: bool = False,
) -> list[Path]:
    if cap < 0 or offset < 0:
        raise ValueError("Stable priority cap and offset must be non-negative.")
    if offset and cap == 0:
        raise ValueError("A disjoint stable-priority slice requires an explicit positive cap.")
    ranked = sorted(
        paths,
        key=lambda path: _stable_priority(seed, path.relative_to(root).as_posix()),
    )
    if cap == 0:
        return ranked
    selected = ranked[offset : offset + cap]
    if require_exact and len(selected) != cap:
        raise ValueError(
            f"Stable priority slice [{offset}, {offset + cap}) exceeds available support "
            f"({len(ranked)} candidates)."
        )
    return selected


def _stable_unit_slice(
    units: Sequence[AcademicUnit],
    *,
    cap: int,
    offset: int,
    seed: int,
    stratum: str,
    require_exact: bool = False,
) -> list[AcademicUnit]:
    if cap < 0 or offset < 0:
        raise ValueError(f"Invalid stable unit slice for {stratum!r}.")
    if offset and cap == 0:
        raise ValueError(
            f"Disjoint stable unit slice {stratum!r} requires an explicit positive cap."
        )
    ranked = sorted(
        units,
        key=lambda unit: (_stable_priority(seed, unit.unit_id), unit.unit_id),
    )
    if cap == 0:
        return ranked
    selected = ranked[offset : offset + cap]
    if require_exact and len(selected) != cap:
        raise ValueError(
            f"Stable unit slice {stratum!r} [{offset}, {offset + cap}) exceeds "
            f"available support ({len(ranked)} candidates)."
        )
    return selected


def _priority_slice(
    retained: Sequence[tuple[int, str, AcademicUnit]],
    *,
    cap: int,
    rank_start: int,
    seed: int,
    stratum: str,
) -> list[AcademicUnit]:
    if cap < 0 or rank_start < 0:
        raise ValueError(f"Invalid priority slice for {stratum!r}.")
    if rank_start and cap == 0:
        raise ValueError(
            f"Disjoint priority slice {stratum!r} requires an explicit positive cap."
        )
    units = [item[2] for item in retained]
    ranked = sorted(units, key=lambda unit: (_stable_priority(seed, unit.unit_id), unit.unit_id))
    if cap == 0:
        return ranked
    selected = ranked[rank_start : rank_start + cap]
    if rank_start and len(selected) != cap:
        raise ValueError(
            f"Priority slice {stratum!r} [{rank_start}, {rank_start + cap}) exceeds "
            f"available support ({len(ranked)} retained candidates)."
        )
    return selected


def _phase_rank_start(
    config: Mapping[str, object],
    phase: str,
    stratum: str,
    *,
    fallback: str | None = None,
) -> int:
    allocation = config.get("phase_allocation")
    if allocation is None:
        return 0
    if not isinstance(allocation, Mapping):
        raise ValueError("phase_allocation must be an object.")
    if allocation.get("method") not in PHASE_ALLOCATION_METHODS:
        raise ValueError(
            "phase_allocation.method must be one of "
            f"{sorted(PHASE_ALLOCATION_METHODS)!r}."
        )
    phase_record = allocation.get(phase)
    if not isinstance(phase_record, Mapping):
        raise ValueError(f"phase_allocation.{phase} must be an object.")
    offsets = phase_record.get("offsets")
    if not isinstance(offsets, Mapping):
        raise ValueError(f"phase_allocation.{phase}.offsets must be an object.")
    key = stratum if stratum in offsets else fallback
    if key is None or key not in offsets:
        raise ValueError(
            f"phase_allocation.{phase}.offsets has no entry for stratum {stratum!r}."
        )
    raw = offsets[key]
    if not isinstance(raw, int) or isinstance(raw, bool) or raw < 0:
        raise ValueError(
            f"phase_allocation.{phase}.offsets.{key} must be a non-negative integer."
        )
    return int(raw)


def _phase_allocation_audit(
    config: Mapping[str, object], phase: str
) -> dict[str, object]:
    allocation = config.get("phase_allocation")
    if allocation is None:
        return {
            "method": "legacy-no-cross-phase-isolation",
            "phase": phase,
            "offsets": {},
            "passed": False,
            "limitation": "pilot and confirmatory source units are not guaranteed disjoint",
        }
    if not isinstance(allocation, Mapping):
        raise ValueError("phase_allocation must be an object.")
    if allocation.get("method") not in PHASE_ALLOCATION_METHODS:
        raise ValueError("Unsupported phase allocation method.")
    phase_record = allocation.get(phase)
    if not isinstance(phase_record, Mapping):
        raise ValueError(f"phase_allocation.{phase} must be an object.")
    offsets = phase_record.get("offsets")
    if not isinstance(offsets, Mapping) or not offsets:
        raise ValueError(f"phase_allocation.{phase}.offsets must be non-empty.")
    if any(
        not isinstance(value, int) or isinstance(value, bool) or value < 0
        for value in offsets.values()
    ):
        raise ValueError("Phase allocation offsets must be non-negative integers.")
    normalized = {str(key): int(value) for key, value in offsets.items()}
    return {
        "method": allocation.get("method"),
        "phase": phase,
        "offsets": normalized,
        "identity": canonical_json_hash(
            {"method": allocation.get("method"), "phase": phase, "offsets": normalized}
        ),
        "passed": True,
    }


def _phase_caps(config: Mapping[str, object], phase: str) -> dict[str, object]:
    raw = config.get("phase_caps", {})
    if not isinstance(raw, Mapping):
        raise ValueError("phase_caps must be an object.")
    selected = raw.get(phase, {})
    if not isinstance(selected, Mapping):
        raise ValueError(f"phase_caps.{phase} must be an object.")
    return {str(key): value for key, value in selected.items()}


def _cap(caps: Mapping[str, object], name: str) -> int:
    value = int(caps.get(name, 0))
    if value < 0:
        raise ValueError(f"Cap {name!r} cannot be negative.")
    return value


def _hai_cap(
    caps: Mapping[str, object], partition: str, label_name: str
) -> int:
    raw = caps.get(partition, {})
    if not isinstance(raw, Mapping):
        raise ValueError(f"HAI cap {partition!r} must be an object.")
    value = int(raw.get(label_name, 0))
    if value < 0:
        raise ValueError(f"HAI cap {partition}.{label_name} cannot be negative.")
    return value


def _hai_total_cap(
    caps: Mapping[str, object], partition: str
) -> int | None:
    raw = caps.get(partition, {})
    if not isinstance(raw, Mapping):
        raise ValueError(f"HAI cap {partition!r} must be an object.")
    if "total" not in raw:
        return None
    value = int(raw["total"])
    if value < 0:
        raise ValueError(f"HAI cap {partition}.total cannot be negative.")
    return value


__all__ = [
    "AcademicDataset",
    "AcademicUnit",
    "AcademicWindow",
    "PARTITIONS",
    "PreparedDataset",
    "PreparedPartition",
    "PreprocessingState",
    "WindowedDataset",
    "aggregate_window_scores",
    "audit_group_leakage",
    "audit_window_parentage",
    "canonical_json_hash",
    "file_sha256",
    "fit_preprocessing",
    "load_academic_dataset",
    "prepare_dataset_arrays",
    "support_summary",
    "validate_academic_support",
    "window_dataset",
]
