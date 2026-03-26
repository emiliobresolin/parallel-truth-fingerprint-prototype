"""Minimal CometBFT RPC client for the live consensus demo path."""

from __future__ import annotations

import base64
from dataclasses import dataclass
import json
from typing import Any
from urllib import parse, request

from parallel_truth_fingerprint.contracts.consensus_round_input import ConsensusRoundInput


@dataclass(frozen=True)
class CometBftCommitReceipt:
    """Committed transaction metadata returned by the real consensus layer."""

    round_id: str
    height: int
    tx_hash: str
    check_tx_code: int
    deliver_tx_code: int


def serialize_round_input(round_input: ConsensusRoundInput) -> bytes:
    """Return a deterministic transaction payload for one consensus round."""

    replicated_states = []
    for state in sorted(round_input.replicated_states, key=lambda item: item.owner_edge_id):
        sensor_values = {
            sensor_name: {
                "value": payload.process_data.pv.value,
                "unit": payload.process_data.pv.unit,
            }
            for sensor_name, payload in sorted(state.observations_by_sensor.items())
        }
        replicated_states.append(
            {
                "owner_edge_id": state.owner_edge_id,
                "sensor_values": sensor_values,
            }
        )

    payload = {
        "round_id": round_input.round_identity.round_id,
        "window_started_at": round_input.round_identity.window_started_at.isoformat(),
        "window_ended_at": round_input.round_identity.window_ended_at.isoformat(),
        "participating_edges": list(round_input.participating_edges),
        "replicated_states": replicated_states,
    }
    return json.dumps(payload, sort_keys=True, separators=(",", ":")).encode("utf-8")


class CometBftRpcClient:
    """Small HTTP client for broadcast and query against CometBFT RPC."""

    def __init__(self, rpc_url: str) -> None:
        self._rpc_url = rpc_url.rstrip("/")

    def broadcast_round(self, round_input: ConsensusRoundInput) -> CometBftCommitReceipt:
        """Submit a round transaction through CometBFT and wait for commit."""

        encoded_tx = base64.b64encode(serialize_round_input(round_input)).decode("ascii")
        response = self._json_rpc(
            "broadcast_tx_commit",
            {"tx": encoded_tx},
            candidate_paths=("/v1", ""),
        )
        result = response["result"]
        return CometBftCommitReceipt(
            round_id=round_input.round_identity.round_id,
            height=int(result["height"]),
            tx_hash=result["hash"],
            check_tx_code=int(result["check_tx"]["code"]),
            deliver_tx_code=int(result["tx_result"]["code"]),
        )

    def query_committed_round(self, round_id: str) -> dict[str, Any]:
        """Query the ABCI application state for one committed round."""

        quoted_round_id = json.dumps(round_id)
        response = self._get_json(
            "/abci_query",
            {"data": quoted_round_id},
            fallback_paths=("/v1/abci_query", "/abci_query"),
        )
        query_result = response["result"]["response"]
        if int(query_result["code"]) != 0:
            raise RuntimeError(query_result.get("log", "abci_query failed"))
        raw_value = base64.b64decode(query_result["value"])
        return json.loads(raw_value.decode("utf-8"))

    def status(self) -> dict[str, Any]:
        """Return node status to prove the real consensus network is reachable."""

        response = self._get_json("/status", None, fallback_paths=("/v1/status", "/status"))
        return response["result"]

    def _json_rpc(
        self,
        method: str,
        params: dict[str, Any],
        *,
        candidate_paths: tuple[str, ...],
    ) -> dict[str, Any]:
        payload = json.dumps(
            {
                "jsonrpc": "2.0",
                "id": 1,
                "method": method,
                "params": params,
            }
        ).encode("utf-8")
        last_error: Exception | None = None
        for path in candidate_paths:
            try:
                req = request.Request(
                    f"{self._rpc_url}{path}",
                    data=payload,
                    headers={"Content-Type": "application/json"},
                    method="POST",
                )
                with request.urlopen(req, timeout=15) as response:
                    body = json.loads(response.read().decode("utf-8"))
                if body.get("error"):
                    raise RuntimeError(body["error"])
                return body
            except Exception as exc:  # pragma: no cover - fallback path handling
                last_error = exc
        raise RuntimeError(f"CometBFT RPC call failed: {last_error}") from last_error

    def _get_json(
        self,
        default_path: str,
        query: dict[str, str] | None,
        *,
        fallback_paths: tuple[str, ...],
    ) -> dict[str, Any]:
        suffix = ""
        if query:
            suffix = f"?{parse.urlencode(query)}"
        last_error: Exception | None = None
        for path in fallback_paths:
            try:
                with request.urlopen(f"{self._rpc_url}{path}{suffix}", timeout=15) as response:
                    return json.loads(response.read().decode("utf-8"))
            except Exception as exc:  # pragma: no cover - fallback path handling
                last_error = exc
        raise RuntimeError(f"CometBFT HTTP call failed: {last_error}") from last_error
