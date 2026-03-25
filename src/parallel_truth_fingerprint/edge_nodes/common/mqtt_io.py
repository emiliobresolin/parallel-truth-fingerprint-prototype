"""Minimal MQTT-style passive relay helpers for local edge exchange.

This module models brokered publish/subscribe behavior for the prototype
without making the broker part of the trust model.
"""

from __future__ import annotations

from collections import defaultdict
from dataclasses import dataclass
from typing import Callable

from parallel_truth_fingerprint.contracts.raw_hart_payload import RawHartPayload


@dataclass(frozen=True)
class RelayMessage:
    topic: str
    publisher_id: str
    payload: RawHartPayload


class PassiveMqttRelay:
    """Passive publish/subscribe relay for local prototype messaging."""

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
        callback: Callable[[RawHartPayload], None],
    ) -> None:
        self._subscribers[topic].append((subscriber_id, callback))

    def publish(self, *, topic: str, publisher_id: str, payload: RawHartPayload) -> None:
        message = RelayMessage(topic=topic, publisher_id=publisher_id, payload=payload)
        self._messages.append(message)

        for subscriber_id, callback in self._subscribers.get(topic, []):
            if subscriber_id == publisher_id:
                continue
            callback(payload)

    def published_messages(self) -> list[dict[str, object]]:
        return [
            {
                "topic": message.topic,
                "publisher_id": message.publisher_id,
                "payload": message.payload,
            }
            for message in self._messages
        ]
