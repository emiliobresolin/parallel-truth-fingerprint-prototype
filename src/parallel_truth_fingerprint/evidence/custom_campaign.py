"""Synchronized custom current-domain and edge-syscall campaign artifacts."""

from __future__ import annotations

from dataclasses import asdict, dataclass
from datetime import datetime
from hashlib import sha256
import json
from pathlib import Path
import re
from typing import Iterable

from parallel_truth_fingerprint.lstm_service.dataset_builder import extract_feature_vector


_STRACE_LINE = re.compile(r"^(?P<timestamp>\d+\.\d+)\s+(?P<name>[A-Za-z_][A-Za-z0-9_]*)\(")


@dataclass(frozen=True)
class CampaignReadiness:
    ready: bool
    campaign_id: str
    reasons: tuple[str, ...]
    authorization_effect: str = "none"


@dataclass(frozen=True)
class SynchronizedCampaignRow:
    """One physical-artifact time window with raw edge syscall observations."""

    campaign_id: str
    round_id: str
    window_started_at: str
    window_ended_at: str
    artifact_key: str
    scenario_label: str
    current_feature_schema: tuple[str, ...]
    current_feature_vector: tuple[float, ...]
    syscall_tokens: tuple[str, ...]
    autoencoder_results: tuple[dict[str, object], ...]

    def to_dict(self) -> dict[str, object]:
        return asdict(self)


@dataclass(frozen=True)
class CampaignDatasetManifest:
    campaign_id: str
    schema_version: str
    runtime_log_sha256: str
    syscall_trace_sha256: dict[str, str]
    row_count: int
    rows_with_syscalls: int
    autoencoder_enabled: bool
    artifact_keys: tuple[str, ...]
    output_file: str

    def to_dict(self) -> dict[str, object]:
        return asdict(self)


def verify_campaign(
    *,
    campaign_id: str,
    physical_authorization_id: str,
    syscall_authorization_id: str,
    correlation_policy_id: str,
) -> CampaignReadiness:
    """Legacy immutable-ID check retained for callers of the former stub."""

    refs = (
        campaign_id,
        physical_authorization_id,
        syscall_authorization_id,
        correlation_policy_id,
    )
    bad = (
        ("CAMPAIGN-IMMUTABLE-CLOSURE",)
        if any(not value.startswith("sha256:") for value in refs)
        else ()
    )
    return CampaignReadiness(not bad, campaign_id, bad)


