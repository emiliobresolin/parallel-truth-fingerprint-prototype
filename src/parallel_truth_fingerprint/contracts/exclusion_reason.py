"""Explicit bounded exclusion reasons for one consensus round."""

from enum import StrEnum


class ExclusionReason(StrEnum):
    INSUFFICIENT_DATA = "insufficient_data"
    INCONSISTENT_VIEW = "inconsistent_view"
    TRUST_BELOW_THRESHOLD = "trust_below_threshold"
    SUSPECTED_BYZANTINE_BEHAVIOR = "suspected_byzantine_behavior"
