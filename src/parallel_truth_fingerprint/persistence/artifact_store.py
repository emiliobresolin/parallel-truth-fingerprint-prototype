"""Object-store adapters for valid artifact persistence."""

from __future__ import annotations

from dataclasses import dataclass
import importlib.util
import io
import json


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

    def list_json_objects(self, prefix: str = "") -> tuple[str, ...]:
        """List JSON object keys under the configured bucket and prefix."""

        client = self._ensure_client()
        if not client.bucket_exists(self.config.bucket):
            return ()

        object_names = [
            item.object_name
            for item in client.list_objects(
                self.config.bucket,
                prefix=prefix,
                recursive=True,
            )
            if item.object_name.endswith(".json")
        ]
        return tuple(sorted(object_names))

    def load_json(self, object_name: str) -> dict[str, object]:
        """Load one JSON payload from the configured bucket."""

        client = self._ensure_client()
        response = client.get_object(self.config.bucket, object_name)
        try:
            payload = response.read().decode("utf-8")
        finally:
            close = getattr(response, "close", None)
            if callable(close):
                close()
            release_conn = getattr(response, "release_conn", None)
            if callable(release_conn):
                release_conn()
        return json.loads(payload)

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
