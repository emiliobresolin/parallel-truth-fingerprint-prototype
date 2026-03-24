"""Named simulation profiles for the local prototype."""

from parallel_truth_fingerprint.config.ranges import (
    DEFAULT_COMPRESSOR_PROFILE,
    CompressorSimulationProfile,
)


def default_compressor_profile() -> CompressorSimulationProfile:
    """Return the default profile for the single simulated compressor."""

    return DEFAULT_COMPRESSOR_PROFILE
