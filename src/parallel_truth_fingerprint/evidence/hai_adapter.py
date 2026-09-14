"""Version-pinned, native-schema HAI 23.05 inspection.

HAI is kept as its published multivariate industrial-control dataset.  In
particular, tags are never renamed as compressor sensors and are never
converted to mA.  Labels are read only from the two published label files and
are returned separately from observations.
"""
from __future__ import annotations
import csv
from dataclasses import dataclass
from hashlib import sha256
from pathlib import Path
from typing import Iterator


_OBSERVATION_FILES = ("hai-train1.csv", "hai-train2.csv", "hai-train3.csv", "hai-train4.csv", "hai-test1.csv", "hai-test2.csv")
_LABEL_BY_TEST = {"hai-test1.csv": "label-test1.csv", "hai-test2.csv": "label-test2.csv"}


class Hai2305LayoutError(ValueError):
    """The on-disk bytes cannot be interpreted as the published 23.05 layout."""


@dataclass(frozen=True)
class HaiFileManifest:
    file_name: str
    role: str
    row_count: int
    columns: tuple[str, ...]
    first_timestamp: str
    last_timestamp: str
    content_sha256: str


@dataclass(frozen=True)
class Hai2305Manifest:
    root: Path
    observations: tuple[HaiFileManifest, ...]
    labels: tuple[HaiFileManifest, ...]
    version_id: str = "HAI-23.05"
    schema_version: str = "HAI-23.05-native-csv-v1"


def inspect_hai_23_05(root: Path) -> Hai2305Manifest:
    """Validate all official files, chronology and positional label alignment.

    This streaming inspection is intentionally explicit and fail-closed.  It
    does not coerce values, load truth into observations, or publish anything.
    """
    root = Path(root)
    expected = (*_OBSERVATION_FILES, "label-test1.csv", "label-test2.csv")
    missing = [name for name in expected if not (root / name).is_file()]
    if missing:
        raise Hai2305LayoutError(f"HAI-23.05 missing required files: {missing}")
    observations = tuple(_inspect_csv(root / name, role="train" if name.startswith("hai-train") else "test", require_label=False) for name in _OBSERVATION_FILES)
    labels = tuple(_inspect_csv(root / name, role="restricted-evaluation-truth", require_label=True) for name in ("label-test1.csv", "label-test2.csv"))
    by_name = {item.file_name: item for item in (*observations, *labels)}
    for test_name, label_name in _LABEL_BY_TEST.items():
        test, label = by_name[test_name], by_name[label_name]
        # HAI 23.05's published labels use a coarser timestamp representation
        # (and label-test2 repeats it) than the second-resolution observation
        # stream.  The release therefore defines truth alignment by row order,
        # not by equality or monotonicity of the label timestamp column.
        if test.row_count != label.row_count:
            raise Hai2305LayoutError(f"HAI-23.05 label alignment failed for {test_name} and {label_name}")
    return Hai2305Manifest(root=root.resolve(), observations=observations, labels=labels)


def iter_native_observations(path: Path) -> Iterator[tuple[str, dict[str, float]]]:
    """Yield timestamped native tag values from one checked HAI CSV.

    Callers receive no labels from this boundary.  Invalid numeric fields and
    timestamp disorder are rejected rather than filled or interpolated.
    """
    previous: str | None = None
    with Path(path).open("r", encoding="utf-8", newline="") as handle:
        reader = csv.DictReader(handle)
        if not reader.fieldnames or reader.fieldnames[0] != "timestamp" or len(reader.fieldnames) < 2:
            raise Hai2305LayoutError(f"Unsupported HAI observation schema in {path}")
        for row_number, row in enumerate(reader, start=2):
            timestamp = row.get("timestamp")
            if not timestamp or (previous is not None and timestamp <= previous):
                raise Hai2305LayoutError(f"Non-monotonic HAI timestamp at {path}:{row_number}")
            try:
                tags = {name: float(row[name]) for name in reader.fieldnames[1:]}
            except (KeyError, TypeError, ValueError) as exc:
                raise Hai2305LayoutError(f"Invalid native HAI value at {path}:{row_number}") from exc
            previous = timestamp
            yield timestamp, tags


def iter_native_labels(path: Path) -> Iterator[tuple[str, int]]:
    """Yield published HAI evaluation labels without attaching them to rows.

    Keeping this iterator separate from ``iter_native_observations`` prevents
    a feature adapter from accidentally treating ground truth as an input.
    A benchmark adapter may zip both streams only after verifying timestamp
    alignment.
    """

    with Path(path).open("r", encoding="utf-8", newline="") as handle:
        reader = csv.DictReader(handle)
        if tuple(reader.fieldnames or ()) != ("timestamp", "label"):
            raise Hai2305LayoutError(f"Unsupported HAI label schema in {path}")
        for row_number, row in enumerate(reader, start=2):
            timestamp = row.get("timestamp")
            raw_label = row.get("label")
            if not timestamp or raw_label not in {"0", "1"}:
                raise Hai2305LayoutError(f"Invalid HAI label at {path}:{row_number}")
            yield timestamp, int(raw_label)


def _inspect_csv(path: Path, *, role: str, require_label: bool) -> HaiFileManifest:
    digest = sha256()
    with path.open("rb") as binary:
        for chunk in iter(lambda: binary.read(1024 * 1024), b""):
            digest.update(chunk)
    with path.open("r", encoding="utf-8", newline="") as handle:
        reader = csv.DictReader(handle)
        columns = tuple(reader.fieldnames or ())
        required = ("timestamp", "label") if require_label else ("timestamp",)
        if not columns or columns[:len(required)] != required or (not require_label and len(columns) < 2):
            raise Hai2305LayoutError(f"Unsupported HAI-23.05 schema in {path}")
        previous: str | None = None
        first: str | None = None
        count = 0
        for row_number, row in enumerate(reader, start=2):
            timestamp = row.get("timestamp")
            if not timestamp or (
                not require_label and previous is not None and timestamp <= previous
            ):
                raise Hai2305LayoutError(f"Non-monotonic HAI timestamp at {path}:{row_number}")
            if require_label and row.get("label") not in {"0", "1"}:
                raise Hai2305LayoutError(f"Invalid HAI label at {path}:{row_number}")
            if not require_label:
                try:
                    for column in columns[1:]:
                        float(row[column])
                except (KeyError, TypeError, ValueError) as exc:
                    raise Hai2305LayoutError(f"Invalid native HAI value at {path}:{row_number}") from exc
            first = first or timestamp
            previous = timestamp
            count += 1
    if count == 0 or first is None or previous is None:
        raise Hai2305LayoutError(f"Empty HAI CSV: {path}")
    return HaiFileManifest(path.name, role, count, columns, first, previous, f"sha256:{digest.hexdigest()}")


@dataclass(frozen=True)
class HaiAdapterAdmission:
 admitted:bool; version_id:str; reason:str|None; authorization_effect:str="none"
def admit_hai_adapter(*,source_manifest_id:str,adapter_code_id:str,layout_hash:str,requested_version_id:str)->HaiAdapterAdmission:
 if any(not x.startswith("sha256:") for x in (source_manifest_id,adapter_code_id,layout_hash,requested_version_id)):return HaiAdapterAdmission(False,requested_version_id,"HAI-IDENTITY")
 return HaiAdapterAdmission(True,requested_version_id,None)
