"""Round-scoped identity contract for consensus auditability."""

from __future__ import annotations

from dataclasses import dataclass
from datetime import datetime


@dataclass(frozen=True)
class RoundIdentity:
    """Unique identity for one consensus round and its observation window."""

    round_id: str
    window_started_at: datetime
    window_ended_at: datetime

    def __post_init__(self) -> None:
        if self.window_ended_at < self.window_started_at:
            raise ValueError("Round window end must be greater than or equal to the start.")
