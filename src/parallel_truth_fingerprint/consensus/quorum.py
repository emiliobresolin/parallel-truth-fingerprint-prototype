"""Explicit quorum helpers for deterministic prototype consensus."""


def required_quorum(participant_count: int) -> int:
    """Return strictly more than two thirds of equal-power participants."""

    if participant_count <= 0:
        raise ValueError("Participant count must be positive.")
    return (2 * participant_count // 3) + 1
