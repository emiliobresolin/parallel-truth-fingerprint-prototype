"""Deterministic, read-only collection for the v1 evidence baseline."""

from __future__ import annotations

import hashlib
import json
import os
import platform
import re
import subprocess
import sys
import uuid
from dataclasses import replace
from datetime import datetime
from pathlib import Path, PureWindowsPath
from typing import Iterable, Mapping
from urllib.parse import urlsplit

from parallel_truth_fingerprint.contracts.v1_baseline import (
    BaselineEntry,
    BaselineValidationResult,
    DirtyOverlay,
    RepositoryIdentity,
    V1BaselineManifest,
)


VERIFICATION_STATUSES = frozenset(
    {"verified", "missing", "mutable", "corrupt", "unverifiable"}
)
SCIENTIFIC_STATUSES = frozenset(
    {
        "IMPLEMENTED_RUNTIME_EVIDENCE",
        "FIXTURE",
        "PUBLISHED_REFERENCE",
        "MEASURED_RESULT",
        "EXPERIMENTAL_FINGERPRINT_BASELINE",
        "LEGACY_BASELINE",
    }
)
SECRET_MARKERS = (
    "password",
    "secret",
    "token",
    "credential",
    "private",
    "access_key",
    "validator",
    "node_key",
)
SECRET_FILE_NAMES = frozenset(
    {".env", ".npmrc", ".pypirc", "auth.json", "id_rsa", "id_dsa", "id_ecdsa", "id_ed25519", "key.pem"}
)
DEFAULT_EXPECTED_INVENTORY: dict[str, tuple[str, ...]] = {
    "code": ("src", "abci/consensus_app", "scripts"),
    "dependencies": (
        "pyproject.toml",
        "uv.lock",
        "abci/consensus_app/go.mod",
        "abci/consensus_app/go.sum",
        "abci/consensus_app/Dockerfile",
    ),
    "configuration": (".env.example", "compose.local.yml", "compose.consensus.yml"),
    "contracts": (
        "src/parallel_truth_fingerprint/contracts",
        "src/parallel_truth_fingerprint/edge_nodes/common/mqtt_io.py",
        "src/parallel_truth_fingerprint/consensus",
        "src/parallel_truth_fingerprint/scada",
        "src/parallel_truth_fingerprint/dashboard",
        "abci/consensus_app/internal/app",
    ),
    "legacy_baseline": (
        "_bmad-output/local-store/fingerprint-training-history",
        "_bmad-output/local-store/fingerprint-models",
    ),
    "known_absence": (
        "_bmad-output/local-store/fingerprint-models/fingerprint-models/"
        "run-adfa-ld-embed-binary-lstm-embedding-classifier-20260602T175338-3acfb039.weights.h5",
        "_bmad-output/local-store/fingerprint-training-history/fingerprint-training-history/runs/"
        "run-adfa-ld-embed-binary-lstm-embedding-classifier-20260602T175338-3acfb039.json",
        "fingerprint-datasets.zip",
    ),
    "recorded_results": (
        "docs/seminario-andamento/tables/adfa-ld-binary-results.csv",
        "docs/seminario-andamento/tables/adfa-ld-binary-results.md",
        "docs/seminario-andamento/tables/adfa-ld-multiclass-results.csv",
        "docs/seminario-andamento/tables/adfa-ld-multiclass-results.md",
        "docs/seminario-andamento/tables/champion-run-summary.csv",
        "docs/seminario-andamento/tables/champion-run-summary.md",
        "docs/seminario-andamento/tables/confusion-matrix.csv",
        "docs/seminario-andamento/tables/confusion-matrix.md",
        "docs/seminario-andamento/tables/champion-class-metrics.csv",
        "docs/seminario-andamento/tables/champion-class-metrics.md",
        "docs/seminario-andamento/tables/adfa-ld-dataset-summary.csv",
        "docs/seminario-andamento/tables/adfa-ld-dataset-summary.md",
        "docs/seminario-andamento/tables/custom-dataset-summary.csv",
        "docs/seminario-andamento/tables/custom-dataset-summary.md",
        "docs/seminario-andamento/tables/validation-scenarios.csv",
        "docs/seminario-andamento/tables/validation-scenarios.md",
    ),
    "runtime_observations": (
        "_bmad-output/results-evidence",
        "docs/seminario-andamento/evidence",
        "logs",
    ),
    "datasets": (
        "_bmad-output/local-store/fingerprint-datasets",
        "datasets/ADFA-LD",
        "datasets/ADFA-LD.zip",
    ),
    "fixtures": ("tests/lstm_service/offline_training/fixtures",),
    "mutable_pointer": (
        "_bmad-output/local-store/fingerprint-training-history/"
        "fingerprint-training-history/index/latest.json",
    ),
    "reference": ("docs/reference-archive/catalog/checksums.sha256",),
}
REDACTED_CONFIGURATION_LOCATORS = frozenset(DEFAULT_EXPECTED_INVENTORY["configuration"])
EXCLUDED_DIRECTORY_NAMES = frozenset({".git", ".venv", "__pycache__", "build", ".pytest_cache"})
APPROVED_CONFIG_KEYS = frozenset(
    {
        "PROJECT_NAME",
        "PYTHONPATH",
        "MQTT_TRANSPORT",
        "MQTT_BROKER_HOST",
        "MQTT_BROKER_PORT",
        "MQTT_TOPIC",
        "COMETBFT_RPC_URL",
        "DEMO_STEPS",
        "DEMO_CYCLE_INTERVAL_SECONDS",
        "DEMO_MAX_CYCLES",
        "DEMO_TRAIN_AFTER_ELIGIBLE_CYCLES",
        "DEMO_FINGERPRINT_SEQUENCE_LENGTH",
        "DEMO_POWER",
        "DEMO_DASHBOARD_HOST",
        "DEMO_DASHBOARD_PORT",
        "DEMO_SCENARIO",
        "DEMO_SCENARIO_START_CYCLE",
        "DEMO_FAULT_MODE",
        "DEMO_FAULTY_EDGES",
        "DEMO_SCADA_MODE",
        "DEMO_SCADA_START_CYCLE",
        "DEMO_SCADA_OFFSET_VALUE",
        "MINIO_ENDPOINT",
        "MINIO_BUCKET",
        "MINIO_SECURE",
        "KERAS_BACKEND",
        "LSTM_SERVICE_HOST",
        "LSTM_SERVICE_PORT",
    }
)
DECLARED_EXTERNAL_STORAGE = (
    "minio://valid-consensus-artifacts/",
    "minio://fingerprint-datasets/",
    "minio://fingerprint-models/",
    "minio://fingerprint-training-history/runs/",
    "minio://fingerprint-training-history/index/by-benchmark/",
)
ROLE_SCIENTIFIC_STATUS = {
    "implementation": "IMPLEMENTED_RUNTIME_EVIDENCE",
    "source": "IMPLEMENTED_RUNTIME_EVIDENCE",
    "redacted_configuration_identity": "IMPLEMENTED_RUNTIME_EVIDENCE",
    "declared_container_image": "IMPLEMENTED_RUNTIME_EVIDENCE",
    "reference": "PUBLISHED_REFERENCE",
    "recorded_result": "MEASURED_RESULT",
    "historical_result": "LEGACY_BASELINE",
    "historical_evidence": "EXPERIMENTAL_FINGERPRINT_BASELINE",
    "historical_detector": "LEGACY_BASELINE",
    "convenience_pointer": "LEGACY_BASELINE",
    "declared_storage_namespace": "LEGACY_BASELINE",
    "test_fixture": "FIXTURE",
    "runtime_observation": "IMPLEMENTED_RUNTIME_EVIDENCE",
    "runtime_identity": "IMPLEMENTED_RUNTIME_EVIDENCE",
    "historical_record": "LEGACY_BASELINE",
}
CATEGORY_SCIENTIFIC_STATUS = {
    "reference": "PUBLISHED_REFERENCE",
    "recorded_results": "LEGACY_BASELINE",
    "datasets": "EXPERIMENTAL_FINGERPRINT_BASELINE",
    "legacy_baseline": "LEGACY_BASELINE",
    "mutable_pointer": "LEGACY_BASELINE",
    "fixtures": "FIXTURE",
    "runtime_observations": "IMPLEMENTED_RUNTIME_EVIDENCE",
    "runtime_identity": "IMPLEMENTED_RUNTIME_EVIDENCE",
    "known_absence": "LEGACY_BASELINE",
}
CATEGORY_ROLES = {
    "code": frozenset({"implementation", "source"}),
    "dependencies": frozenset({"implementation", "source"}),
    "configuration": frozenset({"redacted_configuration_identity"}),
    "contracts": frozenset({"implementation", "source"}),
    "legacy_baseline": frozenset({"historical_detector"}),
    "recorded_results": frozenset({"historical_result"}),
    "datasets": frozenset({"historical_evidence"}),
    "mutable_pointer": frozenset({"convenience_pointer"}),
    "reference": frozenset({"reference"}),
    "fixtures": frozenset({"test_fixture"}),
    "image_reference": frozenset({"declared_container_image"}),
    "external_storage": frozenset({"declared_storage_namespace"}),
    "runtime_observations": frozenset({"runtime_observation"}),
    "runtime_identity": frozenset({"runtime_identity"}),
    "known_absence": frozenset({"historical_record"}),
}
CHILD_INVENTORY_CATEGORIES = frozenset(
    {"datasets", "fixtures", "legacy_baseline", "runtime_observations"}
)
ALLOWED_EVIDENCE_ROOT_CATEGORIES = frozenset(
    {"datasets", "fixtures", "legacy_baseline", "recorded_results", "reference", "runtime_observations"}
)
OVERLAY_ORIGINS = frozenset(
    {"tracked", "untracked", "ignored_evidence", "excluded_post_v1"}
)
SHA256_PATTERN = re.compile(r"^sha256:[0-9a-f]{64}$")
SHA1_PATTERN = re.compile(r"^sha1:[0-9a-f]{40}$")
OBSERVED_AT_PATTERN = re.compile(r"^\d{4}-\d{2}-\d{2}T\d{2}:\d{2}:\d{2}(?:\.\d+)?Z$")
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
SAFE_COMPOSE_VALUE_KEYS = frozenset(
    {
        "image",
        "build",
        "container_name",
        "hostname",
        "restart",
        "ports",
        "volumes",
        "networks",
        "depends_on",
        "profiles",
    }
)


