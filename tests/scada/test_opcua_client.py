from __future__ import annotations

import unittest

from parallel_truth_fingerprint.scada.opcua_client import (
    OfflineOpcUaClient, OpcUaDataValue, OpcUaReadRequest, read_scada_observation,
)


def digest(char: str) -> str:
    return "sha256:" + char * 64


def request(*, enabled: bool = True) -> OpcUaReadRequest:
    return OpcUaReadRequest("opc.tcp://127.0.0.1:4840/ptfp", "None", "urn:ptfp:v2",
        {name: f"ns=2;s={name}" for name in ("raw_current_ma", "engineering_value", "revision", "profile", "correlation", "snapshot_ref")},
        digest("a"), digest("b"), digest("c"), digest("d"), digest("e"), enabled)


def values(*, revision: str | None = None) -> dict[str, OpcUaDataValue]:
    base = {"raw_current_ma": "4.0", "engineering_value": "1.0", "revision": revision or digest("d"),
            "profile": digest("e"), "correlation": digest("c"), "snapshot_ref": digest("d")}
    return {name: OpcUaDataValue(value, "Good", "2026-01-01T00:00:00Z", "2026-01-01T00:00:01Z") for name, value in base.items()}


class OpcUaClientContractTests(unittest.IsolatedAsyncioTestCase):
    async def test_offline_fake_builds_deterministic_complete_observation(self) -> None:
        fake = OfflineOpcUaClient(values())
        result = await read_scada_observation(request(), lambda *_: fake, now=lambda: "2026-01-01T00:00:02.000000Z")
        self.assertIsNone(result.blocking_reason)
        self.assertEqual("4.0", result.raw_current_ma.value)
        self.assertEqual("Good", result.raw_current_ma.status_code)
        self.assertTrue(fake.connected and fake.disconnected)
        self.assertEqual(result.content_id(), result.content_id())

    async def test_mixed_revision_fails_without_a_fabricated_value(self) -> None:
        result = await read_scada_observation(request(), lambda *_: OfflineOpcUaClient(values(revision=digest("f"))), now=lambda: "2026-01-01T00:00:02.000000Z")
        self.assertEqual("mixed_snapshot_identity", result.blocking_reason)
        self.assertIsNone(result.raw_current_ma)
        self.assertIsNone(result.snapshot_ref)

    async def test_transport_error_is_a_closed_failure_receipt(self) -> None:
        result = await read_scada_observation(request(), lambda *_: OfflineOpcUaClient({}, error=RuntimeError("offline")), now=lambda: "2026-01-01T00:00:02.000000Z")
        self.assertEqual("client_read_failed", result.blocking_reason)
        self.assertEqual("RuntimeError", result.error)
        self.assertIsNone(result.engineering_value)

    async def test_disabled_v2_never_constructs_or_uses_a_client(self) -> None:
        result = await read_scada_observation(request(enabled=False), lambda *_: self.fail("factory must not run"), now=lambda: "2026-01-01T00:00:02.000000Z")
        self.assertEqual("v2_mode_disabled", result.blocking_reason)

    def test_request_rejects_projected_or_incomplete_node_map(self) -> None:
        invalid = request()
        object.__setattr__(invalid, "node_ids", {"raw_current_ma": "projected"})
        with self.assertRaisesRegex(ValueError, "OPC2-REQUEST-NODES"):
            invalid.validate()


if __name__ == "__main__":
    unittest.main()
