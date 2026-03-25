"""Consensus package."""

from parallel_truth_fingerprint.consensus.engine import ConsensusEngine
from parallel_truth_fingerprint.consensus.quorum import required_quorum

__all__ = ["ConsensusEngine", "required_quorum"]