class BaselineError(ValueError):
    """Raised when a baseline would be ambiguous, mutable, or unsafe."""


def canonical_json_bytes(payload: object) -> bytes:
    """Serialize the project canonical JSON form without claiming RFC 8785."""

    return json.dumps(
        payload,
        sort_keys=True,
        ensure_ascii=False,
        separators=(",", ":"),
        allow_nan=False,
    ).encode("utf-8")


def _sha256_bytes(payload: bytes) -> str:
    return "sha256:" + hashlib.sha256(payload).hexdigest()


def _file_signature(path: Path) -> tuple[int, int, int, int]:
    stat = path.stat(follow_symlinks=False)
    return (stat.st_dev, stat.st_ino, stat.st_size, stat.st_mtime_ns)


def sha256_file_stable(path: Path) -> tuple[str | None, str]:
    """Hash a regular file and identify a concurrent mutation conservatively."""

    try:
        if not path.is_file() or path.is_symlink():
            return None, "unverifiable"
        before = _file_signature(path)
        digest = hashlib.sha256()
        with path.open("rb", buffering=0) as stream:
            for chunk in iter(lambda: stream.read(1024 * 1024), b""):
                digest.update(chunk)
        after = _file_signature(path)
    except (OSError, ValueError):
        return None, "unverifiable"
    if before != after:
        return None, "mutable"
    return "sha256:" + digest.hexdigest(), "verified"


def normalize_local_locator(project_root: Path, target: Path) -> str:
    """Return a safe project-relative POSIX locator or fail closed."""

    root = project_root.resolve(strict=False)
    candidate = target.resolve(strict=False)
    try:
        relative = candidate.relative_to(root)
    except ValueError as error:
        raise BaselineError("local locator escapes allowlisted project root") from error
    if not relative.parts or any(part in {"", ".", ".."} for part in relative.parts):
        raise BaselineError("local locator is ambiguous")
    return relative.as_posix()


def _contains_secret_marker(value: str) -> bool:
    normalized = value.lower().replace("-", "_")
    return any(marker in normalized for marker in SECRET_MARKERS)


def _path_contains_secret_marker(path: Path) -> bool:
    return path.name.lower() in SECRET_FILE_NAMES or any(
        part.lower() in SECRET_FILE_NAMES or _contains_secret_marker(part) for part in path.parts
    )


def redact_configuration(
    value: object, *, allowed_keys: set[str]
) -> object:
    """Return an allowlisted, secret-free configuration view without hashes."""

    if isinstance(value, Mapping):
        sanitized: dict[str, object] = {}
        for key in sorted(value, key=str):
            key_text = str(key)
            if _contains_secret_marker(key_text) or key_text not in allowed_keys:
                continue
            child = redact_configuration(value[key], allowed_keys=allowed_keys)
            if child not in ({}, [], None):
                sanitized[key_text] = child
        return sanitized
    if isinstance(value, (list, tuple)):
        return [redact_configuration(item, allowed_keys=allowed_keys) for item in value]
    return value


