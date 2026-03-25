"""Explicit bounded status values for consensus results."""

from enum import StrEnum


class ConsensusStatus(StrEnum):
    SUCCESS = "success"
    FAILED_CONSENSUS = "failed_consensus"
