"""Structured deterministic trust-evaluation evidence for one consensus round."""

from __future__ import annotations

from dataclasses import dataclass

from parallel_truth_fingerprint.contracts.round_identity import RoundIdentity


@dataclass(frozen=True)
class SensorDeviationEvidence:
    """Per-sensor numeric deviation evidence with units."""

    sensor_name: str
    deviation_value: float
    unit: str


@dataclass(frozen=True)
class PerEdgeTrustEvidence:
    """Per-edge trust evidence derived directly from the trust model."""

    round_identity: RoundIdentity
    edge_id: str
    score: float
    sensor_deviations: tuple[SensorDeviationEvidence, ...]

