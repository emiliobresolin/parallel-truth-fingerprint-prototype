"""Consensus package."""

from parallel_truth_fingerprint.consensus.alerts import (
    build_consensus_alert,
    format_consensus_alert_compact,
    format_consensus_alert_detailed,
)
from parallel_truth_fingerprint.consensus.cometbft_mapper import (
    committed_round_to_audit_package,
)
from parallel_truth_fingerprint.consensus.engine import ConsensusEngine
from parallel_truth_fingerprint.consensus.logging import (
    build_round_log,
    format_round_log_compact,
    format_round_log_detailed,
)
from parallel_truth_fingerprint.consensus.quorum import required_quorum
from parallel_truth_fingerprint.consensus.summary import (
    build_round_summary,
    format_round_summary,
)

__all__ = [
    "ConsensusEngine",
    "build_consensus_alert",
    "committed_round_to_audit_package",
    "build_round_log",
    "build_round_summary",
    "format_consensus_alert_compact",
    "format_consensus_alert_detailed",
    "format_round_log_compact",
    "format_round_log_detailed",
    "format_round_summary",
    "required_quorum",
]
