"""MQTT transport helpers for local edge exchange.

This module keeps MQTT strictly as transport infrastructure. It supports:
- an in-memory passive relay for deterministic tests
- a real MQTT client path for local runtime/demo use
"""

from __future__ import annotations

from abc import ABC, abstractmethod
from collections import defaultdict
from dataclasses import dataclass
import json
from typing import Callable

from parallel_truth_fingerprint.contracts.raw_hart_payload import (
    DeviceInfo,
    Diagnostics,
    PhysicsMetrics,
    ProcessData,
    ProcessVariable,
    RawHartPayload,
)


@dataclass(frozen=True)
class RelayMessage:
    topic: str
    publisher_id: str
    payload: RawHartPayload


def serialize_payload(payload: RawHartPayload) -> str:
    """Serialize a raw payload for transport."""

    return json.dumps(payload.to_dict())


def deserialize_payload(payload_text: str) -> RawHartPayload:
    """Deserialize a raw payload from transport."""

    data = json.loads(payload_text)
    process_data = data["process_data"]
    diagnostics = data["diagnostics"]
    physics_metrics = process_data["physics_metrics"]

    return RawHartPayload(
        protocol=data["protocol"],
        gateway_id=data["gateway_id"],
        timestamp=data["timestamp"],
        device_info=DeviceInfo(**data["device_info"]),
        process_data=ProcessData(
            pv=ProcessVariable(**process_data["pv"]),
            sv=ProcessVariable(**process_data["sv"]),
            loop_current_ma=process_data["loop_current_ma"],
            pv_percent_range=process_data["pv_percent_range"],
            physics_metrics=PhysicsMetrics(**physics_metrics),
        ),
        diagnostics=Diagnostics(**diagnostics),
    )


class MqttTransport(ABC):
    """Narrow transport boundary shared by passive and real MQTT paths."""

    @abstractmethod
    def subscribe(
        self,
        *,
        topic: str,
        subscriber_id: str,
        callback: Callable[[str, RawHartPayload], None],
    ) -> None:
        """Subscribe one edge to peer observations."""

    @abstractmethod
    def publish(self, *, topic: str, publisher_id: str, payload: RawHartPayload) -> None:
        """Publish one raw local observation."""


class PassiveMqttRelay(MqttTransport):
    """Passive publish/subscribe relay for local prototype tests."""

    def __init__(self) -> None:
        self._subscribers: dict[str, list[tuple[str, Callable[[RawHartPayload], None]]]] = (
            defaultdict(list)
        )
        self._messages: list[RelayMessage] = []

    def subscribe(
        self,
        *,
        topic: str,
        subscriber_id: str,
        callback: Callable[[str, RawHartPayload], None],
    ) -> None:
        self._subscribers[topic].append((subscriber_id, callback))

    def publish(self, *, topic: str, publisher_id: str, payload: RawHartPayload) -> None:
        message = RelayMessage(topic=topic, publisher_id=publisher_id, payload=payload)
        self._messages.append(message)

        for subscriber_id, callback in self._subscribers.get(topic, []):
            if subscriber_id == publisher_id:
                continue
            callback(publisher_id, payload)

    def published_messages(self) -> list[dict[str, object]]:
        return [
            {
                "topic": message.topic,
                "publisher_id": message.publisher_id,
                "payload": message.payload,
            }
            for message in self._messages
        ]


class RealMqttTransport(MqttTransport):
    """Real MQTT client path for local runtime/demo use."""

    def __init__(
        self,
        *,
        host: str,
        port: int,
        client_factory=None,
        keepalive: int = 60,
    ) -> None:
        self._host = host
        self._port = port
        self._keepalive = keepalive
        self._client = self._build_client(client_factory)
        self._connect_if_supported()
        self._start_loop_if_supported()

    def _build_client(self, client_factory):
        if client_factory is not None:
            return client_factory()

        try:
            from paho.mqtt.client import Client  # type: ignore
        except ImportError as exc:
            raise RuntimeError(
                "Real MQTT transport requires paho-mqtt to be installed for runtime/demo use."
            ) from exc

        return Client()

    def _connect_if_supported(self) -> None:
        connect = getattr(self._client, "connect", None)
        if callable(connect):
            connect(self._host, self._port, self._keepalive)

    def _start_loop_if_supported(self) -> None:
        loop_start = getattr(self._client, "loop_start", None)
        if callable(loop_start):
            loop_start()

    def subscribe(
        self,
        *,
        topic: str,
        subscriber_id: str,
        callback: Callable[[str, RawHartPayload], None],
    ) -> None:
        subscription_topic = f"{topic}/#"
        subscribe = getattr(self._client, "subscribe", None)
        if callable(subscribe):
            subscribe(subscription_topic)

        callback_add = getattr(self._client, "message_callback_add", None)
        if callable(callback_add):

            def _wrapped_callback(*args) -> None:
                if len(args) == 2:
                    received_topic, payload_text = args
                else:
                    message = args[-1]
                    received_topic = message.topic
                    payload_bytes = message.payload
                    payload_text = (
                        payload_bytes.decode("utf-8")
                        if isinstance(payload_bytes, (bytes, bytearray))
                        else str(payload_bytes)
                    )

                publisher_id = received_topic.rsplit("/", 1)[-1]
                if publisher_id == subscriber_id:
                    return
                callback(publisher_id, deserialize_payload(payload_text))

            callback_add(subscription_topic, _wrapped_callback)

    def publish(self, *, topic: str, publisher_id: str, payload: RawHartPayload) -> None:
        publish = getattr(self._client, "publish", None)
        if callable(publish):
            publish(f"{topic}/{publisher_id}", serialize_payload(payload))


def create_transport(
    mode: str,
    *,
    host: str = "localhost",
    port: int = 1883,
    client_factory=None,
) -> MqttTransport:
    """Create the selected MQTT transport without changing edge responsibilities."""

    if mode == "passive":
        return PassiveMqttRelay()
    if mode == "real":
        return RealMqttTransport(
            host=host,
            port=port,
            client_factory=client_factory,
        )
    raise ValueError(f"Unsupported MQTT transport mode: {mode}")