def _is_safe_approved_config_value(key: str, value: str) -> bool:
    """Accept only non-secret representations for allowlisted config keys."""

    if not value or _contains_secret_marker(value) or "${" in value:
        return False
    if key == "COMETBFT_RPC_URL":
        parsed = urlsplit(value)
        return (
            parsed.scheme in {"http", "https"}
            and parsed.hostname is not None
            and parsed.username is None
            and parsed.password is None
            and not parsed.query
            and not parsed.fragment
        )
    return not any(marker in value for marker in ("@", "://", "\\"))


def _configuration_identity(path: Path, locator: str) -> tuple[str | None, int | None, str]:
    """Hash only an explicit allowlist of non-secret configuration values.

    The source file is read solely to derive this redacted view. Neither the raw
    text nor a digest over it is retained, so a secret-value change cannot enter
    a baseline identity.
    """

    try:
        text = path.read_text(encoding="utf-8")
    except (OSError, UnicodeError):
        return None, None, "unverifiable"
    if path.suffix.lower() in {".yml", ".yaml"}:
        safe_lines: list[str] = []
        redacted_keys: list[str] = []
        redacted_indent: int | None = None
        context: list[tuple[int, str]] = []
        for raw_line in text.splitlines():
            stripped = raw_line.strip()
            if not stripped or stripped.startswith("#"):
                continue
            indentation = len(raw_line) - len(raw_line.lstrip())
            if redacted_indent is not None:
                if indentation > redacted_indent:
                    continue
                redacted_indent = None
            while context and context[-1][0] >= indentation:
                context.pop()
            parent_key = context[-1][1] if context else ""
            list_environment = re.match(
                r"^-\s*([A-Za-z_][A-Za-z0-9_-]*)\s*=\s*(.*)$", stripped
            )
            if list_environment and parent_key == "environment":
                key, value = list_environment.groups()
                normalized_key = key.upper()
                if (
                    _contains_secret_marker(normalized_key)
                    or normalized_key not in APPROVED_CONFIG_KEYS
                    or not _is_safe_approved_config_value(normalized_key, value)
                ):
                    redacted_keys.append(normalized_key)
                    continue
                safe_lines.append(raw_line.rstrip())
                continue
            key_match = re.match(r"^(?:-\s*)?([A-Za-z_][A-Za-z0-9_-]*)\s*:", stripped)
            key = key_match.group(1) if key_match else ""
            if key and _contains_secret_marker(key):
                redacted_keys.append(key.upper())
                redacted_indent = indentation
                continue
            if _contains_secret_marker(stripped):
                redacted_keys.append("INLINE_SECRET_MARKER")
                continue
            if key_match:
                value = stripped[key_match.end() :].strip()
                if not value:
                    safe_lines.append(raw_line.rstrip())
                    context.append((indentation, key.lower()))
                    continue
                normalized_key = key.upper()
                if parent_key == "environment":
                    if (
                        normalized_key in APPROVED_CONFIG_KEYS
                        and _is_safe_approved_config_value(normalized_key, value)
                    ):
                        safe_lines.append(raw_line.rstrip())
                    else:
                        redacted_keys.append(normalized_key)
                    continue
                if key.lower() in SAFE_COMPOSE_VALUE_KEYS and _is_safe_compose_scalar(value):
                    safe_lines.append(raw_line.rstrip())
                else:
                    redacted_keys.append(normalized_key)
                continue
            if stripped.startswith("-") and parent_key in {"ports", "volumes", "networks", "profiles"}:
                if _is_safe_compose_scalar(stripped.removeprefix("-").strip()):
                    safe_lines.append(raw_line.rstrip())
        identity_view: object = {
            "locator": locator,
            "safe_compose_lines": safe_lines,
            "redacted_keys": sorted(set(redacted_keys)),
        }
    else:
        approved: dict[str, str] = {}
        redacted_keys = []
        for line in text.splitlines():
            match = re.match(r"^\s*([A-Za-z][A-Za-z0-9_]*)\s*(?:=|:)\s*(.*?)\s*$", line)
            if match is None:
                continue
            key, value = match.groups()
            normalized_key = key.upper()
            if _contains_secret_marker(normalized_key) or normalized_key not in APPROVED_CONFIG_KEYS:
                continue
            if _is_safe_approved_config_value(normalized_key, value):
                approved[normalized_key] = value
            else:
                redacted_keys.append(normalized_key)
        identity_view = {
            "locator": locator,
            "approved": approved,
            "redacted_keys": sorted(redacted_keys),
        }
    payload = canonical_json_bytes(identity_view)
    return _sha256_bytes(payload), len(payload), "verified"


def _observed_mutable_pointer_target(path: Path) -> tuple[str | None, bool]:
    """Read only an allowlisted target field from a small legacy JSON pointer."""

    try:
        payload = json.loads(path.read_text(encoding="utf-8"))
    except (OSError, UnicodeError, json.JSONDecodeError):
        return None, False
    if not isinstance(payload, dict):
        return None, False
    for key in ("target", "run_id", "artifact_id"):
        value = payload.get(key)
        if not isinstance(value, str) or not value or _contains_secret_marker(key):
            continue
        candidate = value.replace("\\", "/")
        if (
            candidate.startswith(("/", "~"))
            or Path(candidate).is_absolute()
            or PureWindowsPath(candidate).is_absolute()
            or ".." in Path(candidate).parts
            or "://" in candidate
            or "@" in candidate
            or _contains_secret_marker(candidate)
            or any(ord(character) < 32 for character in candidate)
        ):
            return None, False
        return candidate, True
    return None, False


def _mutable_pointer_identity(
    path: Path,
) -> tuple[str | None, int | None, str | None, str]:
    """Hash only the approved pointer target, never the complete legacy JSON."""

    try:
        before = _file_signature(path)
        observed_target, structurally_valid = _observed_mutable_pointer_target(path)
        after = _file_signature(path)
    except OSError:
        return None, None, None, "unverifiable"
    if before != after:
        return None, None, None, "mutable"
    if not structurally_valid or observed_target is None:
        return None, None, None, "corrupt"
    payload = canonical_json_bytes({"observed_target": observed_target})
    return _sha256_bytes(payload), len(payload), observed_target, "mutable"


def _is_safe_compose_scalar(value: str) -> bool:
    candidate = value.strip().strip("'\"")
    return bool(candidate) and not (
        _contains_secret_marker(candidate)
        or "${" in candidate
        or "://" in candidate
        or "@" in candidate
        or "\\" in candidate
        or any(ord(character) < 32 for character in candidate)
    )


