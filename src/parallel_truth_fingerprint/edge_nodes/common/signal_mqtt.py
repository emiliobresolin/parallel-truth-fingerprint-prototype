"""Canonical, injected MQTT-shaped transport boundary for ``SignalObservation.v2``.

No broker client, retry policy, credentials, or legacy payload codec belongs
here.  The small in-memory relay exists solely to exercise the byte boundary.
"""
from __future__ import annotations

from dataclasses import dataclass, field
import json
from typing import Callable, Protocol

from parallel_truth_fingerprint.contracts.signal_observation import (
    SignalObservation,
    SignalObservationError,
    parse_signal_observation_json,
)
from parallel_truth_fingerprint.edge_nodes.common.signal_acquisition import (
    EdgeSignalObservationView,
    SignalReceiveResult,
)
from parallel_truth_fingerprint.evidence.signal_observations import (
    SignalObservationResolver,
    validate_signal_observation,
)

SIGNAL_OBSERVATION_V2_TOPIC = "physical/observations/v2"


@dataclass(frozen=True)
class SignalMqttTransportPolicy:
    policy_id: str
    authorization_effect: str = "none"

    def __post_init__(self) -> None:
        if not isinstance(self.policy_id, str) or not self.policy_id or self.authorization_effect != "none":
            raise ValueError("PTEV2_TRANSPORT_POLICY")


class SignalMqttPublisher(Protocol):
    def publish(self, *, topic: str, publisher_id: str, payload: bytes) -> None: ...


class SignalMqttSubscriber(Protocol):
    def subscribe(self, *, topic: str, callback: Callable[[str, bytes], None]) -> None: ...


@dataclass(frozen=True)
class SignalMqttResult:
    accepted: bool
    content_id: str | None
    diagnostics: tuple[dict[str, str], ...]
    authorization_effect: str = "none"


def _failure(exc: SignalObservationError) -> SignalMqttResult:
    return SignalMqttResult(False, None, (exc.violation.to_dict(),))


def encode_signal_observation_v2(observation: SignalObservation, *, resolver: SignalObservationResolver) -> bytes:
    """Return only validated canonical bytes; no noncanonical JSON can leave."""
    checked = validate_signal_observation(observation.to_dict(), resolver)
    if not checked.valid or checked.observation is None:
        diagnostic = checked.violations[0]
        raise SignalObservationError(diagnostic["family"], diagnostic["field"], diagnostic["token"])
    # ``SignalObservation.canonical_bytes`` is intentionally the content-ID
    # preimage and excludes the ID.  Transport must carry the complete record,
    # in one equally canonical JSON spelling.
    return json.dumps(checked.observation.to_dict(), ensure_ascii=True, sort_keys=True,
                      separators=(",", ":"), allow_nan=False).encode("ascii")


def decode_signal_observation_v2(payload: bytes, *, resolver: SignalObservationResolver) -> SignalObservation:
    """Strict-parse and prove exact canonical byte representation."""
    observation = parse_signal_observation_json(payload)
    canonical = json.dumps(observation.to_dict(), ensure_ascii=True, sort_keys=True,
                           separators=(",", ":"), allow_nan=False).encode("ascii")
    if canonical != payload:
        raise SignalObservationError("PTEV2_MQTT_CODEC", "payload", "noncanonical_bytes")
    checked = validate_signal_observation(observation.to_dict(), resolver)
    if not checked.valid or checked.observation is None:
        diagnostic = checked.violations[0]
        raise SignalObservationError(diagnostic["family"], diagnostic["field"], diagnostic["token"])
    return checked.observation


def publish_signal_observation_v2(
    observation: SignalObservation, *, publisher: SignalMqttPublisher,
    policy: SignalMqttTransportPolicy, resolver: SignalObservationResolver,
) -> SignalMqttResult:
    """Validate before the injected publisher is called; publisher ID is record-owned."""
    del policy  # Shape is required at the boundary; runtime qualification is downstream.
    try:
        payload = encode_signal_observation_v2(observation, resolver=resolver)
    except SignalObservationError as exc:
        return _failure(exc)
    data = observation.to_dict()
    publisher.publish(topic=SIGNAL_OBSERVATION_V2_TOPIC, publisher_id=data["edge_id"], payload=payload)
    return SignalMqttResult(True, data["observation_content_id"], ())


def bind_signal_observation_v2_receiver(
    *, subscriber: SignalMqttSubscriber, view: EdgeSignalObservationView,
    policy: SignalMqttTransportPolicy, resolver: SignalObservationResolver,
    on_result: Callable[[SignalMqttResult], None] | None = None,
) -> None:
    """Subscribe a strict decoder. Invalid bytes never reach the local view."""
    del policy

    def receive(topic: str, payload: bytes) -> None:
        if topic != SIGNAL_OBSERVATION_V2_TOPIC:
            result = SignalMqttResult(False, None, ({"family": "PTEV2_MQTT_TOPIC", "field": "topic", "token": "exact_v2_topic_required"},))
        else:
            try:
                observation = decode_signal_observation_v2(payload, resolver=resolver)
                local: SignalReceiveResult = view.receive(observation, resolver=resolver)
                result = SignalMqttResult(local.accepted, local.content_id, tuple(dict(v) for v in local.diagnostics))
            except SignalObservationError as exc:
                result = _failure(exc)
        if on_result is not None:
            on_result(result)

    subscriber.subscribe(topic=SIGNAL_OBSERVATION_V2_TOPIC, callback=receive)


@dataclass
class InMemorySignalMqtt:
    """Deterministic fake transport for offline codec tests only."""
    _callbacks: list[Callable[[str, bytes], None]] = field(default_factory=list)
    messages: list[tuple[str, str, bytes]] = field(default_factory=list)

    def subscribe(self, *, topic: str, callback: Callable[[str, bytes], None]) -> None:
        if topic != SIGNAL_OBSERVATION_V2_TOPIC:
            raise ValueError("PTEV2_MQTT_TOPIC")
        self._callbacks.append(callback)

    def publish(self, *, topic: str, publisher_id: str, payload: bytes) -> None:
        if topic != SIGNAL_OBSERVATION_V2_TOPIC:
            raise ValueError("PTEV2_MQTT_TOPIC")
        self.messages.append((topic, publisher_id, payload))
        for callback in tuple(self._callbacks):
            callback(topic, payload)
