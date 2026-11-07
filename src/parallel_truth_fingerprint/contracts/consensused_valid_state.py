"""Trusted state contract produced only by successful consensus."""

from __future__ import annotations

from dataclasses import dataclass

from parallel_truth_fingerprint.contracts.round_identity import RoundIdentity


@dataclass(frozen=True)
class ConsensusedValidState:
    """Validated state for downstream consumers."""

    round_identity: RoundIdentity
    source_edges: tuple[str, ...]
    sensor_values: dict[str, float]
    measurement_domain: str = 'loop_current_ma'

    def __post_init__(self):
        import math
        if self.measurement_domain != 'loop_current_ma' or not self.sensor_values or any(not math.isfinite(float(v)) for v in self.sensor_values.values()):
            raise ValueError('Validated state must contain finite acquired currents in mA.')