def _declared_container_image_entries(project_root: Path) -> list[BaselineEntry]:
    """Inventory Compose image declarations without inspecting or pulling images."""

    entries: list[BaselineEntry] = []
    for relative_path in DEFAULT_EXPECTED_INVENTORY["configuration"]:
        path = project_root / relative_path
        if not path.exists() or _contains_secret_marker(path.name):
            continue
        try:
            locator = normalize_local_locator(project_root, path)
            lines = path.read_text(encoding="utf-8").splitlines()
        except (BaselineError, OSError, UnicodeError):
            continue
        image_index = 0
        for line in lines:
            match = re.match(r"^\s*image\s*:\s*['\"]?([^\s'\"#]+)", line)
            if match is None:
                continue
            image_index += 1
            reference = match.group(1)
            declares_digest = "@sha256:" in reference
            valid_digest = re.fullmatch(r"[^@\s]+@sha256:[0-9a-f]{64}", reference) is not None
            safe_reference = (
                "$" not in reference
                and not _contains_secret_marker(reference)
                and ("@" not in reference or valid_digest)
            )
            status = "unverifiable" if valid_digest else "mutable"
            limitation = (
                "digest-pinned declaration was observed locally; its image bytes were not inspected"
                if valid_digest
                else "invalid digest declaration was excluded as unverifiable metadata"
                if declares_digest
                else "tagged image declaration is mutable and was not inspected or pulled"
            )
            entries.append(
                BaselineEntry(
                    entry_id=f"image_reference:{locator}:{image_index}",
                    category="image_reference",
                    role="declared_container_image",
                    version=reference if safe_reference else None,
                    locator=f"{locator}#image/{image_index}",
                    byte_size=len(reference.encode("utf-8")) if safe_reference else None,
                    sha256=None,
                    verification_status=status if safe_reference else "unverifiable",
                    scientific_status="IMPLEMENTED_RUNTIME_EVIDENCE",
                    limitation=limitation if safe_reference or declares_digest else "image declaration was excluded as unsafe metadata",
                )
            )
    return entries


def _role_for_category(category: str) -> tuple[str, str]:
    if category == "configuration":
        return "redacted_configuration_identity", "IMPLEMENTED_RUNTIME_EVIDENCE"
    if category == "reference":
        return "reference", "PUBLISHED_REFERENCE"
    if category == "recorded_results":
        return "historical_result", "LEGACY_BASELINE"
    if category == "datasets":
        return "historical_evidence", "EXPERIMENTAL_FINGERPRINT_BASELINE"
    if category == "legacy_baseline":
        return "historical_detector", "LEGACY_BASELINE"
    if category == "mutable_pointer":
        return "convenience_pointer", "LEGACY_BASELINE"
    if category == "fixtures":
        return "test_fixture", "FIXTURE"
    if category == "runtime_observations":
        return "runtime_observation", "IMPLEMENTED_RUNTIME_EVIDENCE"
    if category == "runtime_identity":
        return "runtime_identity", "IMPLEMENTED_RUNTIME_EVIDENCE"
    if category == "known_absence":
        return "historical_record", "LEGACY_BASELINE"
    return "implementation", "IMPLEMENTED_RUNTIME_EVIDENCE"


def _directory_inventory(
    project_root: Path,
    directory: Path,
    excluded_locators: frozenset[str] = frozenset(),
) -> tuple[list[dict[str, object]], str]:
    records: list[dict[str, object]] = []
    if directory.name in EXCLUDED_DIRECTORY_NAMES:
        return [], "unverifiable"
    try:
        children = sorted(
            (
                child
                for child in directory.rglob("*")
                if child.is_file()
                and not any(
                    part in EXCLUDED_DIRECTORY_NAMES
                    for part in child.relative_to(directory).parts
                )
                and normalize_local_locator(project_root, child) not in excluded_locators
            ),
            key=lambda child: normalize_local_locator(project_root, child),
        )
        for child in children:
            relative_child = child.relative_to(project_root)
            if child.is_symlink() or _path_contains_secret_marker(relative_child):
                return [], "unverifiable"
            digest, status = sha256_file_stable(child)
            if status != "verified" or digest is None:
                return [], status
            records.append(
                {
                    "locator": normalize_local_locator(project_root, child),
                    "byte_size": child.stat(follow_symlinks=False).st_size,
                    "sha256": digest,
                }
            )
    except (BaselineError, OSError):
        return [], "unverifiable"
    return records, "verified"


def _directory_digest(
    project_root: Path,
    directory: Path,
    excluded_locators: frozenset[str] = frozenset(),
) -> tuple[str | None, int | None, str]:
    records, status = _directory_inventory(project_root, directory, excluded_locators)
    if status != "verified":
        return None, None, status
    return (
        _sha256_bytes(canonical_json_bytes(records)),
        sum(int(record["byte_size"]) for record in records),
        "verified",
    )


def _safe_expected_locator(project_root: Path, relative_path: str) -> tuple[Path, str]:
    candidate_text = relative_path.replace("\\", "/")
    candidate_path = Path(candidate_text)
    if (
        not candidate_text
        or candidate_text.startswith(("/", "~"))
        or candidate_path.is_absolute()
        or PureWindowsPath(candidate_text).is_absolute()
        or ".." in candidate_path.parts
    ):
        raise BaselineError("expected inventory locator is unsafe")
    target = project_root / candidate_path
    return target, normalize_local_locator(project_root, target)


