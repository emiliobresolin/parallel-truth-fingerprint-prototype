"""Filesystem-backed store mirroring the MinioArtifactStore contract.

Lets the offline training track persist real artifacts (training records,
sweep results, promotion pointers) to disk when a real MinIO instance is
not available. Same method surface as `MinioArtifactStore`:

    save_json(object_name, payload) -> str
    save_bytes(object_name, payload, content_type=...) -> str
    list_json_objects(prefix='') -> tuple[str, ...]
    load_json(object_name) -> dict
    load_bytes(object_name) -> bytes
    .config.bucket -> str
"""

from __future__ import annotations

from dataclasses import dataclass
import json
from pathlib import Path


@dataclass(frozen=True)
class LocalFileStoreConfig:
    """Roughly mirrors MinioStoreConfig so callers can swap stores."""

    bucket: str
    root_path: Path


class LocalFileArtifactStore:
    """Filesystem-backed artifact store with a MinIO-compatible surface."""

    def __init__(self, config: LocalFileStoreConfig) -> None:
        self.config = config
        self._bucket_root = Path(config.root_path) / config.bucket
        self._bucket_root.mkdir(parents=True, exist_ok=True)

    def save_json(self, object_name: str, payload: dict[str, object]) -> str:
        target = self._bucket_root / object_name
        target.parent.mkdir(parents=True, exist_ok=True)
        target.write_text(json.dumps(payload, indent=2), encoding="utf-8")
        return object_name

    def save_bytes(
        self,
        object_name: str,
        payload: bytes,
        *,
        content_type: str = "application/octet-stream",
    ) -> str:
        del content_type  # disk store has no MIME tagging
        target = self._bucket_root / object_name
        target.parent.mkdir(parents=True, exist_ok=True)
        target.write_bytes(payload)
        return object_name

    def list_json_objects(self, prefix: str = "") -> tuple[str, ...]:
        base = self._bucket_root / prefix
        # If the prefix points at a directory we walk it; otherwise we
        # fall back to a recursive glob from the bucket root.
        candidates: list[Path] = []
        if base.is_dir():
            for path in sorted(base.rglob("*.json")):
                candidates.append(path)
        else:
            for path in sorted(self._bucket_root.rglob("*.json")):
                relative = path.relative_to(self._bucket_root).as_posix()
                if relative.startswith(prefix):
                    candidates.append(path)
        return tuple(
            path.relative_to(self._bucket_root).as_posix()
            for path in candidates
        )

    def load_json(self, object_name: str) -> dict[str, object]:
        target = self._bucket_root / object_name
        if not target.is_file():
            raise FileNotFoundError(
                f"Object not found in local store: {object_name!r} "
                f"(looked under {self._bucket_root})."
            )
        return json.loads(target.read_text(encoding="utf-8"))

    def load_bytes(self, object_name: str) -> bytes:
        target = self._bucket_root / object_name
        if not target.is_file():
            raise FileNotFoundError(
                f"Object not found in local store: {object_name!r}."
            )
        return target.read_bytes()
