"""Focused tests for the fake OPC UA SCADA service."""

from __future__ import annotations

import importlib.util
from datetime import datetime, timedelta, timezone
import unittest

from parallel_truth_fingerprint.contracts.consensused_valid_state import (
    ConsensusedValidState,
)
from parallel_truth_fingerprint.contracts.round_identity import RoundIdentity
from parallel_truth_fingerprint.scada import FakeOpcUaScadaService
from tests.persistence.test_service import build_valid_audit_package


def build_valid_state(
    *,
    round_id: str = "round-001",
    temperature: float = 72.5,
    pressure: float = 5.3,
    rpm: float = 3120.0,
) -> ConsensusedValidState:
    ended_at = datetime(2026, 4, 1, 12, 0, 0, tzinfo=timezone.utc)
    return ConsensusedValidState(
        round_identity=RoundIdentity(
            round_id=round_id,
            window_started_at=ended_at - timedelta(minutes=1),
            window_ended_at=ended_at,
        ),
        source_edges=("edge-1", "edge-2"),
        sensor_values={
            "temperature": temperature,
            "pressure": pressure,
            "rpm": rpm,
        },
    )


class FakeOpcUaScadaServiceTests(unittest.TestCase):
    def test_project_state_matches_consensused_values_by_default(self) -> None:
        service = FakeOpcUaScadaService()
        source_state = build_valid_audit_package(round_id="round-001").round_input.replicated_states[0]

        scada_state = service.project_state(
            build_valid_state(),
            source_replicated_state=source_state,
        )

        self.assertEqual(scada_state.compressor_id, "compressor-1")
        self.assertEqual(scada_state.source_round_id, "round-001")
        self.assertEqual(scada_state.behavioral_source_round_id, "round-001")
        self.assertEqual(scada_state.sensor_values["temperature"].value, 72.5)
        self.assertEqual(scada_state.sensor_values["temperature"].unit, "degC")
        self.assertEqual(scada_state.sensor_values["pressure"].value, 5.3)
        self.assertEqual(scada_state.sensor_values["pressure"].unit, "bar")
        self.assertEqual(scada_state.sensor_values["rpm"].value, 3120.0)
        self.assertEqual(scada_state.sensor_values["rpm"].unit, "rpm")
        self.assertTrue(
            all(sensor.mode == "match" for sensor in scada_state.sensor_values.values())
        )
        self.assertEqual(
            scada_state.behavioral_sensor_values["temperature"].loop_current_ma,
            14.2,
        )
        self.assertEqual(
            scada_state.behavioral_sensor_values["temperature"].source_round_id,
            "round-001",
        )

    def test_offset_freeze_and_replay_modes_are_deterministic(self) -> None:
        service = FakeOpcUaScadaService()

        first_state = service.update_from_consensused_state(
            build_valid_state(round_id="round-001", temperature=70.0, pressure=5.0, rpm=3000.0),
            source_replicated_state=build_valid_audit_package(
                round_id="round-001"
            ).round_input.replicated_states[0],
        )
        self.assertEqual(first_state.sensor_values["temperature"].value, 70.0)

        service.set_sensor_override("temperature", mode="offset", offset=2.5)
        offset_state = service.update_from_consensused_state(
            build_valid_state(round_id="round-002", temperature=70.0, pressure=5.1, rpm=3050.0),
            source_replicated_state=build_valid_audit_package(
                round_id="round-002"
            ).round_input.replicated_states[0],
        )
        self.assertEqual(offset_state.sensor_values["temperature"].value, 72.5)
        self.assertEqual(offset_state.sensor_values["temperature"].mode, "offset")
        self.assertEqual(
            offset_state.behavioral_sensor_values["temperature"].mode,
            "offset",
        )

        service.clear_sensor_override("temperature")
        service.set_sensor_override("pressure", mode="freeze")
        frozen_state = service.update_from_consensused_state(
            build_valid_state(round_id="round-003", temperature=71.0, pressure=6.2, rpm=3100.0),
            source_replicated_state=build_valid_audit_package(
                round_id="round-003"
            ).round_input.replicated_states[0],
        )
        still_frozen_state = service.update_from_consensused_state(
            build_valid_state(round_id="round-004", temperature=72.0, pressure=7.1, rpm=3150.0),
            source_replicated_state=build_valid_audit_package(
                round_id="round-004"
            ).round_input.replicated_states[0],
        )
        self.assertEqual(frozen_state.sensor_values["pressure"].value, 6.2)
        self.assertEqual(still_frozen_state.sensor_values["pressure"].value, 6.2)
        self.assertEqual(still_frozen_state.sensor_values["pressure"].mode, "freeze")
        self.assertEqual(
            still_frozen_state.behavioral_sensor_values["pressure"].mode,
            "freeze",
        )

        service.clear_sensor_override("pressure")
        service.set_sensor_override("rpm", mode="replay", replay_round_id="round-001")
        replay_state = service.update_from_consensused_state(
            build_valid_state(round_id="round-005", temperature=74.0, pressure=7.0, rpm=3500.0),
            source_replicated_state=build_valid_audit_package(
                round_id="round-005"
            ).round_input.replicated_states[0],
        )
        self.assertEqual(replay_state.sensor_values["rpm"].value, 3500.0)
        self.assertEqual(replay_state.sensor_values["rpm"].mode, "replay")
        self.assertEqual(replay_state.behavioral_source_round_id, "round-001")
        self.assertEqual(
            replay_state.behavioral_sensor_values["rpm"].mode,
            "replay",
        )
        self.assertEqual(
            replay_state.behavioral_sensor_values["rpm"].source_round_id,
            "round-001",
        )


@unittest.skipIf(
    importlib.util.find_spec("asyncua") is None,
    "asyncua not installed in the current environment",
)
class FakeOpcUaScadaServiceOpcUaTests(unittest.IsolatedAsyncioTestCase):
    async def asyncSetUp(self) -> None:
        self.service = FakeOpcUaScadaService(
            endpoint_url="opc.tcp://127.0.0.1:48419/ptf/scada/server/",
        )
        await self.service.start()

    async def asyncTearDown(self) -> None:
        await self.service.stop()

    async def test_service_exposes_temperature_pressure_and_rpm_over_opcua(self) -> None:
        await self.service.publish_consensused_state(
            build_valid_state(
                round_id="round-010",
                temperature=68.4,
                pressure=4.9,
                rpm=2875.0,
            )
        )

        namespace_index = self.service.namespace_index
        self.assertIsNotNone(namespace_index)
        self.assertGreater(namespace_index, 0)
        self.assertEqual(self.service.endpoint_url, "opc.tcp://127.0.0.1:48419/ptf/scada/server/")

        live_values = await self.service.read_live_values()

        self.assertEqual(live_values["temperature"], 68.4)
        self.assertEqual(live_values["pressure"], 4.9)
        self.assertEqual(live_values["rpm"], 2875.0)