def _entry_for_expected(
    project_root: Path, category: str, relative_path: str
) -> BaselineEntry:
    role, scientific_status = _role_for_category(category)
    target, locator = _safe_expected_locator(project_root, relative_path)
    entry_id = f"{category}:{locator}"
    if _path_contains_secret_marker(Path(locator)):
        return BaselineEntry(
            f"{category}:[REDACTED_SECRET_PATH]", category, role, None, None, None, None,
            "unverifiable", scientific_status, "secret material excluded without reading or hashing"
        )
    if not target.exists():
        return BaselineEntry(
            entry_id, category, role, None, locator, None, None,
            "missing", scientific_status, "expected baseline item is absent"
        )
    try:
        safe_locator = normalize_local_locator(project_root, target)
        if category == "known_absence":
            return BaselineEntry(
                entry_id, category, role, None, safe_locator, None, None,
                "unverifiable", scientific_status,
                "item declared as expected absent exists and requires historical reconciliation",
            )
        if category == "configuration":
            digest, byte_size, status = _configuration_identity(target, safe_locator)
            return BaselineEntry(
                entry_id,
                category,
                "redacted_configuration_identity",
                None,
                safe_locator,
                byte_size,
                digest,
                status,
                scientific_status,
                "identity covers allowlisted non-secret fields only; raw configuration bytes are excluded",
            )
        if category == "mutable_pointer":
            if not target.is_file() or target.is_symlink():
                return BaselineEntry(
                    entry_id, category, "convenience_pointer", None, safe_locator,
                    None, None, "unverifiable", "LEGACY_BASELINE",
                    "mutable pointer must be a readable regular file",
                    None,
                )
            digest, byte_size, observed_target, pointer_status = _mutable_pointer_identity(target)
            if pointer_status == "corrupt":
                return BaselineEntry(
                    entry_id, category, "convenience_pointer", None, safe_locator,
                    byte_size, None, "corrupt", "LEGACY_BASELINE",
                    "mutable pointer contains invalid JSON or lacks an approved target field",
                    None,
                )
            if pointer_status != "mutable":
                return BaselineEntry(
                    entry_id, category, "convenience_pointer", None, safe_locator,
                    None, None, pointer_status, "LEGACY_BASELINE",
                    "mutable pointer changed during observation or could not be safely read",
                    None,
                )
            return BaselineEntry(
                entry_id, category, "convenience_pointer", None, safe_locator, byte_size, digest,
                "mutable", "LEGACY_BASELINE",
                "mutable pointer is recorded for compatibility only and cannot be resolved scientifically",
                observed_target,
            )
        if target.is_dir():
            digest, byte_size, status = _directory_digest(project_root, target)
            return BaselineEntry(
                entry_id, category, role, None, safe_locator, byte_size, digest,
                status, scientific_status,
                None if status == "verified" else "directory could not be safely inventoried",
            )
        digest, status = sha256_file_stable(target)
        byte_size = target.stat(follow_symlinks=False).st_size if status == "verified" else None
        limitation = None if status == "verified" else "file could not be safely verified"
        if category == "recorded_results" and status == "verified":
            limitation = (
                "historical result table is frozen without resolved evidence origin "
                "and is not admitted as a measured result"
            )
        return BaselineEntry(
            entry_id, category, role, None, safe_locator, byte_size, digest,
            status, scientific_status,
            limitation,
        )
    except (BaselineError, OSError):
        return BaselineEntry(
            entry_id, category, role, None, locator, None, None,
            "unverifiable", scientific_status, "locator is unsafe or unreadable",
        )


def _entries_for_expected(
    project_root: Path,
    category: str,
    relative_path: str,
    excluded_locators: frozenset[str] = frozenset(),
) -> list[BaselineEntry]:
    target, safe_locator = _safe_expected_locator(project_root, relative_path)
    if _path_contains_secret_marker(Path(safe_locator)):
        return [_entry_for_expected(project_root, category, relative_path)]
    if not target.is_dir() or category not in CHILD_INVENTORY_CATEGORIES:
        return [_entry_for_expected(project_root, category, relative_path)]
    role, scientific_status = _role_for_category(category)
    root_entry_id = f"{category}:{safe_locator}"
    records, status = _directory_inventory(project_root, target, excluded_locators)
    if status != "verified":
        return [
            BaselineEntry(
                root_entry_id,
                category,
                role,
                None,
                safe_locator,
                None,
                None,
                status,
                scientific_status,
                "directory contains secret, unsafe, unreadable, or mutable material",
            )
        ]
    root_entry = BaselineEntry(
        root_entry_id,
        category,
        role,
        None,
        safe_locator,
        sum(int(record["byte_size"]) for record in records),
        _sha256_bytes(canonical_json_bytes(records)),
        "verified",
        scientific_status,
    )
    children: list[BaselineEntry] = []
    root_prefix = safe_locator.rstrip("/") + "/"
    for record in records:
        child_locator = str(record["locator"])
        child_relative = child_locator.removeprefix(root_prefix)
        children.append(
            BaselineEntry(
                f"{root_entry_id}#child:{child_relative}",
                category,
                role,
                None,
                child_locator,
                int(record["byte_size"]),
                str(record["sha256"]),
                "verified",
                scientific_status,
            )
        )
    return [root_entry, *children]


def _run_git(project_root: Path, *arguments: str) -> tuple[bytes | None, str]:
    try:
        result = subprocess.run(
            ["git", *arguments],
            cwd=project_root,
            check=False,
            capture_output=True,
            timeout=5,
        )
    except (OSError, subprocess.SubprocessError):
        return None, "unverifiable"
    if result.returncode != 0:
        return None, "unverifiable"
    return result.stdout, "verified"


def _sanitized_git_path(raw_path: str, *, suffix: str = "1") -> str:
    locator = raw_path.replace("\\", "/")
    if _path_contains_secret_marker(Path(locator)) or any(ord(character) < 32 for character in locator):
        return f"[REDACTED_SECRET_PATH]/{suffix}"
    return locator


def _sanitized_git_status_digest(raw_status: bytes) -> str:
    """Hash Git state after replacing secret-bearing path metadata."""

    records = [item for item in raw_status.split(b"\0") if item]
    sanitized: list[dict[str, str]] = []
    index = 0
    while index < len(records):
        record = records[index]
        code = record[:2].decode("ascii", "replace")
        raw_path = record[3:].decode("utf-8", "replace")
        item = {"code": code, "path": _sanitized_git_path(raw_path)}
        if "R" in code or "C" in code:
            index += 1
            if index < len(records):
                item["original_path"] = _sanitized_git_path(
                    records[index].decode("utf-8", "replace")
                )
        sanitized.append(item)
        index += 1
    return _sha256_bytes(canonical_json_bytes(sanitized))


