"""Pure resolver-bound construction and validation for ``SignalObservation.v2``."""
from __future__ import annotations

from dataclasses import dataclass
from typing import Any, Callable, Mapping

from parallel_truth_fingerprint.contracts.signal_observation import SignalObservation, SignalObservationError, parse_signal_observation


@dataclass(frozen=True)
class SignalObservationResolver:
    """All authority is injected; no environment, clock, I/O or global registry is read."""
    snapshot_id: str
    identity_resolves: Callable[[str], bool]
    audience_permitted: Callable[[str], bool]
    semantic_permitted: Callable[[Mapping[str, Any]], bool]
    profile_binding_resolves: Callable[[Mapping[str, Any], str], bool]
    recompute: Callable[[Mapping[str, Any]], Mapping[str, Any]]


@dataclass(frozen=True)
class SignalObservationValidation:
    valid: bool
    observation: SignalObservation | None
    violations: tuple[Mapping[str, str], ...]
    authorization_effect: str = "none"


def validate_signal_observation(payload: object, resolver: SignalObservationResolver) -> SignalObservationValidation:
    try:
        observation = parse_signal_observation(payload)
        data = observation.to_dict()
        identities = ("experiment_id", "run_id", "round_id", "edge_id", "sensor_id", "source_stream_id", "source_boot_id", "source_session_id", "event_id")
        if any(not resolver.identity_resolves(data[key]) for key in identities):
            raise SignalObservationError("SOV2_AUDIENCE_IDENTITY", "identity", "resolver_rejected")
        if not resolver.audience_permitted(data["audience_access_class"]):
            raise SignalObservationError("SOV2_AUDIENCE_IDENTITY", "audience_access_class", "resolver_rejected")
        if not resolver.semantic_permitted(data["semantic_identity"]):
            raise SignalObservationError("SOV2_SEMANTIC_ROLE", "semantic_identity", "resolver_rejected")
        if not resolver.profile_binding_resolves(data["profile_binding"], resolver.snapshot_id):
            raise SignalObservationError("SOV2_PROFILE_REFERENCE", "profile_binding", "resolver_rejected")
        recomputed = resolver.recompute(data)
        for field in ("quality_trace", "normalized_span", "engineering_value"):
            if recomputed.get(field) != data[field]:
                raise SignalObservationError("SOV2_QUALITY_RECOMPUTE" if field == "quality_trace" else "SOV2_REPRESENTATION_RECOMPUTE", field, "recompute_mismatch")
        return SignalObservationValidation(True, observation, ())
    except SignalObservationError as exc:
        return SignalObservationValidation(False, None, (exc.violation.to_dict(),))


def build_signal_observation(raw_facts: Mapping[str, Any], *, resolver: SignalObservationResolver) -> SignalObservation:
    """Build only from raw facts plus resolver-owned recomputation.

    Derived quality/representation input is rejected so callers cannot smuggle
    local conversion results into the canonical record.
    """
    forbidden = {"quality_trace", "normalized_span", "engineering_value", "observation_content_id"}
    if forbidden.intersection(raw_facts):
        raise SignalObservationError("SOV2_QUALITY_RECOMPUTE", "builder_input", "caller_derived_fields_forbidden")
    data = dict(raw_facts)
    computed = resolver.recompute(data)
    data.update({key: computed[key] for key in ("quality_trace", "normalized_span", "engineering_value")})
    from parallel_truth_fingerprint.contracts.signal_observation import observation_content_id
    data["observation_content_id"] = observation_content_id(data)
    result = validate_signal_observation(data, resolver)
    if not result.valid or result.observation is None:
        diagnostic = result.violations[0]
        raise SignalObservationError(diagnostic["family"], diagnostic["field"], diagnostic["token"])
    return result.observation