def build_synchronized_campaign_dataset(
    *,
    campaign_id: str,
    capture_directory: Path,
    runtime_payload: dict[str, object],
    artifacts: Iterable[dict[str, object]],
    output_directory: Path,
) -> CampaignDatasetManifest:
    """Write a traceable custom dataset from one live campaign.

    The correlation uses absolute epoch timestamps: strace is invoked with
    timestamps and each persisted consensus artifact carries its acquisition
    window.  No synthetic syscall stream is created when a physical window
    has no corresponding edge events; that condition fails the campaign.
    """

    capture_directory = Path(capture_directory)
    runtime_path = capture_directory / "runtime.json"
    if not runtime_path.is_file():
        raise ValueError(f"Missing runtime log: {runtime_path}")
    if runtime_payload.get("runtime", {}).get("status") != "completed":
        raise ValueError("Custom campaign requires a completed live runtime log.")
    if _runtime_autoencoder_disabled(runtime_payload):
        raise ValueError("Custom campaign requires DEMO_DISABLE_RUNTIME_AUTOENCODER=false.")

    trace_paths = tuple(sorted(capture_directory.glob("edge-syscalls.*")))
    if not trace_paths:
        raise ValueError("Custom campaign requires raw edge-syscalls.* traces.")
    syscall_events = _read_syscall_events(trace_paths)
    if not syscall_events:
        raise ValueError("No parseable timestamped syscalls were found in the capture.")

    inference_by_round = _inference_by_round(runtime_payload)
    rows: list[SynchronizedCampaignRow] = []
    for artifact in sorted(artifacts, key=_artifact_window_end):
        dataset_context = artifact.get("dataset_context")
        round_identity = artifact.get("round_identity")
        if not isinstance(dataset_context, dict) or not isinstance(round_identity, dict):
            raise ValueError("Campaign artifact lacks dataset_context or round_identity.")
        if dataset_context.get("campaign_id") != campaign_id:
            raise ValueError("Artifact campaign_id does not match the capture run id.")
        started = str(round_identity["window_started_at"])
        ended = str(round_identity["window_ended_at"])
        window_tokens = _tokens_in_window(
            syscall_events,
            started_at=_to_epoch(started),
            ended_at=_to_epoch(ended),
        )
        if not window_tokens:
            raise ValueError(
                f"No raw edge syscall is correlated to round {round_identity['round_id']}."
            )
        schema, values = extract_feature_vector(artifact)
        round_id = str(round_identity["round_id"])
        rows.append(
            SynchronizedCampaignRow(
                campaign_id=campaign_id,
                round_id=round_id,
                window_started_at=started,
                window_ended_at=ended,
                artifact_key=str(artifact.get("artifact_key") or ""),
                scenario_label=str(dataset_context.get("scenario_label")),
                current_feature_schema=schema,
                current_feature_vector=values,
                syscall_tokens=window_tokens,
                autoencoder_results=tuple(inference_by_round.get(round_id, ())),
            )
        )
    if not rows:
        raise ValueError("No persisted campaign artifacts were supplied.")
    schema_set = {row.current_feature_schema for row in rows}
    if len(schema_set) != 1:
        raise ValueError("Current feature schema drifted within one campaign.")

    output_directory = Path(output_directory)
    output_directory.mkdir(parents=True, exist_ok=True)
    data_path = output_directory / "current-syscall-windows.jsonl"
    with data_path.open("w", encoding="utf-8", newline="\n") as handle:
        for row in rows:
            handle.write(json.dumps(row.to_dict(), sort_keys=True) + "\n")

    manifest = CampaignDatasetManifest(
        campaign_id=campaign_id,
        schema_version="PTFP-Custom-current-syscall-v1",
        runtime_log_sha256=_sha256_file(runtime_path),
        syscall_trace_sha256={path.name: _sha256_file(path) for path in trace_paths},
        row_count=len(rows),
        rows_with_syscalls=sum(bool(row.syscall_tokens) for row in rows),
        autoencoder_enabled=True,
        artifact_keys=tuple(row.artifact_key for row in rows),
        output_file=str(data_path),
    )
    (output_directory / "manifest.json").write_text(
        json.dumps(manifest.to_dict(), indent=2, sort_keys=True) + "\n",
        encoding="utf-8",
    )
    return manifest


def _runtime_autoencoder_disabled(runtime_payload: dict[str, object]) -> bool:
    runtime = runtime_payload.get("runtime")
    if not isinstance(runtime, dict):
        return True
    return runtime.get("model_status") == "runtime_autoencoder_disabled"


def _read_syscall_events(trace_paths: Iterable[Path]) -> tuple[tuple[float, str], ...]:
    events: list[tuple[float, str]] = []
    for path in trace_paths:
        for line in path.read_text(encoding="utf-8", errors="replace").splitlines():
            match = _STRACE_LINE.match(line)
            if match:
                events.append((float(match.group("timestamp")), match.group("name")))
    return tuple(sorted(events))


def _tokens_in_window(
    events: Iterable[tuple[float, str]], *, started_at: float, ended_at: float
) -> tuple[str, ...]:
    return tuple(name for timestamp, name in events if started_at <= timestamp <= ended_at)


def _inference_by_round(runtime_payload: dict[str, object]) -> dict[str, list[dict[str, object]]]:
    result: dict[str, list[dict[str, object]]] = {}
    for cycle in runtime_payload.get("cycle_history", []):
        if not isinstance(cycle, dict):
            continue
        for inference in cycle.get("fingerprint_inference_results", []):
            if not isinstance(inference, dict):
                continue
            for round_id in inference.get("round_ids", []):
                result.setdefault(str(round_id), []).append(dict(inference))
    return result


def _artifact_window_end(artifact: dict[str, object]) -> str:
    identity = artifact.get("round_identity")
    return str(identity.get("window_ended_at", "")) if isinstance(identity, dict) else ""


def _to_epoch(value: str) -> float:
    return datetime.fromisoformat(value.replace("Z", "+00:00")).timestamp()


def _sha256_file(path: Path) -> str:
    digest = sha256()
    with path.open("rb") as handle:
        for chunk in iter(lambda: handle.read(1024 * 1024), b""):
            digest.update(chunk)
    return f"sha256:{digest.hexdigest()}"