def collect_repository_identity(project_root: Path) -> RepositoryIdentity:
    """Collect Git observations without changing the worktree."""

    head_raw, head_status = _run_git(project_root, "rev-parse", "--verify", "HEAD")
    branch_raw, branch_status = _run_git(project_root, "branch", "--show-current")
    status_raw, status_status = _run_git(
        project_root,
        "status",
        "--porcelain=v1",
        "--untracked-files=all",
        "-z",
    )
    ignored_raw, ignored_status = _run_git(
        project_root,
        "status",
        "--porcelain=v1",
        "--ignored=matching",
        "--untracked-files=all",
        "-z",
    )
    head = "sha1:" + head_raw.decode("ascii").strip() if head_raw else None
    branch = (
        _sanitized_git_path(branch_raw.decode("utf-8", "replace").strip(), suffix="branch")
        if branch_raw
        else None
    )
    overlays: list[DirtyOverlay] = []
    overlay_raw = ignored_raw if ignored_raw is not None else status_raw
    if overlay_raw is not None:
        records = [item for item in overlay_raw.split(b"\0") if item]
        index = 0
        while index < len(records):
            record = records[index]
            code = record[:2].decode("ascii", "replace")
            raw_path = record[3:].decode("utf-8", "replace")
            path = project_root / raw_path
            try:
                locator = normalize_local_locator(project_root, path)
            except BaselineError:
                locator = raw_path.replace("\\", "/")
            origin = (
                "ignored_evidence"
                if code == "!!"
                else "untracked"
                if code == "??"
                else "tracked"
            )
            is_post_v1 = bool(
                re.match(
                    r"^_bmad-output/implementation-artifacts/(?:9|1[0-8])[-/]",
                    locator,
                )
                or locator.startswith("_bmad-output/planning-artifacts/")
            )
            if _path_contains_secret_marker(Path(locator)):
                if is_post_v1:
                    origin = "excluded_post_v1"
                locator = f"[REDACTED_SECRET_PATH]/{len(overlays) + 1}"
                digest, verification, byte_size = None, "unverifiable", None
                limitation = "secret-bearing worktree overlay excluded without reading or hashing"
            elif is_post_v1:
                origin = "excluded_post_v1"
                digest, verification, byte_size = None, "unverifiable", None
                limitation = "post-v1 planning material is recorded as excluded provenance"
            elif any(part in EXCLUDED_DIRECTORY_NAMES for part in Path(locator).parts):
                digest, verification, byte_size = None, "unverifiable", None
                limitation = "derived or cache worktree root is excluded without reading or hashing"
            else:
                if locator in REDACTED_CONFIGURATION_LOCATORS and path.is_file():
                    digest, byte_size, verification = _configuration_identity(path, locator)
                elif path.is_dir():
                    digest, byte_size, verification = _directory_digest(project_root, path)
                else:
                    digest, verification = sha256_file_stable(path)
                    byte_size = path.stat(follow_symlinks=False).st_size if verification == "verified" else None
                limitation = None if verification == "verified" else "dirty overlay cannot be safely verified"
            overlays.append(
                DirtyOverlay(
                    locator,
                    code,
                    byte_size,
                    digest,
                    verification,
                    limitation,
                    origin,
                )
            )
            if "R" in code or "C" in code:
                index += 1
                if index < len(records):
                    original_path = records[index].decode("utf-8", "replace")
                    safe_original = _sanitized_git_path(
                        original_path, suffix=f"rename-source-{len(overlays) + 1}"
                    )
                    overlays.append(
                        DirtyOverlay(
                            safe_original,
                            f"{code}:original",
                            None,
                            None,
                            "unverifiable",
                            "rename or copy source is recorded separately and is not rehashed as the destination",
                            origin,
                        )
                    )
            index += 1
    return RepositoryIdentity(
        head=head,
        branch=branch,
        status_sha256=_sanitized_git_status_digest(status_raw) if status_raw is not None else None,
        status_verification="verified" if head_status == branch_status == status_status == "verified" else "unverifiable",
        ignored_status_sha256=_sanitized_git_status_digest(ignored_raw) if ignored_raw is not None else None,
        ignored_status_verification="verified" if ignored_status == "verified" else "unverifiable",
        dirty_overlays=tuple(sorted(overlays, key=lambda item: item.locator)),
    )


def build_manifest(
    *,
    project_root: Path,
    observed_at: str,
    expected_inventory: Mapping[str, Iterable[str]] | None = None,
    include_declared_runtime: bool = False,
) -> V1BaselineManifest:
    """Collect the expected v1 inventory without reading unsafe payloads."""

    root = project_root.resolve(strict=False)
    inventory = DEFAULT_EXPECTED_INVENTORY if expected_inventory is None else expected_inventory
    excluded_locators = frozenset(
        _safe_expected_locator(root, item)[1]
        for item in inventory.get("mutable_pointer", ())
    )
    collected_entries = [
        entry
        for category in sorted(inventory)
        for item in sorted(inventory[category])
        for entry in _entries_for_expected(root, category, item, excluded_locators)
    ]
    collected_entries = [
        replace(entry, evidence_origin="test_fixture")
        if entry.category == "fixtures"
        else entry
        for entry in collected_entries
    ]
    if expected_inventory is None or include_declared_runtime:
        runtime_payload = canonical_json_bytes(
            {
                "implementation": platform.python_implementation(),
                "version": platform.python_version(),
                "cache_tag": sys.implementation.cache_tag,
            }
        )
        collected_entries.append(
            BaselineEntry(
                entry_id="runtime_identity:python",
                category="runtime_identity",
                role="runtime_identity",
                version=platform.python_version(),
                locator="runtime://python",
                byte_size=len(runtime_payload),
                sha256=_sha256_bytes(runtime_payload),
                verification_status="verified",
                scientific_status="IMPLEMENTED_RUNTIME_EVIDENCE",
                limitation="runtime observation identifies the collecting interpreter, not historical execution",
            )
        )
        collected_entries.extend(
            BaselineEntry(
                entry_id=f"external_storage:{locator}",
                category="external_storage",
                role="declared_storage_namespace",
                version=None,
                locator=locator,
                byte_size=None,
                sha256=None,
                verification_status="unverifiable",
                scientific_status="LEGACY_BASELINE",
                limitation="external object storage was deliberately not contacted during offline baseline collection",
            )
            for locator in DECLARED_EXTERNAL_STORAGE
        )
        collected_entries.extend(_declared_container_image_entries(root))
    entries = tuple(sorted(collected_entries, key=lambda entry: entry.entry_id))
    return manifest_with_identity(
        V1BaselineManifest(
            schema_version="V1BaselineManifest.v1",
            baseline_id=None,
            observed_at=observed_at,
            repository=collect_repository_identity(root),
            entries=entries,
            authorization_effect="none",
        )
    )


def manifest_with_identity(manifest: V1BaselineManifest) -> V1BaselineManifest:
    """Attach the derived immutable identity after structural validation."""

    provisional = replace(manifest, baseline_id=None)
    validate_manifest(provisional)
    return replace(provisional, baseline_id=_sha256_bytes(canonical_json_bytes(provisional.to_identity_dict())))


def _is_safe_manifest_locator(locator: str) -> bool:
    if locator.startswith(("minio://", "runtime://")):
        return True
    candidate = locator.replace("\\", "/")
    path = Path(candidate)
    return not (
        not candidate
        or candidate.startswith(("/", "~"))
        or "://" in candidate
        or path.is_absolute()
        or PureWindowsPath(candidate).is_absolute()
        or ".." in path.parts
    )


