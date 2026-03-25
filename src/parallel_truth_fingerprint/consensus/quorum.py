"""Explicit quorum helpers for deterministic prototype consensus."""


def required_quorum(participant_count: int) -> int:
    """Return the strict majority quorum."""

    if participant_count <= 0:
        raise ValueError("Participant count must be positive.")
    return (participant_count // 2) + 1
