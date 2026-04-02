"""Object-store adapters for valid artifact persistence."""

from __future__ import annotations

from dataclasses import dataclass
import importlib.util
import io
import json
from pathlib import Path


@dataclass(frozen=True)
class MinioStoreConfig:
    """Connection settings for the local MinIO-compatible artifact store."""

    endpoint: str
    access_key: str
    secret_key: str
    bucket: str
    secure: bool = False


class MinioArtifactStore:
    """Small JSON artifact writer aligned to the local MinIO boundary."""

    def __init__(
        self,
        config: MinioStoreConfig,
        *,
        client=None,
    ) -> None:
        self.config = config
        self._client = client

    def save_json(self, object_name: str, payload: dict[str, object]) -> str:
        """Persist one JSON payload and return the object key."""

        client = self._ensure_client()
        if not client.bucket_exists(self.config.bucket):
            client.make_bucket(self.config.bucket)

        encoded = json.dumps(payload, indent=2).encode("utf-8")
        client.put_object(
            self.config.bucket,
            object_name,
            io.BytesIO(encoded),
            length=len(encoded),
            content_type="application/json",
        )
        return object_name

    def _ensure_client(self):
        if self._client is not None:
            return self._client
        if importlib.util.find_spec("minio") is None:
            raise RuntimeError(
                "MinIO artifact persistence requires the 'minio' package. "
                "Install project dependencies before using Story 3.4 runtime persistence."
            )
        from minio import Minio

        self._client = Minio(
            self.config.endpoint,
            access_key=self.config.access_key,
            secret_key=self.config.secret_key,
            secure=self.config.secure,
        )
        return self._client


class FileArtifactStore:
    """Small local file-backed artifact writer for demo-friendly persistence."""

    def __init__(self, root_path: Path) -> None:
        self.root_path = Path(root_path)

    def save_json(self, object_name: str, payload: dict[str, object]) -> str:
        """Persist one JSON payload under the configured local root."""

        target_path = self.resolve_path(object_name)
        target_path.parent.mkdir(parents=True, exist_ok=True)
        target_path.write_text(json.dumps(payload, indent=2), encoding="utf-8")
        return object_name

    def resolve_path(self, object_name: str) -> Path:
        """Resolve one logical object key to a local file path."""

        return self.root_path / Path(object_name)