def validate_manifest(manifest: V1BaselineManifest) -> BaselineValidationResult:
    """Validate only structure and identity policy; never writes or authorizes."""

    if manifest.schema_version != "V1BaselineManifest.v1":
        raise BaselineError("unsupported baseline manifest schema")
    if manifest.authorization_effect != "none":
        raise BaselineError("baseline manifest cannot authorize activity")
    if not OBSERVED_AT_PATTERN.fullmatch(manifest.observed_at):
        raise BaselineError("baseline observation time must be an explicit UTC instant")
    try:
        datetime.fromisoformat(manifest.observed_at.removesuffix("Z") + "+00:00")
    except ValueError as error:
        raise BaselineError("baseline observation time is not a valid calendar instant") from error
    if manifest.repository.status_verification not in {"verified", "unverifiable"}:
        raise BaselineError("unknown repository verification status")
    if manifest.repository.ignored_status_verification not in {"verified", "unverifiable"}:
        raise BaselineError("unknown ignored-worktree verification status")
    if manifest.repository.status_verification == "verified":
        if manifest.repository.head is None or not SHA1_PATTERN.fullmatch(manifest.repository.head):
            raise BaselineError("verified repository identity requires a valid SHA-1 HEAD")
        if (
            manifest.repository.status_sha256 is None
            or not SHA256_PATTERN.fullmatch(manifest.repository.status_sha256)
        ):
            raise BaselineError("verified repository identity requires a valid status digest")
    if manifest.repository.status_sha256 is not None and not SHA256_PATTERN.fullmatch(
        manifest.repository.status_sha256
    ):
        raise BaselineError("repository status digest is invalid")
    if manifest.repository.ignored_status_verification == "verified" and (
        manifest.repository.ignored_status_sha256 is None
        or not SHA256_PATTERN.fullmatch(manifest.repository.ignored_status_sha256)
    ):
        raise BaselineError("verified ignored-worktree identity requires a valid digest")
    if manifest.repository.ignored_status_sha256 is not None and not SHA256_PATTERN.fullmatch(
        manifest.repository.ignored_status_sha256
    ):
        raise BaselineError("ignored-worktree digest is invalid")
    for overlay in manifest.repository.dirty_overlays:
        if overlay.origin not in OVERLAY_ORIGINS:
            raise BaselineError("unknown dirty-overlay origin")
        if overlay.verification_status not in VERIFICATION_STATUSES:
            raise BaselineError("unknown dirty-overlay verification status")
        if overlay.byte_size is not None and overlay.byte_size < 0:
            raise BaselineError("dirty-overlay byte size cannot be negative")
        if overlay.sha256 is not None and not SHA256_PATTERN.fullmatch(overlay.sha256):
            raise BaselineError("dirty-overlay digest is invalid")
        if overlay.verification_status == "verified" and (
            overlay.byte_size is None or overlay.sha256 is None
        ):
            raise BaselineError("verified dirty overlays require size and digest")
        if overlay.verification_status != "verified" and not overlay.limitation:
            raise BaselineError("unverified dirty overlays require a limitation")
    identifiers: set[str] = set()
    for entry in manifest.entries:
        if not entry.entry_id or entry.entry_id in identifiers:
            raise BaselineError("baseline entry identifiers must be non-empty and unique")
        identifiers.add(entry.entry_id)
        if entry.verification_status not in VERIFICATION_STATUSES:
            raise BaselineError("unknown baseline verification status")
        if entry.scientific_status not in SCIENTIFIC_STATUSES:
            raise BaselineError("unknown baseline scientific status")
        if entry.evidence_origin is not None and entry.evidence_origin not in EVIDENCE_ORIGINS:
            raise BaselineError("unknown baseline evidence origin")
        if entry.scientific_status == "MEASURED_RESULT" and entry.evidence_origin != "measured":
            raise BaselineError("measured results require explicit measured evidence origin")
        if entry.scientific_status == "FIXTURE" and entry.evidence_origin != "test_fixture":
            raise BaselineError("fixtures require explicit test-fixture evidence origin")
        if entry.category not in CATEGORY_ROLES:
            raise BaselineError("unknown baseline category")
        expected_role_status = ROLE_SCIENTIFIC_STATUS.get(entry.role)
        if expected_role_status is None:
            raise BaselineError("unknown baseline role")
        if entry.scientific_status != expected_role_status:
            raise BaselineError("baseline role is incompatible with scientific status")
        expected_category_status = CATEGORY_SCIENTIFIC_STATUS.get(entry.category)
        if (
            expected_category_status is not None
            and entry.scientific_status != expected_category_status
        ):
            raise BaselineError("baseline category is incompatible with scientific status")
        allowed_roles = CATEGORY_ROLES.get(entry.category)
        if allowed_roles is not None and entry.role not in allowed_roles:
            raise BaselineError("baseline category is incompatible with evidence role")
        if entry.verification_status == "verified":
            if entry.locator is None or entry.byte_size is None or entry.sha256 is None:
                raise BaselineError("verified baseline entries require locator, size, and digest")
            if entry.byte_size < 0 or not SHA256_PATTERN.fullmatch(entry.sha256):
                raise BaselineError("verified baseline entry has invalid size or digest")
        elif entry.sha256 is not None and entry.verification_status != "mutable":
            raise BaselineError("unverified entries must not present an immutable digest")
        if entry.verification_status == "missing" and (
            entry.byte_size is not None
            or entry.sha256 is not None
            or entry.observed_target is not None
        ):
            raise BaselineError("missing entries cannot carry fabricated identity metadata")
        if entry.byte_size is not None and entry.byte_size < 0:
            raise BaselineError("baseline entry byte size cannot be negative")
        if entry.sha256 is not None and not SHA256_PATTERN.fullmatch(entry.sha256):
            raise BaselineError("baseline entry digest is invalid")
        if entry.verification_status != "verified" and not entry.limitation:
            raise BaselineError("non-verified baseline entries require a limitation")
        if entry.locator is not None and not _is_safe_manifest_locator(entry.locator):
            raise BaselineError("baseline entry locator is unsafe")
    if manifest.baseline_id is not None:
        if not SHA256_PATTERN.fullmatch(manifest.baseline_id):
            raise BaselineError("baseline identity syntax is invalid")
        expected = _sha256_bytes(canonical_json_bytes(manifest.to_identity_dict()))
        if manifest.baseline_id != expected:
            raise BaselineError("baseline identity does not match canonical payload")
    return BaselineValidationResult(valid=True, diagnostics=())


def _baseline_path(output_root: Path, baseline_id: str) -> Path:
    if not baseline_id.startswith("sha256:") or len(baseline_id) != 71:
        raise BaselineError("invalid baseline identity")
    return output_root / f"sha256-{baseline_id.removeprefix('sha256:')}" / "baseline-manifest.v1.json"


def _write_staging_file(staging_root: Path, payload: bytes) -> Path:
    staging_root.mkdir(parents=True, exist_ok=True)
    path = staging_root / f"baseline-{uuid.uuid4().hex}.json"
    descriptor = os.open(path, os.O_WRONLY | os.O_CREAT | os.O_EXCL, 0o600)
    try:
        with os.fdopen(descriptor, "wb", closefd=False) as stream:
            stream.write(payload)
            stream.flush()
            os.fsync(stream.fileno())
    finally:
        os.close(descriptor)
    return path


def _reverify_entry(
    entry: BaselineEntry,
    project_root: Path,
    excluded_locators: frozenset[str] = frozenset(),
) -> None:
    """Fail closed when a locally verified entry changed before finalization."""

    if entry.verification_status != "verified":
        return
    if entry.category == "runtime_identity" and entry.locator == "runtime://python":
        payload = canonical_json_bytes(
            {
                "implementation": platform.python_implementation(),
                "version": platform.python_version(),
                "cache_tag": sys.implementation.cache_tag,
            }
        )
        if entry.sha256 != _sha256_bytes(payload) or entry.byte_size != len(payload):
            raise BaselineError("runtime identity changed before manifest publication")
        return
    if entry.locator is None or "://" in entry.locator:
        raise BaselineError("verified entry has no safe local locator for revalidation")
    target = project_root / Path(entry.locator)
    if normalize_local_locator(project_root, target) != entry.locator:
        raise BaselineError("verified entry locator changed or escaped the project root")
    if entry.category == "configuration":
        digest, byte_size, status = _configuration_identity(target, entry.locator)
    elif target.is_dir():
        digest, byte_size, status = _directory_digest(project_root, target, excluded_locators)
    else:
        digest, status = sha256_file_stable(target)
        byte_size = target.stat(follow_symlinks=False).st_size if status == "verified" else None
    if status != "verified" or digest != entry.sha256 or byte_size != entry.byte_size:
        raise BaselineError("verified entry changed before manifest publication")


def publish_manifest(project_root: Path, manifest: V1BaselineManifest) -> Path:
    """Publish a complete manifest with a fail-if-target-exists primitive."""

    validate_manifest(manifest)
    if manifest.baseline_id is None:
        raise BaselineError("baseline identity is required before publication")
    if manifest_with_identity(manifest).baseline_id != manifest.baseline_id:
        raise BaselineError("baseline identity must be derived from the current payload")
    payload = canonical_json_bytes(manifest.to_dict())
    resolved_project_root = project_root.resolve(strict=False)
    root = (
        resolved_project_root
        / "_bmad-output"
        / "evidence-artifacts"
        / "v1-baselines"
    )
    try:
        root.resolve(strict=False).relative_to(resolved_project_root)
    except ValueError as error:
        raise BaselineError("baseline output root escapes the project through a link") from error
    target = _baseline_path(root, manifest.baseline_id)
    if target.is_symlink():
        raise BaselineError("final baseline manifest cannot be a symlink")
    if target.exists():
        if target.is_file() and target.read_bytes() == payload:
            return target
        raise BaselineError("existing finalized baseline cannot be overwritten")
    if collect_repository_identity(project_root) != manifest.repository:
        raise BaselineError("repository identity changed before manifest publication")
    excluded_locators = frozenset(
        entry.locator
        for entry in manifest.entries
        if entry.category == "mutable_pointer" and entry.locator is not None
    )
    for entry in manifest.entries:
        _reverify_entry(entry, project_root, excluded_locators)
    staging = _write_staging_file(root / ".staging", payload)
    try:
        target.parent.mkdir(parents=True, exist_ok=False)
    except FileExistsError:
        staging.unlink(missing_ok=True)
        if target.is_symlink():
            raise BaselineError("final baseline manifest cannot be a symlink")
        if target.is_file() and target.read_bytes() == payload:
            return target
        raise BaselineError("final baseline identity already has incomplete or different content")
    try:
        os.link(staging, target)
    except OSError as error:
        try:
            target.parent.rmdir()
        except OSError:
            pass
        raise BaselineError("atomic no-overwrite final publication is unavailable") from error
    finally:
        staging.unlink(missing_ok=True)
    return target


def resolve_entry(manifest: V1BaselineManifest, project_root: Path, entry_id: str) -> Path:
    """Resolve one verified local entry with its recorded size and digest."""

    validate_manifest(manifest)
    if manifest.baseline_id is None:
        raise BaselineError("a finalized baseline identity is required for resolution")
    resolved_project_root = project_root.resolve(strict=False)
    publication_root = (
        resolved_project_root
        / "_bmad-output"
        / "evidence-artifacts"
        / "v1-baselines"
    )
    try:
        publication_root.resolve(strict=False).relative_to(resolved_project_root)
    except ValueError as error:
        raise BaselineError("published baseline root escapes the project through a link") from error
    published_manifest = _baseline_path(publication_root, manifest.baseline_id)
    if (
        published_manifest.is_symlink()
        or not published_manifest.is_file()
        or published_manifest.read_bytes() != canonical_json_bytes(manifest.to_dict())
    ):
        raise BaselineError("resolver requires the exact published content-addressed manifest")
    matches = [entry for entry in manifest.entries if entry.entry_id == entry_id]
    if len(matches) != 1:
        raise BaselineError("baseline entry is unknown or ambiguous")
    entry = matches[0]
    if entry.verification_status != "verified" or entry.locator is None:
        raise BaselineError("baseline entry is not immutable local evidence")
    if entry.category == "configuration":
        raise BaselineError("redacted configuration identities do not resolve to raw files")
    if "://" in entry.locator:
        raise BaselineError("baseline entry is an observation, not resolvable local evidence")
    target = project_root / Path(entry.locator)
    if normalize_local_locator(project_root, target) != entry.locator:
        raise BaselineError("baseline locator normalization mismatch")
    if target.is_dir():
        excluded_locators = frozenset(
            candidate.locator
            for candidate in manifest.entries
            if candidate.category == "mutable_pointer" and candidate.locator is not None
        )
        digest, byte_size, status = _directory_digest(project_root, target, excluded_locators)
    else:
        digest, status = sha256_file_stable(target)
        byte_size = target.stat(follow_symlinks=False).st_size if status == "verified" else None
    if status != "verified" or digest != entry.sha256:
        raise BaselineError("baseline entry bytes no longer match frozen identity")
    if byte_size != entry.byte_size:
        raise BaselineError("baseline entry size no longer matches frozen identity")
    return target
